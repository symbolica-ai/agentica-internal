# fmt: off

from types import ModuleType

__all__ = [
    'SCIPY_UNIT_TESTS',
]

################################################################################

SCIPY_UNIT_TESTS = []

def unit(fn):
    SCIPY_UNIT_TESTS.append(fn)
    return fn

################################################################################

@unit
def scipy_constants(np: ModuleType, sp: ModuleType):
    consts = sp.constants
    assert str(consts.pi) == '3.141592653589793'

################################################################################

@unit
def linalg_basics(np: ModuleType, sp: ModuleType):
    """Test basic linear algebra operations."""
    linalg = sp.linalg

    # Matrix inverse
    A = np.array([[1, 2], [3, 4]], dtype=float)
    A_inv = linalg.inv(A)
    assert np.allclose(A @ A_inv, np.eye(2)), "inv: A @ A_inv should be identity"
    assert np.allclose(A_inv @ A, np.eye(2)), "inv: A_inv @ A should be identity"

    # Determinant
    assert np.isclose(linalg.det(A), -2.0), "det of [[1,2],[3,4]] should be -2"
    assert np.isclose(linalg.det(np.eye(5)), 1.0), "det of identity should be 1"

    # Eigenvalues and eigenvectors
    symmetric = np.array([[2, 1], [1, 2]], dtype=float)
    eigenvalues, eigenvectors = linalg.eig(symmetric)
    for i in range(len(eigenvalues)):
        lam = eigenvalues[i]
        v = eigenvectors[:, i]
        assert np.allclose(symmetric @ v, lam * v), f"Eigenvector {i} failed Av = λv"

    # Solve linear system Ax = b
    b = np.array([5, 11], dtype=float)
    x = linalg.solve(A, b)
    assert np.allclose(A @ x, b), "solve: A @ x should equal b"

    # Norm
    v = np.array([3, 4], dtype=float)
    assert np.isclose(linalg.norm(v), 5.0), "norm of [3,4] should be 5"
    assert np.isclose(linalg.norm(v, ord=1), 7.0), "L1 norm of [3,4] should be 7"
    assert np.isclose(linalg.norm(v, ord=np.inf), 4.0), "Linf norm of [3,4] should be 4"


@unit
def linalg_decompositions(np: ModuleType, sp: ModuleType):
    """Test matrix decompositions."""
    linalg = sp.linalg

    A = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 10]], dtype=float)

    # LU decomposition
    P, L, U = linalg.lu(A)
    assert np.allclose(P @ L @ U, A), "LU: P @ L @ U should equal A"
    assert np.allclose(L, np.tril(L)), "L should be lower triangular"
    assert np.allclose(U, np.triu(U)), "U should be upper triangular"

    # QR decomposition
    Q, R = linalg.qr(A)
    assert np.allclose(Q @ R, A), "QR: Q @ R should equal A"
    assert np.allclose(Q.T @ Q, np.eye(Q.shape[1]), atol=1e-10), "Q should be orthogonal"
    assert np.allclose(R, np.triu(R)), "R should be upper triangular"

    # SVD
    U, s, Vh = linalg.svd(A)
    S = np.zeros_like(A)
    np.fill_diagonal(S, s)
    assert np.allclose(U @ S @ Vh, A), "SVD: U @ S @ Vh should equal A"
    assert np.allclose(U.T @ U, np.eye(U.shape[1]), atol=1e-10), "U should be orthogonal"
    assert np.allclose(Vh @ Vh.T, np.eye(Vh.shape[0]), atol=1e-10), "Vh should be orthogonal"

    # Cholesky (requires positive definite matrix)
    B = np.array([[4, 2], [2, 5]], dtype=float)  # positive definite
    L_chol = linalg.cholesky(B, lower=True)
    assert np.allclose(L_chol @ L_chol.T, B), "Cholesky: L @ L.T should equal B"
    assert np.allclose(L_chol, np.tril(L_chol)), "Cholesky L should be lower triangular"


@unit
def optimize_minimize_scalar(np: ModuleType, sp: ModuleType):
    """Test scalar function minimization."""
    optimize = sp.optimize

    # Simple parabola: minimum at x=2
    f = lambda x: (x - 2) ** 2 + 1
    result = optimize.minimize_scalar(f)
    assert result.success, "minimize_scalar should succeed"
    assert np.isclose(result.x, 2.0, atol=1e-5), "minimum of (x-2)^2 + 1 is at x=2"
    assert np.isclose(result.fun, 1.0, atol=1e-5), "minimum value should be 1"

    # Bounded minimization
    g = lambda x: (x - 5) ** 2
    result_bounded = optimize.minimize_scalar(g, bounds=(0, 3), method='bounded')
    assert result_bounded.success, "bounded minimize_scalar should succeed"
    assert np.isclose(result_bounded.x, 3.0, atol=1e-5), "bounded minimum should be at boundary x=3"


@unit
def optimize_root_finding(np: ModuleType, sp: ModuleType):
    """Test root finding algorithms."""
    optimize = sp.optimize

    # Simple root: x^2 - 4 = 0, roots at x = ±2
    f = lambda x: x ** 2 - 4

    # brentq requires bracketing interval
    root = optimize.brentq(f, 0, 5)
    assert np.isclose(root, 2.0, atol=1e-10), "brentq should find root at x=2"

    root_neg = optimize.brentq(f, -5, 0)
    assert np.isclose(root_neg, -2.0, atol=1e-10), "brentq should find root at x=-2"

    # bisect
    root_bisect = optimize.bisect(f, 1, 4)
    assert np.isclose(root_bisect, 2.0, atol=1e-10), "bisect should find root at x=2"

    # newton (derivative-free version uses secant)
    root_newton = optimize.newton(f, x0=1.5)
    assert np.isclose(abs(root_newton), 2.0, atol=1e-6), "newton should find root at x=±2"

    # fsolve for systems
    def equations(x):
        return [x[0] + x[1] - 3, x[0] - x[1] - 1]

    solution = optimize.fsolve(equations, [0, 0])
    assert np.allclose(solution, [2, 1], atol=1e-6), "fsolve should find x=2, y=1"


@unit
def optimize_minimize_multivariate(np: ModuleType, sp: ModuleType):
    """Test multivariate optimization."""
    optimize = sp.optimize

    # Rosenbrock function: minimum at (1, 1)
    rosenbrock = lambda x: (1 - x[0]) ** 2 + 100 * (x[1] - x[0] ** 2) ** 2

    x0 = np.array([0.0, 0.0])
    result = optimize.minimize(rosenbrock, x0, method='BFGS')
    assert result.success, "minimize should succeed on Rosenbrock"
    assert np.allclose(result.x, [1, 1], atol=1e-4), "Rosenbrock minimum at (1,1)"

    # Simple quadratic with gradient
    def quadratic(x):
        return x[0] ** 2 + x[1] ** 2 + x[0] * x[1]

    def quadratic_grad(x):
        return np.array([2 * x[0] + x[1], 2 * x[1] + x[0]])

    result2 = optimize.minimize(quadratic, [1, 1], jac=quadratic_grad, method='BFGS')
    assert result2.success, "minimize with gradient should succeed"
    assert np.allclose(result2.x, [0, 0], atol=1e-6), "quadratic minimum at origin"


@unit
def integrate_quad(np: ModuleType, sp: ModuleType):
    """Test numerical integration."""
    integrate = sp.integrate

    # Integrate x^2 from 0 to 1, should be 1/3
    result, error = integrate.quad(lambda x: x ** 2, 0, 1)
    assert np.isclose(result, 1 / 3, atol=1e-8), "∫x² dx from 0 to 1 = 1/3"

    # Integrate sin(x) from 0 to pi, should be 2
    result2, error2 = integrate.quad(np.sin, 0, np.pi)
    assert np.isclose(result2, 2.0, atol=1e-8), "∫sin(x) dx from 0 to π = 2"

    # Integrate exp(-x^2) from -inf to inf, should be sqrt(pi)
    result3, error3 = integrate.quad(lambda x: np.exp(-x ** 2), -np.inf, np.inf)
    assert np.isclose(result3, np.sqrt(np.pi), atol=1e-6), "∫exp(-x²) dx = √π"

    # Integrate 1/x from 1 to e, should be 1
    result4, error4 = integrate.quad(lambda x: 1 / x, 1, np.e)
    assert np.isclose(result4, 1.0, atol=1e-8), "∫(1/x) dx from 1 to e = 1"


@unit
def interpolate_1d(np: ModuleType, sp: ModuleType):
    """Test 1D interpolation."""
    interpolate = sp.interpolate

    # Linear interpolation
    x = np.array([0, 1, 2, 3, 4], dtype=float)
    y = np.array([0, 1, 4, 9, 16], dtype=float)  # y = x^2

    f_linear = interpolate.interp1d(x, y, kind='linear')
    assert np.isclose(f_linear(0.5), 0.5, atol=1e-10), "linear interp at 0.5"
    assert np.isclose(f_linear(1.5), 2.5, atol=1e-10), "linear interp at 1.5"

    # Cubic interpolation (should be closer to true x^2)
    f_cubic = interpolate.interp1d(x, y, kind='cubic')
    test_points = np.array([0.5, 1.5, 2.5, 3.5])
    expected = test_points ** 2
    interpolated = f_cubic(test_points)
    assert np.allclose(interpolated, expected, atol=0.1), "cubic interp approximates x^2"

    # Verify boundary values are exact
    assert np.isclose(f_cubic(0), 0, atol=1e-10), "cubic interp exact at x=0"
    assert np.isclose(f_cubic(2), 4, atol=1e-10), "cubic interp exact at x=2"


@unit
def interpolate_spline(np: ModuleType, sp: ModuleType):
    """Test spline interpolation."""
    interpolate = sp.interpolate

    # Fit spline to sin(x)
    x = np.linspace(0, 2 * np.pi, 10)
    y = np.sin(x)

    # UnivariateSpline
    spline = interpolate.UnivariateSpline(x, y, s=0)  # s=0 for interpolating spline

    # Check it passes through data points
    assert np.allclose(spline(x), y, atol=1e-10), "spline should pass through data points"

    # Check intermediate values are reasonable
    x_test = np.linspace(0, 2 * np.pi, 100)
    y_test = spline(x_test)
    y_true = np.sin(x_test)
    assert np.allclose(y_test, y_true, atol=0.05), "spline should approximate sin(x)"

    # CubicSpline
    cs = interpolate.CubicSpline(x, y)
    assert np.allclose(cs(x), y, atol=1e-10), "CubicSpline passes through data"

    # Derivative should approximate cos(x)
    cs_deriv = cs(x_test, 1)  # first derivative
    assert np.allclose(cs_deriv, np.cos(x_test), atol=0.1), "spline derivative ≈ cos(x)"


@unit
def special_functions(np: ModuleType, sp: ModuleType):
    """Test special mathematical functions."""
    special = sp.special

    # Gamma function
    assert np.isclose(special.gamma(5), 24.0, atol=1e-10), "Γ(5) = 4! = 24"
    assert np.isclose(special.gamma(0.5), np.sqrt(np.pi), atol=1e-10), "Γ(1/2) = √π"
    assert np.isclose(special.gamma(1), 1.0, atol=1e-10), "Γ(1) = 1"

    # Beta function
    assert np.isclose(special.beta(2, 3), 1 / 12, atol=1e-10), "B(2,3) = 1/12"
    assert np.isclose(special.beta(1, 1), 1.0, atol=1e-10), "B(1,1) = 1"

    # Error function
    assert np.isclose(special.erf(0), 0.0, atol=1e-10), "erf(0) = 0"
    assert np.isclose(special.erf(np.inf), 1.0, atol=1e-10), "erf(∞) = 1"
    assert np.isclose(special.erfc(0), 1.0, atol=1e-10), "erfc(0) = 1"

    # Bessel functions
    assert np.isclose(special.j0(0), 1.0, atol=1e-10), "J₀(0) = 1"
    assert np.isclose(special.j1(0), 0.0, atol=1e-10), "J₁(0) = 0"

    # Factorial and combinations
    assert special.factorial(5) == 120, "5! = 120"
    assert special.comb(5, 2) == 10, "C(5,2) = 10"
    assert special.perm(5, 2) == 20, "P(5,2) = 20"


@unit
def stats_distributions(np: ModuleType, sp: ModuleType):
    """Test statistical distributions."""
    stats = sp.stats

    # Normal distribution
    norm = stats.norm(loc=0, scale=1)
    assert np.isclose(norm.pdf(0), 1 / np.sqrt(2 * np.pi), atol=1e-10), "N(0,1) pdf at 0"
    assert np.isclose(norm.cdf(0), 0.5, atol=1e-10), "N(0,1) cdf at 0 = 0.5"
    assert np.isclose(norm.ppf(0.5), 0.0, atol=1e-10), "N(0,1) ppf(0.5) = 0"
    assert np.isclose(norm.mean(), 0.0, atol=1e-10), "N(0,1) mean = 0"
    assert np.isclose(norm.var(), 1.0, atol=1e-10), "N(0,1) variance = 1"

    # Uniform distribution
    uniform = stats.uniform(loc=0, scale=1)
    assert np.isclose(uniform.pdf(0.5), 1.0, atol=1e-10), "U(0,1) pdf = 1"
    assert np.isclose(uniform.cdf(0.5), 0.5, atol=1e-10), "U(0,1) cdf(0.5) = 0.5"
    assert np.isclose(uniform.mean(), 0.5, atol=1e-10), "U(0,1) mean = 0.5"

    # Exponential distribution
    expon = stats.expon(scale=2)  # mean = 2
    assert np.isclose(expon.pdf(0), 0.5, atol=1e-10), "Exp(λ=0.5) pdf at 0"
    assert np.isclose(expon.mean(), 2.0, atol=1e-10), "Exp(λ=0.5) mean = 2"

    # Chi-squared
    chi2 = stats.chi2(df=3)
    assert np.isclose(chi2.mean(), 3.0, atol=1e-10), "χ²(3) mean = 3"
    assert np.isclose(chi2.var(), 6.0, atol=1e-10), "χ²(3) variance = 6"


@unit
def stats_hypothesis_tests(np: ModuleType, sp: ModuleType):
    """Test statistical hypothesis tests."""
    stats = sp.stats
    np.random.seed(42)

    # t-test: compare two samples from same distribution
    sample1 = np.random.normal(0, 1, 100)
    sample2 = np.random.normal(0, 1, 100)
    t_stat, p_value = stats.ttest_ind(sample1, sample2)
    assert p_value > 0.05, "t-test should not reject H0 for same distribution"

    # t-test: compare samples from different distributions
    sample3 = np.random.normal(0, 1, 100)
    sample4 = np.random.normal(2, 1, 100)  # different mean
    t_stat2, p_value2 = stats.ttest_ind(sample3, sample4)
    assert p_value2 < 0.05, "t-test should reject H0 for different means"

    # One-sample t-test
    sample5 = np.random.normal(0.5, 1, 100)
    t_stat3, p_value3 = stats.ttest_1samp(sample5, 0)
    # With mean 0.5 and n=100, should likely reject H0: μ=0

    # Pearson correlation
    x = np.arange(20, dtype=float)
    y = 2 * x + np.random.normal(0, 1, 20)
    r, p = stats.pearsonr(x, y)
    assert r > 0.9, "strong positive correlation expected"
    assert p < 0.01, "correlation should be significant"


@unit
def stats_descriptive(np: ModuleType, sp: ModuleType):
    """Test descriptive statistics."""
    stats = sp.stats

    data = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)

    # Describe
    desc = stats.describe(data)
    assert desc.nobs == 10, "n = 10"
    assert np.isclose(desc.mean, 5.5, atol=1e-10), "mean = 5.5"
    assert np.isclose(desc.variance, np.var(data, ddof=1), atol=1e-10), "variance"

    # Mode
    mode_data = np.array([1, 2, 2, 3, 3, 3, 4])
    mode_result = stats.mode(mode_data)
    assert mode_result.mode == 3, "mode should be 3"

    # Skewness and kurtosis
    symmetric = np.array([-2, -1, 0, 1, 2], dtype=float)
    assert np.isclose(stats.skew(symmetric), 0.0, atol=1e-10), "symmetric data has 0 skew"

    # Percentile/quantile via scoreatpercentile
    assert np.isclose(stats.scoreatpercentile(data, 50), 5.5, atol=1e-10), "median"


@unit
def signal_filtering(np: ModuleType, sp: ModuleType):
    """Test signal processing filters."""
    signal = sp.signal

    # Design a simple lowpass Butterworth filter
    b, a = signal.butter(4, 0.1, btype='low')
    assert len(b) == 5 and len(a) == 5, "4th order filter has 5 coefficients"

    # Create a test signal: low frequency + high frequency
    t = np.linspace(0, 1, 1000)
    low_freq = np.sin(2 * np.pi * 5 * t)    # 5 Hz
    high_freq = np.sin(2 * np.pi * 100 * t)  # 100 Hz
    signal_data = low_freq + 0.5 * high_freq

    # Apply filter
    filtered = signal.filtfilt(b, a, signal_data)

    # High frequency component should be attenuated
    # Check that filtered signal is closer to low_freq than original
    error_original = np.mean((signal_data - low_freq) ** 2)
    error_filtered = np.mean((filtered - low_freq) ** 2)
    assert error_filtered < error_original, "filtering should reduce high frequency noise"


# @unit
def signal_convolution(np: ModuleType, sp: ModuleType):
    """Test convolution and correlation."""
    signal = sp.signal

    # Convolution
    x = np.array([1, 2, 3])
    h = np.array([0, 1, 0.5])
    conv_result = signal.convolve(x, h)
    expected = np.array([0, 1, 2.5, 4, 1.5])
    assert np.allclose(conv_result, expected), "convolution result"

    # Correlation
    corr_result = signal.correlate(x, x, mode='full')
    # Auto-correlation should peak at center
    center = len(corr_result) // 2
    assert corr_result[center] == max(corr_result), "autocorrelation peaks at center"

    # 2D convolution
    img = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]], dtype=float)
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=float)  # Laplacian
    conv2d = signal.convolve2d(img, kernel, mode='same')
    assert conv2d.shape == img.shape, "same mode preserves shape"


@unit
def fft(np: ModuleType, sp: ModuleType):
    """Test FFT functionality."""
    fft = sp.fft

    # FFT of pure sine wave
    N = 1000
    t = np.linspace(0, 1, N, endpoint=False)
    freq = 10  # Hz
    signal = np.sin(2 * np.pi * freq * t)

    spectrum = fft.fft(signal)
    freqs = fft.fftfreq(N, 1 / N)

    # Find dominant frequency
    magnitude = np.abs(spectrum)
    dominant_idx = np.argmax(magnitude[:N // 2])
    dominant_freq = freqs[dominant_idx]
    assert np.isclose(dominant_freq, freq, atol=1), f"dominant frequency should be {freq} Hz"

    # Inverse FFT should recover signal
    recovered = fft.ifft(spectrum)
    assert np.allclose(recovered.real, signal, atol=1e-10), "ifft should recover original"

    # Real FFT
    rfft_result = fft.rfft(signal)
    irfft_result = fft.irfft(rfft_result, n=N)
    assert np.allclose(irfft_result, signal, atol=1e-10), "irfft should recover original"


@unit
def sparse_basics(np: ModuleType, sp: ModuleType):
    """Test sparse matrix basics."""
    sparse = sp.sparse

    # Create sparse matrix from dense
    dense = np.array([[1, 0, 0], [0, 2, 0], [0, 0, 3]], dtype=float)
    csr = sparse.csr_matrix(dense)

    assert csr.shape == (3, 3), "shape preserved"
    assert csr.nnz == 3, "3 non-zero elements"
    assert np.allclose(csr.toarray(), dense), "toarray recovers dense"

    # COO format
    row = np.array([0, 1, 2])
    col = np.array([0, 1, 2])
    data = np.array([1, 2, 3], dtype=float)
    coo = sparse.coo_matrix((data, (row, col)), shape=(3, 3))
    assert np.allclose(coo.toarray(), dense), "COO construction"

    # Matrix operations
    csc = sparse.csc_matrix(dense)
    result = csr @ csc
    expected = dense @ dense
    assert np.allclose(result.toarray(), expected), "sparse matrix multiplication"

    # Scalar operations
    scaled = csr * 2
    assert np.allclose(scaled.toarray(), dense * 2), "scalar multiplication"


@unit
def sparse_linalg(np: ModuleType, sp: ModuleType):
    """Test sparse linear algebra."""
    sparse = sp.sparse
    linalg = sp.sparse.linalg

    # Create a sparse SPD matrix
    n = 10
    diag = 4 * np.ones(n)
    off_diag = -np.ones(n - 1)
    A = sparse.diags([off_diag, diag, off_diag], [-1, 0, 1], format='csr')

    b = np.ones(n)

    # Solve sparse system
    x = linalg.spsolve(A, b)
    assert np.allclose(A @ x, b), "spsolve: Ax = b"

    # Iterative solver (conjugate gradient for SPD)
    x_cg, info = linalg.cg(A, b)
    assert info == 0, "CG should converge"
    assert np.allclose(A @ x_cg, b, atol=1e-5), "CG solution"

    # Eigenvalues of sparse matrix
    eigenvalues, eigenvectors = linalg.eigs(A.astype(float), k=3, which='SM')
    for i in range(len(eigenvalues)):
        lam = eigenvalues[i]
        v = eigenvectors[:, i]
        residual = A @ v - lam * v
        assert np.linalg.norm(residual) < 1e-10, f"eigenvector {i} check"


@unit
def spatial_distance(np: ModuleType, sp: ModuleType):
    """Test spatial distance computations."""
    spatial = sp.spatial
    distance = sp.spatial.distance

    # Euclidean distance
    p1 = np.array([0, 0])
    p2 = np.array([3, 4])
    assert np.isclose(distance.euclidean(p1, p2), 5.0), "euclidean distance"

    # Other distance metrics
    v1 = np.array([1, 0, 0])
    v2 = np.array([0, 1, 0])
    assert np.isclose(distance.cosine(v1, v2), 1.0), "cosine distance of orthogonal = 1"

    v3 = np.array([1, 0, 0])
    v4 = np.array([1, 0, 0])
    assert np.isclose(distance.cosine(v3, v4), 0.0), "cosine distance of same = 0"

    # Pairwise distances
    points = np.array([[0, 0], [1, 0], [0, 1], [1, 1]], dtype=float)
    pdist_result = distance.pdist(points)
    assert len(pdist_result) == 6, "pdist returns n*(n-1)/2 distances"

    # cdist between two sets
    set1 = np.array([[0, 0], [1, 1]], dtype=float)
    set2 = np.array([[1, 0], [0, 1]], dtype=float)
    cdist_result = distance.cdist(set1, set2)
    assert cdist_result.shape == (2, 2), "cdist shape"
    assert np.isclose(cdist_result[0, 0], 1.0), "distance (0,0) to (1,0)"


@unit
def spatial_kdtree(np: ModuleType, sp: ModuleType):
    """Test KD-tree spatial queries."""
    spatial = sp.spatial

    # Create random points
    np.random.seed(42)
    points = np.random.rand(100, 3)
    tree = spatial.KDTree(points)

    # Query nearest neighbor
    query_point = np.array([0.5, 0.5, 0.5])
    dist, idx = tree.query(query_point)

    # Verify it's actually the nearest
    all_dists = np.linalg.norm(points - query_point, axis=1)
    assert idx == np.argmin(all_dists), "query returns nearest point"
    assert np.isclose(dist, np.min(all_dists)), "query returns correct distance"

    # Query k nearest neighbors
    dists, idxs = tree.query(query_point, k=5)
    sorted_all = np.sort(all_dists)[:5]
    assert np.allclose(np.sort(dists), sorted_all), "k-nearest correct"

    # Query within radius
    radius = 0.3
    idxs_ball = tree.query_ball_point(query_point, radius)
    for i in idxs_ball:
        assert np.linalg.norm(points[i] - query_point) <= radius, "ball query"


@unit
def ndimage_filters(np: ModuleType, sp: ModuleType):
    """Test image filtering operations."""
    ndimage = sp.ndimage

    # Create test image
    img = np.zeros((10, 10))
    img[4:6, 4:6] = 1  # small square in center

    # Gaussian filter
    smoothed = ndimage.gaussian_filter(img, sigma=1)
    assert smoothed.shape == img.shape, "shape preserved"
    assert smoothed[5, 5] < img[5, 5], "center value decreased by smoothing"
    assert smoothed[0, 0] > img[0, 0], "corner value increased by smoothing"

    # Uniform filter (box blur)
    uniform = ndimage.uniform_filter(img, size=3)
    assert uniform.shape == img.shape, "shape preserved"

    # Sobel edge detection
    edges_x = ndimage.sobel(img, axis=0)
    edges_y = ndimage.sobel(img, axis=1)
    edge_magnitude = np.sqrt(edges_x ** 2 + edges_y ** 2)
    # Edges should be detected at boundaries of square
    assert edge_magnitude[4, 5] > 0, "edge detected"


@unit
def ndimage_morphology(np: ModuleType, sp: ModuleType):
    """Test morphological operations."""
    ndimage = sp.ndimage

    # Binary image
    img = np.zeros((10, 10), dtype=bool)
    img[3:7, 3:7] = True  # 4x4 square

    # Erosion (shrink)
    eroded = ndimage.binary_erosion(img)
    assert eroded.sum() < img.sum(), "erosion shrinks"

    # Dilation (grow)
    dilated = ndimage.binary_dilation(img)
    assert dilated.sum() > img.sum(), "dilation grows"

    # Opening (erosion then dilation) removes small features
    small_feature = img.copy()
    small_feature[0, 0] = True  # isolated point
    opened = ndimage.binary_opening(small_feature)
    assert not opened[0, 0], "opening removes isolated point"

    # Closing (dilation then erosion) fills small holes
    with_hole = img.copy()
    with_hole[5, 5] = False  # hole in center
    closed = ndimage.binary_closing(with_hole)
    assert closed[5, 5], "closing fills hole"


@unit
def ndimage_measurements(np: ModuleType, sp: ModuleType):
    """Test image measurements and labeling."""
    ndimage = sp.ndimage

    # Create image with labeled regions
    img = np.zeros((10, 10), dtype=int)
    img[1:3, 1:3] = 1   # region 1
    img[5:8, 5:8] = 2   # region 2
    img[1:3, 7:9] = 3   # region 3

    # Label connected components
    binary = img > 0
    labeled, num_features = ndimage.label(binary)
    assert num_features == 3, "should find 3 regions"

    # Find objects (bounding boxes)
    objects = ndimage.find_objects(labeled)
    assert len(objects) == 3, "3 bounding boxes"

    # Center of mass
    com = ndimage.center_of_mass(img, labeled, [1, 2, 3])
    assert len(com) == 3, "3 centers of mass"

    # Sum over labeled regions
    region_sums = ndimage.sum(img, labeled, [1, 2, 3])
    assert list(region_sums) == [4, 12, 18]
