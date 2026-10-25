"""Thin current-registry adapter for the pure quadratic-reciprocity stack.

The core stack builder deliberately knows nothing about ``theorems.py``.
Existing campaign tools still need a convenient view over today's public
registry, so this module takes an immutable snapshot and injects the exact
``TheoremSpec`` type.  It does not register, replay, or admit any candidate.

Production enrollment must not import this adapter from ``theorems.py``.
Instead it should freeze its pre-QR tuple locally and call the pure builder
directly, avoiding a registry/adapter import cycle.
"""

from __future__ import annotations

from functools import lru_cache
from types import MappingProxyType

from .quadratic_reciprocity_stack import (
    QuadraticReciprocityStack,
    build_quadratic_reciprocity_stack as _build_pure_stack,
)
from .theorems import THEOREMS, TheoremSpec


def _frozen_public_by_name() -> MappingProxyType[str, TheoremSpec]:
    """Copy the current public table so stack assembly cannot retain an alias."""

    result: dict[str, TheoremSpec] = {}
    for spec in THEOREMS:
        if spec.name in result:
            raise ValueError(f"duplicate public theorem {spec.name!r}")
        result[spec.name] = spec
    return MappingProxyType(result)


def build_quadratic_reciprocity_stack() -> QuadraticReciprocityStack[TheoremSpec]:
    """Build a fresh, validated, non-admitting stack for today's registry."""

    return _build_pure_stack(
        spec_type=TheoremSpec,
        public_by_name=_frozen_public_by_name(),
    )


@lru_cache(maxsize=1)
def quadratic_reciprocity_stack() -> QuadraticReciprocityStack[TheoremSpec]:
    """Return the cached compatibility stack without replay or registration."""

    return build_quadratic_reciprocity_stack()


__all__ = [
    "build_quadratic_reciprocity_stack",
    "quadratic_reciprocity_stack",
]
