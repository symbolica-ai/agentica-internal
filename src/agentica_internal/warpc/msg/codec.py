# fmt: off

from typing import Protocol, NoReturn, Iterable as Iter, TYPE_CHECKING

from ..alias import *
from ..kinds import *

__all__ = [
    'EncoderP',
    'EncoderContextP',
    'DecoderP',
    'DecoderContextP',
    'CodecP',
    'NULL_CODEC'
]

################################################################################

if TYPE_CHECKING:
    from ..repl import ReplP
    from .term import TermMsg, TermPassByValMsg
    from .term_resource import ResourceMsg, LocalResourceMsg, RemoteResourceMsg, SystemResourceMsg
    from .resource_def import DefinitionMsg
    from .term_exception import ExceptionMsg
    from .msg_aliases import *

################################################################################

class EncoderP(Protocol):
    """
    Protocol (implemented by `warp.Frame`) that covers encoding of python values
    into messages.

    `enc_loc` only encodes resources that are local (NOT virtual).
    `enc_rem` only encodes resources that are remote (ARE virtual).
    `enc_sys` only encodes resources that are builtin system resources.

    `enc_args`, `enc_kwargs` drop ARG_DEFAULT values.
    """

    def enc_any(self, term: TermT, /)                -> 'TermMsg': ...

    def enc_exception(self, exc: BaseException, /)   -> 'ExceptionMsg': ...
    def enc_value(self, val: ValueT, /)              -> 'TermPassByValMsg': ...

    def enc_object(self, obj: ObjectT, /)            -> 'ObjectMsg': ...
    def enc_class(self, cls: ClassT, /)              -> 'ClassMsg': ...
    def enc_type(self, cls: TypeT, /)                -> 'TypeMsg': ...
    def enc_function(self, fun: FunctionT, /)        -> 'FunctionMsg': ...
    def enc_module(self, mod: ModuleT, /)            -> 'ModuleMsg': ...
    def enc_future(self, fut: FutureT, /)            -> 'FutureMsg': ...

    def enc_resource(self, res: ResourceT, /)        -> 'ResourceMsg': ...
    def enc_local_resource(self, res: ResourceT, /)  -> 'LocalResourceMsg': ...
    def enc_remote_resource(self, res: ResourceT, /) -> 'RemoteResourceMsg': ...
    def enc_system_resource(self, res: ResourceT, /) -> 'SystemResourceMsg': ...

    def enc_sequence(self, seq: Iter[TermT], /)      -> 'Tup[TermMsg]': ...
    def enc_record(self, dct: Rec[TermT], /)         -> 'Rec[TermMsg]': ...

    def enc_args(self, tup: ArgsT, /)                -> 'ArgsMsg': ...
    def enc_kwargs(self, rec: KwargsT, /)            -> 'KwargsMsg': ...

    def enc_methods(self, rec: MethodsT, /)          -> 'MethodsMsg': ...
    def enc_annotations(self, rec: AnnotationsT, /)  -> 'AnnotationsMsg': ...
    def enc_properties(self, rec: PropertiesT, /)    -> 'PropertiesMsg': ...

    def enc_owner(self)                              -> 'ResourceMsg': ...

    def enc_context(self) -> 'EncoderContextP': ...

    # this takes an existing future and returns a future_id for it, used when describing futures
    # as FutureData objects
    def future_to_id(self, future: FutureT, /) -> FutureID: ...

    def enc_before(self, lrid: LocalRID, /) -> GlobalRID | None: ...


################################################################################

class EncoderContextP(Protocol):
    """
    A temporary context in which new definitions that are entrained during
    encoding can be found at the end of encoding.
    """

    def __enter__(self) -> None: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...

    def enc_context_defs(self) -> 'Tup[DefinitionMsg]': ...


################################################################################

class DecoderP(Protocol):
    """
    Protocol (implemented by `warp.Frame`) that covers decoding of python values
    into messages.
    """

    def dec_any(self, msg: 'TermMsg', /)                       -> TermT: ...

    def dec_value(self, msg: 'TermPassByValMsg', /)            -> ValueT: ...
    def dec_exception(self, msg: 'ExceptionMsg', /)            -> BaseException: ...

    def dec_object(self, msg: 'ObjectMsg', /)                  -> ObjectT: ...
    def dec_class(self, msg: 'ClassMsg', /)                    -> ClassT: ...
    def dec_type(self, msg: 'TypeMsg', /)                      -> TypeT: ...
    def dec_function(self, msg: 'FunctionMsg', /)              -> FunctionT: ...
    def dec_module(self, msg: 'ModuleMsg', /)                  -> ModuleT: ...
    def dec_future(self, rec: 'FutureMsg', /)                  -> FutureT: ...

    def dec_resource(self, msg: 'ResourceMsg', /)              -> ResourceT: ...
    def dec_local_resource(self, msg: 'LocalResourceMsg', /)   -> ResourceT: ...
    def dec_remote_resource(self, msg: 'RemoteResourceMsg', /) -> ResourceT: ...
    def dec_system_resource(self, msg: 'SystemResourceMsg', /) -> ResourceT: ...

    def dec_sequence(self, seq: 'Iter[TermMsg]', /)            -> Tup[TermT]: ...
    def dec_record(self, rec: 'Rec[TermMsg]', /)               -> Rec[TermT]: ...

    def dec_args(self, tup: 'ArgsMsg', /)                      -> ArgsT: ...
    def dec_kwargs(self, rec: 'KwargsMsg', /)                  -> KwargsT: ...
    def dec_methods(self, rec: 'MethodsMsg', /)                -> MethodsT: ...
    def dec_annotations(self, rec: 'AnnotationsMsg', /)        -> AnnotationsT: ...
    def dec_properties(self, rec: 'PropertiesMsg', /)          -> PropertiesT: ...

    def get_repl(self) -> 'ReplP | None': ...

    def dec_context(self, msgs: 'Tup[DefinitionMsg]', /) -> 'DecoderContextP': ...

    # this creates or gets a future with a given future_id, used when taking
    # FutureData objects and turning them into futures. this will either be a
    # new totally virtual future, or an existing future that has a matching ID
    def future_from_id(self, future_id: FutureID, /) -> FutureT: ...

    def dec_before(self, grid: GlobalRID, /) -> LocalRID | None: ...


################################################################################

class DecoderContextP(Protocol):
    """
    A temporary context in which messages are decoded in the context of
    auxiliary definitions, which do not have to be in any particular order.
    """

    def __enter__(self) -> None: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...


################################################################################

class CodecP(EncoderP, DecoderP):
    """
    Combines encoding and decoding into one Protocol.
    """
    ...


################################################################################

def _none(*args) -> None:
    return None

def _raise(*args) -> NoReturn:
    raise RuntimeError("no encoder available")

class NullCodec(CodecP):

    dec_any              = _none
    dec_value            = _raise
    dec_exception        = _raise
    dec_sequence         = _raise
    dec_record           = _raise
    dec_object           = _raise
    dec_class            = _raise
    dec_type             = _raise
    dec_function         = _raise
    dec_module           = _raise
    dec_future           = _raise
    dec_resource         = _raise
    dec_local_resource   = _raise
    dec_remote_resource  = _raise
    dec_system_resource  = _raise
    dec_args             = _raise
    dec_kwargs           = _raise
    dec_methods          = _raise
    dec_annotations      = _raise
    dec_properties       = _raise

    enc_any              = _raise
    enc_exception        = _raise
    enc_value            = _raise
    enc_object           = _raise
    enc_class            = _raise
    enc_type             = _raise
    enc_function         = _raise
    enc_module           = _raise
    enc_future           = _raise
    enc_resource         = _raise
    enc_local_resource   = _raise
    enc_remote_resource  = _raise
    enc_system_resource  = _raise
    enc_sequence         = _raise
    enc_record           = _raise
    enc_args             = _raise
    enc_kwargs           = _raise
    enc_methods          = _raise
    enc_annotations      = _raise
    enc_properties       = _raise

    enc_owner            = _none
    get_repl             = _none

    enc_before           = _none
    dec_before           = _none

    future_from_id       = _raise
    future_to_id         = _raise

    def enc_context(self) -> 'EncoderContextP':
        return self

    def dec_context(self, msgs: 'Tup[DefinitionMsg]', /):
        return self

    def enc_context_defs(self) -> 'Tup[DefinitionMsg]':
        return ()

    def __enter__(self) -> None: ...
    def __exit__(self, exc_type, exc_val, exc_tb) -> None: ...


NULL_CODEC = NullCodec()
