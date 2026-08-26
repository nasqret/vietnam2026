"""Constructive growth laws for relational powers.

This second Bertrand quantitative tranche builds only on checked power
algebra and the isolated order candidates in
``bertrand_power_order_candidate``.  It proves that a base at least one has
all powers at least one, that such powers are nonzero, and that exponent
growth is monotone.  All notation is expanded before parsing and the module
remains an unregistered candidate surface.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import power_relation


def _le(left: str, right: str, *, tag: str) -> str:
    return f"exists bpg_gap_{tag}. bpg_gap_{tag} + ({left}) = ({right})"


def make_bertrand_power_growth_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build positive-base nonzeroness and exponent monotonicity."""

    base_at_least_one = _le("1", "a", tag="base")
    value_at_least_one = _le("1", "x", tag="value")
    power = power_relation("a", "e", "x", tag="bpg_value")
    prefix_power = power_relation("a", "e", "r", tag="bpg_prefix")

    exponent_le = _le("e", "f", tag="exponent")
    exponent_result_le = _le("x", "y", tag="exponent_result")
    exponent_left_power = power_relation("a", "e", "x", tag="bpg_exp_left")
    exponent_right_power = power_relation("a", "f", "y", tag="bpg_exp_right")
    # ``cases hef`` introduces the additive gap under the deterministic local
    # name ``x1``; this expanded helper is used only after that elimination.
    gap_power = power_relation("a", "x1", "z", tag="bpg_exp_gap")

    return (
        spec(
            "one_le_pow",
            "forall a e x. "
            f"({base_at_least_one}) -> ({power}) -> ({value_at_least_one})",
            (
                "pow_zero",
                "pow_successor_decompose",
                "le_refl",
                "le_mul_of_one_le_right",
                "le_trans",
            ),
            (
                "intro a",
                "intro e",
                "induction e",
                "intro x",
                "intro ha",
                "intro hx",
                "have hx1 : x = 1",
                "specialize pow_zero a",
                "specialize pow_zero 0",
                "specialize pow_zero x",
                "apply pow_zero",
                "refl",
                "exact hx",
                "rewrite hx1",
                "specialize le_refl 1",
                "exact le_refl",
                "intro x",
                "intro ha",
                "intro hx",
                f"have hstep : exists r. ({prefix_power}) /\\ x = r * a",
                "specialize pow_successor_decompose a",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose x",
                "apply pow_successor_decompose",
                "refl",
                "exact hx",
                "cases hstep",
                "cases hstep_witness",
                "have hr : exists k. k + 1 = x1",
                "specialize IH x1",
                "apply IH",
                "exact ha",
                "exact hstep_witness_left",
                "have hrproduct : exists k. k + x1 = x1 * a",
                "specialize le_mul_of_one_le_right x1",
                "specialize le_mul_of_one_le_right a",
                "apply le_mul_of_one_le_right",
                "exact ha",
                "rewrite hstep_witness_right",
                "specialize le_trans 1",
                "specialize le_trans x1",
                "specialize le_trans (x1 * a)",
                "apply le_trans",
                "exact hr",
                "exact hrproduct",
            ),
            "Every relational power of a base at least one is at least one.",
        ),
        spec(
            "pow_nonzero_of_one_le",
            "forall a e x. "
            f"({base_at_least_one}) -> ({power}) -> ~(x = 0)",
            ("one_le_pow", "ne_zero_of_one_le"),
            (
                "intro a",
                "intro e",
                "intro x",
                "intro ha",
                "intro hx",
                f"have hx1 : {value_at_least_one}",
                "specialize one_le_pow a",
                "specialize one_le_pow e",
                "specialize one_le_pow x",
                "apply one_le_pow",
                "exact ha",
                "exact hx",
                "intro hx0",
                "specialize ne_zero_of_one_le x",
                "apply ne_zero_of_one_le",
                "exact hx1",
                "exact hx0",
            ),
            "A relational power of a base at least one cannot be zero.",
        ),
        spec(
            "pow_exponent_monotone",
            "forall a e f x y. "
            f"({base_at_least_one}) -> ({exponent_le}) -> "
            f"({exponent_left_power}) -> ({exponent_right_power}) -> "
            f"({exponent_result_le})",
            (
                "pow_exists",
                "pow_add",
                "one_le_pow",
                "le_mul_of_one_le_right",
                "add_comm",
            ),
            (
                "intro a",
                "intro e",
                "intro f",
                "intro x",
                "intro y",
                "intro ha",
                "intro hef",
                "intro hx",
                "intro hy",
                "cases hef",
                "have hsum : f = e + x1",
                "trans x1 + e",
                "symm",
                "exact hef_witness",
                "specialize add_comm x1",
                "specialize add_comm e",
                "exact add_comm",
                f"have hgap : exists z. ({gap_power})",
                "specialize pow_exists a",
                "specialize pow_exists x1",
                "exact pow_exists",
                "cases hgap",
                "have hyfactor : y = x * x2",
                "specialize pow_add a",
                "specialize pow_add e",
                "specialize pow_add x1",
                "specialize pow_add f",
                "specialize pow_add x",
                "specialize pow_add x2",
                "specialize pow_add y",
                "apply pow_add",
                "exact hsum",
                "exact hx",
                "exact hgap_witness",
                "exact hy",
                "have hgap1 : exists k. k + 1 = x2",
                "specialize one_le_pow a",
                "specialize one_le_pow x1",
                "specialize one_le_pow x2",
                "apply one_le_pow",
                "exact ha",
                "exact hgap_witness",
                "rewrite hyfactor",
                "specialize le_mul_of_one_le_right x",
                "specialize le_mul_of_one_le_right x2",
                "apply le_mul_of_one_le_right",
                "exact hgap1",
            ),
            "Powers of a base at least one are monotone in the exponent.",
        ),
    )


__all__ = ["make_bertrand_power_growth_candidate_theorems"]
