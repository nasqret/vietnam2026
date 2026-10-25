"""Code-owned append manifest for the Bertrand Alpha-v9 tranche.

Alpha v8 is an immutable 1,055-row parent.  This module appends exactly
twenty-one reviewed Primorial rows in two dependency-topological
microbatches of ten and eleven rows.  Enrollment records dependency-curried
body evidence only; it never admits an empty-context theorem or grants
checked use.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from .editions_v8 import (
    ALPHA_ENTRIES as ALPHA_V8_ENTRIES,
    ALPHA_V8_ENROLLMENT_SHA256,
    ALPHA_V8_IDENTITY_SHA256,
    EditionEntry as EditionEntryV8,
)
from .theorems import TheoremSpec


class AlphaV9EnrollmentError(ValueError):
    """The frozen v8 parent or reviewed twenty-one-row append is invalid."""


class BertrandV9EnrollmentOrigin(str, Enum):
    """Immutable first-enrollment origin for the Alpha-v9 suffix."""

    BERTRAND = "bertrand"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV9:
    """One exact candidate factory and its executable audit sources."""

    origin: BertrandV9EnrollmentOrigin
    module: str
    factory: str
    test_path: str
    rfc_path: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV9Enrollment:
    """The sealed v8 parent and exact twenty-one-row Bertrand append."""

    parent_entries: tuple[EditionEntryV8, ...]
    bertrand_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    origin_by_name: Mapping[str, BertrandV9EnrollmentOrigin]


PARENT_ALPHA_V8_COUNT = 1_055
PARENT_ALPHA_V8_ENROLLMENT_SHA256 = (
    "a01b0224be070b09551c6ef7b50f9c32688448f48465b80ca97a23c01effd5c2"
)
PARENT_ALPHA_V8_IDENTITY_SHA256 = (
    "2101b7b384ec9791c41d07d8115123d6842729615a0084ce87cead619bc8c123"
)
BERTRAND_V9_START_INDEX = PARENT_ALPHA_V8_COUNT
BERTRAND_PRIMORIAL_FOUNDATION_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-primorial-foundation-tranche-rfc-v1.md"
)
BERTRAND_PRIMORIAL_MEMBERSHIP_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-primorial-membership-tranche-rfc-v1.md"
)
BERTRAND_RFC_PATHS = (
    BERTRAND_PRIMORIAL_FOUNDATION_RFC_PATH,
    BERTRAND_PRIMORIAL_MEMBERSHIP_RFC_PATH,
)


BERTRAND_V9_BODY_ENROLLMENT_MANIFEST: tuple[EnrollmentSourceV9, ...] = (
    # Microbatch one: conservative Primorial relation and recursive laws.
    EnrollmentSourceV9(
        BertrandV9EnrollmentOrigin.BERTRAND,
        "bertrand_primorial_foundation_candidate",
        "make_bertrand_primorial_foundation_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_primorial_foundation_candidate.py",
        BERTRAND_PRIMORIAL_FOUNDATION_RFC_PATH,
        (
            "primorial_factor_choice_exists",
            "primorial_factor_choice_functional",
            "primorial_factor_prefix_extend",
            "primorial_factor_prefix_exists",
            "primorial_factor_prefix_transport_entry",
            "primorial_exists",
            "primorial_functional",
            "primorial_zero",
            "primorial_succ_decompose",
            "primorial_positive",
        ),
    ),
    # Microbatch two: prime membership, divisibility, and monotonicity.
    EnrollmentSourceV9(
        BertrandV9EnrollmentOrigin.BERTRAND,
        "bertrand_primorial_membership_candidate",
        "make_bertrand_primorial_membership_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_primorial_membership_candidate.py",
        BERTRAND_PRIMORIAL_MEMBERSHIP_RFC_PATH,
        (
            "primorial_index_eq_transport",
            "primorial_factor_choice_prime_divisor_eq",
            "primorial_prime_divides_of_le",
            "primorial_prime_le_of_divides",
            "primorial_prime_divides_iff_le",
            "primorial_succ_factor",
            "primorial_succ_divides",
            "primorial_add_length_divides",
            "primorial_le_divides",
            "primorial_le_positive_quotient",
            "primorial_le_monotone",
        ),
    ),
)

BERTRAND_V9_EXPECTED_NAMES = tuple(
    name
    for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST
    for name in source.names
)
BERTRAND_V9_EXPECTED_COUNTS = (10, 11)
BERTRAND_V9_EXPECTED_MICROBATCH_SOURCE_COUNTS = (1, 1)
BERTRAND_V9_MICROBATCH_COUNTS = (10, 11)
BERTRAND_V9_MICROBATCH_NAMES = tuple(
    source.names for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST
)
BERTRAND_V9_EXPECTED_COUNT = 21


def _load_source(source: EnrollmentSourceV9) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaV9EnrollmentError(
            f"missing Bertrand factory {source.module}.{source.factory}"
        )
    produced = tuple(factory(TheoremSpec))
    if any(type(spec) is not TheoremSpec for spec in produced):
        raise AlphaV9EnrollmentError(
            f"{source.module}.{source.factory} returned a non-TheoremSpec value"
        )
    produced_names = tuple(spec.name for spec in produced)
    if produced_names != source.names:
        raise AlphaV9EnrollmentError(
            f"Bertrand factory {source.module} changed rows or order: "
            f"{produced_names!r}"
        )
    if len(set(produced_names)) != len(produced_names):
        raise AlphaV9EnrollmentError(
            f"Bertrand factory {source.module} returned duplicate names"
        )
    return produced


@lru_cache(maxsize=1)
def alpha_v9_enrollment() -> AlphaV9Enrollment:
    """Return the exact v8 ledger plus the non-admitting reviewed append."""

    if len(ALPHA_V8_ENTRIES) != PARENT_ALPHA_V8_COUNT:
        raise AlphaV9EnrollmentError("Alpha v8 parent count changed")
    if ALPHA_V8_ENROLLMENT_SHA256 != PARENT_ALPHA_V8_ENROLLMENT_SHA256:
        raise AlphaV9EnrollmentError("Alpha v8 enrollment identity changed")
    if ALPHA_V8_IDENTITY_SHA256 != PARENT_ALPHA_V8_IDENTITY_SHA256:
        raise AlphaV9EnrollmentError("Alpha v8 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V8_ENTRIES}
    if len(available) != PARENT_ALPHA_V8_COUNT:
        raise AlphaV9EnrollmentError("Alpha v8 parent contains duplicate names")

    specs: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    rfc_by_name: dict[str, str] = {}
    origin_by_name: dict[str, BertrandV9EnrollmentOrigin] = {}
    prefix = "peano-lab/py/peano_lab/library"
    for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST:
        path = f"{prefix}/{source.module}.py"
        for spec in _load_source(source):
            if spec.name in available:
                raise AlphaV9EnrollmentError(
                    f"Bertrand theorem collides with an earlier row: {spec.name!r}"
                )
            missing = tuple(
                dependency
                for dependency in spec.dependencies
                if dependency not in available
            )
            if missing:
                raise AlphaV9EnrollmentError(
                    f"Bertrand theorem {spec.name!r} has missing or forward "
                    f"dependencies {missing!r}"
                )
            if any("DNE" in command for command in spec.script):
                raise AlphaV9EnrollmentError(
                    f"Bertrand theorem {spec.name!r} contains DNE"
                )
            available.add(spec.name)
            specs.append(spec)
            source_by_name[spec.name] = path
            test_by_name[spec.name] = source.test_path
            rfc_by_name[spec.name] = source.rfc_path
            origin_by_name[spec.name] = source.origin

    result = tuple(specs)
    if tuple(spec.name for spec in result) != BERTRAND_V9_EXPECTED_NAMES:
        raise AlphaV9EnrollmentError("Bertrand v9 append order changed")
    source_counts = tuple(
        len(source.names) for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST
    )
    if source_counts != BERTRAND_V9_EXPECTED_COUNTS:
        raise AlphaV9EnrollmentError("Bertrand v9 source-block counts changed")
    first_sources, second_sources = BERTRAND_V9_EXPECTED_MICROBATCH_SOURCE_COUNTS
    if first_sources + second_sources != len(source_counts):
        raise AlphaV9EnrollmentError("Bertrand v9 microbatch boundary changed")
    microbatch_counts = (
        sum(source_counts[:first_sources]),
        sum(source_counts[first_sources:]),
    )
    if microbatch_counts != BERTRAND_V9_MICROBATCH_COUNTS:
        raise AlphaV9EnrollmentError("Bertrand v9 microbatch row counts changed")
    first_row_count = BERTRAND_V9_MICROBATCH_COUNTS[0]
    microbatch_names = (
        tuple(spec.name for spec in result[:first_row_count]),
        tuple(spec.name for spec in result[first_row_count:]),
    )
    if microbatch_names != BERTRAND_V9_MICROBATCH_NAMES:
        raise AlphaV9EnrollmentError("Bertrand v9 microbatch order changed")
    if tuple(
        source.rfc_path for source in BERTRAND_V9_BODY_ENROLLMENT_MANIFEST
    ) != BERTRAND_RFC_PATHS:
        raise AlphaV9EnrollmentError("Bertrand v9 RFC binding changed")
    if len(result) != BERTRAND_V9_EXPECTED_COUNT:
        raise AlphaV9EnrollmentError("Bertrand v9 append count changed")
    return AlphaV9Enrollment(
        parent_entries=ALPHA_V8_ENTRIES,
        bertrand_specs=result,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        rfc_by_name=MappingProxyType(rfc_by_name),
        origin_by_name=MappingProxyType(origin_by_name),
    )


__all__ = [
    "AlphaV9Enrollment",
    "AlphaV9EnrollmentError",
    "BERTRAND_PRIMORIAL_FOUNDATION_RFC_PATH",
    "BERTRAND_PRIMORIAL_MEMBERSHIP_RFC_PATH",
    "BERTRAND_RFC_PATHS",
    "BERTRAND_V9_BODY_ENROLLMENT_MANIFEST",
    "BERTRAND_V9_EXPECTED_COUNT",
    "BERTRAND_V9_EXPECTED_COUNTS",
    "BERTRAND_V9_EXPECTED_MICROBATCH_SOURCE_COUNTS",
    "BERTRAND_V9_EXPECTED_NAMES",
    "BERTRAND_V9_MICROBATCH_COUNTS",
    "BERTRAND_V9_MICROBATCH_NAMES",
    "BERTRAND_V9_START_INDEX",
    "BertrandV9EnrollmentOrigin",
    "EnrollmentSourceV9",
    "PARENT_ALPHA_V8_COUNT",
    "PARENT_ALPHA_V8_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V8_IDENTITY_SHA256",
    "alpha_v9_enrollment",
]
