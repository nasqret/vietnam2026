"""Additive hygienic first-order definitions for the Alpha-v24 research layer.

The immutable historical Quadratic Reciprocity, Bertrand, and Alpha-v20–v23
definition identities are reused by object identity.  Every new abbreviation
is the exact checked-candidate formula over unchanged Heyting arithmetic;
conceptual notation edges do not grant theorem-proof authority.
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

from constructive_milestone_closure_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as HISTORICAL_DEFINITIONS_BY_NAME,
)
from peano_lab.library.defined_syntax import DefinitionSpec, _definition  # noqa: E402
from peano_lab.library.generalized_crt_fold_candidate import (  # noqa: E402
    crt_canonical_prefix_solution,
    crt_pairwise_coprime_prefix,
    crt_positive_moduli_prefix,
    crt_prefix_lcm,
    crt_prefix_solution,
)
from peano_lab.library.matrix_determinant_minors_candidate import (  # noqa: E402
    matrix_minor_cell_relation,
    matrix_minor_prefix_relation,
    matrix_skip_index_relation,
    signed_matrix_minor_relation,
)
from peano_lab.library.polynomial_hensel_candidate import (  # noqa: E402
    horner_derivative_only_relation,
    horner_derivative_relation,
    horner_derivative_trace_relation,
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
        category="constructive_research_layer",
        priority="P2",
        conceptual_dependencies=dependencies,
    )


RESEARCH_LAYER_DEFINITIONS: tuple[DefinitionSpec, ...] = (
    _construct(
        identifier="ND0046",
        name="MatrixSkipIndex",
        parameters=("i", "r", "s"),
        source=matrix_skip_index_relation("i", "r", "s", tag="research"),
        summary="The unique order-preserving source coordinate that skips one genuinely deleted matrix row or column.",
        dependencies=("Lt", "Le"),
    ),
    _construct(
        identifier="ND0047",
        name="MatrixMinorCell",
        parameters=("b", "c", "w", "r", "d", "i", "j", "z"),
        source=matrix_minor_cell_relation(
            "b", "c", "w", "r", "d", "i", "j", "z", tag="research"
        ),
        summary="The exact beta-decoded source entry after independently skipping the removed row and column.",
        dependencies=("MatrixSkipIndex", "Beta"),
    ),
    _construct(
        identifier="ND0048",
        name="MatrixMinorPrefix",
        parameters=("b", "c", "w", "r", "d", "u", "v", "q", "l"),
        source=matrix_minor_prefix_relation(
            "b", "c", "w", "r", "d", "u", "v", "q", "l", tag="research"
        ),
        summary="One complete row-major beta code containing every genuine skipped-row/skipped-column matrix entry.",
        dependencies=("Lt", "MatrixMinorCell", "Beta"),
    ),
    _construct(
        identifier="ND0049",
        name="SignedMatrixMinor",
        parameters=(
            "pb", "pc", "nb", "nc", "w", "r", "d", "q", "up", "us", "un", "ut"
        ),
        source=signed_matrix_minor_relation(
            "pb", "pc", "nb", "nc", "w", "r", "d", "q", "up", "us", "un", "ut",
            tag="research",
        ),
        summary="Both complete independently beta-coded natural components of a genuine signed square cofactor minor.",
        dependencies=("MatrixMinorPrefix",),
    ),
    _construct(
        identifier="ND0050",
        name="HornerDerivativeTrace",
        parameters=("b", "c", "t", "l", "u", "v", "d", "e"),
        source=horner_derivative_trace_relation(
            "b", "c", "t", "l", "u", "v", "d", "e", tag="research"
        ),
        summary="Parallel beta-coded Horner value and derivative traces satisfying the exact formal differentiation recurrence.",
        dependencies=("Beta", "Horner"),
    ),
    _construct(
        identifier="ND0051",
        name="HornerDerivative",
        parameters=("b", "c", "t", "l", "n", "z"),
        source=horner_derivative_relation(
            "b", "c", "t", "l", "n", "z", tag="research"
        ),
        summary="The exact jointly witnessed natural Horner polynomial value and its formal derivative.",
        dependencies=("HornerDerivativeTrace", "Horner"),
    ),
    _construct(
        identifier="ND0052",
        name="HornerDerivativeOnly",
        parameters=("b", "c", "t", "l", "z"),
        source=horner_derivative_only_relation(
            "b", "c", "t", "l", "z", tag="research"
        ),
        summary="The exact natural formal derivative obtained by existentially packaging its actual Horner value.",
        dependencies=("HornerDerivative",),
    ),
    _construct(
        identifier="ND0053",
        name="CRTPositiveModuliPrefix",
        parameters=("b", "c", "l"),
        source=crt_positive_moduli_prefix("b", "c", "l", tag="research"),
        summary="A bounded beta-coded finite prefix consisting entirely of genuinely positive moduli.",
        dependencies=("Beta", "Lt"),
    ),
    _construct(
        identifier="ND0054",
        name="CRTPairwiseCoprimePrefix",
        parameters=("b", "c", "l"),
        source=crt_pairwise_coprime_prefix("b", "c", "l", tag="research"),
        summary="Exact pairwise coprimality of every pair of distinct positions in a beta-coded modulus prefix.",
        dependencies=("Beta", "Lt", "Coprime"),
    ),
    _construct(
        identifier="ND0055",
        name="CRTPrefixSolution",
        parameters=("r", "s", "b", "c", "l", "x"),
        source=crt_prefix_solution("r", "s", "b", "c", "l", "x", tag="research"),
        summary="One actual simultaneous solution to every beta-coded finite residue/modulus pair.",
        dependencies=("Beta", "Lt", "ModEq"),
    ),
    _construct(
        identifier="ND0056",
        name="CRTPrefixLCM",
        parameters=("b", "c", "l", "M"),
        source=crt_prefix_lcm("b", "c", "l", "M", tag="research"),
        summary="The exact beta-prefix least common multiple, specified by divisibility and its universal leastness property.",
        dependencies=("Beta", "Lt", "Dvd"),
    ),
    _construct(
        identifier="ND0057",
        name="CRTCanonicalPrefixSolution",
        parameters=("r", "s", "b", "c", "l", "x", "M"),
        source=crt_canonical_prefix_solution(
            "r", "s", "b", "c", "l", "x", "M", tag="research"
        ),
        summary="A genuine simultaneous finite CRT solution in the unique half-open range below its actual prefix LCM.",
        dependencies=("CRTPrefixLCM", "Lt", "CRTPrefixSolution"),
    ),
)


_KNOWN = dict(HISTORICAL_DEFINITIONS_BY_NAME)
_SEEN_IDS = {definition.stable_id for definition in _KNOWN.values()}
if len(_KNOWN) != 97 or len(_SEEN_IDS) != len(_KNOWN):
    raise ValueError("the immutable Alpha-v23 reviewed definition registry changed")
for offset, definition in enumerate(RESEARCH_LAYER_DEFINITIONS, start=46):
    if definition.stable_id != f"ND{offset:04d}":
        raise ValueError("research-layer definition identifiers must be contiguous and additive")
    if definition.name in _KNOWN or definition.stable_id in _SEEN_IDS:
        raise ValueError("research-layer definitions repeat an immutable historical identity")
    dependencies = definition.conceptual_dependencies
    if len(dependencies) != len(set(dependencies)) or not set(dependencies) <= set(_KNOWN):
        raise ValueError("research-layer definitions contain a repeated, unknown, or cyclic edge")
    _KNOWN[definition.name] = definition
    _SEEN_IDS.add(definition.stable_id)

RESEARCH_LAYER_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(
    {definition.name: definition for definition in RESEARCH_LAYER_DEFINITIONS}
)
ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME: Mapping[str, DefinitionSpec] = MappingProxyType(_KNOWN)
RESEARCH_LAYER_REGISTRIES: tuple[tuple[str, tuple[DefinitionSpec, ...]], ...] = (
    ("matrix-determinant-minors", RESEARCH_LAYER_DEFINITIONS[:4]),
    ("polynomial-hensel", RESEARCH_LAYER_DEFINITIONS[4:7]),
    ("generalized-crt-fold", RESEARCH_LAYER_DEFINITIONS[7:]),
)
if tuple(item for _, group in RESEARCH_LAYER_REGISTRIES for item in group) != (
    RESEARCH_LAYER_DEFINITIONS
):
    raise ValueError("research-layer definition registry partition changed")


__all__ = (
    "ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME",
    "RESEARCH_LAYER_DEFINITIONS",
    "RESEARCH_LAYER_DEFINITIONS_BY_NAME",
    "RESEARCH_LAYER_REGISTRIES",
)
