"""Exact additive enrollment for the post-v21 constructive transport layer.

Enrollment validates closed, dependency-ordered specifications only; it is
never a proof provider.  Actual checked-use authority requires the separately
sealed original-kernel proof bundle and its independent Lean verification.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from . import editions_v21 as v21
from .theorems import TheoremSpec, _closed_formula


class AlphaV22EnrollmentError(ValueError):
    """The immutable parent or independently reviewed frontier changed."""


class FrontierV22Campaign(str, Enum):
    BINARY_LENGTH = "binary_length"
    EUCLIDEAN_GCD_TRANSPORT = "euclidean_gcd_transport"
    BINARY_MODULAR_EXECUTION = "binary_modular_execution"


@dataclass(frozen=True, slots=True)
class AlphaV22Enrollment:
    parent_entries: tuple[v21.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV22Campaign]


PARENT_ALPHA_V21_COUNT = 1_830
PARENT_ALPHA_V21_ENROLLMENT_SHA256 = (
    "ad2616d7656438ee2084f5ea404df3dad2106a99c6819fd174fd8c3ed6bb4c98"
)
PARENT_ALPHA_V21_IDENTITY_SHA256 = (
    "aee42cc37e4a4073eb4892e81e4f26d957b3b4b42675c1ed4e67c90dc89602e6"
)

# Frozen only after all new ordinary constructive proof bodies are checked.
FRONTIER_V22_EXPECTED_COUNT = 60
FRONTIER_V22_EXPECTED_EDGE_COUNT = 142
FRONTIER_V22_EXPECTED_NAMES_SHA256 = (
    "c2d9a2840111e6b79a8716eb1a9a0c02345a771bcf60d42c96e6a7c3283e6713"
)
EXPECTED_CAMPAIGN_COUNTS: dict[FrontierV22Campaign, int] = {
    FrontierV22Campaign.BINARY_LENGTH: 21,
    FrontierV22Campaign.EUCLIDEAN_GCD_TRANSPORT: 20,
    FrontierV22Campaign.BINARY_MODULAR_EXECUTION: 19,
}
ROOT_STATEMENT_SHA256: dict[str, str] = {
    "binary_length_exists": (
        "53b6739ac80ec864c4b36aecdbca366e4bc997a8a45e5a1ef2daaf05dbde7778"
    ),
    "binary_length_functional": (
        "4b14a06b7b09b4b54be5cbc0c0a22110d029c5e57a16e126f2f9298eca7f9e7f"
    ),
    "binary_length_exists_unique": (
        "4365c8d9b855b85331e421d1c5e82349c598097f22dfe65141738573ee7ae89e"
    ),
    "binary_length_power_exact": (
        "69eace7cc1b3f3f0b2a5b3694e4c43d54124099b5f2c7102ed705bb73cd7868f"
    ),
    "euclidean_trace_terminal_gcd_exists": (
        "66cf940ab57702728d12727ad01c75ebfd27a35dcd3a7e254917e66bf3bac9f5"
    ),
    "euclidean_execution_terminal_identified": (
        "2b051e092e5b38f1caf67f94722b9b21c844ee2c9fd8b36f805b5f6db7bfbc9d"
    ),
    "euclidean_anchored_execution_exists": (
        "fa82bf6592c70a883cf31cb31a3ade3379bbfb4c1d55dd314682deb680ce8adb"
    ),
    "euclidean_anchored_execution_linear_bound": (
        "f14b30ffeb6b2ead02fb92f6518e57b9049e14fe03646208de9819ff84e1675f"
    ),
    "binary_execution_prefix_exists": (
        "d4021e49514a61208d99766bd84f04b3e272d3c52c151ca8f9dccf1ad04f67eb"
    ),
    "binary_modular_execution_exists": (
        "103c179820815d1978bc1f147e0e7ad6b4289a98b8fb275c72f9ed9a66dd3c7c"
    ),
    "binary_modular_execution_power_correct": (
        "8f924863e885c353860e298956baced60a6a43d56e9d3f3f1c6267deac657321"
    ),
    "binary_modular_execution_horner_exists": (
        "345afe4884b51a608ea42c66b8c56f4ba9e6031a66ab52f2fb679ec5d93138e3"
    ),
    "binary_modular_execution_result_exists_unique": (
        "10df7f702c8ab056bfaeb1d391e7b06d9c69011b5f50bd3fef12e91de53ee9ce"
    ),
}


@dataclass(frozen=True, slots=True)
class _Factory:
    campaign: FrontierV22Campaign
    module: str
    factory: str
    rfc: str


_FACTORIES = (
    _Factory(
        FrontierV22Campaign.BINARY_LENGTH,
        "binary_length_candidate",
        "make_binary_length_candidate_theorems",
        "research/arithmetic-library/binary-length-rfc-v1.md",
    ),
    _Factory(
        FrontierV22Campaign.EUCLIDEAN_GCD_TRANSPORT,
        "euclidean_gcd_transport_candidate",
        "make_euclidean_gcd_transport_candidate_theorems",
        "research/arithmetic-library/euclidean-gcd-transport-rfc-v1.md",
    ),
    _Factory(
        FrontierV22Campaign.BINARY_MODULAR_EXECUTION,
        "binary_modular_execution_candidate",
        "make_binary_modular_execution_candidate_theorems",
        "research/arithmetic-library/binary-modular-execution-rfc-v1.md",
    ),
)


def _validate_parent() -> None:
    if (
        len(v21.ALPHA_ENTRIES) != PARENT_ALPHA_V21_COUNT
        or len(v21.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V21_COUNT
        or v21.ALPHA_V21_ENROLLMENT_SHA256 != PARENT_ALPHA_V21_ENROLLMENT_SHA256
        or v21.ALPHA_V21_IDENTITY_SHA256 != PARENT_ALPHA_V21_IDENTITY_SHA256
        or len(v21.STABLE_SPECS) != 432
    ):
        raise AlphaV22EnrollmentError("immutable fully checked Alpha-v21 parent changed")


@lru_cache(maxsize=1)
def alpha_v22_enrollment() -> AlphaV22Enrollment:
    _validate_parent()
    available = {entry.spec.name for entry in v21.ALPHA_ENTRIES}
    rows: list[TheoremSpec] = []
    sources: dict[str, str] = {}
    tests: dict[str, str] = {}
    rfcs: dict[str, str] = {}
    campaigns: dict[str, FrontierV22Campaign] = {}

    for owner in _FACTORIES:
        try:
            module = import_module(f".{owner.module}", package=__package__)
            candidates = tuple(getattr(module, owner.factory)(TheoremSpec))
        except (AttributeError, ImportError, OSError, TypeError, ValueError) as error:
            raise AlphaV22EnrollmentError(
                f"unavailable reviewed Alpha-v22 factory {owner.module}.{owner.factory}"
            ) from error
        expected = EXPECTED_CAMPAIGN_COUNTS[owner.campaign]
        if expected and len(candidates) != expected:
            raise AlphaV22EnrollmentError(
                f"exact Alpha-v22 campaign cardinality changed: {owner.campaign.value}"
            )
        for item in candidates:
            if type(item) is not TheoremSpec or item.name in available:
                raise AlphaV22EnrollmentError("invalid or duplicate Alpha-v22 theorem")
            missing = set(item.dependencies).difference(available)
            if missing:
                raise AlphaV22EnrollmentError(
                    f"forward Alpha-v22 dependencies for {item.name!r}: {sorted(missing)!r}"
                )
            if not item.script or any(
                "DNE" in command or command.startswith("use ") for command in item.script
            ):
                raise AlphaV22EnrollmentError(
                    f"Alpha-v22 theorem lacks an explicit constructive script: {item.name!r}"
                )
            _closed_formula(item.statement)
            sources[item.name] = f"peano-lab/py/peano_lab/library/{owner.module}.py"
            tests[item.name] = f"peano-lab/py/tests/test_{owner.module}.py"
            rfcs[item.name] = owner.rfc
            campaigns[item.name] = owner.campaign
            rows.append(item)
            available.add(item.name)

    if FRONTIER_V22_EXPECTED_COUNT and (
        len(rows) != FRONTIER_V22_EXPECTED_COUNT
        or sum(len(item.dependencies) for item in rows) != FRONTIER_V22_EXPECTED_EDGE_COUNT
        or sha256("\n".join(item.name for item in rows).encode()).hexdigest()
        != FRONTIER_V22_EXPECTED_NAMES_SHA256
    ):
        raise AlphaV22EnrollmentError("exact additive Alpha-v22 frontier changed")
    by_name = {item.name: item for item in rows}
    for name, expected in ROOT_STATEMENT_SHA256.items():
        actual = by_name.get(name)
        if actual is None or sha256(actual.statement.encode()).hexdigest() != expected:
            raise AlphaV22EnrollmentError(f"exact Alpha-v22 campaign root changed: {name}")

    return AlphaV22Enrollment(
        parent_entries=v21.ALPHA_ENTRIES,
        frontier_specs=tuple(rows),
        source_by_name=MappingProxyType(sources),
        test_by_name=MappingProxyType(tests),
        rfc_by_name=MappingProxyType(rfcs),
        campaign_by_name=MappingProxyType(campaigns),
    )


__all__ = (
    "AlphaV22Enrollment",
    "AlphaV22EnrollmentError",
    "EXPECTED_CAMPAIGN_COUNTS",
    "FRONTIER_V22_EXPECTED_COUNT",
    "FRONTIER_V22_EXPECTED_EDGE_COUNT",
    "FRONTIER_V22_EXPECTED_NAMES_SHA256",
    "FrontierV22Campaign",
    "PARENT_ALPHA_V21_COUNT",
    "PARENT_ALPHA_V21_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V21_IDENTITY_SHA256",
    "ROOT_STATEMENT_SHA256",
    "alpha_v22_enrollment",
)
