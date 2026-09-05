"""Public builds stay hidden without altering the local builder or proof bytes."""
from pathlib import Path
import json
import os
import stat
import subprocess

import pytest

from proof_explorer_layout import LayoutError
import stage_public_proof_policy as policy


def fixture_base(tmp_path):
    base = tmp_path / "proofs-layout-v1"
    page = "family/explorer/defined/tag/T.html"
    before = b'<html><head><script defer src="/proofs/assets/lean-selector.js"></script></head><body><main><p data-current-release="v34">Release</p><div>Proof</div><aside>Receipt</aside></main></body></html>'
    after = before.replace(b'<p data-current-release="v34">', b'<p data-current-release="v34" style="grid-column: 1 / -1;">')
    payloads = {
        page: after,
        policy.PUBLIC_SELECTOR: (policy.ROOT / policy.LOCAL_SELECTOR).read_bytes(),
        "assets/explorer.js": b'"use strict"; // Original graph\n',
        "family/api/proof.json": b'{"proof":"unchanged"}\n',
        "release-v34/manifest.json": b'{"historical":"unchanged"}\n',
    }
    original = {name: policy.pin(raw) for name, raw in payloads.items()}
    original[page] = policy.pin(before)
    layout = dict(schema="peano-proof-explorer-layout-v1", presentation_only=True,
        proof_bytes_changed=False, original_assets_changed=False,
        alpha_admission_performed=False, stable_admission_performed=False,
        changed_files={page: {"before": policy.pin(before), "after": policy.pin(after)}},
        base_file_count=len(original), families=["family"],
        base_inventory_sha256=policy.sha256(policy.canonical(original)).hexdigest())
    payloads[policy.BASE_MANIFEST] = policy.canonical(layout)
    for name, raw in payloads.items():
        path = base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return base, policy.sha256(payloads[policy.BASE_MANIFEST]).hexdigest()


def test_public_asset_performs_no_dom_or_network_actions():
    harness = r'''
const fs = require("fs"), vm = require("vm");
const forbidden = new Proxy({}, {get(_target, key) { throw new Error("Unexpected public action: " + String(key)); }});
const source = fs.readFileSync(process.argv[1], "utf8");
vm.runInNewContext(source, {window: forbidden, document: forbidden,
  fetch() { throw new Error("Unexpected public request"); },
  setTimeout() { throw new Error("Unexpected public timer"); }}, {timeout: 1000});
console.log("Inactive public selector: no DOM or network actions.");
'''
    result = subprocess.run(["node", "-e", harness, str(policy.ROOT / policy.DISABLED_SELECTOR)],
        capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "no DOM or network actions" in result.stdout


def test_policy_changes_only_public_selector_and_preserves_every_page_and_local_tool(tmp_path):
    base, digest = fixture_base(tmp_path)
    original = policy.inventory(base)
    local = (policy.ROOT / policy.LOCAL_SELECTOR).read_bytes()
    output = tmp_path / "proofs-public-v1"
    result = policy.stage(base, output, accepted_sha256=digest)
    assert result["changed_files"] == result["selector_pages"] == result["family_count"] == 1
    assert result["public_on_demand_builds"] is False
    assert policy.inventory(base) == original
    assert (policy.ROOT / policy.LOCAL_SELECTOR).read_bytes() == local
    assert b'method: "POST"' in local and b"Build Lean proof" in local
    actual = policy.inventory(output)
    assert {name for name in original if original[name] != actual[name]} == {policy.PUBLIC_SELECTOR}
    assert set(actual) - set(original) == {policy.POLICY_MANIFEST}
    metadata = json.loads((output / policy.POLICY_MANIFEST).read_bytes())
    assert metadata["html_bytes_changed"] is False
    assert metadata["generated_lean_live_links"] is False
    assert metadata["runtime_services_changed"] is False
    assert metadata["local_builder_changed"] is False
    assert policy.stage(base, output, check=True, accepted_sha256=digest)["manifest_sha256"] == result["manifest_sha256"]
    with pytest.raises(LayoutError, match="already exists"):
        policy.stage(base, output, accepted_sha256=digest)


def test_new_public_tree_has_readable_modes_even_with_a_private_operator_umask(tmp_path):
    base, digest = fixture_base(tmp_path)
    output = tmp_path / "proofs-public-v1"
    previous = os.umask(0o077)
    try:
        policy.stage(base, output, accepted_sha256=digest)
    finally:
        os.umask(previous)
    for path in (output, *output.rglob("*")):
        assert stat.S_IMODE(path.stat().st_mode) == (0o755 if path.is_dir() else 0o644)


@pytest.mark.parametrize("fault", ("proof", "page", "asset", "manifest", "extra-input", "linked-input", "same-root", "nested-output", "linked-output", "changed-output", "extra-output", "changed-policy-manifest", "reenabled-selector"))
def test_policy_rejects_unaccepted_inputs_overwrites_and_tampered_outputs(tmp_path, fault):
    base, digest = fixture_base(tmp_path)
    output = tmp_path / "proofs-public-v1"
    if fault in ("changed-output", "extra-output", "changed-policy-manifest", "reenabled-selector"):
        policy.stage(base, output, accepted_sha256=digest)
        target = {"changed-output": "family/api/proof.json", "extra-output": "unexpected.json", "changed-policy-manifest": policy.POLICY_MANIFEST, "reenabled-selector": policy.PUBLIC_SELECTOR}[fault]
        (output / target).write_bytes(b'{"changed":true}\n')
    elif fault == "manifest":
        digest = "0" * 64
    elif fault in ("proof", "page", "asset", "extra-input"):
        target = {"proof": "family/api/proof.json", "page": "family/explorer/defined/tag/T.html", "asset": policy.PUBLIC_SELECTOR, "extra-input": "unexpected.json"}[fault]
        (base / target).write_bytes(b'changed\n')
    elif fault == "linked-input":
        (base / "linked.json").symlink_to(base / "family/api/proof.json")
    elif fault == "linked-output":
        output.symlink_to(base, target_is_directory=True)
    elif fault == "same-root":
        output = base
    elif fault == "nested-output":
        output = base / "nested"
    with pytest.raises(LayoutError):
        policy.stage(base, output, check=fault in ("changed-output", "extra-output", "changed-policy-manifest", "reenabled-selector"), accepted_sha256=digest)
