"""Exact addition of pointwise-related beta-coded finite sums.

Three decoded prefixes have a common length.  If the third entry is the sum
of the corresponding first and second entries at every bounded index, then
its relational ``Sum`` is exactly the sum of the other two terminal values.
The proof is a constructive induction on the common prefix length and never
identifies raw beta codes.

This module is dependency-curried authoring evidence only.  Every displayed
surface relation expands to the unchanged first-order Peano language, and the
candidate is deliberately absent from the public theorem registry.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, sum_relation


def _sum_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    entry = beta_at(code, scale, length, "a", tag=f"{tag}_entry")
    prefix = sum_relation(code, scale, length, "r", tag=f"{tag}_prefix")
    return f"exists a r. ({entry}) /\\ (({prefix}) /\\ {result} = r + a)"


def make_finite_sum_pointwise_add_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build exact pointwise addition for three relational finite sums."""

    left_sum = sum_relation("b", "c", "l", "n", tag="pointadd_left")
    right_sum = sum_relation("d", "e", "l", "m", tag="pointadd_right")
    total_sum = sum_relation("f", "g", "l", "q", tag="pointadd_total")
    left_entry = beta_at("b", "c", "i", "a", tag="pointadd_left_entry")
    right_entry = beta_at("d", "e", "i", "z", tag="pointadd_right_entry")
    total_entry = beta_at("f", "g", "i", "s", tag="pointadd_total_entry")
    pointwise = (
        "forall i a z s. (exists h. h + S i = l) -> "
        f"({left_entry}) -> ({right_entry}) -> ({total_entry}) -> s = a + z"
    )
    prefix_left_entry = beta_at(
        "b", "c", "i", "a", tag="pointadd_prefix_left_entry"
    )
    prefix_right_entry = beta_at(
        "d", "e", "i", "z", tag="pointadd_prefix_right_entry"
    )
    prefix_total_entry = beta_at(
        "f", "g", "i", "s", tag="pointadd_prefix_total_entry"
    )
    prefix_pointwise = (
        "forall i a z s. (exists h. h + S i = l) -> "
        f"({prefix_left_entry}) -> ({prefix_right_entry}) -> "
        f"({prefix_total_entry}) -> s = a + z"
    )
    left_decomposition = _sum_decomposition(
        "b", "c", "l", "n", tag="pointadd_left_decomp"
    )
    right_decomposition = _sum_decomposition(
        "d", "e", "l", "m", tag="pointadd_right_decomp"
    )
    total_decomposition = _sum_decomposition(
        "f", "g", "l", "q", tag="pointadd_total_decomp"
    )

    return (
        spec(
            "beta_sum_pointwise_add",
            "forall b c d e f g l n m q. "
            f"({left_sum}) -> ({right_sum}) -> ({total_sum}) -> "
            f"({pointwise}) -> n + m = q",
            (
                "beta_sum_zero",
                "beta_sum_succ_decompose",
                "le_succ",
                "le_refl",
                "add_assoc",
                "add_comm",
            ),
            (
                "intro b",
                "intro c",
                "intro d",
                "intro e",
                "intro f",
                "intro g",
                "induction l",
                "intro n",
                "intro m",
                "intro q",
                "intro hleft",
                "intro hright",
                "intro htotal",
                "intro hpointwise",
                "have hn : n = 0",
                "specialize beta_sum_zero b",
                "specialize beta_sum_zero c",
                "specialize beta_sum_zero n",
                "apply beta_sum_zero",
                "exact hleft",
                "have hm : m = 0",
                "specialize beta_sum_zero d",
                "specialize beta_sum_zero e",
                "specialize beta_sum_zero m",
                "apply beta_sum_zero",
                "exact hright",
                "have hq : q = 0",
                "specialize beta_sum_zero f",
                "specialize beta_sum_zero g",
                "specialize beta_sum_zero q",
                "apply beta_sum_zero",
                "exact htotal",
                "rewrite hn",
                "rewrite hm",
                "rewrite hq",
                "simp",
                "intro n",
                "intro m",
                "intro q",
                "intro hleft",
                "intro hright",
                "intro htotal",
                "intro hpointwise",
                f"have hleft_decomp : {left_decomposition}",
                "specialize beta_sum_succ_decompose b",
                "specialize beta_sum_succ_decompose c",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose n",
                "apply beta_sum_succ_decompose",
                "exact hleft",
                "cases hleft_decomp",
                "cases hleft_decomp_witness",
                "cases hleft_decomp_witness_witness",
                "cases hleft_decomp_witness_witness_right",
                f"have hright_decomp : {right_decomposition}",
                "specialize beta_sum_succ_decompose d",
                "specialize beta_sum_succ_decompose e",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose m",
                "apply beta_sum_succ_decompose",
                "exact hright",
                "cases hright_decomp",
                "cases hright_decomp_witness",
                "cases hright_decomp_witness_witness",
                "cases hright_decomp_witness_witness_right",
                f"have htotal_decomp : {total_decomposition}",
                "specialize beta_sum_succ_decompose f",
                "specialize beta_sum_succ_decompose g",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose q",
                "apply beta_sum_succ_decompose",
                "exact htotal",
                "cases htotal_decomp",
                "cases htotal_decomp_witness",
                "cases htotal_decomp_witness_witness",
                "cases htotal_decomp_witness_witness_right",
                f"have hprefix_pointwise : {prefix_pointwise}",
                "intro i",
                "intro a",
                "intro z",
                "intro s",
                "intro hi",
                "intro ha",
                "intro hz",
                "intro hs",
                "specialize hpointwise i",
                "specialize hpointwise a",
                "specialize hpointwise z",
                "specialize hpointwise s",
                "apply hpointwise",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact ha",
                "exact hz",
                "exact hs",
                "have hprefix : x1 + x3 = x5",
                "specialize IH x1",
                "specialize IH x3",
                "specialize IH x5",
                "apply IH",
                "exact hleft_decomp_witness_witness_right_left",
                "exact hright_decomp_witness_witness_right_left",
                "exact htotal_decomp_witness_witness_right_left",
                "exact hprefix_pointwise",
                "have hlast : x4 = x + x2",
                "specialize hpointwise l",
                "specialize hpointwise x",
                "specialize hpointwise x2",
                "specialize hpointwise x4",
                "apply hpointwise",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hleft_decomp_witness_witness_left",
                "exact hright_decomp_witness_witness_left",
                "exact htotal_decomp_witness_witness_left",
                "rewrite hleft_decomp_witness_witness_right_right",
                "rewrite hright_decomp_witness_witness_right_right",
                "rewrite htotal_decomp_witness_witness_right_right",
                "rewrite hlast",
                "simp [add_assoc, add_comm]",
                "trans (x1 + x3) + (x2 + x)",
                "symm",
                "apply add_assoc",
                "rewrite hprefix",
                "refl",
            ),
            "Pointwise sums of decoded entries induce exact addition of finite sums.",
        ),
    )


__all__ = ["make_finite_sum_pointwise_add_candidate_theorems"]
