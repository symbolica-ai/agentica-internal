# fmt: off

from .vshared import *
from .vmethods import *

################################################################################

class _list(list):

    @forward
    def append(self, value, /) -> None: ...

    @forward
    def clear(self) -> None: ...

    @forward
    def copy(self) -> Self: ...

    @forward
    def count(self, value, /) -> int: ...

    @forward
    def extend(self, value, /) -> None: ...

    @forward
    def remove(self, value, /) -> None: ...

    @forward
    def reverse(self) -> None: ...

    ############################################################################

    @forward
    def index(self, value, start=ARG_DEFAULT, stop=ARG_DEFAULT) -> int: ...

    @forward
    def insert(self, index: int, value, /) -> None: ...

    @forward
    def pop(self, index: int = ARG_DEFAULT, /) -> Any: ...

    @forward
    def sort(self, *, key=None, reverse: bool = False) -> None: ...

    ############################################################################

    @forward
    def __add__(self, other: list, /) -> list: ...

    def __contains__(self, value: object, /) -> bool:        return v_contains(list, self, value)
    def __getitem__(self, index: index_t, /) -> object:      return v_getitem(list, self, index)
    def __setitem__(self, index: index_t, value, /) -> None: return v_setitem(list, self, index, value)
    def __delitem__(self, index: index_t, /) -> None:        return v_delitem(list, self, index)

    ############################################################################

    def __eq__(self, other, /) -> bool: return v_eq(list, self, other)
    def __ne__(self, other, /) -> bool: return v_ne(list, self, other)
    def __lt__(self, other, /) -> bool: return v_lt(list, self, other)
    def __le__(self, other, /) -> bool: return v_le(list, self, other)
    def __gt__(self, other, /) -> bool: return v_gt(list, self, other)
    def __ge__(self, other, /) -> bool: return v_ge(list, self, other)

    ############################################################################

    def __len__(self) -> int:                return v_len(list, self)
    def __iter__(self) -> Iterator[Any]:     return v_iter(list, self)
    def __reversed__(self) -> Iterator[Any]: return v_iter(list, self, rev=True)

    ############################################################################

    def __str__(self) -> Any:  return v_str(list, self)
    def __repr__(self) -> Any: return v_repr(list, self)

    ############################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(list, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(list, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(list, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(list, self)

    ############################################################################

    __hash__ = None
