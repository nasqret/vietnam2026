"""Exact additive enrollment for the next constructive Alpha campaign.

Enrollment describes dependency-ordered first-order specifications only. It
does not replay a proof, introduce an axiom, or grant theorem-use authority.
The immutable Alpha-v20 parent and the unchanged Stable channel are retained
verbatim; only independently original-kernel-checked constructive candidates
are eligible for the separately verified Alpha-v21 proof-bundle admission.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from . import editions_v20 as v20
from .theorems import TheoremSpec, _closed_formula


class AlphaV21EnrollmentError(ValueError):
    """The sealed parent or the exact constructive frontier changed."""


class FrontierV21Campaign(str, Enum):
    MATRIX_CODED_PRODUCT = "matrix_coded_product"
    EUCLIDEAN_COMPLEXITY = "euclidean_complexity"
    BINARY_MODULAR_EXPONENTIATION = "binary_modular_exponentiation"


@dataclass(frozen=True, slots=True)
class AlphaV21Enrollment:
    parent_entries: tuple[v20.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV21Campaign]


PARENT_ALPHA_V20_COUNT = 1_776
PARENT_ALPHA_V20_ENROLLMENT_SHA256 = (
    "947e12db1db93decddd87b833067acf774a37fcb7d89de117010d53baf00065c"
)
PARENT_ALPHA_V20_IDENTITY_SHA256 = (
    "ee0f596150d8609ab302303ade44c4413290675398a1d6999a47b3ba046ac38b"
)

# These counts and exact endpoint hashes are frozen after every original
# candidate body is independently kernel checked; unset values never suffice
# to replay a theorem or to authenticate an Alpha-v21 proof artifact.
FRONTIER_V21_EXPECTED_COUNT = 54
FRONTIER_V21_EXPECTED_EDGE_COUNT = 104
FRONTIER_V21_EXPECTED_NAMES_SHA256 = (
    "cbf76fb45efbae79a2b1cd2c7fc3cf806a6f8ebc593a5fceee6f5bea7cd734f5"
)
EXPECTED_CAMPAIGN_COUNTS: dict[FrontierV21Campaign, int] = {
    FrontierV21Campaign.MATRIX_CODED_PRODUCT: 23,
    FrontierV21Campaign.EUCLIDEAN_COMPLEXITY: 15,
    FrontierV21Campaign.BINARY_MODULAR_EXPONENTIATION: 16,
}

MATRIX_CODED_PRODUCT_ROOT_NAME = "beta_matrix_product_exists"
SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME = "beta_signed_matrix_product_exists"
SIGNED_DOT_PRODUCT_ROOT_NAME = "beta_signed_dot_product_exists_unique"
SIGNED_THREE_DETERMINANT_ROOT_NAME = "signed_matrix_three_full_determinant_exists"
EUCLIDEAN_TWO_STEP_HALVING_ROOT_NAME = "euclidean_two_step_halving"
EUCLIDEAN_EXECUTION_ROOT_NAME = "euclidean_gcd_execution_linear_bound"
BINARY_MODULAR_EXPONENTIATION_ROOT_NAME = (
    "binary_modular_exponentiation_result_exists_unique"
)
_ROOT_STATEMENT_SHA256: dict[str, str] = {
    MATRIX_CODED_PRODUCT_ROOT_NAME: (
        "c2d3335be60c889559096aa9a36ed8d9bd38c8b33b5f776d73cdec0a60e951c2"
    ),
    SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME: (
        "13291ba49b84a8b1345863e446bca126321e7962eb912bd84b48761f9db24c7f"
    ),
    SIGNED_DOT_PRODUCT_ROOT_NAME: (
        "f84fbb5d723d32ea972a38d562c3e59cbedc78ab485e9f20cda90c0c4f186c04"
    ),
    SIGNED_THREE_DETERMINANT_ROOT_NAME: (
        "edd7918f03a700f96dc345ba77e3dae458485fb323162139c2e93dbc09fae784"
    ),
    EUCLIDEAN_TWO_STEP_HALVING_ROOT_NAME: (
        "a7bf1c208237e02edcfdb3b7c819e944be1d0bc8783a06bcb05cfcab5ba7df94"
    ),
    EUCLIDEAN_EXECUTION_ROOT_NAME: (
        "cde09bcea3d247bca7dc5d0b44a0576b1822a0464826f54f5ff3424bdeec2435"
    ),
    BINARY_MODULAR_EXPONENTIATION_ROOT_NAME: (
        "7b9895f8ad3956c33e9fb06ea8040113f17f272be5e97d942ca71aed2a88f136"
    ),
}


@dataclass(frozen=True, slots=True)
class _Factory:
    campaign: FrontierV21Campaign
    module: str
    factory: str
    rfc: str


_FACTORIES = (
    _Factory(
        FrontierV21Campaign.MATRIX_CODED_PRODUCT,
        "matrix_coded_product_candidate",
        "make_matrix_coded_product_candidate_theorems",
        "research/arithmetic-library/matrix-coded-product-rfc-v1.md",
    ),
    _Factory(
        FrontierV21Campaign.EUCLIDEAN_COMPLEXITY,
        "euclidean_complexity_candidate",
        "make_euclidean_complexity_candidate_theorems",
        "research/arithmetic-library/euclidean-complexity-rfc-v1.md",
    ),
    _Factory(
        FrontierV21Campaign.BINARY_MODULAR_EXPONENTIATION,
        "binary_modular_exponentiation_candidate",
        "make_binary_modular_exponentiation_candidate_theorems",
        "research/arithmetic-library/binary-modular-exponentiation-rfc-v1.md",
    ),
)


def _validate_parent() -> None:
    if (
        len(v20.ALPHA_ENTRIES) != PARENT_ALPHA_V20_COUNT
        or len(v20.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V20_COUNT
        or v20.ALPHA_V20_ENROLLMENT_SHA256 != PARENT_ALPHA_V20_ENROLLMENT_SHA256
        or v20.ALPHA_V20_IDENTITY_SHA256 != PARENT_ALPHA_V20_IDENTITY_SHA256
        or len(v20.STABLE_SPECS) != 432
    ):
        raise AlphaV21EnrollmentError("immutable, fully checked Alpha-v20 parent changed")


@lru_cache(maxsize=1)
def alpha_v21_enrollment() -> AlphaV21Enrollment:
    _validate_parent()
    available = {entry.spec.name for entry in v20.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    rfc_by_name: dict[str, str] = {}
    campaign_by_name: dict[str, FrontierV21Campaign] = {}

    for owner in _FACTORIES:
        try:
            module = import_module(f".{owner.module}", package=__package__)
            factory = getattr(module, owner.factory)
            candidates = tuple(factory(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV21EnrollmentError(
                f"unavailable constructive Alpha-v21 factory {owner.module}.{owner.factory}"
            ) from error
        expected = EXPECTED_CAMPAIGN_COUNTS.get(owner.campaign)
        if expected is not None and len(candidates) != expected:
            raise AlphaV21EnrollmentError(
                f"exact Alpha-v21 campaign cardinality changed: {owner.campaign.value}"
            )
        for item in candidates:
            if type(item) is not TheoremSpec:
                raise AlphaV21EnrollmentError("Alpha-v21 rows must be exact theorem specs")
            if item.name in available:
                raise AlphaV21EnrollmentError(f"duplicate Alpha-v21 theorem {item.name!r}")
            missing = set(item.dependencies).difference(available)
            if missing:
                raise AlphaV21EnrollmentError(
                    f"forward Alpha-v21 dependencies for {item.name!r}: {sorted(missing)!r}"
                )
            if not item.script or any(
                "DNE" in command or command.startswith("use ") for command in item.script
            ):
                raise AlphaV21EnrollmentError(
                    f"Alpha-v21 theorem lacks an explicit constructive script: {item.name!r}"
                )
            _closed_formula(item.statement)
            source_by_name[item.name] = f"peano-lab/py/peano_lab/library/{owner.module}.py"
            test_by_name[item.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfc_by_name[item.name] = owner.rfc
            campaign_by_name[item.name] = owner.campaign
            rows.append(item)
            available.add(item.name)

    if FRONTIER_V21_EXPECTED_COUNT and (
        len(rows) != FRONTIER_V21_EXPECTED_COUNT
        or sum(len(item.dependencies) for item in rows) != FRONTIER_V21_EXPECTED_EDGE_COUNT
        or sha256("\n".join(item.name for item in rows).encode()).hexdigest()
        != FRONTIER_V21_EXPECTED_NAMES_SHA256
    ):
        raise AlphaV21EnrollmentError("exact additive Alpha-v21 campaign surface changed")
    by_name = {item.name: item for item in rows}
    for name, expected in _ROOT_STATEMENT_SHA256.items():
        actual = by_name.get(name)
        if actual is None or sha256(actual.statement.encode()).hexdigest() != expected:
            raise AlphaV21EnrollmentError(f"exact Alpha-v21 campaign endpoint changed: {name}")

    return AlphaV21Enrollment(
        parent_entries=v20.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        rfc_by_name=MappingProxyType(rfc_by_name),
        campaign_by_name=MappingProxyType(campaign_by_name),
    )


__all__ = [
    "AlphaV21Enrollment",
    "AlphaV21EnrollmentError",
    "BINARY_MODULAR_EXPONENTIATION_ROOT_NAME",
    "EUCLIDEAN_EXECUTION_ROOT_NAME",
    "EUCLIDEAN_TWO_STEP_HALVING_ROOT_NAME",
    "EXPECTED_CAMPAIGN_COUNTS",
    "FRONTIER_V21_EXPECTED_COUNT",
    "FRONTIER_V21_EXPECTED_EDGE_COUNT",
    "FRONTIER_V21_EXPECTED_NAMES_SHA256",
    "FrontierV21Campaign",
    "MATRIX_CODED_PRODUCT_ROOT_NAME",
    "PARENT_ALPHA_V20_COUNT",
    "PARENT_ALPHA_V20_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V20_IDENTITY_SHA256",
    "SIGNED_DOT_PRODUCT_ROOT_NAME",
    "SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME",
    "SIGNED_THREE_DETERMINANT_ROOT_NAME",
    "alpha_v21_enrollment",
]
