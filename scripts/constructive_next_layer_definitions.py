"""Canonical conservative, hygienic definitions shared by Alpha-v20 campaigns.

These immutable parser-only aliases are *not* new predicates, axioms, kernel
constructors, or release-admission mechanisms. Each exact source is expanded
and parsed into the unchanged first-order Heyting-arithmetic formula syntax at
construction. The atlas registry and all four next-layer reading explorers
consume these same ``DefinitionSpec`` objects, stable identities, and formulas.
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

from peano_lab.library.bertrand_defined_edition import (  # noqa: E402
    ALL_BERTRAND_DEFINITIONS,
)
from peano_lab.library.bertrand_prime_campaign_candidate import (  # noqa: E402
    bertrand_chain,
    bertrand_window,
    power_valuation_one,
)
from peano_lab.library.continued_fraction_candidate import (  # noqa: E402
    continued_fraction,
    continued_fraction_trace,
)
from peano_lab.library.defined_syntax import DefinitionSpec, _definition  # noqa: E402
from peano_lab.library.ha_pair_cell_seed_candidate import cell  # noqa: E402
from peano_lab.library.matrix_dot_product_candidate import (  # noqa: E402
    dot_product_relation,
    matrix_cell_relation,
)
from peano_lab.library.polynomial_horner_candidate import horner_relation  # noqa: E402


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
        category="constructive_next_layer",
        priority="P2",
        conceptual_dependencies=dependencies,
    )


_EXISTING = {
    definition.name: definition for definition in ALL_BERTRAND_DEFINITIONS
}
if len(_EXISTING) != len(ALL_BERTRAND_DEFINITIONS):
    raise ValueError("the reviewed base definition registry repeats a name")

NEXT_LAYER_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(
        identifier="ND0001",
        name="Beta",
        parameters=("b", "c", "i", "x"),
        source=_EXISTING["BetaAt"].template_source,
        summary="Exact hygienic Gödel-beta extraction; a signature-identical alias of checked BetaAt.",
    ),
    _construct(
        identifier="ND0002",
        name="Horner",
        parameters=("b", "c", "x", "ell", "z"),
        source=horner_relation("b", "c", "x", "ell", "z", tag="explorer"),
        summary="A complete beta-coded natural-polynomial Horner trace with an explicitly witnessed terminal value.",
        dependencies=("Beta", "Lt"),
    ),
    _construct(
        identifier="ND0003",
        name="MatrixAt",
        parameters=("b", "c", "w", "i", "j", "z"),
        source=matrix_cell_relation("b", "c", "w", "i", "j", "z", tag="explorer"),
        summary="The exact natural matrix entry stored at flattened beta index i*w+j.",
        dependencies=("Beta",),
    ),
    _construct(
        identifier="ND0004",
        name="DotProduct",
        parameters=("b", "c", "d", "e", "ell", "z"),
        source=dot_product_relation("b", "c", "d", "e", "ell", "z", tag="explorer"),
        summary="The witnessed sum of the pointwise products of two beta-coded natural vectors.",
        dependencies=("Beta", "Lt", "Sum"),
    ),
    _construct(
        identifier="ND0005",
        name="SignedDet2",
        parameters=("a", "b", "c", "d", "p", "n"),
        source="p = a * d /\\ n = b * c",
        summary="The exact positive and negative natural components p=ad and n=bc of a signed 2×2 determinant.",
    ),
    _construct(
        identifier="ND0006",
        name="BertrandWindow",
        parameters=("n", "p"),
        source=bertrand_window("n", "p", tag="explorer"),
        summary="Prime(p) together with the exact strict inequalities n<p<2*n.",
        dependencies=("Prime", "Lt"),
    ),
    _construct(
        identifier="ND0007",
        name="PowerValuationOne",
        parameters=("p", "n"),
        source=power_valuation_one("p", "n", tag="explorer"),
        summary="The exact existing bounded prime-power valuation relation at literal exponent one.",
        dependencies=("PowerValuation",),
    ),
    _construct(
        identifier="ND0008",
        name="BertrandChain",
        parameters=("b", "c", "n", "k"),
        source=bertrand_chain("b", "c", "n", "k", tag="explorer"),
        summary="A beta-coded length-k strict prime chain starting at n, without choice or a new sequence primitive.",
        dependencies=("Beta", "Lt", "BertrandWindow"),
    ),
    _construct(
        identifier="ND0009",
        name="ListCell",
        parameters=("s", "q", "t"),
        source=cell("s", "q", "t"),
        summary="The exact tagged natural-number list cell containing quotient q and tail t.",
    ),
    _construct(
        identifier="ND0010",
        name="ContinuedFractionTrace",
        parameters=("a", "b", "s", "u", "v", "ell"),
        source=continued_fraction_trace("a", "b", "s", "u", "v", "ell", tag="explorer"),
        summary="A finite beta-coded reverse Euclidean history whose quotient list has forward continued-fraction order.",
        dependencies=("Beta", "Lt", "ListCell"),
    ),
    _construct(
        identifier="ND0011",
        name="ContinuedFraction",
        parameters=("a", "b", "s"),
        source=continued_fraction("a", "b", "s", tag="explorer"),
        summary="Positive natural inputs together with a witnessed nonempty complete simple continued fraction.",
        dependencies=("ContinuedFractionTrace",),
    ),
)

_BY_NAME = {definition.name: definition for definition in NEXT_LAYER_DEFINITIONS}
if (
    len(_BY_NAME) != len(NEXT_LAYER_DEFINITIONS)
    or len({definition.stable_id for definition in NEXT_LAYER_DEFINITIONS})
    != len(NEXT_LAYER_DEFINITIONS)
):
    raise ValueError("next-layer definitions repeat a reviewed stable identity")
if (
    _BY_NAME["Beta"].parameters != _EXISTING["BetaAt"].parameters
    or _BY_NAME["Beta"].template_formula != _EXISTING["BetaAt"].template_formula
):
    raise ValueError("canonical Beta alias is not identical to reviewed BetaAt")

NEXT_LAYER_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(
    _BY_NAME
)
NEXT_LAYER_REGISTRIES: tuple[tuple[str, tuple[DefinitionSpec, ...]], ...] = (
    (
        "polynomial-horner",
        (_BY_NAME["Beta"], _BY_NAME["Horner"]),
    ),
    (
        "matrix-dot-product",
        (_BY_NAME["MatrixAt"], _BY_NAME["DotProduct"], _BY_NAME["SignedDet2"]),
    ),
    (
        "bertrand-prime-chains",
        (
            _BY_NAME["BertrandWindow"],
            _BY_NAME["PowerValuationOne"],
            _BY_NAME["BertrandChain"],
        ),
    ),
    (
        "continued-fractions",
        (
            _BY_NAME["ListCell"],
            _BY_NAME["ContinuedFractionTrace"],
            _BY_NAME["ContinuedFraction"],
        ),
    ),
)


__all__ = (
    "NEXT_LAYER_DEFINITIONS",
    "NEXT_LAYER_DEFINITIONS_BY_NAME",
    "NEXT_LAYER_REGISTRIES",
)
