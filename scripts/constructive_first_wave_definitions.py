"""One conservative definition DAG for positive triples and actual descent.

The five historical Pythagorean explorer aliases keep their CF identifiers and
their byte-exact expansions.  Six new definitions distinguish positive
primitive triples, their Euclid witnesses, and the actual descent invariant.
These are syntax abbreviations, never new axioms or kernel predicates.
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

from constructive_breakthrough_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
)
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.library.defined_syntax import DefinitionSpec, _definition  # noqa: E402
from peano_lab.library.fermat_four_descent_candidate import (  # noqa: E402
    fermat_four_descent_witness,
    fermat_four_trivial_solution,
    primitive_four_counterexample,
)
from peano_lab.library.pythagorean_fermat_four_candidate import (  # noqa: E402
    fermat_four_counterexample,
    fermat_four_strict_descent,
    primitive_pythagorean,
    pythagorean_triple,
)
from peano_lab.library.pythagorean_inverse_candidate import (  # noqa: E402
    euclidean_parameter_witness,
    euclidean_parametrization,
    positive_primitive_pythagorean,
)
from peano_lab.library.pythagorean_primitive_candidate import opposite_parity  # noqa: E402


def _construct(
    *, identifier: str, name: str, parameters: tuple[str, ...], source: str,
    summary: str, dependencies: tuple[str, ...] = (),
) -> DefinitionSpec:
    if parameters:
        return _definition(
            stable_id=identifier, name=name, parameters=parameters,
            template_source=source, summary=summary,
            category="constructive_first_wave", priority="P2",
            conceptual_dependencies=dependencies,
        )
    # The existing CF0015 is a closed proposition, not a predicate with a
    # dummy argument.  Preserve that exact nullary signature without changing
    # the historical non-nullary definition factory or the ordinary parser.
    if (identifier, name) != ("CF0015", "FermatFourStrictDescent"):
        raise ValueError("only the exact historical descent alias is nullary")
    return DefinitionSpec(
        stable_id=identifier, name=name, parameters=(), template_source=source,
        template_formula=parse_formula_in_context(source, []), summary=summary,
        category="constructive_first_wave", priority="P2",
        conceptual_dependencies=dependencies,
    )


FIRST_WAVE_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(
        identifier="CF0011", name="Pythagorean", parameters=("x", "y", "z"),
        source=pythagorean_triple("x", "y", "z"),
        summary="The exact natural Pythagorean equation, with zero coordinates allowed.",
    ),
    _construct(
        identifier="CF0013", name="PrimitivePythagorean", parameters=("x", "y", "z"),
        source=primitive_pythagorean("x", "y", "z", tag="frontier"),
        summary="The historical Pythagorean equation with coprime legs; this predicate still permits the zero-leg triples.",
        dependencies=("Pythagorean", "Coprime"),
    ),
    _construct(
        identifier="CF0014", name="FermatFourCounterexample", parameters=("x", "y", "z"),
        source=fermat_four_counterexample("x", "y", "z", tag="frontier"),
        summary="Three nonzero natural coordinates satisfying the stronger square-hypotenuse counterexample equation x⁴+y⁴=z².",
    ),
    _construct(
        identifier="CF0015", name="FermatFourStrictDescent", parameters=(),
        source=fermat_four_strict_descent(tag="frontier"),
        summary="Every positive fourth-power counterexample has a positive counterexample with a strictly smaller natural hypotenuse.",
        dependencies=("FermatFourCounterexample", "Lt"),
    ),
    _construct(
        identifier="CF0016", name="OppositeParity", parameters=("m", "n"),
        source=opposite_parity("m", "n", tag="frontier"),
        summary="A witnessed choice between even/odd and odd/even parameter orientations.",
        dependencies=("Even", "Odd"),
    ),
    _construct(
        identifier="ND0069", name="PrimitiveTriple", parameters=("a", "b", "c"),
        source=positive_primitive_pythagorean("a", "b", "c", tag="firstwave"),
        summary="Exactly the blueprint's positive primitive ordered triple: all three coordinates are nonzero, the square equation holds, and the legs are coprime.",
        dependencies=("PrimitivePythagorean",),
    ),
    _construct(
        identifier="ND0070", name="EuclidParameters", parameters=("a", "b", "c", "m", "n"),
        source=euclidean_parameter_witness("a", "b", "c", "m", "n", tag="firstwave"),
        summary="Explicit m>n>0, coprime opposite-parity parameters, c=m²+n², the subtraction-free odd-leg equation m²=n²+a, and b=2mn.",
        dependencies=("Lt", "Coprime", "OppositeParity"),
    ),
    _construct(
        identifier="ND0071", name="PrimitiveFermatFourCounterexample", parameters=("x", "y", "z"),
        source=primitive_four_counterexample("x", "y", "z", tag="firstwave"),
        summary="A positive fourth-power counterexample whose two bases are coprime, as constructed by gcd normalization.",
        dependencies=("FermatFourCounterexample", "Coprime"),
    ),
    _construct(
        identifier="ND0072", name="SmallerFermatFourCounterexample", parameters=("x", "y", "z", "h"),
        source=fermat_four_descent_witness("x", "y", "z", "h", tag="firstwave"),
        summary="An actual positive fourth-power counterexample together with the explicit strict descent witness z<h.",
        dependencies=("FermatFourCounterexample", "Lt"),
    ),
    _construct(
        identifier="ND0073", name="TrivialFermatFourSolution", parameters=("x", "y", "z"),
        source=fermat_four_trivial_solution("x", "y", "z", tag="firstwave"),
        summary="Exactly the two zero-coordinate orientations of a natural Fermat-four solution: x=0 and y=z, or y=0 and x=z.",
    ),
    _construct(
        identifier="ND0074", name="EuclidParametrization", parameters=("a", "b", "c"),
        source=euclidean_parametrization("a", "b", "c", tag="firstwave"),
        summary="There exist m>n>0 with coprime opposite-parity parameters and c=m²+n², with either ordered leg orientation (m²−n²,2mn) or (2mn,m²−n²).",
        dependencies=("Lt", "Coprime", "OppositeParity"),
    ),
)


_KNOWN = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_SEEN_IDS = {definition.stable_id for definition in _KNOWN.values()}
if len(_KNOWN) != 120 or len(_SEEN_IDS) != len(_KNOWN):
    raise ValueError("the immutable Alpha-v25 definition registry changed")
_EXPECTED_IDS = ("CF0011", "CF0013", "CF0014", "CF0015", "CF0016") + tuple(
    f"ND{index:04d}" for index in range(69, 75)
)
if tuple(definition.stable_id for definition in FIRST_WAVE_DEFINITIONS) != _EXPECTED_IDS:
    raise ValueError("historical frontier IDs or additive first-wave IDs changed")
for definition in FIRST_WAVE_DEFINITIONS:
    if definition.name in _KNOWN or definition.stable_id in _SEEN_IDS:
        raise ValueError("first-wave definitions repeat a historical identity")
    dependencies = definition.conceptual_dependencies
    if len(dependencies) != len(set(dependencies)) or not set(dependencies) <= set(_KNOWN):
        raise ValueError("first-wave definitions contain repeated, unknown, or cyclic edges")
    _KNOWN[definition.name] = definition
    _SEEN_IDS.add(definition.stable_id)

FIRST_WAVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType({
    definition.name: definition for definition in FIRST_WAVE_DEFINITIONS
})
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_KNOWN)
FIRST_WAVE_REGISTRIES: tuple[tuple[str, tuple[DefinitionSpec, ...]], ...] = (
    ("pythagorean-fermat-four", FIRST_WAVE_DEFINITIONS),
)


__all__ = (
    "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME", "FIRST_WAVE_DEFINITIONS",
    "FIRST_WAVE_DEFINITIONS_BY_NAME", "FIRST_WAVE_REGISTRIES",
)
