"""Scratch ordinary-HA bridges for actual affine and row-major signed sums.

All sum, table and slice relations are the unchanged existing beta graphs.
No sum identity is placed in a definition. These conditional bodies are not
an admission or a dependency-closed certificate.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.divisor_sum_algebra_candidate import _add_code
from peano_lab.library.divisor_sum_table_candidate import _signed_sum, _table, _table_at
from peano_lab.library.prime_valuation_support_candidate import (
    _and, _call, _cases, _intro, _parts, _rewrite,
)
from peano_lab.library.signed_rectangular_slice_candidate import _index, _slice, _slice_sum
from peano_lab.library.signed_rectangular_sums_candidate import _rect_sum, _row_sums


def _iff(first: str, second: str) -> str:
    return _and(f'({first}) -> ({second})', f'({second}) -> ({first})')


def _identity_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    identity = _intro('F', 'l', 'hF') + ('split', 'exact hF', 'split')
    identity += _call('signed_table_domain_resize', '0', 'l', 'F') + ('exact hF',)
    identity += _intro('i', 'hi') + (f"have hz : exists z. ({_table_at('F','i','z','identity_value')})",)
    identity += _call('signed_table_lookup_any', '0', 'F', 'i') + ('exact hF', 'cases hz', 'exists x', 'split')
    identity += (f"have hindex : {_index('0','1','i')} = i", 'trans 1*i')
    identity += _call('zero_add', '1*i') + _call('one_mul', 'i')
    identity += _rewrite('hindex', _table_at('F','coord','x','identity_rewrite'), 'coord')
    identity += ('exact hz_witness', 'exact hz_witness')

    iff = _intro('F','l','z','hF') + (f"have hself : {_slice('F','F','0','1','l','unit_self')}",)
    iff += _call('signed_slice_identity', 'F','l') + ('exact hF', 'split', 'intro hs', 'cases hs', 'cases hs_witness')
    iff += (f"have ht : exists w. ({_signed_sum('F','l','w','unit_actual_sum')})",)
    iff += _call('arithmetic_signed_sum_exists','0','F','l') + ('exact hF','cases ht','have heq : x1=z','symm')
    iff += _call('divisor_signed_sum_extensional','x','F','l','z','x1')
    iff += _call('signed_rectangular_slice_extensional_unique','F','x','F','0','1','l')
    iff += ('exact hs_witness_left','exact hself','exact hs_witness_right','exact ht_witness')
    iff += _rewrite('heq',_signed_sum('F','l','x1','unit_rewrite'),'x1','ht_witness')
    iff += ('exact ht_witness','intro hs','exists F','split','exact hself','exact hs')
    return (
        spec('signed_slice_identity',
             f"forall F l. ({_table('0','F','identity_source')}) -> ({_slice('F','F','0','1','l','identity_result')})",
             ('signed_table_domain_resize','signed_table_lookup_any','zero_add','one_mul'), identity,
             'The original packed table itself is a genuine zero-origin, unit-stride slice; the certified endpoint is unused.'),
        spec('signed_slice_sum_unit_prefix_iff',
             f"forall F l z. ({_table('0','F','unit_source')}) -> "
             + _iff(_slice_sum('F','0','1','l','z','unit_slice'), _signed_sum('F','l','z','unit_prefix')),
             ('signed_slice_identity','arithmetic_signed_sum_exists','divisor_signed_sum_extensional',
              'signed_rectangular_slice_extensional_unique'), iff,
             'An actual zero-origin, unit-stride slice sum is exactly the existing actual signed prefix sum, independently of slice encoding.'),
    )


def _concatenation_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    shifted = _index('o','s','p')
    body = ('induction q',) + _intro('F','o','s','p','a','b','c','ha','hb','hadd')
    body += ('have hb0 : b=0',) + _call('signed_rectangular_slice_sum_empty_value','F',shifted,'s','b') + ('exact hb',)
    body += _rewrite('hb0',_add_code('a','b','c','concat_base_add'),'b','hadd')
    body += ('have hca : c=a',) + _call('signed_add_functional','a','0','c','a')
    body += ('exact hadd',) + _call('signed_add_zero_right','a')
    body += _rewrite('hca',_slice_sum('F','o','s','p+0','c','concat_base_value'),'c')
    body += ('have hlength : p+0=p','simp')
    body += _rewrite('hlength',_slice_sum('F','o','s','length','a','concat_base_length'),'length') + ('exact ha',)
    body += _intro('F','o','s','p','a','b','c','ha','hb','hadd')
    inner = _and(_slice_sum('F',shifted,'s','q','u','concat_tail_prefix'),
                 _table_at('F',_index(shifted,'s','q'),'v','concat_tail_last'),
                 _add_code('u','v','b','concat_tail_add'))
    body += (f'have hd : exists u v. ({inner})',)
    body += _call('signed_rectangular_slice_sum_successor_decompose','F',shifted,'s','q','b')
    body += ('exact hb',) + _cases('hd',2) + _parts('hd_witness_witness',3)
    body += (f"have ht : exists t. ({_add_code('a','x','t','concat_intermediate')})",)
    body += _call('signed_add_total','a','x') + ('cases ht',)
    body += (f"have hp : {_slice_sum('F','o','s','p+q','x2','concat_prefix')}",)
    body += _call('IH','F','o','s','p','a','x','x2')
    body += ('exact ha','exact hd_witness_witness_left','exact ht_witness')
    body += (f"have hnext : {_add_code('x2','x1','c','concat_next_add')}",)
    body += _call('signed_table_add_reassociate','a','x','x1','x2','b','c')
    body += ('exact ht_witness','exact hd_witness_witness_right_right','exact hadd')
    body += (f"have hindex : {_index(shifted,'s','q')} = {_index('o','s','p+q')}",
             'trans o+(s*p+s*q)')
    body += _call('add_assoc','o','s*p','s*q') + ('congr','refl','symm') + _call('mul_add','s','p','q')
    body += _rewrite('hindex',_table_at('F','coord','x1','concat_coordinate'),'coord','hd_witness_witness_right_left')
    body += ('have hlength : p+S q=S(p+q)','simp')
    body += _rewrite('hlength',_slice_sum('F','o','s','length','c','concat_next_length'),'length')
    body += _call('signed_rectangular_slice_sum_successor_intro','F','o','s','p+q','x2','x1','c')
    body += ('exact hp','exact hd_witness_witness_right_left','exact hnext')

    values = _intro('F','o','s','p','q','a','b','c','ha','hb','hc')
    values += (f"have ht : exists t. ({_add_code('a','b','t','concat_values_add')})",)
    values += _call('signed_add_total','a','b') + ('cases ht','have heq : x=c')
    values += _call('signed_rectangular_slice_sum_functional','F','o','s','p+q','x','c')
    values += _call('signed_slice_sum_concatenate','q','F','o','s','p','a','b','x')
    values += ('exact ha','exact hb','exact ht_witness','exact hc')
    values += _rewrite('heq',_add_code('a','b','x','concat_values_rewrite'),'x','ht_witness') + ('exact ht_witness',)
    return (
        spec('signed_slice_sum_concatenate',
             f"forall q F o s p a b c. ({_slice_sum('F','o','s','p','a','concat_first')}) -> "
             f"({_slice_sum('F',shifted,'s','q','b','concat_second')}) -> ({_add_code('a','b','c','concat_add')}) -> "
             f"({_slice_sum('F','o','s','p+q','c','concat_result')})",
             ('signed_rectangular_slice_sum_empty_value','signed_add_functional','signed_add_zero_right',
              'signed_rectangular_slice_sum_successor_decompose','signed_add_total','signed_table_add_reassociate',
              'add_assoc','mul_add','signed_rectangular_slice_sum_successor_intro'), body,
             'Ordinary length induction concatenates actual affine sum traces at offset o+s*p, including zero length and zero stride.'),
        spec('signed_slice_sum_concatenate_values',
             f"forall F o s p q a b c. ({_slice_sum('F','o','s','p','a','concat_value_first')}) -> "
             f"({_slice_sum('F',shifted,'s','q','b','concat_value_second')}) -> "
             f"({_slice_sum('F','o','s','p+q','c','concat_value_total')}) -> ({_add_code('a','b','c','concat_value_result')})",
             ('signed_add_total','signed_rectangular_slice_sum_functional','signed_slice_sum_concatenate'), values,
             'The two actual consecutive affine sums add to the actual combined sum, without assuming the addition law as a premise.'),
    )


def _flatten_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    flatten = ('induction m',) + _intro('F','R','n','z','hr','hs')
    flatten += _parts('hr',3) + ('have hz : z=0',) + _call('divisor_signed_sum_empty_value','R','z') + ('exact hs',)
    flatten += _rewrite('hz',_slice_sum('F','0','1','0*n','z','flatten_base_value'),'z')
    flatten += ('have hlength : 0*n=0',) + _call('mul_zero_left','n')
    flatten += _rewrite('hlength',_slice_sum('F','0','1','length','0','flatten_base_length'),'length')
    flatten += _call('signed_rectangular_slice_sum_empty_exists','F','0','1') + ('exact hr_left',)
    flatten += _intro('F','R','n','z','hr','hs')
    dec = _and(_signed_sum('R','m','a','flatten_prefix_sum'),_table_at('R','m','b','flatten_last_row'),
               _add_code('a','b','z','flatten_addition'))
    flatten += (f'have hd : exists a b. ({dec})',) + _call('divisor_signed_sum_successor_decompose','R','m','z')
    flatten += ('exact hs',) + _cases('hd',2) + _parts('hd_witness_witness',3)
    flatten += (f"have hp : {_slice_sum('F','0','1','m*n','x','flatten_prefix')}",)
    flatten += _call('IH','F','R','n','x') + _call('signed_rectangular_row_sums_restrict_outer','F','R','0','n','1','m','n')
    flatten += ('exact hr','exact hd_witness_witness_left')
    flatten += (f"have hl : {_slice_sum('F',_index('0','n','m'),'1','n','x1','flatten_last')}",)
    flatten += _call('signed_rectangular_row_sums_lookup','F','R','0','n','1','S m','n','m','x1')
    flatten += ('exact hr',) + _call('le_refl','S m') + ('exact hd_witness_witness_right_left',)
    flatten += (f"have hindex : {_index('0','n','m')} = {_index('0','1','m*n')}", 'trans n*m')
    flatten += _call('zero_add','n*m') + ('trans m*n',) + _call('mul_comm','n','m')
    flatten += ('symm','trans 1*(m*n)') + _call('zero_add','1*(m*n)') + _call('one_mul','m*n')
    flatten += _rewrite('hindex',_slice_sum('F','offset','1','n','x1','flatten_offset'),'offset','hl')
    flatten += ('have hlength : (S m)*n=m*n+n',) + _call('mul_succ_left','m','n')
    flatten += _rewrite('hlength',_slice_sum('F','0','1','length','z','flatten_length'),'length')
    flatten += _call('signed_slice_sum_concatenate','n','F','0','1','m*n','x','x1','z')
    flatten += ('exact hp','exact hl','exact hd_witness_witness_right_right')

    iff = _intro('F','m','n','z','hF')
    unit = _iff(_slice_sum('F','0','1','m*n','z','flat_unit_slice'), _signed_sum('F','m*n','z','flat_unit_prefix'))
    iff += (f'have hi : {unit}',) + _call('signed_slice_sum_unit_prefix_iff','F','m*n','z') + ('exact hF','cases hi','split','intro hs')
    iff += (f"have hr : exists R. ({_row_sums('F','R','0','n','1','m','n','flat_construct_rows')})",)
    iff += _call('signed_rectangular_row_sums_exists','m','F','0','n','1','n') + ('exact hF','cases hr',)
    iff += (f"have hv : exists v. ({_signed_sum('x','m','v','flat_construct_sum')})",)
    iff += _call('arithmetic_signed_sum_exists','m','x','m') + _parts('hr_witness',3) + ('exact hr_witness_right_left','cases hv',)
    iff += (f"have hflat : {_slice_sum('F','0','1','m*n','x1','flat_construct_flat')}",)
    iff += _call('signed_row_sums_flatten','m','F','x','n','x1') + ('exact hr_witness','exact hv_witness','have heq : x1=z')
    iff += _call('signed_rectangular_slice_sum_functional','F','0','1','m*n','x1','z')
    iff += ('exact hflat','apply hi_right','exact hs')
    iff += _rewrite('heq',_signed_sum('x','m','x1','flat_rewrite_sum'),'x1','hv_witness')
    iff += ('exists x','split','exact hr_witness','exact hv_witness','intro hr','cases hr','cases hr_witness','apply hi_left')
    iff += _call('signed_row_sums_flatten','m','F','x','n','z') + ('exact hr_witness_left','exact hr_witness_right')

    exists = _intro('F','m','n','hF') + (f"have hr : exists z. ({_rect_sum('F','0','n','1','m','n','z','flat_exists_rectangle')})",)
    exists += _call('signed_rectangular_sum_exists','F','0','n','1','m','n') + ('exact hF','cases hr','exists x','split')
    target = _iff(_signed_sum('F','m*n','x','flat_exists_prefix'), _rect_sum('F','0','n','1','m','n','x','flat_exists_rect'))
    exists += (f'have hi : {target}',) + _call('signed_prefix_sum_row_major_iff','F','m','n','x')
    exists += ('exact hF','cases hi','apply hi_right','exact hr_witness','exact hr_witness')
    return (
        spec('signed_row_sums_flatten',
             f"forall m F R n z. ({_row_sums('F','R','0','n','1','m','n','flatten_rows')}) -> "
             f"({_signed_sum('R','m','z','flatten_sum')}) -> ({_slice_sum('F','0','1','m*n','z','flatten_result')})",
             ('divisor_signed_sum_empty_value','mul_zero_left','signed_rectangular_slice_sum_empty_exists',
              'divisor_signed_sum_successor_decompose','signed_rectangular_row_sums_restrict_outer',
              'signed_rectangular_row_sums_lookup','le_refl','zero_add','mul_comm','one_mul','mul_succ_left',
              'signed_slice_sum_concatenate'), flatten,
             'Actual row sums concatenate into the genuine flattened source sum by row-count induction, including either zero dimension.'),
        spec('signed_prefix_sum_row_major_iff',
             f"forall F m n z. ({_table('0','F','flat_source')}) -> "
             + _iff(_signed_sum('F','m*n','z','flat_prefix'), _rect_sum('F','0','n','1','m','n','z','flat_rectangle')),
             ('signed_slice_sum_unit_prefix_iff','signed_rectangular_row_sums_exists','arithmetic_signed_sum_exists',
              'signed_row_sums_flatten','signed_rectangular_slice_sum_functional'), iff,
             'The actual flattened signed prefix and actual row-major rectangle are equivalent, not merely two transposed rectangular folds.'),
        spec('signed_prefix_sum_row_major_exists',
             f"forall F m n. ({_table('0','F','flat_exists_source')}) -> exists z. "
             + _and(_signed_sum('F','m*n','z','flat_exists_prefix'),_rect_sum('F','0','n','1','m','n','z','flat_exists_rectangle')),
             ('signed_rectangular_sum_exists','signed_prefix_sum_row_major_iff'), exists,
             'Construct an actual signed value shared by the flattened prefix and its row-major rectangular fold, with no supplied trace or row table.'),
    )


def make_signed_block_sum_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return _identity_rows(spec) + _concatenation_rows(spec) + _flatten_rows(spec)


__all__ = ['make_signed_block_sum_candidate_theorems']
