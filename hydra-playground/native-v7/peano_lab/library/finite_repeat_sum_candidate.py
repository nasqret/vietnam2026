"""Exact sums of constant beta prefixes.

The conservative ``Repeat`` relation says that every bounded decoded entry is
the same natural value.  This tranche proves that any exact relational
``Sum`` of such a prefix equals ``length * value`` and packages existence of
the code, trace, and exact endpoint.  The proof is ordinary constructive
induction over the prefix length.

These candidates are dependency-curried authoring evidence.  Their contracts
expand before checking to the unchanged first-order Peano language, and they
are deliberately absent from the public theorem registry.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, repeat_relation, sum_relation


def _sum_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    entry = beta_at(code, scale, length, "a", tag=f"{tag}_entry")
    prefix = sum_relation(code, scale, length, "r", tag=f"{tag}_prefix")
    return f"exists a r. ({entry}) /\\ (({prefix}) /\\ {result} = r + a)"


def make_finite_repeat_sum_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build exact evaluation and existence for sums of Repeat prefixes."""

    repeated = repeat_relation("b", "c", "a", "l", tag="repeatsum_repeat")
    summed = sum_relation("b", "c", "l", "n", tag="repeatsum_sum")
    prefix_repeated = repeat_relation(
        "b", "c", "a", "l", tag="repeatsum_prefix_repeat"
    )
    decomposition = _sum_decomposition(
        "b", "c", "l", "n", tag="repeatsum_decomp"
    )
    exact_existence_repeat = repeat_relation(
        "b", "c", "a", "l", tag="repeatsum_exists_repeat"
    )
    exact_existence_sum = sum_relation(
        "b", "c", "l", "n", tag="repeatsum_exists_sum"
    )

    return (
        spec(
            "beta_repeat_sum_exact",
            f"forall b c a l n. ({repeated}) -> ({summed}) -> n = l * a",
            (
                "beta_sum_zero",
                "beta_sum_succ_decompose",
                "le_succ",
                "le_refl",
                "beta_repeat_entry_eq",
                "mul_zero_left",
                "mul_succ_left",
            ),
            (
                "intro b",
                "intro c",
                "intro a",
                "induction l",
                "intro n",
                "intro hrepeat",
                "intro hsum",
                "have hn : n = 0",
                "specialize beta_sum_zero b",
                "specialize beta_sum_zero c",
                "specialize beta_sum_zero n",
                "apply beta_sum_zero",
                "exact hsum",
                "rewrite hn",
                "symm",
                "specialize mul_zero_left a",
                "exact mul_zero_left",
                "intro n",
                "intro hrepeat",
                "intro hsum",
                f"have hdecomp : {decomposition}",
                "specialize beta_sum_succ_decompose b",
                "specialize beta_sum_succ_decompose c",
                "specialize beta_sum_succ_decompose l",
                "specialize beta_sum_succ_decompose n",
                "apply beta_sum_succ_decompose",
                "exact hsum",
                "cases hdecomp",
                "cases hdecomp_witness",
                "cases hdecomp_witness_witness",
                "cases hdecomp_witness_witness_right",
                f"have hprefix_repeat : {prefix_repeated}",
                "intro i",
                "intro hi",
                "specialize hrepeat i",
                "apply hrepeat",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "have hprefix : x1 = l * a",
                "specialize IH x1",
                "apply IH",
                "exact hprefix_repeat",
                "exact hdecomp_witness_witness_right_left",
                "have hlast : x = a",
                "specialize beta_repeat_entry_eq b",
                "specialize beta_repeat_entry_eq c",
                "specialize beta_repeat_entry_eq a",
                "specialize beta_repeat_entry_eq (S l)",
                "specialize beta_repeat_entry_eq l",
                "specialize beta_repeat_entry_eq x",
                "apply beta_repeat_entry_eq",
                "exact hrepeat",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hdecomp_witness_witness_left",
                "rewrite hdecomp_witness_witness_right_right",
                "rewrite hprefix",
                "rewrite hlast",
                "specialize mul_succ_left l",
                "specialize mul_succ_left a",
                "symm",
                "exact mul_succ_left",
            ),
            "A constant beta prefix has exact relational sum length times value.",
        ),
        spec(
            "beta_repeat_sum_exists_exact",
            "forall a l. exists b c n. "
            f"({exact_existence_repeat}) /\\ "
            f"(({exact_existence_sum}) /\\ n = l * a)",
            (
                "beta_repeat_exists",
                "beta_sum_exists",
                "beta_repeat_sum_exact",
            ),
            (
                "intro a",
                "intro l",
                f"have hrepeat : exists b c. ({exact_existence_repeat})",
                "specialize beta_repeat_exists a",
                "specialize beta_repeat_exists l",
                "exact beta_repeat_exists",
                "cases hrepeat",
                "cases hrepeat_witness",
                "have hsum : exists n. "
                f"({sum_relation('x', 'x1', 'l', 'n', tag='repeatsum_exists_trace')})",
                "specialize beta_sum_exists x",
                "specialize beta_sum_exists x1",
                "specialize beta_sum_exists l",
                "exact beta_sum_exists",
                "cases hsum",
                "have hexact : x2 = l * a",
                "specialize beta_repeat_sum_exact x",
                "specialize beta_repeat_sum_exact x1",
                "specialize beta_repeat_sum_exact a",
                "specialize beta_repeat_sum_exact l",
                "specialize beta_repeat_sum_exact x2",
                "apply beta_repeat_sum_exact",
                "exact hrepeat_witness_witness",
                "exact hsum_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "exact hrepeat_witness_witness",
                "split",
                "exact hsum_witness",
                "exact hexact",
            ),
            "Every value and length admit a constant prefix with its exact sum.",
        ),
    )


__all__ = ["make_finite_repeat_sum_candidate_theorems"]
