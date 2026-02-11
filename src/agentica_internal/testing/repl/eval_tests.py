import asyncio

from agentica_internal.repl.repl import *


def verify_sync_exec():
    repl = BaseRepl()
    ev = repl.run_code('''
    x = 1 + 1
    ''')
    assert not ev.error
    assert repl.vars.locals['x'] == 2


def verify_async_exec():
    repl = BaseRepl()
    loop = asyncio.new_event_loop()
    repl.set_loop(loop)
    ev = repl.run_code('''
    import asyncio
    await asyncio.sleep(0.1)
    ''')
    assert not ev.error
    assert 0.1 < ev.duration < 0.2


def verify_class_enclosing_scope_access():
    repl = BaseRepl(logging=True)
    ev = repl.run_code('''
    MY_DEFAULT = 100
    
    class Test2:
        value: int = MY_DEFAULT    
    ''')


if __name__ == '__main__':
    verify_sync_exec()
    verify_async_exec()
    verify_class_enclosing_scope_access()
