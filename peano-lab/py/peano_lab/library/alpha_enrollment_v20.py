"""Sealed additive enrollment for the next constructive number-theory layer.

Enrollment describes exact first-order statements and their dependency order;
it is deliberately not a proof or theorem-admission mechanism. Alpha v19 and
Stable are immutable parents. Actual checked use is granted separately only
after every dependency-curried proof body and complete ordinary proof bundle
have been accepted by the unchanged intuitionistic kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from . import editions_v19 as v19
from .theorems import TheoremSpec, _closed_formula


class AlphaV20EnrollmentError(ValueError):
    """The immutable parent or exact next-layer dependency inventory changed."""


class FrontierV20Campaign(str, Enum):
    POLYNOMIAL_HORNER = "polynomial_horner"
    MATRIX_DOT_PRODUCT = "matrix_dot_product"
    BERTRAND_PRIME = "bertrand_prime"
    CONTINUED_FRACTION = "continued_fraction"


@dataclass(frozen=True, slots=True)
class AlphaV20Enrollment:
    parent_entries: tuple[v19.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV20Campaign]


PARENT_ALPHA_V19_COUNT = 1_737
PARENT_ALPHA_V19_ENROLLMENT_SHA256 = (
    "1295d6fc3da84646cb6bc8d5070627d42a6df33d673c44a2adfcd433edc41795"
)
PARENT_ALPHA_V19_IDENTITY_SHA256 = (
    "905189c32e13b3ec8b19ecad30fe51353eb0b66a9eb065ddae542c80746d3ea7"
)
FRONTIER_V20_EXPECTED_COUNT = 39
FRONTIER_V20_EXPECTED_EDGE_COUNT = 103
FRONTIER_V20_EXPECTED_NAMES_SHA256 = (
    "6a9564cc3e55245161d7c13b81e25005e287232dd44deb303133e3a8e3ae2eba"
)
EXPECTED_CAMPAIGN_COUNTS = {
    FrontierV20Campaign.POLYNOMIAL_HORNER: 7,
    FrontierV20Campaign.MATRIX_DOT_PRODUCT: 10,
    FrontierV20Campaign.BERTRAND_PRIME: 13,
    FrontierV20Campaign.CONTINUED_FRACTION: 9,
}

POLYNOMIAL_HORNER_ROOT_NAME = "beta_horner_eval_exists"
MATRIX_DOT_PRODUCT_ROOT_NAME = "beta_dot_product_exists_unique"
BERTRAND_MULTIPLICITY_ROOT_NAME = "central_binom_prime_divisor_multiplicity_one_exists"
BERTRAND_CHAIN_ROOT_NAME = "iterated_bertrand_prime_chain_exists"
CONTINUED_FRACTION_ROOT_NAME = "continued_fraction_positive_exists"

_ROOT_STATEMENT_SHA256 = {
    POLYNOMIAL_HORNER_ROOT_NAME: (
        "bd1fa1601bd14a7dd6e769eb49bb646326d12f9a26d206c89eea1c7de54ac7d3"
    ),
    MATRIX_DOT_PRODUCT_ROOT_NAME: (
        "8a40343d3cb482060f468b5d8d2f3fe02f76bf740482be0ee67730d0d8c2969d"
    ),
    BERTRAND_MULTIPLICITY_ROOT_NAME: (
        "d0899600b713e85d0cb20997ada171ce02b6a6e8316364ed4ab603389724f5a8"
    ),
    BERTRAND_CHAIN_ROOT_NAME: (
        "02c52d46368ec2320c8d316b41d37ef7c1dbb5de32dbd15247325a17382650d2"
    ),
    CONTINUED_FRACTION_ROOT_NAME: (
        "d3b12766820bb64d9b1437e0ef96a9068c84d6d3176e066fe70f5a4f2d9e087d"
    ),
}


@dataclass(frozen=True, slots=True)
class _Factory:
    campaign: FrontierV20Campaign
    module: str
    factory: str
    rfc: str


_FACTORIES = (
    _Factory(
        FrontierV20Campaign.POLYNOMIAL_HORNER,
        "polynomial_horner_candidate",
        "make_polynomial_horner_candidate_theorems",
        "research/arithmetic-library/polynomial-horner-rfc-v1.md",
    ),
    _Factory(
        FrontierV20Campaign.MATRIX_DOT_PRODUCT,
        "matrix_dot_product_candidate",
        "make_matrix_dot_product_candidate_theorems",
        "research/arithmetic-library/matrix-dot-product-rfc-v1.md",
    ),
    _Factory(
        FrontierV20Campaign.BERTRAND_PRIME,
        "bertrand_prime_campaign_candidate",
        "make_bertrand_prime_campaign_candidate_theorems",
        "research/arithmetic-library/bertrand-prime-campaign-next-layer-rfc-v1.md",
    ),
    _Factory(
        FrontierV20Campaign.CONTINUED_FRACTION,
        "continued_fraction_candidate",
        "make_continued_fraction_candidate_theorems",
        "research/arithmetic-library/continued-fraction-rfc-v1.md",
    ),
)


def _validate_parent() -> None:
    if (
        len(v19.ALPHA_ENTRIES) != PARENT_ALPHA_V19_COUNT
        or len(v19.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V19_COUNT
        or v19.ALPHA_V19_ENROLLMENT_SHA256 != PARENT_ALPHA_V19_ENROLLMENT_SHA256
        or v19.ALPHA_V19_IDENTITY_SHA256 != PARENT_ALPHA_V19_IDENTITY_SHA256
        or len(v19.STABLE_SPECS) != 432
    ):
        raise AlphaV20EnrollmentError("immutable, fully checked Alpha-v19 parent changed")


@lru_cache(maxsize=1)
def alpha_v20_enrollment() -> AlphaV20Enrollment:
    """Return exactly 39 new conservative specifications in dependency order."""

    _validate_parent()
    available = {entry.spec.name for entry in v19.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    rfc_by_name: dict[str, str] = {}
    campaign_by_name: dict[str, FrontierV20Campaign] = {}

    for owner in _FACTORIES:
        try:
            module = import_module(f".{owner.module}", package=__package__)
            factory = getattr(module, owner.factory)
            candidates = tuple(factory(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV20EnrollmentError(
                f"unavailable constructive Alpha-v20 factory {owner.module}.{owner.factory}"
            ) from error
        if len(candidates) != EXPECTED_CAMPAIGN_COUNTS[owner.campaign]:
            raise AlphaV20EnrollmentError(
                f"exact Alpha-v20 campaign cardinality changed: {owner.campaign.value}"
            )
        for item in candidates:
            if type(item) is not TheoremSpec:
                raise AlphaV20EnrollmentError("Alpha-v20 rows must be exact theorem specs")
            if item.name in available:
                raise AlphaV20EnrollmentError(f"duplicate Alpha-v20 theorem {item.name!r}")
            missing = set(item.dependencies).difference(available)
            if missing:
                raise AlphaV20EnrollmentError(
                    f"forward Alpha-v20 dependencies for {item.name!r}: {sorted(missing)!r}"
                )
            if not item.script or any(
                "DNE" in command or command.startswith("use ")
                for command in item.script
            ):
                raise AlphaV20EnrollmentError(
                    f"Alpha-v20 theorem lacks an explicit constructive script: {item.name!r}"
                )
            _closed_formula(item.statement)
            source_by_name[item.name] = f"peano-lab/py/peano_lab/library/{owner.module}.py"
            test_by_name[item.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfc_by_name[item.name] = owner.rfc
            campaign_by_name[item.name] = owner.campaign
            rows.append(item)
            available.add(item.name)

    if (
        len(rows) != FRONTIER_V20_EXPECTED_COUNT
        or sum(len(item.dependencies) for item in rows) != FRONTIER_V20_EXPECTED_EDGE_COUNT
        or sha256("\n".join(item.name for item in rows).encode()).hexdigest()
        != FRONTIER_V20_EXPECTED_NAMES_SHA256
    ):
        raise AlphaV20EnrollmentError("exact additive Alpha-v20 campaign surface changed")
    by_name = {item.name: item for item in rows}
    for name, expected in _ROOT_STATEMENT_SHA256.items():
        actual = by_name.get(name)
        if actual is None or sha256(actual.statement.encode()).hexdigest() != expected:
            raise AlphaV20EnrollmentError(f"exact Alpha-v20 campaign endpoint changed: {name}")

    return AlphaV20Enrollment(
        parent_entries=v19.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        rfc_by_name=MappingProxyType(rfc_by_name),
        campaign_by_name=MappingProxyType(campaign_by_name),
    )


__all__ = [
    "AlphaV20Enrollment",
    "AlphaV20EnrollmentError",
    "BERTRAND_CHAIN_ROOT_NAME",
    "BERTRAND_MULTIPLICITY_ROOT_NAME",
    "CONTINUED_FRACTION_ROOT_NAME",
    "EXPECTED_CAMPAIGN_COUNTS",
    "FRONTIER_V20_EXPECTED_COUNT",
    "FRONTIER_V20_EXPECTED_EDGE_COUNT",
    "FRONTIER_V20_EXPECTED_NAMES_SHA256",
    "FrontierV20Campaign",
    "MATRIX_DOT_PRODUCT_ROOT_NAME",
    "PARENT_ALPHA_V19_COUNT",
    "PARENT_ALPHA_V19_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V19_IDENTITY_SHA256",
    "POLYNOMIAL_HORNER_ROOT_NAME",
    "alpha_v20_enrollment",
]
