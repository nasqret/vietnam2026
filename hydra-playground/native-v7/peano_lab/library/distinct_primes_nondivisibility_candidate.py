"""Mutual nondivisibility of distinct primes.

This small reusable bridge extracts the exact ``p does not divide q`` and
``q does not divide p`` premises needed by arbitrary Gauss's lemma from the
usual prime and distinctness assumptions.  Predicates expand to first-order
PA; the candidates remain isolated, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import not_divides, prime


def make_distinct_primes_nondivisibility_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build both oriented nondivisibility facts and their package."""

    prime_p = prime("p", tag="dpn_prime_p")
    prime_q = prime("q", tag="dpn_prime_q")
    p_not_q = not_divides("p", "q", tag="dpn_p_not_q")
    q_not_p = not_divides("q", "p", tag="dpn_q_not_p")

    return (
        spec(
            "distinct_primes_left_not_divide_right",
            f"forall p q. ({prime_p}) -> ({prime_q}) -> ~(p = q) -> ({p_not_q})",
            ("prime_divisor_eq_one_or_self",),
            (
                "intro p", "intro q", "intro hp", "intro hq", "intro hpq",
                "intro hdiv",
                r"have hfactor : p = 1 \/ q = p",
                "specialize prime_divisor_eq_one_or_self q",
                "specialize prime_divisor_eq_one_or_self p",
                "apply prime_divisor_eq_one_or_self",
                "exact hq", "exact hdiv",
                "cases hfactor",
                "cases hp", "apply hp_left", "exact hfactor_left",
                "apply hpq", "symm", "exact hfactor_right",
            ),
            "A prime cannot divide a distinct prime.",
        ),
        spec(
            "distinct_primes_right_not_divide_left",
            f"forall p q. ({prime_p}) -> ({prime_q}) -> ~(p = q) -> ({q_not_p})",
            ("distinct_primes_left_not_divide_right",),
            (
                "intro p", "intro q", "intro hp", "intro hq", "intro hpq",
                "have hqp : ~(q = p)",
                "intro h", "apply hpq", "symm", "exact h",
                "specialize distinct_primes_left_not_divide_right q",
                "specialize distinct_primes_left_not_divide_right p",
                "intro hdiv",
                "apply distinct_primes_left_not_divide_right",
                "exact hq", "exact hp", "exact hqp", "exact hdiv",
            ),
            "The reverse orientation is nondivisible as well.",
        ),
        spec(
            "distinct_primes_mutually_nondivisible",
            f"forall p q. ({prime_p}) -> ({prime_q}) -> ~(p = q) -> "
            f"(({p_not_q}) /\\ ({q_not_p}))",
            (
                "distinct_primes_left_not_divide_right",
                "distinct_primes_right_not_divide_left",
            ),
            (
                "intro p", "intro q", "intro hp", "intro hq", "intro hpq",
                "split",
                "specialize distinct_primes_left_not_divide_right p",
                "specialize distinct_primes_left_not_divide_right q",
                "intro hdiv",
                "apply distinct_primes_left_not_divide_right",
                "exact hp", "exact hq", "exact hpq", "exact hdiv",
                "specialize distinct_primes_right_not_divide_left p",
                "specialize distinct_primes_right_not_divide_left q",
                "intro hdiv",
                "apply distinct_primes_right_not_divide_left",
                "exact hp", "exact hq", "exact hpq", "exact hdiv",
            ),
            "Distinct primes are mutually nondivisible.",
        ),
    )


__all__ = ["make_distinct_primes_nondivisibility_candidate_theorems"]
