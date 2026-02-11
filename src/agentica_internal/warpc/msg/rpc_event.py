# fmt: off

from .__ import *
from .rpc import RPCMsg


__all__ = [
    'EventMsg',
    'FutureEventMsg',
    'FutureCanceledMsg',
    'FutureCompletedMsg',
]


################################################################################

if TYPE_CHECKING:
    from .term_result import ResultMsg
    from .resource_def import DefinitionMsg
    from .msg_aliases import SrcLocationMsg
    from ..request.request_future import FutureRequest, CompleteFuture, CancelFuture

################################################################################

class EventMsg(RPCMsg):
    """ABC for RPC events, that do not themselves require responses."""


################################################################################

class FutureEventMsg(EventMsg):
    """ABC for RPC event about futures."""

    future_id: FutureID

    @staticmethod
    def encode_event(enc: EncoderP, future_id: FutureID, result: Result) -> 'FutureEventMsg':
        from .term_result import ResultMsg
        if result.is_completed:
            enc_ctx = enc.enc_context()
            with enc_ctx:
                result_msg = ResultMsg.encode(result, enc)
            defs = enc_ctx.enc_context_defs()
            return FutureCompletedMsg(future_id, result_msg, defs)
        elif result.is_canceled:
            return FutureCanceledMsg(future_id)
        else:
            raise E.WarpEncodingError("future result still pending")

    def decode(self, dec: DecoderP) -> 'FutureRequest':
        ...

################################################################################

class FutureCanceledMsg(FutureEventMsg, tag='future_canceled'):
    """Deliver the result of a Future with a given ID (string or integer)."""

    future_id: FutureID
    origin:   'SrcLocationMsg' = None

    def decode(self, dec) -> 'CancelFuture':
        from ..request.request_future import CancelFuture
        return CancelFuture(
            dec.future_from_id(self.future_id)
        )

################################################################################

class FutureCompletedMsg(FutureEventMsg, tag='future_completed'):
    """Deliver the result of a Future with a given ID (string or integer)."""

    future_id: FutureID
    result:   'ResultMsg'
    defs:     'Tup[DefinitionMsg]' = ()
    origin:   'SrcLocationMsg' = None

    def decode(self, dec) -> 'CompleteFuture':
        from ..request.request_future import CompleteFuture
        with dec.dec_context(self.defs):
            return CompleteFuture(
                dec.future_from_id(self.future_id),
                self.result.decode(dec),
            )

    ############################################################################

    def get_result_msg(self) -> 'ResultMsg | None':
        return self.result

    def get_definition_msgs(self) -> 'Tup[DefinitionMsg] | None':
        return self.defs
