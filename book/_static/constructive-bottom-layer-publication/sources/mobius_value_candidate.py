"""Independent constructive Möbius values over the immutable Alpha-v30 basis.

The value is defined from genuine prime-factor lists, their length parity,
and actual prime-square divisibility.  No divisor-sum identity or inversion
property occurs in the definition.  Values use the existing signed-natural
coding: zero is 0, positive one is 2, and negative one is 1.

These additive ordinary-HA bodies are not themselves Alpha admission or
empty-context proof certificates.
"""

from __future__ import annotations

from typing import Any, Callable

from .foundation_saturation_candidate import _factorization
from .prime_factorization_permutation_candidate import _length_result
from .prime_valuation_support_candidate import (
    _and, _call, _cases, _dvd, _intro, _prime, _public, _rewrite,
)
from .squarefree_decomposition_candidate import _squarefree


def _even(n: str, tag: str) -> str:
    k = "mv_even_half_" + tag
    return f"exists {k}. ({n}) = 2 * {k}"


def _odd(n: str, tag: str) -> str:
    k = "mv_odd_half_" + tag
    return f"exists {k}. ({n}) = 2 * {k} + 1"


def _sign(n: str, z: str, tag: str) -> str:
    return (
        f"({_and(_even(n,tag+'even'),f'({z}) = 2')}) \\/ "
        f"({_and(_odd(n,tag+'odd'),f'({z}) = 1')})"
    )


def _prime_square(n: str, tag: str) -> str:
    p = "mv_square_prime_" + tag
    return f"exists {p}. " + _and(_prime(p,tag+'prime'),_dvd(f'{p} * {p}',n,tag+'divisor'))


def _factor_sign(n: str, z: str, tag: str) -> str:
    b, c, l = ("mv_" + role + "_" + tag for role in ("factor_code", "factor_scale", "factor_count"))
    return f"exists {b} {c} {l}. " + _and(
        _factorization(n,b,c,l,tag+'factorization'), _sign(l,z,tag+'parity')
    )


def _mu(n: str, z: str, tag: str) -> str:
    zero = _and(_prime_square(n,tag+'square'),f"({z}) = 0")
    unit = _and(_squarefree(n,tag+'squarefree'),_factor_sign(n,z,tag+'factors'))
    return _and(f"~(({n}) = 0)",f"({zero}) \\/ ({unit})")


def alternating_signed_unit_relation(n: str, z: str, *, tag: str, variables: tuple[str,...]) -> str:
    """The canonical integer (-1)^n, specified independently by parity."""
    return _public(_sign,(n,z),tag=tag,variables=variables)


def has_prime_square_divisor_relation(n: str, *, tag: str, variables: tuple[str,...]) -> str:
    """An actual prime and an actual quotient witness its squared divisibility."""
    return _public(_prime_square,(n,),tag=tag,variables=variables)


def prime_factor_parity_sign_relation(n: str, z: str, *, tag: str, variables: tuple[str,...]) -> str:
    """A genuine prime-factor list whose length gives the canonical parity sign."""
    return _public(_factor_sign,(n,z),tag=tag,variables=variables)


def mobius_value_relation(n: str, z: str, *, tag: str, variables: tuple[str,...]) -> str:
    """Positive-input Möbius value from square divisors and real prime factors."""
    return _public(_mu,(n,z),tag=tag,variables=variables)


def _sign_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            "alternating_signed_unit_exists",
            f"forall n. exists z. ({_sign('n','z','total')})",
            ("parity_cases",),
            _intro('n')+('have h : exists k. n = 2 * k \\/ n = 2 * k + 1',)
            +_call('parity_cases','n')+('cases h','cases h_witness',
                'exists 2','left','split','exists x','exact h_witness_left','refl',
                'exists 1','right','split','exists x','exact h_witness_right','refl'),
            "Parity constructs an actual canonical code for the alternating unit at every natural exponent.",
        ),
        spec(
            "alternating_signed_unit_functional",
            f"forall n a b. ({_sign('n','a','first')}) -> ({_sign('n','b','second')}) -> a = b",
            ('even_not_odd','odd_not_even'),
            _intro('n','a','b','ha','hb')+('cases ha','cases ha_left','cases hb','cases hb_left',
                'trans 2','exact ha_left_right','symm','exact hb_left_right',
                'cases hb_right','exfalso')+_call('even_not_odd','n')
            +('exact ha_left_left','exact hb_right_left','cases ha_right','cases hb','cases hb_left','exfalso')
            +_call('odd_not_even','n')+('exact ha_right_left','exact hb_left_left',
                'cases hb_right','trans 1','exact ha_right_right','symm','exact hb_right_right'),
            "Constructive parity exclusivity makes the signed alternating-unit code unique.",
        ),
        spec(
            "alternating_signed_unit_zero",
            _sign('0','2','zero'),
            (),
            ('left','split','exists 0','symm','apply PA5','refl'),
            "Exponent zero has canonical positive-unit code two, not code one.",
        ),
        spec(
            "mobius_prime_factor_count_unique",
            f"forall n b c l d e m. ({_factorization('n','b','c','l','mv_count_first')}) -> "
            f"({_factorization('n','d','e','m','mv_count_second')}) -> l = m",
            ('prime_factor_lists_matching_by_length',),
            _intro('n','b','c','l','d','e','m','ha','hb')
            +(f"have h : {_length_result('b','c','l','d','e','m','mv_count_matching')}",)
            +_call('prime_factor_lists_matching_by_length','l','n','b','c','m','d','e')
            +('exact ha','exact hb','cases h','exact h_left'),
            "Actual unordered prime-factor uniqueness proves literal equality of factor counts; no canonical list is assumed.",
        ),
    )


def _value_rows(spec: Callable[...,Any]) -> tuple[Any,...]:
    return (
        spec(
            "mobius_input_positive",
            f"forall n z. ({_mu('n','z','positive')}) -> ~(n = 0)",
            (), _intro('n','z','h')+('cases h','exact h_left'),
            "The independent Möbius graph explicitly excludes the infinite-divisor boundary zero.",
        ),
        spec(
            "mobius_zero_has_no_value",
            f"forall z. ({_mu('0','z','zero_excluded')}) -> false",
            ('mobius_input_positive',),
            _intro('z','h')+_call('mobius_input_positive','0','z')+('exact h','refl'),
            "No canonical signed value is asserted for the excluded input zero.",
        ),
        spec(
            "mobius_from_prime_square",
            f"forall n p. ~(n = 0) -> ({_prime('p','zero_prime')}) -> "
            f"({_dvd('p * p','n','zero_divisor')}) -> ({_mu('n','0','zero_value')})",
            (),
            _intro('n','p','hn','hp','hdiv')+('split','exact hn','left','split','exists p',
                'split','exact hp','exact hdiv','refl'),
            "A supplied actual prime-square divisor of a positive input constructs its canonical zero Möbius value.",
        ),
        spec(
            "mobius_from_squarefree_factor_count",
            f"forall n b c l z. ({_squarefree('n','constructor_sf')}) -> "
            f"({_factorization('n','b','c','l','mv_constructor_factors')}) -> "
            f"({_sign('l','z','constructor_sign')}) -> ({_mu('n','z','constructor_value')})",
            (),
            _intro('n','b','c','l','z','hsf','hf','hs')+('cases hsf','split','exact hsf_left',
                'right','split','exact hsf','exists b','exists c','exists l','split','exact hf','exact hs'),
            "Squarefreeness, a real prime-factor list and its actual length parity construct the nonzero Möbius value.",
        ),
        spec(
            "mobius_value_exists",
            f"forall n. ~(n = 0) -> exists z. ({_mu('n','z','exists_value')})",
            ('squarefree_or_prime_square_divisor','foundation_prime_factor_list_exists',
             'alternating_signed_unit_exists','mobius_from_squarefree_factor_count','mobius_from_prime_square'),
            _intro('n','hn')
            +(f"have hcase : ({_squarefree('n','exists_decision')}) \\/ exists p. "
              f"({_prime('p','exists_prime')}) /\\ ({_dvd('p * p','n','exists_square')})",)
            +_call('squarefree_or_prime_square_divisor','n')+('exact hn','cases hcase',)
            +(f"have hf : exists l b c. ({_factorization('n','b','c','l','mv_exists_factors')})",)
            +_call('foundation_prime_factor_list_exists','n')+('exact hn',)+_cases('hf',3)
            +(f"have hs : exists z. ({_sign('x','z','exists_sign')})",)
            +_call('alternating_signed_unit_exists','x')+('cases hs','exists x3',)
            +_call('mobius_from_squarefree_factor_count','n','x1','x2','x','x3')
            +('exact hcase_left','exact hf_witness_witness_witness','exact hs_witness',
                'cases hcase_right','cases hcase_right_witness','exists 0')
            +_call('mobius_from_prime_square','n','x')
            +('exact hn','exact hcase_right_witness_left','exact hcase_right_witness_right'),
            "Finite prime-square search, actual prime factorization and parity construct the independently defined Möbius value for every positive natural.",
        ),
        spec(
            "mobius_squarefree_evaluation",
            f"forall n b c l z. ({_squarefree('n','evaluation_sf')}) -> "
            f"({_factorization('n','b','c','l','mv_evaluation_factors')}) -> "
            f"({_mu('n','z','evaluation_value')}) -> ({_sign('l','z','evaluation_result')})",
            ('squarefree_excludes_prime_square','mobius_prime_factor_count_unique'),
            _intro('n','b','c','l','z','hsf','hf','hmu')
            +('cases hmu','cases hmu_right','cases hmu_right_left','cases hmu_right_left_left',
                'cases hmu_right_left_left_witness','exfalso')
            +_call('squarefree_excludes_prime_square','n','x')
            +('exact hsf','exact hmu_right_left_left_witness_left','exact hmu_right_left_left_witness_right',
                'cases hmu_right_right')+_cases('hmu_right_right_right',3)
            +('cases hmu_right_right_right_witness_witness_witness','have heq : x2 = l')
            +_call('mobius_prime_factor_count_unique','n','x','x1','x2','b','c','l')
            +('exact hmu_right_right_right_witness_witness_witness_left','exact hf')
            +_rewrite('heq',_sign('x2','z','evaluation_transport'),'x2',
                'hmu_right_right_right_witness_witness_witness_right')
            +('exact hmu_right_right_right_witness_witness_witness_right',),
            "For a squarefree input, every real factor list computes the same Möbius sign, independently of ordering or chosen witnesses.",
        ),
        spec(
            "mobius_value_functional",
            f"forall n a b. ({_mu('n','a','functional_first')}) -> "
            f"({_mu('n','b','functional_second')}) -> a = b",
            ('squarefree_excludes_prime_square','mobius_squarefree_evaluation','alternating_signed_unit_functional'),
            _intro('n','a','b','ha','hb')+('cases ha','cases ha_right','cases ha_right_left',
                'cases hb','cases hb_right','cases hb_right_left','trans 0','exact ha_right_left_right',
                'symm','exact hb_right_left_right','cases hb_right_right','cases ha_right_left_left',
                'cases ha_right_left_left_witness','exfalso')
            +_call('squarefree_excludes_prime_square','n','x')
            +('exact hb_right_right_left','exact ha_right_left_left_witness_left','exact ha_right_left_left_witness_right',
                'cases ha_right_right')+_cases('ha_right_right_right',3)
            +('cases ha_right_right_right_witness_witness_witness',
                f"have hs : {_sign('x2','b','functional_other_sign')}")
            +_call('mobius_squarefree_evaluation','n','x','x1','x2','b')
            +('exact ha_right_right_left','exact ha_right_right_right_witness_witness_witness_left','exact hb')
            +_call('alternating_signed_unit_functional','x2','a','b')
            +('exact ha_right_right_right_witness_witness_witness_right','exact hs'),
            "Möbius values have literally unique canonical signed codes; square-divisor and squarefree branches are disjoint by proof.",
        ),
        spec(
            "mobius_value_exists_unique",
            f"forall n. ~(n = 0) -> exists z. ({_mu('n','z','unique_chosen')}) /\\ "
            f"forall w. ({_mu('n','w','unique_other')}) -> w = z",
            ('mobius_value_exists','mobius_value_functional'),
            _intro('n','hn')+(f"have hz : exists z. ({_mu('n','z','unique_exists')})",)
            +_call('mobius_value_exists','n')+('exact hn','cases hz','exists x','split','exact hz_witness')
            +_intro('w','hw')+_call('mobius_value_functional','n','w','x')+('exact hw','exact hz_witness'),
            "Every positive natural has one actual, uniquely determined, factorization-defined canonical Möbius value.",
        ),
        spec(
            "mobius_one",
            _mu('1','2','one_value'),
            ('foundation_prime_factor_list_exists','factor_permutation_unit_length_zero',
             'alternating_signed_unit_zero','mobius_from_squarefree_factor_count','squarefree_one'),
            ('have hn : ~(1 = 0)','intro hzero','apply PA1','exact hzero',
                f"have hf : exists l b c. ({_factorization('1','b','c','l','mv_one_factors')})")
            +_call('foundation_prime_factor_list_exists','1')+('exact hn',)+_cases('hf',3)
            +('have heq : x = 0',)+_call('factor_permutation_unit_length_zero','1','x1','x2','x')
            +('exact hf_witness_witness_witness','refl',f"have hs : {_sign('x','2','one_sign')}")
            +_rewrite('heq',_sign('x','2','one_sign_transport'),'x')+('apply alternating_signed_unit_zero',)
            +_call('mobius_from_squarefree_factor_count','1','x1','x2','x','2')
            +('apply squarefree_one','exact hf_witness_witness_witness','exact hs'),
            "The unit boundary has Möbius value positive one (signed code two), proved from its actual empty prime factorization.",
        ),
    )


def make_mobius_value_candidate_theorems(spec: Callable[...,Any]) -> tuple[Any,...]:
    """Return additive ordinary proof scripts; no automatic theorem admission."""
    return _sign_rows(spec)+_value_rows(spec)


__all__ = [
    'alternating_signed_unit_relation', 'has_prime_square_divisor_relation', 'prime_factor_parity_sign_relation',
    'mobius_value_relation', 'make_mobius_value_candidate_theorems',
]
