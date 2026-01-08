# fmt: off

import builtins
import sys
import threading
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from typing import NamedTuple, TextIO

__all__ = [
    'SystemHooks',
    'original_print',
    'original_stdout',
    'original_stderr',
    'original_stdin',
]

################################################################################

type PrintFn = Callable[..., None]

# Store the original system values before any REPL manipulates them
_original_stdin = sys.stdin
_original_stdout = sys.stdout
_original_stderr = sys.stderr
_original_print = builtins.print

# Export these for use by other modules that need the true originals
original_stdin = _original_stdin
original_stdout = _original_stdout
original_stderr = _original_stderr
original_print = _original_print

# Thread-local storage for per-thread hooks
_thread_local = threading.local()


def _get_thread_hooks() -> 'SystemHooks | None':
    """Get the hooks for the current thread, or None if not set."""
    return getattr(_thread_local, 'hooks', None)


def _set_thread_hooks(hooks: 'SystemHooks | None') -> None:
    """Set the hooks for the current thread."""
    _thread_local.hooks = hooks


class ThreadLocalTextIO(TextIO):
    """
    A delegating wrapper around TextIO that looks up the actual stream
    from thread-local storage. Falls back to the original stream if no
    thread-local hook is set.
    """
    def __init__(self, attr_name: str, original: TextIO):
        self._attr_name = attr_name
        self._original = original

    def _get_stream(self) -> TextIO:
        hooks = _get_thread_hooks()
        if hooks is not None:
            return getattr(hooks, self._attr_name)
        return self._original

    def write(self, s: str) -> int:
        return self._get_stream().write(s)

    def writelines(self, lines: Iterable[str]) -> None:
        return self._get_stream().writelines(lines)

    def read(self, size: int = -1) -> str:
        return self._get_stream().read(size)

    def readline(self, size: int = -1) -> str:
        return self._get_stream().readline(size)

    def readlines(self, hint: int = -1) -> list[str]:
        return self._get_stream().readlines(hint)

    def flush(self) -> None:
        return self._get_stream().flush()

    def close(self) -> None:
        # Don't close the underlying stream
        pass

    def isatty(self) -> bool:
        return self._get_stream().isatty()

    def readable(self) -> bool:
        return self._get_stream().readable()

    def writable(self) -> bool:
        return self._get_stream().writable()

    def seekable(self) -> bool:
        return self._get_stream().seekable()

    def fileno(self) -> int:
        return self._get_stream().fileno()

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._get_stream().seek(offset, whence)

    def tell(self) -> int:
        return self._get_stream().tell()

    def truncate(self, size: int | None = None) -> int:
        return self._get_stream().truncate(size)

    @property
    def encoding(self) -> str:
        return self._get_stream().encoding

    @property
    def errors(self) -> str | None:
        return self._get_stream().errors

    @property
    def line_buffering(self) -> bool:
        return bool(self._get_stream().line_buffering)

    @property
    def newlines(self):
        return self._get_stream().newlines

    @property
    def buffer(self):
        return self._get_stream().buffer

    @property
    def mode(self) -> str:
        return self._get_stream().mode

    @property
    def name(self):
        return self._get_stream().name

    @property
    def closed(self) -> bool:
        return self._get_stream().closed

    def __iter__(self):
        return iter(self._get_stream())

    def __next__(self):
        return next(self._get_stream())

    def __enter__(self):
        return self._get_stream().__enter__()

    def __exit__(self, *args):
        return self._get_stream().__exit__(*args)


def _thread_local_print(*args, sep: str = ' ', end: str = '\n', file=None, flush: bool = False) -> None:
    """
    Thread-local print function that delegates to the per-thread print hook
    if one is set, otherwise uses the original print.
    """
    hooks = _get_thread_hooks()
    if hooks is not None:
        # Use the thread-local print function
        hooks.print_fn(*args, sep=sep, end=end, file=file, flush=flush)
    else:
        # Fall back to original print
        _original_print(*args, sep=sep, end=end, file=file, flush=flush)


# Install thread-local wrappers once at import time
# This ensures that sys.stdout etc. always delegate to thread-local hooks
_delegating_stdin = ThreadLocalTextIO('stdin', _original_stdin)
_delegating_stdout = ThreadLocalTextIO('stdout', _original_stdout)
_delegating_stderr = ThreadLocalTextIO('stderr', _original_stderr)

sys.stdin = _delegating_stdin  # type: ignore
sys.stdout = _delegating_stdout  # type: ignore
sys.stderr = _delegating_stderr  # type: ignore
builtins.print = _thread_local_print

################################################################################


class SystemHooks(NamedTuple):
    """
    Represents the changes of global Python state that must be made during
    a REPL execution.

    Make a desired state with `state = SystemHooks.make(...)`.

    Temporarily apply it with `with state.applied(): ...`

    Permanently apply it with `state.set()`.

    Get the current system state with `SystemHooks.get()`.
    
    NOTE: Hooks are now thread-local. Each thread has its own set of hooks,
    preventing concurrent sandboxes from interfering with each other's stdout.
    """

    stdin:           TextIO
    stdout:          TextIO
    stderr:          TextIO
    print_fn:        PrintFn
    recursion_limit: int

    @staticmethod
    def make(
            stdin: TextIO,
            stdout: TextIO,
            stderr: TextIO, *,
            print_fn: PrintFn = builtins.print,
            recursion_limit: int = 0) -> 'SystemHooks':

        return SystemHooks(
            stdin, stdout, stderr,
            print_fn,
            recursion_limit,
        )

    def set(self) -> None:
        """
        Set the hooks for the current thread.
        
        This is now thread-local, so concurrent threads can have different hooks
        without interfering with each other.
        """
        _set_thread_hooks(self)
        # Ensure sys.stdin/stdout/stderr are always our delegating wrappers
        # (user code might have reassigned them)
        sys.stdin = _delegating_stdin
        sys.stdout = _delegating_stdout
        sys.stderr = _delegating_stderr
        builtins.print = _thread_local_print
        # Recursion limit is still process-global, but that's generally safe
        if self.recursion_limit:
            sys.setrecursionlimit(self.recursion_limit)

    @staticmethod
    def get() -> 'SystemHooks':
        """
        Get the current hooks for this thread.
        
        If no thread-local hooks are set, returns the original system values.
        """
        hooks = _get_thread_hooks()
        if hooks is not None:
            return hooks
        rec_limit = sys.getrecursionlimit()
        return SystemHooks(
            _original_stdin, _original_stdout, _original_stderr,
            _original_print,
            rec_limit,
        )

    @staticmethod
    def clear() -> None:
        """Clear the thread-local hooks, reverting to original system streams."""
        _set_thread_hooks(None)
        # Ensure sys.stdin/stdout/stderr are always our delegating wrappers
        # (user code might have reassigned them)
        sys.stdin = _delegating_stdin
        sys.stdout = _delegating_stdout
        sys.stderr = _delegating_stderr
        builtins.print = _thread_local_print

    @contextmanager
    def applied(self):
        old = SystemHooks.get()
        self.set()
        try:
            yield
        finally:
            if old == SystemHooks(
                _original_stdin, _original_stdout, _original_stderr,
                _original_print, old.recursion_limit
            ):
                # If old was the original state, clear instead
                SystemHooks.clear()
            else:
                old.set()
