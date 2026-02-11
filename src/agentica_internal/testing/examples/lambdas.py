# fmt: off

from agentica_internal.testing.decorators import get_module_functions, runs, invalid, set_checks

__all__ = [
    'lmb_const',
    'lmb_first',
    'lmb_rest',
    'lmb_ternary',
    'lmb_plus_2',
    'lmb_minus_2',
    'lmb_times_2',
    'lmb_div_2',
    'lmb_args',
    'lmb_kwargs',
    'lmb_call',
    'LAMBDAS'
]

lmb_const       = lambda: 5
lmb_first       = lambda x: x[0]
lmb_rest        = lambda x: x[1:]
lmb_ternary     = lambda x: 1 if x else 0
lmb_plus_2      = lambda x: x + 1
lmb_minus_2     = lambda x: x - 1
lmb_times_2     = lambda x: x * 2
lmb_div_2       = lambda x: x / 2
lmb_args        = lambda *x: tuple(x)
lmb_kwargs      = lambda **kwargs: tuple(kwargs.keys())
lmb_call        = lambda x: lmb_plus_2(x)

TAKES_SEQ = lmb_first, lmb_rest,
TAKES_INT = lmb_ternary, lmb_plus_2, lmb_minus_2, lmb_times_2, lmb_div_2, lmb_div_2, lmb_call

set_checks(TAKES_SEQ,  runs([1]), runs((1,)), invalid(), invalid(0))
set_checks(TAKES_INT,  runs(1), invalid())

set_checks(lmb_const,  runs(),  invalid(1))
set_checks(lmb_args,   runs(1, 2, 3))
set_checks(lmb_kwargs, runs(a=1, b=2))

LAMBDAS = get_module_functions(__name__)
