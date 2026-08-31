"""Lean browser views stay theorem-first, honest, bounded, and release-aware."""

from __future__ import annotations

import driver
import pytest

from peano_lab.library import editions_v19 as alpha
from peano_lab.library import editions_v33 as current_alpha
from peano_lab.library.lean import LIVE_LEAN_PREFIX, formula_to_lean
from peano_lab.library.theorems import get, replay
from peano_lab.ui import data_library


def _forbid_current_alpha_proofs(monkeypatch, forbidden):
    # Current and inherited proof providers must all remain unused by previews.
    for edition, provider in ((current_alpha, "research"), (current_alpha.v32.v31, "completed_lower")):
        monkeypatch.setattr(edition, "replay", forbidden)
        monkeypatch.setattr(edition, "_checked_" + provider + "_bundle", forbidden)
        monkeypatch.setattr(edition, "checked_" + provider + "_bundle", forbidden)
    monkeypatch.setattr(current_alpha.v32.v31.v30, "replay", forbidden)


@pytest.mark.parametrize("command", ("zero_add", "compact zero_add", "pretty zero_add"))
def test_compact_view_is_theorem_first_and_truthful_about_verification(
    command: str,
) -> None:
    output = driver.LabSession().run(f"pa lean {command}")

    assert output.splitlines()[0] == "Lean 4 independently checked theorem — zero_add"
    assert "Authenticated release evidence: stable_closed." in output
    assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert "import PeanoLab.Codec" in output
    assert "PeanoLab.Artifact.check_sound" in output
    assert "--format compact --package-dir artifacts/lean/zero_add --verify" in output
    assert LIVE_LEAN_PREFIX not in output
    assert "sorry" not in output
    assert len(output.encode("utf-8")) <= 15 * 1024


def test_large_stable_theorem_preview_never_replays_or_builds_a_certificate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("a safe theorem preview must not replay or export a proof")

    monkeypatch.setattr(data_library, "replay", forbidden)
    monkeypatch.setattr(data_library, "lean_export", forbidden)
    monkeypatch.setattr(data_library, "export_checked_theorem", forbidden)

    output = driver.LabSession().run("pa lean prime_unbounded")

    assert output.startswith("Lean 4 independently checked theorem — prime_unbounded")
    assert "Prime" in output
    assert "Certificate proof nodes: not loaded" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert len(output.encode("utf-8")) <= 15 * 1024


@pytest.mark.parametrize("mode", ("compact", "exact", "tactics"))
def test_alpha_inspection_modes_never_replay_or_export_certificates(
    monkeypatch: pytest.MonkeyPatch,
    mode: str,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Alpha inspection must never replay its large proof roots")

    monkeypatch.setattr(alpha, "replay", forbidden)
    _forbid_current_alpha_proofs(monkeypatch, forbidden)
    monkeypatch.setattr(data_library, "export_checked_theorem", forbidden)

    output = driver.LabSession().run(f"pa lean alpha {mode} zero_add")

    assert "Release edition: Alpha v33." in output
    assert "Checked-use authority: YES." in output
    assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in output
    assert "--edition alpha --format compact" in output
    assert len(output.encode("utf-8")) <= 15 * 1024


def test_real_large_alpha_root_preview_never_replays_root_certificate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from peano_lab.library.quadratic_reciprocity_stack import QR_ROOT_NAME

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("quadratic reciprocity root must not replay from the browser")

    monkeypatch.setattr(alpha, "replay", forbidden)
    _forbid_current_alpha_proofs(monkeypatch, forbidden)
    monkeypatch.setattr(data_library, "export_checked_theorem", forbidden)

    output = driver.LabSession().run(f"pa lean alpha {QR_ROOT_NAME}")

    assert QR_ROOT_NAME in output
    assert "Authenticated release evidence: alpha_closed." in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert len(output.encode("utf-8")) <= 15 * 1024


def test_compact_preview_keeps_verification_disclosures_even_for_huge_unicode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from peano_lab.library import lean_presentation

    monkeypatch.setattr(
        lean_presentation,
        "preview_checked_presentation",
        lambda *_args, **_kwargs: "∀" * 40_000,
    )

    output = driver.LabSession().run("pa lean zero_add")

    assert "theorem presentation abbreviated" in output
    assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert "--package-dir artifacts/lean/zero_add --verify" in output
    assert len(output.encode("utf-8")) <= 15 * 1024


def test_exact_mode_displays_the_real_expanded_formula_without_replaying(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = formula_to_lean(replay("zero_add").formula)

    def forbidden(_name: str) -> None:
        raise AssertionError("exact formula inspection must not replay a certificate")

    monkeypatch.setattr(data_library, "replay", forbidden)

    output = driver.LabSession().run("pa lean exact zero_add")

    assert "Exact Lean proposition; semantic aliases have been fully expanded:" in output
    assert expected in output
    assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in output


def test_tactics_mode_discloses_original_peano_commands_without_claiming_lean_proof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    specification = get("add_comm")
    assert specification is not None

    def forbidden(_name: str) -> None:
        raise AssertionError("proof-script inspection must not replay a certificate")

    monkeypatch.setattr(data_library, "replay", forbidden)

    output = driver.LabSession().run("pa lean tactics add_comm")

    assert "Generated dependency introductions (Peano commands; not Lean tactics):" in output
    assert "Original authored Peano tactics (not Lean tactics):" in output
    assert "intro zero_add" in output
    assert specification.script[0] in output
    assert "Independent Lean compilation: NOT RUN" in output


@pytest.mark.parametrize("mode", ("compact", "exact", "tactics"))
def test_alpha_channel_and_view_mode_can_be_written_in_either_order(mode: str) -> None:
    session = driver.LabSession()

    assert session.run(f"pa lean alpha {mode} zero_add") == session.run(
        f"pa lean {mode} alpha zero_add"
    )


def test_alpha_body_only_entries_are_rejected_before_any_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item = next(
        candidate for candidate in alpha.v18.ALPHA_ENTRIES if not candidate.checked_use
    )

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("a body-only entry cannot have checked theorem authority")

    monkeypatch.setattr(alpha, "replay", forbidden)
    _forbid_current_alpha_proofs(monkeypatch, forbidden)
    monkeypatch.setattr(data_library, "_alpha_item", lambda _name: (alpha, item))

    output = driver.LabSession().run(f"pa lean alpha {item.spec.name}")

    assert "requires a closed theorem certificate" in output
    assert "Checked-use authority: YES" not in output


@pytest.mark.parametrize(
    ("command", "expected"),
    (
        ("full", "Usage: pa lean full <theorem>"),
        ("exact", "Usage: pa lean exact <theorem>"),
        ("tactics", "Usage: pa lean tactics <theorem>"),
        ("alpha", "Usage: pa lean alpha <theorem>"),
        ("alpha full", "Usage: pa lean alpha full <theorem>"),
        ("missing", "No library theorem 'missing'"),
        ("alpha missing", "No Alpha v33 theorem 'missing'"),
        ("exact zero_add trailing", "Usage: pa lean exact <theorem>"),
    ),
)
def test_missing_names_and_malformed_modes_fail_without_export(
    command: str,
    expected: str,
) -> None:
    output = driver.LabSession().run(f"pa lean {command}")

    assert expected in output


def test_full_mode_preserves_explicit_complete_checked_source_without_live_url() -> None:
    output = driver.LabSession().run("pa lean full zero_add")

    assert "complete constructive certificate" in output
    assert "Independent empty-context Peano kernel check: PASS" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert "theorem «zero_add»" in output
    assert LIVE_LEAN_PREFIX not in output


@pytest.mark.parametrize(
    "name",
    (
        "fundamental_theorem_of_arithmetic",
        "prime_factorization_existence",
        "prime_factorization_exists_up_to",
    ),
)
def test_large_stable_full_audit_is_blocked_before_any_proof_replay(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("large full-browser audits must stop before loading any proof")

    monkeypatch.setattr(data_library, "replay", forbidden)
    monkeypatch.setattr(data_library, "lean_export", forbidden)
    monkeypatch.setattr(data_library, "export_checked_theorem", forbidden)

    output = driver.LabSession().run(f"pa lean full {name}")

    assert output.startswith(f"Browser full-certificate audit blocked for safety — {name}")
    assert "dependency closure exceeds 128 theorem entries" in output
    assert "Checked-use authority remains YES" in output
    assert "fresh kernel replay and Lean verification were NOT RUN" in output
    assert f"pa lean {name}" in output
    assert f"--format full --output /private/tmp/peano-{name}.lean" in output
    assert "--max-memory-mib 1536 --max-verify-seconds 180 --verify" in output


@pytest.mark.parametrize(
    "name",
    (
        "quadratic_reciprocity_combined",
        *alpha.v18.v17.SUPPLEMENTARY_ROOT_NAMES,
        *alpha.v18.FLAGSHIP_ROOT_NAMES,
        "infinitely_many_primes_one_mod_four",
        "prime_is_two_squares_iff_two_or_one_mod_four",
    ),
)
def test_large_alpha_full_audit_is_blocked_before_any_proof_replay(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("large Alpha roots must not load a browser proof certificate")

    monkeypatch.setattr(alpha, "replay", forbidden)
    _forbid_current_alpha_proofs(monkeypatch, forbidden)
    monkeypatch.setattr(data_library, "export_checked_theorem", forbidden)

    output = driver.LabSession().run(f"pa lean alpha full {name}")

    assert output.startswith(f"Browser full-certificate audit blocked for safety — {name}")
    assert "dependency closure exceeds 128 theorem entries" in output
    assert "Checked-use authority remains YES" in output
    assert "fresh kernel replay and Lean verification were NOT RUN" in output
    assert f"pa lean alpha {name}" in output
    assert "--edition alpha --format full" in output
    historical = alpha.v18
    owner = historical.FLAGSHIP_PROMOTION_OWNERS.get(name)
    if owner is not None and historical.FLAGSHIP_BUNDLE_ROOTS[owner] == (name,):
        assert (
            "--proof-bundle research/arithmetic-library/artifacts/"
            + historical.FLAGSHIP_ARTIFACT_FILENAMES[owner]
        ) in output
    elif name in alpha.FRONTIER_NEW_NAMES:
        assert "--proof-bundle" not in output


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
def test_large_alpha_root_preview_recommends_its_exact_self_contained_bundle(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    artifact: str,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("bundle guidance must not load or replay a proof")

    monkeypatch.setattr(alpha, "replay", forbidden)
    _forbid_current_alpha_proofs(monkeypatch, forbidden)

    output = driver.LabSession().run(f"pa lean alpha {name}")

    assert "--format compact --package-dir" in output
    assert (
        "--proof-bundle research/arithmetic-library/artifacts/" + artifact
    ) in output
    assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in output


def test_dependency_guard_stops_at_first_excess_without_traversing_full_graph(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    original_get = data_library.get
    inspected: list[str] = []

    def tracked_get(name: str):
        inspected.append(name)
        return original_get(name)

    def forbidden(_name: str) -> None:
        raise AssertionError("dependency guard must inspect metadata, never replay")

    monkeypatch.setattr(data_library, "get", tracked_get)
    monkeypatch.setattr(data_library, "replay", forbidden)

    output = driver.LabSession().run("pa lean full fundamental_theorem_of_arithmetic")

    assert "blocked for safety" in output
    assert len(inspected) <= data_library._LEAN_FULL_BROWSER_DEPENDENCY_LIMIT + 1


def test_small_alpha_full_audit_remains_explicitly_available() -> None:
    output = driver.LabSession().run("pa lean alpha full zero_add")

    assert "complete constructive certificate" in output
    assert "Independent empty-context Peano kernel check: PASS" in output
    assert "Release edition: Alpha v33." in output
    assert "theorem «zero_add»" in output


def test_library_help_documents_the_explicit_inspection_views() -> None:
    output = driver.LabSession().run("pa lib help")

    assert "pa lean full <name>" in output
    assert "pa lean exact <name>" in output
    assert "pa lean tactics <name>" in output
