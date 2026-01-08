# fmt: off

import sys
from collections.abc import Iterable, Sequence
from importlib import import_module
from io import StringIO
from time import time_ns
from types import ModuleType
from typing import TYPE_CHECKING, Any, NoReturn

from ..core import print as P
from ..core.log import LogBase
from .repl_abc import AbstractRepl
from .repl_alias import *
from .repl_code import CompileOpts, ReplCode
from .repl_eval_data import NO_VALUE, ReplError, ReplEvaluationData, ReturnExit
from .repl_eval_info import ReplEvaluationInfo
from .repl_fmt import fmt_exception_tb, fmt_print
from .repl_hooks import SystemHooks, _delegating_stdout, original_print
from .repl_var_info import ReplVarInfo
from .repl_vars import ReplSymbols, ReplVars, sorted_list, system_builtins

__all__ = [
    'BaseRepl',
    'ReplEvaluationInfo',
    'CompileOpts',
]


################################################################################

if TYPE_CHECKING:
    from asyncio import AbstractEventLoop

################################################################################

class BaseRepl(LogBase, AbstractRepl):
    """
    This is a self-contained REPL implementation that allows for:
    1. evaluation of top level await, if an event loop is set
    2. automatic printing of the last expression of a multi-line code block
    3. handling of uncaught exceptions
    4. temporary redirection of stdin, stderr, stdout, etc. during evaluation.
    5. customization of the semantics of `import`
    6. customized stacktraces

    It maintains the most recent evaluation, and a history of past evaluations.

    The main entry point here is `.run_code`, which returns a `ReplEvaluationData`
    object with rich information about what happened.

    The hooking of (normally system-implemented) functionality instead runs:
    * `print_hook`:    to implement the replacement of `builtins.print`
    * `import_hook`:   to implement the replacement of `builtins.__import__`
    * `dir_hook`:      to implement the replacement of `builtins.dir`
    * `display_hook`:  to implement the replacement of `sys.displayhook`
    * `globals_hook`:  to implement the replacement of `globals()`
    * `locals_hook`:   to implement the replacement of `globals()`
    * `return_hook`:   run when `return XXX` occurs in executed code
    * `raise_hook`:    run when `raise XXX` occurs in executed code

    The following methods can be overridden to customize how stringification
    works:
    * `fmt_repr`
    * `fmt_print`
    * `fmt_print_arg`
    * `fmt_display_arg`
    * `fmt_traceback`

    Event-handling methods that can be specified in a subclass:
    * `on_initialized`:        after `.initialize` runs
    * `on_started`:            before a `run_code` block is executed
    * `on_finished`:           after a `run_code` block is executed
    * `on_return`:             if the code does `return XXX` or `result_var = XXX`
    * `on_uncaught_exception`: if an exception is emitted from third-party code
    * `on_raised_exception`:   if an exception is explicitly raised in the code block
    * `on_display`:            if the final statement is an expression
    * `on_import`:             when `import XXX` executes
    * `on_print`:              when `print(...)` executes

    `evaluation_finished` is called *last*, after `on_{uncaught,raised}_exception`,
    and only then is the `output` computed, which gives the other handlers a
    chance to add to the output.

    The namespace seen by executed code is managed by a `ReplVars` object, but
    actual modification and introspection should go through the methods:
      has_var, get_var, set_var, set_vars, del_var, dir_vars, clear_vars,
      hide_var, hide_vars

    These all take a`Scope` parameter that can be:
        Scope.LOCALS, Scope.GLOBALS, Scope.USER, Scope.BUILTINS
    to select which sub-namespace is affected.
    """

    last_eval:    ReplEvaluationData
    curr_eval:    ReplEvaluationData | None
    evals:        list[ReplEvaluationData]
    hooks:        SystemHooks
    options:      CompileOpts

    vars:         ReplVars
    uuid:         int
    symbols:      ReplSymbols
    __modules:    dict[str, ModuleType]
    __loop:      'AbstractEventLoop | None'
    __stream:     StringIO

    __raised:     list[BaseException]

    def __init__(self, logging: bool = False, id_name: str | None = None) -> None:

        super().__init__(logging=logging, id_name=id_name)

        self.uuid = time_ns()
        self.options = CompileOpts(
            display_fn=self.display_hook,
            raise_fn=self.raise_hook,
            return_fn=self.return_hook,
            do_not_catch=ReturnExit,
            allow_await=True
        )
        builtins = system_builtins.copy()
        builtins.update(
            __import__=self.import_hook,
            __name__='repl',
            print=self.print_hook,
            dir=self.dir_hook,
            globals=self.globals_hook,
            locals=self.locals_hook,
        )

        self.vars = ReplVars(local_vars={}, global_vars={}, builtin_vars=builtins)
        self.symbols = ReplSymbols(self.vars)

        self.__raised = []
        self.__modules = {}
        self.__loop = None
        self.__stream = stream = StringIO()
        self.__eval_stdout = None  # sys.stdout at start of evaluation, used to detect pytest redirects

        self.hooks = SystemHooks.make(
            sys.stdin, stream, stream,
            print_fn=self.print_hook,
            recursion_limit=600
        )

        self.curr_eval = None
        self.history = []

        self.__post_init__()

    def __post_init__(self):
        pass

    # --------------------------------------------------------------------------

    def initialize(self, *,
                   local_vars: Vars | None,
                   global_vars: Vars | None,
                   hidden_vars: VarKeys = ()) -> None:
        self.set_vars(LOCALS, local_vars) if local_vars else None
        self.set_vars(GLOBALS, global_vars) if global_vars else None
        self.hide_vars(hidden_vars) if hidden_vars else None
        self.on_initialize()

    def reset(self):
        self.vars.clear()
        self.clear_history()
        self.on_reset()

    def clear_history(self):
        del self.last_eval
        self.curr_eval = None
        self.history.clear()
        self.__stream.seek(0)
        self.__stream.truncate(0)

    # --------------------------------------------------------------------------

    def eval_expr(self, source: str) -> Any:
        return eval(source, self.symbols)

    # --------------------------------------------------------------------------

    def run_code(self, source: str) -> ReplEvaluationData:
        eval_data = self.__new_eval(source)
        return eval_data.eval_sync(self)

    def run_code_info(self, source: str, **options) -> ReplEvaluationInfo:
        eval_data = self.run_code(source)
        return eval_data.to_info()

    # --------------------------------------------------------------------------

    async def async_run_code(self, source: str) -> ReplEvaluationData:
        eval_data = self.__new_eval(source)
        return await eval_data.eval_async(self)

    async def async_run_code_info(self, source: str, **options) -> ReplEvaluationInfo:
        eval_data = await self.async_run_code(source)
        return eval_data.to_info()

    # --------------------------------------------------------------------------

    def __new_eval(self, source: str) -> ReplEvaluationData:
        if self.curr_eval is not None:
            raise ReplException("repl evaluation already running")
        uid = f'{len(self.history)}'
        repl_code = ReplCode.from_source(source=source, scope=self.symbols, opts=self.options, uid=uid)
        return ReplEvaluationData(repl_code)

    # --------------------------------------------------------------------------

    def get_output_pos(self) -> int:
        return self.__stream.tell()

    def get_output_since(self, pos: int) -> str:
        stream = self.__stream
        stream.seek(pos)
        output = stream.read()
        return output

    def write_output(self, text: str, flush: bool) -> None:
        self.__stream.write(text)
        self.__stream.flush() if flush else None

    # --------------------------------------------------------------------------

    # event handlers

    def on_reset(self) -> None:
        self.log('repl reset')

    def on_initialize(self) -> None:
        self.log('repl initialized for new computation')

    def on_started(self, eval_data: ReplEvaluationData, /) -> None:
        self.log('evaluation started')

    def on_finished(self, eval_data: ReplEvaluationData, /) -> None:
        self.log('evaluation finished')

    def on_print(self, eval_data: ReplEvaluationData, text: str, /) -> None:
        self.log('evaluation printed', repr(text))

    def on_return(self, eval_data: ReplEvaluationData, value: object, /) -> None:
        self.log('evaluation returned', value)

    def on_uncaught_exception(self, eval_data: ReplEvaluationData, error: ReplError, /) -> None:
        error.traceback = traceback = self.fmt_exception_tb(error.exception)
        self.write_output(traceback + '\n', True)
        self.log('evaluation threw exception', error.exception)

    def on_raised_exception(self, eval_data: ReplEvaluationData, error: ReplError, /) -> None:
        self.log('evaluation raised exception', error.exception)

    def on_display(self, eval_data: ReplEvaluationData, value: object, /) -> None:
        self.log('evaluation displayed', value)

    def on_import(self, eval_data: ReplEvaluationData, name: str, items: Sequence[str], /) -> None:
        self.log('evaluation importing', repr(name), items)

    # --------------------------------------------------------------------------

    # these are called from ReplEvaluation itself, and trigger the `on_xxx` event handlers above

    def evaluation_started(self, eval_data: ReplEvaluationData, /) -> None:
        self.curr_eval = eval_data
        # Save sys.stdout at eval start to detect pytest redirects during evaluation
        self.__eval_stdout = sys.stdout
        self.on_started(eval_data)

    def evaluation_finished(self, eval_data: ReplEvaluationData, /) -> None:
        self.__raised.clear()
        self.curr_eval = None
        self.__eval_stdout = None
        self.last_eval = eval_data
        # self.history.append(eval_data)
        self.on_finished(eval_data)

    def evaluation_returned(self, eval_data: ReplEvaluationData, value: object, /) -> None:
        self.on_return(eval_data, value)

    def evaluation_errored(self, eval_data: ReplEvaluationData, error: ReplError, /) -> None:
        error.raised = was_raised = self.__was_raised(error.exception)
        if was_raised:
            self.on_raised_exception(eval_data, error)
        else:
            self.on_uncaught_exception(eval_data, error)

    # --------------------------------------------------------------------------

    # these are called from *somewhere*, we assume because of the currently evaluating ReplEvaluation
    # there should never be more than one, because the top-level evaluation is not in an `async def`!

    def should_capture_file(self, file) -> bool:
        if file is None:
            # print() with no file argument - capture unless user redirected sys.stdout
            # during the current evaluation
            current_stdout = sys.stdout
            # If sys.stdout is still what it was when evaluation started, capture
            # This handles pytest capture (sys.stdout is pytest's capture at eval start)
            if self.__eval_stdout is not None and current_stdout is self.__eval_stdout:
                return True
            # Also capture if sys.stdout is our delegating wrapper or our stream
            if current_stdout is _delegating_stdout or current_stdout is self.__stream:
                return True
            # User redirected sys.stdout to something else (e.g., StringIO), honor that
            return False
        return file is sys_stdout or file is sys_stderr or file is self.__stream

    def print_hook(self, *args, sep: str = ' ', end='\n', file=None, flush: bool = False) -> None:
        curr_eval = self.curr_eval
        if curr_eval is None:
            return
        if self.should_capture_file(file):
            text = self.fmt_print(args, sep, end)
            self.on_print(curr_eval, text)
            self.write_output(text, flush)
        else:
            # if sys.stdout is redirected during execution, we fallback on the *system* print for
            # compatibility
            builtin_print(*args, sep=sep, end=end, file=file, flush=flush)

    def display_hook(self, value: Any, /) -> None:
        curr_eval = self.curr_eval
        if curr_eval is None:
            return
        curr_eval.out_value = value
        if value is not None:
            self.on_display(curr_eval, value)
            displayed = self.fmt_display_arg(value)
            curr_eval.out_str = displayed
            self.write_output(displayed + '\n', True)

    def import_hook(self, name: str,
                    globals_: Vars | None = None,
                    locals_: Vars | None = None,
                    fromlist: Sequence[str] = (),
                    level: int = 0) -> ModuleType:
        curr_eval = self.curr_eval
        if curr_eval is None or not isinstance(globals_, ReplSymbols):
            return __import__(name, globals=globals_, locals=locals_, fromlist=fromlist, level=level)
        self.on_import(curr_eval, name, fromlist)
        set_global = self.set_global
        module = self.get_module(name)
        if not fromlist:
            root = name.split('.', 1)[0]
            module = self.get_module(root)
            set_global(root, module)
        # else:
        #     for name in fromlist:
        #         set_global(name, getattr(module, name))
        return module

    def dir_hook(self, arg: object = NO_VALUE) -> list[str]:
        return self.vars.dir_user() if arg is NO_VALUE else builtin_dir(arg)

    def globals_hook(self) -> Vars:
        return self.vars.globals

    def locals_hook(self) -> Vars:
        return self.vars.locals

    def return_hook(self, value: object, /) -> NoReturn:
        # a `return XXX` is transformed into a `return_hook(XXX)`
        # also, `result = XXX` is similarly transformed into `result = return_hook(XXX)`
        # ReplEvaluation will silently ignore a `ReturnExit`
        self.curr_eval.return_value = value
        raise ReturnExit() from None

    def raise_hook(self, exception: BaseException, /) -> BaseException:
        # a syntactic `raise XXX` will turn into a `raise repl.raise_hook(XXX)`,
        # so we add this to a list (reset after each eval), and repl evaluation
        # can ask if is this was in the raised list.
        self.__raised.append(exception)
        return exception

    def __was_raised(self, exception: BaseException, /) -> bool:
        for exc in self.__raised:
            if exc is exception:
                return True
        return False

    ############################################################################

    def set_recursion_limit(self, rec_limit: int, /) -> None:
        self.hooks.recursion_limit = rec_limit

    def set_local(self, name: str, value: object, /) -> None:
        self.vars.set_local(name, value)

    def set_global(self, name: str, value: object, /) -> None:
        self.vars.set_global(name, value)

    def update_globals(self, dct: Vars):
        self.vars.update_globals(dct)

    def update_locals(self, dct: Vars):
        self.vars.update_locals(dct)

    def hide_var(self, key: str) -> None:
        self.vars.hide((key,))

    def hide_vars(self, keys: Iterable[str]) -> None:
        self.vars.hide(keys)

    def dir_global(self) -> list[str]:
        return self.vars.dir_global()

    def dir_local(self) -> list[str]:
        return self.vars.dir_local()

    def dir_user(self) -> list[str]:
        return self.vars.dir_user()

    # --------------------------------------------------------------------------

    def get_module(self, name: str) -> ModuleType:
        if self.curr_eval:
            imported = self.curr_eval.imported
            if name not in imported:
                imported.append(name)
        modules = self.__modules
        if module := modules.get(name):
            return module
        modules[name] = module = self.load_module(name)
        return module

    def add_modules(self, *modules: ModuleType) -> None:
        for module in modules:
            self.__modules[module.__name__] = module

    def load_module(self, name: str) -> ModuleType:
        self.log(f"load_module: {name}")
        return import_module(name)

    def allowed_modules(self) -> list[str]:
        return ALL_SYSTEM_MODULES

    def preload_modules(self, modules: Iterable[ModuleType]) -> None:
        _modules = self.__modules
        _globals = self.vars.globals
        for module in modules:
            name = module.__name__
            assert '.' not in name, 'can only preload root modules'
            _modules[name] = module   # ensures import 'foo' will use this module
            _globals[name] = module   # makes the module name available

    # --------------------------------------------------------------------------

    def get_loop(self) -> 'AbstractEventLoop | None':
        return self.__loop

    def set_loop(self, loop: 'AbstractEventLoop | None') -> None:
        self.log("loop set to", loop)
        self.__loop = loop

    ############################################################################

    # formatting: override these methods

    def fmt_exception_tb(self, exc: BaseException, /) -> str:
        return fmt_exception_tb(exc)

    def fmt_print(self, args: tuple[object, ...], sep: str, end: str) -> str:
        return fmt_print(args, sep, end, self.fmt_print_arg)

    def fmt_print_arg(self, value: Any, /) -> str:
        return str(value)

    def fmt_display_arg(self, value: Any, /) -> str:
        return self.fmt_repr(value)

    def fmt_repr(self, value: Any, /) -> str:
        return repr(value)

    ############################################################################

    # for debugging

    def console_lines(self) -> Iterable[str]:
        for i, eval_data in enumerate(self.history):
            if i:
                yield ''
            yield from eval_data.console_lines()

    def console_str(self) -> str:
        return '\n'.join(self.console_lines())

    def console_print(self) -> None:
        print(self.console_str())

    def print_history(self):
        P.hprint('REPL HISTORY:\n')
        for item in self.history:
            item.print()
        P.hdiv()

    def print_variables(self):
        P.hprint('REPL VARIABLES:\n')
        self.vars.pprint()
        P.hdiv()

    ############################################################################

    # AbstractRepl implementation of vars

    def __contains__(self, key: str) -> bool:
        return key in self.symbols

    def __getitem__(self, key: str) -> object:
        return self.symbols[key]

    def var_info(self, scope: Scope, key: str, /) -> ReplVarInfo | None:
        try:
            val = self.get_scope(scope).get(key, NO_VALUE)
            return None if val is NO_VALUE else ReplVarInfo.from_value(val)
        except:
            return None

    def get_var(self, scope: Scope, key: str, /) -> Any:
        return self.get_scope(scope)[key]

    def set_var(self, scope: Scope, key: str, val: Any, /) -> Any:
        self.get_scope(scope)[key] = val

    def has_var(self, scope: Scope, key: str) -> bool:
        if scope == HIDDEN:
            return key in self.vars.hidden
        return key in self.get_scope(scope)

    def del_var(self, scope: Scope, key: str) -> None:
        del self.get_scope(scope)[key]

    def dir_vars(self, scope: Scope, /) -> list[str]:
        if scope == HIDDEN:
            return sorted_list(self.vars.hidden)
        lst = list(self.get_scope(scope).keys())
        lst.sort()
        return lst

    def clear_vars(self, scope: Scope, /) -> None:
        if scope == HIDDEN:
            self.vars.hidden.clear()
        else:
            self.get_scope(scope).clear()

    def set_vars(self, scope: Scope, rec: Vars) -> None:
        self.get_scope(scope).update(rec)

    def get_scope(self, scope: Scope) -> Vars:
        if scope == LOCALS:
            return self.vars.locals
        elif scope == GLOBALS:
            return self.vars.globals
        elif scope == BUILTINS:
            return self.vars.builtins
        elif scope == USER:
            return self.symbols
        else:
            raise ReplException(f"invalid scope: {scope}")

    ############################################################################

    def get_last_exception(self) -> BaseException:
        self.log('get_last_exception')
        if not hasattr(self, 'last_eval'):
            raise ReplException('no evaluation to get the exception of')
        last_eval = self.last_eval
        if last_eval.error is None:
            raise ReplException('last evaluation did not have an exception')
        last_exception = last_eval.error.exception
        assert isinstance(last_exception, BaseException)
        return last_exception

    def get_last_return_value(self) -> object:
        self.log('get_last_return_value')
        if not hasattr(self, 'last_eval'):
            raise ReplException('no evaluation to get the exception of')
        last_eval = self.last_eval
        if last_eval is None:
            raise ReplException('no evaluation to get the return value of')
        return_value = last_eval.return_value
        if return_value is NO_VALUE:
            raise ReplException('last evaluation did not have a return value')
        return return_value

################################################################################

def all_system_modules() -> list[str]:
    known = set()
    known |= sys.stdlib_module_names
    known |= set(sys.builtin_module_names)
    known = list(known)
    known.sort()
    return known

ALL_SYSTEM_MODULES = all_system_modules()

builtin_dir = dir
# Use the original print function, not the thread-local wrapper that was installed
# by repl_hooks.py. This prevents infinite recursion in print_hook's fallback path.
builtin_print = original_print
# Use the thread-local wrappers for identity comparison in should_capture_file
sys_stdout = sys.stdout
sys_stderr = sys.stderr
