"""Constructive closed-upper Bertrand capstone candidate.

The single row below splits at the frozen factorized cutoff ``16 * 32``.
The weak branch is discharged by the checked large-input theorem and the
strict branch by the native finite-cover theorem.  Its public statement is
the exact base-language BP01 source frozen by the campaign RFC.

This module is candidate evidence only.  It grants no registry authority or
edition membership.
"""

from __future__ import annotations

from typing import Any, Callable

from .bertrand_b7_eventual_candidate import (
    BERTRAND_EVENTUALLY_CLOSED_UPPER,
)
from .bertrand_b8_small_candidate import BERTRAND_SMALL_CLOSED_UPPER


BERTRAND_CLOSED_UPPER = "bertrand_closed_upper"

BERTRAND_CLOSED_UPPER_BASE_SOURCE = (
    "forall n. ~(n = 0) -> exists p. ((~(p = 1) /\\ "
    "forall a b. p = a * b -> a = 1 \\/ b = 1) /\\ "
    "((exists u. u + S n = p) /\\ "
    "(exists v. v + p = n + n)))"
)


def make_bertrand_bp01_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the exact BP01 cutoff-split candidate."""

    return (
        spec(
            BERTRAND_CLOSED_UPPER,
            BERTRAND_CLOSED_UPPER_BASE_SOURCE,
            (
                "le_or_lt",
                BERTRAND_EVENTUALLY_CLOSED_UPPER,
                BERTRAND_SMALL_CLOSED_UPPER,
            ),
            (
                "intro n",
                "intro hnonzero",
                "specialize le_or_lt (16 * 32)",
                "specialize le_or_lt n",
                "cases le_or_lt",
                f"specialize {BERTRAND_EVENTUALLY_CLOSED_UPPER} n",
                f"apply {BERTRAND_EVENTUALLY_CLOSED_UPPER}",
                "exact le_or_lt_left",
                f"specialize {BERTRAND_SMALL_CLOSED_UPPER} n",
                f"apply {BERTRAND_SMALL_CLOSED_UPPER}",
                "exact hnonzero",
                "exact le_or_lt_right",
            ),
            (
                "Every nonzero natural has a prime in its open-closed "
                "Bertrand interval."
            ),
        ),
    )


__all__ = [
    "BERTRAND_CLOSED_UPPER",
    "BERTRAND_CLOSED_UPPER_BASE_SOURCE",
    "make_bertrand_bp01_candidate_theorems",
]
