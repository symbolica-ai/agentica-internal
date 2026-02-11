# fmt: off

from collections.abc import Iterator
from typing import NoReturn, Any

from ... import flags
from ...attrs import VHDL
from ...request.request_resource import (
    ResourceGetAttr, ResourceSetAttr, ResourceDelAttr,
    ResourceCallMethod, ResourceCallSystemMethod
)

from ..handle import obj_handle, cls_handle, has_handle
from ..__raw import obj_get, cls_get

__all__ = [
    'obj_get',
    'cls_get',
    'v_getattribute',
    'v_getattr',
    'v_setattr',
    'v_delattr',
    'v_dir',
    'v_dict',
    'v_eq',
    'v_ne',
    'v_lt',
    'v_le',
    'v_gt',
    'v_ge',
    'v_len',
    'v_iter',
    'v_contains',
    'v_getitem',
    'v_setitem',
    'v_delitem',
    'v_str',
    'v_repr',
    'v_hash',
    'v_class_getitem',
    'v_empty'
]

################################################################################

# TODO:
# - modifying the dic returned by __dict__ should trigger __setattr__ on the remote;
# - trying to set `__dict__` should trigger the remote to replace its attributes.

def v_dict(self) -> dict[str, Any]:
    handle = obj_handle(self)
    if handle.open:
        return handle.hdlr(handle, ResourceCallSystemMethod(self, vars))
    else:
        dunder_dict = {}
        for k in handle.keys:
            try:
                dunder_dict[k] = getattr(self, k)
            except AttributeError:
                pass
        return dunder_dict

################################################################################

def v_getattribute(base: type, self, name: str) -> Any:
    if flags.VIRTUAL_OBJECT_DUNDER_DICT and name == '__dict__':
        return v_dict(self)
    return obj_get(self, name)

def v_getattr(base: type, self, name: str) -> Any:
    if base is BaseException and name == 'args':
        return ()
    handle = obj_handle(self)
    if not handle.open and name not in handle.keys and not hasattr(type(self), name):
        raise AttributeError(f"{handle.name} has no attribute {name!r}")
    value = handle.hdlr(handle, ResourceGetAttr(self, name))
    if name not in handle.keys:
        handle.keys.append(name)
    return value

def v_setattr(base: type, self, name: str, value) -> None:
    if not flags.VIRTUAL_OBJECT_MUTATION or base is BaseException:
        protected_attr(self, name)
    handle = obj_handle(self)
    handle.hdlr(handle, ResourceSetAttr(self, name, value))
    keys = handle.keys
    if name not in keys:
        keys.append(name)

def v_delattr(base: type, self, name: str):
    if not flags.VIRTUAL_OBJECT_MUTATION or base is BaseException:
        protected_attr(self, name)
    handle = obj_handle(self)
    if handle.open:
        handle.hdlr(handle, ResourceDelAttr(self, name))
        if name in handle.keys:
            handle.keys.remove(name)
    else:
        if name not in handle.keys:
            raise AttributeError(f"{handle.name} has no attribute {name!r}")
        handle.hdlr(handle, ResourceDelAttr(self, name))
        handle.keys.remove(name)

def v_dir(base: type, self) -> list[str]:
    handle = obj_handle(self)
    if handle.open:
        return handle.hdlr(handle, ResourceCallSystemMethod(self, dir))
    else:
        c_dir = dir(type(self))
        if VHDL in c_dir:
            c_dir.remove(VHDL)
        return handle.keys + c_dir

def protected_attr(obj, name: str) -> NoReturn:
    msg = f"Attribute '{name}' of object of type '{type(obj).__name__}' is protected."
    raise AttributeError(msg)

################################################################################

def v_eq(base: type, self, other):
    if self is other:
        return True
    if not issubclass(type(other), base):
        return False
    if hasattr(base, '__len__') and not has_handle(other):
        # if 'other' has differing length, do a cheaper test first
        if len(self) != len(other):
            return False
    handle = obj_handle(self)
    return handle.hdlr(handle, ResourceCallMethod(self, '__eq__', (other,)))

def v_ne(base: type, self, other):
    if self is other:
        return False
    if not issubclass(type(other), base):
        return False
    if hasattr(base, '__len__') and not has_handle(other):
        # if 'other' has differing length, do a cheaper test first
        if len(self) != len(other):
            return True
    handle = obj_handle(self)
    return handle.hdlr(handle, ResourceCallMethod(self, '__ne__', (other,)))

def v_lt(base: type, self, other):
    if self is other:
        return False
    if not issubclass(type(other), base):
        return not_supp_cmp('<', self, other)
    handle = obj_handle(self)
    return handle.hdlr(handle, ResourceCallMethod(self, '__lt__', (other,)))

def v_le(base: type, self, other):
    if self is other:
        return False
    if not issubclass(type(other), base):
        return not_supp_cmp('<=', self, other)
    handle = obj_handle(self)
    return handle.hdlr(handle, ResourceCallMethod(self, '__le__', (other,)))

def v_gt(base: type, self, other):
    if self is other:
        return False
    if not issubclass(type(other), base):
        return not_supp_cmp('>', self, other)
    handle = obj_handle(self)
    return handle.hdlr(handle, ResourceCallMethod(self, '__gt__', (other,)))

def v_ge(base: type, self, other):
    if self is other:
        return False
    if not issubclass(type(other), base):
        return not_supp_cmp('>=', self, other)
    handle = obj_handle(self)
    return handle.hdlr(handle, ResourceCallMethod(self, '__ge__', (other,)))

def not_supp_cmp(syntax: str, a: type, b: type) -> NoReturn:
    msg = f"'{syntax}' not supported between instances of '{a.__name__}' and '{b.__name__}'"
    raise TypeError(msg)

################################################################################

def v_len(base: type, self) -> int:
    handle = obj_handle(self)
    if hasattr(handle, 'size'):
        size = handle.size
    else:
        size = handle.hdlr(handle, ResourceCallSystemMethod(self, len))
    return size

def v_iter(base: type, self, *, rev: bool = False, oneshot: bool = False) -> Iterator[Any]:
    handle = obj_handle(self)
    func = reversed if rev else iter
    if oneshot:
        data = handle.hdlr(handle, ResourceCallSystemMethod(self, tuple))
        result = func(data)
    else:
        result = handle.hdlr(handle, ResourceCallSystemMethod(self, func))
    if not hasattr(type(result), '__next__'):
        raise TypeError(f"'{type(self).__name__}' object is not iterable")
    return result

################################################################################

def v_contains(base: type, self, other) -> bool:
    handle = obj_handle(self)
    if hasattr(handle, 'size') and handle.size == 0:
        return False
    return handle.hdlr(handle, ResourceCallMethod(self, '__contains__', (other,)))

def v_getitem(base: type, self, key) -> object:
    handle = obj_handle(self)
    return handle.hdlr(handle, ResourceCallMethod(self, '__getitem__', (key,)))

def v_setitem(base: type, self, key, val) -> None:
    handle = obj_handle(self)
    return handle.hdlr(handle, ResourceCallMethod(self, '__setitem__', (key, val,)))

def v_delitem(base: type, self, key) -> None:
    handle = obj_handle(self)
    return handle.hdlr(handle, ResourceCallMethod(self, '__delitem__', (key,)))

################################################################################

def v_str(base: type, self) -> str:
    try:
        handle = obj_handle(self)
        if hasattr(handle, 'str'):
            return handle.str
        res = handle.hdlr(handle, ResourceCallSystemMethod(self, str))
        assert type(res) is str
        return res
    except Exception as e:
        return f'<{type(self).__name__!r} object>'

def v_repr(base: type, self) -> str:
    try:
        handle = obj_handle(self)
        if hasattr(handle, 'str'):
            return handle.str
        res = handle.hdlr(handle, ResourceCallSystemMethod(self, repr))
        assert type(res) is str
        return res
    except:
        return f'<{type(self).__name__!r} object>'

################################################################################

def v_hash(base: type, self) -> int:
    handle = obj_handle(self)
    if hasattr(handle, 'hash'):
        return handle.hash
    result = handle.hdlr(handle, ResourceCallSystemMethod(self, hash))
    if type(result) is int:
        setattr(handle, 'hash', result)
        return result
    return id(self)

################################################################################

def v_class_getitem(base: type, cls: type, item: Any) -> Any:
    handle = cls_handle(cls)
    return handle.hdlr(handle, ResourceCallMethod(cls, '__class_getitem__', (item, ),))

################################################################################

V_EMPTY = {}
OBJECT_NEW = object.__new__

def v_empty(base: type, cls: type) -> object:
    if fn := V_EMPTY.get(base):
        return fn(cls)
    return base.__new__(cls)
