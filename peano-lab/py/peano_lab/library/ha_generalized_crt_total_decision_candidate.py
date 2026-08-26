"""Raw-input total decision wrapper for binary generalized CRT.

M5e accepts a supplied relational gcd witness.  This isolated M5f wrapper
removes that authoring burden: public relational-gcd existence constructs a
gcd, and the M5e theorem returns compatibility with a solution or certified
incompatibility with unsolvability.  The gcd remains explicit in the output so
the obstruction is inspectable and reusable.

All readable relations expand hygienically to first-order HA over
``0, S, +, *, =`` before parsing.  Nothing here is registered or admitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .ha_canonical_gcd_candidate import is_gcd
from .ha_generalized_crt_congruence_candidate import balanced_mod_eq, crt_solution


def make_ha_generalized_crt_total_decision_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the single raw-input total-decision wrapper."""

    variables = ("m", "n", "a", "b", "g")
    gcd_relation = is_gcd("g", "m", "n", tag="total_decision")
    compatibility = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="total_decision_compatible",
        variables=variables,
    )
    incompatibility = balanced_mod_eq(
        "g",
        "a",
        "b",
        tag="total_decision_incompatible",
        variables=variables,
    )
    positive_solution = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="total_decision_positive",
        variables=(*variables, "x"),
    )
    negative_solution = crt_solution(
        "x",
        "m",
        "n",
        "a",
        "b",
        tag="total_decision_negative",
        variables=(*variables, "x"),
    )

    return (
        spec(
            "generalized_binary_crt_total_decision",
            f"forall m n a b. exists g. (({gcd_relation}) /\\ "
            f"((({compatibility}) /\\ exists x. ({positive_solution})) \\/ "
            f"(~({incompatibility}) /\\ "
            f"~(exists x. ({negative_solution})))))",
            (
                "gcd_exists_relational",
                "generalized_binary_crt_solution_or_obstruction",
            ),
            (
                "intro m",
                "intro n",
                "intro a",
                "intro b",
                "specialize gcd_exists_relational m",
                "specialize gcd_exists_relational n",
                "cases gcd_exists_relational",
                "exists x",
                "split",
                "exact gcd_exists_relational_witness",
                "specialize generalized_binary_crt_solution_or_obstruction x",
                "specialize generalized_binary_crt_solution_or_obstruction m",
                "specialize generalized_binary_crt_solution_or_obstruction n",
                "specialize generalized_binary_crt_solution_or_obstruction a",
                "specialize generalized_binary_crt_solution_or_obstruction b",
                "apply generalized_binary_crt_solution_or_obstruction",
                "exact gcd_exists_relational_witness",
            ),
            "Every raw binary CRT input returns a relational gcd and either a solution or a certified incompatibility obstruction.",
        ),
    )


__all__ = ["make_ha_generalized_crt_total_decision_candidate_theorems"]
