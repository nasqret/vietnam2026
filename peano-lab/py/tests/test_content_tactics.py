"""M6 tactic encyclopedia coverage and executable worked examples."""

from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

import driver
from peano_lab.engine.tactics import TACTIC_NAMES
from peano_lab.ui import data_tactics


EXPECTED_TACTICALS = (";", "<|>", "repeat", "first", "all_goals", "focus")
EXPECTED_AUTOMATION = ("norm_num", "ring", "auto", "hint")
EXPECTED_SURFACE_PRIMITIVES = tuple(
    name for name in TACTIC_NAMES if name != "norm_num"
) + ("use",)


def test_every_operational_surface_has_exactly_one_card() -> None:
    assert data_tactics.PRIMITIVE_NAMES == EXPECTED_SURFACE_PRIMITIVES
    assert data_tactics.TACTICAL_NAMES == EXPECTED_TACTICALS
    assert data_tactics.AUTOMATION_NAMES == EXPECTED_AUTOMATION

    expected = EXPECTED_SURFACE_PRIMITIVES + EXPECTED_TACTICALS + EXPECTED_AUTOMATION
    assert data_tactics.names() == expected
    assert len(data_tactics.TACTIC_CARDS) == len(expected) == 31
    assert len(data_tactics.TACTIC_MAP) == len(expected)


def test_every_card_has_all_required_teaching_fields() -> None:
    for card in data_tactics.TACTIC_CARDS:
        assert card.name
        assert card.kind in {"primitive", "tactical", "automation"}
        assert card.syntax
        assert card.summary
        assert card.goal_effect
        assert card.certificate_effect
        assert card.example_theorem
        assert card.example_commands
        assert card.common_errors
        assert all(command and "\n" not in command and "\r" not in command
                   for command in card.example_commands)
        assert all(error.endswith(".") for error in card.common_errors)


@pytest.mark.parametrize("card", data_tactics.TACTIC_CARDS, ids=lambda card: card.name)
def test_every_worked_example_reaches_checked_qed(card: data_tactics.TacticCard) -> None:
    session = driver.LabSession()
    started = session.run(f"pa prove {card.example_theorem}")
    assert "Peano Lab proof" in started
    assert "Parse error:" not in started

    for command in card.example_commands:
        output = session.run(command)
        assert "Tactic error:" not in output, (card.name, command, output)
        assert "QED check failed:" not in output, (card.name, command, output)

    finished = session.run("qed")
    assert "No open goals. QED." in finished, (card.name, finished)


def test_lookup_aliases_and_frozen_cards_are_safe_for_ui_use() -> None:
    assert data_tactics.lookup("intro") is data_tactics.TACTIC_MAP["intro"]
    assert data_tactics.lookup(" then ") is data_tactics.TACTIC_MAP[";"]
    assert data_tactics.lookup("orelse") is data_tactics.TACTIC_MAP["<|>"]
    assert data_tactics.lookup("INTRO") is None
    assert data_tactics.lookup(1) is None  # type: ignore[arg-type]

    with pytest.raises(FrozenInstanceError):
        data_tactics.TACTIC_CARDS[0].syntax = "changed"  # type: ignore[misc]


def test_renderers_are_complete_deterministic_and_terminal_safe() -> None:
    first_index = data_tactics.render_index()
    assert first_index == data_tactics.render_index()
    assert "Primitive tactics" in first_index
    assert "Tacticals" in first_index
    assert "Automation and advice" in first_index
    assert "\x1b" not in first_index
    assert "\n" not in first_index.replace("\r\n", "")

    for card in data_tactics.TACTIC_CARDS:
        rendered = data_tactics.render_card(card.name)
        assert rendered == data_tactics.render_card(card)
        assert f"Tactic: {card.name}" in rendered
        assert f"Syntax: {card.syntax}" in rendered
        assert "Goal effect:" in rendered
        assert "Certificate effect:" in rendered
        assert "Worked executable example:" in rendered
        assert f"pa prove {card.example_theorem}" in rendered
        assert "Common errors:" in rendered
        assert rendered.endswith(card.common_errors[-1])
        assert "\x1b" not in rendered
        assert "\n" not in rendered.replace("\r\n", "")

    assert data_tactics.render_card("missing") == (
        "No tactic named 'missing'. Type `pa tactic`."
    )
