# fmt: off

from typing import AbstractSet

from .vshared import *
from .vmethods import *

################################################################################

class _frozenset(frozenset):

    @forward
    def copy(self) -> Self: ...

    @forward
    def difference(self, *s: Iterable[Any]) -> Self: ...

    @forward
    def intersection(self, *s: Iterable[Any]) -> Self: ...

    @forward
    def isdisjoint(self, s: Iterable[Any], /) -> bool: ...

    @forward
    def issubset(self, s: Iterable[Any], /) -> bool: ...

    @forward
    def issuperset(self, s: Iterable[Any], /) -> bool: ...

    @forward
    def symmetric_difference(self, s: Iterable[Any], /) -> Self: ...

    @forward
    def union(self, *s: Iterable[Any]) -> Self: ...

    ############################################################################

    @forward
    def __and__(self, value: AbstractSet[Any], /) -> Self: ...

    @forward
    def __or__(self, value: AbstractSet[Any], /) -> Self: ...

    @forward
    def __sub__(self, value: AbstractSet[Any], /) -> Self: ...

    @forward
    def __xor__(self, value: AbstractSet[Any], /) -> Self: ...

    ############################################################################

    def __eq__(self, other: object, /) -> bool:           return v_eq(frozenset, self, other)
    def __ne__(self, other: object, /) -> bool:           return v_ne(frozenset, self, other)
    def __lt__(self, other: AbstractSet[Any], /) -> bool: return v_lt(frozenset, self, other)
    def __le__(self, other: AbstractSet[Any], /) -> bool: return v_le(frozenset, self, other)
    def __gt__(self, other: AbstractSet[Any], /) -> bool: return v_gt(frozenset, self, other)
    def __ge__(self, other: AbstractSet[Any], /) -> bool: return v_ge(frozenset, self, other)

    ############################################################################

    def __len__(self) -> int:            return v_len(frozenset, self)
    def __iter__(self) -> Iterator[Any]: return v_iter(frozenset, self)

    def __contains__(self, value: object, /) -> bool:  return v_contains(frozenset, self, value)

    ############################################################################

    def __str__(self) -> Any:  return v_str(frozenset, self)
    def __repr__(self) -> Any: return v_repr(frozenset, self)

    ############################################################################

    def __hash__(self) -> int: return v_hash(frozenset, self)

    ############################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(frozenset, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(frozenset, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(frozenset, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(frozenset, self)
