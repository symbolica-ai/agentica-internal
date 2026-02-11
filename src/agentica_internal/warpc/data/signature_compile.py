# fmt: off

from types import FunctionType
from collections.abc import Callable

from ...core.sentinels import ARG_DEFAULT
from ...cpython.function import func_compile, func_is_coro, func_mark_coro, func_set_defaults
from ...cpython.overloads import set_overloads, OverloadContext
from .identifier import Identifier, set_fun_identifier, get_fun_identifier
from .signature import Signature, get_signature


__all__ = [
    'sig_compile',
    'create_proxy_function',
]

################################################################################

_MARG = "`METHOD_ARGS_KWARGS"
_FARG = "`FUNCTION_ARGS_KWARGS"
_CALL = "`CALL"

def sig_compile(ident: Identifier, sig: Signature, body: str, *,
                ctx: OverloadContext = None, no_def=...,
                **constants) -> FunctionType:

    _marg = _farg = _call = None
    if _MARG in body: body = body.replace(_MARG, sig.forward_args_kwargs_str(skip=1))
    if _FARG in body: body = body.replace(_FARG, sig.forward_args_kwargs_str())
    if _CALL in body: body = body.replace(_CALL, sig.forward_call_str())

    fn = func_compile(sig.def_params_str(), body, **constants)
    set_fun_identifier(fn, ident)
    set_fun_signature(fn, sig, no_def)

    if sig.next_over:
        overloads = list(_compile_overloads(ident, sig, no_def))
        overloads.reverse()
        set_overloads(fn, overloads, ctx)

    return fn

################################################################################

def _compile_overloads(ident: Identifier, sig: Signature, no_def):
    while sig := sig.next_over:
        fn = func_compile(sig.def_params_str(), OVERLOAD_BODY)
        set_fun_identifier(fn, ident)
        set_fun_signature(fn, sig, no_def)
        yield fn

OVERLOAD_BODY = 'raise NotImplementedError("You should not call an overloaded function.")'

################################################################################

def set_fun_signature(fn: FunctionType, sig: Signature, no_def: object):
    defs = sig.defaults
    if defs and no_def is not ARG_DEFAULT:
        f = ARG_DEFAULT.replace_with(no_def)
        defs = {k: f(v) for k, v in defs.items()}
    func_set_defaults(fn, defs)
    fn.__doc__ = sig.doc_str
    fn.__annotations__ = sig.annos
    if sig.is_coro and not func_is_coro(fn): func_mark_coro(fn)

################################################################################

def create_proxy_function(signature_fn: Callable, actual_fn: Callable) -> FunctionType:
    sig = get_signature(signature_fn)
    ident = get_fun_identifier(signature_fn)
    return sig_compile(ident, sig, 'return `ACTUAL(`CALL)', ACTUAL=actual_fn)
