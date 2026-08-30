"""Bounded, declared-lineage proposals; no proof, model, file or network access.

All SHA arguments in this module are canonical JSON/semantic SHA-256 values,
not raw-file hashes. File descriptors, exposure summaries and provenance are
externally supplied declarations: their preimages are bound, but this module
does not authenticate filesystem bytes, Git objects, human identity or hidden
training exposure. Native admission and the existing lineage/reference gates
remain separate. A validated human assertion cannot seal a test set or grant
compute authority. No function creates a human review record.
"""

from collections import defaultdict, deque
import datetime
import hashlib
import json
import re


INVENTORY_SCHEMA = "peano-hydra-scaling-lineage-inventory-v1"
PROPOSAL_SCHEMA = "peano-hydra-scaling-lineage-proposal-v1"
AUDIT_SCHEMA = "peano-hydra-scaling-lineage-audit-v1"
REVIEW_SCHEMA = "peano-hydra-scaling-lineage-review-v1"
REVIEW_VALIDATION_SCHEMA = "peano-hydra-scaling-lineage-review-validation-v1"
PILOT_PROFILE = "peano-hydra-scaling-lineage-pilot-v1"
LARGE_PROFILE = "peano-hydra-scaling-lineage-large-v1"
MAX_RECORDS = 32768
MAX_FILES = 4096
MAX_EXPOSURES = 64
MAX_RELATIONS = 262144
MAX_JSON_BYTES = 128 * 1024 * 1024
MAX_JSON_NODES = 2097152
MAX_JSON_DEPTH = 24
# These are descriptor sizes, not bytes read here. Historical training JSONL
# already exceeds source-code file sizes; declared sharded data may be larger.
MAX_FILE_BYTES = 1024**3
MAX_DECLARED_FILE_BYTES = 64 * 1024**3
SPLITS = frozenset(("train", "dev", "test", "quarantine"))
ACKNOWLEDGMENTS = (
    "declared_relations_and_exposures_only",
    "no_unseen_or_semantic_completeness_claim",
    "no_independent_test_seal_or_compute_authority",
    "reviewer_identity_not_cryptographically_verified",
)
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_COMMIT = re.compile(r"[0-9a-f]{40}\Z")
_ID = re.compile(r"[A-Za-z0-9_][A-Za-z0-9_.:-]{0,127}\Z", re.ASCII)
_ROUTE_FIELDS = frozenset((
    "route_id", "family", "template_sha256", "statement_sha256", "lineage_sha256",
    "parent_lineages", "dependency_ids", "equivalent_ids", "intermediate_statement_sha256s",
    "intermediate_state_sha256s", "source_sha256", "epoch_sha256", "authority_sha256",
    "seed", "provenance_complete",
))
_EXPOSURE_HASH_FIELDS = (
    "template_sha256s", "lineage_sha256s", "statement_sha256s",
    "intermediate_statement_sha256s", "intermediate_state_sha256s",
)
_INVENTORY_FIELDS = frozenset((
    "schema", "bounds_profile", "source_commit", "source_dirty", "source_files", "source_files_sha256",
    "epoch_sha256", "authority_sha256", "canonicalization_sha256", "records", "parents",
    "exposure_requirements", "exposures", "exclusions",
))
_PROPOSAL_FIELDS = frozenset((
    "schema", "inventory", "inventory_sha256", "allocations", "components", "relations",
    "relations_sha256", "conflicts", "review_requests", "counts", "status", "claims",
    "resource_bounds", "proposal_sha256",
))


class ScalingLineageError(ValueError):
    """An inventory, allocation or external assertion lost its exact scope."""


def _require(condition, message):
    if not condition:
        raise ScalingLineageError(message)


def bounds_profile_record(profile=PILOT_PROFILE):
    """Fixed metadata envelopes; caller still supervises actual CPU/RSS usage."""
    _require(type(profile) is str and profile in (PILOT_PROFILE, LARGE_PROFILE), "unknown lineage bounds profile")
    large = profile == LARGE_PROFILE
    return {
        "name": profile,
        "max_route_records": min(MAX_RECORDS, 32768 if large else 4096),
        "max_parent_records": min(MAX_RECORDS, 32768 if large else 4096),
        "max_relations": min(MAX_RELATIONS, 262144 if large else 131072),
        "max_inventory_bytes": min(MAX_JSON_BYTES, (48 if large else 16) * 1024 * 1024),
        "max_result_bytes": min(MAX_JSON_BYTES, (128 if large else 48) * 1024 * 1024),
        "max_json_nodes": MAX_JSON_NODES, "max_json_depth": MAX_JSON_DEPTH,
        "recommended_worker_rss_bytes": 1024**3, "runtime_rss_measured_here": False,
    }


def canonical_bytes(value):
    """Strict bounded JSON; reject subclasses, cycles, floats and hidden hooks."""
    active, count = set(), 0
    stack = [(value, 0, False)]
    while stack:
        item, depth, leaving = stack.pop()
        if leaving:
            active.remove(id(item))
            continue
        count += 1
        _require(count <= MAX_JSON_NODES and depth <= MAX_JSON_DEPTH, "JSON structural bound exceeded")
        kind = type(item)
        if kind is dict or kind is list:
            _require(len(item) <= MAX_JSON_NODES, "JSON container bound exceeded")
            _require(id(item) not in active, "cyclic JSON is not an inventory")
            active.add(id(item))
            stack.append((item, depth, True))
            if kind is dict:
                _require(all(type(key) is str for key in item), "JSON keys must be exact strings")
                for key, child in item.items():
                    stack.append((key, depth + 1, False))
                    stack.append((child, depth + 1, False))
            else:
                stack.extend((child, depth + 1, False) for child in item)
            _require(len(stack) <= 2 * MAX_JSON_NODES, "JSON pending-work bound exceeded")
        elif kind is str:
            try:
                size = len(item.encode("utf-8"))
            except UnicodeError:
                raise ScalingLineageError("JSON contains invalid Unicode") from None
            _require(size <= 4096, "JSON string bound exceeded")
        elif kind is int:
            _require(-(2**63) <= item < 2**63, "JSON integer bound exceeded")
        else:
            _require(item is None or kind is bool, "non-JSON or nonfinite/float metadata value")
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                     separators=(",", ":")).encode("utf-8")
    _require(len(raw) <= MAX_JSON_BYTES, "JSON byte bound exceeded")
    return raw


def canonical_sha256(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def decode_record(raw):
    """Optional strict transport decoder; never silently keep duplicate keys."""
    _require(type(raw) is bytes and 0 < len(raw) <= MAX_JSON_BYTES, "bounded JSON bytes required")
    def pairs(items):
        result = {}
        for key, value in items:
            _require(key not in result, "duplicate JSON field")
            result[key] = value
        return result
    def invalid(_):
        raise ScalingLineageError("floating or nonfinite JSON numbers are forbidden")
    def integer(text):
        _require(len(text) <= 20, "JSON integer bound exceeded")
        return int(text)
    try:
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=pairs,
                           parse_constant=invalid, parse_float=invalid, parse_int=integer)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as error:
        raise ScalingLineageError("invalid bounded JSON: " + type(error).__name__) from None
    _require(type(value) is dict, "record must be a JSON object")
    canonical_bytes(value)
    return value


def _object(value, fields, label):
    _require(type(value) is dict and set(value) == set(fields), label + " has unexpected or missing fields")
    return value


def _sha(value, label):
    _require(type(value) is str and _SHA.fullmatch(value) is not None, label + " requires lowercase SHA-256")
    return value


def _identifier(value, label):
    _require(type(value) is str and _ID.fullmatch(value) is not None, label + " requires a bounded identifier")
    return value


def _boolean(value, label):
    _require(type(value) is bool, label + " requires a strict boolean")


def _integer(value, maximum, label):
    _require(type(value) is int and 0 <= value <= maximum, label + " requires a bounded nonnegative integer")


def _array(value, maximum, label, minimum=0):
    _require(type(value) is list and minimum <= len(value) <= maximum, label + " requires a bounded array")


def _set_list(value, validator, maximum, label):
    _array(value, maximum, label)
    for item in value:
        validator(item, label)
    _require(len(set(value)) == len(value), label + " contains duplicates")
    return sorted(value)


def _files(value, expected_sha, label):
    _require(type(value) is dict and 1 <= len(value) <= MAX_FILES, label + " requires a bounded nonempty inventory")
    total = 0
    for name, item in value.items():
        _require(type(name) is str and 0 < len(name) <= 1024 and "\\" not in name
                 and all(part not in ("", ".", "..") for part in name.split("/"))
                 and not any(ord(char) < 32 or ord(char) == 127 for char in name),
                 label + " contains a noncanonical relative path")
        _object(item, ("bytes", "sha256"), label + " file")
        _integer(item["bytes"], MAX_FILE_BYTES, label + " file bytes")
        _sha(item["sha256"], label + " file hash")
        total += item["bytes"]
    _require(total <= MAX_DECLARED_FILE_BYTES, label + " declared byte bound exceeded")
    _require(_sha(expected_sha, label + " inventory hash") == canonical_sha256(value), label + " inventory hash differs")


def _inventory(value):
    _object(value, _INVENTORY_FIELDS, "inventory")
    limits = bounds_profile_record(value["bounds_profile"])
    raw = canonical_bytes(value)
    _require(len(raw) <= limits["max_inventory_bytes"], "profile inventory byte bound exceeded")
    value = decode_record(raw)
    _require(value["schema"] == INVENTORY_SCHEMA, "inventory schema differs")
    _require(value["source_commit"] is None or type(value["source_commit"]) is str
             and _COMMIT.fullmatch(value["source_commit"]) is not None, "source commit must be exact or explicitly unknown")
    _boolean(value["source_dirty"], "source_dirty")
    _files(value["source_files"], value["source_files_sha256"], "source")
    for name in ("epoch_sha256", "authority_sha256", "canonicalization_sha256"):
        _sha(value[name], name)
    _array(value["records"], limits["max_route_records"], "route records", 1)
    route_ids = set()
    for row in value["records"]:
        _object(row, _ROUTE_FIELDS, "route")
        _identifier(row["route_id"], "route_id")
        _require(row["route_id"] not in route_ids, "duplicate route_id")
        route_ids.add(row["route_id"])
        _identifier(row["family"], "family")
        for name in ("template_sha256", "statement_sha256", "lineage_sha256", "source_sha256", "epoch_sha256", "authority_sha256"):
            _sha(row[name], "route " + name)
        for name in ("parent_lineages", "intermediate_statement_sha256s", "intermediate_state_sha256s"):
            row[name] = _set_list(row[name], _sha, 1024, "route " + name)
        for name in ("dependency_ids", "equivalent_ids"):
            row[name] = _set_list(row[name], _identifier, MAX_RECORDS, "route " + name)
        _integer(row["seed"], 2**31 - 1, "seed")
        _boolean(row["provenance_complete"], "route provenance_complete")
    value["records"].sort(key=lambda row: row["route_id"])
    _array(value["parents"], limits["max_parent_records"], "parents")
    seen = set()
    for row in value["parents"]:
        _object(row, ("lineage_sha256", "source_sha256", "epoch_sha256", "authority_sha256", "parent_lineages", "provenance_complete"), "parent")
        for name in ("lineage_sha256", "source_sha256", "epoch_sha256", "authority_sha256"):
            _sha(row[name], "parent " + name)
        _require(row["lineage_sha256"] not in seen, "duplicate parent lineage declaration")
        seen.add(row["lineage_sha256"])
        row["parent_lineages"] = _set_list(row["parent_lineages"], _sha, 1024, "parent ancestry")
        _boolean(row["provenance_complete"], "parent provenance_complete")
    value["parents"].sort(key=lambda row: row["lineage_sha256"])
    _array(value["exposure_requirements"], MAX_EXPOSURES, "exposure requirements", 1)
    requirements = {}
    for row in value["exposure_requirements"]:
        _object(row, ("exposure_id", "manifest_sha256"), "exposure requirement")
        _identifier(row["exposure_id"], "exposure_id")
        _sha(row["manifest_sha256"], "exposure manifest")
        _require(row["exposure_id"] not in requirements, "duplicate exposure requirement")
        requirements[row["exposure_id"]] = row["manifest_sha256"]
    value["exposure_requirements"].sort(key=lambda row: row["exposure_id"])
    _array(value["exposures"], MAX_EXPOSURES, "exposure summaries")
    seen = set()
    for row in value["exposures"]:
        _object(row, ("exposure_id", "manifest_sha256", "files", "files_sha256", "row_count",
                      "covered_route_ids", "complete", "families") + _EXPOSURE_HASH_FIELDS, "exposure summary")
        _identifier(row["exposure_id"], "exposure_id")
        _require(row["exposure_id"] in requirements and row["exposure_id"] not in seen,
                 "unknown or duplicate exposure summary")
        seen.add(row["exposure_id"])
        _require(_sha(row["manifest_sha256"], "exposure manifest") == requirements[row["exposure_id"]],
                 "required exposure manifest differs")
        _files(row["files"], row["files_sha256"], "exposure")
        _integer(row["row_count"], 10**9, "exposure row_count")
        _boolean(row["complete"], "exposure complete")
        row["covered_route_ids"] = _set_list(row["covered_route_ids"], _identifier, MAX_RECORDS, "covered routes")
        _require(set(row["covered_route_ids"]) <= route_ids, "exposure coverage contains unknown routes")
        row["families"] = _set_list(row["families"], _identifier, MAX_RECORDS, "exposed families")
        for name in _EXPOSURE_HASH_FIELDS:
            row[name] = _set_list(row[name], _sha, MAX_RELATIONS, "exposure " + name)
    value["exposures"].sort(key=lambda row: row["exposure_id"])
    exclusions = _object(value["exclusions"], ("manifest_sha256", "complete", "target_sha256s", "intermediate_state_sha256s"), "exclusions")
    _sha(exclusions["manifest_sha256"], "exclusions manifest")
    _boolean(exclusions["complete"], "exclusions complete")
    for name in ("target_sha256s", "intermediate_state_sha256s"):
        exclusions[name] = _set_list(exclusions[name], _sha, MAX_RELATIONS, "exclusions " + name)
    return value


def _claims():
    return {
        "declared_relations_only": True, "source_bytes_authenticated": False,
        "source_commit_authenticated": False, "semantic_equivalence_complete": False,
        "independent_human_identity_verified": False, "independent_authorship_verified": False,
        "independent_test_seal_granted": False, "eligible_for_unseen_model_comparison": False,
        "model_training_authorized": False, "gpu_execution_authorized": False,
        "h0_complete": False, "h1_complete": False, "h5_complete": False,
    }


class _Graph:
    def __init__(self, maximum):
        self.parents = {}
        self.edges = []
        self.maximum = maximum

    def root(self, node):
        self.parents.setdefault(node, node)
        while self.parents[node] != node:
            self.parents[node] = self.parents[self.parents[node]]
            node = self.parents[node]
        return node

    def join(self, left, right, relation):
        _require(len(self.edges) < self.maximum, "complete lineage relation inventory exceeds bound")
        self.edges.append([left, right, relation])
        left, right = self.root(left), self.root(right)
        if left != right:
            self.parents[max(left, right)] = min(left, right)


def _cyclic_or_dependent(adjacency):
    counts = {node: len(parents) for node, parents in adjacency.items()}
    children = defaultdict(set)
    for node, parents in adjacency.items():
        for parent in parents:
            children[parent].add(node)
            counts.setdefault(parent, 0)
    pending = deque(sorted(node for node, count in counts.items() if count == 0))
    while pending:
        node = pending.popleft()
        for child in sorted(children[node]):
            counts[child] -= 1
            if counts[child] == 0:
                pending.append(child)
    return {node for node, count in counts.items() if count}


def _allocations(value, component_ids):
    if value is None:
        return None, {}
    value = decode_record(canonical_bytes({"rows": value}))["rows"]
    _array(value, len(component_ids), "allocations")
    found = {}
    for row in value:
        _object(row, ("component_id", "split", "diagnostic"), "allocation")
        identifier = _sha(row["component_id"], "component_id")
        _require(identifier in component_ids and identifier not in found, "unknown, duplicate or partial component allocation")
        _require(type(row["split"]) is str and row["split"] in SPLITS, "allocation split differs")
        _boolean(row["diagnostic"], "allocation diagnostic")
        _require(row["diagnostic"] is (row["split"] == "dev"), "DEV must explicitly be diagnostic; other splits must not")
        found[identifier] = row
    return sorted(value, key=lambda row: row["component_id"]), found


def build_lineage_proposal(inventory, allocations=None):
    """Propose whole components; unknowns stay quarantined and never reviewed.

    Exposed TRAIN is permitted as a proposal. DEV is explicitly diagnostic
    only. Any exposed TEST component is quarantined. Sharing a generator file
    alone does not establish a shared derivation or merge different families.
    """
    inventory = _inventory(inventory)
    limits = bounds_profile_record(inventory["bounds_profile"])
    records = {row["route_id"]: row for row in inventory["records"]}
    parents = {row["lineage_sha256"]: row for row in inventory["parents"]}
    known_lineages = set(parents) | {row["lineage_sha256"] for row in records.values()}
    sources = {row["sha256"] for row in inventory["source_files"].values()}
    graph, issues, ancestry = _Graph(limits["max_relations"]), defaultdict(list), defaultdict(set)
    dependencies = {}
    def issue(node, code, related):
        issues[node].append({"code": code, "related": related})
    for name, row in records.items():
        node = "route:" + name
        for key, relation in (("family", "declared_family"), ("template_sha256", "shared_template"),
                              ("lineage_sha256", "same_lineage"), ("statement_sha256", "canonical_target")):
            prefix = {"template_sha256": "template", "lineage_sha256": "lineage", "statement_sha256": "statement"}.get(key, key)
            graph.join(node, prefix + ":" + row[key], relation)
        for key, prefix in (("intermediate_statement_sha256s", "statement"), ("intermediate_state_sha256s", "state")):
            for value in row[key]:
                graph.join(node, prefix + ":" + value, "intermediate_" + prefix)
        for key in ("dependency_ids", "equivalent_ids"):
            for other in row[key]:
                graph.join(node, "route:" + other, key)
                if other not in records:
                    issue(node, "unresolved_" + key, other)
        dependencies[name] = set(row["dependency_ids"])
        for parent in row["parent_lineages"]:
            graph.join(node, "lineage:" + parent, "declared_parent_lineage")
            ancestry[row["lineage_sha256"]].add(parent)
            if parent not in known_lineages:
                issue(node, "unresolved_parent_lineage", parent)
        if not row["provenance_complete"]:
            issue(node, "unresolved_route_provenance", name)
        if row["source_sha256"] not in sources:
            issue(node, "unresolved_generator_source", row["source_sha256"])
        for key in ("epoch_sha256", "authority_sha256"):
            if row[key] != inventory[key]:
                issue(node, "route_" + key + "_mismatch", name)
    for sha, row in parents.items():
        node = "lineage:" + sha
        graph.root(node)
        ancestry[sha].update(row["parent_lineages"])
        for parent in row["parent_lineages"]:
            graph.join(node, "lineage:" + parent, "parent_ancestry")
            if parent not in known_lineages:
                issue(node, "unresolved_parent_lineage", parent)
        if not row["provenance_complete"]:
            issue(node, "unresolved_parent_provenance", sha)
    for name in _cyclic_or_dependent(dependencies):
        issue("route:" + name, "cyclic_dependency", name)
    for sha in _cyclic_or_dependent(ancestry):
        issue("lineage:" + sha, "cyclic_parent_provenance", sha)
    groups, attached_parents, grouped_issues = defaultdict(list), defaultdict(list), defaultdict(list)
    grouped_lineages = defaultdict(set)
    for name in records:
        groups[graph.root("route:" + name)].append(name)
    for sha in parents:
        attached_parents[graph.root("lineage:" + sha)].append(sha)
    for node, reasons in issues.items():
        grouped_issues[graph.root(node)].extend(reasons)
    for node in graph.parents:
        if node.startswith("lineage:"):
            grouped_lineages[graph.root(node)].add(node.split(":", 1)[1])
    preliminary = []
    for root, names in sorted(groups.items()):
        binding = {"records": [canonical_sha256(records[name]) for name in names],
                   "parents": [canonical_sha256(parents[sha]) for sha in sorted(attached_parents[root])]}
        preliminary.append((canonical_sha256(binding), root, names))
    proposed, assigned = _allocations(allocations, {item[0] for item in preliminary})
    exposures = {row["exposure_id"]: row for row in inventory["exposures"]}
    exposure_sets = {
        identifier: {name: set(summary[name]) for name in
            ("covered_route_ids", "families") + _EXPOSURE_HASH_FIELDS}
        for identifier, summary in exposures.items()
    }
    for sets in exposure_sets.values():
        sets["statement_aliases"] = sets["statement_sha256s"] | sets["intermediate_statement_sha256s"]
    excluded_targets = set(inventory["exclusions"]["target_sha256s"])
    excluded_states = set(inventory["exclusions"]["intermediate_state_sha256s"])
    components, conflicts, requests = [], [], []
    for identifier, root, names in sorted(preliminary):
        rows = [records[name] for name in names]
        reasons = list(grouped_issues[root])
        if inventory["source_dirty"] or inventory["source_commit"] is None:
            reasons.append({"code": "source_not_frozen", "related": inventory["source_files_sha256"]})
        if not inventory["exclusions"]["complete"]:
            reasons.append({"code": "exclusion_coverage_unknown", "related": inventory["exclusions"]["manifest_sha256"]})
        families = {row["family"] for row in rows}
        templates = {row["template_sha256"] for row in rows}
        lineages = grouped_lineages[root]
        targets = {row["statement_sha256"] for row in rows}
        intermediate = {sha for row in rows for sha in row["intermediate_statement_sha256s"]}
        states = {sha for row in rows for sha in row["intermediate_state_sha256s"]}
        for sha in sorted((targets | intermediate) & excluded_targets):
            reasons.append({"code": "excluded_target_or_intermediate", "related": sha})
        for sha in sorted(states & excluded_states):
            reasons.append({"code": "excluded_intermediate_state", "related": sha})
        matched_exposures = []
        for requirement in inventory["exposure_requirements"]:
            exposure_id = requirement["exposure_id"]
            summary = exposures.get(exposure_id)
            if summary is None:
                reasons.append({"code": "exposure_source_missing", "related": exposure_id})
                continue
            known = exposure_sets[exposure_id]
            if not summary["complete"] or not set(names) <= known["covered_route_ids"]:
                reasons.append({"code": "exposure_coverage_unknown", "related": exposure_id})
            matches = {
                "families": sorted(families & known["families"]),
                "templates": sorted(templates & known["template_sha256s"]),
                "lineages": sorted(lineages & known["lineage_sha256s"]),
                "target_or_intermediate_statements": sorted((targets | intermediate) & known["statement_aliases"]),
                "intermediate_states": sorted(states & known["intermediate_state_sha256s"]),
            }
            if any(matches.values()):
                matched_exposures.append({"exposure_id": exposure_id, "matches": matches})
        allocation = assigned.get(identifier)
        split = allocation["split"] if allocation else "quarantine"
        if split == "test" and matched_exposures:
            reasons.append({"code": "test_component_previously_exposed", "related": identifier})
        reasons = sorted({canonical_bytes(reason): reason for reason in reasons}.values(),
                         key=lambda reason: (reason["code"], reason["related"]))
        effective = "quarantine" if reasons else split
        component = {
            "component_id": identifier, "route_ids": names, "families": sorted(families),
            "template_sha256s": sorted(templates), "parent_lineages": sorted(lineages),
            "requested_split": split, "effective_split": effective,
            "explicitly_allocated": allocation is not None,
            "diagnostic": allocation["diagnostic"] if allocation else False,
            "previously_exposed_under_declared_inventory": bool(matched_exposures),
            "exposures": matched_exposures, "reasons": reasons,
            "status": "blocked" if reasons else "not-reviewed", "review_status": "not-reviewed",
        }
        components.append(component)
        conflicts.extend(dict(reason, component_id=identifier) for reason in reasons)
        requests.append({"component_id": identifier, "requested_split": split, "effective_split": effective,
                         "diagnostic": component["diagnostic"], "status": "not-reviewed",
                         "required": ["source_and_parent_provenance", "complete_declared_exposure_inventory",
                                      "whole_component_allocation", "target_and_intermediate_exclusions",
                                      "independent_test_ownership_is_a_separate_gate"]})
    relations = sorted(graph.edges)
    result = {"schema": PROPOSAL_SCHEMA, "inventory": inventory,
              "inventory_sha256": canonical_sha256(inventory), "allocations": proposed,
              "components": components, "relations": relations, "relations_sha256": canonical_sha256(relations),
              "conflicts": conflicts, "review_requests": requests,
              "counts": {"routes": len(records), "components": len(components),
                         "blocked_components": sum(row["status"] == "blocked" for row in components),
                         "effective_routes_by_split": {split: sum(len(row["route_ids"]) for row in components
                                                              if row["effective_split"] == split) for split in sorted(SPLITS)},
                         "reviewed_components": 0, "approved_model_rows": 0},
              "status": "blocked" if conflicts else "not-reviewed", "claims": _claims(),
              "resource_bounds": limits}
    result["proposal_sha256"] = canonical_sha256(result)
    _require(len(canonical_bytes(result)) <= limits["max_result_bytes"], "profile proposal byte bound exceeded")
    return result


def _proposal(proposal, expected_sha256):
    _sha(expected_sha256, "external canonical proposal SHA")
    canonical_bytes(proposal)
    _object(proposal, _PROPOSAL_FIELDS, "proposal")
    _require(proposal["proposal_sha256"] == expected_sha256 and expected_sha256 == canonical_sha256(
        {key: value for key, value in proposal.items() if key != "proposal_sha256"}), "proposal external seal differs")
    expected = build_lineage_proposal(proposal["inventory"], proposal["allocations"])
    _require(canonical_bytes(proposal) == canonical_bytes(expected), "proposal derivation, counts or claims differ")
    return expected


def audit_lineage(proposal, *, expected_proposal_sha256):
    """Recompute the declared graph and every exclusion; never infer review."""
    proposal = _proposal(proposal, expected_proposal_sha256)
    result = {"schema": AUDIT_SCHEMA, "proposal_sha256": expected_proposal_sha256,
              "inventory_sha256": proposal["inventory_sha256"], "status": proposal["status"],
              "components": proposal["components"], "conflicts": proposal["conflicts"],
              "counts": proposal["counts"], "review_requests": proposal["review_requests"],
              "claims": _claims(), "resource_bounds": proposal["resource_bounds"]}
    result["audit_sha256"] = canonical_sha256(result)
    _require(len(canonical_bytes(result)) <= proposal["resource_bounds"]["max_result_bytes"], "profile audit byte bound exceeded")
    return result


def validate_review_record(review, *, proposal, expected_proposal_sha256,
                           expected_review_sha256, required_scope=None):
    """Validate an externally supplied assertion, not an independent reviewer.

    An accept decision may cover exposed TRAIN or explicit diagnostic DEV.
    It cannot release a blocked component from quarantine, remove exclusions,
    assert unseen data, seal TEST, authorize a model run or complete H0/H1/H5.
    """
    proposal = _proposal(proposal, expected_proposal_sha256)
    canonical_bytes(review)
    _object(review, ("schema", "proposal_sha256", "scope", "decision", "reviewer_reference", "reviewed_at",
                     "asserted_human_review", "acknowledgments", "review_sha256"), "external review")
    _sha(expected_review_sha256, "external canonical review SHA")
    _require(review["schema"] == REVIEW_SCHEMA and review["proposal_sha256"] == expected_proposal_sha256
             and review["review_sha256"] == expected_review_sha256
             and expected_review_sha256 == canonical_sha256({key: value for key, value in review.items() if key != "review_sha256"}),
             "external review does not bind this exact proposal")
    _require(review["asserted_human_review"] is True, "review must explicitly assert later human input")
    _object(review["acknowledgments"], ACKNOWLEDGMENTS, "review acknowledgments")
    _require(all(value is True for value in review["acknowledgments"].values()), "review acknowledgments must be explicit strict true")
    _require(type(review["decision"]) is str and review["decision"] in ("accept", "reject"), "review decision differs")
    reference = review["reviewer_reference"]
    _require(type(reference) is str and 1 <= len(reference) <= 256 and reference.strip() == reference
             and not any(ord(char) < 32 or ord(char) == 127 for char in reference), "bounded nonempty reviewer reference required")
    stamp = review["reviewed_at"]
    _require(type(stamp) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", stamp),
             "review time must be an explicit UTC timestamp")
    try:
        datetime.datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError:
        raise ScalingLineageError("invalid review calendar time") from None
    components = {row["component_id"]: row for row in proposal["components"]}
    scope, _ = _allocations(review["scope"], set(components))
    _require(bool(scope), "review scope must explicitly name whole components")
    if required_scope is not None:
        expected_scope, _ = _allocations(required_scope, set(components))
        _require(scope == expected_scope, "review scope differs from the consumer's explicit required scope")
    for allocation in scope:
        component = components[allocation["component_id"]]
        _require(component["explicitly_allocated"] and allocation["split"] == component["requested_split"]
                 and allocation["diagnostic"] == component["diagnostic"], "review changes the proposed whole-component allocation")
        if review["decision"] == "accept":
            _require(allocation["split"] == "quarantine" or component["effective_split"] == allocation["split"],
                     "review cannot override unresolved, exposed TEST or excluded components")
    result = {"schema": REVIEW_VALIDATION_SCHEMA, "status": "human-assertion-record-validated",
              "proposal_sha256": expected_proposal_sha256, "review_sha256": expected_review_sha256,
              "decision": review["decision"], "scope": scope, "reviewer_reference": reference,
              "reviewed_at": stamp, "review_provenance": "externally anchored human assertion; not cryptographic identity or independent ownership proof",
              "claims": _claims()}
    result["validation_sha256"] = canonical_sha256(result)
    return result
