"""Transport-only adversarial tests; deliberately false rows are NOT proofs."""

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import ast
import json
import os
from pathlib import Path
import shutil

import pytest

import peano_catalog_shards as old
import peano_catalog_shards_v32 as codec


def encoded(value):
    return old._json_bytes(value)


@pytest.fixture(scope="module")
def model():
    parent = old._decode(codec.DEFAULT_PARENT.read_bytes(), "real v30 fixture parent")
    previous_manifest = old._decode(codec.PREVIOUS_MANIFEST.read_bytes(), "real v31 fixture manifest")
    prior = previous_manifest["metadata"]
    delta = old._decode(codec.PREVIOUS_MANIFEST.with_name("catalog-v31-delta.json").read_bytes(), "real v31 delta")
    inherited = delta["theorems"]
    assert codec._content_digest(inherited) == codec.INHERITED_DELTA_SHA256
    additions = []
    for i in range(175):
        additions.append({"name": f"transport_only_v32_fixture_{i:03d}", "enrollment_index": 3796+i,
            "dependencies": [additions[-1]["name"] if additions else inherited[-1]["name"]],
            "checked_use": True, "body_checked": True, "membership": "alpha_only",
            "evidence_status": "alpha_closed", "enrollment_origin": "ha",
            "frontier_campaign": "multiplicative-convolution" if i < 90 else "polynomial-division-prerequisites",
            "statement": "0 = 1", "script": ["THIS IS NOT A PROOF"],
            "fixture_notice": "Transport-only false statement, never admission evidence."})
    metadata = deepcopy(prior)
    metadata.update(schema=codec.LOGICAL_SCHEMA, theorem_count=3971, checked_use_count=3971,
        stable_count=432, alpha_only_count=3539,
        membership_counts={"stable": 432, "alpha_only": 3539},
        evidence_counts={"stable_closed": 432, "alpha_closed": 3539},
        enrollment_origin_counts=dict(Counter(prior["enrollment_origin_counts"])+Counter(ha=175)),
        canonical_order=[*prior["canonical_order"], "Transport-only G009 fixture", "Transport-only polynomial fixture"],
        alpha_v32_research_promotion={"fixture_notice": "NOT PROOF EVIDENCE"},
        parent_alpha_v31={"fixture_notice": "Independent admission must authenticate the actual parent"},
        frontier_v32_campaign_counts=dict(codec.EXPECTED_CAMPAIGNS),
        frontier_v32_ordered_names_sha256=sha256("\n".join(row["name"] for row in additions).encode()).hexdigest())
    rows = [*parent["theorems"], *inherited, *additions]
    metadata["edge_count"], metadata["layer_count"], _counts = old._rows(rows,3971)
    for key in old._IDENTITY_FIELDS[:5]:
        metadata[key] = sha256(("transport-only-v32-"+key).encode()).hexdigest()
    return parent, prior, metadata, [*inherited,*additions]


@pytest.fixture(scope="module")
def transport(model, tmp_path_factory):
    directory = tmp_path_factory.mktemp("v32-transport-only").resolve()
    manifest, delta = codec.encode_catalog(model[2],model[3])
    shutil.copyfile(codec.DEFAULT_PARENT, directory/codec.PARENT_BASENAME)
    (directory/"catalog-v32.json").write_bytes(manifest)
    (directory/codec.DELTA_BASENAME).write_bytes(delta)
    return directory


@pytest.fixture
def files(transport, tmp_path):
    os.link(transport/codec.PARENT_BASENAME,tmp_path/codec.PARENT_BASENAME)
    os.link(transport/codec.DELTA_BASENAME,tmp_path/codec.DELTA_BASENAME)
    shutil.copyfile(transport/"catalog-v32.json",tmp_path/"catalog-v32.json")
    return tmp_path


def load(directory):
    path = directory/"catalog-v32.json"
    return codec.load_catalog(path,expected_sha256=sha256(path.read_bytes()).hexdigest())


def rewrite(directory, mutate):
    path = directory/"catalog-v32.json"
    value = json.loads(path.read_bytes())
    mutate(value)
    path.write_bytes(encoded(value))


def test_original_limits_and_three_file_nonrecursive_shape():
    for key in ("MAX_CATALOG_BYTES","MAX_ROWS","MAX_DEPENDENCIES_PER_ROW","MAX_EDGES",
                "MAX_JSON_CONTAINERS","MAX_JSON_DEPTH","MAX_JSON_VALUES","MAX_REFERENCED_DOCUMENTS"):
        assert getattr(codec,key) == getattr(old,key)
    assert (codec.PARENT_ROW_COUNT,codec.INHERITED_DELTA_COUNT,codec.NEW_ROW_COUNT,codec.DELTA_ROW_COUNT,
            codec.ROW_COUNT,codec.STABLE_COUNT) == (3222,574,175,749,3971,432)
    tree = ast.parse(Path(codec.__file__).read_text())
    imports = [node.module or "" for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
    imports += [alias.name for node in ast.walk(tree) if isinstance(node,ast.Import) for alias in node.names]
    assert not any(name.startswith(("peano_lab","subprocess","importlib")) for name in imports)


def test_literal_prefix_and_all_prior_metadata_are_retained(model,transport):
    result = load(transport)
    parent,prior,metadata,delta = model
    assert result["theorems"][:3222] == parent["theorems"]
    assert result["theorems"][3222:] == delta
    assert result["evidence_documents"] == prior["evidence_documents"]
    assert result["canonical_order"][:115] == prior["canonical_order"]
    assert len(result["theorems"]) == 3971
    assert all(row["statement"] == "0 = 1" for row in result["theorems"][3796:])
    assert all(row["script"] == ["THIS IS NOT A PROOF"] for row in result["theorems"][3796:])
    path = transport/"catalog-v32.json"
    bindings = codec.verify_catalog_bindings(path,expected_sha256=sha256(path.read_bytes()).hexdigest())
    assert len(bindings.files) == 3
    assert bindings.fingerprint == codec.catalog_input_fingerprint(path,expected_sha256=sha256(path.read_bytes()).hexdigest())


@pytest.mark.parametrize("key",["schema","metadata","parent","delta","previous_v31_metadata"])
def test_required_manifest_fields(files,key):
    rewrite(files,lambda value:value.pop(key))
    with pytest.raises(codec.CatalogError): load(files)


@pytest.mark.parametrize("extra",["parent2","next","references","theorems","receipt","checked"])
def test_no_recursive_or_authority_manifest_fields(files,extra):
    rewrite(files,lambda value:value.update({extra:True}))
    with pytest.raises(codec.CatalogError): load(files)


@pytest.mark.parametrize("role",["parent","delta"])
@pytest.mark.parametrize("path",["../catalog-v30.json","/tmp/catalog.json","https://example.test/x","./catalog-v32-delta.json","catalog-v31.json","catalog-v32.json","x\\y","catalog-*.json"])
def test_only_exact_nonrecursive_basenames(files,role,path):
    rewrite(files,lambda value:value[role].update(path=path))
    with pytest.raises(codec.CatalogError): load(files)


@pytest.mark.parametrize("role",["parent","delta"])
@pytest.mark.parametrize("key,value",[("bytes",True),("bytes",0),("bytes",-1),("bytes",67_108_865),
    ("row_count",True),("row_count",0),("row_count",3971),("sha256","A"*64),("schema","peano-library-alpha-shards-v32")])
def test_binding_exact_types_and_original_limits(files,role,key,value):
    rewrite(files,lambda item:item[role].update({key:value}))
    with pytest.raises(codec.CatalogError): load(files)


@pytest.mark.parametrize("key",["theorem_count","checked_use_count","stable_count","alpha_only_count","edge_count","layer_count"])
@pytest.mark.parametrize("value",[True,-1,4097])
def test_metadata_exact_integer_counts(files,key,value):
    rewrite(files,lambda item:item["metadata"].update({key:value}))
    with pytest.raises(codec.CatalogError): load(files)


@pytest.mark.parametrize("key",["schema","evidence_documents","canonical_order","frontier_v31_campaign_counts","alpha_v31_completed_lower_promotion"])
def test_literal_inline_v31_metadata_cannot_be_reinterpreted(files,key):
    rewrite(files,lambda item:item["previous_v31_metadata"].update({key:False}))
    with pytest.raises(codec.CatalogError,match="immutable v31 metadata"): load(files)


@pytest.mark.parametrize("index",[0,573])
@pytest.mark.parametrize("key,value",[("statement","0 = 1"),("checked_use",1),("enrollment_index",True),
                                     ("dependencies",[]),("script",["NOT A PROOF"]),("summary","changed")])
def test_every_inherited_row_field_is_literal_bound(model,index,key,value):
    parent,prior,metadata,rows=model
    changed=list(rows)
    changed[index]={**changed[index],key:value}
    with pytest.raises(codec.CatalogError,match="574 immutable"):
        codec._combine(parent,prior,metadata,changed)


@pytest.mark.parametrize("index,key,value",[(574,"checked_use",1),(748,"body_checked",False),
    (574,"dependencies",["missing"]),(748,"enrollment_index",3796),(574,"membership","stable"),
    (574,"frontier_campaign","polynomial-division-prerequisites"),(748,"name","transport_only_v32_fixture_000")])
def test_new_topology_types_and_ownership_are_structural_not_proof_acceptance(model,index,key,value):
    parent,prior,metadata,rows=model
    changed=list(rows)
    changed[index]={**changed[index],key:value}
    with pytest.raises(codec.CatalogError): codec._combine(parent,prior,metadata,changed)


def test_symlink_manifest_is_rejected(files):
    path=files/"catalog-v32.json"
    actual=files/"manifest-original.json"
    path.replace(actual)
    path.symlink_to(actual.name)
    with pytest.raises(codec.CatalogError): load(files)


def test_wrong_literal_parent_hash_is_rejected_before_read(files):
    rewrite(files,lambda value:value["parent"].update(sha256="0"*64))
    with pytest.raises(codec.CatalogError): load(files)


def test_wrong_delta_hash_is_rejected(files):
    rewrite(files,lambda value:value["delta"].update(sha256="0"*64))
    with pytest.raises(codec.CatalogError): load(files)


def test_unknown_logical_metadata_cannot_survive_combination(model):
    parent,prior,metadata,rows=model
    with pytest.raises(codec.CatalogError): codec._combine(parent,prior,{**metadata,"unreviewed":True},rows)


def test_historical_document_and_order_changes_are_rejected(model):
    parent,prior,metadata,rows=model
    changed=deepcopy(metadata)
    changed["evidence_documents"].pop()
    with pytest.raises(codec.CatalogError): codec._combine(parent,prior,changed,rows)
    changed=deepcopy(metadata)
    changed["canonical_order"][0]="rewritten history"
    with pytest.raises(codec.CatalogError): codec._combine(parent,prior,changed,rows)
