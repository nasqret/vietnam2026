"""Deterministic post-training rows derived only from kernel-checked proofs.

This is a development corpus, not a benchmark or an attestation that a model
generated a theorem.  Positive rows come from an original-goal QED replay;
preference rows compare two separately checked complete routes to the same
theorem.  The checked theorem DAG and the reviewed definition DAG stay frozen
and are never modified by this module.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import json

from peano_lab.batch import BatchResult
from peano_lab.kernel.formulas import ParseError, parse_formula_with_names, pretty_formula
from training.peano_hydra.development import DiscoveryResult, OptimizationResult
from training.peano_hydra.epoch import HydraEpoch
from training.peano_hydra.runner import HydraRunResult
from training.peano_policy.contract import prompt_environment
from training.peano_policy.prompt import (
    COMPLETION_SUFFIX,
    CapabilityIdentity,
    ProofExample,
    render_prompt,
)
from training.peano_policy.search import state_sha256


CURRICULUM_SCHEMA = "peano-hydra-verified-curriculum-v1"
TRANSITION_SCHEMA = "peano-hydra-verified-transition-v1"
PREFERENCE_SCHEMA = "peano-hydra-verified-preference-v1"
MAX_TRANSITIONS = 16_384
MAX_PROMPT_BYTES = 1_000_000
MAX_DATASET_BYTES = 64 * 1024 * 1024


class HydraCurriculumError(ValueError):
    """A candidate training row lacks complete independently checked evidence."""


def _canonical(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise HydraCurriculumError(f"curriculum evidence is not strict JSON: {error}") from None


def _digest(value: object) -> str:
    return hashlib.sha256(_canonical(value)).hexdigest()


def _lineage(epoch: HydraEpoch, names: tuple[str, ...], *, candidate: str | None = None) -> str:
    """Keep entire connected theorem-DAG components in a single data split."""

    adjacency: dict[str, set[str]] = {item.name: set() for item in epoch.theorems}
    for theorem in epoch.theorems:
        for dependency in theorem.dependencies:
            adjacency[theorem.name].add(dependency)
            adjacency[dependency].add(theorem.name)
    seen: set[str] = set()
    pending = list(names)
    while pending:
        name = pending.pop()
        if name in seen:
            continue
        if name not in adjacency:
            raise HydraCurriculumError("training lineage escaped its frozen theorem DAG")
        seen.add(name)
        pending.extend(sorted(adjacency[name] - seen))
    if not seen:
        if type(candidate) is not str or not candidate:
            raise HydraCurriculumError("an independent candidate lineage needs its exact theorem")
        return _digest({"kind": "unadmitted-candidate", "statement": candidate})
    return _digest({"kind": "checked-theorem-component", "members": sorted(seen)})


def _lineage_index(epoch: HydraEpoch) -> dict[str, str]:
    """Hash each frozen undirected theorem component once per whole corpus."""

    adjacency: dict[str, set[str]] = {item.name: set() for item in epoch.theorems}
    for theorem in epoch.theorems:
        for dependency in theorem.dependencies:
            adjacency[theorem.name].add(dependency)
            adjacency[dependency].add(theorem.name)
    lineages: dict[str, str] = {}
    for theorem in epoch.theorems:
        if theorem.name in lineages:
            continue
        component: set[str] = set()
        pending = [theorem.name]
        while pending:
            name = pending.pop()
            if name in component:
                continue
            component.add(name)
            pending.extend(adjacency[name] - component)
        digest = _digest(
            {"kind": "checked-theorem-component", "members": sorted(component)}
        )
        lineages.update((name, digest) for name in component)
    if len(lineages) != len(epoch.theorems):
        raise HydraCurriculumError("checked theorem lineage index escaped its frozen DAG")
    return lineages


def _split(epoch: HydraEpoch, lineage: str) -> str:
    digest = hashlib.sha256(f"{epoch.epoch_sha256}:{lineage}".encode("ascii")).digest()
    return "dev" if int.from_bytes(digest[:8], "big") % 10 == 0 else "train"


def _canonical_statement(statement: str) -> str:
    try:
        formula, names = parse_formula_with_names(statement)
    except (ParseError, RecursionError, TypeError, ValueError) as error:
        raise HydraCurriculumError(f"training theorem has an invalid original statement: {error}") from None
    if names:
        raise HydraCurriculumError("training theorem must preserve its original closed statement")
    return pretty_formula(formula, list(names))


def _catalog_result(epoch: HydraEpoch, result: OptimizationResult) -> None:
    target = epoch.theorem(result.theorem_name)
    if target is None:
        raise HydraCurriculumError("optimization training proof is not in the frozen theorem DAG")
    canonical = _canonical_statement(target.statement)
    if (
        result.theorem != canonical
        or result.winner.theorem != canonical
        or result.baseline.theorem != canonical
    ):
        raise HydraCurriculumError("optimization training proof changed its exact enrolled statement")


def _checked_replay(run: HydraRunResult, *, epoch: HydraEpoch) -> BatchResult:
    if type(run) is not HydraRunResult or not run.proved or run.replay is None:
        raise HydraCurriculumError("post-training positives require an independently checked proof")
    replay = run.replay
    if (
        replay.status != "proved"
        or replay.kernel_checked is not True
        or replay.theorem != run.theorem
        or replay.surface != epoch.surface_label
        or replay.environment_sha256 != run.environment.get("environment_sha256")
        or replay.failed_tactics
        or replay.goals
        or replay.proof_nodes != run.search.certificate_nodes
        or type(replay.trace) is not tuple
        or len(replay.trace) != len(run.commands) + 1
        or type(replay.trace[-1]) is not dict
        or replay.trace[-1].get("qed") is not True
        or replay.trace[-1].get("theorem") != run.theorem
    ):
        raise HydraCurriculumError("post-training positive lost its frozen original-goal QED replay")
    return replay


def _transition_rows(
    *,
    epoch: HydraEpoch,
    theorem_name: str,
    run: HydraRunResult,
    track: str,
    source: str,
    lineage: str,
) -> tuple[dict[str, object], ...]:
    replay = _checked_replay(run, epoch=epoch)
    capabilities = run.environment.get("capabilities")
    identity = CapabilityIdentity.from_record(capabilities)
    environment = prompt_environment(False, identity)
    if environment.sha256 != run.environment.get("environment_sha256"):
        raise HydraCurriculumError("training prompt authority differs from its checked proof")
    rows: list[dict[str, object]] = []
    for index, row in enumerate(replay.trace[:-1], 1):
        if type(row) is not dict or row.get("status") != "ok" or row.get("error") is not None:
            raise HydraCurriculumError("positive training transition must be one successful trace step")
        if row.get("step") != index or row.get("session") != replay.session_id:
            raise HydraCurriculumError("positive training trace lost its exact step identity")
        before = row.get("goals_before")
        after = row.get("goals_after")
        focus = row.get("focus")
        tactic = row.get("tactic")
        if (
            type(before) is not list
            or not before
            or type(after) is not list
            or type(focus) is not int
            or not 0 <= focus < len(before)
            or type(tactic) is not str
            or tactic != run.commands[index - 1]
        ):
            raise HydraCurriculumError("positive training row changed its checked state or action")
        goals = tuple(before)
        state = state_sha256(goals)
        prompt = render_prompt(goals=goals, focus=focus, environment=environment)
        if len(prompt.encode("utf-8")) > MAX_PROMPT_BYTES:
            raise HydraCurriculumError("training prompt exceeds its explicit byte bound")
        completion = tactic + COMPLETION_SUFFIX
        example = ProofExample(
            example_id=f"{theorem_name}:{index}:{state[:16]}",
            prompt=prompt,
            completion=completion,
            environment_sha256=environment.sha256,
        )
        rows.append(
            {
                "schema": TRANSITION_SCHEMA,
                "epoch_sha256": epoch.epoch_sha256,
                "theorem_name": theorem_name,
                "theorem": run.theorem,
                "track": track,
                "source": source,
                "lineage_sha256": lineage,
                "split": _split(epoch, lineage),
                "step": index,
                "state_sha256": state,
                "goals_before": before,
                "goals_after": after,
                "focus": focus,
                "action": example.tactic,
                "action_head": example.tactic.split(" ", 1)[0],
                "prompt": example.prompt,
                "completion": example.completion,
                "environment_sha256": example.environment_sha256,
                "commands_sha256": run.commands_sha256,
                "proof_nodes": replay.proof_nodes,
                "kernel_checked": True,
                "research_claim_eligible": False,
            }
        )
    return tuple(rows)


def _preferences(
    epoch: HydraEpoch,
    optimization: OptimizationResult,
    transitions: tuple[dict[str, object], ...],
    lineage: str,
) -> tuple[dict[str, object], ...]:
    if optimization.baseline is optimization.winner:
        return ()
    baseline = _checked_replay(optimization.baseline, epoch=epoch)
    winner = _checked_replay(optimization.winner, epoch=epoch)
    if len(optimization.winner.commands) >= len(optimization.baseline.commands):
        return ()
    first_baseline = baseline.trace[0]
    first_winner = winner.trace[0]
    if (
        first_baseline.get("goals_before") != first_winner.get("goals_before")
        or first_baseline.get("focus") != first_winner.get("focus")
        or first_baseline.get("tactic") == first_winner.get("tactic")
    ):
        return ()
    root = transitions[0]
    chosen = first_winner["tactic"] + COMPLETION_SUFFIX
    rejected = first_baseline["tactic"] + COMPLETION_SUFFIX
    ProofExample(
        example_id=f"preference:{optimization.theorem_name}:chosen",
        prompt=root["prompt"],
        completion=chosen,
        environment_sha256=root["environment_sha256"],
    )
    ProofExample(
        example_id=f"preference:{optimization.theorem_name}:rejected",
        prompt=root["prompt"],
        completion=rejected,
        environment_sha256=root["environment_sha256"],
    )
    return (
        {
            "schema": PREFERENCE_SCHEMA,
            "epoch_sha256": epoch.epoch_sha256,
            "theorem_name": optimization.theorem_name,
            "theorem": optimization.theorem,
            "lineage_sha256": lineage,
            "split": _split(epoch, lineage),
            "state_sha256": root["state_sha256"],
            "prompt": root["prompt"],
            "chosen": chosen,
            "rejected": rejected,
            "chosen_remaining_tactics": len(optimization.winner.commands),
            "rejected_remaining_tactics": len(optimization.baseline.commands),
            "chosen_proof_nodes": optimization.winner.search.certificate_nodes,
            "rejected_proof_nodes": optimization.baseline.search.certificate_nodes,
            "chosen_kernel_checked": True,
            "rejected_kernel_checked": True,
            "ranking": "shorter independently checked complete original-goal route",
            "research_claim_eligible": False,
        },
    )


def encode_jsonl(rows: tuple[dict[str, object], ...]) -> bytes:
    """Encode complete strict-JSON records without lossy truncation."""

    if type(rows) is not tuple or len(rows) > MAX_TRANSITIONS:
        raise HydraCurriculumError("dataset exceeds its exact row-count boundary")
    payload = b"".join(_canonical(row) + b"\n" for row in rows)
    if len(payload) > MAX_DATASET_BYTES:
        raise HydraCurriculumError("dataset exceeds its explicit aggregate byte boundary")
    return payload


@dataclass(frozen=True, slots=True)
class VerifiedCurriculum:
    """Deterministic, lineage-separated development-only proof evidence."""

    epoch_sha256: str
    transitions: tuple[dict[str, object], ...]
    preferences: tuple[dict[str, object], ...]
    discoveries: tuple[dict[str, object], ...]
    duplicate_transitions_removed: int = 0

    def manifest(self) -> dict[str, object]:
        sft = encode_jsonl(self.transitions)
        preferences = encode_jsonl(self.preferences)
        discoveries = encode_jsonl(self.discoveries)
        heads = Counter(row["action_head"] for row in self.transitions)
        splits = Counter(row["split"] for row in self.transitions)
        lineages = {
            name: sorted(
                {
                    row["lineage_sha256"]
                    for row in self.transitions
                    if row["split"] == name
                }
            )
            for name in ("train", "dev")
        }
        if set(lineages["train"]) & set(lineages["dev"]):
            raise HydraCurriculumError("one theorem lineage leaked across training and development")
        return {
            "schema": CURRICULUM_SCHEMA,
            "epoch_sha256": self.epoch_sha256,
            "development_only": True,
            "research_claim_eligible": False,
            "sealed_benchmark": False,
            "model_trained": False,
            "alpha_admitted": False,
            "proof_optimization_claim": "best independently checked observed route only",
            "discovery_claim": "kernel-checked unadmitted candidate only; no semantic novelty claim",
            "historical_model_authority": {
                "model": "Qwen3-1.7B historical model-v3 adapter",
                "frozen_checked_theorem_count": 247,
                "silently_expanded": False,
            },
            "files": {
                "sft.jsonl": {
                    "rows": len(self.transitions),
                    "bytes": len(sft),
                    "sha256": hashlib.sha256(sft).hexdigest(),
                },
                "preferences.jsonl": {
                    "rows": len(self.preferences),
                    "bytes": len(preferences),
                    "sha256": hashlib.sha256(preferences).hexdigest(),
                },
                "discovery.jsonl": {
                    "rows": len(self.discoveries),
                    "bytes": len(discoveries),
                    "sha256": hashlib.sha256(discoveries).hexdigest(),
                },
            },
            "transition_count": len(self.transitions),
            "duplicate_transitions_removed": self.duplicate_transitions_removed,
            "preference_count": len(self.preferences),
            "discovery_count": len(self.discoveries),
            "tactic_head_counts": dict(sorted(heads.items())),
            "split_transition_counts": {
                "train": splits.get("train", 0),
                "dev": splits.get("dev", 0),
            },
            "split_lineages": lineages,
            "max_prompt_utf8_bytes": max(
                (len(row["prompt"].encode("utf-8")) for row in self.transitions),
                default=0,
            ),
            "open_research_gates": [
                "H0 provider attestation and raw-call evidence",
                "H1 reviewed sealed matched-compute benchmark",
                "versioned structured macro protocol",
                "independent external-provider audit",
            ],
        }


def build_verified_curriculum(
    epoch: HydraEpoch,
    optimization: OptimizationResult,
    discovery: DiscoveryResult,
    *,
    additional_optimizations: tuple[OptimizationResult, ...] = (),
) -> VerifiedCurriculum:
    """Publish only positive complete-QED transitions under one frozen epoch."""

    if type(epoch) is not HydraEpoch:
        raise TypeError("curriculum requires one exact frozen HydraEpoch")
    if type(optimization) is not OptimizationResult:
        raise TypeError("curriculum requires one exact checked OptimizationResult")
    if type(discovery) is not DiscoveryResult:
        raise TypeError("curriculum requires one exact DiscoveryResult")
    if type(additional_optimizations) is not tuple or not all(
        type(item) is OptimizationResult for item in additional_optimizations
    ):
        raise TypeError("additional checked catalog routes must be an exact tuple")
    if optimization.epoch_sha256 != epoch.epoch_sha256:
        raise HydraCurriculumError("optimization proof does not belong to the frozen epoch")
    if discovery.epoch_sha256 != epoch.epoch_sha256:
        raise HydraCurriculumError("discovery proof does not belong to the frozen epoch")
    _catalog_result(epoch, optimization)
    if discovery.result.theorem != _canonical_statement(discovery.proposal.theorem):
        raise HydraCurriculumError("discovery training proof changed its exact proposed statement")
    lineages = _lineage_index(epoch)
    optimization_lineage = lineages[optimization.theorem_name]
    optimization_rows = _transition_rows(
        epoch=epoch,
        theorem_name=optimization.theorem_name,
        run=optimization.winner,
        track="proof_optimization",
        source="independently_checked_recorded_route",
        lineage=optimization_lineage,
    )
    rows = list(optimization_rows)
    preferences = list(
        _preferences(epoch, optimization, optimization_rows, optimization_lineage)
    )
    for additional in additional_optimizations:
        if additional.epoch_sha256 != epoch.epoch_sha256:
            raise HydraCurriculumError("additional catalog proof does not belong to the frozen epoch")
        _catalog_result(epoch, additional)
        target = epoch.theorem(additional.theorem_name)
        if additional.winner.environment["capabilities"]["allowed_theorems"] != sorted(
            target.dependencies
        ):
            raise HydraCurriculumError(
                "additional catalog proof changed its exact checked direct prerequisites"
            )
        lineage = lineages[target.name]
        route_rows = _transition_rows(
            epoch=epoch,
            theorem_name=target.name,
            run=additional.winner,
            track="checked_catalog_replay",
            source="independently_checked_frozen_catalog_script",
            lineage=lineage,
        )
        rows.extend(route_rows)
        preferences.extend(_preferences(epoch, additional, route_rows, lineage))
    if discovery.checked:
        discovery_lineage = _lineage(
            epoch,
            discovery.proposal.dependencies,
            candidate=discovery.proposal.theorem,
        )
        rows.extend(
            _transition_rows(
                epoch=epoch,
                theorem_name=discovery.proposal.name,
                run=discovery.result,
                track="proof_discovery",
                source=discovery.proposal.source,
                lineage=discovery_lineage,
            )
        )
    if len(rows) > MAX_TRANSITIONS:
        raise HydraCurriculumError("post-training transitions exceed their reviewed bound")
    unique: dict[tuple[str, str, str, str, str], dict[str, object]] = {}
    deduplicated: list[dict[str, object]] = []
    duplicates_removed = 0
    for row in rows:
        key = (
            row["epoch_sha256"],
            row["lineage_sha256"],
            row["state_sha256"],
            row["action"],
            row["environment_sha256"],
        )
        earlier = unique.get(key)
        if earlier is not None:
            if (
                earlier["goals_before"] != row["goals_before"]
                or earlier["goals_after"] != row["goals_after"]
                or earlier["focus"] != row["focus"]
                or earlier["prompt"] != row["prompt"]
                or earlier["completion"] != row["completion"]
            ):
                raise HydraCurriculumError(
                    "identical proof state/action changed its independently checked transition"
                )
            duplicates_removed += 1
            continue
        unique[key] = row
        deduplicated.append(row)
    result = VerifiedCurriculum(
        epoch.epoch_sha256,
        tuple(deduplicated),
        tuple(preferences),
        (discovery.to_dict(),),
        duplicates_removed,
    )
    result.manifest()
    return result


__all__ = [
    "CURRICULUM_SCHEMA",
    "HydraCurriculumError",
    "PREFERENCE_SCHEMA",
    "TRANSITION_SCHEMA",
    "VerifiedCurriculum",
    "build_verified_curriculum",
    "encode_jsonl",
]
