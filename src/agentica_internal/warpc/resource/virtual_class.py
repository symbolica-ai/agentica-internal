# fmt: off

import typing
from dataclasses import KW_ONLY
from enum import EnumType
from typing import _TypedDictMeta  # type: ignore
from typing import _ProtocolMeta

from ..msg.term_exception import EXC_NEW_ARGS
from .__ import *
from .base import *
from .handle import is_virtual_class
from .stub_methods import V_CLASS_GETITEM, V_OBJECT_METHODS

__all__ = [
    'ClassData',
]


################################################################################

class ClassData(ResourceData):
    __slots__ = (
        'name', 'qname', 'module', 'doc', 'cls', 'bases', 'methods', 'attrs',
        'sattrs', 'params', 'keys', 'annos',
    )

    FORBIDDEN_FORM = forbidden_class

    name:     str
    qname:    optstr
    module:   optstr
    doc:      optstr
    cls:      ClassT
    bases:    ClassesTupleT
    methods:  MethodsT
    attrs:    AttributesT
    sattrs:   strtup
    params:   Tup[TypeT]
    annos:    AnnotationsT
    keys:     strtup

    # attrs is for class-level attributes whose values ARE recreated locally
    # in the special case of cls = EnumMeta, these class-level attributes will include members
    # of the enumeration, and these are presented as serialized as `EnumMemberData` objects

    # `keys` is for any fields that getattr should work on but ARE NOT present in `methods` or `attrs`
    # these are represent attributes of the class object itself, in other words, if they have
    # corresponding annotations in `annos`, these annotations would be wrapped in ClassVar[...]

    # `sattrs` corresponds to the confusingly-named `__static_attributes__` field, which is what the
    # python compiler populates by finding all the `self.XXX` that occur in methods of a class
    # definition. we reproduce it here, but it is not semantically meaningful for virtualization.

    # implementation attached later
    @classmethod
    def describe_resource(cls, cls_obj: ClassT) -> 'ClassData': ...  # noqa: F841

    # implementation attached later
    def create_resource(self, handle: ResourceHandle) -> ClassT: ...


################################################################################

# TODO: is `__foo__` supposed to be considered private?
def is_private_field(ckey: str) -> bool:
    return ckey.startswith('_')

def describe_real_class(cls: type) -> ClassData:
    data = ClassData()

    assert isinstance(cls, type), f"{f_object_id(cls)} is not a class"

    bases, cdict, name, qname, module, doc = get_cls_attrs(cls)

    qname = qname if type(qname) is str else None
    doc = doc if type(doc) is str else None
    module = module if type(module) is str else None

    if not is_str(name):
        raise E.WarpEncodingError(f"class {cls!r} name {f_object_id(name)} is not a string")

    if not is_tup(bases):
        raise E.WarpEncodingError(f"class {cls!r} bases {f_object_id(bases)} is not a tuple")

    if is_forbidden(cls, module):
        raise E.WarpEncodingForbiddenError(f"<class {cls.__module__}.{cls.__qualname__}'>")

    data.name = name
    data.qname = qname
    data.module = module
    data.doc = doc

    mcls = type(cls)
    data.cls = mcls
    data.bases = bases

    no_priv_fields = flags.OMIT_PRIVATE_FIELDS
    no_priv_annos = flags.OMIT_PRIVATE_ANNOS
    allow_dunders = flags.ALLOW_KNOWN_DUNDER_METHODS

    data.methods, add_meth = mkdict()
    data.attrs, add_attr = mkdict()
    keys = []
    for ckey, cval in cdict.items():
        if ckey in CLS_IGNORE:
            continue
        if ckey.startswith('___'):
            continue
        if no_priv_fields and is_private_field(ckey) and ckey != '__init__':
            if not allow_cls_attr(ckey, allow_dunders):
                continue
        # TODO: we need to treat properties as first-class, this works for now because we have open keys but
        # stub generation is broken because it doesn't know about these properties on the classes.
        if is_property_t(cval):
            continue
        elif is_method_t(cval):
            add_meth(ckey, cval)
        elif ckey in CLASS_ATTR_WHITELIST:
            add_attr(ckey, cval)
        else:
            keys.append(ckey)

    data.keys = tuple(keys)
    data.params = getattr(cls, TPARAMS, ())

    sattrs, annos = multi_get_raw(cls, SATTRS, ANNOS)

    if not is_strtup(sattrs):
        sattrs = ()

    if not is_rec(annos):
        annos = {}

    if sattrs and no_priv_fields:
        sattrs = tuple(s for s in sattrs if not is_private_field(s))

    if annos and no_priv_annos:
        annos = {k: v for k, v in annos.items() if not is_private_field(k) or v is KW_ONLY}

    data.sattrs = sattrs
    data.annos = annos

    return data


################################################################################

def allow_cls_attr(ckey: str, allow_dunders: bool) -> bool:
    if not ckey.startswith('_'):
        return True
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

    if not any_virtual_bases:
        # if no bases at all, or none of the bases are virtual:
        # pick up the virtual versions of __str__, __hash__, etc; subclasses of this virtual
        # class will inherit these, or the true class may override them later in this
        # function, or in a subclass
        cdict.update(V_OBJECT_METHODS)

    # handle is the buried handle that tells us how to do virtual calls
    handle.keys = keys
    handle.open = flags.CLASS_OPEN_KEYS
    handle.name = name

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

    def __new__(cls, *args, **kwargs):
        if len(args) == 1 and type(args[0]) is ResourceHandle:
            base = object
            if issubclass(cls, Exception):
                base = Exception
            elif issubclass(cls, BaseException):
                base = BaseException
            v_obj = base.__new__(cls)
            obj_set(v_obj, VHDL, args[0])
            return v_obj
        v_obj = handle.hdlr(handle, ResourceNew(cls, args, kwargs))
        if issubclass(cls, (BaseException, Exception)):
            object.__setattr__(v_obj, EXC_NEW_ARGS, tuple(args))
        return v_obj

    # VIRTUAL METHODS ==========================================================

    # add methods
    for k, m in data.methods.items():
        add(k, m)

    add('__new__', __new__)

    # ATTRIBUTES ===============================================================

    # add (real) non-method attributes
    for k, a in data.attrs.items():
        add(k, a)

    # METADATA =================================================================

    # add metadata
    add(VHDL, handle)
    add(QUALNAME, qname)
    add(MODULE, data.module)
    add(DOC, data.doc)
    add(SATTRS, data.sattrs)
    add(ANNOS, data.annos)
    add(TPARAMS, data.params)

    # CLASS HIERARCHY ==========================================================

    bases = tuple(b for b in data.bases if b not in EXCLUDE_BASES)

    if data.params:
        # this allows (virtual) MyClass[int] to resolve to a typing._GenericAlias locally
        add('__class_getitem__', V_CLASS_GETITEM)

    mcls = data.cls

    # CLASS CREATION ===========================================================

    error: TypeError | None = None
    try:
        if mcls is _ProtocolMeta:
            cdict['_is_protocol'] = True
            cdict['_is_runtime_protocol'] = True

        if typing.Protocol in bases and any(not issubclass(b, typing.Protocol) for b in bases):
            bases = tuple(b for b in bases if b is not typing.Protocol)

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
            cls_set(v_cls, key, v_attr)
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

HEAP_CLASS = 1 << 9

get_cls_attrs = O.attrgetter(BASES, DICT, NAME, QUALNAME, MODULE, DOC)

CLS_REQUIRED = (
    BASES,
    DICT,
    NAME,
    QUALNAME,
    MODULE,
    DOC,
)
CLS_OPTIONAL = SATTRS, ANNOS
CLS_INTERNAL = WEAKREF, FSTLINE, SLOTS
CLS_HOOKED = '__str__', '__repr__', '__hash__', '__getattr__', '__setattr__', '__delattr__'
CLS_IGNORE = CLS_REQUIRED + CLS_OPTIONAL + CLS_INTERNAL + CLS_HOOKED

EXCLUDE_BASES = [T.Generic]

################################################################################

# attach implementations to class
ClassData.describe_resource = staticmethod(describe_real_class)
ClassData.create_resource = create_virtual_class
