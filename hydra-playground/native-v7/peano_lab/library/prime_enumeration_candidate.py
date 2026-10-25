"""Construct the actual first primes and witnessed effective nth-prime bounds.

The least-prime search and beta-coded list below are ordinary first-order HA
relations.  A sparse Bertrand chain is not an enumeration of the first primes:
each transition here proves global minimality among primes above its input.
Candidate bodies grant no Alpha admission or proof authority by themselves.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .binary_length_candidate import _power_two_terms
from .finite_fold_surface import _identifier
from .finite_sum_theorems import _at
from .prime_count_chebyshev_candidate import _call, _intro, _le, _lt, _prime


def _fresh(tag: str, terms: tuple[str, ...], *roles: str) -> tuple[str, ...]:
    _identifier(tag, "prime-enumeration definition tag")
    names = tuple(f"pen_{role}_{tag}" for role in roles)
    variables = set(re.findall(r"[A-Za-z_][A-Za-z_0-9']*", " ".join(terms)))
    if set(names) & variables:
        raise ValueError("prime-enumeration definition binder captures an argument")
    return names


def _next(a: str, p: str, *, tag: str) -> str:
    (q,) = _fresh(tag, (a, p), "comparison")
    return (
        f"({_prime(p, tag=f'pen_{tag}_prime')}) /\\ "
        f"(({_lt(a, p, tag=f'pen_{tag}_greater')}) /\\ "
        f"forall {q}. ({_prime(q, tag=f'pen_{tag}_comparison')}) -> "
        f"({_lt(a, q, tag=f'pen_{tag}_above')}) -> "
        f"({_le(p, q, tag=f'pen_{tag}_minimal')}))"
    )


def next_prime_relation(a: str, p: str, *, tag: str) -> str:
    """The genuinely least prime strictly above a, not an arbitrary next prime."""
    for value in (a, p):
        _identifier(value, "next-prime argument")
        if value.startswith("pen_"):
            raise ValueError("prime-enumeration definition binder captures an argument")
    return _next(a, p, tag=tag)


def _chain(b: str, c: str, k: str, *, tag: str) -> str:
    i, a, p = _fresh(tag, (b, c, k), "index", "previous", "following")
    return (
        f"({_at(b, c, '0', '2', tag=f'pen_{tag}_initial')}) /\\ "
        f"forall {i}. ({_lt(i, k, tag=f'pen_{tag}_bound')}) -> "
        f"exists {a} {p}. ({_at(b, c, i, a, tag=f'pen_{tag}_previous')}) /\\ "
        f"(({_at(b, c, f'S {i}', p, tag=f'pen_{tag}_following')}) /\\ "
        f"({_next(a, p, tag=f'{tag}_next')}))"
    )


def initial_prime_chain_relation(b: str, c: str, k: str, *, tag: str) -> str:
    """A list starting at two with exactly k least-prime transitions."""
    for value in (b, c, k):
        _identifier(value, "initial-prime-chain argument")
        if value.startswith("pen_"):
            raise ValueError("prime-enumeration definition binder captures an argument")
    return _chain(b, c, k, tag=tag)


def _list(b: str, c: str, k: str, *, tag: str) -> str:
    (j,) = _fresh(tag, (b, c, k), "last_index")
    return f"({k} = 0 \\/ exists {j}. {k} = S {j} /\\ ({_chain(b,c,j,tag=f'{tag}_chain')}))"


def prime_list_relation(b: str, c: str, k: str, *, tag: str) -> str:
    """Exactly the first k primes at beta indices 0 through k-1; k=0 is empty."""
    for value in (b, c, k):
        _identifier(value, "prime-list argument")
        if value.startswith("pen_"):
            raise ValueError("prime-enumeration definition binder captures an argument")
    return _list(b, c, k, tag=tag)


def _scan(a: str, n: str, *, tag: str) -> str:
    p, q = _fresh(tag, (a, n), "least", "unseen")
    return (
        f"(exists {p}. {_next(a,p,tag=f'{tag}_found')}) \\/ "
        f"(forall {q}. ({_prime(q,tag=f'pen_{tag}_prime')}) -> "
        f"({_lt(a,q,tag=f'pen_{tag}_above')}) -> "
        f"({_lt(f'{a} + {n}',q,tag=f'pen_{tag}_unseen')}))"
    )


def _next_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "least_prime_above_finite_scan",
            f"forall a n. {_scan('a','n',tag='scan')}",
            ("prime_decidable", "add_comm", "le_eq_or_lt"),
            (*_intro("a"), "induction n", "right", *_intro("q", "hp", "ha"),
             "have hz : a + 0 = a", "apply PA3", "rewrite hz", "exact ha", "cases IH", "left", "exact IH_left",
             f"have hdec : ({_prime('S (a + n)',tag='pen_scan_candidate')}) \\/ ~({_prime('S (a + n)',tag='pen_scan_candidate_not')})",
             *_call("prime_decidable", "(S (a + n))"), "cases hdec", "left", "exists S (a + n)",
             "split", "exact hdec_left", "split", "exists n", "rewrite PA4", "congr", "apply add_comm",
             *_intro("q", "hp", "ha"), "specialize IH_right q", "apply IH_right", "exact hp", "exact ha",
             "right", *_intro("q", "hp", "ha"),
             f"have hprev : {_le('S (a + n)','q',tag='pen_scan_previous')}",
             "specialize IH_right q", "apply IH_right", "exact hp", "exact ha",
             f"have hcase : S (a + n) = q \\/ ({_lt('S (a + n)','q',tag='pen_scan_later')})",
             *_call("le_eq_or_lt", "(S (a + n))", "q"), "exact hprev", "cases hcase",
             "exfalso", "apply hdec_right", "rewrite hcase_left", "rewrite hcase_left", "exact hp",
             "have hsucc : a + S n = S (a + n)", "apply PA4", "rewrite hsucc", "exact hcase_right"),
            "Finite decidable scanning either finds the actual least prime above a or proves every such prime exceeds the scanned interval.",
        ),
        spec(
            "least_prime_above_exists",
            f"forall a. exists p. {_next('a','p',tag='next_exists')}",
            ("prime_unbounded", "least_prime_above_finite_scan", "lt_not_le", "le_add_left"),
            (*_intro("a"),
             f"have hu : exists p. ({_lt('a','p',tag='pen_unbounded')}) /\\ ({_prime('p',tag='pen_unbounded_prime')})",
             *_call("prime_unbounded", "a"), "cases hu", "cases hu_witness",
             f"have hs : {_scan('a','x',tag='exists_scan')}", *_call("least_prime_above_finite_scan", "a", "x"),
             "cases hs", "exact hs_left", "exfalso",
             f"have hlt : {_lt('a + x','x',tag='pen_exists_contradiction')}",
             "specialize hs_right x", "apply hs_right", "exact hu_witness_right", "exact hu_witness_left",
             *_call("lt_not_le", "(a + x)", "x"), "exact hlt", *_call("le_add_left", "x", "a")),
            "Euclid unboundedness terminates the finite least-prime scan without any unbounded-search axiom.",
        ),
        spec(
            "least_prime_above_unique",
            f"forall a p q. ({_next('a','p',tag='unique_left')}) -> ({_next('a','q',tag='unique_right')}) -> p = q",
            ("le_antisymm",),
            (*_intro("a", "p", "q", "hp", "hq"), "cases hp", "cases hp_right", "cases hq", "cases hq_right",
             *_call("le_antisymm", "p", "q"),
             "specialize hp_right_right q", "apply hp_right_right", "exact hq_left", "exact hq_right_left",
             "specialize hq_right_right p", "apply hq_right_right", "exact hp_left", "exact hp_right_left"),
            "The least prime above any natural is uniquely determined by its minimality, not by its code.",
        ),
        spec(
            "least_prime_above_bertrand_bound",
            f"forall a p. ({_prime('a',tag='pen_bertrand_source')}) -> ({_next('a','p',tag='bertrand_next')}) -> ({_lt('p','a + a',tag='pen_bertrand_bound')})",
            ("prime_two_le", "bertrand_strict", "lt_of_le_of_lt"),
            (*_intro("a", "p", "ha", "hp"), "cases hp", "cases hp_right",
             f"have hw : exists q. ({_prime('q',tag='pen_bertrand_witness')}) /\\ (({_lt('a','q',tag='pen_bertrand_lower')}) /\\ ({_lt('q','a + a',tag='pen_bertrand_upper')}))",
             *_call("bertrand_strict", "a"), *_call("prime_two_le", "a"), "exact ha",
             "cases hw", "cases hw_witness", "cases hw_witness_right",
             *_call("lt_of_le_of_lt", "p", "x", "(a + a)"),
             "specialize hp_right_right x", "apply hp_right_right", "exact hw_witness_left", "exact hw_witness_right_left",
             "exact hw_witness_right_right"),
            "Bertrand's theorem bounds the actual consecutive prime, rather than only producing a sparse prime subsequence.",
        ),
        spec(
            "least_prime_above_exists_unique",
            f"forall a. exists p. ({_next('a','p',tag='unique_exists')}) /\\ "
            f"forall q. ({_next('a','q',tag='unique_exists_other')}) -> q = p",
            ("least_prime_above_exists", "least_prime_above_unique"),
            (*_intro("a"), "specialize least_prime_above_exists a", "cases least_prime_above_exists",
             "exists x", "split", "exact least_prime_above_exists_witness", *_intro("q", "hq"),
             *_call("least_prime_above_unique", "a", "q", "x"), "exact hq", "exact least_prime_above_exists_witness"),
            "Least-prime search is a total, uniquely valued constructive relation for every natural input.",
        ),
    )


def _transfer(b: str, c: str, d: str, e: str, l: str, *, tag: str) -> str:
    i, a = _fresh(tag, (b,c,d,e,l), "index", "value")
    return (
        f"forall {i} {a}. ({_lt(i,l,tag=f'pen_{tag}_bound')}) -> "
        f"({_at(b,c,i,a,tag=f'pen_{tag}_old')}) -> ({_at(d,e,i,a,tag=f'pen_{tag}_new')})"
    )


def _chain_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "initial_prime_chain_singleton_exists",
            f"exists b c. {_chain('b','c','0',tag='singleton')}",
            ("bertrand_chain_singleton_code_exists", "lt_not_le", "zero_le"),
            ("specialize bertrand_chain_singleton_code_exists 2", "cases bertrand_chain_singleton_code_exists",
             "cases bertrand_chain_singleton_code_exists_witness", "exists x", "exists x1", "split",
             "exact bertrand_chain_singleton_code_exists_witness_witness", *_intro("i", "hi"), "exfalso",
             *_call("lt_not_le", "i", "0"), "exact hi", *_call("zero_le", "i")),
            "The one-entry initial prime chain is an actual beta code of the prime two.",
        ),
        spec(
            "initial_prime_chain_prefix_extend",
            f"forall k b c a p. ({_chain('b','c','k',tag='extend_before')}) -> "
            f"({_at('b','c','k','a',tag='pen_extend_terminal')}) -> ({_next('a','p',tag='extend_next')}) -> "
            f"exists z d. ({_chain('z','d','S k',tag='extend_after')}) /\\ ({_at('z','d','S k','p',tag='pen_extend_new_terminal')})",
            ("beta_prefix_extend", "zero_le", "succ_le_succ", "le_refl", "finite_lt_succ_eq_or_lt"),
            (*_intro("k", "b", "c", "a", "p", "hc", "ha", "hp"), "cases hc",
             f"have he : exists z d. ({_at('z','d','S k','p',tag='pen_extend_entry')}) /\\ ({_transfer('b','c','z','d','S k',tag='extend_transfer')})",
             *_call("beta_prefix_extend", "(S k)", "b", "c", "p"),
             "cases he", "cases he_witness", "cases he_witness_witness", "exists x", "exists x1", "split", "split",
             "specialize he_witness_witness_right 0", "specialize he_witness_witness_right 2", "apply he_witness_witness_right",
             *_call("succ_le_succ", "0", "k"), *_call("zero_le", "k"), "exact hc_left",
             *_intro("i", "hi"), f"have hs : i = k \\/ ({_lt('i','k',tag='pen_extend_case')})",
             *_call("finite_lt_succ_eq_or_lt", "k", "i"), "exact hi", "cases hs",
             "exists a", "exists p", "split", "rewrite hs_left", "rewrite hs_left",
             "specialize he_witness_witness_right k", "specialize he_witness_witness_right a", "apply he_witness_witness_right",
             *_call("le_refl", "(S k)"), "exact ha", "split", "rewrite hs_left", "rewrite hs_left",
             "exact he_witness_witness_left", "exact hp",
             f"have hold : exists u v. ({_at('b','c','i','u',tag='pen_extend_old_left')}) /\\ "
             f"(({_at('b','c','S i','v',tag='pen_extend_old_right')}) /\\ ({_next('u','v',tag='extend_old_next')}))",
             "specialize hc_right i", "apply hc_right", "exact hs_right",
             "cases hold", "cases hold_witness", "cases hold_witness_witness", "cases hold_witness_witness_right",
             "exists x2", "exists x3", "split",
             "specialize he_witness_witness_right i", "specialize he_witness_witness_right x2", "apply he_witness_witness_right",
             "exact hi", "exact hold_witness_witness_left", "split",
             "specialize he_witness_witness_right (S i)", "specialize he_witness_witness_right x3", "apply he_witness_witness_right",
             *_call("succ_le_succ", "(S i)", "k"), "exact hs_right", "exact hold_witness_witness_right_left",
             "exact hold_witness_witness_right_right", "exact he_witness_witness_left"),
            "Appending the actual next prime preserves every old decoded entry and every minimal-successor edge.",
        ),
        spec(
            "initial_prime_chain_prefix_restrict",
            f"forall b c k i. ({_le('i','k',tag='pen_restrict_bound')}) -> "
            f"({_chain('b','c','k',tag='restrict_source')}) -> ({_chain('b','c','i',tag='restrict_result')})",
            ("lt_of_lt_of_le",),
            (*_intro("b", "c", "k", "i", "hi", "hc"), "cases hc", "split", "exact hc_left",
             *_intro("j", "hj"), "specialize hc_right j", "apply hc_right",
             *_call("lt_of_lt_of_le", "j", "i", "k"), "exact hj", "exact hi"),
            "Every initial segment retains the same genuine least-prime transitions.",
        ),
        spec(
            "initial_prime_chain_terminal_is_prime",
            f"forall b c k p. ({_chain('b','c','k',tag='terminal_source')}) -> "
            f"({_at('b','c','k','p',tag='pen_terminal_entry')}) -> ({_prime('p',tag='pen_terminal_prime')})",
            ("beta_at_unique", "prime_two", "le_refl"),
            (*_intro("b", "c"), "induction k", *_intro("p", "hc", "hp"), "cases hc",
             "have hp2 : p = 2", *_call("beta_at_unique", "b", "c", "0", "p", "2"), "exact hp", "exact hc_left",
             "rewrite hp2", "rewrite hp2", "exact prime_two",
             *_intro("p", "hc", "hp"), "cases hc",
             f"have he : exists a q. ({_at('b','c','k','a',tag='pen_terminal_previous')}) /\\ "
             f"(({_at('b','c','S k','q',tag='pen_terminal_last')}) /\\ ({_next('a','q',tag='terminal_next')}))",
             "specialize hc_right k", "apply hc_right", *_call("le_refl", "(S k)"),
             "cases he", "cases he_witness", "cases he_witness_witness", "cases he_witness_witness_right",
             "cases he_witness_witness_right_right", "have heq : p = x1",
             *_call("beta_at_unique", "b", "c", "(S k)", "p", "x1"), "exact hp", "exact he_witness_witness_right_left",
             "rewrite heq", "rewrite heq", "exact he_witness_witness_right_right_left"),
            "Every decoded terminal entry of an initial-prime chain is genuinely prime, including the first entry two.",
        ),
        spec(
            "initial_prime_chain_bounded_exists",
            f"forall k. exists b c p P. ({_chain('b','c','k',tag='bounded_chain')}) /\\ "
            f"(({_at('b','c','k','p',tag='pen_bounded_terminal')}) /\\ "
            f"(({_power_two_terms('S (S k)','P',tag='pen_bounded_power')}) /\\ ({_lt('p','P',tag='pen_bounded_bound')})))",
            ("initial_prime_chain_singleton_exists", "pow_two_two_exact", "least_prime_above_exists",
             "initial_prime_chain_prefix_extend", "binary_power_two_exists", "binary_power_two_successor_double",
             "initial_prime_chain_terminal_is_prime", "least_prime_above_bertrand_bound", "add_lt_add", "lt_trans"),
            ("induction k", "cases initial_prime_chain_singleton_exists", "cases initial_prime_chain_singleton_exists_witness",
             "exists x", "exists x1", "exists 2", "exists 4", "split",
             "exact initial_prime_chain_singleton_exists_witness_witness", "split", "cases initial_prime_chain_singleton_exists_witness_witness",
             "exact initial_prime_chain_singleton_exists_witness_witness_left", "split", "exact pow_two_two_exact", "exists 1", "norm_num",
             "cases IH", "cases IH_witness", "cases IH_witness_witness", "cases IH_witness_witness_witness",
             "cases IH_witness_witness_witness_witness", "cases IH_witness_witness_witness_witness_right",
             "cases IH_witness_witness_witness_witness_right_right",
             f"have hn : exists q. {_next('x2','q',tag='bounded_next')}", *_call("least_prime_above_exists", "x2"), "cases hn",
             f"have hP : exists Q. {_power_two_terms('S (S (S k))','Q',tag='pen_bounded_next_power')}",
             *_call("binary_power_two_exists", "(S (S (S k)))"), "cases hP",
             f"have he : exists z d. ({_chain('z','d','S k',tag='bounded_new_chain')}) /\\ ({_at('z','d','S k','x4',tag='pen_bounded_new_last')})",
             *_call("initial_prime_chain_prefix_extend", "k", "x", "x1", "x2", "x4"),
             "exact IH_witness_witness_witness_witness_left", "exact IH_witness_witness_witness_witness_right_left", "exact hn_witness",
             "cases he", "cases he_witness", "cases he_witness_witness", "exists x6", "exists x7", "exists x4", "exists x5",
             "split", "exact he_witness_witness_left", "split", "exact he_witness_witness_right", "split", "exact hP_witness",
             "have hd : x5 = x3 + x3", *_call("binary_power_two_successor_double", "(S (S k))", "x3", "x5"),
             "exact IH_witness_witness_witness_witness_right_right_left", "exact hP_witness", "rewrite hd",
             *_call("lt_trans", "x4", "(x2 + x2)", "(x3 + x3)"),
             *_call("least_prime_above_bertrand_bound", "x2", "x4"),
             *_call("initial_prime_chain_terminal_is_prime", "x", "x1", "k", "x2"),
             "exact IH_witness_witness_witness_witness_left", "exact IH_witness_witness_witness_witness_right_left", "exact hn_witness",
             *_call("add_lt_add", "x2", "x3", "x2", "x3"),
             "exact IH_witness_witness_witness_witness_right_right_right", "exact IH_witness_witness_witness_witness_right_right_right"),
            "Construct the first k+1 primes with their actual terminal value strictly below the witnessed power 2^(k+2).",
        ),
        spec(
            "first_primes_double_exponential_bound",
            f"forall k. ~(k = 0) -> exists b c j p e B. k = S j /\\ "
            f"(({_list('b','c','k',tag='effective_list')}) /\\ "
            f"(({_at('b','c','j','p',tag='pen_effective_last')}) /\\ "
            f"(({_power_two_terms('k','e',tag='pen_effective_exponent')}) /\\ "
            f"(({_power_two_terms('e','B',tag='pen_effective_bound')}) /\\ ({_lt('p','B',tag='pen_effective_strict')})))))",
            ("nonzero_is_succ", "initial_prime_chain_bounded_exists", "binary_power_two_exists",
             "binary_power_two_dominates_successor", "binary_power_two_exponent_monotone", "lt_of_lt_of_le"),
            (*_intro("k", "hk"), "have hj : exists j. k = S j", *_call("nonzero_is_succ", "k"), "exact hk", "cases hj",
             f"have hc : exists b c p P. ({_chain('b','c','x',tag='effective_chain')}) /\\ "
             f"(({_at('b','c','x','p',tag='pen_effective_terminal')}) /\\ "
             f"(({_power_two_terms('S (S x)','P',tag='pen_effective_simple_power')}) /\\ ({_lt('p','P',tag='pen_effective_simple_bound')})))",
             *_call("initial_prime_chain_bounded_exists", "x"), "cases hc", "cases hc_witness", "cases hc_witness_witness",
             "cases hc_witness_witness_witness", "cases hc_witness_witness_witness_witness",
             "cases hc_witness_witness_witness_witness_right", "cases hc_witness_witness_witness_witness_right_right",
             f"have he : exists e. {_power_two_terms('k','e',tag='pen_effective_pow_exists')}", *_call("binary_power_two_exists", "k"), "cases he",
             f"have hB : exists B. {_power_two_terms('x5','B',tag='pen_effective_bound_exists')}", *_call("binary_power_two_exists", "x5"), "cases hB",
             "exists x1", "exists x2", "exists x", "exists x3", "exists x5", "exists x6", "split", "exact hj_witness",
             "split", "right", "exists x", "split", "exact hj_witness", "exact hc_witness_witness_witness_witness_left",
             "split", "exact hc_witness_witness_witness_witness_right_left", "split", "exact he_witness", "split", "exact hB_witness",
             *_call("lt_of_lt_of_le", "x3", "x4", "x6"), "exact hc_witness_witness_witness_witness_right_right_right",
             *_call("binary_power_two_exponent_monotone", "(S (S x))", "x5", "x4", "x6"),
             "rewrite <- hj_witness", *_call("binary_power_two_dominates_successor", "k", "x5"), "exact he_witness",
             "exact hc_witness_witness_witness_witness_right_right_left", "exact hB_witness"),
            "For every positive k, construct exactly the first k primes and both power witnesses proving p_k < 2^(2^k).",
        ),
    )


def _semantic_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    edge = (
        f"exists a t. ({_at('b','c','k','a',tag='pen_semantic_previous')}) /\\ "
        f"(({_at('b','c','S k','t',tag='pen_semantic_last')}) /\\ ({_next('a','t',tag='semantic_next')}))"
    )
    restrict = (
        f"have hr : {_chain('b','c','k',tag='semantic_prefix')}",
        *_call("initial_prime_chain_prefix_restrict", "b", "c", "(S k)", "k"),
        *_call("le_succ_self", "k"), "exact hc",
    )
    last_edge = (
        "cases hc", f"have he : {edge}", "specialize hc_right k", "apply hc_right",
        *_call("le_refl", "(S k)"), "cases he", "cases he_witness", "cases he_witness_witness",
        "cases he_witness_witness_right", "cases he_witness_witness_right_right",
        "cases he_witness_witness_right_right_right",
    )
    return (
        spec(
            "initial_prime_chain_strict_order",
            f"forall b c k i p q. ({_chain('b','c','k',tag='order_chain')}) -> "
            f"({_lt('i','k',tag='pen_order_indices')}) -> ({_at('b','c','i','p',tag='pen_order_first')}) -> "
            f"({_at('b','c','k','q',tag='pen_order_last')}) -> ({_lt('p','q',tag='pen_order_values')})",
            ("lt_not_le", "zero_le", "initial_prime_chain_prefix_restrict", "le_succ_self", "le_refl",
             "finite_lt_succ_eq_or_lt", "beta_at_unique", "lt_trans"),
            (*_intro("b", "c"), "induction k", *_intro("i", "p", "q", "hc", "hi", "hp", "hq"),
             "exfalso", *_call("lt_not_le", "i", "0"), "exact hi", *_call("zero_le", "i"),
             *_intro("i", "p", "q", "hc", "hi", "hp", "hq"), *restrict, *last_edge,
             "have hqeq : q = x1", *_call("beta_at_unique", "b", "c", "(S k)", "q", "x1"),
             "exact hq", "exact he_witness_witness_right_left", "rewrite hqeq",
             f"have hs : i = k \\/ ({_lt('i','k',tag='pen_order_index_case')})", *_call("finite_lt_succ_eq_or_lt", "k", "i"), "exact hi",
             "cases hs", "have hpeq : p = x", *_call("beta_at_unique", "b", "c", "k", "p", "x"),
             "rewrite hs_left at hp", "rewrite hs_left at hp", "exact hp", "exact he_witness_witness_left",
             "rewrite hpeq", "exact he_witness_witness_right_right_right_left",
             *_call("lt_trans", "p", "x", "x1"), "specialize IH i", "specialize IH p", "specialize IH x", "apply IH",
             "exact hr", "exact hs_right", "exact hp", "exact he_witness_witness_left",
             "exact he_witness_witness_right_right_right_left"),
            "Every earlier decoded prime is strictly smaller than the terminal prime; repetitions and descending lists are excluded.",
        ),
        spec(
            "initial_prime_chain_exhausts_primes",
            f"forall b c k p q. ({_chain('b','c','k',tag='complete_chain')}) -> "
            f"({_at('b','c','k','p',tag='pen_complete_terminal')}) -> ({_prime('q',tag='pen_complete_prime')}) -> "
            f"({_le('q','p',tag='pen_complete_value_bound')}) -> exists i. ({_le('i','k',tag='pen_complete_index')}) /\\ "
            f"({_at('b','c','i','q',tag='pen_complete_found')})",
            ("beta_at_unique", "le_antisymm", "prime_two_le", "le_refl", "initial_prime_chain_prefix_restrict",
             "le_succ_self", "le_or_lt", "le_succ"),
            (*_intro("b", "c"), "induction k", *_intro("p", "q", "hc", "hp", "hq", "hqp"), "cases hc",
             "have hp2 : p = 2", *_call("beta_at_unique", "b", "c", "0", "p", "2"), "exact hp", "exact hc_left",
             "have hq2 : q = 2", *_call("le_antisymm", "q", "2"), "rewrite hp2 at hqp", "exact hqp",
             *_call("prime_two_le", "q"), "exact hq", "exists 0", "split", *_call("le_refl", "0"),
             "rewrite hq2", "rewrite hq2", "exact hc_left",
             *_intro("p", "q", "hc", "hp", "hq", "hqp"), *restrict, *last_edge,
             "have hpeq : p = x1", *_call("beta_at_unique", "b", "c", "(S k)", "p", "x1"),
             "exact hp", "exact he_witness_witness_right_left",
             f"have hs : ({_le('q','x',tag='pen_complete_earlier')}) \\/ ({_lt('x','q',tag='pen_complete_later')})",
             *_call("le_or_lt", "q", "x"), "cases hs",
             f"have ho : exists i. ({_le('i','k',tag='pen_complete_old_index')}) /\\ ({_at('b','c','i','q',tag='pen_complete_old_found')})",
             "specialize IH x", "specialize IH q", "apply IH", "exact hr", "exact he_witness_witness_left", "exact hq", "exact hs_left",
             "cases ho", "cases ho_witness", "exists x2", "split", *_call("le_succ", "x2", "k"), "exact ho_witness_left", "exact ho_witness_right",
             "have hqp_eq : q = p", *_call("le_antisymm", "q", "p"), "exact hqp", "rewrite hpeq",
             "specialize he_witness_witness_right_right_right_right q", "apply he_witness_witness_right_right_right_right", "exact hq", "exact hs_right",
             "exists S k", "split", *_call("le_refl", "(S k)"), "rewrite hqp_eq", "rewrite hqp_eq", "exact hp"),
            "Every prime no larger than a decoded terminal prime occurs in the actual prefix; no smaller prime is omitted.",
        ),
        spec(
            "prime_list_nonempty_chain",
            f"forall b c k. ({_list('b','c','k',tag='nonempty_list')}) -> ~(k = 0) -> "
            f"exists j. k = S j /\\ ({_chain('b','c','j',tag='nonempty_chain')})",
            (),
            (*_intro("b", "c", "k", "hl", "hk"), "cases hl", "exfalso", "apply hk", "exact hl_left", "exact hl_right"),
            "Every positive-length first-prime list exposes its actual final index and minimal-successor chain.",
        ),
        spec(
            "prime_list_every_entry_is_prime",
            f"forall b c k i p. ({_list('b','c','k',tag='entries_list')}) -> "
            f"({_lt('i','k',tag='pen_entries_index')}) -> ({_at('b','c','i','p',tag='pen_entries_value')}) -> "
            f"({_prime('p',tag='pen_entries_prime')})",
            ("lt_not_le", "zero_le", "le_of_succ_le_succ", "initial_prime_chain_prefix_restrict", "initial_prime_chain_terminal_is_prime"),
            (*_intro("b", "c", "k", "i", "p", "hl", "hi", "hp"), "cases hl", "exfalso",
             "rewrite hl_left at hi", *_call("lt_not_le", "i", "0"), "exact hi", *_call("zero_le", "i"),
             "cases hl_right", "cases hl_right_witness",
             *_call("initial_prime_chain_terminal_is_prime", "b", "c", "i", "p"),
             *_call("initial_prime_chain_prefix_restrict", "b", "c", "x", "i"),
             *_call("le_of_succ_le_succ", "i", "x"), "rewrite hl_right_witness_left at hi", "exact hi",
             "exact hl_right_witness_right", "exact hp"),
            "Every entry of every first-prime list is prime, with the empty-list boundary proved vacuously.",
        ),
        spec(
            "prime_list_omits_no_smaller_prime",
            f"forall b c k i p q. ({_list('b','c','k',tag='list_complete_source')}) -> "
            f"({_lt('i','k',tag='pen_list_complete_index')}) -> ({_at('b','c','i','p',tag='pen_list_complete_value')}) -> "
            f"({_prime('q',tag='pen_list_complete_prime')}) -> ({_le('q','p',tag='pen_list_complete_bound')}) -> "
            f"exists j. ({_le('j','i',tag='pen_list_complete_position')}) /\\ ({_at('b','c','j','q',tag='pen_list_complete_found')})",
            ("lt_not_le", "zero_le", "le_of_succ_le_succ", "initial_prime_chain_prefix_restrict", "initial_prime_chain_exhausts_primes"),
            (*_intro("b", "c", "k", "i", "p", "q", "hl", "hi", "hp", "hq", "hqp"), "cases hl", "exfalso",
             "rewrite hl_left at hi", *_call("lt_not_le", "i", "0"), "exact hi", *_call("zero_le", "i"),
             "cases hl_right", "cases hl_right_witness",
             *_call("initial_prime_chain_exhausts_primes", "b", "c", "i", "p", "q"),
             *_call("initial_prime_chain_prefix_restrict", "b", "c", "x", "i"),
             *_call("le_of_succ_le_succ", "i", "x"), "rewrite hl_right_witness_left at hi", "exact hi",
             "exact hl_right_witness_right", "exact hp", "exact hq", "exact hqp"),
            "The first-prime list is exhaustive below each of its entries, with an explicit bounded index witnessing every smaller prime.",
        ),
        spec(
            "prime_list_strictly_increasing",
            f"forall b c k i j p q. ({_list('b','c','k',tag='list_order_source')}) -> "
            f"({_lt('i','j',tag='pen_list_order_indices')}) -> ({_lt('j','k',tag='pen_list_order_bound')}) -> "
            f"({_at('b','c','i','p',tag='pen_list_order_first')}) -> ({_at('b','c','j','q',tag='pen_list_order_last')}) -> "
            f"({_lt('p','q',tag='pen_list_order_values')})",
            ("lt_not_le", "zero_le", "le_of_succ_le_succ", "initial_prime_chain_prefix_restrict", "initial_prime_chain_strict_order"),
            (*_intro("b", "c", "k", "i", "j", "p", "q", "hl", "hij", "hj", "hp", "hq"), "cases hl", "exfalso",
             "rewrite hl_left at hj", *_call("lt_not_le", "j", "0"), "exact hj", *_call("zero_le", "j"),
             "cases hl_right", "cases hl_right_witness",
             *_call("initial_prime_chain_strict_order", "b", "c", "j", "i", "p", "q"),
             *_call("initial_prime_chain_prefix_restrict", "b", "c", "x", "j"),
             *_call("le_of_succ_le_succ", "j", "x"), "rewrite hl_right_witness_left at hj", "exact hj",
             "exact hl_right_witness_right", "exact hij", "exact hp", "exact hq"),
            "Every first-prime list is strictly increasing at all valid index pairs, not merely at its last transition.",
        ),
        spec(
            "first_primes_list_exists",
            f"forall k. exists b c. {_list('b','c','k',tag='total_list')}",
            ("eq_decidable", "first_primes_double_exponential_bound"),
            (*_intro("k"), "have hz : k = 0 \\/ ~(k = 0)", *_call("eq_decidable", "k", "0"), "cases hz",
             "exists 0", "exists 0", "left", "exact hz_left",
             "specialize first_primes_double_exponential_bound k", "have hpositive : "
             f"exists b c j p e B. k = S j /\\ (({_list('b','c','k',tag='total_positive_list')}) /\\ "
             f"(({_at('b','c','j','p',tag='pen_total_positive_last')}) /\\ "
             f"(({_power_two_terms('k','e',tag='pen_total_positive_exponent')}) /\\ "
             f"(({_power_two_terms('e','B',tag='pen_total_positive_bound')}) /\\ ({_lt('p','B',tag='pen_total_positive_strict')})))))",
             "apply first_primes_double_exponential_bound", "exact hz_right", "cases hpositive", "cases hpositive_witness",
             "cases hpositive_witness_witness", "cases hpositive_witness_witness_witness", "cases hpositive_witness_witness_witness_witness",
             "cases hpositive_witness_witness_witness_witness_witness", "cases hpositive_witness_witness_witness_witness_witness_witness",
             "cases hpositive_witness_witness_witness_witness_witness_witness_right", "exists x", "exists x1",
             "exact hpositive_witness_witness_witness_witness_witness_witness_right_left"),
            "Every finite number of initial primes has a real beta-coded list, including the empty list at zero.",
        ),
    )


def make_prime_enumeration_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Dependency-ordered exact proof scripts; independent release gates follow."""
    return (*_next_rows(spec), *_chain_rows(spec), *_semantic_rows(spec))
