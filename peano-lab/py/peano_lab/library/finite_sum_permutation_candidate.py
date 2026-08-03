"""Constructive exact-sum transport for beta-coded finite swaps.

This isolated candidate reuses the already audited *shape* of the finite-
product exchange proof, but substitutes the additive fold contracts exactly:
the empty fold is zero, a successor fold appends by addition, and replacing
``x`` by ``y`` satisfies ``new + x = old + y``.  Beta-code arithmetic is not
rewritten; every ``*`` that remains in a public formula belongs to the
unchanged Goedel-beta encoding.

The resulting theorem specifications are dependency-curried authoring
evidence only.  They are deliberately absent from the public registry.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import (
    product_relation,
    product_successor_relation,
    sum_relation,
)
from .finite_product_permutation_theorems import (
    make_finite_product_permutation_theorems,
)


def _sum_successor_relation(
    code: str,
    scale: str,
    predecessor: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand ``Sum(code, scale, S predecessor, result)`` hygienically."""

    marker = "finitesumsuccessorlengthmarker"
    expanded = sum_relation(code, scale, marker, result, tag=tag)
    if expanded.count(marker) != 3:
        raise AssertionError("unexpected Sum length-marker multiplicity")
    return expanded.replace(marker, f"S {predecessor}")


def _template_spec(
    name: str,
    statement: str,
    dependencies: tuple[str, ...],
    script: tuple[str, ...],
    summary: str,
) -> tuple[str, str, tuple[str, ...], tuple[str, ...], str]:
    return name, statement, dependencies, script, summary


def _surface_pairs() -> tuple[tuple[str, str], ...]:
    """Exact Product-to-Sum surface substitutions used by the template."""

    ordinary = (
        ("b", "c", "k", "p", "balance_old"),
        ("z", "d", "k", "q", "balance_new"),
        ("b", "c", "k", "r", "balance_old_prefix"),
        ("z", "d", "k", "r", "balance_new_prefix"),
        ("z", "d", "k", "x2", "balance_transported_prefix"),
        ("b", "c", "n", "r", "swap_old_prefix"),
        ("z", "d", "n", "r", "swap_new_prefix"),
    )
    successor = (
        ("b", "c", "n", "p", "product_swap_old"),
        ("z", "d", "n", "q", "product_swap_new"),
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

    # These are the only fold-specific algebra fragments in the two template
    # proofs.  In particular, beta-code moduli and quotient witnesses retain
    # their multiplication signs.
    replacements = (
        ("beta_product_", "beta_sum_"),
        ("beta_sum_functional", "beta_sum_trace_functional"),
        ("mul_assoc", "add_assoc"),
        ("mul_comm", "add_comm"),
        ("q * x = p * y", "q + x = p + y"),
        ("x4 * x = x2 * y", "x4 + x = x2 + y"),
        ("(x4 * x) * y", "(x4 + x) + y"),
        ("(x4 * x) * x1", "(x4 + x) + x1"),
        ("p = r * a", "p = r + a"),
        ("q = r * a", "q = r + a"),
    )
    for old, new in replacements:
        result = result.replace(old, new)
    return result


def _assert_sumified(source: str) -> None:
    forbidden = (
        "beta_product_",
        "mul_assoc",
        "mul_comm",
        "q * x = p * y",
        "x4 * x = x2 * y",
        "p = r * a",
        "q = r * a",
    )
    if any(fragment in source for fragment in forbidden):
        raise AssertionError("finite-sum template retained product-fold syntax")


def make_finite_sum_permutation_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build replacement balance and interior/last exact-sum invariance."""

    templates = make_finite_product_permutation_theorems(_template_spec)[1:]
    built = []
    for name, statement, dependencies, script, summary in templates:
        sum_name = name.replace("beta_product_", "beta_sum_")
        sum_statement = _sumify_text(statement)
        sum_dependencies = tuple(_sumify_text(item) for item in dependencies)
        sum_script = tuple(_sumify_text(command) for command in script)
        sum_summary = summary.replace("product", "sum").replace(
            "factor", "summand"
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


__all__ = ["make_finite_sum_permutation_candidate_theorems"]
