# ruff: noqa
# fmt: off

import pytest

from agentica_internal.testing.repl.delta_tests import *
from agentica_internal.testing.repl.eval_tests import *
from agentica_internal.testing.repl.fmt_tests import *
from agentica_internal.testing.repl.hook_tests import *
from agentica_internal.testing.repl.raise_tests import *
from agentica_internal.testing.repl.return_tests import *
from agentica_internal.testing.repl.summary_tests import *
from agentica_internal.testing.repl.traceback_tests import *
from agentica_internal.testing.repl.behavior_tests import *
from agentica_internal.testing.repl.stdout_tests import *


def test_delta_added():
    verify_delta_added()

def test_delta_changed():
    verify_delta_changed()

def test_delta_removed():
    verify_delta_removed()

def test_sync_exec():
    verify_sync_exec()

def test_async_exec():
    verify_async_exec()

def test_fmt_print():
    verify_fmt_print()

def test_fmt_display():
    verify_fmt_display()

def test_fmt_exception():
    verify_fmt_exception()

def test_print_hook():
    verify_print_hook()

def test_display_hook():
    verify_display_hook()

def test_exception_hook():
    verify_exception_hook()

def test_import_hook():
    verify_import_hook()

def test_explicit_raise():
    verify_explicit_raise()

def test_ignores_reraise():
    verify_ignores_reraise()

def test_return_statement():
    verify_return_statement()

def test_return_statement_nesting():
    verify_return_statement_nesting()

def test_return_variable():
    verify_return_variable()

def test_stdout_capture():
    verify_stdout_capture()

def test_return_variable_nesting():
    verify_return_variable_nesting()

def test_does_not_catch_returnexit():
    verify_does_not_catch_returnexit()

def test_run_code_summary():
    verify_run_code_summary()

def test_traceback_avoids_repl():
    verify_traceback_avoids_repl()

def test_traceback_avoids_agentica():
    verify_traceback_avoids_agentica()

def test_traceback_includes_other():
    verify_traceback_includes_other()


# Stdout capture and isolation tests

def test_basic_stdout_capture():
    verify_basic_stdout_capture()

def test_multi_print_stdout_capture():
    verify_multi_print_stdout_capture()

def test_concurrent_repl_print_isolation():
    verify_concurrent_repl_print_isolation()

def test_concurrent_repl_stdout_write_isolation():
    verify_concurrent_repl_stdout_write_isolation()

def test_many_concurrent_repls():
    verify_many_concurrent_repls()
