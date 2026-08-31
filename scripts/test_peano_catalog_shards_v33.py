"""Transport-only adversarial tests; deliberately false rows are NOT proofs."""

from collections import Counter
from copy import deepcopy
from hashlib import sha256
import ast
import json
import os
from pathlib import Path
import shutil
import resource
import signal
import sys
import time

_BOUNDED_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest

import peano_catalog_shards as old
import peano_catalog_shards_v33 as codec


def encoded(value):
    return old._json_bytes(value)


@pytest.fixture(scope="module")
def model():
    parent = old._decode(codec.DEFAULT_PARENT.read_bytes(), "real v30 fixture parent")
    previous_manifest = old._decode(codec.PREVIOUS_MANIFEST.read_bytes(), "real v32 fixture manifest")
    ancestor = previous_manifest["previous_v31_metadata"]
    prior = previous_manifest["metadata"]
    delta = old._decode(codec.PREVIOUS_MANIFEST.with_name("catalog-v32-delta.json").read_bytes(), "real v32 delta")
    inherited = delta["theorems"]
    assert codec._content_digest(inherited) == codec.INHERITED_DELTA_SHA256
    additions = []
    for i in range(121):
        additions.append({"name": f"transport_only_v33_fixture_{i:03d}", "enrollment_index": 3971+i,
            "dependencies": [additions[-1]["name"] if additions else inherited[-1]["name"]],
            "checked_use": True, "body_checked": True, "membership": "alpha_only",
            "evidence_status": "alpha_closed", "enrollment_origin": "ha",
            "frontier_campaign": "polynomial-euclidean-division",
            "statement": "0 = 1", "script": ["THIS IS NOT A PROOF"],
            "fixture_notice": "Transport-only false statement, never admission evidence."})
    metadata = deepcopy(prior)
    metadata.update(schema=codec.LOGICAL_SCHEMA, theorem_count=4092, checked_use_count=4092,
        stable_count=432, alpha_only_count=3660,
        membership_counts={"stable": 432, "alpha_only": 3660},
        evidence_counts={"stable_closed": 432, "alpha_closed": 3660},
        enrollment_origin_counts=dict(Counter(prior["enrollment_origin_counts"])+Counter(ha=121)),
        canonical_order=[*prior["canonical_order"], "Transport-only polynomial execution fixture"],
        alpha_v33_research_promotion={"fixture_notice": "NOT PROOF EVIDENCE"},
        parent_alpha_v32={"fixture_notice": "Independent admission must authenticate the actual parent"},
        frontier_v33_campaign_counts=dict(codec.EXPECTED_CAMPAIGNS),
        frontier_v33_ordered_names_sha256=sha256("\n".join(row["name"] for row in additions).encode()).hexdigest())
    rows = [*parent["theorems"], *inherited, *additions]
    metadata["edge_count"], metadata["layer_count"], _counts = old._rows(rows,4092)
    for key in old._IDENTITY_FIELDS[:5]:
        metadata[key] = sha256(("transport-only-v33-"+key).encode()).hexdigest()
    return parent, ancestor, prior, metadata, [*inherited,*additions]


@pytest.fixture(scope="module")
def transport(model, tmp_path_factory):
    directory = tmp_path_factory.mktemp("v33-transport-only").resolve()
    manifest, delta = codec.encode_catalog(model[3],model[4])
    shutil.copyfile(codec.DEFAULT_PARENT, directory/codec.PARENT_BASENAME)
    (directory/"catalog-v33.json").write_bytes(manifest)
    (directory/codec.DELTA_BASENAME).write_bytes(delta)
    return directory


@pytest.fixture
def files(transport, tmp_path):
    os.link(transport/codec.PARENT_BASENAME,tmp_path/codec.PARENT_BASENAME)
    os.link(transport/codec.DELTA_BASENAME,tmp_path/codec.DELTA_BASENAME)
    shutil.copyfile(transport/"catalog-v33.json",tmp_path/"catalog-v33.json")
    return tmp_path


def load(directory):
    path = directory/"catalog-v33.json"
    return codec.load_catalog(path,expected_sha256=sha256(path.read_bytes()).hexdigest())


def rewrite(directory, mutate):
    path = directory/"catalog-v33.json"
    value = json.loads(path.read_bytes())
    mutate(value)
    path.write_bytes(encoded(value))


def test_original_limits_and_three_file_nonrecursive_shape():
    for key in ("MAX_CATALOG_BYTES","MAX_ROWS","MAX_DEPENDENCIES_PER_ROW","MAX_EDGES",
                "MAX_JSON_CONTAINERS","MAX_JSON_DEPTH","MAX_JSON_VALUES","MAX_REFERENCED_DOCUMENTS"):
        assert getattr(codec,key) == getattr(old,key)
    assert (codec.PARENT_ROW_COUNT,codec.INHERITED_DELTA_COUNT,codec.NEW_ROW_COUNT,codec.DELTA_ROW_COUNT,
            codec.ROW_COUNT,codec.STABLE_COUNT) == (3222,749,121,870,4092,432)
    tree = ast.parse(Path(codec.__file__).read_text())
    imports = [node.module or "" for node in ast.walk(tree) if isinstance(node,ast.ImportFrom)]
    imports += [alias.name for node in ast.walk(tree) if isinstance(node,ast.Import) for alias in node.names]
    assert not any(name.startswith(("peano_lab","subprocess","importlib")) for name in imports)


def test_literal_prefix_and_all_prior_metadata_are_retained(model,transport):
    result = load(transport)
    parent,ancestor,prior,metadata,delta = model
    assert result["theorems"][:3222] == parent["theorems"]
    assert result["theorems"][3222:] == delta
    assert result["evidence_documents"] == prior["evidence_documents"]
    assert result["canonical_order"][:len(prior["canonical_order"])] == prior["canonical_order"]
    assert len(result["theorems"]) == 4092
    assert all(row["statement"] == "0 = 1" for row in result["theorems"][3971:])
    assert all(row["script"] == ["THIS IS NOT A PROOF"] for row in result["theorems"][3971:])
    path = transport/"catalog-v33.json"
    bindings = codec.verify_catalog_bindings(path,expected_sha256=sha256(path.read_bytes()).hexdigest())
    assert len(bindings.files) == 3
    assert bindings.fingerprint == codec.catalog_input_fingerprint(path,expected_sha256=sha256(path.read_bytes()).hexdigest())


@pytest.mark.parametrize("key",["schema","metadata","parent","delta","previous_v31_metadata","previous_v32_metadata"])
def test_required_manifest_fields(files,key):
    rewrite(files,lambda value:value.pop(key))
    with pytest.raises(codec.CatalogError): load(files)


@pytest.mark.parametrize("extra",["parent2","next","references","theorems","receipt","checked"])
def test_no_recursive_or_authority_manifest_fields(files,extra):
    rewrite(files,lambda value:value.update({extra:True}))
    with pytest.raises(codec.CatalogError): load(files)


@pytest.mark.parametrize("role",["parent","delta"])
@pytest.mark.parametrize("path",["../catalog-v30.json","/tmp/catalog.json","https://example.test/x","./catalog-v33-delta.json","catalog-v31.json","catalog-v33.json","x\\y","catalog-*.json"])
def test_only_exact_nonrecursive_basenames(files,role,path):
    rewrite(files,lambda value:value[role].update(path=path))
    with pytest.raises(codec.CatalogError): load(files)


@pytest.mark.parametrize("role",["parent","delta"])
@pytest.mark.parametrize("key,value",[("bytes",True),("bytes",0),("bytes",-1),("bytes",67_108_865),
    ("row_count",True),("row_count",0),("row_count",4092),("sha256","A"*64),("schema","peano-library-alpha-shards-v33")])
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


@pytest.mark.parametrize("index",[0,573,574,748])
@pytest.mark.parametrize("key,value",[("statement","0 = 1"),("checked_use",1),("enrollment_index",True),
                                     ("dependencies",[]),("script",["NOT A PROOF"]),("summary","changed")])
def test_every_inherited_row_field_is_literal_bound(model,index,key,value):
    parent,ancestor,prior,metadata,rows=model
    changed=list(rows)
    if key == "dependencies" and rows[index][key] == value:
        value = ["unreviewed_dependency"]
    changed[index]={**changed[index],key:value}
    assert encoded(changed[index]) != encoded(rows[index])
    with pytest.raises(codec.CatalogError,match="749 immutable"):
        codec._combine(parent,ancestor,prior,metadata,changed)


@pytest.mark.parametrize("index,key,value",[(749,"checked_use",1),(869,"body_checked",False),
    (749,"dependencies",["missing"]),(869,"enrollment_index",3971),(749,"membership","stable"),
    (749,"frontier_campaign","polynomial-division-prerequisites"),(869,"name","transport_only_v33_fixture_000")])
def test_new_topology_types_and_ownership_are_structural_not_proof_acceptance(model,index,key,value):
    parent,ancestor,prior,metadata,rows=model
    changed=list(rows)
    changed[index]={**changed[index],key:value}
    with pytest.raises(codec.CatalogError): codec._combine(parent,ancestor,prior,metadata,changed)


@pytest.mark.parametrize("key",["schema","evidence_documents","canonical_order","frontier_v32_campaign_counts","alpha_v32_research_promotion"])
def test_literal_inline_v32_metadata_cannot_be_reinterpreted(files,key):
    rewrite(files,lambda item:item["previous_v32_metadata"].update({key:False}))
    with pytest.raises(codec.CatalogError,match="immutable v32 metadata"): load(files)


def test_symlink_manifest_is_rejected(files):
    path=files/"catalog-v33.json"
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
    parent,ancestor,prior,metadata,rows=model
    with pytest.raises(codec.CatalogError): codec._combine(parent,ancestor,prior,{**metadata,"unreviewed":True},rows)


def test_historical_document_and_order_changes_are_rejected(model):
    parent,ancestor,prior,metadata,rows=model
    changed=deepcopy(metadata)
    changed["evidence_documents"].pop()
    with pytest.raises(codec.CatalogError): codec._combine(parent,ancestor,prior,changed,rows)
    changed=deepcopy(metadata)
    changed["canonical_order"][0]="rewritten history"
    with pytest.raises(codec.CatalogError): codec._combine(parent,ancestor,prior,changed,rows)


def _main(argv=None):
    """Run only the selected actual tests in one original bounded window."""
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pytest-select", default="")
    parser.add_argument("--case-start", type=int, default=0)
    parser.add_argument("--case-count", type=int)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args(argv)
    if args.case_start < 0 or args.case_count is not None and args.case_count <= 0:
        parser.error("a case window must be positive and bounded")

    class Window:
        def __init__(self):
            self.selected = []
            self.passed = set()
            self.bad = []
        @pytest.hookimpl(trylast=True)
        def pytest_collection_modifyitems(self, session, config, items):
            chosen = items[args.case_start:None if args.case_count is None else args.case_start + args.case_count]
            if args.case_count is not None and len(chosen) != args.case_count:
                raise ValueError("the exact requested case window is unavailable")
            if not chosen:
                raise ValueError("an empty bounded case selection is not a pass")
            selected = {item.nodeid for item in chosen}
            rejected = [item for item in items if item.nodeid not in selected]
            config.hook.pytest_deselected(items=rejected)
            items[:] = chosen
            self.selected = [item.nodeid for item in chosen]
        def pytest_runtest_logreport(self, report):
            if report.when == "call" and report.passed:
                self.passed.add(report.nodeid)
            elif report.failed or report.skipped or getattr(report, "wasxfail", None):
                self.bad.append(report.nodeid)

    plugin = Window()
    options = [str(Path(__file__).resolve()), "-q", "--disable-warnings", "-k", args.pytest_select]
    if args.collect_only:
        options.append("--collect-only")
    status = pytest.main(options, plugins=[plugin])
    peak = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    if sys.platform != "darwin":
        peak *= 1024
    if not 0 < peak <= 1536 * 1024 * 1024:
        raise RuntimeError("the original observed RSS ceiling was exceeded")
    if not args.collect_only and (plugin.bad or plugin.passed != set(plugin.selected)):
        status = status or 1
    print(json.dumps({"selected": len(plugin.selected), "passed": len(plugin.passed),
                      "collect_only": args.collect_only, "pytest_exit_code": int(status),
                      "elapsed_seconds": time.monotonic() - _BOUNDED_STARTED,
                      "peak_rss_bytes": peak, "cpu": list(resource.getrlimit(resource.RLIMIT_CPU)),
                      "wall_seconds": 180}, sort_keys=True), flush=True)
    return int(status)


if __name__ == "__main__":
    raise SystemExit(_main())
