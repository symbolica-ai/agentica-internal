# fmt: off

from typing import Self, ClassVar
from datetime import date, timedelta

from .vshared import *
from .vmethods import *

_int = int  # should be typing.SupportsIndex

################################################################################

class _date(date):

    min:        ClassVar[date]
    max:        ClassVar[date]
    resolution: ClassVar[timedelta]

    def __new__(cls,
                year: _int = ARG_DEFAULT,
                month: _int = ARG_DEFAULT,
                day: _int = ARG_DEFAULT) -> Self:
        return date.__new__(cls, 2026, 1, 1)

    ############################################################################

    @ro_property
    def year(self) -> int: ...

    @ro_property
    def month(self) -> int: ...

    @ro_property
    def day(self) -> int: ...

    ############################################################################

    @classmethod
    def today(cls) -> Self: ...

    @classmethod
    def fromtimestamp(cls, timestamp: float, /) -> Self: ...

    @classmethod
    def fromordinal(cls, n: int, /) -> Self: ...

    @classmethod
    def fromisoformat(cls, date_string: str, /) -> Self: ...

    @classmethod
    def fromisocalendar(cls, year: int, week: int, day: int) -> Self: ...

    @classmethod
    def strptime(cls, date_string: str, format: str, /) -> Self: ...

    ############################################################################

    @forward
    def replace(self, year: _int = ..., month: _int = ..., day: _int = ...) -> Self: ...

    ############################################################################

    @forward
    def strftime(self, format: str) -> str: ...

    @forward
    def isoformat(self) -> str: ...

    @forward
    def ctime(self) -> str: ...

    @forward
    def __format__(self, fmt: str, /) -> str: ...

    ############################################################################

    @forward
    def weekday(self) -> int: ...

    @forward
    def isoweekday(self) -> int: ...

    @forward
    def isocalendar(self): ...

    @forward
    def toordinal(self) -> int: ...

    @forward
    def timetuple(self) -> tuple: ...

    ############################################################################

    @forward
    def __add__(self, value: timedelta, /) -> Self: ...

    @forward
    def __sub__(self, value: timedelta | Self, /) -> Self | timedelta: ...

    @forward
    def __radd__(self, value: timedelta, /) -> Self: ...

    ############################################################################

    def __eq__(self, other: object, /) -> bool: return v_eq(date, self, other)
    def __ne__(self, other: object, /) -> bool: return v_ne(date, self, other)
    def __lt__(self, other: date, /) -> bool:   return v_lt(date, self, other)
    def __le__(self, other: date, /) -> bool:   return v_le(date, self, other)
    def __gt__(self, other: date, /) -> bool:   return v_gt(date, self, other)
    def __ge__(self, other: date, /) -> bool:   return v_ge(date, self, other)

    ############################################################################

    def __hash__(self) -> int: return v_hash(date, self)
