# ruff: noqa
# fmt: off

import pytest

from agentica_internal.testing.warpc.virtual_c_derived_tests import *


def test_warp_choose_system_base():
    verify_choose_system_base()


@pytest.mark.asyncio
async def test_warp_named_tuple():
    await verify_named_tuple()


@pytest.mark.asyncio
async def test_warp_list_derived():
    await verify_list_derived()


@pytest.mark.asyncio
async def test_warp_dict_derived():
    await verify_dict_derived()


@pytest.mark.asyncio
async def test_warp_set_derived():
    await verify_set_derived()
