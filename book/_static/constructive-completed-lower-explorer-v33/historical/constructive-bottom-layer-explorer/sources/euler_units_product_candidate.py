"""Actual coprime-weighted finite products for Euler's theorem.

The factor at i is i when Coprime(i,m), and one otherwise.  Neither the
factor graph nor its beta prefix mentions Phi, exponentiation, or the Euler
conclusion.  The same frozen zero-based interval is used by the unit count.
"""

from __future__ import annotations

from typing import Any, Callable

from .euler_totient_count_candidate import _call, _cop, _intro, _lt
from .euler_units_residue_candidate import _checked, _map, _mod
from .finite_modular_set_candidate import _compose
from .finite_sum_theorems import _at
from .foundation_saturation_candidate import _product
from .prime_valuation_support_candidate import _rewrite


def _factor(m: str, i: str, v: str, tag: str) -> str:
    predicate = _cop(i, m, tag="eu_" + tag + "_coprime")
    return f"((({predicate}) /\\ ({v})=({i})) \\/ (~({predicate}) /\\ ({v})=1))"


def _factors(m: str, b: str, c: str, l: str, tag: str) -> str:
    i, v = f"eu_factor_index_{tag}", f"eu_factor_value_{tag}"
    return f"forall {i}. ({_lt(i,l,tag='eu_'+tag+'_index')}) -> exists {v}. " \
        f"({_at(b,c,i,v,tag='eu_'+tag+'_at')}) /\\ ({_factor(m,i,v,tag+'_choice')})"


def _scale(a: str, m: str, b: str, c: str, d: str, e: str, l: str, tag: str) -> str:
    i, u, v = (f"eu_scale_{role}_{tag}" for role in ("index", "source", "target"))
    unit = _cop(i,m,tag="eu_"+tag+"_unit")
    return f"forall {i} {u} {v}. ({_lt(i,l,tag='eu_'+tag+'_index')}) -> " \
        f"({_at(b,c,i,u,tag='eu_'+tag+'_source')}) -> ({_at(d,e,i,v,tag='eu_'+tag+'_target')}) -> " \
        f"((({unit}) -> ({_mod(m,f'({a})*{u}',v,tag+'_scaled')})) /\\ " \
        f"(~({unit}) -> ({_mod(m,u,v,tag+'_unchanged')})))"


def unit_product_factor_relation(modulus: str, index: str, factor: str, *, tag: str, variables: tuple[str, ...] | None = None) -> str:
    """The independently decided factor i for coprime i, and one otherwise."""
    return _checked(_factor, (modulus, index, factor), tag, variables)


def unit_product_prefix_relation(modulus: str, code: str, scale: str, length: str, *, tag: str, variables: tuple[str, ...] | None = None) -> str:
    """An actual beta prefix of the coprime-weighted factors on 0<=i<length."""
    return _checked(_factors, (modulus, code, scale, length), tag, variables)


def unit_scaled_prefix_relation(multiplier: str, modulus: str, source_code: str, source_scale: str, target_code: str, target_scale: str, length: str, *, tag: str, variables: tuple[str, ...] | None = None) -> str:
    """Multiply exactly the coprime-index factors modulo m; leave others unchanged."""
    return _checked(_scale, (multiplier, modulus, source_code, source_scale, target_code, target_scale, length), tag, variables)


def _factor_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "euler_unit_product_factor_exists",
            f"forall m i. exists v. ({_factor('m','i','v','factor_exists')})",
            ("totient_coprime_decidable",),
            (*_intro("m","i"), f"have hc : ({_cop('i','m',tag='eu_factor_yes')}) \\/ ~({_cop('i','m',tag='eu_factor_no')})",
             *_call("totient_coprime_decidable","i","m"), "cases hc", "exists i", "left", "split", "exact hc_left", "refl",
             "exists 1", "right", "split", "exact hc_right", "refl"),
            "Construct the actual weighted factor by the independent decidable coprimality predicate.",
        ),
        spec(
            "euler_unit_product_factor_unit_value",
            f"forall m i v. ({_cop('i','m',tag='eu_factor_unit')}) -> ({_factor('m','i','v','factor_unit')}) -> v=i",
            (),
            (*_intro("m","i","v","hc","hf"), "cases hf", "cases hf_left", "exact hf_left_right", "cases hf_right", "exfalso", "apply hf_right_left", "exact hc"),
            "At a genuine unit index the weighted factor is the index itself.",
        ),
        spec(
            "euler_unit_product_factor_nonunit_value",
            f"forall m i v. ~({_cop('i','m',tag='eu_factor_nonunit')}) -> ({_factor('m','i','v','factor_nonunit')}) -> v=1",
            (),
            (*_intro("m","i","v","hc","hf"), "cases hf", "cases hf_left", "exfalso", "apply hc", "exact hf_left_left", "cases hf_right", "exact hf_right_right"),
            "A nonunit index contributes exactly one, not a zero or an assumed cancellable residue.",
        ),
        spec(
            "euler_unit_product_factor_coprime",
            f"forall m i v. ({_factor('m','i','v','factor_coprime')}) -> ({_cop('v','m',tag='eu_factor_result_coprime')})",
            ("coprime_one_left",),
            (*_intro("m","i","v","hf"), "cases hf", "cases hf_left", "rewrite hf_left_right", "exact hf_left_left",
             "cases hf_right", "rewrite hf_right_right", *_call("coprime_one_left","m")),
            "Every weighted factor is coprime to the modulus, including the modulus-one zero factor.",
        ),
    )


def _prefix_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "euler_unit_product_prefix_empty",
            f"forall m b c. ({_factors('m','b','c','0','factors_empty')})",
            ("lt_not_le", "zero_le"),
            (*_intro("m","b","c","i","hi"), "exfalso", *_call("lt_not_le","i","0"), "exact hi", *_call("zero_le","i")),
            "The empty weighted-factor prefix is valid for any beta codes.",
        ),
        spec(
            "euler_unit_product_prefix_extend",
            f"forall m b c l v. ({_factors('m','b','c','l','factors_extend_old')}) -> ({_factor('m','l','v','factor_extend_last')}) -> "
            f"exists d e. ({_factors('m','d','e','S l','factors_extend_new')})",
            ("beta_prefix_extend", "finite_lt_succ_eq_or_lt"),
            (*_intro("m","b","c","l","v","h","hv"), "specialize beta_prefix_extend l", "specialize beta_prefix_extend b", "specialize beta_prefix_extend c", "specialize beta_prefix_extend v",
             "cases beta_prefix_extend", "cases beta_prefix_extend_witness", "cases beta_prefix_extend_witness_witness", "exists x", "exists x1", *_intro("i","hi"),
             f"have hs : i=l \\/ ({_lt('i','l',tag='eu_factor_extend_index')})", *_call("finite_lt_succ_eq_or_lt","l","i"), "exact hi", "cases hs", "exists v", "split",
             "rewrite hs_left", "rewrite hs_left", "exact beta_prefix_extend_witness_witness_left",
             *_rewrite("hs_left", _factor('m','i','v','rewrite_factor_last'), "i"), "exact hv",
             f"have hp : exists w. ({_at('b','c','i','w',tag='eu_factor_extend_old')}) /\\ ({_factor('m','i','w','factor_extend_old')})",
             *_call("h","i"), "exact hs_right", "cases hp", "cases hp_witness", "exists x2", "split",
             *_call("beta_prefix_extend_witness_witness_right","i","x2"), "exact hs_right", "exact hp_witness_left", "exact hp_witness_right"),
            "Actually append the independently chosen next factor while preserving every earlier factor.",
        ),
        spec(
            "euler_unit_product_prefix_exists",
            f"forall m l. exists b c. ({_factors('m','b','c','l','factors_exists')})",
            ("euler_unit_product_prefix_empty", "euler_unit_product_factor_exists", "euler_unit_product_prefix_extend"),
            ("intro m", "induction l", "exists 0", "exists 0", *_call("euler_unit_product_prefix_empty","m","0","0"),
             "cases IH", "cases IH_witness", f"have hv : exists v. ({_factor('m','l','v','factor_next')})", *_call("euler_unit_product_factor_exists","m","l"), "cases hv",
             *_call("euler_unit_product_prefix_extend","m","x","x1","l","x2"), "exact IH_witness_witness", "exact hv_witness"),
            "HA induction constructs all coprime-weighted factors; their list is never an endpoint assumption.",
        ),
        spec(
            "euler_unit_product_prefix_drop_last",
            f"forall m b c l. ({_factors('m','b','c','S l','factors_drop_old')}) -> ({_factors('m','b','c','l','factors_drop_new')})",
            ("le_succ",),
            (*_intro("m","b","c","l","h","i","hi"), *_call("h","i"), *_call("le_succ","S i","l"), "exact hi"),
            "Restrict an actual weighted-factor prefix to its predecessor interval.",
        ),
        spec(
            "euler_unit_product_prefix_entry",
            f"forall m b c l i v. ({_factors('m','b','c','l','factors_entry')}) -> ({_lt('i','l',tag='eu_factor_entry_bound')}) -> "
            f"({_at('b','c','i','v',tag='eu_factor_entry_given')}) -> ({_factor('m','i','v','factor_entry')})",
            ("beta_at_unique",),
            (*_intro("m","b","c","l","i","v","h","hi","hv"),
             f"have hp : exists w. ({_at('b','c','i','w',tag='eu_factor_entry_chosen')}) /\\ ({_factor('m','i','w','factor_entry_chosen')})",
             *_call("h","i"), "exact hi", "cases hp", "cases hp_witness", "have he : x=v", *_call("beta_at_unique","b","c","i","x","v"), "exact hp_witness_left", "exact hv",
             "rewrite he at hp_witness_right", "rewrite he at hp_witness_right", "exact hp_witness_right"),
            "The weighted-factor choice holds for every actual decoded entry, independently of beta encoding.",
        ),
        spec(
            "euler_unit_product_coprime",
            f"forall l m b c P. ({_factors('m','b','c','l','product_coprime_factors')}) -> ({_product('b','c','l','P','eu_product_coprime')}) -> ({_cop('P','m',tag='eu_product_coprime')})",
            ("beta_product_zero", "coprime_one_left", "beta_product_succ_decompose", "euler_unit_product_prefix_drop_last", "euler_unit_product_prefix_entry", "euler_unit_product_factor_coprime", "coprime_mul_left", "le_refl"),
            ("induction l", *_intro("m","b","c","P","hf","hP"), "have he : P=1", *_call("beta_product_zero","b","c","P"), "exact hP", "rewrite he", *_call("coprime_one_left","m"),
             *_intro("m","b","c","P","hf","hP"), f"have hd : exists v Q. ({_at('b','c','l','v',tag='eu_product_last')}) /\\ (({_product('b','c','l','Q','eu_product_previous')}) /\\ P=Q*v)",
             *_call("beta_product_succ_decompose","b","c","l","P"), "exact hP", "cases hd", "cases hd_witness", "cases hd_witness_witness", "cases hd_witness_witness_right",
             "rewrite hd_witness_witness_right_right", *_call("coprime_mul_left","x1","x","m"), *_call("IH","m","b","c","x1"),
             *_call("euler_unit_product_prefix_drop_last","m","b","c","l"), "exact hf", "exact hd_witness_witness_right_left",
             *_call("euler_unit_product_factor_coprime","m","l","x"), *_call("euler_unit_product_prefix_entry","m","b","c","S l","l","x"), "exact hf", *_call("le_refl","S l"), "exact hd_witness_witness_left"),
            "The entire actual unit-weighted product is coprime to m; this is the proved cancellation premise.",
        ),
    )


def _scale_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "euler_unit_factor_scaled_congruence",
            f"forall a m i r u v. ({_cop('a','m',tag='eu_scale_multiplier')}) -> ({_mod('m','a*i','r','scale_residue')}) -> "
            f"({_factor('m','i','u','scale_source')}) -> ({_factor('m','r','v','scale_target')}) -> ({_cop('i','m',tag='eu_scale_index_unit')}) -> ({_mod('m','a*u','v','scale_result')})",
            ("euler_multiplier_coprime_iff", "euler_unit_product_factor_unit_value"),
            (*_intro("a","m","i","r","u","v","ha","hmod","hu","hv","hi"),
             f"have hequiv : (({_cop('i','m',tag='eu_scale_left')}) -> ({_cop('r','m',tag='eu_scale_right')})) /\\ (({_cop('r','m',tag='eu_scale_right_back')}) -> ({_cop('i','m',tag='eu_scale_left_back')}))",
             *_call("euler_multiplier_coprime_iff","a","m","i","r"), "exact ha", "exact hmod", "cases hequiv",
             "have he : u=i", *_call("euler_unit_product_factor_unit_value","m","i","u"), "exact hi", "exact hu",
             "have hf : v=r", *_call("euler_unit_product_factor_unit_value","m","r","v"), "apply hequiv_left", "exact hi", "exact hv",
             "rewrite he", "rewrite hf", "exact hmod"),
            "A unit index contributes exactly one multiplier factor under the actual residue permutation.",
        ),
        spec(
            "euler_nonunit_factor_unchanged_congruence",
            f"forall a m i r u v. ({_cop('a','m',tag='eu_no_scale_multiplier')}) -> ({_mod('m','a*i','r','no_scale_residue')}) -> "
            f"({_factor('m','i','u','no_scale_source')}) -> ({_factor('m','r','v','no_scale_target')}) -> ~({_cop('i','m',tag='eu_no_scale_index')}) -> ({_mod('m','u','v','no_scale_result')})",
            ("euler_multiplier_coprime_iff", "euler_unit_product_factor_nonunit_value", "mod_eq_refl"),
            (*_intro("a","m","i","r","u","v","ha","hmod","hu","hv","hi"),
             f"have hequiv : (({_cop('i','m',tag='eu_no_scale_left')}) -> ({_cop('r','m',tag='eu_no_scale_right')})) /\\ (({_cop('r','m',tag='eu_no_scale_right_back')}) -> ({_cop('i','m',tag='eu_no_scale_left_back')}))",
             *_call("euler_multiplier_coprime_iff","a","m","i","r"), "exact ha", "exact hmod", "cases hequiv",
             "have he : u=1", *_call("euler_unit_product_factor_nonunit_value","m","i","u"), "exact hi", "exact hu",
             "have hf : v=1", *_call("euler_unit_product_factor_nonunit_value","m","r","v"), "intro hr", "apply hi", "apply hequiv_right", "exact hr", "exact hv",
             "rewrite he", "rewrite hf", *_call("mod_eq_refl","m","1")),
            "A nonunit index and its image both contribute one, so neither adds to the exponent.",
        ),
        spec(
            "euler_unit_scaled_prefix_drop_last",
            f"forall a m b c d e l. ({_scale('a','m','b','c','d','e','S l','scale_drop_old')}) -> ({_scale('a','m','b','c','d','e','l','scale_drop_new')})",
            ("le_succ",),
            (*_intro("a","m","b","c","d","e","l","h","i","u","v","hi","hu","hv"), *_call("h","i","u","v"), *_call("le_succ","S i","l"), "exact hi", "exact hu", "exact hv"),
            "Restrict the independently specified unit-scaled action to its predecessor prefix.",
        ),
        spec(
            "euler_unit_product_reindex_scale",
            f"forall a m r s b c z d. ({_cop('a','m',tag='eu_reindex_unit')}) -> ({_map('a','m','r','s','m','reindex_map')}) -> "
            f"({_factors('m','b','c','m','reindex_factors')}) -> ({_compose('r','s','b','c','z','d','m',tag='eu_reindex_composition')}) -> ({_scale('a','m','b','c','z','d','m','reindex_scale')})",
            ("euler_unit_product_prefix_entry", "beta_at_unique", "euler_unit_factor_scaled_congruence", "euler_nonunit_factor_unchanged_congruence"),
            (*_intro("a","m","r","s","b","c","z","d","ha","hmap","hfac","hcomp","i","u","v","hi","hu","hv"),
             f"have hindex : exists j. ({_at('r','s','i','j',tag='eu_reindex_index')}) /\\ (({_lt('j','m',tag='eu_reindex_bound')}) /\\ ({_mod('m','a*i','j','reindex_mod')}))",
             *_call("hmap","i"), "exact hi", "cases hindex", "cases hindex_witness", "cases hindex_witness_right",
             f"have hsource : {_factor('m','i','u','reindex_source_choice')}", *_call("euler_unit_product_prefix_entry","m","b","c","m","i","u"), "exact hfac", "exact hi", "exact hu",
             f"have htarget : exists w. ({_at('b','c','x','w',tag='eu_reindex_chosen_at')}) /\\ ({_factor('m','x','w','reindex_chosen_factor')})",
             *_call("hfac","x"), "exact hindex_witness_right_left", "cases htarget", "cases htarget_witness",
             "have he : x1=v", *_call("beta_at_unique","z","d","i","x1","v"), *_call("hcomp","i","x","x1"), "exact hi", "exact hindex_witness_left", "exact htarget_witness_left", "exact hv",
             "rewrite he at htarget_witness_right", "rewrite he at htarget_witness_right", "split", "intro hunit",
             *_call("euler_unit_factor_scaled_congruence","a","m","i","x","u","v"), "exact ha", "exact hindex_witness_right_right", "exact hsource", "exact htarget_witness_right", "exact hunit",
             "intro hnot", *_call("euler_nonunit_factor_unchanged_congruence","a","m","i","x","u","v"), "exact ha", "exact hindex_witness_right_right", "exact hsource", "exact htarget_witness_right", "exact hnot"),
            "Actual beta composition along the multiplier permutation scales precisely the factors counted by Phi.",
        ),
    )


def make_euler_units_product_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (*_factor_rows(spec), *_prefix_rows(spec), *_scale_rows(spec))


__all__ = ["unit_product_factor_relation", "unit_product_prefix_relation", "unit_scaled_prefix_relation", "make_euler_units_product_candidate_theorems"]
