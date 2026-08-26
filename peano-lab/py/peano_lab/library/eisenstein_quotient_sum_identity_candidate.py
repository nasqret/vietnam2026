"""Exact Eisenstein identity for the two decoded quotient sums.

The semantic Fubini endpoint gives ``N + T = h * k`` for the two rectangle
row-count totals.  The independently audited row-quotient bridges identify
those totals with the beta-coded division quotients in the two orientations.
This module composes the interfaces and eliminates the intermediate semantic
totals, yielding the native finite floor-sum identity needed by reciprocity.

All relations expand before parsing to unchanged first-order PA.  The sole
candidate is constructive, dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_rectangle_count_candidate import (
    eisenstein_rectangle_row_count_prefix,
)
from .eisenstein_scaled_division_candidate import scaled_successor_prefix
from .fermat_residue_product_candidate import prime
from .finite_division_prefix_candidate import division_prefix
from .finite_fold_surface import sum_relation


def make_eisenstein_quotient_sum_identity_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact sum of both decoded quotient prefixes."""

    prime_p = prime("p", tag="quotient_sum_identity_prime_p")
    prime_q = prime("q", tag="quotient_sum_identity_prime_q")
    first_scaled = scaled_successor_prefix(
        "q", "tb", "tc", "h", tag="quotient_sum_identity_first_scaled"
    )
    first_divisions = division_prefix(
        "p", "tb", "tc", "qb", "qc", "ub", "uc", "h",
        tag="quotient_sum_identity_first_divisions",
    )
    second_scaled = scaled_successor_prefix(
        "p", "sb", "sc", "k", tag="quotient_sum_identity_second_scaled"
    )
    second_divisions = division_prefix(
        "q", "sb", "sc", "vb", "vc", "wb", "wc", "k",
        tag="quotient_sum_identity_second_divisions",
    )
    first_outer = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "ab", "ac", "h",
        tag="quotient_sum_identity_first_outer",
    )
    second_outer = eisenstein_rectangle_row_count_prefix(
        "q", "p", "h", "bb", "bc", "k",
        tag="quotient_sum_identity_second_outer",
    )
    first_quotient_sum = sum_relation(
        "qb", "qc", "h", "Q", tag="quotient_sum_identity_first_sum"
    )
    second_quotient_sum = sum_relation(
        "vb", "vc", "k", "U", tag="quotient_sum_identity_second_sum"
    )

    return (
        spec(
            "distinct_odd_prime_eisenstein_quotient_sum_identity",
            "forall p q h k tb tc qb qc ub uc sb sc vb vc wb wc "
            "ab ac bb bc Q U. "
            f"p = 2 * h + 1 -> q = 2 * k + 1 -> ({prime_p}) -> "
            f"({prime_q}) -> ~(p = q) -> ({first_scaled}) -> "
            f"({first_divisions}) -> ({second_scaled}) -> "
            f"({second_divisions}) -> ({first_outer}) -> ({second_outer}) -> "
            f"({first_quotient_sum}) -> ({second_quotient_sum}) -> "
            "Q + U = h * k",
            (
                "beta_sum_exists",
                "distinct_odd_prime_quotient_sum_equals_rectangle_total",
                "eisenstein_rectangle_floor_sum_identity",
            ),
            (
                "intro p", "intro q", "intro h", "intro k",
                "intro tb", "intro tc", "intro qb", "intro qc",
                "intro ub", "intro uc", "intro sb", "intro sc",
                "intro vb", "intro vc", "intro wb", "intro wc",
                "intro ab", "intro ac", "intro bb", "intro bc",
                "intro Q", "intro U",
                "intro hpodd", "intro hqodd", "intro hp", "intro hq",
                "intro hpq", "intro hfirstscaled", "intro hfirstdivisions",
                "intro hsecondscaled", "intro hseconddivisions",
                "intro hfirstouter", "intro hsecondouter",
                "intro hfirstsum", "intro hsecondsum",
                "have hfirst_total : exists N. "
                f"({sum_relation('ab', 'ac', 'h', 'N', tag='quotient_sum_identity_first_total')})",
                "specialize beta_sum_exists ab", "specialize beta_sum_exists ac",
                "specialize beta_sum_exists h", "exact beta_sum_exists",
                "cases hfirst_total",
                "have hsecond_total : exists T. "
                f"({sum_relation('bb', 'bc', 'k', 'T', tag='quotient_sum_identity_second_total')})",
                "specialize beta_sum_exists bb", "specialize beta_sum_exists bc",
                "specialize beta_sum_exists k", "exact beta_sum_exists",
                "cases hsecond_total",
                "have hqp : ~(q = p)",
                "intro hqp_eq", "apply hpq", "symm", "exact hqp_eq",
                "have hQ : Q = x",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total p",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total q",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total h",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total k",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total tb",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total tc",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total qb",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total qc",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total ub",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total uc",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total ab",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total ac",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total Q",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total x",
                "apply distinct_odd_prime_quotient_sum_equals_rectangle_total",
                "exact hpodd", "exact hqodd", "exact hp", "exact hq",
                "exact hpq", "exact hfirstscaled", "exact hfirstdivisions",
                "exact hfirstouter", "exact hfirstsum",
                "exact hfirst_total_witness",
                "have hU : U = x1",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total q",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total p",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total k",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total h",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total sb",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total sc",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total vb",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total vc",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total wb",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total wc",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total bb",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total bc",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total U",
                "specialize distinct_odd_prime_quotient_sum_equals_rectangle_total x1",
                "apply distinct_odd_prime_quotient_sum_equals_rectangle_total",
                "exact hqodd", "exact hpodd", "exact hq", "exact hp",
                "exact hqp", "exact hsecondscaled", "exact hseconddivisions",
                "exact hsecondouter", "exact hsecondsum",
                "exact hsecond_total_witness",
                "have harea : x + x1 = h * k",
                "specialize eisenstein_rectangle_floor_sum_identity p",
                "specialize eisenstein_rectangle_floor_sum_identity q",
                "specialize eisenstein_rectangle_floor_sum_identity h",
                "specialize eisenstein_rectangle_floor_sum_identity k",
                "specialize eisenstein_rectangle_floor_sum_identity ab",
                "specialize eisenstein_rectangle_floor_sum_identity ac",
                "specialize eisenstein_rectangle_floor_sum_identity bb",
                "specialize eisenstein_rectangle_floor_sum_identity bc",
                "specialize eisenstein_rectangle_floor_sum_identity x",
                "specialize eisenstein_rectangle_floor_sum_identity x1",
                "apply eisenstein_rectangle_floor_sum_identity",
                "exact hfirstouter", "exact hsecondouter",
                "exact hfirst_total_witness", "exact hsecond_total_witness",
                "rewrite hQ", "rewrite hU", "exact harea",
            ),
            "For distinct odd primes, the two decoded finite quotient sums add exactly to h*k.",
        ),
    )


__all__ = ["make_eisenstein_quotient_sum_identity_candidate_theorems"]
