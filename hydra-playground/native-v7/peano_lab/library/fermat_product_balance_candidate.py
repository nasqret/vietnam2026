"""Static finite-product balance candidate for the native Fermat route.

The theorem here combines the residue reindexing, exact finite products, the
general product-permutation theorem, and pointwise scale-product congruence.
It remains isolated from the public registry until independent WMI discovery
and receipt-pinned admission replays succeed.

All helper relations expand to the unchanged first-order language of Peano
arithmetic.  No product, power, congruence, map, or permutation primitive is
added to the parser or kernel.
"""

from __future__ import annotations

from typing import Any, Callable

from .fermat_residue_map_candidate import not_divides, prime
from .fermat_residue_product_candidate import range_one
from .fermat_scale_product_candidate import product_left_mod, scale_mod_prefix
from .finite_fold_surface import power_relation, product_relation
from .finite_permutation_theorems import bounded_prefix, injective_prefix
from .finite_product_reindex_support import aligned_prefix


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
    names = tuple(f"fpb_{stem}_{safe_tag}" for stem in stems)
    if len(set(names)) != len(names) or set(names) & set(variables):
        raise ValueError("generated Fermat-balance binder captures an argument")
    return names


def residue_reindex_data(
    map_code: str,
    map_scale: str,
    source_code: str,
    source_scale: str,
    target_code: str,
    target_scale: str,
    length: str,
    modulus: str,
    multiplier: str,
    *,
    tag: str,
) -> str:
    """Expand the right-associated residue-reindex data package."""

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
            (modulus, "modulus"),
            (multiplier, "multiplier"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    bounded = bounded_prefix(
        map_code,
        map_scale,
        length,
        tag=f"fpb_{safe_tag}_bounded",
    )
    injective = injective_prefix(
        map_code,
        map_scale,
        length,
        tag=f"fpb_{safe_tag}_injective",
    )
    aligned = aligned_prefix(
        map_code,
        map_scale,
        source_code,
        source_scale,
        target_code,
        target_scale,
        length,
        tag=f"fpb_{safe_tag}_aligned",
    )
    scaled = scale_mod_prefix(
        modulus,
        multiplier,
        source_code,
        source_scale,
        target_code,
        target_scale,
        length,
        tag=f"fpb_{safe_tag}_scaled",
    )
    return f"({bounded}) /\\ (({injective}) /\\ (({aligned}) /\\ ({scaled})))"


def residue_reindex_witness(
    source_code: str,
    source_scale: str,
    length: str,
    modulus: str,
    multiplier: str,
    *,
    tag: str,
) -> str:
    """Expand existential ownership of a residue map and target prefix."""

    variables = tuple(
        _identifier(value, label)
        for value, label in (
            (source_code, "source code"),
            (source_scale, "source scale"),
            (length, "length"),
            (modulus, "modulus"),
            (multiplier, "multiplier"),
        )
    )
    safe_tag = _identifier(tag, "binder tag")
    map_code, map_scale, target_code, target_scale = _binders(
        safe_tag,
        variables,
        ("map_code", "map_scale", "target_code", "target_scale"),
    )
    data = residue_reindex_data(
        map_code,
        map_scale,
        source_code,
        source_scale,
        target_code,
        target_scale,
        length,
        modulus,
        multiplier,
        tag=f"{safe_tag}_data",
    )
    return (
        f"exists {map_code} {map_scale} {target_code} {target_scale}. ({data})"
    )


def make_fermat_product_balance_candidate_theorems(
    spec: Callable[..., Any],
) -> tuple[Any, ...]:
    """Build the isolated product-balance candidate theorem data."""

    prime_p = prime("p", tag="balance_prime")
    nonzero_a = not_divides("p", "a", tag="balance_multiplier")
    source_range = range_one("b", "c", "n", tag="balance_range")
    source_product = product_relation("b", "c", "n", "F", tag="balance_source")
    multiplier_power = power_relation("a", "n", "A", tag="balance_power")
    result = product_left_mod("p", "A", "F", "F", tag="balance_result")

    reindex_exists = residue_reindex_witness(
        "b", "c", "n", "p", "a", tag="balance_reindex"
    )
    target_product_exists = (
        "exists Q. "
        f"({product_relation('x2', 'x3', 'n', 'Q', tag='balance_target_exists')})"
    )
    scaled_product = product_left_mod(
        "p", "A", "F", "x4", tag="balance_scaled_product"
    )

    return (
        spec(
            "prime_mul_residue_product_balance",
            "forall p n a b c F A. "
            f"p = S n -> ({prime_p}) -> ({nonzero_a}) -> ({source_range}) -> "
            f"({source_product}) -> ({multiplier_power}) -> ({result})",
            (
                "prime_mul_residue_reindex_exists",
                "beta_product_pointwise_scale_mod",
                "beta_product_exists",
                "beta_product_permutation_invariant",
            ),
            (
                "intro p",
                "intro n",
                "intro a",
                "intro b",
                "intro c",
                "intro F",
                "intro A",
                "intro hpn",
                "intro hp",
                "intro hnotdiv",
                "intro hrange",
                "intro hF",
                "intro hA",
                f"have hreindex : {reindex_exists}",
                "specialize prime_mul_residue_reindex_exists p",
                "specialize prime_mul_residue_reindex_exists n",
                "specialize prime_mul_residue_reindex_exists a",
                "specialize prime_mul_residue_reindex_exists b",
                "specialize prime_mul_residue_reindex_exists c",
                "apply prime_mul_residue_reindex_exists",
                "exact hpn",
                "exact hp",
                "exact hnotdiv",
                "exact hrange",
                "cases hreindex",
                "cases hreindex_witness",
                "cases hreindex_witness_witness",
                "cases hreindex_witness_witness_witness",
                "cases hreindex_witness_witness_witness_witness",
                "cases hreindex_witness_witness_witness_witness_right",
                "cases hreindex_witness_witness_witness_witness_right_right",
                f"have htarget_product_exists : {target_product_exists}",
                "specialize beta_product_exists x2",
                "specialize beta_product_exists x3",
                "specialize beta_product_exists n",
                "exact beta_product_exists",
                "cases htarget_product_exists",
                "have hFQ : F = x4",
                "specialize beta_product_permutation_invariant n",
                "specialize beta_product_permutation_invariant x",
                "specialize beta_product_permutation_invariant x1",
                "specialize beta_product_permutation_invariant b",
                "specialize beta_product_permutation_invariant c",
                "specialize beta_product_permutation_invariant x2",
                "specialize beta_product_permutation_invariant x3",
                "specialize beta_product_permutation_invariant F",
                "specialize beta_product_permutation_invariant x4",
                "apply beta_product_permutation_invariant",
                "exact hreindex_witness_witness_witness_witness_left",
                "exact hreindex_witness_witness_witness_witness_right_left",
                "exact hreindex_witness_witness_witness_witness_right_right_left",
                "exact hF",
                "exact htarget_product_exists_witness",
                f"have hscale : {scaled_product}",
                "specialize beta_product_pointwise_scale_mod p",
                "specialize beta_product_pointwise_scale_mod a",
                "specialize beta_product_pointwise_scale_mod b",
                "specialize beta_product_pointwise_scale_mod c",
                "specialize beta_product_pointwise_scale_mod x2",
                "specialize beta_product_pointwise_scale_mod x3",
                "specialize beta_product_pointwise_scale_mod n",
                "specialize beta_product_pointwise_scale_mod F",
                "specialize beta_product_pointwise_scale_mod x4",
                "specialize beta_product_pointwise_scale_mod A",
                "apply beta_product_pointwise_scale_mod",
                "exact hreindex_witness_witness_witness_witness_right_right_right",
                "exact hF",
                "exact htarget_product_exists_witness",
                "exact hA",
                "rewrite <- hFQ at hscale",
                "exact hscale",
            ),
            "Scaling the nonzero residues modulo a prime preserves their exact product modulo p.",
        ),
    )


__all__ = [
    "make_fermat_product_balance_candidate_theorems",
    "residue_reindex_data",
    "residue_reindex_witness",
]
