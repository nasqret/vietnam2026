"""Bounded, dependency-aware orchestration for independently checked goals.

The scheduler adds no proof authority.  Each job constructs a fresh untrusted
portfolio, executes :func:`run_hydra` under its own exact capabilities, and is
counted as proved only after that runner's independent original-goal replay.
Entire worst-case resource envelopes are reserved before workers start; worker
completion order can never affect dependency waves or published result order.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import stat
from threading import Lock
from typing import Callable, Literal
import unicodedata

from peano_lab.batch import BatchResult, run_proof
from peano_lab.kernel.formulas import (
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.ui.prove import MAX_INPUT, SurfaceCapabilities, oversized_numeral

from training.peano_hydra.policy import HydraPortfolioPolicy
from training.peano_hydra.runner import (
    HydraRunResult,
    _validate_replay,
    policy_environment,
    run_hydra,
)
from training.peano_policy.search import SearchLimits, numeral_limit_for_capabilities


MAX_CAMPAIGN_WORKERS = 32
MAX_CAMPAIGN_GOALS = 4_096
MAX_CAMPAIGN_CHECKPOINT_BYTES = 8 * 1024 * 1024
CAMPAIGN_CHECKPOINT_VERSION = 1
_GOAL_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.-]{0,95}")
CampaignGoalStatus = Literal["proof", "exhausted", "limit", "blocked"]
GoalPolicyFactory = Callable[[], HydraPortfolioPolicy]


class CampaignSchedulerError(RuntimeError):
    """A campaign graph, worker, or declared resource contract is invalid."""


def _goal_id(value: object, *, field_name: str) -> str:
    if type(value) is not str or _GOAL_ID.fullmatch(value) is None:
        raise ValueError(
            f"{field_name} must be a safe 1–96 character campaign identifier"
        )
    return value


def _canonical_theorem(source: object, *, capabilities: SurfaceCapabilities) -> str:
    if type(source) is not str or not source:
        raise ValueError("campaign theorem must be non-empty text")
    if (
        source != source.strip()
        or source.splitlines() != [source]
        or len(source) > MAX_INPUT
    ):
        raise ValueError("campaign theorem must be one bounded whitespace-clean line")
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in source
    ):
        raise ValueError("campaign theorem contains unsafe control or format text")
    dangerous = oversized_numeral(
        source,
        maximum=numeral_limit_for_capabilities(capabilities),
    )
    if dangerous is not None:
        raise ValueError(f"campaign theorem contains resource-dangerous numeral {dangerous}")
    try:
        formula, names = parse_formula_with_names(source)
    except (ParseError, TypeError, ValueError, RecursionError) as exc:
        raise ValueError("campaign theorem is not a valid Peano formula") from exc
    if names:
        raise ValueError("campaign theorem must be closed")
    return pretty_formula(formula, [])


@dataclass(frozen=True, slots=True)
class CampaignGoal:
    """One independently checked proof task and its fixed resource envelope."""

    goal_id: str
    theorem: str
    capabilities: SurfaceCapabilities
    policy_factory: GoalPolicyFactory
    dependencies: tuple[str, ...] = ()
    limits: SearchLimits = SearchLimits()
    classical: bool = False
    canonical_theorem: str = field(init=False)

    def __post_init__(self) -> None:
        _goal_id(self.goal_id, field_name="goal_id")
        if type(self.capabilities) is not SurfaceCapabilities:
            raise TypeError("campaign goal needs exact SurfaceCapabilities")
        if not callable(self.policy_factory):
            raise TypeError("campaign goal needs a callable fresh policy factory")
        if type(self.dependencies) is not tuple:
            raise TypeError("campaign dependencies must be an exact tuple")
        for dependency in self.dependencies:
            _goal_id(dependency, field_name="dependency")
        if len(set(self.dependencies)) != len(self.dependencies):
            raise ValueError("campaign dependencies must not repeat goal IDs")
        if self.goal_id in self.dependencies:
            raise ValueError("a campaign goal cannot depend on itself")
        if type(self.limits) is not SearchLimits:
            raise TypeError("campaign goal needs exact SearchLimits")
        if type(self.classical) is not bool:
            raise TypeError("campaign goal classical mode must be a Boolean")
        object.__setattr__(
            self,
            "canonical_theorem",
            _canonical_theorem(self.theorem, capabilities=self.capabilities),
        )


@dataclass(frozen=True, slots=True)
class CampaignLimits:
    """Globally reserved worst-case limits for an entire proof campaign."""

    max_workers: int = 4
    max_goals: int = 512
    max_total_model_calls: int = 131_072
    max_total_states: int = 1_048_576
    max_total_candidates: int = 1_048_576

    def __post_init__(self) -> None:
        for name in (
            "max_workers",
            "max_goals",
            "max_total_model_calls",
            "max_total_states",
            "max_total_candidates",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ValueError(f"campaign {name} must be a positive integer")
        if self.max_workers > MAX_CAMPAIGN_WORKERS:
            raise ValueError(
                f"campaign max_workers may not exceed {MAX_CAMPAIGN_WORKERS}"
            )
        if self.max_goals > MAX_CAMPAIGN_GOALS:
            raise ValueError(f"campaign max_goals may not exceed {MAX_CAMPAIGN_GOALS}")


@dataclass(frozen=True, slots=True)
class CampaignGoalResult:
    """One checked runner outcome or an explicit dependency-blocked task."""

    goal_id: str
    theorem: str
    status: CampaignGoalStatus
    dependencies: tuple[str, ...]
    blocked_by: tuple[str, ...]
    run: HydraRunResult | None
    restored_replay: BatchResult | None = None

    def __post_init__(self) -> None:
        if self.status == "blocked":
            if (
                not self.blocked_by
                or self.run is not None
                or self.restored_replay is not None
            ):
                raise ValueError("a blocked campaign goal needs blockers and no run")
        elif self.restored_replay is not None:
            if (
                self.status != "proof"
                or self.run is not None
                or self.blocked_by
                or type(self.restored_replay) is not BatchResult
                or self.restored_replay.status != "proved"
                or self.restored_replay.kernel_checked is not True
                or self.restored_replay.theorem != self.theorem
            ):
                raise ValueError("a restored goal needs one original-goal kernel replay")
        elif self.run is None or self.blocked_by or self.run.status != self.status:
            raise ValueError("an executed campaign goal needs its exact runner result")
        if self.run is not None and self.run.theorem != self.theorem:
            raise ValueError("campaign runner changed its original theorem")

    @property
    def proved(self) -> bool:
        return self.status == "proof"

    @property
    def restored(self) -> bool:
        return self.restored_replay is not None

    def to_dict(self, *, include_trace: bool = False) -> dict[str, object]:
        return {
            "id": self.goal_id,
            "theorem": self.theorem,
            "status": self.status,
            "proved": self.proved,
            "restored": self.restored,
            "dependencies": list(self.dependencies),
            "blocked_by": list(self.blocked_by),
            "run": (
                None
                if self.run is None
                else self.run.to_dict(include_trace=include_trace)
            ),
            "restored_replay": (
                None
                if self.restored_replay is None
                else self.restored_replay.to_dict(include_trace=include_trace)
            ),
        }


@dataclass(frozen=True, slots=True)
class CampaignRunResult:
    """Declaration-ordered outcomes and reproducible resource accounting."""

    goals: tuple[CampaignGoalResult, ...]
    workers: int
    waves: int
    reserved_model_calls: int
    reserved_states: int
    reserved_candidates: int
    model_calls: int
    states_discovered: int
    candidates_executed: int
    proof_nodes: int

    @property
    def proved_goals(self) -> int:
        return sum(goal.proved for goal in self.goals)

    @property
    def blocked_goals(self) -> int:
        return sum(goal.status == "blocked" for goal in self.goals)

    @property
    def restored_goals(self) -> int:
        return sum(goal.restored for goal in self.goals)

    def to_dict(self, *, include_trace: bool = False) -> dict[str, object]:
        return {
            "goals": [goal.to_dict(include_trace=include_trace) for goal in self.goals],
            "goal_count": len(self.goals),
            "proved_goals": self.proved_goals,
            "blocked_goals": self.blocked_goals,
            "restored_goals": self.restored_goals,
            "workers": self.workers,
            "waves": self.waves,
            "reserved": {
                "model_calls": self.reserved_model_calls,
                "states": self.reserved_states,
                "candidates": self.reserved_candidates,
            },
            "consumed": {
                "model_calls": self.model_calls,
                "states": self.states_discovered,
                "candidates": self.candidates_executed,
                "proof_nodes": self.proof_nodes,
            },
            # The pre-H0 runner intentionally does not produce campaign-grade
            # comparison evidence merely because several runs were scheduled.
            "eligible_for_comparison": False,
        }


def _validate_graph(
    goals: tuple[CampaignGoal, ...],
    limits: CampaignLimits,
) -> tuple[dict[str, CampaignGoal], int, int, int]:
    if type(goals) is not tuple or not goals:
        raise ValueError("campaign goals must be one non-empty exact tuple")
    if len(goals) > limits.max_goals:
        raise ValueError(f"campaign exceeds its {limits.max_goals}-goal limit")
    by_id: dict[str, CampaignGoal] = {}
    for goal in goals:
        if type(goal) is not CampaignGoal:
            raise TypeError("campaign entries must be exact CampaignGoal values")
        if goal.goal_id in by_id:
            raise ValueError(f"campaign repeats goal ID {goal.goal_id!r}")
        by_id[goal.goal_id] = goal

    for goal in goals:
        unknown = tuple(name for name in goal.dependencies if name not in by_id)
        if unknown:
            raise ValueError(
                f"campaign goal {goal.goal_id!r} has unknown dependencies: "
                + ", ".join(unknown)
            )

    remaining = set(by_id)
    consumed: set[str] = set()
    while remaining:
        ready = tuple(
            goal.goal_id
            for goal in goals
            if goal.goal_id in remaining
            and all(dependency in consumed for dependency in goal.dependencies)
        )
        if not ready:
            raise ValueError("campaign dependency graph contains a cycle")
        remaining.difference_update(ready)
        consumed.update(ready)

    reserved_calls = sum(goal.limits.max_model_calls for goal in goals)
    reserved_states = sum(goal.limits.max_states for goal in goals)
    reserved_candidates = sum(
        goal.limits.max_model_calls * goal.limits.candidates_per_state
        for goal in goals
    )
    if reserved_calls > limits.max_total_model_calls:
        raise ValueError("campaign reserved model calls exceed its global budget")
    if reserved_states > limits.max_total_states:
        raise ValueError("campaign reserved states exceed its global budget")
    if reserved_candidates > limits.max_total_candidates:
        raise ValueError("campaign reserved candidates exceed its global budget")
    return by_id, reserved_calls, reserved_states, reserved_candidates


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _goal_profile(goal: CampaignGoal) -> dict[str, object]:
    return {
        "id": goal.goal_id,
        "source": goal.theorem,
        "theorem": goal.canonical_theorem,
        "dependencies": list(goal.dependencies),
        "environment": policy_environment(
            goal.capabilities,
            classical=goal.classical,
        ),
        "classical": goal.classical,
        "numeral_limit": numeral_limit_for_capabilities(goal.capabilities),
        "limits": {
            "max_depth": goal.limits.max_depth,
            "beam_width": goal.limits.beam_width,
            "candidates_per_state": goal.limits.candidates_per_state,
            "max_model_calls": goal.limits.max_model_calls,
            "max_states": goal.limits.max_states,
        },
    }


def _graph_identity(goals: tuple[CampaignGoal, ...], limits: CampaignLimits) -> str:
    profile = {
        "v": CAMPAIGN_CHECKPOINT_VERSION,
        "goals": [_goal_profile(goal) for goal in goals],
        "limits": {
            "max_workers": limits.max_workers,
            "max_goals": limits.max_goals,
            "max_total_model_calls": limits.max_total_model_calls,
            "max_total_states": limits.max_total_states,
            "max_total_candidates": limits.max_total_candidates,
        },
    }
    return _sha256(profile)


def _strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate checkpoint field {key!r}")
        result[key] = value
    return result


def _directory_descriptor(path: Path) -> tuple[int, str]:
    if path.name in {"", ".", ".."}:
        raise CampaignSchedulerError("checkpoint needs an exact ordinary filename")
    flags = os.O_RDONLY
    flags |= getattr(os, "O_DIRECTORY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(os.fspath(path.parent), flags)
    except OSError as exc:
        raise CampaignSchedulerError(
            "checkpoint parent must be an existing non-symlink directory"
        ) from exc
    return descriptor, path.name


def _checkpoint_stat(descriptor: int, name: str) -> os.stat_result | None:
    try:
        result = os.stat(name, dir_fd=descriptor, follow_symlinks=False)
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise CampaignSchedulerError("checkpoint destination cannot be inspected") from exc
    if not stat.S_ISREG(result.st_mode):
        raise CampaignSchedulerError("checkpoint must be a regular non-symlink file")
    return result


def _checkpoint_document(graph_sha256: str, receipts: list[dict[str, object]]) -> bytes:
    payload = _canonical_json(
        {
            "v": CAMPAIGN_CHECKPOINT_VERSION,
            "graph_sha256": graph_sha256,
            "receipts": receipts,
        }
    )
    if len(payload) > MAX_CAMPAIGN_CHECKPOINT_BYTES:
        raise CampaignSchedulerError("checkpoint exceeds its bounded byte envelope")
    return payload + b"\n"


def _write_checkpoint(
    path: Path,
    graph_sha256: str,
    receipts: list[dict[str, object]],
    *,
    initial: bool,
) -> None:
    payload = _checkpoint_document(graph_sha256, receipts)
    descriptor, name = _directory_descriptor(path)
    temporary = f".{name}.{secrets.token_hex(12)}.tmp"
    fd: int | None = None
    try:
        existing = _checkpoint_stat(descriptor, name)
        if initial and existing is not None:
            raise CampaignSchedulerError(
                "checkpoint already exists; resume must be explicitly requested"
            )
        if not initial and existing is None:
            raise CampaignSchedulerError("checkpoint disappeared during publication")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        flags |= getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(temporary, flags, 0o600, dir_fd=descriptor)
        with os.fdopen(fd, "wb") as sink:
            fd = None
            sink.write(payload)
            sink.flush()
            os.fsync(sink.fileno())
        if initial:
            try:
                os.link(
                    temporary,
                    name,
                    src_dir_fd=descriptor,
                    dst_dir_fd=descriptor,
                    follow_symlinks=False,
                )
            except FileExistsError as exc:
                raise CampaignSchedulerError(
                    "checkpoint destination appeared during publication"
                ) from exc
            os.unlink(temporary, dir_fd=descriptor)
        else:
            _checkpoint_stat(descriptor, name)
            os.replace(
                temporary,
                name,
                src_dir_fd=descriptor,
                dst_dir_fd=descriptor,
            )
        os.fsync(descriptor)
    except CampaignSchedulerError:
        raise
    except OSError as exc:
        raise CampaignSchedulerError("checkpoint atomic publication failed") from exc
    finally:
        if fd is not None:
            os.close(fd)
        try:
            os.unlink(temporary, dir_fd=descriptor)
        except FileNotFoundError:
            pass
        except OSError:
            # Never replace the original error with optional temporary cleanup.
            pass
        os.close(descriptor)


def _read_checkpoint(path: Path, graph_sha256: str) -> list[dict[str, object]]:
    descriptor, name = _directory_descriptor(path)
    fd: int | None = None
    try:
        initial = _checkpoint_stat(descriptor, name)
        if initial is None:
            raise CampaignSchedulerError("requested checkpoint does not exist")
        if initial.st_size > MAX_CAMPAIGN_CHECKPOINT_BYTES + 1:
            raise CampaignSchedulerError("checkpoint exceeds its bounded byte envelope")
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(name, flags, dir_fd=descriptor)
        opened = os.fstat(fd)
        if (
            not stat.S_ISREG(opened.st_mode)
            or opened.st_dev != initial.st_dev
            or opened.st_ino != initial.st_ino
        ):
            raise CampaignSchedulerError("checkpoint destination changed while opening")
        with os.fdopen(fd, "rb") as source:
            fd = None
            payload = source.read(MAX_CAMPAIGN_CHECKPOINT_BYTES + 2)
            after = os.fstat(source.fileno())
        if (
            len(payload) > MAX_CAMPAIGN_CHECKPOINT_BYTES + 1
            or len(payload) != opened.st_size
            or after.st_size != opened.st_size
            or after.st_mtime_ns != opened.st_mtime_ns
        ):
            raise CampaignSchedulerError("checkpoint changed during bounded stable read")
    except CampaignSchedulerError:
        raise
    except OSError as exc:
        raise CampaignSchedulerError("checkpoint cannot be read without following links") from exc
    finally:
        if fd is not None:
            os.close(fd)
        os.close(descriptor)

    try:
        record = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=_strict_json_object,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-finite checkpoint number {value!r}")
            ),
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise CampaignSchedulerError("checkpoint contains malformed or ambiguous JSON") from exc
    if type(record) is not dict or set(record) != {"v", "graph_sha256", "receipts"}:
        raise CampaignSchedulerError("checkpoint has an invalid exact field schema")
    if (
        type(record["v"]) is not int
        or record["v"] != CAMPAIGN_CHECKPOINT_VERSION
    ):
        raise CampaignSchedulerError("checkpoint has an unsupported version")
    if record["graph_sha256"] != graph_sha256:
        raise CampaignSchedulerError("checkpoint graph, authority, or resource limits differ")
    receipts = record["receipts"]
    if type(receipts) is not list:
        raise CampaignSchedulerError("checkpoint receipts must be an exact array")
    return receipts


def _proof_receipt(goal: CampaignGoal, result: HydraRunResult) -> dict[str, object]:
    if not result.proved or result.replay is None:
        raise CampaignSchedulerError("only independently checked proofs enter a checkpoint")
    commands = result.commands
    digest = _sha256(list(commands))
    if result.commands_sha256 != digest:
        raise CampaignSchedulerError("checkpoint proof command digest disagrees with replay")
    return {
        "id": goal.goal_id,
        "theorem": goal.canonical_theorem,
        "dependencies": list(goal.dependencies),
        "goal_sha256": _sha256(_goal_profile(goal)),
        "environment_sha256": result.environment["environment_sha256"],
        "classical": goal.classical,
        "commands": list(commands),
        "commands_sha256": digest,
        "proof_nodes": result.search.certificate_nodes,
    }


def _restore_checkpoint(
    path: Path,
    goals: tuple[CampaignGoal, ...],
    graph_sha256: str,
) -> tuple[dict[str, CampaignGoalResult], list[dict[str, object]]]:
    receipts = _read_checkpoint(path, graph_sha256)
    if len(receipts) > len(goals):
        raise CampaignSchedulerError("checkpoint contains more receipts than campaign goals")
    by_id = {goal.goal_id: goal for goal in goals}
    restored: dict[str, CampaignGoalResult] = {}
    expected_fields = {
        "id",
        "theorem",
        "dependencies",
        "goal_sha256",
        "environment_sha256",
        "classical",
        "commands",
        "commands_sha256",
        "proof_nodes",
    }
    for receipt in receipts:
        if type(receipt) is not dict or set(receipt) != expected_fields:
            raise CampaignSchedulerError("checkpoint proof receipt has an invalid schema")
        identifier = receipt["id"]
        if type(identifier) is not str or identifier not in by_id:
            raise CampaignSchedulerError("checkpoint names an unknown campaign goal")
        if identifier in restored:
            raise CampaignSchedulerError("checkpoint repeats one campaign goal")
        goal = by_id[identifier]
        environment = policy_environment(goal.capabilities, classical=goal.classical)
        if (
            receipt["theorem"] != goal.canonical_theorem
            or receipt["dependencies"] != list(goal.dependencies)
            or receipt["goal_sha256"] != _sha256(_goal_profile(goal))
            or receipt["environment_sha256"] != environment["environment_sha256"]
            or receipt["classical"] is not goal.classical
        ):
            raise CampaignSchedulerError("checkpoint receipt changed its goal or authority")
        if not all(dependency in restored for dependency in goal.dependencies):
            raise CampaignSchedulerError("checkpoint proof precedes a checked dependency")
        raw_commands = receipt["commands"]
        if (
            type(raw_commands) is not list
            or not raw_commands
            or len(raw_commands) > goal.limits.max_depth
            or not all(
                type(command) is str
                and command
                and command == command.strip()
                and command.splitlines() == [command]
                and len(command) <= MAX_INPUT
                and oversized_numeral(
                    command,
                    maximum=numeral_limit_for_capabilities(goal.capabilities),
                )
                is None
                for command in raw_commands
            )
        ):
            raise CampaignSchedulerError("checkpoint proof has unsafe or unbounded commands")
        commands = tuple(raw_commands)
        digest = _sha256(raw_commands)
        if receipt["commands_sha256"] != digest:
            raise CampaignSchedulerError("checkpoint proof command digest changed")
        nodes = receipt["proof_nodes"]
        if type(nodes) is not int or nodes < 1:
            raise CampaignSchedulerError("checkpoint proof needs a positive node count")
        request_id = f"hydra-checkpoint-{graph_sha256[:12]}-{goal.goal_id}"
        session_id = f"peano-hydra-checkpoint-{digest[:24]}"
        try:
            replay = run_proof(
                goal.theorem,
                commands,
                request_id=request_id,
                classical=goal.classical,
                on_error="stop",
                capabilities=goal.capabilities,
                session_id=session_id,
            )
            _validate_replay(
                expected_theorem=goal.canonical_theorem,
                expected_commands=commands,
                expected_nodes=nodes,
                expected_request_id=request_id,
                expected_session_id=session_id,
                expected_environment=environment,
                classical=goal.classical,
                replay=replay,
            )
        except Exception as exc:
            raise CampaignSchedulerError(
                f"checkpoint proof for {identifier!r} failed fresh original-goal replay"
            ) from exc
        restored[identifier] = CampaignGoalResult(
            identifier,
            goal.canonical_theorem,
            "proof",
            goal.dependencies,
            (),
            None,
            replay,
        )
    return restored, receipts


def _checked_worker_result(goal: CampaignGoal, result: HydraRunResult) -> HydraRunResult:
    if type(result) is not HydraRunResult:
        raise CampaignSchedulerError("goal worker returned a malformed Hydra result")
    if (
        result.theorem != goal.canonical_theorem
        or result.search.theorem != goal.canonical_theorem
    ):
        raise CampaignSchedulerError("goal worker changed its original theorem")
    if result.environment != policy_environment(
        goal.capabilities, classical=goal.classical
    ):
        raise CampaignSchedulerError("goal worker changed its execution authority")
    expected_limits = {
        "max_depth": goal.limits.max_depth,
        "beam_width": goal.limits.beam_width,
        "candidates_per_state": goal.limits.candidates_per_state,
        "max_model_calls": goal.limits.max_model_calls,
        "max_states": goal.limits.max_states,
    }
    if result.limits != expected_limits:
        raise CampaignSchedulerError("goal worker changed its declared search limits")
    for name in ("model_calls", "states_discovered", "candidates_executed"):
        observed = getattr(result.search, name)
        if type(observed) is not int or observed < 0:
            raise CampaignSchedulerError(f"goal worker returned an invalid {name} count")
    if result.search.states_discovered == 0:
        raise CampaignSchedulerError("goal worker omitted its original root state")
    if result.search.model_calls > goal.limits.max_model_calls:
        raise CampaignSchedulerError("goal worker exceeded its model-call reservation")
    if result.search.states_discovered > goal.limits.max_states:
        raise CampaignSchedulerError("goal worker exceeded its state reservation")
    if (
        result.search.candidates_executed
        > result.search.model_calls * goal.limits.candidates_per_state
    ):
        raise CampaignSchedulerError("goal worker exceeded its candidate reservation")
    if result.proved and (
        result.replay is None
        or result.replay.kernel_checked is not True
        or result.replay.theorem != goal.canonical_theorem
        or result.replay.proof_nodes != result.search.certificate_nodes
    ):
        raise CampaignSchedulerError("goal worker proof lacks original-goal kernel replay")
    return result


def run_campaign(
    goals: tuple[CampaignGoal, ...],
    *,
    limits: CampaignLimits = CampaignLimits(),
    checkpoint: Path | None = None,
    resume: bool = False,
) -> CampaignRunResult:
    """Execute bounded dependency waves, optionally resuming checked receipts.

    A checkpoint is never theorem authority.  Resumption first binds the exact
    graph, statements, capabilities, logic mode, and resource envelopes, then
    independently kernel-replays every stored proof before releasing a child.
    Fresh searches and restored proofs are reported separately.
    """

    if type(limits) is not CampaignLimits:
        raise TypeError("campaign needs exact CampaignLimits")
    if type(resume) is not bool:
        raise TypeError("campaign resume flag must be a Boolean")
    if checkpoint is not None and not isinstance(checkpoint, Path):
        raise TypeError("campaign checkpoint must be a filesystem Path")
    if checkpoint is None and resume:
        raise ValueError("campaign resume requires an explicit checkpoint Path")
    _, reserved_calls, reserved_states, reserved_candidates = _validate_graph(
        goals, limits
    )
    graph_sha256 = _graph_identity(goals, limits)
    receipts: list[dict[str, object]] = []
    restored: dict[str, CampaignGoalResult] = {}
    if checkpoint is not None:
        checkpoint = checkpoint.absolute()
        if resume:
            restored, receipts = _restore_checkpoint(checkpoint, goals, graph_sha256)
        else:
            _write_checkpoint(checkpoint, graph_sha256, receipts, initial=True)
    workers = min(limits.max_workers, len(goals))
    policy_lock = Lock()
    active_policies: list[HydraPortfolioPolicy] = []
    active_policy_ids: set[int] = set()
    results: dict[str, CampaignGoalResult] = dict(restored)
    remaining = {goal.goal_id for goal in goals if goal.goal_id not in restored}
    waves = 0

    def execute(goal: CampaignGoal) -> HydraRunResult:
        policy = goal.policy_factory()
        with policy_lock:
            identifier = id(policy)
            if identifier in active_policy_ids:
                raise CampaignSchedulerError("campaign goals cannot share one policy instance")
            # Hold policies only until this wave completes.  This prevents
            # object-ID reuse within concurrent work without retaining every
            # model/provider and proposal ledger for the entire campaign.
            # Reuse in a later wave is rejected independently by run_hydra's
            # non-empty-ledger rule.
            active_policy_ids.add(identifier)
            active_policies.append(policy)
        result = run_hydra(
            goal.theorem,
            policy,
            capabilities=goal.capabilities,
            classical=goal.classical,
            limits=goal.limits,
            label=f"campaign-{goal.goal_id}",
        )
        return _checked_worker_result(goal, result)

    with ThreadPoolExecutor(
        max_workers=workers,
        thread_name_prefix="peano-hydra-goal",
    ) as executor:
        while remaining:
            changed = True
            while changed:
                changed = False
                for goal in goals:
                    if goal.goal_id not in remaining:
                        continue
                    blockers = tuple(
                        dependency
                        for dependency in goal.dependencies
                        if dependency in results and not results[dependency].proved
                    )
                    if blockers:
                        results[goal.goal_id] = CampaignGoalResult(
                            goal.goal_id,
                            goal.canonical_theorem,
                            "blocked",
                            goal.dependencies,
                            blockers,
                            None,
                        )
                        remaining.remove(goal.goal_id)
                        changed = True

            ready = tuple(
                goal
                for goal in goals
                if goal.goal_id in remaining
                and all(
                    dependency in results and results[dependency].proved
                    for dependency in goal.dependencies
                )
            )
            if not ready:
                if remaining:
                    raise CampaignSchedulerError("campaign has no runnable dependency wave")
                break
            waves += 1
            futures = tuple((goal, executor.submit(execute, goal)) for goal in ready)
            for goal, future in futures:
                try:
                    result = future.result()
                except Exception as exc:
                    reason = " ".join(str(exc).split()) or type(exc).__name__
                    raise CampaignSchedulerError(
                        f"campaign goal {goal.goal_id!r} failed: {reason[:1_000]}"
                    ) from exc
                results[goal.goal_id] = CampaignGoalResult(
                    goal.goal_id,
                    goal.canonical_theorem,
                    result.status,
                    goal.dependencies,
                    (),
                    result,
                )
                if checkpoint is not None and result.proved:
                    receipts.append(_proof_receipt(goal, result))
                    _write_checkpoint(
                        checkpoint,
                        graph_sha256,
                        receipts,
                        initial=False,
                    )
                remaining.remove(goal.goal_id)
            with policy_lock:
                active_policy_ids.clear()
                active_policies.clear()

    ordered = tuple(results[goal.goal_id] for goal in goals)
    executed = tuple(result.run for result in ordered if result.run is not None)
    return CampaignRunResult(
        ordered,
        workers,
        waves,
        reserved_calls,
        reserved_states,
        reserved_candidates,
        sum(result.search.model_calls for result in executed),
        sum(result.search.states_discovered for result in executed),
        sum(result.search.candidates_executed for result in executed),
        sum(result.search.certificate_nodes or 0 for result in executed)
        + sum(
            result.restored_replay.proof_nodes or 0
            for result in ordered
            if result.restored_replay is not None
        ),
    )


__all__ = [
    "CAMPAIGN_CHECKPOINT_VERSION",
    "MAX_CAMPAIGN_CHECKPOINT_BYTES",
    "MAX_CAMPAIGN_GOALS",
    "MAX_CAMPAIGN_WORKERS",
    "CampaignGoal",
    "CampaignGoalResult",
    "CampaignGoalStatus",
    "CampaignLimits",
    "CampaignRunResult",
    "CampaignSchedulerError",
    "run_campaign",
]
