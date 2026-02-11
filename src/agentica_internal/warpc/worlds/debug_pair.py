# fmt: off

from asyncio import Queue

from ...core.debug import enable_rich_tracebacks
from ...core.log import LoggingSpec, set_log_tags
from .__ import *

from .debug_pipe import Pipe

__all__ = [
    'Pair',
    'Pipe'
]


################################################################################

if TYPE_CHECKING:
    from .debug_world import DebugWorld

################################################################################


class Pair:
    a: 'DebugWorld'
    b: 'DebugWorld'

    A: Pipe
    B: Pipe

    _logging: LoggingSpec
    _tmp_file: Path | None

    def __init__(
        self,
        a_name: str = 'a',
        b_name: str = 'b',
        logging: LoggingSpec = None,
        dump_msgs: bool = False,
        **kwargs,
    ) -> None:
        from .debug_world import DebugWorld

        enable_rich_tracebacks()
        P.NOW_FORMAT = ''
        self._reset_logging = set_log_tags(logging)
        self._logging = logging
        self.a = a = DebugWorld(a_name, **kwargs)
        self.b = b = DebugWorld(b_name, **kwargs)
        self.l = logging
        self._tmp_file = None
        a.other = b
        b.other = a
        if dump_msgs:
            a_path = Path('debug_world_a.msgs').absolute()
            b_path = Path('debug_world_b.msgs').absolute()
            print(f"writing debug world msgs to:\n{a_path}\n{b_path}")
            a.write_msgs_to(a_path)
            b.write_msgs_to(b_path)
        self.A = Pipe(b, a)
        self.B = Pipe(a, b)

    @property
    def tmp_file(self) -> Path:
        from tempfile import mktemp

        if file := self._tmp_file:  # type: ignore
            return file
        self._tmp_file = file = Path(mktemp())
        return file

    @property
    def worlds(self):
        return self.a, self.b

    @property
    def pipes(self):
        return self.A, self.B

    def __call__(self, real):
        return self.B(real)

    async def __aenter__(self):
        set_log_tags(self._logging)
        a_to_b = Queue()
        b_to_a = Queue()
        self.a.start_msg_loop(a_to_b.put, b_to_a.get)
        self.b.start_msg_loop(b_to_a.put, a_to_b.get)
        return self.B

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.a.close()
        self.b.close()
        self._reset_logging()
        if file := self._tmp_file:
            file.unlink(missing_ok=True)

    def history_str(self) -> str:
        a_name = self.a.log_name
        b_name = self.b.log_name
        a_str = self.a.history_str()
        b_str = self.b.history_str()
        return f'{a_name}:\n{a_str}\n\n{b_name}:\n{b_str}'

    def print(self):
        print(self.history_str())

    def collect_events(self, events: list[Event]):
        self.a.collect_events(events)
        self.b.collect_events(events)

    @property
    def a_event(self):
        return self.a.last_event()

    @property
    def b_event(self):
        return self.b.last_event()
