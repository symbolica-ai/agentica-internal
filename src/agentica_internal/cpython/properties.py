# fmt: off

from typing import TypeGuard, Any, Literal, NamedTuple

from .alias import MutablePropertyC, SlotPropertyC, TupleSlotPropertyC, PROPERTIES

__all__ = [
    'PropertyT',
    'PropertyInfo',
    'PropertyKind',
    'property_info'
]

################################################################################

type PropertyT = property | MutablePropertyC | SlotPropertyC | TupleSlotPropertyC

def is_property_t(obj: Any) -> TypeGuard[PropertyT]:
    return type(obj) in PROPERTIES

################################################################################

type PropertyKind = Literal['py', 'c', 'slot', 'tupelem']

################################################################################

class PropertyInfo(NamedTuple):
    kind:   PropertyKind
    read:   bool
    write:  bool
    delete: bool
    anno:   Any

################################################################################

def property_info(prop: PropertyT) -> PropertyInfo:
    cls = type(prop)
    if cls is property:
        fget, fset, fdel = prop.fget, prop.fset, prop.fdel
        annos = getattr(fget, '__annotations__', None)
        anno = annos.get('property') if isinstance(annos, dict) else None
        return PropertyInfo(
            'py',
            fget is not None,
            fset is not None,
            fdel is not None,
            anno,
        )
    elif cls is MutablePropertyC:
        return PropertyInfo('c', True, False, False, None)
    elif cls is SlotPropertyC:
        return PropertyInfo('slot', True, True, True, None)
    elif cls is TupleSlotPropertyC:
        return PropertyInfo('tupelem', True, False, False, None)
    else:
        raise TypeError(prop)
