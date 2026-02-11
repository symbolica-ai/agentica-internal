# fmt: off

from types import FunctionType, ModuleType
from typing import Any, NoReturn, Never
from collections.abc import Callable, Iterator
from ...cpython.class_info import READ_ONLY_CLASS, NO_CONS_CLASS

from ...cpython.classes.sys import *
from ..kinds import unpack_method
from .. import flags
from .signature import Signature, FilterFn, ALL_DEFAULTS, NO_DEFAULTS

__all__ = [
    'sig_of_callable',
    'sig_of_class_constructor',
    'sig_of_callable_obj',
    'sig_of_py_function',
    'sig_of_c_dunder_method',
    'sig_of_def_str',
    'sig_of_c_function',
    'sig_of_ctypes_funcptr',
    'ALL_DEFAULTS',
    'NO_DEFAULTS',
]

################################################################################

def sig_of_callable(f: Callable, s: int, d: FilterFn):
    cls = type(f)

    if cls is FunctionType:
        return sig_of_py_function(f, s, d)

    if cls is BoundMethodT:
        return sig_of_callable(f.__func__, s+1, d)

    if cls in (BoundDunderMethodC, UnboundDunderMethodC):
        s2 = s + 1 if cls is BoundDunderMethodC else s
        if sig := sig_of_c_dunder_method(f.__objclass__, f.__name__, s2):
            return sig

    if cls is CachingFunctionC:
        return sig_of_callable(f.__wrapped__, s, d)

    if cls in C_CALLABLES:
        return sig_of_c_function(f, s, d)

    if cls is type or isinstance(f, type):
        return sig_of_class_constructor(f, s + 1, d)

    return sig_of_callable_obj(f, s, d)

################################################################################

def sig_of_class_constructor(cls: type, skip: int, dfilt: FilterFn) -> Signature:

    __new__ = cls.__new__

    flags = cls.__flags__
    if __new__ is None or flags & NO_CONS_CLASS:
        return Signature(annos={'return': NoReturn})

    # builtin classes resolve to their `__new__`
    if flags & READ_ONLY_CLASS and cls.__module__ == 'builtins':
        return _fix_cons(sig_of_callable(__new__, skip, dfilt))

    mcls = type(cls)
    if mcls is not type:
        return _fix_cons(sig_of_callable(mcls.__call__, skip, dfilt))

    elif isinstance(__new__, FunctionType):
        return _fix_cons(sig_of_py_function(__new__, skip, dfilt))

    elif isinstance(__new__, BoundMethodOrFuncC):
        # does this bind to `object`'s `__new__`?
        if __new__.__self__ is object:
            # if so, we know that this will forward to cls.__init__
            return _fix_cons(sig_of_callable(cls.__init__, skip, dfilt))

    return _fix_cons(sig_of_callable(__new__, skip, dfilt))

################################################################################

def _fix_cons(sig: Signature):
    annos = sig.annos
    if 'return' in annos:
        ret = annos['return']
        if ret is NoReturn or ret is Never:
            annos['return'] = NoReturn
        else:
            annos.pop('return')
    return sig

################################################################################

def sig_of_callable_obj(fun: Callable, skip: int, dfilt: FilterFn) -> Signature:
    assert callable(fun)
    call = getattr(fun, '__call__', None)
    assert call is not None
    return sig_of_callable(call, skip, dfilt)

################################################################################

def sig_of_py_function(
            fun: FunctionType, skip: int, dfilt: FilterFn,
            overloads: list[FunctionType] | None = None
        ) -> Signature:

    from ...cpython.code import code_arg_info
    from ...cpython.overloads import get_overloads
    from ...cpython.function import func_get_defaults, func_is_coro

    is_coro = func_is_coro(fun)

    fun_code = fun.__code__
    args = code_arg_info(fun_code, skip)

    defs = {}
    opts = []
    default_keys = args.default_keys()
    for k, d in func_get_defaults(fun):
        if k in default_keys:
            opts.append(k)
            if dfilt is ALL_DEFAULTS or dfilt(d):
                defs[k] = d

    fun_annos = fun.__annotations__
    if isinstance(fun_annos, dict):
        annos = {
            k: fun_annos[k]
            for k in args.anno_keys()
            if k in fun_annos
        }
    else:
        annos = {}

    doc = fun.__doc__
    doc = doc if isinstance(doc, str) else None

    if overloads is None:
        overloads = get_overloads(fun)

    if overloads:
        kind, func = unpack_method(overloads.pop())
        next_over = sig_of_py_function(func, 0, dfilt, overloads)
    else:
        next_over = None

    return Signature(
        pos_args=args.pos,
        key_args=args.key,
        pos_only=args.pos_only,
        pos_star=args.pos_star,
        key_star=args.key_star,
        optional=opts,
        doc_str=doc,
        defaults=defs,
        annos=annos,
        is_coro=is_coro,
        next_over=next_over
    )

################################################################################

DUNDER_SIGS = {
    'bool':         ('self', bool),
    'str':          ('self', str),
    'complex':      ('self', complex),
    'repr':         ('self', str),
    'contains':     ('self', 'value', bool),
    'getattribute': ('self', 'name', Any),
    'getattr':      ('self', 'name', Any),
    'setattr':      ('self', 'name', 'value', None),
    'delattr':      ('self', 'name', None),
    'dir':          ('self', list[str]),
    'reduce':       ('self', Any),
    'reduce_ex':    ('self', 'protocol', Any),
    'getstate':     ('self', Any),
    'setstate':     ('self', 'state', None),
    'object.init':  ('self', ...),

}

def bulk_sig(sig: tuple, *names: str):
    DUNDER_SIGS.update((name, sig) for name in names)

_INT  = ('self', int)
_ITR = ('self', Iterator[Any])
_BIN = ('self', 'other', Any)
_CMP = ('self', 'other', bool)

bulk_sig(_ITR, 'iter', 'reversed')
bulk_sig(_INT, 'hash', 'index', 'int', 'len')
bulk_sig(_CMP, 'eq', 'ne', 'lt', 'le', 'gt', 'ge')
bulk_sig(_BIN, 'add', 'sub', 'mul', 'pow', 'divmod', 'and', 'or')

def sig_of_c_dunder_method(cls: type, name: str, skip: int) -> Signature | None:
    name = name.removeprefix('__').removesuffix('__')
    tup = DUNDER_SIGS.get(name, None)
    if tup is None:
        name = f'{cls.__name__}.{name}'
        tup = DUNDER_SIGS.get(name, None)
    if tup is None:
        return None
    *args, ret = tup
    if skip: args = args[skip:]
    annos = {}
    if ret is not ...: annos['return'] = ret
    if 'name' in args: annos['name'] = str
    if 'value' in args: annos['value'] = str
    return Signature(pos_args=tuple(args), is_cext=True, annos=annos)

################################################################################

TEXT_SIGNATURE_CACHE: dict[tuple, Signature] = {}

def sig_of_c_function(fun: Callable, skip: int, dfilt: FilterFn) -> Signature:
    key = fun, skip, dfilt
    if sig := TEXT_SIGNATURE_CACHE.get(key):
        return sig
    ts = get_text_signature(fun)
    if ts is None:
        return Signature(pos_star='args', key_star='kwargs')
    assert type(ts) is str, f"Bad text signature for {fun} of type {type(fun).__name__}: {ts}"
    assert ts.startswith('(') and (ts.endswith(')') or ' -> ' in ts)

    cls = type(fun)
    # log('\n', SYS_TO_NAME.get(cls, cls.__name__), fun, f"with ts={ts!r}")

    i = 2 if ts.startswith('($') else 1
    ts = ts[i:]

    # numpy.array is module-bound but forgot to include $module
    if cls is BoundMethodOrFuncC:
        self = fun.__self__
        if type(self) is ModuleType and not ts.startswith('module'):
            ts = 'module, ' + ts
        elif type(self) is type:
            skip -= 1  # e.g. object.__new__

    if cls in (BoundMethodOrFuncC, BoundMethodC, BoundDunderMethodC):
        skip += 1

    defn = f"def _({ts}: pass"
    if not flags.BELIEVE_TEXT_SIGNATURE_DEFAULTS:
        dfilt = NO_DEFAULTS
    sig = sig_of_def_str(defn, skip, dfilt)
    sig.is_cext = True
    TEXT_SIGNATURE_CACHE[key] = sig
    return sig

SEQ_NEW_SIG = '(cls: type, iter: Iterator[Any], /)'
SEQ_INIT_SIG = '(self, iter: Iterator[Any], /)'

TEXT_SIGNATURE_OVERRIDES = {
    'list.__new__':     SEQ_NEW_SIG,
    'tuple.__new__':    SEQ_NEW_SIG,
    'set.__new__':      SEQ_NEW_SIG,
    'list.__init__':    SEQ_INIT_SIG,
    'tuple.__init__':   SEQ_INIT_SIG,
    'set.__init__':     SEQ_INIT_SIG,
    'object.__init__': "(self, /)",
    'type.__new__':    "(cls: type, name: str, bases: tuple[type, ...], namespace: dict[str, Any], /, **kwds: Any)",
    'str.__new__':     "(cls: type, object: collections.abc.Buffer, encoding: str = 'utf-8', errors: str = 'strict')",
}

def get_text_signature(fun: Any) -> str | None:
    cls = type(fun)
    if cls is UnboundMethodC or cls is UnboundDunderMethodC or \
            (cls is BoundMethodOrFuncC and type(fun.__self__) is type):
        if sig := TEXT_SIGNATURE_OVERRIDES.get(fun.__qualname__):
            return sig
    return getattr(fun, '__text_signature__', None)


################################################################################

DEF_STR_SIGNATURE_CACHE: dict[tuple, Signature] = {}

def sig_of_def_str(def_str: str, skip: int, dfilt: FilterFn, names: dict = None) -> Signature:

    key = def_str, skip, dfilt
    if sig := DEF_STR_SIGNATURE_CACHE.get(key):
        return sig

    import ast
    from ...core.eval import eval_safe
    from ...core.sentinels import ARG_DEFAULT

    def_str = def_str.replace('<unrepresentable>', 'ARG_DEFAULT')

    if '[,' in def_str:
        def_str = def_str.split('[,', 1)[0] + ', *args, **kwargs): ...'
        # log('replaced optional arg syntax:', def_str)
    try:
        parsed = ast.parse(def_str, filename='')
    except:
        # log('def_str parse error', def_str)
        return Signature(pos_star='args', key_star='kwargs')

    sig_def = parsed.body[0]
    assert isinstance(sig_def, ast.FunctionDef)

    arguments = sig_def.args
    _pos_only_args = arguments.posonlyargs
    num_pos_only = len(_pos_only_args)
    _pos_args = _pos_only_args + arguments.args
    _key_args = arguments.kwonlyargs

    if skip:
        _pos_args = _pos_args[skip:]
        num_pos_only = max(num_pos_only - skip, 0)

    # populate arguments and their annos
    annos = {}
    def parse_node(arg: 'ast.arg'):
        name = arg.arg
        anno_valid, anno = eval_safe(arg.annotation, names=names)
        if anno_valid: annos[name] = anno
        return name

    _pos_star = arguments.vararg
    _key_star = arguments.kwarg
    pos_args = tuple(map(parse_node, _pos_args))
    pos_star = parse_node(_pos_star) if _pos_star else None
    key_args = tuple(map(parse_node, _key_args))
    key_star = parse_node(_key_star) if _key_star else None

    # populate returns anno
    return_valid, returns = eval_safe(sig_def.returns, names=names)
    if return_valid: annos['return'] = returns

    # populate `defaults` and `optional`
    defaults = {}
    optional = ()
    _pos_nodes = arguments.defaults
    _key_nodes = arguments.kw_defaults
    if _pos_nodes or _key_nodes:

        def parse_default(def_name: str, def_node: 'ast.expr'):
            valid, default = eval_safe(def_node, unrep=ARG_DEFAULT, filt=dfilt, names=names)
            if valid: defaults[def_name] = default
            return def_name

        n = len(_pos_nodes)
        pos_names = pos_args[-n:] if n else ()
        key_names = key_args
        optional = tuple(
            parse_default(name, node)
            for name, node in zip(pos_names + key_names, _pos_nodes + _key_nodes)
            if node is not None
        )

    sig = Signature(
        pos_args=pos_args,
        key_args=key_args,
        pos_star=pos_star,
        key_star=key_star,
        pos_only=num_pos_only,
        optional=optional,
        defaults=defaults,
        annos=annos,
    )
    DEF_STR_SIGNATURE_CACHE[key] = sig
    return sig

################################################################################

def sig_of_ctypes_funcptr(fun: Callable) -> Signature:

    args_types = getattr(fun, 'argtypes', None)
    assert type(args_types) is tuple
    arg_names = tuple(f'arg{i}' for i in range(len(args_types)))

    annos = {}
    for n, t in zip(arg_names, args_types):
        if a := parse_cty(t):
            annos[n] = a

    res_type = getattr(fun, 'restype', None)
    if a := parse_cty(res_type):
        annos['return'] = a

    return Signature(pos_args=arg_names, annos=annos)

def parse_cty(cty) -> type | None:
    if code := getattr(cty, '_type_', None):
        for codes, ty in FROM_CTYPE:
            if code in codes:
                return ty
    return None

FROM_CTYPE = [
    ('?',  bool),
    ('P',  int | None),
    ('Z',  str),
    ('u',  str),
    ('zc', bytes),
    ('c',  bytes),
    ('bBlLqQiIH', int),
    ('fgd', float),
    ('O',   object)
]
