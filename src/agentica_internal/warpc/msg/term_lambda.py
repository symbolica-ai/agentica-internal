# fmt: off

import ast
import builtins

from types import LambdaType

from .__ import *
from .base import Msg
from .term import TermPassByValMsg
from .term_atom import AtomMsg


__all__ = [
    'LambdaMsg',
    'SyntaxMsg',
]


################################################################################

class LambdaMsg(TermPassByValMsg, tag='lambda'):

    syntax:  'LambdaSyntaxMsg'
    globals: 'AttributesT'

    @staticmethod
    def encode_lambda(enc: EncoderP, func: FunctionType) -> 'LambdaMsg':
        msg = function_to_lambda_msg(enc, func)
        return msg

    def decode(self, dec) -> FunctionType:
        fun = lambda_msg_to_function(dec, self)
        return fun


################################################################################

type SyntaxMsgs = list[SyntaxMsg]

class SyntaxMsg(Msg): ...


################################################################################

class LambdaSyntaxMsg(SyntaxMsg, tag='lambda$'):

    args: list[str]
    body: 'SyntaxMsg'


################################################################################

class NameSyntax(SyntaxMsg):
    name: str

class LambdaArgSyntax(NameSyntax,   tag='arg$'):
    name: str

class BuiltinNameSyntax(NameSyntax, tag='sys$'):
    name: str

class GlobalNameSyntax(NameSyntax,  tag='var$'):
    name: str


################################################################################

type BinOp = Literal[
    'Add', 'Sub', 'Mult', 'Div', 'FloorDiv', 'Mod', 'Pow', 'LShift', 'RShift',
    'BitOr', 'BitXor', 'BitAnd', 'MatMult'
]

class BinarySyntax(SyntaxMsg, tag='binary$'):
    left:  'SyntaxMsg'
    op:     BinOp
    right: 'SyntaxMsg'


################################################################################

type BoolOp = Literal['A', 'USub', 'Not', 'Invert']

class BoolSyntax(SyntaxMsg):
    args: 'SyntaxMsgs'

class AndSyntax(BoolSyntax, tag='and$'): ...
class OrSyntax(BoolSyntax, tag='or$'): ...


################################################################################

type CmpOp = Literal[
    'Eq', 'NotEq', 'Lt', 'LtE', 'Gt', 'GtE', 'Is', 'IsNot', 'In', 'NotIn'
]


class CompareSyntax(SyntaxMsg, tag='cmp$'):
    left:  'SyntaxMsg'
    op:     CmpOp
    right: 'SyntaxMsg'


################################################################################

type UnaryOp = Literal['UAdd', 'USub', 'Not', 'Invert']

class UnarySyntax(SyntaxMsg, tag='unary$'):
    op:   UnaryOp
    arg: 'SyntaxMsg'


################################################################################

class ConstantSyntax(SyntaxMsg, tag='const$'):
    const: 'AtomMsg'


################################################################################

class CallSyntax(SyntaxMsg, tag='call$'):
    fn:   'SyntaxMsg'
    args: 'SyntaxMsgs'


################################################################################

class TernaryIfSyntax(SyntaxMsg, tag='if$'):
    test:  'SyntaxMsg'
    tbody: 'SyntaxMsg'
    fbody: 'SyntaxMsg'


################################################################################

class AwaitSyntax(SyntaxMsg, tag='await$'):
    arg: 'SyntaxMsg'


################################################################################

class GetAttrSyntax(SyntaxMsg, tag='getattr$'):
    obj:  'SyntaxMsg'
    attr: str


class GetItemSyntax(SyntaxMsg, tag='getitem$'):
    obj:  'SyntaxMsg'
    item: 'SyntaxMsg'


################################################################################

class ContainerSyntax(SyntaxMsg):
    vals: 'SyntaxMsgs' = []

class ListSyntax(ContainerSyntax,  tag='list$'): ...
class TupleSyntax(ContainerSyntax, tag='tuple$'): ...
class SetSyntax(ContainerSyntax,   tag='set$'): ...

class DictSyntax(ContainerSyntax, tag='dict$'):
    keys: 'SyntaxMsgs' = []
    vals: 'SyntaxMsgs' = []


################################################################################

class FmtSyntax(SyntaxMsg, tag='fmt$'):
    value: 'SyntaxMsg'
    conversion: int

class FStringSyntax(SyntaxMsg, tag='fstr$'):
    elems: list[str | FmtSyntax]


################################################################################

# TODO: hook these up

class ComprehensionIteratorSyntax(SyntaxMsg, tag='comp_iter$'):
    target: 'SyntaxMsg'
    iter:   'SyntaxMsg'
    tests:  'SyntaxMsgs'

class ComprehensionSyntax(SyntaxMsg):
    elem: 'SyntaxMsg'
    iters: list[ComprehensionIteratorSyntax]

class ListComprehensionSyntax(ComprehensionSyntax, tag='list_comp$'): ...
class SetComprehensionSyntax(ComprehensionSyntax, tag='set_comp$'): ...
class DictComprehensionSyntax(ComprehensionSyntax, tag='dict_comp$'): ...
class GeneratorSyntax(ComprehensionSyntax, tag='generator$'): ...


################################################################################

def function_to_lambda_msg(enc: EncoderP, func: FunctionType | LambdaType) -> LambdaMsg:
    from inspect import getsource
    try:
        source = getsource(func)
    except:
        source = None
    if not source:
        raise E.WarpLambdaEncodingError(f'could not obtain source for {func!r}')
    return source_to_lambda_msg(enc, source, func.__globals__)

def source_to_lambda_msg(enc: EncoderP, source: str, lambda_globals: AttributesT | None = None) -> LambdaMsg:
    from ast import parse
    source = source.strip()
    if not source.startswith('lambda ') and 'lambda ' not in source:
        raise E.WarpLambdaEncodingError(f'not a lambda function: {source!r}')
    try:
        tree = parse(source, '<lambda>', 'exec')
    except OSError:
        tree = None
    if tree is None:
        raise E.WarpLambdaEncodingError(f'could not recompile lambda:\n{source!r}\ngot {tree!r}')
    lambda_node = find_lambda_node(tree)
    if lambda_node is None:
        raise E.WarpLambdaEncodingError(f'could not find lambda:\n{source!r}')
    return encode_lambda_msg(enc, lambda_node, lambda_globals)

def find_lambda_node(node: ast.AST) -> ast.Lambda | None:
    # TODO: make this more precise, since there might be multiple lambdas in
    # the returned source. we can do better by 1) checking the argument names
    # to disambiguate 2) aborting if there is STILL possible ambiguity
    if isinstance(node, ast.Lambda):
        return node
    for node in ast.walk(node):
        if isinstance(node, ast.Lambda):
            return node
    return None

################################################################################

def lambda_msg_to_ast(dec: DecoderP, msg: LambdaMsg) -> ast.Lambda:
    lambda_node, lambda_globals = decode_lambda_msg(dec, msg)
    return lambda_node

def lambda_msg_to_source(dec: DecoderP, msg: LambdaMsg) -> str:
    lambda_node, lambda_globals = decode_lambda_msg(dec, msg)
    return ast.unparse(lambda_node)

def lambda_msg_to_function(dec: DecoderP, msg: LambdaMsg) -> FunctionType:
    lambda_node, lambda_globals = decode_lambda_msg(dec, msg)
    expr = ast.Expression(body=lambda_node)
    ast.fix_missing_locations(expr)
    try:
        code = compile(expr, '<lambda>', 'eval')
    except OSError:
        code = None
    if not isinstance(code, S.CodeT):
        f_node = ast.dump(lambda_node, indent=3)
        raise E.WarpLambdaDecodingError(f'could not compile lambda tree:\n{f_node}')
    try:
        func = eval(code, lambda_globals)
        if isinstance(func, FunctionType):
            return func
    except:
        pass

    raise E.WarpLambdaDecodingError(f'could not create a FunctionType from code object:\n{code}')

################################################################################

def encode_lambda_msg(encoder: EncoderP, root: ast.Lambda, known_globals: dict[str, Any]) -> LambdaMsg:

    lambda_globals: dict[str, Any] = {}
    lambda_args: set[str] = set()

    if known_globals is None:
        known_globals = {}
    get_global = known_globals.get

    def enc_syntax(node: ast.expr) -> SyntaxMsg:
        match node:
            case ast.Name(name, ast.Load()):
                return enc_name(name)

            case ast.Lambda():
                return enc_lambda(node)

            case ast.Constant(value):
                return ConstantSyntax(AtomMsg.encode_atom(value))

            case ast.UnaryOp(op, operand):
                return UnarySyntax(enc_unary_op(op), enc(operand))

            case ast.BinOp(left, op, right):
                return BinarySyntax(enc(left), enc_bin_op(op), enc(right))

            case ast.BoolOp(op, values):
                cls = AndSyntax if type(op) is ast.And else OrSyntax
                return cls(enc_list(values))

            case ast.Compare(left, ops, comparators):
                assert len(ops) == 1
                return CompareSyntax(enc(left), enc_cmp_op(ops[0]), enc(comparators[0]))

            case ast.Call(func, args, keywords):
                assert len(keywords) == 0
                return CallSyntax(enc(func), enc_list(args))

            case ast.IfExp(test, body, orelse):
                return TernaryIfSyntax(enc(test), enc(body), enc(orelse))

            case ast.Subscript(value, part, ast.Load()):
                return GetItemSyntax(enc(value), enc(part))

            case ast.Attribute(value, attr, ast.Load()):
                return GetAttrSyntax(enc(value), attr)

            case ast.Tuple(vals, ast.Load()):
                return TupleSyntax(enc_list(vals))
            case ast.List(vals, ast.Load()):
                return ListSyntax(enc_list(vals))
            case ast.Set(vals, ast.Load()):
                return SetSyntax(enc_list(vals))
            case ast.Dict(keys, vals):
                return DictSyntax(enc_list(keys), enc_list(vals))

            case ast.JoinedStr(values):
                return FStringSyntax([enc_fstr_node(v) for v in values])
            case ast.FormattedValue():
                return enc_fstr_node(node)

            case _:
                raise E.WarpLambdaEncodingError(node)

    def enc_list(nodes):
        return list(map(enc_syntax, nodes))

    def enc_fstr_node(elem) -> FmtSyntax | str:
        match elem:
            case ast.FormattedValue(fval, conversion, None):
                return FmtSyntax(enc(fval), conversion)
            case str():
                return elem
            case _:
                raise E.WarpLambdaEncodingError(elem)

    def enc_pos_args(args: ast.arguments) -> list[str]:
        match args:
            case ast.arguments(pos_args, reg_args, None, [], [], None, []):
                return [a.arg for a in pos_args + reg_args]
            case _:
                enc_node_error("unsupported ast.arguments", args)

    def enc_lambda(node: ast.Lambda) -> LambdaSyntaxMsg:
        args = enc_pos_args(node.args)
        lambda_args.update(args)
        body = enc_syntax(node.body)
        return LambdaSyntaxMsg(args, body)

    def enc_name(name: str) -> SyntaxMsg:
        if name in lambda_args:
            return LambdaArgSyntax(name)
        if name in lambda_globals:
            return lambda_globals[name]

        value = get_global(name, NO_GLOBAL)
        if value is not NO_GLOBAL:
            lambda_globals[name] = value
            return GlobalNameSyntax(name)

        if builtin_global := get_builtin(name):
            return builtin_global

        raise E.WarpLambdaEncodingError(f"cannot resolve name: {name!r}")

    enc = enc_syntax

    lambda_syntax_msg = enc_lambda(root)
    lambda_globals_msg = encoder.enc_record(lambda_globals)
    lambda_msg = LambdaMsg(lambda_syntax_msg, lambda_globals_msg)

    return lambda_msg


################################################################################

def decode_lambda_msg(decoder: DecoderP, root: LambdaMsg) -> tuple[ast.Lambda, AttributesT]:

    def dec_syntax(msg):
        match msg:

            case NameSyntax(name):
                return ast.Name(name, ast.Load())

            case LambdaSyntaxMsg():
                return dec_lambda(msg)

            case ConstantSyntax(const):
                return ast.Constant(const.decode_atom())

            case UnarySyntax(op, operand):
                return ast.UnaryOp(dec_unary_op(op), dec(operand))

            case BinarySyntax(left, op, right):
                return ast.BinOp(dec(left), dec_bin_op(op), dec(right))

            case AndSyntax(args):
                return ast.BoolOp(ast.And(), dec_list(args))

            case OrSyntax(args):
                return ast.BoolOp(ast.Or(), dec_list(args))

            case CompareSyntax(left, op, right):
                ops = [dec_cmp_op(op)]
                rights = [dec_syntax(right)]
                return ast.Compare(dec(left), ops, rights)

            case CallSyntax(func, args):
                return ast.Call(dec(func), dec_list(args), [])

            case TernaryIfSyntax(test, tbody, fbody):
                return ast.IfExp(dec(test), dec(tbody), dec(fbody))

            case GetItemSyntax(value, part):
                return ast.Subscript(dec(value), dec(part), ast.Load())

            case GetAttrSyntax(value, attr):
                return ast.Attribute(dec(value), attr, ast.Load())

            case TupleSyntax(vals):
                return ast.Tuple(dec_list(vals), ast.Load())
            case ListSyntax(vals):
                return ast.List(dec_list(vals), ast.Load())
            case SetSyntax(vals):
                return ast.Set(dec_list(vals))
            case DictSyntax(keys, vals):
                return ast.Dict(dec_list(keys), dec_list(vals))

            case FStringSyntax(values):
                return ast.JoinedStr(list(map(dec_fstr_node, values)))
            case FmtSyntax():
                return dec_fstr_node(msg)

            case _:
                raise E.WarpLambdaDecodingError(msg)

    def dec_fstr_node(msg: FmtSyntax | str) -> ast.FormattedValue | str:
        match msg:
            case FmtSyntax(value, conversion):
                return ast.FormattedValue(dec_syntax(value), conversion)
            case str():
                return msg
            case _:
                raise E.WarpLambdaDecodingError(msg)

    def dec_pos_args(strs: list[str]) -> ast.arguments:
        args = [ast.arg(s) for s in strs]
        return ast.arguments([], args, None, [], [], None, [])

    def dec_lambda(msg: LambdaSyntaxMsg) -> ast.Lambda:
        args = dec_pos_args(msg.args)
        body = dec_syntax(msg.body)
        if not isinstance(body, ast.expr):
            raise E.WarpLambdaDecodingError()
        return ast.Lambda(args, body)

    def dec_list(msgs):
        return list(map(dec_syntax, msgs))

    dec = dec_syntax

    lambda_node = dec_lambda(root.syntax)
    lambda_globals = decoder.dec_record(root.globals)
    return lambda_node, lambda_globals


################################################################################

def enc_node_error(msg: str, node: ast.AST) -> NoReturn:
    f_node = ast.dump(node, indent=3)
    raise E.WarpLambdaEncodingError(f'{msg}\n{f_node}')


################################################################################

NO_GLOBAL = object()

################################################################################

builtin_globals: dict[str, BuiltinNameSyntax] = {
    name: BuiltinNameSyntax(name)
    for name in dir(builtins)
    if not name.startswith('__')
}

get_builtin = builtin_globals.get


################################################################################

def enc_dec_singletons[B](
    base: type[B],
    alias: T.TypeAliasType) -> tuple[Callable[[B], Any], Callable[[Any], B]]:
    value = alias.__value__
    names = value.__args__
    assert is_strtup(names)

    to_sng: dict[str, B] = {}
    for subcls in base.__subclasses__():
        name = subcls.__name__
        if name in names:
            to_sng[name] = subcls()

    def to_str(obj) -> str:
        name = type(obj).__name__
        assert name in names
        return name

    return to_str, to_sng.__getitem__

enc_bin_op, dec_bin_op     = enc_dec_singletons(ast.operator, BinOp)
enc_cmp_op, dec_cmp_op     = enc_dec_singletons(ast.cmpop, CmpOp)
enc_unary_op, dec_unary_op = enc_dec_singletons(ast.unaryop, UnaryOp)
