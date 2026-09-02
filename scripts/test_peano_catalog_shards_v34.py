"""Adversarial transport tests with deliberately false, non-admitting rows.

The real inherited catalogue is used only as authenticated inert JSON. No test
creates an admission capability, runs a prover, or treats flags as proof.
"""
import ast
from collections import Counter
from copy import deepcopy
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import sys

if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest
import peano_catalog_capacity_v34 as capacity
import peano_catalog_shards as old
import peano_catalog_shards_v33 as parent_codec
import peano_catalog_shards_v34 as codec
from test_peano_catalog_capacity_v34 import _main


@pytest.fixture(scope="module")
def model():
    # Never install a provisional/fake release registration for these tests.
    codec.require_registration()
    parent_raw = codec.DEFAULT_PARENT.read_bytes()
    assert len(parent_raw) == codec.PARENT_BYTES
    assert sha256(parent_raw).hexdigest() == codec.PARENT_SHA256
    parent = old._decode(parent_raw, "actual v30 fixture")
    del parent_raw
    prior_raw = codec.PREVIOUS_MANIFEST.read_bytes()
    assert len(prior_raw) == codec.PREVIOUS_MANIFEST_BYTES
    assert sha256(prior_raw).hexdigest() == codec.PREVIOUS_MANIFEST_SHA256
    manifest = old._decode(prior_raw, "actual v33 fixture")
    delta_raw = codec.PREVIOUS_MANIFEST.with_name("catalog-v33-delta.json").read_bytes()
    assert len(delta_raw) == manifest["delta"]["bytes"]
    assert sha256(delta_raw).hexdigest() == manifest["delta"]["sha256"]
    inherited = old._decode(delta_raw, "actual v33 delta fixture")["theorems"]
    del delta_raw
    assert len(inherited) == 870
    assert codec._content_digest(inherited) == codec.INHERITED_DELTA_SHA256
    prior = manifest["metadata"]
    additions = []
    for campaign, count in codec.EXPECTED_CAMPAIGNS.items():
        for _ in range(count):
            i = len(additions)
            additions.append({"name": f"transport_false_v34_{i:03d}", "enrollment_index": 4092+i,
                "dependencies": [additions[-1]["name"] if additions else inherited[-1]["name"]],
                "checked_use": True, "body_checked": True, "membership": "alpha_only",
                "evidence_status": "alpha_closed", "enrollment_origin": "ha",
                "frontier_campaign": campaign, "statement": "0 = 1",
                "script": ["NOT A PROOF"], "notice": "transport test, never proof evidence"})
    metadata = deepcopy(prior)
    metadata.update(schema=codec.LOGICAL_SCHEMA, theorem_count=codec.ROW_COUNT,
        checked_use_count=codec.ROW_COUNT, stable_count=432, alpha_only_count=codec.ROW_COUNT-432,
        membership_counts={"stable": 432, "alpha_only": codec.ROW_COUNT-432},
        evidence_counts={"stable_closed": 432, "alpha_closed": codec.ROW_COUNT-432},
        enrollment_origin_counts=dict(Counter(prior["enrollment_origin_counts"])+Counter(ha=codec.NEW_ROW_COUNT)),
        canonical_order=[*prior["canonical_order"], *codec.CANONICAL_ORDER_SUFFIX],
        alpha_v34_research_promotion={"notice": "NOT AN ADMISSION REPORT"},
        parent_alpha_v33={"notice": "actual parent independently authenticated by release verifier"},
        catalogue_capacity_v34=dict(codec.CAPACITY_METADATA),
        frontier_v34_campaign_counts=dict(codec.EXPECTED_CAMPAIGNS),
        frontier_v34_ordered_names_sha256=sha256("\n".join(row["name"] for row in additions).encode()).hexdigest())
    all_rows = [*parent["theorems"], *inherited, *additions]
    metadata["edge_count"], metadata["layer_count"], _counts = capacity.validate_rows(all_rows, codec.ROW_COUNT)
    for key in old._IDENTITY_FIELDS[:5]:
        metadata[key] = sha256(("false-transport-v34-"+key).encode()).hexdigest()
    return (parent, manifest["previous_v31_metadata"], manifest["previous_v32_metadata"],
            prior, metadata, [*inherited, *additions])


@pytest.fixture(scope="module")
def transport(model, tmp_path_factory):
    directory = tmp_path_factory.mktemp("v34-transport-only").resolve()
    manifest, delta = codec.encode_catalog(model[4], model[5])
    shutil.copyfile(codec.DEFAULT_PARENT, directory/codec.PARENT_BASENAME)
    (directory/"catalog-v34.json").write_bytes(manifest)
    (directory/codec.DELTA_BASENAME).write_bytes(delta)
    return directory


@pytest.fixture
def files(transport, tmp_path):
    # Data are immutable shared hardlinks except when a test explicitly copies
    # a private replacement. Never mutate an inherited on-disk fixture inode.
    for name in (codec.PARENT_BASENAME, codec.DELTA_BASENAME):
        os.link(transport/name, tmp_path/name)
    shutil.copyfile(transport/"catalog-v34.json", tmp_path/"catalog-v34.json")
    return tmp_path


def rewrite(directory, mutate):
    path = directory/"catalog-v34.json"
    value = json.loads(path.read_bytes())
    mutate(value)
    path.write_bytes(old._json_bytes(value))


def verify(directory, method=codec.verify_catalog_bindings):
    path = directory/"catalog-v34.json"
    return method(path, expected_sha256=sha256(path.read_bytes()).hexdigest())


def changed_combine(model, *, metadata=None, rows=None):
    return codec._combine(*model[:4], model[4] if metadata is None else metadata,
                          model[5] if rows is None else rows)


def test_no_historical_global_mutation_or_proof_imports():
    assert capacity.MAX_ROWS == codec.MAX_ROWS == 8192 and old.MAX_ROWS == parent_codec.MAX_ROWS == 4096
    for name in ("MAX_CATALOG_BYTES", "MAX_REFERENCED_DOCUMENTS", "MAX_DEPENDENCIES_PER_ROW",
                 "MAX_EDGES", "MAX_JSON_CONTAINERS", "MAX_JSON_DEPTH", "MAX_JSON_VALUES"):
        assert getattr(codec, name) == getattr(old, name)
    tree = ast.parse(Path(codec.__file__).read_text())
    imports = [n.module or "" for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
    imports += [a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names]
    assert not any(name.startswith(("peano_lab", "subprocess", "importlib")) for name in imports)
    assert not any(isinstance(n, ast.Attribute) and isinstance(n.ctx, (ast.Store, ast.Del))
                   for n in ast.walk(tree))
    combine = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_combine")
    calls = [ast.unparse(n.func) for n in ast.walk(combine) if isinstance(n, ast.Call)]
    assert calls.count("parent_codec._combine") == 1
    assert calls.count("capacity.validate_rows") == 1
    assert not any(name.startswith("peano_lab") for name in sys.modules)


def test_final_source_inventory_is_exact_119_plus_12():
    codec.require_registration()
    assert (codec.PARENT_ROW_COUNT, codec.INHERITED_DELTA_COUNT, codec.PREVIOUS_ROW_COUNT,
            codec.NEW_ROW_COUNT, codec.DELTA_ROW_COUNT, codec.ROW_COUNT, codec.STABLE_COUNT
            ) == (3222, 870, 4092, 131, 1001, 4223, 432)
    assert tuple(codec.EXPECTED_CAMPAIGNS.items()) == (
        ("polynomial-gcd-bezout", 119), ("congruence-arithmetic", 12))
    assert codec.CANONICAL_ORDER_SUFFIX == ("Constructive Alpha-v34 polynomial-gcd-bezout (119)",
                                           "Constructive Alpha-v34 congruence-arithmetic (12)")
    assert codec.CAPACITY_METADATA == {"schema": "peano-library-logical-capacity-v34",
        "previous_max_rows": 4096, "max_rows": 8192, "proof_limits_changed": False}


@pytest.mark.parametrize("payload", [b'{"x":1,"x":2}', b'{"x":NaN}', b'{"x":Infinity}',
    b'{"x":1e9999}', b'{"x":[}', b'{"x":',
    b'{"x":'+b'['*256+b'0'+b']'*256+b'}',
    b'{"x":['+b','.join([b'[]']*65535)+b']}'],
    ids=["duplicate-key", "nan", "infinity", "overflow-float", "mismatched", "unclosed",
         "depth257", "containers65537"])
def test_original_json_syntax_depth_and_container_guards_remain_active(payload):
    with pytest.raises(codec.CatalogError): old._decode(payload, "hostile v34 transport")


def test_unregistered_exact_inventory_rejects_without_any_io(monkeypatch):
    monkeypatch.setattr(codec, "NEW_ROW_COUNT", None)
    def forbidden(*args, **kwargs): pytest.fail("unregistered encoding reached I/O")
    monkeypatch.setattr(old, "_read_file", forbidden)
    with pytest.raises(codec.CatalogError, match="not registered"):
        codec.encode_catalog({}, [])


@pytest.mark.parametrize("key,value", [("NEW_ROW_COUNT", True), ("NEW_ROW_COUNT", 118),
    ("ROW_COUNT", 8193), ("DELTA_ROW_COUNT", True), ("EXPECTED_CAMPAIGNS", {}),
    ("EXPECTED_CAMPAIGNS", {"polynomial-gcd-bezout": True})])
def test_registration_types_partition_and_capacity_are_enforced(monkeypatch, key, value):
    monkeypatch.setattr(codec, key, value)
    with pytest.raises(codec.CatalogError): codec.require_registration()


def test_actual_old_prefix_survives_and_false_new_rows_do_not_become_proofs(model, transport):
    result = verify(transport, codec.load_catalog)
    assert len(result["theorems"]) == codec.ROW_COUNT > 4096
    assert result["theorems"][:3222] == model[0]["theorems"]
    assert result["theorems"][3222:4092] == model[5][:870]
    assert result["evidence_documents"] == model[3]["evidence_documents"]
    assert all(row["statement"] == "0 = 1" and row["script"] == ["NOT A PROOF"]
               for row in result["theorems"][4092:])
    assert not hasattr(result, "require_unchanged")  # plain data, no live authority
    bindings = verify(transport)
    assert len(bindings.files) == 3
    assert bindings.fingerprint == verify(transport, codec.catalog_input_fingerprint)


@pytest.mark.parametrize("key", ["schema", "metadata", "parent", "delta", "previous_v31_metadata",
                                "previous_v32_metadata", "previous_v33_metadata"])
def test_missing_manifest_fields_reject(files, key):
    rewrite(files, lambda value: value.pop(key))
    with pytest.raises(codec.CatalogError): verify(files)


@pytest.mark.parametrize("key", ["references", "parent2", "theorems", "receipt", "checked"])
def test_recursive_or_authority_manifest_fields_reject(files, key):
    rewrite(files, lambda value: value.update({key: True}))
    with pytest.raises(codec.CatalogError): verify(files)


@pytest.mark.parametrize("role", ["parent", "delta"])
@pytest.mark.parametrize("path", ["../catalog-v30.json", "/tmp/catalog.json", "https://example.test/x",
    "./catalog-v34-delta.json", "catalog-v33.json", "catalog-v34.json", "x\\y"])
def test_only_two_literal_same_directory_data_paths(files, role, path):
    rewrite(files, lambda value: value[role].update(path=path))
    with pytest.raises(codec.CatalogError): verify(files)


@pytest.mark.parametrize("role", ["parent", "delta"])
@pytest.mark.parametrize("key,value", [("bytes", True), ("bytes", 0), ("bytes", 67108865),
    ("row_count", True), ("row_count", 8193), ("sha256", "A"*64), ("schema", "wrong")])
def test_exact_binding_types_and_original_file_budget(files, role, key, value):
    rewrite(files, lambda item: item[role].update({key: value}))
    with pytest.raises(codec.CatalogError): verify(files)


@pytest.mark.parametrize("key,value", [("theorem_count", True), ("checked_use_count", 4096),
    ("stable_count", 433), ("alpha_only_count", 8193), ("edge_count", 65537),
    ("layer_count", 0), ("layer_count", 8193), ("membership_counts", {"ha": 8193}),
    ("frontier_v34_ordered_names_sha256", "A"*64), ("parent_alpha_v33", {}),
    ("alpha_v34_research_promotion", False), ("frontier_v34_campaign_counts", {"foreign": 131})])
def test_current_metadata_types_counts_and_policies(files, key, value):
    rewrite(files, lambda item: item["metadata"].update({key: value}))
    with pytest.raises(codec.CatalogError): verify(files)


@pytest.mark.parametrize("key,value", [("schema", "other"), ("max_rows", 4096), ("max_rows", 8192.0),
    ("previous_max_rows", True), ("proof_limits_changed", 0), ("proof_limits_changed", True)])
def test_capacity_upgrade_is_exact_typed_metadata(files, key, value):
    rewrite(files, lambda item: item["metadata"]["catalogue_capacity_v34"].update({key: value}))
    with pytest.raises(codec.CatalogError): verify(files)


@pytest.mark.parametrize("version", [31, 32, 33])
@pytest.mark.parametrize("key", ["schema", "evidence_documents", "canonical_order"])
def test_inline_ancestor_metadata_remains_exact_pinned_bytes(files, version, key):
    rewrite(files, lambda item: item[f"previous_v{version}_metadata"].update({key: False}))
    with pytest.raises(codec.CatalogError, match=f"immutable v{version} metadata"):
        verify(files)


@pytest.mark.parametrize("index", [0, 573, 574, 748, 749, 869])
@pytest.mark.parametrize("key,value", [("statement", "0 = 1"), ("dependencies", ["foreign"]),
    ("first_admission", {"revision": "forged-v34"})])
def test_all_870_prior_records_including_first_admission_remain_byte_exact(model, index, key, value):
    changed = list(model[5])
    changed[index] = {**changed[index], key: value}
    assert old._json_bytes(changed[index]) != old._json_bytes(model[5][index])
    with pytest.raises(codec.CatalogError, match="870 immutable"):
        changed_combine(model, rows=changed)


@pytest.mark.parametrize("key,value", [("checked_use", 1), ("body_checked", False),
    ("dependencies", ["missing"]), ("enrollment_index", 4091), ("membership", "stable"),
    ("frontier_campaign", "polynomial-euclidean-division"), ("name", "duplicate")])
def test_new_row_topology_membership_and_campaigns_still_require_original_semantics(model, key, value):
    changed = list(model[5])
    if key == "name": value = changed[869]["name"]
    changed[870] = {**changed[870], key: value}
    with pytest.raises(codec.CatalogError): changed_combine(model, rows=changed)


@pytest.mark.parametrize("mutation", ["missing_document", "changed_document", "order", "suffix", "unknown",
                                     "old_promotion", "wrong_names", "wrong_edges", "campaign_order"])
def test_old_evidence_and_full_logical_metadata_are_preserved(model, mutation):
    changed = deepcopy(model[4])
    if mutation == "missing_document": changed["evidence_documents"].pop()
    elif mutation == "changed_document": changed["evidence_documents"][0]["sha256"] = "0"*64
    elif mutation == "order": changed["canonical_order"][0] = "rewritten history"
    elif mutation == "suffix": changed["canonical_order"][-2:] = reversed(changed["canonical_order"][-2:])
    elif mutation == "unknown": changed["unreviewed"] = True
    elif mutation == "old_promotion": changed["alpha_v33_research_promotion"] = {"forged": True}
    elif mutation == "wrong_names": changed["frontier_v34_ordered_names_sha256"] = "0"*64
    elif mutation == "wrong_edges": changed["edge_count"] += 1
    else:
        rows = list(model[5])
        rows[870] = {**rows[870], "frontier_campaign": "congruence-arithmetic"}
        with pytest.raises(codec.CatalogError): changed_combine(model, rows=rows)
        return
    with pytest.raises(codec.CatalogError): changed_combine(model, metadata=changed)


@pytest.mark.parametrize("name", ["catalog-v34.json", "catalog-v30.json", "catalog-v34-delta.json"])
def test_every_symlink_is_rejected(files, name):
    target = files/name
    original = files/(name+".original")
    target.replace(original)
    target.symlink_to(original.name)
    with pytest.raises(codec.CatalogError): verify(files)


def test_wrong_owner_and_manifest_digest_reject(files):
    path = files/"catalog-v34.json"
    with pytest.raises(codec.CatalogError):
        codec.verify_catalog_bindings(path, expected_sha256="0"*64)
    with pytest.raises(codec.CatalogError):
        codec.verify_catalog_bindings(path, expected_sha256=sha256(path.read_bytes()).hexdigest(),
                                       owner_uid=os.getuid()+1)


def test_wrong_parent_literal_and_wrong_delta_actual_digest_reject(files):
    rewrite(files, lambda item: item["parent"].update(sha256="0"*64))
    with pytest.raises(codec.CatalogError): verify(files)
    rewrite(files, lambda item: item["parent"].update(sha256=codec.PARENT_SHA256))
    rewrite(files, lambda item: item["delta"].update(sha256="0"*64))
    with pytest.raises(codec.CatalogError): verify(files)


def test_warm_fingerprint_covers_replaced_delta_and_hash_check_rejects(files):
    before = verify(files, codec.catalog_input_fingerprint)
    path = files/codec.DELTA_BASENAME
    replacement = files/"private-delta"
    raw = path.read_bytes()
    replacement.write_bytes(raw[:-1]+b" ")  # same length, another inode, wrong digest
    replacement.replace(path)
    after = verify(files, codec.catalog_input_fingerprint)
    assert before != after
    with pytest.raises(codec.CatalogError): verify(files)


def test_toctou_after_authenticated_read_rejects(files, monkeypatch):
    read = old._read_file
    touched = []
    def race(path, **kwargs):
        result = read(path, **kwargs)
        if Path(path).name == codec.DELTA_BASENAME and not touched:
            touched.append(True)
            replacement = files/"private-delta"
            shutil.copyfile(path, replacement)
            replacement.replace(path)
        return result
    monkeypatch.setattr(old, "_read_file", race)
    with pytest.raises(codec.CatalogError, match="changed"):
        verify(files)
    assert touched == [True]


def test_inode_alias_rejects_before_row_decoding(files, monkeypatch):
    # Rejection-only stat attack: the real manifest is authenticated, but the
    # two data stats are made aliases. No successful transport is fabricated.
    stat = old._stat_file
    first = []
    def alias(path, owner, expected_bytes=None):
        value = stat(path, owner, expected_bytes)
        if Path(path).name == codec.PARENT_BASENAME: first.append(value)
        if Path(path).name == codec.DELTA_BASENAME:
            from dataclasses import replace
            value = replace(value, device=first[0].device, inode=first[0].inode)
        return value
    monkeypatch.setattr(old, "_stat_file", alias)
    with pytest.raises(codec.CatalogError, match="distinct ordinary"):
        verify(files)


def test_new_bad_manifest_never_loads_old_v33_fallback(files, monkeypatch):
    # The new loader has no fallback path, including after a warm caller cache.
    verify(files, codec.catalog_input_fingerprint)
    rewrite(files, lambda item: item.update(schema="invalid-newest"))
    def forbidden(*args, **kwargs): pytest.fail("newest-present failure fell back to v33")
    monkeypatch.setattr(parent_codec, "load_catalog", forbidden)
    with pytest.raises(codec.CatalogError): verify(files, codec.load_catalog)


if __name__ == "__main__":
    raise SystemExit(_main(__file__))
