from typing import Any, Literal

from msgspec import UNSET, Struct, UnsetType
from msgspec.json import Decoder, Encoder

from agentica_internal.core.print import pprint

__all__ = [
    #  structures
    "FrameUID",
    "DefnUID",
    "UniMsg",  # data or RPC
    # Data messages
    "ConceptUniMsg",
    "NoDefUniMsg",  # ref or value
    "DefUniMsg",  # resource or annotation
    "DefPayload",
    ## Reference messages
    "RefUniMsg",
    ## Value messages
    "ValueUniMsg",
    "AtomUniMsg",
    "ContainerUniMsg",
    ### Atomic values
    "NoneUniMsg",
    "BoolUniMsg",
    "IntUniMsg",
    "FloatUniMsg",
    "StrUniMsg",
    "BytesUniMsg",
    "TypeStringRefUniMsg",
    ### Symbols
    "EnumValUniMsg",
    ### Container values
    "ArrayUniMsg",
    "SetUniMsg",
    "MapUniMsg",
    "TupleUniMsg",
    ## Resource messages
    "ResourceDefUniMsg",
    "PlaceholderUniMsg",
    "ClassField",
    "ClassMethod",
    "TypeArgument",
    "IndexSignature",
    "ClassPayload",
    "ClassDefUniMsg",
    "FunctionArgument",
    "FunctionPayload",
    "FunctionDefUniMsg",
    "ObjectPayload",
    "ObjectDefUniMsg",
    ## Annotation messages
    "AnnotationDefUniMsg",
    "UnionPayload",
    "UnionUniMsg",
    "IntersectionPayload",
    "IntersectionUniMsg",
    "InterfaceUniMsg",
    "Membership",
    "MethodSignatureUniMsg",
    # RPC messages
    "RpcUniMsg",
    "ChannelUniMsg",
    "RequestUniMsg",
    "RequestPayload",
    "ResponseUniMsg",
    "ResponsePayload",
    # Request messages
    "CallArg",
    "CallNewPayload",
    "CallNewUniMsg",
    "CallFunctionPayload",
    "CallFunctionUniMsg",
    "CallMethodPayload",
    "CallMethodUniMsg",
    "HasAttrPayload",
    "HasAttrUniMsg",
    "GetAttrPayload",
    "GetAttrUniMsg",
    "SetAttrPayload",
    "SetAttrUniMsg",
    "DelAttrPayload",
    "DelAttrUniMsg",
    "InstanceOfPayload",
    "InstanceOfUniMsg",
    # Response messages
    "OkUniMsg",
    "ErrPayload",
    "ErrUniMsg",
    "ResPayload",
    "ResUniMsg",
    # Event messages
    "EventUniMsg",
    "FutureCanceledUniMsg",
    "FutureCompletedUniMsg",
    # CODEC
    'json_to_uni',
    'json_to_rpc_uni',
    'json_to_def_uni',
    'json_to_request_uni',
    'json_to_response_uni',
    'uni_to_json',
    'referentialize',
    'make_client_ref',
]

###

type ResourceUniMsg = ClassDefUniMsg | FunctionDefUniMsg | ObjectDefUniMsg
type AnnotationUniMsg = UnionUniMsg | IntersectionUniMsg | InterfaceUniMsg | MethodSignatureUniMsg

# Explicit unions for native decoding
type NoDefMsgUnion = (
    NoneUniMsg
    | BoolUniMsg
    | IntUniMsg
    | FloatUniMsg
    | StrUniMsg
    | TypeStringRefUniMsg
    | BytesUniMsg
    | EnumValUniMsg
    | ArrayUniMsg
    | SetUniMsg
    | MapUniMsg
    | TupleUniMsg
    | RefUniMsg
    | GenericExceptionUniMsg
    | ForeignExceptionUniMsg
    | InternalErrorUniMsg
    | NoDefUniMsg
)

type DefMsgUnion = (
    ClassDefUniMsg
    | FunctionDefUniMsg
    | ObjectDefUniMsg
    | UnionUniMsg
    | IntersectionUniMsg
    | InterfaceUniMsg
    | MethodSignatureUniMsg
    | PlaceholderUniMsg
    | DefUniMsg
)

type RequestUnion = (
    CallNewUniMsg
    | CallFunctionUniMsg
    | CallMethodUniMsg
    | HasAttrUniMsg
    | GetAttrUniMsg
    | SetAttrUniMsg
    | DelAttrUniMsg
    | InstanceOfUniMsg
)

type TermUnion = ValueUniMsg | DefMsgUnion

type ConceptUnion = NoDefMsgUnion | DefMsgUnion

type ResponseUnion = OkUniMsg | ErrUniMsg | ResUniMsg

type EventUnion = FutureCanceledUniMsg | FutureCompletedUniMsg

type RpcUnion = RequestUnion | ResponseUnion | EventUnion | ChannelUniMsg

type AnyUni = NoDefMsgUnion | DefMsgUnion | RpcUnion

type FrameID = int
type DefnID = int

type WorldEnum = Literal['client', 'server']
type MembershipKind = Literal['static', 'instance']

###


class FrameUID(Struct):
    world: WorldEnum
    frame: FrameID


class DefnUID(Struct):
    world: WorldEnum
    resource: DefnID
    # Added merely for Python compatibility
    py_world: int = -1
    py_resource: int = -1
    py_frame: int = -1

    def __hash__(self) -> int:  # make hashable for dict/set usage
        return hash((self.world, self.resource, self.py_world, self.py_resource, self.py_frame))


###


class UniMsg(Struct, tag_field='kind'):  # data or RPC
    def __short_str__(self) -> str:
        """Determines how this will get formatted in stack traces."""
        return type(self).__name__ + '(...)'

    def pprint(self) -> None:
        """Used in logging."""
        pprint(json_to_python(uni_to_json(self)))


class ConceptUniMsg(UniMsg):
    pass


class NoDefUniMsg(ConceptUniMsg):  # ref or value
    pass


class DefPayload(Struct, kw_only=True):
    is_top_level: bool = False


class DefUniMsg(ConceptUniMsg):  # resource or annotation
    uid: DefnUID
    payload: DefPayload


# Take a concept, churn out a ref
def referentialize(msg: ConceptUniMsg) -> NoDefUniMsg:
    # HACK: Pass through atoms (StrUniMsg, IntUniMsg, etc.) unchanged
    # This allows TypeScript to embed literal values in TypeArgument.type for typing.Literal support
    if isinstance(msg, NoDefUniMsg):
        return msg
    elif isinstance(msg, ClassDefUniMsg):
        return RefUniMsg(uid=msg.uid, system=msg.payload.system_resource)
    elif isinstance(msg, DefUniMsg):
        return RefUniMsg(uid=msg.uid)
    else:
        raise ValueError(f'Unknown DataUniMsg: {msg}')


def make_client_ref(uid: int) -> 'RefUniMsg':
    return RefUniMsg(uid=DefnUID(world='client', resource=uid))


###


class RefUniMsg(NoDefUniMsg, tag='ref', tag_field='kind'):
    uid: DefnUID
    system: bool = False


###


class ValueUniMsg(NoDefUniMsg):
    pass


###


class AtomUniMsg(ValueUniMsg):
    pass


class NoneUniMsg(AtomUniMsg, tag='none', tag_field='kind'):
    val: None = None


class BoolUniMsg(AtomUniMsg, tag='bool', tag_field='kind'):
    val: bool


class IntUniMsg(AtomUniMsg, tag='int', tag_field='kind'):
    val: int


class FloatUniMsg(AtomUniMsg, tag='float', tag_field='kind'):
    val: float


class StrUniMsg(AtomUniMsg, tag='str', tag_field='kind'):
    val: str


class BytesUniMsg(AtomUniMsg, tag='bytes', tag_field='kind'):
    val: bytes


###


class TypeStringRefUniMsg(RefUniMsg, tag='type_string', tag_field='kind'):
    uid: DefnUID  # Matches RefUniMsg protocol
    name: str = ''


###


class EnumValUniMsg(ValueUniMsg, tag='enum_val', tag_field='kind'):
    val: StrUniMsg | IntUniMsg | FloatUniMsg
    cls: RefUniMsg


###


class ContainerUniMsg(ValueUniMsg):
    pass


class ArrayUniMsg(ContainerUniMsg, tag='array', tag_field='kind'):
    val: list[NoDefMsgUnion]


class SetUniMsg(ContainerUniMsg, tag='set', tag_field='kind'):
    val: list[NoDefMsgUnion]


class MapPayload(Struct):
    keys: list[NoDefMsgUnion]
    vals: list[NoDefMsgUnion]


class MapUniMsg(ContainerUniMsg, tag='map', tag_field='kind'):
    val: MapPayload


class TupleUniMsg(ContainerUniMsg, tag='tuple', tag_field='kind'):
    val: list[NoDefMsgUnion]


###


class GenericExceptionUniMsg(NoDefUniMsg, tag='generic_excp', tag_field='kind', kw_only=True):
    excp_cls_name: str
    excp_str_args: list[str]
    excp_stack: list[str]


class ForeignExceptionUniMsg(NoDefUniMsg, tag='foreign_excp', tag_field='kind', kw_only=True):
    excp_cls: RefUniMsg
    excp_args: list[NoDefMsgUnion]


class InternalErrorUniMsg(NoDefUniMsg, tag='internal_error', tag_field='kind', kw_only=True):
    error: str


###


class ResourceDefUniMsg(DefUniMsg):
    uid: DefnUID
    payload: Any


###


class PlaceholderUniMsg(ResourceDefUniMsg):
    payload: dict[str, Any] | UnsetType = UNSET


###


class FunctionArgument(Struct):
    name: str
    type: RefUniMsg | None
    optional: bool | UnsetType = UNSET
    default: NoDefMsgUnion | UnsetType = UNSET
    rest: bool | UnsetType = UNSET


class FunctionPayload(DefPayload):
    name: str
    arguments: list[FunctionArgument]
    doc: str | UnsetType = UNSET
    returnType: RefUniMsg | UnsetType = UNSET
    module: str | UnsetType = UNSET


class FunctionDefUniMsg(ResourceDefUniMsg, tag='func', tag_field='kind'):
    uid: DefnUID
    payload: FunctionPayload


###


class ClassField(Struct):
    name: str
    type: RefUniMsg
    is_private: bool | UnsetType = UNSET
    is_static: bool | UnsetType = UNSET
    default: NoDefMsgUnion | UnsetType = UNSET
    is_optional: bool | UnsetType = UNSET


class ClassMethod(Struct):
    name: str
    function: RefUniMsg
    is_private: bool | UnsetType = UNSET
    is_static: bool | UnsetType = UNSET


class TypeArgument(Struct):
    name: str
    # HACK: May be AtomUniMsgs for Literal types
    type: RefUniMsg | StrUniMsg | IntUniMsg | FloatUniMsg | BoolUniMsg


class IndexSignature(Struct):
    key_type: RefUniMsg
    value_type: RefUniMsg
    map_type: RefUniMsg


class ClassPayload(DefPayload):
    name: str
    fields: list[ClassField] | UnsetType = UNSET
    methods: list[ClassMethod] | UnsetType = UNSET
    doc: str | UnsetType = UNSET
    module: str | UnsetType = UNSET
    ctor_args: list["FunctionArgument"] | UnsetType = UNSET
    supplied_type_args: list["TypeArgument"] | FunctionDefUniMsg | UnsetType = UNSET
    instance_of_generic: DefnUID | UnsetType = UNSET
    bases: list[RefUniMsg] | UnsetType = UNSET
    system_resource: bool = False
    is_plain_object_type: bool | UnsetType = UNSET
    index_signature: IndexSignature | UnsetType = UNSET


class ClassDefUniMsg(ResourceDefUniMsg, tag='cls', tag_field='kind'):
    uid: DefnUID
    payload: ClassPayload


###


class ObjectPayload(DefPayload):
    name: str | UnsetType = UNSET
    cls: RefUniMsg | UnsetType = UNSET  # NOTE: note always a class, could be an annotation
    keys: list[str] | UnsetType = UNSET


class ObjectDefUniMsg(ResourceDefUniMsg, tag='obj', tag_field='kind'):
    uid: DefnUID
    payload: ObjectPayload


###


# Annotation messages
class AnnotationDefUniMsg(DefUniMsg):
    uid: DefnUID
    payload: Any


###


class UnionPayload(DefPayload):
    classes: list[RefUniMsg]


class UnionUniMsg(AnnotationDefUniMsg, tag='union', tag_field='kind'):
    uid: DefnUID
    payload: UnionPayload


###


class IntersectionPayload(DefPayload):
    classes: list[RefUniMsg]


class IntersectionUniMsg(AnnotationDefUniMsg, tag='intersection', tag_field='kind'):
    uid: DefnUID
    payload: IntersectionPayload


###


class InterfaceUniMsg(AnnotationDefUniMsg, tag='interface', tag_field='kind'):
    uid: DefnUID
    payload: ClassPayload


###


class Membership(Struct):
    uid: DefnUID
    kind: MembershipKind


class MethodSignatureUniMsg(AnnotationDefUniMsg, tag='methodsig', tag_field='kind'):
    uid: DefnUID
    methodOf: Membership
    payload: FunctionPayload


def toMethodSignature(msg: FunctionDefUniMsg, mem: Membership) -> MethodSignatureUniMsg:
    return MethodSignatureUniMsg(uid=msg.uid, methodOf=mem, payload=msg.payload)


###


# RPC messages
class RpcUniMsg(UniMsg, tag_field='kind', kw_only=True):
    pass


# RPC messages


# not used by typescript SDK, used for debugging
# does not handle errors because the way the Uni protocol message ADT is split
# up is highly verbose and repetitive, and I don't want to make it even more so
class ChannelUniMsg(RpcUniMsg, kw_only=True):
    value: 'NoDefMsgUnion'
    last: bool
    defs: list[DefMsgUnion] = []


class RequestPayload(Struct):
    pass


class RequestUniMsg(RpcUniMsg, tag_field='kind', kw_only=True):
    payload: RequestPayload
    parentFID: FrameID = -1
    selfFID: FrameID = -1
    requestedFID: FrameID = -1
    defs: list[DefMsgUnion] = []


class ResponsePayload(Struct):
    pass


class ResponseUniMsg(RpcUniMsg, tag_field='kind', kw_only=True):
    parentFID: FrameID = -1
    selfFID: FrameID = -1
    iid: str | UnsetType = UNSET


###


class CallArg(Struct):
    name: str  # For bookkeeping
    val: NoDefMsgUnion


class CallNewPayload(RequestPayload):
    cls: RefUniMsg
    args: list[CallArg]
    type_args: dict[str, RefUniMsg] | UnsetType = UNSET


class CallNewUniMsg(RequestUniMsg, tag='new', tag_field='kind'):
    payload: CallNewPayload


###


class CallFunctionPayload(RequestPayload):
    fun: RefUniMsg
    args: list[CallArg]


class CallFunctionUniMsg(RequestUniMsg, tag='callfun', tag_field='kind'):
    payload: CallFunctionPayload


###


class CallMethodPayload(RequestPayload):
    owner: RefUniMsg
    method_name: str
    args: list[CallArg]
    method_ref: RefUniMsg | UnsetType = UNSET


class CallMethodUniMsg(RequestUniMsg, tag='callmethod', tag_field='kind'):
    payload: CallMethodPayload


###


class HasAttrPayload(RequestPayload):
    owner: RefUniMsg
    attr: str | None


class HasAttrUniMsg(RequestUniMsg, tag='hasattr', tag_field='kind'):
    payload: HasAttrPayload


###


class GetAttrPayload(RequestPayload):
    owner: RefUniMsg
    attr: str | None


class GetAttrUniMsg(RequestUniMsg, tag='getattr', tag_field='kind'):
    payload: GetAttrPayload


###


class SetAttrPayload(RequestPayload):
    owner: RefUniMsg
    attr: str | None
    val: NoDefMsgUnion


class SetAttrUniMsg(RequestUniMsg, tag='setattr', tag_field='kind'):
    payload: SetAttrPayload


###


class DelAttrPayload(RequestPayload):
    owner: RefUniMsg
    attr: str | None


class DelAttrUniMsg(RequestUniMsg, tag='delattr', tag_field='kind'):
    payload: DelAttrPayload


###


class InstanceOfPayload(RequestPayload):
    owner: RefUniMsg
    cls: RefUniMsg


class InstanceOfUniMsg(RequestUniMsg, tag='instanceof', tag_field='kind'):
    payload: InstanceOfPayload


###


# Response messages
class OkUniMsg(ResponseUniMsg, tag='ok', tag_field='kind', kw_only=True):
    payload: None = None


###


class ErrPayload(ResponsePayload):
    error: ForeignExceptionUniMsg | InternalErrorUniMsg | GenericExceptionUniMsg


class ErrUniMsg(ResponseUniMsg, tag='err', tag_field='kind', kw_only=True):
    payload: ErrPayload


###


class ResPayload(ResponsePayload):
    result: DefMsgUnion | NoDefMsgUnion


class ResUniMsg(ResponseUniMsg, tag='result', tag_field='kind', kw_only=True):
    payload: ResPayload
    defs: list[DefMsgUnion] = []


###


class EventUniMsg(RpcUniMsg, tag_field='kind'):
    future_id: int


class FutureCanceledUniMsg(EventUniMsg, tag='future_canceled', tag_field='kind', kw_only=True):
    future_id: int


class FutureCompletedUniMsg(EventUniMsg, tag='future_completed', tag_field='kind'):
    future_id: int
    result: ResUniMsg | ErrUniMsg


json_to_uni = Decoder(AnyUni).decode
json_to_rpc_uni = Decoder(RpcUnion).decode
json_to_concept_uni = Decoder(ConceptUnion).decode
json_to_def_uni = Decoder(DefMsgUnion).decode
json_to_term_uni = Decoder(TermUnion).decode
json_to_request_uni = Decoder(RequestUnion).decode
json_to_response_uni = Decoder(ResponseUnion).decode
uni_to_json = Encoder().encode
json_to_python = Decoder().decode
