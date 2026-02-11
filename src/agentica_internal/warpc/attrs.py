# fmt: off

from collections.abc import Callable, Iterable
from typing import Any, Literal, cast

__all__ = [
    'VHDL',
    'WARP_AS',
    'CLASS_WARP_AS',
    'FUTURE_ID',
    'WORLD_ID',
    'CLASS',
    'DICT',
    'NAME',
    'QUALNAME',
    'MODULE',
    'DOC',
    'ANNOS',
    'TPARAMS',
    'BASES',
    'MRO',
    'SLOTS',
    'SATTRS',
    'MATCHARGS',
    'FILE',
    'ALL',
    'CLS_GETITEM',
    'get_raw',
    'multi_get_raw',
    'multi_get',
    'set_raw',
    'multi_set_raw',
    'multi_set',
]

# shared

VHDL: Literal['___vhdl___'] = '___vhdl___'

WORLD_ID        = '___world_id___'
FUTURE_ID       = '___future_id___'
WARP_AS         = '___warp_as___'
CLASS_WARP_AS   = '___class_warp_as___'

# shared
CLASS      = '__class__'
DICT       = '__dict__'

# class and function
NAME       = '__name__'
QUALNAME   = '__qualname__'
MODULE     = '__module__'
DOC        = '__doc__'
ANNOS      = '__annotations__'
TPARAMS    = '__type_params__'

# class
BASES       = '__bases__'
MRO         = '__mro__'
SLOTS       = '__slots__'
SATTRS      = '__static_attributes__'
MATCHARGS   = '__match_args__'

# module
FILE       = '__file__'
ALL        = '__all__'

CLS_GETITEM = '__class_getitem__'

################################################################################

get_raw = cast(Callable[[Any, str], Any], object.__getattribute__)
set_raw = cast(Callable[[Any, str, Any], Any], object.__setattr__)

################################################################################

def multi_get(thing: Any, *keys: str) -> Iterable[Any]:
    for k in keys:
        yield getattr(thing, k, None)

def multi_get_raw(thing: Any, *keys: str) -> Iterable[Any]:
    for k in keys:
        try:
            yield get_raw(thing, k)
        except AttributeError:
            yield None

################################################################################

def multi_set(thing: Any, *args: dict[str, Any], **kwargs: Any):
    for a in args:
        kwargs.update(a)
    for k, v in kwargs.items():
        setattr(thing, k, v)

def multi_set_raw(thing: Any, *args: dict[str, Any], **kwargs: Any):
    for a in args:
        kwargs.update(a)
    for k, v in kwargs.items():
        set_raw(thing, k, v)
