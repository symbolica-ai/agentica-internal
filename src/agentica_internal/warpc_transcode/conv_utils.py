import builtins
from asyncio import Future
from collections import defaultdict
from enum import Enum
from types import FunctionType
from typing import TYPE_CHECKING, Any, Literal, Never
from typing import ClassVar as TypingClassVar

from msgspec import UNSET, UnsetType

from agentica_internal.core.print import colorize, hprint
from agentica_internal.core.data import bidict
from agentica_internal.core.log.log_flag import LogFlag
from agentica_internal.warpc.alias import GlobalRID, FrameID, MessageID
from agentica_internal.warpc.system import LRID_TO_SRID


from .uni_msgs import (
    ClassDefUniMsg,
    ClassPayload,
    DefnUID,
    DefUniMsg,
    InterfaceUniMsg,
    IntersectionPayload,
    IntersectionUniMsg,
    RefUniMsg,
    TypeStringRefUniMsg,
)
from .uni_sys_id import BUILTIN_UNI_IDS
from ..warpc.fmt import f_grid


if TYPE_CHECKING:
    from agentica_internal.warpc.msg.all import FramedMsg
    from .uni_msgs import (
        DefnUID,
        FunctionDefUniMsg,
        Membership,
        MethodSignatureUniMsg,
        RequestUniMsg,
        ResponseUniMsg,
    )

CNV = 1048576  # conversion factor for resource IDs (=2^20)
ORDER_MARKER = "|"

LOG_TS = LogFlag('TS')

DEP_GRAPH = colorize('DepGraph')


def get_def_or_sysref_from_ctx(
    ctx: dict[DefnUID, DefUniMsg], ref: 'RefUniMsg | Membership | TypeStringRefUniMsg'
) -> DefUniMsg | RefUniMsg | None:
    from .uni_msgs import Membership, RefUniMsg, TypeStringRefUniMsg

    if isinstance(ref, (RefUniMsg, Membership)) and not isinstance(ref, TypeStringRefUniMsg):
        uid = ref.uid
    elif isinstance(ref, TypeStringRefUniMsg):
        uid = ref.uid
    else:
        raise ValueError(f"Transcoder Error: Unsupported reference type: {type(ref)}")

    deref = ctx.get(uid, None)

    if deref is None:
        if uid.resource < 0:
            # For system resources use references in place of defs
            return RefUniMsg(uid=uid)
        else:
            grid = f_uid_grid(uid)
            known = ' '.join(f_uid_grid(uid) for uid in ctx.keys()) or 'none'
            details = f"GRID  = {grid}\nUID   = {uid}\nKNOWN = {known}"
            raise ValueError(f"Transcoder Error: Reference not found in context:\n{details}")
    return deref


def f_uid_grid(uid: DefnUID) -> str:
    return f_grid(resourceUIDToGrid(uid))


def gridToResourceUID(grid: GlobalRID) -> 'DefnUID':
    # TODO: @tali ... hack: use -1 has a marker for client world

    from .uni_msgs import DefnUID

    if grid[0] == -1:
        resource_UID = grid[2]
        return DefnUID(
            world='client',
            resource=resource_UID,
        )
    else:
        # Try to generate somewhat unique deterministic resource ID
        resource_UID = (
            int(grid[0] % CNV) * CNV * CNV + int(grid[1] % CNV) * CNV + (grid[2] % CNV) - CNV
        )
        return DefnUID(
            world='server',
            resource=resource_UID,
            py_world=grid[0],
            py_frame=grid[1],
            py_resource=grid[2],
        )


def resourceUIDToGrid(uid: 'DefnUID') -> GlobalRID:
    # TODO: @tali here's the reverse hack
    if uid.world == 'client':
        return (-1, -1, uid.resource)
    else:
        assert uid.world == 'server'
        assert uid.py_world is not UNSET
        assert uid.py_resource is not UNSET
        assert uid.py_frame is not UNSET
        return (uid.py_world, uid.py_frame, uid.py_resource)


def unsetNone[T](value: T | None) -> T | UnsetType:
    if value is None:
        return UNSET
    return value


def function_to_method(
    function: 'FunctionDefUniMsg', methodOf: 'Membership'
) -> 'MethodSignatureUniMsg':
    from .uni_msgs import MethodSignatureUniMsg

    return MethodSignatureUniMsg(
        uid=function.uid,
        methodOf=methodOf,
        payload=function.payload,
    )


###
# System resource conversion
# TODO: this is neither efficient nor complete atm

_PY_SYSID_TO_UNI_NAME: dict[int, set[str]] = {
    id(object): {'Object'},
    id(str): {'String'},
    id(int): {'Number'},
    id(float): {'Number'},
    id(bool): {'Boolean'},
    id(list): {'Array'},
    id(dict): {'Map'},
    id(set): {'Set'},
    id(tuple): {'Tuple'},
    id(Exception): {'Error'},
    id(BaseException): {'Error'},
    id(Future): {'Future'},
    id(FunctionType): {'Function'},
    id(type(None)): {'None'},
    id(Never): {'Never'},
    id(Literal): {'Literal'},
    id(AttributeError): {'AttributeError'},
    id(KeyError): {'KeyError'},
    id(ValueError): {'ValueError'},
    id(TypeError): {'TypeError'},
    id(builtins.repr): {'magicRepr'},
    id(builtins.print): {'console.log'},
    id(builtins.len): {'magicLen'},
    id(builtins.isinstance): {'magicInstanceof'},
    id(builtins.hasattr): {'Reflect.has'},
    id(builtins.getattr): {'Reflect.get'},
    id(builtins.dir): {'magicKeys'},
    id(Enum): {'Enum'},
    id(type): {'TYPE'},
    id(TypingClassVar): {'ClassVar'},
}


def sridToUniSysId(sid: int) -> int | None:
    for py_sys_id, uni_names in _PY_SYSID_TO_UNI_NAME.items():
        if LRID_TO_SRID.get(py_sys_id) == sid:
            for uni_name in uni_names:
                uni_id = BUILTIN_UNI_IDS.get(uni_name)
                if uni_id is not None:
                    return uni_id
    return None


def uniSysIdToSrid(uni_id: int) -> int | None:
    uni_name: str | None = None
    for name, uid in BUILTIN_UNI_IDS.items():
        if uid == uni_id:
            uni_name = name
            break
    if not uni_name:
        return None
    for py_sys_id, mapped_names in _PY_SYSID_TO_UNI_NAME.items():
        if uni_name in mapped_names:
            return LRID_TO_SRID.get(py_sys_id)
    return None


class MangleManager:
    """
    Original names are deterministically mapped to normalized names.
    This mapping is not injective, so we need to add a suffix to the normalized name
    to obtain unique names.
    """

    type NormalizedName = str
    type Suffix = int
    type OriginalName = str
    type UniqueName = str

    uniqueness: dict[NormalizedName, Suffix]
    names: bidict[OriginalName, UniqueName]

    # special-case normalization rules
    normalizers: list[tuple[str, str]]
    reserved_prefixes: list[str]
    reserved_suffixes: list[str]

    NUM_PREFIX = 'NUM__'
    KW_SUFFIX = '_KW_'

    def __init__(self):
        self.uniqueness = defaultdict(int)
        self.names = bidict()
        # default special-case TypeScript->Python normalization rules
        self.normalizers = [
            ('$', 'Dollar_'),
        ]
        self.reserved_prefixes = [self.NUM_PREFIX]
        self.reserved_suffixes = [self.KW_SUFFIX]

    def normalize(self, original_name: OriginalName) -> NormalizedName:
        """replace non-Python compatible characters with underscores, and guard for keywords"""
        import keyword
        import re

        # check the ident does not already use a reserved prefix or suffix or sentinel
        uses_reserved_prefix = any(map(original_name.startswith, self.reserved_prefixes))
        uses_reserved_suffix = any(map(original_name.endswith, self.reserved_suffixes))
        uses_sentinel = any(sentinel in original_name for _, sentinel in self.normalizers)
        if uses_reserved_prefix or uses_reserved_suffix or uses_sentinel:
            raise ValueError(
                f"Identifier {original_name} cannot use reserved prefixes"
                + f"({', '.join(self.reserved_prefixes)})"
                + f", suffixes "
                + f"({', '.join(self.reserved_suffixes)})"
                + f", or sentinels "
                + f"({', '.join(sentinel for _, sentinel in self.normalizers)})"
            )

        normalized_name = original_name

        # we special-case a few normalization rules first.
        for original_pattern, normalized_pattern in self.normalizers:
            normalized_name = normalized_name.replace(original_pattern, normalized_pattern)

        # remaining invalid characters are replaced with underscores
        normalized = re.sub(r"\W", "_", normalized_name)

        if not normalized[0].isalpha() and normalized[0] != '_':
            normalized = f"{self.NUM_PREFIX}{normalized}"

        if keyword.iskeyword(normalized):
            normalized = f"{normalized}{self.KW_SUFFIX}"

        return normalized

    def mangle(self, original_name: OriginalName) -> UniqueName:
        if original_name in self.names:
            # this name already has a unique mangled name
            return self.names[original_name]

        normalized_name = self.normalize(original_name)
        self.names[original_name] = normalized_name
        return normalized_name

    def demangle(self, unique_name: UniqueName) -> OriginalName:
        """reverse the mangling process if this name was previously mangled."""
        # leave unchanged if never mangled
        return self.names.with_value(unique_name, default=unique_name)


def msg_uni_name_sanitization(msg: Any, mangler: MangleManager) -> Any:
    """
    Recursively sanitize all names in a UniMsg by mangling TypeScript names into
    Python-compatible identifiers using the provided MangleManager.
    Used when receiving messages from TypeScript.
    """
    from .uni_msgs import (
        CallMethodPayload,
        ClassField,
        ClassMethod,
        ClassPayload,
        DelAttrPayload,
        FunctionArgument,
        FunctionPayload,
        GetAttrPayload,
        HasAttrPayload,
        SetAttrPayload,
    )

    if msg is UNSET or msg is None:
        return msg

    # Some fields are lists
    if isinstance(msg, list):
        return [msg_uni_name_sanitization(item, mangler) for item in msg]

    # Handle structs with __struct_fields__
    fields = getattr(type(msg), "__struct_fields__", None)
    if not fields:
        return msg

    updates = {}

    # Special handling for specific payload types with name fields
    if isinstance(msg, ClassPayload):
        if msg.name is not UNSET:
            updates['name'] = mangler.mangle(msg.name)
    elif isinstance(msg, FunctionPayload):
        if msg.name is not UNSET:
            updates['name'] = mangler.mangle(msg.name)
    elif isinstance(msg, ClassMethod):
        if msg.name is not UNSET:
            updates['name'] = mangler.mangle(msg.name)
    elif isinstance(msg, ClassField):
        if msg.name is not UNSET:
            updates['name'] = mangler.mangle(msg.name)
    elif isinstance(msg, FunctionArgument):
        if msg.name is not UNSET:
            updates['name'] = mangler.mangle(msg.name)
    elif isinstance(msg, (GetAttrPayload, SetAttrPayload, DelAttrPayload, HasAttrPayload)):
        if hasattr(msg, 'attr') and msg.attr is not None:
            updates['attr'] = mangler.mangle(msg.attr)
    elif isinstance(msg, CallMethodPayload):
        if msg.method_name is not UNSET:
            updates['method_name'] = mangler.mangle(msg.method_name)

    # Recursively process all fields
    for field_name in fields:
        if field_name in updates:
            continue  # Already handled above
        try:
            attr = getattr(msg, field_name)
        except Exception:
            continue
        if attr is not UNSET:
            new_attr = msg_uni_name_sanitization(attr, mangler)
            if new_attr is not attr:
                updates[field_name] = new_attr

    if updates:
        return type(msg)(**{**{f: getattr(msg, f) for f in fields}, **updates})
    return msg


def msg_TS_name_restoration(msg: Any, mangler: MangleManager) -> Any:
    """
    Recursively restore all names in a UniMsg by demangling Python identifiers
    back to their original TypeScript names using the provided MangleManager.
    Used when sending messages to TypeScript.
    """
    from .uni_msgs import (
        CallMethodPayload,
        ClassField,
        ClassMethod,
        ClassPayload,
        DelAttrPayload,
        FunctionArgument,
        FunctionPayload,
        GetAttrPayload,
        HasAttrPayload,
        SetAttrPayload,
    )

    if msg is UNSET or msg is None:
        return msg

    # Some fields are lists
    if isinstance(msg, list):
        return [msg_TS_name_restoration(item, mangler) for item in msg]

    # Handle structs with __struct_fields__
    fields = getattr(type(msg), "__struct_fields__", None)
    if not fields:
        return msg

    updates = {}

    # Special handling for specific payload types with name fields
    if isinstance(msg, ClassPayload):
        if msg.name is not UNSET:
            updates['name'] = mangler.demangle(msg.name)
    elif isinstance(msg, FunctionPayload):
        if msg.name is not UNSET:
            updates['name'] = mangler.demangle(msg.name)
    elif isinstance(msg, ClassMethod):
        if msg.name is not UNSET:
            updates['name'] = mangler.demangle(msg.name)
    elif isinstance(msg, ClassField):
        if msg.name is not UNSET:
            updates['name'] = mangler.demangle(msg.name)
    elif isinstance(msg, FunctionArgument):
        if msg.name is not UNSET:
            updates['name'] = mangler.demangle(msg.name)
    elif isinstance(msg, (GetAttrPayload, SetAttrPayload, DelAttrPayload, HasAttrPayload)):
        if hasattr(msg, 'attr') and msg.attr is not None:
            updates['attr'] = mangler.demangle(msg.attr)
    elif isinstance(msg, CallMethodPayload):
        if msg.method_name is not UNSET:
            updates['method_name'] = mangler.demangle(msg.method_name)

    # Recursively process all fields
    for field_name in fields:
        if field_name in updates:
            continue  # Already handled above
        try:
            attr = getattr(msg, field_name)
        except Exception:
            continue
        if attr is not UNSET:
            new_attr = msg_TS_name_restoration(attr, mangler)
            if new_attr is not attr:
                updates[field_name] = new_attr

    if updates:
        return type(msg)(**{**{f: getattr(msg, f) for f in fields}, **updates})
    return msg


def order_defs(defs: list[DefUniMsg], keys: list[Any] = []) -> tuple[list[DefUniMsg], list[Any]]:
    """
    Topologically sort definitions by dependencies.

    This algorithm handles cycles by:
    1. Detecting inheritance cycles (which are errors)
    2. Grouping mutually recursive class-like defs into strata
    3. Sorting strata by dependency order
    4. Within each stratum, processing defs in inheritance order
    5. Replacing forward references with TypeStringRefUniMsg where needed

    Bases references are never replaced with type strings (they must be concrete types).
    """

    uid_to_def: dict[DefnUID, DefUniMsg] = {definition.uid: definition for definition in defs}

    def is_classlike(defmsg: DefUniMsg) -> bool:
        """Class-like defs (ClassDefUniMsg, InterfaceUniMsg, IntersectionUniMsg) can be replaced by type strings"""
        return (
            isinstance(defmsg, (ClassDefUniMsg, InterfaceUniMsg, IntersectionUniMsg))
            and defmsg.uid.resource > -1
        )

    def get_name(defmsg: DefUniMsg) -> str:
        """Extract the name from a definition."""
        return getattr(defmsg.payload, 'name', f'Unnamed{defmsg.uid.resource}')

    def walk_refs(value: Any, callback: Any) -> None:
        """
        Recursively walk a structure and invoke callback on each RefUniMsg found.
        Does not walk into TypeStringRefUniMsg.
        """
        if value is UNSET or value is None:
            return
        if isinstance(value, RefUniMsg):
            callback(value)
            return
        if isinstance(value, TypeStringRefUniMsg):
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                walk_refs(item, callback)
            return
        if isinstance(value, dict):
            for k, v in value.items():
                walk_refs(k, callback)
                walk_refs(v, callback)
            return
        fields = getattr(type(value), "__struct_fields__", None)
        if fields:
            for field_name in fields:
                try:
                    attr = getattr(value, field_name)
                except Exception:
                    continue
                if attr is not UNSET:
                    walk_refs(attr, callback)

    def extract_refs(defmsg: DefUniMsg) -> set[DefnUID]:
        """
        Extract all RefUniMsg UIDs from a definition.
        """
        found: set[DefnUID] = set()
        allowed_uids = set(uid_to_def.keys())

        def process_ref(ref: RefUniMsg) -> None:
            if ref.uid in allowed_uids:
                found.add(ref.uid)

        walk_refs(defmsg, process_ref)

        return found

    def extract_bases(defmsg: DefUniMsg) -> set[DefnUID]:
        """Extract classlike UIDs from the 'bases' or 'classes' field of a class-like definition."""
        if not is_classlike(defmsg):
            return set()

        if isinstance(defmsg, IntersectionUniMsg):
            bases_list = getattr(defmsg.payload, 'classes', UNSET)
        else:
            bases_list = getattr(defmsg.payload, 'bases', UNSET)

        if bases_list is UNSET or bases_list is None:
            return set()

        found: set[DefnUID] = set()

        def process_ref(ref: RefUniMsg) -> None:
            if ref.uid in classlike_uids:
                found.add(ref.uid)

        walk_refs(bases_list, process_ref)
        return found

    def replace_refs_in_def(defmsg: DefUniMsg, uids_to_replace: dict[DefnUID, str]) -> DefUniMsg:
        """
        Create a copy of defmsg with specified UIDs replaced by TypeStringRefUniMsg.
        Should never replaces refs in the 'bases' field.
        """
        if not uids_to_replace:
            return defmsg

        def replacer(value: Any) -> tuple[Any, bool]:
            """Returns (new_value, changed)."""
            if value is UNSET or value is None:
                return value, False
            if isinstance(value, RefUniMsg):
                if value.uid in uids_to_replace:
                    return TypeStringRefUniMsg(uid=value.uid, name=uids_to_replace[value.uid]), True
                return value, False
            if isinstance(value, (list, tuple, set)):
                result = []
                any_changed = False
                for item in value:
                    new_item, changed = replacer(item)
                    result.append(new_item)
                    any_changed = any_changed or changed
                if any_changed:
                    return (type(value)(result) if not isinstance(value, list) else result), True
                return value, False
            if isinstance(value, dict):
                new_dict = {}
                any_changed = False
                for k, v in value.items():
                    new_v, changed = replacer(v)
                    new_dict[k] = new_v
                    any_changed = any_changed or changed
                if any_changed:
                    return new_dict, True
                return value, False
            fields = getattr(type(value), "__struct_fields__", None)
            if fields:
                updates = {}
                for field_name in fields:
                    try:
                        attr = getattr(value, field_name)
                    except Exception:
                        continue
                    if attr is not UNSET:
                        new_attr, changed = replacer(attr)
                        if changed:
                            updates[field_name] = new_attr
                if updates:
                    if 'bases' in updates and isinstance(value, ClassPayload):
                        raise RuntimeError(
                            f"Forward reference detection attempted to replace 'bases' of class {get_name(defmsg)} with type string."
                        )
                    if 'classes' in updates and isinstance(value, IntersectionPayload):
                        raise RuntimeError(
                            f"Forward reference detection attempted to replace 'bases classes' of interface {get_name(defmsg)} with type string."
                        )
                    return type(value)(
                        **{**{f: getattr(value, f) for f in fields}, **updates}
                    ), True
            return value, False

        result, _ = replacer(defmsg)
        return result

    # ===== STAGE 0: Build dependency and inheritance graphs =====

    dependency_graph: dict[DefnUID, set[DefnUID]] = {}
    inheritance_graph: dict[DefnUID, set[DefnUID]] = {}
    classlike_uids: set[DefnUID] = set()

    for defmsg in defs:
        uid = defmsg.uid
        dependency_graph[uid] = extract_refs(defmsg)

        if is_classlike(defmsg):
            classlike_uids.add(uid)
            inheritance_graph[uid] = extract_bases(defmsg)

    if LOG_TS:
        hprint(DEP_GRAPH, f"Built graphs: {len(defs)} defs, {len(classlike_uids)} classlike")

    # ===== STAGE 1: Detect inheritance cycles =====

    visited_inheritance: set[DefnUID] = set()

    def find_inheritance_cycle(start_uid: DefnUID) -> list[DefnUID] | None:
        """DFS to find a cycle in the inheritance graph starting from start_uid."""
        path: list[DefnUID] = []

        def dfs(current_uid: DefnUID) -> list[DefnUID] | None:
            if current_uid in path:
                cycle_start = path.index(current_uid)
                return path[cycle_start:] + [current_uid]

            if current_uid in visited_inheritance:
                return None

            visited_inheritance.add(current_uid)
            path.append(current_uid)

            for base_uid in inheritance_graph.get(current_uid, set()):
                if base_uid not in visited_inheritance:
                    cycle = dfs(base_uid)
                    if cycle:
                        return cycle

            path.pop()
            return None

        return dfs(start_uid)

    for uid in classlike_uids:
        if uid not in visited_inheritance:
            cycle = find_inheritance_cycle(uid)
            if cycle:
                cycle_str = " -> ".join(f"{get_name(uid_to_def[u])} ({u.resource})" for u in cycle)
                raise ValueError(f"Inheritance cycle detected: {cycle_str}")

    if LOG_TS:
        hprint(DEP_GRAPH, "No inheritance cycles detected")

    # ===== STAGE 2: Create strata from dependency cycles =====

    def find_dependency_cycles() -> list[tuple[set[DefnUID], set[DefnUID]]]:
        """Find all strongly connected components with multiple classlike nodes"""
        index_counter = 0
        stack: list[DefnUID] = []
        lowlinks: dict[DefnUID, int] = {}
        index: dict[DefnUID, int] = {}
        on_stack: set[DefnUID] = set()
        sccs: list[tuple[set[DefnUID], set[DefnUID]]] = []

        def strongconnect(uid: DefnUID) -> None:
            nonlocal index_counter
            index[uid] = index_counter
            lowlinks[uid] = index_counter
            index_counter += 1
            stack.append(uid)
            on_stack.add(uid)

            for dep_uid in dependency_graph.get(uid, set()):
                if dep_uid not in index:
                    strongconnect(dep_uid)
                    lowlinks[uid] = min(lowlinks[uid], lowlinks[dep_uid])
                elif dep_uid in on_stack:
                    lowlinks[uid] = min(lowlinks[uid], index[dep_uid])

            if lowlinks[uid] == index[uid]:
                scc: set[DefnUID] = set()
                while True:
                    w = stack.pop()
                    on_stack.remove(w)
                    scc.add(w)
                    if w == uid:
                        break
                classlike_in_scc = scc.intersection(classlike_uids)
                if len(classlike_in_scc) >= 1:
                    sccs.append((classlike_in_scc, scc))
                elif len(scc) > 1:
                    raise RuntimeError(
                        f"Found a dependency component with multiple nodes but none are classlike: {scc}"
                    )
                else:
                    # Singleton SCC
                    sccs.append((classlike_in_scc, scc))

        for uid in dependency_graph.keys():
            if uid not in index:
                strongconnect(uid)

        return sccs

    all_sccs = find_dependency_cycles()

    uid_to_scc: dict[DefnUID, frozenset[DefnUID]] = {}
    scc_to_stratum: dict[frozenset[DefnUID], frozenset[DefnUID]] = {}
    classlike_scc_count = 0

    for classlike_scc, full_scc in all_sccs:
        frozen_scc = frozenset(full_scc)
        for uid in full_scc:
            uid_to_scc[uid] = frozen_scc

        if len(classlike_scc) > 0:
            classlike_scc_count += 1
            stratum = frozenset(classlike_scc)
            scc_to_stratum[frozen_scc] = stratum

    # Build SCC dependency graph (for all SCCs)
    all_scc_set = set(uid_to_scc.values())
    scc_deps: dict[frozenset[DefnUID], set[frozenset[DefnUID]]] = {}
    for scc in all_scc_set:
        deps: set[frozenset[DefnUID]] = set()
        for uid in scc:
            for dep_uid in dependency_graph.get(uid, set()):
                dep_scc = uid_to_scc[dep_uid]
                if dep_scc != scc:
                    deps.add(dep_scc)
        scc_deps[scc] = deps

    if LOG_TS:
        hprint(
            DEP_GRAPH, f"Found {len(all_scc_set)} SCCs ({classlike_scc_count} with classlike nodes)"
        )

    # ===== STAGE 3: Sort strata by dependency order =====

    # Toposort SCCs and collect strata
    sorted_strata: list[frozenset[DefnUID]] = []
    visited_sccs: set[frozenset[DefnUID]] = set()

    def toposort_scc_dfs(scc: frozenset[DefnUID]) -> None:
        if scc in visited_sccs:
            return
        visited_sccs.add(scc)
        for dep_scc in scc_deps[scc]:
            toposort_scc_dfs(dep_scc)
        if scc in scc_to_stratum:
            sorted_strata.append(scc_to_stratum[scc])

    for scc in all_scc_set:
        toposort_scc_dfs(scc)

    if LOG_TS:
        hprint(DEP_GRAPH, f"Sorted {len(sorted_strata)} strata")

    # ===== STAGE 4: Process each stratum in order =====

    ordered_defs: list[DefUniMsg] = []
    visited_uids: set[DefnUID] = set()

    def sort_by_inheritance(stratum_uids: set[DefnUID]) -> list[DefnUID]:
        """Sort class-like defs within a stratum by inheritance order."""
        stratum_ordered: list[DefnUID] = []
        visited_in_stratum: set[DefnUID] = set()

        def inheritance_dfs(uid: DefnUID) -> None:
            if uid in visited_in_stratum:
                return
            visited_in_stratum.add(uid)
            bases = inheritance_graph.get(uid, set())
            bases_in_stratum = bases.intersection(stratum_uids)
            for base_uid in bases_in_stratum:
                inheritance_dfs(base_uid)
            stratum_ordered.append(uid)

        for uid in stratum_uids:
            inheritance_dfs(uid)

        return stratum_ordered

    for stratum in sorted_strata:
        stratum_ordered_uids = sort_by_inheritance(set(stratum))

        for classlike_uid in stratum_ordered_uids:
            collected_non_classlike: list[DefnUID] = []
            forward_classlike_refs: dict[DefnUID, str] = {}

            def collect_and_find_forward_refs(current_uid: DefnUID) -> None:
                """DFS collecting non-classlike nodes and recording forward classlike refs."""
                if current_uid in visited_uids:
                    return

                if current_uid in classlike_uids:
                    forward_classlike_refs[current_uid] = get_name(uid_to_def[current_uid])
                    return

                for dep_uid in dependency_graph.get(current_uid, set()):
                    collect_and_find_forward_refs(dep_uid)

                collected_non_classlike.append(current_uid)
                visited_uids.add(current_uid)

            # Note: dependency graph contains self references if there are any
            for dep_uid in dependency_graph.get(classlike_uid, set()):
                collect_and_find_forward_refs(dep_uid)

            if forward_classlike_refs and LOG_TS:
                hprint(
                    DEP_GRAPH,
                    f"Replacing forward refs in {get_name(uid_to_def[classlike_uid])}:\n"
                    f"{list(forward_classlike_refs.keys())} -> {list(forward_classlike_refs.values())}",
                )

            # Replace forward RefMsg in the collected defs
            for uid in collected_non_classlike:
                uid_to_def[uid] = replace_refs_in_def(uid_to_def[uid], forward_classlike_refs)

            # Replace forward RefMsg in the classlike def itself
            updated_classlike = replace_refs_in_def(
                uid_to_def[classlike_uid], forward_classlike_refs
            )
            uid_to_def[classlike_uid] = updated_classlike

            ordered_defs.extend(uid_to_def[uid] for uid in collected_non_classlike)
            ordered_defs.append(updated_classlike)
            visited_uids.add(classlike_uid)

    # ===== STAGE 5: Append remaining non-classlike defs =====

    for uid in uid_to_def.keys():
        if uid not in visited_uids:
            ordered_defs.append(uid_to_def[uid])
            visited_uids.add(uid)

    ordered_keys = []
    if keys:
        assert len(defs) == len(keys), "defs and keys must have the same length"
        key_map = {definition.uid: key for key, definition in zip(keys, defs)}
        ordered_keys = [key_map[definition.uid] for definition in ordered_defs]

    return ordered_defs, ordered_keys


# Frame model translation

################################################################################

# whatever was going on here needs to be fixed in the TS SDK by adding a messageID
type PyRPCIds = tuple[FrameID, MessageID]  # fid, mid
type UniRequestIDs = tuple[FrameID, FrameID, FrameID]  # pid, fid, mid
type UniResponseIDs = tuple[FrameID, FrameID]  # pid, fid

################################################################################


def py_to_uni_request_ids(msg: 'FramedMsg') -> UniRequestIDs:
    pid, fid, mid = 0, msg.fid, msg.mid
    return pid, 0, mid


def uni_to_py_request_ids(req: 'RequestUniMsg') -> PyRPCIds:
    fid = req.selfFID
    mid = req.requestedFID
    return fid, mid


################################################################################


def py_to_uni_response_ids(msg: 'FramedMsg') -> UniResponseIDs:
    pid, fid, mid = 0, msg.fid, msg.mid
    if fid == 0:  # originated in python?
        fid = mid
    return pid, fid


def uni_to_py_response_ids(res: 'ResponseUniMsg') -> PyRPCIds:
    fid = res.selfFID
    return fid, fid
