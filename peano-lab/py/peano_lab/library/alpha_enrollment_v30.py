"""Strict additive Gaussian-factorization enrollment over the immutable Alpha-v29 edition.

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

from . import editions_v29 as v29
from .campaign_gaussian_factorization_closure import FACTORIES, _specs_digest
from .theorems import TheoremSpec, _closed_formula


class AlphaV30EnrollmentError(ValueError):
    """The frozen parent, reviewed proof factory, or dependency DAG changed."""


class FrontierV30Campaign(str, Enum):
    GAUSSIAN_FACTORIZATION = "gaussian_factorization"


@dataclass(frozen=True, slots=True)
class AlphaV30Enrollment:
    parent_entries: tuple[v29.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV30Campaign]


PARENT_ALPHA_V29_COUNT = 3_042
PARENT_ALPHA_V29_ENROLLMENT_SHA256 = (
    "feac02afbfe516116accd30a6a117060f5d5cd99d608971a7f62bd1f3787104d"
)
PARENT_ALPHA_V29_IDENTITY_SHA256 = (
    "57da70c3718579cb8eb81c59a4c2898a5071140fa944e31bca312fe53432574c"
)

# Exact frozen Gaussian specifications; the complete artifact must independently
# pass the original kernel and compiled Lean. Metadata alone is never a proof.
FRONTIER_V30_EXPECTED_COUNT = 180
FRONTIER_V30_EXPECTED_EDGE_COUNT = 673
FRONTIER_V30_EXPECTED_NAMES_SHA256 = "0894c4ef5f36b631a424c74d4119bd538f790245fd5e9dfb25c682e0c05e16fa"
FRONTIER_V30_EXPECTED_SPECS_SHA256 = "c2072a3d9e07b3e64813e8234522e5f2c606a7be79efe03c22b730ae1ca0cd46"
EXPECTED_FACTORY_METADATA_SHA256 = "e31f0c584cac4c227232bd2b59062395f7b6dc64e5d2764aa2d0da0d6a72bd48"
EXPECTED_CAMPAIGN_COUNTS: dict[FrontierV30Campaign, int] = {
    FrontierV30Campaign.GAUSSIAN_FACTORIZATION: 180,
}
EXPECTED_FACTORY_COUNTS: dict[str, int] = {
    "gaussian_ring_candidate": 65,
    "gaussian_divisibility_candidate": 29,
    "gaussian_gcd_candidate": 14,
    "gaussian_factor_search_candidate": 23,
    "gaussian_factorization_candidate": 28,
    "gaussian_product_reindex_candidate": 3,
    "gaussian_factor_permutation_candidate": 18
}
EXPECTED_FACTORY_SOURCE_SHA256: dict[str, str] = {
    "gaussian_ring_candidate": "7e6d4a3ba15f7190047e656d91a2a0f781e6a24ab055ebcf7bc0efc6d15d3e44",
    "gaussian_divisibility_candidate": "ce5d6fd7d38504d2d6cd050e38bccef4b6a504f8ecb49f8ca86e78aaace48747",
    "gaussian_gcd_candidate": "da72285e399ece582e3ececadf660cb71936e293627b75849410f6022946ef33",
    "gaussian_factor_search_candidate": "039bb7e5d7bb3c3fe1acd3177904c99c62ecfd78424685e78c8c5dc28cd1b6ce",
    "gaussian_factorization_candidate": "cb95534689e6155fdbb1a7e80be843bdd91153504f9b5df99bf6ee59e77e8d1e",
    "gaussian_product_reindex_candidate": "7a5b5d0b19aa8217fab943d215b859e031bada36f7eebc1409c0949b99b33f2c",
    "gaussian_factor_permutation_candidate": "13d404c9870cf2ef2fb089749f60224b858d2954ec581bb37b09320c23055f1f"
}
ROOT_STATEMENT_SHA256: dict[str, str] = {
    "gaussian_unit_iff_norm_one": "1c480f8f6989ba91bf2103bec39c839a75aa0b3026dc5314b8141643c178a6e7",
    "gaussian_divides_input_valid": "51aedd3767e25d58e936a98a37f4ec1a9b59c95be1976d3bff6b2592bc58ed6e",
    "gaussian_divides_value_valid": "75c9826a99881c9e9ea45b6947fe64d07aa7cac2d054bc0b0b34635e06bccc74",
    "gaussian_divides_product_right": "c667470627951c96a2d2164cf79a963e66516ed7d2918f69d33a15be79478bdd",
    "gaussian_unit_divides": "f652687bfc69e1eef958ea56e0708fa5be0dfd73929fde4bcc7bb031c2d04a97",
    "gaussian_divides_decidable": "c008dfc3987d6c5565c6f85a23eb9ce2b618f58b327d1336039bfde9fb606569",
    "gaussian_associate_reflexive": "7374976c09975f92cde7f3213b1a2b6bd2fabdd3b1fbec5bff75b2f7a5a86596",
    "gaussian_associate_norm": "aaa4519eb61ce02f4d998c2d6760c348e99a5917163b90e961316c04557166f9",
    "gaussian_divisor_norm_bound": "f5d18361d3f4a6b7dd50809d625b8775dcf964e1c57f03c91db76c1939012cad",
    "gaussian_gcd_bezout_zero_right": "5b8d4b9317e0c9cbbe61b8b952a01fd32d43769f28c7c192b53a02a133dd2e15",
    "gaussian_common_divisor_of_bezout": "be7b180bfff891f64f847a70791c677947f0f50876c8821eb4964d757ea34c9e",
    "gaussian_gcd_bezout_exists": "67d09aa8ff5c895839b29eb5f9f44d9d91087f8f2316698b47530795b800f981",
    "gaussian_gcd_unique_up_to_associate": "2ea8e4c57a49cecb2aee00f5611ef247500d39fe0f1fc1b239b478a49bd3a7c5",
    "gaussian_irreducible_dvd_product": "e2fb26736c7080feea9c73498dc0609b2e08cfdd89bdf16857afd0e6a9eb7620",
    "gaussian_irreducible_iff_prime": "aa8c5f0706fbabf6c9069ae0fd2a7f7b3ecf9651b30bad9d7b4483fbd6d2689e",
    "gaussian_irreducible_decidable": "d2dda07b5adbba8a24df4aacbc1921b52c969822b96f7bbd9a61b484784bc3e9",
    "gaussian_prime_factorization_exists": "86d207a622593e87fc60e4c852a6aabb8e6b1057b960cbadc7e2ac736aae827b",
    "gaussian_factorization_value_valid": "287c3e10b11f20850b983fccafccff71dcd688966eabc0aecaf62ea187092edb",
    "gaussian_product_replace_balance_iff": "f9b481d187747f5c3084772a722011398d5f5692e2b7174f8a2d9215505c0f7c",
    "gaussian_unique_prime_factorization": "57abdbebab6835ebe1fecb15f4229f2eee579b7d67c22638345cc0deb6e20219",
    "gaussian_zero_has_no_prime_factorization": "98f2d733c8b7cab7fce0324135b3985336b1cb9922936d723adf48379a213034",
    "gaussian_unit_prime_factorization_length_zero": "66bcf4d61ae664d21b59e77b66203fe3b2cffb1d360d4263f228984dd2f66b1b"
}


def _validate_parent() -> None:
    if (
        len(v29.ALPHA_ENTRIES) != PARENT_ALPHA_V29_COUNT
        or len(v29.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V29_COUNT
        or v29.ALPHA_V29_ENROLLMENT_SHA256 != PARENT_ALPHA_V29_ENROLLMENT_SHA256
        or v29.ALPHA_V29_IDENTITY_SHA256 != PARENT_ALPHA_V29_IDENTITY_SHA256
        or len(v29.STABLE_SPECS) != 432
    ):
        raise AlphaV30EnrollmentError("immutable completely checked Alpha-v29 parent changed")


@lru_cache(maxsize=1)
def alpha_v30_enrollment() -> AlphaV30Enrollment:
    if (
        FRONTIER_V30_EXPECTED_COUNT <= 0
        or FRONTIER_V30_EXPECTED_EDGE_COUNT <= 0
        or len(FRONTIER_V30_EXPECTED_NAMES_SHA256) != 64
        or len(FRONTIER_V30_EXPECTED_SPECS_SHA256) != 64
        or len(EXPECTED_FACTORY_METADATA_SHA256) != 64
        or any(count <= 0 for count in EXPECTED_FACTORY_COUNTS.values())
        or any(count <= 0 for count in EXPECTED_CAMPAIGN_COUNTS.values())
    ):
        raise AlphaV30EnrollmentError("Alpha-v30 reviewed inventory is not sealed for admission")
    _validate_parent()
    if tuple(owner.module for owner in FACTORIES) != tuple(EXPECTED_FACTORY_COUNTS):
        raise AlphaV30EnrollmentError("reviewed Alpha-v30 factory inventory or order changed")
    available = {entry.spec.name for entry in v29.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV30Campaign] = {}

    for owner in FACTORIES:
        if (
            owner.factory != f"make_{owner.module}_theorems"
            or not owner.rfc.endswith("-rfc-v1.md")
            or "/" in owner.rfc or "\\" in owner.rfc or ".." in owner.rfc
            or owner.source_sha256 != EXPECTED_FACTORY_SOURCE_SHA256.get(owner.module)
        ):
            raise AlphaV30EnrollmentError("reviewed Alpha-v30 factory metadata changed")
        try:
            campaign = FrontierV30Campaign(owner.campaign)
            module = import_module(f".{owner.module}", package=__package__)
            candidates = tuple(getattr(module, owner.factory)(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV30EnrollmentError(
                f"unavailable reviewed Alpha-v30 factory {owner.module}.{owner.factory}"
            ) from error
        if len(candidates) != EXPECTED_FACTORY_COUNTS[owner.module]:
            raise AlphaV30EnrollmentError(
                f"exact Alpha-v30 factory cardinality changed: {owner.module}"
            )
        for item in candidates:
            if type(item) is not TheoremSpec or item.name in available:
                raise AlphaV30EnrollmentError("invalid or duplicate additive Alpha-v30 theorem")
            missing = set(item.dependencies).difference(available)
            if missing or len(set(item.dependencies)) != len(item.dependencies):
                raise AlphaV30EnrollmentError(
                    f"invalid Alpha-v30 dependencies for {item.name!r}: {sorted(missing)!r}"
                )
            if not item.script or any(
                "DNE" in command or command.startswith(("use ", "admit", "sorry")) for command in item.script
            ):
                raise AlphaV30EnrollmentError(
                    f"Alpha-v30 theorem lacks an explicit constructive script: {item.name!r}"
                )
            _closed_formula(item.statement)
            sources[item.name] = f"peano-lab/py/peano_lab/library/{owner.module}.py"
            tests[item.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfcs[item.name] = f"research/arithmetic-library/{owner.rfc}"
            campaigns[item.name] = campaign
            rows.append(item)
            available.add(item.name)

    if Counter(campaigns.values()) != EXPECTED_CAMPAIGN_COUNTS:
        raise AlphaV30EnrollmentError("exact Alpha-v30 aggregate campaign cardinalities changed")
    factory_metadata = json.dumps(
        [(f.campaign, f.module, f.factory, f.rfc, f.source_sha256) for f in FACTORIES],
        separators=(",", ":"),
    )
    if sha256(factory_metadata.encode()).hexdigest() != EXPECTED_FACTORY_METADATA_SHA256:
        raise AlphaV30EnrollmentError("exact Alpha-v30 reviewed factory metadata changed")
    if FRONTIER_V30_EXPECTED_COUNT and (
        len(rows) != FRONTIER_V30_EXPECTED_COUNT
        or sum(len(item.dependencies) for item in rows) != FRONTIER_V30_EXPECTED_EDGE_COUNT
        or sha256("\n".join(item.name for item in rows).encode()).hexdigest()
        != FRONTIER_V30_EXPECTED_NAMES_SHA256
        or _specs_digest(tuple(rows)) != FRONTIER_V30_EXPECTED_SPECS_SHA256
    ):
        raise AlphaV30EnrollmentError("exact additive Alpha-v30 Gaussian-factorization frontier changed")
    by_name = {item.name: item for item in rows}
    for name, expected in ROOT_STATEMENT_SHA256.items():
        actual = by_name.get(name)
        if actual is None or sha256(actual.statement.encode()).hexdigest() != expected:
            raise AlphaV30EnrollmentError(f"exact Alpha-v30 campaign root changed: {name}")

    return AlphaV30Enrollment(
        parent_entries=v29.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(sources),
        test_by_name=MappingProxyType(tests),
        rfc_by_name=MappingProxyType(rfcs),
        campaign_by_name=MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV30Enrollment", "AlphaV30EnrollmentError", "EXPECTED_CAMPAIGN_COUNTS",
    "EXPECTED_FACTORY_COUNTS", "EXPECTED_FACTORY_SOURCE_SHA256", "FRONTIER_V30_EXPECTED_COUNT",
    "EXPECTED_FACTORY_METADATA_SHA256",
    "FRONTIER_V30_EXPECTED_EDGE_COUNT", "FRONTIER_V30_EXPECTED_NAMES_SHA256",
    "FRONTIER_V30_EXPECTED_SPECS_SHA256",
    "FrontierV30Campaign", "PARENT_ALPHA_V29_COUNT",
    "PARENT_ALPHA_V29_ENROLLMENT_SHA256", "PARENT_ALPHA_V29_IDENTITY_SHA256",
    "ROOT_STATEMENT_SHA256", "alpha_v30_enrollment",
)

