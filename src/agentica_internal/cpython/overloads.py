# fmt: off

import typing
from collections import defaultdict
from collections.abc import Callable
from types import FunctionType
from functools import partial

__all__ = [
    'get_overloads',
    'set_overloads',
    'overload_dummy',
    'OverloadContext'
]

################################################################################

type OverloadContext = int | None

def get_overloads(func: Callable) -> list[Callable]:
    f, m, q, c = _fun_info(func)
    if not m or not q: return []
    registry = get_overload_registry(c)
    if m not in registry: return []
    mod_dict = registry[m]
    if q not in mod_dict: return []
    return list(mod_dict[q].values())

get_overloads.__module__ = 'typing'

################################################################################

def _fun_info(func: Callable) -> tuple[FunctionType | None, str | None, str | None, OverloadContext]:
    f = getattr(func, "__func__", func)
    m = getattr(f, "__module__", None)
    q = getattr(f, '__qualname__', None)
    c = getattr(f, OVERLOAD_CONTEXT, None)
    if type(f) is not FunctionType: f = None
    if type(m) is not str: m = None
    if type(q) is not str: q = None
    if type(c) is not int: c = None
    return f, m, q, c

################################################################################

def get_overload_context(func: Callable) -> OverloadContext:
    f = getattr(func, "__func__", func)
    c = getattr(f, OVERLOAD_CONTEXT, None)
    return c

################################################################################

def set_overloads(func: Callable, dummies: list[Callable], c: OverloadContext = None):
    if not dummies: return
    f, m, q, d = _fun_info(func)
    if c is None:
        c = d
    elif f is not None:
        setattr(f, OVERLOAD_CONTEXT, c)
    registry = get_overload_registry(c)
    mq_dict = registry[m][q]
    mq_dict.clear()
    for g in dummies:
        g = getattr(g, "__func__", g)
        if type(g) is not FunctionType: continue
        if c is not None: setattr(g, OVERLOAD_CONTEXT, c)
        l = g.__code__.co_firstlineno
        while l in mq_dict: l -= 2
        mq_dict[l] = g

################################################################################

type OverloadRegistry = dict[str, dict[str, dict[int, FunctionType]]]

def sys_overload_registry() -> OverloadRegistry:
    return typing._overload_registry  # type: ignore

def get_overload_registry(c: OverloadContext) -> OverloadRegistry:
    if type(c) is int:
        registries = getattr(typing, REGISTRIES_VAR, None)
        if registries is not None:
            return registries[c]
    return typing._overload_registry  # type: ignore

def new_overload_registry() -> OverloadRegistry:
    return defaultdict(partial(defaultdict, dict))

################################################################################

REGISTRIES_VAR = '_overload_registries_'
OVERLOAD_CONTEXT = '__overload_context__'

################################################################################

if not hasattr(typing, REGISTRIES_VAR):
    setattr(typing, REGISTRIES_VAR, defaultdict(new_overload_registry))
    setattr(typing, 'get_overloads', get_overloads)

overload_dummy: FunctionType
overload_dummy = typing._overload_dummy  # type: ignore
