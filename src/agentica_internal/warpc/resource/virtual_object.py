# fmt: off

from .__ import *
from .base import *

__all__ = [
    'ObjectData',
]


################################################################################

class ObjectData(ResourceData):
    __slots__ = 'cls', 'keys', 'open', 'size', 'hash',

    KIND = Kind.Object
    FORBIDDEN_FORM = forbidden_object

    cls:    ClassT
    keys:   strtup
    open:   bool
    size:   int | None
    hash:   int | None

    # implementation attached later
    @classmethod
    def describe_resource(cls, obj: ObjectT) -> 'ObjectData': ...

    # implementation attached later
    def create_resource(self, handle: ResourceHandle) -> ObjectT: ...


################################################################################

def describe_real_object(obj: ObjectT) -> ObjectData:
    cls = type(obj)

    if is_forbidden(obj, cls.__module__):
        raise E.WarpEncodingForbiddenError(f"<'{cls.__module__}.{cls.__qualname__}' object>")

    data = ObjectData()
    data.cls = cls

    keys = ()
    try:
        odict = get_raw(obj, DICT)
        keys = tuple(odict.keys())
    except:
        pass

    data.keys = keys
    data.open = flags.OBJECT_OPEN_KEYS
    data.size = len(obj) if issubclass(cls, SEND_SIZE) else None
    data.hash = hash(obj) if issubclass(cls, SEND_HASH) else None

    return data


SEND_SIZE = str, bytes, tuple, frozenset
SEND_HASH = str, bytes, bool, int, float

################################################################################

def create_virtual_object(data: ObjectData, handle: ResourceHandle) -> ObjectT:

    handle.kind = Kind.Object
    handle.keys = list(data.keys)
    handle.open = data.open
    handle.name = f'<{data.cls.__name__!r} object>'

    # if object has an immutable __len__ or __hash__
    if data.size is not None:
        handle.size = data.size
    if data.hash is not None:
        handle.hash = data.hash

    v_cls = data.cls

    has_handle = False
    try:
        cls_get(v_cls, VHDL)
        has_handle = True
    except:
        pass

    if not has_handle:
        # if we are being asked to create an instance of a builtin class
        # like 'list' directly, use code which creates a totally synthetic
        # class on-demand
        from .virtual_builtin import create_virtual_builtin_object
        return create_virtual_builtin_object(v_cls, handle)

    # this triggers special behavior in create_virtual_class's `def __new__` stub
    # to AVOID virtualizing and instead just embed the handle
    v_obj = v_cls.__new__(v_cls, ___vhdl___=handle)  # type: ignore
    return v_obj


################################################################################

ObjectData.describe_resource = staticmethod(describe_real_object)
ObjectData.create_resource = create_virtual_object
