# fmt: off

import pytest
import itertools as I

from typing import Iterable
from agentica_internal.cpython.iters import *
from agentica_internal.testing import *


def make_iters() -> Iterable[tuple[str, Iterable, int]]:

    str_ = 'abc'
    bytes_ = b'abc'
    empty = ()
    r0 = range(0)
    r2 = range(2)
    r8 = range(8)
    list_ = [1, 2, 3]
    tuple_ = (1, 2, 3)
    set_  = {1, 2, 3}
    dict_ = {1: 1, 2: 2, 3: 3}
    dict_keys = dict_.keys()
    dict_values = dict_.values()
    dict_items = dict_.items()
    map_proxy = object.__dict__

    f1 = lambda _: 0
    f2 = lambda _, __: 0

    yield 'r0', r0, 0
    yield 'r2', r2, 2
    yield 'r8', r8, 8
    yield 'empty', empty, 0
    yield 'str', str_, 3
    yield 'bytes', bytes_, 3
    yield 'list', list_, 3
    yield 'tuple', tuple_, 3
    yield 'set', set_, 3
    yield 'dict', dict_, 3
    yield 'dict_keys', dict_keys, 3
    yield 'dict_values', dict_values, 3
    yield 'dict_items', dict_items, 3
    yield 'map_proxy', map_proxy, len(map_proxy)
    yield 'map(f1, r2)', map(f1, r2), 2
    yield 'map(f1, r8)', map(f1, r8), 8
    yield 'map(f2, r8, r2)', map(f2, r8, r2), 2
    yield 'map(f2, r8, r8)', map(f2, r8, r8), 8
    yield 'zip(r2)', zip(r2), 2
    yield 'zip(r8)', zip(r8), 8
    yield 'zip(r2, r2)', zip(r2, r2), 2
    yield 'zip(r2, r8)', zip(r2, r8), 2
    yield 'zip(r8, r8)', zip(r8, r8), 8
    yield 'reversed(list)', reversed(list_), 3
    yield 'reversed(tuple)', reversed(tuple_), 3
    yield 'count()', I.count(), UNBOUNDED
    yield 'cycle(list)', I.cycle(list_), UNBOUNDED
    yield 'islice(r2, 5)', I.islice(r2, 5), 2
    yield 'islice(r2, 5)', I.islice(r8, 5), 5
    yield 'repeat(r2, r8)', I.repeat(5), UNBOUNDED
    yield 'repeat(r2, r8)', I.repeat(5, 2), 2
    yield 'starmap(f1, zip(r8, r8))', I.starmap(f2, zip(r8, r8)), 8
    yield 'zip_longest(r2, r8)', I.zip_longest(r2, r8), 8
    # yield 'pairwise(r8)', I.pairwise(r8), 1
    # yield 'accumulate(r2)', I.accumulate(r2), 3
    # yield 'combinations(r2, r8)', I.product(r2, r8), 16
    # yield 'product(r2, r8)', I.product(r2, r8), 16
    # yield 'chain(r2, r8)', I.chain(r2, r8), 10


NAMES, OBJECTS, LENGTHS = zip(*make_iters())

def verify_iter_len(obj: Iterable, n_true: int) -> None:

    n_obj = iter_len(obj)
    assert n_obj == n_true, f"iter_len(obj) = {n_obj} != {n_true}"

    it = iter(obj)
    # print(type(obj), type(it))
    n_iter = iter_len(obj)
    assert n_iter == n_true

    if n_true >= UNBOUNDED:
        return

    done = False
    for i in range(1, 32):
        try:
            next(it)
        except StopIteration:
            done = True
        if done:
            assert n_true == 0, f"{n_true=!r} is wrong"
            return
        n_iter = iter_len(it)
        n_true -= 1
        assert n_iter == n_true, f"after {i}: {n_iter} != {n_true}"

@pytest.mark.parametrize('obj,n_true', zip(OBJECTS, LENGTHS), ids=NAMES)
def test_iter_lens(obj: Iterable, n_true: int):
    verify_iter_len(obj, n_true)


if __name__ == '__main__':
    run_object_tests(verify_iter_len, OBJECTS, LENGTHS, names=NAMES)
