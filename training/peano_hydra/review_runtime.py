"""Sequential owned-process limits and OS resource receipts for review work.

No shell, no inherited Lean search path, no process-wide cache flushing, and
no model/provider startup. Kills affect only the new child's process group.
macOS RSS is sampled; it is explicitly not an instantaneous hard cap.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import base64
import hashlib
import math
import os
from pathlib import Path
import re
import signal
import stat
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "scripts" / "hydra_bounded_exec.py"
RESOURCE_MEASUREMENT = "owned-child wait4; RSS guard sampled at 100ms; no hardware attestation"
_MAX_INPUT_BYTES = 16 * 1024**2
_MAX_COUNTER = 2**63 - 1
_PROCESS_FIELDS = frozenset({
    "command", "limits", "stdin_bytes", "stdin_sha256", "returncode", "reason",
    "stdout", "stderr", "output_encoding", "raw_output_base64", "output_truncated",
    "stdout_bytes", "stderr_bytes", "stdout_sha256", "stderr_sha256", "resources",
    "observed_descendant_count", "resource_measurement",
})
_RESOURCE_FIELDS = frozenset({
    "wall_seconds", "cpu_seconds", "peak_rss_bytes", "sampled_peak_group_rss_bytes",
    "cpu_instructions", "energy_joules",
})
_REASONS = frozenset({
    "exited", "wall_limit", "cpu_limit", "rss_limit", "output_limit",
    "unexpected_descendant", "invalid_output_encoding",
})
_EXTRA_FIELD = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}\Z")


class ReviewRuntimeError(ValueError):
    """A review worker cannot run under its declared safe contract."""


@dataclass(frozen=True)
class ProcessLimits:
    wall_seconds: int = 45
    cpu_seconds: int = 30
    rss_bytes: int = 1024**3
    output_bytes: int = 1024**2

    def __post_init__(self) -> None:
        ceilings = {"wall_seconds": 180, "cpu_seconds": 120,
                    "rss_bytes": 2 * 1024**3, "output_bytes": 8 * 1024**2}
        for key, ceiling in ceilings.items():
            value = getattr(self, key)
            if type(value) is not int or not 1 <= value <= ceiling:
                raise ReviewRuntimeError(f"invalid process bound: {key}")
        if self.cpu_seconds > self.wall_seconds or self.rss_bytes < 128 * 1024**2:
            raise ReviewRuntimeError("inconsistent CPU/wall/RSS bounds")

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def hash_file(path: Path, *, maximum: int = 512 * 1024**2) -> dict[str, object]:
    """Hash a regular bounded input without loading a compiler/library into RAM."""
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    digest = hashlib.sha256()
    with os.fdopen(descriptor, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > maximum:
            raise ReviewRuntimeError(f"not one bounded regular input: {path}")
        size = 0
        while block := stream.read(1024**2):
            size += len(block)
            if size > maximum:
                raise ReviewRuntimeError("input grew beyond its bound")
            digest.update(block)
        after = os.fstat(stream.fileno())
    if (before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (
        after.st_size, after.st_mtime_ns, after.st_ctime_ns
    ) or size != after.st_size:
        raise ReviewRuntimeError("input changed while hashing")
    return {"bytes": size, "sha256": digest.hexdigest()}


def _validate_request(command: tuple[str, ...], limits: ProcessLimits, input_bytes: bytes) -> None:
    if type(limits) is not ProcessLimits:
        raise ReviewRuntimeError("worker limits must be an exact ProcessLimits value")
    # Revalidate even a value changed through reflection after construction.
    ProcessLimits(**limits.to_dict())
    try:
        valid_command = (
            type(command) is tuple and 1 <= len(command) <= 1024
            and all(type(value) is str and value and "\x00" not in value
                    and len(value.encode("utf-8")) <= 16384 for value in command)
            and Path(command[0]).is_absolute()
        )
    except UnicodeError:
        valid_command = False
    if not valid_command:
        raise ReviewRuntimeError("expected one bounded shell-free executable tuple")
    if type(input_bytes) is not bytes or len(input_bytes) > _MAX_INPUT_BYTES:
        raise ReviewRuntimeError("worker request exceeds its reservation")


def _counter(value: object, label: str) -> int:
    if type(value) is not int or not 0 <= value <= _MAX_COUNTER:
        raise ReviewRuntimeError(f"{label} must be a bounded nonnegative integer")
    return value


def _seconds(value: object, label: str) -> int | float:
    # The broad counter ceiling is only a representation guard. A limited
    # child may legitimately overshoot its requested budget before sampling or
    # OS accounting; only an ordinary exit must fit the requested ceilings.
    if type(value) not in (int, float) or not 0 <= value <= _MAX_COUNTER or not math.isfinite(value):
        raise ReviewRuntimeError(f"{label} must be a bounded finite nonnegative number")
    return value


def validate_process_record(
    record: dict[str, object], *, command: tuple[str, ...], limits: ProcessLimits,
    input_bytes: bytes = b"", success_codes: tuple[int, ...] | None = None,
    extra_fields: tuple[str, ...] = (),
) -> None:
    """Validate one exact worker receipt, without treating a failure as success.

    Hashes cover the complete supplied stdin and the retained output prefixes.
    Output byte counts describe the full temporary streams, possibly larger
    than those prefixes. Caller-declared extra fields must be present; their
    semantic contents remain the caller's responsibility. Failed runs retain
    honest over-limit measurements instead of being forced into success bounds.
    """
    _validate_request(command, limits, input_bytes)
    if (type(extra_fields) is not tuple or len(extra_fields) > 16
        or any(type(name) is not str or _EXTRA_FIELD.fullmatch(name) is None
               or name in _PROCESS_FIELDS for name in extra_fields)
        or len(set(extra_fields)) != len(extra_fields)):
        raise ReviewRuntimeError("extra process fields must be distinct explicit non-reserved names")
    if (success_codes is not None and
        (type(success_codes) is not tuple or not success_codes or len(success_codes) > 256
         or any(type(code) is not int or not 0 <= code <= 255 for code in success_codes)
         or len(set(success_codes)) != len(success_codes))):
        raise ReviewRuntimeError("success codes must be distinct normal Unix exit codes")
    if type(record) is not dict or set(record) != _PROCESS_FIELDS | set(extra_fields):
        raise ReviewRuntimeError("process receipt has missing or unknown fields")
    if (type(record["command"]) is not list
        or any(type(value) is not str for value in record["command"])
        or record["command"] != list(command)):
        raise ReviewRuntimeError("process receipt changed its exact command")
    saved_limits = record["limits"]
    if (type(saved_limits) is not dict or set(saved_limits) != set(limits.to_dict())
        or any(type(value) is not int for value in saved_limits.values())
        or saved_limits != limits.to_dict()):
        raise ReviewRuntimeError("process receipt changed its exact limits")
    if (type(record["stdin_bytes"]) is not int or record["stdin_bytes"] != len(input_bytes)
        or type(record["stdin_sha256"]) is not str
        or record["stdin_sha256"] != hashlib.sha256(input_bytes).hexdigest()):
        raise ReviewRuntimeError("process receipt changed its exact stdin bytes/hash")
    reason, code = record["reason"], record["returncode"]
    if type(reason) is not str or reason not in _REASONS:
        raise ReviewRuntimeError("unknown process termination reason")
    if type(code) is not int or not -127 <= code <= 255:
        raise ReviewRuntimeError("process return code is not an exact Unix exit/signal integer")
    if type(record["resource_measurement"]) is not str or record["resource_measurement"] != RESOURCE_MEASUREMENT:
        raise ReviewRuntimeError("process resource-measurement contract changed")
    descendants = _counter(record["observed_descendant_count"], "observed descendant count")

    if type(record["output_truncated"]) is not bool:
        raise ReviewRuntimeError("output_truncated must be an exact Boolean")
    sizes = {name: _counter(record[name + "_bytes"], name + " byte count") for name in ("stdout", "stderr")}
    truncated = max(sizes.values()) > limits.output_bytes
    if record["output_truncated"] is not truncated:
        raise ReviewRuntimeError("output truncation and full byte counts disagree")
    encoding = record["output_encoding"]
    streams: dict[str, bytes] = {}
    if type(encoding) is str and encoding == "utf-8":
        if record["raw_output_base64"] is not None:
            raise ReviewRuntimeError("UTF-8 output must not contain a raw fallback")
        for name in ("stdout", "stderr"):
            if type(record[name]) is not str or len(record[name]) > limits.output_bytes:
                raise ReviewRuntimeError("retained UTF-8 output is not bounded exact text")
            try:
                streams[name] = record[name].encode("utf-8")
            except UnicodeError:
                raise ReviewRuntimeError("retained text is not valid UTF-8") from None
        if reason == "invalid_output_encoding":
            raise ReviewRuntimeError("encoding-failure reason has valid UTF-8 output")
    elif type(encoding) is str and encoding == "invalid-utf8-base64-preserved":
        raw = record["raw_output_base64"]
        if (type(raw) is not dict or set(raw) != {"stdout", "stderr"}
            or type(record["stdout"]) is not str or record["stdout"] != ""
            or type(record["stderr"]) is not str or record["stderr"] != ""
            or reason != "invalid_output_encoding"):
            raise ReviewRuntimeError("invalid UTF-8 fallback shape or termination reason")
        invalid = False
        for name in ("stdout", "stderr"):
            value = raw[name]
            if type(value) is not str or len(value) > 4 * ((limits.output_bytes + 2) // 3):
                raise ReviewRuntimeError("raw output base64 exceeds its exact retained bound")
            try:
                streams[name] = base64.b64decode(value.encode("ascii"), validate=True)
            except (ValueError, UnicodeError):
                raise ReviewRuntimeError("raw output is not strict base64") from None
            if base64.b64encode(streams[name]).decode("ascii") != value:
                raise ReviewRuntimeError("raw output base64 is not canonical")
            try:
                streams[name].decode("utf-8")
            except UnicodeDecodeError:
                invalid = True
        if not invalid:
            raise ReviewRuntimeError("raw fallback does not preserve any invalid UTF-8")
    else:
        raise ReviewRuntimeError("unknown output encoding")
    for name, retained in streams.items():
        if len(retained) != min(sizes[name], limits.output_bytes):
            raise ReviewRuntimeError("retained output length disagrees with full byte count and bound")
        digest = record[name + "_sha256"]
        if type(digest) is not str or digest != hashlib.sha256(retained).hexdigest():
            raise ReviewRuntimeError("retained output hash differs from its exact bytes")
    if reason == "output_limit" and not truncated:
        raise ReviewRuntimeError("output-limit receipt did not exceed its output bound")
    if truncated and reason not in {"output_limit", "invalid_output_encoding"}:
        raise ReviewRuntimeError("truncated output lost its limit/encoding termination reason")

    resources = record["resources"]
    if type(resources) is not dict or set(resources) != _RESOURCE_FIELDS:
        raise ReviewRuntimeError("process resource fields changed")
    wall = _seconds(resources["wall_seconds"], "wall seconds")
    cpu = _seconds(resources["cpu_seconds"], "CPU seconds")
    peak = _counter(resources["peak_rss_bytes"], "peak RSS")
    sampled = resources["sampled_peak_group_rss_bytes"]
    if sampled is not None:
        _counter(sampled, "sampled group peak RSS")
    if resources["cpu_instructions"] is not None or resources["energy_joules"] is not None:
        raise ReviewRuntimeError("unmeasured CPU instructions/energy must remain null")
    if reason == "exited":
        if (wall > limits.wall_seconds or cpu > limits.cpu_seconds or peak > limits.rss_bytes
            or (sampled is not None and sampled > limits.rss_bytes)
            or descendants != 0 or code == -signal.SIGXCPU):
            raise ReviewRuntimeError("ordinary exit exceeded its resource/descendant contract")
    if reason == "unexpected_descendant" and descendants == 0:
        raise ReviewRuntimeError("descendant failure has no observed descendant")
    if reason == "wall_limit" and wall < limits.wall_seconds:
        raise ReviewRuntimeError("wall-limit receipt did not reach its wall bound")
    if reason == "cpu_limit" and cpu <= limits.cpu_seconds and code != -signal.SIGXCPU:
        raise ReviewRuntimeError("CPU-limit receipt lacks excess CPU or SIGXCPU evidence")
    if reason == "rss_limit" and max(peak, sampled or 0) <= limits.rss_bytes:
        raise ReviewRuntimeError("RSS-limit receipt did not exceed its RSS bound")
    if success_codes is not None and (
        reason != "exited" or code not in success_codes or truncated
        or encoding != "utf-8" or descendants != 0
    ):
        raise ReviewRuntimeError("process receipt is not an expected complete successful exit")


def _kill_owned_group(pid: int) -> None:
    try:
        os.killpg(pid, signal.SIGKILL)
    except ProcessLookupError:
        pass


def _group_members(pid: int) -> list[tuple[int, int]]:
    """PID/RSS only, never other processes' arguments or environment."""
    executable = "/bin/ps" if Path("/bin/ps").is_file() else "/usr/bin/ps"
    try:
        result = subprocess.run([executable, "-axo", "pid=,pgid=,rss="],
                                capture_output=True, text=True, timeout=1, check=False)
        if result.returncode != 0 or len(result.stdout) > 4 * 1024**2:
            raise ReviewRuntimeError("owned process-group accounting unavailable")
        members = []
        for line in result.stdout.splitlines():
            fields = line.split()
            if len(fields) == 3 and all(value.isdigit() for value in fields):
                process_id, group, rss_kib = map(int, fields)
                if group == pid:
                    members.append((process_id, rss_kib * 1024))
        return members
    except (OSError, subprocess.TimeoutExpired) as error:
        raise ReviewRuntimeError("owned process-group accounting unavailable") from error


def run_bounded(
    command: tuple[str, ...], *, cwd: Path, limits: ProcessLimits,
    input_bytes: bytes = b"", lean_path: Path | None = None,
) -> dict[str, object]:
    """Run one sequential child, retaining bounded output and wait4 measurements.

    Source-reviewed workers must not spawn descendants. Sampled group checks
    reject observed descendants and every exit cleans up the owned group.
    This is resource supervision, not a sandbox for hostile executables.
    Nonzero exits are observations (Lean intentionally rejects mutations), not
    fabricated proofs. The caller interprets only exact expected protocol rows.
    """
    _validate_request(command, limits, input_bytes)
    if not hasattr(os, "wait4") or sys.platform not in {"linux", "darwin"}:
        raise ReviewRuntimeError("review workers require Unix wait4 accounting")
    environment = {name: value for name, value in os.environ.items()
                   if not name.startswith(("LD_", "DYLD_"))}
    for name in ("LEAN_PATH", "LEAN_SRC_PATH", "LEAN_SYSROOT", "LEAN_OPTS"):
        environment.pop(name, None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONMALLOC"] = "malloc"
    if lean_path is not None:
        environment["LEAN_PATH"] = str(lean_path.resolve())
    guarded = (sys.executable, str(GUARD), "--cpu-seconds", str(limits.cpu_seconds),
               "--rss-bytes", str(limits.rss_bytes), "--", *command)
    started = time.monotonic()
    reason = "exited"
    sampled_peak = None
    observed_descendants = set()
    next_sample = started
    with tempfile.TemporaryFile() as incoming, tempfile.TemporaryFile() as outgoing, tempfile.TemporaryFile() as errors:
        incoming.write(input_bytes)
        incoming.seek(0)
        process = subprocess.Popen(
            guarded, stdin=incoming, stdout=outgoing, stderr=errors,
            cwd=cwd, env=environment, start_new_session=True,
        )
        try:
            while True:
                reaped, status, usage = os.wait4(process.pid, os.WNOHANG)
                if reaped:
                    process.returncode = os.waitstatus_to_exitcode(status)
                    members = _group_members(process.pid)
                    observed_descendants.update(member for member, _ in members if member != process.pid)
                    if observed_descendants:
                        reason = "unexpected_descendant"
                    _kill_owned_group(process.pid)
                    break
                now = time.monotonic()
                if now - started >= limits.wall_seconds:
                    reason = "wall_limit"
                if max(os.fstat(outgoing.fileno()).st_size, os.fstat(errors.fileno()).st_size) > limits.output_bytes:
                    reason = "output_limit"
                if now >= next_sample and reason == "exited":
                    members = _group_members(process.pid)
                    current = sum(rss for _, rss in members) if members else None
                    observed_descendants.update(member for member, _ in members if member != process.pid)
                    if observed_descendants:
                        reason = "unexpected_descendant"
                    if current is not None:
                        sampled_peak = max(sampled_peak or 0, current)
                        if current > limits.rss_bytes:
                            reason = "rss_limit"
                    next_sample = time.monotonic() + 0.1
                if reason != "exited":
                    _kill_owned_group(process.pid)
                    _, status, usage = os.wait4(process.pid, 0)
                    process.returncode = os.waitstatus_to_exitcode(status)
                    break
                time.sleep(0.02)
        except BaseException:
            _kill_owned_group(process.pid)
            try:
                _, status, _ = os.wait4(process.pid, 0)
                process.returncode = os.waitstatus_to_exitcode(status)
            except ChildProcessError:
                pass
            raise
        elapsed = time.monotonic() - started
        stdout_size, stderr_size = os.fstat(outgoing.fileno()).st_size, os.fstat(errors.fileno()).st_size
        outgoing.seek(0)
        errors.seek(0)
        stdout, stderr = outgoing.read(limits.output_bytes), errors.read(limits.output_bytes)
    peak = int(usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024)
    cpu = float(usage.ru_utime + usage.ru_stime)
    if reason == "exited" and process.returncode == -signal.SIGXCPU:
        reason = "cpu_limit"
    if reason == "exited" and elapsed > limits.wall_seconds:
        reason = "wall_limit"
    if reason == "exited" and cpu > limits.cpu_seconds:
        reason = "cpu_limit"
    if reason == "exited" and peak > limits.rss_bytes:
        reason = "rss_limit"
    if max(stdout_size, stderr_size) > limits.output_bytes:
        reason = "output_limit"
    if not all(math.isfinite(value) and value >= 0 for value in (elapsed, cpu, peak)):
        raise ReviewRuntimeError("invalid OS resource readings")
    encoding = "utf-8"
    raw_fallback = None
    try:
        stdout_text, stderr_text = stdout.decode("utf-8"), stderr.decode("utf-8")
    except UnicodeDecodeError:
        reason = "invalid_output_encoding"
        encoding = "invalid-utf8-base64-preserved"
        raw_fallback = {"stdout": base64.b64encode(stdout).decode("ascii"),
                        "stderr": base64.b64encode(stderr).decode("ascii")}
        stdout_text = stderr_text = ""
    result = {
        "command": list(command), "limits": limits.to_dict(), "returncode": process.returncode,
        "stdin_bytes": len(input_bytes), "stdin_sha256": hashlib.sha256(input_bytes).hexdigest(),
        "reason": reason, "stdout": stdout_text, "stderr": stderr_text,
        "output_encoding": encoding, "raw_output_base64": raw_fallback,
        "output_truncated": max(stdout_size, stderr_size) > limits.output_bytes,
        "stdout_bytes": stdout_size, "stderr_bytes": stderr_size,
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
        "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "resources": {"wall_seconds": elapsed, "cpu_seconds": cpu,
                      "peak_rss_bytes": peak, "sampled_peak_group_rss_bytes": sampled_peak,
                      "cpu_instructions": None, "energy_joules": None},
        "observed_descendant_count": len(observed_descendants),
        "resource_measurement": RESOURCE_MEASUREMENT,
    }
    validate_process_record(result, command=command, limits=limits, input_bytes=input_bytes)
    return result
