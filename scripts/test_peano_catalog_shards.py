"""Independent transport/security tests; synthetic rows are NOT proof evidence.

The shared fixture uses the real byte-pinned v30 parent and intentionally
proof-free new row records. A successful codec test therefore says nothing
about theorem validity or Alpha admission. No accepting proof checker is
mocked. The release's separate HA/Lean verifier must reject these fixture rows.
"""

from __future__ import annotations

import ast
from collections import Counter
from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from hashlib import sha256
import json
import os
from pathlib import Path
import resource
import shutil
import signal
import sys
import time

import pytest

import peano_catalog_shards as codec


def _json(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode()


def _topology(rows):
    levels = {}
    for row in rows:
        levels[row["name"]] = 1 + max((levels[dep] for dep in row["dependencies"]), default=-1)
    return sum(len(row["dependencies"]) for row in rows), max(levels.values()) + 1


@pytest.fixture(scope="module")
def model():
    # This is a real immutable parent read, not a substituted pin or factory.
    path = codec.DEFAULT_PARENT
    assert path.stat().st_size == 66_503_303
    with path.open("rb") as source:
        raw = source.read(66_503_304)
    assert len(raw) == 66_503_303
    assert sha256(raw).hexdigest() == "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"
    parent = json.loads(raw)
    del raw
    new = []
    for index in range(574):
        new.append({
            "name": f"transport_only_fixture_{index:04d}",
            "enrollment_index": 3222 + index,
            "dependencies": [new[-1]["name"] if new else parent["theorems"][-1]["name"]],
            "checked_use": True, "body_checked": True,
            "membership": "alpha_only", "evidence_status": "alpha_closed", "enrollment_origin": "ha",
            "frontier_campaign": f"transport_only_{index % 19:02d}",
            "statement": "0 = 1", "script": ["THIS IS NOT A PROOF"],
            "fixture_notice": "Transport-only deliberately false formula; no admission authority.",
        })
    metadata = {key: value for key, value in parent.items() if key != "theorems"}
    metadata.update({
        "schema": codec.LOGICAL_SCHEMA, "theorem_count": 3796, "checked_use_count": 3796,
        "stable_count": 432, "alpha_only_count": 3364,
        "membership_counts": {"stable": 432, "alpha_only": 3364},
        "evidence_counts": {"stable_closed": 432, "alpha_closed": 3364},
        "enrollment_origin_counts": dict(Counter(parent["enrollment_origin_counts"]) + Counter(ha=574)),
        "canonical_order": [*parent["canonical_order"], "Transport-only deliberately unproved fixture (574)"],
        "alpha_v31_completed_lower_promotion": {"fixture_notice": "NOT PROOF EVIDENCE"},
        "parent_alpha_v30": {"fixture_notice": "Literal binding is independently checked by the transport"},
        "frontier_v31_campaign_counts": dict(Counter(row["frontier_campaign"] for row in new)),
        "frontier_v31_ordered_names_sha256": sha256("\n".join(row["name"] for row in new).encode()).hexdigest(),
    })
    metadata["edge_count"], metadata["layer_count"] = _topology([*parent["theorems"], *new])
    for key in ("edition_identity_sha256", "evidence_root_sha256", "membership_root_sha256",
                "ordered_enrollment_root_sha256", "ordered_spec_root_sha256"):
        metadata[key] = sha256(("transport-only-" + key).encode()).hexdigest()
    return parent, metadata, new


@pytest.fixture(scope="module")
def transport_directory(model, tmp_path_factory):
    directory = tmp_path_factory.mktemp("catalog-shards-transport-only").resolve()
    before = codec.DEFAULT_PARENT.stat()
    manifest, delta = codec.encode_catalog(model[1], model[2])
    # Copy once. Per-test hard links point to this OWNED disposable copy, never
    # to the real repository parent, and parent mutation tests replace entries.
    shutil.copyfile(codec.DEFAULT_PARENT, directory / codec.PARENT_BASENAME)
    (directory / "catalog-v31.json").write_bytes(manifest)
    (directory / codec.DELTA_BASENAME).write_bytes(delta)
    after = codec.DEFAULT_PARENT.stat()
    assert (before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) == (
        after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)
    return directory


@pytest.fixture
def files(transport_directory, tmp_path):
    directory = tmp_path.resolve()
    os.link(transport_directory / codec.PARENT_BASENAME, directory / codec.PARENT_BASENAME)
    for name in ("catalog-v31.json", codec.DELTA_BASENAME):
        shutil.copyfile(transport_directory / name, directory / name)
    return directory


def _manifest_path(directory):
    return directory / "catalog-v31.json"


def _expected(directory):
    return sha256(_manifest_path(directory).read_bytes()).hexdigest()


def _write_manifest(directory, transform):
    path = _manifest_path(directory)
    value = json.loads(path.read_bytes())
    transform(value)
    path.write_bytes(_json(value))


def _write_delta(directory, transform):
    path = directory / codec.DELTA_BASENAME
    value = json.loads(path.read_bytes())
    transform(value)
    raw = _json(value)
    path.write_bytes(raw)
    _write_manifest(directory, lambda manifest: manifest["delta"].update(
        bytes=len(raw), sha256=sha256(raw).hexdigest()))


def _copy_row(rows, index=0):
    result = list(rows)
    result[index] = deepcopy(rows[index])
    return result


def test_fixed_v31_contract_and_all_old_budget_constants_are_exact():
    assert (codec.PARENT_ROW_COUNT, codec.DELTA_ROW_COUNT, codec.ROW_COUNT, codec.STABLE_COUNT) == (3222, 574, 3796, 432)
    assert codec.MAX_REFERENCED_DOCUMENTS == 2
    assert codec.MAX_CATALOG_BYTES == 67_108_864
    assert (codec.MAX_ROWS, codec.MAX_DEPENDENCIES_PER_ROW, codec.MAX_EDGES) == (4096, 256, 65536)
    assert (codec.TRANSPORT_SCHEMA, codec.LOGICAL_SCHEMA, codec.DELTA_SCHEMA) == (
        "peano-library-alpha-shards-v31", "peano-library-alpha-snapshot-v31", "peano-library-alpha-delta-v31")
    source = codec.DEFAULT_PARENT.parents[3] / "peano-lab/py/peano_lab/library/proof_bundle.py"
    tree = ast.parse(source.read_text())
    limits = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "BundleLimits")
    defaults = {node.target.id: ast.literal_eval(node.value) for node in limits.body if isinstance(node, ast.AnnAssign)}
    assert (defaults["max_nodes"], defaults["max_dependencies_per_node"], defaults["max_edges"]) == (
        codec.MAX_ROWS, codec.MAX_DEPENDENCIES_PER_ROW, codec.MAX_EDGES)
    assert codec.MAX_JSON_CONTAINERS == defaults["max_edges"]
    assert codec.MAX_JSON_DEPTH == defaults["max_body_depth"] == 256
    assert codec.MAX_JSON_VALUES == defaults["max_total_body_nodes"] == 5_000_000


def test_transport_import_has_no_proof_library_or_checker_or_process_authority():
    tree = ast.parse(Path(codec.__file__).read_text())
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(item.name for item in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not any(name.startswith(("peano_lab", "subprocess", "importlib")) for name in imports)
    assert "lru_cache" not in Path(codec.__file__).read_text()
    assert "NOT a proof-checking receipt" in codec.CatalogBindings.__doc__


def test_public_encode_load_preserves_all_3222_parent_records_and_documents(model, transport_directory):
    parent, metadata, new = model
    result = codec.load_catalog(_manifest_path(transport_directory), expected_sha256=_expected(transport_directory))
    assert type(result) is dict and result["schema"] == codec.LOGICAL_SCHEMA
    assert len(result["theorems"]) == 3796
    assert result["theorems"][:3222] == parent["theorems"]
    assert result["theorems"][3222:] == new
    assert result["evidence_documents"] == parent["evidence_documents"]
    assert all(type(row["checked_use"]) is bool and type(row["enrollment_index"]) is int for row in result["theorems"])
    assert {key: value for key, value in result.items() if key != "theorems"} == metadata
    # The codec does not turn an authenticated claim into a proved theorem.
    assert result["theorems"][-1]["statement"] == "0 = 1"
    assert result["theorems"][-1]["script"] == ["THIS IS NOT A PROOF"]
    assert "proof_verified" not in result and "admitted_by_loader" not in result


def test_encoder_is_deterministic_canonical_and_does_not_reencode_parent(model, transport_directory):
    manifest = _manifest_path(transport_directory).read_bytes()
    delta = (transport_directory / codec.DELTA_BASENAME).read_bytes()
    parsed_manifest, parsed_delta = json.loads(manifest), json.loads(delta)
    assert manifest == _json(parsed_manifest) and delta == _json(parsed_delta)
    assert parsed_manifest["parent"] == {
        "path": "catalog-v30.json", "bytes": 66_503_303,
        "sha256": "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7",
        "schema": "peano-library-alpha-snapshot-v30", "row_count": 3222,
    }
    assert parsed_delta == {"schema": codec.DELTA_SCHEMA, "row_count": 574, "theorems": model[2]}
    assert "theorems" not in parsed_manifest["metadata"]
    assert parsed_manifest["delta"]["bytes"] == len(delta)
    assert parsed_manifest["delta"]["sha256"] == sha256(delta).hexdigest()


def test_hash_only_authentication_does_not_parse_or_retain_parent_or_delta(transport_directory, monkeypatch):
    decoded, captured = [], []
    original_decode, original_read = codec._decode, codec._read_file
    def decode(raw, label):
        decoded.append(label)
        assert label == "v31 manifest"
        return original_decode(raw, label)
    def read(path, **kwargs):
        captured.append((path.name, kwargs.get("capture", True)))
        return original_read(path, **kwargs)
    monkeypatch.setattr(codec, "_decode", decode)
    monkeypatch.setattr(codec, "_read_file", read)
    result = codec.verify_catalog_bindings(_manifest_path(transport_directory), expected_sha256=_expected(transport_directory))
    assert decoded == ["v31 manifest"]
    assert captured == [("catalog-v31.json", True), ("catalog-v30.json", False), ("catalog-v31-delta.json", False)]
    assert tuple(item.role for item in result.files) == ("manifest", "parent", "delta")
    assert result.fingerprint == tuple(item.fingerprint for item in result.files)
    with pytest.raises(FrozenInstanceError):
        result.delta.bytes = 0


def test_cache_fingerprint_covers_all_files_without_authorizing_their_content(files, monkeypatch):
    path, digest = _manifest_path(files), _expected(files)
    before = codec.catalog_input_fingerprint(path, expected_sha256=digest)
    assert tuple(Path(item.path).name for item in before) == ("catalog-v31.json", "catalog-v30.json", "catalog-v31-delta.json")
    delta = files / codec.DELTA_BASENAME
    original = delta.stat()
    raw = delta.read_bytes()
    replacement = files / "replacement.json"
    replacement.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
    os.utime(replacement, ns=(original.st_atime_ns, original.st_mtime_ns))
    replacement.replace(delta)
    after = codec.catalog_input_fingerprint(path, expected_sha256=digest)
    assert before[:2] == after[:2] and before[2] != after[2]
    with pytest.raises(codec.CatalogError, match="SHA-256"):
        codec.verify_catalog_bindings(path, expected_sha256=digest)


@pytest.mark.parametrize("name", ("catalog-v31.json", "catalog-v30.json", "catalog-v31-delta.json"))
def test_every_file_hash_is_required_even_for_same_size_replacements(files, name):
    manifest, expected = _manifest_path(files), _expected(files)
    before = codec.catalog_input_fingerprint(manifest, expected_sha256=expected)
    path = files / name
    old = path.stat()
    replacement = files / "private-replacement.json"
    shutil.copyfile(path, replacement)
    with replacement.open("r+b") as stream:
        first = stream.read(1)
        stream.seek(0)
        stream.write(bytes([first[0] ^ 1]))
    os.utime(replacement, ns=(old.st_atime_ns, old.st_mtime_ns))
    replacement.replace(path)
    if name != "catalog-v31.json":
        after = codec.catalog_input_fingerprint(manifest, expected_sha256=expected)
        changed = [i for i, (left, right) in enumerate(zip(before, after)) if left != right]
        assert changed == [("catalog-v31.json", "catalog-v30.json", "catalog-v31-delta.json").index(name)]
    for reader in (codec.verify_catalog_bindings, codec.load_catalog):
        with pytest.raises(codec.CatalogError, match="SHA-256"):
            reader(manifest, expected_sha256=expected)


@pytest.mark.parametrize("field", ("device", "inode", "mode", "uid", "size", "mtime_ns", "ctime_ns"))
def test_cache_key_includes_all_security_relevant_stat_fields(field):
    original = codec.FileFingerprint("/owned/catalog.json", 1, 2, 3, 4, 5, 6, 7)
    assert original != replace(original, **{field: getattr(original, field) + 1})


@pytest.mark.parametrize("value", (None, 1, True, "", "a" * 63, "A" * 64, "g" * 64))
def test_manifest_digest_is_mandatory_strict_and_checked_before_file_read(tmp_path, monkeypatch, value):
    monkeypatch.setattr(codec, "_opened", lambda *_a, **_k: pytest.fail("opened before validating the expected digest"))
    with pytest.raises(codec.CatalogError, match="digest"):
        codec.load_catalog(tmp_path / "catalog-v31.json", expected_sha256=value)


@pytest.mark.parametrize("parent", (True, False))
@pytest.mark.parametrize("path", ("../catalog.json", "/catalog.json", "./catalog-v30.json", "https://host/catalog.json",
                                  "file:///catalog.json", "catalog-*.json", "catalog?.json", "dir/catalog.json",
                                  "dir\\catalog.json", "catalog.json#fragment", "catalog%2ev30.json", ""))
def test_only_the_two_literal_same_directory_basenames_are_allowed(parent, path):
    value = codec._parent_binding() if parent else {
        "path": codec.DELTA_BASENAME, "schema": codec.DELTA_SCHEMA, "bytes": 1, "sha256": "a" * 64, "row_count": 574}
    value["path"] = path
    with pytest.raises(codec.CatalogError, match="basenames"):
        codec._validate_binding(value, parent=parent)


@pytest.mark.parametrize("field,value", (
    ("bytes", True), ("bytes", 0), ("bytes", -1), ("bytes", 67_108_865), ("bytes", 66_503_302),
    ("row_count", True), ("row_count", 3221), ("row_count", 3222.0),
    ("schema", codec.TRANSPORT_SCHEMA), ("schema", "peano-library-alpha-snapshot-v29"),
    ("sha256", "0" * 64), ("sha256", "A" * 64),
))
def test_every_literal_parent_binding_component_is_fixed(field, value):
    binding = codec._parent_binding()
    binding[field] = value
    with pytest.raises(codec.CatalogError):
        codec._validate_binding(binding, parent=True)


@pytest.mark.parametrize("field,value", (("bytes", True), ("bytes", 0), ("bytes", 67_108_865),
                                       ("row_count", True), ("row_count", 574.0), ("row_count", 575),
                                       ("schema", codec.TRANSPORT_SCHEMA), ("sha256", "A" * 64)))
def test_delta_binding_types_and_budgets_are_equally_strict(field, value):
    binding = {"path": codec.DELTA_BASENAME, "schema": codec.DELTA_SCHEMA, "bytes": 1,
               "sha256": "a" * 64, "row_count": 574}
    binding[field] = value
    with pytest.raises(codec.CatalogError):
        codec._validate_binding(binding, parent=False)


@pytest.mark.parametrize("key", ("parent", "parents", "files", "url", "proof_verified"))
def test_no_recursive_parent_or_extra_binding_fields(key):
    binding = codec._parent_binding()
    binding[key] = {"path": "elsewhere.json"}
    with pytest.raises(codec.CatalogError, match="exact five"):
        codec._validate_binding(binding, parent=True)


@pytest.mark.parametrize("mutation", ("extra", "missing", "wrong_schema", "embedded_rows", "third_data_binding"))
def test_public_manifest_rejects_nonexact_envelope_before_data_files(files, monkeypatch, mutation):
    def change(value):
        if mutation == "extra": value["proof_verified"] = True
        elif mutation == "missing": value.pop("delta")
        elif mutation == "wrong_schema": value["schema"] = codec.LOGICAL_SCHEMA
        elif mutation == "embedded_rows": value["theorems"] = []
        else: value["third"] = value["delta"]
    _write_manifest(files, change)
    monkeypatch.setattr(codec, "_stat_file", lambda *_a, **_k: pytest.fail("data stat before manifest rejection"))
    # _read_file also restats its own manifest; allow only that exact call.
    original = codec._opened
    def stat_file(path, owner, size=None):
        assert path.name == "catalog-v31.json", "data file reached before malformed manifest rejection"
        with original(path, owner, size) as (_fd, fingerprint): return fingerprint
    monkeypatch.setattr(codec, "_stat_file", stat_file)
    with pytest.raises(codec.CatalogError, match="manifest"):
        codec.load_catalog(_manifest_path(files), expected_sha256=_expected(files))


@pytest.mark.parametrize("raw", (
    b'{"x":1,"x":2}', b'{"x":{"same":0,"same":false}}', b'{"x":NaN}',
    b'{"x":Infinity}', b'{"x":-Infinity}', b'{"x":1e9999}', b'[]', b'null',
    b'{"x":"\xff"}', b'\xef\xbb\xbf{}', b'{broken',
    b'{"x":' + b'[' * 2000 + b'0' + b']' * 2000 + b'}',
))
def test_strict_json_rejects_duplicate_nonfinite_invalid_and_deep_inputs(raw):
    with pytest.raises(codec.CatalogError):
        codec._decode(raw, "hostile fixture")


@pytest.mark.parametrize("limit,raw", (
    ("MAX_JSON_CONTAINERS", b'{"x":[[],[],[]]}'),
    ("MAX_JSON_DEPTH", b'{"x":[[[0]]]}'),
    ("MAX_JSON_VALUES", b'{"x":[0,1,2,3]}'),
))
def test_json_allocation_budgets_fail_before_the_object_decoder(monkeypatch, limit, raw):
    monkeypatch.setattr(codec, limit, 3)  # Narrow-only diagnostic, never relax production limits.
    monkeypatch.setattr(codec.json, "loads", lambda *_a, **_k: pytest.fail("decoded before allocation guard"))
    with pytest.raises(codec.CatalogError, match="allocation budget"):
        codec._decode(raw, "hostile allocation fixture")


def test_json_allocation_lexer_treats_escaped_formula_and_script_strings_as_data(monkeypatch):
    monkeypatch.setattr(codec, "MAX_JSON_CONTAINERS", 1)
    monkeypatch.setattr(codec, "MAX_JSON_DEPTH", 1)
    monkeypatch.setattr(codec, "MAX_JSON_VALUES", 3)
    expected = {"formula": '([{not JSON}]):, and an escaped "quote" plus \\'}
    assert codec._decode(_json(expected), "quoted data") == expected


@pytest.mark.parametrize("target", ("manifest", "delta"))
def test_public_load_rejects_duplicate_keys_even_with_a_matching_literal_hash(files, target):
    path = _manifest_path(files) if target == "manifest" else files / codec.DELTA_BASENAME
    original = path.read_bytes()
    raw = b'{"schema":"forged duplicate",' + original[1:]
    path.write_bytes(raw)
    if target == "delta":
        _write_manifest(files, lambda value: value["delta"].update(bytes=len(raw), sha256=sha256(raw).hexdigest()))
    with pytest.raises(codec.CatalogError, match="duplicate JSON object key"):
        codec.load_catalog(_manifest_path(files), expected_sha256=_expected(files))


@pytest.mark.parametrize("field,value", (
    ("theorem_count", True), ("theorem_count", 3795), ("theorem_count", 3796.0),
    ("checked_use_count", False), ("checked_use_count", 3795),
    ("stable_count", 433), ("alpha_only_count", 3363), ("edge_count", True),
    ("edge_count", 65537), ("layer_count", False), ("layer_count", 0), ("layer_count", 4097),
))
def test_exact_metadata_integer_types_and_counts(model, field, value):
    metadata = {**model[1], field: value}
    with pytest.raises(codec.CatalogError):
        codec._combine(model[0], metadata, model[2])


@pytest.mark.parametrize("field", tuple(codec._IDENTITY_FIELDS))
def test_current_identity_digests_require_exact_lowercase_hex(model, field):
    with pytest.raises(codec.CatalogError, match="SHA-256"):
        codec._combine(model[0], {**model[1], field: "A" * 64}, model[2])


@pytest.mark.parametrize("field", ("channel", "enrollment_policy", "evidence_policy", "stable_snapshot", "promotion_model",
                                  "parent_alpha_v29", "alpha_v16_qr_promotion", "alpha_v30_gaussian_factorization_promotion",
                                  "frontier_v30_campaign_counts", "frontier_v30_ordered_names_sha256"))
def test_historical_first_admission_and_policy_metadata_cannot_be_replaced(model, field):
    with pytest.raises(codec.CatalogError, match="immutable historical metadata"):
        codec._combine(model[0], {**model[1], field: {"forged": True}}, model[2])


@pytest.mark.parametrize("mutation", ("missing_old", "unknown_new", "theorems_inside", "missing_new"))
def test_full_metadata_is_required_without_unreviewed_extension_fields(model, mutation):
    metadata = dict(model[1])
    if mutation == "missing_old": metadata.pop("stable_snapshot")
    elif mutation == "unknown_new": metadata["arbitrary_parent"] = "other.json"
    elif mutation == "theorems_inside": metadata["theorems"] = []
    else: metadata.pop("parent_alpha_v30")
    with pytest.raises(codec.CatalogError):
        codec._combine(model[0], metadata, model[2])


@pytest.mark.parametrize("mutation", ("removed", "changed", "reordered", "duplicate", "not_list", "not_string"))
def test_canonical_order_is_strictly_additive(model, mutation):
    order = list(model[1]["canonical_order"])
    if mutation == "removed": order = order[:-1]
    elif mutation == "changed": order[0] = "new first admission"
    elif mutation == "reordered": order[0], order[1] = order[1], order[0]
    elif mutation == "duplicate": order[-1] = order[0]
    elif mutation == "not_list": order = tuple(order)
    else: order[-1] = True
    with pytest.raises(codec.CatalogError, match="canonical_order"):
        codec._combine(model[0], {**model[1], "canonical_order": order}, model[2])


@pytest.mark.parametrize("mutation", ("missing", "sha", "size_bool", "size", "role", "path", "duplicate", "unsorted"))
def test_every_old_evidence_document_record_is_preserved_exactly(model, mutation):
    documents = deepcopy(model[1]["evidence_documents"])
    if mutation == "missing": documents.pop(0)
    elif mutation == "sha": documents[0]["sha256"] = "0" * 64
    elif mutation == "size_bool": documents[0]["bytes"] = True
    elif mutation == "size": documents[0]["bytes"] += 1
    elif mutation == "role": documents[0]["role"] = "new authority"
    elif mutation == "path": documents[0]["path"] = "../old.json"
    elif mutation == "duplicate": documents.insert(0, deepcopy(documents[0]))
    else: documents.reverse()
    with pytest.raises(codec.CatalogError):
        codec._combine(model[0], {**model[1], "evidence_documents": documents}, model[2])


def test_nested_boolean_and_integer_aliases_cannot_launder_historical_metadata(model):
    parent = {**model[0], "transport_diagnostic": {"zero": 0, "checked": True}}
    metadata = {**model[1], "transport_diagnostic": {"zero": False, "checked": 1}}
    with pytest.raises(codec.CatalogError, match="immutable historical metadata"):
        codec._combine(parent, metadata, model[2])


def test_new_evidence_records_can_only_be_added_without_replacing_old_ones(model):
    extra = {"path": "z-transport-only/unproved.json", "bytes": 0, "sha256": sha256(b"").hexdigest(),
             "role": "Transport fixture, not a proof receipt"}
    documents = [*model[1]["evidence_documents"], extra]
    result = codec._combine(model[0], {**model[1], "evidence_documents": documents}, model[2])
    assert result["evidence_documents"][:-1] == model[0]["evidence_documents"]
    assert result["evidence_documents"][-1] == extra


@pytest.mark.parametrize("field", ("membership_counts", "evidence_counts", "enrollment_origin_counts", "frontier_v31_campaign_counts"))
@pytest.mark.parametrize("mutation", ("wrong", "boolean", "unknown"))
def test_all_count_maps_match_actual_rows_without_boolean_aliases(model, field, mutation):
    counts = dict(model[1][field])
    first = next(iter(counts))
    if mutation == "wrong": counts[first] -= 1
    elif mutation == "boolean": counts[first] = True
    else: counts["unknown_partition"] = 1
    with pytest.raises(codec.CatalogError):
        codec._combine(model[0], {**model[1], field: counts}, model[2])


@pytest.mark.parametrize("mutation", ("missing_row", "extra_row", "duplicate_old", "duplicate_new", "swapped", "index", "boolean_index",
                                     "negative_index", "self", "forward", "cycle", "unknown", "duplicate_dep", "nonstring_dep",
                                     "tuple_deps", "too_many_deps", "invalid_name", "not_row", "not_list"))
def test_rows_reject_all_topology_order_and_inventory_substitutions(model, mutation):
    parent, metadata, source = model
    rows = _copy_row(source)
    if mutation == "missing_row": rows.pop()
    elif mutation == "extra_row": rows.append(rows[-1])
    elif mutation == "duplicate_old": rows[0]["name"] = parent["theorems"][0]["name"]
    elif mutation == "duplicate_new": rows[0]["name"] = rows[1]["name"]
    elif mutation == "swapped": rows[0], rows[1] = rows[1], rows[0]
    elif mutation == "index": rows[0]["enrollment_index"] += 1
    elif mutation == "boolean_index": rows[0]["enrollment_index"] = True
    elif mutation == "negative_index": rows[0]["enrollment_index"] = -1
    elif mutation == "self": rows[0]["dependencies"] = [rows[0]["name"]]
    elif mutation == "forward": rows[0]["dependencies"] = [rows[2]["name"]]
    elif mutation == "cycle": rows[0]["dependencies"] = [rows[1]["name"]]
    elif mutation == "unknown": rows[0]["dependencies"] = ["missing_theorem"]
    elif mutation == "duplicate_dep": rows[0]["dependencies"] *= 2
    elif mutation == "nonstring_dep": rows[0]["dependencies"] = [True]
    elif mutation == "tuple_deps": rows[0]["dependencies"] = tuple(rows[0]["dependencies"])
    elif mutation == "too_many_deps": rows[0]["dependencies"] = [r["name"] for r in parent["theorems"][:257]]
    elif mutation == "invalid_name": rows[0]["name"] = "../not-a-name"
    elif mutation == "not_row": rows[0] = None
    else: rows = tuple(rows)
    with pytest.raises(codec.CatalogError):
        codec._combine(parent, metadata, rows)


def test_the_established_theorem_identifier_grammar_includes_apostrophes(model):
    rows = _copy_row(model[2])
    rows[1] = deepcopy(rows[1])
    rows[0]["name"] += "'"
    rows[1]["dependencies"] = [rows[0]["name"]]
    metadata = {**model[1], "frontier_v31_ordered_names_sha256":
                sha256("\n".join(row["name"] for row in rows).encode()).hexdigest()}
    result = codec._combine(model[0], metadata, rows)
    assert result["theorems"][3222]["name"].endswith("'")
    assert result["theorems"][3223]["dependencies"] == [rows[0]["name"]]


@pytest.mark.parametrize("field,value", (("checked_use", 1), ("checked_use", False), ("body_checked", 1),
                                       ("body_checked", False), ("membership", "stable"),
                                       ("evidence_status", "body_checked"), ("enrollment_origin", "qr"),
                                       ("frontier_campaign", None)))
def test_claimed_release_partitions_and_boolean_flags_are_exact_transport_data(model, field, value):
    rows = _copy_row(model[2])
    rows[0][field] = value
    with pytest.raises(codec.CatalogError):
        codec._combine(model[0], model[1], rows)


@pytest.mark.parametrize("field", ("edge_count", "layer_count", "frontier_v31_ordered_names_sha256"))
def test_actual_dependency_topology_and_ordered_names_determine_metadata(model, field):
    value = "0" * 64 if field.endswith("sha256") else model[1][field] + 1
    with pytest.raises(codec.CatalogError):
        codec._combine(model[0], {**model[1], field: value}, model[2])


def test_existing_total_edge_budget_cannot_be_hidden_in_many_small_rows():
    rows = []
    for i in range(4096):
        rows.append({"name": f"fixture_{i}", "enrollment_index": i,
                     "dependencies": [f"fixture_{j}" for j in range(max(0, i - 256), i)],
                     "checked_use": True, "body_checked": True, "membership": "alpha_only",
                     "evidence_status": "alpha_closed", "enrollment_origin": "ha"})
    with pytest.raises(codec.CatalogError, match="edge budget"):
        codec._rows(rows, 4096)


def test_existing_row_budget_cannot_be_overridden_by_an_expected_count():
    with pytest.raises(codec.CatalogError, match="row count"):
        codec._rows([{}] * 4097, 4097)


@pytest.mark.parametrize("mutation", ("schema", "count", "bool_count", "extra", "missing", "recursive"))
def test_hashed_delta_still_requires_the_exact_nonrecursive_logical_schema(files, mutation):
    def change(delta):
        if mutation == "schema": delta["schema"] = codec.TRANSPORT_SCHEMA
        elif mutation == "count": delta["row_count"] = 575
        elif mutation == "bool_count": delta["row_count"] = True
        elif mutation == "extra": delta["proof_verified"] = True
        elif mutation == "missing": delta.pop("theorems")
        else: delta["parent"] = {"path": "other.json"}
    _write_delta(files, change)
    with pytest.raises(codec.CatalogError):
        codec.load_catalog(_manifest_path(files), expected_sha256=_expected(files))


@pytest.mark.parametrize("name", ("catalog-v31.json", "catalog-v30.json", "catalog-v31-delta.json"))
def test_symlinked_manifest_parent_or_delta_is_rejected(files, name):
    path = files / name
    target = files / ("owned-" + name)
    path.rename(target)
    path.symlink_to(target)
    with pytest.raises(codec.CatalogError, match="safely open"):
        codec.load_catalog(_manifest_path(files), expected_sha256=sha256((files / "catalog-v31.json").read_bytes()).hexdigest())


def test_symlinked_directory_component_cannot_be_resolved_away(transport_directory, tmp_path):
    link = tmp_path / "alias"
    link.symlink_to(transport_directory, target_is_directory=True)
    with pytest.raises(codec.CatalogError, match="safely open"):
        codec.load_catalog(link / "catalog-v31.json", expected_sha256=_expected(transport_directory))


@pytest.mark.parametrize("path", ("../catalog-v31.json", "https://example/catalog-v31.json", "catalog-*.json", "dir\\catalog-v31.json"))
def test_top_level_path_has_no_traversal_url_or_glob_semantics(path):
    with pytest.raises(codec.CatalogError, match="paths"):
        codec.load_catalog(path, expected_sha256="a" * 64)


def test_hard_linked_parent_and_delta_are_not_two_distinct_bound_documents(files):
    delta = files / codec.DELTA_BASENAME
    delta.unlink()
    os.link(files / codec.PARENT_BASENAME, delta)
    _write_manifest(files, lambda value: value["delta"].update(bytes=codec.PARENT_BYTES, sha256=codec.PARENT_SHA256))
    with pytest.raises(codec.CatalogError, match="hard-linked aliases"):
        codec.load_catalog(_manifest_path(files), expected_sha256=_expected(files))


@pytest.mark.parametrize("size", (0, 67_108_865))
def test_file_size_is_rejected_before_allocation_or_read(tmp_path, monkeypatch, size):
    path = tmp_path / "oversized.json"
    with path.open("wb") as output: output.truncate(size)
    monkeypatch.setattr(codec.os, "read", lambda *_a: pytest.fail("read before size guard"))
    with pytest.raises(codec.CatalogError, match="64 MiB"):
        codec._read_file(path.resolve(), owner_uid=os.getuid(), expected_sha256="a" * 64)


@pytest.mark.parametrize("name", ("catalog-v31.json", "catalog-v30.json", "catalog-v31-delta.json"))
def test_every_public_file_is_size_checked_before_any_large_data_read(files, monkeypatch, name):
    expected = _expected(files)
    oversized = files / "owned-sparse-oversize.json"
    with oversized.open("wb") as stream: stream.truncate(67_108_865)
    oversized.replace(files / name)  # Never truncate the shared disposable parent in place.
    original = codec._read_file
    def read(path, **kwargs):
        assert path.name == "catalog-v31.json", "data allocation happened before all file-size checks"
        return original(path, **kwargs)
    monkeypatch.setattr(codec, "_read_file", read)
    with pytest.raises(codec.CatalogError, match="64 MiB"):
        codec.load_catalog(_manifest_path(files), expected_sha256=expected)


def test_named_pipe_is_rejected_without_blocking_or_reading(tmp_path, monkeypatch):
    path = tmp_path / "pipe.json"
    os.mkfifo(path)
    monkeypatch.setattr(codec.os, "read", lambda *_a: pytest.fail("read from a FIFO"))
    with pytest.raises(codec.CatalogError, match="type or owner"):
        codec._read_file(path.resolve(), owner_uid=os.getuid(), expected_sha256="a" * 64)


def test_wrong_owner_is_rejected_before_reading(tmp_path, monkeypatch):
    path = tmp_path / "owned.json"
    path.write_bytes(b"{}")
    monkeypatch.setattr(codec.os, "read", lambda *_a: pytest.fail("read before owner check"))
    with pytest.raises(codec.CatalogError, match="owner"):
        codec._read_file(path.resolve(), owner_uid=os.getuid() + 1, expected_sha256=sha256(b"{}").hexdigest())


@pytest.mark.parametrize("owner", (True, False, -1, 1.0, "0"))
def test_owner_parameter_cannot_disable_or_coerce_the_ownership_guard(tmp_path, owner):
    with pytest.raises(codec.CatalogError, match="owner_uid"):
        codec.load_catalog(tmp_path / "catalog-v31.json", expected_sha256="a" * 64, owner_uid=owner)


@pytest.mark.parametrize("mutation", ("grow", "shrink", "same_size", "replace_path"))
def test_mutation_during_bounded_reads_never_returns_authenticated_data(tmp_path, monkeypatch, mutation):
    path = (tmp_path / "racing.json").resolve()
    original = b'{"a":1}'
    path.write_bytes(original)
    read = os.read
    called = False
    def racing_read(fd, length):
        nonlocal called
        if not called:
            called = True
            if mutation == "grow": path.write_bytes(original + b" ")
            elif mutation == "shrink": path.write_bytes(b"{}")
            elif mutation == "same_size": path.write_bytes(b'{"a":2}')
            else:
                other = path.with_name("replacement.json")
                other.write_bytes(original)
                other.replace(path)
        return read(fd, length)
    monkeypatch.setattr(codec.os, "read", racing_read)
    with pytest.raises(codec.CatalogError, match="changed|grew|SHA-256"):
        codec._read_file(path, owner_uid=os.getuid(), expected_bytes=len(original), expected_sha256=sha256(original).hexdigest())


def test_mutation_after_logical_validation_is_caught_before_return(files, monkeypatch):
    original = codec._combine
    def combine(*args):
        result = original(*args)
        delta = files / codec.DELTA_BASENAME
        with delta.open("ab") as stream: stream.write(b" ")
        return result
    monkeypatch.setattr(codec, "_combine", combine)
    with pytest.raises(codec.CatalogError, match="size|changed"):
        codec.load_catalog(_manifest_path(files), expected_sha256=_expected(files))


def test_hash_only_rechecks_files_after_its_last_hash(files, monkeypatch):
    original = codec._read_file
    def read(path, **kwargs):
        result = original(path, **kwargs)
        if path.name == codec.DELTA_BASENAME:
            with path.open("ab") as stream: stream.write(b" ")
        return result
    monkeypatch.setattr(codec, "_read_file", read)
    with pytest.raises(codec.CatalogError, match="size|changed"):
        codec.verify_catalog_bindings(_manifest_path(files), expected_sha256=_expected(files))


def test_encoder_enforces_bound_during_encoding_and_rejects_nonfinite_values(monkeypatch):
    monkeypatch.setattr(codec, "MAX_CATALOG_BYTES", 32)  # A narrower test-only budget, never an increased one.
    with pytest.raises(codec.CatalogError, match="64 MiB"):
        codec._json_bytes({"x": "a" * 64})
    with pytest.raises(codec.CatalogError, match="JSON"):
        codec._json_bytes({"x": float("nan")})


def main(argv=None):
    """Run this lightweight suite inside the same unchanged authoring window."""
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    result = pytest.main([str(Path(__file__).resolve()), "-q", *(sys.argv[1:] if argv is None else argv)])
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if sys.platform != "darwin": peak *= 1024
    elapsed = time.monotonic() - started
    if peak > 1536 * 1024 * 1024 or elapsed > 180:
        raise SystemExit("catalogue transport tests exceeded the unchanged authoring budget")
    print(json.dumps({"status": result, "elapsed_seconds": elapsed, "peak_rss_bytes": peak,
                      "cpu_limits": [170, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024}))
    return result


if __name__ == "__main__":
    raise SystemExit(main())
