"""Constructive divisor masks and actual signed divisor sums.

Every kept entry has d!=0 and a real quotient n=d*q.  Zero and nondivisors
are masked to canonical zero without reading F(0).  The fold is the existing
signed beta prefix sum over exactly S n entries.  Neither cancellation nor
Möbius inversion occurs in any definition or premise of the construction.
"""

from __future__ import annotations

from typing import Any, Callable

from .arithmetic_table_extension_candidate import _extension
from .divisor_sum_algebra_candidate import _add_code
from .divisor_sum_table_candidate import _signed_sum, _table, _table_at, _table_equal
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _dvd, _intro, _le, _lt, _parts, _public, _rewrite,
)


def _entry(F: str, n: str, d: str, z: str, tag: str) -> str:
    q='dm_quotient_'+tag
    keep=_and(f'~(({d})=0)',f'exists {q}. '+_and(f'({n})=({d})*{q}',_table_at(F,d,z,tag+'input')))
    omit=_and(f'({d})=0 \\/ ~({_dvd(d,n,tag+"nondivisor")})',f'({z})=0')
    return f'({keep}) \\/ ({omit})'


def _mask(F: str, n: str, l: str, M: str, tag: str) -> str:
    d,z='dm_index_'+tag,'dm_value_'+tag
    return _and(_table(l,M,tag+'table'),f'forall {d} {z}. ({_le(d,l,tag+"domain")}) -> '
                f'({_table_at(M,d,z,tag+"lookup")}) -> ({_entry(F,n,d,z,tag+"entry")})')


def _positive_equal(F: str, G: str, N: str, tag: str) -> str:
    d,a,b=('dm_'+role+'_'+tag for role in ('index','first_value','second_value'))
    return (f'forall {d} {a} {b}. ~({d}=0) -> ({_le(d,N,tag+"domain")}) -> '
            f'({_table_at(F,d,a,tag+"first")}) -> ({_table_at(G,d,b,tag+"second")}) -> {a}={b}')


def _divisor_sum(F: str, n: str, z: str, tag: str) -> str:
    M='dm_mask_table_'+tag
    return _and(f'~(({n})=0)',f'exists {M}. '+_and(_mask(F,n,n,M,tag+'mask'),_signed_sum(M,f'S ({n})',z,tag+'fold')))


def divisor_mask_entry_relation(F: str, n: str, d: str, z: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Keep an actual positive divisor's input; use zero otherwise, including d=0."""
    return _public(_entry,(F,n,d,z),tag=tag,variables=variables)


def divisor_mask_prefix_relation(F: str, n: str, l: str, M: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Actual mask for divisibility of n on the inclusive table prefix through l."""
    return _public(_mask,(F,n,l,M),tag=tag,variables=variables)


def positive_arithmetic_table_equality_relation(F: str, G: str, N: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Equality on precisely 0<d<=N; the two input values at zero are unrestricted."""
    return _public(_positive_equal,(F,G,N),tag=tag,variables=variables)


def signed_divisor_sum_relation(F: str, n: str, z: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Positive-input divisor sum computed by a real zero-masked S n-entry fold."""
    return _public(_divisor_sum,(F,n,z),tag=tag,variables=variables)


def _comparison_body(*, same_source: bool) -> tuple[str,...]:
    positive=(_call('divisor_signed_table_at_functional','F','d','a','b')
              +('exact ha_left_right_witness_right','exact hb_left_right_witness_right')
              if same_source else _call('he','d','a','b')
              +('exact ha_left_left','exact hdn','exact ha_left_right_witness_right','exact hb_left_right_witness_right'))
    return (
        'cases ha','cases ha_left','cases ha_left_right','cases ha_left_right_witness',
        'cases hb','cases hb_left','cases hb_left_right','cases hb_left_right_witness',
    )+positive+(
        'cases hb_right','exfalso','cases hb_right_left','apply ha_left_left','exact hb_right_left_left',
        'apply hb_right_left_right','exists x','exact ha_left_right_witness_left',
        'cases ha_right','cases hb','cases hb_left','cases hb_left_right','cases hb_left_right_witness',
        'exfalso','cases ha_right_left','apply hb_left_left','exact ha_right_left_left',
        'apply ha_right_left_right','exists x','exact hb_left_right_witness_left',
        'cases hb_right','trans 0','exact ha_right_right','symm','exact hb_right_right',
    )


def _entry_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'divisor_mask_entry_zero',
            f"forall F n. ({_entry('F','n','0','0','zero_entry')})",
            (),_intro('F','n')+('right','split','left','refl','refl'),
            'Index zero is masked to canonical zero for every input table and n, without inspecting or restricting F(0).',
        ),
        spec(
            'divisor_mask_entry_from_quotient',
            f"forall F n d q z. ~(d=0) -> n=d*q -> ({_table_at('F','d','z','keep_input')}) -> ({_entry('F','n','d','z','keep_result')})",
            (),_intro('F','n','d','q','z','hd','hq','hz')+('left','split','exact hd','exists q','split','exact hq','exact hz'),
            'A real quotient and a positive divisor justify retaining its actual signed input entry.',
        ),
        spec(
            'divisor_mask_entry_from_nondivisor',
            f"forall F n d. ~({_dvd('d','n','omit_guard')}) -> ({_entry('F','n','d','0','omit_result')})",
            (),_intro('F','n','d','hd')+('right','split','right','exact hd','refl'),
            'A proved nondivisor contributes zero independently of every signed input value.',
        ),
        spec(
            'divisor_mask_entry_exists',
            f"forall N F n d. ({_table('N','F','choice_table')}) -> ({_le('d','N','choice_bound')}) -> exists z. ({_entry('F','n','d','z','choice_result')})",
            ('eq_decidable','multiple_decidable_nonzero','divisor_signed_table_lookup',
             'divisor_mask_entry_zero','divisor_mask_entry_from_quotient','divisor_mask_entry_from_nondivisor'),
            _intro('N','F','n','d','ht','hbound')+('have hc : d=0 \\/ ~(d=0)',)+_call('eq_decidable','d','0')
            +('cases hc','exists 0')+_rewrite('hc_left',_entry('F','n','d','0','choice_zero_rewrite'),'d')
            +_call('divisor_mask_entry_zero','F','n')
            +(f"have hdiv : ({_dvd('d','n','choice_yes')}) \\/ ~({_dvd('d','n','choice_no')})",)
            +_call('multiple_decidable_nonzero','d','n')+('exact hc_right','cases hdiv','cases hdiv_left',
                f"have hz : exists z. ({_table_at('F','d','z','choice_actual_input')})")
            +_call('divisor_signed_table_lookup','N','F','d')+('exact ht','exact hbound','cases hz','exists x1')
            +_call('divisor_mask_entry_from_quotient','F','n','d','x','x1')
            +('exact hc_right','exact hdiv_left_witness','exact hz_witness','exists 0')
            +_call('divisor_mask_entry_from_nondivisor','F','n','d')+('exact hdiv_right',),
            'Constructively decide zero and divisibility, then construct the actual retained lookup or zero code; no quotient or choice oracle is assumed.',
        ),
        spec(
            'divisor_mask_entry_functional',
            f"forall F n d a b. ({_entry('F','n','d','a','unique_first')}) -> ({_entry('F','n','d','b','unique_second')}) -> a=b",
            ('divisor_signed_table_at_functional',),
            _intro('F','n','d','a','b','ha','hb')+_comparison_body(same_source=True),
            'The kept and omitted alternatives are constructively exclusive, and actual signed input functionality makes the resulting code unique.',
        ),
        spec(
            'divisor_mask_entry_quotient_input',
            f"forall F n d q z. ~(d=0) -> n=d*q -> ({_entry('F','n','d','z','read_mask')}) -> ({_table_at('F','d','z','read_input')})",
            (),
            _intro('F','n','d','q','z','hd','hq','he')+('cases he','cases he_left','cases he_left_right','cases he_left_right_witness',
                'exact he_left_right_witness_right','cases he_right','exfalso','cases he_right_left',
                'apply hd','exact he_right_left_left','apply he_right_left_right','exists q','exact hq'),
            'At a witnessed positive divisor, a mask value is genuinely the input value, not a value attached to an unspecified quotient.',
        ),
        spec(
            'divisor_mask_entry_omitted_value',
            f"forall F n d z. (d=0 \\/ ~({_dvd('d','n','zero_guard')})) -> ({_entry('F','n','d','z','zero_mask')}) -> z=0",
            (),
            _intro('F','n','d','z','hc','he')+('cases he','cases he_left','cases he_left_right','cases he_left_right_witness',
                'exfalso','cases hc','apply he_left_left','exact hc_left','apply hc_right','exists x','exact he_left_right_witness_left',
                'cases he_right','exact he_right_right'),
            'Every omitted index is exactly canonical zero, including the explicit d=0 branch for arbitrary F(0).',
        ),
    )


def _prefix_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'divisor_mask_prefix_zero_constructor',
            f"forall F n M. ({_table('0','M','base_table')}) -> ({_table_at('M','0','0','base_entry')}) -> ({_mask('F','n','0','M','base_result')})",
            ('le_zero','divisor_signed_table_at_functional'),
            _intro('F','n','M','ht','hz')+('split','exact ht')+_intro('d','z','hd','he')
            +('have hd0 : d=0',)+_call('le_zero','d')+('exact hd',)
            +_rewrite('hd0',_table_at('M','d','z','base_rewrite'),'d','he')
            +('right','split','left','exact hd0')+_call('divisor_signed_table_at_functional','M','0','z','0')
            +('exact he','exact hz'),
            'The genuine singleton zero table is the base mask prefix for any fixed divisibility target.',
        ),
        spec(
            'divisor_mask_prefix_append',
            f"forall F n l M z. ({_mask('F','n','l','M','append_source')}) -> ({_entry('F','n','S l','z','append_last')}) -> "
            f"exists G. ({_mask('F','n','S l','G','append_result')}) /\\ ({_table_equal('M','G','S l','append_equal')})",
            ('arithmetic_signed_table_append','le_eq_or_lt','le_of_succ_le_succ',
             'divisor_signed_table_at_functional','divisor_signed_table_lookup'),
            _intro('F','n','l','M','z','hm','hz')+('cases hm',
                f"have hext : exists G. ({_extension('M','G','S l','z','append_construct')})")
            +_call('arithmetic_signed_table_append','l','M','z')+('exact hm_left','cases hext')+_parts('hext_witness',3)
            +('exists x','split','split','exact hext_witness_left')+_intro('d','u','hd','hu')
            +(f"have hc : d=S l \\/ ({_lt('d','S l','append_cases')})",)+_call('le_eq_or_lt','d','S l')+('exact hd','cases hc')
            +_rewrite('hc_left',_table_at('x','d','u','append_last_lookup'),'d','hu')
            +('have heq : z=u',)+_call('divisor_signed_table_at_functional','x','S l','z','u')
            +('exact hext_witness_right_right','exact hu')
            +_rewrite('heq',_entry('F','n','S l','z','append_last_rewrite'),'z','hz')
            +_rewrite('hc_left',_entry('F','n','d','u','append_target_rewrite'),'d')+('exact hz',)
            +(f"have hbound : {_le('d','l','append_previous_bound')}",)+_call('le_of_succ_le_succ','d','l')+('exact hc_right',
                f"have hv : exists v. ({_table_at('M','d','v','append_previous_lookup')})")
            +_call('divisor_signed_table_lookup','l','M','d')+('exact hm_left','exact hbound','cases hv','have heq : x1=u')
            +_call('hext_witness_right_left','d','x1','u')+('exact hc_right','exact hv_witness','exact hu')
            +_rewrite('heq',_table_at('M','d','x1','append_previous_rewrite'),'x1','hv_witness')
            +_call('hm_right','d','u')+('exact hbound','exact hv_witness','exact hext_witness_right_left'),
            'Append one actually decided divisor-mask value while preserving the whole previous signed prefix.',
        ),
        spec(
            'divisor_mask_prefix_exists',
            f"forall N F n l. ({_table('N','F','exists_input')}) -> ({_le('l','N','exists_bound')}) -> exists M. ({_mask('F','n','l','M','exists_mask')})",
            ('arithmetic_signed_table_singleton','divisor_mask_prefix_zero_constructor','le_trans','le_succ_self',
             'divisor_mask_entry_exists','divisor_mask_prefix_append'),
            _intro('N','F','n','l')+('induction l',)+_intro('ht','hbound')
            +(f"have hzero : exists M. ({_table('0','M','exists_base_table')}) /\\ ({_table_at('M','0','0','exists_base_entry')})",)
            +_call('arithmetic_signed_table_singleton','0')+('cases hzero','cases hzero_witness','exists x')
            +_call('divisor_mask_prefix_zero_constructor','F','n','x')+('exact hzero_witness_left','exact hzero_witness_right')
            +_intro('ht','hbound')+(f"have hlow : {_le('l','N','exists_previous_bound')}",)
            +_call('le_trans','l','S l','N')+_call('le_succ_self','l')+('exact hbound',
                f"have hprev : exists M. ({_mask('F','n','l','M','exists_previous_mask')})")
            +_call('IH')+('exact ht','exact hlow','cases hprev',
                f"have hz : exists z. ({_entry('F','n','S l','z','exists_next_value')})")
            +_call('divisor_mask_entry_exists','N','F','n','S l')+('exact ht','exact hbound','cases hz',
                f"have hnext : exists G. ({_mask('F','n','S l','G','exists_next_mask')}) /\\ ({_table_equal('x','G','S l','exists_previous_values')})")
            +_call('divisor_mask_prefix_append','F','n','l','x','x1')+('exact hprev_witness','exact hz_witness','cases hnext','cases hnext_witness','exists x2','exact hnext_witness_left'),
            'Ordinary prefix induction constructs every finite divisor mask inside the actual source domain, with explicit beta extensions at each step.',
        ),
        spec(
            'divisor_mask_prefix_extensional',
            f"forall F n l M K. ({_mask('F','n','l','M','unique_first_mask')}) -> ({_mask('F','n','l','K','unique_second_mask')}) -> ({_table_equal('M','K','S l','unique_mask_values')})",
            ('le_of_succ_le_succ','divisor_mask_entry_functional'),
            _intro('F','n','l','M','K','hM','hK')+('cases hM','cases hK')+_intro('d','a','b','hd','ha','hb')
            +(f"have hbound : {_le('d','l','unique_mask_bound')}",)+_call('le_of_succ_le_succ','d','l')+('exact hd',)
            +_call('divisor_mask_entry_functional','F','n','d','a','b')+_call('hM_right','d','a')
            +('exact hbound','exact ha')+_call('hK_right','d','b')+('exact hbound','exact hb'),
            'Any two real mask constructions agree on every signed value through l, not necessarily on their beta codes or component representatives.',
        ),
        spec(
            'divisor_mask_prefix_restrict',
            f"forall F n l k M. ({_mask('F','n','l','M','restrict_mask')}) -> ({_le('k','l','restrict_bound')}) -> ({_mask('F','n','k','M','restrict_result')})",
            ('divisor_signed_table_restrict','le_trans'),
            _intro('F','n','l','k','M','hm','hkl')+('cases hm','split')
            +_call('divisor_signed_table_restrict','l','k','M')+('exact hm_left','exact hkl')+_intro('d','z','hd','hz')
            +_call('hm_right','d','z')+_call('le_trans','d','k','l')+('exact hd','exact hkl','exact hz'),
            'The same actual mask code restricts to any smaller inclusive prefix for its fixed divisibility target.',
        ),
        spec(
            'divisor_mask_positive_quotient_entry',
            f"forall F n l M d q z. ({_mask('F','n','l','M','keep_mask')}) -> ({_le('d','l','keep_bound')}) -> ~(d=0) -> n=d*q -> "
            f"({_table_at('F','d','z','keep_source')}) -> ({_table_at('M','d','z','keep_mask_entry')})",
            ('divisor_signed_table_lookup','divisor_mask_entry_functional','divisor_mask_entry_from_quotient'),
            _intro('F','n','l','M','d','q','z','hm','hbound','hd','hq','hz')+('cases hm',
                f"have hu : exists u. ({_table_at('M','d','u','keep_actual_lookup')})")
            +_call('divisor_signed_table_lookup','l','M','d')+('exact hm_left','exact hbound','cases hu','have heq : x=z')
            +_call('divisor_mask_entry_functional','F','n','d','x','z')+_call('hm_right','d','x')+('exact hbound','exact hu_witness')
            +_call('divisor_mask_entry_from_quotient','F','n','d','q','z')+('exact hd','exact hq','exact hz')
            +_rewrite('heq',_table_at('M','d','x','keep_lookup_rewrite'),'x','hu_witness')+('exact hu_witness',),
            'The constructed mask retains precisely the canonical input value at every witnessed positive divisor inside its finite domain.',
        ),
        spec(
            'divisor_mask_omitted_entry',
            f"forall F n l M d. ({_mask('F','n','l','M','omit_mask')}) -> ({_le('d','l','omit_bound')}) -> "
            f"(d=0 \\/ ~({_dvd('d','n','omit_reason')})) -> ({_table_at('M','d','0','omit_mask_entry')})",
            ('divisor_signed_table_lookup','divisor_mask_entry_omitted_value'),
            _intro('F','n','l','M','d','hm','hbound','hc')+('cases hm',
                f"have hu : exists u. ({_table_at('M','d','u','omit_actual_lookup')})")
            +_call('divisor_signed_table_lookup','l','M','d')+('exact hm_left','exact hbound','cases hu','have heq : x=0')
            +_call('divisor_mask_entry_omitted_value','F','n','d','x')+('exact hc',)+_call('hm_right','d','x')+('exact hbound','exact hu_witness')
            +_rewrite('heq',_table_at('M','d','x','omit_lookup_rewrite'),'x','hu_witness')+('exact hu_witness',),
            'Every actual mask explicitly has zero at index zero and at each nondivisor; the source value there is not constrained.',
        ),
    )


def _source_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'divisor_mask_entry_positive_source_extensional',
            f"forall F G n d a b. ({_positive_equal('F','G','n','source_equal')}) -> ({_le('d','n','source_bound')}) -> "
            f"({_entry('F','n','d','a','source_first')}) -> ({_entry('G','n','d','b','source_second')}) -> a=b",
            (),_intro('F','G','n','d','a','b','he','hdn','ha','hb')+_comparison_body(same_source=False),
            'Mask values depend only on positive input values: zero branches ignore F(0), while kept branches supply the positivity and quotient data needed for actual source equality.',
        ),
        spec(
            'divisor_mask_positive_source_extensional',
            f"forall F G n M K. ({_positive_equal('F','G','n','mask_source_equal')}) -> ({_mask('F','n','n','M','mask_source_first')}) -> "
            f"({_mask('G','n','n','K','mask_source_second')}) -> ({_table_equal('M','K','S n','mask_source_result')})",
            ('le_of_succ_le_succ','divisor_mask_entry_positive_source_extensional'),
            _intro('F','G','n','M','K','he','hM','hK')+('cases hM','cases hK')+_intro('d','a','b','hd','ha','hb')
            +(f"have hbound : {_le('d','n','mask_source_bound')}",)+_call('le_of_succ_le_succ','d','n')+('exact hd',)
            +_call('divisor_mask_entry_positive_source_extensional','F','G','n','d','a','b')+('exact he','exact hbound')
            +_call('hM_right','d','a')+('exact hbound','exact ha')+_call('hK_right','d','b')+('exact hbound','exact hb'),
            'Positive-only equality of arbitrary inputs yields full equality of their actual divisor masks, including the forced zero output at index zero.',
        ),
    )


def _sum_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'signed_divisor_sum_exists',
            f"forall N F n. ({_table('N','F','sum_total_input')}) -> ~(n=0) -> ({_le('n','N','sum_total_bound')}) -> exists z. ({_divisor_sum('F','n','z','sum_total_result')})",
            ('divisor_mask_prefix_exists','arithmetic_signed_sum_exists'),
            _intro('N','F','n','ht','hn','hbound')+(f"have hm : exists M. ({_mask('F','n','n','M','sum_total_mask')})",)
            +_call('divisor_mask_prefix_exists','N','F','n','n')+('exact ht','exact hbound','cases hm','cases hm_witness',
                f"have hz : exists z. ({_signed_sum('x','S n','z','sum_total_fold')})")
            +_call('arithmetic_signed_sum_exists','n','x','S n')+('exact hm_witness_left','cases hz','exists x1','split','exact hn',
                'exists x','split','exact hm_witness','exact hz_witness'),
            'For every positive n within the finite source domain, construct a real divisor mask and its S n-entry signed fold.',
        ),
        spec(
            'signed_divisor_sum_functional',
            f"forall F n a b. ({_divisor_sum('F','n','a','sum_unique_first')}) -> ({_divisor_sum('F','n','b','sum_unique_second')}) -> a=b",
            ('divisor_mask_prefix_extensional','divisor_signed_sum_extensional'),
            _intro('F','n','a','b','ha','hb')+('cases ha','cases ha_right','cases ha_right_witness',
                'cases hb','cases hb_right','cases hb_right_witness')
            +_call('divisor_signed_sum_extensional','x','x1','S n','a','b')
            +_call('divisor_mask_prefix_extensional','F','n','n','x','x1')
            +('exact ha_right_witness_left','exact hb_right_witness_left','exact ha_right_witness_right','exact hb_right_witness_right'),
            'The canonical divisor-sum result is literally unique despite different mask codes and positive/negative representatives.',
        ),
        spec(
            'signed_divisor_sum_exists_unique',
            f"forall N F n. ({_table('N','F','sum_unique_input')}) -> ~(n=0) -> ({_le('n','N','sum_unique_bound')}) -> "
            f"exists z. ({_divisor_sum('F','n','z','sum_unique_value')}) /\\ forall w. ({_divisor_sum('F','n','w','sum_unique_other')}) -> w=z",
            ('signed_divisor_sum_exists','signed_divisor_sum_functional'),
            _intro('N','F','n','ht','hn','hbound')+(f"have hz : exists z. ({_divisor_sum('F','n','z','sum_unique_constructed')})",)
            +_call('signed_divisor_sum_exists','N','F','n')+('exact ht','exact hn','exact hbound','cases hz','exists x','split','exact hz_witness')
            +_intro('w','hw')+_call('signed_divisor_sum_functional','F','n','w','x')+('exact hw','exact hz_witness'),
            'Every genuine finite signed arithmetic input has a unique actual divisor sum at every 0<n<=N, with no zero-value restriction or cancellation premise.',
        ),
        spec(
            'signed_divisor_sum_zero_excluded',
            f"forall F z. ({_divisor_sum('F','0','z','sum_zero_excluded')}) -> false",
            (),_intro('F','z','h')+('cases h','apply h_left','refl'),
            'Divisor sums here are explicitly positive-input; the zero target is not assigned a spurious finite divisor sum.',
        ),
        spec(
            'signed_divisor_sum_one',
            f"forall N F a. ({_table('N','F','sum_one_input')}) -> ({_le('1','N','sum_one_bound')}) -> "
            f"({_table_at('F','1','a','sum_one_entry')}) -> ({_divisor_sum('F','1','a','sum_one_result')})",
            ('divisor_mask_prefix_exists','arithmetic_signed_sum_exists','divisor_signed_sum_empty_value',
             'divisor_signed_sum_successor_intro','divisor_mask_omitted_entry','divisor_mask_positive_quotient_entry',
             'zero_le','zero_add','one_mul','signed_add_zero_left'),
            _intro('N','F','a','ht','hbound','ha')+(f"have hm : exists M. ({_mask('F','1','1','M','sum_one_mask')})",)
            +_call('divisor_mask_prefix_exists','N','F','1','1')+('exact ht','exact hbound','cases hm','cases hm_witness',
                f"have hzero : exists z. ({_signed_sum('x','0','z','sum_one_empty')})")
            +_call('arithmetic_signed_sum_exists','1','x','0')+('exact hm_witness_left','cases hzero','have heq : x1=0')
            +_call('divisor_signed_sum_empty_value','x','x1')+('exact hzero_witness',)
            +_rewrite('heq',_signed_sum('x','0','x1','sum_one_empty_rewrite'),'x1','hzero_witness')
            +(f"have hfirst : {_signed_sum('x','1','0','sum_one_first')}",)
            +_call('divisor_signed_sum_successor_intro','x','0','0','0','0')+('exact hzero_witness',)
            +_call('divisor_mask_omitted_entry','F','1','1','x','0')+('exact hm_witness',)+_call('zero_le','1')
            +('left','refl')+_call('signed_add_zero_left','0')
            +('split','intro hnzero','apply PA1','exact hnzero','exists x','split','exact hm_witness')
            +_call('divisor_signed_sum_successor_intro','x','1','0','a','a')+('exact hfirst',)
            +_call('divisor_mask_positive_quotient_entry','F','1','1','x','1','1','a')
            +('exact hm_witness','exists 0','apply zero_add','intro hd0','apply PA1','exact hd0','symm','apply one_mul','exact ha')
            +_call('signed_add_zero_left','a'),
            'At n=1, the real two-entry masked fold is 0+F(1), so its exact value is F(1) regardless of F(0).',
        ),
        spec(
            'signed_divisor_sum_positive_source_extensional',
            f"forall F G n a b. ({_positive_equal('F','G','n','sum_source_equal')}) -> ({_divisor_sum('F','n','a','sum_source_first')}) -> "
            f"({_divisor_sum('G','n','b','sum_source_second')}) -> a=b",
            ('divisor_mask_positive_source_extensional','divisor_signed_sum_extensional'),
            _intro('F','G','n','a','b','he','ha','hb')+('cases ha','cases ha_right','cases ha_right_witness',
                'cases hb','cases hb_right','cases hb_right_witness')
            +_call('divisor_signed_sum_extensional','x','x1','S n','a','b')
            +_call('divisor_mask_positive_source_extensional','F','G','n','x','x1')
            +('exact he','exact ha_right_witness_left','exact hb_right_witness_left','exact ha_right_witness_right','exact hb_right_witness_right'),
            'Actual divisor sums depend only on positive in-domain input values; input entries at zero can be unrelated signed integers.',
        ),
    )


def make_divisor_mask_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _entry_rows(spec)+_prefix_rows(spec)+_source_rows(spec)+_sum_rows(spec)


__all__ = [
    'divisor_mask_entry_relation','divisor_mask_prefix_relation',
    'positive_arithmetic_table_equality_relation','signed_divisor_sum_relation',
    'make_divisor_mask_candidate_theorems',
]
