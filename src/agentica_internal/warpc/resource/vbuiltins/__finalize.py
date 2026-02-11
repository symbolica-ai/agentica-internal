# fmt: off

from types import FunctionType
from agentica_internal.cpython.class_info import get_builtin_base

from ... import flags
from . import classes
from .vmethods import V_EMPTY

__all__ = [
    'SystemBase',
    'VirtualBase',
    'virtual_base',
    'virtual_base_methods',
    'choose_system_base',
]

################################################################################

type SystemBase = type   # one of object, type, bool, date, etc.
type VirtualBase = type  # one of _object, _type, _bool, _date, etc.

def virtual_base(cls: SystemBase) -> VirtualBase:
    return SBASE_TO_VBASE.get(cls, classes._object)

################################################################################

type Methods = dict[str, FunctionType]

V_BASE_METHODS: dict[SystemBase, tuple[Methods, Methods]] = {}

def virtual_base_methods(s_base: SystemBase) -> tuple[Methods, Methods]:

    if s_base in V_BASE_METHODS:
        return V_BASE_METHODS[s_base]

    v_base = virtual_base(s_base)

    methods = {}
    specials = {}
    V_BASE_METHODS[s_base] = (methods, specials)
    o_name = v_base.__name__
    n_name = o_name.removeprefix('_')
    v_base.__name__ = n_name
    v_base.__module__ = 'builtins'
    for k, v in v_base.__dict__.items():
        if k == '__new__':
            V_EMPTY[s_base] = v
            continue
        c = None
        if isinstance(v, (classmethod, staticmethod)):
            c = type(v)
            v = v.__func__
        if isinstance(v, FunctionType):
            if hasattr(v, '__is_dummy__'):
                continue
            q_name = v.__qualname__
            if q_name.startswith(o_name):
                v.__qualname__ = q_name.removeprefix('_')
        elif isinstance(v, property):
            pass
        else:
            continue
        if hasattr(v, '__special__'):
            specials[k] = v
        else:
            methods[k] = c(v) if c else v

    if not flags.VIRTUAL_OBJECT_DUNDER_DICT:
        methods.pop('__getattribute__', None)

    return methods, specials

################################################################################

def choose_system_base(bases: tuple[type, ...]) -> SystemBase:
    # this is what determines what methods get layered on, and what the system
    # type's __new__ will be called to instantiate a 'blank' virtual object
    # that serves as the local instance of a remote-hosted instance

    for cls in bases:
        # this uses flags, so it's fast
        s_base = get_builtin_base(cls)
        if s_base is not object:
            return s_base

    for cls in bases:
        for s_base in SBASES:
            if issubclass(cls, s_base):
                return s_base

    for cls in bases:
        for s_base, test_bases in FALLBACKS:
            if issubclass(cls, test_bases):
                return s_base

    return object


################################################################################

SBASES:         list[type] = []
SBASE_TO_VBASE: dict[type, type] = {}
FALLBACKS:      list[tuple[type, tuple[type, ...]]] = []

def initialize():
    from collections.abc import Iterator
    from ....cpython.iters import ITER_TYPES
    from . import classes

    SBASE_TO_VBASE.clear()
    SBASES.clear()
    FALLBACKS.clear()

    for name in classes.__all__:
        v_base: type = getattr(classes, name)
        s_base: type = v_base.__bases__[0]
        SBASE_TO_VBASE[s_base] = v_base
        SBASES.append(s_base)

    SBASES.remove(object)
    SBASES.remove(Iterator)
    SBASES.sort(key=lambda t: -len(t.__mro__))

    FALLBACKS.append((Iterator, ITER_TYPES))
    FALLBACKS.append((Exception, (Exception,)))
    FALLBACKS.append((BaseException, (BaseException,)))

initialize()
del initialize
