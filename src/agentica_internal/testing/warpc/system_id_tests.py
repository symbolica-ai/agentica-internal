from agentica_internal.cpython.ids import (
    SYS_CLASS_ID_DICT,
    SYS_FUNCTION_ID_DICT,
    SYS_OBJECT_ID_DICT,
)
from agentica_internal.warpc.system import (
    CLS_OFFSET,
    FUN_OFFSET,
    OBJ_OFFSET,
    SRID_TO_CLS,
    SRID_TO_FUN,
    SRID_TO_OBJ,
)

SKIPPED_PREFIXES = ('CT_', 'SQL_')


def verify_system_class_ids():
    not_found = []
    for cls_name, cls_id in SYS_CLASS_ID_DICT.items():
        srid = cls_id + CLS_OFFSET
        if srid not in SRID_TO_CLS:
            if cls_name.startswith(SKIPPED_PREFIXES):
                continue
            not_found.append(cls_name)
    assert len(not_found) == 0, f"system classes not registered: {' '.join(not_found)}"


def verify_system_function_ids():
    not_found = []
    for fun_name, fun_id in SYS_FUNCTION_ID_DICT.items():
        srid = fun_id + FUN_OFFSET
        if srid not in SRID_TO_FUN:
            if fun_name.startswith(SKIPPED_PREFIXES):
                continue
            not_found.append(fun_name)
    assert len(not_found) == 0, f"system functions not registered: {' '.join(not_found)}"


RENAMED = {'IN__is_coroutine_mark'}


def verify_system_object_ids():
    for obj_name, obj_id in SYS_OBJECT_ID_DICT.items():
        srid = obj_id + OBJ_OFFSET
        if obj_name in RENAMED:
            continue
        assert srid in SRID_TO_OBJ, f"system object {obj_name} not registered"


def verify_system_tables_disjoint():
    funs = set(map(id, SRID_TO_FUN.values()))
    clss = set(map(id, SRID_TO_CLS.values()))
    objs = set(map(id, SRID_TO_OBJ.values()))
    assert funs.isdisjoint(clss), f"classes and funtions not disjoint"
    assert objs.isdisjoint(clss), f"classes and objects not disjoint"
    assert funs.isdisjoint(objs), f"functions and objects not disjoint"


if __name__ == '__main__':
    verify_system_class_ids()
    verify_system_function_ids()
    verify_system_object_ids()
    verify_system_tables_disjoint()
