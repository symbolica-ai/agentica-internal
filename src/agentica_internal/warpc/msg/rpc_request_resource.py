# fmt: off

from .__ import *
from .rpc_request import RequestMsg


__all__ = [
    'ResourceRequestMsg',
    'ResourceNewMsg',
    'ResourceCallRequestMsg',
    'ResourceCallFunctionMsg',
    'ResourceCallMethodMsg',
    'ResourceCallSystemMethodMsg',
    'ResourceAttrRequestMsg',
    'ResourceHasAttrMsg',
    'ResourceGetAttrMsg',
    'ResourceSetAttrMsg',
    'ResourceDelAttrMsg',
]


################################################################################

if TYPE_CHECKING:
    from ..request.request_resource import *
    from .msg_aliases import *
    from .term import TermMsg
    from .term_resource import SystemResourceMsg

################################################################################

class ResourceRequestMsg(RequestMsg):
    """ABC for messages that describe requests of virtual resources.

    These correspond 1-to-1 with the class hierarchy in `warpc.request`.
    """

    LOG_TAGS = 'RSRC'

    def decode(self, dec: DecoderP) -> 'ResourceRequest': ...


################################################################################

class ResourceCallRequestMsg(ResourceRequestMsg):
    """ABC for function-call-like requests; these have a pos and key field."""
    ...


################################################################################

class ResourceNewMsg(ResourceCallRequestMsg, tag='new'):
    """Describes a call to create an instance of a virtualized class."""

    cls: 'ClassMsg'
    pos: 'ArgsMsg' = ()
    key: 'KwargsMsg' = {}

    def __shape__(self) -> str:
        return self.cls.shape

    def decode(self, dec) -> 'ResourceNew':
        from ..request.request_resource import ResourceNew
        return ResourceNew(
            dec.dec_local_resource(self.cls),
            dec.dec_args(self.pos),
            dec.dec_kwargs(self.key),
        )


################################################################################

class ResourceCallFunctionMsg(ResourceCallRequestMsg, tag='call'):
    """Describes a call to a function."""

    fun: 'FunctionMsg'
    pos: 'ArgsMsg' = ()
    key: 'KwargsMsg' = {}

    def __shape__(self) -> str:
        return self.fun.shape

    def decode(self, dec) -> 'ResourceCallFunction':
        from ..request.request_resource import ResourceCallFunction
        return ResourceCallFunction(
            dec.dec_local_resource(self.fun),
            dec.dec_args(self.pos),
            dec.dec_kwargs(self.key),
        )


################################################################################

class ResourceCallMethodMsg(ResourceCallRequestMsg, tag='callmethod'):
    """Describes a call to a named method of an object."""

    obj: 'ObjectMsg'
    mth:  Name
    pos: 'ArgsMsg' = ()
    key: 'KwargsMsg' = {}

    def __shape__(self) -> str:
        return f'{self.obj.shape},{self.mth!r}'

    def decode(self, dec) -> 'ResourceCallMethod':
        from ..request.request_resource import ResourceCallMethod
        return ResourceCallMethod(
            dec.dec_local_resource(self.obj),
            self.mth,
            dec.dec_args(self.pos),
            dec.dec_kwargs(self.key),
        )


################################################################################

class ResourceCallSystemMethodMsg(ResourceCallRequestMsg, tag='callsys'):
    """Describes a call like `hash(obj)` or `str(obj)` that invokes a special
    dunder method on the object."""

    obj: 'ObjectMsg'
    fun: 'SystemResourceMsg'

    def __shape__(self) -> str:
        return f'{self.obj.shape}, {self.fun.shape}'

    def decode(self, dec) -> 'ResourceCallSystemMethod':
        from ..request.request_resource import ResourceCallSystemMethod
        return ResourceCallSystemMethod(
            dec.dec_resource(self.obj),
            dec.dec_system_resource(self.fun),
        )


################################################################################

class ResourceAttrRequestMsg(ResourceRequestMsg):
    """ABC for request messages referring to attributes."""

    obj: 'ObjectMsg'
    attr: str | tuple[str, ...]

    def __shape__(self) -> str:
        return f'{self.obj.shape},{self.attr!r}'


################################################################################

class ResourceHasAttrMsg(ResourceAttrRequestMsg, tag='hasattr'):

    def decode(self, dec) -> 'ResourceHasAttr':
        from ..request.request_resource import ResourceHasAttr
        return ResourceHasAttr(
            dec.dec_local_resource(self.obj),
            self.attr,
        )


################################################################################

class ResourceGetAttrMsg(ResourceAttrRequestMsg, tag='getattr'):

    def decode(self, dec) -> 'ResourceGetAttr':
        from ..request.request_resource import ResourceGetAttr
        return ResourceGetAttr(
            dec.dec_local_resource(self.obj),
            self.attr,
        )


################################################################################

class ResourceDelAttrMsg(ResourceAttrRequestMsg, tag='delattr'):

    def decode(self, dec) -> 'ResourceDelAttr':
        from ..request.request_resource import ResourceDelAttr
        return ResourceDelAttr(
            dec.dec_local_resource(self.obj),
            self.attr,
        )


################################################################################

class ResourceSetAttrMsg(ResourceAttrRequestMsg, tag='setattr'):

    val: 'TermMsg'

    def decode(self, dec) -> 'ResourceSetAttr':
        from ..request.request_resource import ResourceSetAttr
        return ResourceSetAttr(
            dec.dec_local_resource(self.obj),
            self.attr,
            dec.dec_any(self.val),
        )
