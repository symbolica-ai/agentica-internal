# fmt: off

from typing import *

from agentica_internal.core.type import anno_str
from agentica_internal.testing import *
from agentica_internal.testing.examples import ANNOS, CLASSES
from agentica_internal.testing.examples.annos import TreeAlias
from agentica_internal.testing.examples.classes import ENUM_CLASSES
from agentica_internal.warpc.worlds.debug_world import DebugWorld

SKIP = (
    'VarInt',  # we don't serialize TypeVar bounds yet
)

ANNOS = [a for a in ANNOS if a not in ENUM_CLASSES]
CLASSES = [a for a in CLASSES if a not in ENUM_CLASSES]

async def verify_annotation_equality(anno: Any):

    # verify that either deserialized annotation compares equal to original,
    # or it formats the same (because e.g. buried classes will be different)
    pair = DebugWorld.connected_pair(qualify_names=False)

    async with pair as B:
        if anno is TreeAlias:
            return pair
        anno_a = anno
        anno_b = await B(anno)
        str_a = anno_str(anno_a)
        str_b = anno_str(anno_b)
        obj_equal = anno_a == anno_b
        str_equal = str_a == str_b
        if any(skip in str_a for skip in SKIP):
            return pair
        assert obj_equal or str_equal, f"annotations not equal: {str_a} == {str_b}"

    return pair


async def verify_class_annotation_equality(cls: type):

    # verify that either deserialized annotation compares equal to original,
    # or it formats the same (because e.g. buried classes will be different)
    pair = DebugWorld.connected_pair(qualify_names=False)

    async with pair as B:
        anno_a = cls.__annotations__
        cls_b = await B(cls)
        anno_b = cls_b.__annotations__
        str_a = anno_str(anno_a)
        str_b = anno_str(anno_b)
        obj_equal = anno_a == anno_b
        str_equal = str_a == str_b
        if any(skip in str_a for skip in SKIP):
            return
        assert obj_equal or str_equal, f"class annotations not equal: {str_a} == {str_b}"

    return pair


def verify_normalizing_unions():
    # verify that the weird normalizing behavior of union types don't cause problems

    from types import NoneType

    from agentica_internal.warpc.messages import DefinitionMsg, SystemResourceMsg
    from agentica_internal.warpc.pure import PURE_CODEC
    from agentica_internal.warpc.resources import TypeUnionData

    def encode_decode_union(sys: bool, alts: tuple):
        grid = 9, 9, 9
        union_data = TypeUnionData()
        union_data.alts = alts
        union_data.sys = False
        def_msg = DefinitionMsg(grid, union_data.encode(PURE_CODEC))

        world = DebugWorld(logging=False)
        frame = world.root
        resource = frame.decode_incoming_definition(grid, def_msg)
        assert id(resource) not in frame.remote_lrids
        # ensure no aliasing occurred
        assert isinstance(frame.enc_any(NoneType), SystemResourceMsg)
        assert isinstance(frame.enc_any(int), SystemResourceMsg)
        return resource

    assert encode_decode_union(False, (int, str, str,)) == Union[str, int]
    assert encode_decode_union(False, (int,)) == int
    assert encode_decode_union(False, (NoneType, NoneType,)) is NoneType
    assert encode_decode_union(False, (NoneType,)) is NoneType
    assert encode_decode_union(False, ()) is NoReturn

    assert encode_decode_union(True, (int, str, str,)) == int | str
    assert encode_decode_union(True, (int,)) == int
    assert encode_decode_union(True, (NoneType, NoneType,)) is NoneType
    assert encode_decode_union(True, (NoneType,)) is NoneType
    assert encode_decode_union(True, ()) is NoReturn


if __name__ == '__main__':
    verify_normalizing_unions()
    run_object_tests(verify_annotation_equality, ANNOS, on_error='s')
    run_object_tests(verify_class_annotation_equality, CLASSES, on_error='s')
