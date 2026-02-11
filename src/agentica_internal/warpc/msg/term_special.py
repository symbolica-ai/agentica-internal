# fmt: off

from typing import Union

import enum
import re
import warnings
from copyreg import _reconstructor as reconstructor  # type: ignore

from .__ import *
from .term import *
from .msg_aliases import *


__all__ = [
    'SlotObjMsg',
    'ReduceObjMsg',
    'ConstructObjMsg',
    'RegexPatternMsg',
    'RegexMatchMsg',
    'ClassUnionMsg',
    'EnumMemberMsg',
    'EnumKeyMsg',
    'EnumValMsg'
]


################################################################################

if TYPE_CHECKING:
    from .term_resource import SystemResourceMsg

################################################################################

def slot_stdlib_types():
    import dataclasses as DC
    return DC.Field, DC._DataclassParams, DC.InitVar  # type: ignore

SLOT_OBJ_TYPES: tuple[type, ...] = slot_stdlib_types()

SlotObjT = Union[*SLOT_OBJ_TYPES]

del slot_stdlib_types

################################################################################

class SlotObjMsg(TermPassByValMsg, tag='slots'):
    """Message describing objects by-value via their slot contents. Used
    for instances of certain builtin system classes that we wish to serialize by-value, like
    dataclass Fields."""

    type V = SlotObjT

    cls:   'SystemResourceMsg'
    slots: 'Rec[TermMsg]'

    def __len__(self) -> int:
        return len(self.slots)

    def __shape__(self) -> str:
        return self.cls.sys_name

    def decode(self, dec: DecoderP) -> V:
        from .term_resource import SystemResourceMsg
        assert isinstance(self.cls, SystemResourceMsg)
        _cls = self.cls.sys_cls
        term = object.__new__(_cls)  # type: ignore
        slots = dec.dec_record(self.slots)
        for slot_key, slot_val in slots.items():
            setattr(term, slot_key, slot_val)
        return term

    @classmethod
    def encode_compound(cls, term: V, enc: EncoderP) -> 'SlotObjMsg':
        _cls = type(term)
        slot_keys = _cls.__slots__
        cls_msg = enc.enc_class(_cls)
        assert isinstance(cls_msg, SystemResourceMsg), f"trying to encode non-system cls {_cls}"
        slots, add_slot = mkdict()
        enc_any = enc.enc_any
        for slot_key in slot_keys:
            val = getattr(term, slot_key, FIELD_ABSENT)
            if val is not FIELD_ABSENT:
                add_slot(slot_key, enc_any(val))
        return SlotObjMsg(cls_msg, slots)


################################################################################

def reducible_stdlib_types():
    import itertools as IT, inspect as INS, os as OS, datetime as DT
    import ipaddress as IP
    return (
        partial,
        IT.count, IT.islice, IT.cycle, IT.repeat, IT.takewhile, IT.dropwhile, IT.zip_longest, IT.starmap,
        OS.stat_result,
        DT.date, DT.time, DT.datetime, DT.timedelta, DT.tzinfo, DT.timezone,
        INS.Signature, INS.Parameter, INS.BoundArguments,
        IP.IPv4Address, IP.IPv4Interface, IP.IPv4Network, IP.IPv6Address, IP.IPv6Interface, IP.IPv6Network
    )

REDUCIBLE_TYPES = reducible_stdlib_types()

ReducibleObjT = Union[*REDUCIBLE_TYPES]

del reducible_stdlib_types

################################################################################

class ReduceObjMsg(TermPassByValMsg, tag='reduce'):
    """Message describing objects by-value via the result of `__reduce__`."""

    type V = ReducibleObjT

    cls:   'SystemResourceMsg'
    args:  'Tup[TermMsg]'
    state: 'TermMsg | None'

    def __shape__(self) -> str:
        return self.cls.sys_name

    def decode(self, dec: DecoderP) -> V:
        assert isinstance(self.cls, SystemResourceMsg)
        _cls = self.cls.sys_resource  # might be a class, or 'iter', which is a function
        if _cls not in REDUCIBLE_TYPES:
            raise E.WarpDecodingError(f"{_cls!r} is not reducible")
        args = dec.dec_sequence(self.args)
        state = dec.dec_any(self.state) if self.state is not None else None
        try:
            obj = _cls(*args)
            obj.__setstate__(state) if state is not None else None
            return obj
        except BaseException as exc:
            raise E.WarpDecodingError(f"Could not expand {_cls} on {args}\n{self}:\n{exc!r}")

    @classmethod
    def encode_compound(cls, term: Any, enc: EncoderP) -> 'ReduceObjMsg':
        _cls = type(term)
        try:
            reduced = term.__reduce__()
            n = len(reduced)
            assert n == 2 or n == 3, f"bad reduction: {f_object_id(reduced)}"
            if n == 2:
                clb, args = reduced
                state = None
            else:
                clb, args, state = reduced
            assert clb is _cls, f"constructor is not original type: {clb} != {_cls}"
            assert type(args) is tuple, f"args is not a tuple: {f_object_id(args)}"
        except BaseException as exc:
            # f_exc = fmt_exception(exc)
            raise E.WarpEncodingError(f"Could not reduce {f_object_id(term)}: {exc}")
        cls_msg = enc.enc_system_resource(_cls)
        args_msg = enc.enc_sequence(args)
        state_msg = enc.enc_any(state) if state is not None else None
        return ReduceObjMsg(cls_msg, args_msg, state_msg)


################################################################################

def constructible_stdlib_types():
    import urllib.parse as UP, urllib.request as UR
    return (
        UP.DefragResult, UP.DefragResultBytes, UP.ParseResult, UP.ParseResultBytes, UP.SplitResult,
        UP.SplitResultBytes, UR.Request
    )

CONSTRUCTIBLE_TYPES = constructible_stdlib_types()

ConstructibleObjT = Union[*CONSTRUCTIBLE_TYPES]

del constructible_stdlib_types

################################################################################

class ConstructObjMsg(TermPassByValMsg, tag='reconstruct'):

    type V = ConstructibleObjT

    cls:   'SystemResourceMsg'
    base:  'SystemResourceMsg'
    init:  'TermMsg'

    def decode(self, dec: DecoderP) -> V:
        cls = self.cls.sys_resource
        base = self.base.sys_resource
        if not isinstance(cls, type) or cls not in CONSTRUCTIBLE_TYPES:
            raise E.WarpDecodingError(f"{cls!r} is not constructible type")
        if not isinstance(base, type) or not base.__flags__ & 256:
            raise E.WarpDecodingError(f"{base!r} is not a constructible base")
        init = dec.dec_any(self.init)
        return reconstructor(cls, base, init)

    @classmethod
    def encode_compound(cls, term: Any, enc: EncoderP) -> 'ConstructObjMsg':
        try:
            reduced = term.__reduce__()
            assert len(reduced) == 2
            clb, args = reduced
            assert clb is reconstructor
            assert len(args) == 3
            _cls, base, init = args
            assert _cls is type(term)
            assert type(base) is type
            cls_msg = enc.enc_system_resource(_cls)
            base_msg = enc.enc_system_resource(base)
            init_msg = enc.enc_any(init)
        except BaseException as exc:
            raise E.WarpEncodingError(f"Could not deconstruct {f_object_id(term)}: {exc}")
        return ConstructObjMsg(cls_msg, base_msg, init_msg)


################################################################################

class RegexPatternMsg(TermPassByValMsg, tag='regex_pattern'):
    """Message describing re.Pattern objects by value."""

    type V = re.Pattern

    pattern: str
    flags:   int

    def decode(self, dec: DecoderP) -> V:
        return re._compile(self.pattern, self.flags)  # type: ignore

    @classmethod
    def encode_atom(cls, term: V) -> 'RegexPatternMsg':
        return RegexPatternMsg(term.pattern, term.flags)


################################################################################

class RegexMatchMsg(TermPassByValMsg, tag='regex_match'):
    """Message describing re.Match objects by value."""

    type V = re.Match

    pattern: str
    flags:   int
    string:  str
    span:    tuple[int, int]

    def decode(self, dec: DecoderP) -> V:
        # this is ugly but since re.Match is not pickle-able there is
        # no other way to do it!
        patt = re._compile(self.pattern, self.flags)  # type: ignore
        start, end = span = self.span
        for match in patt.finditer(self.string, start, end):
            if match.span() == span:
                return match
        raise E.WarpDecodingError(f"Could not reconstruct re.Match")

    @classmethod
    def encode_atom(cls, term: V) -> 'RegexMsg':
        re = term.re
        return RegexMatchMsg(re.pattern, int(re.flags), term.string, term.span())


################################################################################

class ClassUnionMsg(TermPassByValMsg, tag='class_union'):
    """Message for simple inline unions like `int | float` (used by typescript for 'Number')."""

    alts: 'Tup[ClassMsg]'

    def decode(self, dec: DecoderP) -> TypeT:
        try:
            cls_list = []
            for msg in self.alts:
                cls = dec.dec_type(msg)
                if not isinstance(cls, type):
                    return Any
            union = cls_list[0]
            for cls in cls_list[1:]:
                union |= cls
            return union
        except:
            return Any


################################################################################

class EnumMemberMsg(TermPassByValMsg):

    cls: 'ClassMsg'

    def decode(self, dec: DecoderP) -> enum.Enum: ...

    @staticmethod
    def encode_enum(value: enum.Enum, enc: EncoderP) -> 'EnumMemberMsg':
        cls_msg = enc.enc_class(type(value))
        if isinstance(value, int):
            # IntFlags in particular allow non-nameable enum values
            return EnumValMsg(cls_msg, enc.enc_any(int(value)))
        else:
            return EnumKeyMsg(cls_msg, value.name)


################################################################################

class EnumKeyMsg(EnumMemberMsg, tag='enum_key'):

    cls: 'ClassMsg'
    key:  str

    def decode(self, dec: DecoderP) -> TypeT:
        enum_cls = dec.dec_class(self.cls)
        if not issubclass(enum_cls, enum.Enum):
            raise E.WarpEncodingError(f"{enum_cls=!r} is not an enum class")
        return enum_cls._member_map_[self.key]


################################################################################

class EnumValMsg(EnumMemberMsg, tag='enum_val'):

    cls: 'ClassMsg'
    val: 'TermMsg'

    def decode(self, dec: DecoderP) -> TypeT:
        enum_cls = dec.dec_class(self.cls)
        enum_val = dec.dec_any(self.val)
        if not issubclass(enum_cls, enum.Enum):
            raise E.WarpEncodingError(f"{enum_cls=!r} is not an enum class")
        return enum_cls(enum_val)


################################################################################

# FIXME: replace this mechanism with virtual iterators
warnings.filterwarnings(
    'ignore',
    message='Pickle, copy, and deepcopy support will be removed from itertools in Python 3.14.',
    category=DeprecationWarning,
    append=True
)
