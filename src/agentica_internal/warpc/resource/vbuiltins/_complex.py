# fmt: off

from .vshared import *
from .vmethods import *

################################################################################

class _complex(complex):

    def conjugate(self): ...

    ############################################################################

    @forward
    def __abs__(self, *args, **kwargs): ...

    @forward
    def __add__(self, *args, **kwargs): ...

    @forward
    def __bool__(self, *args, **kwargs): ...

    @forward
    def __complex__(self, *args, **kwargs): ...

    @forward
    def __format__(self, *args, **kwargs): ...

    @forward
    def __mul__(self, *args, **kwargs): ...

    @forward
    def __neg__(self, *args, **kwargs): ...

    @forward
    def __pos__(self, *args, **kwargs): ...

    @forward
    def __pow__(self, *args, **kwargs): ...

    @forward
    def __sub__(self, *args, **kwargs): ...

    @forward
    def __truediv__(self, *args, **kwargs): ...

    ############################################################################

    def __eq__(self, other, /) -> bool: return v_eq(complex, self, other)
    def __ne__(self, other, /) -> bool: return v_ne(complex, self, other)
    def __lt__(self, other, /) -> bool: return v_lt(complex, self, other)
    def __le__(self, other, /) -> bool: return v_le(complex, self, other)
    def __gt__(self, other, /) -> bool: return v_gt(complex, self, other)
    def __ge__(self, other, /) -> bool: return v_ge(complex, self, other)

    ############################################################################

    def __str__(self) -> Any:  return v_str(complex, self)
    def __repr__(self) -> Any: return v_repr(complex, self)

    ############################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(complex, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(complex, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(complex, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(complex, self)

    ############################################################################

    def __hash__(self) -> int: return v_hash(complex, self)
