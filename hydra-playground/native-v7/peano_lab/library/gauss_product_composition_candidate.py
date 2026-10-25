"""Isolated product composition and cancellation for Gauss's lemma.

The preceding candidate layers separately establish four facts: scaled
canonical factors are congruent to signed pointwise products, magnitudes
permute the canonical half range, sign-factor products are powers of the odd
predecessor, and synchronized pointwise products multiply exactly.  This
module composes those facts into

``A * P == P * R (mod p)``

and then cancels the canonical half-range product ``P``.  Cancellation is
constructive: the half-range entries are positive and below the prime, the
generic finite-product theorem makes ``P`` coprime to ``p``, and the existing
Bezout-based congruence theorem cancels it.

All notation below is expanded into ordinary first-order PA before parsing.
The module remains an unregistered candidate and introduces no trusted
sequence, product, power, prime, coprime, or congruence primitive.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_product_candidate import coprime, prime
from .finite_bitcount_theorems import bit_count
from .finite_fold_surface import power_relation, product_relation
from .finite_permutation_theorems import injective_prefix
from .finite_pointwise_mul_product_candidate import pointwise_mul_prefix
from .finite_prime_product_coprime_candidate import positive_below_prime_prefix
from .gauss_magnitude_permutation_candidate import (
    magnitude_range_prefix,
    predecessor_recode_prefix,
)
from .gauss_sign_product_candidate import sign_factor_prefix
from .gauss_signed_prefix_candidate import half_range, signed_half_prefix


def _balanced_mod(left: str, right: str, *, tag: str) -> str:
    """Expand balanced congruence for module-owned arithmetic terms."""

    return (
        f"exists gpc_left_{tag} gpc_right_{tag}. "
        f"{left} + p * gpc_left_{tag} = "
        f"{right} + p * gpc_right_{tag}"
    )


def make_gauss_product_composition_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build half-product coprimality, composition, and cancellation specs."""

    prime_p = prime("p", tag="gauss_composition_prime")
    canonical_half = half_range(
        "b", "c", "h", tag="gauss_composition_half_range"
    )
    canonical_bounds = positive_below_prime_prefix(
        "b", "c", "h", "p", tag="gauss_composition_bounds"
    )
    canonical_product = product_relation(
        "b", "c", "h", "P", tag="gauss_composition_canonical_product"
    )
    canonical_coprime = coprime(
        "P", "p", tag="gauss_composition_canonical_coprime"
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
        tag="gauss_composition_signed_prefix",
    )
    sign_factors = sign_factor_prefix(
        "sb",
        "sc",
        "fb",
        "fc",
        "r",
        "h",
        tag="gauss_composition_sign_factors",
    )
    pointwise_products = pointwise_mul_prefix(
        "mb",
        "mc",
        "fb",
        "fc",
        "tb",
        "tc",
        "h",
        tag="gauss_composition_pointwise_products",
    )
    magnitude_range = magnitude_range_prefix(
        "mb", "mc", "h", "h", tag="gauss_composition_magnitude_range"
    )
    magnitude_injective = injective_prefix(
        "mb", "mc", "h", tag="gauss_composition_magnitude_injective"
    )
    predecessor_recode = predecessor_recode_prefix(
        "mb",
        "mc",
        "rb",
        "rc",
        "h",
        tag="gauss_composition_predecessor_recode",
    )
    sign_count = bit_count(
        "sb", "sc", "h", "e", tag="gauss_composition_sign_count"
    )
    magnitude_product = product_relation(
        "mb", "mc", "h", "M", tag="gauss_composition_magnitude_product"
    )
    sign_product = product_relation(
        "fb", "fc", "h", "Sprod", tag="gauss_composition_sign_product"
    )
    target_product = product_relation(
        "tb", "tc", "h", "T", tag="gauss_composition_target_product"
    )
    multiplier_power = power_relation(
        "a", "h", "A", tag="gauss_composition_multiplier_power"
    )
    sign_power = power_relation(
        "r", "e", "R", tag="gauss_composition_sign_power"
    )
    scaled_target_balance = _balanced_mod(
        "A * P", "T", tag="scaled_target"
    )
    product_balance = _balanced_mod(
        "A * P", "P * R", tag="product_balance"
    )
    normalized_product_balance = _balanced_mod(
        "P * A", "P * R", tag="normalized_product_balance"
    )
    cancelled_balance = _balanced_mod("A", "R", tag="cancelled_balance")

    shared_variables = (
        "p h r a b c mb mc rb rc sb sc fb fc tb tc e "
        "P M Sprod T A R"
    )
    shared_premises = (
        f"p = S r -> r = 2 * h -> ({signed_prefix}) -> "
        f"({sign_factors}) -> ({pointwise_products}) -> "
        f"({magnitude_range}) -> ({magnitude_injective}) -> "
        f"({predecessor_recode}) -> ({canonical_half}) -> "
        f"({sign_count}) -> ({canonical_product}) -> "
        f"({magnitude_product}) -> ({sign_product}) -> "
        f"({target_product}) -> ({multiplier_power}) -> ({sign_power}) -> "
    )

    return (
        spec(
            "prime_half_range_product_coprime",
            f"forall p h b c P. p = 2 * h + 1 -> ({prime_p}) -> "
            f"({canonical_half}) -> ({canonical_product}) -> "
            f"({canonical_coprime})",
            (
                "beta_half_range_entry_bounds",
                "prime_positive_bounded_product_coprime",
            ),
            (
                "intro p",
                "intro h",
                "intro b",
                "intro c",
                "intro P",
                "intro hp",
                "intro hprime",
                "intro hhalf",
                "intro hproduct",
                f"have hbounds : {canonical_bounds}",
                "intro i",
                "intro x",
                "intro hi",
                "intro hx",
                "specialize beta_half_range_entry_bounds p",
                "specialize beta_half_range_entry_bounds h",
                "specialize beta_half_range_entry_bounds b",
                "specialize beta_half_range_entry_bounds c",
                "specialize beta_half_range_entry_bounds i",
                "specialize beta_half_range_entry_bounds x",
                "apply beta_half_range_entry_bounds",
                "exact hp",
                "exact hhalf",
                "exact hi",
                "exact hx",
                "specialize prime_positive_bounded_product_coprime p",
                "specialize prime_positive_bounded_product_coprime b",
                "specialize prime_positive_bounded_product_coprime c",
                "specialize prime_positive_bounded_product_coprime h",
                "specialize prime_positive_bounded_product_coprime P",
                "apply prime_positive_bounded_product_coprime",
                "exact hprime",
                "exact hbounds",
                "exact hproduct",
            ),
            "The canonical half-range product is coprime to its odd prime modulus.",
        ),
        spec(
            "gauss_signed_products_balance_mod",
            f"forall {shared_variables}. {shared_premises}({product_balance})",
            (
                "gauss_signed_pointwise_mul_product_mod",
                "gauss_magnitude_product_eq_half_range",
                "beta_sign_factor_product_power",
                "beta_product_pointwise_mul_exact",
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
                "intro rb",
                "intro rc",
                "intro sb",
                "intro sc",
                "intro fb",
                "intro fc",
                "intro tb",
                "intro tc",
                "intro e",
                "intro P",
                "intro M",
                "intro Sprod",
                "intro T",
                "intro A",
                "intro R",
                "intro hp",
                "intro hr",
                "intro hsigned",
                "intro hsigns",
                "intro hpointwise",
                "intro hmagnitude_range",
                "intro hmagnitude_injective",
                "intro hrecode",
                "intro hhalf",
                "intro hcount",
                "intro hP",
                "intro hM",
                "intro hS",
                "intro hT",
                "intro hA",
                "intro hR",
                f"have hscaled : {scaled_target_balance}",
                "specialize gauss_signed_pointwise_mul_product_mod p",
                "specialize gauss_signed_pointwise_mul_product_mod h",
                "specialize gauss_signed_pointwise_mul_product_mod r",
                "specialize gauss_signed_pointwise_mul_product_mod a",
                "specialize gauss_signed_pointwise_mul_product_mod b",
                "specialize gauss_signed_pointwise_mul_product_mod c",
                "specialize gauss_signed_pointwise_mul_product_mod mb",
                "specialize gauss_signed_pointwise_mul_product_mod mc",
                "specialize gauss_signed_pointwise_mul_product_mod sb",
                "specialize gauss_signed_pointwise_mul_product_mod sc",
                "specialize gauss_signed_pointwise_mul_product_mod fb",
                "specialize gauss_signed_pointwise_mul_product_mod fc",
                "specialize gauss_signed_pointwise_mul_product_mod tb",
                "specialize gauss_signed_pointwise_mul_product_mod tc",
                "specialize gauss_signed_pointwise_mul_product_mod P",
                "specialize gauss_signed_pointwise_mul_product_mod T",
                "specialize gauss_signed_pointwise_mul_product_mod A",
                "apply gauss_signed_pointwise_mul_product_mod",
                "exact hp",
                "exact hr",
                "exact hsigned",
                "exact hsigns",
                "exact hpointwise",
                "exact hP",
                "exact hT",
                "exact hA",
                "have hPM : P = M",
                "specialize gauss_magnitude_product_eq_half_range mb",
                "specialize gauss_magnitude_product_eq_half_range mc",
                "specialize gauss_magnitude_product_eq_half_range rb",
                "specialize gauss_magnitude_product_eq_half_range rc",
                "specialize gauss_magnitude_product_eq_half_range b",
                "specialize gauss_magnitude_product_eq_half_range c",
                "specialize gauss_magnitude_product_eq_half_range h",
                "specialize gauss_magnitude_product_eq_half_range P",
                "specialize gauss_magnitude_product_eq_half_range M",
                "apply gauss_magnitude_product_eq_half_range",
                "exact hmagnitude_range",
                "exact hmagnitude_injective",
                "exact hrecode",
                "exact hhalf",
                "exact hP",
                "exact hM",
                "have hSR : Sprod = R",
                "specialize beta_sign_factor_product_power sb",
                "specialize beta_sign_factor_product_power sc",
                "specialize beta_sign_factor_product_power fb",
                "specialize beta_sign_factor_product_power fc",
                "specialize beta_sign_factor_product_power r",
                "specialize beta_sign_factor_product_power h",
                "specialize beta_sign_factor_product_power e",
                "specialize beta_sign_factor_product_power Sprod",
                "specialize beta_sign_factor_product_power R",
                "apply beta_sign_factor_product_power",
                "exact hcount",
                "exact hsigns",
                "exact hS",
                "exact hR",
                "have hTMS : T = M * Sprod",
                "specialize beta_product_pointwise_mul_exact mb",
                "specialize beta_product_pointwise_mul_exact mc",
                "specialize beta_product_pointwise_mul_exact fb",
                "specialize beta_product_pointwise_mul_exact fc",
                "specialize beta_product_pointwise_mul_exact tb",
                "specialize beta_product_pointwise_mul_exact tc",
                "specialize beta_product_pointwise_mul_exact h",
                "specialize beta_product_pointwise_mul_exact M",
                "specialize beta_product_pointwise_mul_exact Sprod",
                "specialize beta_product_pointwise_mul_exact T",
                "apply beta_product_pointwise_mul_exact",
                "exact hpointwise",
                "exact hM",
                "exact hS",
                "exact hT",
                "cases hscaled",
                "cases hscaled_witness",
                "exists x",
                "exists x1",
                "trans T + p * x1",
                "exact hscaled_witness_witness",
                "congr",
                "trans M * Sprod",
                "exact hTMS",
                "congr",
                "symm",
                "exact hPM",
                "exact hSR",
                "refl",
            ),
            "The four Gauss product layers compose to A*P == P*r^e modulo p.",
        ),
        spec(
            "gauss_signed_products_cancel_mod",
            f"forall {shared_variables}. ({prime_p}) -> "
            f"{shared_premises}({cancelled_balance})",
            (
                "gauss_signed_products_balance_mod",
                "prime_half_range_product_coprime",
                "prime_nonzero",
                "mod_eq_cancel_coprime",
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
                "intro rb",
                "intro rc",
                "intro sb",
                "intro sc",
                "intro fb",
                "intro fc",
                "intro tb",
                "intro tc",
                "intro e",
                "intro P",
                "intro M",
                "intro Sprod",
                "intro T",
                "intro A",
                "intro R",
                "intro hprime",
                "intro hp",
                "intro hr",
                "intro hsigned",
                "intro hsigns",
                "intro hpointwise",
                "intro hmagnitude_range",
                "intro hmagnitude_injective",
                "intro hrecode",
                "intro hhalf",
                "intro hcount",
                "intro hP",
                "intro hM",
                "intro hS",
                "intro hT",
                "intro hA",
                "intro hR",
                f"have hbalance : {product_balance}",
                "specialize gauss_signed_products_balance_mod p",
                "specialize gauss_signed_products_balance_mod h",
                "specialize gauss_signed_products_balance_mod r",
                "specialize gauss_signed_products_balance_mod a",
                "specialize gauss_signed_products_balance_mod b",
                "specialize gauss_signed_products_balance_mod c",
                "specialize gauss_signed_products_balance_mod mb",
                "specialize gauss_signed_products_balance_mod mc",
                "specialize gauss_signed_products_balance_mod rb",
                "specialize gauss_signed_products_balance_mod rc",
                "specialize gauss_signed_products_balance_mod sb",
                "specialize gauss_signed_products_balance_mod sc",
                "specialize gauss_signed_products_balance_mod fb",
                "specialize gauss_signed_products_balance_mod fc",
                "specialize gauss_signed_products_balance_mod tb",
                "specialize gauss_signed_products_balance_mod tc",
                "specialize gauss_signed_products_balance_mod e",
                "specialize gauss_signed_products_balance_mod P",
                "specialize gauss_signed_products_balance_mod M",
                "specialize gauss_signed_products_balance_mod Sprod",
                "specialize gauss_signed_products_balance_mod T",
                "specialize gauss_signed_products_balance_mod A",
                "specialize gauss_signed_products_balance_mod R",
                "apply gauss_signed_products_balance_mod",
                "exact hp",
                "exact hr",
                "exact hsigned",
                "exact hsigns",
                "exact hpointwise",
                "exact hmagnitude_range",
                "exact hmagnitude_injective",
                "exact hrecode",
                "exact hhalf",
                "exact hcount",
                "exact hP",
                "exact hM",
                "exact hS",
                "exact hT",
                "exact hA",
                "exact hR",
                "have hodd : p = 2 * h + 1",
                "trans S r",
                "exact hp",
                "trans S (2 * h)",
                "congr",
                "exact hr",
                "simp",
                f"have hcoprime : {canonical_coprime}",
                "specialize prime_half_range_product_coprime p",
                "specialize prime_half_range_product_coprime h",
                "specialize prime_half_range_product_coprime b",
                "specialize prime_half_range_product_coprime c",
                "specialize prime_half_range_product_coprime P",
                "apply prime_half_range_product_coprime",
                "exact hodd",
                "exact hprime",
                "exact hhalf",
                "exact hP",
                "have hp0 : ~(p = 0)",
                "intro hpzero",
                "specialize prime_nonzero p",
                "apply prime_nonzero",
                "exact hprime",
                "exact hpzero",
                f"have hnormalized : {normalized_product_balance}",
                "cases hbalance",
                "cases hbalance_witness",
                "exists x",
                "exists x1",
                "trans (A * P) + p * x",
                "congr",
                "apply mul_comm",
                "refl",
                "exact hbalance_witness_witness",
                "specialize mod_eq_cancel_coprime p",
                "specialize mod_eq_cancel_coprime P",
                "specialize mod_eq_cancel_coprime A",
                "specialize mod_eq_cancel_coprime R",
                "apply mod_eq_cancel_coprime",
                "exact hp0",
                "exact hcoprime",
                "exact hnormalized",
            ),
            "Coprimality of the half-range product constructively cancels P.",
        ),
    )


__all__ = ["make_gauss_product_composition_candidate_theorems"]
