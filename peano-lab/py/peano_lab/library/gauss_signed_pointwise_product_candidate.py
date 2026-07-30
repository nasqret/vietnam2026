"""Isolated congruence bridge from Gauss signed choices to factor products.

The signed-half prefix stores, at each position, a positive magnitude and a
zero/one reflection bit.  A downstream sign-factor code maps those bits to
``1`` and ``r``; a pointwise-product code stores magnitude times sign factor.
Under ``p = S r`` and ``r = 2*h``, this module proves that the stored target is
congruent modulo ``p`` to the scaled source entry.  For the canonical half
range, that source entry is ``S i``.

All helpers expand to ordinary first-order PA before parsing.  This module is
an unregistered candidate and adds no congruence, sequence, or fold primitive
to the kernel language.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_scale_product_candidate import (
    product_left_mod,
    scale_mod_prefix,
)
from .finite_fold_surface import beta_at, power_relation, product_relation
from .finite_pointwise_mul_product_candidate import pointwise_mul_prefix
from .gauss_sign_product_candidate import sign_factor_prefix
from .gauss_signed_prefix_candidate import (
    _beta_at_term,
    _entry_term,
    half_range,
    signed_half_prefix,
)


def _scaled_successor_mod(*, tag: str) -> str:
    return (
        f"exists gspc_left_{tag} gspc_right_{tag}. "
        f"a * S i + p * gspc_left_{tag} = t + p * gspc_right_{tag}"
    )


def make_gauss_signed_pointwise_product_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build pointwise scale, canonical-successor, and product endpoints."""

    signed_prefix = signed_half_prefix(
        "p",
        "h",
        "a",
        "b",
        "c",
        "mb",
        "mc",
        "sb",
        "sc",
        "h",
        tag="pointwise_signed_prefix",
    )
    sign_factors = sign_factor_prefix(
        "sb", "sc", "fb", "fc", "r", "h", tag="pointwise_sign_factors"
    )
    multiplied_prefix = pointwise_mul_prefix(
        "mb", "mc", "fb", "fc", "tb", "tc", "h", tag="pointwise_products"
    )
    scale_prefix = scale_mod_prefix(
        "p", "a", "b", "c", "tb", "tc", "h", tag="pointwise_scale_result"
    )
    signed_entry = _entry_term(
        "p",
        "h",
        "a",
        "b",
        "c",
        "mb",
        "mc",
        "sb",
        "sc",
        "i",
        tag="pointwise_signed_entry",
        variables=(
            "p",
            "h",
            "r",
            "a",
            "b",
            "c",
            "mb",
            "mc",
            "sb",
            "sc",
            "fb",
            "fc",
            "tb",
            "tc",
            "i",
            "v",
            "t",
        ),
    )
    factor_one_entry = _beta_at_term(
        "fb",
        "fc",
        "i",
        "1",
        tag="pointwise_factor_one",
        variables=(
            "p",
            "h",
            "r",
            "a",
            "b",
            "c",
            "mb",
            "mc",
            "sb",
            "sc",
            "fb",
            "fc",
            "tb",
            "tc",
            "i",
            "v",
            "t",
            "x",
            "x1",
            "x2",
        ),
    )
    factor_r_entry = beta_at(
        "fb", "fc", "i", "r", tag="pointwise_factor_r"
    )

    canonical_range = half_range("b", "c", "h", tag="successor_half_range")
    target_entry = beta_at(
        "tb", "tc", "i", "t", tag="successor_target_entry"
    )
    successor_result = _scaled_successor_mod(tag="successor_result")
    canonical_raw_entry = _beta_at_term(
        "b",
        "c",
        "i",
        "1 + i",
        tag="successor_raw_entry",
        variables=(
            "p",
            "h",
            "r",
            "a",
            "b",
            "c",
            "mb",
            "mc",
            "sb",
            "sc",
            "fb",
            "fc",
            "tb",
            "tc",
            "i",
            "t",
        ),
    )
    canonical_successor_entry = _beta_at_term(
        "b",
        "c",
        "i",
        "S i",
        tag="successor_canonical_entry",
        variables=(
            "p",
            "h",
            "r",
            "a",
            "b",
            "c",
            "mb",
            "mc",
            "sb",
            "sc",
            "fb",
            "fc",
            "tb",
            "tc",
            "i",
            "t",
        ),
    )

    source_product = product_relation(
        "b", "c", "h", "P", tag="pointwise_product_source"
    )
    target_product = product_relation(
        "tb", "tc", "h", "T", tag="pointwise_product_target"
    )
    multiplier_power = power_relation(
        "a", "h", "A", tag="pointwise_product_power"
    )
    product_result = product_left_mod(
        "p", "A", "P", "T", tag="pointwise_product_result"
    )

    return (
        spec(
            "gauss_signed_pointwise_mul_scale_mod",
            "forall p h r a b c mb mc sb sc fb fc tb tc. "
            f"p = S r -> r = 2 * h -> ({signed_prefix}) -> "
            f"({sign_factors}) -> ({multiplied_prefix}) -> ({scale_prefix})",
            (
                "beta_at_unique",
                "mul_one",
                "mul_comm",
            ),
            (
                "intro p",
                "intro h",
                "intro r",
                "intro a",
                "intro b",
                "intro c",
                "intro mb",
                "intro mc",
                "intro sb",
                "intro sc",
                "intro fb",
                "intro fc",
                "intro tb",
                "intro tc",
                "intro hp",
                "intro hr",
                "intro hsigned",
                "intro hfactor",
                "intro hmul",
                "intro i",
                "intro v",
                "intro t",
                "intro hi",
                "intro hv",
                "intro ht",
                f"have hentry : {signed_entry}",
                "specialize hsigned i",
                "apply hsigned",
                "exact hi",
                "cases hentry",
                "cases hentry_witness",
                "cases hentry_witness_witness",
                "cases hentry_witness_witness_witness",
                "cases hentry_witness_witness_witness_right",
                "cases hentry_witness_witness_witness_right_right",
                "cases hentry_witness_witness_witness_right_right_right",
                "cases hentry_witness_witness_witness_right_right_right_right",
                "cases hentry_witness_witness_witness_right_right_right_right_right",
                "have hvx : v = x",
                "specialize beta_at_unique b",
                "specialize beta_at_unique c",
                "specialize beta_at_unique i",
                "specialize beta_at_unique v",
                "specialize beta_at_unique x",
                "apply beta_at_unique",
                "exact hv",
                "exact hentry_witness_witness_witness_left",
                "have hfactor_case : (((x2 = 0) /\\ "
                f"({factor_one_entry})) \\/ ((x2 = 1) /\\ ({factor_r_entry})))",
                "specialize hfactor i",
                "specialize hfactor x2",
                "apply hfactor",
                "exact hi",
                "exact hentry_witness_witness_witness_right_right_left",
                "cases hentry_witness_witness_witness_right_right_right_right_right_right",
                "cases hentry_witness_witness_witness_right_right_right_right_right_right_left",
                "cases hfactor_case",
                "cases hfactor_case_left",
                "have ht_one : t = x1 * 1",
                "specialize hmul i",
                "specialize hmul x1",
                "specialize hmul 1",
                "specialize hmul t",
                "apply hmul",
                "exact hi",
                "exact hentry_witness_witness_witness_right_left",
                "exact hfactor_case_left_right",
                "exact ht",
                "rewrite hvx",
                "rewrite ht_one",
                "specialize mul_one x1",
                "rewrite mul_one",
                "exact hentry_witness_witness_witness_right_right_right_right_right_right_left_right",
                "cases hfactor_case_right",
                "exfalso",
                "apply PA1",
                "trans x2",
                "symm",
                "exact hfactor_case_right_left",
                "exact hentry_witness_witness_witness_right_right_right_right_right_right_left_left",
                "cases hentry_witness_witness_witness_right_right_right_right_right_right_right",
                "cases hfactor_case",
                "cases hfactor_case_left",
                "exfalso",
                "apply PA1",
                "trans x2",
                "symm",
                "exact hentry_witness_witness_witness_right_right_right_right_right_right_right_left",
                "exact hfactor_case_left_left",
                "cases hfactor_case_right",
                "have ht_r : t = x1 * r",
                "specialize hmul i",
                "specialize hmul x1",
                "specialize hmul r",
                "specialize hmul t",
                "apply hmul",
                "exact hi",
                "exact hentry_witness_witness_witness_right_left",
                "exact hfactor_case_right_right",
                "exact ht",
                "have ht_reflected : t = (2 * h) * x1",
                "trans x1 * r",
                "exact ht_r",
                "trans r * x1",
                "apply mul_comm",
                "congr",
                "exact hr",
                "refl",
                "rewrite hvx",
                "rewrite ht_reflected",
                "exact hentry_witness_witness_witness_right_right_right_right_right_right_right_right",
            ),
            "Signed magnitudes times their 1/r factors are pointwise congruent to the scaled source prefix.",
        ),
        spec(
            "gauss_signed_pointwise_mul_successor_mod",
            "forall p h r a b c mb mc sb sc fb fc tb tc. "
            f"p = S r -> r = 2 * h -> ({canonical_range}) -> "
            f"({signed_prefix}) -> ({sign_factors}) -> ({multiplied_prefix}) -> "
            f"forall i t. (exists gap. gap + S i = h) -> ({target_entry}) -> "
            f"({successor_result})",
            (
                "gauss_signed_pointwise_mul_scale_mod",
                "add_succ_left",
                "zero_add",
            ),
            (
                "intro p",
                "intro h",
                "intro r",
                "intro a",
                "intro b",
                "intro c",
                "intro mb",
                "intro mc",
                "intro sb",
                "intro sc",
                "intro fb",
                "intro fc",
                "intro tb",
                "intro tc",
                "intro hp",
                "intro hr",
                "intro hhalf",
                "intro hsigned",
                "intro hfactor",
                "intro hmul",
                f"have hscale : {scale_prefix}",
                "specialize gauss_signed_pointwise_mul_scale_mod p",
                "specialize gauss_signed_pointwise_mul_scale_mod h",
                "specialize gauss_signed_pointwise_mul_scale_mod r",
                "specialize gauss_signed_pointwise_mul_scale_mod a",
                "specialize gauss_signed_pointwise_mul_scale_mod b",
                "specialize gauss_signed_pointwise_mul_scale_mod c",
                "specialize gauss_signed_pointwise_mul_scale_mod mb",
                "specialize gauss_signed_pointwise_mul_scale_mod mc",
                "specialize gauss_signed_pointwise_mul_scale_mod sb",
                "specialize gauss_signed_pointwise_mul_scale_mod sc",
                "specialize gauss_signed_pointwise_mul_scale_mod fb",
                "specialize gauss_signed_pointwise_mul_scale_mod fc",
                "specialize gauss_signed_pointwise_mul_scale_mod tb",
                "specialize gauss_signed_pointwise_mul_scale_mod tc",
                "apply gauss_signed_pointwise_mul_scale_mod",
                "exact hp",
                "exact hr",
                "exact hsigned",
                "exact hfactor",
                "exact hmul",
                "intro i",
                "intro t",
                "intro hi",
                "intro ht",
                f"have hraw : {canonical_raw_entry}",
                "specialize hhalf i",
                "apply hhalf",
                "exact hi",
                "have hone : 1 + i = S i",
                "trans S (0 + i)",
                "specialize add_succ_left 0",
                "specialize add_succ_left i",
                "exact add_succ_left",
                "congr",
                "specialize zero_add i",
                "exact zero_add",
                f"have hsource : {canonical_successor_entry}",
                "rewrite hone at hraw",
                "rewrite hone at hraw",
                "exact hraw",
                "specialize hscale i",
                "specialize hscale (S i)",
                "specialize hscale t",
                "apply hscale",
                "exact hi",
                "exact hsource",
                "exact ht",
            ),
            "For the canonical half range, the scaled successor a*S i is congruent to the signed product target.",
        ),
        spec(
            "gauss_signed_pointwise_mul_product_mod",
            "forall p h r a b c mb mc sb sc fb fc tb tc P T A. "
            f"p = S r -> r = 2 * h -> ({signed_prefix}) -> "
            f"({sign_factors}) -> ({multiplied_prefix}) -> "
            f"({source_product}) -> ({target_product}) -> "
            f"({multiplier_power}) -> ({product_result})",
            (
                "gauss_signed_pointwise_mul_scale_mod",
                "beta_product_pointwise_scale_mod",
            ),
            (
                "intro p",
                "intro h",
                "intro r",
                "intro a",
                "intro b",
                "intro c",
                "intro mb",
                "intro mc",
                "intro sb",
                "intro sc",
                "intro fb",
                "intro fc",
                "intro tb",
                "intro tc",
                "intro P",
                "intro T",
                "intro A",
                "intro hp",
                "intro hr",
                "intro hsigned",
                "intro hfactor",
                "intro hmul",
                "intro hP",
                "intro hT",
                "intro hA",
                f"have hscale : {scale_prefix}",
                "specialize gauss_signed_pointwise_mul_scale_mod p",
                "specialize gauss_signed_pointwise_mul_scale_mod h",
                "specialize gauss_signed_pointwise_mul_scale_mod r",
                "specialize gauss_signed_pointwise_mul_scale_mod a",
                "specialize gauss_signed_pointwise_mul_scale_mod b",
                "specialize gauss_signed_pointwise_mul_scale_mod c",
                "specialize gauss_signed_pointwise_mul_scale_mod mb",
                "specialize gauss_signed_pointwise_mul_scale_mod mc",
                "specialize gauss_signed_pointwise_mul_scale_mod sb",
                "specialize gauss_signed_pointwise_mul_scale_mod sc",
                "specialize gauss_signed_pointwise_mul_scale_mod fb",
                "specialize gauss_signed_pointwise_mul_scale_mod fc",
                "specialize gauss_signed_pointwise_mul_scale_mod tb",
                "specialize gauss_signed_pointwise_mul_scale_mod tc",
                "apply gauss_signed_pointwise_mul_scale_mod",
                "exact hp",
                "exact hr",
                "exact hsigned",
                "exact hfactor",
                "exact hmul",
                "specialize beta_product_pointwise_scale_mod p",
                "specialize beta_product_pointwise_scale_mod a",
                "specialize beta_product_pointwise_scale_mod b",
                "specialize beta_product_pointwise_scale_mod c",
                "specialize beta_product_pointwise_scale_mod tb",
                "specialize beta_product_pointwise_scale_mod tc",
                "specialize beta_product_pointwise_scale_mod h",
                "specialize beta_product_pointwise_scale_mod P",
                "specialize beta_product_pointwise_scale_mod T",
                "specialize beta_product_pointwise_scale_mod A",
                "apply beta_product_pointwise_scale_mod",
                "exact hscale",
                "exact hP",
                "exact hT",
                "exact hA",
            ),
            "The scaled canonical-source product is congruent to the product of signed magnitudes.",
        ),
    )


__all__ = ["make_gauss_signed_pointwise_product_candidate_theorems"]
