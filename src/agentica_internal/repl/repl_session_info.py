# fmt: off

from dataclasses import dataclass, field
from typing import Literal

from ..warpc.predicates import *
from .repl_callable_info import ReplCallableInfo
from .repl_var_info import VarKind

__all__ = [
    'ReplResourcesInfo',
    'ReplReturnInfo',
    'ReplSystemInfo',
    'ReplSessionInfo',
    'ReplRole',
    'VALID_REPL_ROLES',
]


################################################################################

type ReplRole = Literal['function', 'agent']

VALID_REPL_ROLES = 'function', 'agent'

################################################################################

@dataclass
class ReplResourcesInfo:

    names:  tuple[str, ...]    = ()
    kinds:  dict[str, VarKind] = field(default_factory=dict)
    reprs:  dict[str, str]     = field(default_factory=dict)
    stub:   str                = ''

    def __bool__(self) -> bool:
        return bool(self.names) and bool(self.stub.strip())

    def clear(self):
        self.names = ()
        self.kinds.clear()
        self.reprs.clear()
        self.stub = ''

    def update(self, names, kinds, reprs, stub):
        self.names = tuple(dict.fromkeys(self.names) | dict.fromkeys(names))  # preserve order
        self.kinds.update(kinds)
        self.reprs.update(reprs)
        self.stub = stub or self.stub  # preserve the old stub if the new one is empty

    def __debug_info_str__(self) -> str:
        return f'names={self.names}'


################################################################################

@dataclass
class ReplSystemInfo:

    # python_version: str
    modules: tuple[str, ...] = ()

    def __debug_info_str__(self) -> str:
        return f'modules=<{len(self.modules)}>'


################################################################################

@dataclass
class ReplReturnInfo:

    type_str: str  = ''
    is_text:  bool = False
    is_none:  bool = False

    def __debug_info_str__(self) -> str:
        return f'type={self.type_str}'


################################################################################

@dataclass
class ReplSessionInfo:
    """
    Represents all the information needed to do prompting at once,
    so that we do not need to make repeated calls to the AgentRepl.

    This object is capable of accepting json-formatted updates via
    `.update`, and `AgentRepl.initialize()` will emit exactly the output
    needed to keep the `ReplSessionInfo` up-to-date with warp-driven changes.
    """

    role:       ReplRole
    returns:    ReplReturnInfo
    locals:     ReplResourcesInfo
    globals:    ReplResourcesInfo
    system:     ReplSystemInfo
    agentic_fn: ReplCallableInfo
    supports_custom_tools: bool = False

    @staticmethod
    def empty() -> 'ReplSessionInfo':
        return ReplSessionInfo(
            role='agent',
            returns=ReplReturnInfo(),
            locals=ReplResourcesInfo(),
            globals=ReplResourcesInfo(),
            system=ReplSystemInfo(),
            agentic_fn=ReplCallableInfo(),
            supports_custom_tools=False,
        )

    ############################################################################

    @property
    def is_function(self) -> bool:
        return self.role == 'function'

    @property
    def is_agent(self) -> bool:
        return self.role == 'agent'

    @property
    def uses_tool_calls(self) -> bool:
        """Returns True if the model should use tool calls instead of markdown."""
        return self.supports_custom_tools

    ############################################################################

    @property
    def return_type(self) -> str:
        return self.returns.type_str

    @property
    def is_returning_text(self) -> bool:
        return self.returns.is_text

    @property
    def is_returning_none(self) -> bool:
        return self.returns.is_none

    ############################################################################

    @property
    def has_arguments(self) -> bool:
        return bool(self.agentic_fn.arg_names)

    @property
    def function_name(self) -> str:
        return self.agentic_fn.fun_name

    @property
    def function_argument_names(self) -> list[str]:
        return self.agentic_fn.arg_names

    @property
    def function_argument_types(self) -> dict[str, str]:
        return self.agentic_fn.arg_annos

    @property
    def function_arguments_stub(self) -> str:
        return self.agentic_fn.args_stub

    @property
    def function_argument_signature(self) -> str:
        return self.agentic_fn.signature_str()

    @property
    def function_description(self) -> str:
        return self.agentic_fn.doc_str or ''

    @property
    def function_stub(self) -> str:
        return self.agentic_fn.fun_stub

    ############################################################################

    @property
    def available_modules(self) -> tuple[str, ...]:
        return self.system.modules

    @property
    def has_global_resources(self) -> bool:
        return bool(self.globals.stub)

    @property
    def has_local_resources(self) -> bool:
        return bool(self.locals.stub)

    @property
    def global_resources(self) -> tuple[str, ...]:
        return self.globals.names

    @property
    def local_resources(self) -> tuple[str, ...]:
        return self.locals.names

    @property
    def global_resources_stub(self) -> str:
        return self.globals.stub

    @property
    def local_resources_stub(self) -> str:
        return self.locals.stub

    @property
    def inputs_stub(self) -> str:
        return self.locals.stub

    @property
    def input_reprs(self) -> dict[str, str]:
        return self.locals.reprs

    ############################################################################

    def __template_vars__(self) -> set[str]:
        return SESSION_VARS

    def __debug_info_str__(self) -> str:
        return f'role={self.role} ret={self.returns.type_str}'

    ############################################################################

    def update(self, dct: dict[str, object]):
        self.__update_field(dct, 'returns',    ReplReturnInfo)
        self.__update_field(dct, 'locals',     ReplResourcesInfo)
        self.__update_field(dct, 'globals',    ReplResourcesInfo)
        self.__update_field(dct, 'system',     ReplSystemInfo)
        self.__update_field(dct, 'agentic_fn', ReplCallableInfo)
        self.__dict__.update(dct)

    def __update_field(self, dct: dict[str, object], name: str, cls: type):
        kwargs = dct.pop(name, None)
        if isinstance(kwargs, dict):
            setattr(self, name, cls(**kwargs))

################################################################################

SESSION_VARS = {
    'is_agentic_fn',
    'is_agent',
    # tool call support
    'supports_custom_tools',
    'uses_tool_calls',
    # for agentic functions AND agents
    'task_description',
    'return_type',
    'is_returning_text',
    'is_returning_none',
    # for agentic functions
    'has_arguments',
    'function_name',
    'function_description',
    'function_argument_names',
    'function_argument_types',
    'function_argument_signature',
    'function_arguments_stub',
    'function_stub',
    # system and resource information
    'available_modules',
    'has_global_resources',
    'global_resources',
    'global_resources_stub',
    'has_local_resources',
    'local_resources',
    'local_resources_stub',
    # inputs
    'inputs_stub',
    'inputs_reprs',
}

################################################################################

def update_field(dct: dict[str, object], name: str, cls: type) -> None:
    kwargs = dct.pop(name)
    dct[name] = cls(**kwargs) if is_rec(kwargs) else cls()
