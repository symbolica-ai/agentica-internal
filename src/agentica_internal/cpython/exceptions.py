# fmt: off

from collections.abc import Callable
from collections import deque

__all__ = [
    'ExceptionClass',
    'get_exception_args',
    'get_exception_str',
    'get_exception_bases',
]

################################################################################

def get_exception_args(exc: BaseException) -> tuple | None:

    cls = type(exc)

    # first try exc.args
    try:
        args = exc.args
        assert type(args) is tuple
        cls(*args)
        return args
    except:
        pass

    # next try exc.__reduce__ args
    try:
        reduce = exc.__reduce__()
        recon = reduce[0]
        args = reduce[1]
        assert type(args) is tuple
        assert type(recon(*args)) is cls
        return args
    except Exception as e:
        print(e)
        pass

    # next try exc.__getstate__ (works for JSONDecodeError)
    try:
        state = exc.__getstate__()
        if isinstance(state, dict):
            args = tuple(state.values())
            cls(*args)
            return args
        if isinstance(state, tuple):
            args = state
            cls(*args)
            return args
    except:
        pass

    return None


################################################################################

def get_exception_str(exc: BaseException, max_len: int = 1024) -> str | None:
    try:
        text = str(exc)
        assert type(text) is str
        return text[:max_len-3] + '...' if len(text) > max_len else text
    except:
        return None


################################################################################

type ExceptionClass = type[BaseException]

def get_exception_bases(cls: ExceptionClass, test: Callable[[type], bool]) -> list[ExceptionClass]:
    bases = []
    visit = deque()
    visit.append(cls)
    while visit:
        b = visit.popleft()
        if bases and any(issubclass(z, b) for z in bases):
            pass  # if a base we've already collected is <: b, skip b
        elif b is BaseException or test(b):
            bases.append(b)
        else:
            visit.extend(
                c for c in b.__bases__
                if issubclass(c, BaseException) and c not in bases
            )
    return bases
