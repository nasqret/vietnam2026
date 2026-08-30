"""Actual complementary-divisor reindexing and finite support for convolution.

The finite map is constructed by the existing divisor-involution theorem.
Its true pullback relates real summand tables; ordinary signed permutation
invariance proves commutativity. Zero padding is separately proved from the
actual positive divisor bounds, not included as a convolution assumption.
"""

from __future__ import annotations

from typing import Any, Callable

from .dirichlet_convolution_candidate import _entry, _prefix, _convolution, _convolution_table
from .divisor_involution_candidate import _complement, _prefix as _complement_prefix
from .divisor_sum_reindex_candidate import _reindex
from .divisor_sum_table_candidate import _signed_sum, _table, _table_at
from .prime_factorization_permutation_candidate import _permutation
from .prime_valuation_support_candidate import (
    _and, _at, _call, _cases, _dvd, _intro, _le, _lt, _parts, _rewrite,
)
from .signed_finite_support_candidate import _zero_window
from .signed_table_operations_candidate import _mul_code


def _entry_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    p = 'he_left_right_witness_witness_witness'
    swap = _intro('F','G','n','d','q','z','hn','hc','he')+('cases hc','cases hc_left',)
    swap += ('have hq : ~(q=0)','intro hqzero')+_call('factor_nonzero_right','n','d','q')
    swap += ('exact hn','exact hc_left_right','exact hqzero','cases he','cases he_left')
    swap += _cases('he_left_right',3)+_parts(p,4)+('have hr : x=d',)
    swap += _call('mul_left_cancel_nonzero','q','x','d')+('exact hq','trans n','symm','exact '+p+'_left',
             'trans d*q','exact hc_left_right','apply mul_comm')
    swap += _rewrite('hr',_table_at('G','x','x2','complement_input_rewrite'),'x',p+'_right_right_left')
    swap += _call('dirichlet_convolution_entry_from_quotient','G','F','n','d','q','x2','x1','z')
    swap += ('exact hc_left_left','exact hc_left_right','exact '+p+'_right_right_left','exact '+p+'_right_left')
    swap += _call('signed_mul_commutative','x1','x2','z')+('exact '+p+'_right_right_right',)
    swap += ('cases he_right','exfalso','cases he_right_left','apply hq','exact he_right_left_left',
             'apply he_right_left_right','exists d','trans d*q','exact hc_left_right','apply mul_comm',
             'cases hc_right')
    swap += _rewrite('hc_right_right',_entry('F','G','n','q','z','complement_fixed_rewrite'),'q','he')
    swap += ('right','split','exact hc_right_left')
    swap += _call('dirichlet_convolution_entry_omitted_value','F','G','n','d','z')
    swap += ('exact hc_right_left','exact he')

    value = _intro('F','G','n','l','M','d','z','hp','hd','he')+('cases hp',)
    value += (f"have hv : exists v. ({_table_at('M','d','v','prefix_value_lookup')})",)
    value += _call('divisor_signed_table_lookup','l','M','d')+('exact hp_left','exact hd','cases hv','have heq : z=x')
    value += _call('dirichlet_convolution_entry_functional','F','G','n','d','z','x')+('exact he',)
    value += _call('hp_right','d','x')+('exact hd','exact hv_witness')
    value += _rewrite('heq',_table_at('M','d','z','prefix_value_rewrite'),'z')+('exact hv_witness',)
    return (
        spec('dirichlet_convolution_entry_complement',
             f"forall F G n d q z. ~(n=0) -> ({_complement('n','d','q','swap_complement')}) -> "
             f"({_entry('F','G','n','q','z','swap_source')}) -> ({_entry('G','F','n','d','z','swap_target')})",
             ('factor_nonzero_right','mul_left_cancel_nonzero','mul_comm','dirichlet_convolution_entry_from_quotient',
              'signed_mul_commutative','dirichlet_convolution_entry_omitted_value'),swap,
             'Actual divisor complementation swaps the two signed factors, while fixed zero/nondivisor positions remain genuinely zero.'),
        spec('dirichlet_convolution_prefix_value_from_entry',
             f"forall F G n l M d z. ({_prefix('F','G','n','l','M','value_prefix')}) -> ({_le('d','l','value_bound')}) -> "
             f"({_entry('F','G','n','d','z','value_graph')}) -> ({_table_at('M','d','z','value_result')})",
             ('divisor_signed_table_lookup','dirichlet_convolution_entry_functional'),value,
             'Every independently justified summand value is present in the actual prefix, by constructed lookup and functionality.'),
    )


def _reindex_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    reindex = _intro('F','G','n','P','Q','r','s','hn','hP','hQ','hc','d','q','z','hd','hmap','hz')
    reindex += (f"have hdb : {_le('d','n','pullback_index_bound')}",)
    reindex += _call('le_of_succ_le_succ','d','n')+('exact hd',)
    reindex += (f"have hcomp : {_complement('n','d','q','pullback_complement')}",)
    reindex += _call('divisor_complement_prefix_lookup','n','r','s','S n','d','q')+('exact hc','exact hd','exact hmap')
    reindex += (f"have hqb : {_le('q','n','pullback_image_bound')}",)
    reindex += _call('divisor_complement_bounded','n','d','q')+('exact hn','exact hdb','exact hcomp')
    reindex += _call('dirichlet_convolution_prefix_value_from_entry','G','F','n','n','Q','d','z')
    reindex += ('exact hQ','exact hdb')+_call('dirichlet_convolution_entry_complement','F','G','n','d','q','z')
    reindex += ('exact hn','exact hcomp')+_call('dirichlet_convolution_prefix_lookup','F','G','n','n','P','q','z')
    reindex += ('exact hP','exact hqb','exact hz')

    commute = _intro('F','G','n','a','b','ha','hb')
    commute += ('cases ha','cases ha_right','cases ha_right_witness','cases hb','cases hb_right','cases hb_right_witness')
    perm = _and(_complement_prefix('n','r','s','S n','sum_complement'),_permutation('r','s','S n','sum_permutation'))
    commute += (f'have hp : exists r s. ({perm})',)
    commute += _call('positive_divisor_involution_exists','n')+('exact ha_left',)+_cases('hp',2)
    commute += ('cases hp_witness_witness',)+_parts('hp_witness_witness_right',3)
    commute += _call('divisor_signed_sum_permutation_invariant','x','x1','x2','x3','S n','a','b')
    commute += ('exact hp_witness_witness_right_left','exact hp_witness_witness_right_right_left')
    commute += _call('dirichlet_convolution_prefix_complement_reindex','F','G','n','x','x1','x2','x3')
    commute += ('exact ha_left','exact ha_right_witness_left','exact hb_right_witness_left','exact hp_witness_witness_left',
                'exact ha_right_witness_right','exact hb_right_witness_right')

    swap = _intro('N','F','G','n','z','hF','hG','hbound','hz')+('cases hz',)
    swap += (f"have hs : exists a. ({_convolution('G','F','n','a','swap_actual_opposite')})",)
    swap += _call('dirichlet_convolution_sum_exists','N','G','F','n')
    swap += ('exact hG','exact hF','exact hz_left','exact hbound','cases hs','have he : x=z','symm')
    swap += _call('dirichlet_convolution_sum_commutative','F','G','n','z','x')+('exact hz','exact hs_witness')
    swap += _rewrite('he',_convolution('G','F','n','x','swap_result_rewrite'),'x','hs_witness')+('exact hs_witness',)

    tables = _intro('N','F','G','H','h')+_parts('h',4)
    tables += ('split','exact h_right_left','split','exact h_left','split','exact h_right_right_left')
    tables += _intro('n','z','hn','hbound','hz')+_call('dirichlet_convolution_sum_swap','N','F','G','n','z')
    tables += ('exact h_left','exact h_right_left','exact hbound')
    tables += _call('h_right_right_right','n','z')+('exact hn','exact hbound','exact hz')
    return (
        spec('dirichlet_convolution_prefix_complement_reindex',
             f"forall F G n P Q r s. ~(n=0) -> ({_prefix('F','G','n','n','P','pullback_first')}) -> "
             f"({_prefix('G','F','n','n','Q','pullback_second')}) -> ({_complement_prefix('n','r','s','S n','pullback_map')}) -> "
             f"({_reindex('P','Q','r','s','S n','pullback_result')})",
             ('le_of_succ_le_succ','divisor_complement_prefix_lookup','divisor_complement_bounded',
              'dirichlet_convolution_prefix_value_from_entry','dirichlet_convolution_entry_complement',
              'dirichlet_convolution_prefix_lookup'),reindex,
             'The actual complement beta map pulls one constructed convolution-summand prefix into the factor-swapped prefix.'),
        spec('dirichlet_convolution_sum_commutative',
             f"forall F G n a b. ({_convolution('F','G','n','a','commutative_first')}) -> "
             f"({_convolution('G','F','n','b','commutative_second')}) -> a=b",
             ('positive_divisor_involution_exists','divisor_signed_sum_permutation_invariant',
              'dirichlet_convolution_prefix_complement_reindex'),commute,
             'A genuinely constructed finite divisor permutation proves commutativity of actual signed Dirichlet-convolution values.'),
        spec('dirichlet_convolution_sum_swap',
             f"forall N F G n z. ({_table('N','F','swap_left')}) -> ({_table('N','G','swap_right')}) -> "
             f"({_le('n','N','swap_bound')}) -> ({_convolution('F','G','n','z','swap_given')}) -> "
             f"({_convolution('G','F','n','z','swap_result')})",
             ('dirichlet_convolution_sum_exists','dirichlet_convolution_sum_commutative'),swap,
             'Construct the factor-swapped convolution and prove that the original canonical value is its actual sum.'),
        spec('dirichlet_convolution_table_commutative',
             f"forall N F G H. ({_convolution_table('N','F','G','H','table_commutative_source')}) -> "
             f"({_convolution_table('N','G','F','H','table_commutative_result')})",
             ('dirichlet_convolution_sum_swap',),tables,
             'The same genuine output table represents either convolution order on every positive index; its value at zero remains unrestricted.'),
    )


def _support_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    past = _intro('F','G','n','d','z','hn','hnd','he')
    past += _call('dirichlet_convolution_entry_omitted_value','F','G','n','d','z')
    past += ('right','intro hd')+_call('lt_not_le','n','d')+('exact hnd',)
    past += _call('divisor_le_nonzero','d','n')+('exact hn','exact hd','exact he')

    tail = _intro('F','G','n','L','M','hn','hp','i','z','hni','hiL','hz')
    tail += _call('dirichlet_convolution_entry_past_support_zero','F','G','n','i','z')+('exact hn','exact hni')
    tail += _call('dirichlet_convolution_prefix_lookup','F','G','n','L','M','i','z')+('exact hp',)
    tail += _call('le_of_succ_le_succ','i','L')+('exact hiL','exact hz')

    padded = _intro('F','G','n','L','M','z','hn','hbound','hp','hs')+('cases hp',)
    padded += (f"have hshort : exists a. ({_signed_sum('M','S n','a','padded_actual_short')})",)
    padded += _call('arithmetic_signed_sum_exists','L','M','S n')+('exact hp_left','cases hshort','have he : x=z')
    padded += _call('signed_prefix_sum_zero_tail','M','S n','S L','x','z')
    padded += _call('succ_le_succ','n','L')+('exact hbound',)
    padded += _call('dirichlet_convolution_prefix_zero_tail','F','G','n','L','M')+('exact hn','exact hp','exact hshort_witness','exact hs')
    padded += _rewrite('he',_signed_sum('M','S n','x','padded_short_rewrite'),'x','hshort_witness')
    padded += ('split','exact hn','exists M','split')
    padded += _call('dirichlet_convolution_prefix_restrict','F','G','n','L','n','M')
    padded += ('exact hp','exact hbound','exact hshort_witness')

    forward = _signed_sum('M','S L','z','padded_iff_fold')
    backward = _convolution('F','G','n','z','padded_iff_value')
    equivalence = _intro('F','G','n','L','M','z','hn','hbound','hp')+('split','intro hs')
    equivalence += _call('dirichlet_convolution_from_padded_prefix','F','G','n','L','M','z')
    equivalence += ('exact hn','exact hbound','exact hp','exact hs','intro hs','cases hp')
    equivalence += (f"have ht : exists a. ({_signed_sum('M','S L','a','padded_iff_actual')})",)
    equivalence += _call('arithmetic_signed_sum_exists','L','M','S L')+('exact hp_left','cases ht','have he : x=z')
    equivalence += _call('dirichlet_convolution_sum_functional','F','G','n','x','z')
    equivalence += _call('dirichlet_convolution_from_padded_prefix','F','G','n','L','M','x')
    equivalence += ('exact hn','exact hbound','exact hp','exact ht_witness','exact hs')
    equivalence += _rewrite('he',_signed_sum('M','S L','x','padded_iff_rewrite'),'x','ht_witness')+('exact ht_witness',)
    return (
        spec('dirichlet_convolution_entry_past_support_zero',
             f"forall F G n d z. ~(n=0) -> ({_lt('n','d','past_support_index')}) -> "
             f"({_entry('F','G','n','d','z','past_support_entry')}) -> z=0",
             ('dirichlet_convolution_entry_omitted_value','lt_not_le','divisor_le_nonzero'),past,
             'A summand beyond a positive input is zero because a positive-input divisor cannot exceed that input.'),
        spec('dirichlet_convolution_prefix_zero_tail',
             f"forall F G n L M. ~(n=0) -> ({_prefix('F','G','n','L','M','prefix_tail_source')}) -> "
             f"({_zero_window('M','S n','S L','prefix_tail_result')})",
             ('dirichlet_convolution_entry_past_support_zero','dirichlet_convolution_prefix_lookup','le_of_succ_le_succ'),tail,
             'Every actually stored convolution summand after index n is zero, with the inclusive prefix endpoints retained exactly.'),
        spec('dirichlet_convolution_from_padded_prefix',
             f"forall F G n L M z. ~(n=0) -> ({_le('n','L','padded_bound')}) -> ({_prefix('F','G','n','L','M','padded_prefix')}) -> "
             f"({_signed_sum('M','S L','z','padded_sum')}) -> ({_convolution('F','G','n','z','padded_result')})",
             ('arithmetic_signed_sum_exists','signed_prefix_sum_zero_tail','succ_le_succ',
              'dirichlet_convolution_prefix_zero_tail','dirichlet_convolution_prefix_restrict'),padded,
             'An actual longer summand prefix computes the same convolution after its proved zero tail is removed.'),
        spec('dirichlet_convolution_padded_prefix_iff',
             f"forall F G n L M z. ~(n=0) -> ({_le('n','L','padded_iff_bound')}) -> "
             f"({_prefix('F','G','n','L','M','padded_iff_prefix')}) -> "+_and(f'({forward}) -> ({backward})',f'({backward}) -> ({forward})'),
             ('dirichlet_convolution_from_padded_prefix','arithmetic_signed_sum_exists','dirichlet_convolution_sum_functional'),equivalence,
             'The actual padded fold and the original finite convolution are equivalent; the reverse direction constructs its own genuine sum trace.'),
    )


def make_dirichlet_commutativity_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return _entry_rows(spec)+_reindex_rows(spec)+_support_rows(spec)


__all__ = ['make_dirichlet_commutativity_candidate_theorems']
