"""An actual division execution gives a proper product and an aligned sum.

The aligned-addition builders below are literal copies of the preceding
working alignment layer.  Their grouped common-representative clause is
checked independently by the focused tests; this module imports no working
module and installs no package alias.  The two rows use only actual decoded
coefficient graphs and formal power-coefficient equivalence.

An empty quotient is handled by constructing the genuine length-zero
product and proving that the division execution's ambient zero prefix
represents it.  No universal ambient/proper-length equality, polynomial
division uniqueness, gcd result, or new proof authority is asserted here.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _parts, _prime, _public,
)
from peano_lab.library.prime_field_polynomial_candidate import _add, _coeff
from peano_lab.library.prime_field_polynomial_convolution_candidate import _convolution
from peano_lab.library.prime_field_polynomial_division_candidate import (
    _coefficient_identity, _division_execution,
)
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent
from peano_lab.library.prime_field_polynomial_trim_candidate import _trim
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + clause + ')' for clause in (*premises, result))


def _common_representatives(ab: str, ac: str, L: str, bb: str, bc: str, M: str,
                           ub: str, uc: str, vb: str, vc: str, K: str, tag: str) -> str:
    return _and(_equivalent(ab, ac, L, ub, uc, K, tag + '_left'),
                _equivalent(bb, bc, M, vb, vc, K, tag + '_right'))


def _aligned_witness(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str,
                     rb: str, rc: str, N: str, ub: str, uc: str, vb: str, vc: str,
                     tb: str, tc: str, K: str, tag: str) -> str:
    return _and(_common_representatives(ab, ac, L, bb, bc, M, ub, uc, vb, vc, K,
                                        tag + '_common'),
                _add(p, ub, uc, vb, vc, tb, tc, K, tag + '_operation'),
                _equivalent(tb, tc, K, rb, rc, N, tag + '_output'))


def _aligned_add(p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str,
                 rb: str, rc: str, N: str, tag: str) -> str:
    witnesses = tuple('pfaa_' + role + '_' + tag
                      for role in ('left_b', 'left_c', 'right_b', 'right_c',
                                   'sum_b', 'sum_c', 'length'))
    return _and(_coeff(p, ab, ac, L, tag + '_left_bounded'),
                _coeff(p, bb, bc, M, tag + '_right_bounded'),
                _coeff(p, rb, rc, N, tag + '_result_bounded'),
                'exists ' + ' '.join(witnesses) + '. '
                + _aligned_witness(p, ab, ac, L, bb, bc, M, rb, rc, N,
                                   *witnesses, tag + '_witness'))


def prime_field_polynomial_euclidean_aligned_add_relation(
        p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str,
        rb: str, rc: str, N: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """The actual grouped aligned-addition graph used by both candidate rows."""
    return _public(_aligned_add, (p, ab, ac, L, bb, bc, M, rb, rc, N),
                   tag=tag, variables=variables)


TRIM_PARAMETERS = ('p', 'pb', 'pc', 'N', 'xb', 'xc', 'ub', 'uc',
                   'ab', 'ac', 'L', 't', 'rb', 'rc', 'R')
EXECUTION_PARAMETERS = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'd',
                        'qb', 'qc', 'q', 'rb', 'rc', 'R')


def _add_trim_row(spec: Callable[..., Any]) -> Any:
    premises = (
        _coeff('p', 'pb', 'pc', 'N', 'trim_aligned_product_bounded'),
        _equivalent('pb', 'pc', 'N', 'xb', 'xc', 'L', 'trim_aligned_product'),
        _add('p', 'xb', 'xc', 'ub', 'uc', 'ab', 'ac', 'L', 'trim_aligned_sum'),
        _trim('p', 'ub', 'uc', 'L', 't', 'rb', 'rc', 'R', 'trim_aligned_trim'),
    )
    body = _intro(*TRIM_PARAMETERS, 'hproduct', 'hequivalent', 'hadd', 'htrim')
    body += ('have hbounds : ' + _and(
        _coeff('p', 'xb', 'xc', 'L', 'trim_aligned_left_bound'),
        _coeff('p', 'ub', 'uc', 'L', 'trim_aligned_right_bound'),
        _coeff('p', 'ab', 'ac', 'L', 'trim_aligned_sum_bound')),)
    body += _call('prime_field_polynomial_add_bounded',
                  'p', 'xb', 'xc', 'ub', 'uc', 'ab', 'ac', 'L')
    body += ('exact hadd',) + _parts('hbounds', 3)
    body += ('have hremainder : '
             + _coeff('p', 'rb', 'rc', 'R', 'trim_aligned_remainder_bound'),)
    body += _call('prime_field_polynomial_trim_output_coefficients',
                  'p', 'ub', 'uc', 'L', 't', 'rb', 'rc', 'R')
    body += ('exact htrim',)
    body += ('have hreverse : '
             + _equivalent('rb', 'rc', 'R', 'ub', 'uc', 'L', 'trim_aligned_reverse'),)
    body += _call('prime_field_polynomial_equivalent_symmetric',
                  'ub', 'uc', 'L', 'rb', 'rc', 'R')
    body += _call('prime_field_polynomial_trim_equivalent',
                  'p', 'ub', 'uc', 'L', 't', 'rb', 'rc', 'R')
    body += ('exact htrim', 'split', 'exact hproduct', 'split',
             'exact hremainder', 'split', 'exact hbounds_right_right')
    body += tuple('exists ' + value for value in ('xb', 'xc', 'ub', 'uc', 'ab', 'ac', 'L'))
    body += ('split', 'split', 'exact hequivalent', 'exact hreverse',
             'split', 'exact hadd')
    body += _call('prime_field_polynomial_power_coefficient_functional', 'ab', 'ac', 'L')
    return spec(
        'prime_field_polynomial_add_trim_aligned',
        _contract(TRIM_PARAMETERS, premises,
                  _aligned_add('p', 'pb', 'pc', 'N', 'rb', 'rc', 'R',
                               'ab', 'ac', 'L', 'trim_aligned_result')),
        ('prime_field_polynomial_add_bounded',
         'prime_field_polynomial_trim_output_coefficients',
         'prime_field_polynomial_equivalent_symmetric',
         'prime_field_polynomial_trim_equivalent',
         'prime_field_polynomial_power_coefficient_functional'),
        body,
        'An actual fixed-length sum and actual trim supply real common representatives for the canonical product and trimmed remainder; no prime premise or equality of unused beta entries is needed.',
    )


def _execution_identity_row(spec: Callable[..., Any]) -> Any:
    result = 'exists pb pc N. ' + _and(
        _convolution('p', 'qb', 'qc', 'q', 'bb', 'bc', 'S d',
                     'pb', 'pc', 'N', 'execution_aligned_product'),
        _aligned_add('p', 'pb', 'pc', 'N', 'rb', 'rc', 'R',
                     'ab', 'ac', 'L', 'execution_aligned_sum'),
    )
    body = _intro(*EXECUTION_PARAMETERS, 'hp', 'he')
    body += ('have hidentity : '
             + _coefficient_identity(*EXECUTION_PARAMETERS, 'execution_aligned_identity'),)
    body += _call('prime_field_polynomial_division_coefficient_identity', *EXECUTION_PARAMETERS)
    body += ('exact hp', 'exact he')
    tail = 'hidentity'
    for _ in range(5):
        body += ('cases ' + tail,)
        tail += '_witness'
    body += _parts(tail, 3) + _parts('he', 4)
    addition, trimming, product = tail + '_right_left', tail + '_right_right', tail + '_left'
    body += ('have hbounds : ' + _and(
        _coeff('p', 'x', 'x1', 'L', 'execution_aligned_ambient_bound'),
        _coeff('p', 'x2', 'x3', 'L', 'execution_aligned_residual_bound'),
        _coeff('p', 'ab', 'ac', 'L', 'execution_aligned_input_bound')),)
    body += _call('prime_field_polynomial_add_bounded',
                  'p', 'x', 'x1', 'x2', 'x3', 'ab', 'ac', 'L')
    body += ('exact ' + addition,) + _parts('hbounds', 3)
    body += ('cases ' + product, 'cases ' + product + '_left',
             'exists 0', 'exists 0', 'exists 0', 'split')

    # The proper product of an empty quotient really has length zero.  The
    # arbitrary quotient codes need only their vacuous bounded prefix.
    body += _call('prime_field_polynomial_convolution_empty',
                  'p', 'qb', 'qc', 'q', 'bb', 'bc', 'S d', '0', '0')
    body += _rewrite_all(product + '_left_left',
                         _coeff('p', 'qb', 'qc', 'q', 'execution_aligned_empty_quotient'), 'q')
    body += _intro('empty_i', 'empty_hi') + ('exfalso',)
    body += _call('lt_not_le', 'empty_i', '0') + ('exact empty_hi',)
    body += _call('zero_le', 'empty_i')
    body += ('exact he_right_left', 'left', 'exact ' + product + '_left_left')
    body += _call('prime_field_polynomial_add_trim_aligned',
                  'p', '0', '0', '0', 'x', 'x1', 'x2', 'x3',
                  'ab', 'ac', 'L', 'x4', 'rb', 'rc', 'R')
    body += _intro('zero_i', 'zero_hi') + ('exfalso',)
    body += _call('lt_not_le', 'zero_i', '0') + ('exact zero_hi',)
    body += _call('zero_le', 'zero_i')
    body += _call('prime_field_polynomial_equivalent_symmetric', 'x', 'x1', 'L', '0', '0', '0')
    body += _call('prime_field_polynomial_zero_prefix_equivalent_empty', 'x', 'x1', 'L')
    body += ('exact ' + product + '_left_right', 'exact ' + addition, 'exact ' + trimming)

    # In the nonempty branch the inherited identity already supplies the
    # actual proper product at ambient length L; its real codes are reused.
    body += ('cases ' + product + '_right', 'exists x', 'exists x1', 'exists L',
             'split', 'exact ' + product + '_right_right')
    body += _call('prime_field_polynomial_add_trim_aligned',
                  'p', 'x', 'x1', 'L', 'x', 'x1', 'x2', 'x3',
                  'ab', 'ac', 'L', 'x4', 'rb', 'rc', 'R')
    body += ('exact hbounds_left',)
    body += _call('prime_field_polynomial_power_coefficient_functional', 'x', 'x1', 'L')
    body += ('exact ' + addition, 'exact ' + trimming)
    return spec(
        'prime_field_polynomial_division_execution_aligned_identity',
        _contract(EXECUTION_PARAMETERS,
                  (_prime('p', 'execution_aligned_prime'),
                   _division_execution(*EXECUTION_PARAMETERS, 'execution_aligned_source')),
                  result),
        ('prime_field_polynomial_division_coefficient_identity',
         'prime_field_polynomial_add_bounded',
         'prime_field_polynomial_convolution_empty', 'lt_not_le', 'zero_le',
         'prime_field_polynomial_add_trim_aligned',
         'prime_field_polynomial_equivalent_symmetric',
         'prime_field_polynomial_zero_prefix_equivalent_empty',
         'prime_field_polynomial_power_coefficient_functional'),
        body,
        'Every actual prime-field division execution yields an actual proper Q*B product and the aligned formal identity A=Q*B+R, including an empty quotient whose ambient zero product has a different length.',
    )


def make_prime_field_polynomial_euclidean_identity_candidate_theorems(
        spec: Callable[..., Any]) -> tuple[Any, ...]:
    return _add_trim_row(spec), _execution_identity_row(spec)


__all__ = [
    'prime_field_polynomial_euclidean_aligned_add_relation',
    'make_prime_field_polynomial_euclidean_identity_candidate_theorems',
]
