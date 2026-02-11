################################################################################

import sys
from types import MappingProxyType
from typing import Any, Iterable, ClassVar, Iterator
from collections.abc import Iterable, Iterator

################################################################################

__classes__ = ['dict_keys', 'dict_values', 'dict_items']

__functions__ = []

__aliases__ = []

__annos__ = []

__constants__ = []

__all__ = ['dict_keys', 'dict_values', 'dict_items']

################################################################################


class dict_keys:
    __hash__: ClassVar[None]

    def __eq__(self, value: object, /) -> bool: ...
    def __reversed__(self) -> Iterator: ...

    if sys.version_info >= (3, 13):

        def isdisjoint(self, other: Iterable, /) -> bool: ...

    if sys.version_info >= (3, 10):

        @property
        def mapping(self) -> MappingProxyType: ...


################################################################################


class dict_values:
    def __reversed__(self) -> Iterator: ...

    if sys.version_info >= (3, 10):

        @property
        def mapping(self) -> MappingProxyType: ...


################################################################################


class dict_items:
    __hash__: ClassVar[None]

    def __eq__(self, value: object, /) -> bool: ...
    def __reversed__(self) -> Iterator[tuple[Any, Any]]: ...

    if sys.version_info >= (3, 13):

        def isdisjoint(self, other: Iterable[tuple[Any, Any]], /) -> bool: ...

    if sys.version_info >= (3, 10):

        @property
        def mapping(self) -> MappingProxyType: ...
