"""Strict-HA parity prerequisites for canonical signed-natural codes.

The public parity ladder contains a pointwise even/odd exclusion theorem, but
its current proof travels through division-with-remainder uniqueness.  That
dependency points in the wrong direction for the signed-natural substrate:
signed codes belong to K3 while division belongs to K4.  This isolated module
therefore reproves the pointwise separation directly by induction, using only
the fixed PA axioms and the K1 ``zero_or_succ`` decomposition.

Both candidates are dependency-curried, constructive, unregistered, and
unadmitted.  Their statements use only the unchanged first-order language
``{0,S,+,*,=}``.
"""

from __future__ import annotations

from typing import Any, Callable


def make_ha_signed_parity_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build K1-only parity separation and uniqueness of an even half."""

    return (
        spec(
            "even_odd_exclusive_k1",
            "forall n even_half odd_half. n = 2 * even_half -> "
            "n = 2 * odd_half + 1 -> false",
            ("zero_or_succ",),
            (
                "intro n",
                "induction n",
                "intro even_half",
                "intro odd_half",
                "intro heven",
                "intro hodd",
                "rewrite PA4 at hodd",
                "rewrite PA3 at hodd",
                "apply PA1",
                "symm",
                "exact hodd",
                "intro even_half",
                "intro odd_half",
                "intro heven",
                "intro hodd",
                "rewrite PA4 at hodd",
                "rewrite PA3 at hodd",
                "have h_even_predecessor : n = 2 * odd_half",
                "apply PA2",
                "exact hodd",
                "specialize zero_or_succ even_half",
                "cases zero_or_succ",
                "rewrite zero_or_succ_left at heven",
                "rewrite PA5 at heven",
                "apply PA1",
                "exact heven",
                "cases zero_or_succ_right",
                "rewrite zero_or_succ_right_witness at heven",
                "rewrite PA6 at heven",
                "rewrite PA4 at heven",
                "have h_odd_predecessor : n = 2 * x + 1",
                "apply PA2",
                "exact heven",
                "specialize IH odd_half",
                "specialize IH x",
                "apply IH",
                "exact h_even_predecessor",
                "exact h_odd_predecessor",
            ),
            "A natural cannot have both an even and an odd half witness; the "
            "proof uses only induction and the zero-or-successor split.",
        ),
        spec(
            "even_half_unique",
            "forall n a b. n = 2 * a -> n = 2 * b -> a = b",
            ("mul_left_cancel_nonzero",),
            (
                "intro n",
                "intro a",
                "intro b",
                "intro ha",
                "intro hb",
                "have hm : 2 * a = 2 * b",
                "trans n",
                "symm",
                "exact ha",
                "exact hb",
                "specialize mul_left_cancel_nonzero 2",
                "specialize mul_left_cancel_nonzero a",
                "specialize mul_left_cancel_nonzero b",
                "apply mul_left_cancel_nonzero",
                "intro htwo",
                "apply PA1",
                "exact htwo",
                "exact hm",
            ),
            "The witness in an even decomposition is unique by cancellation "
            "of the nonzero factor two.",
        ),
    )


__all__ = ["make_ha_signed_parity_candidate_theorems"]
