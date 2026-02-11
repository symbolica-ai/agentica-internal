# ruff: noqa
# fmt: off

import pytest

from agentica_internal.testing.warpc.virtual_function_tests import (
    FUNCTIONS, LAMBDAS,
    verify_virtual_func_checks,
    verify_virtual_signature,
    verify_func_defaults_filtering
)


@pytest.mark.asyncio
@pytest.mark.parametrize('func', FUNCTIONS + LAMBDAS)
async def test_warp_func_argument_handling(func):
    await verify_virtual_func_checks(func)

@pytest.mark.asyncio
@pytest.mark.parametrize('func', FUNCTIONS)
async def test_warp_func_signature(func):
    await verify_virtual_signature(func)

@pytest.mark.asyncio
async def test_warp_func_defaults_filtering():
    await verify_func_defaults_filtering()
