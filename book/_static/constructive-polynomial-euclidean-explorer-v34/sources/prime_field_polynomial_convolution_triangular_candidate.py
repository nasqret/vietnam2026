"""Actual triangular convolution steps for constructive polynomial division.

These working-only candidates use the inherited highest-degree-first beta
representation.  They compare the actual antidiagonal term tables and their
natural finite sums.  No quotient identity, field law, or degree conclusion is
included in a construction premise.  All imports are existing source helpers;
this module is not registered in any admitted edition.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _add, _and, _call, _intro, _lt, _mod, _mul, _parts,
)
from peano_lab.library.prime_field_polynomial_candidate import _at, _equal
from peano_lab.library.prime_field_polynomial_convolution_candidate import (
    _coefficient, _diagonal, _le, _pad, _sum, _term,
)
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _prefix_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    params = ('ab', 'ac', 'L', 'AB', 'AC', 'K', 'bb', 'bc', 'M', 'N')
    statement = (
        f"forall {' '.join(params)} i j t. "
        f"({_le('N','L','tri_term_old_length')}) -> "
        f"({_le('N','K','tri_term_new_length')}) -> "
        f"({_equal('ab','ac','AB','AC','N','tri_term_equal')}) -> "
        f"({_lt('j','N','tri_term_index')}) -> "
        f"({_term('ab','ac','L','bb','bc','M','i','j','t','tri_term_old')}) -> "
        f"({_term('AB','AC','K','bb','bc','M','i','j','t','tri_term_new')})"
    )
    body = _intro(*params, 'i', 'j', 't', 'hl', 'hk', 'he', 'hj', 'ht')
    body += tuple('cases ht' + '_witness' * i for i in range(3))
    body += _parts('ht_witness_witness_witness', 4)
    body += (f"have hjl : {_lt('j','L','tri_term_inside_old')}",)
    body += _call('lt_of_lt_of_le', 'j', 'N', 'L') + ('exact hj', 'exact hl')
    body += (f"have hjk : {_lt('j','K','tri_term_inside_new')}",)
    body += _call('lt_of_lt_of_le', 'j', 'N', 'K') + ('exact hj', 'exact hk')
    body += (f"have ha : {_at('ab','ac','j','x1','tri_term_source_entry')}",)
    body += _call('polynomial_zero_extended_entry_inside', 'ab', 'ac', 'L', 'j', 'x1')
    body += ('exact hjl', 'exact ht_witness_witness_witness_right_left')
    body += ('exists x', 'exists x1', 'exists x2', 'split',
             'exact ht_witness_witness_witness_left', 'split', 'left', 'split', 'exact hjk')
    body += _call('he', 'j', 'x1') + ('exact hj', 'exact ha', 'split',
             'exact ht_witness_witness_witness_right_right_left',
             'exact ht_witness_witness_witness_right_right_right')
    term = spec(
        'polynomial_diagonal_left_prefix_transport', statement,
        ('lt_of_lt_of_le', 'polynomial_zero_extended_entry_inside'), body,
        'A genuine antidiagonal term below a shared left prefix survives changing its code and its declared input length.',
    )

    body = _intro(*params, 'i', 'db', 'dc', 'hl', 'hk', 'he', 'hd', 'j', 'hj')
    chosen = _and(_at('db','dc','j','t','tri_prefix_chosen_entry'),
                  _term('ab','ac','L','bb','bc','M','i','j','t','tri_prefix_chosen_term'))
    body += (f'have ht : exists t. {chosen}',) + _call('hd', 'j')
    body += ('exact hj', 'cases ht', 'cases ht_witness', 'exists x', 'split', 'exact ht_witness_left')
    body += _call('polynomial_diagonal_left_prefix_transport', *params, 'i', 'j', 'x')
    body += ('exact hl', 'exact hk', 'exact he', 'exact hj', 'exact ht_witness_right')
    diagonal = spec(
        'polynomial_diagonal_prefix_left_transport',
        f"forall {' '.join(params)} i db dc. "
        f"({_le('N','L','tri_prefix_old_length')}) -> "
        f"({_le('N','K','tri_prefix_new_length')}) -> "
        f"({_equal('ab','ac','AB','AC','N','tri_prefix_equal')}) -> "
        f"({_diagonal('ab','ac','L','bb','bc','M','i','db','dc','N','tri_prefix_old')}) -> "
        f"({_diagonal('AB','AC','K','bb','bc','M','i','db','dc','N','tri_prefix_new')})",
        ('polynomial_diagonal_left_prefix_transport',), body,
        'The same actual first-N antidiagonal table remains valid after a left input prefix extension.',
    )

    body = _intro('p', *params, 'i', 'r', 'hl', 'hk', 'he', 'hi', 'hr')
    body += tuple('cases hr' + '_witness' * i for i in range(3))
    body += _parts('hr_witness_witness_witness', 3)
    body += ('exists x', 'exists x1', 'exists x2', 'split') + _intro('j', 'hj')
    chosen = _and(_at('x','x1','j','t','tri_coefficient_chosen_entry'),
                  _term('ab','ac','L','bb','bc','M','i','j','t','tri_coefficient_chosen_term'))
    body += (f'have ht : exists t. {chosen}',) + _call('hr_witness_witness_witness_left', 'j')
    body += ('exact hj', 'cases ht', 'cases ht_witness', 'exists x3', 'split', 'exact ht_witness_left')
    body += _call('polynomial_diagonal_left_prefix_transport', *params, 'i', 'j', 'x3')
    body += ('exact hl', 'exact hk', 'exact he')
    body += _call('lt_of_lt_of_le', 'j', 'S i', 'N') + ('exact hj', 'exact hi', 'exact ht_witness_right')
    body += ('split', 'exact hr_witness_witness_witness_right_left', 'exact hr_witness_witness_witness_right_right')
    coefficient = spec(
        'prime_field_convolution_coefficient_prefix_transport',
        f"forall p {' '.join(params)} i r. "
        f"({_le('N','L','tri_coefficient_old_length')}) -> "
        f"({_le('N','K','tri_coefficient_new_length')}) -> "
        f"({_equal('ab','ac','AB','AC','N','tri_coefficient_equal')}) -> "
        f"({_lt('i','N','tri_coefficient_index')}) -> "
        f"({_coefficient('p','ab','ac','L','bb','bc','M','i','r','tri_coefficient_old')}) -> "
        f"({_coefficient('p','AB','AC','K','bb','bc','M','i','r','tri_coefficient_new')})",
        ('polynomial_diagonal_left_prefix_transport', 'lt_of_lt_of_le'), body,
        'Every coefficient below the shared prefix is unchanged, with its actual diagonal and sum witnesses reused verbatim.',
    )
    invariant = spec(
        'prime_field_convolution_coefficient_append_invariant',
        f"forall p ab ac AB AC bb bc M N i r. "
        f"({_equal('ab','ac','AB','AC','N','tri_append_equal')}) -> "
        f"({_lt('i','N','tri_append_earlier_index')}) -> "
        f"({_coefficient('p','ab','ac','N','bb','bc','M','i','r','tri_append_earlier_old')}) -> "
        f"({_coefficient('p','AB','AC','S N','bb','bc','M','i','r','tri_append_earlier_new')})",
        ('prime_field_convolution_coefficient_prefix_transport', 'le_refl', 'le_succ'),
        _intro('p','ab','ac','AB','AC','bb','bc','M','N','i','r','he','hi','hr')
        + _call('prime_field_convolution_coefficient_prefix_transport',
                'p','ab','ac','N','AB','AC','S N','bb','bc','M','N','i','r')
        + _call('le_refl','N') + _call('le_succ','N','N') + _call('le_refl','N')
        + ('exact he','exact hi','exact hr'),
        'Appending one quotient coefficient cannot alter any already constructed earlier convolution coefficient.',
    )
    return term, diagonal, coefficient, invariant


def _last_term_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('ab','ac','bb','bc','M','N','t','ht')
    body += tuple('cases ht' + '_witness' * i for i in range(3))
    body += _parts('ht_witness_witness_witness', 4)
    left = 'ht_witness_witness_witness_right_left'
    body += ('cases ' + left, 'cases ' + left + '_left', 'exfalso')
    body += _call('lt_not_le','N','N') + ('exact ' + left + '_left_left',) + _call('le_refl','N')
    body += ('cases ' + left + '_right', 'trans x1*x2',
             'exact ht_witness_witness_witness_right_right_right', 'rewrite ' + left + '_right_right')
    body += _call('mul_zero_left','x2')
    zero = spec(
        'polynomial_diagonal_last_term_left_empty',
        f"forall ab ac bb bc M N t. ({_term('ab','ac','N','bb','bc','M','N','N','t','tri_last_old')}) -> t=0",
        ('lt_not_le','le_refl','mul_zero_left'), body,
        'At diagonal index N the absent N-th entry of a length-N left prefix contributes actual zero.',
    )
    body = _intro('ab','ac','bb','bc','d','N','a','b','t','ha','hb','ht')
    body += tuple('cases ht' + '_witness' * i for i in range(3))
    body += _parts('ht_witness_witness_witness', 4)
    body += ('have hk : x=0',) + _call('add_left_cancel','N','x','0')
    body += ('trans N','exact ht_witness_witness_witness_left','simp')
    body += _rewrite_all('hk',_pad('bb','bc','S d','x','x2','tri_last_complement'),'x',
                         'ht_witness_witness_witness_right_right_left')
    body += ('have hleft : x1=a',)
    body += _call('polynomial_zero_extended_entry_functional','ab','ac','S N','N','x1','a')
    body += ('exact ht_witness_witness_witness_right_left','left','split','exists 0','apply zero_add','exact ha')
    body += ('have hright : x2=b',)
    body += _call('polynomial_zero_extended_entry_functional','bb','bc','S d','0','x2','b')
    body += ('exact ht_witness_witness_witness_right_right_left','left','split','exists d','simp','exact hb')
    body += ('trans x1*x2','exact ht_witness_witness_witness_right_right_right','congr','exact hleft','exact hright')
    last = spec(
        'polynomial_diagonal_last_term_left_append',
        f"forall ab ac bb bc d N a b t. ({_at('ab','ac','N','a','tri_last_new_entry')}) -> "
        f"({_at('bb','bc','0','b','tri_last_leading_entry')}) -> "
        f"({_term('ab','ac','S N','bb','bc','S d','N','N','t','tri_last_new')}) -> t=a*b",
        ('add_left_cancel','polynomial_zero_extended_entry_functional','zero_add'), body,
        'The sole new last antidiagonal term is exactly the appended coefficient times the nonempty right prefix head.',
    )
    return zero, last


def _sum_append_row(spec: Callable[..., Any]) -> Any:
    params = ('ab','ac','AB','AC','bb','bc','d','N','a','b','db','dc','eb','ec','u','v')
    old_diagonal = lambda tag: _diagonal('ab','ac','N','bb','bc','S d','N','db','dc','S N',tag)
    new_diagonal = lambda tag: _diagonal('AB','AC','S N','bb','bc','S d','N','eb','ec','S N',tag)
    body = _intro(*params,'he','ha','hb','hd','hu','hetable','hv')
    old_decomposition = _and(_at('db','dc','N','t','tri_sum_old_last'),
                             _sum('db','dc','N','s','tri_sum_old_prefix'),'u=s+t')
    new_decomposition = _and(_at('eb','ec','N','t','tri_sum_new_last'),
                             _sum('eb','ec','N','s','tri_sum_new_prefix'),'v=s+t')
    body += (f'have hold : exists t s. {old_decomposition}',)
    body += _call('beta_sum_succ_decompose','db','dc','N','u') + ('exact hu','cases hold','cases hold_witness')
    body += _parts('hold_witness_witness',3)
    body += (f'have hnew : exists t s. {new_decomposition}',)
    body += _call('beta_sum_succ_decompose','eb','ec','N','v') + ('exact hv','cases hnew','cases hnew_witness')
    body += _parts('hnew_witness_witness',3)
    body += ('have hz : x=0',) + _call('polynomial_diagonal_last_term_left_empty','ab','ac','bb','bc','S d','N','x')
    body += _call('polynomial_diagonal_prefix_entry','ab','ac','N','bb','bc','S d','N','db','dc','S N','N','x')
    body += ('exact hd',) + _call('le_refl','S N') + ('exact hold_witness_witness_left',)
    body += ('have ht : x2=a*b',) + _call('polynomial_diagonal_last_term_left_append','AB','AC','bb','bc','d','N','a','b','x2')
    body += ('exact ha','exact hb')
    body += _call('polynomial_diagonal_prefix_entry','AB','AC','S N','bb','bc','S d','N','eb','ec','S N','N','x2')
    body += ('exact hetable',) + _call('le_refl','S N') + ('exact hnew_witness_witness_left',)
    transported = _diagonal('AB','AC','S N','bb','bc','S d','N','db','dc','N','tri_sum_transported')
    body += (f'have hprefix : {transported}',)
    body += _call('polynomial_diagonal_prefix_left_transport','ab','ac','N','AB','AC','S N','bb','bc','S d','N','N','db','dc')
    body += _call('le_refl','N') + _call('le_succ','N','N') + _call('le_refl','N') + ('exact he',)
    body += _intro('j','hj') + _call('hd','j') + _call('le_succ','S j','N') + ('exact hj',)
    body += (f"have hs : {_sum('eb','ec','N','x1','tri_sum_same_prefix')}",)
    body += _call('beta_sum_transport_prefix','db','dc','eb','ec','N','x1') + ('exact hold_witness_witness_right_left',)
    body += _call('polynomial_diagonal_prefix_functional','AB','AC','S N','bb','bc','S d','N','db','dc','eb','ec','N')
    body += ('exact hprefix',) + _intro('j','hj') + _call('hetable','j') + _call('le_succ','S j','N') + ('exact hj',)
    body += ('have hbase : x1=x3',) + _call('beta_sum_functional','eb','ec','N','x1','x3')
    body += ('exact hs','exact hnew_witness_witness_right_left','have huvalue : u=x1','trans x1+x',
             'exact hold_witness_witness_right_right','rewrite hz','simp',
             'trans x3+x2','exact hnew_witness_witness_right_right','congr','trans x1','symm','exact hbase',
             'symm','exact huvalue','exact ht')
    return spec(
        'polynomial_diagonal_sum_left_append',
        f"forall {' '.join(params)}. "
        f"({_equal('ab','ac','AB','AC','N','tri_sum_equal')}) -> "
        f"({_at('AB','AC','N','a','tri_sum_appended')}) -> "
        f"({_at('bb','bc','0','b','tri_sum_head')}) -> "
        f"({old_diagonal('tri_sum_old_table')}) -> ({_sum('db','dc','S N','u','tri_sum_old_actual')}) -> "
        f"({new_diagonal('tri_sum_new_table')}) -> ({_sum('eb','ec','S N','v','tri_sum_new_actual')}) -> v=u+a*b",
        ('beta_sum_succ_decompose','polynomial_diagonal_last_term_left_empty',
         'polynomial_diagonal_last_term_left_append','polynomial_diagonal_prefix_entry',
         'le_refl','polynomial_diagonal_prefix_left_transport','le_succ',
         'beta_sum_transport_prefix','polynomial_diagonal_prefix_functional','beta_sum_functional'),
        body,
        'Compare two independently coded actual antidiagonal sums: their first N terms agree and their last terms are zero and the new leading product.',
    )


def _coefficient_append_row(spec: Callable[..., Any]) -> Any:
    params = ('p','ab','ac','AB','AC','bb','bc','d','N','a','b','c','t','r')
    body = _intro(*params,'he','ha','hb','hc','hr','hm')
    for hypothesis in ('hc','hr'):
        body += tuple('cases ' + hypothesis + '_witness' * i for i in range(3))
        body += _parts(hypothesis + '_witness_witness_witness',3)
    body += ('have hn : x5=x2+a*b',)
    body += _call('polynomial_diagonal_sum_left_append','ab','ac','AB','AC','bb','bc','d','N','a','b','x','x1','x3','x4','x2','x5')
    body += ('exact he','exact ha','exact hb','exact hc_witness_witness_witness_left',
             'exact hc_witness_witness_witness_right_left','exact hr_witness_witness_witness_left',
             'exact hr_witness_witness_witness_right_left')
    body += ('cases hc_witness_witness_witness_right_right','cases hr_witness_witness_witness_right_right')
    body += _parts('hm',4)
    body += _rewrite_all('hn',_mod('p','x5','r','tri_append_new_sum_rewrite'),'x5',
                         'hr_witness_witness_witness_right_right_right')
    body += ('split','exact hc_witness_witness_witness_right_right_left','split','exact hm_right_right_left',
             'split','exact hr_witness_witness_witness_right_right_left')
    body += _call('mod_eq_trans','p','c+t','x2+a*b','r')
    body += _call('mod_eq_symm','p','x2+a*b','c+t')
    body += _call('mod_eq_add','p','x2','c','a*b','t')
    body += ('exact hc_witness_witness_witness_right_right_right','exact hm_right_right_right',
             'exact hr_witness_witness_witness_right_right_right')
    return spec(
        'prime_field_convolution_coefficient_append',
        f"forall {' '.join(params)}. "
        f"({_equal('ab','ac','AB','AC','N','tri_append_prefix')}) -> "
        f"({_at('AB','AC','N','a','tri_append_actual_entry')}) -> "
        f"({_at('bb','bc','0','b','tri_append_actual_head')}) -> "
        f"({_coefficient('p','ab','ac','N','bb','bc','S d','N','c','tri_append_previous_coefficient')}) -> "
        f"({_coefficient('p','AB','AC','S N','bb','bc','S d','N','r','tri_append_actual_coefficient')}) -> "
        f"({_mul('p','a','b','t','tri_append_actual_product')}) -> ({_add('p','c','t','r','tri_append_result')})",
        ('polynomial_diagonal_sum_left_append','mod_eq_trans','mod_eq_symm','mod_eq_add'), body,
        'Appending a quotient coefficient changes its new convolution position by exactly its actual field product with the divisor head; all sum and residue witnesses are real.',
    )


def make_prime_field_polynomial_convolution_triangular_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (*_prefix_rows(spec), *_last_term_rows(spec),
            _sum_append_row(spec), _coefficient_append_row(spec))


__all__ = ['make_prime_field_polynomial_convolution_triangular_candidate_theorems']
