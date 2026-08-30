"""Additive conservative definitions for the three fully closed v23 milestones.

Each abbreviation is an exact hygienic expansion from its original-kernel
candidate module.  Historical PD/ND identities remain immutable.  In
particular, the three-modulo-four surface is checked against the existing
Quadratic Reciprocity definition ``Mod4Three`` and reuses ``PD0012`` rather
than inventing a logically identical definition with a new identity.
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
import sys
from types import MappingProxyType


ROOT = Path(__file__).resolve().parents[1]
PY_ROOT = ROOT / "peano-lab" / "py"
if str(PY_ROOT) not in sys.path:
    sys.path.insert(0, str(PY_ROOT))

from constructive_transport_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
)
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.library.binary_digit_extraction_candidate import (  # noqa: E402
    binary_canonical_exponent_digit_code,
    binary_complete_modular_execution,
    binary_execution_operation_count,
    binary_exponent_digit_code,
)
from peano_lab.library.defined_syntax import DefinitionSpec, _definition  # noqa: E402
from peano_lab.library.euclidean_logarithmic_bound_candidate import (  # noqa: E402
    euclidean_bounded_trace,
    euclidean_logarithmic_execution,
)
from peano_lab.library.primes_three_mod_four_candidate import (  # noqa: E402
    euclid_three_number,
    three_mod_four_prime_divisor,
    three_mod_four_relation,
)


def _construct(
    *,
    identifier: str,
    name: str,
    parameters: tuple[str, ...],
    source: str,
    summary: str,
    dependencies: tuple[str, ...] = (),
) -> DefinitionSpec:
    return _definition(
        stable_id=identifier,
        name=name,
        parameters=parameters,
        template_source=source,
        summary=summary,
        category="constructive_milestone_closure",
        priority="P2",
        conceptual_dependencies=dependencies,
    )


_HISTORICAL_MOD4_THREE = HISTORICAL_DEFINITIONS_BY_NAME.get("Mod4Three")
if (
    _HISTORICAL_MOD4_THREE is None
    or _HISTORICAL_MOD4_THREE.stable_id != "PD0012"
    or _HISTORICAL_MOD4_THREE.parameters != ("n",)
):
    raise ValueError("the immutable Quadratic Reciprocity Mod4Three identity changed")
if parse_formula_in_context(three_mod_four_relation("n", tag="milestone"), ["n"]) != (
    _HISTORICAL_MOD4_THREE.template_formula
):
    raise ValueError("the three-mod-four campaign does not reuse the exact Mod4Three AST")


MILESTONE_CLOSURE_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(
        identifier="ND0038",
        name="EuclideanBoundedTrace",
        parameters=("a", "b", "B"),
        source=euclidean_bounded_trace("a", "b", "B", tag="milestone"),
        summary="An actual complete beta-coded Euclidean history with a constructive witnessed step budget.",
        dependencies=("ContinuedFractionTrace", "Le"),
    ),
    _construct(
        identifier="ND0039",
        name="EuclideanLogarithmicExecution",
        parameters=("a", "b", "ell", "g", "k"),
        source=euclidean_logarithmic_execution("a", "b", "ell", "g", "k", tag="milestone"),
        summary="A canonical binary-length witness and a terminal-gcd-anchored Euclidean execution satisfying k≤2ell+1.",
        dependencies=("BitLen", "EuclideanAnchoredExecution", "Le"),
    ),
    _construct(
        identifier="ND0040",
        name="BinaryExponentDigitCode",
        parameters=("e", "ell", "b", "c"),
        source=binary_exponent_digit_code("e", "ell", "b", "c", tag="milestone"),
        summary="A genuine beta-coded binary digit prefix whose base-two Horner value is exactly the supplied exponent.",
        dependencies=("BinaryDigitPrefix", "Horner"),
    ),
    _construct(
        identifier="ND0041",
        name="BinaryCanonicalExponentDigitCode",
        parameters=("e", "ell", "b", "c"),
        source=binary_canonical_exponent_digit_code("e", "ell", "b", "c", tag="milestone"),
        summary="An actual beta-coded exponent digit prefix of exactly its unique canonical binary length.",
        dependencies=("BitLen", "BinaryExponentDigitCode"),
    ),
    _construct(
        identifier="ND0042",
        name="BinaryCompleteModularExecution",
        parameters=("e", "a", "m", "ell", "b", "c", "r"),
        source=binary_complete_modular_execution(
            "e", "a", "m", "ell", "b", "c", "r", tag="milestone"
        ),
        summary="Canonical beta-coded exponent digits, the actual square-and-multiply accumulator trace, and its independently certified modular-power output.",
        dependencies=(
            "BinaryCanonicalExponentDigitCode",
            "BinaryModularExecution",
            "BinaryModularPower",
        ),
    ),
    _construct(
        identifier="ND0043",
        name="BinaryExecutionOperationCount",
        parameters=("b", "c", "ell", "k"),
        source=binary_execution_operation_count("b", "c", "ell", "k", tag="milestone"),
        summary="The exact square-and-multiply operation count 2+2ell+popcount of the actual beta-coded digit prefix.",
        dependencies=("BitCount",),
    ),
    _construct(
        identifier="ND0044",
        name="PrimeThreeModFourDivisor",
        parameters=("n", "p"),
        source=three_mod_four_prime_divisor("n", "p", tag="milestone"),
        summary="An actual prime divisor of n together with a witnessed residue p=4q+3.",
        dependencies=("Prime", "Mod4Three", "Dvd"),
    ),
    _construct(
        identifier="ND0045",
        name="EuclidThreeNumber",
        parameters=("c", "n"),
        source=euclid_three_number("c", "n", tag="milestone"),
        summary="The subtraction-free Euclidean number n=4d+3 with positive common multiple c=S d.",
        dependencies=("Mod4Three",),
    ),
)


_KNOWN = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_SEEN_IDS = {definition.stable_id for definition in _KNOWN.values()}
if len(_SEEN_IDS) != len(_KNOWN):
    raise ValueError("the immutable reviewed definition registry repeats an identity")
for offset, definition in enumerate(MILESTONE_CLOSURE_DEFINITIONS, start=38):
    if definition.stable_id != f"ND{offset:04d}":
        raise ValueError("milestone definition stable identifiers must be contiguous and additive")
    if definition.name in _KNOWN or definition.stable_id in _SEEN_IDS:
        raise ValueError("milestone definitions repeat a historical reviewed identity")
    dependencies = definition.conceptual_dependencies
    if len(dependencies) != len(set(dependencies)) or not set(dependencies) <= set(_KNOWN):
        raise ValueError("milestone definitions have a repeated, unknown, or cyclic dependency")
    _KNOWN[definition.name] = definition
    _SEEN_IDS.add(definition.stable_id)

MILESTONE_CLOSURE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(
    {definition.name: definition for definition in MILESTONE_CLOSURE_DEFINITIONS}
)
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_KNOWN)
MILESTONE_CLOSURE_REGISTRIES: tuple[tuple[str, tuple[DefinitionSpec, ...]], ...] = (
    ("euclidean-logarithmic-bound", MILESTONE_CLOSURE_DEFINITIONS[:2]),
    ("binary-digit-extraction", MILESTONE_CLOSURE_DEFINITIONS[2:6]),
    ("primes-three-mod-four", MILESTONE_CLOSURE_DEFINITIONS[6:]),
)
if tuple(item for _, group in MILESTONE_CLOSURE_REGISTRIES for item in group) != (
    MILESTONE_CLOSURE_DEFINITIONS
):
    raise ValueError("milestone definition registry partition changed")


__all__ = (
    "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME",
    "MILESTONE_CLOSURE_DEFINITIONS",
    "MILESTONE_CLOSURE_DEFINITIONS_BY_NAME",
    "MILESTONE_CLOSURE_REGISTRIES",
)
