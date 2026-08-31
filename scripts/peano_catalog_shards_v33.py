"""Bounded, nonrecursive Alpha-v33 transport; never a proof authority.

Exactly three files retain the original 64-MiB per-file ceiling: the current
manifest, the literal v30 base, and one cumulative delta. Its first 749 rows
are the unchanged v31/v32 delta; only the final 121 rows are new. Literal
v31 and v32 metadata let the unchanged prior validators check the inherited
prefix without recursively loading manifests or treating receipts as proof.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path

import peano_catalog_shards as previous
import peano_catalog_shards_v32 as parent_codec


CatalogError = previous.CatalogError
CatalogBindings = previous.CatalogBindings
CatalogFileBinding = previous.CatalogFileBinding
FileFingerprint = previous.FileFingerprint
TRANSPORT_SCHEMA = "peano-library-alpha-shards-v33"
LOGICAL_SCHEMA = "peano-library-alpha-snapshot-v33"
DELTA_SCHEMA = "peano-library-alpha-delta-v33"
PARENT_SCHEMA = previous.PARENT_SCHEMA
PARENT_BASENAME = previous.PARENT_BASENAME
PARENT_BYTES = previous.PARENT_BYTES
PARENT_SHA256 = previous.PARENT_SHA256
PARENT_ROW_COUNT = previous.PARENT_ROW_COUNT
DELTA_BASENAME = "catalog-v33-delta.json"
INHERITED_DELTA_COUNT = 749
NEW_ROW_COUNT = 121
DELTA_ROW_COUNT = INHERITED_DELTA_COUNT + NEW_ROW_COUNT
ROW_COUNT = PARENT_ROW_COUNT + DELTA_ROW_COUNT
STABLE_COUNT = 432
MAX_REFERENCED_DOCUMENTS = previous.MAX_REFERENCED_DOCUMENTS
MAX_CATALOG_BYTES = previous.MAX_CATALOG_BYTES
MAX_ROWS = previous.MAX_ROWS
MAX_DEPENDENCIES_PER_ROW = previous.MAX_DEPENDENCIES_PER_ROW
MAX_EDGES = previous.MAX_EDGES
MAX_JSON_CONTAINERS = previous.MAX_JSON_CONTAINERS
MAX_JSON_DEPTH = previous.MAX_JSON_DEPTH
MAX_JSON_VALUES = previous.MAX_JSON_VALUES
DEFAULT_PARENT = previous.DEFAULT_PARENT
PREVIOUS_MANIFEST = DEFAULT_PARENT.with_name("catalog-v32.json")
PREVIOUS_MANIFEST_BYTES = 603_900
PREVIOUS_MANIFEST_SHA256 = "41b9f387d88a5a4f0fe5ee2bd5578f37a27a4657b0a80f1a1a2cb5109f69a623"
PREVIOUS_METADATA_BYTES = 310_582
PREVIOUS_METADATA_SHA256 = "d09e52aacc3fb7d281b11b5e8901f2636ffea2f43305b80f0601e7f9989bfa6d"
INHERITED_DELTA_SHA256 = "a369a35127da430d356127baa16bd80dede5102b3d2be29e405088fbc3ab7403"
EXPECTED_CAMPAIGNS = {"polynomial-euclidean-division": 121}
_NEW_FIELDS = frozenset(("alpha_v33_research_promotion", "frontier_v33_campaign_counts",
                         "frontier_v33_ordered_names_sha256", "parent_alpha_v32"))
_content_digest = parent_codec._content_digest


def _previous_metadata(value):
    if type(value) is not dict or "theorems" in value:
        raise CatalogError("the prior metadata must be a literal object without rows")
    raw = previous._json_bytes(value)
    if len(raw) != PREVIOUS_METADATA_BYTES or sha256(raw).hexdigest() != PREVIOUS_METADATA_SHA256:
        raise CatalogError("the literal immutable v32 metadata changed")
    parent_codec._metadata_header(value)
    return value


def _ancestor_metadata(value):
    return parent_codec._previous_metadata(value)


def _metadata_header(metadata):
    required = previous._CURRENT_FIELDS | previous._NEW_FIELDS | parent_codec._NEW_FIELDS | _NEW_FIELDS
    if type(metadata) is not dict or "theorems" in metadata or not required <= set(metadata):
        raise CatalogError("incomplete logical v33 metadata or unexpected inline theorem rows")
    if type(metadata["schema"]) is not str or metadata["schema"] != LOGICAL_SCHEMA:
        raise CatalogError("the logical catalogue is not Alpha v33")
    for key, wanted in (("theorem_count", ROW_COUNT), ("checked_use_count", ROW_COUNT),
                        ("stable_count", STABLE_COUNT), ("alpha_only_count", ROW_COUNT-STABLE_COUNT)):
        if previous._integer(metadata[key], key, maximum=MAX_ROWS) != wanted:
            raise CatalogError("the exact v33 metadata count changed: " + key)
    previous._integer(metadata["edge_count"], "edge_count", maximum=MAX_EDGES)
    previous._integer(metadata["layer_count"], "layer_count", minimum=1, maximum=MAX_ROWS)
    for key in (*previous._IDENTITY_FIELDS, "frontier_v33_ordered_names_sha256"):
        previous._digest(metadata[key], key)
    for key in ("membership_counts", "evidence_counts", "enrollment_origin_counts",
                "frontier_v31_campaign_counts", "frontier_v32_campaign_counts", "frontier_v33_campaign_counts"):
        previous._counts(metadata[key], key)
    if not previous._same(metadata["frontier_v33_campaign_counts"], EXPECTED_CAMPAIGNS):
        raise CatalogError("the exact one-family v33 ownership partition changed")
    for key in ("parent_alpha_v32", "alpha_v33_research_promotion"):
        if type(metadata[key]) is not dict or not metadata[key]:
            raise CatalogError("missing v33 parent or promotion metadata")
    return metadata


def _validate_binding(value, *, parent):
    if parent:
        return previous._validate_binding(value, parent=True)
    if type(value) is not dict or set(value) != previous._BINDING_FIELDS:
        raise CatalogError("the cumulative delta binding needs exactly five fields")
    if type(value["path"]) is not str or value["path"] != DELTA_BASENAME:
        raise CatalogError("only the exact same-directory v33 delta basename is allowed")
    if type(value["schema"]) is not str or value["schema"] != DELTA_SCHEMA:
        raise CatalogError("the cumulative delta schema is not the literal v33 schema")
    if previous._integer(value["row_count"], "delta row count", maximum=MAX_ROWS) != DELTA_ROW_COUNT:
        raise CatalogError("the cumulative delta must have exactly 870 rows")
    previous._integer(value["bytes"], "delta bytes", minimum=1, maximum=MAX_CATALOG_BYTES)
    previous._digest(value["sha256"], "delta digest")
    return value


def _manifest(path, expected_sha256, owner_uid):
    path, owner = previous._absolute_path(path), previous._owner(owner_uid)
    raw, fingerprint = previous._read_file(path, owner_uid=owner, expected_sha256=expected_sha256)
    value = previous._decode(raw, "v33 manifest")
    if (set(value) != {"schema", "metadata", "parent", "delta",
                       "previous_v31_metadata", "previous_v32_metadata"}
            or value["schema"] != TRANSPORT_SCHEMA):
        raise CatalogError("v33 requires exactly two data bindings and pinned inline v31/v32 metadata")
    _metadata_header(value["metadata"])
    _ancestor_metadata(value["previous_v31_metadata"])
    _previous_metadata(value["previous_v32_metadata"])
    parent = _validate_binding(value["parent"], parent=True)
    delta = _validate_binding(value["delta"], parent=False)
    files = [CatalogFileBinding("manifest", path, fingerprint.size, expected_sha256,
                                TRANSPORT_SCHEMA, ROW_COUNT, fingerprint)]
    for role, item in (("parent", parent), ("delta", delta)):
        target = path.parent / item["path"]
        info = previous._stat_file(target, owner, item["bytes"])
        files.append(CatalogFileBinding(role, target, item["bytes"], item["sha256"],
                                       item["schema"], item["row_count"], info))
    if len({(item.fingerprint.device, item.fingerprint.inode) for item in files}) != 3:
        raise CatalogError("v33 data documents must be three distinct ordinary files")
    return value, CatalogBindings(*files), owner


def catalog_input_fingerprint(path, *, expected_sha256, owner_uid=None):
    """A three-file stat key, never a hash check or mathematical authority."""
    _value, bindings, owner = _manifest(path, expected_sha256, owner_uid)
    previous._unchanged(bindings, owner)
    return bindings.fingerprint


def verify_catalog_bindings(path, *, expected_sha256, owner_uid=None):
    """Authenticate every byte; do not parse theorem data or accept a proof."""
    _value, bindings, owner = _manifest(path, expected_sha256, owner_uid)
    for item in (bindings.parent, bindings.delta):
        _raw, fingerprint = previous._read_file(item.path, owner_uid=owner,
            expected_bytes=item.bytes, expected_sha256=item.sha256, capture=False)
        if fingerprint != item.fingerprint:
            raise CatalogError("catalogue file changed after its binding was read: " + item.role)
    previous._unchanged(bindings, owner)
    return bindings


def _combine(parent, ancestor_metadata, prior_metadata, metadata, cumulative_rows):
    """Structural transport validation only; original proof gates stay separate."""
    _ancestor_metadata(ancestor_metadata)
    _previous_metadata(prior_metadata)
    _metadata_header(metadata)
    if type(cumulative_rows) is not list or len(cumulative_rows) != DELTA_ROW_COUNT:
        raise CatalogError("the cumulative delta must have exactly 749 inherited and 121 new rows")
    inherited_rows, new_rows = cumulative_rows[:INHERITED_DELTA_COUNT], cumulative_rows[INHERITED_DELTA_COUNT:]
    if _content_digest(inherited_rows) != INHERITED_DELTA_SHA256:
        raise CatalogError("one of the 749 immutable v31/v32 theorem records changed")
    # Both original structural validators execute unchanged. No recursive
    # manifest resolution, replaced globals, proof receipt or skipped row.
    prior = parent_codec._combine(parent, ancestor_metadata, prior_metadata, inherited_rows)
    inherited = set(prior_metadata)
    if set(metadata) != inherited | _NEW_FIELDS:
        raise CatalogError("logical v33 metadata dropped old fields or added unknown fields")
    for key in inherited - previous._CURRENT_FIELDS:
        if not previous._same(metadata[key], prior_metadata[key]):
            raise CatalogError("immutable historical metadata changed: " + key)
    old_order, order = prior_metadata["canonical_order"], metadata["canonical_order"]
    if (type(order) is not list or len(order) != len(old_order)+1
            or order[:len(old_order)] != old_order
            or any(type(item) is not str or not item for item in order)
            or len(set(order)) != len(order)):
        raise CatalogError("v33 must append exactly one distinct campaign-order entry")
    old_documents = previous._documents(prior_metadata["evidence_documents"], "v32")
    documents = previous._documents(metadata["evidence_documents"], "v33")
    for path, old in old_documents.items():
        if path not in documents or not previous._same(old, documents[path]):
            raise CatalogError("immutable v32 evidence record changed: " + path)
    rows = [*prior["theorems"], *new_rows]
    edges, layer_count, counts = previous._rows(rows, ROW_COUNT)
    expected = {
        "membership_counts": {"stable": STABLE_COUNT, "alpha_only": ROW_COUNT-STABLE_COUNT},
        "evidence_counts": {"stable_closed": STABLE_COUNT, "alpha_closed": ROW_COUNT-STABLE_COUNT},
        "enrollment_origin_counts": dict(Counter(prior_metadata["enrollment_origin_counts"]) + Counter(ha=NEW_ROW_COUNT)),
    }
    for key, row_key in (("membership_counts", "membership"), ("evidence_counts", "evidence_status"),
                         ("enrollment_origin_counts", "enrollment_origin")):
        if not previous._same(metadata[key], expected[key]) or counts[row_key] != expected[key]:
            raise CatalogError("v33 metadata counts differ from the actual ordered rows: " + key)
    if metadata["edge_count"] != edges or metadata["layer_count"] != layer_count:
        raise CatalogError("v33 topology metadata differs from the actual dependency DAG")
    if any(row.get("frontier_campaign") != "polynomial-euclidean-division"
           or row["membership"] != "alpha_only" or row["evidence_status"] != "alpha_closed"
           or row["enrollment_origin"] != "ha" for row in new_rows):
        raise CatalogError("the exact ordered 121-row admission partition changed")
    names = sha256("\n".join(row["name"] for row in new_rows).encode()).hexdigest()
    if metadata["frontier_v33_ordered_names_sha256"] != names:
        raise CatalogError("v33 ordered theorem-name digest differs from the actual new rows")
    return {**metadata, "theorems": rows}


def load_catalog(path, *, expected_sha256, owner_uid=None):
    manifest, bindings, owner = _manifest(path, expected_sha256, owner_uid)
    values = []
    for item in (bindings.parent, bindings.delta):
        raw, fingerprint = previous._read_file(item.path, owner_uid=owner,
            expected_bytes=item.bytes, expected_sha256=item.sha256)
        if fingerprint != item.fingerprint:
            raise CatalogError("catalogue document changed after its binding: " + item.role)
        values.append(previous._decode(raw, "v33 " + item.role))
        del raw
    parent, delta = values
    if (set(delta) != {"schema", "row_count", "theorems"} or delta["schema"] != DELTA_SCHEMA
            or previous._integer(delta.get("row_count"), "delta row count", maximum=MAX_ROWS) != DELTA_ROW_COUNT):
        raise CatalogError("malformed literal cumulative v33 delta")
    result = _combine(parent, manifest["previous_v31_metadata"], manifest["previous_v32_metadata"],
                      manifest["metadata"], delta["theorems"])
    previous._unchanged(bindings, owner)
    return result


def encode_catalog(metadata, cumulative_rows):
    """Return the manifest/delta bytes; never write, follow parents or admit."""
    owner = previous._owner(None)
    raw, prior_fingerprint = previous._read_file(PREVIOUS_MANIFEST, owner_uid=owner,
        expected_bytes=PREVIOUS_MANIFEST_BYTES, expected_sha256=PREVIOUS_MANIFEST_SHA256)
    prior_manifest = previous._decode(raw, "literal v32 manifest")
    if (set(prior_manifest) != {"schema", "metadata", "parent", "delta", "previous_v31_metadata"}
            or prior_manifest["schema"] != parent_codec.TRANSPORT_SCHEMA):
        raise CatalogError("the previous manifest is not the exact frozen v32 transport")
    ancestor_metadata = _ancestor_metadata(prior_manifest["previous_v31_metadata"])
    prior_metadata = _previous_metadata(prior_manifest["metadata"])
    raw, parent_fingerprint = previous._read_file(DEFAULT_PARENT, owner_uid=owner,
        expected_bytes=PARENT_BYTES, expected_sha256=PARENT_SHA256)
    parent = previous._decode(raw, "literal v30 base")
    del raw
    _combine(parent, ancestor_metadata, prior_metadata, metadata, cumulative_rows)
    delta = previous._json_bytes({"schema": DELTA_SCHEMA, "row_count": DELTA_ROW_COUNT, "theorems": cumulative_rows})
    manifest = previous._json_bytes({"schema": TRANSPORT_SCHEMA, "metadata": metadata,
        "previous_v31_metadata": ancestor_metadata, "previous_v32_metadata": prior_metadata,
        "parent": previous._parent_binding(),
        "delta": {"path": DELTA_BASENAME, "bytes": len(delta), "sha256": sha256(delta).hexdigest(),
                  "schema": DELTA_SCHEMA, "row_count": DELTA_ROW_COUNT}})
    for path, fingerprint in ((PREVIOUS_MANIFEST, prior_fingerprint), (DEFAULT_PARENT, parent_fingerprint)):
        if previous._stat_file(path, owner, fingerprint.size) != fingerprint:
            raise CatalogError("a literal parent changed during v33 encoding")
    return manifest, delta

