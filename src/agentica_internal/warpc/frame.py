# fmt: off

import logging
import uuid

from enum import Enum, EnumMeta, IntEnum, StrEnum
from types import MethodType
from .data.identifier import get_stack_identifier

from ..core.log import LogBase
from ..cpython.iters import *

from .__ import *
from .hooks import *
from .attrs import FUTURE_ID, WARP_AS, CLASS_WARP_AS
from .kinds import *
from .msg.all import *
from .msg.term import COMPLEX_ENCODERS, CONSTANT_ENCODERS, SIMPLE_ENCODERS
from .repl import *
from .request.all import *
from .resource.all import *
from .resource.logging import *
from .system import FORBIDDEN_IDS, LRID_TO_SRID, SRID_TO_RSRC

__all__ = [
    'WorldP',
    'Frame',
    'ExecRemoteFn',
    'ResponseMsgFn',
]

################################################################################

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop, Task

################################################################################

type ResponseMsgFn = Callable[[FramedResponseMsg], Any]
type ExecRemoteFn = Callable[[FramedRequestMsg], FramedResponseMsg]

################################################################################

class WorldP(Protocol):
    """WorldP is a protocol describing the API surface of World that is relevant
    for how virtual resources are handled by Frame on behalf of World."""

    def get_log_name(self) -> str: ...
    def get_world_id(self) -> WorldID: ...
    def get_repl(self) -> ReplP | None: ...

    def get_frame(self, fid: FrameID) -> 'Frame | None': ...
    def delete_frame(self, frame: 'Frame'): ...

    def new_message_id(self) -> MessageID: ...

    def register_future(self, future: FutureT, /) -> None: ...
    def unregister_future(self, future: FutureT, /) -> None: ...
    def future_from_id(self, future_id: FutureID, /) -> FutureT: ...

    def resource_post_encode(self, frame: 'Frame', data: ResourceData, grid: GlobalRID) -> None: ...
    def resource_pre_decode(self, frame: 'Frame', data: ResourceData, grid: GlobalRID) -> None: ...
    def resource_post_decode(self, resource: ResourceT, handle: ResourceHandle) -> None: ...

    def send_event(self, msg: EventMsg) -> None: ...
    def execute_outgoing_request_sync(self, msg: FramedRequestMsg) -> FramedResponseMsg: ...
    def execute_outgoing_request_coro(self, msg: FramedRequestMsg) -> Awaitable[FramedResponseMsg]: ...
    def execute_outgoing_request_future(self, msg: FramedRequestMsg) -> Awaitable[FramedResponseMsg]: ...

    def will_hook(self, request: ResourceRequest) -> bool: ...
    def get_resource_request_hook_result(self, remote: Callable[[], Result], handle: ResourceHandle, request: ResourceRequest) -> Result: ...


################################################################################

class Frame(LogBase, CodecP):
    __slots__ = (
        'wid', 'fid', 'pid', 'key', 'dep', 'man',
        'lrid_to_rmsg', 'grid_to_rsrc',
        'outgoing_defs', 'incoming_defs',
        'local_lrids', 'remote_lrids'
    )

    wid: WorldID  # our world id
    fid: FrameID  # our frame id
    pid: FrameID  # parent frame id

    # used to look up a world and frame unambiguously
    key: FrameKey

    depth: int
    world: WorldP

    outgoing_defs:  list[DefinitionMsg]             # definitions we have sent
    incoming_defs:  dict[GlobalRID, DefinitionMsg]  # definitions we have received via .defs
    lrid_to_rmsg:   dict[LocalRID, UserResourceMsg]  # local OR remote resources sent or received
    grid_to_rsrc:   dict[GlobalRID, ResourceT]
    local_lrids:    set[LocalRID]
    remote_lrids:   set[LocalRID]

    __enc_stack:    list[ResourceMsg]
    __dec_stack:    list[GlobalRID]
    __obj_stack:    list[object]  # for debugging

    ############################################################################

    def extend(self, other: Self) -> None:
        self.lrid_to_rmsg.update(other.lrid_to_rmsg)
        self.grid_to_rsrc.update(other.grid_to_rsrc)

    ############################################################################

    def __init__(self, fid: FrameID, pid: FrameID, wid: WorldID):
        self.wid = wid
        self.fid = fid
        self.pid = pid
        self.key = wid, fid
        super().__init__(id_name=f_id(fid))

    ############################################################################

    def init_root(self, world: WorldP):
        self.world = world
        self.lrid_to_rmsg = {}
        self.grid_to_rsrc = {}
        self.local_lrids = set()
        self.remote_lrids = set()
        self.outgoing_defs = []
        self.incoming_defs = {}
        self.log_name = world.get_log_name() + '.' + self.log_name
        self.__enc_stack = []
        self.__dec_stack = []
        self.__obj_stack = []

    def cloned_root(self, world: WorldP) -> Self:
        cloned = Frame(self.fid, self.pid, self.wid)
        cloned.world = world
        cloned.lrid_to_rmsg = self.lrid_to_rmsg.copy()
        cloned.grid_to_rsrc = self.grid_to_rsrc.copy()
        cloned.local_lrids = self.local_lrids.copy()
        cloned.remote_lrids = self.remote_lrids.copy()
        cloned.outgoing_defs = self.outgoing_defs.copy()
        cloned.incoming_defs = {}
        cloned.log_name = world.get_log_name() + '.' + self.log_name
        cloned.__enc_stack = []
        cloned.__dec_stack = []
        cloned.__obj_stack = []
        return cloned

    def inherit(self, fid: FrameID = 0) -> 'Frame':
        return self

    def delete(self) -> None:
        pass

    ############################################################################

    def exec_incoming_request(
            self,
            request_msg: FramedRequestMsg,
            send_fn:     ResponseMsgFn | None,
            exit_fn:     ResponseMsgFn
    ) -> FramedResponseMsg:
        """
        Decodes an incoming `FramedRequestMsg`, execute it, then immediately
        encode the result and send it via a `FramedResponseMsg`.

        This is called by `SDKWorld.handle_incoming_message` and
        `AgentWorld.run_until_mid`.
        """
        request = request_msg.decode_request(self)
        result = request.execute()
        response_msg = request_msg.encode_response(self, result)
        exit_fn(response_msg)
        # TODO: just have a BaseWorld.send_later that either sends immediately
        if send_fn:
            assert send_fn(response_msg) is None  # send_fn cannot be an async function
        return response_msg

    def exec_incoming_request_task(
            self,
            request_msg:  FramedRequestMsg,
            loop:        'AbstractEventLoop',
            send_fn:      ResponseMsgFn | None,
            exit_fn:      ResponseMsgFn
    ) -> 'Task[FramedResponseMsg]':
        """
        Decodes an incoming FramedRequestMsg, then creates an asyncio task to
        execute it in via a coroutine.

        This is called by worlds when they receive an incoming
        `FramedRequestMsg` and this message is marked as needing to execute
        asynchronously (via `async_mode = 'coro' | 'future'`).

        This method lives in `Frame` because it natively uses this frame's
        state to decode the incoming  `FramedRequestMsg` and encode the outgoing
        `FramedResponseMsg`.

        This is called by `SDKWorld.handle_incoming_message` and
        `AgentWorld.run_until_mid`.
        """

        request = request_msg.decode_request(self)
        result_coro = request.execute_async()

        async def respond():
            result = await result_coro
            response_msg = request_msg.encode_response(self, result)
            exit_fn(response_msg)
            if send_fn:
                obj = send_fn(response_msg)
                # if callback was an async function, (e.g. send_xxx), wait for it to complete
                if isinstance(obj, Awaitable):
                    await obj
            return response_msg

        respond_coro = respond()
        task = loop.create_task(respond_coro)

        return task

    ############################################################################

    def get_user_resource(self, grid: GlobalRID) -> ResourceT:
        resource = self.grid_to_rsrc.get(grid)
        if resource is not None:
            return resource
        def_msg = self.incoming_defs.get(grid)
        if def_msg is not None:
            return self.decode_incoming_definition(grid, def_msg)
        self.missing_user_resource(grid)

    def missing_user_resource(self, grid: GlobalRID) -> NoReturn:
        grid_ = f_grid(grid)
        name = self.log_name
        if LOG_DECR:
            P.hdiv()
            P.nprint(ICON_C1, 'missing virtual resource', grid_, 'in', name)
        P.eprint(ICON_C1, 'missing virtual resource', grid_, 'in', name)
        problem = f"resource with grid={grid_} is not defined.\n"
        self.raise_dec_err(problem)

    ############################################################################

    def decode_incoming_definition(
            self,
            grid: GlobalRID,
            def_msg: DefinitionMsg,
        ) -> ResourceT:

        obj_stack = self.__obj_stack
        dec_stack = self.__dec_stack

        if grid in dec_stack:
            fallback_resource = self.handle_decode_recursion(grid, def_msg.data)
            if fallback_resource is not None:
                return fallback_resource

        # decode the data field, e.g. ClassDataMsg into ClassData
        try:
            dec_stack.append(grid)
            data = def_msg.data.decode(self)
        finally:
            dec_stack.pop()

        if log := bool(LOG_DECR):
            P.hdiv()
            P.nprint(ICON_C0, 'creating virtual resource in', self, 'from data message:\n')
            def_msg.data.pprint()

        # world can mess with the data if it wants
        self.world.resource_pre_decode(self, data, grid)

        # create a virtual resource that uses us to service requests
        handle = self.new_resource_handle(grid)
        try:
            obj_stack.append(data)
            remote_resource = data.create_resource(handle)
        finally:
            obj_stack.pop()

        # world can inspect the newly decoded resource if it wants
        self.world.resource_post_decode(remote_resource, handle)

        # bind this remote resource and the message to send it as under its ids
        self.grid_to_rsrc[grid] = remote_resource

        if not data.MIGHT_ALIAS:
            lrid = id(remote_resource)
            self.lrid_to_rmsg[lrid] = UserResourceMsg(grid)  # so we can send it back
            self.remote_lrids.add(lrid)

        if log:
            P.nprint()
            action = 'made (uncached)' if data.MIGHT_ALIAS else 'made'
            P.nprint(ICON_C1, action, remote_resource, 'in', self.world, f'VHDL={f_grid(handle.grid)}')
            P.hdiv()

        return remote_resource

    def handle_decode_recursion(self, grid: GlobalRID, data: ResourceDataMsg) -> ResourceT:
        if isinstance(data, TypeAliasDataMsg):
            alias_name = data.name
            alias_module = data.module
            return T.ForwardRef(alias_name, is_argument=False, module=alias_module)
        elif isinstance(data, ClassDataMsg):
            alias_name = data.qname
            alias_module = data.module
            return T.ForwardRef(alias_name, is_argument=False, module=alias_module, is_class=True)
        elif isinstance(data, TypeData):
            return Any
        else:
            self.raise_dec_err(f'cannot decode grid {f_grid(grid)} for recursive resource: {data}')

    # --------------------------------------------------------------------------

    def encode_outgoing_resource(self, lrid: LocalRID, resource: ResourceT) -> ResourceMsg:

        assert lrid not in self.lrid_to_rmsg
        enc_stack = self.__enc_stack
        obj_stack = self.__obj_stack

        # choose the kind of data class
        data_cls = choose_resource_class(resource)

        # make a fresh GlobalRID
        grid = self.new_global_resource_id(lrid)

        if log := bool(LOG_ENCR):
            P.hdiv()
            P.nprint(ICON_C0, 'describing real resource', f_object_id(resource), 'in', self)
            P.nprint()

        # bind this local resource and the message to send it as under its ids
        resource_msg = UserResourceMsg(grid)
        self.lrid_to_rmsg[lrid] = resource_msg
        self.grid_to_rsrc[grid] = resource
        self.local_lrids.add(lrid)

        # make an ResourceData instance (e.g. ClassData)

        try:
            obj_stack.append(resource)
            data = data_cls.describe_resource(resource)
        except E.WarpEncodingForbiddenError:
            if log:
                P.nprint(ICON_C1, 'forbidden error while encoding:', resource)
                P.hdiv()
            return data_cls.forbidden_msg()
        finally:
            obj_stack.pop()

        # let the world mess with the data if it wants
        self.world.resource_post_encode(self, data, grid)

        if log:
            data.pprint()
            P.nprint()
            P.nprint(ICON_CM, 'described resource; grid =', f_grid(grid))
            P.hdiv()

        # encode the ResourceData to a ResourceDataMsg

        try:
            obj_stack.append(resource)
            enc_stack.append(resource_msg)
            data_msg = data.encode(self)
        finally:
            obj_stack.pop()
            enc_stack.pop()

        if log:
            P.nprint(ICON_C1, 'encoded to', type(data_msg).__name__)

        # wrap the ResourceDataMsg in a DefinitionMsg
        def_msg = DefinitionMsg(grid, data_msg)

        # add this definition for benefit of enc_context
        self.outgoing_defs.append(def_msg)

        if log:
            self.log('encoded', f_grid(grid), 'from', f_object_id(resource))

        return resource_msg

    def new_global_resource_id(self, ptr: Ptr) -> GlobalRID:
        return self.wid, self.fid, ptr

    def new_resource_handle(self, grid: GlobalRID) -> ResourceHandle:
        handle = ResourceHandle()
        handle.grid = grid
        handle.fkey = self.key
        handle.hdlr = self.handle_virtual_resource_request
        return handle

    # --------------------------------------------------------------------------

    def handle_virtual_resource_request(self, origin: ResourceHandle, req: ResourceRequest) -> Any:

        # +1 for the virtual stub function, +1 to get to userland
        src_loc = get_stack_identifier(2) if flags.SEND_VIRTUAL_REQUEST_ORIGIN else None

        if bool(LOG_VSTACK):
            P.print_current_stack()

        if log := bool(LOG_VIRT):
            P.hdiv()
            P.nprint(ICON_I, 'VRR of', origin, 'in', self, 'of', 'in', self.world)
            req.pprint()
            P.hdiv()

        result: Result

        if flags.VIRTUAL_RESOURCE_REQUEST_HOOKS and self.world.will_hook(req):
            P.nprint(ICON_I, 'running hook for', req.hook_key()) if log else None
            remote_fn = partial(self.remote_resource_request_result, origin, req, src_loc)
            result = self.world.get_resource_request_hook_result(remote_fn, origin, req)
        else:
            result = self.remote_resource_request_result(origin, req, src_loc)

        if log:
            P.nprint(ICON_O, result)

        return result.realize()

    ############################################################################

    # this executes an outgoing request and returns the result
    # if this is an .as_future or .as_coro request, we can return immediately,
    # otherwise, we use world.execute_outgoing_request_sync(msg) to block until the
    # eventual FramedResponseMsg is received
    def remote_resource_request_result(self, origin: ResourceHandle,
                                       request: ResourceRequest,
                                       src_loc: SrcLocationMsg) -> Result:
        """
        This executes an outgoing request and returns the result as a `Result`.

        If this is an asynchronous request (`.is_async` are True), we will return
        a coroutine / future immediately.

        Otherwise, we use  `world.execute_outgoing_request_sync(msg)` to  block
        until the eventual FramedResponseMsg is received.
        """

        log = bool(LOG_VIRT)
        if origin.fkey is not self.key:
            P.nprint(ICON_E, f'origin key mismatch:', origin.fkey, '!=', self.key) if log else None
            return GENERIC_RESOURCE_ERROR

        mid = self.world.new_message_id()
        msg = FramedRequestMsg.encode_request(self, mid, self.fid, request, src_loc)

        if request.as_future:
            P.nprint(ICON_A, 'sending future-based request') if log else None

            # this will create an `awaiting` future for the FramedResponseMsg
            response_future = self.world.execute_outgoing_request_future(msg)
            P.nprint(ICON_A, 'response future =', response_future) if log else None

            P.nprint(ICON_A, 'created derived future for result') if log else None
            # this will create a derived future that decodes this awaiting future
            result_future = self.world.future_from_id(msg.mid)

            P.nprint(ICON_M, 'returning result future =', result_future) if log else None
            return Result.good(result_future)

        elif request.as_coro:

            async_name = request.async_name()
            log_name = f'<async {async_name} #{mid}>'

            async def dummy_fn():
                P.nprint(ICON_A, log_name, 'coroutine started') if log else None
                awaitable = self.world.execute_outgoing_request_coro(msg)
                P.nprint(ICON_A, log_name, 'awaiting response') if log else None
                assert isinstance(awaitable, Awaitable)
                response_msg = await awaitable
                final_result = response_msg.decode_response(self)
                P.nprint(ICON_A, log_name, 'got response', final_result) if log else None
                return final_result.realize()

            dummy_fn.__name__ = dummy_fn.__qualname__ = async_name
            dummy_fn.__module__ = 'virtual'
            dummy_fn.__code__ = dummy_fn.__code__.replace(
                co_name=async_name,
                co_qualname=async_name,
                co_filename='virtual'
            )

            P.nprint(ICON_M, log_name, 'returning coroutine immediately') if log else None
            coro = dummy_fn()
            return Result.good(coro)

        response = self.world.execute_outgoing_request_sync(msg)

        # if ctx:
        #     ctx.info('received response:', response)

        if not isinstance(response, FramedResponseMsg):
            cause = f'expected FramedResponseMsg, not {f_object_id(response)}'
            raise E.WarpProtocolError(cause)

        result = response.decode_response(self)

        # if ctx:
        #     ctx.info('decoded result:', result)

        return result

    ############################################################################

    def enc_any(self, term: TermT) -> TermMsg:

        msg = self._enc_val(term)
        if msg is not None:
            return msg

        cls = type(term)

        if flags.TYPE_ERASE_ENUMS and type(cls) is EnumMeta:
            if issubclass(term, IntEnum):
                val_cls = int
            elif issubclass(term, StrEnum):
                val_cls = str
            else:
                val_cls = object
            return self.enc_class(val_cls)

        if cls.__flags__ & 256 and cls in ITER_TYPES:
            return self._enc_iter(term)

        if flags.VIRTUAL_LAMBDAS:
            if cls is FunctionType and term.__name__ == '<lambda>':
                try:
                    return LambdaMsg.encode_lambda(self, term)
                except:
                    pass

        return self.enc_resource(term)

    def _enc_iter(self, it):

        cls = type(it)

        # for small iterators
        lim = flags.REALIZE_ITERATOR_LIMIT
        if lim >= 0:

            if cls in STR_ITER_TYPES:
                if it.__length_hint__() < 1024:
                    if bool(LOG_ENCR):
                        P.nprint(ICON_E, f'sending raw str iterator')
                    return DataIterMsg.encode_iter(it, self)

            size = iter_len(it)
            if size <= lim:
                msg_cls = TupleMsg
                if cls is ListIterType:
                    msg_cls = ListMsg  # preserve the type, why not?
                elif cls is not TupleIterType:
                    if bool(LOG_ENCR):
                        P.nprint(ICON_E, f'realizing len {size} iterator of class', cls)
                seq_msg = msg_cls(self.enc_sequence(it))
                return DataIterMsg(seq_msg)

        if flags.VIRTUAL_ITERATORS:
            # becomes an IteratorDataMsg later due to is_iterator_t
            return self.enc_resource(it)

        else:
            self.raise_enc_err("builtin iterator objects require `flags.VIRTUAL_ITERATORS = True`")

    # --------------------------------------------------------------------------

    def enc_exception(self, exc: BaseException) -> ExceptionMsg | ExceptionRefMsg:
        if not isinstance(exc, BaseException):
            self.raise_enc_err(f"not an exception: {f_object_id(exc)}")
        return ExceptionMsg.encode_exception(exc, self)

    def enc_value(self, val: ValueT) -> TermPassByValMsg:
        if msg := self._enc_val(val):
            return msg
        self.raise_enc_err(f"{f_object_id(val)} is not a pass-by-value term")

    def _enc_val(self, val: ValueT) -> TermPassByValMsg | None:

        cls = type(val)

        if msg := const_fn(cls):
            return msg

        if fn := atom_fn(cls):
            return fn(val)

        if fn := compound_fn(cls):
            return fn(val, self)

        if isinstance(val, BaseException):
            return ExceptionMsg.encode_exception(val, self)

        if isinstance(val, Enum):
            return EnumMemberMsg.encode_enum(val, self)

        return None

    # --------------------------------------------------------------------------

    def enc_object(self, obj: ObjectT) -> ResourceMsg:
        if not is_object_t(obj):
            raise E.WarpEncodingError(f"not an object: {f_object_id(obj)}")
        return self.enc_resource(obj)

    def enc_class(self, cls: ClassT) -> ClassMsg:
        if not is_class_t(cls):
            self.raise_enc_err(f"not a class: {f_object_id(cls)}")
        return self.enc_resource(cls)

    def enc_type(self, cls: TypeT) -> TypeMsg:
        try:
            return self.enc_any(cls)
        except E.WarpEncodingError:
            return self.enc_resource(Any)

    def enc_function(self, fun: FunctionT) -> FunctionMsg:
        if not is_function_t(fun) and not callable(fun):
            self.raise_enc_err(f"not a function: {f_object_id(fun)}")
        return self.enc_resource(fun)

    def enc_module(self, mod: ModuleT) -> ModuleMsg:
        if not is_module_t(mod):
            self.raise_enc_err(f"not a module: {f_object_id(mod)}")
        return self.enc_resource(mod)

    def enc_future(self, fut: FutureT) -> FutureMsg:
        if not is_future_t(fut):
            self.raise_enc_err(f"not a future: {f_object_id(fut)}")
        return self.enc_resource(fut)

    def enc_resource(self, resource: ResourceT) -> ResourceMsg:
        lrid = id(resource)

        # is it a known, system resource?
        if sid := LRID_TO_SRID.get(lrid):
            return SystemResourceMsg(sid)

        # have we encoded this resource before?
        if msg := self.lrid_to_rmsg.get(lrid):
            return msg

        if flags.RESPECT_WARP_AS:
            cls = type(resource)
            if cls is type or isinstance(resource, type):
                if warp_as := getattr(resource, CLASS_WARP_AS, None):
                    if type(warp_as) is MethodType:
                        self.log("class resource will warp as something else via", warp_as)
                        as_class = warp_as()
                        self.log("warping as", as_class)
                        return self.enc_class(as_class)
            else:
                if warp_as := getattr(cls, WARP_AS, None):
                    if callable(warp_as):
                        self.log("resource will warp as something else via", warp_as)
                        as_resource = warp_as(resource)
                        self.log("warping as", as_resource)
                        return self.enc_any(as_resource)  # type: ignore

        handle = get_handle(resource)
        if handle is not None:
            f_resource = f_object_id(resource)
            self.log("ERROR: existing", resource, "with handle", handle, "not in cache")
            msg = f"existing {f_resource} with handle {handle} not in cache"
            self.raise_enc_err(msg)

        return self.encode_outgoing_resource(lrid, resource)

    def enc_local_resource(self, res: ResourceT) -> LocalResourceMsg:
        if has_handle(res):
            self.raise_enc_err(f'local resource expected, got {f_object_id(res)}')
        return self.enc_resource(res)

    def enc_remote_resource(self, res: ResourceT) -> RemoteResourceMsg:
        # NOTE: could also check remote_lrids, but this wouldn't work across frames
        if not has_handle(res):
            self.raise_enc_err(f'remote resource expected, got {f_object_id(res)}')
        return self.enc_resource(res)

    def enc_system_resource(self, res: ResourceT) -> SystemResourceMsg:
        sid = LRID_TO_SRID.get(id(res))
        if sid is None:
            self.raise_enc_err(f'system resource expected, got {f_object_id(res)}')
        return SystemResourceMsg(sid)

    # --------------------------------------------------------------------------

    def enc_sequence(self, seq: Iter) -> Tup[TermMsg]:
        return tuple(map(self.enc_any, seq))

    def enc_record(self, dct: dict) -> Rec[TermMsg]:
        if type(dct) is not dict:
            self.raise_enc_err(f'record expected, got {f_object_id(dct)}')
        if not dct: return {}
        msg = dict(zip(dct.keys(), map(self.enc_any, dct.values())))
        return msg

    def enc_args(self, tup: ArgsT) -> ArgsMsg:
        if not tup: return ()
        enc_any = self.enc_any
        if not any(a is ARG_DEFAULT for a in tup):
            return tuple(map(enc_any, tup))
        res = []
        for i, arg in enumerate(tup):
            if arg is ARG_DEFAULT:
                if not all(a is ARG_DEFAULT for a in tup[i:]):
                    self.log(f"malformed args: {tup}")
                break
            res.append(enc_any(arg))
        return tuple(res)

    def enc_kwargs(self, rec: KwargsT) -> KwargsMsg:
        enc_any = self.enc_any
        return {k: enc_any(v) for k, v in rec.items() if v is not ARG_DEFAULT}

    def enc_annotations(self, rec: AnnotationsT) -> AnnotationsMsg:
        if not rec:
            return {}
        res = {}
        for k, v in rec.items():
            try:
                v_msg = self.enc_any(v)
                if isinstance(v_msg, SystemResourceMsg) and v_msg.sid in FORBIDDEN_IDS:
                    continue
                res[k] = v_msg
            except E.WarpEncodingError:
                pass
        return res

    def enc_properties(self, rec: PropertiesT) -> PropertiesMsg:
        if not rec:
            return {}
        res = {}
        for k, v in rec.items():
            if not is_property_t(v):
                continue
            try:
                v_msg = self.enc_any(v)
                if isinstance(v_msg, SystemResourceMsg) and v_msg.sid in FORBIDDEN_IDS:
                    continue
                res[k] = v_msg
            except E.WarpEncodingError:
                pass
        return res

    def enc_methods(self, rec: MethodsT, /) -> 'MethodsMsg':
        enc_fun = self.enc_function
        dct = {}
        for k, v in rec.items():
            kind, func = unpack_method(v)
            dct[k] = kind, enc_fun(func)
        return dct

    def enc_owner(self) -> 'ResourceMsg | None':
        stack = self.__enc_stack
        return stack[-2] if len(stack) > 1 else None

    ############################################################################

    def dec_any(self, msg: TermMsg) -> TermT:
        if not isinstance(msg, TermMsg):
            self.raise_dec_err(f"{f_object_id(msg)} is not a TermMsg")
        return msg.decode(self)

    # --------------------------------------------------------------------------

    def dec_exception(self, msg: ExceptionMsg | ExceptionRefMsg) -> BaseException:
        if isinstance(msg, ExceptionMsg):
            return msg.decode(self)
        elif isinstance(msg, ResourceMsg):
            exc = self.dec_resource(msg)
            if isinstance(exc, BaseException):
                return exc
        self.raise_dec_err(f"{f_object_id(msg)} is not an ExceptionMsg")

    def dec_value(self, msg: TermMsg) -> ValueT:
        if not isinstance(msg, TermPassByValMsg):
            self.raise_dec_err(f"{f_object_id(msg)} is not a TermPassByValMsg")
        return msg.decode(self)

    # --------------------------------------------------------------------------

    def dec_object(self, msg: ObjectMsg) -> ObjectT:
        obj = self.dec_resource(msg)
        is_object_t(obj) or self.raise_wrong_type(msg, obj, Kind.Object)
        return obj

    def dec_class(self, msg: ClassMsg) -> ClassT:
        cls = self.dec_resource(msg)
        is_class_t(cls) or self.raise_wrong_type(msg, cls, Kind.Class)
        return cls

    def dec_function(self, msg: FunctionMsg) -> FunctionT:
        fun = self.dec_resource(msg)
        is_function_t(fun) or callable(fun) or self.raise_wrong_type(msg, fun, Kind.Function)
        return fun

    def dec_module(self, msg: ModuleMsg) -> ModuleT:
        mod = self.dec_resource(msg)
        is_module_t(mod) or self.raise_wrong_type(msg, mod, Kind.Module)
        return mod

    def dec_future(self, msg: FutureMsg) -> FutureT:
        mod = self.dec_resource(msg)
        is_future_t(mod) or self.raise_wrong_type(msg, mod, Kind.Future)
        return mod

    def dec_type(self, msg: TypeMsg) -> TypeT:
        try:
            return self.dec_any(msg)
        except E.WarpDecodingError as err:
            P.nprint("decoding type anno", msg, "threw exception", err)
            return Any

    def dec_resource(self, msg: ResourceMsg) -> ResourceT:
        if isinstance(msg, SystemResourceMsg):
            return SRID_TO_RSRC[msg.sid]
        elif isinstance(msg, UserResourceMsg):
            return self.get_user_resource(msg.rid)
        else:
            self.raise_dec_err(f'not a resource msg: {f_object_id(msg)}')

    def dec_local_resource(self, msg: 'LocalResourceMsg') -> ResourceT:
        if isinstance(msg, SystemResourceMsg):
            return SRID_TO_RSRC[msg.sid]
        elif not isinstance(msg, UserResourceMsg):
            self.raise_dec_err(f'not an ResourceMsg: {msg}')
        rsrc = self.grid_to_rsrc[msg.rid]
        if id(rsrc) not in self.local_lrids:
            self.raise_dec_err(f'expected a local resource')
        return rsrc

    def dec_remote_resource(self, msg: 'RemoteResourceMsg') -> ResourceT:
        if not isinstance(msg, UserResourceMsg):
            self.raise_dec_err(f'not an UserResourceMsg: {msg}')
        rsrc = self.grid_to_rsrc[msg.rid]
        if id(rsrc) not in self.remote_lrids:
            self.raise_dec_err(f'expected a remote resource')
        return rsrc

    def dec_system_resource(self, msg: 'SystemResourceMsg') -> ResourceT:
        if not isinstance(msg, SystemResourceMsg):
            self.raise_dec_err(f'not an SystemResourceMsg: {msg}')
        return SRID_TO_RSRC[msg.sid]

    # --------------------------------------------------------------------------

    def dec_sequence(self, seq: Iter[TermMsg]) -> Tup[TermT]:
        return tuple(map(self.dec_any, seq))

    def dec_record(self, rec: Rec[TermMsg]) -> Rec[TermT]:
        if type(rec) is not dict:
            self.raise_dec_err(f"{f_object_id(rec)} is not dict (of TermMsgs)")
        if not rec:
            return {}
        return dict(zip(rec.keys(), map(self.dec_any, rec.values())))

    def dec_args(self, tup: ArgsMsg) -> ArgsT:
        dec_any = self.dec_any
        return tuple(v for m in tup if (v := dec_any(m)) is not ARG_DEFAULT)

    def dec_kwargs(self, rec: KwargsMsg) -> KwargsT:
        dec_any = self.dec_any
        return {k: v for k, m in rec.items() if (v := dec_any(m)) is not ARG_DEFAULT}

    def dec_annotations(self, rec: AnnotationsMsg) -> AnnotationsT:
        if type(rec) is not dict:
            self.raise_dec_err(f"{f_object_id(rec)} is not dict (of TermMsgs)")
        if not rec: return {}
        return dict(zip(rec.keys(), map(self.dec_type, rec.values())))

    def dec_property(self, msg: PropertyMsg) -> PropertyT:
        prop = self.dec_resource(msg)
        if not isinstance(prop, property):
            self.raise_dec_err(f"{f_object_id(msg)} is not a property msg")
        return prop

    def dec_properties(self, rec: PropertiesMsg) -> PropertiesT:
        if type(rec) is not dict:
            self.raise_dec_err(f"{f_object_id(rec)} is not dict (of property msgs)")
        dec_prop = self.dec_property
        props = {}
        for k, m in rec.items():
            try:
                props[k] = dec_prop(m)
            except E.WarpDecodingError:
                continue
        return props

    def dec_methods(self, rec: MethodsMsg) -> MethodsT:
        if type(rec) is not dict:
            self.raise_dec_err(f"{f_object_id(rec)} is not dict (of MethodMsgs)")
        dct = {}
        for k, pair in rec.items():
            if type(pair) is tuple:
                kind, fun_msg = pair
                dct[k] = pack_method(kind, self.dec_function(fun_msg))
            else:
                assert isinstance(pair, ResourceMsg)
                dct[k] = self.dec_function(pair)
        return dct

    # --------------------------------------------------------------------------

    def get_repl(self) -> ReplP | None:
        return self.world.get_repl()

    def future_to_id(self, future: FutureT, /) -> FutureID:
        future_id: FutureID | None = getattr(future, FUTURE_ID, None)
        if future_id is None:
            future_id: str = uuid.uuid4().hex
            setattr(future, FUTURE_ID, future_id)
        else:
            assert isinstance(future_id, (int, str))
        self.world.register_future(future)
        return future_id

    def future_from_id(self, future_id: FutureID) -> FutureT:
        return self.world.future_from_id(future_id)

    ############################################################################

    def enc_before(self, lrid: LocalRID, /) -> bool:
        return lrid in self.lrid_to_rmsg

    def dec_before(self, grid: GlobalRID, /) -> bool:
        return grid in self.grid_to_rsrc

    ############################################################################

    def enc_context(self) -> 'FrameEncoderContext':
        return FrameEncoderContext(self)

    def dec_context(self, msgs: 'Tup[DefinitionMsg]') -> 'FrameDecoderContext':
        return FrameDecoderContext(self, msgs)

    ############################################################################

    def raise_dec_err(self, problem: str) -> NoReturn:
        raise self.add_note(E.WarpDecodingError(problem))

    def raise_wrong_type(self, msg: ResourceMsg, rsr: ResourceT, kind: Kind) -> NoReturn:
        problem = f"{msg} decoded to non-{kind}: {f_object_id(rsr)} in {self.log_name}"
        P.nprint(msg, f"decoded to non-{kind}", rsr, "in", self)
        raise E.WarpDecodingError(problem)

    def raise_enc_err(self, problem: str) -> NoReturn:
        raise self.add_note(E.WarpEncodingError(problem))

    def add_note(self, exc: BaseException) -> BaseException:
        exc.add_note(f"frame: {self.log_name}")
        if stack := self.__obj_stack:
            exc.add_note(f"stack: {fmt_obj_stack(stack)}")
        if id_set := self.local_lrids:
            exc.add_note(f"local resources: {fmt_id_set(id_set)}")
        if id_set := self.remote_lrids:
            exc.add_note(f"remote resources: {fmt_id_set(id_set)}")
        return exc

    ############################################################################

    def log_internal_error(self, msg: str, exc: BaseException) -> None:
        from ..core.color import RESET
        f_msg = f"INTERNAL WARP ERROR IN {self.name}: {msg}"
        frame_logger.error(f_msg, exc_info=exc)
        f_exception = D.fmt_exception(exc)
        P.eprint(f"{RESET}\n{ERROR_BAR}\n{f_msg}\n{f_exception}")


def enc_no_defs(enc, vals: Iter):
    return tuple(enc(v) for v in vals if v is not ARG_DEFAULT)


################################################################################

def choose_resource_class(resource: ResourceT) -> type[ResourceData]:
    if is_function_t(resource):
        return FunctionData
    elif is_class_t(resource):
        if type(resource) is EnumMeta:
            return EnumClassData
        return ClassData
    elif is_coroutine_t(resource):
        return CoroutineData
    elif is_type_t(resource):
        return TypeAliasData
    elif flags.VIRTUAL_MODULES and is_module_t(resource):
        return ModuleData
    elif flags.VIRTUAL_ITERATORS and is_iterator_t(resource):
        return IteratorData
    elif flags.VIRTUAL_FUTURES and is_future_t(resource):
        return FutureData
    elif flags.CLASS_PROPERTIES and is_property_t(resource):
        return PropertyData
    elif flags.VIRTUAL_EXCEPTIONS and isinstance(resource, BaseException):
        return ExceptionData
    else:
        return ObjectData

################################################################################

class FrameEncoderContext:

    outgoing: list[DefinitionMsg]
    start: int
    stop: int

    def __init__(self, frame: Frame):
        self.outgoing = frame.outgoing_defs

    def __enter__(self):
        self.start = len(self.outgoing)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop = len(self.outgoing)

    def enc_context_defs(self) -> Tup[DefinitionMsg]:
        defs = self.outgoing[self.start:self.stop]
        defs.reverse()
        return tuple(defs)


################################################################################

class FrameDecoderContext:

    incoming: dict[GlobalRID, DefinitionMsg]
    defs: tuple[DefinitionMsg, ...]
    added: set[GlobalRID]

    def __init__(self, frame: Frame, defs: tuple[DefinitionMsg, ...]):
        self.incoming = frame.incoming_defs
        self.defs = defs

    def __enter__(self):
        incoming = self.incoming
        self.added = added = set()
        for msg in self.defs:
            grid = msg.rid
            if grid not in incoming:
                incoming[grid] = msg
                added.add(grid)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_tb:
            P.print_traceback(exc_tb)
        incoming = self.incoming
        for grid in self.added:
            incoming.pop(grid)

################################################################################

const_fn    = CONSTANT_ENCODERS.get
atom_fn     = SIMPLE_ENCODERS.get
compound_fn = COMPLEX_ENCODERS.get

################################################################################

def fmt_obj_stack(objs) -> str:
    lines = []
    add = lines.append
    for obj in objs:
        f_obj = '<error>'
        try:
            f_obj = f_object_id(obj)
        except:
            pass
        add('  during ' + f_obj)
    return '\n'.join(lines)

def fmt_id_set(ids: set[int]) -> str:
    text = ' '.join(f'0x{i:x}' for i in list(ids)[:16])
    return text if len(ids) < 16 else text + ' ...'

################################################################################

# uncomment to see mappings from literal classes to their compound encounders
# for k, v in COMPLEX_ENCODERS.items():
#     print(k.__name__.ljust(50), v)

################################################################################

frame_logger = logging.getLogger(__file__)

ERROR_BAR = P.RED('█' * 19)
