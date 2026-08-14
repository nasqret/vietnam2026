"""Zero boundary law for the relational central-binomial surface.

``CentralBinom(0,z)`` remains authoring-only notation for
``Choose(0 + 0,0,z)``.  The notation is expanded before parsing, and this
module creates no trusted primitive, authority enrollment, or checked-use
grant.
"""

from __future__ import annotations

from typing import Any, Callable

from peano_lab.library.bertrand_central_binom_candidate import (
    _central_binom_relation_term,
)


CENTRAL_BINOM_ZERO = "central_binom_zero"


def make_bertrand_central_binom_zero_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated central-binomial zero boundary candidate."""

    relation = _central_binom_relation_term(
        "0",
        "z",
        tag="bcbz_source",
        variables=("z",),
    )
    return (
        spec(
            CENTRAL_BINOM_ZERO,
            f"forall z. ({relation}) -> z = 1",
            ("choose_zero",),
            (
                "intro z",
                "intro hcentral",
                "specialize choose_zero (0 + 0)",
                "specialize choose_zero z",
                "apply choose_zero",
                "exact hcentral",
            ),
            "The zeroth relational central-binomial value is one.",
        ),
    )


__all__ = ["make_bertrand_central_binom_zero_candidate_theorems"]
