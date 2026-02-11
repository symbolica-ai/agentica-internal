import pytest

from agentica_internal.testing.warpc.virtual_property_tests import *

@pytest.mark.asyncio
async def test_virtual_getter():
    await verify_virtual_getter()

@pytest.mark.asyncio
async def test_virtual_getter_setter():
    await verify_virtual_getter_setter()

@pytest.mark.asyncio
async def test_virtual_deleter():
    await verify_virtual_deleter()

@pytest.mark.asyncio
async def test_virtual_prop_inheritance():
    await verify_virtual_prop_inheritance()

@pytest.mark.asyncio
async def test_virtual_slots():
    await verify_virtual_slots()
