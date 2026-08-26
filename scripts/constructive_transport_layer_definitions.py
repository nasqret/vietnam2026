"""Immutable conservative definitions for the checked Alpha-v22 transport layer.

These are hygienic notation only.  Every expansion is obtained directly from
its reviewed original-kernel theorem module, parsed into unchanged first-order
Heyting arithmetic, and appended without changing any historical definition.
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

from constructive_advanced_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
)
from peano_lab.library.binary_length_candidate import (  # noqa: E402
    binary_digit_relation,
    binary_length_relation,
    binary_power_relation,
)
from peano_lab.library.binary_modular_execution_candidate import (  # noqa: E402
    binary_digit_prefix,
    binary_execution_power_invariant,
    binary_execution_trace,
    binary_modular_execution,
)
from peano_lab.library.defined_syntax import DefinitionSpec, _definition  # noqa: E402
from peano_lab.library.euclidean_gcd_transport_candidate import (  # noqa: E402
    euclidean_anchored_execution,
    euclidean_common_divisor,
    euclidean_state_at,
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
        category="constructive_transport_layer",
        priority="P2",
        conceptual_dependencies=dependencies,
    )


TRANSPORT_LAYER_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(
        identifier="ND0028",
        name="PowTwo",
        parameters=("e", "p"),
        source=binary_power_relation("e", "p", tag="transport"),
        summary="The exact existing constructive exponentiation relation Pow(2,e,p).",
        dependencies=("Pow",),
    ),
    _construct(
        identifier="ND0029",
        name="BinaryDigit",
        parameters=("n", "h", "b"),
        source=binary_digit_relation("n", "h", "b", tag="transport"),
        summary="An exact binary digit split n=2h+b, with b explicitly zero or one.",
        dependencies=("BinaryExponentSplit",),
    ),
    _construct(
        identifier="ND0030",
        name="BitLen",
        parameters=("n", "ell"),
        source=binary_length_relation("n", "ell", tag="transport"),
        summary="The unique binary length, with BitLen(0,1) and positive bounds 2^(ell-1)≤n<2^ell.",
        dependencies=("PowTwo", "Le", "Lt"),
    ),
    _construct(
        identifier="ND0031",
        name="EuclideanCommonDivisor",
        parameters=("d", "a", "b"),
        source=euclidean_common_divisor("d", "a", "b", tag="transport"),
        summary="Two actual natural divisibility witnesses for a common Euclidean divisor.",
        dependencies=("Dvd",),
    ),
    _construct(
        identifier="ND0032",
        name="EuclideanStateAt",
        parameters=("h", "s", "i", "a", "b", "q"),
        source=euclidean_state_at("h", "s", "i", "a", "b", "q", tag="transport"),
        summary="The unique doubled-Cantor-packed beta state of an actual Euclidean history.",
        dependencies=("Beta",),
    ),
    _construct(
        identifier="ND0033",
        name="EuclideanAnchoredExecution",
        parameters=("a", "b", "g", "k"),
        source=euclidean_anchored_execution("a", "b", "g", "k", tag="transport"),
        summary="A complete beta-coded Euclidean trace whose final zero-remainder state is exactly its independently proved gcd output.",
        dependencies=("ContinuedFractionTrace", "EuclideanStateAt", "IsGCD"),
    ),
    _construct(
        identifier="ND0034",
        name="BinaryDigitPrefix",
        parameters=("d", "s", "n"),
        source=binary_digit_prefix("d", "s", "n", tag="transport"),
        summary="Every genuinely beta-decoded entry of a bounded finite prefix is zero or one.",
        dependencies=("Beta", "Lt"),
    ),
    _construct(
        identifier="ND0035",
        name="BinaryExecutionTrace",
        parameters=("d", "s", "a", "m", "n", "h", "t"),
        source=binary_execution_trace("d", "s", "a", "m", "n", "h", "t", tag="transport"),
        summary="A complete beta-coded accumulator history starting at one and preserving the checked square-and-multiply transition at every digit.",
        dependencies=("Beta", "Lt", "BinaryModularStep"),
    ),
    _construct(
        identifier="ND0036",
        name="BinaryModularExecution",
        parameters=("d", "s", "a", "m", "n", "r"),
        source=binary_modular_execution("d", "s", "a", "m", "n", "r", tag="transport"),
        summary="An actual beta-coded repeated-squaring trace together with its decoded terminal accumulator.",
        dependencies=("BinaryExecutionTrace", "Beta"),
    ),
    _construct(
        identifier="ND0037",
        name="BinaryExecutionPowerInvariant",
        parameters=("d", "s", "a", "m", "n", "r"),
        source=binary_execution_power_invariant("d", "s", "a", "m", "n", "r", tag="transport"),
        summary="The beta-coded digit prefix evaluated by base-two Horner together with its unique canonical modular power.",
        dependencies=("Horner", "BinaryModularPower"),
    ),
)


_KNOWN = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_SEEN_IDS = {item.stable_id for item in _KNOWN.values()}
if len(_SEEN_IDS) != len(_KNOWN):
    raise ValueError("the immutable reviewed definition registry repeats an identity")
for offset, definition in enumerate(TRANSPORT_LAYER_DEFINITIONS, start=28):
    if definition.stable_id != f"ND{offset:04d}":
        raise ValueError("transport definition stable identifiers must be contiguous and additive")
    if definition.name in _KNOWN or definition.stable_id in _SEEN_IDS:
        raise ValueError("transport definitions repeat a historical reviewed identity")
    dependencies = definition.conceptual_dependencies
    if len(dependencies) != len(set(dependencies)) or not set(dependencies) <= set(_KNOWN):
        raise ValueError("transport definitions have a repeated, unknown, or cyclic dependency")
    _KNOWN[definition.name] = definition
    _SEEN_IDS.add(definition.stable_id)

TRANSPORT_LAYER_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(
    {definition.name: definition for definition in TRANSPORT_LAYER_DEFINITIONS}
)
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_KNOWN)
TRANSPORT_LAYER_REGISTRIES: tuple[tuple[str, tuple[DefinitionSpec, ...]], ...] = (
    ("binary-length", TRANSPORT_LAYER_DEFINITIONS[:3]),
    ("euclidean-gcd-transport", TRANSPORT_LAYER_DEFINITIONS[3:6]),
    ("binary-modular-execution", TRANSPORT_LAYER_DEFINITIONS[6:]),
)
if tuple(item for _, group in TRANSPORT_LAYER_REGISTRIES for item in group) != (
    TRANSPORT_LAYER_DEFINITIONS
):
    raise ValueError("transport definition registry partition changed")


__all__ = (
    "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME",
    "TRANSPORT_LAYER_DEFINITIONS",
    "TRANSPORT_LAYER_DEFINITIONS_BY_NAME",
    "TRANSPORT_LAYER_REGISTRIES",
)
