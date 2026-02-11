# fmt: off

from typing import ClassVar, TypeGuard, Self
from collections.abc import Callable

from .hashing import raw_str_hash

__all__ = [
    'Sentinel',
    'NoValue',
    'FalseSentinel',
    'ArgDefault',
    'FieldAbsent',
    'OnDemand',
    'Pending',
    'Closed',
    'Canceled',
    'Errored',
    'NO_VALUE',
    'ARG_DEFAULT',
    'FIELD_ABSENT',
    'ON_DEMAND',
    'CLOSED',
    'PENDING',
    'CANCELED',
    'ERRORED',
    'SENTINEL_TYPES',
    'SENTINEL_IDS',
    'SENTINEL_OBJS',
    'SENTINELS',
    'is_sentinel',
    'getter'
]

###############################################################################

SENTINELS: dict[str, 'Sentinel'] = {}

SENTINEL_TYPES = set()
SENTINEL_IDS = set()
SENTINEL_OBJS = set()

class Sentinel:
    __slots__ = ('__hash_value__',)

    hval: ClassVar[int]
    name: ClassVar[str]
    caps: ClassVar[str]
    inst: ClassVar['Sentinel']

    def __init_subclass__(cls, name: str, caps: str | None = None):
        cls.name = name
        cls.inst = inst = object.__new__(cls)
        cls.caps = caps or name
        cls.hval = raw_str_hash(name) ^ 0x1234
        inst.__hash_value__ = cls.hval
        SENTINEL_TYPES.add(cls)
        SENTINEL_IDS.add(id(inst))
        SENTINEL_OBJS.add(inst)
        SENTINELS[name] = inst

    def __new__(cls):
        return cls.inst

    def __repr__(self) -> str:
        return type(self).name

    def __hash__(self) -> int:
        return self.__hash_value__

    def __eq__(self, other) -> bool:
        return self is other

    def __ne__(self, other) -> bool:
        return self is not other

    def const(self) -> Callable[..., Self]:
        return lambda *_, **__: self

    def replace_with(self, new) -> Callable[[object], object]:
        return lambda x: new if x is self else x

    __short_str__ = __repr__


###############################################################################

class FalseSentinel(Sentinel, name=''):

    def __bool__(self) -> bool:
        return False

###############################################################################

class NoValue(FalseSentinel,     name='NO_VALUE'): ...
class ArgDefault(FalseSentinel,  name='...', caps='ARG_DEFAULT'): ...
class FieldAbsent(FalseSentinel, name='FIELD_ABSENT'): ...
class Pending(FalseSentinel,     name='PENDING'): ...
class Closed(FalseSentinel,      name='CLOSED'): ...
class Canceled(FalseSentinel,    name='CANCELED'): ...
class Errored(FalseSentinel,     name='ERRORED'): ...
class OnDemand(FalseSentinel,    name='ON_DEMAND'): ...

NO_VALUE     = NoValue()
ARG_DEFAULT  = ArgDefault()
FIELD_ABSENT = FieldAbsent()
PENDING      = Pending()
CLOSED       = Closed()
CANCELED     = Canceled()
ERRORED      = Errored()
ON_DEMAND    = OnDemand()

###############################################################################

# for emulating dict.get
def getter[K, V, D](dct: dict[K, V] | None, default: D = NO_VALUE) -> Callable[[K], V | D]:
    if dct: return lambda k: dct.get(k, default)
    else:   return lambda k: default

###############################################################################

# this doesn't work, for some reason...
# def none_schema(cls, source_type, handler):
#     from pydantic_core import core_schema
#     return core_schema.none_schema()
#
# ArgDefault.__get_pydantic_core_schema__ = classmethod(none_schema)
#
# ensure that virtualized functions with foo=ARG_DEFAULT are understood by
# pydantic

###############################################################################

is_sentinel_id = SENTINEL_IDS.__contains__


def is_sentinel(obj) -> TypeGuard[Sentinel]:
    return is_sentinel_id(id(obj))
