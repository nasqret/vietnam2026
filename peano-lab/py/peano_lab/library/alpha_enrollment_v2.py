"""Code-owned append manifest for the Alpha v2 K3C tranche.

Channel v1 is immutable.  This module imports its exact 885-row ledger and
adds only the frozen K3C factories, in dependency-topological source order.
It constructs theorem specifications but never replays or admits a proof.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from importlib import import_module
from types import MappingProxyType
from typing import Mapping

from .editions import (
    ALPHA_EDITION as ALPHA_V1_EDITION,
    ALPHA_ENROLLMENT_SHA256 as ALPHA_V1_ENROLLMENT_SHA256,
    ALPHA_ENTRIES as ALPHA_V1_ENTRIES,
    EditionEntry as EditionEntryV1,
)
from .theorems import TheoremSpec


class AlphaV2EnrollmentError(ValueError):
    """The frozen parent ledger or K3C append manifest is inconsistent."""


@dataclass(frozen=True, slots=True)
class EnrollmentSourceV2:
    """One exact factory in the ordered K3C append."""

    module: str
    factory: str
    names: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AlphaV2Enrollment:
    """The sealed v1 parent and exact K3C append specifications."""

    parent_entries: tuple[EditionEntryV1, ...]
    k3c_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]


PARENT_ALPHA_V1_COUNT = 885
PARENT_ALPHA_V1_ENROLLMENT_SHA256 = (
    "7371461aa930071f00007f766f899cef88c4126a5ddf576f93d79e336bc65c49"
)
PARENT_ALPHA_V1_IDENTITY_SHA256 = (
    "b464c50cced007f06aa7bdf0d61ad6687a09c0e5bfb5c29f1879ffc68b016588"
)
K3C_START_INDEX = PARENT_ALPHA_V1_COUNT


K3C_BODY_ENROLLMENT_MANIFEST: tuple[EnrollmentSourceV2, ...] = (
    EnrollmentSourceV2(
        "ha_cell_list_validity_candidate",
        "make_ha_cell_list_validity_candidate_theorems",
        (
            "cell_list_valid_nil",
            "cell_list_valid_cell_intro",
            "cell_list_valid_cases",
            "cell_list_valid_cell_elim",
            "list_at_implies_cell_list_valid",
        ),
    ),
    EnrollmentSourceV2(
        "ha_cell_list_membership_candidate",
        "make_ha_cell_list_membership_candidate_theorems",
        (
            "list_member_implies_cell_list_valid",
            "list_member_nil_false",
            "list_member_cell_intro_head",
            "list_member_cell_intro_tail",
            "list_member_cell_elim",
            "list_member_cell_iff",
            "list_member_pointwise_transport",
        ),
    ),
    EnrollmentSourceV2(
        "ha_cell_list_interface_candidate",
        "make_ha_cell_list_interface_candidate_theorems",
        (
            "list_at_exists_unique",
            "cell_list_nonempty_iff_head_exists",
            "cell_list_code_eq_lookup_values",
            "cell_list_code_eq_iff_pointwise",
            "cell_list_decompose_unique",
        ),
    ),
)

K3C_EXPECTED_NAMES = tuple(
    name for source in K3C_BODY_ENROLLMENT_MANIFEST for name in source.names
)
K3C_EXPECTED_COUNT = 17


def _load_source(
    source: EnrollmentSourceV2,
) -> tuple[TheoremSpec, ...]:
    module = import_module(f"{__package__}.{source.module}")
    factory = getattr(module, source.factory, None)
    if not callable(factory):
        raise AlphaV2EnrollmentError(
            f"missing K3C factory {source.module}.{source.factory}"
        )
    produced = tuple(factory(TheoremSpec))
    if any(type(spec) is not TheoremSpec for spec in produced):
        raise AlphaV2EnrollmentError(
            f"{source.module}.{source.factory} returned a non-TheoremSpec value"
        )
    names = tuple(spec.name for spec in produced)
    if names != source.names:
        raise AlphaV2EnrollmentError(
            f"K3C factory {source.module} changed rows or order: {names!r}"
        )
    if len(set(names)) != len(names):
        raise AlphaV2EnrollmentError(
            f"K3C factory {source.module} returned duplicate names"
        )
    return produced


@lru_cache(maxsize=1)
def alpha_v2_enrollment() -> AlphaV2Enrollment:
    """Return the validated v1 ledger plus the non-admitting K3C append."""

    if len(ALPHA_V1_ENTRIES) != PARENT_ALPHA_V1_COUNT:
        raise AlphaV2EnrollmentError("Alpha v1 parent count changed")
    if ALPHA_V1_ENROLLMENT_SHA256 != PARENT_ALPHA_V1_ENROLLMENT_SHA256:
        raise AlphaV2EnrollmentError("Alpha v1 enrollment identity changed")
    if ALPHA_V1_EDITION.identity_sha256 != PARENT_ALPHA_V1_IDENTITY_SHA256:
        raise AlphaV2EnrollmentError("Alpha v1 edition identity changed")

    parent_names = {entry.spec.name for entry in ALPHA_V1_ENTRIES}
    if len(parent_names) != PARENT_ALPHA_V1_COUNT:
        raise AlphaV2EnrollmentError("Alpha v1 parent contains duplicate names")

    specs: list[TheoremSpec] = []
    source_by_name: dict[str, str] = {}
    available = set(parent_names)
    prefix = "peano-lab/py/peano_lab/library"
    for source in K3C_BODY_ENROLLMENT_MANIFEST:
        path = f"{prefix}/{source.module}.py"
        for spec in _load_source(source):
            if spec.name in available:
                raise AlphaV2EnrollmentError(
                    f"K3C theorem collides with an earlier row: {spec.name!r}"
                )
            missing = tuple(
                dependency
                for dependency in spec.dependencies
                if dependency not in available
            )
            if missing:
                raise AlphaV2EnrollmentError(
                    f"K3C theorem {spec.name!r} has missing or forward "
                    f"dependencies {missing!r}"
                )
            available.add(spec.name)
            specs.append(spec)
            source_by_name[spec.name] = path

    result = tuple(specs)
    if tuple(spec.name for spec in result) != K3C_EXPECTED_NAMES:
        raise AlphaV2EnrollmentError("K3C append order changed")
    if len(result) != K3C_EXPECTED_COUNT:
        raise AlphaV2EnrollmentError("K3C append count changed")
    return AlphaV2Enrollment(
        parent_entries=ALPHA_V1_ENTRIES,
        k3c_specs=result,
        source_by_name=MappingProxyType(source_by_name),
    )


__all__ = [
    "AlphaV2Enrollment",
    "AlphaV2EnrollmentError",
    "EnrollmentSourceV2",
    "K3C_BODY_ENROLLMENT_MANIFEST",
    "K3C_EXPECTED_COUNT",
    "K3C_EXPECTED_NAMES",
    "K3C_START_INDEX",
    "PARENT_ALPHA_V1_COUNT",
    "PARENT_ALPHA_V1_ENROLLMENT_SHA256",
    "PARENT_ALPHA_V1_IDENTITY_SHA256",
    "alpha_v2_enrollment",
]
