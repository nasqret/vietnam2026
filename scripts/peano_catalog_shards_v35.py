"""Explicit v35 three-file catalogue transport, never proof authority.

The logical catalogue budget remains v34's 8192 rows. The immutable
v30 base and all 1001 cumulative v31-v34 rows retain their original validators
and identities. No historical globals, proof limits or I/O budgets change.
"""
from collections import Counter
from hashlib import sha256

import peano_catalog_shards as previous
import peano_catalog_shards_v34 as parent_codec
import peano_catalog_capacity_v34 as capacity

CatalogError = previous.CatalogError
CatalogBindings = previous.CatalogBindings
CatalogFileBinding = previous.CatalogFileBinding
FileFingerprint = previous.FileFingerprint
TRANSPORT_SCHEMA = "peano-library-alpha-shards-v35"
LOGICAL_SCHEMA = "peano-library-alpha-snapshot-v35"
DELTA_SCHEMA = "peano-library-alpha-delta-v35"
PARENT_SCHEMA = previous.PARENT_SCHEMA
PARENT_BASENAME = previous.PARENT_BASENAME
PARENT_BYTES = previous.PARENT_BYTES
PARENT_SHA256 = previous.PARENT_SHA256
PARENT_ROW_COUNT = previous.PARENT_ROW_COUNT
DELTA_BASENAME = "catalog-v35-delta.json"
INHERITED_DELTA_COUNT = 1001
PREVIOUS_ROW_COUNT = 4223
STABLE_COUNT = 432
# Exact novel Jordan source inventory after conservative alias reconciliation.
# These counts confer no admission; fresh release evidence remains mandatory.
NEW_ROW_COUNT = 95
DELTA_ROW_COUNT = 1096
ROW_COUNT = 4318
EXPECTED_CAMPAIGNS = {"jordan-totient": 95}
CANONICAL_ORDER_SUFFIX = (
    "Constructive Alpha-v35 jordan-totient (95)",
)
MAX_ROWS = capacity.MAX_ROWS
MAX_REFERENCED_DOCUMENTS = previous.MAX_REFERENCED_DOCUMENTS
MAX_CATALOG_BYTES = previous.MAX_CATALOG_BYTES
MAX_DEPENDENCIES_PER_ROW = previous.MAX_DEPENDENCIES_PER_ROW
MAX_EDGES = previous.MAX_EDGES
MAX_JSON_CONTAINERS = previous.MAX_JSON_CONTAINERS
MAX_JSON_DEPTH = previous.MAX_JSON_DEPTH
MAX_JSON_VALUES = previous.MAX_JSON_VALUES
DEFAULT_PARENT = previous.DEFAULT_PARENT
PREVIOUS_MANIFEST = DEFAULT_PARENT.with_name("catalog-v34.json")
PREVIOUS_MANIFEST_BYTES = 1324026
PREVIOUS_MANIFEST_SHA256 = "33db63eccfb26d68c8c5f7928c48a15a53c8fde6df990441e7ccb747f6a1bcd8"
PREVIOUS_METADATA_BYTES = 377182
PREVIOUS_METADATA_SHA256 = "9c2a10a77df92cd4ba7c5e96e39efa1c3e134008adb2c04d30262fbcdcdd2e5a"
INHERITED_DELTA_SHA256 = "906dbdb47cad0feb5e6288c736b5136f58c8f5b011212b63630e7d28cbaf99a3"
CAPACITY_METADATA = parent_codec.CAPACITY_METADATA
_NEW_FIELDS = frozenset(("alpha_v35_research_promotion", "frontier_v35_campaign_counts",
    "frontier_v35_ordered_names_sha256", "parent_alpha_v34"))
_content_digest = parent_codec._content_digest


def require_registration():
    if (type(NEW_ROW_COUNT) is not int or NEW_ROW_COUNT != 95
            or type(DELTA_ROW_COUNT) is not int or DELTA_ROW_COUNT != INHERITED_DELTA_COUNT + NEW_ROW_COUNT
            or type(ROW_COUNT) is not int or ROW_COUNT != PREVIOUS_ROW_COUNT + NEW_ROW_COUNT
            or type(EXPECTED_CAMPAIGNS) is not dict or not EXPECTED_CAMPAIGNS):
        raise CatalogError("the exact v35 new inventory is not registered")
    capacity.logical_count(ROW_COUNT, "v35 theorem count")
    capacity.counts(EXPECTED_CAMPAIGNS, "v35 campaign counts")
    if sum(EXPECTED_CAMPAIGNS.values()) != NEW_ROW_COUNT or any(v <= 0 for v in EXPECTED_CAMPAIGNS.values()):
        raise CatalogError("v35 exact campaign partition differs")


def _previous_metadata(value):
    if type(value) is not dict or "theorems" in value:
        raise CatalogError("the prior metadata must be a literal object without rows")
    raw = previous._json_bytes(value)
    if len(raw) != PREVIOUS_METADATA_BYTES or sha256(raw).hexdigest() != PREVIOUS_METADATA_SHA256:
        raise CatalogError("the literal immutable v34 metadata changed")
    parent_codec._metadata_header(value)
    return value


def _metadata_header(metadata):
    require_registration()
    required = (previous._CURRENT_FIELDS | previous._NEW_FIELDS
                | parent_codec.parent_codec.parent_codec._NEW_FIELDS
                | parent_codec.parent_codec._NEW_FIELDS | parent_codec._NEW_FIELDS | _NEW_FIELDS)
    if type(metadata) is not dict or "theorems" in metadata or not required <= set(metadata):
        raise CatalogError("incomplete logical v35 metadata or unexpected inline theorem rows")
    if type(metadata["schema"]) is not str or metadata["schema"] != LOGICAL_SCHEMA:
        raise CatalogError("the logical catalogue is not Alpha v35")
    for key, wanted in (("theorem_count", ROW_COUNT), ("checked_use_count", ROW_COUNT),
                        ("stable_count", STABLE_COUNT), ("alpha_only_count", ROW_COUNT-STABLE_COUNT)):
        if capacity.logical_count(metadata[key], key) != wanted:
            raise CatalogError("the exact v35 metadata count changed: " + key)
    previous._integer(metadata["edge_count"], "edge_count", maximum=MAX_EDGES)
    capacity.logical_count(metadata["layer_count"], "layer_count", minimum=1)
    for key in (*previous._IDENTITY_FIELDS, "frontier_v32_ordered_names_sha256",
                "frontier_v33_ordered_names_sha256", "frontier_v34_ordered_names_sha256", "frontier_v35_ordered_names_sha256"):
        previous._digest(metadata[key], key)
    for key in ("membership_counts", "evidence_counts", "enrollment_origin_counts",
                "frontier_v31_campaign_counts", "frontier_v32_campaign_counts",
                "frontier_v33_campaign_counts", "frontier_v34_campaign_counts", "frontier_v35_campaign_counts"):
        capacity.counts(metadata[key], key)
    if not previous._same(metadata["frontier_v35_campaign_counts"], EXPECTED_CAMPAIGNS):
        raise CatalogError("the exact v35 ownership partition changed")
    if not previous._same(metadata["catalogue_capacity_v34"], CAPACITY_METADATA):
        raise CatalogError("the reviewed catalogue-only capacity policy changed")
    for key in ("parent_alpha_v34", "alpha_v35_research_promotion"):
        if type(metadata[key]) is not dict or not metadata[key]:
            raise CatalogError("missing v35 parent or promotion metadata")
    return metadata


def _validate_binding(value, *, parent):
    if parent:
        return previous._validate_binding(value, parent=True)
    require_registration()
    if type(value) is not dict or set(value) != previous._BINDING_FIELDS:
        raise CatalogError("the cumulative delta binding needs exactly five fields")
    if type(value["path"]) is not str or value["path"] != DELTA_BASENAME:
        raise CatalogError("only the exact same-directory v35 delta basename is allowed")
    if type(value["schema"]) is not str or value["schema"] != DELTA_SCHEMA:
        raise CatalogError("the cumulative delta schema is not the literal v35 schema")
    if capacity.logical_count(value["row_count"], "delta row count") != DELTA_ROW_COUNT:
        raise CatalogError("the exact cumulative delta count changed")
    previous._integer(value["bytes"], "delta bytes", minimum=1, maximum=MAX_CATALOG_BYTES)
    previous._digest(value["sha256"], "delta digest")
    return value


def _manifest(path, expected_sha256, owner_uid):
    path, owner = previous._absolute_path(path), previous._owner(owner_uid)
    raw, fingerprint = previous._read_file(path, owner_uid=owner, expected_sha256=expected_sha256)
    value = previous._decode(raw, "v35 manifest")
    if (type(value) is not dict or set(value) != {"schema", "metadata", "parent", "delta",
            "previous_v31_metadata", "previous_v32_metadata", "previous_v33_metadata", "previous_v34_metadata"}
            or value["schema"] != TRANSPORT_SCHEMA):
        raise CatalogError("v35 requires exactly two data bindings and pinned inline v31/v32/v33/v34 metadata")
    _metadata_header(value["metadata"])
    parent_codec.parent_codec._ancestor_metadata(value["previous_v31_metadata"])
    parent_codec.parent_codec._previous_metadata(value["previous_v32_metadata"])
    parent_codec._previous_metadata(value["previous_v33_metadata"])
    _previous_metadata(value["previous_v34_metadata"])
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
        raise CatalogError("v35 data documents must be three distinct ordinary files")
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


def _combine(parent, v31_metadata, v32_metadata, v33_metadata, prior_metadata, metadata, cumulative_rows):
    """Structural transport validation only; original proof gates stay separate."""
    parent_codec.parent_codec._ancestor_metadata(v31_metadata)
    parent_codec.parent_codec._previous_metadata(v32_metadata)
    parent_codec._previous_metadata(v33_metadata)
    _previous_metadata(prior_metadata)
    _metadata_header(metadata)
    if type(cumulative_rows) is not list or len(cumulative_rows) != DELTA_ROW_COUNT:
        raise CatalogError("the exact inherited1001 plus new v35 rows are required")
    inherited_rows = cumulative_rows[:INHERITED_DELTA_COUNT]
    new_rows = cumulative_rows[INHERITED_DELTA_COUNT:]
    if _content_digest(inherited_rows) != INHERITED_DELTA_SHA256:
        raise CatalogError("one of the1001 immutable v31-v34 theorem records changed")
    # The original v34 validator checks all4223 old rows with its own8192 catalogue cap.
    # No patched globals, shortened inherited inventory or replacement validator.
    prior = parent_codec._combine(parent, v31_metadata, v32_metadata, v33_metadata, prior_metadata, inherited_rows)
    inherited = set(prior_metadata)
    if set(metadata) != inherited | _NEW_FIELDS:
        raise CatalogError("logical v35 metadata dropped old fields or added unknown fields")
    for key in inherited - previous._CURRENT_FIELDS:
        if not previous._same(metadata[key], prior_metadata[key]):
            raise CatalogError("immutable historical metadata changed: " + key)
    old_order, order = prior_metadata["canonical_order"], metadata["canonical_order"]
    if (type(order) is not list or len(order) != len(old_order)+len(EXPECTED_CAMPAIGNS)
            or order[:len(old_order)] != old_order
            or tuple(order[len(old_order):]) != CANONICAL_ORDER_SUFFIX
            or any(type(item) is not str or not item for item in order)
            or len(set(order)) != len(order)):
        raise CatalogError("v35 must append exactly its distinct campaign-order entries")
    old_documents = previous._documents(prior_metadata["evidence_documents"], "v34")
    documents = previous._documents(metadata["evidence_documents"], "v35")
    for path, old in old_documents.items():
        if path not in documents or not previous._same(old, documents[path]):
            raise CatalogError("immutable v34 evidence record changed: " + path)
    rows = [*prior["theorems"], *new_rows]
    edges, layer_count, counts = capacity.validate_rows(rows, ROW_COUNT)
    expected = {
        "membership_counts": {"stable": STABLE_COUNT, "alpha_only": ROW_COUNT-STABLE_COUNT},
        "evidence_counts": {"stable_closed": STABLE_COUNT, "alpha_closed": ROW_COUNT-STABLE_COUNT},
        "enrollment_origin_counts": dict(Counter(prior_metadata["enrollment_origin_counts"]) + Counter(ha=NEW_ROW_COUNT)),
    }
    for key, row_key in (("membership_counts", "membership"), ("evidence_counts", "evidence_status"),
                         ("enrollment_origin_counts", "enrollment_origin")):
        if not previous._same(metadata[key], expected[key]) or counts[row_key] != expected[key]:
            raise CatalogError("v35 counts differ from the actual ordered rows: " + key)
    if metadata["edge_count"] != edges or metadata["layer_count"] != layer_count:
        raise CatalogError("v35 topology metadata differs from the actual dependency DAG")
    campaigns = []
    for campaign, count in EXPECTED_CAMPAIGNS.items():
        campaigns.extend([campaign]*count)
    if any(row.get("frontier_campaign") != campaign
           or row["membership"] != "alpha_only" or row["evidence_status"] != "alpha_closed"
           or row["enrollment_origin"] != "ha" for row, campaign in zip(new_rows, campaigns, strict=True)):
        raise CatalogError("the exact ordered v35 admission partition changed")
    names = sha256("\n".join(row["name"] for row in new_rows).encode()).hexdigest()
    if metadata["frontier_v35_ordered_names_sha256"] != names:
        raise CatalogError("v35 ordered theorem-name digest differs from the actual new rows")
    return {**metadata, "theorems": rows}


def load_catalog(path, *, expected_sha256, owner_uid=None):
    manifest, bindings, owner = _manifest(path, expected_sha256, owner_uid)
    values = []
    for item in (bindings.parent, bindings.delta):
        raw, fingerprint = previous._read_file(item.path, owner_uid=owner,
            expected_bytes=item.bytes, expected_sha256=item.sha256)
        if fingerprint != item.fingerprint:
            raise CatalogError("catalogue document changed after its binding: " + item.role)
        values.append(previous._decode(raw, "v35 " + item.role))
        del raw
    parent, delta = values
    if (type(delta) is not dict or set(delta) != {"schema", "row_count", "theorems"}
            or delta["schema"] != DELTA_SCHEMA
            or capacity.logical_count(delta.get("row_count"), "delta row count") != DELTA_ROW_COUNT):
        raise CatalogError("malformed literal cumulative v35 delta")
    result = _combine(parent, manifest["previous_v31_metadata"], manifest["previous_v32_metadata"],
                      manifest["previous_v33_metadata"], manifest["previous_v34_metadata"], manifest["metadata"], delta["theorems"])
    previous._unchanged(bindings, owner)
    return result


def encode_catalog(metadata, cumulative_rows):
    """Return manifest/delta bytes; never write, follow parents or admit."""
    require_registration()
    owner = previous._owner(None)
    raw, prior_fingerprint = previous._read_file(PREVIOUS_MANIFEST, owner_uid=owner,
        expected_bytes=PREVIOUS_MANIFEST_BYTES, expected_sha256=PREVIOUS_MANIFEST_SHA256)
    prior_manifest = previous._decode(raw, "literal v34 manifest")
    if (type(prior_manifest) is not dict or set(prior_manifest) != {"schema", "metadata", "parent", "delta",
            "previous_v31_metadata", "previous_v32_metadata", "previous_v33_metadata"}
            or prior_manifest["schema"] != parent_codec.TRANSPORT_SCHEMA):
        raise CatalogError("the previous manifest is not the exact frozen v34 transport")
    v31_metadata = parent_codec.parent_codec._ancestor_metadata(prior_manifest["previous_v31_metadata"])
    v32_metadata = parent_codec.parent_codec._previous_metadata(prior_manifest["previous_v32_metadata"])
    v33_metadata = parent_codec._previous_metadata(prior_manifest["previous_v33_metadata"])
    prior_metadata = _previous_metadata(prior_manifest["metadata"])
    raw, parent_fingerprint = previous._read_file(DEFAULT_PARENT, owner_uid=owner,
        expected_bytes=PARENT_BYTES, expected_sha256=PARENT_SHA256)
    parent = previous._decode(raw, "literal v30 base")
    del raw
    _combine(parent, v31_metadata, v32_metadata, v33_metadata, prior_metadata, metadata, cumulative_rows)
    delta = previous._json_bytes({"schema": DELTA_SCHEMA, "row_count": DELTA_ROW_COUNT, "theorems": cumulative_rows})
    manifest = previous._json_bytes({"schema": TRANSPORT_SCHEMA, "metadata": metadata,
        "previous_v31_metadata": v31_metadata, "previous_v32_metadata": v32_metadata,
        "previous_v33_metadata": v33_metadata, "previous_v34_metadata": prior_metadata, "parent": previous._parent_binding(),
        "delta": {"path": DELTA_BASENAME, "bytes": len(delta), "sha256": sha256(delta).hexdigest(),
                  "schema": DELTA_SCHEMA, "row_count": DELTA_ROW_COUNT}})
    for path, fingerprint in ((PREVIOUS_MANIFEST, prior_fingerprint), (DEFAULT_PARENT, parent_fingerprint)):
        if previous._stat_file(path, owner, fingerprint.size) != fingerprint:
            raise CatalogError("a literal parent changed during v35 encoding")
    return manifest, delta
