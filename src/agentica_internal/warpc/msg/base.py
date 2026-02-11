# fmt: off

from ..transcode import TranscodablePythonMessage
from .__ import *

__all__ = [
    'Msg',
]

################################################################################

def to_tag(s: str):
    return s.removesuffix('Msg').replace('Request', 'Req').replace('Control', 'Ctrl')

class Msg(TranscodablePythonMessage, tag=True, tag_field="msg", frozen=(not TYPE_CHECKING), cache_hash=True,
    omit_defaults=True):
    """
    ABC for all warpc protocol messages.

    Direct subclasses are `RPCMsg`, `RequestMsg`, `ResultMsg`, and `TermMsg`.

    Msgs are cheaply and stably hashable, have a 'tag' field so they form a
    discriminated union.

    ## Properties

    `msg_tag` is the short name used on the wire for a message.

    `shape` gives a short string showing the nested structure of a message,
    using the `msg_tag` as the head, e.g. `request[call[sys[int]]]`. Override
    `__shape__` to customize what the fields appear.

    ## Methods

    `repr()` gives a longer string, with `deep=True` to recurse.
    `pprint()`, `pprint_msgpack()`, `pprint_json()`
    `to_msgpack()`, `from_msgpack()`
    `to_json()`, `from_json()`
    """

    ############################################################################

    # this will be dynamically set to a per-class LogFlag, via mechanism in __final__
    LOG: ClassVar[bool] = False
    TAG: ClassVar[str] = 'msg'
    UNION: ClassVar[T.TypeAliasType]

    # this is populated for every class, in __final__.py, when all classes have been defined
    LEAF_CLASSES: ClassVar[tuple[type['Msg'], ...]] = ()

    __debug_fmt_str__ = '<{cls} {info}>'

    ############################################################################

    @property
    def msg_tag(self) -> str:
        return self.__class__.__struct_config__.tag

    @property
    def shape(self) -> str:
        f_args = self.__shape__()
        f_name = type(self).TAG
        if f_args:
            return f'{f_name}[{f_args}]'
        return f_name

    def __shape__(self) -> str:
        return ''

    ############################################################################

    # hides BLANK fields
    def repr(self, deep: bool = True) -> str:
        f_cls = self.__class__.__name__
        strs, add = mklist()
        nest_fn = repr if deep else f_object
        for k, v in self.__rich_repr__():
            s = f_slot(k, v, nest_fn)
            add(f'{k}={s}' if len(k) > 1 else s)
        return f'{f_cls}({commas(strs)})'

    def __repr__(self) -> str:
        return self.repr()

    def __debug_info_str__(self) -> str:
        return ''

    def msgpack_str(self, multiline: bool = True, censor_ids: bool = False) -> str:
        data = self.to_msgpack()
        return fmt_msgpack(data, multiline=multiline, censor_ids=censor_ids)

    ############################################################################

    def pprint(self, err: bool = False):
        from ...core.fmt import f_slot_obj
        P.rprint(f_slot_obj(self), err=err)

    def pprint_msgpack(self, err: bool = False):
        data = self.to_msgpack()
        pprint_msgpack(data, err=err)

    def pprint_json(self, err: bool = False):
        data = self.to_json()
        pprint_json(data, err=err)

    ############################################################################

    # this is for `core.debug` to use

    def short_str(self) -> str:
        return self.shape

    def __short_str__(self) -> str:
        return self.shape

    # if you want to use the `rich` library to pretty print deep messages
    def __rich_repr__(self):
        fields = self.__class__.__struct_fields__
        fields_1 = [f for f in fields if f.endswith('id')]
        fields_2 = [f for f in fields if f not in fields_1]
        for field in fields_1 + fields_2:
            value = getattr(self, field, UNSET)
            if value is UNSET:
                continue
            if field.endswith('id') and type(value) is int:
                value = f_id(value)
            if field == 'rid' and type(value) is tuple:
                value = f_grid(value)
            yield field, value

    def to_json(self) -> bytes:
        from .__json import enc_json
        return enc_json(self)

    def to_msgpack(self) -> bytes:
        try:
            return enc_msgpack(self)
        except EncodeError as exc:
            P.tprint('error encoding message:', exc, err=True)
            P.tprint('message being encoded:', self, err=True)
            return b''

    @classmethod
    def rec_to_msgpack(cls, rec: dict) -> bytes:
        assert is_rec(rec)
        assert all(isinstance(v, cls) for v in rec.values())
        return enc_msgpack(rec)

    @classmethod
    def from_json[M: Msg](cls: type[M], json_data: bytes) -> M: ...

    @classmethod
    def from_msgpack[M: Msg](cls: type[M], msgpack_data: bytes) -> M: ...

    @classmethod
    def check[M: Msg](cls: type[M], msg: Any):
        assert isinstance(msg, cls), (
            f'expected {cls.__name__!r} message, but got {msg.__class__.__name__}'
        )
