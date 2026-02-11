# fmt: off

import asyncio
from typing import Any

from agentica_internal.warpc.worlds.debug_world import *


def try_set(obj: object, name: str, value: object) -> object:
    try:
        return setattr(obj, name, value)
    except Exception as e:
        return type(e)


async def verify_named_tuple():
    from typing import NamedTuple

    class Point(NamedTuple):
        x: int
        y: int
        z: int = 0

    def is_namedtuple(instance):
        return isinstance(instance, tuple) and getattr(instance, "_fields", None)

    def verify_point_instance(p, xyz: tuple):
        dct = {'x': xyz[0], 'y': xyz[1], 'z': xyz[2]}
        assert is_namedtuple(p)
        assert (p.x, p.y, p.z) == xyz
        assert tuple(iter(p)) == xyz
        assert p._asdict() == dct

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:

        A, B = pair.pipes

        Point_o = Point

        Point_b = await B(Point_o)
        assert is_virtual(Point_b)

        Point_a = await A(Point_b)
        assert Point_a is Point_o

        point_o = Point_o(1, 2)
        assert tuple(iter(point_o)) == (1, 2, 0)

        point_b = Point_b(1, 2)
        assert is_virtual(point_b)
        assert type(point_b) is Point_b

        point_a = await A(point_b)
        assert is_real(point_a)
        assert type(point_a) is Point_a

        assert repr(point_a) == repr(point_b)
        verify_point_instance(point_b, (1, 2, 0))

        point_b = Point_b(1, 2, 3)
        verify_point_instance(point_b, (1, 2, 3))

        point_b = point_b._replace(z=9)
        verify_point_instance(point_b, (1, 2, 9))

        assert try_set(point_b, 'x', 99) is AttributeError


def check_container_data(virt: Any, base: type, data: Any):
    assert len(virt) == len(data)
    assert isinstance(virt, base)

    if base is dict:
        for key, val in data.items():
            assert key in virt, f"{key} not in virt"
            assert virt[key] == val, f"{virt[key]=} != {val}"
    elif base is set:
        # unfortunately, set(my_set) does not trigger iter, so
        # we end up with an empty set!
        v_set = set(iter(virt))
        d_set = set(data)
        assert v_set == d_set, f"{v_set} != {d_set}"
    else:
        for i, elem in enumerate(data):
            assert virt[i] == elem

    assert virt == base(data)


async def verify_list_derived():

    class MyList(list):
        pass

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:

        A, B = pair.pipes

        elems = 1, 2, 3

        my_list_o = MyList(elems)
        my_list_b = await B(my_list_o)
        assert is_virtual(my_list_b)
        my_list_a = await A(my_list_b)
        assert my_list_a is my_list_o

        check_container_data(my_list_b, list, elems)
        assert len(my_list_b) == 3

        assert 1 in my_list_b
        assert 5 not in my_list_b

        my_list_b.append(9)
        assert len(my_list_b) == 4
        assert len(my_list_a) == 4
        assert 9 in my_list_b

        my_list_b.clear()
        assert len(my_list_a) == 0


async def verify_set_derived():

    class MySet(set):
        pass

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:

        A, B = pair.pipes

        elems = 1, 2, 3

        my_set_o = MySet(elems)
        my_set_b = await B(my_set_o)
        assert is_virtual(my_set_b)
        my_set_a = await A(my_set_b)
        assert my_set_a is my_set_o

        check_container_data(my_set_b, set, elems)
        assert len(my_set_b) == 3

        assert 1 in my_set_b
        assert 5 not in my_set_b

        my_set_b.add(9)
        assert len(my_set_b) == 4
        assert len(my_set_a) == 4
        assert 9 in my_set_b

        my_set_b.discard(9)
        assert len(my_set_b) == 3
        assert len(my_set_a) == 3
        assert 9 not in my_set_b

        my_set_b.discard(10)

        my_set_b |= {11, 12}
        assert len(my_set_a) == 5
        assert len(my_set_b) == 5
        assert 11 in my_set_b
        assert 12 in my_set_b

        my_set_b.clear()
        assert len(my_set_a) == 0


async def verify_dict_derived():

    class MyDict(dict):
        pass

    pair = DebugWorld.connected_pair(logging=False, qualify_names=False)
    async with pair:

        A, B = pair.pipes

        items = {'a': 1, 'b': 2, 'c': 3}

        my_dict_o = MyDict(items)
        my_dict_b = await B(my_dict_o)
        assert is_virtual(my_dict_b)
        my_dict_a = await A(my_dict_b)
        assert my_dict_a is my_dict_o

        assert len(my_dict_b) == 3
        keys_a = my_dict_a.keys()
        keys_b = my_dict_b.keys()
        assert type(keys_a) is not type(keys_b)

        assert tuple(my_dict_b.keys()) == tuple(my_dict_a.keys())
        assert tuple(my_dict_b.values()) == tuple(my_dict_a.values())
        assert tuple(my_dict_b.items()) == tuple(my_dict_a.items())

        assert 'd' not in my_dict_b
        assert 'a' in my_dict_b

        assert my_dict_b.get('a') == 1
        assert my_dict_b.get('d') is None
        assert my_dict_b.get('d', 9) == 9

        check_container_data(my_dict_b, dict, items)
        my_dict_b['d'] = 4
        assert 'd' in my_dict_a
        assert my_dict_b['d'] == 4
        assert len(my_dict_b) == 4
        assert len(my_dict_a) == 4

        assert my_dict_b.pop('z', 9) == 9
        assert my_dict_b.pop('a') == 1
        assert len(my_dict_b) == 3
        assert len(my_dict_a) == 3

        my_dict_b.clear()
        assert len(my_dict_a) == 0


def verify_choose_system_base():
    from agentica_internal.warpc.resource.vbuiltins import choose_system_base

    from datetime import date, datetime
    from collections.abc import Iterator
    from agentica_internal.cpython.iters import ITER_TYPES

    def verify(cls: type, e_base: type):
        a_base = choose_system_base((cls,))
        assert a_base is e_base, f"base({cls.__name__}) = {a_base.__name__} != {e_base.__name__}"

    class my_class: pass
    class my_list(list): pass
    class my_int(my_class, int): pass
    class my_frozenset(frozenset): pass
    class my_iterator(map): pass
    class my_abc_iterator(Iterator):
        def __next__(self): ...
    class my_date(date): pass
    class my_datetime(datetime): pass
    class my_exception(Exception): pass
    class my_base_exception(BaseException): pass


    verify(object, object)
    verify(dict, dict)
    verify(list, list)
    verify(tuple, tuple)
    verify(set, set)
    verify(frozenset, frozenset)
    verify(my_frozenset, frozenset)
    verify(my_list, list)
    verify(my_int, int)
    verify(my_iterator, Iterator)
    verify(my_abc_iterator, object)  # important!
    verify(my_date, date)
    verify(my_datetime, datetime)
    verify(RuntimeError, BaseException)
    verify(my_exception, BaseException)
    verify(my_base_exception, BaseException)

    for cls in ITER_TYPES:
        verify(cls, Iterator)


if __name__ == '__main__':
    asyncio.run(verify_named_tuple())
    asyncio.run(verify_list_derived())
    asyncio.run(verify_dict_derived())
    asyncio.run(verify_set_derived())
    verify_choose_system_base()
