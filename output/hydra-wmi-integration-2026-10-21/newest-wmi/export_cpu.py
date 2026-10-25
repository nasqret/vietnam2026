"""Export one authenticated vanilla LoRA checkpoint; no model or GPU execution."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import signal
import time

PINS = {
    "best.pt": "177501bf7b662a210b6cf6887844a282365437c781e53138ad5495f02c620a06",
    "receipt.json": "80a8074c0151302496d411d5193df1e038189511c9ab277e7509484eddca58be",
    "selection.json": "65af30a89ea720163cabedd8b00e39371d3fc7acf5e977ad781f3f777b9cd6a9",
}
RUN_ID = "wmi-pro6000-c6-long-vanilla-qwen_vanilla-s11"
DIMS = {"self_attn.q_proj": (2048, 2048), "self_attn.k_proj": (2048, 1024),
        "self_attn.v_proj": (2048, 1024), "self_attn.o_proj": (2048, 2048),
        "mlp.gate_proj": (2048, 6144), "mlp.up_proj": (2048, 6144),
        "mlp.down_proj": (6144, 2048)}


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def fingerprint(path):
    require(path.is_file() and not path.is_symlink(), "Missing or linked input: " + str(path))
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(4 * 1024**2), b""):
            h.update(chunk)
    return {"bytes": path.stat().st_size, "sha256": h.hexdigest()}


def object_sha(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                    allow_nan=False).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    signal.alarm(180)
    start = time.monotonic()
    started = datetime.now(timezone.utc).isoformat()
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "GPU visibility must be empty")
    require(args.run.name == RUN_ID, "Wrong run")
    pins = {name: fingerprint(args.run / name) for name in PINS}
    require(all(pins[name]["sha256"] == pin for name, pin in PINS.items()), "Input hash mismatch")
    receipt = json.loads((args.run / "receipt.json").read_text())
    selection = json.loads((args.run / "selection.json").read_text())
    identity, cfg = receipt["identity"], receipt["config"]
    require(object_sha(cfg) == identity["config_sha256"], "Config identity mismatch")
    require(object_sha(identity) == selection["identity_sha256"], "Selection identity mismatch")
    require(identity["arm"] == "qwen_vanilla" and identity["seed"] == 11, "Not selected vanilla seed11")
    require(cfg["lora_rank"] == 32 and cfg["lora_alpha"] == 64 and cfg["lora_dropout"] == 0,
            "Unexpected LoRA configuration")
    require(selection["state"] == "locked" and selection["checkpoint"] == "best.pt"
            and selection["checkpoint_step"] == 16384 and selection["checkpoint_sha256"] == PINS["best.pt"]
            and selection["halting_policy"] == {"kind": "fixed", "depth": 1}, "Selection mismatch")
    source_pins = {name: fingerprint(args.source / name) for name in identity["sources_sha256"]}
    require(len(source_pins) == 20 and all(source_pins[name]["sha256"] == pin
            for name, pin in identity["sources_sha256"].items()), "Frozen source mismatch")
    import torch
    from safetensors.torch import load_file, save_file
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    require(not torch.cuda.is_initialized(), "CUDA unexpectedly initialized")
    saved = torch.load(args.run / "best.pt", map_location="cpu", weights_only=True)
    require(saved["identity"] == identity and saved["step"] == 16384
            and saved["policy"] == {"kind": "fixed", "depth": 1}, "Checkpoint identity/step/policy mismatch")
    require(saved["val_loss"] == selection["best_validation_loss"], "Selected loss mismatch")
    weights = saved["trainable"]
    expected = {}
    for layer in range(28):
        for projection, (input_size, output_size) in DIMS.items():
            name = f"base_model.base_model.model.model.layers.{layer}.{projection}"
            expected[name + ".lora_A.default.weight"] = (32, input_size)
            expected[name + ".lora_B.default.weight"] = (output_size, 32)
    require(type(weights) is dict and set(weights) == set(expected), "Expected exactly 392 vanilla matrices")
    for name, tensor in weights.items():
        require(type(tensor) is torch.Tensor and tensor.device.type == "cpu"
                and tensor.dtype == torch.float32 and tuple(tensor.shape) == expected[name]
                and bool(torch.isfinite(tensor).all()), "Invalid tensor: " + name)
    args.output.mkdir(parents=True, exist_ok=False)
    export = args.output / "selected-lora.safetensors"
    save_file({name: tensor.contiguous() for name, tensor in weights.items()}, str(export))
    reloaded = load_file(str(export), device="cpu")
    require(set(reloaded) == set(weights) and all(torch.equal(reloaded[n], weights[n]) for n in weights),
            "Safetensors roundtrip differs")
    require(not torch.cuda.is_initialized(), "CUDA unexpectedly initialized")
    require(all(fingerprint(args.run / name) == pin for name, pin in pins.items()), "Inputs changed during export")
    result = {"schema": "hydra-lora-cpu-export-v1", "status": "completed", "training": False,
        "inference": False, "model_loaded": False, "gpu_used": False, "cuda_initialized": False,
        "automatic_retry": False, "run_id": RUN_ID, "selected_step": 16384,
        "checkpoint_sha256": PINS["best.pt"], "training_receipt_sha256": PINS["receipt.json"],
        "selection_sha256": PINS["selection.json"], "identity_sha256": object_sha(identity),
        "policy": saved["policy"], "input_files": pins, "source_files": source_pins,
        "export": fingerprint(export), "exported_lora_sha256": fingerprint(export)["sha256"],
        "tensor_count": len(weights), "tensor_dtype": "float32", "tensor_values_bitwise_equal": True,
        "torch_version": torch.__version__, "started_utc": started,
        "completed_utc": datetime.now(timezone.utc).isoformat(), "wall_seconds": time.monotonic() - start,
        "exporter": fingerprint(Path(__file__))}
    with (args.output / "export-receipt.json").open("x") as stream:
        json.dump(result, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
    print(json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
