"""Non-admitting research publication stays separate from Alpha and production."""

from hashlib import sha256
import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SPEC = importlib.util.spec_from_file_location(
    "public_checkpoint_navigation", ROOT / "scripts/stage_public_checkpoint_navigation.py"
)
assert SPEC is not None and SPEC.loader is not None
NAV = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = NAV
SPEC.loader.exec_module(NAV)


@pytest.fixture
def proof_stage(tmp_path):
    root = tmp_path / "proofs"
    (root / "grand-campaign").mkdir(parents=True)
    (root / "checkpoints").mkdir()
    for name in NAV.SOURCE_PINS:
        (root / "grand-campaign" / name).write_bytes((NAV.ATLAS / name).read_bytes())
    (root / "checkpoints/index.html").write_text(
        '<html><body>Public HA/Lean-checked research checkpoints; not Alpha admitted.</body></html>'
    )
    return root


def _tree(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def test_atlas_navigation_changes_only_staged_html_and_never_admission_data(proof_stage):
    source = NAV._source()
    before = _tree(proof_stage)
    assert NAV.stage_public_checkpoint_navigation(proof_stage) is True
    after = _tree(proof_stage)
    assert before.keys() == after.keys()
    assert [name for name in before if before[name] != after[name]] == ["grand-campaign/index.html"]
    assert after["grand-campaign/index.html"] == NAV._overlay(source["index.html"])
    assert NAV._source() == source
    assert b"not Alpha or Stable admissions" in after["grand-campaign/index.html"]
    assert b"170 additional complete HA/Lean-checked" in after["grand-campaign/index.html"]
    assert b"prime-power field and M\xc3\xb6bius inversion goals remain open" in after["grand-campaign/index.html"]
    assert NAV.stage_public_checkpoint_navigation(proof_stage) is False
    assert NAV.stage_public_checkpoint_navigation(proof_stage, check=True) is False


def test_missing_overlay_check_is_read_only(proof_stage):
    before = _tree(proof_stage)
    with pytest.raises(NAV.CheckpointNavigationError, match="missing or stale"):
        NAV.stage_public_checkpoint_navigation(proof_stage, check=True)
    assert _tree(proof_stage) == before


@pytest.mark.parametrize("name", tuple(NAV.SOURCE_PINS))
def test_changed_staged_atlas_is_not_overwritten_or_resealed(proof_stage, name):
    target = proof_stage / "grand-campaign" / name
    target.write_bytes(target.read_bytes() + b"\n")
    before = _tree(proof_stage)
    with pytest.raises(NAV.CheckpointNavigationError):
        NAV.stage_public_checkpoint_navigation(proof_stage)
    assert _tree(proof_stage) == before


@pytest.mark.parametrize("relative", (
    "grand-campaign/index.html", "grand-campaign/campaign.json",
    "grand-campaign/definitions.json", "checkpoints/index.html",
))
def test_missing_staging_inputs_fail_before_any_write(proof_stage, relative):
    (proof_stage / relative).unlink()
    before = _tree(proof_stage)
    with pytest.raises(NAV.CheckpointNavigationError):
        NAV.stage_public_checkpoint_navigation(proof_stage)
    assert _tree(proof_stage) == before


@pytest.mark.parametrize("relative", (
    "grand-campaign/index.html", "grand-campaign/campaign.json", "checkpoints/index.html",
))
def test_staged_symlinks_cannot_modify_sources(proof_stage, tmp_path, relative):
    target = proof_stage / relative
    external = tmp_path / "external.html"
    original = target.read_bytes()
    external.write_bytes(original)
    target.unlink()
    target.symlink_to(external)
    with pytest.raises(NAV.CheckpointNavigationError):
        NAV.stage_public_checkpoint_navigation(proof_stage)
    assert external.read_bytes() == original


def test_staged_hard_link_does_not_modify_the_original_inode(proof_stage, tmp_path):
    target = proof_stage / "grand-campaign/index.html"
    original = target.read_bytes()
    preserved = tmp_path / "original.html"
    preserved.hardlink_to(target)
    NAV.stage_public_checkpoint_navigation(proof_stage)
    assert preserved.read_bytes() == original
    assert not target.samefile(preserved)


def test_symlinked_staging_root_is_rejected(proof_stage, tmp_path):
    linked = tmp_path / "linked"
    linked.symlink_to(proof_stage, target_is_directory=True)
    with pytest.raises(NAV.CheckpointNavigationError, match="ordinary directory"):
        NAV.stage_public_checkpoint_navigation(linked)


def test_changed_frozen_source_is_rejected_before_staging(proof_stage, tmp_path, monkeypatch):
    source = tmp_path / "frozen"
    source.mkdir()
    for name in NAV.SOURCE_PINS:
        (source / name).write_bytes((NAV.ATLAS / name).read_bytes())
    (source / "index.html").write_bytes((source / "index.html").read_bytes() + b"\n")
    monkeypatch.setattr(NAV, "ATLAS", source)
    before = _tree(proof_stage)
    with pytest.raises(NAV.CheckpointNavigationError, match="source changed"):
        NAV.stage_public_checkpoint_navigation(proof_stage)
    assert _tree(proof_stage) == before


def test_staging_refuses_to_overlay_the_frozen_source_itself(proof_stage, monkeypatch):
    monkeypatch.setattr(NAV, "ATLAS", proof_stage / "grand-campaign")
    before = _tree(proof_stage)
    with pytest.raises(NAV.CheckpointNavigationError, match="not a staging destination"):
        NAV.stage_public_checkpoint_navigation(proof_stage)
    assert _tree(proof_stage) == before


def test_navigation_input_has_an_explicit_bounded_read(tmp_path, monkeypatch):
    path = tmp_path / "oversized.html"
    path.write_bytes(b"x" * 11)
    monkeypatch.setattr(NAV, "MAX_BYTES", 10)
    with pytest.raises(NAV.CheckpointNavigationError, match="oversized"):
        NAV._read(path)


def test_original_atlas_pins_and_added_links_are_explicit():
    source = NAV._source()
    assert {name: sha256(payload).hexdigest() for name, payload in source.items()} == NAV.SOURCE_PINS
    result = NAV._overlay(source["index.html"])
    assert result.count(b"data-proof-checkpoints") == 1
    assert result.count(b"data-checkpoint-publication-notice") == 1
    assert result.count(b"../checkpoints/?v=ac7111ec14ff") == 2
    assert b"Alpha v31" not in result
    for anchor in (NAV.NAV_ANCHOR, NAV.NOTICE_ANCHOR):
        with pytest.raises(NAV.CheckpointNavigationError, match="unique"):
            NAV._overlay(source["index.html"] + anchor)


def test_make_stages_verified_checkpoints_durably_without_deploying():
    output = subprocess.run(["make", "-n", "stage-proofs"], cwd=ROOT,
                            check=True, capture_output=True, text=True).stdout
    verify = "python3 scripts/build_constructive_bottom_layer_publication.py --check"
    copy = "rsync -a --delete book/_static/constructive-bottom-layer-publication/"
    overlay = "python3 scripts/stage_public_checkpoint_navigation.py"
    selector = "python3 scripts/stage_public_lean_selector.py"
    assert output.index(verify) < output.index(copy) < output.index(overlay) < output.index(selector)
    assert '"_deploy/proofs/checkpoints/"' in output
    assert "lts-faculty.wmi.amu.edu.pl:" not in output
    assert "scripts/build_peano_library_channels_v31.py" not in output
    assert "public_lean_tunnel.py start" not in output


def test_hub_distinguishes_all_four_checkpoint_families_from_alpha():
    page = (ROOT / "deploy/proofs/index.html").read_text()
    for slug in ("euler-units", "prime-fields", "mobius-values", "signed-sums"):
        assert f'href="checkpoints/{slug}/?v=ac7111ec14ff"' in page
    assert 'href="checkpoints/grand-campaign/?v=ac7111ec14ff"' in page
    assert "170 complete proofs" in page
    assert "not yet Alpha-enrolled or Stable" in page
    assert "Alpha v30 remains 3,222 entries and Stable remains 432" in page


@pytest.mark.parametrize("directory", (
    "constructive-bottom-layer-explorer", "constructive-bottom-layer-publication",
))
def test_gitignore_includes_real_proof_certificates_not_training_checkpoints(directory):
    proof = f"book/_static/{directory}/checkpoints/bottom-layer-euler-units-proof-bundle-v2.json"
    ignored = subprocess.run(
        ["git", "check-ignore", "--no-index", proof, "results/peano-policy/checkpoints/weights.bin"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.splitlines()
    assert proof not in ignored
    assert "results/peano-policy/checkpoints/weights.bin" in ignored
