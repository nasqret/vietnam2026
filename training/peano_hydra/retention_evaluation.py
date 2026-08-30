"""Separately versioned DEV retention/transfer evaluation for a mixed adapter.

This is not a FRONTIER BoundEvaluation or a legacy training origin. A genuine
old OriginReference and the new retention training artifact loader bind the
two roles. The exact old DEV32 and existing frontier DEV32 are registered
before training; no TRAIN or reserved benchmark goals enter this protocol.

The original search/model lane, proposal validation, saved-proof validation,
native replay workers and checkpoint file primitives are reused unchanged.
The row/checkpoint wrappers retain their original validation order and caps,
but have their own plan, artifact, authorization and checkpoint schemas.
Execution requires an external one-use scheduler gate and an allocation-wide
monotonic deadline. This module neither allocates nor resumes/retries work.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import stat
import sys
import time
from types import SimpleNamespace

from peano_lab.batch import MODEL_V1_COMMANDS
from peano_lab.ui.prove import SurfaceCapabilities
from training.peano_hydra import capacity, comparison_checkpoint as cp, evaluation as shared
from training.peano_hydra import origin_bridge as bridge, paired_checkpoint as paired
from training.peano_hydra import scaling_evaluation as original, scaling_experiment as experiment
from training.peano_hydra.runner import policy_environment, HYDRA_PROFILED_RUNNER_VERSION, SURFACE_MACRO_V0_INELIGIBILITY
from training.peano_policy.authority import AUTHORITY_PRIMITIVE_PROFILE, authority_contract_record, authority_profile_record
from training.peano_policy.prompt import CapabilityIdentity
from training.peano_policy.search import SearchLimits
from training.peano_policy.state_identity import CONTEXT_ALPHA_V1, StateIdentityReport, search_profile_contract


ROOT = Path(__file__).absolute().parents[2]
PROPOSAL_SCHEMA = "peano-hydra-retention-evaluation-plan-v1"
PLAN_SCHEMA = "peano-hydra-retention-bound-evaluation-v1"
RESULT_SCHEMA = "peano-hydra-retention-evaluation-results-v1"
VERIFY_SCHEMA = "peano-hydra-retention-evaluation-verification-v1"
AUTHORIZATION_SCHEMA = "peano-hydra-retention-evaluation-authorization-v1"
HEADER_SCHEMA = "peano-hydra-retention-evaluation-checkpoint-header-v1"
HEAD_SCHEMA = "peano-hydra-retention-evaluation-checkpoint-head-v1"
ROW_SCHEMA = "peano-hydra-retention-evaluation-checkpoint-row-v1"
ROLES = ("saved-corrected", "mixed-retention")
BUDGETS = (8, 16)
COHORTS = ("retention-dev32", "frontier-dev32")
CHUNK_GOALS = 8
GOAL_COUNT = 64
TOTAL_RECORDS = 256
MAX_CALLS = 3072
MAX_REPORT_BYTES = original.MAX_REPORT_BYTES
MAX_CHECKPOINT_BYTES = original.MAX_CHECKPOINT_BYTES
MAX_AUTHORIZED_SECONDS = 3300
HARD_WALL_SECONDS = 3600
LOADING = original.LOADING
FRONTIER_PLAN_RAW_SHA = "a8084683ea64e4128f4d34eea0753c67fc42a55772e1c698a5dbd62865878c4b"
FRONTIER_PLAN_SHA = "f3875b785182c624abd3ea7b402420a125b38468d4971a1839028ca0ecd7343d"
FRONTIER_GOAL_SET_SHA = "8fec06d69eea03debe38e022cde6b21abad7ef180263205fb6b0bde37e0cc802"
OLD_FAMILIES = ("assumed_le_unpack", "contradiction_elimination", "guarded_projection")
OLD_FAMILY_SIZES = {"assumed_le_unpack": 4, "contradiction_elimination": 48, "guarded_projection": 48}
OLD_INDICES = tuple(i * 47 // 13 for i in range(14))
GOAL_FIELDS = ("name", "source", "statement", "statement_sha256", "lineage_sha256")
FIXED_SEARCH = {"max_depth": 16, "beam_width": 4, "candidates_per_state": 4,
                "max_states": 64, "max_new_tokens": 64, "seed": experiment.SEED}
CLAIM = ("Public, exposed and correlated DEV diagnostics: old DEV retention and frontier DEV transfer "
         "are reported separately. No TRAIN capability probe, unseen/sealed benchmark, readiness, "
         "engine/epoch equivalence, shortest-proof claim or historical GPU attestation.")
CLAIMS = {"research_claim_eligible": False, "sealed_benchmark": False,
          "benchmark_acceptance_eligible": False, "self_training_readiness_eligible": False,
          "heldout_or_reserved_goals_scored": False, "training_goals_scored": False}
_canonical, _digest = shared._canonical, shared._digest
_require, _same, _keys, _integer = capacity._require, capacity._same, capacity._keys, capacity._integer
_runtime, _proposals, _bounds = original._runtime, original._proposals, original._bounds


def _read(path, expected=None, maximum=shared.MAX_MANIFEST_BYTES):
    return original._read(path, expected, maximum)


def _projection(route):
    _require(type(route) is dict and set(GOAL_FIELDS) <= set(route), "DEV route lost its original projection")
    result = {key: route[key] for key in GOAL_FIELDS}
    experiment._name(result["name"], "DEV goal name")
    for key in ("source", "statement"):
        _require(type(result[key]) is str and 0 < len(result[key].encode()) <= 4096
                 and "\x00" not in result[key], "DEV goal text exceeds unchanged replay bound")
    experiment.sha(result["lineage_sha256"], "DEV lineage SHA")
    _require(result["statement_sha256"] == hashlib.sha256(result["statement"].encode()).hexdigest(),
             "DEV statement raw hash changed")
    return result


def _old_selection(routes):
    _require(type(routes) is list and len(routes) == 100, "retention selection requires all100 original DEV routes")
    grouped = {family: [] for family in OLD_FAMILIES}
    for route in routes:
        _require(type(route) is dict and route.get("family") in grouped and route.get("split") == "dev",
                 "undeclared old DEV family or training route")
        grouped[route["family"]].append(route)
    _require({key: len(value) for key, value in grouped.items()} == OLD_FAMILY_SIZES,
             "old DEV family inventory changed")
    selected = []
    for family in OLD_FAMILIES:
        ordered = sorted(grouped[family], key=lambda route: route["name"])
        indices = range(4) if family == "assumed_le_unpack" else OLD_INDICES
        selected.extend(_projection(ordered[index]) for index in indices)
    return selected


def _proposal(preparation_sha, cohorts):
    experiment.sha(preparation_sha, "mixed preparation raw manifest SHA")
    _keys(cohorts, set(COHORTS), "retention evaluation cohorts")
    clean, names, statements = {}, set(), set()
    for cohort in COHORTS:
        rows = cohorts[cohort]
        _require(type(rows) is list and len(rows) == 32, "each fixed DEV cohort requires32 goals")
        clean[cohort] = []
        for row in rows:
            _keys(row, set(GOAL_FIELDS), "evaluation goal")
            goal = _projection(row)
            _require(goal["name"] not in names and goal["statement_sha256"] not in statements,
                     "retention/transfer goal names or statements overlap")
            names.add(goal["name"]); statements.add(goal["statement_sha256"])
            clean[cohort].append(goal)
    _require(_digest(clean[COHORTS[1]]) == FRONTIER_GOAL_SET_SHA,
             "frontier DEV32 changed its exact historical goal projection/order")
    goals = [goal for cohort in COHORTS for goal in clean[cohort]]
    body = {"schema": PROPOSAL_SCHEMA, "status": "planned-not-run", "run_id": "retention-pilot-v1",
        "preparation_manifest_sha256": preparation_sha,
        "frontier_plan_raw_sha256": FRONTIER_PLAN_RAW_SHA, "frontier_plan_sha256": FRONTIER_PLAN_SHA,
        "retention_selection": {"family_order": list(OLD_FAMILIES), "original_family_sizes": OLD_FAMILY_SIZES,
            "assumed_le_unpack_indices": list(range(4)), "other_family_indices": list(OLD_INDICES),
            "ordering": "family-order; lexicographic original theorem name before selecting indices",
            "selection_uses_model_scores": False},
        "cohort_order": list(COHORTS), "cohorts": clean, "goals": goals, "goal_set_sha256": _digest(goals),
        "roles": list(ROLES), "budgets": list(BUDGETS), "fixed_search": FIXED_SEARCH,
        "search_profile": CONTEXT_ALPHA_V1,
        "ordered_slots": [{"role": role, "max_model_calls": budget, "goal": goal["name"]}
            for role in ROLES for budget in BUDGETS for goal in goals],
        "max_model_calls_total": MAX_CALLS, "goal_records": TOTAL_RECORDS,
        "allocation": {"gpu_count": 1, "cpus": 8, "memory_gib": 64,
            "hard_wall_seconds": HARD_WALL_SECONDS, "whole_allocation_soft_wall_seconds": MAX_AUTHORIZED_SECONDS},
        "all_positive_proofs_require_fresh_native_replay": True,
        "same_budget_comparisons_only": True, "partial_pairs_scored": False,
        "interrupted_or_unstarted": "unknown; never an invented failed proof",
        "training_authorized": False, "gpu_execution_authorized": False,
        "automatic_retry": False, "resume": False, "claim_boundary": CLAIM, **CLAIMS}
    # Callers may inspect/edit a draft without mutating this module's fixed
    # search/selection dictionaries and thereby changing later validation.
    return json.loads(_canonical({**body, "plan_sha256": _digest(body)}))


def validate_evaluation_plan(record):
    """Pure metadata validation; this does not authenticate a preparation."""
    _require(type(record) is dict, "retention plan must be a JSON object")
    expected = _proposal(record.get("preparation_manifest_sha256"), record.get("cohorts"))
    _require(_same(record, expected), "retention plan changed its fixed cohort/budget/claim contract")
    return expected


def validate_preparation_join(record, checked_data):
    """Join a genuinely loaded mixed preparation, not a fabricated old origin."""
    from training.peano_hydra.retention_data import RetentionPreparation
    _require(type(checked_data) is RetentionPreparation, "evaluation requires the exact mixed preparation type")
    plan = validate_evaluation_plan(record)
    _require(plan["preparation_manifest_sha256"] == checked_data.manifest_sha256,
             "evaluation changed the pretraining mixed data manifest")
    routes = checked_data.dev_cohorts
    _keys(routes, {"saved-v25", "frontier-v28"}, "original DEV source cohorts")
    _require(_same(_old_selection(routes["saved-v25"]), plan["cohorts"][COHORTS[0]]),
             "retention goals are not the fixed original DEV selection")
    front = {_projection(route)["name"]: _projection(route) for route in routes["frontier-v28"]}
    _require(len(front) == len(routes["frontier-v28"])
             and all(route.get("split") == "dev" for route in routes["frontier-v28"]),
             "duplicate or reassigned original frontier DEV route")
    for goal in plan["cohorts"][COHORTS[1]]:
        _require(front.get(goal["name"]) == goal, "frontier goal changed its original DEV source route")
    training_statements = {row["theorem_statement_sha256"] for row in checked_data.train_rows}
    training_lineages = {row["lineage_sha256"] for row in checked_data.train_rows}
    development = {(row["theorem_name"], row["theorem_statement_sha256"], row["lineage_sha256"])
                   for row in checked_data.dev_rows}
    for goal in plan["goals"]:
        _require(goal["statement_sha256"] not in training_statements and goal["lineage_sha256"] not in training_lineages
                 and (goal["name"], goal["statement_sha256"], goal["lineage_sha256"]) in development,
                 "selected DEV goal was trained, missing or reassigned")
    return plan


def build_evaluation_plan(checked_data, *, frontier_evaluation_plan_path, expected_frontier_plan_sha256):
    """Register deterministic old DEV32 plus the unchanged exposed frontier32."""
    _require(expected_frontier_plan_sha256 == FRONTIER_PLAN_RAW_SHA, "frontier selection needs its preserved raw plan pin")
    frontier, _ = _read(frontier_evaluation_plan_path, expected_frontier_plan_sha256, experiment.MAX_RECORD_BYTES)
    experiment.validate_evaluation_plan(frontier)
    _require(frontier["plan_sha256"] == FRONTIER_PLAN_SHA and frontier["goal_set_sha256"] == FRONTIER_GOAL_SET_SHA,
             "historical frontier DEV selection changed")
    plan = _proposal(checked_data.manifest_sha256, {COHORTS[0]: _old_selection(checked_data.dev_cohorts["saved-v25"]),
        COHORTS[1]: frontier["goals"]})
    return validate_preparation_join(plan, checked_data)


def execution_sources():
    result = original.execution_sources()
    for name in ("retention_data.py", "retention_training.py", "retention_evaluation.py"):
        relative = "training/peano_hydra/" + name
        result[relative] = hashlib.sha256(bridge._read(ROOT / relative, bridge.MAX_PYTHON_BYTES)).hexdigest()
    _require(len(result) <= capacity.MAX_SOURCE_FILES, "retention execution inventory exceeds inherited bound")
    return dict(sorted(result.items()))


@dataclass(frozen=True, slots=True)
class BoundEvaluation:
    evaluation_path: Path
    evaluation_raw_sha256: str
    baseline: original.OriginReference
    candidate: object
    _record_json: str

    def to_dict(self): return json.loads(self._record_json)
    @property
    def proposal(self): return self.to_dict()["evaluation_plan"]
    @property
    def goals(self): return tuple(self.proposal["goals"])
    @property
    def training_identities(self): return self.to_dict()["training_identities"]


def _training_identity(kind, identity):
    body = {"kind": kind, "identity": identity}
    return {**body, "identity_sha256": _digest(body)}


def bind_evaluation(evaluation_plan_path, *, expected_evaluation_plan_sha256, baseline, candidate):
    """Authenticate the real old origin and separately typed completed mixture."""
    from training.peano_hydra.retention_training import TrainingArtifactReference
    _require(type(baseline) is original.OriginReference and type(candidate) is TrainingArtifactReference,
             "retention evaluation needs genuine old and mixed artifact reference types")
    path = bridge._absolute(Path(evaluation_plan_path))
    proposal, raw = _read(path, expected_evaluation_plan_sha256, experiment.MAX_RECORD_BYTES)
    validate_evaluation_plan(proposal)
    before = execution_sources()
    old, mixed = baseline.load(), candidate.load()
    _require(_same(candidate.inputs.baseline.to_dict(), baseline.to_dict()), "mixed training changed the declared old baseline origin")
    frontier = candidate.inputs.frontier.load()
    validate_preparation_join(proposal, mixed.checked_data)
    _require(_same(proposal, mixed.plan.evaluation_plan)
             and candidate.inputs.evaluation_plan_sha256 == expected_evaluation_plan_sha256,
             "evaluation was not the exact plan declared before mixed training")
    prepared, _ = _read(candidate.inputs.frontier.request.preparation_directory / "manifest.json",
                         candidate.inputs.frontier.request.preparation_manifest_sha256)
    caps, environment = original._caps(prepared["authority"])
    prompt, decoder = authority_contract_record(), authority_profile_record(environment)
    model = {"model_id": experiment.MODEL_ID, "revision": experiment.MODEL_REVISION}
    for identity in (old.origin, frontier.origin, mixed.identity):
        _require(identity["training_authority_profile"] == AUTHORITY_PRIMITIVE_PROFILE
                 and _same(identity["model"], model) and _same(identity["training_prompt_contract"], prompt)
                 and _same(identity["training_decoder_profile"], decoder),
                 "retention roles changed the pinned model/V4/no-import contract")
    _require(_same(old.origin["artifacts"]["tokenizer"], mixed.identity["artifacts"]["tokenizer"])
             and _same(frontier.origin["artifacts"]["tokenizer"], mixed.identity["artifacts"]["tokenizer"]),
             "matched retention roles changed tokenizer bytes")
    _require(baseline.request.adapter_manifest_sha256 != candidate.manifest_sha256,
             "old and mixed roles must identify distinct artifacts")
    identities = {ROLES[0]: _training_identity("preserved-original-training-origin", old.origin),
                  ROLES[1]: _training_identity("authenticated-mixed-retention-training-artifact", mixed.identity)}
    contract = {"schema": "peano-hydra-retention-evaluation-execution-contract-v1",
        "evaluation_plan_sha256": proposal["plan_sha256"], "evaluation_raw_sha256": expected_evaluation_plan_sha256,
        "training_identities": identities, "execution_epoch_sha256": frontier.origin["epoch_sha256"],
        "model": model, "environment": policy_environment(caps), "authority_profile": AUTHORITY_PRIMITIVE_PROFILE,
        "prompt_contract": prompt, "decoder_profile": decoder, "search_profile": search_profile_contract(CONTEXT_ALPHA_V1),
        "fixed_search": FIXED_SEARCH, "budgets": list(BUDGETS), "chunk_goals": CHUNK_GOALS,
        "goal_set_sha256": proposal["goal_set_sha256"], "order": "role-budget-goal", "model_loading": LOADING,
        "engine_or_epoch_equivalence_claimed": False, "historical_checkpoint_reuse_allowed": False}
    binding = bridge.execution_binding(source_root=ROOT, source_files=before, contract=contract)
    record = {"schema": PLAN_SCHEMA, "evaluation_plan": proposal, "evaluation_raw_sha256": expected_evaluation_plan_sha256,
        "training_identities": identities, "baseline_reference": baseline.to_dict(), "candidate_reference": candidate.to_dict(),
        "execution_binding": binding, "execution_sources": before, "claim_boundary": CLAIM,
        "max_report_bytes": MAX_REPORT_BYTES, "max_checkpoint_bytes": MAX_CHECKPOINT_BYTES,
        "max_goal_evidence_bytes": shared.MAX_GOAL_EVIDENCE_BYTES, "max_chunk_evidence_bytes": shared.MAX_LANE_EVIDENCE_BYTES,
        "offline_replay_limits": capacity.REPLAY_LIMITS.to_dict(), "gpu_execution_authorized": False,
        "training_authorized": False, "resume_allowed": False, **CLAIMS}
    _require(_same(before, execution_sources()) and bridge._read(path, experiment.MAX_RECORD_BYTES) == raw,
             "retention execution source or preregistered plan changed during binding")
    _require(_same(baseline.load().origin, old.origin) and _same(candidate.load().identity, mixed.identity),
             "retention artifact identity changed during binding")
    record["plan_sha256"] = _digest(record)
    _require(len(_canonical(record)) <= cp.MAX_HEADER_BYTES // 2, "retention bound metadata exceeds inherited header cap")
    return BoundEvaluation(path, expected_evaluation_plan_sha256, baseline, candidate, _canonical(record).decode())


def _refresh(plan):
    _require(type(plan) is BoundEvaluation, "retention needs its own authenticated plan type")
    fresh = bind_evaluation(plan.evaluation_path, expected_evaluation_plan_sha256=plan.evaluation_raw_sha256,
                            baseline=plan.baseline, candidate=plan.candidate)
    _require(_same(fresh.to_dict(), plan.to_dict()), "retention data/source/artifact/plan binding changed")


def _schema(plan, schema):
    _require(type(plan) is BoundEvaluation, "legacy evaluation plans cannot enter retention checkpoints")
    return schema


def _claim(plan): return plan.to_dict()["claim_boundary"]


@dataclass(frozen=True, slots=True)
class _Execution:
    plan: BoundEvaluation
    budget: int
    _goals_json: str

    @property
    def contract(self): return self.plan.to_dict()["execution_binding"]["contract"]
    @property
    def model(self): return self.contract["model"]
    @property
    def epoch(self): return SimpleNamespace(epoch_sha256=self.contract["execution_epoch_sha256"])
    @property
    def environment(self): return policy_environment(self.capabilities)
    @property
    def capabilities(self):
        identity = self.contract["environment"]["capabilities"]
        return SurfaceCapabilities(label=identity["label"], allowed_commands=frozenset(identity["allowed_commands"]),
                                   allowed_theorems=frozenset(identity["allowed_theorems"]))
    @property
    def authority_profile(self): return AUTHORITY_PRIMITIVE_PROFILE
    @property
    def goals(self): return tuple(json.loads(self._goals_json))
    @property
    def limits(self): return SearchLimits(max_depth=16, beam_width=4, candidates_per_state=4, max_states=64, max_model_calls=self.budget)
    @property
    def seed(self): return experiment.SEED
    @property
    def max_new_tokens(self): return 64
    @property
    def goal_set_sha256(self): return _digest(self.goals)
    @property
    def matched_budget(self):
        return {**shared._limits_record(self.limits), "goal_count": len(self.goals),
                "max_model_calls_per_lane": len(self.goals) * self.budget, "max_new_tokens": 64,
                "seed": self.seed, "sampling": "deterministic batched candidate beam search"}


def _view(plan, budget, goals=None):
    _require(type(plan) is BoundEvaluation and type(budget) is int and budget in BUDGETS, "unknown retention plan/budget")
    goals = plan.goals if goals is None else tuple(goals)
    return _Execution(plan, budget, _canonical(goals).decode())


def _provider(plan, role, budget, runtime):
    _require(role in ROLES and type(budget) is int and budget in BUDGETS, "unknown retention role/budget")
    _runtime(runtime)
    return {"kind": "mixed-retention-evaluation-provider-v1", "adapter_attached": True,
        "model": _view(plan, budget).model, "training_identity": plan.training_identities[role], "role": role,
        "max_model_calls": budget, "search_profile": search_profile_contract(CONTEXT_ALPHA_V1),
        "execution_binding_sha256": plan.to_dict()["execution_binding"]["execution_binding_sha256"],
        "runtime": runtime, "research_claim_eligible": False}


def _guard_output(path, plan):
    from training.peano_hydra import corrective_workflow as files
    reference = plan.baseline
    protected = (reference.request.source_root, reference.request.adapter_manifest.parent,
        reference.receipt_path.parent, plan.evaluation_path.parent, *plan.candidate.protected_paths(),
        ROOT / "training", ROOT / "scripts", ROOT / "slurm", ROOT / "peano-lab")
    return files.guard_output(path, protected=protected)


# These wrappers preserve the original validator/checkpoint algorithm.
# Their globals bind this module's new plan/types/schemas, not legacy plans.
def validate_row(plan, role, budget, goal, row, runtime, *, replay=False):
    """Authenticate saved assertions; only explicit fresh replay proves a positive."""
    _require(type(replay) is bool, "replay must be an explicit Boolean")
    if replay: paired._model_free()
    _require(type(plan) is BoundEvaluation and any(_same(goal, item) for item in plan.goals), "undeclared evaluation goal")
    view, contract = _view(plan, budget), search_profile_contract(CONTEXT_ALPHA_V1)
    provider = _provider(plan, role, budget, runtime)
    _keys(row, paired._ROW_FIELDS, "FRONTIER model row")
    _require(row["goal"] == goal["name"] and row["research_claim_eligible"] is False
             and len(_canonical(row)) <= cp.MAX_ROW_BYTES, "row goal/claim/byte bound changed")
    paired._resources(row["resources"])
    _integer(row["model_generate_calls"], "model calls", budget)
    evidence = row["evidence"]
    _require(type(evidence) is dict, "row lacks structured Hydra evidence")
    search = evidence.get("search")
    _keys(evidence, paired._EVIDENCE_FIELDS | {"search_profile"}, "FRONTIER Hydra evidence")
    _keys(search, paired._SEARCH_FIELDS | {"state_identity"}, "FRONTIER search evidence")
    _require(type(evidence["v"]) is int and evidence["v"] == HYDRA_PROFILED_RUNNER_VERSION
             and _same(evidence["search_profile"], contract), "runner/profile contract changed")
    identity = search["state_identity"]
    _keys(identity, {"contract", "counters"}, "FRONTIER state identity")
    _require(_same(identity["contract"], contract), "nested state-identity contract changed")
    _keys(identity["counters"], {"key_attempts", "keys_built", "keys_declined", "duplicate_states", "renamed_states",
                                  "retained_key_bytes", "key_budget_declines"}, "state-identity counters")
    StateIdentityReport(**identity["counters"])
    counters = identity["counters"]
    _integer(search["candidates_executed"], "candidate executions", budget * 4)
    _integer(search["states_discovered"], "states discovered", 64, 1)
    _require(1 <= counters["key_attempts"] <= search["candidates_executed"] + 1
             and search["states_discovered"] <= counters["key_attempts"] - counters["duplicate_states"]
             and counters["retained_key_bytes"] <= min(contract["max_retained_key_bytes"], search["states_discovered"] * contract["max_key_bytes"]),
             "state-identity counters exceed actual bounded work")
    _require(len(_canonical(evidence)) <= shared.MAX_GOAL_EVIDENCE_BYTES
             and hashlib.sha256(_canonical(evidence)).hexdigest() == row["evidence_sha256"], "evidence digest/bytes differ")
    _require(evidence["theorem"] == search["theorem"] == goal["statement"]
             and _same(evidence["environment"], view.environment)
             and _same(evidence["limits"], shared._limits_record(view.limits))
             and evidence["label"] == f"hydra-alpha-eval-trained-{goal['name']}"
             and evidence["policy"] == f"hydra-alpha-portfolio-trained-{goal['name']}"
             and evidence["degraded"] is False and evidence["degradation_reasons"] == []
             and evidence["eligible_for_comparison"] is False
             and evidence["comparison_ineligibility_reasons"] == [SURFACE_MACRO_V0_INELIGIBILITY], "search authority/limit/claim changed")
    _require(row["status"] == evidence["status"] == search["status"]
             and type(search["model_calls"]) is int and type(search["states_expanded"]) is int
             and search["model_calls"] == search["states_expanded"] == row["model_generate_calls"], "status/call accounting differs")
    _integer(search["frontier_peak"], "frontier peak", 4, 1)
    _integer(search["depth_reached"], "search depth", 16)
    _require(type(search["diagnostics"]) is list and len(search["diagnostics"]) <= 128, "diagnostic count exceeds bound")
    for diagnostic in search["diagnostics"]:
        _keys(diagnostic, {"kind", "depth", "state_sha256", "command", "message"}, "search diagnostic")
        _integer(diagnostic["depth"], "diagnostic depth", 16)
        _require(all(type(diagnostic[k]) is str and len(diagnostic[k].encode()) <= 4096 for k in ("kind", "state_sha256", "message"))
                 and (diagnostic["command"] is None or type(diagnostic["command"]) is str and len(diagnostic["command"].encode()) <= 4096),
                 "diagnostic text exceeds bound")
    commands = search["commands"]
    _require(type(commands) is list and len(commands) <= 16 and all(type(c) is str and 0 < len(c.encode()) <= 4096 for c in commands),
             "command route exceeds bounds")
    _require(type(row["tactic_decisions"]) is int and row["tactic_decisions"] == len(commands)
             and row["commands_sha256"] == evidence["commands_sha256"] == (_digest(commands) if row["status"] == "proof" else None),
             "command count/digest differs")
    proposals = _proposals(view, goal, row, provider)
    if row["status"] != "proof":
        _require(row["status"] in {"limit", "exhausted"} and row["kernel_checked"] is False
                 and evidence["proved"] is False and commands == [] and evidence["replay"] is None
                 and row["proof_nodes"] is None and search["certificate_nodes"] is None, "unproved outcome invented proof evidence")
        return None
    _require(row["kernel_checked"] is True and evidence["proved"] is True and 1 <= len(commands) <= search["depth_reached"],
             "positive proof/depth claim differs")
    _integer(row["proof_nodes"], "proof nodes", 1_000_000, 1)
    _require(type(search["certificate_nodes"]) is int and search["certificate_nodes"] == row["proof_nodes"], "certificate count differs")
    paired._saved_proof(evidence, goal, row, contract, proposals)
    if not replay: return None
    fresh, process = capacity._replay_success(view, goal, row)
    _require(_same(fresh, evidence["replay"]), "independent original-goal proof replay differs")
    return {"role": role, "max_model_calls": budget, "goal": goal["name"], "commands_sha256": row["commands_sha256"],
            "proof_nodes": row["proof_nodes"], "replay_process": process}

def validate_execution_authorization(plan, record, *, expected_authorization_sha256):
    """Check an externally pinned CANONICAL assertion; never mint approval.

    A future caller must also supply its trusted reservation checker. Neither
    this assertion nor passing that callback attests a user or a GPU device.
    """
    experiment.sha(expected_authorization_sha256, "external canonical authorization SHA")
    _keys(record, {"schema", "authorization_id", "plan_sha256", "execution_binding_sha256",
        "model_inference_authorized", "gpu_count", "max_wall_seconds", "max_model_calls", "max_goal_records",
        "external_hard_wall_limit_required", "training_authorized", "upload_authorized", "new_allocation_authorized",
        "automatic_retry", "resume", "historical_checkpoint_reuse_allowed"}, "FRONTIER execution authorization")
    _require(_digest(record) == expected_authorization_sha256, "externally pinned authorization changed")
    experiment._name(record["authorization_id"], "authorization ID")
    _integer(record["max_wall_seconds"], "authorized wall seconds", MAX_AUTHORIZED_SECONDS, 1)
    _require(record["schema"] == AUTHORIZATION_SCHEMA and record["model_inference_authorized"] is True
             and record["external_hard_wall_limit_required"] is True
             and all(record[k] is False for k in ("training_authorized", "upload_authorized", "new_allocation_authorized",
                                                  "automatic_retry", "resume", "historical_checkpoint_reuse_allowed"))
             and type(record["gpu_count"]) is int and record["gpu_count"] == 1
             and type(record["max_model_calls"]) is int and record["max_model_calls"] == plan.proposal["max_model_calls_total"]
             and type(record["max_goal_records"]) is int and record["max_goal_records"] == len(plan.proposal["ordered_slots"])
             and record["plan_sha256"] == plan.to_dict()["plan_sha256"]
             and record["execution_binding_sha256"] == plan.to_dict()["execution_binding"]["execution_binding_sha256"],
             "authorization changed the exact one-GPU fresh evaluation/plan/call boundaries")
    return json.loads(_canonical(record))

class EvaluationCheckpoint(cp.CheckpointStore):
    """New schemas and fixed planned order; fresh writes or read-only inspection."""
    head_schema = HEAD_SCHEMA
    claim = CLAIM

    def __init__(self, path, plan, *, expected_authorization_sha256, authorization=None,
                 runtime=None, progress=None, verify_only=False, replay_proofs=True):
        _require(type(plan) is BoundEvaluation and type(verify_only) is bool and type(replay_proofs) is bool,
                 "checkpoint requires the exact new plan and Boolean mode")
        _require(verify_only or replay_proofs, "metadata-only checkpoint mode is read-only")
        self.verify_only, self.replay_proofs = verify_only, replay_proofs
        self.head_schema, self.claim = _schema(plan, HEAD_SCHEMA), _claim(plan)
        self.expected_authorization_sha256 = experiment.sha(expected_authorization_sha256, "external canonical authorization SHA")
        self.total_goals, self.goals_per_role = len(plan.proposal["ordered_slots"]), len(plan.goals)
        self.authorization = None if authorization is None else validate_execution_authorization(
            plan, authorization, expected_authorization_sha256=expected_authorization_sha256)
        _refresh(plan)
        if not verify_only:
            _require(self.authorization is not None, "fresh checkpoint needs explicit evaluation authorization")
            _guard_output(Path(path), plan)
            super().__init__(Path(path), plan, plan.training_identities, runtime=runtime, resume=False, progress=progress)
            return
        _require(authorization is None and runtime is None, "read-only verification uses saved metadata, not replacements")
        paired._model_free()
        self.path, self.plan, self.origins = bridge._absolute(Path(path)), plan, plan.training_identities
        self.progress, self.goals = progress or cp.Progress(), plan.goals
        self.rows, self.hashes, self.replayed = [], [], []
        self.fd = self.lock = -1
        try:
            self.fd = cp._directory(self.path, create=False)
            self.lock = os.open(".lock", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
            info = os.fstat(self.lock)
            _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, "unsafe read-only checkpoint lock")
            fcntl.flock(self.lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
            self._load()
            self.runtime = self.header["provider_runtime"]
            self.assert_unchanged()
            _refresh(plan)
            self.assert_unchanged()
        except BaseException:
            self.close()
            raise

    def _goal_inventory(self): return self.plan.goals
    def _contexts(self): self.contexts = {}
    def _cohort_bounds(self): _bounds(self.plan, self.rows)

    def _make_header(self, runtime):
        _runtime(runtime)
        validate_execution_authorization(self.plan, self.authorization,
                                          expected_authorization_sha256=self.expected_authorization_sha256)
        return cp._sign({"schema": _schema(self.plan, HEADER_SCHEMA), "plan": self.plan.to_dict(), "provider_runtime": runtime,
            "authorization": self.authorization, "authorization_sha256": self.expected_authorization_sha256,
            "order": "role-budget-goal", "goal_records": self.total_goals,
            "historical_gpu_inference_attested": False, "research_claim_eligible": False}, "header_sha256")

    def _goal_binding(self, index):
        _integer(index, "checkpoint ordinal", self.total_goals - 1)
        slot = self.plan.proposal["ordered_slots"][index]
        goal = self.goals[index % self.goals_per_role]
        _require(slot["goal"] == goal["name"], "planned slot changed exact goal order")
        return {"ordinal": index + 1, **slot, "cohort": "calls-" + str(slot["max_model_calls"]),
            "goal_sha256": _digest(goal), "source_sha256": hashlib.sha256(goal["source"].encode()).hexdigest(),
            "statement_sha256": goal["statement_sha256"], "search_profile": CONTEXT_ALPHA_V1,
            "search_profile_sha256": search_profile_contract(CONTEXT_ALPHA_V1)["contract_sha256"],
            "training_identity_sha256": self.plan.training_identities[slot["role"]]["identity_sha256"]}

    def _make_record(self, previous, binding, row):
        return cp._sign({"schema": _schema(self.plan, ROW_SCHEMA), "header_sha256": self.header["header_sha256"],
            "previous_sha256": previous, **binding, "row": row, "row_sha256": _digest(row),
            "proposal_records_sha256": _digest(row["evidence"]["proposal_records"]),
            "evidence_sha256": row["evidence_sha256"], "commands_sha256": row["commands_sha256"]}, "record_sha256")

    def _validate_completed_row(self, binding, row, *, replay):
        goal = self.goals[(binding["ordinal"] - 1) % self.goals_per_role]
        return validate_row(self.plan, binding["role"], binding["max_model_calls"], goal, row,
                            self.header["provider_runtime"], replay=replay)

    def _write(self, name, value, *, replace_existing):
        _require(not self.verify_only, "read-only evaluation checkpoint cannot write")
        return super()._write(name, value, replace_existing=replace_existing)

    def begin(self, role, cohort, goal):
        _require(not self.verify_only, "checkpoint inspection cannot resume generation")
        return super().begin(role, cohort, goal)

    def append(self, row):
        _require(not self.verify_only, "checkpoint inspection cannot append evidence")
        self.assert_unchanged(contents=False)
        binding = self._goal_binding(len(self.rows))
        _require(_same(self.head["inflight"], binding), "completion has no exact in-flight slot")
        row = shared._json_object(_canonical(row), description="FRONTIER checkpoint row")
        self._validate_completed_row(binding, row, replay=False)
        _bounds(self.plan, self.rows + [row])
        record = self._make_record(self.head["record_sha256"], binding, row)
        raw = _canonical(record) + b"\n"
        total = self.head["record_bytes"] + len(raw)
        _require(len(raw) <= cp.MAX_ROW_BYTES and total <= MAX_CHECKPOINT_BYTES, "checkpoint exceeds retained-byte reservation")
        self._write(f"{len(self.rows) + 1:06d}.goal.json", record, replace_existing=False)
        head = self._head(len(self.rows) + 1, record["record_sha256"], total, None)
        self._write("HEAD.json", head, replace_existing=True)
        self.head = head
        self.rows.append(row)
        self.hashes.append(hashlib.sha256(raw).hexdigest())

    def _load(self):
        header, _ = self._read("header.json", cp.MAX_HEADER_BYTES)
        self.authorization = validate_execution_authorization(self.plan, header.get("authorization"),
            expected_authorization_sha256=self.expected_authorization_sha256)
        _require(_same(header, self._make_header(header.get("provider_runtime"))), "checkpoint header changed plan/origins/authorization")
        self.header = header
        self.head, _ = self._read("HEAD.json", cp.MAX_HEADER_BYTES)
        _keys(self.head, {"schema", "header_sha256", "completed", "record_sha256", "record_bytes", "inflight", "head_sha256"}, "checkpoint HEAD")
        capacity._signed(self.head, "head_sha256")
        _require(self.head["schema"] == self.head_schema and self.head["header_sha256"] == header["header_sha256"], "checkpoint HEAD changed identity")
        count = _integer(self.head["completed"], "committed count", self.total_goals)
        _integer(self.head["record_bytes"], "retained bytes", MAX_CHECKPOINT_BYTES)
        inflight = self.head["inflight"]
        _require(inflight is None or count < self.total_goals and _same(inflight, self._goal_binding(count)), "unknown in-flight binding")
        self._inventory(count)  # Debris/uncommitted rows are never promoted.
        previous, total = header["header_sha256"], 0
        for index in range(count):
            record, raw = self._read(f"{index + 1:06d}.goal.json", cp.MAX_ROW_BYTES)
            binding, row = self._goal_binding(index), record.get("row")
            _require(type(row) is dict and _same(record, self._make_record(previous, binding, row)), "checkpoint exact order/chain/row digest changed")
            self._validate_completed_row(binding, row, replay=False)
            previous, total = record["record_sha256"], total + len(raw)
            _require(total <= MAX_CHECKPOINT_BYTES, "checkpoint total byte bound exceeded")
            self.rows.append(row)
            self.hashes.append(hashlib.sha256(raw).hexdigest())
        _require(_same(self.head, self._head(count, previous, total, inflight)), "checkpoint HEAD/count/bytes differ")
        self._cohort_bounds()
        self.assert_unchanged()
        # No proof work until ALL committed metadata and terminal state join.
        if self.replay_proofs:
            for index, row in enumerate(self.rows):
                if row["kernel_checked"]:
                    self.replayed.append(self._validate_completed_row(self._goal_binding(index), row, replay=True))

    def receipt(self, *, status=None):
        complete = len(self.rows) == self.total_goals and self.head["inflight"] is None
        replayed = self.verify_only and self.replay_proofs
        return {"schema": _schema(self.plan, VERIFY_SCHEMA), "status": status or ("native-prefix-verified" if replayed else "metadata-only"),
            "plan_sha256": self.plan.to_dict()["plan_sha256"], "checkpoint_header_sha256": self.header["header_sha256"],
            "checkpoint_head_sha256": self.head["head_sha256"], "completed_goal_records": len(self.rows),
            "total_goal_records": self.total_goals, "all_goal_records_present": complete,
            "verification_complete": complete and replayed, "proof_replay_performed": replayed,
            "committed_model_generate_calls": sum(row["model_generate_calls"] for row in self.rows),
            "inflight": self.head["inflight"], "inflight_model_generate_calls": None if self.head["inflight"] else 0,
            "independently_replayed_proofs": self.replayed, "model_outputs_regenerated": False,
            "historical_gpu_inference_attested": False, "claim_boundary": self.claim, **CLAIMS}

def verify_checkpoint(plan, directory, *, expected_authorization_sha256, replay=True, progress=None):
    """Read-only committed prefix; never retry an interrupted in-flight goal."""
    with EvaluationCheckpoint(directory, plan, expected_authorization_sha256=expected_authorization_sha256,
                              verify_only=True, replay_proofs=replay, progress=progress) as store:
        return store.receipt()


def summarize_outcomes(plan, rows):
    """Derived metadata only; complete matched cohorts are never cherry-picked."""
    _require(type(plan) is BoundEvaluation and type(rows) is list and len(rows) <= TOTAL_RECORDS,
             "retention metrics require one bounded exact prefix")
    validate_evaluation_plan(plan.proposal)
    by_slot = {(slot["role"], slot["max_model_calls"], slot["goal"]): row
               for slot, row in zip(plan.proposal["ordered_slots"], rows)}
    def outcome(row, budget):
        if row is None: return "missing-unknown"
        if row["kernel_checked"]: return "proof"
        if row["status"] == "exhausted": return "exhausted"
        return "call-limit" if row["model_generate_calls"] == budget else "unknown"
    cohorts = {}
    for cohort in COHORTS:
        goals = plan.proposal["cohorts"][cohort]
        lanes, comparisons = [], []
        for budget in BUDGETS:
            for role in ROLES:
                selected = [by_slot.get((role, budget, goal["name"])) for goal in goals]
                statuses = Counter(outcome(row, budget) for row in selected)
                committed = [row for row in selected if row is not None]
                unknown = statuses["unknown"] + statuses["missing-unknown"]
                lanes.append({"role": role, "max_model_calls": budget, "planned_goals": 32,
                    "committed_goal_records": len(committed), "reported_proofs": statuses["proof"],
                    "unknown_outcomes_including_missing": unknown,
                    "missing_unknown_goal_records": statuses["missing-unknown"],
                    "known_unproved_within_budget": statuses["exhausted"] + statuses["call-limit"],
                    "reported_proof_fraction_if_all_known": statuses["proof"] / 32 if unknown == 0 else None,
                    "committed_model_generate_calls": sum(row["model_generate_calls"] for row in committed),
                    "malformed_sequences_rejected": sum(row["generation"]["malformed_sequences_rejected"] for row in committed),
                    "authority_sequences_rejected": sum(row["generation"]["authority_sequences_rejected"] for row in committed)})
            complete = all((role, budget, goal["name"]) in by_slot for role in ROLES for goal in goals)
            item = {"max_model_calls": budget, "all64_matched_rows_present": complete,
                "planned_paired_goals": 32, "known_paired_goals": None, "unknown_pair_goals": None,
                "reported_gains": None, "reported_losses": None, "reported_net_gain_among_known_pairs": None}
            if complete:
                gains, losses, unknown = [], [], []
                for goal in goals:
                    name = goal["name"]
                    old, new = (outcome(by_slot[(role, budget, name)], budget) for role in ROLES)
                    if "unknown" in (old, new): unknown.append(name)
                    elif old != "proof" and new == "proof": gains.append(name)
                    elif old == "proof" and new != "proof": losses.append(name)
                item.update(known_paired_goals=32 - len(unknown), unknown_pair_goals=unknown,
                    reported_gains=gains, reported_losses=losses, reported_net_gain_among_known_pairs=len(gains) - len(losses))
            comparisons.append(item)
        cohorts[cohort] = {"lanes": lanes, "matched_comparisons": comparisons}
    return {"schema": "peano-hydra-retention-evaluation-metadata-v1",
        "status": "metadata-only-not-independent-proof-verification", "cohorts": cohorts,
        "completed_goal_records": len(rows), "missing_unknown_goal_records": TOTAL_RECORDS - len(rows),
        "all256_records_present": len(rows) == TOTAL_RECORDS, "proof_replay_performed": False,
        "partial_pairs_scored": False, "cross_budget_training_claim_allowed": False,
        "claim_boundary": CLAIM, **CLAIMS}


def _result(plan, rows, runtime, authorization, authorization_sha):
    _require(len(rows) == TOTAL_RECORDS, "partial retention prefix cannot become a final evaluation")
    result = {"schema": RESULT_SCHEMA, "status": "executed", "plan": plan.to_dict(), "provider_runtime": runtime,
        "authorization": authorization, "authorization_sha256": authorization_sha, "rows": rows,
        "metrics": summarize_outcomes(plan, rows), "model_outputs_regenerated": False,
        "historical_gpu_inference_attested": False, "claim_boundary": CLAIM, **CLAIMS}
    result["evaluation_sha256"] = _digest(result)
    _require(len(_canonical(result)) <= MAX_REPORT_BYTES, "retention result exceeds inherited report cap")
    return result


def verify_result(plan, result, *, expected_authorization_sha256, replay=True):
    """All metadata precedes unchanged bounded native replay of every positive."""
    _require(type(replay) is bool, "replay choice must be Boolean")
    if replay: paired._model_free()
    _refresh(plan)
    _require(type(result) is dict and len(_canonical(result)) <= MAX_REPORT_BYTES, "retention report bound")
    authorization = validate_execution_authorization(plan, result.get("authorization"),
        expected_authorization_sha256=expected_authorization_sha256)
    _runtime(result.get("provider_runtime"))
    rows = result.get("rows")
    _require(type(rows) is list and len(rows) == TOTAL_RECORDS, "retention report lacks all256 prescribed rows")
    for index, (slot, row) in enumerate(zip(plan.proposal["ordered_slots"], rows, strict=True)):
        validate_row(plan, slot["role"], slot["max_model_calls"], plan.goals[index % GOAL_COUNT], row,
                     result["provider_runtime"], replay=False)
    _bounds(plan, rows)
    _require(_same(result, _result(plan, rows, result["provider_runtime"], authorization, expected_authorization_sha256)),
             "retention result changed its plan/digest/metrics/claims")
    checked = []
    if replay:
        for index, (slot, row) in enumerate(zip(plan.proposal["ordered_slots"], rows, strict=True)):
            if row["kernel_checked"]:
                checked.append(validate_row(plan, slot["role"], slot["max_model_calls"], plan.goals[index % GOAL_COUNT],
                                            row, result["provider_runtime"], replay=True))
    _refresh(plan)
    return {"schema": VERIFY_SCHEMA, "status": "passed" if replay else "metadata-checked-native-replay-not-performed",
        "plan_sha256": plan.to_dict()["plan_sha256"], "evaluation_sha256": result["evaluation_sha256"],
        "verification_complete": replay, "proof_replay_performed": replay, "independently_replayed_proofs": checked,
        "metrics": result["metrics"], "model_outputs_regenerated": False,
        "historical_gpu_inference_attested": False, "claim_boundary": CLAIM, **CLAIMS}


def _reservation(record):
    """Validate the trusted caller's live observation, not a substitute ledger."""
    fields = {"status", "profile", "run_id", "stage", "job_id", "resource_request_sha256", "approval_sha256",
        "source_commit", "source_files_sha256", "payloads_sha256", "reservation", "allocation_elapsed_seconds",
        "allocation_remaining_seconds", "scientific_input", "automatic_retry", "resume"}
    _require(type(record) is dict and fields <= set(record), "trusted scheduler observation is incomplete")
    _require(record["status"] == "job-verified" and record["profile"] == "peano-hydra-retention-pilot-v1"
             and record["run_id"] == "retention-pilot-v1" and record["stage"] == "evaluate"
             and type(record["job_id"]) is str and record["job_id"].isascii() and record["job_id"].isdigit()
             and 1 <= len(record["job_id"]) <= 16
             and record["automatic_retry"] is False and record["resume"] is False
             and _same(record["reservation"], {"seconds": HARD_WALL_SECONDS, "gpus": 1, "cpus": 8, "memory_gib": 64}),
             "trusted scheduler observation changed exact job/profile/resources")
    for field in ("resource_request_sha256", "approval_sha256", "source_files_sha256", "payloads_sha256"):
        experiment.sha(record[field], "scheduler " + field)
    _require(type(record["source_commit"]) is str and len(record["source_commit"]) == 40
             and all(c in "0123456789abcdef" for c in record["source_commit"]), "scheduler source commit is malformed")
    for field in ("allocation_elapsed_seconds", "allocation_remaining_seconds"):
        _require(type(record[field]) in (int, float) and math.isfinite(record[field])
                 and 0 <= record[field] <= HARD_WALL_SECONDS, "scheduler allocation clock is malformed")
    _require(record["allocation_remaining_seconds"] == HARD_WALL_SECONDS - record["allocation_elapsed_seconds"],
             "scheduler elapsed/remaining allocation clocks differ")
    descriptor = record["scientific_input"]
    _keys(descriptor, {"path", "bytes", "sha256"}, "approved scientific input")
    _require(bridge._relative(descriptor["path"]).startswith("_deploy/hydra-retention-pilot-v1/"),
             "scientific input escaped the approved pilot package")
    _integer(descriptor["bytes"], "scientific input bytes", shared.MAX_MANIFEST_BYTES, 1)
    experiment.sha(descriptor["sha256"], "approved scientific input raw SHA")
    return json.loads(_canonical({key: value for key, value in record.items()
        if key not in {"allocation_elapsed_seconds", "allocation_remaining_seconds"}}))


def execute_evaluation(plan, *, authorization, expected_authorization_sha256, checkpoint_directory,
                       reservation_check, allocation_deadline, progress=None, stop_requested=None):
    """Explicit future inference, no model loading until all caller gates pass.

    The trusted callback owns the actual scheduler/ledger/approval checks.
    Its immutable identity is retained across all four model-loading arms.
    allocation_deadline is the caller's monotonic allocation-wide soft stop;
    the live scheduler elapsed clock can only shorten it, never extend it.
    """
    started = time.monotonic()
    _require(callable(reservation_check) and (stop_requested is None or callable(stop_requested)),
             "explicit trusted reservation gate and valid stop hook are required")
    authorization = validate_execution_authorization(plan, authorization,
        expected_authorization_sha256=expected_authorization_sha256)
    _require(type(allocation_deadline) in (int, float) and math.isfinite(allocation_deadline)
             and allocation_deadline <= started + MAX_AUTHORIZED_SECONDS,
             "explicit allocation-wide monotonic deadline required")
    deadline = min(allocation_deadline, started + authorization["max_wall_seconds"])
    reservation_identity = None
    def check_reservation():
        nonlocal deadline, reservation_identity
        observed = reservation_check(json.loads(_canonical(authorization)))
        identity = _reservation(observed)
        _require(reservation_identity is None or _same(identity, reservation_identity),
                 "trusted reservation changed immutable job/source/request identity")
        reservation_identity = identity
        deadline = min(deadline, time.monotonic() + MAX_AUTHORIZED_SECONDS - observed["allocation_elapsed_seconds"])
    def stopping():
        return (stop_requested is not None and stop_requested()) or time.monotonic() >= deadline

    def stop_before_loading():
        if stopping():
            raise cp.CheckpointPaused({"schema": _schema(plan, VERIFY_SCHEMA), "status": "stopped-before-model-loading",
                "completed_goal_records": 0, "total_goal_records": len(plan.proposal["ordered_slots"]),
                "checkpoint_created": False, "model_loaded": False, "verification_complete": False})

    # Validation/byte authentication can itself exhaust the reservation. Never
    # carry a stale stop decision across one of those boundaries into loading.
    stop_before_loading()
    check_reservation()
    stop_before_loading()
    _guard_output(Path(checkpoint_directory), plan)
    stop_before_loading()
    _refresh(plan)
    stop_before_loading()
    progress = progress or cp.Progress()
    progress.emit("retention-validation-complete", plan_sha256=plan.to_dict()["plan_sha256"])
    stop_before_loading()
    handles = {}
    for role, ref in zip(ROLES, (plan.baseline, plan.candidate), strict=True):
        handles[role] = ref.load()
        stop_before_loading()
    loaded_identities = {ROLES[0]: _training_identity("preserved-original-training-origin", handles[ROLES[0]].origin),
        ROLES[1]: _training_identity("authenticated-mixed-retention-training-artifact", handles[ROLES[1]].identity)}
    _require(_same(loaded_identities, plan.training_identities), "retention artifacts changed before loading")
    stop_before_loading()
    torch, transformers, peft = shared._model_runtime()
    stop_before_loading()
    runtime = {"torch_version": str(torch.__version__), "transformers_version": str(transformers.__version__),
        "peft_version": str(peft.__version__), "visible_cuda_devices": 1, "cuda_device": torch.cuda.get_device_name(0),
        "dtype": "bfloat16", "attention": "sdpa", "local_files_only": True, "model_loading": LOADING}
    _runtime(runtime)
    stop_before_loading()
    with EvaluationCheckpoint(checkpoint_directory, plan, expected_authorization_sha256=expected_authorization_sha256,
                              authorization=authorization, runtime=runtime, progress=progress) as store:
        def stop_boundary():
            if stopping() and len(store.rows) < store.total_goals:
                store.assert_unchanged()
                raise cp.CheckpointPaused(store.receipt(status="stopped-at-clean-boundary"))

        for role in ROLES:
            for budget in BUDGETS:
                model = tokenizer = None
                try:
                    stop_boundary()
                    _refresh(plan)
                    stop_boundary()
                    check_reservation()
                    stop_boundary()
                    shared._reset_seed(torch, transformers, experiment.SEED)
                    stop_boundary()
                    progress.emit("retention-model-loading-start", role=role, max_model_calls=budget)
                    stop_boundary()
                    tokenizer = transformers.AutoTokenizer.from_pretrained(str(handles[role].tokenizer_directory),
                        trust_remote_code=False, use_fast=True, local_files_only=True)
                    stop_boundary()
                    if tokenizer.pad_token_id is None:
                        _require(tokenizer.eos_token_id is not None, "pinned tokenizer lacks EOS/padding")
                        tokenizer.pad_token_id = tokenizer.eos_token_id
                    model = shared._load_base_model(torch, transformers, plan.to_dict()["execution_binding"]["contract"]["model"])
                    stop_boundary()
                    model = peft.PeftModel.from_pretrained(model, str(handles[role].adapter_directory), is_trainable=False)
                    stop_boundary()
                    model.to("cuda:0")
                    stop_boundary()
                    model.eval()
                    stop_boundary()
                    progress.emit("retention-model-loading-complete", role=role, max_model_calls=budget)
                    goal_started = [0.0, 0.0]
                    def begin(goal):
                        stop_boundary()
                        store.begin(role, "calls-" + str(budget), goal)
                        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats(0)
                        goal_started[:] = [time.monotonic(), time.process_time()]
                        progress.emit("retention-goal-start", role=role, max_model_calls=budget, goal=goal["name"],
                                      completed=len(store.rows), total=store.total_goals)
                    def committed(row):
                        torch.cuda.synchronize()
                        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                        resources = {"goal_wall_seconds": time.monotonic() - goal_started[0],
                            "goal_cpu_seconds": time.process_time() - goal_started[1],
                            "process_peak_rss_bytes": int(rss if sys.platform == "darwin" else rss * 1024),
                            "cuda_peak_allocated_bytes": int(torch.cuda.max_memory_allocated(0)),
                            "cuda_peak_reserved_bytes": int(torch.cuda.max_memory_reserved(0))}
                        store.append({**row, "resources": resources})
                        progress.emit("retention-goal-committed", role=role, max_model_calls=budget, goal=row["goal"],
                            completed=len(store.rows), total=store.total_goals, status=row["status"],
                            model_generate_calls=row["model_generate_calls"], checkpoint_head_sha256=store.head["head_sha256"])
                    for offset in range(0, len(plan.goals), CHUNK_GOALS):
                        goals = plan.goals[offset:offset + CHUNK_GOALS]
                        view = _view(plan, budget, goals)
                        _require(len(goals) * budget <= shared.MAX_MODEL_CALLS_PER_LANE, "chunk exceeds inherited call cap")
                        shared._run_model_lane(view, model=model, tokenizer=tokenizer, lane="trained",
                            provider=_provider(plan, role, budget, runtime), on_goal_start=begin, on_goal=committed,
                            search_profile=CONTEXT_ALPHA_V1)
                finally:
                    model = tokenizer = None
                    from training.peano_policy.authority_runtime import clear_authority_runtime_cache
                    clear_authority_runtime_cache()
                    shared._release_gpu(torch)
        store.assert_unchanged()
        _refresh(plan)
        result = _result(plan, store.rows, runtime, authorization, expected_authorization_sha256)
        verify_result(plan, result, expected_authorization_sha256=expected_authorization_sha256, replay=False)
        progress.emit("retention-evaluation-complete", completed=len(store.rows), total=store.total_goals,
                      evaluation_sha256=result["evaluation_sha256"])
        return result
