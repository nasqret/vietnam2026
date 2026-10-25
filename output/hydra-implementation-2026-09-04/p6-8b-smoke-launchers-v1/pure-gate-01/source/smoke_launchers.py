"""Prepare, submit held, release, or collect ONE fixed 8B base-model smoke.

All real operations are explicit phases; importing this module is inert.
No training duration, model, adapter, retry, or automatic next phase is exposed.
The two completed pilot collections are re-admitted before submission/release.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import secrets
import select
import shlex
import subprocess
import sys
import time

import remote_smoke_control as control

HERE = Path(__file__).resolve().parent
ROOT, BASE = HERE.parents[2], HERE.parent
CAMPAIGN_FILE = BASE / "campaign.json"
BUNDLE = BASE / "p6-source-bundle-06"
BUNDLE_MANIFEST_SHA = "e1f5518231eaa04469d39c830bd480ec11ff4ed891907772d48aeab67da18f96"
BUNDLE_SEAL_SHA = "fe2b602d75c6e2c9a3227bdfc7783717ea6cc546407b1614211322f17071e79b"
LOGIN_PYTHON = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3"
LOGIN_PYTHON_LIB = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib"
SSH = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
    "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
    "-o", "ClearAllForwardings=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
    "-o", "ControlMaster=no", "-o", "ControlPath=none", "--", "plgnasqret@helios.cyfronet.pl"]
TRAINING_PINS = {"training_launchers.py": "966552cff6a91253b97fdc6df39ef8ed975d29fac306038af30defc5a49a5329",
    "remote_training_control.py": "7c87dda334901f464cd63413fc394b4808485dd57e0449634daae9f3f4e7fb62"}
BASE_ADMISSION_SHA = "526d09a8da89e370d01fb3f0a3c902856a5c62f133e79c89e94226a3f538e3d4"
TRANSFER_SHA = "6139660d6a10d4c27878f32617c7a4f2d8df7e82acbfd9fcc240c9afbe3fc5e8"
require, canonical, digest = control.require, control.canonical, control.digest


def validate_choice(choice):
    require(type(choice) is dict and set(choice) == {"schema", "pilots"}
            and choice["schema"] == "hydra-p6-8b-smoke-evidence-choice-v1"
            and type(choice["pilots"]) is dict and set(choice["pilots"]) == set(control.PILOTS),
            "Exactly both completed fresh pilot evidence sets are required; no launch overrides.")


def admit_pilot(model, descriptors, reader, manifest, expected_base):
    require(model in control.PILOTS and type(descriptors) is dict
            and set(descriptors) == {"response", "transport", "actual_completion"},
            "Actual completed fresh training evidence is missing.")
    actual_completion(json.loads(evidence(descriptors["actual_completion"])))
    transport = json.loads(evidence(descriptors["transport"]))
    require(transport.get("actual_ssh_exit_code") == 0 and transport.get("owned_child_reaped") is True
            and transport.get("stop_reason") is None
            and transport.get("remote_script_sha256") == TRAINING_PINS["remote_training_control.py"],
            "The pinned training collection transport did not complete.")
    response = json.loads(evidence(descriptors["response"]))
    require(response.get("schema") == "hydra-p6-training-control-phase-v1" and response.get("phase") == "collect"
            and response.get("completed") is True and response.get("error") is None, "Incomplete training collection.")
    observation = response["result"]
    validate_observation(observation, allowed=reader.control.FILES)
    request = reader.complete_json(observation, "job/result/request.json")
    require(type(request) is dict and type(request.get("reservation")) is dict, "Missing actual training reservation.")
    record = request["reservation"]
    require(record.get("model_key") == model and type(record.get("uid")) is int and record["uid"] == control.UID
            and observation.get("job_id") == record.get("job_id"), "Wrong pilot owner, model or job.")
    choice = {"schema": "hydra-p6-training-allocation-choice-v1", "model_key": model,
        "seconds": record["seconds"], "soft_limit_seconds": record["soft_limit_seconds"],
        "throughput": {}, "transfer_receipt": {}, "base_admission": {}}
    spec = reader.make_spec(choice, record["nonce"], digest(canonical(manifest)))
    require(record == reader.control.reservation(spec, record["job_id"], control.UID), "Pilot is not the fixed fresh run.")
    summary = reader.summarize(observation, spec, record, expected_base_identity=expected_base)
    require(summary.get("status") == "complete_saved_artifact_metadata_requires_fresh_reload"
            and summary.get("saved_artifact_metadata_complete") is True,
            "Prior pilot has not completed: " + str(summary.get("errors"))[:1000])
    return {"job_id": record["job_id"], "seconds": record["seconds"],
        "reservation_sha256": digest(canonical(record) + b"\n"),
        "manifest_sha256": observation["files"]["artifact/manifest.json"]["sha256"],
        "completion_sha256": observation["files"]["job/result/completion.json"]["sha256"],
        "request_sha256": observation["files"]["job/result/request.json"]["sha256"],
        "base_identity_sha256": expected_base}


def prerequisites(choice, manifest):
    validate_choice(choice)
    cpu = json.loads(read(BASE / "p6-cpu-prerequisite-01.json", control.CPU_SHA, 65536))
    require(cpu.get("schema") == "hydra-p6-actual-cpu-prerequisite-v1" and cpu.get("completed") is True
            and cpu.get("scheduler_helper_sha256") == control.SMOKE_SHA
            and all(cpu.get(key) is True for key in ("positive_proof_replayed", "negative_probe_rejected", "owned_cleanup_verified"))
            and all(cpu.get(key) == 0 for key in ("actual_process_exit_code", "actual_scheduler_query_exit_code", "actual_collector_tool_exit_code"))
            and cpu.get("actual_scheduler_state") == "COMPLETED" and cpu.get("actual_scheduler_exit") == "0:0"
            and type(cpu.get("actual_collector_completion_chunk")) is str and cpu["actual_collector_completion_chunk"],
            "Actual CPU/scheduler prerequisite is incomplete.")
    require(type(cpu.get("evidence_files")) is dict and 3 <= len(cpu["evidence_files"]) <= 16, "Missing CPU evidence scope.")
    total = 0
    for name, identity in cpu["evidence_files"].items():
        relative = Path(name)
        require(not relative.is_absolute() and ".." not in relative.parts, "CPU evidence path escapes.")
        total += len(read(BASE / relative, identity))
        require(total <= 32 * 1024**2, "CPU evidence scope exceeds its finite bound.")
    transfer = json.loads(read(BASE / "p6-transfer-06/actual-completion.json", TRANSFER_SHA))
    require(transfer.get("actual_ssh_exit_code") == 0 and transfer.get("archive_sha256") == control.ARCHIVE_SHA
            and transfer.get("archive_bytes") == 10257464
            and transfer.get("remote_directory") == str(Path(control.SOURCE).parent), "Source-data-07 transfer is not complete.")
    base = json.loads(read(BASE / "p6-clean-base-admission-01/stdout.jsonl", BASE_ADMISSION_SHA).rstrip().splitlines()[-1])
    require(base.get("completed") is True
            and base["models"][control.MODEL_KEY]["identity"]["base_identity_sha256"] == control.BASE_SHA,
            "The exact 8B base admission is missing.")
    reader = training_reader()
    result = {model: admit_pilot(model, choice["pilots"][model], reader, manifest,
        base["models"][model]["identity"]["base_identity_sha256"]) for model in control.PILOTS}
    control.validate_pilots(result)
    return result


def charge_records():
    patterns = ("p6-training-launchers-v*/attempts/*/release/charge-intent.json",
        "paired-launchers-v*/prepared/arms/*/release/charge-intent.json",
        "p7-teacher-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-8b-smoke-launchers-v*/attempts/*/release/charge-intent.json")
    paths = sorted({path for pattern in patterns for path in BASE.glob(pattern)})
    require(len(paths) <= 16, "Unexpected cross-family release history.")
    return [json.loads(read(path, limit=65536)) for path in paths]


def current_ledger(expected, pilots):
    raw = read(CAMPAIGN_FILE, expected, 2 * 1024**2)
    ledger = json.loads(raw)
    total = ledger_seconds(ledger)
    check_charges(ledger, charge_records())
    rows = {row["attempt"]: row for row in ledger["gpu_reservations"]}
    require(control.ATTEMPT not in rows, "The new attempt is already registered; no repeat or retry.")
    for model, (attempt, _) in control.PILOTS.items():
        pilot, row = pilots[model], rows.get(attempt, {})
        require(all(row.get(key) == pilot[key] for key in ("job_id", "seconds", "reservation_sha256"))
                and row.get("allocated_seconds") == pilot["seconds"] and row.get("gpus") == 1,
                "Prior completed pilot has not been fully reconciled into the current campaign ledger.")
    require(total + 600 <= 21600, "The fixed smoke exceeds the remaining six-GPU-hour budget.")
    return ledger, raw, total


def prepare(args):
    choice_raw = read(Path(args.choice).resolve(), args.choice_sha256, 65536)
    choice = json.loads(choice_raw)
    manifest, launch, source_map = bundle_inputs()
    pilots = prerequisites(choice, manifest)
    ledger, ledger_raw, used = current_ledger(args.ledger_sha256, pilots)
    row = launch["models"][control.MODEL_KEY]
    require(row["model"] == control.MODEL and row["config_sha256"] == control.CONFIG_SHA
            and row["plan_sha256"] == control.PLAN_SHA and row["training_rows"] == 2047
            and row["expected_optimizer_steps"] == 256, "8B probe plan differs from frozen metadata.")
    read(ROOT / row["prepared_plan"]["path"], row["prepared_plan"]["sha256"])
    spec = {**control.fixed_spec_fields(), "nonce": secrets.token_hex(16),
        "manifest_content_sha256": digest(canonical(manifest)), "pilot_evidence": pilots}
    control.validate_spec(spec)
    directory = HERE / "attempts" / control.ATTEMPT
    directory.mkdir(parents=True, exist_ok=False)
    put(directory / "choice.json", choice)
    put(directory / "source-map.json", source_map)
    put(directory / "prepare-ledger.json", ledger)
    prepared = {"schema": "hydra-p6-prepared-8b-smoke-v1", "status": "prepared_not_submitted",
        "spec": spec, "choice": file_pin(directory / "choice.json"), "original_choice_sha256": digest(choice_raw),
        "launcher_sources": {name: file_pin(HERE / name) for name in ("smoke_launchers.py", "remote_smoke_control.py")},
        "ledger_read_sha256": digest(ledger_raw), "full_seconds_before": used, "full_seconds_after_potential_release": used + 600,
        "training_steps_selected": None, "new_optimizer_updates": 0, "automatic_retry": False, "automatic_launch": False}
    put(directory / "prepared.json", prepared)
    with (directory / "job.sbatch").open("x") as stream:
        stream.write(control.job_script(spec))
    (directory / "job.sbatch").chmod(0o444)
    print(json.dumps({"prepared": file_pin(directory / "prepared.json"), "model_key": control.MODEL_KEY,
        "seconds": 600, "ssh_calls": 0, "allocations": 0, "automatic_next_phase": False}))


def load_prepared(expected, *, recheck_pilots):
    directory = HERE / "attempts" / control.ATTEMPT
    prepared = json.loads(read(directory / "prepared.json", expected))
    require(prepared.get("schema") == "hydra-p6-prepared-8b-smoke-v1", "Wrong preparation schema.")
    spec = control.validate_spec(prepared["spec"])
    for name in ("smoke_launchers.py", "remote_smoke_control.py"):
        require(file_pin(HERE / name) == prepared["launcher_sources"][name], "Launcher source changed since preparation.")
    choice = json.loads(read(directory / "choice.json", prepared["choice"]["sha256"]))
    manifest, _, source_map = bundle_inputs()
    require(digest(canonical(manifest)) == spec["manifest_content_sha256"]
            and json.loads(read(directory / "source-map.json")) == source_map
            and read(directory / "job.sbatch", limit=32768) == control.job_script(spec).encode(), "Prepared source/command changed.")
    if recheck_pilots:
        require(prerequisites(choice, manifest) == spec["pilot_evidence"], "Completed pilot inputs changed.")
    return directory, prepared, spec, source_map


def execute_phase(directory, payload):
    put(directory / "request.json", payload)
    output, receipt = ssh_once(payload)
    with (directory / "transport.stdout").open("xb") as stream:
        stream.write(output)
    (directory / "transport.stdout").chmod(0o444)
    put(directory / "transport-completion.json", receipt)
    require(receipt["actual_ssh_exit_code"] == 0 and receipt["owned_child_reaped"] is True
            and receipt["output_complete"] is True and receipt["stop_reason"] is None,
            "The single SSH attempt failed or is uncertain; preserve it and do not retry.")
    response = json.loads(output)
    require(response.get("schema") == "hydra-p6-8b-smoke-control-phase-v1" and response.get("completed") is True
            and response.get("phase") == payload["phase"] and response.get("error") is None,
            "Remote phase did not complete.")
    put(directory / "response.json", response)
    return response["result"]


def mutate_phase(args):
    directory, _, spec, source_map = load_prepared(args.prepared_sha256, recheck_pilots=True)
    ledger, ledger_raw, used = current_ledger(args.ledger_sha256, spec["pilot_evidence"])
    action = "submit" if args.action == "submit-held" else args.action
    require(action in {"submit", "release"}, "Only held submit or one release is allowed.")
    phase_dir = directory / action
    phase_dir.mkdir(exist_ok=False)
    put(phase_dir / "ledger-snapshot.json", ledger)
    payload = {"phase": action, "spec": spec, "source_map": source_map}
    if action == "release":
        receipt = json.loads(read(directory / "submit/transport-completion.json"))
        require(receipt.get("actual_ssh_exit_code") == 0 and receipt.get("owned_child_reaped") is True
                and receipt.get("output_complete") is True and receipt.get("stop_reason") is None,
                "Held submission transport did not complete.")
        submission = json.loads(read(directory / "submit/response.json"))["result"]
        require(submission["actual_sbatch_exit_code"] == 0 and submission["held"] is True
                and submission["released"] is False, "Exact held submission was not confirmed.")
        record = control.reservation(spec, submission["job_id"], submission["uid"])
        put(phase_dir / "reservation.json", record)
        # Charge is immutable BEFORE the only release SSH; uncertain release is not refunded.
        put(phase_dir / "charge-intent.json", {"schema": "hydra-p6-full-release-charge-v1", "attempt": control.ATTEMPT,
            "job_id": record["job_id"], "gpus": 1, "seconds": 600, "allocated_seconds": 600,
            "reservation_sha256": digest(canonical(record) + b"\n"), "status": "release_requested_or_uncertain",
            "ledger_before_sha256": digest(ledger_raw), "seconds_before": used, "seconds_after": used + 600,
            "refund_allowed_automatically": False, "automatic_retry": False})
        payload["reservation"] = record
    put(phase_dir / "phase-intent.json", {"action": action, "prepared_sha256": args.prepared_sha256,
        "ledger_sha256": digest(ledger_raw), "automatic_retry": False, "one_use": True})
    result = execute_phase(phase_dir, payload)
    print(json.dumps({"phase": action, "result": result, "campaign_file_modified": False, "next_phase_automatic": False}))


def validate_observation(observation, *, allowed=None):
    require(type(observation) is dict and observation.get("read_only") is True
            and type(observation.get("files")) is dict and set(observation["files"]) <= set(allowed or control.FILES),
            "Unexpected observation files.")
    total = 0
    for row in observation["files"].values():
        raw = control.base64.b64decode(row["base64"], validate=True)
        total += len(raw)
        require(type(row["bytes"]) is int and len(raw) == row["bytes"] and digest(raw) == row["sha256"]
                and len(raw) <= 2 * 1024**2 and total <= control.MAX_OBSERVATION, "Observation bytes differ or exceed limits.")


def expected_smoke_pins(source_map):
    names = {control.SMOKE, "hydra-playground/experimental_model.py", "hydra-playground/experimental-models/qwen3-base-v1.json",
        "hydra-playground/proof_planner.py", "hydra-playground/planner_provider.py", "hydra-playground/finite_difference.py",
        "hydra-playground/arithmetic_search.py", "hydra-playground/training-v5/BASELINE.json"}
    names.update(name for name in source_map if name.endswith(".py") and name.startswith((
        "hydra-playground/native-v7/peano_lab/", "hydra-playground/training-v5/hydra_training_v5/")))
    require(100 <= len(names) <= 1024 and names <= set(source_map), "The smoke source scope is incomplete.")
    return {name: source_map[name]["sha256"] for name in names}


def summarize(observation, spec, record, source_map):
    summary = {"status": "in_progress_or_incomplete_evidence", "job_id": record["job_id"],
        "transport_and_inference_complete": False, "gradient_probe_complete": False,
        "model_trained": False, "adapter_saved": False, "optimizer_updates": 0,
        "quality_evaluated": False, "proof_success_is_separate": True, "errors": []}
    try:
        validate_observation(observation)
        require(observation.get("job_id") == record["job_id"], "Wrong observed job.")
        completion = complete_json(observation, "job/result/completion.json")
        if completion:
            summary["observed_completion"] = {key: completion.get(key) for key in ("completed", "error", "elapsed_seconds", "sources_unchanged")}
            summary["observed_model_counters"] = {key: completion.get("session", {}).get(key) for key in
                ("actual_model_calls", "forward_passes", "generated_token_slots")}
        accounting = observation["scheduler"]["sacct"]
        require(accounting["actual_exit_code"] == 0 and accounting["stop_reason"] is None, "Actual accounting unavailable.")
        rows = [line.split("|") for line in accounting["stdout_stderr"].splitlines() if line.split("|", 1)[0] == record["job_id"]]
        require(len(rows) == 1 and len(rows[0]) == 14, "Exact allocation accounting is missing.")
        row = rows[0]
        require(row[1:5] == [spec["job_name"], control.REMOTE_USER, control.ACCOUNT, control.PARTITION], "Wrong accounting identity.")
        summary.update(slurm_state=row[5], slurm_exit_code=row[6], actual_scheduler_elapsed_seconds=row[7])
        if row[5] not in {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE"}:
            return summary
        summary["status"] = "terminal_failed_or_incomplete_evidence"
        require(row[5] == "COMPLETED" and row[6] == "0:0" and row[8] == "10" and row[9] == "8", "Smoke did not finish successfully in Slurm.")
        allocated = control.tres(row[12])
        require(allocated.get("cpu") == "8" and allocated.get("gres/gpu") == "1" and allocated.get("node") == "1"
                and allocated.get("mem") in {"64G", "65536M"}, "Allocated resources differ.")
        exit_row = observation["files"].get("job/actual-process-exit.txt", {})
        require(exit_row.get("complete_file") is True and exit_row.get("stable") is True
                and control.base64.b64decode(exit_row["base64"], validate=True).strip() == b"0", "Actual smoke process exit0 missing.")
        require(completion and completion.get("schema") == "hydra-p6-remote-smoke-completion-v1"
                and completion.get("completed") is True and completion.get("error") is None
                and completion.get("sources_unchanged") is True and completion.get("transport_and_inference_passed") is True
                and completion.get("optimizer_updates") == 0 and completion.get("model_trained_by_probe") is False
                and completion.get("automatic_retry") is False, "Smoke controller did not complete its no-update contract.")
        request = complete_json(observation, "job/result/request.json")
        require(request and request.get("schema") == "hydra-p6-remote-smoke-request-v1" and request.get("reservation") == record
                and request.get("reservation_sha256") == digest(canonical(record) + b"\n")
                and request.get("source_pins_before") == completion.get("source_pins_after") == expected_smoke_pins(source_map)
                and request.get("provider_sha256") == control.PROVIDER_SHA and request.get("base_directory") ==
                control.CAMPAIGN + "/authenticated-bases-01/" + control.MODEL_KEY
                and request.get("adapter_directory") is None and request.get("optional_throughput_examples") == 8,
                "Smoke input/source/model binding differs.")
        session, identity = completion.get("session", {}), complete_json(observation, "job/result/model-admission.json")
        require(identity and identity.get("schema") == "hydra-experimental-loaded-model-v1"
                and identity.get("profile") == "hydra-experimental-torch-qwen3-v2"
                and identity.get("model_id") == control.MODEL["model_id"] and identity.get("revision") == control.MODEL["revision"]
                and identity.get("source_sha256") == control.PROVIDER_SHA and identity.get("base_identity_sha256") == control.BASE_SHA
                and identity.get("model_loaded") is True and identity.get("adapter", {}).get("adapter_present") is False
                and identity.get("allocation", {}).get("job_id") == record["job_id"]
                and identity.get("model_manifest_sha256") == digest(canonical({key: value for key, value in identity.items() if key != "model_manifest_sha256"}))
                and session.get("identity") == identity and session.get("actual_model_calls") == 2
                and type(session.get("forward_passes")) is int and session["forward_passes"] >= 2
                and type(session.get("generated_token_slots")) is int and 0 <= session["generated_token_slots"] <= 512,
                "Actual loaded 8B identity or model counters differ.")
        primitive, planner = complete_json(observation, "job/result/primitive.json"), complete_json(observation, "job/result/planner.json")
        require(primitive and planner and primitive.get("actual_model_calls") == planner.get("actual_model_calls") == 1,
                "Two distinct actual primitive/planner calls are required.")
        summary["transport_and_inference_complete"] = True
        probe = complete_json(observation, "job/result/throughput.json")
        require(probe and probe.get("schema") == "hydra-completion-gradient-probe-v1" and probe.get("status") == "complete"
                and probe.get("model") == control.MODEL and probe.get("plan_sha256") == control.PLAN_SHA
                and probe.get("max_examples") == probe.get("examples_completed") == probe.get("forward_calls") == probe.get("backward_calls") == 8
                and probe.get("optimizer_steps") == 0 and probe.get("optimizer_created") is False
                and probe.get("finite_gradients") is True and probe.get("trainable_tensors_unchanged") is True
                and probe.get("model_trained") is False and probe.get("adapter_saved") is False,
                "The eight-example no-update gradient probe is incomplete.")
        summary.update(status="complete_base_provider_and_gradient_smoke", gradient_probe_complete=True,
            actual_model_calls=2, primitive_calls=1, planner_calls=1, gradient_examples=8,
            throughput_elapsed_seconds=probe.get("elapsed_seconds"))
    except (ValueError, KeyError, TypeError) as exc:
        summary["errors"].append(str(exc)[:1000])
    return summary


def collect(args):
    directory, _, spec, source_map = load_prepared(args.prepared_sha256, recheck_pilots=False)
    record = json.loads(read(directory / "release/reservation.json"))
    require(record == control.reservation(spec, record.get("job_id"), control.UID), "Collection uses another reservation.")
    output = directory / ("observation-" + str(args.index).zfill(2))
    output.mkdir(exist_ok=False)
    observation = execute_phase(output, {"phase": "collect", "spec": spec, "reservation": record})
    validate_observation(observation)
    for name, row in observation["files"].items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(control.base64.b64decode(row["base64"], validate=True))
        target.chmod(0o444)
    summary = summarize(observation, spec, record, source_map)
    put(output / "summary.json", summary)
    print(json.dumps({"observation_succeeded": True, "smoke": summary,
        "collection_exit_is_not_smoke_success": True, "automatic_next_phase": False}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    prep = subs.add_parser("prepare")
    prep.add_argument("--choice", required=True)
    prep.add_argument("--choice-sha256", required=True)
    prep.add_argument("--ledger-sha256", required=True)
    for action in ("submit-held", "release", "collect"):
        sub = subs.add_parser(action)
        sub.add_argument("--prepared-sha256", required=True)
        if action == "collect":
            sub.add_argument("--index", type=int, choices=range(1, 129), required=True)
        else:
            sub.add_argument("--ledger-sha256", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    with phase_lock():
        if args.action == "prepare":
            prepare(args)
        elif args.action == "collect":
            collect(args)
        else:
            mutate_phase(args)
    return 0


# Hash-bound metadata/transport helper definitions follow; no work on import.
def read(path, expected=None, limit=4 * 1024**2):
    raw = control.ordinary_bytes(path, limit)
    if expected is not None:
        require(type(expected) is str and len(expected) == 64 and digest(raw) == expected, "File pin differs: " + str(path))
    return raw


def put(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= 14 * 1024**2, "Local metadata exceeds its bound.")
    with path.open("xb") as stream:
        stream.write(raw)
    path.chmod(0o444)


def file_pin(path):
    raw = read(path)
    return {"path": path.relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": digest(raw)}


def ledger_seconds(ledger):
    """Conservative full reservations, never actual short failure elapsed time."""
    require(ledger.get("schema") == "hydra-implementation-campaign-v1"
            and ledger.get("campaign_gpu_hours_ceiling") == 6 and ledger.get("automatic_retry") is False,
            "Campaign authority/ceiling differs.")
    rows = ledger.get("gpu_reservations")
    require(type(rows) is list and len(rows) <= 64, "Invalid bounded campaign ledger.")
    total, attempts, jobs = 0, set(), set()
    for row in rows:
        require(type(row) is dict and type(row.get("attempt")) is str and row["attempt"] not in attempts,
                "Ambiguous campaign attempt.")
        attempts.add(row["attempt"])
        seconds = control.integer(row.get("seconds"), 1, 21600, "reserved seconds")
        require(type(row.get("gpus")) is int and row["gpus"] == 1, "Only single-GPU campaign rows are admitted.")
        job = row.get("job_id")
        if job is not None:
            require(type(job) is str and control.re.fullmatch(r"[0-9]{1,20}", job) and job not in jobs, "Ambiguous actual job id.")
            jobs.add(job)
        allocated = row.get("allocated_seconds")
        if allocated is not None:
            control.integer(allocated, 0, seconds, "charged seconds")
        zero = row.get("status") == "preflight_stopped_before_sbatch" and allocated == 0 and job is None
        if not zero:
            require(allocated in (None, seconds), "A submitted, failed or uncertain allocation cannot receive an automatic partial refund.")
            total += seconds
    reported = ledger.get("gpu_hours_allocated")
    require(type(reported) in (int, float) and math.isfinite(reported) and 0 <= reported <= 6, "Invalid allocated-hours total.")
    reserved = control.integer(ledger.get("gpu_seconds_reserved"), 0, 21600, "campaign reserved seconds")
    total = max(total, math.ceil(reported * 3600 - 1e-7), reserved)
    require(total <= 21600, "Campaign has exceeded its six-GPU-hour ceiling.")
    return total


def check_charges(ledger, charges):
    """Root must reconcile full immutable charges before any later allocation."""
    rows = {row["attempt"]: row for row in ledger["gpu_reservations"]}
    for charge in charges:
        row = rows.get(charge["attempt"], {})
        require(all(row.get(key) == charge[key] for key in ("attempt", "job_id", "seconds", "allocated_seconds", "reservation_sha256")),
                "Reconcile the existing full release charge into campaign.json before another allocation; no refund/retry.")


def bundle_inputs():
    read(BUNDLE / "local-seal.json", BUNDLE_SEAL_SHA)
    manifest = json.loads(read(BUNDLE / "manifest.json", BUNDLE_MANIFEST_SHA))
    launch = json.loads(read(BUNDLE / "training-launch-inputs.json", control.LAUNCH_INPUTS_SHA))
    source_map = json.loads(read(BUNDLE / "controller-source-pins.json"))
    require(digest(canonical(source_map)) == control.SOURCE_MAP_SHA and len(source_map) == 585
            and launch["source_pins_sha256"] == control.SOURCE_MAP_SHA
            and launch["training_controller_sha256"] == control.TRAINER_SHA
            and launch["scheduler_helper_sha256"] == control.SMOKE_SHA
            and launch["provider_sha256"] == control.PROVIDER_SHA
            and manifest["archive_sha256"] == control.ARCHIVE_SHA, "Sealed bundle06 launch bindings differ.")
    return manifest, launch, source_map


@contextmanager
def phase_lock():
    # Serializes only these local launchers; root also serializes the overall campaign.
    with (HERE / ".phase.lock").open("ab") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def complete_json(observation, name):
    row = observation["files"].get(name)
    if row is None or row["complete_file"] is not True or row["stable"] is not True:
        return None
    return json.loads(control.base64.b64decode(row["base64"], validate=True))


def evidence(item, *, limit=16 * 1024**2):
    require(type(item) is dict and set(item) == {"path", "sha256"}, "Evidence needs exact workspace path and SHA.")
    path = Path(item["path"])
    require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == item["path"], "Evidence path escapes.")
    return read(ROOT / path, item["sha256"], limit)


def actual_completion(record):
    keys = ("actual_exit_code", "actual_process_exit_code", "actual_outer_exit_code", "exit_code")
    exits = [record[key] for key in keys if key in record]
    require(exits and all(type(code) is int and code == 0 for code in exits), "Actual observed process exit0 is required.")
    chunks = [record[key] for key in ("completion_chunk", "actual_completion_chunk", "actual_outer_completion_chunk") if key in record]
    require(chunks and all(type(chunk) is str and chunk for chunk in chunks), "Separately observed completion chunk is required.")


def training_reader():
    """Reuse the frozen metadata-only admission, without copying evaluator logic."""
    directory = BASE / "p6-training-launchers-v2"
    modules, prior = {}, {}
    try:
        for name, filename in (("remote_training_control", "remote_training_control.py"),
                               ("_smoke_training_metadata", "training_launchers.py")):
            path = directory / filename
            read(path, TRAINING_PINS[filename], 65536)
            prior[name] = sys.modules.get(name)
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            modules[name] = module
    finally:
        for name, old in prior.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old
    return modules["_smoke_training_metadata"]


def ssh_once(payload):
    """One fixed SSH child, nonblocking input/output and a 600-second ceiling."""
    raw = canonical(payload)
    require(len(raw) <= control.MAX_INPUT, "SSH input exceeds its bound.")
    code = read(HERE / "remote_smoke_control.py", limit=65536).decode()
    argv = SSH + ["/usr/bin/env " + shlex.quote("LD_LIBRARY_PATH=" + LOGIN_PYTHON_LIB)
                  + " " + shlex.quote(LOGIN_PYTHON) + " -I -B -c " + shlex.quote(code)]
    process, output, offset, started = None, bytearray(), 0, time.monotonic()
    eof = False
    receipt = {"actual_ssh_exit_code": None, "ssh_attempted": False, "owned_child_reaped": False,
        "stop_reason": None, "automatic_retry": False, "remote_script_sha256": digest(code.encode())}
    limit = control.MAX_RESPONSE
    try:
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        receipt["ssh_attempted"] = True
        os.set_blocking(process.stdin.fileno(), False)
        os.set_blocking(process.stdout.fileno(), False)
        eof = False
        while not (eof and process.poll() is not None):
            if time.monotonic() - started >= 600:
                receipt["stop_reason"] = "ssh_wall_limit"
                break
            readable, writable, _ = select.select([] if eof else [process.stdout],
                [process.stdin] if offset < len(raw) else [], [], 0.05)
            if writable:
                offset += os.write(process.stdin.fileno(), raw[offset:offset + 16384])
                if offset == len(raw):
                    process.stdin.close()
            if readable:
                chunk = os.read(process.stdout.fileno(), min(65536, limit + 1 - len(output)))
                if chunk:
                    output.extend(chunk)
                    if len(output) > limit:
                        receipt["stop_reason"] = "ssh_output_limit"
                        break
                else:
                    eof = True
    except BaseException as exc:
        receipt["stop_reason"] = type(exc).__name__ + ": " + str(exc)[:1024]
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            try:
                receipt["actual_ssh_exit_code"] = process.wait(timeout=3)
                receipt["owned_child_reaped"] = True
            except subprocess.TimeoutExpired:
                receipt["stop_reason"] = "ssh_child_not_reaped"
            for pipe in (process.stdin, process.stdout):
                if pipe and not pipe.closed:
                    pipe.close()
        receipt.update(elapsed_seconds=time.monotonic() - started, input_bytes_sent=offset,
                       output_bytes_retained=min(limit, len(output)), output_complete=bool(eof and offset == len(raw) and receipt["stop_reason"] is None and len(output) <= limit),
                       remote_outcome="reported_in_response" if receipt["stop_reason"] is None
                           and receipt["actual_ssh_exit_code"] == 0 and eof else "unknown")
    return bytes(output[:limit]), receipt


if __name__ == "__main__":
    raise SystemExit(main())
