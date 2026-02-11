# fmt: off

from collections.abc import Callable
from dataclasses import dataclass, field

__all__ = [
    'ReplCallableInfo',
]
from agentica_internal.cpython.function import func_annotations

################################################################################

@dataclass
class ReplCallableInfo:
    """
    Represents information about a callable value in the repl.

    warp will automatically JSON-serialize instances within REPL messages
    since they operate with `fmt=JSON`.
    """

    fun_name:     str            = ''
    fun_qualname: str            = ''
    arg_names:    list[str]      = field(default_factory=list)
    arg_annos:    dict[str, str] = field(default_factory=dict)
    ret_anno:     str | None     = None
    doc_str:      str | None     = None
    is_async:     bool           = False
    fun_stub:     str | None     = None
    args_stub:    str | None     = None

    def set_from_function(self, fun: Callable, /):

        if not callable(fun):
            return

        from ..warpc.data.identifier import get_fun_identifier
        from ..warpc.data.signature import get_signature
        from ..core.anno import anno_str

        ident = get_fun_identifier(fun)
        sig = get_signature(fun)

        self.fun_name = ident.name
        self.fun_qualname = ident.qualname
        self.doc_str = sig.doc_str
        annos = dict(func_annotations(fun))

        self.arg_names = arg_names = list(sig.pos_args + sig.key_args)
        self.arg_annos = {k: anno_str(annos[k]) if k in annos else 'Any' for k in arg_names}
        self.ret_anno = anno_str(annos['return']) if 'return' in annos else 'Any'
        self.is_async = sig.is_coro

    def __debug_info_str__(self) -> str:
        return f'name={self.fun_name!r} args={self.arg_names!r} ret={self.ret_anno!r}'

    def signature_str(self) -> str:
        f_args = ', '.join(f'{k}: {v}' for k, v in self.arg_annos.items())
        return f'({f_args})'
