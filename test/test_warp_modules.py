# ruff: noqa
# fmt: off

import pytest
from agentica_internal.testing.warpc.virtual_module_tests import *


@pytest.mark.asyncio
async def test_virtual_module():
    await verify_virtual_module()


@pytest.mark.asyncio
async def test_virtual_module_laziness():
    await verify_virtual_module_laziness()

@pytest.mark.asyncio
async def test_numpy_dispatch():
    await verify_numpy_dispatch()


@pytest.mark.asyncio
async def test_numpy_module():
    await verify_numpy_module()
