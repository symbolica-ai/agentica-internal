# fmt: off

from typing import Union

from ...cpython.exceptions import get_exception_str, get_exception_bases

from ..data.identifier import set_cls_identifier, get_cls_identifier
from ..system import SYS_EXCEPTIONS, is_sys_exc_class

from .__ import *
from .term import TermPassByValMsg
from .term_resource import SystemResourceMsg, UserResourceMsg, class_to_system_msg

__all__ = [
    'ExceptionMsg',
    'SystemExceptionMsg',
    'StopIterationMsg',
    'UserExceptionMsg',
    'ShallowUserExceptionMsg',
    'DeepUserExceptionMsg',
    'InternalExceptionMsg'
]

################################################################################

if TYPE_CHECKING:
    from .msg_aliases import ClassMsg, ArgsMsg

################################################################################

SystemExceptionT = Union[*SYS_EXCEPTIONS]

################################################################################

class ExceptionMsg(TermPassByValMsg):
    """ABC for messages encoding exceptions *by value* in various ways."""

    type V = BaseException

    def decode(self, dec: DecoderP) -> BaseException: ...

    @classmethod
    def encode_exception(cls, exc: BaseException, enc: EncoderP) -> 'ExceptionMsg':
        _cls = type(exc)

        if _cls is StopIterationMsg:
            # singleton
            msg = StopIterationMsg()

        elif issubclass(_cls, E.WarpError):
            msg = InternalExceptionMsg(str(exc))

        elif is_sys_exc_class(_cls):
            # will decode to a full system exception (by value)
            msg = SystemExceptionMsg.encode_compound(exc, enc)

        elif enc.enc_before(id(type(exc))):
            # will decode to a full virtual exception (by reference)
            msg = DeepUserExceptionMsg.encode_exception(exc, enc)

        elif issubclass(_cls, BaseException):
            # will decode as a once-off class
            msg = ShallowUserExceptionMsg.encode_exception(exc, enc)

        else:
            msg = InternalExceptionMsg(f'Tried to encode non-exception of type {_cls.__qualname__}')

        return msg

################################################################################

class SystemExceptionMsg(ExceptionMsg, tag='sys_exc'):
    """Message describing an instance of a system exception. These are passed by-value."""

    type V = SystemExceptionT

    exc_cls:  'SystemResourceMsg'
    exc_args: 'ArgsMsg | None' = None

    def __shape__(self) -> str:
        return self.exc_cls.sys_name

    def decode(self, dec: DecoderP) -> SystemExceptionT:
        exc_args = dec.dec_sequence(self.exc_args) if self.exc_args else ()
        exc_cls = self.exc_cls.sys_cls
        if issubclass(exc_cls, BaseException):
            return exc_cls(*exc_args)
        return E.RemoteException(*exc_args)

    @classmethod
    def encode_compound(cls, exc: SystemExceptionT, enc: EncoderP) -> 'ExceptionMsg':
        _cls = type(exc)

        assert _cls in SYS_EXCEPTIONS

        if _cls is StopIterationMsg:
            return StopIterationMsg()

        if _cls in (AttributeError, KeyError, ValueError, TypeError, NameError, ImportError, ZeroDivisionError):
            # fast path
            args = exc.args
        else:
            from ..resource.virtual_exception import get_exception_args
            args = get_exception_args(exc)
            if args is None:
                # if we can't extract args, return it as a TransientExceptionMsg,
                # so it at least gets stringified
                return ShallowUserExceptionMsg.encode_exception(exc, enc)

        args_msg = enc.enc_sequence(args) if args else None
        cls_msg = enc.enc_system_resource(_cls)

        return SystemExceptionMsg(cls_msg, args_msg)


################################################################################

# we hardcode this as a singleton, because it is so common

class StopIterationMsg(ExceptionMsg, tag='stop'):

    type V = StopIteration

    exc_cls:  'SystemResourceMsg' = class_to_system_msg(StopIteration)
    exc_args:  None = None

    def decode(self, dec: DecoderP) -> StopIteration:
        return StopIteration()

    @classmethod
    def encode_constant(cls) -> 'StopIterationMsg':
        return StopIterationMsg()


################################################################################

class UserExceptionMsg(ExceptionMsg):
    pass

################################################################################

class ShallowUserExceptionMsg(UserExceptionMsg, tag='shallow_exc'):
    """Message describing an instance of a non-system exception class, but
    where the class has not been encoded before. To avoid serializing
    all class, its args, all its base classes, and potentially incurring a lot
    of expense (as well as opportunities for failure), we instead encode only
    the text of the exception, the name of the class, and its *known* bases.

    Because it hasn't been encoded before, the decoding runtime wouldn't be
    able to literally match against the class anyway, so this optimization
    should be imperceptible in most cases.
    """

    ident:      Identifier           # name of the exception class
    exc_str:    optstr = None        # str(exception)
    exc_bases: 'Tup[ClassMsg]' = ()  # the closest *known* exception classes this derives from

    def __shape__(self) -> str:
        return self.ident.__short_str__()

    def decode(self, dec: DecoderP) -> BaseException:

        ident = self.ident

        key = self.ident.fullname
        cls = SHALLOW_EXC_CLS_CACHE.get(key)
        if cls is None:
            bases = tuple(map(dec.dec_class, self.exc_bases)) or (Exception,)
            assert all(issubclass(base, BaseException) for base in bases)
            cls = create_shallow_exception_class(ident, bases)
            SHALLOW_EXC_CLS_CACHE[key] = cls

        exc_str = self.exc_str
        return cls(exc_str) if exc_str else cls()

    @classmethod
    def encode_exception(cls, exc: BaseException, enc: EncoderP) -> 'ExceptionMsg':

        _cls = type(exc)

        ident = get_cls_identifier(_cls)
        exc_str = get_exception_str(exc)

        # collect those bases that we must inherit from in order to satisfy
        # any isinstance checks that the remote side has access to
        bases = get_exception_bases(_cls, lambda c: is_sys_exc_class(c) or bool(enc.enc_before(c)))
        if Exception in bases: bases.remove(Exception)
        bases_msg = tuple(map(enc.enc_class, bases))

        return ShallowUserExceptionMsg(ident=ident, exc_str=exc_str, exc_bases=bases_msg)

################################################################################

SHALLOW_EXC_CLS_CACHE: dict[str, type[BaseException]] = {}

SHALLOW_EXC_CLS_METHODS = {
    '__new__':  BaseException.__new__,
    '__str__':  BaseException.__str__,
    '__repr__': BaseException.__repr__
}

def create_shallow_exception_class(ident: Identifier, bases: tuple[type, ...]) -> type[BaseException]:
    try:
        cls = type(ident.name, bases, SHALLOW_EXC_CLS_METHODS)
        # ensure the BaseException.__new__ works for these bases:
        cls()
        cls('msg')
    except:
        cls = type(ident.name, (Exception,), SHALLOW_EXC_CLS_METHODS)
    assert issubclass(cls, BaseException)
    set_cls_identifier(cls, ident)
    return cls


################################################################################

class DeepUserExceptionMsg(UserExceptionMsg, tag='deep_exc'):

    exc_ref: 'UserResourceMsg'   # the exception *by reference*
    exc_str: optstr = None      # None if the msg IS args[0]

    def decode(self, dec: DecoderP) -> BaseException:
        from ..resource.handle import get_handle
        exc_str = self.exc_str
        try:
            exc = dec.dec_resource(self.exc_ref)
            assert isinstance(exc, BaseException)
            if exc_str is not None and (h := get_handle(exc)) and not hasattr(h, '_str'):
                h._str = exc_str
            return exc
        except:
            return E.RemoteException(exc_str)

    @classmethod
    def encode_exception(cls, exc: BaseException, enc: EncoderP) -> 'ExceptionMsg':

        try:
            # encode the exception by-reference
            exc_ref = enc.enc_resource(exc)
            assert isinstance(exc_ref, UserResourceMsg)
        except:
            return ShallowUserExceptionMsg.encode_exception(exc, enc)

        exc_str = get_exception_str(exc)
        return DeepUserExceptionMsg(exc_ref, exc_str)

################################################################################

class InternalExceptionMsg(ExceptionMsg, tag='internal_exc'):
    """Message encoding an internal exception or error condition."""

    error: str

    def decode(self, dec: DecoderP) -> BaseException:
        return RuntimeError(f'Internal error: {self.error}')


MAX_MSG_LEN = 8192
