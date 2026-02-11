################################################################################

from typing import overload, Any, Iterable, Literal
from collections.abc import Iterable

################################################################################

__classes__ = [
    '_SupportsCeil',
    '_SupportsFloor',
    '_SupportsProdWithNoDefaultGiven',
    '_SupportsTrunc',
]

__functions__ = [
    'acos',
    'acosh',
    'asin',
    'asinh',
    'atan',
    'atan2',
    'atanh',
    'ceil',
    'ceil',
    'comb',
    'copysign',
    'cos',
    'cosh',
    'degrees',
    'dist',
    'erf',
    'erfc',
    'exp',
    'expm1',
    'fabs',
    'factorial',
    'floor',
    'floor',
    'fmod',
    'frexp',
    'fsum',
    'gamma',
    'gcd',
    'hypot',
    'isclose',
    'isinf',
    'isfinite',
    'isnan',
    'isqrt',
    'lcm',
    'ldexp',
    'lgamma',
    'log',
    'log10',
    'log1p',
    'log2',
    'modf',
    'perm',
    'pow',
    'prod',
    'prod',
    'prod',
    'radians',
    'remainder',
    'sin',
    'sinh',
    'sqrt',
    'tan',
    'tanh',
    'trunc',
    'ulp',
]

__aliases__ = ['_SupportsFloatOrIndex', '_PositiveInteger', '_NegativeInteger']

__annos__ = []

__constants__ = []

__all__ = [
    'SupportsCeil',
    'SupportsFloor',
    'SupportsProdWithNoDefaultGiven',
    'SupportsTrunc',
    'acos',
    'acosh',
    'asin',
    'asinh',
    'atan',
    'atan2',
    'atanh',
    'ceil',
    'comb',
    'copysign',
    'cos',
    'cosh',
    'degrees',
    'dist',
    'erf',
    'erfc',
    'exp',
    'expm1',
    'fabs',
    'factorial',
    'floor',
    'fmod',
    'frexp',
    'fsum',
    'gamma',
    'gcd',
    'hypot',
    'isclose',
    'isinf',
    'isfinite',
    'isnan',
    'isqrt',
    'lcm',
    'ldexp',
    'lgamma',
    'log',
    'log10',
    'log1p',
    'log2',
    'modf',
    'perm',
    'pow',
    'prod',
    'radians',
    'remainder',
    'sin',
    'sinh',
    'sqrt',
    'tan',
    'tanh',
    'trunc',
    'ulp',
]

################################################################################


class _SupportsCeil:
    def __ceil__(self) -> Any: ...


################################################################################


class _SupportsFloor:
    def __floor__(self) -> Any: ...


################################################################################


class _SupportsProdWithNoDefaultGiven:
    pass


################################################################################


class _SupportsTrunc:
    def __trunc__(self) -> Any: ...


################################################################################


def acos(x: float | int, /) -> float: ...


def acosh(x: float | int, /) -> float: ...


def asin(x: float | int, /) -> float: ...


def asinh(x: float | int, /) -> float: ...


def atan(x: float | int, /) -> float: ...


def atan2(y: float | int, x: float | int, /) -> float: ...


def atanh(x: float | int, /) -> float: ...


@overload
# pyrefly: ignore[invalid-overload]
def ceil(x: _SupportsCeil, /) -> Any: ...


@overload
# pyrefly: ignore[invalid-overload]
def ceil(x: float | int, /) -> int: ...


def comb(n: int, k: int, /) -> int: ...


def copysign(x: float | int, y: float | int, /) -> float: ...


def cos(x: float | int, /) -> float: ...


def cosh(x: float | int, /) -> float: ...


def degrees(x: float | int, /) -> float: ...


def dist(p: Iterable[float | int], q: Iterable[float | int], /) -> float: ...


def erf(x: float | int, /) -> float: ...


def erfc(x: float | int, /) -> float: ...


def exp(x: float | int, /) -> float: ...


def expm1(x: float | int, /) -> float: ...


def fabs(x: float | int, /) -> float: ...


def factorial(x: int, /) -> int: ...


@overload
# pyrefly: ignore[invalid-overload]
def floor(x: _SupportsFloor, /) -> Any: ...


@overload
# pyrefly: ignore[invalid-overload]
def floor(x: float | int, /) -> int: ...


def fmod(x: float | int, y: float | int, /) -> float: ...


def frexp(x: float | int, /) -> tuple: ...


def fsum(seq: Iterable[float | int], /) -> float: ...


def gamma(x: float | int, /) -> float: ...


def gcd(*integers: int) -> int: ...


def hypot(*coordinates: float | int) -> float: ...


def isclose(
    a: float | int, b: float | int, *, rel_tol: float | int = 1e-09, abs_tol: float | int = 0.0
) -> bool: ...


def isinf(x: float | int, /) -> bool: ...


def isfinite(x: float | int, /) -> bool: ...


def isnan(x: float | int, /) -> bool: ...


def isqrt(n: int, /) -> int: ...


def lcm(*integers: int) -> int: ...


def ldexp(x: float | int, i: int, /) -> float: ...


def lgamma(x: float | int, /) -> float: ...


def log(x: float | int, base: float | int = ...) -> float: ...


def log10(x: float | int, /) -> float: ...


def log1p(x: float | int, /) -> float: ...


def log2(x: float | int, /) -> float: ...


def modf(x: float | int, /) -> tuple: ...


def perm(n: int, k: int | None = None, /) -> int: ...


def pow(x: float | int, y: float | int, /) -> float: ...


@overload
# pyrefly: ignore[invalid-overload]
def prod(iterable: Iterable[bool | int], /, *, start: int = 1) -> int: ...


@overload
# pyrefly: ignore[invalid-overload]
def prod(iterable: Iterable, /) -> Any | Literal[1]: ...


@overload
# pyrefly: ignore[invalid-overload]
def prod(iterable: Iterable, /, *, start: Any) -> Any: ...


def radians(x: float | int, /) -> float: ...


def remainder(x: float | int, y: float | int, /) -> float: ...


def sin(x: float | int, /) -> float: ...


def sinh(x: float | int, /) -> float: ...


def sqrt(x: float | int, /) -> float: ...


def tan(x: float | int, /) -> float: ...


def tanh(x: float | int, /) -> float: ...


def trunc(x: _SupportsTrunc, /) -> Any: ...


def ulp(x: float | int, /) -> float: ...
