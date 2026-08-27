"""Strict additive priority-layer enrollment over the immutable Alpha-v28 edition.

Enrollment records reviewed specifications, not proof authority. Checked use
requires every actual body in the exact dependency-closed artifact to pass the
unchanged intuitionistic kernel; publication additionally runs the independent
compiled Lean verifier. Historical admission records and Stable stay intact.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
import json
from types import MappingProxyType
from typing import Mapping

from . import editions_v28 as v28
from .campaign_priority_layer_closure import FACTORIES, _specs_digest
from .theorems import TheoremSpec, _closed_formula


class AlphaV29EnrollmentError(ValueError):
    """The frozen parent, reviewed proof factory, or dependency DAG changed."""


class FrontierV29Campaign(str, Enum):
    PRIME_VALUATION_SUPPORT = "prime_valuation_support"
    CONTINUED_FRACTION_APPROXIMATION = "continued_fraction_approximation"
    EULER_TOTIENT = "euler_totient"
    SQUAREFREE_PERFECT_POWER = "squarefree_perfect_power"
    ODD_PRIME_LTE = "odd_prime_lte"


@dataclass(frozen=True, slots=True)
class AlphaV29Enrollment:
    parent_entries: tuple[v28.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV29Campaign]


PARENT_ALPHA_V28_COUNT = 2_764
PARENT_ALPHA_V28_ENROLLMENT_SHA256 = (
    "75c80dffb8899dbf6f97a561322e630679d9df58416309e5c439746e96466fce"
)
PARENT_ALPHA_V28_IDENTITY_SHA256 = (
    "4936d155e8d2a39409a4e83beb4ac5cb2481948d8b6eeecf1c7571161786646b"
)

# Frozen after all four complete dependency cones passed the original kernel
# and independently compiled Lean verifier. Metadata alone is never a proof.
FRONTIER_V29_EXPECTED_COUNT = 278
FRONTIER_V29_EXPECTED_EDGE_COUNT = 931
FRONTIER_V29_EXPECTED_NAMES_SHA256 = "cf4615b863bb1640151bde7dffd8dd904dc47cb9589c2cc4ec90485c82c4f509"
FRONTIER_V29_EXPECTED_SPECS_SHA256 = "99c0f9b3ad573043717d68714e9121475d62a9dd36974d0739352b15c6652a90"
EXPECTED_FACTORY_METADATA_SHA256 = "585e82858bec74d758be931e49e7509e5652ba2d7773c5d5ff84e0161633fe03"
EXPECTED_CAMPAIGN_COUNTS: dict[FrontierV29Campaign, int] = {
    FrontierV29Campaign.PRIME_VALUATION_SUPPORT: 20,
    FrontierV29Campaign.CONTINUED_FRACTION_APPROXIMATION: 83,
    FrontierV29Campaign.EULER_TOTIENT: 84,
    FrontierV29Campaign.SQUAREFREE_PERFECT_POWER: 53,
    FrontierV29Campaign.ODD_PRIME_LTE: 38,
}
EXPECTED_FACTORY_COUNTS: dict[str, int] = {
    "prime_valuation_support_candidate": 20,
    "continued_fraction_approximation_candidate": 39,
    "continued_fraction_convergents_candidate": 44,
    "euler_totient_count_candidate": 25,
    "euler_totient_interval_candidate": 12,
    "euler_totient_prime_step_candidate": 17,
    "euler_totient_algebra_candidate": 9,
    "euler_totient_product_candidate": 21,
    "squarefree_decomposition_candidate": 16,
    "perfect_power_profile_candidate": 37,
    "odd_prime_lte_candidate": 38
}
EXPECTED_FACTORY_SOURCE_SHA256: dict[str, str] = {
    "prime_valuation_support_candidate": "bbd6e661a575f6a39f7a71424611da36a16d34cb6704cbae2b918387cc0f66d2",
    "continued_fraction_approximation_candidate": "a9074eacabc922aaf57dd7ef7eb5210ca23fe70679db334a8a283dfe2ad33e59",
    "continued_fraction_convergents_candidate": "f97eb7e8e34ad04b5c7089cdbf44641fe4ee00608371ea509b5fd07104d78aa9",
    "euler_totient_count_candidate": "bb907716fb6a51c45f924068040a7732a7c0377b3fe4607274bd0b8f1a62cc14",
    "euler_totient_interval_candidate": "cd1b01f9645d47c1f8c02b5355f3dbd0173f47218ee7f34b01981ad0e7dce843",
    "euler_totient_prime_step_candidate": "179b7129bba16862808e3c2d083ffbfb8ed301d830976dcdb863d26aafd84ed2",
    "euler_totient_algebra_candidate": "137a03f968e0487dce8444d937591617c5ba9ad57b4771c95a8d5ee99b734622",
    "euler_totient_product_candidate": "98434c9fb1762f50fabc5eaa75c4bd6b7a2a0d05eaf3dc7860e6d05872076b67",
    "squarefree_decomposition_candidate": "3d4f2481e62adb13e53b6fbb70c0c22afd8c36b85ce62611686c04919f1bcec4",
    "perfect_power_profile_candidate": "6f29118bb08b670af9a170e95546084eb868608d3d3b853279d72fad53dded3d",
    "odd_prime_lte_candidate": "bd701478669f7a531fb4c387cf1e0949c57ef475a1675953cd5802cb43f62bdb"
}
ROOT_STATEMENT_SHA256: dict[str, str] = {
    "prime_valuation_support_exists": "d6e0d6a185004dcf15dae72c0bc893200f0b3d5688a8784c53497ef8fe60907b",
    "continued_fraction_convergent_index_is_valid": "7bf9f8067ced2ed2eb52386f08e7efa1a7cfe47aa05b36bfc9aa3048df5aeed7",
    "continued_fraction_initial_zero_over_one": "f3f23d230d72430e8d5af7462c5bf58a2d931e50d74083053c8d6374153ded00",
    "continued_fraction_has_exact_terminal_convergent": "4f2ff1801b78a9b8142e1e104bea9e49a5251d5c165f2982332e6a70fe966ea0",
    "continued_fraction_convergent_exists_unique_at_history_index": "a2350b3a79e730cf6c26001c3c5e8b515a6757a5d32cb64d83cd55853e6e6c5b",
    "continued_fraction_initial_convergent_is_first_quotient": "3c86b18e5e51da36f00546e6905a043475ce884f391fff5706099738e6fc3ade",
    "continued_fraction_adjacent_convergent_determinant": "5666bd5d85b19e815856e29a5c93bfa0c07e9e28b8e9aa651e08e9978dbded41",
    "continued_fraction_convergent_coprime": "dc7cd76880ad898f76cdcc22f0602e7ec51b08c4ac99e1e43afa1dd682fa859b",
    "continued_fraction_convergent_best_approximation_signed": "d1401bdb17320a1fc10ebfa605c42972b850cd596d1a6d114ad82b5be8f5492b",
    "continued_fraction_convergent_best_approximation": "f77356be459116bfcf711c13c7d70777afc2a7a5e93a91f28ee464d07c4bca2c",
    "totient_bounded": "69b251a8267787c85934ff7c8938bb84dc9a26ece3224c8c84ff61a90294cfcb",
    "totient_exists_unique": "949c4af14495d74cb45019f5e068fbb45580968e2abf1527f27b80146db77013",
    "totient_unit_count_modulus_transport": "f773949552a0f34466fcf6d695fdf06583d01c1add1627df2de3c967aa9cab87",
    "totient_prime_coprime_iff_nondivisor": "28dddd435dbbca016175a04306d00675492aaf81e7a19263d085fb01b8381f30",
    "totient_prime_power_value": "5a77436d23c80965981715a3196f5669122f4184a3201c19955d7fdfcdfb10f0",
    "totient_euler_factor_functional": "9e34f682291f3bdbe3c99335f23214c14fd3a291afe61926df6bf0bd8ef42150",
    "totient_euler_factor_prefix_drop_last": "40ba3047fc6390bb7a4f53a00ffa7d12a74215f671fb4d0aee5b4e4dfbffe7bb",
    "totient_euler_product_functional": "f47c7eb97e11c3971ab41e5c3fe090335cd36b1cfbc9264868d7b82d90678194",
    "totient_euler_product_iff": "1d37df29457d21f2f36c8fc9a652a0dfcde15bde5a730c8a3ae789fcf98eb176",
    "totient_euler_product_one": "5650edfce8b3712b3658545e921b60eeabc9f895078d4f2a756be5d19a698d45",
    "totient_euler_product_zero_excluded": "4f75707ef4318b5d242df321a53288e3f0d62bbd69acd9b487bfbe4d9a0484a4",
    "totient_euler_product_formula": "30f159a663418d13fe52b39acca9de20a67d44219cc28eb965c36f352ddcf2a2",
    "squarefree_one": "7836966aff0c8d2a23ca95bc525812398670799b96efeb0cb8db831bba43393e",
    "squarefree_decomposition_exists_unique": "efce5f0c441fd9d953dceab7c4a0869a11c41ad65e4eee3d1e73e3c6b92aacf3",
    "prime_exponent_prefix_gcd_functional": "2bbca6f988120d68d2789dd845c53c4df532890e8c301d90a8f2ba8c5d8b6182",
    "perfect_power_profile_data_degree_classification": "4c2d57506081b169c3db70a52b5996fcc7685864831fe45db892f6607586ecf4",
    "perfect_power_profile_data_root_lookup": "67dba36528e372272b28d94b01e479f8db3093917cae2768bda48ebe3ca57444",
    "perfect_power_profile_positive": "c1a1d56c0398396e62e907c86c128bcae4918d8e130dedb880fba3e3aa941819",
    "perfect_power_profile_unit_code": "60b383063bf7111a2d64778f10054bd8279c6781030bbf8934f90dea3f5133eb",
    "perfect_power_profile_nonunit_decode": "a6aab6715f2b60fed8d17529c812776693709806192da75df76904dc82de4fcf",
    "positive_squarefree_kernel_and_power_profile": "d90dd7d83bf94f698c6fde0134034eed5e89b5bae73c2caf58b6cdc788313949",
    "odd_prime_lifting_the_exponent": "36da85a059e7c726b9b4708cd6d34696d387b13f962fe6148654df3f0c469f6b",
    "odd_prime_lifting_the_exponent_value": "703616c3381acc0809aac4629c10006424894b62fceb60c40899b783329eac22"
}


def _validate_parent() -> None:
    if (
        len(v28.ALPHA_ENTRIES) != PARENT_ALPHA_V28_COUNT
        or len(v28.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V28_COUNT
        or v28.ALPHA_V28_ENROLLMENT_SHA256 != PARENT_ALPHA_V28_ENROLLMENT_SHA256
        or v28.ALPHA_V28_IDENTITY_SHA256 != PARENT_ALPHA_V28_IDENTITY_SHA256
        or len(v28.STABLE_SPECS) != 432
    ):
        raise AlphaV29EnrollmentError("immutable completely checked Alpha-v28 parent changed")


@lru_cache(maxsize=1)
def alpha_v29_enrollment() -> AlphaV29Enrollment:
    if (
        FRONTIER_V29_EXPECTED_COUNT <= 0
        or FRONTIER_V29_EXPECTED_EDGE_COUNT <= 0
        or len(FRONTIER_V29_EXPECTED_NAMES_SHA256) != 64
        or len(FRONTIER_V29_EXPECTED_SPECS_SHA256) != 64
        or len(EXPECTED_FACTORY_METADATA_SHA256) != 64
        or any(count <= 0 for count in EXPECTED_FACTORY_COUNTS.values())
        or any(count <= 0 for count in EXPECTED_CAMPAIGN_COUNTS.values())
    ):
        raise AlphaV29EnrollmentError("Alpha-v29 reviewed inventory is not sealed for admission")
    _validate_parent()
    if tuple(owner.module for owner in FACTORIES) != tuple(EXPECTED_FACTORY_COUNTS):
        raise AlphaV29EnrollmentError("reviewed Alpha-v29 factory inventory or order changed")
    available = {entry.spec.name for entry in v28.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV29Campaign] = {}

    for owner in FACTORIES:
        if (
            owner.factory != f"make_{owner.module}_theorems"
            or not owner.rfc.endswith("-rfc-v1.md")
            or "/" in owner.rfc or "\\" in owner.rfc or ".." in owner.rfc
            or owner.source_sha256 != EXPECTED_FACTORY_SOURCE_SHA256.get(owner.module)
        ):
            raise AlphaV29EnrollmentError("reviewed Alpha-v29 factory metadata changed")
        try:
            campaign = FrontierV29Campaign(owner.campaign)
            module = import_module(f".{owner.module}", package=__package__)
            candidates = tuple(getattr(module, owner.factory)(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV29EnrollmentError(
                f"unavailable reviewed Alpha-v29 factory {owner.module}.{owner.factory}"
            ) from error
        if len(candidates) != EXPECTED_FACTORY_COUNTS[owner.module]:
            raise AlphaV29EnrollmentError(
                f"exact Alpha-v29 factory cardinality changed: {owner.module}"
            )
        for item in candidates:
            if type(item) is not TheoremSpec or item.name in available:
                raise AlphaV29EnrollmentError("invalid or duplicate additive Alpha-v29 theorem")
            missing = set(item.dependencies).difference(available)
            if missing or len(set(item.dependencies)) != len(item.dependencies):
                raise AlphaV29EnrollmentError(
                    f"invalid Alpha-v29 dependencies for {item.name!r}: {sorted(missing)!r}"
                )
            if not item.script or any(
                "DNE" in command or command.startswith(("use ", "admit", "sorry")) for command in item.script
            ):
                raise AlphaV29EnrollmentError(
                    f"Alpha-v29 theorem lacks an explicit constructive script: {item.name!r}"
                )
            _closed_formula(item.statement)
            sources[item.name] = f"peano-lab/py/peano_lab/library/{owner.module}.py"
            tests[item.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfcs[item.name] = f"research/arithmetic-library/{owner.rfc}"
            campaigns[item.name] = campaign
            rows.append(item)
            available.add(item.name)

    if Counter(campaigns.values()) != EXPECTED_CAMPAIGN_COUNTS:
        raise AlphaV29EnrollmentError("exact Alpha-v29 aggregate campaign cardinalities changed")
    factory_metadata = json.dumps(
        [(f.campaign, f.module, f.factory, f.rfc, f.source_sha256) for f in FACTORIES],
        separators=(",", ":"),
    )
    if sha256(factory_metadata.encode()).hexdigest() != EXPECTED_FACTORY_METADATA_SHA256:
        raise AlphaV29EnrollmentError("exact Alpha-v29 reviewed factory metadata changed")
    if FRONTIER_V29_EXPECTED_COUNT and (
        len(rows) != FRONTIER_V29_EXPECTED_COUNT
        or sum(len(item.dependencies) for item in rows) != FRONTIER_V29_EXPECTED_EDGE_COUNT
        or sha256("\n".join(item.name for item in rows).encode()).hexdigest()
        != FRONTIER_V29_EXPECTED_NAMES_SHA256
        or _specs_digest(tuple(rows)) != FRONTIER_V29_EXPECTED_SPECS_SHA256
    ):
        raise AlphaV29EnrollmentError("exact additive Alpha-v29 priority-layer frontier changed")
    by_name = {item.name: item for item in rows}
    for name, expected in ROOT_STATEMENT_SHA256.items():
        actual = by_name.get(name)
        if actual is None or sha256(actual.statement.encode()).hexdigest() != expected:
            raise AlphaV29EnrollmentError(f"exact Alpha-v29 campaign root changed: {name}")

    return AlphaV29Enrollment(
        parent_entries=v28.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(sources),
        test_by_name=MappingProxyType(tests),
        rfc_by_name=MappingProxyType(rfcs),
        campaign_by_name=MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV29Enrollment", "AlphaV29EnrollmentError", "EXPECTED_CAMPAIGN_COUNTS",
    "EXPECTED_FACTORY_COUNTS", "EXPECTED_FACTORY_SOURCE_SHA256", "FRONTIER_V29_EXPECTED_COUNT",
    "EXPECTED_FACTORY_METADATA_SHA256",
    "FRONTIER_V29_EXPECTED_EDGE_COUNT", "FRONTIER_V29_EXPECTED_NAMES_SHA256",
    "FRONTIER_V29_EXPECTED_SPECS_SHA256",
    "FrontierV29Campaign", "PARENT_ALPHA_V28_COUNT",
    "PARENT_ALPHA_V28_ENROLLMENT_SHA256", "PARENT_ALPHA_V28_IDENTITY_SHA256",
    "ROOT_STATEMENT_SHA256", "alpha_v29_enrollment",
)
