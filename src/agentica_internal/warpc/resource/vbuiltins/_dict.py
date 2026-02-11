# fmt: off

from .vshared import *
from .vmethods import *

################################################################################

class _dict(dict):

    @forward
    def clear(self) -> None: ...

    @forward
    def copy(self): ...

    @forward
    def get(self, key, default=None) -> Any: ...

    @forward
    def items(self) -> Iterable[tuple[Any, Any]]: ...

    @forward
    def keys(self) -> Iterable[Any]: ...

    @forward
    def pop(self, key, default=ARG_DEFAULT, /) -> Any: ...

    @forward
    def popitem(self) -> tuple[Any, Any]: ...

    @forward
    def reversed(self) -> Iterable[Any]: ...

    @forward
    def setdefault(self, key, default=None, /) -> None: ...

    def update(self, iterable=ARG_DEFAULT, /, **kwargs) -> None:
        handle = obj_handle(self)
        return handle.hdlr(handle, ResourceCallMethod(self, 'update', (iterable,), kwargs))

    @forward
    def values(self) -> Iterable[Any]: ...

    ############################################################################

    @classmethod
    def fromkeys(cls, iterable: Iterable[Any], value=None, /):
        handle = cls_handle(cls)
        return handle.hdlr(handle, ResourceCallMethod(cls, 'fromkeys', (iterable, value),))

    ############################################################################

    @forward
    def __or__(self, other: list, /) -> list: ...

    ############################################################################

    def __eq__(self, other, /) -> bool: return v_eq(dict, self, other)
    def __ne__(self, other, /) -> bool: return v_ne(dict, self, other)
    def __lt__(self, other, /) -> bool: return v_lt(dict, self, other)
    def __le__(self, other, /) -> bool: return v_le(dict, self, other)
    def __gt__(self, other, /) -> bool: return v_gt(dict, self, other)
    def __ge__(self, other, /) -> bool: return v_ge(dict, self, other)

    ############################################################################

    def __len__(self) -> int:                return v_len(dict, self)
    def __iter__(self) -> Iterator[Any]:     return v_iter(dict, self)

    ############################################################################

    def __contains__(self, key, /) -> bool:       return v_contains(dict, self, key)
    def __getitem__(self, key, /) -> object:      return v_getitem(dict, self, key)
    def __setitem__(self, key, value, /) -> None: return v_setitem(dict, self, key, value)
    def __delitem__(self, key, /) -> None:        return v_delitem(dict, self, key)

    ############################################################################

    def __str__(self) -> Any:  return v_str(dict, self)
    def __repr__(self) -> Any: return v_repr(dict, self)

    ############################################################################

    def __getattr__(self, name: str, /) -> Any:         return v_getattr(list, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(list, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(list, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(list, self)

    ############################################################################

    __hash__ = None
