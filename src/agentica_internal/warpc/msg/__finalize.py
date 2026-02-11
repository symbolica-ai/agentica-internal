# fmt: off

from types import ModuleType, NoneType
from collections.abc import Callable
from typing import Any, TypeAliasType, ForwardRef, Union

import msgspec
from .signature_msg import SignatureMsg
from .resource_def import DefinitionMsg

from ...core.debug import avoid_file
from ...core.anno import union_iter
from ...core.print import eprint
from ...core.log import LogFlag

from ..data.identifier import Identifier
from ..alias import Tup, Rec, MethodKind
from .. import flags

from . import (
    base, bad,
    resource_data, resource_def,
    rpc, rpc_framed,
    rpc_request, rpc_request_repl, rpc_request_resource,
    rpc_sideband,
    term, term_atom, term_container, term_exception,
    term_resource, term_result, term_special, term_wrapper,
    msg_aliases
)

from .__json import fmt_json
from .__msgpack import pprint_msgpack

from .bad import NO_MSG, Msg
from .term import TermMsg, SIMPLE_ENCODERS, COMPLEX_ENCODERS, CONSTANT_ENCODERS
from .term_resource import ResourceMsg, UserResourceMsg
from .resource_data import FunctionDataMsg
from .term_exception import SystemExceptionMsg, ExceptionMsg
from .term_lambda import SyntaxMsg

__all__ = [
    'finalize_message_classes',
]


################################################################################

LOG_FINALIZE = False

avoid_file(__file__)

################################################################################

MSG_CLS_MODULES: list[ModuleType] = [
    msg_aliases,
    base, bad,
    resource_data, resource_def,
    rpc, rpc_framed,
    rpc_request, rpc_request_repl, rpc_request_resource,
    rpc_sideband,
    term, term_atom, term_container, term_exception,
    term_resource, term_result, term_special, term_wrapper
]

def _import_msg_classes():

    for mod in MSG_CLS_MODULES:
        imports = NAME_TO_MSG_CLS.copy()
        mod.__dict__.update(NAME_TO_MSG_CLS)


MSG_CLS_LIST:    list[type[Msg]] = []
NAME_TO_MSG_CLS: dict[str, type[Msg]] = {}

################################################################################

def _scan_msg_classes(fn: Callable[[type[Msg]], None]):

    for msg_cls in MSG_CLS_LIST:
        try:
            fn(msg_cls)
        except Exception as exc:
            exc.add_note(f'while applying {fn.__name__} to {msg_cls.__name__}')
            raise

################################################################################

upd_cnst = CONSTANT_ENCODERS.update
upd_atom = SIMPLE_ENCODERS.update
upd_comp = COMPLEX_ENCODERS.update

def _visit_cls(cls: type[Msg]):
    MSG_CLS_LIST.append(cls)
    NAME_TO_MSG_CLS[cls.__name__] = cls

    cls.LOG = LogFlag(cls)  # type: ignore
    subs = cls.__subclasses__()
    cls.TAG = cls.__struct_config__.tag

    if not subs:
        if hasattr(cls, 'V') and not issubclass(cls, ResourceMsg):
            types = tuple(union_iter(cls.V.__value__, type))
            if encode_fn := getattr(cls, 'encode_constant', None):
                msg = encode_fn()
                upd_cnst(dict.fromkeys(types, msg))
            if encode_fn := getattr(cls, 'encode_atom', None):
                upd_atom(dict.fromkeys(types, encode_fn))
            elif encode_fn := getattr(cls, 'encode_compound', None):
                upd_comp(dict.fromkeys(types, encode_fn))
        cls.LEAF_CLASSES = (cls,)
        cls.UNION = cls  # type: ignore
        return

    leafs = []
    extend = leafs.extend
    for sub in subs:
        _visit_cls(sub)
        extend(sub.LEAF_CLASSES)

    if cls is TermMsg and flags.INLINE_ATOMS:
        leafs.extend(flags.INLINE_ATOMS)

    if cls is ResourceMsg and flags.INLINE_DEFINITIONS:
        leafs.append(DefinitionMsg)

    cls.LEAF_CLASSES = tuple(leafs)

    union: Any = Union[*leafs]
    cls.UNION = union  # type: ignore


################################################################################

def _resolve_forward_refs(msg_cls: type[Msg]) -> None:

    annos = getattr(msg_cls, '__annotations__', None)
    if annos is None:
        return

    for key, anno in annos.items():
        if isinstance(anno, ForwardRef):
            anno = anno.__forward_arg__
        if isinstance(anno, TypeAliasType):
            anno = anno.__name__
        if isinstance(anno, str):
            try:
                parsed = parse(anno)
                annos[key] = parsed
            except:
                pass

def parse(anno: str):
    if equiv := get_equiv(anno):
        return equiv
    if anno.startswith('Tup['):
        parsed = parse(anno[4:-1])
        return Tup[parsed]
    elif anno.startswith('Rec['):
        parsed = parse(anno[4:-1])
        return Rec[parsed]
    elif ' | ' in anno:
        parsed = list(map(parse, anno.split(' | ')))
        return Union[*parsed]
    elif anno == 'None':
        return None
    cls = NAME_TO_MSG_CLS[anno]
    return cls.UNION


################################################################################

def _attach_decoders(cls: type[Msg]):
    cls_name = cls.__name__

    union_t = cls.UNION
    if LOG_FINALIZE:
        from ...core.type import anno_str
        if type(union_t) is not type(Msg):
            eprint(f'{cls_name:<20}{anno_str(union_t)}')
    try:
        json_decoder = msgspec.json.Decoder(union_t).decode
        msgpack_decoder = msgspec.msgpack.Decoder(union_t).decode
    except Exception as e:
        e.add_note(f'error while attaching decoders to {cls_name}:')
        e.add_note(f'UNION = {union_t}')
        f_annos = '\n'.join(f"\t{k:<20}: {v} {type(v)}" for k, v in cls.__annotations__.items())
        e.add_note(f_annos)
        raise

    def from_json(msg_cls, json_data: bytes):
        try:
            assert msg_cls is cls
            assert isinstance(json_data, bytes)
            json_data = bytes(json_data)
            return json_decoder(json_data)
        except Exception as exc:
            f_json = fmt_json(json_data)
            f_cls = msg_cls.__module__ + '.' + msg_cls.__name__
            exc.add_note(f'error while decoding {f_cls!r}:\n{f_json}')
            raise

    def from_msgpack(msg_cls, msgpack_data: bytes):
        if not isinstance(msgpack_data, bytes):
            return NO_MSG
        assert msg_cls is cls
        try:
            if not msgpack_data:
                return cls()
            return msgpack_decoder(msgpack_data)
        except Exception as exc:
            print_msgspec_error(cls_name, msgpack_data, exc)
            raise

    from_msgpack.__name__ = from_msgpack.__qualname__ = f'{cls_name}.from_msgpack'
    from_json.__name__ = from_json.__qualname__ = f'{cls_name}.from_json'

    cls.from_json = classmethod(from_json)
    cls.from_msgpack = classmethod(from_msgpack)


def print_msgspec_error(cls_name: str, msgpack_data: bytes, exc: Exception) -> None:
    eprint(
        f'\n\nERROR DECODING {cls_name}',
        'EXCEPTION:',
        exc,
        'MESSAGE FOLLOWS:',
        sep='\n',
    )
    pprint_msgpack(msgpack_data, err=True)


################################################################################

def _dispatch_on_sys_exc_types():
    from ..system import SYS_EXCEPTIONS
    # for cls in SYS_EXCEPTIONS:
    #     try:
    #         exc = cls()
    #         try:
    #             s = exc.__getstate__()
    #             if s is not None:
    #                 print()
    #                 print("Exception state", cls, s)
    #         except Exception as e:
    #             print()
    #             print("Cannot got exception state", cls, e)
    #     except Exception as e:
    #         print()
    #         print(get_signature(cls))
    #         print("Cannot create", cls, e)
    upd_comp(dict.fromkeys(SYS_EXCEPTIONS, SystemExceptionMsg.encode_compound))


################################################################################

FINALIZED = False

EQUIVS: dict[str, Any] = {
    'str': str,
    'int': int,
    'float': float,
    'bool': bool,
    'None': NoneType
}
get_equiv = EQUIVS.get

def finalize_message_classes():
    eprint('\nfinalize_message_classes\n') if LOG_FINALIZE else None
    global FINALIZED
    if FINALIZED:
        eprint("warning: finalize_message_classes called more than once")
        return

    _visit_cls(Msg)
    MSG_CLS_LIST.reverse()
    _import_msg_classes()

    MSG_CLS_LIST.remove(SignatureMsg)
    MSG_CLS_LIST.insert(0, SignatureMsg)

    excp_msg_union = ExceptionMsg.UNION                        # type: ignore
    synt_msg_union = SyntaxMsg.UNION                           # type: ignore
    term_msg_union = TermMsg.UNION                             # type: ignore
    rsrc_msg_union = ResourceMsg.UNION                         # type: ignore
    term_tup_t = tuple[term_msg_union, ...]                    # type: ignore
    term_rec_t = dict[str, term_msg_union]                     # type: ignore
    rsrc_rec_t = dict[str, rsrc_msg_union]                     # type: ignore
    synt_lst_t = list[synt_msg_union]                          # type: ignore
    method_pair_t = tuple[MethodKind, rsrc_msg_union]          # type: ignore
    methods_msg_t = dict[str, method_pair_t | rsrc_msg_union]  # type: ignore
    fn_data_tup_t: Any = tuple[FunctionDataMsg, ...]           # type: ignore

    EQUIVS['ExceptionMsg']       = excp_msg_union
    EQUIVS['TermMsg']            = term_msg_union
    EQUIVS['SyntaxMsg']          = synt_msg_union
    EQUIVS['ResourceMsg']        = rsrc_msg_union
    EQUIVS['LocalResourceMsg']   = rsrc_msg_union

    EQUIVS['ArgsMsg']            = term_tup_t
    EQUIVS['KwargsMsg']          = term_rec_t
    EQUIVS['AttributesMsg']      = term_rec_t
    EQUIVS['SyntaxMsgs']         = synt_lst_t
    EQUIVS['MethodsMsg']         = methods_msg_t

    EQUIVS['TypeMsg']            = term_msg_union
    EQUIVS['ObjectMsg']          = rsrc_msg_union
    EQUIVS['ClassMsg']           = rsrc_msg_union
    EQUIVS['ModuleMsg']          = rsrc_msg_union
    EQUIVS['FutureMsg']          = rsrc_msg_union
    EQUIVS['FunctionMsg']        = rsrc_msg_union
    EQUIVS['PropertyMsg']        = rsrc_msg_union
    EQUIVS['ExceptionRefMsg']    = UserResourceMsg

    EQUIVS['PropertiesMsg']      = rsrc_rec_t
    EQUIVS['AnnotationsMsg']     = term_rec_t
    EQUIVS['AttributesT']        = term_rec_t
    EQUIVS['SrcLocationMsg']     = Identifier | None

    _scan_msg_classes(_resolve_forward_refs)
    _scan_msg_classes(_attach_decoders)
    _dispatch_on_sys_exc_types()
    FINALIZED = True
    eprint('\nfinalize_message_classes done\n') if LOG_FINALIZE else None
