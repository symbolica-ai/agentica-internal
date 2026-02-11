# fmt: off

from typing import NoReturn, TYPE_CHECKING

if TYPE_CHECKING:
    from .msg.term_resource import UserResourceMsg

__all__ = [
    'WarpError',
    'WarpFrameError',
    'WarpResourceError',
    'WarpProtocolError',
    'WarpCodecError',
    'WarpEncodingForbiddenError',
    'WarpAsyncError',
    'WarpRoleConfusionError',
    'WarpEncodingError',
    'WarpDecodingError',
    'WarpLambdaEncodingError',
    'WarpLambdaDecodingError',
    'WarpShutdown',
    'RemoteException',
    'ForbiddenError',
    'raise_shutdown',
    'REM_EXC_CLS_MSG'
]

################################################################################

class WarpError(BaseException): ...
class WarpFrameError(WarpError): ...
class WarpResourceError(WarpError): ...
class WarpProtocolError(WarpError): ...
class WarpCodecError(WarpError): ...
class WarpEncodingError(WarpCodecError): ...
class WarpDecodingError(WarpCodecError): ...
class WarpEncodingForbiddenError(WarpEncodingError): ...
class WarpAsyncError(WarpEncodingError): ...

class WarpRoleConfusionError(WarpProtocolError):
    """WarpRoleConfusion is raised when an operation is applied to the wrong kind of thing."""

class WarpShutdown(WarpError):
    """
    WarpShutdown is raised inside the python implementation of WasmRunner when a guest thread tries
    to do RPC but the host WasmRunner has been shut down. This terminates the stack that the RPC
    occurred in.
    """

class WarpLambdaEncodingError(WarpEncodingError): ...
class WarpLambdaDecodingError(WarpDecodingError): ...

################################################################################

class RemoteException(RuntimeError):

    if TYPE_CHECKING:
        ___remote_exception_class_msg___: UserResourceMsg

REM_EXC_CLS_MSG = '___remote_exception_class_msg___'

################################################################################

class ForbiddenError(RuntimeError): ...

# this is so that warp allows its encoding
# it is also registered in `warpc.system` so it has an SID
RemoteException.__module__ = 'builtins'
ForbiddenError.__module__ = 'builtins'

################################################################################

def raise_shutdown(*args, **kwargs) -> NoReturn:
    raise WarpShutdown()
