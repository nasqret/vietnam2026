"""Global reading delivery is additive, authenticated and never clobbers a tree."""
from __future__ import annotations

import json
import os
from pathlib import Path
import stat
import subprocess

import pytest

from proof_explorer_layout import LayoutError
from proof_readability import strip_reading_layer
import stage_proof_readability as reader
from test_proof_readability import fixture


def base_fixture(tmp_path):
    base = tmp_path / "public"
    original = {
        "family/explorer/tag/T.html": fixture(),
        "family/explorer/defined/tag/T.html": fixture(defined=True),
        "family/api/corpus.json": b'{"unchanged":"mathematical evidence"}\n',
        "presentation/layout-v1.json": b'{"unchanged":"historical layout"}\n',
        "assets/defined-explorer.js": b'"use strict"; // immutable graph\n',
        "assets/lean-selector.js": b'"use strict"; // old selector\n',
    }
    before = {name: reader.pin(raw) for name, raw in original.items()}
    disabled = b'"use strict"; // disabled public build\n'
    original["assets/lean-selector.js"] = disabled
    manifest = dict(schema="peano-proof-public-lean-policy-v1", presentation_only=True,
        proof_bytes_changed=False, html_bytes_changed=False, public_on_demand_builds=False,
        alpha_admission_performed=False, stable_admission_performed=False, families=["family"],
        base_file_count=len(before), base_inventory_sha256=reader.sha256(reader.canonical(before)).hexdigest(),
        changed_files={"assets/lean-selector.js": {"before": before["assets/lean-selector.js"], "after": reader.pin(disabled)}})
    original[reader.BASE_MANIFEST] = reader.canonical(manifest)
    for name, raw in original.items():
        path = base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    return base, reader.sha256(original[reader.BASE_MANIFEST]).hexdigest()


def test_stage_preserves_all_original_mathematics_and_has_exact_page_recovery(tmp_path):
    base, accepted = base_fixture(tmp_path)
    before = reader.inventory(base)
    output = tmp_path / "readable"
    result = reader.stage(base, output, accepted_sha256=accepted)
    assert result["pages"] == 2 and result["families"] == 1
    assert reader.inventory(base) == before
    for name in before:
        raw = (output / name).read_bytes()
        if name.endswith(".html"):
            raw = strip_reading_layer(raw)
        assert reader.pin(raw) == before[name]
    manifest = json.loads((output / reader.MANIFEST).read_bytes())
    assert manifest["proof_bytes_changed"] is False
    assert manifest["original_assets_changed"] is False
    assert manifest["mathematical_definitions_changed"] is False
    assert manifest["public_on_demand_builds"] is False
    assert reader.stage(base, output, check=True, accepted_sha256=accepted)["manifest_sha256"] == result["manifest_sha256"]


@pytest.mark.parametrize("fault", ["source-proof", "source-page", "source-asset", "source-extra", "wrong-manifest", "same-root", "nested-output", "linked-output", "output-page", "output-audit", "output-asset", "output-extra", "overwrite"])
def test_changed_sources_unexpected_outputs_and_overwrites_are_rejected(tmp_path, fault):
    base, accepted = base_fixture(tmp_path)
    output = tmp_path / "readable"
    check = fault.startswith("output-")
    if check or fault == "overwrite":
        reader.stage(base, output, accepted_sha256=accepted)
        if check:
            target = {"output-page": "family/explorer/tag/T.html", "output-audit": reader.AUDIT,
                      "output-asset": "assets/proof-reader.js", "output-extra": "forged.json"}[fault]
            (output / target).write_bytes(b'forged\n')
    elif fault.startswith("source-"):
        target = {"source-proof": "family/api/corpus.json", "source-page": "family/explorer/tag/T.html",
                  "source-asset": "assets/defined-explorer.js", "source-extra": "extra.json"}[fault]
        (base / target).write_bytes(b'changed\n')
    elif fault == "wrong-manifest":
        accepted = "0" * 64
    elif fault == "same-root":
        output = base
    elif fault == "nested-output":
        output = base / "child"
    elif fault == "linked-output":
        output.symlink_to(base, target_is_directory=True)
    with pytest.raises(LayoutError):
        reader.stage(base, output, check=check, accepted_sha256=accepted)


def test_stage_is_readable_with_private_operator_umask(tmp_path):
    base, accepted = base_fixture(tmp_path)
    output = tmp_path / "readable"
    old = os.umask(0o077)
    try:
        reader.stage(base, output, accepted_sha256=accepted)
    finally:
        os.umask(old)
    for path in (output, *output.rglob("*")):
        assert stat.S_IMODE(path.stat().st_mode) == (0o755 if path.is_dir() else 0o644)


def test_historical_checkpoint_pages_do_not_become_a_new_alpha_family():
    records = {
        "family/explorer/defined/tag/T.html": dict(theorem="example", edition="defined", script_sha256="a", local_claim_count=1,
            large_display_claims=0, max_defined_claim_characters=12, curated_mathematical_explanation=False),
        "checkpoints/family/explorer/defined/tag/T.html": dict(theorem="example", edition="defined", script_sha256="b", local_claim_count=1,
            large_display_claims=0, max_defined_claim_characters=12, curated_mathematical_explanation=False),
    }
    audit = reader.reading_audit(records)
    assert audit["family_count"] == 1 and audit["historical_checkpoint_pages"] == 1
    assert audit["current_release_pages"] == 1 and audit["proof_authority"] is False


def test_reader_controls_links_search_and_print_without_network_or_proof_execution():
    harness = r'''
const fs=require("fs"), vm=require("vm"), assert=require("assert");
function el(tag="DIV") { return {tagName:tag,dataset:{},hidden:false,open:false,listeners:{},
  addEventListener(n,f){this.listeners[n]=f;}, closest(){return this;}, contains(){return true;},
  focus(){this.focused=true;},scrollIntoView(){this.scrolled=true;}}; }
const toolbar=el(), search=el("INPUT"), status=el(), summary=el("SUMMARY"), ledger=el("DETAILS");
ledger.matches=s=>s==="[data-reader-exact]"; ledger.querySelector=()=>summary;
const groups=[el("DETAILS"),el("DETAILS")];
groups[0].textContent="Establish a nonzero multiplier"; groups[1].textContent="Construct witness 0";
const reader=el();reader.nextElementSibling=ledger;
reader.querySelector=s=>({"[data-reader-toolbar]":toolbar,"[data-reader-search]":search,"[data-reader-status]":status}[s]);
reader.querySelectorAll=()=>groups;
const line=el("LI");line.parentElement=ledger;ledger.parentElement=null;
const document={readyState:"complete",querySelectorAll:()=>[reader],getElementById:id=>id==="L2"?line:null};
const window={location:{hash:""},listeners:{},addEventListener(n,f){this.listeners[n]=f;}};
const context={document,window,fetch(){throw Error("unexpected network")},XMLHttpRequest(){throw Error("unexpected network")}};
const code=fs.readFileSync(process.argv[1],"utf8");
vm.runInNewContext(code,context,{timeout:1000});
assert.strictEqual(toolbar.hidden,false);assert.strictEqual(reader.dataset.readerReady,"true");
const button=el("BUTTON");button.dataset.readerAction="open";
toolbar.listeners.click({target:button});assert(groups.every(x=>x.open));
button.dataset.readerAction="close";toolbar.listeners.click({target:button});assert(groups.every(x=>!x.open));
search.value="nonzero";search.listeners.input();assert(!groups[0].hidden&&groups[1].hidden);assert(status.textContent.startsWith("1 of 2"));
search.value="";search.listeners.input();assert(groups.every(x=>!x.hidden));
const link=el("A");link.hash="#L2";reader.listeners.click({target:link});assert(ledger.open);
ledger.open=false;button.dataset.readerAction="exact";toolbar.listeners.click({target:button});assert(ledger.open&&summary.focused&&ledger.scrolled);
window.listeners.beforeprint();assert(groups.every(x=>x.open));window.listeners.afterprint();assert(groups.every(x=>!x.open));
window.location.hash="#%malformed";window.listeners.hashchange();
window.location.hash="#L2";ledger.open=false;window.listeners.hashchange();assert(ledger.open);
const saved=toolbar.listeners.click;vm.runInNewContext(code,context,{timeout:1000});assert.strictEqual(toolbar.listeners.click,saved);
console.log("Reader controls, anchors, search, print restoration and no-network contract passed.");
'''
    result = subprocess.run(["node", "-e", harness, str(reader.ROOT / "deploy/proofs/proof-reader.js")], capture_output=True, text=True, timeout=5)
    assert result.returncode == 0, result.stdout + result.stderr


def test_reader_inherits_both_original_edition_palettes_including_dark_mode():
    css = (reader.ROOT / "deploy/proofs/proof-reader.css").read_text()
    exact = (reader.ROOT / "book/_static/pa-proof-explorer/assets/explorer.css").read_text()
    defined = (reader.ROOT / "book/_static/pa-proof-explorer/defined/assets/explorer.css").read_text()
    for token in ("paper", "paper-alt", "ink", "muted", "border", "accent", "sans"):
        assert f"var(--pd-{token}, var(--pe-{token}," in css
        assert f"--pe-{token}:" in exact and f"--pd-{token}:" in defined
    assert "var(--pa-" not in css
