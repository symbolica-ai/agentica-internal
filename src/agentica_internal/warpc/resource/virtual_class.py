# fmt: off


from dataclasses import KW_ONLY
from enum import EnumType
from typing import _TypedDictMeta, Never  # type: ignore
from typing import _ProtocolMeta

from ...cpython.class_info import HEAP_CLASS
from ...cpython.function import func_compile
from ...cpython.iters import ITER_TYPES

from ..data.identifier import Identifier, set_fun_identifier
from ..data.signature import Signature, get_signature
from ..data.signature_compile import set_fun_signature
from ..data.signature_utils import sig_of_class_constructor, NO_DEFAULTS

from .__ import *
from .base import *
from .handle import is_virtual_class
from .vbuiltins import choose_system_base, virtual_base_methods, v_classes
from .vbuiltins.vmethods import v_dict, v_empty

__all__ = [
    'ClassData',
]


################################################################################

class ClassData(ResourceData):
    __slots__ = (
        'name', 'qname', 'module', 'doc', 'cls', 'bases', 'factory', 'methods', 'attrs',
        'sattrs', 'params', 'props', 'keys', 'annos', 'mch_args', 'hashing'
    )

    KIND = Kind.Class
    FORBIDDEN_FORM = forbidden_class

    name:     str
    qname:    optstr
    module:   optstr
    doc:      optstr
    cls:      ClassT
    bases:    Tup[ClassT]
    factory:  Signature | None
    methods:  MethodsT
    attrs:    AttributesT
    sattrs:   strtup
    params:   Tup[TypeT]
    props:    PropertiesT
    annos:    AnnotationsT
    mch_args: strtup | None
    hashing:  HashMode
    keys:     strtup

    # attrs is for class-level attributes whose values ARE recreated locally
    # in the special case of cls = EnumMeta, these class-level attributes will include members
    # of the enumeration, and these are presented as serialized as `EnumMemberData` objects

    # `keys` is for any fields that getattr should work on but ARE NOT present in `methods` or `attrs`
    # these are represent attributes of the class object itself, in other words, if they have
    # corresponding annotations in `annos`, these annotations would be wrapped in ClassVar[...]
    # some unwarpable dunders (like `__class_getitem__`) will be forwarded instead if they
    # are noticed in the keys

    # `sattrs` corresponds to the confusingly-named `__static_attributes__` field, which is what the
    # python compiler populates by finding all the `self.XXX` that occur in methods of a class
    # definition. we reproduce it here, but it is not semantically meaningful for virtualization.

    # `factory` is the *signature* that should be used for `__new__`, locally.
    # we must know this because blind *args, **kwargs destroys local type introspection

    # implementation attached later
    @classmethod
    def describe_resource(cls, cls_obj: ClassT) -> 'ClassData': ...  # noqa: F841

    # implementation attached later
    def create_resource(self, handle: ResourceHandle) -> ClassT: ...


################################################################################

def describe_real_class(cls: type) -> ClassData:

    data = ClassData()

    if not isinstance(cls, type):
        raise E.WarpEncodingError(f"{f_object_id(cls)} is not a class")

    name, qualname, module, doc = get_class_strings(cls)

    bases = cls.__bases__
    if not is_tup(bases):
        raise E.WarpEncodingError(f"class {cls!r} bases {f_object_id(bases)} is not a tuple")

    if is_forbidden(cls, module):
        raise E.WarpEncodingForbiddenError(f"<class {cls.__module__}.{cls.__qualname__}'>")

    data.name = name
    data.qname = qualname
    data.module = module
    data.doc = doc

    mcls = type(cls)
    data.cls = mcls
    data.bases = bases

    no_priv_fields = flags.OMIT_PRIVATE_FIELDS
    no_priv_annos = flags.OMIT_PRIVATE_ANNOS
    allow_dunders = flags.ALLOW_KNOWN_DUNDER_METHODS

    sys_base = choose_system_base(bases)
    v_methods, v_specials = virtual_base_methods(sys_base)

    data.methods, add_meth = mkdict()
    data.attrs, add_attr = mkdict()
    data.props, add_prop = mkdict()
    mch_args = None
    keys = []
    cdict = cls.__dict__
    for ckey, cval in cdict.items():
        if ckey.startswith('___'):  # these are ours!
            continue
        if ckey in v_methods:
            continue
        if ckey in v_specials:
            keys.append(ckey)
            continue
        if no_priv_fields and ckey.startswith('_'):
            if not allow_cls_attr(ckey, allow_dunders):
                continue
        if is_property_t(cval):
            if not flags.CLASS_PROPERTIES:
                continue
            add_prop(ckey, cval)
        elif is_method_t(cval):
            add_meth(ckey, cval)
        elif ckey in CLASS_ATTR_WHITELIST:
            add_attr(ckey, cval)
        elif ckey == MATCHARGS and is_strtup(cval):
            mch_args = cval
        elif ckey not in CLASS_METADATA:
            keys.append(ckey)

    data.keys = tuple(keys)
    data.params = getattr(cls, TPARAMS, ())

    sattrs, annos = multi_get_raw(cls, SATTRS, ANNOS)

    data.factory = sig_of_class_constructor(cls, 1, NO_DEFAULTS)
    factory_ret = data.factory.annos.get('return')
    if factory_ret is Never or factory_ret is NoReturn:
        data.factory = None

    if not is_strtup(sattrs):
        sattrs = ()

    if not is_rec(annos):
        annos = {}

    if sattrs and no_priv_fields:
        sattrs = tuple(s for s in sattrs if not s.startswith('_'))

    if annos and no_priv_annos:
        annos = {k: v for k, v in annos.items() if not k.startswith('_') or v is KW_ONLY}

    hash_fn = getattr(cls, '__hash__')
    if hash_fn is object.__hash__:
        hash_mode = 'id'
    elif hash_fn is None:
        hash_mode = None
    else:
        hash_mode = 'user'

    data.sattrs = sattrs
    data.annos = annos
    data.mch_args = mch_args
    data.hashing = hash_mode

    return data


################################################################################

def allow_cls_attr(ckey: str, allow_dunders: bool) -> bool:
    if not ckey.startswith('_'):
        return True
    elif ckey in UNWARPABLE_DUNDER_METHODS:
        return False
    elif ckey in CLASS_ATTR_WHITELIST:
        return True
    elif allow_dunders and ckey.endswith('__') and ckey in KNOWN_DUNDER_METHODS:
        return True
    else:
        return False

################################################################################

def create_virtual_class(data: ClassData, handle: ResourceHandle) -> ClassT:

    handle.kind = Kind.Class

    name = data.name
    qname = data.qname
    bases = data.bases
    module = data.module

    cdict, add = mkdict()

    # REMOTE KEYS ==============================================================

    # here we decide what getattr keys should be allowed to result in a GetAttr request

    # the virtual class's keys = the union of what came over wire, and the keys of any virtual
    # parents
    keys = set(data.keys)

    any_virtual_bases = False
    for base in bases:
        if is_virtual_class(base):
            any_virtual_bases = True
            if base.__flags__ & HEAP_CLASS:
                keys |= cls_handle(base).keys

    # the goal is to find the 'safe' version of __new__, likely `object.__new__`
    # this also determines what methods we will layer on into cdict
    sys_base = choose_system_base(bases)
    # print(f'{module:<30} {qname:<20}: ', [b.__name__ for b in bases], sys_base.__name__)

    v_methods, v_specials = virtual_base_methods(sys_base)

    if not any_virtual_bases:
        # pick up the virtual versions of __str__, __hash__, ...; subclasses of this virtual
        # class will inherit these, or the true class may override them later in this
        # function, or in a subclass
        cdict.update(v_methods)

    if Generic in bases:
        keys.add(CLS_GETITEM)

    # specials are ONLY added if they were present (but excluded on encoding)
    for k, m in v_specials.items():
        if k in keys:
            cdict[k] = m

    if flags.VIRTUAL_OBJECT_DUNDER_DICT and sys_base is object:
        cdict['__dict__'] = property(v_dict)

    # `handle` is the buried handle that tells us how to do virtual calls
    handle.keys = keys
    handle.open = flags.CLASS_OPEN_KEYS
    handle.name = name

    # TYPESCRIPT COMPATIBILITY =================================================

    # typescript assumes that the factory is specified as `__init__`, so we
    # pop it off here and move it to factory
    if data.factory is None:
        if init := data.methods.pop('__init__', None):
            if type(init) is tuple: init = init[1]
            assert type(init) is FunctionType
            data.factory = get_signature(init, skip=1)

    # VIRTUAL METHODS ==========================================================

    # add methods
    for k, m in data.methods.items():
        add(k, m)

    # OBJECT INSTANTIATION =====================================================

    # this `__new__` stub ensures that `v_cls(...)` will result in a `New` request, which will
    # construct an *ordinary* object remotely, whereupon it will be encoded to `ObjectDataMsg` when
    # the returned value is encoded. when this is decoded back here, it will trigger
    # `ObjectData.create_virtual_resource`, which will create an instance of the `v_cls` we are
    # defining here.

    # `__new__` is automatically class method, so when it is invoked by Python, the `cls`
    # argument isn't necessarily equal to `v_cls` (it could be a subclass of `v_cls`). but
    # because every such subclass must have been created by decoding, it will have its own
    # `__new__` that is more specialized. so we are guaranteed that `cls is v_cls`, though we
    # cannot assert this here because `v_cls` does not exist yet and so cannot be closed over.

    factory = data.factory
    __new__ = make_virtual_new(f'{qname}.__new__', module, handle, sys_base, factory)
    __init__ = make_virtual_init(f'{qname}.__init__', module, factory)

    add('__new__', __new__)
    add('__init__', __init__)

    # VIRTUAL PROPERTIES =======================================================

    # add properties (virtual implementors of descriptor protocol):
    for k, p in data.props.items():
        add(k, p)

    # ATTRIBUTES ===============================================================

    # add (real) non-method attributes
    for k, a in data.attrs.items():
        add(k, a)

    # METADATA =================================================================

    # add metadata
    add(VHDL, handle)
    add(QUALNAME, qname)
    add(MODULE, module)
    add(DOC, data.doc)
    add(SATTRS, data.sattrs)
    add(ANNOS, data.annos)
    add(TPARAMS, data.params)

    mch_args = data.mch_args
    if mch_args is not None:
        add(MATCHARGS, data.mch_args)

    # HASHING ==================================================================

    match data.hashing:
        case 'id':   cdict['__hash__'] = object.__hash__
        case 'user': cdict['__hash__'] = v_methods.get('__hash__') or v_classes._object.__hash__
        case None:   cdict['__hash__'] = None

    # CLASS HIERARCHY ==========================================================

    bases = tuple(b for b in bases if b is not Generic)
    mcls = data.cls

    # CLASS CREATION ===========================================================

    error: TypeError | None = None
    try:
        if mcls is _ProtocolMeta:
            cdict['_is_protocol'] = True
            cdict['_is_runtime_protocol'] = True

        if Protocol in bases and any(not issubclass(b, Protocol) for b in bases):
            bases = tuple(b for b in bases if b is not Protocol)

        if mcls is EnumType:
            raise E.WarpDecodingError('enums not supported')
        elif mcls is _TypedDictMeta:
            bases = tuple(b for b in bases if b is not dict)
            # typeddict meta takes extra keyword argument `total`
            total = data.attrs.get('__total__', True)
            v_cls = mcls(name, bases, cdict, total=total)
        else:
            v_cls = mcls(name, bases, cdict)

    except Exception as exc:
        error = exc
        v_cls = type

    if error:
        f_error = D.fmt_exception(error)
        problem = f"Error creating virtual class {name!r} with bases {bases!r} and mcls {mcls!r}:\n"
        raise E.WarpDecodingError(problem + f_error)

    # CLASS ATTRIBUTES =========================================================

    # we set these AFTER class creation, so that _ProtocolMeta does not see these
    # attributes and getattr them, triggering RPC
    if flags.VIRTUAL_CLASS_ATTRIBUTES:
        # these will cause v_cls.foo to produce a ResourceGetAttr request against
        # v_cls. this is necessary because `v_cls.__getattr__` (which is really the `__getattr__` from
        # stub_methods.py) will only trigger for *instances* of v_cls.
        for key in keys:
            if key in cdict:
                # this shouldn't happen: keys is for attributes that aren't already
                # a method or an attribute
                continue
            v_attr = class_attribute(handle)
            try:
                cls_set(v_cls, key, v_attr)
            except AttributeError:  # sympy.FunctionClass.nargs
                pass
            v_attr.__set_name__(v_cls, key)

    return v_cls


###############################################################################

class class_attribute:
    # ___vhdl___ is the handle for the class itself
    __slots__ = 'name', '__objclass__', VHDL

    def __init__(self, handle: ResourceHandle) -> None:
        self.___vhdl___ = handle
        self.__objclass__ = object
        self.name = '<unset>'

    def __set_name__(self, owner: type, name: str) -> None:
        self.__objclass__ = owner
        self.name = name

    def __get__(self, instance, owner: Any = None):
        handle = self.___vhdl___
        if instance is not None:
            # Instance access (e.g., v_obj.attr) - get from instance
            # This handles dataclass fields where the class has a default but
            # the instance has a different value
            from .handle import obj_handle
            inst_handle = obj_handle(instance)
            request = ResourceGetAttr(instance, self.name)
            return inst_handle.hdlr(inst_handle, request)
        else:
            # Class access (e.g., VirtualCls.attr) - get from class
            request = ResourceGetAttr(self.__objclass__, self.name)
            return handle.hdlr(handle, request)

    def __repr__(self):
        return f'<attribute {self.name!r}>'

    __str__ = __repr__


###############################################################################

def make_virtual_new(qual_name: str, mod: str, cls_handle: ResourceHandle, sys_base: type, sig: Signature) -> FunctionType:

    if log := bool(LOG_DECR):
        P.nprint(ICON_CM, "making virtual __new__ method for", cls_handle, "with system base", sys_base.__name__)

    if sig is None:
        new_fn = make_unconstructible_new(log, qual_name, sys_base)
    elif sys_base is type:
        new_fn = make_virtual_metaclass_new(log, qual_name, cls_handle)
    elif sys_base is object:
        new_fn = make_virtual_object_new(log, qual_name, cls_handle, sys_base, sig)
    else:
        new_fn = make_virtual_builtin_new(log, qual_name, cls_handle, sys_base)

    ident = Identifier('__new__', qual_name, mod)
    set_fun_identifier(new_fn, ident)

    return new_fn


################################################################################

def make_unconstructible_new(log: bool, qual_name: str, sys_base: type) -> FunctionType:

    def new_local(cls: type, obj_handle: ResourceHandle):
        if log: P.nprint(ICON_C1, f"{qual_name}: creating new local object of unconconstructible", cls, "with handle", obj_handle)
        v_obj = v_empty(sys_base, cls)  # type: ignore
        obj_set(v_obj, VHDL, obj_handle)
        return v_obj

    def new_remote(cls):
        if log: P.nprint(ICON_C1, f"{qual_name}: refusing attempt to create unconstructible", cls)
        raise TypeError(f"Cannot construct instances of {cls.__name__} in this environment.")

    def __new__(cls, *args, **kwargs) -> Never:
        obj_handle = kwargs.get(VHDL)
        return new_local(cls, obj_handle) if obj_handle is not None else new_remote(cls)

    return __new__  # type: ignore

###############################################################################

def make_virtual_object_new(log: bool, qual_name: str, cls_handle: ResourceHandle, sys_base: type, sig: Signature) -> FunctionType:

    def new_local(cls: type, obj_handle: ResourceHandle):
        if log: P.nprint(ICON_C1, f"{qual_name}: creating new local object of", cls, "with handle", obj_handle)
        v_obj = v_empty(sys_base, cls)  # type: ignore
        obj_set(v_obj, VHDL, obj_handle)
        return v_obj

    def new_remote(cls: type, args, kwargs):
        if log: P.nprint(ICON_CM, f"{qual_name}: creating new remote object of", cls)
        kwargs.pop(VHDL, None)
        for i, a in enumerate(args):
            if a is ARG_DEFAULT:
                args = args[:i]
                break
        if log:
            if args:   P.nprint(ICON_CM, "args=", args)
            if kwargs: P.nprint(ICON_CM, "kwargs=", kwargs)

        v_obj = cls_handle.hdlr(cls_handle, ResourceNew(cls, args, kwargs))
        return v_obj

    if sig.num_args == 2 and sig.pos_star and sig.key_star:
        def __new__(cls, *args, **kwargs):
            if log: P.nprint(ICON_CM, f"{qual_name}: creating new object")
            return new_local(cls, kwargs[VHDL]) if VHDL in kwargs else new_remote(cls, args, kwargs)
        return __new__  # type: ignore

    # here we make a more accurate `__new__` with the same arguments as the
    # factory, but all are optional, and there is an additional `VHDL` kw arg
    sig = sig.copy()
    sig.key_args = sig.key_args + (VHDL,)
    sig.num_args += 1

    fixed = sig.pos_args + sig.key_args
    sig.optional = set(fixed)
    sig.defaults = dict.fromkeys(fixed, ARG_DEFAULT)

    new_params = '_cls, ' + sig.def_params_str()
    fwd_args_kwargs = sig.forward_args_kwargs_str()
    body = f"return `NEW_LOCAL(_cls, {VHDL}) if {VHDL} else `NEW_REMOTE(_cls, {fwd_args_kwargs})"

    P.nprint(
        ICON_CM,
        f"synthesizing __new__ for ", cls_handle, "; sys_base =", sys_base.__name__,
        f'\n    {qual_name}({new_params}):\n        {body}'
    ) if log else None

    new_func = func_compile(new_params, body, NEW_LOCAL=new_local, NEW_REMOTE=new_remote)
    set_fun_signature(new_func, sig, ARG_DEFAULT)

    return new_func

###############################################################################

def make_virtual_init(qual_name: str, mod: str, sig: Signature) -> FunctionType:

    ident = Identifier('__init__', qual_name, mod)

    if sig is None:
        def init_func(self, *args, **kwargs): pass
        assert isinstance(init_func, FunctionType)
        set_fun_identifier(init_func, ident)
        return init_func

    if bool(LOG_DECR):
        P.nprint(ICON_CM, "making virtual __init__ method")

    sig = sig.copy()
    sig.doc_str = sig.doc_str or ''  # for stub purposes

    # since __init__ *WILL* be called whether we like it or not,
    # we have to deal with the additional argument VHDL arg
    if sig.key_star:
        pass
    elif sig.is_cext:
        sig.key_args = sig.key_args + (VHDL,)
        sig.num_args += 1
        sig.optional.add(VHDL)
        sig.defaults[VHDL] = ...
    else:
        sig.key_star = '___'
        sig.num_args += 1

    init_params = 'self, ' + sig.def_params_str()
    init_func = func_compile(init_params, 'pass')

    set_fun_signature(init_func, sig, ARG_DEFAULT)

    set_fun_identifier(init_func, ident)

    return init_func

###############################################################################

def make_virtual_builtin_new(log: bool, qual_name: str, builtin_cls_handle: ResourceHandle, sys_base: type) -> FunctionType:

    def new_local(cls: type, args, kwargs):
        cont_handle = kwargs[VHDL]
        if log: P.nprint(ICON_C1, f"{qual_name}: creating new local builtin of", cls, "with handle", cont_handle)
        P.nprint(ICON_C1, "creating new local container of class", cls) if log else None
        v_obj = v_empty(sys_base, cls)  # type: ignore
        obj_set(v_obj, VHDL, cont_handle)
        return v_obj

    def new_remote(cls: type, args, kwargs):
        if log: P.nprint(ICON_CM, f"{qual_name}: creating new remote container of class", cls)
        if not kwargs and len(args) == 1:
            seq = args[0]
            seq_cls = type(seq)
            if seq_cls.__flags__ & 256 and seq_cls in ITER_TYPES:
                args = tuple(seq),  # realize any iterator
        v_tuple = builtin_cls_handle.hdlr(builtin_cls_handle, ResourceNew(cls, args, kwargs))
        return v_tuple

    def __new__(cls, *args, **kwargs):
        if log: P.nprint(ICON_CM, f"{qual_name}: creating new container")
        new_fn = new_local if VHDL in kwargs else new_remote
        v_obj = new_fn(cls, args, kwargs)
        return v_obj

    return __new__  # type: ignore

###############################################################################

def make_virtual_metaclass_new(log: bool, qual_name: str, type_class_handle: ResourceHandle) -> FunctionType:

    def new_local(mcls, name, bases, cdict, kwargs):
        P.nprint(ICON_C1, f"{qual_name}: creating new local class of metaclass", mcls) if log else None
        return type.__new__(mcls, name, bases, cdict)

    def new_remote(mcls, name, bases, cdict, kwargs):
        if log: P.nprint(ICON_CM, f"{qual_name}: creating new remote class of metaclass", mcls)
        v_cls = type_class_handle.hdlr(type_class_handle, ResourceNew(mcls, (name, bases, cdict), kwargs))
        # NOTE: when the result is deserialized it will trigger new_local
        return v_cls

    def __new__(mcls: type, name: str, bases: tuple[type, ...] = (), cdict: dict[str, Any] = None, **kwargs: Any):
        new_fn = new_local if VHDL in cdict else new_remote
        v_cls = new_fn(mcls, name, bases, cdict if cdict else None, kwargs)
        return v_cls

    return __new__  # type: ignore

###############################################################################

CLASS_METADATA = NAME, QUALNAME, MODULE, DOC, SATTRS, MATCHARGS

_get_cls_strs = O.attrgetter(NAME, QUALNAME, MODULE, DOC)

def get_class_strings(cls: type) -> tuple[optstr, optstr, optstr, optstr]:

    name, qualname, module, doc = _get_cls_strs(cls)

    qualname = qualname if type(qualname) is str else None
    doc = doc if type(doc) is str else None
    module = module if type(module) is str else None

    if not is_str(name):
        raise E.WarpEncodingError(f"class {cls!r} name {f_object_id(name)} is not a string")

    return name, qualname, module, doc


################################################################################

CLASS_ATTR_WHITELIST = {
    # dataclass
    '__dataclass_fields__'
    '__dataclass_params__'
    # named tuple
    '_fields',
    '_field_defaults',
    '_asdict',
    '_replace',
    # typed dict
    '__required_keys__',
    '__optional_keys__',
    '__total__',
    # enum
    '_member_names_',
    '_member_map_',
    # abc
    '__abstractmethods__',
    # numpy
    '__array_interface__',
    '__array_struct__',
    '__array_namespace__',
}

KNOWN_DUNDER_METHODS = {
    '__array__',  # numpy
    '__abs__',
    '__add__',
    '__aiter__',
    '__aenter__',
    '__aexit__',
    '__and__',
    '__anext__',
    '__await__',
    '__bool__',
    '__buffer__',
    '__call__',
    '__copy__',
    '__cmp__',
    '__contains__',
    '__dataclass_transform__',
    '__delitem__',
    '__delslice__',
    '__div__',
    '__divmod__',
    '__doc__',
    '__enter__',
    '__eq__',
    '__exit__',
    '__fields__',
    '__float__',
    '__floordiv__',
    '__format__',
    '__ge__',
    '__getitem__',
    '__getslice__',
    '__gt__',
    '__hex__',
    '__iadd__',
    '__iand__',
    '__idiv__',
    '__ifloordiv__',
    '__ilshift__',
    '__imod__',
    '__imul__',
    '__index__',
    '__init__',
    '__instancecheck__',
    '__int__',
    '__invert__',
    '__ior__',
    '__ipow__',
    '__irshift__',
    '__isub__',
    '__iter__',
    '__itruediv__',
    '__ixor__',
    '__le__',
    '__len__',
    '__length_hint__',
    '__long__',
    '__lshift__',
    '__lt__',
    '__matmul__',
    '__mod__',
    '__mul__',
    '__ne__',
    '__neg__',
    '__next__',
    '__nonzero__',
    '__oct__',
    '__or__',
    '__pos__',
    '__radd__',
    '__rand__',
    '__rdiv__',
    '__pow__',
    '__rdivmod__',
    '__release_buffer__',
    '__replace__',
    '__repr__',
    '__reversed__',
    '__rfloordiv__',
    '__rlshift__',
    '__rmod__',
    '__rmul__',
    '__ror__',
    '__rpow__',
    '__rrshift__',
    '__rshift__',
    '__rsub__',
    '__rtruediv__',
    '__rxor__',
    '__setitem__',
    '__str__',
    '__sub__',
    '__truediv__',
    '__xor__',
}

UNWARPABLE_DUNDER_METHODS = {
    '__init__',
    '__reduce__',
    '__reduce_ex__',
    '__setstate__',
    '__getstate__',
    '__getnewargs__',
    '__getnewargs_ex__',
    '__init_subclass__',
    '__prepare__',
}

################################################################################

# attach implementations to class
ClassData.describe_resource = staticmethod(describe_real_class)
ClassData.create_resource = create_virtual_class
