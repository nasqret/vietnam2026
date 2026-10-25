"""One local real-data preparation/import check, never a recovery or model run."""
from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time

HERE = Path(__file__).resolve().parent
BUNDLE = HERE.parent / "p6-source-bundle-08"
RUNTIME = BUNDLE / "source"
ORIGINAL_APP = HERE.parent / "p6-source-bundle-06/source/hydra-playground"
APP = RUNTIME / "hydra-playground"
OUTPUT = HERE / "import-preparation-gate-01"
METADATA_SHA = "aa2745a98bf56c54dc23d2393b0104bdf9a6ae0e14c6962dd4136c6d1f285e16"
MANIFEST_SHA = "baa6c45db4fb01806a36aa188508e7cca9517a41934e5ad2f46739873722e1ff"
RUNTIME_PLAN_SHA = "77119db9f4a4ef1b6a3bcb78dea8c28d7f4008671099154f84f8a18a9e86bb1f"
FORBIDDEN = {"torch", "transformers", "peft", "mlx", "tokenizers", "jax", "tensorflow", "safetensors"}


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def pin(path):
    raw = Path(path).read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def audit(event, args):
    if event == "import":
        require(str(args[0]).split(".", 1)[0] not in FORBIDDEN, "Preparation gate forbids model/framework imports.")
    require(not event.startswith("socket.") and event not in {
        "subprocess.Popen", "os.system", "os.posix_spawn", "os.fork", "os.exec"},
        "Preparation gate forbids child processes and network calls.")


def forbid_proof_execution(frame, event, arg):
    if event != "call" or frame.f_code.co_name == "<module>":
        return
    name = frame.f_globals.get("__name__", "")
    function = frame.f_code.co_name
    checker = name == "peano_lab.kernel.checker" and function in {"check", "check_classical", "_entry", "_check", "_infer"}
    transition = name.startswith("peano_lab.engine") and function in {"apply_tactic", "checked_final"}
    surface = name == "peano_lab.ui.prove" and function == "checked_surface_final"
    require(not (checker or transition or surface),
            "This gate permits formula admission, not proof construction/checking: " + str(name)[:160])


def verify_scope(metadata, source_map):
    total = 0
    for name, expected in source_map.items():
        _, actual = metadata.read(RUNTIME / name, 4 * 1024**2, expected["sha256"])
        total += actual["bytes"]
        require(actual == expected and total <= 32 * 1024**2, "Runtime scope changed or exceeds its bound.")
    prefixes = ("hydra-playground/native-v7/peano_lab/", "hydra-playground/training-v5/hydra_training_v5/")
    wanted = {name for name in source_map if name.endswith(".py") and name.startswith(prefixes)}
    observed = {path.relative_to(RUNTIME).as_posix() for prefix in prefixes for path in (RUNTIME / prefix).rglob("*.py")}
    require(observed == wanted, "Unexpected native/training module inventory.")
    return {"files": len(source_map), "bytes": total, "map_sha256": hashlib.sha256(canonical(source_map)).hexdigest()}


def main():
    OUTPUT.mkdir(exist_ok=False)
    resource.setrlimit(resource.RLIMIT_CPU, (90, 95))
    if sys.platform != "darwin":
        resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    resource.setrlimit(resource.RLIMIT_FSIZE, (128 * 1024**2, 128 * 1024**2))
    def expired(*_):
        raise TimeoutError("Import/preparation gate exceeded its 120-second wall limit.")
    signal.signal(signal.SIGALRM, expired)
    signal.signal(signal.SIGXCPU, expired)
    signal.alarm(120)
    started = time.monotonic()
    result = {"schema": "hydra-recovery-import4-local-preparation-gate-v1", "passed": False,
        "error": None, "prepare_calls": 0, "actual_cpu_metadata_admission_performed": False,
        "original_artifact_admission_performed": False, "base_or_tensor_reload_performed": False,
        "model_calls": 0, "optimizer_updates": 0, "native_proof_calls": 0, "ssh_calls": 0,
        "allocation_calls": 0, "automatic_retry": False,
        "limits": {"cpu_seconds": 90, "wall_seconds": 120,
                   "address_space_bytes": None if sys.platform == "darwin" else 2 * 1024**3,
                   "darwin_rss_supervision": "separate_owned_parent_receipt"}}
    source_map = None
    metadata = None
    try:
        require(pin(HERE / "metadata_recovery.py")["sha256"] == METADATA_SHA, "Unreviewed import selector.")
        require(pin(BUNDLE / "manifest.json")["sha256"] == MANIFEST_SHA, "Wrong inference bundle.")
        require(not any(name.split(".", 1)[0] in FORBIDDEN | {"peano_lab", "hydra_training_v5", "experimental_model"}
                        for name in sys.modules), "A fresh process is required.")
        sys.dont_write_bytecode = True
        os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1")
        sys.addaudithook(audit)
        spec = importlib.util.spec_from_file_location("recovery_import4_fixture", HERE / "metadata_recovery.py")
        metadata = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(metadata)
        original_map = json.loads((HERE / "controller-source-pins.json").read_bytes())
        source_map = json.loads((HERE / "runtime-source-pins-base3.json").read_bytes())
        metadata.validate_source_maps(original_map, source_map)
        manifest = json.loads((BUNDLE / "manifest.json").read_bytes())
        require(manifest["inference_only"] is True and manifest["training_execution_allowed"] is False
                and all(manifest["files"].get(name) == value for name, value in source_map.items()),
                "Runtime manifest/map binding differs.")
        result["sources_before"] = verify_scope(metadata, source_map)
        result["metadata_source"] = pin(HERE / "metadata_recovery.py")
        result["gate_source"] = pin(__file__)
        os.chdir(RUNTIME)
        sys.path[:0] = [str(APP), str(APP / "native-v7"), str(APP / "training-v5")]
        sys.setprofile(forbid_proof_execution)
        native = metadata.import_runtime_native(APP)
        require(Path(native.__file__).resolve() == APP / "native-v7/peano_lab/__init__.py", "Wrong native package.")
        pilot = importlib.import_module("hydra_training_v5.decision_pilot")
        require(Path(pilot.__file__).resolve() == APP / "training-v5/hydra_training_v5/decision_pilot.py",
                "Wrong preparation module.")
        result["prepare_calls"] += 1
        plan = pilot.prepare(RUNTIME / metadata.CONFIG_REL, dataset_manifest=metadata.DATA_REL,
                             dataset_sha256=metadata.DATA_SHA, failure_output=OUTPUT / "admission-failure")
        recorded = json.loads((BUNDLE / "original-prepared-qwen3-1.7b-base.json").read_bytes())
        original, runtime_plan, derivation = metadata.normalized_plan(plan.record, recorded, recorded)
        require(runtime_plan["plan_sha256"] == RUNTIME_PLAN_SHA and original == recorded,
                "Complete regenerated plan differs beyond the explicit provider binding.")
        pilot._refresh(plan)
        metadata.require_runtime_imports(APP)
        imported = {name: str(Path(module.__file__).resolve().relative_to(APP))
                    for name, module in tuple(sys.modules.items()) if name.split(".", 1)[0] == "peano_lab"}
        require(imported and all(path.startswith("native-v7/peano_lab/") for path in imported.values()),
                "A native submodule escaped the exact selected package.")
        frozen = RUNTIME / "_deploy/hydra-retention-evaluation-recovery-execution-20260831/peano-lab/py"
        require(str(frozen) not in sys.path, "The exporter reselected its sibling fallback.")
        try:
            metadata.require_runtime_imports(ORIGINAL_APP)
        except ValueError as wrong_root:
            result["wrong_root_rejection"] = str(wrong_root)[:1200]
            require("module=" in str(wrong_root) and "path=" in str(wrong_root), "Missing import diagnosis.")
        else:
            raise ValueError("Actual runtime imports were incorrectly admitted against the original tree.")
        result.update(native_imports=imported, sibling_fallback_added=False, original_plan_sha256=original["plan_sha256"],
                      runtime_plan_sha256=runtime_plan["plan_sha256"], plan_derivation=derivation,
                      original_source_or_plan_rewritten=False, training_rows=runtime_plan["training_rows"],
                      validation_rows=runtime_plan["validation_rows"], formula_admission_performed=True)
        with (OUTPUT / "runtime-prepared-plan.json").open("xb") as stream:
            stream.write(canonical(runtime_plan) + b"\n")
        result["passed"] = True
    except BaseException as failure:
        result["passed"] = False
        result["error"] = {"type": type(failure).__name__, "detail": str(failure)[:1600]}
    finally:
        sys.setprofile(None)
        try:
            if source_map is not None and metadata is not None:
                result["sources_after"] = verify_scope(metadata, source_map)
                require(result.get("sources_before") == result["sources_after"], "Sources changed during preparation.")
                result["sources_unchanged"] = True
            require(not any(name.split(".", 1)[0] in FORBIDDEN for name in sys.modules), "A framework was imported.")
        except BaseException as failure:
            result["passed"] = False
            result["final_check_error"] = {"type": type(failure).__name__, "detail": str(failure)[:1600]}
        finally:
            signal.alarm(0)
    result["elapsed_seconds"] = time.monotonic() - started
    result["peak_rss_bytes"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    raw = canonical(result) + b"\n"
    require(len(raw) <= 256 * 1024, "Gate result exceeds its bound.")
    with (OUTPUT / "result.json").open("xb") as stream:
        stream.write(raw)
    print(json.dumps({key: result[key] for key in ("passed", "error", "prepare_calls", "elapsed_seconds", "peak_rss_bytes")}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
