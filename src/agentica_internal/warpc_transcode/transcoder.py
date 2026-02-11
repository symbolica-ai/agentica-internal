from __future__ import annotations

from asyncio import Protocol
from collections import defaultdict, deque
from collections.abc import Callable

import msgspec
import msgspec.json
import msgspec.msgpack

from agentica_internal.core.print import colorize, hdiv, tprint
from agentica_internal.warpc.msg.all import (
    Msg,
    DefinitionMsg,
    ListMsg,
    RPCMsg,
    StrMsg,
    VarsMsg,
    TermMsg,
)
from agentica_internal.warpc.worlds.interface import AsyncRecvBytes, AsyncSendBytes
from agentica_internal.warpc_transcode.conv_utils import (
    LOG_TS,
    ORDER_MARKER,
    MangleManager,
    msg_TS_name_restoration,
    msg_uni_name_sanitization,
    order_defs,
    f_uid_grid,
)
from agentica_internal.warpc_transcode.py_to_uni import py_to_uni_rpc
from agentica_internal.warpc_transcode.uni_msgs import (
    DefnUID,
    DefUniMsg,
    FutureCompletedUniMsg,
    RequestUniMsg,
    ResUniMsg,
    RpcUniMsg,
    TermUnion,
    UniMsg,
    json_to_concept_uni,
    json_to_rpc_uni,
    uni_to_json,
)
from agentica_internal.warpc_transcode.uni_to_py import uni_to_py_def, uni_to_py_rpc, uni_to_py_term


class InterceptorProto(Protocol):
    def decode_defs(self, warpc_locals: bytes) -> bytes: ...
    def intercept_sdk(
        self, recv_from_sdk: AsyncRecvBytes, send_to_sdk: AsyncSendBytes
    ) -> tuple[AsyncRecvBytes, AsyncSendBytes]: ...


class NoopInterceptor(InterceptorProto):
    def decode_defs(self, warpc_locals: bytes) -> bytes:
        return warpc_locals

    def intercept_sdk(
        self, recv_from_sdk: AsyncRecvBytes, send_to_sdk: AsyncSendBytes
    ) -> tuple[AsyncRecvBytes, AsyncSendBytes]:
        return recv_from_sdk, send_to_sdk


TRANS = colorize('Transcoder')


class TranscodingInterceptor(InterceptorProto):
    defn_ctx: dict[DefnUID, DefUniMsg]
    mangler: MangleManager
    _orig_recv_bytes: AsyncRecvBytes | None
    _orig_send_bytes: AsyncSendBytes | None
    logging: bool

    def __init__(
        self,
        log: Callable[..., None] | None = None,
    ) -> None:
        self._msg_counter = 0
        self._in_queue: deque[RPCMsg] = deque()
        self.defn_ctx = {}
        self.mangler = MangleManager()
        self.logging = bool(LOG_TS)
        self.log("init")

    def log(self, *args) -> None:
        # note to others: you can either use FORE_ENABLE_LOGGING=TS, or
        # ./run_local.sh --tags=TS ...
        # ./run_local_pylog.sh test_something TS
        # or even just setting self.logging = True temporarily
        if self.logging:
            tprint(TRANS, *args)

    def log_msg(self, msg: UniMsg | Msg):
        if self.logging:
            msg.pprint()
            hdiv()

    def decode_defs(self, warpc_locals: bytes) -> bytes:
        self.log("decode_defs")

        # Case of empty warpc_globals
        if not warpc_locals or not warpc_locals.strip():
            return msgspec.msgpack.Encoder().encode({})
        dict_decoder = msgspec.json.Decoder(dict[str, msgspec.Raw])
        transcoded_vars: dict[str, TermMsg] = {}
        def_msgs: list['DefinitionMsg'] = []

        raw_dict = dict_decoder.decode(warpc_locals)

        # Populate context and map defs uid to set of names of locals with that defn
        uid_to_local_name: defaultdict[DefnUID, set[str]] = defaultdict(set)
        locals_without_uid: dict[str, TermUnion] = {}
        for name, json_bytes in raw_dict.items():
            if name == "":
                raise ValueError("Var cannot be empty")

            try:
                term_msg = json_to_concept_uni(json_bytes)
                # Sanitize names from TypeScript by mangling TS identifiers to Python identifiers
                term_msg = msg_uni_name_sanitization(term_msg, self.mangler)
                name = self.mangler.mangle(name)
            except Exception as e:
                self.log("error json bytes; json_bytes =")
                # print("BYTES", bytes(json_bytes))
                raise e

            self.log("locals parsing incoming, var ", name, "| parsed:")
            self.log_msg(term_msg)

            if hasattr(term_msg, 'uid') and term_msg.uid is not None:
                assert isinstance(term_msg, DefUniMsg), f"Locals with uid should be definitions"
                self.defn_ctx[term_msg.uid] = term_msg
                uid_to_local_name[term_msg.uid].add(name)
            else:
                locals_without_uid[name] = term_msg

        # Order defs by referential dependencies
        ordered_defs, _ = order_defs(list(self.defn_ctx.values()))

        self.log(f"@@@ uid_to_local_name: {uid_to_local_name}")

        # Transcode definitions and collect Vars mapping + defs list
        local_count = 0
        for def_msg in ordered_defs:
            for name in uid_to_local_name[def_msg.uid]:
                self.log(f"transcoding local def parent {name}|{local_count} ... input msg:")
                self.log_msg(def_msg)
                assert isinstance(def_msg, DefUniMsg), (
                    f"Expected DefUniMsg in warpc_locals, got {def_msg}"
                )
                if def_msg.uid not in self.defn_ctx:
                    self.defn_ctx[def_msg.uid] = def_msg
                synths: list[DefUniMsg] = []
                native_def = uni_to_py_def(def_msg, self.defn_ctx, name=name, synthetic_defs=synths)
                self.log("primary output msg:")
                self.log_msg(native_def)
                # Add synths first
                for syn in synths:
                    self.log(f"enqueuing synthetic def:\n{syn}")
                    def_msgs.append(uni_to_py_def(syn, self.defn_ctx))
                # Then parent
                def_msgs.append(native_def)
                # Set variable to a reference to the defined resource (with order marker)
                marked_name = name + ORDER_MARKER + str(local_count)
                local_count += 1
                transcoded_vars[marked_name] = native_def.as_ref
                self.log("defined variable:", marked_name, "->", native_def.as_ref)

        # Collect names of non-top-level definitions to hide
        hidden_names: set[str] = set()
        for term_msg in ordered_defs:
            if hasattr(term_msg, 'payload') and hasattr(term_msg.payload, 'is_top_level'):
                if not term_msg.payload.is_top_level:
                    for name in uid_to_local_name[term_msg.uid]:
                        hidden_names.add(name)

        # Add locals that are defless terms
        for name, msg in locals_without_uid.items():
            self.log("transcoding local term:", name, "|", local_count, " input:")
            self.log_msg(msg)

            native_msg = uni_to_py_term(msg, self.defn_ctx)

            self.log("transcoding local term:", name, "|", local_count, " output:")
            self.log_msg(native_msg)

            marked_name = name + ORDER_MARKER + str(local_count)
            local_count += 1
            transcoded_vars[marked_name] = native_msg
            self.log("marked_name:", marked_name)

        self.log("processed local count: ", len(transcoded_vars))
        self.log("hidden names: ", hidden_names)

        # Build VarsMsg with collected vars and defs; attach hidden names for REPL to hide
        if hidden_names:
            try:
                hidden_list = tuple(StrMsg(v=name) for name in hidden_names)
                transcoded_vars['__hidden_names'] = ListMsg(vs=hidden_list)
                self.log("hidden names:", hidden_names)
            except Exception:
                pass
        vars_msg = VarsMsg(vars=transcoded_vars, defs=tuple(def_msgs))
        return vars_msg.to_msgpack()

    def transcode_to_py(self, uni_msg: RpcUniMsg) -> RPCMsg:
        self.log("transcode_to_py incoming")
        self.log_msg(uni_msg)

        self._msg_counter += 1

        # Sanitize names from TypeScript by mangling TS identifiers to Python identifiers
        uni_msg = msg_uni_name_sanitization(uni_msg, self.mangler)

        # Update context _before_ transcoding
        if isinstance(uni_msg, (RequestUniMsg, ResUniMsg)):
            for defmsg in uni_msg.defs:
                self.defn_ctx[defmsg.uid] = defmsg
        if isinstance(uni_msg, FutureCompletedUniMsg):
            self.log("updating context from future completed defs")
            if hasattr(uni_msg.result, 'defs') and isinstance(uni_msg.result, ResUniMsg):
                self.log("found defs in future completed result")
                for defmsg in uni_msg.result.defs:
                    self.defn_ctx[defmsg.uid] = defmsg

        # Transcode
        py_msg = uni_to_py_rpc(uni_msg, self.defn_ctx)
        self.log("transcode_to_py outgoing")
        self.log_msg(py_msg)
        return py_msg

    def transcode_to_uni(self, py_msg: RPCMsg) -> RpcUniMsg:
        self.log("transcode_to_uni incoming")
        self.log_msg(py_msg)

        self._msg_counter += 1

        # Context will be updated while transcoding
        uni_msg = py_to_uni_rpc(py_msg, self.defn_ctx)

        # Restore names for TypeScript by demangling Python identifiers back to TS identifiers
        uni_msg = msg_TS_name_restoration(uni_msg, self.mangler)

        self.log("transcode_to_uni outgoing")
        self.log_msg(uni_msg)
        return uni_msg

    def intercept_sdk(
        self, recv_from_sdk: AsyncRecvBytes, send_to_sdk: AsyncSendBytes
    ) -> tuple[AsyncRecvBytes, AsyncSendBytes]:
        self._orig_recv_bytes = recv_from_sdk
        self._orig_send_bytes = send_to_sdk

        async def transcoded_recv_from_sdk() -> bytes:
            assert self._orig_recv_bytes is not None, "Transcoder recv_bytes is not set"
            warpc_msg = await self._orig_recv_bytes()
            rpc_msg: RpcUniMsg = json_to_rpc_uni(warpc_msg)
            try:
                py_msg = self.transcode_to_py(rpc_msg)
            except Exception as e:
                tprint(TRANS, f"{type(e).__name__} during TypeScript -> Python", err=True)
                rpc_msg.pprint()
                e.add_note(f"TS MSG={rpc_msg!r}")
                raise
            return py_msg.to_msgpack()

        async def transcoded_send_to_sdk(data: bytes) -> None:
            assert self._orig_send_bytes is not None, "Transcoder send_bytes is not set"
            rpc_msg = RPCMsg.from_msgpack(data)
            try:
                uni_msg = self.transcode_to_uni(rpc_msg)
            except Exception as e:
                tprint(TRANS, f"{type(e).__name__} during Python -> TypeScript", err=True)
                rpc_msg.pprint()
                e.add_note("PY MSG=" + rpc_msg.msgpack_str(multiline=False))
                raise
            uni_msg_json = uni_to_json(uni_msg)
            await self._orig_send_bytes(uni_msg_json)

        return transcoded_recv_from_sdk, transcoded_send_to_sdk

    def print_context(self):
        print("TRANSCODER CONTEXT:")
        for defn_id, defn_msg in self.defn_ctx.items():
            print('*', f_uid_grid(defn_id), '\t', type(defn_msg).__name__)
