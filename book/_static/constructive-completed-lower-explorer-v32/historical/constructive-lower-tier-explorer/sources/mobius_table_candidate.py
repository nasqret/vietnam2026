"""Actual finite tables of the independently defined positive-input Möbius value.

The table's zero entry is deliberately the canonical zero code.  This is only
a finite-table convention: Mobius(0,z) remains false for every z.  Construction
uses ordinary induction and genuine paired-beta prefix extension, not choice,
an assumed divisor identity, or a unique table-code representation.
"""

from __future__ import annotations

from typing import Any, Callable

from .arithmetic_table_extension_candidate import _extension
from .divisor_sum_table_candidate import _table, _table_at, _table_equal
from .mobius_value_candidate import _mu
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _intro, _le, _lt, _parts, _public, _rewrite,
)


def _mu_table(N: str, M: str, tag: str) -> str:
    i,z='mt_index_'+tag,'mt_value_'+tag
    return _and(
        _table(N,M,tag+'table'), _table_at(M,'0','0',tag+'zero'),
        f'forall {i} {z}. ~({i}=0) -> ({_le(i,N,tag+"domain")}) -> '
        f'({_table_at(M,i,z,tag+"entry")}) -> ({_mu(i,z,tag+"value")})',
    )


def mobius_arithmetic_table_relation(
    N: str, M: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """A real signed table through N, zero convention and true positive μ values."""
    return _public(_mu_table,(N,M),tag=tag,variables=variables)


def _constructor_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'mobius_table_zero_constructor',
            f"forall F. ({_table('0','F','base_table')}) -> ({_table_at('F','0','0','base_zero')}) -> ({_mu_table('0','F','base_result')})",
            ('le_zero',),
            _intro('F','ht','hz')+('split','exact ht','split','exact hz')
            +_intro('i','z','hi','hib','hv')+('exfalso','apply hi')+_call('le_zero','i')+('exact hib',),
            'The zero-length inclusive table has its prescribed zero entry and no positive index; this does not define a Möbius value at zero.',
        ),
        spec(
            'mobius_table_append',
            f"forall N F z. ({_mu_table('N','F','append_old')}) -> ({_mu('S N','z','append_value')}) -> "
            f"exists G. ({_mu_table('S N','G','append_new')}) /\\ ({_table_equal('F','G','S N','append_preserved')})",
            ('arithmetic_signed_table_append','arithmetic_signed_table_equal_entry_transport',
             'zero_le','succ_le_succ','le_eq_or_lt','le_of_succ_le_succ',
             'divisor_signed_table_at_functional','divisor_signed_table_lookup'),
            _intro('N','F','z','hmu','hz')+_parts('hmu',3)
            +(f"have hext : exists G. ({_extension('F','G','S N','z','append_real')})",)
            +_call('arithmetic_signed_table_append','N','F','z')+('exact hmu_left','cases hext')+_parts('hext_witness',3)
            +('exists x','split','split','exact hext_witness_left','split')
            +_call('arithmetic_signed_table_equal_entry_transport','S N','F','x','S N','0','0')
            +('exact hext_witness_left','exact hext_witness_right_left')+_call('zero_le','S N')
            +_call('succ_le_succ','0','N')+_call('zero_le','N')+('exact hmu_right_left',)
            +_intro('i','y','hi','hib','hv')+(f"have hcase : i = S N \\/ ({_lt('i','S N','append_cases')})",)
            +_call('le_eq_or_lt','i','S N')+('exact hib','cases hcase')
            +_rewrite('hcase_left',_table_at('x','i','y','append_last_entry'),'i','hv')
            +(f"have heq : z = y",)+_call('divisor_signed_table_at_functional','x','S N','z','y')
            +('exact hext_witness_right_right','exact hv')
            +_rewrite('heq',_mu('S N','z','append_last_value'),'z','hz')
            +_rewrite('hcase_left',_mu('i','y','append_last_target'),'i')+('exact hz',)
            +(f"have hbound : {_le('i','N','append_old_bound')}",)
            +_call('le_of_succ_le_succ','i','N')+('exact hcase_right',
                f"have hu : exists u. ({_table_at('F','i','u','append_old_lookup')})")
            +_call('divisor_signed_table_lookup','N','F','i')+('exact hmu_left','exact hbound','cases hu','have heq : x1 = y')
            +_call('hext_witness_right_left','i','x1','y')+('exact hcase_right','exact hu_witness','exact hv')
            +_rewrite('heq',_table_at('F','i','x1','append_old_rewrite'),'x1','hu_witness')
            +_call('hmu_right_right','i','y')+('exact hi','exact hbound','exact hu_witness','exact hext_witness_right_left'),
            'An actual value of μ at the next positive index is appended by real beta recoding; every earlier signed value, including the zero convention, is preserved.',
        ),
        spec(
            'mobius_table_exists',
            f"forall N. exists M. ({_mu_table('N','M','exists_result')})",
            ('arithmetic_signed_table_singleton','mobius_table_zero_constructor','mobius_value_exists','mobius_table_append'),
            _intro('N')+('induction N',
                f"have hbase : exists F. ({_table('0','F','exists_base_table')}) /\\ ({_table_at('F','0','0','exists_base_zero')})")
            +_call('arithmetic_signed_table_singleton','0')+('cases hbase','cases hbase_witness','exists x')
            +_call('mobius_table_zero_constructor','x')+('exact hbase_witness_left','exact hbase_witness_right')
            +('cases IH',f"have hz : exists z. ({_mu('S N','z','exists_step_value')})")
            +_call('mobius_value_exists','S N')+('intro hzero','apply PA1','exact hzero','cases hz',
                f"have hnext : exists G. ({_mu_table('S N','G','exists_next')}) /\\ ({_table_equal('x','G','S N','exists_preserve')})")
            +_call('mobius_table_append','N','x','x1')+('exact IH_witness','exact hz_witness','cases hnext','cases hnext_witness','exists x2','exact hnext_witness_left'),
            'Ordinary induction constructs a genuine packed Möbius table for every finite bound, using independently proved positive-input μ totality at each step.',
        ),
    )


def _lookup_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'mobius_table_lookup',
            f"forall N M i. ({_mu_table('N','M','lookup_source')}) -> ~(i=0) -> ({_le('i','N','lookup_bound')}) -> "
            f"exists z. ({_table_at('M','i','z','lookup_entry')}) /\\ ({_mu('i','z','lookup_value')})",
            ('divisor_signed_table_lookup',),
            _intro('N','M','i','hm','hi','hib')+_parts('hm',3)
            +(f"have hz : exists z. ({_table_at('M','i','z','lookup_construct')})",)
            +_call('divisor_signed_table_lookup','N','M','i')+('exact hm_left','exact hib','cases hz','exists x','split','exact hz_witness')
            +_call('hm_right_right','i','x')+('exact hi','exact hib','exact hz_witness'),
            'Every positive index in the finite domain has an actual canonical table entry and an independently defined Möbius value.',
        ),
        spec(
            'mobius_table_entry_iff',
            f"forall N M i z. ({_mu_table('N','M','iff_table')}) -> ~(i=0) -> ({_le('i','N','iff_bound')}) -> "
            f"(({_table_at('M','i','z','iff_entry_forward')}) -> ({_mu('i','z','iff_value_forward')})) /\\ "
            f"(({_mu('i','z','iff_value_reverse')}) -> ({_table_at('M','i','z','iff_entry_reverse')}))",
            ('mobius_table_lookup','mobius_value_functional'),
            _intro('N','M','i','z','hm','hi','hib')+_parts('hm',3)+('split','intro he')
            +_call('hm_right_right','i','z')+('exact hi','exact hib','exact he','intro hz',
                f"have hu : exists u. ({_table_at('M','i','u','iff_actual_entry')}) /\\ ({_mu('i','u','iff_actual_value')})")
            +_call('mobius_table_lookup','N','M','i')+('exact hm','exact hi','exact hib','cases hu','cases hu_witness','have heq : x = z')
            +_call('mobius_value_functional','i','x','z')+('exact hu_witness_right','exact hz')
            +_rewrite('heq',_table_at('M','i','x','iff_rewrite'),'x','hu_witness_left')+('exact hu_witness_left',),
            'At a positive in-domain index, the actual table lookup is equivalent to the independently specified μ graph, by constructed lookup and literal value uniqueness.',
        ),
        spec(
            'mobius_table_one_entry',
            f"forall N M. ({_mu_table('N','M','unit_table')}) -> ({_le('1','N','unit_bound')}) -> ({_table_at('M','1','2','unit_entry')})",
            ('mobius_table_entry_iff','mobius_one'),
            _intro('N','M','hm','hN')
            +(f"have hiff : (({_table_at('M','1','2','unit_iff_entry')}) -> ({_mu('1','2','unit_iff_value')})) /\\ "
              f"(({_mu('1','2','unit_iff_value_reverse')}) -> ({_table_at('M','1','2','unit_iff_entry_reverse')}))",)
            +_call('mobius_table_entry_iff','N','M','1','2')+('exact hm','intro hzero','apply PA1','exact hzero','exact hN','cases hiff','apply hiff_right','exact mobius_one'),
            'Whenever index one lies in the table, it contains canonical +1 (code two), while the unrelated zero-index convention stays separate.',
        ),
    )


def _extensional_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'mobius_table_extensional',
            f"forall N F G. ({_mu_table('N','F','unique_first')}) -> ({_mu_table('N','G','unique_second')}) -> ({_table_equal('F','G','S N','unique_values')})",
            ('le_of_succ_le_succ','eq_decidable','divisor_signed_table_at_functional','mobius_value_functional'),
            _intro('N','F','G','hf','hg')+_parts('hf',3)+_parts('hg',3)+_intro('i','a','b','hi','ha','hb')
            +(f"have hib : {_le('i','N','unique_domain')}",)+_call('le_of_succ_le_succ','i','N')+('exact hi','have hcase : i=0 \\/ ~(i=0)')
            +_call('eq_decidable','i','0')+('cases hcase',)
            +_rewrite('hcase_left',_table_at('F','i','a','unique_zero_first'),'i','ha')
            +_rewrite('hcase_left',_table_at('G','i','b','unique_zero_second'),'i','hb')
            +('trans 0',)+_call('divisor_signed_table_at_functional','F','0','a','0')+('exact ha','exact hf_right_left','symm')
            +_call('divisor_signed_table_at_functional','G','0','b','0')+('exact hb','exact hg_right_left')
            +_call('mobius_value_functional','i','a','b')+_call('hf_right_right','i','a')
            +('exact hcase_right','exact hib','exact ha')+_call('hg_right_right','i','b')+('exact hcase_right','exact hib','exact hb'),
            'All valid Möbius tables have the same signed values through N; their packed codes and arbitrary component representatives need not coincide.',
        ),
        spec(
            'mobius_table_restrict',
            f"forall N K M. ({_mu_table('N','M','restrict_source')}) -> ({_le('K','N','restrict_bound')}) -> ({_mu_table('K','M','restrict_target')})",
            ('divisor_signed_table_restrict','le_trans'),
            _intro('N','K','M','hm','hKN')+_parts('hm',3)+('split',)
            +_call('divisor_signed_table_restrict','N','K','M')+('exact hm_left','exact hKN','split','exact hm_right_left')
            +_intro('i','z','hi','hiK','hz')+_call('hm_right_right','i','z')+('exact hi',)
            +_call('le_trans','i','K','N')+('exact hiK','exact hKN','exact hz'),
            'A larger actual Möbius table restricts to every smaller finite bound without changing its zero convention or any positive value.',
        ),
    )


def make_mobius_table_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _constructor_rows(spec)+_lookup_rows(spec)+_extensional_rows(spec)


__all__ = ['mobius_arithmetic_table_relation','make_mobius_table_candidate_theorems']
