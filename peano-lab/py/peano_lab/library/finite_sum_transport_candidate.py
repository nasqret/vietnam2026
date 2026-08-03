"""Pointwise transport for native beta-coded finite sums.

The existing relational ``Sum`` trace stores its partial sums in a separate
beta prefix.  If a second source prefix decodes every bounded entry to the
same value, that trace can be reused verbatim.  This gives exact equality of
the terminal sum without identifying raw beta codes and without induction.

The candidate below expands to the unchanged first-order Peano language.  It
is dependency-curried authoring evidence only and is deliberately absent from
the public theorem registry.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, sum_relation


def _successor_entry(code: str, scale: str, index: str, value: str) -> str:
    marker = "sumtransportsuccessorindex"
    expanded = beta_at(
        code,
        scale,
        marker,
        value,
        tag="transport_step_successor",
    )
    if expanded.count(marker) != 2:
        raise AssertionError("unexpected BetaAt index-marker multiplicity")
    return expanded.replace(marker, f"S {index}")


def make_finite_sum_transport_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build exact pointwise preservation of a relational finite sum."""

    source_sum = sum_relation("b", "c", "l", "n", tag="transport_source")
    target_sum = sum_relation("z", "e", "l", "n", tag="transport_target")
    source_entry = beta_at("b", "c", "i", "a", tag="transport_source_entry")
    target_entry = beta_at("z", "e", "i", "a", tag="transport_target_entry")
    preservation = (
        "forall i a. (exists h. h + S i = l) -> "
        f"({source_entry}) -> ({target_entry})"
    )
    trace_step = (
        "exists a r s. "
        f"(({beta_at('b', 'c', 'i', 'a', tag='transport_step_source')}) /\\ "
        f"(({beta_at('x', 'x1', 'i', 'r', tag='transport_step_partial')}) /\\ "
        f"(({_successor_entry('x', 'x1', 'i', 's')}) /\\ "
        "s = r + a)))"
    )

    return (
        spec(
            "beta_sum_transport_prefix",
            "forall b c z e l n. "
            f"({source_sum}) -> ({preservation}) -> ({target_sum})",
            (),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro e",
                "intro l",
                "intro n",
                "intro hsum",
                "intro hpres",
                "cases hsum",
                "cases hsum_witness",
                "cases hsum_witness_witness",
                "cases hsum_witness_witness_right",
                "exists x",
                "exists x1",
                "split",
                "exact hsum_witness_witness_left",
                "split",
                "exact hsum_witness_witness_right_left",
                "intro i",
                "intro hi",
                f"have hstep : {trace_step}",
                "specialize hsum_witness_witness_right_right i",
                "apply hsum_witness_witness_right_right",
                "exact hi",
                "cases hstep",
                "cases hstep_witness",
                "cases hstep_witness_witness",
                "cases hstep_witness_witness_witness",
                "cases hstep_witness_witness_witness_right",
                "cases hstep_witness_witness_witness_right_right",
                "exists x2",
                "exists x3",
                "exists x4",
                "split",
                "specialize hpres i",
                "specialize hpres x2",
                "apply hpres",
                "exact hi",
                "exact hstep_witness_witness_witness_left",
                "split",
                "exact hstep_witness_witness_witness_right_left",
                "split",
                "exact hstep_witness_witness_witness_right_right_left",
                "exact hstep_witness_witness_witness_right_right_right",
            ),
            "Pointwise-equal decoded prefixes preserve an exact relational Sum.",
        ),
    )


__all__ = ["make_finite_sum_transport_candidate_theorems"]
