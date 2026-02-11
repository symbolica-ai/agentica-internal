# fmt: off

import asyncio
from collections import Counter, OrderedDict

from agentica_internal.warpc.worlds.debug_world import DebugWorld


class sub_object(object):
    def name(self):
        return 'sub_object'


class sub_list(list):
    def name(self):
        return 'sub_list'


class sub_dict(dict):
    def name(self):
        return 'sub_dict'


class sub_set(set):
    def name(self):
        return 'sub_set'


class sub_Counter(Counter):
    def name(self):
        return 'sub_Counter'


class sub_OrderedDict(OrderedDict):
    def name(self):
        return 'sub_OrderedDict'


SUB_CLASSES = [
    sub_object,
    sub_list,
    sub_dict,
    sub_set,
    sub_Counter,
    sub_OrderedDict,
]

COLL_CLASSES = [
    Counter,
    OrderedDict,
]

type_get = type.__getattribute__


async def verify_sub_class_can_instantiate(cls: type):

    pair = DebugWorld.connected_pair(logging=False)

    async with pair:

        A, B = pair.pipes

        cls_a = cls
        sup_a = cls.__bases__[0]
        cls_b = await B(cls_a)
        obj_a = cls_a()

        obj_b = await B(obj_a)
        assert obj_b.name() == obj_a.name()

        obj_b = cls_b()
        obj_b_cls = type(obj_b)
        assert obj_b_cls is not cls_a, f"{obj_b_cls} is {cls_a}"
        assert issubclass(obj_b_cls, sup_a), f"{obj_b_cls} is not subclass of {cls_a}"
        assert obj_b_cls is cls_b, f"{obj_b_cls} is not {cls_b}"

        obj_a = await A(obj_b)
        assert type(obj_a) is cls_a
        assert type(obj_a) is not cls_b

    return pair


async def verify_coll_class_can_instantiate(cls: type):

    pair = DebugWorld.connected_pair(logging=False)

    async with pair:

        A, B = pair.pipes

        cls_a = cls
        cls_b = await B(cls_a)
        obj_a = cls_a()

        obj_b = cls_b()
        obj_b_cls = type(obj_b)
        assert obj_b_cls is cls_a, f"{obj_b_cls} is not {cls_a}"

        obj_a2 = await A(obj_b)
        obj_a2_cls = type(obj_a2)
        assert obj_a2_cls is cls_a, f"{obj_b_cls} is not {cls_a}"
        assert obj_a == obj_a2

    return pair



def collect_collection_events():
    ...


async def verify_classes_can_instantiate():
    for cls in SUB_CLASSES:
        await verify_sub_class_can_instantiate(cls)
    for cls in COLL_CLASSES:
        await verify_coll_class_can_instantiate(cls)


if __name__ == '__main__':
    asyncio.run(verify_classes_can_instantiate())
