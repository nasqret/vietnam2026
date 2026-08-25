"""Exact additive Alpha-v19 constructive number-theory campaign inventory.

Enrollment planning is intentionally evidence-free: none of the factories,
candidate scripts, hashes, or parent receipts grants checked theorem use.
Actual Alpha-v19 admission is justified separately by complete ordinary
intuitionistic proof bundles and the unchanged independent kernel.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from . import editions_v18 as v18
from .theorems import TheoremSpec, _closed_formula


class AlphaV19EnrollmentError(ValueError):
    """The sealed parent, candidate inventory, or dependency order changed."""


class FrontierV19Campaign(str, Enum):
    PYTHAGOREAN = "pythagorean"
    PRIME_TWO_SQUARE = "prime_two_square"
    LINEAR_CONGRUENCE = "linear_congruence"
    PRIMES_ONE_MOD_FOUR = "primes_one_mod_four"


@dataclass(frozen=True, slots=True)
class AlphaV19Enrollment:
    parent_entries: tuple[v18.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV19Campaign]


PARENT_ALPHA_V18_COUNT = 1_673
PARENT_ALPHA_V18_CHECKED_COUNT = 1_589
PARENT_ALPHA_V18_ENROLLMENT_SHA256 = (
    "44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175"
)
PARENT_ALPHA_V18_IDENTITY_SHA256 = (
    "f694881096fd09b1002d0d49bb7be2d68d9894457749ef04128deebd92a64f66"
)
PYTHAGOREAN_V19_EXPECTED_COUNT = 44
FRONTIER_V19_EXPECTED_COUNT = 64
FRONTIER_V19_EXPECTED_NAMES_SHA256 = (
    "07b9c92ab3ef80dc609681a9b588d21b0faeb69e87448c1420b78272a54aaed1"
)
PRIME_TWO_SQUARE_ROOT_NAME = "prime_is_two_squares_iff_two_or_one_mod_four"
PRIME_TWO_SQUARE_ROOT_STATEMENT_SHA256 = (
    "84184c6c9fccba3457f8db4cb5716f0e75e85fa2749f1db6471f902cbbe415d7"
)
PYTHAGOREAN_V19_ROOT_NAMES = (
    "pythagorean_primitive_euclidean_from_order",
    "pythagorean_primitive_normal_form",
)
LINEAR_CONGRUENCE_ROOT_NAME = "linear_congruence_solvable_iff_gcd_divides"
PRIMES_ONE_MOD_FOUR_ROOT_NAME = "infinitely_many_primes_one_mod_four"
_ROOT_STATEMENT_SHA256 = {
    "pythagorean_primitive_euclidean_from_order": (
        "7b71efd8961214c09eacc96a84603d56f5658d850a3f31256df3e00255a48e90"
    ),
    "pythagorean_primitive_normal_form": (
        "0e58024c289803991f5b0536889cea380c59940c3b351eebe2e57298db872bac"
    ),
    PRIME_TWO_SQUARE_ROOT_NAME: PRIME_TWO_SQUARE_ROOT_STATEMENT_SHA256,
    LINEAR_CONGRUENCE_ROOT_NAME: (
        "808ae7b7b17bc3c2a027e76aff9d4f7d58157d50ce20ee50e323631b2b02296e"
    ),
    PRIMES_ONE_MOD_FOUR_ROOT_NAME: (
        "eb4e068b6bb3a271118a6e6aaea03ddd9d0fc10317f38bc4697b0a46dd9ac1be"
    ),
}


@dataclass(frozen=True, slots=True)
class _Factory:
    campaign: FrontierV19Campaign
    module: str
    factory: str
    rfc: str
    only: frozenset[str] = frozenset()


_FACTORIES = (
    _Factory(
        FrontierV19Campaign.PYTHAGOREAN,
        "pythagorean_fermat_four_candidate",
        "make_pythagorean_fermat_four_candidate_theorems",
        "research/arithmetic-library/pythagorean-fermat-four-rfc-v1.md",
    ),
    _Factory(
        FrontierV19Campaign.PYTHAGOREAN,
        "pythagorean_primitive_candidate",
        "make_pythagorean_primitive_candidate_theorems",
        "research/arithmetic-library/pythagorean-primitive-rfc-v1.md",
    ),
    _Factory(
        FrontierV19Campaign.PRIME_TWO_SQUARE,
        "fermat_two_squares_classification_candidate",
        "make_fermat_two_squares_classification_candidate_theorems",
        "research/arithmetic-library/fermat-two-squares-classification-rfc-v1.md",
        frozenset({PRIME_TWO_SQUARE_ROOT_NAME}),
    ),
    _Factory(
        FrontierV19Campaign.LINEAR_CONGRUENCE,
        "linear_congruence_complete_candidate",
        "make_linear_congruence_complete_candidate_theorems",
        "research/arithmetic-library/linear-congruence-complete-rfc-v1.md",
    ),
    _Factory(
        FrontierV19Campaign.PRIMES_ONE_MOD_FOUR,
        "primes_one_mod_four_candidate",
        "make_primes_one_mod_four_candidate_theorems",
        "research/arithmetic-library/primes-one-mod-four-rfc-v1.md",
    ),
)


def _validate_parent() -> None:
    if (
        len(v18.ALPHA_ENTRIES) != PARENT_ALPHA_V18_COUNT
        or len(v18.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V18_CHECKED_COUNT
        or v18.ALPHA_V18_ENROLLMENT_SHA256 != PARENT_ALPHA_V18_ENROLLMENT_SHA256
        or v18.ALPHA_V18_IDENTITY_SHA256 != PARENT_ALPHA_V18_IDENTITY_SHA256
        or len(v18.STABLE_SPECS) != 432
    ):
        raise AlphaV19EnrollmentError("immutable Alpha-v18 campaign parent changed")


@lru_cache(maxsize=1)
def alpha_v19_enrollment() -> AlphaV19Enrollment:
    """Collect exact new first-order specifications in strict dependency order."""

    _validate_parent()
    available = {entry.spec.name for entry in v18.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    rfc_by_name: dict[str, str] = {}
    campaign_by_name: dict[str, FrontierV19Campaign] = {}

    for owner in _FACTORIES:
        try:
            module = import_module(f".{owner.module}", package=__package__)
            factory = getattr(module, owner.factory)
            candidates = tuple(factory(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV19EnrollmentError(
                f"unavailable constructive Alpha-v19 factory {owner.module}.{owner.factory}"
            ) from error
        if not candidates:
            raise AlphaV19EnrollmentError(f"empty Alpha-v19 campaign {owner.module!r}")
        selected = tuple(
            row for row in candidates if not owner.only or row.name in owner.only
        )
        if owner.only and frozenset(row.name for row in selected) != owner.only:
            raise AlphaV19EnrollmentError(
                f"missing exact Alpha-v19 campaign endpoint in {owner.module!r}"
            )
        for spec in selected:
            if type(spec) is not TheoremSpec:
                raise AlphaV19EnrollmentError("Alpha-v19 rows must be exact theorem specs")
            if spec.name in available:
                raise AlphaV19EnrollmentError(
                    f"duplicate Alpha-v19 campaign theorem {spec.name!r}"
                )
            missing = set(spec.dependencies).difference(available)
            if missing:
                raise AlphaV19EnrollmentError(
                    f"forward Alpha-v19 dependencies for {spec.name!r}: {sorted(missing)!r}"
                )
            if not spec.script or any("DNE" in command for command in spec.script):
                raise AlphaV19EnrollmentError(
                    f"Alpha-v19 theorem lacks a constructive script: {spec.name!r}"
                )
            _closed_formula(spec.statement)
            source_by_name[spec.name] = (
                f"peano-lab/py/peano_lab/library/{owner.module}.py"
            )
            test_by_name[spec.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfc_by_name[spec.name] = owner.rfc
            campaign_by_name[spec.name] = owner.campaign
            rows.append(spec)
            available.add(spec.name)

    if sum(
        campaign is FrontierV19Campaign.PYTHAGOREAN
        for campaign in campaign_by_name.values()
    ) != PYTHAGOREAN_V19_EXPECTED_COUNT:
        raise AlphaV19EnrollmentError("exact 44-row Pythagorean frontier changed")
    by_name = {row.name: row for row in rows}
    for name in (
        *PYTHAGOREAN_V19_ROOT_NAMES,
        PRIME_TWO_SQUARE_ROOT_NAME,
        LINEAR_CONGRUENCE_ROOT_NAME,
        PRIMES_ONE_MOD_FOUR_ROOT_NAME,
    ):
        if name not in by_name:
            raise AlphaV19EnrollmentError(f"missing constructive campaign root {name!r}")
    if (
        len(rows) != FRONTIER_V19_EXPECTED_COUNT
        or sha256("\n".join(row.name for row in rows).encode()).hexdigest()
        != FRONTIER_V19_EXPECTED_NAMES_SHA256
    ):
        raise AlphaV19EnrollmentError("exact additive Alpha-v19 campaign order changed")
    for name, frozen in _ROOT_STATEMENT_SHA256.items():
        if sha256(by_name[name].statement.encode()).hexdigest() != frozen:
            raise AlphaV19EnrollmentError(f"exact campaign endpoint changed: {name}")

    return AlphaV19Enrollment(
        parent_entries=v18.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        rfc_by_name=MappingProxyType(rfc_by_name),
        campaign_by_name=MappingProxyType(campaign_by_name),
    )


__all__ = [
    "AlphaV19Enrollment",
    "AlphaV19EnrollmentError",
    "FRONTIER_V19_EXPECTED_COUNT",
    "FRONTIER_V19_EXPECTED_NAMES_SHA256",
    "FrontierV19Campaign",
    "LINEAR_CONGRUENCE_ROOT_NAME",
    "PARENT_ALPHA_V18_CHECKED_COUNT",
    "PARENT_ALPHA_V18_COUNT",
    "PARENT_ALPHA_V18_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V18_IDENTITY_SHA256",
    "PRIMES_ONE_MOD_FOUR_ROOT_NAME",
    "PRIME_TWO_SQUARE_ROOT_NAME",
    "PRIME_TWO_SQUARE_ROOT_STATEMENT_SHA256",
    "PYTHAGOREAN_V19_EXPECTED_COUNT",
    "PYTHAGOREAN_V19_ROOT_NAMES",
    "alpha_v19_enrollment",
]
