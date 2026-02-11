# fmt: off

from enum import EnumType, Enum, IntEnum, StrEnum, ReprEnum, Flag, IntFlag

from .__ import *
from .base import *

__all__ = [
    'EnumType',
    'EnumKind',
    'EnumClassData',
]


################################################################################

type EnumKind = Literal['any', 'int', 'str', 'repr', 'flag', 'intflag']

class EnumClassData(ResourceData):
    __slots__ = 'kind', 'name', 'qualname', 'module', 'members', 'methods'

    KIND = Kind.Class
    FORBIDDEN_FORM = forbidden_class

    kind:     EnumKind
    name:     str
    qualname: optstr
    module:   optstr
    members:  AttributesT
    methods:  MethodsT

    # implementation attached later
    @classmethod
    def describe_resource(cls, enum_cls: EnumType) -> 'EnumClassData': ...

    # implementation attached later
    def create_resource(self, handle: ResourceHandle) -> EnumType: ...


################################################################################

_KINDS: list[EnumKind] = ['any', 'int', 'str', 'repr', 'flag', 'intflag']
_TYPES: list[EnumType] = [Enum, IntEnum, StrEnum, ReprEnum, Flag, IntFlag]

_TO_KIND: dict[EnumType, EnumKind] = dict(zip(_TYPES, _KINDS))
_TO_TYPE: dict[EnumKind, EnumType] = dict(zip(_KINDS, _TYPES))

################################################################################

def describe_real_enum_class(enum_cls: EnumType) -> EnumClassData:

    data = EnumClassData()
    data.kind = 'any'

    for base in enum_cls.__mro__:
        if kind := _TO_KIND.get(base):  # type: ignore
            data.kind = kind
            break

    name = enum_cls.__name__
    qualname = enum_cls.__qualname__
    module = enum_cls.__module__

    data.name = name
    data.qualname = qualname if qualname != name else None
    data.module = module
    data.methods = {}  # for now

    data.members = {k: v._value_ for k, v in enum_cls.__members__.items()}

    return data


################################################################################

def create_virtual_enum_class(data: EnumClassData, handle: ResourceHandle) -> ObjectT:

    handle.kind = Kind.Enum
    handle.keys = []
    handle.open = True
    handle.name = f'<{data.name!r} enum>'

    enum_type = _TO_TYPE[data.kind]

    v_cls = EnumType.__call__(
        enum_type, data.name,
        names=data.members, module=data.module, qualname=data.qualname
    )

    # TODO: attach methods

    return v_cls

################################################################################

EnumClassData.describe_resource = staticmethod(describe_real_enum_class)
EnumClassData.create_resource = create_virtual_enum_class
