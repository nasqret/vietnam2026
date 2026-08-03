"""Complementary beta-bit prefixes have counts summing to their length.

This is the finite-cardinality identity needed by rectangle partitions: at
every bounded position exactly one of two decoded bits is one.  The proof uses
ordinary induction and the existing relational ``BitCount`` decomposition;
it never identifies raw beta codes.

The theorem is an isolated dependency-curried candidate.  Its displayed
relations expand to first-order Peano arithmetic before kernel checking, and
it is neither registered nor admitted here.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, bit_count


def make_finite_bitcount_complement_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact complementary-count identity."""

    left_count = bit_count("b", "c", "l", "n", tag="complement_left")
    right_count = bit_count("z", "e", "l", "m", tag="complement_right")
    left_entry = beta_at("b", "c", "i", "a", tag="complement_left_entry")
    right_entry = beta_at("z", "e", "i", "d", tag="complement_right_entry")
    complement = (
        "forall i a d. (exists h. h + S i = l) -> "
        f"({left_entry}) -> ({right_entry}) -> "
        "((a = 0 /\\ d = 1) \\/ (a = 1 /\\ d = 0))"
    )
    prefix_complement = (
        "forall i a d. (exists h. h + S i = l) -> "
        f"({beta_at('b', 'c', 'i', 'a', tag='complement_prefix_left')}) -> "
        f"({beta_at('z', 'e', 'i', 'd', tag='complement_prefix_right')}) -> "
        "((a = 0 /\\ d = 1) \\/ (a = 1 /\\ d = 0))"
    )
    left_last = beta_at("b", "c", "l", "a", tag="complement_left_last")
    left_prefix_count = bit_count(
        "b", "c", "l", "r", tag="complement_left_prefix"
    )
    left_decomposition = (
        f"exists a r. ({left_last}) /\\ (({left_prefix_count}) /\\ "
        "((a = 0 \\/ a = 1) /\\ n = r + a))"
    )
    right_last = beta_at("z", "e", "l", "d", tag="complement_right_last")
    right_prefix_count = bit_count(
        "z", "e", "l", "s", tag="complement_right_prefix"
    )
    right_decomposition = (
        f"exists d s. ({right_last}) /\\ (({right_prefix_count}) /\\ "
        "((d = 0 \\/ d = 1) /\\ m = s + d))"
    )

    return (
        spec(
            "complementary_bit_counts_add_length",
            "forall b c z e l n m. "
            f"({left_count}) -> ({right_count}) -> ({complement}) -> n + m = l",
            (
                "bit_count_zero",
                "bit_count_succ_decompose",
                "le_succ",
                "le_refl",
                "add_succ_left",
            ),
            (
                "intro b",
                "intro c",
                "intro z",
                "intro e",
                "induction l",
                "intro n",
                "intro m",
                "intro hleft",
                "intro hright",
                "intro hcomplement",
                "have hn : n = 0",
                "specialize bit_count_zero b",
                "specialize bit_count_zero c",
                "specialize bit_count_zero 0",
                "specialize bit_count_zero n",
                "apply bit_count_zero",
                "refl",
                "exact hleft",
                "have hm : m = 0",
                "specialize bit_count_zero z",
                "specialize bit_count_zero e",
                "specialize bit_count_zero 0",
                "specialize bit_count_zero m",
                "apply bit_count_zero",
                "refl",
                "exact hright",
                "rewrite hn",
                "rewrite hm",
                "simp",
                "intro n",
                "intro m",
                "intro hleft",
                "intro hright",
                "intro hcomplement",
                f"have hleft_decomp : {left_decomposition}",
                "specialize bit_count_succ_decompose b",
                "specialize bit_count_succ_decompose c",
                "specialize bit_count_succ_decompose l",
                "specialize bit_count_succ_decompose (S l)",
                "specialize bit_count_succ_decompose n",
                "apply bit_count_succ_decompose",
                "refl",
                "exact hleft",
                "cases hleft_decomp",
                "cases hleft_decomp_witness",
                "cases hleft_decomp_witness_witness",
                "cases hleft_decomp_witness_witness_right",
                "cases hleft_decomp_witness_witness_right_right",
                f"have hright_decomp : {right_decomposition}",
                "specialize bit_count_succ_decompose z",
                "specialize bit_count_succ_decompose e",
                "specialize bit_count_succ_decompose l",
                "specialize bit_count_succ_decompose (S l)",
                "specialize bit_count_succ_decompose m",
                "apply bit_count_succ_decompose",
                "refl",
                "exact hright",
                "cases hright_decomp",
                "cases hright_decomp_witness",
                "cases hright_decomp_witness_witness",
                "cases hright_decomp_witness_witness_right",
                "cases hright_decomp_witness_witness_right_right",
                f"have hprefix_complement : {prefix_complement}",
                "intro i",
                "intro a",
                "intro d",
                "intro hi",
                "intro ha",
                "intro hd",
                "specialize hcomplement i",
                "specialize hcomplement a",
                "specialize hcomplement d",
                "apply hcomplement",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact ha",
                "exact hd",
                "have hprefix : x1 + x3 = l",
                "specialize IH x1",
                "specialize IH x3",
                "apply IH",
                "exact hleft_decomp_witness_witness_right_left",
                "exact hright_decomp_witness_witness_right_left",
                "exact hprefix_complement",
                "have hlast : ((x = 0 /\\ x2 = 1) \\/ (x = 1 /\\ x2 = 0))",
                "specialize hcomplement l",
                "specialize hcomplement x",
                "specialize hcomplement x2",
                "apply hcomplement",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hleft_decomp_witness_witness_left",
                "exact hright_decomp_witness_witness_left",
                "rewrite hleft_decomp_witness_witness_right_right_right",
                "rewrite hright_decomp_witness_witness_right_right_right",
                "cases hlast",
                "cases hlast_left",
                "rewrite hlast_left_left",
                "rewrite hlast_left_right",
                "simp",
                "cases hlast_right",
                "rewrite hlast_right_left",
                "rewrite hlast_right_right",
                "simp",
                "specialize add_succ_left x1",
                "specialize add_succ_left x3",
                "trans S (x1 + x3)",
                "exact add_succ_left",
                "rewrite hprefix",
                "refl",
            ),
            "Complementary decoded bit prefixes have counts summing to their length.",
        ),
    )


__all__ = ["make_finite_bitcount_complement_candidate_theorems"]
