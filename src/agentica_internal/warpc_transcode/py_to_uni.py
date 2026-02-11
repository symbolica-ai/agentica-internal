from msgspec import UNSET, UnsetType

from agentica_internal.warpc.alias import *
from agentica_internal.warpc.msg.all import *

# Compatibility aliases for legacy/new message names
from agentica_internal.warpc.msg.rpc_request_resource import ResourceCallFunctionMsg as CallMsg
from agentica_internal.warpc.msg.rpc_request_resource import ResourceCallMethodMsg as CallMethodMsg
from agentica_internal.warpc.msg.rpc_request_resource import (
    ResourceCallSystemMethodMsg as CallSystemMethodMsg,
)
from agentica_internal.warpc.msg.rpc_request_resource import ResourceDelAttrMsg as DelAttrMsg
from agentica_internal.warpc.msg.rpc_request_resource import ResourceGetAttrMsg as GetAttrMsg
from agentica_internal.warpc.msg.rpc_request_resource import ResourceHasAttrMsg as HasAttrMsg
from agentica_internal.warpc.msg.rpc_request_resource import ResourceNewMsg as NewMsg
from agentica_internal.warpc.msg.rpc_request_resource import ResourceRequestMsg
from agentica_internal.warpc.msg.rpc_request_resource import ResourceSetAttrMsg as SetAttrMsg
from agentica_internal.warpc.msg.rpc_sideband import FutureResultMsg
from agentica_internal.warpc.msg.term_resource import SystemResourceMsg as ResourceSysMsg
from agentica_internal.warpc.msg.term_resource import UserResourceMsg as ResourceRefMsg

# Resource data messages are available via the aggregated messages import above
from .conv_utils import *
from .uni_msgs import *
from .uni_msgs import (
    ForeignExceptionUniMsg,
    FrameID,
    GenericExceptionUniMsg,
    InternalErrorUniMsg,
    TypeArgument,
    toMethodSignature,
)

__all__ = ['py_to_uni_rpc']

"""
note: also see warpc/msg/__final__.py for how message classes are finalized...
"""


# Py RPC -> Uni RPC
def py_to_uni_rpc(msg: RPCMsg, ctx: dict[DefnUID, DefUniMsg]) -> RpcUniMsg:
    new_defs = {}

    for py_def in getattr(msg, 'defs', ()):
        py_def_to_uni_def(py_def, new_defs, ctx)

    match msg:
        case RemotePrintMsg(text, origin):
            return consoleLogMsg(f'{origin}\n{text}' if origin else text)

        case ChannelMsg(data=data, last=last):
            term = py_term_to_uni_concept(data.value, new_defs, ctx)
            assert isinstance(term, NoDefUniMsg)
            return ChannelUniMsg(value=term, last=last, defs=list(new_defs.values()))

        case FramedRequestMsg(request=request):
            assert isinstance(request, ResourceRequestMsg)
            frames = py_to_uni_request_ids(msg)
            return py_to_uni_rsrc_request(request, new_defs, ctx, frames)

        case FramedResponseMsg(result=result):
            frames = py_to_uni_response_ids(msg)
            return py_result_to_uni_result(result, new_defs, ctx, frames)

        case FutureResultMsg(result=result_msg):
            # why isn't this using the futureid?
            frames = 0, 0  # legacy approximation; frames not tied to IID
            return py_result_to_uni_result(result_msg, new_defs, ctx, frames)

        case _:
            raise ValueError(f'Unsupported RPC message: {msg}')


CONSOLE_LOG = RefUniMsg(uid=DefnUID(world='client', resource=BUILTIN_UNI_IDS['console.log']))


def consoleLogMsg(text: str):
    from ..core.print import add_gutter, RP_GUTTER

    text = add_gutter(RP_GUTTER, text)
    return CallFunctionUniMsg(
        selfFID=0,
        parentFID=0,
        requestedFID=999,
        payload=CallFunctionPayload(
            fun=CONSOLE_LOG, args=[CallArg(name='arg', val=StrUniMsg(text))]
        ),
        defs=[],
    )


def try_intercept_dict_protocol(
    self_ref: RefUniMsg,
    method_name: str,
    method_args: tuple,
    method_kwargs: dict,
    selfFID: FrameID,
    parentFID: FrameID,
    requestedFID: FrameID,
    new_defs: dict[DefnUID, DefUniMsg],
    ctx: dict[DefnUID, DefUniMsg],
) -> RequestUniMsg | None:
    # TODO: method_kwargs is not used yet!

    # Get owner object definition
    owner_def = new_defs.get(self_ref.uid) or get_def_or_sysref_from_ctx(ctx, self_ref)
    if not isinstance(owner_def, ObjectDefUniMsg):
        return None
    if not isinstance(owner_def.payload.cls, RefUniMsg):
        return None

    # Get class/interface definition
    cls_def = new_defs.get(owner_def.payload.cls.uid) or get_def_or_sysref_from_ctx(
        ctx, owner_def.payload.cls
    )
    if not isinstance(cls_def, (ClassDefUniMsg, InterfaceUniMsg)):
        return None

    # Check if class/interface has index signature
    if cls_def.payload.index_signature is UNSET:
        return None

    # Check if this is a dict protocol method
    if method_name not in ('__getitem__', '__setitem__', '__delitem__', '__contains__'):
        return None

    if len(method_args) == 0:
        key_term = None
    else:
        key_term = py_term_to_uni_concept(method_args[0], new_defs, ctx)

    # Convert key to string attribute name
    attr_name: str | None
    match key_term:
        case StrUniMsg(val=v):
            attr_name = v
        case IntUniMsg(val=v) | FloatUniMsg(val=v):
            attr_name = str(v)
        case BoolUniMsg(val=v):
            # typescript bool is lowercase :((((
            attr_name = str(v).lower()
        case _:
            # Cause a key error on the other side
            attr_name = None

    # Convert to appropriate attribute access message
    match method_name:
        case '__getitem__':
            return GetAttrUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,
                payload=GetAttrPayload(owner=self_ref, attr=attr_name),
                defs=list(new_defs.values()),
            )

        case '__setitem__':
            if len(method_args) < 2:
                value_term = NoDefUniMsg()
            else:
                value_term = py_term_to_uni_concept(method_args[1], new_defs, ctx)
            return SetAttrUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,
                payload=SetAttrPayload(
                    owner=self_ref,
                    attr=attr_name,
                    val=referentialize(value_term),
                ),
                defs=list(new_defs.values()),
            )

        case '__delitem__':
            return DelAttrUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,
                payload=DelAttrPayload(owner=self_ref, attr=attr_name),
                defs=list(new_defs.values()),
            )

        case '__contains__':
            return HasAttrUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,
                payload=HasAttrPayload(owner=self_ref, attr=attr_name),
                defs=list(new_defs.values()),
            )


def py_to_uni_rsrc_request(
    msg: ResourceRequestMsg,
    new_defs: dict[DefnUID, DefUniMsg],
    ctx: dict[DefnUID, DefUniMsg],
    frames: UniRequestIDs,
) -> RequestUniMsg:
    # Helper function for making call-like requests

    def make_args(
        info: NewMsg | CallMsg | CallMethodMsg,
        args_def: list[FunctionArgument] | None = None,  # THIS IS ORDERED
        skip_self: bool = False,
    ) -> list[CallArg]:
        args: dict[str, NoDefUniMsg] = {}
        pos_values = info.pos[1:] if skip_self else info.pos

        # Case 1: we do have a definition for the arguments
        if args_def is not None and args_def is not UNSET:
            # Handle rest parameters: collect remaining args into an array
            pos_idx = 0
            for arg in args_def:
                if arg.rest:
                    # Rest parameter: collect all remaining positional args as an array
                    rest_values = []
                    while pos_idx < len(pos_values):
                        rest_values.append(
                            py_term_to_uni_concept(pos_values[pos_idx], new_defs, ctx)
                        )
                        pos_idx += 1
                    args[arg.name] = referentialize(ArrayUniMsg(val=rest_values))
                elif pos_idx < len(pos_values):
                    # Regular parameter
                    args[arg.name] = referentialize(
                        py_term_to_uni_concept(pos_values[pos_idx], new_defs, ctx)
                    )
                    pos_idx += 1

            # Handle keyword arguments
            for k, v in info.key.items():
                args[k] = referentialize(py_term_to_uni_concept(v, new_defs, ctx))

            # Build final positional args list in order
            pos_args = []
            for arg_name in [arg.name for arg in args_def]:
                if arg_name in args:
                    pos_args.append(CallArg(name=arg_name, val=args[arg_name]))
                else:
                    pass  # let it error on the SDK side!
            return pos_args

        # Case 2: everything goes (...positionally)
        all_args = list(pos_values) + [v for k, v in info.key.items()]
        pos_args = []
        for idx, arg_msg in enumerate(all_args):
            arg_name = f'{idx}'
            uni_arg_ref = referentialize(py_term_to_uni_concept(arg_msg, new_defs, ctx))
            pos_args.append(CallArg(name=arg_name, val=uni_arg_ref))
        return pos_args

    info = msg
    parentFID, selfFID, requestedFID = frames

    # Any new defs nested inside the py request
    new_defs: dict[DefnUID, DefUniMsg] = {}

    match info:
        case NewMsg():
            cls_msg = py_term_to_uni_concept(info.cls, new_defs, ctx)
            if isinstance(cls_msg, RefUniMsg):
                cls_def = new_defs.get(cls_msg.uid) or get_def_or_sysref_from_ctx(ctx, cls_msg)
                if cls_def is None:
                    raise ValueError(f"Class {cls_msg.uid} not found in transcoder context")
                cls_ref = cls_msg
            else:
                cls_def = cls_msg
                cls_ref = referentialize(cls_msg)

            assert isinstance(cls_ref, RefUniMsg), f"Expected ref for cls, got {cls_ref}"

            return CallNewUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,  # TODO: @tali ... a hack but probably ok
                payload=CallNewPayload(
                    cls=cls_ref,
                    args=make_args(
                        info, getattr(getattr(cls_def, "payload", None), "ctor_args", None)
                    ),
                    type_args=UNSET,
                ),
                defs=list(new_defs.values()),
            )

        case CallMsg():
            fun_msg = py_term_to_uni_concept(info.fun, new_defs, ctx)

            # Extract the fun def
            if isinstance(fun_msg, RefUniMsg):
                fun_def = new_defs.get(fun_msg.uid) or get_def_or_sysref_from_ctx(ctx, fun_msg)
                fun_ref = fun_msg
            else:
                fun_def = fun_msg
                fun_ref = referentialize(fun_msg)

            assert isinstance(fun_ref, RefUniMsg), f"Expected ref for fun, got {fun_ref}"

            # Case 1: we have a function definition
            if isinstance(fun_def, (FunctionDefUniMsg, MethodSignatureUniMsg)):
                required_args = sum(1 for arg in fun_def.payload.arguments if not arg.optional)
                has_rest = any(arg.rest for arg in fun_def.payload.arguments)
                if (
                    isinstance(fun_def, MethodSignatureUniMsg)
                    and fun_def.methodOf.kind == 'instance'
                    and len(info.pos) >= required_args + 1  # self + required args
                    and (
                        has_rest or len(info.pos) <= len(fun_def.payload.arguments) + 1
                    )  # if no rest, not more than self + all args
                ):
                    # Owner is first positional argument
                    self_msg = py_term_to_uni_concept(info.pos[0], new_defs, ctx)
                    self_ref = referentialize(self_msg)
                    assert isinstance(self_ref, RefUniMsg), (
                        f"Expected ref for owner, got {self_ref}"
                    )
                    method_name = fun_def.payload.name

                    # Try to intercept dict protocol methods
                    # SURPRISE: x.__getitem__(y) is not a CallMethodMsg, it's a CallMsg!
                    intercepted = try_intercept_dict_protocol(
                        self_ref=self_ref,
                        method_name=method_name,
                        method_args=info.pos[1:],  # Skip self
                        method_kwargs=info.key,
                        selfFID=selfFID,
                        parentFID=parentFID,
                        requestedFID=requestedFID,
                        new_defs=new_defs,
                        ctx=ctx,
                    )
                    if intercepted is not None:
                        return intercepted

                    # Build msg (args excluding the first positional!)
                    return CallMethodUniMsg(
                        selfFID=selfFID,
                        parentFID=parentFID,
                        requestedFID=requestedFID,
                        payload=CallMethodPayload(
                            owner=self_ref,
                            method_name=method_name,
                            args=make_args(info, fun_def.payload.arguments, skip_self=True),
                            method_ref=fun_ref,
                        ),
                        defs=list(new_defs.values()),
                    )

                # Otherwise, regular function call (includes static methods)
                return CallFunctionUniMsg(
                    selfFID=selfFID,
                    parentFID=parentFID,
                    requestedFID=requestedFID,
                    payload=CallFunctionPayload(
                        fun=fun_ref,
                        args=make_args(
                            info,
                            fun_def.payload.arguments,
                        ),
                    ),
                    defs=list(new_defs.values()),
                )

            # Case 2: we don't have a function definition
            return CallFunctionUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,
                payload=CallFunctionPayload(
                    fun=fun_ref,
                    args=make_args(info, None),
                ),
                defs=list(new_defs.values()),
            )

        case CallMethodMsg():
            self_msg = py_term_to_uni_concept(info.obj, new_defs, ctx)
            self_ref = referentialize(self_msg)

            # Extract the owner def
            if isinstance(self_msg, RefUniMsg):
                owner_def = new_defs.get(self_msg.uid) or get_def_or_sysref_from_ctx(ctx, self_msg)
                if owner_def is None:
                    raise ValueError(f"Method {self_msg.uid} not found in transcoder context")
                self_ref = self_msg
            else:
                owner_def = self_msg
                self_ref = referentialize(self_msg)

            assert isinstance(self_ref, RefUniMsg)

            cls_def = None
            if (
                isinstance(owner_def, ObjectDefUniMsg)
                and (cls_ref := owner_def.payload.cls) is not UNSET
            ):
                cls_def = new_defs.get(cls_ref.uid) or get_def_or_sysref_from_ctx(ctx, cls_ref)

            # Case 1: we have the object's class definition
            if isinstance(cls_def, (ClassDefUniMsg, InterfaceUniMsg)):
                # Try to intercept dict protocol methods
                intercepted = try_intercept_dict_protocol(
                    self_ref=self_ref,
                    method_name=info.mth,
                    method_args=info.pos,
                    method_kwargs=info.key,
                    selfFID=selfFID,
                    parentFID=parentFID,
                    requestedFID=requestedFID,
                    new_defs=new_defs,
                    ctx=ctx,
                )
                if intercepted is not None:
                    return intercepted

                for method in getattr(cls_def.payload, "methods", []):
                    if method.name == info.mth:
                        method_ref = method.function
                        method_def = new_defs.get(method_ref.uid) or get_def_or_sysref_from_ctx(
                            ctx, method_ref
                        )
                        method_name = info.mth
                        break
                else:
                    # let it error on the SDK side!
                    method_def = None
                    method_ref = UNSET
                    method_name = info.mth

                # Build the call method uni msg
                return CallMethodUniMsg(
                    selfFID=selfFID,
                    parentFID=parentFID,
                    requestedFID=requestedFID,
                    payload=CallMethodPayload(
                        owner=self_ref,
                        method_name=method_name,
                        args=make_args(
                            info,
                            getattr(getattr(method_def, "payload", None), "arguments", None),
                        ),
                        method_ref=method_ref,
                    ),
                    defs=list(new_defs.values()),
                )

            # Case 2: we don't have the object's class definition
            return CallMethodUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,
                payload=CallMethodPayload(
                    owner=self_ref,
                    method_name=info.mth,  # py_to_ts_method_equivalent(info.mth),
                    args=make_args(info, None),
                    method_ref=UNSET,
                ),
                defs=list(new_defs.values()),
            )

        case CallSystemMethodMsg():
            self_msg = py_term_to_uni_concept(info.obj, new_defs, ctx)
            self_ref = referentialize(self_msg)
            fun_msg = info.fun
            if fun_msg.sys_resource is str:  # because str already means String
                fun_uid = BUILTIN_UNI_IDS['magicStr']
            else:
                fun_uid = sridToUniSysId(fun_msg.sid)
            if fun_uid is None:
                raise ValueError(
                    f"System method {fun_msg.sid} not found in transcoder context ... it may yet not be supported in the universal model."
                )
            fun_ref = RefUniMsg(uid=DefnUID(world='client', resource=fun_uid))

            return CallFunctionUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,
                payload=CallFunctionPayload(
                    fun=fun_ref,
                    args=[CallArg(name='arg', val=self_ref)],
                ),
            )

        case HasAttrMsg():
            self_msg = py_term_to_uni_concept(info.obj, new_defs, ctx)
            self_ref = referentialize(self_msg)

            # Validation
            assert isinstance(self_ref, RefUniMsg), (
                f"Expected ref for HasAttr owner, got {self_ref}"
            )

            attr_name = info.attr
            return HasAttrUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,
                payload=HasAttrPayload(
                    owner=self_ref,
                    attr=attr_name,
                ),
                defs=list(new_defs.values()),
            )

        case GetAttrMsg():
            self_msg = py_term_to_uni_concept(info.obj, new_defs, ctx)
            self_ref = referentialize(self_msg)

            # Validation
            assert isinstance(self_ref, RefUniMsg), (
                f"Expected ref for GetAttr owner, got {self_ref}"
            )

            attr_name = info.attr
            return GetAttrUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,  # TODO: @tali ... a hack but probably ok
                payload=GetAttrPayload(
                    owner=self_ref,
                    attr=attr_name,
                ),
                defs=list(new_defs.values()),
            )
        case SetAttrMsg():
            self_msg = py_term_to_uni_concept(info.obj, new_defs, ctx)
            self_ref = referentialize(self_msg)

            # Validation
            assert isinstance(self_ref, RefUniMsg), (
                f"Expected ref for SetAttr owner, got {self_ref}"
            )

            attr_name = info.attr
            val_msg = py_term_to_uni_concept(info.val, new_defs, ctx)
            val_ref = referentialize(val_msg)

            # Validation
            assert isinstance(val_ref, NoDefUniMsg), f"Expected term for SetAttr val, got {val_ref}"

            return SetAttrUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,  # TODO: @tali ... a hack but probably ok
                payload=SetAttrPayload(
                    owner=self_ref,
                    attr=attr_name,
                    val=val_ref,
                ),
                defs=list(new_defs.values()),
            )
        case DelAttrMsg():
            self_msg = py_term_to_uni_concept(info.obj, new_defs, ctx)
            self_ref = referentialize(self_msg)

            # Validation
            assert isinstance(self_ref, RefUniMsg), (
                f"Expected ref for DelAttr owner, got {self_ref}"
            )
            if isinstance(self_msg, (FunctionDefUniMsg)):
                raise ValueError(f"Cannot delete attribute on function: {self_msg}")

            attr_name = info.attr
            return DelAttrUniMsg(
                selfFID=selfFID,
                parentFID=parentFID,
                requestedFID=requestedFID,  # TODO: @tali ... a hack but probably ok
                payload=DelAttrPayload(
                    owner=self_ref,
                    attr=attr_name,
                ),
                defs=list(new_defs.values()),
            )
        case _:
            raise ValueError(f'Unsupported request for universal messages: {info}')


def py_result_to_uni_result(
    result: ResultMsg,
    new_defs: dict[DefnUID, DefUniMsg],
    ctx: dict[DefnUID, DefUniMsg],
    frames: UniResponseIDs,
) -> ResponseUniMsg:  # type: ignore
    parentFID, selfFID = frames
    done = result.done
    value = result.value
    error = result.error

    payload = py_result_to_uni_payload(result, new_defs, ctx)
    if isinstance(payload, ErrPayload):
        return ErrUniMsg(selfFID=selfFID, parentFID=parentFID, payload=payload)
    else:
        defs = list(new_defs.values())
        return ResUniMsg(selfFID=selfFID, parentFID=parentFID, payload=payload, defs=defs)


def py_result_to_uni_payload(
    result: ResultMsg,
    new_defs: dict[DefnUID, DefUniMsg],
    ctx: dict[DefnUID, DefUniMsg],
) -> ErrPayload | ResPayload:  # type: ignore
    done = result.done
    value = result.value
    error = result.error

    if error is not None or not done:
        exc_msg = to_exc_uni_msg(error, new_defs, ctx)
        return ErrPayload(error=exc_msg)

    term = py_term_to_uni_concept(value, new_defs, ctx)

    # Validation
    assert isinstance(term, (NoDefUniMsg, DefUniMsg)), f"Expected term for Res, got {term}"

    return ResPayload(result=term)


def to_exc_uni_msg(
    exc: ExceptionMsg | None, new_defs: dict[DefnUID, DefUniMsg], ctx: dict[DefnUID, DefUniMsg]
) -> GenericExceptionUniMsg | InternalErrorUniMsg | ForeignExceptionUniMsg:
    match exc:
        case ShallowUserExceptionMsg(ident=ident, exc_str=exc_str):
            return GenericExceptionUniMsg(
                excp_cls_name=ident.name, excp_str_args=[exc_str], excp_stack=[]
            )
        case SystemExceptionMsg(exc_cls, exc_args):
            from .conv_utils import sridToUniSysId

            uni_res_id = sridToUniSysId(exc_cls.sid)
            if uni_res_id is None:
                return GenericExceptionUniMsg(
                    excp_cls_name=exc_cls.sys_cls.__name__,
                    excp_str_args=[a.v for a in exc_args if isinstance(a, StrMsg)],
                    excp_stack=[],
                )
            excp_cls = py_term_to_uni_concept(exc_cls, new_defs, ctx)
            excp_args = [py_term_to_uni_concept(v, new_defs, ctx) for v in exc_args]
            return ForeignExceptionUniMsg(excp_cls=excp_cls, excp_args=excp_args)  # type: ignore

        case DeepUserExceptionMsg(exc_ref=exc_ref, exc_str=exc_str):
            # hack: look up the ForeignExceptionUniMsg that was stored previously in py_def_to_uni_def when it saw
            # ExceptionDataMsg
            uid = gridToResourceUID(exc_ref.rid)
            match ctx.get(uid):
                # if TS originally sent the exception, the current way the transcoder (and TS protocol)
                # are designed, we have no choice but to make a copy of it that includes the raw string
                # we'd need a pass-by-reference version of the TS exception msg
                case ObjectDefUniMsg(payload=ObjectPayload(name=name, cls=excp_cls)):
                    match ctx.get(excp_cls.uid):
                        case ClassDefUniMsg(payload=ClassPayload(), uid=uid):
                            excp_args = [StrUniMsg(exc_str)] if exc_str else []
                            return ForeignExceptionUniMsg(excp_cls=excp_cls, excp_args=excp_args)
                # otherwise, if python originally sent the exception, we translated it previously
                # in py_def_to_uni_def when we saw its ExceptionDataMsg
                case ForeignExceptionUniMsg() as exc_msg:
                    return exc_msg

        case InternalExceptionMsg(error):
            return InternalErrorUniMsg(error=error)

    return InternalErrorUniMsg(error="unknown error")


# Py Term -> Uni Concept
def py_term_to_uni_concept(
    term: TermMsg, new_defs: dict[DefnUID, DefUniMsg], ctx: dict[DefnUID, DefUniMsg]
) -> ConceptUniMsg:  # type: ignore
    assert isinstance(term, TermMsg), f"not a TermMsg: {term}"
    match term:
        case ResourceMsg():
            match term:
                case ResourceRefMsg():
                    uid = gridToResourceUID(term.rid)
                    return RefUniMsg(uid=uid)
                case ResourceSysMsg():
                    # Map Python system RID to universal negative ID if possible
                    from .conv_utils import sridToUniSysId

                    uni_res_id = sridToUniSysId(term.sid)
                    if uni_res_id is None:
                        uid = DefnUID(world='client', resource=term.sid)
                        # Fallback: synthesize a minimal class definition for builtin classes
                        # so non-Python runtimes can treat them like user-defined classes.
                        if uid in ctx:
                            return RefUniMsg(uid=uid, system=True)

                        if isinstance(term.sys_cls, type):
                            ref = py_system_cls_to_uni_cls(term, new_defs, ctx)
                            ctx[uid] = ref
                            return ref
                        raise NotImplementedError("ResourceSysMsg mapping not available")

                    uid = DefnUID(world='client', resource=uni_res_id)
                    return RefUniMsg(uid=uid, system=True)

        case AtomMsg():
            # Map based on concrete atom message classes
            from agentica_internal.warpc.msg.term_atom import BytesMsg, NumberMsg, StrMsg
            from agentica_internal.warpc.msg.term_atom import NoneMsg as PyNoneMsg

            if isinstance(term, PyNoneMsg):
                return NoneUniMsg(val=None)
            if isinstance(term, NumberMsg):
                v = term.v
                if isinstance(v, bool):
                    return BoolUniMsg(val=v)
                if isinstance(v, int):
                    return IntUniMsg(v)
                if isinstance(v, float):
                    return FloatUniMsg(v)
            if isinstance(term, StrMsg):
                return StrUniMsg(term.v)
            if isinstance(term, BytesMsg):
                return BytesUniMsg(val=term.v)
            raise ValueError(f'Unsupported atom message {type(term).__name__}')
        case ContainerMsg():
            match term:
                case MappingMsg():
                    keys = [
                        referentialize(py_term_to_uni_concept(k, new_defs, ctx)) for k in term.ks
                    ]
                    vals = [
                        referentialize(py_term_to_uni_concept(v, new_defs, ctx)) for v in term.vs
                    ]
                    from .uni_msgs import MapPayload

                    return MapUniMsg(val=MapPayload(keys=keys, vals=vals))
                case SequenceMsg():
                    return ArrayUniMsg(
                        val=[
                            referentialize(py_term_to_uni_concept(v, new_defs, ctx))
                            for v in term.vs
                        ]
                    )
                case SlotObjMsg():
                    raise ValueError("SlotObjMsg is not supported in universal messages")
        case EnumMemberMsg():
            if isinstance(term, EnumValMsg):
                valMsg = py_term_to_uni_concept(term.val, new_defs, ctx)
                assert isinstance(valMsg, (StrUniMsg, IntUniMsg, FloatUniMsg)), (
                    f"Expected str, int, or float for enum value, got {valMsg}"
                )
                clsMsg = py_term_to_uni_concept(term.cls, new_defs, ctx)
                clsRef = referentialize(clsMsg)
                assert isinstance(clsRef, RefUniMsg), f"Expected ref for enum class, got {clsRef}"
                return EnumValUniMsg(val=valMsg, cls=clsRef)
            elif isinstance(term, EnumKeyMsg):
                clsMsg = py_term_to_uni_concept(term.cls, new_defs, ctx)
                clsRef = referentialize(clsMsg)
                assert isinstance(clsRef, RefUniMsg), f"Expected ref for enum class, got {clsRef}"
                classDef = get_def_or_sysref_from_ctx(ctx, clsRef)
                assert isinstance(classDef, ClassDefUniMsg), (
                    f"Expected ClassDefUniMsg, got {classDef}"
                )
                assert isinstance(classDef.payload.supplied_type_args, list), (
                    f"Expected enum class to have supplied_type_args"
                )
                for typeArg in classDef.payload.supplied_type_args:
                    if typeArg.name == term.key:
                        valMsg = typeArg.type
                        assert isinstance(valMsg, (StrUniMsg, IntUniMsg, FloatUniMsg)), (
                            f"Expected str, int, or float for enum value, got {valMsg}"
                        )
                        return EnumValUniMsg(val=valMsg, cls=clsRef)
                raise ValueError(f"Enum key '{term.key}' not found in class {clsRef.uid}")
            else:
                raise ValueError(f"Unsupported enum member message: {term}")
        case DeepUserExceptionMsg(exc_ref=exc_ref):
            uid = gridToResourceUID(exc_ref.rid)
            return RefUniMsg(uid=uid)

        case _:
            raise ValueError(f'Unknown Term message: {term}')


def py_system_cls_to_uni_cls(
    term: ResourceSysMsg, new_defs: dict[DefnUID, DefUniMsg], ctx: dict[DefnUID, DefUniMsg]
) -> ClassDefUniMsg:
    uid = DefnUID(world='client', resource=term.sid)

    # Construct minimal class payload via inspection
    bases_refs: list[RefUniMsg] = []
    try:
        from agentica_internal.warpc.msg.term_resource import SystemResourceMsg as PyResourceSysMsg
        from agentica_internal.warpc.system import LRID_TO_SRID

        for base in getattr(term.sys_cls, '__bases__', ()):  # type: ignore[attr-defined]
            base_sid = LRID_TO_SRID.get(id(base))
            if base_sid is None:
                continue
            base_concept = py_term_to_uni_concept(PyResourceSysMsg(sid=base_sid), new_defs, ctx)
            base_ref = referentialize(base_concept)
            if isinstance(base_ref, RefUniMsg):
                bases_refs.append(base_ref)
    except Exception:
        # Give up with no bases
        bases_refs = []

    # Best-effort: expose all attributes and methods as fields with unknown type (Object)
    # so non-Python runtimes can discover callable/values via getattr
    from .uni_sys_id import BUILTIN_UNI_IDS

    object_uid = DefnUID(world='client', resource=BUILTIN_UNI_IDS.get('Object', 0))
    object_ref = RefUniMsg(uid=object_uid, system=True)
    field_names: list[str] = []
    try:
        # dir() provides a superset including inherited attributes
        for name in dir(term.sys_cls):
            if not name or name.startswith('__') and name.endswith('__'):
                continue
            field_names.append(name)
    except Exception:
        field_names = []
    fields: list[ClassField] = [ClassField(name=n, type=object_ref) for n in field_names]

    payload = ClassPayload(
        name=getattr(term.sys_cls, '__name__', 'Unknown'),
        doc=unsetNone(getattr(term.sys_cls, '__doc__', None)),
        module=unsetNone(getattr(term.sys_cls, '__module__', None)),
        fields=fields,
        methods=[],
        bases=bases_refs if bases_refs else UNSET,
        supplied_type_args=UNSET,
        ctor_args=UNSET,
        system_resource=True,
    )

    uni_def = ClassDefUniMsg(uid=uid, payload=payload)
    if uid not in new_defs:
        new_defs[uid] = uni_def
    return uni_def


def get_class_def_from_name(cls_name: str, ctx: dict[DefnUID, DefUniMsg]) -> ClassDefUniMsg | None:
    for msg in ctx:
        if isinstance(msg, ClassDefUniMsg) and msg.payload.name == cls_name:
            return msg
    return None


# Py Def -> Uni Def
def py_def_to_uni_def(
    defmsg: DefinitionMsg, new_defs: dict[DefnUID, DefUniMsg], ctx: dict[DefnUID, DefUniMsg]
) -> None:
    uni_def: DefUniMsg
    uid = gridToResourceUID(defmsg.rid)

    match defmsg.data:
        case ExceptionDataMsg(cls, args):
            # hack: we have to save this VALUE somewhere for when the DeepUserExceptionMsg gets decoded
            # so use the python RID as a key, since we can't introduce a third
            # dictionary that gets passed around everywhere.
            cls_uid = gridToResourceUID(cls.rid)
            cls_ref = RefUniMsg(uid=cls_uid)
            exc_msg = ForeignExceptionUniMsg(
                excp_cls=cls_ref,
                excp_args=[py_term_to_uni_concept(v, new_defs, ctx) for v in args],  # type: ignore
            )
            ctx[defmsg.rid] = exc_msg  # type: ignore
            return

        case ClassDataMsg():
            payload = class_data_to_class_payload(defmsg.data, uid, new_defs, ctx)
            uni_def = ClassDefUniMsg(uid=uid, payload=payload)

        case GenericAliasDataMsg():
            # TODO: needed? untested!
            origin_term = defmsg.data.origin
            base_uid: DefnUID
            if isinstance(origin_term, ResourceSysMsg):
                from .conv_utils import sridToUniSysId

                uni_res_id = sridToUniSysId(origin_term.sid)
                if uni_res_id is None:
                    raise NotImplementedError(
                        "ResourceSysMsg mapping not available for GenericAlias"
                    )
                base_uid = DefnUID(world='client', resource=uni_res_id)
            else:
                origin_uni = py_term_to_uni_concept(origin_term, new_defs, ctx)
                origin_ref = referentialize(origin_uni)
                assert isinstance(origin_ref, RefUniMsg), (
                    f"Expected ref for origin, got {origin_ref}"
                )
                base_uid = origin_ref.uid

            # Map args to RefUniMsg dictionary
            type_args: list[TypeArgument] = []
            for idx, arg_term in enumerate(defmsg.data.args):
                arg_uni = py_term_to_uni_concept(arg_term, new_defs, ctx)
                arg_ref = referentialize(arg_uni)
                assert isinstance(arg_ref, RefUniMsg), f"Expected ref for type arg, got {arg_ref}"
                type_args.append(TypeArgument(name=f'a{idx}', type=arg_ref))

            payload = ClassPayload(
                name='GenericAlias',
                fields=[],
                methods=[],
                instance_of_generic=base_uid,
                supplied_type_args=type_args,
            )
            uni_def = ClassDefUniMsg(uid=uid, payload=payload)
        case FunctionDataMsg(ident=ident, sig=sig) as fdata:
            payload = function_data_to_function_payload(fdata, uid, new_defs, ctx)
            uni_def = fn_def = FunctionDefUniMsg(uid=uid, payload=payload)
            if ident.qual is not None and ident.name != ident.qual:
                cls_name = ident.qual.split(".")[0]
                cls_uid = get_class_def_from_name(cls_name, ctx)
                if cls_uid is not None:
                    uni_def = toMethodSignature(
                        fn_def,
                        Membership(
                            uid=cls_uid.uid, kind='instance'
                        ),  # TODO: @tali instance vs static
                    )
        case ObjectDataMsg():
            payload = object_data_to_object_payload(defmsg.data, uid, new_defs, ctx)
            uni_def = ObjectDefUniMsg(uid=uid, payload=payload)
        case TypeUnionDataMsg():
            # Encode union as an annotation UnionUniMsg with classes as refs
            classes: list[RefUniMsg] = []
            for alt in defmsg.data.alts:
                alt_uni = py_term_to_uni_concept(alt, new_defs, ctx)
                alt_ref = referentialize(alt_uni)
                assert isinstance(alt_ref, RefUniMsg)
                classes.append(alt_ref)
            uni_def = UnionUniMsg(uid=uid, payload=UnionPayload(classes=classes))
        case _:
            raise ValueError(f'Unsupported resource data type {defmsg} in universal messages')

    uid = uni_def.uid
    assert uid not in ctx, f"Definition {uid} already exists in context ... this shouldn't happen"
    ctx[uid] = uni_def
    if uid not in new_defs:
        new_defs[uid] = uni_def


# Py Class Data -> Uni Class Payload
def class_data_to_class_payload(
    data: ClassDataMsg,
    uid: DefnUID,
    new_defs: dict[DefnUID, DefUniMsg],
    ctx: dict[DefnUID, DefUniMsg],
) -> ClassPayload:
    if data.name == 'GenericAlias':
        # raise ValueError("GenericAlias translation is not supported yet")
        return ClassPayload(name="GenericAlias", fields=[], methods=[])  # TODO: @tali

    bases: list[RefUniMsg] = []
    methods: list[ClassMethod] = []
    fields: list[ClassField] = []
    ctor_args: list[FunctionArgument] | UnsetType = UNSET
    supplied_type_args: list[TypeArgument] | UnsetType = UNSET  # TODO: not implemented

    for base in data.bases:  # type: ignore # see warpc/msg/__final__.py
        base_msg = py_term_to_uni_concept(base, new_defs, ctx)
        field_type_ref = referentialize(base_msg)

        # Validation
        assert isinstance(field_type_ref, RefUniMsg), f"Expected reference, got {field_type_ref}"
        if isinstance(base_msg, (ObjectDefUniMsg, FunctionDefUniMsg)):
            raise ValueError(f"Got obj/fun def for class base: {base_msg}")

        bases.append(field_type_ref)

    for name, method in data.methods.items():  # type: ignore # see warpc/msg/__final__.py
        # MethodsMsg: mapping name -> (kind, ResourceMsg)
        method_kind, method_res = method
        fun_msg = py_term_to_uni_concept(method_res, new_defs, ctx)

        if isinstance(fun_msg, RefUniMsg):
            method_ref = fun_msg
            methods.append(ClassMethod(name=name, function=method_ref))
        else:
            assert isinstance(fun_msg, FunctionDefUniMsg), (
                f"Expected function def for method, got {fun_msg}"
            )
            mk = 'static' if method_kind in ('class', 'static') else 'instance'
            membership = Membership(uid=uid, kind=mk)  # type: ignore[arg-type]
            method_def = function_to_method(fun_msg, membership)
            method_ref = referentialize(method_def)
            assert isinstance(method_ref, RefUniMsg), "reffy ref erf"

            # Overwrite fun def with method def (keyed by (world, resource))
            new_defs[(method_def.uid.world, method_def.uid.resource)] = method_def  # type: ignore[index]
            if name == '__init__':
                ctor_args = fun_msg.payload.arguments
            else:
                methods.append(ClassMethod(name=name, function=method_ref))

    for name, field_type_msg in data.annos.items():
        field_type_msg = py_term_to_uni_concept(field_type_msg, new_defs, ctx)
        field_type_ref = referentialize(field_type_msg)

        # Validation
        if isinstance(field_type_msg, (ObjectDefUniMsg, FunctionDefUniMsg)):
            # raise ValueError(f"Got obj/fun def for field type: {field_type_msg}"
            field_type = ClassDefUniMsg(  # TODO: @tali
                uid=field_type_msg.uid,
                payload=ClassPayload(name="GenericAlias", fields=[], methods=[]),
            )
            field_type_ref = referentialize(field_type)
        assert isinstance(field_type_ref, RefUniMsg), (
            f"Expected ref for field type, got {field_type_ref}"
        )

        fields.append(ClassField(name=name, type=field_type_ref))
    # TODO: translate attrs and sattrs into universal model @tali

    return ClassPayload(
        name=data.name,
        doc=unsetNone(data.doc),
        module=unsetNone(data.module),
        instance_of_generic=UNSET,  # TODO: not implemented @tali
        bases=bases,
        methods=methods,
        fields=fields,
        supplied_type_args=supplied_type_args,  # TODO: not implemented
        ctor_args=ctor_args,
    )


# Py Fun Data -> Uni Fun Payload
def function_data_to_function_payload(
    data: FunctionDataMsg,
    uid: DefnUID,
    defs: dict[DefnUID, DefUniMsg],
    ctx: dict[DefnUID, DefUniMsg],
) -> FunctionPayload:
    arguments: list[FunctionArgument] = []
    return_type: RefUniMsg | UnsetType = UNSET

    ident = data.ident
    sig = data.sig

    annos = sig.annos
    defaults = sig.defaults

    for arg_name in sig.pos_args + sig.key_args:
        if arg_name in annos:
            anno = annos[arg_name]
            ref = referentialize(py_term_to_uni_concept(anno, defs, ctx))
            assert isinstance(ref, RefUniMsg)
        else:
            ref = None
        optional = arg_name in defaults
        arg = FunctionArgument(name=arg_name, type=ref, optional=optional)
        arguments.append(arg)

    if ret_msg := annos.pop('return', None):
        ref = referentialize(py_term_to_uni_concept(ret_msg, defs, ctx))
        assert isinstance(ref, RefUniMsg)
        return_type = ref

    return FunctionPayload(
        name=ident.name, doc=unsetNone(sig.doc), arguments=arguments, returnType=return_type
    )


# Py Object Data -> Uni Object Payload
def object_data_to_object_payload(
    data: ObjectDataMsg,
    uid: DefnUID,
    defs: dict[DefnUID, DefUniMsg],
    ctx: dict[DefnUID, DefUniMsg],
) -> ObjectPayload:
    cls_msg = py_term_to_uni_concept(data.cls, defs, ctx)
    cls_ref = referentialize(cls_msg)

    # Validation
    assert isinstance(cls_ref, RefUniMsg), f"Expected ref for cls, got {cls_ref}"
    if isinstance(cls_msg, (ObjectDefUniMsg, FunctionDefUniMsg)):
        raise ValueError(f"Got obj/fun def for cls: {cls_msg}")

    return ObjectPayload(name=UNSET, cls=cls_ref, keys=[k for k in data.keys])


# DUNDER_TO_TS_METHOD = {
#     '__str__':      'toString',
#     '__repr__':     'toString',
#     '__contains__': 'includes',
# }
#
# def py_to_ts_method_equivalent(name: str) -> str:
#     return DUNDER_TO_TS_METHOD.get(name, name)
