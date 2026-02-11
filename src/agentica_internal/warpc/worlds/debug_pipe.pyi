# fmt: off

from collections.abc import Callable
from typing import TypeVar, overload

from .debug_world import DebugWorld

from ..resource.all import ResourceData
from ..msg.all import ChannelMsg, RPCMsg
from ..events import Event, OutgoingFrameExit

__all__ = [
    'Pipe',
]


################################################################################

Type = TypeVar('Type', bound='type')
Return = TypeVar('Return', bound='object')
Object = TypeVar('Object', bound='object')
Function = TypeVar('Function', bound=Callable)

################################################################################

class Pipe:

    src: DebugWorld
    dst: DebugWorld

    last_event: Event
    last_frame: OutgoingFrameExit
    last_rdata: ResourceData
    last_piped: ChannelMsg
    last_msg:   RPCMsg

    all_events:   list[Event]
    all_frames:   list[OutgoingFrameExit]
    all_rdata:    list[ResourceData]
    all_piped:    list[ChannelMsg]
    all_msgs:     list[RPCMsg]

    def __init__(self, src: DebugWorld, dst: DebugWorld):
        self.src = src
        self.dst = dst

    @overload
    async def __call__[T](self, real: T, /) -> T:
        return real

    def print_events(self) -> None: ...
    def pprint_events(self) -> None: ...
