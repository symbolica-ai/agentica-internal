# fmt: off

import sys
from collections.abc import Callable
from time import time_ns
from typing import ClassVar, NoReturn, Self

from ..color import WARN
from ..debug import fmt_exception

from .log_fns import *

__all__ = [
    'LogContext',
    'CancelMe',
    'is_user_exception',
    'no_log_ctx'
]

###############################################################################

class LogContext:
    LOGGING: ClassVar[bool] = True
    NULL: ClassVar['LogContext']
    PRINT_SLOW: ClassVar[float | int] = 30

    label: str
    title: tuple
    log: Callable[..., None]

    def __init__(self, label: str | tuple[str, str], *title) -> None:
        self.title = title or ()
        self.label = label
        self.log = log_fn(label) if self.LOGGING else no_log_fn

    def __bool__(self) -> bool:
        return True

    def __enter__(self) -> Self:
        self.start_ns = time_ns()
        self.log('(', *self.title, ')')
        return self

    def __call__(self, *args) -> None:
        if self.LOGGING:
            self.log(*args)

    def print(self, *args) -> None:
        log1(self.label, *args)

    def warn(self, *args) -> None:
        self.log(WARN('WARNING:'), *args)

    def vars(self, **kwargs) -> None:
        from ..print import f_multiline_dict
        self.log(f_multiline_dict(kwargs))

    def cancel_outer(self) -> NoReturn:
        raise CancelMe()

    def print_exception(self, exc: BaseException) -> None:
        f_exception = fmt_exception(exc)
        self.print(f_exception)

    def info(self, *args) -> None:
        self.log(*args)

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        nanos = time_ns() - self.start_ns
        secs = nanos / 1e9

        # if secs > LogContext.PRINT_SLOW:
        #   print(f"PRINT_SLOW: {secs:.4f}s TAKEN BY", self.label, file=STDERR)

        if not self.LOGGING:
            return

        after = f'after {secs:.2f}s' if secs > 0.01 else ''
        if exc_type:
            exc_name = exc_type.__name__
            # virtual coroutines methods can return this, don't be noisy with logs
            # if exc_type in UNLOGGED_EXCEPTIONS:
            #     self.log(f'saw {exc_name}')
            #     return
            if 'Cancelled' in exc_name:
                self.log('was cancelled', after)
            elif exc_name == 'WarpShutdown':
                self.log('shutting down due to WarpShutdown', after)
            elif exc_type is CancelMe:
                self.log('chose to cancel; raising CancelledError', after)
                import asyncio

                raise asyncio.CancelledError(f'{self.label} chose to cancel')
            else:
                self.log('experienced exception', exc_name, after, '\n', exc_val)
        else:
            self.log('exited', after) if after else None

###############################################################################

class NoLogContext:

    def __call__(self, *args) -> None: ...

    def __bool__(self) -> bool:
        return False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def print(self, *args) -> None: ...
    def log(self, *args) -> None: ...
    def info(self, *args) -> None: ...
    def warn(self, *args) -> None: ...
    def vars(self, **kwargs) -> None: ...
    def cancel_outer(self) -> NoReturn: ...
    def print_exception(self, exc: BaseException) -> None: ...

no_log_ctx = NoLogContext()

###############################################################################

def is_user_exception(exc: Exception) -> bool:
    if not isinstance(exc, BaseException):
        return False
    exc_name = type(exc).__name__
    if exc_name in ('WarpShutdown', 'CancelMe', 'CancelledError'):
        return False
    if exc_name.startswith('Warp'):
        return False
    return True

###############################################################################

UNLOGGED_EXCEPTIONS = (
    RuntimeError,
    StopIteration,
    AttributeError,
    KeyError,
    ValueError,
    TypeError,
    NameError,
)

STDOUT = sys.stdout
STDERR = sys.stderr
EXIT_BANNER = '█' * 80

###############################################################################

class CancelMe(BaseException):
    pass
