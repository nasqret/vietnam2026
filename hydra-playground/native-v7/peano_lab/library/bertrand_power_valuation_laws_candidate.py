"""Prime-power valuation laws for the Bertrand campaign.

The bounded valuation factory deliberately defines a valuation as a greatest
``PowDiv`` exponent below the value itself.  This isolated tranche proves that
on its intended domain -- a prime base and a nonzero value -- the selected
exponent has the familiar successor-nondivisibility property.

All displayed relations are expanded into the unchanged first-order Peano
language before parsing.  The factory is intentionally absent from every
library registry and edition pending a separate closure and enrollment review.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_power_valuation_candidate import (
    _power_divides_terms,
    at_most,
    power_divides,
    power_valuation,
)
from .fermat_residue_map_candidate import prime
from .finite_fold_surface import power_relation


def _le_terms(left: str, right: str, *, tag: str) -> str:
    """Expand one module-owned order formula containing compound terms."""

    return f"exists bpvl_gap_{tag}. bpvl_gap_{tag} + ({left}) = ({right})"


def make_bertrand_power_valuation_law_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the dependency-ordered maximal-prime-power bridge."""

    prime_p = prime("p", tag="bpvl_prime")
    power_pe_x = power_relation("p", "e", "x", tag="bpvl_exponent_bound")
    successor_power_divides = _power_divides_terms(
        "p", "S e", "a", tag="bpvl_successor_divides"
    )
    selected_power_divides = power_divides(
        "p", "e", "a", tag="bpvl_selected_divides"
    )
    valuation = power_valuation("p", "a", "e", tag="bpvl_valuation")

    return (
        spec(
            "prime_two_le",
            f"forall p. ({prime_p}) -> ({_le_terms('2', 'p', tag='prime_two')})",
            ("prime_is_succ_succ",),
            (
                "intro p",
                "intro hp",
                "have hshape : exists k. p = S (S k)",
                "specialize prime_is_succ_succ p",
                "apply prime_is_succ_succ",
                "exact hp",
                "cases hshape",
                "exists x",
                "trans S (S x)",
                "rewrite PA4",
                "rewrite PA4",
                "rewrite PA3",
                "refl",
                "symm",
                "exact hshape_witness",
            ),
            "Every prime is at least two in witness-defined order.",
        ),
        spec(
            "succ_le_mul_of_two_le_right",
            "forall r p. ~(r = 0) -> "
            f"({_le_terms('2', 'p', tag='factor_two')}) -> "
            f"({_le_terms('S r', 'r * p', tag='factor_result')})",
            (
                "mul_lt_mul_succ_left_nonzero",
                "mul_le_mul_left",
                "mul_one",
                "le_trans",
            ),
            (
                "intro r",
                "intro p",
                "intro hr",
                "intro hp",
                "have hstep : exists k. k + S (r * 1) = r * 2",
                "specialize mul_lt_mul_succ_left_nonzero r",
                "specialize mul_lt_mul_succ_left_nonzero 1",
                "apply mul_lt_mul_succ_left_nonzero",
                "exact hr",
                "specialize mul_one r",
                "rewrite mul_one at hstep",
                "have hscaled : exists k. k + r * 2 = r * p",
                "specialize mul_le_mul_left 2",
                "specialize mul_le_mul_left p",
                "specialize mul_le_mul_left r",
                "apply mul_le_mul_left",
                "exact hp",
                "specialize le_trans (S r)",
                "specialize le_trans (r * 2)",
                "specialize le_trans (r * p)",
                "apply le_trans",
                "exact hstep",
                "exact hscaled",
            ),
            "Multiplying a nonzero natural by a factor at least two exceeds it.",
        ),
        spec(
            "prime_power_exponent_le",
            f"forall p e x. ({prime_p}) -> ({power_pe_x}) -> "
            f"({at_most('e', 'x', tag='power_exponent')})",
            (
                "pow_successor_decompose",
                "zero_le",
                "prime_nonzero",
                "one_le_of_ne_zero",
                "pow_nonzero_of_one_le",
                "prime_two_le",
                "succ_le_succ",
                "succ_le_mul_of_two_le_right",
                "le_trans",
            ),
            (
                "intro p",
                "intro e",
                "induction e",
                "intro x",
                "intro hp",
                "intro hx",
                "specialize zero_le x",
                "exact zero_le",
                "intro x",
                "intro hp",
                "intro hx",
                "have hstep : exists r. "
                f"({power_relation('p', 'e', 'r', tag='bpvl_prefix')}) /\\ "
                "x = r * p",
                "specialize pow_successor_decompose p",
                "specialize pow_successor_decompose e",
                "specialize pow_successor_decompose (S e)",
                "specialize pow_successor_decompose x",
                "apply pow_successor_decompose",
                "refl",
                "exact hx",
                "cases hstep",
                "cases hstep_witness",
                "have he_prefix : exists k. k + e = x1",
                "specialize IH x1",
                "apply IH",
                "exact hp",
                "exact hstep_witness_left",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hp",
                "exact hpzero",
                "have hp1 : exists k. k + 1 = p",
                "specialize one_le_of_ne_zero p",
                "apply one_le_of_ne_zero",
                "exact hp0",
                "have hprefix0 : ~(x1 = 0)",
                "intro hprefixzero",
                "specialize pow_nonzero_of_one_le p",
                "specialize pow_nonzero_of_one_le e",
                "specialize pow_nonzero_of_one_le x1",
                "apply pow_nonzero_of_one_le",
                "exact hp1",
                "exact hstep_witness_left",
                "exact hprefixzero",
                "have hp2 : exists k. k + 2 = p",
                "specialize prime_two_le p",
                "apply prime_two_le",
                "exact hp",
                "have hprefix_step : exists k. k + S x1 = x1 * p",
                "specialize succ_le_mul_of_two_le_right x1",
                "specialize succ_le_mul_of_two_le_right p",
                "apply succ_le_mul_of_two_le_right",
                "exact hprefix0",
                "exact hp2",
                "have he_step : exists k. k + S e = S x1",
                "specialize succ_le_succ e",
                "specialize succ_le_succ x1",
                "apply succ_le_succ",
                "exact he_prefix",
                "rewrite hstep_witness_right",
                "specialize le_trans (S e)",
                "specialize le_trans (S x1)",
                "specialize le_trans (x1 * p)",
                "apply le_trans",
                "exact he_step",
                "exact hprefix_step",
            ),
            "The exponent of a relational power at a prime base is bounded by its value.",
        ),
        spec(
            "prime_power_divides_exponent_le_value",
            f"forall p e a. ({prime_p}) -> ~(a = 0) -> "
            f"({power_divides('p', 'e', 'a', tag='bpvl_bound_divides')}) -> "
            f"({at_most('e', 'a', tag='divides_exponent_value')})",
            ("prime_power_exponent_le", "divisor_le_nonzero", "le_trans"),
            (
                "intro p",
                "intro e",
                "intro a",
                "intro hp",
                "intro ha",
                "intro hdivides",
                "cases hdivides",
                "cases hdivides_witness",
                "have hexponent : exists k. k + e = x",
                "specialize prime_power_exponent_le p",
                "specialize prime_power_exponent_le e",
                "specialize prime_power_exponent_le x",
                "apply prime_power_exponent_le",
                "exact hp",
                "exact hdivides_witness_left",
                "have hpower_value : exists k. k + x = a",
                "specialize divisor_le_nonzero x",
                "specialize divisor_le_nonzero a",
                "apply divisor_le_nonzero",
                "exact ha",
                "exact hdivides_witness_right",
                "specialize le_trans e",
                "specialize le_trans x",
                "specialize le_trans a",
                "apply le_trans",
                "exact hexponent",
                "exact hpower_value",
            ),
            "A dividing prime power has exponent at most the nonzero dividend.",
        ),
        spec(
            "power_valuation_successor_not_divides",
            f"forall p a e. ({prime_p}) -> ~(a = 0) -> ({valuation}) -> "
            f"~({successor_power_divides})",
            (
                "prime_power_divides_exponent_le_value",
                "zero_add",
                "lt_not_le",
            ),
            (
                "intro p",
                "intro a",
                "intro e",
                "intro hp",
                "intro ha",
                "intro hvaluation",
                "intro hsuccessor",
                "have hbound : exists k. k + S e = a",
                "specialize prime_power_divides_exponent_le_value p",
                "specialize prime_power_divides_exponent_le_value (S e)",
                "specialize prime_power_divides_exponent_le_value a",
                "apply prime_power_divides_exponent_le_value",
                "exact hp",
                "exact ha",
                "exact hsuccessor",
                "cases hvaluation",
                "have himpossible : exists k. k + S e = e",
                "specialize hvaluation_right (S e)",
                "apply hvaluation_right",
                "exact hbound",
                "exact hsuccessor",
                "have hstrict : exists k. k + S e = S e",
                "exists 0",
                "specialize zero_add (S e)",
                "exact zero_add",
                "specialize lt_not_le e",
                "specialize lt_not_le (S e)",
                "apply lt_not_le",
                "exact hstrict",
                "exact himpossible",
            ),
            "A canonical valuation at a prime cannot admit the next power divisor.",
        ),
        spec(
            "power_valuation_selected_and_successor_not_divides",
            f"forall p a e. ({prime_p}) -> ~(a = 0) -> ({valuation}) -> "
            f"(({selected_power_divides}) /\\ ~({successor_power_divides}))",
            (
                "power_valuation_power_divides",
                "power_valuation_successor_not_divides",
            ),
            (
                "intro p",
                "intro a",
                "intro e",
                "intro hp",
                "intro ha",
                "intro hvaluation",
                "split",
                "specialize power_valuation_power_divides p",
                "specialize power_valuation_power_divides a",
                "specialize power_valuation_power_divides e",
                "apply power_valuation_power_divides",
                "exact hvaluation",
                "intro hsuccessor",
                "specialize power_valuation_successor_not_divides p",
                "specialize power_valuation_successor_not_divides a",
                "specialize power_valuation_successor_not_divides e",
                "apply power_valuation_successor_not_divides",
                "exact hp",
                "exact ha",
                "exact hvaluation",
                "exact hsuccessor",
            ),
            "Canonical prime valuations have the usual maximal-power characterization.",
        ),
    )


__all__ = ["make_bertrand_power_valuation_law_candidate_theorems"]
