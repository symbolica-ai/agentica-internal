# fmt: off

from .__ import *
from .term import TermPassByValMsg

__all__ = [
    'ResultMsg',
]


################################################################################

if TYPE_CHECKING:
    from .term import TermMsg
    from .term_exception import ExceptionMsg

################################################################################

class ResultMsg(TermPassByValMsg):
    """
    ABC for messages matching `Result`.
    """
    type V = Result

    done:   bool                 = True
    value: 'TermMsg | None'      = None
    error: 'ExceptionMsg | None' = None

    ############################################################################

    @property
    def is_ok(self) -> bool:
        return self.done and self.error is None

    @property
    def is_err(self) -> bool:
        return self.done and self.error is not None

    @property
    def is_unavailable(self) -> bool:
        return not self.done

    ############################################################################

    def decode(self, dec: DecoderP, /) -> Result:
        error = value = None
        if msg := self.error:
            error = dec.dec_exception(msg)
        elif msg := self.value:
            value = dec.dec_any(msg)
        return Result.from_triple(self.done, value, error)

    ############################################################################

    @staticmethod
    def encode(res: Result, enc: EncoderP, /) -> 'ResultMsg':
        done, value, error = res
        error_msg = value_msg = None
        if error is not None:
            error_msg = enc.enc_exception(error)
        elif value is not None:
            value_msg = enc.enc_any(value)
        return ResultMsg(done=done, value=value_msg, error=error_msg)

    @staticmethod
    def encode_as(res: Result, enc: EncoderP, fmt: DecodeFmt, /) -> 'ResultMsg':
        if fmt == 'full' or not res.done:
            return ResultMsg.encode(res, enc)
        done, value, error = res
        if error is not None:
            return ResultMsg(error=enc.enc_exception(error))
        match fmt:
            case 'raw':    return ResultMsg.encode_raw(value, enc)
            case 'json':   return ResultMsg.encode_json(value)
            case 'type':   return ResultMsg.encode_json(type(value))
            case 'schema': return ResultMsg.encode_json(get_json_schema(value))
            case _:        raise E.WarpEncodingError(f'unknown result format {fmt}')

    @staticmethod
    def encode_value(value: TermT, enc: EncoderP, /) -> 'ResultMsg':
        return ResultMsg(value=enc.enc_any(value))

    @staticmethod
    def encode_error(error: BaseException, enc: EncoderP, /) -> 'ResultMsg':
        return ResultMsg(error=enc.enc_exception(error))

    @staticmethod
    def encode_raw(value: TermT, enc: EncoderP, /) -> 'ResultMsg':
        from .term_wrapper import RawMsg
        data = enc.enc_any(value).to_msgpack()
        value_msg = RawMsg(data)
        return ResultMsg(value=value_msg)

    @staticmethod
    def encode_json(value: TermT, /) -> 'ResultMsg':
        from .term_wrapper import JsonMsg
        value_msg = JsonMsg(enc_json(value))
        return ResultMsg(value=value_msg)
