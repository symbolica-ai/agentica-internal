# fmt: off

from types import get_original_bases

from ...core.result import PENDING_RESULT
from ..resource.all import *
from ..resource.virtual_function import FunctionData
from .__ import *
from .base import Msg
from .msg_aliases import *
from .signature_msg import SignatureMsg, enc_signature, dec_signature

__all__ = [
    'ResourceDataMsg',
    'ObjectDataMsg',
    'ClassDataMsg',
    'FunctionDataMsg',
    'CoroutineDataMsg',
    'ModuleDataMsg',
    'TypeDataMsg',
    'TypeVarDataMsg',
    'IteratorDataMsg',
    'EnumClassDataMsg',
    'PropertyDataMsg',
    'ExceptionDataMsg',
]


################################################################################

if TYPE_CHECKING:
    from ..resource.all import ResourceData
    from .term_result import ResultMsg
    from .term import TermMsg
    from .term_resource import ResourceMsg
    from .term_special import ReduceObjMsg

################################################################################

class ResourceDataMsg[R: ResourceData](Msg):
    """
    ABC for messages describing the content of virtualized resources.

    These can only occur in the `defs` field of a `FramedRequestMsg` or
    `FramedResponseMsg`.
    """

    KIND:     ClassVar[Kind] = Kind.Unknown
    DATA_CLS: ClassVar['type[ResourceData]']

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__()
        base = get_original_bases(cls)[0]
        args = T.get_args(base)
        cls.DATA_CLS = data_cls = args[0]
        data_cls.MSG_CLS = cls
        if not hasattr(data_cls, '__annotations__'):
            return
        msg_cls_keys = set(cls.__annotations__.keys())
        data_cls_keys = set(data_cls.__annotations__.keys())
        if msg_cls_keys != data_cls_keys:
            problem = f"{cls.__name__} is out of sync with {data_cls.__name__}:\n"
            problem += f"{msg_cls_keys=!r}\n{data_cls_keys=!r}\n"
            raise TypeError(problem)

    def __debug_info_str__(self) -> str:
        name = getattr(self, 'name', None)
        return f'name={name}' if name else ''

    def __shape__(self) -> str:
        return getattr(self, 'name', '')

    def decode(self, dec: DecoderP) -> R:
        cls = type(self)
        data_cls = cls.DATA_CLS
        data = data_cls()
        self.decode_fields(data, dec)
        for key in cls.__struct_fields__:
            if not hasattr(data, key):
                setattr(data, key, getattr(self, key))
        return data

    @classmethod
    def encode_fields(cls, data: R, enc: EncoderP) -> dict[str, Any]:
        return {}

    def decode_fields(self, data: R, dec: DecoderP) -> None:
        return


################################################################################

class ObjectDataMsg(ResourceDataMsg[ObjectData], tag='obj:'):

    KIND = Kind.Object

    cls: 'ClassMsg'
    keys: strtup
    open: bool = False
    size: int | None = None
    hash: int | None = None

    def __debug_info_str__(self) -> str:
        return f'cls={self.cls.shape}'

    def __shape__(self) -> str:
        return self.cls.shape

    @classmethod
    def encode_fields(cls, data: ObjectData, enc: EncoderP):
        return dict(cls=enc.enc_class(data.cls))

    def decode_fields(self, data: ObjectData, dec: DecoderP):
        data.cls = dec.dec_class(self.cls)


################################################################################

class ClassDataMsg(ResourceDataMsg[ClassData], tag='cls:'):

    KIND = Kind.Class

    name:     str
    cls:     'ClassMsg'
    bases:   'Tup[ClassMsg]'
    factory: 'SignatureMsg | None' = None
    methods: 'MethodsMsg' = {}
    sattrs:   strtup = ()
    keys:     strtup = ()
    annos:   'AnnotationsMsg' = {}
    attrs:   'AttributesMsg' = {}
    params:  'ArgsMsg' = ()
    props:   'PropertiesMsg' = {}
    qname:    optstr = None  # note: same CPython classes don't actually have a qname or module
    module:   optstr = None
    doc:      optstr = None
    mch_args: strtup | None = None
    hashing:  HashMode = 'user'

    @classmethod
    def encode_fields(cls, data: ClassData, enc: EncoderP):
        return dict(
            cls=enc.enc_class(data.cls),
            bases=tuple(map(enc.enc_class, data.bases)),
            factory=enc_signature(data.factory, enc) if data.factory else None,
            methods=enc.enc_methods(data.methods),
            annos=enc.enc_annotations(data.annos),
            attrs=enc.enc_record(data.attrs),
            params=enc.enc_sequence(data.params),
            props=enc.enc_properties(data.props),
        )

    def decode_fields(self, data: ClassData, dec: DecoderP):
        dec_cls = dec.dec_class
        data.cls = dec_cls(self.cls)
        data.bases = tuple(map(dec_cls, self.bases))
        data.factory = dec_signature(self.factory, dec) if self.factory else None
        data.methods = dec.dec_methods(self.methods)
        data.annos = dec.dec_annotations(self.annos)
        data.attrs = dec.dec_record(self.attrs)
        data.params = dec.dec_sequence(self.params)
        data.props = dec.dec_properties(self.props)


################################################################################

class FunctionDataMsg(ResourceDataMsg[FunctionData], tag='fun:'):

    KIND = Kind.Function

    ident:      Identifier
    sig:       'SignatureMsg'
    isig:      'ReduceObjMsg | None' = None
    owner:     'ResourceMsg | None' = None         # for benefit of TS
    async_mode: AsyncMode = None
    keys:       strtup = ()

    @property
    def name(self) -> str:
        return self.ident.name

    @property
    def is_async(self) -> bool:
        return self.sig.is_coro

    @classmethod
    def encode_fields(cls, data: FunctionData, enc: EncoderP):
        from .signature_msg import enc_signature
        return dict(
            sig=enc_signature(data.sig, enc),
            isig=enc.enc_any(data.isig) if data.isig is not None else None,
            owner=enc.enc_owner(),
        )

    def decode_fields(self, data: FunctionData, dec: DecoderP):
        from .signature_msg import dec_signature
        data.sig = dec_signature(self.sig, dec)
        data.isig = dec.dec_any(self.isig) if self.isig is not None else None
        data.owner = None
        # data.owner = dec.dec_cls(self.owner) if self.owner is not None else None


################################################################################

class CoroutineDataMsg(ResourceDataMsg[CoroutineData], tag='cor:'):

    KIND = Kind.Coroutine

    name:  str
    qname: optstr

    @classmethod
    def encode_fields(cls, data: FunctionData, enc: EncoderP):
        return dict()

    def decode_fields(self, data: FunctionData, dec: DecoderP):
        pass


################################################################################

class ModuleDataMsg(ResourceDataMsg[ModuleData], tag='mod:'):

    KIND = Kind.Module

    name:     str
    doc:      optstr
    file:     optstr
    package:  optstr
    exports: 'Rec[TermMsg | None]'
    hidden:   strtup = ()
    annos:   'AnnotationsMsg' = {}

    @classmethod
    def encode_fields(cls, data: ModuleData, enc: EncoderP):
        enc_any = enc.enc_any
        exports_msg = {k: None if v is ON_DEMAND else enc_any(v) for k, v in data.exports.items()}
        annos_msg = enc.enc_annotations(data.annos)
        return dict(exports=exports_msg, annos=annos_msg)

    def decode_fields(self, data: ModuleData, dec: DecoderP):
        dec_any = dec.dec_any
        data.exports = {k: (ON_DEMAND if v is None else dec_any(v)) for k, v in self.exports.items()}
        data.annos = dec.dec_annotations(self.annos)


################################################################################

class TypeDataMsg[R: TypeData](ResourceDataMsg[R]):
    KIND = Kind.Type


class TypeAliasDataMsg(TypeDataMsg[TypeAliasData], tag='alias:'):

    name:    str
    module:  str
    params: 'ArgsMsg'
    value:  'TermMsg'

    @classmethod
    def encode_fields(cls, data: TypeAliasData, enc: EncoderP):
        return dict(params=enc.enc_sequence(data.params), value=enc.enc_any(data.value))

    def decode_fields(self, data: TypeAliasData, dec: DecoderP):
        try:
            data.params = dec.dec_sequence(self.params)
        except E.WarpDecodingError:
            data.params = ()
        try:
            data.value = dec.dec_any(self.value)
        except E.WarpDecodingError:
            data.value = Any


class TypeVarDataMsg(TypeDataMsg[TypeVarData], tag='tvar:'):

    name:  str
    pspec: bool

    @classmethod
    def encode_fields(cls, data: TypeVarData, enc: EncoderP):
        return dict()

    def decode_fields(self, data: TypeVarData, dec: DecoderP):
        pass


class GenericAliasDataMsg(TypeDataMsg[GenericAliasData], tag='gen:'):

    origin: 'TermMsg'
    args:   'ArgsMsg'

    @classmethod
    def encode_fields(cls, data: GenericAliasData, enc: EncoderP):
        args = data.args
        return dict(
            origin=enc.enc_any(data.origin),
            args=enc.enc_sequence(args),
        )

    def decode_fields(self, data: GenericAliasData, dec: DecoderP):
        data.origin = dec.dec_any(self.origin)
        data.args = tuple(map(dec.dec_type, self.args))


class CallableTypeDataMsg(TypeDataMsg[CallableTypeData], tag='clb:'):

    abc:       bool
    args:      'ArgsMsg | TermMsg'
    ret:       'TermMsg'

    @classmethod
    def encode_fields(cls, data: CallableTypeData, enc: EncoderP):
        args, ret = data.args, data.ret
        return dict(
            args=enc.enc_sequence(args) if type(args) is tuple else enc.enc_any(args),
            ret=enc.enc_any(ret),
        )

    def decode_fields(self, data: CallableTypeData, dec: DecoderP):
        args, ret = self.args, self.ret
        data.args = tuple(map(dec.dec_type, args)) if type(args) is tuple else dec.dec_type(args)
        data.ret = dec.dec_type(ret)


class TypeUnionDataMsg(TypeDataMsg[TypeUnionData], tag='union:'):

    alts: 'ArgsMsg'
    sys:   bool = True  # builtin: True if types.Union

    @classmethod
    def encode_fields(cls, data: TypeUnionData, enc: EncoderP):
        return dict(alts=tuple(map(enc.enc_type, data.alts)))

    def decode_fields(self, data: TypeUnionData, dec: DecoderP):
        data.alts = tuple(map(dec.dec_type, self.alts))


class ForwardRefDataMsg(TypeDataMsg[ForwardRefData], tag='fwd:'):
    name: str

    @classmethod
    def encode_fields(cls, data: ForwardRefData, enc: EncoderP):
        return dict()

    def decode_fields(self, data: ForwardRefData, dec: DecoderP):
        pass


################################################################################

class IteratorDataMsg(ResourceDataMsg[IteratorData], tag='iter:'):
    KIND = Kind.Iterator

    name: str | None = None
    hint: int | None = None

    @classmethod
    def encode_fields(cls, data: IteratorData, enc: EncoderP):
        return {}

    def decode_fields(self, data: IteratorData, dec: DecoderP):
        pass

################################################################################

class FutureDataMsg(ResourceDataMsg[FutureData], tag='future:'):
    KIND = Kind.Future

    future:   FutureID
    result:  'ResultMsg | None' = None  # only set if complete

    @classmethod
    def encode_fields(cls, data: FutureData, enc: EncoderP):
        future_id = enc.future_to_id(data.future)
        if data.result.is_completed:
            result_msg = ResultMsg.encode(data.result, enc)
        else:
            result_msg = None
        return dict(future=future_id, result=result_msg)

    def decode_fields(self, data: FutureData, dec: DecoderP):
        data.future = dec.future_from_id(self.future)
        if result_msg := self.result:
            data.result = result_msg.decode(dec)
        else:
            data.result = PENDING_RESULT


################################################################################

class EnumClassDataMsg(ResourceDataMsg[EnumClassData], tag='enum:'):
    KIND = Kind.Class

    name:     str
    members:  AttributesMsg
    module:   optstr = None
    qualname: optstr = None
    kind:     EnumKind = 'any'
    methods:  MethodsMsg = {}

    @classmethod
    def encode_fields(cls, data: EnumClassData, enc: EncoderP):
        return dict(
            members=enc.enc_record(data.members),
            methods=enc.enc_methods(data.methods)
        )

    def decode_fields(self, data: EnumClassData, dec: DecoderP):
        data.members = dec.dec_record(self.members)
        data.methods = dec.dec_methods(self.methods)

################################################################################

class PropertyDataMsg(ResourceDataMsg[PropertyData], tag='prop:'):
    KIND = Kind.Property

    def __debug_info_str__(self) -> str:
        if self.delete: return 'rwd'
        if self.write: return 'rw'
        return 'r'

    read:   bool
    write:  bool
    delete: bool
    anno:  'TypeMsg | None' = None

    @classmethod
    def encode_fields(cls, data: PropertyData, enc: EncoderP):
        return dict(
            anno=enc.enc_type(data.anno) if data.anno is not None else None,
        )

    def decode_fields(self, data: PropertyData, dec: DecoderP):
        data.anno = dec.dec_type(self.anno) if self.anno is not None else None

################################################################################

class ExceptionDataMsg(ResourceDataMsg[ExceptionData], tag='exc:'):
    KIND = Kind.Exception

    cls:   ClassMsg
    args: 'ArgsMsg' = ()
    keys:  strtup = ()
    notes: tuple[str, ...] | None = None

    def __debug_info_str__(self) -> str:
        f_cls = f'cls={self.cls.shape}'
        f_args = f',args=<{len(self.args)}>' if self.args else ''
        return f'{f_cls}{f_args}'

    def __shape__(self) -> str:
        return f'{self.cls.shape}, <{len(self.args)}>'

    @classmethod
    def encode_fields(cls, data: ExceptionData, enc: EncoderP):
        return dict(
            cls=enc.enc_class(data.cls),
            args=enc.enc_args(data.args)
        )

    def decode_fields(self, data: ExceptionData, dec: DecoderP):
        cls = dec.dec_class(self.cls)
        args = dec.dec_args(self.args)
        data.cls = cls if issubclass(cls, BaseException) else RuntimeError
        data.args = args
