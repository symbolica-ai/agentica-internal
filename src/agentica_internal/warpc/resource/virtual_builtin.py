# fmt: off

from ...core.type import C_CALLABLES, UnboundDunderMethodC, UnboundMethodC

from ..data.identifier import Identifier, set_fun_identifier
from ..data.signature import get_signature
from ..data.signature_compile import sig_compile

from .__ import *
from .base import *
from .virtual_class import allow_cls_attr, choose_system_base
from .vbuiltins.vmethods import v_empty
from .vbuiltins import virtual_base_methods

__all__ = [
    'virtual_builtin_class',
    'create_virtual_builtin_object',
]


################################################################################

def create_virtual_builtin_object(cls: type, handle: ResourceHandle) -> object:
    log = bool(LOG_DECR)
    v_cls = virtual_builtin_class(cls)
    if log: P.nprint(ICON_C0, 'create_virtual_builtin_object of builtin', cls, 'and proxy cls', v_cls)
    v_obj = v_cls(**{VHDL: handle})  # uses new_fn, see below
    if log: P.nprint(ICON_C0, 'created virtual builtin object', v_obj)
    return v_obj


################################################################################

def create_virtual_builtin_class(cls: type) -> type:
    """
    This is to satisfy the case that a ObjectData message comes in whose
    class is a *system* class. E.g. an anonymous virtual builtin object.

    This creates a class with the same signature as a builtin class, but whose
    instance methods and instance properties cause RPC to happen. It assumes
    the 'self' argument is an object created with `create_virtual_builtin_object`.

    This is useful for creating virtual objects that should *appear* to be instances
    of known builtin classes (e.g. `asyncio.Queue`).

    They will not satisfy `isinstance`, however.
    """

    sys_base = choose_system_base((cls,))

    log = bool(LOG_DECR)
    if log: P.nprint(ICON_C0, 'create_virtual_builtin_class', cls, 'with sys_base =', sys_base.__name__)

    methods, add_meth = mkset()
    properties, add_prop = mkset()
    for base in cls.__mro__:
        dct = cls_dict(base)
        for k, v in dct.items():
            if k.startswith('_'):
                if k == '__init__':
                    continue
                if not allow_cls_attr(k, True):
                    continue
            if is_method_t(v) or type(v) in C_CALLABLES:
                add_meth(k)
            elif is_property_t(v):
                add_prop(k)
            else:
                pass
                # P.nprint(ICON_M, 'skipping', k, 'of type', type(v))

    cdict = {}
    methods = list(methods)
    methods.sort()

    sys_proxies, _ = virtual_base_methods(sys_base)

    cdict.update(sys_proxies)
    if log:
        for name, proxy in sys_proxies.items():
            P.nprint(ICON_M, 'sys_method', name, proxy)

    for method_name in methods:
        if method_name in cdict: continue
        if log: P.nprint(ICON_M, 'method', method_name)
        method = getattr(cls, method_name)
        qual_name = getattr(method, '__qualname__', None)
        if proxy_method := create_proxy_method(method_name, qual_name, method):
            cdict[method_name] = proxy_method

    for property_name in properties:
        if property_name in cdict: continue
        if log: P.nprint(ICON_M, 'property', property_name)
        proxy_property = create_proxy_property(property_name)
        cdict[property_name] = proxy_property

    # ensure this class warps as the original
    def __class_warp_as__(_cls):
        return cls

    cdict[CLASS_WARP_AS] = classmethod(__class_warp_as__)

    name = cls.__name__
    doc = cls.__doc__
    module = cls.__module__
    qualname = cls.__qualname__
    doc = doc if isinstance(doc, str) else None
    module = module if isinstance(module, str) else module
    qualname = qualname if isinstance(qualname, str) else name

    # allow construction from remote object (via hidden VHDL= kwarg)
    def new_fn(cls, *args, **kwargs):
        if log:
            P.nprint(ICON_M, f'{qualname}.__new__', args, kwargs)
        if handle := kwargs.get(VHDL):
            v_obj = v_empty(sys_base, cls)
            obj_set(v_obj, VHDL, handle)
            return v_obj
        raise TypeError(f"Cannot create instances of the {qualname} in this environment")
    set_fun_identifier(new_fn, Identifier('__new__', qualname, module))
    cdict['__new__'] = new_fn

    def init_fn(self, *args, **kwargs):
        pass

    set_fun_identifier(init_fn, Identifier('__init__', qualname, module))
    cdict['__init__'] = init_fn

    v_cls = type(name, (sys_base,), cdict)
    v_cls.__qualname__ = qualname
    v_cls.__module__ = module
    v_cls.__doc__ = doc

    if log: P.nprint(ICON_C1, 'created proxy class', v_cls)
    return v_cls


def create_proxy_property(property_name: str) -> property:

    def proxy_get(self):
        handle = obj_get(self, VHDL)
        return handle.hdlr(handle, ResourceGetAttr(self, property_name))

    prop = property(fget=proxy_get)
    return prop


def create_proxy_method(method_name: str, qual_name: str, method: MethodT) -> MethodT | None:

    if isinstance(method, (FunctionType, UnboundMethodC, UnboundDunderMethodC)):

        ident = Identifier(method_name, qual_name)

        sig = get_signature(method)
        body = f'''
        HANDLE = object.__getattribute__(self, {VHDL!r})
        return HANDLE.hdlr(HANDLE, `REQUEST(self, {method_name!r}, `METHOD_ARGS_KWARGS))'''

        return sig_compile(ident, sig, body, no_def=ARG_DEFAULT, REQUEST=ResourceCallMethod)

    elif isinstance(method, (staticmethod, classmethod)):
        return method

    else:
        return None

################################################################################

class VirtualBuiltinClassCache(dict[type, type]):
    def __missing__(self, key: type):
        self[key] = cls = create_virtual_builtin_class(key)
        return cls


VIRTUAL_BUILTIN_CLASS_CACHE = VirtualBuiltinClassCache()


def virtual_builtin_class(cls: type) -> type: ...

virtual_builtin_class = VIRTUAL_BUILTIN_CLASS_CACHE.__getitem__  # type: ignore
