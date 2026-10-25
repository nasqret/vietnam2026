"""Exact effective prime-count bounds, authored over unchanged first-order HA.

All counting, masking, products and powers expand to existing beta-coded
relations. Candidate-body checks are not library admission receipts.
"""

from __future__ import annotations

import re
from typing import Any, Callable

from .bertrand_primorial_foundation_candidate import (
    _prime_term, _primorial_factor_choice_term, _primorial_factor_prefix_term,
    _primorial_relation_term,
)
from .bertrand_central_binom_candidate import _central_binom_relation_term
from .bertrand_prime_contribution_candidate import (
    _prime_contribution_choice_term, _prime_contribution_prefix_term,
    _prime_contribution_product_term,
)
from .binary_length_candidate import _length_terms
from .finite_fold_surface import _identifier, _product_relation_term
from .finite_sum_theorems import _at, _sum_relation_terms
from .power_algebra_theorems import _power_terms


def _call(name: str, *arguments: str) -> tuple[str, ...]:
    return (*(f"specialize {name} {argument}" for argument in arguments), f"apply {name}")


def _intro(*names: str) -> tuple[str, ...]:
    return tuple(f"intro {name}" for name in names)


def _rewrite(formula: str, variable: str, equation: str, hypothesis: str) -> tuple[str, ...]:
    return (f"rewrite {equation} at {hypothesis}",) * len(re.findall(rf"\b{re.escape(variable)}\b", formula))


def _fresh(tag: str, terms: tuple[str, ...], *roles: str) -> tuple[str, ...]:
    _identifier(tag, "prime-count definition tag")
    names = tuple(f"pc_{role}_{tag}" for role in roles)
    variables = set(re.findall(r"[A-Za-z_][A-Za-z_0-9']*", " ".join(terms)))
    if set(names) & variables or any(f"_{tag}" in name for name in variables):
        raise ValueError("prime-count definition binder captures an argument")
    return names


def _lt(a: str, b: str, *, tag: str) -> str:
    (gap,) = _fresh(tag, (a, b), "lt")
    return f"exists {gap}. {gap} + S ({a}) = ({b})"


def _le(a: str, b: str, *, tag: str) -> str:
    (gap,) = _fresh(tag, (a, b), "le")
    return f"exists {gap}. {gap} + ({a}) = ({b})"


def _prime(a: str, *, tag: str) -> str:
    variables = tuple(sorted(set(re.findall(r"[A-Za-z_][A-Za-z_0-9']*", a)) - {"S"}))
    return _prime_term(a, tag=f"pc_{tag}", avoid=variables)


def _sum(b: str, c: str, l: str, n: str, *, tag: str) -> str:
    return _sum_relation_terms(b, c, l, n, tag=f"pc_{tag}")


def _product(b: str, c: str, l: str, n: str, *, tag: str) -> str:
    return _product_relation_term(b, c, l, n, tag=f"pc_{tag}", avoid=(b, c, l, n))


def _pow(a: str, e: str, n: str, *, tag: str) -> str:
    return _power_terms(a, e, n, tag=f"pc_{tag}")


def _vars(*terms: str) -> tuple[str, ...]:
    return tuple(sorted(set(re.findall(r"[A-Za-z_][A-Za-z_0-9']*", " ".join(terms))) - {"S"}))


def _central(n: str, C: str, *, tag: str) -> str:
    return _central_binom_relation_term(n, C, tag=f"pc_{tag}", variables=_vars(n,C))


def _length(n: str, ell: str, *, tag: str) -> str:
    return _length_terms(n,ell,tag=f"pc_{tag}",variables=_vars(n,ell))


def _pchoice(i: str, a: str, *, tag: str) -> str:
    return _primorial_factor_choice_term(i,a,tag=f"pc_{tag}",variables=_vars(i,a))


def _pprefix(b: str, c: str, l: str, *, tag: str) -> str:
    return _primorial_factor_prefix_term(b,c,l,tag=f"pc_{tag}",variables=_vars(b,c,l))


def _primorial(l: str, P: str, *, tag: str) -> str:
    return _primorial_relation_term(l,P,tag=f"pc_{tag}",variables=_vars(l,P))


def _cchoice(C: str, i: str, a: str, *, tag: str) -> str:
    return _prime_contribution_choice_term(C,i,a,tag=f"pc_{tag}",variables=_vars(C,i,a))


def _cprefix(C: str, b: str, c: str, l: str, *, tag: str) -> str:
    return _prime_contribution_prefix_term(C,b,c,l,tag=f"pc_{tag}",variables=_vars(C,b,c,l))


def _contribution(C: str, l: str, P: str, *, tag: str) -> str:
    return _prime_contribution_product_term(C,l,P,tag=f"pc_{tag}",variables=_vars(C,l,P))


def _bits(b: str, c: str, l: str, *, tag: str) -> str:
    i, e = _fresh(tag, (b, c, l), "index", "bit")
    return f"forall {i}. ({_lt(i, l, tag=f'{tag}_bound')}) -> exists {e}. ({_at(b,c,i,e,tag=f'pc_{tag}_entry')}) /\\ ({e} = 0 \\/ {e} = 1)"


def _choice(i: str, e: str, *, tag: str) -> str:
    p = _prime(f"S ({i})", tag=f"{tag}_prime")
    return f"((({p}) /\\ {e} = 1) \\/ (~({p}) /\\ {e} = 0))"


def _mask(b: str, c: str, l: str, *, tag: str) -> str:
    i, e = _fresh(tag, (b, c, l), "index", "bit")
    entry = _at(b, c, i, e, tag=f"pc_{tag}_entry")
    return f"forall {i}. ({_lt(i,l,tag=f'{tag}_bound')}) -> exists {e}. ({entry}) /\\ ({_choice(i,e,tag=f'{tag}_choice')})"


def prime_bit_prefix(b: str, c: str, length: str, *, tag: str) -> str:
    """Bit at index i is one exactly when S i is prime."""
    for value in (b, c, length):
        _identifier(value, "prime-mask argument")
    return _mask(b, c, length, tag=tag)


def _count(bound: str, count: str, *, tag: str) -> str:
    b, c = _fresh(tag, (bound, count), "code", "scale")
    return f"exists {b} {c}. ({_mask(b,c,bound,tag=f'{tag}_mask')}) /\\ ({_sum(b,c,bound,count,tag=f'{tag}_sum')})"


def prime_count(bound: str, count: str, *, tag: str) -> str:
    """Actual finite count of the primes at most bound, including bounds 0,1."""
    for value in (bound, count):
        _identifier(value, "prime-count argument")
    return _count(bound, count, tag=tag)


def _weighted(b: str, c: str, d: str, f: str, length: str, base: str, *, upper: bool, tag: str) -> str:
    i, a, e = _fresh(tag, (b, c, d, f, length, base), "index", "factor", "bit")
    zero = f"{a} = 1" if upper else _le("1", a, tag=f"{tag}_zero")
    one = _le(a, base, tag=f"{tag}_one") if upper else _le(base, a, tag=f"{tag}_one")
    return (
        f"forall {i} {a} {e}. ({_lt(i,length,tag=f'{tag}_index')}) -> "
        f"({_at(b,c,i,a,tag=f'pc_{tag}_factor')}) -> ({_at(d,f,i,e,tag=f'pc_{tag}_bit')}) -> "
        f"(({e} = 0 /\\ ({zero})) \\/ ({e} = 1 /\\ ({one})))"
    )


def _weighted_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    rows = []
    for upper in (True, False):
        direction = "upper" if upper else "lower"
        weight = lambda length, tag: _weighted("b", "c", "d", "f", length, "B", upper=upper, tag=f"weight_{direction}_{tag}")
        bound = lambda left, right, tag: _le(left, right, tag=tag) if upper else _le(right, left, tag=tag)
        last_zero = "x = 1" if upper else _le("1", "x", tag="weight_last_zero")
        last_one = _le("x", "B", tag="weight_last_one") if upper else _le("B", "x", tag="weight_last_one")
        dependencies = (
            "beta_product_zero", "beta_sum_zero", "pow_zero", "le_refl",
            "beta_product_succ_decompose", "beta_sum_succ_decompose", "pow_exists",
            "le_succ", "pow_functional", "pow_successor_pair_mul", "mul_le_mul",
            *(("mul_one",) if upper else ("le_trans", "le_mul_of_one_le_right")),
        )
        zero_finish = (
            ("rewrite hlast_left_right", "have hm : x1 * 1 = x1", "apply mul_one", "rewrite hm", "exact hpre")
            if upper else
            (*_call("le_trans", "x4", "x1", "(x1 * x)"), "exact hpre", *_call("le_mul_of_one_le_right", "x1", "x"), "exact hlast_left_right")
        )
        one_finish = (
            (*_call("mul_le_mul", "x1", "x4", "x", "B"), "exact hpre", "exact hlast_right_right")
            if upper else
            (*_call("mul_le_mul", "x4", "x1", "B", "x"), "exact hpre", "exact hlast_right_right")
        )
        rows.append(spec(
            f"beta_product_bit_weighted_{direction}_power",
            f"forall b c d f B l z k Q. ({weight('l','source')}) -> ({_product('b','c','l','z',tag=f'weight_{direction}_product')}) -> "
            f"({_sum('d','f','l','k',tag=f'weight_{direction}_sum')}) -> ({_pow('B','k','Q',tag=f'weight_{direction}_power')}) -> "
            f"({bound('z','Q',f'weight_{direction}_result')})",
            dependencies,
            (*_intro("b", "c", "d", "f", "B"), "induction l", *_intro("z", "k", "Q", "hw", "hz", "hk", "hQ"),
             "have hz1 : z = 1", *_call("beta_product_zero", "b", "c", "z"), "exact hz",
             "have hk0 : k = 0", *_call("beta_sum_zero", "d", "f", "k"), "exact hk",
             "have hQ1 : Q = 1", *_call("pow_zero", "B", "k", "Q"), "exact hk0", "exact hQ",
             "rewrite hz1", "rewrite hQ1", *_call("le_refl", "1"),
             *_intro("z", "k", "Q", "hw", "hz", "hk", "hQ"),
             f"have hprod : exists a w. ({_at('b','c','l','a',tag='pc_weight_last_factor')}) /\\ (({_product('b','c','l','w',tag='weight_previous_product')}) /\\ z = w * a)",
             *_call("beta_product_succ_decompose", "b", "c", "l", "z"), "exact hz", "cases hprod", "cases hprod_witness", "cases hprod_witness_witness", "cases hprod_witness_witness_right",
             f"have hsum : exists e K. ({_at('d','f','l','e',tag='pc_weight_last_bit')}) /\\ (({_sum('d','f','l','K',tag='weight_previous_sum')}) /\\ k = K + e)",
             *_call("beta_sum_succ_decompose", "d", "f", "l", "k"), "exact hk", "cases hsum", "cases hsum_witness", "cases hsum_witness_witness", "cases hsum_witness_witness_right",
             f"have hp : exists R. {_pow('B','x3','R',tag='weight_previous_power')}", *_call("pow_exists", "B", "x3"), "cases hp",
             f"have hpre : {bound('x1','x4','weight_previous_bound')}", "specialize IH x1", "specialize IH x3", "specialize IH x4", "apply IH",
             *_intro("i", "a", "e", "hi", "ha", "he"), "specialize hw i", "specialize hw a", "specialize hw e", "apply hw",
             *_call("le_succ", "(S i)", "l"), "exact hi", "exact ha", "exact he",
             "exact hprod_witness_witness_right_left", "exact hsum_witness_witness_right_left", "exact hp_witness",
             f"have hlast : (x2 = 0 /\\ ({last_zero})) \\/ (x2 = 1 /\\ ({last_one}))",
             "specialize hw l", "specialize hw x", "specialize hw x2", "apply hw", *_call("le_refl", "(S l)"),
             "exact hprod_witness_witness_left", "exact hsum_witness_witness_left", "cases hlast", "cases hlast_left",
             "have hk0 : k = x3", "trans x3 + x2", "exact hsum_witness_witness_right_right", "rewrite hlast_left_left", "apply PA3",
             *_rewrite(_pow('B','k','Q',tag='weight_zero_transport'), 'k', 'hk0', 'hQ'),
             "have hQ0 : Q = x4", *_call("pow_functional", "B", "x3", "Q", "x4"), "exact hQ", "exact hp_witness",
             "rewrite hprod_witness_witness_right_right", "rewrite hQ0", *zero_finish,
             "cases hlast_right", "have hk1 : k = S x3", "trans x3 + x2", "exact hsum_witness_witness_right_right", "rewrite hlast_right_left", "simp",
             "have hQ1 : Q = x4 * B", *_call("pow_successor_pair_mul", "B", "x3", "k", "x4", "Q"), "exact hk1", "exact hp_witness", "exact hQ",
             "rewrite hprod_witness_witness_right_right", "rewrite hQ1", *one_finish),
            f"An actual bit-weighted finite product has the corresponding {direction} bound by a power of its actual bit sum.",
        ))
    return tuple(rows)


def _cutchoice(u: str, b: str, c: str, i: str, e: str, *, tag: str) -> str:
    return f"((({_lt(i,u,tag=f'{tag}_below')}) /\\ {e} = 0) \\/ (({_le(u,i,tag=f'{tag}_above')}) /\\ ({_at(b,c,i,e,tag=f'pc_{tag}_source')})))"


def _cutoff(u: str, b: str, c: str, d: str, f: str, length: str, *, tag: str) -> str:
    i, e = _fresh(tag, (u, b, c, d, f, length), "index", "bit")
    return f"forall {i}. ({_lt(i,length,tag=f'{tag}_bound')}) -> exists {e}. ({_at(d,f,i,e,tag=f'pc_{tag}_entry')}) /\\ ({_cutchoice(u,b,c,i,e,tag=f'{tag}_choice')})"


def cutoff_bit_prefix(u: str, b: str, c: str, d: str, f: str, length: str, *, tag: str) -> str:
    """Zero below index u; exactly the source entries from index u onward."""
    arguments = (u, b, c, d, f, length)
    for value in arguments:
        _identifier(value, "cutoff-prefix argument")
    return _cutoff(*arguments, tag=tag)


def _cutoff_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "beta_cutoff_choice_exists",
            f"forall u b c i. exists e. {_cutchoice('u','b','c','i','e',tag='cutchoice_exists')}",
            ("le_or_lt", "beta_at_exists"),
            (*_intro("u", "b", "c", "i"), "have hs : (exists g. g + u = i) \\/ (exists g. g + S i = u)", *_call("le_or_lt", "u", "i"), "cases hs",
             f"have he : exists e. {_at('b','c','i','e',tag='pc_cutchoice_value')}", *_call("beta_at_exists", "b", "c", "i"), "cases he",
             "exists x", "right", "split", "exact hs_left", "exact he_witness", "exists 0", "left", "split", "exact hs_right", "refl"),
            "Construct each exact cutoff entry by decidable order and beta decoding.",
        ),
        spec(
            "beta_cutoff_prefix_empty",
            f"forall u b c d f. {_cutoff('u','b','c','d','f','0',tag='cut_empty')}",
            ("lt_not_le", "zero_le"),
            (*_intro("u", "b", "c", "d", "f", "i", "hi"), "exfalso", *_call("lt_not_le", "i", "0"), "exact hi", *_call("zero_le", "i")),
            "The empty cutoff prefix is valid for every source and threshold.",
        ),
        spec(
            "beta_cutoff_prefix_drop_last",
            f"forall u b c d f l. ({_cutoff('u','b','c','d','f','S l',tag='cut_drop_source')}) -> ({_cutoff('u','b','c','d','f','l',tag='cut_drop_target')})",
            ("le_succ",),
            (*_intro("u", "b", "c", "d", "f", "l", "h", "i", "hi"), "specialize h i", "apply h", *_call("le_succ", "(S i)", "l"), "exact hi"),
            "Restrict an actual cutoff table to its preceding prefix.",
        ),
        spec(
            "beta_cutoff_prefix_entry",
            f"forall u b c d f l i e. ({_cutoff('u','b','c','d','f','l',tag='cut_entry_source')}) -> ({_lt('i','l',tag='cut_entry_bound')}) -> "
            f"({_at('d','f','i','e',tag='pc_cut_entry_given')}) -> ({_cutchoice('u','b','c','i','e',tag='cut_entry_choice')})",
            ("beta_at_unique",),
            (*_intro("u", "b", "c", "d", "f", "l", "i", "e", "h", "hi", "he"),
             f"have hp : exists a. ({_at('d','f','i','a',tag='pc_cut_entry_actual')}) /\\ ({_cutchoice('u','b','c','i','a',tag='cut_entry_actual_choice')})",
             "specialize h i", "apply h", "exact hi", "cases hp", "cases hp_witness",
             "have heq : x = e", *_call("beta_at_unique", "d", "f", "i", "x", "e"), "exact hp_witness_left", "exact he",
             *_rewrite(_cutchoice('u','b','c','i','x',tag='cut_entry_transport'), 'x', 'heq', 'hp_witness_right'), "exact hp_witness_right"),
            "Every decoded cutoff entry obeys its actual below/above-threshold choice.",
        ),
        spec(
            "beta_cutoff_prefix_extend",
            f"forall u b c d f l e. ({_cutoff('u','b','c','d','f','l',tag='cut_extend_source')}) -> ({_cutchoice('u','b','c','l','e',tag='cut_extend_choice')}) -> "
            f"exists g h. {_cutoff('u','b','c','g','h','S l',tag='cut_extend_target')}",
            ("beta_prefix_extend", "le_eq_or_lt", "le_of_succ_le_succ"),
            (*_intro("u", "b", "c", "d", "f", "l", "e", "h", "he"),
             f"have hext : exists g j. ({_at('g','j','l','e',tag='pc_cut_extend_last')}) /\\ "
             f"forall i a. ({_lt('i','l',tag='cut_extend_bound')}) -> ({_at('d','f','i','a',tag='pc_cut_extend_old')}) -> ({_at('g','j','i','a',tag='pc_cut_extend_new')})",
             *_call("beta_prefix_extend", "l", "d", "f", "e"), "cases hext", "cases hext_witness", "cases hext_witness_witness",
             "exists x", "exists x1", "intro i", "intro hi",
             "have hc : i = l \\/ exists g. g + S i = l", *_call("le_eq_or_lt", "i", "l"), *_call("le_of_succ_le_succ", "i", "l"), "exact hi", "cases hc",
             "exists e", "split", "rewrite hc_left", "rewrite hc_left", "exact hext_witness_witness_left",
             *("rewrite hc_left",) * len(re.findall(r"\bi\b", _cutchoice('u','b','c','i','e',tag='cut_extend_transport'))), "exact he",
             f"have hp : exists a. ({_at('d','f','i','a',tag='pc_cut_extend_point')}) /\\ ({_cutchoice('u','b','c','i','a',tag='cut_extend_point_choice')})",
             "specialize h i", "apply h", "exact hc_right", "cases hp", "cases hp_witness", "exists x2", "split",
             "specialize hext_witness_witness_right i", "specialize hext_witness_witness_right x2", "apply hext_witness_witness_right", "exact hc_right", "exact hp_witness_left", "exact hp_witness_right"),
            "Append an actual cutoff choice, preserving every previously coded entry.",
        ),
        spec(
            "beta_cutoff_prefix_exists",
            f"forall u b c l. exists d f. {_cutoff('u','b','c','d','f','l',tag='cut_exists')}",
            ("beta_cutoff_prefix_empty", "beta_cutoff_choice_exists", "beta_cutoff_prefix_extend"),
            (*_intro("u", "b", "c"), "induction l", "exists 0", "exists 0", *_call("beta_cutoff_prefix_empty", "u", "b", "c", "0", "0"),
             f"have hp : exists d f. {_cutoff('u','b','c','d','f','l',tag='cut_exists_pre')}", "apply IH", "cases hp", "cases hp_witness",
             f"have hc : exists e. {_cutchoice('u','b','c','l','e',tag='cut_exists_choice')}", *_call("beta_cutoff_choice_exists", "u", "b", "c", "l"), "cases hc",
             *_call("beta_cutoff_prefix_extend", "u", "b", "c", "x", "x1", "l", "x2"), "exact hp_witness_witness", "exact hc_witness"),
            "Construct the complete finite cutoff table by actual length induction.",
        ),
        spec(
            "beta_cutoff_count_comparison",
            f"forall u b c d f l k L. ({_bits('b','c','l',tag='cut_count_bits')}) -> ({_cutoff('u','b','c','d','f','l',tag='cut_count_source')}) -> "
            f"({_sum('b','c','l','k',tag='cut_count_whole')}) -> ({_sum('d','f','l','L',tag='cut_count_tail')}) -> ({_le('k','u + L',tag='cut_count_result')})",
            ("beta_sum_zero", "zero_le", "le_or_lt", "bit_count_bounded", "le_trans", "le_add_right", "beta_sum_succ_decompose", "beta_cutoff_prefix_entry",
             "le_refl", "lt_not_le", "beta_at_unique", "all_bits_prefix_succ", "beta_cutoff_prefix_drop_last", "add_le_add_right", "add_assoc"),
            (*_intro("u", "b", "c", "d", "f"), "induction l", *_intro("k", "L", "hb", "hc", "hk", "hL"),
             "have hk0 : k = 0", *_call("beta_sum_zero", "b", "c", "k"), "exact hk", "rewrite hk0", *_call("zero_le", "(u + L)"),
             *_intro("k", "L", "hb", "hc", "hk", "hL"), "have hs : (exists g. g + u = l) \\/ (exists g. g + S l = u)", *_call("le_or_lt", "u", "l"), "cases hs",
             f"have hd : exists e K. ({_at('b','c','l','e',tag='pc_cut_count_source_last')}) /\\ (({_sum('b','c','l','K',tag='cut_count_source_pre')}) /\\ k = K + e)",
             *_call("beta_sum_succ_decompose", "b", "c", "l", "k"), "exact hk", "cases hd", "cases hd_witness", "cases hd_witness_witness", "cases hd_witness_witness_right",
             f"have he : exists e M. ({_at('d','f','l','e',tag='pc_cut_count_tail_last')}) /\\ (({_sum('d','f','l','M',tag='cut_count_tail_pre')}) /\\ L = M + e)",
             *_call("beta_sum_succ_decompose", "d", "f", "l", "L"), "exact hL", "cases he", "cases he_witness", "cases he_witness_witness", "cases he_witness_witness_right",
             f"have hlast : {_cutchoice('u','b','c','l','x2',tag='cut_count_choice')}", *_call("beta_cutoff_prefix_entry", "u", "b", "c", "d", "f", "(S l)", "l", "x2"),
             "exact hc", *_call("le_refl", "(S l)"), "exact he_witness_witness_left", "cases hlast", "cases hlast_left", "exfalso",
             *_call("lt_not_le", "l", "u"), "exact hlast_left_left", "exact hs_left", "cases hlast_right",
             "have heq : x = x2", *_call("beta_at_unique", "b", "c", "l", "x", "x2"), "exact hd_witness_witness_left", "exact hlast_right_right",
             "have hpre : exists g. g + x1 = u + x3", "specialize IH x1", "specialize IH x3", "apply IH",
             *_call("all_bits_prefix_succ", "b", "c", "l", "(S l)"), "refl", "exact hb",
             *_call("beta_cutoff_prefix_drop_last", "u", "b", "c", "d", "f", "l"), "exact hc", "exact hd_witness_witness_right_left", "exact he_witness_witness_right_left",
             "rewrite hd_witness_witness_right_right", "rewrite he_witness_witness_right_right", "rewrite heq",
             "have hassoc : u + (x3 + x2) = (u + x3) + x2", "symm", "apply add_assoc", "rewrite hassoc",
             *_call("add_le_add_right", "x1", "(u + x3)", "x2"), "exact hpre",
             "have hsmall : exists g. g + k = u", *_call("le_trans", "k", "(S l)", "u"),
             *_call("bit_count_bounded", "b", "c", "(S l)", "k"), "split", "exact hk", "exact hb", "exact hs_right",
             *_call("le_trans", "k", "u", "(u + L)"), "exact hsmall", *_call("le_add_right", "u", "L")),
            "The full bit count is at most the cutoff index plus the actual count above that index.",
        ),
    )


def _power_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "binary_power_two_dominates_successor",
            f"forall n v. ({_pow('2','n','v',tag='power_dom_source')}) -> ({_le('S n','v',tag='power_dom_result')})",
            ("pow_zero", "le_refl", "pow_successor_decompose", "mul_le_mul_right", "le_trans", "add_comm", "zero_add"),
            ("induction n", *_intro("v", "h"), "have heq : v = 1", *_call("pow_zero", "2", "0", "v"), "refl", "exact h",
             "rewrite heq", *_call("le_refl", "1"), *_intro("v", "h"),
             f"have hp : exists a. ({_pow('2','n','a',tag='power_dom_previous')}) /\\ v = a * 2", *_call("pow_successor_decompose", "2", "n", "(S n)", "v"), "refl", "exact h", "cases hp", "cases hp_witness",
             "have hpre : exists g. g + S n = x", "specialize IH x", "apply IH", "exact hp_witness_left",
             "rewrite hp_witness_right", *_call("le_trans", "(S (S n))", "((S n) * 2)", "(x * 2)"), "exists n", "simp [add_comm, zero_add]",
             *_call("mul_le_mul_right", "(S n)", "x", "2"), "exact hpre"),
            "Actual powers of two dominate the successor of their exponent, by HA induction.",
        ),
        spec(
            "binary_power_two_order_reflects_exponent",
            f"forall a b x y. ({_pow('2','a','x',tag='power_reflect_left')}) -> ({_pow('2','b','y',tag='power_reflect_right')}) -> "
            f"({_le('x','y',tag='power_reflect_values')}) -> ({_le('a','b',tag='power_reflect_result')})",
            ("le_or_lt", "binary_power_two_exponent_strict", "lt_not_le"),
            (*_intro("a", "b", "x", "y", "hx", "hy", "hle"), "have hc : (exists g. g + a = b) \\/ (exists g. g + S b = a)", *_call("le_or_lt", "a", "b"), "cases hc", "exact hc_left", "exfalso",
             *_call("lt_not_le", "y", "x"), *_call("binary_power_two_exponent_strict", "b", "a", "y", "x"), "exact hc_right", "exact hy", "exact hx", "exact hle"),
            "Weak order between actual powers of two reflects weak order of the exponents.",
        ),
        spec(
            "binary_power_two_strict_order_reflects_exponent",
            f"forall a b x y. ({_pow('2','a','x',tag='power_strict_reflect_left')}) -> ({_pow('2','b','y',tag='power_strict_reflect_right')}) -> "
            f"({_lt('x','y',tag='power_strict_reflect_values')}) -> ({_lt('a','b',tag='power_strict_reflect_result')})",
            ("le_or_lt", "binary_power_two_exponent_monotone", "lt_not_le"),
            (*_intro("a", "b", "x", "y", "hx", "hy", "hlt"), "have hc : (exists g. g + b = a) \\/ (exists g. g + S a = b)", *_call("le_or_lt", "b", "a"), "cases hc", "exfalso",
             *_call("lt_not_le", "x", "y"), "exact hlt", *_call("binary_power_two_exponent_monotone", "b", "a", "y", "x"), "exact hc_left", "exact hy", "exact hx", "exact hc_right"),
            "Strict order between actual powers of two reflects strict exponent order.",
        ),
        spec(
            "pow_four_is_square_of_pow_two",
            f"forall n v w. ({_pow('2','n','v',tag='power_four_binary')}) -> ({_pow('4','n','w',tag='power_four_quaternary')}) -> w = v * v",
            ("pow_mul_base",),
            (*_intro("n", "v", "w", "hv", "hw"), *_call("pow_mul_base", "2", "2", "n", "v", "v", "w"), "exact hv", "exact hv",
             "have hfour : 2 * 2 = 4", "norm_num", "rewrite hfour", "rewrite hfour", "exact hw"),
            "The actual fourth power-base value is the square of the actual binary power value.",
        ),
        spec(
            "central_binom_dominates_pow_two",
            f"forall n C v. ({_le('4','n',tag='central_lower_bound')}) -> ({_central('n','C',tag='central_lower_value')}) -> "
            f"({_pow('2','n','v',tag='central_lower_power')}) -> ({_le('v','C',tag='central_lower_result')})",
            ("pow_exists", "pow_four_is_square_of_pow_two", "four_pow_lt_mul_central_binom", "binary_power_two_dominates_successor", "lt_to_le",
             "mul_le_mul_right", "le_trans", "mul_le_cancel_left_nonzero", "pow_nonzero_of_one_le"),
            (*_intro("n", "C", "v", "hn", "hC", "hv"), f"have hw : exists w. {_pow('4','n','w',tag='central_lower_four')}", *_call("pow_exists", "4", "n"), "cases hw",
             "have hsquare : x = v * v", *_call("pow_four_is_square_of_pow_two", "n", "v", "x"), "exact hv", "exact hw_witness",
             "have hlower : exists g. g + S x = n * C", *_call("four_pow_lt_mul_central_binom", "n", "x", "C"), "exact hn", "exact hw_witness", "exact hC",
             "have hnsmall : exists g. g + n = v", *_call("lt_to_le", "n", "v"), *_call("binary_power_two_dominates_successor", "n", "v"), "exact hv",
             "have hscale : exists g. g + n * C = v * C", *_call("mul_le_mul_right", "n", "v", "C"), "exact hnsmall",
             "have hfull : exists g. g + x = v * C", *_call("le_trans", "x", "(n * C)", "(v * C)"), *_call("lt_to_le", "x", "(n * C)"), "exact hlower", "exact hscale",
             "rewrite hsquare at hfull", *_call("mul_le_cancel_left_nonzero", "v", "v", "C"), "intro hz",
             *_call("pow_nonzero_of_one_le", "2", "n", "v"), "exists 1", "norm_num", "exact hv", "exact hz", "exact hfull"),
            "For n at least four, the central binomial coefficient dominates the actual 2^n value.",
        ),
    )


def _prime_product_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "primorial_prefix_decoded_choice",
            f"forall b c l i a. ({_pprefix('b','c','l',tag='prim_entry_source')}) -> ({_lt('i','l',tag='prim_entry_bound')}) -> "
            f"({_at('b','c','i','a',tag='pc_prim_entry_given')}) -> ({_pchoice('i','a',tag='prim_entry_result')})",
            ("beta_at_unique",),
            (*_intro("b", "c", "l", "i", "a", "h", "hi", "ha"),
             f"have hp : exists v. ({_at('b','c','i','v',tag='pc_prim_entry_actual')}) /\\ ({_pchoice('i','v',tag='prim_entry_choice')})", "specialize h i", "apply h", "exact hi", "cases hp", "cases hp_witness",
             "have heq : x = a", *_call("beta_at_unique", "b", "c", "i", "x", "a"), "exact hp_witness_left", "exact ha",
             *_rewrite(_pchoice('i','x',tag='prim_entry_transport'), 'x', 'heq', 'hp_witness_right'), "exact hp_witness_right"),
            "Every actually decoded dense primorial factor has its exact prime-or-one choice.",
        ),
        spec(
            "primorial_factor_choice_one_le",
            f"forall i a. ({_pchoice('i','a',tag='prim_positive_source')}) -> ({_le('1','a',tag='prim_positive_result')})",
            ("le_refl",),
            (*_intro("i", "a", "h"), "cases h", "cases h_left", "rewrite h_left_right", "exists i", "simp",
             "cases h_right", "rewrite h_right_right", *_call("le_refl", "1")),
            "Every dense primorial factor is at least one, including nonprime positions.",
        ),
        spec(
            "prime_contribution_prefix_decoded_choice",
            f"forall C b c l i a. ({_cprefix('C','b','c','l',tag='contrib_entry_source')}) -> ({_lt('i','l',tag='contrib_entry_bound')}) -> "
            f"({_at('b','c','i','a',tag='pc_contrib_entry_given')}) -> ({_cchoice('C','i','a',tag='contrib_entry_result')})",
            ("beta_at_unique",),
            (*_intro("C", "b", "c", "l", "i", "a", "h", "hi", "ha"),
             f"have hp : exists v. ({_at('b','c','i','v',tag='pc_contrib_entry_actual')}) /\\ ({_cchoice('C','i','v',tag='contrib_entry_choice')})", "specialize h i", "apply h", "exact hi", "cases hp", "cases hp_witness",
             "have heq : x = a", *_call("beta_at_unique", "b", "c", "i", "x", "a"), "exact hp_witness_left", "exact ha",
             *_rewrite(_cchoice('C','i','x',tag='contrib_entry_transport'), 'x', 'heq', 'hp_witness_right'), "exact hp_witness_right"),
            "Every decoded prime contribution has its actual valuation and power witness, or is one at a nonprime index.",
        ),
        spec(
            "central_binom_prime_mask_weighted_upper",
            f"forall n C b c d f l. ({_le('1','n',tag='central_weight_positive')}) -> ({_central('n','C',tag='central_weight_value')}) -> "
            f"({_cprefix('C','b','c','l',tag='central_weight_factors')}) -> ({_mask('d','f','l',tag='central_weight_mask')}) -> "
            f"({_weighted('b','c','d','f','l','n + n',upper=True,tag='central_weight_result')})",
            ("prime_bit_prefix_entry", "prime_contribution_prefix_decoded_choice", "central_binom_prime_power_contribution_le_double"),
            (*_intro("n", "C", "b", "c", "d", "f", "l", "hn", "hC", "hf", "hm", "i", "a", "e", "hi", "ha", "he"),
             f"have hb : {_choice('i','e',tag='central_weight_bit')}", *_call("prime_bit_prefix_entry", "d", "f", "l", "i", "e"), "exact hm", "exact hi", "exact he",
             f"have hv : {_cchoice('C','i','a',tag='central_weight_factor')}", *_call("prime_contribution_prefix_decoded_choice", "C", "b", "c", "l", "i", "a"), "exact hf", "exact hi", "exact ha",
             "cases hb", "cases hb_left", "cases hv", "cases hv_left", "cases hv_left_right", "cases hv_left_right_witness", "right", "split", "exact hb_left_right",
             *_call("central_binom_prime_power_contribution_le_double", "(S i)", "n", "C", "x", "a"), "exact hb_left_left", "exact hn", "exact hC", "exact hv_left_right_witness_left", "exact hv_left_right_witness_right",
             "cases hv_right", "exfalso", "apply hv_right_left", "exact hb_left_left",
             "cases hb_right", "cases hv", "cases hv_left", "exfalso", "apply hb_right_left", "exact hv_left_left",
             "cases hv_right", "left", "split", "exact hb_right_right", "exact hv_right_right"),
            "The actual central-binomial contribution product is bounded factorwise by 2n exactly at prime-mask positions.",
        ),
        spec(
            "primorial_cutoff_weighted_lower",
            f"forall u b c d f g h l. ({_pprefix('b','c','l',tag='prim_weight_factors')}) -> ({_mask('d','f','l',tag='prim_weight_mask')}) -> "
            f"({_cutoff('u','d','f','g','h','l',tag='prim_weight_cutoff')}) -> ({_weighted('b','c','g','h','l','u',upper=False,tag='prim_weight_result')})",
            ("primorial_prefix_decoded_choice", "primorial_factor_choice_one_le", "beta_cutoff_prefix_entry", "prime_bit_prefix_entry", "le_succ"),
            (*_intro("u", "b", "c", "d", "f", "g", "h", "l", "hf", "hm", "hc", "i", "a", "e", "hi", "ha", "he"),
             f"have hv : {_pchoice('i','a',tag='prim_weight_choice')}", *_call("primorial_prefix_decoded_choice", "b", "c", "l", "i", "a"), "exact hf", "exact hi", "exact ha",
             "have hpositive : exists v. v + 1 = a", *_call("primorial_factor_choice_one_le", "i", "a"), "exact hv",
             f"have hcut : {_cutchoice('u','d','f','i','e',tag='prim_weight_actual_cut')}", *_call("beta_cutoff_prefix_entry", "u", "d", "f", "g", "h", "l", "i", "e"), "exact hc", "exact hi", "exact he",
             "cases hcut", "cases hcut_left", "left", "split", "exact hcut_left_right", "exact hpositive", "cases hcut_right",
             f"have hb : {_choice('i','e',tag='prim_weight_actual_bit')}", *_call("prime_bit_prefix_entry", "d", "f", "l", "i", "e"), "exact hm", "exact hi", "exact hcut_right_right",
             "cases hb", "cases hb_left", "right", "split", "exact hb_left_right", "cases hv", "cases hv_left", "rewrite hv_left_right", *_call("le_succ", "u", "i"), "exact hcut_right_left",
             "cases hv_right", "exfalso", "apply hv_right_left", "exact hb_left_left", "cases hb_right", "left", "split", "exact hb_right_right", "exact hpositive"),
            "Every prime strictly beyond the cutoff contributes at least the cutoff to the actual primorial product.",
        ),
        spec(
            "central_binom_prime_count_power_bound",
            f"forall n N k C Q. ({_le('1','n',tag='central_count_positive')}) -> ({_le('n + n','N',tag='central_count_range')}) -> "
            f"({_count('N','k',tag='central_count_count')}) -> ({_central('n','C',tag='central_count_value')}) -> "
            f"({_pow('n + n','k','Q',tag='central_count_power')}) -> ({_le('C','Q',tag='central_count_result')})",
            ("central_binom_positive", "prime_contribution_complete_exists", "central_binom_prime_divisor_le_double", "le_trans",
             "beta_product_bit_weighted_upper_power", "central_binom_prime_mask_weighted_upper"),
            (*_intro("n", "N", "k", "C", "Q", "hn", "hN", "hk", "hC", "hQ"), "cases hk", "cases hk_witness", "cases hk_witness_witness",
             f"have hcomplete : exists z. ({_contribution('C','N','z',tag='central_count_complete')}) /\\ C = z", *_call("prime_contribution_complete_exists", "C", "N"),
             "intro hz", "have hp : exists r. C = S r", *_call("central_binom_positive", "n", "C"), "exact hC", "cases hp", "apply PA1", "trans C", "symm", "exact hp_witness", "exact hz",
             *_intro("p", "hp", "hd"), *_call("le_trans", "p", "(n + n)", "N"), *_call("central_binom_prime_divisor_le_double", "n", "C", "p"), "exact hp", "exact hC", "exact hd", "exact hN",
             "cases hcomplete", "cases hcomplete_witness", "cases hcomplete_witness_left", "cases hcomplete_witness_left_witness", "cases hcomplete_witness_left_witness_witness",
             "rewrite hcomplete_witness_right", *_call("beta_product_bit_weighted_upper_power", "x3", "x4", "x", "x1", "(n + n)", "N", "x2", "k", "Q"),
             *_call("central_binom_prime_mask_weighted_upper", "n", "C", "x3", "x4", "x", "x1", "N"), "exact hn", "exact hC", "exact hcomplete_witness_left_witness_witness_left", "exact hk_witness_witness_left",
             "exact hcomplete_witness_left_witness_witness_right", "exact hk_witness_witness_right", "exact hQ"),
            "The actual central binomial coefficient is at most (2n)^pi(N) whenever 2n is at most N; all factors and prime counts are constructed.",
        ),
        spec(
            "primorial_cutoff_count_power_bound",
            f"forall n u b c d f L P Q. ({_mask('b','c','n',tag='prim_count_mask')}) -> ({_cutoff('u','b','c','d','f','n',tag='prim_count_cutoff')}) -> "
            f"({_sum('d','f','n','L',tag='prim_count_sum')}) -> ({_primorial('n','P',tag='prim_count_primorial')}) -> "
            f"({_pow('u','L','Q',tag='prim_count_power')}) -> ({_le('Q','P',tag='prim_count_result')})",
            ("beta_product_bit_weighted_lower_power", "primorial_cutoff_weighted_lower"),
            (*_intro("n", "u", "b", "c", "d", "f", "L", "P", "Q", "hm", "hc", "hL", "hP", "hQ"), "cases hP", "cases hP_witness", "cases hP_witness_witness",
             *_call("beta_product_bit_weighted_lower_power", "x", "x1", "d", "f", "u", "n", "P", "L", "Q"),
             *_call("primorial_cutoff_weighted_lower", "u", "x", "x1", "b", "c", "d", "f", "n"), "exact hP_witness_witness_left", "exact hm", "exact hc",
             "exact hP_witness_witness_right", "exact hL", "exact hQ"),
            "The cutoff raised to the actual number of primes beyond it is bounded by the actual primorial.",
        ),
    )


def _scale_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "binary_split_half_lower_bound",
            f"forall N h d m. (d = 0 \\/ d = 1) -> N = (h + h) + d -> ({_le('m + m','N',tag='half_lower_input')}) -> ({_le('m','h',tag='half_lower_result')})",
            ("pairing_double_equals_two_mul", "le_or_lt", "doubling_floor_above_implies_double_above_half", "lt_not_le"),
            (*_intro("N", "h", "d", "m", "hd", "hN", "hm"), "have heq : h + h = 2 * h", *_call("pairing_double_equals_two_mul", "h"),
             "have hrep : N = 2 * h \\/ N = 2 * h + 1", "cases hd", "left", "rewrite hN", "rewrite hd_left", "rewrite heq", "simp",
             "right", "rewrite hN", "rewrite hd_right", "rewrite heq", "refl",
             "have hs : (exists g. g + m = h) \\/ (exists g. g + S h = m)", *_call("le_or_lt", "m", "h"), "cases hs", "exact hs_left",
             "exfalso", *_call("lt_not_le", "N", "(2 * m)"), *_call("doubling_floor_above_implies_double_above_half", "N", "h", "m"), "exact hrep", "exact hs_right",
             "have hmeq : m + m = 2 * m", *_call("pairing_double_equals_two_mul", "m"), "rewrite hmeq at hm", "exact hm"),
            "A lower bound on a doubled input reflects to its actual binary quotient, including either remainder bit.",
        ),
        spec(
            "binary_split_successor_le_double_successor",
            f"forall e h d ell. (d = 0 \\/ d = 1) -> e = (h + h) + d -> ell = S e -> ({_le('ell','S h + S h',tag='half_successor_result')})",
            ("euclidean_log_double_successor", "le_succ_self", "le_refl"),
            (*_intro("e", "h", "d", "ell", "hd", "he", "hl"), "have hdouble : S h + S h = S (S (h + h))", *_call("euclidean_log_double_successor", "h"),
             "rewrite hl", "rewrite he", "rewrite hdouble", "cases hd", "rewrite hd_left", "have hz : (h + h) + 0 = h + h", "apply PA3", "rewrite hz", *_call("le_succ_self", "(S (h + h))"),
             "rewrite hd_right", "have hone : S ((h + h) + 1) = S (S (h + h))", "simp", "rewrite hone", *_call("le_refl", "(S (S (h + h)))")),
            "The successor of a binary-split exponent is at most twice the successor of its half.",
        ),
        spec(
            "double_successor_le_triple_above_one",
            f"forall h. ({_le('2','h',tag='triple_input')}) -> ({_le('S h + S h','3 * h',tag='triple_result')})",
            ("euclidean_log_double_successor", "add_le_add_left", "mul_comm", "zero_add", "add_assoc"),
            (*_intro("h", "hh"), "have hdouble : S h + S h = (h + h) + 2", "trans S (S (h + h))", *_call("euclidean_log_double_successor", "h"), "symm", "simp",
             "have htriple : 3 * h = (h + h) + h", "trans h * 3", "apply mul_comm", "simp [zero_add, add_assoc]", "rewrite hdouble", "rewrite htriple", *_call("add_le_add_left", "2", "h", "(h + h)"), "exact hh"),
            "For h at least two, twice its successor is at most three times h.",
        ),
        spec(
            "binary_length_positive",
            f"forall n ell. ({_length('n','ell',tag='length_positive_source')}) -> ({_le('1','ell',tag='length_positive_result')})",
            ("le_refl",),
            (*_intro("n", "ell", "h"), "cases h", "cases h_left", "rewrite h_left_right", *_call("le_refl", "1"),
             "cases h_right", "cases h_right_witness", "cases h_right_witness_witness", "cases h_right_witness_witness_witness", "rewrite h_right_witness_witness_witness_left", "exists x", "simp"),
            "The established binary-length convention always has positive length, including zero input.",
        ),
        spec(
            "binary_length_nonzero_components",
            f"forall n ell. ~(n = 0) -> ({_length('n','ell',tag='length_components_source')}) -> exists e v w. "
            f"ell = S e /\\ (({_pow('2','e','v',tag='length_components_lower_power')}) /\\ (({_pow('2','ell','w',tag='length_components_upper_power')}) /\\ "
            f"(({_le('v','n',tag='length_components_lower')}) /\\ ({_lt('n','w',tag='length_components_upper')}))))",
            (),
            (*_intro("n", "ell", "hn", "h"), "cases h", "cases h_left", "exfalso", "apply hn", "exact h_left_left",
             "cases h_right", "cases h_right_witness", "cases h_right_witness_witness", "cases h_right_witness_witness_witness",
             "cases h_right_witness_witness_witness_right", "cases h_right_witness_witness_witness_right_right", "cases h_right_witness_witness_witness_right_right_right",
             "exists x", "exists x1", "exists x2", "split", "exact h_right_witness_witness_witness_left", "split", "exact h_right_witness_witness_witness_right_right_left", "split",
             "exact h_right_witness_witness_witness_right_right_right_left", "exact h_right_witness_witness_witness_right_right_right_right"),
            "Expose the actual lower and upper binary powers for a nonzero input without changing the BitLen definition.",
        ),
        spec(
            "binary_half_scale_bounds",
            f"forall N ell e h d U V. ell = S e -> e = (h + h) + d -> (d = 0 \\/ d = 1) -> ({_le('5','ell',tag='half_scale_length')}) -> "
            f"({_pow('2','h','U',tag='half_scale_power')}) -> ({_pow('2','e','V',tag='half_scale_lower_power')}) -> ({_le('V','N',tag='half_scale_lower')}) -> "
            f"({_le('2','h',tag='half_scale_half_positive')}) /\\ (({_le('U * U','N',tag='half_scale_square')}) /\\ (({_le('ell','2 * U',tag='half_scale_twice')}) /\\ ({_le('ell','3 * h',tag='half_scale_thrice')})))",
            ("le_of_succ_le_succ", "binary_split_half_lower_bound", "pow_exists", "pow_add", "binary_power_two_exponent_monotone", "le_add_right",
             "le_trans", "binary_split_successor_le_double_successor", "binary_power_two_dominates_successor", "euclidean_log_double_monotone", "pairing_double_equals_two_mul", "double_successor_le_triple_above_one"),
            (*_intro("N", "ell", "e", "h", "d", "U", "V", "hl", "he", "hd", "hell", "hU", "hV", "hVN"),
             "have he4 : exists g. g + 4 = e", *_call("le_of_succ_le_succ", "4", "e"), "rewrite <- hl", "exact hell",
             "have hh2 : exists g. g + 2 = h", *_call("binary_split_half_lower_bound", "e", "h", "d", "2"), "exact hd", "exact he",
             "have hfour : 2 + 2 = 4", "norm_num", "rewrite hfour", "exact he4",
             f"have hW : exists W. {_pow('2','h + h','W',tag='half_scale_square_power')}", *_call("pow_exists", "2", "(h + h)"), "cases hW",
             "have hsquare : x = U * U", *_call("pow_add", "2", "h", "h", "(h + h)", "U", "U", "x"), "refl", "exact hU", "exact hU", "exact hW_witness",
             "have hUV : exists g. g + x = V", *_call("binary_power_two_exponent_monotone", "(h + h)", "e", "x", "V"), "rewrite he", *_call("le_add_right", "(h + h)", "d"), "exact hW_witness", "exact hV",
             "have hsquareN : exists g. g + U * U = N", "rewrite <- hsquare", *_call("le_trans", "x", "V", "N"), "exact hUV", "exact hVN",
             "have hlengthhalf : exists g. g + ell = S h + S h", *_call("binary_split_successor_le_double_successor", "e", "h", "d", "ell"), "exact hd", "exact he", "exact hl",
             "have hhalfpower : exists g. g + S h = U", *_call("binary_power_two_dominates_successor", "h", "U"), "exact hU",
             "have hlengthpower : exists g. g + ell = U + U", *_call("le_trans", "ell", "(S h + S h)", "(U + U)"), "exact hlengthhalf", *_call("euclidean_log_double_monotone", "(S h)", "U"), "exact hhalfpower",
             "split", "exact hh2", "split", "exact hsquareN", "split", "have hdouble : U + U = 2 * U", *_call("pairing_double_equals_two_mul", "U"), "rewrite hdouble at hlengthpower", "exact hlengthpower",
             *_call("le_trans", "ell", "(S h + S h)", "(3 * h)"), "exact hlengthhalf", *_call("double_successor_le_triple_above_one", "h"), "exact hh2"),
            "The power-of-two threshold at half the lower exponent has square at most N, while ell is at most both 2U and 3h.",
        ),
    )


def _upper_bound_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "pow_four_equals_binary_double",
            f"forall n P Q. ({_pow('4','n','P',tag='four_double_four')}) -> ({_pow('2','n + n','Q',tag='four_double_two')}) -> P = Q",
            ("pow_exists", "pow_four_is_square_of_pow_two", "pow_add"),
            (*_intro("n", "P", "Q", "hP", "hQ"), f"have hp : exists v. {_pow('2','n','v',tag='four_double_middle')}", *_call("pow_exists", "2", "n"), "cases hp",
             "trans x * x", *_call("pow_four_is_square_of_pow_two", "n", "x", "P"), "exact hp_witness", "exact hP", "symm",
             *_call("pow_add", "2", "n", "n", "(n + n)", "x", "x", "Q"), "refl", "exact hp_witness", "exact hp_witness", "exact hQ"),
            "Actual 4^n equals actual 2^(n+n), using only constructed powers and their checked product laws.",
        ),
        spec(
            "prime_cutoff_exponent_bound",
            f"forall N h U b c d f L. ({_pow('2','h','U',tag='cut_exp_power')}) -> ({_mask('b','c','N',tag='cut_exp_mask')}) -> "
            f"({_cutoff('U','b','c','d','f','N',tag='cut_exp_cutoff')}) -> ({_sum('d','f','N','L',tag='cut_exp_count')}) -> ({_le('h * L','N + N',tag='cut_exp_result')})",
            ("primorial_exists", "pow_exists", "pow_mul_exp", "pow_four_equals_binary_double", "primorial_cutoff_count_power_bound", "primorial_le_four_pow", "le_trans", "binary_power_two_order_reflects_exponent"),
            (*_intro("N", "h", "U", "b", "c", "d", "f", "L", "hU", "hm", "hc", "hL"),
             f"have hP : exists P. {_primorial('N','P',tag='cut_exp_primorial')}", *_call("primorial_exists", "N"), "cases hP",
             f"have hQ : exists Q. {_pow('U','L','Q',tag='cut_exp_outer_power')}", *_call("pow_exists", "U", "L"), "cases hQ",
             f"have hT : exists T. {_pow('2','h * L','T',tag='cut_exp_flat_power')}", *_call("pow_exists", "2", "(h * L)"), "cases hT",
             f"have hR : exists R. {_pow('4','N','R',tag='cut_exp_four_power')}", *_call("pow_exists", "4", "N"), "cases hR",
             f"have hW : exists W. {_pow('2','N + N','W',tag='cut_exp_double_power')}", *_call("pow_exists", "2", "(N + N)"), "cases hW",
             "have hflat : x1 = x2", *_call("pow_mul_exp", "2", "h", "L", "(h * L)", "U", "x1", "x2"), "refl", "exact hU", "exact hQ_witness", "exact hT_witness",
             "have hdouble : x3 = x4", *_call("pow_four_equals_binary_double", "N", "x3", "x4"), "exact hR_witness", "exact hW_witness",
             "have hbound : exists g. g + x1 = x3", *_call("le_trans", "x1", "x", "x3"),
             *_call("primorial_cutoff_count_power_bound", "N", "U", "b", "c", "d", "f", "L", "x", "x1"), "exact hm", "exact hc", "exact hL", "exact hP_witness", "exact hQ_witness",
             *_call("primorial_le_four_pow", "N", "x", "x3"), "exact hP_witness", "exact hR_witness",
             "rewrite hflat at hbound", "rewrite hdouble at hbound", *_call("binary_power_two_order_reflects_exponent", "(h * L)", "(N + N)", "x2", "x4"), "exact hT_witness", "exact hW_witness", "exact hbound"),
            "At a genuine binary-power cutoff U=2^h, h times the actual upper prime count is at most 2N.",
        ),
        spec(
            "chebyshev_upper_arithmetic",
            f"forall N ell k h U L. ({_le('k','U + L',tag='upper_arith_count')}) -> ({_le('U * U','N',tag='upper_arith_square')}) -> "
            f"({_le('ell','2 * U',tag='upper_arith_small')}) -> ({_le('ell','3 * h',tag='upper_arith_large')}) -> ({_le('h * L','N + N',tag='upper_arith_exponent')}) -> ({_le('k * ell','8 * N',tag='upper_arith_result')})",
            ("mul_le_mul_left", "mul_le_mul_right", "le_trans", "mul_assoc", "mul_comm", "mul_add", "add_mul", "add_le_add_right", "add_le_add_left"),
            (*_intro("N", "ell", "k", "h", "U", "L", "hk", "hsq", "hs", "hl", "he"),
             "have hsmall0 : exists g. g + U * ell = U * (2 * U)", *_call("mul_le_mul_left", "ell", "(2 * U)", "U"), "exact hs",
             "have hsmall1 : U * (2 * U) = 2 * (U * U)", "trans (2 * U) * U", "apply mul_comm", "apply mul_assoc", "rewrite hsmall1 at hsmall0",
             "have hsmall : exists g. g + U * ell = 2 * N", *_call("le_trans", "(U * ell)", "(2 * (U * U))", "(2 * N)"), "exact hsmall0", *_call("mul_le_mul_left", "(U * U)", "N", "2"), "exact hsq",
             "have hlarge0 : exists g. g + L * ell = L * (3 * h)", *_call("mul_le_mul_left", "ell", "(3 * h)", "L"), "exact hl",
             "have hlarge1 : L * (3 * h) = 3 * (h * L)", "trans (3 * h) * L", "apply mul_comm", "apply mul_assoc", "rewrite hlarge1 at hlarge0",
             "have hlarge2 : exists g. g + L * ell = 3 * (N + N)", *_call("le_trans", "(L * ell)", "(3 * (h * L))", "(3 * (N + N))"), "exact hlarge0", *_call("mul_le_mul_left", "(h * L)", "(N + N)", "3"), "exact he",
             "have hsix : 3 * (N + N) = 6 * N", "trans 3 * N + 3 * N", "apply mul_add", "symm", "have hsixnum : 6 = 3 + 3", "norm_num", "rewrite hsixnum", "apply add_mul", "rewrite hsix at hlarge2",
             "have hsum0 : exists g. g + (U * ell + L * ell) = 2 * N + L * ell", *_call("add_le_add_right", "(U * ell)", "(2 * N)", "(L * ell)"), "exact hsmall",
             "have hsum : exists g. g + (U * ell + L * ell) = 2 * N + 6 * N", *_call("le_trans", "(U * ell + L * ell)", "(2 * N + L * ell)", "(2 * N + 6 * N)"), "exact hsum0", *_call("add_le_add_left", "(L * ell)", "(6 * N)", "(2 * N)"), "exact hlarge2",
             "have hproduct : (U + L) * ell = U * ell + L * ell", "apply add_mul", "rewrite <- hproduct at hsum",
             "have height : 2 * N + 6 * N = 8 * N", "symm", "have heightnum : 8 = 2 + 6", "norm_num", "rewrite heightnum", "apply add_mul", "rewrite height at hsum",
             *_call("le_trans", "(k * ell)", "((U + L) * ell)", "(8 * N)"), *_call("mul_le_mul_right", "k", "(U + L)", "ell"), "exact hk", "exact hsum"),
            "The exact small-prime 2N and large-prime 6N budgets combine to the required 8N bound.",
        ),
        spec(
            "prime_count_chebyshev_upper",
            f"forall N ell k. ({_le('2','N',tag='cheb_upper_positive')}) -> ({_length('N','ell',tag='cheb_upper_length')}) -> ({_count('N','k',tag='cheb_upper_count')}) -> ({_le('k * ell','8 * N',tag='cheb_upper_result')})",
            ("le_or_lt", "prime_count_bounded", "mul_le_mul", "mul_le_mul_left", "mul_comm", "le_trans", "binary_length_nonzero_components", "le_zero",
             "binary_exponent_split_exists", "pow_exists", "binary_half_scale_bounds", "beta_cutoff_prefix_exists", "beta_sum_exists", "beta_cutoff_count_comparison",
             "prime_bit_prefix_all_bits", "prime_cutoff_exponent_bound", "chebyshev_upper_arithmetic"),
            (*_intro("N", "ell", "k", "hN", "hl", "hk"), "have hc : (exists g. g + ell = 4) \\/ (exists g. g + S 4 = ell)", *_call("le_or_lt", "ell", "4"), "cases hc",
             "have hsmall : exists g. g + k * ell = N * 4", *_call("mul_le_mul", "k", "N", "ell", "4"), *_call("prime_count_bounded", "N", "k"), "exact hk", "exact hc_left",
             "have hscale : exists g. g + N * 4 = N * 8", *_call("mul_le_mul_left", "4", "8", "N"), "exists 4", "norm_num",
             "have hswap : N * 8 = 8 * N", "apply mul_comm", "rewrite hswap at hscale", *_call("le_trans", "(k * ell)", "(N * 4)", "(8 * N)"), "exact hsmall", "exact hscale",
             f"have hdata : exists e v w. ell = S e /\\ (({_pow('2','e','v',tag='cheb_upper_lower_power')}) /\\ (({_pow('2','ell','w',tag='cheb_upper_upper_power')}) /\\ (({_le('v','N',tag='cheb_upper_lower_value')}) /\\ ({_lt('N','w',tag='cheb_upper_upper_value')}))))",
             *_call("binary_length_nonzero_components", "N", "ell"), "intro hz", "have hbad : exists g. g + 2 = 0", "rewrite hz at hN", "exact hN", "apply PA1", *_call("le_zero", "2"), "exact hbad", "exact hl",
             "cases hdata", "cases hdata_witness", "cases hdata_witness_witness", "cases hdata_witness_witness_witness", "cases hdata_witness_witness_witness_right", "cases hdata_witness_witness_witness_right_right", "cases hdata_witness_witness_witness_right_right_right",
             "have hsplit : exists h d. (d = 0 \\/ d = 1) /\\ x = (h + h) + d", *_call("binary_exponent_split_exists", "x"), "cases hsplit", "cases hsplit_witness", "cases hsplit_witness_witness",
             f"have hU : exists U. {_pow('2','x3','U',tag='cheb_upper_threshold')}", *_call("pow_exists", "2", "x3"), "cases hU",
             "have hscale : (exists g. g + 2 = x3) /\\ ((exists g. g + x5 * x5 = N) /\\ ((exists g. g + ell = 2 * x5) /\\ (exists g. g + ell = 3 * x3)))",
             *_call("binary_half_scale_bounds", "N", "ell", "x", "x3", "x4", "x5", "x1"), "exact hdata_witness_witness_witness_left", "exact hsplit_witness_witness_right", "exact hsplit_witness_witness_left", "exact hc_right", "exact hU_witness", "exact hdata_witness_witness_witness_right_left", "exact hdata_witness_witness_witness_right_right_right_left",
             "cases hscale", "cases hscale_right", "cases hscale_right_right", "cases hk", "cases hk_witness", "cases hk_witness_witness",
             f"have hcut : exists d f. {_cutoff('x5','x6','x7','d','f','N',tag='cheb_upper_cutoff')}", *_call("beta_cutoff_prefix_exists", "x5", "x6", "x7", "N"), "cases hcut", "cases hcut_witness",
             f"have hsum : exists L. {_sum('x8','x9','N','L',tag='cheb_upper_tail_count')}", *_call("beta_sum_exists", "x8", "x9", "N"), "cases hsum",
             *_call("chebyshev_upper_arithmetic", "N", "ell", "k", "x3", "x5", "x10"),
             *_call("beta_cutoff_count_comparison", "x5", "x6", "x7", "x8", "x9", "N", "k", "x10"), *_call("prime_bit_prefix_all_bits", "x6", "x7", "N"), "exact hk_witness_witness_left", "exact hcut_witness_witness", "exact hk_witness_witness_right", "exact hsum_witness",
             "exact hscale_right_left", "exact hscale_right_right_left", "exact hscale_right_right_right",
             *_call("prime_cutoff_exponent_bound", "N", "x3", "x5", "x6", "x7", "x8", "x9", "x10"), "exact hU_witness", "exact hk_witness_witness_left", "exact hcut_witness_witness", "exact hsum_witness"),
            "The exact effective Chebyshev upper bound pi(N)*BitLen(N) <= 8N, including every N at least two.",
        ),
    )


def _lower_bound_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "binary_split_upper_bound",
            f"forall N h d. (d = 0 \\/ d = 1) -> N = (h + h) + d -> ({_le('N','S (h + h)',tag='split_upper_result')})",
            ("le_succ_self", "le_refl"),
            (*_intro("N", "h", "d", "hd", "he"), "rewrite he", "cases hd", "rewrite hd_left", "have hz : (h + h) + 0 = h + h", "apply PA3", "rewrite hz", *_call("le_succ_self", "(h + h)"),
             "rewrite hd_right", "have hone : (h + h) + 1 = S (h + h)", "simp", "rewrite hone", *_call("le_refl", "(S (h + h))")),
            "An actual binary-split integer is at most twice its half plus one.",
        ),
        spec(
            "double_successor_le_triple_of_positive",
            f"forall A. ({_le('1','A',tag='positive_triple_input')}) -> ({_le('S (A + A)','3 * A',tag='positive_triple_result')})",
            ("mul_comm", "zero_add", "add_assoc", "add_le_add_left"),
            (*_intro("A", "hA"), "have htriple : 3 * A = (A + A) + A", "trans A * 3", "apply mul_comm", "simp [zero_add, add_assoc]",
             "have hone : (A + A) + 1 = S (A + A)", "simp", "rewrite <- hone", "rewrite htriple", *_call("add_le_add_left", "1", "A", "(A + A)"), "exact hA"),
            "For positive A, twice A plus one is at most three times A.",
        ),
        spec(
            "binary_split_eight_bound",
            f"forall N h d A. (d = 0 \\/ d = 1) -> N = (h + h) + d -> ({_le('h','A',tag='split_eight_half')}) -> ({_le('1','A',tag='split_eight_positive')}) -> ({_le('N','8 * A',tag='split_eight_result')})",
            ("binary_split_upper_bound", "euclidean_log_double_monotone", "succ_le_succ", "double_successor_le_triple_of_positive", "mul_le_mul_right", "le_trans"),
            (*_intro("N", "h", "d", "A", "hd", "hN", "hh", "hA"), "have hfirst : exists g. g + N = S (A + A)", *_call("le_trans", "N", "(S (h + h))", "(S (A + A))"),
             *_call("binary_split_upper_bound", "N", "h", "d"), "exact hd", "exact hN", *_call("succ_le_succ", "(h + h)", "(A + A)"), *_call("euclidean_log_double_monotone", "h", "A"), "exact hh",
             "have hsecond : exists g. g + N = 3 * A", *_call("le_trans", "N", "(S (A + A))", "(3 * A)"), "exact hfirst", *_call("double_successor_le_triple_of_positive", "A"), "exact hA",
             *_call("le_trans", "N", "(3 * A)", "(8 * A)"), "exact hsecond", *_call("mul_le_mul_right", "3", "8", "A"), "exists 5", "norm_num"),
            "An actual binary split whose half is bounded by a positive A is bounded by 8A.",
        ),
        spec(
            "central_binom_prime_count_exponent_bound",
            f"forall N ell k h. ({_le('4','h',tag='central_exp_half_positive')}) -> ({_le('h + h','N',tag='central_exp_range')}) -> "
            f"({_length('N','ell',tag='central_exp_length')}) -> ({_count('N','k',tag='central_exp_count')}) -> ({_le('h','ell * k',tag='central_exp_result')})",
            ("central_binom_exists", "pow_exists", "binary_length_upper_power_bound", "central_binom_prime_count_power_bound", "central_binom_dominates_pow_two", "le_trans", "lt_to_le", "pow_base_monotone", "pow_mul_exp", "binary_power_two_order_reflects_exponent"),
            (*_intro("N", "ell", "k", "h", "hh", "hN", "hl", "hk"),
             f"have hC : exists C. {_central('h','C',tag='central_exp_central')}", *_call("central_binom_exists", "h"), "cases hC",
             f"have hV : exists V. {_pow('2','h','V',tag='central_exp_half_power')}", *_call("pow_exists", "2", "h"), "cases hV",
             f"have hW : exists W. ({_pow('2','ell','W',tag='central_exp_upper_power')}) /\\ ({_lt('N','W',tag='central_exp_upper_bound')})", *_call("binary_length_upper_power_bound", "N", "ell"), "exact hl", "cases hW", "cases hW_witness",
             f"have hQ : exists Q. {_pow('h + h','k','Q',tag='central_exp_factor_power')}", *_call("pow_exists", "(h + h)", "k"), "cases hQ",
             f"have hR : exists R. {_pow('x2','k','R',tag='central_exp_outer_power')}", *_call("pow_exists", "x2", "k"), "cases hR",
             f"have hT : exists T. {_pow('2','ell * k','T',tag='central_exp_flat_power')}", *_call("pow_exists", "2", "(ell * k)"), "cases hT",
             "have hCbound : exists g. g + x = x3", *_call("central_binom_prime_count_power_bound", "h", "N", "k", "x", "x3"),
             *_call("le_trans", "1", "4", "h"), "exists 3", "norm_num", "exact hh", "exact hN", "exact hk", "exact hC_witness", "exact hQ_witness",
             "have hVbound : exists g. g + x1 = x3", *_call("le_trans", "x1", "x", "x3"), *_call("central_binom_dominates_pow_two", "h", "x", "x1"), "exact hh", "exact hC_witness", "exact hV_witness", "exact hCbound",
             "have hbase : exists g. g + (h + h) = x2", *_call("le_trans", "(h + h)", "N", "x2"), "exact hN", *_call("lt_to_le", "N", "x2"), "exact hW_witness_right",
             "have hQbound : exists g. g + x3 = x4", *_call("pow_base_monotone", "(h + h)", "x2", "k", "x3", "x4"), "exact hbase", "exact hQ_witness", "exact hR_witness",
             "have hflat : x4 = x5", *_call("pow_mul_exp", "2", "ell", "k", "(ell * k)", "x2", "x4", "x5"), "refl", "exact hW_witness_left", "exact hR_witness", "exact hT_witness", "rewrite hflat at hQbound",
             *_call("binary_power_two_order_reflects_exponent", "h", "(ell * k)", "x1", "x5"), "exact hV_witness", "exact hT_witness", *_call("le_trans", "x1", "x3", "x5"), "exact hVbound", "exact hQbound"),
            "Central-binomial growth and actual prime contributions force floor(N/2) <= BitLen(N)*pi(N) whenever the half is at least four.",
        ),
        spec(
            "prime_count_chebyshev_lower_large",
            f"forall N ell k. ({_le('8','N',tag='cheb_large_input')}) -> ({_length('N','ell',tag='cheb_large_length')}) -> ({_count('N','k',tag='cheb_large_count')}) -> ({_le('N','8 * k * ell',tag='cheb_large_result')})",
            ("binary_exponent_split_exists", "binary_split_half_lower_bound", "le_add_right", "central_binom_prime_count_exponent_bound", "le_trans", "binary_split_eight_bound", "mul_comm", "mul_assoc"),
            (*_intro("N", "ell", "k", "hN", "hl", "hk"), "have hsplit : exists h d. (d = 0 \\/ d = 1) /\\ N = (h + h) + d", *_call("binary_exponent_split_exists", "N"), "cases hsplit", "cases hsplit_witness", "cases hsplit_witness_witness",
             "have hh : exists g. g + 4 = x", *_call("binary_split_half_lower_bound", "N", "x", "x1", "4"), "exact hsplit_witness_witness_left", "exact hsplit_witness_witness_right", "have height : 4 + 4 = 8", "norm_num", "rewrite height", "exact hN",
             "have hhalf : exists g. g + (x + x) = N", "rewrite hsplit_witness_witness_right", *_call("le_add_right", "(x + x)", "x1"),
             "have hexponent : exists g. g + x = ell * k", *_call("central_binom_prime_count_exponent_bound", "N", "ell", "k", "x"), "exact hh", "exact hhalf", "exact hl", "exact hk",
             "have hpositivehalf : exists g. g + 1 = x", *_call("le_trans", "1", "4", "x"), "exists 3", "norm_num", "exact hh",
             "have hpositive : exists g. g + 1 = ell * k", *_call("le_trans", "1", "x", "(ell * k)"), "exact hpositivehalf", "exact hexponent",
             "have hbound : exists g. g + N = 8 * (ell * k)", *_call("binary_split_eight_bound", "N", "x", "x1", "(ell * k)"), "exact hsplit_witness_witness_left", "exact hsplit_witness_witness_right", "exact hexponent", "exact hpositive",
             "have horder : 8 * (ell * k) = (8 * k) * ell", "have hswap : ell * k = k * ell", "apply mul_comm", "rewrite hswap", "symm", "apply mul_assoc", "rewrite horder at hbound", "exact hbound"),
            "The required lower prime-count bound for all N at least eight, using the actual binary half and central coefficient.",
        ),
        spec(
            "prime_count_chebyshev_lower",
            f"forall N ell k. ({_le('2','N',tag='cheb_lower_positive')}) -> ({_length('N','ell',tag='cheb_lower_length')}) -> ({_count('N','k',tag='cheb_lower_count')}) -> ({_le('N','8 * k * ell',tag='cheb_lower_result')})",
            ("le_or_lt", "prime_count_chebyshev_lower_large", "prime_count_positive_above_one", "binary_length_positive", "le_mul_of_one_le_right", "le_trans", "mul_le_mul_left", "mul_one", "mul_assoc", "lt_to_le"),
            (*_intro("N", "ell", "k", "hN", "hl", "hk"), "have hc : (exists g. g + 8 = N) \\/ (exists g. g + S N = 8)", *_call("le_or_lt", "8", "N"), "cases hc",
             *_call("prime_count_chebyshev_lower_large", "N", "ell", "k"), "exact hc_left", "exact hl", "exact hk",
             "have hpositive : exists g. g + 1 = k * ell", *_call("le_trans", "1", "k", "(k * ell)"), *_call("prime_count_positive_above_one", "N", "k"), "exact hN", "exact hk", *_call("le_mul_of_one_le_right", "k", "ell"), *_call("binary_length_positive", "N", "ell"), "exact hl",
             "have hscale : exists g. g + 8 * 1 = 8 * (k * ell)", *_call("mul_le_mul_left", "1", "(k * ell)", "8"), "exact hpositive", "have hone : 8 * 1 = 8", "apply mul_one", "rewrite hone at hscale",
             "have hassoc : (8 * k) * ell = 8 * (k * ell)", "apply mul_assoc", "rewrite hassoc", *_call("le_trans", "N", "8", "(8 * (k * ell))"), *_call("lt_to_le", "N", "8"), "exact hc_right", "exact hscale"),
            "The exact effective Chebyshev lower bound N <= 8*pi(N)*BitLen(N), including every N at least two.",
        ),
        spec(
            "prime_count_chebyshev_bounds",
            f"forall N ell k. ({_le('2','N',tag='cheb_full_positive')}) -> ({_length('N','ell',tag='cheb_full_length')}) -> ({_count('N','k',tag='cheb_full_count')}) -> "
            f"({_le('N','8 * k * ell',tag='cheb_full_lower')}) /\\ ({_le('k * ell','8 * N',tag='cheb_full_upper')})",
            ("prime_count_chebyshev_lower", "prime_count_chebyshev_upper"),
            (*_intro("N", "ell", "k", "hN", "hl", "hk"), "split", *_call("prime_count_chebyshev_lower", "N", "ell", "k"), "exact hN", "exact hl", "exact hk",
             *_call("prime_count_chebyshev_upper", "N", "ell", "k"), "exact hN", "exact hl", "exact hk"),
            "Exact G027: for every N at least two and its actual prime count and binary length, N <= 8*pi(N)*BitLen(N) and pi(N)*BitLen(N) <= 8N.",
        ),
    )


def _count_audit_rows(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "prime_bit_choice_functional",
            f"forall i e f. ({_choice('i','e',tag='choice_functional_left')}) -> ({_choice('i','f',tag='choice_functional_right')}) -> e = f",
            (),
            (*_intro("i", "e", "f", "he", "hf"), "cases he", "cases he_left", "cases hf", "cases hf_left", "trans 1", "exact he_left_right", "symm", "exact hf_left_right",
             "cases hf_right", "exfalso", "apply hf_right_left", "exact he_left_left",
             "cases he_right", "cases hf", "cases hf_left", "exfalso", "apply he_right_left", "exact hf_left_left",
             "cases hf_right", "trans 0", "exact he_right_right", "symm", "exact hf_right_right"),
            "The primality indicator is uniquely zero or one, without a classical principle.",
        ),
        spec(
            "prime_bit_prefix_equal_entry",
            f"forall b c d f l i e a. ({_mask('b','c','l',tag='mask_equal_left')}) -> ({_mask('d','f','l',tag='mask_equal_right')}) -> "
            f"({_lt('i','l',tag='mask_equal_bound')}) -> ({_at('b','c','i','e',tag='pc_mask_equal_e')}) -> ({_at('d','f','i','a',tag='pc_mask_equal_a')}) -> e = a",
            ("prime_bit_choice_functional", "prime_bit_prefix_entry"),
            (*_intro("b", "c", "d", "f", "l", "i", "e", "a", "hb", "hd", "hi", "he", "ha"), *_call("prime_bit_choice_functional", "i", "e", "a"),
             *_call("prime_bit_prefix_entry", "b", "c", "l", "i", "e"), "exact hb", "exact hi", "exact he",
             *_call("prime_bit_prefix_entry", "d", "f", "l", "i", "a"), "exact hd", "exact hi", "exact ha"),
            "Primality masks with different beta codes have equal entries at every actual shared index.",
        ),
        spec(
            "prime_count_functional",
            f"forall N k K. ({_count('N','k',tag='count_functional_left')}) -> ({_count('N','K',tag='count_functional_right')}) -> k = K",
            ("le_antisymm", "beta_sum_pointwise_le", "prime_bit_prefix_equal_entry", "le_refl"),
            (*_intro("N", "k", "K", "hk", "hK"), "cases hk", "cases hk_witness", "cases hk_witness_witness", "cases hK", "cases hK_witness", "cases hK_witness_witness",
             *_call("le_antisymm", "k", "K"), *_call("beta_sum_pointwise_le", "x", "x1", "x2", "x3", "N", "k", "K"),
             *_intro("i", "a", "z", "hi", "ha", "hz"), "have heq : a = z", *_call("prime_bit_prefix_equal_entry", "x", "x1", "x2", "x3", "N", "i", "a", "z"),
             "exact hk_witness_witness_left", "exact hK_witness_witness_left", "exact hi", "exact ha", "exact hz", "rewrite heq", *_call("le_refl", "z"), "exact hk_witness_witness_right", "exact hK_witness_witness_right",
             *_call("beta_sum_pointwise_le", "x2", "x3", "x", "x1", "N", "K", "k"), *_intro("i", "a", "z", "hi", "ha", "hz"), "have heq : a = z", *_call("prime_bit_prefix_equal_entry", "x2", "x3", "x", "x1", "N", "i", "a", "z"),
             "exact hK_witness_witness_left", "exact hk_witness_witness_left", "exact hi", "exact ha", "exact hz", "rewrite heq", *_call("le_refl", "z"), "exact hK_witness_witness_right", "exact hk_witness_witness_right"),
            "The exact prime count is independent of every mask and sum-trace encoding choice.",
        ),
        spec(
            "prime_count_zero",
            f"forall k. ({_count('0','k',tag='count_zero_source')}) -> k = 0",
            ("beta_sum_zero",),
            (*_intro("k", "h"), "cases h", "cases h_witness", "cases h_witness_witness", *_call("beta_sum_zero", "x", "x1", "k"), "exact h_witness_witness_right"),
            "The exact prime count at zero is zero.",
        ),
        spec(
            "prime_count_one",
            f"forall k. ({_count('1','k',tag='count_one_source')}) -> k = 0",
            ("beta_sum_succ_decompose", "prime_bit_prefix_entry", "le_refl", "beta_sum_zero"),
            (*_intro("k", "h"), "cases h", "cases h_witness", "cases h_witness_witness",
             f"have hd : exists a w. ({_at('x','x1','0','a',tag='pc_count_one_entry')}) /\\ (({_sum('x','x1','0','w',tag='count_one_previous')}) /\\ k = w + a)", *_call("beta_sum_succ_decompose", "x", "x1", "0", "k"), "exact h_witness_witness_right", "cases hd", "cases hd_witness", "cases hd_witness_witness", "cases hd_witness_witness_right",
             f"have hc : {_choice('0','x2',tag='count_one_choice')}", *_call("prime_bit_prefix_entry", "x", "x1", "1", "0", "x2"), "exact h_witness_witness_left", *_call("le_refl", "1"), "exact hd_witness_witness_left",
             "cases hc", "cases hc_left", "cases hc_left_left", "exfalso", "apply hc_left_left_left", "refl", "cases hc_right",
             "have hz : x3 = 0", *_call("beta_sum_zero", "x", "x1", "x3"), "exact hd_witness_witness_right_left", "rewrite hd_witness_witness_right_right", "rewrite hz", "rewrite hc_right_right", "norm_num"),
            "One contributes no prime: the exact prime count at one is zero.",
        ),
        spec(
            "prime_count_exists_unique",
            f"forall N. exists k. ({_count('N','k',tag='count_unique_value')}) /\\ forall K. ({_count('N','K',tag='count_unique_other')}) -> k = K",
            ("prime_count_exists", "prime_count_functional"),
            ("intro N", f"have h : exists k. {_count('N','k',tag='count_unique_actual')}", *_call("prime_count_exists", "N"), "cases h", "exists x", "split", "exact h_witness", *_intro("K", "hK"), *_call("prime_count_functional", "N", "x", "K"), "exact h_witness", "exact hK"),
            "Every bound has a genuinely constructed, uniquely determined exact prime count.",
        ),
    )


def make_prime_count_chebyshev_candidate_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    return (
        spec(
            "prime_bit_choice_exists",
            f"forall i. exists e. {_choice('i','e',tag='choice_exists')}",
            ("prime_decidable",),
            ("intro i", f"have hp : ({_prime('S i',tag='choice_decision')}) \\/ ~({_prime('S i',tag='choice_decision_other')})",
             *_call("prime_decidable", "(S i)"), "cases hp", "exists 1", "left", "split", "exact hp_left", "refl",
             "exists 0", "right", "split", "exact hp_right", "refl"),
            "Construct the zero/one primality indicator at each dense index.",
        ),
        spec(
            "prime_bit_prefix_empty",
            f"forall b c. {_mask('b','c','0',tag='mask_empty')}",
            ("lt_not_le", "zero_le"),
            (*_intro("b", "c", "i", "hi"), "exfalso", *_call("lt_not_le", "i", "0"), "exact hi", *_call("zero_le", "i")),
            "The empty primality bit prefix is valid.",
        ),
        spec(
            "prime_bit_prefix_drop_last",
            f"forall b c l. ({_mask('b','c','S l',tag='mask_drop_source')}) -> ({_mask('b','c','l',tag='mask_drop_target')})",
            ("le_succ",),
            (*_intro("b", "c", "l", "h", "i", "hi"), "specialize h i", "apply h", *_call("le_succ", "(S i)", "l"), "exact hi"),
            "A primality mask restricts to its preceding prefix.",
        ),
        spec(
            "prime_bit_prefix_entry",
            f"forall b c l i e. ({_mask('b','c','l',tag='mask_entry_source')}) -> ({_lt('i','l',tag='mask_entry_bound')}) -> "
            f"({_at('b','c','i','e',tag='pc_mask_entry_given')}) -> ({_choice('i','e',tag='mask_entry_choice')})",
            ("beta_at_unique",),
            (*_intro("b", "c", "l", "i", "e", "h", "hi", "he"),
             f"have hp : exists a. ({_at('b','c','i','a',tag='pc_mask_entry_actual')}) /\\ ({_choice('i','a',tag='mask_entry_actual_choice')})",
             "specialize h i", "apply h", "exact hi", "cases hp", "cases hp_witness",
             "have heq : x = e", *_call("beta_at_unique", "b", "c", "i", "x", "e"), "exact hp_witness_left", "exact he",
             "rewrite heq at hp_witness_right", "rewrite heq at hp_witness_right", "exact hp_witness_right"),
            "Every decoded mask entry has the exact primality indicator, independently of beta-code choice.",
        ),
        spec(
            "prime_bit_prefix_extend",
            f"forall b c l e. ({_mask('b','c','l',tag='mask_extend_source')}) -> ({_choice('l','e',tag='mask_extend_choice')}) -> "
            f"exists d f. {_mask('d','f','S l',tag='mask_extend_target')}",
            ("beta_prefix_extend", "le_eq_or_lt", "le_of_succ_le_succ"),
            (*_intro("b", "c", "l", "e", "h", "he"),
             f"have hext : exists d f. ({_at('d','f','l','e',tag='pc_mask_extend_last')}) /\\ "
             f"forall i a. ({_lt('i','l',tag='mask_extend_bound')}) -> ({_at('b','c','i','a',tag='pc_mask_extend_old')}) -> ({_at('d','f','i','a',tag='pc_mask_extend_new')})",
             *_call("beta_prefix_extend", "l", "b", "c", "e"), "cases hext", "cases hext_witness", "cases hext_witness_witness",
             "exists x", "exists x1", "intro i", "intro hi",
             "have hcases : i = l \\/ exists g. g + S i = l", *_call("le_eq_or_lt", "i", "l"),
             *_call("le_of_succ_le_succ", "i", "l"), "exact hi", "cases hcases",
             "exists e", "split", "rewrite hcases_left", "rewrite hcases_left", "exact hext_witness_witness_left",
             "rewrite hcases_left", "rewrite hcases_left", "rewrite hcases_left", "rewrite hcases_left", "exact he",
             f"have hp : exists a. ({_at('b','c','i','a',tag='pc_mask_extend_point')}) /\\ ({_choice('i','a',tag='mask_extend_point_choice')})",
             "specialize h i", "apply h", "exact hcases_right", "cases hp", "cases hp_witness", "exists x2", "split",
             "specialize hext_witness_witness_right i", "specialize hext_witness_witness_right x2", "apply hext_witness_witness_right",
             "exact hcases_right", "exact hp_witness_left", "exact hp_witness_right"),
            "Append a genuinely decided prime bit while preserving the entire existing prefix.",
        ),
        spec(
            "prime_bit_prefix_exists",
            f"forall l. exists b c. {_mask('b','c','l',tag='mask_exists')}",
            ("prime_bit_prefix_empty", "prime_bit_choice_exists", "prime_bit_prefix_extend"),
            ("induction l", "exists 0", "exists 0", *_call("prime_bit_prefix_empty", "0", "0"),
             f"have hpre : exists b c. {_mask('b','c','l',tag='mask_exists_pre')}", "apply IH", "cases hpre", "cases hpre_witness",
             f"have hc : exists e. {_choice('l','e',tag='mask_exists_choice')}", *_call("prime_bit_choice_exists", "l"), "cases hc",
             *_call("prime_bit_prefix_extend", "x", "x1", "l", "x2"), "exact hpre_witness_witness", "exact hc_witness"),
            "HA induction constructs the complete finite primality mask at every natural bound.",
        ),
        spec(
            "prime_bit_prefix_all_bits",
            f"forall b c l. ({_mask('b','c','l',tag='mask_bits_source')}) -> ({_bits('b','c','l',tag='mask_bits_target')})",
            (),
            (*_intro("b", "c", "l", "h", "i", "hi"),
             f"have hp : exists e. ({_at('b','c','i','e',tag='pc_mask_bits_entry')}) /\\ ({_choice('i','e',tag='mask_bits_choice')})",
             "specialize h i", "apply h", "exact hi", "cases hp", "cases hp_witness", "exists x", "split", "exact hp_witness_left",
             "cases hp_witness_right", "cases hp_witness_right_left", "right", "exact hp_witness_right_left_right",
             "cases hp_witness_right_right", "left", "exact hp_witness_right_right_right"),
            "A primality mask consists of actual zero/one entries.",
        ),
        spec(
            "prime_count_exists",
            f"forall n. exists k. {_count('n','k',tag='count_exists')}",
            ("prime_bit_prefix_exists", "beta_sum_exists"),
            ("intro n", f"have hm : exists b c. {_mask('b','c','n',tag='count_exists_mask')}", *_call("prime_bit_prefix_exists", "n"),
             "cases hm", "cases hm_witness", f"have hs : exists k. {_sum('x','x1','n','k',tag='count_exists_sum')}",
             *_call("beta_sum_exists", "x", "x1", "n"), "cases hs", "exists x2", "exists x", "exists x1", "split",
             "exact hm_witness_witness", "exact hs_witness"),
            "Construct the exact prime count for every bound, including zero and one.",
        ),
        spec(
            "prime_count_bounded",
            f"forall n k. ({_count('n','k',tag='count_bound_source')}) -> ({_le('k','n',tag='count_bound_result')})",
            ("bit_count_bounded", "prime_bit_prefix_all_bits"),
            (*_intro("n", "k", "h"), "cases h", "cases h_witness", "cases h_witness_witness",
             *_call("bit_count_bounded", "x", "x1", "n", "k"), "split", "exact h_witness_witness_right",
             *_call("prime_bit_prefix_all_bits", "x", "x1", "n"), "exact h_witness_witness_left"),
            "The exact prime count is at most the ambient finite interval length.",
        ),
        spec(
            "beta_sum_entry_le",
            f"forall b c l n i a. ({_sum('b','c','l','n',tag='entry_le_sum')}) -> ({_lt('i','l',tag='entry_le_index')}) -> "
            f"({_at('b','c','i','a',tag='pc_entry_le_value')}) -> ({_le('a','n',tag='entry_le_result')})",
            ("lt_not_le", "zero_le", "beta_sum_succ_decompose", "le_eq_or_lt", "le_of_succ_le_succ", "beta_at_unique", "le_add_left", "le_add_right", "le_trans"),
            (*_intro("b", "c"), "induction l", *_intro("n", "i", "a", "hs", "hi", "ha"), "exfalso",
             *_call("lt_not_le", "i", "0"), "exact hi", *_call("zero_le", "i"),
             *_intro("n", "i", "a", "hs", "hi", "ha"),
             f"have hd : exists v w. ({_at('b','c','l','v',tag='pc_entry_le_last')}) /\\ (({_sum('b','c','l','w',tag='entry_le_prefix')}) /\\ n = w + v)",
             *_call("beta_sum_succ_decompose", "b", "c", "l", "n"), "exact hs", "cases hd", "cases hd_witness", "cases hd_witness_witness", "cases hd_witness_witness_right",
             "have hc : i = l \\/ exists g. g + S i = l", *_call("le_eq_or_lt", "i", "l"), *_call("le_of_succ_le_succ", "i", "l"), "exact hi", "cases hc",
             "rewrite hc_left at ha", "rewrite hc_left at ha", "have heq : a = x", *_call("beta_at_unique", "b", "c", "l", "a", "x"), "exact ha", "exact hd_witness_witness_left",
             "rewrite heq", "rewrite hd_witness_witness_right_right", *_call("le_add_left", "x", "x1"),
             *_call("le_trans", "a", "x1", "n"), "specialize IH x1", "specialize IH i", "specialize IH a", "apply IH", "exact hd_witness_witness_right_left", "exact hc_right", "exact ha",
             "rewrite hd_witness_witness_right_right", *_call("le_add_right", "x1", "x")),
            "Every actual nonnegative summand is at most its actual finite sum.",
        ),
        spec(
            "prime_count_positive_above_one",
            f"forall n k. ({_le('2','n',tag='count_positive_bound')}) -> ({_count('n','k',tag='count_positive_source')}) -> ({_le('1','k',tag='count_positive_result')})",
            ("prime_two", "beta_at_exists", "prime_bit_prefix_entry", "beta_sum_entry_le"),
            (*_intro("n", "k", "hn", "h"), "cases h", "cases h_witness", "cases h_witness_witness",
             f"have he : exists e. {_at('x','x1','1','e',tag='pc_count_positive_entry')}", *_call("beta_at_exists", "x", "x1", "1"), "cases he",
             f"have hc : {_choice('1','x2',tag='count_positive_choice')}", *_call("prime_bit_prefix_entry", "x", "x1", "n", "1", "x2"), "exact h_witness_witness_left", "exact hn", "exact he_witness",
             "cases hc", "cases hc_left",
             "have hle : exists g. g + x2 = k", *_call("beta_sum_entry_le", "x", "x1", "n", "k", "1", "x2"), "exact h_witness_witness_right", "exact hn", "exact he_witness",
             "rewrite hc_left_right at hle", "exact hle", "cases hc_right", "exfalso", "apply hc_right_left", "exact prime_two"),
            "The actual prime two makes every prime count at bound at least two positive.",
        ),
    ) + _weighted_rows(spec) + _cutoff_rows(spec) + _power_rows(spec) + _prime_product_rows(spec) + _scale_rows(spec) + _upper_bound_rows(spec) + _lower_bound_rows(spec) + _count_audit_rows(spec)
