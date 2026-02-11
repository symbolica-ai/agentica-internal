# fmt: off

from operator import attrgetter
from types import CodeType
from typing import NamedTuple, TypeGuard

__all__ = [
    'is_code',
    'is_async_code',
    'code_arg_info',
    'code_arg_names',
    'print_code',
    'ArgInfo',
    'FLAGS',
]

################################################################################

def is_code(obj: object) -> TypeGuard[CodeType]:
    """Returns True for `CodeType` objects."""

    return isinstance(obj, CodeType)

################################################################################

def is_async_code(code: CodeType) -> bool:
    return isinstance(code, CodeType) and bool(code.co_flags & FLAGS.IS_ASYNC)

################################################################################

class ArgInfo(NamedTuple):
    pos:       list[str]
    key:       list[str]
    pos_star:  str | None
    key_star:  str | None
    pos_only:  int

    def anno_keys(self) -> tuple[str, ...]:
        keys = *self.pos, self.pos_star, *self.key, self.key_star, 'return'
        return tuple(k for k in keys if k)

    def default_keys(self) -> tuple[str, ...]:
        return *self.pos, *self.key

################################################################################

def code_arg_info(code: CodeType, skip: int = 0) -> ArgInfo:
    """Given a CodeType object, returns a ArgInfo describing it properties."""

    assert type(code) is CodeType, f'{code} is not a CodeType object'

    strs, flags, pos, pos_only, key_only = codeattrs(code)
    skip = min(skip, pos)
    if skip:
        strs = strs[skip:]
        pos -= skip
        pos_only -= skip
        if pos_only < 0: pos_only = 0
    key_only = key_only
    fixed = pos + key_only

    pos_star = bool(flags & FLAGS.VARARGS)
    key_star = bool(flags & FLAGS.VARKEYWORDS)

    return ArgInfo(
        pos=strs[:pos],
        key=strs[pos:fixed],
        pos_only=pos_only,
        pos_star=strs[fixed] if pos_star else None,
        key_star=strs[fixed + pos_star] if key_star else None,
    )

################################################################################

def code_arg_names(code: CodeType) -> list[str]:
    """Given a CodeType object, returns its argument names."""

    assert type(code) is CodeType, f'{code} is not a CodeType object'

    strs, flags, non_key, pos_only, key_only = codeattrs(code)
    has_tup = bool(flags & FLAGS.VARARGS)
    has_dct = bool(flags & FLAGS.VARKEYWORDS)
    num_strs = non_key + key_only + has_tup + has_dct

    return strs[:num_strs]

################################################################################

codeattrs = attrgetter(
    'co_varnames', 'co_flags', 'co_argcount', 'co_posonlyargcount', 'co_kwonlyargcount'
)

################################################################################

class FLAGS:
    """Flags present on a CodeObject."""

    OPTIMIZED = 1
    NEWLOCALS = 2
    VARARGS = 4
    VARKEYWORDS = 8
    NESTED = 16
    GENERATOR = 32
    NOFREE = 64
    COROUTINE = 128
    ITERABLE_COROUTINE = 256
    ASYNC_GENERATOR = 512
    IS_ASYNC = ASYNC_GENERATOR | COROUTINE | ITERABLE_COROUTINE

################################################################################

def print_code(code: CodeType) -> None:
    print(f'''
CodeType(
    co_name     = {code.co_name!r}
    co_qualname = {code.co_qualname!r}
    co_argcount = {code.co_argcount}
    co_nlocals  = {code.co_nlocals}
    co_names    = {fmt_names(code.co_names)}
    co_varnames = {fmt_names(code.co_varnames)}
    co_freevars = {fmt_names(code.co_freevars)}
    co_cellvars = {fmt_names(code.co_cellvars)}
    co_conts    = {code.co_consts}
    co_flags    = {code.co_flags}
    co_code     = {code.co_code!r}
                  {fmt_bytecode(code)}>
)''')

################################################################################

def fmt_names(strs: tuple[str, ...]) -> str:
    return '[' + ', '.join(map(repr, strs)) + ']'

################################################################################

def fmt_bytecode(code: CodeType) -> str:
    from dis import get_instructions
    strs = []
    for i, ins in enumerate(get_instructions(code)):
        strs.append(f'{ins.opname}({ins.arg})')
        if i > 8:
            break
    return '[' + ', '.join(strs) + ']'
