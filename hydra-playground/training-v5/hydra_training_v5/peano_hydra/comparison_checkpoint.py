"""Durable, prefix-only execution of the unchanged public comparison.

Training-bound comparison.py stays byte-identical. This wrapper explicitly
adds its execution sources to a fresh ComparisonPlan, not to either training
origin. Checkpoints are integrity-bound receipts, not GPU attestations. An
interrupted in-flight goal is never silently generated again. Only a clean,
authenticated prefix may resume; every saved positive is freshly replayed.
"""

from __future__ import annotations

from dataclasses import replace
import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys
import time
from typing import Callable
import uuid

from hydra_training_v5.peano_hydra import capacity, comparison, evaluation as shared

HEADER_SCHEMA = "peano-hydra-comparison-checkpoint-header-v1"
HEAD_SCHEMA = "peano-hydra-comparison-checkpoint-head-v1"
ROW_SCHEMA = "peano-hydra-comparison-checkpoint-goal-v1"
VERIFY_SCHEMA = "peano-hydra-comparison-checkpoint-verification-v1"
PROGRESS_SCHEMA = "peano-hydra-comparison-progress-v1"
SOURCE_FILES = (
    "training/peano_hydra/comparison_checkpoint.py",
    "training/peano_policy/authority_runtime.py",
)
TOTAL_GOALS = 3 * comparison.GOAL_COUNT
MAX_HEADER_BYTES = 2 * 1024**2
MAX_ROW_BYTES = shared.MAX_GOAL_EVIDENCE_BYTES + 128 * 1024
MAX_CHECKPOINT_BYTES = comparison.MAX_REPORT_BYTES + MAX_HEADER_BYTES
_canonical, _digest = comparison._canonical, comparison._digest
_require, _same, _keys, _integer = comparison._require, comparison._same, comparison._keys, comparison._integer


class CheckpointPaused(comparison.ComparisonError):
    """A clean boundary stopped; no complete report or proof-rate claim exists."""

    def __init__(self, receipt: dict):
        super().__init__("comparison paused at a durable clean goal boundary")
        self.receipt = receipt


class Progress:
    """Small flushed operational events; timings are not benchmark scores."""

    def __init__(self, sink: Callable[[dict], None] | None = None):
        self.sink = sink
        self.started = time.monotonic()
        self.cpu_started = time.process_time()

    def emit(self, phase: str, **fields: object) -> None:
        if self.sink is not None:
            record = {"schema": PROGRESS_SCHEMA, "phase": phase,
                      "elapsed_wall_seconds": round(time.monotonic() - self.started, 6),
                      "elapsed_cpu_seconds": round(time.process_time() - self.cpu_started, 6), **fields}
            _require(len(_canonical(record)) <= 4096, "progress event exceeds its byte bound")
            self.sink(record)


def extend_plan(plan: comparison.ComparisonPlan) -> comparison.ComparisonPlan:
    """Explicit execution-only source admission, never a training relabel."""
    _require(type(plan) is comparison.ComparisonPlan, "checkpoint requires an exact comparison plan")
    sources = json.loads(plan._sources_json)
    for name in SOURCE_FILES:
        current = hashlib.sha256(shared._read_regular(
            comparison.ROOT / name, maximum=2 * 1024**2, description="checkpoint execution source"
        )).hexdigest()
        _require(name not in sources or sources[name] == current,
                 "checkpoint execution source changed after base planning")
        sources[name] = current
    _require(len(sources) <= capacity.MAX_SOURCE_FILES, "checkpoint source inventory exceeds its bound")
    return replace(plan, _sources_json=_canonical(dict(sorted(sources.items()))).decode())


def build_checkpoint_plan(*args, **kwargs) -> comparison.ComparisonPlan:
    return extend_plan(comparison.build_comparison_plan(*args, **kwargs))


def _refresh(plan: comparison.ComparisonPlan) -> None:
    current = plan.execution.authority.trained_adapter
    fresh = build_checkpoint_plan(
        plan.execution.authority.preparation_directory,
        previous_preparation_directory=plan.previous.preparation_directory,
        previous_adapter=Path(plan.previous.trained_adapter["manifest_path"]),
        trained_adapter=None if current is None else Path(current["manifest_path"]),
    )
    _require(_same(fresh.to_dict(), plan.to_dict())
             and _same(fresh.execution.authority.trained_adapter, current),
             "checkpoint source, exact preparation or adapter changed after planning")


def _runtime(value: dict) -> None:
    _keys(value, {"torch_version", "transformers_version", "peft_version", "visible_cuda_devices", "cuda_device",
                  "dtype", "attention", "local_files_only", "model_loading"}, "checkpoint runtime")
    _require(all(type(value[k]) is str and 1 <= len(value[k]) <= 256
                 for k in ("torch_version", "transformers_version", "peft_version", "cuda_device"))
             and type(value["visible_cuda_devices"]) is int and value["visible_cuda_devices"] == 1
             and value["dtype"] == "bfloat16" and value["attention"] == "sdpa"
             and value["local_files_only"] is True and value["model_loading"] == comparison.LOADING,
             "checkpoint runtime contract differs")


def _sign(record: dict, field: str) -> dict:
    return {**record, field: _digest(record)}


def _header(plan, origins, runtime) -> dict:
    _runtime(runtime)
    return _sign({"schema": HEADER_SCHEMA, "plan": plan.to_dict(), "training_origins": origins,
                  "provider_runtime": runtime, "order": "role-cohort-goal", "goal_records": TOTAL_GOALS,
                  "research_claim_eligible": False, "historical_gpu_inference_attested": False}, "header_sha256")


def _binding(index: int, goals: tuple[dict, ...]) -> dict:
    _integer(index, "checkpoint ordinal", TOTAL_GOALS - 1)
    role = comparison.ROLES[index // comparison.GOAL_COUNT]
    goal_index = index % comparison.GOAL_COUNT
    goal = goals[goal_index]
    return {"ordinal": index + 1, "role": role, "cohort": comparison.COHORTS[goal_index // 32],
            "goal": goal["name"], "goal_sha256": _digest(goal),
            "source_sha256": hashlib.sha256(goal["source"].encode()).hexdigest(),
            "statement_sha256": goal["statement_sha256"]}


def _record(header_sha: str, previous_sha: str, binding: dict, row: dict) -> dict:
    return _sign({"schema": ROW_SCHEMA, "header_sha256": header_sha, "previous_sha256": previous_sha,
                  **binding, "row": row, "row_sha256": _digest(row),
                  "proposal_records_sha256": _digest(row["evidence"]["proposal_records"]),
                  "evidence_sha256": row["evidence_sha256"], "commands_sha256": row["commands_sha256"]},
                 "record_sha256")


def _validate_row(plan, role, cohort_name, goal, row, runtime, origins, *, replay: bool,
                  context: tuple | None = None) -> dict | None:
    """The frozen full-lane checks applied to one exact bounded prefix row.

    Final publication also runs the original full-report validator. No fake
    padding rows or inferred negative outcomes are used for partial evidence.
    """
    # A store hoists only these identical immutable-plan-derived values. No
    # rows, proof checks or cross-run/source authentication are cached.
    cohort, provider = (plan.cohort(cohort_name), comparison._provider(plan, role, runtime, origins)) if context is None else context
    name = "pretrained" if role == "base" else "trained"
    limits = capacity.LIMITS
    _keys(row, {"goal", "status", "kernel_checked", "tactic_decisions", "proof_nodes", "commands_sha256",
                "model_generate_calls", "generation", "policy_identity", "evidence", "evidence_sha256",
                "research_claim_eligible"}, "checkpoint model goal")
    _require(row["goal"] == goal["name"] and row["research_claim_eligible"] is False, "checkpoint goal/claim differs")
    _integer(row["model_generate_calls"], "checkpoint calls", limits.max_model_calls)
    evidence = row["evidence"]
    encoded = _canonical(evidence)
    _require(len(encoded) <= shared.MAX_GOAL_EVIDENCE_BYTES
             and hashlib.sha256(encoded).hexdigest() == row["evidence_sha256"], "checkpoint evidence digest/bytes differ")
    _keys(evidence, {"v", "label", "status", "proved", "theorem", "policy", "policy_identity", "environment",
                     "limits", "commands_sha256", "proposal_records", "degraded", "eligible_for_comparison",
                     "comparison_ineligibility_reasons", "degradation_reasons", "search", "replay"}, "checkpoint evidence")
    _require(evidence["theorem"] == goal["statement"] and _same(evidence["environment"], cohort.environment)
             and _same(evidence["limits"], shared._limits_record(limits)) and evidence["degraded"] is False
             and evidence["degradation_reasons"] == [] and type(evidence["v"]) is int
             and evidence["v"] == comparison.HYDRA_RUNNER_VERSION
             and evidence["label"] == f"hydra-alpha-eval-{name}-{goal['name']}"
             and evidence["policy"] == f"hydra-alpha-portfolio-{name}-{goal['name']}"
             and evidence["eligible_for_comparison"] is False
             and evidence["comparison_ineligibility_reasons"] == [comparison.SURFACE_MACRO_V0_INELIGIBILITY],
             "checkpoint changed proof goal, authority, claim or limits")
    search = evidence["search"]
    _keys(search, {"status", "theorem", "commands", "certificate_nodes", "diagnostics", "model_calls",
                   "states_expanded", "states_discovered", "candidates_executed", "frontier_peak", "depth_reached"},
          "checkpoint search")
    _require(row["status"] == evidence["status"] == search["status"] and search["theorem"] == goal["statement"]
             and type(search["model_calls"]) is int and search["model_calls"] == row["model_generate_calls"]
             and type(search["states_expanded"]) is int and search["states_expanded"] == row["model_generate_calls"],
             "checkpoint search status/calls differ")
    for field, maximum, minimum in (("states_discovered", limits.max_states, 1),
                                    ("candidates_executed", limits.max_model_calls * 4, 0),
                                    ("frontier_peak", limits.beam_width, 1), ("depth_reached", limits.max_depth, 0)):
        _integer(search[field], field, maximum, minimum)
    _require(type(search["diagnostics"]) is list and len(search["diagnostics"]) <= 128, "checkpoint diagnostics exceed bound")
    for diagnostic in search["diagnostics"]:
        _keys(diagnostic, {"kind", "depth", "state_sha256", "command", "message"}, "checkpoint diagnostic")
        _integer(diagnostic["depth"], "diagnostic depth", limits.max_depth)
        _require(all(type(diagnostic[f]) is str and len(diagnostic[f].encode()) <= 4096
                     for f in ("kind", "state_sha256", "message"))
                 and (diagnostic["command"] is None or type(diagnostic["command"]) is str
                      and len(diagnostic["command"].encode()) <= 4096), "checkpoint diagnostic text exceeds bound")
    commands = search["commands"]
    _require(type(commands) is list and len(commands) <= limits.max_depth
             and all(type(c) is str and len(c.encode()) <= 4096 for c in commands), "checkpoint commands exceed bound")
    _require(type(row["tactic_decisions"]) is int and row["tactic_decisions"] == len(commands)
             and row["commands_sha256"] == evidence["commands_sha256"]
             == (_digest(commands) if row["status"] == "proof" else None), "checkpoint command digest/count differs")
    proposals = capacity._validate_proposals(cohort, goal, name, row, provider)
    if row["status"] != "proof":
        _require(row["status"] in {"limit", "exhausted"} and row["kernel_checked"] is False
                 and evidence["proved"] is False and not commands and evidence["replay"] is None
                 and row["proof_nodes"] is None and search["certificate_nodes"] is None, "checkpoint invented proof/unknown")
        return None
    _require(row["kernel_checked"] is True and evidence["proved"] is True and commands, "checkpoint proof claim differs")
    saved = evidence["replay"]
    _require(type(saved) is dict and saved.get("kernel_checked") is True and saved.get("theorem") == goal["statement"]
             and saved.get("status") == "proved" and type(saved.get("trace")) is list
             and len(saved["trace"]) == len(commands) + 1, "checkpoint lacks original checked trace")
    _integer(row["proof_nodes"], "checkpoint proof nodes", 1_000_000, 1)
    _require(type(search["certificate_nodes"]) is int and type(saved.get("proof_nodes")) is int
             and row["proof_nodes"] == search["certificate_nodes"] == saved["proof_nodes"], "checkpoint proof nodes differ")
    for command, step in zip(commands, saved["trace"][:-1], strict=True):
        _require(type(step) is dict and step.get("tactic") == command and type(step.get("goals_before")) is list,
                 "checkpoint trace command/prestate differs")
        normalized = comparison._normalize_metavariables(tuple(step["goals_before"]))
        _require(any(command in p["accepted_candidates"]
                     and comparison._normalize_metavariables(tuple(p["goals"])) == normalized for p in proposals),
                 "checkpoint successful command/prestate was not among model proposals")
    if replay:
        _require("torch" not in sys.modules, "checkpoint replay must precede model imports")
        fresh, process = capacity._replay_success(cohort, goal, row)
        _require(fresh.get("kernel_checked") is True and fresh.get("theorem") == goal["statement"]
                 and fresh.get("proof_nodes") == row["proof_nodes"] and _same(fresh, saved),
                 "checkpoint independent original-goal replay differs")
        return {"role": role, "cohort": cohort_name, "goal": goal["name"],
                "commands_sha256": row["commands_sha256"], "proof_nodes": row["proof_nodes"], "replay_process": process}
    return None


def _directory(path: Path, *, create: bool) -> int:
    path = path.absolute()
    _require(len(str(path).encode()) <= 4096 and ".." not in path.parts and 1 < len(path.parts) <= 64,
             "unsafe checkpoint directory path")
    readable = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    # Shared Linux ancestors may grant search/traversal but not directory-read
    # permission. O_PATH anchors those components without listing them; the
    # final storage descriptor must still support listdir/fsync. O_DIRECTORY
    # remains essential with O_PATH|O_NOFOLLOW: never accept a symlink itself.
    access = getattr(os, "O_PATH", os.O_RDONLY) if sys.platform == "linux" else os.O_RDONLY
    ancestor = access | os.O_DIRECTORY | os.O_NOFOLLOW
    current = os.open(path.anchor, ancestor)
    try:
        for index, part in enumerate(path.parts[1:], 1):
            final = index == len(path.parts) - 1
            if create and final:
                # Only the immediately mutated, project-owned parent needs a
                # readable fd for durable mkdir. Reopen it through the anchored
                # descriptor before mutation; fsync on an O_PATH fd is invalid.
                parent = os.open(".", readable, dir_fd=current)
                try:
                    os.mkdir(part, mode=0o700, dir_fd=parent)
                    os.fsync(parent)
                    following = os.open(part, readable, dir_fd=parent)
                finally:
                    os.close(parent)
            else:
                following = os.open(part, readable if final else ancestor, dir_fd=current)
            os.close(current)
            current = following
        info = os.fstat(current)
        _require(stat.S_IMODE(info.st_mode) & 0o022 == 0, "checkpoint directory must not be group/world writable")
        result, current = current, -1
        return result
    finally:
        if current >= 0:
            os.close(current)


class CheckpointStore:
    """Locked, bounded canonical files; ambiguous interrupted commits reject."""

    # Fixed subclasses may supply a separately versioned panel. The original
    # defaults and public V1 entrypoints retain exactly their 288-row contract;
    # no schema, role, or goal inventory is inferred from saved checkpoint data.
    total_goals = TOTAL_GOALS
    goals_per_role = comparison.GOAL_COUNT
    head_schema = HEAD_SCHEMA
    verify_schema = VERIFY_SCHEMA
    claim = comparison.CLAIM

    def _goal_inventory(self):
        return comparison.comparison_goals()

    def _make_header(self, runtime):
        return _header(self.plan, self.origins, runtime)

    def _goal_binding(self, index):
        return _binding(index, self.goals)

    def _make_record(self, previous, binding, row):
        return _record(self.header["header_sha256"], previous, binding, row)

    def _validate_completed_row(self, binding, row, *, replay):
        return _validate_row(
            self.plan, binding["role"], binding["cohort"],
            self.goals[(binding["ordinal"] - 1) % self.goals_per_role], row,
            self.header["provider_runtime"], self.origins, replay=replay,
            context=self.contexts[binding["role"], binding["cohort"]],
        )

    def __init__(self, path: Path, plan, origins, *, runtime: dict | None = None,
                 resume: bool = False, progress: Progress | None = None):
        self.path, self.plan, self.origins = path.absolute(), plan, origins
        self.progress = progress or Progress()
        self.goals = self._goal_inventory()
        self.rows, self.hashes, self.replayed = [], [], []
        self.fd = self.lock = -1
        try:
            self.fd = _directory(self.path, create=not resume)
            flags = os.O_RDWR | os.O_NOFOLLOW | (0 if resume else os.O_CREAT | os.O_EXCL)
            self.lock = os.open(".lock", flags, 0o600, dir_fd=self.fd)
            info = os.fstat(self.lock)
            _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0,
                     "unsafe checkpoint lock")
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if resume:
                self._load()
            else:
                _require(runtime is not None, "new checkpoint needs its actual runtime")
                self.header = self._make_header(runtime)
                self.head = self._head(0, self.header["header_sha256"], 0, None)
                self._write("header.json", self.header, replace_existing=False)
                self._write("HEAD.json", self.head, replace_existing=False)
            self.runtime = self.header["provider_runtime"]
            self._contexts()
            self.assert_unchanged()
        except BaseException:
            self.close()
            raise

    def close(self) -> None:
        if self.lock >= 0:
            os.close(self.lock)
            self.lock = -1
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def _read(self, name: str, maximum: int) -> tuple[dict, bytes]:
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
        try:
            info = os.fstat(fd)
            _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size <= maximum,
                     "checkpoint file is unsafe or exceeds its byte bound")
            chunks, retained = [], 0
            while True:
                chunk = os.read(fd, min(65536, maximum + 1 - retained))
                if not chunk:
                    break
                chunks.append(chunk)
                retained += len(chunk)
                _require(retained <= maximum, "checkpoint file exceeds its byte bound")
            raw = b"".join(chunks)
            _require(len(raw) == info.st_size, "checkpoint file changed during read")
        finally:
            os.close(fd)
        value = shared._json_object(raw, description="checkpoint " + name)
        _require(raw == _canonical(value) + b"\n", "checkpoint is noncanonical or truncated")
        return value, raw

    def _write(self, name: str, value: dict, *, replace_existing: bool) -> None:
        raw = _canonical(value) + b"\n"
        _require(len(raw) <= (MAX_ROW_BYTES if name.endswith(".goal.json") else MAX_HEADER_BYTES),
                 "checkpoint write exceeds its byte bound")
        if not replace_existing:
            _require(name not in os.listdir(self.fd), "checkpoint refuses to overwrite existing evidence")
        temporary = ".transaction-" + uuid.uuid4().hex
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=self.fd)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            if replace_existing:
                os.replace(temporary, name, src_dir_fd=self.fd, dst_dir_fd=self.fd)
            else:
                # Atomic no-replace publication; a racing file is preserved.
                os.link(temporary, name, src_dir_fd=self.fd, dst_dir_fd=self.fd, follow_symlinks=False)
                os.unlink(temporary, dir_fd=self.fd)
            os.fsync(self.fd)
        except BaseException:
            # Preserve an interrupted transaction for diagnosis. Resume must
            # reject it rather than truncate evidence or silently retry work.
            raise

    def _head(self, count, digest, size, inflight) -> dict:
        return _sign({"schema": self.head_schema, "header_sha256": self.header["header_sha256"],
                      "completed": count, "record_sha256": digest, "record_bytes": size,
                      "inflight": inflight}, "head_sha256")

    def _contexts(self) -> None:
        runtime = self.header["provider_runtime"]
        cohorts = {name: self.plan.cohort(name) for name in comparison.COHORTS}
        providers = {role: comparison._provider(self.plan, role, runtime, self.origins) for role in comparison.ROLES}
        self.contexts = {(role, name): (cohorts[name], providers[role])
                         for role in comparison.ROLES for name in comparison.COHORTS}

    def _inventory(self, count: int) -> None:
        expected = {".lock", "header.json", "HEAD.json"}
        expected.update(f"{index + 1:06d}.goal.json" for index in range(count))
        observed = set()
        with os.scandir(self.fd) as entries:
            for entry in entries:
                _require(len(observed) < self.total_goals + 3, "checkpoint inventory exceeds its file bound")
                _require(not entry.is_symlink() and entry.is_file(follow_symlinks=False), "unsafe checkpoint entry")
                observed.add(entry.name)
        _require(observed == expected, "checkpoint has missing, skipped, duplicate or uncommitted entries")

    def _load(self) -> None:
        header, _ = self._read("header.json", MAX_HEADER_BYTES)
        _require(type(header.get("provider_runtime")) is dict, "checkpoint lacks its runtime")
        expected = self._make_header(header["provider_runtime"])
        _require(_same(header, expected), "checkpoint header changed its exact plan, source or training origins")
        self.header = header
        self._contexts()
        self.head, _ = self._read("HEAD.json", MAX_HEADER_BYTES)
        _keys(self.head, {"schema", "header_sha256", "completed", "record_sha256", "record_bytes",
                          "inflight", "head_sha256"}, "checkpoint HEAD")
        capacity._signed(self.head, "head_sha256")
        _require(self.head["schema"] == self.head_schema and self.head["header_sha256"] == header["header_sha256"],
                 "checkpoint HEAD header/schema differs")
        count = _integer(self.head.get("completed"), "checkpoint completed count", self.total_goals)
        _integer(self.head["record_bytes"], "checkpoint byte count", MAX_CHECKPOINT_BYTES)
        _require(self.head.get("inflight") is None,
                 "checkpoint contains an interrupted in-flight goal; refusing hidden generation retries")
        self._inventory(count)
        previous, total = header["header_sha256"], 0
        for index in range(count):
            record, raw = self._read(f"{index + 1:06d}.goal.json", MAX_ROW_BYTES)
            binding = self._goal_binding(index)
            row = record.get("row")
            _require(type(row) is dict, "checkpoint row is malformed")
            checked = self._validate_completed_row(binding, row, replay=True)
            _require(_same(record, self._make_record(previous, binding, row)),
                     "checkpoint chain, order, goal or evidence binding differs")
            previous = record["record_sha256"]
            total += len(raw)
            _require(total <= MAX_CHECKPOINT_BYTES, "checkpoint total bytes exceed bound")
            self.rows.append(row)
            self.hashes.append(hashlib.sha256(raw).hexdigest())
            if checked is not None:
                self.replayed.append(checked)
            self.progress.emit("checkpoint-row-verified", completed=index + 1, total=self.total_goals,
                               role=binding["role"], cohort=binding["cohort"], goal=binding["goal"],
                               kernel_checked=row["kernel_checked"])
        _require(_same(self.head, self._head(count, previous, total, None)), "checkpoint HEAD/count/bytes differs")
        self._cohort_bounds()

    def _cohort_bounds(self) -> None:
        for offset in range(0, len(self.rows), 32):
            group = self.rows[offset:offset + 32]
            _require(sum(r["model_generate_calls"] for r in group) <= 256
                     and sum(len(_canonical(r["evidence"])) for r in group) <= shared.MAX_LANE_EVIDENCE_BYTES,
                     "checkpoint cohort exceeds call/evidence reservation")

    def assert_unchanged(self, *, contents: bool = True) -> None:
        other = _directory(self.path, create=False)
        try:
            a, b = os.fstat(self.fd), os.fstat(other)
            _require((a.st_dev, a.st_ino) == (b.st_dev, b.st_ino), "checkpoint directory was replaced")
        finally:
            os.close(other)
        held = os.fstat(self.lock)
        named = os.stat(".lock", dir_fd=self.fd, follow_symlinks=False)
        _require(stat.S_ISREG(named.st_mode) and named.st_nlink == held.st_nlink == 1
                 and named.st_size == held.st_size == 0
                 and (named.st_dev, named.st_ino) == (held.st_dev, held.st_ino),
                 "checkpoint lock identity was replaced")
        self._inventory(len(self.rows))
        _require(_same(self._read("header.json", MAX_HEADER_BYTES)[0], self.header)
                 and _same(self._read("HEAD.json", MAX_HEADER_BYTES)[0], self.head), "checkpoint metadata changed")
        if contents:
            for index, digest in enumerate(self.hashes):
                _, raw = self._read(f"{index + 1:06d}.goal.json", MAX_ROW_BYTES)
                _require(hashlib.sha256(raw).hexdigest() == digest, "committed checkpoint evidence changed")

    def begin(self, role: str, cohort: str, goal: dict) -> None:
        self.assert_unchanged(contents=False)
        binding = self._goal_binding(len(self.rows))
        _require(self.head["inflight"] is None and binding["role"] == role and binding["cohort"] == cohort
                 and _same(goal, self.goals[len(self.rows) % self.goals_per_role]), "checkpoint attempted a duplicate/skipped goal")
        self.head = self._head(len(self.rows), self.head["record_sha256"], self.head["record_bytes"], binding)
        self._write("HEAD.json", self.head, replace_existing=True)

    def append(self, row: dict) -> None:
        self.assert_unchanged(contents=False)
        binding = self._goal_binding(len(self.rows))
        _require(_same(self.head["inflight"], binding), "checkpoint completion has no exact in-flight goal")
        row = shared._json_object(_canonical(row), description="completed checkpoint row")
        self._validate_completed_row(binding, row, replay=False)
        record = self._make_record(self.head["record_sha256"], binding, row)
        raw = _canonical(record) + b"\n"
        total = self.head["record_bytes"] + len(raw)
        _require(len(raw) <= MAX_ROW_BYTES and total <= MAX_CHECKPOINT_BYTES, "checkpoint evidence exceeds disk bound")
        offset = len(self.rows) // 32 * 32
        group = self.rows[offset:] + [row]
        _require(sum(r["model_generate_calls"] for r in group) <= 256
                 and sum(len(_canonical(r["evidence"])) for r in group) <= shared.MAX_LANE_EVIDENCE_BYTES,
                 "checkpoint cohort exceeds its exact reservation")
        self._write(f"{len(self.rows) + 1:06d}.goal.json", record, replace_existing=False)
        head = self._head(len(self.rows) + 1, record["record_sha256"], total, None)
        self._write("HEAD.json", head, replace_existing=True)
        self.head = head
        self.rows.append(row)
        self.hashes.append(hashlib.sha256(raw).hexdigest())

    def receipt(self, *, status: str) -> dict:
        return {"schema": self.verify_schema, "status": status, "plan_sha256": self.header["plan"]["plan_sha256"],
                "checkpoint_header_sha256": self.header["header_sha256"], "checkpoint_head_sha256": self.head["head_sha256"],
                "completed_goal_records": len(self.rows), "total_goal_records": self.total_goals,
                "complete_comparison": len(self.rows) == self.total_goals, "clean_boundary": self.head["inflight"] is None,
                "committed_model_generate_calls": sum(r["model_generate_calls"] for r in self.rows),
                "independently_replayed_proofs": self.replayed,
                "model_outputs_regenerated": False, "historical_gpu_inference_attested": False,
                "research_claim_eligible": False, "claim_boundary": self.claim}


def verify_checkpoint(plan, directory: Path, *, progress: Progress | None = None) -> dict:
    _require("torch" not in sys.modules, "checkpoint verification must start without model frameworks")
    _refresh(plan)
    origins, _, _ = comparison._origins(plan)
    with CheckpointStore(directory, plan, origins, resume=True, progress=progress) as store:
        return store.receipt(status="prefix-verified")


def _lane(plan, role, cohort_name, rows, runtime, origins) -> dict:
    cohort = plan.cohort(cohort_name)
    return {"status": "executed", "lane": "pretrained" if role == "base" else "trained", "model": plan.model,
            "adapter_attached": role != "base", "epoch_sha256": cohort.epoch.epoch_sha256,
            "environment_sha256": cohort.environment["environment_sha256"], "goal_set_sha256": cohort.goal_set_sha256,
            "matched_budget": cohort.matched_budget, "provider": comparison._provider(plan, role, runtime, origins),
            "goals": rows, "kernel_checked_proofs": sum(r["kernel_checked"] for r in rows),
            "model_generate_calls": sum(r["model_generate_calls"] for r in rows),
            "retained_evidence_bytes": sum(len(_canonical(r["evidence"])) for r in rows),
            "research_claim_eligible": False}


def execute_checkpoint_comparison(plan, *, checkpoint_directory: Path, resume: bool = False,
                                  progress: Progress | None = None, stop_after_seconds: float | None = None,
                                  stop_requested: Callable[[], bool] | None = None) -> dict:
    """Resume only clean authenticated goals; final schema remains unchanged."""
    _require(type(resume) is bool, "checkpoint resume must be Boolean")
    _require(not resume or "torch" not in sys.modules, "checkpoint resume must precede model imports")
    if stop_after_seconds is not None:
        _require(type(stop_after_seconds) in (int, float) and math.isfinite(stop_after_seconds)
                 and 0 < stop_after_seconds <= 7200, "soft-stop seconds must be finite and within 7200")
    progress = progress or Progress()
    progress.emit("validation-start", resume=resume)
    _refresh(plan)
    origins, adapter_directories, tokenizer_directory = comparison._origins(plan)
    progress.emit("validation-complete", plan_sha256=plan.to_dict()["plan_sha256"])
    store, torch, tokenizer = None, None, None
    try:
        if resume:
            progress.emit("checkpoint-validation-start")
            store = CheckpointStore(checkpoint_directory, plan, origins, resume=True, progress=progress)
            progress.emit("checkpoint-validation-complete", completed=len(store.rows), total=TOTAL_GOALS,
                          independently_replayed_proofs=len(store.replayed))
        if store is None or len(store.rows) < TOTAL_GOALS:
            progress.emit("runtime-loading-start")
            torch, transformers, peft = shared._model_runtime()
            runtime = {"torch_version": str(torch.__version__), "transformers_version": str(transformers.__version__),
                       "peft_version": str(peft.__version__), "visible_cuda_devices": 1,
                       "cuda_device": torch.cuda.get_device_name(0), "dtype": "bfloat16", "attention": "sdpa",
                       "local_files_only": True, "model_loading": comparison.LOADING}
            if store is None:
                store = CheckpointStore(checkpoint_directory, plan, origins, runtime=runtime, progress=progress)
            else:
                _require(_same(runtime, store.runtime), "resumed model runtime differs from checkpoint")
            shared._reset_seed(torch, transformers, capacity.SEED)
            tokenizer = transformers.AutoTokenizer.from_pretrained(
                str(tokenizer_directory), trust_remote_code=False, use_fast=True, local_files_only=True)
            if tokenizer.pad_token_id is None:
                _require(tokenizer.eos_token_id is not None, "checkpoint tokenizer has no EOS/padding identity")
                tokenizer.pad_token_id = tokenizer.eos_token_id
            progress.emit("runtime-loading-complete", completed=len(store.rows), total=TOTAL_GOALS)
        runtime = store.runtime

        def stop_at_boundary():
            reason = "signal" if stop_requested is not None and stop_requested() else (
                "soft_deadline" if stop_after_seconds is not None
                and time.monotonic() - progress.started >= stop_after_seconds else None)
            if reason is not None and len(store.rows) < TOTAL_GOALS:
                store.assert_unchanged()
                receipt = {**store.receipt(status="paused"), "pause_reason": reason}
                progress.emit("paused", completed=len(store.rows), total=TOTAL_GOALS,
                              reason=reason, checkpoint_head_sha256=store.head["head_sha256"])
                raise CheckpointPaused(receipt)

        lanes = {}
        for role_index, role in enumerate(comparison.ROLES):
            role_start = role_index * 96
            role_complete = len(store.rows) >= role_start + 96
            model = None
            try:
                if not role_complete:
                    stop_at_boundary()
                    fresh_origins, _, _ = comparison._origins(plan)
                    _require(_same(fresh_origins, origins), "training-origin bytes changed before model loading")
                    shared._reset_seed(torch, transformers, capacity.SEED)
                    progress.emit("model-loading-start", role=role, completed=len(store.rows), total=TOTAL_GOALS)
                    model = shared._load_base_model(torch, transformers, plan.model)
                    if role != "base":
                        model = peft.PeftModel.from_pretrained(model, str(adapter_directories[role]), is_trainable=False)
                    model.to("cuda:0")
                    model.eval()
                    progress.emit("model-loading-complete", role=role, completed=len(store.rows), total=TOTAL_GOALS)
                lanes[role] = {}
                for cohort_index, cohort_name in enumerate(comparison.COHORTS):
                    start = role_start + 32 * cohort_index
                    completed = tuple(store.rows[start:min(start + 32, len(store.rows))])
                    progress.emit("cohort-start", role=role, cohort=cohort_name,
                                  resumed_goals=len(completed), completed=len(store.rows), total=TOTAL_GOALS)
                    if len(completed) == 32:
                        lane = _lane(plan, role, cohort_name, list(completed), runtime, origins)
                    else:
                        goal_started = [0.0, 0.0]

                        def begin(goal):
                            stop_at_boundary()
                            store.begin(role, cohort_name, goal)
                            goal_started[:] = [time.monotonic(), time.process_time()]
                            progress.emit("goal-start", role=role, cohort=cohort_name, goal=goal["name"],
                                          completed=len(store.rows), total=TOTAL_GOALS)

                        def committed(row):
                            store.append(row)
                            progress.emit("goal-committed", role=role, cohort=cohort_name, goal=row["goal"],
                                          completed=len(store.rows), total=TOTAL_GOALS, status=row["status"],
                                          kernel_checked=row["kernel_checked"], model_generate_calls=row["model_generate_calls"],
                                          goal_wall_seconds=round(time.monotonic() - goal_started[0], 6),
                                          goal_cpu_seconds=round(time.process_time() - goal_started[1], 6),
                                          checkpoint_head_sha256=store.head["head_sha256"])

                        lane = shared._run_model_lane(
                            plan.cohort(cohort_name), model=model, tokenizer=tokenizer,
                            lane="pretrained" if role == "base" else "trained",
                            provider=comparison._provider(plan, role, runtime, origins), completed_rows=completed,
                            on_goal=committed, on_goal_start=begin)
                        _require(_same(lane["goals"], store.rows[start:start + 32]), "live/checkpoint rows differ")
                    lanes[role][cohort_name] = lane
                    progress.emit("cohort-complete", role=role, cohort=cohort_name,
                                  completed=len(store.rows), total=TOTAL_GOALS)
            finally:
                del model
                if not role_complete and torch is not None:
                    from hydra_training_v5.peano_policy.authority_runtime import clear_authority_runtime_cache

                    clear_authority_runtime_cache()
                    shared._release_gpu(torch)
                    progress.emit("model-unloaded", role=role)
        _require(len(store.rows) == TOTAL_GOALS and store.head["inflight"] is None,
                 "partial checkpoint cannot publish a complete comparison")
        progress.emit("final-validation-start", completed=TOTAL_GOALS, total=TOTAL_GOALS)
        final_origins, _, _ = comparison._origins(plan)
        _require(_same(final_origins, origins), "training-origin bytes changed during inference")
        _refresh(plan)
        store.assert_unchanged()
        result = {"schema": comparison.RESULT_SCHEMA, "status": "executed", "plan": plan.to_dict(),
                  "training_origins": origins, "provider_runtime": runtime, "lanes": lanes,
                  "metrics": comparison._metrics(lanes), "claim_boundary": comparison.CLAIM,
                  "research_claim_eligible": False, "sealed_benchmark": False,
                  "final_benchmark_expanded": False, "independent_discoveries": False}
        result["evaluation_sha256"] = _digest(result)
        comparison.validate_comparison_result(plan, result, replay=False, origins=origins)
        progress.emit("final-validation-complete", evaluation_sha256=result["evaluation_sha256"],
                      checkpoint_head_sha256=store.head["head_sha256"], completed=TOTAL_GOALS, total=TOTAL_GOALS)
        return result
    finally:
        if store is not None:
            store.close()


def verify_comparison(path: Path, *, preparation_directory: Path, previous_preparation_directory: Path,
                      previous_adapter: Path, trained_adapter: Path | None = None) -> dict:
    """Dispatch only the explicitly source-bound checkpoint extension offline."""
    _require("torch" not in sys.modules, "offline comparison replay must start without model frameworks")
    raw = shared._read_regular(path, maximum=comparison.MAX_REPORT_BYTES, description="comparison result")
    report = shared._json_object(raw, description="comparison result")
    sources = report.get("plan", {}).get("source_files", {}) if type(report.get("plan")) is dict else {}
    builder = build_checkpoint_plan if type(sources) is dict and SOURCE_FILES[0] in sources else comparison.build_comparison_plan
    plan = builder(preparation_directory, previous_preparation_directory=previous_preparation_directory,
                   previous_adapter=previous_adapter, trained_adapter=trained_adapter)
    result = comparison.validate_comparison_result(plan, report, replay=True)
    result["report_file_sha256"] = hashlib.sha256(raw).hexdigest()
    return result


def check_fresh_output(path: Path) -> None:
    """No symlink components, existing target, or implicit parent creation."""
    _require(path.name not in {"", ".", ".."}, "unsafe comparison output path")
    directory = _directory(path.parent, create=False)
    try:
        try:
            os.stat(path.name, dir_fd=directory, follow_symlinks=False)
        except FileNotFoundError:
            return
        raise comparison.ComparisonError("comparison output must be a fresh non-symlink file")
    finally:
        os.close(directory)


def publish_result(path: Path, rendered: str) -> None:
    """Publish a complete final file atomically, durably, without replacement."""
    raw = rendered.encode("utf-8")
    _require(len(raw) <= comparison.MAX_REPORT_BYTES, "comparison output exceeds its byte bound")
    check_fresh_output(path)
    directory = _directory(path.parent, create=False)
    temporary = ".comparison-publication-" + uuid.uuid4().hex
    try:
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        # link() is atomic and refuses an existing destination, unlike replace.
        os.link(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
        os.unlink(temporary, dir_fd=directory)
        os.fsync(directory)
    finally:
        os.close(directory)
