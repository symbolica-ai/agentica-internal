# fmt: off

import asyncio

from .__ import *
from .base import *

__all__ = [
    'FutureData',
    'unregister_virtual_future'
]
from ...core.futures import HookableFuture


################################################################################

type FutureHandler = Callable[[FutureT], Any]

class FutureData(ResourceData):
    __slots__ = 'future', 'result'

    KIND = Kind.Future
    future: FutureT  # the existing real / novel virtual future created by `id_to_future`
    result: Result   # value/exception if done, PENDING_RESULT / CANCELED_RESULT if not

    # NOTE: this is pretty trivial, the reason is that the special sauce is
    # applied when a FutureData is *encoded* to a FutureDataMsg, and conversely
    # a FutureDataMsg is *decoded* to a FutureData. See FutureDataMsg in
    # `warpc.msg.resource_data` for that code.
    #
    # * during *encoding*, the future is registered with the owning world via
    # `frame.future_to_id`, which cooks up a future_id for it and attaches a
    # done_callback which will send events against this future_id.
    #
    # * during *decoding*, that future_id is passed to `frame.id_to_future` to create
    # matched local future which will respond to incoming `FutureEventMsgs` against
    # this future_id. This will be a HookableFuture to ensure that awaits and cancels
    # work correctly.
    #
    # see encode_fields and decode_fields in FutureDataMsg for where this happens

    @classmethod
    def describe_resource(cls, future: asyncio.Future) -> 'FutureData':
        data = FutureData()
        data.future = future
        data.result = Result.from_future(future)
        return data

    def create_resource(self, handle: ResourceHandle) -> FutureT:
        # this code ensures that the future behaves like a virtual resource,
        # triggering RPC when it is cancelled *locally*, the other code path, in
        # which it is set or cancelled via events received from the remote world,
        # happens because FutureDataMsg.decode_fields called `future_from_id` to
        # fill `data.future`
        future = self.future
        result = self.result
        handle.kind = Kind.Future
        setattr(future, VHDL, handle)
        result.into_future(future)  # no effect if result is pending
        register_virtual_future(future)
        return future

################################################################################

# this is only called by create_resource above!
def register_virtual_future(future: FutureT) -> None:

    if isinstance(future, HookableFuture):
        future.___set_hooks___(
            cancel_hook=send_future_cancel,
            set_result_hook=send_future_result,
            set_exception_hook=send_future_exception,
        )

# this should be called to DISABLE the triggering of RPC when a virtual future
# is canceled. it is called by `send_future_request`, but ALSO by a Frame when it
# receives a future event and sets the virtual future's outcome to match what
# happened with the remote future, to avoid the close event from triggering RPC.
def unregister_virtual_future(future: FutureT) -> None:

    if isinstance(future, HookableFuture):
        future.___del_hooks___()

# these functions allow *local* calls to .set_result, etc. for a matched future
# to trigger messages that will cancel/set the original future via a *framed*
# ResourceRequest using the same 'handle @' mechanism used for other virtual
# resources.
def send_future_cancel(future: asyncio.Future, _: None) -> None:

    unregister_virtual_future(future)

    if handle := get_handle(future):
        event = CancelFuture(future)
        handle.hdlr(handle, event)


def send_future_result(future: asyncio.Future, result: Any) -> None:

    unregister_virtual_future(future)

    if handle := get_handle(future):
        event = CompleteFuture(future, Result.good(result))
        handle.hdlr(handle, event)


def send_future_exception(future: asyncio.Future, exception: BaseException) -> None:

    unregister_virtual_future(future)

    if handle := get_handle(future):
        event = CompleteFuture(future, Result.bad(exception))
        handle.hdlr(handle, event)
