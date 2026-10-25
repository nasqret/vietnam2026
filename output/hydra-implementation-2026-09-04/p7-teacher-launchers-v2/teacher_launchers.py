"""Prepare one teacher allocation; each later command is one explicit phase.

No network, scheduler, native, tokenizer, or model action occurs at import.
The fixed whole-minute duration is supplied only after real Qwen prerequisites.
"""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
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
import remote_teacher_control as control

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAMPAIGN_FILE = HERE.parent / "campaign.json"
BUNDLE = HERE.parent / "combined-source-bundle-01"
LOGIN_PYTHON = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3"
LOGIN_PYTHON_LIB = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib"
SSH = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
       "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
       "-o", "ClearAllForwardings=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
       "-o", "ControlMaster=no", "-o", "ControlPath=none", "--", "plgnasqret@helios.cyfronet.pl"]
ADMISSION_SHA = "d49c91257d107e4b0618fc35cbaac193efed0f7abf7c29f56a1e79d5ede39e8f"
require, canonical, digest = control.require, control.canonical, control.digest


def admission_api():
    path = HERE.parent / "pilot-completion-admission-v1/pilot_admission.py"
    raw = read(path, ADMISSION_SHA, 128 * 1024)
    spec = importlib.util.spec_from_file_location("_explicit_pilot_admission", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


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


def evidence(record):
    require(type(record) is dict and set(record) == {"path", "sha256", "format"}, "Evidence needs an exact path/hash/format.")
    relative = Path(record["path"])
    require(not relative.is_absolute() and ".." not in relative.parts and str(relative) == record["path"], "Evidence must stay in this workspace.")
    raw = read(ROOT / relative, record["sha256"])
    require(record["format"] in {"json", "jsonl-last"}, "Unknown evidence format.")
    return json.loads(raw if record["format"] == "json" else raw.rstrip().splitlines()[-1])


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


@contextmanager
def phase_lock():
    # Serializes only these local launchers; root also serializes the overall campaign.
    with (HERE / ".phase.lock").open("ab") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def ssh_once(payload):
    """One fixed SSH child, nonblocking input/output and a 600-second ceiling."""
    raw = canonical(payload)
    require(len(raw) <= control.MAX_INPUT, "SSH input exceeds its bound.")
    code = read(HERE / "remote_teacher_control.py", limit=65536).decode()
    argv = SSH + ["/usr/bin/env " + shlex.quote("LD_LIBRARY_PATH=" + LOGIN_PYTHON_LIB)
                  + " " + shlex.quote(LOGIN_PYTHON) + " -I -B -c " + shlex.quote(code)]
    process, output, offset, started = None, bytearray(), 0, time.monotonic()
    receipt = {"actual_ssh_exit_code": None, "ssh_attempted": False, "owned_child_reaped": False,
        "stop_reason": None, "automatic_retry": False, "remote_script_sha256": digest(code.encode())}
    limit = 14 * 1024**2
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
                       output_bytes_retained=min(limit, len(output)), output_complete=len(output) <= limit)
    return bytes(output[:limit]), receipt


def execute_phase(directory, payload):
    put(directory / "request.json", payload)
    output, receipt = ssh_once(payload)
    with (directory / "transport.stdout").open("xb") as stream:
        stream.write(output)
    (directory / "transport.stdout").chmod(0o444)
    put(directory / "transport-completion.json", receipt)
    require(receipt["actual_ssh_exit_code"] == 0 and receipt["owned_child_reaped"] and receipt["stop_reason"] is None,
            "The single SSH attempt failed or was uncertain; preserve it and do not retry.")
    response = json.loads(output)
    require(response.get("completed") is True and response.get("phase") == payload["phase"], "Remote phase did not complete.")
    put(directory / "response.json", response)
    return response["result"]


def complete_json(observation, name):
    row = observation["files"].get(name)
    if row is None or row["complete_file"] is not True or row["stable"] is not True:
        return None
    return json.loads(control.base64.b64decode(row["base64"], validate=True))


def current_ledger(expected):
    raw = read(CAMPAIGN_FILE, expected, 2 * 1024**2)
    ledger = json.loads(raw)
    used = ledger_seconds(ledger)
    charge_paths = set()
    for pattern in ("p6-training-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-8b-smoke-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-8b-training-launchers-v*/attempts/*/release/charge-intent.json",
        "paired-launchers-v*/prepared/arms/*/release/charge-intent.json",
        "p7-teacher-launchers-v*/attempts/*/release/charge-intent.json",
        "p7-student-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-postsave-recovery-v*/attempts/*/release/charge-intent.json"):
        charge_paths.update(HERE.parent.glob(pattern))
    require(len(charge_paths) <= 64, "Cross-family release charge inventory exceeds its bound.")
    check_charges(ledger, [json.loads(read(path)) for path in sorted(charge_paths)])
    require(all(row["attempt"] != control.ATTEMPT for row in ledger["gpu_reservations"]),
            "The single teacher attempt is already charged/reserved; no second invocation.")
    return ledger, raw, used


def bundle_inputs():
    manifest = json.loads(read(BUNDLE / "manifest.json", control.MANIFEST_SHA))
    require(manifest["archive_sha256"] == control.ARCHIVE_SHA
            and manifest["teacher_source_map_sha256"] == control.SOURCE_MAP_SHA,
            "Wrong sealed combined teacher package.")
    source = BUNDLE / "source"
    document = json.loads(read(source / "output/p7-prototype/staged-source-pins.json"))
    source_map = document["sources"]
    require(document["source_pins_sha256"] == control.SOURCE_MAP_SHA
            and digest(canonical(source_map)) == control.SOURCE_MAP_SHA,
            "Fixed teacher source-map scope changed.")
    read(source / control.SELECTION, control.SELECTION_SHA)
    read(source / control.JOB_BODY, control.JOB_BODY_SHA)
    transfer = json.loads(read(HERE.parent / "cpu-fixture-01/upload/actual-completion.json",
                              "2d2ab8c26e6349a8dc3ba30d8610016fb8e0b99e0e3473cb8c661ecd2e82a0ee"))
    upload = json.loads(read(HERE.parent / "cpu-fixture-01/upload/stdout.bin"))
    require(transfer.get("actual_ssh_exit_code") == 0 and transfer.get("transport_timeout") is False
            and upload.get("archive_sha256") == control.ARCHIVE_SHA
            and upload.get("manifest_sha256") == control.MANIFEST_SHA and upload.get("source") == control.SOURCE
            and upload.get("verified_files") == 1301 and upload.get("verified_bytes") == 111831565,
            "Exact combined source upload has not completed.")
    prior = json.loads(read(HERE.parent / "p7-clean-base-admission-01/stdout.json",
                           "e7e36aefc4096c1045dd70ae90fef4eabbdd7f1ad58648f93d77f12f711dabe6"))
    prior_exit = json.loads(read(HERE.parent / "p7-clean-base-admission-01/actual-completion.json",
                                "cb98724c2df9c515ac23c7666941a7300b62c2e2604543377bae235842abdd2d"))
    require(prior_exit.get("actual_ssh_exit_code") == 0 and prior.get("completed") is True
            and digest(canonical(prior)) == control.PRIOR_ADMISSION_CONTENT_SHA
            and prior.get("view") == control.BASE
            and prior.get("identity", {}).get("base_identity_sha256") == control.BASE_IDENTITY_SHA
            and prior["identity"].get("weight_bytes_fully_hashed") is True,
            "Full prior exact teacher base admission is missing.")
    return source_map


def validate_choice(choice):
    require(type(choice) is dict and set(choice) == {"schema", "seconds", "throughput", "fresh_pilots"}
            and choice["schema"] == "hydra-p7-teacher-allocation-choice-v2", "Explicit teacher choice is required.")
    control.integer(choice["seconds"], 600, 7200, "teacher allocation seconds")
    require(choice["seconds"] % 60 == 0, "Teacher duration must use whole minutes; no inferred default.")
    require(type(choice["fresh_pilots"]) is dict and set(choice["fresh_pilots"]) == {"qwen3-1.7b-base", "qwen3-4b-base"},
            "Teacher follows both completed fresh Qwen pilots.")


def verify_prerequisites(choice):
    validate_choice(choice)
    throughput = evidence(choice["throughput"])
    require(throughput.get("schema") == "hydra-completion-gradient-probe-v1"
            and throughput.get("status") == "complete" and throughput.get("max_examples") == 8
            and throughput.get("examples_completed") == throughput.get("forward_calls") == throughput.get("backward_calls") == 8
            and throughput.get("optimizer_steps") == 0 and throughput.get("optimizer_created") is False
            and throughput.get("finite_gradients") is True and throughput.get("trainable_tensors_unchanged") is True
            and throughput.get("model_trained") is False and throughput.get("adapter_saved") is False
            and throughput.get("automatic_retry") is False
            and throughput.get("model") == {"model_id": "Qwen/Qwen3-4B-Base", "revision": "906bfd4b4dc7f14ee4320094d8b41684abff8539"}
            and throughput.get("plan_sha256") == "e332678d9102db48071638b1d94b958cea0cf33c9c60234aef4bf7e5ba64ec7f",
            "Complete real 4B throughput is required before choosing teacher duration.")
    return admission_api().admit_pair(choice["fresh_pilots"], root=ROOT)


def prepare(args):
    choice_raw = read(Path(args.choice).resolve(), args.choice_sha256, 65536)
    choice = json.loads(choice_raw)
    admissions = verify_prerequisites(choice)
    source_map = bundle_inputs()
    ledger, ledger_raw, used = current_ledger(args.ledger_sha256)
    admission_api().require_pilot_charges(ledger, admissions.values())
    require(used + choice["seconds"] <= 21600, "Teacher duration exceeds the remaining full-charge campaign budget.")
    directory = HERE / "attempts" / control.ATTEMPT
    directory.mkdir(parents=True, exist_ok=False)
    spec = control.make_spec(choice["seconds"], secrets.token_hex(16))
    put(directory / "choice.json", choice)
    put(directory / "source-map.json", source_map)
    put(directory / "prepare-ledger.json", ledger)
    prepared = {"schema": "hydra-p7-prepared-teacher-launch-v2", "status": "prepared_not_submitted",
        "spec": spec, "choice": file_pin(directory / "choice.json"), "original_choice_sha256": digest(choice_raw),
        "ledger_read_sha256": digest(ledger_raw), "full_seconds_charged_or_reserved_before": used,
        "full_seconds_after_potential_release": used + choice["seconds"],
        "launcher_sources": {name: file_pin(HERE / name) for name in ("teacher_launchers.py", "remote_teacher_control.py")},
        "base_identity_sha256": control.BASE_IDENTITY_SHA, "automatic_retry": False, "automatic_launch": False,
        "pilot_admissions": admissions,
        "admission_source": file_pin(HERE.parent / "pilot-completion-admission-v1/pilot_admission.py")}
    put(directory / "prepared.json", prepared)
    with (directory / "job.sbatch").open("x") as stream:
        stream.write(control.job_script(spec))
    print(json.dumps({"prepared": file_pin(directory / "prepared.json"), "seconds": choice["seconds"],
                      "source_pins_sha256": control.SOURCE_MAP_SHA, "ssh_calls": 0, "allocations": 0}))


def load_prepared(expected):
    directory = HERE / "attempts" / control.ATTEMPT
    prepared = json.loads(read(directory / "prepared.json", expected))
    require(prepared.get("schema") == "hydra-p7-prepared-teacher-launch-v2", "Wrong teacher prepared record.")
    spec = prepared["spec"]
    control.validate_spec(spec)
    for name in ("teacher_launchers.py", "remote_teacher_control.py"):
        require(file_pin(HERE / name) == prepared["launcher_sources"][name], "Launcher source changed after preparation.")
    choice = json.loads(read(directory / "choice.json", prepared["choice"]["sha256"]))
    admissions = verify_prerequisites(choice)
    require(admissions == prepared["pilot_admissions"]
            and file_pin(HERE.parent / "pilot-completion-admission-v1/pilot_admission.py") == prepared["admission_source"],
            "Pilot admission evidence/helper changed after preparation.")
    require(choice["seconds"] == spec["seconds"], "Prepared duration differs from explicit choice.")
    source_map = bundle_inputs()
    require(json.loads(read(directory / "source-map.json")) == source_map, "Prepared teacher source map changed.")
    return directory, prepared, spec, source_map


def mutate_phase(args):
    directory, prepared, spec, source_map = load_prepared(args.prepared_sha256)
    ledger, ledger_raw, used = current_ledger(args.ledger_sha256)
    admission_api().require_pilot_charges(ledger, prepared["pilot_admissions"].values())
    require(used + spec["seconds"] <= 21600, "Full teacher charge exceeds the remaining campaign budget.")
    phase_dir = directory / args.action
    phase_dir.mkdir(exist_ok=False)
    put(phase_dir / "ledger-snapshot.json", ledger)
    payload = {"phase": args.action, "spec": spec, "source_map": source_map}
    if args.action == "release":
        transport = json.loads(read(directory / "submit/transport-completion.json"))
        require(transport.get("actual_ssh_exit_code") == 0 and transport.get("stop_reason") is None
                and transport.get("owned_child_reaped") is True, "Held teacher submission transport is incomplete.")
        submission = json.loads(read(directory / "submit/response.json"))["result"]
        require(submission.get("actual_sbatch_exit_code") == 0 and submission.get("held") is True
                and submission.get("released") is False, "Held teacher submission not confirmed.")
        record = control.reservation(spec, submission["job_id"], submission["uid"])
        put(phase_dir / "reservation.json", record)
        # This full, immutable charge is written before the sole release SSH.
        charge = {"schema": "hydra-p7-full-release-charge-v1", "attempt": control.ATTEMPT,
            "job_id": record["job_id"], "gpus": 1, "seconds": spec["seconds"], "allocated_seconds": spec["seconds"],
            "reservation_sha256": digest(canonical(record) + b"\n"), "status": "release_requested_or_uncertain",
            "ledger_before_sha256": digest(ledger_raw), "seconds_before": used, "seconds_after": used + spec["seconds"],
            "refund_allowed_automatically": False, "automatic_retry": False}
        put(phase_dir / "charge-intent.json", charge)
        payload["reservation"] = record
    put(phase_dir / "phase-intent.json", {"action": args.action, "prepared_sha256": args.prepared_sha256,
        "ledger_sha256": digest(ledger_raw), "source_pins_sha256": control.SOURCE_MAP_SHA,
        "automatic_retry": False, "one_use": True})
    result = execute_phase(phase_dir, payload)
    print(json.dumps({"phase": args.action, "result": result, "campaign_file_modified": False,
                      "next_phase_automatic": False}, sort_keys=True))


def summarize(observation, spec, record):
    summary = {"job_id": record["job_id"], "status": "in_progress_or_incomplete_evidence",
        "teacher_campaign_metadata_complete": False, "positive_continuations_reported": None,
        "distillation_admitted": False, "full_native_proof_artifacts_downloaded": False,
        "errors": [], "automatic_retry": False}
    try:
        completion = complete_json(observation, "result/completion.json")
        if completion:
            for field in ("states_completed", "proposals", "positive_continuations", "session", "error"):
                summary[field] = completion.get(field)
        sacct = observation["scheduler"]["sacct"]
        require(sacct["actual_exit_code"] == 0 and sacct["stop_reason"] is None, "Actual teacher accounting unavailable.")
        rows = [line.split("|") for line in sacct["stdout_stderr"].splitlines() if line.split("|", 1)[0] == record["job_id"]]
        require(len(rows) == 1 and len(rows[0]) == 14, "Exact teacher accounting row unavailable.")
        row = rows[0]
        require(row[1:5] == [spec["job_name"], control.REMOTE_USER, control.ACCOUNT, control.PARTITION],
                "Teacher accounting identity differs.")
        summary.update(slurm_state=row[5], slurm_exit_code=row[6], actual_scheduler_elapsed_seconds=row[7])
        if row[5] not in {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE"}:
            return summary
        summary["status"] = "terminal_failed_or_incomplete_evidence"
        require(row[5] == "COMPLETED" and row[6] == "0:0" and row[8] == str(spec["seconds"] // 60) and row[9] == "8",
                "Teacher allocation did not complete with exact successful accounting.")
        allocated = control.tres(row[12])
        require(allocated.get("gres/gpu") == "1" and allocated.get("cpu") == "8" and allocated.get("node") == "1"
                and allocated.get("mem") in {"64G", "65536M"}, "Teacher final allocated resources differ.")
        exit_row = observation["files"].get("actual-process-exit.txt", {})
        require(exit_row.get("complete_file") is True
                and control.base64.b64decode(exit_row["base64"], validate=True).strip() == b"0", "Actual teacher process exit0 missing.")
        require(completion and completion.get("schema") == "hydra-teacher-campaign-completion-v1"
                and completion.get("completed") is True and completion.get("error") is None
                and completion.get("selected_states") == completion.get("states_completed") == 32
                and completion.get("sources_unchanged") is True and completion.get("automatic_retry") is False
                and completion.get("student_model_calls") == completion.get("solver_calls") == completion.get("optimizer_updates") == 0,
                "Complete bounded teacher campaign evidence is missing.")
        request = complete_json(observation, "result/request.json")
        require(request and request.get("reservation") == record
                and request.get("reservation_sha256") == digest(canonical(record) + b"\n")
                and request.get("selection_sha256") == control.SELECTION_SHA
                and request.get("source_pins_before") == completion.get("source_pins_after")
                and digest(canonical(request["source_pins_before"])) == control.SOURCE_MAP_SHA,
                "Teacher request/source/selection pins differ.")
        admission = complete_json(observation, "result/model-admission.json")
        identity = admission.get("identity", {}) if admission else {}
        session = completion.get("session")
        require(identity.get("schema") == "hydra-loaded-remote-teacher-v1"
                and identity.get("model_key") == control.MODEL_KEY
                and identity.get("model_id") == "deepseek-ai/DeepSeek-Prover-V2-7B"
                and identity.get("revision") == "a8d9e14432b2e8dd9df2a4d4e70f1ba9bc8d9b7b"
                and identity.get("base", {}).get("base_identity_sha256") == control.BASE_IDENTITY_SHA
                and identity.get("model_loaded") is True and identity.get("adapter_present") is False
                and identity.get("source_sha256") == "f16f46a9cbb98950749e9b67eb0b3818f011ce25256be6285a962700e4fd13da"
                and identity.get("p6_helper_sha256") == "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
                and identity.get("model_manifest_sha256") == digest(canonical(
                    {key: value for key, value in identity.items() if key != "model_manifest_sha256"}))
                and type(session) is dict and session.get("identity") == identity,
                "Actual loaded teacher identity is missing or differs.")
        control.integer(session.get("actual_model_calls"), 0, 64, "actual teacher calls")
        control.integer(session.get("generated_tokens"), 0, 32768, "actual teacher generated tokens")
        control.integer(completion.get("proposals"), 0, 128, "actual teacher proposals")
        positives = complete_json(observation, "result/positive-continuations.json")
        require(positives and positives.get("schema") == "hydra-teacher-positive-continuations-v1"
                and positives.get("positive_count") == completion.get("positive_continuations") == len(positives.get("records", []))
                and positives.get("training_performed") is False and positives.get("fresh_p5_admission_required") is True,
                "Teacher positive-continuation metadata differs.")
        count = positives["positive_count"]
        summary.update(status="teacher_metadata_complete_fresh_native_admission_required" if count else "teacher_complete_zero_yield_distillation_blocked",
            teacher_campaign_metadata_complete=True, positive_continuations_reported=count)
    except (ValueError, KeyError, TypeError) as exc:
        summary["errors"].append(str(exc)[:1024])
    return summary


def collect(args):
    directory, prepared, spec, _ = load_prepared(args.prepared_sha256)
    record = json.loads(read(directory / "release/reservation.json"))
    output = directory / ("observation-" + str(args.index).zfill(3))
    output.mkdir(exist_ok=False)
    observation = execute_phase(output, {"phase": "collect", "spec": spec, "reservation": record})
    require(observation.get("job_id") == record["job_id"] and observation.get("read_only") is True
            and set(observation["files"]) <= set(control.FILES), "Wrong or excessive teacher observation.")
    total = 0
    for name, row in observation["files"].items():
        data = control.base64.b64decode(row["base64"], validate=True)
        total += len(data)
        require(len(data) == row["bytes"] and digest(data) == row["sha256"] and total <= control.MAX_OBSERVATION,
                "Teacher observation bytes differ.")
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(data)
    summary = summarize(observation, spec, record)
    for row in observation["files"].values():
        row.pop("base64")
    put(output / "observation.json", observation)
    put(output / "summary.json", summary)
    print(json.dumps(summary, sort_keys=True))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    prep = subs.add_parser("prepare")
    prep.add_argument("--choice", required=True)
    prep.add_argument("--choice-sha256", required=True)
    prep.add_argument("--ledger-sha256", required=True)
    for action in ("submit", "release", "collect"):
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


if __name__ == "__main__":
    raise SystemExit(main())
