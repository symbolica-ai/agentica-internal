# fmt: off

import asyncio
import tempfile
from collections.abc import Callable
from types import ModuleType
from pathlib import Path
from agentica_internal.core import print as P
from agentica_internal.core.log import ScopedLogging
from agentica_internal.cpython.function import func_location

from agentica_internal.warpc.worlds.debug_world import *



async def verify_numpy_sum():

    import numpy

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair as B:
        A, B = pair.pipes

        numpy_b = await B(numpy)
        array_b = numpy_b.ndarray([1, 2, 3])
        array_a = await A(array_b)
        sum_o = array_a.sum()
        sum_b = array_b.sum()
        sum_a = await A(sum_b)
        assert sum_a == sum_o


async def verify_numpy_scalars():

    from numpy import int64

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair as B:
        A, B = pair.pipes

        int64_b = await B(int64)
        i_o = int64(1)
        i_b = await B(i_o)
        j_b = int64_b(1)

        assert i_b == j_b
        assert str(i_b) == str(i_o)
        assert hash(i_o) == hash(i_b)
        assert hash(i_o) == hash(i_b)

        k_o = i_o + i_o
        k_b = i_b + i_b
        k_a = await A(k_b)
        assert k_o == k_a

        assert str(k_a) == str(k_b)
        assert hash(k_a) == hash(k_b)


async def verify_numpy_array_call():

    # the individual tests were Opus 4.5 generated, but human
    # vetted against the real numpy first

    import numpy

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:

        A, B = pair.pipes

        array_o = numpy.array
        array_b = await B(array_o)

        array_in_b = array_b([1, 2, 3], dtype='int32')
        array_in_a = await A(array_in_b)
        array_in_o = array_o([1, 2, 3])

        assert str(array_in_o) == str(array_in_b)


async def verify_numpy_ndarray_behavior():

    # the individual tests were Opus 4.5 generated, but human
    # vetted against the real numpy first

    from numpy import zeros

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:

        A, B = pair.pipes

        array_a = zeros(shape=(2, 2), dtype=float)
        array_b = await B(array_a)

        sum_o = array_a.sum()
        sum_b = array_b.sum()
        assert is_virtual(sum_b)

        sum_a = await A(sum_b)

        assert sum_a == sum_o
        assert sum_b == 0.0
        assert sum_b <= 5
        assert sum_b != 1.0

        assert str(sum_o) == '0.0'
        assert str(sum_b) == '0.0'


async def verify_virtual_module(*args: ModuleType | Path, tests: list[Callable], logging=False):

    # first test the functionality in the original args
    # for i, fn in enumerate(tests):
    #     try:
    #         fn(*args)
    #     except Exception as e:
    #         e.add_note(f"error in non-warped test #{i}: {fn.__name__!r}")
    #         e.add_note(func_location(fn))
    #         raise

    pair = DebugWorld.connected_pair(logging=logging, qualify_names=False)
    async with pair as B:
        args_b = []
        for m in args:
            args_b.append(await B(m))

        # next test the functionality in the warped args
        for i, fn in enumerate(tests):
            try:
                fn(*args_b)
                continue
            except Exception as e:
                print(f'\nERROR in warped test #{i}: {fn.__name__!r}:\n{e!r}')
                P.print_exception(e)
                print(func_location(fn))

            if not logging:

                try:
                    with ScopedLogging(True):
                        fn(*args_b)
                except Exception as e:
                    e.add_note(f"error in warped test #{i}: {fn.__name__!r}")
                    raise


async def verify_virtual_numpy():
    import numpy
    from agentica_internal.testing.library_tests.numpy_tests import NUMPY_UNIT_TESTS
    await verify_virtual_module(numpy, tests=NUMPY_UNIT_TESTS)


async def verify_virtual_sqlite3():
    import sqlite3
    from agentica_internal.testing.library_tests.sqlite3_tests import SQLITE3_UNIT_TESTS
    await verify_virtual_module(sqlite3, tests=SQLITE3_UNIT_TESTS)


async def verify_virtual_sympy():
    import sympy
    from agentica_internal.testing.library_tests.sympy_tests import SYMPY_UNIT_TESTS
    await verify_virtual_module(sympy, tests=SYMPY_UNIT_TESTS, logging=False)


async def verify_virtual_scipy():
    import numpy
    import scipy
    from agentica_internal.testing.library_tests.scipy_tests import SCIPY_UNIT_TESTS
    await verify_virtual_module(numpy, scipy, tests=SCIPY_UNIT_TESTS, logging=False)


async def verify_virtual_skimage():
    import numpy
    import skimage
    from agentica_internal.testing.library_tests.skimage_tests import SKIMAGE_UNIT_TESTS
    await verify_virtual_module(numpy, skimage, tests=SKIMAGE_UNIT_TESTS)


async def verify_virtual_pandas():
    import numpy
    import pandas
    import pathlib
    from agentica_internal.testing.library_tests.pandas_tests import PANDAS_UNIT_TESTS
    with tempfile.TemporaryDirectory(prefix='pandas') as tmp_dir:
        tmp_dir = pathlib.Path(tmp_dir)
        await verify_virtual_module(numpy, pandas, tmp_dir, tests=PANDAS_UNIT_TESTS)


async def verify_pydantic_exception():

    from pydantic import ValidationError

    exc_o = ValidationError.from_exception_data('foo', [], 'python', False)
    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair as B:
        exc_b = await B(exc_o)
        repr_a = str(exc_o)
        repr_b = str(exc_b)
        assert repr_a == repr_b, f"{repr_a} != {repr_b}"


async def verify_virtual_pydantic():
    # we don't virtualize pydantic itself, only the models, since agents
    # can't and don't need to define their own models (yet)
    from agentica_internal.testing.library_tests.pydantic_tests import PYDANTIC_UNIT_TESTS, load_models
    PYDANTIC_MODELS = load_models()
    await verify_virtual_module(PYDANTIC_MODELS, tests=PYDANTIC_UNIT_TESTS, logging=False)


if __name__ == '__main__':
    asyncio.run(verify_numpy_array_call())
    asyncio.run(verify_numpy_sum())
    asyncio.run(verify_numpy_ndarray_behavior())
    asyncio.run(verify_numpy_scalars())
    asyncio.run(verify_virtual_numpy())
    asyncio.run(verify_virtual_scipy())
    asyncio.run(verify_virtual_sqlite3())
    asyncio.run(verify_virtual_sympy())
    asyncio.run(verify_virtual_skimage())
    asyncio.run(verify_virtual_pandas())
    asyncio.run(verify_pydantic_exception())
    asyncio.run(verify_virtual_pydantic())
