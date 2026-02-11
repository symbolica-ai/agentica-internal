# fmt: off

from .__ import *
from .base import Request, ResultCoro


__all__ = [
    'ResourceRequest',
    'ResourceNew',
    'ResourceCallRequest',
    'ResourceCallFunction',
    'ResourceCallMethod',
    'ResourceCallSystemMethod',
    'ResourceAttrRequest',
    'ResourceGetAttr',
    'ResourceHasAttr',
    'ResourceDelAttr',
    'ResourceSetAttr',
    'GENERIC_RESOURCE_ERROR'
]


################################################################################

class ResourceRequest(Request, ABC):
    """
    ABC for a fully decoded request on a resource.

    It can be executed via `.execute` or `.execute_async` methods.

    It can be encoded to a `ResourceRequestMsg` via `.encode`.

    Instances of some subclasses can have the `async_` slot set, which communicates
    the intent for how they should be executed. This slot is only present on those
    requests for which this makes sense, preventing misuse.
    """

    __slots__ = __match_args__ = ()

    ############################################################################

    @abstractmethod
    def encode(self, codec: 'EncoderP') -> 'ResourceRequestMsg':
        """
        Encode a locally expressed resource request (in which typically the first
        argument is a remote resource virtualized locally) into a wire message.
        """
        ...

    ############################################################################

    def execute(self) -> Result:
        """
        Executes a decoded remote resource request immediately, wrapping the
        result in a Result.This happens through `__execute__`, which actually
        does the operation without worrying about catching exceptions.
        """
        try:
            value = self.__execute__()
            return Result.good(value)
        except BaseException as e:
            return Result.bad(e)

    @abstractmethod
    def __execute__(self) -> Any: ...

    ############################################################################

    def execute_async(self) -> ResultCoro:
        """
        Executes a decoded remote request, but not immediately: defers the
        creation of the Result of the execution via a coroutine function.

        This coroutine function will run the underlying exec, assume it *returns*
        an awaitable result (e.g. a coroutine object), await this, and then wrap
        the output in a Result.

        This is called by `Frame.exec_incoming_request_task`.
        """
        if self.is_sync:
            async def execute() -> Result:
                return self.execute()
        else:
            async def execute() -> Result:
                try:
                    awaitable = self.__execute__()
                    value = await awaitable
                    return Result.good(value)
                except BaseException as e:
                    return Result.bad(e)

        # ensure the coroutine object has a name that matches the underlying
        # resource
        coro = execute()
        coro.__qualname__ = coro.__name__ = self.async_name()
        return coro

    ############################################################################

    def hook_key(self) -> A.Hashable: ...


################################################################################

class ResourceNew(ResourceRequest):
    __slots__ = __match_args__ = 'cls', 'pos', 'key'

    cls: type
    pos: ArgsT
    key: KwargsT

    def __init__(self, cls: type, pos: ArgsT = (), key: KwargsT = {}) -> None:
        self.cls = cls
        self.pos = pos
        self.key = key

    def __execute__(self):
        return self.cls(*self.pos, **self.key)

    def encode(self, enc) -> 'ResourceNewMsg':
        from ..msg.rpc_request_resource import ResourceNewMsg
        return ResourceNewMsg(
            enc.enc_remote_resource(self.cls),
            enc.enc_args(self.pos),
            enc.enc_kwargs(self.key)
        )

    def hook_key(self):
        return 'new'


################################################################################

class ResourceCallRequest(ResourceRequest, ABC):
    __slots__ = __match_args__ = 'pos', 'key', 'async_mode'


################################################################################

class ResourceCallFunction(ResourceCallRequest):
    __slots__ = __match_args__ = 'fun', 'pos', 'key', 'async_mode'

    fun: Callable
    pos: ArgsT
    key: KwargsT

    def __init__(self, fun: Callable, pos: ArgsT = (), key: KwargsT = {}) -> None:
        self.fun = fun
        self.pos = pos
        self.key = key

    def __execute__(self):
        return self.fun(*self.pos, **self.key)

    def async_name(self):
        fun_name = getattr(self.fun, '__qualname__')
        return fun_name

    def print(self):
        P.nprint("ResourceCallFunction(")
        P.nprint("FUN", self.fun)
        for i, v in enumerate(self.pos):
            P.nprint("POS", i, v)
        for k, v in self.key.items():
            P.nprint("KEY", k, v)
        P.nprint(")")

    def encode(self, enc) -> 'ResourceCallFunctionMsg':
        from ..msg.rpc_request_resource import ResourceCallFunctionMsg
        return ResourceCallFunctionMsg(
            enc.enc_remote_resource(self.fun),
            enc.enc_args(self.pos),
            enc.enc_kwargs(self.key)
        )

    def hook_key(self):
        return 'call'


################################################################################

class ResourceCallMethod(ResourceCallRequest):
    __slots__ = __match_args__ = 'obj', 'mth', 'pos', 'key', 'async_mode'

    obj: object
    mth: str
    pos: ArgsT
    key: KwargsT

    def __init__(self, obj: object, meth: str, pos: ArgsT = (), key: KwargsT = {}) -> None:
        self.obj = obj
        self.mth = meth
        self.pos = pos
        self.key = key

    def __execute__(self):
        fun = getattr(self.obj, self.mth)
        return fun(*self.pos, **self.key)

    def async_name(self):
        cls_name = type(self).__qualname__
        mth_name = self.mth
        return f'{cls_name}.{mth_name}'

    def encode(self, enc) -> 'ResourceCallMethodMsg':
        from ..msg.rpc_request_resource import ResourceCallMethodMsg
        return ResourceCallMethodMsg(
            enc.enc_remote_resource(self.obj),
            self.mth,
            enc.enc_args(self.pos),
            enc.enc_kwargs(self.key)
        )

    def hook_key(self):
        return 'call_method', self.mth


################################################################################

class ResourceCallSystemMethod(ResourceCallRequest):
    __slots__ = __match_args__ = 'fun', 'obj', 'async_mode'

    obj: object
    fun: Callable

    def __init__(self, obj: object, fun: Callable):
        self.obj = obj
        self.fun = fun

    def async_name(self):
        cls_name = type(self).__qualname__
        fun_name = getattr(self.fun, '__name__')
        return f'{fun_name}(<{cls_name}>)'

    def __execute__(self):
        return self.fun(self.obj)

    def encode(self, enc) -> 'ResourceCallSystemMethodMsg':
        from ..msg.rpc_request_resource import ResourceCallSystemMethodMsg
        return ResourceCallSystemMethodMsg(
            enc.enc_remote_resource(self.obj),
            enc.enc_system_resource(self.fun),
        )

    def hook_key(self):
        return self.fun



################################################################################

class ResourceAttrRequest(ResourceRequest, ABC):
    __slots__ = __match_args__ = 'obj', 'attr',

    obj:  object
    attr: str | tuple[str, ...]


################################################################################

class ResourceHasAttr(ResourceAttrRequest):
    __slots__ = __match_args__ = 'obj', 'attr',

    def __init__(self, obj: object, attr: str):
        if type(attr) not in (str, tuple):
            bad_attr(attr)
        self.obj = obj
        self.attr = attr

    def __execute__(self):
        obj = self.obj
        attr = self.attr
        if isinstance(attr, tuple):
            return tuple(hasattr(obj, a) for a in attr)
        else:
            return hasattr(obj, self.attr)

    def encode(self, enc) -> 'ResourceHasAttrMsg':
        from ..msg.rpc_request_resource import ResourceHasAttrMsg
        return ResourceHasAttrMsg(
            enc.enc_remote_resource(self.obj),
            self.attr,
        )

    def hook_key(self):
        return hasattr


################################################################################

class ResourceGetAttr(ResourceAttrRequest):
    __slots__ = __match_args__ = 'obj', 'attr',

    def __init__(self, obj: object, attr: str | tuple[str, ...]):
        if type(attr) not in (str, tuple):
            bad_attr(attr)
        self.obj = obj
        self.attr = attr

    def __execute__(self):
        obj = self.obj
        attr = self.attr
        if isinstance(attr, tuple):
            return tuple(getattr(obj, a, FIELD_ABSENT) for a in attr)
        else:
            return getattr(obj, self.attr)

    def encode(self, enc) -> 'ResourceGetAttrMsg':
        from ..msg.rpc_request_resource import ResourceGetAttrMsg
        return ResourceGetAttrMsg(
            enc.enc_remote_resource(self.obj),
            self.attr,
        )

    def hook_key(self):
        return getattr


################################################################################

class ResourceDelAttr(ResourceAttrRequest):
    __slots__ = __match_args__ = 'obj', 'attr',

    def __init__(self, obj: object, attr: str | tuple[str, ...]):
        if type(attr) not in (str, tuple):
            bad_attr(attr)
        self.obj = obj
        self.attr = attr

    def __execute__(self):
        obj = self.obj
        attr = self.attr
        if isinstance(attr, tuple):
            for a in attr:
                delattr(obj, a)
        else:
            delattr(obj, attr)

    def encode(self, enc) -> 'ResourceDelAttrMsg':
        from ..msg.rpc_request_resource import ResourceDelAttrMsg
        return ResourceDelAttrMsg(
            enc.enc_remote_resource(self.obj),
            self.attr,
        )

    def hook_key(self):
        return delattr


################################################################################

class ResourceSetAttr(ResourceAttrRequest):
    __slots__ = __match_args__ = 'obj', 'attr', 'val',

    obj: object
    attr: str
    val: Any

    def __init__(self, obj: object, attr: str | tuple[str, ...], val: Any):
        if type(attr) not in (str, tuple):
            bad_attr(attr)
        self.obj = obj
        self.attr = attr
        self.val = val

    def __execute__(self):
        obj = self.obj
        attr = self.attr
        val = self.val
        if isinstance(attr, tuple):
            assert isinstance(val, tuple)
            for a, v in zip(attr, val):
                setattr(obj, a, v)
        else:
            setattr(obj, attr, val)

    def encode(self, enc) -> 'ResourceSetAttrMsg':
        from ..msg.rpc_request_resource import ResourceSetAttrMsg
        return ResourceSetAttrMsg(
            enc.enc_remote_resource(self.obj),
            self.attr,
            enc.enc_any(self.val),
        )

    def hook_key(self):
        return setattr


################################################################################


def bad_attr(attr) -> NoReturn:
    raise TypeError(f'attribute name must be a string, not {f_object(attr)}')


GENERIC_RESOURCE_ERROR = Result.bad(RuntimeError('resource no longer available'))
