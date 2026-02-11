# fmt: off

import typing as T

from .filters import FilterFn, ALL, NONE

__all__ = [
    'eval_safe',
]


################################################################################

def eval_safe(expr: 'ast.expr | None', *,
              unrep: object = None, filt: FilterFn = ALL, names: dict = None) -> tuple[bool, object]:

    if expr is None or filt is NONE:
        return False, unrep

    from ast import Constant, Name, Tuple, List, Call, Subscript, BinOp, BitOr, Attribute, UnaryOp, USub, dump

    def ev(node):
        match node:
            case Constant(const):
                return const
            case Attribute(Name("typing"), a):
                import typing
                assert a in typing.__all__
                return getattr(typing, a)
            case Attribute(Attribute(Name("collections"), 'abc'), a):
                from collections import abc as abc
                assert a in abc.__all__
                return getattr(abc, a)
            case Name(name):
                if name in SAFE_EVAL_NS:
                    return SAFE_EVAL_NS[name]
                if names and name in names:
                    return names[name]
                raise NameError(name)
            case Tuple(elems):
                return tuple(map(ev, elems))
            case List(elems):
                return tuple(map(ev, elems))
            case Call(Name('object'), args=[], keywords=[]):
                return unrep
            case Subscript(lhs, slice=arg):
                orig = ev(lhs)
                return orig[ev(arg)]
            case BinOp(left=lhs, op=BitOr(), right=rhs):
                return ev(lhs) | ev(rhs)
            case UnaryOp(USub(), Constant(val)):
                return -val
            case _:
                node = dump(node, indent=2)
                print("CANNOT EVAL: ", node)
                raise NotImplementedError()

    try:
        value = ev(expr)
        valid = filt is ALL or filt(value)
        return valid, value
    except:
        return False, unrep


################################################################################

SAFE_EVAL_NS = dict(
    bool=bool, int=int, float=float, complex=complex,
    str=str, bytes=bytes, bytearray=bytearray,
    list=list, tuple=tuple, set=set, dict=dict, frozenset=frozenset,
    object=object, type=type,
    Any=T.Any, Literal=T.Literal, NoReturn=T.NoReturn, Never=T.Never, Self=T.Self,
    Tuple=T.Tuple, List=T.List, Dict=T.Dict, Set=T.Set, FrozenSet=frozenset,
    Sequence=T.Sequence, Mapping=T.Mapping, Collection=T.Collection,
    Callable=T.Callable, Type=T.Type, Protocol=T.Protocol,
)
