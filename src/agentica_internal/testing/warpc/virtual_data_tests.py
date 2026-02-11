# fmt: off

import asyncio

from agentica_internal.warpc.worlds.debug_world import *


async def verify_plain_old_data():

    import datetime as DT
    import ipaddress as IP
    import urllib.parse as UP

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair as B:

        async def assert_equal(a):
            b = await B(a)
            assert is_real(b), f"not is_real(b)"
            assert type(a) is type(b), f"{type(a)=}  is not  {type(b)=}"
            assert a is b, f"a is not b"

        async def assert_equivalent(a):
            b = await B(a)
            assert is_real(b), f"not is_real(b); {type(b)=}"
            assert type(a) is type(b), f"{type(a)=}  is not  {type(b)=}"
            assert a is not b, f"a is b"
            assert a == b, f"a != b"

        await assert_equal(True)
        await assert_equal(False)
        await assert_equal(None)

        await assert_equivalent(12345)
        await assert_equivalent(1.234)

        await assert_equal(())
        await assert_equivalent((1, 2, 3))

        await assert_equivalent([])
        await assert_equivalent([1, 2, 3])

        await assert_equivalent(set())
        await assert_equivalent({1, 2, 3})

        await assert_equal('')
        await assert_equivalent('string')

        await assert_equal(b'')
        await assert_equivalent(b'bytes')

        await assert_equivalent(DT.date(2023, 12, 25))
        await assert_equivalent(DT.time(14, 30, 45))
        await assert_equivalent(DT.timedelta(days=7, hours=3))
        await assert_equivalent(DT.datetime(2023, 12, 25, 14, 30, 45))

        await assert_equivalent(IP.IPv4Address('192.168.1.1'))
        await assert_equivalent(IP.IPv6Address('::1'))
        await assert_equivalent(UP.urlparse('https://example.com/path?q=value'))

        await assert_equivalent((True, False, 5.3, [], 'string', b'bytes'))


if __name__ == '__main__':
    asyncio.run(verify_plain_old_data())
