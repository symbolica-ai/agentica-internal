# fmt: off

import asyncio

from agentica_internal.warpc.worlds.debug_world import *

async def verify_libc():

    import ctypes

    # Load the C standard library
    libc = ctypes.CDLL("libc.dylib")

    # Set up the function signature
    libc.strlen.argtypes = [ctypes.c_char_p]
    libc.strlen.restype = ctypes.c_size_t

    # Call it
    string = b"hello"
    length = len(string)

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair as B:
        A, B = pair.pipes

        strlen_o = libc.strlen
        strlen_b = await B(strlen_o)
        assert is_virtual(strlen_b)
        assert strlen_b(string) == length

        strlen_a = await A(strlen_b)
        assert strlen_a is strlen_o


if __name__ == '__main__':
    asyncio.run(verify_libc())
