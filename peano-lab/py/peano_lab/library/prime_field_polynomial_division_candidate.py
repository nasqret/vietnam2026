"""Working constructive quotient recursion over actual prime-field tables.

The quotient is built coefficient by coefficient in highest-degree-first
order.  At index i its execution graph computes the genuine convolution
coefficient of the already-built length-i prefix, subtracts that value from
the input coefficient, and multiplies by a supplied canonical scalar.  The
separate correctness theorem requires that scalar to be the actual inverse
of the nonzero divisor head.  The graph does not contain a quotient identity,
a vanishing-prefix assertion, or a remainder-degree conclusion.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.prime_field_arithmetic_candidate import (
    _add, _and, _call, _intro, _inv, _lt, _mul, _part, _parts, _prime, _public,
)
from peano_lab.library.prime_field_polynomial_candidate import _add as _polynomial_add, _at, _coeff, _equal, _repeat
from peano_lab.library.prime_field_polynomial_convolution_candidate import _coefficient, _convolution, _le, _prefix
from peano_lab.library.prime_field_polynomial_degree_candidate import _degree
from peano_lab.library.prime_field_polynomial_subtraction_candidate import _subtract
from peano_lab.library.prime_field_polynomial_trim_candidate import _trim
from peano_lab.library.prime_field_tables_candidate import _rewrite_all


def _quotient_step(p: str, k: str, ab: str, ac: str, bb: str, bc: str,
                   M: str, qb: str, qc: str, i: str, q: str, tag: str) -> str:
    a, c, s = ('pfd_' + role + '_' + tag for role in ('input', 'previous', 'difference'))
    return f'exists {a} {c} {s}. ' + _and(
        _at(ab,ac,i,a,tag+'input'),
        _coefficient(p,qb,qc,i,bb,bc,M,i,c,tag+'previous'),
        _add(p,c,s,a,tag+'subtract'), _mul(p,k,s,q,tag+'multiply'),
    )


def _quotient_prefix(p: str, k: str, ab: str, ac: str, bb: str, bc: str,
                     M: str, qb: str, qc: str, N: str, tag: str) -> str:
    i, q = 'pfd_index_' + tag, 'pfd_value_' + tag
    return f'forall {i}. ({_lt(i,N,tag+"bound")}) -> exists {q}. ' + _and(
        _at(qb,qc,i,q,tag+'entry'),
        _quotient_step(p,k,ab,ac,bb,bc,M,qb,qc,i,q,tag+'step'),
    )


def _quotient_length(L: str, d: str, q: str, tag: str) -> str:
    return f"({_and(f'({q})=0',_le(L,d,tag+'short'))}) \\/ " + f"({_and(f'~(({q})=0)',f'({q})+({d})=({L})')})"


def _division_execution(p: str, ab: str, ac: str, L: str, bb: str, bc: str,
                        d: str, qb: str, qc: str, q: str,
                        rb: str, rc: str, R: str, tag: str) -> str:
    b,k,pb,pc,ub,uc,t=('pfd_'+role+'_'+tag for role in
                      ('head','inverse','product_code','product_scale','residual_code','residual_scale','cut'))
    data=_and(
        _at(bb,bc,'0',b,tag+'head'),_inv(p,b,k,tag+'inverse'),
        _quotient_prefix(p,k,ab,ac,bb,bc,f'S ({d})',qb,qc,q,tag+'quotient'),
        _prefix(p,qb,qc,q,bb,bc,f'S ({d})',pb,pc,L,tag+'product'),
        _subtract(p,ab,ac,pb,pc,ub,uc,L,tag+'difference'),
        _trim(p,ub,uc,L,t,rb,rc,R,tag+'trim'),
    )
    return _and(_coeff(p,ab,ac,L,tag+'input'),_coeff(p,bb,bc,f'S ({d})',tag+'divisor'),
                _quotient_length(L,d,q,tag+'length'),f'exists {b} {k} {pb} {pc} {ub} {uc} {t}. {data}')


def _remainder_degree(p: str, rb: str, rc: str, R: str, d: str, tag: str) -> str:
    e='pfd_remainder_degree_'+tag
    return f'({R})=0 \\/ (exists {e}. '+_and(_degree(p,rb,rc,R,e,tag+'represented'),_lt(e,d,tag+'strict'))+')'


def prime_field_polynomial_quotient_step_relation(
    p: str, k: str, ab: str, ac: str, bb: str, bc: str, M: str,
    qb: str, qc: str, i: str, q: str, *, tag: str, variables: tuple[str,...],
) -> str:
    return _public(_quotient_step,(p,k,ab,ac,bb,bc,M,qb,qc,i,q),tag=tag,variables=variables)


def prime_field_polynomial_quotient_prefix_relation(
    p: str, k: str, ab: str, ac: str, bb: str, bc: str, M: str,
    qb: str, qc: str, N: str, *, tag: str, variables: tuple[str,...],
) -> str:
    return _public(_quotient_prefix,(p,k,ab,ac,bb,bc,M,qb,qc,N),tag=tag,variables=variables)


def prime_field_polynomial_quotient_length_relation(
    L: str, d: str, q: str, *, tag: str, variables: tuple[str,...],
) -> str:
    return _public(_quotient_length,(L,d,q),tag=tag,variables=variables)


def prime_field_polynomial_division_execution_relation(
    p: str, ab: str, ac: str, L: str, bb: str, bc: str, d: str,
    qb: str, qc: str, q: str, rb: str, rc: str, R: str,
    *, tag: str, variables: tuple[str,...],
) -> str:
    """Actual quotient execution, ambient product, subtraction, and trim data."""
    return _public(_division_execution,(p,ab,ac,L,bb,bc,d,qb,qc,q,rb,rc,R),tag=tag,variables=variables)


def _inverse_step_row(spec: Callable[..., Any]) -> Any:
    body = _intro('p','b','k','c','s','a','q','t','r','hp','hk','ha','hq','ht','hr')
    body += ('cases hk',) + _parts('hq',3)
    body += ('have heq : s=t',)
    body += _call('prime_field_multiply_associative','p','b','k','s','1','q','s','t')
    body += ('exact hk_right',) + _call('prime_field_multiply_one_left','p','s')
    body += ('exact hp','exact hq_right_left','exact hq')
    body += _call('prime_field_multiply_commutative','p','q','b','t') + ('exact ht',)
    body += _rewrite_all('heq',_add('p','c','s','a','division_scalar_rewrite'),'s','ha')
    body += _call('prime_field_add_functional','p','c','t','r','a') + ('exact hr','exact ha')
    return spec(
        'prime_field_polynomial_quotient_scalar_cancellation',
        f"forall p b k c s a q t r. ({_prime('p','division_scalar_prime')}) -> "
        f"({_inv('p','b','k','division_scalar_inverse')}) -> "
        f"({_add('p','c','s','a','division_scalar_difference')}) -> "
        f"({_mul('p','k','s','q','division_scalar_quotient')}) -> "
        f"({_mul('p','q','b','t','division_scalar_product')}) -> "
        f"({_add('p','c','t','r','division_scalar_sum')}) -> r=a",
        ('prime_field_multiply_associative','prime_field_multiply_one_left',
         'prime_field_multiply_commutative','prime_field_add_functional'), body,
        'The actual inverse scalar solves the triangular coefficient equation, including prime two and an arbitrary nonzero divisor head.',
    )


def _step_transport_row(spec: Callable[..., Any]) -> Any:
    params = ('p','k','ab','ac','bb','bc','M','qb','qc','QB','QC','i','q')
    body = _intro(*params,'he','hs')
    body += tuple('cases hs'+'_witness'*index for index in range(3))
    body += _parts('hs_witness_witness_witness',4)
    body += ('exists x','exists x1','exists x2','split','exact hs_witness_witness_witness_left','split')
    body += _call('prime_field_convolution_coefficient_transport','p','qb','qc','i','bb','bc','M','i','QB','QC','bb','bc','x1')
    body += ('exact he',) + _intro('j','v','hj','hv') + ('exact hv','exact hs_witness_witness_witness_right_left',
             'split','exact hs_witness_witness_witness_right_right_left','exact hs_witness_witness_witness_right_right_right')
    return spec(
        'prime_field_polynomial_quotient_step_recode',
        f"forall {' '.join(params)}. ({_equal('qb','qc','QB','QC','i','division_step_recode')}) -> "
        f"({_quotient_step('p','k','ab','ac','bb','bc','M','qb','qc','i','q','division_step_old')}) -> "
        f"({_quotient_step('p','k','ab','ac','bb','bc','M','QB','QC','i','q','division_step_new')})",
        ('prime_field_convolution_coefficient_transport',),body,
        'An execution step depends only on the actual previously built quotient prefix, never on unused beta entries.',
    )


def _prefix_base_rows(spec: Callable[..., Any]) -> tuple[Any,...]:
    params = ('p','k','ab','ac','bb','bc','M','qb','qc')
    empty = spec(
        'prime_field_polynomial_quotient_prefix_empty',
        f"forall {' '.join(params)}. {_quotient_prefix(*params,'0','division_empty')}",
        ('lt_not_le','zero_le'),
        _intro(*params,'i','hi')+('exfalso',)+_call('lt_not_le','i','0')+('exact hi',)+_call('zero_le','i'),
        'The actual empty quotient execution exists for all encodings and makes no assertion about an unused scalar or entry.',
    )
    restrict = spec(
        'prime_field_polynomial_quotient_prefix_restrict',
        f"forall {' '.join(params)} N K. ({_le('K','N','division_restrict_bound')}) -> "
        f"({_quotient_prefix(*params,'N','division_restrict_old')}) -> "
        f"({_quotient_prefix(*params,'K','division_restrict_new')})",
        ('lt_of_lt_of_le',),
        _intro(*params,'N','K','hk','h','i','hi')+_call('h','i')
        +_call('lt_of_lt_of_le','i','K','N')+('exact hi','exact hk'),
        'Every earlier portion of an actual quotient execution is the same execution prefix.',
    )
    body = _intro(*params,'N','i','q','h','hi','hq')
    point = _and(_at('qb','qc','i','r','division_entry_chosen'),
                 _quotient_step('p','k','ab','ac','bb','bc','M','qb','qc','i','r','division_entry_step'))
    body += (f'have hv : exists r. {point}',)+_call('h','i')+('exact hi','cases hv','cases hv_witness','have heq : x=q')
    body += _call('beta_at_unique','qb','qc','i','x','q')+('exact hv_witness_left','exact hq')
    body += _rewrite_all('heq',_quotient_step('p','k','ab','ac','bb','bc','M','qb','qc','i','x','division_entry_rewrite'),'x','hv_witness_right')
    body += ('exact hv_witness_right',)
    entry = spec(
        'prime_field_polynomial_quotient_prefix_entry',
        f"forall {' '.join(params)} N i q. ({_quotient_prefix(*params,'N','division_entry_source')}) -> "
        f"({_lt('i','N','division_entry_bound')}) -> ({_at('qb','qc','i','q','division_entry_given')}) -> "
        f"({_quotient_step('p','k','ab','ac','bb','bc','M','qb','qc','i','q','division_entry_result')})",
        ('beta_at_unique',),body,
        'Every actual bounded decoded quotient value has the exact subtraction-and-inverse-product execution witnesses.',
    )
    body = _intro(*params,'N','h','i','hi')
    point = _and(_at('qb','qc','i','q','division_bound_entry'),
                 _quotient_step('p','k','ab','ac','bb','bc','M','qb','qc','i','q','division_bound_step'))
    body += (f'have hv : exists q. {point}',)+_call('h','i')+('exact hi','cases hv','cases hv_witness','exists x','split','exact hv_witness_left')
    body += tuple('cases hv_witness_right'+'_witness'*index for index in range(3))
    body += _parts('hv_witness_right_witness_witness_witness',4)
    body += _parts('hv_witness_right_witness_witness_witness_right_right_right',4)
    body += ('exact hv_witness_right_witness_witness_witness_right_right_right_right_right_left',)
    bounded = spec(
        'prime_field_polynomial_quotient_prefix_bounded',
        f"forall {' '.join(params)} N. ({_quotient_prefix(*params,'N','division_bound_source')}) -> "
        f"({_coeff('p','qb','qc','N','division_bound_result')})",
        (),body,
        'The computed quotient prefix is canonical because every stored value is an actual bounded field-product output.',
    )
    return empty,restrict,entry,bounded


def _append_row(spec: Callable[...,Any]) -> Any:
    params = ('p','k','ab','ac','bb','bc','M','qb','qc','QB','QC','N','q')
    old = lambda tag:_quotient_prefix('p','k','ab','ac','bb','bc','M','qb','qc','N',tag)
    new = lambda tag:_quotient_prefix('p','k','ab','ac','bb','bc','M','QB','QC','S N',tag)
    body = _intro(*params,'h','he','hq','hs','i','hi')
    body += (f"have hcase : i=N \\/ ({_lt('i','N','division_append_earlier')})",)
    body += _call('finite_lt_succ_eq_or_lt','N','i')+('exact hi','cases hcase','exists q','split')
    body += _rewrite_all('hcase_left',_at('QB','QC','i','q','division_append_last_entry'),'i')+('exact hq',)
    body += _rewrite_all('hcase_left',_quotient_step('p','k','ab','ac','bb','bc','M','QB','QC','i','q','division_append_last_step'),'i')
    body += _call('prime_field_polynomial_quotient_step_recode','p','k','ab','ac','bb','bc','M','qb','qc','QB','QC','N','q')
    body += ('exact he','exact hs')
    point = _and(_at('qb','qc','i','r','division_append_old_entry'),
                 _quotient_step('p','k','ab','ac','bb','bc','M','qb','qc','i','r','division_append_old_step'))
    body += (f'have hv : exists r. {point}',)+_call('h','i')+('exact hcase_right','cases hv','cases hv_witness','exists x','split')
    body += _call('he','i','x')+('exact hcase_right','exact hv_witness_left')
    body += _call('prime_field_polynomial_quotient_step_recode','p','k','ab','ac','bb','bc','M','qb','qc','QB','QC','i','x')
    body += _intro('j','a','hj','ha')+_call('he','j','a')
    body += _call('lt_of_lt_of_le','j','S i','N')+_call('le_succ','S j','i')+('exact hj','exact hcase_right','exact ha','exact hv_witness_right')
    return spec(
        'prime_field_polynomial_quotient_prefix_append',
        f"forall {' '.join(params)}. ({old('division_append_old')}) -> "
        f"({_equal('qb','qc','QB','QC','N','division_append_equal')}) -> "
        f"({_at('QB','QC','N','q','division_append_given_entry')}) -> "
        f"({_quotient_step('p','k','ab','ac','bb','bc','M','qb','qc','N','q','division_append_given_step')}) -> "
        f"({new('division_append_new')})",
        ('finite_lt_succ_eq_or_lt','prime_field_polynomial_quotient_step_recode','lt_of_lt_of_le','le_succ'),body,
        'An actual beta-prefix extension preserves all earlier steps and adds the independently computed next quotient value.',
    )


def _exists_row(spec: Callable[...,Any]) -> Any:
    params=('p','k','ab','ac','bb','bc','M','N')
    body=_intro(*params,'hp','hk')+('induction N','intro ha','exists 0','exists 0')
    body+=_call('prime_field_polynomial_quotient_prefix_empty','p','k','ab','ac','bb','bc','M','0','0')
    body+=('intro ha',f"have hold : exists qb qc. ({_quotient_prefix('p','k','ab','ac','bb','bc','M','qb','qc','N','division_exists_old')})")
    body+=_call('IH')+_intro('i','hi')+_call('ha','i')+_call('le_succ','S i','N')+('exact hi','cases hold','cases hold_witness')
    body+=(f"have hinput : exists a. {_and(_at('ab','ac','N','a','division_exists_input'),_lt('a','p','division_exists_input_bound'))}",)
    body+=_call('ha','N')+_call('le_refl','S N')+('cases hinput','cases hinput_witness',)
    body+=(f"have hc : exists c. ({_coefficient('p','x','x1','N','bb','bc','M','N','c','division_exists_previous')})",)
    body+=_call('prime_field_convolution_coefficient_exists','p','x','x1','N','bb','bc','M','N')
    body+=('intro hz',)+_call('prime_nonzero','p')+('exact hp','exact hz','cases hc')
    body+=(f"have hs : exists s. ({_add('p','x3','s','x2','division_exists_difference')})",)
    body+=_call('prime_field_subtract_exists','p','x2','x3')+('exact hp','exact hinput_witness_right')
    body+=_call('prime_field_convolution_coefficient_bounded','p','x','x1','N','bb','bc','M','N','x3')+('exact hc_witness','cases hs')
    body+=(f"have hq : exists q. ({_mul('p','k','x4','q','division_exists_quotient')})",)
    body+=_call('prime_field_multiply_exists','p','k','x4')+('exact hp','exact hk','cases hs_witness','cases hs_witness_right','exact hs_witness_right_left','cases hq')
    extension=_and(_at('QB','QC','N','x5','division_exists_new_entry'),_equal('x','x1','QB','QC','N','division_exists_preservation'))
    body+=(f'have hnew : exists QB QC. {extension}',)+_call('beta_prefix_extend','N','x','x1','x5')
    body+=('cases hnew','cases hnew_witness','cases hnew_witness_witness','exists x6','exists x7')
    body+=_call('prime_field_polynomial_quotient_prefix_append','p','k','ab','ac','bb','bc','M','x','x1','x6','x7','N','x5')
    body+=('exact hold_witness_witness','exact hnew_witness_witness_right','exact hnew_witness_witness_left',
           'exists x2','exists x3','exists x4','split','exact hinput_witness_left','split','exact hc_witness',
           'split','exact hs_witness','exact hq_witness')
    return spec(
        'prime_field_polynomial_quotient_prefix_exists',
        f"forall {' '.join(params)}. ({_prime('p','division_exists_prime')}) -> "
        f"({_lt('k','p','division_exists_scalar')}) -> ({_coeff('p','ab','ac','N','division_exists_source')}) -> "
        f"exists qb qc. ({_quotient_prefix('p','k','ab','ac','bb','bc','M','qb','qc','N','division_exists_result')})",
        ('prime_field_polynomial_quotient_prefix_empty','le_succ','le_refl',
         'prime_field_convolution_coefficient_exists','prime_nonzero','prime_field_subtract_exists',
         'prime_field_convolution_coefficient_bounded','prime_field_multiply_exists',
         'beta_prefix_extend','prime_field_polynomial_quotient_prefix_append'),body,
        'Construct every quotient coefficient with actual sum, subtraction, inverse-scaling and beta-extension witnesses, by ordinary finite induction.',
    )


def _matching_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    params=('p','k','ab','ac','bb','bc','d','qb','qc','N','b','i','r')
    body=_intro(*params,'hp','hb','hk','hq','hi','hr')
    point=_and(_at('qb','qc','i','q','division_match_quotient_entry'),
               _quotient_step('p','k','ab','ac','bb','bc','S d','qb','qc','i','q','division_match_step'))
    body+=(f'have hpoint : exists q. {point}',)+_call('hq','i')+('exact hi','cases hpoint','cases hpoint_witness')
    body+=tuple('cases hpoint_witness_right'+'_witness'*index for index in range(3))
    body+=_parts('hpoint_witness_right_witness_witness_witness',4)
    head='hpoint_witness_right_witness_witness_witness'
    mulhyp=head+'_right_right_right'
    body+=(f"have hqbound : {_lt('x','p','division_match_value_bound')}",)+_parts(mulhyp,4)+('exact '+mulhyp+'_right_right_left',)
    body+=(f"have hbnd : {_lt('b','p','division_match_head_bound')}",'cases hk','cases hk_right','exact hk_right_left')
    body+=(f"have hproduct : exists t. ({_mul('p','x','b','t','division_match_product')})",)
    body+=_call('prime_field_multiply_exists','p','x','b')+('exact hp','exact hqbound','exact hbnd','cases hproduct')
    shorter=_coefficient('p','qb','qc','S i','bb','bc','S d','i','r','division_match_shorter')
    body+=(f'have hshort : {shorter}',)
    body+=_call('prime_field_convolution_coefficient_prefix_transport','p','qb','qc','N','qb','qc','S i','bb','bc','S d','S i','i','r')
    body+=('exact hi',)+_call('le_refl','S i')+_intro('j','v','hj','hv')+('exact hv',)+_call('le_refl','S i')+('exact hr',)
    body+=(f"have hsum : {_add('p','x2','x4','r','division_match_sum')}",)
    body+=_call('prime_field_convolution_coefficient_append','p','qb','qc','qb','qc','bb','bc','d','i','x','b','x2','x4','r')
    body+=_intro('j','v','hj','hv')+('exact hv','exact hpoint_witness_left','exact hb','exact '+head+'_right_left','exact hshort','exact hproduct_witness')
    body+=('have heq : r=x1',)+_call('prime_field_polynomial_quotient_scalar_cancellation','p','b','k','x2','x3','x1','x','x4','r')
    body+=('exact hp','exact hk','exact '+head+'_right_right_left','exact '+mulhyp,'exact hproduct_witness','exact hsum')
    body+=_rewrite_all('heq',_at('ab','ac','i','r','division_match_result'),'r')+('exact '+head+'_left',)
    entry=spec(
        'prime_field_polynomial_quotient_prefix_convolution_entry',
        f"forall {' '.join(params)}. ({_prime('p','division_match_prime')}) -> "
        f"({_at('bb','bc','0','b','division_match_head')}) -> ({_inv('p','b','k','division_match_inverse')}) -> "
        f"({_quotient_prefix('p','k','ab','ac','bb','bc','S d','qb','qc','N','division_match_execution')}) -> "
        f"({_lt('i','N','division_match_index')}) -> "
        f"({_coefficient('p','qb','qc','N','bb','bc','S d','i','r','division_match_actual_coefficient')}) -> "
        f"({_at('ab','ac','i','r','division_match_input')})",
        ('prime_field_multiply_exists','prime_field_convolution_coefficient_prefix_transport','le_refl',
         'prime_field_convolution_coefficient_append','prime_field_polynomial_quotient_scalar_cancellation'),body,
        'Every actual convolution coefficient below the constructed quotient length equals the corresponding input coefficient, proved from the execution rather than assumed.',
    )
    params=('p','k','ab','ac','bb','bc','d','qb','qc','N','b','pb','pc','L')
    body=_intro(*params,'hp','hb','hk','hq','hlen','hproduct','i','a','hi','ha')
    point=_and(_at('pb','pc','i','r','division_match_table_entry'),
               _coefficient('p','qb','qc','N','bb','bc','S d','i','r','division_match_table_coefficient'))
    body+=(f'have hv : exists r. {point}',)+_call('hproduct','i')
    body+=_call('lt_of_lt_of_le','i','N','L')+('exact hi','exact hlen','cases hv','cases hv_witness')
    body+=(f"have hinput : {_at('ab','ac','i','x','division_match_table_input')}",)
    body+=_call('prime_field_polynomial_quotient_prefix_convolution_entry','p','k','ab','ac','bb','bc','d','qb','qc','N','b','i','x')
    body+=('exact hp','exact hb','exact hk','exact hq','exact hi','exact hv_witness_right','have heq : x=a')
    body+=_call('beta_at_unique','ab','ac','i','x','a')+('exact hinput','exact ha')
    body+=_rewrite_all('heq',_at('pb','pc','i','x','division_match_table_rewrite'),'x','hv_witness_left')+('exact hv_witness_left',)
    product=spec(
        'prime_field_polynomial_quotient_prefix_product_matches',
        f"forall {' '.join(params)}. ({_prime('p','division_match_table_prime')}) -> "
        f"({_at('bb','bc','0','b','division_match_table_head')}) -> ({_inv('p','b','k','division_match_table_inverse')}) -> "
        f"({_quotient_prefix('p','k','ab','ac','bb','bc','S d','qb','qc','N','division_match_table_execution')}) -> "
        f"({_le('N','L','division_match_table_length')}) -> "
        f"({_prefix('p','qb','qc','N','bb','bc','S d','pb','pc','L','division_match_table_product')}) -> "
        f"({_equal('ab','ac','pb','pc','N','division_match_table_result')})",
        ('lt_of_lt_of_le','prime_field_polynomial_quotient_prefix_convolution_entry','beta_at_unique'),body,
        'The actual ambient product table agrees with the input throughout the computed quotient prefix, including the vacuous zero-length case.',
    )
    params=(*params,'ub','uc')
    body=_intro(*params,'hp','hb','hk','hq','hlen','hproduct','hsubtract')
    body+=_call('prime_field_polynomial_subtract_equal_zero','p','ab','ac','pb','pc','ub','uc','N')+('exact hp',)
    body+=_call('prime_field_polynomial_quotient_prefix_product_matches',*params[:-2])+('exact hp','exact hb','exact hk','exact hq','exact hlen','exact hproduct')
    body+=_intro('i','hi')+_call('hsubtract','i')+_call('lt_of_lt_of_le','i','N','L')+('exact hi','exact hlen')
    zero=spec(
        'prime_field_polynomial_quotient_prefix_remainder_zero',
        f"forall {' '.join(params)}. ({_prime('p','division_zero_prime')}) -> "
        f"({_at('bb','bc','0','b','division_zero_head')}) -> ({_inv('p','b','k','division_zero_inverse')}) -> "
        f"({_quotient_prefix('p','k','ab','ac','bb','bc','S d','qb','qc','N','division_zero_execution')}) -> "
        f"({_le('N','L','division_zero_length')}) -> "
        f"({_prefix('p','qb','qc','N','bb','bc','S d','pb','pc','L','division_zero_product')}) -> "
        f"({_subtract('p','ab','ac','pb','pc','ub','uc','L','division_zero_subtraction')}) -> "
        f"({_repeat('ub','uc','0','N','division_zero_result')})",
        ('prime_field_polynomial_subtract_equal_zero','prime_field_polynomial_quotient_prefix_product_matches','lt_of_lt_of_le'),body,
        'Subtracting the constructed product gives an actually all-zero leading prefix of the residual table.',
    )
    return entry,product,zero


def _length_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    body=_intro('L','d')+(f"have horder : ({_le('L','d','division_length_short')}) \\/ ({_lt('d','L','division_length_long')})",)
    body+=_call('le_or_lt','L','d')+('cases horder','exists 0','left','split','refl','exact horder_left',
           'cases horder_right','exists S x','right','split','intro hz')
    body+=_call('succ_ne_zero','x')+('exact hz','trans x+S d','simp [add_succ_left]','exact horder_right_witness')
    exists=spec(
        'polynomial_quotient_length_exists',
        f"forall L d. exists q. ({_quotient_length('L','d','q','division_length_exists')})",
        ('le_or_lt','succ_ne_zero','add_succ_left'),body,
        'Construct the true nonnegative quotient length: zero for a shorter input, otherwise the positive difference L-d.',
    )
    body=_intro('L','d','q','h')+('cases h','cases h_left','split','rewrite h_left_left')
    body+=_call('zero_le','L')+('have heq : q+d=d','rewrite h_left_left','apply zero_add',
           'rewrite heq','exact h_left_right','cases h_right','split','rewrite <- h_right_right')
    body+=_call('le_add_right','q','d')+('rewrite h_right_right',)+_call('le_refl','L')
    bounds=spec(
        'polynomial_quotient_length_bounds',
        f"forall L d q. ({_quotient_length('L','d','q','division_length_bound_source')}) -> "
        +_and(_le('q','L','division_length_quotient_bound'),_le('L','q+d','division_length_cover')),
        ('zero_le','zero_add','le_add_right','le_refl'),body,
        'The constructed quotient prefix fits in the input and its length plus the divisor degree covers every input coefficient.',
    )
    return exists,bounds


def _trim_bound_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    params=('p','ub','uc','L','t','rb','rc','R','q')
    trim=lambda tag:_trim('p','ub','uc','L','t','rb','rc','R',tag)
    body=_intro(*params,'hlen','hz','ht')
    body+=(f"have horder : ({_le('q','t','division_cut_before')}) \\/ ({_lt('t','q','division_cut_inside')})",)
    body+=_call('le_or_lt','q','t')+('cases horder','exact horder_left','have hR : R=0 \\/ ~(R=0)')
    body+=_call('eq_decidable','R','0')+('cases hR',f'have hcopy : {trim("division_cut_copy")}', 'exact ht')
    body+=_parts('hcopy',5)+('have hLt : L=t','trans t+R','exact hcopy_left','rewrite hR_left','simp',
           'rewrite hLt at hlen','exact hlen','exfalso')
    body+=_call('prime_field_polynomial_trim_leading_source_nonzero','p','ub','uc','L','t','rb','rc','R','0')
    body+=('exact ht','exact hR_right')+_call('hz','t')+('exact horder_right','refl')
    cut=spec(
        'prime_field_polynomial_trim_zero_prefix_cut_bound',
        f"forall {' '.join(params)}. ({_le('q','L','division_cut_length')}) -> "
        f"({_repeat('ub','uc','0','q','division_cut_zero')}) -> ({trim('division_cut_trim')}) -> "
        f"({_le('q','t','division_cut_result')})",
        ('le_or_lt','eq_decidable','prime_field_polynomial_trim_leading_source_nonzero'),body,
        'A normalized trim cannot stop inside a proved all-zero leading prefix; empty output is treated separately.',
    )
    params=(*params,'d')
    body=_intro(*params,'hqL','hLd','hz','ht')
    body+=(f"have hqt : {_le('q','t','division_remainder_cut')}",)
    body+=_call('prime_field_polynomial_trim_zero_prefix_cut_bound',*params[:-1])+('exact hqL','exact hz','exact ht')
    body+=(f'have hcopy : {trim("division_remainder_copy")}', 'exact ht')+_parts('hcopy',5)
    body+=('have htotal : R+t=L','trans t+R')+_call('add_comm','R','t')+('symm','exact hcopy_left',)
    body+=(f"have hpartial : {_le('R+q','R+t','division_remainder_partial')}",)
    body+=_call('add_le_add_left','q','t','R')+('exact hqt','rewrite htotal at hpartial')
    body+=(f"have hfull : {_le('R+q','q+d','division_remainder_full')}",)
    body+=_call('le_trans','R+q','L','q+d')+('exact hpartial','exact hLd','have hcomm : q+d=d+q')
    body+=_call('add_comm','q','d')+('rewrite hcomm at hfull',)+_call('add_le_cancel_right','R','d','q')+('exact hfull',)
    length=spec(
        'prime_field_polynomial_trim_zero_prefix_remainder_bound',
        f"forall {' '.join(params)}. ({_le('q','L','division_remainder_quotient_length')}) -> "
        f"({_le('L','q+d','division_remainder_cover_length')}) -> "
        f"({_repeat('ub','uc','0','q','division_remainder_zero')}) -> ({trim('division_remainder_trim')}) -> "
        f"({_le('R','d','division_remainder_bound')})",
        ('prime_field_polynomial_trim_zero_prefix_cut_bound','add_comm','add_le_add_left','le_trans','add_le_cancel_right'),body,
        'The actual trimmed residual has at most d coefficients after a length-q zero prefix is proved; no degree is assigned to the empty case.',
    )
    params=('p','ub','uc','L','t','rb','rc','R','d')
    body=_intro(*params,'ht','hbound')+('have hR : R=0 \\/ exists e. R=S e',)
    body+=_call('zero_or_succ','R')+('cases hR','left','exact hR_left','cases hR_right','right','exists x','split')
    body+=_call('prime_field_polynomial_trim_represented_degree','p','ub','uc','L','t','rb','rc','R','x')
    body+=('exact ht','exact hR_right_witness','rewrite hR_right_witness at hbound','exact hbound')
    degree=spec(
        'prime_field_polynomial_trim_bounded_degree',
        f"forall {' '.join(params)}. ({trim('division_remainder_degree_trim')}) -> "
        f"({_le('R','d','division_remainder_degree_bound')}) -> ({_remainder_degree('p','rb','rc','R','d','division_remainder_degree')})",
        ('zero_or_succ','prime_field_polynomial_trim_represented_degree'),body,
        'An actual normalized remainder of length at most d is empty or has an actual represented degree strictly below d, even when d=0.',
    )
    return cut,length,degree


def _quotient_data(p: str, ab: str, ac: str, L: str, bb: str, bc: str,
                   d: str, b: str, k: str, q: str, qb: str, qc: str, tag: str) -> str:
    return _and(_at(bb,bc,'0',b,tag+'head'),_inv(p,b,k,tag+'inverse'),
                _quotient_length(L,d,q,tag+'length'),
                _quotient_prefix(p,k,ab,ac,bb,bc,f'S ({d})',qb,qc,q,tag+'execution'))


def _residual_data(p: str, ab: str, ac: str, L: str, bb: str, bc: str,
                   d: str, qb: str, qc: str, q: str,
                   pb: str, pc: str, ub: str, uc: str, t: str,
                   rb: str, rc: str, R: str, tag: str) -> str:
    return _and(_prefix(p,qb,qc,q,bb,bc,f'S ({d})',pb,pc,L,tag+'product'),
                _subtract(p,ab,ac,pb,pc,ub,uc,L,tag+'difference'),
                _trim(p,ub,uc,L,t,rb,rc,R,tag+'trim'))


def _quotient_data_exists_row(spec: Callable[...,Any]) -> Any:
    params=('p','ab','ac','L','bb','bc','d')
    body=_intro(*params,'hp','ha','hb')+_parts('hb',3)
    body+=('cases hb_right_right','cases hb_right_right_witness',)
    body+=(f"have hi : exists k. ({_inv('p','x','k','division_total_inverse')})",)
    body+=_call('prime_field_inverse_exists','p','x')+('exact hp',)
    body+=_call('matrix_rank_bounded_prefix_value','bb','bc','S d','p','0','x')
    body+=('exact hb_right_left','exists d','simp','exact hb_right_right_witness_left','exact hb_right_right_witness_right','cases hi')
    body+=(f"have hk : {_lt('x1','p','division_total_scalar_bound')}",'cases hi_witness','cases hi_witness_right','cases hi_witness_right_right','exact hi_witness_right_right_left')
    body+=(f"have hlength : exists q. ({_quotient_length('L','d','q','division_total_length')})",)
    body+=_call('polynomial_quotient_length_exists','L','d')+('cases hlength',)
    body+=(f"have hbounds : {_and(_le('x2','L','division_total_q_bound'),_le('L','x2+d','division_total_cover'))}",)
    body+=_call('polynomial_quotient_length_bounds','L','d','x2')+('exact hlength_witness','cases hbounds')
    body+=(f"have hquotient : exists qb qc. ({_quotient_prefix('p','x1','ab','ac','bb','bc','S d','qb','qc','x2','division_total_quotient')})",)
    body+=_call('prime_field_polynomial_quotient_prefix_exists','p','x1','ab','ac','bb','bc','S d','x2')+('exact hp','exact hk')
    body+=_intro('i','hindex')+_call('ha','i')+_call('lt_of_lt_of_le','i','x2','L')+('exact hindex','exact hbounds_left','cases hquotient','cases hquotient_witness')
    body+=('exists x','exists x1','exists x2','exists x3','exists x4','split','exact hb_right_right_witness_left',
           'split','exact hi_witness','split','exact hlength_witness','exact hquotient_witness_witness')
    return spec(
        'prime_field_polynomial_division_quotient_data_exists',
        f"forall {' '.join(params)}. ({_prime('p','division_quotient_data_prime')}) -> "
        f"({_coeff('p','ab','ac','L','division_quotient_data_input')}) -> "
        f"({_degree('p','bb','bc','S d','d','division_quotient_data_divisor')}) -> exists b k q qb qc. "
        f"({_quotient_data(*params,'b','k','q','qb','qc','division_quotient_data_result')})",
        ('prime_field_inverse_exists','matrix_rank_bounded_prefix_value','polynomial_quotient_length_exists',
         'polynomial_quotient_length_bounds','prime_field_polynomial_quotient_prefix_exists','lt_of_lt_of_le'),body,
        'Construct the actual divisor head, inverse, quotient length and quotient table as one small independently checked construction stage.',
    )


def _residual_data_exists_row(spec: Callable[...,Any]) -> Any:
    params=('p','ab','ac','L','bb','bc','d','qb','qc','q')
    body=_intro(*params,'hp','ha')
    body+=(f"have hproduct : exists pb pc. ({_prefix('p','qb','qc','q','bb','bc','S d','pb','pc','L','division_residual_product')})",)
    body+=_call('prime_field_convolution_prefix_exists','p','qb','qc','q','bb','bc','S d','L')+('intro hz',)
    body+=_call('prime_nonzero','p')+('exact hp','exact hz','cases hproduct','cases hproduct_witness')
    body+=(f"have hresidual : exists ub uc. ({_subtract('p','ab','ac','x','x1','ub','uc','L','division_residual_difference')})",)
    body+=_call('prime_field_polynomial_subtract_exists','p','ab','ac','x','x1','L')+('exact hp','exact ha')
    body+=_call('prime_field_convolution_prefix_bounded','p','qb','qc','q','bb','bc','S d','x','x1','L')
    body+=('exact hproduct_witness_witness','cases hresidual','cases hresidual_witness')
    body+=(f"have htrim : exists t rb rc R. ({_trim('p','x2','x3','L','t','rb','rc','R','division_residual_trim')})",)
    body+=_call('prime_field_polynomial_trim_exists','p','x2','x3','L')
    bounds=_and(_coeff('p','ab','ac','L','division_residual_source_bound'),_coeff('p','x','x1','L','division_residual_product_bound'),_coeff('p','x2','x3','L','division_residual_result_bound'))
    body+=(f'have hcanonical : {bounds}',)+_call('prime_field_polynomial_subtract_bounded','p','ab','ac','x','x1','x2','x3','L')
    body+=('exact hresidual_witness_witness','cases hcanonical','cases hcanonical_right','exact hcanonical_right_right')
    body+=tuple('cases htrim'+'_witness'*index for index in range(4))
    body+=tuple('exists '+value for value in ('x','x1','x2','x3','x4','x5','x6','x7'))
    body+=('split','exact hproduct_witness_witness','split','exact hresidual_witness_witness','exact htrim_witness_witness_witness_witness')
    return spec(
        'prime_field_polynomial_division_residual_data_exists',
        f"forall {' '.join(params)}. ({_prime('p','division_residual_data_prime')}) -> "
        f"({_coeff('p','ab','ac','L','division_residual_data_input')}) -> exists pb pc ub uc t rb rc R. "
        f"({_residual_data(*params,'pb','pc','ub','uc','t','rb','rc','R','division_residual_data_result')})",
        ('prime_field_convolution_prefix_exists','prime_nonzero','prime_field_polynomial_subtract_exists',
         'prime_field_convolution_prefix_bounded','prime_field_polynomial_trim_exists','prime_field_polynomial_subtract_bounded'),body,
        'Construct the actual ambient product, residual and normalized trim as a separate stage; none is supplied as an oracle or identity premise.',
    )


def _execution_exists_row(spec: Callable[...,Any]) -> Any:
    params=('p','ab','ac','L','bb','bc','d')
    body=_intro(*params,'hp','ha','hb')
    data=_quotient_data(*params,'b','k','q','qb','qc','division_total_quotient_data')
    body+=(f'have hquotient : exists b k q qb qc. ({data})',)
    body+=_call('prime_field_polynomial_division_quotient_data_exists',*params)+('exact hp','exact ha','exact hb')
    body+=tuple('cases hquotient'+'_witness'*index for index in range(5))
    hq='hquotient'+'_witness'*5
    body+=_parts(hq,4)
    data=_residual_data(*params,'x3','x4','x2','pb','pc','ub','uc','t','rb','rc','R','division_total_residual_data')
    body+=(f'have hresidual : exists pb pc ub uc t rb rc R. ({data})',)
    body+=_call('prime_field_polynomial_division_residual_data_exists',*params,'x3','x4','x2')+('exact hp','exact ha')
    body+=tuple('cases hresidual'+'_witness'*index for index in range(8))
    hr='hresidual'+'_witness'*8
    body+=_parts(hr,3)+_parts('hb',3)
    body+=('exists x3','exists x4','exists x2','exists x10','exists x11','exists x12','split','exact ha','split','exact hb_right_left','split','exact '+_part(hq,4,2),
           'exists x','exists x1','exists x5','exists x6','exists x7','exists x8','exists x9',
           'split','exact '+_part(hq,4,0),'split','exact '+_part(hq,4,1),'split','exact '+_part(hq,4,3),
           'split','exact '+_part(hr,3,0),'split','exact '+_part(hr,3,1),'exact '+_part(hr,3,2))
    return spec(
        'prime_field_polynomial_division_execution_exists',
        f"forall {' '.join(params)}. ({_prime('p','division_total_prime')}) -> "
        f"({_coeff('p','ab','ac','L','division_total_input')}) -> "
        f"({_degree('p','bb','bc','S d','d','division_total_divisor')}) -> exists qb qc q rb rc R. "
        f"({_division_execution(*params,'qb','qc','q','rb','rc','R','division_total_result')})",
        ('prime_field_polynomial_division_quotient_data_exists','prime_field_polynomial_division_residual_data_exists'),body,
        'Construct general quotient and normalized remainder codes from any canonical input and actual nonzero divisor, without assuming any output identity or degree bound.',
    )


def _execution_degree_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    params=('p','ab','ac','L','bb','bc','d','qb','qc','q','rb','rc','R')
    body=_intro(*params,'hp','h')+_parts('h',4)
    data='h_right_right_right'
    body+=tuple('cases '+data+'_witness'*index for index in range(7))
    inner=data+'_witness'*7
    body+=_parts(inner,6)
    body+=(f"have hbounds : {_and(_le('q','L','division_degree_q_bound'),_le('L','q+d','division_degree_cover'))}",)
    body+=_call('polynomial_quotient_length_bounds','L','d','q')+('exact h_right_right_left','cases hbounds')
    body+=_call('prime_field_polynomial_trim_bounded_degree','p','x4','x5','L','x6','rb','rc','R','d')+('exact '+_part(inner,6,5),)
    body+=_call('prime_field_polynomial_trim_zero_prefix_remainder_bound','p','x4','x5','L','x6','rb','rc','R','q','d')
    body+=('exact hbounds_left','exact hbounds_right')
    body+=_call('prime_field_polynomial_quotient_prefix_remainder_zero','p','x1','ab','ac','bb','bc','d','qb','qc','q','x','x2','x3','L','x4','x5')
    body+=('exact hp','exact '+_part(inner,6,0),'exact '+_part(inner,6,1),'exact '+_part(inner,6,2),
           'exact hbounds_left','exact '+_part(inner,6,3),'exact '+_part(inner,6,4),'exact '+_part(inner,6,5))
    degree=spec(
        'prime_field_polynomial_division_remainder_degree',
        f"forall {' '.join(params)}. ({_prime('p','division_degree_prime')}) -> "
        f"({_division_execution(*params,'division_degree_execution')}) -> "
        f"({_remainder_degree('p','rb','rc','R','d','division_degree_result')})",
        ('polynomial_quotient_length_bounds','prime_field_polynomial_trim_bounded_degree',
         'prime_field_polynomial_trim_zero_prefix_remainder_bound','prime_field_polynomial_quotient_prefix_remainder_zero'),body,
        'Every actual constructed remainder is empty or has genuinely represented degree below the divisor degree, including constant divisors and empty inputs.',
    )
    initial=params[:7]
    body=_intro(*initial,'hp','ha','hb')
    graph=_division_execution(*initial,'qb','qc','q','rb','rc','R','division_bounded_chosen')
    body+=(f'have h : exists qb qc q rb rc R. ({graph})',)
    body+=_call('prime_field_polynomial_division_execution_exists',*initial)+('exact hp','exact ha','exact hb')
    body+=tuple('cases h'+'_witness'*index for index in range(6))
    body+=tuple('exists '+name for name in ('x','x1','x2','x3','x4','x5'))+('split','exact h_witness_witness_witness_witness_witness_witness')
    body+=_call('prime_field_polynomial_division_remainder_degree',*initial,'x','x1','x2','x3','x4','x5')+('exact hp','exact h_witness_witness_witness_witness_witness_witness')
    exists=spec(
        'prime_field_polynomial_division_exists_with_remainder_bound',
        f"forall {' '.join(initial)}. ({_prime('p','division_bounded_prime')}) -> "
        f"({_coeff('p','ab','ac','L','division_bounded_input')}) -> "
        f"({_degree('p','bb','bc','S d','d','division_bounded_divisor')}) -> exists qb qc q rb rc R. "
        +_and(_division_execution(*params,'division_bounded_execution'),_remainder_degree('p','rb','rc','R','d','division_bounded_degree')),
        ('prime_field_polynomial_division_execution_exists','prime_field_polynomial_division_remainder_degree'),body,
        'Unconditionally construct an actual general division execution and derive its strict remainder-degree alternative; no theorem claims degree for zero.',
    )
    return degree,exists


def _proper_product_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    from peano_lab.library.prime_field_polynomial_convolution_candidate import _length

    body=_intro('L','d','q','h','hq')+('cases h','cases h_left','exfalso','apply hq','exact h_left_left',
           'cases h_right','right','split','exact hq','split','intro hz')
    body+=_call('succ_ne_zero','d')+('exact hz','trans S (q+d)','simp','congr','exact h_right_right')
    length=spec(
        'polynomial_quotient_length_product',
        f"forall L d q. ({_quotient_length('L','d','q','division_product_length_source')}) -> ~(q=0) -> "
        f"({_length('q','S d','L','division_product_length_result')})",
        ('succ_ne_zero',),body,
        'A positive constructed quotient has exactly the proper product length L with the length-S d divisor.',
    )
    params=('p','k','ab','ac','bb','bc','d','qb','qc','q','pb','pc','L')
    body=_intro(*params,'hlen','hpositive','hb','hq','hproduct')+('split',)
    body+=_call('prime_field_polynomial_quotient_prefix_bounded','p','k','ab','ac','bb','bc','S d','qb','qc','q')
    body+=('exact hq','split','exact hb','split')+_call('polynomial_quotient_length_product','L','d','q')
    body+=('exact hlen','exact hpositive','exact hproduct')
    proper=spec(
        'prime_field_polynomial_quotient_proper_product',
        f"forall {' '.join(params)}. ({_quotient_length('L','d','q','division_product_chosen_length')}) -> ~(q=0) -> "
        f"({_coeff('p','bb','bc','S d','division_product_divisor')}) -> "
        f"({_quotient_prefix('p','k','ab','ac','bb','bc','S d','qb','qc','q','division_product_quotient')}) -> "
        f"({_prefix('p','qb','qc','q','bb','bc','S d','pb','pc','L','division_product_ambient')}) -> "
        f"({_convolution('p','qb','qc','q','bb','bc','S d','pb','pc','L','division_product_actual')})",
        ('prime_field_polynomial_quotient_prefix_bounded','polynomial_quotient_length_product'),body,
        'For a nonempty quotient the actual ambient product is the actual proper polynomial convolution, not a Horner or synthetic surrogate.',
    )
    params=('p','qb','qc','bb','bc','M','pb','pc','L')
    body=_intro(*params,'hp','h','i','hi')
    point=_and(_at('pb','pc','i','r','division_empty_product_entry'),
               _coefficient('p','qb','qc','0','bb','bc','M','i','r','division_empty_product_coefficient'))
    body+=(f'have hv : exists r. {point}',)+_call('h','i')+('exact hi','cases hv','cases hv_witness','have hz : x=0')
    body+=_call('prime_field_convolution_coefficient_zero_left','p','qb','qc','0','bb','bc','M','i','x')+('exact hp',)
    body+=_intro('j','hj')+('exfalso',)+_call('lt_not_le','j','0')+('exact hj',)+_call('zero_le','j')+('exact hv_witness_right',)
    body+=_rewrite_all('hz',_at('pb','pc','i','x','division_empty_product_rewrite'),'x','hv_witness_left')+('exact hv_witness_left',)
    empty=spec(
        'prime_field_convolution_prefix_empty_left_zero',
        f"forall {' '.join(params)}. ~(p=0) -> "
        f"({_prefix('p','qb','qc','0','bb','bc','M','pb','pc','L','division_empty_product_source')}) -> "
        f"({_repeat('pb','pc','0','L','division_empty_product_result')})",
        ('prime_field_convolution_coefficient_zero_left','lt_not_le','zero_le'),body,
        'An actual ambient convolution prefix of an empty quotient consists entirely of zero coefficients, regardless of its requested length.',
    )
    return length,proper,empty


def _coefficient_identity(p: str, ab: str, ac: str, L: str, bb: str, bc: str,
                          d: str, qb: str, qc: str, q: str, rb: str, rc: str,
                          R: str, tag: str) -> str:
    pb,pc,ub,uc,t=('pfd_identity_'+role+'_'+tag for role in ('pb','pc','ub','uc','t'))
    product=(f"({_and(f'({q})=0',_repeat(pb,pc,'0',L,tag+'empty'))}) \\/ "
             f"({_and(f'~(({q})=0)',_convolution(p,qb,qc,q,bb,bc,f'S ({d})',pb,pc,L,tag+'product'))})")
    return f'exists {pb} {pc} {ub} {uc} {t}. '+_and(
        product,_polynomial_add(p,pb,pc,ub,uc,ab,ac,L,tag+'addition'),
        _trim(p,ub,uc,L,t,rb,rc,R,tag+'remainder'))


def _identity_row(spec: Callable[...,Any]) -> Any:
    params=('p','ab','ac','L','bb','bc','d','qb','qc','q','rb','rc','R')
    body=_intro(*params,'hp','h')+_parts('h',4)
    data='h_right_right_right'
    body+=tuple('cases '+data+'_witness'*index for index in range(7))
    inner=data+'_witness'*7
    body+=_parts(inner,6)+tuple('exists '+name for name in ('x2','x3','x4','x5','x6'))
    body+=('split','have hq : q=0 \\/ ~(q=0)')+_call('eq_decidable','q','0')
    body+=('cases hq','left','split','exact hq_left')
    body+=_call('prime_field_convolution_prefix_empty_left_zero','p','qb','qc','bb','bc','S d','x2','x3','L')+('intro hz',)
    body+=_call('prime_nonzero','p')+('exact hp','exact hz',)
    prefix=_prefix('p','qb','qc','q','bb','bc','S d','x2','x3','L','division_identity_empty_rewrite')
    body+=_rewrite_all('hq_left',prefix,'q',_part(inner,6,3))+('exact '+_part(inner,6,3),'right','split','exact hq_right')
    body+=_call('prime_field_polynomial_quotient_proper_product','p','x1','ab','ac','bb','bc','d','qb','qc','q','x2','x3','L')
    body+=('exact h_right_right_left','exact hq_right','exact h_right_left','exact '+_part(inner,6,2),'exact '+_part(inner,6,3),'split')
    body+=_call('prime_field_polynomial_subtract_recover_add','p','ab','ac','x2','x3','x4','x5','L')
    body+=('exact '+_part(inner,6,4),'exact '+_part(inner,6,5))
    return spec(
        'prime_field_polynomial_division_coefficient_identity',
        f"forall {' '.join(params)}. ({_prime('p','division_identity_prime')}) -> "
        f"({_division_execution(*params,'division_identity_execution')}) -> ({_coefficient_identity(*params,'division_identity_result')})",
        ('eq_decidable','prime_field_convolution_prefix_empty_left_zero','prime_nonzero',
         'prime_field_polynomial_quotient_proper_product','prime_field_polynomial_subtract_recover_add'),body,
        'Derive the actual coefficient identity A=P+U, where P is the proper product Q*B (or padded empty product), and the actual trim makes U precisely a leading-zero representation of the normalized remainder.',
    )


def make_prime_field_polynomial_division_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (_inverse_step_row(spec),_step_transport_row(spec),*_prefix_base_rows(spec),
            _append_row(spec),_exists_row(spec),*_matching_rows(spec),*_length_rows(spec),
            *_trim_bound_rows(spec),_quotient_data_exists_row(spec),_residual_data_exists_row(spec),
            _execution_exists_row(spec),*_execution_degree_rows(spec),*_proper_product_rows(spec),_identity_row(spec))


__all__ = ['prime_field_polynomial_quotient_step_relation',
           'prime_field_polynomial_quotient_prefix_relation',
           'prime_field_polynomial_quotient_length_relation',
           'prime_field_polynomial_division_execution_relation',
           'make_prime_field_polynomial_division_candidate_theorems']
