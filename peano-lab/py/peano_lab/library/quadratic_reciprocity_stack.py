"""Collect the exact native quadratic-reciprocity candidate stack.

This module is deliberately registry-neutral.  It explicitly imports the
reviewed candidate factories, validates their outputs, and resolves only the
dependency ancestors of ``quadratic_reciprocity_combined`` against a frozen
public mapping supplied by its caller.  It does not import the public theorem
registry, register a theorem, replay a tactic script, construct a certificate,
or admit anything to the public library.

The returned admission order places all required public dependencies first,
then the candidate ancestors in deterministic topological order.  The full
factory output is retained only as audit metadata so accidental duplicate or
publicly conflicting theorem names fail before dependency resolution.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from types import MappingProxyType
from typing import Any, Callable, Generic, TypeVar

from .distinct_primes_nondivisibility_candidate import (
    make_distinct_primes_nondivisibility_candidate_theorems,
)
from .eisenstein_division_threshold_candidate import (
    make_eisenstein_division_threshold_candidate_theorems,
)
from .eisenstein_fubini_row_decomposition_candidate import (
    make_eisenstein_fubini_row_decomposition_candidate_theorems,
)
from .eisenstein_fubini_total_candidate import (
    make_eisenstein_fubini_total_candidate_theorems,
)
from .eisenstein_initial_segment_count_candidate import (
    make_eisenstein_initial_segment_count_candidate_theorems,
)
from .eisenstein_lattice_orientation_candidate import (
    make_eisenstein_lattice_orientation_candidate_theorems,
)
from .eisenstein_outer_sum_bridge_candidate import (
    make_eisenstein_outer_sum_bridge_candidate_theorems,
)
from .eisenstein_quotient_bound_candidate import (
    make_eisenstein_quotient_bound_candidate_theorems,
)
from .eisenstein_quotient_sum_identity_candidate import (
    make_eisenstein_quotient_sum_identity_candidate_theorems,
)
from .eisenstein_rectangle_count_candidate import (
    make_eisenstein_rectangle_count_candidate_theorems,
)
from .eisenstein_remainder_nonzero_candidate import (
    make_eisenstein_remainder_nonzero_candidate_theorems,
)
from .eisenstein_row_indicator_candidate import (
    make_eisenstein_row_indicator_candidate_theorems,
)
from .eisenstein_row_quotient_candidate import (
    make_eisenstein_row_quotient_candidate_theorems,
)
from .eisenstein_scaled_division_candidate import (
    make_eisenstein_scaled_division_candidate_theorems,
)
from .eisenstein_transposed_cell_candidate import (
    make_eisenstein_transposed_cell_candidate_theorems,
)
from .eisenstein_transposed_column_candidate import (
    make_eisenstein_transposed_column_candidate_theorems,
)
from .eisenstein_transposed_column_count_candidate import (
    make_eisenstein_transposed_column_count_candidate_theorems,
)
from .euler_criterion_arbitrary_candidate import (
    make_euler_criterion_arbitrary_candidate_theorems,
)
from .euler_criterion_bounded_candidate import (
    make_euler_criterion_bounded_candidate_theorems,
)
from .euler_criterion_residue_candidate import (
    make_euler_criterion_residue_candidate_theorems,
)
from .euler_nonresidue_endpoint_candidate import (
    make_euler_nonresidue_endpoint_candidate_theorems,
)
from .euler_pair_product_candidate import make_euler_pair_product_candidate_theorems
from .euler_scaled_inverse_candidate import (
    make_euler_scaled_inverse_candidate_theorems,
)
from .euler_scaled_inverse_prefix_candidate import (
    make_euler_scaled_inverse_prefix_candidate_theorems,
)
from .euler_scaled_inverse_prefix_extensional_candidate import (
    make_euler_scaled_inverse_prefix_extensional_candidate_theorems,
)
from .euler_scaled_pair_order_entrance_candidate import (
    make_euler_scaled_pair_order_entrance_candidate_theorems,
)
from .euler_scaled_pair_order_iteration_candidate import (
    make_euler_scaled_pair_order_iteration_candidate_theorems,
)
from .fermat_endpoints_candidate import make_fermat_endpoint_candidate_theorems
from .fermat_product_balance_candidate import (
    make_fermat_product_balance_candidate_theorems,
)
from .fermat_residue_map_candidate import make_fermat_residue_map_candidate_theorems
from .fermat_residue_product_candidate import (
    make_fermat_residue_product_candidate_theorems,
)
from .fermat_residue_reindex_candidate import (
    make_fermat_residue_reindex_candidate_theorems,
)
from .fermat_scale_product_candidate import (
    make_fermat_scale_product_candidate_theorems,
)
from .finite_bitcount_complement_candidate import (
    make_finite_bitcount_complement_candidate_theorems,
)
from .finite_division_prefix_candidate import (
    make_finite_division_prefix_candidate_theorems,
)
from .finite_omission_candidate import make_finite_omission_candidate_theorems
from .finite_pointwise_mul_product_candidate import (
    make_finite_pointwise_mul_product_candidate_theorems,
)
from .finite_pointwise_mul_recode_candidate import (
    make_finite_pointwise_mul_recode_candidate_theorems,
)
from .finite_prime_product_coprime_candidate import (
    make_finite_prime_product_coprime_candidate_theorems,
)
from .finite_product_reindex_candidate import make_finite_product_reindex_candidate
from .finite_repeat_sum_candidate import make_finite_repeat_sum_candidate_theorems
from .finite_sum_permutation_candidate import (
    make_finite_sum_permutation_candidate_theorems,
)
from .finite_sum_pointwise_add_candidate import (
    make_finite_sum_pointwise_add_candidate_theorems,
)
from .finite_sum_pointwise_mod_candidate import (
    make_finite_sum_pointwise_mod_candidate_theorems,
)
from .finite_sum_reindex_candidate import make_finite_sum_reindex_candidate_theorems
from .finite_sum_transport_candidate import (
    make_finite_sum_transport_candidate_theorems,
)
from .gauss_count_sum_parity_candidate import (
    make_gauss_count_sum_parity_candidate_theorems,
)
from .gauss_eisenstein_data_candidate import (
    make_gauss_eisenstein_data_candidate_theorems,
)
from .gauss_eisenstein_pointwise_candidate import (
    make_gauss_eisenstein_pointwise_candidate_theorems,
)
from .gauss_eisenstein_sum_candidate import (
    make_gauss_eisenstein_sum_candidate_theorems,
)
from .gauss_lemma_arbitrary_candidate import (
    make_gauss_lemma_arbitrary_candidate_theorems,
)
from .gauss_lemma_endpoint_candidate import (
    make_gauss_lemma_endpoint_candidate_theorems,
)
from .gauss_magnitude_coprime_candidate import (
    make_gauss_magnitude_coprime_candidate_theorems,
)
from .gauss_magnitude_permutation_candidate import (
    make_gauss_magnitude_permutation_candidate_theorems,
)
from .gauss_magnitude_product_candidate import (
    make_gauss_magnitude_product_candidate_theorems,
)
from .gauss_product_composition_candidate import (
    make_gauss_product_composition_candidate_theorems,
)
from .gauss_sign_factor_recode_candidate import (
    make_gauss_sign_factor_recode_candidate_theorems,
)
from .gauss_sign_product_candidate import make_gauss_sign_product_candidate_theorems
from .gauss_signed_division_alignment_candidate import (
    make_gauss_signed_division_alignment_candidate_theorems,
)
from .gauss_signed_half_candidate import make_gauss_signed_half_candidate_theorems
from .gauss_signed_pointwise_product_candidate import (
    make_gauss_signed_pointwise_product_candidate_theorems,
)
from .gauss_signed_prefix_candidate import make_gauss_signed_prefix_candidate_theorems
from .parity_mod_two_candidate import make_parity_mod_two_candidate_theorems
from .parity_odd_division_candidate import make_parity_odd_division_candidate_theorems
from .parity_odd_half_mod_four_candidate import (
    make_parity_odd_half_mod_four_candidate_theorems,
)
from .parity_sum_classification_candidate import (
    make_parity_sum_classification_candidate_theorems,
)
from .quadratic_reciprocity_candidate import (
    make_quadratic_reciprocity_candidate_theorems,
)
from .quadratic_reciprocity_conditional_candidate import (
    make_quadratic_reciprocity_conditional_candidate_theorems,
)
from .quadratic_reciprocity_parity_candidate import (
    make_quadratic_reciprocity_parity_candidate_theorems,
)
from .quadratic_residue_surface import QUADRATIC_RECIPROCITY_COMBINED
from .signed_division_parity_bridge_candidate import (
    make_signed_division_parity_bridge_candidate_theorems,
)
from .wilson_endpoint_restoration_candidate import (
    make_wilson_endpoint_restoration_candidate_theorems,
)
from .wilson_inverse_endpoints_candidate import (
    make_wilson_inverse_endpoints_candidate_theorems,
)
from .wilson_inverse_involution_candidate import (
    make_wilson_inverse_involution_candidate_theorems,
)
from .wilson_inverse_orbit_candidate import (
    make_wilson_inverse_orbit_candidate_theorems,
)
from .wilson_inverse_point_candidate import (
    make_wilson_inverse_point_candidate_theorems,
)
from .wilson_inverse_prefix_candidate import (
    make_wilson_inverse_prefix_candidate_theorems,
)
from .wilson_pair_order_candidate import make_wilson_pair_order_candidate_theorems
from .wilson_pair_order_induction_candidate import (
    make_wilson_pair_order_induction_candidate_theorems,
)
from .wilson_pair_order_iteration_candidate import (
    make_wilson_pair_order_iteration_candidate_theorems,
)
from .wilson_pair_order_paired_iteration_candidate import (
    make_wilson_pair_order_paired_iteration_candidate_theorems,
)
from .wilson_pair_product_candidate import make_wilson_pair_product_candidate_theorems
from .wilson_square_one_candidate import make_wilson_square_one_candidate_theorems
from .wilson_successor_lift_candidate import (
    make_wilson_successor_lift_candidate_theorems,
)
from .wilson_terminal_product_candidate import (
    make_wilson_terminal_product_candidate_theorems,
)


QR_ROOT_NAME = "quadratic_reciprocity_combined"
QR_FINAL_DIRECT_DEPENDENCIES = (
    "distinct_odd_primes_gauss_eisenstein_data_exists",
    "conditional_qres_same_status_from_oriented_gauss_counts",
    "conditional_qres_opposite_status_from_oriented_gauss_counts",
)
_SOURCE_ROOT = Path(__file__).resolve().parent

FactoryBuilder = Callable[[Callable[..., Any]], tuple[Any, ...]]
SpecT = TypeVar("SpecT")


@dataclass(frozen=True)
class CandidateFactory:
    """One reviewed candidate source and its explicitly imported factory."""

    module_name: str
    builder: FactoryBuilder

    @property
    def factory_name(self) -> str:
        return self.builder.__name__


@dataclass(frozen=True)
class QuadraticReciprocityStack(Generic[SpecT]):
    """Immutable metadata and deterministic ancestor order for native QR.

    ``all_candidate_by_name`` audits every factory output; the shorter
    ``candidate_by_name`` contains only ancestors of ``QR_ROOT_NAME`` and is
    the map intended for a future admission compiler.
    """

    all_candidates: tuple[SpecT, ...]
    all_candidate_by_name: Mapping[str, SpecT]
    candidate_by_name: Mapping[str, SpecT]
    owner_by_name: Mapping[str, str]
    candidate_order: tuple[SpecT, ...]
    public_order: tuple[SpecT, ...]
    combined_order: tuple[tuple[str, SpecT], ...]
    admission_order: tuple[SpecT, ...]
    dependency_depth_by_name: Mapping[str, int]
    dependency_layers: tuple[tuple[SpecT, ...], ...]
    source_rows: tuple[tuple[str, str, str], ...]
    graph_sha256: str
    source_sha256: str


# Alphabetical source order is intentional and part of the source receipt.
QR_CANDIDATE_FACTORY_MANIFEST: tuple[CandidateFactory, ...] = (
    CandidateFactory(
        "distinct_primes_nondivisibility_candidate",
        make_distinct_primes_nondivisibility_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_division_threshold_candidate",
        make_eisenstein_division_threshold_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_fubini_row_decomposition_candidate",
        make_eisenstein_fubini_row_decomposition_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_fubini_total_candidate",
        make_eisenstein_fubini_total_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_initial_segment_count_candidate",
        make_eisenstein_initial_segment_count_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_lattice_orientation_candidate",
        make_eisenstein_lattice_orientation_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_outer_sum_bridge_candidate",
        make_eisenstein_outer_sum_bridge_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_quotient_bound_candidate",
        make_eisenstein_quotient_bound_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_quotient_sum_identity_candidate",
        make_eisenstein_quotient_sum_identity_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_rectangle_count_candidate",
        make_eisenstein_rectangle_count_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_remainder_nonzero_candidate",
        make_eisenstein_remainder_nonzero_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_row_indicator_candidate",
        make_eisenstein_row_indicator_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_row_quotient_candidate",
        make_eisenstein_row_quotient_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_scaled_division_candidate",
        make_eisenstein_scaled_division_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_transposed_cell_candidate",
        make_eisenstein_transposed_cell_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_transposed_column_candidate",
        make_eisenstein_transposed_column_candidate_theorems,
    ),
    CandidateFactory(
        "eisenstein_transposed_column_count_candidate",
        make_eisenstein_transposed_column_count_candidate_theorems,
    ),
    CandidateFactory(
        "euler_criterion_arbitrary_candidate",
        make_euler_criterion_arbitrary_candidate_theorems,
    ),
    CandidateFactory(
        "euler_criterion_bounded_candidate",
        make_euler_criterion_bounded_candidate_theorems,
    ),
    CandidateFactory(
        "euler_criterion_residue_candidate",
        make_euler_criterion_residue_candidate_theorems,
    ),
    CandidateFactory(
        "euler_nonresidue_endpoint_candidate",
        make_euler_nonresidue_endpoint_candidate_theorems,
    ),
    CandidateFactory(
        "euler_pair_product_candidate",
        make_euler_pair_product_candidate_theorems,
    ),
    CandidateFactory(
        "euler_scaled_inverse_candidate",
        make_euler_scaled_inverse_candidate_theorems,
    ),
    CandidateFactory(
        "euler_scaled_inverse_prefix_candidate",
        make_euler_scaled_inverse_prefix_candidate_theorems,
    ),
    CandidateFactory(
        "euler_scaled_inverse_prefix_extensional_candidate",
        make_euler_scaled_inverse_prefix_extensional_candidate_theorems,
    ),
    CandidateFactory(
        "euler_scaled_pair_order_entrance_candidate",
        make_euler_scaled_pair_order_entrance_candidate_theorems,
    ),
    CandidateFactory(
        "euler_scaled_pair_order_iteration_candidate",
        make_euler_scaled_pair_order_iteration_candidate_theorems,
    ),
    CandidateFactory(
        "fermat_endpoints_candidate",
        make_fermat_endpoint_candidate_theorems,
    ),
    CandidateFactory(
        "fermat_product_balance_candidate",
        make_fermat_product_balance_candidate_theorems,
    ),
    CandidateFactory(
        "fermat_residue_map_candidate",
        make_fermat_residue_map_candidate_theorems,
    ),
    CandidateFactory(
        "fermat_residue_product_candidate",
        make_fermat_residue_product_candidate_theorems,
    ),
    CandidateFactory(
        "fermat_residue_reindex_candidate",
        make_fermat_residue_reindex_candidate_theorems,
    ),
    CandidateFactory(
        "fermat_scale_product_candidate",
        make_fermat_scale_product_candidate_theorems,
    ),
    CandidateFactory(
        "finite_bitcount_complement_candidate",
        make_finite_bitcount_complement_candidate_theorems,
    ),
    CandidateFactory(
        "finite_division_prefix_candidate",
        make_finite_division_prefix_candidate_theorems,
    ),
    CandidateFactory(
        "finite_omission_candidate",
        make_finite_omission_candidate_theorems,
    ),
    CandidateFactory(
        "finite_pointwise_mul_product_candidate",
        make_finite_pointwise_mul_product_candidate_theorems,
    ),
    CandidateFactory(
        "finite_pointwise_mul_recode_candidate",
        make_finite_pointwise_mul_recode_candidate_theorems,
    ),
    CandidateFactory(
        "finite_prime_product_coprime_candidate",
        make_finite_prime_product_coprime_candidate_theorems,
    ),
    CandidateFactory(
        "finite_product_reindex_candidate",
        make_finite_product_reindex_candidate,
    ),
    CandidateFactory(
        "finite_repeat_sum_candidate",
        make_finite_repeat_sum_candidate_theorems,
    ),
    CandidateFactory(
        "finite_sum_permutation_candidate",
        make_finite_sum_permutation_candidate_theorems,
    ),
    CandidateFactory(
        "finite_sum_pointwise_add_candidate",
        make_finite_sum_pointwise_add_candidate_theorems,
    ),
    CandidateFactory(
        "finite_sum_pointwise_mod_candidate",
        make_finite_sum_pointwise_mod_candidate_theorems,
    ),
    CandidateFactory(
        "finite_sum_reindex_candidate",
        make_finite_sum_reindex_candidate_theorems,
    ),
    CandidateFactory(
        "finite_sum_transport_candidate",
        make_finite_sum_transport_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_count_sum_parity_candidate",
        make_gauss_count_sum_parity_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_eisenstein_data_candidate",
        make_gauss_eisenstein_data_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_eisenstein_pointwise_candidate",
        make_gauss_eisenstein_pointwise_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_eisenstein_sum_candidate",
        make_gauss_eisenstein_sum_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_lemma_arbitrary_candidate",
        make_gauss_lemma_arbitrary_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_lemma_endpoint_candidate",
        make_gauss_lemma_endpoint_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_magnitude_coprime_candidate",
        make_gauss_magnitude_coprime_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_magnitude_permutation_candidate",
        make_gauss_magnitude_permutation_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_magnitude_product_candidate",
        make_gauss_magnitude_product_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_product_composition_candidate",
        make_gauss_product_composition_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_sign_factor_recode_candidate",
        make_gauss_sign_factor_recode_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_sign_product_candidate",
        make_gauss_sign_product_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_signed_division_alignment_candidate",
        make_gauss_signed_division_alignment_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_signed_half_candidate",
        make_gauss_signed_half_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_signed_pointwise_product_candidate",
        make_gauss_signed_pointwise_product_candidate_theorems,
    ),
    CandidateFactory(
        "gauss_signed_prefix_candidate",
        make_gauss_signed_prefix_candidate_theorems,
    ),
    CandidateFactory(
        "parity_mod_two_candidate",
        make_parity_mod_two_candidate_theorems,
    ),
    CandidateFactory(
        "parity_odd_division_candidate",
        make_parity_odd_division_candidate_theorems,
    ),
    CandidateFactory(
        "parity_odd_half_mod_four_candidate",
        make_parity_odd_half_mod_four_candidate_theorems,
    ),
    CandidateFactory(
        "parity_sum_classification_candidate",
        make_parity_sum_classification_candidate_theorems,
    ),
    CandidateFactory(
        "quadratic_reciprocity_candidate",
        make_quadratic_reciprocity_candidate_theorems,
    ),
    CandidateFactory(
        "quadratic_reciprocity_conditional_candidate",
        make_quadratic_reciprocity_conditional_candidate_theorems,
    ),
    CandidateFactory(
        "quadratic_reciprocity_parity_candidate",
        make_quadratic_reciprocity_parity_candidate_theorems,
    ),
    CandidateFactory(
        "signed_division_parity_bridge_candidate",
        make_signed_division_parity_bridge_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_endpoint_restoration_candidate",
        make_wilson_endpoint_restoration_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_inverse_endpoints_candidate",
        make_wilson_inverse_endpoints_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_inverse_involution_candidate",
        make_wilson_inverse_involution_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_inverse_orbit_candidate",
        make_wilson_inverse_orbit_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_inverse_point_candidate",
        make_wilson_inverse_point_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_inverse_prefix_candidate",
        make_wilson_inverse_prefix_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_pair_order_candidate",
        make_wilson_pair_order_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_pair_order_induction_candidate",
        make_wilson_pair_order_induction_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_pair_order_iteration_candidate",
        make_wilson_pair_order_iteration_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_pair_order_paired_iteration_candidate",
        make_wilson_pair_order_paired_iteration_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_pair_product_candidate",
        make_wilson_pair_product_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_square_one_candidate",
        make_wilson_square_one_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_successor_lift_candidate",
        make_wilson_successor_lift_candidate_theorems,
    ),
    CandidateFactory(
        "wilson_terminal_product_candidate",
        make_wilson_terminal_product_candidate_theorems,
    ),
)


def _spec_payload(scope: str, spec: Any) -> str:
    return "\x1f".join(
        (
            scope,
            spec.name,
            spec.statement,
            "\x1e".join(spec.script),
            "\x1e".join(spec.dependencies),
        )
    )


def _collect_factory_outputs(
    factory_manifest: tuple[CandidateFactory, ...],
    spec_type: type[SpecT],
) -> tuple[
    tuple[SpecT, ...], dict[str, str], tuple[tuple[str, str, str], ...]
]:
    all_candidates: list[SpecT] = []
    owner_by_name: dict[str, str] = {}
    source_rows: list[tuple[str, str, str]] = []
    seen_factories: set[tuple[str, str]] = set()

    for entry in factory_manifest:
        factory_key = (entry.module_name, entry.factory_name)
        if factory_key in seen_factories:
            raise ValueError(f"duplicate QR candidate factory: {factory_key!r}")
        seen_factories.add(factory_key)
        expected_module = f"peano_lab.library.{entry.module_name}"
        if entry.builder.__module__ != expected_module:
            raise ValueError(
                f"QR factory {entry.factory_name} belongs to "
                f"{entry.builder.__module__}, expected {expected_module}"
            )
        source = Path(entry.builder.__code__.co_filename).resolve()
        expected_source = (_SOURCE_ROOT / f"{entry.module_name}.py").resolve()
        if source != expected_source:
            raise ValueError(
                f"QR factory {entry.factory_name} source is {source}, "
                f"expected {expected_source}"
            )
        source_rows.append(
            (
                entry.module_name,
                entry.factory_name,
                sha256(source.read_bytes()).hexdigest(),
            )
        )
        for candidate in tuple(entry.builder(spec_type)):
            if type(candidate) is not spec_type:
                raise TypeError(
                    f"QR factory {entry.factory_name} returned "
                    f"{type(candidate).__name__}, expected {spec_type.__name__}"
                )
            if candidate.name in owner_by_name:
                raise ValueError(
                    f"duplicate QR candidate theorem {candidate.name!r} from "
                    f"{owner_by_name[candidate.name]} and {entry.module_name}"
                )
            owner_by_name[candidate.name] = entry.module_name
            all_candidates.append(candidate)

    return tuple(all_candidates), owner_by_name, tuple(source_rows)


def _freeze_public_mapping(
    spec_type: type[SpecT], public_by_name: Mapping[str, SpecT]
) -> Mapping[str, SpecT]:
    """Validate and snapshot the caller's explicit pre-QR public registry."""

    if not isinstance(public_by_name, Mapping):
        raise TypeError("public_by_name must be an explicit theorem mapping")
    frozen: dict[str, SpecT] = {}
    for name, spec in public_by_name.items():
        if type(name) is not str or not name:
            raise TypeError("public theorem mapping keys must be non-empty strings")
        if type(spec) is not spec_type:
            raise TypeError(
                f"public theorem {name!r} has type {type(spec).__name__}, "
                f"expected {spec_type.__name__}"
            )
        if getattr(spec, "name", None) != name:
            raise ValueError(
                f"public theorem mapping key {name!r} does not match "
                f"specification name {getattr(spec, 'name', None)!r}"
            )
        frozen[name] = spec
    return MappingProxyType(frozen)


def _assemble_quadratic_reciprocity_stack(
    *,
    all_candidates: tuple[SpecT, ...],
    owner_by_name: Mapping[str, str],
    source_rows: tuple[tuple[str, str, str], ...],
    public_by_name: Mapping[str, SpecT],
    root_name: str,
) -> QuadraticReciprocityStack[SpecT]:
    candidate_by_name: dict[str, SpecT] = {}
    for candidate in all_candidates:
        if candidate.name in candidate_by_name:
            raise ValueError(f"duplicate QR candidate theorem {candidate.name!r}")
        candidate_by_name[candidate.name] = candidate
    missing_owners = sorted(set(candidate_by_name).difference(owner_by_name))
    extra_owners = sorted(set(owner_by_name).difference(candidate_by_name))
    if missing_owners or extra_owners:
        raise ValueError(
            "QR candidate ownership mismatch: "
            f"missing={missing_owners!r}, extra={extra_owners!r}"
        )
    conflicts = sorted(set(candidate_by_name).intersection(public_by_name))
    if conflicts:
        raise ValueError(
            f"QR candidate names conflict with public theorems: {conflicts!r}"
        )
    if root_name not in candidate_by_name:
        raise ValueError(f"missing QR root candidate {root_name!r}")

    visiting: set[tuple[str, str]] = set()
    visited: set[tuple[str, str]] = set()
    combined_order: list[tuple[str, SpecT]] = []

    def visit(name: str, parent_scope: str | None = None) -> None:
        if name in candidate_by_name:
            scope = "candidate"
            spec = candidate_by_name[name]
        elif name in public_by_name:
            scope = "public"
            spec = public_by_name[name]
        else:
            raise ValueError(f"unknown QR dependency {name!r}")
        if parent_scope == "public" and scope == "candidate":
            raise ValueError(
                f"public QR dependency graph points to candidate {name!r}"
            )
        key = (scope, name)
        if key in visited:
            return
        if key in visiting:
            raise ValueError(f"cycle in QR dependency graph at {name!r}")
        visiting.add(key)
        for dependency in spec.dependencies:
            visit(dependency, scope)
        visiting.remove(key)
        visited.add(key)
        combined_order.append((scope, spec))

    visit(root_name)
    candidate_order = tuple(
        spec for scope, spec in combined_order if scope == "candidate"
    )
    candidate_ancestor_by_name = {
        spec.name: spec for spec in candidate_order
    }
    public_order = tuple(
        spec for scope, spec in combined_order if scope == "public"
    )
    admission_order = public_order + candidate_order
    positions = {spec.name: index for index, spec in enumerate(admission_order)}
    for spec in admission_order:
        for dependency in spec.dependencies:
            if dependency not in positions or positions[dependency] >= positions[spec.name]:
                raise ValueError(
                    f"non-topological QR admission order at {spec.name!r} "
                    f"dependency {dependency!r}"
                )

    dependency_depth_by_name: dict[str, int] = {}
    for spec in admission_order:
        dependency_depth_by_name[spec.name] = (
            0
            if not spec.dependencies
            else 1
            + max(
                dependency_depth_by_name[dependency]
                for dependency in spec.dependencies
            )
        )
    layer_count = max(dependency_depth_by_name.values(), default=-1) + 1
    layer_lists: list[list[SpecT]] = [[] for _ in range(layer_count)]
    for spec in admission_order:
        layer_lists[dependency_depth_by_name[spec.name]].append(spec)
    dependency_layers = tuple(tuple(layer) for layer in layer_lists)

    graph_sha256 = sha256(
        "\x1c".join(
            _spec_payload(scope, spec) for scope, spec in combined_order
        ).encode()
    ).hexdigest()
    source_sha256 = sha256(
        "\x1c".join("\x1f".join(row) for row in source_rows).encode()
    ).hexdigest()
    return QuadraticReciprocityStack(
        all_candidates=all_candidates,
        all_candidate_by_name=MappingProxyType(candidate_by_name),
        candidate_by_name=MappingProxyType(candidate_ancestor_by_name),
        owner_by_name=MappingProxyType(dict(owner_by_name)),
        candidate_order=candidate_order,
        public_order=public_order,
        combined_order=tuple(combined_order),
        admission_order=admission_order,
        dependency_depth_by_name=MappingProxyType(dependency_depth_by_name),
        dependency_layers=dependency_layers,
        source_rows=source_rows,
        graph_sha256=graph_sha256,
        source_sha256=source_sha256,
    )


def build_quadratic_reciprocity_stack(
    *,
    spec_type: type[SpecT],
    public_by_name: Mapping[str, SpecT],
) -> QuadraticReciprocityStack[SpecT]:
    """Build a fresh QR stack against one explicit frozen public snapshot.

    The caller supplies the exact specification class used by every factory
    and the pre-QR public registry.  This module snapshots that mapping before
    factory evaluation, so later caller mutation cannot change the build.
    """

    if not isinstance(spec_type, type):
        raise TypeError("spec_type must be an exact theorem specification type")
    frozen_public = _freeze_public_mapping(spec_type, public_by_name)

    candidates, owners, source_rows = _collect_factory_outputs(
        QR_CANDIDATE_FACTORY_MANIFEST,
        spec_type,
    )
    stack = _assemble_quadratic_reciprocity_stack(
        all_candidates=candidates,
        owner_by_name=owners,
        source_rows=source_rows,
        public_by_name=frozen_public,
        root_name=QR_ROOT_NAME,
    )
    root = stack.candidate_by_name[QR_ROOT_NAME]
    if root.statement != QUADRATIC_RECIPROCITY_COMBINED:
        raise ValueError("quadratic-reciprocity root surface changed")
    if root.dependencies != QR_FINAL_DIRECT_DEPENDENCIES:
        raise ValueError("quadratic-reciprocity root dependency spine changed")
    return stack


__all__ = [
    "CandidateFactory",
    "QuadraticReciprocityStack",
    "QR_CANDIDATE_FACTORY_MANIFEST",
    "QR_FINAL_DIRECT_DEPENDENCIES",
    "QR_ROOT_NAME",
    "build_quadratic_reciprocity_stack",
]
