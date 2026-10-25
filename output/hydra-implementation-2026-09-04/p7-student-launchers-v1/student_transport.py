"""One explicit student transport phase; no allocation or network on import."""
from __future__ import annotations
import argparse
from contextlib import contextmanager
import fcntl
import hashlib
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
import remote_student_control as control
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CAMPAIGN_FILE = HERE.parent / "campaign.json"
LOGIN_PYTHON = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3"
LOGIN_PYTHON_LIB = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib"
SSH = ["/usr/bin/ssh","-T","-o","BatchMode=yes","-o","ConnectTimeout=15",
       "-o","ServerAliveInterval=10","-o","ServerAliveCountMax=2","-o","ForwardAgent=no",
       "-o","ClearAllForwardings=yes","-o","StrictHostKeyChecking=yes","-o","UpdateHostKeys=no",
       "-o","ControlMaster=no","-o","ControlPath=none","--","plgnasqret@helios.cyfronet.pl"]
require, canonical, digest = control.require, control.canonical, control.digest

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
    code = read(HERE / "remote_student_control.py", limit=65536).decode()
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
    raw = read(CAMPAIGN_FILE, expected, 2*1024**2)
    ledger = json.loads(raw); used = ledger_seconds(ledger)
    paths = set()
    for pattern in ("p6-training-launchers-v*/attempts/*/release/charge-intent.json",
                    "p6-8b-smoke-launchers-v*/attempts/*/release/charge-intent.json",
                    "p6-8b-training-launchers-v*/attempts/*/release/charge-intent.json",
                    "paired-launchers-v*/prepared/arms/*/release/charge-intent.json",
                    "p7-teacher-launchers-v*/attempts/*/release/charge-intent.json",
                    "p7-student-launchers-v*/attempts/*/release/charge-intent.json"):
        paths.update(HERE.parent.glob(pattern))
    require(len(paths) <= 64, "Cross-family charge inventory exceeds its bound.")
    check_charges(ledger,[json.loads(read(path)) for path in sorted(paths)])
    require(all(row["attempt"] != control.ATTEMPT for row in ledger["gpu_reservations"]),
            "Student attempt already reserved/charged; do not invoke it twice.")
    return ledger, raw, used


def validate_request(payload):
    require(type(payload) is dict and payload.get("phase") in {"submit","release","collect"}, "Unknown student phase.")
    expected = {"phase","spec","source_map"} | ({"reservation"} if payload["phase"] != "submit" else set())
    require(set(payload) == expected, "Unexpected student phase inputs.")
    control.validate_spec(payload["spec"])
    require(type(payload["source_map"]) is dict and len(payload["source_map"]) == 595
            and digest(canonical(payload["source_map"])) == control.SOURCE_MAP_SHA, "Wrong exact student source map.")
    if payload["phase"] != "submit":
        record = payload["reservation"]
        require(record == control.reservation(payload["spec"],record.get("job_id"),record.get("uid")), "Wrong actual student reservation.")


def summarize(observation, spec, record, transport):
    """A successful read does not imply completed training or tensor admission."""
    summary = {"job_id":record["job_id"],"status":"in_progress_or_incomplete_evidence",
        "collection_verified":False,"training_evidence_complete":False,"saved_artifact_metadata_complete":False,
        "adapter_reload_admitted":False,"quality_evaluated":False,"automatic_retry":False,
        "expected_optimizer_steps":spec["expected_optimizer_steps"],"errors":[]}
    try:
        require(type(transport.get("actual_ssh_exit_code")) is int and transport["actual_ssh_exit_code"] == 0
                and transport.get("owned_child_reaped") is True and transport.get("output_complete") is True
                and transport.get("stop_reason") is None and transport.get("automatic_retry") is False,
                "Actual collection transport is incomplete.")
        require(observation.get("job_id") == record["job_id"] and observation.get("read_only") is True,
                "Student collection belongs to another job.")
        summary["collection_verified"] = True
        completion = complete_json(observation,"job/result/completion.json")
        if completion:
            summary.update(controller_reported_completed=completion.get("completed"),
                optimizer_callbacks_observed=completion.get("optimizer_callbacks_observed"),
                actual_optimizer_steps_in_complete_artifact=completion.get("actual_optimizer_steps"))
        query = observation["scheduler"]["sacct"]
        require(type(query.get("actual_exit_code")) is int and query["actual_exit_code"] == 0
                and query.get("stop_reason") is None, "Successful actual terminal accounting is unavailable.")
        rows = [line.split("|") for line in query["stdout_stderr"].splitlines() if line.split("|",1)[0] == record["job_id"]]
        require(len(rows) == 1 and len(rows[0]) == 14, "An exact 14-column allocation accounting row is required.")
        row = rows[0]
        require(row[1:5] == [spec["job_name"],control.REMOTE_USER,control.ACCOUNT,control.PARTITION], "Accounting job identity differs.")
        summary.update(slurm_state=row[5],slurm_exit_code=row[6],actual_scheduler_elapsed_seconds=row[7])
        if row[5] not in {"COMPLETED","FAILED","CANCELLED","TIMEOUT","OUT_OF_MEMORY","NODE_FAIL","PREEMPTED","BOOT_FAIL","DEADLINE"}:
            return summary
        summary["status"] = "terminal_failed_or_incomplete_evidence"
        require(row[5:7] == ["COMPLETED","0:0"] and row[7].isdigit()
                and row[8] == str(spec["seconds"]//60) and row[9] == "8", "Actual Slurm completion/limits differ.")
        allocated = control.tres(row[12])
        require(allocated.get("cpu") == "8" and allocated.get("node") == allocated.get("gres/gpu") == "1"
                and allocated.get("mem") in {"64G","65536M"}, "Actual student allocation resources differ.")
        require(control.REQUIRED <= set(observation["files"])
                and "artifact/incomplete.json" not in observation["files"], "Saved student evidence is incomplete.")
        for name in control.REQUIRED:
            pin = observation["files"][name]
            raw = control.base64.b64decode(pin["base64"],validate=True)
            require(pin.get("stable") is True and pin.get("complete_file") is True
                    and len(raw) == pin["bytes"] and digest(raw) == pin["sha256"], "Required evidence bytes changed or are partial.")
        require(control.base64.b64decode(observation["files"]["job/actual-process-exit.txt"]["base64"],validate=True).strip() == b"0",
                "Actual student process exit zero is missing.")
        require(complete_json(observation,"job/reservation.json") == record, "Collected reservation differs.")
        request = complete_json(observation,"job/result/request.json")
        manifest = complete_json(observation,"artifact/manifest.json")
        require(request and completion and manifest, "Required full JSON records are missing.")
        require(request.get("schema") == "hydra-p7-student-update-request-v1" and request.get("profile") == control.PROFILE
                and request.get("reservation") == record and request.get("reservation_sha256") == digest(canonical(record)+b"\n")
                and digest(canonical(request.get("source_pins_before"))) == control.SOURCE_MAP_SHA
                and request.get("source_pins_before") == completion.get("source_pins_after")
                and request.get("config") == control.SOURCE+"/"+control.CONFIG
                and request.get("dataset_manifest") == control.SOURCE+"/"+control.DATA,
                "Actual student inputs/source/reservation differ.")
        plan, steps = manifest.get("plan"), spec["expected_optimizer_steps"]
        control.validate_plan(plan,spec)
        require(completion.get("schema") == "hydra-p7-student-update-completion-v1"
                and completion.get("profile") == control.PROFILE and completion.get("completed") is True
                and completion.get("error") is None and completion.get("sources_unchanged") is True
                and type(completion.get("actual_optimizer_steps")) is int and completion["actual_optimizer_steps"] == steps
                and type(completion.get("optimizer_callbacks_observed")) is int and completion["optimizer_callbacks_observed"] == steps
                and completion.get("base_rows_preserved") == 2047
                and completion.get("teacher_rows_added") == spec["training_rows"]-2047
                and completion.get("resume") is False and completion.get("automatic_retry") is False,
                "Actual training completion does not cover the admitted dynamic optimizer count.")
        claim = complete_json(observation,"job/reservation.json.claimed")
        require(claim and claim.get("schema") == "hydra-p7-student-update-consumption-v1"
                and claim.get("job_id") == record["job_id"] and claim.get("nonce") == record["nonce"]
                and claim.get("reservation_sha256") == request["reservation_sha256"]
                and claim.get("dataset_sha256") == spec["dataset_sha256"] and claim.get("plan_sha256") == spec["plan_sha256"]
                and claim.get("automatic_retry") is False and claim.get("resume") is False,
                "The actual one-use student consumption is missing.")
        tokens = complete_json(observation,"job/result/token-preflight.json")
        require(manifest.get("schema") == "hydra-decision-pilot-artifact-v1" and manifest.get("profile") == control.PROFILE
                and manifest.get("model") == control.MODEL and manifest.get("model_trained") is True
                and type(manifest.get("actual_optimizer_steps")) is int and manifest["actual_optimizer_steps"] == steps
                and manifest.get("resume") is False and manifest.get("automatic_retry") is False
                and manifest.get("saved_adapter_reload_admission") == "required_by_P6_before_inference"
                and complete_json(observation,"job/result/prepared-plan.json") == plan
                and complete_json(observation,"job/result/trained-artifact.json") == manifest
                and manifest.get("token_preflight") == tokens and tokens
                and tokens.get("plan_sha256") == spec["plan_sha256"]
                and manifest.get("base") == tokens.get("base")
                and manifest.get("base",{}).get("base_identity_sha256") == spec["base_identity_sha256"]
                and manifest.get("reservation",{}).get("job_id") == manifest.get("final_reservation",{}).get("job_id") == record["job_id"],
                "Saved manifest/plan/token/base/completion receipts disagree.")
        audit, update = manifest.get("finite_gradient_audit",{}), manifest.get("adapter_update",{})
        require(all(type(audit.get(k)) is int and audit[k] == steps for k in
            ("expected_optimizer_boundaries","observed_optimizer_boundaries","raw_finite_optimizer_boundaries","post_clip_finite_optimizer_boundaries"))
            and audit.get("first_optimizer_step") == 1 and audit.get("last_optimizer_step") == steps,
            "Finite gradients do not cover every admitted optimizer boundary.")
        require(type(update.get("changed_parameter_tensors")) is int and update["changed_parameter_tensors"] > 0
                and type(update.get("trainable_parameter_tensors")) is int and update["trainable_parameter_tensors"] > 0
                and update.get("trainable_parameter_tensors") == update.get("final_finite_parameter_tensors")
                and all(control.valid_sha(update.get(k)) for k in ("initial_tensor_population_sha256","final_tensor_population_sha256"))
                and update["initial_tensor_population_sha256"] != update["final_tensor_population_sha256"],
                "Saved adapter update audit is incomplete.")
        current = observation.get("admitted_plan_check",{})
        hashes = observation.get("artifact_byte_verification",{})
        require(current.get("status") == "verified_current_pins" and current.get("plan_sha256") == spec["plan_sha256"]
                and current.get("plan_file_sha256") == spec["plan_file_sha256"] and current.get("expected_optimizer_steps") == steps
                and hashes.get("status") == "verified_bytes_not_loaded" and hashes.get("tensor_reload_performed") is False
                and hashes.get("groups") == {k:manifest[k] for k in ("adapter","tokenizer")},
                "Actual current input/saved-file hashes have not been verified.")
        summary.update(status="complete_saved_student_evidence_requires_reload",training_evidence_complete=True,
            saved_artifact_metadata_complete=True,saved_file_bytes_verified=True,
            manifest_sha256=observation["files"]["artifact/manifest.json"]["sha256"],
            admitted_plan_sha256=spec["plan_sha256"],finite_gradient_boundaries=steps,
            changed_parameter_tensors=update["changed_parameter_tensors"])
    except (ValueError,KeyError,TypeError) as error:
        summary["errors"].append(str(error)[:1024])
    return summary


def run(args):
    raw = read(Path(args.request).absolute(),args.request_sha256,control.MAX_INPUT)
    payload = json.loads(raw); validate_request(payload)
    phase, spec = payload["phase"], payload["spec"]
    attempt = HERE/"attempts"/control.ATTEMPT
    attempt.mkdir(parents=True,exist_ok=True)
    if phase == "collect":
        require(type(args.index) is int and 1 <= args.index <= 128, "Choose a new explicit observation index.")
        prior = json.loads(read(attempt/"release/request.json"))
        require(payload["spec"] == prior["spec"] and payload["source_map"] == prior["source_map"]
                and payload["reservation"] == prior["reservation"], "Collection differs from the actual release request.")
        destination = attempt/("observation-"+str(args.index).zfill(3))
    else:
        require(args.index is None and control.valid_sha(args.ledger_sha256), "A mutation needs the current exact campaign ledger.")
        ledger, ledger_raw, used = current_ledger(args.ledger_sha256)
        require(used+spec["seconds"] <= 21600, "The full student reservation exceeds the remaining campaign ceiling.")
        destination = attempt/phase
    destination.mkdir(exist_ok=False)
    if phase != "collect":
        put(destination/"ledger-snapshot.json",ledger)
    if phase == "release":
        submission = json.loads(read(attempt/"submit/response.json"))["result"]
        previous = json.loads(read(attempt/"submit/request.json"))
        transport = json.loads(read(attempt/"submit/transport-completion.json"))
        require(transport.get("actual_ssh_exit_code") == 0 and transport.get("owned_child_reaped") is True
                and transport.get("stop_reason") is None and transport.get("output_complete") is True
                and submission.get("actual_sbatch_exit_code") == 0 and submission.get("held") is True
                and submission.get("released") is False and previous["spec"] == spec
                and previous["source_map"] == payload["source_map"], "Held student submission is not the exact completed prior phase.")
        record = control.reservation(spec,submission["job_id"],submission["uid"])
        require(record == payload["reservation"], "Release reservation differs from the actual held job.")
        put(destination/"charge-intent.json",{"schema":"hydra-p7-student-full-release-charge-v1",
            "attempt":control.ATTEMPT,"job_id":record["job_id"],"gpus":1,"seconds":spec["seconds"],
            "allocated_seconds":spec["seconds"],"reservation_sha256":digest(canonical(record)+b"\n"),
            "ledger_before_sha256":digest(ledger_raw),"seconds_before":used,"seconds_after":used+spec["seconds"],
            "status":"release_requested_or_uncertain","refund_allowed_automatically":False,"automatic_retry":False})
    result = execute_phase(destination,payload)
    if phase != "collect":
        print(json.dumps({"phase":phase,"result":result,"next_phase_automatic":False,"campaign_file_modified":False},sort_keys=True))
        return 0
    require(set(result["files"]) <= set(control.FILES), "Unexpected student collection path.")
    total = 0
    for name, row in result["files"].items():
        data = control.base64.b64decode(row["base64"],validate=True); total += len(data)
        require(len(data) == row["bytes"] and digest(data) == row["sha256"] and total <= control.MAX_OBSERVATION,
                "Collected bytes/hash/bound differs.")
        target = destination/name; target.parent.mkdir(parents=True,exist_ok=True)
        with target.open("xb") as stream: stream.write(data)
        target.chmod(0o444)
    receipt = json.loads(read(destination/"transport-completion.json"))
    summary = summarize(result,spec,payload["reservation"],receipt)
    for row in result["files"].values(): row.pop("base64")
    put(destination/"observation.json",result); put(destination/"summary.json",summary)
    print(json.dumps(summary,sort_keys=True))
    return 0


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request",required=True)
    parser.add_argument("--request-sha256",required=True)
    parser.add_argument("--ledger-sha256")
    parser.add_argument("--index",type=int)
    args = parser.parse_args(); os.umask(0o077)
    with phase_lock():
        return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
