# fmt: off

import asyncio

import numpy
from agentica_internal.core.log import set_log_tags
from agentica_internal.warpc.worlds.debug_world import *


async def verify_numpy_module():

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


async def verify_numpy_ndarray():

    pair = DebugWorld.connected_pair(qualify_names=False)
    async with pair:

        A, B = pair.pipes

        array_a = numpy.ndarray(shape=(2, 2), dtype=float)
        array_b = await B(array_a)

        sum_o = array_a.sum()
        sum_b = array_b.sum()
        sum_a = await A(sum_b)

        assert str(sum_o) == '0.0'
        assert str(sum_b) == '0.0'
        set_log_tags(False)
        assert is_virtual(sum_b)
        assert is_real(sum_a)
        assert is_real(type(sum_a))
        assert type(sum_a) is type(sum_o)
        assert sum_a == sum_o




if __name__ == '__main__':
    asyncio.run(verify_numpy_module())
    asyncio.run(verify_numpy_ndarray())
