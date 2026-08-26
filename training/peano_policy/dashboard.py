"""Read-only live status collection for Peano policy training on WMI.

The dashboard is deliberately an observer, never part of the training
authority.  It asks Slurm for scheduler/resource state and reads bounded tails
of already-existing artifacts.  It does not signal the job, create remote
files, or infer successful training from a progress bar.

The public entry point :func:`fetch_dashboard_status` returns a JSON-ready
record.  Parsing helpers are kept pure so recorded WMI output can be exercised
without a network connection.
"""

from __future__ import annotations

import ast
from datetime import datetime, timezone
import json
import math
import re
import subprocess
import time
from typing import Callable, Mapping


DASHBOARD_SCHEMA = "peano-policy-training-dashboard"
DASHBOARD_VERSION = 1
REMOTE_SNAPSHOT_SCHEMA = "peano-policy-training-remote-snapshot"
REMOTE_SNAPSHOT_VERSION = 1
DEFAULT_SSH_TARGET = "wmicluster"
DEFAULT_JOB_ID = "217859"
SSH_TIMEOUT_SECONDS = 25
MAX_REMOTE_RESPONSE_BYTES = 2_000_000
MAX_LOG_DISPLAY_CHARS = 48_000
MAX_LOSS_POINTS = 2_000

_SSH_TARGET_RE = re.compile(
    r"[A-Za-z0-9._-]+(?:@[A-Za-z0-9.-]+)?\Z"
)
_JOB_ID_RE = re.compile(r"[0-9]+\Z")
_TERMINAL_FAILURE_STATES = frozenset(
    {
        "BOOT_FAIL",
        "CANCELLED",
        "DEADLINE",
        "FAILED",
        "NODE_FAIL",
        "OUT_OF_MEMORY",
        "PREEMPTED",
        "REVOKED",
        "TIMEOUT",
    }
)
_LIVE_STATES = frozenset(
    {"CONFIGURING", "COMPLETING", "PENDING", "RUNNING", "SUSPENDED"}
)
_TQDM_RE = re.compile(
    r"(?P<display_percent>[0-9]{1,3})%\|[^|\r\n]*\|\s*"
    r"(?P<step>[0-9]+)/(?P<total>[0-9]+)\s*\["
    r"(?P<body>[^\]\r\n]+)\]"
)
_RATE_RE = re.compile(r"(?P<value>[0-9]+(?:\.[0-9]+)?)(?P<unit>s/it|it/s)")
_GPU_TRES_RE = re.compile(
    r"(?:^|,)gres/gpu:(?P<kind>[A-Za-z0-9_-]+)=(?P<count>[0-9]+)(?:,|$)"
)


class DashboardError(RuntimeError):
    """The live observer could not obtain or validate a status snapshot."""


# This source is sent verbatim to ``python3 - JOB_ID`` on WMI.  Every path is
# fixed below or derived from a decimal job id.  All file opens are read-only,
# subprocesses use argv lists, and every response component has a byte ceiling.
REMOTE_SNAPSHOT_SOURCE = r'''from __future__ import annotations
import datetime
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

ROOT = Path("/work/bnaskrecki/peano-lab-training")
MAX_COMMAND = 65536
MAX_STDOUT_TAIL = 262144
MAX_STDERR_TAIL = 262144
MAX_JSON = 8388608
MAX_RECOVERY_MANIFEST = 1048576
MAX_SAMPLE_LINE = 1000000
MAX_SAMPLE_SCAN = 1048576
MAX_SAMPLES = 4
JOB_RE = re.compile(r"[0-9]+\Z")
TRAIN_PATH_RE = re.compile(
    r"checkpoints/corpora/peano-policy-v3-[0-9]+/data/train[.]jsonl\Z"
)
SNAPSHOT_RE = re.compile(r"step-([0-9]{8})-run-[0-9a-f]{16}-job-([0-9]+)\Z")

def command(argv):
    try:
        result = subprocess.run(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=8,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"returncode": None, "stdout": "", "stderr": str(exc)}
    def bounded(value):
        value = value[:MAX_COMMAND]
        return value.decode("utf-8", errors="replace")
    return {
        "returncode": result.returncode,
        "stdout": bounded(result.stdout),
        "stderr": bounded(result.stderr),
    }

def ordinary_file(path):
    try:
        metadata = path.lstat()
    except OSError:
        return None
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        return None
    return metadata

def tail(path, limit):
    metadata = ordinary_file(path)
    if metadata is None:
        return {"exists": False, "size": None, "mtime_ns": None,
                "truncated": False, "text": ""}
    count = min(metadata.st_size, limit)
    try:
        with path.open("rb") as stream:
            if count:
                stream.seek(-count, os.SEEK_END)
            raw = stream.read(count)
    except OSError as exc:
        return {"exists": True, "size": metadata.st_size,
                "mtime_ns": metadata.st_mtime_ns, "truncated": False,
                "text": "", "error": str(exc)}
    return {"exists": True, "size": metadata.st_size,
            "mtime_ns": metadata.st_mtime_ns,
            "truncated": metadata.st_size > count,
            "text": raw.decode("utf-8", errors="replace")}

def json_file(path, limit=MAX_JSON):
    metadata = ordinary_file(path)
    if metadata is None:
        return {"exists": False, "value": None}
    if metadata.st_size > limit:
        return {"exists": True, "value": None, "error": "size limit"}
    try:
        raw = path.read_bytes()
        current = path.lstat()
        if ((metadata.st_dev, metadata.st_ino, metadata.st_size,
             metadata.st_mtime_ns) !=
            (current.st_dev, current.st_ino, current.st_size,
             current.st_mtime_ns)):
            raise RuntimeError("file changed while read")
        value = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError, RuntimeError) as exc:
        return {"exists": True, "value": None, "error": str(exc)}
    return {"exists": True, "value": value}

def project(wrapper, keys):
    value = wrapper.get("value")
    if isinstance(value, dict):
        wrapper = dict(wrapper)
        wrapper["value"] = {key: value.get(key) for key in keys}
    return wrapper

def project_run_identity(wrapper):
    value = wrapper.get("value")
    if not isinstance(value, dict):
        return wrapper
    config = value.get("config")
    resolved = config.get("resolved") if isinstance(config, dict) else None
    projected_resolved = {}
    if isinstance(resolved, dict):
        for key in ("curriculum", "data", "lora", "model", "run", "trainer"):
            projected_resolved[key] = resolved.get(key)
    deployment = value.get("deployment")
    inputs = value.get("inputs")
    job = value.get("job")
    projected = {
        "config": {
            "sha256": config.get("sha256") if isinstance(config, dict) else None,
            "resolved": projected_resolved,
        },
        "deployment": {
            "source_sync": deployment.get("source_sync")
            if isinstance(deployment, dict) else None,
        },
        "inputs": {
            "schedule_preflight": inputs.get("schedule_preflight")
            if isinstance(inputs, dict) else None,
            "tokenized_splits": inputs.get("tokenized_splits")
            if isinstance(inputs, dict) else None,
        },
        "job": {
            "submission": job.get("submission") if isinstance(job, dict) else None,
        },
        "model": value.get("model"),
        "prompt_version": value.get("prompt_version"),
    }
    wrapper = dict(wrapper)
    wrapper["value"] = projected
    return wrapper

def clip(value, limit):
    if not isinstance(value, str):
        return ""
    value = "".join(ch for ch in value if ch in "\n\t" or ord(ch) >= 32)
    return value if len(value) <= limit else value[:limit - 1] + "…"

def samples(run_identity):
    try:
        relative = run_identity["config"]["resolved"]["data"]["train_path"]
    except (KeyError, TypeError):
        return []
    if not isinstance(relative, str) or TRAIN_PATH_RE.fullmatch(relative) is None:
        return []
    path = ROOT / relative
    if ordinary_file(path) is None:
        return []
    found = []
    sessions = set()
    consumed = 0
    try:
        with path.open("rb") as stream:
            while len(found) < MAX_SAMPLES and consumed < MAX_SAMPLE_SCAN:
                raw = stream.readline(MAX_SAMPLE_LINE + 1)
                if not raw:
                    break
                consumed += len(raw)
                if len(raw) > MAX_SAMPLE_LINE:
                    break
                row = json.loads(raw.decode("utf-8"))
                metadata = row.get("metadata")
                session = row.get("session")
                if (not isinstance(metadata, dict) or
                    metadata.get("trajectory") != "catalog-predecessor-prefix-v1" or
                    not isinstance(session, str) or session in sessions):
                    continue
                sessions.add(session)
                completion = row.get("completion")
                if isinstance(completion, str) and completion.endswith("</tactic>"):
                    completion = completion[:-9]
                state_value = row.get("state")
                state_preview = []
                if isinstance(state_value, list):
                    state_preview = [clip(item, 700) for item in state_value[:3]
                                     if isinstance(item, str)]
                capabilities = row.get("capabilities")
                allowed = (capabilities.get("allowed_theorems")
                           if isinstance(capabilities, dict) else None)
                library = ([clip(item, 120) for item in allowed[-12:]
                            if isinstance(item, str)]
                           if isinstance(allowed, list) else [])
                found.append({
                    "example_id": session + ":" + str(row.get("step", "")),
                    "theorem": clip(row.get("theorem"), 160),
                    "formula": clip(row.get("formula"), 700),
                    "family": clip(row.get("family"), 200),
                    "state": state_preview,
                    "next_tactic": clip(completion, 300),
                    "library": library,
                    "kind": "selected-catalog-example",
                })
    except (OSError, UnicodeError, ValueError, TypeError):
        return []
    return found

if len(sys.argv) != 2 or JOB_RE.fullmatch(sys.argv[1]) is None:
    raise SystemExit("one decimal job id is required")
job = sys.argv[1]
output = ROOT / "results/peano-policy/qwen3-1.7b-lora-v3-library"
run_identity = json_file(output / "run-identity.json")
manifest = json_file(output / "training-manifest.json")
prepare = None
if isinstance(run_identity.get("value"), dict):
    try:
        candidate = run_identity["value"]["job"]["submission"]["dependency_job_id"]
    except (KeyError, TypeError):
        candidate = None
    if isinstance(candidate, str) and JOB_RE.fullmatch(candidate):
        prepare = json_file(ROOT / "logs" /
            ("peano-wmi-v3-prepare-runtime-" + candidate + ".json"), 1048576)

recovery = []
recovery_root = output / "recovery-snapshots"
try:
    entries = sorted(recovery_root.iterdir(), key=lambda item: item.name)
except OSError:
    entries = []
for entry in entries:
    match = SNAPSHOT_RE.fullmatch(entry.name)
    if match is None or match.group(2) != job:
        continue
    value = json_file(entry / "recovery-manifest.json", MAX_RECOVERY_MANIFEST)
    value = project(value, ["global_step", "training_complete",
                            "eligible_as_training_result", "resumable"])
    recovery.append({"name": entry.name, "declared_step": int(match.group(1)),
                     "manifest": value})
    if len(recovery) >= 32:
        break

sample_rows = samples(run_identity.get("value"))
run_identity = project_run_identity(run_identity)
manifest = project(manifest, ["adapter", "metrics", "training_evidence"])
if prepare is not None:
    prepare = project(prepare, ["format", "status", "trainer_integration"])

payload = {
    "schema": "peano-policy-training-remote-snapshot",
    "v": 1,
    "captured_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    "job_id": job,
    "scheduler": {
        "squeue": command(["squeue", "-h", "-j", job, "-o",
            "%i|%P|%j|%T|%R|%b|%M|%l|%S"]),
        "sacct": command(["sacct", "-n", "-X", "-j", job,
            "--format=JobIDRaw,JobName,Partition,State,ExitCode,DerivedExitCode,ElapsedRaw,Start,End,AllocTRES", "-P"]),
        "sstat": command(["sstat", "-n", "-j", job + ".batch",
            "--format=JobID,AveCPU,AveRSS,MaxRSS,AveDiskRead,AveDiskWrite,TRESUsageInAve,TRESUsageInMax", "-P"]),
    },
    "files": {
        "stdout": tail(ROOT / "logs" / ("peano-wmi-qwen17-v3-" + job + ".out"), MAX_STDOUT_TAIL),
        "stderr": tail(ROOT / "logs" / ("peano-wmi-qwen17-v3-" + job + ".err"), MAX_STDERR_TAIL),
        "run_identity": run_identity,
        "training_manifest": manifest,
        "preparation_runtime_smoke": prepare,
    },
    "recovery": recovery,
    "samples": sample_rows,
}
print(json.dumps(payload, ensure_ascii=False, allow_nan=False,
                 sort_keys=True, separators=(",", ":")))
'''


def validate_job_id(value: str) -> str:
    """Return one safe decimal Slurm allocation id."""

    if type(value) is not str or _JOB_ID_RE.fullmatch(value) is None:
        raise ValueError("job id must be non-empty decimal text")
    return value


def validate_ssh_target(value: str) -> str:
    """Accept the same deliberately narrow host spelling as WMI controls."""

    if (
        type(value) is not str
        or value.startswith("-")
        or _SSH_TARGET_RE.fullmatch(value) is None
    ):
        raise ValueError("SSH target must be a host or user@host name")
    return value


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_remote_snapshot(
    job_id: str = DEFAULT_JOB_ID,
    *,
    ssh_target: str = DEFAULT_SSH_TARGET,
    timeout_seconds: int = SSH_TIMEOUT_SECONDS,
    runner: Callable[..., subprocess.CompletedProcess[bytes]] = subprocess.run,
) -> dict[str, object]:
    """Fetch one bounded snapshot through a fixed, read-only SSH program."""

    job_id = validate_job_id(job_id)
    ssh_target = validate_ssh_target(ssh_target)
    if type(timeout_seconds) is not int or not 1 <= timeout_seconds <= 60:
        raise ValueError("dashboard SSH timeout must be an integer from 1 to 60")
    command = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "ConnectTimeout=10",
        "-o",
        "ServerAliveInterval=10",
        "-o",
        "ServerAliveCountMax=1",
        ssh_target,
        "python3",
        "-",
        job_id,
    ]
    started = time.monotonic()
    try:
        result = runner(
            command,
            input=REMOTE_SNAPSHOT_SOURCE.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise DashboardError("WMI snapshot request timed out") from exc
    except OSError as exc:
        raise DashboardError(f"cannot start SSH snapshot request: {exc}") from exc
    latency_ms = round((time.monotonic() - started) * 1000)
    stdout = bytes(result.stdout or b"")
    stderr = bytes(result.stderr or b"")
    if len(stdout) > MAX_REMOTE_RESPONSE_BYTES:
        raise DashboardError("WMI snapshot exceeded its response byte limit")
    if result.returncode != 0:
        detail = _clean_text(stderr.decode("utf-8", errors="replace"), 2_000)
        raise DashboardError(
            f"WMI snapshot command failed with exit {result.returncode}: {detail}"
        )
    try:
        value = json.loads(stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise DashboardError(f"WMI snapshot was not strict JSON: {exc}") from exc
    if (
        type(value) is not dict
        or value.get("schema") != REMOTE_SNAPSHOT_SCHEMA
        or value.get("v") != REMOTE_SNAPSHOT_VERSION
        or value.get("job_id") != job_id
    ):
        raise DashboardError("WMI snapshot identity does not match the request")
    value["_connection"] = {
        "status": "connected",
        "target": ssh_target,
        "latency_ms": latency_ms,
        "error": None,
    }
    return value


def _clean_text(value: object, limit: int = MAX_LOG_DISPLAY_CHARS) -> str:
    if type(value) is not str:
        return ""
    value = value.replace("\r", "\n")
    value = "".join(
        character
        for character in value
        if character in "\n\t" or ord(character) >= 32
    )
    return value if len(value) <= limit else "…" + value[-(limit - 1) :]


def _strict_number(value: object) -> float | None:
    if type(value) not in (int, float):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _duration_seconds(value: str) -> int | None:
    """Parse tqdm/Slurm durations without accepting free-form text."""

    if not value:
        return None
    days = 0
    if "-" in value:
        day_text, value = value.split("-", 1)
        if not day_text.isdecimal():
            return None
        days = int(day_text)
    parts = value.split(":")
    if not 1 <= len(parts) <= 3 or any(not part.isdecimal() for part in parts):
        return None
    numbers = [int(part) for part in parts]
    if len(numbers) == 3:
        hours, minutes, seconds = numbers
    elif len(numbers) == 2:
        hours, (minutes, seconds) = 0, numbers
    else:
        hours, minutes, seconds = 0, 0, numbers[0]
    if minutes >= 60 or seconds >= 60:
        return None
    return days * 86_400 + hours * 3_600 + minutes * 60 + seconds


def parse_tqdm_progress(text: str, *, expected_total: int) -> dict[str, object] | None:
    """Return the last well-formed training bar for the audited schedule."""

    if type(expected_total) is not int or expected_total < 1:
        raise ValueError("expected progress total must be positive")
    latest: dict[str, object] | None = None
    for match in _TQDM_RE.finditer(_clean_text(text, 1_000_000)):
        step = int(match.group("step"))
        total = int(match.group("total"))
        if total != expected_total or step > total:
            continue
        body = match.group("body")
        before_rate, _, _ = body.rpartition(",")
        timing = before_rate or body
        if "<" in timing:
            elapsed_text, eta_text = timing.split("<", 1)
            eta = _duration_seconds(eta_text.strip())
        else:
            elapsed_text = timing
            eta = None
        elapsed = _duration_seconds(elapsed_text.strip())
        rates = list(_RATE_RE.finditer(body))
        seconds_per_step: float | None = None
        if rates:
            rate = float(rates[-1].group("value"))
            if rate > 0:
                seconds_per_step = (
                    rate if rates[-1].group("unit") == "s/it" else 1.0 / rate
                )
        if seconds_per_step is None and elapsed is not None and step:
            seconds_per_step = elapsed / step
        if eta is None and seconds_per_step is not None:
            eta = round((total - step) * seconds_per_step)
        latest = {
            "step": step,
            "total_steps": total,
            "percent": round(step * 100.0 / total, 3),
            "seconds_per_step": (
                None if seconds_per_step is None else round(seconds_per_step, 3)
            ),
            "eta_seconds": eta,
            "training_elapsed_seconds": elapsed,
            "source": "stderr-tqdm",
        }
    return latest


def _decode_log_mapping(line: str) -> dict[str, object] | None:
    if not 2 <= len(line) <= 8_192 or not line.startswith("{") or not line.endswith("}"):
        return None
    try:
        value = json.loads(line)
    except (json.JSONDecodeError, RecursionError):
        try:
            value = ast.literal_eval(line)
        except (SyntaxError, ValueError, RecursionError):
            return None
    return value if type(value) is dict else None


def parse_loss_points(
    stdout: str,
    *,
    logging_steps: int,
    total_steps: int,
) -> list[dict[str, object]]:
    """Parse bounded Transformers ``PrinterCallback`` loss dictionaries.

    The callback's printed dictionary omits ``step``.  Model-v3 is a fresh,
    one-shot schedule and the preflight requires exact divisibility by
    ``logging_steps``, so the record ordinal determines the step.  Records are
    accepted only when their epoch agrees with that schedule.
    """

    if type(logging_steps) is not int or logging_steps < 1:
        raise ValueError("logging_steps must be positive")
    if type(total_steps) is not int or total_steps < 1:
        raise ValueError("total_steps must be positive")
    points: list[dict[str, object]] = []
    for raw_line in _clean_text(stdout, 1_000_000).splitlines():
        record = _decode_log_mapping(raw_line.strip())
        if record is None or "loss" not in record:
            continue
        loss = _strict_number(record.get("loss"))
        epoch = _strict_number(record.get("epoch"))
        learning_rate = _strict_number(record.get("learning_rate"))
        grad_norm = _strict_number(record.get("grad_norm"))
        step = logging_steps * (len(points) + 1)
        if loss is None or epoch is None or step > total_steps:
            continue
        # Trainer epochs may be rounded in display output.  This rejects setup
        # JSON or unrelated dictionaries without requiring exact float text.
        expected_epoch = step / total_steps
        if abs(epoch - expected_epoch) > 0.015:
            continue
        points.append(
            {
                "step": step,
                "loss": loss,
                "learning_rate": learning_rate,
                "grad_norm": grad_norm,
                "epoch": epoch,
                "source": "stdout-transformers-log",
            }
        )
        if len(points) >= MAX_LOSS_POINTS:
            break
    return points


def _pipe_rows(value: object) -> list[list[str]]:
    if type(value) is not dict or value.get("returncode") != 0:
        return []
    stdout = value.get("stdout")
    if type(stdout) is not str:
        return []
    return [line.split("|") for line in stdout.splitlines() if line.strip()]


def _slurm_state(value: str) -> str | None:
    match = re.match(r"([A-Z_]+)", value)
    return match.group(1) if match is not None else None


def _hardware_from_tres(value: str | None) -> str | None:
    if type(value) is not str:
        return None
    match = _GPU_TRES_RE.search(value)
    if match is None:
        return None
    labels = {"nvidia_a100": "NVIDIA A100"}
    kind = match.group("kind")
    return f"{int(match.group('count'))} × {labels.get(kind, kind)}"


def _scheduler(snapshot: Mapping[str, object]) -> dict[str, object]:
    scheduler = snapshot.get("scheduler")
    if type(scheduler) is not dict:
        scheduler = {}
    queue_rows = _pipe_rows(scheduler.get("squeue"))
    accounting_rows = _pipe_rows(scheduler.get("sacct"))
    queue = queue_rows[0] if len(queue_rows) == 1 and len(queue_rows[0]) == 9 else None
    accounting = (
        accounting_rows[0]
        if len(accounting_rows) == 1 and len(accounting_rows[0]) == 10
        else None
    )
    state = None
    if queue is not None:
        state = _slurm_state(queue[3])
    elif accounting is not None:
        state = _slurm_state(accounting[3])
    allocated_tres = accounting[9] if accounting is not None else None
    return {
        "id": snapshot.get("job_id"),
        "name": queue[2] if queue is not None else (accounting[1] if accounting else None),
        "state": state or "UNKNOWN",
        "partition": queue[1] if queue is not None else (accounting[2] if accounting else None),
        "node_or_reason": queue[4] if queue is not None else None,
        "gpu": queue[5] if queue is not None else None,
        "elapsed": queue[6] if queue is not None else None,
        "time_limit": queue[7] if queue is not None else None,
        "start_at": queue[8] if queue is not None else (accounting[7] if accounting else None),
        "end_at": accounting[8] if accounting is not None else None,
        "elapsed_seconds": (
            int(accounting[6])
            if accounting is not None and accounting[6].isdecimal()
            else None
        ),
        "exit_code": accounting[4] if accounting is not None else None,
        "derived_exit_code": accounting[5] if accounting is not None else None,
        "allocated_tres": allocated_tres,
        "hardware": _hardware_from_tres(allocated_tres),
    }


def _file_value(files: object, name: str) -> object:
    if type(files) is not dict:
        return None
    record = files.get(name)
    return record.get("value") if type(record) is dict else None


def _file_text(files: object, name: str) -> str:
    if type(files) is not dict:
        return ""
    record = files.get(name)
    return _clean_text(record.get("text") if type(record) is dict else "")


def _manifest_loss_points(manifest: object) -> list[dict[str, object]]:
    if type(manifest) is not dict:
        return []
    evidence = manifest.get("training_evidence")
    logging = evidence.get("logging") if type(evidence) is dict else None
    records = logging.get("records") if type(logging) is dict else None
    if type(records) is not list:
        return []
    points: list[dict[str, object]] = []
    for record in records:
        if type(record) is not dict or "loss" not in record:
            continue
        step = record.get("step")
        loss = _strict_number(record.get("loss"))
        if type(step) is not int or step < 1 or loss is None:
            continue
        points.append(
            {
                "step": step,
                "loss": loss,
                "learning_rate": _strict_number(record.get("learning_rate")),
                "grad_norm": _strict_number(record.get("grad_norm")),
                "epoch": _strict_number(record.get("epoch")),
                "source": "completed-training-evidence",
            }
        )
    return points[:MAX_LOSS_POINTS]


def _smoke_loss(smoke: object) -> dict[str, object] | None:
    if type(smoke) is not dict or smoke.get("status") != "passed":
        return None
    integration = smoke.get("trainer_integration")
    if type(integration) is not dict:
        return None
    training = _strict_number(integration.get("training_loss"))
    evaluation = _strict_number(integration.get("evaluation_loss"))
    step = integration.get("train_global_step")
    if training is None or evaluation is None or type(step) is not int:
        return None
    return {
        "status": "passed",
        "training_loss": training,
        "evaluation_loss": evaluation,
        "optimizer_steps": step,
        "meaning": "preparation-runtime smoke; not production loss",
    }


def _snapshots(snapshot: Mapping[str, object], schedule: object) -> dict[str, object]:
    recovery_plan = schedule.get("adapter_recovery") if type(schedule) is dict else None
    planned = (
        recovery_plan.get("planned_optimizer_steps")
        if type(recovery_plan) is dict
        else []
    )
    if type(planned) is not list or any(type(step) is not int for step in planned):
        planned = []
    published: list[dict[str, object]] = []
    records = snapshot.get("recovery")
    if type(records) is list:
        for item in records:
            if type(item) is not dict:
                continue
            declared = item.get("declared_step")
            wrapper = item.get("manifest")
            manifest = wrapper.get("value") if type(wrapper) is dict else None
            if (
                type(declared) is int
                and type(manifest) is dict
                and manifest.get("global_step") == declared
                and manifest.get("training_complete") is False
                and manifest.get("eligible_as_training_result") is False
            ):
                published.append(
                    {
                        "step": declared,
                        "name": item.get("name"),
                        "status": "published-partial-recovery",
                        "resumable": manifest.get("resumable") is True,
                    }
                )
    published.sort(key=lambda item: int(item["step"]))
    return {
        "planned_steps": planned,
        "published": published,
        "latest_step": published[-1]["step"] if published else None,
    }


def _resources(snapshot: Mapping[str, object]) -> dict[str, object]:
    scheduler = snapshot.get("scheduler")
    rows = _pipe_rows(scheduler.get("sstat") if type(scheduler) is dict else None)
    if len(rows) != 1 or len(rows[0]) != 8:
        return {"status": "unavailable"}
    row = rows[0]
    average_values: dict[str, str] = {}
    maximum_values: dict[str, str] = {}
    for field, destination in (
        (row[6], average_values),
        (row[7], maximum_values),
    ):
        for part in field.split(","):
            key, separator, value = part.partition("=")
            if separator:
                destination[key] = value
    return {
        "status": "available",
        "average_cpu": row[1] or None,
        "average_rss": row[2] or None,
        "max_rss": row[3] or None,
        "disk_read_bytes": int(row[4]) if row[4].isdecimal() else None,
        "disk_write_bytes": int(row[5]) if row[5].isdecimal() else None,
        "gpu_memory": average_values.get("gres/gpumem"),
        "max_gpu_memory": maximum_values.get("gres/gpumem"),
        "gpu_utilization_percent": (
            int(average_values["gres/gpuutil"])
            if average_values.get("gres/gpuutil", "").isdecimal()
            else None
        ),
        "max_gpu_utilization_percent": (
            int(maximum_values["gres/gpuutil"])
            if maximum_values.get("gres/gpuutil", "").isdecimal()
            else None
        ),
    }


def _samples(snapshot: Mapping[str, object]) -> list[dict[str, object]]:
    """Apply a second bounded projection to remote proof-data previews."""

    raw_samples = snapshot.get("samples")
    if type(raw_samples) is not list:
        return []
    result: list[dict[str, object]] = []
    for value in raw_samples[:8]:
        if type(value) is not dict:
            continue
        states = value.get("state")
        clean_states = (
            [_clean_text(item, 700) for item in states[:3] if type(item) is str]
            if type(states) is list
            else []
        )
        library = value.get("library")
        clean_library = (
            [_clean_text(item, 120) for item in library[-12:] if type(item) is str]
            if type(library) is list
            else []
        )
        result.append(
            {
                "example_id": _clean_text(value.get("example_id"), 220),
                "theorem": _clean_text(value.get("theorem"), 160),
                "formula": _clean_text(value.get("formula"), 700),
                "family": _clean_text(value.get("family"), 200),
                "state": clean_states,
                "next_tactic": _clean_text(value.get("next_tactic"), 300),
                "library": clean_library,
                "kind": "selected-catalog-example",
            }
        )
    return result


def _phase(
    state: str,
    *,
    progress: Mapping[str, object] | None,
    run_identity: object,
    manifest: object,
) -> str:
    if state in _TERMINAL_FAILURE_STATES:
        return "failed"
    if state == "PENDING":
        return "queued"
    if state == "SUSPENDED":
        return "suspended"
    if state == "COMPLETED":
        return "completed" if type(manifest) is dict else "incomplete"
    if state == "COMPLETING":
        return "finalizing"
    if state == "RUNNING" and progress is not None:
        if progress.get("step") == progress.get("total_steps"):
            return "evaluating-and-admitting"
        return "training"
    if state == "RUNNING" and type(run_identity) is dict:
        return "initializing-model-and-data"
    return "scheduler-startup" if state in _LIVE_STATES else "unknown"


def build_dashboard_status(snapshot: Mapping[str, object]) -> dict[str, object]:
    """Normalize one remote payload into the stable browser API schema."""

    if (
        not isinstance(snapshot, Mapping)
        or snapshot.get("schema") != REMOTE_SNAPSHOT_SCHEMA
        or snapshot.get("v") != REMOTE_SNAPSHOT_VERSION
    ):
        raise DashboardError("cannot build status from an incompatible snapshot")
    job = _scheduler(snapshot)
    files = snapshot.get("files")
    run_identity = _file_value(files, "run_identity")
    if type(run_identity) is dict:
        submission = run_identity.get("job", {}).get("submission", {})
        bound_job_id = submission.get("job_id") if type(submission) is dict else None
        if bound_job_id != snapshot.get("job_id"):
            raise DashboardError(
                "run identity job does not match the requested Slurm allocation"
            )
    manifest = _file_value(files, "training_manifest")
    smoke = _file_value(files, "preparation_runtime_smoke")
    schedule = (
        run_identity.get("inputs", {}).get("schedule_preflight")
        if type(run_identity) is dict
        else None
    )
    if type(schedule) is not dict:
        schedule = {}
    else:
        schedule = dict(schedule)
    tokenized_splits = (
        run_identity.get("inputs", {}).get("tokenized_splits")
        if type(run_identity) is dict
        else None
    )
    if type(tokenized_splits) is dict:
        for role in ("train", "eval"):
            split = tokenized_splits.get(role)
            sequence = split.get("sequence") if type(split) is dict else None
            if type(sequence) is dict:
                total = sequence.get("total")
                maximum = sequence.get("maximum")
                if type(total) is int and total >= 0:
                    schedule[f"{role}_tokens"] = total
                if type(maximum) is int and maximum >= 0:
                    schedule[f"{role}_maximum_sequence_tokens"] = maximum
    total_steps = schedule.get("expected_optimizer_steps")
    if type(total_steps) is not int or total_steps < 1:
        total_steps = 649
    stderr = _file_text(files, "stderr")
    stdout = _file_text(files, "stdout")
    progress = parse_tqdm_progress(stderr, expected_total=total_steps)
    snapshots = _snapshots(snapshot, schedule)
    if progress is None and type(snapshots["latest_step"]) is int:
        step = snapshots["latest_step"]
        progress = {
            "step": step,
            "total_steps": total_steps,
            "percent": round(step * 100.0 / total_steps, 3),
            "seconds_per_step": None,
            "eta_seconds": None,
            "training_elapsed_seconds": None,
            "source": "recovery-manifest-lower-bound",
        }
    logging_steps = None
    if type(run_identity) is dict:
        logging_steps = (
            run_identity.get("config", {})
            .get("resolved", {})
            .get("trainer", {})
            .get("logging_steps")
        )
    if type(logging_steps) is not int or logging_steps < 1:
        logging_steps = 11
    points = _manifest_loss_points(manifest)
    if points:
        loss_status = "completed-evidence"
    else:
        points = parse_loss_points(
            stdout, logging_steps=logging_steps, total_steps=total_steps
        )
        loss_status = "live" if points else (
            "buffered" if progress is not None and progress.get("step", 0) else "pending"
        )

    source_sync = (
        run_identity.get("deployment", {}).get("source_sync", {})
        if type(run_identity) is dict
        else {}
    )
    model_record = run_identity.get("model", {}) if type(run_identity) is dict else {}
    resolved_config = (
        run_identity.get("config", {}).get("resolved", {})
        if type(run_identity) is dict
        else {}
    )
    connection = snapshot.get("_connection")
    if type(connection) is not dict:
        connection = {
            "status": "recorded",
            "target": None,
            "latency_ms": None,
            "error": None,
        }
    current_progress = progress or {
        "step": 0,
        "total_steps": total_steps,
        "percent": 0.0,
        "seconds_per_step": None,
        "eta_seconds": None,
        "training_elapsed_seconds": None,
        "source": None,
    }
    current_progress = dict(current_progress)
    current_progress["phase"] = _phase(
        str(job["state"]),
        progress=progress,
        run_identity=run_identity,
        manifest=manifest,
    )
    # Keep the requested high-value fields first when rendered as insertion-
    # ordered JSON; supplemental evidence remains available to the UI.
    progress_record = {
        "phase": current_progress["phase"],
        "step": current_progress["step"],
        "total_steps": current_progress["total_steps"],
        "percent": current_progress["percent"],
        "seconds_per_step": current_progress["seconds_per_step"],
        "eta_seconds": current_progress["eta_seconds"],
        "training_elapsed_seconds": current_progress.get("training_elapsed_seconds"),
        "source": current_progress.get("source"),
    }
    return {
        "schema": DASHBOARD_SCHEMA,
        "v": DASHBOARD_VERSION,
        "fetched_at": _utc_now(),
        "connection": dict(connection),
        "job": job,
        "progress": progress_record,
        "loss": {
            "status": loss_status,
            "smoke": _smoke_loss(smoke),
            "points": points,
        },
        "schedule": schedule,
        "model": {
            "id": model_record.get("id") if type(model_record) is dict else None,
            "revision": (
                model_record.get("revision") if type(model_record) is dict else None
            ),
            "dtype": (
                resolved_config.get("model", {}).get("dtype")
                if type(resolved_config) is dict
                else None
            ),
            "lora": (
                resolved_config.get("lora")
                if type(resolved_config) is dict
                else None
            ),
        },
        "source": {
            "commit": (
                source_sync.get("git_commit") if type(source_sync) is dict else None
            ),
            "synced_at": (
                source_sync.get("synced_at") if type(source_sync) is dict else None
            ),
            "config_sha256": (
                run_identity.get("config", {}).get("sha256")
                if type(run_identity) is dict
                else None
            ),
            "preparation_job_id": (
                run_identity.get("job", {})
                .get("submission", {})
                .get("dependency_job_id")
                if type(run_identity) is dict
                else None
            ),
        },
        "snapshots": snapshots,
        "samples": _samples(snapshot),
        "logs": {"stdout": stdout, "stderr": stderr},
        "resources": _resources(snapshot),
        "artifacts": {
            "run_identity": type(run_identity) is dict,
            "training_manifest": type(manifest) is dict,
            "final_adapter": (
                type(manifest) is dict and type(manifest.get("adapter")) is dict
            ),
        },
    }


def fetch_dashboard_status(
    job_id: str = DEFAULT_JOB_ID,
    *,
    ssh_target: str = DEFAULT_SSH_TARGET,
    timeout_seconds: int = SSH_TIMEOUT_SECONDS,
) -> dict[str, object]:
    """Fetch and normalize one live dashboard status record."""

    return build_dashboard_status(
        fetch_remote_snapshot(
            job_id,
            ssh_target=ssh_target,
            timeout_seconds=timeout_seconds,
        )
    )


def disconnected_status(
    job_id: str,
    *,
    ssh_target: str,
    error: Exception,
) -> dict[str, object]:
    """Return a schema-compatible connection failure for a resilient UI."""

    validate_job_id(job_id)
    validate_ssh_target(ssh_target)
    return {
        "schema": DASHBOARD_SCHEMA,
        "v": DASHBOARD_VERSION,
        "fetched_at": _utc_now(),
        "connection": {
            "status": "error",
            "target": ssh_target,
            "latency_ms": None,
            "error": _clean_text(str(error), 2_000),
        },
        "job": {"id": job_id, "state": "UNKNOWN"},
        "progress": {
            "phase": "unreachable",
            "step": None,
            "total_steps": None,
            "percent": None,
            "seconds_per_step": None,
            "eta_seconds": None,
        },
        "loss": {"status": "unavailable", "smoke": None, "points": []},
        "schedule": {},
        "model": {},
        "source": {},
        "snapshots": {"planned_steps": [], "published": [], "latest_step": None},
        "samples": [],
        "logs": {"stdout": "", "stderr": ""},
        "resources": {"status": "unavailable"},
        "artifacts": {
            "run_identity": False,
            "training_manifest": False,
            "final_adapter": False,
        },
    }


__all__ = [
    "DASHBOARD_SCHEMA",
    "DASHBOARD_VERSION",
    "DEFAULT_JOB_ID",
    "DEFAULT_SSH_TARGET",
    "DashboardError",
    "REMOTE_SNAPSHOT_SOURCE",
    "build_dashboard_status",
    "disconnected_status",
    "fetch_dashboard_status",
    "fetch_remote_snapshot",
    "parse_loss_points",
    "parse_tqdm_progress",
    "validate_job_id",
    "validate_ssh_target",
]
