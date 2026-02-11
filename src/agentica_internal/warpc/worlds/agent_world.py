# fmt: off

import sys

from sys import modules as sys_modules
from asyncio import Future, Task, AbstractEventLoop, sleep, _get_running_loop
from collections import deque

from .__ import *
from .base_world import *

__all__ = ['AgentWorld']

################################################################################

PROTECTED_MODULES = set(sys.modules.keys())

class AgentWorld(World):

    recv_bytes: SyncRecvBytes
    send_bytes: SyncSendBytes
    responses:  dict[MessageID, FramedResponseMsg] = {}
    awaiting:   dict[MessageID, Future[FramedResponseMsg]] = {}
    futures:    dict[FutureID, Future] = {}
    channel:    deque[ChannelMsg] | None
    running:    bool
    loop:       AbstractEventLoop
    task:       Task | None

    dummy_modules: dict[str, ModuleType]

    protected_modules: set[str] = set()

    ############################################################################

    def __post_init__(self) -> None:
        self.running = False
        self.channel = deque()
        self.responses = {}
        self.awaiting = {}
        self.futures = {}
        self.task = None
        # modules that exist when the world is created are protected
        self.protected_modules |= PROTECTED_MODULES
        self.dummy_modules = {}

    def _closed(self):
        self.running = False
        self.channel = None
        self.responses.clear()
        self.awaiting.clear()
        self.futures.clear()

    ############################################################################

    def set_loop(self, loop: AbstractEventLoop):
        self.loop = loop
        if loop.is_running():
            raise RuntimeError(f"AgentWorld given a running loop {loop}")
        self.log("loop set to", loop)

    ############################################################################

    def send_msg(self, msg: RPCMsg):
        try:
            data = msg.to_msgpack()
            self.send_bytes(data)
        except Exception as error:
            self.log_forced('send_msg failed; raising WarpShutdown', error)
            raise E.WarpShutdown()

    def __recv_msg(self, ctx: LogContext) -> RPCMsg:
        try:
            ctx.info('awaiting bytes')
            data = self.recv_bytes()
        except RuntimeError:
            ctx.log('recv_bytes broken, exiting')
            raise E.WarpShutdown()
        if data == QUIT:
            ctx.log('QUIT received, exiting')
            raise E.WarpShutdown()
        try:
            rpc_msg = RPCMsg.from_msgpack(data)
            return rpc_msg
        except:
            ctx.warn('corrupt message, exciting')
            raise E.WarpShutdown()

    def __pop_queue(self) -> Result | Closed:
        channel_msg = self.channel.popleft()
        if channel_msg.last:
            self.channel = None
        return channel_msg.decode(self.root)

    ############################################################################

    def resource_post_decode(self, resource: ResourceT, handle: ResourceHandle) -> None:
        # fake the existence of the resource in the correct module

        mod_name = getattr(resource, '__module__', None)
        if type(mod_name) is not str or not mod_name:
            return

        obj_name: str | None = getattr(handle, 'name', None) or getattr(resource, '__name__', None)
        if type(obj_name) is not str or not obj_name:
            return

        dummy_modules = self.dummy_modules
        if mod_name in sys_modules and mod_name not in dummy_modules:
            # if module exists in system modules and is not one we made,
            # then do nothing
            return

        module = dummy_modules.get(mod_name)
        if module is None:
            dummy_modules[mod_name] = module = ModuleType(mod_name, "remote module")

        if mod_name not in sys_modules:
            sys_modules[mod_name] = module

        setattr(module, obj_name, resource)

    ############################################################################

    # to satisfy WorldP

    def execute_outgoing_request_sync(self, msg: FramedRequestMsg) -> FramedResponseMsg:
        with self.log_as('execute_outgoing_request_sync', msg.mid) as ctx:
            ctx.log('sending msg', msg)
            self.send_msg(msg)
            ctx.log('message sent')
            return self.run_until_mid(ctx, msg.mid)

    async def execute_outgoing_request_coro(self, msg: FramedRequestMsg) -> FramedResponseMsg:

        with self.log_as('execute_outgoing_request_coro', msg) as ctx:
            self._check_loop(ctx)

            # otherwise, we start an asyncio task that will service messages
            # and this task will at some point cause the future to be done
            # it is fine for this task to 'compete' with run_until_mid,
            # because read_msg is blocking, only one of them will ever be active
            # on the task queue, and it does the same job as the other

            # if such a task is already running, we do nothing

            ctx.log('sending msg')
            self.send_msg(msg)

            self.start_futures_task()

            mid = msg.mid
            self.awaiting[mid] = future = self.loop.create_future()
            ctx.log(f'future #{f_id(mid)}', future, 'created')

            return await future

    def execute_outgoing_request_future(self, msg: FramedRequestMsg) -> Future[FramedResponseMsg]:

        with self.log_as('execute_outgoing_request_future', msg) as ctx:
            ctx.log('sending msg')
            self.send_msg(msg)

            self.start_futures_task()

            mid = msg.mid
            self.awaiting[mid] = future = self.loop.create_future()
            ctx.log(f'future #{f_id(mid)}', future, 'created')

            return future

    ############################################################################

    def _new_future(self, future_id: FutureID, /) -> FutureT | None:
        future = new_hookable_future(self.loop)
        setattr(future, FUTURE_ID, future_id)
        return future

    def _await_future(self, future: FutureT, _: None):
        with self.log_as('_await_future', future) as ctx:
            self._check_future(future, ctx)
            self.start_futures_task()

    def _gather_future(self, future: FutureT, _: None):
        with self.log_as('_gather_future', future) as ctx:
            self._check_future(future, ctx)
            self.start_futures_task()

    def send_event(self, msg: EventMsg) -> None:
        self.on_event(Outgoing, self.tick, msg)
        self.send_msg(msg)

    def _check_future(self, future: FutureT, ctx: LogContext):
        future_loop = future.get_loop()
        our_loop = self.loop
        if future_loop is not our_loop:
            self._raise_async_error(ctx, 'future', future, 'on loop', future_loop, 'instead of', our_loop)

    def _check_loop(self, ctx: LogContext):
        our_loop = self.loop
        if not our_loop:
            self._raise_async_error(ctx, 'no loop set')
        running_loop = _get_running_loop()
        if running_loop and running_loop is not our_loop:
            self._raise_async_error(ctx, 'running loop', running_loop, 'is not our loop', our_loop)

    def _raise_async_error(self, ctx: LogContext, *args) -> NoReturn:
        ctx.log(*args)
        raise E.WarpAsyncError(P.sprint(*args))

    ############################################################################

    def run_msg_loop(self,
            send_bytes: SyncSendBytes,
            recv_bytes: SyncRecvBytes,
            recv_ready: SyncRecvReady) -> None:

        del recv_ready

        # run a message loop forever, this is the outermost kind of message loop,
        # and we might have many run_until_mid appearing on the stack
        # multiple times AND have `futures_task` running if asyncio gets involved,
        # this is all fine

        with self.log_as('run_msg_loop', self.loop) as ctx:

            self._check_loop(ctx)
            self.recv_bytes = recv_bytes
            self.send_bytes = send_bytes
            try:
                self.run_until_mid(ctx, NO_MID)  # we don't expect any replies at top-level
            except E.WarpShutdown:
                ctx.log('caught WarpShutdown; shutting down')
                pass

    ############################################################################

    def run_until_mid(self, ctx: LogContext, until_mid: MessageID, break_fn=None) -> FramedResponseMsg:

        # this is the 'hand-rolled async' version of the AgentWorld message loop,
        # it runs a given message ID is received, but in the meantime stores any
        # responses that loops higher up in the stack frame may be interested in,
        # and fulfills any active futures (which would imply we are in operating
        # in hybrid mode)

        # compare with `futures_task`

        futures = self.awaiting
        responses = self.responses
        frame = self.root
        loop = self.loop
        send = self.send_msg

        log = bool(ctx)

        while True:

            # if another nested call already received this response
            if response := self.responses.pop(until_mid, None):
                ctx.log('mid=', until_mid, 'received')
                return response

            if break_fn and break_fn():
                ctx.log('break_fn stopped loop')
                return None  # type: ignore

            msg: RPCMsg = self.__recv_msg(ctx)
            ctx.log('got message', msg)

            if isinstance(msg, FramedRequestMsg):
                exit_fn = self.on_frame(Incoming, msg)
                ctx.log('is_async =', msg.is_async)
                if msg.is_async and loop.is_running():
                    ctx.log('calling frame.exec_incoming_request_task')
                    frame.exec_incoming_request_task(msg, loop, send, exit_fn)
                else:
                    ctx.log('calling frame.exec_incoming_request')
                    frame.exec_incoming_request(msg, send, exit_fn)

            elif isinstance(msg, FramedResponseMsg):
                received_mid = msg.mid
                if future := futures.get(received_mid):
                    if not future.done():
                        ctx.log(f'future #{f_id(received_mid)} fulfilled:', future)
                        future.set_result(msg)
                    else:
                        ctx.warn(f'future #{f_id(received_mid)} already set:', future, future._state)
                    del futures[received_mid]

                if received_mid == until_mid:
                    ctx.log('returning matched response, mid =', received_mid)
                    return msg
                elif not future:
                    ctx.log('saving unmatched response, mid =', received_mid)
                    responses[received_mid] = msg

            elif isinstance(msg, FutureEventMsg):
                self.handle_future_event_msg(msg)

            elif isinstance(msg, ChannelMsg):
                self.on_channel(Incoming, self.tick, msg)
                channel = self.channel
                if channel is not None:
                    channel.append(msg)

            else:
                self.raise_protocol_error(ctx, f'unexpected message: {msg}')

        raise RuntimeError('unreachable')

    ############################################################################

    def start_futures_task(self) -> None:
        if self.task:
            return
        # self.log('starting futures task')
        name = f'{self.log_name}.futures_task'
        self.task = self.loop.create_task(self.futures_task(), name=name)

    def __log_futures_task_status(self, ctx: LogContext) -> None:
        if awaiting := self.awaiting:
            ctx.log('still awaiting keys:', ' '.join(f_id(k) for k in awaiting.keys()))
        if futures := self.futures:
            ctx.log('still awaiting futures: ', list(futures.keys()))
        if not futures and not awaiting:
            ctx.log('no further reason for futures task')

    async def futures_task(self) -> None:
        # this is the 'asyncio' version of the AgentWorld message loop, it runs
        # as long as there are Futures that can have the tasks waiting on them
        # awoken when we receive their replies

        loop = self.loop
        awaiting = self.awaiting
        responses = self.responses
        futures = self.futures
        frame = self.root
        send_msg = self.send_msg

        with self.log_as('futures_task') as ctx:
            self._check_loop(ctx)

            try:

                while len(awaiting) or len(futures):

                    # yield, so that we are only call recv_msg as last resort
                    await sleep(0)

                    self.__log_futures_task_status(ctx) if ctx else None

                    # might have finished during that time
                    if not len(awaiting) and not len(futures):
                        break

                    msg: RPCMsg = self.__recv_msg(ctx)

                    ctx.log('got msg:', msg) if ctx else None

                    if isinstance(msg, FramedRequestMsg):
                        exit_fn = self.on_frame(Incoming, msg)
                        if msg.is_async:
                            frame.exec_incoming_request_task(msg, loop, send_msg, exit_fn)
                        else:
                            frame.exec_incoming_request(msg, send_msg, exit_fn)

                    elif isinstance(msg, FramedResponseMsg):
                        mid = msg.mid
                        if future := awaiting.get(mid):
                            if not future.done():
                                ctx.log(f'future #{f_id(mid)} fulfilled:', future)
                                future.set_result(msg)
                                del awaiting[mid]
                            else:
                                ctx.warn(f'future #{f_id(mid)} already set', future, future._state)
                        else:
                            responses[mid] = msg

                    elif isinstance(msg, FutureEventMsg):
                        self.handle_future_event_msg(msg)

                    elif isinstance(msg, ChannelMsg):
                        self.on_channel(Incoming, self.tick, msg)
                        channel = self.channel
                        if channel is not None:
                            channel.append(msg)

                    else:
                        self.raise_protocol_error(ctx, f'unexpected message: {msg}')

                ctx.log('ending futures task')

            finally:
                self.task = None

    ############################################################################

    def close(self):
        """Make a best-effort attempt to interrupt currently running msg_loop."""
        self.send_bytes = cast(SyncSendBytes, E.raise_shutdown)
        self.recv_bytes = cast(SyncRecvBytes, E.raise_shutdown)
        self.channel = None
        if futures := self.futures:
            for key, future in futures.items():
                self.unregister_future(future)
        super().close()

    ############################################################################

    def channel_close(self):
        self.send_msg(CHANNEL_CLOSED_MSG)

    def channel_send_value(self, value: Any, last: bool, /):
        src_loc = get_stack_identifier(1) if flags.SEND_VIRTUAL_REQUEST_ORIGIN else None
        channel_msg = ChannelMsg.encode(self.root, Result.good(value), last, src_loc)
        self.on_channel(Outgoing, self.tick, channel_msg)
        self.send_msg(channel_msg)

    def channel_send_exception(self, exception: BaseException, last: bool, /):
        src_loc = get_stack_identifier(1) if flags.SEND_VIRTUAL_REQUEST_ORIGIN else None
        channel_msg = ChannelMsg.encode(self.root, Result.bad(exception), last, src_loc)
        self.send_msg(channel_msg)

    def channel_recv(self) -> Result | Closed | Pending:
        queue = self.channel
        if queue is None:
            return CLOSED
        if not len(queue):
            return PENDING
        return self.__pop_queue()

    ############################################################################

    def remote_print(self, *args, sep: str = ' ', end: str = '\n', file=None, flush: bool = True):
        text = P._remote_print_str(args, sep=sep)
        self.send_msg(RemotePrintMsg(text))


NO_MID = 1 << 32
