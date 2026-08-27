"""Strict additive lower-layer enrollment over the immutable Alpha-v27 edition.

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
from types import MappingProxyType
from typing import Mapping

from . import editions_v27 as v27
from .campaign_lower_layer_closure import FACTORIES
from .theorems import TheoremSpec, _closed_formula


class AlphaV28EnrollmentError(ValueError):
    """The frozen parent, reviewed proof factory, or dependency DAG changed."""


class FrontierV28Campaign(str, Enum):
    FOUNDATIONS = "foundations"
    GAUSSIAN_EUCLIDEAN = "gaussian_euclidean"
    EISENSTEIN_EUCLIDEAN = "eisenstein_euclidean"
    PRIME_ENUMERATION = "prime_enumeration"


@dataclass(frozen=True, slots=True)
class AlphaV28Enrollment:
    parent_entries: tuple[v27.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV28Campaign]


PARENT_ALPHA_V27_COUNT = 2_560
PARENT_ALPHA_V27_ENROLLMENT_SHA256 = (
    "20866c3865baec2bc6cee3c8e54bcb2f55e95a7b1a7fc85c103e3c9b055ecf4e"
)
PARENT_ALPHA_V27_IDENTITY_SHA256 = (
    "5c5935ed524b63827068cba37da222fc78b458de6c5af2e07cf572bb9fab7d05"
)

# Frozen after all four complete dependency cones passed the original kernel
# and independently compiled Lean verifier. Metadata alone is never a proof.
FRONTIER_V28_EXPECTED_COUNT = 204
FRONTIER_V28_EXPECTED_EDGE_COUNT = 788
FRONTIER_V28_EXPECTED_NAMES_SHA256 = "7882fe1fbcd64ee23668f62dcc45aa4a946a562c7da2fd5dba3b30612bccc402"
EXPECTED_CAMPAIGN_COUNTS: dict[FrontierV28Campaign, int] = {
    FrontierV28Campaign.FOUNDATIONS: 28,
    FrontierV28Campaign.GAUSSIAN_EUCLIDEAN: 93,
    FrontierV28Campaign.EISENSTEIN_EUCLIDEAN: 65,
    FrontierV28Campaign.PRIME_ENUMERATION: 18,
}
EXPECTED_FACTORY_COUNTS: dict[str, int] = {
    "foundation_saturation_candidate": 5,
    "prime_factorization_permutation_candidate": 23,
    "signed_integer_division_candidate": 5,
    "gaussian_euclidean_candidate": 88,
    "eisenstein_euclidean_candidate": 65,
    "prime_enumeration_candidate": 18,
}
ROOT_STATEMENT_SHA256: dict[str, str] = {
    "foundation_division_exists_unique": "f43569ef56675e5aab556c26ad0606eea4f4de9c1c54078e6c51c3e96ef653ab",
    "foundation_signed_bezout_canonical_gcd": "3d20b5eb4e05f3b50ba301946c3fc791504ef4586ae3d2bed3f2bd58648790a6",
    "foundation_coprime_product_divisor": "4ec0d3dde7c6319356d61d282abed4edd22af6eeffba58e03162a18c4e58de42",
    "foundation_prime_factor_list_exists": "af68e2e841fe13eafddb375135f9f1abde79b0185d5722d3851c0fcf61af56dc",
    "foundation_primes_above_every_bound": "be3aeb8487e6cac71fa3093363e847f3afbdd176e23ebdbb5f003c080f518167",
    "prime_factor_lists_permutation_exists": "89df5c484cb30ab9c74dd04af9a5700c635ae402d01f8088ff934f75e0254518",
    "prime_factorization_exists_unique_up_to_permutation": "622f8362d88b818d10462b55bca228e06f0c517174001c7ea039b85bb054ab7c",
    "least_prime_above_exists_unique": "ccf83345ee78da1ec4542d321ee586284122be1121874e6b53de8e64960d043c",
    "first_primes_double_exponential_bound": "b69363aca6a0a887d3baba0ca6ddd13a550496075f15ec2cb4199e7c73054676",
    "prime_list_every_entry_is_prime": "d0a3b4a6314a9146f511ea2279ccf7ef6d02d4fd89a58620a3b6e94987e12e92",
    "prime_list_omits_no_smaller_prime": "6d518facea11f0601663db951a03bfcaa9790bfd7edfdd33ae81089de5a8c734",
    "prime_list_strictly_increasing": "3f5496bc64b968f967791192cf2d11b65e1de916b9e24ddbedb83163a8f75431",
    "first_primes_list_exists": "4427d0ffd64799cd180d0c99e4084a39db1023c734a88c77f840c2d59a215d7b",
    "gaussian_signed_euclidean_division_exists": "b74e03b044aac9c837f2098ad4e3d75a977fddf0d331ae84e02d440d422c91d8",
    "gaussian_euclidean_division_exists": "7c20ce64493b15888f961ece2d86e97171370aee53e8517ee21db8d53d82fd10",
    "gaussian_norm_exists_unique": "452d832311908cb4fca7139b9147039b0a05331967073d0b1743117f510599fd",
    "gaussian_add_exists": "af126fdb2cc45f1f1b2620570ac6e6759b4e3118a25acaa96862b53971ec255d",
    "gaussian_multiply_exists": "3ded8b89b9624cb91cd7a7eb23ea6a2921aa912aba4dc6a8c35d8d308d3971d0",
    "gaussian_norm_multiply": "b9f32039576506c3cabe3efcb762725f554089562b866d504fb0f92187159c64",
    "gaussian_representation_zero_iff": "7fa8a228116bfb6de5d50cd5782c6e33cc4e659ff2a2c4725d0979e77f0d6a08",
    "eisenstein_signed_euclidean_division_exists": "481e8a8d2b7dc8431901e86b902b578a144c8aa72133a5e5e6b4b6c8c5e44725",
    "eisenstein_euclidean_division_exists": "160d72250ab01db0ed32ca57bc472fd22d5ea307e4042815397cc771c3e102a9",
    "eisenstein_norm_exists": "e6d89e5a8fe3273d17fa59ff1f1f8df4011980acfc8ed776174a95edaa13cf24",
    "eisenstein_norm_functional": "887f9714c16a4ef5214f55c99765f59e34790e513d78487079ed0dd7b8e79463",
    "eisenstein_add_exists": "d4eef68809aa569e91530014909f8b0f27df7cb44d02d499c43403b89cbef319",
    "eisenstein_add_functional": "352350308e61675c50d3d6f9ed650738a0c23a0d42b64dbcd75e8796667d12d8",
    "eisenstein_multiply_exists": "06cca39ddb2e8b5d18210bf0ed9a24e36653bee25af58920a1ac1cca363ab482",
    "eisenstein_multiply_functional": "dbb42ca73f3287a28cdda7151f5e6fb4382429e74a2067d9e719d20d65724387",
    "eisenstein_norm_multiply": "42d3bea19f1c39be902a69da5b51c89dc4acef875a41d63dc46d20eef932e340",
}


def _validate_parent() -> None:
    if (
        len(v27.ALPHA_ENTRIES) != PARENT_ALPHA_V27_COUNT
        or len(v27.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V27_COUNT
        or v27.ALPHA_V27_ENROLLMENT_SHA256 != PARENT_ALPHA_V27_ENROLLMENT_SHA256
        or v27.ALPHA_V27_IDENTITY_SHA256 != PARENT_ALPHA_V27_IDENTITY_SHA256
        or len(v27.STABLE_SPECS) != 432
    ):
        raise AlphaV28EnrollmentError("immutable completely checked Alpha-v27 parent changed")


@lru_cache(maxsize=1)
def alpha_v28_enrollment() -> AlphaV28Enrollment:
    if (
        FRONTIER_V28_EXPECTED_COUNT <= 0
        or FRONTIER_V28_EXPECTED_EDGE_COUNT <= 0
        or len(FRONTIER_V28_EXPECTED_NAMES_SHA256) != 64
        or any(count <= 0 for count in EXPECTED_FACTORY_COUNTS.values())
        or any(count <= 0 for count in EXPECTED_CAMPAIGN_COUNTS.values())
    ):
        raise AlphaV28EnrollmentError("Alpha-v28 reviewed inventory is not sealed for admission")
    _validate_parent()
    if tuple(owner.module for owner in FACTORIES) != tuple(EXPECTED_FACTORY_COUNTS):
        raise AlphaV28EnrollmentError("reviewed Alpha-v28 factory inventory or order changed")
    available = {entry.spec.name for entry in v27.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV28Campaign] = {}

    for owner in FACTORIES:
        if (
            owner.factory != f"make_{owner.module}_theorems"
            or not owner.rfc.endswith("-rfc-v1.md")
            or "/" in owner.rfc or "\\" in owner.rfc or ".." in owner.rfc
        ):
            raise AlphaV28EnrollmentError("reviewed Alpha-v28 factory metadata changed")
        try:
            campaign = FrontierV28Campaign(owner.campaign)
            module = import_module(f".{owner.module}", package=__package__)
            candidates = tuple(getattr(module, owner.factory)(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV28EnrollmentError(
                f"unavailable reviewed Alpha-v28 factory {owner.module}.{owner.factory}"
            ) from error
        if len(candidates) != EXPECTED_FACTORY_COUNTS[owner.module]:
            raise AlphaV28EnrollmentError(
                f"exact Alpha-v28 factory cardinality changed: {owner.module}"
            )
        for item in candidates:
            if type(item) is not TheoremSpec or item.name in available:
                raise AlphaV28EnrollmentError("invalid or duplicate additive Alpha-v28 theorem")
            missing = set(item.dependencies).difference(available)
            if missing or len(set(item.dependencies)) != len(item.dependencies):
                raise AlphaV28EnrollmentError(
                    f"invalid Alpha-v28 dependencies for {item.name!r}: {sorted(missing)!r}"
                )
            if not item.script or any(
                "DNE" in command or command.startswith("use ") for command in item.script
            ):
                raise AlphaV28EnrollmentError(
                    f"Alpha-v28 theorem lacks an explicit constructive script: {item.name!r}"
                )
            _closed_formula(item.statement)
            sources[item.name] = f"peano-lab/py/peano_lab/library/{owner.module}.py"
            tests[item.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfcs[item.name] = f"research/arithmetic-library/{owner.rfc}"
            campaigns[item.name] = campaign
            rows.append(item)
            available.add(item.name)

    if Counter(campaigns.values()) != EXPECTED_CAMPAIGN_COUNTS:
        raise AlphaV28EnrollmentError("exact Alpha-v28 aggregate campaign cardinalities changed")
    if FRONTIER_V28_EXPECTED_COUNT and (
        len(rows) != FRONTIER_V28_EXPECTED_COUNT
        or sum(len(item.dependencies) for item in rows) != FRONTIER_V28_EXPECTED_EDGE_COUNT
        or sha256("\n".join(item.name for item in rows).encode()).hexdigest()
        != FRONTIER_V28_EXPECTED_NAMES_SHA256
    ):
        raise AlphaV28EnrollmentError("exact additive Alpha-v28 lower-layer frontier changed")
    by_name = {item.name: item for item in rows}
    for name, expected in ROOT_STATEMENT_SHA256.items():
        actual = by_name.get(name)
        if actual is None or sha256(actual.statement.encode()).hexdigest() != expected:
            raise AlphaV28EnrollmentError(f"exact Alpha-v28 campaign root changed: {name}")

    return AlphaV28Enrollment(
        parent_entries=v27.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(sources),
        test_by_name=MappingProxyType(tests),
        rfc_by_name=MappingProxyType(rfcs),
        campaign_by_name=MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV28Enrollment", "AlphaV28EnrollmentError", "EXPECTED_CAMPAIGN_COUNTS",
    "EXPECTED_FACTORY_COUNTS", "FRONTIER_V28_EXPECTED_COUNT",
    "FRONTIER_V28_EXPECTED_EDGE_COUNT", "FRONTIER_V28_EXPECTED_NAMES_SHA256",
    "FrontierV28Campaign", "PARENT_ALPHA_V27_COUNT",
    "PARENT_ALPHA_V27_ENROLLMENT_SHA256", "PARENT_ALPHA_V27_IDENTITY_SHA256",
    "ROOT_STATEMENT_SHA256", "alpha_v28_enrollment",
)
