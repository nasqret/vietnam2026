#!/usr/bin/env python3
"""Freeze checked Hydra authority and prepare verified post-training evidence.

This command does not train a language model, admit new theorems, mutate either
mathematical DAG, or deploy public content.  Both route optimization and the
teacher-oracle candidate are independently replayed against their original
formulas before deterministic development-only JSONL artifacts are emitted.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import asdict, dataclass
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from constructive_definition_graph import DefinitionGraphError  # noqa: E402
from peano_lab.batch import MODEL_V1_COMMANDS  # noqa: E402
from sync_constructive_grand_campaign import (  # noqa: E402
    CampaignDagError,
    validate_campaign_dags,
)
from training.peano_hydra.curriculum import (  # noqa: E402
    HydraCurriculumError,
    VerifiedCurriculum,
    build_verified_curriculum,
    encode_jsonl,
)
from training.peano_hydra.development import (  # noqa: E402
    DevelopmentLimits,
    DiscoveryProposal,
    DiscoveryResult,
    HydraDevelopmentError,
    OptimizationResult,
    OptimizationRoute,
    discover_proof,
    optimize_proof,
    recorded_route_factory,
)
from training.peano_hydra.epoch import (  # noqa: E402
    EpochTheorem,
    HydraEpoch,
    HydraEpochError,
    freeze_epoch,
)
from training.peano_hydra.pilot import (  # noqa: E402
    PILOT_COMMANDS,
    TeacherOraclePilotError,
    load_checked_teacher_artifact,
)
from training.peano_hydra.runner import HydraRunnerError  # noqa: E402
from training.peano_policy.search import SearchLimits  # noqa: E402


OUTPUT_FILENAMES = (
    "epoch.json",
    "sft.jsonl",
    "preferences.jsonl",
    "discovery.jsonl",
    "manifest.json",
)
MAX_ADDITIONAL_CATALOG_THEOREMS = 512
MAX_CATALOG_ROUTE_DECISIONS = 32
MAX_CATALOG_TOTAL_TACTICS = 8_192
MAX_CATALOG_STATEMENT_BYTES = 4_096
MAX_CATALOG_DEPENDENCY_CLOSURE_TACTICS = 256
MAX_CATALOG_DEPENDENCY_CLOSURE_STATEMENT_BYTES = 8_192
MAX_CATALOG_ROUTE_EVIDENCE_BYTES = 512 * 1_024
MAX_CATALOG_TOTAL_EVIDENCE_BYTES = 24 * 1_024 * 1_024
CATALOG_MEMBERSHIPS = ("alpha_only", "stable")


@dataclass(frozen=True, slots=True)
class CatalogCollection:
    """One bounded checked collection and an exact whole-catalog census."""

    results: tuple[OptimizationResult, ...]
    coverage: dict[str, object]


def _strict_json(value: object, *, pretty: bool = False) -> bytes:
    rendered = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        indent=2 if pretty else None,
        separators=None if pretty else (",", ":"),
    )
    return (rendered + "\n").encode("utf-8")


def _audited_epoch() -> tuple[HydraEpoch, dict[str, object]]:
    epoch = freeze_epoch(REPOSITORY_ROOT)
    campaign_path = (
        REPOSITORY_ROOT / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
    )
    definition_path = campaign_path.with_name("definitions.json")
    catalog_path = (
        REPOSITORY_ROOT
        / "artifacts"
        / "peano-library"
        / "alpha"
        / f"catalog-{epoch.version}.json"
    )
    campaign_raw = campaign_path.read_bytes()
    definitions_raw = definition_path.read_bytes()
    catalog_raw = catalog_path.read_bytes()
    if (
        hashlib.sha256(campaign_raw).hexdigest() != epoch.campaign_artifact_sha256
        or hashlib.sha256(definitions_raw).hexdigest() != epoch.definition_artifact_sha256
        or hashlib.sha256(catalog_raw).hexdigest() != epoch.alpha_catalog_sha256
    ):
        raise HydraEpochError("a campaign artifact changed while Hydra was freezing its authority")
    audit = validate_campaign_dags(
        json.loads(campaign_raw),
        definition_graph=json.loads(definitions_raw),
        catalog=json.loads(catalog_raw),
        catalog_sha256=epoch.alpha_catalog_sha256,
    )
    agreements = (
        audit.alpha_version == epoch.version,
        audit.theorem_count == len(epoch.theorems),
        audit.theorem_edge_count == epoch.theorem_edge_count,
        audit.theorem_dag_sha256 == epoch.theorem_dag_sha256,
        audit.reviewed_definition_count == len(epoch.definitions),
        audit.reviewed_definition_edge_count == epoch.definition_edge_count,
        audit.reviewed_definition_dag_sha256 == epoch.reviewed_definition_dag_sha256,
        audit.milestone_count == epoch.milestone_count,
        audit.milestone_proof_edge_count == epoch.milestone_edge_count,
        audit.milestone_dag_sha256 == epoch.milestone_dag_sha256,
    )
    if not all(agreements):
        raise HydraEpochError("central product DAG audit disagrees with Hydra's frozen authority")
    return epoch, asdict(audit)


def _route_limits(command_count: int) -> SearchLimits:
    return SearchLimits(
        max_depth=command_count,
        beam_width=1,
        candidates_per_state=1,
        max_model_calls=command_count,
        max_states=command_count + 1,
    )


def _optimization(epoch: HydraEpoch) -> OptimizationResult:
    theorem = epoch.theorem("zero_add")
    if theorem is None:
        raise HydraEpochError("current immutable Stable foundation lacks zero_add")
    short = ("induction n", "simp", "simp [IH]")
    long = ("have h : 0 = 0", "refl", "induction n", "simp", "simp [IH]")
    capabilities = epoch.alpha_capabilities(
        allowed_commands=frozenset({"have", "induction", "refl", "simp"}),
        allowed_theorems=frozenset(),
    )
    routes = tuple(
        OptimizationRoute(
            name,
            recorded_route_factory(
                theorem.statement,
                commands,
                capabilities=capabilities,
                name=name,
            ),
            _route_limits(len(commands)),
        )
        for name, commands in (
            ("reviewed-long-baseline", long),
            ("reviewed-short-route", short),
        )
    )
    return optimize_proof(
        epoch,
        theorem.name,
        routes,
        capabilities=capabilities,
        limits=DevelopmentLimits(
            max_routes=2,
            max_total_model_calls=8,
            max_total_states=10,
            max_total_candidates=8,
        ),
    )


def _discovery(epoch: HydraEpoch) -> DiscoveryResult:
    artifact = load_checked_teacher_artifact()
    capabilities = epoch.alpha_capabilities(
        allowed_commands=PILOT_COMMANDS,
        allowed_theorems=frozenset(),
    )
    name = "triangular_product_even_hydra_candidate"
    proposal = DiscoveryProposal(
        name,
        artifact.theorem_source,
        (),
        recorded_route_factory(
            artifact.theorem_source,
            artifact.commands,
            capabilities=capabilities,
            name="teacher-oracle-triangular-even",
        ),
        _route_limits(len(artifact.commands)),
        source="teacher_oracle_plumbing",
    )
    return discover_proof(
        epoch,
        proposal,
        capabilities=capabilities,
        limits=DevelopmentLimits(
            max_routes=1,
            max_total_model_calls=len(artifact.commands),
            max_total_states=len(artifact.commands) + 1,
            max_total_candidates=len(artifact.commands),
        ),
    )


def _catalog_decisions(theorem: EpochTheorem) -> int:
    return len(theorem.dependencies) + len(theorem.script)


def _catalog_memberships(theorems: tuple[EpochTheorem, ...]) -> dict[str, int]:
    counts = Counter(theorem.membership for theorem in theorems)
    unknown = set(counts) - set(CATALOG_MEMBERSHIPS)
    if unknown:
        raise HydraDevelopmentError("frozen catalog contains an unknown theorem membership")
    return {membership: counts.get(membership, 0) for membership in CATALOG_MEMBERSHIPS}


def _catalog_prerequisite_profile(
    theorem: EpochTheorem,
    by_name: dict[str, EpochTheorem],
) -> tuple[str | None, int, int]:
    """Bound prerequisite work before any independently checked import runs.

    A short Alpha tactic script can import a promoted theorem whose ``use``
    operation independently loads an entire multi-megabyte campaign bundle.
    Route depth and retained trace bounds do not constrain that work. Broad
    automatic sampling therefore admits Alpha *targets*, but imports only
    bounded immutable Stable prerequisite closures. Explicit legacy requests
    remain strict and retain their existing behavior outside full-scan mode.
    """

    closure: set[str] = set()
    pending = list(theorem.dependencies)
    while pending:
        name = pending.pop()
        if name in closure:
            continue
        dependency = by_name.get(name)
        if dependency is None:
            raise HydraDevelopmentError("prerequisite profiling escaped the frozen theorem DAG")
        if dependency.membership != "stable":
            return "alpha_prerequisite_replay_bound", 0, 0
        closure.add(name)
        pending.extend(dependency.dependencies)
    tactics = sum(len(by_name[name].script) for name in closure)
    statement_bytes = sum(
        len(by_name[name].statement.encode("utf-8")) for name in closure
    )
    if (
        tactics > MAX_CATALOG_DEPENDENCY_CLOSURE_TACTICS
        or statement_bytes > MAX_CATALOG_DEPENDENCY_CLOSURE_STATEMENT_BYTES
    ):
        return "dependency_closure_bound", tactics, statement_bytes
    return None, tactics, statement_bytes


def _catalog_order(
    epoch: HydraEpoch,
    theorems: tuple[EpochTheorem, ...],
) -> tuple[EpochTheorem, ...]:
    """Scatter reproducibly across campaign eras while preserving membership balance."""

    groups = {
        membership: sorted(
            (theorem for theorem in theorems if theorem.membership == membership),
            key=lambda theorem: (
                hashlib.sha256(
                    f"{epoch.epoch_sha256}:{theorem.name}".encode("utf-8")
                ).digest(),
                theorem.enrollment_index,
            ),
        )
        for membership in CATALOG_MEMBERSHIPS
    }
    counts = {membership: len(group) for membership, group in groups.items()}
    positions = dict.fromkeys(CATALOG_MEMBERSHIPS, 0)
    total = sum(counts.values())
    ordered: list[EpochTheorem] = []
    for index in range(total):
        available = [
            membership
            for membership in CATALOG_MEMBERSHIPS
            if positions[membership] < counts[membership]
        ]
        membership = max(
            available,
            key=lambda item: (
                counts[item] * (index + 1) - positions[item] * total,
                item == "alpha_only",
            ),
        )
        ordered.append(groups[membership][positions[membership]])
        positions[membership] += 1
    return tuple(ordered)


def _checked_catalog_route(epoch: HydraEpoch, theorem: EpochTheorem) -> OptimizationResult:
    capabilities = epoch.alpha_capabilities(
        allowed_commands=MODEL_V1_COMMANDS,
        allowed_theorems=frozenset(theorem.dependencies),
    )
    # Authored rows are dependency-curried. Every actual direct prerequisite
    # must therefore be independently imported through its exact finite grant.
    commands = tuple(
        f"use {dependency} as {dependency}"
        for dependency in theorem.dependencies
    ) + theorem.script
    route = OptimizationRoute(
        f"catalog-{theorem.name}",
        recorded_route_factory(
            theorem.statement,
            commands,
            capabilities=capabilities,
            name=f"catalog-{theorem.name}",
        ),
        _route_limits(len(commands)),
    )
    return optimize_proof(
        epoch,
        theorem.name,
        (route,),
        capabilities=capabilities,
        limits=DevelopmentLimits(
            max_routes=1,
            max_total_model_calls=len(commands),
            max_total_states=len(commands) + 1,
            max_total_candidates=len(commands),
        ),
    )


def _catalog_evidence_bytes(result: OptimizationResult) -> int:
    replay = result.winner.replay
    if replay is None or replay.kernel_checked is not True:
        raise HydraDevelopmentError("catalog route has no independently checked retained evidence")
    return len(
        _strict_json(
            {
                "environment": result.winner.environment,
                "policy_identity": result.winner.policy_identity,
                "proposal_records": result.winner.proposal_records,
                "trace": replay.trace,
            }
        )
    )


def _catalog_failure_reason(error: Exception) -> str:
    message = str(error).casefold()
    if "source replay" in message:
        return "source_replay_rejected"
    if "baseline" in message or "no independently checked" in message:
        return "bounded_search_unknown"
    if "recursion" in message:
        return "parser_recursion_bound"
    return "checked_replay_rejected"


def _collect_catalog_routes(
    epoch: HydraEpoch,
    *,
    prefix_count: int,
    theorem_names: tuple[str, ...],
    scan_all: bool = False,
    max_decisions: int = MAX_CATALOG_ROUTE_DECISIONS,
    max_total_tactics: int = MAX_CATALOG_TOTAL_TACTICS,
) -> CatalogCollection:
    if type(epoch) is not HydraEpoch:
        raise TypeError("catalog collection needs one exact frozen Hydra epoch")
    if type(prefix_count) is not int or not 0 <= prefix_count <= MAX_ADDITIONAL_CATALOG_THEOREMS:
        raise HydraDevelopmentError(
            f"additional catalog prefix must contain 0–{MAX_ADDITIONAL_CATALOG_THEOREMS} theorems"
        )
    if type(theorem_names) is not tuple or not all(type(item) is str for item in theorem_names):
        raise HydraDevelopmentError("additional catalog targets must be an exact tuple of names")
    if type(scan_all) is not bool:
        raise TypeError("whole-catalog scanning must be an exact Boolean")
    if type(max_decisions) is not int or not 1 <= max_decisions <= MAX_CATALOG_ROUTE_DECISIONS:
        raise HydraDevelopmentError(
            f"each catalog route must reserve 1–{MAX_CATALOG_ROUTE_DECISIONS} tactic decisions"
        )
    if type(max_total_tactics) is not int or not 1 <= max_total_tactics <= MAX_CATALOG_TOTAL_TACTICS:
        raise HydraDevelopmentError(
            f"whole-catalog tactic budget must lie between 1 and {MAX_CATALOG_TOTAL_TACTICS}"
        )

    by_name = {theorem.name: theorem for theorem in epoch.theorems}
    if len(by_name) != len(epoch.theorems):
        raise HydraDevelopmentError("frozen catalog contains duplicate theorem names")
    decisions_eligible: list[EpochTheorem] = []
    resource_eligible: list[EpochTheorem] = []
    replay_safe: list[EpochTheorem] = []
    prerequisite_profiles: dict[str, tuple[str | None, int, int]] = {}
    statuses: dict[str, str] = {}
    unselected = "route_limit" if scan_all else "not_requested"
    for theorem in epoch.theorems:
        if theorem.name == "zero_add":
            statuses[theorem.name] = "built_in_optimization"
            continue
        if _catalog_decisions(theorem) > max_decisions:
            statuses[theorem.name] = "decision_bound"
            continue
        decisions_eligible.append(theorem)
        if len(theorem.statement.encode("utf-8")) > MAX_CATALOG_STATEMENT_BYTES:
            statuses[theorem.name] = "statement_byte_bound"
            continue
        resource_eligible.append(theorem)
        profile = _catalog_prerequisite_profile(theorem, by_name)
        prerequisite_profiles[theorem.name] = profile
        if profile[0] is None:
            replay_safe.append(theorem)
        statuses[theorem.name] = profile[0] if scan_all and profile[0] else unselected

    explicit: list[EpochTheorem] = []
    for name in theorem_names:
        theorem = by_name.get(name)
        if theorem is None:
            raise HydraDevelopmentError(f"catalog training theorem {name!r} is not enrolled")
        if name == "zero_add" or theorem in explicit:
            continue
        if _catalog_decisions(theorem) > max_decisions:
            raise HydraDevelopmentError(
                f"catalog training theorem {name!r} exceeds the {max_decisions}-decision "
                "Hydra search bound"
            )
        if len(theorem.statement.encode("utf-8")) > MAX_CATALOG_STATEMENT_BYTES:
            raise HydraDevelopmentError(
                f"catalog training theorem {name!r} exceeds the "
                f"{MAX_CATALOG_STATEMENT_BYTES}-byte statement bound"
            )
        if scan_all and prerequisite_profiles[theorem.name][0] is not None:
            raise HydraDevelopmentError(
                f"catalog training theorem {name!r} exceeds its bounded prerequisite "
                f"replay policy: {prerequisite_profiles[theorem.name][0]}"
            )
        explicit.append(theorem)

    if scan_all:
        requested_limit = prefix_count or MAX_ADDITIONAL_CATALOG_THEOREMS
        if len(explicit) > requested_limit:
            raise HydraDevelopmentError("explicit catalog targets exceed the requested route limit")
        explicit_names = {theorem.name for theorem in explicit}
        candidates = tuple(explicit) + tuple(
            theorem
            for theorem in _catalog_order(epoch, tuple(replay_safe))
            if theorem.name not in explicit_names
        )
    else:
        if len(resource_eligible) < prefix_count:
            raise HydraDevelopmentError("the frozen catalog has too few bounded proof-script targets")
        selected = list(resource_eligible[:prefix_count])
        selected_names = {theorem.name for theorem in selected}
        selected.extend(theorem for theorem in explicit if theorem.name not in selected_names)
        if len(selected) > MAX_ADDITIONAL_CATALOG_THEOREMS:
            raise HydraDevelopmentError("additional checked catalog targets exceed the reviewed bound")
        if sum(_catalog_decisions(theorem) for theorem in selected) > max_total_tactics:
            raise HydraDevelopmentError(
                "additional checked catalog routes exceed the whole-run tactic budget"
            )
        candidates = tuple(selected)
        requested_limit = len(candidates)

    results: list[OptimizationResult] = []
    attempted: list[EpochTheorem] = []
    failures: list[dict[str, object]] = []
    attempted_tactics = 0
    evidence_bytes = 0
    explicit_names = {theorem.name for theorem in explicit}
    for theorem in candidates:
        if len(attempted) >= requested_limit:
            break
        decisions = _catalog_decisions(theorem)
        if attempted_tactics + decisions > max_total_tactics:
            statuses[theorem.name] = "tactic_budget"
            if not scan_all or theorem.name in explicit_names:
                raise HydraDevelopmentError(
                    f"catalog theorem {theorem.name!r} exceeds the whole-run tactic budget"
                )
            continue
        # Failed attempts consume their complete reservation too. They can
        # never multiply the declared call, state, candidate, or memory caps.
        attempted.append(theorem)
        attempted_tactics += decisions
        try:
            checked = _checked_catalog_route(epoch, theorem)
            retained = _catalog_evidence_bytes(checked)
            if retained > MAX_CATALOG_ROUTE_EVIDENCE_BYTES:
                reason = "route_evidence_byte_bound"
            elif evidence_bytes + retained > MAX_CATALOG_TOTAL_EVIDENCE_BYTES:
                reason = "aggregate_evidence_byte_bound"
            else:
                reason = ""
            if reason:
                statuses[theorem.name] = reason
                failures.append(
                    {
                        "theorem_name": theorem.name,
                        "membership": theorem.membership,
                        "reason": reason,
                        "evidence_bytes": retained,
                    }
                )
                if not scan_all or theorem.name in explicit_names:
                    raise HydraDevelopmentError(
                        f"catalog theorem {theorem.name!r} exceeds its checked evidence byte budget"
                    )
                continue
        except (HydraDevelopmentError, HydraRunnerError, RecursionError, TypeError, ValueError) as error:
            reason = _catalog_failure_reason(error)
            statuses[theorem.name] = reason
            failures.append(
                {
                    "theorem_name": theorem.name,
                    "membership": theorem.membership,
                    "reason": reason,
                    "detail": " ".join(str(error).split())[:240],
                }
            )
            if not scan_all or theorem.name in explicit_names:
                raise HydraDevelopmentError(
                    f"catalog theorem {theorem.name!r} failed its bounded checked route: {error}"
                ) from error
            continue
        results.append(checked)
        evidence_bytes += retained
        statuses[theorem.name] = "checked"

    checked_theorems = tuple(by_name[result.theorem_name] for result in results)
    skipped_theorems = tuple(
        theorem for theorem in epoch.theorems if statuses[theorem.name] != "checked"
    )
    skipped_reasons = Counter(
        reason for reason in statuses.values() if reason != "checked"
    )
    coverage = {
        "collection_mode": "bounded_full_catalog_scan" if scan_all else "strict_catalog_prefix",
        "sampling_order": (
            "epoch-sha256-theorem-name weighted membership scatter v1"
            if scan_all
            else "frozen dependency-ordered catalog prefix"
        ),
        "enrolled_theorem_count": len(epoch.theorems),
        "enrolled_membership_counts": _catalog_memberships(epoch.theorems),
        "eligible_theorem_count": len(decisions_eligible),
        "eligible_membership_counts": _catalog_memberships(tuple(decisions_eligible)),
        "resource_eligible_theorem_count": len(resource_eligible),
        "resource_eligible_membership_counts": _catalog_memberships(tuple(resource_eligible)),
        "replay_safe_theorem_count": len(replay_safe),
        "replay_safe_membership_counts": _catalog_memberships(tuple(replay_safe)),
        "requested_route_limit": requested_limit,
        "selected_route_count": len(attempted),
        "selected_membership_counts": _catalog_memberships(tuple(attempted)),
        "checked_route_count": len(results),
        "checked_membership_counts": _catalog_memberships(checked_theorems),
        "skipped_theorem_count": len(skipped_theorems),
        "skipped_membership_counts": _catalog_memberships(skipped_theorems),
        "skipped_reason_counts": dict(sorted(skipped_reasons.items())),
        "failed_routes": failures,
        "max_route_decisions": max_decisions,
        "max_statement_utf8_bytes": MAX_CATALOG_STATEMENT_BYTES,
        "max_prerequisite_closure_tactics": MAX_CATALOG_DEPENDENCY_CLOSURE_TACTICS,
        "max_prerequisite_closure_statement_bytes": (
            MAX_CATALOG_DEPENDENCY_CLOSURE_STATEMENT_BYTES
        ),
        "automatic_prerequisite_membership": "stable_only",
        "max_route_evidence_bytes": MAX_CATALOG_ROUTE_EVIDENCE_BYTES,
        "max_total_evidence_bytes": MAX_CATALOG_TOTAL_EVIDENCE_BYTES,
        "retained_evidence_bytes": evidence_bytes,
        "whole_run_tactic_budget": max_total_tactics,
        "attempted_tactic_decisions": attempted_tactics,
        "attempted_proof_state_reservations": attempted_tactics + len(attempted),
    }
    if (
        len(results) + len(skipped_theorems) != len(epoch.theorems)
        or sum(skipped_reasons.values()) != len(skipped_theorems)
        or attempted_tactics > max_total_tactics
        or evidence_bytes > MAX_CATALOG_TOTAL_EVIDENCE_BYTES
    ):
        raise HydraDevelopmentError("whole-catalog coverage failed its exact accounting boundary")
    return CatalogCollection(tuple(results), coverage)


def _catalog_optimizations(
    epoch: HydraEpoch,
    *,
    prefix_count: int,
    theorem_names: tuple[str, ...],
) -> tuple[OptimizationResult, ...]:
    """Preserve the strict, dependency-ordered historical collection API."""

    return _collect_catalog_routes(
        epoch,
        prefix_count=prefix_count,
        theorem_names=theorem_names,
    ).results


def prepare(
    *,
    catalog_limit: int = 0,
    catalog_theorems: tuple[str, ...] = (),
    catalog_all: bool = False,
    catalog_max_decisions: int = MAX_CATALOG_ROUTE_DECISIONS,
    catalog_max_tactics: int = MAX_CATALOG_TOTAL_TACTICS,
) -> tuple[HydraEpoch, VerifiedCurriculum, dict[str, object]]:
    """Return one checked, deterministic development epoch and full manifest."""

    epoch, dag_audit = _audited_epoch()
    optimization = _optimization(epoch)
    discovery = _discovery(epoch)
    if not discovery.checked:
        raise HydraDevelopmentError("reviewed teacher-oracle candidate was not independently checked")
    collection = _collect_catalog_routes(
        epoch,
        prefix_count=catalog_limit,
        theorem_names=catalog_theorems,
        scan_all=catalog_all,
        max_decisions=catalog_max_decisions,
        max_total_tactics=catalog_max_tactics,
    )
    additional = collection.results
    curriculum = build_verified_curriculum(
        epoch,
        optimization,
        discovery,
        additional_optimizations=additional,
    )
    manifest = curriculum.manifest()
    manifest["version"] = epoch.version
    manifest["edition_identity_sha256"] = epoch.edition_identity_sha256
    manifest["theorem_dag_sha256"] = epoch.theorem_dag_sha256
    manifest["reviewed_definition_dag_sha256"] = epoch.reviewed_definition_dag_sha256
    manifest["dag_audit"] = dag_audit
    manifest["optimization"] = optimization.to_dict()
    manifest["discovery"] = discovery.to_dict()
    manifest["catalog_training"] = {
        **collection.coverage,
        "theorem_names": [item.theorem_name for item in additional],
        "total_tactic_decisions": sum(len(item.winner.commands) for item in additional),
        "source": "independently replayed frozen-catalog authored proof routes",
        "model_generated": False,
        "research_claim_eligible": False,
    }
    return epoch, curriculum, manifest


def _write_atomic(path: Path, payload: bytes) -> None:
    if path.is_symlink() or (path.exists() and not path.is_file()):
        raise HydraDevelopmentError("Hydra output refuses symlinks and non-regular artifacts")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as sink:
            sink.write(payload)
            sink.flush()
            os.fsync(sink.fileno())
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise HydraDevelopmentError("Hydra output changed to an unsafe target during publication")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _publish(
    directory: Path,
    *,
    epoch: HydraEpoch,
    curriculum: VerifiedCurriculum,
    manifest: dict[str, object],
    include_graphs: bool,
) -> Path:
    output = directory.expanduser().absolute()
    if output.is_symlink() or (output.exists() and not output.is_dir()):
        raise HydraDevelopmentError("Hydra output directory must be a real dedicated directory")
    output.mkdir(parents=True, exist_ok=True)
    for filename in OUTPUT_FILENAMES:
        target = output / filename
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise HydraDevelopmentError(f"Hydra output artifact {filename!r} is not a regular file")
    payloads = {
        "epoch.json": _strict_json(epoch.to_dict(include_graphs=include_graphs), pretty=True),
        "sft.jsonl": encode_jsonl(curriculum.transitions),
        "preferences.jsonl": encode_jsonl(curriculum.preferences),
        "discovery.jsonl": encode_jsonl(curriculum.discoveries),
        "manifest.json": _strict_json(manifest, pretty=True),
    }
    for filename in OUTPUT_FILENAMES:
        _write_atomic(output / filename, payloads[filename])
    return output


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=REPOSITORY_ROOT / "_deploy" / "hydra",
        metavar="PATH",
        help="dedicated deterministic development-artifact directory",
    )
    parser.add_argument(
        "--include-graphs",
        action="store_true",
        help="include all authenticated checked theorems and reviewed definitions in epoch.json",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="independently verify the entire pipeline without writing any output",
    )
    parser.add_argument(
        "--catalog-limit",
        type=int,
        default=0,
        metavar="N",
        help=(
            "also independently replay N bounded frozen-catalog proof routes "
            f"(maximum {MAX_ADDITIONAL_CATALOG_THEOREMS}); with --catalog-all, "
            "sample across the complete Alpha/Stable theorem DAG"
        ),
    )
    parser.add_argument(
        "--catalog-all",
        action="store_true",
        help=(
            "audit the entire frozen theorem DAG and deterministically sample "
            "checked Alpha/Stable routes; report every bounded skip explicitly"
        ),
    )
    parser.add_argument(
        "--catalog-max-decisions",
        type=int,
        default=MAX_CATALOG_ROUTE_DECISIONS,
        metavar="N",
        help=(
            "maximum complete tactic decisions per catalog proof "
            f"(1–{MAX_CATALOG_ROUTE_DECISIONS})"
        ),
    )
    parser.add_argument(
        "--catalog-max-tactics",
        type=int,
        default=MAX_CATALOG_TOTAL_TACTICS,
        metavar="N",
        help=(
            "whole-run tactic/state/candidate reservation, including failed "
            f"routes (1–{MAX_CATALOG_TOTAL_TACTICS})"
        ),
    )
    parser.add_argument(
        "--catalog-theorem",
        action="append",
        default=[],
        metavar="NAME",
        help="also replay one named checked Stable or Alpha theorem (repeatable)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    arguments = parser.parse_args(argv)
    try:
        epoch, curriculum, manifest = prepare(
            catalog_limit=arguments.catalog_limit,
            catalog_theorems=tuple(arguments.catalog_theorem),
            catalog_all=arguments.catalog_all,
            catalog_max_decisions=arguments.catalog_max_decisions,
            catalog_max_tactics=arguments.catalog_max_tactics,
        )
        destination = None
        if not arguments.check:
            destination = _publish(
                arguments.output_dir,
                epoch=epoch,
                curriculum=curriculum,
                manifest=manifest,
                include_graphs=arguments.include_graphs,
            )
    except (
        CampaignDagError,
        DefinitionGraphError,
        HydraCurriculumError,
        HydraDevelopmentError,
        HydraEpochError,
        HydraRunnerError,
        TeacherOraclePilotError,
        OSError,
        TypeError,
        ValueError,
    ) as error:
        print(f"prepare-peano-hydra: {' '.join(str(error).split())}", file=sys.stderr)
        return 2
    summary = {
        "version": epoch.version,
        "epoch_sha256": epoch.epoch_sha256,
        "checked_theorems": len(epoch.theorems),
        "reviewed_definitions": len(epoch.definitions),
        "sft_rows": len(curriculum.transitions),
        "duplicate_transitions_removed": curriculum.duplicate_transitions_removed,
        "preference_rows": len(curriculum.preferences),
        "checked_discoveries": sum(row["kernel_checked"] for row in curriculum.discoveries),
        "tactic_decisions_saved": manifest["optimization"]["tactic_decisions_saved"],
        "checked_catalog_routes": manifest["catalog_training"]["checked_route_count"],
        "checked_catalog_alpha_routes": (
            manifest["catalog_training"]["checked_membership_counts"]["alpha_only"]
        ),
        "eligible_catalog_routes": manifest["catalog_training"]["eligible_theorem_count"],
        "skipped_catalog_routes": manifest["catalog_training"]["skipped_theorem_count"],
        "development_only": True,
        "output_dir": None if destination is None else str(destination),
    }
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
