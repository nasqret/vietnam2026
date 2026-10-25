"""Algebraic join from two quotient/count congruences to one count sum.

The two Gauss--Eisenstein orientations eventually provide ``e == Q`` and
``f == U`` modulo two, while the native Fubini theorem provides the exact
identity ``Q+U=h*k``.  This isolated candidate performs only that final
balanced-congruence addition and rewrite.  It is expanded native PA and is
neither registered nor admitted.
"""

from __future__ import annotations

from typing import Any, Callable


def _mod_two(left: str, right: str, *, tag: str) -> str:
    return (
        f"exists gcsp_u_{tag} gcsp_v_{tag}. "
        f"{left} + 2 * gcsp_u_{tag} = {right} + 2 * gcsp_v_{tag}"
    )


def make_gauss_count_sum_parity_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact two-orientation modulo-two sum join."""

    e_q = _mod_two("e", "Q", tag="e_q")
    f_u = _mod_two("f", "U", tag="f_u")
    sum_qu = _mod_two("e + f", "Q + U", tag="sum_qu")
    sum_product = _mod_two("e + f", "h * k", tag="sum_product")

    return (
        spec(
            "gauss_count_sum_mod_two_from_quotient_sums",
            f"forall e f Q U h k. ({e_q}) -> ({f_u}) -> "
            f"Q + U = h * k -> ({sum_product})",
            ("mod_eq_add",),
            (
                "intro e", "intro f", "intro Q", "intro U", "intro h", "intro k",
                "intro heq", "intro hfu", "intro hsum",
                f"have hjoined : {sum_qu}",
                "specialize mod_eq_add 2",
                "specialize mod_eq_add e",
                "specialize mod_eq_add Q",
                "specialize mod_eq_add f",
                "specialize mod_eq_add U",
                "apply mod_eq_add",
                "exact heq",
                "exact hfu",
                "rewrite hsum at hjoined",
                "exact hjoined",
            ),
            "Two oriented count/quotient congruences plus the exact floor-sum identity give e+f == h*k modulo two.",
        ),
    )


__all__ = ["make_gauss_count_sum_parity_candidate_theorems"]
