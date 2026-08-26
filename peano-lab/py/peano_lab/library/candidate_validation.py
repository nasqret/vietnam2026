"""Fast, non-admitting validation for isolated theorem-candidate scripts.

Candidate authoring has two logically separate questions:

1. does the tactic script prove its statement when every declared dependency
   is introduced as an ordinary hypothesis; and
2. can all dependencies be closed, packaged, and checked within the admission
   resource limits?

This module answers only the first question.  It still calls the independent
kernel on the dependency-curried goal, so tactic bugs cannot create a false
positive.  It deliberately does not replay or trust any dependency theorem
and therefore must never be cited as an admission receipt.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

from ..engine.state import proof_identity_metrics, proof_metrics, start
from ..engine.tactics import apply_tactic, checked_final
from ..kernel.formulas import Imp
from .theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


class CandidateBodyError(ValueError):
    """A candidate body or its declared dependency surface is invalid."""


@dataclass(frozen=True, slots=True)
class CandidateBodyReceipt:
    """Kernel-checked metrics for one dependency-curried candidate body."""

    name: str
    dependency_count: int
    command_count: int
    proof_nodes: int
    proof_depth: int
    proof_objects: int
    proof_edges: int
    reused_objects: int


def _candidate_table(specs: Iterable[TheoremSpec]) -> tuple[tuple[TheoremSpec, ...], dict[str, TheoremSpec]]:
    ordered = tuple(specs)
    table: dict[str, TheoremSpec] = {}
    for spec in ordered:
        if type(spec) is not TheoremSpec:
            raise CandidateBodyError("candidate entries must be exact TheoremSpec values")
        if not spec.name or spec.name != spec.name.strip() or any(
            character.isspace() for character in spec.name
        ):
            raise CandidateBodyError("candidate names must be non-empty single words")
        if spec.name in table:
            raise CandidateBodyError(f"duplicate candidate theorem {spec.name!r}")
        if not spec.script:
            raise CandidateBodyError(f"candidate {spec.name!r} has no tactic script")
        _closed_formula(spec.statement)
        table[spec.name] = spec
    return ordered, table


def replay_candidate_bodies(
    specs: Iterable[TheoremSpec],
    *,
    core: Mapping[str, TheoremSpec] | None = None,
) -> tuple[CandidateBodyReceipt, ...]:
    """Kernel-check candidate scripts with dependencies left as hypotheses.

    Local dependencies may occur anywhere in ``specs`` because this pass does
    not close them.  Graph ordering, recursive dependency replay, Cut-spine
    mutation tests, and resource admission remain separate mandatory gates.
    """

    ordered, local = _candidate_table(specs)
    public = dict(_specs_by_name() if core is None else core)
    receipts: list[CandidateBodyReceipt] = []

    for spec in ordered:
        formula = _closed_formula(spec.statement)
        target = formula
        dependency_specs: list[TheoremSpec] = []
        for dependency in spec.dependencies:
            dependency_spec = local.get(dependency) or public.get(dependency)
            if dependency_spec is None:
                raise CandidateBodyError(
                    f"candidate {spec.name!r} has unknown dependency {dependency!r}"
                )
            dependency_specs.append(dependency_spec)
        for dependency_spec in reversed(dependency_specs):
            target = Imp(_closed_formula(dependency_spec.statement), target)

        state = start(target)
        for dependency in spec.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for index, command in enumerate(spec.script):
            try:
                tactic, args = _primitive(command)
                state = apply_tactic(state, tactic, args)
            except Exception as exc:
                raise CandidateBodyError(
                    f"candidate {spec.name!r} failed at command {index}: {command!r}: {exc}"
                ) from exc

        try:
            certificate = checked_final(state, target)
        except Exception as exc:
            raise CandidateBodyError(
                f"candidate {spec.name!r} produced a rejected dependency-curried certificate: {exc}"
            ) from exc
        nodes, depth = proof_metrics(certificate)
        objects, edges, reused = proof_identity_metrics(certificate)
        receipts.append(
            CandidateBodyReceipt(
                name=spec.name,
                dependency_count=len(spec.dependencies),
                command_count=len(spec.script),
                proof_nodes=nodes,
                proof_depth=depth,
                proof_objects=objects,
                proof_edges=edges,
                reused_objects=reused,
            )
        )

    return tuple(receipts)


__all__ = [
    "CandidateBodyError",
    "CandidateBodyReceipt",
    "replay_candidate_bodies",
]
