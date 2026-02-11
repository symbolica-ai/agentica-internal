# ruff: noqa
# fmt: off
import warnings

import pytest

from agentica_internal.testing.warpc.cfunc_sig_tests import verify_cfunc_sigs
from agentica_internal.testing.warpc.virtual_library_tests import *


@pytest.mark.asyncio
async def test_cfunc_sigs():
    await verify_cfunc_sigs()


@pytest.mark.asyncio
async def test_warp_numpy_sum():
    await verify_numpy_sum()


@pytest.mark.asyncio
async def test_warp_numpy_ndarray_behavior():
    await verify_numpy_ndarray_behavior()


@pytest.mark.asyncio
async def test_warp_virtual_numpy():
    await verify_virtual_numpy()


@pytest.mark.asyncio
async def test_warp_virtual_scipy():
    await verify_virtual_scipy()


@pytest.mark.asyncio
async def test_warp_virtual_sqlite3():
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=DeprecationWarning)
        await verify_virtual_sqlite3()


@pytest.mark.asyncio
async def test_warp_virtual_sympy():
    await verify_virtual_sympy()


@pytest.mark.asyncio
async def test_warp_virtual_skimage():
    await verify_virtual_skimage()


@pytest.mark.asyncio
async def test_warp_virtual_pandas():
    await verify_virtual_pandas()


@pytest.mark.asyncio
async def test_warp_virtual_pydantic():
    await verify_virtual_pydantic()
