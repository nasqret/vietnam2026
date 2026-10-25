"""One explicitly invoked SSH phase for the sealed CPU-only monitor probe.

No automatic next phase, retry, cancellation, actual-tool companion or GPU
ledger update is performed. Local intent is exclusive and precedes SSH.
"""
from __future__ import annotations

import argparse
import base64
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import select
import shlex
import subprocess
import sys
import time

import remote_probe_control as control

HERE = Path(__file__).resolve().parent
PAYLOAD = HERE.parent
ATTEMPT = HERE / "attempt"
LOGIN_PYTHON = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3"
LOGIN_PYTHON_LIB = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib"
SSH = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
    "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
    "-o", "ClearAllForwardings=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
    "-o", "ControlMaster=no", "-o", "ControlPath=none", "--", "plgnasqret@helios.cyfronet.pl"]
require, canonical, digest = control.require, control.canonical, control.digest


def read(path, expected=None, limit=4 * 1024**2):
    raw = control.ordinary_bytes(Path(path), limit)
    if expected is not None:
        require(control.valid_sha(expected) and digest(raw) == expected, "File pin differs: " + str(path))
    return raw


def write(path, raw):
    require(len(raw) <= control.MAX_RESPONSE, "Local evidence exceeds its bound.")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(raw)
    path.chmod(0o444)


def put(path, value):
    write(path, canonical(value) + b"\n")


def source_seal():
    raw = read(HERE / "PREPARED.json", limit=65536)
    seal = json.loads(raw)
    require(seal.get("schema") == "hydra-child-linux-monitor-control-prepared-v1"
            and seal.get("status") == "prepared_not_executed"
            and set(seal["code"]) == {"probe_control.py", "remote_probe_control.py"}
            and seal.get("payload_manifest") == control.PINS["manifest.json"], "Unknown control seal.")
    for name, expected in seal["code"].items():
        data = read(HERE / name, expected["sha256"], 65536)
        require(len(data) == expected["bytes"], "Control source size changed.")
    for name, expected in control.PINS.items():
        data = read(PAYLOAD / name, expected["sha256"], 128 * 1024)
        require(len(data) == expected["bytes"], "Frozen probe payload changed.")
    return seal, digest(raw)


@contextmanager
def phase_lock():
    fd = os.open(HERE / ".phase.lock", os.O_WRONLY | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)


def finished_phase(name):
    directory = ATTEMPT / name
    request = json.loads(read(directory / "request.json", limit=control.MAX_INPUT))
    transport = json.loads(read(directory / "transport-completion.json", limit=16384))
    response = json.loads(read(directory / "response.json", limit=control.MAX_RESPONSE))
    result = json.loads(read(directory / "result.json", limit=16384))
    require(result.get("completed") is True and result.get("sources_unchanged") is True
            and result.get("error") is None, "Prior local phase/source verification did not complete.")
    require(transport.get("actual_ssh_exit_code") == 0 and transport.get("owned_child_reaped") is True
            and transport.get("output_complete") is True and transport.get("stop_reason") is None,
            "Prior phase lacks a complete successful SSH observation; preserve uncertainty.")
    require(response.get("schema") == "hydra-child-linux-monitor-control-response-v1"
            and response.get("completed") is True and response.get("error") is None
            and response.get("phase") == request["phase"] and response.get("nonce") == request["nonce"]
            and response.get("remote_control_sha256") == request["remote_control_sha256"]
            and response.get("manifest_sha256") == request["manifest_sha256"], "Prior phase response binding differs.")
    return request, response


def payload_for(args, seal):
    source_sha = seal["code"]["remote_probe_control.py"]["sha256"]
    if args.phase == "stage":
        require(re.fullmatch(r"[0-9a-f]{32}", args.nonce), "Use one explicit 32-character lowercase hex nonce.")
        request = {"schema": "hydra-child-linux-monitor-control-request-v1", "phase": "stage", "nonce": args.nonce,
                   "manifest_sha256": control.PINS["manifest.json"]["sha256"], "remote_control_sha256": source_sha,
                   "uploads": {name: base64.b64encode(read(PAYLOAD / name, control.PINS[name]["sha256"],
                                               128 * 1024)).decode("ascii") for name in control.UPLOADS}}
        control.decode_uploads(request["uploads"])
    else:
        original, stage = finished_phase("stage")
        require(original["remote_control_sha256"] == source_sha and stage["phase_result"]["completed"] is True,
                "Staged control code differs from this seal.")
        request = {key: original[key] for key in ("schema", "nonce", "manifest_sha256", "remote_control_sha256")}
        request["phase"] = args.phase
        if args.phase in {"release", "collect"}:
            submitted, held = finished_phase("submit-held")
            result = held["phase_result"]
            require(submitted["nonce"] == original["nonce"] and result.get("held_confirmed") is True
                    and type(result.get("job_id")) is str and re.fullmatch(r"[0-9]{1,20}", result["job_id"]),
                    "No complete exact held job is available; do not invent an ID.")
            request["job_id"] = result["job_id"]
    require(len(canonical(request)) <= control.MAX_INPUT, "Bounded control request is too large.")
    return request


def save_observation(directory, response):
    result = response["phase_result"]
    require(result.get("observation_only") is True and result.get("probe_success_claimed") is False,
            "Collection is not an actual-tool completion or a probe success claim.")
    job_id = result["job_id"]
    allowed = {"actual-process-exit.txt", "slurm-" + job_id + ".out", "slurm-" + job_id + ".err"}
    allowed |= {"run-01/" + name for name in control.RUN_FILES}
    files = result["files"]
    require(type(files) is dict and set(files) <= allowed and len(files) <= len(allowed), "Unlisted collected file.")
    run_bytes = 0
    for name, item in files.items():
        require(set(item) == {"bytes", "sha256", "base64"}, "Unexpected file descriptor.")
        raw = base64.b64decode(item["base64"], validate=True)
        limit = 256 * 1024 if name.startswith("run-01/") else (16 if name == "actual-process-exit.txt" else 65536)
        require(len(raw) <= limit and control.pin(raw) == {key: item[key] for key in ("bytes", "sha256")},
                "Collected bytes do not match their exact descriptor.")
        if name.startswith("run-01/"):
            run_bytes += len(raw)
        require(run_bytes <= 2 * 1024**2, "Collected run exceeds its total byte bound.")
        path = directory / "files" / name
        path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        write(path, raw)
        if name == "run-01/result.json":
            write(directory / "result.json", raw)


# Fixed SSH transport is copied from paired-v5, with only this adjacent filename
# and the smaller explicit 150-second wall ceiling substituted.
def ssh_once(payload):
    """One fixed SSH child, nonblocking input/output and a 150-second ceiling."""
    raw = canonical(payload)
    require(len(raw) <= control.MAX_INPUT, "SSH input exceeds its bound.")
    code = read(HERE / "remote_probe_control.py", limit=65536).decode()
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
            if time.monotonic() - started >= 150:
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="phase", required=True)
    stage = commands.add_parser("stage")
    stage.add_argument("--nonce", required=True)
    commands.add_parser("submit-held")
    commands.add_parser("release")
    collect = commands.add_parser("collect")
    collect.add_argument("--observation", required=True, choices=["%03d" % i for i in range(1, 9)])
    args = parser.parse_args()
    os.umask(0o077)
    with phase_lock():
        seal, seal_sha = source_seal()
        request = payload_for(args, seal)
        if args.phase == "stage":
            ATTEMPT.mkdir(mode=0o700, exist_ok=False)
        label = args.phase if args.phase != "collect" else "collect-" + args.observation
        phase_directory = ATTEMPT / label
        phase_directory.mkdir(mode=0o700, exist_ok=False)
        observation = None
        if args.phase == "collect":
            observation = PAYLOAD / ("observation-" + args.observation)
            observation.mkdir(mode=0o700, exist_ok=False)
        put(phase_directory / "request.json", request)
        put(phase_directory / "intent.json", {"schema": "hydra-child-linux-monitor-local-phase-intent-v1",
            "phase": args.phase, "nonce": request["nonce"], "job_id": request.get("job_id"),
            "prepared_sha256": seal_sha, "remote_control_sha256": request["remote_control_sha256"],
            "request_sha256": digest(canonical(request)), "automatic_retry": False,
            "automatic_next_phase": False, "status": "intent_not_outcome", "created_unix": time.time()})
        raw, transport = ssh_once(request)
        transport.update(schema="hydra-child-linux-monitor-ssh-completion-v1", phase=args.phase,
                         request_sha256=digest(canonical(request)), prepared_sha256=seal_sha,
                         actual_tool_exit_code=None, actual_tool_completion_recorded_by_root=False)
        write(phase_directory / "raw-response.bin", raw)
        put(phase_directory / "transport-completion.json", transport)
        response, error = None, None
        try:
            require(transport["owned_child_reaped"] and transport["output_complete"],
                    "SSH observation is incomplete; the remote outcome is uncertain.")
            response = json.loads(raw)
            require(response.get("schema") == "hydra-child-linux-monitor-control-response-v1"
                    and response.get("phase") == args.phase and response.get("nonce") == request["nonce"]
                    and response.get("manifest_sha256") == request["manifest_sha256"]
                    and response.get("remote_control_sha256") == request["remote_control_sha256"],
                    "Remote response identity differs.")
            put(phase_directory / "response.json", response)
            if observation is not None:
                write(observation / "raw-response.bin", raw)
                put(observation / "response.json", response)
                put(observation / "transport-completion.json", transport)
                put(observation / "request.json", request)
                if response.get("completed") is True:
                    save_observation(observation, response)
            require(transport["actual_ssh_exit_code"] == 0 and response.get("completed") is True
                    and response.get("error") is None, "Remote phase failed; preserve it without automatic retry.")
        except BaseException as failure:
            error = {"type": type(failure).__name__, "detail": str(failure)[:1200]}
        unchanged = False
        try:
            unchanged = source_seal()[1] == seal_sha
        except BaseException as failure:
            error = error or {"type": type(failure).__name__, "detail": str(failure)[:1200]}
        result = {"schema": "hydra-child-linux-monitor-local-phase-result-v1", "phase": args.phase,
                  "completed": error is None and unchanged, "error": error, "sources_unchanged": unchanged,
                  "nonce": request["nonce"], "job_id": response.get("job_id") if response else request.get("job_id"),
                  "actual_ssh_exit_code": transport["actual_ssh_exit_code"], "phase_directory": str(phase_directory),
                  "observation_directory": str(observation) if observation else None,
                  "probe_success_claimed": False, "actual_tool_companion_created": False,
                  "automatic_retry": False, "automatic_next_phase": False}
        put(phase_directory / "result.json", result)
        print(json.dumps(result, sort_keys=True))
        return 0 if result["completed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"completed": False, "error": type(error).__name__ + ": " + str(error)[:1200],
                          "automatic_retry": False}), file=sys.stderr)
        raise SystemExit(1)
