import pytest
import pytest_asyncio

from typing import Callable
from agentica_internal.core import print as P
from agentica_internal.warpc.worlds.debug_world import DebugWorld, Pair, Pipe, is_virtual, is_real

__all__ = [
    'Pair',
    'Pipe',
    'pair',
    'pair_log',
    'pipe',
    'pipe_log',
    'pipe_log_virtual',
    'catcher',
    'catch',
    'is_virtual',
    'is_real',
    'P'
]

@pytest_asyncio.fixture
async def pair():
    pair = DebugWorld.connected_pair(logging=False)
    async with pair:
        yield pair

@pytest_asyncio.fixture
async def pair_log():
    pair = DebugWorld.connected_pair(logging=True)
    async with pair:
        yield pair

@pytest_asyncio.fixture
async def pipe():
    pair = DebugWorld.connected_pair(logging=False)
    async with pair:
        yield pair.B

@pytest_asyncio.fixture
async def pipe_log():
    pair = DebugWorld.connected_pair(logging=True)
    async with pair:
        yield pair.B

@pytest_asyncio.fixture
async def pipe_log_virtual():
    pair = DebugWorld.connected_pair(logging='virtual')
    async with pair:
        yield pair.B

class Catcher:

    error: BaseException | None

    def __enter__(self) -> 'Catcher':
        self.error = None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        error = exc_val
        return True

@pytest.fixture
def catcher() -> Catcher:
    return Catcher()

def catch(fn: Callable, *args, **kwargs) -> BaseException:
    err = None
    try:
        fn(*args, **kwargs)
    except BaseException as exc:
        err = exc
    assert err is not None
    return err
