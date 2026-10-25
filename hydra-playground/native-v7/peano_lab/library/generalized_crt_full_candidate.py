"""Full finite-list generalized CRT over unchanged constructive arithmetic.

This additive candidate proves the missing unrestricted gcd--LCM lattice
identity and uses it to discharge, rather than assume, every predecessor-LCM
merge condition.  Historical Alpha catalogues and definitions are not changed.
All displayed relations are hygienic first-order abbreviations; proof bodies
contain only ordinary original-kernel tactics.
"""

from __future__ import annotations

from typing import Any, Callable

from ..kernel.terms import parse_term_with_names
from .euclidean_complexity_candidate import _gcd_term
from .fermat_residue_product_candidate import coprime
from .generalized_crt_compatibility_candidate import (
    _arguments as _compatibility_arguments, _merge_terms, _pairwise_terms,
)
from .generalized_crt_fold_candidate import (
    _at, _bound, _canonical_terms, _lcm_terms, _positive_terms, _safe, _solution_terms,
)
from .ha_generalized_crt_congruence_candidate import _checked_term, balanced_mod_eq
from .ha_lcm_totality_bridge_candidate import _term_is_lcm


def _context(*terms: str) -> tuple[str, ...]:
    names = tuple(dict.fromkeys(name for term in terms for name in parse_term_with_names(term)[1]))
    return names or ("gfull_unused",)


def _gcd(g: str, a: str, b: str, *, tag: str) -> str:
    context = _context(g, a, b)
    return _gcd_term(
        *(_checked_term(term, context) for term in (g, a, b)),
        tag=f"gfull_{tag}", arguments=context,
    )


def _lcm(L: str, a: str, b: str, *, tag: str) -> str:
    return _term_is_lcm(L, a, b, tag=f"gfull_{tag}", variables=_context(L, a, b))


def _mod(d: str, a: str, b: str, *, tag: str) -> str:
    return balanced_mod_eq(d, a, b, tag=f"gfull_{tag}", variables=_context(d, a, b))


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return (*(f"specialize {name} {argument}" for argument in arguments), f"apply {name}")


def _intros(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def _rewrite(equation: str, count: int, *, at: str | None = None) -> tuple[str, ...]:
    return (f"rewrite {equation}" + (f" at {at}" if at else ""),) * count


def _expand(builder: Callable[..., str], *arguments: str, tag: str) -> str:
    return builder(*arguments, tag=f"gfull_{tag}", context=_context(*arguments))


def _prefix_gcd_terms(b: str, c: str, l: str, n: str, u: str, v: str, *, tag: str) -> str:
    context = _context(b, c, l, n, u, v)
    index, modulus, gcd = (f"gfull_{role}_{_safe(tag)}" for role in ("index", "modulus", "gcd"))
    if {index, modulus, gcd} & set(context):
        raise ValueError("generated finite-gcd-congruence binder captures an argument")
    local = context + (index, modulus, gcd)
    return (
        f"forall {index} {modulus} {gcd}. "
        f"({_bound(index, l, tag=f'gfull_{tag}_bound', context=local)}) -> "
        f"({_at(b, c, index, modulus, tag=f'gfull_{tag}_entry', context=local)}) -> "
        f"({_gcd(gcd, modulus, n, tag=f'{tag}_gcd')}) -> "
        f"({_mod(gcd, u, v, tag=f'{tag}_mod')})"
    )


def crt_prefix_gcd_congruences(
    modulus_code: str, modulus_scale: str, length: str,
    comparison_modulus: str, left: str, right: str, *, tag: str,
) -> str:
    """Expand congruence modulo every decoded modulus/comparison gcd."""

    values = _compatibility_arguments(*zip(
        (modulus_code, modulus_scale, length, comparison_modulus, left, right),
        ("modulus code", "modulus scale", "prefix length", "comparison modulus", "left residue", "right residue"),
    ))
    if any(value.startswith(("gfull_", "ec_", "hscale_")) for value in values):
        raise ValueError("generated finite-gcd-congruence binder captures an argument")
    return _prefix_gcd_terms(*values, tag=_safe(tag))


def _normalized_terms(r: str, s: str, b: str, c: str, l: str, x: str, M: str, *, tag: str) -> str:
    least = _expand(_lcm_terms, b, c, l, M, tag=f"{tag}_lcm")
    bounded = _expand(_bound, x, M, tag=f"{tag}_bound")
    solution = _expand(_solution_terms, r, s, b, c, l, x, tag=f"{tag}_solution")
    return f"(({least}) /\\ (({M} = 0 \\/ ({bounded})) /\\ ({solution})))"


def crt_normalized_prefix_solution(
    residue_code: str, residue_scale: str, modulus_code: str, modulus_scale: str,
    length: str, value: str, modulus: str, *, tag: str,
) -> str:
    """Expand the exact list LCM, zero-or-strict bound, and actual solution.

    When the LCM is zero, simultaneous congruence is still required and its
    uniqueness follows from the proved zero-LCM solution theorem.  This does
    not alter the historical, positive-modulus canonical definition.
    """

    values = _compatibility_arguments(*zip(
        (residue_code, residue_scale, modulus_code, modulus_scale, length, value, modulus),
        ("residue code", "residue scale", "modulus code", "modulus scale", "prefix length", "solution", "list lcm"),
    ))
    if any(item.startswith(("gfull_", "ec_", "hscale_")) for item in values):
        raise ValueError("generated normalized-CRT binder captures an argument")
    return _normalized_terms(*values, tag=_safe(tag))


def make_generalized_crt_full_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Return ordered genuine proof bodies; this factory grants no admission."""

    return (
        spec(
            "crt_gcd_zero_right_value",
            f"forall a g. ({_gcd('g', 'a', '0', tag='zero_right')}) -> g = a",
            ("canonical_gcd_zero_right_iff",),
            (*_intros("a", "g", "hg"),
             "specialize canonical_gcd_zero_right_iff a",
             "specialize canonical_gcd_zero_right_iff g",
             "cases canonical_gcd_zero_right_iff",
             "apply canonical_gcd_zero_right_iff_left", "exact hg"),
            "A relational gcd with zero on the right equals its other input.",
        ),
        spec(
            "crt_gcd_nonzero_left",
            f"forall a b g. ~(a = 0) -> ({_gcd('g', 'a', 'b', tag='nonzero')}) -> ~(g = 0)",
            ("is_gcd_dvd_left", "factor_nonzero_left"),
            (*_intros("a", "b", "g", "ha", "hg"),
             "have hdiv : exists q. a = g * q",
             *_call("is_gcd_dvd_left", "g", "a", "b"), "exact hg", "cases hdiv",
             "intro hz", *_call("factor_nonzero_left", "a", "g", "x"),
             "exact ha", "exact hdiv_witness", "exact hz"),
            "A gcd of a nonzero left input is nonzero, without restricting the right input.",
        ),
        spec(
            "crt_gcd_nonzero_right",
            f"forall a b g. ~(b = 0) -> ({_gcd('g', 'a', 'b', tag='nonzero_right')}) -> ~(g = 0)",
            ("crt_gcd_nonzero_left", "is_gcd_symm"),
            (*_intros("a", "b", "g", "hb", "hg", "hz"),
             *_call("crt_gcd_nonzero_left", "b", "a", "g"), "exact hb",
             *_call("is_gcd_symm", "g", "a", "b"), "exact hg", "exact hz"),
            "A gcd of a nonzero right input is nonzero, including a zero left input.",
        ),
        spec(
            "crt_gcd_coprime_cofactors",
            f"forall a b g. ~(g = 0) -> ({_gcd('g', 'a', 'b', tag='cofactors')}) -> "
            f"exists A B. (a = g * A /\\ (b = g * B /\\ ({coprime('A', 'B', tag='gfull_cofactors')})))",
            ("is_gcd_dvd_left", "is_gcd_dvd_right", "is_gcd_quotients_coprime_nonzero"),
            (*_intros("a", "b", "g", "hn", "hg"),
             "have hleft : exists A. a = g * A",
             *_call("is_gcd_dvd_left", "g", "a", "b"), "exact hg", "cases hleft",
             "have hright : exists B. b = g * B",
             *_call("is_gcd_dvd_right", "g", "a", "b"), "exact hg", "cases hright",
             "exists x", "exists x1", "split", "exact hleft_witness", "split", "exact hright_witness",
             *_call("is_gcd_quotients_coprime_nonzero", "g", "a", "b", "x", "x1"),
             "exact hg", "exact hn", "exact hleft_witness", "exact hright_witness"),
            "A nonzero gcd yields both exact natural cofactors and their constructive coprimality.",
        ),
        spec(
            "crt_gcd_lcm_distributes_scaled_coprime",
            "forall k n d K N a b L ga gb g. "
            "k = d * K -> n = d * N -> ~(d = 0) -> ~(N = 0) -> "
            f"({coprime('K', 'N', tag='gfull_scaled_comparison')}) -> "
            f"({coprime('a', 'b', tag='gfull_scaled_factors')}) -> L = k * (a * b) -> "
            f"({_gcd('ga', 'k * a', 'n', tag='scaled_ga')}) -> "
            f"({_gcd('gb', 'k * b', 'n', tag='scaled_gb')}) -> "
            f"({_gcd('g', 'L', 'n', tag='scaled_g')}) -> "
            f"({_lcm('g', 'ga', 'gb', tag='scaled_result')})",
            ("canonical_gcd_exists", "crt_coprime_divisor_pair", "is_gcd_dvd_left",
             "crt_is_gcd_coprime_product", "crt_gcd_scaled_coprime_component",
             "is_gcd_unique", "is_lcm_scale_nonzero", "coprime_product_is_lcm"),
            (*_intros("k", "n", "d", "K", "N", "a", "b", "L", "ga", "gb", "g",
                      "hk", "hn", "hd", "hN", "hKN", "hab", "hL", "hga", "hgb", "hg"),
             "have hau : exists u. " + _gcd("u", "a", "N", tag="scaled_u"),
             *_call("canonical_gcd_exists", "a", "N"), "cases hau",
             "have hbv : exists v. " + _gcd("v", "b", "N", tag="scaled_v"),
             *_call("canonical_gcd_exists", "b", "N"), "cases hbv",
             f"have huv : {coprime('x', 'x1', tag='gfull_scaled_uv')}",
             *_call("crt_coprime_divisor_pair", "a", "b", "x", "x1"), "exact hab",
             *_call("is_gcd_dvd_left", "x", "a", "N"), "exact hau_witness",
             *_call("is_gcd_dvd_left", "x1", "b", "N"), "exact hbv_witness",
             "have hproduct : " + _gcd("x * x1", "a * b", "N", tag="scaled_product"),
             *_call("crt_is_gcd_coprime_product", "a", "b", "N", "x", "x1", "(x * x1)", "(a * b)"),
             "exact hN", "refl", "refl", "exact hab", "exact hau_witness", "exact hbv_witness",
             "have hua : " + _gcd("d * x", "k * a", "n", tag="scaled_ua"),
             *_call("crt_gcd_scaled_coprime_component", "k", "n", "d", "K", "N", "a", "x", "(k * a)", "(d * x)"),
             "exact hk", "exact hn", "refl", "refl", "exact hKN", "exact hau_witness",
             "have hvb : " + _gcd("d * x1", "k * b", "n", tag="scaled_vb"),
             *_call("crt_gcd_scaled_coprime_component", "k", "n", "d", "K", "N", "b", "x1", "(k * b)", "(d * x1)"),
             "exact hk", "exact hn", "refl", "refl", "exact hKN", "exact hbv_witness",
             "have hw : " + _gcd("d * (x * x1)", "L", "n", tag="scaled_w"),
             *_call("crt_gcd_scaled_coprime_component", "k", "n", "d", "K", "N", "(a * b)", "(x * x1)", "L", "(d * (x * x1))"),
             "exact hk", "exact hn", "exact hL", "refl", "exact hKN", "exact hproduct",
             "have heqa : ga = d * x", *_call("is_gcd_unique", "ga", "(d * x)", "(k * a)", "n"),
             "exact hga", "exact hua",
             "have heqb : gb = d * x1", *_call("is_gcd_unique", "gb", "(d * x1)", "(k * b)", "n"),
             "exact hgb", "exact hvb",
             "have heqg : g = d * (x * x1)", *_call("is_gcd_unique", "g", "(d * (x * x1))", "L", "n"),
             "exact hg", "exact hw",
             "have hlcm : " + _lcm("d * (x * x1)", "d * x", "d * x1", tag="scaled_lcm"),
             *_call("is_lcm_scale_nonzero", "d", "(x * x1)", "x", "x1"), "exact hd",
             *_call("coprime_product_is_lcm", "x", "x1"), "exact huv",
             *_rewrite("heqa", 2), *_rewrite("heqb", 2), *_rewrite("heqg", 3), "exact hlcm"),
            "Factoring a common gcd scale reduces unrestricted gcd--LCM distributivity to genuinely coprime cofactors.",
        ),
        spec(
            "crt_gcd_lcm_distributes_nonzero",
            "forall a b n L ga gb g. ~(a = 0) -> ~(n = 0) -> "
            f"({_lcm('L', 'a', 'b', tag='nonzero_L')}) -> "
            f"({_gcd('ga', 'a', 'n', tag='nonzero_ga')}) -> "
            f"({_gcd('gb', 'b', 'n', tag='nonzero_gb')}) -> "
            f"({_gcd('g', 'L', 'n', tag='nonzero_g')}) -> "
            f"({_lcm('g', 'ga', 'gb', tag='nonzero_result')})",
            ("canonical_gcd_exists", "crt_gcd_nonzero_left", "crt_gcd_nonzero_right",
             "crt_gcd_coprime_cofactors", "factor_nonzero_right",
             "crt_lcm_gcd_cofactor_product", "crt_gcd_lcm_distributes_scaled_coprime"),
            (*_intros("a", "b", "n", "L", "ga", "gb", "g", "ha", "hn", "hL", "hga", "hgb", "hg"),
             "have hd : exists d. " + _gcd("d", "a", "b", tag="nonzero_d"),
             *_call("canonical_gcd_exists", "a", "b"), "cases hd",
             "have hdnonzero : ~(x = 0)", "intro hz",
             *_call("crt_gcd_nonzero_left", "a", "b", "x"), "exact ha", "exact hd_witness", "exact hz",
             f"have hab : exists A B. (a = x * A /\\ (b = x * B /\\ ({coprime('A', 'B', tag='gfull_nonzero_AB')})))",
             *_call("crt_gcd_coprime_cofactors", "a", "b", "x"), "exact hdnonzero", "exact hd_witness",
             "cases hab", "cases hab_witness", "cases hab_witness_witness", "cases hab_witness_witness_right",
             "have he : exists e. " + _gcd("e", "x", "n", tag="nonzero_e"),
             *_call("canonical_gcd_exists", "x", "n"), "cases he",
             "have henonzero : ~(x3 = 0)", "intro hz",
             *_call("crt_gcd_nonzero_right", "x", "n", "x3"), "exact hn", "exact he_witness", "exact hz",
             f"have hdn : exists D N. (x = x3 * D /\\ (n = x3 * N /\\ ({coprime('D', 'N', tag='gfull_nonzero_DN')})))",
             *_call("crt_gcd_coprime_cofactors", "x", "n", "x3"), "exact henonzero", "exact he_witness",
             "cases hdn", "cases hdn_witness", "cases hdn_witness_witness", "cases hdn_witness_witness_right",
             "have hN : ~(x5 = 0)", "intro hz",
             *_call("factor_nonzero_right", "n", "x3", "x5"), "exact hn", "exact hdn_witness_witness_right_left", "exact hz",
             "have hLeq : L = x * (x1 * x2)",
             *_call("crt_lcm_gcd_cofactor_product", "a", "b", "x", "x1", "x2", "L"),
             "exact hdnonzero", "exact hab_witness_witness_left", "exact hab_witness_witness_right_left",
             "exact hd_witness", "exact hL",
             *_call("crt_gcd_lcm_distributes_scaled_coprime", "x", "n", "x3", "x4", "x5", "x1", "x2", "L", "ga", "gb", "g"),
             "exact hdn_witness_witness_left", "exact hdn_witness_witness_right_left",
             "exact henonzero", "exact hN", "exact hdn_witness_witness_right_right",
             "exact hab_witness_witness_right_right", "exact hLeq",
             *_rewrite("<- hab_witness_witness_left", 2), "exact hga",
             *_rewrite("<- hab_witness_witness_right_left", 2), "exact hgb", "exact hg"),
            "GCD distributes over the actual binary LCM for a nonzero left input and nonzero comparison input; the right input may be zero.",
        ),
        spec(
            "crt_gcd_lcm_distributes_zero_left",
            "forall a b n L ga gb g. a = 0 -> "
            f"({_lcm('L', 'a', 'b', tag='zero_left_L')}) -> "
            f"({_gcd('ga', 'a', 'n', tag='zero_left_ga')}) -> "
            f"({_gcd('gb', 'b', 'n', tag='zero_left_gb')}) -> "
            f"({_gcd('g', 'L', 'n', tag='zero_left_g')}) -> "
            f"({_lcm('g', 'ga', 'gb', tag='zero_left_result')})",
            ("is_lcm_symm", "crt_gcd_lcm_distributes_divisibility"),
            (*_intros("a", "b", "n", "L", "ga", "gb", "g", "ha", "hL", "hga", "hgb", "hg"),
             "have hswap : " + _lcm("L", "b", "a", tag="zero_left_swapped"),
             *_call("is_lcm_symm", "L", "a", "b"), "exact hL",
             *_call("is_lcm_symm", "g", "gb", "ga"),
             *_call("crt_gcd_lcm_distributes_divisibility", "b", "a", "n", "L", "gb", "ga", "g"),
             "exists 0", "rewrite ha", "symm", "apply PA5",
             "exact hswap",
             "exact hgb", "exact hga", "exact hg"),
            "The zero-left-modulus boundary of gcd--LCM distributivity follows from exact divisibility, not a positivity assumption.",
        ),
        spec(
            "crt_gcd_lcm_distributes_zero_comparison",
            "forall a b n L ga gb g. n = 0 -> "
            f"({_lcm('L', 'a', 'b', tag='zero_n_L')}) -> "
            f"({_gcd('ga', 'a', 'n', tag='zero_n_ga')}) -> "
            f"({_gcd('gb', 'b', 'n', tag='zero_n_gb')}) -> "
            f"({_gcd('g', 'L', 'n', tag='zero_n_g')}) -> "
            f"({_lcm('g', 'ga', 'gb', tag='zero_n_result')})",
            ("crt_gcd_zero_right_value",),
            (*_intros("a", "b", "n", "L", "ga", "gb", "g", "hn", "hL", "hga", "hgb", "hg"),
             "have heqa : ga = a", *_call("crt_gcd_zero_right_value", "a", "ga"), *_rewrite("<- hn", 2), "exact hga",
             "have heqb : gb = b", *_call("crt_gcd_zero_right_value", "b", "gb"), *_rewrite("<- hn", 2), "exact hgb",
             "have heqg : g = L", *_call("crt_gcd_zero_right_value", "L", "g"), *_rewrite("<- hn", 2), "exact hg",
             *_rewrite("heqa", 2), *_rewrite("heqb", 2), *_rewrite("heqg", 3), "exact hL"),
            "Comparison with zero turns all three gcds into their other inputs and preserves the exact original LCM.",
        ),
        spec(
            "crt_gcd_lcm_distributes",
            "forall a b n L ga gb g. "
            f"({_lcm('L', 'a', 'b', tag='full_L')}) -> "
            f"({_gcd('ga', 'a', 'n', tag='full_ga')}) -> "
            f"({_gcd('gb', 'b', 'n', tag='full_gb')}) -> "
            f"({_gcd('g', 'L', 'n', tag='full_g')}) -> "
            f"({_lcm('g', 'ga', 'gb', tag='full_result')})",
            ("eq_decidable", "crt_gcd_lcm_distributes_zero_left",
             "crt_gcd_lcm_distributes_zero_comparison", "crt_gcd_lcm_distributes_nonzero"),
            (*_intros("a", "b", "n", "L", "ga", "gb", "g", "hL", "hga", "hgb", "hg"),
             "have ha : a = 0 \\/ ~(a = 0)", *_call("eq_decidable", "a", "0"), "cases ha",
             *_call("crt_gcd_lcm_distributes_zero_left", "a", "b", "n", "L", "ga", "gb", "g"),
             "exact ha_left", "exact hL", "exact hga", "exact hgb", "exact hg",
             "have hn : n = 0 \\/ ~(n = 0)", *_call("eq_decidable", "n", "0"), "cases hn",
             *_call("crt_gcd_lcm_distributes_zero_comparison", "a", "b", "n", "L", "ga", "gb", "g"),
             "exact hn_left", "exact hL", "exact hga", "exact hgb", "exact hg",
             *_call("crt_gcd_lcm_distributes_nonzero", "a", "b", "n", "L", "ga", "gb", "g"),
             "exact ha_right", "exact hn_right", "exact hL", "exact hga", "exact hgb", "exact hg"),
            "Unconditional constructive gcd(lcm(a,b),n)=lcm(gcd(a,n),gcd(b,n)), including every zero boundary.",
        ),
        spec(
            "crt_prefix_gcd_congruences_drop_last",
            "forall b c l n u v. "
            f"({_prefix_gcd_terms('b', 'c', 'S l', 'n', 'u', 'v', tag='drop_source')}) -> "
            f"({_prefix_gcd_terms('b', 'c', 'l', 'n', 'u', 'v', tag='drop_result')})",
            ("le_succ",),
            (*_intros("b", "c", "l", "n", "u", "v", "hp", "i", "m", "d", "hi", "hm", "hd"),
             *_call("hp", "i", "m", "d"),
             *_call("le_succ", "(S i)", "l"), "exact hi", "exact hm", "exact hd"),
            "Pointwise congruence modulo decoded gcds restricts to the preceding finite prefix.",
        ),
        spec(
            "crt_prefix_gcd_congruences_lcm",
            "forall b c l n u v L g. "
            f"({_expand(_lcm_terms, 'b', 'c', 'l', 'L', tag='prefix_lcm')}) -> "
            f"({_prefix_gcd_terms('b', 'c', 'l', 'n', 'u', 'v', tag='prefix_pointwise')}) -> "
            f"({_gcd('g', 'L', 'n', tag='prefix_final_gcd')}) -> "
            f"({_mod('g', 'u', 'v', tag='prefix_final_mod')})",
            ("crt_prefix_lcm_unique", "crt_prefix_lcm_empty", "canonical_gcd_one_left_iff",
             "crt_mod_one_universal", "crt_prefix_lcm_exists_unique", "beta_at_exists",
             "lcm_exists_relational", "crt_prefix_lcm_successor_intro", "canonical_gcd_exists",
             "crt_prefix_gcd_congruences_drop_last", "crt_gcd_lcm_distributes",
             "mod_eq_lcm_merge", "le_refl"),
            (*_intros("b", "c"), "induction l",
             *_intros("n", "u", "v", "L", "g", "hL", "hp", "hg"),
             "have hLone : L = 1",
             *_call("crt_prefix_lcm_unique", "b", "c", "0", "L", "1"), "exact hL",
             *_call("crt_prefix_lcm_empty", "b", "c"),
             "have hgone : g = 1", "specialize canonical_gcd_one_left_iff n",
             "specialize canonical_gcd_one_left_iff g", "cases canonical_gcd_one_left_iff",
             "apply canonical_gcd_one_left_iff_left", *_rewrite("<- hLone", 2), "exact hg",
             *_rewrite("hgone", 2), *_call("crt_mod_one_universal", "u", "v"),
             *_intros("n", "u", "v", "L", "g", "hL", "hp", "hg"),
             "specialize crt_prefix_lcm_exists_unique b", "specialize crt_prefix_lcm_exists_unique c",
             "specialize crt_prefix_lcm_exists_unique l", "cases crt_prefix_lcm_exists_unique",
             "cases crt_prefix_lcm_exists_unique_witness",
             "have hm : exists m. " + _expand(_at, "b", "c", "l", "m", tag="prefix_actual_last"),
             *_call("beta_at_exists", "b", "c", "l"), "cases hm",
             "have hK : exists K. " + _lcm("K", "x", "x1", tag="prefix_binary_lcm"),
             *_call("lcm_exists_relational", "x", "x1"), "cases hK",
             "have hLeq : L = x2",
             *_call("crt_prefix_lcm_unique", "b", "c", "(S l)", "L", "x2"), "exact hL",
             *_call("crt_prefix_lcm_successor_intro", "b", "c", "l", "x", "x1", "x2"),
             "exact crt_prefix_lcm_exists_unique_witness_left", "exact hm_witness", "exact hK_witness",
             "have hd : exists d. " + _gcd("d", "x", "n", tag="prefix_old_gcd"),
             *_call("canonical_gcd_exists", "x", "n"), "cases hd",
             "have he : exists e. " + _gcd("e", "x1", "n", tag="prefix_new_gcd"),
             *_call("canonical_gcd_exists", "x1", "n"), "cases he",
             "have hmod : " + _mod("x3", "u", "v", tag="prefix_old_mod"),
             *_call("IH", "n", "u", "v", "x", "x3"),
             "exact crt_prefix_lcm_exists_unique_witness_left",
             *_call("crt_prefix_gcd_congruences_drop_last", "b", "c", "l", "n", "u", "v"),
             "exact hp", "exact hd_witness",
             "have hlat : " + _lcm("g", "x3", "x4", tag="prefix_lattice_result"),
             *_call("crt_gcd_lcm_distributes", "x", "x1", "n", "x2", "x3", "x4", "g"),
             "exact hK_witness", "exact hd_witness", "exact he_witness",
             *_rewrite("<- hLeq", 2), "exact hg",
             *_call("mod_eq_lcm_merge", "g", "x3", "x4", "u", "v"), "exact hlat", "exact hmod",
             *_call("hp", "l", "x1", "x4"), *_call("le_refl", "(S l)"),
             "exact hm_witness", "exact he_witness"),
            "Induction over every finite decoded modulus list lifts pointwise gcd congruences to congruence modulo the gcd of its exact list LCM; zero moduli and the empty list are included.",
        ),
        spec(
            "crt_pairwise_compatible_prefix_induces_gcd_congruences",
            "forall r s b c l i x a n. "
            f"({_expand(_pairwise_terms, 'r', 's', 'b', 'c', 'l', tag='bridge_pairs')}) -> "
            f"({_expand(_bound, 'i', 'l', tag='bridge_index')}) -> "
            f"({_expand(_solution_terms, 'r', 's', 'b', 'c', 'i', 'x', tag='bridge_solution')}) -> "
            f"({_expand(_at, 'r', 's', 'i', 'a', tag='bridge_residue')}) -> "
            f"({_expand(_at, 'b', 'c', 'i', 'n', tag='bridge_modulus')}) -> "
            f"({_prefix_gcd_terms('b', 'c', 'i', 'n', 'x', 'a', tag='bridge_result')})",
            ("beta_at_exists", "lt_trans", "mod_eq_trans", "mod_eq_of_mod_eq_multiple", "is_gcd_dvd_left"),
            (*_intros("r", "s", "b", "c", "l", "i", "x", "a", "n", "hp", "hi", "hs", "ha", "hn",
                      "j", "m", "d", "hj", "hm", "hd"),
             "have hz : exists z. " + _expand(_at, "r", "s", "j", "z", tag="bridge_previous_residue"),
             *_call("beta_at_exists", "r", "s", "j"), "cases hz",
             *_call("mod_eq_trans", "d", "x", "x1", "a"),
             *_call("mod_eq_of_mod_eq_multiple", "d", "m", "x", "x1"),
             *_call("is_gcd_dvd_left", "d", "m", "n"), "exact hd",
             *_call("hs", "j", "x1", "m"), "exact hj", "exact hz_witness", "exact hm",
             *_call("hp", "j", "i", "x1", "a", "m", "n", "d"),
             *_call("lt_trans", "j", "i", "l"), "exact hj", "exact hi",
             "exact hi", "exact hz_witness", "exact ha", "exact hm", "exact hn", "exact hd"),
            "Pairwise compatibility and an actual prefix solution imply every gcd congruence needed for the next merge, without any dominating-last or coprimality assumption.",
        ),
        spec(
            "crt_pairwise_compatible_prefix_implies_merge_compatible",
            "forall r s b c l. "
            f"({_expand(_pairwise_terms, 'r', 's', 'b', 'c', 'l', tag='full_pairs_source')}) -> "
            f"({_expand(_merge_terms, 'r', 's', 'b', 'c', 'l', tag='full_merge_result')})",
            ("crt_prefix_gcd_congruences_lcm", "crt_pairwise_compatible_prefix_induces_gcd_congruences"),
            (*_intros("r", "s", "b", "c", "l", "hp", "i", "x", "M", "a", "n", "g",
                      "hi", "hM", "hs", "ha", "hn", "hg"),
             *_call("crt_prefix_gcd_congruences_lcm", "b", "c", "i", "n", "x", "a", "M", "g"), "exact hM",
             *_call("crt_pairwise_compatible_prefix_induces_gcd_congruences", "r", "s", "b", "c", "l", "i", "x", "a", "n"),
             "exact hp", "exact hi", "exact hs", "exact ha", "exact hn", "exact hg"),
            "Every pairwise gcd-compatible finite list satisfies every actual predecessor-LCM merge condition, including arbitrary noncoprime and zero moduli.",
        ),
        spec(
            "crt_pairwise_compatible_prefix_solution_exists",
            "forall r s b c l. "
            f"({_expand(_pairwise_terms, 'r', 's', 'b', 'c', 'l', tag='full_existence_pairs')}) -> exists x. "
            f"({_expand(_solution_terms, 'r', 's', 'b', 'c', 'l', 'x', tag='full_existence_solution')})",
            ("crt_pairwise_compatible_prefix_implies_merge_compatible", "crt_merge_compatible_prefix_solution_exists"),
            (*_intros("r", "s", "b", "c", "l", "hp"),
             *_call("crt_merge_compatible_prefix_solution_exists", "r", "s", "b", "c", "l"),
             *_call("crt_pairwise_compatible_prefix_implies_merge_compatible", "r", "s", "b", "c", "l"), "exact hp"),
            "Unrestricted finite-list generalized CRT: every pairwise-compatible decoded residue/modulus list has a genuine simultaneous natural solution, including zero and repeated moduli and empty lists.",
        ),
        spec(
            "crt_pairwise_compatible_prefix_canonical_exists_unique",
            "forall r s b c l. "
            f"({_expand(_positive_terms, 'b', 'c', 'l', tag='full_canonical_positive')}) -> "
            f"({_expand(_pairwise_terms, 'r', 's', 'b', 'c', 'l', tag='full_canonical_pairs')}) -> exists x M. "
            f"(({_expand(_canonical_terms, 'r', 's', 'b', 'c', 'l', 'x', 'M', tag='full_canonical_chosen')}) /\\ "
            f"forall y. ({_expand(_canonical_terms, 'r', 's', 'b', 'c', 'l', 'y', 'M', tag='full_canonical_compared')}) -> y = x)",
            ("crt_pairwise_compatible_prefix_implies_merge_compatible", "crt_merge_compatible_prefix_canonical_exists_unique"),
            (*_intros("r", "s", "b", "c", "l", "hpositive", "hp"),
             *_call("crt_merge_compatible_prefix_canonical_exists_unique", "r", "s", "b", "c", "l"), "exact hpositive",
             *_call("crt_pairwise_compatible_prefix_implies_merge_compatible", "r", "s", "b", "c", "l"), "exact hp"),
            "Full constructive canonical generalized CRT for arbitrary finite pairwise-compatible positive moduli: an exact list LCM and a unique strictly bounded simultaneous solution, with no supplied merge invariant or dominating modulus.",
        ),
        spec(
            "crt_canonical_prefix_solution_implies_normalized",
            "forall r s b c l x M. "
            f"({_expand(_canonical_terms, 'r', 's', 'b', 'c', 'l', 'x', 'M', tag='canonical_to_normal_source')}) -> "
            f"({_normalized_terms('r', 's', 'b', 'c', 'l', 'x', 'M', tag='canonical_to_normal_result')})",
            (),
            (*_intros("r", "s", "b", "c", "l", "x", "M", "hc"),
             "cases hc", "cases hc_right", "split", "exact hc_left", "split",
             "right", "exact hc_right_left", "exact hc_right_right"),
            "Every historical strictly bounded canonical solution is also a zero-safe normalized solution, without changing either definition.",
        ),
        spec(
            "crt_normalized_prefix_solution_unique",
            "forall r s b c l M x y. "
            f"({_normalized_terms('r', 's', 'b', 'c', 'l', 'x', 'M', tag='normalized_unique_left')}) -> "
            f"({_normalized_terms('r', 's', 'b', 'c', 'l', 'y', 'M', tag='normalized_unique_right')}) -> y = x",
            ("crt_prefix_zero_lcm_solution_unique", "crt_canonical_prefix_solution_unique"),
            (*_intros("r", "s", "b", "c", "l", "M", "x", "y", "hx", "hy"),
             "cases hx", "cases hx_right", "cases hy", "cases hy_right", "cases hx_right_left",
             *_call("crt_prefix_zero_lcm_solution_unique", "r", "s", "b", "c", "l", "M", "x", "y"),
             "exact hx_left", "exact hx_right_left_left", "exact hx_right_right", "exact hy_right_right",
             "cases hy_right_left",
             *_call("crt_prefix_zero_lcm_solution_unique", "r", "s", "b", "c", "l", "M", "x", "y"),
             "exact hx_left", "exact hy_right_left_left", "exact hx_right_right", "exact hy_right_right",
             *_call("crt_canonical_prefix_solution_unique", "r", "s", "b", "c", "l", "M", "x", "y"),
             "split", "exact hx_left", "split", "exact hx_right_left_right", "exact hx_right_right",
             "split", "exact hy_left", "split", "exact hy_right_left_right", "exact hy_right_right"),
            "Normalized representatives are literally unique at every list LCM; the zero case uses congruence equality, not a false bound below zero.",
        ),
        spec(
            "crt_prefix_solution_normalized_exists",
            "forall r s b c l M x. "
            f"({_expand(_lcm_terms, 'b', 'c', 'l', 'M', tag='normalize_lcm')}) -> "
            f"({_expand(_solution_terms, 'r', 's', 'b', 'c', 'l', 'x', tag='normalize_solution')}) -> exists z. "
            f"({_normalized_terms('r', 's', 'b', 'c', 'l', 'z', 'M', tag='normalize_result')})",
            ("eq_decidable", "crt_prefix_solution_canonical_remainder", "crt_canonical_prefix_solution_implies_normalized"),
            (*_intros("r", "s", "b", "c", "l", "M", "x", "hM", "hs"),
             "have hz : M = 0 \\/ ~(M = 0)", *_call("eq_decidable", "M", "0"), "cases hz",
             "exists x", "split", "exact hM", "split", "left", "exact hz_left", "exact hs",
             "have hc : exists y. " + _expand(_canonical_terms, "r", "s", "b", "c", "l", "y", "M", tag="normalize_canonical"),
             *_call("crt_prefix_solution_canonical_remainder", "r", "s", "b", "c", "l", "M", "x"),
             "exact hz_right", "exact hM", "exact hs", "cases hc", "exists x1",
             *_call("crt_canonical_prefix_solution_implies_normalized", "r", "s", "b", "c", "l", "x1", "M"), "exact hc_witness"),
            "Every simultaneous solution has a normalized representative for its exact list LCM, with zero retained rather than divided by.",
        ),
        spec(
            "crt_pairwise_compatible_prefix_normalized_exists_unique",
            "forall r s b c l. "
            f"({_expand(_pairwise_terms, 'r', 's', 'b', 'c', 'l', tag='normalized_exists_pairs')}) -> exists x M. "
            f"(({_normalized_terms('r', 's', 'b', 'c', 'l', 'x', 'M', tag='normalized_exists_chosen')}) /\\ "
            f"forall y. ({_normalized_terms('r', 's', 'b', 'c', 'l', 'y', 'M', tag='normalized_exists_compared')}) -> y = x)",
            ("crt_pairwise_compatible_prefix_solution_exists", "crt_prefix_lcm_exists_unique",
             "crt_prefix_solution_normalized_exists", "crt_normalized_prefix_solution_unique"),
            (*_intros("r", "s", "b", "c", "l", "hp"),
             "have hs : exists x. " + _expand(_solution_terms, "r", "s", "b", "c", "l", "x", tag="normalized_exists_actual"),
             *_call("crt_pairwise_compatible_prefix_solution_exists", "r", "s", "b", "c", "l"), "exact hp", "cases hs",
             "specialize crt_prefix_lcm_exists_unique b", "specialize crt_prefix_lcm_exists_unique c",
             "specialize crt_prefix_lcm_exists_unique l", "cases crt_prefix_lcm_exists_unique",
             "cases crt_prefix_lcm_exists_unique_witness",
             "have hn : exists z. " + _normalized_terms("r", "s", "b", "c", "l", "z", "x1", tag="normalized_exists_value"),
             *_call("crt_prefix_solution_normalized_exists", "r", "s", "b", "c", "l", "x1", "x"),
             "exact crt_prefix_lcm_exists_unique_witness_left", "exact hs_witness", "cases hn",
             "exists x2", "exists x1", "split", "exact hn_witness", "intro y", "intro hy",
             *_call("crt_normalized_prefix_solution_unique", "r", "s", "b", "c", "l", "x1", "x2", "y"),
             "exact hn_witness", "exact hy"),
            "Full zero-inclusive generalized CRT: every arbitrary pairwise-compatible finite list has its exact LCM and a unique normalized simultaneous solution; neither positivity nor an operational merge invariant is assumed.",
        ),
        spec(
            "crt_pairwise_compatible_prefix_solvable_iff",
            "forall r s b c l. "
            f"((({_expand(_pairwise_terms, 'r', 's', 'b', 'c', 'l', tag='solvable_pairs_forward')}) -> exists x. "
            f"({_expand(_solution_terms, 'r', 's', 'b', 'c', 'l', 'x', tag='solvable_solution_forward')})) /\\ "
            f"((exists x. ({_expand(_solution_terms, 'r', 's', 'b', 'c', 'l', 'x', tag='solvable_solution_backward')})) -> "
            f"({_expand(_pairwise_terms, 'r', 's', 'b', 'c', 'l', tag='solvable_pairs_backward')})))",
            ("crt_pairwise_compatible_prefix_solution_exists", "crt_prefix_solution_implies_pairwise_compatible"),
            (*_intros("r", "s", "b", "c", "l"), "split", "intro hp",
             *_call("crt_pairwise_compatible_prefix_solution_exists", "r", "s", "b", "c", "l"), "exact hp",
             "intro hs", "cases hs", *_call("crt_prefix_solution_implies_pairwise_compatible", "r", "s", "b", "c", "l", "x"), "exact hs_witness"),
            "Exact pairwise gcd compatibility is necessary and sufficient for solvability of every finite natural congruence list, including zero moduli.",
        ),
        spec(
            "crt_pairwise_compatible_prefix_merge_iff",
            "forall r s b c l. "
            f"((({_expand(_pairwise_terms, 'r', 's', 'b', 'c', 'l', tag='merge_iff_pairs_forward')}) -> "
            f"({_expand(_merge_terms, 'r', 's', 'b', 'c', 'l', tag='merge_iff_merge_forward')})) /\\ "
            f"(({_expand(_merge_terms, 'r', 's', 'b', 'c', 'l', tag='merge_iff_merge_backward')}) -> "
            f"({_expand(_pairwise_terms, 'r', 's', 'b', 'c', 'l', tag='merge_iff_pairs_backward')})))",
            ("crt_pairwise_compatible_prefix_implies_merge_compatible", "crt_merge_compatible_prefix_implies_pairwise_compatible"),
            (*_intros("r", "s", "b", "c", "l"), "split", "intro hp",
             *_call("crt_pairwise_compatible_prefix_implies_merge_compatible", "r", "s", "b", "c", "l"), "exact hp",
             "intro hm", *_call("crt_merge_compatible_prefix_implies_pairwise_compatible", "r", "s", "b", "c", "l"), "exact hm"),
            "Pairwise compatibility and the formerly stronger predecessor-LCM merge invariant are constructively equivalent for arbitrary finite natural lists.",
        ),
        spec(
            "crt_normalized_prefix_solution_class_iff_lcm",
            "forall r s b c l M x y. "
            f"({_normalized_terms('r', 's', 'b', 'c', 'l', 'x', 'M', tag='normalized_class_source')}) -> "
            f"((({_expand(_solution_terms, 'r', 's', 'b', 'c', 'l', 'y', tag='normalized_class_solution_forward')}) -> "
            f"({_mod('M', 'y', 'x', tag='normalized_class_mod_forward')})) /\\ "
            f"(({_mod('M', 'y', 'x', tag='normalized_class_mod_backward')}) -> "
            f"({_expand(_solution_terms, 'r', 's', 'b', 'c', 'l', 'y', tag='normalized_class_solution_backward')})))",
            ("crt_prefix_solution_class_iff_lcm",),
            (*_intros("r", "s", "b", "c", "l", "M", "x", "y", "hx"),
             "cases hx", "cases hx_right",
             *_call("crt_prefix_solution_class_iff_lcm", "r", "s", "b", "c", "l", "M", "x", "y"),
             "exact hx_left", "exact hx_right_right"),
            "All simultaneous solutions form exactly the congruence class of the normalized solution modulo the exact list LCM, also when that LCM is zero.",
        ),
        spec(
            "crt_normalized_zero_lcm_all_solutions_unique",
            "forall r s b c l M x y. "
            f"({_normalized_terms('r', 's', 'b', 'c', 'l', 'x', 'M', tag='normalized_zero_source')}) -> M = 0 -> "
            f"({_expand(_solution_terms, 'r', 's', 'b', 'c', 'l', 'y', tag='normalized_zero_compared')}) -> y = x",
            ("crt_prefix_zero_lcm_solution_unique",),
            (*_intros("r", "s", "b", "c", "l", "M", "x", "y", "hx", "hzero", "hy"),
             "cases hx", "cases hx_right",
             *_call("crt_prefix_zero_lcm_solution_unique", "r", "s", "b", "c", "l", "M", "x", "y"),
             "exact hx_left", "exact hzero", "exact hx_right_right", "exact hy"),
            "At zero list LCM every actual simultaneous solution equals the normalized one; no bound or normalization premise is imposed on the comparison solution.",
        ),
        spec(
            "crt_positive_normalized_prefix_iff_canonical",
            "forall r s b c l x M. "
            f"({_expand(_positive_terms, 'b', 'c', 'l', tag='normalized_positive_hypothesis')}) -> "
            f"((({_normalized_terms('r', 's', 'b', 'c', 'l', 'x', 'M', tag='normalized_positive_forward')}) -> "
            f"({_expand(_canonical_terms, 'r', 's', 'b', 'c', 'l', 'x', 'M', tag='canonical_positive_forward')})) /\\ "
            f"(({_expand(_canonical_terms, 'r', 's', 'b', 'c', 'l', 'x', 'M', tag='canonical_positive_backward')}) -> "
            f"({_normalized_terms('r', 's', 'b', 'c', 'l', 'x', 'M', tag='normalized_positive_backward')})))",
            ("crt_positive_prefix_lcm_nonzero", "crt_canonical_prefix_solution_implies_normalized"),
            (*_intros("r", "s", "b", "c", "l", "x", "M", "hp"), "split", "intro hn",
             "cases hn", "cases hn_right", "split", "exact hn_left", "split", "cases hn_right_left",
             "exfalso", *_call("crt_positive_prefix_lcm_nonzero", "b", "c", "l", "M"),
             "exact hp", "exact hn_left", "exact hn_right_left_left",
             "exact hn_right_left_right", "exact hn_right_right",
             "intro hc", *_call("crt_canonical_prefix_solution_implies_normalized", "r", "s", "b", "c", "l", "x", "M"), "exact hc"),
            "For positive modulus lists, zero-safe normalization is exactly the historical strict canonical definition, not a weaker replacement.",
        ),
    )


__all__ = [
    "crt_prefix_gcd_congruences", "crt_normalized_prefix_solution",
    "make_generalized_crt_full_candidate_theorems",
]
