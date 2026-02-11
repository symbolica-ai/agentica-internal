# fmt: off

from enum import Enum
from .__ import *
from .kinds import *
from .forbidden import *
from .kinds import is_class_t
from .msg.all import *
from .system import LRID_TO_SRID, SRID_TO_RSRC
from .msg.term import SIMPLE_ENCODERS, COMPLEX_ENCODERS, CONSTANT_ENCODERS

__all__ = [
    'PureCodec',
    'PURE_CODEC'
]


################################################################################

class PureCodec(CodecP):
    """
    Allows for encoding and decoding of 'pure' values that contain no
    user-defined classes or anything else.
    Non-supported resources are ENCODED to NotImplemented, and non-supported
    messages are DECODED to forbidden_xxx.
    """

    ############################################################################

    def enc_any(self, term: TermT) -> TermMsg:
        msg = self._enc_val(term)
        return self.enc_resource(term) if msg is None else msg

    # --------------------------------------------------------------------------

    def enc_exception(self, exc: BaseException) -> 'ExceptionMsg':
        return ExceptionMsg.encode_exception(exc, self)

    def enc_value(self, val: ValueT) -> TermPassByValMsg:
        msg = self._enc_val(val)
        assert msg is not None
        return msg

    def _enc_val(self, val: ValueT) -> TermPassByValMsg | None:

        cls = type(val)

        if msg := const_fn(cls):
            return msg

        if fn := atom_fn(cls):
            return fn(val)

        if fn := compound_fn(cls):
            return fn(val, self)

        if isinstance(val, BaseException):
            return ExceptionMsg.encode_exception(val, self)

        if isinstance(val, Enum):
            return self.enc_any(val._value_)  # type: ignore

        return None

    # --------------------------------------------------------------------------

    def enc_resource(self, resource: ResourceT) -> ResourceMsg:
        return encode_system_resource(resource)

    enc_object          = enc_resource
    enc_class           = enc_resource
    enc_type            = enc_resource
    enc_function        = enc_resource
    enc_module          = enc_resource
    enc_future          = enc_resource
    enc_local_resource  = enc_resource
    enc_remote_resource = enc_resource
    enc_system_resource = enc_resource

    # --------------------------------------------------------------------------

    def enc_sequence(self, seq: Iter) -> Tup[TermMsg]:
        return tuple(map(self.enc_any, seq))

    def enc_record(self, rec: dict) -> Rec[TermMsg]:
        return dict(zip(rec.keys(), map(self.enc_any, rec.values())))

    def enc_args(self, tup: ArgsT) -> ArgsMsg:
        enc_any = self.enc_any
        return tuple(enc_any(v) for v in tup if v is not ARG_DEFAULT)

    def enc_kwargs(self, rec: KwargsT) -> KwargsMsg:
        enc_any = self.enc_any
        return {k: enc_any(v) for k, v in rec.items() if v is not ARG_DEFAULT}

    def enc_annotations(self, rec: AnnotationsT) -> AnnotationsMsg:
        if not rec:
            return {}
        res = {}
        for k, v in rec.items():
            try:
                v_msg = self.enc_any(v)
                res[k] = v_msg
            except E.WarpEncodingError:
                pass
        return res

    def enc_properties(self, rec: PropertiesT) -> PropertiesMsg:
        if not rec:
            return {}
        res = {}
        for k, v in rec.items():
            try:
                v_msg = self.enc_resource(v)
                res[k] = v_msg
            except E.WarpEncodingError:
                pass
        return res

    def enc_methods(self, rec: MethodsT, /) -> 'MethodsMsg':
        enc_fun = self.enc_function
        dct = {}
        for k, v in rec.items():
            kind, func = unpack_method(v)
            dct[k] = kind, enc_fun(func)
        return dct

    def enc_owner(self) -> 'ResourceMsg | None':
        return None  # TODO: Fix

    ############################################################################

    def dec_any(self, msg: TermMsg) -> TermT:
        if not isinstance(msg, TermMsg):
            return NotImplemented
        return msg.decode(self)

    # --------------------------------------------------------------------------

    def dec_exception(self, msg: ExceptionMsg) -> BaseException:
        if not isinstance(msg, ExceptionMsg):
            return NotImplemented
        return msg.decode(self)

    def dec_value(self, msg: TermMsg) -> ValueT:
        if not isinstance(msg, TermPassByValMsg):
            return NotImplemented
        return msg.decode(self)

    # --------------------------------------------------------------------------

    def dec_object(self, obj: ObjectMsg) -> ObjectT:
        return decode_system_resource(obj)

    def dec_class(self, cls: ClassMsg) -> ClassT:
        cls = decode_system_resource(cls)
        return cls if is_class_t(cls) else forbidden_class

    def dec_type(self, typ: TypeMsg) -> TypeT:
        try:
            return self.dec_any(typ)
        except E.WarpDecodingError:
            return Any

    def dec_function(self, fun: FunctionMsg) -> FunctionT:
        fun = self.dec_resource(fun)
        return fun if is_function_t(fun) else forbidden_function

    def dec_module(self, mod: ModuleMsg) -> ModuleT:
        fun = self.dec_resource(mod)
        return fun if is_module_t(fun) else forbidden_module

    def dec_future(self, mod: FutureMsg) -> FutureT:
        fun = self.dec_resource(mod)
        return fun if is_future_t(fun) else forbidden_object

    def dec_resource(self, msg: ResourceMsg) -> ResourceT:
        return decode_system_resource(msg)

    dec_loc = dec_resource
    dec_rem = dec_resource
    dec_sys = dec_resource

    # --------------------------------------------------------------------------

    def dec_sequence(self, seq: Iter[TermMsg]) -> Tup[TermT]:
        return tuple(map(self.dec_any, seq))

    def dec_record(self, rec: Rec[TermMsg]) -> Rec[TermT]:
        if type(rec) is not dict:
            return {}
        return dict(zip(rec.keys(), map(self.dec_any, rec.values())))

    def dec_args(self, tup: ArgsMsg) -> ArgsT:
        dec_any = self.dec_any
        return tuple(v for m in tup if (v := dec_any(m)) is not ARG_DEFAULT)

    def dec_kwargs(self, rec: KwargsMsg) -> KwargsT:
        dec_any = self.dec_any
        return {k: v for k, m in rec.items() if (v := dec_any(m)) is not ARG_DEFAULT}

    def dec_annotations(self, rec: AnnotationsMsg) -> AnnotationsT:
        if type(rec) is not dict:
            return {}
        # TODO: use map_dict
        return dict(zip(rec.keys(), map(self.dec_type, rec.values())))

    def dec_properties(self, rec: PropertiesMsg) -> PropertiesT:
        if type(rec) is not dict:
            return {}
        # TODO: use map_dict
        return dict(zip(rec.keys(), map(self.dec_resource, rec.values())))

    def dec_methods(self, rec: MethodsMsg) -> MethodsT:
        if type(rec) is not dict:
            return {}
        dct = {}
        for k, (kind, fun_msg) in rec.items():
            dct[k] = pack_method(kind, self.dec_function(fun_msg))
        return dct

    # --------------------------------------------------------------------------

    def get_repl(self) -> 'ReplP | None':
        return None

    def future_to_id(self, future: FutureT, /) -> FutureID:
        return 0

    def future_from_id(self, future_id: FutureID, /) -> FutureT:
        return forbidden_object

    ############################################################################

    def enc_context(self) -> 'EncoderContextP':
        return self

    def dec_context(self, msgs: 'Tup[DefinitionMsg]', /):
        return self

    def enc_context_defs(self) -> 'Tup[DefinitionMsg]':
        return ()

    def enc_before(self, lrid: LocalRID, /) -> GlobalRID | None:
        return None

    def dec_before(self, grid: GlobalRID, /) -> LocalRID | None:
        return None

    def __enter__(self) -> None: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...


################################################################################

PURE_CODEC = PureCodec()

################################################################################

def decode_system_resource(msg: ResourceMsg) -> ResourceT:
    if not isinstance(msg, SystemResourceMsg):
        return forbidden_object
    return SRID_TO_RSRC.get(msg.sid, forbidden_object)

def encode_system_resource(res: ResourceT) -> SystemResourceMsg:
    if sid := LRID_TO_SRID.get(id(res)):
        return SystemResourceMsg(sid)
    raise E.WarpEncodingError("not a system resource: ", res)

################################################################################

const_fn = CONSTANT_ENCODERS.get
atom_fn = SIMPLE_ENCODERS.get
compound_fn = COMPLEX_ENCODERS.get
