"""Bounded TRAIN-only proof harvesting for an explicit next training round.

Candidate flags and successful-looking logs are never proof authority.
Each admitted candidate is replayed against its registered original goal in
a fresh owned native worker. Exported rows still require the lineage/review
and source-admission gates before a later model run. There is no hidden model
generation, automatic training, retry, benchmark access or theorem admission.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import resource
import sys

from training.peano_hydra.scaling_experiment import (
    canonical, digest, execution_source_inventory, integer, keys, require, sha,
)


ROOT = Path(__file__).absolute().parents[2]
ROUND_SCHEMA = "peano-hydra-train-only-self-training-round-v1"
CANDIDATE_SCHEMA = "peano-hydra-untrusted-training-proof-candidate-v1"
WORKER_SCHEMA = "peano-hydra-fresh-training-proof-replay-v1"
HARVEST_SCHEMA = "peano-hydra-train-only-verified-harvest-v1"
MAX_GOALS = 64
MAX_CANDIDATES = 64
MAX_COMMANDS = 24
MAX_CANDIDATE_BYTES = 96 * 1024
MAX_ROUND_TRANSITIONS = MAX_CANDIDATES * MAX_COMMANDS
MAX_ACCEPTED_BYTES = 3 * 1024**2
WORKER_LIMITS = {"cpu_seconds": 30, "wall_seconds": 45,
                 "rss_bytes": 1024**3, "output_bytes": 1024**2}
_GOAL_FIELDS = {"goal_id", "source", "statement", "statement_sha256",
                "family", "lineage_sha256", "split"}


def _text(value, label, maximum):
    require(type(value) is str and 1 <= len(value.encode("utf-8")) <= maximum
            and "\x00" not in value, label + " exceeds its text bound")
    return value


def _goal(record):
    keys(record, _GOAL_FIELDS, "registered training goal")
    require(record["split"] == "train", "self-training cannot access DEV, TEST or quarantine")
    for field in ("goal_id", "family"):
        _text(record[field], field, 128)
        require(record[field].replace("_", "").replace("-", "").isalnum(),
                "unsafe training goal identifier")
    for field in ("source", "statement"):
        _text(record[field], field, 16_384)
    sha(record["lineage_sha256"], "registered lineage")
    sha(record["statement_sha256"], "registered statement")
    require(hashlib.sha256(record["statement"].encode()).hexdigest() == record["statement_sha256"],
            "registered original statement hash differs")
    return dict(record)


def build_round_plan(*, round_id: str, parent_dataset_sha256: str,
                     lineage_proposal_sha256: str, epoch_sha256: str,
                     authority_sha256: str, model_origin_sha256: str,
                     execution_sources_sha256: str, goals: list[dict],
                     excluded_statement_sha256s: list[str],
                     excluded_lineage_sha256s: list[str],
                     max_candidates: int = 64) -> dict:
    """Declare TRAIN-only targets before proposal generation; no approval."""
    _text(round_id, "round ID", 96)
    require(round_id.replace("-", "").replace("_", "").isalnum(), "unsafe round ID")
    pins = {
        "parent_dataset_sha256": parent_dataset_sha256,
        "lineage_proposal_sha256": lineage_proposal_sha256,
        "epoch_sha256": epoch_sha256, "authority_sha256": authority_sha256,
        "model_origin_sha256": model_origin_sha256,
        "execution_sources_sha256": execution_sources_sha256,
    }
    for label, value in pins.items():
        sha(value, label)
    integer(max_candidates, "round candidate limit", 1, MAX_CANDIDATES)
    require(type(goals) is list and 1 <= len(goals) <= MAX_GOALS, "round goal count exceeds bound")
    exclusions = {}
    for label, values in (("excluded_statement_sha256s", excluded_statement_sha256s),
                          ("excluded_lineage_sha256s", excluded_lineage_sha256s)):
        require(type(values) is list and len(values) <= 32_768, "exclusion inventory exceeds bound")
        for value in values:
            sha(value, label)
        require(len(values) == len(set(values)), "duplicate exclusion declaration")
        exclusions[label] = sorted(values)
    clean = [_goal(g) for g in goals]
    require(len({g["goal_id"] for g in clean}) == len(clean), "duplicate training goal ID")
    require(len({g["statement_sha256"] for g in clean}) == len(clean), "duplicate training statement")
    for g in clean:
        require(g["statement_sha256"] not in exclusions["excluded_statement_sha256s"]
                and g["lineage_sha256"] not in exclusions["excluded_lineage_sha256s"],
                "self-training target intersects held-out/quarantined evidence")
    body = {
        "schema": ROUND_SCHEMA, "round_id": round_id, **pins, **exclusions,
        "goals": clean, "max_candidates": max_candidates, "max_commands": MAX_COMMANDS,
        "worker_limits": dict(WORKER_LIMITS),
        "max_total_replay_cpu_seconds": max_candidates * WORKER_LIMITS["cpu_seconds"],
        "max_total_replay_wall_seconds": max_candidates * WORKER_LIMITS["wall_seconds"],
        "state_action_deduplication": "epoch+authority+lineage+full-state+action",
        "invalid_candidates_are_non_theorem_labels": False,
        "candidate_generation_authorized": False, "training_authorized": False,
        "model_generation_attested": False, "research_claim_eligible": False,
        "automatic_retry": False, "resume": False,
        "next_stage": "review and independently admit a new immutable curriculum; never append old data",
    }
    return {**body, "round_sha256": digest(body)}


def validate_round_plan(plan):
    require(type(plan) is dict, "round plan must be an object")
    fields = ("round_id", "parent_dataset_sha256", "lineage_proposal_sha256",
              "epoch_sha256", "authority_sha256", "model_origin_sha256",
              "execution_sources_sha256", "goals", "excluded_statement_sha256s",
              "excluded_lineage_sha256s", "max_candidates")
    try:
        expected = build_round_plan(**{k: plan[k] for k in fields})
    except KeyError as error:
        raise ValueError("round plan lost required fields") from error
    require(canonical(expected) == canonical(plan), "round plan changed its exact contract")
    return expected


def validate_candidate(plan, candidate):
    plan = validate_round_plan(plan)
    keys(candidate, {"schema", "round_sha256", "goal_id", "commands", "commands_sha256",
                     "model_origin_sha256", "proposal_evidence_sha256", "provider_kind"}, "candidate")
    require(candidate["schema"] == CANDIDATE_SCHEMA and candidate["round_sha256"] == plan["round_sha256"],
            "candidate changed its round")
    require(candidate["model_origin_sha256"] == plan["model_origin_sha256"],
            "candidate changed its declared model origin")
    require(candidate["provider_kind"] in ("model-proposal", "authored-test-fixture"),
            "unknown candidate provider kind")
    sha(candidate["proposal_evidence_sha256"], "proposal evidence")
    goal = next((g for g in plan["goals"] if g["goal_id"] == candidate["goal_id"]), None)
    require(goal is not None, "candidate is not a registered TRAIN goal")
    commands = candidate["commands"]
    require(type(commands) is list and 1 <= len(commands) <= MAX_COMMANDS,
            "candidate proof length exceeds its bound")
    for command in commands:
        _text(command, "primitive command", 4096)
        require("\n" not in command and "\r" not in command, "candidate commands must be single primitives")
    require(candidate["commands_sha256"] == digest(commands), "candidate commands digest differs")
    require(len(canonical(candidate)) <= MAX_CANDIDATE_BYTES, "candidate exceeds its byte bound")
    return dict(goal)


def _worker_request(plan, candidate):
    goal = validate_candidate(plan, candidate)
    return {
        "schema": WORKER_SCHEMA, "round_sha256": plan["round_sha256"],
        "candidate_sha256": digest(candidate), "epoch_sha256": plan["epoch_sha256"],
        "authority_sha256": plan["authority_sha256"],
        "execution_sources_sha256": plan["execution_sources_sha256"],
        "goal": goal, "commands": list(candidate["commands"]),
        "excluded_statement_sha256s": plan["excluded_statement_sha256s"],
    }


def _checked_transitions(rows, request, candidate):
    """Check worker trace linkage without replacing the native proof replay."""
    previous_after = None
    for index, row in enumerate(rows, 1):
        require(type(row) is dict and row.get("step") == index and type(row["step"]) is int
                and row.get("action") == candidate["commands"][index - 1]
                and row.get("track") == "verified_training_candidate"
                and row.get("source") == "fresh_original_goal_native_replayed_candidate",
                "worker positive row differs from its exact replayed command")
        before, after = row.get("goals_before"), row.get("goals_after")
        require(type(before) is list and before and len(before) <= 64 and type(after) is list
                and len(after) <= 64 and all(type(g) is str for g in (*before, *after)),
                "worker positive row lost its complete native state")
        require(row.get("state_sha256") == digest(before), "worker state hash differs")
        require(previous_after is None or before == previous_after, "worker native trace is disconnected")
        previous_after = after
    require(not rows or previous_after == [], "worker trace did not finish the original goal")


def native_replay_worker(request):
    """Internal isolated worker; the parent enforces wall/RSS/descendant guards."""
    require(sys.flags.isolated and sys.dont_write_bytecode and sys.pycache_prefix == "/dev/null",
            "native harvesting requires isolated uncached Python")
    require(resource.getrlimit(resource.RLIMIT_CPU) == (30, 31), "native harvesting lacks its exact CPU guard")
    require(not {"torch", "transformers", "peft", "tokenizers"} & set(sys.modules),
            "harvesting cannot import model frameworks")
    keys(request, {"schema", "round_sha256", "candidate_sha256", "epoch_sha256",
                   "authority_sha256", "execution_sources_sha256", "goal", "commands",
                   "excluded_statement_sha256s"}, "native request")
    require(request["schema"] == WORKER_SCHEMA, "unknown native worker schema")
    for field in ("round_sha256", "candidate_sha256", "epoch_sha256", "authority_sha256"):
        sha(request[field], field)
    require(digest(execution_source_inventory()) == request["execution_sources_sha256"],
            "native harvesting source changed from its round plan")
    goal = _goal(request["goal"])
    commands = request["commands"]
    require(type(commands) is list and 1 <= len(commands) <= MAX_COMMANDS, "unbounded native route")
    for command in commands:
        _text(command, "native command", 4096)
    require(type(request["excluded_statement_sha256s"]) is list
            and len(request["excluded_statement_sha256s"]) <= 32_768, "invalid exclusion set")
    for value in request["excluded_statement_sha256s"]:
        sha(value, "excluded statement")
    from peano_lab.batch import run_proof
    from training.peano_hydra import composition as native
    from training.peano_hydra.epoch import freeze_epoch
    from training.peano_hydra.posttrain import _goal_target
    from training.peano_policy.authority import validate_authority_tactic
    epoch = freeze_epoch(ROOT)
    require(epoch.epoch_sha256 == request["epoch_sha256"], "native harvesting changed its frozen epoch")
    caps, environment, authority, _, _ = native._authority(epoch, native.COMPOSITION_PROFILE)
    require(digest(authority) == request["authority_sha256"], "native harvesting changed authority")
    route = {
        "name": goal["goal_id"], "family": goal["family"], "split": "train",
        "lineage_sha256": goal["lineage_sha256"], "source": goal["source"],
        "statement": goal["statement"], "statement_sha256": goal["statement_sha256"],
        "commands": commands, "commands_sha256": digest(commands),
    }
    base = {
        "schema": WORKER_SCHEMA, "round_sha256": request["round_sha256"],
        "candidate_sha256": request["candidate_sha256"],
        "epoch_sha256": epoch.epoch_sha256, "authority_sha256": request["authority_sha256"],
        "goal_id": goal["goal_id"], "commands_sha256": digest(commands),
        "native_replay_performed": False, "model_generation_performed": False,
        "training_authorized": False, "research_claim_eligible": False,
    }
    try:
        for command in commands:
            validate_authority_tactic(command, environment)
    except (TypeError, ValueError) as error:
        return {**base, "status": "rejected-authority", "error": str(error)[:1000],
                "positive_transitions": [], "proof_nodes": None}
    result = run_proof(goal["source"], tuple(commands), request_id=goal["goal_id"],
                       session_id="selftrain-" + request["candidate_sha256"][:24],
                       classical=False, on_error="stop", capabilities=caps,
                       trace_byte_limit=512 * 1024)
    base["native_replay_performed"] = True
    if result.status != "proved" or result.kernel_checked is not True:
        return {**base, "status": "rejected-candidate-not-a-non-theorem-label",
                "error": str(result.error or result.status)[:1000],
                "positive_transitions": [], "proof_nodes": None}
    native._checked_result(result, route, caps=caps, environment_sha256=environment.sha256)
    rows = native._rows(epoch, route, result, environment)
    excluded = set(request["excluded_statement_sha256s"])
    for row in rows:
        for displayed in (*row["goals_before"], *row["goals_after"]):
            target = _goal_target(displayed)
            if target is not None and hashlib.sha256(target.encode()).hexdigest() in excluded:
                return {**base, "status": "quarantined-intermediate-overlap",
                        "error": "candidate intersects a reserved intermediate target",
                        "positive_transitions": [], "proof_nodes": None}
    # Keep the exact native states/actions but do not relabel a proposal as an
    # authored teacher or bypass the existing trainer's source-schema checks.
    transitions = [{**row, "track": "verified_training_candidate",
                    "source": "fresh_original_goal_native_replayed_candidate"} for row in rows]
    require(digest(execution_source_inventory()) == request["execution_sources_sha256"],
            "native harvesting source changed during replay")
    return {**base, "status": "verified-training-candidate", "error": None,
            "positive_transitions": transitions, "proof_nodes": result.proof_nodes,
            "trace_sha256": digest(list(result.trace))}


def harvest_candidates(plan, candidates, *, parent_bundle, parent_readiness_sha256,
                       review, review_sha256, existing_example_sha256s=()):
    """Verify a finite candidate batch sequentially; no provider or GPU calls.

    Inputs are all validated before the first worker. A limited/failed worker
    stays unknown and is not retried. Accepted outputs are candidate material,
    not an admitted trainer dataset or evidence of independent discovery.
    """
    from training.peano_hydra.review_runtime import ProcessLimits, run_bounded, validate_process_record
    plan = validate_round_plan(plan)
    require(type(candidates) is list and len(candidates) <= plan["max_candidates"],
            "candidate batch exceeds the declared round")
    require(type(existing_example_sha256s) in (list, tuple) and len(existing_example_sha256s) <= 131_072,
            "existing example identity inventory exceeds bound")
    known = set()
    for value in existing_example_sha256s:
        known.add(sha(value, "existing example SHA"))
    requests = [_worker_request(plan, candidate) for candidate in candidates]
    from training.peano_hydra.scaling_workflow import authenticate_harvest_parent
    parent = authenticate_harvest_parent(parent_bundle, parent_readiness_sha256=parent_readiness_sha256,
                                        review=review, review_sha256=review_sha256, round_plan=plan)
    require(digest(execution_source_inventory()) == plan["execution_sources_sha256"],
            "harvesting execution source differs from its planned inventory")
    command = (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null",
               str(ROOT / "scripts/prepare_peano_hydra_scaling.py"), "--harvest-worker")
    limits = ProcessLimits(**WORKER_LIMITS)
    seen_candidates, outcomes, accepted = set(), [], []
    accepted_bytes = 0
    for candidate, request in zip(candidates, requests):
        candidate_sha = request["candidate_sha256"]
        proof_key = (candidate["goal_id"], candidate["commands_sha256"])
        if proof_key in seen_candidates:
            outcomes.append({"candidate_sha256": candidate_sha, "status": "duplicate-proof",
                             "worker_started": False})
            continue
        seen_candidates.add(proof_key)
        payload = canonical(request)
        require(digest(execution_source_inventory()) == plan["execution_sources_sha256"],
                "execution source changed before candidate replay")
        process = run_bounded(command, cwd=ROOT, limits=limits, input_bytes=payload)
        audit = {k: v for k, v in process.items() if k not in {"stdout", "stderr", "raw_output_base64"}}
        if process["returncode"] != 0 or process["reason"] != "exited":
            outcomes.append({"candidate_sha256": candidate_sha, "status": "unknown-worker-failure",
                             "worker_started": True, "process": audit})
            continue
        validate_process_record(process, command=command, limits=limits,
                                input_bytes=payload, success_codes=(0,))
        require(digest(execution_source_inventory()) == plan["execution_sources_sha256"],
                "execution source changed during candidate replay")
        result = json.loads(process["stdout"])
        require(result.get("schema") == WORKER_SCHEMA and result.get("candidate_sha256") == candidate_sha
                and result.get("round_sha256") == plan["round_sha256"]
                and result.get("epoch_sha256") == plan["epoch_sha256"]
                and result.get("authority_sha256") == plan["authority_sha256"]
                and result.get("goal_id") == candidate["goal_id"]
                and result.get("commands_sha256") == candidate["commands_sha256"]
                and result.get("model_generation_performed") is False
                and result.get("training_authorized") is False,
                "fresh native worker changed its exact request identity")
        status = result.get("status")
        require(status in {"verified-training-candidate", "rejected-authority",
                           "rejected-candidate-not-a-non-theorem-label", "quarantined-intermediate-overlap"},
                "unknown native candidate status")
        rows = result.get("positive_transitions")
        require(type(rows) is list and len(rows) <= MAX_COMMANDS, "invalid positive transition inventory")
        if status == "verified-training-candidate":
            require(result.get("native_replay_performed") is True and len(rows) == len(candidate["commands"])
                    and type(result.get("proof_nodes")) is int and result["proof_nodes"] > 0,
                    "positive candidate lacks fresh complete native proof")
        else:
            require(not rows and result.get("proof_nodes") is None, "rejected candidate contains positive labels")
        _checked_transitions(rows, request, candidate)
        additions, addition_keys = [], set()
        for row in rows:
            require(row.get("split") == "train" and row.get("epoch_sha256") == plan["epoch_sha256"]
                    and row.get("lineage_sha256") == request["goal"]["lineage_sha256"]
                    and row.get("theorem") == request["goal"]["statement"]
                    and row.get("commands_sha256") == candidate["commands_sha256"]
                    and row.get("kernel_checked") is True, "positive transition changed its registered goal")
            key = digest([row["epoch_sha256"], row["environment_sha256"], row["lineage_sha256"],
                          row["state_sha256"], row["action"]])
            if key in known or key in addition_keys:
                continue
            addition_keys.add(key)
            additions.append({"example_sha256": key, "candidate_sha256": candidate_sha,
                              "proposal_evidence_sha256": candidate["proposal_evidence_sha256"],
                              "provider_kind": candidate["provider_kind"], "transition": row})
        size = len(canonical(additions))
        if accepted_bytes + size > MAX_ACCEPTED_BYTES:
            outcomes.append({"candidate_sha256": candidate_sha, "status": "verified-but-output-budget",
                             "worker_started": True, "retained_transitions": 0, "process": audit})
            continue
        accepted.extend(additions)
        known.update(addition_keys)
        accepted_bytes += size
        retained = len(additions)
        require(len(accepted) <= MAX_ROUND_TRANSITIONS, "harvest exceeds transition cap")
        outcomes.append({"candidate_sha256": candidate_sha, "status": status,
                         "worker_started": True, "retained_transitions": retained,
                         "native_result_sha256": digest(result), "process": audit})
    require(digest(execution_source_inventory()) == plan["execution_sources_sha256"],
            "execution source changed before harvest publication")
    body = {
        "schema": HARVEST_SCHEMA, "round_sha256": plan["round_sha256"],
        "parent_dataset_sha256": plan["parent_dataset_sha256"],
        "parent_readiness_raw_sha256": parent["parent_readiness_raw_sha256"],
        "lineage_review_sha256": parent["lineage_review_sha256"],
        "registered_train_membership_authenticated": True,
        "candidate_count": len(candidates), "outcomes": outcomes,
        "accepted_transitions": accepted, "accepted_transition_count": len(accepted),
        "unknown_candidates": sum(r["status"] == "unknown-worker-failure" for r in outcomes),
        "output_budget_unretained_candidates": sum(r["status"] == "verified-but-output-budget" for r in outcomes),
        "model_generation_performed": False, "model_generation_attested": False,
        "training_authorized": False, "research_claim_eligible": False,
        "automatic_retry": False, "parent_dataset_modified": False,
    }
    return {**body, "harvest_sha256": digest(body)}
