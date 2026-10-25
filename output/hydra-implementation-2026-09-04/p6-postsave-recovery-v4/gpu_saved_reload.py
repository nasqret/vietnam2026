"""One pinned saved-adapter reload; no decoding, optimizer or native proof work.

The original training job remains FAILED. This controller writes only its new
job directory and never modifies the saved model, its manifest, or old evidence.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import stat
import sys
import time

PROJECT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training"
CAMPAIGN = PROJECT + "/experiments/hydra-practical-v1-20260904"
TRAINING_SOURCE = CAMPAIGN + "/bundles/source-data-07/source"
SOURCE = CAMPAIGN + "/bundles/source-data-09/source"
PACKAGE = CAMPAIGN + "/recovery/p6-postsave-recovery-v1"
ATTEMPT = "p6-saved-recovery-1.7b-import4-01"
JOB_DIRECTORY = CAMPAIGN + "/jobs/" + ATTEMPT
ORIGINAL_JOB = "21912020"
MODEL_KEY = "qwen3-1.7b-base"
MODEL_ID = "Qwen/Qwen3-1.7B-Base"
REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
ARTIFACT = TRAINING_SOURCE + "/output/hydra-implementation-2026-09-04/training-fresh-1.7b-v2-01"
BASE = CAMPAIGN + "/authenticated-bases-01/" + MODEL_KEY
BASE_SHA = "43ab517189660cd7319ab05c46d6c91f90150d2c4a42c942a16ff7cb804329f2"
UID = 105923
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"
TRAINING_PROVIDER_SHA = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
PROVIDER_SHA = "cc279710866146414c439e17935915f28d7dda7a44df20aa5d7e6bcd87994c44"
SMOKE_SHA = "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
TRAINING_SOURCE_MAP_SHA = "11aa82af08bce4369747ddc153a8d0b334243f69d497b16267a7151d0b62513c"
SOURCE_MAP_SHA = "85dadd08b91c9678fa8be1cf9624a82a5e0470b1c29f5a2f8cc25c7716a76f55"
RUNTIME_MANIFEST_SHA = "baa6c45db4fb01806a36aa188508e7cca9517a41934e5ad2f46739873722e1ff"
MANIFEST_SHA = "3799c7d3212885667cd28f7ba6e9d8f9ffcd12bc90bd7d03d031b96a7325f135"
FINAL_TENSOR_SHA = "2499801811ee63fb4f6c20e022d59aa0eeb2bb202ee41c9edd6bcd271e646c3c"
PLAN_SHA = "3ec6e96c39d3294671d61018431614ce02bff5b0874431e5883473cbb1cd5816"
METADATA_SCHEMA = "hydra-p6-postsave-metadata-recovery-v2"
ACTUAL_SCHEMA = "hydra-p6-postsave-metadata-actual-completion-v1"
RESERVATION_SCHEMA = "hydra-p6-saved-reload-reservation-v2"
MAX_RECORD_BYTES = 2 * 1024**2
MAX_OUTPUT_BYTES = 8 * 1024**2


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, maximum=MAX_RECORD_BYTES):
    path = Path(path)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path
            and before.st_size <= maximum, "Expected a bounded ordinary pinned input.")
    with path.open("rb") as stream:
        raw = stream.read(maximum + 1)
    after = path.lstat()
    require(len(raw) <= maximum and all(getattr(before, key) == getattr(after, key)
            for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")), "Input changed while read.")
    return raw


def save(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= MAX_RECORD_BYTES, "Recovery evidence exceeds its record bound.")
    with Path(path).open("xb") as stream:
        stream.write(raw)


def sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_metadata(metadata, actual, metadata_sha, verifier_sha):
    expected = {"schema": METADATA_SCHEMA, "passed": True, "eligible_for_saved_reload": True,
        "saved_adapter_reload_required": True, "model_loaded": False, "job_id": ORIGINAL_JOB,
        "original_process_exit_code": 1, "original_slurm_state": "FAILED",
        "original_slurm_exit_code": "1:0", "original_controller_completed": False,
        "training_source_root": TRAINING_SOURCE, "training_source_pins_sha256": TRAINING_SOURCE_MAP_SHA,
        "training_provider_sha256": TRAINING_PROVIDER_SHA,
        "runtime_source_root": SOURCE, "runtime_source_pins_sha256": SOURCE_MAP_SHA,
        "runtime_provider_sha256": PROVIDER_SHA, "runtime_manifest_sha256": RUNTIME_MANIFEST_SHA,
        "runtime_inference_only": True, "runtime_training_execution_allowed": False,
        "manifest_sha256": MANIFEST_SHA, "artifact_directory": ARTIFACT, "base_directory": BASE,
        "final_tensor_population_sha256": FINAL_TENSOR_SHA, "plan_sha256": PLAN_SHA,
        "metadata_source_sha256": verifier_sha, "sources_unchanged": True, "errors": [],
        "original_recorded_saved_plan_canonical_json_equal": True,
        "runtime_plan_matches_exact_provider_rebinding": True, "training_exposure_changed": False}
    require(type(metadata) is dict and all(type(metadata.get(k)) is type(v) and metadata.get(k) == v
            for k, v in expected.items()), "Successful exact CPU metadata recovery is required before GPU reload.")
    require(type(actual) is dict and actual.get("schema") == ACTUAL_SCHEMA
            and type(actual.get("actual_exit_code")) is int and actual["actual_exit_code"] == 0
            and actual.get("receipt_sha256") == metadata_sha and actual.get("verifier_sha256") == verifier_sha
            and type(actual.get("completion_chunk")) is str
            and re.fullmatch(r"[0-9a-f]{6,64}", actual["completion_chunk"]),
            "Actual successful CPU receipt is missing or bound to another verifier/result.")
    require(sha(metadata_sha) and sha(verifier_sha), "Invalid metadata source/receipt identity.")
    runtime_plan = metadata.get("runtime_regenerated_plan_sha256")
    require(sha(runtime_plan) and runtime_plan != PLAN_SHA and metadata.get("plan_derivation") == {
        "schema": "hydra-p6-recovery-runtime-plan-rebinding-v1", "original_plan_sha256": PLAN_SHA,
        "runtime_plan_sha256": runtime_plan, "only_source_pin_changed": "hydra-playground/experimental_model.py",
        "training_provider_sha256": TRAINING_PROVIDER_SHA, "runtime_provider_sha256": PROVIDER_SHA,
        "all_other_plan_fields_canonical_equal": True, "training_exposure_changed": False, "new_training_performed": False},
        "Complete original/runtime plan derivation is missing.")
    validate_source_maps(metadata.get("training_source_pins"), metadata.get("runtime_source_pins"))
    validate_config_admission(metadata.get("adapter_config_admission"))


def validate_reservation(record, uid):
    require(type(uid) is int and uid == UID, "Recovery belongs to the exact original campaign owner.")
    expected = {"schema": RESERVATION_SCHEMA, "attempt": ATTEMPT,
        "job_name": "hydra-" + ATTEMPT, "uid": uid, "account": ACCOUNT, "partition": PARTITION,
        "model_key": MODEL_KEY, "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64,
        "seconds": 300, "soft_limit_seconds": 240, "original_job_id": ORIGINAL_JOB,
        "provider_sha256": PROVIDER_SHA, "scheduler_helper_sha256": SMOKE_SHA,
        "source_pins_sha256": SOURCE_MAP_SHA, "artifact_manifest_sha256": MANIFEST_SHA,
        "final_tensor_population_sha256": FINAL_TENSOR_SHA, "runtime_source_root": SOURCE,
        "training_source_root": TRAINING_SOURCE, "training_source_pins_sha256": TRAINING_SOURCE_MAP_SHA,
        "training_provider_sha256": TRAINING_PROVIDER_SHA, "runtime_manifest_sha256": RUNTIME_MANIFEST_SHA,
        "artifact_directory": ARTIFACT, "base_directory": BASE,
        "generation_calls": 0, "optimizer_updates": 0, "native_calls": 0,
        "automatic_retry": False, "resume": False}
    variable = {"job_id", "nonce", "controller_sha256", "metadata_receipt_sha256",
                "metadata_actual_sha256", "metadata_verifier_sha256"}
    require(type(record) is dict and set(record) == set(expected) | variable
            and all(type(record.get(k)) is type(v) and record.get(k) == v for k, v in expected.items()),
            "Recovery reservation must bind the exact one-job, zero-generation contract.")
    require(type(record["job_id"]) is str and re.fullmatch(r"[0-9]{1,20}", record["job_id"])
            and record["job_id"] != ORIGINAL_JOB and type(record["nonce"]) is str
            and re.fullmatch(r"[0-9a-f]{32}", record["nonce"]), "Invalid new one-use recovery identity.")
    require(all(sha(record[k]) for k in variable - {"job_id", "nonce"}), "Missing exact recovery input pins.")
    return record


def validate_source_maps(training_map, runtime_map):
    require(type(training_map) is dict and type(runtime_map) is dict
            and len(training_map) == len(runtime_map) == 585 and set(training_map) == set(runtime_map),
            "Original and runtime scopes require the same exact 585 source names.")
    require(digest(canonical(training_map)) == TRAINING_SOURCE_MAP_SHA
            and digest(canonical(runtime_map)) == SOURCE_MAP_SHA, "Original/runtime source-map identity differs.")
    provider = "hydra-playground/experimental_model.py"
    require([name for name in sorted(training_map) if training_map[name] != runtime_map[name]] == [provider]
            and training_map[provider]["sha256"] == TRAINING_PROVIDER_SHA
            and runtime_map[provider]["sha256"] == PROVIDER_SHA,
            "Only the pinned inference provider may differ from original training sources.")
    for mapping in (training_map, runtime_map):
        for name, pin in mapping.items():
            require(type(name) is str and not Path(name).is_absolute() and ".." not in Path(name).parts
                    and Path(name).as_posix() == name and type(pin) is dict and set(pin) == {"bytes", "sha256"}
                    and type(pin["bytes"]) is int and 0 < pin["bytes"] <= 4 * 1024**2 and sha(pin["sha256"]),
                    "Unsafe or unbounded source descriptor.")


def source_pins():
    training_map = json.loads(read(Path(PACKAGE) / "controller-source-pins.json"))
    runtime_map = json.loads(read(Path(PACKAGE) / "runtime-source-pins-base3.json"))
    validate_source_maps(training_map, runtime_map)
    raw_manifest = read(Path(SOURCE).parent / "manifest.json")
    manifest = json.loads(raw_manifest)
    require(digest(raw_manifest) == RUNTIME_MANIFEST_SHA
            and manifest.get("schema") == "hydra-exact-source-data-bundle-v3"
            and manifest.get("inference_only") is True and manifest.get("training_execution_allowed") is False,
            "New runtime is not the exact inference-only source bundle.")
    for source, mapping in ((TRAINING_SOURCE, training_map), (SOURCE, runtime_map)):
        total = 0
        for name, pin in mapping.items():
            raw = read(Path(source) / name, 4 * 1024**2)
            total += len(raw)
            require(total <= 32 * 1024**2 and pin == {"bytes": len(raw), "sha256": digest(raw)},
                    "Original or runtime source bytes changed.")
            if source == SOURCE:
                require(manifest["files"].get(name) == pin, "Runtime source map and manifest differ.")
        prefixes = ("hydra-playground/native-v7/peano_lab/", "hydra-playground/training-v5/hydra_training_v5/")
        expected_python = {name for name in mapping if name.endswith(".py") and name.startswith(prefixes)}
        actual_python = {str(path.relative_to(source)) for prefix in prefixes
                         for path in (Path(source) / prefix).rglob("*.py")}
        require(actual_python == expected_python, "Original/runtime native or training inventory changed.")
    require(runtime_map["output/p6-prototype/remote_provider_smoke.py"]["sha256"] == SMOKE_SHA,
            "Original scheduler helper changed in the inference-only runtime.")
    return runtime_map


def validate_config_admission(evidence):
    expected = {"schema": "hydra-peft-base-identity-admission-v1", "policy": "hydra-peft-authenticated-local-base-v1",
        "adapter_kind": "fresh_decision_pilot", "local_base_name_used": True,
        "recorded_name_matches_authenticated_directory": True,
        "canonical_base_model_id": MODEL_ID, "authenticated_base_identity_sha256": BASE_SHA,
        "authenticated_base_directory_sha256": digest(BASE.encode("utf-8")), "normalization_fields": ["base_model_name_or_path"],
        "saved_config_modified": False, "base_selected_from_adapter_metadata": False}
    require(type(evidence) is dict and all(type(evidence.get(k)) is type(v) and evidence.get(k) == v
            for k, v in expected.items()), "Saved Base display-name normalization is not fully authenticated.")
    require(sha(evidence.get("original_config_canonical_sha256")) and sha(evidence.get("validated_config_canonical_sha256"))
            and evidence["original_config_canonical_sha256"] != evidence["validated_config_canonical_sha256"]
            and type(evidence.get("config_file")) is dict and set(evidence["config_file"]) == {"bytes", "sha256"}
            and type(evidence["config_file"]["bytes"]) is int and 0 < evidence["config_file"]["bytes"] <= 65536
            and sha(evidence["config_file"]["sha256"]), "Raw and normalized config identities are missing.")


def artifact_pins(stop=lambda: False):
    root = Path(ARTIFACT)
    raw = read(root / "manifest.json", 4 * 1024**2)
    require(digest(raw) == MANIFEST_SHA and not (root / "incomplete.json").exists(),
            "Original saved artifact is missing, changed or incomplete.")
    record = json.loads(raw)
    require(record["adapter_update"]["final_tensor_population_sha256"] == FINAL_TENSOR_SHA
            and record["plan"]["plan_sha256"] == PLAN_SHA and record["reservation"]["job_id"] == ORIGINAL_JOB,
            "Original artifact provenance differs.")
    pins, total = {"manifest.json": {"bytes": len(raw), "sha256": digest(raw)}}, 0
    for group in ("adapter", "tokenizer"):
        files = record[group]["files"]
        directory = root / group
        require(type(files) is dict and 1 <= len(files) <= 16 and directory.is_dir()
                and not directory.is_symlink(), "Unsafe saved artifact tree.")
        names = set()
        for path in directory.iterdir():
            names.add(group + "/" + path.name)
            require(len(names) <= 16, "Saved artifact inventory exceeds its finite file bound.")
        require(names == set(files), "Saved artifact inventory changed.")
        for name, expected in sorted(files.items()):
            require(type(name) is str and name.startswith(group + "/") and name.count("/") == 1
                    and Path(name).name not in (".", "..") and sha(expected), "Unsafe artifact path/hash.")
            path = root / name
            before = path.lstat()
            total += before.st_size
            require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path
                    and total <= 256 * 1024**2, "Saved artifact is not a bounded ordinary input.")
            hasher = hashlib.sha256()
            with path.open("rb") as stream:
                while True:
                    if stop():
                        raise TimeoutError("Saved-input hashing reached the recovery deadline.")
                    chunk = stream.read(1024**2)
                    if not chunk:
                        break
                    hasher.update(chunk)
            after = path.lstat()
            require(all(getattr(before, key) == getattr(after, key)
                        for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns"))
                    and hasher.hexdigest() == expected, "Saved artifact changed during read.")
            pins[name] = {"bytes": before.st_size, "sha256": expected}
    return pins


def validate_loaded_report(report, job_id):
    require(type(report) is dict and all(type(report.get(k)) is int and report[k] == 0
            for k in ("actual_model_calls", "forward_passes", "generated_token_slots")),
            "The recovery must perform zero generation/forward calls.")
    identity = report["identity"]
    adapter = identity["adapter"]
    require(identity.get("source_sha256") == PROVIDER_SHA and identity.get("model_id") == MODEL_ID
            and identity.get("profile") == "hydra-experimental-torch-qwen3-v3"
            and identity.get("predecessor_source_sha256") == TRAINING_PROVIDER_SHA
            and identity.get("revision") == REVISION and identity.get("model_loaded") is True
            and identity.get("base_identity_sha256") == BASE_SHA
            and identity.get("automatic_retry") is False and identity.get("automatic_download") is False
            and identity.get("allocation") == {"job_id": job_id, "gpus": 1, "cpus": 8, "memory_gib": 64, "seconds": 300}
            and adapter.get("adapter_present") is True and adapter.get("saved_adapter_reload_checked") is True
            and adapter.get("adapter_manifest_sha256") == MANIFEST_SHA
            and adapter.get("final_tensor_population_sha256") == FINAL_TENSOR_SHA
            and adapter.get("adapter_kind") == "fresh_decision_pilot", "Independent full tensor reload was not admitted.")
    validate_config_admission(adapter.get("base_identity_admission"))


def run(args):
    began = time.monotonic()
    os.umask(0o077)
    require(Path(__file__).resolve() == Path(PACKAGE) / "gpu_saved_reload_import4.py", "Unreviewed recovery deployment path.")
    reservation_path = Path(JOB_DIRECTORY) / "reservation.json"
    raw = read(reservation_path, 65536)
    require(sha(args.reservation_sha256) and digest(raw) == args.reservation_sha256, "Reservation bytes changed.")
    record = validate_reservation(json.loads(raw), os.getuid())
    require(digest(read(Path(__file__))) == record["controller_sha256"]
            and os.environ.get("SLURM_JOB_ID") == record["job_id"], "Not the exact admitted recovery controller/job.")
    metadata_raw = read(Path(PACKAGE) / "metadata-recovery-import4.json")
    actual_raw = read(Path(PACKAGE) / "metadata-actual-completion-import4.json", 65536)
    require(digest(metadata_raw) == record["metadata_receipt_sha256"]
            and digest(actual_raw) == record["metadata_actual_sha256"]
            and digest(read(Path(PACKAGE) / "metadata_recovery_import4.py")) == record["metadata_verifier_sha256"],
            "CPU metadata admission changed before reload.")
    validate_metadata(json.loads(metadata_raw), json.loads(actual_raw), digest(metadata_raw), record["metadata_verifier_sha256"])
    recovery_inputs = {"gpu_saved_reload_import4.py": record["controller_sha256"],
        "metadata_recovery_import4.py": record["metadata_verifier_sha256"],
        "metadata-recovery-import4.json": record["metadata_receipt_sha256"],
        "metadata-actual-completion-import4.json": record["metadata_actual_sha256"]}
    before = source_pins()
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (240, 250))
    resource.setrlimit(resource.RLIMIT_FSIZE, (MAX_OUTPUT_BYTES, MAX_OUTPUT_BYTES))
    output = Path(JOB_DIRECTORY) / "result"
    require(output.resolve() == output, "Recovery output must not escape through links.")
    output.mkdir(exist_ok=False)
    helper_path = Path(SOURCE) / "output/p6-prototype/remote_provider_smoke.py"
    helper_spec = importlib.util.spec_from_file_location("hydra_original_scheduler_cc8", helper_path)
    helpers = importlib.util.module_from_spec(helper_spec)
    helper_spec.loader.exec_module(helpers)
    checker = helpers.LiveReservation(record, output)
    completed, error, session, report, inputs_before = False, None, None, None, None
    unchanged, disposed = False, False
    deadline = began + 240
    def stop():
        return time.monotonic() >= deadline
    def alarm(_signum, _frame):
        raise TimeoutError("Saved reload reached its soft deadline/cancellation; no retry.")
    for signum in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
        signal.signal(signum, alarm)
    signal.alarm(240)
    try:
        first = checker()
        deadline = min(deadline, time.monotonic() + max(0, 240 - first["elapsed_seconds"]))
        require(not stop(), "No recovery budget remains.")
        signal.alarm(max(1, math.ceil(deadline - time.monotonic())))
        save(reservation_path.with_name("reservation.json.claimed"), {
            "schema": "hydra-p6-saved-reload-consumption-v2", "job_id": record["job_id"],
            "nonce": record["nonce"], "reservation_sha256": args.reservation_sha256,
            "pid": os.getpid(), "output": str(output), "first_live_allocation": first, "automatic_retry": False})
        require(digest(read(reservation_path, 65536)) == args.reservation_sha256, "Reservation changed during claim.")
        save(output / "request.json", {"schema": "hydra-p6-saved-reload-request-v2", "reservation": record,
            "reservation_sha256": args.reservation_sha256, "source_pins_before": before,
            "runtime_source_root": SOURCE, "runtime_provider_sha256": PROVIDER_SHA,
            "runtime_source_pins_sha256": SOURCE_MAP_SHA,
            "training_source_root": TRAINING_SOURCE, "training_provider_sha256": TRAINING_PROVIDER_SHA,
            "training_source_pins_sha256": TRAINING_SOURCE_MAP_SHA,
            "original_failed_job_preserved": True, "generation_calls": 0, "optimizer_updates": 0,
            "native_calls": 0, "automatic_retry": False})
        inputs_before = artifact_pins(stop)
        save(output / "artifact-before.json", inputs_before)
        app = Path(SOURCE) / "hydra-playground"
        os.chdir(SOURCE)
        sys.path[:0] = [str(app), str(app / "native-v7"), str(app / "training-v5")]
        from experimental_model import load_torch_model, SessionLimits
        started = time.monotonic()
        session = load_torch_model(MODEL_KEY, base_directory=BASE, adapter_directory=ARTIFACT,
            adapter_manifest_sha256=MANIFEST_SHA, adapter_kind="fresh_decision_pilot",
            reservation_check=checker, should_stop=stop, limits=SessionLimits(max_calls=1, max_token_slots=1), seed=0)
        # SessionLimits cannot express zero. No decoder, encode or generation method is called.
        report = session.report()
        validate_loaded_report(report, record["job_id"])
        require(report["identity"]["adapter"]["base_identity_admission"]
                == json.loads(metadata_raw)["adapter_config_admission"],
                "GPU config admission differs from the authenticated CPU evidence.")
        report["reload_elapsed_seconds"] = time.monotonic() - started
        report["peak_allocated_gpu_bytes"] = session.torch.cuda.max_memory_allocated()
        report["peak_reserved_gpu_bytes"] = session.torch.cuda.max_memory_reserved()
        save(output / "loaded-model.json", report)
        checker()
        if stop():
            raise TimeoutError("Reload finished beyond the recovery soft deadline.")
        completed = True
    except BaseException as failure:
        completed = False
        error = {"type": type(failure).__name__, "detail": str(failure)[:1500]}
    finally:
        # Slurm owns the hard 300-second wall and 64-GiB allocation. Leave a bounded cleanup reserve.
        signal.alarm(max(1, min(45, math.ceil(began + 290 - time.monotonic()))))
        try:
            torch = None if session is None else session.torch
            session = None
            gc.collect()
            if torch is not None:
                torch.cuda.empty_cache()
            disposed = True
            after = source_pins()
            inputs_after = artifact_pins(lambda: time.monotonic() >= began + 285)
            unchanged = before == after and inputs_before == inputs_after and all(
                digest(read(Path(PACKAGE) / name)) == pin for name, pin in recovery_inputs.items())
            save(output / "artifact-after.json", inputs_after)
            require(unchanged, "Recovery source or original saved artifact changed.")
        except BaseException as failure:
            completed = False
            error = error or {"type": type(failure).__name__, "detail": str(failure)[:1500]}
        finally:
            signal.alarm(0)
        result = {"schema": "hydra-p6-saved-reload-completion-v2", "completed": completed and unchanged and disposed and error is None,
            "error": error, "job_id": record["job_id"], "original_job_id": ORIGINAL_JOB,
            "original_slurm_state": "FAILED", "original_slurm_exit_code": "1:0",
            "original_failed_job_preserved": True, "elapsed_seconds": time.monotonic() - began,
            "metadata_receipt_sha256": record["metadata_receipt_sha256"],
            "metadata_actual_sha256": record["metadata_actual_sha256"],
            "controller_sha256": record["controller_sha256"], "provider_sha256": PROVIDER_SHA,
            "source_pins_sha256": SOURCE_MAP_SHA, "sources_and_artifact_unchanged": unchanged,
            "runtime_source_root": SOURCE, "runtime_provider_sha256": PROVIDER_SHA,
            "runtime_source_pins_sha256": SOURCE_MAP_SHA, "runtime_manifest_sha256": RUNTIME_MANIFEST_SHA,
            "training_source_root": TRAINING_SOURCE, "training_provider_sha256": TRAINING_PROVIDER_SHA,
            "training_source_pins_sha256": TRAINING_SOURCE_MAP_SHA,
            "artifact_manifest_sha256": MANIFEST_SHA, "final_tensor_population_sha256": FINAL_TENSOR_SHA,
            "saved_adapter_reload_checked": completed and unchanged and disposed and error is None and report is not None,
            "model_disposal_attempted": True, "model_disposal_completed": disposed,
            "last_live_allocation": checker.last, "scheduler_calls": checker.calls,
            "generation_calls": 0, "optimizer_updates": 0, "native_calls": 0, "solver_calls": 0,
            "automatic_retry": False, "resaved_manifest": False, "quality_evaluated": False,
            "cleanup_scope": "No model/helper subprocess; pinned scheduler children are owned and reaped. Final Slurm/process exits are separately required."}
        require(sum(p.stat().st_size for p in output.iterdir() if p.is_file()) + len(canonical(result)) + 1
                <= MAX_OUTPUT_BYTES, "Recovery output exceeded its total evidence bound.")
        save(output / "completion.json", result)
        print(json.dumps({k: result[k] for k in ("completed", "job_id", "elapsed_seconds", "saved_adapter_reload_checked", "error")}), flush=True)
    return 0 if result["completed"] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reservation-sha256", required=True)
    args = parser.parse_args()
    try:
        return run(args)
    except BaseException as error:
        print(json.dumps({"completed": False, "error_type": type(error).__name__, "error": str(error)[:1500], "automatic_retry": False}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
