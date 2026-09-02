"""V34 navigation authentication, never a mathematical acceptance fixture.

The three-file transport has deliberately EMPTY FALSE delta rows. Only file
bindings and navigation metadata are tested; no logical catalogue decoder,
proof checker, live release capability, subprocess or listener is supplied.
Actual published-package cases are separate and require real installed bytes.
"""
from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import shutil
import sys
from types import SimpleNamespace

import pytest
from tests import test_lean_strand_service_v33 as previous
from tests.test_lean_strand_service import ROOT, non_listening_review_server, service
import peano_catalog_shards_v34 as codec

PACKAGES = (
    "constructive-gcd-congruence-explorer-v34",
    "constructive-polynomial-euclidean-explorer-v34",
    "constructive-research-explorer-v34",
    "constructive-completed-lower-explorer-v34",
    "constructive-historical-explorers-v34",
)
FAMILIES = ("polynomial-gcd-bezout", "congruence-arithmetic")
ASSET_ROOT = ROOT / "book/_static"
_json, _write, _mutate, _current = previous._json, previous._write, previous._mutate, previous._current
owned_base = previous.owned_base


@pytest.fixture(scope="module")
def old_manifest():
    raw = (ROOT / "artifacts/peano-library/alpha/catalog-v33.json").read_bytes()
    assert len(raw) == 946819
    assert sha256(raw).hexdigest() == "6be052da195a295edce02f4b1955cd9e3dd71d7acefb9ac5794277eda7ef40cc"
    return json.loads(raw)


def _install(root, old, base):
    directory = root / "artifacts/peano-library/alpha"
    directory.mkdir(parents=True, exist_ok=True)
    parent = directory / "catalog-v30.json"
    if not parent.exists(): parent.hardlink_to(base)
    metadata = deepcopy(old["metadata"])
    metadata.update(schema=codec.LOGICAL_SCHEMA, theorem_count=4223, checked_use_count=4223,
        alpha_only_count=3791, frontier_v34_campaign_counts=dict(codec.EXPECTED_CAMPAIGNS),
        frontier_v34_ordered_names_sha256="e"*64,
        catalogue_capacity_v34=dict(codec.CAPACITY_METADATA),
        parent_alpha_v33={"notice": "transport fixture; no admission"},
        alpha_v34_research_promotion={"notice": "NOT A PROOF REPORT"})
    delta = _json({"schema": codec.DELTA_SCHEMA, "theorems": [],
                   "notice": "DELIBERATELY FALSE ROWS: navigation only"})
    _write(directory / codec.DELTA_BASENAME, delta)
    manifest = {"schema": codec.TRANSPORT_SCHEMA, "metadata": metadata,
        "parent": deepcopy(old["parent"]),
        "previous_v31_metadata": deepcopy(old["previous_v31_metadata"]),
        "previous_v32_metadata": deepcopy(old["previous_v32_metadata"]),
        "previous_v33_metadata": deepcopy(old["metadata"]),
        "delta": {"path": codec.DELTA_BASENAME, "schema": codec.DELTA_SCHEMA,
            "row_count": 1001, "bytes": len(delta), "sha256": sha256(delta).hexdigest()}}
    raw = _json(manifest)
    catalog = directory / "catalog-v34.json"
    _write(catalog, raw)
    digest, identity = sha256(raw).hexdigest(), metadata["edition_identity_sha256"]
    channel = root / "artifacts/peano-library/channels-v34.json"
    _write(channel, _json({"schema": "peano-library-channels-v34", "default_channel": "stable",
        "channels": {"alpha": {"artifact_path": "artifacts/peano-library/alpha/catalog-v34.json",
            "artifact_sha256": digest, "edition_identity_sha256": identity,
            "theorem_count": 4223, "checked_use_count": 4223}}}))
    campaign = root / "book/_static/constructive-research-campaign-v34/campaign.json"
    _write(campaign, _json({"schema": "constructive-grand-campaign-v1",
        "meta": {"current_alpha_version": "v34", "current_alpha_checked_use_count": 4223},
        "ambitious_boundaries": {"alpha_v34_edition": {"role": "current_immutable_release",
            "catalog_sha256": digest, "identity_sha256": identity,
            "theorem_count": 4223, "checked_use_count": 4223}}}))
    return SimpleNamespace(root=root, static=root/"book/_static", directory=directory,
        version="v34", codec=codec, digest=digest, identity=identity, count=4223,
        channel=channel, campaign=campaign, catalog=catalog, server=non_listening_review_server(root))


@pytest.fixture
def release(tmp_path, old_manifest, owned_base, monkeypatch):
    root=tmp_path.resolve()
    monkeypatch.setattr(service, "ROOT", root)
    return _install(root, old_manifest, owned_base)


def _new_package(release):
    # Read only literal names; no provider import or proof authority is needed.
    tree=ast.parse((ROOT/"peano-lab/py/peano_lab/library/campaign_research_v34_closure.py").read_text())
    families=next(n.value for n in tree.body if isinstance(n, ast.Assign)
        and any(isinstance(t, ast.Name) and t.id=="RESEARCH_FAMILIES" for t in n.targets))
    rows=[]
    for call, slug, prefix, count in zip(families.elts,FAMILIES,("PG","CG"),(119,12),strict=True):
        names=ast.literal_eval(next(k.value for k in call.keywords if k.arg=="owned_names"))
        assert len(names)==count
        rows.append({"slug":slug,"theorem_count":count,"checked_use_count":count,"stable_count":0,
            "first_admitted_version":"v34","package":PACKAGES[0],
            "tags":{name:f"{prefix}{i:04X}" for i,name in enumerate(names,1)}})
    directory=release.static/PACKAGES[0]
    manifest={"schema":"peano-lab-alpha-v34-canonical-publication-v1-manifest",
        "phase":"gcd-congruence","publication_scope":"alpha_checked_use_publication",
        "alpha_edition_version":"v34","alpha_first_enrolled_version":"v34",
        "alpha_edition_checked_use_count":4223,"stable_edition_count":432,
        "theorem_count":131,"checked_use_count":131,"stable_count":0,
        "catalog_sha256":release.digest,"edition_identity_sha256":release.identity,
        "current_G009_multiplicative_closure_proved":True,"current_G091_prime_power_fields_proved":False,
        "families":rows,"files":{},"notice":"NAVIGATION ONLY, NOT PROOF AUTHORITY"}
    path=directory/"manifest.json"
    _write(path,_json(manifest))
    return directory,path,manifest


def test_source_policy_exact_newest_order_and_original_proof_limits():
    assert tuple(service.CONSTRUCTIVE_RESEARCH_CAMPAIGNS.items()) == tuple(
        (f"constructive-research-campaign-v{i}",f"v{i}") for i in (34,33,32))
    assert service.CONSTRUCTIVE_CATALOG_CODECS["v34"] == "peano_catalog_shards_v34"
    assert set(PACKAGES) <= set(service.CONSTRUCTIVE_MODERN_PHASES)
    assert service.CONSTRUCTIVE_MODERN_COUNTS["gcd-congruence"] == (131,131,0)
    assert [service.CONSTRUCTIVE_PUBLICATIONS[p].first_enrolled_version for p in PACKAGES] == [
        "v34","v33","v32","v31","mixed_preserved"]
    assert service.MAX_EXPLORER_CATALOG_BYTES == 64*1024*1024
    assert service.MAX_EXPLORER_MANIFEST_BYTES == 2*1024*1024
    assert service.MAX_EXPLORER_FAMILIES == 512
    assert service.DEFAULT_STRAND_NODES == 1024
    source=inspect.getsource(service.LeanStrandServer._current_constructive_release)
    assert "catalog_input_fingerprint" in source and "verify_catalog_bindings" in source
    assert "load_catalog(" not in source and "decode_proof_bundle" not in source


def test_transport_reuses_real_three_file_authentication_and_never_decodes_false_rows(release, monkeypatch):
    def forbidden(*args,**kwargs): pytest.fail("navigation attempted mathematical acceptance")
    monkeypatch.setattr(codec,"load_catalog",forbidden)
    verified=[]
    original=codec.verify_catalog_bindings
    def observe(*args,**kwargs):
        result=original(*args,**kwargs)
        assert len(result.files)==3
        verified.append(result.fingerprint)
        return result
    monkeypatch.setattr(codec,"verify_catalog_bindings",observe)
    assert _current(release)==("v34",release.digest,release.identity)
    assert _current(release)==("v34",release.digest,release.identity)
    assert len(verified)==1
    assert json.loads((release.directory/codec.DELTA_BASENAME).read_bytes())["theorems"]==[]


@pytest.mark.parametrize("role",("manifest","parent","delta"))
def test_same_size_same_mtime_tamper_invalidates_every_warm_input(release,role):
    previous.test_each_real_catalog_document_invalidates_warm_cache_after_same_size_mtime_change(release,role)


@pytest.mark.parametrize("role",("manifest","parent","delta"))
@pytest.mark.parametrize("mutation",("absent","symlink","directory","oversized"))
def test_each_warm_input_must_remain_ordinary_and_bounded(release,role,mutation):
    previous.test_each_catalog_input_stays_regular_present_and_bounded_on_warm_cache(release,role,mutation)


@pytest.mark.parametrize("which",("campaign","channel"))
def test_control_tamper_invalidates_warm_cache(release,which):
    previous.test_same_size_same_mtime_control_change_invalidates_warm_cache(release,which)


def test_original_default_stable_is_mandatory(release):
    previous.test_modern_default_channel_remains_stable(release)


def test_authentication_to_use_race_rejects(release,monkeypatch):
    original=codec.verify_catalog_bindings
    def changing(*args,**kwargs):
        result=original(*args,**kwargs)
        # Immutable dataclass replacement is a hostile fingerprint only, not a
        # successful fabricated proof or release capability.
        from dataclasses import replace
        file=result.delta
        return replace(result,delta=replace(file,fingerprint=replace(file.fingerprint,size=file.bytes+1)))
    monkeypatch.setattr(codec,"verify_catalog_bindings",changing)
    with pytest.raises(service.ServiceError,match="sealed data"): _current(release)


@pytest.mark.parametrize("attack",("missing","broken_json","wrong_version","wrong_schema","not_directory","symlink"))
def test_present_v34_never_falls_back_to_real_valid_v33(tmp_path,old_manifest,owned_base,monkeypatch,attack):
    root=tmp_path.resolve(); monkeypatch.setattr(service,"ROOT",root)
    old32=json.loads((ROOT/"artifacts/peano-library/alpha/catalog-v32.json").read_bytes())
    older=previous._install_transport(root,"v33",old32,owned_base)
    assert _current(older)[0]=="v33"
    directory=older.static/"constructive-research-campaign-v34"
    if attack=="not_directory": directory.write_bytes(b"not directory")
    elif attack=="symlink": directory.symlink_to(older.campaign.parent,target_is_directory=True)
    else:
        directory.mkdir()
        if attack!="missing":
            raw=json.loads(older.campaign.read_bytes())
            if attack=="wrong_schema":raw["schema"]="foreign"
            _write(directory/"campaign.json",b"{" if attack=="broken_json" else _json(raw))
    with pytest.raises(ValueError):_current(older)


def test_valid_v34_precedes_both_valid_older_releases(tmp_path,old_manifest,owned_base,monkeypatch):
    root=tmp_path.resolve(); monkeypatch.setattr(service,"ROOT",root)
    old32=json.loads((ROOT/"artifacts/peano-library/alpha/catalog-v32.json").read_bytes())
    older=previous._install_transport(root,"v32",old32,owned_base)
    assert _current(older)[0]=="v32"
    previous._install_transport(root,"v33",old32,owned_base)
    assert _current(older)[0]=="v33"
    newest=_install(root,old_manifest,owned_base)
    assert _current(older)==_current(newest)==("v34",newest.digest,newest.identity)


@pytest.mark.parametrize("slug",FAMILIES)
def test_exact_new_family_names_tags_and_first_admission(release,slug):
    directory,path,manifest=_new_package(release)
    raw=path.read_bytes()
    assert release.server.reviewed_constructive_family(directory,slug)
    assert not release.server.reviewed_constructive_family(directory,"polynomial-euclidean-division")
    assert path.read_bytes()==raw and manifest["alpha_first_enrolled_version"]=="v34"


@pytest.mark.parametrize("slug",FAMILIES)
@pytest.mark.parametrize("attack",("missing","repeated","name","tag","first","count","checked_bool","package","stable","extra"))
def test_both_new_family_provenance_checks_reject_on_every_warm_request(release,slug,attack):
    directory,path,_=_new_package(release)
    assert release.server.reviewed_constructive_family(directory,slug)
    def alter(manifest):
        row=next(r for r in manifest["families"] if r["slug"]==slug)
        if attack=="missing":manifest["families"].remove(row)
        elif attack=="repeated":manifest["families"]=[row,row]
        elif attack=="extra":manifest["families"].append({**row,"slug":"foreign"})
        elif attack in {"name","tag"}:
            name=next(iter(row["tags"]))
            if attack=="name":row["tags"]["foreign_theorem"]=row["tags"].pop(name)
            else:row["tags"][name]="PX0001"
        elif attack=="first":row["first_admitted_version"]="v33"
        elif attack=="count":row["theorem_count"]-=1
        elif attack=="checked_bool":row["checked_use_count"]=True
        elif attack=="package":row["package"]="constructive-research-explorer-v34"
        elif attack=="stable":row["stable_count"]=1
    _mutate(path,alter)
    assert not release.server.reviewed_constructive_family(directory,slug)


@pytest.mark.parametrize("field,value",(
    ("phase","polynomial"),("alpha_edition_version","v33"),("alpha_first_enrolled_version","v33"),
    ("alpha_edition_checked_use_count",4092),("stable_edition_count",433),("checked_use_count",True),
    ("first_enrollment_catalog_sha256","0"*64),("current_G091_prime_power_fields_proved",True),
    ("historical_parent",{"notice":"invented first-admission ancestor"}),
))
def test_new_package_cannot_invent_a_history_or_stronger_goal(release,field,value):
    directory,path,_=_new_package(release)
    assert release.server.reviewed_constructive_family(directory,FAMILIES[0])
    _mutate(path,lambda row:row.update({field:value}))
    assert not release.server.reviewed_constructive_family(directory,FAMILIES[0])


@pytest.mark.parametrize("package",PACKAGES)
def test_actual_v34_installed_packages_require_authentic_published_files(package):
    directory=ASSET_ROOT/package; path=directory/"manifest.json"
    assert path.is_file(),"requires actual v34 publication, not a simulated acceptance"
    raw=path.read_bytes(); manifest=json.loads(raw)
    server=non_listening_review_server(ROOT)
    assert server._current_constructive_release(ASSET_ROOT,owner=os.getuid())[0]=="v34"
    assert all(server.reviewed_constructive_family(directory,row["slug"]) for row in manifest["families"])
    handler=object.__new__(service.LeanStrandHandler);handler.server=server
    if package==PACKAGES[0]:
        for row in manifest["families"]:
            tag=next(iter(row["tags"].values()))
            page=directory/row["slug"]/"explorer/tag"/(tag+".html")
            original=page.read_bytes()
            shown=handler._inject_selector(page,page.relative_to(ROOT).parts)
            assert shown is not None and b"lean-selector.js" in shown
            assert page.read_bytes()==original
    assert path.read_bytes()==raw
