"""Transactional A3.2 preview for one live Peano/Vampire attempt.

This module is deliberately separate from H0's frozen ``Dispatch`` protocol.
It gives a host application a small preview API which owns translation,
process containment, reconstruction, and transaction commit.  The copied
Vampire executable is the sole child process: there is no Python/JSON broker.

Vampire output has no proof authority.  An SZS theorem status merely permits
the tiny reconstruction class in :mod:`vampire_adapter` to propose ordinary
Peano Lab commands.  Those commands run on an immutable temporary owner.  A
closed successor is accepted only after the macro runner's same fresh replay
against the owner-held original theorem passes the independent kernel.

The first preview intentionally rejects focused goals with local variables or
hypotheses.  Its premises are an explicit, ordered subset of PA axioms and
public library theorems visible through the owner's capability environment.
"""

from __future__ import annotations

from base64 import b64decode, b64encode
from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import resource
import signal
import stat
import subprocess
import sys
import tempfile
import time
from typing import TypeAlias

from peano_lab.engine.state import apply_formula_subst, proof_metrics
from peano_lab.kernel.checker import axiom_formula, check
from peano_lab.kernel.formulas import pretty_formula
from peano_lab.kernel.proofs import Proof
from peano_lab.library.theorems import get as get_theorem
from peano_lab.ui.prove import run_surface

from .macro_runner import (
    MAX_OWNER_REPLAY_STEPS,
    MacroOwner,
    _error_text,
    _fresh_final_replay,
    _kill_process_group,
    _process_group_usage,
    _state_record,
    _state_summary,
    _validate_owner,
)
from .profile import canonical_profile_theorem
from .vampire_adapter import (
    MAX_PREMISES,
    MAX_VAMPIRE_EXECUTABLE_BYTES,
    MAX_VAMPIRE_OUTPUT_BYTES,
    MAX_VAMPIRE_WALL_TIME_MS,
    VAMPIRE_RECONSTRUCTION_CLASS,
    VAMPIRE_TRANSLATION_CLASS,
    VampireEvidence,
    VampirePremise,
    VampireProblem,
    emit_tptp_problem,
    parse_vampire_output,
    reconstruct_public_commands,
)


VAMPIRE_LIVE_FORMAT = "peano-hydra-vampire-live-preview"
VAMPIRE_LIVE_VERSION = 1
VAMPIRE_LIVE_MODE = ("--mode", "vampire")
MAX_VAMPIRE_LIVE_TRACE_BYTES = 16 * 1024 * 1024
MAX_VAMPIRE_LIVE_ARGUMENTS = 128
MAX_VAMPIRE_LIVE_ARGUMENT_BYTES = 64 * 1024
MAX_VAMPIRE_LIVE_MEMORY_BYTES = 64 * 1024 * 1024 * 1024
MAX_VAMPIRE_LIVE_CPU_SECONDS = 600
MAX_VAMPIRE_LIVE_COMMANDS = 16

_SHA256 = re.compile(r"[0-9a-f]{64}\Z")
_PREMISE_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_']{0,127}\Z")
_FAILURE_PHASES = frozenset(
    {"owner", "input", "goal", "premises", "problem", "process", "reconstruction", "kernel"}
)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@dataclass(frozen=True, slots=True)
class VampireLiveBounds:
    """Pinned host bounds for exactly one solver invocation."""

    max_wall_time_ms: int
    max_cpu_time_seconds: int
    max_memory_bytes: int
    max_output_bytes: int
    max_commands: int = MAX_VAMPIRE_LIVE_COMMANDS
    max_processes: int = 1

    def __post_init__(self) -> None:
        if type(self.max_wall_time_ms) is not int or not (
            1 <= self.max_wall_time_ms <= MAX_VAMPIRE_WALL_TIME_MS
        ):
            raise ValueError("Vampire live wall-time bound is outside its profile")
        if type(self.max_cpu_time_seconds) is not int or not (
            1 <= self.max_cpu_time_seconds <= MAX_VAMPIRE_LIVE_CPU_SECONDS
        ):
            raise ValueError("Vampire live CPU bound is outside its profile")
        if type(self.max_memory_bytes) is not int or not (
            1 <= self.max_memory_bytes <= MAX_VAMPIRE_LIVE_MEMORY_BYTES
        ):
            raise ValueError("Vampire live memory bound is outside its profile")
        if type(self.max_output_bytes) is not int or not (
            1 <= self.max_output_bytes <= MAX_VAMPIRE_OUTPUT_BYTES
        ):
            raise ValueError("Vampire live output bound is outside its profile")
        if type(self.max_commands) is not int or not (
            1 <= self.max_commands <= MAX_VAMPIRE_LIVE_COMMANDS
        ):
            raise ValueError("Vampire live command bound is outside its profile")
        if type(self.max_processes) is not int or self.max_processes != 1:
            raise ValueError("Vampire live process bound must be exactly one")

    def to_dict(self) -> dict[str, int]:
        return {
            "max_commands": self.max_commands,
            "max_cpu_time_seconds": self.max_cpu_time_seconds,
            "max_memory_bytes": self.max_memory_bytes,
            "max_output_bytes": self.max_output_bytes,
            "max_processes": self.max_processes,
            "max_wall_time_ms": self.max_wall_time_ms,
        }


@dataclass(frozen=True, slots=True)
class VampireLiveSolver:
    """Trusted host-owned executable identity and resource contract.

    This object is configuration authority, not a proposal format.  A trusted
    host creates it from deployment configuration; model output, browser
    payloads, and solver output must never be deserialized into this type.
    ``host_owned_trusted_configuration`` is an explicit fail-closed assertion
    of that API boundary, not a credential which can make untrusted input safe.
    """

    executable: str
    executable_sha256: str
    arguments: tuple[str, ...]
    bounds: VampireLiveBounds
    host_owned_trusted_configuration: bool = True

    def __post_init__(self) -> None:
        if type(self.executable) is not str or not self.executable:
            raise TypeError("Vampire live executable must be non-empty text")
        if not Path(self.executable).is_absolute():
            raise ValueError("Vampire live executable path must be absolute")
        if (
            type(self.executable_sha256) is not str
            or _SHA256.fullmatch(self.executable_sha256) is None
        ):
            raise ValueError("Vampire live executable SHA-256 is malformed")
        if type(self.arguments) is not tuple or not all(
            type(argument) is str for argument in self.arguments
        ):
            raise TypeError("Vampire live arguments must be an exact text tuple")
        if not 2 <= len(self.arguments) <= MAX_VAMPIRE_LIVE_ARGUMENTS:
            raise ValueError("Vampire live arguments exceed their count bound")
        encoded_bytes = 0
        for argument in self.arguments:
            if not argument or "\x00" in argument:
                raise ValueError("Vampire live arguments must be non-empty NUL-free text")
            encoded_bytes += len(argument.encode("utf-8"))
        if encoded_bytes > MAX_VAMPIRE_LIVE_ARGUMENT_BYTES:
            raise ValueError("Vampire live arguments exceed their byte bound")
        if self.arguments[:2] != VAMPIRE_LIVE_MODE:
            raise ValueError("Vampire live requires the standard '--mode vampire' prefix")
        if "--mode" in self.arguments[2:] or any(
            argument.startswith("--mode=") for argument in self.arguments
        ):
            raise ValueError("Vampire live mode cannot be overridden")
        forbidden = tuple(
            argument
            for argument in self.arguments
            if any(token in argument.casefold() for token in ("portfolio", "casc", "schedule"))
        )
        if forbidden:
            raise ValueError("Vampire live portfolio/schedule arguments are forbidden")
        if type(self.bounds) is not VampireLiveBounds:
            raise TypeError("Vampire live solver needs exact VampireLiveBounds")
        VampireLiveBounds(**self.bounds.to_dict())
        if self.host_owned_trusted_configuration is not True:
            raise ValueError(
                "VampireLiveSolver must be trusted host-owned configuration; "
                "model/browser-supplied configuration is forbidden"
            )

    def to_dict(self) -> dict[str, object]:
        return {
            "arguments": list(self.arguments),
            "browser_supplied": False,
            "bounds": self.bounds.to_dict(),
            "executable": self.executable,
            "executable_sha256": self.executable_sha256,
            "host_owned_trusted_configuration": True,
            "mode": "vampire",
            "model_supplied": False,
            "portfolio": False,
        }


def _exact_record(
    label: str,
    value: object,
    fields: frozenset[str],
) -> dict[str, object]:
    if type(value) is not dict or set(value) != fields:
        raise ValueError(f"{label} has the wrong exact fields")
    return value


def _exact_int(label: str, value: object, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"{label} must be an exact integer >= {minimum}")
    return value


def _require_digest(label: str, value: object) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise ValueError(f"{label} is not a SHA-256 digest")
    return value


def _decode_base64(label: str, value: object) -> bytes:
    if type(value) is not str:
        raise ValueError(f"{label} must be base64 text")
    try:
        raw = b64decode(value.encode("ascii"), validate=True)
    except (UnicodeEncodeError, ValueError) as exc:
        raise ValueError(f"{label} is not canonical base64: {exc}") from None
    if b64encode(raw).decode("ascii") != value:
        raise ValueError(f"{label} is not canonical base64")
    return raw


def _domain_json_sha256(domain: str, value: object) -> str:
    return _sha256(domain.encode("ascii") + b"\x00" + _canonical_json(value).encode("utf-8"))


def _validate_state_record(label: str, value: object) -> dict[str, object]:
    record = _exact_record(
        label,
        value,
        frozenset(
            {"closed", "goals", "goals_sha256", "history", "replay", "state_sha256"}
        ),
    )
    if type(record["closed"]) is not bool:
        raise ValueError(f"{label} closed flag must be Boolean")
    goals = record["goals"]
    if type(goals) is not list or not all(type(goal) is str for goal in goals):
        raise ValueError(f"{label} goals must be an exact text list")
    if record["closed"] is (len(goals) != 0):
        raise ValueError(f"{label} closed flag disagrees with its goals")
    from training.peano_policy.search import state_sha256 as goal_state_sha256

    if record["goals_sha256"] != goal_state_sha256(tuple(goals)):
        raise ValueError(f"{label} goal digest is inconsistent")
    history = record["history"]
    if type(history) is not list:
        raise ValueError(f"{label} history must be an exact list")
    for entry in history:
        item = _exact_record(
            f"{label} history entry",
            entry,
            frozenset({"args", "tactic"}),
        )
        if not all(type(item[field]) is str for field in ("args", "tactic")):
            raise ValueError(f"{label} history entry must contain text")
    replay = record["replay"]
    if type(replay) is not list or len(replay) != len(history):
        raise ValueError(f"{label} replay must align with history")
    for entry in replay:
        item = _exact_record(
            f"{label} replay entry",
            entry,
            frozenset({"classical", "command"}),
        )
        if type(item["command"]) is not str or not item["command"]:
            raise ValueError(f"{label} replay command must be non-empty text")
        if item["classical"] is not False:
            raise ValueError(f"{label} replay cannot carry classical authority")
    payload = {
        "closed": record["closed"],
        "goals": goals,
        "goals_sha256": record["goals_sha256"],
        "history": history,
        "replay": replay,
    }
    if record["state_sha256"] != _domain_json_sha256(
        "peano-hydra-macro-state-v1", payload
    ):
        raise ValueError(f"{label} state digest is inconsistent")
    return record


def _validate_solver_record(value: object) -> tuple[dict[str, object], VampireLiveBounds]:
    solver = _exact_record(
        "Vampire live trace solver",
        value,
        frozenset(
            {
                "arguments",
                "browser_supplied",
                "bounds",
                "executable",
                "executable_sha256",
                "host_owned_trusted_configuration",
                "mode",
                "model_supplied",
                "portfolio",
            }
        ),
    )
    if (
        solver["host_owned_trusted_configuration"] is not True
        or solver["browser_supplied"] is not False
        or solver["model_supplied"] is not False
    ):
        raise ValueError("Vampire live trace solver is not trusted host configuration")
    if solver["mode"] != "vampire" or solver["portfolio"] is not False:
        raise ValueError("Vampire live trace solver changed its fixed mode")
    if type(solver["executable"]) is not str or not Path(solver["executable"]).is_absolute():
        raise ValueError("Vampire live trace executable path is not absolute")
    _require_digest("Vampire live trace configured executable", solver["executable_sha256"])
    arguments = solver["arguments"]
    if type(arguments) is not list or not all(type(item) is str for item in arguments):
        raise ValueError("Vampire live trace arguments must be an exact text list")
    if (
        not 2 <= len(arguments) <= MAX_VAMPIRE_LIVE_ARGUMENTS
        or any(not argument or "\x00" in argument for argument in arguments)
        or sum(len(argument.encode("utf-8")) for argument in arguments)
        > MAX_VAMPIRE_LIVE_ARGUMENT_BYTES
    ):
        raise ValueError("Vampire live trace arguments exceed their fixed bounds")
    if tuple(arguments[:2]) != VAMPIRE_LIVE_MODE:
        raise ValueError("Vampire live trace arguments changed fixed mode")
    if "--mode" in arguments[2:] or any(
        argument.startswith("--mode=")
        or any(token in argument.casefold() for token in ("portfolio", "casc", "schedule"))
        for argument in arguments
    ):
        raise ValueError("Vampire live trace arguments contain a forbidden mode")
    bounds_record = _exact_record(
        "Vampire live trace bounds",
        solver["bounds"],
        frozenset(
            {
                "max_commands",
                "max_cpu_time_seconds",
                "max_memory_bytes",
                "max_output_bytes",
                "max_processes",
                "max_wall_time_ms",
            }
        ),
    )
    try:
        bounds = VampireLiveBounds(**bounds_record)  # type: ignore[arg-type]
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Vampire live trace bounds are invalid: {exc}") from None
    return solver, bounds


def _validate_problem_record(
    value: object,
    names: list[object],
    resolved: list[object],
) -> tuple[dict[str, object], VampireProblem] | None:
    if value is None:
        return None
    problem = _exact_record(
        "Vampire live trace problem",
        value,
        frozenset(
            {
                "bytes",
                "goal",
                "premises",
                "requested_premises",
                "sha256",
                "symbol_map",
                "tptp_base64",
                "translation_class",
            }
        ),
    )
    raw = _decode_base64("Vampire live TPTP", problem["tptp_base64"])
    if _exact_int("Vampire live TPTP bytes", problem["bytes"], minimum=1) != len(raw):
        raise ValueError("Vampire live TPTP byte accounting is inconsistent")
    if _require_digest("Vampire live TPTP", problem["sha256"]) != _sha256(raw):
        raise ValueError("Vampire live TPTP digest is inconsistent")
    if not raw.endswith(b"\n"):
        raise ValueError("Vampire live TPTP bytes are not LF-terminated")
    if problem["translation_class"] != VAMPIRE_TRANSLATION_CLASS:
        raise ValueError("Vampire live TPTP translation class changed")
    if type(problem["goal"]) is not str or not problem["goal"]:
        raise ValueError("Vampire live problem goal is malformed")
    requested = problem["requested_premises"]
    premises = problem["premises"]
    if requested != names or premises != resolved:
        raise ValueError("Vampire live problem differs from explicit resolved premises")
    if type(premises) is not list:
        raise ValueError("Vampire live problem premises must be an exact list")
    premise_names: list[str] = []
    checked_premises: list[VampirePremise] = []
    for entry in premises:
        item = _exact_record(
            "Vampire live problem premise",
            entry,
            frozenset({"formula", "kind", "name"}),
        )
        if (
            type(item["name"]) is not str
            or _PREMISE_NAME.fullmatch(item["name"]) is None
            or item["kind"] not in {"pa-axiom", "public-theorem"}
            or type(item["formula"]) is not str
            or not item["formula"]
        ):
            raise ValueError("Vampire live problem premise is malformed")
        premise_names.append(item["name"])
        checked_premises.append(
            VampirePremise(item["name"], item["kind"], item["formula"])  # type: ignore[arg-type]
        )
    if premise_names != names or len(premise_names) != len(set(premise_names)):
        raise ValueError("Vampire live problem premise order/uniqueness changed")
    symbol_map = problem["symbol_map"]
    if type(symbol_map) is not list or not all(
        type(entry) is list
        and len(entry) == 2
        and all(type(part) is str and bool(part) for part in entry)
        for entry in symbol_map
    ):
        raise ValueError("Vampire live problem symbol map is malformed")
    expected = emit_tptp_problem(
        problem["goal"],  # type: ignore[arg-type]
        tuple(checked_premises),
        requested_premises=tuple(premise_names),
    )
    if (
        raw != expected.tptp_bytes
        or problem["symbol_map"] != [list(item) for item in expected.symbol_map]
        or problem["sha256"] != expected.sha256
    ):
        raise ValueError("Vampire live TPTP bytes do not reconstruct from goal/premises")
    return problem, expected


def _validate_process_record(
    value: object,
    solver: dict[str, object],
    bounds: VampireLiveBounds,
) -> dict[str, object] | None:
    if value is None:
        return None
    process = _exact_record(
        "Vampire live trace process",
        value,
        frozenset(
            {
                "arguments",
                "containment",
                "copied_executable_sha256",
                "cpu_limited",
                "exit_code",
                "leader_observation_samples",
                "leader_observed",
                "max_observed_leader_rss_bytes",
                "memory_exceeded",
                "observed_output_bytes",
                "output_limited",
                "raw_output_base64",
                "raw_output_sha256",
                "retained_output_bytes",
                "solver_status",
                "szs_parse_error",
                "szs_statuses",
                "timed_out",
                "wall_time_ms",
            }
        ),
    )
    expected_arguments = [*solver["arguments"], "$CWD/problem.p"]  # type: ignore[misc]
    if process["arguments"] != expected_arguments:
        raise ValueError("Vampire live invoked arguments differ from trusted configuration")
    containment = _exact_record(
        "Vampire live process containment",
        process["containment"],
        frozenset(
            {
                "campaign_host_eligible",
                "close_fds",
                "cwd",
                "environment",
                "memory_enforcement",
                "output_enforcement",
                "process_enforcement",
                "process_observation",
                "session",
                "stderr",
                "stdin",
            }
        ),
    )
    if (
        containment["close_fds"] is not True
        or containment["cwd"] != "fresh-mode-0700-temporary-directory"
        or containment["output_enforcement"] != "rlimit-fsize-and-parent-file-observation"
        or containment["process_enforcement"] != "rlimit-nproc-one"
        or containment["process_observation"] != "leader-liveness-only-no-group-enumeration"
        or containment["session"] != "new-process-group"
        or containment["stderr"] != "merged-into-bounded-stdout"
        or containment["stdin"] != "devnull"
    ):
        raise ValueError("Vampire live process containment identity changed")
    expected_environment = {"HOME": "$CWD", "LANG": "C", "LC_ALL": "C", "TMPDIR": "$CWD"}
    if containment["environment"] != expected_environment:
        raise ValueError("Vampire live process environment containment changed")
    memory_mode = containment["memory_enforcement"]
    eligible = containment["campaign_host_eligible"]
    if (memory_mode, eligible) not in {
        ("linux-hard-rlimit-as+data-and-sampled-leader-rss", True),
        ("darwin-sampled-leader-rss-preview-not-campaign-eligible", False),
    }:
        raise ValueError("Vampire live memory-containment claim is inconsistent")
    copied = process["copied_executable_sha256"]
    if copied is not None:
        if _require_digest("Vampire live copied executable", copied) != solver["executable_sha256"]:
            raise ValueError("Vampire live copied executable differs from configured identity")
    raw = _decode_base64("Vampire live raw output", process["raw_output_base64"])
    retained = _exact_int(
        "Vampire live retained output bytes", process["retained_output_bytes"]
    )
    observed = _exact_int(
        "Vampire live observed output bytes", process["observed_output_bytes"]
    )
    if retained != len(raw) or observed < retained:
        raise ValueError("Vampire live output accounting is inconsistent")
    if retained > bounds.max_output_bytes:
        raise ValueError("Vampire live retained output exceeds its bound")
    if _require_digest("Vampire live raw output", process["raw_output_sha256"]) != _sha256(raw):
        raise ValueError("Vampire live raw-output digest is inconsistent")
    for flag in (
        "cpu_limited",
        "leader_observed",
        "memory_exceeded",
        "output_limited",
        "timed_out",
    ):
        if type(process[flag]) is not bool:
            raise ValueError(f"Vampire live process {flag} must be Boolean")
    samples = _exact_int(
        "Vampire live leader observation samples", process["leader_observation_samples"]
    )
    if process["leader_observed"] and samples < 1:
        raise ValueError("Vampire live leader observation accounting is inconsistent")
    rss = _exact_int(
        "Vampire live maximum observed leader RSS",
        process["max_observed_leader_rss_bytes"],
    )
    if process["memory_exceeded"] is not (rss > bounds.max_memory_bytes):
        raise ValueError("Vampire live memory-limit accounting is inconsistent")
    if process["output_limited"] is not (observed >= bounds.max_output_bytes):
        raise ValueError("Vampire live output-limit accounting is inconsistent")
    wall = _exact_int("Vampire live wall time", process["wall_time_ms"])
    if process["timed_out"] is not (wall > bounds.max_wall_time_ms):
        raise ValueError("Vampire live wall-time accounting is inconsistent")
    exit_code = process["exit_code"]
    if exit_code is not None and type(exit_code) is not int:
        raise ValueError("Vampire live exit code must be integer or null")
    expected_cpu = exit_code == -getattr(signal, "SIGXCPU", 24)
    if process["cpu_limited"] is not expected_cpu:
        raise ValueError("Vampire live CPU-limit accounting is inconsistent")
    parsed = parse_vampire_output(raw)
    if (
        process["szs_statuses"] != list(parsed.szs_statuses)
        or process["szs_parse_error"] != parsed.parse_error
    ):
        raise ValueError("Vampire live SZS parse evidence is inconsistent")
    expected_status = parsed.status
    if any(
        process[flag]
        for flag in ("cpu_limited", "memory_exceeded", "output_limited", "timed_out")
    ):
        expected_status = "resource-limit"
    elif exit_code not in {None, 0}:
        expected_status = "unknown"
    if process["solver_status"] not in {None, expected_status}:
        raise ValueError("Vampire live solver status is inconsistent with retained output")
    return process


def _validate_live_trace_record(record: dict[str, object]) -> None:
    solver, bounds = _validate_solver_record(record["solver"])
    before = _validate_state_record("Vampire live owner_before", record["owner_before"])
    after = _validate_state_record("Vampire live owner_after", record["owner_after"])
    premises = _exact_record(
        "Vampire live trace premises",
        record["premises"],
        frozenset({"names", "resolved"}),
    )
    names, resolved = premises["names"], premises["resolved"]
    if (
        type(names) is not list
        or not all(type(name) is str and len(name) <= 128 for name in names)
        or type(resolved) is not list
    ):
        raise ValueError("Vampire live explicit premise evidence is malformed")
    problem_pair = _validate_problem_record(record["problem"], names, resolved)
    process = _validate_process_record(record["process"], solver, bounds)
    if process is not None and problem_pair is None:
        raise ValueError("Vampire live process evidence lacks an exact problem")
    commands = _exact_record(
        "Vampire live trace commands",
        record["commands"],
        frozenset({"intermediate_states", "public_commands", "reconstruction_class"}),
    )
    if commands["reconstruction_class"] != VAMPIRE_RECONSTRUCTION_CLASS:
        raise ValueError("Vampire live reconstruction class changed")
    public = commands["public_commands"]
    intermediate = commands["intermediate_states"]
    if (
        type(public) is not list
        or not all(type(command) is str and bool(command) for command in public)
        or len(public) > bounds.max_commands
        or type(intermediate) is not list
        or len(intermediate) > len(public)
    ):
        raise ValueError("Vampire live command accounting is inconsistent")
    for index, entry in enumerate(intermediate):
        item = _exact_record(
            "Vampire live intermediate state",
            entry,
            frozenset({"command", "command_index", "state"}),
        )
        if item["command_index"] != index or item["command"] != public[index]:
            raise ValueError("Vampire live intermediate command order changed")
        summary = _exact_record(
            "Vampire live intermediate state summary",
            item["state"],
            frozenset(
                {
                    "closed",
                    "goals",
                    "goals_sha256",
                    "history_length",
                    "replay_length",
                    "summary_sha256",
                }
            ),
        )
        if type(summary["closed"]) is not bool:
            raise ValueError("Vampire live intermediate closed flag is malformed")
        summary_goals = summary["goals"]
        if type(summary_goals) is not list or not all(
            type(goal) is str for goal in summary_goals
        ):
            raise ValueError("Vampire live intermediate goals are malformed")
        if summary["closed"] is (len(summary_goals) != 0):
            raise ValueError("Vampire live intermediate closed flag is inconsistent")
        from training.peano_policy.search import state_sha256 as goal_state_sha256

        if summary["goals_sha256"] != goal_state_sha256(tuple(summary_goals)):
            raise ValueError("Vampire live intermediate goal digest is inconsistent")
        expected_length = len(before["replay"]) + index + 1  # type: ignore[arg-type]
        if (
            summary["history_length"] != expected_length
            or summary["replay_length"] != expected_length
        ):
            raise ValueError("Vampire live intermediate replay accounting is inconsistent")
        summary_payload = {
            "closed": summary["closed"],
            "goals": summary_goals,
            "goals_sha256": summary["goals_sha256"],
            "history_length": summary["history_length"],
            "replay_length": summary["replay_length"],
        }
        if summary["summary_sha256"] != _domain_json_sha256(
            "peano-hydra-macro-state-summary-v1", summary_payload
        ):
            raise ValueError("Vampire live intermediate summary digest is inconsistent")
    outcome = _exact_record(
        "Vampire live trace outcome",
        record["outcome"],
        frozenset({"error", "phase", "status"}),
    )
    status = outcome["status"]
    if status == "accepted":
        if outcome != {"error": None, "phase": None, "status": "accepted"}:
            raise ValueError("accepted Vampire live outcome is inconsistent")
        if not public or len(intermediate) != len(public):
            raise ValueError("accepted Vampire live commands lack complete state evidence")
        after_replay = after["replay"]
        if (
            type(after_replay) is not list
            or len(after_replay) != len(before["replay"]) + len(public)  # type: ignore[arg-type]
            or [entry["command"] for entry in after_replay[-len(public) :]] != public
        ):
            raise ValueError("accepted Vampire live commands differ from owner replay")
        final_summary = intermediate[-1]["state"]
        for field in ("closed", "goals", "goals_sha256"):
            if final_summary[field] != after[field]:
                raise ValueError("accepted Vampire live final state summary is inconsistent")
        if (
            final_summary["history_length"] != len(after["history"])  # type: ignore[arg-type]
            or final_summary["replay_length"] != len(after_replay)
        ):
            raise ValueError("accepted Vampire live final replay summary is inconsistent")
    elif status == "rejected":
        if (
            type(outcome["phase"]) is not str
            or outcome["phase"] not in _FAILURE_PHASES
            or type(outcome["error"]) is not str
            or not outcome["error"]
        ):
            raise ValueError("rejected Vampire live outcome is inconsistent")
        if after != before:
            raise ValueError("rejected Vampire live outcome did not roll back exactly")
    else:
        raise ValueError("Vampire live outcome status is unsupported")
    if not (
        status == "rejected" and outcome["phase"] in {"input", "premises"}
    ) and (
        not all(_PREMISE_NAME.fullmatch(name) for name in names)
        or len(names) != len(set(names))
    ):
        raise ValueError("Vampire live accepted premise names are malformed")
    if status == "accepted" or outcome["phase"] in {"reconstruction", "kernel"}:
        if problem_pair is None or process is None:
            raise ValueError("Vampire live reconstruction lacks problem/process evidence")
        if (
            process["copied_executable_sha256"] is None
            or process["exit_code"] != 0
            or any(
                process[flag]
                for flag in (
                    "cpu_limited",
                    "memory_exceeded",
                    "output_limited",
                    "timed_out",
                )
            )
            or process["solver_status"] not in {"theorem", "unsat"}
        ):
            raise ValueError("Vampire live reconstruction lacks one successful solver process")
        raw_output = _decode_base64(
            "Vampire live reconstructed output", process["raw_output_base64"]
        )
        evidence = VampireEvidence(
            raw_output=raw_output,
            status=process["solver_status"],  # type: ignore[arg-type]
            szs_statuses=tuple(process["szs_statuses"]),  # type: ignore[arg-type]
            parse_error=process["szs_parse_error"],  # type: ignore[arg-type]
            exit_code=process["exit_code"],  # type: ignore[arg-type]
            timed_out=False,
            output_limited=False,
            wall_time_ms=process["wall_time_ms"],  # type: ignore[arg-type]
            executable_sha256=solver["executable_sha256"],  # type: ignore[arg-type]
            arguments=tuple(solver["arguments"]),  # type: ignore[arg-type]
        )
        expected_public = reconstruct_public_commands(problem_pair[1], evidence)
        if public != list(expected_public):
            raise ValueError("Vampire live public commands differ from reconstruction")
    kernel = record["kernel"]
    if type(kernel) is not dict:
        raise ValueError("Vampire live kernel evidence must be an exact object")
    if kernel.get("fresh_original_goal_replay") is not True:
        raise ValueError("Vampire live kernel evidence lost fresh-replay identity")
    if status == "accepted" and after["closed"]:
        if (
            kernel.get("attempted") is not True
            or kernel.get("status") != "accepted"
            or kernel.get("fresh") is not True
            or kernel.get("kernel_accepted") is not True
            or kernel.get("error") is not None
        ):
            raise ValueError("closed Vampire live acceptance lacks kernel authority")
        _require_digest("Vampire live final certificate", kernel.get("certificate_sha256"))
        nodes = _exact_int(
            "Vampire live certificate nodes", kernel.get("certificate_nodes"), minimum=1
        )
        depth = _exact_int(
            "Vampire live certificate depth", kernel.get("certificate_depth"), minimum=1
        )
        if (
            kernel.get("certificate_nodes_observed") != nodes
            or kernel.get("certificate_depth_observed") != depth
            or kernel.get("commands")
            != [entry["command"] for entry in after["replay"]]  # type: ignore[index]
        ):
            raise ValueError("Vampire live final kernel accounting is inconsistent")
    elif status == "accepted":
        if kernel != {
            "attempted": False,
            "error": None,
            "fresh_original_goal_replay": True,
            "status": "not-required-open-successor",
        }:
            raise ValueError("open Vampire live progress carries a kernel claim")
    elif outcome["phase"] == "kernel":
        if kernel.get("attempted") is not True or kernel.get("status") != "rejected":
            raise ValueError("kernel-rejected Vampire live outcome lacks rejection evidence")
        if kernel.get("kernel_accepted") not in {None, False}:
            raise ValueError("kernel-rejected Vampire live outcome claims acceptance")
    elif kernel != {
        "attempted": False,
        "error": None,
        "fresh_original_goal_replay": True,
        "status": "not-attempted",
    }:
        raise ValueError("pre-kernel Vampire live rejection carries a kernel claim")


@dataclass(frozen=True, slots=True)
class VampireLiveTrace:
    """Canonical retained evidence for one preview attempt."""

    canonical_json: str

    @classmethod
    def from_record(cls, record: dict[str, object]) -> "VampireLiveTrace":
        return cls(_canonical_json(record))

    def __post_init__(self) -> None:
        if type(self.canonical_json) is not str:
            raise TypeError("Vampire live trace must be canonical JSON text")
        if len(self.canonical_json.encode("utf-8")) > MAX_VAMPIRE_LIVE_TRACE_BYTES:
            raise ValueError("Vampire live trace exceeds its byte bound")
        try:
            record = json.loads(self.canonical_json)
        except (json.JSONDecodeError, TypeError, ValueError) as exc:
            raise ValueError(f"Vampire live trace is not JSON: {exc}") from None
        if _canonical_json(record) != self.canonical_json:
            raise ValueError("Vampire live trace is not canonical JSON")
        if type(record) is not dict or set(record) != {
            "authority",
            "commands",
            "format",
            "kernel",
            "outcome",
            "owner_after",
            "owner_before",
            "premises",
            "problem",
            "process",
            "solver",
            "v",
        }:
            raise ValueError("Vampire live trace has the wrong top-level fields")
        if record["format"] != VAMPIRE_LIVE_FORMAT or record["v"] != VAMPIRE_LIVE_VERSION:
            raise ValueError("Vampire live trace has an unsupported identity")
        authority = record["authority"]
        if authority != {
            "candidate": True,
            "h0_dispatch_behavior_changed": False,
            "h0_dispatch_schema_changed": False,
            "kernel_replay_required_for_qed": True,
            "proof_authority": False,
            "public_commands_authority": False,
            "solver_status_authority": False,
        }:
            raise ValueError("Vampire live trace authority flags are inconsistent")
        _validate_live_trace_record(record)

    def to_dict(self) -> dict[str, object]:
        value = json.loads(self.canonical_json)
        if type(value) is not dict:  # pragma: no cover - constructor invariant
            raise RuntimeError("Vampire live trace lost its object shape")
        return value

    @property
    def sha256(self) -> str:
        return _sha256(self.canonical_json.encode("utf-8"))

    def jsonl(self) -> str:
        return self.canonical_json + "\n"


@dataclass(frozen=True, slots=True)
class VampireLiveAccepted:
    """A committed successor produced only by ordinary public commands."""

    owner: MacroOwner
    public_commands: tuple[str, ...]
    certificate: Proof | None
    trace: VampireLiveTrace
    candidate: bool = True
    proof_authority: bool = False

    def __post_init__(self) -> None:
        if type(self.owner) is not MacroOwner:
            raise TypeError("accepted Vampire preview needs an exact MacroOwner")
        if type(self.public_commands) is not tuple or not all(
            type(command) is str and bool(command) for command in self.public_commands
        ):
            raise TypeError("accepted Vampire preview commands must be an exact text tuple")
        if type(self.trace) is not VampireLiveTrace:
            raise TypeError("accepted Vampire preview needs an exact trace")
        if self.candidate is not True or self.proof_authority is not False:
            raise ValueError("Vampire preview result cannot claim proof authority")
        record = self.trace.to_dict()
        if record["outcome"] != {"error": None, "phase": None, "status": "accepted"}:
            raise ValueError("accepted Vampire preview disagrees with its trace")
        if list(self.public_commands) != record["commands"]["public_commands"]:
            raise ValueError("accepted Vampire commands disagree with their trace")
        if record["owner_after"] != _state_record(self.owner):
            raise ValueError("accepted Vampire owner differs from its retained trace")
        if self.owner.state.is_done():
            if not isinstance(self.certificate, Proof) or not check(
                (), self.certificate, self.owner.original_target
            ):
                raise ValueError("closed Vampire successor lacks a kernel certificate")
            if record["kernel"]["status"] != "accepted":
                raise ValueError("closed Vampire successor lacks accepted replay evidence")
        elif self.certificate is not None:
            raise ValueError("open Vampire successor cannot carry a final certificate")

    @property
    def closed(self) -> bool:
        """Whether the accepted successor closed the complete proof state."""

        return self.owner.state.is_done()

    @property
    def kernel_accepted(self) -> bool:
        """Whether this result carries a fresh original-goal kernel QED."""

        return (
            self.closed
            and isinstance(self.certificate, Proof)
            and self.trace.to_dict()["kernel"]["status"] == "accepted"
            and self.trace.to_dict()["kernel"]["kernel_accepted"] is True
        )

    @property
    def open_progress(self) -> bool:
        """Whether commands committed progress without claiming a QED."""

        return not self.closed


@dataclass(frozen=True, slots=True)
class VampireLiveFailure:
    """One rejected preview; ``owner`` is the caller's identical object."""

    owner: MacroOwner
    phase: str
    error: str
    trace: VampireLiveTrace
    candidate: bool = True
    proof_authority: bool = False

    def __post_init__(self) -> None:
        if type(self.owner) is not MacroOwner:
            raise TypeError("failed Vampire preview needs an exact MacroOwner")
        if type(self.phase) is not str or self.phase not in _FAILURE_PHASES:
            raise ValueError("failed Vampire preview phase is unsupported")
        if type(self.error) is not str or not self.error:
            raise ValueError("failed Vampire preview needs one final error")
        if type(self.trace) is not VampireLiveTrace:
            raise TypeError("failed Vampire preview needs an exact trace")
        if self.candidate is not True or self.proof_authority is not False:
            raise ValueError("Vampire preview failure cannot claim proof authority")
        record = self.trace.to_dict()
        if record["outcome"] != {
            "error": self.error,
            "phase": self.phase,
            "status": "rejected",
        }:
            raise ValueError("failed Vampire preview disagrees with its trace")
        if record["owner_after"] != record["owner_before"]:
            raise ValueError("failed Vampire preview trace did not roll back")
        if record["owner_before"] != _state_record(self.owner):
            raise ValueError("failed Vampire owner differs from its retained trace")


VampireLiveResult: TypeAlias = VampireLiveAccepted | VampireLiveFailure


@dataclass(frozen=True, slots=True)
class _ProcessSuccess:
    evidence: VampireEvidence
    record: dict[str, object]


class _ProcessFailure(RuntimeError):
    def __init__(self, message: str, record: dict[str, object]) -> None:
        super().__init__(message)
        self.record = record


def _authority_record() -> dict[str, bool]:
    return {
        "candidate": True,
        "h0_dispatch_behavior_changed": False,
        "h0_dispatch_schema_changed": False,
        "kernel_replay_required_for_qed": True,
        "proof_authority": False,
        "public_commands_authority": False,
        "solver_status_authority": False,
    }


def _problem_record(problem: VampireProblem) -> dict[str, object]:
    return {
        "bytes": len(problem.tptp_bytes),
        "goal": problem.goal,
        "premises": [
            {"formula": item.formula, "kind": item.kind, "name": item.name}
            for item in problem.premises
        ],
        "requested_premises": list(problem.requested_premises),
        "sha256": problem.sha256,
        "symbol_map": [list(item) for item in problem.symbol_map],
        "tptp_base64": b64encode(problem.tptp_bytes).decode("ascii"),
        "translation_class": problem.translation_class,
    }


def _empty_process_record(solver: VampireLiveSolver) -> dict[str, object]:
    return {
        "arguments": [*solver.arguments, "$CWD/problem.p"],
        "containment": {
            "campaign_host_eligible": sys.platform.startswith("linux"),
            "close_fds": True,
            "cwd": "fresh-mode-0700-temporary-directory",
            "environment": {
                "HOME": "$CWD",
                "LANG": "C",
                "LC_ALL": "C",
                "TMPDIR": "$CWD",
            },
            "memory_enforcement": (
                "linux-hard-rlimit-as+data-and-sampled-leader-rss"
                if sys.platform.startswith("linux")
                else "darwin-sampled-leader-rss-preview-not-campaign-eligible"
            ),
            "output_enforcement": "rlimit-fsize-and-parent-file-observation",
            "process_enforcement": "rlimit-nproc-one",
            "process_observation": "leader-liveness-only-no-group-enumeration",
            "session": "new-process-group",
            "stderr": "merged-into-bounded-stdout",
            "stdin": "devnull",
        },
        "copied_executable_sha256": None,
        "cpu_limited": False,
        "exit_code": None,
        "leader_observation_samples": 0,
        "leader_observed": False,
        "max_observed_leader_rss_bytes": 0,
        "memory_exceeded": False,
        "observed_output_bytes": 0,
        "output_limited": False,
        "raw_output_base64": "",
        "raw_output_sha256": _sha256(b""),
        "retained_output_bytes": 0,
        "solver_status": None,
        "szs_parse_error": None,
        "szs_statuses": [],
        "timed_out": False,
        "wall_time_ms": 0,
    }


def _resolve_premises(
    owner: MacroOwner,
    premise_names: tuple[str, ...],
) -> tuple[VampirePremise, ...]:
    if type(premise_names) is not tuple or not all(
        type(name) is str and _PREMISE_NAME.fullmatch(name) is not None
        for name in premise_names
    ):
        raise ValueError("Vampire live premise names must be one exact identifier tuple")
    if len(premise_names) > MAX_PREMISES:
        raise ValueError("Vampire live premise list exceeds its count bound")
    if len(premise_names) != len(set(premise_names)):
        raise ValueError("Vampire live premise names must be unique")
    result: list[VampirePremise] = []
    for name in premise_names:
        axiom = axiom_formula(name)
        if axiom is not None:
            result.append(VampirePremise(name, "pa-axiom", pretty_formula(axiom, [])))
            continue
        theorem = get_theorem(name)
        if theorem is None or theorem.name != name:
            raise ValueError(f"Vampire live premise {name!r} is unavailable")
        allowed = owner.capabilities.allowed_theorems
        if allowed is not None and name not in allowed:
            raise ValueError(
                f"Vampire live premise {name!r} is masked by capability "
                f"environment {owner.capabilities.label!r}"
            )
        result.append(
            VampirePremise(
                name,
                "public-theorem",
                canonical_profile_theorem(theorem.statement),
            )
        )
    return tuple(result)


def _copy_pinned_executable(
    source_name: str,
    destination: Path,
    *,
    expected_sha256: str,
) -> str:
    try:
        source = Path(source_name).resolve(strict=True)
        with source.open("rb") as input_file:
            metadata = os.fstat(input_file.fileno())
            if (
                not stat.S_ISREG(metadata.st_mode)
                or not 1 <= metadata.st_size <= MAX_VAMPIRE_EXECUTABLE_BYTES
                or not os.access(source, os.X_OK)
            ):
                raise ValueError(
                    "Vampire live executable must be one bounded executable regular file"
                )
            digest = hashlib.sha256()
            written = 0
            with destination.open("wb") as output_file:
                while chunk := input_file.read(1024 * 1024):
                    digest.update(chunk)
                    output_file.write(chunk)
                    written += len(chunk)
                    if written > MAX_VAMPIRE_EXECUTABLE_BYTES:
                        raise ValueError("Vampire live executable changed beyond its size bound")
    except (OSError, ValueError) as exc:
        raise ValueError(f"cannot copy pinned Vampire executable: {_error_text(exc)}") from None
    observed = digest.hexdigest()
    if observed != expected_sha256:
        raise ValueError("Vampire live executable identity mismatch")
    destination.chmod(0o500)
    copied = hashlib.sha256(destination.read_bytes()).hexdigest()
    if copied != expected_sha256:
        raise ValueError("copied Vampire live executable identity mismatch")
    return copied


def _preexec(bounds: VampireLiveBounds) -> None:
    """Install fixed POSIX ceilings immediately before the sole child exec."""

    os.umask(0o077)
    resource.setrlimit(
        resource.RLIMIT_CPU,
        (bounds.max_cpu_time_seconds, bounds.max_cpu_time_seconds),
    )
    if sys.platform.startswith("linux"):
        for name in ("RLIMIT_AS", "RLIMIT_DATA"):
            limit = getattr(resource, name, None)
            if limit is not None:
                resource.setrlimit(limit, (bounds.max_memory_bytes,) * 2)
    resource.setrlimit(resource.RLIMIT_FSIZE, (bounds.max_output_bytes,) * 2)
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    nofile = getattr(resource, "RLIMIT_NOFILE", None)
    if nofile is not None:
        resource.setrlimit(nofile, (64, 64))
    nproc = getattr(resource, "RLIMIT_NPROC", None)
    if nproc is None:
        raise RuntimeError("this host cannot enforce the one-process Vampire bound")
    resource.setrlimit(nproc, (1, 1))


def _invoke_vampire(
    solver: VampireLiveSolver,
    problem: VampireProblem,
) -> _ProcessSuccess:
    """Run the copied Vampire binary itself as the sole bounded child."""

    record = _empty_process_record(solver)
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        raise _ProcessFailure(
            "Vampire live refuses privileged execution because RLIMIT_NPROC "
            "does not enforce the one-process bound for uid 0",
            record,
        )
    process: subprocess.Popen[bytes] | None = None
    raw = b""
    started = time.monotonic()
    timed_out = False
    memory_exceeded = False
    output_limited = False
    max_rss = 0
    leader_observation_samples = 0
    leader_observed = False
    observed_output_size = 0
    try:
        with tempfile.TemporaryDirectory(prefix="peano-hydra-vampire-live-") as directory:
            root = Path(directory)
            root.chmod(0o700)
            executable = root / "vampire"
            copied_sha256 = _copy_pinned_executable(
                solver.executable,
                executable,
                expected_sha256=solver.executable_sha256,
            )
            record["copied_executable_sha256"] = copied_sha256
            problem_path = root / "problem.p"
            problem_path.write_bytes(problem.tptp_bytes)
            problem_path.chmod(0o400)
            output_path = root / "vampire.out"
            environment = {
                "HOME": str(root),
                "LANG": "C",
                "LC_ALL": "C",
                "TMPDIR": str(root),
            }
            with output_path.open("w+b") as output:
                try:
                    process = subprocess.Popen(
                        [str(executable), *solver.arguments, str(problem_path)],
                        stdin=subprocess.DEVNULL,
                        stdout=output,
                        stderr=subprocess.STDOUT,
                        cwd=root,
                        env=environment,
                        close_fds=True,
                        start_new_session=True,
                        preexec_fn=lambda: _preexec(solver.bounds),
                    )
                except (OSError, subprocess.SubprocessError) as exc:
                    raise _ProcessFailure(
                        f"cannot launch bounded Vampire process: {_error_text(exc)}",
                        record,
                    ) from None
                while True:
                    try:
                        observed_leader, observed_rss = _process_group_usage(process.pid)
                    except Exception as exc:
                        _kill_process_group(process)
                        process.wait()
                        raise _ProcessFailure(
                            f"cannot monitor bounded Vampire process: {_error_text(exc)}",
                            record,
                        ) from None
                    if observed_leader not in {0, 1}:
                        _kill_process_group(process)
                        process.wait()
                        raise _ProcessFailure(
                            "Vampire leader monitor returned an invalid liveness count",
                            record,
                        )
                    leader_observation_samples += 1
                    leader_observed = leader_observed or observed_leader == 1
                    max_rss = max(max_rss, observed_rss)
                    elapsed_ms = math.ceil((time.monotonic() - started) * 1_000)
                    try:
                        observed_output = output_path.stat().st_size
                    except OSError as exc:
                        _kill_process_group(process)
                        process.wait()
                        raise _ProcessFailure(
                            f"cannot inspect bounded Vampire output: {_error_text(exc)}",
                            record,
                        ) from None
                    timed_out = elapsed_ms > solver.bounds.max_wall_time_ms
                    memory_exceeded = observed_rss > solver.bounds.max_memory_bytes
                    output_limited = observed_output >= solver.bounds.max_output_bytes
                    if timed_out or memory_exceeded or output_limited:
                        _kill_process_group(process)
                        process.wait()
                        break
                    if process.poll() is not None:
                        break
                    time.sleep(0.01)
                wall_time_ms = math.ceil((time.monotonic() - started) * 1_000)
                timed_out = timed_out or wall_time_ms > solver.bounds.max_wall_time_ms
                output.flush()
                size = output_path.stat().st_size
                observed_output_size = size
                output.seek(0)
                raw = output.read(solver.bounds.max_output_bytes + 1)
                output_limited = output_limited or size >= solver.bounds.max_output_bytes
                if len(raw) > solver.bounds.max_output_bytes:
                    raw = raw[: solver.bounds.max_output_bytes]
                exit_code = process.returncode
    except _ProcessFailure:
        raise
    except Exception as exc:
        if process is not None and process.poll() is None:
            _kill_process_group(process)
            process.wait()
        raise _ProcessFailure(
            f"bounded Vampire host failed closed: {_error_text(exc)}", record
        ) from None

    wall_time_ms = max(0, math.ceil((time.monotonic() - started) * 1_000))
    timed_out = timed_out or wall_time_ms > solver.bounds.max_wall_time_ms
    parsed = parse_vampire_output(raw)
    cpu_limited = exit_code == -getattr(signal, "SIGXCPU", 24)
    status = parsed.status
    if timed_out or memory_exceeded or output_limited or cpu_limited:
        status = "resource-limit"
    elif exit_code != 0:
        status = "unknown"
    evidence = VampireEvidence(
        raw_output=raw,
        status=status,
        szs_statuses=parsed.szs_statuses,
        parse_error=parsed.parse_error,
        exit_code=exit_code,
        timed_out=timed_out,
        output_limited=output_limited,
        wall_time_ms=wall_time_ms,
        executable_sha256=solver.executable_sha256,
        arguments=solver.arguments,
    )
    record.update(
        {
            "cpu_limited": cpu_limited,
            "exit_code": exit_code,
            "leader_observation_samples": leader_observation_samples,
            "leader_observed": leader_observed,
            "max_observed_leader_rss_bytes": max_rss,
            "memory_exceeded": memory_exceeded,
            "observed_output_bytes": observed_output_size,
            "output_limited": output_limited,
            "raw_output_base64": b64encode(raw).decode("ascii"),
            "raw_output_sha256": _sha256(raw),
            "retained_output_bytes": len(raw),
            "solver_status": evidence.status,
            "szs_parse_error": evidence.parse_error,
            "szs_statuses": list(evidence.szs_statuses),
            "timed_out": timed_out,
            "wall_time_ms": wall_time_ms,
        }
    )
    if timed_out:
        raise _ProcessFailure("Vampire exceeded its wall-time bound", record)
    if cpu_limited:
        raise _ProcessFailure("Vampire exceeded its CPU-time bound", record)
    if memory_exceeded:
        raise _ProcessFailure("Vampire exceeded its memory bound", record)
    if output_limited:
        raise _ProcessFailure("Vampire exceeded its output bound", record)
    if exit_code != 0:
        raise _ProcessFailure(
            f"Vampire exited unsuccessfully with status {exit_code}", record
        )
    return _ProcessSuccess(evidence, record)


def run_vampire_live(
    owner: MacroOwner,
    premise_names: tuple[str, ...],
    solver: VampireLiveSolver,
) -> VampireLiveResult:
    """Attempt one transactional live Vampire reconstruction.

    Operational rejection is data, not an exception.  Every
    :class:`VampireLiveFailure` retains the exact ``owner`` object supplied by
    the caller.  ``solver`` is trusted host-owned deployment configuration;
    callers must never populate it from model, browser, or solver bytes.
    Constructor/type violations for the three API values remain ordinary
    programmer errors.
    """

    if type(owner) is not MacroOwner:
        raise TypeError("run_vampire_live needs an exact MacroOwner")
    if type(solver) is not VampireLiveSolver:
        raise TypeError("run_vampire_live needs an exact VampireLiveSolver")
    VampireLiveSolver(
        solver.executable,
        solver.executable_sha256,
        solver.arguments,
        solver.bounds,
        solver.host_owned_trusted_configuration,
    )
    if type(premise_names) is not tuple:
        raise TypeError("run_vampire_live premise names must be an exact tuple")

    before = _state_record(owner)
    premises_record: list[dict[str, str]] = []
    problem_record: dict[str, object] | None = None
    process_record: dict[str, object] | None = None
    public_commands: tuple[str, ...] = ()
    intermediates: list[dict[str, object]] = []
    kernel_record: dict[str, object] = {
        "attempted": False,
        "error": None,
        "fresh_original_goal_replay": True,
        "status": "not-attempted",
    }

    def trace_record(
        *,
        after: dict[str, object],
        status: str,
        phase: str | None,
        error: str | None,
    ) -> VampireLiveTrace:
        return VampireLiveTrace.from_record(
            {
                "authority": _authority_record(),
                "commands": {
                    "intermediate_states": intermediates,
                    "public_commands": list(public_commands),
                    "reconstruction_class": VAMPIRE_RECONSTRUCTION_CLASS,
                },
                "format": VAMPIRE_LIVE_FORMAT,
                "kernel": kernel_record,
                "outcome": {"error": error, "phase": phase, "status": status},
                "owner_after": after,
                "owner_before": before,
                "premises": {
                    "names": list(premise_names),
                    "resolved": premises_record,
                },
                "problem": problem_record,
                "process": process_record,
                "solver": solver.to_dict(),
                "v": VAMPIRE_LIVE_VERSION,
            }
        )

    def reject(phase: str, value: object) -> VampireLiveFailure:
        error = _error_text(value)
        trace = trace_record(
            after=before,
            status="rejected",
            phase=phase,
            error=error,
        )
        return VampireLiveFailure(owner, phase, error, trace)

    try:
        _validate_owner(owner)
    except Exception as exc:
        return reject("owner", exc)

    goal = owner.state.current()
    if goal is None:  # _validate_owner already rejects this; keep the boundary explicit.
        return reject("goal", "Vampire live requires one focused open goal")
    if goal.variables or goal.context:
        return reject(
            "goal",
            "Vampire live A3.2 accepts only a closed focused goal with empty context",
        )
    try:
        focused = apply_formula_subst(goal.target, owner.state.subst)
        goal_text = pretty_formula(focused, [])
    except Exception as exc:
        return reject("goal", exc)

    try:
        premises = _resolve_premises(owner, premise_names)
        premises_record = [
            {"formula": premise.formula, "kind": premise.kind, "name": premise.name}
            for premise in premises
        ]
    except Exception as exc:
        return reject("premises", exc)
    try:
        problem = emit_tptp_problem(
            goal_text,
            premises,
            requested_premises=premise_names,
        )
        problem_record = _problem_record(problem)
    except Exception as exc:
        return reject("problem", exc)

    try:
        invocation = _invoke_vampire(solver, problem)
        process_record = invocation.record
    except _ProcessFailure as exc:
        process_record = exc.record
        return reject("process", exc)
    except Exception as exc:  # defense-in-depth around the preview host.
        return reject("process", exc)

    try:
        public_commands = reconstruct_public_commands(problem, invocation.evidence)
        if not public_commands:
            raise ValueError(
                "Vampire status alone has no authority and yielded no reconstructed commands"
            )
        if len(public_commands) > solver.bounds.max_commands:
            raise ValueError("Vampire reconstruction exceeds its public-command bound")
        if len(owner.replay_steps) + len(public_commands) > MAX_OWNER_REPLAY_STEPS:
            raise ValueError("Vampire reconstruction exceeds the owner replay-step bound")
    except Exception as exc:
        return reject("reconstruction", exc)

    temporary = owner
    for index, command in enumerate(public_commands):
        try:
            session = run_surface(
                temporary.session,
                command,
                capabilities=owner.capabilities,
                record_trace=False,
            )
            temporary = temporary.with_session(session)
            intermediates.append(
                {
                    "command": command,
                    "command_index": index,
                    "state": _state_summary(temporary),
                }
            )
        except Exception as exc:
            return reject("reconstruction", exc)

    certificate: Proof | None = None
    if temporary.state.is_done():
        try:
            certificate, replay = _fresh_final_replay(temporary)
            nodes, depth = proof_metrics(certificate)
            if not check((), certificate, owner.original_target):
                raise ValueError("fresh Vampire replay certificate failed the kernel")
            kernel_record = {
                **replay,
                "attempted": True,
                "certificate_depth_observed": depth,
                "certificate_nodes_observed": nodes,
                "fresh_original_goal_replay": True,
            }
        except Exception as exc:
            retained = getattr(exc, "record", None)
            kernel_record = (
                {
                    **retained,
                    "attempted": True,
                    "fresh_original_goal_replay": True,
                }
                if type(retained) is dict
                else {
                    "attempted": True,
                    "error": _error_text(exc),
                    "fresh_original_goal_replay": True,
                    "status": "rejected",
                }
            )
            return reject("kernel", exc)
    else:
        kernel_record = {
            "attempted": False,
            "error": None,
            "fresh_original_goal_replay": True,
            "status": "not-required-open-successor",
        }

    after = _state_record(temporary)
    trace = trace_record(after=after, status="accepted", phase=None, error=None)
    return VampireLiveAccepted(temporary, public_commands, certificate, trace)


__all__ = [
    "VAMPIRE_LIVE_FORMAT",
    "VAMPIRE_LIVE_VERSION",
    "VAMPIRE_LIVE_MODE",
    "MAX_VAMPIRE_LIVE_TRACE_BYTES",
    "MAX_VAMPIRE_LIVE_MEMORY_BYTES",
    "MAX_VAMPIRE_LIVE_CPU_SECONDS",
    "MAX_VAMPIRE_LIVE_COMMANDS",
    "VampireLiveBounds",
    "VampireLiveSolver",
    "VampireLiveTrace",
    "VampireLiveAccepted",
    "VampireLiveFailure",
    "VampireLiveResult",
    "run_vampire_live",
]
