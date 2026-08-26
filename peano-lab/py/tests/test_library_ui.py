"""Browser commands expose checked scripts and completed Lean certificates."""

from __future__ import annotations

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
    assert "direct closed certificate; no dependency-sharing Cut nodes" in direct


def test_pa_lib_index_parses_statements_without_replaying_certificates(
    monkeypatch,
) -> None:
    def forbidden_replay(_name: str):
        raise AssertionError("the library index must not replay certificates")

    monkeypatch.setattr(data_library, "replay", forbidden_replay)

    index = driver.LabSession().run("pa lib")

    assert f"{len(THEOREMS)} scripted theorems" in index
    assert all(spec.name in index for spec in THEOREMS)


def test_pa_lib_detail_still_requires_checked_replay(monkeypatch) -> None:
    calls: list[str] = []

    def rejected_replay(name: str):
        calls.append(name)
        raise RuntimeError("sentinel replay failure")

    monkeypatch.setattr(data_library, "replay", rejected_replay)

    output = driver.LabSession().run("pa lib add_comm")

    assert calls == ["add_comm"]
    assert output == "RuntimeError: sentinel replay failure"


def test_pa_lib_help_usage_and_unknown_name_are_final_text() -> None:
    session = driver.LabSession()

    assert "pa lean <name>" in session.run("pa lib help")
    assert "No library theorem 'missing'" in session.run("pa lib missing")
    assert session.run("pa prove lib") == (
        "Use `pa lib [name]` for the checked theorem ladder."
    )


def test_pa_lean_defaults_to_a_bounded_human_first_checked_presentation() -> None:
    session = driver.LabSession()
    output = session.run("pa lean mul_eq_zero")

    assert "Lean 4 independently checked theorem — mul_eq_zero" in output
    assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert "--format compact --package-dir" in output
    assert "pa lean exact mul_eq_zero" in output
    assert "pa lean full mul_eq_zero" in output
    assert LIVE_LEAN_PREFIX not in output
    assert len(output.encode("utf-8")) <= 15 * 1024
    assert session.run("pa lean") == (
        "Usage: pa lean <theorem>; list names with `pa lib`."
    )
    assert "No library theorem 'missing'" in session.run("pa lean missing")


def test_pa_lean_full_explicitly_exports_exact_code_without_invalid_live_link() -> None:
    session = driver.LabSession()
    output = session.run("pa lean full mul_eq_zero")
    capstone = get("mul_eq_zero")
    assert capstone is not None
    exported = data_library.lean_export(capstone)

    assert exported.code in output
    assert LIVE_LEAN_PREFIX not in output
    assert "sorry" not in exported.code
    assert "import PeanoLab.Codec" in exported.code
    assert "PeanoLab.Artifact.check_sound" in exported.code
    assert "Independently replayed Peano dependencies: add_eq_zero_right" in exported.code
    assert "intro add_eq_zero_right" not in exported.code
    assert "complete constructive certificate" in output


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
