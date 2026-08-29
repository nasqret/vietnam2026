"""Actual finite signed Dirichlet convolution on positive natural inputs.

Each nonzero summand contains an actual quotient n=d*q, both actual signed
lookups and their signed product.  Zero and nondivisors are masked to zero;
the original S n-entry signed fold supplies the value.  Neither an algebraic
identity nor an inversion conclusion is built into any relation.
"""

from __future__ import annotations

from typing import Any, Callable

from .arithmetic_table_extension_candidate import _extension
from .divisor_mask_candidate import _positive_equal
from .divisor_sum_table_candidate import _signed_sum, _table, _table_at, _table_equal
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _dvd, _intro, _le, _lt, _parts, _public, _rewrite,
)
from .signed_table_operations_candidate import _mul_code


def _entry(F: str, G: str, n: str, d: str, z: str, tag: str) -> str:
    q,a,b=('dc_'+role+'_'+tag for role in ('quotient','left','right'))
    active=_and(f'~(({d})=0)',f'exists {q} {a} {b}. '+_and(
        f'({n})=({d})*{q}',_table_at(F,d,a,tag+'left'),
        _table_at(G,q,b,tag+'right'),_mul_code(a,b,z,tag+'product')))
    omitted=_and(f'({d})=0 \\/ ~({_dvd(d,n,tag+"nondivisor")})',f'({z})=0')
    return f'({active}) \\/ ({omitted})'


def _prefix(F: str, G: str, n: str, l: str, M: str, tag: str) -> str:
    d,z='dc_index_'+tag,'dc_value_'+tag
    return _and(_table(l,M,tag+'table'),f'forall {d} {z}. ({_le(d,l,tag+"domain")}) -> '
                f'({_table_at(M,d,z,tag+"lookup")}) -> ({_entry(F,G,n,d,z,tag+"entry")})')


def _convolution(F: str, G: str, n: str, z: str, tag: str) -> str:
    M='dc_mask_'+tag
    return _and(f'~(({n})=0)',f'exists {M}. '+_and(
        _prefix(F,G,n,n,M,tag+'mask'),_signed_sum(M,f'S ({n})',z,tag+'fold')))


def _convolution_table(N: str, F: str, G: str, H: str, tag: str) -> str:
    n,z='dc_input_'+tag,'dc_output_'+tag
    return _and(_table(N,F,tag+'left'),_table(N,G,tag+'right'),_table(N,H,tag+'table'),
                f'forall {n} {z}. ~({n}=0) -> ({_le(n,N,tag+"domain")}) -> '
                f'({_table_at(H,n,z,tag+"lookup")}) -> ({_convolution(F,G,n,z,tag+"value")})')


def dirichlet_convolution_entry_relation(F: str, G: str, n: str, d: str, z: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_entry,(F,G,n,d,z),tag=tag,variables=variables)


def dirichlet_convolution_prefix_relation(F: str, G: str, n: str, l: str, M: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_prefix,(F,G,n,l,M),tag=tag,variables=variables)


def dirichlet_convolution_sum_relation(F: str, G: str, n: str, z: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_convolution,(F,G,n,z),tag=tag,variables=variables)


def dirichlet_convolution_table_relation(N: str, F: str, G: str, H: str, *, tag: str, variables: tuple[str,...]) -> str:
    return _public(_convolution_table,(N,F,G,H),tag=tag,variables=variables)


def _entry_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    omitted=_intro('F','G','n','d','z','hc','he')+('cases he','cases he_left')
    omitted+=_cases('he_left_right',3)+_parts('he_left_right_witness_witness_witness',4)
    omitted+=('exfalso','cases hc','apply he_left_left','exact hc_left','apply hc_right','exists x',
              'exact he_left_right_witness_witness_witness_left','cases he_right','exact he_right_right')

    read=_intro('F','G','n','d','q','a','b','z','hd','hq','ha','hb','he')+('cases he','cases he_left')
    read+=_cases('he_left_right',3)+_parts('he_left_right_witness_witness_witness',4)
    p='he_left_right_witness_witness_witness'
    read+=('have heqq : x=q',)+_call('mul_left_cancel_nonzero','d','x','q')
    read+=('exact hd','trans n','symm','exact '+p+'_left','exact hq')
    read+=_rewrite('heqq',_table_at('G','x','x2','read_quotient_transport'),'x',p+'_right_right_left')
    read+=('have heqa : x1=a',)+_call('divisor_signed_table_at_functional','F','d','x1','a')
    read+=('exact '+p+'_right_left','exact ha','have heqb : x2=b')
    read+=_call('divisor_signed_table_at_functional','G','q','x2','b')
    read+=('exact '+p+'_right_right_left','exact hb')
    read+=_rewrite('heqa',_mul_code('x1','x2','z','read_left_transport'),'x1',p+'_right_right_right')
    read+=_rewrite('heqb',_mul_code('a','x2','z','read_right_transport'),'x2',p+'_right_right_right')
    read+=('exact '+p+'_right_right_right','cases he_right','exfalso','cases he_right_left',
           'apply hd','exact he_right_left_left','apply he_right_left_right','exists q','exact hq')

    unique=_intro('F','G','n','d','u','v','hu','hv')+('cases hu','cases hu_left')
    unique+=_cases('hu_left_right',3)+_parts('hu_left_right_witness_witness_witness',4)
    p='hu_left_right_witness_witness_witness'
    unique+=_call('signed_mul_functional','x1','x2','u','v')+('exact '+p+'_right_right_right',)
    unique+=_call('dirichlet_convolution_entry_quotient_product','F','G','n','d','x','x1','x2','v')
    unique+=('exact hu_left_left','exact '+p+'_left','exact '+p+'_right_left','exact '+p+'_right_right_left','exact hv',
             'cases hu_right','have hvzero : v=0')
    unique+=_call('dirichlet_convolution_entry_omitted_value','F','G','n','d','v')
    unique+=('exact hu_right_left','exact hv','trans 0','exact hu_right_right','symm','exact hvzero')

    total=_intro('F','G','n','d','hF','hG')+('have hc : d=0 \\/ ~(d=0)',)+_call('eq_decidable','d','0')
    total+=('cases hc','exists 0')+_rewrite('hc_left',_entry('F','G','n','d','0','choice_zero_rewrite'),'d')
    total+=_call('dirichlet_convolution_entry_zero','F','G','n')
    total+=(f"have hdiv : ({_dvd('d','n','choice_yes')}) \\/ ~({_dvd('d','n','choice_no')})",)
    total+=_call('multiple_decidable_nonzero','d','n')+('exact hc_right','cases hdiv','cases hdiv_left',
            f"have ha : exists a. ({_table_at('F','d','a','choice_left')})")
    total+=_call('signed_table_lookup_any','0','F','d')+('exact hF','cases ha',
            f"have hb : exists b. ({_table_at('G','x','b','choice_right')})")
    total+=_call('signed_table_lookup_any','0','G','x')+('exact hG','cases hb',
            f"have hz : exists z. ({_mul_code('x1','x2','z','choice_product')})")
    total+=_call('signed_mul_total','x1','x2')+('cases hz','exists x3')
    total+=_call('dirichlet_convolution_entry_from_quotient','F','G','n','d','x','x1','x2','x3')
    total+=('exact hc_right','exact hdiv_left_witness','exact ha_witness','exact hb_witness','exact hz_witness','exists 0')
    total+=_call('dirichlet_convolution_entry_from_nondivisor','F','G','n','d')+('exact hdiv_right',)
    return (
        spec('dirichlet_convolution_entry_zero',
             f"forall F G n. ({_entry('F','G','n','0','0','zero_result')})",(),
             _intro('F','G','n')+('right','split','left','refl','refl'),
             'The zeroth summand is canonical zero without looking at either input value at zero.'),
        spec('dirichlet_convolution_entry_from_quotient',
             f"forall F G n d q a b z. ~(d=0) -> n=d*q -> ({_table_at('F','d','a','keep_left')}) -> "
             f"({_table_at('G','q','b','keep_right')}) -> ({_mul_code('a','b','z','keep_product')}) -> ({_entry('F','G','n','d','z','keep_result')})",(),
             _intro('F','G','n','d','q','a','b','z','hd','hq','ha','hb','hz')
             +('left','split','exact hd','exists q','exists a','exists b','split','exact hq','split','exact ha','split','exact hb','exact hz'),
             'A positive divisor, actual complementary quotient and actual signed product justify the retained summand.'),
        spec('dirichlet_convolution_entry_from_nondivisor',
             f"forall F G n d. ~({_dvd('d','n','omit_guard')}) -> ({_entry('F','G','n','d','0','omit_result')})",(),
             _intro('F','G','n','d','hd')+('right','split','right','exact hd','refl'),
             'A proved nondivisor contributes zero independently of both input tables.'),
        spec('dirichlet_convolution_entry_omitted_value',
             f"forall F G n d z. (d=0 \\/ ~({_dvd('d','n','omitted_guard')})) -> ({_entry('F','G','n','d','z','omitted_entry')}) -> z=0",(),omitted,
             'Every actual omitted summand is exactly zero, and a supplied product witness cannot override that branch.'),
        spec('dirichlet_convolution_entry_quotient_product',
             f"forall F G n d q a b z. ~(d=0) -> n=d*q -> ({_table_at('F','d','a','read_left')}) -> "
             f"({_table_at('G','q','b','read_right')}) -> ({_entry('F','G','n','d','z','read_entry')}) -> ({_mul_code('a','b','z','read_product')})",
             ('mul_left_cancel_nonzero','divisor_signed_table_at_functional'),read,
             'A retained entry is the product at the specified actual quotient; nonzero multiplication cancellation identifies every quotient witness.'),
        spec('dirichlet_convolution_entry_functional',
             f"forall F G n d u v. ({_entry('F','G','n','d','u','unique_first')}) -> ({_entry('F','G','n','d','v','unique_second')}) -> u=v",
             ('signed_mul_functional','dirichlet_convolution_entry_quotient_product','dirichlet_convolution_entry_omitted_value'),unique,
             'Actual quotient, lookup and signed-product functionality determine one canonical summand, without identifying table codes.'),
        spec('dirichlet_convolution_entry_exists',
             f"forall F G n d. ({_table('0','F','choice_left_table')}) -> ({_table('0','G','choice_right_table')}) -> exists z. ({_entry('F','G','n','d','z','choice_result')})",
             ('eq_decidable','dirichlet_convolution_entry_zero','multiple_decidable_nonzero','signed_table_lookup_any',
              'signed_mul_total','dirichlet_convolution_entry_from_quotient','dirichlet_convolution_entry_from_nondivisor'),total,
             'Decide membership, extract the actual quotient, construct both signed lookups and multiply them; neither choice nor a quotient oracle is assumed.'),
    )


def _prefix_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    base=_intro('F','G','n','M','ht','hz')+('split','exact ht')+_intro('d','z','hd','he')
    base+=('have hd0 : d=0',)+_call('le_zero','d')+('exact hd',)
    base+=_rewrite('hd0',_table_at('M','d','z','base_rewrite'),'d','he')
    base+=('right','split','left','exact hd0')+_call('divisor_signed_table_at_functional','M','0','z','0')
    base+=('exact he','exact hz')

    append=_intro('F','G','n','l','M','z','hm','hz')+('cases hm',
            f"have hext : exists H. ({_extension('M','H','S l','z','append_construct')})")
    append+=_call('arithmetic_signed_table_append','l','M','z')+('exact hm_left','cases hext')+_parts('hext_witness',3)
    append+=('exists x','split','split','exact hext_witness_left')+_intro('d','u','hd','hu')
    append+=(f"have hc : d=S l \\/ ({_lt('d','S l','append_cases')})",)+_call('le_eq_or_lt','d','S l')+('exact hd','cases hc')
    append+=_rewrite('hc_left',_table_at('x','d','u','append_last_lookup'),'d','hu')
    append+=('have heq : z=u',)+_call('divisor_signed_table_at_functional','x','S l','z','u')
    append+=('exact hext_witness_right_right','exact hu')
    append+=_rewrite('heq',_entry('F','G','n','S l','z','append_last_rewrite'),'z','hz')
    append+=_rewrite('hc_left',_entry('F','G','n','d','u','append_target_rewrite'),'d')+('exact hz',)
    append+=(f"have hbound : {_le('d','l','append_previous_bound')}",)+_call('le_of_succ_le_succ','d','l')+('exact hc_right',
             f"have hv : exists v. ({_table_at('M','d','v','append_previous_lookup')})")
    append+=_call('divisor_signed_table_lookup','l','M','d')+('exact hm_left','exact hbound','cases hv','have heq : x1=u')
    append+=_call('hext_witness_right_left','d','x1','u')+('exact hc_right','exact hv_witness','exact hu')
    append+=_rewrite('heq',_table_at('M','d','x1','append_previous_rewrite'),'x1','hv_witness')
    append+=_call('hm_right','d','u')+('exact hbound','exact hv_witness','exact hext_witness_right_left')

    exists=_intro('F','G','n','l')+('induction l',)+_intro('hF','hG')
    exists+=(f"have hzero : exists M. ({_table('0','M','exists_base_table')}) /\\ ({_table_at('M','0','0','exists_base_entry')})",)
    exists+=_call('arithmetic_signed_table_singleton','0')+('cases hzero','cases hzero_witness','exists x')
    exists+=_call('dirichlet_convolution_prefix_zero_constructor','F','G','n','x')+('exact hzero_witness_left','exact hzero_witness_right')
    exists+=_intro('hF','hG')+(f"have hprev : exists M. ({_prefix('F','G','n','l','M','exists_previous')})",)
    exists+=_call('IH')+('exact hF','exact hG','cases hprev',
            f"have hz : exists z. ({_entry('F','G','n','S l','z','exists_next_value')})")
    exists+=_call('dirichlet_convolution_entry_exists','F','G','n','S l')+('exact hF','exact hG','cases hz',
            f"have hnext : exists H. ({_prefix('F','G','n','S l','H','exists_next_prefix')}) /\\ ({_table_equal('x','H','S l','exists_previous_values')})")
    exists+=_call('dirichlet_convolution_prefix_append','F','G','n','l','x','x1')
    exists+=('exact hprev_witness','exact hz_witness','cases hnext','cases hnext_witness','exists x2','exact hnext_witness_left')

    keep=_intro('F','G','n','l','M','d','q','a','b','z','hm','hbound','hd','hq','ha','hb','hz')+('cases hm',
          f"have hu : exists u. ({_table_at('M','d','u','keep_actual_lookup')})")
    keep+=_call('divisor_signed_table_lookup','l','M','d')+('exact hm_left','exact hbound','cases hu','have heq : x=z')
    keep+=_call('dirichlet_convolution_entry_functional','F','G','n','d','x','z')
    keep+=_call('hm_right','d','x')+('exact hbound','exact hu_witness')
    keep+=_call('dirichlet_convolution_entry_from_quotient','F','G','n','d','q','a','b','z')
    keep+=('exact hd','exact hq','exact ha','exact hb','exact hz')
    keep+=_rewrite('heq',_table_at('M','d','x','keep_lookup_rewrite'),'x','hu_witness')+('exact hu_witness',)

    omit=_intro('F','G','n','l','M','d','hm','hbound','hc')+('cases hm',
          f"have hu : exists u. ({_table_at('M','d','u','omit_actual_lookup')})")
    omit+=_call('divisor_signed_table_lookup','l','M','d')+('exact hm_left','exact hbound','cases hu','have heq : x=0')
    omit+=_call('dirichlet_convolution_entry_omitted_value','F','G','n','d','x')+('exact hc',)
    omit+=_call('hm_right','d','x')+('exact hbound','exact hu_witness')
    omit+=_rewrite('heq',_table_at('M','d','x','omit_lookup_rewrite'),'x','hu_witness')+('exact hu_witness',)
    return (
        spec('dirichlet_convolution_prefix_zero_constructor',
             f"forall F G n M. ({_table('0','M','base_table')}) -> ({_table_at('M','0','0','base_entry')}) -> ({_prefix('F','G','n','0','M','base_result')})",
             ('le_zero','divisor_signed_table_at_functional'),base,
             'A real singleton zero table supplies the inclusive zero prefix for every fixed input, independently of F(0) and G(0).'),
        spec('dirichlet_convolution_prefix_append',
             f"forall F G n l M z. ({_prefix('F','G','n','l','M','append_source')}) -> ({_entry('F','G','n','S l','z','append_last')}) -> "
             f"exists H. ({_prefix('F','G','n','S l','H','append_result')}) /\\ ({_table_equal('M','H','S l','append_equal')})",
             ('arithmetic_signed_table_append','le_eq_or_lt','divisor_signed_table_at_functional',
              'le_of_succ_le_succ','divisor_signed_table_lookup'),append,
             'Append one actual product-or-zero entry by paired beta recoding, preserving every earlier canonical signed value.'),
        spec('dirichlet_convolution_prefix_exists',
             f"forall F G n l. ({_table('0','F','exists_left')}) -> ({_table('0','G','exists_right')}) -> exists M. ({_prefix('F','G','n','l','M','exists_result')})",
             ('arithmetic_signed_table_singleton','dirichlet_convolution_prefix_zero_constructor',
              'dirichlet_convolution_entry_exists','dirichlet_convolution_prefix_append'),exists,
             'Ordinary prefix induction constructs every finite summand table; its length is independent of n, and no finite choice principle is assumed.'),
        spec('dirichlet_convolution_prefix_lookup',
             f"forall F G n l M d z. ({_prefix('F','G','n','l','M','lookup_prefix')}) -> ({_le('d','l','lookup_bound')}) -> "
             f"({_table_at('M','d','z','lookup_entry')}) -> ({_entry('F','G','n','d','z','lookup_result')})",(),
             _intro('F','G','n','l','M','d','z','hp','hd','hz')+('cases hp',)+_call('hp_right','d','z')+('exact hd','exact hz'),
             'Every actual decoded entry in the inclusive constructed prefix obeys the independently defined product-or-zero graph.'),
        spec('dirichlet_convolution_prefix_extensional',
             f"forall F G n l M K. ({_prefix('F','G','n','l','M','unique_first')}) -> ({_prefix('F','G','n','l','K','unique_second')}) -> ({_table_equal('M','K','S l','unique_values')})",
             ('le_of_succ_le_succ','dirichlet_convolution_entry_functional'),
             _intro('F','G','n','l','M','K','hM','hK')+('cases hM','cases hK')+_intro('d','a','b','hd','ha','hb')
             +(f"have hbound : {_le('d','l','unique_bound')}",)+_call('le_of_succ_le_succ','d','l')+('exact hd',)
             +_call('dirichlet_convolution_entry_functional','F','G','n','d','a','b')+_call('hM_right','d','a')
             +('exact hbound','exact ha')+_call('hK_right','d','b')+('exact hbound','exact hb'),
             'All genuine summand prefixes agree through their last entry in represented value, without asserting equality of arbitrary table codes.'),
        spec('dirichlet_convolution_prefix_restrict',
             f"forall F G n l k M. ({_prefix('F','G','n','l','M','restrict_source')}) -> ({_le('k','l','restrict_bound')}) -> ({_prefix('F','G','n','k','M','restrict_result')})",
             ('divisor_signed_table_restrict','le_trans'),
             _intro('F','G','n','l','k','M','hm','hkl')+('cases hm','split')
             +_call('divisor_signed_table_restrict','l','k','M')+('exact hm_left','exact hkl')+_intro('d','z','hd','hz')
             +_call('hm_right','d','z')+_call('le_trans','d','k','l')+('exact hd','exact hkl','exact hz'),
             'The same actual summand code restricts to any smaller inclusive window, for its unchanged convolution input n.'),
        spec('dirichlet_convolution_prefix_quotient_entry',
             f"forall F G n l M d q a b z. ({_prefix('F','G','n','l','M','keep_prefix')}) -> ({_le('d','l','keep_bound')}) -> ~(d=0) -> n=d*q -> "
             f"({_table_at('F','d','a','keep_left')}) -> ({_table_at('G','q','b','keep_right')}) -> ({_mul_code('a','b','z','keep_product')}) -> ({_table_at('M','d','z','keep_result')})",
             ('divisor_signed_table_lookup','dirichlet_convolution_entry_functional','dirichlet_convolution_entry_from_quotient'),keep,
             'At every witnessed positive divisor, the actual summand table contains precisely F(d)*G(q), with n=d*q supplied and checked.'),
        spec('dirichlet_convolution_prefix_omitted_entry',
             f"forall F G n l M d. ({_prefix('F','G','n','l','M','omit_prefix')}) -> ({_le('d','l','omit_bound')}) -> "
             f"(d=0 \\/ ~({_dvd('d','n','omit_reason')})) -> ({_table_at('M','d','0','omit_result')})",
             ('divisor_signed_table_lookup','dirichlet_convolution_entry_omitted_value'),omit,
             'The real prefix has zero at every omitted index, including zero, without any corresponding input-value condition.'),
    )


def _sum_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    exists=_intro('N','F','G','n','hF','hG','hn','hbound')
    exists+=(f"have hm : exists M. ({_prefix('F','G','n','n','M','sum_total_prefix')})",)
    exists+=_call('dirichlet_convolution_prefix_exists','F','G','n','n')
    exists+=_call('signed_table_domain_resize','N','0','F')+('exact hF',)
    exists+=_call('signed_table_domain_resize','N','0','G')+('exact hG','cases hm','cases hm_witness',
             f"have hz : exists z. ({_signed_sum('x','S n','z','sum_total_fold')})")
    exists+=_call('arithmetic_signed_sum_exists','n','x','S n')+('exact hm_witness_left','cases hz','exists x1','split','exact hn',
             'exists x','split','exact hm_witness','exact hz_witness')
    functional=_intro('F','G','n','a','b','ha','hb')+('cases ha','cases ha_right','cases ha_right_witness',
                  'cases hb','cases hb_right','cases hb_right_witness')
    functional+=_call('divisor_signed_sum_extensional','x','x1','S n','a','b')
    functional+=_call('dirichlet_convolution_prefix_extensional','F','G','n','n','x','x1')
    functional+=('exact ha_right_witness_left','exact hb_right_witness_left','exact ha_right_witness_right','exact hb_right_witness_right')
    unique=_intro('N','F','G','n','hF','hG','hn','hbound')
    unique+=(f"have hz : exists z. ({_convolution('F','G','n','z','sum_unique_constructed')})",)
    unique+=_call('dirichlet_convolution_sum_exists','N','F','G','n')+('exact hF','exact hG','exact hn','exact hbound',
              'cases hz','exists x','split','exact hz_witness')+_intro('w','hw')
    unique+=_call('dirichlet_convolution_sum_functional','F','G','n','w','x')+('exact hw','exact hz_witness')
    return (
        spec('dirichlet_convolution_sum_exists',
             f"forall N F G n. ({_table('N','F','sum_total_left')}) -> ({_table('N','G','sum_total_right')}) -> ~(n=0) -> ({_le('n','N','sum_total_bound')}) -> exists z. ({_convolution('F','G','n','z','sum_total_result')})",
             ('dirichlet_convolution_prefix_exists','signed_table_domain_resize','arithmetic_signed_sum_exists'),exists,
             'Construct the actual weighted divisor prefix and its S n-entry signed fold at every positive in-domain input.'),
        spec('dirichlet_convolution_sum_functional',
             f"forall F G n a b. ({_convolution('F','G','n','a','sum_unique_first')}) -> ({_convolution('F','G','n','b','sum_unique_second')}) -> a=b",
             ('divisor_signed_sum_extensional','dirichlet_convolution_prefix_extensional'),functional,
             'Different actual weighted prefixes and signed representatives give the same canonical convolution value.'),
        spec('dirichlet_convolution_sum_exists_unique',
             f"forall N F G n. ({_table('N','F','sum_unique_left')}) -> ({_table('N','G','sum_unique_right')}) -> ~(n=0) -> ({_le('n','N','sum_unique_bound')}) -> "
             f"exists z. ({_convolution('F','G','n','z','sum_unique_value')}) /\\ forall w. ({_convolution('F','G','n','w','sum_unique_other')}) -> w=z",
             ('dirichlet_convolution_sum_exists','dirichlet_convolution_sum_functional'),unique,
             'The actual finite Dirichlet convolution has one literally unique signed value at every 0<n<=N; the input zero entries are unrestricted.'),
        spec('dirichlet_convolution_sum_zero_excluded',
             f"forall F G z. ({_convolution('F','G','0','z','sum_zero')}) -> false",(),
             _intro('F','G','z','h')+('cases h','apply h_left','refl'),
             'Zero is outside the convolution-value domain; it is not assigned an artificial finite all-divisors sum.'),
    )


def _positive_source_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    compare=_intro('F','G','H','K','n','d','a','b','hn','hF','hG','hd','ha','hb')+('cases ha','cases ha_left')
    compare+=_cases('ha_left_right',3)+_parts('ha_left_right_witness_witness_witness',4)
    compare+=('cases hb','cases hb_left')+_cases('hb_left_right',3)+_parts('hb_left_right_witness_witness_witness',4)
    a='ha_left_right_witness_witness_witness';b='hb_left_right_witness_witness_witness'
    compare+=('have heqq : x3=x',)+_call('mul_left_cancel_nonzero','d','x3','x')
    compare+=('exact ha_left_left','trans n','symm','exact '+b+'_left','exact '+a+'_left')
    compare+=_rewrite('heqq',_table_at('K','x3','x5','source_quotient_transport'),'x3',b+'_right_right_left')
    compare+=('have hqpositive : ~(x=0)','intro hxzero')+_call('factor_nonzero_right','n','d','x')
    compare+=('exact hn','exact '+a+'_left','exact hxzero',f"have hqbound : {_le('x','n','source_quotient_bound')}")
    compare+=_call('divisor_le_nonzero','x','n')+('exact hn','exists d','trans d*x','exact '+a+'_left','apply mul_comm')
    compare+=('have heqa : x1=x4',)+_call('hF','d','x1','x4')
    compare+=('exact ha_left_left','exact hd','exact '+a+'_right_left','exact '+b+'_right_left','have heqb : x2=x5')
    compare+=_call('hG','x','x2','x5')+('exact hqpositive','exact hqbound','exact '+a+'_right_right_left','exact '+b+'_right_right_left')
    compare+=_rewrite('heqa',_mul_code('x1','x2','a','source_left_product_transport'),'x1',a+'_right_right_right')
    compare+=_rewrite('heqb',_mul_code('x4','x2','a','source_right_product_transport'),'x2',a+'_right_right_right')
    compare+=_call('signed_mul_functional','x4','x5','a','b')+('exact '+a+'_right_right_right','exact '+b+'_right_right_right')
    compare+=('cases hb_right','exfalso','cases hb_right_left','apply ha_left_left','exact hb_right_left_left',
              'apply hb_right_left_right','exists x','exact '+a+'_left','cases ha_right','cases hb','cases hb_left')
    compare+=_cases('hb_left_right',3)+_parts('hb_left_right_witness_witness_witness',4)
    compare+=('exfalso','cases ha_right_left','apply hb_left_left','exact ha_right_left_left',
              'apply ha_right_left_right','exists x','exact '+b+'_left','cases hb_right',
              'trans 0','exact ha_right_right','symm','exact hb_right_right')

    prefixes=_intro('F','G','H','K','n','M','P','hn','hF','hG','hM','hP')+('cases hM','cases hP')
    prefixes+=_intro('d','a','b','hd','ha','hb')+(f"have hbound : {_le('d','n','source_mask_bound')}",)
    prefixes+=_call('le_of_succ_le_succ','d','n')+('exact hd',)
    prefixes+=_call('dirichlet_convolution_entry_positive_source_extensional','F','G','H','K','n','d','a','b')
    prefixes+=('exact hn','exact hF','exact hG','exact hbound')+_call('hM_right','d','a')
    prefixes+=('exact hbound','exact ha')+_call('hP_right','d','b')+('exact hbound','exact hb')

    sums=_intro('F','G','H','K','n','a','b','hF','hG','ha','hb')+('cases ha','cases ha_right','cases ha_right_witness',
          'cases hb','cases hb_right','cases hb_right_witness')
    sums+=_call('divisor_signed_sum_extensional','x','x1','S n','a','b')
    sums+=_call('dirichlet_convolution_prefix_positive_source_extensional','F','G','H','K','n','x','x1')
    sums+=('exact ha_left','exact hF','exact hG','exact ha_right_witness_left','exact hb_right_witness_left',
           'exact ha_right_witness_right','exact hb_right_witness_right')

    transport=_intro('N','F','G','H','K','n','z','hH','hK','hbound','hF','hG','hz')+('cases hz',
              f"have hu : exists u. ({_convolution('H','K','n','u','source_transport_actual')})")
    transport+=_call('dirichlet_convolution_sum_exists','N','H','K','n')
    transport+=('exact hH','exact hK','exact hz_left','exact hbound','cases hu','have heq : z=x')
    transport+=_call('dirichlet_convolution_positive_source_extensional','F','G','H','K','n','z','x')
    transport+=('exact hF','exact hG','exact hz','exact hu_witness')
    transport+=_rewrite('heq',_convolution('H','K','n','z','source_transport_result'),'z')+('exact hu_witness',)
    return (
        spec('dirichlet_convolution_entry_positive_source_extensional',
             f"forall F G H K n d a b. ~(n=0) -> ({_positive_equal('F','H','n','source_equal_left')}) -> "
             f"({_positive_equal('G','K','n','source_equal_right')}) -> ({_le('d','n','source_index_bound')}) -> "
             f"({_entry('F','G','n','d','a','source_entry_first')}) -> ({_entry('H','K','n','d','b','source_entry_second')}) -> a=b",
             ('mul_left_cancel_nonzero','factor_nonzero_right','divisor_le_nonzero','mul_comm','signed_mul_functional'),compare,
             'Only positive in-domain source values matter: a genuine quotient is proved positive and bounded before either source equality is applied.'),
        spec('dirichlet_convolution_prefix_positive_source_extensional',
             f"forall F G H K n M P. ~(n=0) -> ({_positive_equal('F','H','n','prefix_source_left')}) -> ({_positive_equal('G','K','n','prefix_source_right')}) -> "
             f"({_prefix('F','G','n','n','M','prefix_source_first')}) -> ({_prefix('H','K','n','n','P','prefix_source_second')}) -> ({_table_equal('M','P','S n','prefix_source_result')})",
             ('le_of_succ_le_succ','dirichlet_convolution_entry_positive_source_extensional'),prefixes,
             'Positive-source equality gives equality of every actual masked product value, including the forced zero output at index zero.'),
        spec('dirichlet_convolution_positive_source_extensional',
             f"forall F G H K n a b. ({_positive_equal('F','H','n','sum_source_left')}) -> ({_positive_equal('G','K','n','sum_source_right')}) -> "
             f"({_convolution('F','G','n','a','sum_source_first')}) -> ({_convolution('H','K','n','b','sum_source_second')}) -> a=b",
             ('divisor_signed_sum_extensional','dirichlet_convolution_prefix_positive_source_extensional'),sums,
             'Actual convolution values depend only on positive input values through n, permitting all four zeroth input values to be unrelated.'),
        spec('dirichlet_convolution_positive_source_transport',
             f"forall N F G H K n z. ({_table('N','H','transport_left')}) -> ({_table('N','K','transport_right')}) -> ({_le('n','N','transport_bound')}) -> "
             f"({_positive_equal('F','H','n','transport_equal_left')}) -> ({_positive_equal('G','K','n','transport_equal_right')}) -> "
             f"({_convolution('F','G','n','z','transport_source')}) -> ({_convolution('H','K','n','z','transport_result')})",
             ('dirichlet_convolution_sum_exists','dirichlet_convolution_positive_source_extensional'),transport,
             'Construct the comparison fold before transporting an actual convolution value across positive-source equality; zero entries are untouched.'),
    )


def _table_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    base=_intro('F','G','H','hF','hG','hH')+('split','exact hF','split','exact hG','split','exact hH')
    base+=_intro('n','z','hn','hbound','hz')+('exfalso','apply hn')+_call('le_zero','n')+('exact hbound',)

    append=_intro('N','F','G','H','z','hc','hz')+_parts('hc',4)
    append+=(f"have hext : exists K. ({_extension('H','K','S N','z','table_append_construct')})",)
    append+=_call('arithmetic_signed_table_append','N','H','z')+('exact hc_right_right_left','cases hext')+_parts('hext_witness',3)
    append+=('exists x','split','split')+_call('signed_table_domain_resize','N','S N','F')+('exact hc_left','split')
    append+=_call('signed_table_domain_resize','N','S N','G')+('exact hc_right_left','split','exact hext_witness_left')
    append+=_intro('n','u','hn','hbound','hu')+(f"have hcase : n=S N \\/ ({_lt('n','S N','table_append_cases')})",)
    append+=_call('le_eq_or_lt','n','S N')+('exact hbound','cases hcase')
    append+=_rewrite('hcase_left',_table_at('x','n','u','table_append_last_lookup'),'n','hu')
    append+=('have heq : z=u',)+_call('divisor_signed_table_at_functional','x','S N','z','u')
    append+=('exact hext_witness_right_right','exact hu')
    append+=_rewrite('heq',_convolution('F','G','S N','z','table_append_last_value'),'z','hz')
    append+=_rewrite('hcase_left',_convolution('F','G','n','u','table_append_target'),'n')+('exact hz',)
    append+=(f"have hlow : {_le('n','N','table_append_old_bound')}",)+_call('le_of_succ_le_succ','n','N')+('exact hcase_right',
             f"have hv : exists v. ({_table_at('H','n','v','table_append_old_lookup')})")
    append+=_call('divisor_signed_table_lookup','N','H','n')+('exact hc_right_right_left','exact hlow','cases hv','have heq : x1=u')
    append+=_call('hext_witness_right_left','n','x1','u')+('exact hcase_right','exact hv_witness','exact hu')
    append+=_rewrite('heq',_table_at('H','n','x1','table_append_old_transport'),'x1','hv_witness')
    append+=_call('hc_right_right_right','n','u')+('exact hn','exact hlow','exact hv_witness','exact hext_witness_right_left')

    exists=_intro('N')+('induction N',)+_intro('F','G','hF','hG')+('exists F',)
    exists+=_call('dirichlet_convolution_table_zero_constructor','F','G','F')+('exact hF','exact hG','exact hF')
    exists+=_intro('F','G','hF','hG')+(f"have hprev : exists H. ({_convolution_table('N','F','G','H','table_exists_previous')})",)
    exists+=_call('IH','F','G')+_call('signed_table_domain_resize','S N','N','F')+('exact hF',)
    exists+=_call('signed_table_domain_resize','S N','N','G')+('exact hG','cases hprev',
             f"have hz : exists z. ({_convolution('F','G','S N','z','table_exists_next_value')})")
    exists+=_call('dirichlet_convolution_sum_exists','S N','F','G','S N')
    exists+=('exact hF','exact hG','intro hzero','apply PA1','exact hzero')+_call('le_refl','S N')
    exists+=('cases hz',f"have hnext : exists K. ({_convolution_table('S N','F','G','K','table_exists_next')}) /\\ ({_table_equal('x','K','S N','table_exists_preserve')})")
    exists+=_call('dirichlet_convolution_table_append','N','F','G','x','x1')
    exists+=('exact hprev_witness','exact hz_witness','cases hnext','cases hnext_witness','exists x2','exact hnext_witness_left')

    lookup=_intro('N','F','G','H','n','hc','hn','hbound')+_parts('hc',4)
    lookup+=(f"have hz : exists z. ({_table_at('H','n','z','table_lookup_construct')})",)
    lookup+=_call('divisor_signed_table_lookup','N','H','n')+('exact hc_right_right_left','exact hbound','cases hz','exists x','split','exact hz_witness')
    lookup+=_call('hc_right_right_right','n','x')+('exact hn','exact hbound','exact hz_witness')

    unique=_intro('N','F','G','H','K','hH','hK')+_parts('hH',4)+_parts('hK',4)+_intro('n','a','b','hn','hbound','ha','hb')
    unique+=_call('dirichlet_convolution_sum_functional','F','G','n','a','b')
    unique+=_call('hH_right_right_right','n','a')+('exact hn','exact hbound','exact ha')
    unique+=_call('hK_right_right_right','n','b')+('exact hn','exact hbound','exact hb')

    total=_intro('N','F','G','hF','hG')+(f"have h : exists H. ({_convolution_table('N','F','G','H','table_unique_construct')})",)
    total+=_call('dirichlet_convolution_table_exists','N','F','G')+('exact hF','exact hG','cases h','exists x','split','exact h_witness')
    total+=_intro('K','hK')+_call('dirichlet_convolution_table_extensional','N','F','G','x','K')+('exact h_witness','exact hK')

    restrict=_intro('N','J','F','G','H','hc','hJN')+_parts('hc',4)
    for table,assumption in (('F','hc_left'),('G','hc_right_left'),('H','hc_right_right_left')):
        restrict+=('split',)+_call('divisor_signed_table_restrict','N','J',table)+('exact '+assumption,'exact hJN')
    restrict+=_intro('n','z','hn','hnJ','hz')+_call('hc_right_right_right','n','z')+('exact hn',)
    restrict+=_call('le_trans','n','J','N')+('exact hnJ','exact hJN','exact hz')
    return (
        spec('dirichlet_convolution_table_zero_constructor',
             f"forall F G H. ({_table('0','F','table_zero_left')}) -> ({_table('0','G','table_zero_right')}) -> ({_table('0','H','table_zero_output')}) -> ({_convolution_table('0','F','G','H','table_zero_result')})",
             ('le_zero',),base,
             'At bound zero any actual output table is a valid empty positive-window convolution table; no zero-entry value is prescribed.'),
        spec('dirichlet_convolution_table_append',
             f"forall N F G H z. ({_convolution_table('N','F','G','H','table_append_previous')}) -> ({_convolution('F','G','S N','z','table_append_value')}) -> "
             f"exists K. ({_convolution_table('S N','F','G','K','table_append_result')}) /\\ ({_table_equal('H','K','S N','table_append_preserved')})",
             ('arithmetic_signed_table_append','signed_table_domain_resize','le_eq_or_lt',
              'divisor_signed_table_at_functional','le_of_succ_le_succ','divisor_signed_table_lookup'),append,
             'Append the genuinely computed next convolution value by actual beta recoding, preserving every earlier value including an arbitrary output value at zero.'),
        spec('dirichlet_convolution_table_exists',
             f"forall N F G. ({_table('N','F','table_exists_left')}) -> ({_table('N','G','table_exists_right')}) -> exists H. ({_convolution_table('N','F','G','H','table_exists_result')})",
             ('dirichlet_convolution_table_zero_constructor','signed_table_domain_resize','dirichlet_convolution_sum_exists','le_refl','dirichlet_convolution_table_append'),exists,
             'Finite induction constructs an actual convolution table at every positive index through N, including a genuine table witness when N is zero.'),
        spec('dirichlet_convolution_table_lookup',
             f"forall N F G H n. ({_convolution_table('N','F','G','H','table_lookup_source')}) -> ~(n=0) -> ({_le('n','N','table_lookup_bound')}) -> "
             f"exists z. ({_table_at('H','n','z','table_lookup_entry')}) /\\ ({_convolution('F','G','n','z','table_lookup_value')})",
             ('divisor_signed_table_lookup',),lookup,
             'Every positive in-domain convolution-table entry supplies its actual canonical value and complete finite signed fold.'),
        spec('dirichlet_convolution_table_extensional',
             f"forall N F G H K. ({_convolution_table('N','F','G','H','table_unique_first')}) -> ({_convolution_table('N','F','G','K','table_unique_second')}) -> ({_positive_equal('H','K','N','table_unique_values')})",
             ('dirichlet_convolution_sum_functional',),unique,
             'All actual output tables agree at precisely the positive indices through N; their zero entries and beta encodings need not agree.'),
        spec('dirichlet_convolution_table_exists_extensionally_unique',
             f"forall N F G. ({_table('N','F','table_total_left')}) -> ({_table('N','G','table_total_right')}) -> exists H. "
             +_and(_convolution_table('N','F','G','H','table_total_result'),f"forall K. ({_convolution_table('N','F','G','K','table_total_other')}) -> ({_positive_equal('H','K','N','table_total_equal')})"),
             ('dirichlet_convolution_table_exists','dirichlet_convolution_table_extensional'),total,
             'Construct the entire finite Dirichlet-convolution table and prove positive-window uniqueness, not equality of arbitrary codes or zeroth values.'),
        spec('dirichlet_convolution_table_restrict',
             f"forall N J F G H. ({_convolution_table('N','F','G','H','table_restrict_source')}) -> ({_le('J','N','table_restrict_bound')}) -> ({_convolution_table('J','F','G','H','table_restrict_result')})",
             ('divisor_signed_table_restrict','le_trans'),restrict,
             'The same actual inputs and output restrict to every smaller positive window, including J=0, without changing any encoded value.'),
    )


def make_dirichlet_convolution_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _entry_rows(spec)+_prefix_rows(spec)+_sum_rows(spec)+_positive_source_rows(spec)+_table_rows(spec)


__all__=['dirichlet_convolution_entry_relation','dirichlet_convolution_prefix_relation',
         'dirichlet_convolution_sum_relation','dirichlet_convolution_table_relation',
         'make_dirichlet_convolution_candidate_theorems']
