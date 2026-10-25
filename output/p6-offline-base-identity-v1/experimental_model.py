"""Explicit experimental Qwen3 providers; no import-time model or network work.

Version 3 admits a fresh adapter's recorded local Base name only against the
caller's complete authenticated Base identity and exact ordinary directory.
This changes no saved artifact bytes and never selects a Base from adapter
metadata. The original strict settings validator remains unchanged.

This is a separate Torch/BF16, Linux/aarch64 contract. The historical saved
1.7B MLX provider is neither imported nor changed. Only an explicitly supplied
local snapshot and, optionally, an exactly pinned completed decision-pilot
adapter can load. The caller owns the live allocation and process/RSS guard.
Generated tactics/plans are untrusted and never execute in this module.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import importlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import platform
import re
import stat
import struct
import sys
import time

APP = Path(__file__).resolve().parent
REGISTRY_PATH = APP / "experimental-models/qwen3-base-v1.json"
REGISTRY_SHA256 = "3303c4727052557a04bc2e33ea624ff7093703c68ae8fa95b12fb05adbc781c1"
PROFILE = "hydra-experimental-torch-qwen3-v3"
ADAPTER_BASE_IDENTITY = "hydra-peft-authenticated-local-base-v1"
PREDECESSOR_SOURCE_SHA256 = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
PRIMITIVE_DECODER = "hydra-experimental-torch-authority-primitive-v1"
GENERATION_ACCOUNTING = "hydra-transformers-4.53.3-beam-slots-v2"
PLANNER_INPUT = "hydra-raw-base-planner-input-v1"
MAX_INPUT_TOKENS = 4096
MAX_PRIMITIVE_TOKENS = 64
MAX_PLANNER_TOKENS = 512
MAX_CANDIDATES = 16
MAX_CALLS = 128
MAX_TOKEN_SLOTS = 131072
MAX_ADAPTER_BYTES = 256 * 1024**2
MAX_METADATA_BYTES = 16 * 1024**2
MAX_HEADER_BYTES = 1024**2
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_REV = re.compile(r"[0-9a-f]{40}\Z")
_LOADED = object()
MODULES = ("q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj")
HISTORICAL_MANIFEST_SHA256 = "cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca"
HISTORICAL_ADAPTER_SHA256 = "7b86fc09aafa5bbb7b443119384e6b83f1f5a5f51a44340c0ca8b2e7a3b4d7c5"


class ModelAdmissionError(ValueError):
    """Input has no exact supported experimental model interpretation."""


class ExperimentalCancelled(RuntimeError):
    """The host's cooperative stop/deadline was observed."""


def _require(condition, message):
    if not condition:
        raise ModelAdmissionError(message)


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def _json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "Duplicate metadata key.")
            result[key] = value
        return result
    def constant(value):
        raise ModelAdmissionError("Non-finite metadata number: " + value)
    try:
        result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
    except (json.JSONDecodeError, UnicodeError, RecursionError) as error:
        raise ModelAdmissionError("Malformed bounded JSON metadata.") from error
    _require(type(result) is dict, "Metadata must be a JSON object.")
    return result


def _stop(should_stop):
    if should_stop is not None and should_stop():
        raise ExperimentalCancelled("The host stopped the experimental model operation.")


def _stat(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _file(path, *, maximum, expected=None, read=False, should_stop=None):
    """Stable bounded regular-file read; callers decide whether a cache link is allowed."""
    _stop(should_stop)
    path = Path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        _require(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= maximum,
                 "Expected a bounded regular model artifact.")
        digest = sha256()
        pieces = [] if read else None
        total = 0
        while block := stream.read(1024**2):
            _stop(should_stop)
            total += len(block)
            _require(total <= maximum, "Artifact grew beyond its byte bound.")
            digest.update(block)
            if read:
                pieces.append(block)
        _require(_stat(os.fstat(stream.fileno())) == _stat(before), "Artifact changed while read.")
    _require(total == before.st_size and _stat(path.lstat()) == _stat(before),
             "Artifact changed while read.")
    descriptor = {"bytes": total, "sha256": digest.hexdigest()}
    _require(expected is None or descriptor == expected, "Pinned artifact bytes changed: " + path.name)
    return descriptor, (b"".join(pieces) if read else None), _stat(before)


def registry():
    descriptor, raw, _ = _file(REGISTRY_PATH, maximum=65536, read=True)
    _require(descriptor["sha256"] == REGISTRY_SHA256, "Experimental registry bytes changed.")
    value = _json(raw)
    _require(value.get("schema") == "hydra-experimental-qwen3-base-registry-v1"
             and set(value["models"]) == {"qwen3-1.7b-base", "qwen3-4b-base", "qwen3-8b-base"},
             "Expected the exact finite experimental Base registry.")
    return value


def model_spec(key):
    _require(type(key) is str, "An explicit model registry key is required.")
    data = registry()
    _require(key in data["models"], "Model is not in the finite experimental allowlist.")
    return data["models"][key]


def metadata_status():
    """Cheap declared support, never a claim that weights or a device are ready."""
    data = registry()
    return {"profile": PROFILE, "registry_sha256": REGISTRY_SHA256,
            "models": [{"key": key, "model_id": value["model_id"], "revision": value["revision"],
                        "architecture": value["config"]["architectures"][0],
                        "base_weight_bytes": sum(f["bytes"] for f in value["weight_files"].values())}
                       for key, value in data["models"].items()],
            "backend": data["inference_backend"], "model_loaded": False, "available": False,
            "local_mlx_supported": False, "automatic_download": False,
            "detail": "Explicit remote allocation and authenticated local files are required; no model has been loaded."}


def expected_lora_shapes(spec, *, saved=True):
    """Derive every matrix from actual head/hidden dimensions, including Qwen3-4B."""
    c = spec["config"]
    hidden, intermediate = c["hidden_size"], c["intermediate_size"]
    query = c["num_attention_heads"] * c["head_dim"]
    key_value = c["num_key_value_heads"] * c["head_dim"]
    dimensions = {"q_proj": (hidden, query), "k_proj": (hidden, key_value),
                  "v_proj": (hidden, key_value), "o_proj": (query, hidden),
                  "gate_proj": (hidden, intermediate), "up_proj": (hidden, intermediate),
                  "down_proj": (intermediate, hidden)}
    result = {}
    suffix = ".weight" if saved else ".default.weight"
    for layer in range(c["num_hidden_layers"]):
        for module, (inputs, outputs) in dimensions.items():
            group = "self_attn" if module in MODULES[:4] else "mlp"
            prefix = f"base_model.model.model.layers.{layer}.{group}.{module}"
            result[prefix + ".lora_A" + suffix] = (16, inputs)
            result[prefix + ".lora_B" + suffix] = (outputs, 16)
    return result


def validate_adapter_config(config, spec):
    expected = {"alpha_pattern": {}, "auto_mapping": None,
        "base_model_name_or_path": spec["model_id"], "bias": "none", "corda_config": None,
        "eva_config": None, "exclude_modules": None, "fan_in_fan_out": False,
        "inference_mode": True, "init_lora_weights": True, "layer_replication": None,
        "layers_pattern": None, "layers_to_transform": None, "loftq_config": {},
        "lora_alpha": 32, "lora_bias": False, "lora_dropout": 0.05, "megatron_config": None,
        "megatron_core": "megatron.core", "modules_to_save": None, "peft_type": "LORA",
        "qalora_group_size": 16, "r": 16, "rank_pattern": {}, "revision": None,
        "task_type": "CAUSAL_LM", "trainable_token_indices": None, "use_dora": False,
        "use_qalora": False, "use_rslora": False}
    _require(type(config) is dict and set(config) == set(expected) | {"target_modules"},
             "Unexpected PEFT configuration fields.")
    _require(type(config["target_modules"]) is list and len(config["target_modules"]) == len(MODULES)
             and set(config["target_modules"]) == set(MODULES), "Unexpected LoRA target population.")
    normalized = {k: v for k, v in config.items() if k != "target_modules"}
    _require(_canonical(normalized) == _canonical(expected), "PEFT settings/base identity differ from the matched pilot.")
    return True


def validate_adapter_config_with_base_identity(config, spec, *, adapter_kind,
        artifact, authenticated_base=None, authenticated_base_directory=None):
    """Validate a recorded name, never load a Base from that name.

The context must come from authenticate_base() or the loader's full _base_files
authentication. A matching name alone is insufficient: the complete registered
file identity must also equal both saved training and token-preflight records.
This pure settings check performs no model loading or Base-file hashing itself.
"""
    _require(adapter_kind in {"fresh_decision_pilot", "historical_retention"}
             and type(config) is dict, "Unknown adapter settings admission.")
    _require((authenticated_base is None) == (authenticated_base_directory is None),
             "Authenticated Base context and directory must be supplied together.")
    directory = None
    if authenticated_base is not None:
        _require(adapter_kind == "fresh_decision_pilot" and type(authenticated_base) is dict,
                 "Historical adapters retain the original strict Base-name contract.")
        _require(spec["model_id"] in {"Qwen/Qwen3-1.7B-Base", "Qwen/Qwen3-4B-Base", "Qwen/Qwen3-8B-Base"},
                 "The Base identity is outside the finite model registry.")
        key = spec["model_id"].split("/", 1)[1].lower()
        expected = _authenticated_base_record(key, spec,
            {**spec["metadata_files"], **spec["weight_files"]})
        _require(_canonical(authenticated_base) == _canonical(expected),
                 "Authenticated Base context differs from the complete registered file identity.")
        _require(type(artifact) is dict and type(artifact.get("token_preflight")) is dict
                 and artifact.get("model") == {"model_id": spec["model_id"], "revision": spec["revision"]}
                 and _canonical(artifact.get("base")) == _canonical(authenticated_base)
                 and _canonical(artifact["token_preflight"].get("base")) == _canonical(authenticated_base),
                 "Training/token-preflight Base identities differ from the authenticated context.")
        _require(isinstance(authenticated_base_directory, (str, Path)),
                 "An explicit ordinary authenticated Base directory is required.")
        directory_text = str(authenticated_base_directory)
        _require(0 < len(directory_text) <= 4096 and "\x00" not in directory_text,
                 "Malformed authenticated Base directory.")
        directory = Path(directory_text)
        _require(directory.is_absolute() and directory.as_posix() == directory_text
                 and ".." not in directory.parts and directory.resolve(strict=True) == directory
                 and directory.is_dir() and not directory.is_symlink(),
                 "The authenticated Base directory must be an exact ordinary absolute path.")
    normalized = dict(config)
    observed_name = config.get("base_model_name_or_path")
    local_name_used = observed_name != spec["model_id"]
    if local_name_used:
        _require(adapter_kind == "fresh_decision_pilot" and directory is not None
                 and type(observed_name) is str and observed_name == str(directory),
                 "Recorded local Base name is not the explicitly authenticated directory.")
        normalized["base_model_name_or_path"] = spec["model_id"]
    validate_adapter_config(normalized, spec)
    return {"schema": "hydra-peft-base-identity-admission-v1", "policy": ADAPTER_BASE_IDENTITY,
        "adapter_kind": adapter_kind, "local_base_name_used": local_name_used,
        "recorded_name_matches_authenticated_directory": directory is not None and observed_name == str(directory),
        "canonical_base_model_id": spec["model_id"],
        "authenticated_base_identity_sha256": (authenticated_base["base_identity_sha256"]
                                                if authenticated_base is not None else None),
        "authenticated_base_directory_sha256": (sha256(str(directory).encode("utf-8")).hexdigest()
                                                if directory is not None else None),
        "original_config_canonical_sha256": sha256(_canonical(config)).hexdigest(),
        "validated_config_canonical_sha256": sha256(_canonical(normalized)).hexdigest(),
        "normalization_fields": ["base_model_name_or_path"] if local_name_used else [],
        "saved_config_modified": False, "base_selected_from_adapter_metadata": False}


def validate_adapter_header(header, payload_bytes, spec):
    """Pure shape/dtype/offset validation; no tensor contents or framework needed."""
    _require(type(header) is dict and type(payload_bytes) is int and 0 < payload_bytes <= MAX_ADAPTER_BYTES,
             "Malformed adapter header or payload size.")
    meta = header.get("__metadata__", {})
    _require(type(meta) is dict and set(meta) <= {"format"} and meta.get("format", "pt") == "pt",
             "Unsupported adapter tensor format.")
    tensors = {name: value for name, value in header.items() if name != "__metadata__"}
    expected = expected_lora_shapes(spec)
    _require(set(tensors) == set(expected), "Adapter tensor population does not match the selected architecture.")
    intervals = []
    for name, shape in expected.items():
        value = tensors[name]
        _require(type(value) is dict and set(value) == {"dtype", "shape", "data_offsets"}
                 and value["dtype"] == "F32" and type(value["shape"]) is list
                 and all(type(x) is int for x in value["shape"]) and tuple(value["shape"]) == shape,
                 "Adapter matrix shape/dtype differs: " + name)
        offsets = value["data_offsets"]
        _require(type(offsets) is list and len(offsets) == 2 and all(type(x) is int for x in offsets)
                 and 0 <= offsets[0] < offsets[1] <= payload_bytes
                 and offsets[1] - offsets[0] == math.prod(shape) * 4,
                 "Adapter tensor byte offsets are malformed.")
        intervals.append(tuple(offsets))
    cursor = 0
    for start, end in sorted(intervals):
        _require(start == cursor, "Adapter payload has overlapping, omitted or extraneous bytes.")
        cursor = end
    _require(cursor == payload_bytes, "Adapter payload includes unaccounted bytes.")
    return {"tensors": len(tensors), "payload_bytes": payload_bytes, "dtype": "float32"}


def inspect_adapter_header(path, spec):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        _require(stat.S_ISREG(before.st_mode) and 8 < before.st_size <= MAX_ADAPTER_BYTES,
                 "Expected a bounded regular safetensors adapter.")
        prefix = stream.read(8)
        _require(len(prefix) == 8, "Missing safetensors length prefix.")
        size, = struct.unpack("<Q", prefix)
        _require(0 < size <= MAX_HEADER_BYTES and size + 8 < before.st_size, "Oversized safetensors header.")
        raw = stream.read(size)
        _require(len(raw) == size and _stat(os.fstat(stream.fileno())) == _stat(before),
                 "Adapter header changed during inspection.")
    _require(_stat(Path(path).lstat()) == _stat(before), "Adapter changed during header inspection.")
    return validate_adapter_header(_json(raw), before.st_size - 8 - size, spec)


def _training(name):
    path = str(APP / "training-v5")
    if path not in sys.path:
        sys.path.insert(0, path)
    return importlib.import_module("hydra_training_v5.peano_policy." + name)


def _reservation(record):
    _require(type(record) is dict and type(record.get("job_id")) is str
             and re.fullmatch(r"[0-9_]{1,40}", record["job_id"]) is not None,
             "The host must report an actual owned scheduler job.")
    for key, ceiling in (("gpus", 1), ("cpus", 8), ("memory_gib", 64), ("seconds", 7200)):
        value = record.get(key)
        _require(type(value) is int and 1 <= value <= ceiling, "Reservation exceeds the experiment ceiling.")
    elapsed = record.get("elapsed_seconds")
    _require(type(elapsed) in (int, float) and math.isfinite(elapsed)
             and 0 <= elapsed < record["seconds"] - 10, "No live allocation remains for cleanup.")
    return {key: record[key] for key in ("job_id", "gpus", "cpus", "memory_gib", "seconds")}


def _base_files(directory, spec, should_stop):
    """Authenticate all files. HF cache links are resolved once and then watched."""
    directory = Path(directory).resolve(strict=True)
    _require(directory.is_dir(), "Explicit local Base snapshot directory required.")
    descriptors = {**spec["metadata_files"], **spec["weight_files"]}
    names = set()
    with os.scandir(directory) as entries:
        for entry in entries:
            names.add(entry.name)
            _require(len(names) <= 32, "Base snapshot inventory exceeds its finite file bound.")
    _require(set(descriptors) <= names
             and names <= set(descriptors) | {"README.md", ".gitattributes", "LICENSE", "LICENSE.txt"},
             "Base directory has missing or unlisted loadable artifacts.")
    actual, watched = {}, []
    for name, expected in sorted(descriptors.items()):
        _require("/" not in name and name not in {".", ".."}, "Unsafe registry path.")
        logical = directory / name
        resolved = logical.resolve(strict=True)
        descriptor, _, identity = _file(resolved, maximum=expected["bytes"], expected=expected,
                                       should_stop=should_stop)
        actual[name] = descriptor
        watched.append((logical, resolved, identity))
    return directory, actual, watched


def authenticate_base(base_key, base_directory, *, should_stop=None):
    """Read-only full-shard/config/tokenizer authentication, without a framework.

    A portable identity is returned; it is the same for materialized files and
    an exact HF cache snapshot. The training caller should compare this at its
    preflight, load and finalization boundaries. Nothing is downloaded.
    """
    _require(should_stop is None or callable(should_stop), "Malformed cancellation callback.")
    spec = model_spec(base_key)
    _, files, watched = _base_files(base_directory, spec, should_stop)
    _unchanged(watched)
    return _authenticated_base_record(base_key, spec, files)


def _authenticated_base_record(base_key, spec, files):
    record = {"schema": "hydra-experimental-authenticated-base-v1", "registry_sha256": REGISTRY_SHA256,
              "model_key": base_key, "model_id": spec["model_id"], "revision": spec["revision"],
              "files": files, "model_loaded": False, "weight_bytes_fully_hashed": True}
    record["base_identity_sha256"] = sha256(_canonical(record)).hexdigest()
    return record


def _unchanged(watched):
    for logical, resolved, identity in watched:
        _require(logical.resolve(strict=True) == resolved and _stat(resolved.lstat()) == identity,
                 "A previously authenticated artifact changed during model loading.")


def _adapter(directory, expected_sha, spec, should_stop, adapter_kind, *,
             authenticated_base=None, authenticated_base_directory=None, admission_evidence=None):
    _require(admission_evidence is None or (type(admission_evidence) is dict and not admission_evidence),
             "Adapter admission evidence must be a fresh empty dictionary when requested.")
    _require(type(expected_sha) is str and _SHA.fullmatch(expected_sha), "Exact adapter manifest SHA-256 required.")
    directory = Path(directory)
    _require(directory.is_dir() and not directory.is_symlink(), "Ordinary completed adapter directory required.")
    descriptor, raw, manifest_stat = _file(directory / "manifest.json", maximum=4 * 1024**2,
                                          read=True, should_stop=should_stop)
    _require(descriptor["sha256"] == expected_sha, "Selected training manifest changed.")
    record = _json(raw)
    _require(record.get("model_trained") is True and record.get("resume") is False
             and record.get("automatic_retry") is False, "Adapter is not a completed non-resumed training artifact.")
    _require(not (directory / "incomplete.json").exists(), "An incomplete training attempt cannot supply inference weights.")
    if adapter_kind == "historical_retention":
        _require(expected_sha == HISTORICAL_MANIFEST_SHA256
                 and record.get("schema") == "peano-hydra-retention-trained-adapter-v1"
                 and spec["model_id"] == "Qwen/Qwen3-1.7B-Base"
                 and record["model"] == {"model_id": spec["model_id"], "revision": spec["revision"]}
                 and record["reservation"]["job_id"] == "21456251"
                 and record["adapter"]["files"]["adapter/adapter_model.safetensors"] == HISTORICAL_ADAPTER_SHA256,
                 "Historical control must be the exact preserved mixed-retention artifact.")
        steps = record["metrics"]["actual_optimizer_steps"]
        _require(type(steps) is int and steps == 1469 == record["metrics"]["expected_optimizer_steps"],
                 "Historical training completion evidence differs.")
    else:
        _require(adapter_kind == "fresh_decision_pilot"
                 and record.get("schema") == "hydra-decision-pilot-artifact-v1"
                 and record.get("saved_adapter_reload_admission") == "required_by_P6_before_inference",
                 "Adapter is not a completed fresh decision pilot awaiting reload admission.")
        plan = record["plan"]
        _require(plan["model"] == {"model_id": spec["model_id"], "revision": spec["revision"]}
                 and plan["prompt_schema"] == "primitive_v4" and plan["planner_rows_allowed"] is False
                 and plan["epochs"] == 1 and plan["resume"] is False
                 and type(plan["training_rows"]) is int and 1 <= plan["training_rows"] <= 4096
                 and type(plan["validation_rows"]) is int and 1 <= plan["validation_rows"] <= 4096,
                 "Adapter model, training contract or bounded data exposure differs.")
        unsigned = {k: v for k, v in plan.items() if k != "plan_sha256"}
        _require(sha256(_canonical(unsigned)).hexdigest() == plan["plan_sha256"], "Training plan identity changed.")
        steps = record["actual_optimizer_steps"]
        _require(type(steps) is int and steps == plan["expected_optimizer_steps"]
                 == (plan["training_rows"] + 7) // 8, "Training has no complete one-pass optimizer trace.")
    evidence = _training("training_evidence")
    gradients = evidence._validate_gradients(record["finite_gradient_audit"], steps)
    evidence._validate_adapter_update(record["adapter_update"], gradients=gradients)
    _require(tuple(record["adapter_update"]["trainable_parameter_names"])
             == tuple(sorted(expected_lora_shapes(spec, saved=False))), "Trained matrix population differs from this model.")
    paths = {}
    watched = [(directory / "manifest.json", (directory / "manifest.json").resolve(), manifest_stat)]
    for root_name, maximum in (("adapter", MAX_ADAPTER_BYTES), ("tokenizer", 32 * 1024**2)):
        group = record[root_name]
        _require(type(group) is dict and group.get("root") == root_name
                 and type(group.get("files")) is dict and 1 <= len(group["files"]) <= 16,
                 "Invalid bounded artifact tree.")
        artifact_root = directory / root_name
        _require(artifact_root.is_dir() and not artifact_root.is_symlink(), "Ordinary artifact directory required.")
        actual_names = set()
        with os.scandir(artifact_root) as entries:
            for entry in entries:
                _require(not entry.is_symlink() and entry.is_file(follow_symlinks=False),
                         "Artifact trees must be flat regular files without links.")
                actual_names.add(root_name + "/" + entry.name)
                _require(len(actual_names) <= 16, "Artifact inventory exceeds its finite bound.")
        _require(actual_names == set(group["files"]), "Artifact inventory differs from its complete manifest.")
        total = 0
        observed_hashes = {}
        for name, digest in group["files"].items():
            _require(type(name) is str and name.startswith(root_name + "/") and name.count("/") == 1
                     and type(digest) is str and _SHA.fullmatch(digest), "Unsafe artifact inventory.")
            path = directory / name
            _require(not path.is_symlink() and path.is_file(), "Artifact symlink/non-file is not allowed.")
            total += path.stat().st_size
            _require(total <= maximum, "Artifact tree exceeds its byte ceiling.")
            observed, _, identity = _file(path, maximum=maximum, should_stop=should_stop)
            _require(observed["sha256"] == digest, "Artifact file differs from its pinned complete manifest.")
            observed_hashes[name] = observed["sha256"]
            watched.append((path, path.resolve(), identity))
        _require(sha256(_canonical(observed_hashes)).hexdigest() == group.get("sha256"),
                 "Artifact tree aggregate identity differs.")
        paths[root_name] = artifact_root
    _require(set(record["adapter"]["files"]) <= {
        "adapter/README.md", "adapter/adapter_config.json", "adapter/adapter_model.safetensors"}
        and {"adapter/adapter_config.json", "adapter/adapter_model.safetensors"} <= set(record["adapter"]["files"]),
        "Adapter has unexpected payloads.")
    config_file, config_raw, _ = _file(paths["adapter"] / "adapter_config.json", maximum=65536, read=True)
    config_admission = validate_adapter_config_with_base_identity(_json(config_raw), spec,
        adapter_kind=adapter_kind, artifact=record, authenticated_base=authenticated_base,
        authenticated_base_directory=authenticated_base_directory)
    header = inspect_adapter_header(paths["adapter"] / "adapter_model.safetensors", spec)
    if admission_evidence is not None:
        admission_evidence.update(config_admission, config_file=config_file)
    return record, paths, watched, header


@dataclass(frozen=True)
class SessionLimits:
    max_calls: int = MAX_CALLS
    max_token_slots: int = MAX_TOKEN_SLOTS

    def __post_init__(self):
        _require(type(self.max_calls) is int and 1 <= self.max_calls <= MAX_CALLS
                 and type(self.max_token_slots) is int and 1 <= self.max_token_slots <= MAX_TOKEN_SLOTS,
                 "Experimental session limits exceed their finite ceilings.")


def load_torch_model(base_key, *, base_directory, adapter_directory=None,
                     adapter_manifest_sha256=None, adapter_kind="fresh_decision_pilot",
                     reservation_check, should_stop=None,
                     limits=SessionLimits(), seed=0):
    """Authenticate and load once inside the caller's already allocated GH200 job.

    reservation_check must inspect the caller's actual live scheduler reservation.
    No scheduler, transfer, download, retry, training, or native proof runs here.
    Missing/bad dependencies, input files, allocation or architecture fail closed.
    """
    _require(callable(reservation_check) and (should_stop is None or callable(should_stop))
             and type(limits) is SessionLimits and type(seed) is int and 0 <= seed < 2**32,
             "Explicit host reservation/stop contract and bounded seed required.")
    spec, catalog = model_spec(base_key), registry()
    _require((adapter_directory is None) == (adapter_manifest_sha256 is None),
             "Adapter directory and exact manifest identity must be supplied together.")
    _require(adapter_kind in {"fresh_decision_pilot", "historical_retention"}
             and (adapter_directory is not None or adapter_kind == "fresh_decision_pilot"),
             "Unknown adapter contract or historical control without its exact artifact.")
    _require(platform.system() == "Linux" and platform.machine() == "aarch64"
             and sys.version_info[:3] == (3, 13, 5), "This new backend is remote Linux/aarch64 Python3.13.5 only.")
    allocation = _reservation(reservation_check())
    def boundary():
        _stop(should_stop)
        _require(_reservation(reservation_check()) == allocation, "Owned scheduler reservation changed.")
    boundary()
    actual_versions = {name: importlib.metadata.version(name) for name in catalog["dependencies"]}
    _require(actual_versions == catalog["dependencies"], "Experimental Torch dependency identity differs.")
    base_path, base_descriptors, watched = _base_files(base_directory, spec, should_stop)
    base_identity = _authenticated_base_record(base_key, spec, base_descriptors)
    trained = None
    adapter_paths = None
    header = None
    config_admission = {}
    if adapter_directory is not None:
        trained, adapter_paths, adapter_watched, header = _adapter(
            adapter_directory, adapter_manifest_sha256, spec, should_stop, adapter_kind,
            authenticated_base=base_identity if adapter_kind == "fresh_decision_pilot" else None,
            authenticated_base_directory=base_path if adapter_kind == "fresh_decision_pilot" else None,
            admission_evidence=config_admission)
        watched.extend(adapter_watched)
        if adapter_kind == "fresh_decision_pilot":
            _require(trained.get("base") == base_identity and trained["token_preflight"].get("base") == base_identity,
                     "Evaluation Base bytes differ from the complete training/token preflight identity.")
    boundary()
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    _require(torch.cuda.is_available() and torch.cuda.device_count() == 1 and torch.cuda.is_bf16_supported(),
             "Exactly one BF16 CUDA device is required; there is no CPU or MLX fallback.")
    device = torch.cuda.get_device_properties(0)
    _require(device.major == 9 and "GH200" in device.name, "The reviewed remote backend requires one GH200.")
    torch.set_num_threads(allocation["cpus"])
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    tokenizer = AutoTokenizer.from_pretrained(str(base_path), local_files_only=True,
                                             use_fast=True, trust_remote_code=False)
    _require(tokenizer.eos_token_id == spec["config"]["eos_token_id"]
             and tokenizer.is_fast and len(tokenizer) <= spec["config"]["vocab_size"],
             "Loaded tokenizer identity differs from the pinned Base.")
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    tokenizer_identity = sha256(_canonical({k: v for k, v in spec["metadata_files"].items()
                                          if k in {"tokenizer.json", "tokenizer_config.json", "merges.txt", "vocab.json"}})).hexdigest()
    if trained is not None:
        saved_tokenizer = AutoTokenizer.from_pretrained(str(adapter_paths["tokenizer"]),
            local_files_only=True, use_fast=True, trust_remote_code=False)
        saved_tokenizer.pad_token = saved_tokenizer.eos_token
        saved_tokenizer.padding_side = "right"
        _require(_json(tokenizer.backend_tokenizer.to_str()) == _json(saved_tokenizer.backend_tokenizer.to_str()),
                 "Saved tokenizer's complete tokenization pipeline differs from the pinned Base.")
        identity = _training("budget").tokenizer_identity_record(saved_tokenizer,
                    model_id=spec["model_id"], revision=spec["revision"])
        trained_tokenizer = (trained["token_preflight"]["token_exposure"]["train"]["tokenizer"]
                             if adapter_kind == "historical_retention" else trained["token_preflight"]["tokenizer"])
        _require(identity == trained_tokenizer, "Saved tokenizer differs from training preflight.")
        tokenizer = saved_tokenizer
        tokenizer_identity = trained["tokenizer"]["sha256"]
    boundary()
    model = AutoModelForCausalLM.from_pretrained(str(base_path), torch_dtype=torch.bfloat16,
        attn_implementation="sdpa", local_files_only=True, trust_remote_code=False,
        use_safetensors=True, device_map={"": "cuda:0"})
    observed_config = model.config.to_dict()
    for key, expected in spec["config"].items():
        if key in {"transformers_version", "use_cache"}:
            continue
        _require(observed_config.get(key) == expected, "Loaded architecture configuration differs: " + key)
    _require(type(model).__name__ == "Qwen3ForCausalLM", "Unexpected causal model implementation.")
    reload_record = {"adapter_present": False, "saved_adapter_reload_checked": False}
    if trained is not None:
        boundary()
        from peft import PeftModel
        model = PeftModel.from_pretrained(model, str(adapter_paths["adapter"]),
            is_trainable=False, local_files_only=True, use_safetensors=True, autocast_adapter_dtype=True)
        named = [(name, value) for name, value in model.named_parameters() if ".lora_" in name]
        expected = expected_lora_shapes(spec, saved=False)
        _require({name: tuple(value.shape) for name, value in named} == expected
                 and all(value.dtype == torch.float32 for _, value in named),
                 "Reloaded PEFT matrix population/dtype differs from the trained artifact.")
        snapshot = _training("train")._trainable_tensor_population_snapshot(torch, named)
        _require(snapshot.population_sha256 == trained["adapter_update"]["final_tensor_population_sha256"],
                 "Reloaded saved adapter differs from the final trained tensor population.")
        reload_record = {"adapter_present": True, "saved_adapter_reload_checked": True,
                         "final_tensor_population_sha256": snapshot.population_sha256,
                         "adapter_manifest_sha256": adapter_manifest_sha256, "header": header,
                         "training_contract": "primitive_v4", "planner_trained": False,
                         "adapter_kind": adapter_kind, "archived_evaluation_equivalent": False,
                         "base_identity_admission": config_admission}
    model.eval()
    model.requires_grad_(False)
    model.config.use_cache = True
    boundary()
    _unchanged(watched)
    identity = {"schema": "hydra-experimental-loaded-model-v1", "profile": PROFILE,
        "registry_sha256": REGISTRY_SHA256, "model_id": spec["model_id"], "revision": spec["revision"],
        "base_files": base_descriptors, "architecture": spec["config"], "backend": catalog["inference_backend"],
        "base_identity_sha256": base_identity["base_identity_sha256"], "seed": seed,
        "frameworks": actual_versions, "tokenizer_sha256": tokenizer_identity,
        "adapter": reload_record, "allocation": allocation, "device": device.name,
        "model_loaded": True, "model_calls": 0, "kernel_checked": False,
        "automatic_download": False, "automatic_retry": False,
        "generation_accounting": GENERATION_ACCOUNTING,
        "adapter_base_identity_policy": ADAPTER_BASE_IDENTITY,
        "predecessor_source_sha256": PREDECESSOR_SOURCE_SHA256,
        "source_sha256": sha256(Path(__file__).read_bytes()).hexdigest()}
    identity["model_manifest_sha256"] = sha256(_canonical(identity)).hexdigest()
    return TorchModelSession(_LOADED, model, tokenizer, torch, identity, limits, boundary, should_stop)


class _GenerationLedger:
    """Count width * observed decode iterations, including cancelled attempts.

    Transformers 4.53.3 checks an overselected beam-candidate pool before
    selecting the next live beams. With one prompt and our scalar EOS this
    callback has 2 * width rows; greedy has one. Candidate alternatives are
    not additional model-generated beam slots. The masks/decoder are unchanged.
    https://github.com/huggingface/transformers/blob/v4.53.3/src/transformers/generation/utils.py#L3998-L4003
    https://github.com/huggingface/transformers/blob/v4.53.3/src/transformers/generation/utils.py#L4144-L4151
    """
    def __init__(self, prompt_length, width, maximum, account, should_stop):
        _require(type(prompt_length) is int and 0 < prompt_length <= MAX_INPUT_TOKENS
                 and type(width) is int and 1 <= width <= MAX_CANDIDATES
                 and type(maximum) is int and 1 <= maximum <= MAX_PLANNER_TOKENS,
                 "Unexpected decoder accounting dimensions.")
        self.prompt_length, self.width, self.maximum = prompt_length, width, maximum
        self.account, self.should_stop = account, should_stop
        self.callback_rows = 1 if width == 1 else 2 * width
        self.last_rows = self.last_columns = None
        self.seen = 0

    def observe(self, rows, columns):
        self.last_rows = rows if type(rows) is int else None
        self.last_columns = columns if type(columns) is int else None
        _require(type(rows) is int and type(columns) is int and rows == self.callback_rows,
                 "Unexpected decoder stopping-criterion candidate population.")
        new_length = columns - self.prompt_length
        _require(self.seen <= new_length <= self.maximum, "Unexpected decoder token length.")
        added = (new_length - self.seen) * self.width
        self.seen = new_length
        self.account(added)
        _stop(self.should_stop)
        return False

    def __call__(self, input_ids, scores, **kwargs):
        _require(len(input_ids.shape) == 2, "Decoder stopping criterion requires two-dimensional candidates.")
        return self.observe(int(input_ids.shape[0]), int(input_ids.shape[1]))

    def report(self):
        return {"policy": GENERATION_ACCOUNTING, "beam_width": self.width,
                "expected_callback_rows": self.callback_rows, "last_observed_rows": self.last_rows,
                "last_observed_columns": self.last_columns, "prompt_tokens": self.prompt_length,
                "max_new_tokens": self.maximum, "observed_decode_iterations": self.seen,
                "generated_token_slots": self.width * self.seen}


class TorchModelSession:
    def __init__(self, permit, model, tokenizer, torch, identity, limits, boundary, should_stop):
        _require(permit is _LOADED, "Sessions can only be created by the real authenticated loader.")
        self.model, self.tokenizer, self.torch = model, tokenizer, torch
        self.identity, self.limits = identity, limits
        self.boundary, self.should_stop = boundary, should_stop
        self.calls = self.generated_tokens = self.forward_passes = 0
        self._busy = False
        self.last_generation_accounting = None

    def encode(self, prompt):
        _require(type(prompt) is str and 0 < len(prompt.encode("utf-8")) <= 128 * 1024,
                 "Full model input exceeds its byte bound; nothing was truncated.")
        _stop(self.should_stop)
        tokens = self.tokenizer.encode(prompt, add_special_tokens=False)
        _require(type(tokens) is list and all(type(t) is int and 0 <= t < 151936 for t in tokens),
                 "Tokenizer returned malformed IDs.")
        return tuple(tokens)

    def generate(self, input_ids, *, maximum, width, tracker, environment=None, should_stop=None):
        _require(type(input_ids) is tuple and 0 < len(input_ids) <= MAX_INPUT_TOKENS
                 and all(type(t) is int and 0 <= t < 151936 for t in input_ids),
                 "Full input exceeds the 4096-token bound; nothing was truncated.")
        _require(type(width) is int and 1 <= width <= MAX_CANDIDATES
                 and type(maximum) is int and 1 <= maximum <= (MAX_PRIMITIVE_TOKENS if environment else MAX_PLANNER_TOKENS)
                 and (environment is not None or width == 1), "Unsupported generation dimensions.")
        _require(not self._busy and self.calls < self.limits.max_calls
                 and self.generated_tokens + maximum * width <= self.limits.max_token_slots,
                 "Shared experimental model budget exhausted or a decode is already active.")
        def stop():
            return bool((self.should_stop and self.should_stop()) or (should_stop and should_stop()))
        _stop(stop)
        self.boundary()
        torch = self.torch
        from transformers import GenerationConfig, StoppingCriteriaList
        encoded = torch.tensor([list(input_ids)], dtype=torch.long, device="cuda:0")
        attention = torch.ones_like(encoded)
        def account(count):
            self.generated_tokens += count
            tracker.generated_tokens += count
        ledger = _GenerationLedger(len(input_ids), width, maximum, account, stop)
        options = {"max_new_tokens": maximum, "do_sample": False, "num_beams": width,
            "num_return_sequences": width, "bos_token_id": self.tokenizer.eos_token_id,
            "eos_token_id": self.tokenizer.eos_token_id, "pad_token_id": self.tokenizer.eos_token_id,
            "use_cache": True, "return_dict_in_generate": False, "output_scores": False,
            "output_attentions": False, "output_hidden_states": False}
        if width > 1:
            options.update(early_stopping=True, length_penalty=1.0)
        constraints = {}
        if environment is not None:
            constraints = _training("authority_runtime").generation_constraints(self.model, self.tokenizer,
                environment, prompt_length=len(input_ids), max_new_tokens=maximum)
        forward_model = self.model.get_base_model() if hasattr(self.model, "get_base_model") else self.model
        def forward_hook(module, inputs):
            self.forward_passes += 1
        hook = forward_model.register_forward_pre_hook(forward_hook)
        self._busy = True
        try:
            _stop(stop)
            self.calls += 1
            tracker.calls += 1
            with torch.inference_mode():
                output = self.model.generate(input_ids=encoded, attention_mask=attention,
                    generation_config=GenerationConfig(**options),
                    stopping_criteria=StoppingCriteriaList([ledger]), **constraints)
            _require(len(output.shape) == 2 and output.shape[0] == width
                     and len(input_ids) < output.shape[1] <= len(input_ids) + maximum,
                     "Decoder returned unexpected sequence dimensions.")
            rows = output.tolist()
            _require(all(tuple(row[:len(input_ids)]) == input_ids for row in rows),
                     "Decoder changed its full input prefix.")
            suffixes = tuple(tuple(row[len(input_ids):]) for row in rows)
            # Greedy planner output must include every produced token, even EOS.
            # Beam search may return padded finished sequences; accounting keeps
            # the actual width*iterations observed by its stopping criterion.
            if width == 1:
                _require(ledger.seen == len(suffixes[0]), "Greedy decode token accounting differs from actual output.")
            _stop(stop)
            return suffixes
        finally:
            self.last_generation_accounting = ledger.report()
            self._busy = False
            hook.remove()

    def report(self):
        return {"identity": self.identity, "actual_model_calls": self.calls,
                "generated_token_slots": self.generated_tokens, "forward_passes": self.forward_passes,
                "token_count_unit": "actual beam width times emitted decode iterations, including cancelled attempts",
                "generation_accounting": GENERATION_ACCOUNTING,
                "last_generation_accounting": None if self.last_generation_accounting is None else dict(self.last_generation_accounting),
                "kernel_checked": False}


class TorchPrimitivePolicy:
    """The ordinary full-state primitive-v4 prompt and finite native authority."""
    def __init__(self, session, environment):
        _require(type(session) is TorchModelSession, "An authenticated Torch session is required.")
        prompt = _training("prompt")
        _require(type(environment) is prompt.PromptEnvironment and environment.prompt_version == prompt.PEANO_PROMPT_V4,
                 "This experimental primitive provider requires the explicit full-state v4 prompt.")
        self.session, self.environment = session, environment
        self.calls = self.generated_tokens = self.rejected = 0
        self.policy_environment = _training("contract").environment_record(environment)
        self.evaluation_identity = {"name": PROFILE + ":primitive", "kind": "experimental-real-torch-primitive",
            "model": session.identity, "decoder": PRIMITIVE_DECODER, "environment": self.policy_environment,
            "max_input_tokens": MAX_INPUT_TOKENS, "max_new_tokens": MAX_PRIMITIVE_TOKENS,
            "max_candidates": MAX_CANDIDATES, "sampling": False, "repair": False,
            "kernel_checked": False, "historical_provider": False}

    def propose(self, goals_before, *, max_candidates):
        _require(type(goals_before) is tuple and 0 < len(goals_before) <= 64
                 and all(type(g) is str and g.strip() for g in goals_before)
                 and sum(len(g.encode()) for g in goals_before) <= 128 * 1024,
                 "The provider requires the complete bounded ordered native goal tuple.")
        _require(type(max_candidates) is int and 1 <= max_candidates <= MAX_CANDIDATES,
                 "Primitive candidate count exceeds its explicit bound.")
        prompt = _training("prompt").render_prompt(goals=goals_before, focus=0, environment=self.environment)
        ids = self.session.encode(prompt)
        output = self.session.generate(ids, maximum=MAX_PRIMITIVE_TOKENS, width=max_candidates,
                                       tracker=self, environment=self.environment)
        validate = _training("authority").validate_authority_tactic
        accepted = []
        for tokens in output:
            text = self.session.tokenizer.decode(list(tokens), skip_special_tokens=True,
                                                  clean_up_tokenization_spaces=False)
            try:
                line = validate(text, self.environment)
                _require(len(line.encode()) <= 512, "Generated primitive line exceeds its native boundary.")
            except (TypeError, ValueError):
                self.rejected += 1
                continue
            if line not in accepted:
                accepted.append(line)
        return tuple(accepted)


class TorchPlannerBackend:
    """Real P4 backend; raw Base text input, greedy JSON output, no line decoder."""
    def __init__(self, session, *, allow_primitive_adapter=False):
        _require(type(session) is TorchModelSession, "An authenticated Torch session is required.")
        _require(type(allow_primitive_adapter) is bool, "Cross-contract adapter choice must be explicit.")
        _require(not session.identity["adapter"]["adapter_present"] or allow_primitive_adapter,
                 "A primitive-trained adapter needs explicit opt-in for untrained JSON-plan inference.")
        from planner_provider import PlannerBackendIdentity
        self.session = session
        self.calls = self.generated_tokens = 0
        self.identity = PlannerBackendIdentity(
            name=PROFILE + ":planner", architecture="Qwen3ForCausalLM",
            model_manifest_sha256=session.identity["model_manifest_sha256"],
            tokenizer_sha256=session.identity["tokenizer_sha256"],
            runtime_identity=PROFILE + ":" + PLANNER_INPUT, kind="local_model")
        # P4's 'local_model' means a real in-process model, including a remote
        # scheduled worker; it does not mean the user's Apple laptop.

    def encode_prompt(self, prompt):
        from proof_planner import PlannerCancelled, PlannerLimit
        try:
            return self.session.encode(prompt)
        except ExperimentalCancelled as error:
            raise PlannerCancelled(str(error)) from error
        except ModelAdmissionError as error:
            raise PlannerLimit(str(error)) from error

    def generate(self, input_ids, *, max_new_tokens, should_stop=None):
        from proof_planner import PlannerCancelled
        try:
            return self.session.generate(input_ids, maximum=max_new_tokens, width=1,
                tracker=self, should_stop=should_stop)[0]
        except ExperimentalCancelled as error:
            raise PlannerCancelled(str(error)) from error

    def decode_output(self, output_ids):
        _require(type(output_ids) in (tuple, list) and len(output_ids) <= MAX_PLANNER_TOKENS,
                 "Planner output token bound exceeded.")
        return self.session.tokenizer.decode(list(output_ids), skip_special_tokens=True,
                                              clean_up_tokenization_spaces=False)


if __name__ == "__main__":
    # Deliberately metadata-only: the host must supply a real reservation callback
    # and own the model process. CLI invocation never allocates or loads weights.
    _require(len(sys.argv) == 1, "No implicit inference CLI; use the explicit host-owned loader API.")
    print(json.dumps(metadata_status(), indent=2))
