# fmt: off

__all__ = [
    'STATIC_CLASS',
    'SEQ_PATT_CLASS',
    'DICT_PATT_CLASS',
    'NO_CONS_CLASS',
    'HEAP_CLASS',
    'READ_ONLY_CLASS',
    'CAN_SUBCLASS_CLASS',
    'ABSTRACT_CLASS',
    'BUILTIN_SUBCLASS',
    'get_builtin_base'
]

# see line cpython/Include/object.h#%523 and on
STATIC_CLASS       = 1 << 1
SEQ_PATT_CLASS     = 1 << 5
DICT_PATT_CLASS    = 1 << 6
NO_CONS_CLASS      = 1 << 7
READ_ONLY_CLASS    = 1 << 8
HEAP_CLASS         = 1 << 9
CAN_SUBCLASS_CLASS = 1 << 10
ABSTRACT_CLASS     = 1 << 20

# see line cpython/Include/object.h#%608 and on, bits 24 to 31
#                      1 << 24,  25,   26,    27,    28,  29,   30,            31
_BASES: tuple[type, ...] = (int, list, tuple, bytes, str, dict, BaseException, type)
_MASKS = tuple(1 << i for i in range(24, 32))
_MASK_BASE = zip(_MASKS, _BASES)

BUILTIN_SUBCLASS = sum(_MASKS)

def get_builtin_base(cls: type) -> type[int, list, tuple, bytes, str, dict, BaseException, type]:
    flags = cls.__flags__
    if not flags & BUILTIN_SUBCLASS:
        return object
    for m, b in _MASK_BASE:
        if flags & m:
            return b
    return object
