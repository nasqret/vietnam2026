"""Code-owned append manifest for the Bertrand Alpha-v10 tranche.

Alpha v9 is an immutable 1,076-row parent. This module appends exactly one
pinned Product-split support row and eight reviewed Primorial interval rows.
Enrollment records dependency-curried body evidence only; it never admits an
empty-context theorem or grants checked use.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from .editions_v9 import (
    ALPHA_ENTRIES as ALPHA_V9_ENTRIES,
    ALPHA_V9_ENROLLMENT_SHA256,
    ALPHA_V9_IDENTITY_SHA256,
    EditionEntry as EditionEntryV9,
)
from .theorems import TheoremSpec


class AlphaV10EnrollmentError(ValueError):
    """The frozen v9 parent or reviewed nine-row append is invalid."""


class BertrandV10EnrollmentOrigin(str, Enum):
    """Immutable first-enrollment origin for the Alpha-v10 suffix."""

    BERTRAND = "bertrand"


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV10:
    """One exact candidate factory and its executable audit sources."""

    origin: BertrandV10EnrollmentOrigin
    module: str
    factory: str
    test_path: str
    rfc_path: str
    factory_count: int
    selected_count: int
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV10Enrollment:
    """The sealed v9 parent and exact nine-row Bertrand append."""

    parent_entries: tuple[EditionEntryV9, ...]
    bertrand_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    origin_by_name: Mapping[str, BertrandV10EnrollmentOrigin]


PARENT_ALPHA_V9_COUNT = 1_076
PARENT_ALPHA_V9_ENROLLMENT_SHA256 = (
    "fe862a0c9d0c47f05ae6740cbc95c67e9b984a715397e18078c11d44f709046f"
)
PARENT_ALPHA_V9_IDENTITY_SHA256 = (
    "b74d7479d749500dbbd737f7cf5e7ea97a7998f8079233ed87b11c84823e2f80"
)
BERTRAND_V10_START_INDEX = PARENT_ALPHA_V9_COUNT
BERTRAND_PRIMORIAL_INTERVAL_RFC_PATH = (
    "research/arithmetic-library/"
    "ha-bertrand-primorial-interval-split-tranche-rfc-v1.md"
)
BERTRAND_RFC_PATHS = (BERTRAND_PRIMORIAL_INTERVAL_RFC_PATH,)


BERTRAND_V10_BODY_ENROLLMENT_MANIFEST: tuple[EnrollmentSourceV10, ...] = (
    # Select only the reviewed split row; the concat converse stays excluded.
    EnrollmentSourceV10(
        BertrandV10EnrollmentOrigin.BERTRAND,
        "finite_product_prefix_suffix_candidate",
        "make_finite_product_prefix_suffix_candidate_theorems",
        "peano-lab/py/tests/test_finite_product_prefix_suffix_candidate.py",
        BERTRAND_PRIMORIAL_INTERVAL_RFC_PATH,
        2,
        1,
        ("beta_product_prefix_suffix_split",),
    ),
    # Offset selector products and exact prefix/interval splitting.
    EnrollmentSourceV10(
        BertrandV10EnrollmentOrigin.BERTRAND,
        "bertrand_primorial_interval_candidate",
        "make_bertrand_primorial_interval_candidate_theorems",
        "peano-lab/py/tests/test_bertrand_primorial_interval_candidate.py",
        BERTRAND_PRIMORIAL_INTERVAL_RFC_PATH,
        8,
        8,
        (
            "primorial_interval_factor_prefix_extend",
            "primorial_interval_factor_prefix_exists",
            "primorial_interval_factor_prefix_transport_entry",
            "primorial_interval_exists",
            "primorial_interval_functional",
            "primorial_interval_factor_prefix_shift",
            "primorial_factor_prefix_restrict_add",
            "primorial_prefix_interval_split",
        ),
    ),
)

BERTRAND_V10_EXPECTED_NAMES = tuple(
    name
    for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
    for name in source.names
)
BERTRAND_V10_EXPECTED_COUNTS = (1, 8)
BERTRAND_V10_EXPECTED_MICROBATCH_SOURCE_COUNTS = (2,)
BERTRAND_V10_MICROBATCH_COUNTS = (9,)
BERTRAND_V10_MICROBATCH_NAMES = (BERTRAND_V10_EXPECTED_NAMES,)
BERTRAND_V10_EXPECTED_COUNT = 9


def _load_source(source: EnrollmentSourceV10) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaV10EnrollmentError(
            f"missing Bertrand factory {source.module}.{source.factory}"
        )
    produced_all = tuple(factory(TheoremSpec))
    if any(type(spec) is not TheoremSpec for spec in produced_all):
        raise AlphaV10EnrollmentError(
            f"{source.module}.{source.factory} returned a non-TheoremSpec value"
        )
    if len(produced_all) != source.factory_count:
        raise AlphaV10EnrollmentError(
            f"Bertrand factory {source.module} changed full row count"
        )
    if not 0 < source.selected_count <= source.factory_count:
        raise AlphaV10EnrollmentError(
            f"Bertrand factory {source.module} has invalid prefix selection"
        )
    produced = produced_all[: source.selected_count]
    produced_names = tuple(spec.name for spec in produced)
    if produced_names != source.names:
        raise AlphaV10EnrollmentError(
            f"Bertrand factory {source.module} changed rows or order: "
            f"{produced_names!r}"
        )
    if len(set(produced_names)) != len(produced_names):
        raise AlphaV10EnrollmentError(
            f"Bertrand factory {source.module} returned duplicate names"
        )
    return produced


@lru_cache(maxsize=1)
def alpha_v10_enrollment() -> AlphaV10Enrollment:
    """Return the exact v9 ledger plus the non-admitting reviewed append."""

    if len(ALPHA_V9_ENTRIES) != PARENT_ALPHA_V9_COUNT:
        raise AlphaV10EnrollmentError("Alpha v9 parent count changed")
    if ALPHA_V9_ENROLLMENT_SHA256 != PARENT_ALPHA_V9_ENROLLMENT_SHA256:
        raise AlphaV10EnrollmentError("Alpha v9 enrollment identity changed")
    if ALPHA_V9_IDENTITY_SHA256 != PARENT_ALPHA_V9_IDENTITY_SHA256:
        raise AlphaV10EnrollmentError("Alpha v9 edition identity changed")

    available = {entry.spec.name for entry in ALPHA_V9_ENTRIES}
    if len(available) != PARENT_ALPHA_V9_COUNT:
        raise AlphaV10EnrollmentError("Alpha v9 parent contains duplicate names")

    specs: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    test_by_name: dict[str, str] = {}
    rfc_by_name: dict[str, str] = {}
    origin_by_name: dict[str, BertrandV10EnrollmentOrigin] = {}
    prefix = "peano-lab/py/peano_lab/library"
    for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST:
        path = f"{prefix}/{source.module}.py"
        for spec in _load_source(source):
            if spec.name in available:
                raise AlphaV10EnrollmentError(
                    f"Bertrand theorem collides with an earlier row: {spec.name!r}"
                )
            missing = tuple(
                dependency
                for dependency in spec.dependencies
                if dependency not in available
            )
            if missing:
                raise AlphaV10EnrollmentError(
                    f"Bertrand theorem {spec.name!r} has missing or forward "
                    f"dependencies {missing!r}"
                )
            if any("DNE" in command for command in spec.script):
                raise AlphaV10EnrollmentError(
                    f"Bertrand theorem {spec.name!r} contains DNE"
                )
            available.add(spec.name)
            specs.append(spec)
            source_by_name[spec.name] = path
            test_by_name[spec.name] = source.test_path
            rfc_by_name[spec.name] = source.rfc_path
            origin_by_name[spec.name] = source.origin

    result = tuple(specs)
    if tuple(spec.name for spec in result) != BERTRAND_V10_EXPECTED_NAMES:
        raise AlphaV10EnrollmentError("Bertrand v10 append order changed")
    source_counts = tuple(
        len(source.names) for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
    )
    if source_counts != BERTRAND_V10_EXPECTED_COUNTS:
        raise AlphaV10EnrollmentError("Bertrand v10 source-block counts changed")
    source_boundaries = BERTRAND_V10_EXPECTED_MICROBATCH_SOURCE_COUNTS
    if sum(source_boundaries) != len(source_counts):
        raise AlphaV10EnrollmentError("Bertrand v10 microbatch boundary changed")
    microbatch_counts: list[int] = []
    offset = 0
    for source_count in source_boundaries:
        microbatch_counts.append(sum(source_counts[offset : offset + source_count]))
        offset += source_count
    if tuple(microbatch_counts) != BERTRAND_V10_MICROBATCH_COUNTS:
        raise AlphaV10EnrollmentError("Bertrand v10 microbatch row counts changed")
    microbatch_names: list[tuple[str, ...]] = []
    offset = 0
    for row_count in BERTRAND_V10_MICROBATCH_COUNTS:
        microbatch_names.append(
            tuple(spec.name for spec in result[offset : offset + row_count])
        )
        offset += row_count
    if tuple(microbatch_names) != BERTRAND_V10_MICROBATCH_NAMES:
        raise AlphaV10EnrollmentError("Bertrand v10 microbatch order changed")
    source_rfc_paths = tuple(
        dict.fromkeys(
            source.rfc_path
            for source in BERTRAND_V10_BODY_ENROLLMENT_MANIFEST
        )
    )
    if source_rfc_paths != BERTRAND_RFC_PATHS:
        raise AlphaV10EnrollmentError("Bertrand v10 RFC binding changed")
    if len(result) != BERTRAND_V10_EXPECTED_COUNT:
        raise AlphaV10EnrollmentError("Bertrand v10 append count changed")
    return AlphaV10Enrollment(
        parent_entries=ALPHA_V9_ENTRIES,
        bertrand_specs=result,
        source_by_name=MappingProxyType(source_by_name),
        test_by_name=MappingProxyType(test_by_name),
        rfc_by_name=MappingProxyType(rfc_by_name),
        origin_by_name=MappingProxyType(origin_by_name),
    )


__all__ = [
    "AlphaV10Enrollment",
    "AlphaV10EnrollmentError",
    "BERTRAND_PRIMORIAL_INTERVAL_RFC_PATH",
    "BERTRAND_RFC_PATHS",
    "BERTRAND_V10_BODY_ENROLLMENT_MANIFEST",
    "BERTRAND_V10_EXPECTED_COUNT",
    "BERTRAND_V10_EXPECTED_COUNTS",
    "BERTRAND_V10_EXPECTED_MICROBATCH_SOURCE_COUNTS",
    "BERTRAND_V10_EXPECTED_NAMES",
    "BERTRAND_V10_MICROBATCH_COUNTS",
    "BERTRAND_V10_MICROBATCH_NAMES",
    "BERTRAND_V10_START_INDEX",
    "BertrandV10EnrollmentOrigin",
    "EnrollmentSourceV10",
    "PARENT_ALPHA_V9_COUNT",
    "PARENT_ALPHA_V9_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V9_IDENTITY_SHA256",
    "alpha_v10_enrollment",
]
