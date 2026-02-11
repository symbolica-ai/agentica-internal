# fmt: off
# ruff: noqa

"""
This is my module, I am going to be warped.
"""

# these should not be included
from pathlib import Path
import pathlib

__all__ = [
    'MyClass',
    'my_object',
    'my_function',
    'MY_CONSTANT',
    'MY_BYTES'
]

class MyClass:
    a: int
    b: str


class MyHiddenClass:
    pass


def my_function():
    pass


my_object = MyClass()

MY_CONSTANT = 99
MY_BYTES = b'0' * 256
