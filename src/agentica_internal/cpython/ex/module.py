import atexit

__all__ = [
    'ex_function',
    'ex_generator_fn',
    'ex_generator',
    'ex_async_generator',
    'ex_async_generator_fn',
    'ex_coroutine_fn',
    'ex_coroutine',
    'ex_code',
    'ex_cell',
    'ex_object',
    'ex_slot_object',
    'ex_static_method',
    'ex_bound_class_method',
    'ex_mapping_proxy',
    'ex_property',
    'ex_slot_property',
    'ex_unbound_class_method',
    'ex_unbound_method',
    'ex_bound_method',
    'ex_bound_super_method',
    'ex_exception',
    'ex_traceback',
    'ex_frame',
    'ex_type_alias',
    'ex_union',
    'ex_generic_alias',
    'ex_builtin_function',
    'ex_builtin_method',
    'ex_class_method_descriptor',
    'ex_get_set_descriptor',
    'ex_method_descriptor',
    'ex_method_wrapper',
    'ex_singleton',
    'ex_wrapper_descriptor',
]  # noqa

################################################################################


def ex_function(x: int, y: bool = True, *args, **kwargs) -> float:
    """ex_function docstring"""
    return 1


def ex_generator_fn():
    """ex_generator_fn docstring"""
    yield 1


async def ex_async_generator_fn():
    """ex_async_generator_fn docstring"""
    yield 1


async def ex_coroutine_fn():
    """ex_coroutine_fn docstring"""
    pass


################################################################################

ex_async_generator = ex_async_generator_fn()
ex_generator = ex_generator_fn()
ex_coroutine = ex_coroutine_fn()

atexit.register(lambda: ex_coroutine.close())

################################################################################

ex_code = ex_function.__code__


def ex_outer_capturing_fn():
    """ex_outer_capturing_fn docstring"""
    value = 1

    def ex_inner_capturing_fn():
        """ex_inner_capturing_fn docstring"""
        nonlocal value

    return ex_inner_capturing_fn.__closure__[0]  # type: ignore


ex_cell = ex_outer_capturing_fn()

################################################################################


class ExClass:
    """ExClass docstring"""

    x: int

    def __init__(self):
        self.x = 1
        self.y = True

    @property
    def ex_instance_prop(self) -> int:
        """ExClass.ex_instance_prop docstring"""
        return self.x

    def ex_instance_method(self, arg1: str) -> int:
        """ExClass.ex_instance_method docstring"""
        return self.x + len(arg1) + 1

    @staticmethod
    def ex_static_method(arg1: str) -> int:
        """ExClass.ex_static_method docstring"""
        return len(arg1) + 1

    @classmethod
    def ex_class_method(cls, arg1: str) -> int:
        """ExClass.ex_class_method docstring"""
        return len(cls.__name__) + len(arg1) + 1


class ExSlotClass:
    """ExSlotClass docstring"""

    __slots__ = (
        'slot1',
        'slot2',
    )


class ExException(Exception):
    """ExException docstring"""

    pass


################################################################################

ex_object = ExClass()
ex_slot_object = ExSlotClass()
ex_static_method = ExClass.ex_static_method
ex_bound_class_method = ExClass.ex_class_method
ex_mapping_proxy = ExClass.__dict__
ex_property = ExClass.ex_instance_prop
ex_slot_property = ExSlotClass.slot1  # type: ignore
ex_unbound_class_method = ex_mapping_proxy['ex_class_method']
ex_unbound_method = ex_mapping_proxy['ex_instance_method']
ex_bound_method = ex_object.ex_instance_method
ex_bound_super_method = ex_object.__str__

################################################################################

try:
    raise ExException(1)
except ExException as exc:
    ex_exception = exc
    ex_traceback = exc.__traceback__
    ex_frame = exc.__traceback__.tb_frame  # type: ignore

################################################################################

type ex_type_alias = ExClass | str

ex_union = ExClass | str

ex_generic_alias = list[ExClass]

################################################################################

# builtin function where `__self__ = builtins`
ex_builtin_function = len

# builtin function where `__self__ = int`
ex_builtin_method = int.__new__

ex_class_method_descriptor = bytes.__dict__['fromhex']

ex_get_set_descriptor = type(ex_function).__code__  # type: ignore

# bound class method of an CPython object
ex_method_descriptor = bytes.hex

# unbound instance method of an CPython object
ex_wrapper_descriptor = bytes.__buffer__

# bound instance method of an CPython object
ex_method_wrapper = bytes().__buffer__

ex_member_descriptor = range.start

################################################################################

ex_singleton = NotImplemented
