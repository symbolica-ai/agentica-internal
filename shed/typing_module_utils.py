"""
This a hand-curated typeshed file for the builtin `typing` module, specifically non-exported implementation functions.
"""

from intro.shed.typing_module import META, _sentinel

####################################################################################################


def _idfunc[X](arg: X, *args, **kwargs) -> X:
    return arg


####################################################################################################


def _should_unflatten_callable_args(typ, args):
    """
    Internal helper for munging collections.abc.Callable's __args__.

    The canonical representation for a Callable's __args__ flattens the
    argument types, see https://github.com/python/cpython/issues/86361.

    For example::

        >>> import collections.abc
        >>> from typing import ParamSpec
        >>> P = ParamSpec('P')
        >>> collections.abc.Callable[[int, int], str].__args__ == (int, int, str)
        True
        >>> collections.abc.Callable[P, str].__args__ == (P, str)
        True

    As a result, if we need to reconstruct the Callable from its __args__,
    we need to unflatten it.
    """


####################################################################################################


def _type_repr(obj) -> str:
    """
    Return the repr() of an object, special-casing types (internal helper).

    If obj is a type, we return a shorter version than the default
    type.__repr__, based on the module and qualified name, which is
    typically enough to uniquely identify a type.  For everything
    else, we fall back on repr(obj).
    """
    ...


####################################################################################################


def _collect_type_parameters(
    args, *, enforce_default_ordering: bool = True
) -> tuple[META.TypeParam]:
    """
    Collect all type parameters in args
    in order of first appearance (lexicographic order).

    For example::

        >>> from collections.abc import Callable
        >>> from typing import ParamSpec, TypeVar, _collect_type_parameters
        >>> P = ParamSpec('P')
        >>> T = TypeVar('T')
        >>> _collect_type_parameters((T, Callable[P, T]))
        (~T, ~P)
    """
    ...


####################################################################################################


def _check_generic_specialization(cls, arguments):
    """
    Check correct count for parameters of a generic cls (internal helper).

    This gives a nice error message in case of count mismatch.
    """


####################################################################################################


def _unpack_args(*args): ...
def _deduplicate(params, *, unhashable_fallback=False): ...
def _deduplicate_unhashable(unhashable_params): ...
def _compare_args_orderless(first_args, second_args): ...


####################################################################################################


def _remove_dups_flatten(parameters):
    """
    Internal helper for Union creation and substitution.

    Flatten Unions among parameters, then remove duplicates.
    """


####################################################################################################


def _flatten_literal_params(parameters):
    """
    Internal helper for Literal creation: flatten Literals among parameters."""


####################################################################################################


def _tp_cache(func=None, /, *, typed=False):
    """
    Internal wrapper caching __getitem__ of generic types.

    For non-hashable arguments, the original function is used as a fallback.
    """


####################################################################################################


def _eval_type(t, globalns, localns, type_params=_sentinel, *, recursive_guard=frozenset()): ...


####################################################################################################


def _is_unpacked_typevartuple(x) -> bool: ...


def _is_typevar_like(x) -> bool: ...


def _typevar_subst(self, arg): ...


def _typevartuple_prepare_subst(self, alias, args): ...


def _paramspec_subst(self, arg): ...


def _paramspec_prepare_subst(self, alias, args): ...


def _generic_class_getitem(cls, args):
    """
    Parameterizes a generic class.

    At least, parameterizing a generic class is the *main* thing this method
    does. For example, for some generic class `Foo`, this is called when we
    do `Foo[int]` - there, with `cls=Foo` and `args=int`.

    However, note that this method is also called when defining generic
    classes in the first place with `class Foo(Generic[T]): ...`.
    """


def _generic_init_subclass(cls, *args, **kwargs): ...


def _is_dunder(attr): ...
