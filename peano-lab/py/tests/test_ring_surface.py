"""M12 browser/session wiring for certificate-producing ``ring``."""

from __future__ import annotations

import driver
import pytest
from peano_lab.engine.ring import RING_LAW_NAMES
from peano_lab.ui import prove


def _owner(session: driver.LabSession) -> prove.ProofSession:
    owner = prove.get_owner(session.webstate)
    assert owner is not None
    return owner


def test_surface_ring_replays_the_exact_basis_and_traces_one_checked_step(
    monkeypatch,
) -> None:
    calls: list[str] = []
    real_replay = prove.replay

    def spy(name: str):
        calls.append(name)
        return real_replay(name)

    monkeypatch.setattr(prove, "replay", spy)
    session = driver.LabSession()
    session.run("pa prove forall n m. n + m = m + n")
    session.run("intro n")
    session.run("intro m")

    assert "No open goals" in session.run("ring")
    owner = _owner(session)
    assert calls == list(RING_LAW_NAMES)
    assert owner.state.history[-1].tactic == "ring"
    assert owner.trace.records[-1]["tactic"] == "ring"
    assert owner.trace.records[-1]["status"] == "ok"
    assert "No open goals. QED." in session.run("qed")


def test_surface_ring_undo_restores_the_exact_pre_normalization_state() -> None:
    session = driver.LabSession()
    session.run("pa prove (x + 1) * (x + 1) = x * x + 2 * x + 1")
    before = _owner(session).state

    assert "No open goals" in session.run("ring")
    session.run("undo")

    assert _owner(session).state is before


def test_ring_failures_are_traced_and_leave_the_exact_state_unchanged() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 1")
    before = _owner(session).state

    output = session.run("ring")

    owner = _owner(session)
    assert "different polynomial normal forms" in output
    assert owner.state is before
    assert owner.trace.records[-1]["tactic"] == "ring"
    assert owner.trace.records[-1]["status"] == "error"


def test_surface_time_budget_starts_before_basis_replay(monkeypatch) -> None:
    readings = iter((0.0, 6.0))
    monkeypatch.setattr(prove, "monotonic", lambda: next(readings, 6.0))
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    before = _owner(session).state

    output = session.run("ring")

    owner = _owner(session)
    assert "`ring` exceeded its 5-second time limit" in output
    assert owner.state is before
    assert owner.trace.records[-1]["status"] == "error"


def test_ring_is_zero_argument_and_syntax_errors_do_not_enter_orelse() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    before = _owner(session).state

    output = session.run("ring now <|> refl")

    assert "`ring` takes no arguments" in output
    assert _owner(session).state is before


def test_ring_participates_in_surface_tacticals_and_inactive_grammar() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0 /\\ 1 = 1")
    session.run("split")

    assert "No open goals" in session.run("all_goals ring")
    owner = _owner(session)
    assert owner.trace.records[-1]["tactic"] == "all_goals ring"
    assert "QED." in session.run("qed")

    inactive = driver.LabSession()
    assert "No proof is in progress" in inactive.run("pa prove ring")


def test_odd_square_induction_closes_interactively_and_qed_checks_original() -> None:
    session = driver.LabSession()
    commands = (
        "pa prove forall n. exists x. (2 * n + 1) * (2 * n + 1) = 8 * x + 1",
        "induction n",
        "exists 0",
        "ring",
        "cases IH",
        "exists x + S n",
        "trans ((2 * n + 1) * (2 * n + 1)) + (8 * S n)",
        "ring",
        "rewrite IH_witness",
        "ring",
    )

    for command in commands:
        output = session.run(command)
        assert not output.startswith(("Parse error:", "Tactic error:")), output

    assert _owner(session).state.is_done()
    finished = session.run("qed")
    assert "No open goals. QED." in finished
    assert (
        "Theorem: ∀ x. ∃ y. (2 · x + 1) · (2 · x + 1) = 8 · y + 1"
        in finished
    )
    assert not prove.is_active(session.webstate)


@pytest.mark.parametrize(
    "target",
    (
        (
            "(2 * S n + 1) * (2 * S n + 1) = "
            "(2 * n + 1) * (2 * n + 1) + 7 * S n"
        ),
        "8 * x + 1 + 8 * S n = 8 * (x + S n) + 2",
        "8 * x + 1 + 8 * S n = 8 * (x + n) + 1",
    ),
)
def test_mutated_odd_square_coefficients_fail_transactionally(target: str) -> None:
    session = driver.LabSession()
    session.run(f"pa prove {target}")
    before = _owner(session).state

    output = session.run("ring")

    assert "different polynomial normal forms" in output
    assert _owner(session).state is before


def test_ring_does_not_turn_a_conditional_hypothesis_into_an_oracle() -> None:
    session = driver.LabSession()
    session.run("pa prove x = 0 -> x + 1 = 1")
    session.run("intro h")
    before = _owner(session).state

    output = session.run("ring")

    assert "different polynomial normal forms" in output
    assert _owner(session).state is before
