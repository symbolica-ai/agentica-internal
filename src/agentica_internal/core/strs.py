# fmt: off
from datetime import datetime
from collections.abc import Callable, Iterable as Iter, Sequence as Seq
from re import MULTILINE, compile as compile_regex
from typing import Any

__all__ = [
    'ToStr',
    'Strs',
    'pascal_str',
    'camel_str',
    'upper_str',
    'snake_str',
    'indent_str',
    'unindent_str',
    'commas_str',
    'spaces_str',
    'lines_str',
    'indent_lines',
    'paren_str',
    'list_str',
    'tuple_str',
    'set_str',
    'dict_str',
    'dict_kv_str',
    'fn_call_str',
    'headed_str',
    'fn_call_str',
    'dict_str',
    'dict_kv_str',
    'pathsafe_str',
    'idsafe_str',
    'timestamp_str',
    'forward_args_str',
    'forward_kwargs_str',
    'forward_call_str',
    'def_params_str'
]

####################################################################################################

type ToStr = Callable[[object], str]
type Strs = Iter[str]

####################################################################################################

def pascal_str(snake: str) -> str:
    return ''.join(map(upper_str, snake.split('_')))


def camel_str(snake: str) -> str:
    if '_' not in snake:
        return snake
    first, *rest = snake.split('_')
    return first + ''.join(map(upper_str, rest))


def upper_str(word: str) -> str:
    if not word:
        return word
    return word[0].upper() + word[1:]


def snake_str(camel: str) -> str:
    s1 = UPPER_LOWER.sub(r'\1_\2', camel)
    return DIGIT_UPPER.sub(r'\1_\2', s1).lower()


def indent_str(s: str, i: int = 1) -> str:
    return s.replace('\n', indent_sep(i))


def unindent_str(s: str) -> str:
    return INDENTED_LINE.sub('', s)


def commas_str(seq: Strs) -> str:
    return ', '.join(seq)


def spaces_str(seq: Strs) -> str:
    return ' '.join(seq)


def lines_str(seq: Strs) -> str:
    return '\n'.join(seq)


def indent_sep(i: int) -> str:
    if i == 1:
        return '\n\t'
    if i == 0:
        return '\n'
    return '\n' + ('\t' * i)


def indent_lines(seq: Strs, i: int = 1) -> str:
    return indent_sep(i).join(seq)


def paren_str(seq: Strs) -> str:
    return f'({', '.join(seq)})'


def list_str(seq: Strs) -> str:
    seq = tuple(seq)
    if seq == ():
        return '[]'
    if has_nl(seq):
        return comma_indented_str('[', ']', seq)
    return f'[{', '.join(seq)}]'


def tuple_str(seq: Strs) -> str:
    seq = tuple(seq)
    if seq == ():
        return '(,)'
    if len(seq) == 1:
        return f'({seq[0]},)'
    if has_nl(seq):
        return comma_indented_str('(', ')', seq)
    return f'({', '.join(seq)})'


def set_str(seq: Strs) -> str:
    seq = tuple(seq)
    if len(seq) == 0:
        return 'set()'
    if has_nl(seq):
        return comma_indented_str('set(', ')', seq)
    return '{' + ', '.join(seq) + '}'


def frozenset_str(seq: Strs) -> str:
    seq = tuple(seq)
    if len(seq) == 0:
        return 'frozenset()'
    if has_nl(seq):
        return comma_indented_str('frozensetset(', ')', seq)
    return 'frozenset({' + ', '.join(seq) + '})'


def dict_str(dct: dict[str, Any], fn: ToStr, ml: bool = False, sort: bool = True) -> str:
    if not dct:
        return '{}'
    ks = []
    vs = []
    items = list(dct.items())
    if sort:
        items.sort(key=lambda pair: pair[0])
    for k, v in items:
        ks.append(k)
        vs.append(fn(v))
    return dict_kv_str(ks, vs, ml)


def dict_kv_str(keys: Strs, vals: Strs, ml: bool = False) -> str:
    if has_nl(vals) or ml:
        return comma_indented_str('{', '}', (f'{k!r}: {v}' for k, v in zip(keys, vals)))
    return '{' + commas(f'{k!r}: {v}' for k, v in zip(keys, vals)) + '}'


def headed_str(head: str, seq: Strs) -> str:
    return f'{head}({','.join(seq)})'


def fn_call_str(fn: str, args: Strs, kwargs: dict[str, str]) -> str:
    args = list(args)
    args.extend(f'{k}={v}' for k, v in kwargs.items())
    f_args = commas(args)
    return f'{fn}({f_args})'


def has_nl(args: Strs) -> bool:
    return any('\n' in arg for arg in args)


def comma_indented_str(l: str, r: str, args: Strs) -> str:
    return l + '\n  ' + ',\n  '.join(args) + '\n' + r


def pathsafe_str(text: str) -> str:
    text = text.replace('...', 'ellipsis')
    text = text.replace('[', '(').replace(']', ')').replace(', ', ',')
    safe = QUOTES.sub('', text)
    safe = NON_PATHSAFE.sub('_', safe)
    if len(safe) > 64:
        return safe[:64]
    return safe

def timestamp_str() -> str:
    # yymmdd-hhmm-micros
    # 251204-1428-340565
    return datetime.now().strftime("%y%m%d-%H%M%S-%f")

commas = ', '.join

####################################################################################################

def forward_args_str(strs: Seq[str], star: str | None) -> str:
    if not strs:
        return star or '()'
    joined = commas(strs)
    extra = f' *{star}' if star else ''
    return f'({joined},{extra})'

####################################################################################################

def forward_kwargs_str(strs: Seq[str], star: str | None) -> str:
    if not strs:
        return star or '{}'
    joined = commas(f'{k}={k}' for k in strs)
    extra = f', **{star}' if star else ''
    return f'dict({joined}{extra})'

####################################################################################################

def forward_call_str(pos: Seq[str], key: Seq[str], pos_star: str | None, key_star: str | None) -> str:
    strs = list(pos)
    if pos_star: strs.append(f'*{pos_star}')
    strs.extend(f'{k}={k}' for k in key)
    if key_star: strs.append(f'**{key_star}')
    return commas(strs)

####################################################################################################

def def_params_str(pos: Seq[str], key: Seq[str], pos_star: str | None, key_star: str | None, pos_only: int,
                   f: Callable[[str], str]) -> str:
    r = []
    if pos:      r.extend(map(f, pos))
    if pos_only: r.insert(pos_only, '/')
    if pos_star: r.append('*' + f(pos_star))
    elif key:    r.append('*')
    if key:      r.extend(map(f, key))
    if key_star: r.append('**' + f(key_star))
    return commas(r)

####################################################################################################

class IdReplacer(dict[..., str]):
    def __missing__(self, key) -> str:
        n = len(self)
        self[key] = rep = f'0x{n:08x}'
        return rep

def idsafe_str(s: str) -> str:
    if not ID_DIGITS.search(s):
        return s
    reps = IdReplacer()
    return ID_DIGITS.sub(lambda m: reps[m.group(0)], s)

####################################################################################################

UPPER_LOWER   = compile_regex('(.)([A-Z][a-z]+)')
DIGIT_UPPER   = compile_regex('([a-z0-9])([A-Z])')
INDENTED_LINE = compile_regex('^\t|    ', MULTILINE)
QUOTES        = compile_regex('[\'"]')
NON_ALNUM     = compile_regex(r'[^a-zA-Z0-9_]')
NON_PATHSAFE  = compile_regex(r'[^a-zA-Z0-9_()]')
ID_DIGITS     = compile_regex(r'\b[45678]\d{8,10}\b')
