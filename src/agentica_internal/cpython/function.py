# fmt: off

from secrets import token_hex
from types import FunctionType
from typing import Any, TypeGuard, Iterable

from .code import FLAGS

__all__ = [
    'is_function',
    'func_location',
    'func_def_str',
    'func_get_defaults',
    'func_annotations',
    'func_compile',
    'func_is_coro',
    'func_mark_coro',
    'func_set_defaults',
]

################################################################################

def is_function(obj: object) -> TypeGuard[FunctionType]:
    """Returns True for a `FunctionType` object: functions explicitly declared with `def foo(...)`."""

    return isinstance(obj, FunctionType)

################################################################################

def func_location(func: FunctionType) -> str:
    assert isinstance(func, FunctionType)

    code = func.__code__
    return f'{code.co_filename}#{code.co_firstlineno}'

################################################################################

def func_def_str(func: FunctionType) -> str | None:
    assert isinstance(func, FunctionType)
    code = func.__code__
    filename = code.co_filename
    start = code.co_firstlineno
    if not filename: return None
    try:
        stop = max(l for _, _, l in code.co_lines() if l is not None)
        joined = '\n'.join(_func_def_lines(filename, start, stop))
        return joined or None
    except:
        return None


def _func_def_lines(filename: str, start: int, stop: int):
    from linecache import getline
    from os.path import isfile
    assert filename and isfile(filename)
    end_1, end_2 = ') -> ', '):'
    lines = [getline(filename, i) for i in range(start, stop + 1)]
    while not lines[0].lstrip(' \t').startswith('def'): lines.pop(0)
    for line in lines:
        if end_1 in line or end_2 in line:
            yield line.rsplit(':', 1)[0] + ': ...'
            break
        yield line

################################################################################

def func_get_defaults(func: FunctionType) -> Iterable[tuple[str, Any]]:
    if defaults := func.__defaults__:
        code = func.__code__
        var_names = code.co_varnames
        arg_count = code.co_argcount
        keys = var_names[arg_count-len(defaults):]
        yield from zip(keys, defaults)
    if kwdefaults := func.__kwdefaults__:
        yield from kwdefaults.items()

################################################################################

def func_set_defaults(func: FunctionType, defaults: dict[str, Any]):
    if not defaults:
        func.__defaults__ = func.__kwdefaults__ = None
        return

    code = func.__code__
    names = code.co_varnames

    if num_pos := code.co_argcount:
        k = num_pos
        for i in reversed(range(0, num_pos)):
            if names[i] not in defaults: break
            k = i
        tup = tuple(defaults[k] for k in names[k:num_pos])
        func.__defaults__ = tup or None

    if num_key := code.co_kwonlyargcount:
        key_args = names[num_pos:num_pos + num_key]
        dct = {k: defaults[k] for k in key_args if k in defaults}
        func.__kwdefaults__ = dct or None

################################################################################

def func_annotations(func: FunctionType) -> Iterable[tuple[str, Any]]:
    if annos := func.__annotations__:
        if type(annos) is dict:
            return annos.items()
    return ()

################################################################################

def func_compile(params: str, body: str, **constants) -> FunctionType:
    """
    Compiles and returns a function with a given body and params via
        `def _({params}): {body}`

    Each kwarg TOKEN=value becomes a closure slot available as `TOKEN
    in the body. The token `FUNCTION refers to the function itself.
    The token `PROC_OOO_DEFS refers to a function that post-processes
    args/kwargs to handle out-of-order kw default overrides.
    """
    if '`PROC_OOO_DEFS' in body:
        constants['PROC_OOO_DEFS'] = proc_ooo_defs

    const_keys = ', '.join('`' + c for c in constants)

    code = f'''
def _({const_keys}):
    def `FUNCTION({params}): {body}
    return `FUNCTION
'''.strip().replace("`", SALT)

    try:
        exec(code, ns := {})
    except BaseException as err:
        err.add_note(f"{params=!r}\n'''\n{code}\n'''")
        raise err

    fn = ns['_'](*constants.values())
    assert isinstance(fn, FunctionType)

    return fn

SALT = f'_{token_hex(2)}_'

################################################################################

def proc_ooo_defs(args: tuple, kwargs: dict, *keys: str) -> tuple[tuple, dict]:
    from ..core.sentinels import ARG_DEFAULT
    for i, arg in enumerate(args):
        if arg is ARG_DEFAULT: break
    else:
        return args, kwargs
    for arg, key in zip(args[i:], keys[i:]):
        if arg is not ARG_DEFAULT:
            kwargs[key] = arg
    # print("ARGS = ", args[:i], "KWARGS = ", kwargs)
    return args[:i], kwargs

################################################################################

def func_is_coro(func: FunctionType) -> bool:
    return hasattr(func, IS_CORO_ATTR) or bool(func.__code__.co_flags & IS_ASYNC_MASK)

################################################################################

def func_mark_coro(func: FunctionType):
    if hasattr(func, IS_CORO_ATTR) or bool(func.__code__.co_flags & IS_ASYNC_MASK):
        pass
    else:
        from inspect import markcoroutinefunction
        markcoroutinefunction(func)

################################################################################

IS_ASYNC_MASK = FLAGS.IS_ASYNC
IS_CORO_ATTR = '_is_coroutine_marker'
