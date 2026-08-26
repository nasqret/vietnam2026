"""Sealed three-row constructor projection for the Bertrand campaign.

Alpha v6 already byte-binds the original eight-row Eisenstein candidate
factory, so this module leaves that source untouched.  It projects the three
previously unenrolled constructor rows and removes the two unused dependency
declarations from ``eisenstein_initial_segment_prefix_exists``.  Statements,
tactic scripts, and summaries remain byte-for-byte identical to the original
candidate specifications; this is dependency-surface curation only.

The rows remain isolated dependency-curried candidates.  This module neither
registers nor admits a theorem and introduces no kernel rule or classical
principle.
"""

from __future__ import annotations

from typing import Any, Callable

from .eisenstein_initial_segment_count_candidate import (
    make_eisenstein_initial_segment_count_candidate_theorems,
)
from .theorems import TheoremSpec


class BertrandInitialSegmentConstructorError(ValueError):
    """The sealed upstream factory or its constructor projection changed."""


SOURCE_FACTORY_NAMES = (
    "eisenstein_initial_segment_indicator_choice",
    "eisenstein_initial_segment_prefix_extend",
    "eisenstein_initial_segment_prefix_exists",
    "eisenstein_initial_segment_prefix_all_bits",
    "eisenstein_initial_segment_decoded_choice",
    "beta_all_one_bit_count_exact",
    "eisenstein_initial_segment_bit_count_functional",
    "eisenstein_initial_segment_bit_count_exact",
)

BERTRAND_INITIAL_SEGMENT_CONSTRUCTOR_NAMES = SOURCE_FACTORY_NAMES[:3]

ORIGINAL_PREFIX_EXISTS_DEPENDENCIES = (
    "add_eq_zero_right",
    "succ_ne_zero",
    "le_succ",
    "le_refl",
    "eisenstein_initial_segment_indicator_choice",
    "eisenstein_initial_segment_prefix_extend",
)

LIVE_PREFIX_EXISTS_DEPENDENCIES = (
    "add_eq_zero_right",
    "succ_ne_zero",
    "eisenstein_initial_segment_indicator_choice",
    "eisenstein_initial_segment_prefix_extend",
)


def make_bertrand_initial_segment_constructor_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Return the exact three-row projection with its live dependency surface."""

    source = make_eisenstein_initial_segment_count_candidate_theorems(
        TheoremSpec
    )
    if tuple(item.name for item in source) != SOURCE_FACTORY_NAMES:
        raise BertrandInitialSegmentConstructorError(
            "the sealed Eisenstein source factory changed rows or order"
        )
    first, second, third = source[:3]
    if third.dependencies != ORIGINAL_PREFIX_EXISTS_DEPENDENCIES:
        raise BertrandInitialSegmentConstructorError(
            "the sealed prefix-existence dependency surface changed"
        )
    if any(
        "DNE" in command
        for item in (first, second, third)
        for command in item.script
    ):
        raise BertrandInitialSegmentConstructorError(
            "the constructor projection contains DNE"
        )

    return (
        spec(
            first.name,
            first.statement,
            first.dependencies,
            first.script,
            first.summary,
        ),
        spec(
            second.name,
            second.statement,
            second.dependencies,
            second.script,
            second.summary,
        ),
        spec(
            third.name,
            third.statement,
            LIVE_PREFIX_EXISTS_DEPENDENCIES,
            third.script,
            third.summary,
        ),
    )


__all__ = [
    "BERTRAND_INITIAL_SEGMENT_CONSTRUCTOR_NAMES",
    "BertrandInitialSegmentConstructorError",
    "LIVE_PREFIX_EXISTS_DEPENDENCIES",
    "ORIGINAL_PREFIX_EXISTS_DEPENDENCIES",
    "SOURCE_FACTORY_NAMES",
    "make_bertrand_initial_segment_constructor_candidate_theorems",
]
