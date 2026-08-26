"""Constructive support for the complement-form Choose factorial bridge.

The first candidate transports a relational factorial along equality of its
length.  The second isolates the commutative-semiring reassociation needed by
the weighted Choose recurrence.  Factorial is expanded before parsing, and
this module creates no trusted primitive, authority enrollment, or checked-
use grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.finite_factorial_theorems import factorial_relation


FACTORIAL_LENGTH_EQ_TRANSPORT = "factorial_length_eq_transport"
FACTORIAL_WEIGHTED_PRODUCT_COMBINE = "factorial_weighted_product_combine"


def make_bertrand_choose_factorial_support_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build factorial transport followed by the weighted product identity."""

    transport_source = factorial_relation("n", "z", tag="bcflet_source")
    transport_target = factorial_relation("m", "z", tag="bcflet_target")
    transport_script = (
        "intro n",
        "intro m",
        "intro z",
        "intro heq",
        "intro hfactorial",
        "rewrite heq at hfactorial",
        "rewrite heq at hfactorial",
        "rewrite heq at hfactorial",
        "rewrite heq at hfactorial",
        "exact hfactorial",
    )

    combine_script = (
        "intro u",
        "intro v",
        "intro x",
        "intro y",
        "intro f",
        "intro K",
        "intro r",
        "intro F",
        "intro J",
        "intro hJ",
        "intro hF",
        "intro hweighted",
        "intro hf",
        "rewrite hf at hF",
        "have hassoc_xv : ((K * r) * x) * v = (K * r) * (x * v)",
        "apply mul_assoc",
        "rewrite hassoc_xv at hF",
        "have hcomm_xv : x * v = v * x",
        "apply mul_comm",
        "rewrite hcomm_xv at hF",
        "rewrite <- hweighted at hF",
        "have hassoc_uy : ((K * r) * u) * y = (K * r) * (u * y)",
        "apply mul_assoc",
        "rewrite <- hassoc_uy at hF",
        "have hassoc_kru : (K * r) * u = K * (r * u)",
        "apply mul_assoc",
        "rewrite hassoc_kru at hF",
        "rewrite <- hJ at hF",
        "exact hF",
    )

    return (
        spec(
            FACTORIAL_LENGTH_EQ_TRANSPORT,
            "forall n m z. n = m -> "
            f"({transport_source}) -> ({transport_target})",
            (),
            transport_script,
            "Relational factorial transports along equality of its length.",
        ),
        spec(
            FACTORIAL_WEIGHTED_PRODUCT_COMBINE,
            "forall u v x y f K r F J. "
            "J = r * u -> F = f * v -> u * y = v * x -> "
            "f = (K * r) * x -> F = (K * J) * y",
            ("mul_comm", "mul_assoc"),
            combine_script,
            "Weighted factorial products combine by reassociation.",
        ),
    )


__all__ = ["make_bertrand_choose_factorial_support_candidate_theorems"]
