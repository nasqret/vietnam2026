"""Exact additive enrollment for the post-v22 constructive milestone closures.

Enrollment authenticates closed, dependency-ordered specifications only.  New
checked-use authority is granted solely by the separately sealed original-kernel
and independently Lean-verified full proof certificate.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from . import editions_v22 as v22
from .theorems import TheoremSpec, _closed_formula


class AlphaV23EnrollmentError(ValueError):
    """An immutable parent or independently reviewed milestone changed."""


class FrontierV23Campaign(str, Enum):
    EUCLIDEAN_LOGARITHMIC_BOUND = "euclidean_logarithmic_bound"
    BINARY_DIGIT_EXTRACTION = "binary_digit_extraction"
    PRIMES_THREE_MOD_FOUR = "primes_three_mod_four"


@dataclass(frozen=True, slots=True)
class AlphaV23Enrollment:
    parent_entries: tuple[v22.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV23Campaign]


PARENT_ALPHA_V22_COUNT = 1_890
PARENT_ALPHA_V22_ENROLLMENT_SHA256 = (
    "431f7300f9190f6fdc35ef84212e93701f2bb565b7e32c1624b7ae0c89cfc5ea"
)
PARENT_ALPHA_V22_IDENTITY_SHA256 = (
    "2750384264856ad10910c1e9369746da886f4760d41e356bfc9e7f8f4563c7db"
)

# Every reviewed campaign body has independently passed the original arithmetic
# kernel; the ordered additive frontier is sealed after its identity is measured.
FRONTIER_V23_EXPECTED_COUNT = 59
FRONTIER_V23_EXPECTED_EDGE_COUNT = 157
FRONTIER_V23_EXPECTED_NAMES_SHA256 = (
    "7d24a436a735a83e20faf2a1378193560f9ea4fb4ae5c7f03e5fc812b39d69db"
)
EXPECTED_CAMPAIGN_COUNTS: dict[FrontierV23Campaign, int] = {
    FrontierV23Campaign.EUCLIDEAN_LOGARITHMIC_BOUND: 17,
    FrontierV23Campaign.BINARY_DIGIT_EXTRACTION: 24,
    FrontierV23Campaign.PRIMES_THREE_MOD_FOUR: 18,
}
ROOT_STATEMENT_SHA256: dict[str, str] = {
    "euclidean_log_trace_below_power": (
        "915f2b77f40e08f8ed00cf72485d98432cab710e9b90415252c2b72573a028e3"
    ),
    "euclidean_log_trace_bound": (
        "c2558acd5302c364d3b9b37bc6cb5caa5b364c66e5f62054a714e74e95e24051"
    ),
    "euclidean_log_execution_strong": (
        "61e7a009a62e18fb46a29979815fa05ae53ac68cc1d054bff89b940e9ed76baf"
    ),
    "euclidean_gcd_execution_logarithmic_bound": (
        "decf1f8be3a9dcaf2e8bdf7bebd59e46d08e9f91fee375ca325c6b53847c8d6e"
    ),
    "euclidean_gcd_execution_logarithmic_exists": (
        "c9fd69a20e1ef3f4b71cb4fc58a8fb001f37d08fc1d8c51f541409070f016523"
    ),
    "binary_exponent_digit_prefix_exists": (
        "32bdeec52d9746fee467a709ae2315e25800e4f0603fe465c14fa84f03452f0d"
    ),
    "binary_modular_exponent_coded_execution_exists": (
        "d2c7995fed0f8265109081af92313d7a0ff7bd740a238c578b2a06522f016a3a"
    ),
    "binary_modular_exponent_coded_execution_exists_unique": (
        "3b7d9957844c9972de1f2a4cea63b355134d634dab471fc1ad31a89b3e509bfc"
    ),
    "binary_modular_execution_bitlength_bound": (
        "f26f699912b4f5feb522f8afe77676b881747f5a997fa169d27e924c6f7acb73"
    ),
    "binary_modular_execution_logarithmic_bound": (
        "3ac6949afecc26acc6e5fb9d8d9041be9a9f2b8120dcbc918b8e771a7a1bd27d"
    ),
    "infinitely_many_primes_three_mod_four": (
        "3ddac628b2e37925ee3d7a4bd56319de5e173e9065cce6437cab775cc646620b"
    ),
}


@dataclass(frozen=True, slots=True)
class _Factory:
    campaign: FrontierV23Campaign
    module: str
    factory: str
    rfc: str


_FACTORIES = (
    _Factory(
        FrontierV23Campaign.EUCLIDEAN_LOGARITHMIC_BOUND,
        "euclidean_logarithmic_bound_candidate",
        "make_euclidean_logarithmic_bound_candidate_theorems",
        "research/arithmetic-library/euclidean-logarithmic-bound-rfc-v1.md",
    ),
    _Factory(
        FrontierV23Campaign.BINARY_DIGIT_EXTRACTION,
        "binary_digit_extraction_candidate",
        "make_binary_digit_extraction_candidate_theorems",
        "research/arithmetic-library/binary-digit-extraction-rfc-v1.md",
    ),
    _Factory(
        FrontierV23Campaign.PRIMES_THREE_MOD_FOUR,
        "primes_three_mod_four_candidate",
        "make_primes_three_mod_four_candidate_theorems",
        "research/arithmetic-library/primes-three-mod-four-rfc-v1.md",
    ),
)


def _validate_parent() -> None:
    if (
        len(v22.ALPHA_ENTRIES) != PARENT_ALPHA_V22_COUNT
        or len(v22.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V22_COUNT
        or v22.ALPHA_V22_ENROLLMENT_SHA256 != PARENT_ALPHA_V22_ENROLLMENT_SHA256
        or v22.ALPHA_V22_IDENTITY_SHA256 != PARENT_ALPHA_V22_IDENTITY_SHA256
        or len(v22.STABLE_SPECS) != 432
    ):
        raise AlphaV23EnrollmentError("immutable fully checked Alpha-v22 parent changed")


@lru_cache(maxsize=1)
def alpha_v23_enrollment() -> AlphaV23Enrollment:
    _validate_parent()
    available = {entry.spec.name for entry in v22.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV23Campaign] = {}

    for owner in _FACTORIES:
        try:
            module = import_module(f".{owner.module}", package=__package__)
            candidates = tuple(getattr(module, owner.factory)(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV23EnrollmentError(
                f"unavailable reviewed Alpha-v23 factory {owner.module}.{owner.factory}"
            ) from error
        expected = EXPECTED_CAMPAIGN_COUNTS[owner.campaign]
        if expected and len(candidates) != expected:
            raise AlphaV23EnrollmentError(
                f"exact Alpha-v23 campaign cardinality changed: {owner.campaign.value}"
            )
        for item in candidates:
            if type(item) is not TheoremSpec or item.name in available:
                raise AlphaV23EnrollmentError("invalid or duplicate Alpha-v23 theorem")
            missing = set(item.dependencies).difference(available)
            if missing:
                raise AlphaV23EnrollmentError(
                    f"forward Alpha-v23 dependencies for {item.name!r}: {sorted(missing)!r}"
                )
            if not item.script or any(
                "DNE" in command or command.startswith("use ") for command in item.script
            ):
                raise AlphaV23EnrollmentError(
                    f"Alpha-v23 theorem lacks an explicit constructive script: {item.name!r}"
                )
            _closed_formula(item.statement)
            sources[item.name] = f"peano-lab/py/peano_lab/library/{owner.module}.py"
            tests[item.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfcs[item.name] = owner.rfc
            campaigns[item.name] = owner.campaign
            rows.append(item)
            available.add(item.name)

    if FRONTIER_V23_EXPECTED_COUNT and (
        len(rows) != FRONTIER_V23_EXPECTED_COUNT
        or sum(len(item.dependencies) for item in rows) != FRONTIER_V23_EXPECTED_EDGE_COUNT
        or sha256("\n".join(item.name for item in rows).encode()).hexdigest()
        != FRONTIER_V23_EXPECTED_NAMES_SHA256
    ):
        raise AlphaV23EnrollmentError("exact additive Alpha-v23 frontier changed")
    by_name = {item.name: item for item in rows}
    for name, expected in ROOT_STATEMENT_SHA256.items():
        actual = by_name.get(name)
        if actual is None or sha256(actual.statement.encode()).hexdigest() != expected:
            raise AlphaV23EnrollmentError(f"exact Alpha-v23 campaign root changed: {name}")

    return AlphaV23Enrollment(
        parent_entries=v22.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(sources),
        test_by_name=MappingProxyType(tests),
        rfc_by_name=MappingProxyType(rfcs),
        campaign_by_name=MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV23Enrollment",
    "AlphaV23EnrollmentError",
    "EXPECTED_CAMPAIGN_COUNTS",
    "FRONTIER_V23_EXPECTED_COUNT",
    "FRONTIER_V23_EXPECTED_EDGE_COUNT",
    "FRONTIER_V23_EXPECTED_NAMES_SHA256",
    "FrontierV23Campaign",
    "PARENT_ALPHA_V22_COUNT",
    "PARENT_ALPHA_V22_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V22_IDENTITY_SHA256",
    "ROOT_STATEMENT_SHA256",
    "alpha_v23_enrollment",
)
