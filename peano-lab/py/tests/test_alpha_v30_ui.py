"""Current Alpha metadata, honest previews, and fail-closed Gaussian admission."""

from __future__ import annotations

from hashlib import sha256
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import driver
import pytest

from peano_lab.library.alpha_enrollment_v29 import ROOT_STATEMENT_SHA256 as V29_PINS
from peano_lab.library.alpha_enrollment_v30 import ROOT_STATEMENT_SHA256 as V30_PINS
from peano_lab.library import lean_proof_strand, theorems
from peano_lab.ui import data_library


ROOT = Path(__file__).resolve().parents[3]
PRIORITY_ROOTS = (
    "totient_euler_product_formula",
    "positive_squarefree_kernel_and_power_profile",
    "odd_prime_lifting_the_exponent",
    "continued_fraction_convergent_best_approximation",
)
ROOT_PINS = {**{name: V29_PINS[name] for name in PRIORITY_ROOTS}, **V30_PINS}
GAUSSIAN_ROOT = "gaussian_unique_prime_factorization"


@pytest.fixture(scope="module")
def alpha():
    from peano_lab.library import editions_v34

    return editions_v34


@pytest.fixture(scope="module")
def closure():
    from peano_lab.library import campaign_gaussian_factorization_closure

    return campaign_gaussian_factorization_closure


@pytest.fixture(scope="module")
def exporter():
    specification = importlib.util.spec_from_file_location(
        "peano_alpha_v30_ui_exporter", ROOT / "scripts" / "export_peano_lean.py"
    )
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _forbid_proof_loading(monkeypatch, alpha, closure):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Alpha inspection invoked an actual proof provider")

    for edition, provider in (
        (alpha, "research"),
        (alpha.v33, "research"),
        (alpha.v33.v32, "research"),
        (alpha.v33.v32.v31, "completed_lower"),
        (alpha.v33.v32.v31.v30, "gaussian_factorization"),
        (alpha.v33.v32.v31.v30.v29, "priority_layer"),
        (alpha.v33.v32.v31.v30.v29.v28, "lower_layer"),
        (alpha.v33.v32.v31.v30.v29.v28.v27, "second_wave"),
        (alpha.v33.v32.v31.v30.v29.v28.v27.v26, "first_wave"),
    ):
        monkeypatch.setattr(edition, "replay", forbidden)
        monkeypatch.setattr(edition, f"_checked_{provider}_bundle", forbidden)
        monkeypatch.setattr(edition, f"checked_{provider}_bundle", forbidden)
    for name in (
        "parent_snapshot",
        "_table",
        "gaussian_factorization_plan",
        "check_gaussian_factorization_proof_bundle",
        "checked_gaussian_factorization_proof_bundle",
        "gaussian_factorization_bundle",
        "assemble_gaussian_factorization_proof_bundle",
        "replay_gaussian_factorization_theorem",
    ):
        monkeypatch.setattr(closure, name, forbidden)
    monkeypatch.setattr(data_library, "replay", forbidden)
    monkeypatch.setattr(data_library, "lean_export", forbidden)
    monkeypatch.setattr(data_library, "export_checked_theorem", forbidden)
    monkeypatch.setattr(lean_proof_strand, "build_proof_strand", forbidden)


def test_current_inventory_preserves_both_historical_editions(alpha, closure, monkeypatch):
    _forbid_proof_loading(monkeypatch, alpha, closure)
    assert len(alpha.ALPHA_ENTRIES) == 4_223
    assert len(alpha.v33.v32.ALPHA_ENTRIES) == 3_971
    assert len(alpha.v33.v32.FRONTIER_NEW_NAMES) == 175
    assert len(alpha.v33.v32.v31.ALPHA_ENTRIES) == 3_796
    assert len(alpha.v33.v32.v31.v30.ALPHA_ENTRIES) == 3_222
    assert len(alpha.FRONTIER_NEW_NAMES) == 131
    assert len(alpha.v33.v32.v31.FRONTIER_NEW_NAMES) == 574
    assert len(alpha.v33.v32.v31.v30.FRONTIER_NEW_NAMES) == 180
    assert len(alpha.v33.v32.v31.v30.v29.ALPHA_ENTRIES) == 3_042
    assert len(alpha.v33.v32.v31.v30.v29.FRONTIER_NEW_NAMES) == 278
    assert len(alpha.v33.v32.v31.v30.v29.v28.ALPHA_ENTRIES) == 2_764
    assert len(alpha.v33.v32.v31.v30.v29.v28.FRONTIER_NEW_NAMES) == 204
    assert len(alpha.STABLE_SPECS) == 432
    assert alpha.STABLE_EDITION is alpha.v33.v32.v31.v30.v29.v28.STABLE_EDITION
    assert all(
        alpha.ALPHA_EDITION.by_name[item.spec.name] is item
        for item in alpha.v33.v32.v31.v30.v29.ALPHA_ENTRIES
    )

    output = driver.LabSession().run("pa lib alpha")

    assert "immutable Alpha v34" in output
    assert "Enrolled statements: 4,223" in output
    assert "Stable closed: 432" in output
    assert "Alpha closed: 3,791" in output
    assert "Available for independently checked use: 4,223" in output
    assert "Previously added Alpha v28 campaign results: 204" in output
    assert "Previously added Alpha v29 campaign results: 278" in output
    assert "Previously added Alpha v30 campaign results: 180" in output
    assert "Previously added Alpha v31 campaign results: 574" in output
    assert "New constructive campaign results: 131" in output
    assert alpha.ALPHA_V34_IDENTITY_SHA256 in output
    assert "Independent empty-context kernel check: PASS" not in output


@pytest.mark.parametrize("name", tuple(ROOT_PINS))
def test_current_principal_cards_keep_exact_source_and_opt_in_authority(
    alpha, closure, monkeypatch, name
):
    _forbid_proof_loading(monkeypatch, alpha, closure)
    item = alpha.entry(name, edition="alpha")
    assert item is not None and item.checked_use
    assert sha256(item.spec.statement.encode()).hexdigest() == ROOT_PINS[name]
    assert alpha.entry(name, edition="stable") is None
    assert theorems.get(name) is None
    original = alpha.v33.v32.v31.v30.v29 if name in PRIORITY_ROOTS else alpha.v33.v32.v31.v30
    assert name in original.FRONTIER_NEW_NAMES

    output = driver.LabSession().run(f"pa lib alpha {name}")

    assert f"{name} — Alpha v34 theorem evidence" in output
    assert "Release membership: alpha_only" in output
    assert "Checked-use authority: YES" in output
    assert "This evidence card does not itself replay a proof." in output
    assert "Independent empty-context kernel check: PASS" not in output


@pytest.mark.parametrize("name", tuple(ROOT_PINS))
@pytest.mark.parametrize("command", ("pa proof alpha", "pa lean alpha", "pa lean alpha exact"))
def test_new_principal_previews_are_bounded_and_do_not_replay(
    alpha, closure, monkeypatch, name, command
):
    _forbid_proof_loading(monkeypatch, alpha, closure)

    output = driver.LabSession().run(f"{command} {name}")

    assert name in output
    assert "Release edition: Alpha v34." in output
    assert "Authenticated release evidence: alpha_closed." in output
    assert "Checked-use authority: YES." in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert "--edition alpha" in output and "--verify" in output
    assert "--proof-bundle" not in output
    assert len(output.encode("utf-8")) <= 15 * 1024
    if command.startswith("pa proof"):
        assert "Fresh Peano proof replay: NOT RUN" in output
        assert "Release membership: alpha_only." in output
    else:
        assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in output


@pytest.mark.parametrize("name", tuple(ROOT_PINS))
def test_current_exact_strand_plans_keep_historical_statement_pins_without_proof_io(
    alpha, closure, monkeypatch, name
):
    _forbid_proof_loading(monkeypatch, alpha, closure)

    plan = lean_proof_strand.plan_proof_strand(name, edition="alpha")

    assert plan.edition_version == "v34"
    assert plan.edition_identity_sha256 == alpha.ALPHA_V34_IDENTITY_SHA256
    assert plan.root == name
    assert plan.root_node.evidence == "alpha_closed"
    assert plan.root_node.membership == "alpha_only"
    assert sha256(plan.root_node.statement.encode()).hexdigest() == ROOT_PINS[name]


def test_three_metadata_entrypoints_do_not_read_files_or_construct_artifact_plans(
    alpha, closure, exporter, monkeypatch
):
    _forbid_proof_loading(monkeypatch, alpha, closure)

    def forbidden(*_args, **_kwargs):
        raise AssertionError("sealed metadata eligibility opened a file")

    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    assert data_library._alpha_edition() is alpha
    assert lean_proof_strand._edition_view("alpha") == (alpha.ALPHA_EDITION, "v34")
    spec, edition = exporter._load_selected_specification(
        SimpleNamespace(edition="alpha", theorem=GAUSSIAN_ROOT)
    )
    assert edition is alpha and spec.name == GAUSSIAN_ROOT


@pytest.mark.parametrize(
    "field,value",
    (
        ("BUNDLE_BODY_PROOF_NODES", 0),
        ("BUNDLE_BYTES", 0),
        ("BUNDLE_BYTES", -1),
        ("BUNDLE_BYTES", True),
        ("BUNDLE_SHA256", ""),
        ("BUNDLE_SHA256", "0" * 64),
        ("BUNDLE_SHA256", "A" * 64),
        ("BUNDLE_SHA256", "g" * 64),
        ("BUNDLE_SHA256", "a" * 63),
        ("BUNDLE_NODE_COUNT", 1),
        ("BUNDLE_EDGE_COUNT", 1),
        ("FRONTIER_COUNT", 1),
    ),
)
def test_unsealed_or_malformed_artifact_metadata_blocks_all_current_entrypoints(
    alpha, closure, exporter, monkeypatch, field, value
):
    _forbid_proof_loading(monkeypatch, alpha, closure)
    monkeypatch.setattr(closure, "EXPECTED_GAUSSIAN_FACTORIZATION_" + field, value)
    session = driver.LabSession()
    for command in (
        "pa lib alpha",
        f"pa lib alpha {GAUSSIAN_ROOT}",
        f"pa lib alpha check {GAUSSIAN_ROOT}",
        f"pa lean alpha {GAUSSIAN_ROOT}",
        f"pa proof alpha {GAUSSIAN_ROOT}",
    ):
        output = session.run(command)
        assert "not sealed for checked use" in output
        assert "Checked-use authority: YES" not in output
        assert "kernel check: PASS" not in output
    with pytest.raises(lean_proof_strand.ProofStrandError, match="not sealed"):
        lean_proof_strand._edition_view("alpha")
    with pytest.raises(ValueError, match="not sealed"):
        exporter._load_selected_specification(
            SimpleNamespace(edition="alpha", theorem=GAUSSIAN_ROOT)
        )
    assert "432 scripted theorems" in session.run("pa lib")
    assert lean_proof_strand._edition_view("stable")[1] == "stable"


@pytest.mark.parametrize("name", (GAUSSIAN_ROOT, "gaussian_gcd_bezout_exists"))
def test_large_gaussian_browser_replay_stops_before_any_proof_loading(
    alpha, closure, monkeypatch, name
):
    _forbid_proof_loading(monkeypatch, alpha, closure)

    output = driver.LabSession().run(f"pa lib alpha check {name}")

    assert "Checked-use authority: YES" in output
    assert "browser replay blocked for safety" in output
    assert "dependency closure exceeds 128 theorem entries" in output
    assert "no proof certificate was loaded" in output
    assert "Independent empty-context kernel check: PASS" not in output


def test_stable_boot_never_imports_current_alpha_or_gaussian_provider():
    code = """
import sys
import driver
session = driver.LabSession()
assert '432 scripted theorems' in session.run('pa lib')
assert 'Release edition: Stable.' in session.run('pa proof zero_add')
for name in ('editions_v29', 'editions_v30', 'editions_v31', 'editions_v32', 'editions_v33', 'editions_v34', 'campaign_gaussian_factorization_closure', 'campaign_completed_lower_closure', 'campaign_research_v32_closure', 'campaign_research_v33_closure', 'campaign_research_v34_closure'):
    assert 'peano_lab.library.' + name not in sys.modules, name
print('Stable boot remains independent of current Alpha')
"""
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "peano-lab" / "py")
    result = subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        timeout=35,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "Stable boot remains independent" in result.stdout


def test_current_integration_does_not_increase_browser_or_strand_limits():
    assert data_library._LEAN_BROWSER_LIMIT == 15_360
    assert data_library._LEAN_FULL_BROWSER_DEPENDENCY_LIMIT == 128
    assert data_library._PROOF_STRAND_STATEMENT_LIMIT == 4_096
    assert data_library._PROOF_STRAND_SCRIPT_LINES == 48
    assert data_library._PROOF_STRAND_DIRECT_DEPENDENCIES == 16
    assert lean_proof_strand.MAX_STRAND_NODES == 4_096
    assert lean_proof_strand.MAX_STRAND_EDGES == 65_536
    assert lean_proof_strand.MAX_STRAND_DEPTH == 256
    assert lean_proof_strand.MAX_STATEMENT_BYTES == 1_048_576
    assert lean_proof_strand.MAX_SCRIPT_BYTES == 1_048_576
    assert lean_proof_strand.MAX_TOTAL_SPECIFICATION_BYTES == 64 * 1024 * 1024
    assert lean_proof_strand.DEFAULT_PREVIEW_BYTES == 15_360
    assert lean_proof_strand.DEFAULT_MAX_MODULE_BYTES == 64 * 1024 * 1024
    assert lean_proof_strand.DEFAULT_LIVE_SOURCE_BYTES == 1_048_576
    assert lean_proof_strand.DEFAULT_LIVE_URL_BYTES == 512 * 1024
    assert lean_proof_strand.MAX_LIVE_URL_BYTES == 1_048_576
