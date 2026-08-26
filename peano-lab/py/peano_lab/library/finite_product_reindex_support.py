"""Checked support rungs for beta-coded finite-product reindexing.

The helpers in this module are hygienic authoring abbreviations only.  They
expand alignment into the unchanged first-order PA language; no map, list,
function, product, or permutation symbol is added to the parser or kernel.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at
from .finite_permutation_theorems import (
    bounded_prefix,
    bounded_successor_prefix,
    injective_successor_prefix,
)


_RESERVED = {"S", "bot", "exists", "false", "forall"}


def _identifier(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or not (value[0].isalpha() or value[0] == "_")
        or not all(character.isalnum() or character in "_'" for character in value[1:])
        or value in _RESERVED
    ):
        raise ValueError(f"{label} must be a non-reserved Peano identifier")
    return value


def _binders(tag: str, avoid: tuple[str, ...]) -> tuple[str, str, str, str]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"fpr_{stem}_{safe_tag}" for stem in ("i", "j", "x", "h"))
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated finite-product-reindex binder captures an argument")
    return names  # type: ignore[return-value]


def _aligned_prefix_term(
    map_code: str,
    map_scale: str,
    source_code: str,
    source_scale: str,
    target_code: str,
    target_scale: str,
    length_term: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    i, j, value, gap = _binders(tag, avoid)
    bound = f"exists {gap}. {gap} + S {i} = {length_term}"
    map_entry = beta_at(map_code, map_scale, i, j, tag=f"{tag}_map")
    source_entry = beta_at(
        source_code, source_scale, j, value, tag=f"{tag}_source"
    )
    target_entry = beta_at(
        target_code, target_scale, i, value, tag=f"{tag}_target"
    )
    return (
        f"forall {i} {j} {value}. ({bound}) -> ({map_entry}) -> "
        f"({source_entry}) -> ({target_entry})"
    )


def aligned_prefix(
    map_code: str,
    map_scale: str,
    source_code: str,
    source_scale: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand target-to-source pointwise alignment at an identifier length."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (map_code, "map code"),
            (map_scale, "map scale"),
            (source_code, "source code"),
            (source_scale, "source scale"),
            (target_code, "target code"),
            (target_scale, "target scale"),
            (length, "length"),
        )
    )
    return _aligned_prefix_term(
        map_code,
        map_scale,
        source_code,
        source_scale,
        target_code,
        target_scale,
        length,
        tag=tag,
        avoid=variables,
    )


def aligned_successor_prefix(
    map_code: str,
    map_scale: str,
    source_code: str,
    source_scale: str,
    target_code: str,
    target_scale: str,
    predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand alignment at the audited compound length ``S predecessor``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (map_code, "map code"),
            (map_scale, "map scale"),
            (source_code, "source code"),
            (source_scale, "source scale"),
            (target_code, "target code"),
            (target_scale, "target scale"),
            (predecessor, "length predecessor"),
        )
    )
    return _aligned_prefix_term(
        map_code,
        map_scale,
        source_code,
        source_scale,
        target_code,
        target_scale,
        f"S {predecessor}",
        tag=tag,
        avoid=variables,
    )


def make_finite_product_reindex_support_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the fixed-last and synchronized-swap support certificates."""

    fixed_bounded_succ = bounded_successor_prefix(
        "r", "s", "n", tag="fixed_last_bounded_succ"
    )
    fixed_injective_succ = injective_successor_prefix(
        "r", "s", "n", tag="fixed_last_injective_succ"
    )
    fixed_last = beta_at("r", "s", "n", "n", tag="fixed_last_entry")
    fixed_bounded_prefix = bounded_prefix(
        "r", "s", "n", tag="fixed_last_bounded_prefix"
    )

    map_new_i = beta_at("u", "v", "i", "m", tag="align_swap_map_i")
    map_new_n = beta_at("u", "v", "n", "n", tag="align_swap_map_n")
    map_old_k = beta_at("r", "s", "k", "j", tag="align_swap_map_old")
    map_new_k = beta_at("u", "v", "k", "j", tag="align_swap_map_new")
    source_m = beta_at("b", "c", "m", "y", tag="align_swap_source_m")
    source_n = beta_at("b", "c", "n", "x", tag="align_swap_source_n")
    target_new_i = beta_at("w", "e", "i", "y", tag="align_swap_target_i")
    target_new_n = beta_at("w", "e", "n", "x", tag="align_swap_target_n")
    target_old_k = beta_at("z", "d", "k", "a", tag="align_swap_target_old")
    target_new_k = beta_at("w", "e", "k", "a", tag="align_swap_target_new")
    old_alignment = aligned_successor_prefix(
        "r", "s", "b", "c", "z", "d", "n", tag="align_swap_old"
    )
    new_alignment = aligned_successor_prefix(
        "u", "v", "b", "c", "w", "e", "n", tag="align_swap_new"
    )
    map_preservation = (
        "forall k j. (exists h. h + S k = S n) -> "
        f"~(k = i) -> ~(k = n) -> ({map_old_k}) -> ({map_new_k})"
    )
    target_preservation = (
        "forall k a. (exists h. h + S k = S n) -> "
        f"~(k = i) -> ~(k = n) -> ({target_old_k}) -> ({target_new_k})"
    )
    reflection_cases = (
        "(k = i /\\ j = m) \\/ ((k = n /\\ j = n) \\/ "
        "(~(k = i) /\\ (~(k = n) /\\ "
        "((exists h. h + S j = S ((S k) * s)) /\\ "
        "exists q. r = q * S ((S k) * s) + j))))"
    )

    return (
        spec(
            "finite_fixed_last_prefix_bounded",
            f"forall r s n. ({fixed_bounded_succ}) -> "
            f"({fixed_injective_succ}) -> ({fixed_last}) -> "
            f"({fixed_bounded_prefix})",
            (
                "finite_bounded_prefix_without_top",
                "le_succ",
                "le_refl",
                "lt_irrefl_expanded",
            ),
            (
                "intro r",
                "intro s",
                "intro n",
                "intro hbounded",
                "intro hinjective",
                "intro hlast",
                "have hnotop : forall i. (exists h. h + S i = n) -> "
                "~((exists h. h + S n = S ((S i) * s)) /\\ "
                "exists q. r = q * S ((S i) * s) + n)",
                "intro i",
                "intro hi",
                "intro htop",
                "have hisn : exists h. h + S i = S n",
                "specialize le_succ (S i)",
                "specialize le_succ n",
                "apply le_succ",
                "exact hi",
                "have hnsn : exists h. h + S n = S n",
                "specialize le_refl (S n)",
                "exact le_refl",
                "have hin : i = n",
                "specialize hinjective i",
                "specialize hinjective n",
                "specialize hinjective n",
                "apply hinjective",
                "exact hisn",
                "exact hnsn",
                "exact htop",
                "exact hlast",
                "specialize lt_irrefl_expanded n",
                "apply lt_irrefl_expanded",
                "rewrite hin at hi",
                "exact hi",
                "specialize finite_bounded_prefix_without_top r",
                "specialize finite_bounded_prefix_without_top s",
                "specialize finite_bounded_prefix_without_top n",
                "specialize finite_bounded_prefix_without_top (S n)",
                "apply finite_bounded_prefix_without_top",
                "refl",
                "exact hbounded",
                "exact hnotop",
            ),
            "A bounded injective successor reindexing fixed at its last position is bounded on the old prefix.",
        ),
        spec(
            "beta_reindex_alignment_swap_last",
            "forall r s u v b c z d w e n i m x y. "
            f"({map_new_i}) -> ({map_new_n}) -> ({map_preservation}) -> "
            f"({source_m}) -> ({source_n}) -> ({target_new_i}) -> "
            f"({target_new_n}) -> ({target_preservation}) -> "
            f"({old_alignment}) -> ({new_alignment})",
            ("beta_prefix_swap_last_reflect", "beta_at_unique"),
            (
                "intro r",
                "intro s",
                "intro u",
                "intro v",
                "intro b",
                "intro c",
                "intro z",
                "intro d",
                "intro w",
                "intro e",
                "intro n",
                "intro i",
                "intro m",
                "intro x",
                "intro y",
                "intro hmap_i",
                "intro hmap_n",
                "intro hmap_preserve",
                "intro hsource_m",
                "intro hsource_n",
                "intro htarget_i",
                "intro htarget_n",
                "intro htarget_preserve",
                "intro haligned",
                "have hreflect : forall k j. "
                "(exists h. h + S k = S n) -> "
                "((exists h. h + S j = S ((S k) * v)) /\\ "
                "exists q. u = q * S ((S k) * v) + j) -> "
                + reflection_cases,
                "specialize beta_prefix_swap_last_reflect r",
                "specialize beta_prefix_swap_last_reflect s",
                "specialize beta_prefix_swap_last_reflect u",
                "specialize beta_prefix_swap_last_reflect v",
                "specialize beta_prefix_swap_last_reflect n",
                "specialize beta_prefix_swap_last_reflect i",
                "specialize beta_prefix_swap_last_reflect n",
                "specialize beta_prefix_swap_last_reflect m",
                "apply beta_prefix_swap_last_reflect",
                "exact hmap_i",
                "exact hmap_n",
                "exact hmap_preserve",
                "intro k",
                "intro j",
                "intro a",
                "intro hk",
                "intro hmap",
                "intro hsource",
                "specialize hreflect k",
                "specialize hreflect j",
                "have hcases : " + reflection_cases,
                "apply hreflect",
                "exact hk",
                "exact hmap",
                "cases hcases",
                "cases hcases_left",
                "have hay : a = y",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique m",
                "specialize beta_at_unique a",
                "specialize beta_at_unique y",
                "apply beta_at_unique",
                "rewrite hcases_left_right at hsource",
                "rewrite hcases_left_right at hsource",
                "exact hsource",
                "exact hsource_m",
                "rewrite hcases_left_left",
                "rewrite hcases_left_left",
                "rewrite hay",
                "rewrite hay",
                "exact htarget_i",
                "cases hcases_right",
                "cases hcases_right_left",
                "have hax : a = x",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique n",
                "specialize beta_at_unique a",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "rewrite hcases_right_left_right at hsource",
                "rewrite hcases_right_left_right at hsource",
                "exact hsource",
                "exact hsource_n",
                "rewrite hcases_right_left_left",
                "rewrite hcases_right_left_left",
                "rewrite hax",
                "rewrite hax",
                "exact htarget_n",
                "cases hcases_right_right",
                "cases hcases_right_right_right",
                "have hold_target : "
                "((exists h. h + S a = S ((S k) * d)) /\\ "
                "exists q. z = q * S ((S k) * d) + a)",
                "specialize haligned k",
                "specialize haligned j",
                "specialize haligned a",
                "apply haligned",
                "exact hk",
                "exact hcases_right_right_right_right",
                "exact hsource",
                "specialize htarget_preserve k",
                "specialize htarget_preserve a",
                "apply htarget_preserve",
                "exact hk",
                "exact hcases_right_right_left",
                "exact hcases_right_right_right_left",
                "exact hold_target",
            ),
            "Simultaneous interior/final swaps of an index code and target factors preserve alignment.",
        ),
    )


__all__ = [
    "aligned_prefix",
    "aligned_successor_prefix",
    "make_finite_product_reindex_support_theorems",
]
