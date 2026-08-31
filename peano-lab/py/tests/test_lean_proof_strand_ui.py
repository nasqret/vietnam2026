"""Readable browser proof strands are bounded metadata, never proof authority."""

from __future__ import annotations

import driver
import pytest

from peano_lab.library import editions_v19 as historical_alpha
from peano_lab.library import editions_v33 as alpha
from peano_lab.library.alpha_enrollment_v27 import ROOT_STATEMENT_SHA256
from peano_lab.library import lean_proof_strand
from peano_lab.library.lean import LIVE_LEAN_PREFIX
from peano_lab.library.theorems import get
from peano_lab.ui import data_library, prove


def _forbid_current_alpha_proofs(monkeypatch, forbidden):
    # Current and inherited proof providers must all remain unused by previews.
    for edition, provider in ((alpha, "research"), (alpha.v32, "research"), (alpha.v32.v31, "completed_lower")):
        monkeypatch.setattr(edition, "replay", forbidden)
        monkeypatch.setattr(edition, "_checked_" + provider + "_bundle", forbidden)
        monkeypatch.setattr(edition, "checked_" + provider + "_bundle", forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30, "replay", forbidden)


def test_small_proof_strand_is_readable_theorem_first_and_honestly_unverified() -> None:
    output = driver.LabSession().run("pa proof zero_add")

    assert output.startswith("Readable Peano-to-Lean proof strand — zero_add")
    assert "Theorem:" in output
    assert "Authenticated release evidence: stable_closed." in output
    assert "Release membership: stable." in output
    assert "Checked-use authority: YES." in output
    assert "Transitive authenticated theorem entries: 1." in output
    assert "Root authored Peano tactic decisions: 3." in output
    assert "Fresh Peano proof replay: NOT RUN" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert "Direct authored dependencies (0):" in output
    assert "Root authored Peano proof" in output
    assert "original Peano tactics; not executable Lean tactics" in output
    assert "Bounded topological strand outline (metadata only):" in output
    assert "--format strand --package-dir /private/tmp/peano-proof-strands/zero_add" in output
    assert "--verify" in output
    assert LIVE_LEAN_PREFIX not in output
    assert len(output.encode("utf-8")) <= 15 * 1024


def test_number_theory_strand_reads_metadata_without_any_proof_or_certificate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("browser proof strands must never replay or reconstruct proofs")

    monkeypatch.setattr(data_library, "replay", forbidden)
    monkeypatch.setattr(data_library, "lean_export", forbidden)
    monkeypatch.setattr(data_library, "export_checked_theorem", forbidden)
    monkeypatch.setattr(lean_proof_strand, "build_proof_strand", forbidden)

    output = driver.LabSession().run("pa proof prime_unbounded")

    assert "Lt n p ∧ Prime p" in output
    assert "Transitive authenticated theorem entries: 57." in output
    assert "Root authored Peano tactic decisions: 84." in output
    assert "additional authored Peano tactic lines" in output
    assert "Fresh Peano proof replay: NOT RUN" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert len(output.encode("utf-8")) <= 15 * 1024


def test_named_direct_dependencies_include_authenticated_summaries() -> None:
    output = driver.LabSession().run("pa proof add_comm")

    assert "Direct authored dependencies (2):" in output
    assert "  - zero_add:" in output
    assert "Transitive authenticated theorem entries: 3." in output


@pytest.mark.parametrize(
    "command",
    (
        "pa proof zero_add",
        "pa lean strand zero_add",
    ),
)
def test_interactive_proof_command_and_lean_strand_mode_are_equivalent(
    command: str,
) -> None:
    session = driver.LabSession()

    assert session.run(command) == session.run("pa proof zero_add")


@pytest.mark.parametrize(
    "command",
    (
        "pa proof alpha zero_add",
        "pa lean alpha strand zero_add",
        "pa lean strand alpha zero_add",
    ),
)
def test_alpha_proof_strand_routes_preserve_explicit_release_authority(
    command: str,
) -> None:
    output = driver.LabSession().run(command)

    assert "Release edition: Alpha v33." in output
    assert "Release membership: stable." in output
    assert "--edition alpha --format strand" in output
    assert "Independent Lean compilation: NOT RUN" in output


def test_checked_alpha_only_strand_does_not_claim_stable_membership() -> None:
    name = historical_alpha.v18.v17.v16.QR_PROMOTED_NAMES[0]

    output = driver.LabSession().run(f"pa proof alpha {name}")

    assert "Authenticated release evidence: alpha_closed." in output
    assert "Release membership: alpha_only." in output
    assert "Release edition: Alpha v33." in output
    assert "--edition alpha --format strand" in output


@pytest.mark.parametrize(
    "name",
    (
        "doubled_square_plus_one_nonzero",
        "linear_congruence_solvable_iff_gcd_divides",
    ),
)
def test_historical_alpha_v19_frontier_root_has_current_v31_bounded_preview(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    assert name in historical_alpha.FRONTIER_NEW_NAMES

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("a historical Alpha v19 frontier preview must not replay its proof")

    _forbid_current_alpha_proofs(monkeypatch, forbidden)
    monkeypatch.setattr(data_library, "replay", forbidden)
    monkeypatch.setattr(data_library, "export_checked_theorem", forbidden)
    monkeypatch.setattr(lean_proof_strand, "build_proof_strand", forbidden)

    output = driver.LabSession().run(f"pa proof alpha {name}")

    assert output.startswith(f"Readable Peano-to-Lean proof strand — {name}")
    assert "Release edition: Alpha v33." in output
    assert "Authenticated release evidence: alpha_closed." in output
    assert "Release membership: alpha_only." in output
    assert "Fresh Peano proof replay: NOT RUN" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert "--edition alpha --format strand" in output
    assert len(output.encode("utf-8")) <= 15 * 1024


def test_historical_body_only_theorem_has_current_alpha_v31_checked_preview() -> None:
    name = "cell_list_valid_nil"
    historical = historical_alpha.v18.entry(name, edition="alpha")
    current = alpha.entry(name, edition="alpha")
    assert historical is not None and not historical.checked_use
    assert current is not None and current.checked_use

    output = driver.LabSession().run(f"pa proof alpha {name}")

    assert "Release edition: Alpha v33." in output
    assert "Authenticated release evidence: alpha_closed." in output
    assert "Checked-use authority: YES." in output
    assert "Fresh Peano proof replay: NOT RUN" in output
    assert "Independent Lean compilation: NOT RUN" in output


@pytest.mark.parametrize(
    "name",
    (
        "fundamental_theorem_of_arithmetic",
        "prime_factorization_existence",
        "prime_factorization_exists_up_to",
    ),
)
def test_large_stable_strand_shows_root_proof_without_planning_full_closure(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    specification = get(name)
    assert specification is not None

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("a large browser strand must not plan or replay its proof graph")

    monkeypatch.setattr(data_library, "replay", forbidden)
    monkeypatch.setattr(data_library, "export_checked_theorem", forbidden)
    monkeypatch.setattr(lean_proof_strand, "plan_proof_strand", forbidden)
    monkeypatch.setattr(lean_proof_strand, "build_proof_strand", forbidden)

    output = driver.LabSession().run(f"pa proof {name}")

    assert output.startswith(f"Readable Peano-to-Lean proof strand — {name}")
    assert "more than 128; stopped at 129" in output
    assert "Dependency expansion stopped at the browser safety limit" in output
    assert "Root authored Peano proof" in output
    assert specification.script[0] in output
    assert "Checked-use authority: YES." in output
    assert "Fresh Peano proof replay: NOT RUN" in output
    assert f"--package-dir /private/tmp/peano-proof-strands/{name}" in output
    assert len(output.encode("utf-8")) <= 15 * 1024


@pytest.mark.parametrize(
    "name",
    (
        "quadratic_reciprocity_combined",
        "lucas_theorem",
        "bertrand_strict",
        "four_square_lagrange",
        "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
        "infinitely_many_primes_one_mod_four",
        "prime_is_two_squares_iff_two_or_one_mod_four",
        "euclidean_gcd_execution_logarithmic_bound",
        "binary_modular_execution_logarithmic_bound",
        "infinitely_many_primes_three_mod_four",
        "crt_pairwise_coprime_prefix_canonical_exists_unique",
        "signed_matrix_cofactor_family_and_fold_exists",
        "beta_horner_hensel_lift_exists",
        "crt_merge_compatible_prefix_canonical_exists_unique",
        "crt_pairwise_compatible_dominating_last_canonical_exists_unique",
        "pythagorean_positive_primitive_classification",
        "fermat_four_complete_classification",
        "fermat_four_positive_sum_not_square",
    ),
)
def test_flagship_alpha_strand_shows_root_without_loading_full_certificate(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    item = alpha.entry(name, edition="alpha")
    assert item is not None

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Alpha flagship root viewing must not load its proof artifact")

    _forbid_current_alpha_proofs(monkeypatch, forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30.v29.v28.v27.v26, "_checked_first_wave_bundle", forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30.v29.v28.v27, "_checked_second_wave_bundle", forbidden)
    monkeypatch.setattr(data_library, "export_checked_theorem", forbidden)
    monkeypatch.setattr(lean_proof_strand, "plan_proof_strand", forbidden)
    monkeypatch.setattr(lean_proof_strand, "build_proof_strand", forbidden)

    output = driver.LabSession().run(f"pa proof alpha {name}")

    assert output.startswith(f"Readable Peano-to-Lean proof strand — {name}")
    assert "Authenticated release evidence: alpha_closed." in output
    assert "Release membership: alpha_only." in output
    assert "more than 128; stopped at 129" in output
    assert "Root authored Peano proof" in output
    assert item.spec.script[0] in output
    assert "--edition alpha --format strand" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert len(output.encode("utf-8")) <= 15 * 1024


def test_body_only_alpha_theorem_is_denied_before_planning_or_replay(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item = next(
        candidate
        for candidate in historical_alpha.v18.ALPHA_ENTRIES
        if not candidate.checked_use
    )

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("body-only entries have no proof-strand checked-use authority")

    _forbid_current_alpha_proofs(monkeypatch, forbidden)
    monkeypatch.setattr(data_library, "_alpha_item", lambda _name: (alpha, item))
    monkeypatch.setattr(lean_proof_strand, "plan_proof_strand", forbidden)

    output = driver.LabSession().run(f"pa proof alpha {item.spec.name}")

    assert "requires closed checked-use authority" in output
    assert "Checked-use authority: YES" not in output


@pytest.mark.parametrize("name", tuple(ROOT_STATEMENT_SHA256))
def test_second_wave_strands_are_bounded_current_metadata_only(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("a second-wave browser strand loaded proof data")

    _forbid_current_alpha_proofs(monkeypatch, forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30, "_checked_gaussian_factorization_bundle", forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30.v29, "_checked_priority_layer_bundle", forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30.v29.v28, "_checked_lower_layer_bundle", forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30.v29.v28.v27, "_checked_second_wave_bundle", forbidden)
    monkeypatch.setattr(data_library, "export_checked_theorem", forbidden)
    monkeypatch.setattr(lean_proof_strand, "build_proof_strand", forbidden)

    output = driver.LabSession().run(f"pa proof alpha {name}")

    assert output.startswith(f"Readable Peano-to-Lean proof strand — {name}")
    assert "Release edition: Alpha v33." in output
    assert "Authenticated release evidence: alpha_closed." in output
    assert "Release membership: alpha_only." in output
    assert "Fresh Peano proof replay: NOT RUN" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert "--edition alpha --format strand" in output
    assert len(output.encode("utf-8")) <= 15 * 1024


def test_large_unicode_outline_cannot_exhaust_browser_output_budget(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        lean_proof_strand,
        "preview_proof_strand",
        lambda *_args, **_kwargs: "∀" * 40_000,
    )

    output = driver.LabSession().run("pa proof zero_add")

    assert output.startswith("Readable Peano-to-Lean proof strand — zero_add")
    assert "Fresh Peano proof replay: NOT RUN" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert "--format strand --package-dir" in output
    assert "browser output truncated" in output
    assert len(output.encode("utf-8")) <= 15 * 1024


@pytest.mark.parametrize(
    ("name", "edition"),
    (
        ("prime_factorization_existence", "stable"),
        ("rectangular_matrix_rank_exists_unique", "alpha"),
    ),
)
def test_oversized_theorem_keeps_release_evidence_and_exact_export_instructions(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
    edition: str,
) -> None:
    monkeypatch.setattr(
        lean_proof_strand,
        "readable_strand_formula",
        lambda *_args, **_kwargs: "∀" * 40_000,
    )
    prefix = "alpha " if edition == "alpha" else ""

    output = driver.LabSession().run(f"pa proof {prefix}{name}")

    assert output.startswith(f"Readable Peano-to-Lean proof strand — {name}")
    assert "Theorem: ∀" in output
    assert "theorem statement abbreviated" in output
    assert "Checked-use authority: YES." in output
    assert "Fresh Peano proof replay: NOT RUN" in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert f"pa lean {prefix}exact {name}" in output
    assert f"--format strand --package-dir /private/tmp/peano-proof-strands/{name} --verify" in output
    assert len(output.encode("utf-8")) <= 15 * 1024


@pytest.mark.parametrize(
    ("command", "expected"),
    (
        ("pa proof", "Usage: pa proof [alpha] <theorem>"),
        ("pa proof help", "Usage: pa proof [alpha] <theorem>"),
        ("pa proof alpha", "Usage: pa proof alpha <theorem>"),
        ("pa proof missing", "No library theorem 'missing'"),
        ("pa proof alpha missing", "No Alpha v33 theorem 'missing'"),
        ("pa proof zero_add trailing", "Usage: pa proof [alpha] <theorem>"),
        ("pa lean strand", "Usage: pa lean strand <theorem>"),
    ),
)
def test_proof_strand_usage_and_unknown_theorems_fail_cleanly(
    command: str,
    expected: str,
) -> None:
    assert expected in driver.LabSession().run(command)


def test_proof_strand_help_is_visible_in_global_and_library_help() -> None:
    session = driver.LabSession()

    assert "pa proof <name>" in session.run("pa help")
    assert "pa proof <name>" in session.run("pa lib help")
    assert "pa proof alpha <name>" in session.run("pa lib help")
    assert "Usage: pa proof [alpha] <theorem>" in session.run("help proof")


def test_proof_strand_command_cannot_bypass_an_active_proof_owner() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    owner = prove.get_owner(session.webstate)

    output = session.run("pa proof zero_add")

    assert "unknown tactic 'pa'" in output
    assert prove.get_owner(session.webstate) is owner
