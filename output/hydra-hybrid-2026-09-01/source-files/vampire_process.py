"""Bounded, local-only execution of one pinned Vampire binary.

The proof worker may launch only the fixed helper, with a fixed environment.
The helper execs Vampire in the same process group; the HTTP parent owns group
cancellation and sampled RSS accounting. No solver verdict is a kernel proof.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import sys
import time

APP = Path(__file__).resolve().parent
DIRECTORY = APP / ".runtime/vampire"
HELPER = APP / "vampire_worker.py"
VERSION = "5.0.1"
ARCHIVE_SHA = "8c92e649fe7bc622a70000afbdf5a5c51007b384e2d8b8235c95474cc7a68f35"
SOLVER_ARGS = ["--mode", "vampire", "--input_syntax", "tptp", "--proof", "tptp",
               "--output_axiom_names", "on", "-t", "1", "-m", "256"]
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C",
               "PYTHONDONTWRITEBYTECODE": "1"}
MAX_INPUT = 64 * 1024
MAX_OUTPUT = 256 * 1024
MAX_RSS = 256 * 1024**2
MAX_WALL = 3.0


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fingerprint(path, maximum):
    digest, total = hashlib.sha256(), 0
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                and 0 < before.st_size <= maximum, "Invalid bounded Vampire file.")
        while part := stream.read(1024 * 1024):
            digest.update(part)
            total += len(part)
            require(total <= maximum, "Vampire file exceeded its size bound.")
        after = os.fstat(stream.fileno())
    require((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
            == (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
            and total == before.st_size, "Vampire file changed while reading.")
    return {"bytes": total, "sha256": digest.hexdigest()}


def package(*, verify_binary=False, require_ready=True):
    require(DIRECTORY.is_dir() and not DIRECTORY.is_symlink(), "Vampire is not installed locally.")
    manifest_path = DIRECTORY / "manifest.json"
    manifest_pin = fingerprint(manifest_path, 64 * 1024)
    manifest = json.loads(manifest_path.read_bytes())
    require(manifest.get("schema") == "hydra-playground-vampire-package-v1"
            and manifest.get("status") == "installed-not-executed"
            and manifest.get("version") == VERSION
            and manifest.get("release", {}).get("sha256") == ARCHIVE_SHA
            and manifest.get("allowed_solver_args") == SOLVER_ARGS,
            "The installed Vampire package does not match the pinned release.")
    descriptor = manifest["executable"]
    binary = DIRECTORY / "vampire"
    require(descriptor.get("path") == "vampire" and type(descriptor.get("bytes")) is int
            and 0 < descriptor["bytes"] <= 100 * 1024**2 and binary.is_file()
            and not binary.is_symlink() and binary.stat().st_size == descriptor["bytes"]
            and os.access(binary, os.X_OK), "The pinned Vampire executable is unavailable.")
    if verify_binary:
        require(fingerprint(binary, 100 * 1024**2)
                == {key: descriptor[key] for key in ("bytes", "sha256")}, "Vampire executable digest changed.")
    if require_ready:
        ready_path = DIRECTORY / "ready.json"
        fingerprint(ready_path, 64 * 1024)
        ready = json.loads(ready_path.read_bytes())
        require(ready.get("schema") == "hydra-playground-vampire-ready-v1"
                and ready.get("status") == "ready" and ready.get("version") == VERSION
                and ready.get("package_manifest") == manifest_pin
                and ready.get("install_exit_code") == 0
                and ready.get("version_exit_code") == 0 and ready.get("smoke_exit_code") == 0,
                "Vampire has not passed its actual local setup checks.")
    return binary, manifest, manifest_pin


def metadata_status():
    result = {"available": False, "name": "Vampire " + VERSION,
              "role": "untrusted first-order advice; native reconstruction required",
              "limits": {"wall_seconds": MAX_WALL, "cpu_seconds": 2,
                         "sampled_rss_bytes": MAX_RSS, "output_bytes": MAX_OUTPUT}}
    try:
        _, manifest, _ = package()
        result.update(available=True, binary_sha256=manifest["executable"]["sha256"],
                      detail="Local first-order search, proof-used hypotheses and native tactic reconstruction.")
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["detail"] = " ".join(str(error).split())[:400]
    return result


def spawn_argv():
    return [sys.executable, "-I", "-B", str(HELPER)]


def authorized_spawn(executable, argv, cwd, environment):
    return (executable == sys.executable and list(argv) == spawn_argv()
            and cwd == str(APP) and environment == ENVIRONMENT)


class VampireRunner:
    """One synchronous solver process at a time, with bounded captured output."""
    def __init__(self, *, require_ready=True):
        self.calls = 0
        self.records = []
        self.require_ready = require_ready

    def __call__(self, problem):
        require(type(problem) is str, "Vampire input must be generated TPTP text.")
        payload = problem.encode("utf-8")
        require(0 < len(payload) <= MAX_INPUT and b"\x00" not in payload, "Vampire input exceeds its bound.")
        # Only the AST exporter constructs these commands; reject directives
        # that could read problem files even if a caller violates that contract.
        require("include" not in problem.lower(),
                "Vampire file inclusion is disabled.")
        started = time.monotonic()
        problem_sha = hashlib.sha256(payload).hexdigest()
        result = {"status": "unavailable", "available": False, "executed": False,
                  "exit_code": None, "stdout": "", "stderr": "", "problem_sha256": problem_sha}
        try:
            _, manifest, _ = package(verify_binary=True, require_ready=self.require_ready)
        except (OSError, ValueError, KeyError, TypeError) as error:
            result["detail"] = str(error)[:500]
            return result
        result.update(available=True, binary_sha256=manifest["executable"]["sha256"])
        process = None
        selector = selectors.DefaultSelector()
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        failure = None
        try:
            process = subprocess.Popen(spawn_argv(), cwd=str(APP), env=dict(ENVIRONMENT),
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                       close_fds=True, start_new_session=False)
            self.calls += 1
            result["executed"] = True
            for name in ("stdin", "stdout", "stderr"):
                stream = getattr(process, name)
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_WRITE if name == "stdin" else selectors.EVENT_READ, name)
            offset = 0
            while selector.get_map() or process.poll() is None:
                if time.monotonic() - started >= MAX_WALL:
                    raise TimeoutError("Vampire reached its three-second wall limit.")
                for key, _ in selector.select(0.02):
                    if key.data == "stdin":
                        try:
                            offset += os.write(key.fd, payload[offset:offset + 16384])
                        except BrokenPipeError:
                            offset = len(payload)
                        except BlockingIOError:
                            continue
                        if offset == len(payload):
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                    else:
                        chunk = os.read(key.fd, 65536)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        buffers[key.data].extend(chunk)
                        if sum(len(value) for value in buffers.values()) > MAX_OUTPUT:
                            raise ValueError("Vampire exceeded its captured-output limit.")
            result["exit_code"] = process.wait(timeout=0.5)
            result["status"] = "completed" if result["exit_code"] == 0 else "failed"
        except (OSError, RuntimeError, ValueError, TimeoutError) as error:
            failure = str(error)[:500]
            result["status"] = "timeout" if isinstance(error, TimeoutError) else "failed"
        finally:
            if process is not None:
                if process.poll() is None:
                    process.kill()  # Only this unreaped direct child; never an arbitrary PID.
                result["exit_code"] = process.wait(timeout=0.5)
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None and not stream.closed:
                        stream.close()
            selector.close()
        result.update(stdout=bytes(buffers["stdout"]).decode("utf-8", "replace"),
                      stderr=bytes(buffers["stderr"]).decode("utf-8", "replace"),
                      elapsed_seconds=round(time.monotonic() - started, 4))
        if failure:
            result["detail"] = failure
        self.records.append({key: value for key, value in result.items() if key not in {"stdout", "stderr"}} | {
            "output_sha256": hashlib.sha256(bytes(buffers["stdout"])).hexdigest(),
            "output_bytes": sum(len(value) for value in buffers.values())})
        return result
