# fmt: off

from types import FunctionType, UnionType
from typing import NoReturn
from agentica_internal.warpc.data.signature import get_signature

class Foo: ...

class Bar:
    def __init__(self, a: int, b: str): ...

class Baz(Bar): ...

class HasNew(Foo):
    def __new__(cls, a: int): ...

class MyNewFunctionObj:
    def __call__(self, cls): ...

class HasNew2(Foo):
    __new__ = MyNewFunctionObj()

class Metatype(type):
    def __call__(cls, a: int): ...

class Unconstructible1:
    __new__ = None

class Unconstructible2:
    def __init__(self) -> NoReturn: ...

class Type(metaclass=Metatype): ...

TF_SIGS = []
def add(ty, sig): TF_SIGS.append((ty, sig))
# add(object,        "(*args, **kwargs)")
# add(type,          "(name: str, bases: tuple[type, ...], namespace: dict[str, Any], /, **kwds: Any)")
# add(str,           "(object: Buffer, encoding: str = 'utf-8', errors: str = 'strict')")
add(Foo,              "()")
add(Bar,              "(a: int, b: str)")
add(Baz,              "(a: int, b: str)")
add(HasNew,           "(a: int)")
add(HasNew2,          "()")
add(FunctionType,     "(*args, **kwargs)")
add(Type,             "(a: int)")
add(Unconstructible1, "() -> NoReturn")
add(Unconstructible2, "() -> NoReturn")

def verify_type_constructor_signature():

    def assert_tf_sig(ty: type, e_str: str):
        i_sig = get_signature(ty)
        i_str = i_sig.sig_str()
        assert i_str == e_str, f'{ty.__name__!r} class constructor:\n{i_str!r} != {e_str!r}'

    for cls, sig in TF_SIGS:
        assert_tf_sig(cls, sig)

def verify_unconconstructible_signature():
    for ty in (Unconstructible1, Unconstructible2, UnionType):
        i_sig = get_signature(ty)
        assert i_sig.annos['return'] is NoReturn

if __name__ == '__main__':
    verify_type_constructor_signature()
    verify_unconconstructible_signature()
