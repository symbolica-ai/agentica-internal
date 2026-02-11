# ruff: noqa
# fmt: off

import pytest
from agentica_internal.testing.warpc.iterator_tests import *


@pytest.mark.asyncio
@pytest.mark.parametrize('iterator_fn', ITERATOR_FNS)
async def test_warp_iterator(iterator_fn):
    await verify_iterator_content(iterator_fn)


@pytest.mark.asyncio
async def test_warp_re_finditer():
    await verify_re_finditer()



@pytest.mark.asyncio
async def test_warp_iterator_reduce():
    await verify_iterator_reduce()
