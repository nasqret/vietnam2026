"""Actual finite signed Dirichlet inverses and triangular table construction.

The inverse graph contains genuine delta and convolution tables, not the
unit-at-one criterion.  All represented values at zero remain independent.
The constructive solver first handles an arbitrary target table; its scalar
step solves a real signed affine equation after a genuinely constructed
proper prefix, and only then appends the new input value.
"""

from __future__ import annotations

from typing import Any, Callable

from .arithmetic_table_extension_candidate import _extension
from .dirichlet_convolution_candidate import _convolution, _convolution_table, _prefix
from .dirichlet_signed_unit_candidate import _unit
from .dirichlet_units_candidate import _delta, _delta_value
from .divisor_mask_candidate import _positive_equal
from .divisor_sum_algebra_candidate import _add_code
from .divisor_sum_table_candidate import _signed_sum, _table, _table_at, _table_equal
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _intro, _le, _lt, _parts, _public, _rewrite,
)
from .signed_table_operations_candidate import _mul_code


def _unit_at_one(F: str, tag: str) -> str:
    return (f'({_table_at(F,"1","2",tag+"positive")}) \\/ '
            f'({_table_at(F,"1","1",tag+"negative")})')


def _inverse(N: str, F: str, G: str, tag: str) -> str:
    E='di_delta_'+tag
    return f'exists {E}. '+_and(
        _delta(N,E,tag+'delta'),
        _convolution_table(N,F,G,E,tag+'left'),
        _convolution_table(N,G,F,E,tag+'right'))


def dirichlet_unit_at_one_relation(
    F: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """An actual lookup at one is canonical signed +1 or -1."""
    return _public(_unit_at_one,(F,),tag=tag,variables=variables)


def dirichlet_inverse_relation(
    N: str, F: str, G: str, *, tag: str, variables: tuple[str,...],
) -> str:
    """A genuine delta witness and both actual finite convolution identities."""
    return _public(_inverse,(N,F,G),tag=tag,variables=variables)


def _elementary_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    from_value=_intro('F','u','ha','hu')+('cases hu','left')
    from_value+=_rewrite('hu_left',_table_at('F','1','u','unit_from_value'),'u','ha')+('exact ha','right')
    from_value+=_rewrite('hu_right',_table_at('F','1','u','unit_from_value'),'u','ha')+('exact ha',)

    restrict=_intro('N','K','E','hd','hK')+('cases hd','split')
    restrict+=_call('divisor_signed_table_restrict','N','K','E')+('exact hd_left','exact hK')
    restrict+=_intro('n','z','hn','hb','hz')+_call('hd_right','n','z')+('exact hn',)
    restrict+=_call('le_trans','n','K','N')+('exact hb','exact hK','exact hz')

    zero=_intro('F','G','hF','hG')+(f"have hd : exists E. ({_delta('0','E','zero_actual_delta')}) /\\ ({_table_at('E','0','0','zero_delta_value')})",)
    zero+=_call('dirichlet_kronecker_delta_table_exists','0','0')+('cases hd','cases hd_witness','cases hd_witness_left',
             'exists x','split','exact hd_witness_left','split')
    zero+=_call('dirichlet_convolution_table_zero_constructor','F','G','x')
    zero+=('exact hF','exact hG','exact hd_witness_left_left')
    zero+=_call('dirichlet_convolution_table_zero_constructor','G','F','x')
    zero+=('exact hG','exact hF','exact hd_witness_left_left')
    return (
        spec('dirichlet_unit_at_one_witness',
             f"forall F. ({_unit_at_one('F','unit_witness_source')}) -> exists u. "+
             _and(_table_at('F','1','u','unit_witness_entry'),_unit('u','unit_witness_unit')),
             (),_intro('F','hu')+('cases hu','exists 2','split','exact hu_left','left','refl',
                                  'exists 1','split','exact hu_right','right','refl'),
             'An actual unit-at-one lookup supplies its canonical signed unit code; no inverse property is hidden in the predicate.'),
        spec('dirichlet_unit_at_one_from_value',
             f"forall F u. ({_table_at('F','1','u','unit_value_entry')}) -> ({_unit('u','unit_value_unit')}) -> "
             f"({_unit_at_one('F','unit_value_result')})",(),from_value,
             'A genuine lookup with a canonical signed unit value satisfies the two-case unit-at-one predicate.'),
        spec('dirichlet_kronecker_delta_table_restrict',
             f"forall N K E. ({_delta('N','E','delta_restrict_source')}) -> ({_le('K','N','delta_restrict_bound')}) -> "
             f"({_delta('K','E','delta_restrict_result')})",('divisor_signed_table_restrict','le_trans'),restrict,
             'The same actual delta table restricts to every smaller positive window, without changing its unrelated zeroth value.'),
        spec('dirichlet_inverse_from_right_delta',
             f"forall N F G E. ({_delta('N','E','inverse_right_delta')}) -> "
             f"({_convolution_table('N','G','F','E','inverse_right_product')}) -> ({_inverse('N','F','G','inverse_right_result')})",
             ('dirichlet_convolution_table_commutative',),
             _intro('N','F','G','E','hd','hc')+('exists E','split','exact hd','split')
             +_call('dirichlet_convolution_table_commutative','N','G','F','E')+('exact hc','exact hc'),
             'One actual right-delta convolution supplies both inverse laws by the already proved finite commutativity theorem.'),
        spec('dirichlet_inverse_symmetric',
             f"forall N F G. ({_inverse('N','F','G','inverse_symm_source')}) -> ({_inverse('N','G','F','inverse_symm_result')})",(),
             _intro('N','F','G','hi')+('cases hi',)+_parts('hi_witness',3)
             +('exists x','split','exact hi_witness_left','split','exact hi_witness_right_right','exact hi_witness_right_left'),
             'Swapping the two actual convolution identities makes the original table an inverse of its inverse.'),
        spec('dirichlet_inverse_actual_tables',
             f"forall N F G. ({_inverse('N','F','G','inverse_tables_source')}) -> "+
             _and(_table('N','F','inverse_tables_left'),_table('N','G','inverse_tables_right')),(),
             _intro('N','F','G','hi')+('cases hi',)+_parts('hi_witness',3)+_parts('hi_witness_right_left',4)
             +('split','exact hi_witness_right_left_left','exact hi_witness_right_left_right_left'),
             'The inverse graph entails actual valid input tables; it is never a vacuous equation between missing lookups.'),
        spec('dirichlet_inverse_zero',
             f"forall F G. ({_table('0','F','inverse_zero_left')}) -> ({_table('0','G','inverse_zero_right')}) -> "
             f"({_inverse('0','F','G','inverse_zero_result')})",
             ('dirichlet_kronecker_delta_table_exists','dirichlet_convolution_table_zero_constructor'),zero,
             'Every pair of actual zero-window tables has a genuine delta witness and both empty positive-domain inverse identities, with no condition at one.'),
    )


def _construction_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    step=_intro('N','F','T','G','u','hF','hT','hu','hunit','hc')+_parts('hc',4)
    step+=(f"have hp : exists M r. "+_and(_prefix('G','F','S N','N','M','solve_step_prefix'),
                                          _signed_sum('M','S N','r','solve_step_remainder')),)
    step+=_call('dirichlet_convolution_strict_prefix_exists','S N','N','F','G')
    step+=('exact hF','exact hc_left')+_cases('hp',2)+('cases hp_witness_witness',
             f"have he : exists e. ({_table_at('T','S N','e','solve_step_target')})")
    step+=_call('divisor_signed_table_lookup','S N','T','S N')+('exact hT',)+_call('le_refl','S N')
    step+=('cases he',f"have hs : exists a b. "+_and(_mul_code('a','u','b','solve_step_product'),_add_code('x1','b','x2','solve_step_equation')))
    step+=_call('dirichlet_signed_unit_affine_solve','x1','u','x2')+('exact hunit',)+_cases('hs',2)+('cases hs_witness_witness',
             f"have hx : exists H. ({_extension('G','H','S N','x3','solve_step_extension')})")
    step+=_call('arithmetic_signed_table_append','N','G','x3')+('exact hc_left','cases hx')+_parts('hx_witness',3)
    step+=(f"have hlast : {_convolution('x5','F','S N','x2','solve_step_last_sum')}",)
    step+=_call('dirichlet_convolution_first_input_append_step','N','G','F','x','x1','x5','x3','u','x4','x2')
    step+=('exact hp_witness_witness_left','exact hp_witness_witness_right','exact hx_witness','exact hu','exact hs_witness_witness_left','exact hs_witness_witness_right',
           'exists x5','split','split','exact hx_witness_left','split','exact hF','split','exact hT')
    step+=_intro('n','z','hn','hb','hz')+(f"have hcase : n=S N \\/ ({_lt('n','S N','solve_step_cases')})",)
    step+=_call('le_eq_or_lt','n','S N')+('exact hb','cases hcase')
    step+=_rewrite('hcase_left',_table_at('T','n','z','solve_step_last_target'),'n','hz')
    step+=('have heq : x2=z',)+_call('divisor_signed_table_at_functional','T','S N','x2','z')+('exact he_witness','exact hz')
    step+=_rewrite('heq',_convolution('x5','F','S N','x2','solve_step_last_rewrite'),'x2','hlast')
    step+=_rewrite('hcase_left',_convolution('x5','F','n','z','solve_step_index_rewrite'),'n')+('exact hlast',)
    step+=_call('dirichlet_convolution_first_input_append_preserves','G','F','x5','S N','x3','n','z')
    step+=('exact hx_witness','exact hcase_right')+_call('hc_right_right_right','n','z')+('exact hn',)
    step+=_call('le_of_succ_le_succ','n','N')+('exact hcase_right','exact hz','exact hx_witness_right_left')

    exists=_intro('N')+('induction N',)+_intro('F','T','u','w','hF','hT','hu','hunit')
    exists+=(f"have hg : exists G. ({_table('0','G','solve_base_table')}) /\\ ({_table_at('G','0','w','solve_base_zero')})",)
    exists+=_call('arithmetic_signed_table_singleton','w')+('cases hg','cases hg_witness','exists x','split')
    exists+=_call('dirichlet_convolution_table_zero_constructor','x','F','T')
    exists+=('exact hg_witness_left','exact hF','exact hT','exact hg_witness_right')
    exists+=_intro('F','T','u','w','hF','hT','hu','hunit')+(f"have hp : exists G. "+_and(
        _convolution_table('N','G','F','T','solve_previous'),_table_at('G','0','w','solve_previous_zero')),)
    exists+=_call('IH','F','T','u','w')+_call('signed_table_domain_resize','S N','N','F')+('exact hF',)
    exists+=_call('signed_table_domain_resize','S N','N','T')+('exact hT','exact hu','exact hunit','cases hp','cases hp_witness',
             f"have hx : exists H. "+_and(_convolution_table('S N','H','F','T','solve_next'),_table_equal('x','H','S N','solve_next_preserved')))
    exists+=_call('dirichlet_unit_equation_append','N','F','T','x','u')
    exists+=('exact hF','exact hT','exact hu','exact hunit','exact hp_witness_left','cases hx','cases hx_witness',
             'exists x1','split','exact hx_witness_left','cases hx_witness_left')
    exists+=_call('arithmetic_signed_table_equal_entry_transport','S N','x','x1','S N','0','w')
    exists+=('exact hx_witness_left_left','exact hx_witness_right')+_call('zero_le','S N')
    exists+=_call('succ_le_succ','0','N')+_call('zero_le','N')+('exact hp_witness_right',)
    return (
        spec('dirichlet_unit_equation_append',
             f"forall N F T G u. ({_table('S N','F','solve_append_F')}) -> ({_table('S N','T','solve_append_T')}) -> "
             f"({_table_at('F','1','u','solve_append_coefficient')}) -> ({_unit('u','solve_append_unit')}) -> "
             f"({_convolution_table('N','G','F','T','solve_append_previous')}) -> exists H. "+_and(
                 _convolution_table('S N','H','F','T','solve_append_result'),_table_equal('G','H','S N','solve_append_preserved')),
             ('dirichlet_convolution_strict_prefix_exists','divisor_signed_table_lookup','le_refl','dirichlet_signed_unit_affine_solve','arithmetic_signed_table_append',
              'dirichlet_convolution_first_input_append_step','le_eq_or_lt','divisor_signed_table_at_functional',
              'dirichlet_convolution_first_input_append_preserves','le_of_succ_le_succ'),step,
             'Construct the proper signed remainder, solve its unit-coefficient equation, append the actual new input value and preserve every earlier convolution; the target table is arbitrary.'),
        spec('dirichlet_unit_equation_construct',
             f"forall N F T u w. ({_table('N','F','solve_construct_F')}) -> ({_table('N','T','solve_construct_T')}) -> "
             f"({_table_at('F','1','u','solve_construct_coefficient')}) -> ({_unit('u','solve_construct_unit')}) -> exists G. "+
             _and(_convolution_table('N','G','F','T','solve_construct_result'),_table_at('G','0','w','solve_construct_zero')),
             ('arithmetic_signed_table_singleton','dirichlet_convolution_table_zero_constructor','signed_table_domain_resize',
              'dirichlet_unit_equation_append','arithmetic_signed_table_equal_entry_transport','zero_le','succ_le_succ'),exists,
             'Finite induction constructs an actual solution G*F=T for every target table and signed unit F(1), with an arbitrary prescribed G(0), including actual witnesses when N=0.'),
    )


def _calculus_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    unique=_intro('N','F','G','H','hg','hh')+('cases hg',)+_parts('hg_witness',3)+('cases hh',)+_parts('hh_witness',3)
    unique+=_parts('hg_witness_right_left',4)+_parts('hh_witness_right_left',4)
    unique+=(f"have hl : {_convolution_table('N','x','H','H','unique_left_unit')}",)
    unique+=_call('dirichlet_delta_left_table','N','H','x')+('exact hh_witness_right_left_right_left','exact hg_witness_left')
    unique+=(f"have hr : {_convolution_table('N','G','x1','G','unique_right_unit')}",)
    unique+=_call('dirichlet_delta_right_table','N','G','x1')+('exact hg_witness_right_left_right_left','exact hh_witness_left')
    unique+=_parts('hl',4)+_parts('hr',4)+_intro('n','a','b','hn','hb','ha','hv')+('symm',)
    unique+=_call('dirichlet_convolution_associative','N','G','F','H','x','x1','n','b','a')
    unique+=('exact hg_witness_right_right','exact hh_witness_right_left','exact hn','exact hb')
    unique+=_call('hl_right_right_right','n','b')+('exact hn','exact hb','exact hv')
    unique+=_call('hr_right_right_right','n','a')+('exact hn','exact hb','exact ha')

    restrict=_intro('N','K','F','G','hi','hb')+('cases hi',)+_parts('hi_witness',3)+('exists x','split')
    restrict+=_call('dirichlet_kronecker_delta_table_restrict','N','K','x')+('exact hi_witness_left','exact hb','split')
    restrict+=_call('dirichlet_convolution_table_restrict','N','K','F','G','x')+('exact hi_witness_right_left','exact hb')
    restrict+=_call('dirichlet_convolution_table_restrict','N','K','G','F','x')+('exact hi_witness_right_right','exact hb')
    return (
        spec('dirichlet_inverse_positive_unique',
             f"forall N F G H. ({_inverse('N','F','G','inverse_unique_first')}) -> ({_inverse('N','F','H','inverse_unique_second')}) -> "
             f"({_positive_equal('G','H','N','inverse_unique_result')})",
             ('dirichlet_delta_left_table','dirichlet_delta_right_table','dirichlet_convolution_associative'),unique,
             'Associativity and independently constructed delta identities force any two actual inverses to agree at every positive input; neither their codes nor their zero values are identified.'),
        spec('dirichlet_inverse_restrict',
             f"forall N K F G. ({_inverse('N','F','G','inverse_restrict_source')}) -> ({_le('K','N','inverse_restrict_bound')}) -> "
             f"({_inverse('K','F','G','inverse_restrict_result')})",
             ('dirichlet_kronecker_delta_table_restrict','dirichlet_convolution_table_restrict'),restrict,
             'An actual inverse restricts with its actual delta witness to every smaller finite positive window, including zero.'),
        spec('dirichlet_inverse_prefix_compatible',
             f"forall N K F G H. ({_inverse('N','F','G','inverse_prefix_large')}) -> ({_inverse('K','F','H','inverse_prefix_small')}) -> "
             f"({_le('K','N','inverse_prefix_bound')}) -> ({_positive_equal('G','H','K','inverse_prefix_result')})",
             ('dirichlet_inverse_positive_unique','dirichlet_inverse_restrict'),
             _intro('N','K','F','G','H','hg','hh','hb')+_call('dirichlet_inverse_positive_unique','K','F','G','H')
             +_call('dirichlet_inverse_restrict','N','K','F','G')+('exact hg','exact hb','exact hh'),
             'Independently constructed inverse prefixes have identical represented positive values on their common smaller domain.'),
        spec('dirichlet_inverse_involution',
             f"forall N F G H. ({_inverse('N','F','G','inverse_involution_first')}) -> ({_inverse('N','G','H','inverse_involution_second')}) -> "
             f"({_positive_equal('F','H','N','inverse_involution_result')})",
             ('dirichlet_inverse_positive_unique','dirichlet_inverse_symmetric'),
             _intro('N','F','G','H','hg','hh')+_call('dirichlet_inverse_positive_unique','N','G','F','H')
             +_call('dirichlet_inverse_symmetric','N','F','G')+('exact hg','exact hh'),
             'Taking an actual Dirichlet inverse twice recovers precisely the original positive represented values, with no encoding or zeroth-value uniqueness claim.'),
    )


def _inverse_construction_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    unit=_intro('N','F','u','w','hF','hu','hunit')+(f"have hd : exists E. "+_and(
        _delta('N','E','construct_delta'),_table_at('E','0','0','construct_delta_zero')),)
    unit+=_call('dirichlet_kronecker_delta_table_exists','N','0')+('cases hd','cases hd_witness','cases hd_witness_left',
              f"have hg : exists G. "+_and(_convolution_table('N','G','F','x','construct_inverse_equation'),
                                          _table_at('G','0','w','construct_inverse_zero')))
    unit+=_call('dirichlet_unit_equation_construct','N','F','x','u','w')
    unit+=('exact hF','exact hd_witness_left_left','exact hu','exact hunit','cases hg','cases hg_witness',
           'exists x1','split')
    unit+=_call('dirichlet_inverse_from_right_delta','N','F','x1','x')
    unit+=('exact hd_witness_left','exact hg_witness_left','exact hg_witness_right')

    at_one=_intro('N','F','w','hF','hone')+(f"have hu : exists u. "+_and(
        _table_at('F','1','u','construct_unit_entry'),_unit('u','construct_unit_value')),)
    at_one+=_call('dirichlet_unit_at_one_witness','F')+('exact hone','cases hu','cases hu_witness')
    at_one+=_call('dirichlet_inverse_from_unit','N','F','x','w')
    at_one+=('exact hF','exact hu_witness_left','exact hu_witness_right')

    zero=_intro('F','w','hF')+(f"have hg : exists G. "+_and(
        _table('0','G','construct_empty_table'),_table_at('G','0','w','construct_empty_zero')),)
    zero+=_call('arithmetic_signed_table_singleton','w')+('cases hg','cases hg_witness','exists x','split')
    zero+=_call('dirichlet_inverse_zero','F','x')+('exact hF','exact hg_witness_left','exact hg_witness_right')

    constructed=_intro('N','F','w','hF','hc')+('cases hc',)
    constructed+=_rewrite('hc_left',_table('N','F','construct_empty_input'),'N','hF')
    constructed+=_rewrite('hc_left','exists G. '+_and(_inverse('N','F','G','construct_empty_result'),
                                                     _table_at('G','0','w','construct_empty_prescribed')),'N')
    constructed+=_call('dirichlet_inverse_zero_construct','F','w')+('exact hF',)
    constructed+=_call('dirichlet_inverse_from_unit_at_one','N','F','w')+('exact hF','exact hc_right')
    return (
        spec('dirichlet_inverse_from_unit',
             f"forall N F u w. ({_table('N','F','inverse_unit_input')}) -> ({_table_at('F','1','u','inverse_unit_entry')}) -> "
             f"({_unit('u','inverse_unit_value')}) -> exists G. "+_and(
                 _inverse('N','F','G','inverse_unit_result'),_table_at('G','0','w','inverse_unit_zero')),
             ('dirichlet_kronecker_delta_table_exists','dirichlet_unit_equation_construct','dirichlet_inverse_from_right_delta'),unit,
             'Construct an actual delta target and solve the genuine triangular convolution equation; both inverse laws and the independently prescribed zeroth value follow.'),
        spec('dirichlet_inverse_from_unit_at_one',
             f"forall N F w. ({_table('N','F','inverse_at_one_input')}) -> ({_unit_at_one('F','inverse_at_one_unit')}) -> exists G. "+
             _and(_inverse('N','F','G','inverse_at_one_result'),_table_at('G','0','w','inverse_at_one_zero')),
             ('dirichlet_unit_at_one_witness','dirichlet_inverse_from_unit'),at_one,
             'Either actual canonical unit value at one constructively supplies a finite Dirichlet inverse, with any requested value at zero.'),
        spec('dirichlet_inverse_zero_construct',
             f"forall F w. ({_table('0','F','inverse_zero_construct_input')}) -> exists G. "+
             _and(_inverse('0','F','G','inverse_zero_construct_result'),_table_at('G','0','w','inverse_zero_construct_zero')),
             ('arithmetic_signed_table_singleton','dirichlet_inverse_zero'),zero,
             'The empty positive window has a genuinely constructed inverse for any prescribed zeroth value, without assuming any lookup or unit condition at one.'),
        spec('dirichlet_inverse_construct',
             f"forall N F w. ({_table('N','F','inverse_construct_input')}) -> (N=0 \\/ ({_unit_at_one('F','inverse_construct_condition')})) -> exists G. "+
             _and(_inverse('N','F','G','inverse_construct_result'),_table_at('G','0','w','inverse_construct_zero')),
             ('dirichlet_inverse_zero_construct','dirichlet_inverse_from_unit_at_one'),constructed,
             'The exact empty-window-or-unit-at-one condition constructs actual inverse witnesses, preserving an arbitrary requested value at zero.'),
    )


def _necessity_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    necessary=_intro('N','F','G','hi','hn')+('cases hi',)+_parts('hi_witness',3)+_parts('hi_witness_right_left',4)
    necessary+=(f"have hbound : {_le('1','N','necessary_one_bound')}",)
    necessary+=_call('one_le_of_ne_zero','N')+('exact hn',)
    for label,table,guard in (('ha','F','hi_witness_right_left_left'),
                               ('hb','G','hi_witness_right_left_right_left'),
                               ('he','x','hi_witness_right_left_right_right_left')):
        necessary+=(f"have {label} : exists a. ({_table_at(table,'1','a','necessary_lookup_'+label)})",)
        necessary+=_call('divisor_signed_table_lookup','N',table,'1')+('exact '+guard,'exact hbound','cases '+label)
    necessary+=('have heq : x3=2',)+_call('dirichlet_kronecker_delta_table_one_value','N','x','x3')
    necessary+=('exact hi_witness_left','exact hbound','exact he_witness')
    necessary+=_rewrite('heq',_table_at('x','1','x3','necessary_delta_rewrite'),'x3','he_witness')
    convolution=_convolution('F','G','1','2','necessary_one_convolution')
    product=_mul_code('x1','x2','2','necessary_one_product')
    necessary+=(f"have hc : {convolution}",)+_call('hi_witness_right_left_right_right_right','1','2')
    necessary+=('intro hz','apply PA1','exact hz','exact hbound','exact he_witness',
                'have hiff : '+_and(f'({convolution}) -> ({product})',f'({product}) -> ({convolution})'))
    necessary+=_call('dirichlet_convolution_at_one_iff','F','G','x1','x2','2')
    necessary+=('exact ha_witness','exact hb_witness','cases hiff',f'have hp : {product}')
    necessary+=_call('hiff_left')+('exact hc','have hu : (x1=2 /\\ x2=2) \\/ (x1=1 /\\ x2=1)')
    necessary+=_call('dirichlet_signed_unit_product_classification','x1','x2')+('exact hp',)
    necessary+=_call('dirichlet_unit_at_one_from_value','F','x1')+('exact ha_witness','cases hu','cases hu_left',
                 'left','exact hu_left_left','cases hu_right','right','exact hu_right_left')
    return (spec('dirichlet_inverse_requires_unit_at_one',
                 f"forall N F G. ({_inverse('N','F','G','inverse_necessary_source')}) -> ~(N=0) -> "
                 f"({_unit_at_one('F','inverse_necessary_result')})",
                 ('one_le_of_ne_zero','divisor_signed_table_lookup','dirichlet_kronecker_delta_table_one_value',
                  'dirichlet_convolution_at_one_iff','dirichlet_signed_unit_product_classification','dirichlet_unit_at_one_from_value'),necessary,
                 'At the genuinely in-domain index one, the actual convolution is a signed product equal to one, forcing the original value to be +1 or -1; the nonempty-domain guard is essential.'),)


def _criterion_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    inv=_inverse('N','F','G','criterion_inverse')
    condition=f"N=0 \\/ ({_unit_at_one('F','criterion_unit')})"
    criterion=_intro('N','F','hF')+('split','intro hi','cases hi','have hc : N=0 \\/ ~(N=0)')
    criterion+=_call('eq_decidable','N','0')+('cases hc','left','exact hc_left','right')
    criterion+=_call('dirichlet_inverse_requires_unit_at_one','N','F','x')+('exact hi_witness','exact hc_right','intro hc',
                 'have hg : exists G. '+_and(_inverse('N','F','G','criterion_constructed'),_table_at('G','0','0','criterion_zero')))
    criterion+=_call('dirichlet_inverse_construct','N','F','0')+('exact hF','exact hc','cases hg','cases hg_witness','exists x','exact hg_witness_left')

    positive=_intro('N','F','hF','hn')+('split','intro hi','cases hi')
    positive+=_call('dirichlet_inverse_requires_unit_at_one','N','F','x')+('exact hi_witness','exact hn','intro hu',
                 'have hg : exists G. '+_and(_inverse('N','F','G','positive_constructed'),_table_at('G','0','0','positive_zero')))
    positive+=_call('dirichlet_inverse_from_unit_at_one','N','F','0')
    positive+=('exact hF','exact hu','cases hg','cases hg_witness','exists x','exact hg_witness_left')

    unique=_intro('N','F','w','hF','hc')+('have hg : exists G. '+_and(
        _inverse('N','F','G','unique_construct_inverse'),_table_at('G','0','w','unique_construct_zero')),)
    unique+=_call('dirichlet_inverse_construct','N','F','w')+('exact hF','exact hc','cases hg','cases hg_witness',
             'exists x','split','exact hg_witness_left','split','exact hg_witness_right','intro H','intro hh')
    unique+=_call('dirichlet_inverse_positive_unique','N','F','x','H')+('exact hg_witness_left','exact hh')
    return (
        spec('dirichlet_inverse_criterion',
             f"forall N F. ({_table('N','F','criterion_input')}) -> "+_and(
                 f'(exists G. ({inv})) -> ({condition})',f'({condition}) -> exists G. ({inv})'),
             ('eq_decidable','dirichlet_inverse_requires_unit_at_one','dirichlet_inverse_construct'),criterion,
             'An actual finite signed arithmetic table has a Dirichlet inverse exactly when the positive window is empty or its actual value at one is +1 or -1.'),
        spec('dirichlet_inverse_positive_criterion',
             f"forall N F. ({_table('N','F','positive_criterion_input')}) -> ~(N=0) -> "+_and(
                 f'(exists G. ({_inverse("N","F","G","positive_criterion_inverse")})) -> ({_unit_at_one("F","positive_criterion_unit")})',
                 f'({_unit_at_one("F","positive_criterion_unit")}) -> exists G. ({_inverse("N","F","G","positive_criterion_inverse")})'),
             ('dirichlet_inverse_requires_unit_at_one','dirichlet_inverse_from_unit_at_one'),positive,
             'On a nonempty positive domain the general constructive inverse criterion is precisely the actual signed unit-at-one condition.'),
        spec('dirichlet_inverse_exists_positive_unique',
             f"forall N F w. ({_table('N','F','unique_construct_input')}) -> (N=0 \\/ ({_unit_at_one('F','unique_construct_condition')})) -> exists G. "+_and(
                 _inverse('N','F','G','unique_construct_result'),_table_at('G','0','w','unique_construct_value_zero'),
                 f"forall H. ({_inverse('N','F','H','unique_construct_other')}) -> ({_positive_equal('G','H','N','unique_construct_values')})"),
             ('dirichlet_inverse_construct','dirichlet_inverse_positive_unique'),unique,
             'Construct an actual inverse with any prescribed zeroth value and prove that every actual inverse agrees with it on all positive inputs, including the genuine empty-window boundary.'),
    )


def make_dirichlet_inverse_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (_elementary_rows(spec)+_construction_rows(spec)+_inverse_construction_rows(spec)
            +_necessity_rows(spec)+_calculus_rows(spec)+_criterion_rows(spec))


__all__=['dirichlet_unit_at_one_relation','dirichlet_inverse_relation','make_dirichlet_inverse_candidate_theorems']
