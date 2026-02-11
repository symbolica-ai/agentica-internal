# fmt: off

from typing import AbstractSet

from .vshared import *
from .vmethods import *

################################################################################

class _set(set):

    @forward
    def add(self, element, /) -> None: ...

    @forward
    def copy(self) -> Self: ...

    @forward
    def clear(self) -> Self: ...

    @forward
    def difference(self, *s: Iterable[Any]) -> Self: ...

    @forward
    def difference_update(self, *s: Iterable[Any]) -> None: ...

    @forward
    def discard(self, element: Any, /) -> None: ...

    @forward
    def intersection(self, *s: Iterable[Any]) -> Self: ...

    @forward
    def intersection_update(self, *s: Iterable[Any]) -> None: ...

    @forward
    def isdisjoint(self, s: Iterable[Any], /) -> bool: ...

    @forward
    def issubset(self, s: Iterable[Any], /) -> bool: ...

    @forward
    def issuperset(self, s: Iterable[Any], /) -> bool: ...

    @forward
    def pop(self) -> Any: ...

    @forward
    def remove(self, element, /) -> None: ...

    @forward
    def symmetric_difference(self, s: Iterable[Any], /) -> Self: ...

    @forward
    def symmetric_difference_update(self, s: Iterable[Any], /) -> None: ...

    @forward
    def union(self, *s: Iterable[Any]) -> Self: ...

    @forward
    def update(self, *s: Iterable[Any]) -> None: ...

    ############################################################################

    @forward
    def __and__(self, value: AbstractSet[Any], /) -> Self: ...

    @forward
    def __iand__(self, value: AbstractSet[Any], /) -> Self: ...

    @forward
    def __or__(self, value: AbstractSet[Any], /) -> Self: ...

    @forward
    def __ior__(self, value: AbstractSet[Any], /) -> Self: ...

    @forward
    def __sub__(self, value: AbstractSet[Any], /) -> Self: ...

    @forward
    def __isub__(self, value: AbstractSet[Any], /) -> Self: ...

    @forward
    def __xor__(self, value: AbstractSet[Any], /) -> Self: ...

    @forward
    def __ixor__(self, value: AbstractSet[Any], /) -> Self: ...

    ############################################################################

    def __eq__(self, other: object, /) -> bool:           return v_eq(set, self, other)
    def __ne__(self, other: object, /) -> bool:           return v_ne(set, self, other)
    def __lt__(self, other: AbstractSet[Any], /) -> bool: return v_lt(set, self, other)
    def __le__(self, other: AbstractSet[Any], /) -> bool: return v_le(set, self, other)
    def __gt__(self, other: AbstractSet[Any], /) -> bool: return v_gt(set, self, other)
    def __ge__(self, other: AbstractSet[Any], /) -> bool: return v_ge(set, self, other)

    ############################################################################

    def __len__(self) -> int:                         return v_len(set, self)
    def __iter__(self) -> Iterator[Any]:              return v_iter(set, self)
    def __contains__(self, value: object, /) -> bool: return v_contains(set, self, value)

    ############################################################################

    def __str__(self) -> Any:  return v_str(set, self)
    def __repr__(self) -> Any: return v_repr(set, self)

    ############################################################################

    __hash__ = None

    ############################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(set, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(set, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(set, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(set, self)

    ############################################################################

    def __class_getitem__(cls, item): return v_class_getitem(object, cls, item)
