# fmt: off

################################################################################

from .__json import pprint_json, fmt_json
from .__msgpack import pprint_msgpack, fmt_msgpack

################################################################################

from .base import Msg

from .bad import BadMsg, NO_MSG, CORRUPT_MSG, UNEXPECTED_MSG, is_bad_msg

from .codec import (
    EncoderP,
    EncoderContextP,
    DecoderP,
    DecoderContextP,
    CodecP,
    NULL_CODEC
)

################################################################################

from .term import (
    TermMsg,
    TermPassByRefMsg,
    TermPassByValMsg,
)

from .term_exception import (
    ExceptionMsg,
    SystemExceptionMsg,
    StopIterationMsg,
    UserExceptionMsg,
    ShallowUserExceptionMsg,
    DeepUserExceptionMsg,
    InternalExceptionMsg
)

from .term_atom import (
    AtomMsg,
    NumberMsg, ComplexMsg, DecimalMsg,
    SingletonMsg, NoneMsg,
    StrLikeMsg, StrMsg, BytesMsg,
    NotImplMsg, EllipsisMsg, ClosedMsg
)

from .term_container import (
    ContainerMsg,
    MappingMsg, DictMsg,
    SequenceMsg, ListMsg, TupleMsg, SetMsg, FrozenSetMsg,
)

from .term_core import (
    RangeMsg,
    SliceMsg,
    ZipMsg,
    MapMsg,
    FilterMsg,
    EnumerateMsg
)

from .term_iter import (
    ByValueIterMsg,
    DataIterMsg,
    CallIterMsg,
    RangeIterMsg,
)

from .term_special import (
    SlotObjMsg,
    ReduceObjMsg,
    ConstructObjMsg,
    RegexPatternMsg,
    RegexMatchMsg,
    ClassUnionMsg,
    EnumMemberMsg,
    EnumKeyMsg,
    EnumValMsg
)

from .term_wrapper import (
    JsonMsg,
    RawMsg,
    MsgMsg,
    FileMsg,
)

from .term_resource import (
    ResourceMsg,
    UserResourceMsg,
    SystemResourceMsg,
    RemoteResourceMsg,
    LocalResourceMsg,
    class_to_system_msg,
    class_to_system_id,
    pointer_to_system_id,
    pointer_to_system_msg,
)


from .term_lambda import LambdaMsg, SyntaxMsg

from .signature_msg import SignatureMsg

################################################################################

from .resource_def import DefinitionMsg

from .resource_data import (
    ResourceDataMsg,
    ObjectDataMsg, ClassDataMsg, FunctionDataMsg, ModuleDataMsg, CoroutineDataMsg,
    TypeDataMsg, TypeAliasDataMsg, TypeVarDataMsg, GenericAliasDataMsg,
    CallableTypeDataMsg, TypeUnionDataMsg, IteratorDataMsg, EnumClassDataMsg,
    PropertyDataMsg, ExceptionDataMsg
)

################################################################################

from .rpc import RPCMsg

from .rpc_framed import (
    FramedMsg,
    FramedRequestMsg,
    FramedResponseMsg
)

################################################################################

from .rpc_request import RequestMsg

from .rpc_request_repl import (
    ReplRequestMsg,
    ReplInitMsg,
    ReplCallMethodMsg,
    ReplRunCodeMsg,
)

from .rpc_request_resource import (
    ResourceRequestMsg,
    ResourceNewMsg,
    ResourceCallRequestMsg,
    ResourceCallFunctionMsg,
    ResourceCallMethodMsg,
    ResourceCallSystemMethodMsg,
    ResourceAttrRequestMsg,
    ResourceHasAttrMsg,
    ResourceGetAttrMsg,
    ResourceSetAttrMsg,
    ResourceDelAttrMsg,
)

from .rpc_request_future import (
    FutureRequestMsg,
    CancelFutureMsg,
    CompleteFutureMsg,
)

from .rpc_event import (
    EventMsg,
    FutureEventMsg,
    FutureCanceledMsg,
    FutureCompletedMsg,
)

from .rpc_sideband import (
    SidebandMsg,
    ChannelMsg,
    RemotePrintMsg,
    FutureResultMsg,
    CHANNEL_CLOSED_MSG
)

################################################################################

from .term_result import ResultMsg

################################################################################

from .vars import VarsMsg, NO_VARS

################################################################################

from . import system as SYS

################################################################################

from .msg_aliases import (
    ArgsMsg,
    KwargsMsg,
    MethodsMsg,
    AttributesMsg,
    TypeMsg,
    ClassMsg,
    ObjectMsg,
    FunctionMsg,
    ModuleMsg,
    FutureMsg,
    PropertyMsg,
    ExceptionRefMsg,
    AnnotationsMsg,
    PropertiesMsg,
    SrcLocationMsg
)

################################################################################

from .__finalize import finalize_message_classes

################################################################################


__all__ = [
    'Msg',

    'ArgsMsg',
    'KwargsMsg',
    'MethodsMsg',
    'AttributesMsg',
    'TypeMsg',
    'ClassMsg',
    'ObjectMsg',
    'FunctionMsg',
    'ModuleMsg',
    'FutureMsg',
    'PropertyMsg',
    'ExceptionRefMsg',
    'AnnotationsMsg',
    'PropertiesMsg',
    'SrcLocationMsg',

    'EncoderP',
    'EncoderContextP',
    'DecoderP',
    'DecoderContextP',
    'CodecP',
    'NULL_CODEC',

    'BadMsg',
    'NO_MSG',
    'CORRUPT_MSG',
    'UNEXPECTED_MSG',
    'is_bad_msg',

    'TermMsg',
    'TermPassByValMsg',
    'TermPassByRefMsg',

    'AtomMsg',
    'NumberMsg',
    'ComplexMsg',
    'DecimalMsg',
    'SingletonMsg',
    'NoneMsg',
    'NotImplMsg',
    'EllipsisMsg',
    'ClosedMsg',
    'StrLikeMsg',
    'StrMsg',
    'BytesMsg',
    'ContainerMsg',
    'MappingMsg',
    'DictMsg',
    'SequenceMsg',
    'ListMsg',
    'TupleMsg',
    'SetMsg',
    'FrozenSetMsg',
    'RangeMsg',
    'SliceMsg',
    'ZipMsg',
    'MapMsg',
    'FilterMsg',
    'EnumerateMsg',
    'ExceptionMsg',
    'SystemExceptionMsg',
    'UserExceptionMsg',
    'StopIterationMsg',
    'ShallowUserExceptionMsg',
    'DeepUserExceptionMsg',
    'InternalExceptionMsg',
    'ByValueIterMsg',
    'DataIterMsg',
    'CallIterMsg',
    'RangeIterMsg',
    'SlotObjMsg',
    'ReduceObjMsg',
    'ConstructObjMsg',
    'RegexPatternMsg',
    'RegexMatchMsg',
    'ClassUnionMsg',
    'EnumMemberMsg',
    'EnumKeyMsg',
    'EnumValMsg',
    'SyntaxMsg',
    'LambdaMsg',
    'SignatureMsg',
    'JsonMsg',
    'RawMsg',
    'MsgMsg',
    'FileMsg',
    'ResourceMsg',
    'UserResourceMsg',
    'SystemResourceMsg',
    'RemoteResourceMsg',
    'LocalResourceMsg',
    'class_to_system_msg',
    'class_to_system_id',
    'pointer_to_system_msg',
    'pointer_to_system_id',

    'DefinitionMsg',
    'ResourceDataMsg',
    'ObjectDataMsg',
    'ClassDataMsg',
    'FunctionDataMsg',
    'CoroutineDataMsg',
    'ModuleDataMsg',
    'TypeDataMsg',
    'TypeAliasDataMsg',
    'TypeVarDataMsg',
    'GenericAliasDataMsg',
    'CallableTypeDataMsg',
    'TypeUnionDataMsg',
    'IteratorDataMsg',
    'EnumClassDataMsg',
    'PropertyDataMsg',
    'ExceptionDataMsg',

    'RPCMsg',
    'FramedMsg',
    'FramedRequestMsg',
    'FramedResponseMsg',

    'RequestMsg',

    'ResourceRequestMsg',
    'ResourceCallRequestMsg',
    'ResourceNewMsg',
    'ResourceCallFunctionMsg',
    'ResourceCallMethodMsg',
    'ResourceCallSystemMethodMsg',
    'ResourceAttrRequestMsg',
    'ResourceHasAttrMsg',
    'ResourceGetAttrMsg',
    'ResourceSetAttrMsg',
    'ResourceDelAttrMsg',

    'FutureRequestMsg',
    'CancelFutureMsg',
    'CompleteFutureMsg',

    'EventMsg',
    'FutureEventMsg',
    'FutureCanceledMsg',
    'FutureCompletedMsg',

    'ReplRequestMsg',
    'ReplInitMsg',
    'ReplCallMethodMsg',
    'ReplRunCodeMsg',

    'SidebandMsg',
    'ChannelMsg',
    'RemotePrintMsg',
    'FutureResultMsg',
    'CHANNEL_CLOSED_MSG',

    'ResultMsg',

    'NO_VARS',
    'SYS',

    'VarsMsg',

    'msgpack_to_rpc_msg',
    'msgpack_to_vars_msg',

    'rpc_msg_to_msgpack',
    'vars_msg_to_msgpack',

    'pprint_json',
    'pprint_msgpack',
    'fmt_json',
    'fmt_msgpack',

    'bytes_to_repl_init_data',
]


################################################################################

finalize_message_classes()

################################################################################

msgpack_to_rpc_msg = RPCMsg.from_msgpack
msgpack_to_vars_msg = VarsMsg.from_msgpack

def rpc_msg_to_msgpack(msg: RPCMsg) -> bytes:
    assert isinstance(msg, RPCMsg)
    return msg.to_msgpack()

def vars_msg_to_msgpack(msg: VarsMsg) -> bytes:
    assert isinstance(msg, VarsMsg)
    return msg.to_msgpack()

################################################################################

def bytes_to_repl_init_data(globals_data: bytes, locals_data: bytes) -> tuple[ReplInitMsg,
tuple[DefinitionMsg, ...]]:

    globals_msg = VarsMsg.from_msgpack(globals_data)
    locals_msg = VarsMsg.from_msgpack(locals_data)

    init_msg = ReplInitMsg(globals_msg.vars, locals_msg.vars)
    def_msgs = globals_msg.defs + locals_msg.defs

    return init_msg, def_msgs
