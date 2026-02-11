# fmt: off

import time
import sys
from io import StringIO

from os import getenv
from datetime import datetime

from collections.abc import Callable
from typing import Literal
from types import FunctionType, ModuleType
from pprint import pprint as _pprint
from threading import current_thread
from sys import setrecursionlimit, getrecursionlimit
from re import compile as re_compile
from agentica_internal.cpython.frame import exception_location

from .log import write_out, write_err
from .fmt import f_object_id, f_datum
from .color import *
from .ansi.palettes import Medium as MEDIUM
from .debug import debug_fmt, colorize, echoing
from .result import Result

__all__ = [
    'echoing',
    'oprint',
    'eprint',
    'rprint',
    'tprint',
    'nprint',
    'hprint',
    'pprint',
    'sprint',
    'colorize',
    'hdiv',
    'ddiv',
    'remote_print',
    'local_print',
    'print_unclosed_error',
    'print_asyncio_stacks',
    'print_current_stack',
    'print_current_frame',
    'print_all_tasks',
    'print_all_threads',
    'print_exception',
    'print_traceback',
    'print_warning',
    'timestamp',
    'set_timestamp_fmt',
    'RESET',
    'WARN',
    'ERROR',
    'WHITE',
    'RED',
    'YELLOW',
    'GREEN',
    'BLUE',
    'MAGENTA',
    'CYAN',
    'BOLD',
    'ITALIC',
    'UNDER',
    'DIM',
    'MEDIUM'
]

####################################################################################################

def oprint(*args, sep: str = ' ', start: str = '', end='\n', file=None):
    """Print to the _original_ system stdout."""
    text = _sprint(args, sep, start, end, str)
    write_out(text)

def eprint(*args, sep: str = ' ', start: str = '', end='\n', file=None):
    """Print to the _original_ system stderr."""
    text = _sprint(args, sep, start, end, str)
    write_err(text)

def rprint(*args, sep: str = ' ', start: str = '', end='\n', err: bool = False):
    """Prints to either original stdout or stderr."""
    text = _sprint(args, sep, start, end, str)
    write_err(text) if err else write_out(text)

def sprint(*args, sep: str = ' ', start='', end=''):
    """Prints to a string with same semantics as builtin print."""
    return _sprint(args, sep, start, end, str)

####################################################################################################

def _sprint(args: tuple, sep: str, start: str, end: str, str_fn: Callable[[object], str]) -> str:
    start = start if type(start) is str else ''
    end = end if type(end) is str else '\n'
    sep = sep if type(sep) is str else ' '
    if not args:
        return start + end
    strs = [start]
    add = strs.append
    for i, arg in enumerate(args):
        add(sep) if i else None
        add(str_fn(arg))
    add(end)
    return cat(strs)

cat = ''.join

####################################################################################################

def remote_print(*args, sep: str = ' ') -> None:
    _remote_print(RP_GUTTER, args, sep)

def local_print(*args, sep: str = ' ') -> None:
    _remote_print(LP_GUTTER, args, sep)

def _remote_print_str(args: tuple, sep: str = ' ') -> str:
    if len(args) == 1 and type(args[0]) is str:
        return args[0]
    return _sprint(args, sep, '', '', f_object_id)

def _remote_print(gutter: str, args: tuple, sep: str) -> None:
    text = _remote_print_str(args, sep)
    text = add_gutter(gutter, text)
    write_out(text + '\n\n')

def add_gutter(gutter: str, text: str) -> str:
    return cat(gutter + s for s in text.splitlines(True))

RP_GUTTER = "\033[44m RP \033[49m "
LP_GUTTER = "\033[43m LP \033[49m "

####################################################################################################

def pprint(*args, err: bool = False):
    """Pretty prints, using rich if possible."""
    try:
        if 'rich' in sys.modules:
            import rich
            str_io = StringIO()
            rich.print(*args, file=str_io)
            text = str_io.getvalue()
            write_err(text) if err else write_out(text)
            return
    except:
        pass
    str_io = StringIO()
    _pprint(*args, stream=str_io, compact=False, sort_dicts=False, depth=5)
    text = str_io.getvalue()
    write_err(text) if err else write_out(text)

####################################################################################################

START = time.time()

_NOW_FMT: str | None = None

def set_timestamp_fmt(fmt: Literal[None, 'NONE', 'MS', 'SHORT', 'FULL']):
    global _NOW_FMT
    if fmt is None or fmt == 'NONE':
        _NOW_FMT = None
    elif fmt == 'MS':
        _NOW_FMT = '$'
    elif fmt == 'SHORT':
        _NOW_FMT = '@'
    elif fmt == 'FULL':
        _NOW_FMT = FULL_FORMAT + ': '
    else:
        raise ValueError(f'Unknown timestamp format {fmt!r}')

FULL_FORMAT = "%Y-%m-%d %H:%M:%S"

def timestamp() -> str:
    if _NOW_FMT is None:
        return ''
    elif _NOW_FMT == '$':
        millis = round((time.time() - START) * 1000)
        return f'{millis:<10} '
    elif _NOW_FMT == '@':
        now = datetime.now()
        millis = now.microsecond // 1000
        time_str = f'{now.minute:02d}:{now.second:02d}:{millis:03d}'
        return DIM(time_str) + ' '
    elif isinstance(_NOW_FMT, str):
        return datetime.now().strftime(_NOW_FMT)
    return ''

DEFAULT_FORMAT: Literal[None, 'MS', 'SHORT', 'FULL'] = None
set_timestamp_fmt(getenv('LOGGING_TIMESTAMP_FORMAT', DEFAULT_FORMAT)) # type: ignore

####################################################################################################

def tprint(*args, sep: str = ' ', end: str = '\n', truncate: bool = True, err: bool = False) -> None:
    """Print with a timestamp, thread name, and truncating long arguments."""
    limit = getrecursionlimit()
    text = ''
    try:
        setrecursionlimit(1000)
        thread_name = current_thread().name
        if truncate and args:
            args = trunc_args(args, len(thread_name)+1)
        thread_name = colorize(thread_name, 20)
        f_thread = f'\n{timestamp()}{thread_name} '
        text = _sprint(args, sep, f_thread, end, str)
    except Exception as exc:
        f_types = ' '.join(type(arg).__name__ for arg in args)
        f_location = exception_location(exc)
        text = f'\n\ntprint error: {type(exc).__name__}\nloc = {f_location}\nargs = {f_types}\n\n'
    finally:
        setrecursionlimit(limit)
    write_err(text) if err else write_out(text)

####################################################################################################

# TODO: rename `truncate` to `format`
def nprint(*args, sep: str = ' ', end: str = '\n', truncate: bool = True, err: bool = False):
    """Like tprint but without the thread name and timestamp."""
    limit = getrecursionlimit()
    text = ''
    try:
        setrecursionlimit(1000)
        if truncate and args:
            args = trunc_args(args, 0)
        text = _sprint(args, sep, '', end, str)
    except Exception as exc:
        f_types = ' '.join(type(arg).__name__ for arg in args)
        f_location = exception_location(exc)
        text = f'\n\nnprint error: {type(exc).__name__}\nloc = {f_location}\nargs = {f_types}\n\n'
    finally:
        setrecursionlimit(limit)
    write_err(text) if err else write_out(text)

####################################################################################################

def hprint(*args, sep: str = ' ', end: str = '\n'):
    """Print with a horizontal line above."""
    text = _sprint(args, sep, HDIV, end, str)
    write_out(text)

####################################################################################################

def hdiv():
    """Print a horizontal line."""
    write_out(HDIV)

def ddiv():
    """Print a double horizontal line."""
    write_out(DDIV)

####################################################################################################

def print_unclosed_error(obj):
    name = f_trunc(obj)
    text = f'{BANNER}{name} WAS GARBAGE COLLECTED WITHOUT BEING CLOSED\n{BANNER}'
    write_err(text)

####################################################################################################

def f_trunc(arg: object) -> str:

    cls = type(arg)

    if cls is bytes:
        s = f_bytes(arg)  # type: ignore
        return Rgb.hash_bytes(arg)(s)

    if cls is str and len(arg) > 256 and len(pure := strip_ansi(arg)) > 256:
        if 'Traceback (most recent call last)' in arg:
            return arg
        if '\n\n' in arg:
            return arg
        if arg.startswith("'''") and arg.endswith("'''"):
            return arg
        if ' := ' in arg:
            return arg
        return pure[:256] + "…"

    if cls is str:
        if arg.startswith('<') and arg.endswith('>'):
            return colorize(arg)
        if len(arg) == 36 and bool(UUID_RE.fullmatch(arg)):
            return colorize(f_uuid(arg))
        return arg

    if cls in (int, bool, float):
        return f_datum(arg)

    if cls is Result:
        if arg.is_ok:
            return f'Result.ok({f_object_id(arg.value)})'
        return repr(arg)

    kind: str = ''
    name: str = ''
    virt: bool = False

    if cls is type or isinstance(arg, type):
        kind = 'class'
        name = arg.__name__
        virt = is_virt_cls(arg)
    elif cls is FunctionType:
        kind = 'function'
        name = arg.__name__
        virt = is_virt_obj(arg)
    elif cls is ModuleType:
        name = arg.__name__
        kind = 'module'
        virt = is_virt_obj(arg)

    if name:
        if virt:
            kind = 'virtual ' + kind
        return colorize(f'<{kind} {name!r} @ {id(arg):x}>')

    if issubclass(cls, BaseException) and not is_virt_obj(arg):
        return f_exception(arg)

    name = cls.__name__
    if is_virt_obj(arg):
        return colorize(f'<virtual {name!r} object @ {id(arg):x}>')
    elif is_virt_cls(cls):
        name = f'real object of virtual class {cls.__name__!r}'
        return colorize(f'<real object of virtual class {name!r} @ {id(arg):x}>')

    try:
        type_get(cls, 'short_str')
        f_short = arg.short_str()
        if type(f_short) is str:
            return colorize(f_short)
    except:
        pass

    if cls in (tuple, list, set, frozenset) and len(arg) <= 4:
        f_args = ', '.join(map(f_trunc, arg))
        if cls is tuple:
            return '(' + f_args + ')'
        if cls is frozenset:
            return 'frozenset(' + f_args + ')'
        if cls is list:
            return '[' + f_args + ']'
        if cls is set:
            return '{' + f_args + '}'

    if cls is dict and len(arg) <= 6:
        keys = tuple(arg.keys())
        if all(type(k) is str for k in keys):
            return 'dict(' + ', '.join(f'{k}=...' for k in keys) + ')'

    try:
        type_get(cls, '__short_str__')
        f_short = arg.__short_str__()
        if type(f_short) is str:
            return colorize(f_short)
    except:
        pass

    f_arg = f_object_id(arg)
    f_col = Rgb.id_obj(arg)
    return f_col.hi(f_arg)


def is_virt_cls(cls: type) -> bool:
    try:
        type_get(cls, '___vhdl___')
        return True
    except:
        return False

def is_virt_obj(obj: object) -> bool:
    try:
        obj_get(obj, '___vhdl___')
        return True
    except:
        return False


obj_get = object.__getattribute__
type_get = type.__getattribute__

####################################################################################################

def trunc_args(args: tuple[str, ...], margin: int) -> tuple[str, ...]:
    if not args:
        return ()
    *most, last = args
    # this handles the case where there is a single non-colorized final arg
    # that is a record, which we will print on multiple lines using 'k = v' syntax...
    if all(type(arg) is str and arg.startswith(ANSI_PREFIX) for arg in most):
        if isinstance(last, dict) and len(last) and all(type(k) is str for k in last.keys()):
            return *most, f_multiline_dict(last, margin)
    return tuple(map(f_trunc, args))

ANSI_PREFIX = "\033"

####################################################################################################

def f_multiline_dict(dct: dict, margin: int = -1) -> str:
    if not dct:
        return '{}'
    if margin == -1:
        margin = len(current_thread().name) + 1
    keys = list(dct.keys())
    wide = max(map(len, keys))
    f_margin = ' ' * margin
    result = ''.join(f'\n{f_margin}{k.ljust(wide)} := {f_trunc(v)}' for k, v in dct.items())
    return result

####################################################################################################

def f_uuid(s: str) -> str:
    return colorize(s.rsplit('-', 1)[-1])

####################################################################################################

def f_msgpack(m: bytes) -> str:
    from itertools import takewhile
    if m[1:].startswith(b'\xa3msg'):
        msg_kind = ''.join(map(chr, takewhile(lambda x: 32 < x < 128, m[6:32])))
        return f"<{msg_kind!r} msgpack bytes>"
    else:
        return "<unknown msgpack bytes>"

####################################################################################################

def f_bytes(b: bytes) -> str:
    if len(b) > 8 and 0x80 <= b[0] <= 0x8F:
        return f_msgpack(b)
    if len(b) > 48:
        s = repr(b[:48])
        return s[:48] + "…" + s[0]
    return repr(b)

####################################################################################################

def f_exception(exc: BaseException):
    import traceback
    lines = traceback.format_exception(exc)
    if location := exception_location(exc):
        lines.insert(0, location)
    f_exc = '\n'.join(lines).replace('\n', INDENT).rstrip(INDENT)
    return INDENT + f_exc

####################################################################################################

panic                = debug_fmt.panic
print_current_stack  = debug_fmt.print_current_stack
print_current_frame  = debug_fmt.print_current_frame
print_all_tasks      = debug_fmt.print_all_tasks
print_all_threads    = debug_fmt.print_all_threads
print_exception      = debug_fmt.print_exception
print_traceback      = debug_fmt.print_traceback
print_warning        = debug_fmt.print_warning

###############################################################################


def print_asyncio_stacks(delay: int = 0):
    if delay > 0:
        return print_asyncio_stacks_in_n_seconds(delay)

    write_out(STACKS_TEXT)
    try:
        print_all_tasks()
    except Exception as exc:
        oprint("Error printing asyncio stacks:", type(exc).__name__)

    write_out(THREADS_TEXT)

    try:
        print_all_threads()
        oprint('', BDIV, '', sep='\n')
    except Exception as exc:
        oprint("Error printing threads:", type(exc).__name__)


def print_asyncio_stacks_in_n_seconds(delay: int):
    import signal

    def debug_handler(signum, frame):
        del signum
        del frame
        print_asyncio_stacks()

    signal.signal(signal.SIGALRM, debug_handler)
    signal.alarm(delay)


###############################################################################

HDIV = BLUE('─' * 80) + '\n'
DDIV = RED('═' * 80) + '\n'
BDIV = RED('█' * 80) + '\n'

INDENT = '\n┃ '

BANNER = (("*" * 75) + "\n") * 10

UUID_RE = re_compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')

STACKS_TEXT = f'\n{BDIV}ASYNCIO STACKS\n\n'
THREADS_TEXT = f'\n{BDIV}THREADS\n\n'
