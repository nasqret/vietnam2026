"""A separately approved, paired search ablation of one preserved Qwen adapter.

The original training validator runs only through the preserved-origin bridge.
This module binds new execution source, never rewrites the old preparation,
and never accepts an old model report as fresh inference. Both lanes retain
the same model, tokenizer, V4 prompt/decoder, goal seeds and search budgets.
Only the explicit search-state identity profile changes.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import resource
import sys
import time
from typing import Callable

from hydra_training_v5.peano_hydra import capacity, comparison, comparison_checkpoint as cp, evaluation as shared
from hydra_training_v5.peano_hydra.composition import execution_capabilities
from hydra_training_v5.peano_hydra.epoch import HydraEpoch, freeze_epoch
from hydra_training_v5.peano_hydra.origin_bridge import execution_binding
from hydra_training_v5.peano_hydra.runner import policy_environment
from hydra_training_v5.peano_hydra.search_origin import CorrectedOriginReference
from hydra_training_v5.peano_policy.authority import (
    AUTHORITY_PRIMITIVE_PROFILE, authority_contract_record, authority_profile_record,
)
from hydra_training_v5.peano_policy.contract import authority_prompt_environment
from hydra_training_v5.peano_policy.prompt import CapabilityIdentity, PEANO_PROMPT_V4, prompt_contract_sha256
from hydra_training_v5.peano_policy.state_identity import CONTEXT_ALPHA_V1, search_profile_contract


ROOT = Path(__file__).absolute().parents[2]
PLAN_SCHEMA = "peano-hydra-paired-search-primary32-plan-v1"
RESULT_SCHEMA = "peano-hydra-paired-search-primary32-results-v1"
VERIFY_SCHEMA = "peano-hydra-paired-search-primary32-verification-v1"
LANES = ("legacy", "context-alpha")
GOAL_COUNT = 32
TOTAL_GOALS = 64
GOAL_SET_SHA256 = "e275a2ece955082c47f1dc1c74d93d3de43422fb0b7163b84c8d7bca54d3c88a"
LOADING = "sequential-fresh-base-corrected-lora-legacy-unload-context-alpha-unload"
MAX_REPORT_BYTES = 24 * 1024**2
MAX_APPROVED_SECONDS = 1800
CLAIM = (
    "Paired fresh inference by one preserved corrected Qwen adapter on 32 exposed, correlated "
    "PRIMARY32 development goals under matched V4/no-import budgets; only search-state identity "
    "changes. Not retraining, unseen generalization, independent discoveries, proof optimality, "
    "policy-behavior equivalence or a continuation of a historical model evaluation."
)
SOURCE_FILES = (
    "training/peano_hydra/search_comparison.py", "training/peano_hydra/paired_checkpoint.py",
    "training/peano_hydra/search_origin.py", "training/peano_hydra/search_launch.py",
    "training/peano_hydra/search_workflow.py", "training/peano_hydra/corrective_workflow.py",
    "training/peano_hydra/origin_bridge.py", "training/peano_hydra/comparison.py",
    "training/peano_hydra/comparison_checkpoint.py", "training/peano_hydra/helios_runtime.py",
    "training/peano_hydra/__init__.py", "training/peano_policy/__init__.py",
    "training/peano_policy/pretrained_baseline.py", "training/peano_policy/evaluation_replay.py",
    "training/peano_policy/requirements-helios.lock",
    "scripts/eval_peano_hydra_search.py", "scripts/prepare_peano_hydra_search_origin.py",
    "scripts/helios_hydra_search.sh", "scripts/helios_common.sh",
    "scripts/submit_slurm_job.sh", "scripts/helios_submit_job.sh",
    "slurm/peano_hydra_search_evaluate.sbatch",
)
SOURCE_COVERAGE = (
    "Listed evaluation, origin, proposal, checkpoint, launch and native kernel/engine files; "
    "not the whole repository or an attestation of runtime hardware. Mathematical inputs "
    "are separately authenticated against the preserved training-origin source bundle."
)
Error = capacity.CapacityError
_require, _same, _keys, _integer = capacity._require, capacity._same, capacity._keys, capacity._integer
_canonical, _digest = shared._canonical, shared._digest


def search_profile_for(lane: str) -> str | None:
    _require(type(lane) is str and lane in LANES, "unknown paired search lane")
    return None if lane == "legacy" else CONTEXT_ALPHA_V1


def _sources() -> dict[str, str]:
    sources = capacity._sources(authority_profile=AUTHORITY_PRIMITIVE_PROFILE)
    for name in SOURCE_FILES:
        sources[name] = hashlib.sha256(shared._read_regular(
            ROOT / name, maximum=2 * 1024**2, description="paired search execution source"
        )).hexdigest()
    _require(len(sources) <= capacity.MAX_SOURCE_FILES, "paired search source inventory exceeds its bound")
    return dict(sorted(sources.items()))


@dataclass(frozen=True, slots=True)
class SearchExecution:
    """Only the immutable goal/budget interface consumed by the shared model lane."""

    epoch: HydraEpoch
    _model_json: str
    _goals_json: str

    @property
    def model(self):
        return json.loads(self._model_json)

    @property
    def goals(self):
        return tuple(json.loads(self._goals_json))

    @property
    def capabilities(self):
        return execution_capabilities(self.epoch)

    @property
    def environment(self):
        return policy_environment(self.capabilities)

    @property
    def authority_profile(self):
        return AUTHORITY_PRIMITIVE_PROFILE

    @property
    def limits(self):
        return capacity.LIMITS

    @property
    def seed(self):
        return capacity.SEED

    @property
    def max_new_tokens(self):
        return capacity.MAX_NEW_TOKENS

    @property
    def goal_set_sha256(self):
        return _digest(self.goals)

    @property
    def matched_budget(self):
        return {**shared._limits_record(self.limits), "goal_count": GOAL_COUNT,
                "max_model_calls_per_lane": GOAL_COUNT * self.limits.max_model_calls,
                "max_new_tokens": self.max_new_tokens, "seed": self.seed,
                "sampling": "deterministic batched candidate beam search"}


def _epoch_record(epoch: HydraEpoch) -> dict:
    return {name: getattr(epoch, name) for name in (
        "version", "epoch_sha256", "edition_identity_sha256", "theorem_dag_sha256",
        "reviewed_definition_dag_sha256",
    )}


def _execution_contract(execution: SearchExecution, origin: dict) -> dict:
    environment = authority_prompt_environment(
        False, CapabilityIdentity.from_record(execution.environment["capabilities"])
    )
    # The preserved model calls the full primitive-authority contract its
    # prompt_contract; the textual prompt digest is bound separately by the
    # decoder profile. Do not replace that historical record with a summary.
    prompt = authority_contract_record()
    decoder = authority_profile_record(environment)
    _require(_same(prompt, origin["training_prompt_contract"])
             and _same(decoder, origin["training_decoder_profile"]),
             "paired search cannot change the preserved prompt or decoder contract")
    contract = {
        "schema": "peano-hydra-paired-search-execution-v1",
        "epoch": _epoch_record(execution.epoch), "model": execution.model,
        "environment": execution.environment, "authority_profile": execution.authority_profile,
        "prompt_contract": prompt, "decoder_profile": decoder,
        "text_prompt_contract": {"version": PEANO_PROMPT_V4,
                                 "sha256": prompt_contract_sha256(PEANO_PROMPT_V4)},
        "tokenizer": origin["artifacts"]["tokenizer"],
        "matched_budget": execution.matched_budget,
        "search_profiles": {lane: search_profile_contract(search_profile_for(lane)) for lane in LANES},
        "runner_versions": {"legacy": 1, "context-alpha": 2},
        "original_prompts_and_commands_rewritten": False,
        "candidate_goal_seed_schedule": "sha256([20260826,goal_name])[:8] & (2**63-1); identical in both lanes",
    }
    return {**contract, "contract_sha256": _digest(contract)}


@dataclass(frozen=True, slots=True)
class PairedSearchPlan:
    reference: CorrectedOriginReference
    execution: SearchExecution
    _origin_json: str
    _sources_json: str
    _binding_json: str

    @property
    def origin(self):
        return json.loads(self._origin_json)

    @property
    def model(self):
        return self.execution.model

    @property
    def source_files(self):
        return json.loads(self._sources_json)

    def to_dict(self):
        binding = json.loads(self._binding_json)
        record = {
            "schema": PLAN_SCHEMA, "claim_boundary": CLAIM,
            "development_only": True, "public_correlated_exposed_data": True,
            "research_claim_eligible": False, "sealed_benchmark": False, "independent_discoveries": False,
            "retraining": False, "historical_checkpoint_reuse_allowed": False,
            "automatic_retry": False, "resume_allowed": False,
            "lanes": list(LANES), "goal_count_per_lane": GOAL_COUNT, "total_goal_records": TOTAL_GOALS,
            "goals": list(self.execution.goals), "goal_set_sha256": self.execution.goal_set_sha256,
            "matched_budget": self.execution.matched_budget,
            "max_model_calls_total": TOTAL_GOALS * self.execution.limits.max_model_calls,
            "search_profiles": {lane: search_profile_contract(search_profile_for(lane)) for lane in LANES},
            "training_origin": self.origin, "origin_reference": self.reference.to_dict(),
            "model": self.model, "epoch": _epoch_record(self.execution.epoch),
            "execution_contract": binding["contract"], "execution_binding": binding,
            "source_files": self.source_files, "source_coverage": SOURCE_COVERAGE,
            "order": "lane-primary-goal", "model_loading": LOADING,
            "max_report_bytes": MAX_REPORT_BYTES,
            "max_goal_evidence_bytes": shared.MAX_GOAL_EVIDENCE_BYTES,
            "max_lane_evidence_bytes": shared.MAX_LANE_EVIDENCE_BYTES,
            "offline_replay_limits": capacity.REPLAY_LIMITS.to_dict(),
            "per_goal_wall_time_limit": None,
            "interruption_policy": "durable completed prefix; in-flight is unknown; no automatic retry or resume",
            "resource_measurements": "process wall/CPU and cumulative RSS; CUDA allocator peaks; not hardware attestation",
            "gpu_execution_authorized_by_plan": False,
        }
        return {**record, "plan_sha256": _digest(record)}


def build_paired_plan(reference: CorrectedOriginReference) -> PairedSearchPlan:
    """Authenticate one preserved origin and build a new, model-free execution plan."""
    _require(type(reference) is CorrectedOriginReference, "paired search needs an exact corrected-origin reference")
    verified = reference.load()
    origin = verified.origin
    # Read its already authenticated mathematical snapshot, not the current
    # development campaign and not a newly regenerated training preparation.
    epoch = freeze_epoch(reference.request.source_root)
    _require(_same(_epoch_record(epoch), {name: origin[name] for name in _epoch_record(epoch)}),
             "new search execution changed the preserved mathematical epoch")
    _require(origin["training_authority_profile"] == AUTHORITY_PRIMITIVE_PROFILE,
             "paired search changed the corrected model's training authority")
    goals = comparison.comparison_goals()[:GOAL_COUNT]
    _require(len(goals) == GOAL_COUNT and _digest(goals) == GOAL_SET_SHA256,
             "paired search changed the original exact PRIMARY32 goals")
    execution = SearchExecution(epoch, _canonical(origin["model"]).decode(), _canonical(goals).decode())
    contract = _execution_contract(execution, origin)
    sources = _sources()
    binding = execution_binding(source_root=ROOT, source_files=sources, contract=contract)
    _require(_same(_sources(), sources), "paired execution source changed during planning")
    # Receipt reload is a byte check only, never a second 1,024-route rebuild.
    _require(_same(reference.load().origin, origin), "preserved origin changed during planning")
    return PairedSearchPlan(reference, execution, _canonical(origin).decode(),
                            _canonical(sources).decode(), _canonical(binding).decode())


def _refresh(plan: PairedSearchPlan) -> None:
    _require(type(plan) is PairedSearchPlan, "paired search requires its exact independently built plan")
    fresh = build_paired_plan(plan.reference)
    _require(_same(fresh.to_dict(), plan.to_dict()), "paired source, origin or execution contract changed after planning")


def _runtime(value: dict) -> None:
    _keys(value, {"torch_version", "transformers_version", "peft_version", "visible_cuda_devices", "cuda_device",
                  "dtype", "attention", "local_files_only", "model_loading"}, "paired search runtime")
    _require(all(type(value[key]) is str and 1 <= len(value[key]) <= 256 for key in (
        "torch_version", "transformers_version", "peft_version", "cuda_device")), "invalid paired runtime text")
    _require(type(value["visible_cuda_devices"]) is int and value["visible_cuda_devices"] == 1
             and value["dtype"] == "bfloat16" and value["attention"] == "sdpa"
             and value["local_files_only"] is True and value["model_loading"] == LOADING,
             "paired runtime changed its single-GPU/offline/loading contract")


def provider(plan: PairedSearchPlan, lane: str, runtime: dict, origin: dict) -> dict:
    _runtime(runtime)
    _require(_same(plan.origin, origin), "paired provider changed its preserved model origin")
    profile = search_profile_contract(search_profile_for(lane))
    return {"kind": "preserved-corrected-lora-paired-search-v1", "adapter_attached": True,
            "model": plan.model, "training_origin": origin,
            "execution_binding_sha256": json.loads(plan._binding_json)["execution_binding_sha256"],
            "search_lane": lane, "search_profile": profile, "runtime": runtime,
            "research_claim_eligible": False}


def _lane_record(plan: PairedSearchPlan, lane: str, rows: list[dict], runtime: dict) -> dict:
    return {
        "status": "executed", "lane": lane,
        "search_profile": search_profile_contract(search_profile_for(lane)),
        "model": plan.model, "adapter_attached": True,
        "training_origin_sha256": plan.origin["origin_sha256"],
        "epoch_sha256": plan.execution.epoch.epoch_sha256,
        "environment_sha256": plan.execution.environment["environment_sha256"],
        "goal_set_sha256": plan.execution.goal_set_sha256,
        "matched_budget": plan.execution.matched_budget,
        "provider": provider(plan, lane, runtime, plan.origin), "goals": rows,
        "kernel_checked_proofs": sum(row["kernel_checked"] for row in rows),
        "model_generate_calls": sum(row["model_generate_calls"] for row in rows),
        "retained_evidence_bytes": sum(len(_canonical(row["evidence"])) for row in rows),
        "research_claim_eligible": False,
    }


def _metrics(plan: PairedSearchPlan, lanes: dict) -> dict:
    metrics = {}
    for lane in LANES:
        rows = lanes[lane]["goals"]
        metrics[lane] = {
            **comparison._panel_metrics(plan.execution.goals, rows),
            "successful_tactic_decisions": sum(row["tactic_decisions"] for row in rows if row["kernel_checked"]),
            "native_candidate_executions": sum(row["evidence"]["search"]["candidates_executed"] for row in rows),
            "states_discovered": sum(row["evidence"]["search"]["states_discovered"] for row in rows),
            "maximum_depth_reached": max(row["evidence"]["search"]["depth_reached"] for row in rows),
            "resources": {
                "summed_goal_wall_seconds": sum(row["resources"]["goal_wall_seconds"] for row in rows),
                "summed_goal_cpu_seconds": sum(row["resources"]["goal_cpu_seconds"] for row in rows),
                "maximum_observed_process_peak_rss_bytes": max(row["resources"]["process_peak_rss_bytes"] for row in rows),
                "maximum_cuda_allocated_bytes": max(row["resources"]["cuda_peak_allocated_bytes"] for row in rows),
                "maximum_cuda_reserved_bytes": max(row["resources"]["cuda_peak_reserved_bytes"] for row in rows),
                "hardware_attested": False,
            },
        }
    legacy, alpha = (lanes[lane]["goals"] for lane in LANES)
    pairs = list(zip(plan.execution.goals, legacy, alpha, strict=True))
    gained = [goal["name"] for goal, old, new in pairs if not old["kernel_checked"] and new["kernel_checked"]]
    lost = [goal["name"] for goal, old, new in pairs if old["kernel_checked"] and not new["kernel_checked"]]
    return {
        "lanes": metrics,
        "paired": {
            "both_proved": sum(old["kernel_checked"] and new["kernel_checked"] for _, old, new in pairs),
            "context_alpha_only": gained, "legacy_only": lost,
            "neither_proved": sum(not old["kernel_checked"] and not new["kernel_checked"] for _, old, new in pairs),
            "kernel_checked_proof_delta": len(gained) - len(lost),
            "model_generate_calls_delta": metrics["context-alpha"]["model_generate_calls"] - metrics["legacy"]["model_generate_calls"],
            "jointly_proved_routes": [
                {"goal": goal["name"], "legacy_tactic_decisions": old["tactic_decisions"],
                 "context_alpha_tactic_decisions": new["tactic_decisions"],
                 "legacy_proof_nodes": old["proof_nodes"], "context_alpha_proof_nodes": new["proof_nodes"],
                 "identical_commands": old["evidence"]["search"]["commands"] == new["evidence"]["search"]["commands"]}
                for goal, old, new in pairs if old["kernel_checked"] and new["kernel_checked"]
            ],
            "proof_optimality_claimed": False,
        },
    }


def validate_result(plan: PairedSearchPlan, result: dict, *, replay: bool) -> dict:
    """Authenticate the complete report before replaying any claimed positive."""
    from hydra_training_v5.peano_hydra.paired_checkpoint import validate_paired_row

    _require(type(plan) is PairedSearchPlan and type(replay) is bool, "invalid paired verification input")
    _require(not replay or not {"torch", "transformers", "peft", "tokenizers"} & set(sys.modules),
             "independent paired replay requires a model-free process")
    encoded = _canonical(result)
    _require(len(encoded) <= MAX_REPORT_BYTES, "paired report exceeds its retained-byte bound")
    result = shared._json_object(encoded, description="detached paired report")
    _keys(result, {"schema", "status", "plan", "training_origin", "provider_runtime", "lanes", "metrics",
                   "claim_boundary", "research_claim_eligible", "sealed_benchmark", "independent_discoveries",
                   "historical_gpu_inference_attested", "evaluation_sha256"}, "paired result")
    capacity._signed(result, "evaluation_sha256")
    _refresh(plan)
    _require(result["schema"] == RESULT_SCHEMA and result["status"] == "executed"
             and _same(result["plan"], plan.to_dict()) and _same(result["training_origin"], plan.origin)
             and result["claim_boundary"] == CLAIM
             and all(result[key] is False for key in (
                 "research_claim_eligible", "sealed_benchmark", "independent_discoveries", "historical_gpu_inference_attested")),
             "paired result changed its complete plan, origin or claim boundary")
    _runtime(result["provider_runtime"])
    _keys(result["lanes"], set(LANES), "paired result lanes")
    authenticated_rows = []
    for lane in LANES:
        value = result["lanes"][lane]
        _require(type(value) is dict and type(value.get("goals")) is list and len(value["goals"]) == GOAL_COUNT,
                 "a partial lane cannot be reported as a complete paired comparison")
        for goal, row in zip(plan.execution.goals, value["goals"], strict=True):
            validate_paired_row(plan, lane, goal, row, result["provider_runtime"], plan.origin, replay=False)
            authenticated_rows.append((lane, goal, row))
        expected = _lane_record(plan, lane, value["goals"], result["provider_runtime"])
        _require(_same(value, expected), "paired lane identity, provider or derived counts differ")
        _require(value["model_generate_calls"] <= GOAL_COUNT * capacity.LIMITS.max_model_calls
                 and value["retained_evidence_bytes"] <= shared.MAX_LANE_EVIDENCE_BYTES,
                 "paired lane exceeds its call/evidence reservation")
    _require(_same(result["metrics"], _metrics(plan, result["lanes"])), "paired metrics differ from complete row evidence")
    # No proof work occurs until all roles, rows, counts and report seals join.
    checked = []
    if replay:
        for lane, goal, row in authenticated_rows:
            if row["kernel_checked"]:
                receipt = validate_paired_row(plan, lane, goal, row, result["provider_runtime"], plan.origin, replay=True)
                _require(type(receipt) is dict, "positive paired row omitted its independent replay receipt")
                checked.append(receipt)
        _refresh(plan)
    return {
        "schema": VERIFY_SCHEMA, "status": "passed", "plan_sha256": plan.to_dict()["plan_sha256"],
        "evaluation_sha256": result["evaluation_sha256"], "metrics": result["metrics"],
        "proof_replay_performed": replay, "independently_replayed_proofs": checked,
        "model_outputs_regenerated": False, "historical_gpu_inference_attested": False,
        "research_claim_eligible": False, "claim_boundary": CLAIM,
    }


def _execution_approval(plan: PairedSearchPlan, approval_sha256: str) -> None:
    """Even direct library execution requires the dedicated scheduled reservation."""
    from hydra_training_v5.peano_hydra import search_launch

    approval, approved_plan, _ = search_launch.validate_metadata(approval_sha256)
    _require(_same(plan.to_dict(), approved_plan), "execution differs from its externally pinned approved plan")
    _require(approval["training_authorized"] is False and approval["evaluation_only"] is True,
             "paired search cannot acquire training permission")
    search_launch.check_job_reservation(approval_sha256)


def execute_paired_comparison(
    plan: PairedSearchPlan, *, checkpoint_directory: Path, approval_sha256: str,
    progress: cp.Progress | None = None, stop_after_seconds: float = 1500,
    stop_requested: Callable[[], bool] | None = None,
) -> dict:
    """Fresh inference only, with one approved job and a new durable checkpoint."""
    from hydra_training_v5.peano_hydra.paired_checkpoint import PairedCheckpointStore

    _require(type(stop_after_seconds) in (int, float) and math.isfinite(stop_after_seconds)
             and 0 < stop_after_seconds <= MAX_APPROVED_SECONDS, "paired soft deadline exceeds its approved envelope")
    _require(stop_requested is None or callable(stop_requested), "invalid paired stop hook")
    progress = progress or cp.Progress()
    progress.emit("validation-start", profile=PLAN_SCHEMA)
    _execution_approval(plan, approval_sha256)
    _refresh(plan)
    verified = plan.reference.load()
    _require(_same(verified.origin, plan.origin), "model origin changed before paired inference")
    cp.check_fresh_output(checkpoint_directory)
    progress.emit("validation-complete", plan_sha256=plan.to_dict()["plan_sha256"])

    def pause_reason():
        if stop_requested is not None and stop_requested():
            return "signal"
        if time.monotonic() - progress.started >= stop_after_seconds:
            return "soft_deadline"
        return None

    reason = pause_reason()
    if reason is not None:
        raise cp.CheckpointPaused({"schema": "peano-hydra-paired-search-pre-inference-stop-v1",
                                   "status": "paused-before-inference", "pause_reason": reason,
                                   "completed_goal_records": 0, "total_goal_records": TOTAL_GOALS,
                                   "checkpoint_created": False, "model_loaded": False,
                                   "research_claim_eligible": False})
    torch, transformers, peft = shared._model_runtime()
    runtime = {"torch_version": str(torch.__version__), "transformers_version": str(transformers.__version__),
               "peft_version": str(peft.__version__), "visible_cuda_devices": 1,
               "cuda_device": torch.cuda.get_device_name(0), "dtype": "bfloat16", "attention": "sdpa",
               "local_files_only": True, "model_loading": LOADING}
    _runtime(runtime)
    lanes = {}
    with PairedCheckpointStore(checkpoint_directory, plan, plan.origin, runtime=runtime, progress=progress) as store:
        tokenizer = transformers.AutoTokenizer.from_pretrained(
            str(verified.tokenizer_directory), trust_remote_code=False, use_fast=True, local_files_only=True)
        if tokenizer.pad_token_id is None:
            _require(tokenizer.eos_token_id is not None, "paired tokenizer lacks EOS/padding")
            tokenizer.pad_token_id = tokenizer.eos_token_id

        def stop_at_boundary():
            reason = pause_reason()
            if reason is not None and len(store.rows) < TOTAL_GOALS:
                store.assert_unchanged()
                receipt = {**store.receipt(status="paused"), "pause_reason": reason}
                progress.emit("paused", completed=len(store.rows), total=TOTAL_GOALS, reason=reason)
                raise cp.CheckpointPaused(receipt)

        for lane in LANES:
            model = None
            try:
                stop_at_boundary()
                _refresh(plan)
                shared._reset_seed(torch, transformers, capacity.SEED)
                progress.emit("model-loading-start", lane=lane, completed=len(store.rows), total=TOTAL_GOALS)
                model = shared._load_base_model(torch, transformers, plan.model)
                model = peft.PeftModel.from_pretrained(model, str(verified.adapter_directory), is_trainable=False)
                model.to("cuda:0")
                model.eval()
                progress.emit("model-loading-complete", lane=lane, completed=len(store.rows), total=TOTAL_GOALS)
                goal_started = [0.0, 0.0]

                def begin(goal):
                    stop_at_boundary()
                    store.begin(lane, "primary", goal)
                    torch.cuda.synchronize()
                    torch.cuda.reset_peak_memory_stats(0)
                    goal_started[:] = [time.monotonic(), time.process_time()]
                    progress.emit("goal-start", lane=lane, goal=goal["name"], completed=len(store.rows), total=TOTAL_GOALS)

                def committed(row):
                    torch.cuda.synchronize()
                    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
                    resources = {
                        "goal_wall_seconds": time.monotonic() - goal_started[0],
                        "goal_cpu_seconds": time.process_time() - goal_started[1],
                        "process_peak_rss_bytes": int(rss if sys.platform == "darwin" else rss * 1024),
                        "cuda_peak_allocated_bytes": int(torch.cuda.max_memory_allocated(0)),
                        "cuda_peak_reserved_bytes": int(torch.cuda.max_memory_reserved(0)),
                    }
                    store.append({**row, "resources": resources})
                    progress.emit("goal-committed", lane=lane, goal=row["goal"], completed=len(store.rows), total=TOTAL_GOALS,
                                  status=row["status"], kernel_checked=row["kernel_checked"],
                                  model_generate_calls=row["model_generate_calls"], **resources,
                                  checkpoint_head_sha256=store.head["head_sha256"])

                raw_lane = shared._run_model_lane(
                    plan.execution, model=model, tokenizer=tokenizer, lane="trained",
                    provider=provider(plan, lane, runtime, plan.origin), on_goal_start=begin, on_goal=committed,
                    **({"search_profile": search_profile_for(lane)} if lane != "legacy" else {}),
                )
                start = LANES.index(lane) * GOAL_COUNT
                rows = store.rows[start:start + GOAL_COUNT]
                _require(len(rows) == GOAL_COUNT and _same(raw_lane["goals"], [
                    {key: value for key, value in row.items() if key != "resources"} for row in rows
                ]), "live paired evidence differs from its durable completed rows")
                lanes[lane] = _lane_record(plan, lane, rows, runtime)
                progress.emit("lane-complete", lane=lane, completed=len(store.rows), total=TOTAL_GOALS,
                              kernel_checked_proofs=lanes[lane]["kernel_checked_proofs"])
            finally:
                # Drop the adapter's base_model references before cache release.
                del model
                from hydra_training_v5.peano_policy.authority_runtime import clear_authority_runtime_cache

                clear_authority_runtime_cache()
                shared._release_gpu(torch)
                progress.emit("model-unloaded", lane=lane)
        _require(len(store.rows) == TOTAL_GOALS and store.head["inflight"] is None,
                 "partial paired evidence cannot publish a complete score")
        _refresh(plan)
        store.assert_unchanged()
        result = {
            "schema": RESULT_SCHEMA, "status": "executed", "plan": plan.to_dict(),
            "training_origin": plan.origin, "provider_runtime": runtime, "lanes": lanes,
            "metrics": _metrics(plan, lanes), "claim_boundary": CLAIM,
            "research_claim_eligible": False, "sealed_benchmark": False,
            "independent_discoveries": False, "historical_gpu_inference_attested": False,
        }
        result["evaluation_sha256"] = _digest(result)
        validate_result(plan, result, replay=False)
        progress.emit("evaluation-complete", completed=TOTAL_GOALS, total=TOTAL_GOALS,
                      evaluation_sha256=result["evaluation_sha256"])
        return result


__all__ = ["PairedSearchPlan", "SearchExecution", "build_paired_plan", "search_profile_for", "provider",
           "validate_result", "execute_paired_comparison"]
