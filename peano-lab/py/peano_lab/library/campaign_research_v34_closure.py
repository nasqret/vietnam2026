"""Exact browser-safe v34 providers for polynomial gcd and congruence proofs.

Metadata is not proof authority. Checked use authenticates and checks every
actual HA body; compiled-Lean verification belongs to fresh release gates.
The immutable polynomial artifact keeps its original dependency-first order.
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
    ordered_cone_names: tuple[str, ...]
    complete_specs_sha256: str
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


PARENT_ALPHA_V33_COUNT = 4092
PARENT_ALPHA_V33_SPECS_SHA256 = "7b7459e65b0b8da951044a992675ab820488d9aab40985c1ded68da56b007a47"
PARENT_ALPHA_V33_IDENTITY_SHA256 = "9e66890600db5f787230fb5e48e18ce08026750ba4a9d3fa7b0b1e30f6e39a3d"
PARENT_ALPHA_V33_ENROLLMENT_SHA256 = "0d4101bfee06dfff5a49ee8cfaf955a2c81a43ac622623e27890d6fe541eeaa0"
# Exact syntax/artifact registration; mathematical admission still needs fresh gates.
REGISTRATION_COMPLETE = True
EXPECTED_RESEARCH_COUNT = 131
EXPECTED_RESEARCH_EDGE_COUNT = 604
EXPECTED_RESEARCH_COMMAND_COUNT = 12869
EXPECTED_RESEARCH_NAMES_SHA256 = "598d12b73489765a771d4edde6524abaabb3d61c3ea8d583b5e79b7f0ffdf024"
EXPECTED_RESEARCH_SPECS_SHA256 = "ab0c6fd6bd8aa8d5d93dcbe59c5d0721d9e747efcab6413c5b0675f720f9fc60"
EXPECTED_RESEARCH_FAMILY_COUNT = 2
EXPECTED_RESEARCH_FACTORY_COUNT = 21
EXPECTED_RESEARCH_METADATA_SHA256 = "52e939652f8ea66d6ad6511dcaa534f95e5aaef86f69423eb2f2effd2106ea8f"
MAX_SOURCE_BYTES = 2 * 1024 * 1024

FACTORIES = (
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_shift_candidate",
        factory="make_prime_field_polynomial_shift_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=29786,
        source_sha256="325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b",
        count=15,
        specs_sha256="beac32710e2191f4dc40f6317dc376f6b3307ad8ad48a7ccbac17c8bea990081",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_scalar_convolution_candidate",
        factory="make_prime_field_polynomial_scalar_convolution_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=23637,
        source_sha256="e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e",
        count=10,
        specs_sha256="a8ab3e2660a01dc79520722de6093c534e4184dcdbcb9481317df4d5b6a54a7b",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_append_candidate",
        factory="make_prime_field_polynomial_append_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=28396,
        source_sha256="271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042",
        count=6,
        specs_sha256="6035968b0f11aec5e4bd6cb43b4d4958318b55f600fab914025479f571b75c2a",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_shift_equivalence_candidate",
        factory="make_prime_field_polynomial_shift_equivalence_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=6021,
        source_sha256="8846224923876a4f57ad8d6f31020838ccc86c86a683ec78a7c7c23c35b92068",
        count=1,
        specs_sha256="d68b99a4ed9f996bd7e8b23fd0f17e165176b949f07a806a4d2c935d4372529e",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_associativity_step_candidate",
        factory="make_prime_field_polynomial_associativity_step_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=26607,
        source_sha256="dd85dbd1bd87143715a4286724ac7c87f280a909dac6759f00a6cb7dff7c85f1",
        count=3,
        specs_sha256="87017c7298a0247444be68f9be34e6b354b89d491ca7ee49ea4bd06effd6b2cd",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_associativity_induction_candidate",
        factory="make_prime_field_polynomial_associativity_induction_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=9924,
        source_sha256="8d276a028764cd08e6eaebbf25bb4e21fcd5076a610d356a77d52ba6603ebe4c",
        count=2,
        specs_sha256="b6ad06b7925dbb35202bb263ef14c7dc69d18c80771e075497d0a17d42294dc8",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_divisibility_candidate",
        factory="make_prime_field_polynomial_divisibility_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=15168,
        source_sha256="f544adedd3ce963e4a773e8582efcb0f91ba7491207c9792d477d452e854f2b8",
        count=7,
        specs_sha256="2ee9efd3344ef213b2170f080ff541ca0a7a45a018ace9f2f7912cd301bc8bce",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_left_unit_candidate",
        factory="make_prime_field_polynomial_left_unit_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=16858,
        source_sha256="dbb8debb4716b6bb9b246700f7e93865c8a6c1b12a3b65c0ffbb62206a890ba6",
        count=8,
        specs_sha256="d948ceded7269773df58eca0ec6d16f77aa8f207483beed48f85bec30e083f08",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_alignment_candidate",
        factory="make_prime_field_polynomial_alignment_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=11780,
        source_sha256="eb16e2eb02dbd66a7706e616388182992b8cf2e0715818dc1f7748938e7d798e",
        count=7,
        specs_sha256="76b9c342744170146fcb7898cb5a20154334147578b7e01d059f01b9015d5aec",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_aligned_add_candidate",
        factory="make_prime_field_polynomial_aligned_add_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=20704,
        source_sha256="a05bb4f5c4230ca05f51690d3ab82e33ff4596af65176874e25fbe38cf87a0db",
        count=9,
        specs_sha256="b8ce285a000180baef6318db67202fc4fa258ae5bd6aabecfc098236f9588339",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_aligned_algebra_candidate",
        factory="make_prime_field_polynomial_aligned_algebra_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=16013,
        source_sha256="a68de84439afb5f6dd87f1d47449c0bce8dd53a66346c00cc1b7645fb80b2390",
        count=4,
        specs_sha256="0db1ddc08762db5e207469343143a7ead24de983e8f9a21473592a8d6c97d6f4",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_euclidean_identity_candidate",
        factory="make_prime_field_polynomial_euclidean_identity_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=11235,
        source_sha256="8efdcd2abf2143891b79edcb3fc90d7126ae69507c1c631ed33b497172ffdb77",
        count=2,
        specs_sha256="f992bc15fd84b7f3ba9b0f28c0219cb97a53c47c669a9563b087e7a3c535ab27",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_aligned_distributivity_candidate",
        factory="make_prime_field_polynomial_aligned_distributivity_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=8518,
        source_sha256="7d535939e24fe6d82158c485533b2ff6934f4d897b6141fde6c50b4fec9788ba",
        count=2,
        specs_sha256="22b9e7ed76b79f0210eee74433a965db62cc5a4b688c3ab2cf0f236b1dca5719",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_left_constant_candidate",
        factory="make_prime_field_polynomial_left_constant_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=17620,
        source_sha256="9a7a4de30f5f389bcabc2e6267a0d2cc5dc5f061059dcea303a0a03dab58509a",
        count=6,
        specs_sha256="736cd0d7d21f33ac50a189f66a7457909042c83917d9e9cfc2d4932c6fe06836",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_euclidean_normalization_candidate",
        factory="make_prime_field_polynomial_euclidean_normalization_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=16401,
        source_sha256="d2cddfe42dc0d22104dc4e85e95116222914df11ac840d2082a4ff2e462f146f",
        count=5,
        specs_sha256="815b67478a8c42bd854002317e31ab5e77739551f19516dfc923b7fe66d0ce74",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_euclidean_transport_candidate",
        factory="make_prime_field_polynomial_euclidean_transport_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=18256,
        source_sha256="9a589d1749eb38d30d1a24364bc4d66f7df0efb59247527f7831f97557da9c30",
        count=5,
        specs_sha256="aba201eca067048dc65b5a2f7f6affd415c6ebd639c35bc613503227a65059b8",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_bezout_backward_candidate",
        factory="make_prime_field_polynomial_bezout_backward_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=18747,
        source_sha256="c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702",
        count=3,
        specs_sha256="bbab74ad9d4ecfe3b01e97ab75dccd532fc23e22a5cb275a68963f15dbf57564",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_gcd_bezout_laws_candidate",
        factory="make_prime_field_polynomial_gcd_bezout_laws_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=15300,
        source_sha256="76b90226e5e29fdde3d9bb49accccf8d9b4c0cc17a4de406af253e999102533c",
        count=4,
        specs_sha256="cbf875f3e7d13394f062e4f5f4349beba59a2ac363a599e7b02649906ea6d6a2",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_gcd_existence_candidate",
        factory="make_prime_field_polynomial_gcd_existence_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=26480,
        source_sha256="81f2f48dd2e81894c7a267453646eb6f2b6f9bd3ee320386d8c561f6b9f8b8ca",
        count=9,
        specs_sha256="d0bfe3e77e26b0e97c3b20bdd3f6256064c2b34ff56a48039e04f9dbdfcc5d7e",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-gcd-bezout",
        module="prime_field_polynomial_gcd_uniqueness_candidate",
        factory="make_prime_field_polynomial_gcd_uniqueness_candidate_theorems",
        rfc="prime-field-polynomial-gcd-bezout-rfc-v1.md",
        source_bytes=31432,
        source_sha256="916c24ad6c59609612e97daee6e49347a9522cdb28b44f6f09c6c5760bff0b5b",
        count=11,
        specs_sha256="4bea19123a71314f8d2bf07019377497f56990b31f71a51de861f2b9339a1db3",
        test_filename="test_campaign_research_v34_closure.py",
    ),
    ResearchFactory(
        campaign="congruence-arithmetic",
        module="linear_congruence_classification_candidate",
        factory="make_linear_congruence_classification_candidate_theorems",
        rfc="linear-congruence-classification-rfc-v1.md",
        source_bytes=18128,
        source_sha256="12b1a98ce830704485f1ea78475fba8b10e39031ffbef00b1b5dfc8ffdef7f47",
        count=12,
        specs_sha256="b1128492a1dd801ec81f63a39f586f733e95b79a1d2a19d33bb0363130d560c8",
        test_filename="test_campaign_research_v34_closure.py",
    ),
)

RESEARCH_FAMILIES = (
    ResearchFamily(
        slug="polynomial-gcd-bezout",
        research_checkpoint_slug="working-polynomial-gcd119",
        artifact="research/arithmetic-library/artifacts/prime-field-polynomial-gcd-bezout-proof-bundle-v1.json",
        artifact_bytes=5193292,
        artifact_sha256="3fe18ad2899cff7db5fbe19df8570ef70b1bfb902171d5212e9b036dda660a46",
        count=119,
        specs_sha256="72701944f71e8d93c55bcf29d27fc92ac616452801ab75c3e478df4d77df4c38",
        names_sha256="51f959e944c81af1f430aebed63f10934f50f67fdae6934048551ce7bbf81ef5",
        edge_count=543,
        command_count=12211,
        rfc="research/arithmetic-library/prime-field-polynomial-gcd-bezout-rfc-v1.md",
        owned_names=("prime_field_polynomial_shift_exists", "prime_field_polynomial_shift_bounded", "prime_field_polynomial_shift_functional", "prime_field_polynomial_shift_zero_prefix", "polynomial_zero_extended_shift_forward", "polynomial_zero_extended_shift_reverse", "polynomial_diagonal_term_shift_right_iff", "prime_field_convolution_coefficient_shift_right_iff", "polynomial_product_length_shift_right_nonempty", "prime_field_polynomial_convolution_shift_right_nonempty", "prime_field_polynomial_convolution_shift_right_empty", "prime_field_polynomial_convolution_shift_right_equivalent", "prime_field_polynomial_convolution_shift_right_exists", "prime_field_polynomial_shift_power_zero", "prime_field_polynomial_shift_power_successor", "beta_sum_pointwise_mod_scale", "polynomial_zero_extended_scale_congruent", "polynomial_diagonal_term_right_scale_congruent", "polynomial_diagonal_sum_right_scale_congruent", "prime_field_convolution_coefficient_right_scale", "prime_field_polynomial_convolution_right_scale", "prime_field_polynomial_convolution_right_scale_equal", "prime_field_polynomial_convolution_right_scale_exists", "prime_field_polynomial_scale_zero_value", "prime_field_polynomial_convolution_right_scale_zero", "prime_field_polynomial_append_shift_constant_add", "prime_field_polynomial_append_shift_constant_decomposition_exists", "prime_field_convolution_coefficient_right_append_add", "prime_field_polynomial_shift_scale_aligned_sum_exists", "prime_field_polynomial_convolution_right_append_equivalent", "prime_field_polynomial_convolution_right_append_exists", "prime_field_polynomial_shift_equivalent_congruent", "prime_field_polynomial_convolution_shift_scale_aligned_equivalent", "prime_field_polynomial_shift_scale_aligned_congruent", "prime_field_polynomial_convolution_associativity_append_step", "prime_field_polynomial_nested_empty_right_equivalent", "prime_field_polynomial_convolution_associative_equivalent", "prime_field_polynomial_right_divides_from_product", "prime_field_polynomial_right_divides_divisor_bounded", "prime_field_polynomial_right_divides_dividend_bounded", "prime_field_polynomial_right_divides_equivalent_target", "prime_field_polynomial_right_divides_empty", "prime_field_polynomial_right_divides_equivalent_divisor", "prime_field_polynomial_right_divides_transitive", "polynomial_diagonal_left_unit_first_term", "polynomial_diagonal_left_unit_tail_term", "polynomial_diagonal_left_unit_natural_sum", "prime_field_convolution_coefficient_left_unit", "prime_field_polynomial_convolution_left_unit_equal", "prime_field_polynomial_convolution_left_unit_equivalent", "prime_field_polynomial_convolution_left_unit_exists", "prime_field_polynomial_right_divides_reflexive", "prime_field_polynomial_bounded_representative_at_length_exists", "prime_field_polynomial_common_representatives_same_length", "prime_field_polynomial_common_representatives_transport", "prime_field_polynomial_common_representatives_at_length_exists", "prime_field_polynomial_common_representatives_exists", "prime_field_polynomial_common_representatives_functional", "prime_field_polynomial_common_representatives_symmetric", "prime_field_polynomial_aligned_add_from_common", "prime_field_polynomial_aligned_add_bounded", "prime_field_polynomial_aligned_add_from_fixed", "prime_field_polynomial_aligned_add_transport", "prime_field_polynomial_aligned_add_commutative", "prime_field_polynomial_aligned_add_functional", "prime_field_polynomial_aligned_add_exists", "prime_field_polynomial_aligned_add_realize", "prime_field_polynomial_aligned_subtract_from_fixed", "prime_field_polynomial_aligned_subtract_exists", "prime_field_polynomial_aligned_add_cancel_left", "prime_field_polynomial_aligned_add_associative", "prime_field_polynomial_aligned_subtract_functional", "prime_field_polynomial_add_trim_aligned", "prime_field_polynomial_division_execution_aligned_identity", "prime_field_polynomial_aligned_convolution_left_add", "prime_field_polynomial_aligned_convolution_right_add", "polynomial_diagonal_left_constant_first_term", "polynomial_diagonal_left_constant_natural_sum", "prime_field_convolution_coefficient_left_constant", "prime_field_polynomial_left_constant_product_to_scale", "prime_field_polynomial_scale_to_left_constant_product", "prime_field_polynomial_left_constant_product_exists", "prime_field_polynomial_division_remainder_length_descent", "prime_field_polynomial_division_constant_remainder_empty", "prime_field_polynomial_scale_implies_right_divides", "prime_field_polynomial_monic_normalization_right_associates", "prime_field_polynomial_normalized_right_associate_exists", "prime_field_polynomial_right_divides_aligned_add", "prime_field_polynomial_right_divides_aligned_subtract", "prime_field_polynomial_right_divides_left_product", "prime_field_polynomial_common_right_divisor_euclidean_transport", "prime_field_polynomial_division_execution_common_right_divisors", "prime_field_polynomial_euclidean_backward_coefficient_identity", "prime_field_polynomial_bezout_euclidean_backward", "prime_field_polynomial_division_execution_bezout_backward", "prime_field_polynomial_aligned_add_empty_right", "prime_field_polynomial_bezout_from_right_multiple", "prime_field_polynomial_bezout_equivalent_transport", "prime_field_polynomial_bezout_common_right_divisor", "prime_field_polynomial_division_remainder_bounded", "prime_field_polynomial_reduced_representative_exists", "prime_field_polynomial_gcd_bezout_empty_second", "prime_field_polynomial_gcd_bezout_equivalent_second", "prime_field_polynomial_gcd_bezout_division_backward", "prime_field_polynomial_gcd_bezout_exists_up_to", "prime_field_polynomial_gcd_bezout_exists", "prime_field_polynomial_bezout_is_right_gcd", "prime_field_polynomial_normalized_gcd_bezout_exists", "prime_field_polynomial_nonzero_leading_equivalent_length_bound", "prime_field_polynomial_equivalent_represented_degrees_equal", "prime_field_polynomial_product_equivalent_nonzero_left_nonempty", "prime_field_polynomial_right_divides_represented_factorization", "prime_field_polynomial_right_divides_represented_degree_bound", "prime_field_polynomial_monic_singleton_multiple_equivalent", "prime_field_polynomial_monic_equal_degree_right_divides_equivalent", "prime_field_polynomial_monic_right_associates_equivalent", "prime_field_polynomial_empty_right_divisor_implies_equivalent_zero", "prime_field_polynomial_normal_right_associates_equivalent", "prime_field_polynomial_normalized_gcd_equivalent_unique"),
        principal_roots=("prime_field_polynomial_convolution_shift_right_exists", "prime_field_polynomial_convolution_right_scale_exists", "prime_field_polynomial_convolution_right_scale_zero", "prime_field_convolution_coefficient_right_append_add", "prime_field_polynomial_convolution_right_append_exists", "prime_field_polynomial_right_divides_dividend_bounded", "prime_field_polynomial_right_divides_reflexive", "prime_field_polynomial_aligned_subtract_from_fixed", "prime_field_polynomial_aligned_subtract_functional", "prime_field_polynomial_left_constant_product_to_scale", "prime_field_polynomial_division_constant_remainder_empty", "prime_field_polynomial_normalized_gcd_bezout_exists", "prime_field_polynomial_normalized_gcd_equivalent_unique", "prime_field_polynomial_bezout_is_right_gcd"),
        theorem_count=492,
        root_names=("prime_field_polynomial_convolution_shift_right_exists", "prime_field_polynomial_convolution_right_scale_exists", "prime_field_polynomial_convolution_right_scale_zero", "prime_field_convolution_coefficient_right_append_add", "prime_field_polynomial_convolution_right_append_exists", "prime_field_polynomial_right_divides_dividend_bounded", "prime_field_polynomial_right_divides_reflexive", "prime_field_polynomial_aligned_subtract_from_fixed", "prime_field_polynomial_aligned_subtract_functional", "prime_field_polynomial_left_constant_product_to_scale", "prime_field_polynomial_division_constant_remainder_empty", "prime_field_polynomial_normalized_gcd_bezout_exists", "prime_field_polynomial_normalized_gcd_equivalent_unique"),
        node_count=493,
        dependency_edges=1565,
        bundle_edges=1578,
        body_nodes=47545,
        ordered_cone_names_sha256="37f749a11c76fd6d38d4a328dfd450fd8a0ea3e79ffac8f22ad4874239f29e25",
        ordered_cone_names=("zero_add", "add_succ_left", "add_comm", "add_assoc", "mul_zero_left", "mul_succ_left", "mul_comm", "mul_add", "mul_assoc", "one_mul", "mul_one", "add_mul", "succ_ne_zero", "succ_injective", "le_refl", "le_trans", "no_succ_add_fixed", "drop_add_prefix_from_fixed", "antisymm_from_witnesses", "le_antisymm", "le_total", "add_eq_zero_right", "mul_eq_zero", "zero_or_succ", "nonzero_is_succ", "add_congr", "add_right_cancel", "add_left_cancel", "zero_le", "le_succ_self", "le_zero", "one_le_of_ne_zero", "le_add_left", "le_add_right", "add_le_add_right", "add_le_add_left", "succ_le_succ", "le_of_succ_le_succ", "le_succ", "lt_to_le", "add_le_cancel_right", "lt_irrefl_expanded", "le_eq_or_lt", "lt_of_lt_of_le", "le_or_lt", "lt_trichotomy", "lt_not_le", "lt_not_eq_add_middle", "mul_le_mul_right", "division_remainder_succ", "division_remainder_exists", "positive_quotient_gap_impossible", "division_remainder_unique", "add_eq_zero_left", "mul_eq_one_components", "mul_ne_zero", "multiple_zero", "multiple_refl", "multiple_mul_right", "multiple_trans", "divisor_le_nonzero", "divisor_one", "factor_difference", "divides_remainder", "divides_linear_step", "is_gcd_zero_right", "is_gcd_euclid_forward", "gcd_exists_up_to", "gcd_exists_relational", "coprime_one_left", "is_gcd_one_to_coprime", "add_permute_outer", "balanced_bezout_euclid_step", "gcd_balanced_bezout_exists_up_to", "gcd_balanced_bezout_exists", "balanced_combination_scale_right", "common_divisor_divides_balanced_result", "coprime_balanced_bezout", "gauss_coprime_cancel", "eq_decidable", "prime_nonzero", "prime_divisor_eq_one_or_self", "mod_eq_refl", "mod_eq_symm", "mod_eq_trans", "mod_eq_add", "mod_eq_mul_right", "mod_eq_mul_left", "mod_eq_mul", "remainder_decomposition_to_mod_eq", "mod_eq_bounded_unique", "mod_eq_to_remainder_decomposition", "beta_modulus_nonzero", "beta_at_self_of_bound", "beta_at_exists", "beta_at_unique", "beta_at_of_mod_eq_bound", "dvd_to_mod_zero", "bezout_mod_left", "bezout_mod_right", "mod_eq_predecessor_cancel", "binary_crt", "beta_modulus_coprime_base", "common_divisor_beta_moduli_divides_gap_times_c", "beta_moduli_coprime_of_gap_dvd", "bounded_common_multiple_step", "bounded_common_multiple_exists", "beta_moduli_coprime_of_lt_bounded_common_multiple", "beta_moduli_pairwise_coprime_bounded", "coprime_mul_left", "mod_eq_of_mod_eq_multiple", "binary_crt_fold_step", "right_factor_divides_product", "beta_value_le_code", "base_le_beta_modulus", "le_scaled_nonzero", "scaled_bounded_common_multiple", "beta_value_lt_scaled_base", "new_value_lt_scaled_base", "beta_exclusive_accumulated_product_step", "beta_exclusive_recode_congruence_step", "beta_exclusive_recode_invariant_step", "bounded_beta_exclusive_recode_invariant", "beta_prefix_extend", "beta_repeat_empty", "beta_repeat_succ_extend", "beta_repeat_exists", "beta_repeat_entry_eq", "beta_prefix_sum_trace_exists", "beta_sum_exists", "beta_sum_trace_functional", "beta_sum_functional", "beta_sum_zero", "beta_sum_succ_decompose", "prime_coprime_or_divides", "prime_not_divides_coprime", "coprime_balanced_mod_inverse", "coprime_mod_inverse", "mod_eq_cancel_coprime", "prime_mod_inverse", "finite_lt_succ_eq_or_lt", "prime_is_succ_succ", "prime_bounded_nonzero_mod_inverse", "mod_inverse_implies_coprime", "beta_pointwise_mul_prefix_extend", "beta_pointwise_mul_prefix_exists", "beta_division_prefix_extend", "beta_division_prefix_exists", "beta_sum_transport_prefix", "mod_eq_add_cancel_left", "beta_repeat_sum_exact", "prime_two_le", "beta_affine_matrix_slice_extend", "beta_affine_matrix_slice_exists", "beta_pointwise_add_prefix_extend", "beta_pointwise_add_prefix_exists", "binary_canonical_residue_functional", "matrix_recursive_lt_add_left", "matrix_rank_bounded_prefix_value", "matrix_rank_no_index_below_zero", "matrix_rank_prefix_equality_symmetric", "matrix_rank_bounded_prefix_transport", "matrix_rank_bounded_prefix_empty", "matrix_rank_bounded_prefix_drop_last", "matrix_rank_bounded_prefix_extend", "hensel_canonical_residue_exists", "signed_integer_floor_exists", "prime_field_polynomial_shift_exists", "prime_field_zero_below_prime", "prime_field_polynomial_shift_bounded", "prime_field_polynomial_shift_functional", "prime_field_polynomial_shift_zero_prefix", "polynomial_zero_extended_shift_forward", "polynomial_zero_extended_entry_exists", "polynomial_zero_extended_entry_functional", "polynomial_zero_extended_shift_reverse", "polynomial_diagonal_term_shift_right_iff", "prime_field_convolution_coefficient_shift_right_iff", "polynomial_product_length_shift_right_nonempty", "prime_field_convolution_prefix_entry", "polynomial_diagonal_term_functional", "polynomial_diagonal_prefix_entry", "polynomial_diagonal_prefix_functional", "prime_field_convolution_coefficient_functional", "polynomial_zero_extended_zero_value", "polynomial_diagonal_term_zero_left", "prime_field_residue_reflexive", "prime_field_residue_bounded_value", "prime_field_convolution_coefficient_zero_left", "polynomial_diagonal_term_zero_right", "prime_field_convolution_coefficient_zero_right", "polynomial_diagonal_term_past_support", "prime_field_convolution_coefficient_zero_past_support", "prime_field_polynomial_convolution_outside_zero", "prime_field_polynomial_convolution_shift_right_nonempty", "prime_field_polynomial_convolution_zero_left", "prime_field_polynomial_convolution_zero_right", "prime_field_polynomial_convolution_shift_right_empty", "prime_field_polynomial_power_coefficient_exists", "prime_field_polynomial_equivalent_transitive", "prime_field_polynomial_power_index_bound", "prime_field_polynomial_zero_power_coefficient", "prime_field_polynomial_zero_prefix_equivalent_empty", "prime_field_polynomial_equivalent_symmetric", "prime_field_polynomial_power_coefficient_functional", "prime_field_polynomial_power_coefficient_transport", "prime_field_polynomial_equal_implies_equivalent", "prime_field_polynomial_convolution_shift_right_equivalent", "polynomial_product_length_exists", "prime_field_convolution_prefix_from_pointwise", "polynomial_diagonal_prefix_from_pointwise", "polynomial_diagonal_term_exists", "polynomial_diagonal_prefix_exists", "prime_field_convolution_coefficient_exists", "prime_field_convolution_prefix_exists", "prime_field_polynomial_convolution_at_length_exists", "prime_field_polynomial_convolution_shift_right_exists", "prime_field_polynomial_shift_power_zero", "prime_field_polynomial_shift_power_successor", "beta_sum_pointwise_mod_scale", "polynomial_zero_extended_entry_inside", "prime_field_polynomial_scale_entry", "polynomial_zero_extended_scale_congruent", "polynomial_diagonal_term_right_scale_congruent", "polynomial_diagonal_sum_right_scale_congruent", "prime_field_convolution_coefficient_right_scale", "polynomial_product_length_functional", "prime_field_polynomial_convolution_right_scale", "prime_field_multiply_functional", "prime_field_polynomial_scale_functional", "prime_field_polynomial_convolution_right_scale_equal", "prime_field_polynomial_normalization_from_division", "prime_field_polynomial_normalization_exists", "prime_field_residue_input_equal", "prime_field_polynomial_scale_from_normalization", "prime_field_polynomial_scale_exists", "prime_field_polynomial_scale_bounded", "prime_field_convolution_coefficient_bounded", "prime_field_convolution_prefix_bounded", "prime_field_polynomial_convolution_bounded", "prime_field_polynomial_convolution_right_scale_exists", "prime_field_polynomial_scale_zero_value", "prime_field_polynomial_convolution_right_scale_zero", "prime_field_add_commutative", "prime_field_mod_of_equal", "prime_field_add_zero_right", "prime_field_add_zero_left", "prime_field_polynomial_append_shift_constant_add", "prime_field_polynomial_left_pad_exists", "prime_field_polynomial_append_shift_constant_decomposition_exists", "beta_sum_pointwise_mod_add", "prime_field_polynomial_add_entry", "polynomial_zero_extended_add_congruent", "polynomial_diagonal_term_left_add_congruent", "polynomial_diagonal_sum_left_add_congruent", "prime_field_convolution_coefficient_left_add", "prime_field_convolution_coefficient_right_append_add", "prime_field_polynomial_left_pad_index_cases", "prime_field_polynomial_left_pad_bounded", "prime_field_polynomial_add_from_normalization", "prime_field_polynomial_add_exists", "prime_field_polynomial_shift_scale_aligned_sum_exists", "prime_field_polynomial_add_bounded", "prime_field_convolution_prefix_left_add", "prime_field_polynomial_convolution_left_add", "prime_field_polynomial_power_index_before_padding", "prime_field_polynomial_left_pad_power_coefficient", "prime_field_polynomial_left_pad_equivalent", "polynomial_diagonal_left_prefix_transport", "prime_field_convolution_coefficient_prefix_transport", "prime_field_multiply_exists", "polynomial_diagonal_last_term_left_empty", "polynomial_diagonal_last_term_left_append", "polynomial_diagonal_prefix_left_transport", "polynomial_diagonal_sum_left_append", "prime_field_convolution_coefficient_append", "prime_field_add_functional", "prime_field_multiply_commutative", "prime_field_polynomial_constant_right_coefficient", "prime_field_polynomial_scale_to_constant_product", "polynomial_left_pad_zero_prefix", "polynomial_product_length_left_padding_right", "polynomial_zero_extended_left_pad_before", "polynomial_diagonal_term_left_padding_zero_right", "prime_field_convolution_coefficient_before_left_padding_right", "polynomial_zero_extended_left_pad_shift", "polynomial_diagonal_term_left_padding_right", "polynomial_diagonal_left_padding_right", "polynomial_zero_tail_natural_sum_invariant", "prime_field_convolution_coefficient_left_padding_right", "prime_field_polynomial_convolution_left_padding_nonempty_right", "prime_field_polynomial_convolution_left_padding_equivalent_right", "prime_field_polynomial_equivalent_implies_equal_same_length", "prime_field_polynomial_left_pad_transport", "prime_field_polynomial_equivalent_implies_left_pad", "prime_field_polynomial_add_left_pad_transport", "prime_field_polynomial_add_functional", "prime_field_polynomial_add_left_pad_output", "prime_field_polynomial_add_equivalent_congruent", "prime_field_polynomial_convolution_right_append_equivalent", "prime_field_polynomial_convolution_right_append_exists", "prime_field_polynomial_shift_equivalent_congruent", "prime_field_polynomial_convolution_shift_scale_aligned_equivalent", "prime_field_polynomial_shift_scale_aligned_congruent", "prime_field_polynomial_convolution_equivalent_congruent_right", "prime_field_polynomial_convolution_associativity_append_step", "prime_field_polynomial_nested_empty_right_equivalent", "prime_field_polynomial_convolution_associative_equivalent", "prime_field_polynomial_right_divides_from_product", "prime_field_polynomial_right_divides_divisor_bounded", "prime_field_polynomial_right_divides_dividend_bounded", "prime_field_polynomial_right_divides_equivalent_target", "prime_field_polynomial_convolution_empty", "prime_field_polynomial_right_divides_empty", "prime_field_polynomial_right_divides_equivalent_divisor", "prime_field_polynomial_right_divides_transitive", "polynomial_diagonal_left_unit_first_term", "polynomial_diagonal_left_unit_tail_term", "polynomial_diagonal_left_unit_natural_sum", "prime_field_convolution_coefficient_left_unit", "prime_field_polynomial_convolution_entry", "prime_field_polynomial_convolution_left_unit_equal", "prime_field_polynomial_convolution_left_unit_equivalent", "prime_field_polynomial_repeat_coefficients", "prime_field_polynomial_repeat_exists", "prime_field_polynomial_convolution_left_unit_exists", "prime_field_polynomial_right_divides_reflexive", "prime_field_polynomial_bounded_representative_at_length_exists", "prime_field_polynomial_common_representatives_same_length", "prime_field_polynomial_common_representatives_transport", "prime_field_polynomial_common_representatives_at_length_exists", "prime_field_polynomial_common_representatives_exists", "prime_field_polynomial_common_representatives_functional", "prime_field_polynomial_common_representatives_symmetric", "prime_field_polynomial_aligned_add_from_common", "prime_field_polynomial_aligned_add_bounded", "prime_field_polynomial_aligned_add_from_fixed", "prime_field_polynomial_aligned_add_transport", "prime_field_polynomial_add_commutative", "prime_field_polynomial_aligned_add_commutative", "prime_field_polynomial_aligned_add_functional", "prime_field_polynomial_aligned_add_exists", "prime_field_polynomial_add_transport", "prime_field_polynomial_aligned_add_realize", "prime_field_polynomial_subtract_recover_add", "prime_field_polynomial_aligned_subtract_from_fixed", "prime_field_polynomial_subtract_empty", "prime_field_negate_exists", "prime_field_add_exists", "prime_field_add_associative", "prime_field_subtract_exists", "prime_field_polynomial_subtract_exists", "prime_field_polynomial_aligned_subtract_exists", "prime_field_add_cancel_left", "prime_field_polynomial_subtract_entry", "prime_field_polynomial_subtract_functional", "prime_field_polynomial_subtract_from_add", "prime_field_polynomial_aligned_add_cancel_left", "prime_field_polynomial_add_associative", "prime_field_polynomial_aligned_add_associative", "prime_field_polynomial_aligned_subtract_functional", "prime_field_polynomial_suffix_bounded", "prime_field_polynomial_trim_output_coefficients", "prime_field_polynomial_zero_suffix_left_pad", "prime_field_polynomial_trim_left_pad", "prime_field_polynomial_trim_equivalent", "prime_field_polynomial_add_trim_aligned", "prime_field_convolution_prefix_empty_left_zero", "prime_field_polynomial_quotient_prefix_bounded", "polynomial_quotient_length_product", "prime_field_polynomial_quotient_proper_product", "prime_field_polynomial_division_coefficient_identity", "prime_field_polynomial_division_execution_aligned_identity", "prime_field_polynomial_left_distributive_products_exists", "prime_field_polynomial_aligned_convolution_left_add", "polynomial_diagonal_term_right_add_congruent", "polynomial_diagonal_sum_right_add_congruent", "prime_field_convolution_coefficient_right_add", "prime_field_convolution_prefix_right_add", "prime_field_polynomial_convolution_right_add", "prime_field_polynomial_right_distributive_products_exists", "polynomial_product_length_left_padding_left", "polynomial_diagonal_term_left_padding_zero_left", "prime_field_convolution_coefficient_before_left_padding_left", "polynomial_diagonal_term_left_padding_left", "polynomial_diagonal_left_padding_left", "polynomial_left_pad_natural_sum_invariant", "prime_field_convolution_coefficient_left_padding_left", "prime_field_polynomial_convolution_left_padding_nonempty_left", "prime_field_polynomial_convolution_left_padding_equivalent_left", "prime_field_polynomial_convolution_equivalent_congruent_left", "prime_field_polynomial_aligned_convolution_right_add", "polynomial_diagonal_left_constant_first_term", "polynomial_diagonal_left_constant_natural_sum", "prime_field_convolution_coefficient_left_constant", "prime_field_polynomial_left_constant_product_to_scale", "prime_field_polynomial_scale_to_left_constant_product", "prime_field_polynomial_left_constant_product_exists", "polynomial_quotient_length_bounds", "prime_field_polynomial_trim_represented_degree", "prime_field_polynomial_trim_bounded_degree", "prime_field_polynomial_trim_leading_source_nonzero", "prime_field_polynomial_trim_zero_prefix_cut_bound", "prime_field_polynomial_trim_zero_prefix_remainder_bound", "prime_field_subtract_equal_zero", "prime_field_polynomial_subtract_equal_entry_zero", "prime_field_polynomial_subtract_equal_zero", "prime_field_multiply_associative", "prime_field_multiply_one_right", "prime_field_multiply_one_left", "prime_field_polynomial_quotient_scalar_cancellation", "prime_field_polynomial_quotient_prefix_convolution_entry", "prime_field_polynomial_quotient_prefix_product_matches", "prime_field_polynomial_quotient_prefix_remainder_zero", "prime_field_polynomial_division_remainder_degree", "prime_field_polynomial_division_remainder_length_descent", "prime_field_polynomial_division_constant_remainder_empty", "prime_field_polynomial_scale_implies_right_divides", "prime_field_polynomial_scale_associative", "prime_field_polynomial_scale_one", "prime_field_polynomial_scale_transport", "prime_field_polynomial_inverse_scale", "prime_field_polynomial_monic_normalization_right_associates", "prime_field_polynomial_leading_zero_cut_exists", "prime_field_polynomial_suffix_exists", "prime_field_polynomial_trim_from_cut", "prime_field_polynomial_trim_exists", "prime_field_polynomial_trim_nonempty_degree_exists", "prime_field_inverse_exists", "prime_field_polynomial_monic_normalization_exists", "prime_field_polynomial_monic_normalization_bounded", "prime_field_polynomial_monic_normalization_entry", "prime_field_polynomial_monic_normalization_leading", "prime_field_polynomial_monic_normalization_monic", "prime_field_polynomial_normalized_right_associate_exists", "prime_field_polynomial_right_divides_aligned_add", "prime_field_polynomial_right_divides_aligned_subtract", "prime_field_polynomial_right_divides_left_product", "prime_field_polynomial_common_right_divisor_euclidean_transport", "prime_field_polynomial_division_execution_common_right_divisors", "prime_field_polynomial_euclidean_backward_coefficient_identity", "prime_field_polynomial_bezout_euclidean_backward", "prime_field_polynomial_division_execution_bezout_backward", "prime_field_polynomial_add_zero_right", "prime_field_polynomial_aligned_add_empty_right", "prime_field_polynomial_bezout_from_right_multiple", "prime_field_polynomial_bezout_equivalent_transport", "prime_field_polynomial_bezout_common_right_divisor", "prime_field_polynomial_division_remainder_bounded", "prime_field_polynomial_trim_length_bounds", "prime_field_polynomial_reduced_representative_exists", "prime_field_polynomial_gcd_bezout_empty_second", "prime_field_polynomial_gcd_bezout_equivalent_second", "prime_field_polynomial_gcd_bezout_division_backward", "polynomial_quotient_length_exists", "prime_field_polynomial_quotient_prefix_empty", "polynomial_zero_extended_entry_transport", "polynomial_diagonal_term_transport", "polynomial_diagonal_prefix_input_transport", "prime_field_convolution_coefficient_transport", "prime_field_polynomial_quotient_step_recode", "prime_field_polynomial_quotient_prefix_append", "prime_field_polynomial_quotient_prefix_exists", "prime_field_polynomial_division_quotient_data_exists", "prime_field_polynomial_subtract_bounded", "prime_field_polynomial_division_residual_data_exists", "prime_field_polynomial_division_execution_exists", "prime_field_polynomial_gcd_bezout_exists_up_to", "prime_field_polynomial_gcd_bezout_exists", "prime_field_polynomial_bezout_is_right_gcd", "prime_field_polynomial_normalized_gcd_bezout_exists", "prime_field_polynomial_nonzero_leading_equivalent_length_bound", "prime_field_polynomial_equivalent_represented_degrees_equal", "prime_field_polynomial_product_equivalent_nonzero_left_nonempty", "polynomial_product_length_positive_inputs", "polynomial_diagonal_term_leading", "prime_field_convolution_coefficient_leading", "prime_field_polynomial_convolution_leading_coefficient", "prime_field_nonzero_coprime", "prime_field_multiply_cancel_nonzero_left", "prime_field_multiply_zero_right", "prime_field_no_zero_divisors", "prime_field_polynomial_convolution_represented_degree", "prime_field_polynomial_right_divides_represented_factorization", "prime_field_polynomial_right_divides_represented_degree_bound", "prime_field_polynomial_monic_singleton_multiple_equivalent", "prime_field_polynomial_monic_represented_degree", "prime_field_polynomial_monic_equal_degree_right_divides_equivalent", "prime_field_polynomial_monic_right_associates_equivalent", "prime_field_polynomial_empty_right_divisor_implies_equivalent_zero", "prime_field_polynomial_normal_right_associates_equivalent", "prime_field_polynomial_normalized_gcd_equivalent_unique"),
        complete_specs_sha256="ae797cbf373142f63f7dd86af1f5ddad0909f4f1df755af6ad523a9c6c7e1d5d",
        complete_non_alpha_specs_sha256="72701944f71e8d93c55bcf29d27fc92ac616452801ab75c3e478df4d77df4c38",
        modules=("prime_field_polynomial_shift_candidate", "prime_field_polynomial_scalar_convolution_candidate", "prime_field_polynomial_append_candidate", "prime_field_polynomial_shift_equivalence_candidate", "prime_field_polynomial_associativity_step_candidate", "prime_field_polynomial_associativity_induction_candidate", "prime_field_polynomial_divisibility_candidate", "prime_field_polynomial_left_unit_candidate", "prime_field_polynomial_alignment_candidate", "prime_field_polynomial_aligned_add_candidate", "prime_field_polynomial_aligned_algebra_candidate", "prime_field_polynomial_euclidean_identity_candidate", "prime_field_polynomial_aligned_distributivity_candidate", "prime_field_polynomial_left_constant_candidate", "prime_field_polynomial_euclidean_normalization_candidate", "prime_field_polynomial_euclidean_transport_candidate", "prime_field_polynomial_bezout_backward_candidate", "prime_field_polynomial_gcd_bezout_laws_candidate", "prime_field_polynomial_gcd_existence_candidate", "prime_field_polynomial_gcd_uniqueness_candidate"),
        principal_pins=(("prime_field_polynomial_convolution_shift_right_exists", "0fc173b813282a7111d604245b1706a4c01c5bcf566812151810e9afe38f065d"), ("prime_field_polynomial_convolution_right_scale_exists", "5d0349367decc3084471726b73a77617d49f484cf31191bb78effbc434167156"), ("prime_field_polynomial_convolution_right_scale_zero", "fd6d04fd88ff9f594f7ee27de04486c1932ce5de30b6030b6b9b18cb547511ef"), ("prime_field_convolution_coefficient_right_append_add", "a11e1f29b31ae9076959706b6b5d0813689194a2ab57a1a4e879e6a6c3ad69bd"), ("prime_field_polynomial_convolution_right_append_exists", "0ef69b8524dd48c1a9805f158e9eff25c41e421b85378b96b51b7c63bd89f087"), ("prime_field_polynomial_right_divides_dividend_bounded", "a1f28266b77ee02c24747cf96ca7234d9d13bc3c46d38b2bb6b2f805c1538278"), ("prime_field_polynomial_right_divides_reflexive", "d8f3531eb2f6d2fb37e8ee936807a66a7dc1e49b71c95c7c7023c7964fc03852"), ("prime_field_polynomial_aligned_subtract_from_fixed", "3122386d4be93f7e4bca06128ec30ae0e3334dd046f69bb995b602499ae49804"), ("prime_field_polynomial_aligned_subtract_functional", "1025f30027f56856f3370a9d951e7ed68e7b83c785a30164ee5a868824667813"), ("prime_field_polynomial_left_constant_product_to_scale", "c93e29c84d993f933394eb2fc82600d8f3d88f50a06a25ee9d6dc69e6b2141fe"), ("prime_field_polynomial_division_constant_remainder_empty", "ac7f30f0841995aa9fe25e0546803c6bcf4aab7c09fa337a4c61eafa6f196a9b"), ("prime_field_polynomial_normalized_gcd_bezout_exists", "d97cbfa3dc334fa5bcf7b9bd92bde2e117b29595864a9cddb093ffe842832463"), ("prime_field_polynomial_normalized_gcd_equivalent_unique", "302df17d7792e85eb95dc25ff3b82ef61c84f67da66a886c1ef383f1115ef7a7"), ("prime_field_polynomial_bezout_is_right_gcd", "91a89630be8631cd892a7e0dd57bc4a36c2f3a3b734b16f12390124493a0ab43")),
    ),
    ResearchFamily(
        slug="congruence-arithmetic",
        research_checkpoint_slug="working-linear-congruence12",
        artifact="research/arithmetic-library/artifacts/linear-congruence-classification-proof-bundle-v1.json",
        artifact_bytes=542092,
        artifact_sha256="983051afddc637a4e033546b8f3ddb8dc0ac22aa996b4e28b3822be8895576ad",
        count=12,
        specs_sha256="b1128492a1dd801ec81f63a39f586f733e95b79a1d2a19d33bb0363130d560c8",
        names_sha256="fa61dfc9de450ee1609d02d7de06cb0292fa5de682e306b444807bb4926d2d8c",
        edge_count=61,
        command_count=658,
        rfc="research/arithmetic-library/linear-congruence-classification-rfc-v1.md",
        owned_names=("mod_eq_cancel_gcd_cofactor", "linear_congruence_solution_class_iff_reduced_modulus", "linear_congruence_reduced_representative_exists", "linear_congruence_progression_bound_iff", "linear_congruence_bounded_residue_parametrized", "linear_congruence_bounded_parameter_unique", "linear_congruence_bounded_solutions_parametrized", "linear_congruence_exact_bounded_enumeration_exists", "linear_congruence_zero_modulus_nonzero_coefficient_unique", "linear_congruence_zero_modulus_zero_coefficient_iff", "linear_congruence_modulus_one_bounded_iff_zero", "fermat_little_all_inputs"),
        principal_roots=("linear_congruence_exact_bounded_enumeration_exists", "linear_congruence_zero_modulus_nonzero_coefficient_unique", "linear_congruence_zero_modulus_zero_coefficient_iff", "linear_congruence_modulus_one_bounded_iff_zero", "fermat_little_all_inputs"),
        theorem_count=214,
        root_names=("linear_congruence_exact_bounded_enumeration_exists", "linear_congruence_zero_modulus_nonzero_coefficient_unique", "linear_congruence_zero_modulus_zero_coefficient_iff", "linear_congruence_modulus_one_bounded_iff_zero", "fermat_little_all_inputs"),
        node_count=215,
        dependency_edges=642,
        bundle_edges=647,
        body_nodes=13079,
        ordered_cone_names_sha256="d8f0f89555c5808404bee144e0372f145b6f696e0a0030399c52dc7e193fae90",
        ordered_cone_names=("zero_add", "add_succ_left", "add_comm", "add_assoc", "mul_zero_left", "mul_succ_left", "mul_comm", "mul_add", "mul_assoc", "one_mul", "mul_one", "add_mul", "succ_ne_zero", "succ_injective", "le_refl", "le_trans", "no_succ_add_fixed", "le_total", "add_eq_zero_right", "mul_eq_zero", "zero_or_succ", "nonzero_is_succ", "mul_congr", "add_right_cancel", "add_left_cancel", "zero_le", "le_succ_self", "le_zero", "one_le_of_ne_zero", "le_add_left", "le_add_right", "add_le_add_right", "add_le_add_left", "succ_le_succ", "le_of_succ_le_succ", "le_succ", "lt_to_le", "lt_irrefl_expanded", "le_eq_or_lt", "lt_of_lt_of_le", "le_or_lt", "lt_trichotomy", "lt_not_le", "lt_not_eq_add_middle", "mul_le_mul_right", "division_remainder_succ", "division_remainder_exists", "positive_quotient_gap_impossible", "division_remainder_unique", "add_eq_zero_left", "mul_eq_one_components", "mul_ne_zero", "mul_left_cancel_nonzero", "multiple_zero", "multiple_refl", "multiple_mul_right", "multiple_mul_left", "multiple_trans", "divisor_le_nonzero", "divisor_one", "multiple_antisymm", "factor_difference", "divides_remainder", "divides_linear_step", "is_gcd_zero_right", "is_gcd_symm", "is_gcd_dvd_left", "is_gcd_dvd_right", "is_gcd_greatest", "is_gcd_unique", "is_gcd_euclid_forward", "gcd_exists_up_to", "gcd_exists_relational", "coprime_symm", "coprime_one_left", "is_gcd_one_to_coprime", "add_permute_outer", "balanced_bezout_euclid_step", "gcd_balanced_bezout_exists_up_to", "gcd_balanced_bezout_exists", "balanced_combination_scale_right", "common_divisor_divides_balanced_result", "coprime_balanced_bezout", "gauss_coprime_cancel", "eq_decidable", "prime_nonzero", "prime_divisor_eq_one_or_self", "euclid_prime_dvd_product", "mod_eq_refl", "mod_eq_symm", "mod_eq_trans", "mod_eq_add", "mod_eq_mul_right", "mod_eq_mul_left", "mod_eq_mul", "remainder_decomposition_to_mod_eq", "mod_eq_bounded_unique", "mod_eq_to_remainder_decomposition", "beta_modulus_nonzero", "beta_at_self_of_bound", "beta_at_exists", "beta_at_unique", "beta_at_of_mod_eq_bound", "dvd_to_mod_zero", "bezout_mod_left", "bezout_mod_right", "mod_eq_predecessor_cancel", "binary_crt", "beta_modulus_coprime_base", "common_divisor_beta_moduli_divides_gap_times_c", "beta_moduli_coprime_of_gap_dvd", "bounded_common_multiple_step", "bounded_common_multiple_exists", "beta_moduli_coprime_of_lt_bounded_common_multiple", "beta_moduli_pairwise_coprime_bounded", "coprime_mul_left", "mod_eq_of_mod_eq_multiple", "binary_crt_fold_step", "right_factor_divides_product", "beta_value_le_code", "base_le_beta_modulus", "le_scaled_nonzero", "scaled_bounded_common_multiple", "beta_value_lt_scaled_base", "new_value_lt_scaled_base", "beta_exclusive_accumulated_product_step", "beta_exclusive_recode_congruence_step", "beta_exclusive_recode_invariant_step", "bounded_beta_exclusive_recode_invariant", "beta_prefix_extend", "beta_prefix_product_trace_exists", "beta_product_exists", "beta_product_functional", "beta_product_zero", "beta_product_succ_decompose", "beta_product_transport_prefix", "beta_repeat_entry_eq", "pow_zero", "pow_successor_decompose", "beta_range_empty", "beta_range_succ_extend", "beta_range_exists", "beta_range_entry_eq", "prime_coprime_or_divides", "prime_not_divides_coprime", "coprime_balanced_mod_inverse", "coprime_mod_inverse", "mod_eq_cancel_coprime", "prime_mod_cancel", "factorial_exists", "finite_surjective_zero", "finite_injective_prefix_succ", "finite_lt_succ_eq_or_lt", "finite_bounded_entry_lt", "beta_prefix_replace_exists", "beta_prefix_swap_last_from_entries", "beta_prefix_swap_last_reflect", "finite_swap_last_bounded", "finite_swap_last_injective", "finite_swap_last_surjective_back", "finite_contains_decidable", "finite_bounded_prefix_without_top", "finite_bounded_last_succ", "finite_surjective_succ_intro", "finite_last_is_top_from_prefix_surjective", "finite_surjective_succ_from_prefix", "finite_no_top_successor_gate", "finite_bounded_injective_surjective", "beta_product_replace_balance", "beta_product_swap_last_invariant", "finite_fixed_last_prefix_bounded", "beta_reindex_alignment_swap_last", "mod_eq_zero_iff_eq", "mod_eq_scale", "is_gcd_quotients_coprime_nonzero", "mod_eq_common_remainder_decomposition", "crt_scaled_common_remainder_lift", "generalized_binary_crt_sufficient_nonzero", "generalized_binary_crt_sufficient_zero_left", "generalized_binary_crt_sufficient_zero_right", "generalized_binary_crt_sufficient", "beta_product_pointwise_scale_mod", "beta_product_reindex_fixed_last", "beta_product_permutation_invariant", "beta_product_pointwise_coprime", "prime_mul_index_map_exists_up_to", "beta_successor_lift_exists", "fermat_index_map_bounded", "prime_mul_index_map_injective", "beta_range_one_entry_eq_succ", "beta_successor_range_reindex_aligned", "beta_successor_range_scale_mod", "prime_mul_residue_reindex_exists", "prime_mul_residue_product_balance", "prime_range_product_coprime", "fermat_predecessor_exponent_mod_one", "mod_eq_unscale_nonzero", "linear_congruence_zero_residue_divides", "linear_congruence_gcd_divisibility_constructs_solution", "crt_mod_one_universal", "finite_add_le_add", "finite_add_lt_of_lt_of_le", "mod_eq_cancel_gcd_cofactor", "linear_congruence_solution_class_iff_reduced_modulus", "linear_congruence_reduced_representative_exists", "linear_congruence_progression_bound_iff", "linear_congruence_bounded_residue_parametrized", "linear_congruence_bounded_parameter_unique", "linear_congruence_bounded_solutions_parametrized", "linear_congruence_exact_bounded_enumeration_exists", "linear_congruence_zero_modulus_nonzero_coefficient_unique", "linear_congruence_zero_modulus_zero_coefficient_iff", "linear_congruence_modulus_one_bounded_iff_zero", "fermat_little_all_inputs"),
        complete_specs_sha256="8d2b30a02f7103507dba33c635d3f3728e6aedd7451b0ec6a7c78b67111d8094",
        complete_non_alpha_specs_sha256="b1128492a1dd801ec81f63a39f586f733e95b79a1d2a19d33bb0363130d560c8",
        modules=("linear_congruence_classification_candidate",),
        principal_pins=(("linear_congruence_exact_bounded_enumeration_exists", "489b9733a5124b9e9e82074322f4aa82b37cb54e89cc0dfa508658546c84a5c4"), ("linear_congruence_zero_modulus_nonzero_coefficient_unique", "f94cdd4b83fb5b7da9fa6b6694f4b8259ff3d9e48ec90b2b3cdd704f1b5adf59"), ("linear_congruence_zero_modulus_zero_coefficient_iff", "59355ce5396903898f8393dcf5602f96bb91c163b4c0a55d7c2b07b21e3c03a5"), ("linear_congruence_modulus_one_bounded_iff_zero", "924f0bbdbd0c7fa3633fb0b47acd00510e6d07be5e6ebf292e22c9aef17042f3"), ("fermat_little_all_inputs", "6a1162d7a8f6279242317f8ac7b9e93ca4f53d4dcf5563ca4a048d8dec75bb23")),
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
_FAMILY_FIELDS = ("slug", "research_checkpoint_slug", "artifact", "artifact_bytes", "artifact_sha256", "count", "specs_sha256", "names_sha256", "edge_count", "command_count", "rfc", "owned_names", "principal_roots", "theorem_count", "root_names", "node_count", "dependency_edges", "bundle_edges", "body_nodes", "ordered_cone_names_sha256", "ordered_cone_names", "complete_specs_sha256", "complete_non_alpha_specs_sha256", "modules", "principal_pins")


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
            REGISTRATION_COMPLETE is not True
            or type(FACTORIES) is not tuple or type(FAMILIES) is not tuple
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
            raise ResearchClosureError("the research-v34 metadata seal changed")
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
                raise ResearchClosureError("invalid research-v34 factory metadata")
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
                or type(family.ordered_cone_names) is not tuple
                or len(family.ordered_cone_names) != family.theorem_count
                or len(set(family.ordered_cone_names)) != family.theorem_count
                or sha256("\n".join(family.ordered_cone_names).encode()).hexdigest()
                != family.ordered_cone_names_sha256
                or not set(family.principal_roots) <= set(family.owned_names)
                or tuple(name for name, _ in family.principal_pins) != family.principal_roots
                or not family.artifact.startswith("research/arithmetic-library/artifacts/")
                or Path(family.artifact).is_absolute() or ".." in Path(family.artifact).parts
                or tuple(owner.module for owner in FACTORIES if owner.campaign == family.slug)
                != family.modules
            ):
                raise ResearchClosureError("invalid research-v34 family metadata")
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, ResearchClosureError):
            raise
        raise ResearchClosureError("the research-v34 metadata is malformed") from error


def research_family(slug: str) -> ResearchFamily:
    validate_research_metadata()
    if type(slug) is not str or slug not in FAMILY_BY_SLUG:
        raise ResearchClosureError(f"unknown research-v34 family {slug!r}")
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
        raise ResearchClosureError("a research-v34 proof source must be a filesystem path")
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
        raise ResearchClosureError("the full research-v34 specification inventory changed")
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
        from . import editions_v33
        parent_specs = editions_v33.ALPHA_CHECKED_SPECS
    if (type(parent_specs) is not tuple
            or len(parent_specs) != PARENT_ALPHA_V33_COUNT
            or any(type(row) is not TheoremSpec for row in parent_specs)
            or _specs_digest(parent_specs) != PARENT_ALPHA_V33_SPECS_SHA256):
        raise ResearchClosureError("the exact immutable Alpha-v33 parent syntax changed")
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
    # Traversal determines the exact closed set, not serialized node identity.
    # The immutable artifact retains the original v30-plus-frontier assembler
    # order, independently reconciled against every actual target/premise.
    included: set[str] = set()
    active: set[str] = set()
    ordered: list[TheoremSpec] = []

    def visit(name: str) -> None:
        if name not in table or name in active:
            raise ResearchClosureError('unknown or cyclic actual prerequisite: ' + name)
        if name in included:
            return
        if len(active) >= DEFAULT_BUNDLE_LIMITS.max_nodes:
            raise ResearchClosureError('actual dependency traversal exceeds the bundle bound')
        active.add(name)
        row = table[name]
        for dependency in row.dependencies:
            visit(dependency)
        active.remove(name)
        included.add(name)
        ordered.append(row)

    for name in family.owned_names:
        visit(name)
    if (len(family.ordered_cone_names) != len(included)
            or set(family.ordered_cone_names) != included):
        raise ResearchClosureError("the literal artifact order differs from its complete source cone")
    selected = tuple(table[name] for name in family.ordered_cone_names)
    earlier: set[str] = set()
    for row in selected:
        if not set(row.dependencies) <= earlier:
            raise ResearchClosureError("the literal artifact order is not dependency-first")
        earlier.add(row.name)
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
        or _specs_digest(selected) != family.complete_specs_sha256
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
