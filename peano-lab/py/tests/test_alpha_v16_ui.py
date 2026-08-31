"""The optional Alpha browser channel preserves Stable proof authority."""

from __future__ import annotations

import driver
import pytest
from peano_lab.library import editions_v16 as historical_alpha
from peano_lab.library import editions_v33 as alpha
from peano_lab.library.alpha_enrollment_v19 import (
    LINEAR_CONGRUENCE_ROOT_NAME,
    PRIME_TWO_SQUARE_ROOT_NAME,
    PRIMES_ONE_MOD_FOUR_ROOT_NAME,
    PYTHAGOREAN_V19_ROOT_NAMES,
)
from peano_lab.library.alpha_enrollment_v20 import (
    BERTRAND_CHAIN_ROOT_NAME,
    BERTRAND_MULTIPLICITY_ROOT_NAME,
    CONTINUED_FRACTION_ROOT_NAME,
    MATRIX_DOT_PRODUCT_ROOT_NAME,
    POLYNOMIAL_HORNER_ROOT_NAME,
)
from peano_lab.library.alpha_enrollment_v21 import (
    BINARY_MODULAR_EXPONENTIATION_ROOT_NAME,
    EUCLIDEAN_EXECUTION_ROOT_NAME,
    EUCLIDEAN_TWO_STEP_HALVING_ROOT_NAME,
    MATRIX_CODED_PRODUCT_ROOT_NAME,
    SIGNED_DOT_PRODUCT_ROOT_NAME,
    SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME,
    SIGNED_THREE_DETERMINANT_ROOT_NAME,
)
from peano_lab.library.alpha_enrollment_v27 import ROOT_STATEMENT_SHA256
from peano_lab.library.quadratic_reciprocity_stack import QR_ROOT_NAME
from peano_lab.ui import data_library


def _forbid_current_alpha_proofs(monkeypatch, forbidden):
    # Current and inherited proof providers must all remain unused by previews.
    for edition, provider in ((alpha, "research"), (alpha.v32, "research"), (alpha.v32.v31, "completed_lower")):
        monkeypatch.setattr(edition, "replay", forbidden)
        monkeypatch.setattr(edition, "_checked_" + provider + "_bundle", forbidden)
        monkeypatch.setattr(edition, "checked_" + provider + "_bundle", forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30, "replay", forbidden)


def test_alpha_index_reports_exact_current_evidence_without_proof_replay(
    monkeypatch,
) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("Alpha inventory must not load or replay any proof")

    _forbid_current_alpha_proofs(monkeypatch, forbidden_replay)

    output = driver.LabSession().run("pa lib alpha")

    assert "immutable Alpha v33" in output
    assert "Enrolled statements: 4,092" in output
    assert "Stable closed: 432" in output
    assert "Alpha closed: 3,660" in output
    assert "Dependency-curried body only: 0" in output
    assert "Pending closure: 0" in output
    assert "Available for independently checked use: 4,092" in output
    assert "Previously promoted quadratic-reciprocity results: 315" in output
    assert "Previously promoted supplementary-law results: 31" in output
    assert "Previously promoted five-campaign flagship results: 673" in output
    assert "Newly closed legacy residual results: 84" in output
    assert "Previously added Alpha v19 campaign results: 64" in output
    assert "Previously added Alpha v20 campaign results: 39" in output
    assert "Previously added Alpha v21 campaign results: 54" in output
    assert "Previously added Alpha v22 campaign results: 60" in output
    assert "Previously added Alpha v23 campaign results: 59" in output
    assert "Previously added Alpha v24 campaign results: 59" in output
    assert "Previously added Alpha v25 campaign results: 72" in output
    assert "Previously added Alpha v26 campaign results: 58" in output
    assert "Previously added Alpha v27 campaign results: 422" in output
    assert "Previously added Alpha v28 campaign results: 204" in output
    assert "Previously added Alpha v29 campaign results: 278" in output
    assert "Previously added Alpha v30 campaign results: 180" in output
    assert "Previously added Alpha v31 campaign results: 574" in output
    assert "New constructive campaign results: 121" in output
    assert alpha.ALPHA_V33_IDENTITY_SHA256 in output


def test_alpha_root_evidence_card_is_cheap_and_never_claims_stable_membership(
    monkeypatch,
) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("Alpha evidence cards do not independently replay")

    _forbid_current_alpha_proofs(monkeypatch, forbidden_replay)

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

    _forbid_current_alpha_proofs(monkeypatch, forbidden_replay)
    session = driver.LabSession()

    for name in alpha.v32.v31.v30.v29.v28.v27.v26.v25.v24.v23.v22.v21.v19.v18.v17.SUPPLEMENTARY_ROOT_NAMES:
        output = session.run(f"pa lib alpha {name}")
        assert "Release evidence: alpha_closed" in output
        assert "Release membership: alpha_only" in output
        assert "Checked-use authority: YES" in output
        assert "Independent empty-context kernel check: PASS" not in output


def test_all_six_flagship_roots_have_checked_cards_without_replaying(monkeypatch) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("flagship evidence cards never replay large proof roots")

    _forbid_current_alpha_proofs(monkeypatch, forbidden_replay)
    session = driver.LabSession()

    for name in alpha.v32.v31.v30.v29.v28.v27.v26.v25.v24.v23.v22.v21.v19.v18.FLAGSHIP_ROOT_NAMES:
        output = session.run(f"pa lib alpha {name}")
        assert "Release evidence: alpha_closed" in output
        assert "Release membership: alpha_only" in output
        assert "Checked-use authority: YES" in output
        assert "Independent empty-context kernel check: PASS" not in output


def test_all_historical_body_only_theorems_now_have_checked_cards(monkeypatch) -> None:
    historical = next(
        item for item in alpha.v32.v31.v30.v29.v28.v27.v26.v25.v24.v23.v22.v21.v19.v18.ALPHA_ENTRIES if not item.checked_use
    )

    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("historically residual evidence cards never replay a proof")

    _forbid_current_alpha_proofs(monkeypatch, forbidden_replay)
    session = driver.LabSession()

    inspection = session.run(f"pa lib alpha {historical.spec.name}")
    preview = session.run(f"pa lean alpha {historical.spec.name}")

    assert "Release evidence: alpha_closed" in inspection
    assert "Checked-use authority: YES" in inspection
    assert "Release edition: Alpha v33." in preview
    assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in preview
    assert historical.evidence is alpha.v32.v31.v30.v29.v28.v27.v26.v25.v24.v23.v22.v21.v19.v18.EvidenceStatus.BODY_CHECKED
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
        POLYNOMIAL_HORNER_ROOT_NAME,
        MATRIX_DOT_PRODUCT_ROOT_NAME,
        BERTRAND_MULTIPLICITY_ROOT_NAME,
        BERTRAND_CHAIN_ROOT_NAME,
        CONTINUED_FRACTION_ROOT_NAME,
        MATRIX_CODED_PRODUCT_ROOT_NAME,
        SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME,
        SIGNED_DOT_PRODUCT_ROOT_NAME,
        SIGNED_THREE_DETERMINANT_ROOT_NAME,
        EUCLIDEAN_TWO_STEP_HALVING_ROOT_NAME,
        EUCLIDEAN_EXECUTION_ROOT_NAME,
        BINARY_MODULAR_EXPONENTIATION_ROOT_NAME,
        "binary_length_exists_unique",
        "euclidean_anchored_execution_linear_bound",
        "binary_modular_execution_result_exists_unique",
        "beta_signed_matrix_minor_exists",
        "signed_matrix_four_full_determinant_exists",
        "beta_horner_derivative_exists_unique",
        "crt_prefix_lcm_exists_unique",
        "crt_pairwise_coprime_prefix_canonical_exists_unique",
        "signed_matrix_cofactor_family_and_fold_exists",
        "beta_horner_hensel_lift_exists",
        "crt_merge_compatible_prefix_canonical_exists_unique",
        "coprime_square_product_factors",
        "square_divides_square_root",
        "pythagorean_positive_primitive_classification",
        "fermat_four_complete_classification",
        "fermat_four_positive_sum_not_square",
        "crt_pairwise_compatible_dominating_last_canonical_exists_unique",
        *ROOT_STATEMENT_SHA256,
    ),
)
def test_new_campaign_goals_and_complete_valuation_have_checked_cards_without_replay(
    monkeypatch,
    name: str,
) -> None:
    def forbidden_replay(*_args, **_kwargs):
        raise AssertionError("campaign evidence cards must never load or replay proofs")

    _forbid_current_alpha_proofs(monkeypatch, forbidden_replay)

    output = driver.LabSession().run(f"pa lib alpha {name}")

    assert f"{name} — Alpha v33 theorem evidence" in output
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
        POLYNOMIAL_HORNER_ROOT_NAME,
        MATRIX_DOT_PRODUCT_ROOT_NAME,
        BERTRAND_MULTIPLICITY_ROOT_NAME,
        BERTRAND_CHAIN_ROOT_NAME,
        CONTINUED_FRACTION_ROOT_NAME,
        MATRIX_CODED_PRODUCT_ROOT_NAME,
        SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME,
        SIGNED_DOT_PRODUCT_ROOT_NAME,
        SIGNED_THREE_DETERMINANT_ROOT_NAME,
        EUCLIDEAN_TWO_STEP_HALVING_ROOT_NAME,
        EUCLIDEAN_EXECUTION_ROOT_NAME,
        BINARY_MODULAR_EXPONENTIATION_ROOT_NAME,
        "binary_length_exists_unique",
        "euclidean_anchored_execution_linear_bound",
        "binary_modular_execution_result_exists_unique",
        "beta_signed_matrix_minor_exists",
        "beta_horner_derivative_exists_unique",
        "crt_pairwise_coprime_prefix_canonical_exists_unique",
        "signed_matrix_cofactor_family_and_fold_exists",
        "beta_horner_hensel_lift_exists",
        "crt_merge_compatible_prefix_canonical_exists_unique",
        "coprime_square_product_factors",
        "square_divides_square_root",
        "pythagorean_positive_primitive_classification",
        "fermat_four_complete_classification",
        "fermat_four_positive_sum_not_square",
        *ROOT_STATEMENT_SHA256,
    ),
)
def test_new_campaign_lean_previews_are_bounded_and_never_use_synthetic_bundle_targets(
    monkeypatch,
    name: str,
) -> None:
    def forbidden(*_args, **_kwargs):
        raise AssertionError("safe campaign previews must not open or reconstruct proofs")

    _forbid_current_alpha_proofs(monkeypatch, forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30, "_checked_gaussian_factorization_bundle", forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30.v29, "_checked_priority_layer_bundle", forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30.v29.v28, "_checked_lower_layer_bundle", forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30.v29.v28.v27.v26, "_checked_first_wave_bundle", forbidden)
    monkeypatch.setattr(alpha.v32.v31.v30.v29.v28.v27, "_checked_second_wave_bundle", forbidden)

    output = driver.LabSession().run(f"pa lean alpha {name}")

    assert f"Lean 4 independently checked theorem — {name}" in output
    assert "Release edition: Alpha v33." in output
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


@pytest.mark.parametrize(
    "name",
    (historical_alpha.QR_PROMOTED_NAMES[0], "square_zero_root", "square_divides_square_root"),
)
def test_alpha_explicit_verification_checks_actual_empty_context_certificate(name: str) -> None:
    output = driver.LabSession().run(f"pa lib alpha check {name}")

    assert "Release evidence: alpha_closed" in output
    assert "Independent empty-context kernel check: PASS" in output
    assert f"pa lean alpha {name}" in output


@pytest.mark.parametrize(
    "name",
    (
        QR_ROOT_NAME,
        *alpha.v32.v31.v30.v29.v28.v27.v26.v25.v24.v23.v22.v21.v19.v18.v17.SUPPLEMENTARY_ROOT_NAMES,
        *alpha.v32.v31.v30.v29.v28.v27.v26.v25.v24.v23.v22.v21.v19.v18.FLAGSHIP_ROOT_NAMES,
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

    _forbid_current_alpha_proofs(monkeypatch, forbidden_replay)

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

    _forbid_current_alpha_proofs(monkeypatch, forbidden_replay)
    listing = driver.LabSession().run("pa lib alpha checked")

    assert QR_ROOT_NAME in listing
    assert "cell_list_valid_nil" in listing
    assert "prime_power_valuation_exists" in listing
    assert LINEAR_CONGRUENCE_ROOT_NAME in listing
    assert PRIMES_ONE_MOD_FOUR_ROOT_NAME in listing
    assert PRIME_TWO_SQUARE_ROOT_NAME in listing
    assert PYTHAGOREAN_V19_ROOT_NAMES[-1] in listing
    assert POLYNOMIAL_HORNER_ROOT_NAME in listing
    assert MATRIX_DOT_PRODUCT_ROOT_NAME in listing
    assert BERTRAND_MULTIPLICITY_ROOT_NAME in listing
    assert BERTRAND_CHAIN_ROOT_NAME in listing
    assert CONTINUED_FRACTION_ROOT_NAME in listing
    assert MATRIX_CODED_PRODUCT_ROOT_NAME in listing
    assert SIGNED_MATRIX_CODED_PRODUCT_ROOT_NAME in listing
    assert SIGNED_DOT_PRODUCT_ROOT_NAME in listing
    assert SIGNED_THREE_DETERMINANT_ROOT_NAME in listing
    assert EUCLIDEAN_TWO_STEP_HALVING_ROOT_NAME in listing
    assert EUCLIDEAN_EXECUTION_ROOT_NAME in listing
    assert BINARY_MODULAR_EXPONENTIATION_ROOT_NAME in listing
    assert "beta_signed_matrix_minor_exists" in listing
    assert "signed_matrix_four_full_determinant_exists" in listing
    assert "beta_horner_derivative_exists_unique" in listing
    assert "crt_prefix_lcm_exists_unique" in listing
    assert "crt_pairwise_coprime_prefix_canonical_exists_unique" in listing
    assert all(name in listing for name in alpha.FRONTIER_NEW_NAMES)
    assert all(name in listing for name in alpha.v32.v31.FRONTIER_NEW_NAMES)
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

    assert "No Alpha v33 theorem 'missing'" in session.run("pa lib alpha missing")
    assert "No Alpha v33 theorem 'missing'" in session.run("pa lean alpha missing")
    assert session.run("pa lib alpha check") == "Usage: pa lib alpha check <theorem>."


@pytest.mark.parametrize(
    "command",
    (
        "pa lib alpha",
        "pa lib alpha signed_recursive_determinant_exists_unique",
        "pa lib alpha check matrix_recursive_node_code_exists",
        "pa lean alpha signed_recursive_determinant_exists_unique",
        "pa proof alpha rectangular_matrix_rank_exists_unique",
    ),
)
def test_unsealed_alpha_is_never_presented_as_checked_but_stable_remains_available(
    monkeypatch: pytest.MonkeyPatch,
    command: str,
) -> None:
    monkeypatch.setattr(alpha, "EXPECTED_ALPHA_V33_COUNT", 0)
    session = driver.LabSession()

    output = session.run(command)

    assert "Alpha v33 is not sealed for checked use" in output
    assert "Checked-use authority: YES" not in output
    assert "kernel check: PASS" not in output
    assert "432 scripted theorems" in session.run("pa lib")


@pytest.mark.parametrize("name", tuple(ROOT_STATEMENT_SHA256))
def test_second_wave_roots_remain_opt_in_and_do_not_enter_stable(name: str) -> None:
    session = driver.LabSession()

    assert alpha.entry(name, edition="alpha") is not None
    assert alpha.entry(name, edition="stable") is None
    assert f"No library theorem {name!r}" in session.run(f"pa lib {name}")
