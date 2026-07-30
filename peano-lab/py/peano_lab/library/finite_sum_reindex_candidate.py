"""Exact finite-sum invariance under beta-coded permutations.

The map code ``(r,s)`` sends each target position to a source position.
Boundedness plus injectivity supplies finite surjectivity; an interior/last
swap then fixes the final position and reduces the successor case to the
induction hypothesis on the shorter prefix.  This is the same constructive
finite-permutation architecture used by the checked Product theorem, with
every fold-specific surface replaced by the relational ``Sum`` contract.

All theorem inputs are fully expanded first-order PA.  This module is an
isolated, dependency-curried candidate and registers nothing.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import (
    product_relation,
    product_successor_relation,
    sum_relation,
)
from .finite_product_reindex_candidate import (
    make_finite_product_reindex_candidate,
)
from .finite_sum_permutation_candidate import _sum_successor_relation


def _template_spec(
    name: str,
    statement: str,
    dependencies: tuple[str, ...],
    script: tuple[str, ...],
    summary: str,
) -> tuple[str, str, tuple[str, ...], tuple[str, ...], str]:
    return name, statement, dependencies, script, summary


def _surface_pairs() -> tuple[tuple[str, str], ...]:
    ordinary = (
        ("b", "c", "n", "u", "fru"),
        ("z", "d", "n", "v", "frv"),
        (
            "b",
            "c",
            "n",
            "u",
            "fixed_reindex_source_prefix_witness",
        ),
        (
            "z",
            "d",
            "n",
            "v",
            "fixed_reindex_target_prefix_witness",
        ),
        ("b", "c", "l", "p", "reindex_source_product"),
        ("z", "d", "l", "q", "reindex_target_product"),
        ("b", "c", "l", "u", "reindex_source_prefix_product"),
        ("z", "d", "l", "v", "reindex_target_prefix_product"),
        (
            "x6",
            "x7",
            "l",
            "v",
            "reindex_swapped_target_prefix_product",
        ),
    )
    successor = (
        ("b", "c", "n", "p", "frs"),
        ("z", "d", "n", "q", "frt"),
        (
            "x6",
            "x7",
            "l",
            "t",
            "reindex_swapped_target_exists",
        ),
        (
            "x6",
            "x7",
            "l",
            "x8",
            "reindex_swapped_target_product",
        ),
    )
    pairs = [
        (
            product_relation(code, scale, length, result, tag=tag),
            sum_relation(code, scale, length, result, tag=tag),
        )
        for code, scale, length, result, tag in ordinary
    ]
    pairs.extend(
        (
            product_successor_relation(
                code, scale, predecessor, result, tag=tag
            ),
            _sum_successor_relation(
                code, scale, predecessor, result, tag=tag
            ),
        )
        for code, scale, predecessor, result, tag in successor
    )
    return tuple(pairs)


def _sumify_text(source: str) -> str:
    result = source
    for old, new in _surface_pairs():
        result = result.replace(old, new)
    replacements = (
        ("beta_product_", "beta_sum_"),
        ("p = u * a", "p = u + a"),
        ("q = v * a", "q = v + a"),
        ("have hp : p = 1", "have hp : p = 0"),
        ("have hq : q = 1", "have hq : q = 0"),
        ("trans 1", "trans 0"),
    )
    for old, new in replacements:
        result = result.replace(old, new)
    return result


def _assert_sumified(source: str) -> None:
    forbidden = (
        "beta_product_",
        "p = u * a",
        "q = v * a",
        "have hp : p = 1",
        "have hq : q = 1",
        "trans 1",
    )
    if any(fragment in source for fragment in forbidden):
        raise AssertionError("finite-sum reindex template retained Product syntax")


def make_finite_sum_reindex_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build fixed-last reduction and bounded-injective Sum invariance."""

    templates = make_finite_product_reindex_candidate(_template_spec)
    built = []
    for name, statement, dependencies, script, summary in templates:
        sum_name = name.replace("beta_product_", "beta_sum_")
        sum_statement = _sumify_text(statement)
        sum_dependencies = tuple(_sumify_text(item) for item in dependencies)
        sum_script = tuple(_sumify_text(command) for command in script)
        sum_summary = summary.replace("product", "sum").replace(
            "Product", "Sum"
        )
        _assert_sumified(sum_statement)
        _assert_sumified("\n".join(sum_dependencies + sum_script))
        built.append(
            spec(
                sum_name,
                sum_statement,
                sum_dependencies,
                sum_script,
                sum_summary,
            )
        )
    return tuple(built)


__all__ = ["make_finite_sum_reindex_candidate_theorems"]
