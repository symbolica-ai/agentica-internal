# fmt: off

from .__ import *
from .rpc import RPCMsg


__all__ = [
    'FramedMsg',
    'FramedRequestMsg',
    'FramedResponseMsg',
]

################################################################################

if TYPE_CHECKING:
    from ..request.base import Request
    from .resource_def import DefinitionMsg
    from .rpc_request import RequestMsg
    from .term_result import ResultMsg
    from .msg_aliases import SrcLocationMsg

################################################################################

class FramedMsg(RPCMsg):
    """ABC for RPC messages that are associated with frames."""

    if TYPE_CHECKING:
        mid:   MessageID
        fid:   FrameID
        defs: 'Tup[DefinitionMsg]'

    @property
    def thread_name(self) -> str:
        mid = self.mid
        fid = self.fid
        fmt = self.shape
        if mid == -1:
            return fmt
        fmt = f'{mid}:{fmt}'
        if fid == 0:
            return fmt
        return f'{fid}:{fmt}'


################################################################################

class FramedRequestMsg(FramedMsg, tag='req?'):
    """
    Message for all requests associated with a frame.

    Slots:
    * `mid`: the globally unique `MessageID` of this request
    * `fid`: the locally unique `FrameID` of the frame associated with the request
    * `data`: the `RequestMsg` that contains the content of the request
    * `fmt`: the format to encode the response in, one of `'full', 'json', 'schema'
    * `defs`: any auxiliary resource definitions needed to decode the request
    * `async_mode`: if 'coro' or 'future', creates a task to execute the request
    """

    mid:       MessageID
    fid:       FrameID
    request:  'RequestMsg'
    fmt:      'EncodeFmt' = 'full'
    defs:     'Tup[DefinitionMsg]' = ()

    async_mode: AsyncMode = None
    origin:    'SrcLocationMsg' = None

    @property
    def is_async(self) -> bool:
        return self.async_mode in ('coro', 'future') or self.request.is_async

    # --------------------------------------------------------------------------

    def __shape__(self) -> str:
        return f_id(self.mid) + ', ' + self.request.shape

    def __debug_info_str__(self) -> str:
        return f'mid={f_id(self.mid)}, data={self.request.TAG}'

    @property
    def thread_name(self) -> str:
        return f'{self.msg_tag}#{f_id(self.mid)}:{self.request.msg_tag}'

    # --------------------------------------------------------------------------

    def decode_request(self, dec: DecoderP) -> 'Request':
        dec_ctx = dec.dec_context(self.defs)
        with dec_ctx:
            request = self.request.decode(dec)
        if self.async_mode:
            return request.set_async_mode(self.async_mode)
        return request

    @staticmethod
    def encode_request(enc: EncoderP, mid: MessageID, fid: FrameID, request: 'Request',
                       src_loc: 'SrcLocationMsg' = None) -> 'FramedRequestMsg':
        enc_ctx = enc.enc_context()
        with enc_ctx:
            request_msg = request.encode(enc)
        defs = enc_ctx.enc_context_defs()
        async_mode = getattr(request, 'async_mode', None)
        return FramedRequestMsg(
            mid=mid, fid=fid,
            request=request_msg,
            defs=defs,
            async_mode=async_mode,
            origin=src_loc
        )

    def encode_response(self, enc: EncoderP, result: Result) -> 'FramedResponseMsg':
        from .term_result import ResultMsg
        enc_ctx = enc.enc_context()
        with enc_ctx:
            result_msg = ResultMsg.encode_as(result, enc, self.fmt)
        def_msgs = enc_ctx.enc_context_defs()
        return FramedResponseMsg(mid=self.mid, fid=self.fid, result=result_msg, defs=def_msgs)


################################################################################

class FramedResponseMsg(FramedMsg, tag='reply!'):
    """
    A response to a `FramedRequestMsg`.

    Slots:
    * `mid`: the globally unique `MessageID` of this request
    * `fid`: the locally unique `FrameID` of the frame associated with the request
    * `data`: the `ResultMsg` that contains the content of the reply
    * `defs`: any auxiliary resource definitions needed to decode the reply
    """

    fid:     FrameID
    mid:     MessageID
    result: 'ResultMsg'
    defs:   'Tup[DefinitionMsg]' = ()

    origin: 'SrcLocationMsg' = None

    def __shape__(self) -> str:
        return f_id(self.mid) + ', ' + self.result.shape

    def __debug_info_str__(self) -> str:
        return f'mid={f_id(self.mid)}, data={self.result.TAG}'

    def decode_response(self, dec: DecoderP) -> 'Result':
        dec_ctx = dec.dec_context(self.defs)
        with dec_ctx:
            result = self.result.decode(dec)
        return result

    ############################################################################

    def get_result_msg(self) -> 'ResultMsg | None':
        return self.result
