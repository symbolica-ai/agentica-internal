# fmt: off

from .vshared import *
from .vmethods import *

################################################################################

class _int(int):

    def is_integer(self) -> bool:
        return True

    @forward
    def as_integer_ratio(self) -> tuple[int, int]: ...

    @forward
    def bit_count(self) -> int: ...

    @forward
    def bit_length(self) -> int: ...

    @forward
    def conjugate(self) -> int: ...

    @classmethod
    def from_bytes(cls, data, byteorder=ARG_DEFAULT, *, signed=ARG_DEFAULT) -> bool:
        handle = cls_handle(cls)
        return handle.hdlr(handle, ResourceCallMethod(cls, 'from_bytes', (data, byteorder), {'signed': signed}),)

    @forward
    def to_bytes(self, length: int = ARG_DEFAULT, byteorder=ARG_DEFAULT, *, signed=False) -> bytes: ...

    ############################################################################

    @forward
    def __abs__(self) -> Self: ...

    @forward
    def __add__(self, other) -> Self: ...

    @forward
    def __and__(self, other) -> Self: ...

    @forward
    def __bool__(self) -> bool: ...

    @forward
    def __ceil__(self) -> Self: ...

    @forward
    def __complex__(self, *args, **kwargs): ...

    @forward
    def __divmod__(self, other) -> Self: ...

    @forward
    def __float__(self) -> float: ...

    @forward
    def __floordiv__(self) -> Self: ...

    @forward
    def __floor__(self, other) -> Self: ...

    @forward
    def __index__(self) -> int: ...

    @forward
    def __int__(self) -> int: ...

    @forward
    def __invert__(self) -> Self: ...

    @forward
    def __lshift__(self, other) -> Self: ...

    @forward
    def __mod__(self, other) -> bool: ...

    @forward
    def __mul__(self, other) -> Self: ...

    @forward
    def __neg__(self) -> Self: ...

    @forward
    def __or__(self, other): ...

    @forward
    def __pos__(self) -> Self: ...

    @forward
    def __pow__(self, other) -> Self: ...

    ############################################################################

    def __eq__(self, other, /) -> bool: return v_eq(int, self, other)
    def __ne__(self, other, /) -> bool: return v_ne(int, self, other)
    def __lt__(self, other, /) -> bool: return v_lt(int, self, other)
    def __le__(self, other, /) -> bool: return v_le(int, self, other)
    def __gt__(self, other, /) -> bool: return v_gt(int, self, other)
    def __ge__(self, other, /) -> bool: return v_ge(int, self, other)

    ############################################################################

    def __str__(self) -> Any:  return v_str(int, self)
    def __repr__(self) -> Any: return v_repr(int, self)

    ############################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(int, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(int, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(int, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(int, self)

    ############################################################################

    def __hash__(self) -> int: return v_hash(int, self)

    ############################################################################

    def __class_getitem__(cls, item): return v_class_getitem(object, cls, item)
