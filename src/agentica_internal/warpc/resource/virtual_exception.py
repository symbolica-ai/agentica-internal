# fmt: off

from ...cpython.exceptions import get_exception_args

from .__ import *
from .base import *

__all__ = [
    'ExceptionData',
]

################################################################################

class ExceptionData(ResourceData):
    __slots__ = 'cls', 'args', 'keys', 'notes'

    KIND = Kind.Exception
    FORBIDDEN_FORM = forbidden_function

    cls:  type[BaseException]
    args: ArgsT
    keys: strtup
    notes: strtup

    @property
    def name(self) -> str:
        return self.cls.__name__

    @classmethod
    def describe_resource(cls, exc: BaseException) -> 'ExceptionData':
        data = ExceptionData()
        data.cls = type(exc)
        data.args = get_exception_args(exc)
        data.notes = getattr(exc, '__notes__', None)
        data.keys = tuple(exc.__dict__.keys())
        return data

    # implementation attached later
    def create_resource(self, handle: ResourceHandle) -> BaseException:
        handle.kind = Kind.Exception
        handle.keys = list(self.keys)
        handle.open = False
        handle.name = f'<{self.cls.__name__!r} exception>'
        v_exc = BaseException.__new__(self.cls, *self.args)
        set_raw(v_exc, VHDL, handle)
        if notes := self.notes:
            v_exc.__notes__ = list(notes)
        return v_exc
