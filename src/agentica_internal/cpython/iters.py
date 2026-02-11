# fmt: off

import itertools as I
import sys
import warnings
from collections.abc import Callable
from math import comb
from types import MappingProxyType
from typing import Any, Union

__all__ = [
    'DictKeysType',
    'DictValuesType',
    'DictItemsType',
    'DictKeysIterType',
    'DictValuesIterType',
    'DictItemsIterType',
    'SeqIterType',
    'ListIterType',
    'TupleIterType',
    'SetIterType',
    'FrozenSetIterType',
    'ReversedListIterType',
    'ReversedSeqIterType',
    'StrIterType',
    'BytesIterType',
    'ByteArrayIterType',
    'CallIterType',
    'BuiltinIteratorT',
    'STR_ITER_TYPES',
    'SEQ_ITER_TYPES',
    'REV_ITER_TYPES',
    'SET_ITER_TYPES',
    'DICT_ITER_TYPES',
    'MISC_ITER_TYPES',
    'ITER_TYPES',
    'DICT_VIEW_TYPES',
    'PROXY_VIEW_TYPES',
    'VIEW_TYPES',
    'iter_len',
    'iter_len_hint',
    'UNBOUNDED'
]

####################################################################################################
# setup

class _SequenceClass:
    def __getitem__(self, _): return 0
    def __len__(self):        return 3

_sequence_obj        = _SequenceClass()

_dict                = dict()
_dict_keys           = _dict.keys()
_dict_values         = _dict.values()
_dict_items          = _dict.items()

####################################################################################################

def _get_frame_locals():
    return sys._getframe().f_locals

_frame_locals_proxy      = _get_frame_locals()
_mapping_proxy           = object.__dict__

FrameLocalsProxyType     = type(_frame_locals_proxy)
# in 3.12 this is dict, in 3.13 this is a proxy type

del _get_frame_locals
del _mapping_proxy
del _frame_locals_proxy

####################################################################################################

type types = tuple[type, ...]

StrIterType           = type(iter(str()))
BytesIterType         = type(iter(bytes()))
ByteArrayIterType     = type(iter(bytearray()))
STR_ITER_TYPES: types = StrIterType, BytesIterType, ByteArrayIterType

TupleIterType          = type(iter(tuple()))
ListIterType           = type(iter(list()))
SeqIterType            = type(iter(_sequence_obj))
ReversedSeqIterType    = reversed
ReversedListIterType   = type(iter(reversed(list())))
SEQ_ITER_TYPES: types  = TupleIterType, ListIterType, SeqIterType, ReversedListIterType, ReversedSeqIterType
REV_ITER_TYPES: types  = ReversedSeqIterType, ReversedListIterType

SetIterType            = type(iter(set()))
FrozenSetIterType      = type(iter(frozenset()))
SET_ITER_TYPES: types  = SetIterType, FrozenSetIterType

DictKeysType           = type(_dict_keys)
DictValuesType         = type(_dict_values)
DictItemsType          = type(_dict_items)
DictKeysIterType       = type(iter(_dict_keys))
DictValuesIterType     = type(iter(_dict_values))
DictItemsIterType      = type(iter(_dict_items))
DICT_ITER_TYPES: types = DictKeysIterType, DictValuesIterType, DictItemsIterType

# SetIterType is FrozenSetIterType
CallIterType           = type(iter(int, 0))
RangeIterType          = type(iter(range(1)))
MISC_ITER_TYPES: types = CallIterType, RangeIterType

SELF_ITER_TYPES:  types = zip, enumerate, map

ITER_TYPES: types      = STR_ITER_TYPES + SEQ_ITER_TYPES + SET_ITER_TYPES + DICT_ITER_TYPES + \
                         MISC_ITER_TYPES + SELF_ITER_TYPES

BuiltinIteratorT = Union[*ITER_TYPES]

####################################################################################################

DICT_VIEW_TYPES:   types = DictKeysType, DictValuesType, DictItemsType
PROXY_VIEW_TYPES:  types = MappingProxyType, FrameLocalsProxyType
VIEW_TYPES:        types = DICT_VIEW_TYPES + PROXY_VIEW_TYPES

####################################################################################################

UNBOUNDED = 2 << 24 - 1

def iter_len(obj: Any) -> int:

    cls = type(obj)

    if cls in EXACT_LEN_TYPES:
        return len(obj)

    if cls in EXACT_HINT_ITER_TYPES:
        return obj.__length_hint__()

    if len_fn := custom_len_fn(cls):
        return len_fn(obj)

    return UNBOUNDED

####################################################################################################

def iter_len_hint(it: Any) -> int | None:
    cls = type(it)

    if cls in EXACT_LEN_TYPES:
        return len(it)

    if cls in EXACT_HINT_ITER_TYPES:
        return it.__length_hint__()

    if len_fn := custom_len_fn(cls):
        return len_fn(it)

    return _len_hint(it)


EXACT_LEN_TYPES:       types = list, set, dict, tuple, frozenset, str, bytes, bytearray, range, *VIEW_TYPES
INF_LEN_ITER_TYPES:    types = I.cycle,
EXACT_HINT_ITER_TYPES: types = ListIterType, TupleIterType, StrIterType, BytesIterType, \
    ByteArrayIterType, ReversedSeqIterType, ReversedListIterType, RangeIterType

####################################################################################################

def _len(obj: Any) -> int:

    cls = type(obj)

    if cls in EXACT_LEN_TYPES:
        return len(obj)  # type: ignore

    if cls in INF_LEN_ITER_TYPES:
        return UNBOUNDED

    if cls in EXACT_HINT_ITER_TYPES:
        # these are *exact* hints
        return obj.__length_hint__()

    if len_fn := custom_len_fn(cls):
        return len_fn(obj)

    return UNBOUNDED

####################################################################################################

def _len_hint(obj: object) -> int:
    hint_fn = getattr(obj, '__length_hint__', None)
    if callable(hint_fn):
        try:
            hint = hint_fn()
            if type(hint) is int and hint >= 0:
                return hint
        except:
            ...
    return UNBOUNDED

def _len_seq(obj: SeqIterType) -> int:
    match obj.__reduce__():
        case (_, (it, int() as pos)):
            n = _len(it)
            if n is not UNBOUNDED:
                return n - pos
    return UNBOUNDED

def _len_map(obj: map) -> int:
    _, args = obj.__reduce__()
    return min(map(_len, args[1:]))

def _len_zip(obj: zip) -> int:
    match obj.__reduce__():
        case (_, tuple() as its):
            return min(map(_len, its))
    return UNBOUNDED

def _len_enum(obj: enumerate) -> int:
    match obj.__reduce__():
        case (_, (it, _)):
            return _len(it)
    return UNBOUNDED

def _len_rev(obj: ReversedListIterType) -> int:
    match obj.__reduce__():
        case (_, (it, *_)):
            return _len(it)
    return UNBOUNDED

CUSTOM_LEN_FNS: dict[type, Callable[[Any], int]] = {
    map:                  _len_map,
    enumerate:            _len_enum,
    zip:                  _len_zip,
    SeqIterType:          _len_hint,
    SetIterType:          _len_hint,
    DictItemsType:        _len_hint,
    DictKeysIterType:     _len_hint,
    DictValuesIterType:   _len_hint,
    DictItemsIterType:    _len_hint,
    ReversedSeqIterType:  _len_rev,
    ReversedListIterType: _len_rev,
    I.repeat:             _len_hint,
}
custom_len_fn = CUSTOM_LEN_FNS.get

####################################################################################################

if sys.version_info[1] < 14:
    # reduce support in itertools was removed in version 14

    warnings.filterwarnings("ignore", category=DeprecationWarning)

    def _len_islice(obj: I.islice) -> int:
        _, args, _ = obj.__reduce__()
        it, start, stop, step = args
        n1 = _len(it)
        n2 = len(range(start, stop, step))
        return min(n1, n2)

    def _len_combinations(obj: I.combinations) -> int:
        _, (it, r) = obj.__reduce__()
        return comb(_len(it), r)

    def _len_offset(off: int):
        def fn(obj):
            state = obj.__reduce__()
            return _len(state[1][0]) + off
        return fn

    def _len_starmap(obj) -> int:
        match obj.__reduce__():
            case (_, (_, it, *_)):
                return _len(it)
        return UNBOUNDED

    def _len_ziplongest(obj: zip) -> int:
        match obj.__reduce__():
            case (_, tuple() as its, _):
                return max(map(_len, its))
        return UNBOUNDED

    CUSTOM_LEN_FNS |= {
        I.islice:             _len_islice,
        I.starmap:            _len_starmap,
        I.zip_longest:        _len_ziplongest,
        # not implemented correctly yet:
        # I.pairwise:         _len_offset(-1),
        # I.accumulate:       _len_offset(1),
        # I.combinations:     _len_combinations,
        # I.product:          _len_reduce(1, prod),
        # I.chain:            _len_reduce(2, sum)
    }

####################################################################################################

# def _print_info():
#
#     # print some info about concrete examples
#
#     def mk(o):
#         it = iter(o)
#         # next(it)
#         return it
#
#     vals = 1, 2, 3
#
#     iters = {
#         'enum':                 mk(enumerate(vals)),
#         'zip':                  mk(zip(vals, [1,2])),
#         'map':                  mk(map(str, vals)),
#         'SeqIterType':          mk(_sequence_obj),
#         'ListIterType':         mk(list(vals)),
#         'TupleIterType':        mk(tuple(vals)),
#         'StrIterType':          mk(str('abc')),
#         'BytesIterType':        mk(bytes(b'abc')),
#         'ByteArrayIterType':    mk(bytearray(b'abc')),
#         'CallableIterType':     mk(iter(int, 9)),
#         'ReversedIterType':     mk(reversed(vals)),
#         'ReversedListIterType': mk(reversed(list(vals))),
#         'RangeIteratorType':    mk(range(5)),
#     }
#
#     for k, v in iters.items():
#         try:
#             hint1 = iter_len_hint(v)
#             next(v); hint2 = iter_len_hint(v)
#             print(k.ljust(15), hint1, hint2, v.__reduce__())
#         except IOError: ...
#
# _print_info()

####################################################################################################

del _dict
del _dict_keys
del _dict_values
del _dict_items
del _sequence_obj
del _SequenceClass
