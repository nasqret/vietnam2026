# Binds the separately reviewed 15-second, single-query scheduler helper.
# Provider v2 binding of the frozen p6-prototype controller.
# Uses the v2 Transformers 4.53.3 beam-slot accounting; no controller behavior,
# reservation schema, resource ceiling, or retry policy changes.
"""One root-bound fresh decision pilot; never submit, download, resume or retry.

Preparation of this controller does not run a pilot. Its CLI may run only inside
the exact live Slurm allocation named by a new, hash-pinned reservation. The
frozen decision_pilot module owns training, objectives, tensor audits and saves.
P6 must independently reload any saved adapter before using it for inference.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.metadata
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import re
import signal
import sys
import time

SMOKE_SHA = "cc8dec7bcb2187568c1aed1eaa1b580435460e297573b655eac2b32b74a271b4"
FIXED_SOURCES = {
    "experimental_model.py": "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f",
    "experimental-models/qwen3-base-v1.json": "3303c4727052557a04bc2e33ea624ff7093703c68ae8fa95b12fb05adbc781c1",
    "export_decisions.py": "886dfa337725f24290172d8a723133f03d2597a835b355a6af47823932dc491a",
    "branch_ranker.py": "e868f3576bfec3654c2e3fe836367537a1f890074423be201fec45f6f2632be6",
    "certificate_codec.py": "8d14b57dadb75d844aeec7633e5b6290d214cb00880b39f1709796c8f1a3e59e",
    "evaluation-holdout.json": "2a57f12ffe55f90c3c4ac896fba3c2bab47e795b6bb5ba5f15b2c6854cddb58e",
    "training-v5/BASELINE.json": "fa0f560dfd2310557ad31271786dd89abd4878f4f074be98da74e3301558db8d",
    "training-v5/hydra_training_v5/decision_data.py": "b3a6fb79fee07c6b5fdc61988a56e598bb57cea0b7e5501df80519422cbddb53",
    "training-v5/hydra_training_v5/decision_pilot.py": "284d4bc74b2379dd08ffc4ecc5cb029d9593504e71d53f86761d4d5542b281e8",
    "training-v5/hydra_training_v5/pilot_config.py": "8516bfdc9c79ab040bbd0a514ae7a3095ab7a1614a62b0920c0adaa433a710cb",
}
MODELS = {
    "qwen3-1.7b-base": ("Qwen/Qwen3-1.7B-Base", "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"),
    "qwen3-4b-base": ("Qwen/Qwen3-4B-Base", "906bfd4b4dc7f14ee4320094d8b41684abff8539"),
    "qwen3-8b-base": ("Qwen/Qwen3-8B-Base", "49e3418fbbbca6ecbdf9608b4d22e5a407081db4"),
}
MAX_RECORD_BYTES = 2 * 1024**2
MAX_EVIDENCE_BYTES = 8 * 1024**2
MAX_PROGRESS_EVENTS = 1024
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def valid_sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def ordinary(path, maximum=MAX_RECORD_BYTES):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= maximum,
            "Expected a bounded ordinary file: " + str(path))
    before = path.stat()
    raw = path.read_bytes()
    after = path.stat()
    require((before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
            and len(raw) == before.st_size, "File changed during its read.")
    return raw


def digest(path, maximum=MAX_RECORD_BYTES):
    return sha256(ordinary(path, maximum)).hexdigest()


def save(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= MAX_RECORD_BYTES, "One controller record exceeded its byte ceiling.")
    with Path(path).open("xb") as stream:
        stream.write(raw)


def smoke_helpers():
    """Only stdlib code is imported; the reviewed helper never submits jobs."""
    path = Path(__file__).with_name("remote_provider_smoke.py")
    require(digest(path) == SMOKE_SHA, "Scheduler helper differs from its reviewed pin.")
    spec = importlib.util.spec_from_file_location("hydra_training_scheduler_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reservation_spec(record):
    fields = {"schema", "job_id", "job_name", "nonce", "uid", "account", "partition",
              "model_key", "gpus", "nodes", "cpus", "memory_gib", "seconds", "soft_limit_seconds",
              "config_sha256", "dataset_sha256", "plan_sha256", "controller_sha256", "source_pins_sha256"}
    require(type(record) is dict and set(record) == fields
            and record["schema"] == "hydra-p6-training-reservation-v1",
            "Expected exactly the versioned one-use training reservation fields.")
    require(type(record["job_id"]) is str and re.fullmatch(r"\d{1,20}", record["job_id"])
            and type(record["job_name"]) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", record["job_name"])
            and type(record["nonce"]) is str and re.fullmatch(r"[0-9a-f]{32}", record["nonce"]),
            "Malformed reservation identity.")
    require(type(record["uid"]) is int and record["uid"] == os.getuid()
            and record["account"] == ACCOUNT and record["partition"] == PARTITION
            and record["model_key"] in MODELS, "Reservation owner/account/partition/model differs.")
    for key, value in (("gpus", 1), ("nodes", 1), ("cpus", 8), ("memory_gib", 64)):
        require(type(record[key]) is int and record[key] == value,
                "Training requires one explicitly bounded 1-GPU/8-CPU/64-GiB allocation.")
    require(type(record["seconds"]) is int and 300 <= record["seconds"] <= 7200
            and type(record["soft_limit_seconds"]) is int
            and 60 <= record["soft_limit_seconds"] <= min(6900, record["seconds"] - 60),
            "Training allocation/soft stop exceeds its finite limits or cleanup reserve.")
    require(all(valid_sha(record[key]) for key in fields if key.endswith("_sha256")),
            "Reservation is missing a complete exact content pin.")
    return record


def source_pins(app):
    """Portable code-scope hash; no model or native computation is performed."""
    app = Path(app).resolve(strict=True)
    files = {app / name for name in FIXED_SOURCES}
    files.update((app / "native-v7/peano_lab").rglob("*.py"))
    files.update((app / "training-v5/hydra_training_v5").rglob("*.py"))
    files.update((Path(__file__).resolve(), Path(__file__).with_name("remote_provider_smoke.py").resolve()))
    require(100 <= len(files) <= 1024, "Missing/oversized training source bundle.")
    result, total = {}, 0
    for path in sorted(files):
        relative = path.relative_to(app.parent)
        require(path.resolve(strict=True) == app.parent / relative, "A source path escapes through a symlink.")
        raw = ordinary(path, 4 * 1024**2)
        total += len(raw)
        require(total <= 32 * 1024**2, "Training source bundle exceeds 32 MiB.")
        result[relative.as_posix()] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    for name, expected in FIXED_SOURCES.items():
        require(result[(Path(app.name) / name).as_posix()]["sha256"] == expected,
                "Reviewed training source changed: " + name)
    return result


def validate_plan(record, reservation):
    expected_model = dict(zip(("model_id", "revision"), MODELS[reservation["model_key"]]))
    require(type(record) is dict and record.get("schema") == "hydra-decision-pilot-plan-v2"
            and record.get("profile") == "hydra-fresh-decision-pilot-v2"
            and record.get("model") == expected_model
            and record.get("config_sha256") == reservation["config_sha256"]
            and record.get("plan_sha256") == reservation["plan_sha256"],
            "Prepared plan differs from the exact reserved model/config/plan.")
    require(sha256(canonical({key: value for key, value in record.items() if key != "plan_sha256"})).hexdigest()
            == reservation["plan_sha256"], "Prepared plan content does not match its hash.")
    require(record.get("resume") is False and record.get("automatic_retry") is False
            and record.get("epochs") == 1 and record.get("prompt_schema") == "primitive_v4"
            and record.get("planner_rows_allowed") is False and record.get("model_trained") is False,
            "The plan is not one fresh primitive-only pass.")
    rows, validation = record.get("training_rows"), record.get("validation_rows")
    require(type(rows) is int and 1 <= rows <= 4096
            and type(validation) is int and 1 <= validation <= 4096
            and record.get("expected_optimizer_steps") == (rows + 7) // 8,
            "Plan rows/steps exceed the fixed one-pass pilot contract.")


def claim_reservation(path, reservation, expected_sha, output, first_live):
    require(digest(path, 65536) == expected_sha, "Reservation changed before its one-use claim.")
    require(first_live["job_id"] == reservation["job_id"], "Cannot claim another live job.")
    claim = Path(path).with_name(Path(path).name + ".claimed")
    save(claim, {"schema": "hydra-p6-training-reservation-consumption-v1",
        "job_id": reservation["job_id"], "nonce": reservation["nonce"], "reservation_sha256": expected_sha,
        "config_sha256": reservation["config_sha256"], "dataset_sha256": reservation["dataset_sha256"],
        "plan_sha256": reservation["plan_sha256"], "output": str(output), "pid": os.getpid(),
        "first_live_allocation": first_live, "automatic_retry": False, "resume": False})
    return claim


class Progress:
    """Actual callback observations, never invented optimizer/model counts."""
    def __init__(self, output, checker, expected_steps, clock=time.monotonic):
        self.output, self.checker, self.expected_steps, self.clock = output, checker, expected_steps, clock
        self.events = self.bytes = self.last_optimizer_step = 0
        self.started = self.last_scheduler = self.last_print = clock()

    def __call__(self, value):
        require(type(value) is dict and self.events < MAX_PROGRESS_EVENTS, "Invalid/unbounded training progress.")
        kind = value.get("kind")
        require(kind in {"loading-model", "training-start", "optimizer-step", "training-complete"},
                "Unknown frozen training callback kind.")
        if kind == "optimizer-step":
            step = value.get("step")
            require(type(step) is int and step == self.last_optimizer_step + 1
                    and step <= self.expected_steps, "Optimizer callback order/budget differs.")
            self.last_optimizer_step = step
        now = self.clock()
        raw = canonical({"event": self.events + 1, "elapsed_seconds": now - self.started, **value}) + b"\n"
        require(len(raw) <= 8192 and self.bytes + len(raw) <= MAX_RECORD_BYTES, "Progress evidence exceeded its bound.")
        with (self.output / "progress.jsonl").open("ab") as stream:
            stream.write(raw)
        self.events += 1
        self.bytes += len(raw)
        if now - self.last_scheduler >= 150 or kind in {"loading-model", "training-start", "training-complete"}:
            self.checker()
            self.last_scheduler = self.clock()
        if now - self.last_print >= 15 or kind != "optimizer-step":
            print(raw.decode().strip(), flush=True)
            self.last_print = self.clock()


def runtime_identity(registry):
    require(platform.system() == "Linux" and platform.machine() == "aarch64"
            and sys.version_info[:3] == (3, 13, 5), "Training requires the reviewed Linux/aarch64 Python 3.13.5 runtime.")
    require(sys.flags.ignore_environment == 0,
            "Do not launch training with -E/-I: Python must honor the pre-start PYTHONHASHSEED.")
    versions = {name: importlib.metadata.version(name) for name in registry["dependencies"]}
    require(versions == registry["dependencies"], "Training dependencies differ from the pinned P6 environment.")
    require(os.environ.get("WORLD_SIZE", "1") == "1", "Multi-process training is outside this pilot.")
    return {"platform": platform.platform(), "python": sys.version, "dependencies": versions,
            "python_honors_environment": True,
            "single_process": True, "automatic_download": False}


def validate_artifact(artifact, plan_record, tokens, training_output, manifest_module):
    require(type(artifact) is dict and artifact.get("schema") == "hydra-decision-pilot-artifact-v1"
            and artifact.get("model_trained") is True and artifact.get("resume") is False
            and artifact.get("automatic_retry") is False and artifact.get("plan") == plan_record
            and artifact.get("token_preflight") == tokens and artifact.get("base") == tokens["base"]
            and artifact.get("actual_optimizer_steps") == plan_record["expected_optimizer_steps"]
            and artifact.get("saved_adapter_reload_admission") == "required_by_P6_before_inference",
            "Training did not return a complete, exactly bound one-pass artifact.")
    require(not (training_output / "incomplete.json").exists(), "An incomplete attempt cannot be admitted as trained.")
    for name, directory in (("adapter", manifest_module.ADAPTER_SUBDIR), ("tokenizer", manifest_module.TOKENIZER_SUBDIR)):
        require(manifest_module.artifact_directory_hash(training_output, directory) == artifact[name],
                "Saved artifact bytes changed: " + name)
    manifest_module.require_safetensors_adapter(artifact["adapter"])


def run(args):
    helpers = smoke_helpers()
    app = args.app_root.resolve(strict=True)
    reservation_path = args.reservation.absolute()
    raw = ordinary(reservation_path, 65536)
    require(valid_sha(args.reservation_sha256) and sha256(raw).hexdigest() == args.reservation_sha256,
            "Reservation bytes differ from their explicit pin.")
    reservation = reservation_spec(helpers.strict_json(raw))
    require(args.model_key == reservation["model_key"] and digest(__file__) == reservation["controller_sha256"],
            "Controller/model differs from the exact reserved attempt.")
    before = source_pins(app)
    require(sha256(canonical(before)).hexdigest() == reservation["source_pins_sha256"],
            "Full executed source scope differs from the reserved source hash.")
    config = args.config.resolve(strict=True)
    dataset = args.dataset_manifest.resolve(strict=True)
    require(config.is_relative_to(app.parent) and dataset.is_relative_to(app.parent)
            and not args.config.is_symlink() and not args.dataset_manifest.is_symlink()
            and digest(config, 32768) == reservation["config_sha256"]
            and digest(dataset) == reservation["dataset_sha256"], "Dataset/config pin or source-root binding differs.")
    require(os.environ.get("SLURM_JOB_ID") == reservation["job_id"], "Not inside the exact reserved Slurm job.")
    output = args.output.absolute()
    require(not output.is_symlink() and output.resolve() == output, "Controller output must not escape through a symlink.")
    output.mkdir(parents=True, exist_ok=False)
    began = time.monotonic()
    checker = helpers.LiveReservation(reservation, output)
    claim = first = plan = progress = artifact = training_output = tokens = None
    deadline = None
    error = None
    before_alarm = None
    before_handlers = {}
    completed = execute_started = False
    after = None
    returned = None
    try:
        first = checker()
        claim = claim_reservation(reservation_path, reservation, args.reservation_sha256, output, first)
        require(digest(reservation_path, 65536) == args.reservation_sha256,
                "Reservation changed during its consumed claim.")
        deadline = began + reservation["soft_limit_seconds"] - first["elapsed_seconds"]
        require(deadline - time.monotonic() >= 30, "Insufficient time remains before the explicit training soft stop.")
        def stop():
            return time.monotonic() >= deadline
        def interrupt(signum, frame):
            raise TimeoutError("Owned training soft stop/signal reached; this attempt cannot resume or retry.")
        for sig in (signal.SIGALRM, signal.SIGTERM, signal.SIGINT):
            before_handlers[sig] = signal.signal(sig, interrupt)
        before_alarm = signal.alarm(max(1, math.ceil(deadline - time.monotonic())))
        require(before_alarm == 0, "An inherited alarm conflicts with this one-use controller.")
        save(output / "request.json", {"schema": "hydra-p6-remote-training-request-v1",
            "reservation": reservation, "reservation_sha256": args.reservation_sha256,
            "source_pins_before": before, "config": config.relative_to(app.parent).as_posix(),
            "dataset_manifest": dataset.relative_to(app.parent).as_posix(),
            "base_directory": str(args.base_directory), "claimed": str(claim),
            "soft_stop_from_allocation_start_seconds": reservation["soft_limit_seconds"],
            "campaign_hours_ceiling": 6, "campaign_ledger_enforced_by": "root_job_orchestrator",
            "automatic_retry": False, "resume": False, "benchmark_claim": False,
            "native_proof_searches": 0, "native_proof_replays": 0, "solver_calls": 0})
        os.chdir(app.parent)
        sys.path[:0] = [str(app), str(app / "native-v7"), str(app / "training-v5")]
        os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false", WANDB_MODE="disabled")
        registry = helpers.strict_json(ordinary(app / "experimental-models/qwen3-base-v1.json"))
        save(output / "runtime.json", runtime_identity(registry))
        from hydra_training_v5 import decision_pilot
        require(Path(decision_pilot.__file__).resolve() == app / "training-v5/hydra_training_v5/decision_pilot.py",
                "Training module came from an unexpected path.")
        plan = decision_pilot.prepare(config, dataset_manifest=dataset.relative_to(app.parent).as_posix(),
            dataset_sha256=reservation["dataset_sha256"], failure_output=output / "admission-failure")
        validate_plan(plan.record, reservation)
        require(os.environ.get("PYTHONHASHSEED") == str(plan.config.run.seed), "Set the exact PYTHONHASHSEED before Python starts.")
        training_output = app.parent / plan.config.run.output_dir
        require(training_output.resolve() == training_output and not training_output.exists()
                and not training_output.is_symlink() and not training_output.is_relative_to(output)
                and not output.is_relative_to(training_output), "Fresh, separate, contained training output required.")
        save(output / "prepared-plan.json", plan.record)
        checker()
        features, tokens, tokenizer = decision_pilot.tokenize(plan, base_directory=args.base_directory, should_stop=stop)
        token_sha = sha256(canonical(tokens)).hexdigest()
        save(output / "token-preflight.json", tokens)
        save(output / "token-preflight-pin.json", {"sha256": token_sha, "hash_scope": "canonical JSON without trailing newline",
            "training_row_ids_sha256": plan.record["training_row_ids_sha256"],
            "validation_row_ids_sha256": plan.record["validation_row_ids_sha256"],
            "row_dropping_allowed": False, "primitive_schema": "primitive_v4"})
        del features, tokenizer
        require(not stop(), "Token admission used the remaining soft-stop budget.")
        checker()
        import torch
        require(torch.cuda.is_available() and torch.cuda.device_count() == 1 and torch.cuda.is_bf16_supported(),
                "Training needs exactly one BF16 CUDA device; no CPU fallback.")
        device = torch.cuda.get_device_properties(0)
        require(device.major == 9 and "GH200" in device.name, "Training device differs from the reviewed GH200 allocation.")
        torch.set_num_threads(8)
        save(output / "device.json", {"name": device.name, "major": device.major,
            "total_memory_bytes": device.total_memory, "cuda_device_count": 1, "dtype": "bfloat16"})
        progress = Progress(output, checker, plan.record["expected_optimizer_steps"])
        execute_started = True
        artifact = decision_pilot.execute(plan, base_directory=args.base_directory,
            expected_token_preflight_sha256=token_sha, reservation_check=checker, stop_requested=stop,
            progress=progress, stop_after_seconds=reservation["soft_limit_seconds"])
        disk = helpers.strict_json(ordinary(training_output / "manifest.json"))
        require(canonical(disk) == canonical(artifact), "Returned training artifact differs from the saved manifest.")
        from hydra_training_v5.peano_policy import manifest as artifact_manifest
        validate_artifact(artifact, plan.record, tokens, training_output, artifact_manifest)
        require(progress.last_optimizer_step == plan.record["expected_optimizer_steps"],
                "Observed optimizer callbacks do not cover the complete one-pass schedule.")
        returned = {"manifest_path": (training_output / "manifest.json").relative_to(app.parent).as_posix(),
            "manifest_sha256": digest(training_output / "manifest.json"),
            "actual_optimizer_steps": artifact["actual_optimizer_steps"],
            "adapter": artifact["adapter"], "tokenizer": artifact["tokenizer"],
            "finite_gradient_audit": artifact["finite_gradient_audit"], "adapter_update": artifact["adapter_update"],
            "base_identity_sha256": artifact["base"]["base_identity_sha256"],
            "saved_adapter_reload_admission": "required_by_P6_before_inference"}
        save(output / "artifact-receipt.json", returned)
        checker()
        completed = True
    except BaseException as failure:
        error = {"type": type(failure).__name__, "detail": str(failure)[:1500]}
    finally:
        if before_handlers:
            signal.alarm(0)
            for sig, handler in before_handlers.items():
                signal.signal(sig, handler)
        try:
            after = source_pins(app)
        except BaseException as failure:
            if error is None:
                error = {"type": type(failure).__name__, "detail": str(failure)[:1500]}
        unchanged = before == after
        completed = completed and unchanged and error is None
        summary = {"schema": "hydra-p6-remote-training-completion-v1", "completed": completed,
            "error": error, "source_pins_after": after, "sources_unchanged": unchanged,
            "elapsed_controller_seconds": time.monotonic() - began, "reservation_claimed": claim is not None,
            "last_live_allocation": checker.last, "scheduler_calls": checker.calls,
            "execute_invoked": execute_started, "optimizer_steps_observed": 0 if progress is None else progress.last_optimizer_step,
            "optimizer_step_observation_caveat": "On failure, callbacks are a lower bound; a step can finish before a stop interrupts its callback.",
            "actual_optimizer_steps_in_complete_artifact": None if returned is None else returned["actual_optimizer_steps"],
            "training_artifact": returned, "model_reload_performed": False, "quality_evaluated": False,
            "model_inference_calls": 0, "native_proof_searches": 0, "native_proof_replays": 0, "solver_calls": 0,
            "campaign_ledger_enforced_by": "root_job_orchestrator", "automatic_retry": False, "resume": False,
            "cleanup_scope": "No controller-owned model/helper subprocess; exact Slurm hard limits and final process reaping are observed externally.",
            "limit_caveat": "Soft checks/signals cannot interrupt a blocked GPU operation instantaneously; Slurm owns the hard wall/memory bounds."}
        save(output / "completion.json", summary)
        evidence = [path for path in output.rglob("*") if path.is_file()]
        require(len(evidence) <= 32 and sum(path.stat().st_size for path in evidence) <= MAX_EVIDENCE_BYTES,
                "Controller evidence exceeded its finite file/byte ceiling.")
        print(json.dumps({key: summary[key] for key in ("completed", "elapsed_controller_seconds", "sources_unchanged",
            "execute_invoked", "optimizer_steps_observed", "error")}), flush=True)
    return 0 if completed else 1


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--reservation", type=Path, required=True)
    parser.add_argument("--reservation-sha256", required=True)
    parser.add_argument("--model-key", choices=tuple(MODELS), required=True)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--dataset-manifest", type=Path, required=True)
    parser.add_argument("--base-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        return run(args)
    except BaseException as error:
        print(json.dumps({"status": "failed", "error_type": type(error).__name__, "error": str(error)[:1500],
                          "automatic_retry": False, "resume": False}), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
