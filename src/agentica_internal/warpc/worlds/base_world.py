# fmt: off

from asyncio import Future
from copy import copy
from typing import BinaryIO
from time import time_ns

from ...core.log import LogBase, binary_log_dir
from ..frame import ICON_M
from ..hooks import *
from .__ import *

__all__ = [
    'World',
]


################################################################################

WorldUUIDs = UUIDs()

class World(LogBase, WorldP, ABC):

    id:       WorldID
    root:     Frame
    running:  bool
    closed:   bool
    repl:     ReplP | None
    __mids:   Ids
    __fids:   Ids
    __hooks:  dict[Any, RequestHook]
    clock:    EventNumber

    simple_events: list[SimpleEvent]
    __msg_log:  BinaryIO | None

    # these two dictionaries are used by both AgentWorld and SKDWorld
    # in identical ways
    awaiting: dict[MessageID, Future[FramedResponseMsg]]
    futures:  dict[FutureID, Future]

    def __init__(self, *, logging: bool = False, name: str | None = None, world_id: WorldID = None):
        if world_id is None:
            world_id = WorldUUIDs()
        if name is None:
            name = f_id(world_id)
        super().__init__(logging=logging, id_name=name)
        self.id = world_id
        self.__mids = Ids(world_id << 16)
        self.__fids = Ids(world_id << 8)
        self.__hooks = {}
        self.root = Frame(0, 0, world_id)
        self.root.init_root(self)
        self.repl = None
        self.closed = False
        self.clock = 0
        self.simple_events = []
        self.__msg_log = self.open_binary_log('msgs')
        self.__post_init__()

    def __post_init__(self):
        pass

    def write_msgs_to(self, path: Path):
        assert path.suffix == '.msgs'
        assert not path.is_dir()
        self.__msg_log = open(path, 'wb')

    ############################################################################
    # these used by DebugWorld

    @property
    def tick(self) -> Tick:
        self.clock += 1
        return self.clock, time_ns()

    def add_simple_event(self, t: Tick, event: EventType) -> None:
        self.simple_events.append(SimpleEvent(t, event))

    def on_frame(self, d: Direction, request: FramedRequestMsg) -> ResponseMsgFn:
        s = self.tick
        self.on_frame_enter(d, s, request)
        def on_exit(response: FramedResponseMsg) -> None:
            self.on_frame_exit(d, s, request, self.tick, response)
        return on_exit

    def on_frame_enter(self, d: Direction, t: Tick, req: FramedRequestMsg):
        self.add_simple_event(t, FrameEnterEvent.dir(d))

    def on_frame_exit(self, d: Direction, s: Tick, req: FramedRequestMsg, t: Tick, res: FramedResponseMsg):
        self.add_simple_event(t, FrameExitEvent.dir(d))

    def on_resource(self, d: Direction, t: Tick, data: ResourceData) -> None:
        self.add_simple_event(t, ResourceEvent.dir(d))

    def on_event(self, d: Direction, t: Tick, msg: EventMsg) -> None:
        self.add_simple_event(t, EventEvent.dir(d))

    def on_channel(self, d: Direction, t: Tick, msg: ChannelMsg) -> None:
        self.add_simple_event(t, ChannelEvent.dir(d))

    def on_message(self, d: Direction, t: Tick, msg: RPCMsg) -> None:
        if msg_log := self.__msg_log:
            msg_log.write(msg.to_msgpack())
            msg_log.write(BIN_MSG_SEP)
            msg_log.flush()

    def simple_history_str(self) -> str:
        return '\n'.join(map(str, self.simple_events))

    ############################################################################

    def clone(self) -> Self:
        new_name = WorldUUIDs()
        cloned = copy(self)
        cloned.rename(self.name + "#" + str(new_name))
        cloned.log(f'cloned 0x{id(cloned):x} from 0x{id(self):x}')
        cloned.root = self.root.cloned_root(cloned)
        cloned.simple_events = self.simple_events.copy()
        if self.__msg_log:
            cloned.__msg_log = cloned.open_binary_log('msgs')
        return cloned

    def close(self) -> None:
        self.log("closing")
        self.closed = True
        if msg_log := self.__msg_log:
            self.log(f"closing message log")
            msg_log.close()
            self.__msg_log = None

    def attach_repl(self, repl: ReplP | None) -> None:
        self.log('Attaching repl', type(repl))
        self.repl = repl

    ############################################################################

    @property
    def codec(self) -> CodecP:
        return self.root

    ############################################################################

    # These methods make World satisfy WorldP

    def get_log_name(self) -> str:
        return self.log_name

    def get_repl(self) -> ReplP | None:
        return self.repl

    def get_world_id(self) -> WorldID:
        return self.id

    def get_frame(self, fid: FrameID) -> Frame | None:
        return self.root

    def new_message_id(self) -> MessageID:
        return self.__mids()

    def new_frame_id(self, fid: FrameID) -> FrameID:
        return self.__fids()

    # --------------------------------------------------------------------------

    # this differs between SDKWorld and AgentWorld
    def _new_future(self, future_id: FutureID, /) -> FutureT | None:
        raise NotImplementedError("futures not supported in this world")

    # this differs between SDKWorld and AgentWorld
    def _await_future(self, future: FutureT, _: None, /) -> None:
        raise NotImplementedError("futures not supported in this world")

    # this differs between SDKWorld and AgentWorld
    def _gather_future(self, future: FutureT, _: None, /) -> None:
        raise NotImplementedError("futures not supported in this world")

    # this differs between SDKWorld and AgentWorld
    def send_event(self, msg: EventMsg) -> None:
        raise NotImplementedError('events not supported in this world')

    # this is identical for SDKWorld and AgentWorld
    def future_from_id(self, future_id: FutureID, /) -> FutureT:
        with self.log_as("future_from_id", future_id) as ctx:

            if future := self.futures.get(future_id):
                ctx.log('found existing future', future)
                return future

            future = self._new_future(future_id)
            if ctx:
                ctx.log('no existing future; created new future', future)
                ctx.log('existing future ids: ', list(self.futures.keys()))

            if isinstance(future_id, int):
                ctx.log('future matches pending request')
                if awaiting_future := self.awaiting.get(future_id):
                    # if this future ID is a message ID for an outgoing request
                    def decode_into(response_future: Future[FramedResponseMsg]):
                        if response_future.cancelled():
                            future.cancel()
                        else:
                            response_msg = response_future.result()
                            response = response_msg.decode_response(self.root)
                            response.into_future(future)
                    awaiting_future.add_done_callback(decode_into)
                    return future

            self.futures[future_id] = future

            if isinstance(future, HookableFuture):
                # the other three hooks are set in `virtual_async` in
                # `register_virtual_future`
                future.___set_hooks___(
                    await_hook=self._await_future,
                    was_gathered_hook=self._gather_future,
                )

            return future

    # this is identical for SDKWorld and AgentWorld
    def send_future_event(self, future: FutureT, /) -> None:
        with self.log_as('send_future_event', future) as ctx:
            future_id = getattr(future, FUTURE_ID, None)
            ctx.log("future with id", future_id, "done")
            if future_id is None:
                return

            result = Result.from_future(future)
            if result.is_pending:
                ctx.warn(f"future not done!")
                return  # this shouldn't happen

            self.unregister_future(future)
            event_msg = FutureEventMsg.encode_event(self.root, future_id, result)

            ctx.log("will send", event_msg)
            self.send_event(event_msg)

    # this is identical for SDKWorld and AgentWorld
    def handle_future_event_msg(self, msg: FutureEventMsg) -> None:
        with self.log_as('handle_future_event_msg', msg) as ctx:

            future_id = msg.future_id
            ctx.vars(future_id=future_id)

            if not self.futures.get(future_id):
                ctx.warn('no future with id', future_id)
                return

            # decode into a CompleteFuture(...) or CancelFuture(...), and
            # ensure that the request we are about to execute does not
            # trigger requests *back* to the remote (real) future

            future_request = msg.decode(self.root)
            del self.futures[future_id]
            self.unregister_future(future_request.future)
            ctx.vars(future_request=future_request)
            future_request.execute()

    # --------------------------------------------------------------------------

    def resource_post_encode(self, frame: 'Frame', data: ResourceData, grid: GlobalRID) -> None:
        self.on_resource(Outgoing, self.tick, data)

    def resource_pre_decode(self, frame: 'Frame', data: ResourceData, grid: GlobalRID) -> None:
        self.on_resource(Incoming, self.tick, data)

    def resource_post_decode(self, resource: ResourceT, handle: ResourceHandle) -> None:
        pass

    # --------------------------------------------------------------------------

    def execute_outgoing_request_sync(self, msg: FramedRequestMsg) -> FramedResponseMsg:
        raise NotImplementedError('virtual requests not supported in this world')

    def execute_outgoing_request_coro(self, msg: FramedRequestMsg) -> Awaitable[FramedResponseMsg]:
        raise NotImplementedError('virtual async requests not supported in this world')

    def execute_outgoing_request_future(self, msg: FramedRequestMsg) -> FutureT:
        raise NotImplementedError('virtual async requests not supported in this world')

    def get_resource_request_hook_result(self, remote: Callable[[], Result], handle: ResourceHandle, request: ResourceRequest) -> Result:
        hooks = self.__hooks
        if not hooks:
            return remote()  # fallback
        hook = hooks.get(request.hook_key())
        if not hook:
            return remote()  # fallback
        log = bool(LOG_VIRT)
        try:
            P.nprint(ICON_M, "calling hook", hook) if log else None
            if isinstance(hook, PreRequestHook):
                result = hook.hook(handle, request)
            elif isinstance(hook, PostRequestHook):
                result = hook.hook(remote(), handle, request)
            else:
                P.nprint(ICON_M, "invalid hook, neither pre- nor post-") if log else None
                return GENERIC_RESOURCE_ERROR
            if result is NotImplemented:
                P.nprint(ICON_M, "hook declined request") if log else None
                return remote()  # fallback
            if not isinstance(result, Result):
                P.nprint(ICON_M, "hook invalid output", result) if log else None
                return GENERIC_RESOURCE_ERROR
            return result
        except Exception as err:
            P.nprint(ICON_M, "hook threw error", err) if log else None
            return GENERIC_RESOURCE_ERROR

    def will_hook(self, request: ResourceRequest) -> bool:
        if hooks := self.__hooks:
            return request.hook_key() in hooks
        return False

    ############################################################################

    def register_future(self, future: FutureT, /) -> None:
        """
        Registers an existing future, which must have a FUTURE_ID. This does two things:

        1) causes the future to emit FutureEventMsg when it completes
        2) allows FutureDataMsgs to decode to it if their future_id matches this ID.
        """
        if not hasattr(future, FUTURE_ID):
            self.log("register_future:", future, "has no FUTURE_ID")
        elif not future.done():
            self.log("registering existing incomplete future", future)
            future.add_done_callback(self.send_future_event)

    def unregister_future(self, future: FutureT, /) -> None:
        if not hasattr(future, FUTURE_ID):
            self.log("unregister_future:", future, "has no FUTURE_ID")
        else:
            self.log("unregistering existing future", future)
            future.remove_done_callback(self.send_future_event)
            unregister_virtual_future(future)

    ############################################################################

    def register_pre_request_hook(self, key: Any, hook: PreRequestHookFn) -> None:
        self.__hooks[key] = PreRequestHook(hook)

    def register_post_request_hook(self, key: Any, hook: PostRequestHookFn) -> None:
        self.__hooks[key] = PostRequestHook(hook)

    ############################################################################

    def raise_protocol_error(self, ctx: LogContext, problem: str) -> NoReturn:
        ctx.warn('protocol error:', problem)
        raise E.WarpProtocolError(problem)

    ############################################################################

    @classmethod
    def collect_msg_logs(cls, log_dir='') -> dict[str, list[RPCMsg]]:
        log_dir = binary_log_dir(log_dir)
        cls_name = cls.__name__
        files = log_dir.glob(f'*_{cls_name}_*.msgs')
        dct = {}
        for file in files:
            dct[file.name] = load_msg_log(file)
        return dct

    @staticmethod
    def load_msg_log(log_file: Path | str) -> list[RPCMsg]:
        return load_msg_log(log_file)

    @staticmethod
    def print_msg_log(log_file: Path | str) -> None:
        print_msg_log(log_file)
