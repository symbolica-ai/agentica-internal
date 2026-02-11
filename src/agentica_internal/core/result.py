# fmt: off

from typing import Any, NamedTuple, TYPE_CHECKING

from .sentinels import *

__all__ = [
    'Result',
    'set_future_result',
    'get_future_result',
    'EMPTY_RESULT',
    'NO_RESULT',
    'PENDING_RESULT',
    'CANCELED_RESULT',
    'ERRORED_RESULT'
]

################################################################################

if TYPE_CHECKING:
    import asyncio

################################################################################

class Result(NamedTuple):
    done: bool
    value: Any
    error: BaseException | None

    ################################################################################

    @staticmethod
    def good(value: Any) -> 'Result':
        if value is None:
            return EMPTY_RESULT
        return Result(True, value, None)

    @staticmethod
    def bad(exc: BaseException) -> 'Result':
        return Result(True, ERRORED, exc)

    @staticmethod
    def unavailable(reason: Pending | Canceled | Errored | None = None) -> 'Result':
        if reason is PENDING:  return PENDING_RESULT
        if reason is CANCELED: return CANCELED_RESULT
        if reason is ERRORED:  return ERRORED_RESULT
        return NO_RESULT

    ############################################################################

    @staticmethod
    def from_triple(done: bool, value: Any, error: BaseException) -> 'Result':
        if not done:
            assert error is None
            return Result.unavailable(value)
        if error is None:
            if value is None:
                return EMPTY_RESULT
            return Result(True, value, None)
        else:
            return Result(True, ERRORED, error)

    ############################################################################

    @staticmethod
    def from_future(future: 'asyncio.Future') -> 'Result':
        return get_future_result(future)

    def into_future(self, future: 'asyncio.Future') -> None:
        set_future_result(future, self)

    ############################################################################

    @property
    def is_ok(self) -> bool:
        return self.done and self.error is None

    @property
    def is_err(self) -> bool:
        return self.done and self.error is not None

    @property
    def is_unavailable(self) -> bool:
        return not self.done

    @property
    def is_pending(self) -> bool:
        return not self.done and self.value is PENDING

    @property
    def is_canceled(self) -> bool:
        return not self.done and self.value is CANCELED

    @property
    def is_completed(self) -> bool:
        return self.done

    @property
    def sentinel(self) -> Sentinel | None:
        val = self.value
        return val if isinstance(val, Sentinel) else None

    def realize(self) -> Any:
        err = self.error
        val = self.value
        if not self.done:
            if is_sentinel(val):
                raise RuntimeError(f'result not available: {val}')
            raise RuntimeError('result not available')
        if err is not None:
            raise self.error
        return self.value

    def summary_str(self, width: int) -> str:
        from .fmt import f_object_id

        if self.is_err:
            f_error = f_object_id(self.error, width)
            return f'bad({f_error})'

        val = self.value

        if not self.done:
            return f'unavailable({val})'

        if type(val) is tuple:
            f_val = ', '.join(f_object_id(v, width//4) for v in val[:5])
            if len(val) > 5:
                f_val += ', ...'
            f_val = f'({f_val})'
        elif type(val) is str and len(val) <= width:
            f_val = repr(val)
        else:
            f_val = f_object_id(val, width)
        return f'good({f_val})'

    def __repr__(self) -> str:
        return self.summary_str(width=512)

    def __str__(self) -> str:
        return 'Result.' + self.summary_str(width=64)


################################################################################

def get_future_result(future: 'asyncio.Future') -> Result:
    if not future.done():
        return PENDING_RESULT
    elif future.cancelled():
        return CANCELED_RESULT
    elif (exception := future.exception()) is not None:
        return Result.bad(exception)
    else:
        return Result.good(future.result())

def set_future_result(future: 'asyncio.Future', result: Result) -> None:
    if result is PENDING_RESULT:
        return
    elif result is CANCELED_RESULT:
        future.cancel()
    elif result.is_err:
        future.set_exception(result.error)
    else:
        future.set_result(result.value)

###############################################################################

EMPTY_RESULT    = Result(True, None, None)

###############################################################################

NO_RESULT       = Result(False, None, None)
PENDING_RESULT  = Result(False, PENDING, None)
CANCELED_RESULT = Result(False, CANCELED, None)
ERRORED_RESULT  = Result(False, ERRORED, None)

SENT_TO_RES = {PENDING: PENDING_RESULT, CANCELED: CANCELED_RESULT, ERRORED: ERRORED_RESULT}

# NOTE: Result.unavailable(PENDING) will return the singleton PENDING_RESULT, etc.
# ERRORED_RESULT is for out-of-band errors, unlike Result.bad(exception) which is
# to represent a computation that raised an exception which we wish to represent.
