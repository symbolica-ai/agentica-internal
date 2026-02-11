from asyncio import CancelledError, InvalidStateError

from agentica_internal.core.result import Result
from agentica_internal.core.sentinels import *
from agentica_internal.testing import *
from agentica_internal.warpc.messages import *
from agentica_internal.warpc.pure import PURE_CODEC

EXCEPTIONS = [
    AttributeError("A"),
    KeyError("B"),
    ValueError("C"),
    TypeError("D"),
    NameError("E"),
    TimeoutError("F"),
    CancelledError("G"),
    InvalidStateError("H"),
]


def verify_exception_msg(exc_msg: ExceptionMsg):
    assert isinstance(exc_msg, SystemExceptionMsg), f"invalid {exc_msg=!r}"
    cls_msg = exc_msg.exc_cls
    assert isinstance(cls_msg, SystemResourceMsg), f"invalid {cls_msg=!r}"
    cls = cls_msg.sys_cls
    assert isinstance(cls, type) and issubclass(cls, BaseException), f"invalid {cls=!r}"
    args = exc_msg.exc_args
    assert isinstance(args, tuple) and len(args) == 1, f"invalid {args=!r}"
    assert isinstance(args[0], StrMsg), f"invalid arg[0] {args[0]=!r}"


def verify_error_result(exc: Exception):
    result = Result.bad(exc)
    result_msg = ResultMsg.encode(result, PURE_CODEC)
    assert result_msg.is_err, f"invalid {result_msg=!r}"
    exc_msg = result_msg.error
    verify_exception_msg(exc_msg)


def verify_error_results():
    run_object_tests(verify_error_result, EXCEPTIONS)


def verify_unavailable_result(reason):
    result = Result.unavailable(reason)
    result_msg = ResultMsg.encode(result, PURE_CODEC)
    assert result_msg.is_unavailable, f"invalid {result_msg=!r}"
    result_2 = result_msg.decode(PURE_CODEC)
    assert result_2.is_unavailable, f"invalid {result_msg=!r}"
    assert result_2 is result


def verify_unavailable_errors():
    run_object_tests(verify_unavailable_result, [None, PENDING, CANCELED, ERRORED])


if __name__ == '__main__':
    verify_error_results()
    verify_unavailable_errors()
