# fmt: off

from .__ import *
from .term import *


__all__ = [
    'ContainerMsg',
    'MappingMsg',
    'DictMsg',
    'SequenceMsg',
    'ListMsg',
    'TupleMsg',
    'SetMsg',
    'FrozenSetMsg'
]


################################################################################

class ContainerMsg(TermPassByValMsg):
    """ABC for messages describing container values: lists, tuples, dicts, etc."""

    CLS: ClassVar[type[ContainerT]]

    type V = ContainerT

    def length(self) -> int: ...


################################################################################

class MappingMsg(ContainerMsg):
    """Message describing mapping-like container values."""

    type V = MappingT

    ks: 'Tup[TermMsg]'
    vs: 'Tup[TermMsg]'

    def length(self) -> int:
        return len(self.ks)

    def __shape__(self) -> str:
        n = self.length()
        if n > 4:
            return len_shape(n)
        return ','.join(f'{k.shape}:{v.shape}' for k, v in zip(self.ks, self.vs))

    def decode(self, dec: DecoderP) -> V:
        dec_seq = dec.dec_sequence
        ks = dec_seq(self.ks)
        vs = dec_seq(self.vs)
        return self.CLS(zip(ks, vs))

    @classmethod
    def encode_compound(cls, term: V, enc: EncoderP) -> 'MappingMsg':
        enc_seq = enc.enc_sequence
        ks = enc_seq(term.keys())
        vs = enc_seq(term.values())
        return cls(ks, vs)


################################################################################

class DictMsg(MappingMsg, tag='dict'):

    CLS: ClassVar[type[dict]] = dict

    type V = dict | S.MapProxyT



################################################################################

class SequenceMsg(ContainerMsg):
    """Message describing sequence-like container values."""

    type V = SequenceT

    vs: 'Tup[TermMsg]'

    def __shape__(self) -> str:
        return seq_shape(self.vs)

    def length(self) -> int:
        return len(self.vs)

    def decode(self, dec: DecoderP) -> SequenceT:
        vs = dec.dec_sequence(self.vs)
        return self.CLS(vs)

    @classmethod
    def encode_compound(cls, term: V, enc: EncoderP) -> 'SequenceMsg':
        vs = enc.enc_sequence(term)
        return cls(vs)


################################################################################

class TupleMsg(SequenceMsg, tag='tup'):
    CLS: ClassVar[type[tuple]] = tuple
    type V = tuple


class ListMsg(SequenceMsg, tag='list'):
    CLS: ClassVar[type[list]] = list
    type V = list


################################################################################

class SetlikeMsg(SequenceMsg):

    @classmethod
    def encode_compound(cls, term: SequenceT, enc: EncoderP) -> 'SequenceMsg':
        vs = list(enc.enc_sequence(term))
        # ensure deterministic order, important for testing
        vs.sort(key=SetlikeMsg.to_msgpack)  # type: ignore
        return cls(tuple(vs))


class SetMsg(SetlikeMsg, tag='set'):
    CLS: ClassVar[type[set]] = set
    type V = set

class FrozenSetMsg(SetlikeMsg, tag='frozenset'):
    CLS: ClassVar[type[frozenset]] = frozenset
    type V = frozenset
