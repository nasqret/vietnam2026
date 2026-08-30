"""Static finite-product candidates for the Wilson pairing route.

The factor code is read in adjacent pairs.  Pair ``t`` occupies positions
``t+t`` and ``S (t+t)``.  If every such pair has product congruent to one
modulo ``p``, the exact beta-coded product of the first ``m+m`` entries is
congruent to one modulo ``p``.

All authoring relations below expand immediately to the unchanged
first-order Peano language.  This module is deliberately absent from the
public theorem registry pending WMI-only discovery and receipt-pinned replay.
"""

from __future__ import annotations

from typing import Any, Callable


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
    avoid: tuple[str, ...],
    stems: tuple[str, ...],
) -> tuple[str, ...]:
    safe_tag = _identifier(tag, "binder tag")
    names = tuple(f"wpp_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(avoid):
        raise ValueError("generated Wilson-pair binder captures an argument")
    return names


def _strictly_below_term(
    left: str,
    right: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    (gap,) = _binders(tag, avoid, ("gap",))
    return f"exists {gap}. {gap} + S ({left}) = {right}"


def _beta_at_term(
    code: str,
    scale: str,
    index: str,
    value: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    height, quotient = _binders(tag, avoid, ("beta_height", "beta_quotient"))
    modulus = f"S ((S ({index})) * {scale})"
    return (
        f"((exists {height}. {height} + S ({value}) = {modulus}) /\\ "
        f"exists {quotient}. {code} = {quotient} * {modulus} + ({value}))"
    )


def _product_relation_term(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    trace_code, trace_scale, index, factor, prefix, successor = _binders(
        tag,
        avoid,
        ("trace_code", "trace_scale", "index", "factor", "prefix", "successor"),
    )
    nested_avoid = avoid + (
        trace_code,
        trace_scale,
        index,
        factor,
        prefix,
        successor,
    )
    start = _beta_at_term(
        trace_code,
        trace_scale,
        "0",
        "1",
        tag=f"{tag}_start",
        avoid=nested_avoid,
    )
    terminal = _beta_at_term(
        trace_code,
        trace_scale,
        length,
        result,
        tag=f"{tag}_terminal",
        avoid=nested_avoid,
    )
    bound = _strictly_below_term(
        index,
        length,
        tag=f"{tag}_bound",
        avoid=nested_avoid,
    )
    decoded_factor = _beta_at_term(
        code,
        scale,
        index,
        factor,
        tag=f"{tag}_factor",
        avoid=nested_avoid,
    )
    decoded_prefix = _beta_at_term(
        trace_code,
        trace_scale,
        index,
        prefix,
        tag=f"{tag}_prefix",
        avoid=nested_avoid,
    )
    decoded_successor = _beta_at_term(
        trace_code,
        trace_scale,
        f"S ({index})",
        successor,
        tag=f"{tag}_successor",
        avoid=nested_avoid,
    )
    return (
        f"exists {trace_code} {trace_scale}. (({start}) /\\ (({terminal}) /\\ "
        f"forall {index}. ({bound}) -> exists {factor} {prefix} {successor}. "
        f"(({decoded_factor}) /\\ (({decoded_prefix}) /\\ "
        f"(({decoded_successor}) /\\ {successor} = {prefix} * {factor})))))"
    )


def product_relation(
    code: str,
    scale: str,
    length: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand the checked beta-coded ``Product`` convention."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (code, "factor code"),
            (scale, "factor scale"),
            (length, "product length"),
            (result, "product result"),
        )
    )
    return _product_relation_term(
        code,
        scale,
        length,
        result,
        tag=tag,
        avoid=variables,
    )


def _mod_eq_term(
    modulus: str,
    left: str,
    right: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    left_witness, right_witness = _binders(
        tag,
        avoid,
        ("mod_left", "mod_right"),
    )
    return (
        f"exists {left_witness} {right_witness}. "
        f"({left}) + {modulus} * {left_witness} = "
        f"({right}) + {modulus} * {right_witness}"
    )


def mod_eq(modulus: str, left: str, right: str, *, tag: str) -> str:
    """Expand balanced natural congruence for identifier arguments."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (left, "left residue"),
            (right, "right residue"),
        )
    )
    return _mod_eq_term(
        modulus,
        left,
        right,
        tag=tag,
        avoid=variables,
    )


def _adjacent_unit_pairs_term(
    modulus: str,
    code: str,
    scale: str,
    pair_count: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    pair, left, right = _binders(tag, avoid, ("pair", "left", "right"))
    nested_avoid = avoid + (pair, left, right)
    pair_bound = _strictly_below_term(
        pair,
        pair_count,
        tag=f"{tag}_pair_bound",
        avoid=nested_avoid,
    )
    even_index = f"({pair} + {pair})"
    odd_index = f"S ({pair} + {pair})"
    left_entry = _beta_at_term(
        code,
        scale,
        even_index,
        left,
        tag=f"{tag}_left_entry",
        avoid=nested_avoid,
    )
    right_entry = _beta_at_term(
        code,
        scale,
        odd_index,
        right,
        tag=f"{tag}_right_entry",
        avoid=nested_avoid,
    )
    pair_congruence = _mod_eq_term(
        modulus,
        f"{left} * {right}",
        "1",
        tag=f"{tag}_pair_mod",
        avoid=nested_avoid,
    )
    return (
        f"forall {pair} {left} {right}. ({pair_bound}) -> "
        f"({left_entry}) -> ({right_entry}) -> ({pair_congruence})"
    )


def adjacent_unit_pairs(
    modulus: str,
    code: str,
    scale: str,
    pair_count: str,
    *,
    tag: str,
) -> str:
    """Expand the adjacent-pair hypothesis through ``pair_count`` pairs."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (modulus, "modulus"),
            (code, "factor code"),
            (scale, "factor scale"),
            (pair_count, "pair count"),
        )
    )
    return _adjacent_unit_pairs_term(
        modulus,
        code,
        scale,
        pair_count,
        tag=tag,
        avoid=variables,
    )


def _two_factor_decomposition(
    code: str,
    scale: str,
    prefix_length: str,
    result: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    left, right, prefix = _binders(
        tag,
        avoid,
        ("left_factor", "right_factor", "prefix_product"),
    )
    nested_avoid = avoid + (left, right, prefix)
    left_entry = _beta_at_term(
        code,
        scale,
        prefix_length,
        left,
        tag=f"{tag}_left_entry",
        avoid=nested_avoid,
    )
    right_entry = _beta_at_term(
        code,
        scale,
        f"S ({prefix_length})",
        right,
        tag=f"{tag}_right_entry",
        avoid=nested_avoid,
    )
    prefix_product = _product_relation_term(
        code,
        scale,
        prefix_length,
        prefix,
        tag=f"{tag}_prefix",
        avoid=nested_avoid,
    )
    return (
        f"exists {left} {right} {prefix}. ({left_entry}) /\\ "
        f"(({right_entry}) /\\ (({prefix_product}) /\\ "
        f"{result} = ({prefix} * {left}) * {right}))"
    )


def _one_factor_decomposition(
    code: str,
    scale: str,
    prefix_length: str,
    result: str,
    *,
    tag: str,
    avoid: tuple[str, ...],
) -> str:
    factor, prefix = _binders(tag, avoid, ("factor", "prefix_product"))
    nested_avoid = avoid + (factor, prefix)
    final_entry = _beta_at_term(
        code,
        scale,
        prefix_length,
        factor,
        tag=f"{tag}_entry",
        avoid=nested_avoid,
    )
    prefix_product = _product_relation_term(
        code,
        scale,
        prefix_length,
        prefix,
        tag=f"{tag}_prefix",
        avoid=nested_avoid,
    )
    return (
        f"exists {factor} {prefix}. ({final_entry}) /\\ "
        f"(({prefix_product}) /\\ {result} = {prefix} * {factor})"
    )


def make_wilson_pair_product_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build two isolated adjacent-pair product candidates."""

    two_product = product_relation("b", "c", "l", "Q", tag="two_product")
    two_result = _two_factor_decomposition(
        "b",
        "c",
        "k",
        "Q",
        tag="two_result",
        avoid=("b", "c", "k", "l", "Q"),
    )
    outer_decomposition = _one_factor_decomposition(
        "b",
        "c",
        "S k",
        "Q",
        tag="outer_decomposition",
        avoid=("b", "c", "k", "l", "Q"),
    )
    inner_decomposition = _one_factor_decomposition(
        "b",
        "c",
        "k",
        "x1",
        tag="inner_decomposition",
        avoid=("b", "c", "k", "l", "Q", "x", "x1"),
    )

    pair_hypothesis = adjacent_unit_pairs("p", "b", "c", "m", tag="pairs")
    pair_product = _product_relation_term(
        "b",
        "c",
        "m + m",
        "Q",
        tag="pair_product",
        avoid=("p", "b", "c", "m", "Q"),
    )
    pair_result = _mod_eq_term(
        "p",
        "Q",
        "1",
        tag="pair_result",
        avoid=("p", "b", "c", "m", "Q"),
    )

    successor_decomposition = _two_factor_decomposition(
        "b",
        "c",
        "m + m",
        "Q",
        tag="successor_decomposition",
        avoid=("p", "b", "c", "m", "Q"),
    )
    prefix_pairs = adjacent_unit_pairs(
        "p", "b", "c", "m", tag="prefix_pairs"
    )
    all_successor_pairs = _adjacent_unit_pairs_term(
        "p",
        "b",
        "c",
        "S m",
        tag="all_successor_pairs",
        avoid=("p", "b", "c", "m", "Q"),
    )
    prefix_congruence = _mod_eq_term(
        "p",
        "x2",
        "1",
        tag="prefix_congruence",
        avoid=("p", "b", "c", "m", "Q", "x", "x1", "x2"),
    )
    last_pair_congruence = _mod_eq_term(
        "p",
        "x * x1",
        "1",
        tag="last_pair_congruence",
        avoid=("p", "b", "c", "m", "Q", "x", "x1", "x2"),
    )
    folded_congruence = _mod_eq_term(
        "p",
        "x2 * (x * x1)",
        "1 * 1",
        tag="folded_congruence",
        avoid=("p", "b", "c", "m", "Q", "x", "x1", "x2"),
    )

    return (
        spec(
            "beta_product_double_succ_decompose",
            f"forall b c k l Q. l = S (S k) -> ({two_product}) -> ({two_result})",
            ("beta_product_succ_decompose",),
            (
                "intro b",
                "intro c",
                "intro k",
                "intro l",
                "intro Q",
                "intro hlength",
                "intro hproduct",
                "rewrite hlength at hproduct",
                "rewrite hlength at hproduct",
                "rewrite hlength at hproduct",
                f"have houter : {outer_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose (S k)",
                "specialize beta_product_succ_decompose Q",
                "apply beta_product_succ_decompose",
                "exact hproduct",
                "cases houter",
                "cases houter_witness",
                "cases houter_witness_witness",
                "cases houter_witness_witness_right",
                f"have hinner : {inner_decomposition}",
                "specialize beta_product_succ_decompose b",
                "specialize beta_product_succ_decompose c",
                "specialize beta_product_succ_decompose k",
                "specialize beta_product_succ_decompose x1",
                "apply beta_product_succ_decompose",
                "exact houter_witness_witness_right_left",
                "cases hinner",
                "cases hinner_witness",
                "cases hinner_witness_witness",
                "cases hinner_witness_witness_right",
                "exists x2",
                "exists x",
                "exists x3",
                "split",
                "exact hinner_witness_witness_left",
                "split",
                "exact houter_witness_witness_left",
                "split",
                "exact hinner_witness_witness_right_left",
                "rewrite houter_witness_witness_right_right",
                "rewrite hinner_witness_witness_right_right",
                "refl",
            ),
            "A product of length S(S k) decomposes into its k-prefix and its final two factors.",
        ),
        spec(
            "beta_adjacent_unit_pairs_product_one",
            f"forall p b c m Q. ({pair_hypothesis}) -> ({pair_product}) -> "
            f"({pair_result})",
            (
                "beta_product_double_succ_decompose",
                "beta_product_zero",
                "le_succ",
                "le_refl",
                "mod_eq_refl",
                "mod_eq_mul",
                "add_succ_left",
                "mul_assoc",
                "one_mul",
            ),
            (
                "intro p",
                "intro b",
                "intro c",
                "induction m",
                "intro Q",
                "intro hpairs",
                "intro hproduct",
                "have hzero : 0 + 0 = 0",
                "simp",
                "rewrite hzero at hproduct",
                "rewrite hzero at hproduct",
                "rewrite hzero at hproduct",
                "have hQ : Q = 1",
                "specialize beta_product_zero b",
                "specialize beta_product_zero c",
                "specialize beta_product_zero Q",
                "apply beta_product_zero",
                "exact hproduct",
                "rewrite hQ",
                "specialize mod_eq_refl p",
                "specialize mod_eq_refl 1",
                "exact mod_eq_refl",
                "intro Q",
                "intro hpairs",
                "intro hproduct",
                "have hdouble : S m + S m = S (S (m + m))",
                "simp [add_succ_left]",
                f"have hdecomposition : {successor_decomposition}",
                "specialize beta_product_double_succ_decompose b",
                "specialize beta_product_double_succ_decompose c",
                "specialize beta_product_double_succ_decompose (m + m)",
                "specialize beta_product_double_succ_decompose (S m + S m)",
                "specialize beta_product_double_succ_decompose Q",
                "apply beta_product_double_succ_decompose",
                "exact hdouble",
                "exact hproduct",
                "cases hdecomposition",
                "cases hdecomposition_witness",
                "cases hdecomposition_witness_witness",
                "cases hdecomposition_witness_witness_witness",
                "cases hdecomposition_witness_witness_witness_right",
                "cases hdecomposition_witness_witness_witness_right_right",
                f"have hpairs_all : {all_successor_pairs}",
                "exact hpairs",
                f"have hpairs_prefix : {prefix_pairs}",
                "intro t",
                "intro a",
                "intro d",
                "intro ht",
                "intro ha",
                "intro hd",
                "specialize hpairs_all t",
                "specialize hpairs_all a",
                "specialize hpairs_all d",
                "apply hpairs_all",
                "specialize le_succ (S t)",
                "specialize le_succ m",
                "apply le_succ",
                "exact ht",
                "exact ha",
                "exact hd",
                f"have hprefix : {prefix_congruence}",
                "specialize IH x2",
                "apply IH",
                "exact hpairs_prefix",
                "exact hdecomposition_witness_witness_witness_right_right_left",
                f"have hlast : {last_pair_congruence}",
                "specialize hpairs m",
                "specialize hpairs x",
                "specialize hpairs x1",
                "apply hpairs",
                "specialize le_refl (S m)",
                "exact le_refl",
                "exact hdecomposition_witness_witness_witness_left",
                "exact hdecomposition_witness_witness_witness_right_left",
                f"have hfold : {folded_congruence}",
                "specialize mod_eq_mul p",
                "specialize mod_eq_mul x2",
                "specialize mod_eq_mul 1",
                "specialize mod_eq_mul (x * x1)",
                "specialize mod_eq_mul 1",
                "apply mod_eq_mul",
                "exact hprefix",
                "exact hlast",
                "have hone : 1 * 1 = 1",
                "specialize one_mul 1",
                "exact one_mul",
                "rewrite hone at hfold",
                "have hassoc : (x2 * x) * x1 = x2 * (x * x1)",
                "specialize mul_assoc x2",
                "specialize mul_assoc x",
                "specialize mul_assoc x1",
                "exact mul_assoc",
                "rewrite hdecomposition_witness_witness_witness_right_right_right",
                "rewrite hassoc",
                "exact hfold",
            ),
            "Adjacent inverse pairs multiply to one across an exact beta-coded even prefix.",
        ),
    )


__all__ = [
    "adjacent_unit_pairs",
    "make_wilson_pair_product_candidate_theorems",
    "mod_eq",
    "product_relation",
]
