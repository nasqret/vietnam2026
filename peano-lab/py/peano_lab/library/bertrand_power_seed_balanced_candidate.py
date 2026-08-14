"""Balanced exact-power seed for the Bertrand all-root package.

The established ``pow_two_seed_bundle_from_total`` statement is useful to
the Bertrand H/J proof graph, but its original candidate body constructs
``2^7`` through every successor from ``2^2``.  The large unary arithmetic
certificates in the last two successor steps make that otherwise valid body
too deep for the unchanged layered proof-envelope limit.

This isolated replacement provider deliberately returns two small arithmetic
helpers followed by the *same theorem name and expanded statement* as the
old seed.  It is intended only for an explicit name-for-name substitution in
a proof graph; callers must not concatenate the replacement row with the
original provider.  The proof remains constructive.  Its large relational
body builds ``2^3`` and ``2^4`` by small successor steps, obtains a totality
witness for ``2^7``, and identifies that witness through the balanced
factorization ``2^(3+4) = 2^3 * 2^4``.  The unary arithmetic bridges
``8*8=64`` and ``8*16=128`` are proved separately, outside that expanded
power context, so their annotations are not multiplied through the seed
body.  Arithmetic at the tactic depth boundary is expanded explicitly with
the Peano multiplication and addition axioms rather than ``norm_num``.

``PowTotal`` and ``Pow`` are authoring notation only.  Both are expanded into
the existing beta-coded finite-product relation before parsing; this module
adds no predicate, proof rule, arithmetic axiom, or classical principle.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_power_total_candidate import power_total_relation
from .power_algebra_theorems import _power_terms


def make_bertrand_power_seed_balanced_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the substitution-only balanced seed candidate."""

    total_seed = power_total_relation(tag="seed")
    two_two_any = _power_terms(
        "2", "2", "x", tag="bpsb_seed_two_any"
    )
    two_two = _power_terms("2", "2", "4", tag="bpt_seed_two")
    two_three = _power_terms(
        "2", "3", "8", tag="bpsb_seed_three"
    )
    two_four = _power_terms(
        "2", "4", "16", tag="bpsb_seed_four"
    )
    two_seven_any = _power_terms(
        "2", "7", "z", tag="bpsb_seed_seven_any"
    )
    two_seven = _power_terms(
        "2", "7", "128", tag="bpt_seed_seven"
    )

    return (
        spec(
            "eight_times_eight_eq_sixty_four",
            "8 * 8 = 64",
            (),
            (
                *("rewrite PA6",) * 8,
                "rewrite PA5",
                *(
                    (("rewrite PA4",) * 8 + ("rewrite PA3",))
                    * 8
                ),
                "refl",
            ),
            (
                "The bounded arithmetic bridge 8*8=64, expanded directly "
                "through the Peano multiplication and addition axioms."
            ),
        ),
        spec(
            "eight_times_sixteen_eq_one_twenty_eight",
            "8 * 16 = 128",
            ("mul_add", "eight_times_eight_eq_sixty_four"),
            (
                "have hsixteen_split : 16 = 8 + 8",
                "norm_num",
                "have hsixty_four_double : 64 + 64 = 128",
                *("rewrite PA4",) * 64,
                "rewrite PA3",
                "refl",
                "rewrite hsixteen_split",
                "specialize mul_add 8",
                "specialize mul_add 8",
                "specialize mul_add 8",
                "rewrite mul_add",
                "rewrite eight_times_eight_eq_sixty_four",
                "rewrite eight_times_eight_eq_sixty_four",
                "exact hsixty_four_double",
            ),
            (
                "The bounded arithmetic bridge 8*16=128, factored through "
                "two checked copies of 8*8=64."
            ),
        ),
        spec(
            "pow_two_seed_bundle_from_total",
            f"({total_seed}) -> (({two_two}) /\\ ({two_seven}))",
            (
                "pow_successor_compose_from_total",
                "pow_two_base_two_value_four",
                "pow_add",
                "eight_times_sixteen_eq_one_twenty_eight",
            ),
            (
                "intro htotal",
                f"have htwo_exists : exists x. ({two_two_any})",
                "specialize htotal 2",
                "specialize htotal 2",
                "exact htotal",
                "cases htwo_exists",
                "have htwo_value : x = 4",
                "specialize pow_two_base_two_value_four x",
                "apply pow_two_base_two_value_four",
                "exact htwo_exists_witness",
                f"have htwo : {two_two}",
                "rewrite <- htwo_value",
                "rewrite <- htwo_value",
                "exact htwo_exists_witness",
                f"have hthree : {two_three}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 4",
                "specialize pow_successor_compose_from_total 8",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact htwo",
                "norm_num",
                f"have hfour : {two_four}",
                "specialize pow_successor_compose_from_total 2",
                "specialize pow_successor_compose_from_total 3",
                "specialize pow_successor_compose_from_total 8",
                "specialize pow_successor_compose_from_total 16",
                "apply pow_successor_compose_from_total",
                "exact htotal",
                "exact hthree",
                "norm_num",
                f"have hseven_exists : exists z. ({two_seven_any})",
                "specialize htotal 2",
                "specialize htotal 7",
                "exact htotal",
                "cases hseven_exists",
                "have hseven_product : x1 = 8 * 16",
                "specialize pow_add 2",
                "specialize pow_add 3",
                "specialize pow_add 4",
                "specialize pow_add 7",
                "specialize pow_add 8",
                "specialize pow_add 16",
                "specialize pow_add x1",
                "apply pow_add",
                "norm_num",
                "exact hthree",
                "exact hfour",
                "exact hseven_exists_witness",
                "have hseven_value : x1 = 128",
                "trans 8 * 16",
                "exact hseven_product",
                "exact eight_times_sixteen_eq_one_twenty_eight",
                f"have hseven : {two_seven}",
                "rewrite <- hseven_value",
                "rewrite <- hseven_value",
                "exact hseven_exists_witness",
                "split",
                "exact htwo",
                "exact hseven",
            ),
            (
                "The exact seeds 2^2=4 and 2^7=128, with the latter "
                "constructed through the balanced exponent split 3+4."
            ),
        ),
    )


__all__ = ["make_bertrand_power_seed_balanced_candidate_theorems"]
