"""Strictly additive research-frontier enrollment over immutable Alpha v23.

The ordered specifications below grant no checked-use authority by themselves.
Every theorem must subsequently appear in a complete unchanged-kernel-checked
and independently Lean-verified proof certificate before an Alpha v24 release
can be sealed or exposed to the public theorem library.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from . import editions_v23 as v23
from .theorems import TheoremSpec, _closed_formula


class AlphaV24EnrollmentError(ValueError):
    """A frozen parent, reviewed theorem body, or dependency order changed."""


class FrontierV24Campaign(str, Enum):
    MATRIX_DETERMINANT_MINORS = "matrix_determinant_minors"
    POLYNOMIAL_HENSEL = "polynomial_hensel"
    GENERALIZED_CRT_FOLD = "generalized_crt_fold"


@dataclass(frozen=True, slots=True)
class AlphaV24Enrollment:
    parent_entries: tuple[v23.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV24Campaign]


PARENT_ALPHA_V23_COUNT = 1_949
PARENT_ALPHA_V23_ENROLLMENT_SHA256 = (
    "f5d94af7a11c642d7076a195e2e795e7b84c61a6de1a6b074708669b2dac1648"
)
PARENT_ALPHA_V23_IDENTITY_SHA256 = (
    "02059eef420eb96abd48c41bf62049a3cc69f025b00bed9dc3466e7eb2294a85"
)

# Zero and empty seals never authorize checked-use replay or release admission;
# freeze these only after every final candidate body is independently checked.
FRONTIER_V24_EXPECTED_COUNT = 59
FRONTIER_V24_EXPECTED_EDGE_COUNT = 138
FRONTIER_V24_EXPECTED_NAMES_SHA256 = (
    "e88ec1f9a1242c339565305bd7a866a0ec1e95a069f537af1712abf364433947"
)
EXPECTED_CAMPAIGN_COUNTS: dict[FrontierV24Campaign, int] = {
    FrontierV24Campaign.MATRIX_DETERMINANT_MINORS: 17,
    FrontierV24Campaign.POLYNOMIAL_HENSEL: 15,
    FrontierV24Campaign.GENERALIZED_CRT_FOLD: 27,
}
ROOT_STATEMENT_SHA256: dict[str, str] = {
    "beta_matrix_minor_exists": (
        "3abfa041aa3df531be6ac5580a3167802703e2adc4ecf13ae77f19309a31a8ee"
    ),
    "beta_signed_matrix_minor_exists": (
        "bf6e9238c2928e4f6525a14015198b673b41022924c6da1944ab87c8df61bba1"
    ),
    "signed_matrix_four_cofactor_expansion_exists": (
        "f1bf20e0ba8ca02fd964b85ea1b469923bf9c9e1bb320253ebbc456fea524486"
    ),
    "signed_matrix_four_full_determinant_exists": (
        "7ae77d34a56bc459140fcd9afab5bb70cf4792cdb6ebac833c448381adfff848"
    ),
    "signed_matrix_four_full_determinant_functional": (
        "d1987b1ba2337c22463858a07b85da4144d00f20f8e036c076d53d99de8ada59"
    ),
    "beta_horner_derivative_successor_decompose": (
        "042cb58aec7a7a63eaef9c83958feefbc51b1ce89e927010c2e9427f401b7435"
    ),
    "beta_horner_derivative_functional": (
        "48bf3276ce3057494e1e9b46aca2ea063b9937db4659a35d4f879ac09abec09f"
    ),
    "beta_horner_derivative_exists_unique": (
        "171b5939376bfb9e9ec9469d3addd98e27584931fa7994dccb4b372c4d9a693f"
    ),
    "beta_horner_derivative_only_exists_unique": (
        "60a8a62113371b7c5ae1784f965d107b6f985af1fb059438ff42a222b796447d"
    ),
    "crt_prefix_lcm_exists_unique": (
        "09fa610c42ac069677f4fb90f00c6e0780d2b1de843380599e725a9cf19e1175"
    ),
    "crt_pairwise_coprime_prefix_solution_exists": (
        "6e61d9a848010dc5857fdacbc8efc3973e160a997a421a17100a867e1c501e68"
    ),
    "crt_prefix_solution_class_iff_lcm": (
        "a943495e7c8817cf917f4cc282502ad316a2a3ce9892c5d6bb3ba2ab0fbd6488"
    ),
    "crt_pairwise_coprime_prefix_canonical_exists_unique": (
        "6d3913cdbd73b6a2662e31aea220a19ab75f0d1995e3fadf0c583c58d270e01f"
    ),
}


@dataclass(frozen=True, slots=True)
class _Factory:
    campaign: FrontierV24Campaign
    module: str
    factory: str
    rfc: str


_FACTORIES = (
    _Factory(
        FrontierV24Campaign.MATRIX_DETERMINANT_MINORS,
        "matrix_determinant_minors_candidate",
        "make_matrix_determinant_minors_candidate_theorems",
        "research/arithmetic-library/matrix-determinant-minors-rfc-v1.md",
    ),
    _Factory(
        FrontierV24Campaign.POLYNOMIAL_HENSEL,
        "polynomial_hensel_candidate",
        "make_polynomial_hensel_candidate_theorems",
        "research/arithmetic-library/polynomial-hensel-rfc-v1.md",
    ),
    _Factory(
        FrontierV24Campaign.GENERALIZED_CRT_FOLD,
        "generalized_crt_fold_candidate",
        "make_generalized_crt_fold_candidate_theorems",
        "research/arithmetic-library/generalized-crt-fold-rfc-v1.md",
    ),
)


def _validate_parent() -> None:
    if (
        len(v23.ALPHA_ENTRIES) != PARENT_ALPHA_V23_COUNT
        or len(v23.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V23_COUNT
        or v23.ALPHA_V23_ENROLLMENT_SHA256 != PARENT_ALPHA_V23_ENROLLMENT_SHA256
        or v23.ALPHA_V23_IDENTITY_SHA256 != PARENT_ALPHA_V23_IDENTITY_SHA256
        or len(v23.STABLE_SPECS) != 432
    ):
        raise AlphaV24EnrollmentError("immutable fully checked Alpha-v23 parent changed")


@lru_cache(maxsize=1)
def alpha_v24_enrollment() -> AlphaV24Enrollment:
    _validate_parent()
    available = {entry.spec.name for entry in v23.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV24Campaign] = {}

    for owner in _FACTORIES:
        try:
            module = import_module(f".{owner.module}", package=__package__)
            candidates = tuple(getattr(module, owner.factory)(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV24EnrollmentError(
                f"unavailable reviewed Alpha-v24 factory {owner.module}.{owner.factory}"
            ) from error
        expected = EXPECTED_CAMPAIGN_COUNTS[owner.campaign]
        if expected and len(candidates) != expected:
            raise AlphaV24EnrollmentError(
                f"exact Alpha-v24 campaign cardinality changed: {owner.campaign.value}"
            )
        for item in candidates:
            if type(item) is not TheoremSpec or item.name in available:
                raise AlphaV24EnrollmentError("invalid or duplicate Alpha-v24 theorem")
            missing = set(item.dependencies).difference(available)
            if missing:
                raise AlphaV24EnrollmentError(
                    f"forward Alpha-v24 dependencies for {item.name!r}: {sorted(missing)!r}"
                )
            if not item.script or any(
                "DNE" in command or command.startswith("use ") for command in item.script
            ):
                raise AlphaV24EnrollmentError(
                    f"Alpha-v24 theorem lacks an explicit constructive script: {item.name!r}"
                )
            _closed_formula(item.statement)
            sources[item.name] = f"peano-lab/py/peano_lab/library/{owner.module}.py"
            tests[item.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfcs[item.name] = owner.rfc
            campaigns[item.name] = owner.campaign
            rows.append(item)
            available.add(item.name)

    if FRONTIER_V24_EXPECTED_COUNT and (
        len(rows) != FRONTIER_V24_EXPECTED_COUNT
        or sum(len(item.dependencies) for item in rows) != FRONTIER_V24_EXPECTED_EDGE_COUNT
        or sha256("\n".join(item.name for item in rows).encode()).hexdigest()
        != FRONTIER_V24_EXPECTED_NAMES_SHA256
    ):
        raise AlphaV24EnrollmentError("exact additive Alpha-v24 frontier changed")
    by_name = {item.name: item for item in rows}
    for name, expected in ROOT_STATEMENT_SHA256.items():
        actual = by_name.get(name)
        if actual is None or sha256(actual.statement.encode()).hexdigest() != expected:
            raise AlphaV24EnrollmentError(f"exact Alpha-v24 campaign root changed: {name}")

    return AlphaV24Enrollment(
        parent_entries=v23.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(sources),
        test_by_name=MappingProxyType(tests),
        rfc_by_name=MappingProxyType(rfcs),
        campaign_by_name=MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV24Enrollment",
    "AlphaV24EnrollmentError",
    "EXPECTED_CAMPAIGN_COUNTS",
    "FRONTIER_V24_EXPECTED_COUNT",
    "FRONTIER_V24_EXPECTED_EDGE_COUNT",
    "FRONTIER_V24_EXPECTED_NAMES_SHA256",
    "FrontierV24Campaign",
    "PARENT_ALPHA_V23_COUNT",
    "PARENT_ALPHA_V23_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V23_IDENTITY_SHA256",
    "ROOT_STATEMENT_SHA256",
    "alpha_v24_enrollment",
)
