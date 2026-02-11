# fmt: off

from typing import Callable

from .data.signature_compile import create_proxy_function

__all__ = [
    'create_magic_proxy_function'
]


################################################################################

def create_magic_proxy_function(src: Callable, dst: Callable):

    proxy_fn = create_proxy_function(src, dst)
    if isig := getattr(proxy_fn, '__signature__', None):
        setattr(proxy_fn, '__signature__', isig)

    return proxy_fn
