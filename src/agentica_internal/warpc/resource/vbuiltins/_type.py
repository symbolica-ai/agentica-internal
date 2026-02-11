# fmt: off

from .vshared import *
from .vmethods import *

################################################################################

class _type(type):

    @special
    def __class_getitem__(cls, item):
        return v_getitem(type, cls, item)

    def __getattr__(self, name: str) -> Any:
        return v_getattr(type, object, name)
