"""Exact browser-safe v32 providers for 175 completed research theorems.

The two self-contained artifacts retain their original research bytes.
Metadata and enrollment are not proof authority: checked use authenticates
and checks every exact body with the unchanged HA kernel. The runtime never
imports authoring registries or reads a repository catalogue; independent
same-byte compiled-Lean verification belongs to the fresh release driver.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping

from ..kernel.formulas import Formula
from .campaign_lower_layer_closure import _packaging_root, _specs_digest
from .proof_bundle import (
    DEFAULT_BUNDLE_LIMITS, BundleNode, CheckedProofBundle, ProofBundle,
    check_proof_bundle,
)
from .theorems import TheoremSpec, _closed_formula


class ResearchClosureError(ValueError):
    """A frozen source, exact dependency, target, proof, or resource gate failed."""


@dataclass(frozen=True, slots=True)
class ResearchFactory:
    campaign: str
    module: str
    factory: str
    rfc: str
    source_bytes: int
    source_sha256: str
    count: int
    specs_sha256: str
    test_filename: str

    @property
    def source(self) -> str:
        return f"peano-lab/py/peano_lab/library/{self.module}.py"

    @property
    def test(self) -> str:
        return "peano-lab/py/tests/" + self.test_filename


@dataclass(frozen=True, slots=True)
class ResearchFamily:
    slug: str
    research_checkpoint_slug: str
    artifact: str
    artifact_bytes: int
    artifact_sha256: str
    count: int
    specs_sha256: str
    names_sha256: str
    edge_count: int
    command_count: int
    rfc: str
    owned_names: tuple[str, ...]
    principal_roots: tuple[str, ...]
    theorem_count: int
    root_names: tuple[str, ...]
    node_count: int
    dependency_edges: int
    bundle_edges: int
    body_nodes: int
    ordered_cone_names_sha256: str
    complete_non_alpha_specs_sha256: str
    modules: tuple[str, ...]
    principal_pins: tuple[tuple[str, str], ...]

    @property
    def artifact_filename(self) -> str:
        return self.artifact.rsplit("/", 1)[-1]

    @property
    def principal_statement_sha256(self) -> Mapping[str, str]:
        return MappingProxyType(dict(self.principal_pins))


@dataclass(frozen=True, slots=True)
class ResearchRow:
    node_id: int
    inventory_index: int
    name: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    campaign: str | None
    is_owned: bool


@dataclass(frozen=True, slots=True)
class ResearchPlan:
    family: ResearchFamily
    rows: tuple[ResearchRow, ...]
    specs: tuple[TheoremSpec, ...]
    root_names: tuple[str, ...]
    frontier_names: tuple[str, ...]
    owned_names: tuple[str, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    frontier_specs_sha256: str

    @property
    def positions(self) -> Mapping[str, int]:
        return MappingProxyType({row.name: row.node_id for row in self.rows})


PARENT_ALPHA_V31_COUNT = 3796
PARENT_ALPHA_V31_SPECS_SHA256 = "ea10e9dc87e73bf7abd954b8542a6ed9f5b134b0c44382fff9b978f3cbd3483a"
PARENT_ALPHA_V31_IDENTITY_SHA256 = "902fa75c2bf4624bb7fc5aca9a6c49b71ff8fa4499f8bdf9ce726cfd4166a5d7"
PARENT_ALPHA_V31_ENROLLMENT_SHA256 = "e4f6330197152cab52427ea724c488390e1cd3bd50a77c09746161cb0d343768"
EXPECTED_RESEARCH_COUNT = 175
EXPECTED_RESEARCH_EDGE_COUNT = 503
EXPECTED_RESEARCH_COMMAND_COUNT = 9029
EXPECTED_RESEARCH_NAMES_SHA256 = "2411dd4b45e58c5905ac24b5c091462594579c42923de238ba05ffaf2f120a64"
EXPECTED_RESEARCH_SPECS_SHA256 = "5c19425ae209472383459546cbd5765c66511249fdcf0290b8860bd392ef3700"
EXPECTED_RESEARCH_FAMILY_COUNT = 2
EXPECTED_RESEARCH_FACTORY_COUNT = 13
EXPECTED_RESEARCH_METADATA_SHA256 = "796dec78ee5c337f9bc89d53d162cedca5e53883f4754f8d17eb73784d490d7c"
# The existing source-input and proof-bundle ceilings, not enlarged limits.
MAX_SOURCE_BYTES = 2 * 1024 * 1024

FACTORIES = (
    ResearchFactory(
        campaign="multiplicative-convolution",
        module="arithmetic_multiplicative_candidate",
        factory="make_arithmetic_multiplicative_candidate_theorems",
        rfc="g009-multiplicative-convolution-rfc-v1.md",
        source_bytes=10836,
        source_sha256="f4374450ec543f69093b98367c90f67f09ac15daacd1df2f90961d7b6ece4a7e",
        count=11,
        specs_sha256="b628d998a8b38c1180a3bd2b75de2f4a3539a67631ec179188df3b59ae5237a1",
        test_filename="test_arithmetic_multiplicative_candidate.py",
    ),
    ResearchFactory(
        campaign="multiplicative-convolution",
        module="coprime_divisor_decomposition_candidate",
        factory="make_coprime_divisor_decomposition_candidate_theorems",
        rfc="g009-multiplicative-convolution-rfc-v1.md",
        source_bytes=14805,
        source_sha256="de19bb61543f5d7ab3a1d1b675c96ae4b31c7c96b58d6107904e7188973a2e1c",
        count=8,
        specs_sha256="7aaeab34112a70ccca9ac8a9b1fb6c019fb0cc4e481b75924330d0dde8f10dba",
        test_filename="test_coprime_divisor_decomposition_candidate.py",
    ),
    ResearchFactory(
        campaign="multiplicative-convolution",
        module="divisor_pair_index_candidate",
        factory="make_divisor_pair_index_candidate_theorems",
        rfc="g009-multiplicative-convolution-rfc-v1.md",
        source_bytes=6642,
        source_sha256="fc6a5a555fdee62cf5f54365163f32c4acfee10b8f416b811bb69debdbcf62a0",
        count=4,
        specs_sha256="a25d7e77eb5fd54ca6dbecf58c89b68df64f541d98480f9bd21cd9f3865e443c",
        test_filename="test_divisor_pair_index_candidate.py",
    ),
    ResearchFactory(
        campaign="multiplicative-convolution",
        module="signed_block_sum_candidate",
        factory="make_signed_block_sum_candidate_theorems",
        rfc="g009-multiplicative-convolution-rfc-v1.md",
        source_bytes=14390,
        source_sha256="0597b3806fec32b8eb117f5d0f6be2304c754aa8078df6f50de9dd4d12a2c18f",
        count=7,
        specs_sha256="701fdc856da623959071adab01798da9be773933380b573581bf32252d1e639b",
        test_filename="test_signed_block_sum_candidate.py",
    ),
    ResearchFactory(
        campaign="multiplicative-convolution",
        module="signed_cartesian_product_candidate",
        factory="make_signed_cartesian_product_candidate_theorems",
        rfc="g009-multiplicative-convolution-rfc-v1.md",
        source_bytes=33563,
        source_sha256="d7dbe1d9a82ee5b91e33d6a4624d3e7f05b20d4618045ecab8e753eee6c7e351",
        count=20,
        specs_sha256="c78fafc6d55e2f0047a91a9e1ee9c237f1f649ec2293a4b27e77493ca90c778b",
        test_filename="test_signed_cartesian_product_candidate.py",
    ),
    ResearchFactory(
        campaign="multiplicative-convolution",
        module="signed_support_reindex_candidate",
        factory="make_signed_support_reindex_candidate_theorems",
        rfc="g009-multiplicative-convolution-rfc-v1.md",
        source_bytes=44258,
        source_sha256="db91e38ca5e671adf88e3bf70396b1a242f9c760d6f2c52c4785e6a63316339e",
        count=25,
        specs_sha256="59dab408679322a454f9ad7fda1306eed691b843ec6f1f1f3899073573a84737",
        test_filename="test_signed_support_reindex_candidate.py",
    ),
    ResearchFactory(
        campaign="multiplicative-convolution",
        module="dirichlet_multiplicative_entry_candidate",
        factory="make_dirichlet_multiplicative_entry_candidate_theorems",
        rfc="g009-multiplicative-convolution-rfc-v1.md",
        source_bytes=10482,
        source_sha256="d7f55b8f25e56f8b9c5bc3f6c4b83698d5f1ad770e1e4ed77c53f12a602bd897",
        count=5,
        specs_sha256="e91550a16b48e436cd2dfae96419966d64f1d0d40858569a1032506190d28385",
        test_filename="test_dirichlet_multiplicative_entry_candidate.py",
    ),
    ResearchFactory(
        campaign="multiplicative-convolution",
        module="dirichlet_multiplicative_support_candidate",
        factory="make_dirichlet_multiplicative_support_candidate_theorems",
        rfc="g009-multiplicative-convolution-rfc-v1.md",
        source_bytes=19151,
        source_sha256="56e9f8ccaa7c795e42b33984bc2346182ba3a1f820883ba884e571b89091d4a5",
        count=6,
        specs_sha256="3f4ce4b3c453447efee726a648f08ec437df25b71e8a12e4d801b06d5f0c0a91",
        test_filename="test_dirichlet_multiplicative_closure_candidate.py",
    ),
    ResearchFactory(
        campaign="multiplicative-convolution",
        module="dirichlet_multiplicative_candidate",
        factory="make_dirichlet_multiplicative_candidate_theorems",
        rfc="g009-multiplicative-convolution-rfc-v1.md",
        source_bytes=9345,
        source_sha256="bb1342735115781fd8f0107d3876c95098e0b6dc459f31981ffb2c16432eab77",
        count=4,
        specs_sha256="b4d780bb8b2056055def685cd8842dca1b0889ccec3ed98b676b1f94661c0957",
        test_filename="test_dirichlet_multiplicative_closure_candidate.py",
    ),
    ResearchFactory(
        campaign="polynomial-division-prerequisites",
        module="prime_field_polynomial_subtraction_candidate",
        factory="make_prime_field_polynomial_subtraction_candidate_theorems",
        rfc="prime-field-polynomial-division-prerequisites-rfc-v1.md",
        source_bytes=27165,
        source_sha256="d08562b26c683a891e58a4b10faa495867d7487054b1ee7c99f091dd1c707b2b",
        count=26,
        specs_sha256="fddc42488bddd4a722845460af4ba70e820259e07873cfc18d7ef3913c2efc98",
        test_filename="test_prime_field_polynomial_subtraction_candidate.py",
    ),
    ResearchFactory(
        campaign="polynomial-division-prerequisites",
        module="prime_field_polynomial_trim_candidate",
        factory="make_prime_field_polynomial_trim_candidate_theorems",
        rfc="prime-field-polynomial-division-prerequisites-rfc-v1.md",
        source_bytes=26425,
        source_sha256="1125c02fd11646efaa20963380ba1086e18551f2c89b242b8900a8043d358e4c",
        count=22,
        specs_sha256="2df5426db1c38cc2ea8919e6fd8334e4b75d358bebb01d67a8e094df2f8130b6",
        test_filename="test_prime_field_polynomial_trim_candidate.py",
    ),
    ResearchFactory(
        campaign="polynomial-division-prerequisites",
        module="prime_field_polynomial_monic_candidate",
        factory="make_prime_field_polynomial_monic_candidate_theorems",
        rfc="prime-field-polynomial-division-prerequisites-rfc-v1.md",
        source_bytes=25658,
        source_sha256="3bf93aff71b48a332920b1a6174e44167bf78238caac3b6d35634f3591582eef",
        count=20,
        specs_sha256="ccba95d5eaa7b9358ae00236dcfbbd44b80d4fef41389faf36433e6c9c771d23",
        test_filename="test_prime_field_polynomial_monic_candidate.py",
    ),
    ResearchFactory(
        campaign="polynomial-division-prerequisites",
        module="prime_field_polynomial_synthetic_candidate",
        factory="make_prime_field_polynomial_synthetic_candidate_theorems",
        rfc="prime-field-polynomial-division-prerequisites-rfc-v1.md",
        source_bytes=25265,
        source_sha256="0938e369e528666e8e52c5d49b157a12bd00bf50150783182b3b5ebc36b02022",
        count=17,
        specs_sha256="81e0b75fa4db42fe70afd2aed60894a721af323d5bb691829c6b9496aa994dd4",
        test_filename="test_prime_field_polynomial_synthetic_candidate.py",
    ),
)

RESEARCH_FAMILIES = (
    ResearchFamily(
        slug="multiplicative-convolution",
        research_checkpoint_slug="g009-multiplicative-convolution",
        artifact="research/arithmetic-library/artifacts/g009-multiplicative-convolution-proof-bundle-v1.json",
        artifact_bytes=7840579,
        artifact_sha256="953dc5ef340379b1e34883c2f9ab2181e91c872f5bbb7943c52b2fb70ce76959",
        count=90,
        specs_sha256="25086b5c317b7dddd47cc06b0d9ad5639b6a5d88b6ede323cf7aa1124fa9dba7",
        names_sha256="2013935a09dcd2d7fefdae65ad31f63815e73e5e45da37cd71a880fdb2f5031f",
        edge_count=313,
        command_count=5388,
        rfc="research/arithmetic-library/g009-multiplicative-convolution-rfc-v1.md",
        owned_names=("signed_multiplicative_nonempty", "signed_multiplicative_table", "signed_multiplicative_normalized", "signed_multiplicative_coprime_product", "signed_multiplicative_intro", "signed_multiplicative_zero_excluded", "signed_multiplicative_at_one_value", "signed_multiplicative_restrict", "signed_multiplicative_product_values_exist", "signed_positive_table_entry_transport", "signed_multiplicative_positive_extensional", "coprime_divisor_gcd_product", "coprime_divisor_factor_pair_coordinates", "coprime_divisor_factor_pair_unique", "coprime_divisor_factor_pair_exists", "coprime_divisor_factor_pair_bounds", "coprime_divisor_factor_pair_exists_unique", "coprime_divisor_factor_pair_cofactors", "divisor_factor_pair_quotient_product", "divisor_pair_index_map_append", "divisor_pair_index_map_exists", "divisor_pair_index_map_lookup", "divisor_pair_index_map_value", "signed_slice_identity", "signed_slice_sum_unit_prefix_iff", "signed_slice_sum_concatenate", "signed_slice_sum_concatenate_values", "signed_row_sums_flatten", "signed_prefix_sum_row_major_iff", "signed_prefix_sum_row_major_exists", "signed_cartesian_flat_entry_exists", "signed_cartesian_flat_entry_lookup", "signed_cartesian_flat_prefix_zero", "signed_cartesian_flat_prefix_append", "signed_cartesian_flat_prefix_exists", "signed_cartesian_product_from_flat_prefix", "signed_cartesian_product_empty_columns", "signed_cartesian_product_exists", "signed_cartesian_product_row_scalar", "signed_cartesian_product_row_sum", "signed_cartesian_product_row_sums_scalar", "signed_cartesian_product_rectangular_sum", "signed_cartesian_product_prefix_sum", "signed_cartesian_product_sums_exists", "signed_cartesian_quotient_row_bound", "signed_cartesian_coordinates_exists", "signed_cartesian_product_flat_lookup", "signed_cartesian_product_extensional_unique", "signed_cartesian_product_reencode", "signed_cartesian_product_exists_extensionally_unique", "signed_prefix_sum_single_spike_value", "signed_prefix_sum_single_spike_exists", "signed_prefix_sum_point_spike_value", "signed_support_incidence_entry_hit", "signed_support_incidence_entry_miss", "signed_support_incidence_entry_decode", "signed_support_incidence_entry_functional", "signed_support_incidence_entry_exists", "signed_support_incidence_zero_source_value", "signed_support_incidence_nonzero_source_image", "signed_support_incidence_flat_entry_exists", "signed_support_incidence_flat_entry_coordinates", "signed_support_incidence_flat_prefix_zero", "signed_support_incidence_flat_prefix_append", "signed_support_incidence_flat_prefix_exists", "signed_support_incidence_from_flat_prefix", "signed_support_incidence_exists", "signed_support_incidence_row_lookup", "signed_support_incidence_column_lookup", "signed_support_incidence_row_sum_value", "signed_support_incidence_column_sum_value", "signed_support_incidence_row_sums_equal", "signed_support_incidence_column_sums_equal", "signed_support_reindex_sum_equal", "signed_support_reindex_sum_exists", "signed_mul_four_factor_interchange", "signed_mul_nonzero_factors", "dirichlet_convolution_entry_nonzero_support", "dirichlet_multiplicative_pair_factorization", "dirichlet_multiplicative_pair_entry", "dirichlet_coprime_grid_nonzero_coordinates", "dirichlet_coprime_grid_support_preserving", "dirichlet_coprime_grid_support_injective", "dirichlet_coprime_grid_support_covering", "dirichlet_coprime_grid_support_reindex", "dirichlet_coprime_product_data_construct", "dirichlet_convolution_multiplicative_values", "dirichlet_convolution_multiplicative_table", "dirichlet_convolution_multiplicative_exists_unique", "dirichlet_multiplicative_function_invertible"),
        principal_roots=("signed_support_reindex_sum_equal", "signed_cartesian_product_sums_exists", "coprime_divisor_factor_pair_exists_unique", "dirichlet_convolution_multiplicative_values", "dirichlet_convolution_multiplicative_table", "dirichlet_convolution_multiplicative_exists_unique"),
        theorem_count=461,
        root_names=("signed_multiplicative_nonempty", "signed_multiplicative_table", "signed_multiplicative_normalized", "signed_multiplicative_coprime_product", "signed_multiplicative_intro", "signed_multiplicative_zero_excluded", "signed_multiplicative_at_one_value", "signed_multiplicative_restrict", "signed_multiplicative_product_values_exist", "signed_multiplicative_positive_extensional", "coprime_divisor_factor_pair_exists_unique", "divisor_factor_pair_quotient_product", "signed_slice_sum_concatenate_values", "signed_prefix_sum_row_major_exists", "signed_cartesian_product_sums_exists", "signed_cartesian_product_reencode", "signed_cartesian_product_exists_extensionally_unique", "signed_prefix_sum_single_spike_exists", "signed_support_reindex_sum_exists", "dirichlet_convolution_multiplicative_exists_unique", "dirichlet_multiplicative_function_invertible"),
        node_count=462,
        dependency_edges=1350,
        bundle_edges=1371,
        body_nodes=35945,
        ordered_cone_names_sha256="78418f04be696b39352ae11a3470fd970d2d3ed7f792035bcd385ad7c0076deb",
        complete_non_alpha_specs_sha256="25086b5c317b7dddd47cc06b0d9ad5639b6a5d88b6ede323cf7aa1124fa9dba7",
        modules=("arithmetic_multiplicative_candidate", "coprime_divisor_decomposition_candidate", "divisor_pair_index_candidate", "signed_block_sum_candidate", "signed_cartesian_product_candidate", "signed_support_reindex_candidate", "dirichlet_multiplicative_entry_candidate", "dirichlet_multiplicative_support_candidate", "dirichlet_multiplicative_candidate"),
        principal_pins=(("signed_support_reindex_sum_equal", "3077d5330886460850c4a16cd0e57026c138813c128d9e013c61e428ec2c56cc"), ("signed_cartesian_product_sums_exists", "112d93e7f0c1b600a57b30c7b06341d249f529c30dfaf907ceeae9f8614b51c7"), ("coprime_divisor_factor_pair_exists_unique", "629b845a1c30abee52ebb49d4f59dea2b06bc00dab3403512507e737112c4d12"), ("dirichlet_convolution_multiplicative_values", "7a5bfcd97f2feacc1e3c49a520bbf41370e09c940f6d35f16b54ca27a4b84868"), ("dirichlet_convolution_multiplicative_table", "c5f3035ecf2a9e90fc3e56118bb17769ddc68feb1a32a95aa48619cf7c4b8889"), ("dirichlet_convolution_multiplicative_exists_unique", "957aa567b3f1547a98478a195178e8d5a7e88cf6a01af0b67f94413191d56970")),
    ),
    ResearchFamily(
        slug="polynomial-division-prerequisites",
        research_checkpoint_slug="polynomial-division-prerequisites",
        artifact="research/arithmetic-library/artifacts/prime-field-polynomial-division-prerequisites-proof-bundle-v1.json",
        artifact_bytes=1060637,
        artifact_sha256="fec8cf768ef2b94430d58d947daa0affada315bbc5160a03991dc4d2550dd0e9",
        count=85,
        specs_sha256="93663cc10d2d034fb933a60a914f1656fd0beb8d715bbbab8d8e1359c780ab11",
        names_sha256="c7fe5ba9e5b0cbfbdde4f0bea7ef321355661f2408ca31e5a78e3041cfb19ce0",
        edge_count=190,
        command_count=3641,
        rfc="research/arithmetic-library/prime-field-polynomial-division-prerequisites-rfc-v1.md",
        owned_names=("prime_field_subtract_exists", "prime_field_subtract_equal_zero", "prime_field_polynomial_negate_empty", "prime_field_polynomial_negate_exists", "prime_field_polynomial_negate_entry", "prime_field_polynomial_negate_bounded", "prime_field_polynomial_negate_functional", "prime_field_polynomial_negate_transport", "prime_field_polynomial_negate_involutive", "prime_field_polynomial_negate_zero", "prime_field_polynomial_negate_add_zero", "prime_field_polynomial_subtract_empty", "prime_field_polynomial_subtract_exists", "prime_field_polynomial_subtract_entry", "prime_field_polynomial_subtract_bounded", "prime_field_polynomial_subtract_functional", "prime_field_polynomial_subtract_transport", "prime_field_polynomial_subtract_recover_add", "prime_field_polynomial_subtract_from_add", "prime_field_polynomial_subtract_self_zero", "prime_field_polynomial_subtract_zero_right", "prime_field_polynomial_subtract_zero_left", "prime_field_polynomial_subtract_equal_entry_zero", "prime_field_polynomial_subtract_equal_zero", "prime_field_polynomial_subtract_add_cancel", "prime_field_polynomial_subtract_common_right_cancel", "prime_field_polynomial_suffix_exists", "prime_field_polynomial_suffix_entry", "prime_field_polynomial_suffix_bounded", "prime_field_polynomial_suffix_equal", "prime_field_polynomial_leading_zero_cut_exists", "prime_field_polynomial_trim_from_cut", "prime_field_polynomial_trim_exists", "prime_field_polynomial_trim_empty_input", "prime_field_polynomial_trim_output_coefficients", "prime_field_polynomial_trim_length_bounds", "prime_field_polynomial_trim_leading_source_nonzero", "prime_field_polynomial_trim_zero_of_empty", "prime_field_polynomial_trim_empty_of_zero", "prime_field_polynomial_trim_zero_iff", "prime_field_polynomial_trim_removed_le", "prime_field_polynomial_trim_removed_count_unique", "prime_field_polynomial_trim_retained_length_unique", "prime_field_polynomial_trim_output_equal", "prime_field_polynomial_trim_exists_unique", "prime_field_polynomial_trim_represented_degree", "prime_field_polynomial_trim_nonempty_degree_exists", "prime_field_polynomial_trim_represented_identity", "prime_field_polynomial_monic_leading_value", "prime_field_polynomial_monic_represented_degree", "prime_field_polynomial_monic_transport", "prime_field_polynomial_monic_constant", "prime_field_polynomial_monic_normalization_inverse", "prime_field_polynomial_monic_normalization_scalar_nonzero", "prime_field_polynomial_monic_normalization_entry", "prime_field_polynomial_monic_normalization_bounded", "prime_field_polynomial_monic_normalization_leading", "prime_field_polynomial_monic_normalization_monic", "prime_field_polynomial_monic_normalization_represented_degree", "prime_field_polynomial_monic_normalization_exists", "prime_field_polynomial_monic_normalization_scalar_functional", "prime_field_polynomial_monic_normalization_functional", "prime_field_polynomial_monic_normalization_value_functional", "prime_field_polynomial_monic_normalization_transport", "prime_field_polynomial_monic_normalization_fixed", "prime_field_polynomial_monic_normalization_constant", "prime_field_polynomial_monic_normalization_exists_unique", "prime_field_polynomial_monic_normalization_degree_zero_exists", "prime_field_polynomial_horner_trace_prefix", "prime_field_polynomial_horner_trace_state_bounded", "prime_field_polynomial_synthetic_exists", "prime_field_polynomial_synthetic_remainder_execution", "prime_field_polynomial_synthetic_quotient_entry", "prime_field_polynomial_synthetic_quotient_bounded", "prime_field_polynomial_synthetic_remainder_bounded", "prime_field_polynomial_synthetic_functional", "prime_field_polynomial_horner_constant_value", "prime_field_polynomial_horner_transition_values", "prime_field_polynomial_synthetic_leading_coefficient", "prime_field_polynomial_synthetic_middle_coefficients", "prime_field_polynomial_synthetic_final_coefficient", "prime_field_polynomial_synthetic_represented_degree", "prime_field_polynomial_synthetic_constant", "prime_field_polynomial_synthetic_exists_unique", "prime_field_polynomial_synthetic_zero_remainder_iff"),
        principal_roots=("prime_field_polynomial_subtract_exists", "prime_field_polynomial_trim_exists_unique", "prime_field_polynomial_monic_normalization_exists_unique", "prime_field_polynomial_synthetic_exists_unique", "prime_field_polynomial_synthetic_represented_degree", "prime_field_polynomial_synthetic_zero_remainder_iff"),
        theorem_count=292,
        root_names=("prime_field_polynomial_negate_exists", "prime_field_polynomial_negate_bounded", "prime_field_polynomial_negate_functional", "prime_field_polynomial_negate_transport", "prime_field_polynomial_negate_involutive", "prime_field_polynomial_negate_zero", "prime_field_polynomial_subtract_exists", "prime_field_polynomial_subtract_bounded", "prime_field_polynomial_subtract_transport", "prime_field_polynomial_subtract_self_zero", "prime_field_polynomial_subtract_zero_right", "prime_field_polynomial_subtract_zero_left", "prime_field_polynomial_subtract_equal_zero", "prime_field_polynomial_subtract_add_cancel", "prime_field_polynomial_subtract_common_right_cancel", "prime_field_polynomial_suffix_entry", "prime_field_polynomial_trim_empty_input", "prime_field_polynomial_trim_zero_iff", "prime_field_polynomial_trim_exists_unique", "prime_field_polynomial_trim_nonempty_degree_exists", "prime_field_polynomial_trim_represented_identity", "prime_field_polynomial_monic_leading_value", "prime_field_polynomial_monic_transport", "prime_field_polynomial_monic_normalization_inverse", "prime_field_polynomial_monic_normalization_scalar_nonzero", "prime_field_polynomial_monic_normalization_value_functional", "prime_field_polynomial_monic_normalization_transport", "prime_field_polynomial_monic_normalization_fixed", "prime_field_polynomial_monic_normalization_exists_unique", "prime_field_polynomial_monic_normalization_degree_zero_exists", "prime_field_polynomial_horner_trace_state_bounded", "prime_field_polynomial_synthetic_remainder_bounded", "prime_field_polynomial_synthetic_middle_coefficients", "prime_field_polynomial_synthetic_final_coefficient", "prime_field_polynomial_synthetic_represented_degree", "prime_field_polynomial_synthetic_constant", "prime_field_polynomial_synthetic_exists_unique", "prime_field_polynomial_synthetic_zero_remainder_iff"),
        node_count=293,
        dependency_edges=702,
        bundle_edges=740,
        body_nodes=17412,
        ordered_cone_names_sha256="4de0c35a640bbbae0b69f66d7a7796ff91132382ef31e0ea71980e3fa84cf4b1",
        complete_non_alpha_specs_sha256="93663cc10d2d034fb933a60a914f1656fd0beb8d715bbbab8d8e1359c780ab11",
        modules=("prime_field_polynomial_subtraction_candidate", "prime_field_polynomial_trim_candidate", "prime_field_polynomial_monic_candidate", "prime_field_polynomial_synthetic_candidate"),
        principal_pins=(("prime_field_polynomial_subtract_exists", "e6a46edf32d7a565ab18ccc9406cec320dbeefc6f0094b7169f28a1080d6a965"), ("prime_field_polynomial_trim_exists_unique", "9d2f9bdd9da63a0f151a5b0b8c0918506ee25f3868bcd3138b2810c94691caa3"), ("prime_field_polynomial_monic_normalization_exists_unique", "8e2fc07b075ca8acacefcd2ba4ac6ef42511e463f64745b2875a498484eedcb5"), ("prime_field_polynomial_synthetic_exists_unique", "a9ca5a2a94437641e4cc683ef0dcdabb5eef4bbb4a181620e6760f1ff285ad7b"), ("prime_field_polynomial_synthetic_represented_degree", "c8b3b71ec31e34582c37aa3037efa57961699f87f9dfc242316db5bb5e951392"), ("prime_field_polynomial_synthetic_zero_remainder_iff", "817632388315e7ec579bf1788ae68f75200a7cee737a17f46779150cf4c45441")),
    ),

)

FAMILIES = RESEARCH_FAMILIES
FAMILY_BY_SLUG = MappingProxyType({family.slug: family for family in FAMILIES})
FAMILY_BY_NAME = MappingProxyType({
    name: family for family in FAMILIES for name in family.owned_names
})
FACTORY_BY_MODULE = MappingProxyType({owner.module: owner for owner in FACTORIES})
FRONTIER_NEW_NAMES = tuple(name for family in FAMILIES for name in family.owned_names)
_FACTORY_FIELDS = ("campaign", "module", "factory", "rfc", "source_bytes", "source_sha256", "count", "specs_sha256", "test_filename")
_FAMILY_FIELDS = ("slug", "research_checkpoint_slug", "artifact", "artifact_bytes", "artifact_sha256", "count", "specs_sha256", "names_sha256", "edge_count", "command_count", "rfc", "owned_names", "principal_roots", "theorem_count", "root_names", "node_count", "dependency_edges", "bundle_edges", "body_nodes", "ordered_cone_names_sha256", "complete_non_alpha_specs_sha256", "modules", "principal_pins")


def _metadata_digest() -> str:
    payload = (
        tuple(tuple(getattr(owner, field) for field in _FACTORY_FIELDS) for owner in FACTORIES),
        tuple(tuple(getattr(family, field) for field in _FAMILY_FIELDS) for family in FAMILIES),
    )
    return sha256(json.dumps(payload, ensure_ascii=True, separators=(",", ":")).encode()).hexdigest()


def validate_research_metadata() -> None:
    """Metadata-only eligibility; no source, artifact, catalogue or kernel calls."""
    try:
        if (
            type(FACTORIES) is not tuple or type(FAMILIES) is not tuple
            or FAMILIES is not RESEARCH_FAMILIES
            or len(FACTORIES) != EXPECTED_RESEARCH_FACTORY_COUNT
            or len(FAMILIES) != EXPECTED_RESEARCH_FAMILY_COUNT
            or any(type(owner) is not ResearchFactory for owner in FACTORIES)
            or any(type(family) is not ResearchFamily for family in FAMILIES)
            or _metadata_digest() != EXPECTED_RESEARCH_METADATA_SHA256
            or len(FAMILY_BY_SLUG) != len(FAMILIES)
            or len(FACTORY_BY_MODULE) != len(FACTORIES)
            or len(FAMILY_BY_NAME) != EXPECTED_RESEARCH_COUNT
            or tuple(FAMILY_BY_NAME) != FRONTIER_NEW_NAMES
            or tuple(FAMILY_BY_SLUG.values()) != FAMILIES
            or tuple(FACTORY_BY_MODULE.values()) != FACTORIES
            or any(FAMILY_BY_NAME[name] is not family
                   for family in FAMILIES for name in family.owned_names)
            or sum(family.count for family in FAMILIES) != EXPECTED_RESEARCH_COUNT
            or sum(family.edge_count for family in FAMILIES) != EXPECTED_RESEARCH_EDGE_COUNT
            or sum(family.command_count for family in FAMILIES) != EXPECTED_RESEARCH_COMMAND_COUNT
            or sha256("\n".join(FRONTIER_NEW_NAMES).encode()).hexdigest()
            != EXPECTED_RESEARCH_NAMES_SHA256
        ):
            raise ResearchClosureError("the research-v32 metadata seal changed")
        for owner in FACTORIES:
            if (
                re.fullmatch(r"[a-z][a-z0-9_]*_candidate", owner.module) is None
                or owner.factory != f"make_{owner.module}_theorems"
                or not 0 < owner.source_bytes <= MAX_SOURCE_BYTES
                or owner.count <= 0
                or "/" in owner.rfc or "\\" in owner.rfc or ".." in owner.rfc
                or not owner.rfc.endswith("-rfc-v1.md")
                or re.fullmatch(r"test_[a-z][a-z0-9_]*\.py", owner.test_filename) is None
            ):
                raise ResearchClosureError("invalid research-v32 factory metadata")
        for family in FAMILIES:
            if (
                re.fullmatch(r"[a-z][a-z0-9-]*", family.research_checkpoint_slug) is None
                or not 0 < family.artifact_bytes <= DEFAULT_BUNDLE_LIMITS.max_payload_bytes
                or not 0 < family.node_count <= DEFAULT_BUNDLE_LIMITS.max_nodes
                or family.node_count != family.theorem_count + 1
                or family.bundle_edges != family.dependency_edges + len(family.root_names)
                or family.bundle_edges > DEFAULT_BUNDLE_LIMITS.max_edges
                or not 0 < family.body_nodes <= DEFAULT_BUNDLE_LIMITS.max_total_body_nodes
                or family.count != len(family.owned_names)
                or not set(family.principal_roots) <= set(family.owned_names)
                or tuple(name for name, _ in family.principal_pins) != family.principal_roots
                or not family.artifact.startswith("research/arithmetic-library/artifacts/")
                or Path(family.artifact).is_absolute() or ".." in Path(family.artifact).parts
                or tuple(owner.module for owner in FACTORIES if owner.campaign == family.slug)
                != family.modules
            ):
                raise ResearchClosureError("invalid research-v32 family metadata")
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, ResearchClosureError):
            raise
        raise ResearchClosureError("the research-v32 metadata is malformed") from error


def research_family(slug: str) -> ResearchFamily:
    validate_research_metadata()
    if type(slug) is not str or slug not in FAMILY_BY_SLUG:
        raise ResearchClosureError(f"unknown research-v32 family {slug!r}")
    return FAMILY_BY_SLUG[slug]


def _read_pinned(path: Path, size: int, digest: str, *, maximum: int) -> bytes:
    """Bound before allocation/parse; a successful hash is provenance only."""
    if (type(size) is not int or not 0 < size <= maximum
            or type(digest) is not str or re.fullmatch(r"[0-9a-f]{64}", digest) is None):
        raise ResearchClosureError("invalid bounded source pin")
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size != size:
            raise ResearchClosureError(f"sealed source size/type changed: {path.name}")
        with path.open("rb") as source:
            payload = source.read(size + 1)
    except OSError as error:
        raise ResearchClosureError(f"sealed source unavailable: {path.name}") from error
    if len(payload) != size or sha256(payload).hexdigest() != digest:
        raise ResearchClosureError(f"sealed source bytes changed: {path.name}")
    return payload


def validate_research_source_bytes() -> tuple[ResearchFactory, ...]:
    """Authenticate every new mathematical source without opening proof artifacts."""
    validate_research_metadata()
    for owner in FACTORIES:
        _read_pinned(Path(__file__).with_name(owner.module + ".py"),
                     owner.source_bytes, owner.source_sha256, maximum=MAX_SOURCE_BYTES)
    return FACTORIES


def read_research_bundle_bytes(slug: str, source: str | Path) -> bytes:
    """Read exactly one bounded frozen artifact; no acceptance claim."""
    family = research_family(slug)
    if not isinstance(source, (str, Path)):
        raise ResearchClosureError("a research-v32 proof source must be a filesystem path")
    return _read_pinned(Path(source), family.artifact_bytes, family.artifact_sha256,
                        maximum=DEFAULT_BUNDLE_LIMITS.max_payload_bytes)


@lru_cache(maxsize=1)
def _load_research_specs() -> tuple[TheoremSpec, ...]:
    validate_research_source_bytes()
    rows: list[TheoremSpec] = []
    for owner in FACTORIES:
        try:
            module = import_module(f".{owner.module}", package=__package__)
            source = Path(__file__).with_name(owner.module + ".py")
            factory = getattr(module, owner.factory, None)
            if (Path(getattr(module, "__file__", "")).resolve() != source.resolve()
                    or not callable(factory) or getattr(factory, "__module__", None) != module.__name__):
                raise ResearchClosureError(f"foreign cached research factory {owner.module}")
            candidates = tuple(factory(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise ResearchClosureError(f"unavailable frozen factory {owner.module}") from error
        if (
            len(candidates) != owner.count
            or any(type(row) is not TheoremSpec for row in candidates)
            or _specs_digest(candidates) != owner.specs_sha256
        ):
            raise ResearchClosureError(f"exact frozen specifications changed: {owner.module}")
        rows.extend(candidates)
    result = tuple(rows)
    if (len(result) != EXPECTED_RESEARCH_COUNT
            or tuple(row.name for row in result) != FRONTIER_NEW_NAMES
            or _specs_digest(result) != EXPECTED_RESEARCH_SPECS_SHA256):
        raise ResearchClosureError("the full research-v32 specification inventory changed")
    offset = 0
    for family in FAMILIES:
        own = result[offset:offset + family.count]
        offset += family.count
        if (
            _specs_digest(own) != family.specs_sha256
            or sum(len(row.dependencies) for row in own) != family.edge_count
            or sum(len(row.script) for row in own) != family.command_count
            or sha256("\n".join(row.name for row in own).encode()).hexdigest() != family.names_sha256
        ):
            raise ResearchClosureError(f"exact family specifications changed: {family.slug}")
        by_name = {row.name: row for row in own}
        for name, digest in family.principal_pins:
            if sha256(by_name[name].statement.encode()).hexdigest() != digest:
                raise ResearchClosureError(f"an exact principal statement changed: {name}")
    return result


def research_specs() -> tuple[TheoremSpec, ...]:
    """Reviewed exact syntax only; deliberately artifact-free."""
    validate_research_source_bytes()
    return _load_research_specs()


def clear_research_metadata_cache() -> None:
    _load_research_specs.cache_clear()


def _parent_specs(parent_specs: tuple[TheoremSpec, ...] | None) -> tuple[TheoremSpec, ...]:
    if parent_specs is None:
        # Native and browser installations both use installed theorem syntax.
        # No authoring registry, source checkout or catalogue is consulted.
        from . import editions_v31
        parent_specs = editions_v31.ALPHA_CHECKED_SPECS
    if (type(parent_specs) is not tuple
            or len(parent_specs) != PARENT_ALPHA_V31_COUNT
            or any(type(row) is not TheoremSpec for row in parent_specs)
            or _specs_digest(parent_specs) != PARENT_ALPHA_V31_SPECS_SHA256):
        raise ResearchClosureError("the exact immutable Alpha-v31 parent syntax changed")
    return parent_specs


def research_plan(
    slug: str, *, parent_specs: tuple[TheoremSpec, ...] | None = None,
) -> ResearchPlan:
    """Exact, complete topological ownership plan; no proof file is loaded."""
    family = research_family(slug)
    parent = _parent_specs(parent_specs)
    frontier = research_specs()
    inventory = (*parent, *frontier)
    table = {row.name: row for row in inventory}
    if len(table) != len(inventory):
        raise ResearchClosureError("an additive theorem overwrites an existing name")
    available: set[str] = set()
    for row in inventory:
        if (type(row.dependencies) is not tuple
                or len(set(row.dependencies)) != len(row.dependencies)
                or not set(row.dependencies) <= available):
            raise ResearchClosureError(f"unknown, duplicate or forward premise: {row.name}")
        available.add(row.name)
    included: set[str] = set()
    pending = list(family.owned_names)
    while pending:
        name = pending.pop()
        if name not in included:
            included.add(name)
            pending.extend(table[name].dependencies)
    selected = tuple(row for row in inventory if row.name in included)
    non_alpha = tuple(row for row in frontier if row.name in included)
    used = {name for row in non_alpha for name in row.dependencies}
    roots = tuple(row.name for row in non_alpha if row.name not in used)
    ordered_digest = sha256("\n".join(row.name for row in selected).encode()).hexdigest()
    frontier_digest = _specs_digest(non_alpha)
    edges = sum(len(row.dependencies) for row in selected)
    if (
        len(selected) != family.theorem_count
        or roots != family.root_names or not set(roots) <= set(family.owned_names)
        or ordered_digest != family.ordered_cone_names_sha256
        or frontier_digest != family.complete_non_alpha_specs_sha256
        or edges != family.dependency_edges
    ):
        raise ResearchClosureError(f"the exact complete proof cone changed: {slug}")
    indices = {row.name: index for index, row in enumerate(inventory)}
    owned = frozenset(family.owned_names)
    rows = tuple(ResearchRow(
        node_id=index, inventory_index=indices[row.name], name=row.name,
        statement_sha256=sha256(row.statement.encode()).hexdigest(),
        dependencies=row.dependencies,
        campaign=FAMILY_BY_NAME[row.name].slug if row.name in FAMILY_BY_NAME else None,
        is_owned=row.name in owned,
    ) for index, row in enumerate(selected))
    return ResearchPlan(
        family, rows, selected, roots, tuple(row.name for row in non_alpha),
        family.owned_names, edges, ordered_digest, frontier_digest,
    )


def check_research_proof_bundle(
    slug: str, bundle: ProofBundle, target: Formula, *,
    parent_specs: tuple[TheoremSpec, ...] | None = None,
) -> CheckedProofBundle:
    """Check exact targets/ordered premises/packaging, then EVERY original HA body."""
    plan = research_plan(slug, parent_specs=parent_specs)
    family = plan.family
    positions = plan.positions
    if (type(bundle) is not ProofBundle or type(bundle.nodes) is not tuple
            or len(bundle.nodes) != family.node_count
            or type(bundle.root) is not int or bundle.root != len(plan.rows)):
        raise ResearchClosureError("the complete artifact inventory or root changed")
    for row, spec, node in zip(plan.rows, plan.specs, bundle.nodes[:-1], strict=True):
        if (type(node) is not BundleNode or type(node.node_id) is not int
                or node.node_id != row.node_id
                or node.target != _closed_formula(spec.statement)
                or type(node.dependencies) is not tuple
                or any(type(value) is not int for value in node.dependencies)
                or node.dependencies != tuple(positions[name] for name in row.dependencies)):
            raise ResearchClosureError(f"an exact target or ordered premise changed: {row.name}")
    by_name = {row.name: row for row in plan.specs}
    expected_target, expected_body = _packaging_root(tuple(
        _closed_formula(by_name[name].statement) for name in plan.root_names
    ))
    final = bundle.nodes[-1]
    if (type(final) is not BundleNode or type(final.node_id) is not int
            or final.node_id != len(plan.rows) or final.target != expected_target
            or final.body != expected_body or type(final.dependencies) is not tuple
            or any(type(value) is not int for value in final.dependencies)
            or final.dependencies != tuple(positions[name] for name in plan.root_names)
            or target != expected_target):
        raise ResearchClosureError("the exact maximal-theorem packaging root changed")
    receipt = check_proof_bundle(bundle, target)
    if (type(receipt) is not CheckedProofBundle or receipt.target != target
            or receipt.root != bundle.root or receipt.node_count != family.node_count
            or receipt.kernel_calls != family.node_count
            or receipt.topological_order != tuple(range(family.node_count))
            or receipt.dependency_edges != family.bundle_edges
            or receipt.total_body_nodes != family.body_nodes):
        raise ResearchClosureError("a complete original-kernel check or exact body metric changed")
    return receipt


__all__ = (
    "ResearchClosureError", "ResearchFactory", "ResearchFamily",
    "ResearchRow", "ResearchPlan", "FACTORIES", "FAMILIES",
    "RESEARCH_FAMILIES", "FAMILY_BY_SLUG", "FAMILY_BY_NAME",
    "FACTORY_BY_MODULE", "FRONTIER_NEW_NAMES", "research_family",
    "research_specs", "research_plan",
    "validate_research_metadata", "validate_research_source_bytes",
    "read_research_bundle_bytes", "check_research_proof_bundle",
    "clear_research_metadata_cache",
)
