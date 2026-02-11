# fmt: off

from ...cpython.iters import iter_len_hint, UNBOUNDED

from .__ import *
from .base import *
from .vbuiltins._iterator import _iterator

__all__ = [
    'IteratorData',
]

################################################################################

class IteratorData(ResourceData):
    __slots__ = 'name', 'hint',

    KIND = Kind.Iterator
    FORBIDDEN_FORM = forbidden_object

    name: str | None
    hint: int | None

    @classmethod
    def describe_resource(cls, it: IteratorT) -> 'IteratorData':
        data = IteratorData()
        size = iter_len_hint(it)
        data.name = type(it).__name__
        data.hint = None if size is UNBOUNDED else size
        return data

    def create_resource(self, handle: ResourceHandle) -> IteratorT:
        v_it = _iterator()
        handle.keys = []
        handle.open = False
        if name := self.name:
            handle.name = f'<{name!r} iterator>'
        obj_set(v_it, VHDL, handle)
        return v_it
