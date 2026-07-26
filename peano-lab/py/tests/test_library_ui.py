"""M7 browser commands expose checked scripts and exact Lean stubs."""

from __future__ import annotations

from urllib.parse import unquote

import driver
from peano_lab.library.lean import LIVE_LEAN_PREFIX
from peano_lab.library.theorems import THEOREMS, get
from peano_lab.ui import data_library, prove


def test_pa_lib_lists_every_rung_and_opens_exact_replay_script() -> None:
    session = driver.LabSession()
    index = session.run("pa lib")

    assert index == data_library.render_index()
    assert f"{len(THEOREMS)} scripted theorems" in index
    assert all(spec.name in index for spec in THEOREMS)

    card = session.run("pa lib ADD_COMM")
    add_comm = get("add_comm")
    assert add_comm is not None
    assert card == data_library.render_theorem(add_comm)
    assert "Statement: ∀ x. ∀ y. x + y = y + x" in card
    assert "Temporary curried replay target:" in card
    assert "Generated dependency prelude:" in card
    assert "Authored tactic body:" in card
    assert "intro zero_add" in card
    assert "simp [add_succ_left, IH]" in card
    assert "Independent kernel check: PASS" in card

    direct = session.run("pa lib zero_add")
    assert "direct closed certificate; no library dependency cuts" in direct


def test_pa_lib_help_usage_and_unknown_name_are_final_text() -> None:
    session = driver.LabSession()

    assert "pa lean <name>" in session.run("pa lib help")
    assert "No library theorem 'missing'" in session.run("pa lib missing")
    assert session.run("pa prove lib") == (
        "Use `pa lib [name]` for the checked theorem ladder."
    )


def test_pa_lean_exports_exact_code_and_live_link() -> None:
    session = driver.LabSession()
    output = session.run("pa lean mul_eq_zero")
    capstone = get("mul_eq_zero")
    assert capstone is not None
    exported = data_library.lean_export(capstone)

    assert exported.code in output
    assert exported.live_url in output
    assert exported.live_url.startswith(LIVE_LEAN_PREFIX)
    assert unquote(exported.live_url.removeprefix(LIVE_LEAN_PREFIX)) == exported.code
    assert exported.code.count("sorry") == 1
    assert "Earlier checked Peano Lab dependencies: add_eq_zero_right" in exported.code
    assert "intro add_eq_zero_right" not in exported.code
    assert "`sorry` is an intentional proof stub" in output
    assert session.run("pa lean") == (
        "Usage: pa lean <theorem>; list names with `pa lib`."
    )
    assert "No library theorem 'missing'" in session.run("pa lean missing")


def test_library_commands_cannot_bypass_a_live_proof_owner() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    owner = prove.get_owner(session.webstate)

    output = session.run("pa lib add_comm")

    assert "unknown tactic 'pa'" in output
    assert prove.get_owner(session.webstate) is owner


def test_library_rendering_is_deterministic_and_browser_safe() -> None:
    session = driver.LabSession()
    outputs = [session.run("pa lib")]
    outputs.extend(session.run(f"pa lib {spec.name}") for spec in THEOREMS)

    assert all("\x1b" not in output for output in outputs)
    assert all("\u2028" not in output and "\u2029" not in output for output in outputs)
    assert session.run("pa lib") == outputs[0]
