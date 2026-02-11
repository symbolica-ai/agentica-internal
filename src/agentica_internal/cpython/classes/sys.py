# fmt: off

# NOTE: see core.type for more detail

import re

from types import (
    # singletons
    NoneType                  as NoneT,
    EllipsisType              as EllipT,
    NotImplementedType        as NotImplT,

    # misc
    MappingProxyType          as MapProxyT,
    ModuleType                as ModuleT,
    FrameType                 as FrameT,
    TracebackType             as TracebackT,

    # type annotations
    UnionType                 as UnionT,
    GenericAlias              as GenericT,

    # function types
    CellType                  as CellT,
    CodeType                  as CodeT,
    FunctionType              as FunctionT,
    CoroutineType             as CoroutineT,
    GeneratorType             as GeneratorT,
    AsyncGeneratorType        as AGeneratorT,
    MethodType                as BoundMethodT,

    # wrappers and descriptors
    MethodDescriptorType      as UnboundMethodC,
    WrapperDescriptorType     as UnboundDunderMethodC,
    MethodWrapperType         as BoundDunderMethodC,
    ClassMethodDescriptorType as BoundClassMethodC,
    BuiltinFunctionType       as BoundMethodOrFuncC,
    GetSetDescriptorType      as MutablePropertyC,
    MemberDescriptorType      as SlotPropertyC,
)

from functools import _lru_cache_wrapper as CachingFunctionC
from _collections import _tuplegetter as TupleSlotPropertyC

__all__ = [
    'NoneT',
    'EllipT',
    'NotImplT',
    'MapProxyT',
    'ModuleT',
    'FrameT',
    'TracebackT',
    'UnionT',
    'GenericT',
    'CellT',
    'CodeT',
    'FunctionT',
    'CoroutineT',
    'GeneratorT',
    'AGeneratorT',
    'BoundMethodT',
    'UnboundMethodC',
    'UnboundDunderMethodC',
    'BoundDunderMethodC',
    'BoundClassMethodC',
    'BoundMethodOrFuncC',
    'BoundMethodC',
    'MutablePropertyC',
    'SlotPropertyC',
    'CachingFunctionC',
    'TupleSlotPropertyC',

    'PyCallableT',
    'CCallableT',

    'PRIMITIVES',
    'CONTAINERS',
    'PY_CALLABLES',
    'C_CALLABLES',
    'CALLABLES',
    'PROPERTIES',

    'SYS_TO_NAME',
    'BUILTIN_TO_NAME'
]

###############################################################################

# these can be used with isinstance

PyCallableT = FunctionT | BoundMethodT

BoundMethodC = type(re.compile('').finditer)  # inherits from BoundMethodOrFuncC

CCallableT  = UnboundMethodC | UnboundDunderMethodC | BoundDunderMethodC | \
              BoundClassMethodC | BoundMethodOrFuncC | BoundMethodC

###############################################################################

PY_CALLABLES: tuple[type, ...]
C_CALLABLES:  tuple[type, ...]
CALLABLES:    tuple[type, ...]
PRIMITIVES:   tuple[type, ...]
CONTAINERS:   tuple[type, ...]

PY_CALLABLES = FunctionT, BoundMethodT

C_CALLABLES: tuple[type, ...] = (
    UnboundMethodC,
    UnboundDunderMethodC,
    BoundDunderMethodC,
    BoundClassMethodC,
    BoundMethodOrFuncC,
    BoundMethodC,
    CachingFunctionC
)

CALLABLES = PY_CALLABLES + C_CALLABLES

PROPERTIES = MutablePropertyC, SlotPropertyC, TupleSlotPropertyC, property

PRIMITIVES = int, bool, float, EllipT, NotImplT, NoneT
CONTAINERS = list, tuple, set, frozenset, dict

SYS_TO_NAME: dict[type, str] = {
    NoneT:                  'NoneT',
    EllipT:                 'EllipT',
    NotImplT:               'NotImplT',
    MapProxyT:              'MapProxyT',
    ModuleT:                'ModuleT',
    FrameT:                 'FrameT',
    TracebackT:             'TracebackT',
    UnionT:                 'UnionT',
    GenericT:               'GenericT',
    CellT:                  'CellT',
    CodeT:                  'CodeT',
    FunctionT:              'FunctionT',
    CoroutineT:             'CoroutineT',
    GeneratorT:             'GeneratorT',
    AGeneratorT:            'AGeneratorT',
    BoundMethodT:           'BoundMethodT',
    UnboundMethodC:         'UnboundMethodC',
    UnboundDunderMethodC:   'UnboundDunderMethodC',
    BoundDunderMethodC:     'BoundDunderMethodC',
    BoundClassMethodC:      'BoundClassMethodC',
    BoundMethodOrFuncC:     'BoundMethodOrFuncC',
    BoundMethodC:           'BoundMethodC',
    MutablePropertyC:       'MutablePropertyC',
    SlotPropertyC:          'SlotPropertyC',
    TupleSlotPropertyC:     'TupleSlotPropertyC',
}

BUILTIN_TO_NAME: dict[type, str] = {
    bool:                   'bool',
    int:                    'int',
    float:                  'float',
    str:                    'str',
    bytearray:              'bytearray',
    bytes:                  'bytes',
    object:                 'object',
    type:                   'type',
    list:                   'list',
    tuple:                  'tuple',
    set:                    'set',
    frozenset:              'frozenset',
    dict:                   'dict'
}
