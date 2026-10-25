#!/usr/bin/env python3
"""Prepare an exact local bundle; send it once only when explicitly requested.

Both endpoints, the training profile, and the authorization sidecar are fixed.
This archive helper never submits a job, installs software, resumes, or removes
failed output. The separate launch gate remains responsible for admission.
"""
import argparse
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import re
import resource
import selectors
import shlex
import signal
import stat
import struct
import subprocess
import sys
import time

ARCHIVE = Path(__file__).absolute().parent
REMOTE_HELPER = ARCHIVE / "transfer-frontier-training-remote.py"
spec = importlib.util.spec_from_file_location("frontier_transfer_receiver", REMOTE_HELPER)
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
LOCAL_ROOT = Path(r.LOCAL_ROOT)
HOST = "plgnasqret@helios.cyfronet.pl"
GATE = "training/peano_hydra/frontier_training_launch.py"
ATTEMPT = re.compile(r"transfer-[a-z0-9][a-z0-9-]{0,47}\Z")
BOUNDS = {"files": r.MAX_FILES, "file_bytes": r.MAX_FILE, "total_bytes": r.MAX_TOTAL,
          "ssh_wall_seconds": 60, "automatic_retry": False}


def descriptor(raw):
    return {"bytes": len(raw), "sha256": r.sha(raw)}


def read_file(path, maximum=r.MAX_JSON):
    tree = r.Tree(str(path.parent))
    try:
        pin, raw, _ = tree.fingerprint(path.name, retain=True)
        r.require(pin["bytes"] <= maximum, "metadata read bound")
        return raw
    finally:
        tree.close()


def new_json(path, value):
    raw = r.canonical(value) + b"\n"
    r.require(len(raw) <= r.MAX_JSON, "receipt byte bound")
    parent = r.directory(str(path.parent))
    try:
        fd = os.open(path.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        try:
            with os.fdopen(fd, "wb", closefd=False) as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(fd)
        finally:
            os.close(fd)
        os.fsync(parent)
    finally:
        os.close(parent)
    return r.sha(raw)


def attempt_path(name):
    r.require(type(name) is str and ATTEMPT.fullmatch(name), "fresh bounded transfer-NAME required")
    return ARCHIVE / name


def helper_pins():
    return {"helper_sha256": r.sha(read_file(Path(__file__).absolute())),
            "remote_helper_sha256": r.sha(read_file(REMOTE_HELPER))}


def clean_environment():
    result = {key: value for key, value in os.environ.items()
              if not key.startswith(("GIT_", "PYTHON", "SBATCH_"))}
    result.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL="/dev/null", GIT_NO_REPLACE_OBJECTS="1",
                  GIT_NO_LAZY_FETCH="1", GIT_OPTIONAL_LOCKS="0", PYTHONDONTWRITEBYTECODE="1")
    return result


def bounded(command, *, timeout, stdin=None, cwd=None):
    """One process group, bounded stdout/stderr and wall time; no automatic retry."""
    started, start_utc = time.monotonic(), r.utc()
    def limits():
        resource.setrlimit(resource.RLIMIT_CPU, (60, 60))
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    child = subprocess.Popen(command, stdin=stdin if stdin is not None else subprocess.DEVNULL,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd,
                             env=clean_environment(), start_new_session=True, preexec_fn=limits)
    selector = selectors.DefaultSelector()
    output = {"stdout": bytearray(), "stderr": bytearray()}
    reason = "exited"
    try:
        for name in output:
            stream = getattr(child, name)
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, name)
        while selector.get_map():
            r.require(time.monotonic() - started < timeout, "bounded subprocess wall deadline")
            for key, _ in selector.select(0.1):
                block = os.read(key.fileobj.fileno(), 65536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                # Even fully escaped control bytes must fit a retained JSON
                # receipt. Preserve the bounded prefix before killing a child
                # whose output exceeds the cap.
                cap = 512 * 1024 if key.data == "stdout" else 64 * 1024
                available = cap - len(output[key.data])
                output[key.data].extend(block[:available])
                r.require(len(block) <= available, "subprocess output bound")
        child.wait(timeout=max(0.01, timeout - (time.monotonic() - started)))
    except BaseException as error:
        reason = type(error).__name__ + ": " + str(error)
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        child.wait(timeout=2)
    finally:
        selector.close()
        child.stdout.close()
        child.stderr.close()
    return {"command": command, "started_at_utc": start_utc, "wall_seconds": round(time.monotonic() - started, 6),
            "returncode": child.returncode, "reason": reason, "automatic_retry": False,
            **{name: raw.decode("utf-8", "replace") for name, raw in output.items()}}


def local_gate(approval_sha):
    command = [sys.executable, "-I", "-B", str(LOCAL_ROOT / GATE),
               "--check", "--local", "--approval-sha256", approval_sha]
    return bounded(command, timeout=60, cwd=str(LOCAL_ROOT))


def validate_gate(result, record):
    r.require(result["returncode"] == 0 and result["reason"] == "exited", "local launch metadata gate failed")
    value = r.decode(result["stdout"].encode())
    r.require(value.get("status") == "metadata-verified" and value.get("allocation_performed") is False
              and value.get("source_commit") == record["source_commit"]
              and value.get("approval_sha256") == record["approval_sha256"]
              and value.get("helper_sha256") == record["source_files"][GATE]["sha256"], "local metadata gate identity differs")


def source_check(tree, record):
    tree.anchored()
    for name, pin in record["files"].items():
        if name != r.PROVENANCE:
            actual, _, info = tree.fingerprint(name)
            r.require(actual == pin, "local source/payload changed: " + name)
            expected_mode = 0o700 if info[2] & 0o111 else 0o600
            r.require(expected_mode == record["file_modes"][name], "local executable mode changed: " + name)
    package = r.Tree(str(LOCAL_ROOT / r.PACKAGE))
    try:
        actual = {r.PACKAGE + "/" + name for name in package.files()}
        r.require(actual == set(record["payloads"]) | {r.REQUEST, r.APPROVAL}, "local package is not closed")
    finally:
        package.close()
    r.require(r.sha(read_file(ARCHIVE / "user-instruction.json")) == r.USER_INSTRUCTION_SHA256, "authorization sidecar changed")
    r.require(all(record[key] == value for key, value in helper_pins().items()), "transfer helper changed")
    tree.anchored()


def build_inventory(tree, request_sha, approval_sha, commit):
    request_raw = tree.fingerprint(r.REQUEST, retain=True)[1]
    approval_raw = tree.fingerprint(r.APPROVAL, retain=True)[1]
    r.require(r.sha(request_raw) == request_sha and r.sha(approval_raw) == approval_sha, "external request/approval bytes differ")
    request = r.decode(request_raw)
    sources, payloads = r.file_map(request["source_files"]), r.file_map(request["payloads"])
    stamp = r.utc()
    provenance = commit + "\tfalse\t" + stamp + "\n"
    files = dict(sources)
    r.require(not (set(files) & set(payloads)), "source/payload collision")
    files.update(payloads)
    r.require(not ({r.REQUEST, r.APPROVAL, r.PROVENANCE} & set(files)), "reserved file collision")
    files.update({r.REQUEST: descriptor(request_raw), r.APPROVAL: descriptor(approval_raw),
                  r.PROVENANCE: descriptor(provenance.encode())})
    modes = {r.PROVENANCE: 0o600}
    for name in set(files) - {r.PROVENANCE}:
        fd, info = tree.open_file(name)
        os.close(fd)
        modes[name] = 0o700 if info[2] & 0o111 else 0o600
    record = {"schema": r.SCHEMA, "profile": r.PROFILE, "run_id": r.RUN_ID,
              "local_root": r.LOCAL_ROOT, "remote_root": r.REMOTE_ROOT, "source_commit": commit,
              "request_sha256": request_sha, "approval_sha256": approval_sha,
              "user_instruction_sha256": r.USER_INSTRUCTION_SHA256, "created_at_utc": stamp,
              "source_files": sources, "payloads": payloads, "files": files, "file_modes": modes,
              "order": r.expected_order(files), "file_count": len(files),
              "total_bytes": sum(item["bytes"] for item in files.values()), "provenance": provenance,
              "limits": dict(BOUNDS), **helper_pins()}
    r.validate_inventory(record)
    r.validate_control(record, request_raw, approval_raw)
    return record


def write_bundle(path, tree, record, inventory_raw):
    r.require(len(inventory_raw) <= r.MAX_JSON, "inventory byte bound")
    digest = hashlib.sha256()
    count = 0
    with path.open("xb") as output:
        def write(raw):
            nonlocal count
            output.write(raw)
            digest.update(raw)
            count += len(raw)
            r.require(count <= r.MAX_TOTAL + r.MAX_JSON + 128, "bundle byte bound")
        write(r.MAGIC + struct.pack(">Q", len(inventory_raw)) + inventory_raw)
        for name in record["order"]:
            if name == r.PROVENANCE:
                write(record["provenance"].encode())
                continue
            fd, before = tree.open_file(name)
            current, size = hashlib.sha256(), 0
            try:
                while True:
                    block = os.read(fd, 65536)
                    if not block:
                        break
                    size += len(block)
                    r.require(size <= record["files"][name]["bytes"], "source grew while bundling")
                    current.update(block)
                    write(block)
                r.require(r.identity(os.fstat(fd)) == before, "source changed while bundling")
            finally:
                os.close(fd)
            r.require({"bytes": size, "sha256": current.hexdigest()} == record["files"][name], "bundled bytes differ")
        output.flush()
        os.fsync(output.fileno())
    return {"bytes": count, "sha256": digest.hexdigest()}


def prepare(args):
    target = attempt_path(args.attempt)
    archive_fd = r.directory(str(ARCHIVE))
    try:
        os.mkdir(target.name, 0o700, dir_fd=archive_fd)
        os.fsync(archive_fd)
    finally:
        os.close(archive_fd)
    new_json(target / "prepare-started.json", {"started_at_utc": r.utc(), "phase": "preparing-local-bundle",
             "request_sha256": args.request_sha256, "approval_sha256": args.approval_sha256,
             "source_commit": args.source_commit, "network_contacted": False, **helper_pins()})
    result = {"schema": "peano-hydra-frontier-training-transfer-preparation-v1",
              "network_contacted": False, "automatic_retry": False, "partial_outputs_preserved": True}
    tree = None
    try:
        tree = r.Tree(str(LOCAL_ROOT))
        record = build_inventory(tree, args.request_sha256, args.approval_sha256, args.source_commit)
        source_check(tree, record)
        checked = local_gate(args.approval_sha256)
        new_json(target / "local-gate-prepare.json", checked)
        validate_gate(checked, record)
        raw = r.canonical(record) + b"\n"
        inventory_sha = new_json(target / "inventory.json", record)
        bundle = write_bundle(target / "bundle.bin", tree, record, raw)
        source_check(tree, record)
        result.update(status="prepared-local-only", inventory_sha256=inventory_sha, bundle=bundle,
                      source_commit=record["source_commit"], request_sha256=record["request_sha256"],
                      approval_sha256=record["approval_sha256"], file_count=record["file_count"], total_bytes=record["total_bytes"])
    except BaseException as error:
        result.update(status="failed-partial-output-preserved", error=(type(error).__name__ + ": " + str(error))[:2000])
    finally:
        if tree is not None:
            tree.close()
        result["finished_at_utc"] = r.utc()
        receipt_sha = new_json(target / "prepare-result.json", result)
    print(json.dumps({**result, "receipt_sha256": receipt_sha, "attempt": str(target)}, sort_keys=True), flush=True)
    return 0 if result["status"] == "prepared-local-only" else 2


def bundle_open(path, expected):
    parent = r.directory(str(path.parent))
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        before = r.identity(os.fstat(fd))
        r.require(stat.S_ISREG(before[2]) and before[3] == 1 and before[4] == expected["bytes"]
                  and before[4] <= r.MAX_TOTAL + r.MAX_JSON + 128, "bundle identity/bound")
        digest, total = hashlib.sha256(), 0
        while True:
            block = os.read(fd, 65536)
            if not block:
                break
            total += len(block)
            r.require(total <= expected["bytes"], "bundle grew beyond pinned size")
            digest.update(block)
        r.require(total == expected["bytes"] and digest.hexdigest() == expected["sha256"]
                  and r.identity(os.fstat(fd)) == before, "bundle bytes changed")
        os.lseek(fd, 0, os.SEEK_SET)
        # Popen consumes the descriptor offset, not a BufferedReader's logical
        # offset. Keep this unbuffered when inspecting the prefix before SSH.
        return os.fdopen(fd, "rb", buffering=0), before
    except BaseException:
        os.close(fd)
        raise


def send(args):
    target = attempt_path(args.attempt)
    # A durable marker is claimed before any local checking or network action.
    # It prevents a second attempt even when the first outcome is uncertain.
    new_json(target / "send-started.json", {"started_at_utc": r.utc(), "inventory_sha256": args.inventory_sha256,
             "single_attempt": True, "automatic_retry": False, **helper_pins()})
    result = {"schema": "peano-hydra-frontier-training-transfer-send-v1", "network_contacted": False,
              "automatic_retry": False, "partial_outputs_preserved": True, "inventory_sha256": args.inventory_sha256}
    tree = None
    try:
        raw = read_file(target / "inventory.json")
        r.require(r.sha(raw) == args.inventory_sha256, "external inventory SHA differs")
        record = r.validate_inventory(r.decode(raw))
        prepared = r.decode(read_file(target / "prepare-result.json"))
        r.require(prepared.get("status") == "prepared-local-only" and prepared.get("inventory_sha256") == args.inventory_sha256, "successful exact local preparation missing")
        tree = r.Tree(str(LOCAL_ROOT))
        source_check(tree, record)
        checked = local_gate(record["approval_sha256"])
        new_json(target / "local-gate-send.json", checked)
        validate_gate(checked, record)
        bundle, before = bundle_open(target / "bundle.bin", prepared["bundle"])
        try:
            prefix = r.exact(bundle, len(r.MAGIC) + 8)
            r.require(prefix[:len(r.MAGIC)] == r.MAGIC, "bundle magic")
            length = struct.unpack(">Q", prefix[-8:])[0]
            r.require(length == len(raw) and r.exact(bundle, length) == raw, "bundle does not contain the pinned inventory")
            bundle.seek(0)
            program = read_file(REMOTE_HELPER).decode("utf-8") + "\nmain()\n"
            remote_command = "/usr/bin/python3 -I -B -c " + shlex.quote(program) + " " + shlex.quote(args.inventory_sha256)
            command = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                       "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
                       "-o", "ClearAllForwardings=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
                       "-o", "ControlMaster=no", "-o", "ControlPath=none",
                       "--", HOST, remote_command]
            print(json.dumps({"phase": "single-transfer-attempt-starting", "attempt": args.attempt,
                              "file_count": record["file_count"], "total_bytes": record["total_bytes"]}), flush=True)
            result["network_contacted"] = True
            process = bounded(command, timeout=60, stdin=bundle, cwd=str(ARCHIVE))
            # Store program identity instead of repeating its full source in the receipt.
            process["command"] = command[:-1] + ["<fixed remote program; hash recorded below>"]
            process["remote_program_sha256"] = r.sha(program.encode())
            new_json(target / "ssh-process.json", process)
            result["ssh_process"] = process
            r.require(r.identity(os.fstat(bundle.fileno())) == before, "local bundle changed during SSH")
        finally:
            bundle.close()
        # Rehash local originals and the immutable bundle after the attempted transfer.
        source_check(tree, record)
        reread, _ = bundle_open(target / "bundle.bin", prepared["bundle"])
        reread.close()
        result["local_inputs_rechecked"] = True
        r.require(process["returncode"] == 0 and process["reason"] == "exited", "SSH attempt failed; destination may be partial")
        remote = r.decode(process["stdout"].encode())
        r.require(remote.get("status") == "transferred-and-rehashed"
                  and remote.get("inventory_sha256") == args.inventory_sha256
                  and remote.get("file_count") == record["file_count"] and remote.get("total_bytes") == record["total_bytes"]
                  and remote.get("all_file_hashes_rechecked") is True and remote.get("exact_inventory_checked") is True
                  and remote.get("job_submission_performed") is False, "remote receipt does not prove exact transfer")
        result.update(status="transferred-and-rehashed", remote=remote, source_commit=record["source_commit"],
                      request_sha256=record["request_sha256"], approval_sha256=record["approval_sha256"])
    except BaseException as error:
        result.update(status="failed-no-automatic-retry", error=(type(error).__name__ + ": " + str(error))[:2000])
    finally:
        if tree is not None:
            tree.close()
        result["finished_at_utc"] = r.utc()
        receipt_sha = new_json(target / "send-result.json", result)
    print(json.dumps({"status": result["status"], "receipt_sha256": receipt_sha,
                      "receipt": str(target / "send-result.json"), "network_contacted": result["network_contacted"]}), flush=True)
    return 0 if result["status"] == "transferred-and-rehashed" else 2


def main(argv=None):
    r.require(sys.flags.isolated and sys.dont_write_bytecode, "run with python -I -B")
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    def deadline(signum, frame):
        raise TimeoutError("local transfer helper 180-second wall deadline")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(180)
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    commands = parser.add_subparsers(dest="operation", required=True)
    first = commands.add_parser("prepare", allow_abbrev=False)
    first.add_argument("--request-sha256", required=True)
    first.add_argument("--approval-sha256", required=True)
    first.add_argument("--source-commit", required=True)
    first.add_argument("--attempt", required=True)
    second = commands.add_parser("send", allow_abbrev=False)
    second.add_argument("--inventory-sha256", required=True)
    second.add_argument("--attempt", required=True)
    args = parser.parse_args(argv)
    for field in ("request_sha256", "approval_sha256", "inventory_sha256"):
        if hasattr(args, field):
            r.require(r.HEX.fullmatch(getattr(args, field)), "invalid external SHA")
    if hasattr(args, "source_commit"):
        r.require(r.COMMIT.fullmatch(args.source_commit), "invalid external commit")
    return prepare(args) if args.operation == "prepare" else send(args)


if __name__ == "__main__":
    raise SystemExit(main())
