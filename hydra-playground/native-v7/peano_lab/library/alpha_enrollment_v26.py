"""Strict additive first-wave enrollment over the immutable Alpha-v25 edition.

Enrollment is not proof evidence: a candidate receives checked-use authority
only after its complete actual dependency cone is accepted by the unchanged
Heyting-arithmetic kernel and the independent Lean bundle verifier. Every
theorem inventory and root statement below is frozen after all three
mathematical campaigns passed their original-kernel audits.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from . import editions_v25 as v25
from .theorems import TheoremSpec, _closed_formula


class AlphaV26EnrollmentError(ValueError):
    """The frozen parent, reviewed proof factory, or dependency DAG changed."""


class FrontierV26Campaign(str, Enum):
    COPRIME_SQUARE_FACTOR = "coprime_square_factor"
    PYTHAGOREAN_INVERSE = "pythagorean_inverse"
    FERMAT_FOUR_DESCENT = "fermat_four_descent"


@dataclass(frozen=True, slots=True)
class AlphaV26Enrollment:
    parent_entries: tuple[v25.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV26Campaign]


PARENT_ALPHA_V25_COUNT = 2_080
PARENT_ALPHA_V25_ENROLLMENT_SHA256 = (
    "f724872707cdcf401f35cb69680e1bbec86d626c4bf56e6d41f01a3724e2be81"
)
PARENT_ALPHA_V25_IDENTITY_SHA256 = (
    "3516d4730428c79fc73aa6fbdbabc43d93921471941bb2f144ea3d29e0af5b28"
)

# Exact completed square-factor, primitive-inverse, and Fermat-descent rows.
FRONTIER_V26_EXPECTED_COUNT = 58
FRONTIER_V26_EXPECTED_EDGE_COUNT = 218
FRONTIER_V26_EXPECTED_NAMES_SHA256 = "226cc91137521e0484dc6c3dcf90d2138e67acc79bf53798d84fb0deaf5973de"
EXPECTED_CAMPAIGN_COUNTS: dict[FrontierV26Campaign, int] = {
    FrontierV26Campaign.COPRIME_SQUARE_FACTOR: 9,
    FrontierV26Campaign.PYTHAGOREAN_INVERSE: 23,
    FrontierV26Campaign.FERMAT_FOUR_DESCENT: 26,
}
ROOT_STATEMENT_SHA256: dict[str, str] = {
    "square_eq_injective": "0c01cdf647c9957d5522adf164644cab008de48ff22e5c18478d49c012ceaa60",
    "coprime_square_product_factors": "f23a9cdd943c2643d3c3c3b208b34d731715b3e316add8b4a430ec06f8361dca",
    "square_divides_square_root": "b6a82134f1758f33b30be0b733f4910c784805f0ee871400b9e4e0cc4e982b0f",
    "pythagorean_primitive_odd_even_inverse": "b926982a720ad0f6cba2184dbb851f072f4f5c69a152b7c0c5e40f448313646f",
    "pythagorean_positive_primitive_inverse": "52637d9c57c28d1875f272b93a815aa22ba1d05c066be0642d44721f1903ae85",
    "pythagorean_positive_primitive_classification": "df3bd4829643a3900cee8f78fc7b4b242a0fb935f8e29e1b4d2b7e18bdac387f",
    "fermat_four_primitive_normalization": "cc973a8899e25fcdd918ae57abfb71a29e25cf64056588f3f755231a3ff4902a",
    "fermat_four_strict_descent_proved": "a3d8f109acbc3a7a254ad16d0bd5560807da349e8e7d6dabc5bb727dbafde85e",
    "fermat_four_no_square": "2931b656d7b3fa9d5a7abb43237803705f1871882fa07e14f5caac2d7d348786",
    "fermat_four_no_fourth": "9c058a04f2efb7f105017c15d34a94522937627b0008a4ea06305b66e0077cde",
    "fermat_four_complete_classification": "92c99d3f0a218c2706416d7c8b362aee310df0db1180729b85165d4ab11788bd",
    "fermat_four_positive_sum_not_square": "ae59505ab1243e444869a6385357022e648728cb483e36ae9f97a1f0a404409b",
}


@dataclass(frozen=True, slots=True)
class _Factory:
    campaign: FrontierV26Campaign
    module: str
    factory: str
    rfc: str


_FACTORIES = (
    _Factory(
        FrontierV26Campaign.COPRIME_SQUARE_FACTOR,
        "coprime_square_factor_candidate",
        "make_coprime_square_factor_candidate_theorems",
        "research/arithmetic-library/coprime-square-factor-rfc-v1.md",
    ),
    _Factory(
        FrontierV26Campaign.PYTHAGOREAN_INVERSE,
        "pythagorean_inverse_candidate",
        "make_pythagorean_inverse_candidate_theorems",
        "research/arithmetic-library/pythagorean-inverse-rfc-v1.md",
    ),
    _Factory(
        FrontierV26Campaign.FERMAT_FOUR_DESCENT,
        "fermat_four_descent_candidate",
        "make_fermat_four_descent_candidate_theorems",
        "research/arithmetic-library/fermat-four-descent-rfc-v1.md",
    ),
)


def _validate_parent() -> None:
    if (
        len(v25.ALPHA_ENTRIES) != PARENT_ALPHA_V25_COUNT
        or len(v25.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V25_COUNT
        or v25.ALPHA_V25_ENROLLMENT_SHA256 != PARENT_ALPHA_V25_ENROLLMENT_SHA256
        or v25.ALPHA_V25_IDENTITY_SHA256 != PARENT_ALPHA_V25_IDENTITY_SHA256
        or len(v25.STABLE_SPECS) != 432
    ):
        raise AlphaV26EnrollmentError("immutable completely checked Alpha-v25 parent changed")


@lru_cache(maxsize=1)
def alpha_v26_enrollment() -> AlphaV26Enrollment:
    _validate_parent()
    available = {entry.spec.name for entry in v25.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV26Campaign] = {}

    for owner in _FACTORIES:
        try:
            module = import_module(f".{owner.module}", package=__package__)
            candidates = tuple(getattr(module, owner.factory)(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV26EnrollmentError(
                f"unavailable reviewed Alpha-v26 factory {owner.module}.{owner.factory}"
            ) from error
        expected = EXPECTED_CAMPAIGN_COUNTS[owner.campaign]
        if expected and len(candidates) != expected:
            raise AlphaV26EnrollmentError(
                f"exact Alpha-v26 campaign cardinality changed: {owner.campaign.value}"
            )
        for item in candidates:
            if type(item) is not TheoremSpec or item.name in available:
                raise AlphaV26EnrollmentError("invalid or duplicate additive Alpha-v26 theorem")
            missing = set(item.dependencies).difference(available)
            if missing:
                raise AlphaV26EnrollmentError(
                    f"forward Alpha-v26 dependencies for {item.name!r}: {sorted(missing)!r}"
                )
            if not item.script or any(
                "DNE" in command or command.startswith("use ") for command in item.script
            ):
                raise AlphaV26EnrollmentError(
                    f"Alpha-v26 theorem lacks an explicit constructive script: {item.name!r}"
                )
            _closed_formula(item.statement)
            sources[item.name] = f"peano-lab/py/peano_lab/library/{owner.module}.py"
            tests[item.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfcs[item.name] = owner.rfc
            campaigns[item.name] = owner.campaign
            rows.append(item)
            available.add(item.name)

    if FRONTIER_V26_EXPECTED_COUNT and (
        len(rows) != FRONTIER_V26_EXPECTED_COUNT
        or sum(len(item.dependencies) for item in rows) != FRONTIER_V26_EXPECTED_EDGE_COUNT
        or sha256("\n".join(item.name for item in rows).encode()).hexdigest()
        != FRONTIER_V26_EXPECTED_NAMES_SHA256
    ):
        raise AlphaV26EnrollmentError("exact additive Alpha-v26 first-wave frontier changed")
    by_name = {item.name: item for item in rows}
    for name, expected in ROOT_STATEMENT_SHA256.items():
        actual = by_name.get(name)
        if actual is None or sha256(actual.statement.encode()).hexdigest() != expected:
            raise AlphaV26EnrollmentError(f"exact Alpha-v26 campaign root changed: {name}")

    return AlphaV26Enrollment(
        parent_entries=v25.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(sources),
        test_by_name=MappingProxyType(tests),
        rfc_by_name=MappingProxyType(rfcs),
        campaign_by_name=MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV26Enrollment",
    "AlphaV26EnrollmentError",
    "EXPECTED_CAMPAIGN_COUNTS",
    "FRONTIER_V26_EXPECTED_COUNT",
    "FRONTIER_V26_EXPECTED_EDGE_COUNT",
    "FRONTIER_V26_EXPECTED_NAMES_SHA256",
    "FrontierV26Campaign",
    "PARENT_ALPHA_V25_COUNT",
    "PARENT_ALPHA_V25_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V25_IDENTITY_SHA256",
    "ROOT_STATEMENT_SHA256",
    "alpha_v26_enrollment",
)
