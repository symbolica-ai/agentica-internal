# fmt: off

import typing

from types import FunctionType, FrameType
from typing import Any
from sys import modules, _getframe
from msgspec import Struct

from ..alias import optstr, optint

__all__ = [
    'Identifier',
    'get_cls_identifier',
    'set_cls_identifier',
    'get_fun_identifier',
    'set_fun_identifier',
    'get_stack_identifier',
    'get_frame_identifier',
]

################################################################################

class Identifier(Struct):

    __debug_fmt_str__ = '`{info}`'
    __debug_fmt_slots__ = False

    name: str
    qual: optstr = None
    mod:  optstr = None
    file: optstr = None
    line: optint = None

    def __repr__(self):
        return f"<Identifier {self.fullname!r}>"

    def __short_str__(self) -> str:
        s = self.fullname
        if len(s) < 38:
            return s
        elif '.' in s:
            return '.'.join(
                e if len(e) < 10 else e[:8] + '~'
                for e in s.split('.')
            )
        else:
            return f'{s[:32]}~{s[32:]}'

    __debug_info_str__ = __short_str__

    @property
    def qualname(self) -> str:
        return self.qual or self.name

    @property
    def fullname(self) -> str:
        qual = self.qual or self.name
        mod = self.mod
        return f'{mod}.{qual}' if mod and mod != '__main__' else qual


################################################################################

def get_fun_identifier(fun: Any) -> 'Identifier':
    from ...cpython.inspection import callable_module_and_name
    from ..system import sanitize_path

    mod, qual, name = callable_module_and_name(fun)
    if qual == name or qual == '__main__': qual = None

    if type(fun) is FunctionType:
        code = fun.__code__
        file = sanitize_path(code.co_filename)
        return Identifier(name, qual, mod, file, code.co_firstlineno)
    else:
        return Identifier(name, qual, mod)


def set_fun_identifier(fun: FunctionType, loc: Identifier):
    name, qualname = loc.name, loc.qualname
    fun.__name__ = name
    fun.__qualname__ = qualname
    fun.__module__ = loc.mod
    fun.__code__ = fun.__code__.replace(
        co_name=name,
        co_qualname=qualname,
        co_firstlineno=loc.line or 0,
        co_filename=loc.file or ''
    )


################################################################################

def get_cls_identifier(cls: Any) -> 'Identifier':
    name = cls.__name__

    qual = getattr(cls, '__qualname__', None)
    if qual == name or qual == '__main__': qual = None

    mod = getattr(cls, '__module__', None)
    if type(mod) is str:
        line = getattr(cls, '__firstlineno__', None)
        if type(line) is int:
            file = get_module_file(mod)
        else:
            file = line = None
    else:
        mod = file = line = None

    return Identifier(name, qual, mod, line, file)


def set_cls_identifier(cls: type, loc: Identifier):
    cls.__name__ = loc.name
    cls.__qualname__ = loc.qualname
    if mod := loc.mod:
        cls.__module__ = mod
        if file := loc.file:
            cls.__filename__ = file
            if line := loc.line:
                cls.__firstlineno__ = line


################################################################################

def get_module_file(mod: str) -> optstr:
    if mod_obj := modules.get(mod):
        if file := getattr(mod_obj, '__file__', None):
            if type(file) is str:
                return file
    return None


################################################################################

OUR_MODULES = 'agentica_internal', 'agentica'
OUR_PATHS: tuple[str] | None = None

def obtain_our_paths():
    lib_path = typing.__file__.removesuffix('typing.py')
    paths = {'/sandbox/guest/', lib_path, '<'}
    for mod in OUR_MODULES:
        if sys_mod := modules.get(mod):
            if path := sys_mod.__file__:
                paths.add(path)
    return tuple(paths)

def get_stack_identifier(skip: int) -> Identifier | None:
    global OUR_PATHS
    if OUR_PATHS is None:
        OUR_PATHS = obtain_our_paths()
    frame = _getframe(skip + 1)
    while frame:
        filename = frame.f_code.co_filename
        ours = filename.startswith(OUR_PATHS)
        if not ours or 'testing' in filename:
            return get_frame_identifier(frame)
        frame = frame.f_back
    return None

def get_frame_identifier(frame: FrameType) -> Identifier:
    code = frame.f_code
    line = frame.f_lineno
    file = code.co_filename
    qual = code.co_qualname
    name = code.co_name
    mod = frame.f_globals.get('__name__', None)
    if type(mod) is not str: mod = None
    return Identifier(name, qual, mod, file, line)
