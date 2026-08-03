"""Post-QED browser shadow export is one-shot and never theorem authority."""

from __future__ import annotations

import pytest

import driver
from peano_lab.engine.state import proof_size
from peano_lab.kernel.artifact_codec import encode_artifact
from peano_lab.ui import prove


def _finish_reflexivity(session: driver.LabSession, theorem: str = "0 = 0") -> str:
    session.run(f"pa prove {theorem}")
    session.run("refl")
    return session.run("qed")


def test_authoritative_qed_queues_exact_original_target_artifact_once() -> None:
    session = driver.LabSession()
    session.run("pa prove forall n. n = n")
    session.run("intro n")
    session.run("refl")
    owner = prove.get_owner(session.webstate)
    assert owner is not None
    certificate = prove.checked_surface_final(owner.state, owner.original_target)
    fuel = prove.SHADOW_FUEL_MULTIPLIER * proof_size(certificate) + prove.SHADOW_FUEL_OFFSET

    output = session.run("qed")

    assert "No open goals. QED." in output
    assert session.pending_shadow_logic() == "ha"
    assert session.take_shadow_artifact() == encode_artifact(
        fuel, owner.original_target, certificate
    )
    assert session.pending_shadow_logic() == ""
    assert session.take_shadow_artifact() == b""


def test_failed_qed_and_non_qed_commands_export_nothing() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = S 0")

    assert "QED check failed" in session.run("qed")
    assert session.pending_shadow_logic() == ""
    assert session.take_shadow_artifact() == b""

    session.run("abort")
    session.run("help")
    assert session.take_shadow_artifact() == b""


def test_classical_qed_is_explicitly_labeled_for_the_classical_shadow_gate() -> None:
    session = driver.LabSession()
    theorem = "((0 = S 0 -> false) -> false) -> 0 = S 0"
    session.run(f"pa prove {theorem}")
    session.run("intro h")
    session.run("classical on")
    session.run("apply DNE")
    session.run("assumption")

    assert "No open goals. QED." in session.run("qed")
    assert session.pending_shadow_logic() == "classical"
    assert session.take_shadow_artifact().startswith(b'["peano-lab-v2",')


def test_later_command_discards_unconsumed_shadow_material() -> None:
    session = driver.LabSession()
    assert "No open goals. QED." in _finish_reflexivity(session)
    assert session.pending_shadow_logic() == "ha"

    session.run("help")

    assert session.pending_shadow_logic() == ""
    assert session.take_shadow_artifact() == b""


def test_encoder_failure_cannot_retract_an_already_reported_qed(monkeypatch) -> None:
    session = driver.LabSession()
    output = _finish_reflexivity(session)

    def fail_encoding(*_args, **_kwargs):
        raise RuntimeError("synthetic export failure")

    monkeypatch.setattr(prove, "encode_artifact_bounded", fail_encoding)

    assert "No open goals. QED." in output
    with pytest.raises(RuntimeError, match="synthetic"):
        session.take_shadow_artifact()
    assert session.pending_shadow_logic() == ""


def test_browser_limit_is_lower_than_the_live_certificate_resource_ceiling() -> None:
    assert prove.MAX_SHADOW_ARTIFACT_BYTES == 16 * 1024 * 1024
