# fmt: off

# NOTE: there is no actual system iterator class to inherit, since itertools.chain, etc.
# are all different C type bases, so we use collections.abc's Iterator as the base

from .vshared import *
from .vmethods import *

################################################################################

class _iterator(Iterator):

    def __next__(self) -> Any:
        handle = obj_handle(self)
        return handle.hdlr(handle, ResourceCallSystemMethod(self, next))

    def __length_hint__(self) -> int:
        return getattr(obj_handle(self), 'size', NotImplemented)

    def __iter__(self) -> Any:
        return self

    ############################################################################

    def __eq__(self, other, /) -> bool: return self is other
    def __ne__(self, other, /) -> bool: return self is not other

    ############################################################################

    # should we not just forbid attribute access here?
    def __getattr__(self, name: str, /) -> Any:         return v_getattr(Iterator, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(Iterator, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(Iterator, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(Iterator, self)

    ############################################################################

    # no point doing a VRR, we should just say what kind of iterator we are
    def __str__(self) -> Any:  return f'<{type(self).__name__!r} iterator object>'
    def __repr__(self) -> Any: return f'<{type(self).__name__!r} iterator object>'

    ############################################################################

    # iterators are by definition not stable, so might as well use ID as the hash
    def __hash__(self) -> int: return id(self)

_iterator.__name__ = _iterator.__qualname__ = 'iterator'
_iterator.__module__ = 'builtins'
