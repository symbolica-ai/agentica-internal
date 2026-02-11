# fmt: off

import string

from .__ import *
from .base import Msg
from .term import *


__all__ = [
    'JsonMsg',
    'RawMsg',
    'MsgMsg',
    'FileMsg'
]


################################################################################

if TYPE_CHECKING:
    from pathlib import Path

################################################################################

class WrapperMsg(TermPassByValMsg):
    ...

    def decode(self, dec: DecoderP) -> 'TermT':
        return self.decode_wrapped()

    def decode_wrapped(self) -> Any: ...

    @classmethod
    def encode_wrapped(cls, value: Any) -> 'WrapperMsg': ...


################################################################################

class RawMsg(WrapperMsg, tag='raw'):
    """Describes a msgspec Raw object (which is like bytes but encapsulates another msg)."""

    type V = Raw

    raw: bytes

    def decode_wrapped(self) -> V:
        return Raw(self.raw)

    @classmethod
    def encode_wrapped(cls, term: V) -> 'RawMsg':
        assert type(term) in (Raw, bytes)
        return RawMsg(bytes(term))

    encode_atom = encode_wrapped

    def __shape__(self) -> str:
        return f'..{len(self.raw)}'


################################################################################

class MsgMsg(WrapperMsg, tag='msg'):
    """Describes a Msg instance itself."""

    type V = 'Msg'
    wrapped: 'Msg'

    def decode_wrapped(self) -> V:
        return self.wrapped

    @classmethod
    def encode_wrapped(cls, term: V) -> 'EscapedMsg':
        assert isinstance(term, Msg)
        return MsgMsg(term)

    encode_atom = encode_wrapped


################################################################################

class JsonMsg(WrapperMsg, tag='json'):
    """Message that describes a pure JSON-like value."""

    json: bytes

    def decode_wrapped(self) -> Any:
        return dec_json(self.json)

    @classmethod
    def encode_wrapped(cls, value: Any) -> 'JsonMsg':
        return JsonMsg(enc_json(value))

    def __shape__(self) -> str:
        return f'..{len(self.json)}'


################################################################################

class FileMsg(WrapperMsg):
    """Describes a file by-value."""

    name: str
    data: bytes

    def decode_wrapped(self) -> 'Path':
        from xxhash import xxh32_digest
        data = self.data
        name = ''.join(s for s in self.name if s in PATH_SAFE_CHARS)
        tmp_dir = flags.INLINE_FILE_DIRECTORY
        if not tmp_dir:
            raise RuntimeError("Warping of files not enabled in flags.")
        dig = xxh32_digest(data)
        tmp_file = tmp_dir / dig.hex() / name
        if tmp_file.is_file():
            return tmp_file
        tmp_file.parent.mkdir(parents=True, exist_ok=True)
        tmp_file.write_bytes(data)
        return tmp_file

    @classmethod
    def encode_wrapped(cls, path: 'Path') -> 'FileMsg':
        assert path.is_file()
        data = path.read_bytes()
        return FileMsg(path.name, data)

PATH_SAFE_CHARS = set(string.ascii_letters + string.digits + "._")
