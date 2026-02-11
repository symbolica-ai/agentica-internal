# fmt: off

from ..core import print as P

from collections.abc import Iterable
from enum import IntEnum
from typing import TypeVar, NamedTuple, Self, ClassVar, TYPE_CHECKING


__all__ = [
    'Tick',
    'EventNumber',
    'Nanoseconds',
    'f_tick',
    'Direction',
    'Incoming',
    'Outgoing',
    'EventType',
    'SimpleEvent',
    'Event',
    'FrameEvent',
    'FrameEnterEvent',
    'OutgoingFrameEnter',
    'IncomingFrameEnter',
    'FrameExitEvent',
    'OutgoingFrameExit',
    'IncomingFrameExit',
    'ResourceEvent',
    'DescribeResource',
    'CreateResource',
    'ChannelEvent',
    'ChannelSend',
    'ChannelReceive',
    'EventEvent',
    'IncomingEvent',
    'OutgoingEvent',
    'RPCEvent',
    'OutgoingRPC',
    'IncomingRPC',
]


################################################################################

if TYPE_CHECKING:
    from .msg.all import EventMsg, FramedRequestMsg, FramedResponseMsg, \
        TermMsg, ExceptionMsg, DefinitionMsg, RequestMsg, ResultMsg, ChannelMsg
    from .resource.base import ResourceData, FunctionDataMsg, ClassDataMsg

################################################################################

type EventNumber = int
type Nanoseconds = int
type Tick      = tuple[EventNumber, Nanoseconds]

def f_tick(tick: Tick, just: int = 0) -> str:
    from ..core.fmt import f_nanos_time
    # e.g. 324, 14:30:45.123456789
    logical, nanos = tick
    f_time = str(logical)
    if just: f_time = f_time.ljust(just)
    f_nanos = f_nanos_time(tick[1])
    return f'{f_nanos} #{f_time}'

################################################################################

type EventType = type[Event]

class Direction(IntEnum):
    Incoming = 1
    Outgoing = 0

Incoming = Direction.Incoming
Outgoing = Direction.Outgoing

################################################################################

class SimpleEvent(NamedTuple):
    tick: Tick
    type: EventType

    def __repr__(self) -> str:
        return f'{self.tick:<3}\t{self.type.cls_name})'

    __str__ = __repr__

################################################################################

E = TypeVar('E', bound='Event')

class Event:
    __slots__ = 'tick',
    __icon__: ClassVar[str]

    INCOMING: ClassVar[EventType]
    OUTGOING: ClassVar[EventType]

    tick: Tick

    @property
    def cls_name(self) -> str:
        return type(self).__name__

    def short_str(self) -> str:
        short_args = ', '.join(self.__short_args__())
        return f"{self.cls_name}({self.tick}, {short_args})"

    def __str__(self) -> str:
        return self.short_str()

    def line_str(self) -> str:
        line_args = '\t'.join(self.__line_args__())
        tick = f_tick(self.tick, 5)
        return f"{tick}{self.__icon__:<3} {line_args}"

    def __lt__(self, other: Self) -> bool:
        return self.tick < other.tick

    def __le__(self, other: Self) -> bool:
        return self.tick <= other.tick

    def __short_args__(self) -> Iterable[str]: ...

    def __line_args__(self) -> Iterable[str]: ...

    def pprint(self):
        from agentica_internal.core.fmt import f_slot_obj
        P.oprint(f_slot_obj(self))

    @classmethod
    def dir(cls: type[E], d: Direction) -> type[E]:
        return cls.INCOMING if d else cls.OUTGOING

    ################################################################################

    # deconstructors

    def request_msg(self) -> 'RequestMsg | None':
        from .msg.all import FramedRequestMsg
        match self:
            case OutgoingFrameExit(request=FramedRequestMsg(request=msg)): return msg
        return None

    def result_msg(self) -> 'ResultMsg | None':
        from .msg.all import FramedResponseMsg
        match self:
            case OutgoingFrameExit(response=FramedResponseMsg(result=msg)): return msg
        return None

    def return_value_msg(self) -> 'TermMsg | None':
        if result := self.result_msg():
            if result.done:
                return result.value
        return None

    def raised_exception_msg(self) -> 'ExceptionMsg | None':
        if result := self.result_msg():
            if result.done:
                return result.error
        return None

    def request_definition_msgs(self) -> 'tuple[DefinitionMsg, ...] | None':
        match self:
            case OutgoingFrameExit(request=FramedRequestMsg(defs=msgs)): return msgs
        return None

    def response_definition_msgs(self) -> 'tuple[DefinitionMsg, ...] | None':
        match self:
            case OutgoingFrameExit(request=FramedResponseMsg(defs=msgs)): return msgs
        return None

    def class_data_msg(self, name: str) -> 'ClassDataMsg | None':
        from .msg.all import ClassDataMsg
        match self:
            case OutgoingFrameExit(response=FramedResponseMsg(defs=msgs)):
                for m in msgs:
                    d = m.data
                    if isinstance(d, ClassDataMsg) and d.name == name: return d
        return None

    def function_data_msg(self, name: str) -> 'FunctionDataMsg | None':
        from .msg.all import FunctionDataMsg
        match self:
            case OutgoingFrameExit(response=FramedResponseMsg(defs=msgs)):
                for m in msgs:
                    d = m.data
                    if isinstance(d, FunctionDataMsg) and d.name == name: return d
        return None

    def outgoing_resource_data(self) -> 'ResourceData | None':
        match self:
            case DescribeResource(resource=data): return data
        return None

    def incoming_resource_data(self) -> 'ResourceData | None':
        match self:
            case CreateResource(resource=data): return data
        return None


################################################################################

class OutgoingEvent(Event): __slots__ = ()
class IncomingEvent(Event): __slots__ = ()

################################################################################

class RPCEvent(Event):
    __slots__ = 'tick',

    @property
    def msg(self) -> 'RpcMsg': ...

    def __short_args__(self):
        yield self.msg.short_str()

    def __line_args__(self):
        yield self.msg.repr()


class OutgoingRPC(RPCEvent, OutgoingEvent): __slots__ = ()
class IncomingRPC(RPCEvent, IncomingEvent): __slots__ = ()

################################################################################

class FrameEvent(RPCEvent):
    __slots__ = 'tick', 'request'

    tick:      Tick
    request:  'FramedRequestMsg'


################################################################################

class FrameEnterEvent(FrameEvent):
    __slots__ = 'tick', 'request'

    tick:     Tick
    request: 'FramedRequestMsg'

    def __init__(self, tick: Tick, request: 'FramedRequestMsg'):
        self.tick = tick
        self.request = request

    def __short_args__(self):
        yield self.request.short_str()

    def __line_args__(self):
        yield self.request.repr()

    @property
    def msg(self) -> 'FramedRequestMsg':
        return self.request


class OutgoingFrameEnter(FrameEnterEvent, OutgoingRPC):
    __slots__ = ()
    __icon__  = '··>'

class IncomingFrameEnter(FrameEnterEvent, IncomingRPC):
    __slots__ = 'tick', 'request'
    __icon__  = '<··'

################################################################################

class FrameExitEvent(FrameEvent):
    __slots__ = 'start', 'tick', 'request', 'response'

    start:    Tick
    request:  'FramedRequestMsg'

    tick:     Tick
    response: 'FramedResponseMsg'

    def __init__(self, start: Tick, request: 'FramedRequestMsg', tick: Tick, response: 'FramedResponseMsg'):
        self.start = start
        self.tick = tick
        self.request = request
        self.response = response

    def __short_args__(self):
        yield f_tick(self.start)
        yield self.request.short_str()
        yield self.response.short_str()

    def __line_args__(self):
        yield f_tick(self.start)
        yield self.request.repr()
        yield self.response.repr()

    @property
    def msg(self) -> 'FramedResponseMsg':
        return self.response


class OutgoingFrameExit(FrameExitEvent, OutgoingRPC):
    __slots__ = 'start', 'tick', 'request', 'response'
    __icon__  = '-->'


class IncomingFrameExit(FrameExitEvent, IncomingRPC):
    __slots__ = 'start', 'tick', 'request', 'response'
    __icon__  = '<--'


################################################################################

class EventEvent(RPCEvent):
    __slots__ = 'tick', 'event',

    tick:   Tick
    event: 'EventMsg'

    def __init__(self, tick: Tick, event: 'EventMsg'):
        self.tick = tick
        self.event = event

    @property
    def msg(self) -> 'EventMsg':
        return self.event


class EventSend(EventEvent, OutgoingRPC):
    __slots__ = 'tick', 'event',
    __icon__  = '#->'


class EventReceive(EventEvent, IncomingRPC):
    __slots__ = 'tick', 'event',
    __icon__  = '<-#'


################################################################################

class ChannelEvent(RPCEvent):
    __slots__ = 'tick', 'msg'

    tick: 'Tick'
    msg:  'ChannelMsg'

    def __init__(self, tick: Tick, msg: 'ChannelMsg'):
        self.tick = tick
        self.msg = msg

    def __short_args__(self):
        yield self.msg.short_str()

    def __line_args__(self):
        from agentica_internal.warpc.fmt import f_grid
        yield self.msg.data.repr()
        if not self.msg.defs: return
        yield '\n┌─ defs ─┄'
        for d in self.msg.defs:
            yield f'\n {f_grid(d.rid)} := {d.repr()}'
        yield '\n└────────┄'

class ChannelSend(ChannelEvent, OutgoingRPC):
    __slots__ = 'tick', 'term', 'defs'
    __icon__  = '==>'


class ChannelReceive(ChannelEvent, IncomingRPC):
    __slots__ = 'tick', 'term', 'defs'
    __icon__  = '<=='


################################################################################

class ResourceEvent(Event):
    __slots__ = 'tick', 'data',

    tick:      Tick
    data: 'ResourceData'

    def __init__(self, tick: Tick, data: 'ResourceData'):
        self.tick = tick
        self.data = data

    def __short_args__(self):
        yield self.data.short_str()

    def __line_args__(self):
        yield self.data.repr()


class DescribeResource(ResourceEvent):
    __slots__ = 'tick', 'resource',
    __icon__  = '@->'


class CreateResource(ResourceEvent):
    __slots__ = 'tick', 'resource',
    __icon__  = '<-@'


################################################################################

FrameEnterEvent.INCOMING = IncomingFrameEnter
FrameEnterEvent.OUTGOING = OutgoingFrameEnter

FrameExitEvent.INCOMING = IncomingFrameExit
FrameExitEvent.OUTGOING = OutgoingFrameExit

ResourceEvent.INCOMING = CreateResource
ResourceEvent.OUTGOING = DescribeResource

ChannelEvent.INCOMING = ChannelReceive
ChannelEvent.OUTGOING = ChannelSend

RPCEvent.INCOMING = IncomingRPC
RPCEvent.OUTGOING = OutgoingRPC

EventEvent.INCOMING = EventReceive
EventEvent.OUTGOING = EventSend

################################################################################

ChannelReceive.__icon__        = '<=='
ChannelSend.__icon__           = '==>'

IncomingFrameEnter.__icon__    = '<··'
IncomingFrameExit.__icon__     = '<--'

EventSend.__icon__             = '#->'
EventReceive.__icon__          = '<-#'

OutgoingFrameEnter.__icon__    = '··>'
OutgoingFrameExit.__icon__     = '-->'

DescribeResource.__icon__      = '@->'
CreateResource.__icon__        = '<-@'
