"""Read-only v34 historical projection boundaries and exact route conservation."""
import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest

ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT/"scripts",ROOT/"peano-lab/py"):
    if str(path) not in sys.path:sys.path.insert(0,str(path))
import constructive_research_publication_v34 as publication

def test_four_actual_v33_parents_and66_families_preserved():
    families=[];tags=set()
    assert set(publication.OLDER)=={"research","completed","historical","polynomial"}
    for directory,size,digest in publication.OLDER.values():
        raw=(ROOT/"book/_static"/directory/"manifest.json").read_bytes()
        assert len(raw)==size and sha256(raw).hexdigest()==digest
        for item in json.loads(raw)["families"]:
            families.append(item["slug"]);tags.update(item.get("tags",{}).values())
    assert len(families)==len(set(families))==66 and len(tags)==870
    assert not any(tag.startswith(("PG","CG")) for tag in tags)

@pytest.mark.parametrize("old,new",[("Current Alpha: 4,092","Current Alpha: 4,223"),
    ("Current Alpha has 4,092","Current Alpha has 4,223"),
    ("current Alpha v33","current Alpha v34"),
    ("Alpha v33 checked-use","Alpha v34 checked-use"),
    ("First admitted Alpha v33","First admitted Alpha v33")])
def test_current_only_text_projection(old,new):
    assert publication._current_text(old)==new

def test_pure_projection_preserves_original_math_and_false_authority():
    current={"alpha_edition_version":"v34","alpha_edition_checked_use_count":4223}
    original={"alpha_edition_version":"v33","nodes":[{"name":"unadmitted",
        "statement":"0 = 1","script":["unproved"],"dependencies":[],
        "alpha_checked_use":False,"first_admitted_version":"v31","alpha_edition_version":"v33"}]}
    before=deepcopy(original)
    result=publication._refresh_document(original,{},current)
    assert original==before
    assert result["nodes"][0]["alpha_checked_use"] is False
    assert result["nodes"][0]["statement"]=="0 = 1"
    assert result["nodes"][0]["first_admitted_version"]=="v31"
    assert result["nodes"][0]["alpha_edition_version"]=="v34"

@pytest.mark.parametrize("changed",[{}, {"checked_use":False,"body_checked":True},
    {"checked_use":True,"body_checked":False},
    {"checked_use":True,"body_checked":True,"statement":"0 = 1","statement_sha256":"changed"}])
def test_claimed_historical_proof_cannot_disappear_or_change(changed):
    original={"nodes":[{"name":"a","alpha_checked_use":True,"statement":"0 = 0","statement_sha256":"exact"}]}
    with pytest.raises(publication.PublicationError):
        publication._refresh_document(original,{"a":changed},{})

def test_new_output_paths_and_source_bindings():
    assert len(publication.OUTPUT_NAMES)==6
    assert all(name.endswith("-v34") for name in publication.OUTPUT_NAMES.values())
    tree=ast.parse(Path(publication.__file__).read_text())
    require=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=="require_render_inputs")
    text=ast.unparse(require)
    assert "previous.require_render_inputs()" in text
    assert "source_paths()" in text
    assert "test_constructive_polynomial_gcd_definitions_v34.py" in text


@pytest.mark.parametrize("current_count", (4223, 4092))
def test_current_manifest_count_observation_without_live_authority(tmp_path, current_count):
    """Exercise the actual UI helper on inert local bytes, never a live token."""
    from tests.test_constructive_research_publication_v34 import _manifest

    context = SimpleNamespace(catalog_sha256="a" * 64, revision="a" * 12,
        catalog={"edition_identity_sha256": "b" * 64},
        source_binding_sha256="c" * 64, render_source_binding_sha256="d" * 64,
        proof_authority=False, admission_performed=False)
    files = dict(publication._assets())
    pins = {name: {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
            for name, raw in files.items()}
    manifest = {"phase": "gcd-congruence", "families": [{"slug": "observation-only"}],
        "alpha_edition_version": "v34", "alpha_edition_checked_use_count": current_count,
        "stable_edition_count": 432, "catalog_sha256": context.catalog_sha256,
        "html_revision": context.revision,
        "edition_identity_sha256": context.catalog["edition_identity_sha256"],
        "release_source_binding_sha256": context.source_binding_sha256,
        "render_source_binding_sha256": context.render_source_binding_sha256,
        "current_G009_multiplicative_closure_proved": True,
        "current_G091_prime_power_fields_proved": False,
        "files": dict(pins), "file_count_excluding_manifest": len(files),
        "fixture_notice": "NONAUTHORIZING manifest-helper observation only"}
    files["manifest.json"] = json.dumps(manifest).encode()
    pins["manifest.json"] = {"bytes": len(files["manifest.json"]),
        "sha256": sha256(files["manifest.json"]).hexdigest()}
    for name, raw in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
    actual = {"directory": tmp_path, "phase": "gcd-congruence", "context": context,
        "inventory": {"files": pins}}
    with pytest.raises(publication.PublicationError):
        publication.require_live(context)
    if current_count == 4223:
        _manifest(actual, ("observation-only",))
    else:
        with pytest.raises(AssertionError):
            _manifest(actual, ("observation-only",))
    assert context.proof_authority is context.admission_performed is False
