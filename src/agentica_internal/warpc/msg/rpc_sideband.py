# fmt: off

from .__ import *
from .rpc import RPCMsg


__all__ = [
    'SidebandMsg',
    'ChannelMsg',
    'RemotePrintMsg',
    'FutureResultMsg'
]


################################################################################

if TYPE_CHECKING:
    from .term_result import ResultMsg
    from .resource_def import DefinitionMsg
    from .msg_aliases import SrcLocationMsg

################################################################################

class SidebandMsg(RPCMsg):
    """ABC for RPC events, that do not themselves require responses."""


################################################################################

class ChannelMsg(SidebandMsg, tag='chan'):
    """Message describing a result sent over the global channel."""

    LOG_TAGS = 'CHANNEL'

    data:   'ResultMsg | None'
    last:   bool
    defs:   'Tup[DefinitionMsg]' = ()
    origin: 'SrcLocationMsg' = None

    def __shape__(self) -> str:
        return self.data.shape

    @staticmethod
    def encode(enc: EncoderP, value: Result, last: bool, src_loc: 'SrcLocationMsg') -> 'ChannelMsg':
        enc_ctx = enc.enc_context()
        with enc_ctx:
            value_msg = ResultMsg.encode(value, enc)
        def_msgs = enc_ctx.enc_context_defs()
        return ChannelMsg(value_msg, last, def_msgs, src_loc)

    def decode(self, dec: DecoderP) -> Result | Closed:
        if self.data is None:
            assert self.last
            return CLOSED
        dec_ctx = dec.dec_context(self.defs)
        with dec_ctx:
            value = self.data.decode(dec)
        return value

    ############################################################################

    def get_result_msg(self) -> 'ResultMsg | None':
        return self.data


CHANNEL_CLOSED_MSG = ChannelMsg(None, True)


################################################################################

class RemotePrintMsg(SidebandMsg, tag='print'):
    """Message causing a print to happen when decoded locally."""

    text:    str
    origin: 'SrcLocationMsg' = None


################################################################################

class FutureResultMsg(SidebandMsg, tag='futureid'):
    """Deliver the result of a Future with a given ID (string or integer)."""

    fid:    'FutureID'
    result: 'ResultMsg'
    origin: 'SrcLocationMsg' = None

    ############################################################################

    def get_result_msg(self) -> 'ResultMsg | None':
        return self.result
