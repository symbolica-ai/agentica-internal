# fmt: off

from .__ import *
from .msg_aliases import FunctionMsg
from .term import *


__all__ = [
    'SliceMsg',
    'RangeMsg',
    'ZipMsg',
    'MapMsg',
    'FilterMsg',
    'EnumerateMsg'
]


################################################################################

class RangeMsg(TermPassByValMsg, tag='range'):

    type V = range

    start: int
    stop:  int
    step:  int

    def decode(self, dec: DecoderP) -> range:
        return range(self.start, self.stop, self.step)

    @classmethod
    def encode_compound(cls, term: range, enc: EncoderP) -> 'RangeMsg':
        assert type(term) is range
        return RangeMsg(term.start, term.stop, term.step)

################################################################################

class SliceMsg(TermPassByValMsg):

    type V = slice

    start: 'TermMsg'
    stop:  'TermMsg'
    step:  'TermMsg'

    def decode(self, dec: DecoderP) -> slice:
        dec_any = dec.dec_any
        return slice(
            dec_any(self.start),
            dec_any(self.stop),
            dec_any(self.step)
        )

    @classmethod
    def encode_compound(cls, term: slice, enc: EncoderP) -> 'SliceMsg':
        assert type(term) is slice
        enc_any = enc.enc_any
        return SliceMsg(
            enc_any(term.start),
            enc_any(term.stop),
            enc_any(term.step)
        )

################################################################################

class ZipMsg(TermPassByValMsg, tag='zip'):

    type V = zip

    iters:  'Tup[TermMsg]'
    strict: bool = False

    def decode(self, dec: DecoderP) -> zip:
        iters = dec.dec_sequence(self.iters)
        return zip(*iters, strict=self.strict)

    @classmethod
    def encode_compound(cls, term: zip, enc: EncoderP) -> 'ZipMsg':
        assert type(term) is zip
        try:
            _, iters, *state = term.__reduce__()
        except BaseException as exc:
            raise E.WarpEncodingError(f"Bad zip reduction: {exc}")
        iters = enc.enc_sequence(iters)
        strict = True in state
        return ZipMsg(iters, strict)


################################################################################

class MapMsg(TermPassByValMsg, tag='map'):

    type V = map

    func:   'FunctionMsg'
    iters:  'Tup[TermMsg]'
    strict:  bool = False

    def decode(self, dec: DecoderP) -> map:
        func = dec.dec_function(self.func)
        iters = dec.dec_sequence(self.iters)
        if self.strict:  # >= 3.14
            try: return map(func, *iters, strict=True)
            except: ...
        return map(func, *iters)

    @classmethod
    def encode_compound(cls, term: map, enc: EncoderP) -> 'MapMsg':
        assert type(term) is map
        try:
            _, (func, *iters), *state = term.__reduce__()
            assert callable(func)
        except BaseException as exc:
            raise E.WarpEncodingError(f"Bad map reduction: {exc}")
        func_msg = enc.enc_function(func)
        iters_msg = enc.enc_sequence(iters)
        strict = True in state
        return MapMsg(func_msg, iters_msg, strict)


################################################################################

class FilterMsg(TermPassByValMsg, tag='filter'):

    type V = filter

    func: 'FunctionMsg'
    iter: 'TermMsg'

    def decode(self, dec: DecoderP) -> filter:
        func = dec.dec_function(self.func)
        it = dec.dec_any(self.iter)
        return filter(func, it)

    @classmethod
    def encode_compound(cls, term: filter, enc: EncoderP) -> 'FilterMsg':
        assert type(term) is filter
        try:
            _, (func, it) = term.__reduce__()
            assert callable(func)
        except BaseException as exc:
            raise E.WarpEncodingError(f"Bad filter reduction: {exc}")
        func_msg = enc.enc_function(func)
        iter_msg = enc.enc_any(it)
        return FilterMsg(func_msg, iter_msg)

################################################################################

class EnumerateMsg(TermPassByValMsg, tag='enumerate'):

    type V = enumerate

    iter: 'TermMsg'
    start: int = 0

    def decode(self, dec: DecoderP) -> enumerate:
        it = dec.dec_any(self.iter)
        assert hasattr(it, '__next__')
        return enumerate(it, self.start)

    @classmethod
    def encode_compound(cls, term: enumerate, enc: EncoderP) -> 'EnumerateMsg':
        assert type(term) is enumerate
        try:
            _, (it, start) = term.__reduce__()
            assert type(start) is int
        except BaseException as exc:
            raise E.WarpEncodingError(f"Bad enumerate reduction: {exc}")
        iter_msg = enc.enc_any(it)
        return EnumerateMsg(iter_msg, start)
