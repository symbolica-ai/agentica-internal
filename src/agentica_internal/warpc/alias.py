# fmt: off

from typing import Callable, Any, Literal

__all__ = [
    'Tup',
    'Rec',
    'Fn',
    'VarScope',
    'SendBytes',
    'EncodeFmt',
    'DecodeFmt',
    'MethodKind',
    'AsyncMode',
    'HashMode',
    'Options',
    'optstr',
    'optint',
    'strtup',
    'strlist',
    'typetup',
    'record',
    'Name',
    'DocStr',
    'Ptr',
    'ID',
    'WorldID',
    'LocalRID',
    'GlobalRID',
    'ResourceUID',
    'FrameKey',
    'SystemRID',
    'FrameID',
    'MessageID',
    'FutureID'
]

################################################################################

type optstr       = str | None
type optint       = int | None
type strtup       = tuple[str, ...]
type strlist      = list[str]
type typetup      = tuple[type, ...]
type record       = dict[str, Any]

type Tup[V]       = tuple[V, ...]
type Rec[V]       = dict[str, V]

type Fn[*X, Y]    = Callable[[*X], Y]
type SendBytes    = Callable[[bytes], None]

type VarScope     = Literal['locals', 'globals']
type TermFmt      = Literal['full', 'type', 'json', 'schema', 'raw']
type EncodeFmt    = TermFmt
type DecodeFmt    = TermFmt

type DocStr       = str | None

type MethodKind   = Literal['instance', 'class', 'static', None]

type AsyncMode    = Literal['coro', 'future', 'sync', None]  # None means 'use server default'
type HashMode     = Literal['id', 'user', None]
type Options      = dict[str, bool | int | str | float | None]

################################################################################

type Name         = str
type Ptr          = int    # the result of id(...)
type ID           = int    # natural number starting at 0
type UUID         = int    # effectively random integer
type WorldID      = UUID   # this is a UUID based on hash of MAC address
type FrameID      = UUID
type LocalRID     = Ptr
type SystemRID    = ID
type MessageID    = ID
type FutureID     = str | int

################################################################################

# global resource id: the originating world, its frame, and ID there
type GlobalRID    = tuple[WorldID, FrameID, LocalRID]

type ResourceUID  = GlobalRID | SystemRID

# the virtualizing world, its frame, for lookup in servicing requests
type FrameKey     = tuple[WorldID, FrameID]
