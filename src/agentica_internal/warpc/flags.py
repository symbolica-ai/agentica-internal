# fmt: off

from contextlib import contextmanager
from typing import Literal, TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


__all__ = ['with_flags']


# ------------------------------------------------------------------------------

# do we patch TermMsg to support old-style inline DefinitionMsg?
INLINE_DEFINITIONS: bool = True

# do we virtualize v_cls.xxx when xxx is not a known key?
CLASS_OPEN_KEYS: bool = False

# do we serialize information about properties/descriptors or rely on
# open keys instead?
CLASS_PROPERTIES: bool = True

# when an async mode is not specified for a function, what mode should be used?
DEFAULT_ASYNC_MODE: Literal['coro', 'future', 'sync'] = 'future'

# do we virtualize v_obj.xxx when xxx is not a known key?
OBJECT_OPEN_KEYS: bool = True

# do we virtualize lambda functions so they are pass-by-value?
VIRTUAL_LAMBDAS: bool = True

# do we serialize virtual function defaults or just use ARG_DEFAULT placeholder?
VIRTUAL_FUNCTION_DEFAULTS: Literal['all', 'atomic', 'compact', 'none'] = 'compact'

# do we virtualize instances of ModuleType?
VIRTUAL_MODULES: bool = True

# do we virtualize objects that are a known, system generator or iterator?
VIRTUAL_ITERATORS: bool = True

# do we virtualize instances of asyncio.Future?
VIRTUAL_FUTURES: bool = True

# do we virtualize instances of CoroutineType?
VIRTUAL_COROUTINES: bool = True

# do we virtualize non-system exceptions?
VIRTUAL_EXCEPTIONS: bool = True

# is v_obj.__setattr__ and v_obj.__delattr__ virtualized?
VIRTUAL_OBJECT_MUTATION: bool = True
VIRTUAL_OBJECT_DUNDER_DICT: bool = True

# is v_cls.foo where foo in v_cls_data.keys implemented via property object?
VIRTUAL_CLASS_ATTRIBUTES: bool = True

# do we allow str(v_obj), hash(v_obj) etc to be intercepted before causing RPC?
VIRTUAL_RESOURCE_REQUEST_HOOKS: bool = True

# do we look at real_resource.___warp_as___() and ___class_warp_as___ when serializing resources?
RESPECT_WARP_AS: bool = True

# do we avoid virtualizing fields/methods starting with _?
OMIT_PRIVATE_FIELDS: bool = True

# do we avoid virtualizing annotations starting with _?
OMIT_PRIVATE_ANNOS: bool = True

# do we whitelist known dunder methods like __contains__?
ALLOW_KNOWN_DUNDER_METHODS: bool = True

# do we reduce non-realized builtin iterator instances to pass them by value?
REALIZE_ITERATOR_LIMIT: int = 4

# do we actually believe the defaults claimed by __text_signature__ C functions?
BELIEVE_TEXT_SIGNATURE_DEFAULTS: bool = False

# TODO: describe
TYPE_ERASE_ENUMS: bool = True

# do we produce 5 instead of NumberMsg(5), etc?
INLINE_ATOMS: list[type] = []

# if we allow decoding of inline files (back to Paths), where should they go?
INLINE_FILE_DIRECTORY: 'Path | None' = None

# do we capture basic info from the top of the stack when a VRR occurs? good for debugging
SEND_VIRTUAL_REQUEST_ORIGIN: bool = True

# ------------------------------------------------------------------------------

def get_flags():
    g = globals()
    dct = {}
    for k, v in g.items():
        if '_' in k and k[0].isupper():
            dct[k] = v
    return dct

def set_flags(flags: dict):
    g = globals()
    for k, v in flags.items():
        g[k] = v

@contextmanager
def with_flags(**kwargs):
    old = get_flags()
    set_flags(kwargs)
    yield
    set_flags(old)
