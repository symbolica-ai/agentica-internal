# fmt: off

from .vshared import *
from .vmethods import *

################################################################################

class _bytes(bytes):

    @forward
    def capitalize(self) -> bytes: ...

    @forward
    def casefold(self) -> bytes: ...

    @forward
    def center(self, width: int, fillchar: bytes = ..., /) -> bytes: ...

    @forward
    def count(self, sub: bytes, start: int = ..., end: int = ..., /) -> int: ...

    @forward
    def decode(self, encoding: str = ..., errors: str = ...) -> str: ...

    @forward
    def endswith(self, suffix: bytes | tuple[str, ...], start: int = ..., end: int = ..., /) -> bool: ...

    @forward
    def expandtabs(self, tabsize: int = 8) -> bytes: ...

    @forward
    def find(self, sub: bytes, start: int = ..., end: int = ..., /) -> int: ...

    @forward
    def hex(self, sep: str | bytes = ..., bytes_per_sep: int = 1) -> str: ...

    @forward
    def index(self, sub: bytes, start: int = ..., end: int = ..., /) -> int: ...

    @forward
    def isalnum(self) -> bool: ...

    @forward
    def isalpha(self) -> bool: ...

    @forward
    def isascii(self) -> bool: ...

    @forward
    def isdecimal(self) -> bool: ...

    @forward
    def isdigit(self) -> bool: ...

    @forward
    def isidentifier(self) -> bool: ...

    @forward
    def islower(self) -> bool: ...

    @forward
    def isnumeric(self) -> bool: ...

    @forward
    def isprintable(self) -> bool: ...

    @forward
    def isspace(self) -> bool: ...

    @forward
    def istitle(self) -> bool: ...

    @forward
    def isupper(self) -> bool: ...

    @forward
    def join(self, iterable: Iterable[bytes], /) -> bytes: ...

    @forward
    def ljust(self, width: int, fillchar: bytes = ..., /) -> bytes: ...

    @forward
    def lower(self) -> bytes: ...

    @forward
    def lstrip(self, bytes: bytes = ..., /) -> bytes: ...

    @forward
    def partition(self, sep: bytes, /) -> tuple[str, str, str]: ...

    @forward
    def replace(self, old: bytes, new: bytes, /, count: int = ...) -> bytes: ...

    @forward
    def removeprefix(self, prefix: bytes, /) -> bytes: ...

    @forward
    def removesuffix(self, suffix: bytes, /) -> bytes: ...

    @forward
    def rfind(self, sub: bytes, start: int = ..., end: int = ..., /) -> int: ...

    @forward
    def rindex(self, sub: bytes, start: int = ..., end: int = ..., /) -> int: ...

    @forward
    def rjust(self, width: int, fillchar: bytes = ..., /) -> bytes: ...

    @forward
    def rpartition(self, sep: bytes, /) -> tuple[str, str, str]: ...

    @forward
    def rsplit(self, sep: bytes = ..., maxsplit: int = ...) -> list[str]: ...

    @forward
    def rstrip(self, bytes: bytes = ..., /) -> bytes: ...

    @forward
    def split(self, sep: bytes = ..., maxsplit: int = ...) -> list[str]: ...

    @forward
    def splitlines(self, keepends: bool = False) -> list[str]: ...

    @forward
    def startswith(self, prefix: bytes | tuple[str, ...], start: int = ..., end: int = ...) -> bool: ...

    @forward
    def strip(self, bytes: bytes = ..., /) -> bytes: ...

    @forward
    def swapcase(self) -> bytes: ...

    @forward
    def title(self) -> bytes: ...

    @forward
    def translate(self, table, /) -> bytes: ...

    @forward
    def upper(self) -> bytes: ...

    @forward
    def zfill(self, width: int, /) -> bytes: ...

    ############################################################################

    @classmethod
    def fromhex(cls, string: str, /) -> Self: ...

    @staticmethod
    def maketrans(frm, to, /) -> bytes: ...

    ############################################################################

    def __eq__(self, other, /) -> bool: return v_eq(bytes, self, other)
    def __ne__(self, other, /) -> bool: return v_ne(bytes, self, other)
    def __lt__(self, other, /) -> bool: return v_lt(bytes, self, other)
    def __le__(self, other, /) -> bool: return v_le(bytes, self, other)
    def __gt__(self, other, /) -> bool: return v_gt(bytes, self, other)
    def __ge__(self, other, /) -> bool: return v_ge(bytes, self, other)

    ############################################################################

    def __len__(self) -> int:                return v_len(bytes, self)
    def __iter__(self) -> Iterator[Any]:     return v_iter(bytes, self)
    def __reversed__(self) -> Iterator[Any]: return v_iter(bytes, self, rev=True)

    ############################################################################

    def __contains__(self, value: object, /) -> bool: return v_contains(bytes, self, value)
    def __getitem__(self, key: index_t, /) -> Self:   return v_getitem(bytes, self, key)

    ############################################################################

    @forward
    def __add__(self, value, /) -> bytes: ...

    @forward
    def __mul__(self, value: int, /) -> bytes: ...

    @forward
    def __rmul__(self, value: int, /) -> bytes: ...

    @forward
    def __mod__(self, value: Any, /) -> bytes: ...

    ############################################################################

    def __str__(self) -> Any:     return v_str(bytes, self)
    def __repr__(self) -> Any:    return v_repr(bytes, self)

    @forward
    def __bytes__(self) -> bytes: ...

    ############################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(bytes, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(bytes, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(bytes, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(bytes, self)

    ############################################################################

    def __hash__(self) -> int: return v_hash(bytes, self)
