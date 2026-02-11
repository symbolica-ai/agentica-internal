# fmt: off

from ...core.log import LoggingSpec
from .__ import *
from .debug_pair import *
from .sdk_world import *

__all__ = [
    'DebugWorld',
    'Pair',
    'Pipe',
    'is_virtual',
    'is_real',
    'load_msg_log',
    'print_msg_log',
]


################################################################################

class DebugWorld(SDKWorld):
    """
    DebugWorld is for observability and testing purposes.

    If the other world is in-process we can directly satisfy *sync* virtual resource
    requests (which SyncWorld cannot) by directly calling the other world's `exec_incoming_request`.

    Moreover, we can issue (some of) the `repl_` methods that are normally done
    by `Sandbox`.

    It also records all major warp events in a list, which makes for easier
    debugging and instrumenting.
    """

    qualify_names: bool
    repl_next_mid: int
    other: SDKWorld  # only set in a connected pair
    events: list[Event]

    # these are for testing in local loopback setting

    def __init__(
        self,
        name: str = 'debug',
        logging: bool = True,
        world_id: int | None = None,
        qualify_names: bool = True,
    ) -> None:
        super().__init__(name=name, logging=logging, world_id=world_id)
        self.debug_name = name
        self.qualify_names = qualify_names
        self.repl_next_mid = -1
        self.events = []

    # ==========================================================================

    def history_str(self) -> str:
        lines = [item.line_str() for item in sorted(self.events)]
        return '\n'.join(lines)

    def add_event(self, item: Event) -> None:
        self.events.append(item)

    def on_frame_enter(self, d: Direction, s: Tick, req: FramedRequestMsg):
        super().on_frame_enter(d, s, req)
        self.add_event(FrameEnterEvent.dir(d)(s, req))

    def on_frame_exit(self, d: Direction, s: Tick, req: FramedRequestMsg, t: Tick, res: FramedResponseMsg):
        super().on_frame_exit(d, s, req, t, res)
        self.add_event(FrameExitEvent.dir(d)(s, req, t, res))

    def on_resource(self, d: Direction, t: Tick, data: ResourceData) -> None:
        super().on_resource(d, t, data)
        self.add_event(ResourceEvent.dir(d)(t, data))

    def on_event(self, d: Direction, t: Tick, msg: EventMsg) -> None:
        super().on_event(d, t, msg)
        self.add_event(EventEvent.dir(d)(t, msg))

    def on_channel(self, d: Direction, t: Tick, msg: ChannelMsg) -> None:
        super().on_channel(d, t, msg)
        self.add_event(ChannelEvent.dir(d)(t, msg))

    def collect_events(self, events: list[Event]):
        events.extend(self.events)
        self.events.clear()

    # ==========================================================================

    def resource_pre_decode(self, frame: 'Frame', data: ResourceData, grid: GlobalRID) -> None:
        super().resource_pre_decode(frame, data, grid)
        if self.qualify_names and hasattr(data, 'module'):
            setattr(data, 'module', self.debug_name)

    def execute_outgoing_request_sync(self, msg: FramedRequestMsg) -> FramedResponseMsg:
        # because both DebugWorlds are in the same process, we can cheat!
        on_exit = self.on_frame(Outgoing, msg)
        log = bool(LOG_SEND) | bool(LOG_RECV)
        if log: P.nprint(ICON_PAIR, msg.msgpack_str(multiline=False))
        response_msg = self.other.root.exec_incoming_request(msg, None, on_exit)
        if log: P.nprint(ICON_PAIR, response_msg.msgpack_str(multiline=False))
        return response_msg

    def send_event(self, msg: EventMsg) -> None:
        self.on_event(Outgoing, self.tick, msg)
        if hasattr(self, 'other') and isinstance(msg, FutureEventMsg):
            self.other.handle_future_event_msg(msg)
        else:
            self.send_msg(msg)

    # ==========================================================================

    async def repl_init(self, *, globals_data: bytes, locals_data: bytes):
        with self.log_as("repl_init") as ctx:
            request, defs = bytes_to_repl_init_data(globals_data, locals_data)
            return await self.execute_repl_request(request, defs=defs)

    async def execute_repl_request(self, msg: ReplRequestMsg, defs=()) -> Result:
        mid = self.repl_next_mid
        self.repl_next_mid -= 1
        request_msg = FramedRequestMsg(mid=mid, fid=0, request=msg, fmt='json', defs=defs)
        response_msg = await self.execute_outgoing_request_coro(request_msg)
        return response_msg.decode_response(self.root)

    def handle_msg_loop_err(self, exc: BaseException) -> None:
        self.log(exc)
        self.panic("msg loop error:", exc)

    # ==========================================================================

    @staticmethod
    def connected_pair(
            a_name: str = 'a',
            b_name: str = 'b',
            logging: LoggingSpec = False,
            dump_msgs: bool = False,
            **kwargs: Any) -> 'Pair':
        from .debug_pair import Pair
        return Pair(a_name, b_name, logging, dump_msgs=dump_msgs, **kwargs)

    # ==========================================================================

    def last_event[E: Event](self, cls: type[E] = Event) -> E:
        for ev in reversed(self.events):
            if isinstance(ev, cls):
                return ev
        raise RuntimeError(f"No event matching {cls}")

    def all_events[E: Event](self, cls: type[E] = Event) -> Iter[E]:
        for ev in self.events:
            if isinstance(ev, cls):
                yield ev

    def last_msg[M: RPCMsg](self, cls: type[M] = RPCMsg) -> M:
        for ev in reversed(self.events):
            if isinstance(ev, RPCEvent) and isinstance(msg := ev.msg, cls):
                return msg
        raise RuntimeError(f"No message matching {cls}")

    def all_msgs[M: RPCMsg](self, cls: type[M] = RPCMsg) -> Iter[M]:
        for ev in self.all_events(RPCEvent):
            if isinstance(msg := ev.msg, cls):
                yield msg

    # ==========================================================================

    def pprint_events(self):
        for event in self.events:
            P.hdiv()
            event.pprint()
        P.hdiv()

    def print_events(self):
        P.hdiv()
        lines = [event.line_str() for event in self.events]
        print('\n'.join(lines))
        P.hdiv()


def is_virtual(obj: Any) -> bool:
    return has_handle(obj)

def is_real(obj: Any) -> bool:
    return not has_handle(obj)
