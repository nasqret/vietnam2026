"""M4 bounded automation, replayable traces, and kernel-guarded leaves."""

from __future__ import annotations

import pytest

from peano_lab.engine.search import auto, search
from peano_lab.engine.state import ProofState, start
from peano_lab.engine.tactics import TacticError, apply_tactic, checked_final
from peano_lab.engine.trace import TraceLogger
from peano_lab.kernel.checker import check, check_classical
from peano_lab.kernel.formulas import Eq, parse_formula
from peano_lab.kernel.terms import Succ, Zero


ZERO = Zero()
ONE = Succ(ZERO)

FIRST_FOUR = (
    "forall n. 0 + n = n",
    "forall n m. S n + m = S (n + m)",
    "forall n m. n + m = m + n",
    "forall a b c. (a + b) + c = a + (b + c)",
)


def _snapshot(state: ProofState) -> tuple[object, ...]:
    return state.goals, state.partial, state.history, dict(state.subst)


@pytest.mark.parametrize("source", FIRST_FOUR)
def test_auto5_closes_the_first_four_ladder_theorems_from_cold(source: str) -> None:
    target = parse_formula(source)
    initial = start(target)
    logger = TraceLogger(session_id=f"auto-{FIRST_FOUR.index(source)}")

    state = auto(initial, "5", trace=logger)
    certificate = checked_final(state, target, trace=logger)

    assert check((), certificate, target)
    assert state.is_done()
    tactic_records = logger.records[:-1]
    assert tactic_records
    assert all(record["status"] == "ok" for record in tactic_records)
    assert tactic_records[0]["goals_before"]
    assert tactic_records[-1]["goals_after"] == []
    for earlier, later in zip(tactic_records, tactic_records[1:]):
        assert earlier["goals_after"] == later["goals_before"]
    assert len(state.history) == logger.tactic_count
    assert logger.records[-1]["qed"] is True


def test_search_is_deterministic_and_does_not_publish_speculative_history() -> None:
    target = parse_formula("forall n. 0 + n = n")
    initial = start(target)
    before = _snapshot(initial)

    first = search(initial, 5)
    second = search(initial, 5)

    assert first.status == second.status == "found"
    assert first.commands == second.commands
    assert first.checked == second.checked
    assert _snapshot(initial) == before

    replayed = auto(initial, "5")
    assert len(replayed.history) == len(first.commands)
    assert [step.tactic for step in replayed.history] == [
        command.tactic for command in first.commands
    ]


def test_invalid_goals_closed_leaf_is_rejected_and_search_backtracks() -> None:
    # `intro h; congr; cases h` closes every engine hole but places the
    # check-only BotElim below a synthesizing CongS, so the kernel rejects it.
    # Search must continue to a certificate-valid ex-falso route.
    target = parse_formula("false -> S (S 0) = S 0")
    state = auto(start(target), "5")
    certificate = checked_final(state, target)

    assert check((), certificate, target)


def test_later_sibling_can_backtrack_an_earlier_shared_meta_choice() -> None:
    target = parse_formula(
        "0 = 0 -> 1 = 1 -> "
        "(forall x. x = x -> x = 0 -> 0 = S 0) -> 0 = S 0"
    )
    state = start(target)
    for name in ("h0", "h1", "h"):
        state = apply_tactic(state, "intro", name)

    result = search(state, 3)
    assert result.status == "found"
    completed = auto(state, "3")
    certificate = checked_final(completed, target)
    assert check((), certificate, target)


def test_depth_and_node_exhaustion_are_honest_limits() -> None:
    inductive = start(parse_formula("forall n. 0 + n = n"))
    assert search(inductive, 1).status == "limit"

    disjunction = start(parse_formula("0 = 0 \\/ 0 = 0"))
    for nodes in (1, 2):
        result = search(disjunction, 2, max_nodes=nodes)
        assert result.status == "limit"
        assert result.checked == nodes
        assert result.commands == ()

    impossible = search(start(Eq(ZERO, ONE)), 5)
    # PA2 can keep proposing ever-larger successor premises, so bounded
    # search honestly reports a non-verdict rather than unprovability.
    assert impossible.status == "limit"
    assert impossible.commands == ()


def test_failed_auto_is_transactional_and_has_one_unchanged_goal_trace() -> None:
    initial = start(Eq(ZERO, ONE))
    before = _snapshot(initial)
    logger = TraceLogger(session_id="auto-failure")

    with pytest.raises(TacticError, match="depth/node limit|found no proof"):
        auto(initial, "5", trace=logger)

    assert _snapshot(initial) == before
    assert len(logger.records) == 1
    record = logger.records[0]
    assert record["tactic"] == "auto 5"
    assert record["status"] == "error"
    assert record["goals_after"] == record["goals_before"]


@pytest.mark.parametrize("args", ["0", "-1", "1 2", "five", 5])
def test_auto_rejects_malformed_depth_transactionally_and_traces_it(args: object) -> None:
    initial = start(Eq(ZERO, ZERO))
    before = _snapshot(initial)
    logger = TraceLogger(session_id="bad-auto-depth")

    with pytest.raises(TacticError, match="syntax"):
        auto(initial, args, trace=logger)  # type: ignore[arg-type]

    assert _snapshot(initial) == before
    assert logger.records[-1]["status"] == "error"


@pytest.mark.parametrize(
    ("keyword", "value", "message"),
    [
        ("max_depth", True, "positive integer"),
        ("max_depth", 0, "positive integer"),
        ("max_nodes", True, "positive integer"),
        ("max_nodes", 0, "positive integer"),
        ("classical", 1, "Boolean"),
    ],
)
def test_search_rejects_non_exact_resource_and_authority_values(
    keyword: str, value: object, message: str
) -> None:
    options = {"max_depth": 5, "max_nodes": 100, "classical": False}
    options[keyword] = value
    with pytest.raises(ValueError, match=message):
        search(start(Eq(ZERO, ZERO)), **options)  # type: ignore[arg-type]


def test_auto_on_a_completed_state_is_an_explicit_unchanged_event() -> None:
    target = Eq(ZERO, ZERO)
    completed = apply_tactic(start(target), "refl")
    logger = TraceLogger(session_id="already-done")

    result = auto(completed, trace=logger)

    assert result is completed
    assert logger.records[0]["tactic"] == "auto 5"
    assert logger.records[0]["status"] == "ok"
    assert logger.records[0]["goals_before"] == logger.records[0]["goals_after"] == []


def test_auto_uses_dne_only_with_external_classical_authority() -> None:
    target = parse_formula("((0 = S 0 -> false) -> false) -> 0 = S 0")
    initial = start(target)

    assert search(initial, 5).status != "found"
    result = search(initial, 5, classical=True)
    assert result.status == "found"
    assert any(command.args == "DNE" for command in result.commands)

    state = auto(initial, "5", classical=True)
    certificate = checked_final(state, target, classical=True)
    assert check_classical((), certificate, target)
    assert not check((), certificate, target)


def test_search_rejects_a_non_state() -> None:
    with pytest.raises(TypeError, match="valid exact ProofState"):
        search(object())  # type: ignore[arg-type]


def test_search_rejects_broken_goal_hole_invariants_and_false_done_states() -> None:
    initial = start(Eq(ZERO, ZERO))
    no_hole = ProofState(
        initial.goals,
        apply_tactic(initial, "refl").partial,
        (),
        initial.target,
    )
    dangling_hole = ProofState((), initial.partial, (), initial.target)

    for malformed in (no_hole, dangling_hole):
        with pytest.raises(TypeError, match="valid exact ProofState"):
            search(malformed)

    false_done = ProofState(
        (),
        apply_tactic(start(Eq(ZERO, ZERO)), "refl").partial,
        (),
        Eq(ZERO, ONE),
    )
    assert search(false_done).status == "none"


def test_huge_requested_depth_hits_an_internal_limit_without_recursion_crash() -> None:
    initial = start(Eq(ZERO, ONE))
    before = _snapshot(initial)
    result = search(initial, 100_000, max_nodes=500)
    assert result.status == "limit"

    logger = TraceLogger(session_id="huge-auto-depth")
    with pytest.raises(TacticError, match="limit"):
        auto(initial, "100000", max_nodes=500, trace=logger)
    assert _snapshot(initial) == before
    assert logger.records[-1]["status"] == "error"
