# fmt: off

import asyncio
import re
import numpy
import _sqlite3
import math

from typing import Callable

from agentica_internal.warpc.data.signature_utils import sig_of_c_function, NO_DEFAULTS

unbound_finditer = re.Pattern.finditer
bound_finditer = re.compile(" X+ ").finditer

bound_search = iter(bound_finditer("X XX XXX")).__reduce__()[1][0]  # <_sre.SRE_Scanner>.search
unbound_search = type(bound_search.__self__).search

bytes_fromhex = bytes.__dict__['fromhex']

# copied from core.type:
# | UnboundMethodC       | MethodDescriptorType      | `bytes.hex`                |
# | UnboundDunderMethodC | WrapperDescriptorType     | `list.__init__`            |
# | BoundDunderMethodC   | MethodWrapperType         | `[].__len__`               |
# | BoundClassMethodC    | ClassMethodDescriptorType | `bytes.__dict__['fromhex']' |
# | BoundMethodOrFuncC   | BuiltinFunctionType       | `len`                      |
# | BoundMethodOrFuncC   | BuiltinMethodType         | `[].append`                |
# | BoundMethodC         |                           | `re.compile('').finditer`  |

CFUNC_SIG_PAIRS = [

    # UnboundDunderMethodC:
    (object.__init__,  "(self, /)"),
    (object.__hash__,  "(self, /)"),

    # BoundDunderMethodC:
    ([].__len__,       "()"),

    # UnboundMethodC:
    (unbound_finditer, "(self, /, string, pos=..., endpos=...)"),
    (unbound_search,   "(self, /)"),
    (list.append,      "(self, object, /)"),
    (dict.__setitem__, "(self, key, value, /)"),

    # BoundMethodC:
    (bound_finditer,   "(string, pos=..., endpos=...)"),
    (bound_search,     "()"),

    # BoundClassMethodC:
    (bytes_fromhex,    "(type, string, /)"),

    # BoundMethodOrFuncC:
    (object.__new__,  "(type, *args, **kwargs)"),
    (numpy.array,     "(object, dtype=..., *, copy=..., order=..., subok=..., ndmin=..., ndmax=..., like=...)"),
    (len,             "(obj, /)"),
    ([].append,       "(object, /)"),

    # BoundMethodOrFuncC:
    (math.sqrt, "(x, /)"),
    (_sqlite3.register_adapter, "(type, adapter, /)")
]

def verify_cfunc_sig(pair: tuple[Callable, str]):
    func, e_sig_str = pair
    sig = sig_of_c_function(func, 0, NO_DEFAULTS)
    a_sig_str = sig.sig_str()
    assert a_sig_str == e_sig_str, f'{func} sig mismatch: {a_sig_str} != {e_sig_str}'

async def verify_cfunc_sigs():
    for pair in CFUNC_SIG_PAIRS:
        verify_cfunc_sig(pair)

if __name__ == '__main__':
    asyncio.run(verify_cfunc_sigs())
