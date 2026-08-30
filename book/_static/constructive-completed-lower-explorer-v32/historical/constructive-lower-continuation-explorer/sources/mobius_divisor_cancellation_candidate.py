"""Actual prime toggles toward cancellation of independently defined Möbius values.

The raw graph adds a fresh prime, removes a single prime factor, and fixes
prime-square multiples.  The finite divisor graph is the identity outside
positive divisors.  No sum identity is included in either relation.
"""

from __future__ import annotations

from typing import Any, Callable

from .divisor_involution_candidate import _map_prefix, _prefix_choice_script, _prefix_lookup_script
from .divisor_mask_candidate import _divisor_sum, _mask, _positive_equal
from .divisor_sum_reindex_candidate import _reindex
from .divisor_sum_table_candidate import _components, _pack, _rep, _signed_sum, _table, _table_at, _table_equal
from .mobius_prime_step_candidate import _negate
from .mobius_table_candidate import _mu_table
from .mobius_value_candidate import _mu
from .prime_factorization_permutation_candidate import _bounded, _injective, _permutation
from .prime_valuation_support_candidate import (
    _and, _at, _call, _cases, _dvd, _intro, _le, _lt, _parts, _prime, _public, _rewrite,
)
from .squarefree_decomposition_candidate import _cop


def _toggle(p: str, d: str, e: str, tag: str) -> str:
    add = _and(f'~({_dvd(p,d,tag+"fresh_input")})',f'({e})=({p})*({d})')
    remove = _and(f'({d})=({p})*({e})',f'~({_dvd(p,e,tag+"fresh_output")})')
    fixed = _and(_dvd(f'({p})*({p})',d,tag+'square'),f'({e})=({d})')
    return f'({add}) \\/ (({remove}) \\/ ({fixed}))'


def _divisor_toggle(n: str, p: str, d: str, e: str, tag: str) -> str:
    active = _and(f'~(({d})=0)',_dvd(d,n,tag+'divisor'),_toggle(p,d,e,tag+'toggle'))
    fixed = _and(f'({d})=0 \\/ ~({_dvd(d,n,tag+"nondivisor")})',f'({e})=({d})')
    return f'({active}) \\/ ({fixed})'


def _prefix(n: str, p: str, b: str, c: str, l: str, tag: str) -> str:
    return _map_prefix(_divisor_toggle,(n,p),b,c,l,tag)


def _pointwise_negate(F: str, G: str, l: str, tag: str) -> str:
    i,a,b=('mdc_'+role+'_'+tag for role in ('index','source','target'))
    return (f'forall {i} {a} {b}. ({_lt(i,l,tag+"bound")}) -> ({_table_at(F,i,a,tag+"first")}) -> '
            f'({_table_at(G,i,b,tag+"second")}) -> ({_negate(a,b,tag+"negation")})')


def _positive_values(N: str, F: str, tag: str) -> str:
    d,z='mdc_positive_index_'+tag,'mdc_positive_value_'+tag
    return (f'forall {d} {z}. ~({d}=0) -> ({_le(d,N,tag+"bound")}) -> '
            f'({_table_at(F,d,z,tag+"entry")}) -> ({_mu(d,z,tag+"mobius")})')


def prime_factor_toggle_relation(p: str, d: str, e: str, *, tag: str,
                                 variables: tuple[str, ...]) -> str:
    """Add/remove one fresh p; fix actual p-squared multiples."""
    return _public(_toggle,(p,d,e),tag=tag,variables=variables)


def divisor_prime_toggle_relation(n: str, p: str, d: str, e: str, *, tag: str,
                                  variables: tuple[str, ...]) -> str:
    """Prime-factor toggle on positive divisors, identity everywhere else."""
    return _public(_divisor_toggle,(n,p,d,e),tag=tag,variables=variables)


def divisor_prime_toggle_prefix_relation(n: str, p: str, b: str, c: str, l: str, *, tag: str,
                                         variables: tuple[str, ...]) -> str:
    """An actual finite beta map records every prime-toggle output."""
    return _public(_prefix,(n,p,b,c,l),tag=tag,variables=variables)


def signed_arithmetic_table_negation_relation(F: str, G: str, l: str, *, tag: str,
                                              variables: tuple[str, ...]) -> str:
    """Actual signed lookups are opposite on i<l; table validity is separate."""
    return _public(_pointwise_negate,(F,G,l),tag=tag,variables=variables)


def mobius_positive_table_values_relation(N: str, F: str, *, tag: str,
                                          variables: tuple[str, ...]) -> str:
    """Only positive entries through N are μ; no restriction is placed on F(0)."""
    return _public(_positive_values,(N,F),tag=tag,variables=variables)


def _scalar_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    square = _intro('p','d','q','hp','heq','hs')+('cases hs','exists x',)
    square += _call('mul_left_cancel_nonzero','p','q','p*x')+('exact hp','trans d','symm','exact heq',
                'trans (p*p)*x','exact hs_witness','apply mul_assoc')

    fresh = _intro('p','n','d','hp','hpn','hdn','hfresh')
    fresh += (f"have hc : {_cop('p','d','fresh_coprime')}",
              f"have hcases : ({_cop('p','d','fresh_coprime_cases')}) \\/ ({_dvd('p','d','fresh_divisor_cases')})")
    fresh += _call('prime_coprime_or_divides','p','d')+('exact hp','cases hcases','exact hcases_left','exfalso','apply hfresh','exact hcases_right','cases hdn',
                f"have hq : {_dvd('p','x','fresh_quotient')}")
    fresh += _call('gauss_coprime_cancel','p','d','x')+('exact hc',)
    fresh += _rewrite('hdn_witness',_dvd('p','n','fresh_rewrite'),'n','hpn')+('exact hpn','cases hq','exists x1','trans d*x','exact hdn_witness',
                 'trans d*(p*x1)','rewrite hq_witness','refl','trans p*(d*x1)','apply natural_mul_swap_right_tail','symm','apply mul_assoc')
    return (
        spec('prime_toggle_square_quotient_divides',
             f"forall p d q. ~(p=0) -> d=p*q -> ({_dvd('p*p','d','square_input')}) -> ({_dvd('p','q','square_output')})",
             ('mul_left_cancel_nonzero','mul_assoc'),square,
             'Cancel one actual nonzero factor in a witnessed square divisor; the quotient is genuinely divisible by p.'),
        spec('prime_toggle_fresh_divisor_product',
             f"forall p n d. ({_prime('p','fresh_prime')}) -> ({_dvd('p','n','fresh_p_divisor')}) -> ({_dvd('d','n','fresh_d_divisor')}) -> "
             f"~({_dvd('p','d','fresh_guard')}) -> ({_dvd('p*d','n','fresh_product_divisor')})",
             ('prime_coprime_or_divides','gauss_coprime_cancel','natural_mul_swap_right_tail','mul_assoc'),fresh,
             'A prime divisor of n not dividing d can be adjoined to an actual divisor d: Euclid cancellation constructs the required quotient.'),
    )


def _toggle_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    total = _intro('p','d','hp')+(f"have hd : ({_dvd('p','d','total_yes')}) \\/ ~({_dvd('p','d','total_no')})",)
    total += _call('multiple_decidable_nonzero','p','d')+('exact hp','cases hd','cases hd_left',
               f"have hq : ({_dvd('p','x','total_quotient_yes')}) \\/ ~({_dvd('p','x','total_quotient_no')})")
    total += _call('multiple_decidable_nonzero','p','x')+('exact hp','cases hq','cases hq_left','exists d','right','right','split','exists x1',
               'trans p*x','exact hd_left_witness','trans p*(p*x1)','rewrite hq_left_witness','refl','symm','apply mul_assoc','refl',
               'exists x','right','left','split','exact hd_left_witness','exact hq_right',
               'exists p*d','left','split','exact hd_right','refl')

    functional = _intro('p','d','e','f','hp','he','hf')
    functional += ('cases he','cases he_left','cases hf','cases hf_left','trans p*d','exact he_left_right','symm','exact hf_left_right',
                   'cases hf_right','cases hf_right_left','exfalso','apply he_left_left','exists f','exact hf_right_left_left',
                   'cases hf_right_right','exfalso','apply he_left_left')
    functional += _call('multiple_trans','p*p','p','d')+('exact hf_right_right_left','exists p','refl',
                   'cases he_right','cases he_right_left','cases hf','cases hf_left','exfalso','apply hf_left_left','exists e','exact he_right_left_left',
                   'cases hf_right','cases hf_right_left')
    functional += _call('mul_left_cancel_nonzero','p','e','f')+('exact hp','trans d','symm','exact he_right_left_left','exact hf_right_left_left',
                   'cases hf_right_right','exfalso','apply he_right_left_right')
    functional += _call('prime_toggle_square_quotient_divides','p','d','e')+('exact hp','exact he_right_left_left','exact hf_right_right_left',
                   'cases he_right_right','cases hf','cases hf_left','exfalso','apply hf_left_left')
    functional += _call('multiple_trans','p*p','p','d')+('exact he_right_right_left','exists p','refl',
                   'cases hf_right','cases hf_right_left','exfalso','apply hf_right_left_right')
    functional += _call('prime_toggle_square_quotient_divides','p','d','f')+('exact hp','exact hf_right_left_left','exact he_right_right_left',
                   'cases hf_right_right','trans d','exact he_right_right_right','symm','exact hf_right_right_right')

    symmetric = _intro('p','d','e','h')+('cases h','cases h_left','right','left','split','exact h_left_right','exact h_left_left',
                  'cases h_right','cases h_right_left','left','split','exact h_right_left_right','exact h_right_left_left','cases h_right_right')
    symmetric += _rewrite('h_right_right_right',_toggle('p','e','d','symmetric_rewrite'),'e')
    symmetric += ('right','right','split','exact h_right_right_left','refl')

    positive = _intro('p','d','e','hp','hd','he','hz')+('cases he','cases he_left',)
    positive += _call('mul_ne_zero','p','d')+('exact hp','exact hd',)
    positive += _rewrite('he_left_right','e=0','e','hz')+('exact hz','cases he_right','cases he_right_left')
    positive += _call('factor_nonzero_right','d','p','e')+('exact hd','exact he_right_left_left','exact hz','cases he_right_right','apply hd')
    positive += _rewrite('he_right_right_right','e=0','e','hz')+('exact hz',)

    divisor = _intro('p','n','d','e','hp','hpn','hdn','he')+('cases he','cases he_left',)
    divisor += _rewrite('he_left_right',_dvd('e','n','divisor_add_rewrite'),'e')
    divisor += _call('prime_toggle_fresh_divisor_product','p','n','d')+('exact hp','exact hpn','exact hdn','exact he_left_left',
                 'cases he_right','cases he_right_left')
    divisor += _call('multiple_trans','d','e','n')+('exact hdn','exists p','trans p*e','exact he_right_left_left','apply mul_comm','cases he_right_right')
    divisor += _rewrite('he_right_right_right',_dvd('e','n','divisor_fixed_rewrite'),'e')+('exact hdn',)
    return (
        spec('prime_factor_toggle_exists',
             f"forall p d. ~(p=0) -> exists e. ({_toggle('p','d','e','toggle_exists')})",
             ('multiple_decidable_nonzero','mul_assoc'),total,
             'Two constructive divisibility decisions supply the added factor, a genuine quotient, or a fixed prime-square multiple.'),
        spec('prime_factor_toggle_functional',
             f"forall p d e f. ~(p=0) -> ({_toggle('p','d','e','toggle_functional_first')}) -> ({_toggle('p','d','f','toggle_functional_second')}) -> e=f",
             ('multiple_trans','mul_left_cancel_nonzero','prime_toggle_square_quotient_divides'),functional,
             'Fresh, singly divisible and square-divisible branches are disjoint; cancellation of a nonzero p proves exact output uniqueness.'),
        spec('prime_factor_toggle_symmetric',
             f"forall p d e. ({_toggle('p','d','e','toggle_symmetric_first')}) -> ({_toggle('p','e','d','toggle_symmetric_second')})",
             (),symmetric,
             'Adding and removing a fresh factor reverse each other, while the witnessed square-divisible branch is fixed.'),
        spec('prime_factor_toggle_positive',
             f"forall p d e. ~(p=0) -> ~(d=0) -> ({_toggle('p','d','e','toggle_positive_graph')}) -> ~(e=0)",
             ('mul_ne_zero','factor_nonzero_right'),positive,
             'Every raw toggle of a positive input by a nonzero p remains positive, including the quotient branch.'),
        spec('prime_factor_toggle_preserves_divisor',
             f"forall p n d e. ({_prime('p','preserve_prime')}) -> ({_dvd('p','n','preserve_p')}) -> ({_dvd('d','n','preserve_d')}) -> "
             f"({_toggle('p','d','e','preserve_graph')}) -> ({_dvd('e','n','preserve_e')})",
             ('prime_toggle_fresh_divisor_product','multiple_trans','mul_comm'),divisor,
             'Every actual prime toggle of a divisor of n is again a divisor, provided p itself is a prime divisor of n.'),
    )


def _divisor_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    total = _intro('n','p','d','hp')+('have hz : d=0 \\/ ~(d=0)',)+_call('eq_decidable','d','0')
    total += ('cases hz','exists d','right','split','left','exact hz_left','refl',
               f"have hd : ({_dvd('d','n','divisor_total_yes')}) \\/ ~({_dvd('d','n','divisor_total_no')})")
    total += _call('multiple_decidable_nonzero','d','n')+('exact hz_right','cases hd',
               f"have he : exists e. ({_toggle('p','d','e','divisor_total_toggle')})")
    total += _call('prime_factor_toggle_exists','p','d')+('intro hzero',)+_call('prime_nonzero','p')+('exact hp','exact hzero','cases he','exists x','left','split','exact hz_right','split','exact hd_left','exact he_witness',
               'exists d','right','split','right','exact hd_right','refl')

    functional = _intro('n','p','d','e','f','hp','he','hf')+('cases he',)+_parts('he_left',3)+('cases hf',)+_parts('hf_left',3)
    functional += _call('prime_factor_toggle_functional','p','d','e','f')+('intro hzero',)+_call('prime_nonzero','p')
    functional += ('exact hp','exact hzero','exact he_left_right_right','exact hf_left_right_right','cases hf_right','exfalso','cases hf_right_left',
                   'apply he_left_left','exact hf_right_left_left','apply hf_right_left_right','exact he_left_right_left','cases he_right','cases hf')+_parts('hf_left',3)
    functional += ('exfalso','cases he_right_left','apply hf_left_left','exact he_right_left_left','apply he_right_left_right','exact hf_left_right_left',
                   'cases hf_right','trans d','exact he_right_right','symm','exact hf_right_right')

    symmetric = _intro('n','p','d','e','hn','hp','hpn','h')+('cases h',)+_parts('h_left',3)+('left','split','intro hzero',)
    symmetric += _call('prime_factor_toggle_positive','p','d','e')+('intro hpzero',)+_call('prime_nonzero','p')
    symmetric += ('exact hp','exact hpzero','exact h_left_left','exact h_left_right_right','exact hzero','split')
    symmetric += _call('prime_factor_toggle_preserves_divisor','p','n','d','e')+('exact hp','exact hpn','exact h_left_right_left','exact h_left_right_right')
    symmetric += _call('prime_factor_toggle_symmetric','p','d','e')+('exact h_left_right_right','cases h_right')
    symmetric += _rewrite('h_right_right',_divisor_toggle('n','p','e','d','divisor_symmetric_rewrite'),'e')+('right','split','exact h_right_left','refl')

    bounded = _intro('n','p','d','e','hn','hp','hpn','hd','he')+('cases he',)+_parts('he_left',3)
    bounded += _call('divisor_le_nonzero','e','n')+('exact hn',)+_call('prime_factor_toggle_preserves_divisor','p','n','d','e')
    bounded += ('exact hp','exact hpn','exact he_left_right_left','exact he_left_right_right','cases he_right')
    bounded += _rewrite('he_right_right',_le('e','n','divisor_bound_rewrite'),'e')+('exact hd',)
    return (
        spec('divisor_prime_toggle_exists',
             f"forall n p d. ({_prime('p','divisor_total_prime')}) -> exists e. ({_divisor_toggle('n','p','d','e','divisor_total_result')})",
             ('eq_decidable','multiple_decidable_nonzero','prime_factor_toggle_exists','prime_nonzero'),total,
             'Decide positive-divisor membership and construct the raw toggle there, using identity at zero and nondivisors.'),
        spec('divisor_prime_toggle_functional',
             f"forall n p d e f. ({_prime('p','divisor_functional_prime')}) -> ({_divisor_toggle('n','p','d','e','divisor_functional_first')}) -> "
             f"({_divisor_toggle('n','p','d','f','divisor_functional_second')}) -> e=f",
             ('prime_factor_toggle_functional','prime_nonzero'),functional,
             'The actual positive-divisor toggle and omitted-index identity define one output for every natural index.'),
        spec('divisor_prime_toggle_symmetric',
             f"forall n p d e. ~(n=0) -> ({_prime('p','divisor_symmetric_prime')}) -> ({_dvd('p','n','divisor_symmetric_prime_divisor')}) -> "
             f"({_divisor_toggle('n','p','d','e','divisor_symmetric_source')}) -> ({_divisor_toggle('n','p','e','d','divisor_symmetric_target')})",
             ('prime_factor_toggle_positive','prime_nonzero','prime_factor_toggle_preserves_divisor','prime_factor_toggle_symmetric'),symmetric,
             'For a prime divisor of positive n, toggling preserves positive divisors and reverses the actual graph; omitted indices stay fixed.'),
        spec('divisor_prime_toggle_bounded',
             f"forall n p d e. ~(n=0) -> ({_prime('p','divisor_bounded_prime')}) -> ({_dvd('p','n','divisor_bounded_prime_divisor')}) -> "
             f"({_le('d','n','divisor_bounded_input')}) -> ({_divisor_toggle('n','p','d','e','divisor_bounded_graph')}) -> ({_le('e','n','divisor_bounded_output')})",
             ('divisor_le_nonzero','prime_factor_toggle_preserves_divisor'),bounded,
             'Every actual prime-toggle image of the finite interval 0..n remains in that interval, not in an assumed larger universe.'),
    )


def _map_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    body = _intro('n','p','b','c','hn','hp','hpn','hprefix')
    body += (f"have hb : {_bounded('b','c','S n','toggle_permutation_bound')}",)+_intro('i','hi')
    body += (f"have hv : exists e. ({_and(_at('b','c','i','e','toggle_permutation_entry'),_divisor_toggle('n','p','i','e','toggle_permutation_graph'))})",)
    body += _call('hprefix','i')+('exact hi','cases hv','cases hv_witness','exists x','split','exact hv_witness_left')
    body += _call('succ_le_succ','x','n')+_call('divisor_prime_toggle_bounded','n','p','i','x')+('exact hn','exact hp','exact hpn')
    body += _call('le_of_succ_le_succ','i','n')+('exact hi','exact hv_witness_right')
    body += (f"have hinj : {_injective('b','c','S n','toggle_permutation_injective')}",)+_intro('i','j','a','hi','hj','hia','hja')
    body += _call('divisor_prime_toggle_functional','n','p','a','i','j')+('exact hp',)
    for i,hindex,hat in (('i','hi','hia'),('j','hj','hja')):
        body += _call('divisor_prime_toggle_symmetric','n','p',i,'a')+('exact hn','exact hp','exact hpn')
        body += _call('divisor_prime_toggle_prefix_lookup','n','p','b','c','S n',i,'a')+('exact hprefix','exact '+hindex,'exact '+hat)
    body += ('split','exact hb','split','exact hinj')+_call('finite_bounded_injective_surjective','S n','b','c')+('exact hb','exact hinj')
    return (
        spec('divisor_prime_toggle_prefix_exists',
             f"forall n p l. ({_prime('p','prefix_prime')}) -> exists b c. ({_prefix('n','p','b','c','l','prefix_result')})",
             ('factor_permutation_below_zero_impossible','divisor_prime_toggle_exists','beta_prefix_extend','finite_lt_succ_eq_or_lt'),
             _prefix_choice_script(('n','p'),_divisor_toggle,_prefix,'divisor_prime_toggle_exists',('hp',)),
             'Ordinary finite induction constructs the actual beta-coded prime toggle at every index in the requested window.'),
        spec('divisor_prime_toggle_prefix_lookup',
             f"forall n p b c l i q. ({_prefix('n','p','b','c','l','prefix_lookup_source')}) -> ({_lt('i','l','prefix_lookup_bound')}) -> "
             f"({_at('b','c','i','q','prefix_lookup_entry')}) -> ({_divisor_toggle('n','p','i','q','prefix_lookup_result')})",
             ('beta_at_unique',),_prefix_lookup_script(('n','p'),_divisor_toggle),
             'Every actual decoded output of the constructed finite map obeys the independent positive-divisor toggle graph.'),
        spec('divisor_prime_toggle_prefix_permutation',
             f"forall n p b c. ~(n=0) -> ({_prime('p','permutation_prime')}) -> ({_dvd('p','n','permutation_prime_divisor')}) -> "
             f"({_prefix('n','p','b','c','S n','permutation_source')}) -> ({_permutation('b','c','S n','permutation_target')})",
             ('succ_le_succ','divisor_prime_toggle_bounded','le_of_succ_le_succ','divisor_prime_toggle_functional',
              'divisor_prime_toggle_symmetric','divisor_prime_toggle_prefix_lookup','finite_bounded_injective_surjective'),body,
             'The actual S n-entry prime toggle is a bounded, injective and constructively surjective permutation, including all fixed omitted indices.'),
        spec('divisor_prime_toggle_permutation_exists',
             f"forall n p. ~(n=0) -> ({_prime('p','constructed_prime')}) -> ({_dvd('p','n','constructed_divisor')}) -> "
             f"exists b c. ({_prefix('n','p','b','c','S n','constructed_prefix')}) /\\ ({_permutation('b','c','S n','constructed_permutation')})",
             ('divisor_prime_toggle_prefix_exists','divisor_prime_toggle_prefix_permutation'),
             _intro('n','p','hn','hp','hpn')+(f"have ht : exists b c. ({_prefix('n','p','b','c','S n','constructed_map')})",)
             +_call('divisor_prime_toggle_prefix_exists','n','p','S n')+('exact hp',)+_cases('ht',2)
             +('exists x','exists x1','split','exact ht_witness_witness')
             +_call('divisor_prime_toggle_prefix_permutation','n','p','x','x1')+('exact hn','exact hp','exact hpn','exact ht_witness_witness'),
             'For every actual prime divisor of a positive input, construct the complete finite toggle permutation without supplying its code.'),
    )


def _value_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    negate = _intro('p','d','e','a','b','hp','ht','ha','hb')+('cases ht','cases ht_left',)
    negate += _rewrite('ht_left_right',_mu('e','b','negate_add_rewrite'),'e','hb')
    negate += _call('mobius_fresh_prime_negates','p','d','a','b')+('exact hp','exact ht_left_left','exact ha','exact hb',
                'cases ht_right','cases ht_right_left')
    negate += _rewrite('ht_right_left_left',_mu('d','a','negate_remove_rewrite'),'d','ha')
    negate += _call('signed_negate_symmetric','b','a')+_call('mobius_fresh_prime_negates','p','e','b','a')
    negate += ('exact hp','exact ht_right_left_right','exact hb','exact ha','cases ht_right_right','have hzeroa : a=0')
    negate += _call('mobius_prime_square_value_zero','d','p','a')+('exact hp','exact ht_right_right_left','exact ha','have hzerob : b=0')
    negate += _call('mobius_prime_square_value_zero','d','p','b')+('exact hp','exact ht_right_right_left',)
    negate += _rewrite('ht_right_right_right',_mu('e','b','negate_fixed_rewrite'),'e','hb')+('exact hb',)
    negate += _rewrite('hzeroa',_negate('a','b','negate_zero_first'),'a')
    negate += _rewrite('hzerob',_negate('0','b','negate_zero_second'),'b')+('apply signed_negate_zero',)

    actual = _intro('N','M','n','K','d','z','hmu','hnN','hm','hd','hdiv','hbound','hz')+_parts('hmu',3)+('cases hm',)
    actual += _call('hmu_right_right','d','z')+('exact hd',)+_call('le_trans','d','n','N')+('exact hbound','exact hnN','cases hdiv')
    actual += _call('divisor_mask_entry_quotient_input','M','n','d','x','z')+('exact hd','exact hdiv_witness')
    actual += _call('hm_right','d','z')+('exact hbound','exact hz')
    return (
        spec('mobius_prime_factor_toggle_negates',
             f"forall p d e a b. ({_prime('p','value_prime')}) -> ({_toggle('p','d','e','value_toggle')}) -> "
             f"({_mu('d','a','value_source')}) -> ({_mu('e','b','value_target')}) -> ({_negate('a','b','value_negation')})",
             ('mobius_fresh_prime_negates','signed_negate_symmetric','mobius_prime_square_value_zero','signed_negate_zero'),negate,
             'Actual prime toggling negates independently defined Möbius values, including fixed nonsquarefree values, which are proved to be zero.'),
        spec('mobius_divisor_mask_actual_value',
             f"forall N M n K d z. ({_mu_table('N','M','mask_mu_table')}) -> ({_le('n','N','mask_input_bound')}) -> "
             f"({_mask('M','n','n','K','mask_source')}) -> ~(d=0) -> ({_dvd('d','n','mask_positive_divisor')}) -> "
             f"({_le('d','n','mask_index_bound')}) -> ({_table_at('K','d','z','mask_lookup')}) -> ({_mu('d','z','mask_actual_value')})",
             ('le_trans','divisor_mask_entry_quotient_input'),actual,
             'Every retained entry of an actual Möbius divisor mask is the independent positive-input Möbius value at that divisor.'),
    )


def _mask_toggle_row(spec: Callable[..., Any]) -> Any:
    body = _intro('N','M','n','K','p','d','e','a','b','hmu','hn','hnN','hp','hpn','hm','hd','ht','ha','hb')
    body += (f"have he : {_le('e','n','mask_toggle_output_bound')}",)
    body += _call('divisor_prime_toggle_bounded','n','p','d','e')+('exact hn','exact hp','exact hpn','exact hd','exact ht','cases ht')+_parts('ht_left',3)
    body += _call('mobius_prime_factor_toggle_negates','p','d','e','a','b')+('exact hp','exact ht_left_right_right')
    body += _call('mobius_divisor_mask_actual_value','N','M','n','K','d','a')
    body += ('exact hmu','exact hnN','exact hm','exact ht_left_left','exact ht_left_right_left','exact hd','exact ha')
    body += _call('mobius_divisor_mask_actual_value','N','M','n','K','e','b')
    body += ('exact hmu','exact hnN','exact hm','intro hezero')
    body += _call('prime_factor_toggle_positive','p','d','e')+('intro hpzero',)+_call('prime_nonzero','p')
    body += ('exact hp','exact hpzero','exact ht_left_left','exact ht_left_right_right','exact hezero')
    body += _call('prime_factor_toggle_preserves_divisor','p','n','d','e')
    body += ('exact hp','exact hpn','exact ht_left_right_left','exact ht_left_right_right','exact he','exact hb','cases ht_right','cases hm','have hzeroa : a=0')
    body += _call('divisor_mask_entry_omitted_value','M','n','d','a')+('exact ht_right_left',)
    body += _call('hm_right','d','a')+('exact hd','exact ha','have hzerob : b=0')
    body += _call('divisor_mask_entry_omitted_value','M','n','d','b')+('exact ht_right_left',)
    body += _call('hm_right','d','b')+('exact hd',)
    body += _rewrite('ht_right_right',_table_at('K','e','b','mask_toggle_omitted_rewrite'),'e','hb')+('exact hb',)
    body += _rewrite('hzeroa',_negate('a','b','mask_toggle_zero_first'),'a')
    body += _rewrite('hzerob',_negate('0','b','mask_toggle_zero_second'),'b')+('apply signed_negate_zero',)
    return spec('mobius_divisor_mask_prime_toggle_negates',
                f"forall N M n K p d e a b. ({_mu_table('N','M','mask_toggle_mu')}) -> ~(n=0) -> ({_le('n','N','mask_toggle_N')}) -> "
                f"({_prime('p','mask_toggle_prime')}) -> ({_dvd('p','n','mask_toggle_prime_divisor')}) -> ({_mask('M','n','n','K','mask_toggle_mask')}) -> "
                f"({_le('d','n','mask_toggle_input')}) -> ({_divisor_toggle('n','p','d','e','mask_toggle_graph')}) -> "
                f"({_table_at('K','d','a','mask_toggle_source')}) -> ({_table_at('K','e','b','mask_toggle_target')}) -> ({_negate('a','b','mask_toggle_result')})",
                ('divisor_prime_toggle_bounded','mobius_prime_factor_toggle_negates','mobius_divisor_mask_actual_value',
                 'prime_factor_toggle_positive','prime_nonzero','prime_factor_toggle_preserves_divisor',
                 'divisor_mask_entry_omitted_value','signed_negate_zero'),body,
                'Every pair of actual Möbius-mask values along the finite prime toggle are signed opposites, including zero, nondivisors and squared-prime multiples.')


def _signed_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    components=('pb','pc','nb','nc')
    swapped = _intro('F','G',*components,'i','a','b','hF','hG','ha','hn')
    swapped += (f"have hc : exists p n. ({_components(*components,'i','p','n','a','swapped_entry_components')})",)
    swapped += _call('divisor_signed_table_at_to_components','F',*components,'i','a')+('exact hF','exact ha')+_cases('hc',2)+_parts('hc_witness_witness',3)
    swapped += _call('divisor_signed_table_at_from_components','G','nb','nc','pb','pc','i','x1','x','b')
    swapped += ('exact hG','exact hc_witness_witness_right_left','exact hc_witness_witness_left')
    swapped += _call('divisor_signed_balance_negate','a','b','x','x1')+('exact hc_witness_witness_right_right','exact hn')

    H=_pack('x2','x3','x','x1')
    summed = _intro('F','G','l','a','b','hpoint','hF','hG')+_cases('hF',6)+_parts('hF'+'_witness'*6,4)
    summed += (f"have hn : exists v. ({_negate('a','v','sum_negation_exists')})",)
    summed += _call('signed_negate_total','a')+('cases hn',f"have hH : {_signed_sum(H,'l','x6','sum_negation_swapped')}")
    summed += _call('divisor_signed_sum_negation_transport','F',H,'x','x1','x2','x3','l','a','x6')
    summed += ('exact hF_witness_witness_witness_witness_witness_witness_left','refl','exact hF','exact hn_witness',
               f"have hequal : {_table_equal(H,'G','l','sum_negation_equal')}")+_intro('i','u','v','hi','hu','hv')
    summed += (f"have he : exists w. ({_table_at('F','i','w','sum_negation_input_value')})",)
    summed += _call('divisor_signed_table_lookup_from_components','F','x','x1','x2','x3','i')+('exact hF_witness_witness_witness_witness_witness_witness_left','cases he',
               f"have heopp : exists w. ({_negate('x7','w','sum_negation_entry_inverse')})")
    summed += _call('signed_negate_total','x7')+('cases heopp','trans x8')
    summed += _call('divisor_signed_table_at_functional',H,'i','u','x8')+('exact hu',)
    summed += _call('signed_table_swapped_components_negation_at','F',H,'x','x1','x2','x3','i','x7','x8')
    summed += ('exact hF_witness_witness_witness_witness_witness_witness_left','refl','exact he_witness','exact heopp_witness')
    summed += _call('signed_negate_functional','x7','x8','v')+('exact heopp_witness',)
    summed += _call('hpoint','i','x7','v')+('exact hi','exact he_witness','exact hv','have hresult : x6=b')
    summed += _call('divisor_signed_sum_extensional',H,'G','l','x6','b')+('exact hequal','exact hH','exact hG')
    summed += _rewrite('hresult',_negate('a','x6','sum_negation_rewrite'),'x6','hn_witness')+('exact hn_witness',)

    zero = _intro('F','G','r','s','l','a','b','hbound','hinj','hreindex','hnegate','hF','hG')+('have heq : b=a','symm')
    zero += _call('divisor_signed_sum_permutation_invariant','F','G','r','s','l','a','b')
    zero += ('exact hbound','exact hinj','exact hreindex','exact hF','exact hG',f"have hn : {_negate('a','b','anti_sum_negation')}")
    zero += _call('signed_prefix_sum_pointwise_negate','F','G','l','a','b')+('exact hnegate','exact hF','exact hG')
    zero += _rewrite('heq',_negate('a','b','anti_sum_rewrite'),'b','hn')
    zero += _call('divisor_signed_negate_fixed_zero','a')+('exact hn',)
    return (
        spec('signed_table_swapped_components_negation_at',
             f"forall F G {' '.join(components)} i a b. ({_rep('F',*components,'swapped_first_rep')}) -> ({_rep('G','nb','nc','pb','pc','swapped_second_rep')}) -> "
             f"({_table_at('F','i','a','swapped_source')}) -> ({_negate('a','b','swapped_inverse')}) -> ({_table_at('G','i','b','swapped_result')})",
             ('divisor_signed_table_at_to_components','divisor_signed_table_at_from_components','divisor_signed_balance_negate'),swapped,
             'Swapping the real positive and negative beta components constructs the exact negated signed lookup, with no canonical-component equality assumption.'),
        spec('signed_prefix_sum_pointwise_negate',
             f"forall F G l a b. ({_pointwise_negate('F','G','l','sum_negation_entries')}) -> ({_signed_sum('F','l','a','sum_negation_first')}) -> "
             f"({_signed_sum('G','l','b','sum_negation_second')}) -> ({_negate('a','b','sum_negation_result')})",
             ('signed_negate_total','divisor_signed_sum_negation_transport','divisor_signed_table_lookup_from_components',
              'divisor_signed_table_at_functional','signed_table_swapped_components_negation_at','signed_negate_functional','divisor_signed_sum_extensional'),summed,
             'Pointwise opposite canonical signed entries have opposite actual finite sums, by genuine swapped-component folds and representation independence.'),
        spec('anti_invariant_signed_permutation_sum_zero',
             f"forall F G r s l a b. ({_bounded('r','s','l','anti_bound')}) -> ({_injective('r','s','l','anti_injective')}) -> "
             f"({_reindex('F','G','r','s','l','anti_reindex')}) -> ({_pointwise_negate('F','G','l','anti_opposite')}) -> "
             f"({_signed_sum('F','l','a','anti_first_sum')}) -> ({_signed_sum('G','l','b','anti_second_sum')}) -> a=0",
             ('divisor_signed_sum_permutation_invariant','signed_prefix_sum_pointwise_negate','divisor_signed_negate_fixed_zero'),zero,
             'A genuine finite signed sum whose actual permutation pullback is pointwise its opposite is zero; ordinary characteristic-zero cancellation is proved, not assumed.'),
    )


def _delta(n: str, z: str) -> str:
    return f'(({n})=1 /\\ ({z})=2) \\/ (~(({n})=1) /\\ ({z})=0)'


def _cancellation_iff(M: str, n: str, z: str, tag: str) -> str:
    return _and(f'({_divisor_sum(M,n,z,tag+"forward")}) -> ({_delta(n,z)})',
                f'({_delta(n,z)}) -> ({_divisor_sum(M,n,z,tag+"reverse")})')


def _cancellation_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    masked = _intro('N','M','n','K','p','z','hmu','hn','hN','hp','hpn','hmask','hz')
    masked += (f"have hmap : exists r s. ({_prefix('n','p','r','s','S n','cancel_constructed_prefix')}) /\\ ({_permutation('r','s','S n','cancel_constructed_permutation')})",)
    masked += _call('divisor_prime_toggle_permutation_exists','n','p')+('exact hn','exact hp','exact hpn')+_cases('hmap',2)
    masked += ('cases hmap_witness_witness',)+_parts('hmap_witness_witness_right',3)+('cases hmask',)
    masked += (f"have hG : exists G. ({_table('S n','G','cancel_pullback_table')}) /\\ ({_reindex('K','G','x','x1','S n','cancel_pullback')})",)
    masked += _call('divisor_signed_table_reindex_exists','n','K','x','x1','S n')+('exact hmask_left','cases hG','cases hG_witness',
                f"have hsum : exists w. ({_signed_sum('x2','S n','w','cancel_pullback_sum')})")
    masked += _call('arithmetic_signed_sum_exists','S n','x2','S n')+('exact hG_witness_left','cases hsum',
                f"have hpoint : {_pointwise_negate('K','x2','S n','cancel_opposite_entries')}")+_intro('i','a','b','hi','ha','hb')
    masked += (f"have hiimage : exists q. ({_and(_at('x','x1','i','q','cancel_map_entry'),_divisor_toggle('n','p','i','q','cancel_map_graph'))})",)
    masked += _call('hmap_witness_witness_left','i')+('exact hi','cases hiimage','cases hiimage_witness',
                f"have hqbound : {_le('x4','n','cancel_image_bound')}")
    masked += _call('divisor_prime_toggle_bounded','n','p','i','x4')+('exact hn','exact hp','exact hpn')
    masked += _call('le_of_succ_le_succ','i','n')+('exact hi','exact hiimage_witness_right',
                f"have hvalue : exists v. ({_table_at('K','x4','v','cancel_actual_image_value')})")
    masked += _call('divisor_signed_table_lookup','n','K','x4')+('exact hmask_left','exact hqbound','cases hvalue','have heq : x5=b')
    masked += _call('divisor_signed_table_at_functional','x2','i','x5','b')
    masked += _call('hG_witness_right','i','x4','x5')+('exact hi','exact hiimage_witness_left','exact hvalue_witness','exact hb',
                f"have hneg : {_negate('a','x5','cancel_actual_negation')}")
    masked += _call('mobius_divisor_mask_prime_toggle_negates','N','M','n','K','p','i','x4','a','x5')
    masked += ('exact hmu','exact hn','exact hN','exact hp','exact hpn','exact hmask')
    masked += _call('le_of_succ_le_succ','i','n')+('exact hi','exact hiimage_witness_right','exact ha','exact hvalue_witness')
    masked += _rewrite('heq',_negate('a','x5','cancel_point_rewrite'),'x5','hneg')+('exact hneg',)
    masked += _call('anti_invariant_signed_permutation_sum_zero','K','x2','x','x1','S n','z','x3')
    masked += ('exact hmap_witness_witness_right_left','exact hmap_witness_witness_right_right_left',
                'exact hG_witness_right','exact hpoint','exact hz','exact hsum_witness')

    value = _intro('N','M','n','z','hmu','hn','hne','hN','hs')+('cases hs','cases hs_right','cases hs_right_witness',
               f"have hp : exists p. ({_prime('p','cancel_prime_witness')}) /\\ ({_dvd('p','n','cancel_divisor_witness')})")
    value += _call('prime_divisor_exists','n')+('exact hn','exact hne','cases hp','cases hp_witness')
    value += _call('mobius_divisor_mask_prime_factor_sum_zero','N','M','n','x','x1','z')
    value += ('exact hmu','exact hn','exact hN','exact hp_witness_left','exact hp_witness_right','exact hs_right_witness_left','exact hs_right_witness_right')

    zero = _intro('N','M','n','hmu','hn','hne','hN')+_parts('hmu',3)
    zero += (f"have hs : exists z. ({_divisor_sum('M','n','z','cancel_zero_construct')})",)
    zero += _call('signed_divisor_sum_exists','N','M','n')+('exact hmu_left','exact hn','exact hN','cases hs','have heq : x=0')
    zero += _call('mobius_divisor_sum_nonunit_value_zero','N','M','n','x')+('exact hmu','exact hn','exact hne','exact hN','exact hs_witness')
    zero += _rewrite('heq',_divisor_sum('M','n','x','cancel_zero_rewrite'),'x','hs_witness')+('exact hs_witness',)

    unit = _intro('N','M','hmu','hN')+_parts('hmu',3)
    unit += _call('signed_divisor_sum_one','N','M','2')+('exact hmu_left','exact hN')
    unit += _call('mobius_table_one_entry','N','M')+('exact hmu','exact hN')

    iff = _intro('N','M','n','z','hmu','hn','hN')+('split','intro hs','have hc : n=1 \\/ ~(n=1)')
    iff += _call('eq_decidable','n','1')+('cases hc','left','split','exact hc_left')
    iff += _call('signed_divisor_sum_functional','M','1','z','2')
    iff += _rewrite('hc_left',_divisor_sum('M','n','z','cancel_unit_input_rewrite'),'n','hs')+('exact hs',)
    iff += _call('mobius_divisor_sum_unit_one','N','M')+('exact hmu',)
    iff += _rewrite('hc_left',_le('n','N','cancel_unit_bound_rewrite'),'n','hN')+('exact hN','right','split','exact hc_right')
    iff += _call('mobius_divisor_sum_nonunit_value_zero','N','M','n','z')+('exact hmu','exact hn','exact hc_right','exact hN','exact hs','intro hd','cases hd','cases hd_left')
    iff += _rewrite('hd_left_left',_divisor_sum('M','n','z','cancel_unit_target_rewrite'),'n')
    iff += _rewrite('hd_left_right',_divisor_sum('M','1','z','cancel_unit_code_rewrite'),'z')
    iff += _call('mobius_divisor_sum_unit_one','N','M')+('exact hmu',)
    iff += _rewrite('hd_left_left',_le('n','N','cancel_unit_reverse_bound'),'n','hN')+('exact hN','cases hd_right')
    iff += _rewrite('hd_right_right',_divisor_sum('M','n','z','cancel_nonunit_target'),'z')
    iff += _call('mobius_divisor_sum_nonunit_zero','N','M','n')+('exact hmu','exact hn','exact hd_right_left','exact hN')

    exists = _intro('n','hn')+(f"have hm : exists M. ({_mu_table('n','M','cancel_actual_table')})",)
    exists += _call('mobius_table_exists','n')+('cases hm',f"have hs : exists z. ({_divisor_sum('x','n','z','cancel_actual_sum')})")
    exists += _call('signed_divisor_sum_exists','n','x','n')+_parts('hm_witness',3)+('exact hm_witness_left','exact hn')
    exists += _call('le_refl','n')+('cases hs','exists x','exists x1','split','exact hm_witness','split','exact hs_witness',
                  f"have hiff : {_cancellation_iff('x','n','x1','cancel_actual_identity')}")
    exists += _call('mobius_divisor_sum_cancellation','n','x','n','x1')+('exact hm_witness','exact hn')+_call('le_refl','n')
    exists += ('cases hiff','apply hiff_left','exact hs_witness')
    return (
        spec('mobius_divisor_mask_prime_factor_sum_zero',
             f"forall N M n K p z. ({_mu_table('N','M','cancel_mask_mu')}) -> ~(n=0) -> ({_le('n','N','cancel_mask_N')}) -> "
             f"({_prime('p','cancel_mask_prime')}) -> ({_dvd('p','n','cancel_mask_p_divisor')}) -> ({_mask('M','n','n','K','cancel_mask')}) -> "
             f"({_signed_sum('K','S n','z','cancel_mask_sum')}) -> z=0",
             ('divisor_prime_toggle_permutation_exists','divisor_signed_table_reindex_exists','arithmetic_signed_sum_exists',
              'divisor_prime_toggle_bounded','le_of_succ_le_succ','divisor_signed_table_lookup','divisor_signed_table_at_functional',
              'mobius_divisor_mask_prime_toggle_negates','anti_invariant_signed_permutation_sum_zero'),masked,
             'A genuinely constructed prime-toggle permutation makes the actual zero-masked Möbius sum anti-invariant, hence zero; no cancellation formula is an input.'),
        spec('mobius_divisor_sum_nonunit_value_zero',
             f"forall N M n z. ({_mu_table('N','M','cancel_value_table')}) -> ~(n=0) -> ~(n=1) -> ({_le('n','N','cancel_value_bound')}) -> "
             f"({_divisor_sum('M','n','z','cancel_value_sum')}) -> z=0",
             ('prime_divisor_exists','mobius_divisor_mask_prime_factor_sum_zero'),value,
             'For every positive nonunit n, construct an actual prime divisor and prove that every genuine Möbius divisor sum is canonical zero.'),
        spec('mobius_divisor_sum_nonunit_zero',
             f"forall N M n. ({_mu_table('N','M','cancel_zero_table')}) -> ~(n=0) -> ~(n=1) -> ({_le('n','N','cancel_zero_bound')}) -> "
             f"({_divisor_sum('M','n','0','cancel_zero_result')})",
             ('signed_divisor_sum_exists','mobius_divisor_sum_nonunit_value_zero'),zero,
             'Construct the actual finite divisor sum before identifying it with zero for every positive nonunit input.'),
        spec('mobius_divisor_sum_unit_one',
             f"forall N M. ({_mu_table('N','M','cancel_unit_table')}) -> ({_le('1','N','cancel_unit_bound')}) -> ({_divisor_sum('M','1','2','cancel_unit_result')})",
             ('signed_divisor_sum_one','mobius_table_one_entry'),unit,
             'The unit boundary is the genuine two-entry mask fold 0+mu(1)=+1, whose canonical signed code is two.'),
        spec('mobius_divisor_sum_cancellation',
             f"forall N M n z. ({_mu_table('N','M','cancel_iff_table')}) -> ~(n=0) -> ({_le('n','N','cancel_iff_bound')}) -> ({_cancellation_iff('M','n','z','cancel_iff_result')})",
             ('eq_decidable','signed_divisor_sum_functional','mobius_divisor_sum_unit_one',
              'mobius_divisor_sum_nonunit_value_zero','mobius_divisor_sum_nonunit_zero'),iff,
             'Full positive-divisor cancellation for independently defined Möbius values: the actual sum is +1 exactly at n=1 and zero at every n>1, with a constructed fold in both directions.'),
        spec('mobius_divisor_sum_cancellation_exists',
             f"forall n. ~(n=0) -> exists M z. ({_and(_mu_table('n','M','cancel_exists_table'),_divisor_sum('M','n','z','cancel_exists_sum'),_delta('n','z'))})",
             ('mobius_table_exists','signed_divisor_sum_exists','le_refl','mobius_divisor_sum_cancellation'),exists,
             'For each positive natural, construct the actual Möbius table, its real finite divisor-sum trace and the exact unit/nonunit result; no table or quotient is supplied.'),
    )


def _unrestricted_zero_entry_row(spec: Callable[..., Any]) -> Any:
    body = _intro('N','F','n','z','ht','hvalues','hn','hN')
    body += (f"have hM : exists M. ({_mu_table('N','M','arbitrary_zero_mu_table')})",)
    body += _call('mobius_table_exists','N')+('cases hM',)+_parts('hM_witness',3)
    body += (f"have hequal : {_positive_equal('F','x','n','arbitrary_zero_positive_equal')}",)+_intro('d','a','b','hd','hbound','ha','hb')
    body += _call('mobius_value_functional','d','a','b')
    body += _call('hvalues','d','a')+('exact hd',)+_call('le_trans','d','n','N')+('exact hbound','exact hN','exact ha')
    body += _call('hM_witness_right_right','d','b')+('exact hd',)+_call('le_trans','d','n','N')+('exact hbound','exact hN','exact hb')
    body += (f"have hFsum : exists u. ({_divisor_sum('F','n','u','arbitrary_zero_F_sum')})",)
    body += _call('signed_divisor_sum_exists','N','F','n')+('exact ht','exact hn','exact hN','cases hFsum',
               f"have hMsum : exists v. ({_divisor_sum('x','n','v','arbitrary_zero_M_sum')})")
    body += _call('signed_divisor_sum_exists','N','x','n')+('exact hM_witness_left','exact hn','exact hN','cases hMsum',
               f"have hiff : {_cancellation_iff('x','n','z','arbitrary_zero_known_identity')}")
    body += _call('mobius_divisor_sum_cancellation','N','x','n','z')+('exact hM_witness','exact hn','exact hN','cases hiff','split','intro hz','apply hiff_left','have heq : x2=z','symm')
    body += _call('signed_divisor_sum_positive_source_extensional','F','x','n','z','x2')+('exact hequal','exact hz','exact hMsum_witness')
    body += _rewrite('heq',_divisor_sum('x','n','x2','arbitrary_zero_forward_rewrite'),'x2','hMsum_witness')+('exact hMsum_witness','intro hdelta',
               f"have hz : {_divisor_sum('x','n','z','arbitrary_zero_reverse_sum')}",'apply hiff_right','exact hdelta','have heq : x1=z')
    body += _call('signed_divisor_sum_positive_source_extensional','F','x','n','x1','z')+('exact hequal','exact hFsum_witness','exact hz')
    body += _rewrite('heq',_divisor_sum('F','n','x1','arbitrary_zero_reverse_rewrite'),'x1','hFsum_witness')+('exact hFsum_witness',)
    return spec('mobius_divisor_sum_cancellation_on_positive_values',
                f"forall N F n z. ({_table('N','F','arbitrary_zero_table')}) -> ({_positive_values('N','F','arbitrary_zero_values')}) -> "
                f"~(n=0) -> ({_le('n','N','arbitrary_zero_bound')}) -> ({_cancellation_iff('F','n','z','arbitrary_zero_result')})",
                ('mobius_table_exists','mobius_value_functional','le_trans','signed_divisor_sum_exists',
                 'mobius_divisor_sum_cancellation','signed_divisor_sum_positive_source_extensional'),body,
                'Full Möbius divisor cancellation holds for any actual signed table with the correct positive values, with F(0) entirely unrestricted; positive-source extensionality transports genuine folds.')


def make_mobius_divisor_cancellation_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (_scalar_rows(spec)+_toggle_rows(spec)+_divisor_rows(spec)+_map_rows(spec)+_value_rows(spec)
            +(_mask_toggle_row(spec),)+_signed_rows(spec)+_cancellation_rows(spec)+(_unrestricted_zero_entry_row(spec),))


__all__ = ['prime_factor_toggle_relation','divisor_prime_toggle_relation','divisor_prime_toggle_prefix_relation',
           'signed_arithmetic_table_negation_relation',
           'mobius_positive_table_values_relation',
           'make_mobius_divisor_cancellation_candidate_theorems']
