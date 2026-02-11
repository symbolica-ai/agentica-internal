# fmt: off

from types import FunctionType
from collections.abc import Iterable as Iter, Callable

from ...core.debug import fmt_exception
from ...core.fmt import f_anno, f_argument_fn
from ...core.strs import forward_args_str, forward_kwargs_str, forward_call_str, def_params_str
from ...core.sentinels import ARG_DEFAULT
from ...core.filters import FilterFn, ALL as ALL_DEFAULTS, NONE as NO_DEFAULTS

from ..alias import strtup, optstr
from ..kinds import AnnotationsT, AttributesT

from .base import EncodableData

__all__ = [
    'Signature',
    'ALL_DEFAULTS',
    'NO_DEFAULTS',
]


################################################################################

class Signature(EncodableData):

    __debug_fmt_str__ = '⟨{info}⟩'
    __debug_fmt_slots__ = False

    __slots__ = (
        'pos_args', 'key_args', 'pos_star', 'key_star', 'pos_only',
        'optional', 'defaults', 'annos', 'doc_str', 'is_coro', 'is_cext', 'next_over', 'num_args'
    )

    STR_KEYS = REPR_KEYS = True

    pos_args: strtup
    key_args: strtup
    pos_star: optstr
    key_star: optstr
    pos_only: int
    num_args: int

    optional: set[str]
    defaults: AttributesT
    annos:    AnnotationsT
    doc_str:  optstr

    is_coro:  bool
    is_cext:  bool

    next_over: 'Signature | None'

    def __init__(self, *,
                 pos_args=(), key_args=(), pos_star=None, key_star=None, pos_only=0,
                 optional=(), defaults=None, annos=None, doc_str=None,
                 is_coro=False, is_cext=False, next_over=None):
        self.pos_args = pos_args
        self.key_args = key_args
        self.pos_star = pos_star
        self.key_star = key_star
        self.pos_only = pos_only
        self.annos = {} if annos is None else annos
        self.defaults = dict.fromkeys(optional, ARG_DEFAULT)
        self.optional = set(optional)
        if defaults:
            self.defaults.update(defaults)
            self.optional.update(defaults)
        self.is_coro = is_coro
        self.is_cext = is_cext
        self.doc_str = doc_str
        self.next_over = next_over
        self.num_args = len(pos_args) + len(key_args) + bool(pos_star) + bool(key_star)

    def __str__(self) -> str:
        return self.sig_str()

    def __contains__(self, name: str) -> bool:
        return name in self.pos_args or name in self.key_args or name == self.pos_star or name == self.key_star

    def __debug_info_str__(self) -> str:
        return self.sig_str('; ') + ';'

    @property
    def is_optional(self) -> Callable[[str], bool]:
        return self.optional.__contains__

    @property
    def fixed_args(self) -> strtup:
        return self.pos_args + self.key_args

    @property
    def pos_or_key_args(self) -> strtup:
        return self.pos_args[self.pos_only:]

    def overloads(self) -> Iter['Signature']:
        sig = self
        while sig := sig.next_over:
            yield sig

    ################################################################################

    def sig_str(self, over_sep: str = '\n') -> str:
        f_arg = f_argument_fn(self.annos, self.defaults)
        f_params = def_params_str(self.pos_args, self.key_args, self.pos_star, self.key_star, self.pos_only, f_arg)
        s = f'({f_params})'
        if over := self.next_over:
            f_over = over.sig_str()
            s = f'{f_over}{over_sep}{s}'
        if 'return' in self.annos:
            f_ret = f_anno(self.annos['return'])
            s = f'{s} -> {f_ret}'
        return s

    def def_params_str(self) -> str:
        if not self.num_args: return ''
        defs = self.defaults
        wrap = lambda k: f'{k}=...' if k in defs else k
        return def_params_str(self.pos_args, self.key_args, self.pos_star, self.key_star, self.pos_only, wrap)

    def forward_call_str(self) -> str:
        if not self.num_args: return ''
        return forward_call_str(self.pos_args, self.key_args, self.pos_star, self.key_star)

    def forward_args_str(self, skip: int = 0) -> str:
        if not self.num_args: return '()'
        return forward_args_str(self.pos_args[skip:], self.pos_star)

    def forward_kwargs_str(self) -> str:
        if not self.num_args: return '{}'
        return forward_kwargs_str(self.key_args, self.key_star)

    def forward_args_kwargs_str(self, skip: int = 0) -> str:
        if not self.num_args: return '(), {}'
        pos_args = self.pos_args[skip:]
        f_args = forward_args_str(pos_args, self.pos_star)
        f_kwargs = forward_kwargs_str(self.key_args, self.key_star)
        if self.defaults and self.can_have_ooo_defs():
            # see func_compile
            return f'*`PROC_OOO_DEFS({f_args}, {f_kwargs}, {', '.join(map(repr, pos_args))})'
        return f'{f_args}, {f_kwargs}'

    def can_have_ooo_defs(self) -> bool:
        # does this sig allow out-of-order defaults: a non-default pos arg AFTER default pos arg via kw=?
        # f(a, /, b=object(), c=object()) allows f(0, c=5)
        # f(a, /, b=object()) does not
        # this affects whether forwarded args/kwargs must be post-processed
        is_opt = self.is_optional
        get_def = self.defaults.get
        saw_da = False
        for arg in self.pos_or_key_args:
            if saw_da and is_opt(arg):
                return True
            saw_da |= get_def(arg, None) is ARG_DEFAULT
        return False

################################################################################

Signature.ZERO_INST = Signature()

################################################################################

def get_signature(fun: Callable, *, skip: int = 0, defaults: FilterFn = ALL_DEFAULTS) -> Signature:
    from .signature_utils import sig_of_py_function, sig_of_callable

    # fast path
    if isinstance(fun, FunctionType):
        return sig_of_py_function(fun, skip, defaults)

    try:
        sig = sig_of_callable(fun, skip, defaults)
        if hasattr(fun, '_is_coroutine_marker'):
            sig.is_coro = True
        return sig

    except Exception as exc:
        print(f"Error getting signature from {fun}: {exc!r}")
        print(fmt_exception(exc))
        return Signature(pos_star='args', key_star='kwargs')
