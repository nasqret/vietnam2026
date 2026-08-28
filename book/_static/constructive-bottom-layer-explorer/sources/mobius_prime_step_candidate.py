"""Prime-adjunction and divisor lemmas for independently defined Möbius values.

These are additive ordinary HA bodies over the immutable v30 basis and the
independent Möbius-value factory.  The signed-negation graph is precisely the
existing canonical decoder graph, not a new ring operation or an oracle.
"""

from __future__ import annotations

from typing import Any, Callable

from .foundation_saturation_candidate import _allprime, _factorization, _product
from .gaussian_euclidean_candidate import _sd
from .mobius_value_candidate import _even, _mu, _odd, _prime_square, _sign
from .prime_factorization_permutation_candidate import _preserve
from .prime_valuation_support_candidate import (
    _and, _at, _call, _cases, _dvd, _intro, _le, _parts, _prime, _public, _rewrite,
)
from .squarefree_decomposition_candidate import _cop, _squarefree


def _negate(a: str, b: str, tag: str) -> str:
    p, n = ("mps_" + role + "_" + tag for role in ("positive", "negative"))
    return f"exists {p} {n}. " + _and(_sd(a,p,n,tag+'source'),_sd(b,n,p,tag+'target'))


def mobius_signed_negation_relation(a: str, b: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Term-hygienic expansion of the unchanged canonical SignedNegate graph."""
    return _public(_negate,(a,b),tag=tag,variables=variables)


def _squarefree_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'mobius_squarefree_divisor',
            f"forall n d. ({_squarefree('n','divisor_source')}) -> ({_dvd('d','n','divisor_at')}) -> ({_squarefree('d','divisor_target')})",
            ('factor_nonzero_left','squarefree_excludes_prime_square','multiple_trans'),
            _intro('n','d','hsf','hdiv')+('cases hsf','split','intro hz','cases hdiv')
            +_call('factor_nonzero_left','n','d','x')+('exact hsf_left','exact hdiv_witness','exact hz')
            +_intro('p','hp','hbound','hsquare')+_call('squarefree_excludes_prime_square','n','p')
            +('exact hsf','exact hp')+_call('multiple_trans','d','p * p','n')+('exact hdiv','exact hsquare'),
            'A genuine divisor of a positive squarefree input is positive and squarefree, with no bound assumption on its prime-square witnesses.',
        ),
        spec(
            'mobius_prime_squarefree',
            f"forall p. ({_prime('p','squarefree_prime')}) -> ({_squarefree('p','prime_result')})",
            ('prime_nonzero','multiple_trans','prime_divisor_of_prime_forces_equality',
             'mul_left_cancel_nonzero','mul_one','mul_assoc','divisor_one'),
            _intro('p','hp')+('split','intro hz')+_call('prime_nonzero','p')+('exact hp','exact hz')
            +_intro('q','hq','hbound','hdiv')+('have heq : q = p',)
            +_call('prime_divisor_of_prime_forces_equality','q','p')+('exact hq','exact hp')
            +_call('multiple_trans','q * q','q','p')+('exact hdiv','exists q','refl',)
            +_rewrite('heq',_dvd('q * q','p','prime_rewrite'),'q','hdiv')
            +('cases hdiv','have hone : 1 = p * x',)
            +_call('mul_left_cancel_nonzero','p','1','p * x')+('intro hz',)+_call('prime_nonzero','p')
            +('exact hp','exact hz','trans p','apply mul_one','trans (p * p) * x','exact hdiv_witness','apply mul_assoc',
                'cases hp','apply hp_left')+_call('divisor_one','p')+('exists x','exact hone'),
            'No genuine prime has a squared prime divisor; both nonzero and nonunit boundaries are proved from primality.',
        ),
        spec(
            'mobius_squarefree_fresh_prime_product',
            f"forall p n. ({_prime('p','fresh_prime')}) -> ({_squarefree('n','fresh_squarefree')}) -> "
            f"~({_dvd('p','n','fresh_nondivisor')}) -> ({_squarefree('p * n','fresh_product')})",
            ('prime_nonzero','mul_ne_zero','eq_decidable','mul_left_cancel_nonzero','mul_assoc',
             'squarefree_excludes_prime_square','gauss_coprime_cancel','coprime_mul_left','distinct_primes_coprime'),
            _intro('p','n','hp','hsf','hfresh')+('cases hsf','split','intro hz')+_call('mul_ne_zero','p','n')
            +('intro hpz',)+_call('prime_nonzero','p')+('exact hp','exact hpz','exact hsf_left','exact hz')
            +_intro('q','hq','hbound','hdiv')+('have heq : q = p \\/ ~(q = p)',)
            +_call('eq_decidable','q','p')+('cases heq','apply hfresh',)
            +_rewrite('heq_left',_dvd('q * q','p * n','fresh_equal'),'q','hdiv')
            +('cases hdiv','exists x',)+_call('mul_left_cancel_nonzero','p','n','p * x')
            +('intro hz',)+_call('prime_nonzero','p')+('exact hp','exact hz','trans (p * p) * x','exact hdiv_witness','apply mul_assoc')
            +_call('squarefree_excludes_prime_square','n','q')+('exact hsf','exact hq')
            +_call('gauss_coprime_cancel','q * q','p','n')+_call('coprime_mul_left','q','q','p')
            +_call('distinct_primes_coprime','q','p')+('exact hq','exact hp','exact heq_right')
            +_call('distinct_primes_coprime','q','p')+('exact hq','exact hp','exact heq_right','exact hdiv'),
            'Adjoining an actual prime not dividing a squarefree input preserves squarefreeness; Euclid cancellation excludes every possible squared prime divisor.',
        ),
        spec(
            'mobius_prime_factor_list_append',
            f"forall n b c l p. ({_factorization('n','b','c','l','mps_append_source')}) -> "
            f"({_prime('p','append_prime')}) -> exists d e. ({_factorization('n * p','d','e','S l','mps_append_target')})",
            ('beta_factor_prefix_product_append','mul_ne_zero','prime_nonzero','all_prime_transport','all_prime_succ_intro'),
            _intro('n','b','c','l','p','hf','hp')+_parts('hf',3)
            +(f"have hext : exists d e. {_and(_at('d','e','l','p','append_last'),_preserve('b','c','d','e','l','append_preserved'),_product('d','e','S l','n * p','append_product'))}",)
            +_call('beta_factor_prefix_product_append','b','c','l','n','p')+('exact hf_right_left',)
            +_cases('hext',2)+_parts('hext_witness_witness',3)+('exists x','exists x1','split','intro hz')
            +_call('mul_ne_zero','n','p')+('exact hf_left','intro hpz')+_call('prime_nonzero','p')
            +('exact hp','exact hpz','exact hz','split','exact hext_witness_witness_right_right')
            +_call('all_prime_succ_intro','x','x1','l','p')
            +_call('all_prime_transport','b','c','x','x1','l')
            +('exact hf_right_right','exact hext_witness_witness_right_left','split','exact hext_witness_witness_left','exact hp'),
            'The beta extension theorem constructs a new actual prime list with one more occurrence and product n*p; no sorted or preselected factorization is supplied.',
        ),
    )


def _sign_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'mobius_positive_unit_negates_to_negative_unit',
            _negate('2','1','unit_negation'),
            ('mul_one','zero_add'),
            ('exists 1','exists 0','split','left','split','symm','apply mul_one','refl',
             'right','exists 0','split','split','rewrite PA5','symm','apply zero_add','refl','refl'),
            'Canonical code two is positive one and code one is its genuine decoded additive inverse.',
        ),
        spec(
            'alternating_signed_unit_successor_negates',
            f"forall n a b. ({_sign('n','a','successor_source')}) -> ({_sign('S n','b','successor_target')}) -> ({_negate('a','b','successor_negation')})",
            ('successor_odd_of_even','successor_even_of_odd','alternating_signed_unit_functional',
             'mobius_positive_unit_negates_to_negative_unit','signed_negate_symmetric'),
            _intro('n','a','b','ha','hb')+('cases ha','cases ha_left',
                f"have hs : {_sign('S n','1','successor_odd')}",'right','split')
            +_call('successor_odd_of_even','n')+('exact ha_left_left','refl','have heq : b = 1')
            +_call('alternating_signed_unit_functional','S n','b','1')+('exact hb','exact hs')
            +_rewrite('ha_left_right',_negate('a','b','successor_first_rewrite'),'a')
            +_rewrite('heq',_negate('2','b','successor_second_rewrite'),'b')
            +('apply mobius_positive_unit_negates_to_negative_unit','cases ha_right',
                f"have hs : {_sign('S n','2','successor_even')}",'left','split')
            +_call('successor_even_of_odd','n')+('exact ha_right_left','refl','have heq : b = 2')
            +_call('alternating_signed_unit_functional','S n','b','2')+('exact hb','exact hs')
            +_rewrite('ha_right_right',_negate('a','b','successor_third_rewrite'),'a')
            +_rewrite('heq',_negate('1','b','successor_fourth_rewrite'),'b')
            +_call('signed_negate_symmetric','2','1')+('apply mobius_positive_unit_negates_to_negative_unit',),
            'The alternating unit at the successor exponent is the canonical signed negation, proved by the two constructive parity cases.',
        ),
    )


def _value_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            'mobius_prime_square_value_zero',
            f"forall n p z. ({_prime('p','square_value_prime')}) -> ({_dvd('p * p','n','square_value_divisor')}) -> ({_mu('n','z','square_value_input')}) -> z = 0",
            ('mobius_value_functional','mobius_from_prime_square','mobius_input_positive'),
            _intro('n','p','z','hp','hdiv','hmu')+_call('mobius_value_functional','n','z','0')
            +('exact hmu',)+_call('mobius_from_prime_square','n','p')
            +('intro hz',)+_call('mobius_input_positive','n','z')+('exact hmu','exact hz','exact hp','exact hdiv'),
            'Every independently defined Möbius value at an actual prime-square multiple is the canonical zero code.',
        ),
        spec(
            'mobius_fresh_prime_negates',
            f"forall p n a b. ({_prime('p','step_prime')}) -> ~({_dvd('p','n','step_fresh')}) -> "
            f"({_mu('n','a','step_source')}) -> ({_mu('p * n','b','step_target')}) -> ({_negate('a','b','step_result')})",
            ('mobius_prime_square_value_zero','multiple_mul_left','signed_negate_zero',
             'mobius_prime_factor_list_append','mobius_squarefree_fresh_prime_product','mobius_squarefree_evaluation',
             'alternating_signed_unit_successor_negates','mul_comm'),
            _intro('p','n','a','b','hp','hfresh','ha','hb')+('cases ha','cases ha_right','cases ha_right_left',
                'cases ha_right_left_left','cases ha_right_left_left_witness','have heq : b = 0')
            +_call('mobius_prime_square_value_zero','p * n','x','b')
            +('exact ha_right_left_left_witness_left',)+_call('multiple_mul_left','x * x','n','p')
            +('exact ha_right_left_left_witness_right','exact hb')
            +_rewrite('ha_right_left_right',_negate('a','b','step_zero_first'),'a')
            +_rewrite('heq',_negate('0','b','step_zero_second'),'b')+('apply signed_negate_zero',
                'cases ha_right_right')+_cases('ha_right_right_right',3)
            +('cases ha_right_right_right_witness_witness_witness',
                f"have hlist : exists d e. ({_factorization('n * p','d','e','S x2','mps_step_appended')})")
            +_call('mobius_prime_factor_list_append','n','x','x1','x2','p')
            +('exact ha_right_right_right_witness_witness_witness_left','exact hp',)+_cases('hlist',2)
            +(f"have hsf : {_squarefree('p * n','step_product_sf')}",)
            +_call('mobius_squarefree_fresh_prime_product','p','n')+('exact hp','exact ha_right_right_left','exact hfresh',
                f"have hsign : {_sign('S x2','b','step_product_sign')}")
            +_call('mobius_squarefree_evaluation','p * n','x3','x4','S x2','b')+('exact hsf','have heq : n * p = p * n','apply mul_comm',)
            +_rewrite('heq',_factorization('n * p','x3','x4','S x2','mps_step_rewrite'),'n * p','hlist_witness_witness')
            +('exact hlist_witness_witness','exact hb')
            +_call('alternating_signed_unit_successor_negates','x2','a','b')
            +('exact ha_right_right_right_witness_witness_witness_right','exact hsign'),
            'For an actual prime not dividing n, adjoining that prime negates the genuine Möbius value, including all nonsquarefree zero cases.',
        ),
    )


def make_mobius_prime_step_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    return _squarefree_rows(spec)+_sign_rows(spec)+_value_rows(spec)


__all__ = ['mobius_signed_negation_relation','make_mobius_prime_step_candidate_theorems']
