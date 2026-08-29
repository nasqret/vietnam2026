"""Three conservative graphs for actual finite signed Dirichlet inverses.

All 369 inherited definition objects remain unchanged. The new graphs name
canonical signed units, an actual lookup at one, and witnessed two-sided
convolution with a delta table. The equivalence between those notions is a
theorem, never a definition premise or an admission mechanism.
"""

from collections.abc import Mapping
from types import MappingProxyType

from constructive_bottom_layer_definitions import _contextual
from constructive_dirichlet_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
)
from peano_lab.library import dirichlet_inverse_candidate as inversion
from peano_lab.library import dirichlet_signed_unit_candidate as signed_units
from peano_lab.library.defined_syntax import DefinitionSpec, _definition


def _construct(identifier, name, parameters, builder, summary, dependencies):
    return _definition(
        stable_id=f"ND{identifier:04d}", name=name, parameters=parameters,
        template_source=_contextual(builder)(*parameters, tag="dirichlet_inverse"),
        summary=summary, category="constructive_dirichlet_inverse", priority="P2",
        conceptual_dependencies=dependencies,
    )


DIRICHLET_INVERSE_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(
        313, "SignedUnit", ("u",), signed_units.dirichlet_signed_unit_relation,
        "Exactly the canonical signed codes 2 (+1) and 1 (-1). Its equivalence with an actual signed multiplicative inverse and the affine-equation solver are separately proved, not assumed by this two-case graph.",
        (),
    ),
    _construct(
        314, "DirichletUnitAtOne", ("F",), inversion.dirichlet_unit_at_one_relation,
        "An actual lookup F(1) has canonical signed code 2 or 1. This direct disjunction contains ArithAt, not a SignedUnit or inverse subformula. Table validity, the finite window bound, and the inverse criterion are separate hypotheses or theorems.",
        ("ArithAt",),
    ),
    _construct(
        315, "DirichletInverse", ("N", "F", "G"), inversion.dirichlet_inverse_relation,
        "Witness a real Kronecker delta table E and both actual convolution tables F*G=E and G*F=E on 0<n<=N. Their graphs include actual table validity; values at zero remain unrestricted. The unit-at-one criterion is not a definition premise, and its necessity requires N>0; zero-window inverse identities are separately proved for all actual input tables.",
        ("KroneckerDeltaTable", "DirichletTable"),
    ),
)


_known = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_identifiers = {item.stable_id for item in _known.values()}
if len(_known) != 369 or len(_identifiers) != 369:
    raise ValueError("the frozen 369-definition registry changed")
if tuple(item.stable_id for item in DIRICHLET_INVERSE_DEFINITIONS) != (
    "ND0313", "ND0314", "ND0315",
):
    raise ValueError("Dirichlet-inverse definition identifier order changed")
for item in DIRICHLET_INVERSE_DEFINITIONS:
    if item.name in _known or item.stable_id in _identifiers:
        raise ValueError("Dirichlet-inverse notation shadows an inherited identity")
    if (len(item.conceptual_dependencies) != len(set(item.conceptual_dependencies))
            or not set(item.conceptual_dependencies) <= _known.keys()):
        raise ValueError("repeated, forward or missing Dirichlet-inverse definition dependency")
    _known[item.name] = item
    _identifiers.add(item.stable_id)

ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_known)
DIRICHLET_INVERSE_REGISTRIES = (
    ("dirichlet-signed-units", DIRICHLET_INVERSE_DEFINITIONS[:1]),
    ("dirichlet-triangular", ()),
    ("dirichlet-inverses", DIRICHLET_INVERSE_DEFINITIONS[1:]),
)


def definition_closure(names: tuple[str, ...]) -> tuple[DefinitionSpec, ...]:
    """Return only actual transitive expansion prerequisites in stable order."""
    if type(names) is not tuple or any(type(name) is not str or not name for name in names):
        raise ValueError("definition names must be an exact tuple of nonempty text")
    ordered, visited, active = [], set(), set()

    def visit(name):
        if name in visited:
            return
        if name in active or name not in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME:
            raise ValueError("unknown or cyclic Dirichlet-inverse notation: " + name)
        active.add(name)
        item = ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name]
        for dependency in item.conceptual_dependencies:
            visit(dependency)
        active.remove(name)
        visited.add(name)
        ordered.append(item)

    for name in names:
        visit(name)
    return tuple(ordered)


__all__ = (
    "DIRICHLET_INVERSE_DEFINITIONS", "DIRICHLET_INVERSE_REGISTRIES",
    "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME", "definition_closure",
)
