# fmt: off

import typing
from collections.abc import Callable, Iterable
from re import compile as re_compile

__all__ = [
    'maptuple',
    'maplist',
    'mapdict',
    'identity',
    'constant_',
    'then_',
    'is_',
    'eq_',
    'neq_',
    'and_',
    'or_',
    'not_',
    'any_',
    'all_',
    'none_',
    'type_',
    'instance_',
    'in_',
    'prefixed_',
    'suffixed_',
    're_match_',
    'glob_match_',
    'true_fn',
    'false_fn',
    'none_fn',
]


################################################################################

AS = typing.ParamSpec('AS')
A = typing.TypeVar('A')
B = typing.TypeVar('B')
C = typing.TypeVar('C')
K = typing.TypeVar('K')


def maptuple(fn: Callable[[A], B], seq: Iterable[A]) -> tuple[B, ...]:
    return tuple(map(fn, seq))


def maplist(fn: Callable[[A], B], seq: Iterable[A]) -> list[B]:
    return list(map(fn, seq))


def mapdict(fn: Callable[[A], B], dct: dict[K, A]) -> dict[K, B]:
    return {k: fn(v) for k, v in dct.items()}


################################################################################


def identity(value: A) -> A:
    """`identity(val)` returns `val`"""
    return value


identity = typing._idfunc  # type: ignore


def constant_(value: A) -> Callable[..., A]:
    """`constant_(val)` returns `... => val`"""

    def fn(*_, **__):
        return value

    return fn


def then_(f: Callable[AS, B], g: Callable[[B], C]) -> Callable[AS, C]:
    """`then_(f, g)` returns `args.. => g(f(args..))`"""
    if f is identity:
        return g
    if g is identity:
        return f

    def fn(*_, **__):
        return g(f(*_, **__))

    return fn


###############################################################################

# predicates


def is_(a: A) -> A:
    """`is_(a)` returns `b => a is b`"""

    def fn(b):
        return a is b

    return fn


def eq_(a: A) -> A:
    """`eq_(a)` returns `arg => arg == a`"""

    def fn(b):
        return a == b

    return fn


def neq_(a: A) -> A:
    """`neq_(a)` returns `arg => arg != a`"""

    def fn(b):
        return a != b

    return fn


def and_(p: Callable[AS, bool], q: Callable[AS, bool]) -> Callable[AS, bool]:
    """`and_(p, q)` returns `args.. => p(args..) and q(args..)`"""

    def fn(*_, **__):
        return p(*_, **__) and q(*_, **__)

    return fn


def or_(p: Callable[AS, bool], q: Callable[AS, bool]) -> Callable[AS, bool]:
    """`or_(p, q)` returns `args.. => p(args..) or q(args..)`"""

    def fn(*_, **__):
        return p(*_, **__) or q(*_, **__)

    return fn


def not_(p: Callable[AS, bool]) -> Callable[AS, bool]:
    """`not_(p)` returns `args.. => not_fn(p(args..))`"""

    def fn(*_, **__):
        return not p(*_, **__)

    return fn


###############################################################################


def any_(p: Callable[[A], bool]) -> Callable[[Iterable[A]], bool]:
    """`any_(p)` returns `seq => any(p(a) for a in seq)`"""

    def fn(seq):
        return any(map(p, seq))

    return fn


def all_(p: Callable[[A], bool]) -> Callable[[Iterable[A]], bool]:
    """`all_(p)` returns `seq => all(p(a) for a in seq)`"""

    def fn(seq):
        return all(map(p, seq))

    return fn


def none_(p: Callable[[A], bool]) -> Callable[[Iterable[A]], bool]:
    """`none_(p)` returns `seq => not any(p(a) for a in seq)`"""

    def fn(seq):
        return not any(map(p, seq))

    return fn


###############################################################################


def type_(t: type | tuple[type, ...]) -> Callable[[object], bool]:
    """`type_(t)` returns `obj => type(obj) is t`"""
    if type(t) is tuple:

        def fn(obj):
            return type(obj) in t

        return fn

    def fn(obj):
        return type(obj) is t

    return fn


def instance_(t: type | tuple[type, ...]) -> Callable[[object], bool]:
    """`instance_(typ)` returns `obj => instanceof(obj, ty)`"""

    def fn(obj):
        return isinstance(obj, t)

    return fn


def in_(it: Iterable[A]) -> Callable[[A], bool]:
    """`in_(it)` returns `arg => arg in it`"""
    if not isinstance(it, (tuple, set, list, dict, frozenset)):
        it = tuple(it)
    return it.__contains__


###############################################################################


def prefixed_(prefix: str) -> Callable[[str], bool]:
    def fn(s: str) -> bool:
        return s.startswith(prefix)

    return fn


def suffixed_(suffix: str) -> Callable[[str], bool]:
    def fn(s: str) -> bool:
        return s.endswith(suffix)

    return fn


def re_match_(patt: str) -> Callable[[str], bool]:
    regex = re_compile(patt)

    def fn(s: str) -> bool:
        return bool(regex.fullmatch(s))

    return fn


def glob_match_(patt: str | None, default: bool = True) -> Callable[[str], bool]:
    if patt is None:
        return true_fn if default else false_fn

    assert type(patt) is str

    if '*' not in patt:
        return patt.__eq__

    if patt.count('*') == 1:
        if patt.startswith('*'):
            return suffixed_(patt[1:])
        if patt.endswith('*'):
            return prefixed_(patt[:-1])

    import fnmatch

    return re_match_(fnmatch.translate(patt))


###############################################################################

def true_fn(*args, **kwargs):
    return True

def false_fn(*args, **kwargs):
    return False

def none_fn(*args, **kwargs):
    return None
