"""The optional Alpha browser channel preserves Stable proof authority."""

from __future__ import annotations

import driver
import pytest
from peano_lab.library import editions_v16 as historical_alpha
from peano_lab.library import editions_v19 as alpha
from peano_lab.library.alpha_enrollment_v19 import (
    LINEAR_CONGRUENCE_ROOT_NAME,
    PRIME_TWO_SQUARE_ROOT_NAME,
    PRIMES_ONE_MOD_FOUR_ROOT_NAME,
    PYTHAGOREAN_V19_ROOT_NAMES,
)
from peano_lab.library.quadratic_reciprocity_stack import QR_ROOT_NAME
from peano_lab.ui import data_library


def test_alpha_index_reports_exact_current_evidence_without_proof_replay(
    monkeypatch,
) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("Alpha inventory must not load or replay any proof")

    monkeypatch.setattr(alpha, "replay", forbidden_replay)

    output = driver.LabSession().run("pa lib alpha")

    assert "immutable Alpha v19" in output
    assert "Enrolled statements: 1,737" in output
    assert "Stable closed: 432" in output
    assert "Alpha closed: 1,305" in output
    assert "Dependency-curried body only: 0" in output
    assert "Pending closure: 0" in output
    assert "Available for independently checked use: 1,737" in output
    assert "Previously promoted quadratic-reciprocity results: 315" in output
    assert "Previously promoted supplementary-law results: 31" in output
    assert "Previously promoted five-campaign flagship results: 673" in output
    assert "Newly closed legacy residual results: 84" in output
    assert "New constructive campaign results: 64" in output
    assert alpha.ALPHA_V19_IDENTITY_SHA256 in output


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


def test_alpha_supplementary_roots_have_checked_cards_without_replaying(monkeypatch) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("supplementary inventory must not load or replay a proof")

    monkeypatch.setattr(alpha, "replay", forbidden_replay)
    session = driver.LabSession()

    for name in alpha.v18.v17.SUPPLEMENTARY_ROOT_NAMES:
        output = session.run(f"pa lib alpha {name}")
        assert "Release evidence: alpha_closed" in output
        assert "Release membership: alpha_only" in output
        assert "Checked-use authority: YES" in output
        assert "Independent empty-context kernel check: PASS" not in output


def test_all_six_flagship_roots_have_checked_cards_without_replaying(monkeypatch) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("flagship evidence cards never replay large proof roots")

    monkeypatch.setattr(alpha, "replay", forbidden_replay)
    session = driver.LabSession()

    for name in alpha.v18.FLAGSHIP_ROOT_NAMES:
        output = session.run(f"pa lib alpha {name}")
        assert "Release evidence: alpha_closed" in output
        assert "Release membership: alpha_only" in output
        assert "Checked-use authority: YES" in output
        assert "Independent empty-context kernel check: PASS" not in output


def test_all_historical_body_only_theorems_now_have_checked_cards(monkeypatch) -> None:
    historical = next(item for item in alpha.v18.ALPHA_ENTRIES if not item.checked_use)

    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("historically residual evidence cards never replay a proof")

    monkeypatch.setattr(alpha, "replay", forbidden_replay)
    session = driver.LabSession()

    inspection = session.run(f"pa lib alpha {historical.spec.name}")
    preview = session.run(f"pa lean alpha {historical.spec.name}")

    assert "Release evidence: alpha_closed" in inspection
    assert "Checked-use authority: YES" in inspection
    assert "Release edition: Alpha v19." in preview
    assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in preview
    assert historical.evidence is alpha.v18.EvidenceStatus.BODY_CHECKED
    assert not historical.checked_use


@pytest.mark.parametrize(
    "name",
    (
        LINEAR_CONGRUENCE_ROOT_NAME,
        PRIMES_ONE_MOD_FOUR_ROOT_NAME,
        PRIME_TWO_SQUARE_ROOT_NAME,
        *PYTHAGOREAN_V19_ROOT_NAMES,
        "prime_power_valuation_exists",
        "prime_power_valuation_functional",
    ),
)
def test_new_campaign_goals_and_complete_valuation_have_checked_cards_without_replay(
    monkeypatch,
    name: str,
) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("campaign evidence cards must never load or replay proofs")

    monkeypatch.setattr(alpha, "replay", forbidden_replay)

    output = driver.LabSession().run(f"pa lib alpha {name}")

    assert f"{name} — Alpha v19 theorem evidence" in output
    assert "Release evidence: alpha_closed" in output
    assert "Release membership: alpha_only" in output
    assert "Checked-use authority: YES" in output
    assert "Independent empty-context kernel check: PASS" not in output


@pytest.mark.parametrize(
    "name",
    (
        LINEAR_CONGRUENCE_ROOT_NAME,
        PRIMES_ONE_MOD_FOUR_ROOT_NAME,
        PRIME_TWO_SQUARE_ROOT_NAME,
        *PYTHAGOREAN_V19_ROOT_NAMES,
        "prime_power_valuation_exists",
    ),
)
def test_new_campaign_lean_previews_are_bounded_and_never_use_synthetic_bundle_targets(
    monkeypatch,
    name: str,
) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("safe campaign previews must not open or reconstruct proofs")

    monkeypatch.setattr(alpha, "replay", forbidden)
    monkeypatch.setattr(alpha, "_checked_campaign_bundle", forbidden)

    output = driver.LabSession().run(f"pa lean alpha {name}")

    assert f"Lean 4 independently checked theorem — {name}" in output
    assert "Release edition: Alpha v19." in output
    assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in output
    assert "--edition alpha --format compact" in output
    assert "--proof-bundle" not in output
    assert len(output.encode("utf-8")) <= 15 * 1024


@pytest.mark.parametrize(
    ("name", "artifact"),
    (
        ("lucas_theorem", "lucas-proof-bundle-v1.json"),
        ("bertrand_strict", "bertrand-proof-bundle-v1.json"),
        ("four_square_lagrange", "four-square-proof-bundle-v1.json"),
        (
            "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
            "two-square-proof-bundle-v1.json",
        ),
    ),
)
def test_historical_single_root_flagships_keep_their_exact_matching_artifact_commands(
    monkeypatch,
    name: str,
    artifact: str,
) -> None:
    monkeypatch.setattr(
        alpha,
        "replay",
        lambda *_args, **_kwargs: pytest.fail("flagship previews must never replay"),
    )

    output = driver.LabSession().run(f"pa lean alpha {name}")

    assert (
        "--proof-bundle research/arithmetic-library/artifacts/" + artifact
    ) in output
    assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in output


def test_alpha_explicit_verification_checks_actual_empty_context_certificate() -> None:
    name = historical_alpha.QR_PROMOTED_NAMES[0]

    output = driver.LabSession().run(f"pa lib alpha check {name}")

    assert "Release evidence: alpha_closed" in output
    assert "Independent empty-context kernel check: PASS" in output
    assert f"pa lean alpha {name}" in output


@pytest.mark.parametrize(
    "name",
    (
        QR_ROOT_NAME,
        *alpha.v18.v17.SUPPLEMENTARY_ROOT_NAMES,
        *alpha.v18.FLAGSHIP_ROOT_NAMES,
        PRIMES_ONE_MOD_FOUR_ROOT_NAME,
        PRIME_TWO_SQUARE_ROOT_NAME,
    ),
)
def test_large_alpha_browser_kernel_audits_fail_safely_before_proof_loading(
    monkeypatch,
    name: str,
) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("a huge Alpha root must not load a browser proof")

    monkeypatch.setattr(alpha, "replay", forbidden_replay)

    output = driver.LabSession().run(f"pa lib alpha check {name}")

    assert "Release evidence: alpha_closed" in output
    assert "Checked-use authority: YES" in output
    assert "browser replay blocked for safety" in output
    assert "dependency closure exceeds 128 theorem entries" in output
    assert "no proof certificate was loaded" in output
    assert "Independent empty-context kernel check: PASS" not in output


def test_alpha_explicit_lean_export_translates_an_independently_checked_proof() -> None:
    name = historical_alpha.QR_PROMOTED_NAMES[0]

    output = driver.LabSession().run(f"pa lean alpha {name}")

    assert f"Lean 4 independently checked theorem — {name}" in output
    assert "import PeanoLab.Codec" in output
    assert "PeanoLab.Artifact.check_sound" in output
    assert "sorry" not in output


def test_alpha_checked_listing_includes_every_residual_and_new_theorem_without_replay(
    monkeypatch,
) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("listing must not check or load theorem proofs")

    monkeypatch.setattr(alpha, "replay", forbidden_replay)
    listing = driver.LabSession().run("pa lib alpha checked")

    assert QR_ROOT_NAME in listing
    assert "cell_list_valid_nil" in listing
    assert "prime_power_valuation_exists" in listing
    assert LINEAR_CONGRUENCE_ROOT_NAME in listing
    assert PRIMES_ONE_MOD_FOUR_ROOT_NAME in listing
    assert PRIME_TWO_SQUARE_ROOT_NAME in listing
    assert PYTHAGOREAN_V19_ROOT_NAMES[-1] in listing
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

    assert "No Alpha v19 theorem 'missing'" in session.run("pa lib alpha missing")
    assert "No Alpha v19 theorem 'missing'" in session.run("pa lean alpha missing")
    assert session.run("pa lib alpha check") == "Usage: pa lib alpha check <theorem>."
