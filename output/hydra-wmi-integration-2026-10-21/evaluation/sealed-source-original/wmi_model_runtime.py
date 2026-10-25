"""Lazy, explicit WMI C6 vanilla candidate. Status never loads a framework.

One authenticated MLX model is shared by one-call providers. No failed load is
retried and no other model is substituted. The native host owns proof checking,
case supervision and independent replay; this module supplies only suggestions.
"""
from __future__ import annotations

import copy
import importlib
import math
from pathlib import Path
import sys
import time

import model_runtime as trained
from wmi_candidate_core import CandidatePolicy, Limits, require
from wmi_mlx_loader import LocalCandidateSpec, MLXVanillaBackend, inspect_export_header, load_local_policy

APP = Path(__file__).resolve().parent
ROOT = APP.parent
MODEL_SELECTION_ID = "wmi-c6-vanilla47"
NAME = "WMI C6 vanilla47 · 4-bit local candidate"
CHECKPOINT_SHA = "c6c5c90b27499f5f908d1a45f37d17087774e93e4e07db223fadf669f771c731"
EXPORT_SHA = "cabc8994cdc3a98295706041694bd0daa12d858ad5ea9d41027e5990ab7600c1"
EXPORT = ROOT / "output/hydra-wmi-integration-2026-10-21/model/selected-lora.safetensors"
EXPORT_BYTES = 139_520_392
TRAINING_RECEIPT = ROOT / "output/hydra-model-upgrade-2026-10-20/comparison-01/wmi-selected/receipt.json"
TRAINING_RECEIPT_SHA = "f570214001de547a01f087d9f818acdefcc6c17d1370dc48bd3a42a77a6c7319"
ARM_RECEIPT = ROOT / "output/hydra-model-upgrade-2026-10-20/comparison-01/results/wmi_c6_vanilla47/receipt.json"
ARM_RECEIPT_SHA = "2d22994bd9cc58c49e2eec1c25340753224db1520b973b8d78f03eed6dcbfe7f"
FROZEN = ROOT / "output/hydra-model-upgrade-2026-10-20/comparison-01/latent-source"
SELECTED_STEP = 8192
RUN_ID = "wmi-pro6000-c6-main-qwen_vanilla-s47"
MEMORY_LIMIT_BYTES = 6 * 1024**3
SOURCE_FILES = ("wmi_candidate_core.py", "wmi_mlx_loader.py", "wmi_model_runtime.py", "model_runtime.py",
                "model_selection.py", "wmi_model_config.json")


def prompt_renderer(goals):
    """Exact trained serializer; numerical loading uses the pinned source function."""
    import json
    require(type(goals) in (list, tuple) and goals and all(type(g) is str and g for g in goals), "All ordered goals required")
    return "HA model-v3 library-prefix=247/247\n" + json.dumps(
        {"focus": 0, "goals": list(goals)}, ensure_ascii=False, separators=(",", ":")) + "\nTactic:"


def candidate_spec():
    config, _ = trained._small(APP / "wmi_model_config.json")
    require(config["selection_id"] == MODEL_SELECTION_ID and config["checkpoint_sha256"] == CHECKPOINT_SHA
            and config["selected_step"] == SELECTED_STEP and config["export"] == {
                "path": EXPORT.relative_to(ROOT).as_posix(), "bytes": EXPORT_BYTES, "sha256": EXPORT_SHA}
            and config["training_receipt"] == {"path": TRAINING_RECEIPT.relative_to(ROOT).as_posix(), "sha256": TRAINING_RECEIPT_SHA}
            and config["export_receipt"] == {"path": ARM_RECEIPT.relative_to(ROOT).as_posix(), "sha256": ARM_RECEIPT_SHA},
            "Candidate configuration differs from its reviewed exact pins.")
    require(EXPORT.is_file() and not EXPORT.is_symlink(), "The authenticated WMI export is not installed locally.")
    require(EXPORT.stat().st_size == EXPORT_BYTES, "The installed WMI export has the wrong size.")
    return LocalCandidateSpec(export_path=EXPORT, export_bytes=EXPORT_BYTES, export_sha256=EXPORT_SHA,
        checkpoint_sha256=CHECKPOINT_SHA, training_receipt_path=TRAINING_RECEIPT,
        training_receipt_sha256=TRAINING_RECEIPT_SHA, arm_receipt_path=ARM_RECEIPT,
        arm_receipt_sha256=ARM_RECEIPT_SHA, selected_step=SELECTED_STEP, run_id=RUN_ID)


def metadata_status():
    result = {"available": False, "selection_id": MODEL_SELECTION_ID, "name": NAME,
        "model_id": trained.MODEL_ID, "revision": trained.REVISION, "device": "Apple Metal", "backend": "MLX",
        "checkpoint_sha256": CHECKPOINT_SHA, "exported_adapter_sha256": EXPORT_SHA, "selected_step": SELECTED_STEP,
        "training_run_id": RUN_ID, "lora_rank": 32, "lora_alpha": 64, "recurrence_depth": 1,
        "conditioning": "model-v3 full library 247/247", "execution_authority": "current Hydra no imports",
        "quantized_preview": True, "numerical_equivalence_to_training": False,
        "quality_status": "candidate; promotion requires a fresh matched comparison",
        "loaded": False, "memory_limit_bytes": MEMORY_LIMIT_BYTES, "automatic_retry": False,
        "automatic_fallback": False, "detail": "The WMI candidate has not been prepared locally."}
    try:
        base = trained.metadata_status()
        require(base["available"], base["detail"])
        spec = candidate_spec()
        training, _ = trained._small(TRAINING_RECEIPT, expected=TRAINING_RECEIPT_SHA)
        arm, _ = trained._small(ARM_RECEIPT, expected=ARM_RECEIPT_SHA)
        require(arm["status"] == "completed" and arm["training"] is False
                and arm["checkpoint_sha256"] == CHECKPOINT_SHA and arm["exported_lora_sha256"] == EXPORT_SHA,
                "The WMI export receipt differs.")
        require(training["identity"]["arm"] == "qwen_vanilla", "The selected WMI arm is not vanilla.")
        inspect_export_header(EXPORT, spec.export_bytes)
        result.update(available=True, export_bytes=spec.export_bytes,
            byte_authentication="All export/base/source bytes are rehashed before actual loading; status checks metadata only.",
            detail="WMI C6 candidate is installed for explicit selection. It is not the promoted default; local quantization and decoding still require measured evaluation.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["detail"] = " ".join(str(error).split())[:512] or "The WMI candidate is unavailable."
    return result


def _frozen_helpers():
    training, _ = trained._small(TRAINING_RECEIPT, expected=TRAINING_RECEIPT_SHA)
    expected = {name: checksum for name, checksum in training["identity"]["sources_sha256"].items()
                if name.startswith("src/latentproof/") and name.endswith(".py")}
    paths = {path.relative_to(FROZEN).as_posix(): path for path in (FROZEN / "src/latentproof").glob("*.py")}
    require(len(expected) == 20 and set(paths) == set(expected), "Frozen WMI helper inventory differs.")
    pins = {}
    for name, checksum in expected.items():
        pins[name] = trained._fingerprint(paths[name], 256 * 1024)
        require(pins[name]["sha256"] == checksum, "Frozen WMI helper changed: " + name)
    for name, module in tuple(sys.modules.items()):
        if name == "latentproof" or name.startswith("latentproof."):
            require(Path(module.__file__).resolve().is_relative_to(FROZEN.resolve()), "Foreign cached latent helper.")
    sys.path.insert(0, str(FROZEN / "src"))
    data = importlib.import_module("latentproof.qwen_data")
    evaluation = importlib.import_module("latentproof.qwen_eval")
    require(data.compact_prompt(["⊢ 0 = 0", "h : 0 = 0 ⊢ 0 = 0"], 247, 0)
            == prompt_renderer(("⊢ 0 = 0", "h : 0 = 0 ⊢ 0 = 0")), "Local prompt rendering drift.")
    return data, evaluation, pins


class _OneStep:
    def __init__(self, owner, deadline, max_new_tokens, max_context_tokens):
        self.owner, self.deadline = owner, deadline
        self.max_new_tokens, self.max_context_tokens = max_new_tokens, max_context_tokens
        self._record = None
        self._attempted = False

    def propose(self, goals_before, *, max_candidates):
        require(not self._attempted, "A one-call provider cannot be reused.")
        self._attempted = True
        marker = len(self.owner._reports)
        try:
            return self.owner._propose(goals_before, max_candidates=max_candidates, deadline=self.deadline,
                max_new_tokens=self.max_new_tokens, max_context_tokens=self.max_context_tokens)
        finally:
            if len(self.owner._reports) > marker:
                self._record = copy.deepcopy(self.owner._reports[-1])

    def report(self):
        return copy.deepcopy(self._record or {"actual_model_calls": 0, "generated_token_slots": 0,
            "forward_attempts": 0, "forward_passes": 0, "attempts": [], "kernel_checked": False})


class WMIModelPolicy:
    prompt_renderer = staticmethod(prompt_renderer)
    selection_id = MODEL_SELECTION_ID
    name = NAME
    adapter_sha = EXPORT_SHA
    selected_step = SELECTED_STEP

    def __init__(self, capabilities, emit_progress=lambda event: None, *, deadline_monotonic=None,
                 max_calls=128, max_total_decision_tokens=16384):
        require(type(max_calls) is int and 0 < max_calls <= 128
                and type(max_total_decision_tokens) is int and 0 < max_total_decision_tokens <= 16384,
                "Invalid sequential model budget.")
        require(deadline_monotonic is None or (type(deadline_monotonic) in (int, float)
                and math.isfinite(deadline_monotonic)), "Invalid case deadline.")
        self.capabilities, self.emit = capabilities, emit_progress
        self.deadline = deadline_monotonic
        self.max_calls, self.max_total_decision_tokens = max_calls, max_total_decision_tokens
        self.policy = None
        self.load_attempted = False
        self._reports, self._active = [], None
        self._source_pins = self._helper_pins = None
        self.identity = {"name": NAME, "selection_id": MODEL_SELECTION_ID, "checkpoint_sha256": CHECKPOINT_SHA,
            "exported_adapter_sha256": EXPORT_SHA, "selected_step": SELECTED_STEP, "used": False,
            "quantized_preview": True, "numerical_equivalence_to_training": False,
            "automatic_retry": False, "automatic_fallback": False}
        self.evaluation_identity = copy.deepcopy(self.identity)

    def _sum(self, key):
        return sum(row.get(key, 0) for row in self._reports) + (0 if self._active is None else self._active.report().get(key, 0))

    def prepare(self):
        """Explicit one-time authenticated load; the host separately bounds load time."""
        self._prepare()
        return copy.deepcopy(self.identity)

    def new_case(self, *, deadline_monotonic, max_calls=128, max_total_decision_tokens=16384,
                 emit_progress=None):
        """Fresh case counters/deadline sharing the one already loaded model."""
        require(self.policy is not None and self._active is None, "Prepare the shared model before creating a case.")
        fresh = type(self)(self.capabilities, self.emit if emit_progress is None else emit_progress,
            deadline_monotonic=deadline_monotonic, max_calls=max_calls,
            max_total_decision_tokens=max_total_decision_tokens)
        fresh.policy = self.policy
        fresh._source_pins = copy.deepcopy(self._source_pins)
        fresh._helper_pins = copy.deepcopy(self._helper_pins)
        fresh.identity = {**copy.deepcopy(self.identity), "used": False, "shared_model_loaded": True}
        fresh.evaluation_identity = copy.deepcopy(fresh.identity)
        return fresh

    @property
    def calls(self):
        return self._sum("actual_model_calls")

    @property
    def forward_passes(self):
        return self._sum("forward_passes")

    @property
    def generated_tokens(self):
        return self._sum("generated_token_slots")

    @property
    def policy_environment(self):
        self._prepare()
        from training.peano_policy.contract import environment_record
        return environment_record(self.policy.environment)

    def _prepare(self):
        if self.policy is not None:
            return
        if self.load_attempted:
            raise RuntimeError("WMI initialization already failed; no automatic reload or fallback.")
        self.load_attempted = True
        self.emit({"phase": "authenticating", "message": "Checking the selected WMI checkpoint, export and frozen prompt.", "model_calls": self.calls})
        self._source_pins = {name: trained._fingerprint(APP / name, 256 * 1024) for name in SOURCE_FILES}
        data, evaluation, self._helper_pins = _frozen_helpers()
        self.emit({"phase": "loading", "message": "Loading the selected WMI adapter once on the local 4-bit base.", "model_calls": self.calls})
        policy = load_local_policy(trained=trained, spec=candidate_spec(), frozen_data=data, frozen_eval=evaluation,
            limits=Limits(max_calls=1), should_stop=lambda: self.deadline is not None and time.monotonic() >= self.deadline)
        require(self.capabilities.allowed_commands == frozenset(policy.environment.capabilities.allowed_commands)
                and not self.capabilities.allowed_theorems and not policy.environment.capabilities.allowed_theorems,
                "WMI provider and current native authority differ.")
        self.policy = policy
        self.identity.update(copy.deepcopy(policy.evaluation_identity), name=NAME, selection_id=MODEL_SELECTION_ID,
            used=False, loaded=True, memory_limit_bytes=MEMORY_LIMIT_BYTES)
        self.evaluation_identity = copy.deepcopy(self.identity)

    def provider_factory(self, *, deadline, max_new_tokens, max_context_tokens):
        require(type(deadline) in (int, float) and math.isfinite(deadline), "Finite shared case deadline required.")
        require(type(max_new_tokens) is int and 0 < max_new_tokens <= 128
                and type(max_context_tokens) is int and 0 < max_context_tokens <= 6144, "Invalid next-tactic budget.")
        return _OneStep(self, min(deadline, self.deadline) if self.deadline is not None else deadline,
                        max_new_tokens, max_context_tokens)

    def propose(self, goals_before, *, max_candidates):
        if self.deadline is None:
            self.deadline = time.monotonic() + 300.0
        return self._propose(goals_before, max_candidates=max_candidates, deadline=self.deadline,
                             max_new_tokens=128, max_context_tokens=6144)

    def _propose(self, goals_before, *, max_candidates, deadline, max_new_tokens, max_context_tokens):
        require(self._active is None, "WMI provider is not reentrant.")
        require(self.calls < self.max_calls, "WMI model-call budget exhausted.")
        remaining_tokens = self.max_total_decision_tokens - self.generated_tokens
        require(remaining_tokens > 0, "WMI decision-token budget exhausted.")
        if time.monotonic() >= deadline:
            raise TimeoutError("WMI case deadline expired before loading.")
        self._prepare()
        remaining_seconds = deadline - time.monotonic()
        if remaining_seconds <= 0:
            raise TimeoutError("WMI case deadline expired during loading.")
        cap = min(max_new_tokens, remaining_tokens)
        policy = self.policy
        fresh = CandidatePolicy(backend=policy.backend, tokenizer=policy.tokenizer, kind=policy.kind,
            environment=policy.environment, provenance=policy.provenance, render_prompt=policy.render_prompt,
            strict_generation=policy.strict_generation, check_prompt_binding=policy.check_prompt_binding,
            validate_tactic=policy.validate_tactic, constraint_factory=policy.constraint_factory,
            limits=Limits(max_calls=1, max_new_tokens=cap, max_total_decision_tokens=cap,
                          max_context_tokens=max_context_tokens, provider_seconds=min(30.0, remaining_seconds)),
            deadline_monotonic=deadline)
        fresh.evaluation_identity.update(backend="MLX", device="Apple Metal", selection_id=self.selection_id,
            quantized_preview=True, adapter_sha256=self.adapter_sha, selected_step=self.selected_step)
        self._active = fresh
        try:
            self.emit({"phase": "model", "message": self.name + " is proposing one literal tactic for the complete proof state.", "model_calls": self.calls})
            return fresh.propose(goals_before, max_candidates=max_candidates)
        finally:
            self._reports.append(fresh.report())
            self._active = None
            self.identity["used"] = self.calls > 0

    def report(self):
        attempts = [attempt for row in self._reports for attempt in row["attempts"]]
        return {"identity": copy.deepcopy(self.identity), "actual_model_calls": self.calls,
            "forward_attempts": self._sum("forward_attempts"), "forward_passes": self.forward_passes,
            "generated_token_slots": self.generated_tokens, "attempts": copy.deepcopy(attempts),
            "model_loaded": self.policy is not None, "load_attempted": self.load_attempted,
            "kernel_checked": False}

    def finalize(self):
        require(self._active is None, "Cannot finalize an active WMI decode.")
        if self.policy is not None:
            self.policy.finalize()
        if self._source_pins is not None:
            for name, pin in self._source_pins.items():
                require(trained._fingerprint(APP / name, 256 * 1024) == pin, "Runtime changed during inference: " + name)
        if self._helper_pins is not None:
            for name, pin in self._helper_pins.items():
                require(trained._fingerprint(FROZEN / name, 256 * 1024) == pin, "Frozen helper changed during inference: " + name)
        self.identity.update(used=self.calls > 0, load_attempted=self.load_attempted)
        result = self.report()
        result.update(model_calls=self.calls, model_decode_attempts=len(result["attempts"]),
            model_call_unit="actual single-tactic decodes with an attempted forward pass",
            proposal_call_unit="strict one-tactic provider requests", generated_token_steps=self.generated_tokens,
            proposals=[{"tactic": attempt["action"]} for attempt in result["attempts"] if "action" in attempt],
            authority_rejections=[attempt for attempt in result["attempts"] if attempt.get("status") == "rejected"])
        return result


class HistoricalGreedyPolicy(WMIModelPolicy):
    """Matched sequential baseline; the existing beam4 API remains unchanged."""
    selection_id = "hydra-mixed"
    name = "Saved mixed adapter · matched greedy local comparison"
    adapter_sha = trained.ADAPTER_SHA
    selected_step = None

    def __init__(self, capabilities, emit_progress=lambda event: None, **limits):
        super().__init__(capabilities, emit_progress, **limits)
        self.identity = {"name": self.name, "selection_id": self.selection_id,
            "adapter_sha256": trained.ADAPTER_SHA, "adapter_manifest_sha256": trained.MODEL_MANIFEST_SHA,
            "used": False, "quantized_preview": True, "numerical_equivalence_to_training": False,
            "automatic_retry": False, "automatic_fallback": False,
            "decoder_scope": "matched greedy1/full-prefix/128-new/6144-context; not legacy beam4/64/1536"}
        self.evaluation_identity = copy.deepcopy(self.identity)

    def prompt_renderer(self, goals):
        self._prepare()
        return self.policy.render_prompt(goals=tuple(goals), focus=0, environment=self.policy.environment)

    def _prepare(self):
        if self.policy is not None:
            return
        if self.load_attempted:
            raise RuntimeError("Historical initialization already failed; no automatic reload or fallback.")
        self.load_attempted = True
        self._source_pins = {name: trained._fingerprint(APP / name, 256 * 1024) for name in SOURCE_FILES}
        _data, evaluation, self._helper_pins = _frozen_helpers()
        candidate, handle, source_pin, inputs_pin = trained._load_authenticated()
        artifacts = trained._artifact_snapshot(handle)
        quantized, quantized_pin, ready_pin = trained._quantized_snapshot()
        from training.peano_policy.prompt import CapabilityIdentity, render_prompt
        from training.peano_policy.contract import authority_prompt_environment
        from training.peano_policy.authority import (AuthorityTokenConstraint, authority_contract_record,
            authority_profile_record, validate_authority_tactic)
        contract = handle.manifest["common_contract"]
        cap = contract["authority"]["capabilities"]
        environment = authority_prompt_environment(False, CapabilityIdentity.from_record({
            "label": cap["label"], "allowed_commands": cap["allowed_commands"], "allowed_theorems": cap["allowed_theorems"]}))
        require(authority_profile_record(environment) == contract["decoder_profile"]
                and authority_contract_record() == contract["prompt_contract"], "Historical prompt/authority changed.")
        require(self.capabilities.allowed_commands == frozenset(cap["allowed_commands"])
                and not self.capabilities.allowed_theorems and not cap["allowed_theorems"], "Historical execution authority differs.")
        self.emit({"phase": "loading", "message": "Loading the unchanged saved mixed adapter for matched greedy comparison.", "model_calls": 0})
        model, tokenizer, mx = trained._load_model(handle, quantized)
        provenance = {"checkpoint_sha256": trained.ADAPTER_SHA,
            "tokenizer_identity_sha256": handle.manifest["tokenizer"]["sha256"],
            "source_inventory_sha256": source_pin["sha256"], "run_id": "hydra-mixed-matched-local-greedy",
            "policy": {"kind": "fixed", "depth": 1}, "model_vocab_size": 151936}
        policy = CandidatePolicy(backend=MLXVanillaBackend(model, mx, kind="historical_primitive_v4"),
            tokenizer=tokenizer, kind="historical_primitive_v4", environment=environment, provenance=provenance,
            render_prompt=render_prompt, strict_generation=evaluation.strict_generation,
            check_prompt_binding=evaluation.check_prompt_binding, validate_tactic=validate_authority_tactic,
            constraint_factory=AuthorityTokenConstraint, limits=Limits(max_calls=1))

        def finalize():
            require(trained._artifact_snapshot(handle) == artifacts and trained._source_snapshot() == source_pin
                    and trained._fingerprint(trained.INPUTS, inputs_pin["bytes"]) == inputs_pin,
                    "Historical artifact/source inputs changed during matched comparison.")
            require(trained._quantized_snapshot() == (quantized, quantized_pin, ready_pin), "Historical local base changed.")
            return policy.report()

        policy.finalize = finalize
        self.policy = policy
        self.identity.update(backend="MLX", device="Apple Metal", loaded=True, memory_limit_bytes=MEMORY_LIMIT_BYTES,
            quantized_manifest_sha256=quantized_pin["sha256"], admission_receipt_sha256=candidate.admission_receipt_sha256)
        self.evaluation_identity = copy.deepcopy(self.identity)
