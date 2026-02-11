# fmt: off

from .__ import *
from .base import *

__all__ = [
    'CoroutineData',
]


################################################################################

class CoroutineData(ResourceData):
    __slots__ = 'name', 'qname'

    KIND = Kind.Coroutine
    FORBIDDEN_FORM = forbidden_object

    name: str
    qname: optstr

    @classmethod
    def describe_resource(cls, coro: CoroutineT) -> 'CoroutineData':
        data = CoroutineData()
        data.name = getattr(coro, NAME, '')
        data.qname = getattr(coro, QUALNAME, '')
        return data

    def create_resource(self, handle: ResourceHandle) -> 'coroutine':
        handle.kind = Kind.Coroutine
        handle.keys = []
        handle.open = False
        handle.name = self.name
        vobj = coroutine(self.name, self.qname)
        obj_set(vobj, VHDL, handle)
        return vobj


################################################################################

# this 'coroutine' mimics `types.coroutine` as closely as possible.

class coroutine(Coroutine):
    __slots__ = NAME, QUALNAME, VHDL

    if TYPE_CHECKING:
        __name__: str
        __qualname__: str

    def __init__(self, name: str = '', qualname: str = ''):
        self.__name__ = name = name or '<coroutine>'
        self.__qualname__ = qualname or name

    def cr_origin(self) -> tuple[tuple[str, int, str], ...] | None:
        handle = obj_handle(self)
        return handle.hdlr(handle, ResourceCallMethod(self, 'cr_origin'))

    def cr_suspended(self) -> bool:
        handle = obj_handle(self)
        return handle.hdlr(handle, ResourceCallMethod(self, 'cr_suspended'))

    def close(self) -> None:
        handle = obj_handle(self)
        return handle.hdlr(handle, ResourceCallMethod(self, 'close'))

    def __await__(self) -> A.Generator:
        handle = obj_handle(self)
        return handle.hdlr(handle, ResourceCallMethod(self, '__await__'))

    def send(self, arg: Any, /) -> Any:
        handle = obj_handle(self)
        return handle.hdlr(handle, ResourceCallMethod(self, 'send', (arg,)))

    def throw(self, typ: BaseException,
                    val: None = None,
                    tb: S.TracebackT | None = ..., /) -> Any:
        handle = obj_handle(self)
        return handle.hdlr(handle, ResourceCallMethod(self, 'throw', (type, val, None,)))


coroutine.__module__ = 'virtual'
