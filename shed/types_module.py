# ruff: noqa
# fmt: off

"""
This a hand-curated typeshed file for the builtin `types` module.
"""

from types import ModuleType
from typing import (
    Any,
    Callable,
    ItemsView,
    Iterable,
    Iterator,
    KeysView,
    NoReturn,
    Self,
    ValuesView,
    overload,
)

################################################################################

__all__ = [
    'FunctionType',
    'LambdaType',
    'CodeType',
    'CellType',
    'BuiltinFunctionType',
    'BuiltinMethodType',
    'MethodType',
    'MethodWrapperType',
    'MappingProxyType',
    'GetSetDescriptorType',
    'MemberDescriptorType',
    'MethodDescriptorType',
    'ClassMethodDescriptorType',
    'WrapperDescriptorType',
    'EllipsisType',
    'NoneType',
    'NotImplementedType',
    'GeneratorType',
    'AsyncGeneratorType',
    'CoroutineType',
    'TracebackType',
    'FrameType',
    'ModuleType',
    'UnionType',
    'GenericAlias',
    'SimpleNamespace',
]

################################################################################

# for internal use...

type Objs = tuple[object, ...]
type Strs = tuple[str, ...]
type OptStr = str | None
type OptObjs = Objs | None
type OptDict = dict[str, Any] | None
type AnyDict = dict[str, Any]
type TypeParams = tuple[Any, ...]
type OptCells = tuple[CellType, ...] | None
type OptTraceback = TracebackType | None


def _obj_name(obj: object) -> str:
    cls_name = _cls_name(obj)
    ptr_name = _ptr_name(obj)
    return f"{cls_name} object at {ptr_name}"


def _cls_name(obj: object) -> str:
    return obj.__class__.__name__


def _ptr_name(obj: object) -> str:
    return f'0x{id(obj):10x}'


################################################################################


class PyTypeMeta(type):
    __print_form__: str = ''  # what repr() will print for this type
    __alias_name__: str = ''  # what does core.type.sys call this?
    __source_loc__: bytes = b''  # which file is the PyTypeObject defined in, and what is it called?


class PyType(metaclass=PyTypeMeta):
    """
    Represents a CPython-implemented type. These are all immutable.
    """


################################################################################


class CanSort:
    def __lt__(self, other: object) -> bool: ...
    def __le__(self, other: object) -> bool: ...
    def __eq__(self, other: object) -> bool: ...
    def __ne__(self, other: object) -> bool: ...
    def __gt__(self, other: object) -> bool: ...
    def __ge__(self, other: object) -> bool: ...


class CanEqual:
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...


class CanHash:
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...


class CanCall:
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...


class HasSig:
    __text_signature__: OptStr


class HasModule:
    __doc__: OptStr


class HasName:
    __name__:     str
    __qualname__: str
    __doc__:      OptStr


class HasDerivedName:
    @property
    def __doc__(self) -> OptStr: ...
    @property
    def __name__(self) -> str: ...
    @property
    def __qualname__(self) -> str: ...


class BindsSelf:
    __self__: object


class BindsClass:
    __objclass__: type


################################################################################


class CellType(PyType, CanEqual):
    __print_form__ = 'cell'
    __alias_name__ = 'CellT'
    __source_loc__ = b'Objects/cellobject.c#PyCell_Type'

    __hash__ = None

    cell_contents: Any

    def __new__(cls, contents: object = ..., /) -> Self: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, value: object, /) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        ptr_name = _ptr_name(self)
        val_name = _obj_name(self.cell_contents)
        return f"<cell at {ptr_name}: {val_name}>"


class CodeType(PyType, CanCall, CanHash):
    __print_form__ = 'code'
    __alias_name__ = 'CodeT'
    __source_loc__ = b'Objects/codeobject.c#PyCode_Type'

    # methods:
    def __new__(
        cls,
        argcount: int,
        posonlyargcount: int,
        kwonlyargcount: int,
        nlocals: int,
        stacksize: int,
        flags: int,
        codestring: bytes,
        constants: Objs,
        names: Strs,
        varnames: Strs,
        filename: str,
        name: str,
        qualname: str,
        firstlineno: int,
        linetable: bytes,
        exceptiontable: bytes,
        freevars: Strs = ...,
        cellvars: Strs = ...,
        /,
    ) -> Self: ...

    def replace(
        self,
        *,
        co_argcount: int = -1,
        co_posonlyargcount: int = -1,
        co_kwonlyargcount: int = -1,
        co_nlocals: int = -1,
        co_stacksize: int = -1,
        co_flags: int = -1,
        co_firstlineno: int = -1,
        co_code: bytes = ...,
        co_consts: Objs = ...,
        co_names: Strs = ...,
        co_varnames: Strs = ...,
        co_freevars: Strs = ...,
        co_cellvars: Strs = ...,
        co_filename: str = ...,
        co_name: str = ...,
        co_qualname: str = ...,
        co_linetable: bytes = ...,
        co_exceptiontable: bytes = ...,
    ) -> Self: ...

    def __sizeof__(self) -> int: ...
    def __co_lines__(self): ...
    def co_branches(self): ...
    def co_positions(self): ...
    def _varname_from_oparg(self): ...

    __replace__ = replace

    # members:
    co_argcount: int
    co_posonlyargcount: int
    co_kwonlyargcount: int
    co_stacksize: int
    co_flags: int
    co_nlocals: int
    co_consts: Objs
    co_names: Strs
    co_filename: str
    co_name: str
    co_qualname: str
    co_firstlineno: int
    co_linetable: bytes
    co_exceptiontable: bytes
    co_lnotab: bytes
    _co_code_adaptive: bool

    # marked as "backward compat" in CPython source, whatever that means:
    co_varnames: Strs
    co_cellvars: Strs
    co_freevars: Strs
    co_code: bytes

    # from CanCall
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # from CanHash
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        code_name = self.co_name
        ptr_name = _ptr_name(self)
        file_name = repr(self.co_filename)
        line_name = self.co_firstlineno
        return f"<code object {code_name} at {ptr_name}, file {file_name}, line {line_name}>"


################################################################################
# inspect._signature_fromstr


class IsFunction(CanCall, HasName, HasModule, CanHash):
    pass


class FunctionType(PyType, IsFunction):
    __print_form__ = 'function'
    __alias_name__ = 'FunctionT'
    __source_loc__ = b'Objects/funcobject.c#FunctionTion_Type'

    def __new__(
        cls,
        code: CodeType,
        globals: AnyDict,
        name: OptStr = None,
        argdefs: Objs | None = None,
        closure: OptCells = None,
        kwdefaults: OptDict = None,
    ): ...

    __closure__:     OptCells
    __globals__:     AnyDict
    __module__:      str      # from HasModule
    __builtins__:    AnyDict
    __code__:        CodeType
    __defaults__:    OptObjs
    __kwdefaults__:  OptDict
    __dict__:        dict
    __annotations__: AnyDict  # type: ignore
    __type_params__: TypeParams
    __name__:        str      # from HasName
    __qualname__:    str      # from HasName
    __doc__:         OptStr   # from HasName

    # from CanCall
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # from CanHash
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        func_name = self.__name__
        ptr_name = _ptr_name(self)
        return f"<function {func_name} at {ptr_name}>"


LambdaType = FunctionType


class BuiltinFunctionType(PyType, IsFunction, BindsSelf, HasSig):
    __print_form__ = 'builtin_function_or_method'
    __alias_name__ = 'BoundMethodOrFuncC'
    __source_loc__ = b'Objects/methodobject.c#PyCFunction_Type'

    __self__:           object | ModuleType  # from IsBound
    __name__:           str                  # from HasName
    __qualname__:       str                  # from HasName
    __doc__:            str                  # from HasName
    __module__:         str                  # from HasModule
    __text_signature__: OptStr               # from HasSig

    # NOTE:
    # `__self__ = builtins` for  `len`
    # `__self__ = int` for `int.__new__`

    # from CanCall
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # from CanHash
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        func_name = self.__name__
        if isinstance(self.__self__, ModuleType):
            return f"<built-in function {func_name}>"
        self_name = _obj_name(self.__self__)
        return f"<built-in method {func_name} of {self_name}>"


################################################################################

class BuiltinMethodType(BuiltinFunctionType):
    __print_form__ = 'builtin_method'
    __alias_name__ = 'BoundMethodC'
    __source_loc__ = b'Objects/methodobject.c#PyCMethod_Type'

    __self__:           object  # from IsBound
    __name__:           str     # from HasName
    __qualname__:       str     # from HasName
    __doc__:            str     # from HasName
    __module__:         str     # from HasModule
    __text_signature__: OptStr  # from HasSig

    # from CanCall
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # from CanHash
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        func_name = self.__name__
        self_name = _obj_name(self.__self__)
        return f"<built-in method {func_name} of {self_name}>"


################################################################################


class IsMethod(CanCall, HasDerivedName, CanHash):
    pass


class MethodType(PyType, IsMethod, BindsSelf):
    """Stores a python-implemented INSTANCE method and the OBJECT it is bound to.

    Example:
        `my_object.my_instance_method`
    """

    __print_form__ = 'method'
    __alias_name__ = 'BoundMethodT'
    __source_loc__ = b'Objects/classobject.c#PyInstanceMethod_Type'

    __self__: object         # from BindsSelf
    __func__: FunctionType

    def __new__(cls, fn: Callable): ...

    # obtained from inner function
    @property
    def __closure__(self) -> OptCells: ...
    @property
    def __defaults__(self) -> OptObjs: ...

    # from CanCall
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # from HasDerivedName
    @property
    def __doc__(self) -> OptStr: ...
    @property
    def __name__(self) -> str: ...
    @property
    def __qualname__(self) -> str: ...

    # from CanHash
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        meth_name = self.__func__.__name__
        self_name = _obj_name(self.__self__)
        return f"<bound method {meth_name} of <{self_name}>>"


class MethodWrapperType(PyType, IsMethod, BindsSelf, HasSig):
    """Stores the name of a POLYMORPHIC OPERATION and the OBJECT it is bound
    to. The partially-bound version of this (bound to class, but not instance)
    is a WrapperDescriptorType.

    Explanation:
        POLYMORPHIC operations corresponding to built functions `len`, `hash`,
        `str`, `repr`, and `iter`, have single C implementations that do their
        own dispatch. This type is used to store the intended operation AND
        the object it will operate on.

        Bound MONOMORPHIC instance methods often use `BuiltinFunctionType`, which
        can also represent bound methods, e.g. `[].append`.

    Example:
        `[].__len__`
        `().__str__`

    Note:
        MONOMORPHIC instance methods will use `BuiltinFunctionType`, which
        can also represent bound methods, e.g. `[].append`.
    """

    __print_form__ = 'method-wrapper'
    __alias_name__ = 'BoundDunderMethodC'
    __source_loc__ = b'Objects/descrobject.c#_PyMethodWrapper_Type'

    __self__: object            # from BindsSelf
    __text_signature__: OptStr  # from HasSig

    # derived from __self__
    def __objclass__(self) -> type:
        return self.__self__.__class__

    # from CanCall
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # from HasDerivedName
    @property
    def __doc__(self) -> OptStr: ...
    @property
    def __name__(self) -> str: ...
    @property
    def __qualname__(self) -> str: ...

    # from CanHash
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        meth_name = self.__name__
        self_name = _obj_name(self.__self__)
        return f"<method-wrapper '{meth_name}' of {self_name}>"


BuiltinMethodType = BuiltinFunctionType


################################################################################


class IsDescriptor(HasDerivedName, BindsClass, CanHash):
    """Abstract class representing read-only descriptor types."""

    __objclass__: type  # from BindsClass

    def __get__(self, instance: Any, owner: type | None = None, /) -> Any: ...


class IsMutableDescriptor(IsDescriptor):
    """Abstract class representing read-write descriptor types."""

    def __get__(self, instance: Any, owner: type | None = None, /) -> Any: ...
    def __set__(self, instance: Any, value: Any, /) -> None: ...
    def __delete__(self, instance: Any, /) -> None: ...


################################################################################


# properties implemented in C via PyGetSetDef structure, e.g. complex.real, frame.f_locals
class GetSetDescriptorType(PyType, IsMutableDescriptor):
    """Stores the name of an DESCRIPTOR implementation and the CLASS it is for,
    which intercepts get, set, and delete operations on objects of that class
    when the attribute (this thing) is read, written, or changed via the
    owning object.
    """

    __print_form__ = 'getset_descriptor'
    __alias_name__ = 'MutablePropertyC'
    __source_loc__ = b'Objects/object.c#PyGetSetDescr_Type'

    __objclass__: type  # from BindsClass

    # from IsMutableDescriptor
    def __get__(self, instance: Any, owner: type | None = None, /) -> Any: ...
    def __set__(self, instance: Any, value: Any, /) -> None: ...
    def __delete__(self, instance: Any, /) -> None: ...

    # from HasDerivedName
    @property
    def __doc__(self) -> OptStr: ...
    @property
    def __name__(self) -> str: ...
    @property
    def __qualname__(self) -> str: ...

    # from CanHash
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        attr_name = self.__name__
        cls_name = self.__objclass__.__name__
        return f"<attribute '{attr_name}' of '{cls_name}' objects>"


# direct struct member access in C via PyMemberDef, e.g. __weakref__, code.co_name
# faster, but less flexible. Handles slots.
class MemberDescriptorType(PyType, IsMutableDescriptor):
    """Stores the name of a SLOT and the CLASS it is a slot for. It can't be
    called, it is there to satisfy the descriptor protocol to enable slot
    setting and getting to work.

    Example:
        ```
        class HasSlots:
            __slots__ = ('a',)

        HasSlots.a
    """

    __print_form__ = 'slot'
    __alias_name__ = 'SlotPropertyC'
    __source_loc__ = b'Objects/object.c#PyMemberDescr_Type'

    __objclass__: type  # from BindsClass

    # from IsMutableDescriptor
    def __get__(self, instance: Any, owner: type | None = None, /) -> Any: ...
    def __set__(self, instance: Any, value: Any, /) -> None: ...
    def __delete__(self, instance: Any, /) -> None: ...

    # from HasDerivedName
    @property
    def __doc__(self) -> OptStr: ...
    @property
    def __name__(self) -> str: ...
    @property
    def __qualname__(self) -> str: ...

    # from CanHash
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        attr_name = self.__name__
        cls_name = self.__objclass__.__name__
        return f"<slot '{attr_name}' of '{cls_name}' objects>"


################################################################################


class IsMethodDescriptor(IsDescriptor, CanCall, HasSig):
    """Abstract class representing callable descriptor types."""


################################################################################


# bytes.hex, list.append, dict.update
class MethodDescriptorType(PyType, IsMethodDescriptor):
    """Stores the name of C implementation of an INSTANCE method
    and the CLASS it is bound to, and awaits a `self` and arguments.

    Example: `bytes.hex`, where `__objcls__ = hex`.

    The bound equivalent of this is `BuiltinFunctionType` aka `BoundMethodOrFuncC`.
    """

    __print_form__ = 'method_descriptor'
    __alias_name__ = 'UnboundMethodC'
    __source_loc__ = b'Objects/descrobject.c#PyMethodDescr_Type'

    __objclass__: type          # from BindsClass
    __text_signature__: OptStr  # from HasSig

    # from CanCall
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # from IsDescriptor
    def __get__(self, instance: Any, owner: type | None = None, /) -> Any: ...

    # from HasDerivedName
    @property
    def __doc__(self) -> OptStr: ...
    @property
    def __name__(self) -> str: ...
    @property
    def __qualname__(self) -> str: ...

    # from CanHash
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        meth_name = self.__name__
        cls_name = self.__objclass__.__name__
        return f"<method '{meth_name}' of '{cls_name}' objects>"


class ClassMethodDescriptorType(IsMethodDescriptor):
    """Stores the name of a C implementation of an CLASS method AND
    the CLASS it is bound to, and awaits just arguments.

    Example: `bytes.__dict__['fromhex']`, where `__objcls__ = hex`

    There is no unbound version of this!
    """

    __print_form__ = 'classmethod_descriptor'
    __alias_name__ = 'BoundClassMethodC'
    __source_loc__ = b'Objects/descrobject.c#PyClassMethodDescr_Type'

    __objclass__: type          # from BindsClass
    __text_signature__: OptStr  # from HasSig

    # from CanCall
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # from IsDescriptor
    def __get__(self, instance: Any, owner: type | None = None, /) -> Any: ...

    # from HasDerivedName
    @property
    def __doc__(self) -> OptStr: ...
    @property
    def __name__(self) -> str: ...
    @property
    def __qualname__(self) -> str: ...

    # from CanHash
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        meth_name = self.__name__
        cls_name = self.__objclass__.__name__
        return f"<method '{meth_name}' of '{cls_name}' objects>"


class WrapperDescriptorType(IsMethodDescriptor):
    """Stores the name of a POLYMORPHIC OPERATION, and the CLASS it is bound to.
    This awaits an INSTANCE and arguments.

    The fully-bound version of this (bound to a concrete instance rather than
    just the class) is a MethodWrapperType.

    Examples:
        `bytes.__buffer__`
        `object.__init__`
        `object.__lt__`
        `type.__init__`
    """

    __print_form__ = 'wrapper_descriptor'
    __alias_name__ = 'UnboundDunderMethodC'
    __source_loc__ = b'Objects/descrobject.c#PyWrapperDescr_Type'

    __objclass__: type          # from BindsClass
    __text_signature__: OptStr  # from HasSig

    # from CanCall
    def __call__(self, *args: Any, **kwargs: Any) -> Any: ...

    # from IsDescriptor
    def __get__(self, instance: Any, owner: type | None = None, /) -> Any: ...

    # from HasDerivedName
    @property
    def __doc__(self) -> OptStr: ...
    @property
    def __name__(self) -> str: ...
    @property
    def __qualname__(self) -> str: ...

    # from CanHash
    def __hash__(self) -> int: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __ne__(self, other: object) -> bool: ...

    # emulate what str() would do
    def __str__(self) -> str:
        slot_func_name = self.__name__
        cls_name = self.__objclass__.__name__
        return f"<slot wrapper '{slot_func_name}' of '{cls_name}' objects>"


################################################################################


# not a real superclass
class PySingleton(PyType):
    def __init__(self) -> None: ...


class EllipsisType(PySingleton):
    __print_form__ = 'ellipsis'
    __alias_name__ = 'EllipT'
    __source_loc__ = b'Objects/sliceobject.c#PyEllipsis_Type'

    # emulate what str() would do
    def __str__(self) -> str:
        return '...'


class NoneType(PySingleton):
    __print_form__ = 'NoneType'
    __alias_name__ = 'NoneT'
    __source_loc__ = b'Objects/object.c#_PyNone_Type'

    # emulate what str() would do
    def __str__(self) -> str:
        return 'None'


class NotImplementedType(PySingleton):
    __print_form__ = 'NotImplementedType'
    __alias_name__ = 'NotImplT'
    __source_loc__ = b'Objects/object.c#_PyNotImplemented_Type'

    # emulate what str() would do
    def __str__(self) -> str:
        return 'NotImplemented'


################################################################################


class FrameType(PyType):
    __print_form__ = 'frame'
    __alias_name__ = 'FrameT'
    __source_loc__ = b'Objects/frameobject.c#PyFrame_Type'

    # methods
    def __sizeof__(self) -> int: ...
    def clear(self) -> None: ...

    # members
    f_back: Self | None
    f_locals: AnyDict
    f_lineno: int | Any  # writeable
    f_trace: Callable[[Self, str, Any], Any] | None  # writeable
    f_lasti: int
    f_globals: AnyDict
    f_builtins: AnyDict
    f_code: CodeType
    f_trace_opcodes: bool  # writeable
    f_generator: 'GeneratorType | None'

    # getset:
    f_trace_lines: bool


class TracebackType(PyType):
    __print_form__ = 'traceback'
    __alias_name__ = 'TracebackType'
    __source_loc__ = b'Python/Traceback.c#PyTraceBack_Type'

    # methods:
    def __new__(
        cls, tb_next: Self | None, tb_frame: FrameType, tb_lasti: int, tb_lineno: int
    ) -> Self: ...
    def __dir__(self) -> list[str]: ...

    # members:
    tb_frame: FrameType
    tb_lasti: int

    # getset:
    tb_next: Self | None  # writeable
    tb_lineno: int


################################################################################


class CoroutineType(PyType):
    __print_form__ = 'coroutine'
    __alias_name__ = 'CoroutineT'
    __source_loc__ = b'Objects/genobject.c#PyCoro_Type'

    # methods:
    def send(self, arg: Any, /) -> Any: ...
    async def throw(self, typ: BaseException) -> Any: ...

    def close(self) -> NoReturn: ...
    def __sizeof__(self) -> int: ...
    def __class_getitem__(cls, item: Any, /) -> Self: ...

    # getset:
    __name__: str
    __qualname__: str
    cr_running: bool
    cr_await: object | None  # Awaitable or None
    cr_frame: FrameType | None
    cr_suspended: bool
    cr_origin: (
        tuple[tuple[str, int, str], ...] | None
    )  # depends on sys.set_coroutine_origin_tracking_depth


class GeneratorType(PyType):
    __print_form__ = 'generator'
    __alias_name__ = 'GeneratorT'
    __source_loc__ = b'Objects/genobject.c#PyGen_Type'

    # methods:
    def __iter__(self) -> Self: ...
    def __next__(self) -> Any: ...
    def send(self, arg: Any, /) -> Any: ...
    def throw(self, typ: BaseException, /) -> Any: ...
    def close(self) -> NoReturn: ...
    def __sizeof__(self) -> int: ...
    def __class_getitem__(cls, item: Any, /) -> Any: ...

    # getset:
    __name__: str
    __qualname__: str
    gi_yieldfrom: Self | None
    gi_running: bool
    gi_frame: FrameType | None
    gi_suspended: bool
    gi_code: CodeType


class AsyncGeneratorType(PyType):
    __print_form__ = 'async_generator'
    __alias_name__ = 'AGeneratorT'
    __source_loc__ = b'Objects/genobject.c#PyAsyncGen_Type'

    # methods:
    def __aiter__(self) -> Self: ...
    def __anext__(self) -> CoroutineType: ...
    def asend(self, arg: Any, /) -> Any: ...
    async def athrow(self, val: BaseException) -> Any: ...
    def aclose(self) -> NoReturn: ...
    def __sizeof__(self) -> int: ...
    def __class_getitem__(cls, item: Any, /) -> CoroutineType: ...

    # getset:
    __name__: str
    __qualname__: str
    ag_running: bool
    ag_await: object | None  # Awaitable or None
    ag_frame: FrameType | None
    ag_suspended: bool
    ag_code: CodeType


################################################################################


class ModuleSpec:
    """
    Proxy for class implementing importlib.machinery.ModuleSpec, there is no CPython type for it.
    Example implementing type is `_frozen_importlib.ModuleSpec`.
    """

    name: str
    loader: Any
    origin: Any
    submodule_search_locations: list[str]
    loader_state: Any
    cached: OptStr
    parent: str
    has_location: bool


class ModuleLoader:
    """
    Proxy for class implementing importlib.abc.Module, there is no CPython type for it.
    Example implementing type is `_frozen_importlib.ModuleSpec`.
    """

    def create_module(self, spec: ModuleSpec) -> 'ModuleType | None': ...
    def exec_module(self, module: 'ModuleType') -> None: ...


class ModuleType(PyType):
    __print_form__ = 'module'
    __alias_name__ = 'ModuleT'
    __source_loc__ = b'Objects/moduleobject.c#PyFrame_Type'

    # methods:
    def __init__(self, name: str, doc: str | None = ...) -> None: ...
    def __dir__(self) -> dict[str, Any]: ...

    # these are dynamically created and placed in `__dict__`:
    __name__:       str
    __file__:       OptStr     # not necessarily present
    __path__:       list[str]  # not necessarily present
    __package__:    OptStr
    __spec__:       ModuleSpec | None
    __loader__:     ModuleLoader | None
    __doc__:        OptStr
    __cached__:     OptStr     # deprecated, will be removed in 3.15
    __builtins__:   AnyDict  # not necessarily present
    # this has getter/setter but modifies __dict__['__annotations__']
    __annotations_: AnyDict


################################################################################


class UnionType(PyType):
    __print_form__ = 'module'
    __alias_name__ = 'ModuleT'
    __source_loc__ = b'Objects/moduleobject.c#PyModule_Type'

    __args__: Objs

    def __or__(self, value: Any, /) -> Self: ...
    def __ror__(self, value: Any, /) -> Self: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __hash__(self) -> int: ...


################################################################################


class GenericAlias(PyType):
    __print_form__ = 'types.GenericAlias'
    __alias_name__ = 'CPythonGenericAlias'
    __source_loc__ = b'Objects/genericaliasobject.c#PyModule_Type'

    # methods:
    def __new__(cls, origin: type, args: Any) -> Self: ...
    def __getitem__(self, typeargs: Any, /) -> Self: ...
    def __getattr__(self, name: str) -> Any: ...
    def __eq__(self, value: object, /) -> bool: ...
    def __hash__(self) -> int: ...
    def __or__(self, value: Any, /) -> UnionType: ...
    def __ror__(self, value: Any, /) -> UnionType: ...

    # members (readonly):
    __origin__: type
    __args__: Objs
    __unpacked__: bool

    # getset (readonly):
    __parameters__: TypeParams
    __typing_unpacked_tuple_args__: OptObjs


################################################################################


class SimpleNamespace(PyType):
    def __init__(
        self, mapping_or_iterable: Iterable[tuple[str, object]] = (), /, **kwargs: object
    ): ...

    def __repr__(self) -> str: ...
    def __eq__(self, other) -> bool: ...

    def __replace__(self, /, **changes: object) -> None: ...


################################################################################


class MappingProxyType(PyType, CanSort):
    __print_form__ = 'mappingproxy'
    __alias_name__ = 'MapProxyT'
    __source_loc__ = b'Objects/descrobject.c#PyDictProxy_Type'

    __hash__ = None

    # methods:
    def __new__(cls, mapping: Any) -> Self: ...
    def __getitem__(self, key: Any, /) -> Any: ...
    def __iter__(self) -> Iterator[Any]: ...
    def __len__(self) -> int: ...
    def __class_getitem__(cls, item: Any, /) -> GenericAlias: ...
    def __reversed__(self) -> Iterator[Any]: ...
    def __or__(self, value: Any, /) -> dict: ...
    def __ror__(self, value: Any, /) -> dict: ...
    def copy(self) -> dict: ...
    def keys(self) -> KeysView[Any]: ...
    def values(self) -> ValuesView[Any]: ...
    def items(self) -> ItemsView[Any, Any]: ...
    @overload
    def get(self, key: Any, /) -> Any | None: ...
    @overload
    def get(self, key: Any, default: Any, /) -> Any: ...
    def get(self, key: Any, default: Any = None, /) -> Any: ...
