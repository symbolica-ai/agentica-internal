# fmt: off

from types import FunctionType
from typing import overload

from agentica_internal.testing.decorators import runs, invalid, get_module_functions, get_function_checks

__all__ = [
    "fn_nullary",
    "fn_unary",
    "fn_binary",
    "fn_unary_1_def",
    "fn_binary_1_def",
    "fn_binary_2_def",
    "fn_with_args",
    "fn_with_kwargs",
    "fn_with_args_kwargs",
    "fn_blank",
    "fn_pos_only",
    "fn_kw_only",
    "fn_pos_and_kw_only",
    "fn_overloaded",
    "fn_complex",
    "fn_async",
    "fn_async_gen",

    "FUNCTIONS",
]

type MyType = dict[str, object] | None

@invalid(1)
@runs()
def fn_nullary():
    return {}

@invalid()
@invalid(1, 2)
@invalid(a3=5)
@runs(1)
@runs(a1=1)
def fn_unary(a1):
    return {'a1': a1}

@invalid()
@invalid(1)
@invalid(1, 2, 3)
@runs(1, 2)
@runs(a1=1, a2=2)
def fn_binary(a1, a2):
    return {'a1': a1, 'a2': a2}

@invalid(a2=5)
@runs()
@runs(5)
@runs(a1=5)
def fn_unary_1_def(a1=0):
    return {'a1': a1}

@invalid()
@invalid(a2=True)
@runs(1)
@runs(1, False)
@runs(a1=1, a2=False)
@runs(a2=False, a1=1)
def fn_binary_1_def(a1, a2=True):
    return {'a1': a1, 'a2': a2}

@runs(1)
@runs(1, False)
@runs(1, a2=False)
@runs(a1=1)
@runs(a2=False)
@runs(a1=1, a2=False)
@runs(a2=False, a1=1)
def fn_binary_2_def(a1=0, a2=True):
    return {'a1': a1, 'a2': a2}

@runs(1)
def fn_with_ret_type(a1) -> MyType:
    return {'a1': a1}

@invalid()
@invalid(1, a2=5)
@runs(1)
@runs(1, 'a')
@runs(1, 'a', 'b')
@runs(a1=5)
def fn_with_args(a1: int, *args: str) -> dict:
    return {'a1': a1, 'args': args}

@invalid(1, k1=True)
@invalid(1, k1=True, k2='c', k3='d')
@runs(1, k1=True, k2='c')
@runs(1, 'a', 'b', k1=True, k2='c')
def fn_with_args_and_kw_only(a1: int, *args: str, k1: bool, k2: str) -> dict:
    return {'a1': a1, 'k1': k1, 'k2': k2, 'args': args}

@invalid()
@invalid(a2=1)
@runs(1)
@runs(1, x=1)
@runs(1, x=1, y=2)
@runs(a1=1)
@runs(x=1, a1=1)
@runs(x=1, a1=1, a2=2)
def fn_with_kwargs(a1: int, **kwargs: int) -> dict:
    return {'a1': a1, 'kwargs': kwargs}

@runs(1)
@runs(1, 2)
@runs(1, x='a')
@runs(1, 2, x='a')
@runs(1, 2, 3, x='a', y='b')
def fn_with_args_kwargs(a1: int, *args: int, **kwargs: str) -> dict:
    return {'a1': a1, 'args': args, 'kwargs': kwargs}

@invalid(p1=1, a2=True, a3='a')
@runs(1, True, 'a')
@runs(1, a2=True, a3='a')
def fn_pos_only(p1: int, /, a2: bool, a3: str) -> dict:
    return {'p1': p1, 'a2': a2, 'a3': a3}

@invalid(1, 'a', True)
@runs(1, k2=True, k3='a')
@runs(1, k3='a', k2=True)
@runs(k2=True, k3='a', a1='a')
def fn_kw_only(a1: int, *, k2: bool, k3: str) -> dict:
    return {'a1': a1, 'k2': k2, k3: k3}

@runs()
@runs(1, 2)
@runs(x='a', y='b')
@runs(1, 2, x='a', y='b')
def fn_blank(*args, **kwargs) -> dict:
    return {'args': args, 'kwargs': kwargs}

@invalid(1, True, 'a')
@invalid(a2=True, k3='a', a1=1)
@runs(1, a2=True, k3='a')
@runs(1, k3='a', a2=True)
def fn_pos_and_kw_only(p1: int, /, a2: bool, *, k3: str) -> dict:
    return {'p1': p1, 'a2': a2, 'k3': k3}

@overload
def fn_overloaded() -> dict: ...
@overload
def fn_overloaded(a1: bool) -> dict[str, bool]: ...
@overload
def fn_overloaded(a1: bool, a2: int) -> dict[str, int]: ...

@invalid(1, 2, 3)
@runs()
@runs(1)
@runs(1, 2)
def fn_overloaded(*args: int) -> dict[str, int]:
    n = len(args)
    if n == 0: return {}
    if n == 1: return {'a1': args[0]}
    if n == 2: return {'a1': args[0], 'a2': args[1]}
    raise TypeError('0 to 2 arguments expected')

@invalid()
@invalid(1)
@invalid(1, True)
@invalid(p1=1, p2=True, a3='t')
@runs(1, True, 't')
@runs(1, True, a3='t')
@runs(1, True, a3='t', x='a')
@runs(1, True, 'u', 'v', 'w', k4=False, a='a', b='y')
def fn_complex(
    p1: int, p2: bool, /, a3: str, *args: str, k4: bool = True, **kwargs: str
) -> dict:
    return {'p1': p1, 'p2': p2, 'a3': a3, 'k4': k4, 'args': args, 'kwargs': kwargs}


async def fn_async(a1: int):
    return {'a1': a1}

async def fn_async_gen(a1: int):
    yield {'a1': a1}


FUNCTIONS: list[FunctionType] = get_module_functions(__name__)

for fun in FUNCTIONS:
    get_function_checks(fun).apply()
