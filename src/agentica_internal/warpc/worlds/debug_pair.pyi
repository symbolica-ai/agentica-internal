# fmt: off

from pathlib import Path

from ...core.log import LoggingSpec
from ..events import Event
from .debug_world import DebugWorld
from .debug_pipe import Pipe

__all__ = [
    'Pair',
    'Pipe'
]

################################################################################

class Pair:
    a: DebugWorld
    b: DebugWorld

    A: Pipe
    B: Pipe

    def __init__(self,
                 a_name: str = 'a',
                 b_name: str = 'b',
                 logging: LoggingSpec = None,
                 dump_msgs: bool = False,
                 **kwargs) -> None:
        ...

    @property
    def tmp_file(self) -> Path: ...

    @property
    def worlds(self) -> tuple[DebugWorld, DebugWorld]: ...

    @property
    def pipes(self) -> tuple[Pipe, Pipe]: ...

    async def __aenter__(self) -> Pipe: ...

    async def __aexit__(self, exc_type, exc_val, exc_tb): ...

    def history_str(self) -> str: ...

    def print(self) -> None: ...

    def collect_events(self, events: list[Event]): ...

    @property
    def a_event(self) -> Event: ...

    @property
    def b_event(self) -> Event: ...
