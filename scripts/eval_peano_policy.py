#!/usr/bin/env python3
"""Kernel-judged pass@k evaluation for Peano Lab tactic policies.

This module is both an importable, deliberately small evaluation API and a
command-line smoke test.  Policies propose *surface tactic text*.  The harness
executes that text with Peano Lab's real interactive tactic grammar and keeps
the original parsed theorem plus its exact logic mode outside the policy.  A
rollout is a proof only when ``checked_final`` accepts its closed certificate.

No model runtime or training framework is required.  ``RandomPolicy`` is a
deterministic dummy policy which exercises the complete protocol end to end.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, Sequence, runtime_checkable


# Running ``python3 scripts/eval_peano_policy.py`` from the repository root
# should need neither installation nor PYTHONPATH surgery by the caller.
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.engine.state import proof_size, start  # noqa: E402
from peano_lab.engine.tactics import (  # noqa: E402
    InvalidProof,
    TacticError,
    TacticLimit,
    TacticSyntaxError,
    checked_final,
)
from peano_lab.engine.trace import TraceLogger, render_goals  # noqa: E402
from peano_lab.kernel.formulas import (  # noqa: E402
    Formula,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.library.theorems import THEOREMS  # noqa: E402
from peano_lab.ui.prove import ProofSession, _run_surface  # noqa: E402


EVAL_VERSION = 1
MAX_COMMAND_CHARS = 4_000
AttemptStatus = Literal["proof", "invalid", "failing", "limit"]
ATTEMPT_STATUSES: tuple[AttemptStatus, ...] = (
    "proof",
    "invalid",
    "failing",
    "limit",
)


@dataclass(frozen=True, slots=True)
class EvalGoal:
    """One closed theorem and the externally owned logic-mode authority."""

    name: str
    statement: str
    classical: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("an evaluation goal needs a non-empty name")
        if self.name != self.name.strip() or any(
            char.isspace() for char in self.name
        ):
            raise ValueError("an evaluation goal name must be one non-space token")
        if not isinstance(self.statement, str) or not self.statement.strip():
            raise ValueError("an evaluation goal needs a non-empty statement")
        if type(self.classical) is not bool:
            raise TypeError("an evaluation goal's classical mode must be a Boolean")


def _parse_closed_goal(goal: EvalGoal) -> tuple[Formula, tuple[str, ...], str]:
    try:
        target, names = parse_formula_with_names(goal.statement)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"invalid evaluation statement for {goal.name!r}: {exc}") from None
    if names:
        raise ValueError(
            f"evaluation statement {goal.name!r} is not closed; free names: "
            + ", ".join(names)
        )
    return target, names, pretty_formula(target, list(names))


@runtime_checkable
class Policy(Protocol):
    """Minimal state-to-tactic interface used by :func:`evaluate`.

    The policy sees only the canonical trace-format ``goals_before`` strings,
    never the internal ``ProofState``, theorem name/source, or logic mode.
    ``sample`` and ``step`` are zero-based.  The supplied RNG is local to that
    theorem/sample pair, so consuming randomness cannot perturb another
    rollout.  Returning ``None`` is an honest early resource-limit outcome.
    """

    name: str

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        sample: int,
        step: int,
        rng: random.Random,
    ) -> str | None:
        """Return one Peano Lab surface tactic, or ``None`` to stop."""


@dataclass(frozen=True, slots=True)
class RandomPolicy:
    """A deterministic, state-independent random-tactic baseline."""

    name: str = "random-tactic-v1"
    commands: tuple[str, ...] = (
        "simp",
        "assumption",
        "refl",
        "intro n",
        "induction n",
        "split",
        "left",
        "right",
        "congr",
        "exists 0",
        "apply PA1",
        "apply PA2",
        "first [assumption | refl | simp]",
        "induction n; simp",
    )

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("a policy needs a non-empty stable name")
        if type(self.commands) is not tuple or not self.commands:
            raise ValueError("the random policy needs a non-empty command tuple")
        if not all(isinstance(item, str) and item.strip() for item in self.commands):
            raise ValueError("random-policy commands must be non-empty text")

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        sample: int,
        step: int,
        rng: random.Random,
    ) -> str:
        del goals_before, sample, step
        return rng.choice(self.commands)


# These tail-ladder families are the public evaluation split.  Released
# train/validation data excludes all generated ladder sessions and any future
# synthetic variant derived from one of these families.  Statements are
# literal protocol data, not dynamically inherited from a mutable library.
DEFAULT_HELD_OUT_GOALS: tuple[EvalGoal, ...] = (
    EvalGoal("le_trans", "forall n m k. n <= m -> m <= k -> n <= k"),
    EvalGoal("le_antisymm", "forall n m. n <= m -> m <= n -> n = m"),
    EvalGoal("le_total", "forall n m. n <= m \\/ m <= n"),
    EvalGoal("mul_eq_zero", "forall n m. n * m = 0 -> n = 0 \\/ m = 0"),
)
HELD_OUT_LADDER_NAMES: tuple[str, ...] = tuple(
    goal.name for goal in DEFAULT_HELD_OUT_GOALS
)


def _goal_set_sha256(goals: Sequence[EvalGoal]) -> str:
    rows = [
        {
            "name": goal.name,
            "statement": _parse_closed_goal(goal)[2],
            "classical": goal.classical,
        }
        for goal in goals
    ]
    payload = json.dumps(
        [EVAL_VERSION, rows],
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


HELD_OUT_GOAL_SET_SHA256 = _goal_set_sha256(DEFAULT_HELD_OUT_GOALS)


def _guard_held_out_library_alignment() -> None:
    library = {spec.name: spec for spec in THEOREMS}
    for goal in DEFAULT_HELD_OUT_GOALS:
        spec = library.get(goal.name)
        if spec is None:
            raise RuntimeError(f"held-out protocol theorem {goal.name!r} left the library")
        library_goal = EvalGoal(spec.name, spec.statement)
        if _parse_closed_goal(library_goal)[0] != _parse_closed_goal(goal)[0]:
            raise RuntimeError(
                f"held-out theorem {goal.name!r} changed; bump EVAL_VERSION explicitly"
            )


_guard_held_out_library_alignment()


@dataclass(frozen=True, slots=True)
class AttemptResult:
    """One terminal policy rollout."""

    sample: int
    seed: int
    status: AttemptStatus
    commands: tuple[str, ...]
    proof_nodes: int | None
    error: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "sample": self.sample,
            "seed": self.seed,
            "status": self.status,
            "steps": len(self.commands),
            "commands": list(self.commands),
            "proof_nodes": self.proof_nodes,
            "error": self.error,
        }


@dataclass(frozen=True, slots=True)
class GoalResult:
    """All ``k`` independent rollouts for one theorem."""

    goal: EvalGoal
    canonical_statement: str
    attempts: tuple[AttemptResult, ...]

    @property
    def passed(self) -> bool:
        return any(attempt.status == "proof" for attempt in self.attempts)

    @property
    def status_counts(self) -> dict[str, int]:
        return {
            status: sum(attempt.status == status for attempt in self.attempts)
            for status in ATTEMPT_STATUSES
        }

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.goal.name,
            "statement": self.canonical_statement,
            "classical": self.goal.classical,
            "passed": self.passed,
            "status_counts": self.status_counts,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }


@dataclass(frozen=True, slots=True)
class EvaluationReport:
    """Deterministic pass@k report returned by :func:`evaluate`."""

    policy: str
    seed: int
    k: int
    max_steps: int
    goals: tuple[GoalResult, ...]

    @property
    def status_counts(self) -> dict[str, int]:
        attempts = tuple(
            attempt for goal_result in self.goals for attempt in goal_result.attempts
        )
        return {
            status: sum(attempt.status == status for attempt in attempts)
            for status in ATTEMPT_STATUSES
        }

    @property
    def proved_goals(self) -> int:
        return sum(goal_result.passed for goal_result in self.goals)

    @property
    def pass_at_k(self) -> float:
        return self.proved_goals / len(self.goals) if self.goals else 0.0

    @property
    def goal_set_sha256(self) -> str:
        return _goal_set_sha256(tuple(result.goal for result in self.goals))

    def to_dict(self) -> dict[str, object]:
        return {
            "v": EVAL_VERSION,
            "policy": self.policy,
            "judge": "checked_final(original_target, exact_mode)",
            "goal_set_sha256": self.goal_set_sha256,
            "seed": self.seed,
            "k": self.k,
            "max_steps": self.max_steps,
            "goal_count": len(self.goals),
            "attempt_count": sum(len(result.attempts) for result in self.goals),
            "proved_goals": self.proved_goals,
            "pass@k": self.pass_at_k,
            "status_counts": self.status_counts,
            "goals": [result.to_dict() for result in self.goals],
        }

    def json(self, *, indent: int | None = 2) -> str:
        """Return stable UTF-8 JSON with deterministic key ordering."""

        return json.dumps(
            self.to_dict(),
            ensure_ascii=False,
            indent=indent,
            sort_keys=True,
            separators=(",", ":") if indent is None else None,
        )


def _stable_attempt_seed(seed: int, canonical_statement: str, sample: int) -> int:
    payload = json.dumps(
        [EVAL_VERSION, seed, canonical_statement, sample],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _one_line_error(prefix: str, error: BaseException | str) -> str:
    text = " ".join(str(error).split()) or type(error).__name__
    return f"{prefix}: {text}"[:1_000]


def _valid_command(command: object) -> tuple[str | None, str | None]:
    if type(command) is not str:
        return None, "policy output is not tactic text"
    if not command:
        return None, "policy output is blank"
    if len(command) > MAX_COMMAND_CHARS:
        return None, f"policy output exceeds {MAX_COMMAND_CHARS} characters"
    if command.splitlines() != [command]:
        return None, "policy output must be one tactic line"
    stripped = command.strip()
    if not stripped:
        return None, "policy output is blank"
    return stripped, None


def _is_resource_limit(command: str, error: TacticError) -> bool:
    del command
    return isinstance(error, TacticLimit)


def _is_invalid_surface_command(error: TacticError) -> bool:
    return isinstance(error, TacticSyntaxError)


def _rollout(
    policy: Policy,
    goal: EvalGoal,
    target: Formula,
    names: tuple[str, ...],
    canonical_statement: str,
    *,
    sample: int,
    seed: int,
    max_steps: int,
) -> AttemptResult:
    attempt_seed = _stable_attempt_seed(seed, canonical_statement, sample)
    rng = random.Random(attempt_seed)
    owner = ProofSession(
        state=start(target, names),
        original_target=target,
        original_names=names,
        target_source=goal.statement,
        classical=goal.classical,
        trace=TraceLogger(session_id=f"eval-{goal.name}-{sample + 1}"),
    )
    commands: list[str] = []
    meta_names: dict[int, str] = {}

    for step in range(max_steps):
        try:
            proposed = policy.propose(
                tuple(render_goals(owner.state, meta_names=meta_names)),
                sample=sample,
                step=step,
                rng=rng,
            )
        except Exception as exc:  # a broken model adapter is not a proof failure
            return AttemptResult(
                sample,
                attempt_seed,
                "invalid",
                tuple(commands),
                None,
                _one_line_error("policy error", exc),
            )

        if proposed is None:
            return AttemptResult(
                sample,
                attempt_seed,
                "limit",
                tuple(commands),
                None,
                "policy stopped before closing the theorem",
            )
        command, invalid_reason = _valid_command(proposed)
        if command is None:
            return AttemptResult(
                sample,
                attempt_seed,
                "invalid",
                tuple(commands),
                None,
                invalid_reason,
            )
        commands.append(command)

        try:
            # This is the production surface grammar: primitives, tacticals,
            # simp, and auto.  The evaluator has no private tactic operations.
            owner = _run_surface(owner, command)
        except TacticError as exc:
            if _is_resource_limit(command, exc):
                status: AttemptStatus = "limit"
            elif _is_invalid_surface_command(exc):
                status = "invalid"
            else:
                status = "failing"
            return AttemptResult(
                sample,
                attempt_seed,
                status,
                tuple(commands),
                None,
                _one_line_error(
                    "surface error" if status == "invalid" else "tactic error",
                    exc,
                ),
            )
        except Exception as exc:  # malformed adapters/grammar bugs stay non-proofs
            return AttemptResult(
                sample,
                attempt_seed,
                "invalid",
                tuple(commands),
                None,
                _one_line_error("evaluation error", exc),
            )

        if owner.state.is_done():
            try:
                # The externally retained target and exact mode are explicit.
                certificate = checked_final(
                    owner.state,
                    target,
                    classical=goal.classical,
                )
            except InvalidProof as exc:
                return AttemptResult(
                    sample,
                    attempt_seed,
                    "invalid",
                    tuple(commands),
                    None,
                    _one_line_error("kernel rejection", exc),
                )
            return AttemptResult(
                sample,
                attempt_seed,
                "proof",
                tuple(commands),
                proof_size(certificate),
                None,
            )

    return AttemptResult(
        sample,
        attempt_seed,
        "limit",
        tuple(commands),
        None,
        f"step limit reached ({max_steps})",
    )


def evaluate(
    policy: Policy,
    goals: Sequence[EvalGoal] = DEFAULT_HELD_OUT_GOALS,
    *,
    k: int = 8,
    max_steps: int = 16,
    seed: int = 20_260_727,
) -> EvaluationReport:
    """Evaluate ``k`` independent samples per goal with the kernel as judge.

    ``pass@k`` in the returned report is the fraction of goal families with at
    least one checked proof among exactly ``k`` rollouts.  Invalid model output,
    legal-but-failing tactics, and exhausted limits are reported separately and
    never collapsed into a proof failure count.
    """

    if not isinstance(policy, Policy):
        raise TypeError("policy must provide a stable name and propose(...) method")
    if not isinstance(policy.name, str) or not policy.name.strip():
        raise ValueError("policy.name must be non-empty stable text")
    if type(k) is not int or k < 1:
        raise ValueError("k must be a positive integer")
    if type(max_steps) is not int or max_steps < 1:
        raise ValueError("max_steps must be a positive integer")
    if type(seed) is not int:
        raise TypeError("seed must be an integer")
    if isinstance(goals, (str, bytes)):
        raise TypeError("goals must be a sequence of EvalGoal values")
    goal_tuple = tuple(goals)
    if not goal_tuple or not all(type(goal) is EvalGoal for goal in goal_tuple):
        raise ValueError("goals must contain at least one exact EvalGoal")
    if len({goal.name for goal in goal_tuple}) != len(goal_tuple):
        raise ValueError("evaluation goal names must be unique")

    results: list[GoalResult] = []
    for goal in goal_tuple:
        target, names, canonical = _parse_closed_goal(goal)
        attempts = tuple(
            _rollout(
                policy,
                goal,
                target,
                names,
                canonical,
                sample=sample,
                seed=seed,
                max_steps=max_steps,
            )
            for sample in range(k)
        )
        results.append(GoalResult(goal, canonical, attempts))
    return EvaluationReport(policy.name, seed, k, max_steps, tuple(results))


def _selected_goals(names: Sequence[str]) -> tuple[EvalGoal, ...]:
    if not names:
        return DEFAULT_HELD_OUT_GOALS
    table = {goal.name: goal for goal in DEFAULT_HELD_OUT_GOALS}
    unknown = [name for name in names if name not in table]
    if unknown:
        raise ValueError("unknown held-out goal(s): " + ", ".join(unknown))
    if len(set(names)) != len(names):
        raise ValueError("held-out goal names may not be repeated")
    return tuple(table[name] for name in names)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Evaluate Peano Lab's deterministic random-tactic baseline.",
    )
    parser.add_argument(
        "--goal",
        action="append",
        default=[],
        metavar="NAME",
        help="held-out ladder goal to evaluate (repeatable; default: all)",
    )
    parser.add_argument("--k", type=int, default=8, help="samples per goal (default: 8)")
    parser.add_argument(
        "--max-steps",
        type=int,
        default=16,
        help="maximum tactic proposals per sample (default: 16)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=20_260_727,
        help="root deterministic seed (default: 20260727)",
    )
    parser.add_argument(
        "--compact",
        action="store_true",
        help="emit single-line JSON instead of indented JSON",
    )
    parser.add_argument(
        "--list-goals",
        action="store_true",
        help="print the fixed held-out goal names and exit",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.list_goals:
        for name in HELD_OUT_LADDER_NAMES:
            print(name)
        return 0
    try:
        goals = _selected_goals(args.goal)
        report = evaluate(
            RandomPolicy(),
            goals,
            k=args.k,
            max_steps=args.max_steps,
            seed=args.seed,
        )
    except (TypeError, ValueError) as exc:
        parser.error(str(exc))
    print(report.json(indent=None if args.compact else 2))
    return 0


__all__ = [
    "EVAL_VERSION",
    "AttemptStatus",
    "EvalGoal",
    "Policy",
    "RandomPolicy",
    "HELD_OUT_LADDER_NAMES",
    "DEFAULT_HELD_OUT_GOALS",
    "HELD_OUT_GOAL_SET_SHA256",
    "AttemptResult",
    "GoalResult",
    "EvaluationReport",
    "evaluate",
    "build_parser",
    "main",
]


if __name__ == "__main__":
    raise SystemExit(main())
