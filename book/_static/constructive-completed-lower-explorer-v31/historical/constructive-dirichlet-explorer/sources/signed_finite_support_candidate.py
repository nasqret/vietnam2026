"""Actual signed finite sums ignore a proved zero tail.

The zero-window graph states only actual represented entry values. It neither
defines a sum by its desired answer nor equates arbitrary table encodings.
All folding, padding and last-entry conclusions are ordinary HA theorems.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_sum_algebra_candidate import _add_code
from .divisor_sum_table_candidate import _signed_sum, _table, _table_at
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _intro, _le, _lt, _parts, _public, _rewrite,
)


def _zero_window(F: str, k: str, l: str, tag: str) -> str:
    i, z = 'sfs_index_' + tag, 'sfs_value_' + tag
    return (f'forall {i} {z}. ({_le(k,i,tag+"lower")}) -> '
            f'({_lt(i,l,tag+"upper")}) -> ({_table_at(F,i,z,tag+"entry")}) -> {z}=0')


def signed_arithmetic_zero_window_relation(
    F: str, k: str, l: str, *, tag: str, variables: tuple[str, ...],
) -> str:
    """Every actual signed entry on the half-open interval k<=i<l is zero."""
    return _public(_zero_window, (F,k,l), tag=tag, variables=variables)


def _window_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec('signed_zero_window_empty',
             f"forall F k. ({_zero_window('F','k','k','empty_window')})",
             ('lt_not_le',),
             _intro('F','k','i','z','hki','hik','hz')+('exfalso',)
             +_call('lt_not_le','i','k')+('exact hik','exact hki'),
             'A half-open zero window with coinciding endpoints is genuinely empty.'),
        spec('signed_zero_window_restrict',
             f"forall F k l L. ({_le('l','L','restrict_bound')}) -> ({_zero_window('F','k','L','restrict_source')}) -> "
             f"({_zero_window('F','k','l','restrict_result')})",
             ('le_trans',),
             _intro('F','k','l','L','hl','hz','i','z','hki','hil','hi')
             +_call('hz','i','z')+('exact hki',)+_call('le_trans','S i','l','L')
             +('exact hil','exact hl','exact hi'),
             'Restrict the upper endpoint of an actual zero window without changing any represented values.'),
        spec('signed_zero_window_raise_lower',
             f"forall F k K l. ({_le('k','K','raise_bound')}) -> ({_zero_window('F','k','l','raise_source')}) -> "
             f"({_zero_window('F','K','l','raise_result')})",
             ('le_trans',),
             _intro('F','k','K','l','hk','hz','i','z','hKi','hil','hi')
             +_call('hz','i','z')+_call('le_trans','k','K','i')
             +('exact hk','exact hKi','exact hil','exact hi'),
             'Raise the lower endpoint of a zero window, retaining its actual pointwise meaning.'),
    )


def _tail_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('F','k','l')+('induction l',)+_intro('a','b','hkl','hz','ha','hb')
    body += ('have hk : k=0',)+_call('le_zero','k')+('exact hkl',)
    body += _rewrite('hk',_signed_sum('F','k','a','tail_base_rewrite'),'k','ha')
    body += _call('divisor_signed_sum_functional','F','0','a','b')+('exact ha','exact hb')
    body += _intro('a','b','hkl','hz','ha','hb')
    body += (f"have hc : k=S l \\/ ({_lt('k','S l','tail_cases')})",)
    body += _call('le_eq_or_lt','k','S l')+('exact hkl','cases hc')
    body += _rewrite('hc_left',_signed_sum('F','k','a','tail_equal_rewrite'),'k','ha')
    body += _call('divisor_signed_sum_functional','F','S l','a','b')+('exact ha','exact hb')
    body += (f"have hsmall : {_le('k','l','tail_small')}",)
    body += _call('le_of_succ_le_succ','k','l')+('exact hc_right',)
    decomposition = _and(_signed_sum('F','l','u','tail_prefix'),_table_at('F','l','v','tail_entry'),
                         _add_code('u','v','b','tail_add'))
    body += (f'have hd : exists u v. ({decomposition})',)
    body += _call('divisor_signed_sum_successor_decompose','F','l','b')+('exact hb',)
    body += _cases('hd',2)+_parts('hd_witness_witness',3)
    body += ('have hp : a=x',)+_call('IH','a','x')+('exact hsmall',)
    body += _call('signed_zero_window_restrict','F','k','l','S l')
    body += _call('le_succ_self','l')+('exact hz','exact ha','exact hd_witness_witness_left')
    body += ('have hlast : x1=0',)+_call('hz','l','x1')
    body += ('exact hsmall',)+_call('le_refl','S l')+('exact hd_witness_witness_right_left',)
    body += _rewrite('hlast',_add_code('x','x1','b','tail_zero_rewrite'),'x1','hd_witness_witness_right_right')
    body += ('trans x','exact hp','symm')+_call('signed_add_functional','x','0','b','x')
    body += ('exact hd_witness_witness_right_right',)+_call('signed_add_zero_right','x')
    return (
        spec('signed_prefix_sum_zero_tail',
             f"forall F k l a b. ({_le('k','l','tail_order')}) -> ({_zero_window('F','k','l','tail_window')}) -> "
             f"({_signed_sum('F','k','a','tail_short')}) -> ({_signed_sum('F','l','b','tail_long')}) -> a=b",
             ('le_zero','divisor_signed_sum_functional','le_eq_or_lt','le_of_succ_le_succ',
              'divisor_signed_sum_successor_decompose','signed_zero_window_restrict','le_succ_self',
              'le_refl','signed_add_functional','signed_add_zero_right'),body,
             'Ordinary finite induction proves that a genuinely zero tail changes no actual canonical signed prefix sum.'),
    )


def _zero_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    value = _intro('F','l','z','hz','hs')+_cases('hs',6)+_parts('hs'+'_witness'*6,4)
    value += (f"have hzero : {_signed_sum('F','0','0','zero_actual_empty')}",)
    value += _call('divisor_signed_sum_empty_exists','F','x','x1','x2','x3')
    value += ('exact hs_witness_witness_witness_witness_witness_witness_left','symm')
    value += _call('signed_prefix_sum_zero_tail','F','0','l','0','z')
    value += _call('zero_le','l')+('exact hz','exact hzero','exact hs')

    exists = _intro('F','l','hF','hz')+(f"have hs : exists z. ({_signed_sum('F','l','z','zero_construct')})",)
    exists += _call('arithmetic_signed_sum_exists','0','F','l')+('exact hF','cases hs','have hv : x=0')
    exists += _call('signed_prefix_sum_zero_value','F','l','x')+('exact hz','exact hs_witness')
    exists += _rewrite('hv',_signed_sum('F','l','x','zero_result_rewrite'),'x','hs_witness')+('exact hs_witness',)

    decomposition = _and(_signed_sum('F','l','u','last_prefix'),_table_at('F','l','v','last_entry'),
                         _add_code('u','v','z','last_add'))
    last = _intro('F','l','a','z','hz','ha','hs')+(f'have hd : exists u v. ({decomposition})',)
    last += _call('divisor_signed_sum_successor_decompose','F','l','z')+('exact hs',)
    last += _cases('hd',2)+_parts('hd_witness_witness',3)+('have hp : x=0',)
    last += _call('signed_prefix_sum_zero_value','F','l','x')+('exact hz','exact hd_witness_witness_left',)
    last += ('have he : x1=a',)+_call('divisor_signed_table_at_functional','F','l','x1','a')
    last += ('exact hd_witness_witness_right_left','exact ha')
    last += _rewrite('hp',_add_code('x','x1','z','last_prefix_rewrite'),'x','hd_witness_witness_right_right')
    last += _rewrite('he',_add_code('0','x1','z','last_entry_rewrite'),'x1','hd_witness_witness_right_right')
    last += _call('signed_add_functional','0','a','z','a')
    last += ('exact hd_witness_witness_right_right',)+_call('signed_add_zero_left','a')
    return (
        spec('signed_prefix_sum_zero_value',
             f"forall F l z. ({_zero_window('F','0','l','zero_values')}) -> ({_signed_sum('F','l','z','zero_sum')}) -> z=0",
             ('divisor_signed_sum_empty_exists','signed_prefix_sum_zero_tail','zero_le'),value,
             'A genuinely all-zero represented prefix has canonical signed sum zero; the proof retains actual fold witnesses.'),
        spec('signed_prefix_sum_zero_exists',
             f"forall F l. ({_table('0','F','zero_source')}) -> ({_zero_window('F','0','l','zero_window')}) -> "
             f"({_signed_sum('F','l','0','zero_result')})",
             ('arithmetic_signed_sum_exists','signed_prefix_sum_zero_value'),exists,
             'Construct the actual sum of a valid all-zero prefix and prove its value, without postulating a sum oracle.'),
        spec('signed_prefix_sum_last_value',
             f"forall F l a z. ({_zero_window('F','0','l','last_zeros')}) -> ({_table_at('F','l','a','last_value')}) -> "
             f"({_signed_sum('F','S l','z','last_sum')}) -> z=a",
             ('divisor_signed_sum_successor_decompose','signed_prefix_sum_zero_value',
              'divisor_signed_table_at_functional','signed_add_functional','signed_add_zero_left'),last,
             'If a prefix is zero, its next actual sum is precisely the actual last entry, including the l=0 boundary.'),
    )


def _padding_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    short, long = _signed_sum('F','k','z','pad_short'), _signed_sum('F','l','z','pad_long')
    body = _intro('F','k','l','z','hF','hkl','hz')+('split','intro hs',)
    body += (f"have ht : exists a. ({_signed_sum('F','l','a','pad_forward_construct')})",)
    body += _call('arithmetic_signed_sum_exists','0','F','l')+('exact hF','cases ht','have he : x=z','symm')
    body += _call('signed_prefix_sum_zero_tail','F','k','l','z','x')+('exact hkl','exact hz','exact hs','exact ht_witness')
    body += _rewrite('he',_signed_sum('F','l','x','pad_forward_rewrite'),'x','ht_witness')+('exact ht_witness','intro hs')
    body += (f"have ht : exists a. ({_signed_sum('F','k','a','pad_reverse_construct')})",)
    body += _call('arithmetic_signed_sum_exists','0','F','k')+('exact hF','cases ht','have he : x=z')
    body += _call('signed_prefix_sum_zero_tail','F','k','l','x','z')+('exact hkl','exact hz','exact ht_witness','exact hs')
    body += _rewrite('he',_signed_sum('F','k','x','pad_reverse_rewrite'),'x','ht_witness')+('exact ht_witness',)
    return (
        spec('signed_prefix_sum_zero_padding_iff',
             f"forall F k l z. ({_table('0','F','pad_table')}) -> ({_le('k','l','pad_bound')}) -> "
             f"({_zero_window('F','k','l','pad_zero_window')}) -> "+_and(f'({short}) -> ({long})',f'({long}) -> ({short})'),
             ('arithmetic_signed_sum_exists','signed_prefix_sum_zero_tail'),body,
             'Actually construct either fold from the other across a proved zero tail; both implications retain real finite-sum witnesses.'),
    )


def make_signed_finite_support_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return _window_rows(spec)+_tail_rows(spec)+_zero_rows(spec)+_padding_rows(spec)


__all__ = ['signed_arithmetic_zero_window_relation','make_signed_finite_support_candidate_theorems']
