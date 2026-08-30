"""Current v31 lower-campaign UI remains exact, opt-in and proof-lazy."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import driver
import pytest

from peano_lab.library import campaign_completed_lower_closure as closure
from peano_lab.library import lean_proof_strand, theorems
from peano_lab.ui import data_library


ROOT = Path(__file__).resolve().parents[3]
# One independently pinned principal per family, plus the general inverse criterion.
PRINCIPALS = (
    ("euler-units", "euler_coprime_totient_power", "4f3533b3d207055a1f56ca77655cf26a381735fa3999f34a0a2c7935a21497e4"),
    ("prime-fields", "prime_field_of_prime_order_exists", "f0a61089155f5bb6cd5e6fa79774756a296253a412e2b131bf8f491e8099b8a7"),
    ("mobius-values", "mobius_fresh_prime_negates", "2b0116e6d32e45fe7ae5e9a8bd7c11e5f95a88021cd42786276cff6e7ec303d2"),
    ("signed-sums", "divisor_signed_sum_permutation_invariant", "0e94ef4db7c6f73d73ae87525d29e24722764adabcd38a908ab3a844bfec57ac"),
    ("divisor-sums", "signed_divisor_sum_exists_unique", "c148a766390471cd871ca467503a9a7c380142964aff8830ca412a20f743ba6d"),
    ("signed-weighted-sums", "signed_weighted_sum_add_linearity", "0515fa77e429a50f266b273b77efa2682ec7cc78c3e30948559d6a5c3363f255"),
    ("prime-field-polynomials", "prime_field_polynomial_reduce_and_evaluate_exists", "2f0d67795bf12542c6c9fb48cb4d63d26213e8e090bbca1a7a89257a49dd0e2c"),
    ("divisor-involutions", "divisor_complement_prefix_involution", "24bdefde49ebf80220bf5c974be3261d250dc98472d1228f6f3484492a9f34c1"),
    ("mobius-divisor-cancellation", "mobius_divisor_sum_cancellation_on_positive_values", "be20bbedecba3566c7d3611f121e3d2e4fdaffd7fdee715dcd7e60afdb4cfd56"),
    ("rectangular-sums", "signed_rectangular_row_major_fubini", "df286640d573e43c4ce8fc84ed9a405eb4568577f4f683001adb7ae8324ff3ec"),
    ("polynomial-products", "prime_field_polynomial_convolution_represented_degree_exists", "8ff4406ec7462fc8e97a47932550abde9c428392cda01a1c86fe2dfd082fc51a"),
    ("finite-support", "signed_prefix_sum_zero_padding_iff", "0a6919b464fecaa0138aef0d8ce9f24d3e2f48357a29544523c17e67b3200f4e"),
    ("dirichlet-convolution", "dirichlet_convolution_padded_prefix_iff", "81ea53acd86ba6b094a55b9de9d69ee97c444f5a9f5eedfa3e5e6c9afcb9002e"),
    ("dirichlet-fubini", "dirichlet_convolution_associative_tables_exists", "f0e95e4639f59cc7b592d82384c2cf72b63e594814599db6b7bf24339b35adc1"),
    ("dirichlet-units", "dirichlet_constant_one_realizes_divisor_sum", "5aafb1de83c084f4d86aef3f3649ebc962a43b64c55c7356c45500c8db072d09"),
    ("mobius-inversion", "mobius_inversion_iff", "c98dbac33cefe8835eb9c023fd942e6fcb998e7bb8ca0607989b462724a8cad1"),
    ("dirichlet-signed-units", "dirichlet_signed_unit_affine_unique", "68b300d496090f0911613338c333747776a606c71fd28d4c82849bfca1c32d11"),
    ("dirichlet-triangular", "dirichlet_convolution_strict_prefix_exists", "745ac62f2fbed061d5ba9f77972361c063ec4020ed9e52144bd2a1b8a38b96d1"),
    ("dirichlet-inverses", "dirichlet_inverse_exists_positive_unique", "eb7703bdacfaca3d2d4a6c0cf5d2a43326be82107047a7609ce053da0fedd164"),
    ("dirichlet-inverses", "dirichlet_inverse_criterion", "8c777567eae9fae4a3b6f0e0df4e4d80205c694f5b15f93f1808376e1b7d05fc"),
)
LARGE_INVERSE = "dirichlet_inverse_exists_positive_unique"


@pytest.fixture(scope="module")
def alpha():
    from peano_lab.library import editions_v31
    return editions_v31


@pytest.fixture(scope="module")
def exporter():
    spec = importlib.util.spec_from_file_location(
        "peano_alpha_v31_ui_exporter", ROOT / "scripts/export_peano_lean.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _forbid_proof_use(monkeypatch, alpha):
    def forbidden(*_args, **_kwargs):
        raise AssertionError("a metadata/preview route loaded or replayed an actual proof")

    for edition, provider in (
        (alpha, "completed_lower"),
        (alpha.v30, "gaussian_factorization"),
        (alpha.v30.v29, "priority_layer"),
        (alpha.v30.v29.v28, "lower_layer"),
    ):
        monkeypatch.setattr(edition, "replay", forbidden)
        monkeypatch.setattr(edition, "_checked_" + provider + "_bundle", forbidden)
        monkeypatch.setattr(edition, "checked_" + provider + "_bundle", forbidden)
    for name in (
        "read_completed_lower_bundle_bytes", "check_completed_lower_proof_bundle",
        "completed_lower_plan", "completed_lower_specs", "_load_completed_lower_specs",
    ):
        monkeypatch.setattr(closure, name, forbidden)
    for name in ("replay", "lean_export", "export_checked_theorem"):
        monkeypatch.setattr(data_library, name, forbidden)
    monkeypatch.setattr(lean_proof_strand, "build_proof_strand", forbidden)


def test_exact_current_inventory_preserves_v30_and_stable(alpha, monkeypatch):
    _forbid_proof_use(monkeypatch, alpha)
    assert len(alpha.ALPHA_ENTRIES) == 3796 and len(alpha.FRONTIER_NEW_NAMES) == 574
    assert len(alpha.v30.ALPHA_ENTRIES) == 3222
    assert len(alpha.v30.FRONTIER_NEW_NAMES) == 180
    assert alpha.STABLE_ENTRIES is alpha.v30.STABLE_ENTRIES
    assert all(current is old for current, old in zip(alpha.ALPHA_ENTRIES, alpha.v30.ALPHA_ENTRIES))
    assert len({slug for slug, _, _ in PRINCIPALS}) == 19
    output = driver.LabSession().run("pa lib alpha")
    assert "immutable Alpha v31" in output
    assert "Enrolled statements: 3,796" in output
    assert "Stable closed: 432" in output and "Alpha closed: 3,364" in output
    assert "Previously added Alpha v30 campaign results: 180" in output
    assert "New constructive campaign results: 574" in output
    assert alpha.ALPHA_V31_IDENTITY_SHA256 in output
    assert "Independent empty-context kernel check: PASS" not in output


@pytest.mark.parametrize("slug,name,digest", PRINCIPALS, ids=[name for _, name, _ in PRINCIPALS])
def test_all_nineteen_family_principals_and_general_criterion_have_exact_metadata(alpha, monkeypatch, slug, name, digest):
    _forbid_proof_use(monkeypatch, alpha)
    entry = alpha.entry(name, edition="alpha")
    assert entry is not None and entry.checked_use
    assert name in alpha.FRONTIER_NEW_NAMES and alpha.v30.entry(name, edition="alpha") is None
    assert alpha.entry(name, edition="stable") is None and theorems.get(name) is None
    assert closure.FAMILY_BY_NAME[name].slug == slug
    assert sha256(entry.spec.statement.encode()).hexdigest() == digest
    output = driver.LabSession().run("pa lib alpha " + name)
    assert f"{name} — Alpha v31 theorem evidence" in output
    assert "Release evidence: alpha_closed" in output
    assert "Release membership: alpha_only" in output
    assert "Checked-use authority: YES" in output
    assert "This evidence card does not itself replay a proof." in output
    assert entry.spec.summary in output
    assert "Independent empty-context kernel check: PASS" not in output


@pytest.mark.parametrize("slug,name,digest", PRINCIPALS, ids=[name for _, name, _ in PRINCIPALS])
@pytest.mark.parametrize("command", ("pa proof alpha", "pa lean alpha", "pa lean alpha exact", "pa lean alpha tactics"))
def test_actual_exact_and_defined_previews_keep_bounds_and_honest_not_run_status(alpha, monkeypatch, slug, name, digest, command):
    _forbid_proof_use(monkeypatch, alpha)
    output = driver.LabSession().run(command + " " + name)
    assert name in output and "Release edition: Alpha v31." in output
    assert "Authenticated release evidence: alpha_closed." in output
    assert "Checked-use authority: YES." in output
    assert "Independent Lean compilation: NOT RUN" in output
    assert "--edition alpha" in output and "--verify" in output
    assert "--proof-bundle" not in output
    assert len(output.encode("utf-8")) <= 15_360
    assert sha256(alpha.ALPHA_EDITION.by_name[name].spec.statement.encode()).hexdigest() == digest
    if command.startswith("pa proof"):
        assert "Fresh Peano proof replay: NOT RUN" in output
    else:
        assert "Fresh independent empty-context Peano kernel replay: NOT RUN" in output


@pytest.mark.parametrize("slug,name,digest", PRINCIPALS, ids=[name for _, name, _ in PRINCIPALS])
def test_exact_strand_plan_keeps_statement_and_current_identity_without_artifacts(alpha, monkeypatch, slug, name, digest):
    _forbid_proof_use(monkeypatch, alpha)
    plan = lean_proof_strand.plan_proof_strand(name, edition="alpha")
    assert plan.root == name and plan.edition_version == "v31"
    assert plan.edition_identity_sha256 == alpha.ALPHA_V31_IDENTITY_SHA256
    assert plan.root_node.evidence == "alpha_closed" and plan.root_node.membership == "alpha_only"
    assert sha256(plan.root_node.statement.encode()).hexdigest() == digest
    assert plan.root_node.source_path == alpha.ALPHA_EDITION.by_name[name].source_module
    assert plan.root_node.dependencies == alpha.ALPHA_EDITION.by_name[name].spec.dependencies


@pytest.mark.parametrize("slug,name,digest", PRINCIPALS, ids=[name for _, name, _ in PRINCIPALS])
def test_cli_selection_preserves_literal_current_spec_without_any_proof_io(alpha, exporter, monkeypatch, slug, name, digest):
    _forbid_proof_use(monkeypatch, alpha)
    monkeypatch.setattr(Path, "read_bytes", lambda *_a, **_k: pytest.fail("selection read proof bytes"))
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("selection opened a file"))
    spec, selected = exporter._load_selected_specification(SimpleNamespace(edition="alpha", theorem=name))
    assert selected is alpha and spec is alpha.ALPHA_EDITION.by_name[name].spec
    assert sha256(spec.statement.encode()).hexdigest() == digest


@pytest.mark.parametrize("slug", tuple(family.slug for family in closure.FAMILIES))
def test_any_unsealed_family_blocks_all_three_current_entrypoints_without_fallback(alpha, exporter, monkeypatch, slug):
    _forbid_proof_use(monkeypatch, alpha)
    changed = tuple(replace(family, artifact_bytes=0) if family.slug == slug else family
                    for family in closure.FAMILIES)
    monkeypatch.setattr(closure, "FAMILIES", changed)
    monkeypatch.setattr(closure, "COMPLETED_LOWER_FAMILIES", changed)
    session = driver.LabSession()
    for command in ("pa lib alpha", "pa lib alpha " + LARGE_INVERSE, "pa lean alpha " + LARGE_INVERSE,
                    "pa proof alpha " + LARGE_INVERSE):
        output = session.run(command)
        assert "not sealed" in output
        assert "Checked-use authority: YES" not in output and "kernel check: PASS" not in output
    with pytest.raises(lean_proof_strand.ProofStrandError, match="not sealed"):
        lean_proof_strand._edition_view("alpha")
    with pytest.raises(ValueError, match="not sealed"):
        exporter._load_selected_specification(SimpleNamespace(edition="alpha", theorem=LARGE_INVERSE))
    assert "432 scripted theorems" in session.run("pa lib")
    assert lean_proof_strand._edition_view("stable")[1] == "stable"


@pytest.mark.parametrize("command", (
    "pa lib alpha", "pa lib alpha dirichlet_inverse_criterion",
    "pa lib alpha check dirichlet_unit_at_one_witness", "pa lean alpha dirichlet_inverse_criterion",
    "pa proof alpha dirichlet_inverse_criterion",
))
def test_zero_current_count_fails_before_any_old_edition_fallback(alpha, monkeypatch, command):
    _forbid_proof_use(monkeypatch, alpha)
    monkeypatch.setattr(alpha, "EXPECTED_ALPHA_V31_COUNT", 0)
    monkeypatch.setattr(alpha.v30, "entry", lambda *_a, **_k: pytest.fail("unsealed current fell back to v30"))
    output = driver.LabSession().run(command)
    assert "Alpha v31 is not sealed for checked use" in output
    assert "Checked-use authority: YES" not in output
    assert "432 scripted theorems" in driver.LabSession().run("pa lib")


@pytest.mark.parametrize("command", ("pa lib alpha check", "pa lean alpha full"))
def test_38832_node_inverse_remains_blocked_before_browser_proof_loading(alpha, monkeypatch, command):
    # The ordinary certificate size is an independently checked release metric,
    # not an excuse to change the pre-existing 128-entry browser guard.
    _forbid_proof_use(monkeypatch, alpha)
    spec = alpha.ALPHA_EDITION.by_name[LARGE_INVERSE].spec
    assert data_library._lean_full_dependency_count(spec, edition="alpha", alpha_module=alpha) == 129
    output = driver.LabSession().run(command + " " + LARGE_INVERSE)
    assert "browser" in output.lower() and ("safety" in output.lower() or "safe" in output.lower())
    assert "no proof certificate was loaded" in output.lower()
    assert "kernel check: PASS" not in output
    assert "--verify" in output or "pa lean alpha " + LARGE_INVERSE in output


def test_no_ui_or_strand_resource_ceiling_was_increased():
    assert data_library._LEAN_BROWSER_LIMIT == 15_360
    assert data_library._LEAN_FULL_BROWSER_DEPENDENCY_LIMIT == 128
    assert data_library._PROOF_STRAND_STATEMENT_LIMIT == 4_096
    assert data_library._PROOF_STRAND_SCRIPT_LINES == 48
    assert data_library._PROOF_STRAND_DIRECT_DEPENDENCIES == 16
    assert lean_proof_strand.MAX_STRAND_NODES == 4_096
    assert lean_proof_strand.MAX_STRAND_EDGES == 65_536
    assert lean_proof_strand.MAX_STRAND_DEPTH == 256
    assert lean_proof_strand.MAX_TOTAL_SPECIFICATION_BYTES == 64 * 1024 * 1024
