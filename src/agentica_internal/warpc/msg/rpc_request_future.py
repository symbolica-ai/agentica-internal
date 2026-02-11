# fmt: off

from .__ import *
from .rpc_request_resource import ResourceRequestMsg


__all__ = [
    'FutureRequestMsg',
    'CancelFutureMsg',
    'CompleteFutureMsg'
]


################################################################################

if TYPE_CHECKING:
    from ..request.request_future import *
    from .msg_aliases import FutureMsg
    from .term_result import ResultMsg

################################################################################

class FutureRequestMsg(ResourceRequestMsg):

    def decode(self, dec: DecoderP) -> 'FutureRequest': ...

################################################################################

class CancelFutureMsg(FutureRequestMsg, tag='cancel_future'):

    future: 'FutureMsg'

    def decode(self, dec) -> 'CancelFuture':
        from ..request.request_future import CancelFuture
        return CancelFuture(
            dec.dec_future(self.future)
        )

################################################################################

class CompleteFutureMsg(FutureRequestMsg, tag='complete_future'):

    future: 'FutureMsg'
    result: 'ResultMsg'

    def decode(self, dec) -> 'CompleteFuture':
        from ..request.request_future import CompleteFuture
        return CompleteFuture(
            dec.dec_future(self.future),
            self.result.decode(dec),
        )

    ############################################################################

    def get_result_msg(self) -> 'ResultMsg | None':
        return self.result
