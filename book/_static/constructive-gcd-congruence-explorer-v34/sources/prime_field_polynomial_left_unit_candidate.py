"""Working actual left-unit convolution and right-divisibility reflexivity.

These native candidate scripts are not admitted theorems. They use a real
length-one unit, real antidiagonal sums and formal coefficient equivalence.
There is no multiplication-commutativity premise or evaluation-only shortcut.
All relation expansions reuse existing conservative definitions; the last
contract is the self-instance of working ND0342, not a new public alias.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _lt, _parts, _prime, _residue,
)
from peano_lab.library.prime_field_polynomial_candidate import (
    _at, _coeff, _equal, _repeat,
)
from peano_lab.library.prime_field_polynomial_convolution_candidate import (
    _coefficient, _convolution, _diagonal, _le, _sum, _term,
)
from peano_lab.library.prime_field_polynomial_convolution_padding_candidate import _tail
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], result: str) -> str:
    return 'forall ' + ' '.join(parameters) + '. ' + ' -> '.join(
        '(' + part + ')' for part in (*premises, result))


U = ('ub', 'uc', '1')
A = ('ab', 'ac', 'L')
C = ('cb', 'cc', 'L')


def _term_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    parameters = ('ub', 'uc', *A, 'i', 'a', 't')
    body = _intro(*parameters, 'hu', 'hi', 'ha', 'ht')
    body += _call('polynomial_diagonal_term_functional', *U, *A, 'i', '0', 't', 'a')
    body += ('exact ht', 'exists i', 'exists 1', 'exists a', 'split',
             'apply zero_add', 'split', 'left', 'split', 'exists 0',
             'apply zero_add', 'exact hu', 'split', 'left', 'split',
             'exact hi', 'exact ha', 'symm', 'apply one_mul')
    first = spec(
        'polynomial_diagonal_left_unit_first_term',
        _contract(parameters, (
            _at('ub', 'uc', '0', '1', 'unit_first_entry'),
            _lt('i', 'L', 'unit_first_index'), _at('ab', 'ac', 'i', 'a', 'unit_first_A'),
            _term(*U, *A, 'i', '0', 't', 'unit_first_actual'),
        ), 't=a'),
        ('polynomial_diagonal_term_functional', 'zero_add', 'one_mul'), body,
        'The first actual antidiagonal term of a length-one left unit is the chosen right-input coefficient, without any primality or commutativity assumption.',
    )
    parameters = ('ub', 'uc', *A, 'i', 'j', 't')
    body = _intro(*parameters, 'hj', 'ht')
    body += tuple('cases ht' + '_witness' * i for i in range(3))
    inner = 'ht_witness_witness_witness'
    body += _parts(inner, 4) + ('have hz : x1=0',)
    body += _call('polynomial_zero_extended_entry_functional', 'ub', 'uc', '1', 'j', 'x1', '0')
    body += ('exact ' + inner + '_right_left', 'right', 'split', 'exact hj', 'refl',
             'trans x1*x2', 'exact ' + inner + '_right_right_right', 'rewrite hz',
             'apply mul_zero_left')
    tail = spec(
        'polynomial_diagonal_left_unit_tail_term',
        _contract(parameters, (
            _le('1', 'j', 'unit_tail_index'),
            _term(*U, *A, 'i', 'j', 't', 'unit_tail_actual'),
        ), 't=0'),
        ('polynomial_zero_extended_entry_functional', 'mul_zero_left'), body,
        'Every later term is zero because its left input index is outside a genuine length-one prefix. The value of that prefix is irrelevant here.',
    )
    return first, tail


def _sum_row(spec: Callable[..., Any]) -> Any:
    parameters = ('ub', 'uc', *A, 'i', 'a', 'db', 'dc', 'n')
    body = _intro(*parameters, 'hu', 'hi', 'ha', 'hd', 'hs')
    body += ('have hhead : ' + _at('db', 'dc', '0', 'a', 'unit_sum_head'),)
    point = _and(_at('db', 'dc', '0', 't', 'unit_sum_first_entry'),
                 _term(*U, *A, 'i', '0', 't', 'unit_sum_first_term'))
    body += ('have hv : exists t. ' + point,) + _call('hd', '0')
    body += ('exists i', 'simp', 'cases hv', 'cases hv_witness', 'have heq : x=a')
    body += _call('polynomial_diagonal_left_unit_first_term', 'ub', 'uc', *A, 'i', 'a', 'x')
    body += ('exact hu', 'exact hi', 'exact ha', 'exact hv_witness_right')
    body += _rewrite_all('heq', _at('db', 'dc', '0', 'x', 'unit_sum_head_rewrite'),
                         'x', 'hv_witness_left') + ('exact hv_witness_left',)
    body += ('have htail : ' + _tail('db', 'dc', '1', 'i', 'unit_sum_tail'),)
    body += _intro('j', 'hj')
    point = _and(_at('db', 'dc', '1+j', 't', 'unit_sum_tail_entry'),
                 _term(*U, *A, 'i', '1+j', 't', 'unit_sum_tail_term'))
    body += ('have hv : exists t. ' + point,) + _call('hd', '1+j')
    body += ('have hindex : 1+j=S j', 'simp [add_succ_left,zero_add]')
    body += _rewrite_all('hindex', _lt('1+j', 'S i', 'unit_sum_tail_index'), '1+j')
    body += _call('succ_le_succ', 'S j', 'i') + ('exact hj', 'cases hv', 'cases hv_witness',
                                                              'have heq : x=0')
    body += _call('polynomial_diagonal_left_unit_tail_term', 'ub', 'uc', *A, 'i', '1+j', 'x')
    body += _call('le_add_right', '1', 'j') + ('exact hv_witness_right',)
    body += _rewrite_all('heq', _at('db', 'dc', '1+j', 'x', 'unit_sum_tail_rewrite'),
                         'x', 'hv_witness_left') + ('exact hv_witness_left',)
    body += ('have hsingle : exists m. (' + _sum('db', 'dc', '1', 'm', 'unit_single_sum') + ')',)
    body += _call('beta_sum_exists', 'db', 'dc', '1') + ('cases hsingle',)
    decomposition = _and(_at('db', 'dc', '0', 't', 'unit_single_entry'),
                         _sum('db', 'dc', '0', 's', 'unit_single_empty'), 'x=s+t')
    body += ('have hdecomp : exists t s. ' + decomposition,)
    body += _call('beta_sum_succ_decompose', 'db', 'dc', '0', 'x')
    body += ('exact hsingle_witness', 'cases hdecomp', 'cases hdecomp_witness')
    body += _parts('hdecomp_witness_witness', 3)
    body += ('have hzero : x2=0',) + _call('beta_sum_zero', 'db', 'dc', 'x2')
    body += ('exact hdecomp_witness_witness_right_left', 'have hentry : x1=a')
    body += _call('beta_at_unique', 'db', 'dc', '0', 'x1', 'a')
    body += ('exact hdecomp_witness_witness_left', 'exact hhead', 'have hvalue : x=a',
             'trans x2+x1', 'exact hdecomp_witness_witness_right_right', 'rewrite hzero',
             'trans x1', 'apply zero_add', 'exact hentry', 'trans x')
    body += _call('polynomial_zero_tail_natural_sum_invariant',
                  'db', 'dc', 'db', 'dc', '1', 'i', 'x', 'n')
    body += _intro('k', 'v', 'hk', 'hv') + ('exact hv', 'exact htail', 'exact hsingle_witness',
                                          'have hlength : 1+i=S i', 'simp [add_succ_left,zero_add]')
    body += _rewrite_all('hlength', _sum('db', 'dc', '1+i', 'n', 'unit_sum_length_rewrite'), '1+i')
    body += ('exact hs', 'exact hvalue')
    return spec(
        'polynomial_diagonal_left_unit_natural_sum',
        _contract(parameters, (
            _at('ub', 'uc', '0', '1', 'unit_sum_unit'), _lt('i', 'L', 'unit_sum_index'),
            _at('ab', 'ac', 'i', 'a', 'unit_sum_A'),
            _diagonal(*U, *A, 'i', 'db', 'dc', 'S i', 'unit_sum_diagonal'),
            _sum('db', 'dc', 'S i', 'n', 'unit_sum_actual'),
        ), 'n=a'),
        ('polynomial_diagonal_left_unit_first_term', 'polynomial_diagonal_left_unit_tail_term',
         'add_succ_left', 'zero_add', 'succ_le_succ', 'le_add_right', 'beta_sum_exists',
         'beta_sum_succ_decompose', 'beta_sum_zero', 'beta_at_unique',
         'polynomial_zero_tail_natural_sum_invariant'), body,
        'An actual unit-left antidiagonal sum equals its first coefficient: construct the one-term sum and use the proved zero-tail invariant on all remaining actual summands.',
    )


def _coefficient_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', 'ub', 'uc', *A, 'i', 'a', 'r')
    body = _intro(*parameters, 'hu', 'hi', 'ha', 'hb', 'hr')
    body += tuple('cases hr' + '_witness' * i for i in range(3))
    inner = 'hr_witness_witness_witness'
    body += _parts(inner, 3) + ('have hn : x2=a',)
    body += _call('polynomial_diagonal_left_unit_natural_sum',
                  'ub', 'uc', *A, 'i', 'a', 'x', 'x1', 'x2')
    body += ('exact hu', 'exact hi', 'exact ha', 'exact ' + inner + '_left',
             'exact ' + inner + '_right_left')
    body += _rewrite_all('hn', _residue('p', 'x2', 'r', 'unit_coefficient_residue_rewrite'),
                         'x2', inner + '_right_right')
    body += _call('prime_field_residue_bounded_value', 'p', 'a', 'r')
    body += ('exact hb', 'exact ' + inner + '_right_right')
    return spec(
        'prime_field_convolution_coefficient_left_unit',
        _contract(parameters, (
            _at('ub', 'uc', '0', '1', 'unit_coefficient_unit'),
            _lt('i', 'L', 'unit_coefficient_index'), _at('ab', 'ac', 'i', 'a', 'unit_coefficient_A'),
            _lt('a', 'p', 'unit_coefficient_bound'),
            _coefficient('p', *U, *A, 'i', 'r', 'unit_coefficient_actual'),
        ), 'r=a'),
        ('polynomial_diagonal_left_unit_natural_sum', 'prime_field_residue_bounded_value'), body,
        'The actual residue of the unit-left natural sum is its already bounded right-input value. No polynomial equality is hidden among the premises.',
    )


def _equality_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    parameters = ('p', 'ub', 'uc', *A, 'cb', 'cc')
    premises = (_at('ub', 'uc', '0', '1', 'unit_equal_unit'),
                _convolution('p', *U, *A, *C, 'unit_equal_actual'))
    body = _intro(*parameters, 'hu', 'hc')
    body += ('have hA : ' + _coeff('p', *A, 'unit_equal_A'), 'cases hc',
             'cases hc_right', 'exact hc_right_left')
    body += _intro('i', 'r', 'hi', 'hr')
    body += ('have ha : exists a. (' + _at('ab', 'ac', 'i', 'a', 'unit_equal_entry') + ')',)
    body += _call('beta_at_exists', 'ab', 'ac', 'i') + ('cases ha', 'have heq : r=x')
    body += _call('prime_field_convolution_coefficient_left_unit',
                  'p', 'ub', 'uc', *A, 'i', 'x', 'r')
    body += ('exact hu', 'exact hi', 'exact ha_witness')
    body += _call('matrix_rank_bounded_prefix_value', 'ab', 'ac', 'L', 'p', 'i', 'x')
    body += ('exact hA', 'exact hi', 'exact ha_witness')
    body += _call('prime_field_polynomial_convolution_entry', 'p', *U, *A, *C, 'i', 'r')
    body += ('exact hc', 'exact hi', 'exact hr')
    body += _rewrite_all('heq', _at('ab', 'ac', 'i', 'r', 'unit_equal_rewrite'), 'r')
    body += ('exact ha_witness',)
    equal = spec(
        'prime_field_polynomial_convolution_left_unit_equal',
        _contract(parameters, premises, _equal('cb', 'cc', 'ab', 'ac', 'L', 'unit_equal_result')),
        ('beta_at_exists', 'prime_field_convolution_coefficient_left_unit',
         'matrix_rank_bounded_prefix_value', 'prime_field_polynomial_convolution_entry'), body,
        'Every coefficient of an actual length-L product U*A agrees with A when U is a length-one unit, including the vacuous L=0 case.',
    )
    body = _intro(*parameters, 'hu', 'hc')
    body += _call('prime_field_polynomial_equal_implies_equivalent', 'cb', 'cc', 'ab', 'ac', 'L')
    body += _call('prime_field_polynomial_convolution_left_unit_equal', *parameters)
    body += ('exact hu', 'exact hc')
    equivalent = spec(
        'prime_field_polynomial_convolution_left_unit_equivalent',
        _contract(parameters, premises, _equivalent(*C, *A, 'unit_equivalent_result')),
        ('prime_field_polynomial_equal_implies_equivalent',
         'prime_field_polynomial_convolution_left_unit_equal'), body,
        'Actual left multiplication by a length-one unit preserves formal coefficients, not just evaluations or a selected encoding.',
    )
    return equal, equivalent


def _unit_witness(p: str, ab: str, ac: str, L: str, tag: str) -> str:
    return 'exists ub uc cb cc. ' + _and(
        _coeff(p, 'ub', 'uc', '1', tag + '_unit_bound'),
        _at('ub', 'uc', '0', '1', tag + '_unit_value'),
        _convolution(p, 'ub', 'uc', '1', ab, ac, L, 'cb', 'cc', L, tag + '_product'),
        _equivalent('cb', 'cc', L, ab, ac, L, tag + '_equivalent'),
    )


def _exists_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A)
    body = _intro(*parameters, 'hp', 'hA')
    body += ('have hp0 : ~(p=0)', 'intro hz') + _call('prime_nonzero', 'p')
    body += ('exact hp', 'exact hz')
    unit = _and(_coeff('p', 'ub', 'uc', '1', 'unit_exists_bound'),
                _repeat('ub', 'uc', '1', '1', 'unit_exists_repeat'))
    body += ('have hu : exists ub uc. ' + unit,)
    body += _call('prime_field_polynomial_repeat_exists', 'p', '1', '1')
    body += _call('prime_two_le', 'p') + ('exact hp', 'cases hu', 'cases hu_witness',
                                        'cases hu_witness_witness')
    body += ('have hone : ' + _at('x', 'x1', '0', '1', 'unit_exists_value'),)
    body += _call('hu_witness_witness_right', '0') + ('exists 0', 'apply zero_add')
    body += ('have hc : exists cb cc. ('
             + _convolution('p', 'x', 'x1', '1', *A, 'cb', 'cc', 'L', 'unit_exists_chosen') + ')',)
    body += _call('prime_field_polynomial_convolution_at_length_exists', 'p', 'x', 'x1', '1', *A, 'L')
    body += ('exact hp0', 'exact hu_witness_witness_left', 'exact hA',
             r'have hzero : L=0 \/ ~(L=0)')
    body += _call('eq_decidable', 'L', '0') + ('cases hzero', 'left', 'split', 'right',
                                            'exact hzero_left', 'exact hzero_left', 'right', 'split')
    body += _call('succ_ne_zero', '0') + ('split', 'exact hzero_right',
                                         'simp [add_succ_left,zero_add]', 'cases hc', 'cases hc_witness')
    body += ('exists x', 'exists x1', 'exists x2', 'exists x3', 'split',
             'exact hu_witness_witness_left', 'split', 'exact hone', 'split', 'exact hc_witness_witness')
    body += _call('prime_field_polynomial_convolution_left_unit_equivalent',
                  'p', 'x', 'x1', *A, 'x2', 'x3')
    body += ('exact hone', 'exact hc_witness_witness')
    return spec(
        'prime_field_polynomial_convolution_left_unit_exists',
        _contract(parameters, (_prime('p', 'unit_exists_prime'), _coeff('p', *A, 'unit_exists_A')),
                  _unit_witness('p', *A, 'unit_exists_result')),
        ('prime_nonzero', 'prime_field_polynomial_repeat_exists', 'prime_two_le', 'zero_add',
         'prime_field_polynomial_convolution_at_length_exists', 'eq_decidable', 'succ_ne_zero',
         'add_succ_left', 'prime_field_polynomial_convolution_left_unit_equivalent'), body,
        'Construct an actual canonical length-one unit and its actual length-L left product, formally equal to A. The proper length is zero when A is empty.',
    )


def _reflexivity_row(spec: Callable[..., Any]) -> Any:
    parameters = ('p', *A)
    # This is the literal self-instance of the existing working ND0342
    # expansion. Independent tests compare its core AST with that frozen
    # builder; this pure source adds neither a public builder nor an alias.
    result = _and(_coeff('p', *A, 'unit_divides_bound'),
        'exists qb qc Q pb pc P. ' + _and(
            _convolution('p', 'qb', 'qc', 'Q', *A, 'pb', 'pc', 'P', 'unit_divides_product'),
            _equivalent('pb', 'pc', 'P', *A, 'unit_divides_equivalent')))
    body = _intro(*parameters, 'hp', 'hA')
    body += ('have hu : ' + _unit_witness('p', *A, 'unit_divides_witness'),)
    body += _call('prime_field_polynomial_convolution_left_unit_exists', *parameters)
    body += ('exact hp', 'exact hA')
    body += tuple('cases hu' + '_witness' * i for i in range(4))
    inner = 'hu_witness_witness_witness_witness'
    body += _parts(inner, 4)
    body += _call('prime_field_polynomial_right_divides_from_product',
                  'p', *A, *A, 'x', 'x1', '1', 'x2', 'x3', 'L')
    body += ('exact hA', 'exact ' + inner + '_right_right_left',
             'exact ' + inner + '_right_right_right')
    return spec(
        'prime_field_polynomial_right_divides_reflexive',
        _contract(parameters, (_prime('p', 'unit_divides_prime'), _coeff('p', *A, 'unit_divides_A')),
                  result),
        ('prime_field_polynomial_convolution_left_unit_exists',
         'prime_field_polynomial_right_divides_from_product'), body,
        'Every canonical polynomial right-divides itself using a constructed left unit and actual product. Empty and zero prefixes are included, without assuming commutative multiplication.',
    )


def make_prime_field_polynomial_left_unit_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (*_term_rows(spec), _sum_row(spec), _coefficient_row(spec), *_equality_rows(spec),
            _exists_row(spec), _reflexivity_row(spec))


__all__ = ['make_prime_field_polynomial_left_unit_candidate_theorems']
