"""The optional Alpha browser channel preserves Stable proof authority."""

from __future__ import annotations

import driver
from peano_lab.library import editions_v16 as alpha
from peano_lab.library.quadratic_reciprocity_stack import QR_ROOT_NAME
from peano_lab.ui import data_library


def test_alpha_index_reports_exact_current_evidence_without_proof_replay(
    monkeypatch,
) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("Alpha inventory must not load or replay any proof")

    monkeypatch.setattr(alpha, "replay", forbidden_replay)

    output = driver.LabSession().run("pa lib alpha")

    assert "immutable Alpha v16" in output
    assert "Enrolled statements: 1,673" in output
    assert "Stable closed: 432" in output
    assert "Alpha closed: 453" in output
    assert "Dependency-curried body only: 788" in output
    assert "Pending closure: 0" in output
    assert "Available for independently checked use: 885" in output
    assert "Newly promoted quadratic-reciprocity results: 315" in output
    assert alpha.ALPHA_V16_IDENTITY_SHA256 in output


def test_alpha_root_evidence_card_is_cheap_and_never_claims_stable_membership(
    monkeypatch,
) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("Alpha evidence cards do not independently replay")

    monkeypatch.setattr(alpha, "replay", forbidden_replay)

    output = driver.LabSession().run(f"pa lib alpha {QR_ROOT_NAME}")

    assert "Release evidence: alpha_closed" in output
    assert "Release membership: alpha_only" in output
    assert "Checked-use authority: YES" in output
    assert "This evidence card does not itself replay a proof." in output
    assert f"pa lib alpha check {QR_ROOT_NAME}" in output
    assert "Independent empty-context kernel check: PASS" not in output


def test_alpha_body_only_theorems_cannot_replay_or_export(monkeypatch) -> None:
    body = next(item for item in alpha.ALPHA_ENTRIES if not item.checked_use)

    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("body-only evidence must never reach replay")

    monkeypatch.setattr(alpha, "replay", forbidden_replay)
    session = driver.LabSession()

    inspection = session.run(f"pa lib alpha {body.spec.name}")
    attempted_check = session.run(f"pa lib alpha check {body.spec.name}")
    attempted_export = session.run(f"pa lean alpha {body.spec.name}")

    assert "Release evidence: body_checked" in inspection
    assert "Checked-use authority: NO" in inspection
    assert "Independent kernel check: DENIED" in attempted_check
    assert "requires a closed theorem certificate" in attempted_export


def test_alpha_explicit_verification_checks_actual_empty_context_certificate() -> None:
    name = alpha.QR_PROMOTED_NAMES[0]

    output = driver.LabSession().run(f"pa lib alpha check {name}")

    assert "Release evidence: alpha_closed" in output
    assert "Independent empty-context kernel check: PASS" in output
    assert f"pa lean alpha {name}" in output


def test_alpha_explicit_lean_export_translates_an_independently_checked_proof() -> None:
    name = alpha.QR_PROMOTED_NAMES[0]

    output = driver.LabSession().run(f"pa lean alpha {name}")

    assert f"Lean 4 independently checked theorem — {name}" in output
    assert "import PeanoLab.Codec" in output
    assert "PeanoLab.Artifact.check_sound" in output
    assert "sorry" not in output


def test_alpha_checked_listing_filters_body_only_without_replay(monkeypatch) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("listing must not check or load theorem proofs")

    monkeypatch.setattr(alpha, "replay", forbidden_replay)
    body = next(item for item in alpha.ALPHA_ENTRIES if not item.checked_use)

    listing = driver.LabSession().run("pa lib alpha checked")

    assert QR_ROOT_NAME in listing
    assert body.spec.name not in listing
    assert "Alpha evidence ledger:" in listing


def test_alpha_commands_do_not_change_default_public_library() -> None:
    session = driver.LabSession()

    session.run("pa lib alpha")

    assert session.run("pa lib") == data_library.render_index()
    assert f"No library theorem '{QR_ROOT_NAME}'" in session.run(
        f"pa lib {QR_ROOT_NAME}"
    )
    assert "pa lib alpha" in session.run("pa lib help")
    assert session.run("pa lean alpha") == (
        "Usage: pa lean alpha <theorem>; inspect `pa lib alpha`."
    )


def test_alpha_unknown_theorems_fail_without_changing_surface() -> None:
    session = driver.LabSession()

    assert "No Alpha v16 theorem 'missing'" in session.run("pa lib alpha missing")
    assert "No Alpha v16 theorem 'missing'" in session.run("pa lean alpha missing")
    assert session.run("pa lib alpha check") == "Usage: pa lib alpha check <theorem>."
