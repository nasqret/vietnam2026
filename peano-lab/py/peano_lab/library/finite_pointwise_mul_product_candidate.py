"""Isolated exact product theorem for pointwise products of beta prefixes.

The authoring relation in this module aligns three beta codes at each finite
position: the decoded target factor is the product of the decoded left and
right factors.  The checked candidate then proves that the target finite
product is exactly the product of the two source finite products.

Every helper expands to ordinary first-order Peano arithmetic before parsing.
No tuple, function, list, multiplication-map, or fold primitive is added to
the language, and this candidate is not registered publicly.
"""

from __future__ import annotations

from typing import Any, Callable

from .finite_fold_surface import beta_at, product_relation


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


def _binders(
    tag: str,
    variables: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"fpmp_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated pointwise-product binder captures an argument")
    return names


def _pointwise_mul_prefix_term(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    target_code: str,
    target_scale: str,
    length_term: str,
    *,
    tag: str,
    variables: tuple[str, ...],
) -> str:
    index, left, right, target, gap = _binders(
        tag,
        variables,
        ("index", "left", "right", "target", "gap"),
    )
    bound = f"exists {gap}. {gap} + S {index} = {length_term}"
    left_entry = beta_at(
        left_code, left_scale, index, left, tag=f"fpmp_{tag}_left"
    )
    right_entry = beta_at(
        right_code, right_scale, index, right, tag=f"fpmp_{tag}_right"
    )
    target_entry = beta_at(
        target_code, target_scale, index, target, tag=f"fpmp_{tag}_target"
    )
    return (
        f"forall {index} {left} {right} {target}. ({bound}) -> "
        f"({left_entry}) -> ({right_entry}) -> ({target_entry}) -> "
        f"{target} = {left} * {right}"
    )


def pointwise_mul_prefix(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    target_code: str,
    target_scale: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Expand pointwise target decoding as a product of two source entries."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (left_code, "left code"),
            (left_scale, "left scale"),
            (right_code, "right code"),
            (right_scale, "right scale"),
            (target_code, "target code"),
            (target_scale, "target scale"),
            (length, "prefix length"),
        )
    )
    return _pointwise_mul_prefix_term(
        left_code,
        left_scale,
        right_code,
        right_scale,
        target_code,
        target_scale,
        length,
        tag=tag,
        variables=variables,
    )


def pointwise_mul_successor_prefix(
    left_code: str,
    left_scale: str,
    right_code: str,
    right_scale: str,
    target_code: str,
    target_scale: str,
    length_predecessor: str,
    *,
    tag: str,
) -> str:
    """Expand the relation at compound length ``S length_predecessor``."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (left_code, "left code"),
            (left_scale, "left scale"),
            (right_code, "right code"),
            (right_scale, "right scale"),
            (target_code, "target code"),
            (target_scale, "target scale"),
            (length_predecessor, "length predecessor"),
        )
    )
    return _pointwise_mul_prefix_term(
        left_code,
        left_scale,
        right_code,
        right_scale,
        target_code,
        target_scale,
        f"S {length_predecessor}",
        tag=tag,
        variables=variables,
    )


def _product_decomposition(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    factor, prefix = _binders(
        tag,
        (code, scale, length, result),
        ("factor", "prefix"),
    )
    final_entry = beta_at(code, scale, length, factor, tag=f"{tag}_entry")
    prefix_product = product_relation(
        code, scale, length, prefix, tag=f"{tag}_product"
    )
    return (
        f"exists {factor} {prefix}. ({final_entry}) /\\ "
        f"(({prefix_product}) /\\ {result} = {prefix} * {factor})"
    )


def make_finite_pointwise_mul_product_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the restriction lemma and exact synchronized-product theorem."""

    successor_alignment = pointwise_mul_successor_prefix(
        "mb", "mc", "sb", "sc", "tb", "tc", "l", tag="drop_successor"
    )
    prefix_alignment = pointwise_mul_prefix(
        "mb", "mc", "sb", "sc", "tb", "tc", "l", tag="drop_prefix"
    )

    alignment = pointwise_mul_prefix(
        "mb", "mc", "sb", "sc", "tb", "tc", "l", tag="product_alignment"
    )
    left_product = product_relation(
        "mb", "mc", "l", "M", tag="product_left"
    )
    right_product = product_relation(
        "sb", "sc", "l", "Sprod", tag="product_right"
    )
    target_product = product_relation(
        "tb", "tc", "l", "T", tag="product_target"
    )
    left_decomposition = _product_decomposition(
        "mb", "mc", "l", "M", tag="product_left_decomposition"
    )
    right_decomposition = _product_decomposition(
        "sb", "sc", "l", "Sprod", tag="product_right_decomposition"
    )
    target_decomposition = _product_decomposition(
        "tb", "tc", "l", "T", tag="product_target_decomposition"
    )
    restricted_alignment = pointwise_mul_prefix(
        "mb", "mc", "sb", "sc", "tb", "tc", "l", tag="product_restricted"
    )

    return (
        spec(
            "beta_pointwise_mul_prefix_drop_last",
            "forall mb mc sb sc tb tc l. "
            f"({successor_alignment}) -> ({prefix_alignment})",
            ("le_succ",),
            (
                "intro mb",
                "intro mc",
                "intro sb",
                "intro sc",
                "intro tb",
                "intro tc",
                "intro l",
                "intro haligned",
                "intro i",
                "intro m",
                "intro s",
                "intro t",
                "intro hi",
                "intro hm",
                "intro hs",
                "intro ht",
                "specialize haligned i",
                "specialize haligned m",
                "specialize haligned s",
                "specialize haligned t",
                "apply haligned",
                "specialize le_succ (S i)",
                "specialize le_succ l",
                "apply le_succ",
                "exact hi",
                "exact hm",
                "exact hs",
                "exact ht",
            ),
            "Pointwise multiplication alignment restricts to the predecessor prefix.",
        ),
        spec(
            "beta_product_pointwise_mul_exact",
            "forall mb mc sb sc tb tc l M Sprod T. "
            f"({alignment}) -> ({left_product}) -> ({right_product}) -> "
            f"({target_product}) -> T = M * Sprod",
            (
                "beta_product_zero",
                "beta_product_succ_decompose",
                "beta_pointwise_mul_prefix_drop_last",
                "le_refl",
                "one_mul",
                "mul_assoc",
                "mul_comm",
            ),
            (
                "intro mb",
                "intro mc",
                "intro sb",
                "intro sc",
                "intro tb",
                "intro tc",
                "induction l",
                "intro M",
                "intro Sprod",
                "intro T",
                "intro haligned",
                "intro hM",
                "intro hS",
                "intro hT",
                "have hM1 : M = 1",
                "specialize beta_product_zero mb",
                "specialize beta_product_zero mc",
                "specialize beta_product_zero M",
                "apply beta_product_zero",
                "exact hM",
                "have hS1 : Sprod = 1",
                "specialize beta_product_zero sb",
                "specialize beta_product_zero sc",
                "specialize beta_product_zero Sprod",
                "apply beta_product_zero",
                "exact hS",
                "have hT1 : T = 1",
                "specialize beta_product_zero tb",
                "specialize beta_product_zero tc",
                "specialize beta_product_zero T",
                "apply beta_product_zero",
                "exact hT",
                "rewrite hM1",
                "rewrite hS1",
                "rewrite hT1",
                "specialize one_mul 1",
                "symm",
                "exact one_mul",
                "intro M",
                "intro Sprod",
                "intro T",
                "intro haligned",
                "intro hM",
                "intro hS",
                "intro hT",
                f"have hMd : {left_decomposition}",
                "specialize beta_product_succ_decompose mb",
                "specialize beta_product_succ_decompose mc",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose M",
                "apply beta_product_succ_decompose",
                "exact hM",
                "cases hMd",
                "cases hMd_witness",
                "cases hMd_witness_witness",
                "cases hMd_witness_witness_right",
                f"have hSd : {right_decomposition}",
                "specialize beta_product_succ_decompose sb",
                "specialize beta_product_succ_decompose sc",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose Sprod",
                "apply beta_product_succ_decompose",
                "exact hS",
                "cases hSd",
                "cases hSd_witness",
                "cases hSd_witness_witness",
                "cases hSd_witness_witness_right",
                f"have hTd : {target_decomposition}",
                "specialize beta_product_succ_decompose tb",
                "specialize beta_product_succ_decompose tc",
                "specialize beta_product_succ_decompose l",
                "specialize beta_product_succ_decompose T",
                "apply beta_product_succ_decompose",
                "exact hT",
                "cases hTd",
                "cases hTd_witness",
                "cases hTd_witness_witness",
                "cases hTd_witness_witness_right",
                f"have hprefix_alignment : {restricted_alignment}",
                "specialize beta_pointwise_mul_prefix_drop_last mb",
                "specialize beta_pointwise_mul_prefix_drop_last mc",
                "specialize beta_pointwise_mul_prefix_drop_last sb",
                "specialize beta_pointwise_mul_prefix_drop_last sc",
                "specialize beta_pointwise_mul_prefix_drop_last tb",
                "specialize beta_pointwise_mul_prefix_drop_last tc",
                "specialize beta_pointwise_mul_prefix_drop_last l",
                "apply beta_pointwise_mul_prefix_drop_last",
                "exact haligned",
                "have hprefix : x5 = x1 * x3",
                "specialize IH x1",
                "specialize IH x3",
                "specialize IH x5",
                "apply IH",
                "exact hprefix_alignment",
                "exact hMd_witness_witness_right_left",
                "exact hSd_witness_witness_right_left",
                "exact hTd_witness_witness_right_left",
                "have hentry : x4 = x * x2",
                "specialize haligned l",
                "specialize haligned x",
                "specialize haligned x2",
                "specialize haligned x4",
                "apply haligned",
                "specialize le_refl (S l)",
                "exact le_refl",
                "exact hMd_witness_witness_left",
                "exact hSd_witness_witness_left",
                "exact hTd_witness_witness_left",
                "have hshuffle : (x1 * x3) * (x * x2) = "
                "(x1 * x) * (x3 * x2)",
                "simp [mul_assoc, mul_comm]",
                "rewrite hTd_witness_witness_right_right",
                "rewrite hMd_witness_witness_right_right",
                "rewrite hSd_witness_witness_right_right",
                "rewrite hprefix",
                "rewrite hentry",
                "exact hshuffle",
            ),
            "Pointwise products of synchronized beta prefixes multiply their exact finite products.",
        ),
    )


__all__ = [
    "make_finite_pointwise_mul_product_candidate_theorems",
    "pointwise_mul_prefix",
    "pointwise_mul_successor_prefix",
]
