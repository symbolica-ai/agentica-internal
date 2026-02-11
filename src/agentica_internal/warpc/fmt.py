# fmt: off

from typing import Any
from collections.abc import Callable
from types import NoneType

from ..core.fmt import f_object, f_object_id
from .alias import *

__all__ = [
    'f_id',
    'f_grid',
    'f_fkey',
    'f_slot',
    'f_object',
    'f_object_id',
]

################################################################################

def f_id(i: int) -> str:
    if type(i) is int:
        return f'{i:x}' if i >= 0 else f'-{-i:x}'
    return '<!id>'

def f_grid(grid: GlobalRID) -> str:
    if type(grid) is tuple and len(grid) == 3:
        wid, fid, rid = grid
        return f'{wid:x}:{fid:x}:{rid:x}'
    return '<!grid>'

def f_fkey(fkey: FrameKey) -> str:
    if type(fkey) is tuple and len(fkey) == 2:
        wid, fid = fkey
        return f'{wid:x}:{fid:x}'
    return '<!fkey>'

def f_slot(key: str, val: Any, fn: Callable[..., str] = f_object_id) -> str:
    match val:
        case None:
            return 'None'
        case type():
            return val.__name__
        case str() | bytes() if len(val) < 12:
            return repr(val)
        case tuple():
            if key == 'grid':
                return f_grid(val)
            if not val:
                return '()'
            if len(val) == 1:
                return '(' + f_slot('', val[0], fn) + ',)'
            if _is_short(val):
                return '(' + ', '.join(f_slot('', v, fn) for v in val) + ')'
            return '(' + f'{len(val)}…' + ')'
        case list():
            if not val:
                return '[]'
            if _is_short(val):
                return '[' + ', '.join(f_slot('', v, fn) for v in val) + ']'
            return '[' + f'{len(val)}…' + ']'
        case dict():
            if not val:
                return '{}'
            return '{' + f'{len(val)}…' + '}'
        case int() | float() | bool():
            if key.endswith('id'):
                return f_id(val)
            return str(val)
        case _:
            return fn(val)

SHORT = int, bool, str, type, NoneType

def _is_short(seq) -> bool:
    return len(seq) <= 4 and all(type(v) in SHORT for v in seq)
