"""Constructive existential endpoint for Gauss's lemma.

Starting from an odd prime ``p = 2*h + 1``, a multiplier not divisible by
``p``, and a beta-coded canonical half range, this isolated candidate builds
all coding and fold witnesses needed by the product-composition layer.  Its
public conclusion exposes only the reflection count ``e``, the two powers
``A`` and ``R``, their balanced congruence, and a hidden signed-prefix witness
showing what ``e`` counts.

The apparent ``Pow(2*h,e,R)`` below is still only an authoring expansion.  A
hygienic helper substitutes the audited compound term ``2*h`` into the
ordinary beta-repeat/product definition before parsing.  No exponentiation,
sequence, product, prime, or congruence primitive is added to the language or
kernel, and this candidate is not publicly registered.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_product_candidate import prime
from .finite_fold_surface import (
    _identifier as _fold_identifier,
    bit_count,
    power_relation,
    product_relation,
)
from .finite_permutation_theorems import injective_prefix
from .finite_pointwise_mul_product_candidate import pointwise_mul_prefix
from .gauss_magnitude_permutation_candidate import (
    magnitude_range_prefix,
    predecessor_recode_prefix,
)
from .gauss_sign_product_candidate import sign_factor_prefix
from .gauss_signed_prefix_candidate import (
    half_range,
    not_divides,
    signed_half_prefix,
)


def double_half_power_relation(
    half: str,
    exponent: str,
    result: str,
    *,
    tag: str,
) -> str:
    """Expand relational exponentiation with the audited base ``2*half``."""

    safe_half = _fold_identifier(half, "half")
    safe_exponent = _fold_identifier(exponent, "power exponent")
    safe_result = _fold_identifier(result, "power result")
    safe_tag = _fold_identifier(tag, "binder tag")
    sentinel = f"gle_double_half_base_{safe_tag}"
    expanded = power_relation(
        sentinel,
        safe_exponent,
        safe_result,
        tag=f"{safe_tag}_expanded",
    )
    if expanded.count(sentinel) == 0:
        raise AssertionError("unexpected Pow expansion without its base")
    return expanded.replace(sentinel, f"(2 * {safe_half})")


def _double_half_sign_factor_prefix(
    bit_code: str,
    bit_scale: str,
    factor_code: str,
    factor_scale: str,
    half: str,
    length: str,
    *,
    tag: str,
) -> str:
    """Instantiate the sign-factor predecessor with the compound ``2*half``."""

    safe_half = _fold_identifier(half, "half")
    safe_tag = _fold_identifier(tag, "binder tag")
    sentinel = f"gle_double_half_predecessor_{safe_tag}"
    expanded = sign_factor_prefix(
        bit_code,
        bit_scale,
        factor_code,
        factor_scale,
        sentinel,
        length,
        tag=f"{safe_tag}_expanded",
    )
    if expanded.count(sentinel) == 0:
        raise AssertionError("unexpected sign-factor expansion without predecessor")
    return expanded.replace(sentinel, f"(2 * {safe_half})")


def _balanced_mod(left: str, right: str, *, tag: str) -> str:
    return (
        f"exists gle_left_{tag} gle_right_{tag}. "
        f"{left} + p * gle_left_{tag} = {right} + p * gle_right_{tag}"
    )


def make_gauss_lemma_endpoint_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the full witness-producing Gauss congruence endpoint."""

    prime_p = prime("p", tag="lemma_endpoint_prime")
    nondivisor = not_divides("p", "a", tag="lemma_endpoint_nondivisor")
    canonical_half = half_range(
        "b", "c", "h", tag="lemma_endpoint_half_range"
    )
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
        tag="lemma_endpoint_signed_prefix",
    )
    count = bit_count(
        "sb", "sc", "h", "e", tag="lemma_endpoint_bit_count"
    )
    local_count = bit_count(
        "x2", "x3", "h", "e", tag="lemma_endpoint_local_bit_count"
    )
    magnitude_range = magnitude_range_prefix(
        "x", "x1", "h", "h", tag="lemma_endpoint_magnitude_range"
    )
    magnitude_injective = injective_prefix(
        "x", "x1", "h", tag="lemma_endpoint_magnitude_injective"
    )
    predecessor_recode = predecessor_recode_prefix(
        "x",
        "x1",
        "rb",
        "rc",
        "h",
        tag="lemma_endpoint_predecessor_recode",
    )
    canonical_product = product_relation(
        "b", "c", "h", "P", tag="lemma_endpoint_canonical_product"
    )
    magnitude_product = product_relation(
        "x", "x1", "h", "M", tag="lemma_endpoint_magnitude_product"
    )
    sign_factors = _double_half_sign_factor_prefix(
        "x2",
        "x3",
        "fb",
        "fc",
        "h",
        "h",
        tag="lemma_endpoint_sign_factors",
    )
    sign_product = product_relation(
        "fb", "fc", "h", "Sprod", tag="lemma_endpoint_sign_product"
    )
    sign_power = double_half_power_relation(
        "h", "x4", "R", tag="lemma_endpoint_sign_power"
    )
    pointwise_products = pointwise_mul_prefix(
        "x",
        "x1",
        "x9",
        "x10",
        "tb",
        "tc",
        "h",
        tag="lemma_endpoint_pointwise_products",
    )
    target_product = product_relation(
        "tb", "tc", "h", "T", tag="lemma_endpoint_target_product"
    )
    multiplier_power = power_relation(
        "a", "h", "A", tag="lemma_endpoint_multiplier_power"
    )
    result_sign_power = double_half_power_relation(
        "h", "e", "R", tag="lemma_endpoint_result_sign_power"
    )
    result_mod = _balanced_mod("A", "R", tag="lemma_endpoint_result")
    local_result_mod = _balanced_mod(
        "x16", "x12", tag="lemma_endpoint_local_result"
    )

    signed_exists = (
        "exists mb mc sb sc. "
        f"({signed_prefix})"
    )
    count_exists = f"exists e. ({local_count})"
    recode_exists = f"exists rb rc. ({predecessor_recode})"
    canonical_product_exists = f"exists P. ({canonical_product})"
    magnitude_product_exists = f"exists M. ({magnitude_product})"
    sign_package = (
        "exists fb fc Sprod R. "
        f"(({sign_factors}) /\ (({sign_product}) /\ "
        f"(({sign_power}) /\ Sprod = R)))"
    )
    pointwise_package = (
        "exists tb tc T. "
        f"(({pointwise_products}) /\ (({target_product}) /\ "
        "T = x8 * x11))"
    )
    multiplier_power_exists = f"exists A. ({multiplier_power})"
    hidden_signed_count = (
        "exists mb mc sb sc. "
        f"(({signed_prefix}) /\ ({count}))"
    )
    endpoint = (
        "exists e A R. "
        f"(({multiplier_power}) /\ (({result_sign_power}) /\ "
        f"(({hidden_signed_count}) /\ ({result_mod}))))"
    )

    return (
        spec(
            "gauss_lemma_power_congruence_exists",
            "forall p h a b c. p = 2 * h + 1 -> "
            f"({prime_p}) -> ({nondivisor}) -> ({canonical_half}) -> "
            f"({endpoint})",
            (
                "gauss_half_range_signed_prefix_exists",
                "gauss_signed_half_bit_count_exists",
                "gauss_signed_half_magnitude_range",
                "gauss_signed_half_magnitude_injective",
                "gauss_signed_half_predecessor_recode_exists",
                "beta_product_exists",
                "beta_sign_factor_product_power_exists",
                "beta_pointwise_mul_product_exists",
                "pow_exists",
                "gauss_signed_products_cancel_mod",
            ),
            (
                "intro p",
                "intro h",
                "intro a",
                "intro b",
                "intro c",
                "intro hpodd",
                "intro hprime",
                "intro hnotdiv",
                "intro hhalf",
                "have hpsucc : p = S (2 * h)",
                "trans 2 * h + 1",
                "exact hpodd",
                "simp",
                f"have hsigned_exists : {signed_exists}",
                "specialize gauss_half_range_signed_prefix_exists p",
                "specialize gauss_half_range_signed_prefix_exists h",
                "specialize gauss_half_range_signed_prefix_exists a",
                "specialize gauss_half_range_signed_prefix_exists b",
                "specialize gauss_half_range_signed_prefix_exists c",
                "apply gauss_half_range_signed_prefix_exists",
                "exact hpodd",
                "exact hprime",
                "exact hnotdiv",
                "exact hhalf",
                "cases hsigned_exists",
                "cases hsigned_exists_witness",
                "cases hsigned_exists_witness_witness",
                "cases hsigned_exists_witness_witness_witness",
                f"have hcount_exists : {count_exists}",
                "specialize gauss_signed_half_bit_count_exists p",
                "specialize gauss_signed_half_bit_count_exists h",
                "specialize gauss_signed_half_bit_count_exists a",
                "specialize gauss_signed_half_bit_count_exists b",
                "specialize gauss_signed_half_bit_count_exists c",
                "specialize gauss_signed_half_bit_count_exists x",
                "specialize gauss_signed_half_bit_count_exists x1",
                "specialize gauss_signed_half_bit_count_exists x2",
                "specialize gauss_signed_half_bit_count_exists x3",
                "specialize gauss_signed_half_bit_count_exists h",
                "apply gauss_signed_half_bit_count_exists",
                "exact hsigned_exists_witness_witness_witness_witness",
                "cases hcount_exists",
                f"have hmagnitude_range : {magnitude_range}",
                "specialize gauss_signed_half_magnitude_range p",
                "specialize gauss_signed_half_magnitude_range h",
                "specialize gauss_signed_half_magnitude_range a",
                "specialize gauss_signed_half_magnitude_range b",
                "specialize gauss_signed_half_magnitude_range c",
                "specialize gauss_signed_half_magnitude_range x",
                "specialize gauss_signed_half_magnitude_range x1",
                "specialize gauss_signed_half_magnitude_range x2",
                "specialize gauss_signed_half_magnitude_range x3",
                "specialize gauss_signed_half_magnitude_range h",
                "apply gauss_signed_half_magnitude_range",
                "exact hsigned_exists_witness_witness_witness_witness",
                f"have hmagnitude_injective : {magnitude_injective}",
                "specialize gauss_signed_half_magnitude_injective p",
                "specialize gauss_signed_half_magnitude_injective h",
                "specialize gauss_signed_half_magnitude_injective a",
                "specialize gauss_signed_half_magnitude_injective b",
                "specialize gauss_signed_half_magnitude_injective c",
                "specialize gauss_signed_half_magnitude_injective x",
                "specialize gauss_signed_half_magnitude_injective x1",
                "specialize gauss_signed_half_magnitude_injective x2",
                "specialize gauss_signed_half_magnitude_injective x3",
                "apply gauss_signed_half_magnitude_injective",
                "exact hpodd",
                "exact hprime",
                "exact hnotdiv",
                "exact hhalf",
                "exact hsigned_exists_witness_witness_witness_witness",
                f"have hrecode_exists : {recode_exists}",
                "specialize gauss_signed_half_predecessor_recode_exists p",
                "specialize gauss_signed_half_predecessor_recode_exists h",
                "specialize gauss_signed_half_predecessor_recode_exists a",
                "specialize gauss_signed_half_predecessor_recode_exists b",
                "specialize gauss_signed_half_predecessor_recode_exists c",
                "specialize gauss_signed_half_predecessor_recode_exists x",
                "specialize gauss_signed_half_predecessor_recode_exists x1",
                "specialize gauss_signed_half_predecessor_recode_exists x2",
                "specialize gauss_signed_half_predecessor_recode_exists x3",
                "apply gauss_signed_half_predecessor_recode_exists",
                "exact hsigned_exists_witness_witness_witness_witness",
                "cases hrecode_exists",
                "cases hrecode_exists_witness",
                f"have hcanonical_product_exists : {canonical_product_exists}",
                "specialize beta_product_exists b",
                "specialize beta_product_exists c",
                "specialize beta_product_exists h",
                "exact beta_product_exists",
                "cases hcanonical_product_exists",
                f"have hmagnitude_product_exists : {magnitude_product_exists}",
                "specialize beta_product_exists x",
                "specialize beta_product_exists x1",
                "specialize beta_product_exists h",
                "exact beta_product_exists",
                "cases hmagnitude_product_exists",
                f"have hsign_package : {sign_package}",
                "specialize beta_sign_factor_product_power_exists p",
                "specialize beta_sign_factor_product_power_exists (2 * h)",
                "specialize beta_sign_factor_product_power_exists x2",
                "specialize beta_sign_factor_product_power_exists x3",
                "specialize beta_sign_factor_product_power_exists h",
                "specialize beta_sign_factor_product_power_exists x4",
                "apply beta_sign_factor_product_power_exists",
                "exact hpsucc",
                "exact hcount_exists_witness",
                "cases hsign_package",
                "cases hsign_package_witness",
                "cases hsign_package_witness_witness",
                "cases hsign_package_witness_witness_witness",
                "cases hsign_package_witness_witness_witness_witness",
                "cases hsign_package_witness_witness_witness_witness_right",
                "cases hsign_package_witness_witness_witness_witness_right_right",
                f"have hpointwise_package : {pointwise_package}",
                "specialize beta_pointwise_mul_product_exists x",
                "specialize beta_pointwise_mul_product_exists x1",
                "specialize beta_pointwise_mul_product_exists x9",
                "specialize beta_pointwise_mul_product_exists x10",
                "specialize beta_pointwise_mul_product_exists h",
                "specialize beta_pointwise_mul_product_exists x8",
                "specialize beta_pointwise_mul_product_exists x11",
                "apply beta_pointwise_mul_product_exists",
                "exact hmagnitude_product_exists_witness",
                "exact hsign_package_witness_witness_witness_witness_right_left",
                "cases hpointwise_package",
                "cases hpointwise_package_witness",
                "cases hpointwise_package_witness_witness",
                "cases hpointwise_package_witness_witness_witness",
                "cases hpointwise_package_witness_witness_witness_right",
                f"have hmultiplier_power_exists : {multiplier_power_exists}",
                "specialize pow_exists a",
                "specialize pow_exists h",
                "exact pow_exists",
                "cases hmultiplier_power_exists",
                f"have hcancelled : {local_result_mod}",
                "specialize gauss_signed_products_cancel_mod p",
                "specialize gauss_signed_products_cancel_mod h",
                "specialize gauss_signed_products_cancel_mod (2 * h)",
                "specialize gauss_signed_products_cancel_mod a",
                "specialize gauss_signed_products_cancel_mod b",
                "specialize gauss_signed_products_cancel_mod c",
                "specialize gauss_signed_products_cancel_mod x",
                "specialize gauss_signed_products_cancel_mod x1",
                "specialize gauss_signed_products_cancel_mod x5",
                "specialize gauss_signed_products_cancel_mod x6",
                "specialize gauss_signed_products_cancel_mod x2",
                "specialize gauss_signed_products_cancel_mod x3",
                "specialize gauss_signed_products_cancel_mod x9",
                "specialize gauss_signed_products_cancel_mod x10",
                "specialize gauss_signed_products_cancel_mod x13",
                "specialize gauss_signed_products_cancel_mod x14",
                "specialize gauss_signed_products_cancel_mod x4",
                "specialize gauss_signed_products_cancel_mod x7",
                "specialize gauss_signed_products_cancel_mod x8",
                "specialize gauss_signed_products_cancel_mod x11",
                "specialize gauss_signed_products_cancel_mod x15",
                "specialize gauss_signed_products_cancel_mod x16",
                "specialize gauss_signed_products_cancel_mod x12",
                "apply gauss_signed_products_cancel_mod",
                "exact hprime",
                "exact hpsucc",
                "refl",
                "exact hsigned_exists_witness_witness_witness_witness",
                "exact hsign_package_witness_witness_witness_witness_left",
                "exact hpointwise_package_witness_witness_witness_left",
                "exact hmagnitude_range",
                "exact hmagnitude_injective",
                "exact hrecode_exists_witness_witness",
                "exact hhalf",
                "exact hcount_exists_witness",
                "exact hcanonical_product_exists_witness",
                "exact hmagnitude_product_exists_witness",
                "exact hsign_package_witness_witness_witness_witness_right_left",
                "exact hpointwise_package_witness_witness_witness_right_left",
                "exact hmultiplier_power_exists_witness",
                "exact hsign_package_witness_witness_witness_witness_right_right_left",
                "exists x4",
                "exists x16",
                "exists x12",
                "split",
                "exact hmultiplier_power_exists_witness",
                "split",
                "exact hsign_package_witness_witness_witness_witness_right_right_left",
                "split",
                "exists x",
                "exists x1",
                "exists x2",
                "exists x3",
                "split",
                "exact hsigned_exists_witness_witness_witness_witness",
                "exact hcount_exists_witness",
                "exact hcancelled",
            ),
            "Gauss's signed half-range count controls a^h modulo the odd prime.",
        ),
    )


__all__ = [
    "double_half_power_relation",
    "make_gauss_lemma_endpoint_candidate_theorems",
]
