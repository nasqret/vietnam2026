"""Single-use held corrective chain, compatible with login Python 3.6.

This module intentionally imports only the standard library. The remote gate
checks externally approved bytes, not native proofs or installed ARM modules.
Full workflow validation runs locally and again inside the allocated job.
Historical launch ledgers are never reset, refunded, or appended here.
"""

import argparse
import datetime
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).absolute().parents[2]
PROFILE = "peano-hydra-corrective-v2"
RUN_ID = "corrective-v2"
APPROVAL = "_deploy/hydra-corrective-v2-inputs/approval.json"
INPUT = "_deploy/hydra-corrective-v2-inputs/origin-request.json"
BUNDLE = "_deploy/hydra-corrective-v2"
LEDGER = "logs/hydra-corrective-v2.jsonl"
LOCK = "logs/.hydra-corrective-v2.lock"
SUBMISSIONS = "logs/submissions.tsv"
SUBMISSION_HEADER = "timestamp\tjob_id\tscript\tdependency_job_id\tworkdir\tgit_commit\tgit_dirty\tsync_timestamp\tscript_sha256\n"
SCHEMA = "peano-hydra-corrective-held-chain-ledger-v1"
APPROVAL_SCHEMA = "peano-hydra-corrective-approval-v2"
STAGES = ("prepare", "train", "evaluate")
RELEASE_ORDER = ("evaluate", "train", "prepare")
JOBS = {stage: "slurm/peano_hydra_corrective_" + stage + ".sbatch" for stage in STAGES}
JOB_NAMES = {stage: "peano-hydra-corrective-v2-" + stage for stage in STAGES}
RESERVATIONS = {
    "prepare": {"seconds": 1200, "gpus": 0, "cpus": 4, "memory_gib": 8},
    "train": {"seconds": 5400, "gpus": 1, "cpus": 8, "memory_gib": 64},
    "evaluate": {"seconds": 1800, "gpus": 1, "cpus": 8, "memory_gib": 64},
}
PINS = {
    "catalog": {"preparation_relative_path": "_deploy/hydra-posttrain-capacity-fit",
                "preparation_manifest_sha256": "094482ca2949a4248e5720384bb50970259850aaf80dc4f690c94efcf9cea0c2",
                "adapter_manifest_sha256": "723d0f8109c0272774f445c552d781c8e64cadfa50d0516246eb0fa2fd31a955",
                "authority_profile": None},
    "scaled": {"preparation_relative_path": "_deploy/hydra-authority-scale-v1-attempt2/preparation",
               "preparation_manifest_sha256": "3f240267eb89ba58b52cf61514bf995965709f22653e7a0b9d5f2b3d7f712c40",
               "adapter_manifest_sha256": "e3c569796be42cdfb3afd677c3c6c1a6e82c67728b8410a410034c35791d20a4",
               "authority_profile": "peano-authority-primitive-v1"},
}
ORIGINAL_COMMIT = "85a970b1b24170edb9997d5328c1eb6d1d95a8fd"
PRIOR_ATTEMPT = {
    "profile": "peano-hydra-corrective-v1",
    "source_commit": "26dd5c6527ed80b5fc8b49bfba86c9e2addefec3",
    "ledger": "logs/hydra-corrective-v1.jsonl",
    "ledger_sha256": "85769e0edc5b14a1db2f1bda17bf830a62715798ca21d9543c5cd9b06fe1a1c0",
    "cpu_reserved_seconds": 1200,
    "gpu_reserved_seconds": 0,
    "cpu_job_id": "21402731",
    "approval_sha256": "b8d713335981b17a443033001f66cdafdcd39949f7caf5891c1af9808daaa6b9",
}
DECLARED_NATIVE_INPUTS = frozenset((
    "book/_static/constructive-grand-campaign/campaign.json",
    "book/_static/constructive-grand-campaign/definitions.json",
    "artifacts/peano-library/catalog-v1.json",
    "artifacts/peano-library/channels-v25.json",
    "artifacts/peano-library/alpha/catalog-v25.json",
) + tuple("artifacts/peano-hydra/native-search-repair-2026-08-28/witness-fixture-02/" + name
          for name in ("plan.json", "manifest.json", "coverage.json", "proofs.json", "sft.jsonl")))
REQUIRED_SOURCES = frozenset(tuple(JOBS.values()) + (
    "scripts/helios_hydra_corrective.sh", "training/peano_hydra/corrective_launch.py",
    "scripts/helios_common.sh", "scripts/helios_submit_job.sh", "scripts/submit_slurm_job.sh",
    "scripts/prepare_peano_hydra_corrective.py", "scripts/eval_peano_hydra_corrective.py",
    "training/peano_hydra/corrective_workflow.py", "training/peano_hydra/corrective_comparison.py",
    "training/peano_hydra/origin_bridge.py", "training/peano_hydra/corrective_source.py",
    "training/peano_hydra/helios_runtime.py", "training/peano_hydra/posttrain.py",
))
APPROVAL_FIELDS = frozenset(("schema", "profile", "run_id", "approved", "approval_reference", "source_commit",
    "source_files", "origin_request_sha256", "ready_bundle_sha256", "reservations",
    "maximum_aggregate_gpu_seconds", "maximum_concurrent_gpus", "automatic_retry", "payloads", "payloads_sha256",
    "prior_attempt"))
MAX_JSON = 4 * 1024 * 1024
MAX_PAYLOAD = 512 * 1024 * 1024
MAX_TOTAL = 2 * 1024 * 1024 * 1024
MAX_LEDGER = 65536
HEX = re.compile(r"[0-9a-f]{64}\Z")
COMMIT = re.compile(r"[0-9a-f]{40}\Z")
JOB_ID = re.compile(r"[1-9][0-9]{0,19}\Z")


def require(value, message):
    if not value:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(raw):
    require(0 < len(raw) <= MAX_JSON, "metadata JSON exceeds its byte bound")
    def pairs(items):
        result = {}
        for name, value in items:
            require(name not in result, "duplicate metadata key")
            result[name] = value
        return result
    def invalid(value):
        raise ValueError("nonfinite metadata number: " + value)
    def integer(value):
        require(len(value) <= 64, "oversized metadata integer")
        return int(value)
    value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs, parse_constant=invalid, parse_int=integer)
    require(type(value) is dict, "metadata must be one object")
    return value


def relative(value):
    require(type(value) is str and 0 < len(value.encode("utf-8")) <= 4096, "invalid project path")
    parts = value.split("/")
    require(len(parts) <= 64 and all(part not in ("", ".", "..") for part in parts)
            and not Path(value).is_absolute() and not any(ord(char) < 32 or ord(char) == 127 for char in value)
            and "\\" not in value, "noncanonical project-relative path")
    return value


def directory(path):
    path = Path(path).absolute()
    require(".." not in path.parts and 1 < len(path.parts) <= 64, "unsafe metadata directory")
    access = getattr(os, "O_PATH", os.O_RDONLY) if sys.platform == "linux" else os.O_RDONLY
    fd = os.open(path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, part in enumerate(path.parts[1:], 1):
            flags = os.O_RDONLY if index == len(path.parts) - 1 else access
            child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0:
            os.close(fd)


def fingerprint(name, maximum=MAX_PAYLOAD, retain=False):
    path = ROOT / relative(name)
    parent, fd = directory(path.parent), -1
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= maximum,
                "input must be one bounded single-link regular file: " + name)
        sha, size, chunks = hashlib.sha256(), 0, []
        while True:
            block = os.read(fd, min(65536, maximum + 1 - size))
            if not block:
                break
            size += len(block)
            require(size <= maximum, "input grew beyond its bound")
            sha.update(block)
            if retain:
                chunks.append(block)
        after = os.fstat(fd)
        named = os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        fields = ("st_dev", "st_ino", "st_size", "st_nlink", "st_mtime_ns", "st_ctime_ns")
        require(size == before.st_size and all(getattr(before, field) == getattr(after, field) == getattr(named, field)
                                              for field in fields), "metadata changed during its read")
        return {"bytes": size, "sha256": sha.hexdigest()}, b"".join(chunks)
    finally:
        if fd >= 0:
            os.close(fd)
        os.close(parent)


def read(name, maximum=MAX_JSON):
    return fingerprint(name, maximum, True)[1]


def exists(name):
    path = ROOT / relative(name)
    parent = directory(path.parent)
    try:
        try:
            os.stat(path.name, dir_fd=parent, follow_symlinks=False)
        except FileNotFoundError:
            return False
        return True
    finally:
        os.close(parent)


def _identity(approval_sha256):
    require(type(approval_sha256) is str and HEX.fullmatch(approval_sha256), "external approval SHA is required")
    raw = read(APPROVAL)
    require(hashlib.sha256(raw).hexdigest() == approval_sha256, "externally pinned approval bytes differ")
    approval = decode(raw)
    require(set(approval) == APPROVAL_FIELDS and approval["schema"] == APPROVAL_SCHEMA
            and approval["profile"] == PROFILE and approval["run_id"] == RUN_ID and approval["approved"] is True,
            "a proposal or different approval cannot allocate this experiment")
    require(type(approval["approval_reference"]) is str and 0 < len(approval["approval_reference"]) <= 2048
            and type(approval["source_commit"]) is str and COMMIT.fullmatch(approval["source_commit"]),
            "approval lacks its explicit human/source reference")
    require(canonical(approval["reservations"]) == canonical(RESERVATIONS)
            and type(approval["maximum_aggregate_gpu_seconds"]) is int and approval["maximum_aggregate_gpu_seconds"] == 7200
            and type(approval["maximum_concurrent_gpus"]) is int and approval["maximum_concurrent_gpus"] == 1
            and approval["automatic_retry"] is False, "approval changed fixed reservations or retry policy")
    require(canonical(approval["prior_attempt"]) == canonical(PRIOR_ATTEMPT)
            and fingerprint(PRIOR_ATTEMPT["ledger"], MAX_LEDGER)[0]["sha256"] == PRIOR_ATTEMPT["ledger_sha256"],
            "the unchanged zero-GPU prior attempt is not authenticated; no reset/refund")
    provenance = read(".peano-source-provenance.tsv", 1024)
    match = re.fullmatch(rb"([0-9a-f]{40})\tfalse\t([0-9TZ:+-]+)\n", provenance)
    require(match is not None and match.group(1).decode() == approval["source_commit"],
            "approval differs from clean staged source provenance")
    sources = approval["source_files"]
    require(type(sources) is dict and REQUIRED_SOURCES <= set(sources) and len(sources) <= 160,
            "approval omits its guarded source inventory")
    for name, expected in sources.items():
        require(type(expected) is str and HEX.fullmatch(expected), "malformed execution source SHA")
        require(fingerprint(name, 2 * 1024 * 1024)[0]["sha256"] == expected, "approved execution source changed: " + name)
    return approval, {"source_commit": approval["source_commit"], "synced_at": match.group(2).decode(),
                      "approval_sha256": approval_sha256, "source_files_sha256": digest(sources),
                      "job_script_sha256": {stage: sources[JOBS[stage]] for stage in STAGES},
                      "payloads_sha256": approval["payloads_sha256"], "ready_bundle_sha256": approval["ready_bundle_sha256"],
                      "origin_request_sha256": approval["origin_request_sha256"], "prior_attempt": dict(PRIOR_ATTEMPT)}


def validate_metadata(approval_sha256):
    """Authenticate externally approved bytes only; never import Hydra/proofs."""
    approval, identity = _identity(approval_sha256)
    inputs_raw, ready_raw = read(INPUT), read(BUNDLE + "/readiness.json")
    require(hashlib.sha256(inputs_raw).hexdigest() == approval["origin_request_sha256"]
            and hashlib.sha256(ready_raw).hexdigest() == approval["ready_bundle_sha256"], "approved input/readiness anchor changed")
    inputs, ready = decode(inputs_raw), decode(ready_raw)
    require(set(inputs) == {"schema", "source_commit", "source_root", "source_manifest", "source_manifest_sha256", "origins"}
            and inputs["schema"] == "peano-hydra-corrective-origin-inputs-v1"
            and inputs["source_commit"] == ORIGINAL_COMMIT and type(inputs["origins"]) is dict
            and set(inputs["origins"]) == set(PINS), "original input source/roles differ")
    source_root, source_manifest = relative(inputs["source_root"]), relative(inputs["source_manifest"])
    require(fingerprint(source_manifest, MAX_JSON)[0]["sha256"] == inputs["source_manifest_sha256"],
            "portable old-source manifest bytes changed")
    portable = decode(read(source_manifest))
    require(type(portable.get("files")) is dict and 1 <= len(portable["files"]) <= 4096
            and portable.get("git_commit") == ORIGINAL_COMMIT,
            "portable origin inventory lost its original commit")
    names = {INPUT, source_manifest, BUNDLE + "/readiness.json"} | DECLARED_NATIVE_INPUTS
    for name in portable["files"]:
        names.add(relative(source_root + "/" + relative(name)))
    for role, pins in PINS.items():
        value = inputs["origins"][role]
        require(type(value) is dict and set(value) == set(pins) | {"adapter_manifest"}
                and canonical({key: value[key] for key in pins}) == canonical(pins), "original adapter/preparation/authority pin changed")
        preparation = relative(source_root + "/" + pins["preparation_relative_path"])
        require(fingerprint(preparation + "/manifest.json", MAX_JSON)[0]["sha256"] == pins["preparation_manifest_sha256"],
                "original preparation bytes changed")
        manifest = decode(read(preparation + "/manifest.json"))
        require(type(manifest.get("files")) is dict and 1 <= len(manifest["files"]) <= 128
                and type(manifest.get("source")) is dict,
                "original preparation inventory is incomplete")
        names.update(relative(preparation + "/" + relative(name)) for name in set(manifest["files"]) | {"manifest.json"})
        original_source = relative(source_root + "/" + relative(manifest["source"]["directory"]))
        names.update(original_source + "/" + name for name in ("epoch.json", "manifest.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl"))
        adapter_path = relative(value["adapter_manifest"])
        require(fingerprint(adapter_path, MAX_JSON)[0]["sha256"] == pins["adapter_manifest_sha256"], "original adapter manifest changed")
        adapter = decode(read(adapter_path))
        names.add(adapter_path)
        adapter_parent = adapter_path.rsplit("/", 1)[0]
        require("/" in adapter_path, "adapter requires its own declared directory")
        for kind in ("adapter", "tokenizer"):
            require(type(adapter.get(kind)) is dict and type(adapter[kind].get("files")) is dict
                    and 1 <= len(adapter[kind]["files"]) <= 32,
                    "adapter artifact inventory is incomplete")
            names.update(relative(adapter_parent + "/" + relative(name)) for name in adapter[kind]["files"])
    require(ready.get("schema") == "peano-hydra-corrective-readiness-v1" and ready.get("status") == "admitted"
            and ready.get("profile") == PROFILE and ready.get("run_id") == RUN_ID
            and ready.get("complete") is True and ready.get("output_directory") == BUNDLE
            and ready.get("execution_source_files") == approval["source_files"]
            and ready.get("origin_request_file") == INPUT and ready.get("origin_request_sha256") == approval["origin_request_sha256"],
            "readiness does not describe the externally approved bundle")
    for key, expected in (("teacher_routes", 1024), ("train_rows", 8932), ("dev_rows", 744), ("optimizer_steps", 1117)):
        require(type(ready.get(key)) is int and ready[key] == expected, "readiness changed its declared counts")
    require(all(ready.get(key) is False for key in ("model_training_authorized", "model_trained", "research_claim_eligible"))
            and ready.get("token_audit_required_before_weights") is True, "readiness invents model/compute authority")
    expected_receipts = {name for stage in ("source", "preparation", "preflight", "capacity-plan")
                         for name in (stage + ".json", stage + "-process.json")}
    expected_receipts.update({"catalog-origin.json", "scaled-origin.json"})
    require(type(ready.get("files")) is dict and set(ready["files"]) == expected_receipts,
            "readiness omitted/added closed stage receipts")
    names.update(relative(BUNDLE + "/" + relative(name)) for name in ready["files"])
    names.update(BUNDLE + "/source/" + name for name in ("epoch.json", "manifest.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl"))
    names.update(BUNDLE + "/preparation/" + name for name in ("manifest.json", "config.toml", "train.jsonl", "dev.jsonl", "preferences.jsonl", "discovery.jsonl", "quarantine.jsonl"))
    payloads = approval["payloads"]
    require(type(payloads) is dict and 1 <= len(payloads) <= 4096 and set(payloads) == names
            and approval["payloads_sha256"] == digest(payloads), "approved payload inventory omitted/added files")
    total = 0
    for name, expected in payloads.items():
        require(type(expected) is dict and set(expected) == {"bytes", "sha256"}
                and type(expected["bytes"]) is int and 0 <= expected["bytes"] <= MAX_PAYLOAD
                and type(expected["sha256"]) is str and HEX.fullmatch(expected["sha256"]), "invalid payload fingerprint")
        actual = fingerprint(name)[0]
        require(actual == expected, "approved staged payload changed: " + name)
        total += actual["bytes"]
        require(total <= MAX_TOTAL, "approved payload exceeds the 2GiB bound")
    require(_identity(approval_sha256)[1] == identity, "approval or execution source changed during metadata check")
    return approval, identity


def header(identity):
    return {"kind": "header", "schema": SCHEMA, "profile": PROFILE, "run_id": RUN_ID,
            "identity": identity, "reservations": RESERVATIONS, "maximum_aggregate_gpu_seconds": 7200,
            "maximum_cpu_seconds": 1200, "maximum_concurrent_gpus": 1, "automatic_retry": False,
            "release_order": list(RELEASE_ORDER), "prior_attempt": dict(PRIOR_ATTEMPT)}


def _bindings(state):
    return {stage: {"job_id": saved["job_id"], "dependency_job_id": saved["reservation"]["dependency_job_id"],
                    "script_sha256": saved["reservation"]["script_sha256"]}
            for stage, saved in state["stages"].items()}


def _validate_snapshot(snapshot, state, held_stages):
    require(type(snapshot) is dict and set(snapshot) == set(STAGES), "scheduler snapshot omitted a chain job")
    fields = {"job_id", "job_name", "workdir", "job_state", "reason", "priority", "dependency_job_id",
              "requeue", "raw_sha256", "raw_bytes"}
    for stage in STAGES:
        row = snapshot[stage]
        saved = state["stages"][stage]
        require(type(row) is dict and set(row) == fields and row["job_id"] == saved["job_id"]
                and row["job_name"] == JOB_NAMES[stage] and row["workdir"] == str(ROOT)
                and row["job_state"] == "PENDING" and row["requeue"] is False
                and row["dependency_job_id"] == saved["reservation"]["dependency_job_id"]
                and type(row["priority"]) is int and row["priority"] >= 0
                and type(row["reason"]) is str and re.fullmatch(r"[A-Za-z0-9_,:+().-]{1,128}", row["reason"])
                and type(row["raw_sha256"]) is str and HEX.fullmatch(row["raw_sha256"])
                and type(row["raw_bytes"]) is int and 0 < row["raw_bytes"] <= 65536,
                "scheduler snapshot changed the exact pending chain, source path or no-requeue policy")
        if stage in held_stages:
            require(row["priority"] == 0 and row["reason"] == "JobHeldUser", "chain job is not explicitly user-held")
        else:
            require(row["priority"] > 0 and row["reason"] not in {"JobHeldUser", "JobHeldAdmin"},
                    "downstream release was not reflected by the scheduler")


def _empty_state():
    return {"events": [], "stages": {}, "gpu_seconds": 0, "cpu_seconds": 0,
            "phase": "empty", "cpu_release_authorized": False}


def load_ledger(identity):
    if not exists(LEDGER):
        return _empty_state()
    raw = read(LEDGER, MAX_LEDGER)
    require(raw.endswith(b"\n"), "launch ledger is truncated; manual review required")
    lines = raw.splitlines(keepends=True)
    require(1 <= len(lines) <= 11, "launch ledger event count exceeds its one held chain")
    state = _empty_state()
    previous = "0" * 64
    for index, line in enumerate(lines):
        event = decode(line)
        require(set(event) == {"index", "previous_sha256", "payload", "sha256"}
                and type(event["index"]) is int and event["index"] == index and event["previous_sha256"] == previous
                and event["sha256"] == digest({key: event[key] for key in ("index", "previous_sha256", "payload")})
                and canonical(event) + b"\n" == line, "launch ledger chain or canonical bytes differ")
        payload = event["payload"]
        if index == 0:
            require(canonical(payload) == canonical(header(identity)),
                    "launch ledger belongs to another approval/source/prior attempt; no reset allowed")
            state["phase"] = "header"
        elif index == 1:
            require(type(payload) is dict and set(payload) == {"kind", "reservations", "script_sha256", "created_at"}
                    and payload["kind"] == "reserve-chain" and canonical(payload["reservations"]) == canonical(RESERVATIONS)
                    and payload["script_sha256"] == identity["job_script_sha256"]
                    and type(payload["created_at"]) is str and re.fullmatch(r"[0-9TZ:+-]{1,40}", payload["created_at"]),
                    "the entire exact chain must be charged before any submission")
            for stage in STAGES:
                state["stages"][stage] = {"phase": "reserved", "job_id": None, "reservation": {
                    "created_at": payload["created_at"], "reservation": dict(RESERVATIONS[stage]),
                    "script_sha256": payload["script_sha256"][stage], "dependency_job_id": None}}
            state.update(gpu_seconds=7200, cpu_seconds=1200, phase="reserved")
        elif index in (2, 3, 4):
            stage = STAGES[index - 2]
            predecessor = state["stages"][STAGES[index - 3]]["job_id"] if index > 2 else None
            require(type(payload) is dict and set(payload) == {"kind", "stage", "job_id", "dependency_job_id"}
                    and payload["kind"] == "accepted" and payload["stage"] == stage
                    and type(payload["job_id"]) is str and JOB_ID.fullmatch(payload["job_id"])
                    and payload["job_id"] not in {saved["job_id"] for saved in state["stages"].values()}
                    and payload["dependency_job_id"] == predecessor,
                    "held submissions must be three unique IDs in exact afterok order")
            state["stages"][stage].update(phase="accepted", job_id=payload["job_id"])
            state["stages"][stage]["reservation"]["dependency_job_id"] = predecessor
            state["phase"] = "accepted" if index == 4 else "partially-accepted"
        elif index == 5:
            require(type(payload) is dict and set(payload) == {"kind", "snapshot"}
                    and payload["kind"] == "held-chain-validated", "missing full held-chain readback barrier")
            _validate_snapshot(payload["snapshot"], state, set(STAGES))
            state["phase"] = "held-validated"
        elif index == 6:
            require(type(payload) is dict and set(payload) == {"kind", "jobs", "release_order"}
                    and payload["kind"] == "release-chain-authorized" and payload["jobs"] == _bindings(state)
                    and payload["release_order"] == list(RELEASE_ORDER), "release authorization changed the complete chain")
            state["phase"] = "release-authorized"
        elif index in (7, 8, 10):
            stage = {7: "evaluate", 8: "train", 10: "prepare"}[index]
            require(type(payload) is dict and set(payload) == {"kind", "stage", "job_id"}
                    and payload["kind"] == "released" and payload["stage"] == stage
                    and payload["job_id"] == state["stages"][stage]["job_id"],
                    "release ACKs must be durable in evaluate, train, prepare order")
            state["stages"][stage]["phase"] = "released"
            if index == 10:
                state["phase"] = "released"
        elif index == 9:
            require(type(payload) is dict and set(payload) == {"kind", "jobs", "snapshot"}
                    and payload["kind"] == "cpu-release-authorized" and payload["jobs"] == _bindings(state)
                    and all(state["stages"][stage]["phase"] == "released" for stage in ("evaluate", "train")),
                    "CPU release requires both already-durable downstream ACKs")
            _validate_snapshot(payload["snapshot"], state, {"prepare"})
            state.update(cpu_release_authorized=True, phase="cpu-release-authorized")
        require(state["gpu_seconds"] <= 7200 and state["cpu_seconds"] <= 1200, "cumulative reservation exceeds approval")
        state["events"].append(event)
        previous = event["sha256"]
    return state


def append_event(state, payload):
    previous = state["events"][-1]["sha256"] if state["events"] else "0" * 64
    event = {"index": len(state["events"]), "previous_sha256": previous, "payload": payload}
    event["sha256"] = digest(event)
    parent = directory(ROOT / "logs")
    flags = os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    flags |= os.O_APPEND if state["events"] else os.O_CREAT | os.O_EXCL
    fd = os.open(Path(LEDGER).name, flags, 0o600, dir_fd=parent)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "unsafe launch ledger")
        expected = b"".join(canonical(row) + b"\n" for row in state["events"])
        require((not state["events"] and info.st_size == 0) or read(LEDGER, MAX_LEDGER) == expected,
                "launch ledger changed before append")
        raw = canonical(event) + b"\n"
        require(info.st_size + len(raw) <= MAX_LEDGER, "launch ledger exceeds its byte bound")
        with os.fdopen(fd, "ab", closefd=False) as stream:
            stream.write(raw); stream.flush(); os.fsync(fd)
        os.fsync(parent)
        named = os.stat(Path(LEDGER).name, dir_fd=parent, follow_symlinks=False)
        require((named.st_dev, named.st_ino) == (info.st_dev, info.st_ino)
                and read(LEDGER, MAX_LEDGER) == expected + raw, "launch reservation lost its named durable file")
    finally:
        os.close(fd); os.close(parent)
    state["events"].append(event)


def submissions():
    if not exists(SUBMISSIONS):
        return []
    raw = read(SUBMISSIONS, MAX_JSON).decode("utf-8")
    require(raw.startswith(SUBMISSION_HEADER) and raw.endswith("\n"), "project submission ledger is malformed")
    rows = [line.split("\t") for line in raw.splitlines()[1:]]
    require(len(rows) <= 16384 and all(len(row) == 9 for row in rows), "project submission rows exceed their shape/bound")
    require(all(JOB_ID.fullmatch(row[1]) and not any("\r" in field for field in row) for row in rows),
            "project submission ledger contains an invalid job")
    require(len({row[1] for row in rows}) == len(rows), "duplicate project job IDs")
    return rows


def _submission_row(stage, saved, identity):
    request = saved["reservation"]
    return [request["created_at"], saved["job_id"], JOBS[stage], request["dependency_job_id"] or "",
            str(ROOT), identity["source_commit"], "false", identity["synced_at"], request["script_sha256"]]


def check_history(state, identity):
    rows = submissions()
    accepted = {saved["job_id"] for saved in state["stages"].values() if saved["job_id"] is not None}
    # The prior CPU attempt used the same script filenames, but a different
    # immutable source commit. Preserve it, while rejecting unknown jobs from
    # this new source and any altered row for an accepted new-chain job ID.
    own = [row for row in rows if row[1] in accepted
           or (row[2] in JOBS.values() and row[5] == identity["source_commit"])]
    wanted = [_submission_row(stage, saved, identity) for stage, saved in state["stages"].items()
              if saved["job_id"] is not None]
    require(sorted(own) == sorted(wanted), "corrective and project submission histories differ; manual review required")


def append_submission(stage, saved, identity):
    rows = submissions()
    require(saved["job_id"] not in {row[1] for row in rows}, "new accepted job already appears in project ledger")
    existed = exists(SUBMISSIONS)
    parent = directory(ROOT / "logs")
    flags = os.O_WRONLY | os.O_NOFOLLOW | os.O_NONBLOCK | (os.O_APPEND if existed else os.O_CREAT | os.O_EXCL)
    fd = os.open(Path(SUBMISSIONS).name, flags, 0o600, dir_fd=parent)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "unsafe project submission ledger")
        require(submissions() == rows if existed else info.st_size == 0, "project submission ledger changed before append")
        raw = ("\t".join(_submission_row(stage, saved, identity)) + "\n").encode()
        if not existed:
            raw = SUBMISSION_HEADER.encode() + raw
        require(info.st_size + len(raw) <= MAX_JSON, "project submission ledger exceeds its byte bound")
        with os.fdopen(fd, "ab", closefd=False) as stream:
            stream.write(raw); stream.flush(); os.fsync(fd)
        os.fsync(parent)
        named = os.stat(Path(SUBMISSIONS).name, dir_fd=parent, follow_symlinks=False)
        require((named.st_dev, named.st_ino) == (info.st_dev, info.st_ino)
                and submissions() == rows + [_submission_row(stage, saved, identity)],
                "project submission row lost its named durable file")
    finally:
        os.close(fd); os.close(parent)


def run(arguments):
    """Small bounded scheduler metadata; never shell-interpreted strings."""
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        child = subprocess.Popen(arguments, stdin=subprocess.DEVNULL, stdout=out, stderr=err)
        try:
            result = child.wait(timeout=25)
        except BaseException:
            child.kill(); child.wait(); raise
        out.seek(0); err.seek(0)
        stdout, stderr = out.read(MAX_JSON + 1), err.read(65537)
    require(len(stdout) <= MAX_JSON and len(stderr) <= 65536, "scheduler metadata output exceeds bound")
    require(result == 0, "scheduler command failed; any reservation remains charged: " + stderr.decode("utf-8", "replace")[:500])
    return stdout.decode("utf-8")


def check_queue(state):
    user = os.environ.get("USER", "")
    require(re.fullmatch(r"[A-Za-z0-9._-]{1,64}", user), "scheduler user is not declared")
    accepted = {saved["job_id"]: stage for stage, saved in state["stages"].items() if saved["job_id"] is not None}
    raw = run(["squeue", "-h", "-u", user, "-o", "%i|%Z|%j|%T"])
    active = {}
    for line in raw.splitlines():
        fields = line.split("|")
        require(len(fields) == 4 and JOB_ID.fullmatch(fields[0]), "ambiguous scheduler queue row")
        job, workdir, name, status = fields
        if workdir == str(ROOT) or workdir.startswith(str(ROOT) + "/") or name.startswith("peano-hydra-corrective-v2-"):
            require(job in accepted and workdir == str(ROOT) and name == JOB_NAMES[accepted[job]],
                    "an unrelated project job already owns the source/allocation")
            require(job not in active, "scheduler repeated an active project job")
            active[job] = status
    return active


def check_scheduler_history(state, active):
    """A missing local ledger must not reset already accepted allocations."""
    user = os.environ.get("USER", "")
    names = [JOB_NAMES[stage] for stage in STAGES]
    raw = run(["sacct", "-n", "-P", "-X", "-u", user, "--starttime=2026-08-28",
               "--name=" + ",".join(names), "--format=JobIDRaw,JobName%80,WorkDir%4096"])
    accepted = {saved["job_id"]: stage for stage, saved in state["stages"].items() if saved["job_id"] is not None}
    seen = set()
    for line in raw.splitlines():
        if not line.strip():
            continue
        fields = line.split("|")
        require(len(fields) in (3, 4) and (len(fields) == 3 or fields[3] == ""), "ambiguous scheduler accounting row")
        job, name, workdir = fields[:3]
        require(JOB_ID.fullmatch(job) and job not in seen and job in accepted
                and name == JOB_NAMES[accepted[job]] and workdir == str(ROOT),
                "scheduler history differs from charged corrective reservations; no ledger reset")
        seen.add(job)
    require(seen | set(active) == set(accepted), "accepted allocation is absent from queue/accounting; inspect manually")


def check_prior_scheduler_history():
    """The separately pinned first attempt had one CPU job and no GPU jobs."""
    user = os.environ.get("USER", "")
    require(re.fullmatch(r"[A-Za-z0-9._-]{1,64}", user), "scheduler user is not declared")
    raw = run(["sacct", "-n", "-P", "-X", "-u", user, "--starttime=2026-08-28",
               "--name=" + ",".join("peano-hydra-corrective-" + stage for stage in STAGES),
               "--format=JobIDRaw,JobName%80,WorkDir%4096,State,ExitCode"])
    rows = [line.split("|") for line in raw.splitlines() if line.strip()]
    expected = [PRIOR_ATTEMPT["cpu_job_id"], "peano-hydra-corrective-prepare", str(ROOT), "COMPLETED", "0:0"]
    require(len(rows) == 1 and rows[0] in (expected, expected + [""]),
            "prior attempt accounting is not the reviewed CPU-only completion; GPU budget cannot be reset")


def scheduler_snapshot(state, held_stages):
    """Read the controller while CPU is still held, before MinJobAge can apply."""
    snapshot = {}
    keys = {"JobId", "JobName", "WorkDir", "JobState", "Reason", "Priority", "Dependency", "Requeue"}
    for stage in STAGES:
        job = state["stages"][stage]["job_id"]
        require(type(job) is str and JOB_ID.fullmatch(job), "cannot inspect an unaccepted chain job")
        raw = run(["scontrol", "-o", "show", "job", job])
        encoded = raw.encode("utf-8")
        require(0 < len(encoded) <= 65536 and len(raw.strip().splitlines()) == 1,
                "controller job readback must be one bounded record")
        fields = {}
        for match in re.finditer(r"(?:^|\s)([A-Za-z][A-Za-z0-9]*)=(\S*)", raw):
            key, value = match.groups()
            if key in keys:
                require(key not in fields, "controller repeated a guarded job field")
                fields[key] = value
        require(set(fields) == keys and re.fullmatch(r"[0-9]{1,20}", fields["Priority"])
                and fields["Requeue"] == "0", "controller omitted or changed a guarded job field")
        dependency = fields["Dependency"]
        if dependency == "(null)":
            dependency = None
        else:
            match = re.fullmatch(r"afterok:([1-9][0-9]{0,19})(?:\(unfulfilled\))?", dependency)
            require(match is not None, "controller changed the single unfulfilled afterok dependency")
            dependency = match.group(1)
        snapshot[stage] = {"job_id": fields["JobId"], "job_name": fields["JobName"], "workdir": fields["WorkDir"],
                           "job_state": fields["JobState"], "reason": fields["Reason"], "priority": int(fields["Priority"]),
                           "dependency_job_id": dependency, "requeue": False,
                           "raw_sha256": hashlib.sha256(encoded).hexdigest(), "raw_bytes": len(encoded)}
    _validate_snapshot(snapshot, state, set(held_stages))
    return snapshot


def _root_is_remote_project():
    scratch = os.environ.get("SCRATCH")
    require(type(scratch) is str and scratch.startswith("/") and ".." not in Path(scratch).parts,
            "remote SCRATCH is unavailable")
    require(ROOT == Path(scratch) / "codex-control/projects/peano-lab-training",
            "allocation gate must run in the exact staged Helios project")


def _await_lock(fd, operation):
    # Synchronize short ledger commits, never retry a submission or model call.
    deadline = time.monotonic() + 30
    while True:
        try:
            fcntl.flock(fd, operation | fcntl.LOCK_NB)
            return
        except BlockingIOError:
            require(time.monotonic() < deadline, "launch ledger is busy; no automatic allocation retry")
            time.sleep(0.05)


def check_job_reservation(stage, approval_sha256):
    """Every job requires the durable global CPU barrier, not its own ACK."""
    require(stage in STAGES, "unknown scheduled corrective stage")
    _root_is_remote_project()
    job = os.environ.get("SLURM_JOB_ID", "")
    require(JOB_ID.fullmatch(job) and os.environ.get("SLURM_RESTART_COUNT", "0") == "0"
            and os.environ.get("PEANO_JOB_SCRIPT") == JOBS[stage]
            and os.environ.get("PEANO_HYDRA_PROFILE") == PROFILE,
            "scheduled corrective identity or restart differs")
    approval, identity = _identity(approval_sha256)
    parent = directory(ROOT / "logs")
    try:
        fd = os.open(Path(LOCK).name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, "unsafe launch ledger lock")
        _await_lock(fd, fcntl.LOCK_SH)
        state = load_ledger(identity)
        saved = state["stages"].get(stage)
        require(state["cpu_release_authorized"] is True and set(state["stages"]) == set(STAGES)
                and len({item["job_id"] for item in state["stages"].values()}) == 3
                and all(state["stages"][name]["phase"] == "released" for name in ("evaluate", "train"))
                and saved is not None and saved["job_id"] == job
                and saved["reservation"]["script_sha256"] == approval["source_files"][JOBS[stage]],
                "job lacks the complete held-chain/downstream-ACK barrier; direct/restarted submission is forbidden")
        check_history(state, identity)
    finally:
        os.close(fd)


def _submission_options(stage, predecessor):
    spec = RESERVATIONS[stage]
    account = "plgccaiautore2026-gpu-gh200" if spec["gpus"] else "plgccaiautore2026-cpu"
    partition = "plgrid-gpu-gh200" if spec["gpus"] else "plgrid"
    seconds = spec["seconds"]
    wall = "%02d:%02d:%02d" % (seconds // 3600, seconds // 60 % 60, seconds % 60)
    options = ["sbatch", "--parsable", "--hold", "--no-requeue", "--account=" + account,
               "--partition=" + partition, "--nodes=1", "--ntasks=1", "--cpus-per-task=" + str(spec["cpus"]),
               "--mem=" + str(spec["memory_gib"]) + "G", "--time=" + wall, "--chdir=" + str(ROOT),
               "--export=ALL", "--job-name=" + JOB_NAMES[stage], "--output=logs/" + JOB_NAMES[stage] + "-%j.out",
               "--error=logs/" + JOB_NAMES[stage] + "-%j.err"]
    if spec["gpus"]:
        options.append("--gres=gpu:1")
    if predecessor is not None:
        options.append("--dependency=afterok:" + predecessor)
    options.append(JOBS[stage])
    return options


def _record(state, payload, identity):
    append_event(state, payload)
    return load_ledger(identity)


def launch_chain(approval_sha256, *, submit=False, expected_commit=None):
    require(type(submit) is bool, "one fixed complete chain is required")
    require("SLURM_JOB_ID" not in os.environ, "submission cannot nest inside a scheduled job")
    require(not any(name.startswith("SBATCH_") for name in os.environ), "SBATCH overrides are not authorized")
    _root_is_remote_project()
    approval, identity = validate_metadata(approval_sha256)
    require(expected_commit == identity["source_commit"], "remote source does not match the clean local freeze")
    lock = -1
    try:
        if submit:
            parent = directory(ROOT / "logs")
            try:
                lock = os.open(Path(LOCK).name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=parent)
            finally:
                os.close(parent)
            info = os.fstat(lock)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, "unsafe allocation lock")
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        state = load_ledger(identity)
        require(not state["events"], "the single chain was already opened/charged; no retry, resume or reset")
        check_history(state, identity)
        active = check_queue(state)
        check_scheduler_history(state, active)
        check_prior_scheduler_history()
        if not submit:
            return {"status": "test-only", "allocation_performed": False, "scheduler_submission_tested": False,
                    "approval_sha256": approval_sha256, "reservations": RESERVATIONS, "release_order": list(RELEASE_ORDER),
                    "dependencies": {"prepare": None, "train": "prepare", "evaluate": "train"},
                    "future_dependency_job_ids": "not-yet-assigned", "automatic_retry": False}
        require(validate_metadata(approval_sha256)[1] == identity, "approved source/payload changed before reservation")
        state = _record(state, header(identity), identity)
        state = _record(state, {"kind": "reserve-chain", "reservations": RESERVATIONS,
                               "script_sha256": identity["job_script_sha256"],
                               "created_at": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"}, identity)
        # The entire 1200 CPU + 7200 GPU envelope is durable BEFORE any sbatch.
        predecessor = None
        for stage in STAGES:
            raw = run(_submission_options(stage, predecessor)).strip()
            require(re.fullmatch(r"[1-9][0-9]{0,19}(?:;[A-Za-z0-9_-]{1,64})?", raw),
                    "ambiguous sbatch response; the full chain remains charged and CPU is not released")
            job = raw.split(";", 1)[0]
            state = _record(state, {"kind": "accepted", "stage": stage, "job_id": job,
                                   "dependency_job_id": predecessor}, identity)
            append_submission(stage, state["stages"][stage], identity)
            print("accepted_held_" + stage + "_job_id=" + job, flush=True)
            predecessor = job
        check_history(state, identity)
        active = check_queue(state)
        check_scheduler_history(state, active)
        state = _record(state, {"kind": "held-chain-validated", "snapshot": scheduler_snapshot(state, STAGES)}, identity)
        state = _record(state, {"kind": "release-chain-authorized", "jobs": _bindings(state),
                               "release_order": list(RELEASE_ORDER)}, identity)
        # Both descendants remain blocked on afterok while CPU stays held.
        # No job can start while this exclusive metadata lock is held.
        for stage in ("evaluate", "train"):
            job = state["stages"][stage]["job_id"]
            run(["scontrol", "release", job])
            state = _record(state, {"kind": "released", "stage": stage, "job_id": job}, identity)
        check_history(state, identity)
        check_queue(state)
        state = _record(state, {"kind": "cpu-release-authorized", "jobs": _bindings(state),
                               "snapshot": scheduler_snapshot(state, {"prepare"})}, identity)
        # A fast CPU (and its descendants) may authenticate this durable global
        # barrier before its own release ACK returns. Nothing is submitted later.
        fcntl.flock(lock, fcntl.LOCK_UN)
        run(["scontrol", "release", state["stages"]["prepare"]["job_id"]])
        _await_lock(lock, fcntl.LOCK_EX)
        state = _record(state, {"kind": "released", "stage": "prepare",
                               "job_id": state["stages"]["prepare"]["job_id"]}, identity)
        return {"status": "submitted", "profile": PROFILE, "run_id": RUN_ID, "jobs": _bindings(state),
                "approval_sha256": approval_sha256, "reservations": RESERVATIONS,
                "release_order": list(RELEASE_ORDER), "cumulative_gpu_seconds": state["gpu_seconds"],
                "cumulative_cpu_seconds": state["cpu_seconds"], "prior_attempt": dict(PRIOR_ATTEMPT),
                "ledger": LEDGER, "automatic_retry": False}
    finally:
        if lock >= 0:
            os.close(lock)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--chain", action="store_true", required=True)
    parser.add_argument("--approval-sha256", required=True)
    parser.add_argument("--source-commit", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--test-only", action="store_true")
    mode.add_argument("--submit", action="store_true")
    parser.add_argument("--confirm")
    args = parser.parse_args(argv)
    try:
        require(args.confirm == "PEANO-HYDRA-CORRECTIVE" if args.submit else args.confirm is None,
                "real allocation needs the exact new corrective confirmation")
        result = launch_chain(args.approval_sha256, submit=args.submit, expected_commit=args.source_commit)
        print(json.dumps(result, sort_keys=True, allow_nan=False), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, IndexError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        print("corrective-launch: " + " ".join(str(error).split())[:2000], file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
