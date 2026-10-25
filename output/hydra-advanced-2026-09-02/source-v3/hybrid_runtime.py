"""Connect native hybrid search to a lazy trained policy and local Vampire.

The heuristic-only path never imports numerical frameworks. All paths retain
the same finite native tactic surface and independently replay a winning proof.
"""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
import time

import model_runtime as trained

APP = Path(__file__).resolve().parent
MODES = ("model", "heuristic", "symbolic", "hybrid")
SOURCE_FILES = ("hybrid_runtime.py", "hybrid_search.py", "vampire_bridge.py",
                "vampire_process.py", "vampire_worker.py", "vampire_limits.py",
                "search_settings.py", "arithmetic_search.py", "worker.py", "model_runtime.py")


def bounded_records(records, maximum_bytes):
    """Bound optional diagnostic detail without changing actual work counters."""
    kept, size = [], 2
    for record in records:
        cost = len(json.dumps(record, ensure_ascii=False, allow_nan=False,
                              separators=(",", ":")).encode("utf-8")) + 1
        if size + cost > maximum_bytes:
            break
        kept.append(record)
        size += cost
    return kept, len(records) - len(kept)


class LazyModelPolicy:
    """No base weights or MLX imports until the first unresolved model request."""
    def __init__(self, capabilities, emit_progress):
        self.capabilities = capabilities
        self.emit = emit_progress
        self.policy = None
        self.snapshot = None
        self.identity = {"name": trained.NAME, "used": False,
                         "numerical_equivalence_to_training": False}
        self.load_attempted = False
        self._completed_batches = 0
        self._inference_baseline = None

    @property
    def calls(self):
        # The preserved provider counts an attempt before prompt validation.
        # Hybrid inference counts only batches with a completed forward pass,
        # including a currently active batch once it has actually run.
        active = (self.policy is not None and self._inference_baseline is not None
                  and self.policy.forward_passes > self._inference_baseline)
        return self._completed_batches + int(active)

    def _policy_progress(self, event):
        self.emit({**event, "model_calls": self.calls,
                   "model_decode_attempts": 0 if self.policy is None else self.policy.calls})

    def _prepare(self):
        self.load_attempted = True
        self.emit({"phase": "authenticating", "message": "A choice remains: checking the saved model before its first call.",
                   "model_calls": 0})
        candidate, handle, source_pin, inputs_pin = trained._load_authenticated()
        artifacts = trained._artifact_snapshot(handle)
        quantized, quantized_pin, ready_pin = trained._quantized_snapshot()
        runtime_pin = trained._fingerprint(Path(trained.__file__), 256 * 1024)
        from training.peano_policy.prompt import CapabilityIdentity
        from training.peano_policy.contract import authority_prompt_environment
        from training.peano_policy.authority import authority_profile_record, authority_contract_record
        contract = handle.manifest["common_contract"]
        record = contract["authority"]["capabilities"]
        environment = authority_prompt_environment(False, CapabilityIdentity.from_record({
            "label": record["label"], "allowed_commands": record["allowed_commands"],
            "allowed_theorems": record["allowed_theorems"]}))
        trained.require(authority_profile_record(environment) == contract["decoder_profile"]
                        and authority_contract_record() == contract["prompt_contract"],
                        "The original trained prompt or tactic authority changed.")
        trained.require(self.capabilities.allowed_commands == frozenset(record["allowed_commands"])
                        and self.capabilities.allowed_theorems == frozenset(record["allowed_theorems"]),
                        "Hybrid native permissions differ from the trained tactic surface.")
        self.identity = {"name": trained.NAME, "device": "Apple Metal", "backend": "MLX",
            "model_id": trained.MODEL_ID, "revision": trained.REVISION,
            "adapter_manifest_sha256": trained.MODEL_MANIFEST_SHA, "adapter_sha256": trained.ADAPTER_SHA,
            "training_job_id": "21456251", "admission_receipt_sha256": candidate.admission_receipt_sha256,
            "quantization": trained.QUANTIZATION, "quantized_manifest_sha256": quantized_pin["sha256"],
            "runtime_sha256": runtime_pin["sha256"], "kernel_source_commit": trained.SOURCE_COMMIT,
            "decoder": trained.DECODER, "numerical_equivalence_to_training": False,
            "purpose": "interactive hybrid search, not the archived GH200 comparison"}
        self.snapshot = (handle, artifacts, source_pin, inputs_pin, quantized, quantized_pin, ready_pin, runtime_pin)
        self.emit({"phase": "loading", "message": "Loading the local trained model only for the unresolved choice.",
                   "model_calls": 0})
        model, tokenizer, mx = trained._load_model(handle, quantized)
        self.policy = trained._MLXCandidatePolicy(model, tokenizer, mx, environment, self.identity, self._policy_progress)

    def propose(self, goals_before, *, max_candidates):
        if self.policy is None:
            if self.load_attempted:
                raise RuntimeError("The one model initialization attempt failed; no automatic reload.")
            self._prepare()
        self._inference_baseline = self.policy.forward_passes
        try:
            return self.policy.propose(goals_before, max_candidates=max_candidates)
        finally:
            if self.policy.forward_passes > self._inference_baseline:
                self._completed_batches += 1
            self._inference_baseline = None

    def finalize(self):
        if self.snapshot is not None:
            handle, artifacts, source_pin, inputs_pin, quantized, quantized_pin, ready_pin, runtime_pin = self.snapshot
            trained.require(trained._artifact_snapshot(handle) == artifacts
                            and trained._source_snapshot() == source_pin
                            and trained._fingerprint(trained.INPUTS, inputs_pin["bytes"]) == inputs_pin
                            and trained._fingerprint(Path(trained.__file__), runtime_pin["bytes"]) == runtime_pin,
                            "Saved model or source bytes changed during hybrid inference.")
            after, after_pin, after_ready = trained._quantized_snapshot()
            trained.require((after, after_pin, after_ready) == (quantized, quantized_pin, ready_pin),
                            "The local quantized base changed during inference.")
        self.identity.update(used=self.calls > 0, load_attempted=self.load_attempted)
        return {"model_calls": self.calls, "model_loaded": self.policy is not None,
                "model_decode_attempts": 0 if self.policy is None else self.policy.calls,
                "model_call_unit": "candidate batches with at least one completed model forward pass",
                "proposal_call_unit": "provider decode attempts, including prompt-preflight failures",
                "forward_passes": 0 if self.policy is None else self.policy.forward_passes,
                "generated_token_steps": 0 if self.policy is None else self.policy.generated_token_steps,
                "proposals": [] if self.policy is None else self.policy.proposals,
                "authority_rejections": [] if self.policy is None else self.policy.rejections}


def run_search(request, emit_progress):
    mode = request.get("search_mode")
    trained.require(mode in ("heuristic", "symbolic", "hybrid"), "Unknown hybrid search mode.")
    trained.require(sys.flags.isolated and sys.dont_write_bytecode, "Use the bounded isolated proof worker.")
    started = time.monotonic()
    emit = lambda value: trained._progress(emit_progress, value)
    emit({"phase": "preparing", "message": "Preparing native proof branches and independent source checks.", "model_calls": 0})
    source_pin = trained._source_snapshot()
    app_pins = {name: trained._fingerprint(APP / name, 512 * 1024) for name in SOURCE_FILES}
    from peano_lab.batch import MODEL_V1_COMMANDS
    from peano_lab.ui.prove import SurfaceCapabilities
    from training.peano_hydra.protocol import validate_statement
    from hybrid_search import HybridLimits, search
    from search_settings import native_limits, profile as selected_profile
    profile_name = request.get("search_profile", "standard")
    settings = selected_profile(profile_name)
    theorem = validate_statement(request["theorem"])
    trained.require(theorem == request["theorem"], "The worker must supply the original canonical theorem.")
    capabilities = SurfaceCapabilities(label="hydra-authority-no-imports-v1",
        allowed_commands=MODEL_V1_COMMANDS, allowed_theorems=frozenset())
    policy = LazyModelPolicy(capabilities, emit) if mode == "hybrid" else None
    runner = advisor = None
    if mode in ("symbolic", "hybrid"):
        from vampire_bridge import VampireAdvisor
        from vampire_process import VampireRunner, metadata_status
        status = metadata_status(profile=profile_name)
        trained.require(status["available"], "Vampire is not ready: " + status.get("detail", ""))
        runner = VampireRunner(profile=profile_name)
        advisor = VampireAdvisor(runner)
    limits = HybridLimits(**native_limits(request))
    result = search(theorem, capabilities=capabilities, model_policy=policy,
                    vampire_advisor=advisor, limits=limits, emit_progress=emit)
    model_stats = policy.finalize() if policy is not None else {"model_calls": 0, "model_loaded": False,
        "model_decode_attempts": 0,
        "model_call_unit": "candidate batches with at least one completed model forward pass",
        "proposal_call_unit": "provider decode attempts, including prompt-preflight failures",
        "forward_passes": 0, "generated_token_steps": 0, "proposals": [], "authority_rejections": []}
    model_stats["proposals"], model_stats["proposals_omitted"] = bounded_records(
        model_stats["proposals"], 128 * 1024)
    model_stats["authority_rejections"], model_stats["authority_rejections_omitted"] = bounded_records(
        model_stats["authority_rejections"], 32 * 1024)
    trained.require(result["model_calls"] == model_stats["model_calls"], "Actual model-call accounting disagrees.")
    trained.require(result["vampire_calls"] == (0 if runner is None else runner.calls),
                    "Actual Vampire-call accounting disagrees.")
    trained.require(trained._source_snapshot() == source_pin
                    and all(trained._fingerprint(APP / name, pin["bytes"]) == pin for name, pin in app_pins.items()),
                    "Hybrid search code or original kernel changed while the request was running.")
    proved = result["status"] == "proof"
    replay = result["replay"]
    trained.require(proved == (replay is not None), "Hybrid status has no matching independent replay.")
    if proved:
        trained.require(replay["status"] == "proved" and replay["kernel_checked"] is True
                        and replay["theorem"] == theorem and not replay["goals"]
                        and replay["proof_nodes"] == result["certificate_nodes"],
                        "Hybrid result does not independently prove the original theorem.")
    trace = [] if replay is None else [dict(row) for row in replay["trace"]]
    provenance = iter(result["provenance"])
    for row in trace:
        if "tactic" in row:
            item = next(provenance)
            trained.require(item["command"] == row["tactic"], "Tactic provenance does not match native replay.")
            row["origin"] = item
    search_record = {key: value for key, value in result.items() if key not in {"replay", "initial_goals"}}
    search_record.update(model_stats)
    search_record.update(vampire_runs=[] if runner is None else runner.records,
                         elapsed_seconds=round(time.monotonic() - started, 3),
                         requested_beam_width=request["beam_width"], search_mode=mode,
                         settings_profile=profile_name, settings_policy=settings["policy"],
                         application_source_pins=app_pins)
    source_counts = dict(Counter(item["source"] for item in result["provenance"]))
    return {"kind": mode, "search_mode": mode, "status": "proved" if proved else result["status"],
            "theorem": theorem, "goals": [] if proved else result["initial_goals"],
            "goals_scope": "final-independent-replay" if proved else "original-unproved-goal",
            "kernel_checked": proved, "proof_nodes": result["certificate_nodes"],
            "trace": trace, "commands": result["commands"], "search": search_record,
            "model": policy.identity if policy is not None else {"used": False, "name": "No model in this mode"},
            "model_used": model_stats["model_calls"] > 0,
            "vampire_used": runner is not None and runner.calls > 0,
            "proof_sources": source_counts, "benchmark_claim": False,
            "kernel_source_commit": trained.SOURCE_COMMIT,
            "message": "The original Peano kernel independently checked this proof." if proved
                       else "No proof within this bounded search; the theorem has not been refuted."}
