"""Actual synthetic-division executions over the established prime fields.

Coefficients are highest-degree-first. A nonempty input has length S n;
its quotient has length n. The quotient is an actual affine slice of an
actual modular Horner history, not a supplied polynomial identity. The
coefficient recurrence, remainder and degree drop are separate theorems.
This is not arbitrary-divisor polynomial Euclidean division or G091.
"""

from __future__ import annotations

from typing import Any, Callable

from .matrix_coded_product_candidate import _slice_terms
from .prime_field_arithmetic_candidate import (
    _add as _field_add, _mul as _field_mul,
    _and, _call, _intro, _lt, _parts, _prime, _public,
)
from .prime_field_polynomial_candidate import _at, _coeff, _equal
from .prime_field_polynomial_convolution_candidate import _le
from .prime_field_polynomial_degree_candidate import _degree
from .prime_field_polynomial_evaluation_candidate import _eval, _trace
from .prime_field_tables_candidate import _rewrite_all


def _quotient(u: str, v: str, qb: str, qc: str, n: str, tag: str) -> str:
    return _slice_terms(u, v, '1', '1', qb, qc, n, tag='pfs_' + tag)


def _synthetic(p: str, b: str, c: str, a: str, n: str,
               qb: str, qc: str, r: str, tag: str) -> str:
    u, v = 'pfs_history_code_' + tag, 'pfs_history_scale_' + tag
    return f'exists {u} {v}. ' + _and(
        _trace(p, b, c, a, f'S ({n})', r, u, v, tag + 'trace'),
        _quotient(u, v, qb, qc, n, tag + 'quotient'),
    )


def prime_field_polynomial_synthetic_division_relation(
    p: str, b: str, c: str, a: str, n: str, qb: str, qc: str, r: str,
    *, tag: str, variables: tuple[str, ...],
) -> str:
    """Real Horner execution and encoded quotient for division by X-a."""
    return _public(_synthetic, (p, b, c, a, n, qb, qc, r),
                   tag=tag, variables=variables)


def _history_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('p','b','c','a','l','r','u','v','n','h','ht','hn','hh')
    body += _parts('ht',4)
    body += ('exists u','exists v','split','exact ht_left','split',
             'exact ht_right_left','split','exact hh')
    body += _intro('i','hi') + _call('ht_right_right_right','i')
    body += _call('le_trans','S i','n','l') + ('exact hi','exact hn')
    prefix = spec(
        'prime_field_polynomial_horner_trace_prefix',
        f"forall p b c a l r u v n h. ({_trace('p','b','c','a','l','r','u','v','prefix_trace')}) -> "
        f"({_le('n','l','prefix_length')}) -> ({_at('u','v','n','h','prefix_state')}) -> "
        f"({_eval('p','b','c','a','n','h','prefix_execution')})",
        ('le_trans',), body,
        'Every bounded prefix of a genuine Horner history is a genuine execution with its actually decoded terminal state.',
    )
    body = _intro('p','b','c','a','l','r','u','v','n','h','hp','ht','hn','hh')
    body += _call('prime_field_polynomial_horner_result_bounded','p','b','c','a','n','h')
    body += ('exact hp',) + _call('prime_field_polynomial_horner_trace_prefix',
                                'p','b','c','a','l','r','u','v','n','h')
    body += ('exact ht','exact hn','exact hh')
    bounds = spec(
        'prime_field_polynomial_horner_trace_state_bounded',
        f"forall p b c a l r u v n h. ({_prime('p','state_prime')}) -> "
        f"({_trace('p','b','c','a','l','r','u','v','state_trace')}) -> "
        f"({_le('n','l','state_length')}) -> ({_at('u','v','n','h','state_entry')}) -> "
        f"({_lt('h','p','state_bound')})",
        ('prime_field_polynomial_horner_result_bounded',
         'prime_field_polynomial_horner_trace_prefix'), body,
        'All actually decoded states of a canonical Horner history are canonical field elements, including its initial and terminal states.',
    )
    return prefix, bounds


def _construction_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('p','b','c','a','n','hp','hc','ha')
    body += (f"have he : exists r. ({_eval('p','b','c','a','S n','r','construct_eval')})",)
    body += _call('prime_field_polynomial_horner_exists','p','b','c','a','S n')
    body += ('exact hp','exact hc','exact ha','cases he','cases he_witness',
             'cases he_witness_witness')
    body += (f"have hq : exists qb qc. ({_quotient('x1','x2','qb','qc','n','construct_slice')})",)
    body += _call('beta_affine_matrix_slice_exists','x1','x2','1','1','n')
    body += ('cases hq','cases hq_witness','exists x3','exists x4','exists x',
             'exists x1','exists x2','split','exact he_witness_witness_witness',
             'exact hq_witness_witness')
    exists = spec(
        'prime_field_polynomial_synthetic_exists',
        f"forall p b c a n. ({_prime('p','construct_prime')}) -> "
        f"({_coeff('p','b','c','S n','construct_coefficients')}) -> "
        f"({_lt('a','p','construct_base')}) -> exists qb qc r. "
        f"({_synthetic('p','b','c','a','n','qb','qc','r','construct_result')})",
        ('prime_field_polynomial_horner_exists','beta_affine_matrix_slice_exists'),
        body,
        'Construct the actual quotient code and remainder from a real modular Horner history, for every nonempty canonical coefficient prefix.',
    )
    execution = spec(
        'prime_field_polynomial_synthetic_remainder_execution',
        f"forall p b c a n qb qc r. ({_synthetic('p','b','c','a','n','qb','qc','r','remainder_source')}) -> "
        f"({_eval('p','b','c','a','S n','r','remainder_execution')})",
        (),
        _intro('p','b','c','a','n','qb','qc','r','hs')
        + ('cases hs','cases hs_witness','cases hs_witness_witness',
           'exists x','exists x1','exact hs_witness_witness_left'),
        'The synthetic remainder is the actual evaluation of the original input at the divisor root, not an assumed result certificate.',
    )
    body = _intro('p','b','c','a','n','qb','qc','r','i','h','hs','hi','hh')
    body += ('cases hs','cases hs_witness','cases hs_witness_witness')
    body += (f"have he : exists z. ({_at('x','x1','S i','z','entry_history_state')})",)
    body += _call('beta_at_exists','x','x1','S i') + ('cases he',)
    body += ('have hindex : 1+1*i=S i','simp [one_mul,add_succ_left,zero_add]')
    body += (f"have hshift : {_at('x','x1','1+1*i','x2','entry_shifted_state')}",)
    body += _rewrite_all('hindex',_at('x','x1','1+1*i','x2','entry_shift_rewrite'),
                         '1+1*i') + ('exact he_witness',)
    body += ('have heq : h=x2',) + _call('hs_witness_witness_right','i','x2','h')
    body += ('exact hi','exact hshift','exact hh',)
    body += (f"have hex : {_eval('p','b','c','a','S i','x2','entry_execution_chosen')}",)
    body += _call('prime_field_polynomial_horner_trace_prefix',
                  'p','b','c','a','S n','r','x','x1','S i','x2')
    body += ('exact hs_witness_witness_left',) + _call('le_succ','S i','n')
    body += ('exact hi','exact he_witness','have hback : x2=h','symm','exact heq')
    body += _rewrite_all('hback',_eval('p','b','c','a','S i','x2','entry_execution_rewrite'),
                         'x2','hex') + ('exact hex',)
    entry = spec(
        'prime_field_polynomial_synthetic_quotient_entry',
        f"forall p b c a n qb qc r i h. ({_synthetic('p','b','c','a','n','qb','qc','r','entry_division')}) -> "
        f"({_lt('i','n','entry_index')}) -> ({_at('qb','qc','i','h','entry_quotient')}) -> "
        f"({_eval('p','b','c','a','S i','h','entry_execution')})",
        ('beta_at_exists','one_mul','add_succ_left','zero_add',
         'prime_field_polynomial_horner_trace_prefix','le_succ'), body,
        'Each decoded quotient coefficient is precisely the actual Horner value of the corresponding nonempty input prefix.',
    )
    return exists, execution, entry


def _value_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('p','b','c','a','n','qb','qc','r','hp','hs','i','hi')
    body += (f"have he : exists h. ({_at('qb','qc','i','h','bounded_entry')})",)
    body += _call('beta_at_exists','qb','qc','i') + ('cases he','exists x','split','exact he_witness')
    body += _call('prime_field_polynomial_horner_result_bounded','p','b','c','a','S i','x')
    body += ('exact hp',) + _call('prime_field_polynomial_synthetic_quotient_entry',
                                'p','b','c','a','n','qb','qc','r','i','x')
    body += ('exact hs','exact hi','exact he_witness')
    bounded = spec(
        'prime_field_polynomial_synthetic_quotient_bounded',
        f"forall p b c a n qb qc r. ({_prime('p','bounded_prime')}) -> "
        f"({_synthetic('p','b','c','a','n','qb','qc','r','bounded_division')}) -> "
        f"({_coeff('p','qb','qc','n','bounded_quotient')})",
        ('beta_at_exists','prime_field_polynomial_horner_result_bounded',
         'prime_field_polynomial_synthetic_quotient_entry'), body,
        'The constructively encoded quotient has canonical coefficients at every one of its n positions; this includes an empty quotient for constants.',
    )
    remainder = spec(
        'prime_field_polynomial_synthetic_remainder_bounded',
        f"forall p b c a n qb qc r. ({_prime('p','rbound_prime')}) -> "
        f"({_synthetic('p','b','c','a','n','qb','qc','r','rbound_division')}) -> "
        f"({_lt('r','p','rbound_result')})",
        ('prime_field_polynomial_horner_result_bounded',
         'prime_field_polynomial_synthetic_remainder_execution'),
        _intro('p','b','c','a','n','qb','qc','r','hp','hs')
        + _call('prime_field_polynomial_horner_result_bounded','p','b','c','a','S n','r')
        + ('exact hp',) + _call('prime_field_polynomial_synthetic_remainder_execution',
                               'p','b','c','a','n','qb','qc','r') + ('exact hs',),
        'Every actual synthetic remainder is a canonical field value.',
    )
    body = _intro('p','b','c','a','n','qb','qc','r','Qb','Qc','s','hp','hq','hQ')
    body += ('split',) + _call('prime_field_polynomial_horner_functional',
                              'p','b','c','a','S n','r','s') + ('exact hp',)
    body += _call('prime_field_polynomial_synthetic_remainder_execution',
                  'p','b','c','a','n','qb','qc','r') + ('exact hq',)
    body += _call('prime_field_polynomial_synthetic_remainder_execution',
                  'p','b','c','a','n','Qb','Qc','s') + ('exact hQ',)
    body += _intro('i','h','hi','hh')
    body += (f"have ht : exists z. ({_at('Qb','Qc','i','z','functional_target')})",)
    body += _call('beta_at_exists','Qb','Qc','i') + ('cases ht','have heq : x=h')
    body += _call('prime_field_polynomial_horner_functional','p','b','c','a','S i','x','h') + ('exact hp',)
    body += _call('prime_field_polynomial_synthetic_quotient_entry',
                  'p','b','c','a','n','Qb','Qc','s','i','x') + ('exact hQ','exact hi','exact ht_witness')
    body += _call('prime_field_polynomial_synthetic_quotient_entry',
                  'p','b','c','a','n','qb','qc','r','i','h') + ('exact hq','exact hi','exact hh')
    body += _rewrite_all('heq',_at('Qb','Qc','i','x','functional_rewrite'),'x','ht_witness')
    body += ('exact ht_witness',)
    functional = spec(
        'prime_field_polynomial_synthetic_functional',
        f"forall p b c a n qb qc r Qb Qc s. ({_prime('p','functional_prime')}) -> "
        f"({_synthetic('p','b','c','a','n','qb','qc','r','functional_first')}) -> "
        f"({_synthetic('p','b','c','a','n','Qb','Qc','s','functional_second')}) -> "
        + _and('r=s',_equal('qb','qc','Qb','Qc','n','functional_values')),
        ('prime_field_polynomial_horner_functional',
         'prime_field_polynomial_synthetic_remainder_execution','beta_at_exists',
         'prime_field_polynomial_synthetic_quotient_entry'), body,
        'The remainder and all decoded quotient values are unique, independently of either beta encoding or the chosen execution history.',
    )
    return bounded, remainder, functional


def _coefficient_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('p','b','c','a','r','v','hp','he','hv')
    body += (f"have hb : {_and(_lt('a','p','constant_base'),_coeff('p','b','c','1','constant_coefficients'))}",)
    body += _call('prime_field_polynomial_horner_input_bounds','p','b','c','a','1','r')
    body += ('exact he','cases hb',)
    body += _call('prime_field_polynomial_horner_functional','p','b','c','a','1','r','v')
    body += ('exact hp','exact he',) + _call('prime_field_polynomial_horner_constant','p','b','c','a','v')
    body += ('exact hp','exact hb_left',) + _call('matrix_rank_bounded_prefix_value',
                                               'b','c','1','p','0','v')
    body += ('exact hb_right','exists 0','simp','exact hv','exact hv')
    constant = spec(
        'prime_field_polynomial_horner_constant_value',
        f"forall p b c a r v. ({_prime('p','constant_prime')}) -> "
        f"({_eval('p','b','c','a','1','r','constant_execution')}) -> "
        f"({_at('b','c','0','v','constant_actual_coefficient')}) -> r=v",
        ('prime_field_polynomial_horner_input_bounds','prime_field_polynomial_horner_functional',
         'prime_field_polynomial_horner_constant','matrix_rank_bounded_prefix_value'), body,
        'An actual one-step execution returns the decoded constant coefficient; coefficient bounds follow from the execution itself.',
    )
    body = _intro('p','b','c','a','i','h','v','r','hp','he','hn','hv')
    body += (f"have hd : exists v h k. {_and(_at('b','c','i','v','transition_chosen_coefficient'),_eval('p','b','c','a','i','h','transition_chosen_prefix'),_field_mul('p','h','a','k','transition_chosen_product'),_field_add('p','k','v','r','transition_chosen_sum'))}",)
    body += _call('prime_field_polynomial_horner_successor_decompose','p','b','c','a','i','r')
    body += ('exact hn','cases hd','cases hd_witness','cases hd_witness_witness')
    body += _parts('hd_witness_witness_witness',4)
    body += ('have hve : x=v',) + _call('beta_at_unique','b','c','i','x','v')
    body += ('exact hd_witness_witness_witness_left','exact hv','have hhe : x1=h')
    body += _call('prime_field_polynomial_horner_functional','p','b','c','a','i','x1','h')
    body += ('exact hp','exact hd_witness_witness_witness_right_left','exact he')
    body += _rewrite_all('hhe',_field_mul('p','x1','a','x2','transition_product_rewrite'),
                         'x1','hd_witness_witness_witness_right_right_left')
    body += _rewrite_all('hve',_field_add('p','x2','x','r','transition_sum_rewrite'),
                         'x','hd_witness_witness_witness_right_right_right')
    body += ('exists x2','split','exact hd_witness_witness_witness_right_right_left',
             'exact hd_witness_witness_witness_right_right_right')
    transition = spec(
        'prime_field_polynomial_horner_transition_values',
        f"forall p b c a i h v r. ({_prime('p','transition_prime')}) -> "
        f"({_eval('p','b','c','a','i','h','transition_before')}) -> "
        f"({_eval('p','b','c','a','S i','r','transition_after')}) -> "
        f"({_at('b','c','i','v','transition_coefficient')}) -> exists k. "
        + _and(_field_mul('p','h','a','k','transition_product'),
               _field_add('p','k','v','r','transition_sum')),
        ('prime_field_polynomial_horner_successor_decompose','beta_at_unique',
         'prime_field_polynomial_horner_functional'), body,
        'Adjacent actual prefix values satisfy the genuine multiply-then-add recurrence, even when their execution histories use different codes.',
    )
    body = _intro('p','b','c','a','n','qb','qc','r','v','hp','hs','hv')
    body += (f"have hq : exists h. ({_at('qb','qc','0','h','leading_quotient_entry')})",)
    body += _call('beta_at_exists','qb','qc','0') + ('cases hq','have heq : x=v')
    body += _call('prime_field_polynomial_horner_constant_value','p','b','c','a','x','v')
    body += ('exact hp',) + _call('prime_field_polynomial_synthetic_quotient_entry',
                                'p','b','c','a','S n','qb','qc','r','0','x')
    body += ('exact hs','exists n','simp','exact hq_witness','exact hv')
    body += _rewrite_all('heq',_at('qb','qc','0','x','leading_rewrite'),'x','hq_witness')
    body += ('exact hq_witness',)
    leading = spec(
        'prime_field_polynomial_synthetic_leading_coefficient',
        f"forall p b c a n qb qc r v. ({_prime('p','leading_prime')}) -> "
        f"({_synthetic('p','b','c','a','S n','qb','qc','r','leading_division')}) -> "
        f"({_at('b','c','0','v','leading_input')}) -> ({_at('qb','qc','0','v','leading_output')})",
        ('beta_at_exists','prime_field_polynomial_horner_constant_value',
         'prime_field_polynomial_synthetic_quotient_entry'), body,
        'For a nonempty quotient its leading coefficient equals the original leading coefficient, including zero when the input has leading zeros.',
    )
    body = _intro('p','b','c','a','n','qb','qc','r','i','h','j','v','hp','hs','hi','hh','hj','hv')
    body += _call('prime_field_polynomial_horner_transition_values',
                  'p','b','c','a','S i','h','v','j') + ('exact hp',)
    body += _call('prime_field_polynomial_synthetic_quotient_entry',
                  'p','b','c','a','S n','qb','qc','r','i','h')
    body += ('exact hs',) + _call('le_succ','S i','n') + ('exact hi','exact hh')
    body += _call('prime_field_polynomial_synthetic_quotient_entry',
                  'p','b','c','a','S n','qb','qc','r','S i','j')
    body += ('exact hs',) + _call('succ_le_succ','S i','n') + ('exact hi','exact hj','exact hv')
    middle = spec(
        'prime_field_polynomial_synthetic_middle_coefficients',
        f"forall p b c a n qb qc r i h j v. ({_prime('p','middle_prime')}) -> "
        f"({_synthetic('p','b','c','a','S n','qb','qc','r','middle_division')}) -> "
        f"({_lt('i','n','middle_index')}) -> ({_at('qb','qc','i','h','middle_previous')}) -> "
        f"({_at('qb','qc','S i','j','middle_next')}) -> ({_at('b','c','S i','v','middle_input')}) -> exists k. "
        + _and(_field_mul('p','h','a','k','middle_product'),_field_add('p','k','v','j','middle_sum')),
        ('prime_field_polynomial_horner_transition_values',
         'prime_field_polynomial_synthetic_quotient_entry','le_succ','succ_le_succ'), body,
        'Interior quotient coefficients satisfy q[i+1]=a*q[i]+f[i+1] by actual field operations, with the highest-degree-first indices explicit.',
    )
    body = _intro('p','b','c','a','n','qb','qc','r','h','v','hp','hs','hh','hv')
    body += _call('prime_field_polynomial_horner_transition_values',
                  'p','b','c','a','S n','h','v','r') + ('exact hp',)
    body += _call('prime_field_polynomial_synthetic_quotient_entry',
                  'p','b','c','a','S n','qb','qc','r','n','h')
    body += ('exact hs','exists 0','apply zero_add','exact hh')
    body += _call('prime_field_polynomial_synthetic_remainder_execution',
                  'p','b','c','a','S n','qb','qc','r') + ('exact hs','exact hv')
    last = spec(
        'prime_field_polynomial_synthetic_final_coefficient',
        f"forall p b c a n qb qc r h v. ({_prime('p','final_prime')}) -> "
        f"({_synthetic('p','b','c','a','S n','qb','qc','r','final_division')}) -> "
        f"({_at('qb','qc','n','h','final_quotient')}) -> ({_at('b','c','S n','v','final_input')}) -> exists k. "
        + _and(_field_mul('p','h','a','k','final_product'),_field_add('p','k','v','r','final_sum')),
        ('prime_field_polynomial_horner_transition_values',
         'prime_field_polynomial_synthetic_quotient_entry','zero_add',
         'prime_field_polynomial_synthetic_remainder_execution'), body,
        'The remainder satisfies r=a*q[last]+f[last] by genuine canonical multiplication and addition.',
    )
    return constant, transition, leading, middle, last


def _completion_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('p','b','c','a','n','qb','qc','r','hp','hd','hs') + _parts('hd',3)
    body += ('split','refl','split',) + _call('prime_field_polynomial_synthetic_quotient_bounded',
                                           'p','b','c','a','S n','qb','qc','r')
    body += ('exact hp','exact hs','cases hd_right_right','cases hd_right_right_witness',
             'exists x','split')
    body += _call('prime_field_polynomial_synthetic_leading_coefficient',
                  'p','b','c','a','n','qb','qc','r','x')
    body += ('exact hp','exact hs','exact hd_right_right_witness_left',
             'exact hd_right_right_witness_right')
    degree = spec(
        'prime_field_polynomial_synthetic_represented_degree',
        f"forall p b c a n qb qc r. ({_prime('p','degree_prime')}) -> "
        f"({_degree('p','b','c','S (S n)','S n','degree_input')}) -> "
        f"({_synthetic('p','b','c','a','S n','qb','qc','r','degree_division')}) -> "
        f"({_degree('p','qb','qc','S n','n','degree_quotient')})",
        ('prime_field_polynomial_synthetic_quotient_bounded',
         'prime_field_polynomial_synthetic_leading_coefficient'), body,
        'Synthetic division of a nonzero-leading polynomial of positive represented degree S n produces a quotient of represented degree exactly n.',
    )
    constant = spec(
        'prime_field_polynomial_synthetic_constant',
        f"forall p b c a qb qc r v. ({_prime('p','constant_division_prime')}) -> "
        f"({_synthetic('p','b','c','a','0','qb','qc','r','constant_division')}) -> "
        f"({_at('b','c','0','v','constant_division_coefficient')}) -> r=v",
        ('prime_field_polynomial_horner_constant_value',
         'prime_field_polynomial_synthetic_remainder_execution'),
        _intro('p','b','c','a','qb','qc','r','v','hp','hs','hv')
        + _call('prime_field_polynomial_horner_constant_value','p','b','c','a','r','v')
        + ('exact hp',) + _call('prime_field_polynomial_synthetic_remainder_execution',
                               'p','b','c','a','0','qb','qc','r') + ('exact hs','exact hv'),
        'A constant has an empty quotient and its own coefficient as remainder, without assigning a degree to the empty quotient.',
    )
    uniqueness = _and('s=r',_equal('Qb','Qc','qb','qc','n','unique_values'))
    body = _intro('p','b','c','a','n','hp','hc','ha')
    body += (f"have he : exists qb qc r. ({_synthetic('p','b','c','a','n','qb','qc','r','unique_chosen')})",)
    body += _call('prime_field_polynomial_synthetic_exists','p','b','c','a','n')
    body += ('exact hp','exact hc','exact ha','cases he','cases he_witness',
             'cases he_witness_witness','exists x','exists x1','exists x2','split',
             'exact he_witness_witness_witness') + _intro('Qb','Qc','s','hQ')
    body += _call('prime_field_polynomial_synthetic_functional',
                  'p','b','c','a','n','Qb','Qc','s','x','x1','x2')
    body += ('exact hp','exact hQ','exact he_witness_witness_witness')
    unique = spec(
        'prime_field_polynomial_synthetic_exists_unique',
        f"forall p b c a n. ({_prime('p','unique_prime')}) -> "
        f"({_coeff('p','b','c','S n','unique_coefficients')}) -> ({_lt('a','p','unique_base')}) -> "
        'exists qb qc r. ' + _and(_synthetic('p','b','c','a','n','qb','qc','r','unique_execution'),
            f"forall Qb Qc s. ({_synthetic('p','b','c','a','n','Qb','Qc','s','unique_other')}) -> ({uniqueness})"),
        ('prime_field_polynomial_synthetic_exists','prime_field_polynomial_synthetic_functional'),
        body,
        'Every nonempty canonical input has a constructively encoded synthetic quotient and remainder, unique in decoded values rather than raw codes.',
    )
    body = _intro('p','b','c','a','n','qb','qc','r','hp','hs')
    body += (f"have he : {_eval('p','b','c','a','S n','r','root_actual_execution')}",)
    body += _call('prime_field_polynomial_synthetic_remainder_execution',
                  'p','b','c','a','n','qb','qc','r') + ('exact hs','split','intro hz')
    body += _rewrite_all('hz',_eval('p','b','c','a','S n','r','root_rewrite'),'r','he')
    body += ('exact he','intro hz') + _call('prime_field_polynomial_horner_functional',
                                         'p','b','c','a','S n','r','0')
    body += ('exact hp','exact he','exact hz')
    root = spec(
        'prime_field_polynomial_synthetic_zero_remainder_iff',
        f"forall p b c a n qb qc r. ({_prime('p','root_prime')}) -> "
        f"({_synthetic('p','b','c','a','n','qb','qc','r','root_division')}) -> "
        + _and(f"r=0 -> ({_eval('p','b','c','a','S n','0','root_forward')})",
               f"({_eval('p','b','c','a','S n','0','root_backward')}) -> r=0"),
        ('prime_field_polynomial_synthetic_remainder_execution',
         'prime_field_polynomial_horner_functional'), body,
        'The actual synthetic remainder vanishes exactly when the actual input evaluation at a vanishes; a general convolution factor theorem remains a separate obligation.',
    )
    return degree, constant, unique, root


def make_prime_field_polynomial_synthetic_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (*_history_rows(spec), *_construction_rows(spec), *_value_rows(spec),
            *_coefficient_rows(spec), *_completion_rows(spec))


__all__ = ['prime_field_polynomial_synthetic_division_relation',
           'make_prime_field_polynomial_synthetic_candidate_theorems']
