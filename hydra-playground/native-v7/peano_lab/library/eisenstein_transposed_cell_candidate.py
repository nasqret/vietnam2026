"""Pointwise complementarity of transposed Eisenstein row indicators.

An indicator row for ``(p,q)`` records one at ``(i,j)`` exactly when
``p*(j+1) < q*(i+1)``.  The row with swapped parameters ``(q,p)`` records the
opposite strict orientation at the transposed cell ``(j,i)``.  Consequently
their decoded bits are exact complements.

The proof consumes only the semantic row-prefix contracts; primality and
noncollision were already used when those prefixes were constructed.  The
candidate expands to unchanged first-order PA and remains unregistered and
unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_row_indicator_candidate import (
    eisenstein_cell_indicator_choice,
    eisenstein_row_indicator_prefix,
)
from .finite_fold_surface import beta_at


def make_eisenstein_transposed_cell_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build decoded complementarity for one transposed lattice cell."""

    row = eisenstein_row_indicator_prefix(
        "p", "q", "i", "rb", "rc", "k", tag="transpose_row"
    )
    transposed_row = eisenstein_row_indicator_prefix(
        "q", "p", "j", "cb", "cc", "h", tag="transpose_column"
    )
    row_entry = beta_at("rb", "rc", "j", "a", tag="transpose_row_entry")
    transposed_entry = beta_at(
        "cb", "cc", "i", "d", tag="transpose_column_entry"
    )
    row_choice = eisenstein_cell_indicator_choice(
        "p", "q", "i", "j", "a", tag="transpose_row_choice"
    )
    transposed_choice = eisenstein_cell_indicator_choice(
        "q", "p", "j", "i", "d", tag="transpose_column_choice"
    )

    return (
        spec(
            "eisenstein_transposed_decoded_cell_bits_complementary",
            "forall p q h k i j rb rc cb cc a d. "
            f"({row}) -> ({transposed_row}) -> "
            "(exists gap. gap + S j = k) -> "
            "(exists gap. gap + S i = h) -> "
            f"({row_entry}) -> ({transposed_entry}) -> "
            "((a = 0 /\\ d = 1) \\/ (a = 1 /\\ d = 0))",
            ("eisenstein_row_indicator_decoded_choice",),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro i",
                "intro j",
                "intro rb",
                "intro rc",
                "intro cb",
                "intro cc",
                "intro a",
                "intro d",
                "intro hrow",
                "intro htransposed_row",
                "intro hj",
                "intro hi",
                "intro ha",
                "intro hd",
                f"have horiginal : {row_choice}",
                "specialize eisenstein_row_indicator_decoded_choice p",
                "specialize eisenstein_row_indicator_decoded_choice q",
                "specialize eisenstein_row_indicator_decoded_choice i",
                "specialize eisenstein_row_indicator_decoded_choice rb",
                "specialize eisenstein_row_indicator_decoded_choice rc",
                "specialize eisenstein_row_indicator_decoded_choice k",
                "specialize eisenstein_row_indicator_decoded_choice j",
                "specialize eisenstein_row_indicator_decoded_choice a",
                "apply eisenstein_row_indicator_decoded_choice",
                "exact hrow",
                "exact hj",
                "exact ha",
                f"have htransposed : {transposed_choice}",
                "specialize eisenstein_row_indicator_decoded_choice q",
                "specialize eisenstein_row_indicator_decoded_choice p",
                "specialize eisenstein_row_indicator_decoded_choice j",
                "specialize eisenstein_row_indicator_decoded_choice cb",
                "specialize eisenstein_row_indicator_decoded_choice cc",
                "specialize eisenstein_row_indicator_decoded_choice h",
                "specialize eisenstein_row_indicator_decoded_choice i",
                "specialize eisenstein_row_indicator_decoded_choice d",
                "apply eisenstein_row_indicator_decoded_choice",
                "exact htransposed_row",
                "exact hi",
                "exact hd",
                "cases horiginal",
                "cases horiginal_left",
                "cases horiginal_left_right",
                "cases htransposed",
                "cases htransposed_left",
                "cases htransposed_left_right",
                "exfalso",
                "apply horiginal_left_right_right",
                "exact htransposed_left_right_left",
                "cases htransposed_right",
                "left",
                "split",
                "exact horiginal_left_left",
                "exact htransposed_right_left",
                "cases horiginal_right",
                "cases horiginal_right_right",
                "cases htransposed",
                "cases htransposed_left",
                "right",
                "split",
                "exact horiginal_right_left",
                "exact htransposed_left_left",
                "cases htransposed_right",
                "cases htransposed_right_right",
                "exfalso",
                "apply horiginal_right_right_right",
                "exact htransposed_right_right_left",
            ),
            "A decoded cell bit and its swapped-row transpose are exact complements.",
        ),
    )


__all__ = ["make_eisenstein_transposed_cell_candidate_theorems"]
