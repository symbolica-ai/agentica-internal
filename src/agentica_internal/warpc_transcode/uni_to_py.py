from typing import Protocol as TypingProtocol

from agentica_internal.warpc.alias import *
from agentica_internal.warpc.messages import *
from agentica_internal.warpc.msg.resource_data import (
    ClassDataMsg,
    ForwardRefDataMsg,
    FunctionDataMsg,
    FutureDataMsg,
    GenericAliasDataMsg,
    TypeUnionDataMsg,
)
from agentica_internal.warpc.msg.rpc_event import FutureCanceledMsg as PyFutureCanceledMsg
from agentica_internal.warpc.msg.rpc_event import FutureCompletedMsg as PyFutureCompletedMsg
from agentica_internal.warpc.msg.term_atom import ForwardRefTypeMsg
from agentica_internal.warpc.msg.term_exception import ExceptionMsg
from agentica_internal.warpc.msg.term_resource import SystemResourceMsg, UserResourceMsg
from agentica_internal.warpc_transcode.uni_sys_id import ATOMIC_IDS
from agentica_internal.warpc.data.identifier import Identifier

from .conv_utils import *
from .uni_msgs import *
from .uni_msgs import (
    EventUniMsg,
    ForeignExceptionUniMsg,
    FutureCanceledUniMsg,
    FutureCompletedUniMsg,
    GenericExceptionUniMsg,
    InternalErrorUniMsg,
    toMethodSignature,
)

__all__ = ['uni_to_py']


"""
note: also see warpc/msg/__final__.py for how message classes are finalized...
"""


EXCLUDE_FROM_BASES = {BUILTIN_UNI_IDS["Object"]}


# Uni Any -> Py Any
def uni_to_py(msg: UniMsg, ctx: dict[DefnUID, DefUniMsg]) -> Msg:
    if isinstance(msg, RpcUniMsg):
        return uni_to_py_rpc(msg, ctx)
    elif isinstance(msg, ConceptUniMsg):
        return uni_to_py_term(msg, ctx)
    else:
        raise ValueError(f'Unsupported universal message: {msg}')


# Uni RPC -> Py RPC
def uni_to_py_rpc(msg: RpcUniMsg, ctx: dict[DefnUID, DefUniMsg]) -> RPCMsg:
    if isinstance(msg, RequestUniMsg):
        # HACK: use requestedFID for mid
        fid, mid = uni_to_py_request_ids(msg)
        req = uni_to_py_request(msg, ctx)
        defs = tuple(uni_to_ordered_py_defs(msg.defs, ctx))

        return FramedRequestMsg(mid=mid, fid=fid, request=req, defs=defs)

    elif isinstance(msg, ResponseUniMsg):
        # HACK: mid is not known in uni response (set to fid)
        fid, mid = uni_to_py_response_ids(msg)
        result_msg = uni_to_py_result(msg, ctx)
        if hasattr(msg, 'defs'):
            assert isinstance(msg, ResUniMsg), f"Got unexpected defs in response"
            defs = tuple(uni_to_ordered_py_defs(msg.defs, ctx))
        else:
            defs = ()
        return FramedResponseMsg(mid=mid, fid=fid, result=result_msg, defs=defs)

    elif isinstance(msg, EventUniMsg):
        if isinstance(msg, FutureCanceledUniMsg):
            future_id = msg.future_id
            return PyFutureCanceledMsg(future_id=future_id)

        if isinstance(msg, FutureCompletedUniMsg):
            future_id = msg.future_id
            if hasattr(msg.result, 'defs'):
                assert isinstance(msg.result, ResUniMsg), f"Got unexpected defs in completed result"
                defs = tuple(uni_to_ordered_py_defs(msg.result.defs, ctx))
            else:
                defs = ()
            result_msg = uni_to_py_result(msg.result, ctx)
            return PyFutureCompletedMsg(future_id=future_id, result=result_msg, defs=defs)

        raise ValueError(f'Unknown EventUniMsg: {msg}')
    elif isinstance(msg, ChannelUniMsg):
        value = uni_to_py_term(msg.value, ctx)
        result = ResultMsg(value=value)
        defs = tuple(uni_to_ordered_py_defs(msg.defs, ctx))
        return ChannelMsg(data=result, last=msg.last, defs=defs)

    else:
        raise ValueError(f'Unknown RpcUniMsg: {msg}')


# Uni Request -> Py Request
def uni_to_py_request(msg: RequestUniMsg, ctx: dict[DefnUID, DefUniMsg]) -> ResourceRequestMsg:
    if isinstance(msg, CallNewUniMsg):
        cls = uni_to_py_term(msg.payload.cls, ctx)
        assert isinstance(cls, ResourceMsg), f"Expected ResourceMsg for cls, got {cls}"
        pos, key = make_py_call_args(msg.payload.args, ctx)
        info = ResourceNewMsg(cls=cls, pos=pos, key=key)
        return info

    if isinstance(msg, CallFunctionUniMsg):
        fun = uni_to_py_term(msg.payload.fun, ctx)
        assert isinstance(fun, ResourceMsg), f"Expected ResourceMsg for fun, got {fun}"
        pos, key = make_py_call_args(msg.payload.args, ctx)
        info = ResourceCallFunctionMsg(fun=fun, pos=pos, key=key)
        return info

    if isinstance(msg, CallMethodUniMsg):
        owner = uni_to_py_term(msg.payload.owner, ctx)
        assert isinstance(owner, ResourceMsg), f"Expected ResourceMsg for owner, got {owner}"
        pos, key = make_py_call_args(msg.payload.args, ctx)
        info = ResourceCallMethodMsg(obj=owner, mth=msg.payload.method_name, pos=pos, key=key)
        return info

    if isinstance(msg, HasAttrUniMsg):
        ref = uni_to_py_term(msg.payload.owner, ctx)
        assert isinstance(ref, ResourceMsg), f"Expected ResourceMsg for hasattr ref, got {ref}"
        info = ResourceHasAttrMsg(obj=ref, attr=msg.payload.attr)
        return info

    if isinstance(msg, GetAttrUniMsg):
        ref = uni_to_py_term(msg.payload.owner, ctx)
        assert isinstance(ref, ResourceMsg), f"Expected ResourceMsg for getattr ref, got {ref}"
        info = ResourceGetAttrMsg(obj=ref, attr=msg.payload.attr)
        return info

    if isinstance(msg, SetAttrUniMsg):
        ref = uni_to_py_term(msg.payload.owner, ctx)
        assert isinstance(ref, ResourceMsg), f"Expected ResourceMsg for setattr ref, got {ref}"
        val = uni_to_py_term(msg.payload.val, ctx)
        info = ResourceSetAttrMsg(obj=ref, attr=msg.payload.attr, val=val)
        return info

    if isinstance(msg, DelAttrUniMsg):
        ref = uni_to_py_term(msg.payload.owner, ctx)
        assert isinstance(ref, ResourceMsg), f"Expected ResourceMsg for delattr ref, got {ref}"
        info = ResourceDelAttrMsg(obj=ref, attr=msg.payload.attr)
        return info

    raise ValueError(f'Unsupported universal request: {msg}')


# Uni Response -> Py Response
def uni_to_py_result(msg: ResponseUniMsg, ctx: dict[DefnUID, DefUniMsg]) -> ResultMsg:
    if isinstance(msg, OkUniMsg):
        return ResultMsg()

    if isinstance(msg, ResUniMsg):
        term = uni_to_py_term(msg.payload.result, ctx)
        return ResultMsg(value=term)

    if isinstance(msg, ErrUniMsg):
        excp_msg = exc_to_py_msg(msg.payload.error, ctx)
        return ResultMsg(error=excp_msg)

    raise ValueError(f'Unsupported universal response: {msg}')


# Uni Concept -> Py Term
def uni_to_py_term(term: ConceptUniMsg, ctx: dict[DefnUID, DefUniMsg]) -> TermMsg:
    if isinstance(term, RefUniMsg) and (
        not isinstance(term, TypeStringRefUniMsg)
        or term.uid.resource < 0  # isinstance TypeStringRefUniMsg and uid.resource < 0
    ):
        rid = term.uid.resource

        # If the universal resource id is a negative known system id, map to system rid
        if rid < 0:
            from .conv_utils import uniSysIdToSrid

            sys_id = uniSysIdToSrid(rid)
            if sys_id is not None:
                return SystemResourceMsg(sid=sys_id)

        if term.system:
            return SystemResourceMsg(sid=rid)

        rid = resourceUIDToGrid(term.uid)
        return UserResourceMsg(rid=rid)

    if isinstance(term, DefUniMsg):
        # For terms, reference the resource by RID; definitions go separately in defs
        return UserResourceMsg(rid=resourceUIDToGrid(term.uid))

    # Atomics
    if isinstance(term, NoneUniMsg):
        return NoneMsg.MSG
    if isinstance(term, BoolUniMsg):
        return NumberMsg(v=term.val)
    if isinstance(term, IntUniMsg):
        return NumberMsg(v=term.val)
    if isinstance(term, FloatUniMsg):
        return NumberMsg(v=term.val)
    if isinstance(term, StrUniMsg):
        return StrMsg(v=term.val)
    if isinstance(term, TypeStringRefUniMsg):
        return ForwardRefTypeMsg(v=term.name)
    if isinstance(term, BytesUniMsg):
        return BytesMsg(v=term.val)

    # Symbols
    if isinstance(term, EnumValUniMsg):
        return EnumValMsg(val=uni_to_py_term(term.val, ctx), cls=uni_to_py_term(term.cls, ctx))  # type: ignore[call-arg]

    # Containers
    if isinstance(term, ArrayUniMsg):
        vs = tuple(uni_to_py_term(v, ctx) for v in term.val)
        return ListMsg(vs=vs)
    if isinstance(term, SetUniMsg):
        vs = tuple(uni_to_py_term(v, ctx) for v in term.val)
        return SetMsg(vs=vs)
    if isinstance(term, MapUniMsg):
        ks = tuple(uni_to_py_term(k, ctx) for k in term.val.keys)
        vs = tuple(uni_to_py_term(v, ctx) for v in term.val.vals)
        return DictMsg(ks=ks, vs=vs)
    if isinstance(term, TupleUniMsg):
        vs = tuple(uni_to_py_term(v, ctx) for v in term.val)
        return TupleMsg(vs=vs)

    # Exceptions
    if isinstance(term, (ForeignExceptionUniMsg, InternalErrorUniMsg, GenericExceptionUniMsg)):
        return exc_to_py_msg(term, ctx)

    raise ValueError(f'Unknown universal term: {term}')


def exc_to_py_msg(term, ctx) -> ExceptionMsg:
    if isinstance(term, ForeignExceptionUniMsg):
        cls_uid = term.excp_cls.uid
        if cls_uid.world == 'client' and cls_uid.resource < 0:
            if cls_srid := uniSysIdToSrid(cls_uid.resource):
                return SystemExceptionMsg(
                    exc_cls=SystemResourceMsg(sid=cls_srid),
                    exc_args=tuple(uni_to_py_term(v, ctx) for v in term.excp_args),
                )
        if cls_def := get_def_or_sysref_from_ctx(ctx, term.excp_cls):
            if isinstance(cls_def, ClassDefUniMsg):
                cls_name = cls_def.payload.name
                return ShallowUserExceptionMsg(
                    ident=Identifier(cls_name),
                    exc_str=' '.join(a.val for a in term.excp_args if isinstance(a, StrUniMsg)),
                )

    if isinstance(term, InternalErrorUniMsg):
        return InternalExceptionMsg(error=term.error)

    if isinstance(term, GenericExceptionUniMsg):
        return ShallowUserExceptionMsg(
            ident=Identifier(term.excp_cls_name),
            exc_str=' '.join(term.excp_str_args),
        )

    return InternalExceptionMsg(error="Unknown error")


# Uni Def Msg -> Py Definition Msg
def uni_to_py_def(
    defmsg: DefUniMsg,
    ctx: dict[DefnUID, DefUniMsg],
    name: str | None = None,
    synthetic_defs: list[DefUniMsg] | None = None,
) -> DefinitionMsg:
    rid = resourceUIDToGrid(defmsg.uid)

    if isinstance(defmsg, ClassDefUniMsg):
        if defmsg.payload.system_resource:
            sys_data = TypeUnionDataMsg(alts=(SystemResourceMsg(sid=defmsg.uid.resource),))  # type: ignore[arg-type]
            return DefinitionMsg(rid=rid, data=sys_data)

        # Case of "function types" like ((x: int) -> string)
        if isinstance(callmsg := defmsg.payload.supplied_type_args, FunctionDefUniMsg):
            # Comment:
            # * The current approach construct a callable class to encode the function type
            # * but we could also easily turn this into a `Callable[[A,B],C]` GenericAlias instead of a class

            # Synthesize __call__
            start_uid = make_space_for_uid(defmsg.uid.resource)
            call_uid = DefnUID(world='client', resource=start_uid - 1)

            # Create a new function def with the unique UID
            # Copy the payload fields from the original function
            call_payload = FunctionPayload(
                name="__call__",
                arguments=callmsg.payload.arguments,
                doc=callmsg.payload.doc if callmsg.payload.doc is not UNSET else UNSET,
                returnType=callmsg.payload.returnType
                if callmsg.payload.returnType is not UNSET
                else UNSET,
                module=callmsg.payload.module if callmsg.payload.module is not UNSET else UNSET,
            )
            call_func = FunctionDefUniMsg(uid=call_uid, payload=call_payload)

            # Register in context and create reference
            ctx[call_uid] = call_func
            call_ref = UserResourceMsg(rid=resourceUIDToGrid(call_uid))

            if synthetic_defs is not None:
                synthetic_defs.append(call_func)

            data = class_payload_to_py_data(
                defmsg.payload, defmsg.uid, ctx, call_ref, synthetic_defs
            )
            return DefinitionMsg(rid=rid, data=data)

        if (sys_msg := uni_def_to_py_sys(defmsg, ctx)) is not None:
            return sys_msg

        data = class_payload_to_py_data(defmsg.payload, defmsg.uid, ctx, None, synthetic_defs)
        return DefinitionMsg(rid=rid, data=data)

    if isinstance(defmsg, FunctionDefUniMsg):
        data = function_payload_to_py_data(defmsg.payload, ctx)
        return DefinitionMsg(rid=rid, data=data)

    if isinstance(defmsg, ObjectDefUniMsg):
        if defmsg.payload.cls is UNSET:
            raise ValueError("Cannot transcode object without cls")

        ## the special future shortcut
        if (
            (cls_def := get_def_or_sysref_from_ctx(ctx, defmsg.payload.cls)) is not None
            and isinstance(cls_def, ClassDefUniMsg)
            and cls_def.payload.instance_of_generic is not UNSET
            and cls_def.payload.instance_of_generic.resource == BUILTIN_UNI_IDS["Future"]
        ):
            return DefinitionMsg(
                rid=rid, data=FutureDataMsg(future=defmsg.uid.resource, result=None)
            )  # type: ignore[call-arg]

        ## non-future objects
        data = object_payload_to_py_data(
            defmsg.payload if defmsg.payload is not UNSET else ObjectPayload(),
            ctx,
        )
        return DefinitionMsg(rid=rid, data=data)

    if isinstance(defmsg, MethodSignatureUniMsg):
        # Represent as a function definition in native with class context
        memberof = get_def_or_sysref_from_ctx(ctx, defmsg.methodOf)
        assert isinstance(memberof, (ClassDefUniMsg, InterfaceUniMsg, IntersectionUniMsg))
        data = function_payload_to_py_data(defmsg.payload, ctx, class_def=memberof)
        return DefinitionMsg(rid=rid, data=data)

    # Annotation defs
    if isinstance(defmsg, UnionUniMsg):
        # Map union classes to term alts
        alts = tuple(uni_to_py_term(ref, ctx) for ref in defmsg.payload.classes)
        data = TypeUnionDataMsg(alts=alts)  # type: ignore[arg-type]
        return DefinitionMsg(rid=rid, data=data)

    if isinstance(defmsg, IntersectionUniMsg):
        data = intersection_to_class_data(
            defmsg, rid, ctx, name=name, synthetic_defs=synthetic_defs
        )
        return DefinitionMsg(rid=rid, data=data)

    if isinstance(defmsg, InterfaceUniMsg):
        data = class_payload_to_protocol_data(defmsg.payload, defmsg.uid, ctx, synthetic_defs)
        return DefinitionMsg(rid=rid, data=data)

    if isinstance(defmsg, PlaceholderUniMsg):
        raise NotImplementedError('Placeholder defs are not supported')

    raise ValueError(f'Unsupported universal def: {defmsg}')


# uni def -> py sys (or union thereof)
def uni_def_to_py_sys(defmsg: DefUniMsg, ctx: dict[DefnUID, DefUniMsg]) -> DefinitionMsg | None:
    def make_sys_msg(py_ids: list[int]) -> DefinitionMsg:
        alts = tuple(SystemResourceMsg(sid=py_id) for py_id in py_ids)
        union = TypeUnionDataMsg(alts=alts)  # type: ignore[arg-type]
        return DefinitionMsg(rid=resourceUIDToGrid(defmsg.uid), data=union)

    if defmsg.uid.resource == ATOMIC_IDS["object"]:
        py_ids = [LRID_TO_SRID.get(id(object), 0)]
        return make_sys_msg(py_ids)
    if defmsg.uid.resource == ATOMIC_IDS["string"]:
        py_ids = [LRID_TO_SRID.get(id(str), 0)]
        return make_sys_msg(py_ids)
    if defmsg.uid.resource == ATOMIC_IDS["number"]:
        py_ids = [LRID_TO_SRID.get(id(int), 0), LRID_TO_SRID.get(id(float), 0)]
        return make_sys_msg(py_ids)
    if defmsg.uid.resource == ATOMIC_IDS["boolean"]:
        py_ids = [LRID_TO_SRID.get(id(bool), 0)]
        return make_sys_msg(py_ids)
    if defmsg.uid.resource == ATOMIC_IDS["undefined"]:
        py_ids = [LRID_TO_SRID.get(id(type(None)), 0)]
        return make_sys_msg(py_ids)
    return None


# Uni Intersection -> Py Class Data
def intersection_to_class_data(
    defmsg: IntersectionUniMsg,
    rid: GlobalRID,
    ctx: dict[DefnUID, DefUniMsg],
    name: str | None = None,
    synthetic_defs: list[DefUniMsg] | None = None,
) -> ClassDataMsg:
    type_sid = LRID_TO_SRID.get(id(type), 0)
    cls_msg = SystemResourceMsg(sid=type_sid)

    base_names: list[str] = []
    base_uni_refs: list[RefUniMsg] = []
    module: str | None = None
    for ref in defmsg.payload.classes:
        base_def = get_def_or_sysref_from_ctx(ctx, ref)
        if base_def and isinstance(base_def, (ClassDefUniMsg, InterfaceUniMsg)):
            # Exclude builtin types from bases
            if (
                base_def.payload.instance_of_generic is not UNSET
                and base_def.payload.instance_of_generic.resource in EXCLUDE_FROM_BASES
            ):
                continue

            base_names.append(base_def.payload.name)  # type: ignore[attr-defined]
            base_uni_refs.append(ref)  # Add the ref to the list of bases
            # Use the module from the first base that has one

            if (
                module is None
                and hasattr(base_def.payload, 'module')
                and type(base_def.payload.module) is str
            ):  # type: ignore[attr-defined]
                module = base_def.payload.module  # type: ignore[attr-defined]

    if name is None:
        name = '_Also_'.join(base_names) if base_names else f'Intersection_{rid[2]}'

    bases = tuple(uni_to_py_term(ref, ctx) for ref in base_uni_refs)

    # Synthesize uninstantiable __init__ with Never parameter
    init_ref = add_uninstantiable_init_method(name, defmsg.uid, ctx, synthetic_defs)
    methods: dict[str, tuple[str, ResourceMsg]] = (
        {'__init__': ('instance', init_ref)} if init_ref else {}
    )

    return ClassDataMsg(
        name=name,
        cls=cls_msg,
        bases=bases,  # type: ignore
        methods=methods,  # type: ignore
        qname=name,
        module="__main__",  # TODO: maybe one day module if module is not None else '__main__',
        doc=f'Protocol combining: {", ".join(base_names)}' if base_names else '',
        annos={},
        attrs={},
        sattrs=(),
        keys=(),
    )  # type: ignore[call-arg]


# Uni Class Payload -> Py Class Data
def class_payload_to_py_data(
    data: ClassPayload,
    class_uid: DefnUID,
    ctx: dict[DefnUID, DefUniMsg],
    call_rsrc: ResourceMsg | None = None,
    synthetic_defs: list[DefUniMsg] | None = None,
) -> ResourceDataMsg:
    # Short cut for enums
    if (
        data.instance_of_generic is not UNSET
        and data.instance_of_generic.resource == BUILTIN_UNI_IDS["Enum"]
    ):
        members = {}
        assert isinstance(data.supplied_type_args, list)

        # Determine enum_kind by inspecting all arg types; prefer int->str->any if mixed
        arg_types = {type(arg.type) for arg in data.supplied_type_args}
        if all(t is IntUniMsg for t in arg_types):
            enum_kind = 'int'
        elif all(t is StrUniMsg for t in arg_types):
            enum_kind = 'str'
        else:
            enum_kind = 'any'

        for argMsg in data.supplied_type_args:
            members[argMsg.name] = uni_to_py_term(argMsg.type, ctx)
        return EnumClassDataMsg(name=data.name, members=members, kind=enum_kind)  # type: ignore[call-arg]

    # Short cuts for other generic aliases
    if data.instance_of_generic is not UNSET and call_rsrc is None:
        from .conv_utils import uniSysIdToSrid

        classvar_uid = data.instance_of_generic
        sys_id = uniSysIdToSrid(classvar_uid.resource)
        origin: TermMsg
        if sys_id is not None:
            origin = SystemResourceMsg(sid=sys_id)
        else:
            origin = UserResourceMsg(rid=resourceUIDToGrid(classvar_uid))

        args: list[TermMsg] = []
        if isinstance(data.supplied_type_args, list):
            for arg in data.supplied_type_args:
                args.append(uni_to_py_term(arg.type, ctx))

        return GenericAliasDataMsg(origin=origin, args=tuple(args))  # type: ignore[call-arg]

    # General classes
    type_sid = LRID_TO_SRID.get(id(type), 0)
    cls_msg = SystemResourceMsg(sid=type_sid)

    bases = (
        tuple(uni_to_py_term(b, ctx) for b in (data.bases or [])) if data.bases is not UNSET else ()
    )

    # Synthesize __init__ from constructor arguments
    new_synthetic_init = add_init_method(data, class_uid, ctx)
    if synthetic_defs is not None:
        synthetic_defs.extend(new_synthetic_init)

    # Synthesize dict protocol methods if needed
    new_synthetic = add_dict_protocol_methods(data, class_uid, ctx)
    if synthetic_defs is not None:
        synthetic_defs.extend(new_synthetic)

    # methods: mapping name -> resource (function def/ref)
    methods: dict[str, tuple[str, ResourceMsg]] = {}
    if isinstance(uni_methods := data.methods, list):
        for m in uni_methods:
            name = m.name
            # skip private methods
            if m.is_private is not UNSET and m.is_private:
                continue
            fun_ref = uni_to_py_term(m.function, ctx)
            assert isinstance(fun_ref, ResourceMsg)
            methods[name] = ('instance', fun_ref)

    annos, _instance_keys, class_keys = make_annos_and_keys(data, class_uid, ctx, synthetic_defs)

    # Only instance fields are instance keys for now
    keys = tuple(class_keys)

    # For callable classes add __call__ (by reference)
    if call_rsrc is not None:
        methods['__call__'] = ('instance', call_rsrc)
        keys = keys + ('__call__',)

    return ClassDataMsg(  # type: ignore[call-arg]
        name=data.name,
        cls=cls_msg,
        bases=tuple(bases),  # type: ignore
        methods=methods,  # type: ignore
        qname=data.name,
        module="__main__",  # TODO: maybe one day "__main__" if data.module is UNSET else data.module,
        doc="" if data.doc is UNSET else data.doc,
        annos=annos,
        keys=keys,
    )


def make_annos_and_keys(
    data: ClassPayload,
    class_uid: DefnUID,
    ctx: dict[DefnUID, DefUniMsg],
    synthetic_defs: list[DefUniMsg] | None = None,
) -> tuple[dict[str, TermMsg], list[str], list[str]]:
    # annotations to fields
    annos: dict[str, TermMsg] = {}
    instance_keys: list[str] = []
    class_keys: list[str] = []
    if data.fields is not UNSET:
        idx = 0
        for f in data.fields:
            # skip private fields
            if f.is_private is not UNSET and f.is_private:
                continue

            # Instance vs static fields
            is_static = f.is_static is not UNSET and f.is_static
            base_term = uni_to_py_term(f.type, ctx)

            # Instance fields
            if not is_static:
                annos[f.name] = base_term
                instance_keys.append(f.name)
                continue

            # Class fields
            class_keys.append(f.name)
            classvar_wrapper = try_make_classvar(f.type, class_uid, ctx, synthetic_defs, offset=idx)
            if classvar_wrapper is not None:
                annos[f.name] = classvar_wrapper
                idx += 1
            else:
                annos[f.name] = base_term
    return annos, instance_keys, class_keys


def make_space_for_uid(uid_in: int) -> int:
    return -10000 - uid_in * 100


def try_make_classvar(
    field_type: RefUniMsg,
    class_uid: DefnUID,
    ctx: dict[DefnUID, DefUniMsg],
    synthetic_defs: list[DefUniMsg] | None = None,
    offset: int = 0,
) -> UserResourceMsg:
    # Wrap static field types in typing.ClassVar[T]
    classvar_uni_id = BUILTIN_UNI_IDS["ClassVar"]
    classvar_defn_id = DefnUID(world='client', resource=classvar_uni_id)

    # Allocate a unique UID for this alias
    start_uid = make_space_for_uid(class_uid.resource)
    alias_uid = DefnUID(world='client', resource=start_uid - 9 - offset)
    alias_payload = ClassPayload(
        name='GenericAlias',
        fields=[],
        methods=[],
        instance_of_generic=classvar_defn_id,
        supplied_type_args=[TypeArgument(name='a0', type=field_type)],
    )
    alias_uni_def = ClassDefUniMsg(uid=alias_uid, payload=alias_payload)

    # Register synthetic def for output and referencing
    ctx[alias_uid] = alias_uni_def
    if synthetic_defs is not None:
        synthetic_defs.append(alias_uni_def)

    return UserResourceMsg(rid=resourceUIDToGrid(alias_uid))


def add_init_method(
    data: ClassPayload, class_uid: DefnUID, ctx: dict[DefnUID, DefUniMsg]
) -> list[MethodSignatureUniMsg]:
    if data.ctor_args is UNSET or not data.ctor_args:
        return []

    start_uid = make_space_for_uid(class_uid.resource)
    init_uid = DefnUID(world='client', resource=start_uid - 0)

    if init_uid in ctx:
        return []

    none_uid = DefnUID(world='client', resource=BUILTIN_UNI_IDS["None"])
    none_ref = RefUniMsg(uid=none_uid, system=True)

    init_payload = FunctionPayload(
        name='__init__',
        arguments=data.ctor_args,
        returnType=none_ref,
        doc=f"Initialize an instance of {data.name}.",
    )

    init_func = FunctionDefUniMsg(uid=init_uid, payload=init_payload)
    membership = Membership(uid=class_uid, kind='instance')
    init_method = toMethodSignature(init_func, membership)

    ctx[init_uid] = init_method

    if data.methods is UNSET:
        data.methods = []
    data.methods.append(ClassMethod(name='__init__', function=RefUniMsg(uid=init_uid)))

    return [init_method]


def add_uninstantiable_init_method(
    class_name: str,
    class_uid: DefnUID,
    ctx: dict[DefnUID, DefUniMsg],
    synthetic_defs: list[DefUniMsg] | None = None,
) -> ResourceMsg | None:
    start_uid = make_space_for_uid(class_uid.resource)
    init_uid = DefnUID(world='client', resource=start_uid - 0)

    if init_uid in ctx:
        return None

    none_uid = DefnUID(world='client', resource=BUILTIN_UNI_IDS["None"])
    none_ref = RefUniMsg(uid=none_uid, system=True)

    never_uid = DefnUID(world='client', resource=BUILTIN_UNI_IDS["Never"])
    never_ref = RefUniMsg(uid=never_uid, system=True)

    init_payload = FunctionPayload(
        name='__init__',
        arguments=[FunctionArgument(name='_', type=never_ref)],
        returnType=none_ref,
        doc=f"Cannot instantiate {class_name}.",
    )

    init_func = FunctionDefUniMsg(uid=init_uid, payload=init_payload)
    membership = Membership(uid=class_uid, kind='instance')
    init_method = toMethodSignature(init_func, membership)

    ctx[init_uid] = init_method
    if synthetic_defs is not None:
        synthetic_defs.append(init_method)

    # Return the __init__ method reference
    init_ref = uni_to_py_term(RefUniMsg(uid=init_uid), ctx)
    assert isinstance(init_ref, ResourceMsg)
    return init_ref


def add_dict_protocol_methods(
    data: ClassPayload, class_uid: DefnUID, ctx: dict[DefnUID, DefUniMsg]
) -> list[MethodSignatureUniMsg]:
    if data.index_signature is UNSET:
        return []

    key_type = data.index_signature.key_type
    value_type = data.index_signature.value_type
    map_type_uid = data.index_signature.map_type.uid.resource

    start_uid = make_space_for_uid(map_type_uid)
    getitem_uid = DefnUID(world='client', resource=start_uid - 1)
    setitem_uid = DefnUID(world='client', resource=start_uid - 2)
    delitem_uid = DefnUID(world='client', resource=start_uid - 3)
    contains_uid = DefnUID(world='client', resource=start_uid - 4)

    # for __contains__
    bool_uid = DefnUID(world='client', resource=BUILTIN_UNI_IDS["Boolean"])
    bool_ref = RefUniMsg(uid=bool_uid, system=True)
    # for __setitem__ and __delitem__
    none_uid = DefnUID(world='client', resource=BUILTIN_UNI_IDS["None"])
    none_ref = RefUniMsg(uid=none_uid, system=True)

    newly_created: list[MethodSignatureUniMsg] = list()
    membership = Membership(uid=class_uid, kind='instance')

    if getitem_uid not in ctx:
        getitem_payload = FunctionPayload(
            name='__getitem__',
            arguments=[
                FunctionArgument(name='key', type=key_type),
            ],
            returnType=value_type,
            doc="Objects of this class are dict-like, and support indexing with `obj[key]`.",
        )
        getitem_func = FunctionDefUniMsg(uid=getitem_uid, payload=getitem_payload)
        getitem_method = toMethodSignature(getitem_func, membership)
        ctx[getitem_uid] = getitem_method
        newly_created.append(getitem_method)

    if setitem_uid not in ctx:
        setitem_payload = FunctionPayload(
            name='__setitem__',
            arguments=[
                FunctionArgument(name='key', type=key_type),
                FunctionArgument(name='value', type=value_type),
            ],
            returnType=none_ref,
            doc="Objects of this class are dict-like, and support assignment with `obj[key] = value`.",
        )
        setitem_func = FunctionDefUniMsg(uid=setitem_uid, payload=setitem_payload)
        setitem_method = toMethodSignature(setitem_func, membership)
        ctx[setitem_uid] = setitem_method
        newly_created.append(setitem_method)

    if delitem_uid not in ctx:
        delitem_payload = FunctionPayload(
            name='__delitem__',
            arguments=[
                FunctionArgument(name='key', type=key_type),
            ],
            returnType=none_ref,
            doc="Objects of this class are dict-like, and support deletion with `del obj[key]`.",
        )
        delitem_func = FunctionDefUniMsg(uid=delitem_uid, payload=delitem_payload)
        delitem_method = toMethodSignature(delitem_func, membership)
        ctx[delitem_uid] = delitem_method
        newly_created.append(delitem_method)

    if contains_uid not in ctx:
        contains_payload = FunctionPayload(
            name='__contains__',
            arguments=[
                FunctionArgument(name='key', type=key_type),
            ],
            returnType=bool_ref,
            doc="Objects of this class are dict-like, and support checking for membership with `key in obj`.",
        )
        contains_func = FunctionDefUniMsg(uid=contains_uid, payload=contains_payload)
        contains_method = toMethodSignature(contains_func, membership)
        ctx[contains_uid] = contains_method
        newly_created.append(contains_method)

    if data.methods is UNSET:
        data.methods = list()

    data.methods.extend(
        [
            ClassMethod(name='__getitem__', function=RefUniMsg(uid=getitem_uid)),
            ClassMethod(name='__setitem__', function=RefUniMsg(uid=setitem_uid)),
            ClassMethod(name='__delitem__', function=RefUniMsg(uid=delitem_uid)),
            ClassMethod(name='__contains__', function=RefUniMsg(uid=contains_uid)),
        ]
    )

    return newly_created


def uni_inherits_from_interface(base_ref: RefUniMsg, ctx: dict[DefnUID, DefUniMsg]) -> bool:
    visited: set[DefnUID] = set()

    def check_uni_base(ref: RefUniMsg) -> bool:
        if ref.uid in visited:
            return False
        visited.add(ref.uid)

        base_def = get_def_or_sysref_from_ctx(ctx, ref)
        if base_def is None:
            return False

        if isinstance(base_def, InterfaceUniMsg):
            return True

        if isinstance(base_def, ClassDefUniMsg):
            if base_def.payload.bases is not UNSET:
                for parent_ref in base_def.payload.bases:
                    if check_uni_base(parent_ref):
                        return True

        return False

    return check_uni_base(base_ref)


# Uni Class Payload -> Py Protocol Data (for interfaces)
def class_payload_to_protocol_data(
    data: ClassPayload,
    class_uid: DefnUID,
    ctx: dict[DefnUID, DefUniMsg],
    synthetic_defs: list[DefUniMsg] | None = None,
) -> ClassDataMsg:
    # Get the metaclass (type) as a system resource
    type_sid = LRID_TO_SRID.get(id(type), 0)
    cls_msg = SystemResourceMsg(sid=type_sid)

    uni_bases = data.bases if data.bases is not UNSET else ()

    cleaned_uni_bases = list()
    for base in uni_bases:
        base_def = get_def_or_sysref_from_ctx(ctx, base)
        if (
            isinstance(base_def, ClassDefUniMsg)
            and base_def.payload.instance_of_generic is not UNSET
            and base_def.payload.instance_of_generic.resource in EXCLUDE_FROM_BASES
        ):
            continue
        cleaned_uni_bases.append(base)

    # Check if any base is/extends an interface (will become a Protocol)
    # If so, we shouldn't add Protocol again (would cause MRO conflict)
    has_interface_base = any(uni_inherits_from_interface(b, ctx) for b in cleaned_uni_bases)

    # Convert interface bases to Python terms
    interface_bases = tuple(uni_to_py_term(b, ctx) for b in cleaned_uni_bases)

    # Add Protocol as the first base class, only when no base is/extends an interface
    if not has_interface_base:
        protocol_sid = LRID_TO_SRID.get(id(TypingProtocol), 0)
        protocol_msg = SystemResourceMsg(sid=protocol_sid)
        interface_bases = (protocol_msg,) + interface_bases

    # Synthesize __init__ from constructor arguments
    new_synthetic_init = add_init_method(data, class_uid, ctx)
    if synthetic_defs is not None:
        synthetic_defs.extend(new_synthetic_init)

    # Add synthetic dict protocol methods if the interface has an index signature
    new_synthetic = add_dict_protocol_methods(data, class_uid, ctx)
    if synthetic_defs is not None:
        synthetic_defs.extend(new_synthetic)

    # methods: mapping name -> resource (function def/ref)
    methods: dict[str, tuple[str, ResourceMsg]] = {}
    if isinstance(uni_methods := data.methods, list):
        for m in uni_methods:
            name = m.name
            # skip private methods
            if m.is_private is not UNSET and m.is_private:
                continue
            fun_ref = uni_to_py_term(m.function, ctx)
            assert isinstance(fun_ref, ResourceMsg)
            methods[name] = ('instance', fun_ref)

    # annotations to fields
    annos, _instance_keys, class_keys = make_annos_and_keys(data, class_uid, ctx, synthetic_defs)

    return ClassDataMsg(  # type: ignore[call-arg]
        name=data.name,
        cls=cls_msg,
        bases=interface_bases,  # type: ignore[arg-type]
        methods=methods,  # type: ignore
        qname=data.name,
        module="__main__",  # TODO: maybe one day "__main__" if data.module is UNSET else data.module,
        doc="" if data.doc is UNSET else data.doc,
        annos=annos,
        keys=tuple(class_keys),
    )


# Uni Fun Payload -> Py Fun Data
def function_payload_to_py_data(
    data: FunctionPayload,
    ctx: dict[DefnUID, DefUniMsg],
    class_def: ClassDefUniMsg | InterfaceUniMsg | IntersectionUniMsg | None = None,
) -> FunctionDataMsg:
    # Build argument metadata:
    #    args_to_rest_opt: name -> (is_rest, is_optional)
    args_to_rest_opt: dict[str, tuple[bool, bool]] = dict()
    if data.arguments is not UNSET:
        args_to_rest_opt = {
            arg.name: (
                arg.rest is not UNSET and arg.rest,
                (arg.optional is not UNSET and arg.optional) or arg.default is not UNSET,
            )
            for arg in data.arguments
        }

    if args_to_rest_opt:
        rest_args = tuple(k for k, (is_rest, _) in args_to_rest_opt.items() if is_rest)
        pos_star: str | None = rest_args[0] if rest_args else None
        arg_names: tuple[str, ...] = tuple(
            k for k, (is_rest, _) in args_to_rest_opt.items() if not is_rest
        )
        opt_args: tuple[str, ...] = tuple(
            k for k, (is_rest, is_opt) in args_to_rest_opt.items() if is_opt and not is_rest
        )
    else:
        pos_star = None
        arg_names = ()
        opt_args = ()

    # annotations
    annos: dict[str, TermMsg] = {}
    if data.arguments is not UNSET:
        for arg in data.arguments:
            try:
                annos[arg.name] = uni_to_py_term(arg.type, ctx)
            except:
                # TODO: should log / notify about this
                # best-effort: skip unsupported annotations
                pass

    # Default arguments
    defaults: dict[str, TermMsg] = {}
    if data.arguments is not UNSET:
        for arg in data.arguments:
            if arg.default is not UNSET:
                try:
                    defaults[arg.name] = uni_to_py_term(arg.default, ctx)
                except:
                    # TODO: should log / notify about this
                    pass

    # Return type
    if data.returnType is not UNSET:
        annos['return'] = uni_to_py_term(data.returnType, ctx)

    # If this is a method attached to a class, compute qname and prepend self
    qname = data.name
    if class_def is not None:
        # IntersectionPayload doesn't have a name field, so we just use the method name
        if isinstance(class_def, IntersectionUniMsg):
            qname = data.name
        else:
            qname = f"{class_def.payload.name}.{data.name}"
        # Prepend 'self' to args if not already there
        if not arg_names or arg_names[0] != 'self':
            arg_names = ('self',) + tuple(arg_names)
        # Annotate self with the class type
        self_rid = resourceUIDToGrid(class_def.uid)
        # HACK: don't annotate self for now ... it errors due to recursion
        # annos['self'] = uni_to_py_term(
        #     class_def, ctx
        # )  # TODO: could turn this into a string annotation

    ident = Identifier(
        name=data.name,
        qual=qname,
        mod="__main__",  # TODO: maybe one day "__main__" if data.module is UNSET else data.module,
    )

    sig = SignatureMsg(
        pos_args=arg_names,
        optional=opt_args,
        pos_star=pos_star,
        annos=annos,
        defaults=defaults,
        doc=None if data.doc is UNSET else data.doc,
    )

    return FunctionDataMsg(
        ident=ident,
        sig=sig,
        # type: ignore[call-arg]
    )


# Uni Object Payload -> Py Object Data
def object_payload_to_py_data(
    payload: ObjectPayload, ctx: dict[DefnUID, DefUniMsg]
) -> ObjectDataMsg | FutureDataMsg | ForwardRefDataMsg:
    if payload.cls is UNSET:
        cls_def = RefUniMsg(uid=DefnUID(world='client', resource=BUILTIN_UNI_IDS["Any"]))
    else:
        cls_def = get_def_or_sysref_from_ctx(ctx, payload.cls)
        if cls_def is None:
            raise ValueError(f"TranscoderError: class not found in context {payload.cls}")

    if isinstance(cls_def, DefinitionMsg) and isinstance(cls_def.data, ForwardRefDataMsg):
        return ForwardRefDataMsg(name=cls_def.data.name)

    ## CASE 1: union-typed objects have their own code path
    if isinstance(cls_def, UnionUniMsg):
        # For union-typed objects, match runtime keys to a specific disjunct. If we can't find
        # a matching disjunct, then ... uh, well it's better than not having the working paths.
        runtime_keys = set(payload.keys) if payload.keys is not UNSET else set()

        matched_disjunct = None
        for disjunct_ref in cls_def.payload.classes:
            disjunct_def = get_def_or_sysref_from_ctx(ctx, disjunct_ref)
            if disjunct_def is None:
                # Ignore disjuncts that are not in the context... (e.g. primitive values)
                continue

            def get_expected_keys(cls_payload: ClassPayload, expected_keys: set[str]):
                if cls_payload.methods is not UNSET:
                    expected_keys.update(
                        {
                            m.name for m in cls_payload.methods if m.function.uid.resource > 0
                        }  # we want to exclude synthetic methods ... > 0 !
                    )
                if cls_payload.fields is not UNSET:
                    expected_keys.update(
                        {
                            f.name for f in cls_payload.fields if f.is_optional is not True
                        }  # we want to exclude optional fields
                    )

            expected_keys = set()
            if isinstance(disjunct_def, InterfaceUniMsg):
                get_expected_keys(disjunct_def.payload, expected_keys)
            elif isinstance(disjunct_def, ClassDefUniMsg):
                get_expected_keys(disjunct_def.payload, expected_keys)
            if expected_keys.issubset(runtime_keys):
                matched_disjunct = disjunct_ref

        if matched_disjunct is not None:
            cls_ref_py = uni_to_py_term(matched_disjunct, ctx)
            matched_def = ctx[matched_disjunct.uid]

            if isinstance(matched_def, InterfaceUniMsg):
                if matched_def.payload.methods is not UNSET:
                    keys = tuple(
                        m.name
                        for m in matched_def.payload.methods
                        if m.is_private is not UNSET and not m.is_private
                    )
                else:
                    keys = ()
            elif isinstance(matched_def, ClassDefUniMsg):
                if matched_def.payload.fields is not UNSET:
                    keys = tuple(
                        f.name
                        for f in matched_def.payload.fields
                        if f.is_private is not UNSET and not f.is_private
                    )
                else:
                    keys = ()
            else:
                keys = tuple(payload.keys) if payload.keys is not UNSET else ()
        else:
            raise ValueError(
                "Error during union-typed object disambiguation: did not find a matching disjunct"
            )

        return ObjectDataMsg(cls=cls_ref_py, keys=uniq(keys))  # type: ignore[call-arg]

    ## CASE 2: Objects of system classes
    elif isinstance(cls_def, RefUniMsg) and cls_def.uid.resource < 0:
        cls_ref_py = uni_to_py_term(cls_def, ctx)
        keys = tuple(uniq(payload.keys)) if payload.keys is not UNSET else ()
        return ObjectDataMsg(cls=cls_ref_py, keys=keys)  # type: ignore[call-arg]

    ## Non-system and non-union objects
    else:
        ## Expected class types:
        # Objects can have ClassDefUniMsg (concrete class), InterfaceUniMsg (Protocol),
        # or IntersectionUniMsg (Protocol with multiple inheritance) as their class
        assert isinstance(cls_def, (ClassDefUniMsg, InterfaceUniMsg, IntersectionUniMsg)), (
            f"Expected ClassDefUniMsg, InterfaceUniMsg, or IntersectionUniMsg for obj.cls, got {cls_def}"
        )

        ## key extraction logic
        # Extract keys based on the class type
        if isinstance(cls_def, IntersectionUniMsg):
            # For intersections, collect keys from all component types
            keys_list = []
            for component_ref in cls_def.payload.classes:
                component_def = get_def_or_sysref_from_ctx(ctx, component_ref)
                if (
                    component_def
                    and isinstance(component_def, (ClassDefUniMsg, InterfaceUniMsg))
                    and component_def.payload.fields is not UNSET
                ):
                    keys_list.extend(
                        f.name
                        for f in component_def.payload.fields
                        if f.is_private is not UNSET and not f.is_private
                    )  # type: ignore[attr-defined]
            keys = tuple(keys_list)
        elif hasattr(cls_def.payload, 'fields') and not isinstance(
            cls_def.payload.fields, UnsetType
        ):
            # For ClassDefUniMsg and InterfaceUniMsg with fields
            keys = tuple(
                f.name
                for f in cls_def.payload.fields
                if f.is_private is not UNSET and not f.is_private
            )
        else:
            keys = ()

        cls_ref_py = uni_to_py_term(referentialize(cls_def), ctx)

        # Add object-specific keys
        if payload.keys is not UNSET:
            keys = keys + tuple(payload.keys)

        return ObjectDataMsg(cls=cls_ref_py, keys=uniq(keys))  # type: ignore[call-arg]


def uniq(xs):
    seen = set()
    cls = xs.__class__
    return cls(x for x in xs if x not in seen and not seen.add(x))


### Helper functions

# def uni_to_ordered_py_defs(
#     defs: list[DefUniMsg], ctx: dict[DefnUID, DefUniMsg]
# ) -> list[DefinitionMsg]:
#     ordered_defs, _ = order_defs(defs)
#     py_defs: list[DefinitionMsg] = []
#     for d in ordered_defs:
#         try:
#             # NOTE: this is the runtime code path, we ensure that the synths appear before the parent
#             # but this is effectively not exercised by TS runtime so is untested
#             synthetic_defs: list[DefUniMsg] = []
#             res = uni_to_py_def(d, ctx, None, synthetic_defs)
#             for d in synthetic_defs:
#                 res = uni_to_py_def(d, ctx)
#                 py_defs.append(res)
#             py_defs.append(res)
#         except NotImplementedError:
#             raise ValueError(f"Unsupported universal def: {d}")
#     return py_defs


def uni_to_ordered_py_defs(
    uni_defs: list[DefUniMsg], ctx: dict[DefnUID, DefUniMsg]
) -> list[DefinitionMsg]:
    py_defs = []
    synthetic_defs = []
    while uni_defs:
        for uni_def in uni_defs:
            py_def = uni_to_py_def(uni_def, ctx, None, synthetic_defs)
            py_defs.append(py_def)
        uni_defs = synthetic_defs
        synthetic_defs = []
    return py_defs


def make_py_call_args(
    args: list[CallArg],
    ctx: dict[DefnUID, DefUniMsg],
) -> tuple[tuple[TermMsg, ...], dict[str, TermMsg]]:
    # for now, everything is a positional argument
    # TODO: Could deduce key args from ordering in defs
    pos: list[TermMsg] = []
    key: dict[str, TermMsg] = {}
    for arg in args:
        v = arg.val
        py_v = uni_to_py_term(v, ctx)
        pos.append(py_v)
    return tuple(pos), key
