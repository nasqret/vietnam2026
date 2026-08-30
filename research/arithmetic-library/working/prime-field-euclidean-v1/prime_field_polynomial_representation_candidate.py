"""Working constructive representation algebra for highest-degree-first lists.

Left padding adds actual leading zeros, not the right-zero extension used by
the convolution antidiagonal.  Polynomial equivalence compares coefficients
at each power, never values at field elements or raw beta-code equality.
All public graphs are conservative HA expansions.  This working module is
unregistered and does not change a released source, provider, or proof gate.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _and, _call, _intro, _lt, _parts, _prime, _public,
    _add as _field_add, _mul as _field_mul, _inv as _field_inverse,
)
from peano_lab.library.prime_field_polynomial_candidate import (
    _add, _at, _coeff, _equal, _repeat, _scale,
)
from peano_lab.library.prime_field_polynomial_subtraction_candidate import _subtract
from peano_lab.library.prime_field_polynomial_convolution_candidate import _coefficient, _convolution
from peano_lab.library.prime_field_polynomial_trim_candidate import _suffix, _trim
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _le(a: str, b: str, tag: str) -> str:
    gap='pfrep_gap_'+tag
    return f'exists {gap}. {gap}+({a})=({b})'


def _left_pad(b: str, c: str, length: str, count: str,
              d: str, e: str, tag: str) -> str:
    i,a='pfrep_index_'+tag,'pfrep_value_'+tag
    copied=(f'forall {i} {a}. ({_lt(i,length,tag+"bound")}) -> '
            f'({_at(b,c,i,a,tag+"input")}) -> '
            f'({_at(d,e,f"({count})+{i}",a,tag+"output")})')
    return _and(_repeat(d,e,'0',count,tag+'zeros'),copied)


def _power_coefficient(b: str, c: str, length: str,
                       power: str, value: str, tag: str) -> str:
    i='pfrep_position_'+tag
    inside=f'exists {i}. '+_and(f'{i}+S ({power})=({length})',_at(b,c,i,value,tag+'entry'))
    outside=_and(_le(length,power,tag+'outside'),f'({value})=0')
    return f'({inside}) \\/ ({outside})'


def _equivalent(b: str, c: str, length: str, d: str, e: str,
                other_length: str, tag: str) -> str:
    k,a,r=(f'pfrep_{role}_{tag}' for role in ('power','left','right'))
    return (f'forall {k} {a} {r}. '
            f'({_power_coefficient(b,c,length,k,a,tag+"first")}) -> '
            f'({_power_coefficient(d,e,other_length,k,r,tag+"second")}) -> {a}={r}')


def prime_field_polynomial_left_pad_relation(b: str, c: str, length: str,
        count: str, d: str, e: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Actual count leading zeros, then the input prefix; length count+length."""
    return _public(_left_pad,(b,c,length,count,d,e),tag=tag,variables=variables)


def prime_field_polynomial_power_coefficient_relation(b: str, c: str, length: str,
        power: str, value: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Actual coefficient at X^power, zero only outside the represented length."""
    return _public(_power_coefficient,(b,c,length,power,value),tag=tag,variables=variables)


def prime_field_polynomial_equivalent_relation(b: str, c: str, length: str,
        d: str, e: str, other_length: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Formal coefficient equality across lengths, not equality of evaluations."""
    return _public(_equivalent,(b,c,length,d,e,other_length),tag=tag,variables=variables)


def _index_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    bound=spec(
        'prime_field_polynomial_power_index_bound',
        f"forall i k L. i+S k=L -> ({_lt('i','L','power_index_bound')})",
        ('add_comm',),
        _intro('i','k','L','h')+('exists k','trans i+S k','simp [add_comm]','exact h'),
        'A coefficient indexed by its power is genuinely inside the highest-degree-first prefix.',
    )
    body=_intro('t','L','i','hi')+(f"have ho : ({_le('t','i','index_case_ge')}) \\/ ({_lt('i','t','index_case_lt')})",)
    body+=_call('le_or_lt','t','i')+('cases ho','cases ho_left','have heq : t+x=i','trans x+t','apply add_comm','exact ho_left_witness','right','exists x','split','cases hi','exists x1')
    body+=_call('add_left_cancel','t','x1+S x','L')+('trans x1+S (t+x)','simp [add_comm,add_assoc]')
    body+=('rewrite heq','exact hi_witness','symm','exact heq','left','exact ho_right')
    cases=spec(
        'prime_field_polynomial_left_pad_index_cases',
        f"forall t L i. ({_lt('i','t+L','index_cases_bound')}) -> "
        f"({_lt('i','t','index_cases_zero')}) \\/ exists j. ({_and(_lt('j','L','index_cases_copy'),'i=t+j')})",
        ('le_or_lt','add_left_cancel','add_comm','add_assoc'),body,
        'Every index in an actual left-padded window is in its zero block or has an actual bounded source index.',
    )
    body=_intro('t','L','i','k','hi','hk')+(f"have ho : ({_le('t','i','power_pad_ge')}) \\/ ({_lt('i','t','power_pad_lt')})",)
    body+=_call('le_or_lt','t','i')+('cases ho','cases ho_left',f"have hbad : {_lt('k','L','power_pad_contradiction')}",'exists x')
    body+=_call('add_left_cancel','t','x+S k','L')+('trans (t+x)+S k','symm','apply add_assoc')
    body+=('have heq : t+x=i','trans x+t','apply add_comm','exact ho_left_witness','rewrite heq','exact hi','exfalso')
    body+=_call('lt_not_le','k','L')+('exact hbad','exact hk','exact ho_right')
    before=spec(
        'prime_field_polynomial_power_index_before_padding',
        f"forall t L i k. i+S k=t+L -> ({_le('L','k','power_before_outside')}) -> ({_lt('i','t','power_before_result')})",
        ('le_or_lt','add_left_cancel','add_assoc','add_comm','lt_not_le'),body,
        'A power beyond the source degree can only access the actual added leading-zero block.',
    )
    return bound,cases,before


def _power_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body=_intro('b','c','L','k')+(f"have ho : ({_le('L','k','power_exists_outside')}) \\/ ({_lt('k','L','power_exists_inside')})",)
    body+=_call('le_or_lt','L','k')+('cases ho','exists 0','right','split','exact ho_left','refl','cases ho_right')
    body+=(f"have hv : exists a. ({_at('b','c','x','a','power_exists_value')})",)+_call('beta_at_exists','b','c','x')
    body+=('cases hv','exists x1','left','exists x','split','exact ho_right_witness','exact hv_witness')
    exists=spec(
        'prime_field_polynomial_power_coefficient_exists',
        f"forall b c L k. exists a. ({_power_coefficient('b','c','L','k','a','power_exists')})",
        ('le_or_lt','beta_at_exists'),body,
        'Every natural power has an actual decoded coefficient or the proved exterior zero, for arbitrary beta encodings.',
    )
    body=_intro('b','c','L','k','a','r','ha','hr')+('cases ha','cases ha_left','cases ha_left_witness','cases hr','cases hr_left','cases hr_left_witness','have heq : x=x1')
    body+=_call('add_right_cancel','x','x1','S k')+('trans L','exact ha_left_witness_left','symm','exact hr_left_witness_left')
    body+=_rewrite_all('heq',_at('b','c','x','a','power_unique_recode'),'x','ha_left_witness_right')
    body+=_call('beta_at_unique','b','c','x1','a','r')+('exact ha_left_witness_right','exact hr_left_witness_right','cases hr_right','exfalso')
    body+=_call('lt_not_le','k','L')+('exists x','exact ha_left_witness_left','exact hr_right_left')
    body+=('cases ha_right','cases hr','cases hr_left','cases hr_left_witness','exfalso')
    body+=_call('lt_not_le','k','L')+('exists x','exact hr_left_witness_left','exact ha_right_left','cases hr_right','trans 0','exact ha_right_right','symm','exact hr_right_right')
    functional=spec(
        'prime_field_polynomial_power_coefficient_functional',
        f"forall b c L k a r. ({_power_coefficient('b','c','L','k','a','power_unique_a')}) -> "
        f"({_power_coefficient('b','c','L','k','r','power_unique_r')}) -> a=r",
        ('add_right_cancel','beta_at_unique','lt_not_le'),body,
        'The actual coefficient of a formal power is unique, including the exterior and empty-prefix cases.',
    )
    body=_intro('b','c','d','e','L','k','a','he','ha')+('cases ha','cases ha_left','cases ha_left_witness','left','exists x','split','exact ha_left_witness_left')
    body+=_call('he','x','a')+_call('prime_field_polynomial_power_index_bound','x','k','L')+('exact ha_left_witness_left','exact ha_left_witness_right','right','exact ha_right')
    transport=spec(
        'prime_field_polynomial_power_coefficient_transport',
        f"forall b c d e L k a. ({_equal('b','c','d','e','L','power_transport_equal')}) -> "
        f"({_power_coefficient('b','c','L','k','a','power_transport_old')}) -> "
        f"({_power_coefficient('d','e','L','k','a','power_transport_new')})",
        ('prime_field_polynomial_power_index_bound',),body,
        'An exact decoded-prefix recoding preserves every formal coefficient at the same annotated length.',
    )
    return exists,functional,transport


def _equivalence_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    # Reflexivity expands to exactly power_coefficient_functional. Reuse that
    # checked statement rather than enrolling a second name for the same AST.
    symmetric=spec(
        'prime_field_polynomial_equivalent_symmetric',
        f"forall b c L d e M. ({_equivalent('b','c','L','d','e','M','equivalent_symmetric_old')}) -> "
        f"({_equivalent('d','e','M','b','c','L','equivalent_symmetric_new')})",
        (),_intro('b','c','L','d','e','M','he','k','a','r','ha','hr')+('have heq : r=a',)+_call('he','k','r','a')+('exact hr','exact ha','symm','exact heq'),
        'Formal coefficient equivalence is symmetric without choosing canonical raw beta codes.',
    )
    body=_intro('b','c','L','d','e','M','f','g','N','he','hf','k','a','r','ha','hr')
    body+=(f"have hv : exists z. ({_power_coefficient('d','e','M','k','z','equivalent_middle')})",)
    body+=_call('prime_field_polynomial_power_coefficient_exists','d','e','M','k')+('cases hv','trans x')
    body+=_call('he','k','a','x')+('exact ha','exact hv_witness')+_call('hf','k','x','r')+('exact hv_witness','exact hr')
    transitive=spec(
        'prime_field_polynomial_equivalent_transitive',
        f"forall b c L d e M f g N. ({_equivalent('b','c','L','d','e','M','equivalent_transitive_a')}) -> "
        f"({_equivalent('d','e','M','f','g','N','equivalent_transitive_b')}) -> "
        f"({_equivalent('b','c','L','f','g','N','equivalent_transitive_result')})",
        ('prime_field_polynomial_power_coefficient_exists',),body,
        'Transitivity obtains an actual intermediate coefficient; it never assumes existential decoding.',
    )
    forward=spec(
        'prime_field_polynomial_equal_implies_equivalent',
        f"forall b c d e L. ({_equal('b','c','d','e','L','equal_to_equivalent_input')}) -> "
        f"({_equivalent('b','c','L','d','e','L','equal_to_equivalent_result')})",
        ('prime_field_polynomial_power_coefficient_functional','prime_field_polynomial_power_coefficient_transport'),
        _intro('b','c','d','e','L','he','k','a','r','ha','hr')+_call('prime_field_polynomial_power_coefficient_functional','d','e','L','k','a','r')
        +_call('prime_field_polynomial_power_coefficient_transport','b','c','d','e','L','k','a')+('exact he','exact ha','exact hr'),
        'The inherited same-length decoded equality implies formal polynomial equivalence.',
    )
    body=_intro('b','c','d','e','L','he','i','a','hi','ha')+('cases hi','have hs : i+S x=L','trans x+S i','simp [add_comm]','exact hi_witness')
    body+=(f"have hv : exists r. ({_at('d','e','i','r','equivalent_to_equal_lookup')})",)+_call('beta_at_exists','d','e','i')+('cases hv','have heq : a=x1')
    body+=_call('he','x','a','x1')+('left','exists i','split','exact hs','exact ha','left','exists i','split','exact hs','exact hv_witness')
    body+=_rewrite_all('heq',_at('d','e','i','a','equivalent_to_equal_target'),'a')+('exact hv_witness',)
    backward=spec(
        'prime_field_polynomial_equivalent_implies_equal_same_length',
        f"forall b c d e L. ({_equivalent('b','c','L','d','e','L','equivalent_to_equal_input')}) -> "
        f"({_equal('b','c','d','e','L','equivalent_to_equal_result')})",
        ('add_comm','beta_at_exists'),body,
        'At a common annotated length, formal coefficient equivalence gives the exact inherited decoded-prefix equality.',
    )
    return symmetric,transitive,forward,backward


def _padding_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    zero=spec(
        'prime_field_polynomial_left_pad_zero',
        f"forall b c L. ({_left_pad('b','c','L','0','b','c','left_pad_zero')})",
        ('matrix_rank_no_index_below_zero','zero_add'),
        _intro('b','c','L')+('split',)+_intro('i','hi')+('exfalso',)+_call('matrix_rank_no_index_below_zero','i')+('exact hi',)
        +_intro('i','a','hi','ha')+('have hindex : 0+i=i','apply zero_add','rewrite hindex','rewrite hindex','exact ha'),
        'Zero left padding uses the original code and changes no coefficient.',
    )
    body=_intro('b','c','t')+('induction L',f"have hz : exists d e. ({_repeat('d','e','0','t','left_pad_empty_zeros')})")
    body+=_call('beta_repeat_exists','0','t')+('cases hz','cases hz_witness','exists x','exists x1','split','exact hz_witness_witness')
    body+=_intro('i','a','hi','ha')+('exfalso',)+_call('matrix_rank_no_index_below_zero','i')+('exact hi',)
    body+=(f"have hold : exists d e. ({_left_pad('b','c','L','t','d','e','left_pad_previous')})",'exact IH','cases hold','cases hold_witness','cases hold_witness_witness')
    body+=(f"have ha : exists a. ({_at('b','c','L','a','left_pad_next_source')})",)+_call('beta_at_exists','b','c','L')+('cases ha',)
    body+=(f"have hn : exists d e. ({_and(_at('d','e','t+L','x2','left_pad_next_entry'),_equal('x','x1','d','e','t+L','left_pad_preserved'))})",)
    body+=_call('beta_prefix_extend','t+L','x','x1','x2')+('cases hn','cases hn_witness','cases hn_witness_witness','exists x3','exists x4','split')
    body+=_intro('i','hi')+_call('hn_witness_witness_right','i','0')+_call('lt_of_lt_of_le','i','t','t+L')+('exact hi',)
    body+=_call('le_add_right','t','L')+_call('hold_witness_witness_left','i')+('exact hi',)
    body+=_intro('i','a','hi','ha0')+(f"have ho : i=L \\/ ({_lt('i','L','left_pad_old_index')})",)+_call('finite_lt_succ_eq_or_lt','L','i')+('exact hi','cases ho')
    body+=_rewrite_all('ho_left',_at('x3','x4','t+i','a','left_pad_appended'),'i')
    body+=('have heq : a=x2',)+_call('beta_at_unique','b','c','L','a','x2')
    body+=_rewrite_all('ho_left',_at('b','c','i','a','left_pad_last_source'),'i','ha0')+('exact ha0','exact ha_witness')
    body+=_rewrite_all('heq',_at('x3','x4','t+L','a','left_pad_last_target'),'a')+('exact hn_witness_witness_left',)
    body+=_call('hn_witness_witness_right','t+i','a')+_call('matrix_recursive_lt_add_left','i','L','t')+('exact ho_right',)
    body+=_call('hold_witness_witness_right','i','a')+('exact ho_right','exact ha0')
    exists=spec(
        'prime_field_polynomial_left_pad_exists',
        f"forall b c t L. exists d e. ({_left_pad('b','c','L','t','d','e','left_pad_exists')})",
        ('beta_repeat_exists','matrix_rank_no_index_below_zero','beta_at_exists','beta_prefix_extend',
         'lt_of_lt_of_le','le_add_right','finite_lt_succ_eq_or_lt','beta_at_unique','matrix_recursive_lt_add_left'),body,
        'Finite induction genuinely constructs the zero block and appends every actual input coefficient, including empty input and arbitrary encodings.',
    )
    entry=spec(
        'prime_field_polynomial_left_pad_entry',
        f"forall b c L t d e i a r. ({_left_pad('b','c','L','t','d','e','left_pad_entry_graph')}) -> "
        f"({_lt('i','L','left_pad_entry_bound')}) -> ({_at('b','c','i','a','left_pad_entry_source')}) -> "
        f"({_at('d','e','t+i','r','left_pad_entry_target')}) -> r=a",
        ('beta_at_unique',),_intro('b','c','L','t','d','e','i','a','r','h','hi','ha','hr')+('cases h',)
        +_call('beta_at_unique','d','e','t+i','r','a')+('exact hr',)+_call('h_right','i','a')+('exact hi','exact ha'),
        'Each copied coefficient is identified with the actual source value, without identifying codes.',
    )
    body=_intro('p','b','c','L','t','d','e','hp','hc','h','i','hi')+('cases h',)
    body+=(f"have ho : ({_lt('i','t','left_pad_bound_zero')}) \\/ exists j. ({_and(_lt('j','L','left_pad_bound_source'),'i=t+j')})",)
    body+=_call('prime_field_polynomial_left_pad_index_cases','t','L','i')+('exact hi','cases ho','exists 0','split')
    body+=_call('h_left','i')+('exact ho_left',)+_call('prime_field_zero_below_prime','p')+('exact hp','cases ho_right','cases ho_right_witness')
    body+=(f"have hv : exists a. ({_and(_at('b','c','x','a','left_pad_bound_entry'),_lt('a','p','left_pad_bound_value'))})",)
    body+=_call('hc','x')+('exact ho_right_witness_left','cases hv','cases hv_witness','exists x1','split')
    body+=_rewrite_all('ho_right_witness_right',_at('d','e','i','x1','left_pad_bound_target'),'i')
    body+=_call('h_right','x','x1')+('exact ho_right_witness_left','exact hv_witness_left','exact hv_witness_right')
    bounded=spec(
        'prime_field_polynomial_left_pad_bounded',
        f"forall p b c L t d e. ({_prime('p','left_pad_bounded_prime')}) -> ({_coeff('p','b','c','L','left_pad_bounded_source')}) -> "
        f"({_left_pad('b','c','L','t','d','e','left_pad_bounded_graph')}) -> ({_coeff('p','d','e','t+L','left_pad_bounded_target')})",
        ('prime_field_polynomial_left_pad_index_cases','prime_field_zero_below_prime'),body,
        'Actual leading-zero padding preserves canonical prime-field bounds at its exact enlarged length.',
    )
    body=_intro('b','c','L','t','d','e','f','g','hd','hf','i','a','hi','ha')+('cases hd','cases hf',)
    body+=(f"have ho : ({_lt('i','t','left_pad_equal_zero')}) \\/ exists j. ({_and(_lt('j','L','left_pad_equal_source'),'i=t+j')})",)
    body+=_call('prime_field_polynomial_left_pad_index_cases','t','L','i')+('exact hi','cases ho','have heq : a=0')
    body+=_call('beta_at_unique','d','e','i','a','0')+('exact ha',)+_call('hd_left','i')+('exact ho_left',)
    body+=_rewrite_all('heq',_at('f','g','i','a','left_pad_equal_zero_target'),'a')+_call('hf_left','i')+('exact ho_left','cases ho_right','cases ho_right_witness')
    body+=(f"have hv : exists z. ({_at('b','c','x','z','left_pad_equal_choice')})",)+_call('beta_at_exists','b','c','x')+('cases hv','have heq : a=x1')
    body+=_call('beta_at_unique','d','e','t+x','a','x1')
    body+=_rewrite_all('ho_right_witness_right',_at('d','e','i','a','left_pad_equal_old'),'i','ha')+('exact ha',)
    body+=_call('hd_right','x','x1')+('exact ho_right_witness_left','exact hv_witness')
    body+=_rewrite_all('ho_right_witness_right',_at('f','g','i','a','left_pad_equal_new_index'),'i')
    body+=_rewrite_all('heq',_at('f','g','t+x','a','left_pad_equal_new_value'),'a')
    body+=_call('hf_right','x','x1')+('exact ho_right_witness_left','exact hv_witness')
    functional=spec(
        'prime_field_polynomial_left_pad_functional',
        f"forall b c L t d e f g. ({_left_pad('b','c','L','t','d','e','left_pad_functional_first')}) -> "
        f"({_left_pad('b','c','L','t','f','g','left_pad_functional_second')}) -> ({_equal('d','e','f','g','t+L','left_pad_functional_result')})",
        ('prime_field_polynomial_left_pad_index_cases','beta_at_unique','beta_at_exists'),body,
        'Any two constructed left pads have equal decoded coefficients on the full padded length.',
    )
    return zero,exists,entry,bounded,functional


def _trim_padding_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body=_intro('b','c','L','t','d','e','hz','hs')+('split','exact hz')+_intro('i','a','hi','ha')
    body+=(f"have hv : exists r. ({_at('d','e','t+i','r','suffix_to_pad_choice')})",)+_call('beta_at_exists','d','e','t+i')+('cases hv','have heq : x=a')
    body+=_call('beta_at_unique','b','c','i','x','a')+_call('hs','i','x')+('exact hi','exact hv_witness','exact ha')
    body+=_rewrite_all('heq',_at('d','e','t+i','x','suffix_to_pad_rewrite'),'x','hv_witness')+('exact hv_witness',)
    suffix=spec(
        'prime_field_polynomial_zero_suffix_left_pad',
        f"forall b c L t d e. ({_repeat('d','e','0','t','suffix_to_pad_zero')}) -> "
        f"({_suffix('d','e','t','b','c','L','suffix_to_pad_suffix')}) -> ({_left_pad('b','c','L','t','d','e','suffix_to_pad_result')})",
        ('beta_at_exists','beta_at_unique'),body,
        'A real suffix after an actual zero block gives the reverse decoding needed by genuine left padding.',
    )
    trim=spec(
        'prime_field_polynomial_trim_left_pad',
        f"forall p b c L t d e M. ({_trim('p','b','c','L','t','d','e','M','trim_to_pad_source')}) -> "
        f"({_left_pad('d','e','M','t','b','c','trim_to_pad_result')})",
        ('prime_field_polynomial_zero_suffix_left_pad',),
        _intro('p','b','c','L','t','d','e','M','h')+_parts('h',5)
        +_call('prime_field_polynomial_zero_suffix_left_pad','d','e','M','t','b','c')+('exact h_right_right_left','exact h_right_right_right_left'),
        'Actual trimming identifies its input as the retained coefficient prefix with exactly the removed leading zeros restored.',
    )
    body=_intro('b','c','L','t','d','e','k','a','h','ha')+('cases h','cases ha','cases ha_left','cases ha_left_witness','left','exists t+x','split','trans t+(x+S k)','apply add_assoc','rewrite ha_left_witness_left','refl')
    body+=_call('h_right','x','a')+_call('prime_field_polynomial_power_index_bound','x','k','L')+('exact ha_left_witness_left','exact ha_left_witness_right','cases ha_right')
    body+=(f"have ho : ({_le('t+L','k','pad_power_outside')}) \\/ ({_lt('k','t+L','pad_power_inside')})",)+_call('le_or_lt','t+L','k')
    body+=('cases ho','right','split','exact ho_left','exact ha_right_right','cases ho_right','left','exists x','split','exact ho_right_witness')
    body+=_rewrite_all('ha_right_right',_at('d','e','x','a','pad_power_zero_target'),'a')
    body+=_call('h_left','x')+_call('prime_field_polynomial_power_index_before_padding','t','L','x','k')+('exact ho_right_witness','exact ha_right_left')
    power=spec(
        'prime_field_polynomial_left_pad_power_coefficient',
        f"forall b c L t d e k a. ({_left_pad('b','c','L','t','d','e','pad_power_graph')}) -> "
        f"({_power_coefficient('b','c','L','k','a','pad_power_source')}) -> "
        f"({_power_coefficient('d','e','t+L','k','a','pad_power_result')})",
        ('add_assoc','prime_field_polynomial_power_index_bound','le_or_lt','prime_field_polynomial_power_index_before_padding'),body,
        'Adding actual leading zeros preserves each formal power coefficient, including the zero coefficients above the old leading power.',
    )
    equivalent=spec(
        'prime_field_polynomial_left_pad_equivalent',
        f"forall b c L t d e. ({_left_pad('b','c','L','t','d','e','pad_equivalent_source')}) -> "
        f"({_equivalent('b','c','L','d','e','t+L','pad_equivalent_result')})",
        ('prime_field_polynomial_power_coefficient_functional','prime_field_polynomial_left_pad_power_coefficient'),
        _intro('b','c','L','t','d','e','h','k','a','r','ha','hr')+_call('prime_field_polynomial_power_coefficient_functional','d','e','t+L','k','a','r')
        +_call('prime_field_polynomial_left_pad_power_coefficient','b','c','L','t','d','e','k','a')+('exact h','exact ha','exact hr'),
        'Leading-zero padding is harmless for formal polynomial coefficients, unlike right padding by trailing zeros.',
    )
    body=_intro('p','b','c','L','t','d','e','M','h')+(f"have hc : {_trim('p','b','c','L','t','d','e','M','trim_equivalence_copy')}",'exact h')+_parts('hc',5)
    body+=_rewrite_all('hc_left',_equivalent('b','c','L','d','e','M','trim_equivalence_length'),'L')
    body+=_call('prime_field_polynomial_equivalent_symmetric','d','e','M','b','c','t+M')
    body+=_call('prime_field_polynomial_left_pad_equivalent','d','e','M','t','b','c')
    body+=_call('prime_field_polynomial_trim_left_pad','p','b','c','L','t','d','e','M')+('exact h',)
    trimmed=spec(
        'prime_field_polynomial_trim_equivalent',
        f"forall p b c L t d e M. ({_trim('p','b','c','L','t','d','e','M','trim_equivalence_source')}) -> "
        f"({_equivalent('b','c','L','d','e','M','trim_equivalence_result')})",
        ('prime_field_polynomial_equivalent_symmetric','prime_field_polynomial_left_pad_equivalent','prime_field_polynomial_trim_left_pad'),body,
        'The actually constructed trimmed representation has exactly the same formal coefficients as its original input.',
    )
    return suffix,trim,power,equivalent,trimmed


def _padding_transport_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    args=('b','c','B','C','L','t','d','e','D','E')
    body=_intro(*args,'hi','ho','h')+('cases h',f"have hr : {_equal('B','C','b','c','L','pad_transport_reverse')}")
    body+=_call('matrix_rank_prefix_equality_symmetric','b','c','B','C','L')+('exact hi','split')
    body+=_intro('i','hindex')+_call('ho','i','0')+_call('lt_of_lt_of_le','i','t','t+L')+('exact hindex',)
    body+=_call('le_add_right','t','L')+_call('h_left','i')+('exact hindex',)
    body+=_intro('i','a','hindex','ha')+_call('ho','t+i','a')+_call('matrix_recursive_lt_add_left','i','L','t')+('exact hindex',)
    body+=_call('h_right','i','a')+('exact hindex',)+_call('hr','i','a')+('exact hindex','exact ha')
    transport=spec(
        'prime_field_polynomial_left_pad_transport',
        f"forall {' '.join(args)}. ({_equal('b','c','B','C','L','pad_transport_input')}) -> "
        f"({_equal('d','e','D','E','t+L','pad_transport_output')}) -> "
        f"({_left_pad('b','c','L','t','d','e','pad_transport_old')}) -> "
        f"({_left_pad('B','C','L','t','D','E','pad_transport_new')})",
        ('matrix_rank_prefix_equality_symmetric','lt_of_lt_of_le','le_add_right','matrix_recursive_lt_add_left'),body,
        'Input and full-output recoding preserve the actual leading-zero block and every copied coefficient.',
    )
    return (transport,)


def _operation_transport_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    result=[]
    for kind in ('add','subtract','scale'):
        scaled=kind=='scale'
        originals=(('ab','ac'),('bb','bc')) if scaled else (('ab','ac'),('bb','bc'),('cb','cc'))
        targets=tuple((b.upper(),c.upper()) for b,c in originals)
        letters=('a','r') if scaled else ('a','b','r')
        if scaled:
            args=('p','k',*(item for pair in originals for item in pair),'L','t',*(item for pair in targets for item in pair))
            old=_scale('p','k','ab','ac','bb','bc','L','pad_operation_old')
            new=_scale('p','k','AB','AC','BB','BC','t+L','pad_operation_new')
            field=_field_mul('p','k','a','r','pad_operation_point')
        else:
            args=('p',*(item for pair in originals for item in pair),'L','t',*(item for pair in targets for item in pair))
            operation=_add if kind=='add' else _subtract
            old=operation('p','ab','ac','bb','bc','cb','cc','L','pad_operation_old')
            new=operation('p','AB','AC','BB','BC','CB','CC','t+L','pad_operation_new')
            field=_field_add('p','a','b','r','pad_operation_point') if kind=='add' else _field_add('p','b','r','a','pad_operation_point')
        pads=tuple(_left_pad(b,c,'L','t',B,C,'pad_operation_'+b) for (b,c),(B,C) in zip(originals,targets,strict=True))
        hypotheses=tuple('h'+str(i) for i in range(len(pads)))
        body=_intro(*args,'hp','hop',*hypotheses)
        for hypothesis in hypotheses:
            body+=('cases '+hypothesis,)
        point_hypothesis='hop'
        if scaled:
            body+=('cases hop','split','exact hop_left')
            point_hypothesis='hop_right'
        body+=_intro('i','hi')+(f"have hc : ({_lt('i','t','pad_operation_zero')}) \\/ exists j. ({_and(_lt('j','L','pad_operation_source'),'i=t+j')})",)
        body+=_call('prime_field_polynomial_left_pad_index_cases','t','L','i')+('exact hi','cases hc',)
        body+=tuple('exists 0' for _ in letters)
        for hypothesis in hypotheses:
            body+=('split',)+_call(hypothesis+'_left','i')+('exact hc_left',)
        if scaled:
            body+=_call('prime_field_multiply_zero_right','p','k')+('exact hp','exact hop_left')
        else:
            body+=_call('prime_field_add_zero_right','p','0')+('exact hp',)+_call('prime_field_zero_below_prime','p')+('exact hp',)
        body+=('cases hc_right','cases hc_right_witness')
        point=_and(*(_at(b,c,'x',letter,'pad_operation_'+letter) for (b,c),letter in zip(originals,letters,strict=True)),field)
        body+=(f"have hv : exists {' '.join(letters)}. ({point})",)+_call(point_hypothesis,'x')+('exact hc_right_witness_left',)
        context='hv'
        for _ in letters:
            body+=('cases '+context,)
            context+='_witness'
        body+=_parts(context,len(letters)+1)
        body+=tuple('exists x'+str(i+1) for i in range(len(letters)))
        for index,((B,C),hypothesis) in enumerate(zip(targets,hypotheses,strict=True)):
            old_hyp=context+'_right'*index+'_left'
            body+=('split',)+_rewrite_all('hc_right_witness_right',_at(B,C,'i','x'+str(index+1),'pad_operation_output_'+str(index)),'i')
            body+=_call(hypothesis+'_right','x','x'+str(index+1))+('exact hc_right_witness_left','exact '+old_hyp)
        body+=('exact '+context+'_right'*len(letters),)
        dependencies=('prime_field_polynomial_left_pad_index_cases',)+(
            ('prime_field_multiply_zero_right',) if scaled else ('prime_field_add_zero_right','prime_field_zero_below_prime'))
        result.append(spec(
            'prime_field_polynomial_'+kind+'_left_pad_transport',
            f"forall {' '.join(args)}. "+' -> '.join(f'({clause})' for clause in (_prime('p','pad_operation_prime'),old,*pads,new)),
            dependencies,body,
            'Common actual leading-zero padding preserves the genuine aligned '+kind+' coefficient operation, including empty prefixes.',
        ))
    return tuple(result)


def _zero_equivalence_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body=_intro('b','c','L','k','a','hz','ha')+('cases ha','cases ha_left','cases ha_left_witness')
    body+=_call('beta_repeat_entry_eq','b','c','0','L','x','a')+('exact hz',)
    body+=_call('prime_field_polynomial_power_index_bound','x','k','L')+('exact ha_left_witness_left','exact ha_left_witness_right','cases ha_right','exact ha_right_right')
    value=spec(
        'prime_field_polynomial_zero_power_coefficient',
        f"forall b c L k a. ({_repeat('b','c','0','L','zero_power_source')}) -> "
        f"({_power_coefficient('b','c','L','k','a','zero_power_entry')}) -> a=0",
        ('beta_repeat_entry_eq','prime_field_polynomial_power_index_bound'),body,
        'Every formal power coefficient of an actual zero prefix is zero, including exterior powers.',
    )
    body=_intro('b','c','L','hz','k','a','r','ha','hr')+('trans 0',)
    body+=_call('prime_field_polynomial_zero_power_coefficient','b','c','L','k','a')+('exact hz','exact ha','have heq : r=0')
    body+=_call('prime_field_polynomial_zero_power_coefficient','0','0','0','k','r')
    body+=_call('beta_repeat_empty','0','0','0','0')+('refl','exact hr','symm','exact heq')
    empty=spec(
        'prime_field_polynomial_zero_prefix_equivalent_empty',
        f"forall b c L. ({_repeat('b','c','0','L','zero_equivalent_source')}) -> "
        f"({_equivalent('b','c','L','0','0','0','zero_equivalent_empty')})",
        ('prime_field_polynomial_zero_power_coefficient','beta_repeat_empty'),body,
        'An actual all-zero ambient convolution prefix represents the same formal polynomial as an empty product.',
    )
    return value,empty


def _constant_product_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    args=('p','ab','ac','L','bb','bc','k','i','a','r')
    body=_intro(*args,'hp','hA','hB','hk','hi','ha','hr')
    body+=('have hp0 : ~(p=0)','intro hpzero')+_call('prime_nonzero','p')+('exact hp','exact hpzero')
    body+=(f"have hc : exists c. ({_coefficient('p','ab','ac','i','bb','bc','1','i','c','constant_old_coefficient')})",)
    body+=_call('prime_field_convolution_coefficient_exists','p','ab','ac','i','bb','bc','1','i')+('exact hp0','cases hc','have hc0 : x=0')
    body+=_call('prime_field_convolution_coefficient_zero_past_support','p','ab','ac','i','bb','bc','1','i','x')+('exact hp0','exists 0','simp [zero_add]','exact hc_witness')
    body+=(f"have hshort : {_coefficient('p','ab','ac','S i','bb','bc','1','i','r','constant_short_coefficient')}",)
    body+=_call('prime_field_convolution_coefficient_prefix_transport','p','ab','ac','L','ab','ac','S i','bb','bc','1','S i','i','r')+('exact hi',)
    body+=_call('le_refl','S i')+_intro('j','z','hj','hz')+('exact hz',)+_call('le_refl','S i')+('exact hr',)
    body+=(f"have hm : exists z. ({_field_mul('p','a','k','z','constant_chosen_product')})",)
    body+=_call('prime_field_multiply_exists','p','a','k')+('exact hp',)
    body+=_call('matrix_rank_bounded_prefix_value','ab','ac','L','p','i','a')+('exact hA','exact hi','exact ha')
    body+=_call('matrix_rank_bounded_prefix_value','bb','bc','1','p','0','k')+('exact hB','exists 0','simp [zero_add]','exact hk','cases hm')
    body+=(f"have hs : {_field_add('p','x','x1','r','constant_actual_sum')}",)
    body+=_call('prime_field_convolution_coefficient_append','p','ab','ac','ab','ac','bb','bc','0','i','a','k','x','x1','r')
    body+=_intro('j','z','hj','hz')+('exact hz','exact ha','exact hk','exact hc_witness','exact hshort','exact hm_witness')
    body+=_rewrite_all('hc0',_field_add('p','x','x1','r','constant_sum_zero'),'x','hs')
    body+=('have heq : r=x1',)+_call('prime_field_add_functional','p','0','x1','r','x1')+('exact hs',)
    body+=_call('prime_field_add_zero_left','p','x1')+('exact hp',)
    body+=(f"have hmc : {_field_mul('p','a','k','x1','constant_product_copy')}",'exact hm_witness')+_parts('hmc',4)+('exact hmc_right_right_left',)
    body+=_rewrite_all('heq',_field_mul('p','k','a','r','constant_product_result'),'r')
    body+=_call('prime_field_multiply_commutative','p','a','k','x1')+('exact hm_witness',)
    coefficient=spec(
        'prime_field_polynomial_constant_right_coefficient',
        f"forall {' '.join(args)}. "+' -> '.join(f'({clause})' for clause in (
            _prime('p','constant_coefficient_prime'),_coeff('p','ab','ac','L','constant_coefficient_A'),
            _coeff('p','bb','bc','1','constant_coefficient_B'),_at('bb','bc','0','k','constant_coefficient_constant'),
            _lt('i','L','constant_coefficient_index'),_at('ab','ac','i','a','constant_coefficient_entry'),
            _coefficient('p','ab','ac','L','bb','bc','1','i','r','constant_coefficient_actual'),
            _field_mul('p','k','a','r','constant_coefficient_result'))),
        ('prime_nonzero','prime_field_convolution_coefficient_exists','prime_field_convolution_coefficient_zero_past_support',
         'zero_add','prime_field_convolution_coefficient_prefix_transport','le_refl','prime_field_multiply_exists',
         'matrix_rank_bounded_prefix_value','prime_field_convolution_coefficient_append','prime_field_add_functional',
         'prime_field_add_zero_left','prime_field_multiply_commutative'),body,
        'The actual antidiagonal coefficient with a length-one right factor is its actual scalar product, by triangular append and proved vanished prior support.',
    )
    args=('p','k','ab','ac','bb','bc','cb','cc','L')
    graph=lambda tag:_convolution('p','ab','ac','L','bb','bc','1','cb','cc','L',tag)
    body=_intro(*args,'hp','hk','hc')+(f"have hcopy : {graph('constant_product_copy')}",'exact hc')+_parts('hcopy',4)+('split',)
    body+=_call('matrix_rank_bounded_prefix_value','bb','bc','1','p','0','k')+('exact hcopy_right_left','exists 0','simp','exact hk')
    body+=_intro('i','hi')+(f"have ha : exists a. ({_at('ab','ac','i','a','constant_scale_source')})",)+_call('beta_at_exists','ab','ac','i')+('cases ha',)
    body+=(f"have hr : exists r. ({_at('cb','cc','i','r','constant_scale_target')})",)+_call('beta_at_exists','cb','cc','i')+('cases hr','exists x','exists x1','split','exact ha_witness','split','exact hr_witness')
    body+=_call('prime_field_polynomial_constant_right_coefficient','p','ab','ac','L','bb','bc','k','i','x','x1')+('exact hp','exact hcopy_left','exact hcopy_right_left','exact hk','exact hi','exact ha_witness')
    body+=_call('prime_field_polynomial_convolution_entry','p','ab','ac','L','bb','bc','1','cb','cc','L','i','x1')+('exact hc','exact hi','exact hr_witness')
    to_scale=spec(
        'prime_field_polynomial_constant_product_to_scale',
        f"forall {' '.join(args)}. ({_prime('p','constant_scale_prime')}) -> ({_at('bb','bc','0','k','constant_scale_value')}) -> "
        f"({graph('constant_scale_convolution')}) -> ({_scale('p','k','ab','ac','cb','cc','L','constant_scale_result')})",
        ('matrix_rank_bounded_prefix_value','beta_at_exists','prime_field_polynomial_constant_right_coefficient','prime_field_polynomial_convolution_entry'),body,
        'An actual proper-length constant-right polynomial product is the existing actual coefficient scalar action.',
    )
    body=_intro(*args,'hp','hB','hk','hs')+(f"have hb : {_and(_coeff('p','ab','ac','L','constant_recover_A'),_coeff('p','cb','cc','L','constant_recover_C'))}",)
    body+=_call('prime_field_polynomial_scale_bounded','p','k','ab','ac','cb','cc','L')+('exact hs','cases hb','split','exact hb_left','split','exact hB','split','have hz : L=0 \\/ ~(L=0)')
    body+=_call('eq_decidable','L','0')+('cases hz','left','split','left','exact hz_left','exact hz_left','right','split','exact hz_right','split','intro hbad')
    body+=_call('succ_ne_zero','0')+('exact hbad','simp')
    body+=_intro('i','hi')+(f"have hv : exists a r. ({_and(_at('ab','ac','i','a','constant_recover_source'),_at('cb','cc','i','r','constant_recover_target'),_field_mul('p','k','a','r','constant_recover_mul'))})",)
    body+=('cases hs',)+_call('hs_right','i')+('exact hi','cases hv','cases hv_witness')+_parts('hv_witness_witness',3)
    body+=(f"have hc : exists r. ({_coefficient('p','ab','ac','L','bb','bc','1','i','r','constant_recover_actual')})",)
    body+=_call('prime_field_convolution_coefficient_exists','p','ab','ac','L','bb','bc','1','i')+('intro hpzero',)+_call('prime_nonzero','p')+('exact hp','exact hpzero','cases hc','have heq : x2=x1')
    body+=_call('prime_field_multiply_functional','p','k','x','x2','x1')
    body+=_call('prime_field_polynomial_constant_right_coefficient','p','ab','ac','L','bb','bc','k','i','x','x2')
    body+=('exact hp','exact hb_left','exact hB','exact hk','exact hi','exact hv_witness_witness_left','exact hc_witness','exact hv_witness_witness_right_right','exists x1','split','exact hv_witness_witness_right_left')
    body+=_rewrite_all('heq',_coefficient('p','ab','ac','L','bb','bc','1','i','x2','constant_recover_rewrite'),'x2','hc_witness')+('exact hc_witness',)
    from_scale=spec(
        'prime_field_polynomial_scale_to_constant_product',
        f"forall {' '.join(args)}. ({_prime('p','constant_recover_prime')}) -> ({_coeff('p','bb','bc','1','constant_recover_constant')}) -> "
        f"({_at('bb','bc','0','k','constant_recover_value')}) -> ({_scale('p','k','ab','ac','cb','cc','L','constant_recover_scale')}) -> ({graph('constant_recover_product')})",
        ('prime_field_polynomial_scale_bounded','eq_decidable','succ_ne_zero','prime_field_convolution_coefficient_exists',
         'prime_nonzero','prime_field_multiply_functional','prime_field_polynomial_constant_right_coefficient'),body,
        'Recover a genuine convolution from scalar action by constructing every antidiagonal sum and identifying its residue, including the empty product case.',
    )
    return coefficient,to_scale,from_scale


def _inverse_scale_row(spec: Callable[...,Any]) -> Any:
    args=('p','a','k','ab','ac','bb','bc','L')
    body=_intro(*args,'hp','hinv','hs')+(f"have hbound : {_and(_coeff('p','ab','ac','L','inverse_scale_A'),_coeff('p','bb','bc','L','inverse_scale_B'))}",)
    body+=_call('prime_field_polynomial_scale_bounded','p','k','ab','ac','bb','bc','L')+('exact hs','cases hbound','cases hinv')
    body+=(f"have hm : {_field_mul('p','a','k','1','inverse_scale_product')}",'exact hinv_right')+_parts('hinv_right',4)
    body+=(f"have hr : exists cb cc. ({_scale('p','a','bb','bc','cb','cc','L','inverse_scale_actual')})",)
    body+=_call('prime_field_polynomial_scale_exists','p','a','bb','bc','L')+('intro hpzero',)+_call('prime_nonzero','p')+('exact hp','exact hpzero','exact hinv_right_left','exact hbound_right','cases hr','cases hr_witness')
    body+=(f"have he : {_equal('x','x1','ab','ac','L','inverse_scale_result_equal')}",)
    body+=_call('prime_field_polynomial_scale_associative','p','a','k','1','ab','ac','bb','bc','x','x1','ab','ac','L')+('exact hm','exact hs','exact hr_witness_witness')
    body+=_call('prime_field_polynomial_scale_one','p','ab','ac','L')+('exact hp','exact hbound_left')
    body+=_call('prime_field_polynomial_scale_transport','p','a','bb','bc','x','x1','bb','bc','ab','ac','L')
    body+=_intro('i','r','hi','hat')+('exact hat','exact he','exact hr_witness_witness')
    return spec(
        'prime_field_polynomial_inverse_scale',
        f"forall {' '.join(args)}. ({_prime('p','inverse_scale_prime')}) -> ({_field_inverse('p','a','k','inverse_scale_inverse')}) -> "
        f"({_scale('p','k','ab','ac','bb','bc','L','inverse_scale_forward')}) -> ({_scale('p','a','bb','bc','ab','ac','L','inverse_scale_backward')})",
        ('prime_field_polynomial_scale_bounded','prime_field_polynomial_scale_exists','prime_nonzero',
         'prime_field_polynomial_scale_associative','prime_field_polynomial_scale_one','prime_field_polynomial_scale_transport'),body,
        'An actual inverse scalar gives the reverse coefficient action, with a constructed intermediate table and exact decoded transport; no unit-associate law is assumed.',
    )


def make_prime_field_polynomial_representation_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (*_index_rows(spec),*_power_rows(spec),*_equivalence_rows(spec),
            *_padding_rows(spec),*_trim_padding_rows(spec),*_padding_transport_rows(spec),
            *_operation_transport_rows(spec),*_zero_equivalence_rows(spec),
            *_constant_product_rows(spec),_inverse_scale_row(spec))


__all__=[
    'prime_field_polynomial_left_pad_relation',
    'prime_field_polynomial_power_coefficient_relation',
    'prime_field_polynomial_equivalent_relation',
    'make_prime_field_polynomial_representation_candidate_theorems',
]
