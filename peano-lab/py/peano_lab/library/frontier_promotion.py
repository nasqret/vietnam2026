"""Fail-closed, bounded empty-context planning for Alpha-v13 proof frontiers.

The completed Lucas and Lagrange statements are Alpha-v13 enrolled, but their
dependency-curried body receipts do not grant checked use.  This module plans
their exact dependency-closed slices and constructs only actual, independently
kernel-checked empty-context certificates inside immutable hard limits.  It
never changes Alpha or Stable membership, evidence, or release authority.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, fields, replace
from hashlib import sha256
import json
import subprocess
import sys
from typing import Mapping, Sequence

from ..engine.state import start
from ..engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    apply_tactic,
    checked_final,
)
from ..kernel.checker import check
from ..kernel.formulas import Imp
from ..kernel.proofs import Cut, DNE, ImpIntro, Proof
from . import editions_v13 as v13
from .layered_replay import (
    DEFAULT_LAYERED_REPLAY_LIMITS,
    LayeredReplayBundle,
    LayeredReplayError,
    LayeredReplayNode,
    _proof_envelope_metrics_bounded,
    compile_layered_replay,
)
from .theorems import _closed_formula, _primitive


FRONTIER_PROMOTION_ROOTS = (
    "lucas_theorem",
    "four_square_lagrange",
)
MAX_FRONTIER_CLOSURE_MICROBATCH = 16
MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES = 125_000
MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS = 25_000
FRONTIER_COLD_CHECK_SCHEMA = "peano-lab-frontier-cold-kernel-check-v1"

# Measured structural occurrences of actual individually checked direct
# prerequisites.  These are diagnostic observations, never theorem evidence;
# the ordinary constructor still measures every supplied Proof from scratch.
LUCAS_FACTORIAL_BRIDGE_OBSERVED_DIRECT_PROOF_NODES = (
    ("choose_exists", 89_492),
    ("choose_weighted_vertical", 102_493),
    ("choose_self_of_eq", 2_236),
    ("factorial_length_eq_transport", 26),
    ("factorial_weighted_product_combine", 382),
)
LUCAS_FACTORIAL_BRIDGE_NAIVE_DIRECT_NODE_LOWER_BOUND = sum(
    count for _name, count in LUCAS_FACTORIAL_BRIDGE_OBSERVED_DIRECT_PROOF_NODES
)
LUCAS_PRIME_DIVIDES_MAXIMAL_SHARED_ROWS = (
    "beta_pascal_zero_row_pointwise_functional",
    "beta_pascal_row_step_pointwise_functional",
    "beta_pascal_table_row_pointwise_functional",
    "choose_out_of_range_zero",
    "choose_zero",
    "beta_pascal_table_diagonal_boundary",
    "choose_self",
    "beta_pascal_table_successor_cell_recurrence",
    "choose_succ_succ_of_lt",
    "choose_succ_succ",
    "choose_self_of_eq",
    "choose_weighted_vertical",
    "choose_factorial_bridge",
    "factorial_prime_divides_of_le",
    "factorial_prime_le_of_divides",
)
LUCAS_PRIME_DIVIDES_OBSERVED_UNCHECKED_LEAF_PROOF_NODES = (
    ("choose_exists", 89_492),
    ("factorial_length_eq_transport", 26),
    ("factorial_weighted_product_combine", 382),
)
LUCAS_PRIME_DIVIDES_SEALED_STABLE_LEAF_COUNT = 29
LUCAS_PRIME_DIVIDES_SEALED_STABLE_LEAF_PROOF_NODES = 76_923
LUCAS_PRIME_DIVIDES_SHARED_LEAF_NODE_LOWER_BOUND = (
    LUCAS_PRIME_DIVIDES_SEALED_STABLE_LEAF_PROOF_NODES
    + sum(
        count
        for _name, count in LUCAS_PRIME_DIVIDES_OBSERVED_UNCHECKED_LEAF_PROOF_NODES
    )
)


class FrontierPromotionError(ValueError):
    """A frontier slice, resource envelope, or actual proof is invalid."""


@dataclass(frozen=True, slots=True)
class FrontierPromotionRow:
    """One exact Alpha-v13 theorem surface, retaining its existing evidence."""

    alpha_index: int
    name: str
    statement: str
    statement_sha256: str
    dependencies: tuple[str, ...]
    membership: str
    evidence: str
    enrollment_origin: str
    source_module: str
    source_release: str

    @property
    def needs_closure(self) -> bool:
        return self.evidence == v13.EvidenceStatus.BODY_CHECKED.value

    @property
    def checked_use(self) -> bool:
        return self.evidence in {
            v13.EvidenceStatus.STABLE_CLOSED.value,
            v13.EvidenceStatus.ALPHA_CLOSED.value,
        }


@dataclass(frozen=True, slots=True)
class FrontierPromotionPlan:
    """Exact immutable dependency slice; planning is never checked authority."""

    roots: tuple[str, ...]
    parent_alpha_enrollment_sha256: str
    parent_alpha_identity_sha256: str
    rows: tuple[FrontierPromotionRow, ...]
    dependency_edge_count: int
    ordered_names_sha256: str
    exact_surface_sha256: str

    @property
    def pending_rows(self) -> tuple[FrontierPromotionRow, ...]:
        return tuple(row for row in self.rows if row.needs_closure)

    @property
    def stable_rows(self) -> tuple[FrontierPromotionRow, ...]:
        return tuple(
            row
            for row in self.rows
            if row.evidence == v13.EvidenceStatus.STABLE_CLOSED.value
        )

    @property
    def alpha_closed_rows(self) -> tuple[FrontierPromotionRow, ...]:
        return tuple(
            row
            for row in self.rows
            if row.evidence == v13.EvidenceStatus.ALPHA_CLOSED.value
        )

    @property
    def unchecked_parent_rows(self) -> tuple[FrontierPromotionRow, ...]:
        return tuple(
            row
            for row in self.pending_rows
            if row.source_release == "v12"
        )

    @property
    def unchecked_frontier_rows(self) -> tuple[FrontierPromotionRow, ...]:
        return tuple(
            row
            for row in self.pending_rows
            if row.source_release == "v13"
        )


@dataclass(frozen=True, slots=True)
class CheckedFrontierPromotionCertificate:
    """Metrics for one actual independently checked empty-context proof."""

    name: str
    statement_sha256: str
    proof_nodes: int
    proof_objects: int
    proof_depth: int
    annotation_occurrences: int
    proof_envelope_depth: int


@dataclass(frozen=True, slots=True)
class ConstructedFrontierClosedCandidate:
    """An actual proof object; existing release evidence remains unchanged."""

    name: str
    certificate: Proof
    diagnostics: CheckedFrontierPromotionCertificate


def _canonical_roots(roots: Sequence[str]) -> tuple[str, ...]:
    if isinstance(roots, str) or not isinstance(roots, (tuple, list)):
        raise FrontierPromotionError("frontier promotion roots must be a tuple or list")
    if not roots:
        raise FrontierPromotionError("at least one frontier root is required")
    if any(type(root) is not str for root in roots):
        raise FrontierPromotionError("frontier root names must be exact strings")
    if len(set(roots)) != len(roots):
        raise FrontierPromotionError("duplicate frontier promotion root")
    unsupported = set(roots).difference(FRONTIER_PROMOTION_ROOTS)
    if unsupported:
        raise FrontierPromotionError(
            f"unsupported frontier promotion root: {sorted(unsupported)!r}"
        )
    return tuple(root for root in FRONTIER_PROMOTION_ROOTS if root in roots)


def _row(index: int, entry: v13.EditionEntry) -> FrontierPromotionRow:
    return FrontierPromotionRow(
        alpha_index=index,
        name=entry.spec.name,
        statement=entry.spec.statement,
        statement_sha256=sha256(entry.spec.statement.encode("utf-8")).hexdigest(),
        dependencies=entry.spec.dependencies,
        membership=entry.membership.value,
        evidence=entry.evidence.value,
        enrollment_origin=entry.enrollment_origin.value,
        source_module=entry.source_module,
        source_release="v12" if index < v13.PARENT_ALPHA_V12_COUNT else "v13",
    )


def frontier_promotion_plan(
    roots: Sequence[str] = FRONTIER_PROMOTION_ROOTS,
) -> FrontierPromotionPlan:
    """Return exact closed slices without replaying or claiming any proof."""

    selected = _canonical_roots(roots)
    table = v13.ALPHA_EDITION.by_name
    needed: set[str] = set()
    pending = list(reversed(selected))
    while pending:
        name = pending.pop()
        if name in needed:
            continue
        entry = table.get(name)
        if entry is None:
            raise FrontierPromotionError(f"missing Alpha-v13 dependency {name!r}")
        if entry.evidence is v13.EvidenceStatus.PENDING_LAYERED_CLOSURE:
            raise FrontierPromotionError(
                f"frontier promotion depends on pending layered closure {name!r}"
            )
        needed.add(name)
        pending.extend(reversed(entry.spec.dependencies))

    rows = tuple(
        _row(index, entry)
        for index, entry in enumerate(v13.ALPHA_ENTRIES)
        if entry.spec.name in needed
    )
    if len(rows) != len(needed):
        raise FrontierPromotionError("Alpha-v13 dependency slice is incomplete")

    seen: set[str] = set()
    edge_count = 0
    for row in rows:
        if row.name in seen:
            raise FrontierPromotionError(f"duplicate frontier theorem {row.name!r}")
        missing = set(row.dependencies).difference(seen)
        if missing:
            raise FrontierPromotionError(
                f"non-topological frontier dependencies for {row.name!r}: {sorted(missing)!r}"
            )
        edge_count += len(row.dependencies)
        seen.add(row.name)

    surfaces = [
        {
            "alpha_index": row.alpha_index,
            "dependencies": row.dependencies,
            "enrollment_origin": row.enrollment_origin,
            "evidence": row.evidence,
            "membership": row.membership,
            "name": row.name,
            "source_module": row.source_module,
            "source_release": row.source_release,
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
    return FrontierPromotionPlan(
        roots=selected,
        parent_alpha_enrollment_sha256=v13.ALPHA_V13_ENROLLMENT_SHA256,
        parent_alpha_identity_sha256=v13.ALPHA_V13_IDENTITY_SHA256,
        rows=rows,
        dependency_edge_count=edge_count,
        ordered_names_sha256=sha256(
            "\n".join(row.name for row in rows).encode("utf-8")
        ).hexdigest(),
        exact_surface_sha256=sha256(payload).hexdigest(),
    )


def _sealed_plan(plan: FrontierPromotionPlan | None) -> FrontierPromotionPlan:
    if plan is None:
        return frontier_promotion_plan()
    if type(plan) is not FrontierPromotionPlan:
        raise FrontierPromotionError("frontier promotion plan has an invalid type")
    if plan != frontier_promotion_plan(plan.roots):
        raise FrontierPromotionError(
            "frontier promotion plan does not match the exact sealed Alpha-v13 slice"
        )
    return plan


def frontier_pending_layers(
    *,
    plan: FrontierPromotionPlan | None = None,
) -> tuple[tuple[str, ...], ...]:
    """Expose exact dependency-ready unchecked layers without constructing proofs."""

    selected = _sealed_plan(plan)
    remaining = {row.name for row in selected.pending_rows}
    result: list[tuple[str, ...]] = []
    while remaining:
        ready = tuple(
            row.name
            for row in selected.pending_rows
            if row.name in remaining
            and not any(dependency in remaining for dependency in row.dependencies)
        )
        if not ready:
            raise FrontierPromotionError("frontier pending dependencies contain a cycle")
        result.append(ready)
        remaining.difference_update(ready)
    return tuple(result)


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


def check_frontier_promotion_certificate(
    name: str,
    certificate: Proof,
    *,
    plan: FrontierPromotionPlan | None = None,
) -> CheckedFrontierPromotionCertificate:
    """Check one actual intuitionistic empty-context proof against its exact row."""

    selected = _sealed_plan(plan)
    row = next((item for item in selected.rows if item.name == name), None)
    if row is None:
        raise FrontierPromotionError(f"theorem {name!r} is outside the frontier slice")
    if not isinstance(certificate, Proof):
        raise FrontierPromotionError("frontier promotion evidence must be a kernel proof")
    if _contains_dne(certificate):
        raise FrontierPromotionError("frontier promotion certificate contains classical DNE")

    limits = DEFAULT_LAYERED_REPLAY_LIMITS
    try:
        envelope = _proof_envelope_metrics_bounded(
            certificate,
            max_proof_occurrences=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
            max_proof_objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
            max_proof_depth=MAX_LIVE_PROOF_DEPTH,
            max_annotation_occurrences=limits.max_candidate_annotation_occurrences,
            max_annotation_depth=limits.max_formula_depth,
            max_envelope_depth=limits.max_candidate_envelope_depth,
            label=f"frontier promotion certificate {name}",
        )
    except (LayeredReplayError, TypeError, ValueError) as exc:
        raise FrontierPromotionError(
            f"frontier certificate for {name!r} violates its resource envelope"
        ) from exc

    if not check((), certificate, _closed_formula(row.statement)):
        raise FrontierPromotionError(
            f"intuitionistic kernel rejected empty-context frontier theorem {name!r}"
        )

    nodes, objects, depth, annotations, envelope_depth = envelope
    return CheckedFrontierPromotionCertificate(
        name=name,
        statement_sha256=row.statement_sha256,
        proof_nodes=nodes,
        proof_objects=objects,
        proof_depth=depth,
        annotation_occurrences=annotations,
        proof_envelope_depth=envelope_depth,
    )


def check_frontier_promotion_batch(
    certificates: Mapping[str, Proof],
    *,
    plan: FrontierPromotionPlan | None = None,
) -> tuple[CheckedFrontierPromotionCertificate, ...]:
    """Require actual closed proofs for every unchecked theorem in the slice."""

    selected = _sealed_plan(plan)
    if not isinstance(certificates, Mapping):
        raise FrontierPromotionError("frontier promotion certificates must be a mapping")
    required = {row.name for row in selected.pending_rows}
    supplied = set(certificates)
    missing = required.difference(supplied)
    unexpected = supplied.difference(required)
    if missing:
        raise FrontierPromotionError(
            f"missing {len(missing)} dependency-closed frontier certificates"
        )
    if unexpected:
        raise FrontierPromotionError(
            f"unexpected frontier promotion certificates: {sorted(unexpected)!r}"
        )
    return tuple(
        check_frontier_promotion_certificate(row.name, certificates[row.name], plan=selected)
        for row in selected.pending_rows
    )


def construct_frontier_closed_candidate(
    name: str,
    *,
    prerequisites: Mapping[str, Proof] | None = None,
    plan: FrontierPromotionPlan | None = None,
) -> ConstructedFrontierClosedCandidate:
    """Construct one actual closed proof using only independently checked premises."""

    selected = _sealed_plan(plan)
    row = next((item for item in selected.rows if item.name == name), None)
    if row is None:
        raise FrontierPromotionError(f"theorem {name!r} is outside the frontier slice")
    if not row.needs_closure:
        raise FrontierPromotionError(f"theorem {name!r} already has closed evidence")
    provided = {} if prerequisites is None else prerequisites
    if not isinstance(provided, Mapping):
        raise FrontierPromotionError("frontier candidate prerequisites must be a mapping")

    table = v13.ALPHA_EDITION.by_name
    required = {
        dependency
        for dependency in row.dependencies
        if not table[dependency].checked_use
    }
    missing = required.difference(provided)
    unexpected = set(provided).difference(required)
    if missing:
        raise FrontierPromotionError(
            f"missing independently closed frontier prerequisites: {sorted(missing)!r}"
        )
    if unexpected:
        raise FrontierPromotionError(
            f"unexpected frontier prerequisite proofs: {sorted(unexpected)!r}"
        )

    dependency_formulas = tuple(
        _closed_formula(table[dependency].spec.statement)
        for dependency in row.dependencies
    )
    dependency_proofs: list[Proof] = []
    direct_nodes = 0
    direct_objects = 0
    for dependency in row.dependencies:
        entry = table[dependency]
        certificate = (
            v13.replay(dependency, edition=v13.EditionName.ALPHA).certificate
            if entry.checked_use
            else provided[dependency]
        )
        receipt = check_frontier_promotion_certificate(
            dependency, certificate, plan=selected
        )
        direct_nodes += receipt.proof_nodes
        direct_objects += receipt.proof_objects
        if direct_nodes >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES:
            raise FrontierPromotionError(
                f"frontier candidate {name!r} direct premises already exceed "
                "the proof-node budget"
            )
        if direct_objects >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS:
            raise FrontierPromotionError(
                f"frontier candidate {name!r} direct premises already exceed "
                "the proof-object budget"
            )
        dependency_proofs.append(certificate)

    target = _closed_formula(row.statement)
    body_target = target
    for formula in reversed(dependency_formulas):
        body_target = Imp(formula, body_target)

    try:
        state = start(body_target)
        for dependency in row.dependencies:
            state = apply_tactic(state, "intro", dependency)
        for command in table[name].spec.script:
            tactic, arguments = _primitive(command)
            if tactic == "use":
                raise FrontierPromotionError(
                    f"frontier candidate {name!r} attempts implicit theorem authority"
                )
            state = apply_tactic(state, tactic, arguments)
        body = checked_final(state, body_target)
    except FrontierPromotionError:
        raise
    except (AttributeError, IndexError, RuntimeError, TypeError, ValueError) as exc:
        raise FrontierPromotionError(
            f"cannot replay exact Alpha-v13 proof body for {name!r}"
        ) from exc

    closed = body
    for dependency in row.dependencies:
        if type(closed) is not ImpIntro:
            raise FrontierPromotionError(
                f"frontier candidate {name!r} did not expose premise {dependency!r}"
            )
        closed = closed.body
    for formula, proof in reversed(
        tuple(zip(dependency_formulas, dependency_proofs, strict=True))
    ):
        closed = Cut(formula, target, proof, closed)

    diagnostics = check_frontier_promotion_certificate(name, closed, plan=selected)
    return ConstructedFrontierClosedCandidate(name, closed, diagnostics)


def construct_frontier_shared_closed_candidate(
    name: str,
    *,
    shared_rows: Sequence[str],
    prerequisites: Mapping[str, Proof] | None = None,
    plan: FrontierPromotionPlan | None = None,
) -> ConstructedFrontierClosedCandidate:
    """Share genuine local premise bodies without relaxing kernel/resource limits.

    Each requested body is replayed independently against its exact original
    dependency-curried target. Already-closed leaves are actual empty-context
    proofs, never receipts. The unchanged layered ``Cut`` compiler packages
    common leaves once, and the unchanged intuitionistic kernel must still
    accept the final ordinary proof under the same 125k/25k hard ceiling.
    At most sixteen newly constructed body rows are allowed.
    """

    selected = _sealed_plan(plan)
    if isinstance(shared_rows, str) or not isinstance(shared_rows, (tuple, list)):
        raise FrontierPromotionError("shared frontier rows must be a tuple or list")
    if any(type(item) is not str for item in shared_rows):
        raise FrontierPromotionError("shared frontier row names must be exact strings")
    body_names = tuple(shared_rows) + (name,)
    if len(body_names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise FrontierPromotionError("shared frontier microbatch exceeds its row budget")
    if len(set(body_names)) != len(body_names):
        raise FrontierPromotionError("shared frontier microbatch repeats a theorem")

    table = v13.ALPHA_EDITION.by_name
    positions = {row.name: row.alpha_index for row in selected.pending_rows}
    if not set(body_names) <= set(positions):
        raise FrontierPromotionError("shared frontier microbatch contains a nonpending theorem")
    if tuple(positions[item] for item in body_names) != tuple(
        sorted(positions[item] for item in body_names)
    ):
        raise FrontierPromotionError("shared frontier microbatch is not dependency ordered")

    provided = {} if prerequisites is None else prerequisites
    if not isinstance(provided, Mapping):
        raise FrontierPromotionError("shared frontier prerequisites must be a mapping")
    local = set(body_names)
    leaf_names = {
        dependency
        for item in body_names
        for dependency in table[item].spec.dependencies
        if dependency not in local
    }
    required = {dependency for dependency in leaf_names if not table[dependency].checked_use}
    missing = required.difference(provided)
    unexpected = set(provided).difference(required)
    if missing:
        raise FrontierPromotionError(
            f"missing independently closed shared frontier prerequisites: {sorted(missing)!r}"
        )
    if unexpected:
        raise FrontierPromotionError(
            f"unexpected shared frontier prerequisite proofs: {sorted(unexpected)!r}"
        )

    ordered_names = tuple(
        row.name for row in selected.rows if row.name in leaf_names or row.name in local
    )
    identities = {item: index for index, item in enumerate(ordered_names)}
    nodes: list[LayeredReplayNode] = []
    leaf_node_budget = 0
    leaf_object_budget = 0
    for item in ordered_names:
        exact = table[item].spec
        formula = _closed_formula(exact.statement)
        if item not in local:
            certificate = (
                v13.replay(item, edition=v13.EditionName.ALPHA).certificate
                if table[item].checked_use
                else provided[item]
            )
            receipt = check_frontier_promotion_certificate(item, certificate, plan=selected)
            leaf_node_budget += receipt.proof_nodes
            leaf_object_budget += receipt.proof_objects
            if leaf_node_budget >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES:
                raise FrontierPromotionError(
                    f"shared frontier leaves for {name!r} already exceed the proof-node budget"
                )
            if leaf_object_budget >= MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS:
                raise FrontierPromotionError(
                    f"shared frontier leaves for {name!r} already exceed the proof-object budget"
                )
            nodes.append(LayeredReplayNode(identities[item], formula, (), certificate))
            continue

        target = formula
        for dependency in reversed(exact.dependencies):
            target = Imp(_closed_formula(table[dependency].spec.statement), target)
        try:
            state = start(target)
            for dependency in exact.dependencies:
                state = apply_tactic(state, "intro", dependency)
            for command in exact.script:
                tactic, arguments = _primitive(command)
                if tactic == "use":
                    raise FrontierPromotionError(
                        f"shared frontier candidate {item!r} attempts implicit authority"
                    )
                state = apply_tactic(state, tactic, arguments)
            body = checked_final(state, target)
        except FrontierPromotionError:
            raise
        except (AttributeError, IndexError, RuntimeError, TypeError, ValueError) as exc:
            raise FrontierPromotionError(
                f"cannot replay exact shared frontier body for {item!r}"
            ) from exc
        nodes.append(
            LayeredReplayNode(
                identities[item],
                formula,
                tuple(identities[dependency] for dependency in exact.dependencies),
                body,
            )
        )

    limits = replace(
        DEFAULT_LAYERED_REPLAY_LIMITS,
        max_body_occurrences=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
        max_body_objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
        max_total_body_occurrences=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
        max_total_body_objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
        max_candidate_proof_occurrences=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES,
        max_candidate_proof_objects=MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS,
    )
    root = identities[name]
    target = _closed_formula(table[name].spec.statement)
    candidate = compile_layered_replay(
        LayeredReplayBundle(tuple(nodes), root), target, limits=limits
    )
    if candidate is None:
        raise FrontierPromotionError(
            f"shared frontier proof for {name!r} violates its unchanged "
            "layered graph or resource envelope"
        )
    diagnostics = check_frontier_promotion_certificate(
        name, candidate.certificate, plan=selected
    )
    return ConstructedFrontierClosedCandidate(name, candidate.certificate, diagnostics)


def construct_frontier_closed_microbatch(
    names: Sequence[str],
    *,
    prerequisites: Mapping[str, Proof] | None = None,
    plan: FrontierPromotionPlan | None = None,
) -> tuple[ConstructedFrontierClosedCandidate, ...]:
    """Construct at most sixteen exact proofs under immutable aggregate limits."""

    selected = _sealed_plan(plan)
    if isinstance(names, str) or not isinstance(names, (tuple, list)):
        raise FrontierPromotionError("frontier microbatch names must be a tuple or list")
    if not names:
        raise FrontierPromotionError("frontier closure microbatch cannot be empty")
    if len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise FrontierPromotionError(
            f"frontier closure microbatch exceeds {MAX_FRONTIER_CLOSURE_MICROBATCH} rows"
        )
    if any(type(name) is not str for name in names):
        raise FrontierPromotionError("frontier microbatch names must be exact strings")
    if len(set(names)) != len(names):
        raise FrontierPromotionError("duplicate frontier closure microbatch theorem")

    order = {row.name: index for index, row in enumerate(selected.pending_rows)}
    positions = tuple(order.get(name, -1) for name in names)
    if -1 in positions:
        raise FrontierPromotionError("frontier microbatch contains a nonpending theorem")
    if positions != tuple(sorted(positions)):
        raise FrontierPromotionError("frontier microbatch is not in Alpha dependency order")

    provided = {} if prerequisites is None else prerequisites
    if not isinstance(provided, Mapping):
        raise FrontierPromotionError("frontier microbatch prerequisites must be a mapping")
    unexpected = set(provided).difference(order)
    if unexpected:
        raise FrontierPromotionError(
            f"frontier microbatch has unknown prerequisite proofs: {sorted(unexpected)!r}"
        )

    proofs = dict(provided)
    result: list[ConstructedFrontierClosedCandidate] = []
    total_nodes = 0
    total_objects = 0
    table = v13.ALPHA_EDITION.by_name
    for name in names:
        unchecked = {
            dependency
            for dependency in table[name].spec.dependencies
            if not table[dependency].checked_use
        }
        direct = {
            dependency: proofs[dependency]
            for dependency in unchecked
            if dependency in proofs
        }
        candidate = construct_frontier_closed_candidate(
            name, prerequisites=direct, plan=selected
        )
        total_nodes += candidate.diagnostics.proof_nodes
        total_objects += candidate.diagnostics.proof_objects
        if total_nodes > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES:
            raise FrontierPromotionError(
                "frontier microbatch exceeds its aggregate proof-node budget"
            )
        if total_objects > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS:
            raise FrontierPromotionError(
                "frontier microbatch exceeds its aggregate proof-object budget"
            )
        proofs[name] = candidate.certificate
        result.append(candidate)
    return tuple(result)


def cold_frontier_microbatch_receipts(
    names: Sequence[str],
    *,
    roots: Sequence[str] = FRONTIER_PROMOTION_ROOTS,
    timeout_seconds: int = 60,
) -> tuple[CheckedFrontierPromotionCertificate, ...]:
    """Run a genuine isolated-process kernel replay; receipts are not authority."""

    if type(timeout_seconds) is not int or timeout_seconds <= 0:
        raise FrontierPromotionError("cold frontier timeout must be a positive integer")
    selected_roots = _canonical_roots(roots)
    if isinstance(names, str) or not isinstance(names, (tuple, list)) or not names:
        raise FrontierPromotionError("cold frontier microbatch names must be a nonempty sequence")
    if len(names) > MAX_FRONTIER_CLOSURE_MICROBATCH:
        raise FrontierPromotionError("cold frontier microbatch exceeds its row budget")

    command = [
        sys.executable,
        "-m",
        "peano_lab.library.frontier_promotion",
        "--roots",
        ",".join(selected_roots),
        "--rows",
        ",".join(names),
    ]
    try:
        result = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise FrontierPromotionError("isolated frontier kernel replay failed") from exc
    if result.returncode:
        raise FrontierPromotionError(
            f"isolated frontier kernel replay rejected its microbatch: "
            f"{result.stderr.strip()[:300]}"
        )
    try:
        payload = json.loads(result.stdout)
    except (TypeError, ValueError) as exc:
        raise FrontierPromotionError("isolated frontier replay returned invalid JSON") from exc
    if (
        not isinstance(payload, dict)
        or payload.get("schema") != FRONTIER_COLD_CHECK_SCHEMA
        or payload.get("alpha_identity_sha256") != v13.ALPHA_V13_IDENTITY_SHA256
        or payload.get("roots") != list(selected_roots)
        or not isinstance(payload.get("receipts"), list)
    ):
        raise FrontierPromotionError("isolated frontier replay returned an invalid receipt envelope")
    try:
        receipts = tuple(
            CheckedFrontierPromotionCertificate(**receipt)
            for receipt in payload["receipts"]
        )
    except (TypeError, ValueError) as exc:
        raise FrontierPromotionError("isolated frontier replay returned invalid receipts") from exc
    if tuple(receipt.name for receipt in receipts) != tuple(names):
        raise FrontierPromotionError("isolated frontier replay changed its requested names")
    selected = frontier_promotion_plan(selected_roots)
    rows = {row.name: row for row in selected.pending_rows}
    total_nodes = 0
    total_objects = 0
    for receipt in receipts:
        exact = rows.get(receipt.name)
        if exact is None or receipt.statement_sha256 != exact.statement_sha256:
            raise FrontierPromotionError(
                "isolated frontier replay returned an unsealed theorem statement"
            )
        values = (
            receipt.proof_nodes,
            receipt.proof_objects,
            receipt.proof_depth,
            receipt.annotation_occurrences,
            receipt.proof_envelope_depth,
        )
        if any(type(value) is not int or value < 0 for value in values):
            raise FrontierPromotionError(
                "isolated frontier replay returned malformed resource metrics"
            )
        if receipt.proof_nodes == 0 or receipt.proof_objects == 0:
            raise FrontierPromotionError(
                "isolated frontier replay returned an empty proof receipt"
            )
        total_nodes += receipt.proof_nodes
        total_objects += receipt.proof_objects
    if total_nodes > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES:
        raise FrontierPromotionError(
            "isolated frontier replay exceeded its aggregate proof-node budget"
        )
    if total_objects > MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS:
        raise FrontierPromotionError(
            "isolated frontier replay exceeded its aggregate proof-object budget"
        )
    return receipts


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--roots", required=True)
    parser.add_argument("--rows", required=True)
    arguments = parser.parse_args(argv)
    roots = tuple(arguments.roots.split(","))
    names = tuple(arguments.rows.split(","))
    plan = frontier_promotion_plan(roots)
    checked = construct_frontier_closed_microbatch(names, plan=plan)
    payload = {
        "schema": FRONTIER_COLD_CHECK_SCHEMA,
        "alpha_identity_sha256": v13.ALPHA_V13_IDENTITY_SHA256,
        "roots": list(plan.roots),
        "receipts": [asdict(row.diagnostics) for row in checked],
    }
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "FRONTIER_COLD_CHECK_SCHEMA",
    "FRONTIER_PROMOTION_ROOTS",
    "LUCAS_FACTORIAL_BRIDGE_NAIVE_DIRECT_NODE_LOWER_BOUND",
    "LUCAS_FACTORIAL_BRIDGE_OBSERVED_DIRECT_PROOF_NODES",
    "LUCAS_PRIME_DIVIDES_MAXIMAL_SHARED_ROWS",
    "LUCAS_PRIME_DIVIDES_OBSERVED_UNCHECKED_LEAF_PROOF_NODES",
    "LUCAS_PRIME_DIVIDES_SEALED_STABLE_LEAF_COUNT",
    "LUCAS_PRIME_DIVIDES_SEALED_STABLE_LEAF_PROOF_NODES",
    "LUCAS_PRIME_DIVIDES_SHARED_LEAF_NODE_LOWER_BOUND",
    "MAX_FRONTIER_CLOSURE_MICROBATCH",
    "MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_NODES",
    "MAX_FRONTIER_CLOSURE_MICROBATCH_PROOF_OBJECTS",
    "CheckedFrontierPromotionCertificate",
    "ConstructedFrontierClosedCandidate",
    "FrontierPromotionError",
    "FrontierPromotionPlan",
    "FrontierPromotionRow",
    "check_frontier_promotion_batch",
    "check_frontier_promotion_certificate",
    "cold_frontier_microbatch_receipts",
    "construct_frontier_closed_candidate",
    "construct_frontier_closed_microbatch",
    "construct_frontier_shared_closed_candidate",
    "frontier_pending_layers",
    "frontier_promotion_plan",
]
