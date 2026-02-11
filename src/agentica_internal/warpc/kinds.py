# fmt: off

import asyncio

from typing import Any, TypeGuard
from enum import StrEnum
from collections.abc import Callable, Coroutine
from types import (
    FunctionType,
    CoroutineType,
    EllipsisType,
    GeneratorType,
    AsyncGeneratorType,
    ModuleType,
    NoneType,
    NotImplementedType,
)
from functools import _lru_cache_wrapper as CachedFunctionT

from ..cpython.properties import PropertyT, is_property_t
from ..cpython.alias import CALLABLES as FUNC_TYPES
from ..cpython.alias import UnboundMethodC, UnboundDunderMethodC
from ..cpython.classes.anno import ANNOS, AnnoT
from ..cpython.iters import BuiltinIteratorT, ITER_TYPES
from .alias import Rec, Tup, MethodKind


__all__ = [
    'Kind',
    'TermT',
    'TypeT',
    'ValueT',
        'AtomT',
            'NumberT',
            'StrLikeT',
            'SingletonT',
        'ContainerT',
            'SequenceT',
            'MappingT',
    'ResourceT',
        'ObjectT',
        'ClassT',
        'FunctionT',
        'ModuleT',
        'CoroutineT',
        'IteratorT',
        'FutureT',
    'ArgsT',
    'KwargsT',
    'AnnotationsT',
    'PropertiesT',
    'AttributesT',
    'MethodT',
    'MethodsT',
    'PropertyT',
    'is_atom_t',
    'is_object_t',
    'is_class_t',
    'is_function_t',
    'is_method_t',
    'is_property_t',
    'is_coroutine_t',
    'is_module_t',
    'is_type_t',
    'is_generator_t',
    'is_iterator_t',
    'is_future_t',
    'is_compact_t',
    'pack_method',
    'unpack_method',
]


################################################################################

class Kind(StrEnum):
    Object         = 'object'
    Class          = 'class'
    Coroutine      = 'coroutine'
    Type           = 'type'
    Function       = 'function'
    Module         = 'module'
    Iterator       = 'iterator'
    Generator      = 'generator'
    Future         = 'future'
    Enum           = 'enum'
    Unknown        = 'unknown'
    Property       = 'property'
    Exception      = 'exception'

################################################################################

type TermT      = Any
type NumberT    = bool | int | float
type StrLikeT   = str | bytes
type SingletonT = NoneType | NotImplementedType | EllipsisType
type AtomT      = NumberT | StrLikeT | SingletonT
type SequenceT  = list | dict | set | frozenset
type MappingT   = dict
type ContainerT = SequenceT | MappingT
type ValueT     = AtomT | ContainerT
type ObjectT    = object
type TypeT      = AnnoT
type ClassT     = type
type FunctionT  = Callable[..., Any]
type MethodT    = FunctionType | staticmethod | classmethod
type CoroutineT = CoroutineType
type ModuleT    = ModuleType
type IteratorT  = BuiltinIteratorT
type FutureT    = asyncio.Future

type ResourceT  = ObjectT | ClassT | FunctionT | ModuleT | IteratorT | FutureT

################################################################################

# these make it easy to recognize certain patterns for codec compilation
type ArgsT            = Tup[TermT]
type KwargsT          = Rec[TermT]
type AnnotationsT     = Rec[TypeT]
type AttributesT      = Rec[TermT]
type MethodsT         = Rec[MethodT]
type PropertiesT      = Rec[PropertyT]

################################################################################

TYPE_TYPES = ANNOS

GENERATOR_TYPES = AsyncGeneratorType, GeneratorType,
ITERATOR_TYPES = GENERATOR_TYPES + ITER_TYPES

ATOM_TYPES = bool, int, float, str, bytes, None, NotImplementedType, EllipsisType

NON_OBJECT_TYPES = FUNC_TYPES + TYPE_TYPES + GENERATOR_TYPES + (type, ModuleType, CoroutineType)

METHOD_TYPES = FunctionType, staticmethod, classmethod, UnboundMethodC, UnboundDunderMethodC

def is_atom_t(arg: Any) -> TypeGuard[AtomT]:
    return type(arg) in ATOM_TYPES

def is_object_t(arg: Any) -> TypeGuard[ObjectT]:
    return not issubclass(type(arg), NON_OBJECT_TYPES)

def is_class_t(arg: Any) -> TypeGuard[ClassT]:
    return type(arg) is type or isinstance(arg, type)

def is_coroutine_t(arg: Any) -> TypeGuard[CoroutineT]:
    return type(arg) is CoroutineType or isinstance(arg, Coroutine)

def is_function_t(arg: Any) -> TypeGuard[FunctionT]:
    cls = type(arg)
    if issubclass(cls, FUNC_TYPES):
        return True
    if cls is type or not callable(cls):
        return False
    if cls is CachedFunctionT:
        return True
    name = cls.__qualname__
    if name == 'cython_function_or_method':
        return True   # (CPython is not a system module)
    if name.startswith('CDLL.'):
        from _ctypes import CFuncPtr
        return issubclass(cls, CFuncPtr)
    return False

def is_method_t(arg: Any) -> TypeGuard[MethodT]:
    return type(arg) in METHOD_TYPES

def is_module_t(arg: Any) -> TypeGuard[ModuleT]:
    return issubclass(type(arg), ModuleType)

def is_type_t(arg: Any) -> TypeGuard[TypeT]:
    return issubclass(type(arg), TYPE_TYPES)

def is_generator_t(arg: Any) -> TypeGuard[IteratorT]:
    return type(arg) in GENERATOR_TYPES

def is_iterator_t(arg: Any) -> TypeGuard[IteratorT]:
    return type(arg) in ITERATOR_TYPES

def is_future_t(arg: Any) -> TypeGuard[FutureT]:
    return isinstance(arg, asyncio.Future)

def is_compact_t(obj: Any) -> bool:
    """Can this be cheaply encoded without resorting to encoding a resource?"""
    cls = type(obj)
    if cls in ATOM_TYPES:
        return True
    if cls in (list, tuple, set, dict, frozenset) and not len(obj):
        return True
    from .system import LRID_TO_SRID
    return id(obj) in LRID_TO_SRID

################################################################################

def pack_method(kind: MethodKind, func: FunctionT) -> MethodT:
    if kind == 'class':
        return classmethod(func)  # type: ignore
    elif kind == 'static':
        return staticmethod(func)
    elif kind == 'instance':
        return func  # type: ignore
    else:
        raise ValueError(kind)

def unpack_method(method: MethodT) -> tuple[MethodKind, FunctionT]:
    if isinstance(method, classmethod):
        return 'class', method.__func__
    elif isinstance(method, staticmethod):
        return 'static', method.__func__
    else:
        return 'instance', method
