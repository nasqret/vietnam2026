"""Transport the Eisenstein quotient sum to the semantic rectangle total.

The quotient beta prefix and the outer rectangle beta prefix use unrelated raw
codes.  Their bounded entries nevertheless agree: the outer entry is a
semantic row ``BitCount``, and the row-quotient bridge identifies that count
with the quotient decoded at the same row.  Exact pointwise agreement lets the
checked beta-sum transport theorem reuse the quotient sum trace for the outer
prefix.  Sum functionality then identifies any independently supplied outer
rectangle total with the quotient-sum endpoint.

Every displayed relation expands before parsing to unchanged first-order
Peano arithmetic.  These candidates are dependency-curried, constructive,
unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_division_threshold_candidate import _lt_term
from .eisenstein_rectangle_count_candidate import (
    eisenstein_rectangle_row_count_prefix,
    eisenstein_row_count_witness,
)
from .eisenstein_scaled_division_candidate import scaled_successor_prefix
from .fermat_residue_product_candidate import prime
from .finite_division_prefix_candidate import division_prefix
from .finite_fold_surface import beta_at, sum_relation


def make_eisenstein_outer_sum_bridge_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build entry agreement, sum transport, and endpoint equality."""

    prime_p = prime("p", tag="outer_sum_bridge_prime_p")
    prime_q = prime("q", tag="outer_sum_bridge_prime_q")
    row_bound = _lt_term(
        "i",
        "h",
        tag="outer_sum_bridge_row_bound",
        variables=(
            "p", "q", "h", "k", "i", "tb", "tc", "qb", "qc", "ub", "uc",
            "cb", "cc", "d",
        ),
    )
    scaled_prefix = scaled_successor_prefix(
        "q", "tb", "tc", "h", tag="outer_sum_bridge_scaled"
    )
    divisions = division_prefix(
        "p",
        "tb",
        "tc",
        "qb",
        "qc",
        "ub",
        "uc",
        "h",
        tag="outer_sum_bridge_division",
    )
    rectangle_prefix = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "cb", "cc", "h", tag="outer_sum_bridge_rectangle"
    )
    quotient_entry = beta_at(
        "qb", "qc", "i", "d", tag="outer_sum_bridge_quotient_entry"
    )
    rectangle_entry = beta_at(
        "cb", "cc", "i", "d", tag="outer_sum_bridge_rectangle_entry"
    )
    quotient_sum = sum_relation(
        "qb", "qc", "h", "Q", tag="outer_sum_bridge_quotient_sum"
    )
    transported_rectangle_sum = sum_relation(
        "cb", "cc", "h", "Q", tag="outer_sum_bridge_transported_sum"
    )
    rectangle_total = sum_relation(
        "cb", "cc", "h", "T", tag="outer_sum_bridge_rectangle_total"
    )

    stored_entry = beta_at(
        "cb", "cc", "i", "n", tag="outer_sum_bridge_stored_entry"
    )
    stored_semantics = eisenstein_row_count_witness(
        "p", "q", "k", "i", "n", tag="outer_sum_bridge_stored_semantics"
    )
    stored_package = (
        f"exists n. (({stored_entry}) /\\ ({stored_semantics}))"
    )

    preservation_bound = _lt_term(
        "i",
        "h",
        tag="outer_sum_bridge_preservation_bound",
        variables=(
            "p", "q", "h", "k", "tb", "tc", "qb", "qc", "ub", "uc",
            "cb", "cc", "Q", "i", "a",
        ),
    )
    preservation_source = beta_at(
        "qb", "qc", "i", "a", tag="outer_sum_bridge_preservation_source"
    )
    preservation_target = beta_at(
        "cb", "cc", "i", "a", tag="outer_sum_bridge_preservation_target"
    )
    preservation = (
        f"forall i a. ({preservation_bound}) -> ({preservation_source}) -> "
        f"({preservation_target})"
    )

    common = (
        "p = 2 * h + 1 -> q = 2 * k + 1 -> "
        f"({prime_p}) -> ({prime_q}) -> ~(p = q) -> "
    )

    return (
        spec(
            "distinct_odd_prime_quotient_entry_matches_rectangle",
            "forall p q h k i tb tc qb qc ub uc cb cc d. "
            f"{common}({row_bound}) -> ({scaled_prefix}) -> ({divisions}) -> "
            f"({rectangle_prefix}) -> ({quotient_entry}) -> ({rectangle_entry})",
            ("distinct_odd_prime_semantic_row_equals_decoded_quotient",),
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
                "intro cb",
                "intro cc",
                "intro d",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hi",
                "intro hscaled",
                "intro hdivisions",
                "intro hrectangle",
                "intro hdentry",
                f"have hstored : {stored_package}",
                "specialize hrectangle i",
                "apply hrectangle",
                "exact hi",
                "cases hstored",
                "cases hstored_witness",
                "have hnd : x = d",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient p",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient q",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient h",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient k",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient i",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient tb",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient tc",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient qb",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient qc",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient ub",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient uc",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient x",
                "specialize distinct_odd_prime_semantic_row_equals_decoded_quotient d",
                "apply distinct_odd_prime_semantic_row_equals_decoded_quotient",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hi",
                "exact hscaled",
                "exact hdivisions",
                "exact hstored_witness_right",
                "exact hdentry",
                "rewrite hnd at hstored_witness_left",
                "rewrite hnd at hstored_witness_left",
                "exact hstored_witness_left",
            ),
            "Every decoded quotient entry is the corresponding semantic rectangle entry.",
        ),
        spec(
            "distinct_odd_prime_quotient_sum_transports_to_rectangle",
            "forall p q h k tb tc qb qc ub uc cb cc Q. "
            f"{common}({scaled_prefix}) -> ({divisions}) -> ({rectangle_prefix}) -> "
            f"({quotient_sum}) -> ({transported_rectangle_sum})",
            (
                "distinct_odd_prime_quotient_entry_matches_rectangle",
                "beta_sum_transport_prefix",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro tb",
                "intro tc",
                "intro qb",
                "intro qc",
                "intro ub",
                "intro uc",
                "intro cb",
                "intro cc",
                "intro Q",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hscaled",
                "intro hdivisions",
                "intro hrectangle",
                "intro hquotient_sum",
                f"have hpreservation : {preservation}",
                "intro i",
                "intro a",
                "intro hi",
                "intro ha",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle p",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle q",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle h",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle k",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle i",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle tb",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle tc",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle qb",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle qc",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle ub",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle uc",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle cb",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle cc",
                "specialize distinct_odd_prime_quotient_entry_matches_rectangle a",
                "apply distinct_odd_prime_quotient_entry_matches_rectangle",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hi",
                "exact hscaled",
                "exact hdivisions",
                "exact hrectangle",
                "exact ha",
                "specialize beta_sum_transport_prefix qb",
                "specialize beta_sum_transport_prefix qc",
                "specialize beta_sum_transport_prefix cb",
                "specialize beta_sum_transport_prefix cc",
                "specialize beta_sum_transport_prefix h",
                "specialize beta_sum_transport_prefix Q",
                "apply beta_sum_transport_prefix",
                "exact hquotient_sum",
                "exact hpreservation",
            ),
            "The quotient Sum trace transports exactly to the semantic rectangle prefix.",
        ),
        spec(
            "distinct_odd_prime_quotient_sum_equals_rectangle_total",
            "forall p q h k tb tc qb qc ub uc cb cc Q T. "
            f"{common}({scaled_prefix}) -> ({divisions}) -> ({rectangle_prefix}) -> "
            f"({quotient_sum}) -> ({rectangle_total}) -> Q = T",
            (
                "distinct_odd_prime_quotient_sum_transports_to_rectangle",
                "beta_sum_functional",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro tb",
                "intro tc",
                "intro qb",
                "intro qc",
                "intro ub",
                "intro uc",
                "intro cb",
                "intro cc",
                "intro Q",
                "intro T",
                "intro hpodd",
                "intro hqodd",
                "intro hp",
                "intro hq",
                "intro hpq",
                "intro hscaled",
                "intro hdivisions",
                "intro hrectangle",
                "intro hquotient_sum",
                "intro hrectangle_sum",
                f"have htransported : {transported_rectangle_sum}",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle p",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle q",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle h",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle k",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle tb",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle tc",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle qb",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle qc",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle ub",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle uc",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle cb",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle cc",
                "specialize distinct_odd_prime_quotient_sum_transports_to_rectangle Q",
                "apply distinct_odd_prime_quotient_sum_transports_to_rectangle",
                "exact hpodd",
                "exact hqodd",
                "exact hp",
                "exact hq",
                "exact hpq",
                "exact hscaled",
                "exact hdivisions",
                "exact hrectangle",
                "exact hquotient_sum",
                "specialize beta_sum_functional cb",
                "specialize beta_sum_functional cc",
                "specialize beta_sum_functional h",
                "specialize beta_sum_functional Q",
                "specialize beta_sum_functional T",
                "apply beta_sum_functional",
                "exact htransported",
                "exact hrectangle_sum",
            ),
            "The quotient floor-sum endpoint equals the independently summed semantic rectangle total.",
        ),
    )


__all__ = ["make_eisenstein_outer_sum_bridge_candidate_theorems"]
