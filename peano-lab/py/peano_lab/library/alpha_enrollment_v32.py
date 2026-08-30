"""Artifact-free exact enrollment of the two completed constructive research campaigns.

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

from . import editions_v31 as v31
from .campaign_research_v32_closure import (
    FACTORIES, FAMILIES, FRONTIER_NEW_NAMES,
    EXPECTED_RESEARCH_METADATA_SHA256,
    PARENT_ALPHA_V31_COUNT, PARENT_ALPHA_V31_SPECS_SHA256,
    PARENT_ALPHA_V31_ENROLLMENT_SHA256, PARENT_ALPHA_V31_IDENTITY_SHA256,
    research_specs, validate_research_metadata, _specs_digest,
)
from .theorems import TheoremSpec, _closed_formula


class AlphaV32EnrollmentError(ValueError):
    """The frozen parent, reviewed factory or additive dependency DAG changed."""


class FrontierV32Campaign(str, Enum):
    MULTIPLICATIVE_CONVOLUTION = "multiplicative-convolution"
    POLYNOMIAL_DIVISION_PREREQUISITES = "polynomial-division-prerequisites"


@dataclass(frozen=True, slots=True)
class AlphaV32Enrollment:
    parent_entries: tuple[v31.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV32Campaign]


FRONTIER_V32_EXPECTED_COUNT = 175
FRONTIER_V32_EXPECTED_EDGE_COUNT = 503
FRONTIER_V32_EXPECTED_COMMAND_COUNT = 9029
FRONTIER_V32_EXPECTED_NAMES_SHA256 = "2411dd4b45e58c5905ac24b5c091462594579c42923de238ba05ffaf2f120a64"
FRONTIER_V32_EXPECTED_SPECS_SHA256 = "5c19425ae209472383459546cbd5765c66511249fdcf0290b8860bd392ef3700"
EXPECTED_FACTORY_METADATA_SHA256 = "9a7c1669f4cce42df441aad52ecf9813f01a31bb2f1d5725b2e130a208810254"
EXPECTED_CAMPAIGN_COUNTS = MappingProxyType({
    FrontierV32Campaign.MULTIPLICATIVE_CONVOLUTION: 90,
    FrontierV32Campaign.POLYNOMIAL_DIVISION_PREREQUISITES: 85,
})
EXPECTED_FACTORY_COUNTS = MappingProxyType({
    "arithmetic_multiplicative_candidate": 11,
    "coprime_divisor_decomposition_candidate": 8,
    "divisor_pair_index_candidate": 4,
    "signed_block_sum_candidate": 7,
    "signed_cartesian_product_candidate": 20,
    "signed_support_reindex_candidate": 25,
    "dirichlet_multiplicative_entry_candidate": 5,
    "dirichlet_multiplicative_support_candidate": 6,
    "dirichlet_multiplicative_candidate": 4,
    "prime_field_polynomial_subtraction_candidate": 26,
    "prime_field_polynomial_trim_candidate": 22,
    "prime_field_polynomial_monic_candidate": 20,
    "prime_field_polynomial_synthetic_candidate": 17,
})
EXPECTED_FACTORY_SOURCE_SHA256 = MappingProxyType({
    "arithmetic_multiplicative_candidate": "f4374450ec543f69093b98367c90f67f09ac15daacd1df2f90961d7b6ece4a7e",
    "coprime_divisor_decomposition_candidate": "de19bb61543f5d7ab3a1d1b675c96ae4b31c7c96b58d6107904e7188973a2e1c",
    "divisor_pair_index_candidate": "fc6a5a555fdee62cf5f54365163f32c4acfee10b8f416b811bb69debdbcf62a0",
    "signed_block_sum_candidate": "0597b3806fec32b8eb117f5d0f6be2304c754aa8078df6f50de9dd4d12a2c18f",
    "signed_cartesian_product_candidate": "d7dbe1d9a82ee5b91e33d6a4624d3e7f05b20d4618045ecab8e753eee6c7e351",
    "signed_support_reindex_candidate": "db91e38ca5e671adf88e3bf70396b1a242f9c760d6f2c52c4785e6a63316339e",
    "dirichlet_multiplicative_entry_candidate": "d7f55b8f25e56f8b9c5bc3f6c4b83698d5f1ad770e1e4ed77c53f12a602bd897",
    "dirichlet_multiplicative_support_candidate": "56e9f8ccaa7c795e42b33984bc2346182ba3a1f820883ba884e571b89091d4a5",
    "dirichlet_multiplicative_candidate": "bb1342735115781fd8f0107d3876c95098e0b6dc459f31981ffb2c16432eab77",
    "prime_field_polynomial_subtraction_candidate": "d08562b26c683a891e58a4b10faa495867d7487054b1ee7c99f091dd1c707b2b",
    "prime_field_polynomial_trim_candidate": "1125c02fd11646efaa20963380ba1086e18551f2c89b242b8900a8043d358e4c",
    "prime_field_polynomial_monic_candidate": "3bf93aff71b48a332920b1a6174e44167bf78238caac3b6d35634f3591582eef",
    "prime_field_polynomial_synthetic_candidate": "0938e369e528666e8e52c5d49b157a12bd00bf50150783182b3b5ebc36b02022",
})
ROOT_STATEMENT_SHA256 = MappingProxyType({
    "signed_support_reindex_sum_equal": "3077d5330886460850c4a16cd0e57026c138813c128d9e013c61e428ec2c56cc",
    "signed_cartesian_product_sums_exists": "112d93e7f0c1b600a57b30c7b06341d249f529c30dfaf907ceeae9f8614b51c7",
    "coprime_divisor_factor_pair_exists_unique": "629b845a1c30abee52ebb49d4f59dea2b06bc00dab3403512507e737112c4d12",
    "dirichlet_convolution_multiplicative_values": "7a5bfcd97f2feacc1e3c49a520bbf41370e09c940f6d35f16b54ca27a4b84868",
    "dirichlet_convolution_multiplicative_table": "c5f3035ecf2a9e90fc3e56118bb17769ddc68feb1a32a95aa48619cf7c4b8889",
    "dirichlet_convolution_multiplicative_exists_unique": "957aa567b3f1547a98478a195178e8d5a7e88cf6a01af0b67f94413191d56970",
    "prime_field_polynomial_subtract_exists": "e6a46edf32d7a565ab18ccc9406cec320dbeefc6f0094b7169f28a1080d6a965",
    "prime_field_polynomial_trim_exists_unique": "9d2f9bdd9da63a0f151a5b0b8c0918506ee25f3868bcd3138b2810c94691caa3",
    "prime_field_polynomial_monic_normalization_exists_unique": "8e2fc07b075ca8acacefcd2ba4ac6ef42511e463f64745b2875a498484eedcb5",
    "prime_field_polynomial_synthetic_exists_unique": "a9ca5a2a94437641e4cc683ef0dcdabb5eef4bbb4a181620e6760f1ff285ad7b",
    "prime_field_polynomial_synthetic_represented_degree": "c8b3b71ec31e34582c37aa3037efa57961699f87f9dfc242316db5bb5e951392",
    "prime_field_polynomial_synthetic_zero_remainder_iff": "817632388315e7ec579bf1788ae68f75200a7cee737a17f46779150cf4c45441",
})


def _validate_parent() -> None:
    try:
        v31.require_completed_lower_seal()
    except v31.EditionV31Error as error:
        raise AlphaV32EnrollmentError("the immutable Alpha-v31 parent seal changed") from error
    if (
        len(v31.ALPHA_ENTRIES) != PARENT_ALPHA_V31_COUNT
        or len(v31.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V31_COUNT
        or v31.ALPHA_V31_ENROLLMENT_SHA256 != PARENT_ALPHA_V31_ENROLLMENT_SHA256
        or v31.ALPHA_V31_IDENTITY_SHA256 != PARENT_ALPHA_V31_IDENTITY_SHA256
        or _specs_digest(v31.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V31_SPECS_SHA256
        or len(v31.STABLE_SPECS) != 432
    ):
        raise AlphaV32EnrollmentError("the immutable completely checked Alpha-v31 parent changed")


@lru_cache(maxsize=1)
def alpha_v32_enrollment() -> AlphaV32Enrollment:
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
        raise AlphaV32EnrollmentError("the literal Alpha-v32 factory inventory changed")
    rows = research_specs()
    if (
        len(rows) != FRONTIER_V32_EXPECTED_COUNT
        or tuple(row.name for row in rows) != FRONTIER_NEW_NAMES
        or sha256("\n".join(row.name for row in rows).encode()).hexdigest()
        != FRONTIER_V32_EXPECTED_NAMES_SHA256
        or _specs_digest(rows) != FRONTIER_V32_EXPECTED_SPECS_SHA256
        or sum(len(row.dependencies) for row in rows) != FRONTIER_V32_EXPECTED_EDGE_COUNT
        or sum(len(row.script) for row in rows) != FRONTIER_V32_EXPECTED_COMMAND_COUNT
    ):
        raise AlphaV32EnrollmentError("the complete additive Alpha-v32 specifications changed")
    available = {entry.spec.name for entry in v31.ALPHA_ENTRIES}
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV32Campaign] = {}
    offset = 0
    for owner in FACTORIES:
        local = rows[offset:offset + owner.count]
        offset += owner.count
        campaign = FrontierV32Campaign(owner.campaign)
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
                raise AlphaV32EnrollmentError(f"invalid additive constructive theorem {item.name!r}")
            _closed_formula(item.statement)
            available.add(item.name)
            sources[item.name] = owner.source
            tests[item.name] = owner.test
            rfcs[item.name] = "research/arithmetic-library/" + owner.rfc
            campaigns[item.name] = campaign
    if Counter(campaigns.values()) != EXPECTED_CAMPAIGN_COUNTS:
        raise AlphaV32EnrollmentError("the exact Alpha-v32 campaign ownership counts changed")
    by_name = {row.name: row for row in rows}
    for name, digest in ROOT_STATEMENT_SHA256.items():
        if name not in by_name or sha256(by_name[name].statement.encode()).hexdigest() != digest:
            raise AlphaV32EnrollmentError(f"an exact principal statement changed: {name}")
    return AlphaV32Enrollment(
        v31.ALPHA_ENTRIES, rows, MappingProxyType(sources), MappingProxyType(tests),
        MappingProxyType(rfcs), MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV32Enrollment", "AlphaV32EnrollmentError", "FrontierV32Campaign",
    "alpha_v32_enrollment", "EXPECTED_CAMPAIGN_COUNTS", "EXPECTED_FACTORY_COUNTS",
    "EXPECTED_FACTORY_METADATA_SHA256", "EXPECTED_FACTORY_SOURCE_SHA256",
    "FRONTIER_V32_EXPECTED_COUNT", "FRONTIER_V32_EXPECTED_EDGE_COUNT",
    "FRONTIER_V32_EXPECTED_COMMAND_COUNT", "FRONTIER_V32_EXPECTED_NAMES_SHA256",
    "FRONTIER_V32_EXPECTED_SPECS_SHA256", "PARENT_ALPHA_V31_COUNT",
    "PARENT_ALPHA_V31_SPECS_SHA256", "PARENT_ALPHA_V31_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V31_IDENTITY_SHA256", "ROOT_STATEMENT_SHA256",
)
