# fmt: off

from .vshared import *
from .vmethods import *

################################################################################

class _tuple(tuple):

    @forward
    def count(self, value, /) -> int: ...

    @forward
    def index(self, value, start: int = ..., stop: int = ...) -> int: ...

    ############################################################################

    @forward
    def __add__(self, other: tuple, /) -> tuple: ...

    ############################################################################

    def __len__(self) -> int:                return v_len(tuple, self)
    def __iter__(self) -> Iterator[Any]:     return v_iter(tuple, self)
    def __reversed__(self) -> Iterator[Any]: return v_iter(tuple, self, rev=True)

    ############################################################################

    def __contains__(self, value, /) -> bool: return v_contains(tuple, self, value)
    def __getitem__(self, index: index_t, /): return v_getitem(tuple, self, index)

    ############################################################################

    def __eq__(self, other, /) -> bool: return v_eq(tuple, self, other)
    def __ne__(self, other, /) -> bool: return v_ne(tuple, self, other)
    def __lt__(self, other, /) -> bool: return v_lt(tuple, self, other)
    def __le__(self, other, /) -> bool: return v_le(tuple, self, other)
    def __gt__(self, other, /) -> bool: return v_gt(tuple, self, other)
    def __ge__(self, other, /) -> bool: return v_ge(tuple, self, other)

    ############################################################################

    def __str__(self) -> Any:  return v_str(tuple, self)
    def __repr__(self) -> Any: return v_repr(tuple, self)

    ############################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(tuple, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(tuple, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(tuple, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(tuple, self)

    ############################################################################

    def __hash__(self) -> int: return v_hash(tuple, self)

    ############################################################################

    def __class_getitem__(cls, item): return v_class_getitem(object, cls, item)
