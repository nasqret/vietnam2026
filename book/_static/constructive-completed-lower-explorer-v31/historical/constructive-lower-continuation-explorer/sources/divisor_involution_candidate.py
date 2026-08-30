"""Constructive positive divisor quotients and actual finite involutions.

The complement graph uses a witnessed product n=d*q on positive divisors,
and the identity at zero and nondivisors.  A real beta prefix is constructed
by ordinary finite induction; neither a quotient oracle nor a permutation
witness is included among its input assumptions.
"""

from __future__ import annotations

from typing import Any, Callable

from .prime_factorization_permutation_candidate import _bounded, _injective, _permutation, _preserve
from .prime_valuation_support_candidate import (
    _and, _at, _call, _cases, _dvd, _intro, _le, _lt, _parts, _public, _rewrite,
)


def _complement(n: str, d: str, q: str, tag: str) -> str:
    keep = _and(f"~(({d})=0)", f"({n})=({d})*({q})")
    omit = _and(f"({d})=0 \\/ ~({_dvd(d,n,tag+'nondivisor')})", f"({q})=({d})")
    return f"({keep}) \\/ ({omit})"


def _map_prefix(graph: Callable[..., str], arguments: tuple[str, ...],
                b: str, c: str, l: str, tag: str) -> str:
    i, q = "dvi_index_" + tag, "dvi_value_" + tag
    return (f"forall {i}. ({_lt(i,l,tag+'domain')}) -> exists {q}. "
            + _and(_at(b,c,i,q,tag+'entry'), graph(*arguments,i,q,tag+'graph')))


def _prefix(n: str, b: str, c: str, l: str, tag: str) -> str:
    return _map_prefix(_complement,(n,),b,c,l,tag)


def positive_divisor_complement_relation(n: str, d: str, q: str, *, tag: str,
                                         variables: tuple[str, ...]) -> str:
    """Actual positive-divisor quotient, extended by identity off that domain."""
    return _public(_complement,(n,d,q),tag=tag,variables=variables)


def divisor_complement_prefix_relation(n: str, b: str, c: str, l: str, *, tag: str,
                                      variables: tuple[str, ...]) -> str:
    """A real beta map records the complement at every index i<l."""
    return _public(_prefix,(n,b,c,l),tag=tag,variables=variables)


def _prefix_choice_script(parameters: tuple[str, ...], graph: Callable[..., str],
                          prefix: Callable[..., str], total_name: str,
                          guards: tuple[str, ...]) -> tuple[str, ...]:
    """Only a guide emitting ordinary tactics; every resulting body is checked."""
    body = _intro(*parameters,'l') + ('induction l',) + _intro(*guards)
    body += ('exists 0','exists 0') + _intro('i','hi') + ('exfalso',)
    body += _call('factor_permutation_below_zero_impossible','i') + ('exact hi',)
    body += _intro(*guards)
    body += (f"have hprev : exists b c. ({prefix(*parameters,'b','c','l','choice_previous')})",'apply IH')
    body += tuple('exact '+guard for guard in guards) + _cases('hprev',2)
    body += (f"have hv : exists v. ({graph(*parameters,'l','v','choice_value')})",)
    body += _call(total_name,*parameters,'l') + tuple('exact '+guard for guard in guards) + ('cases hv',)
    extension = _and(_at('b','c','l','x2','choice_last'),_preserve('x','x1','b','c','l','choice_preserve'))
    body += (f'have hext : exists b c. ({extension})',)
    body += _call('beta_prefix_extend','l','x','x1','x2') + _cases('hext',2)
    body += ('cases hext_witness_witness','exists x3','exists x4') + _intro('i','hi')
    body += (f"have hc : i=l \\/ ({_lt('i','l','choice_cases')})",)
    body += _call('finite_lt_succ_eq_or_lt','l','i') + ('exact hi','cases hc')
    last = f"exists v. ({_and(_at('x3','x4','i','v','choice_rewrite_entry'),graph(*parameters,'i','v','choice_rewrite_graph'))})"
    body += _rewrite('hc_left',last,'i')
    body += ('exists x2','split','exact hext_witness_witness_left','exact hv_witness')
    body += (f"have hold : exists v. ({_and(_at('x','x1','i','v','choice_old_entry'),graph(*parameters,'i','v','choice_old_graph'))})",)
    body += _call('hprev_witness_witness','i') + ('exact hc_right','cases hold','cases hold_witness','exists x5','split')
    body += _call('hext_witness_witness_right','i','x5')
    body += ('exact hc_right','exact hold_witness_left','exact hold_witness_right')
    return body


def _prefix_lookup_script(parameters: tuple[str, ...], graph: Callable[..., str]) -> tuple[str, ...]:
    body = _intro(*parameters,'b','c','l','i','q','hp','hi','hat')
    body += (f"have hv : exists v. ({_and(_at('b','c','i','v','lookup_entry'),graph(*parameters,'i','v','lookup_graph'))})",)
    body += _call('hp','i') + ('exact hi','cases hv','cases hv_witness','have heq : q=x')
    body += _call('beta_at_unique','b','c','i','q','x') + ('exact hat','exact hv_witness_left')
    body += _rewrite('heq',graph(*parameters,'i','q','lookup_rewrite'),'q') + ('exact hv_witness_right',)
    return body


def _quotient_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    properties = _and('n=d*q','~(q=0)',_dvd('q','n','quotient_divisor'),_le('q','n','quotient_bound'),
                      'forall r. n=d*r -> r=q')
    body = _intro('n','d','hn','hd') + ('cases hd','exists x','split','exact hd_witness','split')
    body += ('intro hqzero',)+_call('factor_nonzero_right','n','d','x') + ('exact hn','exact hd_witness','exact hqzero','split','exists d')
    body += ('trans d*x','exact hd_witness','apply mul_comm','split')
    body += _call('divisor_le_nonzero','x','n') + ('exact hn','exists d','trans d*x','exact hd_witness','apply mul_comm')
    body += _intro('r','hr') + _call('mul_left_cancel_nonzero','d','r','x')
    body += ('intro hdzero',)+_call('factor_nonzero_left','n','d','x') + ('exact hn','exact hd_witness','exact hdzero','trans n','symm','exact hr','exact hd_witness')
    return (
        spec('positive_divisor_quotient_exists_unique',
             f"forall n d. ~(n=0) -> ({_dvd('d','n','quotient_input')}) -> exists q. ({properties})",
             ('factor_nonzero_right','mul_comm','divisor_le_nonzero','mul_left_cancel_nonzero','factor_nonzero_left'),body,
             'Every divisor of a positive input has a unique actual positive quotient, itself a divisor bounded by the input.'),
        spec('divisor_complement_exists',
             f"forall n d. ~(n=0) -> exists q. ({_complement('n','d','q','exists_result')})",
             ('eq_decidable','multiple_decidable_nonzero'),
             _intro('n','d','hn')+('have hz : d=0 \\/ ~(d=0)',)+_call('eq_decidable','d','0')
             +('cases hz','exists d','right','split','left','exact hz_left','refl',
               f"have hd : ({_dvd('d','n','exists_divisor')}) \\/ ~({_dvd('d','n','exists_nondivisor')})")
             +_call('multiple_decidable_nonzero','d','n')+('exact hz_right','cases hd','cases hd_left','exists x','left','split',
                 'exact hz_right','exact hd_left_witness','exists d','right','split','right','exact hd_right','refl'),
             'Decide zero and divisibility constructively, extracting a real quotient only in the positive-divisor branch.'),
        spec('divisor_complement_functional',
             f"forall n d q r. ({_complement('n','d','q','functional_first')}) -> ({_complement('n','d','r','functional_second')}) -> q=r",
             ('mul_left_cancel_nonzero',),
             _intro('n','d','q','r','hq','hr')+('cases hq','cases hq_left','cases hr','cases hr_left')
             +_call('mul_left_cancel_nonzero','d','q','r')+('exact hq_left_left','trans n','symm','exact hq_left_right','exact hr_left_right',
                 'cases hr_right','exfalso','cases hr_right_left','apply hq_left_left','exact hr_right_left_left',
                 'apply hr_right_left_right','exists q','exact hq_left_right','cases hq_right','cases hr','cases hr_left',
                 'exfalso','cases hq_right_left','apply hr_left_left','exact hq_right_left_left','apply hq_right_left_right',
                 'exists r','exact hr_left_right','cases hr_right','trans d','exact hq_right_right','symm','exact hr_right_right'),
             'The actual quotient and identity branches are disjoint and determine one output; beta-code equality is not assumed.'),
        spec('divisor_complement_positive_equation',
             f"forall n d q. ~(d=0) -> ({_dvd('d','n','equation_divisor')}) -> ({_complement('n','d','q','equation_graph')}) -> n=d*q",
             (),
             _intro('n','d','q','hd','hdiv','hq')+('cases hq','cases hq_left','exact hq_left_right','cases hq_right',
                 'exfalso','cases hq_right_left','apply hd','exact hq_right_left_left','apply hq_right_left_right','exact hdiv'),
             'At every genuine positive divisor the complement output satisfies n=d*q; the identity convention cannot supply that branch.'),
        spec('divisor_complement_symmetric',
             f"forall n d q. ~(n=0) -> ({_complement('n','d','q','symmetric_source')}) -> ({_complement('n','q','d','symmetric_target')})",
             ('factor_nonzero_right','mul_comm'),
             _intro('n','d','q','hn','hq')+('cases hq','cases hq_left','left','split','intro hqzero')
             +_call('factor_nonzero_right','n','d','q')+('exact hn','exact hq_left_right','exact hqzero','trans d*q','exact hq_left_right','apply mul_comm','cases hq_right')
             +_rewrite('hq_right_right',_complement('n','q','d','symmetric_rewrite'),'q')
             +('right','split','exact hq_right_left','refl'),
             'For positive n the actual complementary quotient is reversible; zero and nondivisors remain fixed.'),
        spec('divisor_complement_bounded',
             f"forall n d q. ~(n=0) -> ({_le('d','n','bounded_input')}) -> ({_complement('n','d','q','bounded_graph')}) -> ({_le('q','n','bounded_result')})",
             ('divisor_le_nonzero','mul_comm'),
             _intro('n','d','q','hn','hd','hq')+('cases hq','cases hq_left')
             +_call('divisor_le_nonzero','q','n')+('exact hn','exists d','trans d*q','exact hq_left_right','apply mul_comm','cases hq_right')
             +_rewrite('hq_right_right',_le('q','n','bounded_rewrite'),'q')+('exact hd',),
             'Divisor complementation stays in the exact inclusive interval 0..n, including its explicitly fixed omitted indices.'),
    )


def _map_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('n','b','c','hn','hp')
    body += (f"have hb : {_bounded('b','c','S n','permutation_bounded')}",) + _intro('i','hi')
    body += (f"have hv : exists q. ({_and(_at('b','c','i','q','permutation_at'),_complement('n','i','q','permutation_comp'))})",)
    body += _call('hp','i')+('exact hi','cases hv','cases hv_witness','exists x','split','exact hv_witness_left')
    body += _call('succ_le_succ','x','n')+_call('divisor_complement_bounded','n','i','x')+('exact hn',)
    body += _call('le_of_succ_le_succ','i','n')+('exact hi','exact hv_witness_right')
    body += (f"have hinj : {_injective('b','c','S n','permutation_injective')}",)+_intro('i','j','a','hi','hj','hia','hja')
    body += _call('divisor_complement_functional','n','a','i','j')
    for i,hindex,hat in (('i','hi','hia'),('j','hj','hja')):
        body += _call('divisor_complement_symmetric','n',i,'a')+('exact hn',)
        body += _call('divisor_complement_prefix_lookup','n','b','c','S n',i,'a')+('exact hp','exact '+hindex,'exact '+hat)
    body += ('split','exact hb','split','exact hinj')+_call('finite_bounded_injective_surjective','S n','b','c')+('exact hb','exact hinj')
    return (
        spec('divisor_complement_prefix_exists',
             f"forall n l. ~(n=0) -> exists b c. ({_prefix('n','b','c','l','prefix_exists')})",
             ('factor_permutation_below_zero_impossible','divisor_complement_exists','beta_prefix_extend','finite_lt_succ_eq_or_lt'),
             _prefix_choice_script(('n',),_complement,_prefix,'divisor_complement_exists',('hn',)),
             'Finite HA induction constructs a genuine beta prefix of quotient values, rather than assuming a finite-choice or coding oracle.'),
        spec('divisor_complement_prefix_lookup',
             f"forall n b c l i q. ({_prefix('n','b','c','l','lookup_prefix')}) -> ({_lt('i','l','lookup_index')}) -> "
             f"({_at('b','c','i','q','lookup_beta')}) -> ({_complement('n','i','q','lookup_result')})",
             ('beta_at_unique',),_prefix_lookup_script(('n',),_complement),
             'Every actual beta lookup in the constructed finite window has the literal complementary-divisor graph.'),
        spec('divisor_complement_prefix_permutation',
             f"forall n b c. ~(n=0) -> ({_prefix('n','b','c','S n','permutation_prefix')}) -> ({_permutation('b','c','S n','permutation_result')})",
             ('succ_le_succ','divisor_complement_bounded','le_of_succ_le_succ','divisor_complement_functional',
              'divisor_complement_symmetric','divisor_complement_prefix_lookup','finite_bounded_injective_surjective'),body,
             'The real S n-entry complement code is bounded and injective by its proved involution; constructive finite surjectivity yields a genuine permutation.'),
        spec('positive_divisor_involution_exists',
             f"forall n. ~(n=0) -> exists b c. ({_prefix('n','b','c','S n','involution_prefix')}) /\\ ({_permutation('b','c','S n','involution_permutation')})",
             ('divisor_complement_prefix_exists','divisor_complement_prefix_permutation'),
             _intro('n','hn')+(f"have hp : exists b c. ({_prefix('n','b','c','S n','involution_construct')})",)
             +_call('divisor_complement_prefix_exists','n','S n')+('exact hn',)+_cases('hp',2)
             +('exists x','exists x1','split','exact hp_witness_witness')
             +_call('divisor_complement_prefix_permutation','n','x','x1')+('exact hn','exact hp_witness_witness'),
             'Every positive natural has an actually constructed finite divisor-complement permutation, with exact quotient equations on positive divisors.'),
    )


def _decoded_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    involution = _intro('n','b','c','i','q','hn','hp','hi','hat')
    involution += (f"have hcomp : {_complement('n','i','q','decoded_complement')}",)
    involution += _call('divisor_complement_prefix_lookup','n','b','c','S n','i','q')+('exact hp',)
    involution += _call('succ_le_succ','i','n')+('exact hi','exact hat')
    involution += (f"have hq : {_le('q','n','decoded_bound')}",)
    involution += _call('divisor_complement_bounded','n','i','q')+('exact hn','exact hi','exact hcomp')
    involution += (f"have hnext : exists r. ({_and(_at('b','c','q','r','decoded_next'),_complement('n','q','r','decoded_next_graph'))})",)
    involution += _call('hp','q')+_call('succ_le_succ','q','n')+('exact hq','cases hnext','cases hnext_witness','have heq : x=i')
    involution += _call('divisor_complement_functional','n','q','x','i')+('exact hnext_witness_right',)
    involution += _call('divisor_complement_symmetric','n','i','q')+('exact hn','exact hcomp')
    involution += _rewrite('heq',_at('b','c','q','x','decoded_rewrite'),'x','hnext_witness_left')+('exact hnext_witness_left',)

    quotient = _intro('n','b','c','d','q','hn','hp','hd','heq')
    quotient += (f"have hbound : {_lt('d','S n','decoded_quotient_bound')}",)
    quotient += _call('succ_le_succ','d','n')+_call('divisor_le_nonzero','d','n')+('exact hn','exists q','exact heq')
    quotient += (f"have hv : exists r. ({_and(_at('b','c','d','r','decoded_quotient_entry'),_complement('n','d','r','decoded_quotient_graph'))})",)
    quotient += _call('hp','d')+('exact hbound','cases hv','cases hv_witness','have hvalue : x=q')
    quotient += _call('divisor_complement_functional','n','d','x','q')+('exact hv_witness_right','left','split','exact hd','exact heq')
    quotient += _rewrite('hvalue',_at('b','c','d','x','decoded_quotient_rewrite'),'x','hv_witness_left')+('exact hv_witness_left',)
    return (
        spec('divisor_complement_prefix_involution',
             f"forall n b c i q. ~(n=0) -> ({_prefix('n','b','c','S n','decoded_prefix')}) -> ({_le('i','n','decoded_input_bound')}) -> "
             f"({_at('b','c','i','q','decoded_first')}) -> ({_at('b','c','q','i','decoded_second')})",
             ('divisor_complement_prefix_lookup','succ_le_succ','divisor_complement_bounded',
              'divisor_complement_functional','divisor_complement_symmetric'),involution,
             'Decoding the constructed finite map twice returns the original index, with the intermediate index proved to remain in bounds.'),
        spec('divisor_complement_prefix_positive_quotient',
             f"forall n b c d q. ~(n=0) -> ({_prefix('n','b','c','S n','decoded_quotient_prefix')}) -> ~(d=0) -> n=d*q -> ({_at('b','c','d','q','decoded_quotient_result')})",
             ('succ_le_succ','divisor_le_nonzero','divisor_complement_functional'),quotient,
             'The actual beta code at a positive divisor is precisely its witnessed quotient, not merely an unspecified bounded permutation image.'),
    )


def make_divisor_involution_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return _quotient_rows(spec) + _map_rows(spec) + _decoded_rows(spec)


__all__ = ['positive_divisor_complement_relation','divisor_complement_prefix_relation',
           'make_divisor_involution_candidate_theorems']
