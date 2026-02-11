# fmt: off

# this file is pretty much imported everywhere else and sets up extremely common shared imports,
# to avoid endless ruff churn and inconvenience in having to import things per-file

import collections.abc as A
import operator as O
import typing as T
from abc import ABC, abstractmethod

from collections.abc import Callable, Coroutine, Awaitable, Iterable as Iter, Sequence as Seq

from functools import partial
from types import ModuleType, FunctionType, CoroutineType
from typing import Any, ClassVar, Generic, Literal, NoReturn, Protocol, Self, TypeGuard
from typing import cast, overload, TYPE_CHECKING

from ..core import type as S
from ..core import debug as D
from ..core import fmt as F
from ..core import print as P

from ..core.make import *
from ..core.result import *
from ..core.sentinels import *
from ..core.log import LogFlag, LogContext, should_log_cls

from . import exceptions as E
from . import flags

from .kinds import *
from .fmt import *
from .alias import *
from .predicates import *


__all__ = [
    # from system modules
    'partial',
    'ModuleType', 'FunctionType', 'CoroutineType',
    'ABC', 'abstractmethod',
    'Callable', 'Coroutine', 'Awaitable', 'Iter', 'Seq',
    'Any', 'Generic', 'TypeGuard', 'Self', 'ClassVar', 'Protocol',
    'Literal', 'NoReturn', 'cast', 'overload', 'TYPE_CHECKING',

    # aliases for common modules
    'T', 'S', 'A', 'O', 'D', 'P', 'F', 'E',

    'flags',

    # from `core.log`
    'LogFlag',
    'LogContext',
    'should_log_cls',

    # from `core.sentinels`
    'ArgDefault',  'FieldAbsent',  'Pending', 'Closed', 'Canceled', 'OnDemand',
    'ARG_DEFAULT', 'FIELD_ABSENT', 'PENDING', 'CLOSED', 'CANCELED', 'ON_DEMAND',
    'Sentinel', 'is_sentinel',

    # from `core.result`
    'Result',

    # from `core.make`
    'mklist', 'mkdict', 'mkset',

    # from `warpc.alias`
    'Tup', 'Rec', 'Fn', 'SendBytes', 'EncodeFmt', 'DecodeFmt', 'MethodKind', 'VarScope',
    'AsyncMode', 'HashMode',
    'optstr', 'optint', 'strtup', 'strlist', 'typetup', 'record',
    'Name', 'Ptr', 'ID',
    'WorldID', 'LocalRID', 'GlobalRID', 'ResourceUID',
    'FrameKey', 'SystemRID', 'FrameID', 'MessageID', 'FutureID', 'Options',

    # from `warpc.predicates`
    'is_bool',
    'is_str',
    'is_strtup',
    'is_strlist',
    'is_optstr',
    'is_tup',
    'is_list',
    'is_rec',
    'is_bytes',

    # from `warpc.kinds`
    'Kind',
    'TermT',
    'ValueT', 'AtomT', 'NumberT', 'StrLikeT', 'SingletonT', 'ContainerT', 'SequenceT', 'MappingT',
    'ResourceT', 'ObjectT', 'ClassT', 'FunctionT', 'CoroutineT', 'ModuleT', 'TypeT', 'IteratorT',
    'FutureT',
    'MethodsT', 'ArgsT', 'KwargsT', 'AnnotationsT', 'AttributesT',

    # from `warpc.fmt`
    'f_id', 'f_grid', 'f_fkey',
    'f_slot', 'f_object', 'f_object_id',
]
