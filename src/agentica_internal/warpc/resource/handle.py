# fmt: off

from ..__ import *
from ..attrs import VHDL
from .__raw import *

__all__ = [
    'is_virtual_object',
    'is_virtual_class',
    'ExecHandler',
    'ResourceHandle',
    'has_handle',
    'get_handle',
    'obj_handle',
    'cls_handle',
]


################################################################################

if TYPE_CHECKING:
    from ..request.request_resource import ResourceRequest

################################################################################

type ExecHandler = Callable[[ResourceHandle, 'ResourceRequest'], Any]

################################################################################

# ResourceHandle is buried inside a virtual resource (under the VHDL attribute)
# and contains enough information to resolve resource requests
class ResourceHandle:
    __slots__ = 'grid', 'fkey', 'hdlr', 'kind', 'keys', 'open', 'name', 'hash', 'size', '_str', '_rep'

    # don't wish this to ever be visible
    if TYPE_CHECKING:
        grid: GlobalRID     # what is our global resource ID?
        fkey: FrameKey      # what frame carries information about us? CURRENTLY NOT USED
        hdlr: ExecHandler   # callback function to satisfy requests
        kind: Kind          # Kind.Class, Kind.Function, etc.
        keys: list[str]     # which `getattrs` should be let through
        open: bool          # True if there might be more keys we don't know about locally
        hash: int           # set the first time __hash__ is executed remotely
        name: str           # the unqualified name of the resource, if any
        size: int           # set if object has an unchanging `__len__`
        _str: str           # statically known result of calling __str__
        _rep: str           # statically known result of calling __repr__

    def __repr__(self) -> str:
        info = self.__debug_info_str__()
        return f"<{info}>"

    def __debug_info_str__(self) -> str:
        name = self.name
        kind = self.kind
        grid = f_grid(self.grid)
        if name.endswith('>'):
            return f'{name[1:-1]} {grid}'
        return f'{kind} {name!r} {grid}'

    __short_str__ = __str__ = __repr__

################################################################################

def has_handle(obj: Any) -> bool:
    try:
        if type(obj) is type or isinstance(obj, type):
            handle = cls_get(obj, VHDL)
        elif isinstance(obj, ModuleType):
            handle = mod_get(obj, VHDL)
        else:
            handle = obj_get(obj, VHDL)
        return type(handle) is ResourceHandle
    except:
        pass
    return False

def is_virtual_object(obj: Any) -> bool:
    try:
        handle = obj_get(obj, VHDL)
        return type(handle) is ResourceHandle
    except:
        pass
    return False

def is_virtual_class(cls: type) -> bool:
    try:
        if type(cls) is type or isinstance(cls, type):
            handle = cls_get(cls, VHDL)
            return type(handle) is ResourceHandle
    except:
        pass
    return False

def get_handle(obj: Any) -> ResourceHandle | None:
    try:
        if type(obj) is type or isinstance(obj, type):
            handle = cls_get(obj, VHDL)
        elif isinstance(obj, ModuleType):
            handle = mod_get(obj, VHDL)
        else:
            handle = obj_get(obj, VHDL)
        if type(handle) is ResourceHandle:
            return handle
    except:
         pass
    return None
