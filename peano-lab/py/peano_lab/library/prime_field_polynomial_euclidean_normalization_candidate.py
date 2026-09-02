"""Actual Euclidean length descent and monic right-associate witnesses.

These working candidate bodies reuse the canonical division, degree,
scalar, convolution and monic-normalization graphs.  The local RightDivides
expansion is exactly existing working ND0342, not a new registered predicate.
The divisor length is S d; zero has retained length zero and no represented
degree.  Monic normalization yields genuine products with LEFT singleton
quotients in both directions.  No gcd induction, Bezout endpoint, arbitrary
division-identity uniqueness, raw-code equality or admission is asserted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import _and, _call, _intro, _lt, _parts, _prime
from peano_lab.library.prime_field_polynomial_candidate import _at, _coeff, _equal, _scale
from peano_lab.library.prime_field_polynomial_convolution_candidate import _convolution, _le
from peano_lab.library.prime_field_polynomial_degree_candidate import _degree
from peano_lab.library.prime_field_polynomial_division_candidate import _division_execution, _remainder_degree
from peano_lab.library.prime_field_polynomial_monic_candidate import _monic, _normalization
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent
from peano_lab.library.prime_field_polynomial_trim_candidate import _trim
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + clause + ')' for clause in (*premises, result))


def _right_divides(p: str, db: str, dc: str, D: str,
                  ab: str, ac: str, L: str, tag: str) -> str:
    """Literal hygienic reuse of ND0342: canonical A and actual Q*D equiv A."""
    qb, qc, Q, pb, pc, P = tuple('pfen_' + role + '_' + tag
                                for role in ('qb', 'qc', 'qlen', 'pb', 'pc', 'plen'))
    witnesses = f'exists {qb} {qc} {Q} {pb} {pc} {P}. ' + _and(
        _convolution(p, qb, qc, Q, db, dc, D, pb, pc, P, tag + '_product'),
        _equivalent(pb, pc, P, ab, ac, L, tag + '_target'))
    return _and(_coeff(p, ab, ac, L, tag + '_canonical'), witnesses)


DIVISION_PARAMETERS = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'd', 'qb', 'qc', 'q', 'rb', 'rc', 'R')


def _descent_row(spec: Callable[..., Any]) -> Any:
    body = _intro(*DIVISION_PARAMETERS, 'hp', 'hexecution')
    body += ('have hdegree : ' + _remainder_degree('p', 'rb', 'rc', 'R', 'd', 'normalization_descent_degree'),)
    body += _call('prime_field_polynomial_division_remainder_degree', *DIVISION_PARAMETERS)
    body += ('exact hp', 'exact hexecution',
             'have hbound : ' + _le('R', 'd', 'normalization_descent_bound'),
             'cases hdegree', 'rewrite hdegree_left')
    body += _call('zero_le', 'd')
    body += ('cases hdegree_right', 'cases hdegree_right_witness',
             'cases hdegree_right_witness_left',
             'rewrite hdegree_right_witness_left_left', 'exact hdegree_right_witness_right',
             'split', 'exact hbound')
    body += _call('succ_le_succ', 'R', 'd') + ('exact hbound',)
    return spec(
        'prime_field_polynomial_division_remainder_length_descent',
        _contract(DIVISION_PARAMETERS, (
            _prime('p', 'normalization_descent_prime'),
            _division_execution(*DIVISION_PARAMETERS, 'normalization_descent_execution'),
        ), _and(_le('R', 'd', 'normalization_descent_weak'),
                _lt('R', 'S d', 'normalization_descent_strict'))),
        ('prime_field_polynomial_division_remainder_degree', 'zero_le', 'succ_le_succ'), body,
        'Every actual normalized remainder has retained length at most d and strictly less than the actual divisor length S d. The zero branch is handled directly; the nonzero branch uses its genuine represented-degree length equation.',
    )


def _constant_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'ab', 'ac', 'L', 'bb', 'bc', 'qb', 'qc', 'q', 'rb', 'rc', 'R')
    actual = ('p', 'ab', 'ac', 'L', 'bb', 'bc', '0', 'qb', 'qc', 'q', 'rb', 'rc', 'R')
    result = _and(_le('R', '0', 'normalization_constant_bound'),
                  _lt('R', 'S 0', 'normalization_constant_strict'))
    body = _intro(*parameters, 'hp', 'hexecution') + ('have hbound : ' + result,)
    body += _call('prime_field_polynomial_division_remainder_length_descent', *actual)
    body += ('exact hp', 'exact hexecution', 'cases hbound')
    body += _call('le_zero', 'R') + ('exact hbound_left',)
    return spec(
        'prime_field_polynomial_division_constant_remainder_empty',
        _contract(parameters, (
            _prime('p', 'normalization_constant_prime'),
            _division_execution(*actual, 'normalization_constant_execution'),
        ), 'R=0'),
        ('prime_field_polynomial_division_remainder_length_descent', 'le_zero'), body,
        'Actual division by the nonzero degree-zero divisor produces an empty normalized remainder, including an empty dividend. This assigns no degree to the zero polynomial.',
    )


def _scale_divisibility_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'k', 'ab', 'ac', 'hb', 'hc', 'L')
    source_scale = _scale('p', 'k', 'ab', 'ac', 'hb', 'hc', 'L', 'normalization_scale_source')
    bounds = _and(_coeff('p', 'ab', 'ac', 'L', 'normalization_scale_A'),
                  _coeff('p', 'hb', 'hc', 'L', 'normalization_scale_H'))
    body = _intro(*parameters, 'hp', 'hs')
    body += ('have hcopy : ' + source_scale, 'exact hs', 'cases hcopy', 'have hbounds : ' + bounds)
    body += _call('prime_field_polynomial_scale_bounded', *parameters)
    body += ('exact hs', 'cases hbounds')
    witnesses = _and(
        _coeff('p', 'ub', 'uc', '1', 'normalization_scale_singleton'),
        _at('ub', 'uc', '0', 'k', 'normalization_scale_head'),
        _scale('p', 'k', 'ab', 'ac', 'vb', 'vc', 'L', 'normalization_scale_constructed'),
        _convolution('p', 'ub', 'uc', '1', 'ab', 'ac', 'L', 'vb', 'vc', 'L', 'normalization_scale_product'))
    body += ('have hactual : exists ub uc vb vc. ' + witnesses,)
    body += _call('prime_field_polynomial_left_constant_product_exists', 'p', 'k', 'ab', 'ac', 'L')
    body += ('exact hp', 'exact hcopy_left', 'exact hbounds_left')
    body += tuple('cases hactual' + '_witness' * i for i in range(4))
    data = 'hactual_witness_witness_witness_witness'
    body += _parts(data, 4)
    body += ('have hequal : ' + _equal('x2', 'x3', 'hb', 'hc', 'L', 'normalization_scale_recode'),)
    body += _call('prime_field_polynomial_scale_functional',
                  'p', 'k', 'ab', 'ac', 'x2', 'x3', 'hb', 'hc', 'L')
    body += ('exact ' + data + '_right_right_left', 'exact hs')
    body += _call('prime_field_polynomial_right_divides_from_product',
                  'p', 'ab', 'ac', 'L', 'hb', 'hc', 'L', 'x', 'x1', '1', 'x2', 'x3', 'L')
    body += ('exact hbounds_right', 'exact ' + data + '_right_right_right')
    body += _call('prime_field_polynomial_equal_implies_equivalent', 'x2', 'x3', 'hb', 'hc', 'L')
    body += ('exact hequal',)
    return spec(
        'prime_field_polynomial_scale_implies_right_divides',
        _contract(parameters, (_prime('p', 'normalization_scale_prime'), source_scale),
                  _right_divides('p', 'ab', 'ac', 'L', 'hb', 'hc', 'L', 'normalization_scale_divides')),
        ('prime_field_polynomial_scale_bounded', 'prime_field_polynomial_left_constant_product_exists',
         'prime_field_polynomial_scale_functional', 'prime_field_polynomial_right_divides_from_product',
         'prime_field_polynomial_equal_implies_equivalent'), body,
        'A genuine scalar output is a right multiple of its source: construct an actual LEFT singleton quotient and actual product, then transport the independently encoded product to the supplied target by decoded-prefix equality. Empty inputs and scalar zero are included.',
    )


def _monic_associates_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'k', 'gb', 'gc', 'hb', 'hc', 'L')
    graph = _normalization(*parameters, 'normalization_associates_actual')
    body = _intro(*parameters, 'hp', 'hnormalization')
    body += ('have hcopy : ' + graph, 'exact hnormalization') + _parts('hcopy', 3)
    body += ('split',)
    body += _call('prime_field_polynomial_scale_implies_right_divides', *parameters)
    body += ('exact hp', 'exact hcopy_right_right',
             'cases hcopy_right_left', 'cases hcopy_right_left_witness')
    reverse = _scale('p', 'x', 'hb', 'hc', 'gb', 'gc', 'L', 'normalization_associates_reverse')
    body += ('have hreverse : ' + reverse,)
    body += _call('prime_field_polynomial_inverse_scale', 'p', 'x', 'k', 'gb', 'gc', 'hb', 'hc', 'L')
    body += ('exact hp', 'exact hcopy_right_left_witness_right', 'exact hcopy_right_right')
    body += _call('prime_field_polynomial_scale_implies_right_divides',
                  'p', 'x', 'hb', 'hc', 'gb', 'gc', 'L')
    body += ('exact hp', 'exact hreverse')
    return spec(
        'prime_field_polynomial_monic_normalization_right_associates',
        _contract(parameters, (_prime('p', 'normalization_associates_prime'), graph), _and(
            _right_divides('p', 'gb', 'gc', 'L', 'hb', 'hc', 'L', 'normalization_associates_forward'),
            _right_divides('p', 'hb', 'hc', 'L', 'gb', 'gc', 'L', 'normalization_associates_backward'))),
        ('prime_field_polynomial_scale_implies_right_divides', 'prime_field_polynomial_inverse_scale'), body,
        'An actual monic normalization and its genuinely inverted scalar action supply actual right-divisibility witnesses in both directions. These witnesses use left constant quotients; no polynomial commutativity, unit-associate oracle, or equality of beta codes is used.',
    )


def _normalized_associate_exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'ab', 'ac', 'L')
    body = _intro(*parameters, 'hp', 'hA')
    body += ('have hp0 : ~(p=0)', 'intro hpzero') + _call('prime_nonzero', 'p')
    body += ('exact hp', 'exact hpzero')
    trim = _trim('p', 'ab', 'ac', 'L', 't', 'tb', 'tc', 'M', 'normalized_associate_trim')
    body += ('have htrim : exists t tb tc M. ' + trim,)
    body += _call('prime_field_polynomial_trim_exists', *parameters) + ('exact hA',)
    body += tuple('cases htrim' + '_witness' * i for i in range(4))
    data = 'htrim_witness_witness_witness_witness'
    body += ('have hT : ' + _coeff('p', 'x1', 'x2', 'x3', 'normalized_associate_trim_bound'),)
    body += _call('prime_field_polynomial_trim_output_coefficients',
                  'p', 'ab', 'ac', 'L', 'x', 'x1', 'x2', 'x3') + ('exact ' + data,)
    equivalent = _equivalent('x1', 'x2', 'x3', 'ab', 'ac', 'L', 'normalized_associate_trim_equivalent')
    body += ('have hTA : ' + equivalent,)
    body += _call('prime_field_polynomial_equivalent_symmetric', 'ab', 'ac', 'L', 'x1', 'x2', 'x3')
    body += _call('prime_field_polynomial_trim_equivalent',
                  'p', 'ab', 'ac', 'L', 'x', 'x1', 'x2', 'x3') + ('exact ' + data,)
    body += ('have hcase : x3=0 \\/ ~(x3=0)',) + _call('eq_decidable', 'x3', '0')
    body += ('cases hcase',)

    # Empty trim: actual empty products give both directions after formal
    # target transport.  Neither a leading value nor a degree is requested.
    body += _rewrite_all('hcase_left',
                         _coeff('p', 'x1', 'x2', 'x3', 'normalized_associate_empty_bound'),
                         'x3', 'hT')
    body += _rewrite_all('hcase_left', equivalent, 'x3', 'hTA')
    body += ('exists x1', 'exists x2', 'exists 0', 'split', 'left', 'refl', 'split')
    body += _call('prime_field_polynomial_right_divides_empty', 'p', 'ab', 'ac', 'L', 'x1', 'x2')
    body += ('exact hA',)
    body += _call('prime_field_polynomial_right_divides_equivalent_target',
                  'p', 'x1', 'x2', '0', 'x1', 'x2', '0', 'ab', 'ac', 'L')
    body += ('exact hA',)
    body += _call('prime_field_polynomial_right_divides_empty', 'p', 'x1', 'x2', '0', 'x1', 'x2')
    body += ('exact hT', 'exact hTA')

    # Nonempty trim: its genuine represented degree makes the canonical
    # leading-inverse normalization constructor applicable.
    degree = _degree('p', 'x1', 'x2', 'x3', 'd', 'normalized_associate_degree')
    body += ('have hdegree : exists d. ' + degree,)
    body += _call('prime_field_polynomial_trim_nonempty_degree_exists',
                  'p', 'ab', 'ac', 'L', 'x', 'x1', 'x2', 'x3')
    body += ('exact ' + data, 'exact hcase_right', 'cases hdegree')
    normalization = _normalization('p', 'k', 'x1', 'x2', 'hb', 'hc', 'x3', 'normalized_associate_monic')
    body += ('have hnormalization : exists k hb hc. ' + normalization,)
    body += _call('prime_field_polynomial_monic_normalization_exists', 'p', 'x1', 'x2', 'x3', 'x4')
    body += ('exact hp', 'exact hdegree_witness')
    body += tuple('cases hnormalization' + '_witness' * i for i in range(3))
    normalized = 'hnormalization_witness_witness_witness'
    associates = _and(
        _right_divides('p', 'x1', 'x2', 'x3', 'x6', 'x7', 'x3', 'normalized_associate_forward'),
        _right_divides('p', 'x6', 'x7', 'x3', 'x1', 'x2', 'x3', 'normalized_associate_backward'))
    body += ('have hassociates : ' + associates,)
    body += _call('prime_field_polynomial_monic_normalization_right_associates',
                  'p', 'x5', 'x1', 'x2', 'x6', 'x7', 'x3')
    body += ('exact hp', 'exact ' + normalized, 'cases hassociates',
             'exists x6', 'exists x7', 'exists x3', 'split', 'right')
    body += _call('prime_field_polynomial_monic_normalization_monic',
                  'p', 'x5', 'x1', 'x2', 'x6', 'x7', 'x3') + ('exact ' + normalized, 'split')
    # Replace the divisor T by the genuinely equivalent original A.
    body += _call('prime_field_polynomial_right_divides_equivalent_divisor',
                  'p', 'x1', 'x2', 'x3', 'x6', 'x7', 'x3', 'ab', 'ac', 'L')
    body += ('exact hp0', 'exact hA', 'exact hTA', 'exact hassociates_left')
    # In the reverse direction replace the target T by that same original A.
    body += _call('prime_field_polynomial_right_divides_equivalent_target',
                  'p', 'x6', 'x7', 'x3', 'x1', 'x2', 'x3', 'ab', 'ac', 'L')
    body += ('exact hA', 'exact hassociates_right', 'exact hTA')
    normal = 'H=0 \\/ (' + _monic('p', 'hb', 'hc', 'H', 'normalized_associate_result_monic') + ')'
    result = 'exists hb hc H. ' + _and(
        normal,
        _right_divides('p', 'ab', 'ac', 'L', 'hb', 'hc', 'H', 'normalized_associate_result_forward'),
        _right_divides('p', 'hb', 'hc', 'H', 'ab', 'ac', 'L', 'normalized_associate_result_backward'))
    return spec(
        'prime_field_polynomial_normalized_right_associate_exists',
        _contract(parameters, (_prime('p', 'normalized_associate_prime'),
                               _coeff('p', 'ab', 'ac', 'L', 'normalized_associate_input')), result),
        ('prime_nonzero', 'prime_field_polynomial_trim_exists',
         'prime_field_polynomial_trim_output_coefficients', 'prime_field_polynomial_equivalent_symmetric',
         'prime_field_polynomial_trim_equivalent', 'eq_decidable',
         'prime_field_polynomial_right_divides_empty', 'prime_field_polynomial_right_divides_equivalent_target',
         'prime_field_polynomial_trim_nonempty_degree_exists', 'prime_field_polynomial_monic_normalization_exists',
         'prime_field_polynomial_monic_normalization_right_associates',
         'prime_field_polynomial_monic_normalization_monic', 'prime_field_polynomial_right_divides_equivalent_divisor'), body,
        'Construct a zero-or-monic right associate of every canonical polynomial, first trimming its actual leading zeros and then normalizing only a nonempty trim. Both divisibility directions have real product witnesses and are transported to the original representation. Empty and all-zero encodings need no degree or inverse of zero.',
    )


def make_prime_field_polynomial_euclidean_normalization_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (_descent_row(spec), _constant_row(spec), _scale_divisibility_row(spec),
            _monic_associates_row(spec), _normalized_associate_exists_row(spec))


__all__ = ['make_prime_field_polynomial_euclidean_normalization_candidate_theorems']
