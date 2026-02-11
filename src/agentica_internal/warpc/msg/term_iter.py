# fmt: off

from typing import Union

from ...cpython.iters import SEQ_ITER_TYPES, STR_ITER_TYPES, REV_ITER_TYPES, CallIterType, RangeIterType

from .__ import *
from .term import *
from .msg_aliases import *

__all__ = [
    'ByValueIterMsg',
    'DataIterMsg',
    'CallIterMsg',
    'RangeIterMsg',
]


################################################################################

class ByValueIterMsg(TermPassByValMsg):
    pass

################################################################################

DATA_ITER_TYPES = SEQ_ITER_TYPES + STR_ITER_TYPES

type DataIterT = Union[*DATA_ITER_TYPES]

class DataIterMsg(ByValueIterMsg, tag='data_iter'):

    type V = DataIterT

    seq: 'TermMsg'  # this must be a sequence
    pos:  int = 0
    rev:  bool = False

    def decode(self, dec: DecoderP) -> DataIterT:
        seq = dec.dec_any(self.seq)
        if type(seq) not in (str, bytes, bytearray, tuple, list):
            assert hasattr(type(seq), '__getitem__')
            seq = sequence(seq)
        it = iter(reversed(seq)) if self.rev else iter(seq)
        if self.pos: it.__setstate__(self.pos)
        return it

    # this is NOT encode_compound because we do not
    # want to willy-nilly realize potentially expensive TupleIterType etc.
    # rather the encoder decides whether to do this
    @classmethod
    def encode_iter(cls, term: DataIterT, enc: EncoderP) -> 'DataIterMsg':
        _cls = type(term)
        try:
            assert _cls in DATA_ITER_TYPES, f"{_cls} not a data iter type"
            reduced = term.__reduce__()
            n = len(reduced)
            if n == 2:
                pos = None
                _, (seq,) = reduced
            else:
                _, (seq,), pos = reduced
        except Exception as exc:
            raise E.WarpEncodingError(f"Bad DateIterType reduction: {exc}")
        rev = _cls in REV_ITER_TYPES
        pos = pos if type(pos) is int else None
        seq_msg = enc.enc_any(seq)
        return DataIterMsg(seq_msg, pos, rev)

# this wrapper ensures that iter(my_list) does not recursively VRR on __iter__
class sequence:
    __slot__ = 'seq'

    def __init__(self, seq):
        self.seq = seq

    def __getitem__(self, pos):
        return self.seq[pos]

    def __len__(self):
        return len(self.seq)

################################################################################

class CallIterMsg(ByValueIterMsg, tag='call_iter'):

    type V = CallIterType

    func:  'FunctionMsg'
    stop:  'TermMsg'

    def decode(self, dec: DecoderP) -> CallIterType:
        func = dec.dec_function(self.func)
        stop = dec.dec_any(self.stop)
        assert callable(func)
        return iter(func, stop)

    @classmethod
    def encode_compound(cls, term: CallIterType, enc: EncoderP) -> 'CallIterMsg':
        assert type(term) is CallIterType
        try:
            _, (func, stop) = term.__reduce__()
            assert callable(func)
        except BaseException as exc:
            raise E.WarpEncodingError("Bad CallIterType reduction")
        func_msg = enc.enc_function(func)
        stop_msg = enc.enc_any(stop)
        return CallIterMsg(func_msg, stop_msg)

################################################################################

class RangeIterMsg(ByValueIterMsg, tag='range_iter'):

    type V = RangeIterType

    start: int
    stop:  int
    step:  int

    def decode(self, dec: DecoderP) -> RangeIterType:
        return iter(range(self.start, self.stop, self.step))

    @classmethod
    def encode_compound(cls, term: RangeIterType, enc: EncoderP) -> 'RangeIterMsg':
        assert type(term) is RangeIterType
        try:
            _, (r,), _ = term.__reduce__()
            assert type(r) is range
        except BaseException as exc:
            raise E.WarpEncodingError("Bad RangeIterType reduction")
        return RangeIterMsg(r.start, r.stop, r.step)
