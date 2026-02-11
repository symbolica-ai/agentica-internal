# fmt: off

from asyncio import Future
from ..data.signature_compile import sig_compile

from ...core.filters import to_filter_fn

from ..data.identifier import Identifier, get_fun_identifier
from ..data.signature import Signature, get_signature

from .__ import *
from .base import *

__all__ = [
    'FunctionData',
]

################################################################################

class FunctionData(ResourceData):
    __slots__ = (
        'ident', 'sig', 'isig', 'owner', 'async_mode', 'keys'
    )

    KIND = Kind.Function
    FORBIDDEN_FORM = forbidden_function

    ident:      Identifier
    sig:        Signature       # from warp
    isig:       object | None   # from inspect
    owner:      type | None
    async_mode: AsyncMode
    keys:       strtup

    @property
    def name(self) -> str:
        return self.ident.name

    # implementation attached later
    @classmethod
    def describe_resource(cls, fun: FunctionT) -> 'FunctionData': ...

    # implementation attached later
    def create_resource(self, handle: ResourceHandle) -> FunctionT: ...


################################################################################

def to_default_filter_fn(spec):
    spec = spec or flags.VIRTUAL_FUNCTION_DEFAULTS
    return to_filter_fn(spec, compact=is_compact_t, atomic=is_atom_t)

################################################################################

def describe_real_function(fun: FunctionT, defaults=None) -> FunctionData:

    from ...cpython.inspection import has_coroutine_mark

    data = FunctionData()

    data.ident = ident = get_fun_identifier(fun)

    d_filter = to_default_filter_fn(defaults)
    data.sig = sig = get_signature(fun, defaults=d_filter)
    sig.is_coro |= has_coroutine_mark(fun)

    isig = getattr(fun, '__signature__', None)
    data.isig = isig if type(isig).__module__ == 'inspect' else None

    data.owner = None  # will be set later during FunctionData.encode_fields via `.enc_owner()`.

    data.async_mode = flags.DEFAULT_ASYNC_MODE if sig.is_coro else None

    if is_forbidden(fun, ident.mod):
        raise E.WarpEncodingForbiddenError(f"<function '{ident.fullname}'> is forbidden'>")

    data.keys = tuple(fun.__dict__.keys()) if hasattr(fun, '__dict__') else ()

    return data


################################################################################

def create_virtual_function(data: FunctionData, handle: ResourceHandle) -> FunctionT:

    ident = data.ident

    name = ident.name
    handle.name = f'<{name!r} function>'
    handle.kind = Kind.Function
    handle.keys = list(data.keys)
    handle.open = False
    world_id = handle.grid[0]

    sig = data.sig
    if name == '__init__':
        # this prevents us from virtualizing 'init', which has already happened because we called '__new__' via RPC
        v_fun = sig_compile(ident, sig, 'pass', ctx=world_id, no_def=ARG_DEFAULT)
    else:
        modifier = apply_async_mode(sig, data.async_mode)
        body = f"return `HANDLE.hdlr(`HANDLE, `REQUEST(`FUNCTION, `FUNCTION_ARGS_KWARGS){modifier})"
        v_fun = sig_compile(ident, sig, body, ctx=world_id, no_def=ARG_DEFAULT,
                            HANDLE=handle, REQUEST=ResourceCallFunction)

    setattr(v_fun, VHDL, handle)

    if isig := data.isig:
        v_fun.__signature__ = isig

    return v_fun

################################################################################

# def create_virtual_method(data: FunctionData, cls_handle: ResourceHandle) -> FunctionT:
#     sig = data.sig
#     modifier = apply_async_mode(sig, data.async_mode)
#     world_id = cls_handle.grid[0]
#     body_str = f"return `HANDLE.hdlr(`HANDLE, `REQUEST(`FUNCTION, `METHOD_ARGS_KWARGS){modifier})"
#     return sig_compile(data.ident, data.sig, body_str, ctx=world_id, no_def=ARG_DEFAULT,
#                        HANDLE=cls_handle, REQUEST=ResourceCallMethod)

################################################################################

def apply_async_mode(sig: Signature, mode: AsyncMode) -> str:

    was_coro = sig.is_coro

    if mode is None:
        mode = 'sync' if not was_coro else flags.DEFAULT_ASYNC_MODE

    if mode == 'sync' and was_coro:
        mode = 'coro'

    if mode == 'future':
        annos = sig.annos
        returns = annos.get('return', Any)
        annos['return'] = Future[returns]  # type: ignore

    is_coro  = mode == 'coro'
    is_async = mode != 'sync'

    sig.is_coro = is_coro
    return f".set_async_mode('{mode}')" if is_async else ''


################################################################################

# attach definitions to class
FunctionData.describe_resource = staticmethod(describe_real_function)
FunctionData.create_resource = create_virtual_function
