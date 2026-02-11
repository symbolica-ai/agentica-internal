# fmt: off

from sys import modules as sys_modules
from types import ModuleType, FunctionType
from typing import Any
from collections import defaultdict
from collections.abc import Callable

from agentica_internal.core.fmt import f_signature

__all__ = [
    'runs',
    'raises',
    'invalid',
    'set_checks',
    'get_function_checks',
    'get_module_functions',
]

################################################################################

type Args = tuple[Any, ...]
type Kwargs = dict[str, Any] | None
type ExcClass = BaseException

class FunCheck:

    def attach(self, fun: Callable):
        assert isinstance(fun, FunctionType)
        checks = FUN_CHECKS.get(fun)
        if checks is None:
            MOD_FUNS[fun.__module__].append(fun)
            FUN_CHECKS[fun] = checks = FunChecks(fun)
        checks.append(self)

    # makes this a decorator
    def __call__[C: Callable](self, fun: C) -> C:
        self.attach(fun)
        return fun

    def apply(self, fun: Callable) -> Any:
        pass

    def compare(self, fun_1: FunctionType, fun_2: FunctionType) -> None:
        pass


class FunRunsCheck(FunCheck):
    args:    Args
    kwargs:  Kwargs

    def __init__(self, args: Args, kwargs: Kwargs) -> None:
        self.args = args
        self.kwargs = kwargs

    def apply(self, fun: FunctionType) -> Any:
        try:
            return fun(*self.args, **self.kwargs)
        except BaseException as e:
            raise self.assertion(fun, f'$ raised {type(e).__name__}: {e}')

    def compare(self, fun_1: FunctionType, fun_2: FunctionType) -> None:
        res_1 = self.apply(fun_1)
        res_2 = self.apply(fun_2)
        if res_1 != res_2:
            raise self.assertion(fun_2, "$ gave different output")

    def assertion(self, fun: FunctionType, msg: str) -> AssertionError:
        from agentica_internal.core.fmt import f_function_call
        msg = msg.replace('$', f_function_call(fun, self.args, self.kwargs))
        err = AssertionError(msg)
        code = fun.__code__
        err.add_note(f'  File "{code.co_filename}", line {code.co_firstlineno}')
        return err


class FunRaisesCheck(FunRunsCheck):
    ename: type[BaseException]

    def __init__(self, ename: str, args: Args, kwargs: Kwargs) -> None:
        super().__init__(args, kwargs)
        self.ename = ename

    def compare(self, fun_1: FunctionType, fun_2: FunctionType) -> None:
        res_1 = self.apply(fun_1)
        res_2 = self.apply(fun_2)
        if str(res_1) != str(res_2):
            raise self.assertion(fun_2, f"$ gave different exception message:\n{res_1}\n{res_2}")

    def apply(self, fun: FunctionType) -> BaseException:
        ename = self.ename
        exc = None
        try:
            fun(*self.args, **self.kwargs)
        except BaseException as e:
            exc = e
        if exc is None:
            raise self.assertion(fun, f'$ completed without raising {ename}')
        aname = type(exc).__name__
        if aname != ename:
            raise self.assertion(fun, f'$ raised {aname} instead of {ename}: {exc}')
        return exc

################################################################################

def runs(*args, **kwargs) -> FunRunsCheck:
    return FunRunsCheck(args, kwargs)

def invalid(*args, **kwargs) -> FunRaisesCheck:
    return FunRaisesCheck('TypeError', args, kwargs)

def raises(exc_cls: ExcClass, *args, **kwargs) -> FunRaisesCheck:
    return FunRaisesCheck(exc_cls.__name__, args, kwargs)

def set_checks(fun: Callable | tuple[Callable, ...], *checks: FunCheck):
    if type(fun) is not tuple: fun = fun,
    for f in fun:
        for check in checks:
            check.attach(f)

################################################################################

def get_function_checks(fun: Callable) -> 'FunChecks':
    assert isinstance(fun, FunctionType)
    assert fun in FUN_CHECKS
    return FUN_CHECKS[fun]

################################################################################

class FunChecks(list[FunCheck]):

    def __init__(self, fun):
        self.fun = fun
        super().__init__()

    def apply(self) -> None:
        fun = self.fun
        for check in self:
            check.apply(fun)

    def compare(self, fun_2: FunctionType) -> None:
        fun_1 = self.fun
        compare_defs(fun_1.__defaults__,   fun_2.__defaults__)
        compare_defs(fun_1.__kwdefaults__, fun_2.__kwdefaults__)
        for check in self:
            check.compare(fun_1, fun_2)
        sig_1 = f_signature(fun_1)
        sig_2 = f_signature(fun_2)
        if sig_1 != sig_2:
            raise AssertionError(f"Signatures differ:\n{sig_1}\n{sig_2}")

def compare_defs(d1, d2):
    assert type(d2) is type(d1), f"defaults types differ: {d1} {d2}"
    if type(d1) in (tuple, list, dict, set):
        assert len(d1) == len(d2), f"default lens differ: {d1} {d2}"

################################################################################


FUN_CHECKS: dict[FunctionType, FunChecks] = {}
MOD_FUNS = defaultdict[str, list[FunctionType]](list)

def get_module_functions(mod: ModuleType | str) -> list[FunctionType]:
    if isinstance(mod, ModuleType):
        mod_obj = mod
        mod = mod.__name__
    else:
        mod_obj = sys_modules[mod]

    assert isinstance(mod, str)
    lst = MOD_FUNS[mod]
    lst.sort(key=fn_line)

    to_name = {
        id(v): k for k, v in mod_obj.__dict__.items()
        if type(v) is FunctionType
    }
    for f in lst:
        if id(f) in to_name:
            f.__name__ = f.__qualname__ = to_name[id(f)]
    return lst

def fn_line(f: FunctionType) -> int:
    return f.__code__.co_firstlineno
