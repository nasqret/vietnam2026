"""Constructive parity classification for a sum.

The core parity ladder supplies forward closure laws.  Quadratic reciprocity
also needs their constructive converses: an even sum has equal-parity
summands, while an odd sum has opposite-parity summands.  The proofs split the
two explicit ``parity_cases`` witnesses and reject the impossible branches by
the checked even/odd exclusivity lemmas.

These isolated candidates expand parity to ordinary existential equations in
first-order PA.  They are dependency-curried authoring evidence only and are
not registered or admitted here.
"""

from __future__ import annotations

from typing import Any, Callable


def _even(term: str, *, tag: str) -> str:
    return f"exists psc_even_{tag}. {term} = 2 * psc_even_{tag}"


def _odd(term: str, *, tag: str) -> str:
    return f"exists psc_odd_{tag}. {term} = 2 * psc_odd_{tag} + 1"


def make_parity_sum_classification_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build classifiers and iff packages for sum parity."""

    even_sum = _even("m + n", tag="even_sum")
    odd_sum = _odd("m + n", tag="odd_sum")
    even_m = _even("m", tag="even_m")
    odd_m = _odd("m", tag="odd_m")
    even_n = _even("n", tag="even_n")
    odd_n = _odd("n", tag="odd_n")
    same = f"((({even_m}) /\\ ({even_n})) \\/ (({odd_m}) /\\ ({odd_n})))"
    opposite = (
        f"((({even_m}) /\\ ({odd_n})) \\/ (({odd_m}) /\\ ({even_n})))"
    )

    return (
        spec(
            "even_sum_parity_cases",
            f"forall m n. ({even_sum}) -> ({same})",
            (
                "parity_cases",
                "even_add_odd",
                "odd_add_even",
                "even_not_odd",
            ),
            (
                "intro m",
                "intro n",
                "intro hsum",
                "have hm : exists a. m = 2 * a \\/ m = 2 * a + 1",
                "specialize parity_cases m",
                "exact parity_cases",
                "have hn : exists b. n = 2 * b \\/ n = 2 * b + 1",
                "specialize parity_cases n",
                "exact parity_cases",
                "cases hm",
                "cases hn",
                "cases hm_witness",
                "cases hn_witness",
                "left",
                "split",
                "exists x",
                "exact hm_witness_left",
                "exists x1",
                "exact hn_witness_left",
                "exfalso",
                "have hodd : exists c. m + n = 2 * c + 1",
                "specialize even_add_odd m",
                "specialize even_add_odd n",
                "apply even_add_odd",
                "exists x",
                "exact hm_witness_left",
                "exists x1",
                "exact hn_witness_right",
                "specialize even_not_odd (m + n)",
                "apply even_not_odd",
                "exact hsum",
                "exact hodd",
                "cases hn_witness",
                "exfalso",
                "have hodd : exists c. m + n = 2 * c + 1",
                "specialize odd_add_even m",
                "specialize odd_add_even n",
                "apply odd_add_even",
                "exists x",
                "exact hm_witness_right",
                "exists x1",
                "exact hn_witness_left",
                "specialize even_not_odd (m + n)",
                "apply even_not_odd",
                "exact hsum",
                "exact hodd",
                "right",
                "split",
                "exists x",
                "exact hm_witness_right",
                "exists x1",
                "exact hn_witness_right",
            ),
            "An even sum has summands of the same parity.",
        ),
        spec(
            "odd_sum_parity_cases",
            f"forall m n. ({odd_sum}) -> ({opposite})",
            (
                "parity_cases",
                "even_add_even",
                "odd_add_odd",
                "odd_not_even",
            ),
            (
                "intro m",
                "intro n",
                "intro hsum",
                "have hm : exists a. m = 2 * a \\/ m = 2 * a + 1",
                "specialize parity_cases m",
                "exact parity_cases",
                "have hn : exists b. n = 2 * b \\/ n = 2 * b + 1",
                "specialize parity_cases n",
                "exact parity_cases",
                "cases hm",
                "cases hn",
                "cases hm_witness",
                "cases hn_witness",
                "exfalso",
                "have heven : exists c. m + n = 2 * c",
                "specialize even_add_even m",
                "specialize even_add_even n",
                "apply even_add_even",
                "exists x",
                "exact hm_witness_left",
                "exists x1",
                "exact hn_witness_left",
                "specialize odd_not_even (m + n)",
                "apply odd_not_even",
                "exact hsum",
                "exact heven",
                "left",
                "split",
                "exists x",
                "exact hm_witness_left",
                "exists x1",
                "exact hn_witness_right",
                "cases hn_witness",
                "right",
                "split",
                "exists x",
                "exact hm_witness_right",
                "exists x1",
                "exact hn_witness_left",
                "exfalso",
                "have heven : exists c. m + n = 2 * c",
                "specialize odd_add_odd m",
                "specialize odd_add_odd n",
                "apply odd_add_odd",
                "exists x",
                "exact hm_witness_right",
                "exists x1",
                "exact hn_witness_right",
                "specialize odd_not_even (m + n)",
                "apply odd_not_even",
                "exact hsum",
                "exact heven",
            ),
            "An odd sum has summands of opposite parity.",
        ),
        spec(
            "even_sum_iff_same_parity",
            f"forall m n. ((({even_sum}) -> ({same})) /\\ (({same}) -> ({even_sum})))",
            (
                "even_sum_parity_cases",
                "even_add_even",
                "odd_add_odd",
            ),
            (
                "intro m",
                "intro n",
                "split",
                "intro hsum",
                "specialize even_sum_parity_cases m",
                "specialize even_sum_parity_cases n",
                "apply even_sum_parity_cases",
                "exact hsum",
                "intro hsame",
                "cases hsame",
                "cases hsame_left",
                "specialize even_add_even m",
                "specialize even_add_even n",
                "apply even_add_even",
                "exact hsame_left_left",
                "exact hsame_left_right",
                "cases hsame_right",
                "specialize odd_add_odd m",
                "specialize odd_add_odd n",
                "apply odd_add_odd",
                "exact hsame_right_left",
                "exact hsame_right_right",
            ),
            "A sum is even exactly when its summands have the same parity.",
        ),
        spec(
            "odd_sum_iff_opposite_parity",
            f"forall m n. ((({odd_sum}) -> ({opposite})) /\\ "
            f"(({opposite}) -> ({odd_sum})))",
            (
                "odd_sum_parity_cases",
                "even_add_odd",
                "odd_add_even",
            ),
            (
                "intro m",
                "intro n",
                "split",
                "intro hsum",
                "specialize odd_sum_parity_cases m",
                "specialize odd_sum_parity_cases n",
                "apply odd_sum_parity_cases",
                "exact hsum",
                "intro hopposite",
                "cases hopposite",
                "cases hopposite_left",
                "specialize even_add_odd m",
                "specialize even_add_odd n",
                "apply even_add_odd",
                "exact hopposite_left_left",
                "exact hopposite_left_right",
                "cases hopposite_right",
                "specialize odd_add_even m",
                "specialize odd_add_even n",
                "apply odd_add_even",
                "exact hopposite_right_left",
                "exact hopposite_right_right",
            ),
            "A sum is odd exactly when its summands have opposite parity.",
        ),
    )


__all__ = ["make_parity_sum_classification_candidate_theorems"]
