from collections import defaultdict
from collections.abc import Callable
from types import CellType, FrameType, FunctionType, ModuleType
from typing import Any, Concatenate

from agentica_internal.core.data import chaindict

__all__ = [
    'mixin',
    'init_module',
    'bases',
    'module',
    'finalize',
]

MIXIN_MODULE_INIT_HOOK_NAME = '___init_submodule___'
MIXIN_MODULE_BASES = '___mixing_module_bases___'
MIXIN_MODULE_SELF = '___mixing_module_self___'


def module(caller_globals: dict[str, Any] | None = None) -> ModuleType:
    """get the current module"""
    import sys

    if caller_globals is None:
        caller_globals = sys._getframe(1).f_globals
    dct = chaindict.top(caller_globals) or caller_globals
    if MIXIN_MODULE_SELF in dct:
        return dct[MIXIN_MODULE_SELF]
    raise ValueError('No module found')


def mixin(
    mod: ModuleType,
    *,
    include: tuple[str, ...] | None = None,
    exclude: tuple[str, ...] = (),
    **init_module_kwargs: Any,
) -> None:
    """
    Mixin a module's functions into the caller's namespace.

    Notably, mixed-in functions will have the caller's module as their `__globals__`
    global namespace, meaning any overridden/redefined functions in the caller's module
    will be called by the implicitly mixed-in functions, instead of the non-overridden ones
    in the original module.

    Essentially, this gives us singleton module-level function/method inheritance.

    Example:
    ```python a.py
    def foo():
        print('a.foo')

    def bar():
        foo()
        print('a.bar')
    ```
    ```python b.py
    import a
    from a import *
    mixin(a)

    def foo():
        print('b.foo')

    if __name__ == '__main__':
        bar()
        # b.foo
        # a.bar
    ```
    Without `mixin`, `bar()` would print `a.foo` and `a.bar`.
    """
    import inspect
    import sys

    caller_frame = sys._getframe(1)
    caller_globals: dict[str, Any] = caller_frame.f_globals
    caller_mod_name: str = caller_globals['__name__']
    sub_mod = sys.modules[caller_mod_name]  # the new module that is inheriting from `mod`
    src = mod.__dict__

    _attach_self(sub_mod)
    _attach_self(mod)

    # populate bases
    _add_base(sub_mod, mod)

    if include is None:
        names = [name for name in src if name not in exclude]
    else:
        names = include

    _sentinel = object()

    def _transform(_):
        """transform the module's functions (inheritance) and run the init_module hook"""
        for name in names:
            if (override := caller_globals.get(name, _sentinel)) is not _sentinel:
                if origin := getattr(override, '__module__', None):
                    # if an object is redefined, i.e. it comes from the same module as the caller,
                    # then we don't want to override it
                    if origin == caller_mod_name:
                        # this won't happen if `mixin()` happens at the top of the module anyway
                        continue
                else:
                    # don't override if object does not have __module__
                    continue

            obj = src[name]

            if origin := getattr(obj, '__module__', None):
                if origin != mod.__name__:
                    # anything that has __module__ and is not actually from the module
                    # we're mixing in, should not be overridden.
                    continue

            if inspect.isfunction(obj):
                new_func = _rewrite_function_globals(obj, caller_globals, caller_mod_name)
                caller_globals[name] = new_func
            else:
                caller_globals[name] = obj

        # equivalent to `__init_subclass__`, but for when a module is mixin'd
        if init_module_hook := mod.__dict__.get(MIXIN_MODULE_INIT_HOOK_NAME):
            # rewrite the hook's globals so `global X` statements affect sub_mod, not mod
            rewritten_hook = _rewrite_function_globals(
                init_module_hook, caller_globals, caller_mod_name
            )
            rewritten_hook(sub_mod, **init_module_kwargs)

    finalize(_transform, caller_frame)


def init_module[**Args](
    init: Callable[Concatenate[ModuleType, Args], None],
) -> Callable[Concatenate[ModuleType, Args], None]:
    """decorator: run function as an initialization hook on module when it is mixed-in"""
    import sys

    # first, just run it on the current module with default arguments:
    mod = sys.modules[init.__module__]
    _attach_self(mod)
    no_args = lambda mod: init(mod, *(), **{})  # type: ignore[call-arg]
    finalize(no_args, sys._getframe(1))

    # then attach it to the module's __dict__ for use when the module is mixed-in:
    init.__name__ = MIXIN_MODULE_INIT_HOOK_NAME
    init.__globals__[MIXIN_MODULE_INIT_HOOK_NAME] = init
    return init


def bases(mod: ModuleType | None = None) -> tuple[ModuleType, ...]:
    """
    Get the base modules for a module.

    If `mod` is None, determines the module from the caller's globals.
    This works with mixin's globals rewriting - the caller's globals()['__name__']
    will be the child module's name, so bases() returns the right bases.
    """
    if mod is None:
        import sys

        caller_globals = sys._getframe(1).f_globals
        mod_name = caller_globals['__name__']
        mod = sys.modules[mod_name]
    if b := getattr(mod, MIXIN_MODULE_BASES, None):
        return b
    return ()


def _add_base(mod: ModuleType, base: ModuleType) -> None:
    if bases := getattr(mod, MIXIN_MODULE_BASES, None):
        if base not in bases:
            bases = (*bases, base)
        updated_bases = tuple(bases)
        setattr(mod, MIXIN_MODULE_BASES, updated_bases)
    else:
        setattr(mod, MIXIN_MODULE_BASES, (base,))


def _rewrite_function_globals(
    func: FunctionType,
    new_globals: dict[str, Any],
    caller_mod_name: str,
    _seen: dict[int, FunctionType] | None = None,
) -> FunctionType:
    """
    create a copy of `func` with `new_globals`, recursively updating any
    functions captured in its closure.
    """
    if _seen is None:
        _seen = {}

    # avoid infinite recursion for self-referential closures
    if id(func) in _seen:
        return _seen[id(func)]

    # submodule gets priority lookup over the original module
    func_globals = chaindict(new_globals, func.__globals__)

    new_closure: tuple[CellType, ...] | None = None
    if func.__closure__:
        new_cells: list[CellType] = []
        for cell in func.__closure__:
            cell_contents = cell.cell_contents
            if isinstance(cell_contents, FunctionType):
                updated_func = _rewrite_function_globals(
                    cell_contents,
                    new_globals,
                    caller_mod_name,
                    _seen,
                )
                new_cells.append(CellType(updated_func))
            else:
                new_cells.append(cell)
        new_closure = tuple(new_cells)

    new_func = FunctionType(
        code=func.__code__,
        globals=func_globals,
        name=func.__name__,
        argdefs=func.__defaults__,
        closure=new_closure,
    )
    new_func.__dict__.update(func.__dict__)
    new_func.__annotations__ = dict(getattr(func, '__annotations__', {}))
    new_func.__module__ = caller_mod_name

    _seen[id(func)] = new_func
    return new_func


def _attach_self(mod: ModuleType | dict[str, Any]) -> None:
    if isinstance(mod, ModuleType):
        if hasattr(mod, MIXIN_MODULE_SELF):
            return
        setattr(mod, MIXIN_MODULE_SELF, mod)
    else:
        import sys

        if MIXIN_MODULE_SELF in mod:
            return
        mod[MIXIN_MODULE_SELF] = sys.modules[mod['__name__']]


type FinalizeCallback = Callable[[ModuleType], None]
_DEFERRED_FINALIZE_CALLBACKS: dict[FrameType, list[FinalizeCallback]] = defaultdict(list)


def finalize(transform: FinalizeCallback, caller_frame: FrameType | None = None):
    """run code after module is loaded"""
    if caller_frame is None:
        import sys

        caller_frame = sys._getframe(1)

    callbacks = _DEFERRED_FINALIZE_CALLBACKS[caller_frame]
    if transform in callbacks:
        return
    callbacks.append(transform)

    if caller_frame.f_trace is None:
        _attach_finalize_trace(caller_frame)


def _attach_finalize_trace(caller_frame: FrameType):
    import sys

    module_globals = caller_frame.f_globals
    _attach_self(module_globals)
    mod = module(module_globals)
    old_trace = sys.gettrace()

    def local_trace(frame, event, _arg):
        if frame is not caller_frame:
            return None
        if event in ('return', 'exception'):
            # cleanup: callbacks are popped, they have been executed and are no longer needed
            for callback in _DEFERRED_FINALIZE_CALLBACKS.pop(caller_frame, []):
                callback(mod)
            sys.settrace(old_trace)
            return None
        return local_trace

    def noop_trace(_frame, _event, _arg):
        return None

    caller_frame.f_trace = local_trace
    sys.settrace(noop_trace)
