"""K4 relational-gcd client for the canonical signed Bezout bridge.

The strict-K3 ``SignedBezout`` bridge deliberately does not depend on the
division-backed public gcd development.  This isolated client composes the
public balanced-Bezout existence theorem with that bridge and exposes signed
coefficient codes for a relational gcd.  It is constructive,
dependency-curried, unregistered, and unadmitted.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.ha_signed_bezout_candidate import signed_bezout


def make_ha_signed_bezout_gcd_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated K4 signed-Bezout client theorem."""

    gcd_relation = (
        "(((exists u. a = d * u) /\\ (exists v. b = d * v)) /\\ "
        "forall c. (exists s. a = c * s) -> "
        "(exists t. b = c * t) -> exists w. d = c * w)"
    )
    signed_relation = signed_bezout(
        "d", "a", "b", "x", "y", tag="gcd"
    )

    return (
        spec(
            "gcd_signed_bezout_exists",
            f"forall a b. exists d x y. ({gcd_relation} /\\ "
            f"({signed_relation}))",
            (
                "gcd_balanced_bezout_exists",
                "balanced_bezout_to_signed_bezout",
            ),
            (
                "intro a",
                "intro b",
                "specialize gcd_balanced_bezout_exists a",
                "specialize gcd_balanced_bezout_exists b",
                "cases gcd_balanced_bezout_exists",
                "cases gcd_balanced_bezout_exists_witness",
                "have hsigned : exists xcode ycode. "
                f"({signed_bezout('x', 'a', 'b', 'xcode', 'ycode', tag='gcd_bridge')})",
                "specialize balanced_bezout_to_signed_bezout x",
                "specialize balanced_bezout_to_signed_bezout a",
                "specialize balanced_bezout_to_signed_bezout b",
                "apply balanced_bezout_to_signed_bezout",
                "exact gcd_balanced_bezout_exists_witness_right",
                "cases hsigned",
                "cases hsigned_witness",
                "exists x",
                "exists x1",
                "exists x2",
                "split",
                "exact gcd_balanced_bezout_exists_witness_left",
                "exact hsigned_witness_witness",
            ),
            "Every pair has a relational gcd together with canonical signed "
            "Bezout coefficient codes.",
        ),
    )


__all__ = ["make_ha_signed_bezout_gcd_candidate_theorems"]
