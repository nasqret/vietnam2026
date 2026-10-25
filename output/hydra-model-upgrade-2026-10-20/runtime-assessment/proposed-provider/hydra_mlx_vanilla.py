"""Optional local rank32 vanilla preview; not wired into the running playground.

Reuses the current runtime's authenticated quantized Base and source helpers.
Importing this module performs no framework import, model load or inference.
Only original safetensors exports are read; no PyTorch pickle or network path.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib.metadata
import inspect
import json
import os
from pathlib import Path
import platform
import struct
import sys
import time

from hydra_torch_candidate import CandidatePolicy, Limits, require, object_sha, sha256


LORA_DIMS = {"self_attn.q_proj": (2048, 2048), "self_attn.k_proj": (2048, 1024),
             "self_attn.v_proj": (2048, 1024), "self_attn.o_proj": (2048, 2048),
             "mlp.gate_proj": (2048, 6144), "mlp.up_proj": (2048, 6144),
             "mlp.down_proj": (6144, 2048)}
MAX_EXPORT_BYTES = 160 * 1024 * 1024


@dataclass(frozen=True)
class LocalCandidateSpec:
    # Pin this configuration in the eventual host release; no default candidate.
    export_path: Path
    export_bytes: int
    export_sha256: str
    checkpoint_sha256: str
    training_receipt_path: Path
    training_receipt_sha256: str
    arm_receipt_path: Path
    arm_receipt_sha256: str
    selected_step: int
    run_id: str

    def __post_init__(self):
        for name in ("export_sha256", "checkpoint_sha256", "training_receipt_sha256", "arm_receipt_sha256"):
            require(sha256(getattr(self, name)), f"missing actual {name}")
        require(type(self.export_bytes) is int and 0 < self.export_bytes <= MAX_EXPORT_BYTES,
                "invalid export byte bound")
        require(type(self.selected_step) is int and self.selected_step > 0,
                "missing selected checkpoint step")
        require(type(self.run_id) is str and self.run_id, "missing actual candidate run ID")


def rank32_mapping(shapes):
    """Exact wrapper-trained F32 A/B names to MLX names; all values transpose."""
    expected, mapped = {}, {}
    for layer in range(28):
        for projection, (input_size, output_size) in LORA_DIMS.items():
            source = f"base_model.base_model.model.model.layers.{layer}.{projection}"
            target = f"model.layers.{layer}.{projection}"
            expected[source + ".lora_A.default.weight"] = (32, input_size)
            expected[source + ".lora_B.default.weight"] = (output_size, 32)
            mapped[source + ".lora_A.default.weight"] = target + ".lora_a"
            mapped[source + ".lora_B.default.weight"] = target + ".lora_b"
    require(type(shapes) is dict and set(shapes) == set(expected),
            "vanilla export must contain exactly 392 wrapper-named LoRA matrices and no recurrence tensors")
    require(all(tuple(shapes[key]) == shape for key, shape in expected.items()),
            "export is not exact Qwen3-1.7B rank32")
    return mapped


def inspect_export_header(path, expected_bytes):
    """Metadata-only validation, suitable before any MLX import or allocation."""
    path = Path(path)
    require(not path.is_symlink() and path.is_file() and path.stat().st_size == expected_bytes,
            "missing, linked or incorrectly sized safetensors export")
    with path.open("rb") as stream:
        prefix = stream.read(8)
        require(len(prefix) == 8, "short safetensors prefix")
        length = struct.unpack("<Q", prefix)[0]
        require(0 < length <= 2 * 1024 * 1024 and 8 + length < expected_bytes,
                "invalid bounded safetensors header")
        def pairs(items):
            result = {}
            for key, value in items:
                require(key not in result, "duplicate safetensors header key")
                result[key] = value
            return result
        header = json.loads(stream.read(length), object_pairs_hook=pairs)
    require(type(header) is dict, "safetensors header must be an object")
    if "__metadata__" in header:
        metadata = header.pop("__metadata__")
        require(type(metadata) is dict and all(type(k) is str and type(v) is str for k, v in metadata.items()),
                "invalid safetensors metadata")
    require(all(type(v) is dict and set(v) == {"dtype", "shape", "data_offsets"}
                for v in header.values()), "invalid tensor metadata")
    mapping = rank32_mapping({key: value["shape"] for key, value in header.items()})
    intervals = []
    for value in header.values():
        require(value["dtype"] == "F32", "vanilla LoRA matrices must retain float32")
        shape, offsets = value["shape"], value["data_offsets"]
        require(type(shape) is list and all(type(n) is int and n > 0 for n in shape)
                and type(offsets) is list and len(offsets) == 2
                and all(type(n) is int and n >= 0 for n in offsets)
                and offsets[1] - offsets[0] == 4 * shape[0] * shape[1], "invalid tensor byte span")
        intervals.append(tuple(offsets))
    intervals.sort()
    require(intervals[0][0] == 0 and all(a[1] == b[0] for a, b in zip(intervals, intervals[1:]))
            and intervals[-1][1] == expected_bytes - 8 - length,
            "overlapping, missing or trailing safetensors bytes")
    return mapping


def _authenticated_inputs(trained, spec, frozen_data, frozen_eval):
    """Reuse existing source/Base custody; bind new export to genuine receipts."""
    candidate, handle, source_pin, inputs_pin = trained._load_authenticated()
    quantized, quantized_pin, ready_pin = trained._quantized_snapshot()
    training, training_pin = trained._small(Path(spec.training_receipt_path),
                                          expected=spec.training_receipt_sha256)
    arm, arm_pin = trained._small(Path(spec.arm_receipt_path), expected=spec.arm_receipt_sha256)
    require(arm.get("status") == "completed" and arm.get("training") is False
            and arm.get("checkpoint_sha256") == spec.checkpoint_sha256
            and arm.get("exported_lora_sha256") == spec.export_sha256,
            "export is not bound to an actual completed inference-only comparison arm")
    identity, cfg = training["identity"], training["config"]
    require(identity["arm"] == "qwen_vanilla" and cfg["base_model"] == trained.MODEL_ID
            and cfg["base_revision"] == trained.REVISION
            and identity["base"]["model.safetensors"] == trained.ORIGINAL_WEIGHT_SHA,
            "candidate is not vanilla on the exact original Base")
    require(cfg["lora_rank"] == 32 and cfg["lora_alpha"] == 64 and cfg["lora_dropout"] == 0
            and set(cfg["lora_targets"]) == {key.split(".")[-1] for key in LORA_DIMS}
            and cfg["steps"] >= spec.selected_step, "candidate's LoRA or selected-step contract differs")
    for name, expected in identity["base"].items():
        if name == "model.safetensors":
            continue
        relative = "original-config.json" if name == "config.json" else name
        require(quantized["files"][relative]["sha256"] == expected,
                "existing Base/tokenizer differs from candidate training: " + name)
    # Exact candidate-source helpers, not the mutable latent checkout.
    helper_pins = {}
    for module, relative in ((frozen_data, "src/latentproof/qwen_data.py"),
                             (frozen_eval, "src/latentproof/qwen_eval.py")):
        path = Path(inspect.getfile(module))
        helper_pins[relative] = trained._fingerprint(path, 256 * 1024)
        require(helper_pins[relative]["sha256"] == identity["sources_sha256"][relative],
                "compact prompt or strict decoder differs from candidate frozen source")
    export_pin = trained._fingerprint(Path(spec.export_path), MAX_EXPORT_BYTES)
    require(export_pin == {"bytes": spec.export_bytes, "sha256": spec.export_sha256},
            "candidate safetensors export changed")
    mapping = inspect_export_header(spec.export_path, spec.export_bytes)
    return {"handle": handle, "source_pin": source_pin, "inputs_pin": inputs_pin,
            "quantized": quantized, "quantized_pin": quantized_pin, "ready_pin": ready_pin,
            "training": training, "training_pin": training_pin, "arm_pin": arm_pin,
            "export_pin": export_pin, "helper_pins": helper_pins, "mapping": mapping,
            "old_adapter_sha256": trained.ADAPTER_SHA}


class MLXVanillaBackend:
    kind = "latent_compact_v3"
    model_vocab_size = 151936

    def __init__(self, model, mx):
        self.model, self.mx = model, mx

    def next_token(self, sequence, allowed_ids, *, forward_started, forward_completed):
        require(allowed_ids is None, "latent decoder must preserve unmasked trained argmax")
        mx = self.mx
        tokens = mx.array([sequence], dtype=mx.int32)
        forward_started()
        # Exact Qwen3 decoder path, but project only the final hidden state.
        # No KV cache or duplicated inference; model.model includes final norm.
        hidden = self.model.model(tokens, cache=None)[:, -1:, :]
        logits = self.model.model.embed_tokens.as_linear(hidden)[:, -1, :].astype(mx.float32)
        mx.eval(logits)
        forward_completed()
        require(tuple(logits.shape) == (1, self.model_vocab_size)
                and bool(mx.all(mx.isfinite(logits)).item()), "malformed or non-finite MLX logits")
        token = int(mx.argmax(logits, axis=-1).item())
        return token, {"depth": 1, "block_calls": 28, "head_calls": 1, "gate_calls": 0, "readouts": 1}


def load_local_policy(*, trained, spec, frozen_data, frozen_eval, should_stop=lambda: False,
                      deadline_monotonic=None, limits=Limits()):
    """Explicit model-load entry point, called only in a fresh isolated worker.

    No caller invokes this during status inspection. Returned policy supports
    the unchanged Hydra CandidateProvider interface; finalization is explicit.
    """
    require(sys.platform == "darwin" and platform.machine() == "arm64"
            and sys.flags.isolated and sys.dont_write_bytecode,
            "use the existing isolated Apple Silicon worker")
    snapshot = _authenticated_inputs(trained, spec, frozen_data, frozen_eval)
    for package, version in trained.DEPENDENCIES.items():
        require(importlib.metadata.version(package) == version, "local runtime dependency drift: " + package)
    for key, value in {"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1",
                       "HF_HUB_DISABLE_TELEMETRY": "1", "TOKENIZERS_PARALLELISM": "false",
                       "USE_TORCH": "0", "USE_TF": "0", "USE_FLAX": "0"}.items():
        os.environ[key] = value
    import mlx.core as mx
    from mlx.utils import tree_flatten
    from mlx_lm.utils import load_model
    from mlx_lm.tuner.utils import linear_to_lora_layers
    from transformers import AutoTokenizer
    from training.peano_policy.prompt import CapabilityIdentity
    from training.peano_policy.contract import authority_prompt_environment
    from training.peano_policy.authority import validate_authority_tactic, authority_profile_record

    require(mx.metal.is_available(), "Apple Metal is unavailable; no CPU fallback")
    mx.set_default_device(mx.gpu)
    mx.set_memory_limit(6 * 1024**3)
    mx.set_cache_limit(256 * 1024**2)
    expected_config = trained._quantized_config(snapshot["quantized"])
    model, config = load_model(trained.QUANTIZED, lazy=True, strict=True)
    require(config == expected_config and config["model_type"] == "qwen3"
            and config["num_hidden_layers"] == 28 and config["hidden_size"] == 2048
            and config["intermediate_size"] == 6144 and config["vocab_size"] == 151936
            and config["tie_word_embeddings"] is True and config["quantization"] == trained.QUANTIZATION,
            "local Base architecture or quantization changed")
    # This directory already has the exact latent Base tokenizer. The historical
    # adapter's separate tokenizer is different and is deliberately not reused.
    tokenizer = AutoTokenizer.from_pretrained(str(trained.QUANTIZED),
        trust_remote_code=False, use_fast=True, local_files_only=True)
    tokenizer_identity = frozen_data.tokenizer_identity(tokenizer, trained.QUANTIZED)
    weights = mx.load(str(spec.export_path))
    mapping = rank32_mapping({name: tuple(value.shape) for name, value in weights.items()})
    require(mapping == snapshot["mapping"] and all(value.dtype == mx.float32 for value in weights.values()),
            "actual exported tensor set/dtype differs from authenticated header")
    require(bool(mx.stack([mx.all(mx.isfinite(value)) for value in weights.values()]).all().item()),
            "candidate export contains non-finite LoRA weights")
    linear_to_lora_layers(model, 28, {"rank": 32, "scale": 2.0, "dropout": 0.0,
                                    "keys": list(LORA_DIMS)}, use_dora=False)
    mapped = {mapping[name]: value.T for name, value in weights.items()}
    parameters = dict(tree_flatten(model.parameters()))
    actual_lora = {name for name in parameters if name.endswith((".lora_a", ".lora_b"))}
    require(set(mapped) == actual_lora and all(value.shape == parameters[name].shape
                                             for name, value in mapped.items()), "inexact MLX LoRA join")
    model.load_weights(list(mapped.items()), strict=False)
    model.eval()
    require(all(not module.training for _, module in model.named_modules()), "training/dropout enabled")
    mx.eval(model.parameters())
    actual = dict(tree_flatten(model.parameters()))
    require(bool(mx.stack([mx.all(actual[name] == value) for name, value in mapped.items()]).all().item()),
            "loaded LoRA values differ from exact exported transposes")
    require(trained._fingerprint(Path(spec.export_path), MAX_EXPORT_BYTES) == snapshot["export_pin"],
            "export changed while loading")
    contract = snapshot["handle"].manifest["common_contract"]
    cap = contract["authority"]["capabilities"]
    environment = authority_prompt_environment(False, CapabilityIdentity.from_record({
        "label": cap["label"], "allowed_commands": cap["allowed_commands"], "allowed_theorems": cap["allowed_theorems"]}))
    require(authority_profile_record(environment) == contract["decoder_profile"], "current execution authority changed")
    provenance = {"checkpoint_sha256": spec.checkpoint_sha256,
                  "tokenizer_identity_sha256": frozen_data.object_digest(tokenizer_identity),
                  "source_inventory_sha256": object_sha(snapshot["training"]["identity"]["sources_sha256"]),
                  "run_id": spec.run_id, "policy": {"kind": "fixed", "depth": 1}, "model_vocab_size": 151936}
    policy = CandidatePolicy(backend=MLXVanillaBackend(model, mx), tokenizer=tokenizer,
        kind="latent_compact_v3", environment=environment, provenance=provenance,
        render_prompt=frozen_data.compact_prompt, strict_generation=frozen_eval.strict_generation,
        check_prompt_binding=frozen_eval.check_prompt_binding, validate_tactic=validate_authority_tactic,
        limits=limits, should_stop=should_stop, deadline_monotonic=deadline_monotonic)
    policy.evaluation_identity.update(backend="MLX", device="Apple Metal", quantization=trained.QUANTIZATION,
        quantized_preview=True, numerical_equivalence_to_training=False,
        quantized_manifest_sha256=snapshot["quantized_pin"]["sha256"],
        exported_adapter_sha256=spec.export_sha256, selected_step=spec.selected_step,
        fallback_adapter_preserved_sha256=trained.ADAPTER_SHA)

    def finalize():
        require(trained._source_snapshot() == snapshot["source_pin"], "original native sources changed")
        require(trained._quantized_snapshot() == (snapshot["quantized"], snapshot["quantized_pin"], snapshot["ready_pin"]),
                "local Base or tokenizer changed")
        for path, pin, maximum in ((spec.export_path, snapshot["export_pin"], MAX_EXPORT_BYTES),
                                   (spec.training_receipt_path, snapshot["training_pin"], 4 * 1024 * 1024),
                                   (spec.arm_receipt_path, snapshot["arm_pin"], 4 * 1024 * 1024)):
            require(trained._fingerprint(Path(path), maximum) == pin, "candidate input changed during inference")
        return policy.report()

    # Kept separate from proof checking. The host calls this in its finally path.
    policy.finalize = finalize
    return policy
