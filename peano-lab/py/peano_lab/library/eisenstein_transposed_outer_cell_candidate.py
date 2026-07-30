"""Expose complementary inner bits from two transposed rectangle prefixes.

The existing rectangle layer stores only each row count in its outer beta
prefix; the inner row code remains existential semantic evidence.  This
candidate decodes one outer entry in each orientation, opens both inner rows,
decodes the transposed cell entries, and packages their exact complementarity.

It is a representation bridge toward a later nested transpose/Fubini theorem,
not that theorem itself.  Every relation expands to unchanged first-order PA;
the candidate remains dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_rectangle_count_candidate import (
    eisenstein_rectangle_row_count_prefix,
    eisenstein_row_count_witness,
)
from .eisenstein_row_indicator_candidate import eisenstein_row_indicator_prefix
from .finite_fold_surface import beta_at, bit_count


def make_eisenstein_transposed_outer_cell_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build one semantic transposed-cell witness from two outer prefixes."""

    first_outer = eisenstein_rectangle_row_count_prefix(
        "p", "q", "k", "ab", "ac", "h", tag="outer_cell_first"
    )
    second_outer = eisenstein_rectangle_row_count_prefix(
        "q", "p", "h", "bb", "bc", "k", tag="outer_cell_second"
    )
    first_outer_entry = beta_at(
        "ab", "ac", "i", "n", tag="outer_cell_first_entry"
    )
    second_outer_entry = beta_at(
        "bb", "bc", "j", "m", tag="outer_cell_second_entry"
    )
    first_semantic = eisenstein_row_count_witness(
        "p", "q", "k", "i", "n", tag="outer_cell_first_semantic"
    )
    second_semantic = eisenstein_row_count_witness(
        "q", "p", "h", "j", "m", tag="outer_cell_second_semantic"
    )
    first_row = eisenstein_row_indicator_prefix(
        "p", "q", "i", "rb", "rc", "k", tag="outer_cell_first_row"
    )
    first_count = bit_count(
        "rb", "rc", "k", "n", tag="outer_cell_first_count"
    )
    first_entry = beta_at(
        "rb", "rc", "j", "a", tag="outer_cell_first_inner_entry"
    )
    second_row = eisenstein_row_indicator_prefix(
        "q", "p", "j", "cb", "cc", "h", tag="outer_cell_second_row"
    )
    second_count = bit_count(
        "cb", "cc", "h", "m", tag="outer_cell_second_count"
    )
    second_entry = beta_at(
        "cb", "cc", "i", "d", tag="outer_cell_second_inner_entry"
    )
    result = (
        "exists rb rc cb cc a d. "
        f"(({first_row}) /\\ (({first_count}) /\\ (({first_entry}) /\\ "
        f"(({second_row}) /\\ (({second_count}) /\\ (({second_entry}) /\\ "
        "((a = 0 /\\ d = 1) \\/ (a = 1 /\\ d = 0))))))))"
    )

    return (
        spec(
            "eisenstein_transposed_outer_prefix_cell_witness",
            "forall p q h k ab ac bb bc i j n m. "
            f"({first_outer}) -> ({second_outer}) -> "
            "(exists gap. gap + S i = h) -> "
            "(exists gap. gap + S j = k) -> "
            f"({first_outer_entry}) -> ({second_outer_entry}) -> ({result})",
            (
                "eisenstein_rectangle_decoded_row_count",
                "beta_at_exists",
                "eisenstein_transposed_decoded_cell_bits_complementary",
            ),
            (
                "intro p",
                "intro q",
                "intro h",
                "intro k",
                "intro ab",
                "intro ac",
                "intro bb",
                "intro bc",
                "intro i",
                "intro j",
                "intro n",
                "intro m",
                "intro hfirst_outer",
                "intro hsecond_outer",
                "intro hi",
                "intro hj",
                "intro hn",
                "intro hm",
                f"have hfirst : {first_semantic}",
                "specialize eisenstein_rectangle_decoded_row_count p",
                "specialize eisenstein_rectangle_decoded_row_count q",
                "specialize eisenstein_rectangle_decoded_row_count k",
                "specialize eisenstein_rectangle_decoded_row_count ab",
                "specialize eisenstein_rectangle_decoded_row_count ac",
                "specialize eisenstein_rectangle_decoded_row_count h",
                "specialize eisenstein_rectangle_decoded_row_count i",
                "specialize eisenstein_rectangle_decoded_row_count n",
                "apply eisenstein_rectangle_decoded_row_count",
                "exact hfirst_outer",
                "exact hi",
                "exact hn",
                "cases hfirst",
                "cases hfirst_witness",
                "cases hfirst_witness_witness",
                f"have hsecond : {second_semantic}",
                "specialize eisenstein_rectangle_decoded_row_count q",
                "specialize eisenstein_rectangle_decoded_row_count p",
                "specialize eisenstein_rectangle_decoded_row_count h",
                "specialize eisenstein_rectangle_decoded_row_count bb",
                "specialize eisenstein_rectangle_decoded_row_count bc",
                "specialize eisenstein_rectangle_decoded_row_count k",
                "specialize eisenstein_rectangle_decoded_row_count j",
                "specialize eisenstein_rectangle_decoded_row_count m",
                "apply eisenstein_rectangle_decoded_row_count",
                "exact hsecond_outer",
                "exact hj",
                "exact hm",
                "cases hsecond",
                "cases hsecond_witness",
                "cases hsecond_witness_witness",
                f"have hfirst_entry : exists a. ({beta_at('x', 'x1', 'j', 'a', tag='outer_cell_first_exists')})",
                "specialize beta_at_exists x",
                "specialize beta_at_exists x1",
                "specialize beta_at_exists j",
                "exact beta_at_exists",
                "cases hfirst_entry",
                f"have hsecond_entry : exists d. ({beta_at('x2', 'x3', 'i', 'd', tag='outer_cell_second_exists')})",
                "specialize beta_at_exists x2",
                "specialize beta_at_exists x3",
                "specialize beta_at_exists i",
                "exact beta_at_exists",
                "cases hsecond_entry",
                "have hcomplement : ((x4 = 0 /\\ x5 = 1) \\/ (x4 = 1 /\\ x5 = 0))",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary p",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary q",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary h",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary k",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary i",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary j",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary x",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary x1",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary x2",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary x3",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary x4",
                "specialize eisenstein_transposed_decoded_cell_bits_complementary x5",
                "apply eisenstein_transposed_decoded_cell_bits_complementary",
                "exact hfirst_witness_witness_left",
                "exact hsecond_witness_witness_left",
                "exact hj",
                "exact hi",
                "exact hfirst_entry_witness",
                "exact hsecond_entry_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "exists x4",
                "exists x5",
                "split",
                "exact hfirst_witness_witness_left",
                "split",
                "exact hfirst_witness_witness_right",
                "split",
                "exact hfirst_entry_witness",
                "split",
                "exact hsecond_witness_witness_left",
                "split",
                "exact hsecond_witness_witness_right",
                "split",
                "exact hsecond_entry_witness",
                "exact hcomplement",
            ),
            "Two transposed outer entries expose complementary decoded inner cell bits.",
        ),
    )


__all__ = ["make_eisenstein_transposed_outer_cell_candidate_theorems"]
