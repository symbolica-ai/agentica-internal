import types
from types import ModuleType
from agentica_internal.repl.repl import *
from agentica_internal.testing.examples.modules import *


class DebugModuleType(ModuleType):
    def __init__(self, name: str, exports: list[str]):
        super().__init__(name)
        self._mcount = set()
        self.__all__ = exports
        self.__file__ = "/"

    def __getattr__(self, name: str):
        mc = self._mcount
        res = name in mc
        mc.add(name)
        return res


def make_nice_module():
    def nice_func():
        return 'nice'

    def fresh_func():
        return 'fresh'

    nice_func.__module__ = 'nice'
    fresh_func.__module__ = 'nice.fresh'

    fruit = DebugModuleType('nice.fresh.fruit', ['apple'])
    fruit.apple = 'yummy'

    fresh = DebugModuleType('nice.fresh', ['fresh_bool', 'fresh_func', 'fruit'])
    fresh.fruit = fruit
    fresh.fresh_bool = True
    fresh.fresh_func = fresh_func
    assert fresh.fresh_bool == True

    nice = DebugModuleType('nice', ['nice_int', 'nice_func', 'fresh'])
    nice.nice_int = 5
    nice.nice_func = nice_func
    nice.fresh = fresh

    assert nice.nice_int == 5
    return nice


################################################################################


def _verify(code: str):
    repl = BaseRepl(logging=False)
    repl.add_modules(make_nice_module())
    repl.set_global('types', types)
    ev = repl.run_code(code)
    if out := ev.output:
        print(f"OUTPUT:\n{out}")
    if ev.error is not None:
        print(f"TRACEBACK:\n{ev.traceback_str}")
    assert ev.error is None


def verify_simple_import():
    _verify('''
    import nice
    assert nice.nice_int == 5
    assert nice.nice_func() == 'nice'
    assert nice.unicorn == False
    assert nice.unicorn == True
    assert nice.fresh.fresh_bool == True
    assert nice.fresh.fresh_func() == 'fresh'
''')


def verify_nested_import():
    _verify('''
    import nice.fresh as nf 
    assert nf.fresh_bool == True
    assert nf.fresh_func() == 'fresh'
    assert nf.unicorn == False
''')


def verify_nested_nested_import():
    _verify('''
    import nice.fresh.fruit
    assert nice.nice_func() == 'nice'
    assert nice.fresh.fresh_func() ==  'fresh'
    assert nice.fresh.fruit.apple == 'yummy'
''')


def verify_star_import():
    _verify('''
    from nice import *
    assert nice_int == 5
    assert nice_func() == 'nice'
    assert isinstance(fresh, types.ModuleType)
''')


def verify_from_import():
    _verify('''
    from nice import nice_int as n_int, nice_func as n_func
    assert n_int == 5
    assert n_func() == 'nice'
''')


def verify_sub_from_import():
    _verify('''
    from nice.fresh import fresh_bool as f_bool, fresh_func as f_func
    assert f_bool == True
    assert f_func() == 'fresh'
''')


################################################################################

if __name__ == '__main__':
    verify_simple_import()
    verify_nested_import()
    verify_nested_nested_import()
    verify_star_import()
    verify_from_import()
    verify_sub_from_import()
