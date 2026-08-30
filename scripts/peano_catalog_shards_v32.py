"""Bounded, nonrecursive Alpha-v32 transport; never a proof authority.

Exactly three files retain the original 64-MiB per-file budget: this edition's
manifest, the literal v30 base, and a cumulative delta with the unchanged 574
v31 rows followed by 175 new rows.  A small, literally pinned copy of the v31
metadata permits the original v31 structural validator to check that prefix
without following another manifest or accepting a general recursive format.
The original codec and all of its resource and path-safety limits are intact.
"""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

import peano_catalog_shards as previous


CatalogError = previous.CatalogError
CatalogBindings = previous.CatalogBindings
CatalogFileBinding = previous.CatalogFileBinding
FileFingerprint = previous.FileFingerprint
TRANSPORT_SCHEMA = "peano-library-alpha-shards-v32"
LOGICAL_SCHEMA = "peano-library-alpha-snapshot-v32"
DELTA_SCHEMA = "peano-library-alpha-delta-v32"
PARENT_SCHEMA = previous.PARENT_SCHEMA
PARENT_BASENAME = previous.PARENT_BASENAME
PARENT_BYTES = previous.PARENT_BYTES
PARENT_SHA256 = previous.PARENT_SHA256
PARENT_ROW_COUNT = previous.PARENT_ROW_COUNT
DELTA_BASENAME = "catalog-v32-delta.json"
INHERITED_DELTA_COUNT = 574
NEW_ROW_COUNT = 175
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
PREVIOUS_MANIFEST = DEFAULT_PARENT.with_name("catalog-v31.json")
PREVIOUS_MANIFEST_BYTES = 293_294
PREVIOUS_MANIFEST_SHA256 = "6c9ebfb3c37e42aefab200b710f78e7693dc5826c80f053544deea41caf44aab"
PREVIOUS_METADATA_BYTES = 292_856
PREVIOUS_METADATA_SHA256 = "0f012d7aeaf20fcdb59a5500929face631012608ad1712010a8455816af3c1a7"
INHERITED_DELTA_SHA256 = "961b210841a1928926fedf9d0fe46b95fa5fe2ce7985ef932ec1c787f65c8ef6"
EXPECTED_CAMPAIGNS = {"multiplicative-convolution": 90, "polynomial-division-prerequisites": 85}
_NEW_FIELDS = frozenset(("alpha_v32_research_promotion", "frontier_v32_campaign_counts",
                         "frontier_v32_ordered_names_sha256", "parent_alpha_v31"))


def _content_digest(value):
    """Canonical JSON identity without another full in-memory serialization."""
    result = sha256()
    encoder = json.JSONEncoder(ensure_ascii=False, allow_nan=False, sort_keys=True,
                               separators=(",", ":"))
    try:
        for piece in encoder.iterencode(value):
            result.update(piece.encode("utf-8"))
    except (TypeError, ValueError, UnicodeError, RecursionError) as error:
        raise CatalogError("invalid canonical catalogue value") from error
    result.update(b"\n")
    return result.hexdigest()


def _previous_metadata(value):
    if type(value) is not dict or "theorems" in value:
        raise CatalogError("the prior metadata must be a literal object without rows")
    raw = previous._json_bytes(value)
    if len(raw) != PREVIOUS_METADATA_BYTES or sha256(raw).hexdigest() != PREVIOUS_METADATA_SHA256:
        raise CatalogError("the literal immutable v31 metadata changed")
    previous._metadata_header(value)
    return value


def _metadata_header(metadata):
    required = previous._CURRENT_FIELDS | previous._NEW_FIELDS | _NEW_FIELDS
    if type(metadata) is not dict or "theorems" in metadata or not required <= set(metadata):
        raise CatalogError("incomplete logical v32 metadata or unexpected inline theorem rows")
    if metadata["schema"] != LOGICAL_SCHEMA or type(metadata["schema"]) is not str:
        raise CatalogError("the logical catalogue is not Alpha v32")
    for key, wanted in (("theorem_count", ROW_COUNT), ("checked_use_count", ROW_COUNT),
                        ("stable_count", STABLE_COUNT), ("alpha_only_count", ROW_COUNT-STABLE_COUNT)):
        if previous._integer(metadata[key], key, maximum=MAX_ROWS) != wanted:
            raise CatalogError("the exact v32 metadata count changed: " + key)
    previous._integer(metadata["edge_count"], "edge_count", maximum=MAX_EDGES)
    previous._integer(metadata["layer_count"], "layer_count", minimum=1, maximum=MAX_ROWS)
    for key in (*previous._IDENTITY_FIELDS, "frontier_v32_ordered_names_sha256"):
        previous._digest(metadata[key], key)
    for key in ("membership_counts", "evidence_counts", "enrollment_origin_counts",
                "frontier_v31_campaign_counts", "frontier_v32_campaign_counts"):
        previous._counts(metadata[key], key)
    if not previous._same(metadata["frontier_v32_campaign_counts"], EXPECTED_CAMPAIGNS):
        raise CatalogError("the exact two-family v32 ownership partition changed")
    for key in ("parent_alpha_v31", "alpha_v32_research_promotion"):
        if type(metadata[key]) is not dict or not metadata[key]:
            raise CatalogError("missing v32 parent or promotion metadata")
    return metadata


def _validate_binding(value, *, parent):
    if parent:
        return previous._validate_binding(value, parent=True)
    if type(value) is not dict or set(value) != previous._BINDING_FIELDS:
        raise CatalogError("the cumulative delta binding needs exactly five fields")
    if type(value["path"]) is not str or value["path"] != DELTA_BASENAME:
        raise CatalogError("only the exact same-directory v32 delta basename is allowed")
    if type(value["schema"]) is not str or value["schema"] != DELTA_SCHEMA:
        raise CatalogError("the cumulative delta schema is not the literal v32 schema")
    if previous._integer(value["row_count"], "delta row count", maximum=MAX_ROWS) != DELTA_ROW_COUNT:
        raise CatalogError("the cumulative delta must have exactly 749 rows")
    previous._integer(value["bytes"], "delta bytes", minimum=1, maximum=MAX_CATALOG_BYTES)
    previous._digest(value["sha256"], "delta digest")
    return value


def _manifest(path, expected_sha256, owner_uid):
    path, owner = previous._absolute_path(path), previous._owner(owner_uid)
    raw, fingerprint = previous._read_file(path, owner_uid=owner, expected_sha256=expected_sha256)
    value = previous._decode(raw, "v32 manifest")
    if (set(value) != {"schema", "metadata", "parent", "delta", "previous_v31_metadata"}
            or value["schema"] != TRANSPORT_SCHEMA):
        raise CatalogError("v32 requires exactly two data bindings and pinned inline v31 metadata")
    _metadata_header(value["metadata"])
    _previous_metadata(value["previous_v31_metadata"])
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
        raise CatalogError("v32 data documents must be three distinct ordinary files")
    return value, CatalogBindings(*files), owner


def catalog_input_fingerprint(path, *, expected_sha256, owner_uid=None):
    """A three-file stat key, never a hash check or mathematical authority."""
    _value, bindings, owner = _manifest(path, expected_sha256, owner_uid)
    previous._unchanged(bindings, owner)
    return bindings.fingerprint


def verify_catalog_bindings(path, *, expected_sha256, owner_uid=None):
    """Read and authenticate every byte; do not parse or accept a proof."""
    _value, bindings, owner = _manifest(path, expected_sha256, owner_uid)
    for item in (bindings.parent, bindings.delta):
        _raw, fingerprint = previous._read_file(item.path, owner_uid=owner,
            expected_bytes=item.bytes, expected_sha256=item.sha256, capture=False)
        if fingerprint != item.fingerprint:
            raise CatalogError("catalogue file changed after its binding was read: " + item.role)
    previous._unchanged(bindings, owner)
    return bindings


def _combine(parent, prior_metadata, metadata, cumulative_rows):
    """Structural transport validation only; proof gates remain separate."""
    _previous_metadata(prior_metadata)
    _metadata_header(metadata)
    if type(cumulative_rows) is not list or len(cumulative_rows) != DELTA_ROW_COUNT:
        raise CatalogError("the cumulative delta must have exactly 574 inherited and 175 new rows")
    inherited_rows, new_rows = cumulative_rows[:INHERITED_DELTA_COUNT], cumulative_rows[INHERITED_DELTA_COUNT:]
    if _content_digest(inherited_rows) != INHERITED_DELTA_SHA256:
        raise CatalogError("one of the 574 immutable v31 theorem records changed")
    # This is the unmodified v31 structural verifier, not a monkey-patched
    # schema or an inherited success receipt.  The literal v30 bytes have
    # already been authenticated by the caller.
    prior = previous._combine(parent, prior_metadata, inherited_rows)
    inherited = set(prior_metadata)
    if set(metadata) != inherited | _NEW_FIELDS:
        raise CatalogError("logical v32 metadata dropped old fields or added unknown fields")
    for key in inherited - previous._CURRENT_FIELDS:
        if not previous._same(metadata[key], prior_metadata[key]):
            raise CatalogError("immutable historical metadata changed: " + key)
    old_order, order = prior_metadata["canonical_order"], metadata["canonical_order"]
    if (type(order) is not list or len(order) != len(old_order)+2
            or order[:len(old_order)] != old_order
            or any(type(item) is not str or not item for item in order)
            or len(set(order)) != len(order)):
        raise CatalogError("v32 must append exactly two distinct campaign-order entries")
    old_documents = previous._documents(prior_metadata["evidence_documents"], "v31")
    documents = previous._documents(metadata["evidence_documents"], "v32")
    for path, old in old_documents.items():
        if path not in documents or not previous._same(old, documents[path]):
            raise CatalogError("immutable v31 evidence record changed: " + path)
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
            raise CatalogError("v32 metadata counts differ from the actual ordered rows: " + key)
    if metadata["edge_count"] != edges or metadata["layer_count"] != layer_count:
        raise CatalogError("v32 topology metadata differs from the actual dependency DAG")
    slugs = []
    for row in new_rows:
        slug = row.get("frontier_campaign")
        if (type(slug) is not str or slug not in EXPECTED_CAMPAIGNS
                or row["membership"] != "alpha_only" or row["evidence_status"] != "alpha_closed"
                or row["enrollment_origin"] != "ha"):
            raise CatalogError("a new row has an unreviewed family, membership or origin")
        slugs.append(slug)
    if slugs != ["multiplicative-convolution"]*90 + ["polynomial-division-prerequisites"]*85:
        raise CatalogError("the exact ordered 90/85 admission partition changed")
    names = sha256("\n".join(row["name"] for row in new_rows).encode()).hexdigest()
    if metadata["frontier_v32_ordered_names_sha256"] != names:
        raise CatalogError("v32 ordered theorem-name digest differs from the actual new rows")
    return {**metadata, "theorems": rows}


def load_catalog(path, *, expected_sha256, owner_uid=None):
    manifest, bindings, owner = _manifest(path, expected_sha256, owner_uid)
    values = []
    for item in (bindings.parent, bindings.delta):
        raw, fingerprint = previous._read_file(item.path, owner_uid=owner,
            expected_bytes=item.bytes, expected_sha256=item.sha256)
        if fingerprint != item.fingerprint:
            raise CatalogError("catalogue document changed after its binding: " + item.role)
        values.append(previous._decode(raw, "v32 " + item.role))
        del raw
    parent, delta = values
    if (set(delta) != {"schema", "row_count", "theorems"} or delta["schema"] != DELTA_SCHEMA
            or previous._integer(delta.get("row_count"), "delta row count", maximum=MAX_ROWS) != DELTA_ROW_COUNT):
        raise CatalogError("malformed literal cumulative v32 delta")
    result = _combine(parent, manifest["previous_v31_metadata"], manifest["metadata"], delta["theorems"])
    previous._unchanged(bindings, owner)
    return result


def encode_catalog(metadata, cumulative_rows):
    """Return three-file-format manifest/delta bytes; never write or admit."""
    owner = previous._owner(None)
    raw, prior_fingerprint = previous._read_file(PREVIOUS_MANIFEST, owner_uid=owner,
        expected_bytes=PREVIOUS_MANIFEST_BYTES, expected_sha256=PREVIOUS_MANIFEST_SHA256)
    prior_manifest = previous._decode(raw, "literal v31 manifest")
    if set(prior_manifest) != {"schema", "metadata", "parent", "delta"} or prior_manifest["schema"] != previous.TRANSPORT_SCHEMA:
        raise CatalogError("the previous manifest is not the exact frozen v31 transport")
    prior_metadata = _previous_metadata(prior_manifest["metadata"])
    raw, parent_fingerprint = previous._read_file(DEFAULT_PARENT, owner_uid=owner,
        expected_bytes=PARENT_BYTES, expected_sha256=PARENT_SHA256)
    parent = previous._decode(raw, "literal v30 base")
    del raw
    _combine(parent, prior_metadata, metadata, cumulative_rows)
    delta = previous._json_bytes({"schema": DELTA_SCHEMA, "row_count": DELTA_ROW_COUNT, "theorems": cumulative_rows})
    manifest = previous._json_bytes({"schema": TRANSPORT_SCHEMA, "metadata": metadata,
        "previous_v31_metadata": prior_metadata, "parent": previous._parent_binding(),
        "delta": {"path": DELTA_BASENAME, "bytes": len(delta), "sha256": sha256(delta).hexdigest(),
                  "schema": DELTA_SCHEMA, "row_count": DELTA_ROW_COUNT}})
    for path, fingerprint in ((PREVIOUS_MANIFEST, prior_fingerprint), (DEFAULT_PARENT, parent_fingerprint)):
        if previous._stat_file(path, owner, fingerprint.size) != fingerprint:
            raise CatalogError("a literal parent changed during v32 encoding")
    return manifest, delta
