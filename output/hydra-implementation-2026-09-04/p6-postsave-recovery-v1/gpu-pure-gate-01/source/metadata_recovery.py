"""CPU-only, single-artifact recovery admission; never repairs old job evidence.

Run on Helios in a fresh Python >=3.11 process, under the caller's finite CPU
guard (this CLI also enforces 90 CPU / 120 wall seconds / 2 GiB address space):

  python3 -B metadata_recovery.py --source-root ORIGINAL_SOURCE07 \
    --job-directory ORIGINAL_JOB21912020 --observation observation013.json \
    --transport observation013-transport.json --output metadata-recovery.json

The two observation files must be the exact collected observation-013 bytes.
Output belongs in CAMPAIGN/recovery/p6-postsave-recovery-v1 and must not exist.
The sibling *.prepared-plan.json is a new recovery artifact, not a replacement
for the original prepared plan. Full data regeneration parses formulas for the
existing exclusions; it executes no native proof, tokenizer, model or optimizer.
Only a subsequent, independently observed GPU reload can admit the saved tensors.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import signal
import stat
import sys
import time

SCHEMA = "hydra-p6-postsave-metadata-recovery-v1"
JOB_ID = "21912020"
MODEL_KEY = "qwen3-1.7b-base"
CAMPAIGN = Path("/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904")
SOURCE = CAMPAIGN / "bundles/source-data-07/source"
JOB = CAMPAIGN / "jobs/p6-training-fresh-1.7b-v2-01"
DESTINATION = CAMPAIGN / "recovery/p6-postsave-recovery-v1"
BASE = CAMPAIGN / "authenticated-bases-01/qwen3-1.7b-base"
ARTIFACT_REL = "output/hydra-implementation-2026-09-04/training-fresh-1.7b-v2-01"
CONFIG_REL = "hydra-playground/training-v5/configs/qwen3_1_7b_decisions_v2_pilot.toml"
DATA_REL = "output/hydra-implementation-2026-09-04/decisions-v2-01/manifest.json"
PROVIDER_SHA = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
CONTROLLER_SHA = "41b97e63f09571071a75e1f1b01c6df8ab173783f596bc6ee1c3f3b0fab3c617"
SOURCE_SHA = "11aa82af08bce4369747ddc153a8d0b334243f69d497b16267a7151d0b62513c"
MANIFEST_SHA = "3799c7d3212885667cd28f7ba6e9d8f9ffcd12bc90bd7d03d031b96a7325f135"
PLAN_SHA = "3ec6e96c39d3294671d61018431614ce02bff5b0874431e5883473cbb1cd5816"
CONFIG_SHA = "807933e5625536fc2b6412e680010d1534cac7e94156e284ae3e63e87a047e27"
DATA_SHA = "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"
BASE_SHA = "43ab517189660cd7319ab05c46d6c91f90150d2c4a42c942a16ff7cb804329f2"
TENSOR_SHA = "2499801811ee63fb4f6c20e022d59aa0eeb2bb202ee41c9edd6bcd271e646c3c"
OBSERVATION_SHA = "a1d56e0e322a8b3f49d2ecd51da21309efe3ccc6cd091c3482edebef10375923"
TRANSPORT_SHA = "ac2b0deec46aaac68a7fc0405b6d28acab8c8157b0b45c95a0b52ac55b388269"
RESERVATION_SHA = "aeb6cf3ed851d9b3f08a1792451ad477f635d195f6b1e8842a5246527204cf80"
TOKEN_SHA = "2e6bb1f5188de33f515dfa47c08581c044d708b0d6e47611ff6760492623c024"
FAILURE = {"type": "ValueError", "detail": "Returned training artifact differs from the saved manifest."}
MAX_JSON = 2 * 1024**2
FORBIDDEN = {"torch", "transformers", "peft", "mlx", "jax", "tensorflow", "tokenizers", "safetensors"}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def decode(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key.")
            result[key] = value
        return result
    def constant(value):
        raise ValueError("Non-finite JSON constant: " + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def ordinary_path(value, *, directory=False):
    path = Path(value).absolute()
    require(path.resolve(strict=True) == path, "An ordinary path without symlink traversal is required.")
    info = path.lstat()
    require((stat.S_ISDIR(info.st_mode) if directory else stat.S_ISREG(info.st_mode)),
            "Unexpected file type.")
    if not directory:
        require(info.st_nlink == 1, "Metadata/source hard links are not admitted.")
    return path


def read(path, maximum=MAX_JSON, expected=None):
    path = ordinary_path(path)
    with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW), "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and 0 < before.st_size <= maximum, "File exceeds its ordinary bounded read.")
        raw = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    fields = lambda x: (x.st_dev, x.st_ino, x.st_mode, x.st_nlink, x.st_size, x.st_mtime_ns, x.st_ctime_ns)
    require(len(raw) == before.st_size and fields(before) == fields(after) == fields(path.lstat()),
            "File changed during its read.")
    descriptor = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    require(expected is None or descriptor["sha256"] == expected, "Exact file pin differs: " + path.name)
    return raw, descriptor


def relative(root, name):
    require(type(name) is str and not Path(name).is_absolute() and ".." not in Path(name).parts
            and Path(name).as_posix() == name, "Unsafe relative input path.")
    return ordinary_path(root / name)


def save(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= MAX_JSON, "Recovery output exceeds 2 MiB.")
    with Path(path).open("xb") as stream:
        stream.write(raw)
    return {"path": str(path), "bytes": len(raw), "sha256": sha256(raw).hexdigest()}


def validate_failed_job(observation, transport, completion, request, process_exit):
    require(transport.get("actual_ssh_exit_code") == 0 and transport.get("owned_child_reaped") is True
            and transport.get("output_complete") is True and transport.get("stop_reason") is None
            and transport.get("automatic_retry") is False, "Original collection transport is incomplete.")
    require(observation.get("job_id") == JOB_ID and observation.get("read_only") is True,
            "Recovery is only for the exact original observed job.")
    sacct = observation["scheduler"]["sacct"]
    require(sacct.get("actual_exit_code") == 0 and sacct.get("executed") is True
            and sacct.get("owned_child_reaped") is True and sacct.get("stop_reason") is None,
            "Original accounting query did not finish normally.")
    rows = [line.split("|") for line in sacct["stdout_stderr"].splitlines()
            if line.split("|", 1)[0] == JOB_ID]
    require(len(rows) == 1 and len(rows[0]) == 14, "Missing unambiguous original allocation row.")
    row = rows[0]
    require(row[1:10] == ["hydra-p6-training-fresh-1.7b-v2-01", "plgnasqret",
            "plgccaiautore2026-gpu-gh200", "plgrid-gpu-gh200", "FAILED", "1:0", "916", "20", "8"]
            and row[10] == "64G" and row[13] == "x1002c0s3b0n0", "Original failed allocation differs.")
    for text in (row[11], row[12]):
        require(text == "billing=1,cpu=8,gres/gpu=1,mem=64G,node=1", "Original TRES changed.")
    require(process_exit == b"1\n", "The original failed process must remain exit 1.")
    require(completion.get("schema") == "hydra-p6-remote-training-completion-v1"
            and completion.get("completed") is False and completion.get("error") == FAILURE
            and completion.get("execute_invoked") is True and completion.get("reservation_claimed") is True
            and completion.get("optimizer_steps_observed") == 256
            and completion.get("actual_optimizer_steps_in_complete_artifact") is None
            and completion.get("training_artifact") is None and completion.get("model_reload_performed") is False
            and completion.get("sources_unchanged") is True
            and completion.get("automatic_retry") is False and completion.get("resume") is False,
            "Only the diagnosed post-save serialization failure is eligible.")
    require(all(completion.get(k) == 0 for k in ("model_inference_calls", "native_proof_searches",
            "native_proof_replays", "solver_calls")), "The original attempt exceeded its training-only scope.")
    require(request["source_pins_before"] == completion["source_pins_after"]
            and sha256(canonical(request["source_pins_before"])).hexdigest() == SOURCE_SHA,
            "Original executed source scope differs.")
    return {"original_process_exit_code": 1, "original_slurm_state": "FAILED",
            "original_slurm_exit_code": "1:0", "original_controller_completed": False,
            "original_failure": FAILURE, "original_allocated_seconds": 1200,
            "original_elapsed_seconds": 916, "original_charge_refunded": False}


def validate_progress(raw, artifact):
    lines = raw.splitlines()
    require(len(raw) <= MAX_JSON and len(lines) == 259, "Exact complete progress sequence is required.")
    rows = [decode(line) for line in lines]
    kinds = ["loading-model", "training-start"] + ["optimizer-step"] * 256 + ["training-complete"]
    previous = -1.0
    for index, (row, kind) in enumerate(zip(rows, kinds), 1):
        elapsed = row.get("elapsed_seconds")
        require(type(row.get("event")) is int and row["event"] == index and row.get("kind") == kind
                and type(elapsed) in (int, float) and math.isfinite(elapsed)
                and previous <= elapsed < 1140, "Progress was reordered, omitted or exceeded the allocation.")
        previous = elapsed
    require(rows[0]["model"] == artifact["model"] and rows[1].get("rows") == 2047
            and rows[1].get("expected_optimizer_steps") == 256
            and [row.get("step") for row in rows[2:-1]] == list(range(1, 257))
            and rows[-1].get("optimizer_steps") == artifact.get("actual_optimizer_steps") == 256,
            "All 256 actual callbacks and the final saved-training event are required.")
    return {"events": 259, "optimizer_steps": 256, "training_complete_event": True,
            "elapsed_callback_seconds": rows[-1]["elapsed_seconds"]}


def normalized_plan(regenerated, recorded, saved):
    """JSON is the declared plan contract; only representation is normalized."""
    require(canonical(regenerated) == canonical(recorded) == canonical(saved),
            "Regenerated full JSON plan differs from the original saved plan.")
    result = decode(canonical(regenerated))
    require(result["plan_sha256"] == PLAN_SHA
            and sha256(canonical({k: v for k, v in result.items() if k != "plan_sha256"})).hexdigest() == PLAN_SHA,
            "Regenerated canonical plan identity differs.")
    return result


def load_module(name, path):
    require(name not in sys.modules, "A fresh metadata process is required.")
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def prohibit_runtime(event, args):
    if event == "import":
        require(args[0].split(".", 1)[0] not in FORBIDDEN, "Framework/tokenizer loading is forbidden in metadata recovery.")
    require(not (event.startswith("socket.") or event in {"subprocess.Popen", "os.system", "os.exec", "os.posix_spawn"}),
            "Metadata recovery cannot launch a process or use the network.")


def run(args):
    started = time.monotonic()
    root, job = ordinary_path(args.source_root, directory=True), ordinary_path(args.job_directory, directory=True)
    require(root == SOURCE and job == JOB and sys.platform == "linux" and os.getuid() == 105923,
            "Only the actual owned Helios source07/job21912020 is admitted.")
    output = Path(args.output).absolute()
    require(ordinary_path(output.parent, directory=True) == DESTINATION
            and re.fullmatch(r"[A-Za-z0-9_-]{1,80}\.json", output.name)
            and not os.path.lexists(output), "A fresh recovery output in the fixed recovery directory is required.")
    plan_output = output.with_name(output.stem + ".prepared-plan.json")
    failure_output = output.with_name(output.stem + ".admission-failure")
    require(not os.path.lexists(plan_output) and not os.path.lexists(failure_output), "Recovery evidence already exists.")
    _, own_pin = read(__file__, 128 * 1024)
    report = {"schema": SCHEMA, "passed": False, "eligible_for_saved_reload": False,
        "saved_adapter_reload_required": True, "model_loaded": False, "job_id": JOB_ID,
        "source_root": str(root), "source_pins_sha256": SOURCE_SHA, "provider_sha256": PROVIDER_SHA,
        "manifest_sha256": MANIFEST_SHA, "artifact_directory": str(root / ARTIFACT_REL),
        "base_directory": str(BASE), "final_tensor_population_sha256": TENSOR_SHA, "plan_sha256": PLAN_SHA,
        "metadata_source_sha256": own_pin["sha256"], "sources_unchanged": False, "errors": [],
        "original_process_exit_code": None, "original_slurm_state": None, "original_slurm_exit_code": None,
        "original_controller_completed": None, "automatic_retry": False, "resume": False,
        "model_calls": 0, "optimizer_updates": 0, "native_proof_searches": 0, "native_proof_replays": 0,
        "tokenization_performed": False, "quality_evaluated": False, "inputs": {}}
    try:
        raw_obs, obs_pin = read(args.observation, 65536, OBSERVATION_SHA)
        raw_transport, transport_pin = read(args.transport, 65536, TRANSPORT_SHA)
        observation, transport = decode(raw_obs), decode(raw_transport)
        report["inputs"].update(observation={"path": str(Path(args.observation).absolute()), **obs_pin},
                                transport={"path": str(Path(args.transport).absolute()), **transport_pin})
        require(type(observation.get("files")) is dict and 1 <= len(observation["files"]) <= 24,
                "Original observed file population differs.")
        records = {}
        for name, expected in observation["files"].items():
            require(expected.get("complete_file") is True and expected.get("stable") is True
                    and expected.get("offset") == 0
                    and expected["bytes"] == expected["file_bytes_before"] == expected["file_bytes_after"],
                    "A partial or unstable original observation cannot support recovery.")
            if name.startswith("job/"):
                path = relative(job, name[4:])
            else:
                require(name == "artifact/manifest.json", "Unexpected non-job evidence.")
                path = relative(root, ARTIFACT_REL + "/manifest.json")
            raw, descriptor = read(path, expected=expected["sha256"])
            require(descriptor["bytes"] == expected["bytes"], "Original evidence size changed.")
            report["inputs"][name] = {"path": str(path), **descriptor}
            records[name] = decode(raw) if name.endswith(".json") or name.endswith(".claimed") else raw
        request, completion, reservation = (records["job/result/request.json"], records["job/result/completion.json"], records["job/reservation.json"])
        artifact, tokens = records["artifact/manifest.json"], records["job/result/token-preflight.json"]
        report.update(validate_failed_job(observation, transport, completion, request, records["job/actual-process-exit.txt"]))
        require(report["inputs"]["job/reservation.json"]["sha256"] == RESERVATION_SHA
                and request["reservation"] == reservation and request["reservation_sha256"] == RESERVATION_SHA
                and reservation["controller_sha256"] == CONTROLLER_SHA
                and reservation["source_pins_sha256"] == SOURCE_SHA and reservation["plan_sha256"] == PLAN_SHA,
                "Original reservation/source/plan binding differs.")
        claim = records["job/reservation.json.claimed"]
        require(claim["job_id"] == JOB_ID and claim["nonce"] == reservation["nonce"]
                and claim["reservation_sha256"] == RESERVATION_SHA and claim["plan_sha256"] == PLAN_SHA
                and claim["output"] == str(job / "result") and request["claimed"] == str(job / "reservation.json.claimed"),
                "Original consumed reservation changed.")
        require(request["config"] == CONFIG_REL and request["dataset_manifest"] == DATA_REL
                and request["base_directory"] == str(BASE), "Recovery cannot substitute training paths.")
        require(not os.path.lexists(root / ARTIFACT_REL / "incomplete.json")
                and not os.path.lexists(job / "result/artifact-receipt.json"),
                "An incomplete marker or retroactive original completion receipt is not admissible.")
        report["progress"] = validate_progress(records["job/result/progress.jsonl"], artifact)
        require(report["inputs"]["artifact/manifest.json"]["sha256"] == MANIFEST_SHA
                and artifact["adapter_update"]["final_tensor_population_sha256"] == TENSOR_SHA,
                "Saved artifact is not this exact diagnosed candidate.")
        app = ordinary_path(root / "hydra-playground", directory=True)
        for name, expected in request["source_pins_before"].items():
            _, actual = read(relative(root, name), 4 * 1024**2, expected["sha256"])
            require(actual == expected, "Original source size differs.")
        read(relative(root, "output/p6-prototype/remote_training_pilot.py"), expected=CONTROLLER_SHA)
        read(app / "experimental_model.py", expected=PROVIDER_SHA)
        for relative_name, expected in ((CONFIG_REL, CONFIG_SHA), (DATA_REL, DATA_SHA)):
            _, descriptor = read(relative(root, relative_name), expected=expected)
            report["inputs"][relative_name] = {"path": str(root / relative_name), **descriptor}
        require(not any(name.split(".", 1)[0] in FORBIDDEN or name.split(".", 1)[0] in
                        {"peano_lab", "hydra_training_v5", "experimental_model"} for name in sys.modules),
                "Use a fresh process with no imported native/framework/training modules.")
        sys.addaudithook(prohibit_runtime)
        os.chdir(root)
        sys.path[:0] = [str(app), str(app / "native-v7"), str(app / "training-v5")]
        os.environ.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", PYTHONDONTWRITEBYTECODE="1")
        sys.dont_write_bytecode = True
        controller = load_module("hydra_postsave_original_controller", root / "output/p6-prototype/remote_training_pilot.py")
        before = controller.source_pins(app)
        require(before == request["source_pins_before"] and len(before) == 585, "Complete original source inventory differs.")
        pilot = importlib.import_module("hydra_training_v5.decision_pilot")
        require(Path(pilot.__file__).resolve() == app / "training-v5/hydra_training_v5/decision_pilot.py",
                "Unexpected preparation module path.")
        plan = pilot.prepare(root / CONFIG_REL, dataset_manifest=DATA_REL, dataset_sha256=DATA_SHA,
                             failure_output=failure_output)
        normalized = normalized_plan(plan.record, records["job/result/prepared-plan.json"], artifact["plan"])
        controller.validate_plan(plan.record, reservation)
        require(artifact["model"] == normalized["model"] and artifact["objective"] == normalized["objective"]
                and artifact["training_metrics"].get("epoch") == artifact["validation_metrics"].get("epoch") == 1.0
                and all(type(value) in (int, float) and math.isfinite(value)
                        for group in (artifact["training_metrics"], artifact["validation_metrics"])
                        for value in group.values()), "Saved completed training/validation/objective metadata differs.")
        require(sha256(canonical(tokens)).hexdigest() == TOKEN_SHA
                and records["job/result/token-preflight-pin.json"]["sha256"] == TOKEN_SHA
                and tokens == artifact["token_preflight"] and tokens["plan_sha256"] == PLAN_SHA
                and tokens["rows_dropped"] == 0 and tokens["state_truncation"] is False
                and tokens["training_row_ids_sha256"] == normalized["training_row_ids_sha256"]
                and tokens["validation_row_ids_sha256"] == normalized["validation_row_ids_sha256"]
                and tokens["splits"]["train"]["rows"] == 2047 and tokens["splits"]["val"]["rows"] == 432,
                "Recorded token/exposure admission differs; no retokenization is performed here.")
        provider = importlib.import_module("experimental_model")
        require(Path(provider.__file__).resolve() == app / "experimental_model.py", "Unexpected provider module path.")
        runtime = records["job/result/runtime.json"]
        require(runtime["dependencies"] == provider.registry()["dependencies"]
                and artifact["frameworks"] == {k: runtime["dependencies"][k] for k in ("torch", "transformers")},
                "Recorded actual training dependencies differ from the pinned provider contract.")
        stop = lambda: time.monotonic() - started >= 120
        base = provider.authenticate_base(MODEL_KEY, BASE, should_stop=stop)
        require(base == artifact["base"] == tokens["base"] and base["base_identity_sha256"] == BASE_SHA,
                "Actual Base files differ from training/token admission.")
        manifest_module = importlib.import_module("hydra_training_v5.peano_policy.manifest")
        # The original checker is retained; its plan argument is explicitly the
        # complete canonical JSON representation, never a field-filtered plan.
        controller.validate_artifact(artifact, normalized, tokens, root / ARTIFACT_REL, manifest_module)
        admitted, paths, watched, header = provider._adapter(root / ARTIFACT_REL, MANIFEST_SHA,
            provider.model_spec(MODEL_KEY), stop, "fresh_decision_pilot")
        require(admitted == artifact and artifact["finite_gradient_audit"]["observed_optimizer_boundaries"] == 256
                and artifact["adapter_update"]["trainable_parameter_tensors"] == 392
                and artifact["adapter_update"]["changed_parameter_tensors"] == 392,
                "Saved finite/update evidence differs from the expected matrix population.")
        pilot._refresh(plan)
        provider._unchanged(watched)
        require(controller.source_pins(app) == before, "Executed recovery inputs changed.")
        for item in report["inputs"].values():
            _, descriptor = read(item["path"], expected=item["sha256"])
            require(descriptor["bytes"] == item["bytes"], "Original evidence changed during recovery.")
        read(__file__, 128 * 1024, own_pin["sha256"])
        report.update(sources_unchanged=True, source_files_verified=585,
            prepared_plan=save(plan_output, normalized),
            plan_canonical_json_equal=True, data_attestation=normalized["data_attestation"],
            formula_parsing_performed_by_data_admission=True,
            native_replays_repeated_by_data_admission=False,
            base=base, adapter=artifact["adapter"], tokenizer=artifact["tokenizer"],
            safetensors_header=header, finite_gradient_boundaries=256,
            changed_parameter_tensors=392, actual_saved_file_hashes_checked=True,
            training_metrics=artifact["training_metrics"], validation_metrics=artifact["validation_metrics"],
            tokenizer_semantic_reload_pending=True, tensor_population_reload_pending=True,
            source_pins=before, passed=True, eligible_for_saved_reload=True)
    except Exception as failure:
        report["errors"].append({"type": type(failure).__name__, "detail": str(failure)[:1600]})
    report["elapsed_seconds"] = time.monotonic() - started
    save(output, report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-root", "job-directory", "observation", "transport", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args(argv)
    require(sys.platform == "linux" and sys.version_info >= (3, 11), "This bounded recovery CLI requires Linux Python >=3.11.")
    import resource
    for kind, ceiling in ((resource.RLIMIT_CPU, 90), (resource.RLIMIT_AS, 2 * 1024**3),
                          (resource.RLIMIT_FSIZE, 128 * 1024**2)):
        soft, hard = resource.getrlimit(kind)
        limit = ceiling if hard == resource.RLIM_INFINITY else min(ceiling, hard)
        resource.setrlimit(kind, (min(limit, soft) if soft != resource.RLIM_INFINITY else limit, hard))
    def stop(signum, frame):
        raise TimeoutError("Metadata recovery reached its finite wall/CPU/termination bound.")
    for sig in (signal.SIGALRM, signal.SIGXCPU, signal.SIGTERM, signal.SIGINT):
        signal.signal(sig, stop)
    signal.alarm(120)
    try:
        report = run(args)
    finally:
        signal.alarm(0)
    print(json.dumps({k: report[k] for k in ("schema", "passed", "eligible_for_saved_reload", "elapsed_seconds", "errors")}))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
