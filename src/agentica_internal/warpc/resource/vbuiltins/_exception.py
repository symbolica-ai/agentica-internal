# fmt: off

from types import TracebackType

from .vshared import *
from .vmethods import *

################################################################################

class _BaseException(BaseException):

    args: tuple[Any, ...]

    ################################################################################

    def __new__(cls):
        return BaseException.__new__(cls, ())  # type: ignore

    @v_dummy
    def __init__(self, *args: object) -> None: ...

    @v_dummy
    def __setstate__(self, state: dict[str, Any] | None, /) -> None: ...

    ################################################################################

    def __repr__(self) -> Any: return v_repr(BaseException, self)
    def __str__(self) -> Any:  return v_str(BaseException, self)

    ################################################################################

    def __hash__(self) -> int: return v_hash(BaseException, self)

    ################################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(BaseException, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(BaseException, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(BaseException, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(BaseException, self)

    ################################################################################

    def with_traceback(self, tb: TracebackType | None, /) -> Self:
        return self

    @forward
    def add_note(self, note: str, /) -> None: ...
