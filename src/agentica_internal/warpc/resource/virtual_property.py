# fmt: off

from ...cpython.properties import property_info
from .__ import *
from .base import *

__all__ = [
    'PropertyData',
]

################################################################################

class PropertyData(ResourceData):
    __slots__ = 'read', 'write', 'delete', 'anno'

    KIND = Kind.Property
    FORBIDDEN_FORM = forbidden_object

    read:   bool
    write:  bool
    delete: bool
    anno:   TypeT

    # implementation attached later
    @classmethod
    def describe_resource(cls, prop: PropertyT) -> 'PropertyData': ...  # noqa: F841

    # implementation attached later
    def create_resource(self, handle: ResourceHandle) -> PropertyT: ...


###############################################################################

def describe_real_property(prop: PropertyT) -> PropertyData:
    info = property_info(prop)
    data = PropertyData()
    data.read = info.read
    data.write = info.write
    data.delete = info.delete
    data.anno = info.anno
    return data

###############################################################################

def create_virtual_property(data: PropertyData, handle: ResourceHandle) -> property:
    anno = data.anno
    fget = fset = fdel = None

    handle.kind = Kind.Property
    handle.keys = []
    handle.open = False
    handle.name = ''

    def reset_anno(fn: FunctionType):
        if anno is None:
            fn.__annotations__.clear()

    if data.read:
        def fget(obj) -> anno:
            obj_handle = get_handle(obj)
            return obj_handle.hdlr(handle, ResourceGetAttr(obj, handle.name))
        reset_anno(fget)  # type: ignore

    if data.write:
        def fset(obj, value: anno):
            obj_handle = get_handle(obj)
            return handle.hdlr(handle, ResourceSetAttr(obj, handle.name, value))
        reset_anno(fget)  # type: ignore

    if data.delete:
        def fdel(obj):
            obj_handle = get_handle(obj)
            return handle.hdlr(handle, ResourceDelAttr(obj, handle.name))
        reset_anno(fget)  # type: ignore

    v_prop = _property(fget=fget, fset=fset, fdel=fdel)
    set_raw(v_prop, VHDL, handle)
    return v_prop


###############################################################################

class _property(property):

    def __set_name__(self, owner, name: str):
        prop_name = name
        cls_name = owner.__qualname__
        mod_name = owner.__module__
        handle = get_raw(self, VHDL)
        handle.name = name
        qual_name = f'{cls_name}.{name}'
        for obj in (self, self.fset, self.fget, self.fdel):
            set_names(obj, prop_name, qual_name, mod_name)

_property.__name__ = _property.__qualname__ = 'property'
_property.__module__ = 'builtins'

def set_names(obj: object, prop_name: str, qual_name: str, mod_name: str):
    if obj is not None:
        set_raw(obj, NAME, prop_name)
        set_raw(obj, QUALNAME, qual_name)
        set_raw(obj, MODULE, mod_name)


################################################################################

# attach implementations to class
PropertyData.describe_resource = staticmethod(describe_real_property)
PropertyData.create_resource = create_virtual_property
