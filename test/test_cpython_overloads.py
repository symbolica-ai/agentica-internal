def get_overloads_docstrs(f) -> str:
    import typing
    return ' '.join(f.__doc__ for f in typing.get_overloads(f))


def get_overloads_is_patched() -> bool:
    import typing
    return 'cpython' in typing.get_overloads.__code__.co_filename


def test_multi_overloads():
    import typing

    def bar(): ...

    @typing.overload
    def foo(): """orig_0"""

    @typing.overload
    def foo(x): """orig_1"""

    def foo(*args): """orig"""

    def novel_0():  """novel_0"""

    def novel_1(x): """novel_1"""

    def novel_2(x): """novel_2"""

    assert get_overloads_docstrs(foo) == 'orig_0 orig_1'
    assert get_overloads_docstrs(bar) == ''

    from agentica_internal.cpython.overloads import set_overloads

    set_overloads(foo, [novel_0, novel_1, novel_2], 1)

    assert get_overloads_docstrs(foo) == 'novel_0 novel_1 novel_2'
    assert get_overloads_docstrs(bar) == ''
