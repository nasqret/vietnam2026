"""Checked theorem data for β-coded finite sums.

This module remains an untrusted authoring layer: every relation below expands
to ordinary first-order Peano formulas, and every script must replay through
the independent kernel before admission.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import (
    BETA_SUM_EXISTS,
    BETA_SUM_FUNCTIONAL,
    sum_relation,
)


def _at(code: str, scale: str, index: str, value: str, *, tag: str) -> str:
    """Expand BetaAt for trusted internal term fragments."""

    h = f"fs_h_{tag}"
    q = f"fs_q_{tag}"
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists {h}. {h} + S ({value}) = {modulus}) /\\ "
        f"exists {q}. {code} = {q} * {modulus} + ({value}))"
    )


def _bound(index: str, length: str, *, tag: str) -> str:
    return f"exists fs_lt_{tag}. fs_lt_{tag} + S {index} = {length}"


def _sum_steps(
    code: str,
    scale: str,
    length: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    i = f"fs_i_{tag}"
    a = f"fs_a_{tag}"
    r = f"fs_r_{tag}"
    s = f"fs_s_{tag}"
    summand = _at(code, scale, i, a, tag=f"{tag}_summand")
    partial = _at(trace_code, trace_scale, i, r, tag=f"{tag}_partial")
    successor = _at(
        trace_code, trace_scale, f"S {i}", s, tag=f"{tag}_successor"
    )
    return (
        f"forall {i}. ({_bound(i, length, tag=f'{tag}_bound')}) -> "
        f"exists {a} {r} {s}. (({summand}) /\\ "
        f"(({partial}) /\\ (({successor}) /\\ {s} = {r} + {a})))"
    )


def _prefix_sum_trace(
    code: str, scale: str, length: str, *, tag: str
) -> str:
    u = f"fs_u_{tag}"
    v = f"fs_v_{tag}"
    start = _at(u, v, "0", "0", tag=f"{tag}_start")
    steps = _sum_steps(code, scale, length, u, v, tag=f"{tag}_steps")
    return f"exists {u} {v}. (({start}) /\\ {steps})"


def _sum_trace_body(
    code: str,
    scale: str,
    length: str,
    result: str,
    trace_code: str,
    trace_scale: str,
    *,
    tag: str,
) -> str:
    start = _at(trace_code, trace_scale, "0", "0", tag=f"{tag}_start")
    terminal = _at(
        trace_code, trace_scale, length, result, tag=f"{tag}_terminal"
    )
    steps = _sum_steps(
        code, scale, length, trace_code, trace_scale, tag=f"{tag}_steps"
    )
    return f"(({start}) /\\ (({terminal}) /\\ {steps}))"


def _sum_relation_terms(
    code: str, scale: str, length: str, result: str, *, tag: str
) -> str:
    u = f"fs_u_{tag}"
    v = f"fs_v_{tag}"
    body = _sum_trace_body(
        code, scale, length, result, u, v, tag=f"{tag}_body"
    )
    return f"exists {u} {v}. {body}"


def make_finite_sum_theorems(spec: Callable[..., Any]) -> tuple[Any, ...]:
    """Build the dependency-ordered Sum theorem tranche."""

    trace_statement = _prefix_sum_trace("b", "c", "l", tag="trace")
    induction_trace = _prefix_sum_trace("b", "c", "l", tag="induction")
    successor_sum = _sum_relation_terms("b", "c", "S l", "n", tag="succ")
    prefix_sum = sum_relation("b", "c", "l", "r", tag="prefix")
    successor_factor = _at("b", "c", "l", "a", tag="succ_factor")
    successor_decomposition = (
        f"exists a r. ({successor_factor}) /\\ "
        f"(({prefix_sum}) /\\ n = r + a)"
    )
    left_trace = _sum_trace_body(
        "b", "c", "l", "n", "u", "v", tag="functional_left"
    )
    right_trace = _sum_trace_body(
        "b", "c", "l", "m", "w", "d", tag="functional_right"
    )
    trace_functional = (
        f"forall b c l n u v m w d. ({left_trace}) -> "
        f"({right_trace}) -> n = m"
    )
    unique_sum = sum_relation("b", "c", "l", "n", tag="unique_value")
    competing_sum = sum_relation("b", "c", "l", "m", tag="unique_other")
    exists_unique = (
        f"forall b c l. exists n. (({unique_sum}) /\\ "
        f"forall m. ({competing_sum}) -> n = m)"
    )
    zero_sum = _sum_relation_terms("b", "c", "0", "n", tag="zero")

    return (
        spec(
            "beta_prefix_sum_trace_exists",
            f"forall b c l. {trace_statement}",
            (
                "beta_at_self_of_bound",
                "add_eq_zero_right",
                "succ_ne_zero",
                "beta_at_exists",
                "beta_prefix_extend",
                "zero_le",
                "succ_le_succ",
                "le_refl",
                "le_of_succ_le_succ",
                "le_eq_or_lt",
                "one_mul",
            ),
            (
                "intro b",
                "intro c",
                "induction l",
                "exists 0",
                "exists 1",
                "split",
                "specialize beta_at_self_of_bound 1",
                "specialize beta_at_self_of_bound 0",
                "specialize beta_at_self_of_bound 0",
                "apply beta_at_self_of_bound",
                "specialize one_mul 1",
                "rewrite one_mul",
                "specialize succ_le_succ 0",
                "specialize succ_le_succ (S 0)",
                "apply succ_le_succ",
                "specialize zero_le (S 0)",
                "exact zero_le",
                "intro i",
                "intro hi",
                "exfalso",
                "cases hi",
                "have hsi0 : S i = 0",
                "specialize add_eq_zero_right x",
                "specialize add_eq_zero_right (S i)",
                "apply add_eq_zero_right",
                "exact hi_witness",
                "specialize succ_ne_zero i",
                "apply succ_ne_zero",
                "exact hsi0",
                f"have htrace : {induction_trace}",
                "apply IH",
                "cases htrace",
                "cases htrace_witness",
                "cases htrace_witness_witness",
                f"have hfactor : exists p. {_at('b', 'c', 'l', 'p', tag='trace_factor')}",
                "specialize beta_at_exists b",
                "specialize beta_at_exists c",
                "specialize beta_at_exists l",
                "exact beta_at_exists",
                "cases hfactor",
                f"have hlast : exists r. {_at('x', 'x1', 'l', 'r', tag='trace_last')}",
                "specialize beta_at_exists x",
                "specialize beta_at_exists x1",
                "specialize beta_at_exists l",
                "exact beta_at_exists",
                "cases hlast",
                "have hext : exists z v. "
                f"(({_at('z', 'v', 'S l', 'x3 + x2', tag='trace_extension')}) /\\ "
                "forall i a. (exists h. h + S i = S l) -> "
                f"({_at('x', 'x1', 'i', 'a', tag='trace_old')}) -> "
                f"({_at('z', 'v', 'i', 'a', tag='trace_new')}))",
                "specialize beta_prefix_extend (S l)",
                "specialize beta_prefix_extend x",
                "specialize beta_prefix_extend x1",
                "specialize beta_prefix_extend (x3 + x2)",
                "exact beta_prefix_extend",
                "cases hext",
                "cases hext_witness",
                "cases hext_witness_witness",
                "exists x4",
                "exists x5",
                "split",
                "specialize hext_witness_witness_right 0",
                "specialize hext_witness_witness_right 0",
                "apply hext_witness_witness_right",
                "have h0 : exists h. h + S 0 = S l",
                "have hzero : exists h. h + 0 = l",
                "specialize zero_le l",
                "exact zero_le",
                "specialize succ_le_succ 0",
                "specialize succ_le_succ l",
                "apply succ_le_succ",
                "exact hzero",
                "exact h0",
                "exact htrace_witness_witness_left",
                "intro i",
                "intro hi",
                "have hil : exists h. h + i = l",
                "specialize le_of_succ_le_succ i",
                "specialize le_of_succ_le_succ l",
                "apply le_of_succ_le_succ",
                "exact hi",
                "have hsplit : i = l \\/ exists h. h + S i = l",
                "specialize le_eq_or_lt i",
                "specialize le_eq_or_lt l",
                "apply le_eq_or_lt",
                "exact hil",
                "cases hsplit",
                "exists x2",
                "exists x3",
                "exists x3 + x2",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hfactor_witness",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "specialize hext_witness_witness_right l",
                "specialize hext_witness_witness_right x3",
                "apply hext_witness_witness_right",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hlast_witness",
                "split",
                "rewrite hsplit_left",
                "rewrite hsplit_left",
                "exact hext_witness_witness_left",
                "refl",
                "have hold : exists p r s. "
                f"(({_at('b', 'c', 'i', 'p', tag='trace_hold_factor')}) /\\ "
                f"(({_at('x', 'x1', 'i', 'r', tag='trace_hold_partial')}) /\\ "
                f"(({_at('x', 'x1', 'S i', 's', tag='trace_hold_successor')}) /\\ "
                "s = r + p)))",
                "specialize htrace_witness_witness_right i",
                "apply htrace_witness_witness_right",
                "exact hsplit_right",
                "cases hold",
                "cases hold_witness",
                "cases hold_witness_witness",
                "cases hold_witness_witness_witness",
                "cases hold_witness_witness_witness_right",
                "cases hold_witness_witness_witness_right_right",
                "exists x6",
                "exists x7",
                "exists x8",
                "split",
                "exact hold_witness_witness_witness_left",
                "split",
                "specialize hext_witness_witness_right i",
                "specialize hext_witness_witness_right x7",
                "apply hext_witness_witness_right",
                "exact hi",
                "exact hold_witness_witness_witness_right_left",
                "split",
                "specialize hext_witness_witness_right (S i)",
                "specialize hext_witness_witness_right x8",
                "apply hext_witness_witness_right",
                "specialize succ_le_succ (S i)",
                "specialize succ_le_succ l",
                "apply succ_le_succ",
                "exact hsplit_right",
                "exact hold_witness_witness_witness_right_right_left",
                "exact hold_witness_witness_witness_right_right_right",
            ),
            "Every decoded beta prefix admits an exact beta-coded prefix-sum trace.",
        ),
        spec(
            "beta_sum_exists",
            BETA_SUM_EXISTS,
            ("beta_prefix_sum_trace_exists", "beta_at_exists"),
            (
                "intro b",
                "intro c",
                "intro l",
                f"have htrace : {_prefix_sum_trace('b', 'c', 'l', tag='exists_trace')}",
                "specialize beta_prefix_sum_trace_exists b",
                "specialize beta_prefix_sum_trace_exists c",
                "specialize beta_prefix_sum_trace_exists l",
                "exact beta_prefix_sum_trace_exists",
                "cases htrace",
                "cases htrace_witness",
                "cases htrace_witness_witness",
                f"have hterminal : exists n. {_at('x', 'x1', 'l', 'n', tag='sum_terminal')}",
                "specialize beta_at_exists x",
                "specialize beta_at_exists x1",
                "specialize beta_at_exists l",
                "exact beta_at_exists",
                "cases hterminal",
                "exists x2",
                "exists x",
                "exists x1",
                "split",
                "exact htrace_witness_witness_left",
                "split",
                "exact hterminal_witness",
                "exact htrace_witness_witness_right",
            ),
            "Every decoded beta prefix has a relational finite sum.",
        ),
        spec(
            "beta_sum_trace_functional",
            trace_functional,
            ("beta_at_unique", "le_refl", "le_succ", "add_congr"),
            (
                "intro b",
                "intro c",
                "induction l",
                "intro n",
                "intro u",
                "intro v",
                "intro m",
                "intro w",
                "intro d",
                "intro h1",
                "intro h2",
                "cases h1",
                "cases h1_right",
                "cases h2",
                "cases h2_right",
                "have hn : n = 0",
                "specialize beta_at_unique u",
                "specialize beta_at_unique v",
                "specialize beta_at_unique 0",
                "specialize beta_at_unique n",
                "specialize beta_at_unique 0",
                "apply beta_at_unique",
                "exact h1_right_left",
                "exact h1_left",
                "have hm : m = 0",
                "specialize beta_at_unique w",
                "specialize beta_at_unique d",
                "specialize beta_at_unique 0",
                "specialize beta_at_unique m",
                "specialize beta_at_unique 0",
                "apply beta_at_unique",
                "exact h2_right_left",
                "exact h2_left",
                "trans 0",
                "exact hn",
                "symm",
                "exact hm",
                "intro n",
                "intro u",
                "intro v",
                "intro m",
                "intro w",
                "intro d",
                "intro h1",
                "intro h2",
                "cases h1",
                "cases h1_right",
                "cases h2",
                "cases h2_right",
                "have hstep1 : exists a r s. "
                f"(({_at('b', 'c', 'l', 'a', tag='functional_step1_factor')}) /\\ "
                f"(({_at('u', 'v', 'l', 'r', tag='functional_step1_partial')}) /\\ "
                f"(({_at('u', 'v', 'S l', 's', tag='functional_step1_successor')}) /\\ "
                "s = r + a)))",
                "specialize h1_right_right l",
                "apply h1_right_right",
                "specialize le_refl (S l)",
                "exact le_refl",
                "cases hstep1",
                "cases hstep1_witness",
                "cases hstep1_witness_witness",
                "cases hstep1_witness_witness_witness",
                "cases hstep1_witness_witness_witness_right",
                "cases hstep1_witness_witness_witness_right_right",
                "have hstep2 : exists a r s. "
                f"(({_at('b', 'c', 'l', 'a', tag='functional_step2_factor')}) /\\ "
                f"(({_at('w', 'd', 'l', 'r', tag='functional_step2_partial')}) /\\ "
                f"(({_at('w', 'd', 'S l', 's', tag='functional_step2_successor')}) /\\ "
                "s = r + a)))",
                "specialize h2_right_right l",
                "apply h2_right_right",
                "specialize le_refl (S l)",
                "exact le_refl",
                "cases hstep2",
                "cases hstep2_witness",
                "cases hstep2_witness_witness",
                "cases hstep2_witness_witness_witness",
                "cases hstep2_witness_witness_witness_right",
                "cases hstep2_witness_witness_witness_right_right",
                "have hn : n = x2",
                "specialize beta_at_unique u",
                "specialize beta_at_unique v",
                "specialize beta_at_unique (S l)",
                "specialize beta_at_unique n",
                "specialize beta_at_unique x2",
                "apply beta_at_unique",
                "exact h1_right_left",
                "exact hstep1_witness_witness_witness_right_right_left",
                "have hm : m = x5",
                "specialize beta_at_unique w",
                "specialize beta_at_unique d",
                "specialize beta_at_unique (S l)",
                "specialize beta_at_unique m",
                "specialize beta_at_unique x5",
                "apply beta_at_unique",
                "exact h2_right_left",
                "exact hstep2_witness_witness_witness_right_right_left",
                "have ha : x = x3",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique l",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x3",
                "apply beta_at_unique",
                "exact hstep1_witness_witness_witness_left",
                "exact hstep2_witness_witness_witness_left",
                "have hsum1 : "
                f"{_sum_trace_body('b', 'c', 'l', 'x1', 'u', 'v', tag='functional_prefix1')}",
                "split",
                "exact h1_left",
                "split",
                "exact hstep1_witness_witness_witness_right_left",
                "intro i",
                "intro hi",
                "specialize h1_right_right i",
                "apply h1_right_right",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "have hsum2 : "
                f"{_sum_trace_body('b', 'c', 'l', 'x4', 'w', 'd', tag='functional_prefix2')}",
                "split",
                "exact h2_left",
                "split",
                "exact hstep2_witness_witness_witness_right_left",
                "intro i",
                "intro hi",
                "specialize h2_right_right i",
                "apply h2_right_right",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "have hprev : x1 = x4",
                "specialize IH x1",
                "specialize IH u",
                "specialize IH v",
                "specialize IH x4",
                "specialize IH w",
                "specialize IH d",
                "apply IH",
                "exact hsum1",
                "exact hsum2",
                "have hadd : x1 + x = x4 + x3",
                "specialize add_congr x1",
                "specialize add_congr x4",
                "specialize add_congr x",
                "specialize add_congr x3",
                "apply add_congr",
                "exact hprev",
                "exact ha",
                "trans x2",
                "exact hn",
                "trans x1 + x",
                "exact hstep1_witness_witness_witness_right_right_right",
                "trans x4 + x3",
                "exact hadd",
                "trans x5",
                "symm",
                "exact hstep2_witness_witness_witness_right_right_right",
                "symm",
                "exact hm",
            ),
            "Two exact prefix-sum traces over one decoded prefix have equal endpoints.",
        ),
        spec(
            "beta_sum_functional",
            BETA_SUM_FUNCTIONAL,
            ("beta_sum_trace_functional",),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro m",
                "intro hn",
                "intro hm",
                "cases hn",
                "cases hn_witness",
                "cases hm",
                "cases hm_witness",
                "specialize beta_sum_trace_functional b",
                "specialize beta_sum_trace_functional c",
                "specialize beta_sum_trace_functional l",
                "specialize beta_sum_trace_functional n",
                "specialize beta_sum_trace_functional x",
                "specialize beta_sum_trace_functional x1",
                "specialize beta_sum_trace_functional m",
                "specialize beta_sum_trace_functional x2",
                "specialize beta_sum_trace_functional x3",
                "apply beta_sum_trace_functional",
                "exact hn_witness_witness",
                "exact hm_witness_witness",
            ),
            "The relational finite sum has a unique natural value.",
        ),
        spec(
            "beta_sum_exists_unique",
            exists_unique,
            ("beta_sum_exists", "beta_sum_functional"),
            (
                "intro b",
                "intro c",
                "intro l",
                "specialize beta_sum_exists b",
                "specialize beta_sum_exists c",
                "specialize beta_sum_exists l",
                "cases beta_sum_exists",
                "exists x",
                "split",
                "exact beta_sum_exists_witness",
                "intro m",
                "intro hm",
                "specialize beta_sum_functional b",
                "specialize beta_sum_functional c",
                "specialize beta_sum_functional l",
                "specialize beta_sum_functional x",
                "specialize beta_sum_functional m",
                "apply beta_sum_functional",
                "exact beta_sum_exists_witness",
                "exact hm",
            ),
            "Every decoded beta prefix has exactly one relational finite sum.",
        ),
        spec(
            "beta_sum_zero",
            f"forall b c n. ({zero_sum}) -> n = 0",
            ("beta_at_unique",),
            (
                "intro b",
                "intro c",
                "intro n",
                "intro hsum",
                "cases hsum",
                "cases hsum_witness",
                "cases hsum_witness_witness",
                "cases hsum_witness_witness_right",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique 0",
                "specialize beta_at_unique n",
                "specialize beta_at_unique 0",
                "apply beta_at_unique",
                "exact hsum_witness_witness_right_left",
                "exact hsum_witness_witness_left",
            ),
            "The sum of an empty decoded prefix is zero.",
        ),
        spec(
            "beta_sum_succ_decompose",
            f"forall b c l n. ({successor_sum}) -> {successor_decomposition}",
            ("le_refl", "le_succ", "beta_at_unique"),
            (
                "intro b",
                "intro c",
                "intro l",
                "intro n",
                "intro hsum",
                "cases hsum",
                "cases hsum_witness",
                "cases hsum_witness_witness",
                "cases hsum_witness_witness_right",
                "have hstep : exists a r s. "
                f"(({_at('b', 'c', 'l', 'a', tag='decomp_factor')}) /\\ "
                f"(({_at('x', 'x1', 'l', 'r', tag='decomp_partial')}) /\\ "
                f"(({_at('x', 'x1', 'S l', 's', tag='decomp_successor')}) /\\ "
                "s = r + a)))",
                "specialize hsum_witness_witness_right_right l",
                "apply hsum_witness_witness_right_right",
                "specialize le_refl (S l)",
                "exact le_refl",
                "cases hstep",
                "cases hstep_witness",
                "cases hstep_witness_witness",
                "cases hstep_witness_witness_witness",
                "cases hstep_witness_witness_witness_right",
                "cases hstep_witness_witness_witness_right_right",
                "have hn : n = x4",
                "specialize beta_at_unique x",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique (S l)",
                "specialize beta_at_unique n",
                "specialize beta_at_unique x4",
                "apply beta_at_unique",
                "exact hsum_witness_witness_right_left",
                "exact hstep_witness_witness_witness_right_right_left",
                "exists x2",
                "exists x3",
                "split",
                "exact hstep_witness_witness_witness_left",
                "split",
                "exists x",
                "exists x1",
                "split",
                "exact hsum_witness_witness_left",
                "split",
                "exact hstep_witness_witness_witness_right_left",
                "intro i",
                "intro hi",
                "specialize hsum_witness_witness_right_right i",
                "apply hsum_witness_witness_right_right",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "trans x4",
                "exact hn",
                "exact hstep_witness_witness_witness_right_right_right",
            ),
            "A successor sum decomposes into its prefix sum and final summand.",
        ),
    )


__all__ = ["make_finite_sum_theorems"]
