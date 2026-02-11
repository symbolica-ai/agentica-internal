# fmt: off

from enum import EnumMeta

from ..cpython.alias import CALLABLES as FUNC_TYPES
from ..cpython.ids import SYS_MOD_TABLE, SYS_CLASS_ID_DICT, SYS_FUNCTION_ID_DICT, SYS_OBJECT_ID_DICT

from .__ import *
from .forbidden import *

__all__ = [
    'SRID_TO_RSRC',
    'LRID_TO_SRID',
    'SRID_TO_NAME',
    'SYS_MODULES',
    'SYS_EXCEPTIONS',
    'SYS_CLASSES',
    'to_system_id',
    'is_sys_exc_class',
    'sanitize_path',
    'FORBIDDEN_IDS',
    'SYSTEM_IDS',
    'SITE_PACKAGES',
]


################################################################################

CLS_OFFSET = 0x00000
OBJ_OFFSET = 0x10000
FUN_OFFSET = 0x20000
MOD_OFFSET = 0x30000
FRB_OFFSET = 0x0FFFF

SYS_MODULES: list[ModuleType] = []
SYS_EXCEPTIONS: list[type[BaseException]] = []
SYS_CLASSES: list[type] = []

FORBIDDEN_IDS: list[int] = []

SKIP_MODULES: list[str] = ['ctypes', 'sqlite3']

SYSTEM_IDS: frozenset[LocalRID]

SITE_PACKAGES: tuple[str]

################################################################################

def _init_tables():
    global SRID_TO_CLS, SRID_TO_OBJ, SRID_TO_FUN, SRID_TO_MOD
    global SRID_TO_NAME, SRID_TO_RSRC, LRID_TO_SRID
    global SYS_MODULES, SYS_EXCEPTIONS
    global FORBIDDEN_IDS, SYSTEM_IDS, SITE_PACKAGES
    from importlib import import_module
    from site import getusersitepackages, getsitepackages


    add_exc = SYS_EXCEPTIONS.append
    cls_items, add_cls = mklist()
    obj_items, add_obj = mklist()
    fun_items, add_fun = mklist()
    mod_items, add_mod = mklist()
    rids, add_rid = mklist()
    sids, add_sid = mklist()
    vals, add_val = mklist()
    nams, add_nam = mklist()

    def add(f, val: Any, sid: int, nam: str):
        f((sid, val))
        if id(val) in rids:
            oid = sid - de_off[f]
            raise RuntimeError(f"DUP SYS ID: {val} 0x{oid:X} {nam}")
        add_rid(id(val))
        add_sid(sid)
        add_val(val)
        add_nam(nam)

    get_cls_id = SYS_CLASS_ID_DICT.get
    get_obj_id = SYS_OBJECT_ID_DICT.get
    get_fun_id = SYS_FUNCTION_ID_DICT.get

    cls_i, obj_i, fun_i, mod_i = CLS_OFFSET, OBJ_OFFSET, FUN_OFFSET, MOD_OFFSET
    de_off = {add_cls: cls_i, add_obj: obj_i, add_fun: fun_i, add_mod: mod_i}
    add(add_obj, None, obj_i + 0, 'None')

    for i, prefix, mod_name in SYS_MOD_TABLE:
        if mod_name in SKIP_MODULES:
            continue
        try:
            mod = import_module(mod_name)
        except Exception as err:
            err.add_note(f'while obtaining IDs for module {mod_name!r}')
            P.print_exception(err)
            continue
        add(add_mod, mod, mod_i + i, mod_name)
        for name, thing in vars(mod).items():
            if isinstance(thing, type):
                j = get_cls_id(f'{prefix}_{name}')
                if j is None:
                    continue
                SYS_CLASSES.append(thing)
                add(add_cls, thing, cls_i + j, f'{mod_name}.{name}')
                if issubclass(thing, BaseException):
                    add_exc(thing)
                elif isinstance(thing, EnumMeta):
                    for key, obj in thing._member_map_.items():
                        k = get_obj_id(f'{prefix}_{key}')
                        if k is None:
                            continue
                        add(add_obj, obj, obj_i + k, f'{mod_name}.{name}.{key}')
            elif type(thing) in FUNC_TYPES:
                j = get_fun_id(f'{prefix}_{name}')
                if j is None:
                    continue
                add(add_fun, thing, fun_i + j, f'{mod_name}.{name}')
            elif j := get_obj_id(f'{prefix}_{name}'):
                add(add_obj, thing, obj_i + j, f'{mod_name}.{name}')
            # elif 'coroutine' in name:
            #     print(name, thing, mod_name, type(thing))

    add(add_cls, E.ForbiddenError,  cls_i + 0xFFFD, 'ForbiddenError')
    add(add_cls, E.RemoteException, cls_i + 0xFFFE, 'RemoteException')
    add_exc(E.RemoteException)
    add_exc(E.ForbiddenError)

    frb_id = FRB_OFFSET
    frb_cls_id = cls_i + frb_id
    frb_obj_id = obj_i + frb_id
    frb_mod_id = mod_i + frb_id
    frb_fun_id = fun_i + frb_id

    add(add_cls, forbidden_class,    frb_cls_id, 'forbidden_class')
    add(add_obj, forbidden_object,   frb_obj_id, 'forbidden_object')
    add(add_mod, forbidden_module,   frb_mod_id, 'forbidden_module')
    add(add_fun, forbidden_function, frb_fun_id, 'forbidden_function')
    FORBIDDEN_IDS.extend((frb_cls_id, frb_obj_id, frb_mod_id, frb_fun_id))

    cls_items.sort()
    obj_items.sort()
    fun_items.sort()
    mod_items.sort()

    SRID_TO_CLS = dict(cls_items)
    SRID_TO_OBJ = dict(obj_items)
    SRID_TO_FUN = dict(fun_items)
    SRID_TO_MOD = dict(mod_items)

    SRID_TO_NAME = dict(zip(sids, nams))
    SRID_TO_RSRC = dict(zip(sids, vals))
    LRID_TO_SRID = dict(zip(rids, sids))

    SYSTEM_IDS = frozenset(rids)

    SITE_PACKAGES = getusersitepackages(), *getsitepackages()
    SITE_PACKAGES = tuple(s for s in SITE_PACKAGES if type(s) is str and s)

################################################################################

SRID_TO_CLS: dict[SystemRID, ClassT] = {}
SRID_TO_OBJ: dict[SystemRID, ObjectT] = {}
SRID_TO_FUN: dict[SystemRID, FunctionT] = {}
SRID_TO_MOD: dict[SystemRID, ModuleT] = {}

SRID_TO_NAME: dict[SystemRID, str] = {}
SRID_TO_RSRC: dict[LocalRID, ResourceT] = {}
LRID_TO_SRID: dict[LocalRID, SystemRID] = {}

def to_system_id(obj: Any) -> SystemRID | None:
    return LRID_TO_SRID.get(id(obj))

def is_sys_exc_class(cls: type) -> bool: ...

################################################################################

_init_tables()
del _init_tables

is_sys_exc_class = set(SYS_EXCEPTIONS).__contains__  # type: ignore

################################################################################

def sanitize_path(p: str) -> str:
    if not p: return p
    if not p.startswith(SITE_PACKAGES): return p
    for s in SITE_PACKAGES:
        if p.startswith(s):
            return f'/usr/site-packages/{s[len(p):]}'  # TODO: Windows
    # TODO: do this for ~ as well, to become just /usr/
    return p

################################################################################

def print_system_ids():
    print()
    for srid, name in SRID_TO_NAME.items():
        print(f'{srid:8} {srid:6x}   {name}')
    print()

# print_system_ids()
