# fmt: off

import asyncio
from collections.abc import Iterable
from itertools import islice

from agentica_internal.core.print import hprint
from agentica_internal.testing.examples import ITERATOR_FNS
from agentica_internal.warpc.flags import with_flags
from agentica_internal.warpc.worlds.debug_world import DebugWorld


def realize(it) -> list:
    return list(islice(it, 32))


async def verify_iterator_content(iter_fn):

    # verify the *content* of iterators
    pair = DebugWorld.connected_pair(logging=False)
    async with pair as B:
        content_a = realize(iter_fn())

        iter_obj = iter_fn()
        iter_obj_b = await B(iter_obj)
        content_b = realize(iter_obj_b)

        assert content_a == content_b, f"Content not equal: {content_a} != {content_b}"

    return pair


async def verify_iterators():

    for iter_fn in ITERATOR_FNS:
        hprint(iter_fn())
        await verify_iterator_content(iter_fn)

    for iter_fn in ITERATOR_FNS:
        hprint(iter_fn())
        await verify_iterator_content(iter_fn)


async def verify_re_finditer():
    import re

    # verify the *content* of iterators
    pair = DebugWorld.connected_pair(logging=False)
    async with pair as B:

        patt = re.compile(" X+ ")
        iter_fn = lambda: patt.finditer(" X XX XXX ")

        list_a = list(iter_fn())
        iter_b = await B(iter_fn())
        assert isinstance(iter_b, Iterable)

        list_b = list(iter_b)
        assert isinstance(list_b[0], re.Match)
        assert repr(list_a) == repr(list_b)

    return pair


async def verify_iterator_reduce():
    from agentica_internal.warpc.resource.vbuiltins._iterator import _iterator

    # verify the *content* of iterators
    pair = DebugWorld.connected_pair(logging=False)
    async with pair as B:

        elms = 'abcde'

        for limit in [-1, 100]:

            i = -1
            def fn():
                nonlocal i
                i += 1
                return elms[i] if i < len(elms) else 'f'

            reducible_iter_objs = [
                iter(map(str.lower, elms)),
                iter(list(elms)),
                iter(tuple(elms)),
                iter(str(elms)),
                iter(fn, 'f'),
            ]

            with with_flags(REALIZE_ITERATOR_LIMIT=limit):
                for iter_obj in reducible_iter_objs:
                    type_a = type(iter_obj)
                    iter_obj_b = await B(iter_obj)
                    type_b = type(iter_obj_b)
                    expected = (type_a, _iterator,) if limit == -1 else (type_a,)
                    assert type_b in expected, f"{type_a} != {expected}"
                    elms_b = ''.join(iter_obj_b)
                    assert elms_b == elms, f"{elms_b!r} != {elms!r}"


if __name__ == '__main__':
    asyncio.run(verify_iterators())
    asyncio.run(verify_re_finditer())
    asyncio.run(verify_iterator_reduce())
