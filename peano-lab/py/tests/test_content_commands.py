"""M6 browser command integration for the executable teaching cards."""

from __future__ import annotations

import driver
from peano_lab.ui import data_kb, data_tactics, prove, tutorial


def test_pa_tactic_lists_and_renders_the_exact_encyclopedia() -> None:
    session = driver.LabSession()

    index = session.run("pa tactic")
    assert index == data_tactics.render_index()
    for name in data_tactics.names():
        assert name in index

    card = session.run("pa tactic induction")
    assert card == data_tactics.render_card("induction")
    assert "Goal effect:" in card
    assert "Certificate effect:" in card
    assert "Worked executable example:" in card
    assert "Common errors:" in card

    assert session.run("pa tactic then") == data_tactics.render_card(";")
    assert session.run("pa tactic missing") == (
        "No tactic named 'missing'. Type `pa tactic`."
    )
    assert session.run("pa prove tactic") == (
        "Use `pa tactic [name]` for the executable M6 encyclopedia."
    )


def test_kb_top_level_and_pa_alias_share_lookup_search_and_help() -> None:
    session = driver.LabSession()

    assert session.run("kb") == data_kb.render_index()
    assert session.run("pa kb") == data_kb.render_index()
    assert session.run("KB LIST") == data_kb.render_index()
    assert session.run("pa HELP") == session.run("pa help")
    assert session.run("kb pa3") == data_kb.render_card("pa3")
    assert session.run("pa kb pa3") == data_kb.render_card("pa3")
    assert session.run("help kb") == session.run("pa kb help")

    searched = session.run("kb search de bruijn")
    assert searched == data_kb.render_index(data_kb.search_cards("de bruijn"))
    assert "de-bruijn-indices" in searched
    assert "de-bruijn-criterion" in searched
    assert "simp-termination" in searched
    assert session.run("PA KB SEARCH de bruijn") == searched
    assert session.run("kb search") == "Usage: kb search <words>"
    assert "No knowledge-base card" in session.run("kb absent")


def test_card_commands_cannot_bypass_an_active_proof_owner() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    owner = prove.get_owner(session.webstate)
    assert owner is not None

    output = session.run("kb pa1")

    assert "unknown tactic 'kb'" in output
    assert prove.get_owner(session.webstate) is owner


def test_driver_routes_a_tutorial_owner_and_enter_reaches_checked_qed() -> None:
    session = driver.LabSession()
    assert session.run("tutorial") == session.run("pa tutorial")
    started = session.run("pa tutorial add_comm")
    assert "Prove add_comm by hand" in started
    assert tutorial.is_active(session.webstate)
    assert not prove.is_active(session.webstate)

    before = dict(session.webstate[tutorial.K_ACTIVE])
    refused = session.run("pa axioms")
    assert "owns the complete line" in refused
    assert session.webstate[tutorial.K_ACTIVE] == before

    for _ in range(40):
        if not tutorial.is_active(session.webstate):
            break
        output = session.run("")
    else:
        raise AssertionError("ENTER-only tutorial did not terminate")

    assert "Tutorial complete:" in output
    assert session.webstate[tutorial.K_LAST_RUN]["checked_qed"] is True
    assert session.webstate[tutorial.K_LAST_RUN]["commands"][0] == (
        "pa prove forall n m. n + m = m + n"
    )


def test_proof_owner_has_priority_over_tutorial_commands() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    owner = prove.get_owner(session.webstate)

    output = session.run("pa tutorial add_comm")

    assert "unknown tactic 'pa'" in output
    assert prove.get_owner(session.webstate) is owner
    assert not tutorial.is_active(session.webstate)


def test_all_content_rendering_is_browser_safe_and_deterministic() -> None:
    session = driver.LabSession()
    outputs = [session.run("pa tactic"), session.run("kb")]
    outputs.extend(session.run(f"pa tactic {name}") for name in data_tactics.names())
    outputs.extend(session.run(f"kb {card.slug}") for card in data_kb.CARDS)

    assert all("\x1b" not in output for output in outputs)
    assert all("\u2028" not in output and "\u2029" not in output for output in outputs)
    assert session.run("pa tactic") == outputs[0]
    assert session.run("kb") == outputs[1]
