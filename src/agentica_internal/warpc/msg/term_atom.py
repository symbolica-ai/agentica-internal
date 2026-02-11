# fmt: off

from decimal import Decimal

from .__ import *
from .term import *

__all__ = [
    'AtomMsg',
    'NumberMsg',
    'ComplexMsg',
    'DecimalMsg',
    'StrLikeMsg',
    'StrMsg',
    'BytesMsg',
    'SingletonMsg',
    'NoneMsg',
    'NotImplMsg',
    'EllipsisMsg',
    'ClosedMsg',
]


################################################################################

class ForwardRefTypeMsg(TermPassByValMsg, tag='fwdref'):
    type V = str
    v: str

    def decode(self, dec: DecoderP) -> V:
        from ...cpython.classes.anno import TForward
        return TForward(self.v)

    @classmethod
    def encode_atom(cls, term: V) -> 'ForwardRefTypeMsg':
        return cls(v=term)


################################################################################

class AtomMsg(TermPassByValMsg):
    """ABC for messages describing immutable, atomic values."""

    __debug_fmt_slots__ = False

    type V = AtomT

    def decode(self, fn: DecoderP) -> V:
        return self.decode_atom()

    def decode_atom(self) -> V: ...

    @classmethod
    def encode_atom(cls, term: V) -> 'AtomMsg':
        if isinstance(term, (int, bool, float)):
            return NumberMsg.encode_atom(term)
        if isinstance(term, str):
            return StrMsg.encode_atom(term)
        if isinstance(term, bytes):
            return BytesMsg.encode_atom(term)
        if term is None:
            return NoneMsg.MSG
        if term is Ellipsis:
            return EllipsisMsg.MSG
        if term is NotImplemented:
            return NotImplMsg.MSG
        raise E.WarpEncodingError(f"not an atom: {term}")


################################################################################

class NumberMsg(AtomMsg, tag='num'):

    type V = NumberT
    v:       NumberT | str  # str is for bigints

    def __debug_info_str__(self) -> str:
        return str(self.v)

    @property
    def shape(self) -> str:
        val = self.v
        cls = type(val)
        if cls is int:
            return str(val) if -9 <= val <= 9 else 'int'
        if cls is bool:
            return 'true' if val else 'false'
        return 'float'

    def decode_atom(self) -> V:
        v = self.v
        return int(v) if type(v) is str else v

    @classmethod
    def encode_atom(cls, term: V) -> 'NumberMsg':
        if type(term) is int and abs(term) > (2**63):
            return NumberMsg(str(term))
        return NumberMsg(term)


################################################################################

class ComplexMsg(AtomMsg, tag='complex'):

    type V = complex

    re: float
    im: float

    def decode_atom(self) -> V:
        return complex(self.re, self.im)

    @classmethod
    def encode_atom(cls, term: V) -> 'ComplexMsg':
        return cls(term.real, term.imag)


################################################################################

class DecimalMsg(AtomMsg, tag='decimal'):

    type V = Decimal

    digits: str

    def decode_atom(self) -> V:
        return Decimal(self.digits)

    @classmethod
    def encode_atom(cls, term: V) -> 'AtomMsg':
        return DecimalMsg(str(term))


################################################################################

class StrLikeMsg(AtomMsg):
    """ABC for messages describing `str` or `bytes` values."""

    type V = StrLikeT

    v: StrLikeT

    def __debug_info_str__(self) -> str:
        return self.shape

    @property
    def shape(self) -> str:
        s = type(self).TAG
        v = self.v
        if len(v) <= 5:
            return repr(v)
        else:
            return s

    def decode_atom(self) -> V:
        return self.v

    @classmethod
    def encode_atom(cls, term: V) -> 'StrLikeMsg':
        return cls(term)


################################################################################

class StrMsg(StrLikeMsg, tag='str'):

    type V = str
    v: str


class BytesMsg(StrLikeMsg, tag='bytes'):
    type V = bytes
    v: bytes


################################################################################

class SingletonMsg(AtomMsg):
    """ABC for messages representing singleton values like `None`. They have
    no content, since there is only one possible value they describe."""

    type V = SingletonT

    VAL: ClassVar[SingletonT]
    MSG: ClassVar['SingletonMsg']

    def decode_atom(self) -> V:
        return type(self).VAL

    @classmethod
    def encode_constant(cls):
        return cls.MSG


################################################################################

class NoneMsg(SingletonMsg, tag='none'):
    type V = S.NoneT

    VAL = None


class NotImplMsg(SingletonMsg, tag='notimpl'):
    type V = S.NotImplT

    VAL = NotImplemented


class EllipsisMsg(SingletonMsg, tag='ellip'):
    type V = S.EllipT

    VAL = Ellipsis


class ClosedMsg(SingletonMsg, tag='closed'):
    type V = CLOSED

    VAL = CLOSED


################################################################################

NoneMsg.MSG       = NoneMsg()
NotImplMsg.MSG    = NotImplMsg()
EllipsisMsg.MSG   = EllipsisMsg()
ClosedMsg.MSG     = ClosedMsg()
