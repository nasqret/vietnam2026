"""Artifact-free exact enrollment of the polynomial gcd and standard congruence campaigns.

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

from . import editions_v33 as v33
from .campaign_research_v34_closure import (
    FACTORIES, FAMILIES, FRONTIER_NEW_NAMES,
    EXPECTED_RESEARCH_METADATA_SHA256,
    PARENT_ALPHA_V33_COUNT, PARENT_ALPHA_V33_SPECS_SHA256,
    PARENT_ALPHA_V33_ENROLLMENT_SHA256, PARENT_ALPHA_V33_IDENTITY_SHA256,
    research_specs, validate_research_metadata, _specs_digest,
)
from .theorems import TheoremSpec, _closed_formula


class AlphaV34EnrollmentError(ValueError):
    """The frozen parent, reviewed factory or additive dependency DAG changed."""


class FrontierV34Campaign(str, Enum):
    POLYNOMIAL_GCD_BEZOUT = "polynomial-gcd-bezout"
    CONGRUENCE_ARITHMETIC = "congruence-arithmetic"


@dataclass(frozen=True, slots=True)
class AlphaV34Enrollment:
    parent_entries: tuple[v33.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV34Campaign]


FRONTIER_V34_EXPECTED_COUNT = 131
FRONTIER_V34_EXPECTED_EDGE_COUNT = 604
FRONTIER_V34_EXPECTED_COMMAND_COUNT = 12869
FRONTIER_V34_EXPECTED_NAMES_SHA256 = "598d12b73489765a771d4edde6524abaabb3d61c3ea8d583b5e79b7f0ffdf024"
FRONTIER_V34_EXPECTED_SPECS_SHA256 = "ab0c6fd6bd8aa8d5d93dcbe59c5d0721d9e747efcab6413c5b0675f720f9fc60"
EXPECTED_FACTORY_METADATA_SHA256 = "4d7b72264a963dfec0e58d6e6cb2133a7969cce682a483d42dfdb3a795e80597"
EXPECTED_CAMPAIGN_COUNTS = MappingProxyType({
    FrontierV34Campaign.POLYNOMIAL_GCD_BEZOUT: 119,
    FrontierV34Campaign.CONGRUENCE_ARITHMETIC: 12,
})
EXPECTED_FACTORY_COUNTS = MappingProxyType({
    "prime_field_polynomial_shift_candidate": 15,
    "prime_field_polynomial_scalar_convolution_candidate": 10,
    "prime_field_polynomial_append_candidate": 6,
    "prime_field_polynomial_shift_equivalence_candidate": 1,
    "prime_field_polynomial_associativity_step_candidate": 3,
    "prime_field_polynomial_associativity_induction_candidate": 2,
    "prime_field_polynomial_divisibility_candidate": 7,
    "prime_field_polynomial_left_unit_candidate": 8,
    "prime_field_polynomial_alignment_candidate": 7,
    "prime_field_polynomial_aligned_add_candidate": 9,
    "prime_field_polynomial_aligned_algebra_candidate": 4,
    "prime_field_polynomial_euclidean_identity_candidate": 2,
    "prime_field_polynomial_aligned_distributivity_candidate": 2,
    "prime_field_polynomial_left_constant_candidate": 6,
    "prime_field_polynomial_euclidean_normalization_candidate": 5,
    "prime_field_polynomial_euclidean_transport_candidate": 5,
    "prime_field_polynomial_bezout_backward_candidate": 3,
    "prime_field_polynomial_gcd_bezout_laws_candidate": 4,
    "prime_field_polynomial_gcd_existence_candidate": 9,
    "prime_field_polynomial_gcd_uniqueness_candidate": 11,
    "linear_congruence_classification_candidate": 12,
})
EXPECTED_FACTORY_SOURCE_SHA256 = MappingProxyType({
    "prime_field_polynomial_shift_candidate": "325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b",
    "prime_field_polynomial_scalar_convolution_candidate": "e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e",
    "prime_field_polynomial_append_candidate": "271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042",
    "prime_field_polynomial_shift_equivalence_candidate": "8846224923876a4f57ad8d6f31020838ccc86c86a683ec78a7c7c23c35b92068",
    "prime_field_polynomial_associativity_step_candidate": "dd85dbd1bd87143715a4286724ac7c87f280a909dac6759f00a6cb7dff7c85f1",
    "prime_field_polynomial_associativity_induction_candidate": "8d276a028764cd08e6eaebbf25bb4e21fcd5076a610d356a77d52ba6603ebe4c",
    "prime_field_polynomial_divisibility_candidate": "f544adedd3ce963e4a773e8582efcb0f91ba7491207c9792d477d452e854f2b8",
    "prime_field_polynomial_left_unit_candidate": "dbb8debb4716b6bb9b246700f7e93865c8a6c1b12a3b65c0ffbb62206a890ba6",
    "prime_field_polynomial_alignment_candidate": "eb16e2eb02dbd66a7706e616388182992b8cf2e0715818dc1f7748938e7d798e",
    "prime_field_polynomial_aligned_add_candidate": "a05bb4f5c4230ca05f51690d3ab82e33ff4596af65176874e25fbe38cf87a0db",
    "prime_field_polynomial_aligned_algebra_candidate": "a68de84439afb5f6dd87f1d47449c0bce8dd53a66346c00cc1b7645fb80b2390",
    "prime_field_polynomial_euclidean_identity_candidate": "8efdcd2abf2143891b79edcb3fc90d7126ae69507c1c631ed33b497172ffdb77",
    "prime_field_polynomial_aligned_distributivity_candidate": "7d535939e24fe6d82158c485533b2ff6934f4d897b6141fde6c50b4fec9788ba",
    "prime_field_polynomial_left_constant_candidate": "9a7a4de30f5f389bcabc2e6267a0d2cc5dc5f061059dcea303a0a03dab58509a",
    "prime_field_polynomial_euclidean_normalization_candidate": "d2cddfe42dc0d22104dc4e85e95116222914df11ac840d2082a4ff2e462f146f",
    "prime_field_polynomial_euclidean_transport_candidate": "9a589d1749eb38d30d1a24364bc4d66f7df0efb59247527f7831f97557da9c30",
    "prime_field_polynomial_bezout_backward_candidate": "c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702",
    "prime_field_polynomial_gcd_bezout_laws_candidate": "76b90226e5e29fdde3d9bb49accccf8d9b4c0cc17a4de406af253e999102533c",
    "prime_field_polynomial_gcd_existence_candidate": "81f2f48dd2e81894c7a267453646eb6f2b6f9bd3ee320386d8c561f6b9f8b8ca",
    "prime_field_polynomial_gcd_uniqueness_candidate": "916c24ad6c59609612e97daee6e49347a9522cdb28b44f6f09c6c5760bff0b5b",
    "linear_congruence_classification_candidate": "12b1a98ce830704485f1ea78475fba8b10e39031ffbef00b1b5dfc8ffdef7f47",
})
ROOT_STATEMENT_SHA256 = MappingProxyType({
    "prime_field_polynomial_convolution_shift_right_exists": "0fc173b813282a7111d604245b1706a4c01c5bcf566812151810e9afe38f065d",
    "prime_field_polynomial_convolution_right_scale_exists": "5d0349367decc3084471726b73a77617d49f484cf31191bb78effbc434167156",
    "prime_field_polynomial_convolution_right_scale_zero": "fd6d04fd88ff9f594f7ee27de04486c1932ce5de30b6030b6b9b18cb547511ef",
    "prime_field_convolution_coefficient_right_append_add": "a11e1f29b31ae9076959706b6b5d0813689194a2ab57a1a4e879e6a6c3ad69bd",
    "prime_field_polynomial_convolution_right_append_exists": "0ef69b8524dd48c1a9805f158e9eff25c41e421b85378b96b51b7c63bd89f087",
    "prime_field_polynomial_right_divides_dividend_bounded": "a1f28266b77ee02c24747cf96ca7234d9d13bc3c46d38b2bb6b2f805c1538278",
    "prime_field_polynomial_right_divides_reflexive": "d8f3531eb2f6d2fb37e8ee936807a66a7dc1e49b71c95c7c7023c7964fc03852",
    "prime_field_polynomial_aligned_subtract_from_fixed": "3122386d4be93f7e4bca06128ec30ae0e3334dd046f69bb995b602499ae49804",
    "prime_field_polynomial_aligned_subtract_functional": "1025f30027f56856f3370a9d951e7ed68e7b83c785a30164ee5a868824667813",
    "prime_field_polynomial_left_constant_product_to_scale": "c93e29c84d993f933394eb2fc82600d8f3d88f50a06a25ee9d6dc69e6b2141fe",
    "prime_field_polynomial_division_constant_remainder_empty": "ac7f30f0841995aa9fe25e0546803c6bcf4aab7c09fa337a4c61eafa6f196a9b",
    "prime_field_polynomial_normalized_gcd_bezout_exists": "d97cbfa3dc334fa5bcf7b9bd92bde2e117b29595864a9cddb093ffe842832463",
    "prime_field_polynomial_normalized_gcd_equivalent_unique": "302df17d7792e85eb95dc25ff3b82ef61c84f67da66a886c1ef383f1115ef7a7",
    "prime_field_polynomial_bezout_is_right_gcd": "91a89630be8631cd892a7e0dd57bc4a36c2f3a3b734b16f12390124493a0ab43",
    "linear_congruence_exact_bounded_enumeration_exists": "489b9733a5124b9e9e82074322f4aa82b37cb54e89cc0dfa508658546c84a5c4",
    "linear_congruence_zero_modulus_nonzero_coefficient_unique": "f94cdd4b83fb5b7da9fa6b6694f4b8259ff3d9e48ec90b2b3cdd704f1b5adf59",
    "linear_congruence_zero_modulus_zero_coefficient_iff": "59355ce5396903898f8393dcf5602f96bb91c163b4c0a55d7c2b07b21e3c03a5",
    "linear_congruence_modulus_one_bounded_iff_zero": "924f0bbdbd0c7fa3633fb0b47acd00510e6d07be5e6ebf292e22c9aef17042f3",
    "fermat_little_all_inputs": "6a1162d7a8f6279242317f8ac7b9e93ca4f53d4dcf5563ca4a048d8dec75bb23",
})


def _validate_parent() -> None:
    try:
        v33.require_research_seal()
    except v33.EditionV33Error as error:
        raise AlphaV34EnrollmentError("the immutable Alpha-v33 parent seal changed") from error
    if (
        len(v33.ALPHA_ENTRIES) != PARENT_ALPHA_V33_COUNT
        or len(v33.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V33_COUNT
        or v33.ALPHA_V33_ENROLLMENT_SHA256 != PARENT_ALPHA_V33_ENROLLMENT_SHA256
        or v33.ALPHA_V33_IDENTITY_SHA256 != PARENT_ALPHA_V33_IDENTITY_SHA256
        or _specs_digest(v33.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V33_SPECS_SHA256
        or len(v33.STABLE_SPECS) != 432
    ):
        raise AlphaV34EnrollmentError("the immutable completely checked Alpha-v33 parent changed")


@lru_cache(maxsize=1)
def alpha_v34_enrollment() -> AlphaV34Enrollment:
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
        raise AlphaV34EnrollmentError("the literal Alpha-v34 factory inventory changed")
    rows = research_specs()
    if (
        len(rows) != FRONTIER_V34_EXPECTED_COUNT
        or tuple(row.name for row in rows) != FRONTIER_NEW_NAMES
        or sha256("\n".join(row.name for row in rows).encode()).hexdigest()
        != FRONTIER_V34_EXPECTED_NAMES_SHA256
        or _specs_digest(rows) != FRONTIER_V34_EXPECTED_SPECS_SHA256
        or sum(len(row.dependencies) for row in rows) != FRONTIER_V34_EXPECTED_EDGE_COUNT
        or sum(len(row.script) for row in rows) != FRONTIER_V34_EXPECTED_COMMAND_COUNT
    ):
        raise AlphaV34EnrollmentError("the complete additive Alpha-v34 specifications changed")
    available = {entry.spec.name for entry in v33.ALPHA_ENTRIES}
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV34Campaign] = {}
    offset = 0
    for owner in FACTORIES:
        local = rows[offset:offset + owner.count]
        offset += owner.count
        campaign = FrontierV34Campaign(owner.campaign)
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
                raise AlphaV34EnrollmentError(f"invalid additive constructive theorem {item.name!r}")
            _closed_formula(item.statement)
            available.add(item.name)
            sources[item.name] = owner.source
            tests[item.name] = owner.test
            rfcs[item.name] = "research/arithmetic-library/" + owner.rfc
            campaigns[item.name] = campaign
    if Counter(campaigns.values()) != EXPECTED_CAMPAIGN_COUNTS:
        raise AlphaV34EnrollmentError("the exact Alpha-v34 campaign ownership counts changed")
    by_name = {row.name: row for row in rows}
    for name, digest in ROOT_STATEMENT_SHA256.items():
        if name not in by_name or sha256(by_name[name].statement.encode()).hexdigest() != digest:
            raise AlphaV34EnrollmentError(f"an exact principal statement changed: {name}")
    return AlphaV34Enrollment(
        v33.ALPHA_ENTRIES, rows, MappingProxyType(sources), MappingProxyType(tests),
        MappingProxyType(rfcs), MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV34Enrollment", "AlphaV34EnrollmentError", "FrontierV34Campaign",
    "alpha_v34_enrollment", "EXPECTED_CAMPAIGN_COUNTS", "EXPECTED_FACTORY_COUNTS",
    "EXPECTED_FACTORY_METADATA_SHA256", "EXPECTED_FACTORY_SOURCE_SHA256",
    "FRONTIER_V34_EXPECTED_COUNT", "FRONTIER_V34_EXPECTED_EDGE_COUNT",
    "FRONTIER_V34_EXPECTED_COMMAND_COUNT", "FRONTIER_V34_EXPECTED_NAMES_SHA256",
    "FRONTIER_V34_EXPECTED_SPECS_SHA256", "PARENT_ALPHA_V33_COUNT",
    "PARENT_ALPHA_V33_SPECS_SHA256", "PARENT_ALPHA_V33_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V33_IDENTITY_SHA256", "ROOT_STATEMENT_SHA256",
)
