# fmt: off

from .vshared import *
from .vmethods import *

################################################################################

class _str(str):

    @forward
    def capitalize(self) -> str: ...

    @forward
    def casefold(self) -> str: ...

    @forward
    def center(self, width: int, fillchar: str = ..., /) -> str: ...

    @forward
    def count(self, sub: str, start: int = ..., end: int = ..., /) -> int: ...

    @forward
    def encode(self, encoding: str = ..., errors: str = ...) -> bytes: ...

    @forward
    def endswith(self, suffix: str | tuple[str, ...], start: int = ..., end: int = ..., /) -> bool: ...

    @forward
    def expandtabs(self, tabsize: int = 8) -> str: ...

    @forward
    def find(self, sub: str, start: int = ..., end: int = ..., /) -> int: ...

    @forward
    def format(self, *args: object, **kwargs: object) -> str: ...

    @forward
    def format_map(self, mapping, /) -> str: ...

    @forward
    def index(self, sub: str, start: int = ..., end: int = ..., /) -> int: ...

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
    def join(self, iterable: Iterable[str], /) -> str: ...

    @forward
    def ljust(self, width: int, fillchar: str = ..., /) -> str: ...

    @forward
    def lower(self) -> str: ...

    @forward
    def lstrip(self, chars: str = ..., /) -> str: ...

    @forward
    def partition(self, sep: str, /) -> tuple[str, str, str]: ...

    @forward
    def replace(self, old: str, new: str, /, count: int = ...) -> str: ...

    @forward
    def removeprefix(self, prefix: str, /) -> str: ...

    @forward
    def removesuffix(self, suffix: str, /) -> str: ...

    @forward
    def rfind(self, sub: str, start: int = ..., end: int = ..., /) -> int: ...

    @forward
    def rindex(self, sub: str, start: int = ..., end: int = ..., /) -> int: ...

    @forward
    def rjust(self, width: int, fillchar: str = ..., /) -> str: ...

    @forward
    def rpartition(self, sep: str, /) -> tuple[str, str, str]: ...

    @forward
    def rsplit(self, sep: str = ..., maxsplit: int = ...) -> list[str]: ...

    @forward
    def rstrip(self, chars: str = ..., /) -> str: ...

    @forward
    def split(self, sep: str = ..., maxsplit: int = ...) -> list[str]: ...

    @forward
    def splitlines(self, keepends: bool = False) -> list[str]: ...

    @forward
    def startswith(self, prefix: str | tuple[str, ...], start: int = ..., end: int = ...) -> bool: ...

    @forward
    def strip(self, chars: str = ..., /) -> str: ...

    @forward
    def swapcase(self) -> str: ...

    @forward
    def title(self) -> str: ...

    @forward
    def translate(self, table, /) -> str: ...

    @forward
    def upper(self) -> str: ...

    @forward
    def zfill(self, width: int, /) -> str: ...

    ############################################################################

    def __eq__(self, other, /) -> bool: return v_eq(str, self, other)
    def __ne__(self, other, /) -> bool: return v_ne(str, self, other)
    def __lt__(self, other, /) -> bool: return v_lt(str, self, other)
    def __le__(self, other, /) -> bool: return v_le(str, self, other)
    def __gt__(self, other, /) -> bool: return v_gt(str, self, other)
    def __ge__(self, other, /) -> bool: return v_ge(str, self, other)

    ############################################################################

    def __len__(self) -> int:                return v_len(str, self)
    def __iter__(self) -> Iterator[Any]:     return v_iter(str, self, oneshot=True)
    def __reversed__(self) -> Iterator[Any]: return v_iter(str, self, oneshot=True, rev=True)

    ############################################################################

    def __contains__(self, value, /) -> bool:        return v_contains(str, self, value)
    def __getitem__(self, index: index_t, /) -> str: return v_getitem(str, self, index)

    ############################################################################

    @forward
    def __add__(self, value, /) -> str: ...

    @forward
    def __mul__(self, value: int, /) -> str: ...

    @forward
    def __rmul__(self, value: int, /) -> str: ...

    @forward
    def __mod__(self, value: Any, /) -> str: ...

    ############################################################################

    def __str__(self) -> Any:  return v_str(str, self)
    def __repr__(self) -> Any: return v_repr(str, self)

    ############################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(str, self, name)
    def __setattr__(self, name: str, value, /) -> ...: return v_setattr(str, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(str, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(str, self)

    ############################################################################

    def __hash__(self) -> int: return v_hash(str, self)

    ############################################################################

    def __class_getitem__(cls, item): return v_class_getitem(object, cls, item)
