"""Separate mixed-retention SFT protocol; no legacy origin is manufactured.

The data reference must rejoin both genuine original receipts and every
selected original row. Only execute loads a model, after a trusted caller
checks the exact immutable resource request, approval, ledger and Slurm job.
Training starts from the pinned base with a new LoRA, not from either ancestor
adapter. The original tokenizer, completion loss, collator, finite-gradient
checks and tensor fingerprints are reused without modification.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import time

from training.peano_hydra import corrective_workflow as files, origin_bridge as bridge
from training.peano_hydra import posttrain, scaling_evaluation as original
from training.peano_policy.config import ExperimentConfig, load_config
from training.peano_policy.objective import completion_objective_record
from training.peano_policy.prompt import ProofExample

ROOT = Path(__file__).absolute().parents[2]
PROFILE = "peano-hydra-retention-pilot-v1"
RUN_ID = "retention-pilot-v1"
PACKAGE = "_deploy/hydra-retention-pilot-v1"
OUTPUT = "results/peano-hydra/qwen3-1.7b-authority-primitive-retention-pilot-v1"
INPUT_SCHEMA = "peano-hydra-retention-training-input-reference-v1"
PLAN_SCHEMA = "peano-hydra-retention-training-plan-v1"
AUTHORIZATION_SCHEMA = "peano-hydra-retention-training-authorization-v1"
TOKEN_SCHEMA = "peano-hydra-retention-token-preflight-v1"
ADAPTER_SCHEMA = "peano-hydra-retention-trained-adapter-v1"
ARTIFACT_REFERENCE_SCHEMA = "peano-hydra-retention-artifact-reference-v1"
INITIALIZATION = {"kind": "fresh-pinned-base-new-lora", "continued_from_ancestor_adapter": False}
MIXTURE = "static-mixture-deterministic-shuffle-single-epoch"
MODEL = {"model_id": posttrain.BASE_MODEL_ID, "revision": posttrain.BASE_MODEL_REVISION}
RESERVATION = {"seconds": 7200, "gpus": 1, "cpus": 8, "memory_gib": 64}
SEED = 20260826
MAX_METADATA = 4 * 1024**2
MAX_PROGRESS_BYTES = 4 * 1024**2
MAX_TRAIN_ROWS, MAX_DEV_ROWS = 16384, 4096
CLAIMS = {"research_claim_eligible": False, "sealed_benchmark": False,
          "benchmark_acceptance_eligible": False, "self_training_readiness_eligible": False,
          "historical_gpu_inference_attested": False, "legacy_origin_manufactured": False}
TRAINING_SOURCES = (
    "training/peano_hydra/retention_training.py", "training/peano_hydra/retention_data.py",
    "training/peano_hydra/retention_evaluation.py", "training/peano_hydra/posttrain.py",
    "training/peano_hydra/origin_bridge.py", "training/peano_hydra/review_runtime.py",
    "training/peano_hydra/scaling_evaluation.py", "training/peano_hydra/corrective_workflow.py",
    "training/peano_policy/config.py", "training/peano_policy/data.py",
    "training/peano_policy/objective.py", "training/peano_policy/budget.py",
    "training/peano_policy/train.py", "training/peano_policy/training_evidence.py",
    "training/peano_policy/manifest.py", "training/peano_policy/runtime.py",
    "training/peano_policy/prompt.py", "training/peano_policy/contract.py",
    "training/peano_policy/authority.py", "training/peano_policy/requirements-helios.lock",
)


class RetentionTrainingError(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise RetentionTrainingError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _sha(value, label):
    require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), label + " needs an external raw SHA256")
    return value


def _record(path, expected, maximum=MAX_METADATA):
    _sha(expected, "input")
    raw = bridge._read(bridge._absolute(Path(path)), maximum)
    require(hashlib.sha256(raw).hexdigest() == expected, "externally pinned input bytes changed")
    return bridge._decode(raw, maximum, "retention input"), raw


def training_sources():
    result = original.execution_sources()
    result.update({name: hashlib.sha256(bridge._read(ROOT / name, 2 * 1024**2)).hexdigest() for name in TRAINING_SOURCES})
    return dict(sorted(result.items()))


@dataclass(frozen=True, slots=True)
class TrainingInputReference:
    directory: Path
    manifest_sha256: str
    config_path: Path
    config_sha256: str
    baseline: original.OriginReference
    frontier: original.OriginReference
    evaluation_plan_path: Path
    evaluation_plan_sha256: str

    def __post_init__(self):
        for name in ("directory", "config_path", "evaluation_plan_path"):
            object.__setattr__(self, name, bridge._absolute(Path(getattr(self, name))))
        for name in ("manifest_sha256", "config_sha256", "evaluation_plan_sha256"):
            _sha(getattr(self, name), name)
        require(type(self.baseline) is original.OriginReference and type(self.frontier) is original.OriginReference,
                "retention needs both genuine original origin-reference types")

    def to_dict(self):
        return {"schema": INPUT_SCHEMA, "manifest_sha256": self.manifest_sha256,
            "config_sha256": self.config_sha256, "evaluation_plan_sha256": self.evaluation_plan_sha256,
            "origins": {"saved-v25": self.baseline.to_dict(), "frontier-v28": self.frontier.to_dict()}}

    def locations(self):
        return {"directory": str(self.directory), "config_path": str(self.config_path),
            "evaluation_plan_path": str(self.evaluation_plan_path),
            "origins": {name: {"request": ref.request.locations(), "receipt_path": str(ref.receipt_path)}
                for name, ref in (("saved-v25", self.baseline), ("frontier-v28", self.frontier))}}

    def protected_paths(self):
        paths = [self.directory, self.config_path.parent, self.evaluation_plan_path.parent]
        for ref in (self.baseline, self.frontier):
            paths.extend((ref.request.source_root, ref.request.source_manifest.parent,
                          ref.request.adapter_manifest.parent, ref.receipt_path.parent))
        return tuple(paths)

    def load(self):
        return bind_training(self)


def input_reference(identity, locations):
    """Explicit portable identity with separately supplied physical locations."""
    require(type(identity) is dict and set(identity) == {"schema", "manifest_sha256", "config_sha256",
        "evaluation_plan_sha256", "origins"} and identity["schema"] == INPUT_SCHEMA,
        "wrong retention input identity")
    require(type(locations) is dict and set(locations) == {"directory", "config_path", "evaluation_plan_path", "origins"}
        and set(identity["origins"]) == set(locations["origins"]) == {"saved-v25", "frontier-v28"},
        "retention input locations changed origin inventory")
    refs = {}
    for name in ("saved-v25", "frontier-v28"):
        entry, where = identity["origins"][name], locations["origins"][name]
        require(set(entry) == {"request", "receipt_sha256"} and set(where) == {"request", "receipt_path"},
                "origin location/identity fields changed")
        refs[name] = original.OriginReference(bridge._request(entry["request"], where["request"]),
                                            Path(where["receipt_path"]), entry["receipt_sha256"])
    result = TrainingInputReference(Path(locations["directory"]), identity["manifest_sha256"],
        Path(locations["config_path"]), identity["config_sha256"], refs["saved-v25"], refs["frontier-v28"],
        Path(locations["evaluation_plan_path"]), identity["evaluation_plan_sha256"])
    require(result.to_dict() == identity and result.locations() == locations, "retention paths are not canonical")
    return result


def _configuration(config, inputs):
    require(type(config) is ExperimentConfig, "original parsed configuration required")
    expected = {
        "model": {**MODEL, "dtype": "bfloat16", "attn_implementation": "sdpa", "trust_remote_code": False},
        "lora": {"rank": 16, "alpha": 32, "dropout": 0.05,
                 "target_modules": ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")},
        "trainer": {"epochs": 1.0, "max_steps": -1, "per_device_train_batch_size": 1,
            "per_device_eval_batch_size": 1, "gradient_accumulation_steps": 8, "learning_rate": 0.0001,
            "weight_decay": 0.01, "warmup_ratio": 0.05, "logging_steps": 1, "eval_steps": 100000,
            "save_steps": 100000, "save_total_limit": 1, "gradient_checkpointing": True},
        "generation": {"max_new_tokens": 128, "do_sample": False, "temperature": 1.0, "top_p": 1.0},
    }
    for section, values in expected.items():
        require(asdict(getattr(config, section)) == values, "retention changed the old/new " + section + " recipe")
    require(config.curriculum is None and config.run.seed == SEED and config.run.resume == "never"
        and config.run.max_train_samples is None and config.run.max_eval_samples is None
        and config.run.output_dir == OUTPUT and config.run.name == "qwen3-1.7b-" + RUN_ID
        and config.data.max_length == 4096, "retention run changed fresh-base single-epoch profile")
    try:
        relative = inputs.directory.relative_to(ROOT).as_posix()
    except ValueError as error:
        raise RetentionTrainingError("mixed preparation must be staged under this execution root") from error
    require(config.data.train_path == relative + "/train.jsonl" and config.data.eval_path == relative + "/dev.jsonl",
            "configuration points outside the exact mixed dataset")
    return {section: asdict(getattr(config, section)) for section in ("run", "model", "data", "lora", "trainer", "generation")}


@dataclass(frozen=True, slots=True)
class TrainingPlan:
    inputs: TrainingInputReference
    checked_data: object
    config: ExperimentConfig
    evaluation_plan: dict
    baseline: original.OriginReference
    frontier: original.OriginReference
    _record_json: str

    def to_dict(self):
        return json.loads(self._record_json)


def _native_source(ref, prepared):
    relative = prepared["source"]["directory"]
    require(type(relative) is str and not Path(relative).is_absolute()
        and all(part not in ("", ".", "..") for part in relative.split("/")), "original source location is not retained")
    return ref.request.source_root / relative


def bind_training(inputs):
    """No native/model work; genuine receipts plus complete original-row joins."""
    require(type(inputs) is TrainingInputReference, "exact retention input reference required")
    from training.peano_hydra import retention_data, retention_evaluation
    before = training_sources()
    checked = retention_data.load_preparation(inputs.directory, expected_manifest_sha256=inputs.manifest_sha256)
    require(checked.manifest["mixture_schedule"] == MIXTURE, "a static mixture cannot claim a temporal ramp")
    handles, preparations, adapters = {}, {}, {}
    for name, ref in (("saved-v25", inputs.baseline), ("frontier-v28", inputs.frontier)):
        handles[name] = ref.load()
        preparations[name], _ = _record(ref.request.preparation_directory / "manifest.json", ref.request.preparation_manifest_sha256)
        adapters[name], _ = _record(ref.request.adapter_manifest, ref.request.adapter_manifest_sha256)
        declared = checked.manifest["origins"][name]
        require(declared["preparation_manifest_sha256"] == ref.request.preparation_manifest_sha256
            and declared["source_manifest_sha256"] == preparations[name]["source"]["manifest_sha256"]
            and declared["epoch_sha256"] == handles[name].origin["epoch_sha256"],
            "mixed data did not join its actual original preparation/source/epoch")
    retention_data.verify_against_originals(checked,
        saved_preparation=inputs.baseline.request.preparation_directory,
        frontier_preparation=inputs.frontier.request.preparation_directory,
        frontier_source=_native_source(inputs.frontier, preparations["frontier-v28"]))
    common = ("model", "authority_profile", "authority", "prompt_contract", "decoder_profile", "tokenizer", "objective")
    require(all(adapters["saved-v25"][key] == adapters["frontier-v28"][key] for key in common)
        and adapters["saved-v25"]["model"] == MODEL
        and adapters["saved-v25"]["authority_profile"] == bridge.AUTHORITY_PROFILE
        and adapters["saved-v25"]["objective"] == completion_objective_record(),
        "retention sources do not share the exact pinned model/V4 prompt/tokenizer/objective")
    config_raw = bridge._read(inputs.config_path, 16384)
    require(hashlib.sha256(config_raw).hexdigest() == inputs.config_sha256, "retention config raw hash differs")
    config = load_config(inputs.config_path)
    configuration = _configuration(config, inputs)
    require(bridge._read(inputs.config_path, 16384) == config_raw, "retention config changed while parsing")
    evaluation_plan, _ = _record(inputs.evaluation_plan_path, inputs.evaluation_plan_sha256)
    retention_evaluation.validate_preparation_join(evaluation_plan, checked)
    require(evaluation_plan["preparation_manifest_sha256"] == checked.manifest_sha256,
            "scientific evaluation plan was not preregistered for this mixture")
    train_rows, dev_rows = len(checked.train_rows), len(checked.dev_rows)
    require(8932 < train_rows <= MAX_TRAIN_ROWS and dev_rows == 744 + 2096 <= MAX_DEV_ROWS,
            "retention row count escaped complete old data plus bounded frontier pilot")
    steps = math.ceil(train_rows / 8)
    record = {"schema": PLAN_SCHEMA, "profile": PROFILE, "run_id": RUN_ID,
        "inputs": inputs.to_dict(), "initialization": INITIALIZATION, "mixture_schedule": MIXTURE,
        "within_epoch_mixture_ramp": False, "configuration": configuration,
        "training_sources": before, "training_rows": train_rows, "development_rows": dev_rows,
        "expected_optimizer_steps": steps, "evaluation_plan_sha256": inputs.evaluation_plan_sha256,
        "ancestor_origins": {name: handle.origin for name, handle in handles.items()},
        "common_contract": {key: adapters["saved-v25"][key] for key in common},
        "token_limits": {"max_length": 4096, "max_train_tokens": posttrain.MAX_TRAIN_TOKENS,
            "max_dev_tokens": posttrain.MAX_DEV_TOKENS, "max_train_squared_tokens": posttrain.MAX_TRAIN_SQUARED_TOKENS,
            "max_dev_squared_tokens": posttrain.MAX_DEV_SQUARED_TOKENS, "max_supervised_tokens": 128},
        "resource_request_created": False, "model_training_authorized": False, "model_loaded": False, **CLAIMS}
    record["training_plan_sha256"] = digest(record)
    require(training_sources() == before, "retention execution code changed during binding")
    return TrainingPlan(inputs, checked, config, evaluation_plan, inputs.baseline, inputs.frontier, canonical(record).decode())


def _refresh(plan):
    require(type(plan) is TrainingPlan, "exact retention training plan required")
    refreshed = bind_training(plan.inputs)
    # The saved JSON does not contain the live row dictionaries. Compare every
    # dataclass field so stale/mutated rows, configuration, evaluation selection
    # or origin references cannot be consumed under the original saved identity.
    require(refreshed == plan,
            "retention source, original inputs, configuration or preregistered plan changed")


def _examples(plan, role):
    rows = plan.checked_data.train_rows if role == "train" else plan.checked_data.dev_rows
    return tuple(ProofExample(example_id=f"retention:{role}:{index + 1}:{digest(row)}",
        prompt=row["prompt"], completion=row["completion"], environment_sha256=row["environment_sha256"])
        for index, row in enumerate(rows))


def _tokenize(plan, tokenizer):
    from training.peano_policy.budget import enforce_token_budget, tokenize_split, tokenizer_identity_record
    require(tokenizer.eos_token_id is not None, "pinned tokenizer has no EOS")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    identity = tokenizer_identity_record(tokenizer, **MODEL)
    features, exposures = {}, {}
    for role in ("train", "dev"):
        features[role], exposures[role] = tokenize_split(_examples(plan, role), tokenizer, role=role,
            max_length=4096, tokenizer_identity=identity)
        enforce_token_budget(exposures[role],
            max_total_tokens=posttrain.MAX_TRAIN_TOKENS if role == "train" else posttrain.MAX_DEV_TOKENS,
            max_sum_squared_tokens=posttrain.MAX_TRAIN_SQUARED_TOKENS if role == "train" else posttrain.MAX_DEV_SQUARED_TOKENS,
            max_supervised_tokens=128)
    record = {"schema": TOKEN_SCHEMA, "training_plan_sha256": plan.to_dict()["training_plan_sha256"],
        "inputs": plan.inputs.to_dict(), "initialization": INITIALIZATION,
        "training_rows": len(features["train"]), "development_rows": len(features["dev"]),
        "expected_optimizer_steps": plan.to_dict()["expected_optimizer_steps"],
        "token_exposure": exposures, "model_weights_loaded": False, "model_training_authorized": False}
    record["token_preflight_sha256"] = digest(record)
    return features, record


def token_preflight(plan):
    """Explicit tokenizer-only CPU preflight; never allocate a model/GPU."""
    _refresh(plan)
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(MODEL["model_id"], revision=MODEL["revision"],
        use_fast=True, trust_remote_code=False, local_files_only=True)
    require((tokenizer.init_kwargs.get("_commit_hash") or MODEL["revision"]) == MODEL["revision"], "tokenizer revision drift")
    _, result = _tokenize(plan, tokenizer)
    _refresh(plan)
    return result


def _validate_token_record(plan, record, expected_sha):
    from training.peano_policy.budget import enforce_token_budget
    bound = plan.to_dict()
    require(type(record) is dict and set(record) == {"schema", "training_plan_sha256", "inputs", "initialization",
        "training_rows", "development_rows", "expected_optimizer_steps", "token_exposure", "model_weights_loaded",
        "model_training_authorized", "token_preflight_sha256"}
        and record["schema"] == TOKEN_SCHEMA and record["training_plan_sha256"] == bound["training_plan_sha256"]
        and record["inputs"] == plan.inputs.to_dict() and record["initialization"] == INITIALIZATION
        and record["model_weights_loaded"] is False and record["model_training_authorized"] is False
        and record["token_preflight_sha256"] == expected_sha
        and expected_sha == digest({key: value for key, value in record.items() if key != "token_preflight_sha256"})
        and set(record["token_exposure"]) == {"train", "dev"}
        and all(type(record[key]) is int and record[key] == bound[key]
                for key in ("training_rows", "development_rows", "expected_optimizer_steps")),
        "token preflight changed plan, counts, identity or no-model boundary")
    for role in ("train", "dev"):
        exposure = record["token_exposure"][role]
        require(exposure["role"] == role and exposure["max_length"] == 4096
            and exposure["rows"] == bound["training_rows" if role == "train" else "development_rows"]
            and exposure["tokenizer"]["model_id"] == MODEL["model_id"]
            and exposure["tokenizer"]["revision"] == MODEL["revision"], "tokenized population/model differs")
        enforce_token_budget(exposure,
            max_total_tokens=posttrain.MAX_TRAIN_TOKENS if role == "train" else posttrain.MAX_DEV_TOKENS,
            max_sum_squared_tokens=posttrain.MAX_TRAIN_SQUARED_TOKENS if role == "train" else posttrain.MAX_DEV_SQUARED_TOKENS,
            max_supervised_tokens=128)


def validate_training_authorization(plan, record, *, expected_authorization_sha256):
    """Validate caller-pinned scope; this assertion is not user approval."""
    _sha(expected_authorization_sha256, "training authorization")
    require(type(record) is dict and set(record) == {"schema", "training_plan_sha256", "token_preflight_sha256",
        "resource_approval_sha256", "resource_request_sha256", "model_training_authorized", "initialization",
        "max_wall_seconds", "gpu_count", "training_rows", "development_rows", "expected_optimizer_steps",
        "automatic_retry", "resume"}, "training authorization fields changed")
    for key in ("token_preflight_sha256", "resource_approval_sha256", "resource_request_sha256"):
        _sha(record[key], key)
    bound = plan.to_dict()
    require(digest(record) == expected_authorization_sha256 and record["schema"] == AUTHORIZATION_SCHEMA
        and record["training_plan_sha256"] == bound["training_plan_sha256"]
        and record["initialization"] == INITIALIZATION and record["model_training_authorized"] is True
        and type(record["max_wall_seconds"]) is int and record["max_wall_seconds"] == 7200
        and type(record["gpu_count"]) is int and record["gpu_count"] == 1
        and record["automatic_retry"] is False and record["resume"] is False
        and all(type(record[key]) is int and record[key] == bound[key]
                for key in ("training_rows", "development_rows", "expected_optimizer_steps")),
        "authorization changed exact mixture, fresh initialization, count or resource boundary")
    return json.loads(canonical(record))


def _reservation(record, authorization, *, live):
    require(type(record) is dict and record.get("status") == "job-verified" and record.get("profile") == PROFILE
        and record.get("run_id") == RUN_ID and record.get("stage") == "train"
        and record.get("approval_sha256") == authorization["resource_approval_sha256"]
        and record.get("resource_request_sha256") == authorization["resource_request_sha256"]
        and record.get("reservation") == RESERVATION and record.get("automatic_retry") is False
        and record.get("resume") is False and type(record.get("job_id")) is str
        and re.fullmatch(r"[1-9][0-9]{0,19}", record["job_id"]), "trusted callback returned another reserved job/scope")
    require(type(record.get("source_commit")) is str and re.fullmatch(r"[a-f0-9]{40}", record["source_commit"]),
            "actual immutable source commit missing")
    for key in ("source_files_sha256", "payloads_sha256"):
        _sha(record.get(key), key)
    elapsed, remaining = record.get("allocation_elapsed_seconds"), record.get("allocation_remaining_seconds")
    require(type(elapsed) is int and type(remaining) is int and 0 <= elapsed < 7200
        and remaining == 7200 - elapsed, "whole-allocation elapsed/remaining time is missing or inconsistent")
    if live:
        require(os.environ.get("SLURM_JOB_ID") == record["job_id"], "training is outside its exact actual Slurm job")
    return {key: value for key, value in record.items() if key not in ("allocation_elapsed_seconds", "allocation_remaining_seconds")}


class Progress:
    def __init__(self, stream=None):
        self.stream = sys.stdout if stream is None else stream
        self.bytes = 0

    def emit(self, phase, **values):
        value = {"schema": "peano-hydra-retention-training-progress-v1", "phase": phase, **values}
        raw = canonical(value) + b"\n"
        require(len(raw) <= 16384 and self.bytes + len(raw) <= MAX_PROGRESS_BYTES, "training progress output cap")
        self.stream.write(raw.decode())
        self.stream.flush()
        self.bytes += len(raw)


class _ProgressCallback:
    def __init__(self, progress, stopping):
        self.progress, self.stopping = progress, stopping

    def on_log(self, args, state, control, logs=None, **kwargs):
        self.progress.emit("optimizer-log", step=int(state.global_step), logs=posttrain._finite_metrics(logs or {}))
        return control

    def on_step_end(self, args, state, control, **kwargs):
        require(not self.stopping(), "retention whole-allocation stop; no automatic retry or resume")
        return control


def execute(plan, *, authorization, expected_authorization_sha256, reservation_check,
            stop_requested=None, progress=None, stop_after_seconds=6900):
    """One fresh model run after the caller's real immutable-job reservation."""
    require(type(plan) is TrainingPlan and callable(reservation_check)
        and (stop_requested is None or callable(stop_requested)), "genuine plan and trusted reservation checker required")
    require(type(stop_after_seconds) in (int, float) and math.isfinite(stop_after_seconds)
        and 0 < stop_after_seconds <= 6900, "training soft stop must leave room within the7200-second allocation")
    authorization = validate_training_authorization(plan, authorization, expected_authorization_sha256=expected_authorization_sha256)
    progress = progress or Progress()
    started = time.monotonic()
    reservation = reservation_check(authorization)
    reservation_identity = _reservation(reservation, authorization, live=True)
    allocation_started = started - reservation["allocation_elapsed_seconds"] - 1.0
    def stopping():
        return time.monotonic() - allocation_started >= stop_after_seconds or (stop_requested is not None and stop_requested())
    def boundary():
        require(not stopping(), "retention whole-allocation stop; uncompleted training remains unknown")
    boundary()
    _refresh(plan)
    require(os.environ.get("PYTHONHASHSEED") == str(SEED), "PYTHONHASHSEED must be fixed before Python starts")
    protected = plan.inputs.protected_paths()
    output = ROOT / OUTPUT
    files.guard_output(output, protected=protected)
    require(not output.exists() and not output.is_symlink(), "retention training requires a fresh output directory")
    provenance = posttrain._execution_provenance()
    posttrain._required_frameworks()
    boundary()
    progress.emit("framework-loading-start", initialization=INITIALIZATION, training_plan_sha256=plan.to_dict()["training_plan_sha256"])
    import torch
    import transformers
    from peft import LoraConfig, get_peft_model
    from training.peano_policy import training_evidence, manifest as artifacts
    from training.peano_policy.objective import CompletionOnlyTrainerMixin, require_indexed_logits_support, single_process_trainer_runtime_record
    from training.peano_policy.train import (_CompletionCollator, _FiniteGradientCallbackMixin, _claim_fresh_output_directory,
        _require_output_directory_unchanged, _set_seeds, _trainable_tensor_population_snapshot)
    require(torch.cuda.is_available() and torch.cuda.device_count() == 1 and torch.cuda.is_bf16_supported(),
            "retention needs the exact one-CUDA-GPU BF16 runtime")
    posttrain._process_count()
    posttrain._require_execution_provenance_unchanged(provenance)
    provenance = posttrain._execution_provenance(torch)
    _set_seeds(SEED, torch, transformers.set_seed)
    tokenizer = transformers.AutoTokenizer.from_pretrained(MODEL["model_id"], revision=MODEL["revision"],
        use_fast=True, trust_remote_code=False, local_files_only=True)
    require((tokenizer.init_kwargs.get("_commit_hash") or MODEL["revision"]) == MODEL["revision"], "tokenizer revision drift")
    features, tokens = _tokenize(plan, tokenizer)
    _validate_token_record(plan, tokens, authorization["token_preflight_sha256"])
    boundary()
    _refresh(plan)
    current = reservation_check(authorization)
    require(_reservation(current, authorization, live=True) == reservation_identity, "actual resource reservation changed before model loading")
    boundary()
    progress.emit("model-loading-start", initialization=INITIALIZATION)
    model = transformers.AutoModelForCausalLM.from_pretrained(MODEL["model_id"], revision=MODEL["revision"],
        torch_dtype=torch.bfloat16, attn_implementation="sdpa", trust_remote_code=False,
        use_safetensors=True, local_files_only=True)
    require((getattr(model.config, "_commit_hash", None) or MODEL["revision"]) == MODEL["revision"], "base revision drift")
    require_indexed_logits_support(model)
    model.config.use_cache = False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
    model.enable_input_require_grads()
    model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.05, bias="none",
        task_type="CAUSAL_LM", target_modules=list(plan.config.lora.target_modules)))
    named = [(name, parameter) for name, parameter in model.named_parameters() if parameter.requires_grad]
    initial = _trainable_tensor_population_snapshot(torch, named)
    steps = plan.to_dict()["expected_optimizer_steps"]
    audit = training_evidence.FiniteGradientAudit(expected_optimizer_steps=steps, trainable_parameter_names=initial.names)
    class CompletionTrainer(CompletionOnlyTrainerMixin, transformers.Trainer):
        pass
    class FiniteGradientCallback(_FiniteGradientCallbackMixin, transformers.TrainerCallback):
        pass
    class FlushedProgress(_ProgressCallback, transformers.TrainerCallback):
        pass
    boundary()
    output_identity = _claim_fresh_output_directory(output)
    try:
        args = transformers.TrainingArguments(output_dir=str(output), overwrite_output_dir=False, do_train=True, do_eval=True,
            num_train_epochs=1.0, max_steps=-1, per_device_train_batch_size=1, per_device_eval_batch_size=1,
            gradient_accumulation_steps=8, learning_rate=0.0001, weight_decay=0.01, warmup_ratio=0.05,
            lr_scheduler_type="cosine", optim="adamw_torch_fused", bf16=True, bf16_full_eval=False, tf32=True,
            gradient_checkpointing=True, gradient_checkpointing_kwargs={"use_reentrant": False}, max_grad_norm=0.0,
            logging_steps=1, logging_nan_inf_filter=False, eval_strategy="no", eval_steps=100000,
            save_strategy="no", save_steps=100000, save_total_limit=1, save_safetensors=True,
            report_to=[], seed=SEED, data_seed=SEED, dataloader_num_workers=0, remove_unused_columns=False,
            prediction_loss_only=True, label_names=["labels"], average_tokens_across_devices=True, disable_tqdm=True)
        trainer = CompletionTrainer(model=model, args=args, train_dataset=features["train"], eval_dataset=features["dev"],
            data_collator=_CompletionCollator(torch, tokenizer.pad_token_id), callbacks=[
                FiniteGradientCallback(torch=torch, named_parameters=named, audit=audit), FlushedProgress(progress, stopping)])
        trainer_runtime = single_process_trainer_runtime_record(trainer, expected_gradient_accumulation_steps=8)
        trainer_arguments = training_evidence.reviewed_trainer_arguments_record(trainer)
        progress.emit("training-start", training_rows=len(features["train"]), development_rows=len(features["dev"]),
                      expected_optimizer_steps=steps, mixture_schedule=MIXTURE, initialization=INITIALIZATION)
        trained = trainer.train(resume_from_checkpoint=False)
        require(trained.global_step == steps, "training did not complete its exact single-epoch optimizer schedule")
        gradients = audit.record()
        final = _trainable_tensor_population_snapshot(torch, named)
        require(initial.names == final.names, "trainable population changed during retention training")
        before, after = dict(initial.record_hashes), dict(final.record_hashes)
        update = training_evidence.adapter_update_audit_record(trainable_parameter_names=final.names,
            initial_tensor_population_sha256=initial.population_sha256, final_tensor_population_sha256=final.population_sha256,
            changed_parameter_names=tuple(name for name in final.names if before[name] != after[name]),
            final_finite_parameter_names=final.names)
        boundary()
        progress.emit("adapter-publication-start", optimizer_steps=steps)
        adapter_stage = Path(tempfile.mkdtemp(prefix=".adapter.partial-", dir=output))
        model.save_pretrained(adapter_stage, safe_serialization=True)
        artifacts.publish_staged_directory_noreplace(adapter_stage, output / artifacts.ADAPTER_SUBDIR)
        tokenizer_stage = Path(tempfile.mkdtemp(prefix=".tokenizer.partial-", dir=output))
        tokenizer.save_pretrained(str(tokenizer_stage))
        artifacts.publish_staged_directory_noreplace(tokenizer_stage, output / artifacts.TOKENIZER_SUBDIR)
        adapter = artifacts.artifact_directory_hash(output, artifacts.ADAPTER_SUBDIR)
        tokenizer_record = artifacts.artifact_directory_hash(output, artifacts.TOKENIZER_SUBDIR)
        artifacts.require_safetensors_adapter(adapter)
        require(tokenizer_record == plan.to_dict()["common_contract"]["tokenizer"], "retention tokenizer artifact bytes changed")
        boundary()
        progress.emit("development-loss-start", rows=len(features["dev"]))
        development = posttrain._finite_metrics(trainer.evaluate())
        require(_trainable_tensor_population_snapshot(torch, named) == final, "development evaluation changed adapter weights")
        boundary()
        _refresh(plan)
        _require_output_directory_unchanged(output_identity)
        posttrain._require_execution_provenance_unchanged(provenance, torch)
        final_reservation = reservation_check(authorization)
        require(_reservation(final_reservation, authorization, live=True) == reservation_identity,
                "actual immutable job/request/approval changed during training")
        record = {"schema": ADAPTER_SCHEMA, "profile": PROFILE, "run_id": RUN_ID, "model_trained": True,
            "training_plan": plan.to_dict(), "training_inputs": plan.inputs.to_dict(), "initialization": INITIALIZATION,
            "training_plan_sha256": plan.to_dict()["training_plan_sha256"], "mixture_schedule": MIXTURE,
            "within_epoch_mixture_ramp": False, "model": MODEL, "common_contract": plan.to_dict()["common_contract"],
            "adapter": adapter, "tokenizer": tokenizer_record, "objective": completion_objective_record(),
            "trainer_runtime": trainer_runtime, "trainer_arguments": trainer_arguments,
            "finite_gradient_audit": gradients, "adapter_update": update, "token_preflight": tokens,
            "metrics": {"training_rows": len(features["train"]), "development_rows": len(features["dev"]),
                "expected_optimizer_steps": steps, "actual_optimizer_steps": trained.global_step,
                "train": posttrain._finite_metrics(trained.metrics), "dev": development},
            "execution_provenance": provenance, "reservation": reservation, "final_reservation": final_reservation,
            "authorization": authorization, "authorization_sha256": expected_authorization_sha256,
            "observed_allocation_seconds": time.monotonic() - allocation_started,
            "progress_bytes": progress.bytes, "automatic_retry": False, "resume": False, **CLAIMS}
        _validate_artifact_record(plan, record)
        require(len(canonical(record)) + 1 <= MAX_METADATA, "completed mixed adapter manifest exceeds its byte bound")
        boundary()
        target = artifacts.write_manifest_noreplace(output / "manifest.json", record, compact=True)
        progress.emit("training-complete", manifest_sha256=hashlib.sha256(bridge._read(target, MAX_METADATA)).hexdigest(),
                      optimizer_steps=steps, train_loss=record["metrics"]["train"]["train_loss"], eval_loss=development["eval_loss"])
        return target
    except BaseException as error:
        files.write_new(output / "execution-status.json", {"schema": "peano-hydra-retention-training-interruption-v1",
            "training_plan_sha256": plan.to_dict()["training_plan_sha256"], "status": "incomplete-output-retained",
            "error_type": type(error).__name__, "error": " ".join(str(error).split())[:2048],
            "automatic_retry": False, "resume": False, "model_training_completion_claimed": False, **CLAIMS})
        raise


def _validate_artifact_record(plan, record):
    from training.peano_policy import training_evidence
    require(type(record) is dict and set(record) == {"schema", "profile", "run_id", "model_trained", "training_plan",
        "training_inputs", "initialization", "training_plan_sha256", "mixture_schedule", "within_epoch_mixture_ramp",
        "model", "common_contract", "adapter", "tokenizer", "objective", "trainer_runtime", "trainer_arguments",
        "finite_gradient_audit", "adapter_update", "token_preflight", "metrics", "execution_provenance",
        "reservation", "final_reservation", "authorization", "authorization_sha256", "observed_allocation_seconds",
        "progress_bytes", "automatic_retry", "resume", *CLAIMS}, "completed retention manifest fields changed")
    require(record.get("schema") == ADAPTER_SCHEMA and record.get("profile") == PROFILE and record.get("run_id") == RUN_ID
        and record.get("model_trained") is True and record.get("initialization") == INITIALIZATION
        and record.get("mixture_schedule") == MIXTURE and record.get("within_epoch_mixture_ramp") is False
        and record.get("model") == MODEL and record.get("training_plan") == plan.to_dict()
        and record.get("training_inputs") == plan.inputs.to_dict()
        and record.get("training_plan_sha256") == plan.to_dict()["training_plan_sha256"]
        and record.get("common_contract") == plan.to_dict()["common_contract"]
        and record.get("objective") == completion_objective_record()
        and record.get("automatic_retry") is False and record.get("resume") is False
        and all(record.get(key) is False for key in CLAIMS), "completed retention manifest changed the exact new protocol")
    authorization = validate_training_authorization(plan, record["authorization"], expected_authorization_sha256=record["authorization_sha256"])
    require(_reservation(record["reservation"], authorization, live=False) ==
            _reservation(record["final_reservation"], authorization, live=False), "saved resource identity changed")
    steps = plan.to_dict()["expected_optimizer_steps"]
    metrics = record["metrics"]
    require(all(type(metrics[key]) is int and metrics[key] == plan.to_dict()[key]
                for key in ("training_rows", "development_rows", "expected_optimizer_steps"))
        and type(metrics["actual_optimizer_steps"]) is int and metrics["actual_optimizer_steps"] == steps,
        "retention training schedule is incomplete")
    training_evidence._finite_metrics(metrics["train"], "train_loss", "retention training metrics")
    training_evidence._finite_metrics(metrics["dev"], "eval_loss", "retention development metrics")
    runtime = training_evidence._validate_runtime(record["trainer_runtime"])
    arguments = training_evidence._validate_trainer_arguments(record["trainer_arguments"])
    require(runtime["configured_trainer_gradient_accumulation_steps"] == arguments["gradient_accumulation_steps"] == 8,
            "completion gradient accumulation changed")
    gradients = training_evidence._validate_gradients(record["finite_gradient_audit"], steps)
    training_evidence._validate_adapter_update(record["adapter_update"], gradients=gradients)
    _validate_token_record(plan, record["token_preflight"], authorization["token_preflight_sha256"])
    provenance = record["execution_provenance"]
    require(type(provenance) is dict and set(provenance) == {"runtime", "deployment", "job", "requirements_verification"},
            "training execution provenance is incomplete")
    deployment, job, runtime = provenance["deployment"], provenance["job"], provenance["runtime"]
    lock = provenance["requirements_verification"]
    require(deployment["mode"] == "slurm" and deployment["source_sync"]["git_dirty"] is False
        and deployment["source_sync"]["git_commit"] == record["reservation"]["source_commit"]
        and job["job_id"] == record["reservation"]["job_id"] and job["deployment"] == deployment
        and lock["schema"] == posttrain.RUNTIME_LOCK_SCHEMA and lock["status"] == "verified"
        and lock["requirements"] == runtime["requirements"]
        and runtime["requirements"]["path"] == "training/peano_policy/requirements-helios.lock"
        and runtime["requirements"]["sha256"] == plan.to_dict()["training_sources"][runtime["requirements"]["path"]]
        and digest(lock["packages"]) == lock["packages_sha256"]
        and digest(runtime["packages"]) == runtime["packages_sha256"],
        "saved runtime/lock/source/job provenance no longer joins the actual reserved training")
    normalize = lambda name: re.sub(r"[-_.]+", "-", name).lower()
    installed = {normalize(name): version for name, version in runtime["packages"].items()}
    require(all(installed.get(normalize(name)) == version for name, version in lock["packages"].items()),
            "saved runtime packages differ from its checked lock")
    accelerator = runtime["accelerator"]
    require(runtime["machine"] == "aarch64" and accelerator["cuda_available"] is True
        and accelerator["bf16_supported"] is True and accelerator["device_capability"] == [9, 0]
        and accelerator["torch"] == runtime["packages"]["torch"], "saved runtime is not the reserved GH200 BF16 execution")
    require(record["tokenizer"] == plan.to_dict()["common_contract"]["tokenizer"], "common tokenizer identity changed")
    require(type(record["observed_allocation_seconds"]) in (int, float) and math.isfinite(record["observed_allocation_seconds"])
        and 0 < record["observed_allocation_seconds"] < 7200, "completed training exceeded its reservation")


@dataclass(frozen=True, slots=True)
class AuthenticatedRetentionArtifact:
    identity: dict
    adapter_directory: Path
    tokenizer_directory: Path
    checked_data: object
    manifest: dict
    plan: TrainingPlan

    def to_dict(self):
        return json.loads(canonical(self.identity))


@dataclass(frozen=True, slots=True)
class TrainingArtifactReference:
    manifest_path: Path
    manifest_sha256: str
    inputs: TrainingInputReference

    def __post_init__(self):
        object.__setattr__(self, "manifest_path", bridge._absolute(Path(self.manifest_path)))
        _sha(self.manifest_sha256, "mixed training manifest")
        require(self.manifest_path.name == "manifest.json" and type(self.inputs) is TrainingInputReference,
                "mixed adapter needs its own exact manifest and original inputs")

    def to_dict(self):
        return {"schema": ARTIFACT_REFERENCE_SCHEMA, "manifest_sha256": self.manifest_sha256,
                "training_inputs": self.inputs.to_dict()}

    def protected_paths(self):
        return (self.manifest_path.parent, *self.inputs.protected_paths())

    def load(self):
        return load_training_artifact(self)


def _verified_artifact_directories(root, record):
    """Check saved file bytes only; this does not admit training provenance."""
    from training.peano_policy import manifest as artifacts
    artifacts.require_safetensors_adapter(record["adapter"])
    adapter = artifacts.verify_artifact_directory(root, record["adapter"], "adapter")
    tokenizer = artifacts.verify_artifact_directory(root, record["tokenizer"], "tokenizer")
    return adapter, tokenizer


def load_training_artifact(reference):
    """Explicit mixed-adapter admission; no model/native worker is run."""
    require(type(reference) is TrainingArtifactReference, "exact new artifact-reference type required")
    plan = bind_training(reference.inputs)
    record, raw = _record(reference.manifest_path, reference.manifest_sha256)
    _validate_artifact_record(plan, record)
    adapter, tokenizer = _verified_artifact_directories(reference.manifest_path.parent, record)
    require(bridge._read(reference.manifest_path, MAX_METADATA) == raw, "mixed manifest changed during admission")
    require(training_sources() == plan.to_dict()["training_sources"], "mixed training implementation changed")
    contract = record["common_contract"]
    identity = {"schema": "peano-hydra-retention-artifact-identity-v1", "manifest_sha256": reference.manifest_sha256,
        "training_plan_sha256": record["training_plan_sha256"], "training_inputs": reference.inputs.to_dict(),
        "ancestor_origins": plan.to_dict()["ancestor_origins"], "model": MODEL,
        "training_authority_profile": contract["authority_profile"], "training_authority": contract["authority"],
        "training_prompt_contract": contract["prompt_contract"], "training_decoder_profile": contract["decoder_profile"],
        "artifacts": {"adapter": record["adapter"], "tokenizer": record["tokenizer"]},
        "initialization": INITIALIZATION, "job_id": record["reservation"]["job_id"],
        "claim_boundary": "Mixed retention SFT with both original data origins; no legacy origin, unseen-test or hardware attestation.",
        **CLAIMS}
    return AuthenticatedRetentionArtifact(identity, adapter, tokenizer, plan.checked_data, record, plan)
