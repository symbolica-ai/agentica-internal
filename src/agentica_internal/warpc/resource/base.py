# fmt: off

from types import NoneType, EllipsisType, NotImplementedType

from ..system import sanitize_path

from .__ import *
from .handle import ResourceHandle, get_handle

__all__ = [
    'ResourceData',
    'ResourceHandle',
    'get_handle',
    'is_cheap',
    'sanitize_path'
]

################################################################################

class ResourceData:
    __slots__ = ()

    KIND: ClassVar[Kind] = Kind.Unknown
    STR_NAME: ClassVar[str]
    FORBIDDEN_FORM: ClassVar[ResourceT] = forbidden_object
    MSG_CLS: ClassVar['type[ResourceDataMsg]']
    MIGHT_ALIAS: ClassVar[bool] = False

    def encode(self, enc: EncoderP) -> 'ResourceDataMsg':
        cls = type(self)
        msg_cls = cls.MSG_CLS
        kwargs = msg_cls.encode_fields(self, enc)
        for key in msg_cls.__struct_fields__:
            if key not in kwargs:
                kwargs[key] = getattr(self, key)
        msg = msg_cls(**kwargs)
        return msg

    def repr(self):
        cls = type(self)
        if hasattr(cls, SLOTS):
            dct = {}
            for slot in cls.__slots__:
                dct[slot] = getattr(self, slot, FIELD_ABSENT)
        else:
            dct = self.__dict__
        f_args = ', '.join(f'{k}={f_slot(k, v)}' for k, v in dct.items())
        return f'{cls.__name__}({f_args})'

    __str__ = repr
    __repr__ = repr

    def short_str(self) -> str:
        cls_name = type(self).__name__
        name = getattr(self, 'name', '...')
        return f'{cls_name}({name})'

    def pprint(self, err: bool = False):
        from ...core.fmt import f_slot_obj
        P.rprint(f_slot_obj(self), err=err)

    @classmethod
    def describe_resource(cls, resource: ResourceT, /) -> 'ResourceData': ...

    def create_resource(self, handle: 'ResourceHandle', /) -> ResourceT: ...

    @classmethod
    def forbidden_msg(cls) -> 'SystemResourceMsg':
        from ..msg.term_resource import SystemResourceMsg
        from ..system import LRID_TO_SRID
        forb_cls = cls.FORBIDDEN_FORM
        forb_sid = LRID_TO_SRID[id(forb_cls)]
        return SystemResourceMsg(forb_sid)

    def rename(self, tmpl: str | None, grid: GlobalRID) -> None:
        if tmpl and hasattr(self, 'name'):
            f_kind = type(self).__name__.removesuffix('Data')
            wid, fid, lid = grid
            name = tmpl.format(rsrc_name=self.name, rsrc_kind=f_kind, wid=wid, fid=fid, lid=lid)
            setattr(self, 'name', name)
            if type(getattr(self, 'qname', None)) is str:
                setattr(self, 'qname', name)

################################################################################

def is_cheap(obj: Any) -> bool:
    cls = type(obj)
    if cls in CHEAP_TYPES: return True
    if cls in STR_TYPES: return len(obj) < 64
    from ..system import SYSTEM_IDS
    if id(obj) in SYSTEM_IDS: return True
    if cls in SEQ_TYPES and len(obj) < 8:
        return all(is_cheap(o) for o in obj)
    if cls is dict and len(obj) < 8:
        return all(is_cheap(k) for k in obj.keys()) and all(is_cheap(k) for k in obj.values())
    return False

################################################################################

STR_TYPES = str, bytes
SEQ_TYPES = tuple, list, set, frozenset
CHEAP_TYPES = int, float, NoneType, EllipsisType, NotImplementedType
