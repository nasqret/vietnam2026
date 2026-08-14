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

from ..engine.proof_reduction import ProofReductionError, compile_local_cuts
from ..engine.state import final_certificate, proof_resource_metrics, start
from ..engine.tactics import (
    InvalidProof,
    TacticError,
    TacticLimit,
    apply_tactic,
    checked_final,
    enforce_live_proof_bounds,
)
from ..kernel.formulas import Formula, Imp
from ..kernel.proofs import Proof
from .theorems import (
    TheoremSpec,
    _closed_formula,
    _primitive,
    _specs_by_name,
)


class CandidateBodyError(ValueError):
    """A candidate body or its declared dependency surface is invalid."""

    def __init__(
        self,
        message: str,
        *,
        phase: str = "validation",
        kind: str = "internal",
        command_index: int | None = None,
        command: str | None = None,
    ) -> None:
        super().__init__(message)
        self.phase = phase
        self.kind = kind
        self.command_index = command_index
        self.command = command


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


@dataclass(frozen=True, slots=True)
class CandidateBodyCompilation:
    """One dependency-curried proof checked by the independent kernel.

    This carrier exposes the ordinary kernel objects needed by untrusted
    artifact compilers.  It does not close, replay, or authorize any named
    dependency, and therefore remains non-admitting evidence.
    """

    target: Formula
    certificate: Proof
    receipt: CandidateBodyReceipt


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


def _compile_candidate_body(
    spec: TheoremSpec,
    *,
    local: Mapping[str, TheoremSpec],
    public: Mapping[str, TheoremSpec],
) -> CandidateBodyCompilation:
    if len(set(spec.dependencies)) != len(spec.dependencies):
        raise CandidateBodyError(
            f"candidate {spec.name!r} has a duplicate dependency"
        )
    if spec.name in spec.dependencies:
        raise CandidateBodyError(
            f"candidate {spec.name!r} cannot depend on itself"
        )
    formula = _closed_formula(spec.statement)
    target = formula
    dependency_specs: list[TheoremSpec] = []
    for dependency in spec.dependencies:
        if dependency in local:
            dependency_spec = local[dependency]
        elif dependency in public:
            dependency_spec = public[dependency]
        else:
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
        except TacticLimit as exc:
            raise CandidateBodyError(
                f"candidate {spec.name!r} reached a resource limit at command "
                f"{index}: {command!r}: {exc}",
                phase="command",
                kind="resource-limit",
                command_index=index,
                command=command,
            ) from exc
        except TacticError as exc:
            raise CandidateBodyError(
                f"candidate {spec.name!r} failed at command {index}: "
                f"{command!r}: {exc}",
                phase="command",
                kind="exact-recipe-rejection",
                command_index=index,
                command=command,
            ) from exc
        except Exception as exc:
            raise CandidateBodyError(
                f"candidate {spec.name!r} failed internally at command {index}: "
                f"{command!r}: {exc}",
                phase="command",
                kind="internal",
                command_index=index,
                command=command,
            ) from exc

    # ``checked_final`` intentionally translates the live-certificate
    # ``TacticLimit`` into user-facing ``InvalidProof``.  That is the right UI
    # boundary, but an artifact compiler must distinguish resource exhaustion
    # (unknown) from an ordinary incomplete/rejected recipe.  This exact
    # preflight uses the same immutable proof and the same cut compiler/bound
    # check before asking the normal checked-finalization path to run.
    if state.goals:
        raise CandidateBodyError(
            f"candidate {spec.name!r} produced an incomplete dependency-curried proof",
            phase="finalization",
            kind="exact-recipe-rejection",
        )
    try:
        preview = final_certificate(state)
    except RecursionError as exc:
        raise CandidateBodyError(
            f"candidate {spec.name!r} exhausted resources during finalization",
            phase="finalization",
            kind="resource-limit",
        ) from exc
    if preview is None:
        raise CandidateBodyError(
            f"candidate {spec.name!r} left a hole or metavariable during finalization",
            phase="finalization",
            kind="exact-recipe-rejection",
        )
    if state.target != target:
        raise CandidateBodyError(
            f"candidate {spec.name!r} changed the dependency-curried target",
            phase="finalization",
            kind="internal",
        )
    try:
        preview = compile_local_cuts(preview)
    except ProofReductionError as exc:
        raise CandidateBodyError(
            f"candidate {spec.name!r} has invalid local-reasoning cuts: {exc}",
            phase="finalization",
            kind="exact-recipe-rejection",
        ) from exc
    try:
        enforce_live_proof_bounds(preview)
    except TacticLimit as exc:
        raise CandidateBodyError(
            f"candidate {spec.name!r} exceeded the live proof resource policy",
            phase="finalization",
            kind="resource-limit",
        ) from exc
    except Exception as exc:
        raise CandidateBodyError(
            f"candidate {spec.name!r} failed internally during bound checking",
            phase="finalization",
            kind="internal",
        ) from exc
    try:
        certificate = checked_final(state, target)
    except InvalidProof as exc:
        raise CandidateBodyError(
            f"candidate {spec.name!r} produced a rejected dependency-curried "
            f"certificate: {exc}",
            phase="finalization",
            kind="exact-recipe-rejection",
        ) from exc
    except Exception as exc:
        raise CandidateBodyError(
            f"candidate {spec.name!r} failed internally during finalization",
            phase="finalization",
            kind="internal",
        ) from exc
    nodes, depth, objects, edges, reused = proof_resource_metrics(certificate)
    receipt = CandidateBodyReceipt(
        name=spec.name,
        dependency_count=len(spec.dependencies),
        command_count=len(spec.script),
        proof_nodes=nodes,
        proof_depth=depth,
        proof_objects=objects,
        proof_edges=edges,
        reused_objects=reused,
    )
    return CandidateBodyCompilation(target, certificate, receipt)


def compile_candidate_body(
    spec: TheoremSpec,
    *,
    core: Mapping[str, TheoremSpec] | None = None,
) -> CandidateBodyCompilation:
    """Kernel-check one script with its dependencies left as hypotheses.

    The returned target is the exact dependency-curried proposition.  This
    helper never resolves a theorem name to a certificate and must not be used
    as an admission receipt.
    """

    ordered, local = _candidate_table((spec,))
    public = dict(_specs_by_name() if core is None else core)
    return _compile_candidate_body(ordered[0], local=local, public=public)


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
    return tuple(
        _compile_candidate_body(spec, local=local, public=public).receipt
        for spec in ordered
    )


__all__ = [
    "CandidateBodyCompilation",
    "CandidateBodyError",
    "CandidateBodyReceipt",
    "compile_candidate_body",
    "replay_candidate_bodies",
]
