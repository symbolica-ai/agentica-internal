# fmt: off

from asyncio import Future

from .__ import *
from .request_resource import ResourceRequest


__all__ = [
    'FutureRequest',
    'CancelFuture',
    'CompleteFuture',
]


################################################################################

if TYPE_CHECKING:
    from ..msg.all import FutureRequestMsg, CancelFutureMsg, CompleteFutureMsg

################################################################################

class FutureRequest(ResourceRequest):
    __slots__ = __match_args__ = 'future'

    @abstractmethod
    def encode(self, codec: 'EncoderP') -> 'FutureRequestMsg': ...


################################################################################

class CancelFuture(FutureRequest):
    __slots__ = __match_args__ = 'future',

    future: Future

    def __init__(self, future: Future):
        self.future = future

    def __execute__(self):
        self.future.cancel()

    def encode(self, enc) -> 'CancelFutureMsg':
        from ..msg.all import CancelFutureMsg
        return CancelFutureMsg(
            enc.enc_future(self.future)
        )

    def hook_key(self):
        return 'cancel_future'


################################################################################

class CompleteFuture(FutureRequest):
    __slots__ = __match_args__ = 'future', 'result'

    future: Future
    result: Result

    def __init__(self, future: Future, result: Result):
        self.future = future
        self.result = result

    def __execute__(self):
        result = self.result
        if result.is_ok:
            self.future.set_result(result.value)
        elif result.is_err:
            self.future.set_exception(result.error)
        else:
            pass

    def encode(self, enc) -> 'CompleteFutureMsg':
        from ..msg.all import CompleteFutureMsg, ResultMsg
        return CompleteFutureMsg(
            enc.enc_future(self.future),
            ResultMsg.encode(self.result, enc)
        )

    def hook_key(self):
        return 'complete_future'
