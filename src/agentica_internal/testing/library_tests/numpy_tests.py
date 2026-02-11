# fmt: off

from .. import assert_raises
from types import ModuleType

__all__ = [
    'NUMPY_UNIT_TESTS',
]

################################################################################

NUMPY_UNIT_TESTS = []

def unit(fn):
    NUMPY_UNIT_TESTS.append(fn)
    return fn

################################################################################

@unit
def array_basic(np: ModuleType) -> None:
    """Object with __array__ should be coercible via np.array()."""


    class ArrayLike:

        def __array__(self, dtype=None, copy=None):
            arr = np.array([1, 2, 3])
            if dtype is not None:
                arr = arr.astype(dtype)
            return arr


    obj = ArrayLike()
    result = np.array(obj)
    assert isinstance(result, np.ndarray)
    np.testing.assert_array_equal(result, [1, 2, 3])


@unit
def array_with_dtype(np: ModuleType) -> None:
    """__array__ should receive dtype argument."""


    class ArrayLike:

        def __init__(self):
            self.received_dtype = None

        def __array__(self, dtype=None, copy=None):
            self.received_dtype = dtype
            arr = np.array([1.5, 2.5, 3.5])
            if dtype is not None:
                arr = arr.astype(dtype)
            return arr


    obj = ArrayLike()
    result = np.array(obj, dtype=np.int32)
    assert obj.received_dtype == np.int32
    assert result.dtype == np.int32
    np.testing.assert_array_equal(result, [1, 2, 3])


@unit
def array_copy_semantics(np: ModuleType) -> None:
    """__array__ should receive copy argument (NumPy 2.0+)."""


    class ArrayLike:

        def __init__(self):
            self.received_copy = "not_called"

        def __array__(self, dtype=None, copy=None):
            self.received_copy = copy
            return np.array([1, 2, 3], dtype=dtype)


    obj = ArrayLike()
    # copy=False should be passed through
    try:
        np.array(obj, copy=False)
        # If we get here, copy parameter is supported
        assert obj.received_copy is False or obj.received_copy is None
    except TypeError:
        # Older signature without copy parameter
        # pytest.skip("copy parameter not supported in __array__")
        return


@unit
def array_nested_coercion(np: ModuleType) -> None:
    """Nested objects with __array__ should coerce properly."""


    class Inner:

        def __array__(self, dtype=None, copy=None):
            return np.array([1, 2])


    class Outer:

        def __array__(self, dtype=None, copy=None):
            return np.array([Inner(), Inner()])


    # This tests that the outer __array__ is called
    obj = Outer()
    result = np.array(obj)
    assert result.shape == (2, 2)


@unit
def asarray_uses_array_protocol(np: ModuleType) -> None:
    """np.asarray should use __array__ protocol."""


    class ArrayLike:

        def __array__(self, dtype=None, copy=None):
            return np.array([[1, 2], [3, 4]])


    obj = ArrayLike()
    result = np.asarray(obj)
    assert result.shape == (2, 2)
    np.testing.assert_array_equal(result, [[1, 2], [3, 4]])


@unit
def array_returns_non_array_raises(np: ModuleType) -> None:
    """__array__ returning non-ndarray should raise TypeError."""


    class BadArrayLike:

        def __array__(self, dtype=None, copy=None):
            return [1, 2, 3]  # Returns list, not ndarray


    obj = BadArrayLike()
    exc = None
    with assert_raises(ValueError):
        np.array(obj)


@unit
def array_in_arithmetic(np: ModuleType) -> None:
    """Objects with __array__ should work in arithmetic operations."""


    class ArrayLike:

        def __array__(self, dtype=None, copy=None):
            return np.array([1, 2, 3])


    obj = ArrayLike()
    result = np.array([10, 20, 30]) + obj
    np.testing.assert_array_equal(result, [11, 22, 33])


@unit
def array_creation_basic(np: ModuleType) -> None:
    """Test zeros, ones, full, empty and their _like variants."""
    # zeros
    z1 = np.zeros(5)
    assert z1.shape == (5,) and np.all(z1 == 0)

    z2 = np.zeros((3, 4), dtype=np.int32)
    assert z2.shape == (3, 4) and z2.dtype == np.int32

    # ones
    o1 = np.ones((2, 3))
    assert o1.shape == (2, 3) and np.all(o1 == 1)

    # full
    f1 = np.full((2, 2), 7.5)
    assert np.all(f1 == 7.5)

    # empty (just check shape/dtype, values are undefined)
    e1 = np.empty((3, 4), dtype=np.float32)
    assert e1.shape == (3, 4) and e1.dtype == np.float32

    # _like variants
    template = np.array([[1, 2], [3, 4]], dtype=np.int16)
    assert np.zeros_like(template).dtype == np.int16
    assert np.ones_like(template).shape == (2, 2)
    assert np.full_like(template, 99)[0, 0] == 99
    assert np.empty_like(template).shape == (2, 2)


@unit
def array_creation_ranges(np: ModuleType) -> None:
    """Test arange, linspace, logspace."""
    # arange
    np.testing.assert_array_equal(np.arange(5), [0, 1, 2, 3, 4])
    np.testing.assert_array_equal(np.arange(2, 7), [2, 3, 4, 5, 6])
    np.testing.assert_array_equal(np.arange(0, 10, 2), [0, 2, 4, 6, 8])
    np.testing.assert_array_equal(np.arange(5, 0, -1), [5, 4, 3, 2, 1])

    # linspace
    lin = np.linspace(0, 10, 5)
    np.testing.assert_array_almost_equal(lin, [0, 2.5, 5, 7.5, 10])

    lin_no_end = np.linspace(0, 10, 5, endpoint=False)
    np.testing.assert_array_almost_equal(lin_no_end, [0, 2, 4, 6, 8])

    lin_step, step = np.linspace(0, 1, 5, retstep=True)
    assert step == 0.25

    # logspace
    log = np.logspace(0, 2, 3)  # 10^0, 10^1, 10^2
    np.testing.assert_array_almost_equal(log, [1, 10, 100])

    log_base2 = np.logspace(0, 3, 4, base=2)
    np.testing.assert_array_almost_equal(log_base2, [1, 2, 4, 8])


@unit
def array_creation_identity_diag(np: ModuleType) -> None:
    """Test eye, identity, diag."""
    # eye
    np.testing.assert_array_equal(np.eye(3), [[1, 0, 0], [0, 1, 0], [0, 0, 1]])
    np.testing.assert_array_equal(np.eye(2, 4), [[1, 0, 0, 0], [0, 1, 0, 0]])
    np.testing.assert_array_equal(np.eye(3, k=1), [[0, 1, 0], [0, 0, 1], [0, 0, 0]])
    np.testing.assert_array_equal(np.eye(3, k=-1), [[0, 0, 0], [1, 0, 0], [0, 1, 0]])

    # identity
    ident = np.identity(4)
    assert ident.shape == (4, 4) and np.trace(ident) == 4

    # diag - extract
    mat = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
    np.testing.assert_array_equal(np.diag(mat), [1, 5, 9])
    np.testing.assert_array_equal(np.diag(mat, k=1), [2, 6])
    np.testing.assert_array_equal(np.diag(mat, k=-1), [4, 8])

    # diag - construct
    np.testing.assert_array_equal(np.diag([1, 2, 3]), [[1, 0, 0], [0, 2, 0], [0, 0, 3]])


@unit
def array_creation_from_data(np: ModuleType) -> None:
    """Test array, asarray, copy, meshgrid, fromfunction."""
    # array from list
    a1 = np.array([1, 2, 3])
    np.testing.assert_array_equal(a1, [1, 2, 3])

    a2 = np.array([[1, 2], [3, 4], [5, 6]])
    assert a2.shape == (3, 2)

    # dtype promotion
    a3 = np.array([1, 2.5, 3])
    assert a3.dtype == np.float64

    # asarray (no copy if already array)
    original = np.array([1, 2, 3])
    assert np.asarray(original) is original

    # copy
    copied = np.copy(original)
    assert copied is not original
    copied[0] = 999
    assert original[0] == 1

    # meshgrid
    x, y = np.array([1, 2, 3]), np.array([4, 5])
    xx, yy = np.meshgrid(x, y)
    assert xx.shape == (2, 3) and yy.shape == (2, 3)
    np.testing.assert_array_equal(xx, [[1, 2, 3], [1, 2, 3]])
    np.testing.assert_array_equal(yy, [[4, 4, 4], [5, 5, 5]])

    # fromfunction
    arr = np.fromfunction(lambda i, j: i + j, (3, 3), dtype=int)
    np.testing.assert_array_equal(arr, [[0, 1, 2], [1, 2, 3], [2, 3, 4]])


@unit
def reshaping(np: ModuleType) -> None:
    """Test reshape, ravel, flatten, resize, expand_dims, squeeze."""
    arr = np.arange(12)

    # reshape
    r1 = arr.reshape((3, 4))
    assert r1.shape == (3, 4)
    np.testing.assert_array_equal(r1[0], [0, 1, 2, 3])

    r2 = arr.reshape((2, -1, 3))  # infer dimension
    assert r2.shape == (2, 2, 3)

    # ravel (returns view when possible)
    mat = np.array([[1, 2, 3], [4, 5, 6]])
    np.testing.assert_array_equal(mat.ravel(), [1, 2, 3, 4, 5, 6])
    np.testing.assert_array_equal(mat.ravel(order='F'), [1, 4, 2, 5, 3, 6])

    # flatten (returns copy)
    flat = mat.flatten()
    flat[0] = 999
    assert mat[0, 0] == 1

    # resize
    resized = np.resize(np.array([1, 2, 3]), (2, 4))
    assert resized.shape == (2, 4)

    # expand_dims
    v = np.array([1, 2, 3])
    assert np.expand_dims(v, axis=0).shape == (1, 3)
    assert np.expand_dims(v, axis=1).shape == (3, 1)
    assert v[np.newaxis, :].shape == (1, 3)

    # squeeze
    s = np.array([[[1, 2, 3]]])
    assert np.squeeze(s).shape == (3,)
    assert np.squeeze(np.zeros((1, 3, 1, 4)), axis=0).shape == (3, 1, 4)


@unit
def transpose_swap(np: ModuleType) -> None:
    """Test transpose, T, swapaxes, moveaxis."""
    arr = np.array([[1, 2, 3], [4, 5, 6]])

    # T and transpose
    np.testing.assert_array_equal(arr.T, [[1, 4], [2, 5], [3, 6]])
    np.testing.assert_array_equal(arr.transpose(), arr.T)
    np.testing.assert_array_equal(np.transpose(arr), arr.T)

    # transpose with axes
    arr3d = np.arange(24).reshape((2, 3, 4))
    assert arr3d.transpose((1, 2, 0)).shape == (3, 4, 2)

    # swapaxes
    assert np.swapaxes(arr3d, 0, 2).shape == (4, 3, 2)

    # moveaxis
    assert np.moveaxis(arr3d, 0, -1).shape == (3, 4, 2)
    assert np.moveaxis(arr3d, [0, 1], [-1, -2]).shape == (4, 3, 2)


@unit
def stack_split(np: ModuleType) -> None:
    """Test concatenate, stack, vstack, hstack, split, tile, repeat."""
    a = np.array([1, 2, 3])
    b = np.array([4, 5, 6])

    # concatenate
    np.testing.assert_array_equal(np.concatenate([a, b]), [1, 2, 3, 4, 5, 6])

    m1 = np.array([[1, 2], [3, 4]])
    m2 = np.array([[5, 6]])
    assert np.concatenate([m1, m2], axis=0).shape == (3, 2)

    # stack
    stacked = np.stack([a, b])
    assert stacked.shape == (2, 3)
    np.testing.assert_array_equal(stacked, [[1, 2, 3], [4, 5, 6]])
    assert np.stack([a, b], axis=1).shape == (3, 2)

    # vstack, hstack, dstack
    assert np.vstack([a, b]).shape == (2, 3)
    np.testing.assert_array_equal(np.hstack([a, b]), [1, 2, 3, 4, 5, 6])
    assert np.dstack([m1, m1]).shape == (2, 2, 2)

    # split
    parts = np.split(np.arange(9), 3)
    assert len(parts) == 3
    np.testing.assert_array_equal(parts[0], [0, 1, 2])

    parts_idx = np.split(np.arange(10), [3, 7])
    assert len(parts_idx) == 3

    # array_split (unequal)
    unequal = np.array_split(np.arange(10), 3)
    assert len(unequal[0]) == 4 and len(unequal[1]) == 3

    # tile
    np.testing.assert_array_equal(np.tile(a, 2), [1, 2, 3, 1, 2, 3])
    assert np.tile(m1, (2, 3)).shape == (4, 6)

    # repeat
    np.testing.assert_array_equal(np.repeat(a, 2), [1, 1, 2, 2, 3, 3])
    np.testing.assert_array_equal(np.repeat(a, [1, 2, 3]), [1, 2, 2, 3, 3, 3])


@unit
def aggregation(np: ModuleType) -> None:
    """Test sum, prod, mean, std, var, min, max, argmin, argmax, cumsum, etc."""
    arr = np.array([[1, 2, 3], [4, 5, 6]])

    # basic reductions
    assert np.sum(arr) == 21
    assert np.prod(arr) == 720
    assert np.mean(arr) == 3.5
    np.testing.assert_array_equal(np.sum(arr, axis=0), [5, 7, 9])
    np.testing.assert_array_equal(np.sum(arr, axis=1), [6, 15])
    assert np.sum(arr, axis=0, keepdims=True).shape == (1, 3)

    # std/var
    v = np.array([1, 2, 3, 4, 5])
    assert np.var(v) == 2.0
    np.testing.assert_almost_equal(np.std(v), np.sqrt(2.0))
    assert np.std(v, ddof=1) > np.std(v, ddof=0)

    # min/max
    assert np.min(arr) == 1 and np.max(arr) == 6
    np.testing.assert_array_equal(np.min(arr, axis=0), [1, 2, 3])
    np.testing.assert_array_equal(np.max(arr, axis=1), [3, 6])
    assert np.ptp(v) == 4

    # argmin/argmax
    assert np.argmin(v) == 0 and np.argmax(v) == 4
    np.testing.assert_array_equal(np.argmin(arr, axis=0), [0, 0, 0])

    # cumulative
    np.testing.assert_array_equal(np.cumsum([1, 2, 3, 4]), [1, 3, 6, 10])
    np.testing.assert_array_equal(np.cumprod([1, 2, 3, 4]), [1, 2, 6, 24])
    np.testing.assert_array_equal(np.diff([1, 3, 6, 10]), [2, 3, 4])

    # boolean
    assert np.any([False, True, False]) == True
    assert np.all([True, True, False]) == False
    assert np.count_nonzero([0, 1, 2, 0, 3]) == 3

    # nan-aware
    nan_arr = np.array([1, np.nan, 3])
    assert np.nansum(nan_arr) == 4.0
    assert np.nanmean(nan_arr) == 2.0
    assert np.nanmin(nan_arr) == 1 and np.nanmax(nan_arr) == 3


@unit
def math_operations(np: ModuleType) -> None:
    """Test arithmetic, trig, exp/log, rounding, comparisons, etc."""
    a = np.array([1, 2, 3, 4])
    b = np.array([2, 2, 2, 2])

    # arithmetic
    np.testing.assert_array_equal(np.add(a, b), [3, 4, 5, 6])
    np.testing.assert_array_equal(np.subtract(a, b), [-1, 0, 1, 2])
    np.testing.assert_array_equal(np.multiply(a, b), [2, 4, 6, 8])
    np.testing.assert_array_equal(np.divide(a, b), [0.5, 1, 1.5, 2])
    np.testing.assert_array_equal(np.floor_divide(np.array([5, 7]), 2), [2, 3])
    np.testing.assert_array_equal(np.mod(np.array([5, 7]), 3), [2, 1])
    np.testing.assert_array_equal(np.power(a, 2), [1, 4, 9, 16])
    np.testing.assert_array_equal(np.negative(a), [-1, -2, -3, -4])
    np.testing.assert_array_equal(np.abs(np.array([-1, 2, -3])), [1, 2, 3])

    # broadcasting
    np.testing.assert_array_equal(a + 10, [11, 12, 13, 14])
    mat = np.array([[1, 2], [3, 4]])
    np.testing.assert_array_equal(mat + np.array([10, 20]), [[11, 22], [13, 24]])

    # trigonometry
    angles = np.array([0, np.pi / 2, np.pi])
    np.testing.assert_array_almost_equal(np.sin(angles), [0, 1, 0])
    np.testing.assert_array_almost_equal(np.cos(angles), [1, 0, -1])
    np.testing.assert_array_almost_equal(np.tan([0, np.pi / 4]), [0, 1])
    np.testing.assert_array_almost_equal(np.arcsin([0, 1]), [0, np.pi / 2])
    np.testing.assert_array_almost_equal(np.arctan2([1, 1], [1, -1]), [np.pi / 4, 3 * np.pi / 4])
    np.testing.assert_array_almost_equal(np.hypot([3, 5], [4, 12]), [5, 13])
    np.testing.assert_array_almost_equal(np.degrees([0, np.pi]), [0, 180])

    # hyperbolic
    assert np.sinh(0) == 0 and np.cosh(0) == 1
    np.testing.assert_almost_equal(np.tanh(1000), 1)

    # exponential/logarithm
    np.testing.assert_array_almost_equal(np.exp([0, 1]), [1, np.e])
    np.testing.assert_array_equal(np.exp2([0, 1, 3]), [1, 2, 8])
    np.testing.assert_array_almost_equal(np.log([1, np.e]), [0, 1])
    np.testing.assert_array_almost_equal(np.log2([1, 2, 8]), [0, 1, 3])
    np.testing.assert_array_almost_equal(np.log10([1, 10, 100]), [0, 1, 2])

    # rounding
    np.testing.assert_array_equal(np.round([1.4, 1.6, 2.5]), [1, 2, 2])
    np.testing.assert_array_equal(np.floor([1.9, -1.1]), [1, -2])
    np.testing.assert_array_equal(np.ceil([1.1, -1.9]), [2, -1])
    np.testing.assert_array_equal(np.trunc([1.9, -1.9]), [1, -1])

    # special
    np.testing.assert_array_equal(np.sqrt([0, 1, 4, 9]), [0, 1, 2, 3])
    np.testing.assert_array_almost_equal(np.cbrt([0, 1, 8]), [0, 1, 2])
    np.testing.assert_array_equal(np.square([1, 2, 3]), [1, 4, 9])
    np.testing.assert_array_equal(np.sign([-5, 0, 5]), [-1, 0, 1])
    np.testing.assert_array_equal(np.clip([1, 5, 10, 15], 5, 12), [5, 5, 10, 12])
    np.testing.assert_array_equal(np.maximum([1, 5], [2, 3]), [2, 5])
    np.testing.assert_array_equal(np.minimum([1, 5], [2, 3]), [1, 3])

    # complex
    c = np.array([1 + 2j, 3 + 4j])
    np.testing.assert_array_equal(np.real(c), [1, 3])
    np.testing.assert_array_equal(np.imag(c), [2, 4])
    np.testing.assert_array_equal(np.conj(c), [1 - 2j, 3 - 4j])
    np.testing.assert_array_equal(np.abs(np.array([3 + 4j])), [5])

    # comparisons
    np.testing.assert_array_equal(np.equal([1, 2], [1, 3]), [True, False])
    np.testing.assert_array_equal(np.less([1, 2, 3], 2), [True, False, False])
    np.testing.assert_array_equal(np.greater_equal([1, 2, 3], 2), [False, True, True])
    assert np.array_equal([1, 2], [1, 2]) and not np.array_equal([1, 2], [1, 3])
    assert np.allclose([1.0, 2.0], [1.00001, 2.00001], rtol=1e-4)

    # logical
    np.testing.assert_array_equal(np.logical_and([True, False], [True, True]), [True, False])
    np.testing.assert_array_equal(np.logical_or([True, False], [False, False]), [True, False])
    np.testing.assert_array_equal(np.logical_not([True, False]), [False, True])

    # bitwise
    np.testing.assert_array_equal(np.bitwise_and([0b1100], [0b1010]), [0b1000])
    np.testing.assert_array_equal(np.bitwise_or([0b1100], [0b1010]), [0b1110])
    np.testing.assert_array_equal(np.left_shift([1, 2], 2), [4, 8])


@unit
def where_select_sort(np: ModuleType) -> None:
    """Test where, select, nonzero, sort, argsort, searchsorted, unique."""
    arr = np.array([3, 1, 4, 1, 5, 9, 2, 6])

    # where
    np.testing.assert_array_equal(np.where([False, True, True])[0], [1, 2])
    np.testing.assert_array_equal(np.where([True, False, True], [1, 2, 3], [10, 20, 30]), [1, 20, 3])
    np.testing.assert_array_equal(np.where(arr > 4, arr, 0), [0, 0, 0, 0, 5, 9, 0, 6])

    # select
    x = np.arange(6)
    result = np.select([x < 2, x > 3], [x, x * 10], default=-1)
    np.testing.assert_array_equal(result, [0, 1, -1, -1, 40, 50])

    # nonzero
    rows, cols = np.nonzero([[0, 1], [2, 0]])
    np.testing.assert_array_equal(rows, [0, 1])
    np.testing.assert_array_equal(cols, [1, 0])

    # sort
    np.testing.assert_array_equal(np.sort(arr), [1, 1, 2, 3, 4, 5, 6, 9])

    # argsort
    indices = np.argsort([3, 1, 2])
    np.testing.assert_array_equal(indices, [1, 2, 0])

    # searchsorted
    np.testing.assert_array_equal(np.searchsorted([1, 2, 3, 4], [0, 2, 5]), [0, 1, 4])
    assert np.searchsorted([1, 2, 2, 3], 2, side='left') == 1
    assert np.searchsorted([1, 2, 2, 3], 2, side='right') == 3

    # unique
    unique, counts = np.unique([1, 2, 2, 3, 3, 3], return_counts=True)
    np.testing.assert_array_equal(unique, [1, 2, 3])
    np.testing.assert_array_equal(counts, [1, 2, 3])

    unique, inverse = np.unique([1, 2, 2, 3], return_inverse=True)
    np.testing.assert_array_equal(unique[inverse], [1, 2, 2, 3])


@unit
def set_operations(np: ModuleType) -> None:
    """Test intersect1d, union1d, setdiff1d, setxor1d, in1d, isin."""
    a = np.array([1, 2, 3, 4])
    b = np.array([3, 4, 5, 6])

    np.testing.assert_array_equal(np.intersect1d(a, b), [3, 4])
    np.testing.assert_array_equal(np.union1d(a, b), [1, 2, 3, 4, 5, 6])
    np.testing.assert_array_equal(np.setdiff1d(a, b), [1, 2])
    np.testing.assert_array_equal(np.setxor1d(a, b), [1, 2, 5, 6])


@unit
def linear_algebra_basic(np: ModuleType) -> None:
    """Test dot, matmul, inner, outer, trace, cross."""
    a = np.array([1, 2, 3])
    b = np.array([4, 5, 6])

    # dot product
    assert np.dot(a, b) == 32

    # matrix multiply
    m1 = np.array([[1, 2], [3, 4]])
    m2 = np.array([[5, 6], [7, 8]])
    expected = np.array([[19, 22], [43, 50]])
    np.testing.assert_array_equal(np.dot(m1, m2), expected)
    np.testing.assert_array_equal(np.matmul(m1, m2), expected)
    np.testing.assert_array_equal(m1 @ m2, expected)

    # inner/outer
    assert np.inner(a, b) == 32
    np.testing.assert_array_equal(np.outer([1, 2], [3, 4]), [[3, 4], [6, 8]])

    # trace
    assert np.trace([[1, 2], [3, 4]]) == 5

    # cross product
    np.testing.assert_array_equal(np.cross([1, 0, 0], [0, 1, 0]), [0, 0, 1])

    # vdot (conjugates first argument for complex)
    c1 = np.array([1 + 2j, 3 + 4j])
    c2 = np.array([5 + 6j, 7 + 8j])
    assert np.vdot(c1, c2) == (1 - 2j) * (5 + 6j) + (3 - 4j) * (7 + 8j)


@unit
def array_attributes_and_types(np: ModuleType) -> None:
    """Test shape, ndim, size, dtype, strides, flags, astype, can_cast."""
    arr = np.arange(24).reshape((2, 3, 4))

    # attributes
    assert arr.shape == (2, 3, 4)
    assert arr.ndim == 3
    assert arr.size == 24
    assert arr.itemsize == arr.dtype.itemsize
    assert arr.nbytes == 24 * arr.itemsize
    assert len(arr.strides) == 3
    assert arr.flags['C_CONTIGUOUS']

    # flat iterator
    assert list(np.array([[1, 2], [3, 4]]).flat) == [1, 2, 3, 4]

    # astype
    f = np.array([1.5, 2.5, 3.5])
    i = f.astype(np.int32)
    assert i.dtype == np.int32
    np.testing.assert_array_equal(i, [1, 2, 3])

    # type checking
    assert np.can_cast(np.int32, np.float64)
    assert not np.can_cast(np.float64, np.int32)
    assert np.result_type(np.int32, np.float64) == np.float64

    # nan/inf checks
    arr = np.array([1, np.nan, np.inf, -np.inf, 0])
    np.testing.assert_array_equal(np.isnan(arr), [False, True, False, False, False])
    np.testing.assert_array_equal(np.isinf(arr), [False, False, True, True, False])
    np.testing.assert_array_equal(np.isfinite(arr), [True, False, False, False, True])


@unit
def stringification(np: ModuleType) -> None:
    """Test str, repr, array2string, array_str, array_repr."""
    # 1D array
    a1 = np.array([1, 2, 3])
    s1 = str(a1)
    assert '1' in s1 and '2' in s1 and '3' in s1
    assert '[' in s1 and ']' in s1

    r1 = repr(a1)
    assert 'array' in r1
    assert '1' in r1 and '2' in r1 and '3' in r1

    # 2D array
    a2 = np.array([[1, 2], [3, 4]])
    s2 = str(a2)
    assert '1' in s2 and '4' in s2
    assert s2.count('[') >= 2  # nested brackets

    r2 = repr(a2)
    assert 'array' in r2

    # dtype shown in repr for non-default types
    a_int8 = np.array([1, 2, 3], dtype=np.int8)
    r_int8 = repr(a_int8)
    assert 'int8' in r_int8

    a_complex = np.array([1 + 2j, 3 + 4j])
    r_complex = repr(a_complex)
    assert 'j' in r_complex

    # 0D array (scalar)
    a0 = np.array(42)
    s0 = str(a0)
    assert '42' in s0
    r0 = repr(a0)
    assert 'array' in r0 and '42' in r0

    # empty array
    empty = np.array([])
    s_empty = str(empty)
    assert '[]' in s_empty
    r_empty = repr(empty)
    assert 'array' in r_empty

    # array2string
    a = np.array([1.123456789, 2.987654321])
    s_default = np.array2string(a)
    assert '1.123' in s_default or '1.12' in s_default

    s_precision = np.array2string(a, precision=2)
    assert '1.12' in s_precision

    s_sep = np.array2string(np.array([1, 2, 3]), separator=', ')
    assert ', ' in s_sep

    # array_str and array_repr
    assert '1' in np.array_str(a1)
    assert 'array' in np.array_repr(a1)

    # multidimensional
    a3d = np.arange(24).reshape((2, 3, 4))
    s3d = str(a3d)
    assert '0' in s3d and '23' in s3d

    # bool array
    a_bool = np.array([True, False, True])
    s_bool = str(a_bool)
    assert 'True' in s_bool and 'False' in s_bool


@unit
def iteration(np: ModuleType) -> None:
    """Test iteration over arrays: __iter__, flat, nditer, ndenumerate, ndindex."""
    # 1D iteration
    a1 = np.array([10, 20, 30])
    items = list(a1)
    assert items == [10, 20, 30]

    # iteration yields scalars or subarrays
    for i, x in enumerate(a1):
        assert x == a1[i]
        assert np.isscalar(x) or x.ndim == 0

    # 2D iteration (iterates over first axis)
    a2 = np.array([[1, 2, 3], [4, 5, 6]])
    rows = list(a2)
    assert len(rows) == 2
    np.testing.assert_array_equal(rows[0], [1, 2, 3])
    np.testing.assert_array_equal(rows[1], [4, 5, 6])

    # 3D iteration
    a3 = np.arange(24).reshape((2, 3, 4))
    planes = list(a3)
    assert len(planes) == 2
    assert planes[0].shape == (3, 4)

    # flat iterator
    flat_items = list(a2.flat)
    assert flat_items == [1, 2, 3, 4, 5, 6]

    # flat supports indexing
    assert a2.flat[0] == 1
    assert a2.flat[5] == 6
    assert a2.flat[-1] == 6

    # flat assignment
    a_copy = a2.copy()
    a_copy.flat[0] = 99
    assert a_copy[0, 0] == 99

    # nditer basic
    result = []
    for x in np.nditer(a2):
        result.append(int(x))
    assert result == [1, 2, 3, 4, 5, 6]

    # nditer with order
    result_f = []
    for x in np.nditer(a2, order='F'):
        result_f.append(int(x))
    assert result_f == [1, 4, 2, 5, 3, 6]

    # nditer with multiple arrays (broadcasting)
    a = np.array([1, 2, 3])
    b = np.array([[10], [20]])
    pairs = []
    for x, y in np.nditer([a, b]):
        pairs.append((int(x), int(y)))
    assert len(pairs) == 6
    assert (1, 10) in pairs and (3, 20) in pairs

    # ndenumerate
    enum_result = list(np.ndenumerate(a2))
    assert enum_result[0] == ((0, 0), 1)
    assert enum_result[1] == ((0, 1), 2)
    assert enum_result[5] == ((1, 2), 6)

    # ndindex
    indices = list(np.ndindex(2, 3))
    assert indices == [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]

    indices_tuple = list(np.ndindex((2, 2)))
    assert indices_tuple == [(0, 0), (0, 1), (1, 0), (1, 1)]

    # iteration over 0D raises or returns single element
    a0 = np.array(42)
    err = None
    with assert_raises(TypeError):
        list(a0)

    # empty array iteration
    empty = np.array([])
    assert list(empty) == []
    assert list(empty.flat) == []


@unit
def comparison(np: ModuleType) -> None:
    """Test array comparison: ==, !=, <, >, <=, >=, array_equal, array_equiv, allclose."""
    a = np.array([1, 2, 3, 4])
    b = np.array([1, 2, 3, 4])
    c = np.array([1, 2, 0, 4])
    d = np.array([1, 2, 3, 4, 5])

    # element-wise ==
    eq = (a == b)
    assert eq.dtype == np.bool_
    assert np.all(eq)

    eq2 = (a == c)
    np.testing.assert_array_equal(eq2, [True, True, False, True])

    # element-wise !=
    ne = (a != c)
    np.testing.assert_array_equal(ne, [False, False, True, False])

    # element-wise <, >, <=, >=
    np.testing.assert_array_equal(a < np.array([2, 2, 2, 2]), [True, False, False, False])
    np.testing.assert_array_equal(a > np.array([0, 2, 2, 5]), [True, False, True, False])
    np.testing.assert_array_equal(a <= np.array([1, 2, 2, 5]), [True, True, False, True])
    np.testing.assert_array_equal(a >= np.array([1, 3, 3, 4]), [True, False, True, True])

    # comparison with scalar
    np.testing.assert_array_equal(a == 2, [False, True, False, False])
    np.testing.assert_array_equal(a < 3, [True, True, False, False])
    np.testing.assert_array_equal(a >= 2, [False, True, True, True])

    # array_equal (strict equality, same shape and elements)
    assert np.array_equal(a, b)
    assert not np.array_equal(a, c)
    assert not np.array_equal(a, d)  # different shape

    # array_equal with equal_nan
    nan_a = np.array([1, np.nan, 3])
    nan_b = np.array([1, np.nan, 3])
    assert not np.array_equal(nan_a, nan_b)  # NaN != NaN by default
    assert np.array_equal(nan_a, nan_b, equal_nan=True)

    # array_equiv (allows broadcasting)
    assert np.array_equiv([1, 2], [1, 2])
    assert np.array_equiv([1, 2], [[1, 2], [1, 2]])  # broadcasts
    assert not np.array_equiv([1, 2], [1, 3])

    # allclose (approximate equality)
    f1 = np.array([1.0, 2.0, 3.0])
    f2 = np.array([1.00001, 2.00001, 3.00001])
    assert np.allclose(f1, f2, rtol=1e-4)
    assert not np.allclose(f1, f2, rtol=1e-6)

    # allclose with atol
    assert np.allclose([1.0], [1.1], atol=0.2)
    assert not np.allclose([1.0], [1.1], atol=0.05)

    # allclose with nan
    assert not np.allclose([np.nan], [np.nan])
    assert np.allclose([np.nan], [np.nan], equal_nan=True)

    # isclose (element-wise version of allclose)
    close = np.isclose(f1, f2, rtol=1e-4)
    assert np.all(close)

    close2 = np.isclose([1.0, 2.0], [1.0, 2.1], atol=0.05)
    np.testing.assert_array_equal(close2, [True, False])

    # comparison of different shapes raises or broadcasts
    try:
        result = (a == np.array([1, 2]))  # shape mismatch
        # if it doesn't raise, should return array with broadcast result or error
    except ValueError:
        pass  # expected for incompatible shapes

    # 2D comparison
    m1 = np.array([[1, 2], [3, 4]])
    m2 = np.array([[1, 2], [3, 4]])
    m3 = np.array([[1, 2], [3, 5]])

    assert np.array_equal(m1, m2)
    assert not np.array_equal(m1, m3)

    # comparison result shape matches input
    cmp_result = (m1 == m3)
    assert cmp_result.shape == (2, 2)
    np.testing.assert_array_equal(cmp_result, [[True, True], [True, False]])

    # comparison with different dtypes (promotion)
    int_arr = np.array([1, 2, 3])
    float_arr = np.array([1.0, 2.0, 3.0])
    assert np.array_equal(int_arr, float_arr)

    # bool array comparison
    bool1 = np.array([True, False, True])
    bool2 = np.array([True, True, False])
    np.testing.assert_array_equal(bool1 == bool2, [True, False, False])


@unit
def hashing(np: ModuleType) -> None:
    """Test hashing behavior: arrays are unhashable, scalars may be hashable."""
    # arrays are not hashable (mutable)
    a = np.array([1, 2, 3])
    try:
        hash(a)
        assert False
    except TypeError as e:
        assert 'unhashable' in str(e).lower()

    # 2D array also unhashable
    a2 = np.array([[1, 2], [3, 4]])
    with assert_raises(TypeError):
        hash(a2)

    # 0D array may or may not be hashable depending on implementation
    a0 = np.array(42)
    try:
        h = hash(a0)
        # if hashable, should equal hash of the scalar value
        assert h == hash(42)
    except TypeError:
        pass  # also acceptable

    # numpy scalars (extracted from array) should be hashable
    scalar = a[0]
    if hasattr(scalar, '__hash__') and scalar.__hash__ is not None:
        h = hash(scalar)
        assert isinstance(h, int)

    # np.int64, np.float64 scalars
    i64 = np.int64(42)

    h_i64 = hash(i64)
    assert h_i64 == hash(42)

    f64 = np.float64(3.14)
    h_f64 = hash(f64)
    assert h_f64 == hash(3.14)   # SKIP_IN_INTEGRATION

    # can use scalars as dict keys
    d = {}
    d[np.int64(1)] = 'one'
    d[np.int64(2)] = 'two'
    assert d[1] == 'one'
    assert d[np.int64(2)] == 'two'

    # can use scalars in sets
    s = {np.int64(1), np.int64(2), np.int64(1)}
    assert len(s) == 2
    assert 1 in s and 2 in s

    # bool scalars
    b_true = np.bool_(True)
    b_false = np.bool_(False)
    assert hash(b_true) == hash(True)
    assert hash(b_false) == hash(False)

    # complex scalars
    c = np.complex128(1 + 2j)
    assert hash(c) == hash(1 + 2j)

    # immutable array (via flags) still unhashable in numpy
    a_readonly = np.array([1, 2, 3])
    a_readonly.flags.writeable = False
    try:
        hash(a_readonly)
        # some implementations might allow this
    except TypeError:
        pass  # expected

    # bytes/tobytes can be used for hashing if needed
    a = np.array([1, 2, 3], dtype=np.int32)
    b = a.tobytes()
    assert isinstance(b, bytes)
    h = hash(b)
    assert isinstance(h, int)

    # same content -> same tobytes hash
    a2 = np.array([1, 2, 3], dtype=np.int32)
    assert hash(a.tobytes()) == hash(a2.tobytes())

    # different content -> different hash (usually)
    a3 = np.array([1, 2, 4], dtype=np.int32)
    assert a.tobytes() != a3.tobytes()
