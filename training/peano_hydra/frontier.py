"""Resource-bounded, model-free development evaluation and independent replay.

Each search runs in a fresh sequential process. A killed, malformed, oversized,
or unverified worker never contributes a proof. This is public DEV evidence,
not a sealed test, model comparison, negative decision, or H2/H5 acceptance.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import re
import resource
import stat
import subprocess
import sys
import tempfile
import threading
import time


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts" / "eval_peano_hydra_development.py"
SCHEMA = "peano-hydra-symbolic-development-evaluation-v1"
WORKER_SCHEMA = "peano-hydra-symbolic-development-worker-v1"
MAX_JSON_BYTES = 24 * 1024 * 1024
MAX_ROW_BYTES = 1024 * 1024
MAX_GOALS = 128
LANES = ("closure", "portfolio")
SOURCE_FILES = (
    "training/peano_hydra/protocol.py",
    "training/peano_hydra/benchmark.py",
    "training/peano_hydra/symbolic.py",
    "training/peano_hydra/frontier.py",
    "training/peano_hydra/policy.py",
    "training/peano_hydra/runner.py",
    "training/peano_hydra/epoch.py",
    "training/peano_hydra/curriculum.py",
    "training/peano_hydra/evaluation.py",
    "training/peano_hydra/posttrain.py",
    "training/peano_policy/search.py",
    "scripts/eval_peano_hydra_development.py",
)


class DevelopmentEvaluationError(ValueError):
    """The declared development experiment could not retain valid evidence."""


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DevelopmentEvaluationError(f"duplicate JSON field {key!r}")
        result[key] = value
    return result


def decode(raw: bytes, *, limit: int = MAX_JSON_BYTES) -> dict[str, object]:
    if len(raw) > limit:
        raise DevelopmentEvaluationError("JSON evidence exceeds its byte reservation")
    def invalid(value: str) -> None:
        raise DevelopmentEvaluationError(f"non-finite JSON value {value}")
    try:
        value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=invalid)
    except (ValueError, UnicodeError, RecursionError) as error:
        raise DevelopmentEvaluationError(f"invalid JSON evidence: {error}") from None
    if type(value) is not dict:
        raise DevelopmentEvaluationError("evidence must be a JSON object")
    return value


def read_bytes(path: Path, *, limit: int = MAX_JSON_BYTES) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(descriptor, "rb") as stream:
        metadata = os.fstat(stream.fileno())
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > limit:
            raise DevelopmentEvaluationError(f"not one bounded regular evidence file: {path}")
        raw = stream.read(limit + 1)
        if len(raw) > limit:
            raise DevelopmentEvaluationError("evidence file grew beyond reservation")
        return raw


def read_record(path: Path, *, limit: int = MAX_JSON_BYTES) -> dict[str, object]:
    return decode(read_bytes(path, limit=limit), limit=limit)


def write_once(path: Path, record: dict[str, object]) -> dict[str, object]:
    raw = canonical(record) + b"\n"
    if len(raw) > MAX_JSON_BYTES:
        raise DevelopmentEvaluationError("publication exceeds its evidence reservation")
    with path.open("xb") as stream:
        stream.write(raw)
        stream.flush()
        os.fsync(stream.fileno())
    return {"path": path.name, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


@dataclass(frozen=True)
class WorkerLimits:
    wall_seconds: int = 5
    cpu_seconds: int = 3
    rss_bytes: int = 1024 * 1024 * 1024
    max_depth: int = 16
    beam_width: int = 4
    candidates_per_state: int = 8
    max_states: int = 128
    max_proposals: int = 128

    def __post_init__(self) -> None:
        ceilings = {"wall_seconds": 30, "cpu_seconds": 25, "rss_bytes": 2 * 1024**3,
                    "max_depth": 16, "beam_width": 8, "candidates_per_state": 8,
                    "max_states": 256, "max_proposals": 256}
        for name, ceiling in ceilings.items():
            value = getattr(self, name)
            if type(value) is not int or not 1 <= value <= ceiling:
                raise DevelopmentEvaluationError(f"invalid bounded worker limit: {name}")
        if self.cpu_seconds > self.wall_seconds or self.rss_bytes < 128 * 1024**2:
            raise DevelopmentEvaluationError("inconsistent worker time or memory limits")

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def _rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def _guard(limits: WorkerLimits) -> None:
    # CPU is an OS-enforced hard stop. Linux additionally enforces address
    # space; macOS has enormous reserved VM, so its RSS guard is sampled.
    resource.setrlimit(resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds + 1))
    if sys.platform.startswith("linux"):
        resource.setrlimit(resource.RLIMIT_AS, (limits.rss_bytes, limits.rss_bytes))
    def watch() -> None:
        while True:
            if _rss_bytes() > limits.rss_bytes:
                os._exit(75)
            time.sleep(0.02)
    threading.Thread(target=watch, name="hydra-development-rss-guard", daemon=True).start()


def source_identity() -> dict[str, object]:
    def git(*arguments: str) -> str:
        return subprocess.run(["git", "-C", str(ROOT), *arguments], check=True,
                              capture_output=True, text=True, timeout=10).stdout.strip()
    files = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
             for name in SOURCE_FILES}
    return {"git_commit": git("rev-parse", "HEAD"),
            "git_dirty": bool(git("status", "--porcelain", "--untracked-files=all")),
            "files": files, "files_sha256": digest(files)}


def _config(lane: str, limits: WorkerLimits):
    from training.peano_hydra.symbolic import SymbolicConfig
    if lane not in LANES:
        raise DevelopmentEvaluationError("unknown symbolic lane")
    return SymbolicConfig(structural=lane == "portfolio", witness=lane == "portfolio",
                          induction=lane == "portfolio",
                          candidates_per_state=limits.candidates_per_state,
                          max_proposals=limits.max_proposals)


def execution_capabilities():
    """Native-only authority: the epoch is metadata, not a theorem import grant."""
    from peano_lab.ui.prove import SurfaceCapabilities
    from training.peano_hydra.symbolic import SYMBOLIC_COMMANDS
    return SurfaceCapabilities(label="hydra-development-no-imports-v1",
                               allowed_commands=SYMBOLIC_COMMANDS,
                               allowed_theorems=frozenset())


def search_limits_record(limits: WorkerLimits) -> dict[str, int]:
    return {"max_depth": limits.max_depth, "beam_width": limits.beam_width,
            "candidates_per_state": limits.candidates_per_state,
            "max_model_calls": limits.max_proposals, "max_states": limits.max_states}


def worker(request: dict[str, object]) -> dict[str, object]:
    """Internal worker: original-goal search/replay only, no model or solver."""
    if set(request) != {"schema", "mode", "goal", "lane", "limits", "profile_sha256",
                        "epoch_sha256", "source_files_sha256", "saved_result", "environment"}:
        raise DevelopmentEvaluationError("worker request fields differ")
    if request["schema"] != WORKER_SCHEMA or request["mode"] not in {"search", "replay", "verify"}:
        raise DevelopmentEvaluationError("unknown worker schema or mode")
    limits = WorkerLimits(**request["limits"])
    _guard(limits)
    start_wall, start_cpu = time.monotonic(), time.process_time()
    from peano_lab.batch import run_proof
    from training.peano_hydra.protocol import development_profile, validate_statement
    from training.peano_hydra.runner import run_hydra, policy_environment
    from training.peano_hydra.symbolic import make_symbolic_policy, verify_symbolic_evidence
    from training.peano_policy.search import SearchLimits
    profile = development_profile()
    if (profile["profile_sha256"] != request["profile_sha256"]
        or type(request["epoch_sha256"]) is not str or not re.fullmatch(r"[a-f0-9]{64}", request["epoch_sha256"])):
        raise DevelopmentEvaluationError("worker profile or epoch identity changed")
    files = {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in SOURCE_FILES}
    if digest(files) != request["source_files_sha256"]:
        raise DevelopmentEvaluationError("worker source changed after freezing")
    goal = request["goal"]
    if type(goal) is not dict or set(goal) != {"id", "source", "canonical"}:
        raise DevelopmentEvaluationError("invalid worker goal identity")
    if validate_statement(goal["source"]) != goal["canonical"]:
        raise DevelopmentEvaluationError("worker original formula differs")
    # Workers cannot import ANY catalog theorem. The controller authenticates
    # the complete epoch for masks; reloading that catalog in every native-only
    # proof worker would spend the search budget on unused import authority.
    capabilities = execution_capabilities()
    if request["environment"] != policy_environment(capabilities):
        raise DevelopmentEvaluationError("worker native execution authority changed")
    config = _config(request["lane"], limits)
    if request["mode"] == "search":
        if request["saved_result"] is not None:
            raise DevelopmentEvaluationError("search cannot receive a supplied proof")
        policy = make_symbolic_policy(capabilities, config=config)
        run = run_hydra(goal["source"], policy, capabilities=capabilities,
                        limits=SearchLimits(max_depth=limits.max_depth, beam_width=limits.beam_width,
                            candidates_per_state=limits.candidates_per_state,
                            max_model_calls=limits.max_proposals, max_states=limits.max_states),
                        label=f"dev-{request['lane']}-{goal['id']}")
        if run.degraded:
            raise DevelopmentEvaluationError("symbolic provider degraded")
        evidence = run.to_dict(include_trace=True)
        checked = run.proved
        status = "proved" if checked else "unknown"
        reason = run.status
        workload = dict(policy.heads[0].policy.workload)
        action_records = list(policy.heads[0].policy.action_records)
    else:
        retained = request["saved_result"]
        if type(retained) is not dict or retained["config"] != config.to_dict():
            raise DevelopmentEvaluationError("saved symbolic lane configuration differs")
        if retained["evidence"]["limits"] != search_limits_record(limits):
            raise DevelopmentEvaluationError("saved search budget differs from the frozen experiment")
        if retained["evidence"]["theorem"] != goal["canonical"]:
            raise DevelopmentEvaluationError("saved search target differs")
        verify_symbolic_evidence(retained["evidence"], retained["action_records"], retained["workload"],
                                 capabilities=capabilities, config=config)
        if request["mode"] == "replay":
            commands, saved = retained["evidence"]["search"]["commands"], retained["evidence"]["replay"]
            if type(commands) is not list or not 1 <= len(commands) <= limits.max_depth or type(saved) is not dict:
                raise DevelopmentEvaluationError("replay needs bounded commands and saved trace")
            if any(type(line) is not str or not line or len(line.encode()) > 4096
                   or line.splitlines() != [line] or ";" in line or "<|>" in line for line in commands):
                raise DevelopmentEvaluationError("replay command escapes its single-action boundary")
            replay = run_proof(goal["source"], tuple(commands), request_id=saved["id"],
                               session_id=saved["session"], capabilities=capabilities,
                               classical=False, on_error="stop", trace_byte_limit=MAX_ROW_BYTES)
            if not replay.kernel_checked or replay.theorem != goal["canonical"] or replay.to_dict(include_trace=True) != saved:
                raise DevelopmentEvaluationError("fresh kernel replay differs from saved proof")
        elif retained["kernel_checked"] or retained["evidence"]["replay"] is not None:
            raise DevelopmentEvaluationError("unknown search cannot carry proof evidence")
        checked = request["mode"] == "replay"
        evidence, status = None, "proved" if checked else "unknown"
        reason = "independently_replayed" if checked else "independently_verified_unknown_search"
        workload = {}
        action_records = []
    if "torch" in sys.modules:
        raise DevelopmentEvaluationError("symbolic evaluation imported a model framework")
    result = {"schema": WORKER_SCHEMA, "goal": goal, "lane": request["lane"],
              "profile_sha256": request["profile_sha256"], "epoch_sha256": request["epoch_sha256"],
              "source_files_sha256": request["source_files_sha256"], "limits": limits.to_dict(),
              "environment": request["environment"],
              "config": config.to_dict(), "status": status, "reason": reason,
              "kernel_checked": checked, "model_calls": 0, "solver_calls": 0,
              "workload": workload, "action_records": action_records, "evidence": evidence,
              "resources": {"worker_wall_seconds": time.monotonic() - start_wall,
                            "worker_cpu_seconds": time.process_time() - start_cpu,
                            "peak_rss_bytes": _rss_bytes(), "cpu_instructions": None,
                            "energy_joules": None}}
    if result["resources"]["peak_rss_bytes"] > limits.rss_bytes:
        raise DevelopmentEvaluationError("worker exceeded RSS reservation")
    if len(canonical(result)) + 4096 > MAX_ROW_BYTES:
        raise DevelopmentEvaluationError("worker evidence exceeds reservation")
    return result


def run_isolated(request: dict[str, object]) -> dict[str, object]:
    """Bound time and output without retaining unbounded pipe buffers."""
    limits = WorkerLimits(**request["limits"])
    began = time.monotonic()
    with tempfile.TemporaryFile() as output, tempfile.TemporaryFile() as errors:
        process = subprocess.Popen([sys.executable, str(SCRIPT), "--worker"], cwd=ROOT,
            stdin=subprocess.PIPE, stdout=output, stderr=errors,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONMALLOC": "malloc"})
        try:
            process.communicate(canonical(request), timeout=limits.wall_seconds)
            reason = "worker_exit"
        except subprocess.TimeoutExpired:
            process.kill()
            process.communicate()
            reason = "wall_limit"
        elapsed = time.monotonic() - began
        output.seek(0)
        raw = output.read(MAX_ROW_BYTES + 1)
        errors.seek(0)
        detail = errors.read(4096).decode("utf-8", errors="replace")
    if process.returncode == 0:
        row = decode(raw, limit=MAX_ROW_BYTES)
        for key in ("goal", "lane", "limits", "profile_sha256", "epoch_sha256", "source_files_sha256", "environment"):
            if row.get(key) != request[key]:
                raise DevelopmentEvaluationError(f"worker changed {key}")
        if row.get("schema") != WORKER_SCHEMA or row.get("status") not in {"proved", "unknown"}:
            raise DevelopmentEvaluationError("worker result schema or status differs")
        if row.get("kernel_checked") is not (row["status"] == "proved"):
            raise DevelopmentEvaluationError("worker claimed inconsistent proof status")
        if row.get("model_calls") != 0 or row.get("solver_calls") != 0:
            raise DevelopmentEvaluationError("symbolic worker claimed external calls")
        resources = row.get("resources", {})
        if any(type(resources.get(key)) not in {int, float} or not math.isfinite(resources[key])
               or resources[key] < 0 for key in ("worker_wall_seconds", "worker_cpu_seconds", "peak_rss_bytes")):
            raise DevelopmentEvaluationError("worker resources are malformed")
        if resources["peak_rss_bytes"] > limits.rss_bytes:
            raise DevelopmentEvaluationError("worker memory reservation differs")
        row["resources"]["parent_wall_seconds"] = elapsed
        return row
    return {"schema": WORKER_SCHEMA, **{key: request[key] for key in
            ("goal", "lane", "limits", "profile_sha256", "epoch_sha256", "source_files_sha256", "environment")},
            "status": "unknown", "kernel_checked": False, "reason": reason,
            "worker_returncode": process.returncode, "diagnostic": detail,
            "model_calls": 0, "solver_calls": 0, "evidence": None,
            "workload": None, "action_records": None, "resources": {"parent_wall_seconds": elapsed,
                "worker_wall_seconds": None, "worker_cpu_seconds": None, "peak_rss_bytes": None,
                "cpu_instructions": None, "energy_joules": None}}


def build_plan(preparations: tuple[Path, ...] = (), *, limits: WorkerLimits = WorkerLimits()) -> dict[str, object]:
    from training.peano_hydra.benchmark import build_development_benchmark, audit_preparation
    from training.peano_hydra.epoch import freeze_epoch
    from training.peano_hydra.protocol import development_profile
    from training.peano_hydra.runner import policy_environment
    epoch = freeze_epoch()
    benchmark = build_development_benchmark(epoch)
    if not 1 <= len(benchmark["goals"]) <= MAX_GOALS:
        raise DevelopmentEvaluationError("benchmark exceeds whole-run goal reservation")
    audits = [{"preparation_directory": str(path),
               "audit": audit_preparation(benchmark, path, epoch=epoch)} for path in preparations]
    record = {"schema": SCHEMA, "status": "planned", "development_only": True,
              "sealed_benchmark": False, "research_claim_eligible": False,
              "model_comparison_performed": False, "profile": development_profile(),
              "benchmark": benchmark, "preparation_audits": audits,
              "source": source_identity(), "limits": limits.to_dict(),
              "environment": policy_environment(execution_capabilities()),
              "lanes": {lane: _config(lane, limits).to_dict() for lane in LANES},
              "reserved_worker_runs": len(benchmark["goals"]) * len(LANES),
              "reserved_worker_wall_seconds": len(benchmark["goals"]) * len(LANES) * limits.wall_seconds,
              "parallel_workers": 1,
              "runtime": {"python": platform.python_version(), "implementation": platform.python_implementation(),
                          "platform": platform.platform(), "machine": platform.machine(),
                          "processor": platform.processor() or None, "logical_cpus": os.cpu_count()},
              "rss_enforcement": "OS address-space limit on Linux; 20ms sampled RSS guard on macOS",
              "negative_result_authority": False}
    record["plan_sha256"] = digest(record)
    return record


def _request(plan: dict[str, object], goal: dict[str, object], lane: str,
             *, saved: dict[str, object] | None = None) -> dict[str, object]:
    return {"schema": WORKER_SCHEMA, "mode": ("replay" if saved["kernel_checked"] else "verify") if saved else "search",
            "goal": {key: goal[key] for key in ("id", "source", "canonical")},
            "lane": lane, "limits": plan["limits"],
            "profile_sha256": plan["profile"]["profile_sha256"],
            "epoch_sha256": plan["benchmark"]["epoch_sha256"],
            "source_files_sha256": plan["source"]["files_sha256"],
            "environment": plan["environment"],
            "saved_result": saved}


def validate_resources(row: dict[str, object], limits: WorkerLimits) -> None:
    resources = row.get("resources")
    if type(resources) is not dict:
        raise DevelopmentEvaluationError("row has no resource record")
    for key in ("parent_wall_seconds", "worker_wall_seconds", "worker_cpu_seconds", "peak_rss_bytes"):
        value = resources.get(key)
        if value is None and row.get("evidence") is None and key != "parent_wall_seconds":
            continue
        if type(value) not in {int, float} or not math.isfinite(value) or value < 0:
            raise DevelopmentEvaluationError("row has invalid measured resources")
    if resources.get("peak_rss_bytes") is not None and resources["peak_rss_bytes"] > limits.rss_bytes:
        raise DevelopmentEvaluationError("row exceeded its memory reservation")
    if resources.get("worker_cpu_seconds") is not None and resources["worker_cpu_seconds"] > limits.cpu_seconds + 1:
        raise DevelopmentEvaluationError("row exceeded its CPU reservation")
    if resources.get("worker_wall_seconds") is not None and resources["worker_wall_seconds"] > limits.wall_seconds:
        raise DevelopmentEvaluationError("row exceeded its wall reservation")
    if resources.get("cpu_instructions") is not None or resources.get("energy_joules") is not None:
        raise DevelopmentEvaluationError("unimplemented resource counters cannot be fabricated")


def validate_reservations(plan: dict[str, object]) -> WorkerLimits:
    from training.peano_hydra.runner import policy_environment
    limits = WorkerLimits(**plan["limits"])
    if (not 1 <= len(plan["benchmark"]["goals"]) <= MAX_GOALS
        or plan["reserved_worker_runs"] != len(plan["benchmark"]["goals"]) * len(LANES)
        or plan["lanes"] != {lane: _config(lane, limits).to_dict() for lane in LANES}
        or plan["environment"] != policy_environment(execution_capabilities())
        or plan["source"]["files_sha256"] != digest(plan["source"]["files"])
        or set(plan["source"]["files"]) != set(SOURCE_FILES)
        or plan["reserved_worker_wall_seconds"] != plan["reserved_worker_runs"] * limits.wall_seconds
        or plan["parallel_workers"] != 1):
        raise DevelopmentEvaluationError("plan changed its whole-run resource reservation")
    return limits


def summarize(plan: dict[str, object], rows: list[dict[str, object]]) -> dict[str, object]:
    if len(rows) != plan["reserved_worker_runs"]:
        raise DevelopmentEvaluationError("incomplete evaluation cannot publish complete metrics")
    expected = {(lane, goal["id"]) for lane in LANES for goal in plan["benchmark"]["goals"]}
    if {(row["lane"], row["goal"]["id"]) for row in rows} != expected:
        raise DevelopmentEvaluationError("evaluation has missing or duplicate goal rows")
    output = {}
    for lane in LANES:
        lane_rows = [row for row in rows if row["lane"] == lane]
        recorded_rss = [row["resources"]["peak_rss_bytes"] for row in lane_rows
                        if row["resources"]["peak_rss_bytes"] is not None]
        recorded_cpu = [row["resources"]["worker_cpu_seconds"] for row in lane_rows
                        if row["resources"]["worker_cpu_seconds"] is not None]
        measured = [row for row in lane_rows if row["evidence"] is not None]
        cohorts = {}
        for cohort in ("expanded", "historical"):
            identifiers = {goal["id"] for goal in plan["benchmark"]["goals"] if goal["cohort"] == cohort}
            selected = [row for row in lane_rows if row["goal"]["id"] in identifiers]
            cohorts[cohort] = {"goals": len(selected),
                "proved": sum(row["kernel_checked"] for row in selected),
                "unknown": sum(not row["kernel_checked"] for row in selected)}
        output[lane] = {"cohorts": cohorts, "model_calls": 0, "solver_calls": 0,
            "worker_failures": sum(row["evidence"] is None for row in lane_rows),
            "parent_wall_seconds": sum(row["resources"]["parent_wall_seconds"] for row in lane_rows),
            "max_recorded_peak_rss_bytes": max(recorded_rss, default=None),
            "recorded_worker_cpu_seconds": sum(recorded_cpu) if recorded_cpu else None,
            "unavailable_worker_resource_rows": len(lane_rows) - len(recorded_cpu),
            "completed_worker_search_counters": {field: sum(row["evidence"]["search"][field]
                for row in measured) for field in ("states_expanded", "candidates_executed", "states_discovered")},
            "proof_nodes": sum(row["evidence"]["replay"]["proof_nodes"]
                for row in lane_rows if row["kernel_checked"]),
            "tactic_decisions": sum(len(row["evidence"]["search"]["commands"])
                for row in lane_rows if row["kernel_checked"]),
            "unsolved_goal_ids": [row["goal"]["id"] for row in lane_rows if not row["kernel_checked"]]}
    return output


def execute_plan(plan: dict[str, object], output: Path, *, progress=None) -> dict[str, object]:
    original = dict(plan)
    expected_hash = original.pop("plan_sha256")
    if digest(original) != expected_hash or plan["source"] != source_identity():
        raise DevelopmentEvaluationError("development plan or source changed before execution")
    limits = validate_reservations(plan)
    if output.exists() or output.is_symlink():
        raise DevelopmentEvaluationError("use a fresh development output directory")
    output.mkdir(parents=True, mode=0o700)
    # The benchmark, configurations, masks, and source are durably frozen
    # before the first outcome. Partial runs have no completed report.
    plan_file = write_once(output / "plan.json", plan)
    started_at = datetime.now(timezone.utc).isoformat()
    rows, files = [], []
    for lane in LANES:
        for goal in plan["benchmark"]["goals"]:
            row = run_isolated(_request(plan, goal, lane))
            validate_resources(row, limits)
            if row["kernel_checked"]:
                evidence = row["evidence"]
                if (not evidence or evidence["replay"]["kernel_checked"] is not True
                    or evidence["theorem"] != goal["canonical"] or evidence["degraded"]):
                    raise DevelopmentEvaluationError("positive lost its original-goal kernel evidence")
            filename = f"row-{len(rows):03d}.json"
            files.append(write_once(output / filename, row))
            rows.append(row)
            if progress is not None:
                progress(len(rows), plan["reserved_worker_runs"], row)
    if plan["source"] != source_identity():
        raise DevelopmentEvaluationError("source changed during the frozen development evaluation")
    report = {"schema": SCHEMA, "status": "completed", "plan": plan_file,
              "started_at": started_at, "finished_at": datetime.now(timezone.utc).isoformat(),
              "plan_sha256": plan["plan_sha256"], "profile_sha256": plan["profile"]["profile_sha256"],
              "benchmark_sha256": plan["benchmark"]["manifest_sha256"],
              "rows": files, "metrics": summarize(plan, rows), "development_only": True,
              "sealed_benchmark": False, "research_claim_eligible": False,
              "model_comparison_performed": False}
    report["report_sha256"] = digest(report)
    write_once(output / "report.json", report)
    return report


def verify_run(directory: Path, *, progress=None) -> dict[str, object]:
    report = read_record(directory / "report.json")
    signed = dict(report)
    if signed.pop("report_sha256", None) != digest(signed):
        raise DevelopmentEvaluationError("completed report digest differs")
    if (report.get("schema") != SCHEMA or report.get("status") != "completed"
        or report.get("development_only") is not True or report.get("sealed_benchmark") is not False
        or report.get("research_claim_eligible") is not False or report.get("model_comparison_performed") is not False):
        raise DevelopmentEvaluationError("archived report changed its development-only claim boundary")
    def checked_file(descriptor: dict[str, object], *, limit: int = MAX_JSON_BYTES) -> dict[str, object]:
        name = descriptor["path"]
        if type(name) is not str or Path(name).name != name:
            raise DevelopmentEvaluationError("evidence path escaped its directory")
        path = directory / name
        raw = read_bytes(path, limit=limit)
        value = decode(raw, limit=limit)
        if len(raw) != descriptor["bytes"] or hashlib.sha256(raw).hexdigest() != descriptor["sha256"]:
            raise DevelopmentEvaluationError("archived evidence bytes differ")
        return value
    plan = checked_file(report["plan"])
    limits = validate_reservations(plan)
    unsigned = dict(plan)
    if unsigned.pop("plan_sha256", None) != digest(unsigned):
        raise DevelopmentEvaluationError("archived plan digest differs")
    if (report["plan_sha256"] != plan["plan_sha256"]
        or report["profile_sha256"] != plan["profile"]["profile_sha256"]
        or report["benchmark_sha256"] != plan["benchmark"]["manifest_sha256"]):
        raise DevelopmentEvaluationError("report changed its frozen plan/profile/benchmark")
    from training.peano_hydra.benchmark import build_development_benchmark
    from training.peano_hydra.epoch import freeze_epoch
    from training.peano_hydra.protocol import development_profile
    if plan["benchmark"] != build_development_benchmark(freeze_epoch()):
        raise DevelopmentEvaluationError("archived benchmark or declared lineage masks changed")
    if plan["profile"] != development_profile() or plan["source"]["files"] != source_identity()["files"]:
        raise DevelopmentEvaluationError("replay requires the original frozen source/profile")
    if (report["plan"]["path"] != "plan.json" or len(report["rows"]) != plan["reserved_worker_runs"]
        or [item["path"] for item in report["rows"]] != [f"row-{i:03d}.json" for i in range(len(report["rows"]))]):
        raise DevelopmentEvaluationError("archived evidence inventory differs")
    rows = [checked_file(descriptor, limit=MAX_ROW_BYTES) for descriptor in report["rows"]]
    expected_goals = {goal["id"]: {key: goal[key] for key in ("id", "source", "canonical")}
                      for goal in plan["benchmark"]["goals"]}
    for row in rows:
        if (row["profile_sha256"] != report["profile_sha256"]
            or row["epoch_sha256"] != plan["benchmark"]["epoch_sha256"]
            or row["source_files_sha256"] != plan["source"]["files_sha256"]
            or row["limits"] != plan["limits"] or row["model_calls"] != 0 or row["solver_calls"] != 0
            or row["environment"] != plan["environment"]
            or row["goal"] != expected_goals.get(row["goal"]["id"])
            or type(row["kernel_checked"]) is not bool
            or row["kernel_checked"] != (row["status"] == "proved")):
            raise DevelopmentEvaluationError("archived row changed its authority or resources")
        validate_resources(row, limits)
        if row["evidence"] is not None and row["config"] != plan["lanes"][row["lane"]]:
            raise DevelopmentEvaluationError("archived symbolic component configuration differs")
        if row["evidence"] is not None and row["evidence"]["limits"] != search_limits_record(limits):
            raise DevelopmentEvaluationError("archived search budget differs from the frozen experiment")
    if summarize(plan, rows) != report["metrics"]:
        raise DevelopmentEvaluationError("archived metrics differ from retained rows")
    goals = {goal["id"]: goal for goal in plan["benchmark"]["goals"]}
    count = 0
    verified_rows = 0
    for row in rows:
        if row["evidence"] is None:
            continue
        result = run_isolated(_request(plan, goals[row["goal"]["id"]], row["lane"], saved=row))
        expected_reason = "independently_replayed" if row["kernel_checked"] else "independently_verified_unknown_search"
        if result["reason"] != expected_reason or result["kernel_checked"] is not row["kernel_checked"]:
            raise DevelopmentEvaluationError("independent original-goal replay failed: " + str(result))
        count += int(row["kernel_checked"])
        verified_rows += 1
        if progress is not None:
            progress(verified_rows, sum(item["evidence"] is not None for item in rows), result)
    return {"status": "passed", "report_sha256": report["report_sha256"],
            "independently_replayed_proofs": count, "model_calls": 0,
            "deterministically_verified_policy_rows": verified_rows,
            "solver_calls": 0, "research_claim_eligible": False}
