"""Executable regression for the readable local-reasoning parity proof."""

from __future__ import annotations

from pathlib import Path

import driver

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import parse_formula
from peano_lab.ui.prove import checked_surface_final, get_owner


REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "artifacts" / "triangular-even-readable.pa"


def test_readable_parity_script_replays_and_checks_its_original_goal() -> None:
    commands = tuple(
        line.strip()
        for line in SCRIPT.read_text(encoding="utf-8").splitlines()
        if line.strip()
    )
    assert commands[0].startswith("pa prove ")
    assert commands[-1] == "qed"
    assert any(command.startswith("have strong :") for command in commands)
    assert any(command.startswith("suffices normalize :") for command in commands)

    session = driver.LabSession()
    for command in commands[:-1]:
        result = session.run_result(command)
        assert result["failed"] is False, (command, result["out"])

    owner = get_owner(session.webstate)
    assert owner is not None and not owner.state.goals
    certificate = checked_surface_final(
        owner.state,
        owner.original_target,
        classical=owner.classical,
    )

    assert check((), certificate, owner.original_target)
    mutated = parse_formula("forall n. exists x. n * (n + 1) = 2 * x + 1")
    assert not check((), certificate, mutated)

    finished = session.run_result(commands[-1])
    assert finished["failed"] is False
    assert "No open goals. QED." in str(finished["out"])
