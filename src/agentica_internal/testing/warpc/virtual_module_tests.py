# fmt: off

import asyncio
from agentica_internal.core.sentinels import FIELD_ABSENT

from agentica_internal.testing import *
from agentica_internal.warpc.worlds.debug_world import *
from agentica_internal.testing.warpc import my_module

async def verify_virtual_module():

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        o_mod = my_module
        b_mod = await B(o_mod)
        a_mod = await A(b_mod)

        assert is_virtual(b_mod)
        assert is_real(a_mod)
        assert a_mod is o_mod

        assert b_mod.__all__ == o_mod.__all__
        assert b_mod.__name__ == o_mod.__name__
        assert b_mod.__doc__ == o_mod.__doc__

        o_class = a_mod.MyClass
        m_class = b_mod.MyClass
        b_class = await B(o_class)
        assert m_class is b_class

        assert getattr(b_mod, 'non_existent', None) is None


async def verify_virtual_module_laziness():

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        o_mod = my_module
        b_mod = await B(o_mod)

        o_dict = o_mod.__dict__
        b_dict = b_mod.__dict__

        assert 'my_function' in o_dict

        # test that expensive resources are sent lazily
        assert 'MyClass' not in b_dict

        assert 'MY_CONSTANT' in b_dict
        assert 'my_function' not in b_dict
        assert 'MY_BYTES' not in b_dict

        # test that once getattr goes through, it is cached in dict
        b_mod.my_function()
        assert 'my_function' in b_dict

        del o_mod.my_function
        b_mod.my_function()  # check it's still there

        # test bulk getting of attrs works
        res = b_mod.__getattrs__(('missing', 'MY_CONSTANT', 'MY_BYTES'))
        assert res[0] is FIELD_ABSENT
        assert res[1] == 99
        assert type(res[2]) is bytes

        assert 'missing' not in b_dict
        assert 'MY_BYTES' in b_dict

        # test for caching



async def verify_numpy_dispatch():

    from numpy import savez
    # this is an _ArrayFunctionDispatcher object, implemented in C,
    # whose _ArrayFunctionDispatcher.__call__ is method-wrapper, and was
    # a major obstacle

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        o_fn = savez
        b_fn = await B(o_fn)
        a_fn = await A(b_fn)

        assert is_virtual(b_fn)
        assert callable(b_fn)
        assert is_real(a_fn)

        assert callable(b_fn)


async def verify_numpy_module():

    try:
        import numpy
    except ImportError:
        print("numpy not available, skipping test")
        return

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        o_mod = numpy
        b_mod = await B(o_mod)
        a_mod = await A(b_mod)

        assert is_virtual(b_mod)
        assert is_real(a_mod)
        assert a_mod is o_mod

        assert b_mod.__all__ == o_mod.__all__
        assert b_mod.__name__ == o_mod.__name__
        assert b_mod.__doc__ == o_mod.__doc__


if __name__ == '__main__':
    asyncio.run(verify_virtual_module())
    asyncio.run(verify_virtual_module_laziness())
    asyncio.run(verify_numpy_dispatch())
    asyncio.run(verify_numpy_module())
