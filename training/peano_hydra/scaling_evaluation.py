"""Explicit FRONTIER old/new x eight/sixteen evaluation; no implicit execution.

Binding reuses externally anchored, originally validated training origins. It
does not regenerate a corpus, grant an allocation, fabricate a human review,
or accept historical checkpoints. A future trained candidate needs its own
completed origin receipt AND its still-matching FRONTIER admission sidecars.
The old epoch remains an origin; execution uses the candidate epoch and the
common finite V4/no-import authority, without an epoch-equivalence claim.

Only execute_evaluation loads models. It requires a separately pinned explicit
authorization and a caller's trusted reservation gate. That gate/authorization
is not hardware attestation. Offline verification authenticates ALL metadata
before running the existing bounded original-goal replay workers.
"""

from __future__ import annotations

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
from training.peano_hydra import scaling_admission as admission, scaling_experiment as experiment
from training.peano_hydra.policy import ProposalRecord
from training.peano_hydra.runner import policy_environment, HYDRA_PROFILED_RUNNER_VERSION, SURFACE_MACRO_V0_INELIGIBILITY
from training.peano_policy.authority import AUTHORITY_PRIMITIVE_PROFILE, authority_contract_record, authority_profile_record, validate_authority_tactic
from training.peano_policy.contract import authority_prompt_environment
from training.peano_policy.prompt import CapabilityIdentity
from training.peano_policy.search import SearchLimits
from training.peano_policy.state_identity import CONTEXT_ALPHA_V1, StateIdentityReport, search_profile_contract


ROOT = Path(__file__).absolute().parents[2]
PLAN_SCHEMA = "peano-hydra-frontier-bound-evaluation-v1"
RESULT_SCHEMA = "peano-hydra-frontier-evaluation-results-v1"
VERIFY_SCHEMA = "peano-hydra-frontier-evaluation-verification-v1"
AUTHORIZATION_SCHEMA = "peano-hydra-frontier-evaluation-authorization-v1"
HEADER_SCHEMA = "peano-hydra-frontier-evaluation-checkpoint-header-v1"
HEAD_SCHEMA = "peano-hydra-frontier-evaluation-checkpoint-head-v1"
ROW_SCHEMA = "peano-hydra-frontier-evaluation-checkpoint-row-v1"
BENCHMARK_SCHEMAS = {
    PLAN_SCHEMA: "peano-hydra-frontier-benchmark-bound-evaluation-v2",
    RESULT_SCHEMA: "peano-hydra-frontier-benchmark-evaluation-results-v2",
    VERIFY_SCHEMA: "peano-hydra-frontier-benchmark-evaluation-verification-v2",
    HEADER_SCHEMA: "peano-hydra-frontier-benchmark-checkpoint-header-v2",
    HEAD_SCHEMA: "peano-hydra-frontier-benchmark-checkpoint-head-v2",
    ROW_SCHEMA: "peano-hydra-frontier-benchmark-checkpoint-row-v2",
}
ROLES = ("saved-corrected", "new-frontier")
BUDGETS = (8, 16)
CHUNK_GOALS = 8
MAX_GOALS = 32
MAX_REPORT_BYTES = 48 * 1024**2
MAX_CHECKPOINT_BYTES = 48 * 1024**2
MAX_AUTHORIZED_SECONDS = 7200
LOADING = "sequential-fresh-pinned-base-plus-role-lora-for-each-budget-unload"
CLAIM = ("Public, correlated FRONTIER DEV diagnostics; separately preserved training origins, "
         "candidate-epoch native execution and common V4/no-import authority. No unseen or sealed "
         "benchmark, engine/epoch equivalence, proof optimality, human-identity or GPU attestation.")
SOURCE_COVERAGE = ("Listed runner, generation, authority, checkpoint, origin/admission validation and "
                   "native kernel/engine files; not whole-repository or hardware attestation. "
                   "The earlier candidate/data/plan source inventory remains a separate immutable input.")
EXTRA_SOURCES = (
    "training/peano_hydra/scaling_evaluation.py", "training/peano_hydra/scaling_experiment.py",
    "training/peano_hydra/scaling_admission.py", "training/peano_hydra/scaling_lineage.py",
    "training/peano_hydra/origin_bridge.py", "training/peano_hydra/comparison.py",
    "training/peano_hydra/comparison_checkpoint.py", "training/peano_hydra/paired_checkpoint.py",
    "training/peano_hydra/corrective_workflow.py", "training/peano_hydra/review_runtime.py",
    "training/peano_hydra/__init__.py", "training/peano_policy/__init__.py",
    "training/peano_policy/pretrained_baseline.py", "training/peano_policy/evaluation_replay.py",
    "scripts/hydra_bounded_exec.py",
    "training/peano_hydra/frontier_benchmark_candidates.py",
    "training/peano_hydra/frontier_benchmark_audit.py",
    "training/peano_hydra/frontier_benchmark_protocol.py",
    "training/peano_hydra/frontier_benchmark_run.py",
    "training/peano_hydra/frontier_pilot_launch.py",
    "scripts/eval_peano_hydra_frontier_benchmark.py",
)
_canonical, _digest = shared._canonical, shared._digest
_require, _same, _keys, _integer = capacity._require, capacity._same, capacity._keys, capacity._integer


def _read(path, expected=None, maximum=shared.MAX_MANIFEST_BYTES):
    raw = bridge._read(Path(path), maximum)
    if expected is not None:
        experiment.sha(expected, "external raw input SHA")
        _require(hashlib.sha256(raw).hexdigest() == expected, "externally anchored evaluation input changed")
    return bridge._decode(raw, maximum, "FRONTIER evaluation input"), raw


@dataclass(frozen=True, slots=True)
class OriginReference:
    request: bridge.OriginRequest
    receipt_path: Path
    receipt_sha256: str

    def __post_init__(self):
        _require(type(self.request) is bridge.OriginRequest, "origin needs its explicit preserved request")
        object.__setattr__(self, "receipt_path", bridge._absolute(self.receipt_path))
        experiment.sha(self.receipt_sha256, "external origin receipt SHA")

    def load(self):
        return bridge.load_origin_receipt(self.receipt_path, expected_receipt_sha256=self.receipt_sha256,
                                          request=self.request)

    def to_dict(self):
        return {"request": self.request.to_dict(), "receipt_sha256": self.receipt_sha256}


def execution_sources():
    """Separate execution inventory; never extend/reseal a candidate's sources."""
    result = capacity._sources(authority_profile=AUTHORITY_PRIMITIVE_PROFILE)
    for name in EXTRA_SOURCES:
        result[name] = hashlib.sha256(bridge._read(ROOT / name, 2 * 1024**2)).hexdigest()
    _require(len(result) <= capacity.MAX_SOURCE_FILES, "FRONTIER execution inventory exceeds its bound")
    return dict(sorted(result.items()))


def _caps(authority):
    _keys(authority, {"capabilities", "environment_sha256", "classical"}, "FRONTIER native authority")
    names = ("label", "allowed_commands", "allowed_theorems")
    _keys(authority["capabilities"], set(names), "FRONTIER capability record")
    # Artifact JSON is key-sorted; prompt transport deliberately orders these
    # fields. Reconstruct that transport without changing any bound values.
    identity = CapabilityIdentity.from_record({key: authority["capabilities"][key] for key in names})
    _require(identity.allowed_commands == tuple(sorted(MODEL_V1_COMMANDS))
             and identity.allowed_theorems == () and authority["classical"] is False,
             "FRONTIER evaluation requires the exact finite primitive authority and no imports")
    caps = SurfaceCapabilities(label=identity.label, allowed_commands=MODEL_V1_COMMANDS,
                               allowed_theorems=frozenset())
    environment = authority_prompt_environment(False, identity)
    _require(environment.sha256 == authority["environment_sha256"], "FRONTIER authority environment changed")
    return caps, environment


def _candidate_metadata(reference, origin):
    """The generic origin cache does not cover sibling admission sidecars."""
    request = reference.request
    with bridge._Tree(request.source_root) as tree:
        relative = request.to_dict()["preparation_relative_path"]
        prepared = bridge._decode(tree.read(relative + "/manifest.json", shared.MAX_MANIFEST_BYTES),
                                  shared.MAX_MANIFEST_BYTES, "reviewed candidate preparation")
        source_relative = bridge._relative(prepared["source"]["directory"])
        source = request.source_root / source_relative
        source_manifest = bridge._decode(tree.read(source_relative + "/manifest.json", shared.MAX_MANIFEST_BYTES),
                                         shared.MAX_MANIFEST_BYTES, "candidate source manifest")
        sidecars = {}
        for name in (*sorted(admission.METADATA_FILES), "training-admission.json"):
            raw = tree.read((Path(source_relative).parent / name).as_posix(), admission.MAX_METADATA_BYTES)
            sidecars[name] = {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
        ready = bridge._decode(tree.read((Path(source_relative).parent / "candidate-readiness.json").as_posix(),
                                        admission.MAX_METADATA_BYTES), admission.MAX_METADATA_BYTES, "candidate readiness")
        checked_admission = admission.admission_identity(source)
        tree.assert_unchanged()
    adapter, _ = _read(request.adapter_manifest, request.adapter_manifest_sha256)
    identity = prepared.get("curriculum_identity")
    _require(type(identity) is dict and identity.get("source_schema") == admission.SOURCE_SCHEMA
             and _same(identity, adapter.get("curriculum_identity"))
             and _same(identity.get("review_admission"), checked_admission)
             and identity.get("projection_policy") == admission.PROJECTION_POLICY,
             "candidate lost its exact reviewed FRONTIER admission/projection")
    _require(source_manifest.get("schema") == admission.SOURCE_SCHEMA
             and prepared["source"]["manifest_sha256"] == checked_admission["source_manifest_sha256"]
             and origin["preparation_manifest_sha256"] == request.preparation_manifest_sha256
             and prepared["epoch_sha256"] == origin["epoch_sha256"], "candidate source/preparation/origin identity differs")
    return prepared, source_manifest, checked_admission, ready, sidecars, source


@dataclass(frozen=True, slots=True)
class BoundEvaluation:
    evaluation_path: Path
    evaluation_raw_sha256: str
    baseline: OriginReference
    candidate: OriginReference
    _record_json: str
    benchmark_reference: object | None = None

    def to_dict(self):
        return json.loads(self._record_json)

    @property
    def proposal(self):
        return self.to_dict()["evaluation_plan"]

    @property
    def goals(self):
        return tuple(self.proposal["goals"])

    @property
    def origins(self):
        return self.to_dict()["training_origins"]


def _schema(plan, legacy):
    return (BENCHMARK_SCHEMAS[legacy]
            if plan.proposal["schema"] == experiment.BENCHMARK_EVALUATION_SCHEMA else legacy)


def _claim(plan):
    return plan.to_dict()["claim_boundary"]


def bind_evaluation(evaluation_plan_path, *, expected_evaluation_plan_sha256, baseline, candidate,
                    benchmark_reference=None):
    """Explicit byte/metadata admission; fresh native origin receipts are prerequisites.

    The supplied evaluation-plan SHA is RAW file bytes. No model, corpus
    regeneration, native proof execution, allocation or output write occurs.
    """
    _require(type(baseline) is OriginReference and type(candidate) is OriginReference,
             "both roles require externally pinned independently authenticated origins")
    path = bridge._absolute(Path(evaluation_plan_path))
    proposal, raw = _read(path, expected_evaluation_plan_sha256, experiment.MAX_RECORD_BYTES)
    experiment.validate_evaluation_plan(proposal)
    is_benchmark = proposal["schema"] == experiment.BENCHMARK_EVALUATION_SCHEMA
    benchmark = None
    if is_benchmark:
        from training.peano_hydra.frontier_benchmark_protocol import BenchmarkReference
        _require(type(benchmark_reference) is BenchmarkReference,
                 "versioned benchmark evaluation requires an externally pinned human review")
        benchmark = benchmark_reference.load()
    else:
        _require(benchmark_reference is None, "legacy DEV plans cannot acquire benchmark status")
    allowed_cohort = (proposal["cohort"] in experiment.BENCHMARK_COHORTS if is_benchmark
                      else proposal["cohort"] == "review-candidate-dev")
    _require(allowed_cohort and proposal["roles"] == list(ROLES)
             and proposal["budgets"] == list(BUDGETS) and 1 <= len(proposal["goals"]) <= MAX_GOALS,
             "evaluation must match its separately versioned bounded factorial cohort")
    for goal in proposal["goals"]:
        _require(all(0 < len(goal[key].encode()) <= 4096 for key in ("source", "statement")),
                 "FRONTIER goal exceeds the existing independent replay's 4KiB boundary")
    before = execution_sources()
    handles = {role: ref.load() for role, ref in zip(ROLES, (baseline, candidate), strict=True)}
    origins = {role: handle.origin for role, handle in handles.items()}
    prepared, source, admitted, ready, sidecars, source_path = _candidate_metadata(candidate, origins[ROLES[1]])
    if not is_benchmark:
        _require(ready["files"]["evaluation-plan.json"] == {"bytes": len(raw), "sha256": expected_evaluation_plan_sha256},
                 "evaluation is not the exact preregistered candidate DEV plan")
    else:
        context = {
            "benchmark_manifest_sha256": benchmark["manifest_file_sha256"],
            "benchmark_audit_sha256": benchmark["audit_file_sha256"],
            "benchmark_review_sha256": benchmark["review_file_sha256"],
            "heldout_goals_sha256": benchmark["heldout_goals_sha256"],
            "candidate_readiness_sha256": sidecars["candidate-readiness.json"]["sha256"],
        }
        _require(_same(proposal["benchmark_context"], context)
                 and proposal["epoch_sha256"] == benchmark["epoch_sha256"],
                 "benchmark review, native epoch or candidate readiness changed")
        if proposal["cohort"] == "frontier-heldout-candidate32":
            _require(_same(proposal["goals"], benchmark["primary_goals"]),
                     "held-out evaluation changed its fixed primary goal projection")
        old_prepared, _ = _read(baseline.request.preparation_directory / "manifest.json",
                                baseline.request.preparation_manifest_sha256)
        _require(admitted["source_manifest_sha256"] in benchmark["audited_file_sha256"]
                 and old_prepared["source"]["manifest_sha256"] in benchmark["audited_file_sha256"],
                 "exposure audit does not cover the actual old and new native training sources")
        excluded = benchmark["primary_goals"] + benchmark["reserved_goals"]
        source_routes = source["composition"]["plan"]["routes"]
        _require(not ({g["statement_sha256"] for g in excluded}
                       & {g["statement_sha256"] for g in source_routes})
                 and not ({g["lineage_sha256"] for g in excluded}
                           & {g["lineage_sha256"] for g in source_routes}),
                 "benchmark primary/reserved families must remain outside all model-facing source splits")
    _require(proposal["baseline_adapter_manifest_sha256"] == origins[ROLES[0]]["adapter_manifest_sha256"]
             and origins[ROLES[0]]["adapter_manifest_sha256"] != origins[ROLES[1]]["adapter_manifest_sha256"],
             "old/new role bindings do not identify the declared distinct adapters")
    _require(proposal["epoch_sha256"] == origins[ROLES[1]]["epoch_sha256"] == admitted["bindings"]["epoch_sha256"]
             and proposal["authority_sha256"] == admitted["bindings"]["authority_sha256"] == _digest(prepared["authority"])
             and proposal["lineage_proposal_sha256"] == admitted["proposal_sha256"]
             and proposal["source_files_sha256"] == admitted["bindings"]["execution_source_files_sha256"]
             == _digest(ready["source_files"]), "candidate plan/admission/epoch/authority join differs")
    pilot = experiment.build_pilot_plan(run_id="frontier-" + ready["profile"] + "-v1", profile=ready["profile"],
        source_manifest_sha256=admitted["source_manifest_sha256"], shard_manifest_sha256=ready["shard_manifest_sha256"],
        lineage_proposal_sha256=admitted["proposal_sha256"], epoch_sha256=proposal["epoch_sha256"],
        authority_sha256=proposal["authority_sha256"], baseline_adapter_manifest_sha256=proposal["baseline_adapter_manifest_sha256"],
        split_rows={key: ready["split_rows"][key] for key in ("train", "dev", "quarantine")})
    _require(proposal["candidate_training_plan_sha256"] == pilot["plan_sha256"]
             and ready["files"]["pilot-plan.json"] == {"bytes": len(_canonical(pilot)) + 1,
                                                       "sha256": hashlib.sha256(_canonical(pilot) + b"\n").hexdigest()},
             "candidate pilot identity was substituted")
    if not is_benchmark:
        routes = {r["name"]: r for r in source["composition"]["plan"]["routes"] if r["split"] == "dev"}
        for goal in proposal["goals"]:
            _require(goal["name"] in routes and _same(goal, {key: routes[goal["name"]][key] for key in goal})
                     and goal["name"] in prepared["splits"]["dev"]["theorems"]
                     and goal["lineage_sha256"] not in prepared["splits"]["train"]["lineages"],
                     "evaluation goal is not its exact reviewed DEV route")
    caps, environment = _caps(prepared["authority"])
    prompt, decoder = authority_contract_record(), authority_profile_record(environment)
    model = {"model_id": experiment.MODEL_ID, "revision": experiment.MODEL_REVISION}
    for origin in origins.values():
        _require(origin["training_authority_profile"] == AUTHORITY_PRIMITIVE_PROFILE
                 and _same(origin["model"], model) and _same(origin["training_prompt_contract"], prompt)
                 and _same(origin["training_decoder_profile"], decoder),
                 "training origins do not share the exact pinned model/V4/no-import contract")
    _require(_same(origins[ROLES[0]]["artifacts"]["tokenizer"], origins[ROLES[1]]["artifacts"]["tokenizer"]),
             "matched roles changed the tokenizer artifact bytes")
    contract = {"schema": "peano-hydra-frontier-budget-execution-contract-v1",
        "evaluation_plan_sha256": proposal["plan_sha256"], "evaluation_raw_sha256": expected_evaluation_plan_sha256,
        "training_origins": {role: value["origin_sha256"] for role, value in origins.items()},
        "execution_epoch_sha256": proposal["epoch_sha256"], "model": model,
        "environment": policy_environment(caps), "authority_profile": AUTHORITY_PRIMITIVE_PROFILE,
        "prompt_contract": prompt, "decoder_profile": decoder, "search_profile": search_profile_contract(CONTEXT_ALPHA_V1),
        "fixed_search": proposal["fixed_search"], "budgets": list(BUDGETS), "chunk_goals": CHUNK_GOALS,
        "goal_set_sha256": proposal["goal_set_sha256"], "order": "role-budget-goal",
        "candidate_admission": admitted, "model_loading": LOADING,
        "engine_or_epoch_equivalence_claimed": False, "historical_checkpoint_reuse_allowed": False}
    binding = bridge.execution_binding(source_root=ROOT, source_files=before, contract=contract)
    record = {"schema": BENCHMARK_SCHEMAS[PLAN_SCHEMA] if is_benchmark else PLAN_SCHEMA,
        "evaluation_plan": proposal, "evaluation_raw_sha256": expected_evaluation_plan_sha256,
        "training_origins": origins, "origin_references": {role: ref.to_dict() for role, ref in zip(ROLES, (baseline, candidate), strict=True)},
        "execution_binding": binding, "execution_sources": before, "source_coverage": SOURCE_COVERAGE,
        "candidate_admission_sidecars": sidecars, "candidate_source_relative": source_path.relative_to(candidate.request.source_root).as_posix(),
        "claim_boundary": benchmark["claim_boundary"] if is_benchmark else CLAIM,
        "max_report_bytes": MAX_REPORT_BYTES, "max_checkpoint_bytes": MAX_CHECKPOINT_BYTES,
        "max_goal_evidence_bytes": shared.MAX_GOAL_EVIDENCE_BYTES, "max_chunk_evidence_bytes": shared.MAX_LANE_EVIDENCE_BYTES,
        "offline_replay_limits": capacity.REPLAY_LIMITS.to_dict(), "gpu_execution_authorized": False,
        "training_authorized": False, "resume_allowed": False, "research_claim_eligible": False}
    if is_benchmark:
        record["benchmark_reference"] = benchmark_reference.to_dict()
        record["benchmark_review"] = benchmark
        _require(_same(benchmark_reference.load(), benchmark), "benchmark evidence changed during binding")
    _require(_same(before, execution_sources()) and bridge._read(path, experiment.MAX_RECORD_BYTES) == raw,
             "evaluation execution source or preregistered plan changed while binding")
    _require(_same(admission.admission_identity(source_path), admitted), "candidate admission changed during binding")
    for role, ref in zip(ROLES, (baseline, candidate), strict=True):
        _require(_same(ref.load().origin, origins[role]), "training origin changed during binding")
    record["plan_sha256"] = _digest(record)
    _require(len(_canonical(record)) <= cp.MAX_HEADER_BYTES // 2, "bound evaluation metadata exceeds its header reservation")
    return BoundEvaluation(path, expected_evaluation_plan_sha256, baseline, candidate,
                           _canonical(record).decode(), benchmark_reference)


def _refresh(plan):
    _require(type(plan) is BoundEvaluation, "evaluation needs its exact authenticated binding")
    fresh = bind_evaluation(plan.evaluation_path, expected_evaluation_plan_sha256=plan.evaluation_raw_sha256,
                            baseline=plan.baseline, candidate=plan.candidate,
                            benchmark_reference=plan.benchmark_reference)
    _require(_same(fresh.to_dict(), plan.to_dict()), "FRONTIER evaluation input/source/origin binding changed")


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
    _require(type(plan) is BoundEvaluation and type(budget) is int and budget in BUDGETS, "unknown bound budget")
    goals = plan.goals if goals is None else tuple(goals)
    return _Execution(plan, budget, _canonical(goals).decode())


def _runtime(record):
    _keys(record, {"torch_version", "transformers_version", "peft_version", "visible_cuda_devices", "cuda_device",
                   "dtype", "attention", "local_files_only", "model_loading"}, "FRONTIER runtime")
    _require(all(type(record[k]) is str and 1 <= len(record[k]) <= 256 for k in (
        "torch_version", "transformers_version", "peft_version", "cuda_device"))
        and type(record["visible_cuda_devices"]) is int and record["visible_cuda_devices"] == 1
        and record["dtype"] == "bfloat16" and record["attention"] == "sdpa"
        and record["local_files_only"] is True and record["model_loading"] == LOADING,
        "runtime changed the single-GPU/local-only/precision/loading contract")


def _provider(plan, role, budget, runtime):
    _require(type(role) is str and role in ROLES and type(budget) is int and budget in BUDGETS, "unknown role/budget")
    _runtime(runtime)
    return {"kind": "preserved-origin-frontier-budget-v1", "adapter_attached": True,
        "model": _view(plan, budget).model, "training_origin": plan.origins[role], "role": role,
        "max_model_calls": budget, "search_profile": search_profile_contract(CONTEXT_ALPHA_V1),
        "execution_binding_sha256": plan.to_dict()["execution_binding"]["execution_binding_sha256"],
        "runtime": runtime, "research_claim_eligible": False}


def _proposals(view, goal, row, provider):
    # Intentionally local and budget-aware. The historical capacity validator
    # retains its exact eight-call/32-sequence limits and serialized identities.
    identity = capacity._policy_identity(view, goal, "trained", provider)
    evidence = row["evidence"]
    _require(_same(row["policy_identity"], identity) and _same(evidence["policy_identity"], identity), "policy/provider identity changed")
    records, head = evidence["proposal_records"], identity["heads"][0]
    _require(type(records) is list and len(records) == row["model_generate_calls"], "proposal/call count differs")
    candidates = 0
    for number, record in enumerate(records, 1):
        _keys(record, {"portfolio_call", "head", "role", "head_identity_sha256", "goals", "state_sha256", "quota",
                       "requested", "outcome", "candidates", "accepted_candidates", "suppressed_duplicates",
                       "response_sha256", "error_type", "error"}, "FRONTIER proposal")
        _require(type(record["goals"]) is list and 1 <= len(record["goals"]) <= 64
                 and type(record["candidates"]) is list and len(record["candidates"]) <= 4
                 and type(record["accepted_candidates"]) is list, "proposal inventory bound changed")
        ProposalRecord(**{**record, **{k: tuple(record[k]) for k in ("goals", "candidates", "accepted_candidates")}})
        _require(type(record["portfolio_call"]) is int and record["portfolio_call"] == number
                 and record["head"] == head["name"] and record["role"] == "control"
                 and record["head_identity_sha256"] == head["identity_sha256"] and record["outcome"] == "ok"
                 and type(record["quota"]) is int and type(record["requested"]) is int
                 and record["quota"] == record["requested"] == 4, "proposal head/order/quota changed")
        _require(all(type(c) is str and 0 < len(c.encode()) <= 4096 for c in record["candidates"]), "candidate text exceeds bound")
        unique = list(dict.fromkeys(record["candidates"]))
        _require(record["accepted_candidates"] == unique and type(record["suppressed_duplicates"]) is int
                 and record["suppressed_duplicates"] == len(record["candidates"]) - len(unique)
                 and record["response_sha256"] == _digest(record["candidates"]), "candidate merge/hash differs")
        candidates += len(record["candidates"])
    generation = row["generation"]
    _keys(generation, {"model_generate_calls", "candidate_sequences_requested", "candidate_sequences_returned",
        "candidate_lines_returned", "malformed_sequences_rejected", "authority_sequences_rejected",
        "one_batched_call_per_search_state"}, "FRONTIER generation")
    for field in generation.keys() - {"one_batched_call_per_search_state"}:
        _integer(generation[field], field, view.budget * 4)
    _require(generation["model_generate_calls"] == row["model_generate_calls"]
             and generation["candidate_sequences_requested"] == generation["candidate_sequences_returned"] == 4 * len(records)
             and generation["candidate_lines_returned"] == candidates
             and generation["malformed_sequences_rejected"] + generation["authority_sequences_rejected"] == 4 * len(records) - candidates
             and generation["one_batched_call_per_search_state"] is True, "generation accounting differs")
    environment = authority_prompt_environment(False, CapabilityIdentity.from_record(view.environment["capabilities"]))
    for record in records:
        for command in record["candidates"]:
            validate_authority_tactic(command, environment)
    return records


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


def _bounds(plan, rows):
    _require(type(rows) is list and len(rows) <= len(plan.proposal["ordered_slots"]), "checkpoint row count exceeds plan")
    _require(sum(row["model_generate_calls"] for row in rows) <= plan.proposal["max_model_calls_total"], "whole evaluation call bound exceeded")
    count = len(plan.goals)
    for arm in range(0, len(rows), count):
        for offset in range(arm, min(arm + count, len(rows)), CHUNK_GOALS):
            group = rows[offset:min(offset + CHUNK_GOALS, arm + count)]
            _require(sum(row["model_generate_calls"] for row in group) <= shared.MAX_MODEL_CALLS_PER_LANE
                     and sum(len(_canonical(row["evidence"])) for row in group) <= shared.MAX_LANE_EVIDENCE_BYTES,
                     "eight-goal chunk exceeds inherited call/evidence reservation")


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
            super().__init__(Path(path), plan, plan.origins, runtime=runtime, resume=False, progress=progress)
            return
        _require(authorization is None and runtime is None, "read-only verification uses saved metadata, not replacements")
        paired._model_free()
        self.path, self.plan, self.origins = bridge._absolute(Path(path)), plan, plan.origins
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
            "training_origin_sha256": self.plan.origins[slot["role"]]["origin_sha256"]}

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
            "historical_gpu_inference_attested": False, "research_claim_eligible": False, "claim_boundary": self.claim}


def verify_checkpoint(plan, directory, *, expected_authorization_sha256, replay=True, progress=None):
    """Read-only committed prefix; never retry an interrupted in-flight goal."""
    with EvaluationCheckpoint(directory, plan, expected_authorization_sha256=expected_authorization_sha256,
                              verify_only=True, replay_proofs=replay, progress=progress) as store:
        return store.receipt()


def _outcomes(plan, rows):
    result = []
    for slot, row in zip(plan.proposal["ordered_slots"], rows):
        status = "proof" if row["kernel_checked"] else "exhausted" if row["status"] == "exhausted" else (
            "call-limit" if row["model_generate_calls"] == slot["max_model_calls"] else "unknown")
        result.append({**slot, "status": status, "model_generate_calls": row["model_generate_calls"],
            "tactic_decisions": row["tactic_decisions"] if row["kernel_checked"] else None,
            "proof_nodes": row["proof_nodes"], "commands_sha256": row["commands_sha256"]})
    return result


def _result(plan, rows, runtime, authorization, authorization_sha):
    _require(len(rows) == len(plan.proposal["ordered_slots"]), "partial prefix cannot manufacture a final evaluation")
    result = {"schema": _schema(plan, RESULT_SCHEMA), "status": "executed", "plan": plan.to_dict(), "provider_runtime": runtime,
        "authorization": authorization, "authorization_sha256": authorization_sha, "rows": rows,
        "metrics": experiment.summarize_outcomes(plan.proposal, _outcomes(plan, rows)),
        "model_outputs_regenerated": False, "historical_gpu_inference_attested": False,
        "research_claim_eligible": False, "sealed_benchmark": False, "claim_boundary": _claim(plan)}
    result["evaluation_sha256"] = _digest(result)
    _require(len(_canonical(result)) <= MAX_REPORT_BYTES, "final evaluation exceeds retained-byte reservation")
    return result


def verify_result(plan, result, *, expected_authorization_sha256, replay=True):
    """Validate every row before any bounded native replay, then recheck inputs."""
    _require(type(replay) is bool, "replay choice must be Boolean")
    if replay: paired._model_free()
    _refresh(plan)
    _require(len(_canonical(result)) <= MAX_REPORT_BYTES, "report exceeds byte bound")
    result = shared._json_object(_canonical(result), description="FRONTIER report")
    _keys(result, {"schema", "status", "plan", "provider_runtime", "authorization", "authorization_sha256", "rows",
                  "metrics", "model_outputs_regenerated", "historical_gpu_inference_attested", "research_claim_eligible",
                  "sealed_benchmark", "claim_boundary", "evaluation_sha256"}, "FRONTIER report")
    authorization = validate_execution_authorization(plan, result["authorization"],
        expected_authorization_sha256=expected_authorization_sha256)
    _require(result["authorization_sha256"] == expected_authorization_sha256 and _same(result["plan"], plan.to_dict()),
             "report plan/authorization differs")
    _runtime(result["provider_runtime"])
    rows = result["rows"]
    _require(type(rows) is list and len(rows) == len(plan.proposal["ordered_slots"]), "final report is missing prescribed rows")
    for index, (slot, row) in enumerate(zip(plan.proposal["ordered_slots"], rows, strict=True)):
        validate_row(plan, slot["role"], slot["max_model_calls"], plan.goals[index % len(plan.goals)], row,
                     result["provider_runtime"], replay=False)
    _bounds(plan, rows)
    _require(_same(result, _result(plan, rows, result["provider_runtime"], authorization, expected_authorization_sha256)),
             "report digest, derived metrics or claim boundary changed")
    checked = []
    if replay:
        for index, (slot, row) in enumerate(zip(plan.proposal["ordered_slots"], rows, strict=True)):
            if row["kernel_checked"]:
                checked.append(validate_row(plan, slot["role"], slot["max_model_calls"], plan.goals[index % len(plan.goals)],
                                            row, result["provider_runtime"], replay=True))
    _refresh(plan)
    return {"schema": _schema(plan, VERIFY_SCHEMA), "status": "passed" if replay else "metadata-checked-native-replay-not-performed",
        "plan_sha256": plan.to_dict()["plan_sha256"], "evaluation_sha256": result["evaluation_sha256"],
        "verification_complete": replay, "proof_replay_performed": replay, "independently_replayed_proofs": checked,
        "metrics": result["metrics"], "model_outputs_regenerated": False,
        "historical_gpu_inference_attested": False, "research_claim_eligible": False, "claim_boundary": _claim(plan)}


def _guard_output(path, plan):
    from training.peano_hydra import corrective_workflow as files
    roots = []
    for ref in (plan.baseline, plan.candidate):
        roots.extend((ref.request.source_root, ref.request.adapter_manifest.parent, ref.receipt_path.parent))
    roots.append(plan.evaluation_path.parent)
    if plan.benchmark_reference is not None:
        roots.extend(plan.benchmark_reference.protected_paths())
    return files.guard_output(path, protected=roots)


def execute_evaluation(plan, *, authorization, expected_authorization_sha256, checkpoint_directory,
                       reservation_check, progress=None, stop_requested=None):
    """Explicit future inference, no model loading until all caller gates pass.

    reservation_check must be the host's trusted exact-job/budget checker; it
    may raise but must not allocate/retry/upload. The external reservation owns
    the hard wall limit. This API stops only at safe between-goal boundaries.
    """
    started = time.monotonic()
    _require(callable(reservation_check) and (stop_requested is None or callable(stop_requested)),
             "explicit trusted reservation gate and valid stop hook are required")
    authorization = validate_execution_authorization(plan, authorization,
        expected_authorization_sha256=expected_authorization_sha256)
    def stopping():
        return (stop_requested is not None and stop_requested()) or time.monotonic() - started >= authorization["max_wall_seconds"]

    def stop_before_loading():
        if stopping():
            raise cp.CheckpointPaused({"schema": _schema(plan, VERIFY_SCHEMA), "status": "stopped-before-model-loading",
                "completed_goal_records": 0, "total_goal_records": len(plan.proposal["ordered_slots"]),
                "checkpoint_created": False, "model_loaded": False, "verification_complete": False})

    # Validation/byte authentication can itself exhaust the reservation. Never
    # carry a stale stop decision across one of those boundaries into loading.
    stop_before_loading()
    reservation_check(json.loads(_canonical(authorization)))
    stop_before_loading()
    _guard_output(Path(checkpoint_directory), plan)
    stop_before_loading()
    _refresh(plan)
    stop_before_loading()
    progress = progress or cp.Progress()
    progress.emit("frontier-validation-complete", plan_sha256=plan.to_dict()["plan_sha256"])
    stop_before_loading()
    handles = {}
    for role, ref in zip(ROLES, (plan.baseline, plan.candidate), strict=True):
        handles[role] = ref.load()
        stop_before_loading()
    _require(all(_same(handles[role].origin, plan.origins[role]) for role in ROLES), "model origins changed before loading")
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
                    reservation_check(json.loads(_canonical(authorization)))
                    stop_boundary()
                    shared._reset_seed(torch, transformers, experiment.SEED)
                    stop_boundary()
                    progress.emit("frontier-model-loading-start", role=role, max_model_calls=budget)
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
                    progress.emit("frontier-model-loading-complete", role=role, max_model_calls=budget)
                    goal_started = [0.0, 0.0]
                    def begin(goal):
                        stop_boundary()
                        store.begin(role, "calls-" + str(budget), goal)
                        torch.cuda.synchronize(); torch.cuda.reset_peak_memory_stats(0)
                        goal_started[:] = [time.monotonic(), time.process_time()]
                        progress.emit("frontier-goal-start", role=role, max_model_calls=budget, goal=goal["name"],
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
                        progress.emit("frontier-goal-committed", role=role, max_model_calls=budget, goal=row["goal"],
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
        progress.emit("frontier-evaluation-complete", completed=len(store.rows), total=store.total_goals,
                      evaluation_sha256=result["evaluation_sha256"])
        return result
