# fmt: off

from .vshared import *
from .vmethods import *

################################################################################

class _bytearray(bytearray):

    @forward
    def append(self, item: int, /) -> None: ...

    @forward
    def copy(self) -> bytearray: ...

    @forward
    def extend(self, iterable_of_ints: Iterable[int], /) -> None: ...

    @forward
    def insert(self, index: int, item: int, /) -> None: ...

    @forward
    def pop(self, index: int = -1, /) -> int: ...

    @forward
    def remove(self, value: int, /) -> None: ...

    @forward
    def replace(self, old, new, count: int = ..., /) -> Self: ...

    ############################################################################

    @forward
    def __alloc__(self) -> int: ...

    @forward
    def __buffer__(self, flags: int, /) -> memoryview: ...

    @forward
    def __release_buffer__(self, buffer: memoryview, /) -> None: ...

    ############################################################################

    def __eq__(self, other, /) -> bool: return v_eq(bytearray, self, other)
    def __ne__(self, other, /) -> bool: return v_ne(bytearray, self, other)
    def __lt__(self, other, /) -> bool: return v_lt(bytearray, self, other)
    def __le__(self, other, /) -> bool: return v_le(bytearray, self, other)
    def __gt__(self, other, /) -> bool: return v_gt(bytearray, self, other)
    def __ge__(self, other, /) -> bool: return v_ge(bytearray, self, other)

    ############################################################################

    def __len__(self) -> int:                return v_len(bytearray, self)
    def __iter__(self) -> Iterator[int]:     return v_iter(bytearray, self, oneshot=True)
    def __reversed__(self) -> Iterator[int]: return v_iter(bytearray, self, oneshot=True, rev=True)

    ############################################################################

    def __contains__(self, value: object, /) -> bool:             return v_contains(bytearray, self, value)
    def __getitem__(self, key: index_t, /) -> object:             return v_getitem(bytearray, self, key)
    def __setitem__(self, key: index_t, value: bytes, /) -> None: return v_setitem(bytearray, self, key, value)
    def __delitem__(self, key: index_t, /) -> None:               return v_delitem(bytearray, self, key)

    ############################################################################

    @forward
    def __add__(self, value, /) -> Self: ...

    @forward
    def __iadd__(self, value, /) -> Self: ...  # type: ignore[override]

    @forward
    def __mul__(self, value: int, /) -> Self: ...

    @forward
    def __rmul__(self, value: int, /) -> Self: ...

    @forward
    def __imul__(self, value: int, /) -> Self: ...

    @forward
    def __mod__(self, value: Any, /) -> Self: ...

    ############################################################################

    def __str__(self) -> Any:  return v_str(bytearray, self)
    def __repr__(self) -> Any: return v_repr(bytearray, self)

    ############################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(bytearray, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(bytearray, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(bytearray, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(bytearray, self)

    ############################################################################

    def __hash__(self) -> int: return v_hash(bytearray, self)
