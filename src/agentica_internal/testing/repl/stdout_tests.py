"""
Tests for stdout capture and isolation in the REPL.

Verifies:
1. Basic stdout capture works (single print)
2. Concurrent REPLs in threads have isolated stdout (thread-local hooks fix)
   - Tests both print() and sys.stdout.write() since both need thread-local isolation
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor

from agentica_internal.repl.repl import BaseRepl


def verify_basic_stdout_capture():
    """Verify that a single print statement is captured."""
    repl = BaseRepl()
    result = repl.run_code('print("hello world")')
    assert result.output == "hello world\n"


def verify_multi_print_stdout_capture():
    """Verify that multiple print statements are captured in order."""
    repl = BaseRepl()
    result = repl.run_code('''
print("line 1")
print("line 2")
print("line 3")
''')
    assert result.output == "line 1\nline 2\nline 3\n"


def verify_concurrent_repl_print_isolation():
    """Test that two REPLs in concurrent threads have isolated print() output.

    Uses await asyncio.sleep() to force interleaving and ensure threads actually
    run concurrently rather than sequentially.

    Tests print() which goes through builtins.print - needs thread-local hook.
    """

    def run_repl_with_prefix(prefix: str, count: int = 10) -> str:
        """Run a REPL that prints a pattern and return its output."""

        async def run():
            repl = BaseRepl()
            repl.set_loop(asyncio.get_event_loop())
            code = f'''
import asyncio
for i in range({count}):
    await asyncio.sleep(0.05)  # Force interleaving between threads
    print("{prefix}", i)
'''
            result = await repl.async_run_code(code)
            assert result.output is not None
            return result.output

        return asyncio.run(run())

    # Run two REPLs concurrently in separate threads
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(run_repl_with_prefix, "A")
        future_b = executor.submit(run_repl_with_prefix, "B")

        output_a = future_a.result()
        output_b = future_b.result()

    # Verify each output contains ONLY its own prefix
    assert "A 0" in output_a, f"Output A missing 'A 0'! Got:\n{output_a}"
    assert "A 9" in output_a, f"Output A missing 'A 9'! Got:\n{output_a}"
    assert "B" not in output_a, f"Output A contains B's output! Got:\n{output_a}"

    assert "B 0" in output_b, f"Output B missing 'B 0'! Got:\n{output_b}"
    assert "B 9" in output_b, f"Output B missing 'B 9'! Got:\n{output_b}"
    assert "A" not in output_b, f"Output B contains A's output! Got:\n{output_b}"


def verify_concurrent_repl_stdout_write_isolation():
    """Test that two REPLs in concurrent threads have isolated sys.stdout.write() output.

    Uses await asyncio.sleep() to force interleaving and ensure threads actually
    run concurrently rather than sequentially.

    Tests sys.stdout.write() which bypasses builtins.print - needs thread-local sys.stdout.
    """

    def run_repl_with_prefix(prefix: str, count: int = 10) -> str:
        """Run a REPL that prints a pattern and return its output."""

        async def run():
            repl = BaseRepl()
            repl.set_loop(asyncio.get_event_loop())
            code = f'''
import asyncio
import sys
for i in range({count}):
    await asyncio.sleep(0.05)  # Force interleaving between threads
    sys.stdout.write(f"{prefix} {{i}}\\n")
'''
            result = await repl.async_run_code(code)
            assert result.output is not None
            return result.output

        return asyncio.run(run())

    # Run two REPLs concurrently in separate threads
    with ThreadPoolExecutor(max_workers=2) as executor:
        future_a = executor.submit(run_repl_with_prefix, "A")
        future_b = executor.submit(run_repl_with_prefix, "B")

        output_a = future_a.result()
        output_b = future_b.result()

    # Verify each output contains ONLY its own prefix
    assert "A 0" in output_a, f"Output A missing 'A 0'! Got:\n{output_a}"
    assert "A 9" in output_a, f"Output A missing 'A 9'! Got:\n{output_a}"
    assert "B" not in output_a, f"Output A contains B's output! Got:\n{output_a}"

    assert "B 0" in output_b, f"Output B missing 'B 0'! Got:\n{output_b}"
    assert "B 9" in output_b, f"Output B missing 'B 9'! Got:\n{output_b}"
    assert "A" not in output_b, f"Output B contains A's output! Got:\n{output_b}"


def verify_many_concurrent_repls():
    """Stress test with many concurrent REPLs to verify complete isolation.

    Uses await asyncio.sleep() to force interleaving and ensure threads actually
    run concurrently rather than sequentially.

    Uses both print() and sys.stdout.write() to test both code paths.
    """

    def run_repl_with_id(repl_id: int) -> tuple[int, str]:
        async def run():
            repl = BaseRepl()
            repl.set_loop(asyncio.get_event_loop())
            # Alternate between print() and sys.stdout.write()
            if repl_id % 2 == 0:
                code = f'''
import asyncio
for i in range(5):
    await asyncio.sleep(0.05)
    print("REPL{repl_id}:", i)
'''
            else:
                code = f'''
import asyncio
import sys
for i in range(5):
    await asyncio.sleep(0.05)
    sys.stdout.write(f"REPL{repl_id}: {{i}}\\n")
'''
            result = await repl.async_run_code(code)
            assert result.output is not None
            return result.output

        return repl_id, asyncio.run(run())

    num_repls = 8

    with ThreadPoolExecutor(max_workers=num_repls) as executor:
        futures = [executor.submit(run_repl_with_id, i) for i in range(num_repls)]
        results = dict(f.result() for f in futures)

    # Verify each REPL's output contains only its own ID
    for repl_id, output in results.items():
        expected_marker = f"REPL{repl_id}:"
        # Should have its own output
        assert expected_marker in output, f"REPL {repl_id} missing its own output"

        # Should NOT have any other REPL's output
        for other_id in range(num_repls):
            if other_id != repl_id:
                other_marker = f"REPL{other_id}:"
                assert other_marker not in output, (
                    f"REPL {repl_id}'s output contains REPL {other_id}'s output!\n{output}"
                )


if __name__ == '__main__':
    verify_basic_stdout_capture()
    verify_multi_print_stdout_capture()
    verify_concurrent_repl_print_isolation()
    verify_concurrent_repl_stdout_write_isolation()
    verify_many_concurrent_repls()
    print("All stdout tests passed!")
