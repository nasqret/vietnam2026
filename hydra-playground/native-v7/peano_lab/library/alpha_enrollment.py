"""Code-owned enrollment manifest for the cumulative alpha library.

This module names the exact private factory rows that belong to alpha.  It is
deliberately independent of the research JSON receipts: receipts record
evidence, while this Python manifest controls runtime membership.  Importing
the module constructs specifications only; it never replays or admits a proof.

The canonical order is frozen as

``stable -> quadratic reciprocity -> strict-HA candidates -> K3B``.

One specification, ``mod_eq_add_cancel_left``, occurs in both the QR and HA
sources.  The two values must be exactly equal.  Its first (QR) position is
retained by :mod:`peano_lab.library.editions`.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from types import MappingProxyType

from .quadratic_reciprocity_stack import (
    QR_ROOT_NAME,
    QuadraticReciprocityStack,
    build_quadratic_reciprocity_stack,
)
from .theorems import THEOREMS, TheoremSpec


class AlphaEnrollmentError(ValueError):
    """The code-owned alpha manifest or a candidate factory is inconsistent."""


@dataclass(frozen=True, slots=True)
class EnrollmentSource:
    """An exact ordered selection from one non-admitting candidate factory."""

    module: str
    factory: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaEnrollment:
    """The three post-stable source tranches before compatible merging."""

    qr_stack: QuadraticReciprocityStack[TheoremSpec]
    qr_specs: tuple[TheoremSpec, ...]
    ha_specs: tuple[TheoremSpec, ...]
    k3b_specs: tuple[TheoremSpec, ...]


HA_CLOSED_ENROLLMENT_MANIFEST: tuple[EnrollmentSource, ...] = (
    EnrollmentSource(
        "ha_canonical_gcd_candidate",
        "make_ha_canonical_gcd_candidate_theorems",
        ("canonical_gcd_exists", "canonical_gcd_functional", "canonical_gcd_exists_unique"),
    ),
    EnrollmentSource(
        "ha_signed_parity_candidate",
        "make_ha_signed_parity_candidate_theorems",
        ("even_odd_exclusive_k1", "even_half_unique"),
    ),
    EnrollmentSource(
        "ha_signed_decode_candidate",
        "make_ha_signed_decode_candidate_theorems",
        (
            "signed_decode_nonnegative_constructor",
            "signed_decode_negative_constructor",
            "signed_decode_total",
            "signed_decode_normal",
            "signed_decode_functional",
            "signed_decode_zero_iff",
            "signed_valid_all",
        ),
    ),
    EnrollmentSource(
        "ha_signed_code_extensional_candidate",
        "make_ha_signed_code_extensional_candidate_theorems",
        (
            "signed_decoded_balance_implies_code_eq",
            "signed_code_eq_implies_decoded_balance",
            "signed_code_eq_iff_balance",
        ),
    ),
    EnrollmentSource(
        "ha_signed_balance_candidate",
        "make_ha_signed_balance_candidate_theorems",
        (
            "signed_balance_total",
            "signed_decode_to_balance",
            "signed_balance_equations_cross_sum",
        ),
    ),
    EnrollmentSource(
        "ha_signed_balance_complete_candidate",
        "make_ha_signed_balance_complete_candidate_theorems",
        (
            "signed_balance_extensional",
            "signed_balance_functional",
            "signed_balance_zero_iff",
        ),
    ),
    EnrollmentSource(
        "ha_signed_negate_candidate",
        "make_ha_signed_negate_candidate_theorems",
        (
            "signed_decode_swap_exists",
            "signed_negate_of_swapped_decode",
            "signed_negate_to_swapped_decode",
            "signed_negate_total",
            "signed_negate_functional",
            "signed_negate_zero",
            "signed_negate_symmetric",
            "signed_negate_involutive",
        ),
    ),
    EnrollmentSource(
        "ha_signed_add_candidate",
        "make_ha_signed_add_candidate_theorems",
        (
            "signed_add_of_decoded_equation",
            "signed_add_to_decoded_equation",
            "signed_add_decoded_iff_equation",
            "signed_add_total",
            "signed_add_functional",
        ),
    ),
    EnrollmentSource(
        "ha_signed_add_laws_candidate",
        "make_ha_signed_add_laws_candidate_theorems",
        (
            "signed_add_commutative",
            "signed_add_zero_left",
            "signed_add_zero_right",
            "signed_add_negate_right_zero",
            "signed_add_negate_left_zero",
        ),
    ),
    EnrollmentSource(
        "ha_signed_add_associative_candidate",
        "make_ha_signed_add_associative_candidate_theorems",
        (
            "add_cross_sum_chain",
            "signed_add_equations_associate",
            "signed_add_associative",
        ),
    ),
    EnrollmentSource(
        "ha_signed_mul_candidate",
        "make_ha_signed_mul_candidate_theorems",
        (
            "signed_mul_of_decoded_equation",
            "signed_mul_to_decoded_equation",
            "signed_mul_decoded_iff_equation",
            "signed_mul_total",
            "signed_mul_functional",
        ),
    ),
    EnrollmentSource(
        "ha_signed_mul_laws_candidate",
        "make_ha_signed_mul_laws_candidate_theorems",
        (
            "signed_mul_commutative",
            "signed_mul_zero_left",
            "signed_mul_zero_right",
            "signed_mul_one_left",
            "signed_mul_one_right",
        ),
    ),
    EnrollmentSource(
        "ha_signed_mul_associative_candidate",
        "make_ha_signed_mul_associative_candidate_theorems",
        (
            "signed_pair_mul_cross_transport",
            "signed_pair_mul_components_associate",
            "signed_mul_equations_associate",
            "signed_mul_associative",
        ),
    ),
    EnrollmentSource(
        "ha_signed_mul_distributive_candidate",
        "make_ha_signed_mul_distributive_candidate_theorems",
        (
            "add_shuffle_middle",
            "add_cross_sum_pairwise",
            "signed_mul_distributive_component",
            "add_balance_outputs_compose",
            "signed_mul_left_cross_sum_distributes",
            "signed_mul_left_distributive",
            "signed_mul_right_distributive",
        ),
    ),
    EnrollmentSource(
        "ha_signed_nat_scale_candidate",
        "make_ha_signed_nat_scale_candidate_theorems",
        (
            "signed_nat_scale_of_decoded_equation",
            "signed_nat_scale_to_decoded_equation",
            "signed_nat_scale_decoded_iff_equation",
            "signed_nat_scale_total",
            "signed_nat_scale_functional",
        ),
    ),
    EnrollmentSource(
        "ha_signed_nat_scale_laws_candidate",
        "make_ha_signed_nat_scale_laws_candidate_theorems",
        (
            "mul_cross_sum_left",
            "signed_nat_scale_equations_compose",
            "signed_nat_scale_zero",
            "signed_nat_scale_one",
            "signed_nat_scale_compose",
        ),
    ),
    EnrollmentSource(
        "ha_signed_bezout_candidate",
        "make_ha_signed_bezout_candidate_theorems",
        (
            "balanced_bezout_equation_transport",
            "balanced_bezout_to_signed_bezout",
            "signed_bezout_to_balanced_bezout",
            "balanced_bezout_iff_signed_bezout_exists",
        ),
    ),
    EnrollmentSource(
        "ha_pair_cell_seed_candidate",
        "make_ha_pair_cell_seed_candidate_theorems",
        (
            "pair_code_constructor",
            "pair_code_output_functional",
            "pair_constructor_valid",
            "cell_constructor",
            "cell_nonzero",
            "nil_not_cell",
            "map_entry_constructor",
        ),
    ),
    EnrollmentSource(
        "ha_pair_shell_candidate",
        "make_ha_pair_shell_candidate_theorems",
        (
            "dt_shell_successor",
            "dt_shell_monotone",
            "dt_right_le_shell",
            "pair_code_shell_lower",
            "pair_code_below_next_shell",
            "pair_code_shell_separated",
        ),
    ),
    EnrollmentSource(
        "ha_pair_injective_candidate",
        "make_ha_pair_injective_candidate_theorems",
        ("double_add_injective", "pair_code_injective"),
    ),
    EnrollmentSource(
        "ha_cell_functional_candidate",
        "make_ha_cell_functional_candidate_theorems",
        ("cell_functional", "cell_head_functional", "cell_tail_functional"),
    ),
    EnrollmentSource(
        "ha_cell_bounds_candidate",
        "make_ha_cell_bounds_candidate_theorems",
        (
            "pair_left_le_code",
            "pair_right_le_code",
            "cell_head_lt_code",
            "cell_tail_lt_code",
        ),
    ),
    EnrollmentSource(
        "ha_signed_bezout_gcd_candidate",
        "make_ha_signed_bezout_gcd_candidate_theorems",
        ("gcd_signed_bezout_exists",),
    ),
    EnrollmentSource(
        "ha_canonical_gcd_edges_candidate",
        "make_ha_canonical_gcd_edges_candidate_theorems",
        (
            "canonical_gcd_zero_right_iff",
            "canonical_gcd_zero_left_iff",
            "canonical_gcd_one_left_iff",
            "canonical_gcd_one_right_iff",
            "canonical_gcd_swap_functional",
        ),
    ),
    EnrollmentSource(
        "ha_relational_lcm_candidate",
        "make_ha_relational_lcm_candidate_theorems",
        (
            "is_lcm_of_dvd",
            "is_lcm_of_dvd_right",
            "product_common_multiple",
            "is_lcm_refl",
            "is_lcm_one_left",
            "is_lcm_one_right",
            "lcm_zero_left_value",
            "lcm_zero_right_value",
            "lcm_zero_left_exists_unique",
            "lcm_zero_right_exists_unique",
        ),
    ),
    EnrollmentSource(
        "ha_generalized_crt_congruence_candidate",
        "make_ha_generalized_crt_congruence_stack",
        ("mod_eq_add_cancel_left", "mod_eq_add_cancel_right", "mod_eq_unscale_nonzero"),
    ),
    EnrollmentSource(
        "ha_generalized_crt_sufficiency_candidate",
        "make_ha_generalized_crt_sufficiency_candidate_theorems",
        (
            "factor_nonzero_right",
            "is_gcd_nonzero_coprime_quotients",
            "generalized_binary_crt_solvable_iff_nonzero",
        ),
    ),
)


K3B_CLOSED_ENROLLMENT_MANIFEST: tuple[EnrollmentSource, ...] = (
    EnrollmentSource(
        "ha_cell_history_candidate",
        "make_ha_cell_history_candidate_theorems",
        ("cell_history_nil", "cell_history_extend", "cell_history_succ_elim"),
    ),
    EnrollmentSource(
        "ha_cell_history_prefix_preservation_candidate",
        "make_ha_cell_history_prefix_preservation_candidate_theorems",
        ("cell_history_extend_preserves_prefix",),
    ),
    EnrollmentSource(
        "ha_cell_list_equations_candidate",
        "make_ha_cell_list_equations_candidate_theorems",
        ("cell_list_zero_iff_nil", "cell_list_succ_iff_cell"),
    ),
    EnrollmentSource(
        "ha_cell_list_length_functional_candidate",
        "make_ha_cell_list_length_functional_candidate_theorems",
        ("cell_list_length_functional",),
    ),
    EnrollmentSource(
        "ha_cell_list_length_bound_candidate",
        "make_ha_cell_list_length_bound_candidate_theorems",
        ("cell_list_length_le_code",),
    ),
    EnrollmentSource(
        "ha_cell_list_length_total_candidate",
        "make_ha_cell_list_length_total_candidate_theorems",
        ("cell_list_length_total",),
    ),
    EnrollmentSource(
        "ha_cell_list_lookup_domain_candidate",
        "make_ha_cell_list_lookup_domain_candidate_theorems",
        ("list_at_domain",),
    ),
    EnrollmentSource(
        "ha_cell_list_lookup_head_candidate",
        "make_ha_cell_list_lookup_head_candidate_theorems",
        ("list_at_head_iff",),
    ),
    EnrollmentSource(
        "ha_cell_list_lookup_succ_candidate",
        "make_ha_cell_list_lookup_succ_candidate_theorems",
        ("list_at_succ_iff",),
    ),
    EnrollmentSource(
        "ha_cell_list_lookup_external_bound_candidate",
        "make_ha_cell_list_lookup_external_bound_candidate_theorems",
        ("list_at_external_bound",),
    ),
    EnrollmentSource(
        "ha_cell_list_lookup_exists_candidate",
        "make_ha_cell_list_lookup_exists_candidate_theorems",
        ("list_at_exists",),
    ),
    EnrollmentSource(
        "ha_cell_list_lookup_functional_candidate",
        "make_ha_cell_list_lookup_functional_candidate_theorems",
        ("list_at_functional",),
    ),
    EnrollmentSource(
        "ha_cell_list_lookup_history_independent_candidate",
        "make_ha_cell_list_lookup_history_independent_candidate_theorems",
        ("list_at_history_independent",),
    ),
    EnrollmentSource(
        "ha_cell_list_extensional_candidate",
        "make_ha_cell_list_extensional_candidate_theorems",
        ("cell_list_extensional",),
    ),
)


HA_QR_COMPATIBLE_OVERLAP = "mod_eq_add_cancel_left"
ALPHA_QR_ROOT_NAME = QR_ROOT_NAME


def _load_source(source: EnrollmentSource) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaEnrollmentError(
            f"missing alpha factory {source.module}.{source.factory}"
        )
    produced = tuple(factory(TheoremSpec))
    by_name: dict[str, TheoremSpec] = {}
    for spec in produced:
        if type(spec) is not TheoremSpec:
            raise AlphaEnrollmentError(
                f"{source.module}.{source.factory} returned a non-TheoremSpec value"
            )
        if spec.name in by_name:
            raise AlphaEnrollmentError(
                f"duplicate factory row {spec.name!r} in {source.module}"
            )
        by_name[spec.name] = spec
    missing = tuple(name for name in source.names if name not in by_name)
    if missing:
        raise AlphaEnrollmentError(
            f"alpha source {source.module} is missing selected rows {missing!r}"
        )
    if len(set(source.names)) != len(source.names):
        raise AlphaEnrollmentError(
            f"alpha source {source.module} selects a row more than once"
        )
    return tuple(by_name[name] for name in source.names)


def _load_manifest(
    manifest: tuple[EnrollmentSource, ...],
) -> tuple[TheoremSpec, ...]:
    result: list[TheoremSpec] = []
    owners: dict[str, str] = {}
    for source in manifest:
        for spec in _load_source(source):
            previous = owners.get(spec.name)
            if previous is not None:
                raise AlphaEnrollmentError(
                    f"alpha row {spec.name!r} selected by both {previous} and "
                    f"{source.module}"
                )
            owners[spec.name] = source.module
            result.append(spec)
    return tuple(result)


@lru_cache(maxsize=1)
def alpha_enrollment() -> AlphaEnrollment:
    """Build and validate the exact, non-admitting post-stable inventory."""

    stable_by_name = MappingProxyType({spec.name: spec for spec in THEOREMS})
    if len(stable_by_name) != len(THEOREMS):
        raise AlphaEnrollmentError("stable registry contains duplicate names")
    qr_stack = build_quadratic_reciprocity_stack(
        spec_type=TheoremSpec,
        public_by_name=stable_by_name,
    )
    qr_specs = qr_stack.candidate_order
    ha_specs = _load_manifest(HA_CLOSED_ENROLLMENT_MANIFEST)
    k3b_specs = _load_manifest(K3B_CLOSED_ENROLLMENT_MANIFEST)

    if len(qr_specs) != 316:
        raise AlphaEnrollmentError(
            f"expected 316 QR ancestors, found {len(qr_specs)}"
        )
    if len(ha_specs) != 121:
        raise AlphaEnrollmentError(
            f"expected 121 closed HA candidates, found {len(ha_specs)}"
        )
    if len(k3b_specs) != 17:
        raise AlphaEnrollmentError(
            f"expected 17 closed K3B candidates, found {len(k3b_specs)}"
        )

    qr_by_name = {spec.name: spec for spec in qr_specs}
    ha_by_name = {spec.name: spec for spec in ha_specs}
    overlap = set(qr_by_name).intersection(ha_by_name)
    if overlap != {HA_QR_COMPATIBLE_OVERLAP}:
        raise AlphaEnrollmentError(
            f"unexpected QR/HA overlap: {sorted(overlap)!r}"
        )
    if qr_by_name[HA_QR_COMPATIBLE_OVERLAP] != ha_by_name[HA_QR_COMPATIBLE_OVERLAP]:
        raise AlphaEnrollmentError(
            f"incompatible QR/HA specification for {HA_QR_COMPATIBLE_OVERLAP!r}"
        )
    other_names = set(stable_by_name).union(qr_by_name).union(ha_by_name)
    k3b_overlap = other_names.intersection(spec.name for spec in k3b_specs)
    if k3b_overlap:
        raise AlphaEnrollmentError(
            f"unexpected K3B overlap: {sorted(k3b_overlap)!r}"
        )
    return AlphaEnrollment(qr_stack, qr_specs, ha_specs, k3b_specs)


__all__ = [
    "AlphaEnrollment",
    "AlphaEnrollmentError",
    "EnrollmentSource",
    "HA_CLOSED_ENROLLMENT_MANIFEST",
    "K3B_CLOSED_ENROLLMENT_MANIFEST",
    "HA_QR_COMPATIBLE_OVERLAP",
    "ALPHA_QR_ROOT_NAME",
    "alpha_enrollment",
]
