# fmt: off

from types import ModuleType

__all__ = [
    'SYMPY_UNIT_TESTS',
]

################################################################################

SYMPY_UNIT_TESTS = []

def unit(fn):
    SYMPY_UNIT_TESTS.append(fn)
    return fn

################################################################################

@unit
def symbol_creation_and_basic_algebra(sp: ModuleType):
    """Test symbol creation, basic algebraic operations, and expression manipulation."""
    # Symbol creation
    x = sp.Symbol('x')
    y = sp.Symbol('y')
    z = sp.Symbol('z')

    assert str(x) == 'x'
    assert x != y
    assert x == sp.Symbol('x')  # Same name -> equal symbols

    # Basic arithmetic creates expressions
    expr = x + y
    assert x in expr.free_symbols
    assert y in expr.free_symbols

    # Commutativity and associativity
    assert x + y == y + x
    assert x * y == y * x
    assert (x + y) + z == x + (y + z)

    # Distributivity
    expanded = sp.expand(x * (y + z))
    assert expanded == x * y + x * z

    # Combining like terms
    assert x + x == 2 * x
    assert x + 2 * x == 3 * x
    assert x * x == x ** 2

    # Expression with numbers
    expr = 2 * x + 3 * x - x
    assert expr == 4 * x

    # Powers
    assert x ** 2 * x ** 3 == x ** 5
    assert (x ** 2) ** 3 == x ** 6

    # Division
    assert x / x == 1  # sympy simplifies this
    assert (x ** 2) / x == x


@unit
def substitution_and_evaluation(sp: ModuleType):
    """Test substituting values into expressions and numerical evaluation."""
    x, y = sp.symbols('x y')

    # Simple substitution
    expr = x ** 2 + 2 * x + 1
    result = expr.subs(x, 3)
    assert result == 16  # 9 + 6 + 1

    # Substitution with another symbol
    result = expr.subs(x, y)
    assert result == y ** 2 + 2 * y + 1

    # Multiple substitutions
    expr = x + y
    result = expr.subs([(x, 1), (y, 2)])
    assert result == 3

    # Substitution in more complex expression
    expr = sp.sin(x) + sp.cos(x)
    result = expr.subs(x, 0)
    assert result == 1  # sin(0) + cos(0) = 0 + 1

    # Numerical evaluation with evalf
    expr = sp.sqrt(2)
    numeric = expr.evalf()
    assert abs(float(numeric) - 1.41421356) < 1e-6

    # Pi evaluation
    pi_val = sp.pi.evalf()
    assert abs(float(pi_val) - 3.14159265) < 1e-6


@unit
def expand_factor_simplify(sp: ModuleType):
    """Test expression expansion, factoring, and simplification."""
    x, y = sp.symbols('x y')

    # Expand polynomial
    expr = (x + y) ** 2
    expanded = sp.expand(expr)
    assert expanded == x ** 2 + 2 * x * y + y ** 2

    expr = (x + 1) * (x - 1)
    expanded = sp.expand(expr)
    assert expanded == x ** 2 - 1

    # Factor polynomial
    expr = x ** 2 - 1
    factored = sp.factor(expr)
    assert factored == (x - 1) * (x + 1)

    expr = x ** 2 + 2 * x + 1
    factored = sp.factor(expr)
    assert factored == (x + 1) ** 2

    # Simplify
    expr = (x ** 2 - 1) / (x - 1)
    simplified = sp.simplify(expr)
    assert simplified == x + 1

    # Trigonometric simplification
    expr = sp.sin(x) ** 2 + sp.cos(x) ** 2
    simplified = sp.simplify(expr)
    assert simplified == 1


@unit
def solve_equations(sp: ModuleType):
    """Test solving algebraic equations."""
    x, y = sp.symbols('x y')

    # Linear equation
    solutions = sp.solve(x - 5, x)
    assert solutions == [5]

    # Quadratic equation x^2 - 4 = 0
    solutions = sp.solve(x ** 2 - 4, x)
    assert set(solutions) == {-2, 2}

    # Quadratic with complex roots x^2 + 1 = 0
    solutions = sp.solve(x ** 2 + 1, x)
    assert set(solutions) == {sp.I, -sp.I}

    # Equation expressed as Eq object
    eq = sp.Eq(x ** 2, 9)
    solutions = sp.solve(eq, x)
    assert set(solutions) == {-3, 3}

    # System of linear equations
    eq1 = sp.Eq(x + y, 10)
    eq2 = sp.Eq(x - y, 2)
    solutions = sp.solve([eq1, eq2], [x, y])
    assert solutions == {x: 6, y: 4}


@unit
def calculus_differentiation(sp: ModuleType):
    """Test symbolic differentiation."""
    x, y = sp.symbols('x y')

    # Basic derivatives
    assert sp.diff(x ** 2, x) == 2 * x
    assert sp.diff(x ** 3, x) == 3 * x ** 2
    assert sp.diff(x ** 5, x) == 5 * x ** 4

    # Constant
    assert sp.diff(5, x) == 0
    assert sp.diff(y, x) == 0  # y treated as constant w.r.t. x

    # Sum rule
    expr = x ** 2 + 3 * x + 1
    assert sp.diff(expr, x) == 2 * x + 3

    # Product rule
    expr = x * sp.sin(x)
    deriv = sp.diff(expr, x)
    expected = sp.sin(x) + x * sp.cos(x)
    assert sp.simplify(deriv - expected) == 0

    # Chain rule
    assert sp.diff(sp.sin(x ** 2), x) == 2 * x * sp.cos(x ** 2)

    # Transcendental functions
    assert sp.diff(sp.exp(x), x) == sp.exp(x)
    assert sp.diff(sp.log(x), x) == 1 / x
    assert sp.diff(sp.sin(x), x) == sp.cos(x)
    assert sp.diff(sp.cos(x), x) == -sp.sin(x)

    # Higher-order derivatives
    assert sp.diff(x ** 4, x, 2) == 12 * x ** 2
    assert sp.diff(x ** 4, x, 3) == 24 * x
    assert sp.diff(x ** 4, x, 4) == 24


@unit
def calculus_integration(sp: ModuleType):
    """Test symbolic integration."""
    x = sp.Symbol('x')

    # Power rule (indefinite integrals)
    assert sp.integrate(x ** 2, x) == x ** 3 / 3
    assert sp.integrate(x, x) == x ** 2 / 2
    assert sp.integrate(1, x) == x

    # Transcendental functions
    assert sp.integrate(sp.exp(x), x) == sp.exp(x)
    assert sp.integrate(sp.cos(x), x) == sp.sin(x)
    assert sp.integrate(sp.sin(x), x) == -sp.cos(x)
    assert sp.integrate(1 / x, x) == sp.log(x)  # or log(Abs(x)) depending on implementation

    # Definite integrals
    result = sp.integrate(x ** 2, (x, 0, 1))
    assert result == sp.Rational(1, 3)

    result = sp.integrate(sp.sin(x), (x, 0, sp.pi))
    assert result == 2

    # Gaussian-like integral
    result = sp.integrate(sp.exp(-x ** 2), (x, -sp.oo, sp.oo))
    assert result == sp.sqrt(sp.pi)


@unit
def limits(sp: ModuleType):
    """Test symbolic limit computation."""
    x = sp.Symbol('x')

    # Basic limits
    assert sp.limit(x, x, 0) == 0
    assert sp.limit(x + 1, x, 2) == 3

    # Limit at infinity
    assert sp.limit(1 / x, x, sp.oo) == 0
    assert sp.limit(x, x, sp.oo) == sp.oo

    # Important limits
    # lim x->0 sin(x)/x = 1
    assert sp.limit(sp.sin(x) / x, x, 0) == 1

    # lim x->0 (1 - cos(x))/x^2 = 1/2
    result = sp.limit((1 - sp.cos(x)) / x ** 2, x, 0)
    assert result == sp.Rational(1, 2)

    # lim x->oo (1 + 1/x)^x = e
    result = sp.limit((1 + 1 / x) ** x, x, sp.oo)
    assert result == sp.E


@unit
def matrices(sp: ModuleType):
    """Test matrix operations."""
    # Matrix creation
    M = sp.Matrix([[1, 2], [3, 4]])
    assert M.shape == (2, 2)
    assert M[0, 0] == 1
    assert M[1, 1] == 4

    # Matrix arithmetic
    N = sp.Matrix([[5, 6], [7, 8]])

    # Addition
    result = M + N
    assert result == sp.Matrix([[6, 8], [10, 12]])

    # Scalar multiplication
    result = 2 * M
    assert result == sp.Matrix([[2, 4], [6, 8]])

    # Matrix multiplication
    result = M * N
    assert result == sp.Matrix([[19, 22], [43, 50]])

    # Determinant
    assert M.det() == -2  # 1*4 - 2*3 = -2

    # Identity matrix
    I = sp.eye(2)
    assert M * I == M

    # Inverse
    M_inv = M.inv()
    product = M * M_inv
    # Should equal identity (within simplification)
    assert sp.simplify(product - sp.eye(2)) == sp.zeros(2, 2)

    # Transpose
    assert M.T == sp.Matrix([[1, 3], [2, 4]])

    # Symbolic matrices
    x = sp.Symbol('x')
    M_sym = sp.Matrix([[x, 1], [1, x]])
    assert M_sym.det() == x ** 2 - 1


@unit
def series_expansion(sp: ModuleType):
    """Test Taylor/Maclaurin series expansion."""
    x = sp.Symbol('x')

    # Exponential series around 0
    series = sp.series(sp.exp(x), x, 0, 5)
    # Should be 1 + x + x^2/2 + x^3/6 + x^4/24 + O(x^5)
    assert series.removeO() == 1 + x + x ** 2 / 2 + x ** 3 / 6 + x ** 4 / 24

    # Sin series (odd terms only)
    series = sp.series(sp.sin(x), x, 0, 6)
    assert series.removeO() == x - x ** 3 / 6 + x ** 5 / 120

    # Cos series (even terms only)
    series = sp.series(sp.cos(x), x, 0, 6)
    assert series.removeO() == 1 - x ** 2 / 2 + x ** 4 / 24

    # Geometric series 1/(1-x)
    series = sp.series(1 / (1 - x), x, 0, 5)
    assert series.removeO() == 1 + x + x ** 2 + x ** 3 + x ** 4


@unit
def rationals_and_special_numbers(sp: ModuleType):
    """Test rational number handling and special constants."""
    # Rational numbers
    half = sp.Rational(1, 2)
    third = sp.Rational(1, 3)

    assert half + half == 1
    assert half + third == sp.Rational(5, 6)
    assert half * third == sp.Rational(1, 6)

    # Exact arithmetic (no floating point errors)
    result = sp.Rational(1, 10) + sp.Rational(2, 10)
    assert result == sp.Rational(3, 10)

    # Special constants
    assert sp.sqrt(4) == 2
    assert sp.sqrt(2) ** 2 == 2

    # Pi is symbolic
    assert sp.pi != 3.14159
    assert sp.sin(sp.pi) == 0
    assert sp.cos(sp.pi) == -1

    # E (Euler's number)
    assert sp.log(sp.E) == 1

    # Imaginary unit
    assert sp.I ** 2 == -1
    assert sp.I ** 4 == 1

    # Infinity
    assert 1 / sp.oo == 0
    assert sp.oo + 1 == sp.oo


@unit
def trigonometric_functions(sp: ModuleType):
    """Test trigonometric functions and identities."""
    x = sp.Symbol('x')

    # Basic values
    assert sp.sin(0) == 0
    assert sp.cos(0) == 1
    assert sp.tan(0) == 0

    assert sp.sin(sp.pi / 6) == sp.Rational(1, 2)
    assert sp.cos(sp.pi / 3) == sp.Rational(1, 2)
    assert sp.sin(sp.pi / 2) == 1
    assert sp.cos(sp.pi / 2) == 0

    # Pythagorean identity
    identity = sp.sin(x) ** 2 + sp.cos(x) ** 2
    assert sp.simplify(identity) == 1

    # Double angle
    double_sin = sp.expand(sp.sin(2 * x), trig=True)
    assert double_sin == 2 * sp.sin(x) * sp.cos(x)

    # Inverse functions
    assert sp.asin(0) == 0
    assert sp.acos(1) == 0
    assert sp.atan(0) == 0


@unit
def polynomial_operations(sp: ModuleType):
    """Test polynomial-specific operations."""
    x = sp.Symbol('x')

    # Create polynomial
    p = x ** 3 - 6 * x ** 2 + 11 * x - 6

    # Find roots
    roots = sp.solve(p, x)
    assert set(roots) == {1, 2, 3}

    # Polynomial from roots
    p_reconstructed = sp.expand((x - 1) * (x - 2) * (x - 3))
    assert p_reconstructed == p

    # Degree
    assert sp.degree(p, x) == 3
    assert sp.degree(x ** 2 + 1, x) == 2

    # Coefficients
    p = 3 * x ** 2 + 2 * x + 1
    poly = sp.Poly(p, x)
    assert poly.all_coeffs() == [3, 2, 1]

    # Polynomial division
    # (x^2 - 1) / (x - 1) = x + 1
    quotient, remainder = sp.div(x ** 2 - 1, x - 1, x)
    assert quotient == x + 1
    assert remainder == 0

    # GCD of polynomials
    p1 = (x - 1) * (x - 2)
    p2 = (x - 1) * (x - 3)
    gcd = sp.gcd(p1, p2)
    assert sp.expand(gcd) == x - 1 or sp.expand(gcd) == 1 - x  # sign may vary
