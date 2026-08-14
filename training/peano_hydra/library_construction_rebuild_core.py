"""Small, explicit A2.2 certificate-closing algorithm.

This module does exactly one proof-producing job: replay a ``TheoremSpec``
with a caller-selected direct dependency vector, peel the resulting
dependency introductions, and close the body with independently checked
dependency certificates.  The final certificate is checked from the empty
context against the theorem's original statement.

The surrounding Hydra bundle code owns input pinning, serialization, and all
claim boundaries.  In particular, this helper makes no optimization,
minimality, publication, or admission decision.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Formula
from peano_lab.kernel.proofs import Cut, ImpIntro, Proof
from peano_lab.library.candidate_validation import (
    CandidateBodyCompilation,
    compile_candidate_body,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


class ConstructionRebuildCoreError(ValueError):
    """The selected body or one of its dependency certificates is invalid."""


@dataclass(frozen=True, slots=True)
class DependencyCertificate:
    """One named, empty-context-checked dependency certificate."""

    name: str
    target: Formula
    proof: Proof


@dataclass(frozen=True, slots=True)
class ClosedCandidateCompilation:
    """A freshly built certificate for the uncurried original statement."""

    body: CandidateBodyCompilation
    target: Formula
    proof: Proof


def compile_closed_candidate(
    spec: TheoremSpec,
    *,
    core: Mapping[str, TheoremSpec],
    dependency_certificates: Mapping[str, DependencyCertificate],
) -> ClosedCandidateCompilation:
    """Build and kernel-check one self-contained candidate certificate.

    ``spec.dependencies`` is the exact direct Cut spine to construct.  Every
    supplied dependency is checked from the empty context before it is used,
    and the completed proof is independently checked from the empty context
    against ``spec.statement``.  Named theorems never become kernel axioms.
    """

    if type(spec) is not TheoremSpec:
        raise ConstructionRebuildCoreError("rebuild needs an exact TheoremSpec")
    if len(set(spec.dependencies)) != len(spec.dependencies):
        raise ConstructionRebuildCoreError("rebuild dependencies must be unique")
    if set(dependency_certificates) != set(spec.dependencies):
        raise ConstructionRebuildCoreError(
            "dependency certificate names differ from the selected vector"
        )

    body = compile_candidate_body(spec, core=core)
    closed = body.certificate
    for dependency in spec.dependencies:
        if type(closed) is not ImpIntro:
            raise ConstructionRebuildCoreError(
                f"candidate body did not expose dependency {dependency!r}"
            )
        closed = closed.body

    target = _closed_formula(spec.statement)
    for dependency in reversed(spec.dependencies):
        dependency_spec = core.get(dependency)
        if type(dependency_spec) is not TheoremSpec:
            raise ConstructionRebuildCoreError(
                f"unknown rebuild dependency {dependency!r}"
            )
        expected_target = _closed_formula(dependency_spec.statement)
        carrier = dependency_certificates[dependency]
        if type(carrier) is not DependencyCertificate or carrier.name != dependency:
            raise ConstructionRebuildCoreError(
                f"malformed dependency carrier for {dependency!r}"
            )
        if carrier.target != expected_target or not check(
            (), carrier.proof, expected_target
        ):
            raise ConstructionRebuildCoreError(
                f"dependency certificate {dependency!r} failed empty-context check"
            )
        closed = Cut(expected_target, target, carrier.proof, closed)

    if not check((), closed, target):
        raise ConstructionRebuildCoreError(
            f"rebuilt certificate for {spec.name!r} failed empty-context check"
        )
    return ClosedCandidateCompilation(body=body, target=target, proof=closed)


__all__ = [
    "ClosedCandidateCompilation",
    "ConstructionRebuildCoreError",
    "DependencyCertificate",
    "compile_closed_candidate",
]
