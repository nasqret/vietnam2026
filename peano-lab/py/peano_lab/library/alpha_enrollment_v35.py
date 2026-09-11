"""Artifact-free, exact 95-row Jordan enrollment over immutable Alpha-v34.

The original 96-row source includes one explicitly AST-equal inherited alias.
No original proof bytes or old edition objects are rewritten by enrollment.
"""
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
from hashlib import sha256
from types import MappingProxyType
from typing import Mapping

from . import editions_v34 as v34
from . import campaign_research_v35_closure as research
from .campaign_research_v35_closure import (
    FACTORIES, FAMILIES, FRONTIER_NEW_NAMES, EXPECTED_RESEARCH_METADATA_SHA256,
    PARENT_ALPHA_V34_COUNT, PARENT_ALPHA_V34_SPECS_SHA256,
    PARENT_ALPHA_V34_ENROLLMENT_SHA256, PARENT_ALPHA_V34_IDENTITY_SHA256,
    _specs_digest,
)
from .theorems import TheoremSpec, _closed_formula


class AlphaV35EnrollmentError(ValueError):
    """The unchanged parent or exact additive source/dependency map changed."""


class FrontierV35Campaign(str, Enum):
    JORDAN_TOTIENT = "jordan-totient"


@dataclass(frozen=True, slots=True)
class AlphaV35Enrollment:
    parent_entries: tuple[v34.EditionEntry, ...]
    frontier_specs: tuple[TheoremSpec, ...]
    source_by_name: Mapping[str, str]
    test_by_name: Mapping[str, str]
    rfc_by_name: Mapping[str, str]
    campaign_by_name: Mapping[str, FrontierV35Campaign]


FRONTIER_V35_EXPECTED_COUNT = 95
FRONTIER_V35_EXPECTED_EDGE_COUNT = 254
FRONTIER_V35_EXPECTED_COMMAND_COUNT = 5335
FRONTIER_V35_EXPECTED_NAMES_SHA256 = research.EXPECTED_RESEARCH_NAMES_SHA256
FRONTIER_V35_EXPECTED_SPECS_SHA256 = research.EXPECTED_RESEARCH_SPECS_SHA256
EXPECTED_CAMPAIGN_COUNTS = MappingProxyType({FrontierV35Campaign.JORDAN_TOTIENT: 95})
# These are raw source counts, deliberately not 96 new admissions.
EXPECTED_FACTORY_COUNTS = MappingProxyType({
    module: sum(owner.count for owner in owners)
    for module, owners in research.FACTORY_BY_MODULE.items()
})
EXPECTED_FACTORY_SOURCE_SHA256 = MappingProxyType({
    module: owners[0].source_sha256 for module, owners in research.FACTORY_BY_MODULE.items()
})
ROOT_STATEMENT_SHA256 = FAMILIES[0].principal_statement_sha256


def _validate_parent():
    v34.require_research_seal()
    if (len(v34.ALPHA_ENTRIES) != PARENT_ALPHA_V34_COUNT
            or len(v34.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V34_COUNT
            or v34.ALPHA_V34_ENROLLMENT_SHA256 != PARENT_ALPHA_V34_ENROLLMENT_SHA256
            or v34.ALPHA_V34_IDENTITY_SHA256 != PARENT_ALPHA_V34_IDENTITY_SHA256
            or _specs_digest(v34.ALPHA_CHECKED_SPECS) != PARENT_ALPHA_V34_SPECS_SHA256
            or len(v34.STABLE_SPECS) != 432):
        raise AlphaV35EnrollmentError("the immutable checked Alpha-v34 parent changed")


@lru_cache(maxsize=1)
def alpha_v35_enrollment():
    research.validate_research_metadata()
    _validate_parent()
    rows = research.normalize_owned_specs(research.raw_owned_specs(), v34.ALPHA_CHECKED_SPECS)
    if (len(rows) != 95 or tuple(row.name for row in rows) != FRONTIER_NEW_NAMES
            or _specs_digest(rows) != FRONTIER_V35_EXPECTED_SPECS_SHA256
            or sha256("\n".join(row.name for row in rows).encode()).hexdigest()
            != FRONTIER_V35_EXPECTED_NAMES_SHA256
            or sum(len(row.dependencies) for row in rows) != 254
            or sum(len(row.script) for row in rows) != 5335):
        raise AlphaV35EnrollmentError("the exact 95 novel Jordan specifications changed")
    available = {item.spec.name for item in v34.ALPHA_ENTRIES}
    sources, tests, rfcs, campaigns = {}, {}, {}, {}
    for item in rows:
        if (type(item) is not TheoremSpec or item.name in available
                or type(item.dependencies) is not tuple
                or len(set(item.dependencies)) != len(item.dependencies)
                or not set(item.dependencies) <= available
                or type(item.script) is not tuple or not item.script
                or any(type(command) is not str or not command.strip()
                    or "DNE" in command or command.startswith(("use ", "admit", "sorry"))
                    for command in item.script)):
            raise AlphaV35EnrollmentError("invalid additive constructive theorem: " + item.name)
        _closed_formula(item.statement)
        owner = research.FACTORIES[research._SOURCE_OWNER_INDICES[item.name]]
        available.add(item.name)
        sources[item.name] = owner.source
        tests[item.name] = owner.test
        rfcs[item.name] = "research/arithmetic-library/" + owner.rfc
        campaigns[item.name] = FrontierV35Campaign.JORDAN_TOTIENT
    if Counter(campaigns.values()) != EXPECTED_CAMPAIGN_COUNTS:
        raise AlphaV35EnrollmentError("exact Jordan admission ownership changed")
    by_name = {row.name: row for row in rows}
    for name, digest in ROOT_STATEMENT_SHA256.items():
        if name not in by_name or sha256(by_name[name].statement.encode()).hexdigest() != digest:
            raise AlphaV35EnrollmentError("an exact principal statement changed: " + name)
    return AlphaV35Enrollment(v34.ALPHA_ENTRIES, rows, MappingProxyType(sources),
        MappingProxyType(tests), MappingProxyType(rfcs), MappingProxyType(campaigns))
