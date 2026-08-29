"""Additive delivery routes preserve frozen evidence and exclude live services."""

from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import stage_lower_tier_checkpoint_navigation as nav
import stage_public_checkpoint_navigation as previous


@pytest.fixture
def proof_stage(tmp_path):
    root = tmp_path / "proofs"
    (root / "grand-campaign").mkdir(parents=True)
    (root / "checkpoints/lower-tier").mkdir(parents=True)
    for name in previous.SOURCE_PINS:
        (root / "grand-campaign" / name).write_bytes((previous.ATLAS / name).read_bytes())
    (root / "checkpoints/index.html").write_bytes(
        (ROOT / "book/_static/constructive-bottom-layer-publication/index.html").read_bytes())
    for name in ("index.html", "checkpoints.json"):
        (root / "checkpoints/lower-tier" / name).write_bytes((nav.PUBLIC / name).read_bytes())
    previous.stage_public_checkpoint_navigation(root)
    return root


def _tree(root):
    return {path.relative_to(root).as_posix(): path.read_bytes() for path in root.rglob("*") if path.is_file()}


def test_only_staged_atlas_html_changes_and_both_literal_checkpoint_trees_survive(proof_stage):
    before = _tree(proof_stage)
    assert nav.stage_lower_tier_navigation(proof_stage) is True
    after = _tree(proof_stage)
    assert before.keys() == after.keys()
    assert [name for name in before if before[name] != after[name]] == ["grand-campaign/index.html"]
    assert after["grand-campaign/index.html"] == nav.expected_atlas()
    assert b"296 distinct additional proofs" in after["grand-campaign/index.html"]
    assert b"not Alpha or Stable admissions" in after["grand-campaign/index.html"]
    assert b"data-proof-lower-tier" in after["grand-campaign/index.html"]
    assert nav.stage_lower_tier_navigation(proof_stage) is False
    assert nav.stage_lower_tier_navigation(proof_stage, check=True) is False


def test_readonly_check_never_repairs_an_unstaged_overlay(proof_stage):
    before = _tree(proof_stage)
    with pytest.raises(previous.CheckpointNavigationError, match="missing or stale"):
        nav.stage_lower_tier_navigation(proof_stage, check=True)
    assert _tree(proof_stage) == before


@pytest.mark.parametrize("name", ("grand-campaign/index.html", "grand-campaign/campaign.json",
    "grand-campaign/definitions.json", "checkpoints/lower-tier/index.html", "checkpoints/lower-tier/checkpoints.json"))
def test_stale_or_modified_inputs_are_not_rewritten(proof_stage, name):
    path = proof_stage / name
    path.write_bytes(path.read_bytes() + b" ")
    before = _tree(proof_stage)
    with pytest.raises(previous.CheckpointNavigationError):
        nav.stage_lower_tier_navigation(proof_stage)
    assert _tree(proof_stage) == before


@pytest.mark.parametrize("name", ("grand-campaign/index.html", "grand-campaign/campaign.json",
    "grand-campaign/definitions.json", "checkpoints/index.html", "checkpoints/lower-tier/index.html",
    "checkpoints/lower-tier/checkpoints.json"))
def test_missing_inputs_fail_before_a_write(proof_stage, name):
    (proof_stage / name).unlink()
    before = _tree(proof_stage)
    with pytest.raises(previous.CheckpointNavigationError):
        nav.stage_lower_tier_navigation(proof_stage)
    assert _tree(proof_stage) == before


@pytest.mark.parametrize("name", ("grand-campaign/index.html", "grand-campaign/campaign.json",
    "checkpoints/lower-tier/index.html", "checkpoints/lower-tier/checkpoints.json"))
def test_symlinks_cannot_write_through_to_source(proof_stage, tmp_path, name):
    path = proof_stage / name
    target = tmp_path / "preserved"
    original = path.read_bytes()
    target.write_bytes(original)
    path.unlink()
    path.symlink_to(target)
    with pytest.raises(previous.CheckpointNavigationError):
        nav.stage_lower_tier_navigation(proof_stage)
    assert target.read_bytes() == original


def test_atomic_replacement_preserves_hardlinked_source(proof_stage, tmp_path):
    path = proof_stage / "grand-campaign/index.html"
    preserved = tmp_path / "preserved.html"
    preserved.hardlink_to(path)
    original = preserved.read_bytes()
    nav.stage_lower_tier_navigation(proof_stage)
    assert preserved.read_bytes() == original
    assert not path.samefile(preserved)


def test_frozen_atlas_cannot_be_selected_as_staging(proof_stage, monkeypatch):
    monkeypatch.setattr(previous, "ATLAS", proof_stage / "grand-campaign")
    before = _tree(proof_stage)
    with pytest.raises(previous.CheckpointNavigationError, match="not a staging"):
        nav.stage_lower_tier_navigation(proof_stage)
    assert _tree(proof_stage) == before


def test_hub_has_three_exact_chapters_and_does_not_promote_them():
    page = (ROOT / "deploy/proofs/index.html").read_text()
    for slug in ("divisor-sums", "signed-weighted-sums", "prime-field-polynomials"):
        assert f'href="checkpoints/lower-tier/{slug}/?v=ac7111ec14ff"' in page
    assert "126 new complete proofs" in page
    assert "not new Alpha or Stable admissions" in page
    assert "337 definitions and 697 actual expansion arrows" in page
    assert "170 complete proofs" in page


def test_make_gates_public_proofs_before_staging_and_never_deploys_a_service():
    output = subprocess.run(["make", "-n", "stage-proofs"], cwd=ROOT, text=True,
                            capture_output=True, check=True).stdout
    verify = "python3 scripts/build_constructive_lower_tier_publication.py --check"
    copy = "rsync -a --delete book/_static/constructive-lower-tier-publication/"
    overlay = "python3 scripts/stage_lower_tier_checkpoint_navigation.py"
    selector = "python3 scripts/stage_public_lean_selector.py"
    assert output.index(verify) < output.index(copy) < output.index(overlay) < output.index(selector)
    assert '"_deploy/proofs/checkpoints/lower-tier/"' in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output
    assert "build_peano_library_channels_v31.py" not in output
    assert "public_lean_tunnel.py start" not in output


def test_new_proof_bundle_copies_are_tracked_but_training_checkpoints_are_ignored():
    proof = "book/_static/constructive-lower-tier-publication/checkpoints/lower-tier-divisor-sums-proof-bundle-v1.json"
    result = subprocess.run(["git", "check-ignore", "--no-index", proof, "results/peano-policy/checkpoints/weights.bin"],
                            cwd=ROOT, text=True, capture_output=True, check=True)
    assert proof not in result.stdout.splitlines()
    assert "results/peano-policy/checkpoints/weights.bin" in result.stdout.splitlines()
