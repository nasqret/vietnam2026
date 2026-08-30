"""Profile-bound PRIMARY32 checkpoints; never convert or resume old inference.

The writer reuses the reviewed no-follow, locked, durable file transaction.
Verification opens only existing read-only files and authenticates the entire
committed chain before replaying any proof. An exact in-flight next binding is
reported as unknown, never retried or promoted. Ambiguous transaction debris is
preserved and rejected. Source/origin authentication belongs to the separately
versioned paired plan; these integrity receipts are not GPU attestations.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
from pathlib import Path
import stat
import sys

from training.peano_hydra import capacity, comparison, comparison_checkpoint as cp, evaluation as shared
from training.peano_hydra.runner import HYDRA_RUNNER_VERSION, HYDRA_PROFILED_RUNNER_VERSION, SURFACE_MACRO_V0_INELIGIBILITY
from training.peano_policy.state_identity import CONTEXT_ALPHA_V1, StateIdentityReport, search_profile_contract


HEADER_SCHEMA = "peano-hydra-paired-search-checkpoint-header-v1"
HEAD_SCHEMA = "peano-hydra-paired-search-checkpoint-head-v1"
ROW_SCHEMA = "peano-hydra-paired-search-checkpoint-goal-v1"
PREFIX_SCHEMA = "peano-hydra-paired-search-prefix-verification-v1"
LANES = ("legacy", "context-alpha")
GOAL_COUNT = 32
TOTAL_GOALS = 64
_canonical, _digest = shared._canonical, shared._digest
_require, _same, _keys, _integer = capacity._require, capacity._same, capacity._keys, capacity._integer
_ROW_FIELDS = {"goal", "status", "kernel_checked", "tactic_decisions", "proof_nodes", "commands_sha256",
               "model_generate_calls", "generation", "policy_identity", "evidence", "evidence_sha256",
               "research_claim_eligible", "resources"}
_EVIDENCE_FIELDS = {"v", "label", "status", "proved", "theorem", "policy", "policy_identity", "environment",
                    "limits", "commands_sha256", "proposal_records", "degraded", "eligible_for_comparison",
                    "comparison_ineligibility_reasons", "degradation_reasons", "search", "replay"}
_SEARCH_FIELDS = {"status", "theorem", "commands", "certificate_nodes", "diagnostics", "model_calls",
                  "states_expanded", "states_discovered", "candidates_executed", "frontier_peak", "depth_reached"}
_BATCH_FIELDS = {"v", "id", "session", "status", "kernel_checked", "theorem", "goals", "tactics_requested",
                 "tactics_applied", "engine_steps", "failed_tactics", "proof_nodes", "failed_step", "error_type",
                 "error", "mode", "surface", "environment_sha256", "classical", "on_error", "trace_v", "trace"}
_TRACE_FIELDS = {"v", "session", "step", "goals_before", "focus", "tactic", "goals_after", "status", "error"}


def _api():
    # The plan/executor imports this store, so keep the reverse edge lazy.
    from training.peano_hydra import search_comparison

    return search_comparison


def _model_free() -> None:
    _require(not {"torch", "transformers", "peft"} & set(sys.modules),
             "paired independent verification must precede model imports")


def _plan_origin(plan, origin) -> None:
    api = _api()
    _require(type(plan) is api.PairedSearchPlan and tuple(api.LANES) == LANES,
             "paired checkpoint requires its exact separately versioned plan")
    _require(_same(origin, plan.origin), "paired checkpoint changed its authenticated training origin")
    _require(type(plan.execution.goals) is tuple and len(plan.execution.goals) == GOAL_COUNT
             and len({goal["name"] for goal in plan.execution.goals}) == GOAL_COUNT,
             "paired checkpoint changed its fixed PRIMARY32 inventory")
    _require(_same(shared._limits_record(plan.execution.limits), shared._limits_record(capacity.LIMITS))
             and plan.execution.seed == capacity.SEED and type(plan.execution.seed) is int
             and type(plan.execution.max_new_tokens) is int
             and plan.execution.max_new_tokens == capacity.MAX_NEW_TOKENS,
             "paired checkpoint changed its common generation/search reservation")


def _profile(lane: str):
    _require(type(lane) is str and lane in LANES, "unknown paired search lane")
    expected = None if lane == "legacy" else CONTEXT_ALPHA_V1
    _require(_api().search_profile_for(lane) == expected, "paired search lane changed its fixed profile")
    return expected, search_profile_contract(expected)


def _resources(value) -> None:
    _keys(value, {"goal_wall_seconds", "goal_cpu_seconds", "process_peak_rss_bytes",
                  "cuda_peak_allocated_bytes", "cuda_peak_reserved_bytes"}, "paired goal resources")
    for name in ("goal_wall_seconds", "goal_cpu_seconds"):
        _require(type(value[name]) in (int, float) and math.isfinite(value[name]) and value[name] >= 0,
                 "paired resource times must be finite nonnegative observations")
    for name in ("process_peak_rss_bytes", "cuda_peak_allocated_bytes", "cuda_peak_reserved_bytes"):
        _integer(value[name], name, 2**63 - 1)
    _require(value["cuda_peak_reserved_bytes"] >= value["cuda_peak_allocated_bytes"],
             "paired CUDA reserved bytes are smaller than allocated bytes")


def _profile_evidence(evidence, search, profile, contract) -> None:
    _keys(evidence, _EVIDENCE_FIELDS | ({"search_profile"} if profile is not None else set()), "paired Hydra evidence")
    _keys(search, _SEARCH_FIELDS | ({"state_identity"} if profile is not None else set()), "paired search")
    version = HYDRA_RUNNER_VERSION if profile is None else HYDRA_PROFILED_RUNNER_VERSION
    _require(type(evidence["v"]) is int and evidence["v"] == version, "paired runner/profile version differs")
    if profile is None:
        return
    identity = search["state_identity"]
    _keys(identity, {"contract", "counters"}, "paired state identity")
    _require(_same(evidence["search_profile"], contract) and _same(identity["contract"], contract),
             "paired top-level/nested search profile differs from its exact declared contract")
    counters = identity["counters"]
    _keys(counters, {"key_attempts", "keys_built", "keys_declined", "duplicate_states", "renamed_states",
                     "retained_key_bytes", "key_budget_declines"}, "paired state-identity counters")
    try:
        StateIdentityReport(**counters)
    except (TypeError, ValueError) as error:
        raise capacity.CapacityError(f"invalid paired state-identity counters: {error}") from None
    _integer(search["candidates_executed"], "paired candidate executions", 32)
    _integer(search["states_discovered"], "paired discovered states", 64, 1)
    _require(1 <= counters["key_attempts"] <= search["candidates_executed"] + 1
             and search["states_discovered"] <= counters["key_attempts"] - counters["duplicate_states"]
             and counters["retained_key_bytes"] <= min(contract["max_retained_key_bytes"],
                                                       search["states_discovered"] * contract["max_key_bytes"]),
             "paired state-identity counters exceed actual bounded work")


def _replay_ids(evidence, contract):
    fields = [evidence["v"], evidence["label"], evidence["theorem"], evidence["commands_sha256"],
              evidence["environment"]["environment_sha256"]]
    if contract is not None:
        fields.append(contract["contract_sha256"])
    raw = json.dumps(fields, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    request_id = "hydra-replay-" + hashlib.sha256(raw).hexdigest()[:24]
    session = "peano-hydra-" + evidence["commands_sha256"][:24]
    if contract is not None:
        session += "-" + contract["contract_sha256"][:24]
    return request_id, session


def _saved_proof(evidence, goal, row, contract, proposals) -> None:
    saved, commands = evidence["replay"], evidence["search"]["commands"]
    _keys(saved, _BATCH_FIELDS, "paired checked replay")
    expected_id, expected_session = _replay_ids(evidence, contract)
    _require(type(saved["v"]) is int and saved["v"] == 1
             and type(saved["trace_v"]) is int and saved["trace_v"] == 1
             and saved["id"] == expected_id and saved["session"] == expected_session,
             "paired original-goal replay lost its exact command/profile binding")
    _require(saved["kernel_checked"] is True and saved["status"] == "proved"
             and saved["theorem"] == goal["statement"] and saved["goals"] == []
             and saved["mode"] == "trace" and saved["classical"] is False and saved["on_error"] == "stop"
             and saved["surface"] == evidence["environment"]["surface"]
             and saved["environment_sha256"] == evidence["environment"]["environment_sha256"]
             and saved["failed_step"] is None and saved["error_type"] is None and saved["error"] is None,
             "paired saved replay changed its original theorem, authority or checked outcome")
    for name, exact in (("tactics_requested", len(commands)), ("tactics_applied", len(commands)),
                        ("failed_tactics", 0), ("proof_nodes", row["proof_nodes"])):
        _require(type(saved[name]) is int and saved[name] == exact, "paired replay command/proof accounting differs")
    _integer(saved["engine_steps"], "paired replay engine steps", 1_000_000)
    trace = saved["trace"]
    _require(type(trace) is list and len(trace) == len(commands) + 1, "paired replay trace length differs")
    previous_after = None
    for index, (command, step) in enumerate(zip(commands, trace[:-1], strict=True), 1):
        _keys(step, _TRACE_FIELDS, "paired replay trace step")
        _require(type(step["v"]) is int and step["v"] == 1 and type(step["step"]) is int
                 and step["step"] == index and step["session"] == expected_session
                 and step["tactic"] == command and step["status"] == "ok" and step["error"] is None,
                 "paired replay trace command/session/order differs")
        for name in ("goals_before", "goals_after"):
            _require(type(step[name]) is list and len(step[name]) <= 64
                     and all(type(g) is str and 1 <= len(g.encode()) <= 16384 for g in step[name]),
                     "paired replay trace goals exceed their bound")
        _require(bool(step["goals_before"]), "paired replay applied a command to no goals")
        _integer(step["focus"], "paired replay focus", len(step["goals_before"]) - 1)
        _require(previous_after is None or _same(previous_after, step["goals_before"]),
                 "paired replay trace is discontinuous")
        previous_after = step["goals_after"]
        normalized = comparison._normalize_metavariables(tuple(step["goals_before"]))
        _require(any(command in proposal["accepted_candidates"]
                     and comparison._normalize_metavariables(tuple(proposal["goals"])) == normalized
                     for proposal in proposals), "paired successful command/prestate was not a recorded model proposal")
    _require(previous_after == [], "paired checked trace retained an open goal")
    _keys(trace[-1], {"qed", "theorem", "proof_size", "tactic_count"}, "paired replay footer")
    _require(_same(trace[-1], {"qed": True, "theorem": goal["statement"], "proof_size": row["proof_nodes"],
                              "tactic_count": len(commands)}), "paired replay footer differs")


def validate_paired_row(plan, lane, goal, row, runtime, origin, *, replay=False):
    """Validate one exact profiled model row; optionally freshly replay its proof."""
    _require(type(replay) is bool, "paired replay flag must be Boolean")
    if replay:
        _model_free()
    _plan_origin(plan, origin)
    api = _api()
    api._runtime(runtime)
    profile, contract = _profile(lane)
    _require(any(_same(goal, candidate) for candidate in plan.execution.goals), "paired row is not a declared goal")
    _keys(row, _ROW_FIELDS, "paired model goal")
    _require(len(_canonical(row)) <= cp.MAX_ROW_BYTES and row["goal"] == goal["name"]
             and row["research_claim_eligible"] is False, "paired goal/claim/retained bytes differ")
    _resources(row["resources"])
    _integer(row["model_generate_calls"], "paired model calls", capacity.LIMITS.max_model_calls)
    evidence = row["evidence"]
    _require(type(evidence) is dict and type(evidence.get("search")) is dict, "paired row lacks search evidence")
    search = evidence["search"]
    _profile_evidence(evidence, search, profile, contract)
    encoded = _canonical(evidence)
    _require(len(encoded) <= shared.MAX_GOAL_EVIDENCE_BYTES
             and hashlib.sha256(encoded).hexdigest() == row["evidence_sha256"], "paired evidence digest/bytes differ")
    _require(evidence["theorem"] == goal["statement"] and search["theorem"] == goal["statement"]
             and _same(evidence["environment"], plan.execution.environment)
             and _same(evidence["limits"], shared._limits_record(capacity.LIMITS))
             and evidence["label"] == f"hydra-alpha-eval-trained-{goal['name']}"
             and evidence["policy"] == f"hydra-alpha-portfolio-trained-{goal['name']}"
             and evidence["degraded"] is False and evidence["degradation_reasons"] == []
             and evidence["eligible_for_comparison"] is False
             and evidence["comparison_ineligibility_reasons"] == [SURFACE_MACRO_V0_INELIGIBILITY],
             "paired evidence changed goal, authority, model labels, limits or claim")
    _require(row["status"] == evidence["status"] == search["status"]
             and type(search["model_calls"]) is int and type(search["states_expanded"]) is int
             and search["model_calls"] == search["states_expanded"] == row["model_generate_calls"],
             "paired search status/physical calls differ")
    for name, ceiling, minimum in (("states_discovered", 64, 1), ("candidates_executed", 32, 0),
                                    ("frontier_peak", 4, 1), ("depth_reached", 16, 0)):
        _integer(search[name], name, ceiling, minimum)
    diagnostics = search["diagnostics"]
    _require(type(diagnostics) is list and len(diagnostics) <= 128, "paired diagnostics exceed their bound")
    for diagnostic in diagnostics:
        _keys(diagnostic, {"kind", "depth", "state_sha256", "command", "message"}, "paired diagnostic")
        _integer(diagnostic["depth"], "paired diagnostic depth", 16)
        _require(all(type(diagnostic[k]) is str and len(diagnostic[k].encode()) <= 4096
                     for k in ("kind", "state_sha256", "message"))
                 and (diagnostic["command"] is None or type(diagnostic["command"]) is str
                      and len(diagnostic["command"].encode()) <= 4096), "paired diagnostic text exceeds its bound")
    commands = search["commands"]
    _require(type(commands) is list and len(commands) <= 16
             and all(type(c) is str and 1 <= len(c.encode()) <= 4096 for c in commands),
             "paired proof commands exceed their bound")
    _require(type(row["tactic_decisions"]) is int and row["tactic_decisions"] == len(commands)
             and row["commands_sha256"] == evidence["commands_sha256"]
             == (_digest(commands) if row["status"] == "proof" else None), "paired command digest/count differs")
    proposals = capacity._validate_proposals(plan.execution, goal, "trained", row,
                                             api.provider(plan, lane, runtime, origin))
    if row["status"] != "proof":
        _require(row["status"] in {"limit", "exhausted"} and row["kernel_checked"] is False
                 and evidence["proved"] is False and not commands and evidence["replay"] is None
                 and row["proof_nodes"] is None and search["certificate_nodes"] is None,
                 "paired unsuccessful attempt invented proof data")
        return None
    _require(row["kernel_checked"] is True and evidence["proved"] is True
             and 1 <= len(commands) <= search["depth_reached"], "paired proof claim/depth differs")
    _integer(row["proof_nodes"], "paired proof nodes", 1_000_000, 1)
    _require(type(search["certificate_nodes"]) is int and search["certificate_nodes"] == row["proof_nodes"],
             "paired search proof-node count differs")
    _saved_proof(evidence, goal, row, contract, proposals)
    if not replay:
        return None
    fresh, process = capacity._replay_success(plan.execution, goal, row)
    _require(_same(fresh, evidence["replay"]), "paired independent original-goal replay differs")
    return {"lane": lane, "role": lane, "cohort": "primary", "goal": goal["name"],
            "search_profile": profile, "search_profile_sha256": None if contract is None else contract["contract_sha256"],
            "commands_sha256": row["commands_sha256"], "proof_nodes": row["proof_nodes"], "replay_process": process}


class PairedCheckpointStore(cp.CheckpointStore):
    """Fresh writes OR read-only verification. No public inference resume."""

    total_goals = TOTAL_GOALS
    goals_per_role = GOAL_COUNT
    head_schema = HEAD_SCHEMA
    verify_schema = PREFIX_SCHEMA

    def __init__(self, path, plan, origin, *, runtime=None, progress=None, verify_only=False, replay_proofs=True):
        _require(type(verify_only) is bool and type(replay_proofs) is bool,
                 "paired verification/replay flags must be Boolean")
        _require(verify_only or replay_proofs, "paired metadata-only mode is restricted to read-only verification")
        _plan_origin(plan, origin)
        self.verify_only, self.replay_proofs = verify_only, replay_proofs
        self.claim = _api().CLAIM
        if not verify_only:
            super().__init__(path, plan, origin, runtime=runtime, resume=False, progress=progress)
            return
        _require(runtime is None, "paired read-only verification must use the saved checked runtime")
        _model_free()
        self.path, self.plan, self.origins = Path(path).absolute(), plan, origin
        self.progress = progress or cp.Progress()
        self.goals = self._goal_inventory()
        self.rows, self.hashes, self.replayed = [], [], []
        self.fd = self.lock = -1
        try:
            _api()._refresh(plan)
            self.fd = cp._directory(self.path, create=False)
            self.lock = os.open(".lock", os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
            info = os.fstat(self.lock)
            _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1 and info.st_size == 0, "unsafe paired lock")
            fcntl.flock(self.lock, fcntl.LOCK_SH | fcntl.LOCK_NB)
            self._load()
            self.runtime = self.header["provider_runtime"]
            self.assert_unchanged()
            _api()._refresh(plan)
            self.assert_unchanged()
        except BaseException:
            self.close()
            raise

    def _goal_inventory(self):
        _plan_origin(self.plan, self.origins)
        return self.plan.execution.goals

    def _make_header(self, runtime):
        _api()._runtime(runtime)
        record = self.plan.to_dict()
        capacity._signed(record, "plan_sha256")
        return cp._sign({"schema": HEADER_SCHEMA, "plan": record, "training_origin": self.origins,
                         "provider_runtime": runtime, "order": "lane-primary-goal", "lanes": list(LANES),
                         "goal_records": TOTAL_GOALS, "research_claim_eligible": False,
                         "historical_gpu_inference_attested": False}, "header_sha256")

    def _goal_binding(self, index):
        _integer(index, "paired checkpoint ordinal", TOTAL_GOALS - 1)
        lane, goal = LANES[index // GOAL_COUNT], self.goals[index % GOAL_COUNT]
        profile, contract = _profile(lane)
        return {"ordinal": index + 1, "role": lane, "lane": lane, "cohort": "primary", "goal": goal["name"],
                "goal_sha256": _digest(goal), "source_sha256": hashlib.sha256(goal["source"].encode()).hexdigest(),
                "statement_sha256": goal["statement_sha256"], "search_profile": profile,
                "search_profile_sha256": None if contract is None else contract["contract_sha256"],
                "training_origin_sha256": self.origins["origin_sha256"]}

    def _make_record(self, previous, binding, row):
        return cp._sign({"schema": ROW_SCHEMA, "header_sha256": self.header["header_sha256"],
                         "previous_sha256": previous, **binding, "row": row, "row_sha256": _digest(row),
                         "proposal_records_sha256": _digest(row["evidence"]["proposal_records"]),
                         "evidence_sha256": row["evidence_sha256"], "commands_sha256": row["commands_sha256"]},
                        "record_sha256")

    def _contexts(self):
        # No legacy comparison roles/cohorts or mutable validation caches.
        self.contexts = {}

    def _validate_completed_row(self, binding, row, *, replay):
        return validate_paired_row(self.plan, binding["lane"], self.goals[(binding["ordinal"] - 1) % GOAL_COUNT],
                                   row, self.header["provider_runtime"], self.origins, replay=replay)

    def _write(self, name, value, *, replace_existing):
        _require(not self.verify_only, "paired read-only verification cannot write checkpoints")
        return super()._write(name, value, replace_existing=replace_existing)

    def begin(self, role, cohort, goal):
        _require(not self.verify_only, "paired read-only verification cannot begin or resume inference")
        return super().begin(role, cohort, goal)

    def append(self, row):
        _require(not self.verify_only, "paired read-only verification cannot append or resume inference")
        return super().append(row)

    def _load(self):
        """Authenticate ALL metadata first, then replay only committed rows."""
        header, _ = self._read("header.json", cp.MAX_HEADER_BYTES)
        _require(type(header.get("provider_runtime")) is dict, "paired header lacks runtime")
        _require(_same(header, self._make_header(header["provider_runtime"])),
                 "paired checkpoint changed its exact plan, source, profile or origin")
        self.header = header
        self.head, _ = self._read("HEAD.json", cp.MAX_HEADER_BYTES)
        _keys(self.head, {"schema", "header_sha256", "completed", "record_sha256", "record_bytes", "inflight", "head_sha256"},
              "paired checkpoint HEAD")
        capacity._signed(self.head, "head_sha256")
        _require(self.head["schema"] == HEAD_SCHEMA and self.head["header_sha256"] == header["header_sha256"],
                 "paired HEAD schema/header differs")
        count = _integer(self.head["completed"], "paired committed count", TOTAL_GOALS)
        _integer(self.head["record_bytes"], "paired committed byte count", cp.MAX_CHECKPOINT_BYTES)
        inflight = self.head["inflight"]
        _require(inflight is None or count < TOTAL_GOALS and _same(inflight, self._goal_binding(count)),
                 "paired in-flight binding is not the exact next uncommitted goal")
        self._inventory(count)  # Extra rows or transaction debris reject, without deletion.
        previous, total = header["header_sha256"], 0
        for index in range(count):
            record, raw = self._read(f"{index + 1:06d}.goal.json", cp.MAX_ROW_BYTES)
            binding, row = self._goal_binding(index), record.get("row")
            _require(type(row) is dict and type(row.get("evidence")) is dict
                     and "proposal_records" in row["evidence"] and {"evidence_sha256", "commands_sha256"} <= row.keys(),
                     "paired committed row is malformed")
            _require(_same(record, self._make_record(previous, binding, row)),
                     "paired checkpoint chain, order, lane or goal digest differs")
            self._validate_completed_row(binding, row, replay=False)
            total += len(raw)
            _require(total <= cp.MAX_CHECKPOINT_BYTES, "paired checkpoint total byte bound exceeded")
            previous = record["record_sha256"]
            self.rows.append(row)
            self.hashes.append(hashlib.sha256(raw).hexdigest())
        _require(_same(self.head, self._head(count, previous, total, inflight)), "paired HEAD count/bytes/chain differs")
        self._cohort_bounds()
        self.assert_unchanged()
        _api()._refresh(self.plan)
        self.assert_unchanged()
        if not self.replay_proofs:
            self.progress.emit("paired-checkpoint-metadata-validated", completed=count, total=TOTAL_GOALS,
                               proof_replay_performed=False, clean_boundary=inflight is None)
            return
        for index, row in enumerate(self.rows):
            binding = self._goal_binding(index)
            checked = self._validate_completed_row(binding, row, replay=True)
            if checked is not None:
                self.replayed.append(checked)
            self.progress.emit("paired-checkpoint-row-verified", completed=index + 1, total=TOTAL_GOALS,
                               lane=binding["lane"], goal=binding["goal"], kernel_checked=row["kernel_checked"])

    def receipt(self, *, status):
        result = super().receipt(status=status)
        replayed = self.verify_only and self.replay_proofs
        all_present = len(self.rows) == TOTAL_GOALS
        if self.verify_only and not self.replay_proofs:
            # Even a caller-supplied optimistic label cannot turn metadata
            # admission into fresh native proof verification.
            result["status"] = ("complete-checkpoint-metadata-validated" if all_present
                                else "interrupted-prefix-metadata-validated" if self.head["inflight"] is not None
                                else "clean-prefix-metadata-validated")
            result["complete_comparison"] = False
        return {**result, "inflight": self.head["inflight"],
                "interrupted_model_generate_calls": None if self.head["inflight"] is not None else 0,
                "inflight_model_generate_calls_known": self.head["inflight"] is None,
                "inference_resume_allowed": False, "checkpoint_files_modified": not self.verify_only,
                "proof_replay_performed": replayed, "committed_prefix_verified": replayed,
                "all_goal_records_present": all_present, "verification_complete": replayed and all_present,
                "training_origin_sha256": self.origins["origin_sha256"],
                "source_coverage": self.header["plan"].get("source_coverage", "exact source inventory declared by the paired plan"),
                "resource_measurements": "per-goal elapsed wall/CPU; cumulative process peak RSS; recorded CUDA peaks; not attestation"}


def verify_paired_checkpoint(plan, path, *, progress=None, replay_proofs=True):
    """Read-only verification; explicit metadata-only admission is not proof replay.

    A no-descendant metadata worker may set ``replay_proofs=False``. Its parent
    must still independently replay every positive in fresh bounded workers
    and recheck all source/record bytes before claiming complete verification.
    """
    _model_free()
    with PairedCheckpointStore(path, plan, plan.origin, progress=progress, verify_only=True,
                               replay_proofs=replay_proofs) as store:
        return store.receipt(status="complete-checkpoint-verified" if len(store.rows) == TOTAL_GOALS
                             else "interrupted-prefix-verified" if store.head["inflight"] is not None
                             else "clean-prefix-verified")
