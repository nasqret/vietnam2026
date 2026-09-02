"""Distributive lifts for actual products and independently sized sums.

An aligned sum supplies real common representatives and an actual fixed-
length addition.  The original canonical constructor produces three real
proper products of those representatives at one length.  Formal convolution
congruence connects them to the three supplied products, without assuming
any output identity.  Both fixed-factor orientations are retained.

The grouped aligned-addition builders are literal copies of the preceding
working layer and are independently checked by the focused tests.  There is
no package alias, new operation, admitted theorem, or gcd assertion here.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _parts, _prime, _public,
)
from peano_lab.library.prime_field_polynomial_candidate import _add, _coeff
from peano_lab.library.prime_field_polynomial_convolution_candidate import _convolution
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent


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


def prime_field_polynomial_distributivity_aligned_add_relation(
        p: str, ab: str, ac: str, L: str, bb: str, bc: str, M: str,
        rb: str, rc: str, N: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """The existing actual aligned-addition graph, with grouped witnesses."""
    return _public(_aligned_add, (p, ab, ac, L, bb, bc, M, rb, rc, N),
                   tag=tag, variables=variables)


U, V, W = ('ub', 'uc', 'L'), ('vb', 'vc', 'M'), ('wb', 'wc', 'N')
D = ('db', 'dc', 'J')
P, Q, R = ('pb', 'pc', 'H'), ('qb', 'qc', 'I'), ('rb', 'rc', 'K')
PARAMETERS = ('p', *U, *V, *W, *D, *P, *Q, *R)


def _factors(side: str, changing: tuple[str, str, str]) -> tuple[str, ...]:
    return (*D, *changing) if side == 'left' else (*changing, *D)


def _lift_row(spec: Callable[..., Any], side: str) -> Any:
    factors = tuple(_factors(side, value) for value in (U, V, W))
    originals = tuple(_convolution('p', *factor, *output, 'aligned_' + side + '_' + output[0])
                      for factor, output in zip(factors, (P, Q, R), strict=True))
    body = _intro(*PARAMETERS, 'hp', 'hs', 'hP', 'hQ', 'hR')
    body += ('have hp0 : ~(p=0)', 'intro hpzero')
    body += _call('prime_nonzero', 'p') + ('exact hp', 'exact hpzero')
    body += ('have hfactor : ' + originals[0], 'exact hP', 'cases hfactor')
    if side == 'right':
        body += ('cases hfactor_right',)
    divisor_bound = 'hfactor_left' if side == 'left' else 'hfactor_right_left'

    body += _parts('hs', 4)
    tail = 'hs_right_right_right'
    for _ in range(7):
        body += ('cases ' + tail,)
        tail += '_witness'
    body += _parts(tail, 3) + ('cases ' + tail + '_left',)
    representatives = (('x', 'x1', 'x6'), ('x2', 'x3', 'x6'), ('x4', 'x5', 'x6'))
    temporary_codes = (('PB', 'PC'), ('QB', 'QC'), ('RB', 'RC'))
    constructed = 'exists O PB PC QB QC RB RC. ' + _and(
        *(_convolution('p', *_factors(side, value), *codes, 'O',
                       'aligned_' + side + '_constructed_' + codes[0])
          for value, codes in zip(representatives, temporary_codes, strict=True)),
        _add('p', 'PB', 'PC', 'QB', 'QC', 'RB', 'RC', 'O',
             'aligned_' + side + '_constructed_sum'))
    body += ('have hproducts : ' + constructed,)
    body += _call('prime_field_polynomial_' + side + '_distributive_products_exists',
                  'p', 'x', 'x1', 'x2', 'x3', 'x4', 'x5', 'x6', *D)
    body += ('exact hp0', 'exact ' + divisor_bound, 'exact ' + tail + '_right_left')
    products_tail = 'hproducts'
    for _ in range(7):
        body += ('cases ' + products_tail,)
        products_tail += '_witness'
    body += _parts(products_tail, 4)

    # The new product codes have one actual proper length x7, even if any
    # supplied product uses a different representation length or empty code.
    outputs = (('x8', 'x9', 'x7'), ('x10', 'x11', 'x7'), ('x12', 'x13', 'x7'))
    body += _call('prime_field_polynomial_aligned_add_from_common',
                  'p', *P, *Q, *R, 'x8', 'x9', 'x10', 'x11', 'x12', 'x13', 'x7')
    for factor, output, hypothesis in zip(factors, (P, Q, R), ('hP', 'hQ', 'hR'), strict=True):
        body += _call('prime_field_polynomial_convolution_bounded', 'p', *factor, *output)
        body += ('exact ' + hypothesis,)
    body += ('split',)
    congruence = 'prime_field_polynomial_convolution_equivalent_congruent_' + (
        'right' if side == 'left' else 'left')
    for index, (factor, output, representative, replacement, hypothesis) in enumerate(zip(
            factors[:2], (P, Q), representatives[:2], outputs[:2], ('hP', 'hQ'), strict=True)):
        body += _call(congruence, 'p', *factor, *output, *representative, *replacement)
        equivalent_hypothesis = tail + ('_left_left' if index == 0 else '_left_right')
        product_hypothesis = products_tail + ('_left' if index == 0 else '_right_left')
        body += ('exact hp0', 'exact ' + equivalent_hypothesis,
                 'exact ' + hypothesis, 'exact ' + product_hypothesis)
    body += ('exact ' + products_tail + '_right_right_right',)
    # The original aligned graph gives E(W_representative,W), the direction
    # needed to transport the constructed sum-product to the supplied R.
    body += _call(congruence, 'p', *_factors(side, representatives[2]), *outputs[2], *W, *R)
    body += ('exact hp0', 'exact ' + tail + '_right_right',
             'exact ' + products_tail + '_right_right_left', 'exact hR')
    return spec(
        'prime_field_polynomial_aligned_convolution_' + side + '_add',
        _contract(PARAMETERS,
                  (_prime('p', 'aligned_' + side + '_prime'),
                   _aligned_add('p', *U, *V, *W, 'aligned_' + side + '_input'),
                   *originals),
                  _aligned_add('p', *P, *Q, *R, 'aligned_' + side + '_result')),
        ('prime_nonzero',
         'prime_field_polynomial_' + side + '_distributive_products_exists',
         'prime_field_polynomial_aligned_add_from_common',
         'prime_field_polynomial_convolution_bounded', congruence),
        body,
        'Actual ' + side + ' products distribute over an independently represented aligned sum: construct real equal-length products of its witnesses and prove formal equivalence to the three supplied outputs, including empty-factor cases.',
    )


def make_prime_field_polynomial_aligned_distributivity_candidate_theorems(
        spec: Callable[..., Any]) -> tuple[Any, ...]:
    return _lift_row(spec, 'left'), _lift_row(spec, 'right')


__all__ = [
    'prime_field_polynomial_distributivity_aligned_add_relation',
    'make_prime_field_polynomial_aligned_distributivity_candidate_theorems',
]
