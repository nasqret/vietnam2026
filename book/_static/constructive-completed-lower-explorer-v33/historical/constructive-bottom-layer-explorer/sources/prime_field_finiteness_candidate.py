"""Exact cardinality and characteristic of the constructed prime fields.

Cardinality uses an actual finite beta-coded bijection, not a Python list.
Characteristic uses a beta history starting at zero and adding the actual one
representative at each step.  The connection with ordinary modular residue is
proved by induction, so the characteristic is not built into its trace graph.
"""

from __future__ import annotations

from typing import Any, Callable

from .prime_field_arithmetic_candidate import (
    _add, _and, _call, _intro, _laws, _lt, _parts, _prime, _public, _residue,
)
from .prime_field_tables_candidate import _at, _rewrite_all, _tables


def _enumeration(p: str, b: str, c: str, tag: str) -> str:
    i = f"pff_enumeration_index_{tag}"
    return f"forall {i}. ({_lt(i,p,tag+'bound')}) -> ({_at(b,c,i,i,tag+'entry')})"


def _cardinality(p: str, b: str, c: str, tag: str) -> str:
    i, j, a = (f"pff_cardinality_{name}_{tag}" for name in ("i", "j", "a"))
    bounded = f"forall {i} {a}. ({_lt(i,p,tag+'bounded_index')}) -> ({_at(b,c,i,a,tag+'bounded_entry')}) -> ({_lt(a,p,tag+'bounded_value')})"
    injective = (f"forall {i} {j} {a}. ({_lt(i,p,tag+'injective_i')}) -> ({_lt(j,p,tag+'injective_j')}) -> "
                 f"({_at(b,c,i,a,tag+'injective_first')}) -> ({_at(b,c,j,a,tag+'injective_second')}) -> {i} = {j}")
    surjective = f"forall {a}. ({_lt(a,p,tag+'surjective_value')}) -> exists {i}. ({_lt(i,p,tag+'surjective_index')}) /\\ ({_at(b,c,i,a,tag+'surjective_entry')})"
    return _and(_enumeration(p,b,c,tag+'enumeration'),bounded,injective,surjective)


def _steps(p: str, b: str, c: str, n: str, tag: str) -> str:
    i, u, v = (f"pff_trace_{name}_{tag}" for name in ("index", "before", "after"))
    return (f"forall {i}. ({_lt(i,n,tag+'index')}) -> exists {u} {v}. "
            + _and(_at(b,c,i,u,tag+'before'),_at(b,c,f'S ({i})',v,tag+'after'),_add(p,u,'1',v,tag+'addition')))


def _trace(p: str, b: str, c: str, n: str, r: str, tag: str) -> str:
    return _and(_at(b,c,'0','0',tag+'start'),_at(b,c,n,r,tag+'terminal'),_steps(p,b,c,n,tag+'steps'))


def _multiple(p: str, n: str, r: str, tag: str) -> str:
    b, c = f"pff_history_code_{tag}", f"pff_history_scale_{tag}"
    return f"exists {b} {c}. ({_trace(p,b,c,n,r,tag+'history')})"


def _characteristic(p: str, tag: str) -> str:
    n = f"pff_smaller_positive_{tag}"
    return _and(_multiple(p,p,'0',tag+'modulus'),
                f"forall {n}. ({_lt(n,p,tag+'strict')}) -> ~({n} = 0) -> ~({_multiple(p,n,'0',tag+'smaller')})")


def _structure(p: str, ab: str, ac: str, mb: str, mc: str, nb: str, nc: str, ib: str, ic: str,
               eb: str, ec: str, tag: str) -> str:
    return _and(_tables(p,ab,ac,mb,mc,nb,nc,ib,ic,tag+'tables'),_cardinality(p,eb,ec,tag+'cardinality'),
                _laws(p,tag+'laws'),_characteristic(p,tag+'characteristic'))


def prime_field_enumeration_relation(p: str,b: str,c: str,*,tag: str,variables: tuple[str,...]) -> str:
    return _public(_enumeration,(p,b,c),tag=tag,variables=variables)


def prime_field_cardinality_relation(p: str,b: str,c: str,*,tag: str,variables: tuple[str,...]) -> str:
    """Actual p-entry enumeration, boundedness, injectivity and surjectivity."""
    return _public(_cardinality,(p,b,c),tag=tag,variables=variables)


def prime_field_unit_steps_relation(p: str,b: str,c: str,n: str,*,tag: str,variables: tuple[str,...]) -> str:
    return _public(_steps,(p,b,c,n),tag=tag,variables=variables)


def prime_field_unit_trace_relation(p: str,b: str,c: str,n: str,r: str,*,tag: str,variables: tuple[str,...]) -> str:
    """Start at zero and perform n actual additions of the one representative."""
    return _public(_trace,(p,b,c,n,r),tag=tag,variables=variables)


def prime_field_unit_multiple_relation(p: str,n: str,r: str,*,tag: str,variables: tuple[str,...]) -> str:
    return _public(_multiple,(p,n,r),tag=tag,variables=variables)


def prime_field_characteristic_relation(p: str,*,tag: str,variables: tuple[str,...]) -> str:
    """p repeated additions return zero; no positive smaller number does so."""
    return _public(_characteristic,(p,),tag=tag,variables=variables)


def prime_field_finite_structure_relation(p: str,ab: str,ac: str,mb: str,mc: str,nb: str,nc: str,ib: str,ic: str,
                                         eb: str,ec: str,*,tag: str,variables: tuple[str,...]) -> str:
    """Constructed tables, exact p-element bijection, proved laws and characteristic."""
    return _public(_structure,(p,ab,ac,mb,mc,nb,nc,ib,ic,eb,ec),tag=tag,variables=variables)


def _cardinality_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'prime_field_enumeration_value',
            f"forall p b c i a. ({_enumeration('p','b','c','enumeration_value_source')}) -> ({_lt('i','p','enumeration_value_bound')}) -> ({_at('b','c','i','a','enumeration_value_at')}) -> a = i",
            ('beta_at_unique',),
            _intro('p','b','c','i','a','henum','hi','hat') + _call('beta_at_unique','b','c','i','a','i')
            + ('exact hat',) + _call('henum','i') + ('exact hi',),
            'Every decoded entry of the identity enumeration equals its actual index.',
        ),
        spec(
            'prime_field_enumeration_is_bijection',
            f"forall p b c. ({_enumeration('p','b','c','bijection_source')}) -> ({_cardinality('p','b','c','bijection_result')})",
            ('prime_field_enumeration_value',),
            _intro('p','b','c','henum') + ('split','exact henum','split')
            + _intro('i','a','hi','hat') + ('have heq : a = i',)
            + _call('prime_field_enumeration_value','p','b','c','i','a') + ('exact henum','exact hi','exact hat','rewrite heq','exact hi','split')
            + _intro('i','j','a','hi','hj','hfirst','hsecond') + ('have hleft : a = i',)
            + _call('prime_field_enumeration_value','p','b','c','i','a') + ('exact henum','exact hi','exact hfirst','have hright : a = j')
            + _call('prime_field_enumeration_value','p','b','c','j','a') + ('exact henum','exact hj','exact hsecond','trans a','symm','exact hleft','exact hright')
            + _intro('a','ha') + ('exists a','split','exact ha') + _call('henum','a') + ('exact ha',),
            'The actual p-entry enumeration is bounded, injective and onto every canonical field representative.',
        ),
        spec(
            'prime_field_cardinality_exists',f"forall p. exists b c. ({_cardinality('p','b','c','cardinality_exists')})",
            ('matrix_lattice_identity_selector_exists','prime_field_enumeration_is_bijection'),
            _intro('p') + (f"have he : exists b c. ({_enumeration('p','b','c','cardinality_enumeration')})",)
            + _call('matrix_lattice_identity_selector_exists','p') + ('cases he','cases he_witness','exists x','exists x1')
            + _call('prime_field_enumeration_is_bijection','p','x','x1') + ('exact he_witness_witness',),
            'Exactly p canonical elements are witnessed by an actual finite bijection, not an external model count.',
        ),
    )


def _trace_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    preserve = (f"forall i v. ({_lt('i','S n','trace_recode_bound')}) -> ({_at('b','c','i','v','trace_recode_old')}) -> "
                f"({_at('B','C','i','v','trace_recode_new')})")
    recode = _intro('p','b','c','B','C','n','r','htrace','hpreserve') + _parts('htrace',3)
    recode += ('split',) + _call('hpreserve','0','0') + ('exists n','simp','exact htrace_left','split')
    recode += _call('hpreserve','n','r') + ('exists 0','apply zero_add','exact htrace_right_left')
    recode += _intro('i','hi') + (f"have hs : exists u v. ({_and(_at('b','c','i','u','trace_recode_before'),_at('b','c','S i','v','trace_recode_after'),_add('p','u','1','v','trace_recode_add'))})",)
    recode += _call('htrace_right_right','i') + ('exact hi','cases hs','cases hs_witness') + _parts('hs_witness_witness',3)
    recode += ('exists x','exists x1','split') + _call('hpreserve','i','x') + _call('le_succ','S i','n') + ('exact hi','exact hs_witness_witness_left','split')
    recode += _call('hpreserve','S i','x1') + _call('succ_le_succ','S i','n') + ('exact hi','exact hs_witness_witness_right_left','exact hs_witness_witness_right_right')
    result = [spec(
        'prime_field_unit_trace_recode',
        f"forall p b c B C n r. ({_trace('p','b','c','n','r','trace_recode_source')}) -> ({preserve}) -> ({_trace('p','B','C','n','r','trace_recode_target')})",
        ('zero_add','le_succ','succ_le_succ'), recode,
        'A genuine recoding preserving every one of the n+1 trace entries preserves all actual unit-addition steps.',
    )]
    preserve = (f"forall i v. ({_lt('i','S n','trace_append_bound')}) -> ({_at('b','c','i','v','trace_append_old')}) -> "
                f"({_at('B','C','i','v','trace_append_new')})")
    append = _intro('p','b','c','n','r','s','htrace','hadd')
    append += (f"have he : exists B C. ({_at('B','C','S n','s','trace_append_last')}) /\\ ({preserve})",)
    append += _call('beta_prefix_extend','S n','b','c','s') + ('cases he','cases he_witness','cases he_witness_witness')
    append += (f"have ht : {_trace('p','x','x1','n','r','trace_append_recoded')}",)
    append += _call('prime_field_unit_trace_recode','p','b','c','x','x1','n','r') + ('exact htrace','exact he_witness_witness_right')
    append += _parts('ht',3) + ('exists x','exists x1','split','exact ht_left','split','exact he_witness_witness_left')
    append += _intro('i','hi') + (f"have hcases : i = n \\/ ({_lt('i','n','trace_append_cases')})",)
    append += _call('finite_lt_succ_eq_or_lt','n','i') + ('exact hi','cases hcases')
    append += _rewrite_all('hcases_left',_and(_at('x','x1','i','u','trace_count_before'),_at('x','x1','S i','v','trace_count_after'),_add('p','u','1','v','trace_count_add')),'i')
    append += ('exists r','exists s','split','exact ht_right_left','split','exact he_witness_witness_left','exact hadd')
    append += _call('ht_right_right','i') + ('exact hcases_right',)
    result.append(spec(
        'prime_field_unit_trace_successor',
        f"forall p b c n r s. ({_trace('p','b','c','n','r','trace_successor_source')}) -> ({_add('p','r','1','s','trace_successor_add')}) -> exists B C. ({_trace('p','B','C','S n','s','trace_successor_result')})",
        ('beta_prefix_extend','prime_field_unit_trace_recode','finite_lt_succ_eq_or_lt'), append,
        'Append the genuinely computed next unit sum to an actual finite beta history.',
    ))
    exists = _intro('p','n') + ('induction n','intro hp','exists 0','exists 0','exists 0','split','split','exists 0','norm_num','exists 0','norm_num',
                              'split','split','exists 0','norm_num','exists 0','norm_num')
    exists += _intro('i','hi') + ('exfalso',) + _call('lt_not_le','i','0') + ('exact hi',) + _call('zero_le','i')
    exists += ('intro hp',f"have ht : exists b c r. ({_trace('p','b','c','n','r','trace_exists_previous')})",'apply IH','exact hp','cases ht','cases ht_witness','cases ht_witness_witness')
    exists += (f"have hr : {_lt('x2','p','trace_exists_rbound')}",)
    # n may be zero, so use the already proved residue bridge below rather than
    # assuming every trace contains a last step.  The simultaneous bound is
    # isolated in its own induction theorem earlier in the returned inventory.
    exists += _call('prime_field_unit_trace_result_bounded','p','x','x1','n','x2') + ('exact hp','exact ht_witness_witness_witness')
    exists += (f"have hs : exists s. ({_add('p','x2','1','s','trace_exists_next')})",)
    exists += _call('prime_field_add_exists','p','x2','1') + ('exact hp','exact hr') + _call('prime_two_le','p') + ('exact hp','cases hs',)
    exists += (f"have hnew : exists B C. ({_trace('p','B','C','S n','x3','trace_exists_successor')})",)
    exists += _call('prime_field_unit_trace_successor','p','x','x1','n','x2','x3') + ('exact ht_witness_witness_witness','exact hs_witness','cases hnew','cases hnew_witness','exists x4','exists x5','exists x3','exact hnew_witness_witness')
    # The residue bridge, below, is independent of existence and is placed
    # before this constructor; no circular premise or supplied endpoint occurs.
    result.append(spec(
        'prime_field_unit_trace_exists',
        f"forall p n. ({_prime('p','trace_exists_domain')}) -> exists b c r. ({_trace('p','b','c','n','r','trace_exists_result')})",
        ('lt_not_le','zero_le','prime_field_unit_trace_result_bounded','prime_field_add_exists','prime_two_le','prime_field_unit_trace_successor'),
        exists, 'Construct an actual history of n additions of one for every natural n, including the empty history.',
    ))
    return tuple(result)


def _residue_bridge_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body = _intro('p','n') + ('induction n',) + _intro('b','c','r','hp','htrace') + _parts('htrace',3)
    body += ('have heq : r = 0',) + _call('beta_at_unique','b','c','0','r','0') + ('exact htrace_right_left','exact htrace_left',)
    body += _rewrite_all('heq',_residue('p','0','r','trace_zero_transport'),'r')
    body += _call('prime_field_residue_reflexive','p','0') + _call('prime_field_zero_below_prime','p') + ('exact hp',)
    body += _intro('b','c','r','hp','htrace') + _parts('htrace',3)
    last = _and(_at('b','c','n','u','trace_bridge_last_before'),_at('b','c','S n','v','trace_bridge_last_after'),_add('p','u','1','v','trace_bridge_last_add'))
    body += (f"have hs : exists u v. ({last})",) + _call('htrace_right_right','n') + ('exists 0','apply zero_add','cases hs','cases hs_witness') + _parts('hs_witness_witness',3)
    body += ('have heq : x1 = r',) + _call('beta_at_unique','b','c','S n','x1','r') + ('exact hs_witness_witness_right_left','exact htrace_right_left')
    body += (f"have hprev : {_trace('p','b','c','n','x','trace_bridge_previous')}", 'split','exact htrace_left','split','exact hs_witness_witness_left')
    body += _intro('i','hi') + _call('htrace_right_right','i') + _call('le_succ','S i','n') + ('exact hi',)
    body += (f"have hres : {_residue('p','n','x','trace_bridge_old_residue')}",) + _call('IH','b','c','x') + ('exact hp','exact hprev',)
    body += (f"have hsum : {_residue('p','n+1','x1','trace_bridge_sum_residue')}",)
    body += _call('prime_field_residue_add','p','n','1','x','1','x1') + ('exact hres',)
    body += _call('prime_field_residue_reflexive','p','1') + _call('prime_two_le','p') + ('exact hp','exact hs_witness_witness_right_right')
    body += _rewrite_all('heq',_residue('p','n+1','x1','trace_bridge_result_transport'),'x1','hsum')
    body += _call('prime_field_residue_input_equal','p','S n','n+1','r') + ('simp','exact hsum',)
    bridge = spec(
        'prime_field_unit_trace_residue',
        f"forall p n b c r. ({_prime('p','trace_bridge_domain')}) -> ({_trace('p','b','c','n','r','trace_bridge_source')}) -> ({_residue('p','n','r','trace_bridge_result')})",
        ('beta_at_unique','prime_field_residue_reflexive','prime_field_zero_below_prime','zero_add','le_succ','prime_field_residue_add','prime_two_le','prime_field_residue_input_equal'),
        body,
        'Ordinary induction proves that an actual n-step addition-of-one history has canonical residue n; the relation does not assume this invariant.',
    )
    bounded = spec(
        'prime_field_unit_trace_result_bounded',
        f"forall p b c n r. ({_prime('p','trace_bounded_domain')}) -> ({_trace('p','b','c','n','r','trace_bounded_source')}) -> ({_lt('r','p','trace_bounded_result')})",
        ('prime_field_unit_trace_residue',),
        _intro('p','b','c','n','r','hp','ht') + (f"have hr : {_residue('p','n','r','trace_bounded_residue')}",)
        + _call('prime_field_unit_trace_residue','p','n','b','c','r') + ('exact hp','exact ht','cases hr','exact hr_left'),
        'Every trace endpoint is a canonical representative, including the empty-history endpoint.',
    )
    return (bridge,bounded)


def _completion_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'prime_field_unit_multiple_residue',
            f"forall p n r. ({_prime('p','multiple_residue_domain')}) -> ({_multiple('p','n','r','multiple_residue_source')}) -> ({_residue('p','n','r','multiple_residue_result')})",
            ('prime_field_unit_trace_residue',),
            _intro('p','n','r','hp','hm') + ('cases hm','cases hm_witness')
            + _call('prime_field_unit_trace_residue','p','n','x','x1','r') + ('exact hp','exact hm_witness_witness'),
            'An actual repeated sum of n ones has canonical residue n.',
        ),
        spec(
            'prime_field_unit_multiple_from_residue',
            f"forall p n r. ({_prime('p','multiple_construct_domain')}) -> ({_residue('p','n','r','multiple_construct_residue')}) -> ({_multiple('p','n','r','multiple_construct_result')})",
            ('prime_field_unit_trace_exists','prime_field_unit_trace_residue','binary_canonical_residue_functional'),
            _intro('p','n','r','hp','hr') + (f"have ht : exists b c s. ({_trace('p','b','c','n','s','multiple_construct_trace')})",)
            + _call('prime_field_unit_trace_exists','p','n') + ('exact hp','cases ht','cases ht_witness','cases ht_witness_witness')
            + (f"have hs : {_residue('p','n','x2','multiple_construct_computed')}",)
            + _call('prime_field_unit_trace_residue','p','n','x','x1','x2') + ('exact hp','exact ht_witness_witness_witness','have heq : x2 = r')
            + _call('binary_canonical_residue_functional','p','n','x2','r') + ('exact hs','exact hr','exists x','exists x1')
            + _rewrite_all('heq',_trace('p','x','x1','n','x2','multiple_construct_transport'),'x2','ht_witness_witness_witness')
            + ('exact ht_witness_witness_witness',),
            'Construct a genuine repeated-addition history ending at any supplied canonical residue; the trace invariant is proved, not assumed.',
        ),
        spec(
            'prime_field_unit_multiple_functional',
            f"forall p n r s. ({_prime('p','multiple_unique_domain')}) -> ({_multiple('p','n','r','multiple_unique_first')}) -> ({_multiple('p','n','s','multiple_unique_second')}) -> r = s",
            ('prime_field_unit_multiple_residue','binary_canonical_residue_functional'),
            _intro('p','n','r','s','hp','hr','hs') + _call('binary_canonical_residue_functional','p','n','r','s')
            + _call('prime_field_unit_multiple_residue','p','n','r') + ('exact hp','exact hr')
            + _call('prime_field_unit_multiple_residue','p','n','s') + ('exact hp','exact hs'),
            'Any two actual histories of the same number of additions of one have identical endpoints.',
        ),
        spec(
            'prime_field_unit_multiple_exists_unique',
            f"forall p n. ({_prime('p','multiple_total_domain')}) -> exists r. ({_multiple('p','n','r','multiple_total_chosen')}) /\\ forall s. ({_multiple('p','n','s','multiple_total_other')}) -> s = r",
            ('prime_field_unit_trace_exists','prime_field_unit_multiple_functional'),
            _intro('p','n','hp') + (f"have ht : exists b c r. ({_trace('p','b','c','n','r','multiple_total_trace')})",)
            + _call('prime_field_unit_trace_exists','p','n') + ('exact hp','cases ht','cases ht_witness','cases ht_witness_witness',
               f"have hm : {_multiple('p','n','x2','multiple_total_result')}",'exists x','exists x1','exact ht_witness_witness_witness','exists x2','split','exact hm')
            + _intro('s','hs') + _call('prime_field_unit_multiple_functional','p','n','s','x2') + ('exact hp','exact hs','exact hm'),
            'Repeated addition is a total functional computation on every natural length, with an actual beta execution history.',
        ),
        spec(
            'prime_field_characteristic_exact',
            f"forall p. ({_prime('p','characteristic_domain')}) -> ({_characteristic('p','characteristic_exact')})",
            ('prime_field_unit_multiple_from_residue','prime_field_residue_modulus_zero','prime_field_unit_multiple_residue','prime_field_positive_below_modulus_not_zero'),
            _intro('p','hp') + ('split',) + _call('prime_field_unit_multiple_from_residue','p','p','0') + ('exact hp',)
            + _call('prime_field_residue_modulus_zero','p') + ('exact hp',)
            + _intro('n','hn','hpositive','hm') + _call('prime_field_positive_below_modulus_not_zero','p','n') + ('exact hn','exact hpositive')
            + _call('prime_field_unit_multiple_residue','p','n','0') + ('exact hp','exact hm'),
            'The first positive number of additions of the actual identity one that returns zero is exactly p, including p=2.',
        ),
        spec(
            'prime_field_of_prime_order_exists',
            f"forall p. ({_prime('p','finite_structure_domain')}) -> exists ab ac mb mc nb nc ib ic eb ec. ({_structure('p','ab','ac','mb','mc','nb','nc','ib','ic','eb','ec','finite_structure')})",
            ('prime_field_operation_tables_exists','prime_field_cardinality_exists','prime_field_arithmetic_laws','prime_field_characteristic_exact'),
            _intro('p','hp') + (f"have ht : exists ab ac mb mc nb nc ib ic. ({_tables('p','ab','ac','mb','mc','nb','nc','ib','ic','finite_structure_tables')})",)
            + _call('prime_field_operation_tables_exists','p') + ('exact hp',)
            + tuple('cases ht'+'_witness'*i for i in range(8))
            + (f"have hc : exists eb ec. ({_cardinality('p','eb','ec','finite_structure_cardinality')})",)
            + _call('prime_field_cardinality_exists','p') + ('cases hc','cases hc_witness')
            + tuple('exists x' + (str(i) if i else '') for i in range(10))
            + ('split','exact ht'+'_witness'*8,'split','exact hc_witness_witness','split')
            + _call('prime_field_arithmetic_laws','p') + ('exact hp',)
            + _call('prime_field_characteristic_exact','p') + ('exact hp',),
            'For every prime construct all finite arithmetic tables, an exact p-element bijection, every field law, and characteristic p. This is the k=1 case only, not arbitrary prime-power extension fields.',
        ),
    )


def make_prime_field_finiteness_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    trace_rows = _trace_rows(spec)
    return _cardinality_rows(spec) + trace_rows[:2] + _residue_bridge_rows(spec) + trace_rows[2:] + _completion_rows(spec)


__all__ = [
    'prime_field_enumeration_relation','prime_field_cardinality_relation','prime_field_unit_steps_relation',
    'prime_field_unit_trace_relation','prime_field_unit_multiple_relation','prime_field_characteristic_relation',
    'prime_field_finite_structure_relation','make_prime_field_finiteness_candidate_theorems',
]
