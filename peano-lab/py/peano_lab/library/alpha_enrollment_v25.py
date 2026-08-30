"""Strict additive breakthrough enrollment over the immutable Alpha-v24 edition.

Enrollment is not proof evidence: a candidate receives checked-use authority
only after its complete actual dependency cone is accepted by the unchanged
Heyting-arithmetic kernel and the independent Lean bundle verifier.  The seals
below are deliberately empty during construction and will be frozen only after
all three mathematical campaigns have passed their original-kernel audits.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from . import editions_v24 as v24
from .theorems import TheoremSpec, _closed_formula


class AlphaV25EnrollmentError(ValueError):
    """The frozen parent, reviewed proof factory, or dependency DAG changed."""


class FrontierV25Campaign(str, Enum):
    MATRIX_COFACTOR_EXPANSION = "matrix_cofactor_expansion"
    POLYNOMIAL_TAYLOR_HENSEL = "polynomial_taylor_hensel"
    GENERALIZED_CRT_COMPATIBILITY = "generalized_crt_compatibility"


@dataclass(frozen=True, slots=True)
class AlphaV25Enrollment:
    parent_entries: tuple[v24.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV25Campaign]


PARENT_ALPHA_V24_COUNT = 2_008
PARENT_ALPHA_V24_ENROLLMENT_SHA256 = (
    "7463b938ffb87fe85eea6cd0e40c10ac73c799087ca1c408a070fcbe2687d4e1"
)
PARENT_ALPHA_V24_IDENTITY_SHA256 = (
    "1f4390b8ca5784ece54857fa666007f884b79e2670ef8bb32b2710c10f298a1b"
)

# These exact seals cover only actual original-kernel-checked constructive rows.
FRONTIER_V25_EXPECTED_COUNT = 72
FRONTIER_V25_EXPECTED_EDGE_COUNT = 210
FRONTIER_V25_EXPECTED_NAMES_SHA256 = (
    "28e37959781f86e7dc22e242963a9e7a4d834110d18e80f0c2a691547833c265"
)
EXPECTED_CAMPAIGN_COUNTS: dict[FrontierV25Campaign, int] = {
    FrontierV25Campaign.MATRIX_COFACTOR_EXPANSION: 29,
    FrontierV25Campaign.POLYNOMIAL_TAYLOR_HENSEL: 19,
    FrontierV25Campaign.GENERALIZED_CRT_COMPATIBILITY: 24,
}
ROOT_STATEMENT_SHA256: dict[str, str] = {
    "signed_cofactor_minor_family_exists": (
        "8486fcb74e3c32d6967e4ec4a3058c06ef7d2a6b031551e0722f73ce62b0355c"
    ),
    "signed_alternating_cofactor_fold_exists_unique": (
        "cded0e0b36963f8d799d0b1a2d5a89b58ca00219d40e378bdd31cfc58addfbd5"
    ),
    "signed_first_row_cofactor_fold_exists": (
        "f39d7ee0acfd090d87e144b68d18ed7cb61aee9bc29dc9087c9b8f440974eb73"
    ),
    "signed_matrix_cofactor_family_and_fold_exists": (
        "1f013b934c7540f73e135257094d612345f43f3163b5ee7280dbe97f4f142d2a"
    ),
    "beta_horner_eval_mod_congruence": (
        "dfd08efce5a7956818a6ae16d57d51a06f04625bd6fe7cf86322b413a421e085"
    ),
    "beta_horner_derivative_mod_congruence": (
        "75e0e5ba874eafcc31d275521728a51b9634f6c97692fb75e2da5ebd858c992d"
    ),
    "beta_horner_taylor_remainder_exists": (
        "5df4c9bd62d28df38c7fdcd0daf41c5fddf518942db92a74ac3a17676033ed82"
    ),
    "hensel_correction_exists_unique": (
        "116197e3bebc5a3e2ee9290c2826b209e4d7f3047121533cc22c8e32324c3d70"
    ),
    "beta_horner_hensel_lift_divisibility": (
        "9ddf76110a1036269b8a07f6d80cd83bd26ea3ed7c6416508e1193dc7bbc506b"
    ),
    "beta_horner_hensel_lift_exists": (
        "9cfc4633ea27c492b0deb35a56fe44b25b8dbf50d56fb27f29285f74b6c58a8b"
    ),
    "crt_prefix_solution_implies_pairwise_compatible": (
        "4b114040f7ff0a3e9e98279d8600d587741ebedcd598de06f2d899caad6fde1d"
    ),
    "crt_merge_compatible_prefix_solution_exists": (
        "1e30822d43996807abe877aa76d88026a59c293dfe440ed00461e6a4eb17acc9"
    ),
    "crt_merge_compatible_prefix_canonical_exists_unique": (
        "9e3d68192e707b5953b2fd3c9e4716e9fe90317f63be49734bbed00e3492b927"
    ),
    "crt_is_gcd_scale": (
        "abe947735d13b946283776bfb832f7f0e8dc17861fbd0850c5b7b51827d68f77"
    ),
    "crt_is_gcd_coprime_product": (
        "e3b28cbcdf65cdad1e51c834812bf2efb8a45cb534bb8a5daa1e4245b4d0a347"
    ),
    "crt_gcd_lcm_distributes_divisibility": (
        "0ac6861e424c4c961810fe6565850227601a3c79438256678a50f8df25a544dd"
    ),
    "crt_pairwise_compatible_dominating_last_canonical_exists_unique": (
        "f249f7835eb127e8d5f15e74b3d4344d5d98503d8b01394d608bf2e677823fb0"
    ),
}


@dataclass(frozen=True, slots=True)
class _Factory:
    campaign: FrontierV25Campaign
    module: str
    factory: str
    rfc: str


_FACTORIES = (
    _Factory(
        FrontierV25Campaign.MATRIX_COFACTOR_EXPANSION,
        "matrix_cofactor_expansion_candidate",
        "make_matrix_cofactor_expansion_candidate_theorems",
        "research/arithmetic-library/matrix-cofactor-expansion-rfc-v1.md",
    ),
    _Factory(
        FrontierV25Campaign.POLYNOMIAL_TAYLOR_HENSEL,
        "polynomial_taylor_hensel_candidate",
        "make_polynomial_taylor_hensel_candidate_theorems",
        "research/arithmetic-library/polynomial-taylor-hensel-rfc-v1.md",
    ),
    _Factory(
        FrontierV25Campaign.GENERALIZED_CRT_COMPATIBILITY,
        "generalized_crt_compatibility_candidate",
        "make_generalized_crt_compatibility_candidate_theorems",
        "research/arithmetic-library/generalized-crt-compatibility-rfc-v1.md",
    ),
)


def _validate_parent() -> None:
    if (
        len(v24.ALPHA_ENTRIES) != PARENT_ALPHA_V24_COUNT
        or len(v24.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V24_COUNT
        or v24.ALPHA_V24_ENROLLMENT_SHA256 != PARENT_ALPHA_V24_ENROLLMENT_SHA256
        or v24.ALPHA_V24_IDENTITY_SHA256 != PARENT_ALPHA_V24_IDENTITY_SHA256
        or len(v24.STABLE_SPECS) != 432
    ):
        raise AlphaV25EnrollmentError("immutable completely checked Alpha-v24 parent changed")


@lru_cache(maxsize=1)
def alpha_v25_enrollment() -> AlphaV25Enrollment:
    _validate_parent()
    available = {entry.spec.name for entry in v24.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV25Campaign] = {}

    for owner in _FACTORIES:
        try:
            module = import_module(f".{owner.module}", package=__package__)
            candidates = tuple(getattr(module, owner.factory)(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV25EnrollmentError(
                f"unavailable reviewed Alpha-v25 factory {owner.module}.{owner.factory}"
            ) from error
        expected = EXPECTED_CAMPAIGN_COUNTS[owner.campaign]
        if expected and len(candidates) != expected:
            raise AlphaV25EnrollmentError(
                f"exact Alpha-v25 campaign cardinality changed: {owner.campaign.value}"
            )
        for item in candidates:
            if type(item) is not TheoremSpec or item.name in available:
                raise AlphaV25EnrollmentError("invalid or duplicate additive Alpha-v25 theorem")
            missing = set(item.dependencies).difference(available)
            if missing:
                raise AlphaV25EnrollmentError(
                    f"forward Alpha-v25 dependencies for {item.name!r}: {sorted(missing)!r}"
                )
            if not item.script or any(
                "DNE" in command or command.startswith("use ") for command in item.script
            ):
                raise AlphaV25EnrollmentError(
                    f"Alpha-v25 theorem lacks an explicit constructive script: {item.name!r}"
                )
            _closed_formula(item.statement)
            sources[item.name] = f"peano-lab/py/peano_lab/library/{owner.module}.py"
            tests[item.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfcs[item.name] = owner.rfc
            campaigns[item.name] = owner.campaign
            rows.append(item)
            available.add(item.name)

    if FRONTIER_V25_EXPECTED_COUNT and (
        len(rows) != FRONTIER_V25_EXPECTED_COUNT
        or sum(len(item.dependencies) for item in rows) != FRONTIER_V25_EXPECTED_EDGE_COUNT
        or sha256("\n".join(item.name for item in rows).encode()).hexdigest()
        != FRONTIER_V25_EXPECTED_NAMES_SHA256
    ):
        raise AlphaV25EnrollmentError("exact additive Alpha-v25 breakthrough frontier changed")
    by_name = {item.name: item for item in rows}
    for name, expected in ROOT_STATEMENT_SHA256.items():
        actual = by_name.get(name)
        if actual is None or sha256(actual.statement.encode()).hexdigest() != expected:
            raise AlphaV25EnrollmentError(f"exact Alpha-v25 campaign root changed: {name}")

    return AlphaV25Enrollment(
        parent_entries=v24.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(sources),
        test_by_name=MappingProxyType(tests),
        rfc_by_name=MappingProxyType(rfcs),
        campaign_by_name=MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV25Enrollment",
    "AlphaV25EnrollmentError",
    "EXPECTED_CAMPAIGN_COUNTS",
    "FRONTIER_V25_EXPECTED_COUNT",
    "FRONTIER_V25_EXPECTED_EDGE_COUNT",
    "FRONTIER_V25_EXPECTED_NAMES_SHA256",
    "FrontierV25Campaign",
    "PARENT_ALPHA_V24_COUNT",
    "PARENT_ALPHA_V24_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V24_IDENTITY_SHA256",
    "ROOT_STATEMENT_SHA256",
    "alpha_v25_enrollment",
)
