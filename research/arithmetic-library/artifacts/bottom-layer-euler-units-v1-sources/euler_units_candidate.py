"""Full constructive Euler theorem from actual unit counts and permutations.

The count-prefix induction is separate from the endpoint.  It proves that
scaling exactly the independently decided unit positions multiplies a finite
product by the corresponding actual power.  The endpoint constructs the
weighted factor list, multiplier permutation, reindexed list, product traces,
and power witness, then applies the already proved coprime cancellation law.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_totient_algebra_candidate import _pow
from .euler_totient_count_candidate import _call, _choice, _cop, _count, _intro, _lt, _phi
from .euler_units_product_candidate import _factors, _scale
from .euler_units_residue_candidate import _map, _mod, _unit
from .finite_modular_set_candidate import _compose
from .finite_permutation_theorems import permutation_prefix
from .finite_sum_theorems import _at
from .foundation_saturation_candidate import _product
from .prime_valuation_support_candidate import _rewrite


def _algebra_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "euler_product_scale_shuffle",
            "forall w a P v. (w*a)*(P*v)=(w*P)*(a*v)",
            ("mul_assoc", "natural_mul_swap_right_tail"),
            (*_intro("w","a","P","v"),
             "have hl : (w*a)*(P*v)=w*(a*(P*v))", *_call("mul_assoc","w","a","P*v"),
             "have hm : a*(P*v)=P*(a*v)", *_call("natural_mul_swap_right_tail","a","P","v"),
             "have hr : (w*P)*(a*v)=w*(P*(a*v))", *_call("mul_assoc","w","P","a*v"),
             "rewrite hl", "rewrite hr", "rewrite hm", "refl"),
            "Ordinary multiplication reorders the single newly counted unit multiplier without any arithmetic oracle.",
        ),
        spec(
            "euler_coprime_weighted_product_cancel",
            f"forall m P w. ~(m=0) -> ({_cop('P','m',tag='eu_cancel_product')}) -> ({_mod('m','w*P','P','cancel_balance')}) -> ({_mod('m','w','1','cancel_result')})",
            ("mod_eq_cancel_coprime", "mul_comm", "mul_one"),
            (*_intro("m","P","w","hm","hP","hmod"), *_call("mod_eq_cancel_coprime","m","P","w","1"), "exact hm", "exact hP",
             "have hleft : P*w=w*P", *_call("mul_comm","P","w"), "have hright : P*1=P", *_call("mul_one","P"), "rewrite hleft", "rewrite hright", "exact hmod"),
            "Cancel the proved coprime finite product in a balanced congruence, including the valid modulus-one case.",
        ),
    )


def _count_balance_row(spec: Callable[..., Any]) -> Any:
    return spec(
        "euler_unit_count_product_balance",
        f"forall l a m b c d e t P Q w. ({_count('m','l','t',tag='eu_balance_count')}) -> "
        f"({_scale('a','m','b','c','d','e','l','balance_scale')}) -> ({_product('b','c','l','P','eu_balance_source')}) -> "
        f"({_product('d','e','l','Q','eu_balance_target')}) -> ({_pow('a','t','w',tag='eu_balance_power')}) -> ({_mod('m','w*P','Q','balance_result')})",
        ("totient_unit_count_zero_length", "pow_zero", "beta_product_zero", "one_mul", "mod_eq_refl",
         "totient_unit_count_succ_decompose", "beta_product_succ_decompose", "pow_exists", "euler_unit_scaled_prefix_drop_last", "le_refl",
         "pow_successor_pair_mul", "euler_product_scale_shuffle", "mod_eq_mul", "pow_functional", "mul_assoc"),
        ("induction l", *_intro("a","m","b","c","d","e","t","P","Q","w","ht","hs","hP","hQ","hw"),
         "have ht0 : t=0", *_call("totient_unit_count_zero_length","m","t"), "exact ht",
         "have hw1 : w=1", *_call("pow_zero","a","t","w"), "exact ht0", "exact hw",
         "have hP1 : P=1", *_call("beta_product_zero","b","c","P"), "exact hP",
         "have hQ1 : Q=1", *_call("beta_product_zero","d","e","Q"), "exact hQ",
         "rewrite hw1", "have he : 1*P=P", *_call("one_mul","P"), "rewrite he", "rewrite hP1", "rewrite hQ1", *_call("mod_eq_refl","m","1"),
         *_intro("a","m","b","c","d","e","t","P","Q","w","ht","hs","hP","hQ","hw"),
         f"have hc : exists r f. ({_count('m','l','r',tag='eu_balance_previous_count')}) /\\ (({_choice('m','l','f',tag='eu_balance_last_bit')}) /\\ t=r+f)",
         *_call("totient_unit_count_succ_decompose","m","l","t"), "exact ht", "cases hc", "cases hc_witness", "cases hc_witness_witness", "cases hc_witness_witness_right",
         f"have hp : exists v R. ({_at('b','c','l','v',tag='eu_balance_source_last')}) /\\ (({_product('b','c','l','R','eu_balance_source_previous')}) /\\ P=R*v)",
         *_call("beta_product_succ_decompose","b","c","l","P"), "exact hP", "cases hp", "cases hp_witness", "cases hp_witness_witness", "cases hp_witness_witness_right",
         f"have hq : exists v R. ({_at('d','e','l','v',tag='eu_balance_target_last')}) /\\ (({_product('d','e','l','R','eu_balance_target_previous')}) /\\ Q=R*v)",
         *_call("beta_product_succ_decompose","d","e","l","Q"), "exact hQ", "cases hq", "cases hq_witness", "cases hq_witness_witness", "cases hq_witness_witness_right",
         f"have hz : exists z. ({_pow('a','x','z',tag='eu_balance_previous_power')})", *_call("pow_exists","a","x"), "cases hz",
         f"have hprevious : {_mod('m','x6*x3','x5','balance_previous')}", *_call("IH","a","m","b","c","d","e","x","x3","x5","x6"),
         "exact hc_witness_witness_left", *_call("euler_unit_scaled_prefix_drop_last","a","m","b","c","d","e","l"), "exact hs",
         "exact hp_witness_witness_right_left", "exact hq_witness_witness_right_left", "exact hz_witness",
         f"have hstep : (({_cop('l','m',tag='eu_balance_last_unit')}) -> ({_mod('m','a*x2','x4','balance_last_scaled')})) /\\ "
         f"(~({_cop('l','m',tag='eu_balance_last_nonunit')}) -> ({_mod('m','x2','x4','balance_last_unchanged')}))",
         *_call("hs","l","x2","x4"), *_call("le_refl","S l"), "exact hp_witness_witness_left", "exact hq_witness_witness_left", "cases hstep",
         "cases hc_witness_witness_right_left", "cases hc_witness_witness_right_left_left",
         "have htexp : t=S x", "rewrite hc_witness_witness_right_right", "rewrite hc_witness_witness_right_left_left_right", "simp",
         "have hwp : w=x6*a", *_call("pow_successor_pair_mul","a","x","t","x6","w"), "exact htexp", "exact hz_witness", "exact hw",
         "have hproduct : w*P=(x6*x3)*(a*x2)", "rewrite hwp", "rewrite hp_witness_witness_right_right", *_call("euler_product_scale_shuffle","x6","a","x3","x2"),
         "rewrite hproduct", "rewrite hq_witness_witness_right_right", *_call("mod_eq_mul","m","x6*x3","x5","a*x2","x4"), "exact hprevious", "apply hstep_left", "exact hc_witness_witness_right_left_left_left",
         "cases hc_witness_witness_right_left_right", "have htexp : t=x", "rewrite hc_witness_witness_right_right", "rewrite hc_witness_witness_right_left_right_right", "simp",
         *_rewrite("htexp", _pow('a','t','w',tag='eu_balance_rewrite_power'), "t", "hw"),
         "have hwp : w=x6", *_call("pow_functional","a","x","w","x6"), "exact hw", "exact hz_witness",
         "have hproduct : w*P=(x6*x3)*x2", "rewrite hwp", "rewrite hp_witness_witness_right_right", "symm", *_call("mul_assoc","x6","x3","x2"),
         "rewrite hproduct", "rewrite hq_witness_witness_right_right", *_call("mod_eq_mul","m","x6*x3","x5","x2","x4"), "exact hprevious", "apply hstep_right", "exact hc_witness_witness_right_left_right_left"),
        "Induction on the actual independently counted zero-based unit prefix proves the exact power/product congruence; no Euler conclusion or unit-count oracle is a premise.",
    )


def _endpoint_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "euler_coprime_totient_power_value",
            f"forall a m t w. ~(m=0) -> ({_cop('a','m',tag='eu_endpoint_coprime')}) -> ({_phi('m','t',tag='eu_endpoint_phi')}) -> "
            f"({_pow('a','t','w',tag='eu_endpoint_power')}) -> ({_mod('m','w','1','endpoint_result')})",
            ("euler_unit_product_prefix_exists", "beta_product_exists", "euler_multiplier_permutation_exists", "finite_beta_composition_exists", "beta_product_permutation_invariant",
             "euler_unit_product_reindex_scale", "euler_unit_count_product_balance", "euler_unit_product_coprime", "euler_coprime_weighted_product_cancel"),
            (*_intro("a","m","t","w","hm","ha","ht","hw"), "cases ht",
             f"have hf : exists b c. ({_factors('m','b','c','m','endpoint_factors')})", *_call("euler_unit_product_prefix_exists","m","m"), "cases hf", "cases hf_witness",
             f"have hP : exists P. ({_product('x','x1','m','P','eu_endpoint_product')})", *_call("beta_product_exists","x","x1","m"), "cases hP",
             f"have hmap : exists r s. ({_map('a','m','r','s','m','endpoint_map')}) /\\ ({permutation_prefix('r','s','m',tag='eu_endpoint_permutation')})",
             *_call("euler_multiplier_permutation_exists","a","m"), "exact hm", "exact ha", "cases hmap", "cases hmap_witness", "cases hmap_witness_witness", "cases hmap_witness_witness_right", "cases hmap_witness_witness_right_right",
             f"have hcomp : exists z d. ({_compose('x3','x4','x','x1','z','d','m',tag='eu_endpoint_composition')})", *_call("finite_beta_composition_exists","x3","x4","x","x1","m"), "cases hcomp", "cases hcomp_witness",
             f"have hQ : exists Q. ({_product('x5','x6','m','Q','eu_endpoint_target_product')})", *_call("beta_product_exists","x5","x6","m"), "cases hQ",
             "have he : x7=x2", "symm", *_call("beta_product_permutation_invariant","m","x3","x4","x","x1","x5","x6","x2","x7"),
             "exact hmap_witness_witness_right_left", "exact hmap_witness_witness_right_right_left", "exact hcomp_witness_witness", "exact hP_witness", "exact hQ_witness",
             f"have hs : {_scale('a','m','x','x1','x5','x6','m','endpoint_scaled')}", *_call("euler_unit_product_reindex_scale","a","m","x3","x4","x","x1","x5","x6"),
             "exact ha", "exact hmap_witness_witness_left", "exact hf_witness_witness", "exact hcomp_witness_witness",
             f"have hbalance : {_mod('m','w*x2','x7','endpoint_balance')}", *_call("euler_unit_count_product_balance","m","a","m","x","x1","x5","x6","t","x2","x7","w"),
             "exact ht_right", "exact hs", "exact hP_witness", "exact hQ_witness", "exact hw", "rewrite he at hbalance",
             *_call("euler_coprime_weighted_product_cancel","m","x2","w"), "exact hm", *_call("euler_unit_product_coprime","m","m","x","x1","x2"), "exact hf_witness_witness", "exact hP_witness", "exact hbalance"),
            "For every positive modulus and any actual Phi and Pow values, construct all finite permutation/product witnesses and prove the Euler congruence by coprime cancellation.",
        ),
        spec(
            "euler_coprime_totient_power",
            f"forall a m t. ~(m=0) -> ({_cop('a','m',tag='eu_exists_coprime')}) -> ({_phi('m','t',tag='eu_exists_phi')}) -> "
            f"exists w. ({_pow('a','t','w',tag='eu_exists_power')}) /\\ ({_mod('m','w','1','exists_result')})",
            ("pow_exists", "euler_coprime_totient_power_value"),
            (*_intro("a","m","t","hm","hc","ht"), f"have hw : exists w. ({_pow('a','t','w',tag='eu_constructed_power')})", *_call("pow_exists","a","t"), "cases hw",
             "exists x", "split", "exact hw_witness", *_call("euler_coprime_totient_power_value","a","m","t","x"), "exact hm", "exact hc", "exact ht", "exact hw_witness"),
            "Construct the actual exponentiation witness for Euler's theorem at every positive modulus, without supplying a power, factor list, or permutation.",
        ),
        spec(
            "euler_modular_unit_totient_power",
            f"forall a m t. ({_unit('a','m','unit_endpoint')}) -> ({_phi('m','t',tag='eu_unit_endpoint_phi')}) -> "
            f"exists w. ({_pow('a','t','w',tag='eu_unit_endpoint_power')}) /\\ ({_mod('m','w','1','unit_endpoint_result')})",
            ("euler_coprime_totient_power", "euler_modulus_above_one_nonzero", "euler_modular_unit_coprime"),
            (*_intro("a","m","t","hu","ht"), "cases hu", *_call("euler_coprime_totient_power","a","m","t"),
             "intro hz", *_call("euler_modulus_above_one_nonzero","m"), "exact hu_left", "exact hz",
             *_call("euler_modular_unit_coprime","a","m"), "exact hu", "exact ht"),
            "The exact actual-inverse Unit graph suffices for a constructed Euler power; no prime-modulus restriction is introduced.",
        ),
        spec(
            "euler_theorem_for_units",
            f"forall a m t. (({_lt('1','m',tag='eu_G014_domain')}) /\\ (({_unit('a','m','G014_unit')}) /\\ ({_phi('m','t',tag='eu_G014_phi')}))) -> "
            f"exists w. ({_pow('a','t','w',tag='eu_G014_power')}) /\\ ({_mod('m','w','1','G014_result')})",
            ("euler_modular_unit_totient_power",),
            (*_intro("a","m","t","h"), "cases h", "cases h_right", *_call("euler_modular_unit_totient_power","a","m","t"), "exact h_right_left", "exact h_right_right"),
            "Full exact G014: m>1 and a genuinely witnessed modular unit and independently counted Phi imply an actual Pow witness congruent to one.",
        ),
    )


def make_euler_units_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (*_algebra_rows(spec), _count_balance_row(spec), *_endpoint_rows(spec))


__all__ = ["make_euler_units_candidate_theorems"]
