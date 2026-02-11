# fmt: off

"""
Module to help customize traceback formatting.
Relatively self-contained (only depends on cpython submodule, not ANSI).
"""

import re
import sys
import typing as T
import shutil

from pathlib import Path
from abc import ABCMeta
from collections.abc import Callable, Collection, Iterable
from os import environ
from os.path import abspath
from sys import __stdout__ as STDOUT, __stderr__ as STDERR
from types import (
    BuiltinFunctionType,
    CoroutineType,
    FrameType,
    FunctionType,
    MethodType,
    NoneType,
    TracebackType,
    UnionType,
)
from typing import NoReturn, TYPE_CHECKING, Any

from .color import Rgb
from .recursion import no_recursion_limit
from ..cpython.frame import *

__all__ = [
    'debug_fmt',
    'fmt_frame',
    'fmt_exception',
    'fmt_traceback',
    'fmt_current_stack',
    'frame_function',
    'frame_location',
    'exception_frame',
    'exception_location',
    'enable_rich_tracebacks',
    'echoing',
    'avoid_file',
    'avoid_function',
    'avoid_module',
]

####################################################################################################

if TYPE_CHECKING:
    import asyncio

####################################################################################################

def _print(*args: str, sep: str = ' ', end: str = '\n', err: bool = False) -> None:
    file = STDERR if err else STDOUT
    text = sep.join(a if type(a) is str else '<!str>' for a in args)
    if end:
        text += end
    file.write(text)
    file.flush()

####################################################################################################

type FmtFn = Callable[[Any], str]
type FmtDispatch = dict[type, FmtFn]
type Lines = Iterable[str]

TERM_WIDTH: int = 0
TRIM_LINES: bool = False

IN_DEBUGGER: bool = any(mod in sys.modules for mod in ('pydevd', 'debugpy', 'pdb'))
IN_PYCHARM: bool = 'PYCHARM_HOSTED' in environ
IN_PYTEST: bool = 'PYTEST_VERSION' in environ
COLORTERM: bool = environ.get('COLORTERM') == "truecolor"


def _cls(a: Any) -> type:
    return a.__class__  # type: ignore

GenericAlias         = _cls(list[int])
_GenericAlias        = _cls(T.List[int])
_AnyMeta             = _cls(T.Any)
_SpecialForm         = _cls(T.Self)
_SpecialGenericAlias = _cls(T.List)
_TupleType           = _cls(T.Tuple)
_UnionGenericAlias   = _cls(T.Union[int,str])
_CallableType        = _cls(T.Callable)

TY_CLASSES: tuple[type, ...] = (
    GenericAlias,
    _GenericAlias,
    _AnyMeta,
    _SpecialForm,
    _SpecialGenericAlias,
    _TupleType,
    _UnionGenericAlias,
    _CallableType,
)

TY_SHORT = {
    'GenericAlias':         'Generic',
    'UnionType':            'Union',
    '_SpecialForm':         '_SF',
    '_AnyMeta':             '_AM',
    '_GenericAlias':        '_SGeneric',
    '_SpecialGenericAlias': '_Generic',
    '_UnionGenericAlias':   '_Union',
    '_CallableType':        '_CallableT'
}

dict_keys_t      = type(dict().keys())
dict_values_t    = type(dict().values())
dict_items_t     = type(dict().items())

DICT_TYPES: tuple[type, ...] = dict_keys_t, dict_values_t, dict_items_t

list_iter_t      = type(iter(list()))
tuple_iter_t     = type(iter(tuple()))
set_iter_t       = type(iter(set()))
zip_iter_t       = type(iter(zip((), ())))
map_iter_t       = type(iter(map(hash, ())))

REDUCE_TYPES: tuple[type, ...] = list_iter_t, tuple_iter_t, set_iter_t, zip_iter_t, map_iter_t


class Stringifier(dict[type, FmtFn]):
    ansi: bool
    fmt_object: Callable[..., str]
    fmt_type: FmtFn

    def __init__(self, *args, ansi: bool):
        super().__init__(*args)

        self[list]                 = self.fmt_list
        self[tuple]                = self.fmt_tuple
        self[set]                  = self.fmt_set
        self[dict]                 = self.fmt_dict
        self[GenericAlias]         = self.fmt_galias
        self[UnionType]            = self.fmt_union
        self[_UnionGenericAlias]   = self.fmt_union
        self[_GenericAlias]        = self.fmt_galias
        self[_SpecialGenericAlias] = self.fmt_galias
        self[_SpecialForm]         = self.fmt_sform_ty
        self[_AnyMeta]             = self.fmt_ty_arg
        self[ABCMeta]              = self[type]
        for t in REDUCE_TYPES:
            self[t]                = self.fmt_reduce
        for t in DICT_TYPES:
            self[t]                = self.fmt_dict_part

        self.ansi = ansi
        self.fmt_type = self[type]
        self.fmt_object = self[_object]

    def __call__(self, obj: object) -> str:
        obj_cls = type(obj)
        if fn := self.get(obj_cls):
            return fn(obj)
        for cls, fn in self.items():
            if issubclass(cls, obj_cls):
                return fn(obj)
        return self.fmt_object(obj)

    ############################################################################

    def id_col(self, obj: object) -> FmtFn:
        if not self.ansi:
            return str
        ptr = id(obj)
        return lambda s: _rgb_ptr(ptr, s)

    def fmt_id(self, obj: object, s: str):
        return _rgb_ptr(id(obj), s) if self.ansi else s

    ############################################################################

    def fmt_tuple(self, obj: set) -> str:
        return f'({self.fmt_seq(obj)},)' if obj else '()'

    def fmt_list(self, obj: list) -> str:
        return f'[{self.fmt_seq(obj)}]' if obj else '[]'

    def fmt_set(self, obj: set) -> str:
        return f'set(<{self.fmt_seq(obj)}>)' if obj else 'set()'

    def fmt_dict(self, obj: dict) -> str:
        if not obj:
            return '{}'
        size = len(obj)
        keys = obj.keys
        if size <= 6:
            if all(isinstance(k, str) for k in keys()):
                body = ','.join(f'{k}=…' for k in keys())
                return f'{{{body}}}'
            if all(isinstance(k, (int, bool, str, bytes)) for k in keys()):
                body = ','.join(f'{k!r}:…' for k in keys())
                return f'{{{body}}}'
        return f'{{<{size}>}}'

    def fmt_seq(self, seq: Collection) -> str:
        size = len(seq)
        first = self(next(iter(seq)))
        if size == 1:
            return first
        if size == 2:
            return f'{first}, …'
        return f'{first}, …{size - 1}'

    ############################################################################

    def fmt_reduce(self, obj: object) -> str:
        info = ''
        try:
            _, data, *pos = obj.__reduce__()
            if isinstance(data, tuple) and data:
                info += self.fmt_seq(data)
                if len(pos) == 1:
                    info += 'pos=' + self(pos[0])
        except:
            pass
        return self.fmt_object(obj, info)  # type: ignore

    def fmt_dict_part(self, obj: object) -> str:
        info = ''
        try:
            mapping = getattr(obj, 'mapping', None)
            if mapping is not None:
                info = self(mapping)
        except:
            pass
        return self.fmt_object(obj, info)  # type: ignore

    ############################################################################

    def fmt_call(self, func: str, args: list[tuple[str, object]], k_fn: FmtFn) -> str:
        if len(args) > 6:
            f_items = ''.join(f'\n  {k_fn(k)}={self(v)},' for k, v in args)
            return f'{func}({f_items}\n)'
        f_items = COMMA(f'{k_fn(k)}={self(v)}' for k, v in args)
        return f'{func}({f_items})'

    ############################################################################

    def fmt_union(self, obj: UnionType | _UnionGenericAlias) -> str:  # type: ignore
        info = ''
        try:
            if len(args := obj.__args__) > 1:
                info = self.fmt_ty_args(args, ' | ')
        except Exception:
            pass
        col = self.id_col(obj)
        cname = 'Union' if obj.__class__ is UnionType else '_Union'
        if not info:
            return col(f'<{cname}>')
        return col(f'{cname}[') + info + col(']')

    def fmt_galias(self, obj: GenericAlias | _GenericAlias) -> str:  # type: ignore
        info = ''
        try:
            if hasattr(obj, '__origin__'):
                orig = self.fmt_ty_arg(obj.__origin__)
                args = obj.__args__
                args = self.fmt_ty_args(args, ', ')
                info = f'{orig}[{args}]'
        except Exception:
            pass
        col = self.id_col(obj)
        cname = obj.__class__.__name__
        cname = TY_SHORT.get(cname, cname)
        if not info:
            return col(f'<{cname}>')
        return col(f'{cname}(') + info + col(')')

    def fmt_sform_ty(self, obj: _SpecialForm) -> str:  # type: ignore
        col = self.id_col(obj)
        return col('_SF(') + obj._name + col(')')

    def fmt_ty_args(self, args: tuple, sep: str = ' ') -> str:
        ty_arg = self.fmt_ty_arg
        if args.__class__ is not tuple:
            return '???'
        strs = []
        add = strs.append
        for i, arg in enumerate(args):
            if i >= 2:
                break
            f_arg = ty_arg(arg)
            add(f_arg)
            break
        rem = len(args) - len(strs)
        add(f'…{rem}' if rem > 1 else '…')
        return sep.join(strs)

    def fmt_ty_arg(self, arg: object) -> str:
        cls = arg.__class__
        if cls is type or cls is ABCMeta:
            return self(arg)
        elif issubclass(cls, TY_CLASSES):
            cname = cls.__name__
            cname = TY_SHORT.get(cname) or cname
            return self.fmt_id(arg, cname)
        elif cls is _AnyMeta:
            return self.fmt_id(arg, 'Any')
        else:
            _print(str(arg), end='\n\n')
            return '…'


################################################################################


class DebugFormatter:

    root_path:       str
    avoided_files:   set[str]
    avoided_funcs:   set[int | str]
    fmt_plain:       Stringifier
    fmt_ansi:        Stringifier
    seen:            set[int]


    def __init__(self, *, root_path: str, ansi: bool = True):
        self.root_path = abspath(root_path)
        self.avoided_files = set()
        self.avoided_func_names = set()
        self.avoided_funcs = set()
        self.fmt_plain = Stringifier(PLAIN_DISPATCH, ansi=False)
        self.fmt_ansi = Stringifier(ANSI_DISPATCH, ansi=True)
        self.ansi = ansi and (COLORTERM or not IN_DEBUGGER)
        self.seen = set()

    @property
    def fmt(self) -> Stringifier:
        return self.fmt_ansi if self.ansi else self.fmt_plain

    def fmt_any(self, arg: Any) -> str:
        return self.fmt_ansi(arg) if self.ansi else self.fmt_plain(arg)

    def fmt_args(self, *args) -> str:
        try:
            return ' '.join(map(self.fmt_any, args))
        except Exception as exc:
            return f'<fmt_args: internal error {type(exc).__name__}>'

    def fmt_msg(self, msg: str, *args, **kwargs) -> str:
        fmt = self.fmt
        f_args = [fmt(v) for v in args]
        f_kwargs = {k: fmt(v) for k, v in kwargs.items()}
        return msg.format(*f_args, **f_kwargs)

    def avoid_module(self, module_name: str):
        from pathlib import Path

        if module_name not in sys.modules:
            return
        path = ''
        module = sys.modules[module_name]
        if hasattr(module, '__file__') and module.__file__:
            mod_path = module.__file__
        elif hasattr(module, '__path__'):  # package
            mod_path = module.__path__[0]
        else:
            return
        mod_dir = Path(mod_path).parent
        self.avoided_files.add(mod_dir.as_posix())

    def avoid_file(self, filepath: str):
        self.avoided_files.add(abspath(filepath))

    def avoid_func(self, func: Callable | str):
        fn = func
        add = self.avoided_funcs.add
        if isinstance(func, str):
            add(func)
            return
        while True:
            if isinstance(fn, MethodType):
                add(id(fn))
                fn = fn.__func__
            # elif hasattr(fn, '__wrapped__'):
            #     add(id(fn))
            #     fn = fn.__wrapped__
            elif isinstance(fn, FunctionType):
                add(id(fn))
                break
            else:
                raise TypeError(f'Cannot avoid {func!r}')

    def add_formatter(self, fmt_cls: type, plain_fn: FmtFn, ansi_fn: FmtFn | None = None):
        self.fmt_plain[fmt_cls] = plain_fn
        self.fmt_ansi[fmt_cls] = ansi_fn if ansi_fn else plain_fn

    def see(self, obj: object) -> bool:
        ptr = id(obj)
        if ptr in self.seen:
            return True
        self.seen.add(ptr)
        return False

    ############################################################################

    def use_for_uncaught_exceptions(self) -> None:
        sys.excepthook = self.excepthook

    def excepthook(
        self,
        exc_type: type[BaseException],
        exc_value: BaseException,
        exc_traceback: TracebackType | None,
    ):
        with no_recursion_limit:
            try:
                self.print_caught_exception(exc_value)
            except Exception as fmt_ex:
                fmt_ex_cls = fmt_ex.__class__.__name__
                _print(f'ErrorFormatter.excepthook: error formatting traceback for {fmt_ex_cls}')
                _print('resorting to built-in system excepthook')
                sys.__excepthook__(exc_type, exc_value, exc_traceback)

    ############################################################################

    def print_caught_exception(self, ex: BaseException) -> None:
        with no_recursion_limit:
            style = _EXC_SYS if self.ansi else str
            width = TERM_WIDTH or term_width()
            f_exc = self.fmt_exception(ex, width)
            top = style(justified('UNCAUGHT EXCEPTION', '┏━┓', width))
            bot = style(justified('', '┗━┛', width))
            _print('\n', top, '\n', f_exc, '\n', bot, sep='')

    def panic(self, *args, skip: int = 0, width: int = 0) -> NoReturn:
        with no_recursion_limit:
            try:
                frame = sys._getframe(skip + 1)
                width = width or TERM_WIDTH or term_width()
                f_args = (self.fmt_args(*args), '')
                f_stack = self.fmt_stack(frame, width)
                _print(PANIC_BANNER, *f_args, _PLINE, f_stack, _SLINE, sep='\n', err=True)
                STDOUT.flush()
                STDERR.flush()
            except Exception:
                STDERR.write('panic: internal error while dumping stack\n')
                STDOUT.flush()
            try:
                from os import _exit

                _exit(999)
            except:
                exit(999)

    def print_current_stack(self, *args, skip: int = 0, width: int = 0) -> None:
        with no_recursion_limit:
            try:
                frame = sys._getframe(skip + 1)
                width = width or TERM_WIDTH or term_width()
                f_title = _WARN('CURRENT STACK')
                f_args = self.fmt_args(*args)
                f_stack = self.fmt_stack(frame, width)
                _print(f_title, _SLINE, f_args, f_stack, _SLINE, sep='\n')
            except Exception:
                STDERR.write('print_current_stack: internal error\n')
                STDOUT.flush()

    def print_current_frame(self) -> None:
        with no_recursion_limit:
            frame = sys._getframe(1)
            _print(self.fmt_frame(frame, term_width()))

    def print_all_tasks(self) -> None:
        with no_recursion_limit:
            _print(self.fmt_all_tasks())

    def print_all_threads(self) -> None:
        with no_recursion_limit:
            _print(self.fmt_all_threads())

    def print_tasks(self, task: 'asyncio.Task') -> None:
        with no_recursion_limit:
            _print(self.fmt_task(task))

    def print_coro(self, coro: CoroutineType) -> None:
        with no_recursion_limit:
            _print(self.fmt_coro(coro))

    def print_exception(self, ex: BaseException) -> None:
        with no_recursion_limit:
            self._print_lines(self.exc_lines(ex, term_width()))

    def print_traceback(self, tb: TracebackType) -> None:
        with no_recursion_limit:
            self._print_lines(self.tb_lines(tb, term_width()))

    def print_warning(self, msg: str) -> None:
        with no_recursion_limit:
            msg = f'warning: {msg}'
            _print(_WARN(msg) if self.ansi else msg)

    def _print_lines(self, lines: Lines) -> None:
        w = TERM_WIDTH or term_width()
        lst = []
        add_line = lst.append
        hline = '━' * (w - 2)
        add_line('┏' + hline + '┓')
        for line in lines:
            add_line(line)
        add_line('┗' + hline + '┛')
        sys.stdout.flush()
        _print(*lst, sep='\n')
        sys.stdout.flush()

    ############################################################################

    def push_ansi(self, ansi: bool | None) -> None:
        self._ansi = self.ansi
        if ansi is not None:
            self.ansi = ansi

    def pop_ansi(self) -> None:
        self.ansi = self._ansi

    def fmt_exception(self, ex: BaseException, w: int = 0, ansi: bool | None = None) -> str:
        with no_recursion_limit:
            if not isinstance(ex, BaseException):
                return '<fmt_exception: !BaseException>'
            try:
                self.push_ansi(ansi)
                return self._trim_lines(self.exc_lines(ex, w), w)
            except Exception as exc:
                return f'<fmt_exception: internal error: {type(exc).__name__}>'
            finally:
                self.pop_ansi()

    def fmt_traceback(self, tb: TracebackType, w: int = 0, ansi: bool | None = None) -> str:
        with no_recursion_limit:
            if type(tb) is not TracebackType:
                return '<fmt_traceback: !TracebackType>'
            _ansi = self.ansi
            try:
                self.push_ansi(ansi)
                return self._trim_lines(self.tb_lines(tb, w), w)
            except Exception as exc:
                return f'<fmt_traceback: internal error: {type(exc).__name__}>'
            finally:
                self.pop_ansi()

    def fmt_current_stack(self, *args, skip: int = 0, width: int = 0) -> str:
        with no_recursion_limit:
            frame = sys._getframe(skip + 1)
            f_frame = self.fmt_stack(frame, width)
            if not args:
                return f_frame
            f_args = self.fmt_args(*args)
            return join_nl((_PLINE, f_args, _PLINE, f_frame))

    def fmt_stack(self, frame: FrameType, w: int = 0) -> str:
        with no_recursion_limit:
            if not isinstance(frame, FrameType):
                return '<fmt_stack: !FrameType>'
            try:
                return self._trim_lines(self.stack_lines(frame, w), w)
            except Exception as exc:
                return f'<fmt_stack: internal error: {type(exc).__name__}>'

    def fmt_frame(self, frame: FrameType, w: int = 0) -> str:
        with no_recursion_limit:
            if not isinstance(frame, FrameType):
                return '<fmt_frame: !FrameType>'
            try:
                loc, fun = self._fmt_frame(frame)
                sty = _LOC if self.ansi else str
                trim = self._trim
                if w and len(loc) > w / 2:
                    loc = trim(loc, w)
                    fun = trim(fun, w)
                    return f'{_CALL1}{fun}\n{_CALL2}{sty(loc)}'
                return trim(f'{_CALL1}{sty(loc)} {fun}', w)
            except Exception as exc:
                return f'<fmt_frame: internal error: {type(exc).__name__}>'

    def fmt_task(self, task: 'asyncio.Task', w: int = 0) -> str:
        with no_recursion_limit:
            try:
                return self._trim_lines(self.task_lines(task, w), w)
            except Exception as exc:
                return f'<fmt_task: internal error: {type(exc).__name__}>'

    def fmt_coro(self, coro: CoroutineType, w: int = 0, avoid: str = '') -> str:
        with no_recursion_limit:
            try:
                return self._trim_lines(self.coro_lines(coro, w), w)
            except Exception as exc:
                return f'<fmt_coro: internal error: {type(exc).__name__}>'

    def fmt_all_tasks(self, w: int = 0) -> str:
        with no_recursion_limit:
            from asyncio import all_tasks

            lines = []
            extend = lines.extend
            for task in all_tasks():
                # sys.__stderr__.write('\n')
                # task.print_stack(file=sys.__stderr__)
                # sys.__stderr__.write('\n')
                # sys.__stderr__.flush()
                extend(self.task_lines(task, w))
                extend([''])
            return join_nl(lines)

    def fmt_all_threads(self, w: int = 0) -> str:
        with no_recursion_limit:
            import threading

            lines = []
            for thread in threading.enumerate():
                name, ident, alive, daemon = (
                    thread.name,
                    thread.ident,
                    thread.is_alive(),
                    thread.daemon,
                )
                args = [f'{name=!r}']
                if ident:
                    args.append(f'{ident=!r}')
                if not alive:
                    args.append('alive=False')
                if daemon:
                    args.append('daemon=True')
                lines.append('Thread(' + ','.join(args) + ')')
            return join_nl(lines)

    ############################################################################

    def _trim(self, text: str, w: int = 0) -> str:
        if w == 0 or not TRIM_LINES:
            return text
        if not self.ansi:
            return text[:w]
        return _trim_line(text, w)

    def _trim_lines(self, lines: Lines, w: int) -> str:
        if w == 0 or not TRIM_LINES:
            return join_nl(lines)
        if not self.ansi:
            return join_nl(line[:w] for line in lines)
        return join_nl(_trim_line(line, w) for line in lines)

    ############################################################################

    def exc_lines(self, exc: BaseException, w: int = 0) -> Lines:
        self.seen.clear()
        return self._exc_lines(exc, w)

    def tb_lines(self, tb: TracebackType, w: int = 0) -> Lines:
        self.seen.clear()
        return self._tb_lines(self._tb_frames(tb), w)

    def stack_lines(self, frame: FrameType, w: int = 0) -> Lines:
        self.seen.clear()
        return self._tb_lines(self._stack_frames(frame), w)

    def task_lines(self, task: 'asyncio.Task', w: int = 0) -> Lines:
        global ASYNCIO_PATH
        if not ASYNCIO_PATH:
            import asyncio

            ASYNCIO_PATH = asyncio.__file__.removesuffix('__init__.py')

        cls = type(task)
        if cls.__name__ != 'Task':
            yield '!task'
        task_summary = f'asyncio.Task(name={task.get_name()!r}):'
        yield _BOLD(task_summary) if self.ansi else task_summary

        coro = task.get_coro()
        if isinstance(coro, CoroutineType):
            yield from self.coro_lines(coro, w, ASYNCIO_PATH)
        else:
            yield '<no coroutine stack>'

    def coro_lines(self, coro: CoroutineType, w: int = 0, avoid: str = '') -> Lines:
        if not isinstance(coro, CoroutineType):
            yield '<!coroutine>'
        self.seen.clear()
        avoid_frame = self._avoid_frame
        coro_frames = list(get_coro_stack(coro))
        frames = [f for f in coro_frames if not avoid_frame(f, avoid)]
        frames = frames or coro_frames  # avoid an empty stack
        frames.reverse()
        yield from self._tb_lines(frames, w)

    ############################################################################

    def _fmt_frame(self, frame: FrameType, width: int = 0) -> tuple[str, str]:
        code = frame.f_code
        file = code.co_filename
        line = frame.f_lineno
        if '/JetBrains/' in file:  # for scratch files
            file = file.split('/')[-1]
        loc = f'{file}:{line}'  # .removeprefix(LIB_ROOT)
        name = frame.f_code.co_qualname
        if file == '<string>':
            loc = '<generated code>'
        elif name == '<module>':
            from linecache import getline

            return loc, repr(getline(file, line).rstrip())

        args = frame_call_args(frame)
        f_name = _WHITE(name) if self.ansi else name
        key_fn = _KEY if self.ansi else str
        return loc, self.fmt.fmt_call(f_name, args, key_fn)

    def _exc_lines(self, exc: BaseException, w: int) -> Lines:
        name = type(exc).__name__
        if not isinstance(exc, BaseException):
            yield '!exception: ' + name
            return
        if isinstance(exc, RecursionError):
            yield 'RecursionError; traceback elided'
            return
        traceback = exc.__traceback__
        cause = exc.__cause__
        context = exc.__context__
        notes = getattr(exc, '__notes__', ())

        traceback = traceback if isinstance(traceback, TracebackType) else None
        cause = cause if isinstance(cause, BaseException) else None
        context = context if isinstance(context, BaseException) else None

        str_prop = self._str_lines
        strs_prop = self._strs_lines
        chain_prop = self._chain_lines

        yield from str_prop('exception', name, _EXC_CLS, w)

        if isinstance(exc, SyntaxError) and exc.filename and exc.lineno:
            location = f'{exc.filename}:{exc.lineno}'
            if text := exc.text:
                yield from str_prop('source', text, _MSG, w)
        elif traceback:
            location = frame_location(traceback_frame(traceback), False)
        else:
            location = None

        if location:
            yield from str_prop('location', location, _LOC, w)

        try:
            message = str(exc)
            assert isinstance(message, str)
        except:
            message = "<cannot format exception>"

        if message:
            yield from str_prop('message', message, _MSG, w)

        if notes:
            for i, note in enumerate(notes):
                if isinstance(note, str):
                    yield from str_prop(f'note #{i}', note, _MSG, w)

        if traceback:
            tb_frames = self._tb_frames(traceback)
            yield from strs_prop('traceback', self._tb_lines(tb_frames, w), w)

        w -= 3
        if cause:
            yield from chain_prop('cause', lambda: self._exc_lines(cause, w))  # type: ignore

        if context and context is not cause:
            yield from chain_prop('context', lambda: self._exc_lines(context, w))  # type: ignore

    def _str_lines(self, prop: str, value: str, style: FmtFn, w: int) -> Lines:
        f_prop = _PROP(prop) if self.ansi else prop
        if '\033' in value or not self.ansi:
            style = str
        value = value.strip()
        if not value:
            yield f'{f_prop}: <none>'
        if '\n' not in value:
            if len(prop) + len(value) + 3 < w and (not IN_PYCHARM or prop != 'location'):
                yield f'{f_prop}: {style(value)}'
            else:
                yield ''
                yield f'{f_prop}:'
                yield style(value)
        else:
            if prop != 'exception':
                yield ''
            yield f'{f_prop}:'
            trim = self._trim
            lines = [trim(line) for line in value.splitlines()]
            if lines and style is not str:
                maxw = min(max(map(len, lines)), w)
                for line in lines:
                    yield style(line.ljust(maxw))
            else:
                yield from lines

    def _strs_lines(self, title: str, lines: Lines, w: int) -> Lines:
        styled = _PROP(title) if self.ansi else title
        lines = list(lines)
        if len(lines) == 0:
            yield f'{styled}: <empty>'
            return
        if len(lines) == 1:
            fst = lines[0]
            if len(title) + len(fst) + 3 < w:
                yield f'{styled}: {fst}'
                return
        yield ''
        yield f'{styled}:'
        for line in lines:
            yield line

    def _chain_lines(self, title: str, line_fn: Callable[[], Lines]) -> Lines:
        title = _CHAIN(title) if self.ansi else title
        it = iter(line_fn())
        line = next(it, None)
        if line is None:
            yield f'{title}: <none>'
            return
        yield ''
        yield f'┏━━  {title} ━━━'
        yield '   ' + line
        while True:
            line = next(it, None)
            if line is None:
                break
            yield '   ' + line
        yield ''

    def _tb_lines(self, frames: Iterable[FrameType], w: int) -> Lines:
        see = self.see
        fmt_frame = self._fmt_frame
        fmt_loc = _LOC if self.ansi else str
        locs = []
        addloc = locs.append
        funs = []
        addfun = funs.append
        spill = IN_PYTEST
        for frame in frames:
            if see(frame):
                continue
            loc, fun = fmt_frame(frame)
            spill |= '\n' in fun
            addloc(loc)
            addfun(fun)
        if not locs:
            return
        locw = max(len(loc) for loc in locs)
        if spill or w and locw > w / 2:
            for loc, call in zip(reversed(locs), reversed(funs)):
                lines = list(call.splitlines())
                yield _CALL1 + lines[0]
                yield from lines[1:]
                yield _CALL2 + fmt_loc(loc)
                yield ''
        else:
            for loc, call in zip(locs, funs):
                yield _CALL1 + fmt_loc(loc.ljust(locw)) + ' ┊ ' + call

    ############################################################################

    def _stack_frames(self, frame: FrameType) -> Iterable[FrameType]:
        next_frame = frame

        frames = []
        add_frame = frames.append
        avoid_frame = self._avoid_frame

        while next_frame:
            frame = next_frame
            next_frame = frame.f_back

            if not avoid_frame(frame):
                add_frame(frame)

        frames.reverse()
        return frames

    ############################################################################

    def _tb_frames(self, tb: TracebackType | None) -> Iterable[FrameType]:
        avoid_frame = self._avoid_frame

        see = self.see
        while type(tb) is TracebackType:
            frame = tb.tb_frame
            if see(tb) or avoid_frame(frame):
                pass
            else:
                yield frame
            tb = tb.tb_next

    ############################################################################

    def _avoid_frame(self, frame: FrameType, avoid_dir: str = '') -> bool:
        code = frame.f_code
        filename = code.co_filename
        qualname = code.co_qualname
        file_starts = filename.startswith
        if file_starts(PACKAGE_DIRS):
            rel_path = package_relative_path(filename)
            if rel_path.startswith(SYS_IGNORED_PACKAGES):
                return True
        if file_starts(SYS_IGNORED_FILENAMES):
            return True

        if code.co_name.startswith('raise_'):
            return True
        if qualname.startswith(SYS_IGNORED_QUALNAMES):
            return True
        if avoid_dir and file_starts(avoid_dir):
            return True
        if '<genexpr>' in code.co_qualname:
            return True

        starts = filename.startswith
        if not starts(self.root_path):
            return False
        if any(starts(a) for a in self.avoided_files):
            return True

        avoid_func = self.avoided_funcs.__contains__
        if avoid_func(qualname):
            return True
        if '.<locals>.' in qualname:
            if avoid_func(qualname.split('.<locals>.', 1)[0]):
                return True

        fn = frame_function(frame)
        if avoid_func(id(fn)):
            return True
        if isinstance(fn, MethodType) and avoid_func(id(fn.__func__)):
            return True
        return False


################################################################################

_CODE_RE = re.compile('(\033' + r'\[[0-?]+m)')


def _trim_line(text: str, w: int) -> str:
    if not TRIM_LINES:
        return text
    if w == 0 or len(text) < w:
        return text

    chunks = []
    add = chunks.append
    right = text
    needs_reset = False
    if '\033' not in text:
        return text[:w]
    rem = w
    while True:
        split: list[str] = _CODE_RE.split(right, 1)
        if len(split) == 1:
            add(right[:rem])
            break
        elif len(split) == 3:
            left, code, right = split
        else:
            break
        assert isinstance(left, str)
        rem -= len(left)
        if rem < 0:
            add(left[:rem])
            break
        add(left)
        if rem == 0:
            break
        needs_reset = code != _RESET
        add(code)
    if needs_reset:
        add(_RESET)
    return ''.join(chunks)


def p_int(obj: int) -> str:
    if I48 <= abs(obj) <= I64:
        return f'0x{obj:016x}'
    if I24 <= obj < I48:
        return f'0x{obj:010x}'
    return str(obj)


def p_strlike(obj: str | bytes | bytearray) -> str:
    size = len(obj)
    if size <= 24:
        return repr(obj)
    name = type(obj).__name__
    short = repr(obj[:22])
    short = f'{short[:-2]}…{size - 22}{short[-1]}'
    return f'<{name} {short}>'


def p_function(func: Callable | str) -> str:
    if isinstance(func, str):
        return func
    if hasattr(func, '__qualname__'):
        return func.__qualname__
    elif hasattr(func, '__name__'):
        return func.__name__
    return '<callable>'


def p_method(meth: MethodType) -> str:
    self = meth.__self__
    func = meth.__func__
    self_name = p_type(type(self)) + '.'
    func_name = getattr(func, '__qualname__', '')
    p_self = p_object(self)
    if func_name.startswith(self_name):
        return func_name
    p_func = p_function(func)
    return f'{p_self}.{p_func}'


def p_type(cls: type) -> str:
    if not is_virt_cls(cls) and hasattr(cls, '__short_name__'):
        return cls.__short_name__
    return cls.__qualname__


def p_object(obj: object, extra: str = '') -> str:
    name = p_type(type(obj))
    ptr = id(obj)
    if extra:
        name = name + ' ' + extra
    else:
        info = getattr(obj, '__debug_info_str__', None)
        if callable(info):
            try:
                info_str = info()
                if isinstance(info_str, str):
                    name = name + ' ' + info_str
            except Exception:
                pass
    return f"<{name} @ {ptr:010x}>"


def a_int(obj: int) -> str:
    if I48 <= abs(obj) <= I64:
        return _rgb_hash(obj, f'0x{obj:016x}')
    if I24 <= obj < I48:
        return _rgb_ptr(obj, f'0x{obj:010x}')
    return str(obj)


def a_function(func: Callable | str) -> str:
    return _FUN(p_function(func))


def a_method(meth: MethodType) -> str:
    self = meth.__self__
    func = meth.__func__
    self_name = p_type(type(self)) + '.'
    func_name = getattr(func, '__qualname__', '')
    a_self = a_object(self)
    if func_name.startswith(self_name):
        a_func = a_function(func_name.removeprefix(self_name))
        return f'{a_self}.{a_func}'
    a_func = a_function(func)
    return f'{a_self}.{a_func}'


def a_type(cls: type) -> str:
    if hasattr(cls, '__short_name__'):
        return _CLS(cls.__short_name__)
    return _CLS(cls.__qualname__)


def a_object(obj: object, extra: str = '') -> str:
    cls = type(obj)
    name = p_type(cls)
    if extra:
        name = name + ' ' + extra
    if cls is type or isinstance(obj, type):
        if is_virt_cls(obj):
            name = 'virtual ' + name + f" '{obj.__name__}"
    elif is_virt_obj(obj):
        name = 'virtual ' + name
    elif callable(info := getattr(cls, '__debug_info_str__', None)):
        try:
            if isinstance(res := info(obj), str) and res:
                name = name + ' ' + res
        except Exception:
            pass
    return _rgb_ptr(id(obj), f'<{name}>')


def is_virt_cls(cls: type) -> bool:
    try:
        cls_get(cls, '___vhdl___')
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
cls_get = type.__getattribute__


def _rgb_ptr(ptr: int, s: str) -> str:
    return _rgb_hash(raw_int_hash(ptr), s)


def _rgb_hash(h: int, s: str) -> str:
    r, g, b = (abs(h) & 0xFFFFFF).to_bytes(3)
    return _RGB(r, g, b, s)


COMMA = ', '.join


I24 = 1 << 24
I48 = 1 << 48
I64 = 1 << 64
M57 = (1 << 57) - 1


def raw_int_hash(i: int) -> int:
    n = 0xCBF29CE484222325 ^ i
    n = n ^ (n >> 33)
    n = n * 0xFF51AFD7ED558CCD
    n = n ^ (n >> 33)
    n = n * 0xC4CEB9FE1A85EC53
    n = n ^ (n >> 33)
    return n & M57


# so it doesnt trigger before user fns
class _object: ...


PLAIN_DISPATCH: dict[type, FmtFn] = {
    NoneType:            str,
    bool:                str,
    int:                 p_int,
    str:                 p_strlike,
    bytes:               p_strlike,
    bytearray:           p_strlike,
    FunctionType:        p_function,
    BuiltinFunctionType: p_function,
    MethodType:          p_method,
    type:                p_type,
    _object:             p_object,
}

ANSI_DISPATCH: dict[type, FmtFn] = PLAIN_DISPATCH | {
    int:                 a_int,
    FunctionType:        a_function,
    BuiltinFunctionType: a_function,
    MethodType:          a_method,
    type:                a_type,
    _object:             a_object,
}

join_nl = '\n'.join

_RESET   = '\033[0m'
_RGB     = '\033[38;2;{};{};{}m{}\033[39m'.format

def _ANSI(code: str) -> Callable[..., str]:
    return f'\033[{code}m{{}}\033[0m'.format  # type: ignore

_WARN    = _ANSI('1;43;37')
_ERROR   = _ANSI('1;41;37')
_WHITE   = _ANSI('37')
_RED     = _ANSI('31')
_GREEN   = _ANSI('32')
_YELLOW  = _ANSI('33')
_BLUE    = _ANSI('34')
_MAGENTA = _ANSI('35')
_CYAN    = _ANSI('36')
_BOLD    = _ANSI('1')
_DIM     = _ANSI('2')
_ITALIC  = _ANSI('3')
_UNDER   = _ANSI('4')

_SLINE   = '═' * 50
_PLINE   = '─' * 50
_ALINE   = _DIM(_PLINE)

_PTICK  = '┃  '
_ATICK  = _DIM(_PTICK)
# _PTICKS  = '┌  ', '│  '
# _ATICKS  = _DIM('┌  '), _DIM('│  ')
# colors of actual things
_FUN     = _YELLOW
_PROP    = _ANSI('3;32')
_LOC     = _ANSI('3;90')
_CLS     = _CYAN

_MSG     = _ANSI('1;100')

_KEY     = _ANSI('3;94')
_EXC_SYS = _ANSI('45')
_EXC_CLS = _ANSI('1;35')
_CHAIN   = _ANSI('3;34')

_CALL1   = '' if IN_PYCHARM else '→ '
_CALL2   = '' if IN_PYCHARM else '  '


def term_width() -> int:
    global TERM_WIDTH
    if TERM_WIDTH:
        return TERM_WIDTH
    try:
        TERM_WIDTH = 80
        env_cols = environ.get('COLUMNS', '')
        if env_cols and all(s.isdigit() for s in env_cols.split()):
            TERM_WIDTH = int(env_cols)
        elif IN_PYCHARM:
            TERM_WIDTH = 100
        else:
            TERM_WIDTH = shutil.get_terminal_size().columns
    except Exception:
        pass
    return TERM_WIDTH


def justified(title: str, bg: str, width: int = 0) -> str:
    width = width or TERM_WIDTH or term_width()
    h = (len(bg) - 1) // 2
    l, r = bg[:h], bg[h + 1 :]
    m: str = bg[h]
    line = l + (m * (width - len(l) - len(r))) + r
    if not title:
        return line
    title = ' ' + title + ' '
    x = width // 2 - len(title) // 2
    return line[:x] + title + line[x + len(title) :]


class ColorizeCache(dict[str, str]):
    def __missing__(self, key: str) -> str:
        col = Rgb.hash_str(key)
        res = col.hi(key)
        if len(key) <= 20:
            self[key] = res
        return res


_CCACHE = ColorizeCache()


def colorize(s: str, n: int = 0) -> str:
    if not isinstance(s, str):
        s = str(s)
    if len(s) > 64 or '\033' in s or '\n' in s:
        return s
    s = _CCACHE[s]
    return s + ' ' * (n - len(s)) if n else s


def get_coro_stack(coro: CoroutineType) -> Iterable[FrameType]:
    while type(coro) is CoroutineType:
        if cr_frame := coro.cr_frame:
            while cr_frame:
                yield cr_frame
                cr_frame = cr_frame.f_back
        coro = coro.cr_await


def _package_dirs() -> tuple[str, ...]:
    try:
        import site
        import sysconfig

        packages = site.getsitepackages()
        packages.append(sysconfig.get_path('stdlib'))
        return tuple(abspath(p) for p in packages)
    except:
        return ()


def package_relative_path(filename: str) -> str:
    starts = filename.startswith
    for p_dir in PACKAGE_DIRS:
        if starts(p_dir):
            rel = filename.removeprefix(p_dir).removeprefix('/')
            if 'site-packages' not in rel:
                return rel.replace('/', '.').removesuffix('.py')
    return ''


####################################################################################################

def echoing[C: Callable](fn: C) -> C:
    from .print import nprint
    name = colorize(fn.__name__, 30)
    def wrapped(*args, **kwargs):
        nprint(name, '(', args, kwargs, ')')
        res = fn(*args, **kwargs)
        nprint(name, '->', res)
        return res
    wrapped.__wrapped__ = fn
    wrapped.__name__ = fn.__name__ + '&'
    wrapped.__module__ = getattr(fn, '__module__', 'echoing')
    return wrapped

####################################################################################################

PANIC_BANNER = '''
███████████████
██   PANIC   ██
███████████████
'''

####################################################################################################

PACKAGE_DIRS = _package_dirs()
SYS_IGNORED_PACKAGES = ('pytest', '_pytest', 'pluggy', 'pytest_asyncio', 'asyncio.runners')
SYS_IGNORED_FILENAMES = ('<frozen',)
SYS_IGNORED_QUALNAMES = (
    'Thread._bootstrap',
    'BaseEventLoop.run_until_complete',
)
ASYNCIO_PATH = ''

ROOT_PATH = Path(__file__).parent.parent.as_posix()

####################################################################################################

debug_fmt = DebugFormatter(root_path=ROOT_PATH)

fmt_frame = debug_fmt.fmt_frame
fmt_exception = debug_fmt.fmt_exception
fmt_traceback = debug_fmt.fmt_traceback
fmt_current_stack = debug_fmt.fmt_current_stack

avoid_file = debug_fmt.avoid_file
avoid_function = debug_fmt.avoid_func
avoid_module = debug_fmt.avoid_module

enable_rich_tracebacks = debug_fmt.use_for_uncaught_exceptions

####################################################################################################

NO_REC_LIMIT = 1000
