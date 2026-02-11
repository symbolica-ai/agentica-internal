# ruff: noqa
# fmt: off

from msgspec import UNSET, EncodeError, Raw, Struct, UnsetType, json, msgpack  # noqa: F401

from ..data.all import *
from ..__ import *
from .__json import *
from .__msgpack import *

from .codec import EncoderP, DecoderP, CodecP

def seq_shape(seq: tuple['Msg', ...]) -> str:
    n = len(seq)
    return len_shape(n) if n > 4 else commas(m.shape for m in seq)

def len_shape(n: int) -> str:
    return f'..{n}'

commas = ', '.join
