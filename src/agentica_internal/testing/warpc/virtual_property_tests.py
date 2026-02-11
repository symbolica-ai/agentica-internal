# fmt: off

import asyncio

from agentica_internal.warpc.worlds.debug_world import *


def try_get(obj: object, name: str) -> object:
    try:
        return getattr(obj, name)
    except Exception as e:
        return type(e)


def try_set(obj: object, name: str, value: object) -> object:
    try:
        return setattr(obj, name, value)
    except Exception as e:
        return type(e)


def try_del(obj: object, name: str) -> object:
    try:
        return delattr(obj, name)
    except Exception as e:
        return type(e)


async def verify_virtual_getter():

    class ClassWithGetter:

        @property
        def integer(self) -> int: return 9

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        obj = ClassWithGetter()
        obj_b = await B(obj)
        cls_b = type(obj_b)

        # verify names look right
        assert cls_b.integer.__module__ == __name__
        assert cls_b.integer.__name__ == 'integer'
        assert cls_b.integer.__qualname__ == 'verify_virtual_getter.<locals>.ClassWithGetter.integer'
        assert cls_b.integer.fget.__name__ == 'integer'

        # verify getting works
        assert try_get(obj_b, 'integer') == 9

        # verify that we cannot set
        assert try_set(obj_b, 'integer', 0) is AttributeError

        # verify that we cannot delete
        assert try_del(obj_b, 'integer') is AttributeError



async def verify_virtual_getter_setter():

    class ClassWithGetterSetter:

        def __init__(self):
            self.value = 9

        @property
        def integer(self) -> int:
            return -self.value

        @integer.setter
        def integer(self, value: int):
            self.value = value

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        obj = ClassWithGetterSetter()
        obj_b = await B(obj)
        cls_b = type(obj_b)

        # verify getting works
        assert isinstance(cls_b.integer, property)
        assert try_get(obj_b, 'integer') == -9

        # verify setting works
        assert try_set(obj_b, 'integer', 2) is None
        assert try_get(obj_b, 'integer') == -2

        # verify that we cannot delete
        assert try_del(obj_b, 'integer') is AttributeError


async def verify_virtual_deleter():

    class ClassWithDeleter:

        def __init__(self):
            self.value = 9

        @property
        def integer(self) -> int:
            return self.value

        @integer.deleter
        def integer(self):
            self.value = 0

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        obj = ClassWithDeleter()
        obj_b = await B(obj)
        cls_b = type(obj_b)

        # verify getting works
        assert isinstance(cls_b.integer, property)
        assert try_get(obj_b, 'integer') == 9

        # verify setting does not work
        assert try_set(obj_b, 'integer', 2) is AttributeError

        # verify that we can delete
        assert try_del(obj_b, 'integer') is None
        assert try_get(obj_b, 'integer') == 0


async def verify_virtual_prop_inheritance():

    class ClassWithGetter:

        def __init__(self):
            self.value = 9

        @property
        def integer(self) -> int:
            return self.value


    class SubClassWithGetter(ClassWithGetter):

        @property
        def neg_integer(self) -> int:
            return -self.value

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        obj = SubClassWithGetter()
        obj_b = await B(obj)
        cls_b = type(obj_b)

        # verify getting works
        assert isinstance(cls_b.integer, property)
        assert isinstance(cls_b.neg_integer, property)
        assert try_get(obj_b, 'integer') == 9
        assert try_get(obj_b, 'neg_integer') == -9


async def verify_virtual_slots():

    class ClassWithSlots:
        __slots__ = 'integer',

        def __init__(self):
            self.integer = 0

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:
        A, B = pair.pipes

        obj = ClassWithSlots()
        obj_b = await B(obj)
        cls_b = type(obj_b)

        # verify getting works
        assert isinstance(cls_b.integer, property)
        assert try_get(obj_b, 'integer') == 0

        # verify setting works
        assert try_set(obj_b, 'integer', 9) is None
        assert try_get(obj_b, 'integer') == 9


if __name__ == '__main__':
    asyncio.run(verify_virtual_getter())
    asyncio.run(verify_virtual_getter_setter())
    asyncio.run(verify_virtual_deleter())
    asyncio.run(verify_virtual_prop_inheritance())
    asyncio.run(verify_virtual_slots())
