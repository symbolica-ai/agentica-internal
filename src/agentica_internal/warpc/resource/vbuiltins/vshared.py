# fmt: off
# ruff: noqa

from types import FunctionType
from typing import Self, Any
from collections.abc import Iterable, Iterator, Callable

from ....core.sentinels import ARG_DEFAULT

from ... import flags
from ...attrs import VHDL
from ...request.request_resource import *

from ..handle import has_handle
from ..__raw import obj_get, obj_handle, cls_handle

################################################################################

index_t = int | slice

################################################################################

def copy_fn_attrs(s: FunctionType, t: FunctionType):
    attrs = s.__name__, s.__qualname__, s.__module__, s.__annotations__, s.__defaults__, s.__kwdefaults__
    t.__name__, t.__qualname__, t.__module__, t.__annotations__, t.__defaults__, t.__kwdefaults__ = attrs

################################################################################

def v_dummy[C: Callable](fn: C) -> C:
    assert isinstance(fn, FunctionType)
    fn.__is_dummy__ = True
    return fn

################################################################################

def rw_property[C: Callable](fn: C) -> C:
    assert isinstance(fn, FunctionType)
    anno = fn.__annotations__['return']
    name = fn.__name__

    def fget(obj) -> anno:
        handle = obj_handle(obj)
        return handle.hdlr(handle, ResourceGetAttr(obj, name))

    def fset(obj, value: anno):
        handle = obj_handle(obj)
        return handle.hdlr(handle, ResourceSetAttr(obj, name, value))

    return property(fget, fset)  # type: ignore

################################################################################

def ro_property[C: Callable](fn: C) -> C:
    assert isinstance(fn, FunctionType)
    anno = fn.__annotations__['return']
    name = fn.__name__

    def fget(obj) -> anno:
        handle = obj_handle(obj)
        return handle.hdlr(handle, ResourceGetAttr(obj, name))

    return property(fget)  # type: ignore

################################################################################

def special[C: Callable](fn: C) -> C:
    setattr(fn, '___special___', True)
    return fn

################################################################################

def forward[C: Callable](old_fn: C) -> C:
    assert isinstance(old_fn, FunctionType)
    name, qname = old_fn.__name__, old_fn.__qualname__
    old_code = old_fn.__code__
    old_arg_count = old_code.co_argcount
    old_pos_count = old_code.co_posonlyargcount
    old_key_count = old_code.co_kwonlyargcount
    old_vars = old_code.co_varnames
    kw1 = old_vars[old_arg_count] if old_key_count > 0 else None
    kw2 = old_vars[old_arg_count+1] if old_key_count > 1 else None
    match old_arg_count, old_key_count:
        case (1, 0):
            def new_fn(self):
                handle = obj_handle(self)
                request = ResourceCallMethod(self, name)
                return handle.hdlr(handle, request)
        case (2, 0):
            def new_fn(self, pos1):
                handle = obj_handle(self)
                request = ResourceCallMethod(self, name, (pos1,))
                return handle.hdlr(handle, request)
        case (3, 0):
            def new_fn(self, pos1, pos2):
                handle = obj_handle(self)
                request = ResourceCallMethod(self, name, (pos1, pos2))
                return handle.hdlr(handle, request)
        case (4, 0):
            def new_fn(self, pos1, pos2, pos3):
                handle = obj_handle(self)
                request = ResourceCallMethod(self, name, (pos1, pos2, pos3))
                return handle.hdlr(handle, request)
        case (1, 1):
            def new_fn(self, key1):
                handle = obj_handle(self)
                request = ResourceCallMethod(self, name, (), {kw1: key1})
                return handle.hdlr(handle, request)
        case (1, 2):
            def new_fn(self, key1, key2):
                handle = obj_handle(self)
                request = ResourceCallMethod(self, name, (), {kw1: key1, kw2: key2})
                return handle.hdlr(handle, request)
        case (2, 1):
            def new_fn(self, pos1, key1):
                handle = obj_handle(self)
                request = ResourceCallMethod(self, name, (pos1,), {kw1: key1})
                return handle.hdlr(handle, request)
        case (3, 1):
            def new_fn(self, pos1, pos2, key1):
                handle = obj_handle(self)
                request = ResourceCallMethod(self, name, (pos1, pos2), {kw1: key1})
                return handle.hdlr(handle, request)
        case _:
            raise TypeError(f'{old_arg_count} pos, {old_key_count} key')

    assert isinstance(new_fn, FunctionType)
    copy_fn_attrs(old_fn, new_fn)
    new_code = new_fn.__code__
    new_vars = old_vars + new_code.co_varnames[len(old_vars):]
    new_fn.__code__ = new_code.replace(
        co_name=name,
        co_qualname=qname,
        co_filename='<builtins>',
        co_varnames=new_vars,
        co_argcount=old_arg_count,
        co_posonlyargcount=old_pos_count,
        co_kwonlyargcount=old_key_count,
    )
    return new_fn


################################################################################

def forward_sys[C: Callable](sys_fn) -> Callable[[C], C]:

    def wrap(old_fn):
        def new_fn(self):
            handle = obj_handle(self)
            return handle.hdlr(handle, ResourceCallSystemMethod(self, sys_fn))
        assert isinstance(old_fn, FunctionType)
        assert isinstance(new_fn, FunctionType)
        copy_fn_attrs(old_fn, new_fn)
        return new_fn

    return wrap
