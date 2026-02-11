# fmt: off

from .__ import *

__all__ = [
    'Pipe',
    'Piped',
]


################################################################################

if TYPE_CHECKING:
    from .debug_world import DebugWorld

################################################################################

class Pipe:
    __slots__ = 'src', 'dst', 'send_event', 'recv_event'

    src: 'DebugWorld'
    dst: 'DebugWorld'

    last_event: Event
    send_event: Event
    recv_event: Event

    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

    def __call__(self, real: Any) -> 'Piped':
        return Piped(self, real)  # type: ignore

    async def send(self, real):
        await self.src.channel_send_value(real)
        if self.src.events: self.send_event = self.src.last_event()
        virtual = await self.dst.channel_recv_value()
        if self.dst.events: self.recv_event = self.dst.last_event()
        return virtual

    ############################################################################

    @property
    def last_event(self):
        return self.dst.last_event()

    @property
    def last_frame(self):
        return self.dst.last_event(OutgoingFrameExit)

    @property
    def last_rdata(self):
        return self.dst.last_event(ResourceEvent).data

    @property
    def last_piped(self):
        return self.dst.last_event(ChannelEvent).msg

    @property
    def last_msg(self):
        return self.dst.last_msg()

    ############################################################################

    @property
    def all_events(self):
        return list(self.dst.all_events())

    @property
    def all_frames(self):
        return list(self.dst.all_events(OutgoingFrameExit))

    @property
    def all_rdata(self):
        return [e.data for e in self.dst.all_events(ResourceEvent)]

    @property
    def all_piped(self):
        return [e.msg for e in self.dst.all_events(ChannelEvent)]

    @property
    def all_msgs(self):
        return list(self.dst.all_msgs())

    ############################################################################

    def pprint_events(self):
        self.dst.pprint_events()

    def print_events(self):
        self.dst.print_events()

################################################################################

class Piped(Awaitable):

    __slots__ = 'pipe', 'real', 'virt',

    def __init__(self, pipe, real):
        self.real = real
        self.pipe = pipe

    def __await__(self):
        async def send():
            if hasattr(self, 'virt'):
                return self.virt
            self.virt = virt = await self.pipe.send(self.real)
            return virt
        return send().__await__()

    def __call__(self, *args):
        assert callable(self.real)
        async def call(orig_args: tuple):
            sent_fn = await self
            sent_args = []
            for orig in orig_args:
                sent = orig
                if isinstance(orig, Piped):
                    if orig.pipe.src is self.pipe.src:
                        sent = orig.real
                    else:
                        sent = await orig
                sent_args.append(sent)
            return sent_fn(*sent_args)
        return call(args)
