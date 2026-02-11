# fmt: off

import asyncio
import re

from agentica_internal.warpc.worlds.debug_world import *


async def verify_virtual_queue():

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        queue = asyncio.Queue()
        queue_b = await B(queue)
        assert queue_b is not queue

        assert is_virtual(queue_b)
        queue_a = await A(queue_b)
        assert queue_a is queue

        assert type(queue_b).__name__ == 'Queue'
        assert type(queue_b) is not type(queue)

        assert queue.qsize() == 0
        assert queue_b.qsize() == 0
        queue_b.put_nowait(55)

        assert queue.qsize() == 1
        assert queue_b.qsize() == 1

        assert queue.get_nowait() == 55


async def verify_regex_patt():

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        patt = re.compile('.')
        patt_b = await B(patt)
        assert patt_b is not patt
        assert is_real(type(patt_b)) and is_real(patt_b)
        assert type(patt_b) is type(patt)

        patt_a = await A(patt_b)
        assert patt_a is patt_b

        assert patt_a == patt_b


async def verify_regex_match():

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        patt = re.compile('A+')
        match = patt.search(' AAA ')
        match_b = await B(match)
        assert match_b is not match
        assert is_real(type(match_b)) and is_real(match_b)
        assert type(match_b) is type(match)

        match_a = await A(match_b)
        assert repr(match_a) == repr(match_b)


if __name__ == '__main__':
    asyncio.run(verify_virtual_queue())
    asyncio.run(verify_regex_patt())
    asyncio.run(verify_regex_match())
