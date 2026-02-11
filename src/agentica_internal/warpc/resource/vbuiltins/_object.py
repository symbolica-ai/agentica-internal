# fmt: off

from .vshared import *
from .vmethods import *

################################################################################

class _object(object):

    ############################################################################

    def __str__(self) -> Any:  return v_str(object, self)
    def __repr__(self) -> Any: return v_repr(object, self)

    ############################################################################

    def __hash__(self) -> int: return v_hash(object, self)

    ############################################################################

    def __getattribute__(self, name: str, /) -> Any:    return v_getattribute(object, self, name)
    def __getattr__(self, name: str, /) -> Any:         return v_getattr(object, self, name)
    def __setattr__(self, name: str, value, /) -> None: return v_setattr(object, self, name, value)
    def __delattr__(self, name: str, /):                return v_delattr(object, self, name)
    def __dir__(self) -> list[str]:                     return v_dir(object, self)

    ############################################################################

    def __reduce__(self):
        from pickle import PicklingError
        raise PicklingError(f"Pickling of {type(self).__name__} not possible in this environment")

    ############################################################################

    @special
    def __class_getitem__(cls, item):
        return v_class_getitem(object, cls, item)
