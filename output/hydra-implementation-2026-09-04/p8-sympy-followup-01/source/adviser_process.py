"""One fixed pinned CAS/SMT child, under a shared adviser-session lease.

This extends the existing owned-child Vampire lifecycle. It does not replace
Vampire's supervisor, grant arbitrary argv, create a process group, or weaken
the owning worker/server's separate process-group and memory safeguards.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import stat
import subprocess
import sys
import time

import vampire_process
import vampire_limits
from adviser_protocol import (AdviserRequest, MAX_INPUT, MAX_OUTPUT, POLICY, ProtocolError,
                              RequestLease, canonical_json, limits_for, read_json)


APP = Path(__file__).resolve().parent
HELPER = APP / "adviser_worker.py"
DIRECTORY = APP / ".runtime/advisers"
PACKAGES = DIRECTORY / "packages"
PACKAGE_SHA256 = "ea067a4ea690685589f7d3b6210ca12bd80e5ada20935d8aa7e43879343ac4c9"
PACKAGE_BYTES = 264593
BYTECODE_DIRECTORY = DIRECTORY / "cp311-precompiled-01"
BYTECODE_SHA256 = "55a6fe755ce000b52bb724bae2fa4824be97b80545dd6125e23418d53691bafa"
BYTECODE_BYTES = 996952
VERSIONS = {"sympy": "1.14.0", "cvc5": "1.3.4"}
ENVIRONMENT = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C",
               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
               "SYMPY_GROUND_TYPES": "python", "MPMATH_NOGMPY": "1"}
MAX_PACKAGE_BYTES = 200 * 1024**2


def _require(condition, message):
    if not condition:
        raise ProtocolError(message)


def _file_pin(path, maximum):
    digest, total = hashlib.sha256(), 0
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                 and 0 <= before.st_size <= maximum, "Invalid bounded adviser package file.")
        while part := stream.read(1024 * 1024):
            total += len(part)
            _require(total <= maximum, "Adviser package file grew beyond its bound.")
            digest.update(part)
        after = os.fstat(stream.fileno())
    _require((before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns)
             == (after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
             and total == before.st_size, "Adviser package file changed during verification.")
    return {"bytes": total, "sha256": digest.hexdigest()}


def package_directory(backend):
    _require(backend in VERSIONS, "Unsupported fixed adviser package.")
    return BYTECODE_DIRECTORY / "packages" if backend == "sympy" else PACKAGES


def package(*, backend="cvc5", verify_files=False, should_stop=None):
    packages = package_directory(backend)
    directory = packages.parent
    _require(directory.is_dir() and not directory.is_symlink() and packages.is_dir()
             and not packages.is_symlink(), "The isolated adviser package is not installed.")
    path = directory / "manifest.json"
    expected = ({"bytes": BYTECODE_BYTES, "sha256": BYTECODE_SHA256} if backend == "sympy"
                else {"bytes": PACKAGE_BYTES, "sha256": PACKAGE_SHA256})
    _require(_file_pin(path, 2 * 1024**2) == expected,
             "The adviser package manifest differs from the actual pinned installation.")
    raw = path.read_bytes()
    _require(len(raw) == expected["bytes"] and hashlib.sha256(raw).hexdigest() == expected["sha256"],
             "The pinned manifest changed while being read.")
    manifest = json.loads(raw)  # Already bound to the exact observed installed bytes.
    _require(manifest.get("platform") == "darwin-arm64" and manifest.get("python_abi") == "cp311",
             "Unsupported adviser package platform or schema.")
    if backend == "sympy":
        _require(manifest.get("schema") == "hydra-adviser-bytecode-package-v1"
                 and manifest.get("status") == "prepared-not-executed"
                 and manifest.get("source_manifest") == {"bytes": PACKAGE_BYTES, "sha256": PACKAGE_SHA256}
                 and manifest.get("python_version") == "3.11.12" and sys.version_info[:3] == (3, 11, 12)
                 and manifest.get("invalidation") == "CHECKED_HASH",
                 "The checked-hash bytecode package does not match this exact source/interpreter.")
    else:
        _require(manifest.get("schema") == "hydra-adviser-package-v1"
                 and manifest.get("status") == "installed-not-executed", "Unsupported source package schema.")
    files = manifest["files"]
    _require(type(files) is dict and len(files) <= 10000 and manifest["expanded_bytes"] <= MAX_PACKAGE_BYTES,
             "Installed adviser inventory exceeds its bound.")
    if verify_files:
        actual = set()
        for directory, folders, names in os.walk(packages, followlinks=False):
            for folder in folders:
                _require(not (Path(directory) / folder).is_symlink(), "Symlink in adviser import path.")
            for name in names:
                actual.add((Path(directory) / name).relative_to(packages).as_posix())
                _require(len(actual) <= len(files), "Unexpected file in adviser import path.")
        _require(actual == set(files), "Adviser import inventory changed.")
        total = 0
        for name, descriptor in files.items():
            if should_stop is not None and should_stop():
                raise TimeoutError("Adviser package verification reached cancellation or deadline.")
            _require(_file_pin(packages / name, MAX_PACKAGE_BYTES) == descriptor,
                     "An isolated adviser dependency changed: " + name[:120])
            total += descriptor["bytes"]
        _require(total == manifest["expanded_bytes"], "Adviser package byte accounting changed.")
    return manifest


def backend_identity(backend):
    _require(type(backend) is str and backend in VERSIONS, "Only the fixed SymPy/cvc5 helpers are enabled.")
    names = ("adviser_worker.py", "adviser_process.py", "adviser_protocol.py", "adviser_polynomials.py",
             "sympy_bridge.py" if backend == "sympy" else "smt_bridge.py")
    pins = {name: _file_pin(APP / name, 1024 * 1024) for name in names}
    # The reviewed Darwin reader is reused verbatim, not reimplemented with a
    # process-enumeration command or an unrelated PID lookup.
    pins["vampire_process.py"] = _file_pin(Path(vampire_process.__file__), 1024 * 1024)
    pins["vampire_limits.py"] = _file_pin(Path(vampire_limits.__file__), 1024 * 1024)
    return {"backend": backend, "version": VERSIONS[backend], "profile": "deep", "policy": POLICY,
            "package_sha256": BYTECODE_SHA256 if backend == "sympy" else PACKAGE_SHA256,
            "source_package_sha256": PACKAGE_SHA256,
            "package_format": "source+checked-hash-bytecode-cp311" if backend == "sympy" else "original-wheel-sources",
            "helper_sha256": pins["adviser_worker.py"]["sha256"],
            "helper_sources_sha256": hashlib.sha256(canonical_json(pins, 16384)).hexdigest(),
            "python_abi": "cp311", "platform": "darwin-arm64"}


def metadata_status(backend):
    result = {"backend": backend, "available": False, "limits": limits_for(backend),
              "kernel_checked": False, "validation": "package integrity only; not a native proof smoke test"}
    try:
        result["identity"] = backend_identity(backend)
        package(backend=backend)
        _require(sys.version_info[:2] == (3, 11) and sys.platform == "darwin" and os.uname().machine == "arm64",
                 "This pinned backend requires the worker's Python 3.11 on macOS.")
        result["available"] = True
    except (OSError, ValueError, KeyError, TypeError) as error:
        result["detail"] = str(error)[:400]
    return result


def spawn_argv(backend):
    _require(type(backend) is str and backend in VERSIONS, "Unknown fixed adviser child.")
    # -S prevents site/.pth startup hooks and accidental model-environment imports.
    return [sys.executable, "-I", "-S", "-B", str(HELPER), "--backend", backend]


def authorized_spawn(executable, argv, cwd, environment, *, backend):
    try:
        expected = spawn_argv(backend)
    except ProtocolError:
        return False
    return (executable == sys.executable and type(argv) in (list, tuple) and list(argv) == expected
            and cwd == str(APP) and environment == ENVIRONMENT)


class AdviserRunner:
    def __init__(self, backend):
        _require(type(backend) is str and backend in VERSIONS, "Unsupported adviser runner.")
        self.backend = backend
        self.calls = 0
        self.records = []
        self._owner = None

    @property
    def identity(self):
        return backend_identity(self.backend)

    def __call__(self, lease):
        _require(type(lease) is RequestLease and not lease.completed
                 and lease._owner._active is lease, "A live shared-session lease is required before dispatch.")
        _require(self._owner is None or self._owner is lease._owner,
                 "An adviser runner and its bounded records belong to one search session.")
        self._owner = lease._owner
        request = lease.request
        _require(type(request) is AdviserRequest and request.backend == self.backend
                 and type(request.data) is bytes and 0 < len(request.data) <= MAX_INPUT,
                 "The lease does not authorize this exact bounded helper input.")
        started = time.monotonic()
        bounds = limits_for(self.backend)
        result = {"status": "unavailable", "available": False, "executed": False,
            "exit_code": None, "stdout": b"", "stderr": b"", "input_sha256": request.input_sha256,
            "elapsed_seconds": 0.0, "peak_rss_bytes": None, "rss_samples": 0,
            "rss_measurement": "sampled owned-child RSS; no measurement when samples is zero",
            "quiescent": True, "limits": bounds, "termination": {"reason": "not_launched"}}
        process = None
        selector = None
        buffers = {"stdout": bytearray(), "stderr": bytearray()}
        reason = "not_launched"
        try:
            identity = self.identity
            result["identity"] = identity
            _require(read_json(request.identity, 4096) == identity, "Bound helper identity changed before launch.")
            _require(sys.version_info[:2] == (3, 11) and sys.platform == "darwin" and os.uname().machine == "arm64",
                     "The pinned child requires Python 3.11 on macOS.")
            package(backend=self.backend, verify_files=True,
                    should_stop=lambda: lease._owner.cancelled() or time.monotonic() >= lease.deadline)
            vampire_process._resident_size(os.getpid())
            result["available"] = True
            if lease._owner.cancelled():
                result["status"], reason = "cancelled", "cancelled_before_launch"
            elif time.monotonic() >= lease.deadline:
                result["status"], reason = "timeout", "deadline_before_launch"
            else:
                process = subprocess.Popen(spawn_argv(self.backend), cwd=str(APP), env=dict(ENVIRONMENT),
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    close_fds=True, start_new_session=False)
                self.calls += 1
                result.update(executed=True, quiescent=False)
                selector = selectors.DefaultSelector()
                for name in ("stdin", "stdout", "stderr"):
                    stream = getattr(process, name)
                    os.set_blocking(stream.fileno(), False)
                    selector.register(stream, selectors.EVENT_WRITE if name == "stdin" else selectors.EVENT_READ, name)
                offset, next_sample = 0, 0.0
                while selector.get_map() or process.poll() is None:
                    now = time.monotonic()
                    if lease._owner.cancelled():
                        result["status"], reason = "cancelled", "caller_cancelled"
                        break
                    if now >= lease.deadline:
                        result["status"], reason = "timeout", "outer_wall_watchdog"
                        break
                    if now >= next_sample:
                        next_sample = now + bounds["sample_interval_seconds"]
                        try:
                            rss = vampire_process._owned_child_rss(process)
                        except (OSError, ValueError):
                            result["status"], reason = "failed", "owned_child_rss_accounting_error"
                            break
                        if rss is not None:
                            result["rss_samples"] += 1
                            result["peak_rss_bytes"] = max(result["peak_rss_bytes"] or 0, rss)
                            if rss > bounds["sampled_stop_bytes"]:
                                result["status"], reason = "resource_limit", "owned_child_rss_watchdog"
                                break
                    for key, _ in selector.select(min(bounds["sample_interval_seconds"], max(0.0, lease.deadline - now))):
                        if key.data == "stdin":
                            try:
                                offset += os.write(key.fd, request.data[offset:offset + 16384])
                            except BrokenPipeError:
                                offset = len(request.data)
                            except BlockingIOError:
                                continue
                            if offset == len(request.data):
                                selector.unregister(key.fileobj)
                                key.fileobj.close()
                        else:
                            try:
                                part = os.read(key.fd, 65536)
                            except BlockingIOError:
                                continue
                            if not part:
                                selector.unregister(key.fileobj)
                                continue
                            room = MAX_OUTPUT - sum(len(buffer) for buffer in buffers.values())
                            buffers[key.data].extend(part[:room])
                            if len(part) > room:
                                result["status"], reason = "output_limit", "combined_output_limit"
                                break
                    if reason == "combined_output_limit":
                        break
                if reason == "not_launched":
                    result["exit_code"] = process.wait(timeout=bounds["cleanup_seconds"])
                    result["status"] = "completed" if result["exit_code"] == 0 else "failed"
                    reason = "process_exit" if result["exit_code"] >= 0 else "process_signal"
                    if result["exit_code"] == -signal.SIGXCPU:
                        result["status"], reason = "resource_limit", "cpu_limit_signal"
                    elif result["exit_code"] == -signal.SIGALRM:
                        result["status"], reason = "timeout", "helper_wall_alarm"
        except TimeoutError as error:
            result["status"] = "cancelled" if lease._owner.cancelled() else "timeout"
            reason = "verification_cancelled_or_timed_out"
            result["detail"] = str(error)[:400]
        except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired) as error:
            result["status"] = "failed" if process is not None else "unavailable"
            reason = "runner_io_error" if process is not None else "preflight_failed"
            result["detail"] = str(error)[:400]
        finally:
            if process is not None:
                try:
                    if process.poll() is None:
                        process.kill()  # This unreaped owned Popen only; never a supplied PID/group.
                    result["exit_code"] = process.wait(timeout=bounds["cleanup_seconds"])
                    result["quiescent"] = True
                except (OSError, subprocess.TimeoutExpired) as error:
                    result.update(status="failed", quiescent=False, detail=str(error)[:400])
                    reason = "owned_child_reap_unconfirmed"
                for stream in (process.stdin, process.stdout, process.stderr):
                    if stream is not None and not stream.closed:
                        stream.close()
            if selector is not None:
                selector.close()
        result.update(stdout=bytes(buffers["stdout"]), stderr=bytes(buffers["stderr"]),
                      elapsed_seconds=max(0.0, time.monotonic() - started), termination={"reason": reason})
        # Transport/cancellation/resource authority is never reclassified by text
        # in stdout, even if an apparent complete proof was emitted before a stop.
        self.records.append({key: value for key, value in result.items() if key not in {"stdout", "stderr"}} | {
            "stdout_bytes": len(result["stdout"]), "stderr_bytes": len(result["stderr"]),
            "stdout_sha256": hashlib.sha256(result["stdout"]).hexdigest()})
        return result
