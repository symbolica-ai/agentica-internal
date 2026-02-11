import agentica_internal.cpython.ex.named as NAMED

__all__ = ['NAMED', 'VALS', 'TYPES', 'DICT', 'cpython_type_example']


KEYS: list[str] = NAMED.__all__
VALS: list[object] = [getattr(NAMED, k) for k in KEYS]
TYPES: list[type] = [type(v) for v in VALS]
DICT: dict[str, object] = dict(zip(KEYS, VALS))

TO_EXAMPLE: dict[type, object] = dict(zip(TYPES, VALS))


def cpython_type_example(cls: type) -> object:
    return TO_EXAMPLE[cls]
