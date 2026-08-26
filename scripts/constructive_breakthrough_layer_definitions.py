"""Additive hygienic definitions for the Alpha-v25 constructive breakthrough layer.

Historical reviewed objects retain their immutable identities.  New notation
expands to the exact unchanged first-order formulas used by independently
checked candidate bodies; conceptual definition edges are never proof edges.
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

from constructive_research_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
)
from peano_lab.library.defined_syntax import DefinitionSpec, _definition  # noqa: E402
from peano_lab.library.generalized_crt_compatibility_candidate import (  # noqa: E402
    crt_merge_compatible_prefix,
    crt_pairwise_compatible_prefix,
)
from peano_lab.library.matrix_cofactor_expansion_candidate import (  # noqa: E402
    matrix_minor_four_code_relation,
    signed_alternating_cofactor_fold_relation,
    signed_alternating_cofactor_term_relation,
    signed_alternating_product_prefix_relation,
    signed_cofactor_minor_prefix_relation,
    signed_first_row_cofactor_fold_relation,
    signed_matrix_minor_record_relation,
)
from peano_lab.library.polynomial_taylor_hensel_candidate import (  # noqa: E402
    hensel_correction_relation,
    horner_taylor_remainder_relation,
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
        category="constructive_breakthrough_layer",
        priority="P2",
        conceptual_dependencies=dependencies,
    )


BREAKTHROUGH_LAYER_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(
        identifier="ND0058",
        name="MatrixMinorFourCode",
        parameters=("z", "up", "us", "un", "ut"),
        source=matrix_minor_four_code_relation(
            "z", "up", "us", "un", "ut", tag="breakthrough"
        ),
        summary="One canonical injective doubled-Cantor code for all four signed-minor beta-code parameters.",
    ),
    _construct(
        identifier="ND0059",
        name="SignedMinorRecord",
        parameters=("pb", "pc", "nb", "nc", "q", "j", "z"),
        source=signed_matrix_minor_record_relation(
            "pb", "pc", "nb", "nc", "q", "j", "z", tag="breakthrough"
        ),
        summary="An exactly decoded record containing both beta-coded components of the genuine deleted-row/deleted-column signed minor.",
        dependencies=("MatrixMinorFourCode", "SignedMatrixMinor"),
    ),
    _construct(
        identifier="ND0060",
        name="SignedCofactorMinorPrefix",
        parameters=("pb", "pc", "nb", "nc", "q", "b", "c", "l"),
        source=signed_cofactor_minor_prefix_relation(
            "pb", "pc", "nb", "nc", "q", "b", "c", "l", tag="breakthrough"
        ),
        summary="A beta-coded prefix whose every bounded entry is an actual complete signed first-row cofactor minor.",
        dependencies=("Beta", "Lt", "SignedMinorRecord"),
    ),
    _construct(
        identifier="ND0061",
        name="SignedAlternatingCofactorTerm",
        parameters=("ap", "an", "bp", "bn", "i", "p", "n"),
        source=signed_alternating_cofactor_term_relation(
            "ap", "an", "bp", "bn", "i", "p", "n", tag="breakthrough"
        ),
        summary="The exact positive/negative natural-pair product with signs exchanged precisely at odd cofactor positions.",
        dependencies=("Even", "Odd"),
    ),
    _construct(
        identifier="ND0062",
        name="SignedAlternatingProductPrefix",
        parameters=(
            "ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "ub", "uc", "vb", "vc", "l"
        ),
        source=signed_alternating_product_prefix_relation(
            "ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "ub", "uc", "vb", "vc", "l",
            tag="breakthrough",
        ),
        summary="Complete beta-coded positive and negative streams of every exact signed parity-adjusted row/cofactor product.",
        dependencies=("Beta", "Lt", "SignedAlternatingCofactorTerm"),
    ),
    _construct(
        identifier="ND0063",
        name="SignedAlternatingCofactorFold",
        parameters=("ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "l", "p", "n"),
        source=signed_alternating_cofactor_fold_relation(
            "ab", "ac", "db", "dc", "eb", "ec", "fb", "fc", "l", "p", "n",
            tag="breakthrough",
        ),
        summary="The two uniquely determined subtraction-free finite sums of an arbitrary signed alternating Laplace fold.",
        dependencies=("SignedAlternatingProductPrefix", "Sum"),
    ),
    _construct(
        identifier="ND0064",
        name="SignedFirstRowCofactorFold",
        parameters=("pb", "pc", "nb", "nc", "q", "eb", "ec", "fb", "fc", "p", "n"),
        source=signed_first_row_cofactor_fold_relation(
            "pb", "pc", "nb", "nc", "q", "eb", "ec", "fb", "fc", "p", "n",
            tag="breakthrough",
        ),
        summary="The exact alternating fold of the genuinely beta-decoded first matrix row against supplied signed cofactor values.",
        dependencies=("MatrixAffineSlice", "SignedAlternatingCofactorFold"),
    ),
    _construct(
        identifier="ND0065",
        name="HornerTaylorRemainder",
        parameters=("b", "c", "x", "h", "l", "n", "d", "y", "q"),
        source=horner_taylor_remainder_relation(
            "b", "c", "x", "h", "l", "n", "d", "y", "q", tag="breakthrough"
        ),
        summary="An actual arbitrary-finite-polynomial Taylor witness satisfying the exact quadratic remainder identity.",
        dependencies=("HornerDerivative", "Horner"),
    ),
    _construct(
        identifier="ND0066",
        name="HenselCorrection",
        parameters=("d", "p", "q", "t"),
        source=hensel_correction_relation("d", "p", "q", "t", tag="breakthrough"),
        summary="The bounded modular derivative-inverse correction digit used by the genuine constructive one-step Hensel lift.",
        dependencies=("Lt", "ModEq"),
    ),
    _construct(
        identifier="ND0067",
        name="CRTPairwiseCompatiblePrefix",
        parameters=("r", "s", "b", "c", "l"),
        source=crt_pairwise_compatible_prefix(
            "r", "s", "b", "c", "l", tag="breakthrough"
        ),
        summary="Every pair of finite beta-coded residue/modulus entries agrees modulo its genuinely witnessed greatest common divisor.",
        dependencies=("Beta", "Lt", "IsGCD", "ModEq"),
    ),
    _construct(
        identifier="ND0068",
        name="CRTMergeCompatiblePrefix",
        parameters=("r", "s", "b", "c", "l"),
        source=crt_merge_compatible_prefix(
            "r", "s", "b", "c", "l", tag="breakthrough"
        ),
        summary="The exact successive-LCM/gcd compatibility invariant sufficient to merge every actual noncoprime finite CRT constraint.",
        dependencies=("Lt", "Beta", "CRTPrefixLCM", "CRTPrefixSolution", "IsGCD", "ModEq"),
    ),
)


_KNOWN = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_SEEN_IDS = {definition.stable_id for definition in _KNOWN.values()}
if len(_KNOWN) != 109 or len(_SEEN_IDS) != len(_KNOWN):
    raise ValueError("the immutable Alpha-v24 reviewed definition registry changed")
for offset, definition in enumerate(BREAKTHROUGH_LAYER_DEFINITIONS, start=58):
    if definition.stable_id != f"ND{offset:04d}":
        raise ValueError("breakthrough-layer definition identifiers must remain contiguous")
    if definition.name in _KNOWN or definition.stable_id in _SEEN_IDS:
        raise ValueError("breakthrough-layer definitions repeat an immutable historical identity")
    dependencies = definition.conceptual_dependencies
    if len(dependencies) != len(set(dependencies)) or not set(dependencies) <= set(_KNOWN):
        raise ValueError("breakthrough-layer definitions contain repeated, unknown, or cyclic edges")
    _KNOWN[definition.name] = definition
    _SEEN_IDS.add(definition.stable_id)

BREAKTHROUGH_LAYER_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(
    {definition.name: definition for definition in BREAKTHROUGH_LAYER_DEFINITIONS}
)
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_KNOWN)
BREAKTHROUGH_LAYER_REGISTRIES: tuple[tuple[str, tuple[DefinitionSpec, ...]], ...] = (
    ("matrix-cofactor-expansion", BREAKTHROUGH_LAYER_DEFINITIONS[:7]),
    ("polynomial-taylor-hensel", BREAKTHROUGH_LAYER_DEFINITIONS[7:9]),
    ("generalized-crt-compatibility", BREAKTHROUGH_LAYER_DEFINITIONS[9:]),
)
if tuple(item for _, group in BREAKTHROUGH_LAYER_REGISTRIES for item in group) != (
    BREAKTHROUGH_LAYER_DEFINITIONS
):
    raise ValueError("breakthrough-layer definition registry partition changed")


__all__ = (
    "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME",
    "BREAKTHROUGH_LAYER_DEFINITIONS",
    "BREAKTHROUGH_LAYER_DEFINITIONS_BY_NAME",
    "BREAKTHROUGH_LAYER_REGISTRIES",
)
