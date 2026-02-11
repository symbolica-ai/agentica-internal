# fmt: off

from ..system import LRID_TO_SRID, SRID_TO_CLS, SRID_TO_NAME, SRID_TO_RSRC
from .__ import *
from .term import TermPassByRefMsg

__all__ = [
    'ResourceMsg',
    'UserResourceMsg',
    'SystemResourceMsg',
    'RemoteResourceMsg',
    'LocalResourceMsg',
    'pointer_to_system_msg',
    'class_to_system_msg',
    'class_to_system_id',
]


################################################################################

# for now, these are not distinguished on the wire, but it is helpful
# for documenting what we expect in various places

type RemoteResourceMsg = ResourceMsg
type LocalResourceMsg = ResourceMsg

################################################################################

class ResourceMsg(TermPassByRefMsg):
    type V = ResourceT

    def decode(self, dec: DecoderP) -> ResourceT:
        return dec.dec_resource(self)

    @property
    def as_ref(self) -> 'ResourceMsg':
        return self

    @property
    def uid(self) -> ResourceUID:
        return NotImplemented()


################################################################################

class UserResourceMsg(ResourceMsg, tag='ref'):

    """ABC for messages describing or referencing previously described resource terms."""

    __debug_fmt_slots__ = False

    rid: GlobalRID

    @property
    def as_ref(self) -> 'UserResourceMsg':
        return self

    def __shape__(self) -> str:
        return f_grid(self.rid)

    def __debug_info_str__(self) -> str:
        rid = getattr(self, 'rid', None)
        if type(rid) is tuple:
            return 'rid=' + f_grid(self.rid)
        return ''

    def repr(self, deep: bool = True) -> str:
        return f'ResourceRefMsg({f_grid(self.rid)})'

    def __rich_repr__(self):
        yield f_grid(self.rid)

    ############################################################################

    @property
    def uid(self) -> ResourceUID:
        return self.rid

    def __trans_int_uid__(self) -> int:
        return self.rid[2]


################################################################################

class SystemResourceMsg(ResourceMsg, tag='sys'):

    __debug_fmt_slots__ = False

    sid: SystemRID

    def __repr__(self):
        return f'SystemResourceMsg(sid={f_id(self.sid)},res={self.sys_name})'

    def __debug_info_str__(self) -> str:
        sid = getattr(self, 'sid', None)
        return f"'{self.sys_name}'" if type(sid) is int else ''

    @property
    def as_ref(self) -> 'SystemResourceMsg':
        return self

    @property
    def sys_cls(self) -> type:
        return _get_class(self.sid, object)

    @property
    def sys_resource(self) -> type:
        return _get_resource(self.sid)

    @property
    def sys_name(self) -> str:
        return _get_name(self.sid) or f_id(self.sid)

    def __shape__(self) -> str:
        return self.sys_name

    def __rich_repr__(self):
        yield self.sid
        yield self.sys_name

    ############################################################################

    @property
    def uid(self) -> ResourceUID:
        return 0, 0, -self.sid

    def __trans_int_uid__(self) -> int:
        return -self.sid


_get_name = SRID_TO_NAME.get
_get_class = SRID_TO_CLS.get
_get_resource = SRID_TO_RSRC.__getitem__

################################################################################

class SysMsgCache(dict[Ptr, SystemResourceMsg]):

    def __missing__(self, ptr: Ptr) -> SystemResourceMsg:
        return SystemResourceMsg(LRID_TO_SRID[ptr])

SYS_MSG_CACHE = SysMsgCache()


################################################################################

def class_to_system_id(cls: type) -> SystemRID:
    return pointer_to_system_id(id(cls))

def class_to_system_msg(cls: object) -> SystemResourceMsg:
    return pointer_to_system_msg(id(cls))

################################################################################

def pointer_to_system_id(ptr: Ptr) -> SystemResourceMsg:
    ...

def pointer_to_system_msg(ptr: Ptr) -> SystemResourceMsg:
    ...

pointer_to_system_id  = LRID_TO_SRID.__getitem__   # type: ignore
pointer_to_system_msg = SYS_MSG_CACHE.__getitem__  # type: ignore
