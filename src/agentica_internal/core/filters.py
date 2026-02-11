# fmt: off

from collections.abc import Callable

from .fns import true_fn as ALL, false_fn as NONE

__all__ = [
    'Filter',
    'FilterFn',
    'to_filter_fn',
    'ALL',
    'NONE'
]

################################################################################

type Filter = str | FilterFn

type FilterFn = Callable[[object], bool]

def to_filter_fn(f: Filter, **named: FilterFn) -> FilterFn:
    if isinstance(f, str):
        if fn := named.get(f): return fn
        if fn := basic.get(f): return fn
    if callable(f):
        return f
    raise ValueError(f'Unknown filter: {f}')

basic = {'all': ALL, 'none': NONE}
