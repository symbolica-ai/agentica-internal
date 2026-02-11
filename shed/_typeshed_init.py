################################################################################

from typing import Iterable, overload, Any, AbstractSet, Sequence, Awaitable
from collections.abc import Awaitable, Iterable, Sequence

################################################################################

__classes__ = [
    'IdentityFunction',
    'SupportsNext',
    'SupportsAnext',
    'SupportsDunderLT',
    'SupportsDunderGT',
    'SupportsDunderLE',
    'SupportsDunderGE',
    'SupportsAllComparisons',
    'SupportsAdd',
    'SupportsRAdd',
    'SupportsSub',
    'SupportsRSub',
    'SupportsMul',
    'SupportsRMul',
    'SupportsDivMod',
    'SupportsRDivMod',
    'SupportsIter',
    'SupportsAiter',
    'SupportsLenAndGetItem',
    'SupportsTrunc',
    'SupportsItems',
    'SupportsKeysAndGetItem',
    'SupportsGetItem',
    'SupportsContainsAndGetItem',
    'SupportsItemAccess',
    'HasFileno',
    'SupportsRead',
    'SupportsReadline',
    'SupportsNoArgReadline',
    'SupportsWrite',
    'SupportsFlush',
    'SliceableBuffer',
    'IndexableBuffer',
    'SupportsGetItemBuffer',
    'SizedBuffer',
]

__functions__ = []

__aliases__ = [
    'Incomplete',
    'Unused',
    'MaybeNone',
    'SupportsRichComparison',
    'StrPath',
    'BytesPath',
    'GenericPath',
    'StrOrBytesPath',
    'OpenTextModeUpdating',
    'OpenTextModeWriting',
    'OpenTextModeReading',
    'OpenTextMode',
    'OpenBinaryModeUpdating',
    'OpenBinaryModeWriting',
    'OpenBinaryModeReading',
    'OpenBinaryMode',
    'FileDescriptor',
    'FileDescriptorLike',
    'FileDescriptorOrPath',
    'ReadOnlyBuffer',
    'WriteableBuffer',
    'ReadableBuffer',
    'ExcInfo',
    'OptExcInfo',
    'ProfileFunction',
    'TraceFunction',
    'ConvertibleToFloat',
    'AnnotationForm',
]

__annos__ = []

__constants__ = []

__all__ = [
    'IdentityFunction',
    'SupportsNext',
    'SupportsAnext',
    'SupportsDunderLT',
    'SupportsDunderGT',
    'SupportsDunderLE',
    'SupportsDunderGE',
    'SupportsAllComparisons',
    'SupportsAdd',
    'SupportsRAdd',
    'SupportsSub',
    'SupportsRSub',
    'SupportsMul',
    'SupportsRMul',
    'SupportsDivMod',
    'SupportsRDivMod',
    'SupportsIter',
    'SupportsAiter',
    'SupportsLenAndGetItem',
    'SupportsTrunc',
    'SupportsItems',
    'SupportsKeysAndGetItem',
    'SupportsGetItem',
    'SupportsContainsAndGetItem',
    'SupportsItemAccess',
    'HasFileno',
    'SupportsRead',
    'SupportsReadline',
    'SupportsNoArgReadline',
    'SupportsWrite',
    'SupportsFlush',
    'SliceableBuffer',
    'IndexableBuffer',
    'SupportsGetItemBuffer',
    'SizedBuffer',
    'Incomplete',
    'Unused',
    'MaybeNone',
    'SupportsRichComparison',
    'StrPath',
    'BytesPath',
    'GenericPath',
    'StrOrBytesPath',
    'OpenTextModeUpdating',
    'OpenTextModeWriting',
    'OpenTextModeReading',
    'OpenTextMode',
    'OpenBinaryModeUpdating',
    'OpenBinaryModeWriting',
    'OpenBinaryModeReading',
    'OpenBinaryMode',
    'FileDescriptor',
    'FileDescriptorLike',
    'FileDescriptorOrPath',
    'ReadOnlyBuffer',
    'WriteableBuffer',
    'ReadableBuffer',
    'ExcInfo',
    'OptExcInfo',
    'ProfileFunction',
    'TraceFunction',
    'ConvertibleToFloat',
    'AnnotationForm',
]

################################################################################


class IdentityFunction:
    def __call__(self, x: Any, /) -> Any: ...


################################################################################


class SupportsNext:
    def __next__(self) -> Any: ...


################################################################################


class SupportsAnext:
    def __anext__(self) -> Awaitable: ...


################################################################################


class SupportsDunderLT:
    def __lt__(self, other: Any, /) -> bool: ...


################################################################################


class SupportsDunderGT:
    def __gt__(self, other: Any, /) -> bool: ...


################################################################################


class SupportsDunderLE:
    def __le__(self, other: Any, /) -> bool: ...


################################################################################


class SupportsDunderGE:
    def __ge__(self, other: Any, /) -> bool: ...


################################################################################


class SupportsAllComparisons:
    pass


################################################################################


class SupportsAdd:
    def __add__(self, x: Any, /) -> Any: ...


################################################################################


class SupportsRAdd:
    def __radd__(self, x: Any, /) -> Any: ...


################################################################################


class SupportsSub:
    def __sub__(self, x: Any, /) -> Any: ...


################################################################################


class SupportsRSub:
    def __rsub__(self, x: Any, /) -> Any: ...


################################################################################


class SupportsMul:
    def __mul__(self, x: Any, /) -> Any: ...


################################################################################


class SupportsRMul:
    def __rmul__(self, x: Any, /) -> Any: ...


################################################################################


class SupportsDivMod:
    def __divmod__(self, other: Any, /) -> Any: ...


################################################################################


class SupportsRDivMod:
    def __rdivmod__(self, other: Any, /) -> Any: ...


################################################################################


class SupportsIter:
    def __iter__(self) -> Any: ...


################################################################################


class SupportsAiter:
    def __aiter__(self) -> Any: ...


################################################################################


class SupportsLenAndGetItem:
    def __len__(self) -> int: ...
    def __getitem__(self, k: int, /) -> Any: ...


################################################################################


class SupportsTrunc:
    def __trunc__(self) -> int: ...


################################################################################


class SupportsItems:
    def items(self) -> AbstractSet[tuple[Any, Any]]: ...


################################################################################


class SupportsKeysAndGetItem:
    def keys(self) -> Iterable: ...
    def __getitem__(self, key: Any, /) -> Any: ...


################################################################################


class SupportsGetItem:
    def __getitem__(self, key: Any, /) -> Any: ...


################################################################################


class SupportsContainsAndGetItem:
    def __contains__(self, x: Any, /) -> bool: ...
    def __getitem__(self, key: Any, /) -> Any: ...


################################################################################


class SupportsItemAccess:
    def __contains__(self, x: Any, /) -> bool: ...
    def __getitem__(self, key: Any, /) -> Any: ...
    def __setitem__(self, key: Any, value: Any, /) -> None: ...
    def __delitem__(self, key: Any, /) -> None: ...


################################################################################


class HasFileno:
    def fileno(self) -> int: ...


################################################################################


class SupportsRead:
    def read(self, length: int = ..., /) -> Any: ...


################################################################################


class SupportsReadline:
    def readline(self, length: int = ..., /) -> Any: ...


################################################################################


class SupportsNoArgReadline:
    def readline(self) -> Any: ...


################################################################################


class SupportsWrite:
    def write(self, s: Any, /) -> object: ...


################################################################################


class SupportsFlush:
    def flush(self) -> object: ...


################################################################################


class SliceableBuffer:
    def __getitem__(self, slice: slice, /) -> Sequence[int]: ...


################################################################################


class IndexableBuffer:
    def __getitem__(self, i: int, /) -> int: ...


################################################################################


class SupportsGetItemBuffer:
    def __contains__(self, x: Any, /) -> bool: ...
    @overload
    # pyrefly: ignore[invalid-overload]
    def __getitem__(self, slice: slice, /) -> Sequence[int]: ...
    @overload
    # pyrefly: ignore[invalid-overload]
    def __getitem__(self, i: int, /) -> int: ...


################################################################################


class SizedBuffer:
    pass
