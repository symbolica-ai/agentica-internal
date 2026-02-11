# fmt: off

from types import ModuleType, MethodType
from .exceptions import ForbiddenError

__all__ = [
    'is_forbidden',
    'blacklist_modules',
    'whitelist_modules',
    'whitelist_objects',
    'forbidden_class',
    'forbidden_object',
    'forbidden_function',
    'forbidden_module',
    'ForbiddenError',
]

################################################################################

BLACKLIST_MODULES = 'agentica_internal.warpc.', 'virtual.', 'agentica.', 'ctypes.', '_ctypes.'
WHITELIST_MODULES = 'agentica_internal.testing.',
WHITELIST_OBJECTS: set[int] = set()

################################################################################

def blacklist_modules(*mod_names: str) -> None:
    global BLACKLIST_MODULES
    BLACKLIST_MODULES = tuple(set(BLACKLIST_MODULES + mod_names))

def whitelist_modules(*mod_names: str) -> None:
    global WHITELIST_MODULES
    WHITELIST_MODULES = tuple(set(WHITELIST_MODULES + mod_names))

def whitelist_objects(*objs: object) -> None:
    add = WHITELIST_OBJECTS.add
    for obj in objs:
        if type(obj) is MethodType:
            cls, fun = obj.__self__, obj.__func__
            add(id(cls))
            add(id(fun))
        else:
            add(id(obj))

def is_forbidden(obj: object, mod_name: str | None) -> bool:
    return (
        type(mod_name) is str and
        mod_name.startswith(BLACKLIST_MODULES) and
        not mod_name.startswith(WHITELIST_MODULES) and
        id(obj) not in WHITELIST_OBJECTS
    )

################################################################################

fobj = '<forbidden object>'
fcls = '<forbidden class>'
ffun = '<forbidden function>'
fmod = '<forbidden module>'
ffil = '<forbidden file>'


class forbidden_class:
    def __init__(self, *args, **kwargs) -> None:
        raise ForbiddenError('tried to instantiate a forbidden class')

    def __init_subclass__(cls, **kwargs):
        raise ForbiddenError('tried to subclass a forbidden class')

    def __class_getitem__(cls, item):
        raise ForbiddenError('tried to parameterize a forbidden class')

    def __getattr__(self, name: str):
        raise ForbiddenError('tried to get an attribute on a forbidden object')

    def __setattr__(self, name: str, value) -> None:
        raise ForbiddenError('tried to set an attribute on a forbidden object')

    def __delattr__(self, name: str):
        raise ForbiddenError('tried to delete an attribute on a forbidden object')

    def __str__(self) -> str:
        return fobj

    def __repr__(self) -> str:
        return fobj


forbidden_class.__name__ = forbidden_class.__qualname__ = fcls
forbidden_class.__module__ = fmod

################################################################################

forbidden_object = object.__new__(forbidden_class)

################################################################################


def forbidden_function(*args, **kwargs):
    raise ForbiddenError('tried to call a forbidden function')


forbidden_function.__code__ = forbidden_function.__code__.replace(co_name=ffun, co_qualname=ffun)
forbidden_function.__name__ = forbidden_function.__qualname__ = ffun
forbidden_function.__module__ = fmod
forbidden_function.__file__ = ffil

################################################################################


class ForbiddenModule(ModuleType):
    def __getattr__(self, name: str):
        raise ForbiddenError('tried to get an attribute on a forbidden module')

    def __setattr__(self, name: str, value) -> None:
        raise ForbiddenError('tried to set an attribute on a forbidden module')

    def __delattr__(self, name: str):
        raise ForbiddenError('tried to delete an attribute on a forbidden module')

    def __dir__(self):
        return []


forbidden_module = ModuleType(fmod)
forbidden_module.__file__ = ffil
