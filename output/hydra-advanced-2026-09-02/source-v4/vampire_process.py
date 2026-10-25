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

from vampire_limits import (MAX_INPUT, MAX_OUTPUT, RUNTIME_POLICY, classify_termination,
                            helper_arguments, solver_args, solver_limits)

APP = Path(__file__).resolve().parent
DIRECTORY = APP / ".runtime/vampire"
HELPER = APP / "vampire_worker.py"
VERSION = "5.0.1"
ARCHIVE_SHA = "8c92e649fe7bc622a70000afbdf5a5c51007b384e2d8b8235c95474cc7a68f35"
# The immutable installer manifest and its ready record attest these original
# standard arguments only. New profiles are a separate, explicit runtime policy.
SOLVER_ARGS = solver_args("standard")
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C",
               "PYTHONDONTWRITEBYTECODE": "1"}
MAX_RSS = solver_limits()["sampled_rss_bytes"]
MAX_WALL = solver_limits()["wall_seconds"]


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


def _runtime_metadata(profile, *, ready_verified=False):
    return {"runtime_policy": RUNTIME_POLICY, "profile": profile,
            "solver_args": solver_args(profile), "limits": solver_limits(profile),
            "package_smoke": {"profile": "standard", "ready_record_verified": ready_verified,
                              "covers_selected_profile": ready_verified and profile == "standard"}}


def metadata_status(profile="standard"):
    result = {"available": False, "name": "Vampire " + VERSION,
              "role": "untrusted first-order advice; native reconstruction required",
              **_runtime_metadata(profile)}
    try:
        _, manifest, _ = package()
        result.update(available=True, binary_sha256=manifest["executable"]["sha256"],
                      **_runtime_metadata(profile, ready_verified=True),
                      detail="Local first-order search, proof-used hypotheses and native tactic reconstruction.")
        if profile != "standard":
            result["detail"] += " The original installation smoke did not cover this profile."
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["detail"] = " ".join(str(error).split())[:400]
    return result


def spawn_argv(profile="standard"):
    return [sys.executable, "-I", "-B", str(HELPER), *helper_arguments(profile)]


def authorized_spawn(executable, argv, cwd, environment, profile="standard"):
    try:
        expected = spawn_argv(profile)
    except ValueError:
        return False
    return (executable == sys.executable and type(argv) in (list, tuple) and list(argv) == expected
            and cwd == str(APP) and environment == ENVIRONMENT)


class VampireRunner:
    """One synchronous solver process at a time, with bounded captured output."""
    def __init__(self, profile="standard", *, require_ready=True):
        self.profile = solver_limits(profile)["profile"]
        self.calls = 0
        self.records = []
        self.require_ready = require_ready

    def __call__(self, problem):
        limits = solver_limits(self.profile)
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
                  "exit_code": None, "stdout": "", "stderr": "", "problem_sha256": problem_sha,
                  **_runtime_metadata(self.profile)}
        try:
            _, manifest, _ = package(verify_binary=True, require_ready=self.require_ready)
        except (OSError, ValueError, KeyError, TypeError) as error:
            result["detail"] = str(error)[:500]
            return result
        result.update(available=True, binary_sha256=manifest["executable"]["sha256"],
                      **_runtime_metadata(self.profile, ready_verified=self.require_ready is True))
        process = None
        selector = selectors.DefaultSelector()
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        failure = None
        wall_timed_out = False
        output_limited = False
        try:
            process = subprocess.Popen(spawn_argv(self.profile), cwd=str(APP), env=dict(ENVIRONMENT),
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
                if time.monotonic() - started >= limits["wall_seconds"]:
                    wall_timed_out = True
                    raise TimeoutError(f"Vampire reached its {limits['wall_seconds']}-second wall limit.")
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
                        remaining = MAX_OUTPUT - sum(len(value) for value in buffers.values())
                        buffers[key.data].extend(chunk[:remaining])
                        if len(chunk) > remaining:
                            output_limited = True
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
        decoded = {name: bytes(value).decode("utf-8", "replace") for name, value in buffers.items()}
        # Replacement characters can expand malformed UTF-8. Keep even this
        # display representation within the combined bound and refuse advice.
        remaining = MAX_OUTPUT
        for name in ("stdout", "stderr"):
            encoded = decoded[name].encode("utf-8")
            if len(encoded) > remaining:
                output_limited = True
                decoded[name] = encoded[:remaining].decode("utf-8", "ignore")
            remaining -= len(decoded[name].encode("utf-8"))
        result.update(stdout=decoded["stdout"], stderr=decoded["stderr"],
                      stdout_bytes=len(buffers["stdout"]), stderr_bytes=len(buffers["stderr"]),
                      elapsed_seconds=round(time.monotonic() - started, 4))
        result.update(classify_termination(result["stdout"], result["stderr"], exit_code=result["exit_code"],
                                           wall_timed_out=wall_timed_out, output_limited=output_limited))
        if failure and result["status"] == "completed":
            result["status"] = "failed"
            result["termination"]["reason"] = "runner_io_error"
        if failure:
            result["detail"] = failure
        self.records.append({key: value for key, value in result.items() if key not in {"stdout", "stderr"}} | {
            "output_sha256": hashlib.sha256(bytes(buffers["stdout"])).hexdigest(),
            "output_bytes": sum(len(value) for value in buffers.values())})
        return result
