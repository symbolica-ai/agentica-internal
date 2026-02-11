# fmt: off
"""
This a hand-curated typeshed file for the builtin `typing` module, specifically the exposed classes and type objections
and some of their non-exported base classes.
"""

import collections.abc
import sys
from types import CodeType as CODETYPE
from types import NoneType as NONETYPE
from typing import Any as UNTYPED
from typing import Never as NEVER
from typing import NoReturn as NORETURN

####################################################################################################

__all__ = [
    # namespaces
    'META', 'PRIVATE',

    # actually exposed by `typing` module
    'get_origin', 'get_args', 'get_type_hints',
    'TypeAliasType', 'TypeVar', 'TypeVarTuple', 'ParamSpec', 'ParamSpecArgs', 'ParamSpecKwargs', 'ForwardRef',
    'Any', 'NoDefault', 'NewType', 'Protocol', 'Annotated', 'TypedDict',
    'NoReturn', 'Never', 'Self', 'LiteralString', 'ClassVar', 'Final', 'Union', 'Optional', 'Unpack',
    'Literal', 'TypeAlias', 'Concatenate', 'TypeGuard', 'TypeIs', 'Required', 'NotRequired', 'ReadOnly',

    # deprecated aliases to collections.abc.XXX
    'Hashable', 'Awaitable', 'Coroutine', 'AsyncIterable', 'AsyncIterator', 'Iterable', 'Iterator', 'Reversible',
    'Sized', 'Container', 'Collection', 'Callable', 'AbstractSet', 'MutableSet', 'Mapping', 'MutableMapping',
    'Sequence', 'MutableSequence', 'List', 'Deque', 'Set', 'FrozenSet', 'MappingView', 'KeysView', 'ItemsView',
    'ValuesView', 'Dict', 'DefaultDict', 'OrderedDict', 'Counter', 'ChainMap', 'Generator', 'AsyncGenerator', 'Type',
]

####################################################################################################

PY13 = sys.version_info >= (3, 13)

type GenericTypeObj = CPythonGenericAlias | CPythonUnionType | _BaseGenericAlias
type SymbolicTypeObj = TypeAliasType | TypeVar | ParamSpec | _SpecialForm | _AnyMeta
type TypingObj = GenericTypeObj | SymbolicTypeObj

type TypeObj = type | TypingObj
type TypeObjs = tuple[TypeObj, ...]

type TypeParam = TypeVar | ParamSpec | TypeVarTuple
type TypeParams = tuple[TypeParam, ...]

####################################################################################################


def get_origin(obj: UNTYPED) -> TypeObj | None:
    return None


def get_args(obj: UNTYPED) -> TypeObjs:
    return ()


def get_type_hints(obj: UNTYPED) -> dict[str, TypeObj]:
    return {}


####################################################################################################


def _idfunc[X](arg: X, *args, **kwargs) -> X:
    return arg


####################################################################################################


class NoDefaultType:
    """Indicates a TypeParam has no default."""


NoDefault = NoDefaultType()


class _Sentinel:
    """Internal sentinel singleton Class."""


_sentinel: _Sentinel = _Sentinel()


class _TypingEllipsis:
    """Internal placeholder for ... (ellipsis)."""


class _AnyMeta(type):
    def __instancecheck__(self, obj) -> bool: ...
    def __repr__(self) -> str: ...


class Any(metaclass=_AnyMeta):
    def __new__(cls, *args, **kwargs): ...


####################################################################################################


class _SpecialForm:
    _name: str
    __name__: str

    def _getitem(self): ...
    def __getattr__(self, item): ...
    def __mro_entries__(self, bases) -> NORETURN: ...
    def __repr__(self) -> str: ...

    def __reduce__(self) -> str | tuple[Any, ...]: ...
    def __call__(self, *args, **kwds) -> NORETURN: ...

    def __or__(self, other): ...
    def __ror__(self, other): ...
    def __instancecheck__(self, obj) -> NORETURN: ...
    def __subclasscheck__(self, cls): ...

    # explicitly tell python item type is unknown
    def __getitem__(self, parameters) -> TypingObj: ...


###############################################################################


class CPythonUnionType:
    __args__: TypeObjs

    def __or__(self, value: Any, /) -> 'CPythonUnionType': ...
    def __ror__(self, value: Any, /) -> 'CPythonUnionType': ...
    def __eq__(self, value: object, /) -> bool: ...
    def __hash__(self) -> int: ...


####################################################################################################


class CPythonGenericAlias:
    """
    types.GenericAlias is defined in cypthon/Objects/generalicaliasobject.c and corresponds to
    generic aliases for builtins, like list[int], dict[str, bool], etc. and has instance fields:

    __origin__:     TypeObj
    __args__:       Tup[TypeObj]
    __parameters__: Tup[TypeVar | ParamSpec | TypeVarTuple]
    __unpacked__:   ???
    """

    __origin__: TypeObj
    __args__: TypeObjs
    __unpacked__: UNTYPED
    __parameters__: TypeParams

    @property
    def __typing_unpacked_tuple_args__(self):
        return None

    def __mro_entries__(self, bases):
        return ()

    def __copy__(self) -> 'CPythonGenericAlias':
        return self

    def __deepcopy__(self) -> 'CPythonGenericAlias':
        return self


####################################################################################################


class TypeAliasType:
    """
    typing.TypeAliasType is the type of the values declared via `type alias = int`, and has instance fields:

    __value__:       TypeObj
    __type_params__: Tup[TypeVar | ParamSpec | TypeVarTuple]
    __parameters__:  Tup[TypeObj]
    __name__:        str
    __module__:      str | None
    """

    def __init__(self, name: str, value: UNTYPED, *, type_params: TypeParams = ()): ...

    @property
    def __value__(self) -> TypeObj:
        return object

    @property
    def __type_params__(self) -> TypeParams:
        return ()

    @property
    def __parameters__(self) -> TypeObjs:
        return ()

    @property
    def __name__(self) -> str:
        return 'name'

    __module__: str = 'module'


####################################################################################################


class TypeVar:
    """
    typing.TypeVar is the type of values created when you write e.g. `class Foo[X]: ...`, and has instance fields:

    __bound__:         TypeObj | None
    __constraints__:   Tup[TypeObj]
    __contravariant__: bool
    __covariant__:     bool
    __default__:       TypeObj | NoDefaultType
    __name__:          str
    """

    __bound__: TypeObj | None
    __constraints__: TypeObjs
    __contravariant__: bool
    __covariant__: bool
    __default__: TypeObj | NoDefaultType

    @property
    def __name__(self) -> str:
        return 'name'


####################################################################################################


class TypeVarTuple:
    """
    typing.TypeVarTuple is the type of values created when you write e.g. `class Foo[*X]: ...`, and has instance fields:
    __default__:       TypeObj | NoDefaultType
    __name__:          str
    has_default:       bool
    """

    @property
    def __name__(self) -> str:
        return 'name'

    @property
    def __default__(self) -> TypeObj | NoDefaultType:
        return NoDefault

    def has_default(self) -> bool:
        return False

    def __init__(self, name: str, *, default: UNTYPED = ...): ...
    def __iter__(self) -> UNTYPED:
        return ()

    def __typing_subst__(self, arg: NEVER) -> NEVER: ...
    def __typing_prepare_subst__(self, alias: UNTYPED, args: UNTYPED) -> tuple[UNTYPED, ...]: ...


####################################################################################################


class ParamSpecArgs:
    @property
    def __origin__(self) -> 'ParamSpec': ...

    def __init__(self, origin: 'ParamSpec'): ...
    def __eq__(self, other: object) -> bool: ...


class ParamSpecKwargs:
    @property
    def __origin__(self) -> 'ParamSpec': ...

    def __init__(self, origin: 'ParamSpec'): ...
    def __eq__(self, other: object) -> bool: ...


class ParamSpec:
    @property
    def __name__(self) -> str:
        return 'name'

    @property
    def __bound__(self) -> UNTYPED:
        return None

    @property
    def __covariant__(self) -> bool:
        return True

    @property
    def __contravariant__(self) -> bool:
        return False

    @property
    def __infer_variance__(self) -> bool:
        return True

    @property
    def __default__(self) -> TypeObj | NoDefaultType:
        return NoDefault

    def has_default(self) -> bool:
        return False

    def __init__(
        self,
        name: str,
        *,
        bound: UNTYPED = None,
        contravariant: bool = False,
        covariant: bool = False,
        infer_variance: bool = False,
        default: UNTYPED = ...,
    ):
        pass

    @staticmethod
    def __new__(*args, **kwargs): ...
    @property
    def args(self) -> ParamSpecArgs: ...

    @property
    def kwargs(self) -> ParamSpecKwargs: ...

    def __typing_subst__(self, arg: UNTYPED) -> UNTYPED: ...
    def __typing_prepare_subst__(self, alias: UNTYPED, args: UNTYPED) -> tuple[UNTYPED, ...]: ...

    def __or__(self, right: UNTYPED) -> _SpecialForm: ...
    def __ror__(self, left: UNTYPED) -> _SpecialForm: ...


####################################################################################################


class ForwardRef:
    slots = (
        '__forward_arg__',
        '__forward_code__',
        '__forward_evaluated__',
        '__forward_value__',
        '__forward_is_argument__',
        '__forward_is_class__',
        '__forward_module__',
    )

    __forward_arg__: str
    __forward_code__: CODETYPE
    __forward_evaluated__: bool
    __forward_value__: UNTYPED | None
    __forward_is_argument__: bool
    __forward_is_class__: bool
    __forward_module__: UNTYPED | None

    def __init__(
        self,
        arg: str,
        is_argument: bool = True,
        module: Any | None = None,
        *,
        is_class: bool = False,
    ): ...

    def _evaluate(
        self,
        globalns: dict[str, UNTYPED] | None,
        localns: dict[str, UNTYPED] | None,
        type_params: TypeParams,
        *,
        recursive_guard: frozenset[str],
    ) -> UNTYPED: ...

    def __eq__(self, other: object) -> bool: ...
    def __hash__(self) -> int: ...
    def __or__(self, other: object) -> _SpecialForm: ...
    def __ror__(self, other: object) -> _SpecialForm: ...
    def __repr__(self) -> str: ...


####################################################################################################


class _BaseGenericAlias:
    """The central part of the internal API.

    This represents a generic version of type 'origin' with type arguments 'params'.
    There are two kind of these aliases: user defined and special. The special ones
    are wrappers around builtin collections and ABCs in collections.abc. These must
    have 'name' always set. If 'inst' is False, then the alias can't be instantiated;
    this is used by e.g. typing.List and typing.Dict.
    """

    _inst: bool  # whether it can be instantiated
    _name: str  # name of the generic, proxied by .__name__
    __origin__: type  # underlying class

    def __init__(self, origin, *, inst=True, name=None): ...
    def __call__(self, *args, **kwargs) -> type: ...
    def __mro_entries__(self, bases) -> tuple[type, ...]: ...
    def __getattr__(self, attr): ...
    def __setattr__(self, attr, val): ...
    def __instancecheck__(self, obj) -> bool: ...
    def __subclasscheck__(self, cls): ...
    def __dir__(self) -> list[str]: ...


# Special typing constructs Union, Optional, Generic, Callable and Tuple
# use three special attributes for internal bookkeeping of generic types:
# * __parameters__ is a tuple of unique free type parameters of a generic
#   type, for example, Dict[T, T].__parameters__ == (T,);
# * __origin__ keeps a reference to a type that was subscripted,
#   e.g., Union[T, int].__origin__ == Union, or the non-generic version of
#   the type.
# * __args__ is a tuple of all arguments used in subscripting,
#   e.g., Dict[T, int].__args__ == (T, int).


####################################################################################################


class _GenericAlias(_BaseGenericAlias):
    """The type of parameterized generics.

    That is, for example, `type(List[int])` is `GenericAlias`.

    Objects which are instances of this class include:
    * Parameterized container types, e.g. `Tuple[int]`, `List[int]`.
     * Note that native container types, e.g. `tuple`, `list`, use
       `types.GenericAlias` instead.
    * Parameterized classes:
        class C[T]: pass
        # C[int] is a GenericAlias
    * `Callable` aliases, generic `Callable` aliases, and
      parameterized `Callable` aliases:
        T = TypeVar('T')
        # _CallableGenericAlias inherits from GenericAlias.
        A = Callable[[], None]  # _CallableGenericAlias
        B = Callable[[T], None]  # _CallableGenericAlias
        C = B[int]  # _CallableGenericAlias
    * Parameterized `Final`, `ClassVar`, `TypeGuard`, and `TypeIs`:
        # All GenericAlias
        Final[int]
        ClassVar[float]
        TypeGuard[bool]
        TypeIs[range]
    """

    __parameters__: TypeObjs
    __value__: TypeObj

    def __eq__(self, other) -> bool: ...
    def __hash__(self) -> int: ...
    def __or__(self, right): ...
    def __getitem__(self, args): ...
    def _determine_new_args(self, args): ...
    def _make_substitution(self, args, new_arg_by_param): ...
    def copy_with(self, params) -> '_GenericAlias': ...
    def __repr__(self) -> str: ...
    def __reduce__(self) -> str | tuple[Any, ...]: ...
    def __mro_entries__(self, bases) -> tuple[type, ...]: ...
    def __iter__(self): ...


####################################################################################################


class _SpecialGenericAlias(_BaseGenericAlias):
    _nparams: int
    _defaults: tuple

    def __init__(self, origin, nparams: int, *, inst=True, name=None, defaults=()):
        super().__init__(origin)
        pass

    def __getitem__(self, params): ...
    def copy_with(self, params) -> '_SpecialGenericAlias': ...
    def __repr__(self) -> str: ...
    def __subclasscheck__(self, cls): ...
    def __reduce__(self) -> str | tuple[Any, ...]: ...
    def __or__(self, right): ...
    def __ror__(self, left): ...


####################################################################################################


class _CallableGenericAlias(_GenericAlias):
    def __repr__(self) -> str: ...
    def __reduce__(self) -> str | tuple[Any, ...]: ...


####################################################################################################


if PY13:
    # this proxies the class created by collections.abc.Callable[XXX, YYY]
    class _AbcCallableGenericAlias(CPythonGenericAlias):
        __slots__ = ()

        def __new__(cls, origin: UNTYPED, args: tuple[UNTYPED, UNTYPED]): ...

        def __repr__(self) -> str: ...

        def __getitem__(self, item) -> '_AbcCallableGenericAlias': ...


####################################################################################################


class _CallableType(_SpecialGenericAlias):
    def copy_with(self, params) -> '_CallableType': ...
    def __getitem__(self, params): ...
    def __getitem_inner__(self, params): ...


####################################################################################################


class _TupleType(_SpecialGenericAlias):
    def __getitem__(self, params): ...


####################################################################################################


class _UnionGenericAlias(_GenericAlias):
    def copy_with(self, params) -> '_UnionGenericAlias': ...
    def __eq__(self, other) -> bool: ...
    def __hash__(self) -> int: ...
    def __repr__(self) -> str: ...
    def __instancecheck__(self, obj) -> bool: ...
    def __subclasscheck__(self, cls): ...
    def __reduce__(self) -> str | tuple[Any, ...]: ...


####################################################################################################


class _LiteralGenericAlias(_GenericAlias):
    def __eq__(self, other) -> bool: ...
    def __hash__(self) -> int: ...


####################################################################################################


class _ConcatenateGenericAlias(_GenericAlias):
    def copy_with(self, params) -> _GenericAlias: ...


####################################################################################################


class _UnpackGenericAlias(_GenericAlias):
    def __repr__(self) -> str: ...

    def __getitem__(self, args): ...

    @property
    def __typing_unpacked_tuple_args__(self) -> UNTYPED:
        return None

    @property
    def __typing_is_unpacked_typevartuple__(self) -> UNTYPED:
        return None


####################################################################################################


class _AnnotatedAlias(_GenericAlias):
    """Runtime representation of an annotated type.

    At its core 'Annotated[t, dec1, dec2, ...]' is an alias for the type 't'
    with extra annotations. The alias behaves like a normal typing alias.
    Instantiating is the same as instantiating the underlying type; binding
    it to types is also the same.

    The metadata itself is stored in a '__metadata__' attribute as a tuple.
    """

    def __init__(self, origin, metadata):
        super().__init__(origin)

    def copy_with(self, params) -> '_AnnotatedAlias': ...
    def __repr__(self) -> str: ...
    def __reduce__(self) -> str | tuple[Any, ...]: ...
    def __eq__(self, other) -> bool: ...
    def __hash__(self) -> int: ...
    def __getattr__(self, attr): ...
    def __mro_entries__(self, bases) -> tuple[type, ...]: ...


class _AnnotatedSpecialForm(_SpecialForm):
    def __getitem__(self, parameters) -> _AnnotatedAlias: ...


Annotated = _AnnotatedSpecialForm()

####################################################################################################


class _TypedDictMeta(type):
    def __new__(cls, name, bases, ns, total=True): ...


def TypedDict(typename, fields=_sentinel, /, *, total=True) -> _TypedDictMeta: ...


TypedDictType: _TypedDictMeta


####################################################################################################


class NewType:
    """NewType creates simple unique types with almost zero runtime overhead."""

    __call__ = _idfunc

    def __init__(self, name, tp): ...
    def __mro_entries__(self, bases) -> tuple[type, ...]: ...
    def __repr__(self) -> str: ...
    def __reduce__(self) -> str | tuple[Any, ...]: ...
    def __or__(self, other): ...
    def __ror__(self, other): ...


####################################################################################################


class Protocol:
    """Base class for protocol classes.

    Protocol classes are defined as::

        class Proto(Protocol):
            def meth(self) -> int:
                ...

    Such classes are primarily used with static type checkers that recognize
    structural subtyping (static duck-typing).

    For example::

        class C:
            def meth(self) -> int:
                return 0

        def func(x: Proto) -> int:
            return x.meth()

        func(C())  # Passes static type check

    See PEP 544 for details. Protocol classes decorated with
    @typing.runtime_checkable act as simple-minded runtime protocols that check
    only the presence of given attributes, ignoring their type signatures.
    Protocol classes can be generic, they are defined as::

        class GenProto[T](Protocol):
            def meth(self) -> T:
                ...
    """

    __slots__ = ()
    _is_protocol = True
    _is_runtime_protocol = False

    def __init_subclass__(cls, *args, **kwargs): ...


####################################################################################################


def _eval_type(
    t: UNTYPED, globalns, localns, type_params=_sentinel, *, recursive_guard=frozenset()
) -> TypeObj: ...
def _type_repr(arg: UNTYPED) -> str:
    return 'type'


####################################################################################################

Hashable = _SpecialGenericAlias(collections.abc.Hashable, 0)  # Not generic.
Awaitable = _SpecialGenericAlias(collections.abc.Awaitable, 1)
Coroutine = _SpecialGenericAlias(collections.abc.Coroutine, 3)
AsyncIterable = _SpecialGenericAlias(collections.abc.AsyncIterable, 1)
AsyncIterator = _SpecialGenericAlias(collections.abc.AsyncIterator, 1)
Iterable = _SpecialGenericAlias(collections.abc.Iterable, 1)
Iterator = _SpecialGenericAlias(collections.abc.Iterator, 1)
Reversible = _SpecialGenericAlias(collections.abc.Reversible, 1)
Sized = _SpecialGenericAlias(collections.abc.Sized, 0)  # Not generic.
Container = _SpecialGenericAlias(collections.abc.Container, 1)
Collection = _SpecialGenericAlias(collections.abc.Collection, 1)
Callable = _CallableType(collections.abc.Callable, 2)
AbstractSet = _SpecialGenericAlias(collections.abc.Set, 1, name='AbstractSet')
MutableSet = _SpecialGenericAlias(collections.abc.MutableSet, 1)
Mapping = _SpecialGenericAlias(collections.abc.Mapping, 2)
MutableMapping = _SpecialGenericAlias(collections.abc.MutableMapping, 2)
Sequence = _SpecialGenericAlias(collections.abc.Sequence, 1)
MutableSequence = _SpecialGenericAlias(collections.abc.MutableSequence, 1)
List = _SpecialGenericAlias(list, 1, inst=False, name='List')
Deque = _SpecialGenericAlias(collections.deque, 1, name='Deque')
Set = _SpecialGenericAlias(set, 1, inst=False, name='Set')
FrozenSet = _SpecialGenericAlias(frozenset, 1, inst=False, name='FrozenSet')
MappingView = _SpecialGenericAlias(collections.abc.MappingView, 1)
KeysView = _SpecialGenericAlias(collections.abc.KeysView, 1)
ItemsView = _SpecialGenericAlias(collections.abc.ItemsView, 2)
ValuesView = _SpecialGenericAlias(collections.abc.ValuesView, 1)
Dict = _SpecialGenericAlias(dict, 2, inst=False, name='Dict')
DefaultDict = _SpecialGenericAlias(collections.defaultdict, 2, name='DefaultDict')
OrderedDict = _SpecialGenericAlias(collections.OrderedDict, 2)
Counter = _SpecialGenericAlias(collections.Counter, 1)
ChainMap = _SpecialGenericAlias(collections.ChainMap, 2)
Generator = _SpecialGenericAlias(collections.abc.Generator, 3, defaults=(NONETYPE, NONETYPE))
AsyncGenerator = _SpecialGenericAlias(collections.abc.AsyncGenerator, 2, defaults=(NONETYPE,))
Type = _SpecialGenericAlias(type, 1, inst=False, name='Type')

####################################################################################################


class PRIVATE:
    idfunc = _idfunc
    eval_type = _eval_type
    type_repr = _type_repr
    TypingEllipsis = _TypingEllipsis
    Sentinel = _Sentinel
    sentinel = _sentinel
    AnyMeta = _AnyMeta
    AnnotatedAlias = _AnnotatedAlias
    TypedDictMeta = _TypedDictMeta
    SpecialForm = _SpecialForm
    CPythonGenericAlias = CPythonGenericAlias
    CPythonUnionType = CPythonUnionType
    AbcCallableGenericAlias = _AbcCallableGenericAlias
    BaseGenericAlias = _BaseGenericAlias
    GenericAlias = _GenericAlias
    SpecialGenericAlias = _SpecialGenericAlias
    CallableGenericAlias = _CallableGenericAlias
    CallableType = _CallableType
    TupleType = _TupleType
    UnionGenericAlias = _UnionGenericAlias
    LiteralGenericAlias = _LiteralGenericAlias
    ConcatenateGenericAlias = _ConcatenateGenericAlias
    UnpackGenericAlias = _UnpackGenericAlias


####################################################################################################

# these don't exist, but the shed pretends they do help type inference understand
# what happens in various cases.

type _Forms = tuple[_SpecialForm, ...]


class AnyForm(_SpecialForm):
    OBJS: _Forms = ()

    def __getitem__(self, parameters) -> NORETURN: ...


class SymbolForm(_SpecialForm):
    OBJS: _Forms = ()

    def __getitem__(self, parameters) -> NORETURN: ...


class UnaryForm[T: TypingObj](_SpecialForm):
    OBJS: _Forms = ()

    def __getitem__(self, parameters) -> T: ...


class NaryForm[T: TypingObj](_SpecialForm):
    OBJS: _Forms = ()

    def __getitem__(self, parameters: tuple) -> T: ...


class WrapperForm(_SpecialForm):
    OBJS: _Forms = ()

    def __getitem__(self, parameters) -> _GenericAlias: ...


class GuardForm(WrapperForm):
    OBJS: _Forms = ()


class FieldForm(WrapperForm):
    OBJS: _Forms = ()


class ClsFieldForm(FieldForm):
    pass


class DctFieldForm(FieldForm):
    pass


####################################################################################################

NoReturn = SymbolForm()
Never = SymbolForm()
Self = SymbolForm()
LiteralString = SymbolForm()
Union = NaryForm[_UnionGenericAlias]()
Optional = UnaryForm[_UnionGenericAlias]()
Unpack = UnaryForm[_UnpackGenericAlias]()
Literal = NaryForm[_LiteralGenericAlias]()
TypeAlias = SymbolForm()
Concatenate = NaryForm[_ConcatenateGenericAlias]()

ClassVar = ClsFieldForm()
Final = ClsFieldForm()
Required = DctFieldForm()
NotRequired = DctFieldForm()
ReadOnly = DctFieldForm()
TypeGuard = GuardForm()
TypeIs = GuardForm()

####################################################################################################


class META:
    GenericTypeObj = GenericTypeObj
    SymbolicTypeObj = SymbolicTypeObj
    TypingObj = TypingObj
    TypeObj = TypeObj
    TypeObjs = TypeObjs
    TypeParam = TypeParam
    TypeParams = TypeParams
    AnyForm = AnyForm
    SymbolForm = SymbolForm
    GuardForm = GuardForm
    FieldForm = FieldForm
    WrapperForm = WrapperForm
    UnaryForm = UnaryForm
    NaryForm = NaryForm

    GENERIC_TYPE_CLASSES: tuple[type, ...] = ()
    SYMBOLIC_TYPE_CLASSES: tuple[type, ...] = ()
    TYPING_OBJ_CLASSES: tuple[type, ...] = ()
    TYPE_OBJ_CLASSES: tuple[type, ...] = ()

    class FORMS:
        SYMBOL: _Forms = (
            NoReturn,
            Never,
            Self,
            LiteralString,
            TypeAlias,
        )
        UNARY: _Forms = (
            Unpack,
            Optional,
        )
        NARY: _Forms = (
            Union,
            Literal,
            Concatenate,
        )
        GUARD: _Forms = (
            TypeGuard,
            TypeIs,
        )
        CLS_FIELD: _Forms = (
            ClassVar,
            Final,
        )
        DCT_FIELD: _Forms = (
            Required,
            NotRequired,
            ReadOnly,
        )
        FIELD: _Forms = CLS_FIELD + DCT_FIELD
        WRAPPER: _Forms = GUARD + FIELD
        ALL: _Forms = SYMBOL + WRAPPER + UNARY + NARY

    AnyForm.OBJS = FORMS.ALL
    SymbolForm.OBJS = FORMS.SYMBOL
    UnaryForm.OBJS = FORMS.UNARY
    NaryForm.OBJS = FORMS.NARY
    WrapperForm.OBJS = FORMS.WRAPPER
    GuardForm.OBJS = FORMS.WRAPPER
    FieldForm.OBJS = FORMS.FIELD
    ClsFieldForm.OBJS = FORMS.CLS_FIELD
    DctFieldForm.OBJS = FORMS.DCT_FIELD
