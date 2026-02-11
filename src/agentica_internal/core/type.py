# fmt: off

"""
This file exposes a bunch of internal class objects under more intelligible names.

# `types` module

From `types` we have simple aliases, like `FunctionT` -> `FunctionType`.

But more importantly, we have the following aliases for classes whose instances
are function-like / callable. The first column is the alias name, the second
is the name as reported by `types`, and the third

| alias                | original                  | example instance           |
| BoundMethodT         | MethodType                | `my_obj.my_inst_method`    |
| UnboundMethodC       | MethodDescriptorType      | `bytes.hex`                |
| UnboundDunderMethodC | WrapperDescriptorType     | `list.__init__`            |
| BoundDunderMethodC   | MethodWrapperType         | `[].__len__`               |
| BoundClassMethodC    | ClassMethodDescriptorType | `bytes.__dict__['fromhex']' |
| BoundMethodOrFuncC   | BuiltinFunctionType       | `len`                      |
| BoundMethodOrFuncC   | BuiltinMethodType         | `[].append`                |
| BoundMethodC         |                           | `re.compile('').finditer`  |
| MutablePropertyC     | GetSetDescriptorType      | `FrameType.f_locals`       |
| SlotPropertyC        | MemberDescriptorType      | `timedelta.days`           |

Note that `BuiltinFunctionType is BuiltinMethodType`, the instances of this
class have a `__self__` attribute that is a module for builtin functions,
e.g. `len.__self__ is builtins`, or a genuine object, e.g.
`lst.append.__self__ is lst`.

Here is what these various instances print as, if you want to tell at a glance
what you are dealing with from the print form of such an instance:
| BoundMethodT         | `<bound method 'NAME' of SELF>`            |
| BoundMethodC         | `builtin-in method 'NAME' of SELF>`        |
| UnboundMethodC       | `<method 'NAME' of 'CLASS' objects>`       |
| UnboundDunderMethodC | `<slot wrapper 'NAME' of 'CLASS' objects>` |
| BoundDunderMethodC   | `<method-wrapper 'NAME' of SELF>`          |
| BoundClassMethodC    | `<method 'NAME' of 'CLASS' objects>`       |
| BoundMethodOrFuncC   | `<built-in function 'NAME'>`               |
|                      | `<built-in method 'NAME' of SELF>`         |
| MutablePropertyC     | `<attribute 'NAME' of 'CLASS' objects>`    |
| SlotPropertyC        | `<slot 'NAME' of 'CLASS' objects>`         |

Here is what the classes themselves print as:
| BoundMethodT         | `<class 'method'>`                     |
| BoundMethodC         | `<class 'builtin_method'>`             |
| UnboundMethodC       | `<class 'method_descriptor'>`          |
| UnboundDunderMethodC | `<class 'wrapper_descriptor'>`         |
| BoundDunderMethodC   | `<class 'method-wrapper'>`             |
| BoundClassMethodC    | `<class 'classmethod_descriptor'>`     |
| BoundMethodOrFuncC   | `<class 'builtin_function_or_method'>` |
| MutablePropertyC     | `<class 'getset_descriptor'>`          |
| SlotPropertyC        | `<class 'member_descriptor'>`          |

# `typing`, `collections.abc` module

To actually destructure type annotations, it helps to know what they are
underneath. E.g. `type(List[int])` is not a public class, and while all these
classes are quite rational, they have bizarre names, so here we expose them with
intelligible names.

The first letter of the alias `T` if it is from the `typing` module, and `C` if
it from the `types` module (since such classes are implemented in C).

The first column shows the alias, and the second column shows examples of this
class.

C-implemented in `types`:
| CGeneric       | `UserClass[int]` etc.
| CUnion         | `int | str`
| CCallable      | `collections.abc.Callable[[int], str]`

Python-implemented in `typing`:
| TBaseGeneric   | superclass, any of the below are instances
| TBlankGeneric  | `typing.Callable, typing.List, typing.Iterable` etc.
| TBlankCallable | ONLY `typing.Callable`
| TBlankTuple    | ONLY `typing.Tuple`
| TGeneric       | `typing.ClassVar[int], typing.TypeGuard[int]` etc.

Furthermore, `TGeneric` has various subclasses for special cases:
| TCallable      | `typing.Callable[[int], str]`
| TUnion         | `typing.Union[int, str]`
| TLiteral       | `typing.Literal['a', 'b']`
| TConcat        | `typing.Concat[...]`
| TUnpack        | `typing.Unpack[...]`
| TAnnotated     | `typing.Annotated[int, 'hello']`

Note that *unparameterized* forms of these type constructors are also valid
type annotations, e.g. `typing.Union` on its own. These are all instances
of the class `TForm`.

The following are in the own special category:
| TAny   | `typing.Any`
| TForm  | `typing.Never`, `typing.ClassVar`, `typing.Literal`, etc.

For completeness, we also expose the public classes:
| TForward       | ForwardRef     | `xxx: "whatever"`
| TAlias         | TypeAliasType  | `type xxx = whatever`
| TVar           | TypeVar        | the `X` in `def foo[X](): ...`
| TParamSpec     | ParamSpec      | the `X` in `def foo[**X](): ...`

## Utilities

To tell if an object is a type annotation, you can write:
`type(object) in ANNOS`.

To format a type annotation as a string, you can write:
`anno_str(anno)`, see its docstring for more info.
"""

from ..cpython.classes.sys import *
from ..cpython.classes.anno import *
from .anno import anno_str, is_anno  # noqa: F401
