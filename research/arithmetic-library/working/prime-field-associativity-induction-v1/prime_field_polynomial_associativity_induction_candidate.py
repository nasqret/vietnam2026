"""Draft base and quantified induction for actual polynomial associativity.

This is source-only working material until its real body checks are recorded.
In particular the exact append-step dependency is currently an unproved input
to this draft, not an acceptance receipt. No theorem, definition or Alpha row
is registered here. Formal coefficient equivalence never means raw-code or
finite-field evaluation equality.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import _call, _intro, _parts, _prime
from peano_lab.library.prime_field_polynomial_candidate import _at, _coeff, _repeat
from peano_lab.library.prime_field_polynomial_convolution_candidate import _convolution, _length
from peano_lab.library.prime_field_polynomial_representation_candidate import _equivalent


def _contract(parameters: tuple[str, ...], premises: tuple[str, ...], conclusion: str) -> str:
    return 'forall '+' '.join(parameters)+'. '+' -> '.join('('+part+')' for part in (*premises,conclusion))


A,B,P = ('ab','ac','L'),('bb','bc','M'),('pb','pc','N')
C,Q,R,S = ('cb','cc','J'),('qb','qc','K'),('rb','rc','U'),('sb','sc','V')
BASE_PARAMETERS = ('p',*A,*B,*P,'cb','cc',*Q,*R,*S)
PARAMETERS = ('p',*A,*B,*P,*C,*Q,*R,*S)


def _empty_right_row(spec: Callable[..., Any]) -> Any:
    empty = ('cb','cc','0')
    q = _convolution('p',*B,*empty,*Q,'associativity_empty_Q')
    r = _convolution('p',*P,*empty,*R,'associativity_empty_R')
    s = _convolution('p',*A,*Q,*S,'associativity_empty_S')
    body = _intro(*BASE_PARAMETERS,'hp','hQ','hR','hS')
    body += (f"have hempty : {_repeat('cb','cc','0','0','associativity_empty_prefix')}",)
    body += _call('beta_repeat_empty','cb','cc','0','0') + ('refl',)
    for label,first,second,output,zero,hypothesis in (
        ('hQzero',B,empty,Q,'hempty','hQ'),
        ('hRzero',P,empty,R,'hempty','hR'),
        ('hSzero',A,Q,S,'hQzero','hS'),
    ):
        body += ('have '+label+' : '+_repeat(output[0],output[1],'0',output[2],'associativity_'+label),)
        body += _call('prime_field_polynomial_convolution_zero_right','p',*first,*second,*output)
        body += ('exact hp','exact '+zero,'exact '+hypothesis)
    body += _call('prime_field_polynomial_equivalent_transitive',*R,'0','0','0',*S)
    body += _call('prime_field_polynomial_zero_prefix_equivalent_empty',*R) + ('exact hRzero',)
    body += _call('prime_field_polynomial_equivalent_symmetric',*S,'0','0','0')
    body += _call('prime_field_polynomial_zero_prefix_equivalent_empty',*S) + ('exact hSzero',)
    return spec(
        'prime_field_polynomial_nested_empty_right_equivalent',
        _contract(BASE_PARAMETERS,('~(p=0)',q,r,s),_equivalent(*R,*S,'associativity_empty_result')),
        ('beta_repeat_empty','prime_field_polynomial_convolution_zero_right',
         'prime_field_polynomial_equivalent_transitive','prime_field_polynomial_zero_prefix_equivalent_empty',
         'prime_field_polynomial_equivalent_symmetric'),
        body,
        'At every nonzero modulus, actual Q=B*empty, R=P*empty and S=A*Q have formally equivalent all-zero outputs, for arbitrary actual P. The argument constructs the genuine empty zero-prefix fact and transports it through the real products; it assumes neither P=AB nor an output-length shortcut.',
    )


def _induction_row(spec: Callable[..., Any]) -> Any:
    ab = _convolution('p',*A,*B,*P,'associativity_AB')
    bc = _convolution('p',*B,*C,*Q,'associativity_BC')
    pc = _convolution('p',*P,*C,*R,'associativity_PC')
    aq = _convolution('p',*A,*Q,*S,'associativity_AQ')
    inner_parameters = ('j','db','dc','qxb','qxc','k','rxb','rxc','u','sxb','sxc','v')
    inner_c = ('db','dc','j')
    inner_q,inner_r,inner_s = ('qxb','qxc','k'),('rxb','rxc','u'),('sxb','sxc','v')
    quantified = _contract(inner_parameters,(
        _convolution('p',*B,*inner_c,*inner_q,'associativity_quantified_Q'),
        _convolution('p',*P,*inner_c,*inner_r,'associativity_quantified_R'),
        _convolution('p',*A,*inner_q,*inner_s,'associativity_quantified_S'),
    ),_equivalent(*inner_r,*inner_s,'associativity_quantified_result'))
    body = _intro(*PARAMETERS,'hp','hAB','hBC','hPC','hAQ')
    body += ('have hp0 : ~(p=0)','intro hz') + _call('prime_nonzero','p') + ('exact hp','exact hz')
    body += ('have hABcopy : '+ab,'exact hAB') + _parts('hABcopy',4)
    body += (f"have hPbound : {_coeff('p',*P,'associativity_P_bound')}",)
    body += _call('prime_field_polynomial_convolution_bounded','p',*A,*B,*P) + ('exact hAB',)
    # The predicate quantifies codes and every output triple after j. Thus IH
    # applies to genuine newly constructed prefix products, not fixed codes.
    body += ('have hall : '+quantified,'induction j')
    body += _intro(*inner_parameters[1:],'hQ','hR','hS')
    body += _call('prime_field_polynomial_nested_empty_right_equivalent',
                  'p',*A,*B,*P,'db','dc',*inner_q,*inner_r,*inner_s)
    body += ('exact hp0','exact hQ','exact hR','exact hS')

    body += _intro(*inner_parameters[1:],'hQ','hR','hS')
    full_c = ('db','dc','S j')
    full_q = _convolution('p',*B,*full_c,*inner_q,'associativity_step_Q_copy')
    body += ('have hQcopy : '+full_q,'exact hQ') + _parts('hQcopy',4)
    body += (f"have hprefix_bound : {_coeff('p','db','dc','j','associativity_prefix_bound')}",)
    body += _call('matrix_rank_bounded_prefix_drop_last','db','dc','j','p') + ('exact hQcopy_right_left',)
    body += (f"have hlast : exists a. ({_at('db','dc','j','a','associativity_actual_last')})",)
    body += _call('beta_at_exists','db','dc','j') + ('cases hlast',)

    # Q0=B*C_prefix: actual length x1 and actual codes x2,x3.
    body += (f"have hQlength : exists k0. ({_length('M','j','k0','associativity_Q0_length')})",)
    body += _call('polynomial_product_length_exists','M','j') + ('cases hQlength',)
    q0 = _convolution('p',*B,*inner_c,'q0b','q0c','x1','associativity_Q0')
    body += ('have hQ0 : exists q0b q0c. '+q0,)
    body += _call('prime_field_polynomial_convolution_at_length_exists','p',*B,*inner_c,'x1')
    body += ('exact hp0','exact hABcopy_right_left','exact hprefix_bound','exact hQlength_witness',
             'cases hQ0','cases hQ0_witness')

    # R0=P*C_prefix: independent actual length x4 and codes x5,x6.
    body += (f"have hRlength : exists u0. ({_length('N','j','u0','associativity_R0_length')})",)
    body += _call('polynomial_product_length_exists','N','j') + ('cases hRlength',)
    r0 = _convolution('p',*P,*inner_c,'r0b','r0c','x4','associativity_R0')
    body += ('have hR0 : exists r0b r0c. '+r0,)
    body += _call('prime_field_polynomial_convolution_at_length_exists','p',*P,*inner_c,'x4')
    body += ('exact hp0','exact hPbound','exact hprefix_bound','exact hRlength_witness',
             'cases hR0','cases hR0_witness')

    # S0=A*Q0: again obtain its own length x7 and codes x8,x9.
    body += (f"have hQ0bound : {_coeff('p','x2','x3','x1','associativity_Q0_bound')}",)
    body += _call('prime_field_polynomial_convolution_bounded','p',*B,*inner_c,'x2','x3','x1')
    body += ('exact hQ0_witness_witness',)
    body += (f"have hSlength : exists v0. ({_length('L','x1','v0','associativity_S0_length')})",)
    body += _call('polynomial_product_length_exists','L','x1') + ('cases hSlength',)
    s0 = _convolution('p',*A,'x2','x3','x1','s0b','s0c','x7','associativity_S0')
    body += ('have hS0 : exists s0b s0c. '+s0,)
    body += _call('prime_field_polynomial_convolution_at_length_exists','p',*A,'x2','x3','x1','x7')
    body += ('exact hp0','exact hABcopy_left','exact hQ0bound','exact hSlength_witness',
             'cases hS0','cases hS0_witness')
    equality = _equivalent('x5','x6','x4','x8','x9','x7','associativity_actual_IH')
    body += ('have hprevious : '+equality,)
    body += _call('IH','db','dc','x2','x3','x1','x5','x6','x4','x8','x9','x7')
    body += ('exact hQ0_witness_witness','exact hR0_witness_witness','exact hS0_witness_witness')
    body += _call('prime_field_polynomial_convolution_associativity_append_step',
                  'p',*A,*B,*P,*inner_c,'x2','x3','x1','x5','x6','x4','x8','x9','x7',
                  'x','db','dc',*inner_q,*inner_r,*inner_s)
    body += ('exact hp','exact hAB','exact hQ0_witness_witness','exact hR0_witness_witness',
             'exact hS0_witness_witness','exact hprevious')
    body += _intro('i','a','hi','ha') + ('exact ha',)
    body += ('exact hlast_witness','exact hQ','exact hR','exact hS')

    body += _call('hall','J','cb','cc',*Q,*R,*S) + ('exact hBC','exact hPC','exact hAQ')
    return spec(
        'prime_field_polynomial_convolution_associative_equivalent',
        _contract(PARAMETERS,(_prime('p','associativity_prime'),ab,bc,pc,aq),
                  _equivalent(*R,*S,'associativity_result')),
        ('prime_nonzero','prime_field_polynomial_convolution_bounded',
         'prime_field_polynomial_nested_empty_right_equivalent','matrix_rank_bounded_prefix_drop_last',
         'beta_at_exists','polynomial_product_length_exists','prime_field_polynomial_convolution_at_length_exists',
         'prime_field_polynomial_convolution_associativity_append_step'),
        body,
        'Draft universal rightmost-length induction for formal equivalence of actual (A*B)*C and A*(B*C). The induction predicate quantifies all rightmost codes and proper-length output triples, the successor genuinely constructs three prefix products and decodes the actual endpoint, and the empty base retains arbitrary encodings. This statement is not a successful proof observation until its original body and its exact step dependency are genuinely checked.',
    )


def make_prime_field_polynomial_associativity_induction_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    return (_empty_right_row(spec),_induction_row(spec))


__all__ = ['make_prime_field_polynomial_associativity_induction_candidate_theorems']
