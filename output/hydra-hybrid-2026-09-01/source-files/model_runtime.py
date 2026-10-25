"""Read-only local inference for the saved Hydra mixed-retention adapter.

The base is an explicitly different, locally quantized preview.  The original
adapter, tokenizer, prompt and primitive authority keep their saved identities.
Only the preserved Peano search/kernel can decide whether a proposal proves a
theorem.  Importing this module or asking for status never loads a framework.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import sys
import time

APP = Path(__file__).resolve().parent
ROOT = APP.parent
SOURCE = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831"
SOURCE_COMMIT = "dca88930b59e3147a95d0234d804076ccf757a74"
SOURCE_CATALOG = SOURCE / "_deploy/hydra-retention-evaluation-recovery-source.json"
SOURCE_CATALOG_SHA = "f866666c81c94a6c0c2db685c27f5dfa5c68d84508c5652d848e820caf9b741c"
INPUTS = SOURCE / "_deploy/hydra-retention-evaluation-recovery-v1/inputs.json"
INPUTS_SHA = "e8dae306086368b059f2085441ae3e6ffbf46c7394c84275db7e21af61340a70"
MODEL_ROOT = ROOT / "artifacts/hydra-retention-pilot-2026-08-30/trained-model-collected-01/model"
MODEL_MANIFEST_SHA = "cdacbda7777568120029b671374aaf16e994f2da2a54b867a00c81ece086d6ca"
ADAPTER_SHA = "7b86fc09aafa5bbb7b443119384e6b83f1f5a5f51a44340c0ca8b2e7a3b4d7c5"
RUNTIME = APP / ".runtime"
QUANTIZED = RUNTIME / "model"
RUNTIME_PYTHON = RUNTIME / "venv/bin/python3"
READY = RUNTIME / "model-ready.json"
NAME = "Mixed adapter · 4-bit local preview"
MODEL_ID = "Qwen/Qwen3-1.7B-Base"
REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
ORIGINAL_WEIGHT_BYTES = 3_441_185_608
ORIGINAL_WEIGHT_SHA = "6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841"
QUANTIZATION = {"bits": 4, "group_size": 64, "mode": "affine"}
DEPENDENCIES = {"mlx": "0.29.4", "mlx-metal": "0.29.4", "mlx-lm": "0.28.3",
                "transformers": "4.53.3", "tokenizers": "0.21.2", "numpy": "2.3.1"}
DECODER = "hydra-playground-mlx-authority-beam-v1"
MAX_NEW_TOKENS = 64
MAX_PROMPT_TOKENS = 1536
MAX_QUANTIZED_BYTES = 1150 * 1024 * 1024
RUNTIME_IMPLEMENTED = True
_HEX = re.compile(r"[0-9a-f]{64}\Z")
LORA_KEYS = ("self_attn.q_proj", "self_attn.k_proj", "self_attn.v_proj", "self_attn.o_proj",
             "mlp.gate_proj", "mlp.up_proj", "mlp.down_proj")
LORA_DIMS = {"self_attn.q_proj": (2048, 2048), "self_attn.k_proj": (2048, 1024),
             "self_attn.v_proj": (2048, 1024), "self_attn.o_proj": (2048, 2048),
             "mlp.gate_proj": (2048, 6144), "mlp.up_proj": (2048, 6144),
             "mlp.down_proj": (6144, 2048)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def _progress(sink, event):
    """Only UI previews may be omitted; full proof/search records are untouched."""
    raw = json.dumps(event, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")
    if len(raw) > 3500:
        event = {key: value for key, value in event.items() if key not in {"goals", "candidates"}}
        event["preview_omitted_for_byte_limit"] = True
    require(len(json.dumps(event, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode("utf-8")) <= 3500,
            "Progress metadata exceeded its fixed byte bound.")
    sink(event)


def _json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate metadata key.")
            result[key] = value
        return result

    def invalid(_):
        raise ValueError("Non-finite metadata number.")

    value = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    require(type(value) is dict, "Metadata must be an object.")
    return value


def _stable(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_nlink,
            info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def _safe_path(root, relative):
    require(type(relative) is str and not PurePosixPath(relative).is_absolute()
            and PurePosixPath(relative).as_posix() == relative
            and not set(PurePosixPath(relative).parts) & {".", ".."}, "Unsafe input path.")
    require(root.is_dir() and not root.is_symlink(), "Input directory must not be a link.")
    path = root
    for part in PurePosixPath(relative).parts:
        path = path / part
        require(not path.is_symlink(), "Input paths may not follow symbolic links.")
    return path


def _small(path, maximum=4 * 1024 * 1024, expected=None):
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 < info.st_size <= maximum,
                "Expected a bounded, regular metadata file.")
        raw = stream.read(maximum + 1)
        require(_stable(os.fstat(stream.fileno())) == _stable(info), "Metadata changed while reading.")
    require(len(raw) == info.st_size and _stable(path.lstat()) == _stable(info), "Metadata changed while reading.")
    digest = hashlib.sha256(raw).hexdigest()
    require(expected is None or digest == expected, "Pinned metadata bytes changed.")
    return _json(raw), {"bytes": len(raw), "sha256": digest}


def _fingerprint(path, maximum):
    digest = hashlib.sha256()
    total = 0
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as stream:
        info = os.fstat(stream.fileno())
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and 0 <= info.st_size <= maximum,
                "Expected a bounded regular input file, without links.")
        while block := stream.read(1024 * 1024):
            total += len(block)
            require(total <= maximum, "Input exceeded its declared byte bound.")
            digest.update(block)
        require(_stable(os.fstat(stream.fileno())) == _stable(info), "Input changed while hashing.")
    require(total == info.st_size and _stable(path.lstat()) == _stable(info), "Input changed while hashing.")
    return {"bytes": total, "sha256": digest.hexdigest()}


def metadata_status():
    """Cheap availability only; every real search rehashes and authenticates inputs."""
    result = {"available": False, "name": NAME, "device": "Apple Metal",
              "quantized_preview": True, "numerical_equivalence_to_training": False,
              "model_id": MODEL_ID, "revision": REVISION,
              "adapter_manifest_sha256": MODEL_MANIFEST_SHA,
              "detail": "The compact local model runtime has not been prepared. Manual proof checking is available."}
    try:
        if not RUNTIME_IMPLEMENTED:
            result["detail"] = "The local model loader is being prepared. Manual proof checking is available."
            return result
        require(RUNTIME_PYTHON.is_file(), "The compact Python environment is not installed.")
        _readiness()
        record, pin = _small(QUANTIZED / "manifest.json")
        _validate_quantized_record(record)
        require(all((QUANTIZED / relative).is_file() and not (QUANTIZED / relative).is_symlink()
                    and (QUANTIZED / relative).stat().st_size == descriptor["bytes"]
                    for relative, descriptor in record["files"].items()),
                "The compact model files are incomplete.")
        for package, version in DEPENDENCIES.items():
            require(importlib.metadata.version(package) == version,
                    "Start the playground with its prepared .runtime/venv/bin/python3 environment.")
        result.update(available=True, quantized_manifest_sha256=pin["sha256"],
                      detail="Exploratory local preview of the saved mixed adapter. Quantization and local decoding differ from the GH200 evaluation; accepted proofs still pass the original kernel.")
    except (OSError, ValueError, KeyError, TypeError, importlib.metadata.PackageNotFoundError) as error:
        result["detail"] = " ".join(str(error).split())[:512] or "The compact runtime is unavailable."
    return result


def _validate_quantized_record(record):
    require(record.get("schema") == "hydra-playground-local-quantized-model-v1"
            and record.get("status") == "complete"
            and record.get("numerical_equivalence_to_training") is False,
            "The compact model has no completed conversion manifest.")
    original = record["original_model"]
    require(original["model_id"] == MODEL_ID and original["revision"] == REVISION
            and original["bytes"] == ORIGINAL_WEIGHT_BYTES and original["sha256"] == ORIGINAL_WEIGHT_SHA,
            "The compact model is not derived from the exact trained Base weights.")
    require(record["quantization"] == QUANTIZATION, "Unexpected local quantization profile.")
    require(record.get("full_original_sha256_verified") is True and record.get("all_output_files_rehashed") is True
            and record.get("raw_checkpoint_saved") is False and record.get("training_performed") is False,
            "Compact conversion did not retain the required original-weight checks.")
    files = record["files"]
    require(type(files) is dict and 3 <= len(files) <= 1024 and "config.json" in files
            and "model.safetensors.index.json" in files, "Incomplete compact-model inventory.")
    total = 0
    for relative, descriptor in files.items():
        require(type(relative) is str and PurePosixPath(relative).as_posix() == relative
                and not PurePosixPath(relative).is_absolute() and len(PurePosixPath(relative).parts) == 1
                and relative not in {".", "..", "manifest.json"}, "Unsafe compact-model path.")
        require(type(descriptor) is dict and type(descriptor.get("bytes")) is int
                and 0 < descriptor["bytes"] <= MAX_QUANTIZED_BYTES
                and type(descriptor.get("sha256")) is str and _HEX.fullmatch(descriptor["sha256"]),
                "Invalid compact-model file descriptor.")
        total += descriptor["bytes"]
    require(total <= MAX_QUANTIZED_BYTES, "Compact model exceeds its fixed disk bound.")
    require(record.get("original_config") == {"path": "original-config.json", "bytes": 727,
            "sha256": "1bb33a92c3548fbc68b889b490e810440435253598835bd71dff0396060c12db"},
            "The exact original Base configuration is not retained.")


def _quantized_config(record):
    original, original_pin = _small(QUANTIZED / "original-config.json", 727,
        expected="1bb33a92c3548fbc68b889b490e810440435253598835bd71dff0396060c12db")
    require(original_pin == {key: record["original_config"][key] for key in ("bytes", "sha256")},
            "Original Base configuration descriptor changed.")
    config, _ = _small(QUANTIZED / "config.json", 64 * 1024)
    require(config == {**original, "quantization": QUANTIZATION, "quantization_config": QUANTIZATION},
            "The local configuration changes more than the declared quantization.")
    return config


def _readiness():
    """A real observed setup exit, rather than a provisional converter manifest."""
    ready, ready_pin = _small(READY, 64 * 1024)
    require(ready.get("schema") == "hydra-playground-model-ready-v1" and ready.get("status") == "ready"
            and ready.get("numerical_equivalence_to_training") is False
            and ready.get("automatic_training") is False, "Local model setup has not been confirmed complete.")
    descriptors = ((ready["setup_invocation"], RUNTIME / "setup-invocation.json"),
                   (ready["model_manifest"], QUANTIZED / "manifest.json"))
    for descriptor, path in descriptors:
        require(descriptor["path"] == str(path)
                and _fingerprint(path, 4 * 1024 * 1024) == {key: descriptor[key] for key in ("bytes", "sha256")},
                "Completed setup evidence no longer matches its actual bytes.")
    invocation, _ = _small(RUNTIME / "setup-invocation.json", 64 * 1024)
    require(invocation.get("schema") == "hydra-playground-setup-invocation-v1"
            and invocation.get("status") == "exited" and type(invocation.get("exit_code")) is int
            and invocation["exit_code"] == 0 and invocation.get("automatic_retry") is False
            and invocation.get("observed_from") == "actual-tool-process-completion"
            and invocation["model_manifest"] == ready["model_manifest"],
            "Setup has no actual successful process-completion receipt.")
    helper = invocation["helper"]
    require(helper["path"] == str(APP / "setup_model.py")
            and _fingerprint(APP / "setup_model.py", 256 * 1024)
            == {key: helper[key] for key in ("bytes", "sha256")}, "Setup helper bytes changed.")
    require(type(invocation["argv"]) is list and all(type(item) is str for item in invocation["argv"])
            and str(APP / "setup_model.py") in invocation["argv"], "Setup receipt lacks its actual helper invocation.")
    return ready, ready_pin


def _source_snapshot():
    catalog, pin = _small(SOURCE_CATALOG, expected=SOURCE_CATALOG_SHA)
    require(catalog["schema"] == "peano-hydra-evaluation-recovery-source-bundle-v1"
            and catalog["git_commit"] == SOURCE_COMMIT and catalog["saved_model_retrained"] is False,
            "The preserved proof/model-admission source changed.")
    files = catalog["files"]
    require(type(files) is dict and 1 <= len(files) <= 2048
            and sum(item["bytes"] for item in files.values()) <= 128 * 1024 * 1024,
            "Preserved source inventory escaped its bound.")
    for relative, expected in files.items():
        path = _safe_path(SOURCE, relative)
        actual = _fingerprint(path, expected["bytes"])
        require(actual == {key: expected[key] for key in ("bytes", "sha256")},
                "A preserved source file changed: " + relative)
        require(expected["mode"] == ("100755" if path.stat().st_mode & 0o111 else "100644"),
                "A preserved source mode changed.")
    require(_fingerprint(SOURCE_CATALOG, pin["bytes"]) == pin, "The source catalogue changed.")
    return pin


def _load_authenticated():
    """Use the genuine completed custody; this never creates a new admission."""
    source_pin = _source_snapshot()
    record, inputs_pin = _small(INPUTS, expected=INPUTS_SHA)
    require(record["schema"] == "peano-hydra-retention-evaluation-recovery-inputs-v1"
            and record["candidate_reference"]["manifest_sha256"] == MODEL_MANIFEST_SHA,
            "The saved mixed-model reference changed.")
    sys.path[:0] = [str(SOURCE), str(SOURCE / "peano-lab/py")]
    for name, module in tuple(sys.modules.items()):
        if name == "training" or name.startswith("training.") or name == "peano_lab" or name.startswith("peano_lab."):
            location = getattr(module, "__file__", None)
            require(location is None or Path(location).resolve().is_relative_to(SOURCE),
                    "Another checkout's proof or training modules are already loaded.")
    from training.peano_hydra.retention_saved_artifact import reference
    candidate = reference(record["candidate_reference"], record["locations"]["local"])
    require(candidate.manifest_path == MODEL_ROOT / "manifest.json", "Wrong saved model location.")
    handle = candidate.load()
    require(handle.manifest["model"] == {"model_id": MODEL_ID, "revision": REVISION}
            and handle.manifest["model_trained"] is True
            and handle.manifest["reservation"]["job_id"] == "21456251",
            "The artifact is not the actual completed mixed training run.")
    return candidate, handle, source_pin, inputs_pin


def _artifact_snapshot(handle):
    from training.peano_policy.manifest import verify_artifact_directory
    require(_fingerprint(MODEL_ROOT / "manifest.json", 191597)
            == {"bytes": 191597, "sha256": MODEL_MANIFEST_SHA}, "Saved training manifest changed.")
    for name in ("adapter", "tokenizer"):
        actual = verify_artifact_directory(MODEL_ROOT, handle.manifest[name], name)
        require(actual == MODEL_ROOT / name, "Saved artifact directory changed.")
    return {name: handle.manifest[name] for name in ("adapter", "tokenizer")}


def _quantized_snapshot():
    ready, ready_pin = _readiness()
    record, pin = _small(QUANTIZED / "manifest.json")
    require(pin == {key: ready["model_manifest"][key] for key in ("bytes", "sha256")},
            "The prepared quantized model is not the one whose setup completed.")
    _validate_quantized_record(record)
    require(QUANTIZED.is_dir() and not QUANTIZED.is_symlink(), "Compact model root is not a regular directory.")
    expected_names = {"manifest.json", *record["files"]}
    require({path.name for path in QUANTIZED.iterdir()} == expected_names,
            "Compact-model directory contains unlisted or missing files.")
    for relative, expected in record["files"].items():
        require(_fingerprint(_safe_path(QUANTIZED, relative), expected["bytes"])
                == {key: expected[key] for key in ("bytes", "sha256")},
                "Compact-model bytes changed: " + relative)
    _quantized_config(record)
    require(_fingerprint(QUANTIZED / "manifest.json", pin["bytes"]) == pin,
            "The compact-model manifest changed during hashing.")
    return record, pin, ready_pin


def peft_mapping(shapes):
    """Validate every real PEFT matrix; return its exact transposed MLX name."""
    expected = {}
    result = {}
    for layer in range(28):
        for projection, (input_size, output_size) in LORA_DIMS.items():
            source = f"base_model.model.model.layers.{layer}.{projection}"
            target = f"model.layers.{layer}.{projection}"
            expected[source + ".lora_A.weight"] = (16, input_size)
            expected[source + ".lora_B.weight"] = (output_size, 16)
            result[source + ".lora_A.weight"] = target + ".lora_a"
            result[source + ".lora_B.weight"] = target + ".lora_b"
    require(type(shapes) is dict and set(shapes) == set(expected),
            "The saved adapter does not contain exactly the 392 trained LoRA matrices.")
    require(all(tuple(shapes[name]) == shape for name, shape in expected.items()),
            "The saved adapter matrix shapes do not match Qwen3-1.7B rank16.")
    return result


def _load_model(handle, quantized):
    for package, version in DEPENDENCIES.items():
        require(importlib.metadata.version(package) == version, "Unexpected compact-runtime dependency: " + package)
    for key, value in {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1", "HF_HUB_DISABLE_TELEMETRY": "1",
                       "TOKENIZERS_PARALLELISM": "false", "USE_TORCH": "0", "USE_TF": "0", "USE_FLAX": "0"}.items():
        os.environ[key] = value
    import mlx.core as mx
    from mlx.utils import tree_flatten
    from mlx_lm.utils import load_model
    from mlx_lm.tuner.utils import linear_to_lora_layers
    from transformers import AutoTokenizer

    require(mx.metal.is_available(), "This local preview requires an available Apple Metal device.")
    mx.set_default_device(mx.gpu)
    mx.set_memory_limit(6 * 1024**3)
    mx.set_cache_limit(256 * 1024**2)
    expected_config = _quantized_config(quantized)
    model, config = load_model(QUANTIZED, lazy=True, strict=True)
    require(config == expected_config, "The MLX loader changed the declared Base configuration.")
    require(config["model_type"] == "qwen3" and config["num_hidden_layers"] == 28
            and config["hidden_size"] == 2048 and config["intermediate_size"] == 6144
            and config["vocab_size"] == 151936 and config["tie_word_embeddings"] is True
            and config["quantization"] == QUANTIZATION,
            "Compact model configuration differs from the trained Base architecture.")
    tokenizer = AutoTokenizer.from_pretrained(str(handle.tokenizer_directory),
        trust_remote_code=False, use_fast=True, local_files_only=True)
    adapter_config, _ = _small(handle.adapter_directory / "adapter_config.json")
    require(adapter_config["peft_type"] == "LORA" and adapter_config["r"] == 16
            and adapter_config["lora_alpha"] == 32 and adapter_config["lora_dropout"] == 0.05
            and adapter_config["bias"] == "none" and adapter_config["fan_in_fan_out"] is False
            and adapter_config["use_dora"] is False and adapter_config["use_rslora"] is False
            and adapter_config.get("modules_to_save") is None
            and set(adapter_config["target_modules"]) == {key.split(".")[-1] for key in LORA_KEYS},
            "Saved PEFT options cannot be represented by this exact MLX LoRA mapping.")
    adapter_path = handle.adapter_directory / "adapter_model.safetensors"
    require(_fingerprint(adapter_path, 69_782_384) == {"bytes": 69_782_384, "sha256": ADAPTER_SHA},
            "The trained LoRA bytes changed before loading.")
    weights = mx.load(str(adapter_path))
    names = peft_mapping({name: tuple(value.shape) for name, value in weights.items()})
    require(all(value.dtype == mx.float32 for value in weights.values()), "The original LoRA matrices must remain float32.")
    require(bool(mx.stack([mx.all(mx.isfinite(value)) for value in weights.values()]).all().item()),
            "The saved LoRA contains non-finite values.")
    linear_to_lora_layers(model, 28, {"rank": 16, "scale": 2.0, "dropout": 0.05,
                                    "keys": list(LORA_KEYS)}, use_dora=False)
    mapped = {names[name]: value.T for name, value in weights.items()}
    parameters = dict(tree_flatten(model.parameters()))
    lora_names = {name for name in parameters if name.endswith((".lora_a", ".lora_b"))}
    require(set(mapped) == lora_names and all(tuple(value.shape) == tuple(parameters[name].shape)
                                            for name, value in mapped.items()),
            "MLX did not expose the exact matching LoRA layers.")
    # Strict full-model loading above; exact closed LoRA key/shape join here.
    model.load_weights(list(mapped.items()), strict=False)
    model.eval()
    require(all(not layer.training for _, layer in model.named_modules()), "Inference unexpectedly enabled dropout/training.")
    mx.eval(model.parameters())
    require(_fingerprint(adapter_path, 69_782_384)["sha256"] == ADAPTER_SHA,
            "The original adapter changed while loading.")
    return model, tokenizer, mx


class _Prefix:
    """The unchanged authority callback's one-dimensional token protocol."""
    def __init__(self, values):
        self.values = values

    def tolist(self):
        return list(self.values)


def _rank_extensions(log_probs, active, allowed, width, np):
    """Rank actual allowed logits; stable token-id order resolves score ties."""
    choices = []
    for parent, ((tokens, cumulative), permitted) in enumerate(zip(active, allowed)):
        ids = np.asarray(sorted(set(permitted)), dtype=np.int64)
        require(ids.size > 0 and int(ids[0]) >= 0 and int(ids[-1]) < log_probs.shape[1],
                "Authority token IDs escaped the model vocabulary.")
        scores = log_probs[parent, ids]
        require(bool(np.isfinite(scores).all()), "Model produced non-finite candidate scores.")
        # Only at most 2*width extensions per parent can enter the global top 2*width.
        order = np.argsort(-scores, kind="stable")[:2 * width]
        choices.extend((float(scores[index]) + cumulative, parent, int(ids[index])) for index in order)
    choices.sort(key=lambda item: (-item[0], active[item[1]][0] + (item[2],)))
    return choices[:2 * width]


def _advance_beams(active, choices, completed, width, eos):
    live, parents = [], []
    finished = list(completed)
    for rank, (score, parent, token) in enumerate(choices):
        tokens = active[parent][0] + (token,)
        if token == eos:
            if rank < width:
                finished.append((tokens, score / len(tokens)))
        elif len(live) < width:
            live.append((tokens, score))
            parents.append(parent)
    finished.sort(key=lambda item: (-item[1], item[0]))
    return live, parents, finished[:width]


def _reorder_cache(cache, parents, mx, cache_type):
    """Reindex the public KVCache.state; all live beams have the same length."""
    indices = mx.array(parents, dtype=mx.int32)
    for item in cache:
        require(type(item) is cache_type and type(item.offset) is int and item.offset > 0,
                "This decoder supports only Qwen3's ordinary KVCache.")
        offset = item.offset
        keys, values = item.state
        require(keys.shape[2] == offset and values.shape[2] == offset,
                "The decoder cache does not cover its exact token prefix.")
        item.state = (keys[indices], values[indices])
        require(item.offset == offset and item.state[0].shape[0] == len(parents),
                "The decoder cache failed to retain its beam prefix.")
    mx.eval([item.state for item in cache])


class _MLXCandidatePolicy:
    """Actual model-driven preview, without pretending to be HF model.generate."""
    def __init__(self, model, tokenizer, mx, environment, identity, emit_progress):
        from training.peano_policy.contract import environment_record
        self.model, self.tokenizer, self.mx = model, tokenizer, mx
        self.environment = environment
        self.policy_environment = environment_record(environment)
        self.evaluation_identity = {
            "name": "hydra-playground-mixed-mlx-v1", "kind": "local-quantized-model-candidate-provider-v1",
            "model": identity, "decoder": DECODER,
            "authority": "original-v4-token-mask-and-native-whole-line-postflight",
            "max_new_tokens": MAX_NEW_TOKENS, "max_prompt_tokens": MAX_PROMPT_TOKENS,
            "candidates_per_state": 4, "decoder_beam_width": 4,
            "beam_score": "sum-full-vocabulary-log-probabilities; completed-length-normalization-1",
            "sampling": False, "fallback": False, "repair": False,
            "model_call_unit": "one bounded candidate-batch decoding; forward passes counted separately",
            "numerical_equivalence_to_training": False,
        }
        self.emit_progress = emit_progress
        self.calls = 0
        self.forward_passes = 0
        self.generated_token_steps = 0
        self.rejections = []
        self.proposals = []
        self.initial_goals = None
        self.last_goals = None

    def _decode(self, prompt, width):
        import numpy as np
        from mlx_lm.models.cache import KVCache
        from training.peano_policy.authority import AuthorityTokenConstraint
        mx = self.mx
        prompt_ids = self.tokenizer.encode(prompt, add_special_tokens=False)
        require(type(prompt_ids) is list and 0 < len(prompt_ids) <= MAX_PROMPT_TOKENS,
                "This interactive proof state exceeds the 1,536-token prompt bound; it was not truncated.")
        constraint = AuthorityTokenConstraint(self.tokenizer, self.environment,
                                              prompt_length=len(prompt_ids), max_new_tokens=MAX_NEW_TOKENS)
        eos = self.tokenizer.eos_token_id
        cache = [KVCache() for _ in self.model.layers]
        active = [((), 0.0)]
        completed = []
        next_ids = [prompt_ids]
        for step in range(MAX_NEW_TOKENS):
            logits = self.model(mx.array(next_ids, dtype=mx.int32), cache=cache)[:, -1, :].astype(mx.float32)
            log_probs = logits - mx.logsumexp(logits, axis=-1, keepdims=True)
            mx.eval(log_probs, [item.state for item in cache])
            self.forward_passes += 1
            self.generated_token_steps += 1
            scores = np.asarray(log_probs)
            require(scores.ndim == 2 and scores.shape == (len(active), 151936)
                    and bool(np.isfinite(scores).all()), "Model returned malformed or non-finite logits.")
            allowed = [constraint(index, _Prefix(prompt_ids + list(tokens)))
                       for index, (tokens, _) in enumerate(active)]
            choices = _rank_extensions(scores, active, allowed, width, np)
            live, parents, completed = _advance_beams(active, choices, completed, width, eos)
            if len(completed) >= width or not live:
                active = []
                break
            active = live
            if step + 1 == MAX_NEW_TOKENS:
                break
            _reorder_cache(cache, parents, mx, KVCache)
            next_ids = [[tokens[-1]] for tokens, _ in active]
            if (step + 1) % 8 == 0:
                self.emit_progress({"phase": "decoding", "message": "Ranking primitive tactic continuations.",
                                    "model_calls": self.calls, "decoded_tokens": step + 1})
        # A length-limited prefix is merely a proposed line, subject to the same native postflight.
        completed.extend((tokens, score / len(tokens)) for tokens, score in active if tokens)
        completed.sort(key=lambda item: (-item[1], item[0]))
        chosen = completed[:width]
        del cache
        mx.clear_cache()
        return tuple(self.tokenizer.decode(list(tokens), skip_special_tokens=True,
                                           clean_up_tokenization_spaces=False) for tokens, _ in chosen)

    def propose(self, goals_before, *, max_candidates):
        from training.peano_policy.prompt import render_prompt
        from training.peano_policy.authority import validate_authority_tactic
        require(type(goals_before) is tuple and goals_before and all(type(item) is str for item in goals_before),
                "The kernel supplied a malformed proof state.")
        require(max_candidates == 4, "The local preview keeps four candidate slots.")
        self.calls += 1
        if self.initial_goals is None:
            self.initial_goals = goals_before
        self.last_goals = goals_before
        self.emit_progress({"phase": "proposing", "message": "Asking the trained adapter for the next primitive tactics.",
                            "model_calls": self.calls, "goals": [goal[:512] for goal in goals_before[:3]]})
        prompt = render_prompt(goals=goals_before, focus=0, environment=self.environment)
        raw = self._decode(prompt, 4)
        accepted = []
        for index, line in enumerate(raw):
            try:
                candidate = validate_authority_tactic(line, self.environment)
                require(len(candidate.encode("utf-8")) <= 512, "Generated tactic exceeds the interactive line bound.")
                accepted.append(candidate)
            except ValueError as error:
                self.rejections.append({"call": self.calls, "candidate": index,
                                        "error": " ".join(str(error).split())[:256]})
        self.proposals.append({"call": self.calls, "goals": list(goals_before),
                               "raw": list(raw), "candidates": list(accepted)})
        self.emit_progress({"phase": "checking", "message": "The original kernel is checking the proposed branches.",
                            "model_calls": self.calls, "candidates": [line[:512] for line in accepted]})
        return tuple(accepted)


def run_search(request, emit_progress):
    """Called only by worker.py under its fresh process/resource/offline guard."""
    require(RUNTIME_IMPLEMENTED, "The local model loader is still being prepared; manual checking remains available.")
    require(type(request) is dict and set(request) == {"theorem", "max_model_calls", "beam_width"}
            and type(request["theorem"]) is str and 0 < len(request["theorem"].encode("utf-8")) <= 4096
            and type(request["max_model_calls"]) is int and request["max_model_calls"] in (8, 16)
            and type(request["beam_width"]) is int and request["beam_width"] in (1, 4),
            "Unsupported bounded model request.")
    require(callable(emit_progress) and sys.flags.isolated and sys.dont_write_bytecode,
            "Model inference must run in the isolated, bounded playground worker.")
    actual_sink = emit_progress
    emit_progress = lambda event: _progress(actual_sink, event)
    started = time.monotonic()
    emit_progress({"phase": "authenticating", "message": "Checking the saved adapter, tokenizer, source and admission receipts.",
                   "model_calls": 0})
    candidate, handle, source_pin, inputs_pin = _load_authenticated()
    artifacts = _artifact_snapshot(handle)
    quantized, quantized_pin, ready_pin = _quantized_snapshot()
    runtime_pin = _fingerprint(Path(__file__), 256 * 1024)
    from training.peano_policy.prompt import CapabilityIdentity
    from training.peano_policy.contract import authority_prompt_environment
    from training.peano_policy.authority import authority_profile_record, authority_contract_record
    from training.peano_hydra.protocol import validate_statement
    from peano_lab.ui.prove import SurfaceCapabilities
    from training.peano_policy.search import SearchLimits
    from training.peano_hydra.policy import PolicyHead, HydraCandidatePolicy
    from training.peano_hydra.runner import run_hydra
    theorem = validate_statement(request["theorem"])
    require(theorem == request["theorem"], "The worker must supply the original canonical theorem.")
    contract = handle.manifest["common_contract"]
    capability_record = contract["authority"]["capabilities"]
    environment = authority_prompt_environment(False, CapabilityIdentity.from_record({
        "label": capability_record["label"],
        "allowed_commands": capability_record["allowed_commands"],
        "allowed_theorems": capability_record["allowed_theorems"],
    }))
    require(authority_profile_record(environment) == contract["decoder_profile"]
            and authority_contract_record() == contract["prompt_contract"],
            "Saved primitive authority or prompt contracts no longer match the preserved implementation.")
    capabilities = SurfaceCapabilities(label=capability_record["label"],
        allowed_commands=frozenset(capability_record["allowed_commands"]),
        allowed_theorems=frozenset(capability_record["allowed_theorems"]))
    identity = {"name": NAME, "device": "Apple Metal", "backend": "MLX", "model_id": MODEL_ID,
                "revision": REVISION, "adapter_manifest_sha256": MODEL_MANIFEST_SHA,
                "adapter_sha256": ADAPTER_SHA, "training_job_id": "21456251",
                "admission_receipt_sha256": candidate.admission_receipt_sha256,
                "quantization": QUANTIZATION, "quantized_manifest_sha256": quantized_pin["sha256"],
                "runtime_sha256": runtime_pin["sha256"], "kernel_source_commit": SOURCE_COMMIT,
                "decoder": DECODER, "numerical_equivalence_to_training": False,
                "purpose": "interactive exploration, not the archived GH200 comparison"}
    emit_progress({"phase": "loading", "message": "Loading the local 4-bit Base and the unchanged trained LoRA matrices.",
                   "model_calls": 0})
    model, tokenizer, mx = _load_model(handle, quantized)
    policy = _MLXCandidatePolicy(model, tokenizer, mx, environment, identity, emit_progress)
    portfolio = HydraCandidatePolicy((PolicyHead("mixed-local-preview", "control", 4, policy),),
                                     name="hydra-playground-local-preview-v1")
    limits = SearchLimits(max_depth=16, beam_width=request["beam_width"], candidates_per_state=4,
                          max_model_calls=request["max_model_calls"], max_states=64)
    checked = run_hydra(theorem, portfolio, capabilities=capabilities, classical=False, limits=limits,
                        label="hydra-playground-local-preview", search_profile="context-alpha-v1")
    require(not checked.degraded and checked.search.model_calls == policy.calls,
            "The local model provider did not complete its declared search: " + "; ".join(checked.degradation_reasons))
    emit_progress({"phase": "verifying", "message": "Final proof replay and unchanged-input checks.", "model_calls": policy.calls})
    require(_artifact_snapshot(handle) == artifacts and _source_snapshot() == source_pin
            and _fingerprint(INPUTS, inputs_pin["bytes"]) == inputs_pin
            and _fingerprint(Path(__file__), runtime_pin["bytes"]) == runtime_pin,
            "Saved model, source or caller bytes changed during search.")
    after_quantized, after_quantized_pin, after_ready_pin = _quantized_snapshot()
    require(after_quantized == quantized and after_quantized_pin == quantized_pin and after_ready_pin == ready_pin,
            "The local quantized Base changed during search.")
    replay = checked.replay
    require((checked.status == "proof") == (replay is not None), "Search/replay proof status disagrees.")
    if replay is not None:
        require(replay.kernel_checked is True and replay.status == "proved" and replay.theorem == theorem
                and replay.goals == () and replay.proof_nodes == checked.search.certificate_nodes,
                "The original independent kernel replay did not verify this theorem.")
    search = checked.search.to_dict()
    search.update(forward_passes=policy.forward_passes, generated_token_steps=policy.generated_token_steps,
                  model_call_unit="bounded candidate-batch decoding", proposals=policy.proposals,
                  authority_rejections=policy.rejections, limits={"max_model_calls": request["max_model_calls"],
                      "beam_width": request["beam_width"], "max_depth": 16, "max_states": 64,
                      "candidates_per_state": 4, "max_new_tokens": MAX_NEW_TOKENS,
                      "max_prompt_tokens": MAX_PROMPT_TOKENS},
                  elapsed_seconds=round(time.monotonic() - started, 3))
    return {"kind": "model", "status": "proved" if replay is not None else checked.status,
            "theorem": theorem, "goals": list(replay.goals) if replay is not None else list(policy.initial_goals or ()),
            "goals_scope": "final-independent-replay" if replay is not None else "original-unproved-goal",
            "kernel_checked": replay is not None and replay.kernel_checked,
            "proof_nodes": None if replay is None else replay.proof_nodes,
            "trace": [] if replay is None else replay.to_dict(include_trace=True)["trace"],
            "commands": list(checked.commands), "search": search, "model": identity,
            "benchmark_claim": False, "model_used": True,
            "message": "The original kernel checked this proof." if replay is not None
                       else "Not proved within this search budget; this does not establish that the theorem is false."}
