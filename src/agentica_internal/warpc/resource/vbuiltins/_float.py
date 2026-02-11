# fmt: off

from .vshared import *
from .vmethods import *

################################################################################

class _float(float):

    def is_integer(self) -> bool:
        return False

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

    def __eq__(self, other, /) -> bool: return v_eq(float, self, other)
    def __ne__(self, other, /) -> bool: return v_ne(float, self, other)
    def __lt__(self, other, /) -> bool: return v_lt(float, self, other)
    def __le__(self, other, /) -> bool: return v_le(float, self, other)
    def __gt__(self, other, /) -> bool: return v_gt(float, self, other)
    def __ge__(self, other, /) -> bool: return v_ge(float, self, other)

    ############################################################################

    def __str__(self) -> Any:  return v_str(float, self)
    def __repr__(self) -> Any: return v_repr(float, self)

    ############################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(float, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(float, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(float, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(float, self)

    ############################################################################

    def __hash__(self) -> int: return v_hash(float, self)
