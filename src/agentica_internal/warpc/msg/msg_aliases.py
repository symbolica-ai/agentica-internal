# fmt: off

from typing import TYPE_CHECKING

from ..alias import *

__all__ = [
    'ArgsMsg',
    'KwargsMsg',
    'AnnotationsMsg',
    'AttributesMsg',
    'MethodMsg',
    'MethodsMsg',
    'TypeMsg',
    'ClassMsg',
    'ObjectMsg',
    'FunctionMsg',
    'ClassMsg',
    'ModuleMsg',
    'FutureMsg',
    'PropertyMsg',
    'ExceptionRefMsg',
    'PropertiesMsg',
    'SrcLocationMsg'
]


################################################################################

if TYPE_CHECKING:
    from .term import TermMsg
    from .term_resource import ResourceMsg, LocalResourceMsg
    from ..data.identifier import Identifier

################################################################################

# these make codec compilation easier

type ArgsMsg            = Tup['TermMsg']
type KwargsMsg          = Rec['TermMsg']
type AttributesMsg      = Rec['TermMsg']

type MethodMsg          = tuple[MethodKind, 'ResourceMsg']
type MethodsMsg         = Rec[MethodMsg]

type TypeMsg            = TermMsg
type ClassMsg           = ResourceMsg
type ObjectMsg          = ResourceMsg
type FunctionMsg        = ResourceMsg
type ModuleMsg          = ResourceMsg
type PropertyMsg        = ResourceMsg
type ExceptionRefMsg    = ResourceMsg
type FutureMsg          = LocalResourceMsg

type AnnotationsMsg     = Rec['TermMsg']
type PropertiesMsg      = Rec['ResourceMsg']

type SrcLocationMsg     = Identifier | None
