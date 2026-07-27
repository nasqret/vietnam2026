"""M9 policy evaluation is deterministic and kernel judged."""

from __future__ import annotations

import importlib.util
import json
import random
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest

import peano_lab.engine.tactics as engine_tactics
from peano_lab.kernel.formulas import parse_formula


ROOT = Path(__file__).resolve().parents[3]
EVALUATOR = ROOT / "scripts" / "eval_peano_policy.py"
SPEC = importlib.util.spec_from_file_location("_peano_policy_evaluator", EVALUATOR)
assert SPEC is not None and SPEC.loader is not None
eval_policy = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = eval_policy
SPEC.loader.exec_module(eval_policy)


@dataclass(frozen=True)
class ScriptPolicy:
    commands: tuple[object, ...]
    name: str = "script"

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        sample: int,
        step: int,
        rng: random.Random,
    ):
        del goals_before, sample, rng
        return self.commands[step] if step < len(self.commands) else None


def _only_attempt(report):
    assert len(report.goals) == len(report.goals[0].attempts) == 1
    return report.goals[0].attempts[0]


def test_checked_proof_uses_external_original_target_and_exact_mode(monkeypatch) -> None:
    goal = eval_policy.EvalGoal("refl", "0 = 0", classical=False)
    calls: list[tuple[object, object]] = []
    real_checked_final = eval_policy.checked_surface_final

    def spy(state, original_target, *, classical=False, trace=None):
        calls.append((original_target, classical))
        return real_checked_final(
            state,
            original_target,
            classical=classical,
            trace=trace,
        )

    monkeypatch.setattr(eval_policy, "checked_surface_final", spy)
    report = eval_policy.evaluate(ScriptPolicy(("refl",)), (goal,), k=1)
    attempt = _only_attempt(report)

    assert attempt.status == "proof"
    assert attempt.proof_nodes == 1
    assert calls == [(parse_formula("0 = 0"), False)]
    assert report.to_dict()["judge"] == "checked_final(original_target, exact_mode)"


def test_policy_surface_can_reuse_a_checked_library_theorem() -> None:
    goal = eval_policy.EvalGoal(
        "library_reuse",
        "forall n m. n + m = m + n",
        classical=False,
    )

    report = eval_policy.evaluate(
        ScriptPolicy(("use add_comm", "exact add_comm")),
        (goal,),
        k=1,
    )

    attempt = _only_attempt(report)
    assert attempt.status == "proof"
    assert attempt.commands == ("use add_comm", "exact add_comm")
    assert attempt.proof_nodes is not None and attempt.proof_nodes > 0


@pytest.mark.parametrize(
    ("command", "status"),
    [
        ("use missing", "failing"),
        ("use add_comm under alias", "invalid"),
    ],
)
def test_policy_classifies_library_reuse_failures(command: str, status: str) -> None:
    goal = eval_policy.EvalGoal("library_reuse_failure", "0 = 0")

    report = eval_policy.evaluate(ScriptPolicy((command,)), (goal,), k=1)

    assert _only_attempt(report).status == status


def test_policy_observes_only_canonical_trace_goals() -> None:
    seen: list[tuple[tuple[str, ...], int, int, bool]] = []

    class RecordingPolicy:
        name = "recording"

        def propose(self, goals_before, *, sample, step, rng):
            seen.append((goals_before, sample, step, isinstance(rng, random.Random)))
            return "refl"

    report = eval_policy.evaluate(
        RecordingPolicy(),
        (eval_policy.EvalGoal("secret_name", "0 = 0"),),
        k=1,
    )

    assert _only_attempt(report).status == "proof"
    assert seen == [(("⊢ 0 = 0",), 0, 0, True)]


def test_policy_metavariable_aliases_stay_stable_for_the_whole_rollout() -> None:
    seen: list[tuple[str, ...]] = []
    commands = ("split", "exists ?", "focus 2 exists ?", "refl", "refl")

    class MetaPolicy:
        name = "stable-meta-aliases"

        def propose(self, goals_before, *, sample, step, rng):
            del sample, rng
            seen.append(goals_before)
            return commands[step]

    goal = eval_policy.EvalGoal(
        "two_witnesses", "(exists x. x = 0) /\\ (exists y. y = 0)"
    )
    attempt = _only_attempt(
        eval_policy.evaluate(MetaPolicy(), (goal,), k=1, max_steps=len(commands))
    )

    assert attempt.status == "proof"
    assert seen[-1] == ("⊢ ?t2 = 0",)


def test_policy_rng_depends_on_visible_formula_not_hidden_goal_name() -> None:
    draws: list[float] = []

    class DrawPolicy:
        name = "rng-observer"

        def propose(self, goals_before, *, sample, step, rng):
            del goals_before, sample, step
            draws.append(rng.random())
            return "refl"

    report = eval_policy.evaluate(
        DrawPolicy(),
        (
            eval_policy.EvalGoal("private_a", "0 = 0"),
            eval_policy.EvalGoal("private_b", "0 = 0"),
        ),
        k=1,
    )

    assert report.proved_goals == 2
    assert draws[0] == draws[1]


def test_exact_external_mode_controls_classical_certificate_authority() -> None:
    statement = "((0 = S 0 -> false) -> false) -> 0 = S 0"
    policy = ScriptPolicy(("intro h", "apply DNE", "exact h"))

    classical = _only_attempt(
        eval_policy.evaluate(
            policy,
            (eval_policy.EvalGoal("dne_on", statement, classical=True),),
            k=1,
        )
    )
    intuitionistic = _only_attempt(
        eval_policy.evaluate(
            policy,
            (eval_policy.EvalGoal("dne_off", statement, classical=False),),
            k=1,
        )
    )

    assert classical.status == "proof"
    assert intuitionistic.status == "failing"


def test_closed_but_kernel_invalid_certificate_is_not_a_proof() -> None:
    # This known adversarial route closes every engine hole, but the check-only
    # BotElim cannot synthesize below CongS.  The independent checker rejects it.
    goal = eval_policy.EvalGoal("bad_leaf", "false -> S (S 0) = S 0")
    policy = ScriptPolicy(("intro h", "congr", "cases h"))

    attempt = _only_attempt(
        eval_policy.evaluate(policy, (goal,), k=1, max_steps=3)
    )

    assert attempt.status == "invalid"
    assert attempt.commands == policy.commands
    assert attempt.proof_nodes is None
    assert attempt.error is not None and attempt.error.startswith("kernel rejection:")


def test_failing_tactic_and_step_limit_are_distinct(monkeypatch) -> None:
    goal = eval_policy.EvalGoal("impossible", "0 = S 0")

    failed = _only_attempt(
        eval_policy.evaluate(ScriptPolicy(("refl",)), (goal,), k=1)
    )
    limited = _only_attempt(
        eval_policy.evaluate(
            ScriptPolicy(("repeat assumption", "repeat assumption")),
            (goal,),
            k=1,
            max_steps=2,
        )
    )

    assert failed.status == "failing"
    assert failed.error is not None and failed.error.startswith("tactic error:")
    assert limited.status == "limit"
    assert limited.error == "step limit reached (2)"

    nested_auto = _only_attempt(
        eval_policy.evaluate(
            ScriptPolicy(("first [auto 1]",)),
            (goal,),
            k=1,
            max_steps=1,
        )
    )
    assert nested_auto.status == "limit"

    nested_choices = tuple(
        _only_attempt(
            eval_policy.evaluate(
                ScriptPolicy((command,)),
                (goal,),
                k=1,
                max_steps=1,
            )
        )
        for command in (
            "first [auto 1 | refl]",
            "auto 1 <|> refl",
            "repeat auto 1",
        )
    )
    assert all(attempt.status == "limit" for attempt in nested_choices)

    real_simplify = engine_tactics.simplify_formula

    def one_step(formula, simp_set):
        return real_simplify(formula, simp_set, max_steps=1)

    monkeypatch.setattr(engine_tactics, "simplify_formula", one_step)
    bounded_simp = _only_attempt(
        eval_policy.evaluate(
            ScriptPolicy(("simp",)),
            (
                eval_policy.EvalGoal(
                    "bounded_simp",
                    "(0 + 0) + (0 + 0) = 0",
                ),
            ),
            k=1,
            max_steps=1,
        )
    )
    assert bounded_simp.status == "limit"
    assert bounded_simp.error is not None
    assert "1-step resource limit" in bounded_simp.error

    spoofed = _only_attempt(
        eval_policy.evaluate(
            ScriptPolicy(("refl auto reached its depth/node limit after 7 checks.",)),
            (goal,),
            k=1,
            max_steps=1,
        )
    )
    assert spoofed.status == "failing"


def test_invalid_policy_output_and_session_control_never_claim_proof() -> None:
    goal = eval_policy.EvalGoal("refl", "0 = 0")

    class HostileText(str):
        def strip(self, *_args, **_kwargs):
            raise RuntimeError("policy-controlled str override ran")

    for proposed in (object(), HostileText("refl")):
        invalid = _only_attempt(
            eval_policy.evaluate(ScriptPolicy((proposed,)), (goal,), k=1)
        )
        assert invalid.status == "invalid"
        assert invalid.commands == ()
    session_word = _only_attempt(
        eval_policy.evaluate(ScriptPolicy(("qed",)), (goal,), k=1)
    )

    assert session_word.status == "invalid"
    assert session_word.commands == ("qed",)

    separators = ("\n", "\r", "\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029")
    for separator in separators:
        for proposed in (
            separator + "refl",
            "refl" + separator,
            "refl" + separator + "refl",
        ):
            multiline = _only_attempt(
                eval_policy.evaluate(ScriptPolicy((proposed,)), (goal,), k=1)
            )
            assert multiline.status == "invalid"
            assert multiline.commands == ()

    padded = " " * (eval_policy.MAX_COMMAND_CHARS + 1) + "refl"
    oversized = _only_attempt(
        eval_policy.evaluate(ScriptPolicy((padded,)), (goal,), k=1)
    )
    assert oversized.status == "invalid"
    assert oversized.commands == ()

    for command in ("exact syntax:", "refl unknown tactic"):
        spoofed = _only_attempt(
            eval_policy.evaluate(ScriptPolicy((command,)), (goal,), k=1)
        )
        assert spoofed.status == "failing"

    for command in (
        "not_a_tactic",
        "first [refl |]",
        "repeat simp not-a-set",
        "first [not_a_tactic | refl]",
    ):
        malformed = _only_attempt(
            eval_policy.evaluate(ScriptPolicy((command,)), (goal,), k=1)
        )
        assert malformed.status == "invalid"


class SamplePolicy:
    name = "sample-aware"

    def propose(self, goals_before, *, sample, step, rng):
        del goals_before, step, rng
        return "refl" if sample == 1 else "exact missing"


def test_pass_at_k_means_any_checked_sample_per_goal() -> None:
    goal = eval_policy.EvalGoal("refl", "0 = 0")
    report = eval_policy.evaluate(SamplePolicy(), (goal,), k=2, max_steps=1)

    assert [attempt.status for attempt in report.goals[0].attempts] == [
        "failing",
        "proof",
    ]
    assert report.proved_goals == 1
    assert report.pass_at_k == 1.0
    assert report.status_counts == {
        "proof": 1,
        "invalid": 0,
        "failing": 1,
        "limit": 0,
    }


def test_random_dummy_policy_is_repeatable_end_to_end() -> None:
    goal = eval_policy.EvalGoal("refl", "0 = 0")
    policy = eval_policy.RandomPolicy()
    assert all(command.split()[0] != "auto" for command in policy.commands)

    first = eval_policy.evaluate(policy, (goal,), k=12, max_steps=3, seed=73)
    second = eval_policy.evaluate(policy, (goal,), k=12, max_steps=3, seed=73)

    assert first == second
    assert first.json() == second.json()
    assert first.status_counts["proof"] >= 1
    assert sum(first.status_counts.values()) == 12
    assert all(attempt.commands for attempt in first.goals[0].attempts)


def test_heldout_v1_goal_set_is_literal_and_fingerprinted() -> None:
    assert eval_policy.HELD_OUT_LADDER_NAMES == (
        "le_trans",
        "le_antisymm",
        "le_total",
        "mul_eq_zero",
    )
    assert eval_policy.HELD_OUT_GOAL_SET_SHA256 == (
        "ea1b3039340033bac9d3bf4835cc8f09f5b0da6bc017b179793daab04faa4731"
    )


def test_cli_emits_stable_machine_readable_stats(capsys) -> None:
    arguments = [
        "--goal",
        "le_trans",
        "--k",
        "2",
        "--max-steps",
        "2",
        "--seed",
        "19",
        "--compact",
    ]

    assert eval_policy.main(arguments) == 0
    first = capsys.readouterr().out
    assert eval_policy.main(arguments) == 0
    second = capsys.readouterr().out

    assert first == second
    payload = json.loads(first)
    assert payload["v"] == 1
    assert payload["goal_count"] == 1
    assert payload["attempt_count"] == 2
    assert payload["judge"] == "checked_final(original_target, exact_mode)"
    assert payload["goal_set_sha256"]
    assert set(payload["status_counts"]) == {"proof", "invalid", "failing", "limit"}


def test_eval_inputs_are_closed_unique_and_exactly_typed() -> None:
    policy = eval_policy.RandomPolicy()
    open_goal = eval_policy.EvalGoal("open", "x = x")
    duplicate = eval_policy.EvalGoal("same", "0 = 0")

    try:
        eval_policy.evaluate(policy, (open_goal,), k=1)
    except ValueError as exc:
        assert "not closed" in str(exc)
    else:  # pragma: no cover - assertion spelling is clearer than pytest magic here
        raise AssertionError("an open evaluation statement was accepted")

    try:
        eval_policy.evaluate(policy, (duplicate, duplicate), k=1)
    except ValueError as exc:
        assert "unique" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("duplicate evaluation goal names were accepted")

    for bad_k in (True, 0):
        try:
            eval_policy.evaluate(policy, (duplicate,), k=bad_k)
        except ValueError:
            pass
        else:  # pragma: no cover
            raise AssertionError("a non-positive/exact k was accepted")
