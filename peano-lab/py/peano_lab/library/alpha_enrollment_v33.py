"""Artifact-free exact enrollment of the complete constructive polynomial execution/equivalence campaign.

The old research checkpoints remain immutable. This additive inventory is
eligible for checked Alpha use only through the new complete-body provider;
neither a saved research receipt nor a metadata digest is proof authority.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Mapping

from . import editions_v32 as v32
from .campaign_research_v33_closure import (
    FACTORIES, FAMILIES, FRONTIER_NEW_NAMES,
    EXPECTED_RESEARCH_METADATA_SHA256,
    PARENT_ALPHA_V32_COUNT, PARENT_ALPHA_V32_SPECS_SHA256,
    PARENT_ALPHA_V32_ENROLLMENT_SHA256, PARENT_ALPHA_V32_IDENTITY_SHA256,
    research_specs, validate_research_metadata, _specs_digest,
)
from .theorems import TheoremSpec, _closed_formula


class AlphaV33EnrollmentError(ValueError):
    """The frozen parent, reviewed factory or additive dependency DAG changed."""


class FrontierV33Campaign(str, Enum):
    POLYNOMIAL_EUCLIDEAN_DIVISION = "polynomial-euclidean-division"


@dataclass(frozen=True, slots=True)
class AlphaV33Enrollment:
    parent_entries: tuple[v32.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV33Campaign]


FRONTIER_V33_EXPECTED_COUNT = 121
FRONTIER_V33_EXPECTED_EDGE_COUNT = 461
FRONTIER_V33_EXPECTED_COMMAND_COUNT = 9068
FRONTIER_V33_EXPECTED_NAMES_SHA256 = "80db0f58a3e58fa9edd5a8b2cc4a11314e262cdeb52a79955a63967e9dc674cc"
FRONTIER_V33_EXPECTED_SPECS_SHA256 = "b1e2106738d15dc3714dd1a57f88fedec492692259b6009e4edccc49de439769"
EXPECTED_FACTORY_METADATA_SHA256 = "0a074e7e1a39ecee6bc22863fdcab4fdd3948bad1abb0c752d536a81cd2b99f7"
EXPECTED_CAMPAIGN_COUNTS = MappingProxyType({
    FrontierV33Campaign.POLYNOMIAL_EUCLIDEAN_DIVISION: 121,
})
EXPECTED_FACTORY_COUNTS = MappingProxyType({
    "prime_field_polynomial_convolution_triangular_candidate": 8,
    "prime_field_polynomial_representation_candidate": 30,
    "prime_field_polynomial_division_candidate": 25,
    "prime_field_polynomial_distributivity_candidate": 18,
    "prime_field_polynomial_division_uniqueness_candidate": 9,
    "prime_field_polynomial_convolution_padding_candidate": 23,
    "prime_field_polynomial_equivalence_candidate": 5,
    "prime_field_polynomial_convolution_congruence_candidate": 3,
})
EXPECTED_FACTORY_SOURCE_SHA256 = MappingProxyType({
    "prime_field_polynomial_convolution_triangular_candidate": "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f",
    "prime_field_polynomial_representation_candidate": "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a",
    "prime_field_polynomial_division_candidate": "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2",
    "prime_field_polynomial_distributivity_candidate": "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86",
    "prime_field_polynomial_division_uniqueness_candidate": "6a9d9ebe1f72202743e5df2c069b9aa367fdb3d61108f1d9354cdc9276ab2d15",
    "prime_field_polynomial_convolution_padding_candidate": "2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007",
    "prime_field_polynomial_equivalence_candidate": "929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373",
    "prime_field_polynomial_convolution_congruence_candidate": "effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70",
})
ROOT_STATEMENT_SHA256 = MappingProxyType({
    "prime_field_polynomial_division_execution_functional": "b14ad2149cd34386887dcac50cb06b7df7014500b1ab918fac7967976b6042fe",
    "prime_field_polynomial_division_execution_exists_unique": "0ac4c1f5ca519e7db039365ff2a703f8772e22e58376d4c55a3f7777e08565fc",
    "prime_field_polynomial_convolution_both_left_paddings_equivalent": "fbefa6c478ac7028d2c60d742799660f05d010578ce4ed30b0f72f6f0af237d6",
    "prime_field_polynomial_convolution_both_left_paddings_exists": "b79ee5e0362c752f6b0189437e25cacc49e7060037adf8837f3105db832f8ffd",
    "prime_field_polynomial_equivalent_implies_left_pad": "e9b137b8b2e2d502cb4f5405a4cb90a0abcbb50de9a0df45ff51d5127761a25c",
    "prime_field_polynomial_add_equivalent_congruent": "847a60b511d446febdc15c56231f1368a7993172939945b7b99ab297cb65c4fb",
    "prime_field_polynomial_subtract_equivalent_congruent": "b073daede7886ec70b68c11665fc2f70154db2696cd613e542d1e22900e5f2a3",
    "prime_field_polynomial_convolution_equivalent_congruent": "d984fe3c378d4d4b02941d6f3a126324a2c7c26bf47f4d8ee7c37b2e55404446",
})


def _validate_parent() -> None:
    try:
        v32.require_research_seal()
    except v32.EditionV32Error as error:
        raise AlphaV33EnrollmentError("the immutable Alpha-v32 parent seal changed") from error
    if (
        len(v32.ALPHA_ENTRIES) != PARENT_ALPHA_V32_COUNT
        or len(v32.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V32_COUNT
        or v32.ALPHA_V32_ENROLLMENT_SHA256 != PARENT_ALPHA_V32_ENROLLMENT_SHA256
        or v32.ALPHA_V32_IDENTITY_SHA256 != PARENT_ALPHA_V32_IDENTITY_SHA256
        or _specs_digest(v32.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V32_SPECS_SHA256
        or len(v32.STABLE_SPECS) != 432
    ):
        raise AlphaV33EnrollmentError("the immutable completely checked Alpha-v32 parent changed")


@lru_cache(maxsize=1)
def alpha_v33_enrollment() -> AlphaV33Enrollment:
    validate_research_metadata()
    _validate_parent()
    metadata = tuple((
        owner.campaign, owner.module, owner.factory, owner.rfc,
        owner.source_bytes, owner.source_sha256, owner.count, owner.specs_sha256, owner.test_filename,
    ) for owner in FACTORIES)
    if (
        tuple(owner.module for owner in FACTORIES) != tuple(EXPECTED_FACTORY_COUNTS)
        or sha256(json.dumps(metadata, separators=(",", ":")).encode()).hexdigest()
        != EXPECTED_FACTORY_METADATA_SHA256
        or any(owner.count != EXPECTED_FACTORY_COUNTS[owner.module]
               or owner.source_sha256 != EXPECTED_FACTORY_SOURCE_SHA256[owner.module]
               for owner in FACTORIES)
    ):
        raise AlphaV33EnrollmentError("the literal Alpha-v33 factory inventory changed")
    rows = research_specs()
    if (
        len(rows) != FRONTIER_V33_EXPECTED_COUNT
        or tuple(row.name for row in rows) != FRONTIER_NEW_NAMES
        or sha256("\n".join(row.name for row in rows).encode()).hexdigest()
        != FRONTIER_V33_EXPECTED_NAMES_SHA256
        or _specs_digest(rows) != FRONTIER_V33_EXPECTED_SPECS_SHA256
        or sum(len(row.dependencies) for row in rows) != FRONTIER_V33_EXPECTED_EDGE_COUNT
        or sum(len(row.script) for row in rows) != FRONTIER_V33_EXPECTED_COMMAND_COUNT
    ):
        raise AlphaV33EnrollmentError("the complete additive Alpha-v33 specifications changed")
    available = {entry.spec.name for entry in v32.ALPHA_ENTRIES}
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV33Campaign] = {}
    offset = 0
    for owner in FACTORIES:
        local = rows[offset:offset + owner.count]
        offset += owner.count
        campaign = FrontierV33Campaign(owner.campaign)
        for item in local:
            if (
                type(item) is not TheoremSpec or item.name in available
                or type(item.dependencies) is not tuple
                or len(set(item.dependencies)) != len(item.dependencies)
                or not set(item.dependencies) <= available
                or type(item.script) is not tuple or not item.script
                or any(type(command) is not str or not command.strip()
                       or "DNE" in command or command.startswith(("use ", "admit", "sorry"))
                       for command in item.script)
            ):
                raise AlphaV33EnrollmentError(f"invalid additive constructive theorem {item.name!r}")
            _closed_formula(item.statement)
            available.add(item.name)
            sources[item.name] = owner.source
            tests[item.name] = owner.test
            rfcs[item.name] = "research/arithmetic-library/" + owner.rfc
            campaigns[item.name] = campaign
    if Counter(campaigns.values()) != EXPECTED_CAMPAIGN_COUNTS:
        raise AlphaV33EnrollmentError("the exact Alpha-v33 campaign ownership counts changed")
    by_name = {row.name: row for row in rows}
    for name, digest in ROOT_STATEMENT_SHA256.items():
        if name not in by_name or sha256(by_name[name].statement.encode()).hexdigest() != digest:
            raise AlphaV33EnrollmentError(f"an exact principal statement changed: {name}")
    return AlphaV33Enrollment(
        v32.ALPHA_ENTRIES, rows, MappingProxyType(sources), MappingProxyType(tests),
        MappingProxyType(rfcs), MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV33Enrollment", "AlphaV33EnrollmentError", "FrontierV33Campaign",
    "alpha_v33_enrollment", "EXPECTED_CAMPAIGN_COUNTS", "EXPECTED_FACTORY_COUNTS",
    "EXPECTED_FACTORY_METADATA_SHA256", "EXPECTED_FACTORY_SOURCE_SHA256",
    "FRONTIER_V33_EXPECTED_COUNT", "FRONTIER_V33_EXPECTED_EDGE_COUNT",
    "FRONTIER_V33_EXPECTED_COMMAND_COUNT", "FRONTIER_V33_EXPECTED_NAMES_SHA256",
    "FRONTIER_V33_EXPECTED_SPECS_SHA256", "PARENT_ALPHA_V32_COUNT",
    "PARENT_ALPHA_V32_SPECS_SHA256", "PARENT_ALPHA_V32_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V32_IDENTITY_SHA256", "ROOT_STATEMENT_SHA256",
)
