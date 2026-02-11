# fmt: off
import asyncio

from collections.abc import Callable, Iterable
from functools import wraps
from os import getcwd, _exit
from pathlib import Path
from typing import TypedDict, Unpack, Literal, TYPE_CHECKING
from sys import getrecursionlimit, setrecursionlimit

from ...core.print import print_exception, print_current_stack
from ...core.debug import fmt_exception, exception_location
from ...core.color import RED, BLUE, GREEN, YELLOW, BOLD, ITALIC, UNDER, DIM
from ...core.fns import glob_match_
from ...core.fmt import idsafe_str, f_idsafe

from ...cpython.inspection import callable_location

from .tst_storage import FileTemplate
from .tst_ids import ObjectNamer
from .tst_counts import TestCounts

__all__ = [
    'TestOptions',
    'run_object_to_file_tests',
    'run_object_tests',
    'run_test_loop',
    'print_diff',
    'print_sep',
    'print_path',
    'GLOBAL_COUNTS',
]

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest


TEST_DIR = Path(__file__).parent.parent

RESULTS_TEMPLATE = FileTemplate('{func}.results', section='{kind}:{name}')
TRACEBACKS_TEMPLATE = FileTemplate('{func}.tracebacks', '{name}.traceback')

GLOBAL_COUNTS = TestCounts()

CWD = Path(getcwd()).as_posix()
OVERWRITE: bool = False
RUNNING: bool = False

type Span = int | tuple[int, int] | None

type ErrorMode = Literal['exit', 'print', 'save']

class TestOptions(TypedDict):
    title: str
    subtitle: str
    limit: int
    overwrite: bool
    span: Span
    exceptions: Iterable[type[BaseException]]
    on_error: ErrorMode
    tracebacks_path: FileTemplate
    rec_limit: int
    skipping: str | set[str] | None
    pytest_request: 'FixtureRequest | None'
    stall_alarm: int | None
    names: Iterable[str] | None
    include_name: bool


class TestError(Exception): ...
class TestFail(Exception): ...
class TestSkip(Exception): ...
class TestFileCreated(Exception): ...
class TestFileDiffered(Exception):

    def __str__(self):
        file, act, exp = self.args
        return f'TestFileDiffered("{file}", ...)'

def save_traceback(tb_file: Path, exc: BaseException) -> None:
    tb_file.parent.mkdir(parents=True, exist_ok=True)
    f_exc = fmt_exception(exc, ansi=False)
    tb_file.write_text(f_exc)


def run_object_tests[X](
    test_fn: Callable[[object], X],
    *arguments: Iterable[X],
    include_name: bool = False,
    **opts: Unpack[TestOptions]
):

    __tracebackhide__ = True  # for pytest

    assert callable(test_fn), f"test_fn={type(test_fn)!r} is not callable"

    if asyncio.iscoroutinefunction(test_fn):
        def fn(*args, **kwargs):
            __tracebackhide__ = True  # for pytest
            return asyncio.run(test_fn(*args, **kwargs))
        fn.__wrapped__ = test_fn
    else:
        fn = test_fn

    run_test_loop(fn, arguments, include_name=include_name, **opts)


def run_object_to_file_tests[X, Y](
    test_fn: Callable[[X], Y],
    *arguments: Iterable[X],
    str_fn: Callable[[Y], str] = f_idsafe,
    results_file: FileTemplate = RESULTS_TEMPLATE,
    exceptions: Iterable[type[BaseException]] = (),
    rec_limit: int = 128,
    include_name: bool = True,
    **opts: Unpack[TestOptions]):

    __tracebackhide__ = True  # for pytest

    assert callable(test_fn), f"test_fn={test_fn!r} is not callable"
    assert callable(str_fn), f"str_fn={str_fn!r} is not callable"
    assert isinstance(results_file, FileTemplate), f"file_template={results_file!r} is not a FileTemplate"

    func_name = test_fn.__name__

    @wraps(test_fn)
    def object_to_file_test_fn(fullname: str, obj: X):

        __tracebackhide__ = True  # for pytest

        if ':' in fullname:
            kind, name = fullname.split(':', 1)
        else:
            kind, name = '__', fullname

        file = results_file.format(func=func_name, kind=kind, name=name)
        old_limit = getrecursionlimit()

        try:
            setrecursionlimit(rec_limit)
            result = test_fn(obj)
            actual = str_fn(result)

        except BaseException as exc:
            if exc not in exceptions:
                raise
            try:
                actual = idsafe_str(repr(exc))
            except BaseException:
                actual = type(exc).__name__ + '(...)'
        finally:
            setrecursionlimit(old_limit)

        assert type(actual) is str, f"output was an <{type(actual).__name__}>, not a string"

        if not file.exists():
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(actual)
            raise TestFileCreated(file)

        expected = file.read_text()
        if expected != actual:
            raise TestFileDiffered(file, actual, expected)

    run_test_loop(object_to_file_test_fn, arguments, include_name=include_name, **opts)


def run_test_loop(
    test_fn: Callable,
    arguments: tuple[Iterable, ...],
    title: str = '',
    subtitle: str = '',
    limit: int = 0,
    overwrite: bool = False,
    span: Span = None,
    tracebacks_path: FileTemplate = TRACEBACKS_TEMPLATE,
    include_name: bool = True,
    on_error: ErrorMode = 'halt',
    skipping: str | set[str] | None = None,
    pytest_request: 'FixtureRequest | None' = None,
    stall_alarm: int | None = None,
    names: Iterable[str] | None = None
    ):

    __tracebackhide__ = True  # for pytest

    assert isinstance(tracebacks_path, FileTemplate), f"tracebacks_path={tracebacks_path!r} is not a FileTemplate"
    assert tracebacks_path.section is None, "tracebacks_path cannot be sectioned"

    global OVERWRITE
    global RUNNING

    arguments = [tuple(a) for a in arguments]
    sizes = tuple(len(a) for a in arguments)
    assert len(set(sizes)) == 1
    size = sizes[0]

    if names is None:
        namer = ObjectNamer(path_safe=True)
        names = tuple(map(namer, arguments[0]))
    else:
        names = tuple(names)
        assert len(names) == size

    tuples = list(zip(*arguments))

    OVERWRITE = overwrite
    files = []
    passed = []
    failed = []
    created = []
    errored = []
    to_lst = {'P': passed, 'F': failed, 'C': created, 'E': errored}
    to_col = {'P': GREEN, 'F': RED, 'C': BLUE, 'E': YELLOW}
    to_tag = {'P': 'passed', 'F': 'failed', 'C': 'created', 'E': 'errors'}
    to_col_tag = {k: to_col[k](to_tag[k], 8) for k in ('P', 'F', 'C', 'E')}

    fn_name = getattr(test_fn, '__wrapped__', test_fn).__name__
    title = title or f'Running test function {fn_name!r} over {size} inputs'

    print_path(callable_location(test_fn))
    print(UNDER(title))
    print(YELLOW(subtitle)) if subtitle else None

    verbose = pytest_request is None
    error = None
    failure = None

    skip_fn = glob_match_(skipping, False)
    if stall_alarm is not None:
        import signal
        signal.signal(signal.SIGALRM, stall_handler)
        signal.alarm(stall_alarm)

    def run_test_i(i: int, name: str, args: tuple):

        __tracebackhide__ = True  # for pytest

        nonlocal limit, error, failure

        if isinstance(span, int):
            if i != span:
                return 'S'
        elif isinstance(span, tuple):
            a, b = span
            if not (a <= i <= b):
                return 'S'
        elif skip_fn(name):
            return 'S'

        res = 'P'
        ext = ''
        error = None
        failure = None
        file = None

        tb_file = tracebacks_path.format(func=fn_name, name=name, index=str(i))
        if tb_file.exists():
            tb_file.unlink()
            tb_dir = tb_file.parent
            if not any(tb_dir.iterdir()):
                tb_dir.rmdir()

        try:
            if include_name:
                test_fn(name, *args)
            else:
                test_fn(*args)

        except TestFileCreated as e:
            file = e.args[0]
            created.append(file)
            res = 'C'
            failure = e
        except TestFileDiffered as e:
            file, act, exp = e.args
            print()
            print_diff(exp, act, title=file)
            res = 'F'
            failure = e
        except SystemExit as e:
            print_exception(e)
            _exit(999)
        except BaseException as exc:

            error = exc
            e_loc = exception_location(exc)
            e_cls = exc.__class__.__name__
            e_str = f'{e_cls}: {exc}'
            if e_loc:
                ext = f'{e_loc}\n{e_str}'
                e_tst = isinstance(exc, AssertionError) and ('/testing/' in e_loc or 'test_' in e_loc)
                failure = e_tst
            else:
                e_tst = False

            res = 'F' if e_tst else 'E'

            if not e_tst and not on_error.startswith('i'):
                save_traceback(tb_file, exc)
                if on_error.startswith('e'):
                    print(f'\n\nException during test #{i}:{name}')
                    print_exception(exc)
                    _exit(999)
                elif on_error.startswith('s'):
                    pass
                elif on_error.startswith('p'):
                    print_exception(exc)

        col_tag = to_col_tag[res]

        if file and res != 'P':
            files.append(str(file) + ' ' + col_tag.strip())

        to_lst[res].append(name)
        print(f'{i:<4}', col_tag, name, sep='') if verbose else None

        if ext:
            for line in ext.splitlines():
                print(' ' * 11, YELLOW(line))

        if res != 'P':
            limit -= 1
            if limit == 0:
                print('*' * 50)
                print('limit reached')
                return 'B'

        return res

    try:
        RUNNING = True
        if pytest_request is not None:
            import pytest
            subtests = pytest_request.getfixturevalue('subtests')
            for i, (name, args) in enumerate(zip(names, tuples)):
                with subtests.test(msg=name):
                    match run_test_i(i, name, args):
                        case 'P':
                            continue
                        case 'S':
                            pytest.skip()
                        case 'C':
                            pytest.fail(f'test created; run again', pytrace=False)
                        case 'B':
                            break
                        case 'E':
                            pytest.fail(f'caught {type(error).__name__}', pytrace=False)
                        case 'F':
                            raise failure  # pytest will turn this into a failure
            return

        for i, (name, args) in enumerate(zip(names, tuples)):
            if run_test_i(i, name, args) == 'break':
                break
    finally:
        RUNNING = False

    counts = TestCounts(len(passed), len(failed), len(created), len(errored))
    GLOBAL_COUNTS.add_from(counts)

    if files:
        print()
        print(ITALIC('non-passing files:'))
        for file in files:
            print_path(file)
    print()


def stall_handler(signum, frame):
    if RUNNING:
        print_current_stack()
        _exit(20)


def save_diff(file_e: Path, expected: str, actual: str):
    file_a = file_e.with_suffix('.actual' + file_e.suffix)
    file_o = file_e.with_suffix('.expect' + file_e.suffix)
    if expected == actual:
        if file_a.exists():
            file_a.unlink()
        if file_o.exists() and file_o.read_text() == expected:
            file_o.unlink()
        return

    if OVERWRITE:
        if not file_o.exists():
            file_o.write_text(expected)
        file_e.write_text(actual)
    else:
        file_a.write_text(actual)

    print_sep()
    print_path(str(file_e))
    print_path(str(file_a))
    print_diff(expected, actual)


# def save_diff_pair(
#     actual_a: str,
#     actual_b: str,
#     file_e: Path,
#     suffix_a: str,
#     suffix_b: str,
# ):
#     expected = file_e.read_text() if file_e.exists() else None
#     file_a = file_e.with_suffix(suffix_a + file_e.suffix)
#     file_b = file_e.with_suffix(suffix_b + file_e.suffix)
#     if file_a.exists():
#         file_a.unlink()
#     if file_b.exists():
#         file_b.unlink()
#     if expected is None:
#         if actual_a == actual_b:
#             file_e.write_text(actual_a)
#         else:
#             file_a.write_text(actual_a)
#             file_b.write_text(actual_b)
#             print_sep()
#             print_path(str(file_a))
#             print_path(str(file_b))
#             print_diff(actual_a, actual_b)
#         return
#
#     if actual_a != expected:
#         file_a.write_text(actual_a)
#         print_sep()
#         print_path(str(file_e))
#         print_path(str(file_a))
#         print_diff(expected, actual_a)
#
#     if actual_b != expected:
#         file_b.write_text(actual_b)
#         print_sep()
#         print_path(str(file_e))
#         print_path(str(file_b))
#         print_diff(expected, actual_b)


def print_diff(a: str, b: str, title: str = ''):
    if a == b:
        return
    from difflib import unified_diff

    diff = unified_diff(
        a.splitlines(keepends=True),
        b.splitlines(keepends=True),
    )
    if title:
        print(BOLD(str(title)))
    else:
        print_sep()
    for i, line in enumerate(diff):
        if i <= 2:
            continue
        char = line[0]
        line = '▌ ' + line[1:].rstrip()
        if char == '+':
            print(GREEN(line))
        elif char == '-':
            print(RED(line))
        else:
            print(DIM(line))
    print_sep()


def print_sep():
    print('┈' * 50)

def print_path(file: str):
    file = str(file).removeprefix(CWD + '/')
    if not file.startswith('/'):
        file = './' + file
    print(DIM(file))


def _tests_dir_for(file: str) -> Path:
    assert file.endswith('.py')
    path = Path(file)
    assert path.exists()
    return path.with_suffix('')
