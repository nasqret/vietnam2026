"""Exact browser-safe v33 providers for 121 completed polynomial research theorems.

The single complete artifact retains its exact working-checkpoint bytes.
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


PARENT_ALPHA_V32_COUNT = 3971
PARENT_ALPHA_V32_SPECS_SHA256 = "2d9f09411a511a28dc3bfc9f1175631bafde3c9a08f27521a8f80e0c7aa43736"
PARENT_ALPHA_V32_IDENTITY_SHA256 = "2821b3ef1e5761283af9c015b05c0a02ede073554412585a1ff5ead455269939"
PARENT_ALPHA_V32_ENROLLMENT_SHA256 = "911df25bac9987e73d3313c90bdd0602e9e7e6f3f4af00c81701d35b14268cb5"
EXPECTED_RESEARCH_COUNT = 121
EXPECTED_RESEARCH_EDGE_COUNT = 461
EXPECTED_RESEARCH_COMMAND_COUNT = 9068
EXPECTED_RESEARCH_NAMES_SHA256 = "80db0f58a3e58fa9edd5a8b2cc4a11314e262cdeb52a79955a63967e9dc674cc"
EXPECTED_RESEARCH_SPECS_SHA256 = "b1e2106738d15dc3714dd1a57f88fedec492692259b6009e4edccc49de439769"
EXPECTED_RESEARCH_FAMILY_COUNT = 1
EXPECTED_RESEARCH_FACTORY_COUNT = 8
EXPECTED_RESEARCH_METADATA_SHA256 = "ea9a09d907d3010a8f32e3efc54c1d2c171b074a87a140953c06f626071fdce6"
# Parent specification and metadata identities fail closed until measured from
# the unchanged current parent and these exact canonical factories.
# The existing source-input and proof-bundle ceilings, not enlarged limits.
MAX_SOURCE_BYTES = 2 * 1024 * 1024

FACTORIES = (
    ResearchFactory(
        campaign="polynomial-euclidean-division",
        module="prime_field_polynomial_convolution_triangular_candidate",
        factory="make_prime_field_polynomial_convolution_triangular_candidate_theorems",
        rfc="prime-field-polynomial-euclidean-division-rfc-v1.md",
        source_bytes=16677,
        source_sha256="d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f",
        count=8,
        specs_sha256="7395ad6a1ab86170680644dd40c50e35a34542b4f42bd36b77b8db16e12efb71",
        test_filename="test_campaign_research_v33_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-euclidean-division",
        module="prime_field_polynomial_representation_candidate",
        factory="make_prime_field_polynomial_representation_candidate_theorems",
        rfc="prime-field-polynomial-euclidean-division-rfc-v1.md",
        source_bytes=42623,
        source_sha256="fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a",
        count=30,
        specs_sha256="0dcf4865d92f32c353c21094965eea04cdf38bf56830bb6fe8246aa5702c2c3f",
        test_filename="test_campaign_research_v33_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-euclidean-division",
        module="prime_field_polynomial_division_candidate",
        factory="make_prime_field_polynomial_division_candidate_theorems",
        rfc="prime-field-polynomial-euclidean-division-rfc-v1.md",
        source_bytes=47986,
        source_sha256="edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2",
        count=25,
        specs_sha256="b36e279dda4229d5079fda430de9e195ec7b19cff10547a2d1d6ad160b41a050",
        test_filename="test_campaign_research_v33_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-euclidean-division",
        module="prime_field_polynomial_distributivity_candidate",
        factory="make_prime_field_polynomial_distributivity_candidate_theorems",
        rfc="prime-field-polynomial-euclidean-division-rfc-v1.md",
        source_bytes=26118,
        source_sha256="a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86",
        count=18,
        specs_sha256="1db670ecc1df93a157c40fe0f257a059db15644db4e6a2da65cc5823ca8d74e5",
        test_filename="test_campaign_research_v33_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-euclidean-division",
        module="prime_field_polynomial_division_uniqueness_candidate",
        factory="make_prime_field_polynomial_division_uniqueness_candidate_theorems",
        rfc="prime-field-polynomial-euclidean-division-rfc-v1.md",
        source_bytes=23258,
        source_sha256="6a9d9ebe1f72202743e5df2c069b9aa367fdb3d61108f1d9354cdc9276ab2d15",
        count=9,
        specs_sha256="41bb0ad58b6e7ef3cc6fefba62bcc75ae0fe18a10fb87019905cb43e810ae1da",
        test_filename="test_campaign_research_v33_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-euclidean-division",
        module="prime_field_polynomial_convolution_padding_candidate",
        factory="make_prime_field_polynomial_convolution_padding_candidate_theorems",
        rfc="prime-field-polynomial-euclidean-division-rfc-v1.md",
        source_bytes=39740,
        source_sha256="2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007",
        count=23,
        specs_sha256="5bd7b23cf69bfd35fbf99c47da09a0751c3e267b8cdc31a078b2b65b99f5d619",
        test_filename="test_campaign_research_v33_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-euclidean-division",
        module="prime_field_polynomial_equivalence_candidate",
        factory="make_prime_field_polynomial_equivalence_candidate_theorems",
        rfc="prime-field-polynomial-euclidean-division-rfc-v1.md",
        source_bytes=10469,
        source_sha256="929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373",
        count=5,
        specs_sha256="2fe70cc2ff26a6938768fcbdb661c84b2ad17e19dd7d9551689f3f4ea39da273",
        test_filename="test_campaign_research_v33_closure.py",
    ),
    ResearchFactory(
        campaign="polynomial-euclidean-division",
        module="prime_field_polynomial_convolution_congruence_candidate",
        factory="make_prime_field_polynomial_convolution_congruence_candidate_theorems",
        rfc="prime-field-polynomial-euclidean-division-rfc-v1.md",
        source_bytes=8183,
        source_sha256="effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70",
        count=3,
        specs_sha256="b0da9dd22a52c42045fd22ac189fb9d7fc92365527818f5a61e0f4a71d1be7e6",
        test_filename="test_campaign_research_v33_closure.py",
    ),
)

RESEARCH_FAMILIES = (
    ResearchFamily(
        slug="polynomial-euclidean-division",
        research_checkpoint_slug="working-polynomial-equivalence121",
        artifact="research/arithmetic-library/artifacts/prime-field-polynomial-euclidean-division-proof-bundle-v1.json",
        artifact_bytes=2449379,
        artifact_sha256="6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf",
        count=121,
        specs_sha256="b1e2106738d15dc3714dd1a57f88fedec492692259b6009e4edccc49de439769",
        names_sha256="80db0f58a3e58fa9edd5a8b2cc4a11314e262cdeb52a79955a63967e9dc674cc",
        edge_count=461,
        command_count=9068,
        rfc="research/arithmetic-library/prime-field-polynomial-euclidean-division-rfc-v1.md",
        owned_names=("polynomial_diagonal_left_prefix_transport", "polynomial_diagonal_prefix_left_transport", "prime_field_convolution_coefficient_prefix_transport", "prime_field_convolution_coefficient_append_invariant", "polynomial_diagonal_last_term_left_empty", "polynomial_diagonal_last_term_left_append", "polynomial_diagonal_sum_left_append", "prime_field_convolution_coefficient_append", "prime_field_polynomial_power_index_bound", "prime_field_polynomial_left_pad_index_cases", "prime_field_polynomial_power_index_before_padding", "prime_field_polynomial_power_coefficient_exists", "prime_field_polynomial_power_coefficient_functional", "prime_field_polynomial_power_coefficient_transport", "prime_field_polynomial_equivalent_symmetric", "prime_field_polynomial_equivalent_transitive", "prime_field_polynomial_equal_implies_equivalent", "prime_field_polynomial_equivalent_implies_equal_same_length", "prime_field_polynomial_left_pad_zero", "prime_field_polynomial_left_pad_exists", "prime_field_polynomial_left_pad_entry", "prime_field_polynomial_left_pad_bounded", "prime_field_polynomial_left_pad_functional", "prime_field_polynomial_zero_suffix_left_pad", "prime_field_polynomial_trim_left_pad", "prime_field_polynomial_left_pad_power_coefficient", "prime_field_polynomial_left_pad_equivalent", "prime_field_polynomial_trim_equivalent", "prime_field_polynomial_left_pad_transport", "prime_field_polynomial_add_left_pad_transport", "prime_field_polynomial_subtract_left_pad_transport", "prime_field_polynomial_scale_left_pad_transport", "prime_field_polynomial_zero_power_coefficient", "prime_field_polynomial_zero_prefix_equivalent_empty", "prime_field_polynomial_constant_right_coefficient", "prime_field_polynomial_constant_product_to_scale", "prime_field_polynomial_scale_to_constant_product", "prime_field_polynomial_inverse_scale", "prime_field_polynomial_quotient_scalar_cancellation", "prime_field_polynomial_quotient_step_recode", "prime_field_polynomial_quotient_prefix_empty", "prime_field_polynomial_quotient_prefix_restrict", "prime_field_polynomial_quotient_prefix_entry", "prime_field_polynomial_quotient_prefix_bounded", "prime_field_polynomial_quotient_prefix_append", "prime_field_polynomial_quotient_prefix_exists", "prime_field_polynomial_quotient_prefix_convolution_entry", "prime_field_polynomial_quotient_prefix_product_matches", "prime_field_polynomial_quotient_prefix_remainder_zero", "polynomial_quotient_length_exists", "polynomial_quotient_length_bounds", "prime_field_polynomial_trim_zero_prefix_cut_bound", "prime_field_polynomial_trim_zero_prefix_remainder_bound", "prime_field_polynomial_trim_bounded_degree", "prime_field_polynomial_division_quotient_data_exists", "prime_field_polynomial_division_residual_data_exists", "prime_field_polynomial_division_execution_exists", "prime_field_polynomial_division_remainder_degree", "prime_field_polynomial_division_exists_with_remainder_bound", "polynomial_quotient_length_product", "prime_field_polynomial_quotient_proper_product", "prime_field_convolution_prefix_empty_left_zero", "prime_field_polynomial_division_coefficient_identity", "beta_sum_pointwise_mod_add", "polynomial_zero_extended_add_congruent", "polynomial_diagonal_term_left_add_congruent", "polynomial_diagonal_term_right_add_congruent", "polynomial_diagonal_sum_left_add_congruent", "polynomial_diagonal_sum_right_add_congruent", "prime_field_convolution_coefficient_left_add", "prime_field_convolution_coefficient_right_add", "prime_field_convolution_prefix_left_add", "prime_field_convolution_prefix_right_add", "prime_field_convolution_prefix_left_subtract", "prime_field_convolution_prefix_right_subtract", "prime_field_polynomial_convolution_left_add", "prime_field_polynomial_convolution_right_add", "prime_field_polynomial_convolution_left_subtract", "prime_field_polynomial_convolution_right_subtract", "prime_field_polynomial_left_distributive_products_exists", "prime_field_polynomial_right_distributive_products_exists", "prime_field_polynomial_quotient_step_functional", "prime_field_polynomial_quotient_step_prefix_functional", "prime_field_polynomial_quotient_prefix_functional", "polynomial_quotient_length_functional", "prime_field_polynomial_trim_input_transport", "prime_field_polynomial_division_quotient_data_functional", "prime_field_polynomial_division_residual_data_functional", "prime_field_polynomial_division_execution_functional", "prime_field_polynomial_division_execution_exists_unique", "polynomial_zero_extended_left_pad_shift", "polynomial_zero_extended_left_pad_before", "polynomial_left_pad_zero_prefix", "polynomial_left_pad_natural_sum_invariant", "polynomial_zero_tail_natural_sum_invariant", "polynomial_diagonal_term_left_padding_left", "polynomial_diagonal_term_left_padding_right", "polynomial_diagonal_term_left_padding_zero_left", "polynomial_diagonal_term_left_padding_zero_right", "polynomial_diagonal_left_padding_left", "polynomial_diagonal_left_padding_right", "prime_field_convolution_coefficient_left_padding_left", "prime_field_convolution_coefficient_left_padding_right", "prime_field_convolution_coefficient_before_left_padding_left", "prime_field_convolution_coefficient_before_left_padding_right", "polynomial_product_length_left_padding_left", "polynomial_product_length_left_padding_right", "prime_field_polynomial_convolution_left_padding_nonempty_left", "prime_field_polynomial_convolution_left_padding_nonempty_right", "prime_field_polynomial_convolution_left_padding_equivalent_left", "prime_field_polynomial_convolution_left_padding_equivalent_right", "prime_field_polynomial_convolution_both_left_paddings_equivalent", "prime_field_polynomial_convolution_both_left_paddings_exists", "prime_field_polynomial_equivalent_implies_left_pad", "prime_field_polynomial_add_left_pad_output", "prime_field_polynomial_subtract_left_pad_output", "prime_field_polynomial_add_equivalent_congruent", "prime_field_polynomial_subtract_equivalent_congruent", "prime_field_polynomial_convolution_equivalent_congruent_left", "prime_field_polynomial_convolution_equivalent_congruent_right", "prime_field_polynomial_convolution_equivalent_congruent"),
        principal_roots=("prime_field_polynomial_division_execution_functional", "prime_field_polynomial_division_execution_exists_unique", "prime_field_polynomial_convolution_both_left_paddings_equivalent", "prime_field_polynomial_convolution_both_left_paddings_exists", "prime_field_polynomial_equivalent_implies_left_pad", "prime_field_polynomial_add_equivalent_congruent", "prime_field_polynomial_subtract_equivalent_congruent", "prime_field_polynomial_convolution_equivalent_congruent"),
        theorem_count=376,
        root_names=("prime_field_convolution_coefficient_append_invariant", "prime_field_polynomial_equal_implies_equivalent", "prime_field_polynomial_left_pad_zero", "prime_field_polynomial_left_pad_entry", "prime_field_polynomial_left_pad_functional", "prime_field_polynomial_trim_equivalent", "prime_field_polynomial_scale_left_pad_transport", "prime_field_polynomial_constant_product_to_scale", "prime_field_polynomial_scale_to_constant_product", "prime_field_polynomial_inverse_scale", "prime_field_polynomial_division_exists_with_remainder_bound", "prime_field_polynomial_division_coefficient_identity", "prime_field_polynomial_convolution_left_subtract", "prime_field_polynomial_convolution_right_subtract", "prime_field_polynomial_left_distributive_products_exists", "prime_field_polynomial_right_distributive_products_exists", "prime_field_polynomial_division_execution_exists_unique", "prime_field_polynomial_convolution_both_left_paddings_exists", "prime_field_polynomial_add_equivalent_congruent", "prime_field_polynomial_subtract_equivalent_congruent", "prime_field_polynomial_convolution_equivalent_congruent"),
        node_count=377,
        dependency_edges=1050,
        bundle_edges=1071,
        body_nodes=30527,
        ordered_cone_names_sha256="fd1566ec5f1ab98589092623d9e7009923e6da124caa9c247eed72e48deb01ed",
        complete_non_alpha_specs_sha256="b1e2106738d15dc3714dd1a57f88fedec492692259b6009e4edccc49de439769",
        modules=("prime_field_polynomial_convolution_triangular_candidate", "prime_field_polynomial_representation_candidate", "prime_field_polynomial_division_candidate", "prime_field_polynomial_distributivity_candidate", "prime_field_polynomial_division_uniqueness_candidate", "prime_field_polynomial_convolution_padding_candidate", "prime_field_polynomial_equivalence_candidate", "prime_field_polynomial_convolution_congruence_candidate"),
        principal_pins=(("prime_field_polynomial_division_execution_functional", "b14ad2149cd34386887dcac50cb06b7df7014500b1ab918fac7967976b6042fe"), ("prime_field_polynomial_division_execution_exists_unique", "0ac4c1f5ca519e7db039365ff2a703f8772e22e58376d4c55a3f7777e08565fc"), ("prime_field_polynomial_convolution_both_left_paddings_equivalent", "fbefa6c478ac7028d2c60d742799660f05d010578ce4ed30b0f72f6f0af237d6"), ("prime_field_polynomial_convolution_both_left_paddings_exists", "b79ee5e0362c752f6b0189437e25cacc49e7060037adf8837f3105db832f8ffd"), ("prime_field_polynomial_equivalent_implies_left_pad", "e9b137b8b2e2d502cb4f5405a4cb90a0abcbb50de9a0df45ff51d5127761a25c"), ("prime_field_polynomial_add_equivalent_congruent", "847a60b511d446febdc15c56231f1368a7993172939945b7b99ab297cb65c4fb"), ("prime_field_polynomial_subtract_equivalent_congruent", "b073daede7886ec70b68c11665fc2f70154db2696cd613e542d1e22900e5f2a3"), ("prime_field_polynomial_convolution_equivalent_congruent", "d984fe3c378d4d4b02941d6f3a126324a2c7c26bf47f4d8ee7c37b2e55404446")),
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
            raise ResearchClosureError("the research-v33 metadata seal changed")
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
                raise ResearchClosureError("invalid research-v33 factory metadata")
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
                raise ResearchClosureError("invalid research-v33 family metadata")
    except (AttributeError, KeyError, TypeError, ValueError) as error:
        if isinstance(error, ResearchClosureError):
            raise
        raise ResearchClosureError("the research-v33 metadata is malformed") from error


def research_family(slug: str) -> ResearchFamily:
    validate_research_metadata()
    if type(slug) is not str or slug not in FAMILY_BY_SLUG:
        raise ResearchClosureError(f"unknown research-v33 family {slug!r}")
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
        raise ResearchClosureError("a research-v33 proof source must be a filesystem path")
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
        raise ResearchClosureError("the full research-v33 specification inventory changed")
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
        from . import editions_v32
        parent_specs = editions_v32.ALPHA_CHECKED_SPECS
    if (type(parent_specs) is not tuple
            or len(parent_specs) != PARENT_ALPHA_V32_COUNT
            or any(type(row) is not TheoremSpec for row in parent_specs)
            or _specs_digest(parent_specs) != PARENT_ALPHA_V32_SPECS_SHA256):
        raise ResearchClosureError("the exact immutable Alpha-v32 parent syntax changed")
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
