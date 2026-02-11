# fmt: off

from typing import get_args

from ...cpython.classes.anno import *
from .__ import *
from .base import *

__all__ = [
    'TypeData',
    'TypeAliasData',
    'TypeVarData',
    'TypeUnionData',
    'GenericAliasData',
    'CallableTypeData',
    'ForwardRefData',
]

'''
Note, despite the name, 'virtual types' are actually real type annotations
when decoded, and involve no virtual resource requests.
'''

################################################################################

class TypeData(ResourceData):
    __slots__ = ()

    KIND = Kind.Type
    FORBIDDEN_FORM = Any

    @classmethod
    def describe_resource(cls, ty: TypeT) -> 'TypeData':
        return choose_data_class(ty).describe_real_type(ty)

    def create_resource(self, handle: ResourceHandle) -> TypeT:
        handle.kind = Kind.Type
        return self.create_real_type()

    ############################################################################

    @classmethod
    def describe_real_type(cls, ty: TypeT) -> 'TypeData':
        raise NotImplementedError()

    def create_real_type(self) -> TypeT:
        raise NotImplementedError()


def choose_data_class(ty: TypeT) -> type[TypeData]:
    cls = type(ty)
    if cls is TAlias:
        return TypeAliasData
    elif cls is TVar or cls is TParamSpec:
        return TypeVarData
    elif cls is TUnion or cls is CUnion:
        return TypeUnionData
    elif cls is TForward:
        return ForwardRefData
    elif getattr(ty, '__origin__', None) is A.Callable:
        return CallableTypeData
    else:
        return GenericAliasData


################################################################################

class TypeAliasData(TypeData):
    __slots__ = 'name', 'module', 'params', 'value'

    name:   str
    module: str
    params: Tup[TermT]
    value:  TermT

    @classmethod
    def describe_real_type(cls, ty: TypeT) -> 'TypeAliasData':
        assert type(ty) is TAlias

        name = ty.__name__
        module = ty.__module__
        if is_forbidden(ty, module):
            raise E.WarpEncodingForbiddenError(f"<typealias '{module}.{name}'>")

        data = TypeAliasData()
        data.name = name
        data.module = module
        data.params = ty.__type_params__
        data.value = ty.__value__

        return data

    def create_real_type(self) -> TypeT:
        return T.TypeAliasType(self.name, self.value)


################################################################################

class TypeVarData(TypeData):
    __slots__ = 'name', 'pspec'

    name:        str
    pspec:       bool

    @classmethod
    def describe_real_type(cls, ty: TypeT) -> 'TypeVarData':
        assert type(ty) in (TVar, TParamSpec)

        data = TypeVarData()
        data.name = ty.__name__
        data.pspec = isinstance(ty, TParamSpec)

        return data

    def create_real_type(self) -> TypeT:
        if self.pspec:
            return TParamSpec(self.name)
        else:
            return TVar(self.name)


################################################################################

class GenericAliasData(TypeData):
    __slots__ = 'origin', 'args'

    origin:      TermT
    args:        Tup[TermT]

    @classmethod
    def describe_real_type(cls, ty: TGeneric) -> 'GenericAliasData':
        assert type(ty) in GENERICS, f"class {type(ty)} not a generic type class"
        data = GenericAliasData()

        origin = getattr(ty, '__origin__', None)

        # this resolves List[int] back to List
        if type(ty) is TGeneric:
            if name := getattr(ty, '_name', None):
                if name[0].isupper() and hasattr(T, name):
                    origin = getattr(T, name)

        data.origin = origin
        data.args = get_args(ty)
        return data

    def create_real_type(self) -> TypeT:
        origin, args = self.origin, self.args
        if origin is None:
            return Any
        try:
            if type(origin) is TForm and len(args) == 1:
                ty = origin[args[0]]  # e.g. ClassVar[int]
            elif isinstance(origin, type):
                ty = TGeneric(origin, args)
            else:
                ty = origin[args]  # e.g. Tuple[int, str]
        except Exception:
            return Any
        return ty


################################################################################

class CallableTypeData(TypeData):
    __slots__ = 'abc', 'args', 'ret'

    abc:      bool
    args:     TermT | Tup[TermT]
    ret:      TermT

    @classmethod
    def describe_real_type(cls, ty: TypeT) -> 'CallableTypeData':
        origin = getattr(ty, '__origin__', None)
        assert origin is A.Callable, f"wrong origin: {origin} =!= {A.Callable}"
        args, ret = get_args(ty)
        data = CallableTypeData()
        data.abc = type(ty).__module__ == 'collections.abc'
        data.args = tuple(args) if type(args) is list else args
        data.ret = ret
        return data

    def create_real_type(self) -> TypeT:
        args = self.args
        args = list(args) if type(args) is tuple else args
        ret = self.ret
        cls = A.Callable if self.abc else T.Callable
        return cls[args, ret]


################################################################################


class TypeUnionData(TypeData):
    __slots__ = 'alts', 'sys'

    MIGHT_ALIAS = True

    alts:  Tup[TermT]
    sys:   bool

    @classmethod
    def describe_real_type(cls, ty: TypeT) -> 'TypeUnionData':
        assert type(ty) in (CUnion, TUnion)
        data = TypeUnionData()
        data.alts = get_args(ty)
        data.sys = type(ty) is CUnion
        return data

    def create_real_type(self) -> TypeT:
        alts = self.alts
        n = len(alts)
        if n == 0:
            return NoReturn
        if n == 1:
            return alts[0]
        if self.sys:
            t1, *tr = alts
            for t in tr:
                t1 |= t
            return t1
        return T.Union[alts]


################################################################################


class ForwardRefData(TypeData):
    __slots__ = 'name'

    name: str

    @classmethod
    def describe_real_type(cls, ty: TypeT) -> 'ForwardRefData':
        # TODO: should we store module here as well?
        data = ForwardRefData()
        data.name = ty.__forward_arg__ if isinstance(ty, TForward) else ty
        return data

    def create_real_type(self) -> TypeT:
        return TForward(self.name)
