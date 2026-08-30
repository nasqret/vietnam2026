#!/usr/bin/env bash
# Dedicated, explicitly authorized evaluation-only recovery. Never sync, train,
# install, cancel, poll, refund reservations, or retry submissions automatically.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)"
repo_root="$(cd "$script_dir/.." && pwd -P)"

if [ "${1:-}" = --remote-gate ]; then
  shift
  # Standard system Python only: metadata checks on the x86 login node must not
  # load the existing ARM ML runtime. This code also runs before job module load.
  exec /usr/bin/python3 - "$repo_root" "$@" <<'PY'
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import selectors
import stat
import subprocess
import sys
import time

JOB = "slurm/peano_hydra_authority_scale_evaluate_recovery.sbatch"
LAUNCHER = "scripts/helios_hydra_evaluation_recovery.sh"
JOB_NAME = "peano-hydra-authority-scale-evaluate-recovery"
LEDGER = "logs/hydra-evaluation-recovery-20260828.jsonl"
LOCK = "logs/.hydra-evaluation-recovery-20260828.lock"
RUNS = "results/peano-hydra/evaluations/authority-scale-evaluation-recovery"
OLD = "results/peano-hydra/qwen3-1.7b-alpha-v25-a96223a021ed-capacity-fit-v1"
NEW = "results/peano-hydra/qwen3-1.7b-authority-primitive-v25-a96223a021ed-authority-scale-v1-attempt2"
OLD_SHA = "723d0f8109c0272774f445c552d781c8e64cadfa50d0516246eb0fa2fd31a955"
NEW_SHA = "e3c569796be42cdfb3afd677c3c6c1a6e82c67728b8410a410034c35791d20a4"
CAP = 7200
MAX_LEDGER = 512 * 1024
SUBMISSION_HEADER = "timestamp\tjob_id\tscript\tdependency_job_id\tworkdir\tgit_commit\tgit_dirty\tsync_timestamp\tscript_sha256\n"
IDENTIFIER = re.compile(r"[a-z][a-z0-9-]{0,47}\Z")
HEX40 = re.compile(r"[0-9a-f]{40}\Z")
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
TERMINAL = {"COMPLETED", "FAILED", "CANCELLED", "TIMEOUT", "OUT_OF_MEMORY", "NODE_FAIL", "PREEMPTED", "BOOT_FAIL", "DEADLINE", "REVOKED"}
# One explicitly user-approved continuation, not a general failed-job reset.
# The original 1200-second charge and all five exact ledger events stay intact.
SETUP_FAILURE_JOB = "21388894"
SETUP_FAILURE_REQUEST = "eval-recovery-01"
SETUP_CONTINUATION_REQUEST = "eval-recovery-02"
SETUP_FAILURE_PREFIX_SHA = "00ff67aa6edbb44acf4d4326fe4298afcffd108679e7163405959d32e62b8117"
SETUP_FAILURE_SOURCE = {
    "commit": "b1e886bcd02e7f2d9aeba63e806bb561bbc61c3b",
    "launcher_sha256": "90711d4daf6573f7f113450d766b67bf643d3b859aa4ee975ebef5d370ad46d5",
    "script_sha256": "7500f797b840ae51fb3e1dab141d6e7f2ec103aa911c70da77f257b412f742f6",
    "provenance_sha256": "2b7e4e07e41dc5cb15b4c239354279f4acacdb2a12276f455f4dc5434489597a",
    "synced_at": "2026-08-28T09:09:13Z",
}
SETUP_FAILURE_FILES = {
    "logs/peano-hydra-authority-scale-evaluate-recovery-21388894.out":
        "8f1335aeb0095337aa12ee759590b7f6412a0dfa9c5e691c7c7e224798867b45",
    "logs/peano-hydra-authority-scale-evaluate-recovery-21388894.err":
        "e4194c31077d13472e2eaa70e417632bc4d2799178dc92f33432d59a11d9ca3d",
    RUNS + "/eval-recovery-01/request.json":
        "88fcaec6cd1e6ee8e2247ef9094db167d46b42f22f7973756e076cbbc11428a2",
}
SETUP_FAILURE_ACCOUNTING = {
    "job_id": "21388894", "state": "FAILED", "exit_code": "2:0",
    "elapsed_seconds": 4, "requested_minutes": 20,
    "start": "2026-08-28T11:20:06", "end": "2026-08-28T11:20:10",
    "timezone": "Europe/Warsaw",
    "allocated_resources": "billing=1,cpu=8,gres/gpu=1,mem=64G,node=1",
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False, separators=(",", ":")).encode("ascii")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def object_pairs(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate ledger JSON key")
        result[key] = value
    return result


def decode(raw):
    return json.loads(raw.decode("utf-8"), object_pairs_hook=object_pairs,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("non-finite JSON")))


ROOT = Path(sys.argv[1]).resolve(strict=True)
require("SCRATCH" in os.environ, "SCRATCH is required by the fixed remote project")
expected_root = (Path(os.environ["SCRATCH"]) / "codex-control/projects/peano-lab-training").resolve(strict=True)
require(ROOT == expected_root and ROOT.is_dir(), "recovery gate must run in its fixed Helios project")


def path(relative, create_parents=False):
    pieces = relative.split("/")
    require(pieces and all(piece not in {"", ".", ".."} for piece in pieces), "unsafe recovery path")
    current = ROOT
    for index, piece in enumerate(pieces):
        current = current / piece
        require(not current.is_symlink(), "recovery path contains a symlink: " + relative)
        if index != len(pieces) - 1:
            if create_parents and not current.exists():
                current.mkdir(mode=0o700)
            require(current.is_dir(), "recovery parent is not a regular directory: " + relative)
    return current


def read(relative, maximum):
    target = path(relative)
    descriptor = os.open(str(target), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_size <= maximum, "oversized/nonregular recovery input: " + relative)
        raw = stream.read(maximum + 1)
        after = os.fstat(stream.fileno())
    require(len(raw) <= maximum and (before.st_ino, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_size, after.st_mtime_ns), "recovery input changed during read")
    return raw


def fresh(relative, raw):
    target = path(relative, create_parents=True)
    descriptor = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(str(target.parent), os.O_RDONLY)
    try:
        os.fsync(directory)
    finally:
        os.close(directory)


def source():
    raw = read(".peano-source-provenance.tsv", 1024)
    match = re.fullmatch(rb"([0-9a-f]{40})\tfalse\t([0-9TZ:+-]+)\n", raw)
    require(match is not None, "one explicitly clean committed source-provenance row is required")
    return {"commit": match.group(1).decode(), "synced_at": match.group(2).decode(),
            "provenance_sha256": hashlib.sha256(raw).hexdigest(),
            "launcher_sha256": hashlib.sha256(read(LAUNCHER, 128 * 1024)).hexdigest(),
            "script_sha256": hashlib.sha256(read(JOB, 32 * 1024)).hexdigest()}


def pinned_manifests():
    for directory, wanted in ((OLD, OLD_SHA), (NEW, NEW_SHA)):
        require(hashlib.sha256(read(directory + "/manifest.json", 2 * 1024 * 1024)).hexdigest() == wanted,
                "the exact completed old/new adapter manifest is required: " + directory)
    # The comparison CLI independently verifies full preparation, adapter,
    # tokenizer and training evidence before any model is loaded. No weights
    # are read by this small reservation gate.


def run(arguments, poland_time=False):
    environment = None
    if poland_time:
        environment = dict(os.environ, TZ="Europe/Warsaw", SLURM_TIME_FORMAT="standard")
    process = subprocess.Popen(arguments, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment)
    selector = selectors.DefaultSelector()
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    deadline = time.monotonic() + 30
    try:
        while selector.get_map():
            require(time.monotonic() < deadline, "scheduler metadata command exceeded 30 seconds")
            for key, unused in selector.select(min(0.5, max(0, deadline - time.monotonic()))):
                chunk = os.read(key.fileobj.fileno(), 65536)
                if not chunk:
                    selector.unregister(key.fileobj)
                    continue
                buffers[key.data].extend(chunk)
                require(sum(map(len, buffers.values())) <= 1024 * 1024, "scheduler metadata exceeds 1 MiB")
        status = process.wait(timeout=max(0.1, deadline - time.monotonic()))
        require(status == 0, "scheduler command failed: " + arguments[0] + ": " + buffers["stderr"].decode("utf-8", "replace")[:1000])
        return buffers["stdout"].decode("utf-8", "strict")
    finally:
        selector.close()
        if process.poll() is None:
            process.kill()
            process.wait(timeout=5)


def submissions():
    target = path("logs/submissions.tsv")
    if not target.exists():
        return []
    raw = read("logs/submissions.tsv", 1024 * 1024).decode("utf-8")
    require(raw.startswith(SUBMISSION_HEADER) and raw.endswith("\n"), "project submission ledger is malformed")
    rows = [line.split("\t") for line in raw.splitlines()[1:]]
    require(all(len(row) == 9 for row in rows), "project submission row is malformed")
    return rows


def header(identity):
    return {"kind": "authorization", "schema": "peano-hydra-evaluation-reservation-v1",
            "authorization": "additional-two-GPU-hours-evaluation-only-2026-08-28",
            "budget_seconds": CAP, "previous_adapter_manifest_sha256": OLD_SHA,
            "trained_adapter_manifest_sha256": NEW_SHA, "execution_source_commit": identity["commit"],
            "launcher_sha256": identity["launcher_sha256"], "script_sha256": identity["script_sha256"]}


def setup_amendment(identity):
    require(identity["commit"] != SETUP_FAILURE_SOURCE["commit"]
            and identity["launcher_sha256"] != SETUP_FAILURE_SOURCE["launcher_sha256"]
            and identity["script_sha256"] == SETUP_FAILURE_SOURCE["script_sha256"],
            "setup continuation requires revised clean source and the unchanged reviewed sbatch")
    return {
        "kind": "acknowledged-setup-failure-source-amendment",
        "authorization": "user-approved-permission-respecting-21388894-setup-continuation-only",
        "failed_job_id": SETUP_FAILURE_JOB, "failed_request_id": SETUP_FAILURE_REQUEST,
        "original_ledger_prefix_sha256": SETUP_FAILURE_PREFIX_SHA,
        "original_source": SETUP_FAILURE_SOURCE, "revised_source": identity,
        "evidence_files": SETUP_FAILURE_FILES, "accounting": SETUP_FAILURE_ACCOUNTING,
        "old_directory_entries": ["request.json"], "evaluation_goals_started": 0,
        "model_loaded": False, "checkpoint_created": False, "report_created": False,
        "original_reservation_preserved_seconds": 1200, "reservation_refunded": False,
        "next_request_id": SETUP_CONTINUATION_REQUEST, "next_reservation_seconds": 6000,
        "total_authorized_seconds": CAP,
    }


def setup_failure_evidence(state, live_accounting):
    require(state["setup_failure_prefix"] and state["requests"].get(SETUP_FAILURE_REQUEST, {}).get("seconds") == 1200
            and state["accepted"].get(SETUP_FAILURE_REQUEST) == SETUP_FAILURE_JOB
            and SETUP_FAILURE_REQUEST in state["started"],
            "setup continuation lost the exact original started reservation")
    directory = path(RUNS + "/" + SETUP_FAILURE_REQUEST)
    require(directory.is_dir(), "original setup-failure output directory is unavailable")
    names = []
    with os.scandir(str(directory)) as entries:
        for entry in entries:
            names.append(entry.name)
            require(len(names) <= 1 and entry.name == "request.json" and not entry.is_symlink()
                    and entry.is_file(follow_symlinks=False),
                    "setup failure has checkpoint/report/progress or unexpected output; fresh continuation forbidden")
    require(names == ["request.json"], "setup failure must retain exactly its original request and no evaluation progress")
    for relative, wanted in SETUP_FAILURE_FILES.items():
        require(hashlib.sha256(read(relative, 65536)).hexdigest() == wanted,
                "setup failure evidence changed: " + relative)
    require(decode(read(RUNS + "/" + SETUP_FAILURE_REQUEST + "/request.json", 16384))
            == state["requests"][SETUP_FAILURE_REQUEST], "setup failure request no longer matches its reservation")
    if live_accounting:
        text = run(["sacct", "--noheader", "--parsable2", "--allocations", "--jobs", SETUP_FAILURE_JOB,
                    "--format=JobIDRaw,State,ExitCode,ElapsedRaw,TimelimitRaw,Start,End,AllocTRES"], poland_time=True)
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        require(len(lines) == 1, "setup failure requires one exact allocation accounting row")
        fields = lines[0].split("|")
        if len(fields) == 9 and not fields[-1]:
            fields.pop()
        expected = [SETUP_FAILURE_JOB, "FAILED", "2:0", "4", "20",
                    SETUP_FAILURE_ACCOUNTING["start"], SETUP_FAILURE_ACCOUNTING["end"],
                    SETUP_FAILURE_ACCOUNTING["allocated_resources"]]
        require(fields == expected, "setup failure accounting differs from the approved pre-model failure")


def load_ledger(identity, acknowledge_setup_failure=False):
    raw = read(LEDGER, MAX_LEDGER)
    require(raw.endswith(b"\n"), "reservation ledger has an incomplete event; manual review required")
    lines = raw.splitlines(keepends=True)
    require(1 <= len(lines) <= 482, "reservation ledger exceeds its event bound")
    failure_prefix = len(lines) >= 5 and hashlib.sha256(b"".join(lines[:5])).hexdigest() == SETUP_FAILURE_PREFIX_SHA
    active_identity = SETUP_FAILURE_SOURCE if failure_prefix else identity
    state = {"events": [], "requests": {}, "accepted": {}, "released": set(), "started": set(), "seconds": 0,
             "setup_failure_prefix": failure_prefix, "setup_amendment": None}
    previous = "0" * 64
    for index, line in enumerate(lines):
        event = decode(line)
        require(type(event) is dict and set(event) == {"index", "previous_sha256", "payload", "sha256"}, "unknown reservation event fields")
        unsigned = {key: event[key] for key in ("index", "previous_sha256", "payload")}
        require(type(event["index"]) is int and event["index"] == index and event["previous_sha256"] == previous
                and event["sha256"] == digest(unsigned), "reservation event chain/hash changed")
        payload = event["payload"]
        require(type(payload) is dict, "reservation event payload is not an object")
        if index == 0:
            require(payload == header(active_identity), "reservation authorization/source/pins changed")
        elif payload.get("kind") == "reserve":
            require(set(payload) == {"kind", "request_id", "seconds", "resume_from", "checkpoint_request_id", "source", "created_at"}, "unknown reservation fields")
            request = payload["request_id"]
            require(type(request) is str and IDENTIFIER.fullmatch(request) and request not in state["requests"], "duplicate/invalid recovery request ID")
            seconds = payload["seconds"]
            require(type(seconds) is int and 60 <= seconds <= CAP and seconds % 60 == 0, "invalid GPU reservation")
            saved_source = payload["source"]
            require(type(saved_source) is dict and set(saved_source) == set(active_identity)
                    and all(saved_source[key] == active_identity[key] for key in ("commit", "launcher_sha256", "script_sha256"))
                    and type(saved_source["synced_at"]) is str and re.fullmatch(r"[0-9TZ:+-]+", saved_source["synced_at"])
                    and type(saved_source["provenance_sha256"]) is str and HEX64.fullmatch(saved_source["provenance_sha256"]), "reservation lost its exact clean source")
            require(type(payload["created_at"]) is str and re.fullmatch(r"[0-9TZ:+-]+", payload["created_at"]), "reservation timestamp is malformed")
            resume = payload["resume_from"]
            if resume is None:
                require(payload["checkpoint_request_id"] == request, "fresh request changed its checkpoint root")
            else:
                require(type(resume) is str and resume in state["requests"] and resume in state["released"]
                        and payload["checkpoint_request_id"] == state["requests"][resume]["checkpoint_request_id"], "resume is not bound to its earlier reservation")
            if state["setup_amendment"] is not None:
                require(resume is None and request == SETUP_CONTINUATION_REQUEST and seconds == 6000 and index == 6
                        and state["seconds"] == 1200, "setup amendment permits only its one exact fresh 6000-second continuation")
            state["requests"][request] = payload
            state["seconds"] += seconds
            require(state["seconds"] <= CAP, "cumulative additional GPU reservation exceeds 7200 seconds")
        elif payload.get("kind") == "acknowledged-setup-failure-source-amendment":
            require(index == 5 and failure_prefix and state["setup_amendment"] is None
                    and set(state["requests"]) == {SETUP_FAILURE_REQUEST} and state["seconds"] == 1200
                    and state["accepted"] == {SETUP_FAILURE_REQUEST: SETUP_FAILURE_JOB}
                    and state["released"] == state["started"] == {SETUP_FAILURE_REQUEST},
                    "setup amendment cannot reset arbitrary failed or partially evaluated work")
            require(payload == setup_amendment(identity), "setup amendment changed its approved case/source/evidence")
            state["setup_amendment"] = payload
            active_identity = identity
        elif payload.get("kind") in {"accepted", "release-authorized", "started"}:
            kind, request = payload["kind"], payload.get("request_id")
            require(set(payload) == {"kind", "request_id", "job_id"} and request in state["requests"]
                    and type(payload["job_id"]) is str and re.fullmatch(r"[1-9][0-9]*", payload["job_id"]), "invalid reservation job event")
            if kind == "accepted":
                require(request not in state["accepted"] and payload["job_id"] not in state["accepted"].values(), "duplicate accepted recovery job")
                state["accepted"][request] = payload["job_id"]
            else:
                target = state["released"] if kind == "release-authorized" else state["started"]
                require(state["accepted"].get(request) == payload["job_id"] and request not in target
                        and (kind != "started" or request in state["released"]), "recovery job was released/started twice or out of order")
                target.add(request)
        else:
            raise ValueError("unknown reservation event")
        previous = event["sha256"]
        state["events"].append(event)
    if failure_prefix and state["setup_amendment"] is None:
        require(acknowledge_setup_failure and len(lines) == 5,
                "changed execution source requires explicit acknowledgement of the exact setup-only failure")
        setup_amendment(identity)
    else:
        require(not acknowledge_setup_failure, "setup-failure acknowledgement applies only once to its original five events")
    require(not acknowledge_setup_failure or failure_prefix, "setup acknowledgement does not match the frozen failure ledger")
    return state


def append(state, payload):
    event = {"index": len(state["events"]), "previous_sha256": state["events"][-1]["sha256"] if state["events"] else "0" * 64,
             "payload": payload}
    event["sha256"] = digest(event)
    raw = canonical(event) + b"\n"
    target = path(LEDGER)
    require(target.stat().st_size + len(raw) <= MAX_LEDGER, "reservation ledger byte limit exceeded")
    descriptor = os.open(str(target), os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "ab") as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "reservation ledger is not regular")
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    state["events"].append(event)


def queue_and_history(state):
    user = os.environ.get("USER", "")
    require(re.fullmatch(r"[A-Za-z0-9_.-]+", user) is not None, "USER is required for scheduler ownership checks")
    queued = run(["squeue", "--noheader", "--user", user, "--format=%i|%j|%Z"])
    for line in queued.splitlines():
        if not line.strip():
            continue
        parts = line.strip().split("|")
        require(len(parts) == 3, "ambiguous scheduler queue metadata")
        require(parts[1] != JOB_NAME and parts[2] != str(ROOT) and not parts[2].startswith(str(ROOT) + "/"),
                "an active project/recovery job already owns the source or GPU")
    history = run(["sacct", "--noheader", "--parsable2", "--allocations", "--user", user,
                   "--starttime", "2026-08-28", "--format=JobIDRaw,JobName%100,State"])
    rows = {}
    for line in history.splitlines():
        if not line.strip():
            continue
        parts = line.strip().split("|")
        if len(parts) == 4 and not parts[-1]:
            parts.pop()
        require(len(parts) == 3 and parts[2].strip(), "ambiguous scheduler accounting metadata")
        if parts[1] != JOB_NAME:
            continue
        require(re.fullmatch(r"[1-9][0-9]*", parts[0]) and parts[0] not in rows, "duplicate/invalid recovery accounting row")
        rows[parts[0]] = parts[2].split()[0].rstrip("+")
    wanted = set(state["accepted"].values())
    require(set(rows) == wanted, "scheduler recovery history and reservation ledger differ; manual review required")
    require(all(value in TERMINAL for value in rows.values()), "a previous recovery allocation is not terminal")
    project_rows = [row for row in submissions() if row[2] == JOB]
    require(len(project_rows) == len(wanted) and {row[1] for row in project_rows} == wanted,
            "project submission history and recovery reservations differ")
    for row in project_rows:
        request = next(key for key, value in state["accepted"].items() if value == row[1])
        saved = state["requests"][request]["source"]
        require(row[3] == "" and row[4] == str(ROOT) and row[5] == saved["commit"] and row[6] == "false"
                and row[7] == saved["synced_at"] and row[8] == saved["script_sha256"], "recovery submission lost its source binding")


def main(arguments):
    job_check = arguments and arguments[0] == "--job-check"
    acknowledge_setup_failure = False
    identity = source()
    if job_check:
        require(len(arguments) == 3 and IDENTIFIER.fullmatch(arguments[1])
                and re.fullmatch(r"[1-9][0-9]*", arguments[2]), "invalid job reservation check")
        request, job_id = arguments[1:]
        require(os.environ.get("SLURM_JOB_ID") == job_id and os.environ.get("SLURM_RESTART_COUNT", "0") == "0",
                "job reservation requires its original Slurm allocation, never a restart")
        mode = "--job-check"
    else:
        require(len(arguments) in {9, 10}, "invalid remote recovery arguments")
        mode, commit, launcher_hash, script_hash, request, minutes, initialize, resume = arguments[:8]
        require(arguments[8] == "PEANO-HYDRA-EVALUATION", "explicit evaluation-only authorization is required")
        acknowledgement = arguments[9] if len(arguments) == 10 else "-"
        require(acknowledgement in {"-", SETUP_FAILURE_JOB}, "only the exact approved setup-failure job can be acknowledged")
        acknowledge_setup_failure = acknowledgement == SETUP_FAILURE_JOB
        require(mode in {"--test-only", "--submit"} and HEX40.fullmatch(commit)
                and HEX64.fullmatch(launcher_hash) and HEX64.fullmatch(script_hash)
                and IDENTIFIER.fullmatch(request) and re.fullmatch(r"[1-9][0-9]{0,2}", minutes)
                and 1 <= int(minutes) <= 120 and initialize in {"true", "false"}
                and (resume == "-" or IDENTIFIER.fullmatch(resume)), "malformed remote recovery request")
        require(identity["commit"] == commit and identity["launcher_sha256"] == launcher_hash
                and identity["script_sha256"] == script_hash, "remote source differs from the clean local freeze")
        require("SLURM_JOB_ID" not in os.environ, "submission gate cannot nest inside a scheduled job")
        require(not any(key.startswith("SBATCH_") for key in os.environ), "SBATCH_* overrides are not authorized")
        resume = None if resume == "-" else resume
        if acknowledge_setup_failure:
            require(request == SETUP_CONTINUATION_REQUEST and minutes == "100" and initialize == "false"
                    and resume is None, "setup continuation is only fresh eval-recovery-02 for the remaining 6000 seconds")
    pinned_manifests()
    lock_target = path(LOCK)
    descriptor = None
    try:
        if mode != "--test-only":
            flags = os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
            if not job_check:
                flags |= os.O_CREAT
            descriptor = os.open(str(lock_target), flags, 0o600)
            require(stat.S_ISREG(os.fstat(descriptor).st_mode), "reservation lock is not regular")
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        exists = path(LEDGER).exists()
        if exists:
            require(job_check or initialize == "false", "reservation ledger already exists; never reinitialize it")
            state = load_ledger(identity, acknowledge_setup_failure=acknowledge_setup_failure)
        else:
            require(not job_check and initialize == "true" and not acknowledge_setup_failure,
                    "missing reservation ledger; first launch requires --initialize-ledger")
            state = {"events": [], "requests": {}, "accepted": {}, "released": set(), "started": set(), "seconds": 0}
        if state.get("setup_amendment") is not None:
            setup_failure_evidence(state, live_accounting=False)
        if job_check:
            require(state["accepted"].get(request) == job_id and request in state["released"]
                    and request not in state["started"], "job has no unique unused accepted/released reservation")
            saved = state["requests"][request]
            require(saved["source"] == identity, "source changed after the reservation")
            run_directory = RUNS + "/" + request
            require(decode(read(run_directory + "/request.json", 16384)) == saved, "run directory lost its immutable reservation receipt")
            output = run_directory + "/comparison.json"
            require(not path(output).exists(), "final recovery output already exists")
            checkpoint = RUNS + "/" + saved["checkpoint_request_id"] + "/checkpoints"
            if saved["resume_from"] is None:
                require(not path(checkpoint).exists(), "fresh recovery checkpoint directory already exists")
            else:
                require(path(checkpoint).is_dir(), "resume checkpoint directory is unavailable")
            append(state, {"kind": "started", "request_id": request, "job_id": job_id})
            print("\t".join((str(saved["seconds"]), output, checkpoint, "true" if saved["resume_from"] else "false", OLD, NEW)))
            return
        require(all(key in state["accepted"] and key in state["released"] for key in state["requests"]),
                "an earlier submission is unconfirmed; reservation remains charged, inspect it manually")
        require(request not in state["requests"] and resume != request, "request IDs are unique and cannot resume themselves")
        seconds = int(minutes) * 60
        require(state["seconds"] + seconds <= CAP, "additional GPU reservation would exceed the cumulative 7200-second cap")
        queue_and_history(state)
        if acknowledge_setup_failure:
            require(len(state["events"]) == 5 and state["seconds"] == 1200,
                    "setup continuation must retain the exact original five-event 1200-second charge")
            setup_failure_evidence(state, live_accounting=True)
        require(not state["requests"] or resume is not None or acknowledge_setup_failure,
                "further recovery allocations must explicitly resume the same checkpoint; no fresh reset/retry")
        checkpoint_request = request
        if resume is not None:
            require(resume in state["requests"] and resume in state["released"], "resume requires a previous accepted recovery request")
            checkpoint_request = state["requests"][resume]["checkpoint_request_id"]
            require(path(RUNS + "/" + checkpoint_request + "/checkpoints").is_dir(), "resume checkpoint directory is unavailable")
        run_directory = RUNS + "/" + request
        # Missing output parents are allowed only for a fresh planned run.
        existing = ROOT / run_directory
        for parent in (ROOT / "results", ROOT / "results/peano-hydra", ROOT / "results/peano-hydra/evaluations", ROOT / RUNS, existing):
            require(not parent.is_symlink() and (not parent.exists() or parent.is_dir()), "unsafe recovery output parent")
        require(not existing.exists(), "recovery output directory must be fresh")
        wall = "%02d:%02d:00" % (int(minutes) // 60, int(minutes) % 60)
        options = ["sbatch", "--test-only" if mode == "--test-only" else "--parsable", "--hold", "--no-requeue",
                   "--account=plgccaiautore2026-gpu-gh200", "--partition=plgrid-gpu-gh200", "--nodes=1", "--ntasks=1",
                   "--cpus-per-task=8", "--mem=64G", "--gres=gpu:1", "--time=" + wall, "--export=ALL",
                   "--job-name=" + JOB_NAME, "--chdir=" + str(ROOT),
                   "--output=logs/peano-hydra-authority-scale-evaluate-recovery-%j.out",
                   "--error=logs/peano-hydra-authority-scale-evaluate-recovery-%j.err", JOB, request]
        if mode == "--test-only":
            run(options)
            print("recovery_status=test-only\nrequested_seconds=%d\npreviously_reserved_seconds=%d\nremaining_after_request=%d" %
                  (seconds, state["seconds"], CAP - state["seconds"] - seconds))
            return
        if not exists:
            event = {"index": 0, "previous_sha256": "0" * 64, "payload": header(identity)}
            event["sha256"] = digest(event)
            fresh(LEDGER, canonical(event) + b"\n")
            state["events"].append(event)
        path(run_directory, create_parents=True)
        existing.mkdir(mode=0o700)  # Exclusive final directory; never adopt one.
        reservation = {"kind": "reserve", "request_id": request, "seconds": seconds, "resume_from": resume,
                       "checkpoint_request_id": checkpoint_request, "source": identity,
                       "created_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"}
        fresh(run_directory + "/request.json", canonical(reservation) + b"\n")
        if acknowledge_setup_failure:
            append(state, setup_amendment(identity))  # Preserve, never replace, the original header/source.
        append(state, reservation)  # Charged and fsynced BEFORE any real sbatch.
        submission = run(options).strip()
        require(re.fullmatch(r"[1-9][0-9]*(?:;[A-Za-z0-9_-]+)?", submission),
                "sbatch returned no unique accepted ID; reservation remains charged")
        job_id = submission.split(";", 1)[0]
        require(job_id not in state["accepted"].values(), "scheduler repeated a prior recovery job ID")
        append(state, {"kind": "accepted", "request_id": request, "job_id": job_id})
        rows = submissions()
        require(not any(row[1] == job_id for row in rows), "accepted job already appears in project ledger")
        ledger_path = path("logs/submissions.tsv")
        if not ledger_path.exists():
            fresh("logs/submissions.tsv", SUBMISSION_HEADER.encode())
        row = [reservation["created_at"], job_id, JOB, "", str(ROOT), identity["commit"], "false", identity["synced_at"], identity["script_sha256"]]
        ledger_descriptor = os.open(str(ledger_path), os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW | os.O_NONBLOCK)
        require(stat.S_ISREG(os.fstat(ledger_descriptor).st_mode), "project submission ledger is not regular")
        with os.fdopen(ledger_descriptor, "ab") as stream:
            stream.write(("\t".join(row) + "\n").encode())
            stream.flush()
            os.fsync(stream.fileno())
        append(state, {"kind": "release-authorized", "request_id": request, "job_id": job_id})
        # Let the newly released job acquire its start guard without a race.
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)
        descriptor = None
        print("accepted_held_job_id=" + job_id, flush=True)
        run(["scontrol", "release", job_id])
        print("submitted job_id=%s\nrecovery_request=%s\nreserved_seconds=%d\ncumulative_reserved_seconds=%d\nreservation_ledger=%s\noutput_directory=%s" %
              (job_id, request, seconds, state["seconds"] + seconds, LEDGER, run_directory))
    finally:
        if descriptor is not None:
            os.close(descriptor)


try:
    main(sys.argv[2:])
except (ValueError, TypeError, OSError, RuntimeError, subprocess.SubprocessError) as error:
    print("hydra-evaluation-recovery: " + " ".join(str(error).split()), file=sys.stderr)
    print("No automatic retry/refund/cancellation. Inspect any held job and the reservation ledger before further action.", file=sys.stderr)
    sys.exit(2)
PY
fi

# shellcheck source=helios_common.sh
source "$script_dir/helios_common.sh"
usage() {
  printf 'usage: %s --request-id NAME [--minutes 1..120] [--initialize-ledger] [--resume-from NAME] [--test-only]\n' "$0" >&2
  printf '       %s <same options> --submit --confirm PEANO-HYDRA-EVALUATION\n' "$0" >&2
  printf '       one approved setup continuation: --request-id eval-recovery-02 --minutes 100 --acknowledge-setup-failure 21388894\n' >&2
}
mode=--test-only
mode_set=false
confirmation=""
request=""
minutes=120
minutes_set=false
initialize=false
resume=-
acknowledgement=-
while [ "$#" -gt 0 ]; do
  case "$1" in
    --test-only|--submit)
      [ "$mode_set" = false ] || { usage; exit 2; }
      mode="$1"; mode_set=true; shift ;;
    --confirm)
      [ "$#" -ge 2 ] && [ -z "$confirmation" ] || { usage; exit 2; }
      confirmation="$2"; shift 2 ;;
    --request-id)
      [ "$#" -ge 2 ] && [ -z "$request" ] || { usage; exit 2; }
      request="$2"; shift 2 ;;
    --minutes)
      [ "$#" -ge 2 ] && [ "$minutes_set" = false ] || { usage; exit 2; }
      minutes="$2"; minutes_set=true; shift 2 ;;
    --initialize-ledger)
      [ "$initialize" = false ] || { usage; exit 2; }
      initialize=true; shift ;;
    --resume-from)
      [ "$#" -ge 2 ] && [ "$resume" = - ] || { usage; exit 2; }
      resume="$2"; shift 2 ;;
    --acknowledge-setup-failure)
      [ "$#" -ge 2 ] && [ "$acknowledgement" = - ] || { usage; exit 2; }
      acknowledgement="$2"; shift 2 ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'unknown recovery option: %s\n' "$1" >&2; usage; exit 2 ;;
  esac
done
if [[ ! "$request" =~ ^[a-z][a-z0-9-]{0,47}$ ]] || \
   [[ ! "$minutes" =~ ^[1-9][0-9]{0,2}$ ]] || [ "$minutes" -gt 120 ] || \
   { [ "$resume" != - ] && [[ ! "$resume" =~ ^[a-z][a-z0-9-]{0,47}$ ]]; } || \
   [ "$resume" = "$request" ] || \
   { [ "$mode" = --test-only ] && [ -n "$confirmation" ]; } || \
   { [ "$mode" = --submit ] && [ "$confirmation" != PEANO-HYDRA-EVALUATION ]; }; then
  usage; exit 2
fi
if [ "$initialize" = true ] && [ "$resume" != - ]; then
  printf '%s\n' 'a new ledger cannot resume a previous recovery request' >&2; exit 2
fi
if [ "$acknowledgement" != - ] && { [ "$acknowledgement" != 21388894 ] || [ "$request" != eval-recovery-02 ] || \
   [ "$minutes" != 100 ] || [ "$initialize" != false ] || [ "$resume" != - ]; }; then
  printf '%s\n' 'only the exact approved setup failure permits a fresh 100-minute continuation' >&2; exit 2
fi
for option in $(compgen -e); do
  case "$option" in SBATCH_*) printf '%s\n' 'SBATCH_* overrides are not authorized' >&2; exit 2 ;; esac
done
git_root="$(git -C "$repo_root" rev-parse --show-toplevel)"
[ "$(cd "$git_root" && pwd -P)" = "$repo_root" ] || exit 2
commit="$(git -C "$repo_root" rev-parse HEAD)"
changes="$(git -C "$repo_root" status --porcelain --untracked-files=all)"
if [[ ! "$commit" =~ ^[0-9a-f]{40}$ ]] || [ -n "$changes" ]; then
  printf '%s\n' 'evaluation recovery requires clean committed local source; freeze it separately first' >&2; exit 2
fi
job=slurm/peano_hydra_authority_scale_evaluate_recovery.sbatch
test -f "$repo_root/$job" && test ! -L "$repo_root/$job"
if command -v sha256sum >/dev/null 2>&1; then
  launcher_sha="$(sha256sum "$script_dir/helios_hydra_evaluation_recovery.sh" | awk '{print $1}')"
  script_sha="$(sha256sum "$repo_root/$job" | awk '{print $1}')"
else
  launcher_sha="$(shasum -a 256 "$script_dir/helios_hydra_evaluation_recovery.sh" | awk '{print $1}')"
  script_sha="$(shasum -a 256 "$repo_root/$job" | awk '{print $1}')"
fi
[[ "$launcher_sha" =~ ^[0-9a-f]{64}$ && "$script_sha" =~ ^[0-9a-f]{64}$ ]] || exit 2
ssh_target="$(peano_helios_ssh_target)"
# All interpolated arguments have conservative fixed alphabets. Remote writes
# happen only with explicit --submit; --test-only never initializes the ledger.
exec ssh -o BatchMode=yes -o ConnectTimeout=15 "$ssh_target" \
  "bash -l -s -- $mode $commit $launcher_sha $script_sha $request $minutes $initialize $resume PEANO-HYDRA-EVALUATION $acknowledgement" <<'REMOTE'
set -euo pipefail
project_root="${SCRATCH:?SCRATCH is not defined}/codex-control/projects/peano-lab-training"
cd "$project_root"
exec bash scripts/helios_hydra_evaluation_recovery.sh --remote-gate "$@"
REMOTE
