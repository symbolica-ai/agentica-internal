# fmt: off

from abc import ABC
from typing import ClassVar, Self, TYPE_CHECKING

from ...core.fmt import f_object, f_slot_obj
from ...core.print import rprint

__all__ = [
    'EncodableData'
]

################################################################################

if TYPE_CHECKING:
    from ..msg.base import Msg
    from ..msg.codec import EncoderP

################################################################################

class EncodableData(ABC):
    """
    ABC for a class that can be encoded to a message.

    The main (abstract) subclasses are ResourceData and Request(Data).
    """

    __slots__ = ()

    STR_KEYS:  ClassVar[bool] = False
    REPR_KEYS: ClassVar[bool] = True
    ZERO_INST: ClassVar[object] = None

    ############################################################################

    def copy(self) -> Self:
        cls = type(self)
        copied = EncodableData.__new__(cls)
        for slot in cls.__slots__:
            setattr(copied, slot, getattr(self, slot))
        return copied

    ############################################################################

    def encode(self, enc: 'EncoderP') -> 'Msg': ...

    ############################################################################

    def pprint(self, err: bool = False):
        rprint(f_slot_obj(self), err=err)

    def __repr__(self):
        return self.__fmt__(self.REPR_KEYS)

    def __str__(self):
        return self.__fmt__(self.STR_KEYS)

    def __short_str__(self):
        return self.__fmt__(False)

    def __fmt__(self, keys: bool) -> str:
        f_head = type(self).__name__
        f_args = _commas(
            f'{k}={v}' if keys else v
            for k, v in self.__fmt_args__(keys)
        )
        return f'{f_head}({f_args})'

    def __fmt_args__(self, keys: bool):
        cls = type(self)
        zero = getattr(cls, 'ZERO_INST', None) if keys else None
        if slots := getattr(cls, '__slots__', ()):
            for slot in slots:
                value = getattr(self, slot, _absent)
                if value is not _absent:
                    if zero is not None and getattr(zero, slot) == value:
                        continue
                    yield slot, f_object(value)
        else:
            for key, value in self.__dict__.items():
                yield key, f_object(key)


################################################################################

_absent = object()
_commas = ', '.join
