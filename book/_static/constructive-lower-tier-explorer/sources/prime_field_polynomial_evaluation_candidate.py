"""Actual modular Horner executions over canonical prime-field coefficients.

The coefficient order is the existing T12 highest-degree-first order:
``h[0]=0`` and ``h[i+1]=h[i]*x+a[i]``.  A length is not a degree.
The new graphs only describe decoded execution steps with actual FpMul and
FpAdd witnesses.  Natural-Horner/residue invariance is a theorem, not a field
of the execution relation.  All proofs remain ordinary first-order HA.
"""

from __future__ import annotations

from typing import Any, Callable

from .polynomial_horner_candidate import (
    _horner_relation_terms, _horner_trace_body,
)
from .prime_field_arithmetic_candidate import (
    _add as _field_add, _mul as _field_mul,
    _and, _call, _intro, _lt, _part, _parts, _prime, _public, _residue,
)
from .prime_field_polynomial_candidate import _at, _coeff, _equal, _normalization, _repeat
from .prime_field_tables_candidate import _rewrite_all


def _step(p: str, b: str, c: str, x: str, u: str, v: str, i: str, tag: str) -> str:
    a, h, j, k = (f'pfh_{role}_{tag}' for role in ('coefficient','before','after','product'))
    return f'exists {a} {h} {j} {k}. ' + _and(
        _at(b,c,i,a,tag+'coefficient'), _at(u,v,i,h,tag+'before'),
        _at(u,v,f'S ({i})',j,tag+'after'),
        _field_mul(p,h,x,k,tag+'multiply'), _field_add(p,k,a,j,tag+'add'),
    )


def _steps(p: str, b: str, c: str, x: str, length: str, u: str, v: str, tag: str) -> str:
    i = 'pfh_index_' + tag
    return f'forall {i}. ({_lt(i,length,tag+"index")}) -> ({_step(p,b,c,x,u,v,i,tag+"step")})'


def _trace(p: str, b: str, c: str, x: str, length: str, r: str, u: str, v: str, tag: str) -> str:
    return _and(
        _lt(x,p,tag+'base'), _at(u,v,'0','0',tag+'initial'),
        _at(u,v,length,r,tag+'terminal'), _steps(p,b,c,x,length,u,v,tag+'steps'),
    )


def _eval(p: str, b: str, c: str, x: str, length: str, r: str, tag: str) -> str:
    u, v = 'pfh_trace_code_'+tag, 'pfh_trace_scale_'+tag
    return f'exists {u} {v}. ({_trace(p,b,c,x,length,r,u,v,tag+"trace")})'


def _natural(b: str, c: str, x: str, length: str, n: str, tag: str) -> str:
    return _horner_relation_terms(b,c,x,length,n,tag='pfh_'+tag)


def _natural_trace(b: str, c: str, x: str, length: str, n: str, u: str, v: str, tag: str) -> str:
    return _horner_trace_body(b,c,x,length,n,u,v,tag='pfh_'+tag)


def prime_field_polynomial_horner_step_relation(p: str, b: str, c: str, x: str, u: str, v: str, i: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(_step,(p,b,c,x,u,v,i),tag=tag,variables=variables)


def prime_field_polynomial_horner_steps_relation(p: str, b: str, c: str, x: str, length: str, u: str, v: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(_steps,(p,b,c,x,length,u,v),tag=tag,variables=variables)


def prime_field_polynomial_horner_trace_relation(p: str, b: str, c: str, x: str, length: str, r: str, u: str, v: str, *, tag: str, variables: tuple[str, ...]) -> str:
    return _public(_trace,(p,b,c,x,length,r,u,v),tag=tag,variables=variables)


def prime_field_polynomial_evaluation_relation(p: str, b: str, c: str, x: str, length: str, r: str, *, tag: str, variables: tuple[str, ...]) -> str:
    """An actual finite modular execution, with canonical x even at length zero."""
    return _public(_eval,(p,b,c,x,length,r),tag=tag,variables=variables)


def _construction_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    scalar = spec(
        'prime_field_polynomial_horner_canonical_step',
        f"forall p n t a r s. ({_prime('p','step_prime')}) -> ({_lt('t','p','step_base')}) -> ({_lt('a','p','step_coefficient')}) -> ({_residue('p','n','r','step_previous')}) -> ({_residue('p','n*t+a','s','step_next')}) -> exists k. "
        + _and(_field_mul('p','r','t','k','step_product'),_field_add('p','k','a','s','step_sum')),
        ('prime_field_multiply_exists','prime_field_add_exists','prime_field_residue_multiply','prime_field_residue_add','prime_field_residue_reflexive','binary_canonical_residue_functional'),
        _intro('p','n','t','a','r','s','hp','ht','ha','hr','hs')
        + (f"have hrcopy : {_residue('p','n','r','step_previous_copy')}",'exact hr','cases hrcopy')
        + (f"have hm : exists k. ({_field_mul('p','r','t','k','step_chosen_product')})",)
        + _call('prime_field_multiply_exists','p','r','t') + ('exact hp','exact hrcopy_left','exact ht','cases hm')
        + (f"have hmcopy : {_field_mul('p','r','t','x','step_product_copy')}",'exact hm_witness') + _parts('hmcopy',4)
        + (f"have hadd : exists z. ({_field_add('p','x','a','z','step_chosen_sum')})",)
        + _call('prime_field_add_exists','p','x','a') + ('exact hp','exact hmcopy_right_right_left','exact ha','cases hadd')
        + (f"have hmulres : {_residue('p','n*t','x','step_product_residue')}",)
        + _call('prime_field_residue_multiply','p','n','t','r','t','x') + ('exact hr',)
        + _call('prime_field_residue_reflexive','p','t') + ('exact ht','exact hm_witness')
        + (f"have hsumres : {_residue('p','n*t+a','x1','step_sum_residue')}",)
        + _call('prime_field_residue_add','p','n*t','a','x','a','x1') + ('exact hmulres',)
        + _call('prime_field_residue_reflexive','p','a') + ('exact ha','exact hadd_witness','have heq : x1=s')
        + _call('binary_canonical_residue_functional','p','n*t+a','x1','s') + ('exact hsumres','exact hs','exists x','split','exact hm_witness')
        + _rewrite_all('heq',_field_add('p','x','a','x1','step_transport'),'x1','hadd_witness') + ('exact hadd_witness',),
        'Construct an actual canonical multiply-then-add step from proved residues of the corresponding natural step.',
    )
    body = _intro('p','b','c','t','l','n','u','v','U','V','hp','hc','ht','hn','hred') + _parts('hn',3)
    body += (f"have he : exists r. ({_at('U','V','l','r','trace_construct_terminal')})",) + _call('beta_at_exists','U','V','l') + ('cases he',)
    body += (f"have hr : {_residue('p','n','x','trace_construct_result')}",)
    body += _call('prime_field_polynomial_normalization_entry','p','u','v','U','V','S l','l','n','x')
    body += ('exact hred','exists 0','apply zero_add','exact hn_right_left','exact he_witness')
    body += (f"have hzero : {_at('U','V','0','0','trace_construct_zero')}",)
    body += (f"have hz : exists z. ({_at('U','V','0','z','trace_construct_first')})",) + _call('beta_at_exists','U','V','0') + ('cases hz',)
    body += (f"have hzres : {_residue('p','0','x1','trace_construct_first_residue')}",)
    body += _call('prime_field_polynomial_normalization_entry','p','u','v','U','V','S l','0','0','x1')
    body += ('exact hred','exists l','simp','exact hn_left','exact hz_witness','have hzeq : x1=0')
    body += _call('prime_field_residue_bounded_value','p','0','x1') + _call('prime_field_zero_below_prime','p') + ('exact hp','exact hzres')
    body += _rewrite_all('hzeq',_at('U','V','0','x1','trace_construct_zero_transport'),'x1','hz_witness') + ('exact hz_witness',)
    body += ('exists x','split','split','exact ht','split','exact hzero','split','exact he_witness') + _intro('i','hi')
    natural_step = _and(_at('b','c','i','a','trace_construct_coefficient'),_at('u','v','i','h','trace_construct_before'),_at('u','v','S i','j','trace_construct_after'),'j=h*t+a')
    body += (f'have hs : exists a h j. {natural_step}',) + _call('hn_right_right','i') + ('exact hi','cases hs','cases hs_witness','cases hs_witness_witness') + _parts('hs_witness_witness_witness',4)
    body += (f"have hb : exists r. ({_at('U','V','i','r','trace_construct_canonical_before')})",) + _call('beta_at_exists','U','V','i') + ('cases hb',)
    body += (f"have ha : exists r. ({_at('U','V','S i','r','trace_construct_canonical_after')})",) + _call('beta_at_exists','U','V','S i') + ('cases ha',)
    body += (f"have hbefore : {_residue('p','x2','x4','trace_construct_before_residue')}",)
    body += _call('prime_field_polynomial_normalization_entry','p','u','v','U','V','S l','i','x2','x4')
    body += ('exact hred',) + _call('le_succ','S i','l') + ('exact hi','exact hs_witness_witness_witness_right_left','exact hb_witness')
    body += (f"have hafter : {_residue('p','x2*t+x1','x5','trace_construct_after_residue')}",)
    body += _call('prime_field_residue_input_equal','p','x2*t+x1','x3','x5') + ('symm','exact hs_witness_witness_witness_right_right_right')
    body += _call('prime_field_polynomial_normalization_entry','p','u','v','U','V','S l','S i','x3','x5')
    body += ('exact hred',) + _call('succ_le_succ','S i','l') + ('exact hi','exact hs_witness_witness_witness_right_right_left','exact ha_witness')
    body += (f"have hop : exists k. {_and(_field_mul('p','x4','t','k','trace_construct_multiply'),_field_add('p','k','x1','x5','trace_construct_add'))}",)
    body += _call('prime_field_polynomial_horner_canonical_step','p','x2','t','x1','x4','x5') + ('exact hp','exact ht')
    body += _call('matrix_rank_bounded_prefix_value','b','c','l','p','i','x1') + ('exact hc','exact hi','exact hs_witness_witness_witness_left','exact hbefore','exact hafter','cases hop','cases hop_witness')
    body += ('exists x1','exists x4','exists x5','exists x6','split','exact hs_witness_witness_witness_left','split','exact hb_witness','split','exact ha_witness','split','exact hop_witness_left','exact hop_witness_right','exact hr')
    trace = spec(
        'prime_field_polynomial_horner_trace_from_normalization',
        f"forall p b c t l n u v U V. ({_prime('p','trace_construct_prime')}) -> ({_coeff('p','b','c','l','trace_construct_coefficients')}) -> ({_lt('t','p','trace_construct_base')}) -> "
        f"({_natural_trace('b','c','t','l','n','u','v','trace_construct_natural')}) -> ({_normalization('p','u','v','U','V','S l','trace_construct_normalization')}) -> exists r. "
        + _and(_trace('p','b','c','t','l','r','U','V','trace_construct_execution'),_residue('p','n','r','trace_construct_final_residue')),
        ('beta_at_exists','prime_field_polynomial_normalization_entry','zero_add','prime_field_residue_bounded_value','prime_field_zero_below_prime','le_succ','succ_le_succ','prime_field_residue_input_equal','prime_field_polynomial_horner_canonical_step','matrix_rank_bounded_prefix_value'),
        body,
        'Reducing all l+1 states of a genuine natural Horner trace constructs a genuine canonical execution, including its zero initial state.',
    )
    exists = spec(
        'prime_field_polynomial_horner_exists',
        f"forall p b c t l. ({_prime('p','exists_prime')}) -> ({_coeff('p','b','c','l','exists_coefficients')}) -> ({_lt('t','p','exists_base')}) -> exists r. ({_eval('p','b','c','t','l','r','exists_execution')})",
        ('beta_horner_eval_exists','prime_field_polynomial_normalization_exists','prime_nonzero','prime_field_polynomial_horner_trace_from_normalization'),
        _intro('p','b','c','t','l','hp','hc','ht')
        + (f"have hn : exists n. ({_natural('b','c','t','l','n','exists_natural')})",) + _call('beta_horner_eval_exists','b','c','t','l')
        + ('cases hn','cases hn_witness','cases hn_witness_witness')
        + (f"have hr : exists U V. ({_normalization('p','x1','x2','U','V','S l','exists_normalization')})",)
        + _call('prime_field_polynomial_normalization_exists','p','x1','x2','S l') + ('intro hz',) + _call('prime_nonzero','p')
        + ('exact hp','exact hz','cases hr','cases hr_witness')
        + (f"have he : exists r. {_and(_trace('p','b','c','t','l','r','x3','x4','exists_chosen_trace'),_residue('p','x','r','exists_chosen_residue'))}",)
        + _call('prime_field_polynomial_horner_trace_from_normalization','p','b','c','t','l','x','x1','x2','x3','x4')
        + ('exact hp','exact hc','exact ht','exact hn_witness_witness_witness','exact hr_witness_witness','cases he','cases he_witness','exists x5','exists x3','exists x4','exact he_witness_left'),
        'Every canonical coefficient prefix and canonical base have an actual finite modular Horner history; no trace or norm invariant is supplied.',
    )
    return scalar, trace, exists


def _structural_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    bounds = _intro('p','b','c','t','l','r','h') + ('cases h','cases h_witness') + _parts('h_witness_witness',4)
    bounds += ('split','exact h_witness_witness_left') + _intro('i','hi')
    bounds += (f"have hs : {_step('p','b','c','t','x','x1','i','bounds_step')}",) + _call('h_witness_witness_right_right_right','i') + ('exact hi',)
    bounds += tuple('cases hs'+'_witness'*i for i in range(4)) + _parts('hs_witness_witness_witness_witness',5)
    bounds += _parts('hs_witness_witness_witness_witness_right_right_right_right',3)
    bounds += ('exists x2','split','exact hs_witness_witness_witness_witness_left','exact hs_witness_witness_witness_witness_right_right_right_right_right_left')
    successor = _intro('p','b','c','t','l','r','h') + ('cases h','cases h_witness') + _parts('h_witness_witness',4)
    successor += (f"have hs : {_step('p','b','c','t','x','x1','l','successor_step')}",) + _call('h_witness_witness_right_right_right','l') + ('exists 0','apply zero_add',)
    successor += tuple('cases hs'+'_witness'*i for i in range(4)) + _parts('hs_witness_witness_witness_witness',5)
    successor += ('have heq : x4=r',) + _call('beta_at_unique','x','x1','S l','x4','r') + ('exact hs_witness_witness_witness_witness_right_right_left','exact h_witness_witness_right_right_left')
    successor += _rewrite_all('heq',_field_add('p','x5','x2','x4','successor_result_transport'),'x4','hs_witness_witness_witness_witness_right_right_right_right')
    successor += ('exists x2','exists x3','exists x5','split','exact hs_witness_witness_witness_witness_left','split','exists x','exists x1','split','exact h_witness_witness_left','split','exact h_witness_witness_right_left','split','exact hs_witness_witness_witness_witness_right_left')
    successor += _intro('i','hi') + _call('h_witness_witness_right_right_right','i') + _call('le_succ','S i','l') + ('exact hi','split','exact hs_witness_witness_witness_witness_right_right_right_left','exact hs_witness_witness_witness_witness_right_right_right_right')
    transport = _intro('p','b','c','B','C','t','l','r','heq','h') + ('cases h','cases h_witness') + _parts('h_witness_witness',4)
    transport += ('exists x','exists x1','split','exact h_witness_witness_left','split','exact h_witness_witness_right_left','split','exact h_witness_witness_right_right_left') + _intro('i','hi')
    transport += (f"have hs : {_step('p','b','c','t','x','x1','i','transport_step')}",) + _call('h_witness_witness_right_right_right','i') + ('exact hi',)
    transport += tuple('cases hs'+'_witness'*i for i in range(4)) + _parts('hs_witness_witness_witness_witness',5)
    transport += ('exists x2','exists x3','exists x4','exists x5','split') + _call('heq','i','x2') + ('exact hi','exact hs_witness_witness_witness_witness_left','split','exact hs_witness_witness_witness_witness_right_left','split','exact hs_witness_witness_witness_witness_right_right_left','split','exact hs_witness_witness_witness_witness_right_right_right_left','exact hs_witness_witness_witness_witness_right_right_right_right')
    return (
        spec(
            'prime_field_polynomial_horner_input_bounds',
            f"forall p b c t l r. ({_eval('p','b','c','t','l','r','input_bounds_execution')}) -> " + _and(_lt('t','p','input_bounds_base'),_coeff('p','b','c','l','input_bounds_coefficients')),
            (), bounds,
            'The actual execution graph entails canonical input coefficients and base; no separate input-bound certificates are hidden in its steps.',
        ),
        spec(
            'prime_field_polynomial_horner_empty',
            f"forall p b c t r. ({_eval('p','b','c','t','0','r','empty_execution')}) -> r=0",
            ('beta_at_unique',),
            _intro('p','b','c','t','r','h') + ('cases h','cases h_witness') + _parts('h_witness_witness',4)
            + _call('beta_at_unique','x','x1','0','r','0') + ('exact h_witness_witness_right_right_left','exact h_witness_witness_right_left'),
            'The empty polynomial execution returns zero by its actual initial and terminal beta entries.',
        ),
        spec(
            'prime_field_polynomial_horner_successor_decompose',
            f"forall p b c t l r. ({_eval('p','b','c','t','S l','r','successor_execution')}) -> exists a h k. "
            + _and(_at('b','c','l','a','successor_coefficient'),_eval('p','b','c','t','l','h','successor_prefix'),_field_mul('p','h','t','k','successor_multiply'),_field_add('p','k','a','r','successor_add')),
            ('zero_add','beta_at_unique','le_succ'), successor,
            'An actual successor execution decomposes into its actual prefix and final multiply-then-add step in highest-degree-first order.',
        ),
        spec(
            'prime_field_polynomial_horner_transport',
            f"forall p b c B C t l r. ({_equal('b','c','B','C','l','transport_equal')}) -> ({_eval('p','b','c','t','l','r','transport_old')}) -> ({_eval('p','B','C','t','l','r','transport_new')})",
            (), transport,
            'Coefficient reencoding preserves the same real execution trace and result, without asserting equality of raw code numbers.',
        ),
    )


def _invariant_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('p','b','c','d','e','t','l') + ('induction l',) + _intro('n','r','hp','hred','hn','hr')
    body += ('have hnzero : n=0',) + _call('beta_horner_eval_empty','b','c','t','n') + ('exact hn','have hrzero : r=0')
    body += _call('prime_field_polynomial_horner_empty','p','d','e','t','r') + ('exact hr',)
    body += _rewrite_all('hnzero',_residue('p','n','r','invariant_empty_n'),'n')
    body += _rewrite_all('hrzero',_residue('p','0','r','invariant_empty_r'),'r')
    body += _call('prime_field_residue_reflexive','p','0') + _call('prime_field_zero_below_prime','p') + ('exact hp',)
    body += _intro('n','r','hp','hred','hn','hr')
    body += (f"have hns : exists a h. {_and(_at('b','c','l','a','invariant_natural_coefficient'),_natural('b','c','t','l','h','invariant_natural_prefix'),'n=h*t+a')}",)
    body += _call('beta_horner_eval_successor_decompose','b','c','t','l','n') + ('exact hn','cases hns','cases hns_witness') + _parts('hns_witness_witness',3)
    body += (f"have hrs : exists a h k. {_and(_at('d','e','l','a','invariant_canonical_coefficient'),_eval('p','d','e','t','l','h','invariant_canonical_prefix'),_field_mul('p','h','t','k','invariant_canonical_multiply'),_field_add('p','k','a','r','invariant_canonical_add'))}",)
    body += _call('prime_field_polynomial_horner_successor_decompose','p','d','e','t','l','r') + ('exact hr','cases hrs','cases hrs_witness','cases hrs_witness_witness') + _parts('hrs_witness_witness_witness',4)
    body += (f"have hcoefficient : {_residue('p','x','x2','invariant_coefficient_residue')}",)
    body += _call('prime_field_polynomial_normalization_entry','p','b','c','d','e','S l','l','x','x2')
    body += ('exact hred','exists 0','apply zero_add','exact hns_witness_witness_left','exact hrs_witness_witness_witness_left')
    body += (f"have hprevious : {_residue('p','x1','x3','invariant_previous_residue')}",)
    body += _call('IH','x1','x3') + ('exact hp',) + _intro('i','hi') + _call('hred','i') + _call('le_succ','S i','l')
    body += ('exact hi','exact hns_witness_witness_right_left','exact hrs_witness_witness_witness_right_left')
    body += (f"have hbounds : {_and(_lt('t','p','invariant_base_bound'),_coeff('p','d','e','l','invariant_coefficients'))}",)
    body += _call('prime_field_polynomial_horner_input_bounds','p','d','e','t','l','x3') + ('exact hrs_witness_witness_witness_right_left','cases hbounds')
    body += (f"have hproduct : {_residue('p','x1*t','x4','invariant_product_residue')}",)
    body += _call('prime_field_residue_multiply','p','x1','t','x3','t','x4') + ('exact hprevious',)
    body += _call('prime_field_residue_reflexive','p','t') + ('exact hbounds_left','exact hrs_witness_witness_witness_right_right_left')
    body += _call('prime_field_residue_input_equal','p','n','x1*t+x','r') + ('exact hns_witness_witness_right_right',)
    body += _call('prime_field_residue_add','p','x1*t','x','x4','x2','r') + ('exact hproduct','exact hcoefficient','exact hrs_witness_witness_witness_right_right_right')
    normalization = spec(
        'prime_field_polynomial_horner_normalization_residue',
        f"forall p b c d e t l n r. ({_prime('p','invariant_prime')}) -> ({_normalization('p','b','c','d','e','l','invariant_coefficients_reduced')}) -> ({_natural('b','c','t','l','n','invariant_natural')}) -> ({_eval('p','d','e','t','l','r','invariant_execution')}) -> ({_residue('p','n','r','invariant_result')})",
        ('beta_horner_eval_empty','prime_field_polynomial_horner_empty','prime_field_residue_reflexive','prime_field_zero_below_prime','beta_horner_eval_successor_decompose','prime_field_polynomial_horner_successor_decompose','prime_field_polynomial_normalization_entry','zero_add','le_succ','prime_field_polynomial_horner_input_bounds','prime_field_residue_multiply','prime_field_residue_input_equal','prime_field_residue_add'),
        body,
        'Ordinary induction proves the residue invariant against arbitrary natural coefficients and their actual coefficientwise reduction; the invariant is not part of the execution definition.',
    )
    residue = spec(
        'prime_field_polynomial_horner_residue',
        f"forall p b c t l n r. ({_prime('p','residue_prime')}) -> ({_natural('b','c','t','l','n','residue_natural')}) -> ({_eval('p','b','c','t','l','r','residue_execution')}) -> ({_residue('p','n','r','residue_result')})",
        ('prime_field_polynomial_horner_normalization_residue','prime_field_polynomial_normalization_reflexive','prime_field_polynomial_horner_input_bounds'),
        _intro('p','b','c','t','l','n','r','hp','hn','hr')
        + (f"have hbounds : {_and(_lt('t','p','residue_base_bound'),_coeff('p','b','c','l','residue_coefficients'))}",)
        + _call('prime_field_polynomial_horner_input_bounds','p','b','c','t','l','r') + ('exact hr','cases hbounds')
        + _call('prime_field_polynomial_horner_normalization_residue','p','b','c','b','c','t','l','n','r') + ('exact hp',)
        + _call('prime_field_polynomial_normalization_reflexive','p','b','c','l') + ('exact hbounds_right','exact hn','exact hr'),
        'Actual modular evaluation has exactly the canonical residue of the existing natural T12 Horner value.',
    )
    functional = spec(
        'prime_field_polynomial_horner_functional',
        f"forall p b c t l r s. ({_prime('p','functional_prime')}) -> ({_eval('p','b','c','t','l','r','functional_first')}) -> ({_eval('p','b','c','t','l','s','functional_second')}) -> r=s",
        ('beta_horner_eval_exists','prime_field_polynomial_horner_residue','binary_canonical_residue_functional'),
        _intro('p','b','c','t','l','r','s','hp','hr','hs')
        + (f"have hn : exists n. ({_natural('b','c','t','l','n','functional_natural')})",) + _call('beta_horner_eval_exists','b','c','t','l') + ('cases hn',)
        + _call('binary_canonical_residue_functional','p','x','r','s')
        + _call('prime_field_polynomial_horner_residue','p','b','c','t','l','x','r') + ('exact hp','exact hn_witness','exact hr')
        + _call('prime_field_polynomial_horner_residue','p','b','c','t','l','x','s') + ('exact hp','exact hn_witness','exact hs'),
        'Every actual modular execution of the same coefficient prefix and base has the same canonical result.',
    )
    unique = spec(
        'prime_field_polynomial_horner_exists_unique',
        f"forall p b c t l. ({_prime('p','unique_prime')}) -> ({_coeff('p','b','c','l','unique_coefficients')}) -> ({_lt('t','p','unique_base')}) -> exists r. ({_eval('p','b','c','t','l','r','unique_chosen')}) /\\ forall s. ({_eval('p','b','c','t','l','s','unique_other')}) -> s=r",
        ('prime_field_polynomial_horner_exists','prime_field_polynomial_horner_functional'),
        _intro('p','b','c','t','l','hp','hc','ht') + (f"have he : exists r. ({_eval('p','b','c','t','l','r','unique_execution')})",)
        + _call('prime_field_polynomial_horner_exists','p','b','c','t','l') + ('exact hp','exact hc','exact ht','cases he','exists x','split','exact he_witness')
        + _intro('s','hs') + _call('prime_field_polynomial_horner_functional','p','b','c','t','l','s','x') + ('exact hp','exact hs','exact he_witness'),
        'Constructive totality and uniqueness of genuine finite prime-field polynomial evaluation, including p=2 and length zero.',
    )
    return normalization, residue, functional, unique


def _recurrence_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    empty = spec(
        'prime_field_polynomial_horner_empty_construct',
        f"forall p b c t. ({_prime('p','empty_construct_prime')}) -> ({_lt('t','p','empty_construct_base')}) -> ({_eval('p','b','c','t','0','0','empty_construct_execution')})",
        ('prime_field_polynomial_horner_exists','matrix_rank_bounded_prefix_empty','prime_field_polynomial_horner_empty'),
        _intro('p','b','c','t','hp','ht') + (f"have he : exists r. ({_eval('p','b','c','t','0','r','empty_construct_chosen')})",)
        + _call('prime_field_polynomial_horner_exists','p','b','c','t','0') + ('exact hp',) + _call('matrix_rank_bounded_prefix_empty','b','c','p')
        + ('exact ht','cases he','have hz : x=0') + _call('prime_field_polynomial_horner_empty','p','b','c','t','x') + ('exact he_witness',)
        + _rewrite_all('hz',_eval('p','b','c','t','0','x','empty_construct_rewrite'),'x','he_witness') + ('exact he_witness',),
        'Construct an actual zero-result execution of every empty coefficient prefix, retaining the canonical base guard.',
    )
    body = _intro('p','b','c','t','l','a','h','k','r','hp','ha','hh','hm','hr')
    body += (f"have hbounds : {_and(_lt('t','p','successor_intro_base'),_coeff('p','b','c','l','successor_intro_prefix_bounds'))}",)
    body += _call('prime_field_polynomial_horner_input_bounds','p','b','c','t','l','h') + ('exact hh','cases hbounds')
    body += (f"have hrcopy : {_field_add('p','k','a','r','successor_intro_operation_copy')}",'exact hr') + _parts('hrcopy',3)
    body += (f"have hcoeff : {_coeff('p','b','c','S l','successor_intro_coefficients')}",)
    body += _call('matrix_rank_bounded_prefix_extend','b','c','l','p','a') + ('exact hbounds_right','exact ha','exact hrcopy_right_left')
    body += (f"have he : exists s. ({_eval('p','b','c','t','S l','s','successor_intro_candidate')})",)
    body += _call('prime_field_polynomial_horner_exists','p','b','c','t','S l') + ('exact hp','exact hcoeff','exact hbounds_left','cases he')
    body += (f"have hs : exists a h k. {_and(_at('b','c','l','a','successor_intro_candidate_coefficient'),_eval('p','b','c','t','l','h','successor_intro_candidate_prefix'),_field_mul('p','h','t','k','successor_intro_candidate_multiply'),_field_add('p','k','a','x','successor_intro_candidate_add'))}",)
    body += _call('prime_field_polynomial_horner_successor_decompose','p','b','c','t','l','x') + ('exact he_witness','cases hs','cases hs_witness','cases hs_witness_witness') + _parts('hs_witness_witness_witness',4)
    body += ('have hae : x1=a',) + _call('beta_at_unique','b','c','l','x1','a') + ('exact hs_witness_witness_witness_left','exact ha','have hhe : x2=h')
    body += _call('prime_field_polynomial_horner_functional','p','b','c','t','l','x2','h') + ('exact hp','exact hs_witness_witness_witness_right_left','exact hh')
    body += _rewrite_all('hhe',_field_mul('p','x2','t','x3','successor_intro_multiply_rewrite'),'x2','hs_witness_witness_witness_right_right_left')
    body += ('have hke : x3=k',) + _call('prime_field_multiply_functional','p','h','t','x3','k') + ('exact hs_witness_witness_witness_right_right_left','exact hm')
    body += _rewrite_all('hae',_field_add('p','x3','x1','x','successor_intro_coefficient_rewrite'),'x1','hs_witness_witness_witness_right_right_right')
    body += _rewrite_all('hke',_field_add('p','x3','a','x','successor_intro_product_rewrite'),'x3','hs_witness_witness_witness_right_right_right')
    body += ('have hre : x=r',) + _call('prime_field_add_functional','p','k','a','x','r') + ('exact hs_witness_witness_witness_right_right_right','exact hr')
    body += _rewrite_all('hre',_eval('p','b','c','t','S l','x','successor_intro_result_rewrite'),'x','he_witness') + ('exact he_witness',)
    successor = spec(
        'prime_field_polynomial_horner_successor_construct',
        f"forall p b c t l a h k r. ({_prime('p','successor_intro_prime')}) -> ({_at('b','c','l','a','successor_intro_coefficient')}) -> ({_eval('p','b','c','t','l','h','successor_intro_prefix')}) -> ({_field_mul('p','h','t','k','successor_intro_multiply')}) -> ({_field_add('p','k','a','r','successor_intro_add')}) -> ({_eval('p','b','c','t','S l','r','successor_intro_execution')})",
        ('prime_field_polynomial_horner_input_bounds','matrix_rank_bounded_prefix_extend','prime_field_polynomial_horner_exists','prime_field_polynomial_horner_successor_decompose','beta_at_unique','prime_field_polynomial_horner_functional','prime_field_multiply_functional','prime_field_add_functional'),
        body,
        'Every actual canonical last multiply/add step extends an actual prefix to a full execution; the required coefficient bounds are derived, not assumed.',
    )
    constant = spec(
        'prime_field_polynomial_horner_constant',
        f"forall p b c t a. ({_prime('p','constant_prime')}) -> ({_lt('t','p','constant_base')}) -> ({_lt('a','p','constant_value')}) -> ({_at('b','c','0','a','constant_coefficient')}) -> ({_eval('p','b','c','t','1','a','constant_execution')})",
        ('prime_field_polynomial_horner_successor_construct','prime_field_polynomial_horner_empty_construct','prime_field_multiply_zero_left','prime_field_add_zero_left'),
        _intro('p','b','c','t','a','hp','ht','ha','hentry') + _call('prime_field_polynomial_horner_successor_construct','p','b','c','t','0','a','0','0','a')
        + ('exact hp','exact hentry') + _call('prime_field_polynomial_horner_empty_construct','p','b','c','t') + ('exact hp','exact ht')
        + _call('prime_field_multiply_zero_left','p','t') + ('exact hp','exact ht') + _call('prime_field_add_zero_left','p','a') + ('exact hp','exact ha'),
        'A one-coefficient prefix evaluates to that actual constant, including zero and characteristic two.',
    )
    zero_body = _intro('p','b','c','t','l') + ('induction l',) + _intro('hp','ht','hz')
    zero_body += _call('prime_field_polynomial_horner_empty_construct','p','b','c','t') + ('exact hp','exact ht')
    zero_body += _intro('hp','ht','hz') + _call('prime_field_polynomial_horner_successor_construct','p','b','c','t','l','0','0','0','0')
    zero_body += ('exact hp',) + _call('hz','l') + ('exists 0','apply zero_add')
    zero_body += _call('IH') + ('exact hp','exact ht') + _intro('i','hi') + _call('hz','i') + _call('le_succ','S i','l') + ('exact hi',)
    zero_body += _call('prime_field_multiply_zero_left','p','t') + ('exact hp','exact ht')
    zero_body += _call('prime_field_add_zero_left','p','0') + ('exact hp',) + _call('prime_field_zero_below_prime','p') + ('exact hp',)
    zero = spec(
        'prime_field_polynomial_horner_zero',
        f"forall p b c t l. ({_prime('p','zero_prime')}) -> ({_lt('t','p','zero_base')}) -> ({_repeat('b','c','0','l','zero_coefficients')}) -> ({_eval('p','b','c','t','l','0','zero_execution')})",
        ('prime_field_polynomial_horner_empty_construct','prime_field_polynomial_horner_successor_construct','zero_add','le_succ','prime_field_multiply_zero_left','prime_field_add_zero_left','prime_field_zero_below_prime'),
        zero_body,
        'Every actually encoded all-zero coefficient prefix has a genuine zero-result modular execution, including length zero.',
    )
    return empty, successor, constant, zero


def _completion_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('p','b','c','d','e','t','l','n','r','hp','hred','ht','hn') + ('split','intro he')
    body += _call('prime_field_polynomial_horner_normalization_residue','p','b','c','d','e','t','l','n','r') + ('exact hp','exact hred','exact hn','exact he','intro hr')
    body += (f"have he : exists s. ({_eval('p','d','e','t','l','s','iff_chosen_execution')})",)
    body += _call('prime_field_polynomial_horner_exists','p','d','e','t','l') + ('exact hp',)
    body += _call('prime_field_polynomial_normalization_bounded','p','b','c','d','e','l') + ('exact hred','exact ht','cases he')
    body += (f"have hs : {_residue('p','n','x','iff_chosen_residue')}",)
    body += _call('prime_field_polynomial_horner_normalization_residue','p','b','c','d','e','t','l','n','x') + ('exact hp','exact hred','exact hn','exact he_witness','have heq : x=r')
    body += _call('binary_canonical_residue_functional','p','n','x','r') + ('exact hs','exact hr')
    body += _rewrite_all('heq',_eval('p','d','e','t','l','x','iff_execution_transport'),'x','he_witness') + ('exact he_witness',)
    equivalence = spec(
        'prime_field_polynomial_normalized_horner_iff',
        f"forall p b c d e t l n r. ({_prime('p','iff_prime')}) -> ({_normalization('p','b','c','d','e','l','iff_reduction')}) -> ({_lt('t','p','iff_base')}) -> ({_natural('b','c','t','l','n','iff_natural')}) -> "
        + _and(f"({_eval('p','d','e','t','l','r','iff_execution_forward')}) -> ({_residue('p','n','r','iff_residue_forward')})",f"({_residue('p','n','r','iff_residue_backward')}) -> ({_eval('p','d','e','t','l','r','iff_execution_backward')})"),
        ('prime_field_polynomial_horner_normalization_residue','prime_field_polynomial_horner_exists','prime_field_polynomial_normalization_bounded','binary_canonical_residue_functional'),
        body,
        'After actual coefficient reduction, the genuine modular execution exists with exactly—and every—canonical residue of the original natural T12 evaluation.',
    )
    bounded = spec(
        'prime_field_polynomial_horner_result_bounded',
        f"forall p b c t l r. ({_prime('p','result_bound_prime')}) -> ({_eval('p','b','c','t','l','r','result_bound_execution')}) -> ({_lt('r','p','result_bound')})",
        ('beta_horner_eval_exists','prime_field_polynomial_horner_residue'),
        _intro('p','b','c','t','l','r','hp','he') + (f"have hn : exists n. ({_natural('b','c','t','l','n','result_bound_natural')})",)
        + _call('beta_horner_eval_exists','b','c','t','l') + ('cases hn',f"have hr : {_residue('p','x','r','result_bound_residue')}")
        + _call('prime_field_polynomial_horner_residue','p','b','c','t','l','x','r') + ('exact hp','exact hn_witness','exact he','cases hr','exact hr_left'),
        'Every genuine execution result is strictly below p, including the empty and zero-polynomial boundary cases.',
    )
    body = _intro('p','b','c','t','l','hp','ht')
    body += (f"have hred : exists d e. ({_normalization('p','b','c','d','e','l','complete_reduction')})",)
    body += _call('prime_field_polynomial_normalization_exists','p','b','c','l') + ('intro hz',) + _call('prime_nonzero','p') + ('exact hp','exact hz','cases hred','cases hred_witness')
    body += (f"have he : exists r. ({_eval('p','x','x1','t','l','r','complete_execution')})",)
    body += _call('prime_field_polynomial_horner_exists','p','x','x1','t','l') + ('exact hp',)
    body += _call('prime_field_polynomial_normalization_bounded','p','b','c','x','x1','l') + ('exact hred_witness_witness','exact ht','cases he','exists x','exists x1','exists x2','split','exact hred_witness_witness','split','exact he_witness')
    body += _intro('n','hn') + _call('prime_field_polynomial_horner_normalization_residue','p','b','c','x','x1','t','l','n','x2') + ('exact hp','exact hred_witness_witness','exact hn','exact he_witness')
    complete = spec(
        'prime_field_polynomial_reduce_and_evaluate_exists',
        f"forall p b c t l. ({_prime('p','complete_prime')}) -> ({_lt('t','p','complete_base')}) -> exists d e r. "
        + _and(_normalization('p','b','c','d','e','l','complete_reduction_result'),_eval('p','d','e','t','l','r','complete_execution_result'),f"forall n. ({_natural('b','c','t','l','n','complete_natural')}) -> ({_residue('p','n','r','complete_residue')})"),
        ('prime_field_polynomial_normalization_exists','prime_nonzero','prime_field_polynomial_horner_exists','prime_field_polynomial_normalization_bounded','prime_field_polynomial_horner_normalization_residue'),
        body,
        'For arbitrary finite natural coefficients construct their canonical prime-field table and an actual Horner execution, and prove agreement with every natural T12 evaluation.',
    )
    return equivalence, bounded, complete


def make_prime_field_polynomial_evaluation_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (*_construction_rows(spec), *_structural_rows(spec), *_invariant_rows(spec), *_recurrence_rows(spec), *_completion_rows(spec))


__all__ = [
    'prime_field_polynomial_horner_step_relation','prime_field_polynomial_horner_steps_relation',
    'prime_field_polynomial_horner_trace_relation','prime_field_polynomial_evaluation_relation',
    'make_prime_field_polynomial_evaluation_candidate_theorems',
]
