import pytest

from agentica_internal.warpc.msg.term_exception import ShallowUserExceptionMsg, DeepUserExceptionMsg, SystemExceptionMsg
from conftest import *


@pytest.mark.asyncio
async def test_warp_system_exceptions(pipe: Pipe, catcher):

    def raises(cls: type[BaseException]):
        err = cls(1, 2, 3)
        err.extra = 5
        raise err

    raises_b = await pipe(raises)

    for cls in [KeyError, ValueError, AttributeError, RuntimeError, NameError]:
        error = catch(raises_b, cls)
        msg = pipe.last_event.raised_exception_msg()
        assert isinstance(msg, SystemExceptionMsg)

        assert is_real(error)
        assert type(error) is cls, f"{type(error)=}"
        assert error.args == (1, 2, 3)
        assert not hasattr(error, 'extra')


@pytest.mark.asyncio
async def test_warp_user_exception_shallow(pipe: Pipe):
    class UserException(RuntimeError): pass

    def raises(): raise UserException('xyz')

    raises_b = await pipe(raises)

    error = catch(raises_b)
    msg = pipe.last_event.raised_exception_msg()
    assert isinstance(msg, ShallowUserExceptionMsg)

    cls = type(error)
    assert cls is not UserException
    assert cls.__name__ == 'UserException'
    assert issubclass(cls, RuntimeError)

    assert is_real(error)
    assert str(error) == 'xyz'
    assert repr(error) == "UserException('xyz')"
    assert isinstance(error, RuntimeError)


@pytest.mark.asyncio
async def test_warp_user_exception_deep(pipe: Pipe):
    class UserException(RuntimeError): pass

    def raises(): raise UserException('xyz')

    # send the exception class first so that deep is chosen
    UserExceptionB = await pipe(UserException)
    raises_b = await pipe(raises)

    error = catch(raises_b)
    msg = pipe.last_frame.raised_exception_msg()
    assert isinstance(msg, DeepUserExceptionMsg)

    cls = type(error)
    assert cls is UserExceptionB
    assert cls is not UserException
    assert cls.__name__ == 'UserException'
    assert issubclass(cls, RuntimeError)

    assert is_virtual(error)
    assert str(error) == 'xyz'
    assert repr(error) == "UserException('xyz')"
    assert isinstance(error, RuntimeError)
