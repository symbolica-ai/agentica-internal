import pytest
from agentica_internal.core.result import Result
from agentica_internal.warpc.worlds.debug_world import DebugWorld


@pytest.mark.asyncio
async def test_resource_pre_hooks():
    class MyClass:
        def __str__(self) -> str:
            return 'str'

        def __repr__(self) -> str:
            return 'repr'

        def __hash__(self) -> int:
            return 0

    my_obj = MyClass()

    pair = DebugWorld.connected_pair(logging=False)
    async with pair as B:
        my_obj_b = await B(my_obj)
        assert str(my_obj_b) == 'str'
        assert repr(my_obj_b) == 'repr'

        def hooked_str_or_repl(handle, request):
            return Result.good('hooked')

        def hooked_hash(handle, request):
            return Result.good(handle.grid[2])

        def bad_hook(handle, request):
            return 888

        def null_hook(handle, request):
            return NotImplemented

        pair.b.register_pre_request_hook(str, bad_hook)
        assert str(my_obj_b) == "<'MyClass' object>"

        pair.b.register_pre_request_hook(str, hooked_str_or_repl)
        assert str(my_obj_b) == 'hooked'
        assert repr(my_obj_b) == 'repr'

        pair.b.register_pre_request_hook(repr, hooked_str_or_repl)
        assert str(my_obj_b) == 'hooked'
        assert repr(my_obj_b) == 'hooked'

        pair.b.register_pre_request_hook(repr, null_hook)
        assert repr(my_obj_b) == 'repr'

        pair.b.register_pre_request_hook(hash, hooked_hash)
        assert hash(my_obj_b) == id(my_obj)


@pytest.mark.asyncio
async def test_resource_post_hooks():
    class MyClass:
        def __str__(self) -> str:
            return 'str'

        def __repr__(self) -> str:
            return 'repr'

        def __hash__(self) -> int:
            return 123

    my_obj = MyClass()

    pair = DebugWorld.connected_pair()
    async with pair as B:
        my_obj_b = await B(my_obj)
        assert str(my_obj_b) == 'str'
        assert repr(my_obj_b) == 'repr'

        def hooked_str_or_repl(result, handle, request):
            if result.is_ok:
                return Result.good('<hooked ' + result.value + '>')
            return result

        def hooked_hash(result, handle, request):
            if result.is_ok:
                return Result.good(handle.grid[2] + result.value)
            return result

        def bad_hook(result, handle, request):
            return 888

        def null_hook(result, handle, request):
            return NotImplemented

        pair.b.register_post_request_hook(str, bad_hook)
        assert str(my_obj_b) == "<'MyClass' object>"

        pair.b.register_post_request_hook(str, hooked_str_or_repl)
        assert str(my_obj_b) == '<hooked str>'
        assert repr(my_obj_b) == 'repr'

        pair.b.register_post_request_hook(repr, hooked_str_or_repl)
        assert str(my_obj_b) == '<hooked str>'
        assert repr(my_obj_b) == '<hooked repr>'

        pair.b.register_post_request_hook(repr, null_hook)
        assert repr(my_obj_b) == 'repr'

        pair.b.register_post_request_hook(hash, hooked_hash)
        assert hash(my_obj_b) == id(my_obj) + 123


@pytest.mark.asyncio
async def test_resource_fallback_repr_hooks():
    class MyClass:
        a: int
        b: str

        def __init__(self, a: int, b: str):
            self.a = a
            self.b = b

        def __str__(self) -> str:
            return ''  # type: ignore

        def __repr__(self) -> str:
            return ''  # type: ignore

    my_obj = MyClass(3, 'world')

    pair = DebugWorld.connected_pair()
    async with pair as B:
        my_obj_b = await B(my_obj)

        def v_object_repr(o, post_value: str | None) -> str:
            r = post_value
            if not r:
                r = (
                    f"{o.__class__.__name__}("
                    + ", ".join(f"{k!s}={getattr(o, k)!r}" for k in vars(o))
                    + ")"
                )
            return r

        def v_object_str(o, post_value: str | None) -> str:
            return post_value if post_value else repr(o)

        def post_hook_repr(post, handle, request) -> Result:
            if post.is_ok:
                return Result.good(v_object_repr(request.obj, post.value))
            return post

        def post_hook_str(post, handle, request) -> Result:
            if post.is_ok:
                return Result.good(v_object_str(request.obj, post.value))
            return post

        pair.b.register_post_request_hook(repr, post_hook_repr)
        pair.b.register_post_request_hook(str, post_hook_str)
        assert repr(my_obj_b) == "MyClass(a=3, b='world')"
        assert str(my_obj_b) == "MyClass(a=3, b='world')"
