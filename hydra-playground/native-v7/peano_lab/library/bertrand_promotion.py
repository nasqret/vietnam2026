"""Fail-closed release planning for already enrolled Bertrand theorems.

Alpha membership and a focused capstone certificate do not promote their
dependency closure.  This module computes the exact, dependency-closed slice
of the sealed Alpha-v12 ledger and can independently check supplied ordinary
kernel certificates against its exact theorem statements.  It never mutates
an edition, interprets a receipt as a proof, or grants checked-use authority.
Actual evidence transition remains a separate, versioned release operation.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from hashlib import sha256
import json
from typing import Mapping, Sequence

from ..engine.state import start
from ..engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_LIVE_PROOF_OBJECTS,
    apply_tactic,
    checked_final,
)
from ..kernel.checker import check
from ..kernel.formulas import Imp
from ..kernel.proofs import Cut, DNE, ImpIntro, Proof
from . import editions_v12 as v12
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayError,
    _proof_envelope_metrics_bounded,
)
from .theorems import _closed_formula, _primitive


BERTRAND_PROMOTION_ROOTS = (
    "bertrand_closed_upper",
    "bertrand_strict",
)
MAX_BERTRAND_CLOSURE_MICROBATCH = 16
MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES = 125_000
MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS = 25_000
BERTRAND_BOUNDED_VALUATION_WINDOW = (
    "power_divides_decidable",
    "power_divides_zero",
    "bounded_power_valuation_search",
    "bounded_power_valuation_exists",
    "power_valuation_exists",
    "power_valuation_functional",
    "power_valuation_power_divides",
    "power_valuation_dominates",
)
BERTRAND_BOUNDED_VALUATION_DEFERRED = (
    "bounded_power_valuation_exists",
    "power_valuation_exists",
)
BERTRAND_BOUNDED_VALUATION_SAFE_MICROBATCHES = (
    ("power_divides_decidable",),
    ("power_divides_zero",),
    ("bounded_power_valuation_search",),
    (
        "power_valuation_functional",
        "power_valuation_power_divides",
        "power_valuation_dominates",
    ),
)


class BertrandPromotionError(ValueError):
    """A promotion slice or supplied certificate violates its trust boundary."""


@dataclass(frozen=True, slots=True)
class BertrandPromotionRow:
    """An exact Alpha-v12 dependency, without any upgraded evidence claim."""

    alpha_index: int
    name: str
    statement: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    membership: str
    evidence: str
    enrollment_origin: str
    source_module: str

    @property
    def needs_closure(self) -> bool:
        return self.evidence == v12.EvidenceStatus.BODY_CHECKED.value

    @property
    def checked_use(self) -> bool:
        return self.evidence in {
            v12.EvidenceStatus.STABLE_CLOSED.value,
            v12.EvidenceStatus.ALPHA_CLOSED.value,
        }


@dataclass(frozen=True, slots=True)
class BertrandPromotionPlan:
    """Immutable exact dependency slice; planning itself is not authority."""

    roots: tuple[str, ...]
    parent_alpha_enrollment_sha256: str
    parent_alpha_identity_sha256: str
    rows: tuple[BertrandPromotionRow, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    exact_surface_sha256: str

    @property
    def pending_rows(self) -> tuple[BertrandPromotionRow, ...]:
        return tuple(row for row in self.rows if row.needs_closure)

    @property
    def stable_rows(self) -> tuple[BertrandPromotionRow, ...]:
        return tuple(
            row
            for row in self.rows
            if row.evidence == v12.EvidenceStatus.STABLE_CLOSED.value
        )

    @property
    def alpha_closed_rows(self) -> tuple[BertrandPromotionRow, ...]:
        return tuple(
            row
            for row in self.rows
            if row.evidence == v12.EvidenceStatus.ALPHA_CLOSED.value
        )


@dataclass(frozen=True, slots=True)
class CheckedBertrandPromotionCertificate:
    """Diagnostics for one exact, freshly kernel-checked closed certificate."""

    name: str
    statement_sha256: str
    proof_nodes: int
    proof_objects: int
    proof_depth: int
    annotation_occurrences: int
    proof_envelope_depth: int


@dataclass(frozen=True, slots=True)
class ConstructedBertrandClosedCandidate:
    """One real closed candidate proof; release evidence remains unchanged."""

    name: str
    certificate: Proof
    diagnostics: CheckedBertrandPromotionCertificate


def _canonical_roots(roots: Sequence[str]) -> tuple[str, ...]:
    if isinstance(roots, str) or not isinstance(roots, (tuple, list)):
        raise BertrandPromotionError("promotion roots must be a tuple or list")
    if not roots:
        raise BertrandPromotionError("at least one Bertrand root is required")
    if any(type(root) is not str for root in roots):
        raise BertrandPromotionError("promotion root names must be exact strings")
    if len(set(roots)) != len(roots):
        raise BertrandPromotionError("duplicate Bertrand promotion root")
    unsupported = set(roots).difference(BERTRAND_PROMOTION_ROOTS)
    if unsupported:
        raise BertrandPromotionError(
            f"unsupported Bertrand promotion root: {sorted(unsupported)!r}"
        )
    return tuple(root for root in BERTRAND_PROMOTION_ROOTS if root in roots)


def _row(index: int, entry: v12.EditionEntry) -> BertrandPromotionRow:
    statement = entry.spec.statement
    return BertrandPromotionRow(
        alpha_index=index,
        name=entry.spec.name,
        statement=statement,
        statement_sha256=sha256(statement.encode("utf-8")).hexdigest(),
        dependencies=entry.spec.dependencies,
        membership=entry.membership.value,
        evidence=entry.evidence.value,
        enrollment_origin=entry.enrollment_origin.value,
        source_module=entry.source_module,
    )


def bertrand_promotion_plan(
    roots: Sequence[str] = BERTRAND_PROMOTION_ROOTS,
) -> BertrandPromotionPlan:
    """Return the exact Alpha-v12 closure without replaying any proof body.

    Every missing, non-topological, or pending-layered dependency fails closed.
    Existing evidence is preserved verbatim; no checked-use or Stable status
    changes as a result of computing this plan.
    """

    selected = _canonical_roots(roots)
    by_name = v12.ALPHA_EDITION.by_name
    closure: set[str] = set()
    pending = list(reversed(selected))
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        entry = by_name.get(name)
        if entry is None:
            raise BertrandPromotionError(f"missing Alpha-v12 dependency {name!r}")
        if entry.evidence is v12.EvidenceStatus.PENDING_LAYERED_CLOSURE:
            raise BertrandPromotionError(
                f"Bertrand promotion depends on pending layered closure {name!r}"
            )
        closure.add(name)
        pending.extend(reversed(entry.spec.dependencies))

    rows = tuple(
        _row(index, entry)
        for index, entry in enumerate(v12.ALPHA_ENTRIES)
        if entry.spec.name in closure
    )
    if len(rows) != len(closure):
        raise BertrandPromotionError("Alpha-v12 dependency closure is incomplete")

    observed: set[str] = set()
    edge_count = 0
    for row in rows:
        if row.name in observed:
            raise BertrandPromotionError(f"duplicate dependency {row.name!r}")
        missing = set(row.dependencies).difference(observed)
        if missing:
            raise BertrandPromotionError(
                f"non-topological dependencies for {row.name!r}: {sorted(missing)!r}"
            )
        edge_count += len(row.dependencies)
        observed.add(row.name)

    surfaces = [
        {
            "alpha_index": row.alpha_index,
            "dependencies": row.dependencies,
            "enrollment_origin": row.enrollment_origin,
            "evidence": row.evidence,
            "membership": row.membership,
            "name": row.name,
            "source_module": row.source_module,
            "statement_sha256": row.statement_sha256,
        }
        for row in rows
    ]
    payload = json.dumps(
        surfaces,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return BertrandPromotionPlan(
        roots=selected,
        parent_alpha_enrollment_sha256=v12.ALPHA_V12_ENROLLMENT_SHA256,
        parent_alpha_identity_sha256=v12.ALPHA_V12_IDENTITY_SHA256,
        rows=rows,
        dependency_edge_count=edge_count,
        ordered_names_sha256=sha256(
            "\n".join(row.name for row in rows).encode("utf-8")
        ).hexdigest(),
        exact_surface_sha256=sha256(payload).hexdigest(),
    )


def _contains_dne(certificate: Proof) -> bool:
    seen: set[int] = set()
    pending = [certificate]
    while pending:
        node = pending.pop()
        identity = id(node)
        if identity in seen:
            continue
        seen.add(identity)
        if type(node) is DNE:
            return True
        pending.extend(
            child
            for field in fields(node)
            if isinstance((child := getattr(node, field.name)), Proof)
        )
    return False


def _sealed_promotion_plan(
    plan: BertrandPromotionPlan | None,
) -> BertrandPromotionPlan:
    if plan is None:
        return bertrand_promotion_plan()
    if type(plan) is not BertrandPromotionPlan:
        raise BertrandPromotionError("promotion plan has an invalid type")
    if plan != bertrand_promotion_plan(plan.roots):
        raise BertrandPromotionError(
            "promotion plan does not match the exact sealed Alpha-v12 slice"
        )
    return plan


def bertrand_bounded_valuation_microbatch_plan(
    *,
    plan: BertrandPromotionPlan | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Return only dependency-safe valuation batches under the fixed hard caps.

    The two existence rows require two independently closed direct premises
    whose combined structural proof size already exceeds the 125,000-node
    ceiling. They remain explicitly deferred; later functional/projection
    rows are safe because their direct premises are already Stable-closed or
    empty. Planning does not construct proofs or alter edition evidence.
    """

    selected_plan = _sealed_promotion_plan(plan)
    window = selected_plan.pending_rows[16:24]
    if tuple(row.name for row in window) != BERTRAND_BOUNDED_VALUATION_WINDOW:
        raise BertrandPromotionError(
            "bounded valuation window no longer matches sealed Alpha dependency order"
        )

    deferred = set(BERTRAND_BOUNDED_VALUATION_DEFERRED)
    scheduled = tuple(
        name
        for names in BERTRAND_BOUNDED_VALUATION_SAFE_MICROBATCHES
        for name in names
    )
    if len(set(scheduled)) != len(scheduled) or set(scheduled) | deferred != {
        row.name for row in window
    }:
        raise BertrandPromotionError("bounded valuation schedule does not cover its exact window")
    if set(scheduled) & deferred:
        raise BertrandPromotionError("bounded valuation schedule includes a deferred row")

    available: set[str] = set()
    positions = {row.name: index for index, row in enumerate(window)}
    latest_position = -1
    for names in BERTRAND_BOUNDED_VALUATION_SAFE_MICROBATCHES:
        if not names or len(names) > MAX_BERTRAND_CLOSURE_MICROBATCH:
            raise BertrandPromotionError(
                "bounded valuation schedule violates its hard row cap"
            )
        for name in names:
            position = positions[name]
            if position <= latest_position:
                raise BertrandPromotionError(
                    "bounded valuation schedule is not dependency ordered"
                )
            latest_position = position
            unchecked = {
                dependency
                for dependency in v12.ALPHA_EDITION.by_name[name].spec.dependencies
                if not v12.ALPHA_EDITION.by_name[dependency].checked_use
            }
            missing = unchecked.difference(available)
            if missing:
                raise BertrandPromotionError(
                    f"bounded valuation schedule lacks closed prerequisites: {sorted(missing)!r}"
                )
            available.add(name)
    return BERTRAND_BOUNDED_VALUATION_SAFE_MICROBATCHES


def check_bertrand_promotion_certificate(
    name: str,
    certificate: Proof,
    *,
    plan: BertrandPromotionPlan | None = None,
) -> CheckedBertrandPromotionCertificate:
    """Check one exact empty-context proof; never infer it from a receipt."""

    selected_plan = _sealed_promotion_plan(plan)
    row = next((item for item in selected_plan.rows if item.name == name), None)
    if row is None:
        raise BertrandPromotionError(f"theorem {name!r} is outside the promotion slice")
    if not isinstance(certificate, Proof):
        raise BertrandPromotionError("promotion evidence must be a kernel proof")
    if _contains_dne(certificate):
        raise BertrandPromotionError("promotion certificate contains classical DNE")

    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    try:
        envelope = _proof_envelope_metrics_bounded(
            certificate,
            max_proof_occurrences=MAX_LIVE_PROOF_NODES,
            max_proof_objects=MAX_LIVE_PROOF_OBJECTS,
            max_proof_depth=MAX_LIVE_PROOF_DEPTH,
            max_annotation_occurrences=limits.max_candidate_annotation_occurrences,
            max_annotation_depth=limits.max_formula_depth,
            max_envelope_depth=limits.max_candidate_envelope_depth,
            label=f"Bertrand promotion certificate {name}",
        )
    except (LayeredReplayError, TypeError, ValueError) as exc:
        raise BertrandPromotionError(
            f"promotion certificate for {name!r} violates its resource envelope"
        ) from exc

    target = _closed_formula(row.statement)
    if not check((), certificate, target):
        raise BertrandPromotionError(
            f"intuitionistic kernel rejected empty-context theorem {name!r}"
        )

    nodes, objects, depth, annotations, envelope_depth = envelope
    return CheckedBertrandPromotionCertificate(
        name=name,
        statement_sha256=row.statement_sha256,
        proof_nodes=nodes,
        proof_objects=objects,
        proof_depth=depth,
        annotation_occurrences=annotations,
        proof_envelope_depth=envelope_depth,
    )


def check_bertrand_promotion_batch(
    certificates: Mapping[str, Proof],
    *,
    plan: BertrandPromotionPlan | None = None,
) -> tuple[CheckedBertrandPromotionCertificate, ...]:
    """Require one freshly checked closed proof for every body-only ancestor.

    Even a successful result changes no edition. Independent cold-process,
    mutation, provenance, and explicit versioned-release gates remain separate.
    """

    selected_plan = _sealed_promotion_plan(plan)
    if not isinstance(certificates, Mapping):
        raise BertrandPromotionError("promotion certificates must be a mapping")

    required = {row.name for row in selected_plan.pending_rows}
    supplied = set(certificates)
    missing = required.difference(supplied)
    unexpected = supplied.difference(required)
    if missing:
        raise BertrandPromotionError(
            f"missing {len(missing)} dependency-closed promotion certificates"
        )
    if unexpected:
        raise BertrandPromotionError(
            f"unexpected promotion certificates: {sorted(unexpected)!r}"
        )
    return tuple(
        check_bertrand_promotion_certificate(
            row.name,
            certificates[row.name],
            plan=selected_plan,
        )
        for row in selected_plan.pending_rows
    )


def construct_bertrand_closed_candidate(
    name: str,
    *,
    prerequisites: Mapping[str, Proof] | None = None,
    plan: BertrandPromotionPlan | None = None,
) -> ConstructedBertrandClosedCandidate:
    """Close one body-only row using independently checked direct premises.

    Stable and already-closed Alpha dependencies are replayed through the
    existing edition boundary. Every body-only direct dependency must be
    supplied as an actual independently checked proof. This is a bounded,
    incremental constructor, not recursive promotion and not a release.
    """

    selected_plan = _sealed_promotion_plan(plan)
    row = next((item for item in selected_plan.rows if item.name == name), None)
    if row is None:
        raise BertrandPromotionError(f"theorem {name!r} is outside the promotion slice")
    if not row.needs_closure:
        raise BertrandPromotionError(f"theorem {name!r} already has closed evidence")
    provided = {} if prerequisites is None else prerequisites
    if not isinstance(provided, Mapping):
        raise BertrandPromotionError("candidate prerequisites must be a mapping")

    required = {
        dependency
        for dependency in row.dependencies
        if not v12.ALPHA_EDITION.by_name[dependency].checked_use
    }
    missing = required.difference(provided)
    unexpected = set(provided).difference(required)
    if missing:
        raise BertrandPromotionError(
            f"missing independently closed prerequisite proofs: {sorted(missing)!r}"
        )
    if unexpected:
        raise BertrandPromotionError(
            f"unexpected candidate prerequisite proofs: {sorted(unexpected)!r}"
        )

    dependency_formulas = tuple(
        _closed_formula(v12.ALPHA_EDITION.by_name[dependency].spec.statement)
        for dependency in row.dependencies
    )
    dependency_proofs: list[Proof] = []
    for dependency in row.dependencies:
        dependency_entry = v12.ALPHA_EDITION.by_name[dependency]
        if dependency_entry.checked_use:
            certificate = v12.replay(dependency, edition=v12.EditionName.ALPHA).certificate
        else:
            certificate = provided[dependency]
        check_bertrand_promotion_certificate(
            dependency,
            certificate,
            plan=selected_plan,
        )
        dependency_proofs.append(certificate)

    target = _closed_formula(row.statement)
    body_target = target
    for dependency_formula in reversed(dependency_formulas):
        body_target = Imp(dependency_formula, body_target)

    try:
        state = start(body_target)
        for dependency in row.dependencies:
            state = apply_tactic(state, "intro", dependency)
        exact_spec = v12.ALPHA_EDITION.by_name[name].spec
        for command in exact_spec.script:
            tactic, arguments = _primitive(command)
            if tactic == "use":
                raise BertrandPromotionError(
                    f"candidate {name!r} attempts implicit theorem authority"
                )
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, body_target)
    except BertrandPromotionError:
        raise
    except (AttributeError, IndexError, RuntimeError, TypeError, ValueError) as exc:
        raise BertrandPromotionError(
            f"cannot replay exact Alpha-v12 proof body for {name!r}"
        ) from exc

    closed = body
    for dependency in row.dependencies:
        if type(closed) is not ImpIntro:
            raise BertrandPromotionError(
                f"candidate {name!r} did not expose premise {dependency!r}"
            )
        closed = closed.body
    for formula, proof in reversed(
        tuple(zip(dependency_formulas, dependency_proofs, strict=True))
    ):
        closed = Cut(formula, target, proof, closed)

    diagnostics = check_bertrand_promotion_certificate(
        name,
        closed,
        plan=selected_plan,
    )
    return ConstructedBertrandClosedCandidate(name, closed, diagnostics)


def construct_bertrand_closed_microbatch(
    names: Sequence[str],
    *,
    prerequisites: Mapping[str, Proof] | None = None,
    plan: BertrandPromotionPlan | None = None,
) -> tuple[ConstructedBertrandClosedCandidate, ...]:
    """Close at most sixteen dependency-ordered body-only rows in memory.

    Earlier checked candidates may be passed between microbatches as actual
    proof objects. Hard row, aggregate-node, and aggregate-object limits
    prevent an accidental attempt to materialize the whole 341-row release
    slice on the workstation.
    """

    selected_plan = _sealed_promotion_plan(plan)
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise BertrandPromotionError("closure microbatch names must be a tuple or list")
    if not names:
        raise BertrandPromotionError("closure microbatch cannot be empty")
    if len(names) > MAX_BERTRAND_CLOSURE_MICROBATCH:
        raise BertrandPromotionError(
            f"closure microbatch exceeds {MAX_BERTRAND_CLOSURE_MICROBATCH} rows"
        )
    if any(type(name) is not str for name in names):
        raise BertrandPromotionError("closure microbatch names must be exact strings")
    if len(set(names)) != len(names):
        raise BertrandPromotionError("duplicate closure microbatch theorem")

    order = {row.name: index for index, row in enumerate(selected_plan.pending_rows)}
    positions = tuple(order.get(name, -1) for name in names)
    if -1 in positions:
        raise BertrandPromotionError("closure microbatch contains a nonpending theorem")
    if positions != tuple(sorted(positions)):
        raise BertrandPromotionError("closure microbatch is not in Alpha dependency order")

    provided = {} if prerequisites is None else prerequisites
    if not isinstance(provided, Mapping):
        raise BertrandPromotionError("closure microbatch prerequisites must be a mapping")
    invalid = set(provided).difference(order)
    if invalid:
        raise BertrandPromotionError(
            f"closure microbatch has unknown prerequisite proofs: {sorted(invalid)!r}"
        )
    certificates = dict(provided)
    result: list[ConstructedBertrandClosedCandidate] = []
    total_nodes = 0
    total_objects = 0
    for name in names:
        exact_row = v12.ALPHA_EDITION.by_name[name]
        unchecked = {
            dependency
            for dependency in exact_row.spec.dependencies
            if not v12.ALPHA_EDITION.by_name[dependency].checked_use
        }
        direct = {
            dependency: certificates[dependency]
            for dependency in unchecked
            if dependency in certificates
        }
        candidate = construct_bertrand_closed_candidate(
            name,
            prerequisites=direct,
            plan=selected_plan,
        )
        total_nodes += candidate.diagnostics.proof_nodes
        total_objects += candidate.diagnostics.proof_objects
        if total_nodes > MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES:
            raise BertrandPromotionError(
                "closure microbatch exceeds its aggregate proof-node budget"
            )
        if total_objects > MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS:
            raise BertrandPromotionError(
                "closure microbatch exceeds its aggregate proof-object budget"
            )
        certificates[name] = candidate.certificate
        result.append(candidate)
    return tuple(result)


__all__ = [
    "BERTRAND_BOUNDED_VALUATION_DEFERRED",
    "BERTRAND_BOUNDED_VALUATION_SAFE_MICROBATCHES",
    "BERTRAND_BOUNDED_VALUATION_WINDOW",
    "BERTRAND_PROMOTION_ROOTS",
    "MAX_BERTRAND_CLOSURE_MICROBATCH",
    "MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_NODES",
    "MAX_BERTRAND_CLOSURE_MICROBATCH_PROOF_OBJECTS",
    "BertrandPromotionError",
    "BertrandPromotionPlan",
    "BertrandPromotionRow",
    "CheckedBertrandPromotionCertificate",
    "ConstructedBertrandClosedCandidate",
    "bertrand_bounded_valuation_microbatch_plan",
    "bertrand_promotion_plan",
    "check_bertrand_promotion_batch",
    "check_bertrand_promotion_certificate",
    "construct_bertrand_closed_candidate",
    "construct_bertrand_closed_microbatch",
]
