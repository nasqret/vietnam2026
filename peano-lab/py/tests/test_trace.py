"""Focused tests for the binding version-1 JSONL trace contract."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass

import pytest

from peano_lab.engine.trace import TRACE_VERSION, TraceLogger, render_goal
from peano_lab.engine.state import Goal, MetaVar, start
from peano_lab.kernel.formulas import Eq, Forall, parse_formula_with_names
from peano_lab.kernel.terms import Add, Succ, Var, Zero


@dataclass(frozen=True)
class ExampleGoal:
    context: tuple[tuple[str, object], ...]
    target: object
    variables: tuple[str, ...] = ()


def _induction_goal() -> ExampleGoal:
    n_plus_zero = Eq(Add(Var(0), Zero()), Var(0))
    return ExampleGoal(
        context=(("IH", n_plus_zero),),
        target=Eq(Add(Succ(Var(0)), Zero()), Succ(Var(0))),
        variables=("n",),
    )


def test_goal_rendering_is_canonical_context_first_and_has_no_ansi() -> None:
    goal = ExampleGoal(
        context=(("\x1b[31mnew\x1b[0m", Eq(Var(0), Zero())),),
        target=Eq(Add(Var(0), Zero()), Var(0)),
        variables=("n",),
    )
    rendered = render_goal(goal)
    assert rendered == "n : ℕ, new : n = 0 ⊢ n + 0 = n"
    assert "\x1b" not in rendered


def test_defined_order_sugar_is_identical_in_goals_and_footer() -> None:
    target, names = parse_formula_with_names("a <= b")
    state = start(target, names)
    logger = TraceLogger(session_id="defined-order")

    record = logger.success(state, 0, "classical off", state)
    footer = logger.footer(
        qed=False,
        theorem=target,
        proof_size=0,
        names=state.variables,
    )

    # Free names are an index-to-name de Bruijn context, so declarations are
    # displayed outermost first even though the formula first mentions a.
    assert record["goals_before"] == ["b : ℕ, a : ℕ ⊢ a ≤ b"]
    assert record["goals_after"] == record["goals_before"]
    assert footer["theorem"] == "a ≤ b"


def test_success_record_has_exact_v1_field_order_and_canonical_unicode() -> None:
    logger = TraceLogger(session_id="session-0001")
    before = [ExampleGoal((), Forall(Eq(Add(Var(0), Zero()), Var(0))))]
    after = [_induction_goal()]

    record = logger.success(before, 0, "induction n", after)

    assert list(record) == [
        "v",
        "session",
        "step",
        "goals_before",
        "focus",
        "tactic",
        "goals_after",
        "status",
        "error",
    ]
    assert record == {
        "v": TRACE_VERSION,
        "session": "session-0001",
        "step": 1,
        "goals_before": ["⊢ ∀ x. x + 0 = x"],
        "focus": 0,
        "tactic": "induction n",
        "goals_after": ["n : ℕ, IH : n + 0 = n ⊢ S n + 0 = S n"],
        "status": "ok",
        "error": None,
    }
    assert "\\u22a2" not in logger.jsonl()


def test_failure_is_recorded_and_reuses_unchanged_before_goals() -> None:
    logger = TraceLogger(session_id="fixed")
    goals = [ExampleGoal((), Eq(Zero(), Succ(Zero())))]

    record = logger.failure(goals, 0, "refl", ValueError("the sides differ."))

    assert record["step"] == 1
    assert record["status"] == "error"
    assert record["error"] == "the sides differ."
    assert record["goals_after"] == record["goals_before"]
    assert logger.tactic_count == 1


def test_failed_application_cannot_claim_a_mutated_after_state() -> None:
    logger = TraceLogger(session_id="fixed")
    before = [ExampleGoal((), Eq(Zero(), Succ(Zero())))]
    changed = [ExampleGoal((), Eq(Zero(), Zero()))]
    with pytest.raises(ValueError, match="leave goals unchanged"):
        logger.record_tactic(before, 0, "refl", changed, error="failed")
    assert logger.records == ()


def test_records_collect_in_memory_and_stream_to_optional_text_sink() -> None:
    sink = io.StringIO()
    logger = TraceLogger(sink, session_id="repeatable-id")
    goal = [ExampleGoal((), Eq(Zero(), Zero()))]

    logger.success(goal, 0, "refl", [])
    logger.failure(goal, 0, "unknown", "unknown tactic.")
    footer = logger.footer(
        qed=True,
        theorem=Forall(Eq(Add(Var(0), Zero()), Var(0))),
        proof_size=12,
    )

    assert list(footer) == ["qed", "theorem", "proof_size", "tactic_count"]
    assert footer == {
        "qed": True,
        "theorem": "∀ x. x + 0 = x",
        "proof_size": 12,
        "tactic_count": 2,
    }
    assert sink.getvalue() == logger.jsonl()
    decoded = [json.loads(line) for line in sink.getvalue().splitlines()]
    assert decoded == list(logger.records)
    assert [record.get("step") for record in decoded[:2]] == [1, 2]


def test_no_tactics_may_follow_footer_and_footer_is_unique() -> None:
    logger = TraceLogger(session_id="fixed")
    logger.footer(qed=False, theorem="0 = 1", proof_size=0)
    with pytest.raises(RuntimeError, match="after the session footer"):
        logger.failure([ExampleGoal((), Eq(Zero(), Zero()))], 0, "oops", "failed")
    with pytest.raises(RuntimeError, match="already recorded"):
        logger.footer(qed=False, theorem="0 = 1", proof_size=0)


def test_metavariable_aliases_keep_identity_across_a_transition_and_session() -> None:
    first, second = MetaVar(1000), MetaVar(1001)
    before = [Goal((), Eq(first, Zero())), Goal((), Eq(second, Zero()))]
    after = [Goal((), Eq(second, Zero()))]
    logger = TraceLogger(session_id="stable-metas")

    record = logger.success(before, 0, "close first", after)
    assert "?t1" in record["goals_before"][0]
    assert "?t2" in record["goals_before"][1]
    assert "?t2" in record["goals_after"][0]

    following = logger.failure(after, 0, "retry", "still open")
    assert "?t2" in following["goals_before"][0]


def test_tactic_and_error_fields_are_ansi_free() -> None:
    logger = TraceLogger(session_id="ansi")
    goals = [ExampleGoal((), Eq(Zero(), Zero()))]
    record = logger.failure(
        goals,
        0,
        "\x1b[31mrefl\x1b[0m",
        "\x1b[1mbad tactic\x1b[0m",
    )
    assert record["tactic"] == "refl"
    assert record["error"] == "bad tactic"
    assert "\x1b" not in logger.jsonl()
