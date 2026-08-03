"""Identify an Eisenstein semantic row count with its division quotient.

For a fixed row ``i``, the row-indicator prefix stores one precisely when
``p*(j+1) < q*(i+1)``.  If

``q*(i+1) = p*d + r`` with ``0 < r < p``,

the constructive division-threshold theorem says that this is equivalent to
``j+1 <= d``.  Thus the *same* beta code is an exact initial-segment prefix,
whose checked ``BitCount`` is ``d``.  The odd-prime wrapper obtains ``r != 0``
and ``d <= k`` from the existing Eisenstein arithmetic.  The terminal theorem
then reads ``d`` directly from the quotient beta prefix produced by scaled
division and identifies any semantic row ``BitCount`` with that decoded value.

All surface relations expand before parsing to unchanged first-order Peano
arithmetic.  These dependency-curried candidates remain unregistered and
unadmitted, and none uses double-negation elimination.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_division_threshold_candidate import _le_term, _lt_term
from .eisenstein_initial_segment_count_candidate import (
    eisenstein_initial_segment_prefix,
)
from .eisenstein_row_indicator_candidate import (
    eisenstein_cell_indicator_choice,
    eisenstein_row_indicator_prefix,
)
from .eisenstein_rectangle_count_candidate import eisenstein_row_count_witness
from .eisenstein_scaled_division_candidate import scaled_successor_prefix
from .fermat_residue_product_candidate import prime
from .finite_division_prefix_candidate import division_prefix
from .finite_fold_surface import beta_at, bit_count


def make_eisenstein_row_quotient_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build row-to-initial-segment, relational, and decoded bridges."""

    row_prefix = eisenstein_row_indicator_prefix(
        "p", "q", "i", "rb", "rc", "k", tag="row_quotient_source"
    )
    initial_prefix = eisenstein_initial_segment_prefix(
        "d", "rb", "rc", "k", tag="row_quotient_initial"
    )
    row_bound = _lt_term(
        "i",
        "h",
        tag="row_quotient_row_bound",
        variables=("p", "q", "h", "k", "i", "d", "r", "rb", "rc", "n"),
    )
    remainder_bound = _lt_term(
        "r",
        "p",
        tag="row_quotient_remainder_bound",
        variables=("p", "q", "h", "k", "i", "d", "r", "rb", "rc", "n"),
    )
    quotient_bound = _le_term(
        "d",
        "k",
        tag="row_quotient_quotient_bound",
        variables=("p", "q", "h", "k", "i", "d", "r", "rb", "rc", "n"),
    )
    row_count_n = bit_count(
        "rb", "rc", "k", "n", tag="row_quotient_count_n"
    )
    row_count_d = bit_count(
        "rb", "rc", "k", "d", tag="row_quotient_count_d"
    )
    prime_p = prime("p", tag="row_quotient_prime_p")
    prime_q = prime("q", tag="row_quotient_prime_q")

    decoded_scaled = scaled_successor_prefix(
        "q", "tb", "tc", "h", tag="row_quotient_scaled"
    )
    decoded_division = division_prefix(
        "p",
        "tb",
        "tc",
        "qb",
        "qc",
        "ub",
        "uc",
        "h",
        tag="row_quotient_division",
    )
    decoded_quotient = beta_at(
        "qb", "qc", "i", "d", tag="row_quotient_decoded_quotient"
    )
    semantic_row_count = eisenstein_row_count_witness(
        "p", "q", "k", "i", "n", tag="row_quotient_semantic_row"
    )
    source_entry = beta_at(
        "tb", "tc", "i", "x", tag="row_quotient_source_entry"
    )
    quotient_entry = beta_at(
        "qb", "qc", "i", "quotient", tag="row_quotient_quotient_entry"
    )
    remainder_entry = beta_at(
        "ub", "uc", "i", "remainder", tag="row_quotient_remainder_entry"
    )
    entry_remainder_bound = _lt_term(
        "remainder",
        "p",
        tag="row_quotient_entry_remainder_bound",
        variables=(
            "p", "q", "h", "k", "i", "tb", "tc", "qb", "qc", "ub", "uc",
            "rb", "rc", "n", "d", "x", "quotient", "remainder",
        ),
    )
    decoded_division_entry = (
        "exists x quotient remainder. "
        f"({source_entry}) /\\ (({quotient_entry}) /\\ "
        f"(({remainder_entry}) /\\ (x = p * quotient + remainder /\\ "
        f"({entry_remainder_bound}))))"
    )

    # Pointwise formulas used while transporting the row semantics.
    below = _lt_term(
        "p * S j",
        "q * S i",
        tag="row_quotient_below",
        variables=("p", "q", "i", "d", "r", "rb", "rc", "k", "j", "bit"),
    )
    bounded = _le_term(
        "S j",
        "d",
        tag="row_quotient_bounded",
        variables=("p", "q", "i", "d", "r", "rb", "rc", "k", "j", "bit"),
    )
    return (
        spec(
            "eisenstein_row_indicator_prefix_to_initial_segment",
            "forall p q i d r rb rc k. "
            f"({row_prefix}) -> q * S i = p * d + r -> ~(r = 0) -> "
            f"({remainder_bound}) -> ({initial_prefix})",
            (
                "nonzero_remainder_division_positive_multiple_threshold",
                "le_or_lt",
            ),
            (
                "intro p",
                "intro q",
                "intro i",
                "intro d",
                "intro r",
                "intro rb",
                "intro rc",
                "intro k",
                "intro hrow",
                "intro hdivision",
                "intro hr0",
                "intro hrp",
                "intro j",
                "intro hj",
                "have hstored : exists bit. "
                f"(({beta_at('rb', 'rc', 'j', 'bit', tag='row_quotient_stored')}) /\\ "
                f"({eisenstein_cell_indicator_choice('p', 'q', 'i', 'j', 'bit', tag='row_quotient_stored_choice')}))",
                "specialize hrow j",
                "apply hrow",
                "exact hj",
                "cases hstored",
                "cases hstored_witness",
                "exists x",
                "split",
                "exact hstored_witness_left",
                f"have hthreshold : ((({below}) -> ({bounded})) /\\ (({bounded}) -> ({below})))",
                "specialize nonzero_remainder_division_positive_multiple_threshold p",
                "specialize nonzero_remainder_division_positive_multiple_threshold (q * S i)",
                "specialize nonzero_remainder_division_positive_multiple_threshold d",
                "specialize nonzero_remainder_division_positive_multiple_threshold r",
                "specialize nonzero_remainder_division_positive_multiple_threshold j",
                "apply nonzero_remainder_division_positive_multiple_threshold",
                "exact hdivision",
                "exact hr0",
                "exact hrp",
                "cases hthreshold",
                "cases hstored_witness_right",
                "cases hstored_witness_right_left",
                "cases hstored_witness_right_left_right",
                "right",
                "split",
                "exact hstored_witness_right_left_left",
                "specialize le_or_lt (S j)",
                "specialize le_or_lt d",
                "cases le_or_lt",
                "exfalso",
                "apply hstored_witness_right_left_right_right",
                "apply hthreshold_right",
                "exact le_or_lt_left",
                "exact le_or_lt_right",
                "cases hstored_witness_right_right",
                "cases hstored_witness_right_right_right",
                "left",
                "split",
                "exact hstored_witness_right_right_left",
                "apply hthreshold_left",
                "exact hstored_witness_right_right_right_left",
            ),
            "A semantic row prefix is the exact initial segment cut out by its nonzero division quotient.",
        ),
        spec(
            "distinct_odd_prime_row_bit_count_equals_division_quotient",
            "forall p q h k i d r rb rc n. "
            "p = 2 * h + 1 -> q = 2 * k + 1 -> "
            f"({prime_p}) -> ({prime_q}) -> ~(p = q) -> ({row_bound}) -> "
            f"({row_prefix}) -> ({row_count_n}) -> "
            f"q * S i = p * d + r -> ({remainder_bound}) -> n = d",
            (
                "distinct_primes_own_odd_half_scaled_remainder_nonzero",
                "odd_half_division_quotient_bounded",
                "eisenstein_row_indicator_prefix_to_initial_segment",
                "eisenstein_initial_segment_bit_count_exact",
                "bit_count_functional",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro i",
                "intro d",
                "intro r",
                "intro rb",
                "intro rc",
                "intro n",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hi",
                "intro hrow",
                "intro hcount",
                "intro hdivision",
                "intro hrp",
                "have hr0 : ~(r = 0)",
                "intro hrzero",
                "specialize distinct_primes_own_odd_half_scaled_remainder_nonzero p",
                "specialize distinct_primes_own_odd_half_scaled_remainder_nonzero q",
                "specialize distinct_primes_own_odd_half_scaled_remainder_nonzero h",
                "specialize distinct_primes_own_odd_half_scaled_remainder_nonzero i",
                "specialize distinct_primes_own_odd_half_scaled_remainder_nonzero d",
                "specialize distinct_primes_own_odd_half_scaled_remainder_nonzero r",
                "apply distinct_primes_own_odd_half_scaled_remainder_nonzero",
                "exact hpodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hi",
                "exact hdivision",
                "exact hrzero",
                f"have hdle : {quotient_bound}",
                "specialize odd_half_division_quotient_bounded p",
                "specialize odd_half_division_quotient_bounded q",
                "specialize odd_half_division_quotient_bounded h",
                "specialize odd_half_division_quotient_bounded k",
                "specialize odd_half_division_quotient_bounded i",
                "specialize odd_half_division_quotient_bounded d",
                "specialize odd_half_division_quotient_bounded r",
                "apply odd_half_division_quotient_bounded",
                "exact hpodd",
                "exact hqodd",
                "exact hi",
                "exact hdivision",
                f"have hinitial : {initial_prefix}",
                "specialize eisenstein_row_indicator_prefix_to_initial_segment p",
                "specialize eisenstein_row_indicator_prefix_to_initial_segment q",
                "specialize eisenstein_row_indicator_prefix_to_initial_segment i",
                "specialize eisenstein_row_indicator_prefix_to_initial_segment d",
                "specialize eisenstein_row_indicator_prefix_to_initial_segment r",
                "specialize eisenstein_row_indicator_prefix_to_initial_segment rb",
                "specialize eisenstein_row_indicator_prefix_to_initial_segment rc",
                "specialize eisenstein_row_indicator_prefix_to_initial_segment k",
                "apply eisenstein_row_indicator_prefix_to_initial_segment",
                "exact hrow",
                "exact hdivision",
                "exact hr0",
                "exact hrp",
                f"have hcountd : {row_count_d}",
                "specialize eisenstein_initial_segment_bit_count_exact d",
                "specialize eisenstein_initial_segment_bit_count_exact rb",
                "specialize eisenstein_initial_segment_bit_count_exact rc",
                "specialize eisenstein_initial_segment_bit_count_exact k",
                "apply eisenstein_initial_segment_bit_count_exact",
                "exact hinitial",
                "exact hdle",
                "specialize bit_count_functional rb",
                "specialize bit_count_functional rc",
                "specialize bit_count_functional k",
                "specialize bit_count_functional n",
                "specialize bit_count_functional d",
                "apply bit_count_functional",
                "exact hcount",
                "exact hcountd",
            ),
            "A semantic row BitCount is the quotient in its bounded nonzero division.",
        ),
        spec(
            "distinct_odd_prime_row_bit_count_equals_decoded_quotient",
            "forall p q h k i tb tc qb qc ub uc rb rc n d. "
            "p = 2 * h + 1 -> q = 2 * k + 1 -> "
            f"({prime_p}) -> ({prime_q}) -> ~(p = q) -> ({row_bound}) -> "
            f"({decoded_scaled}) -> ({decoded_division}) -> ({row_prefix}) -> "
            f"({row_count_n}) -> ({decoded_quotient}) -> n = d",
            (
                "add_succ_left",
                "zero_add",
                "beta_at_unique",
                "distinct_odd_prime_row_bit_count_equals_division_quotient",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro i",
                "intro tb",
                "intro tc",
                "intro qb",
                "intro qc",
                "intro ub",
                "intro uc",
                "intro rb",
                "intro rc",
                "intro n",
                "intro d",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hi",
                "intro hscaled",
                "intro hdivisions",
                "intro hrow",
                "intro hcount",
                "intro hdentry",
                f"have hdivision_entry : {decoded_division_entry}",
                "specialize hdivisions i",
                "apply hdivisions",
                "exact hi",
                "cases hdivision_entry",
                "cases hdivision_entry_witness",
                "cases hdivision_entry_witness_witness",
                "cases hdivision_entry_witness_witness_witness",
                "cases hdivision_entry_witness_witness_witness_right",
                "cases hdivision_entry_witness_witness_witness_right_right",
                "cases hdivision_entry_witness_witness_witness_right_right_right",
                "have hxscaled : x = q * (1 + i)",
                "specialize hscaled i",
                "specialize hscaled x",
                "apply hscaled",
                "exact hi",
                "exact hdivision_entry_witness_witness_witness_left",
                "have hone : 1 + i = S i",
                "trans S (0 + i)",
                "specialize add_succ_left 0",
                "specialize add_succ_left i",
                "exact add_succ_left",
                "congr",
                "specialize zero_add i",
                "exact zero_add",
                "have hxscaled_succ : x = q * S i",
                "trans q * (1 + i)",
                "exact hxscaled",
                "congr",
                "refl",
                "exact hone",
                "have hquotient_eq : x1 = d",
                "specialize beta_at_unique qb",
                "specialize beta_at_unique qc",
                "specialize beta_at_unique i",
                "specialize beta_at_unique x1",
                "specialize beta_at_unique d",
                "apply beta_at_unique",
                "exact hdivision_entry_witness_witness_witness_right_left",
                "exact hdentry",
                "have hdivision : q * S i = p * x1 + x2",
                "trans x",
                "symm",
                "exact hxscaled_succ",
                "exact hdivision_entry_witness_witness_witness_right_right_right_left",
                "have hnq : n = x1",
                "specialize distinct_odd_prime_row_bit_count_equals_division_quotient p",
                "specialize distinct_odd_prime_row_bit_count_equals_division_quotient q",
                "specialize distinct_odd_prime_row_bit_count_equals_division_quotient h",
                "specialize distinct_odd_prime_row_bit_count_equals_division_quotient k",
                "specialize distinct_odd_prime_row_bit_count_equals_division_quotient i",
                "specialize distinct_odd_prime_row_bit_count_equals_division_quotient x1",
                "specialize distinct_odd_prime_row_bit_count_equals_division_quotient x2",
                "specialize distinct_odd_prime_row_bit_count_equals_division_quotient rb",
                "specialize distinct_odd_prime_row_bit_count_equals_division_quotient rc",
                "specialize distinct_odd_prime_row_bit_count_equals_division_quotient n",
                "apply distinct_odd_prime_row_bit_count_equals_division_quotient",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hi",
                "exact hrow",
                "exact hcount",
                "exact hdivision",
                "exact hdivision_entry_witness_witness_witness_right_right_right_right",
                "trans x1",
                "exact hnq",
                "exact hquotient_eq",
            ),
            "The semantic row count equals the quotient decoded by the scaled division prefix at that row.",
        ),
        spec(
            "distinct_odd_prime_semantic_row_equals_decoded_quotient",
            "forall p q h k i tb tc qb qc ub uc n d. "
            "p = 2 * h + 1 -> q = 2 * k + 1 -> "
            f"({prime_p}) -> ({prime_q}) -> ~(p = q) -> ({row_bound}) -> "
            f"({decoded_scaled}) -> ({decoded_division}) -> "
            f"({semantic_row_count}) -> ({decoded_quotient}) -> n = d",
            ("distinct_odd_prime_row_bit_count_equals_decoded_quotient",),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro i",
                "intro tb",
                "intro tc",
                "intro qb",
                "intro qc",
                "intro ub",
                "intro uc",
                "intro n",
                "intro d",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hi",
                "intro hscaled",
                "intro hdivisions",
                "intro hsemantic",
                "intro hdentry",
                "cases hsemantic",
                "cases hsemantic_witness",
                "cases hsemantic_witness_witness",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient p",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient q",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient h",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient k",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient i",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient tb",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient tc",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient qb",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient qc",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient ub",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient uc",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient x",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient x1",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient n",
                "specialize distinct_odd_prime_row_bit_count_equals_decoded_quotient d",
                "apply distinct_odd_prime_row_bit_count_equals_decoded_quotient",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hi",
                "exact hscaled",
                "exact hdivisions",
                "exact hsemantic_witness_witness_left",
                "exact hsemantic_witness_witness_right",
                "exact hdentry",
            ),
            "The outer rectangle's semantic row witness is extensionally its decoded division quotient.",
        ),
    )


__all__ = ["make_eisenstein_row_quotient_candidate_theorems"]
