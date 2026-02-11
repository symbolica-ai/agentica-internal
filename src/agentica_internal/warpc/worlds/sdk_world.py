# fmt: off

from asyncio import AbstractEventLoop, Queue, Task, Future, TaskGroup, CancelledError  # noqa
from asyncio import to_thread, run_coroutine_threadsafe, get_running_loop, create_task  # noqa

from ..exceptions import raise_shutdown
# Queue.shutdown only arrived in 3.13, we emulate it for 3.12
from ...core.queues import Queue, QueueShutDown
from ...core.fmt import f_set

from ..request.vars import Vars

from .__ import *
from .base_world import *

__all__ = [
    'SDKWorld',
]

no_send_msg = cast(AsyncSendMsg, raise_shutdown)
no_recv_msg = cast(AsyncRecvMsg, raise_shutdown)

################################################################################

INVOCATION_MID = -1

class SDKWorld(World):
    """
    Handles virtualizing resources, servicing remote resource requests on
    the client side, and transmitting values via `channel_send` and `channel_recv`.

    `send_msg` and `recv_msg` will raise `WarpShutdown` unless an event
    loop task is running.
    """
    executing:  dict[MessageID, Task]  # locally executing request from remote
    awaiting:   dict[MessageID, Future[FramedResponseMsg]]
    futures:    dict[MessageID, Future]
    channel:    Queue[ChannelMsg]

    send_msg:   AsyncSendMsg
    recv_msg:   AsyncRecvMsg
    event_loop: AbstractEventLoop
    tasks:      list[Task]

    def __post_init__(self):
        super().__post_init__()
        self.executing = {}
        self.awaiting = {}
        self.futures = {}
        self.channel = Queue()
        self.task = None
        self.send_msg = no_send_msg
        self.tasks = []

    def clone(self) -> Self:
        cloned = super().clone()
        cloned.executing = {}
        cloned.awaiting = {}
        cloned.futures = {}
        cloned.channel = Queue()
        cloned.task = None
        cloned.inbox = Queue()
        cloned.outbox = Queue()
        cloned.tasks = []
        return cloned

    def __repr__(self) -> str:
        executing = f_set(f_id, self.executing.keys())
        awaiting = f_set(f_id, self.awaiting.keys())
        return f'SDKWorld(id={f_id(self.id)}, {executing=}, {awaiting=})'

    ############################################################################

    def to_payload(self, vars_: Rec[TermT]) -> bytes:
        vars_obj = Vars(vars_)
        vars_msg = vars_obj.encode(self.root, 'full')
        vars_data = vars_msg.to_msgpack()
        return vars_data

    ############################################################################

    def start_msg_loop(self,
                       send_bytes: AsyncSendBytes,
                       recv_bytes: AsyncRecvBytes,
                       future: Future | None = None) -> \
            Task:
        if not hasattr(self, 'event_loop'):
            self.event_loop = get_running_loop()

        log_send = bool(LOG_SEND)
        log_recv = bool(LOG_RECV)

        # rough idea here: a message loop is associated with ONE

        async def send_msg(msg: RPCMsg) -> None:
            try:
                self.on_message(Outgoing, self.tick, msg)
                msg_data = msg.to_msgpack()
                if log_send:
                    P.nprint(ICON_SEND, fmt_msgpack(msg_data, multiline=False))
                await send_bytes(msg_data)
            except RuntimeError:
                raise E.WarpShutdown()

        async def recv_msg() -> RPCMsg:
            msg_data = await recv_bytes()
            if log_recv:
                P.nprint(ICON_RECV, fmt_msgpack(msg_data, multiline=False))
            msg = RPCMsg.from_msgpack(msg_data)
            self.on_message(Incoming, self.tick, msg)
            return msg

        self.send_msg = send_msg

        async def msg_loop() -> None:
            try:
                while True:
                    rpc_msg = await recv_msg()
                    await self.handle_incoming_message(rpc_msg)
            except BaseException as exc:
                if future is not None:
                    if not future.done():
                        future.set_exception(exc)
                if type(exc) not in (CancelledError, E.WarpShutdown):
                    self.handle_msg_loop_err(exc)

        task_coro = msg_loop()
        task_name = f'{self.log_name}.msg_loop'
        task = self.event_loop.create_task(task_coro, name=task_name)
        self.tasks.append(task)
        return task

    def handle_msg_loop_err(self, exc: BaseException) -> None:
        self.log("handle_msg_loop_err", exc)

    # TODO: collapse this with new virtual futures
    def create_future(self, future_id: FutureID, future: Future | None = None) -> Future[Result]:
        with self.log_as("create_future", future_id) as ctx:
            loop = getattr(self, 'event_loop', None)
            if loop is None:
                self.event_loop = loop = get_running_loop()
            futures = self.futures
            previous = futures.get(future_id)
            if previous is None:
                if future is None:
                    ctx.log('created new future', future)
                    future = loop.create_future()
                else:
                    ctx.log('using provided future', future)
                self.futures[future_id] = future
            else:
                ctx.log('future already exists')
            return future

    ############################################################################

    def _new_future(self, future_id: FutureID, /) -> FutureT | None:
        future = new_hookable_future(self.event_loop)
        setattr(future, FUTURE_ID, future_id)
        return future

    def _await_future(self, future: FutureT, _: None, /) -> None:
        pass

    def _gather_future(self, future: FutureT, _: None, /) -> None:
        pass

    def send_event(self, msg: EventMsg) -> None:
        self.on_event(Outgoing, self.tick, msg)
        name = f'{self.log_name}.send_event'
        self.event_loop.create_task(self.send_msg(msg), name=name)

    ############################################################################

    # to satisfy WorldP

    def execute_outgoing_request_sync(self, msg: FramedRequestMsg) -> FramedResponseMsg:
        # we can't break the sync -> async barrier since the rest of agentica uses the
        # main event loop
        raise NotImplementedError('sync virtual requests not supported in this world')

    # NOTE: should this catch exceptions in the await response and turn these into RuntimeError?
    def execute_outgoing_request_coro(self, msg: FramedRequestMsg) -> Awaitable[FramedResponseMsg]:
        on_exit = self.on_frame(Outgoing, msg)
        loop = self.event_loop
        self.awaiting[msg.mid] = future = loop.create_future()

        async def await_response():
            await self.send_msg(msg)
            response = await future
            on_exit(response)
            return response

        await_response_coro = await_response()
        # this task will be cancelled when the future is cancelled, so we don't need to cancel it
        # ourselves
        name = f'{self.log_name}.await_response[{f_id(msg.mid)}]'
        loop.create_task(await_response_coro, name=name)
        return future

    def execute_outgoing_request_future(self, msg: FramedRequestMsg) -> Future[FramedResponseMsg]:
        loop = self.event_loop
        self.awaiting[msg.mid] = future = loop.create_future()
        name = f'{self.log_name}.outgoing_request[{f_id(msg.mid)}]'
        self.event_loop.create_task(self.send_msg(msg), name=name)
        return future

    ############################################################################

    def close(self) -> None:
        if self.closed:
            return
        self.closed = True
        self.__cancel()
        super().close()

    def __cancel(self) -> None:
        self.send_msg = no_send_msg
        self.recv_msg = no_recv_msg
        for task in self.tasks:
            if not task.done():
                task.cancel()
        for task in self.executing.values():
            task.cancel()
        self.executing.clear()
        for future in self.awaiting.values():
            future.cancel()
        self.awaiting.clear()
        for future in self.futures.values():
            self.unregister_future(future)
        self.futures.clear()
        self.channel.shutdown()  # type: ignore

    def needs_close(self) -> bool:
        if self.closed:
            return False
        if not self.executing and not self.awaiting:
            return False
        for executing in self.executing.values():
            if not executing.done():
                return True
        for task in self.tasks:
            if not task.done():
                return True
        self.executing.clear()
        self.tasks.clear()
        return False

    def __del__(self) -> None:
        if self.needs_close():
            P.print_unclosed_error(self)

    ############################################################################

    async def handle_incoming_message(self, msg: RPCMsg) -> None:
        with self.log_as('handle_incoming_message', msg) as ctx:

            if isinstance(msg, FramedRequestMsg):
                loop = self.event_loop
                send_fn = self.send_msg
                exit_fn = self.on_frame(Incoming, msg)
                task = self.root.exec_incoming_request_task(msg, loop, send_fn, exit_fn)
                self.executing[msg.mid] = task
                # FIXME: we will gradually accumulate finished tasks in executing

            elif isinstance(msg, FramedResponseMsg):
                mid = msg.mid
                awaiting = self.awaiting
                if mid in awaiting:
                    awaiting[mid].set_result(msg)

            # TODO: delete FutureResultMsg in favor of FutureEventMsg
            elif isinstance(msg, FutureResultMsg):
                self.handle_future_msg(msg)

            elif isinstance(msg, FutureEventMsg):
                self.on_event(Incoming, self.tick, msg)
                self.handle_future_event_msg(msg)

            elif isinstance(msg, ChannelMsg):
                self.on_channel(Incoming, self.tick, msg)
                await self.channel.put(msg)

            elif isinstance(msg, RemotePrintMsg):
                P.remote_print(msg.text)

            else:
                self.raise_protocol_error(ctx, f'unexpected message: {msg}')

    # TODO: remove in favor of handle_event_msg
    def handle_future_msg(self, msg: FutureResultMsg) -> None:
        with self.log_as('handle_future_msg', msg, msg.fid) as ctx:
            fid = msg.fid
            future = self.futures.pop(fid, None)
            if future is None:
                ctx.warn(f'no future associated with {f_id(fid)}')
                return

            result = msg.result.decode(self.root)
            if result.is_ok:
                ctx.info(f'future.set_result', result.value)
                future.set_result(result.value)
            elif result.is_err:
                ctx.info(f'result.set_error', result.value)
                future.set_exception(result.error)
            elif result.is_unavailable:
                ctx.info(f'future.cancel')
                future.cancel()

    ############################################################################

    async def channel_close(self):
        await self.send_msg(CHANNEL_CLOSED_MSG)

    async def channel_send_value(self, value: Any, *, last: bool = False):
        src_loc = get_stack_identifier(1) if flags.SEND_VIRTUAL_REQUEST_ORIGIN else None
        channel_msg = ChannelMsg.encode(self.root, Result.good(value), last, src_loc)
        self.on_channel(Outgoing, self.tick, channel_msg)
        await self.send_msg(channel_msg)

    async def channel_send_exception(self, exception: BaseException, *, last: bool):
        src_loc = get_stack_identifier(1) if flags.SEND_VIRTUAL_REQUEST_ORIGIN else None
        channel_msg = ChannelMsg.encode(self.root, Result.bad(exception), last, src_loc)
        await self.send_msg(channel_msg)

    async def channel_recv_value(self) -> TermT | Closed:
        result = await self.channel_recv()
        if result is CLOSED:
            return result
        return result.realize()

    async def channel_recv(self) -> Result | Closed:
        channel = self.channel
        if self.closed:
            if channel.empty:
                return CLOSED
        try:
            channel_msg = await channel.get()
        except QueueShutDown:
            return CLOSED
        if channel_msg.last:
            channel.shutdown()  # type: ignore
        return channel_msg.decode(self.root)


REMOTE_PRINT_GUTTER = "\033[43m RP\033[49m "
