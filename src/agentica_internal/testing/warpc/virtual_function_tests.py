# fmt: off

import asyncio
from sys import modules
from types import FunctionType
from agentica_internal.cpython.function import func_def_str

from agentica_internal.testing import *
from agentica_internal.testing.examples import FUNCTIONS, LAMBDAS
from agentica_internal.warpc.flags import with_flags
from agentica_internal.warpc.worlds.debug_world import *
from agentica_internal.warpc.data.signature_utils import *


async def verify_virtual_signature(fun: FunctionType) -> None:

    def_str = func_def_str(fun)
    assert def_str is not None, f"cannot find {fun.__name__}"
    sig_1 = sig_of_py_function(fun, 0, ALL_DEFAULTS)
    sig_2 = sig_of_def_str(def_str, 0, ALL_DEFAULTS, modules[fun.__module__].__dict__)
    sig_1.next_over = None
    sig_repr_1 = repr(sig_1)
    sig_repr_2 = repr(sig_2)
    assert sig_repr_1 == sig_repr_2, f"\n{sig_repr_1}\n != \n{sig_repr_2}"


async def verify_func_defaults_filtering():
    from agentica_internal.core.sentinels import ARG_DEFAULT as DEF

    obj = object()
    def func_a(a=0, b='', c=(), d=obj):
        return a, b, c, d

    defs_o = func_a()

    async def verify(flag: str, defs_e: tuple):
        with with_flags(VIRTUAL_FUNCTION_DEFAULTS=flag):
            pair = DebugWorld.connected_pair()
            async with pair:
                A, B = pair.pipes
                func_b = await B(func_a)
                defs_b = func_b.__defaults__
                assert repr(defs_b) == repr(defs_e), f"{defs_b!r} != {defs_e!r} with flag {flag!r}"
                defs_a = await A(func_b())
                assert defs_a == defs_o

    assert (0, obj) == (0, obj)
    await verify('none',    (DEF, DEF, DEF, DEF))
    await verify('atomic',  (0, '', DEF, DEF))
    await verify('compact', (0, '', (), DEF))
    await verify('all',     (0, '', (), obj))


async def verify_virtual_func_checks(fun: FunctionType) -> None:

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair as B:
        checks = get_function_checks(fun)
        fun_b = await B(fun)
        checks.compare(fun_b)


if __name__ == '__main__':
    run_object_tests(verify_virtual_signature, FUNCTIONS, on_error='exit')
    run_object_tests(verify_virtual_func_checks, FUNCTIONS + LAMBDAS, on_error='print')
    asyncio.run(verify_func_defaults_filtering())
