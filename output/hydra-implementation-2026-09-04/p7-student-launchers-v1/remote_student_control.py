"""One finite student control phase; existing reviewed P6 guards, no training on import.

The scheduled body invokes the unchanged P7 student controller. This transport
never downloads models, retries a phase, or runs a proof/model itself.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import select
import shlex
import signal
import stat
import subprocess
import sys
import time
PROJECT = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training"
CAMPAIGN = PROJECT + "/experiments/hydra-practical-v1-20260904"
SOURCE = CAMPAIGN + "/bundles/teacher-student-source-01/source"
ATTEMPT = "p7-student-update-1.7b-01"
MODEL_KEY = "qwen3-1.7b-base"
MODEL = {"model_id":"Qwen/Qwen3-1.7B-Base","revision":"ea980cb0a6c2ae4b936e82123acc929f1cec04c1"}
ACCOUNT = "plgccaiautore2026-gpu-gh200"
PARTITION = "plgrid-gpu-gh200"
REMOTE_USER = "plgnasqret"
CYCLE = "output/p7-student-cycle-v1"
CONFIG, DATA, PLAN, ARTIFACT = CYCLE+"/student-1.7b.toml", CYCLE+"/dataset/manifest.json", CYCLE+"/student-plan.json", CYCLE+"/student-artifact"
TRAINER = "output/p7-prototype/distillation/remote_student_update.py"
TRAINER_SHA = "11afed22a5635f21082678164dd81ac8e25fa4844d3898e9524dd2ce9faa6b82"
SOURCE_MAP_SHA = "e02dbea834e8dc9233e6c044f5f5108400eda5bacb8beed160c4b44ca759bea1"
PROVIDER_SHA = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
BASE_DATA_SHA = "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"
SELECTION_SHA = "26c09c2b28f54073f3964c4772113f7496eceb03107b356b892c619c9cc835d7"
HOLDOUT_SHA = "2a57f12ffe55f90c3c4ac896fba3c2bab47e795b6bb5ba5f15b2c6854cddb58e"
PROFILE = "hydra-fresh-teacher-augmented-pilot-v1"
MAX_INPUT, MAX_COMMAND_OUTPUT, MAX_OBSERVATION, PHASE_WALL = 256*1024, 65536, 8*1024**2, 550.0
SACCT_FORMAT = "JobIDRaw,JobName%100,User,Account,Partition,State,ExitCode,ElapsedRaw,TimelimitRaw,AllocCPUS,ReqMem,ReqTRES%300,AllocTRES%300,NodeList"
REQUIRED = {"job/actual-process-exit.txt","job/reservation.json","job/reservation.json.claimed",
    "job/result/request.json","job/result/completion.json","job/result/prepared-plan.json",
    "job/result/token-preflight.json","job/result/trained-artifact.json","artifact/manifest.json"}
TAILS = {"job/slurm.out","job/slurm.err","job/result/progress.jsonl","job/result/scheduler.jsonl"}
FILES = tuple(sorted(REQUIRED | TAILS | {"job/release-completion.json","job/result/runtime.json","artifact/incomplete.json"}))

def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def integer(value, lower, upper, name):
    require(type(value) is int and lower <= value <= upper, "Invalid " + name)
    return value


def durations(seconds, soft):
    integer(seconds, 300, 7200, "allocation seconds")
    require(seconds % 60 == 0, "Allocation must use exact whole minutes; no rounding.")
    integer(soft, 60, min(6900, seconds - 60), "soft deadline")


def wall_string(seconds):
    return f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:00"


def ordinary_bytes(path, limit):
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path and before.st_size <= limit,
            "Not a bounded ordinary file: " + str(path))
    with path.open("rb") as stream:
        raw = stream.read(limit + 1)
    after = path.lstat()
    require(len(raw) <= limit and all(getattr(before, key) == getattr(after, key)
            for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns")), "File changed while read.")
    return raw


def save(path, value):
    raw = canonical(value) + b"\n"
    require(len(raw) <= MAX_OBSERVATION, "Control evidence exceeds its bound.")
    with path.open("xb") as stream:
        stream.write(raw)


def fields(raw):
    pairs = re.findall(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=([^\s]+)", raw)
    require(len(pairs) == len({key for key, _ in pairs}), "Ambiguous scheduler response.")
    return dict(pairs)


def tres(raw):
    pairs = [item.split("=", 1) for item in raw.split(",")]
    require(all(len(pair) == 2 for pair in pairs) and len(pairs) == len({p[0] for p in pairs}), "Invalid TRES.")
    return dict(pairs)


def check_queue_row(identifier, row, allowed_job=None):
    require(re.fullmatch(r"[0-9]{1,20}(?:_[0-9]{1,10})?", identifier), "Invalid queue job identity.")
    if "_" in identifier:
        base, task = identifier.split("_")
        require(row.get("ArrayJobId") == base and row.get("ArrayTaskId") == task, "Array element identity differs.")
    else:
        require(row.get("JobId") == identifier, "Queue job identity differs.")
    require("ReqTRES" in row, "Missing requested resources.")
    requested = tres(row["ReqTRES"])
    allocated_raw = row.get("AllocTRES")
    require(allocated_raw is None or type(allocated_raw) is str, "Invalid allocated resources.")
    # Slurm prints this exact sentinel for pending jobs with no allocation yet.
    allocated = {} if allocated_raw in (None, "", "(null)") else tres(allocated_raw)
    if identifier != allowed_job:
        require(not any(key.startswith("gres/gpu") for key in requested.keys() | allocated.keys()),
                "Another owned GPU reservation/allocation exists; leave it unchanged.")
    return {"job_id": identifier, "requested_tres": requested, "allocated_tres": allocated, "left_unchanged": True}


def check_held(row, spec, job_id, uid):
    validate_spec(spec)
    expected = {"JobId": job_id, "JobName": spec["job_name"], "Comment": "hydra-p6:" + spec["nonce"],
        "JobState": "PENDING", "Reason": "JobHeldUser", "Requeue": "0", "Restarts": "0",
        "Account": ACCOUNT, "Partition": PARTITION, "NumCPUs": "8",
        "TimeLimit": wall_string(spec["seconds"]), "Command": spec["remote_job_directory"] + "/job.sbatch",
        "WorkDir": spec["remote_job_directory"], "StdOut": spec["remote_job_directory"] + "/slurm.out",
        "StdErr": spec["remote_job_directory"] + "/slurm.err"}
    require(all(row.get(key) == value for key, value in expected.items()), "Held job identity/resources differ.")
    require(row.get("NumNodes") in ("1", "1-1"), "Held job does not request exactly one node.")
    require(re.fullmatch(r"[^()]+\(" + str(uid) + r"\)", row.get("UserId", "")), "Held job belongs to another uid.")
    requested = tres(row.get("ReqTRES", ""))
    require(all(requested.get(key) == value for key, value in {"cpu": "8", "mem": "64G", "node": "1", "gres/gpu": "1"}.items())
            and all(value == "1" for key, value in requested.items() if key.startswith("gres/gpu")), "Requested TRES differ.")


def bounded_command(argv, timeout=15.0, limit=MAX_COMMAND_OUTPUT):
    """One owned CLI child; bounded combined pipe, explicit kill/reap, no retry."""
    started = time.monotonic()
    record = {"command": argv, "actual_exit_code": None, "executed": False, "owned_child_reaped": False,
              "stop_reason": None, "stdout_stderr": ""}
    process, raw = None, bytearray()
    try:
        process = subprocess.Popen(argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        record["executed"] = True
        os.set_blocking(process.stdout.fileno(), False)
        eof = False
        while not (eof and process.poll() is not None):
            if time.monotonic() - started >= timeout:
                record["stop_reason"] = "wall_limit"
                break
            if not eof and select.select([process.stdout], [], [], 0.05)[0]:
                chunk = os.read(process.stdout.fileno(), min(16384, limit + 1 - len(raw)))
                if chunk:
                    raw.extend(chunk)
                    if len(raw) > limit:
                        record["stop_reason"] = "output_limit"
                        break
                else:
                    eof = True
            elif eof:
                time.sleep(0.02)
    except BaseException as exc:
        record["stop_reason"] = type(exc).__name__ + ": " + str(exc)[:512]
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            try:
                record["actual_exit_code"] = process.wait(timeout=3)
                record["owned_child_reaped"] = True
            except subprocess.TimeoutExpired:
                record["stop_reason"] = "owned_child_not_reaped"
            if process.stdout:
                process.stdout.close()
        record["stdout_stderr"] = bytes(raw[:limit]).decode("utf-8", "replace")
        record["elapsed_seconds"] = time.monotonic() - started
    return record


class Phase:
    def __init__(self):
        self.deadline = time.monotonic() + PHASE_WALL
        self.commands = []

    def run(self, argv, *, timeout=15.0, must_succeed=True):
        require(len(self.commands) < 36 and time.monotonic() < self.deadline, "Phase command/wall bound reached.")
        row = bounded_command(argv, min(timeout, self.deadline - time.monotonic()))
        self.commands.append(row)
        require(row["owned_child_reaped"], "Owned control child cleanup was not confirmed.")
        if must_succeed:
            require(row["actual_exit_code"] == 0 and row["stop_reason"] is None, "Bounded scheduler command failed.")
        return row

    def query(self, job_id):
        return fields(self.run(["scontrol", "-o", "show", "job", job_id])["stdout_stderr"])

    def queue(self, allowed_job=None):
        raw = self.run(["squeue", "--array", "-h", "-u", str(os.getuid()), "-o", "%i|%T|%j|%b"])["stdout_stderr"]
        rows = raw.splitlines()
        require(len(rows) <= 32, "Too many owned queue records for this bounded preflight.")
        result, seen = [], set()
        for line in rows:
            identifier = line.split("|", 1)[0].strip()
            require(identifier not in seen and re.fullmatch(r"[0-9]{1,20}(?:_[0-9]{1,10})?", identifier), "Ambiguous queue identity.")
            seen.add(identifier)
            result.append(check_queue_row(identifier, self.query(identifier), allowed_job))
        if allowed_job is not None:
            require(allowed_job in seen, "Held job absent from current queue.")
        return result


def submit(phase, spec, source_map):
    verify_sources(spec, source_map)
    queue = phase.queue()
    directory = Path(spec["remote_job_directory"])
    directory.mkdir(parents=True, exist_ok=False)
    script = job_script(spec)
    with (directory / "job.sbatch").open("x") as stream:
        stream.write(script)
    save(directory / "allocation-request.json", spec)
    argv = ["sbatch", "--hold", "--parsable", "--no-requeue", "--account=" + ACCOUNT, "--partition=" + PARTITION,
        "--nodes=1", "--ntasks=1", "--cpus-per-task=8", "--mem=64G", "--gres=gpu:1", "--time=" + wall_string(spec["seconds"]),
        "--job-name=" + spec["job_name"], "--comment=hydra-p6:" + spec["nonce"], "--chdir=" + str(directory),
        "--output=" + str(directory / "slurm.out"), "--error=" + str(directory / "slurm.err"), str(directory / "job.sbatch")]
    # Exclusive intent survives failed/uncertain sbatch; this path cannot submit twice.
    save(directory / "submit-intent.json", {"argv": argv, "automatic_retry": False})
    actual = phase.run(argv, timeout=20, must_succeed=False)
    result = {"actual_sbatch_exit_code": actual["actual_exit_code"], "uid": os.getuid(), "held": False,
        "released": False, "other_cpu_jobs": queue, "sbatch": actual}
    if actual["actual_exit_code"] == 0 and actual["stop_reason"] is None:
        job_id = actual["stdout_stderr"].strip()
        require(re.fullmatch(r"[0-9]{1,20}", job_id), "Sbatch did not return an exact scalar job id; do not retry.")
        result["job_id"] = job_id
        before = phase.query(job_id)
        check_held(before, spec, job_id, os.getuid())
        result.update(held=True, held_fields=before)
    save(directory / "held-submission.json", result)
    require(result["held"], "Submission failed or exact held state was not confirmed; no release/retry.")
    return result


def release(phase, spec, source_map, record):
    require(record == reservation(spec, record.get("job_id"), os.getuid()), "Reservation identity differs.")
    verify_sources(spec, source_map)
    directory = Path(spec["remote_job_directory"])
    require(json.loads(ordinary_bytes(directory / "allocation-request.json", MAX_INPUT)) == spec,
            "Remote submitted request changed.")
    require(ordinary_bytes(directory / "job.sbatch", 32768) == job_script(spec).encode(), "Remote job script changed.")
    before = phase.query(record["job_id"])
    check_held(before, spec, record["job_id"], os.getuid())
    queue = phase.queue(record["job_id"])
    raw = canonical(record) + b"\n"
    with (directory / "reservation.json").open("xb") as stream:
        stream.write(raw)
    with (directory / "reservation.sha256").open("x") as stream:
        stream.write(digest(raw) + "\n")
    save(directory / "release-intent.json", {"reservation_sha256": digest(raw), "before": before,
        "queue": queue, "allocated_seconds_ceiling": spec["seconds"], "automatic_retry": False})
    actual = phase.run(["scontrol", "release", record["job_id"]], must_succeed=False)
    result = {"job_id": record["job_id"], "actual_release_exit_code": actual["actual_exit_code"],
        "released": actual["actual_exit_code"] == 0 and actual["stop_reason"] is None,
        "reservation_sha256": digest(raw), "allocated_seconds_ceiling": spec["seconds"], "release": actual,
        "automatic_retry": False, "uncertain_release_still_fully_charged": True}
    save(directory / "release-completion.json", result)
    return result


def snapshot(path, *, tail):
    if not path.exists() and not path.is_symlink():
        return None
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path, "Evidence path is not ordinary.")
    limit = 256 * 1024 if tail else 2 * 1024**2
    require(tail or before.st_size <= limit, "Complete JSON evidence exceeds its bound.")
    offset = max(0, before.st_size - limit) if tail else 0
    with path.open("rb") as stream:
        stream.seek(offset)
        raw = stream.read(min(limit, before.st_size - offset))
    after = path.lstat()
    stable = all(getattr(before, key) == getattr(after, key) for key in ("st_dev", "st_ino", "st_size", "st_mtime_ns"))
    return {"bytes": len(raw), "sha256": digest(raw), "base64": base64.b64encode(raw).decode(),
        "offset": offset, "file_bytes_before": before.st_size, "file_bytes_after": after.st_size,
        "mtime_ns_before": before.st_mtime_ns, "stable": stable,
        "complete_file": stable and offset == 0 and len(raw) == before.st_size}


def valid_sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_plan(plan, spec=None):
    """Metadata preflight only; unchanged student runtime regenerates admission."""
    require(type(plan) is dict and plan.get("schema") == "hydra-teacher-augmented-pilot-plan-v1"
            and plan.get("profile") == PROFILE and plan.get("model") == MODEL
            and plan.get("initialization") == "fresh_pinned_base_new_lora"
            and plan.get("resume") is False and plan.get("automatic_retry") is False
            and plan.get("model_trained") is False and plan.get("epochs") == 1
            and plan.get("prompt_schema") == "primitive_v4" and plan.get("planner_rows_allowed") is False,
            "Only the explicit fresh 1.7B teacher-augmented primitive plan is allowed.")
    require(valid_sha(plan.get("plan_sha256"))
            and digest(canonical({k:v for k,v in plan.items() if k != "plan_sha256"})) == plan["plan_sha256"],
            "The admitted plan's canonical identity differs.")
    rows = integer(plan.get("training_rows"), 2048, 4096, "teacher training rows")
    steps = (rows + 7) // 8
    require(type(plan.get("expected_optimizer_steps")) is int and plan["expected_optimizer_steps"] == steps
            and type(plan.get("validation_rows")) is int and plan["validation_rows"] == 432,
            "Optimizer count must follow the admitted augmented rows; no fixed 256-step assumption.")
    data = plan.get("data_attestation") or {}
    added = integer(data.get("teacher_rows_added"), 1, 2049, "admitted teacher rows")
    verified = integer(data.get("fresh_verified_continuations"), 1, 32, "complete fresh continuations")
    calls = integer(data.get("actual_teacher_model_calls"), 1, 64, "actual teacher calls")
    require(data.get("schema") == "hydra-teacher-augmented-data-attestation-v1"
            and data.get("base_manifest_sha256") == BASE_DATA_SHA and data.get("base_training_rows") == 2047
            and rows == 2047 + added and verified <= calls
            and data.get("selection_sha256") == SELECTION_SHA and data.get("holdout_sha256") == HOLDOUT_SHA
            and data.get("reserved_intermediate_check") == "exact_closed_AST_plus_declared_template_exclusions"
            and data.get("teacher_source_scope") == "complete_teacher_proposed_native_continuation"
            and data.get("regenerated_byte_exact") is True and data.get("base_train_prefix_preserved") is True
            and data.get("validation_test_unchanged") is True
            and valid_sha(data.get("teacher_model_manifest_sha256")) and valid_sha(data.get("manifest_sha256"))
            and valid_sha(plan.get("config_sha256")), "Zero/unadmitted/changed teacher data cannot reserve a student update.")
    require(plan.get("config", {}).get("run", {}).get("output_dir") == ARTIFACT
            and plan["config"].get("data", {}).get("train_path") == CYCLE + "/dataset/primitive-train.jsonl"
            and plan["config"]["data"].get("eval_path") == CYCLE + "/dataset/primitive-val.jsonl",
            "Plan paths differ from the single declared student artifact/dataset.")
    if spec is not None:
        require(plan["plan_sha256"] == spec["plan_sha256"] and plan["config_sha256"] == spec["config_sha256"]
                and data["manifest_sha256"] == spec["dataset_sha256"] and rows == spec["training_rows"]
                and steps == spec["expected_optimizer_steps"], "The reserved student plan changed.")
    return rows, steps


def make_spec(plan, *, config_sha256, dataset_sha256, plan_file_sha256,
              source_manifest_sha256, source_archive_sha256, base_identity_sha256,
              seconds, soft_limit_seconds, nonce):
    rows, steps = validate_plan(plan)
    spec = {"schema":"hydra-p7-student-allocation-v1", "attempt":ATTEMPT,
        "job_name":"hydra-"+ATTEMPT, "nonce":nonce, "model_key":MODEL_KEY,
        "remote_job_directory":CAMPAIGN+"/jobs/"+ATTEMPT, "source":SOURCE,
        "account":ACCOUNT,"partition":PARTITION,"gpus":1,"nodes":1,"cpus":8,"memory_gib":64,
        "seconds":seconds,"soft_limit_seconds":soft_limit_seconds,
        "source_manifest_sha256":source_manifest_sha256,"source_archive_sha256":source_archive_sha256,
        "source_pins_sha256":SOURCE_MAP_SHA,"controller_sha256":TRAINER_SHA,"provider_sha256":PROVIDER_SHA,
        "config_sha256":config_sha256,"dataset_sha256":dataset_sha256,
        "plan_sha256":plan["plan_sha256"],"plan_file_sha256":plan_file_sha256,
        "base_identity_sha256":base_identity_sha256,"training_rows":rows,"validation_rows":432,
        "expected_optimizer_steps":steps,"submit_held":True,"automatic_retry":False,"resume":False,"requeue":False}
    validate_spec(spec); validate_plan(plan, spec)
    return spec


def validate_spec(spec):
    require(type(spec) is dict and spec.get("schema") == "hydra-p7-student-allocation-v1", "Wrong student allocation schema.")
    expected = {"attempt":ATTEMPT,"job_name":"hydra-"+ATTEMPT,"model_key":MODEL_KEY,
        "remote_job_directory":CAMPAIGN+"/jobs/"+ATTEMPT,"source":SOURCE,
        "account":ACCOUNT,"partition":PARTITION,"gpus":1,"nodes":1,"cpus":8,"memory_gib":64,
        "source_pins_sha256":SOURCE_MAP_SHA,"controller_sha256":TRAINER_SHA,"provider_sha256":PROVIDER_SHA,
        "validation_rows":432,"submit_held":True,"automatic_retry":False,"resume":False,"requeue":False}
    dynamic = {"schema","nonce","seconds","soft_limit_seconds","source_manifest_sha256","source_archive_sha256",
        "config_sha256","dataset_sha256","plan_sha256","plan_file_sha256","base_identity_sha256",
        "training_rows","expected_optimizer_steps"}
    require(set(spec) == set(expected) | dynamic
            and all(type(spec.get(k)) is type(v) and spec[k] == v for k,v in expected.items()),
            "Unknown fields or changed fixed student identity/resources.")
    durations(spec["seconds"], spec["soft_limit_seconds"])
    require(type(spec["nonce"]) is str and re.fullmatch(r"[0-9a-f]{32}", spec["nonce"])
            and all(valid_sha(spec[k]) for k in spec if k.endswith("_sha256")), "Missing exact nonce/input pin.")
    rows = integer(spec["training_rows"], 2048, 4096, "teacher training rows")
    require(type(spec["expected_optimizer_steps"]) is int and spec["expected_optimizer_steps"] == (rows+7)//8,
            "Reserved steps differ from one pass over all admitted rows.")


def reservation(spec, job_id, uid):
    validate_spec(spec)
    require(type(job_id) is str and re.fullmatch(r"[0-9]{1,20}", job_id), "Invalid scalar job id.")
    integer(uid, 1, 2**32-1, "uid")
    return {"schema":"hydra-p7-student-update-reservation-v1","job_id":job_id,"uid":uid,
        **{k:spec[k] for k in ("job_name","nonce","account","partition","model_key","gpus","nodes","cpus",
        "memory_gib","seconds","soft_limit_seconds","config_sha256","dataset_sha256","plan_sha256",
        "controller_sha256","source_pins_sha256")}}


def job_script(spec):
    validate_spec(spec)
    job = spec["remote_job_directory"]
    argv = [PROJECT+"/.venv-helios/bin/python","-B",SOURCE+"/"+TRAINER,
        "--reservation",job+"/reservation.json","--reservation-sha256","RESERVATION_SHA_PLACEHOLDER",
        "--config",SOURCE+"/"+CONFIG,"--dataset-manifest",SOURCE+"/"+DATA,
        "--base-directory",CAMPAIGN+"/authenticated-bases-01/"+MODEL_KEY,"--output",job+"/result"]
    invocation = shlex.join(argv).replace("RESERVATION_SHA_PLACEHOLDER", '"$HYDRA_STUDENT_RESERVATION_SHA"')
    return "\n".join(["#!/bin/bash -l","set -euo pipefail","set -C","umask 077","module purge",
        "module load ML-bundle/25.10","unset PYTHONPATH","export PYTHONHASHSEED=20260904",
        "export PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1","export HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1",
        "export TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=8","cd "+shlex.quote(SOURCE),
        "read -r HYDRA_STUDENT_RESERVATION_SHA < "+shlex.quote(job+"/reservation.sha256"),
        "set +e",invocation,"HYDRA_STUDENT_ACTUAL_EXIT=$?","set -e",
        "printf '%s\\n' \"$HYDRA_STUDENT_ACTUAL_EXIT\" > "+shlex.quote(job+"/actual-process-exit.txt"),
        'exit "$HYDRA_STUDENT_ACTUAL_EXIT"',""])


def verify_inputs(spec):
    values = {}
    for name, expected in ((CONFIG,spec["config_sha256"]),(DATA,spec["dataset_sha256"]),(PLAN,spec["plan_file_sha256"])):
        raw = ordinary_bytes(Path(SOURCE)/name, 2*1024**2)
        require(digest(raw) == expected, "Current config/data/admitted-plan bytes changed.")
        if name != CONFIG:
            values[name] = json.loads(raw)
    plan, data = values[PLAN], values[DATA]
    validate_plan(plan, spec)
    require(data.get("schema") == "hydra-teacher-augmented-primitive-dataset-v1"
            and data.get("status") == "complete" and data.get("training_allowed") is True
            and data.get("base_rows_preserved") == 2047 and data.get("training_rows") == spec["training_rows"]
            and data.get("teacher_rows_added") == spec["training_rows"]-2047
            and data.get("source_pins") == plan["data_attestation"]["source_pins"],
            "No matching complete nonzero admitted dataset supports this student.")
    return plan


def verify_sources(spec, source_map, *, fresh=True):
    require(type(source_map) is dict and len(source_map) == 595
            and digest(canonical(source_map)) == SOURCE_MAP_SHA, "Unexpected student source scope.")
    raw_manifest = ordinary_bytes(Path(SOURCE).parent/"manifest.json", 2*1024**2)
    manifest = json.loads(raw_manifest)
    require(digest(raw_manifest) == spec["source_manifest_sha256"]
            and manifest.get("archive_sha256") == spec["source_archive_sha256"], "New derived package manifest changed.")
    total = 0
    for name, expected in source_map.items():
        require(name in manifest["files"] and manifest["files"][name] == expected, "Derived inventory/source map differs.")
        raw = ordinary_bytes(Path(SOURCE)/name, 4*1024**2)
        total += len(raw)
        require(total <= 32*1024**2 and len(raw) == expected["bytes"] and digest(raw) == expected["sha256"],
                "Pinned student controller source changed.")
    plan = verify_inputs(spec)
    target = Path(SOURCE)/ARTIFACT
    require(not fresh or not (target.exists() or target.is_symlink()), "Student artifact already exists; no resume/retry.")
    return plan


def hash_saved_artifact(manifest):
    """Bounded byte verification only. No safetensors parsing or model loading."""
    root = Path(SOURCE)/ARTIFACT
    total, count, output = 0, 0, {}
    for group in ("adapter","tokenizer"):
        expected = manifest.get(group) or {}
        require(set(expected) == {"root","sha256","files"} and expected["root"] == group
                and type(expected["files"]) is dict and 1 <= len(expected["files"]) <= 64,
                "Invalid closed saved artifact inventory.")
        pending, paths, directories, entries = [root/group], {}, {}, 0
        while pending:
            directory = pending.pop()
            require(directory.resolve(strict=True) == directory and directory.is_dir(), "Saved artifact directory is not ordinary.")
            directories[directory] = directory.lstat()
            with os.scandir(directory) as stream:
                for item in stream:
                    entries += 1
                    require(entries <= 128 and not item.is_symlink(), "Saved artifact tree exceeds its bound or contains a symlink.")
                    path = Path(item.path)
                    if item.is_dir(follow_symlinks=False):
                        pending.append(path)
                    else:
                        require(item.is_file(follow_symlinks=False), "Saved artifact contains a special file.")
                        paths[path.relative_to(root).as_posix()] = path
                        require(len(paths) <= 64, "Saved file count exceeded.")
        require(set(paths) == set(expected["files"]), "Saved artifact inventory is incomplete or has extra files.")
        if group == "adapter":
            require(sorted(n for n in paths if n.endswith(".safetensors")) == ["adapter/adapter_model.safetensors"]
                    and not any(Path(n).suffix.lower() in {".bin",".pt",".pth",".pkl",".pickle"} for n in paths),
                    "Adapter must use its one safe saved weights file.")
        hashes = {}
        for name, path in sorted(paths.items()):
            before = path.lstat()
            require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path
                    and before.st_size <= 128*1024**2, "Saved artifact file exceeds its byte bound.")
            total += before.st_size; count += 1
            require(total <= 256*1024**2 and count <= 128, "Saved artifact total exceeds its byte/count bound.")
            value = hashlib.sha256()
            remaining, consumed = before.st_size+1, 0
            with path.open("rb") as stream:
                while True:
                    block = stream.read(min(1024*1024,remaining))
                    if not block:
                        break
                    remaining -= len(block); consumed += len(block)
                    value.update(block)
            after = path.lstat()
            require(consumed == before.st_size and all(getattr(before,k) == getattr(after,k) for k in ("st_dev","st_ino","st_size","st_mtime_ns","st_ctime_ns")),
                    "Saved file changed during collection hashing.")
            hashes[name] = value.hexdigest()
        require(hashes == expected["files"] and digest(canonical(hashes)) == expected["sha256"], "Saved artifact file hashes differ.")
        for directory, before in directories.items():
            after = directory.lstat()
            require(all(getattr(before,k) == getattr(after,k) for k in ("st_dev","st_ino","st_size","st_mtime_ns","st_ctime_ns")),
                    "Saved artifact inventory changed during hashing.")
        output[group] = expected
    return {"status":"verified_bytes_not_loaded","bytes_hashed":total,"files_hashed":count,
            "groups":output,"tensor_reload_performed":False,"model_calls":0}


def collect(phase, spec, source_map, record):
    require(record == reservation(spec, record.get("job_id"), os.getuid()), "Collection reservation identity differs.")
    roots = {"job":Path(spec["remote_job_directory"]),"artifact":Path(SOURCE)/ARTIFACT}
    result = {"job_id":record["job_id"],"read_only":True,"scheduler":{},"files":{},
        "artifact_byte_verification":{"status":"not_checked_incomplete_or_running","tensor_reload_performed":False}}
    result["scheduler"]["sacct"] = phase.run(["sacct","-n","-P","-j",record["job_id"],"--format="+SACCT_FORMAT], must_succeed=False)
    result["scheduler"]["scontrol"] = phase.run(["scontrol","-o","show","job",record["job_id"]], must_succeed=False)
    total = 0
    for name in FILES:
        prefix, relative = name.split("/",1)
        row = snapshot(roots[prefix]/relative, tail=name in TAILS)
        if row is not None:
            total += row["bytes"]
            require(total <= MAX_OBSERVATION, "Student observation exceeds its finite byte bound.")
            result["files"][name] = row
    try:
        exit_row, saved = result["files"].get("job/actual-process-exit.txt",{}), result["files"].get("artifact/manifest.json",{})
        query = result["scheduler"]["sacct"]
        rows = [line.split("|") for line in query["stdout_stderr"].splitlines() if line.split("|",1)[0] == record["job_id"]]
        terminal = query["actual_exit_code"] == 0 and query["stop_reason"] is None and len(rows) == 1 and len(rows[0]) == 14 and rows[0][5:7] == ["COMPLETED","0:0"]
        if terminal and exit_row.get("complete_file") is True and base64.b64decode(exit_row["base64"],validate=True).strip() == b"0" and saved.get("complete_file") is True:
            plan = verify_sources(spec, source_map, fresh=False)
            result["admitted_plan_check"] = {"status":"verified_current_pins","plan_sha256":plan["plan_sha256"],
                "plan_file_sha256":spec["plan_file_sha256"],"expected_optimizer_steps":plan["expected_optimizer_steps"]}
            artifact = json.loads(base64.b64decode(saved["base64"],validate=True))
            result["artifact_byte_verification"] = hash_saved_artifact(artifact)
            require(snapshot(roots["artifact"]/"manifest.json",tail=False)["sha256"] == saved["sha256"], "Manifest changed during saved-file hashing.")
    except TimeoutError:
        raise
    except (ValueError,KeyError,TypeError,OSError) as error:
        result["artifact_byte_verification"] = {"status":"rejected","error":str(error)[:1024],"tensor_reload_performed":False}
    return result


def main():
    os.umask(0o077)
    phase = Phase()
    response = {"schema":"hydra-p7-student-control-phase-v1","completed":False,"error":None,
                "automatic_retry":False,"commands":phase.commands}
    def deadline(_signum,_frame):
        raise TimeoutError("Bounded student control phase expired.")
    signal.signal(signal.SIGALRM,deadline); signal.alarm(int(PHASE_WALL)+5)
    try:
        raw = sys.stdin.buffer.read(MAX_INPUT+1)
        require(len(raw) <= MAX_INPUT, "Control input exceeds its bound.")
        request = json.loads(raw)
        require(type(request) is dict and request.get("phase") in {"submit","release","collect"}, "Unknown phase.")
        expected = {"phase","spec","source_map"} | ({"reservation"} if request["phase"] != "submit" else set())
        require(set(request) == expected, "Unexpected student request fields.")
        spec = request["spec"]; validate_spec(spec); response["phase"] = request["phase"]
        if request["phase"] == "submit":
            response["result"] = submit(phase,spec,request["source_map"])
        elif request["phase"] == "release":
            response["result"] = release(phase,spec,request["source_map"],request["reservation"])
        else:
            response["result"] = collect(phase,spec,request["source_map"],request["reservation"])
        response["completed"] = request["phase"] != "release" or response["result"]["released"]
    except BaseException as error:
        response["error"] = type(error).__name__+": "+str(error)[:2048]
    finally:
        signal.alarm(0)
    raw = canonical(response)
    require(len(raw) <= 14*1024**2, "Encoded response exceeds its bound.")
    sys.stdout.buffer.write(raw+b"\n")
    return 0 if response["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
