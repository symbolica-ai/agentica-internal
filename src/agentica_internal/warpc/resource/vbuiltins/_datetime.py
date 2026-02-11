# fmt: off

from typing import ClassVar
from datetime import date, datetime, timedelta, tzinfo

from .vshared import *
from .vmethods import *

_int = int  # should be typing.SupportsIndex
opt_tz = tzinfo | None

################################################################################

class _datetime(datetime):

    min:        ClassVar[datetime]
    max:        ClassVar[datetime]
    resolution: ClassVar[timedelta]

    def __new__(cls,
                year: _int = ARG_DEFAULT,
                month: _int = ARG_DEFAULT,
                day: _int = ARG_DEFAULT,
                hour: _int = 0,
                minute: _int = 0,
                second: _int = 0,
                microsecond: _int = 0,
                tzinfo: tzinfo = None, *,
                fold: int = 0) -> Self:
        return datetime.__new__(cls, 2026, 1, 1)

    ############################################################################

    @ro_property
    def year(self) -> int: ...

    @ro_property
    def month(self) -> int: ...

    @ro_property
    def day(self) -> int: ...

    # ----

    @ro_property
    def hour(self) -> int: ...

    @ro_property
    def minute(self) -> int: ...

    @ro_property
    def second(self) -> int: ...

    @ro_property
    def microsecond(self) -> int: ...

    @ro_property
    def tzinfo(self) -> object: ...

    @ro_property
    def fold(self) -> int: ...

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

    # ----

    @classmethod
    def now(cls, tz: opt_tz = None) -> Self: ...

    @classmethod
    def utcnow(cls) -> Self: ...

    @classmethod
    def fromtimestamp(cls, timestamp: float, tz=None) -> Self: ...

    @classmethod
    def utcfromtimestamp(cls, t: float, /) -> Self: ...

    @classmethod
    def combine(cls, date, time, tzinfo=...) -> Self: ...

    @classmethod
    def strptime(cls, date_string: str, format: str, /) -> Self: ...

    ############################################################################

    def replace(self,
                year: _int = ..., month: _int = ..., day: _int = ...,
                hour: _int = ..., minute: _int = ..., second: _int = ...,
                microsecond: _int = ..., tzinfo: tzinfo = ..., *, fold: int = ...) -> Self: ...

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

    # ----

    @forward
    def utctimetuple(self) -> tuple: ...

    @forward
    def timestamp(self) -> float: ...

    @forward
    def date(self) -> date: ...

    @forward
    def time(self) -> object: ...

    @forward
    def timetz(self) -> object: ...

    @forward
    def astimezone(self, tz: opt_tz = None) -> Self: ...

    @forward
    def isoformat(self, sep: str = "T", timespec: str = "auto") -> str: ...

    @forward
    def utcoffset(self) -> timedelta | None: ...

    @forward
    def tzname(self) -> str | None: ...

    @forward
    def dst(self) -> timedelta | None: ...

    ############################################################################

    @forward
    def __add__(self, value: timedelta, /) -> Self: ...

    @forward
    def __sub__(self, value: timedelta | Self, /) -> Self | timedelta: ...

    @forward
    def __radd__(self, value: timedelta, /) -> Self: ...

    ############################################################################

    def __eq__(self, other: object, /) -> bool: return v_eq(datetime, self, other)
    def __ne__(self, other: object, /) -> bool: return v_ne(datetime, self, other)
    def __lt__(self, other: date, /) -> bool:   return v_lt(datetime, self, other)
    def __le__(self, other: date, /) -> bool:   return v_le(datetime, self, other)
    def __gt__(self, other: date, /) -> bool:   return v_gt(datetime, self, other)
    def __ge__(self, other: date, /) -> bool:   return v_ge(datetime, self, other)

    ############################################################################

    def __hash__(self) -> int: return v_hash(datetime, self)
