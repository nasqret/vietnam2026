"""Explicit human-assertion gate between frontier candidates and post-training.

The five native source files are copied unchanged. The model-facing projection
must preserve the candidate's exact first-occurrence state/action deduplication;
raw evidence rows are not advertised as training examples. A sibling admission
record binds both counts, the externally anchored candidate, exact review
scope, exclusions and proof-source bytes.
Imports are lazy: missing or mismatched review fails before native replay.

This module never creates a human review, starts a subprocess, loads a model,
grants GPU permission, or changes the original candidate. Call preparation
inside an operator-owned bounded CPU worker. Human provenance is an assertion,
not cryptographic identity, independent test ownership or reference readiness.
"""

from __future__ import annotations

from collections import Counter
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from typing import TYPE_CHECKING

from hydra_training_v5.peano_hydra import scaling_lineage as lineage

if TYPE_CHECKING:
    from hydra_training_v5.peano_hydra.posttrain import VerifiedSource


ROOT = Path(__file__).absolute().parents[2]
ADMISSION_SCHEMA = "peano-hydra-frontier-model-data-admission-v1"
IDENTITY_SCHEMA = "peano-hydra-frontier-admission-identity-v1"
PREPARATION_RESULT_SCHEMA = "peano-hydra-frontier-admitted-preparation-v1"
CANDIDATE_SCHEMA = "peano-hydra-frontier-candidate-bundle-v1"
SOURCE_SCHEMA = "peano-hydra-native-frontier-curriculum-source-v1"
REFERENCE_EXAMPLE_SCHEMA = "peano-hydra-frontier-posttrain-reference-v1"
SOURCE_FILES = frozenset(("epoch.json", "manifest.json", "sft.jsonl", "preferences.jsonl", "discovery.jsonl"))
METADATA_FILES = frozenset(("candidate-readiness.json", "lineage-proposal.json", "lineage-review.json", "native-summary.json"))
PREPARATION_FILES = frozenset(("config.toml", "manifest.json", "train.jsonl", "dev.jsonl", "quarantine.jsonl", "preferences.jsonl", "discovery.jsonl"))
MAX_METADATA_BYTES = 16 * 1024**2
MAX_SOURCE_BYTES = 64 * 1024**2
MAX_PREPARATION_BYTES = 64 * 1024**2
MAX_ROW_BYTES = 256 * 1024
MAX_RESULT_BYTES = 64 * 1024
MAX_ROUTES = 1152
MAX_ROWS = 16384
PROJECTION_POLICY = "first-exact-epoch-environment-lineage-state-action-v1"
_CANDIDATE_FILES = frozenset((
    "native-summary.json", "source-build-process.json", "source-verify-process.json",
    "lineage-proposal.json", "lineage-audit.json", "shard-structural-check.json",
    "pilot-plan.json", "evaluation-plan.json", "review-request.json",
))
_FALSE_CANDIDATE_CLAIMS = frozenset((
    "independent_process_per_route", "human_review_passed", "reference_readiness_passed",
    "training_preparation_created", "token_preflight_passed", "model_trained",
    "training_authorized", "transfer_authorized", "sealed_benchmark", "research_claim_eligible",
))
_CANDIDATE_FIELDS = frozenset((
    "schema", "profile", "status", "source_manifest_sha256", "shard_manifest_sha256",
    "lineage_proposal_sha256", "files", "native_verified_routes", "native_verified_transitions",
    "recovery_attempts", "projected_unique_rows", "duplicate_state_actions_removed", "split_rows",
    "native_source_to_shard_join_checked", "separate_process_source_reverification", "lineage_status",
    "lineage_counts", "baseline_exposure_source", "source_files", "gpu_jobs_started", "bundle_sha256",
)) | _FALSE_CANDIDATE_CLAIMS
_SUMMARY_FIELDS = frozenset((
    "source_manifest_sha256", "source_files", "epoch_sha256", "authority_sha256",
    "source_plan", "lineage_records", "raw_split_rows", "native_verified_routes",
    "native_verified_transitions", "recovery_attempts", "model_generation_performed",
    "training_authorized", "independent_process_per_route",
))
_SHA = re.compile(r"[0-9a-f]{64}\Z")
_RUN_ID = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}\Z")
_ADMISSION_FIELDS = frozenset((
    "schema", "status", "run_id", "source_directory", "candidate_readiness_sha256",
    "candidate_bundle_sha256", "source_manifest_sha256", "source_files", "proposal_sha256",
    "review_sha256", "review_validation_sha256", "scope", "bindings", "files", "counts",
    "human_review_asserted", "human_identity_verified", "model_data_admitted",
    "model_training_authorized", "gpu_execution_authorized", "token_budget_verified",
    "reference_readiness_passed", "research_claim_eligible", "sealed_benchmark",
    "unseen_holdout_claim_eligible", "admission_sha256",
))


class ScalingAdmissionError(ValueError):
    """Candidate, review, native source or preparation lost its exact binding."""


def _require(condition, message):
    if not condition:
        raise ScalingAdmissionError(message)


def _sha(value, label):
    _require(type(value) is str and _SHA.fullmatch(value) is not None, label + " requires lowercase SHA-256")
    return value


def _canonical(value):
    raw = lineage.canonical_bytes(value)
    _require(len(raw) <= MAX_METADATA_BYTES, "admission metadata exceeds its byte bound")
    return raw


def _digest(value):
    return hashlib.sha256(_canonical(value)).hexdigest()


def _decode(raw):
    _require(type(raw) is bytes and 0 < len(raw) <= MAX_METADATA_BYTES, "bounded admission JSON required")
    result = lineage.decode_record(raw)
    _require(type(result) is dict, "admission metadata must be a JSON object")
    return result


def _descriptor(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def _absolute(value):
    _require(type(value) in (str, type(Path("."))), "location must be an explicit string or Path")
    path = Path(value).absolute()
    _require(".." not in path.parts and 1 < len(path.parts) <= 64
             and len(str(path).encode()) <= 4096
             and not any(ord(char) < 32 or ord(char) == 127 for char in str(path)), "noncanonical admission path")
    return path


def _tree_type():
    from hydra_training_v5.peano_hydra.origin_bridge import _Tree
    return _Tree


def _workflow():
    from hydra_training_v5.peano_hydra import scaling_workflow
    return scaling_workflow


def _frontier():
    from hydra_training_v5.peano_hydra import frontier_curriculum
    return frontier_curriculum


def _posttrain():
    from hydra_training_v5.peano_hydra import posttrain
    return posttrain


def _read(tree, name, maximum=MAX_METADATA_BYTES):
    raw = tree.read(name, maximum)
    tree.assert_unchanged()
    return raw


def _closed_directory(tree, relative, names):
    fd = tree.directory(relative)
    expected = set(names)
    entries = os.listdir(fd)
    _require(len(entries) == len(expected) and set(entries) == expected, "directory is not the exact admitted inventory")
    for name in entries:
        info = os.stat(name, dir_fd=fd, follow_symlinks=False)
        _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1, "admitted inventory contains a link or special file")


def _file_map(value, expected_names, label):
    _require(type(value) is dict and set(value) == set(expected_names), label + " file inventory differs")
    total = 0
    for name, descriptor in value.items():
        _require(type(descriptor) is dict and set(descriptor) == {"bytes", "sha256"}, label + " file identity differs")
        _require(type(descriptor["bytes"]) is int and 0 <= descriptor["bytes"] <= MAX_SOURCE_BYTES,
                 label + " file size differs")
        _sha(descriptor["sha256"], label + " file hash")
        total += descriptor["bytes"]
    _require(total <= MAX_SOURCE_BYTES, label + " complete byte bound exceeded")


def _source_files(tree, expected):
    _file_map(expected, SOURCE_FILES, "native source")
    _closed_directory(tree, "source", SOURCE_FILES)
    for name in sorted(SOURCE_FILES):
        actual, _ = tree.fingerprint("source/" + name, maximum=MAX_SOURCE_BYTES, retain=False)
        _require({key: actual[key] for key in ("bytes", "sha256")} == expected[name], "native source differs from candidate bytes")
    tree.assert_unchanged()


def _split_counts(value, label):
    _require(type(value) is dict and not set(value) - {"train", "dev", "test", "quarantine"}, label + " splits differ")
    _require(all(type(count) is int and 0 <= count <= MAX_ROWS for count in value.values()), label + " counts differ")
    _require(sum(value.values()) <= MAX_ROWS, label + " row count exceeds bound")
    return {name: value.get(name, 0) for name in ("train", "dev", "test", "quarantine")}


def _scope_and_bindings(ready, summary, proposal):
    """Join all native routes to whole reviewed model-facing components."""
    _require(type(ready) is type(summary) is type(proposal) is dict and set(ready) == _CANDIDATE_FIELDS,
             "candidate readiness schema has unknown or missing fields")
    _require(set(summary) == _SUMMARY_FIELDS
             and all(summary[name] is False for name in ("model_generation_performed", "training_authorized",
                                                         "independent_process_per_route")),
             "candidate native summary schema or claim boundary differs")
    _require(ready.get("schema") == CANDIDATE_SCHEMA and ready.get("status") == "candidate-verified-review-pending"
             and ready.get("profile") in ("smoke", "pilot")
             and ready.get("native_source_to_shard_join_checked") is True
             and ready.get("separate_process_source_reverification") is True,
             "input is not a review-pending frontier candidate")
    _require(_sha(ready.get("bundle_sha256"), "candidate semantic hash") == _digest(
        {key: value for key, value in ready.items() if key != "bundle_sha256"}), "candidate semantic hash differs")
    for field in _FALSE_CANDIDATE_CLAIMS:
        _require(ready.get(field) is False, "candidate changed its unapproved claim boundary")
    _require(type(ready.get("gpu_jobs_started")) is int and ready["gpu_jobs_started"] == 0,
             "candidate cannot carry a GPU execution claim")
    _file_map(ready.get("files"), _CANDIDATE_FILES, "candidate metadata")
    for field, maximum in (("native_verified_routes", MAX_ROUTES), ("native_verified_transitions", MAX_ROWS),
                           ("recovery_attempts", MAX_ROUTES), ("projected_unique_rows", MAX_ROWS),
                           ("duplicate_state_actions_removed", MAX_ROWS)):
        _require(type(ready.get(field)) is int and 0 <= ready[field] <= maximum,
                 "candidate count is not a bounded integer: " + field)
        if field in ("native_verified_routes", "native_verified_transitions", "recovery_attempts"):
            _require(type(summary.get(field)) is int and summary[field] == ready[field],
                     "native summary count differs: " + field)
    _require(ready.get("source_manifest_sha256") == summary.get("source_manifest_sha256"), "candidate native manifest anchor differs")
    _file_map(summary.get("source_files"), SOURCE_FILES, "candidate source")
    _require(summary["source_files"]["manifest.json"]["sha256"] == ready["source_manifest_sha256"],
             "source manifest descriptor differs")
    lineage.audit_lineage(proposal, expected_proposal_sha256=ready["lineage_proposal_sha256"])
    _require(_canonical(ready["lineage_counts"]) == _canonical(proposal["counts"])
             and ready["lineage_status"] == proposal["status"], "candidate lineage summary differs")
    inventory = proposal["inventory"]
    _require(inventory["source_files"] == ready.get("source_files"), "lineage execution source inventory differs")
    _require(inventory["epoch_sha256"] == summary.get("epoch_sha256")
             and inventory["authority_sha256"] == summary.get("authority_sha256"), "lineage epoch or authority differs")
    plan = summary.get("source_plan")
    _require(type(plan) is dict and _sha(plan.get("plan_sha256"), "native source plan") == _digest(
        {key: value for key, value in plan.items() if key != "plan_sha256"}), "native source plan semantic hash differs")
    _require(plan.get("epoch_sha256") == inventory["epoch_sha256"]
             and _digest(plan.get("authority")) == inventory["authority_sha256"], "native plan authority/epoch differs")
    routes = plan.get("routes")
    _require(type(routes) is list and 1 <= len(routes) <= MAX_ROUTES, "native plan route inventory exceeds bound")
    by_name = {}
    family_rows = plan.get("families")
    _require(type(family_rows) is list and 1 <= len(family_rows) <= MAX_ROUTES
             and all(type(row) is dict and type(row.get("id")) is str for row in family_rows),
             "native family records are malformed")
    families = {row["id"]: row for row in family_rows}
    _require(len(families) == len(family_rows), "native family records are ambiguous")
    for route in routes:
        _require(type(route) is dict and type(route.get("name")) is str and route["name"] not in by_name,
                 "native route identities are ambiguous")
        _require(route.get("split") in ("train", "dev"), "TEST/quarantine source routes cannot enter this trainer")
        _require(type(route.get("family")) is str and route["family"] in families
                 and type(route.get("generator_seed")) is int and route["generator_seed"] >= 0,
                 "native route family/seed differs")
        _sha(route.get("lineage_sha256"), "native route lineage")
        _require(type(route.get("statement")) is str and hashlib.sha256(route["statement"].encode()).hexdigest()
                 == route.get("statement_sha256"), "route statement hash differs")
        _require(_sha(route.get("route_sha256"), "route semantic hash") == _digest(
            {key: value for key, value in route.items() if key != "route_sha256"}), "native route semantic hash differs")
        by_name[route["name"]] = route
    records = {row["route_id"]: row for row in inventory["records"]}
    summary_rows = summary.get("lineage_records")
    _require(type(summary_rows) is list and len(summary_rows) == len(by_name)
             and all(type(row) is dict and set(row) == {"route", "intermediate_statement_sha256s", "intermediate_state_sha256s"}
                     and type(row.get("route")) is dict
                     and type(row["route"].get("name")) is str for row in summary_rows),
             "native route summary is malformed")
    summaries = {row["route"]["name"]: row for row in summary_rows}
    _require(set(records) == set(summaries) == set(by_name)
             and len(summary["lineage_records"]) == len(by_name), "native/lineage route partition differs")
    generator = inventory["source_files"].get("training/peano_hydra/frontier_curriculum.py")
    _require(type(generator) is dict, "lineage lacks its exact frontier generator")
    for name, route in by_name.items():
        row, evidence = records[name], summaries[name]
        _require(evidence["route"] == route and row["family"] == route["family"]
                 and row["statement_sha256"] == route["statement_sha256"]
                 and row["lineage_sha256"] == route["lineage_sha256"]
                 and row["seed"] == route["generator_seed"]
                 and row["source_sha256"] == generator["sha256"]
                 and row["template_sha256"] == _digest({"generator_sha256": generator["sha256"],
                                                        "family": families[route["family"]]})
                 and row["intermediate_statement_sha256s"] == evidence["intermediate_statement_sha256s"]
                 and row["intermediate_state_sha256s"] == evidence["intermediate_state_sha256s"],
                 "lineage route/template/intermediate evidence changed from native summary")
    excluded = plan.get("excluded_targets")
    _require(type(excluded) is list and 1 <= len(excluded) <= 128
             and all(type(row) is dict and type(row.get("statement")) is str for row in excluded),
             "native comparison exclusions are missing")
    targets = sorted({hashlib.sha256(row["statement"].encode()).hexdigest() for row in excluded})
    exclusions = inventory["exclusions"]
    _require(exclusions["complete"] is True and exclusions["manifest_sha256"] == _digest(excluded)
             and set(targets) <= set(exclusions["target_sha256s"])
             and plan.get("excluded_targets_sha256") == _digest(excluded), "native mandatory exclusions were changed or omitted")
    allocations = {row["component_id"]: row for row in proposal["allocations"] or []}
    scope, partition = [], []
    for component in proposal["components"]:
        names = component["route_ids"]
        partition.extend(names)
        selected = allocations.get(component["component_id"])
        _require(selected is not None and component["explicitly_allocated"] is True
                 and component["status"] == "not-reviewed" and not component["reasons"]
                 and selected["split"] in ("train", "dev")
                 and component["requested_split"] == component["effective_split"] == selected["split"]
                 and selected["diagnostic"] is (selected["split"] == "dev")
                 and all(by_name[name]["split"] == selected["split"] for name in names),
                 "all source components need explicit unchanged TRAIN/diagnostic-DEV allocation; quarantine/unknown/TEST cannot enter training")
        scope.append(dict(selected))
    _require(sorted(partition) == sorted(by_name), "component scope must cover every model-facing native route exactly once")
    raw_counts = _split_counts(summary.get("raw_split_rows"), "native source")
    projected_counts = _split_counts(ready.get("split_rows"), "candidate projection")
    _require(raw_counts["train"] > 0 and raw_counts["dev"] > 0 and raw_counts["test"] == raw_counts["quarantine"] == 0,
             "native source must retain nonempty TRAIN and diagnostic DEV only")
    _require(projected_counts["train"] > 0 and projected_counts["dev"] > 0,
             "model-facing candidate projection must retain nonempty TRAIN and diagnostic DEV")
    _require(type(summary.get("native_verified_transitions")) is int
             and summary["native_verified_transitions"] == sum(raw_counts.values()) == ready.get("native_verified_transitions")
             and type(ready.get("projected_unique_rows")) is int
             and ready["projected_unique_rows"] == sum(projected_counts.values())
             and all(projected_counts[key] <= raw_counts[key] for key in raw_counts)
             and ready.get("duplicate_state_actions_removed") == sum(raw_counts.values()) - sum(projected_counts.values()),
             "raw native and projected candidate row counts do not join")
    _require(type(summary.get("native_verified_routes")) is int
             and summary["native_verified_routes"] == len(routes) == ready.get("native_verified_routes")
             and type(plan.get("route_count")) is int and plan["route_count"] == len(routes)
             and _split_counts(plan.get("split_transition_counts"), "native plan") == raw_counts,
             "native plan route/role counts differ")
    bindings = {"epoch_sha256": inventory["epoch_sha256"], "authority_sha256": inventory["authority_sha256"],
                "inventory_sha256": proposal["inventory_sha256"], "source_plan_sha256": plan["plan_sha256"],
                "execution_source_files_sha256": _digest(ready["source_files"]),
                "exclusions_sha256": _digest(exclusions)}
    counts = {"native_routes": len(routes), "native_transition_rows": sum(raw_counts.values()),
              "native_source_split_rows": raw_counts, "candidate_projected_rows": sum(projected_counts.values()),
              "candidate_projected_split_rows": projected_counts,
              "duplicate_transitions_removed": ready["duplicate_state_actions_removed"],
              "duplicate_split_rows": {key: raw_counts[key] - projected_counts[key] for key in ("train", "dev")},
              "row_policy": PROJECTION_POLICY, "complete_native_source_preserved": True}
    return sorted(scope, key=lambda row: row["component_id"]), bindings, counts


def _make_admission(metadata, run_id, expected_readiness_sha256, expected_review_sha256):
    _require(type(run_id) is str and _RUN_ID.fullmatch(run_id), "explicit bounded run_id required")
    _sha(expected_readiness_sha256, "external raw candidate readiness SHA")
    _sha(expected_review_sha256, "external canonical review SHA")
    _require(set(metadata) == METADATA_FILES, "admission metadata inventory differs")
    _require(hashlib.sha256(metadata["candidate-readiness.json"]).hexdigest() == expected_readiness_sha256,
             "external raw candidate readiness anchor differs")
    ready = _decode(metadata["candidate-readiness.json"])
    proposal = _decode(metadata["lineage-proposal.json"])
    summary = _decode(metadata["native-summary.json"])
    review = _decode(metadata["lineage-review.json"])
    scope, bindings, counts = _scope_and_bindings(ready, summary, proposal)
    for name in ("lineage-proposal.json", "native-summary.json"):
        _require(ready.get("files", {}).get(name) == _descriptor(metadata[name]), "candidate metadata raw file anchor differs")
    reviewed = lineage.validate_review_record(review, proposal=proposal,
        expected_proposal_sha256=ready["lineage_proposal_sha256"],
        expected_review_sha256=expected_review_sha256, required_scope=scope)
    _require(reviewed["decision"] == "accept", "explicit accepted human allocation assertion is required")
    result = {"schema": ADMISSION_SCHEMA, "status": "review-accepted-native-source", "run_id": run_id,
              "source_directory": "source", "candidate_readiness_sha256": expected_readiness_sha256,
              "candidate_bundle_sha256": ready["bundle_sha256"],
              "source_manifest_sha256": ready["source_manifest_sha256"], "source_files": summary["source_files"],
              "proposal_sha256": ready["lineage_proposal_sha256"], "review_sha256": expected_review_sha256,
              "review_validation_sha256": reviewed["validation_sha256"], "scope": scope,
              "bindings": bindings, "files": {name: _descriptor(metadata[name]) for name in sorted(metadata)},
              "counts": counts, "human_review_asserted": True, "human_identity_verified": False,
              "model_data_admitted": True, "model_training_authorized": False, "gpu_execution_authorized": False,
              "token_budget_verified": False, "reference_readiness_passed": False,
              "research_claim_eligible": False, "sealed_benchmark": False, "unseen_holdout_claim_eligible": False}
    result["admission_sha256"] = _digest(result)
    return result, summary


def _admitted_gate(tree):
    metadata = {name: _read(tree, name) for name in sorted(METADATA_FILES)}
    raw = _read(tree, "training-admission.json")
    record = _decode(raw)
    _require(set(record) == _ADMISSION_FIELDS, "training admission schema has unknown or missing fields")
    expected, summary = _make_admission(metadata, record["run_id"], record["candidate_readiness_sha256"], record["review_sha256"])
    _require(_canonical(record) == _canonical(expected), "training admission differs from its exact review/source derivation")
    _source_files(tree, record["source_files"])
    return record, summary, hashlib.sha256(raw).hexdigest()


def _identity(record, raw_sha):
    return {"schema": IDENTITY_SCHEMA, "admission_file_sha256": raw_sha,
            "admission_sha256": record["admission_sha256"], "candidate_readiness_sha256": record["candidate_readiness_sha256"],
            "proposal_sha256": record["proposal_sha256"], "review_sha256": record["review_sha256"],
            "source_manifest_sha256": record["source_manifest_sha256"], "scope_sha256": _digest(record["scope"]),
            "bindings": record["bindings"], "counts": record["counts"],
            "model_training_authorized": False, "gpu_execution_authorized": False}


def admission_identity(source_directory):
    """Metadata/bytes-only identity for the trainer's curriculum-identity hash."""
    source = _absolute(source_directory)
    _require(source.name == "source", "admitted native source must be the fixed source/ child")
    with _tree_type()(source.parent) as tree:
        record, _, raw_sha = _admitted_gate(tree)
        tree.assert_unchanged()
        return _identity(record, raw_sha)


def _row_sha(row):
    # Trusted native rows can contain lossless prompts longer than the lineage
    # metadata string bound. Hash their canonical transport, not display text.
    raw = json.dumps(row, sort_keys=True, ensure_ascii=False, allow_nan=False,
                     separators=(",", ":")).encode("utf-8")
    _require(len(raw) <= MAX_ROW_BYTES, "native transition exceeds the candidate row bound")
    return hashlib.sha256(raw).hexdigest()


def _native_projection(source, record):
    rows = source.curriculum.transitions
    _require(type(rows) in (tuple, list) and 0 < len(rows) <= MAX_ROWS, "native transition inventory exceeds bound")
    first, duplicates, seen = {"train": [], "dev": []}, {"train": 0, "dev": 0}, {}
    for row in rows:
        _require(type(row) is dict and row.get("split") in ("train", "dev"), "native transition escaped reviewed splits")
        split = row["split"]
        identity = _digest([row["epoch_sha256"], row["environment_sha256"],
                            row["lineage_sha256"], row["state_sha256"], row["action"]])
        if identity in seen:
            _require(seen[identity] == split, "same state/action identity crosses model-facing splits")
            duplicates[split] += 1
        else:
            seen[identity] = split
            first[split].append(_row_sha(row))
    counts = record["counts"]
    _require(len(rows) == counts["native_transition_rows"]
             and duplicates == counts["duplicate_split_rows"]
             and sum(duplicates.values()) == counts["duplicate_transitions_removed"]
             and all(len(first[split]) == counts["candidate_projected_split_rows"][split] for split in first),
             "fresh native first-occurrence projection differs from the candidate shards")
    return first


def _source_projection(record):
    counts = record["counts"]
    return {"policy": PROJECTION_POLICY, "raw_source_transitions": counts["native_transition_rows"],
            "model_facing_transitions": counts["candidate_projected_rows"], "quarantined_transitions": 0,
            "duplicate_transitions_removed": counts["duplicate_transitions_removed"],
            "duplicate_split_rows": counts["duplicate_split_rows"], "complete_native_source_preserved": True}


def _verify_native(source_directory, tree, record, summary):
    source = _frontier().verify_frontier_source(source_directory)
    _require(source.directory == source_directory and source.manifest.get("schema") == SOURCE_SCHEMA,
             "native verifier returned another source/profile")
    _require(type(source.payloads) is dict and set(source.payloads) == SOURCE_FILES
             and all(type(raw) is bytes for raw in source.payloads.values()), "native verifier returned an incomplete source")
    _require({name: _descriptor(raw) for name, raw in source.payloads.items()} == record["source_files"],
             "fresh native source differs from original candidate raw bytes")
    _require(_canonical(_workflow()._source_summary(source)) == _canonical(summary),
             "fresh native route/trace/role summary differs from the candidate")
    actual = _split_counts(dict(Counter(row["split"] for row in source.curriculum.transitions)), "replayed source")
    _require(actual == record["counts"]["native_source_split_rows"]
             and source.epoch.epoch_sha256 == record["bindings"]["epoch_sha256"]
             and _digest(source.manifest["authority"]) == record["bindings"]["authority_sha256"],
             "fresh native role counts/epoch/authority differ")
    _native_projection(source, record)
    _source_files(tree, record["source_files"])
    tree.assert_unchanged()
    return source


def verify_admitted_frontier_source(source_directory) -> VerifiedSource:
    """Mandatory sibling gate followed by direct fresh native verification."""
    source = _absolute(source_directory)
    _require(source.name == "source", "admitted native source must be the fixed source/ child")
    with _tree_type()(source.parent) as tree:
        record, summary, _ = _admitted_gate(tree)
        verified = _verify_native(source, tree, record, summary)
        tree.assert_unchanged()
        return verified


def _protected():
    return tuple(ROOT / name for name in ("training", "scripts", "slurm", "docs", "book", "peano-lab", "artifacts", ".git"))


def _guard_destination(path, parent_tree, protected):
    parent_tree.assert_unchanged()
    _require(path.parent == parent_tree.root, "output parent binding differs")
    try:
        os.stat(path.name, dir_fd=parent_tree.directory(), follow_symlinks=False)
    except FileNotFoundError:
        pass
    else:
        raise ScalingAdmissionError("output directory must be fresh; no overwrite or implicit resume")
    ancestors = {(os.fstat(fd).st_dev, os.fstat(fd).st_ino) for fd in parent_tree._fds}
    for root, tree in protected:
        _require(path != root and root not in path.parents, "output is inside a protected input")
        if tree is not None:
            tree.assert_unchanged()
            info = os.fstat(tree.directory())
            _require((info.st_dev, info.st_ino) not in ancestors, "output physically aliases a protected input")


def _write(tree, relative, raw, maximum):
    _require(type(raw) is bytes and len(raw) <= maximum, "publication payload exceeds its byte bound")
    tree.assert_unchanged()
    parent, _, name = relative.rpartition("/")
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=tree.directory(parent))
    try:
        view = memoryview(raw)
        while view:
            written = os.write(fd, view)
            _require(written > 0, "short admission publication write")
            view = view[written:]
        os.fsync(fd)
    finally:
        os.close(fd)
    os.fsync(tree.directory(parent))
    actual, _ = tree.fingerprint(relative, maximum=maximum)
    _require({key: actual[key] for key in ("bytes", "sha256")} == _descriptor(raw), "published admission bytes differ")
    tree.assert_unchanged()


def _mkdir(tree, name):
    tree.assert_unchanged()
    os.mkdir(name, 0o700, dir_fd=tree.directory())
    os.fsync(tree.directory())
    tree.directory(name)
    tree.assert_unchanged()


def prepare_admitted_pilot(candidate_bundle, expected_readiness_sha256, review_file,
                           expected_review_sha256, output_directory, run_id):
    """Publish a separate reviewed preparation in one owned CPU process.

    The caller's external readiness hash is RAW bytes; the external review
    hash is the canonical review seal. No candidate bytes are edited. A failed
    output is retained for diagnosis, without a successful preflight record.
    The exact evidence copy is metadata-authenticated first. The unchanged
    trainer performs fresh native verification BEFORE preparation publication;
    its unchanged preflight repeats native verification after publication.
    """
    candidate, review_path, output = map(_absolute, (candidate_bundle, review_file, output_directory))
    _sha(expected_readiness_sha256, "external raw readiness SHA")
    _sha(expected_review_sha256, "external canonical review SHA")
    _require(type(run_id) is str and _RUN_ID.fullmatch(run_id), "explicit bounded run_id required")
    Tree = _tree_type()
    with ExitStack() as stack:
        original = stack.enter_context(Tree(candidate))
        review_tree = stack.enter_context(Tree(review_path.parent))
        parent = stack.enter_context(Tree(output.parent))
        protected = [(candidate, original)]
        for root in _protected():
            if root.name == ".git" and root.is_file() and not root.is_symlink():
                # A linked worktree has a regular Git pointer, not a directory.
                # The fresh-output requirement already forbids replacing it.
                protected.append((root, None))
            elif root.exists() or root.is_symlink():
                protected.append((root, stack.enter_context(Tree(root))))
            else:
                protected.append((root, None))
        _guard_destination(output, parent, protected)
        metadata = {"candidate-readiness.json": _read(original, "readiness.json"),
                    "lineage-proposal.json": _read(original, "lineage-proposal.json"),
                    "native-summary.json": _read(original, "native-summary.json"),
                    "lineage-review.json": _read(review_tree, review_path.name)}
        admission, summary = _make_admission(metadata, run_id, expected_readiness_sha256, expected_review_sha256)
        ready = _decode(metadata["candidate-readiness.json"])
        baseline = ready.get("baseline_exposure_source")
        if baseline is not None:
            _require(type(baseline) is dict and type(baseline.get("directory")) is str, "baseline exposure location differs")
            baseline_root = _absolute(baseline["directory"])
            protected.append((baseline_root, stack.enter_context(Tree(baseline_root))))
            _guard_destination(output, parent, protected)
        checked = _workflow().verify_bundle(candidate, expected_readiness_sha256=expected_readiness_sha256, replay=False)
        _require(checked.get("status") == "metadata-checked-native-replay-not-performed"
                 and checked.get("readiness_raw_sha256") == expected_readiness_sha256
                 and checked.get("native_replay_performed") is False, "candidate metadata/projection verification failed")
        original.assert_unchanged()
        review_tree.assert_unchanged()
        _source_files(original, admission["source_files"])
        # Copy only the five externally bound evidence files. The original
        # trainer below performs the first fresh replay, before any model-facing
        # train/dev file is published. Do not add a third redundant full replay.
        source_payloads = {name: _read(original, "source/" + name, admission["source_files"][name]["bytes"])
                           for name in sorted(SOURCE_FILES)}
        _require({name: _descriptor(value) for name, value in source_payloads.items()} == admission["source_files"],
                 "source copy changed from the candidate raw anchors")
        _guard_destination(output, parent, protected)
        review_tree.assert_unchanged()
        os.mkdir(output.name, 0o700, dir_fd=parent.directory())
        os.fsync(parent.directory())
        created = os.stat(output.name, dir_fd=parent.directory(), follow_symlinks=False)
        parent.assert_unchanged()
        published = stack.enter_context(Tree(output))
        opened = os.fstat(published.directory())
        _require(stat.S_ISDIR(created.st_mode) and (created.st_dev, created.st_ino) == (opened.st_dev, opened.st_ino),
                 "fresh output directory identity changed before publication")
        parent.assert_unchanged()
        original.assert_unchanged()
        review_tree.assert_unchanged()
        for _, tree in protected:
            if tree is not None:
                tree.assert_unchanged()
        _mkdir(published, "source")
        for name in sorted(SOURCE_FILES):
            _write(published, "source/" + name, source_payloads[name], MAX_SOURCE_BYTES)
        for name in sorted(METADATA_FILES):
            _write(published, name, metadata[name], MAX_METADATA_BYTES)
        _write(published, "training-admission.json", _canonical(admission) + b"\n", MAX_METADATA_BYTES)
        original.assert_unchanged()
        review_tree.assert_unchanged()
        del source_payloads
        trainer = _posttrain()
        prepared = trainer.prepare_posttraining(output / "source", output / "preparation", run_id=run_id)
        _require(prepared.output_directory == output / "preparation" and prepared.source.directory == output / "source",
                 "trainer changed the admitted source/preparation destinations")
        projected_rows = _native_projection(prepared.source, admission)
        expected_projection = _source_projection(admission)
        _require(_canonical(prepared.manifest.get("source_projection")) == _canonical(expected_projection),
                 "trainer changed exact raw/duplicate/model-facing projection accounting")
        curriculum_identity = prepared.manifest.get("curriculum_identity")
        _require(type(curriculum_identity) is dict and curriculum_identity.get("projection_policy") == PROJECTION_POLICY
                 and curriculum_identity.get("dataset_schema") == REFERENCE_EXAMPLE_SCHEMA
                 and _canonical(curriculum_identity.get("review_admission")) == _canonical(
                     _identity(admission, _descriptor(_canonical(admission) + b"\n")["sha256"])),
                 "trainer lost the exact admission identity or projection policy")
        # Compact examples still identify the complete native row. Build this
        # index only from the trainer's freshly verified source, never from
        # caller-supplied examples, and reuse it for both reviewed splits.
        reference_index = trainer._frontier_reference_index(prepared.source)
        _require(type(reference_index) is tuple and len(reference_index) == 2
                 and reference_index[0] == admission["source_manifest_sha256"]
                 and type(reference_index[1]) is dict and 1 <= len(reference_index[1]) <= MAX_ROWS,
                 "trainer reference index changed the exact admitted native source")
        for split, examples in (("train", prepared.train_rows), ("dev", prepared.development_rows)):
            _require(type(examples) in (list, tuple) and len(examples) == len(projected_rows[split]),
                     "trainer changed the candidate first-occurrence transition order or membership")
            for row, expected in zip(examples, projected_rows[split]):
                _require(type(row) is dict and row.get("split") == split
                         and row.get("source_transition_sha256") == expected,
                         "trainer changed the candidate first-occurrence transition order or membership")
                resolved = trainer._resolve_frontier_example(prepared.source, row, split=split, index=reference_index)
                _require(type(resolved) is dict and _row_sha(resolved) == expected,
                         "compact model row does not resolve to the exact projected native transition")
        _require(not prepared.quarantined_rows, "admitted projection unexpectedly quarantined native source rows")
        _require(set(prepared.payloads) == PREPARATION_FILES and all(type(raw) is bytes for raw in prepared.payloads.values())
                 and sum(map(len, prepared.payloads.values())) <= MAX_PREPARATION_BYTES,
                 "trainer preparation payload inventory or total byte bound differs")
        published.assert_unchanged()
        original.assert_unchanged()
        review_tree.assert_unchanged()
        # Publication uses exact already-checked trainer payloads and held FDs.
        # The original preflight below re-creates and byte-compares every file.
        _mkdir(published, "preparation")
        for name in sorted(PREPARATION_FILES):
            _write(published, "preparation/" + name, prepared.payloads[name], MAX_PREPARATION_BYTES)
        preflight = trainer.preflight(output / "preparation")
        _require(preflight.get("run_id") == run_id and preflight.get("model_trained") is False
                 and preflight.get("cuda_initialized") is False
                 and preflight.get("epoch_sha256") == admission["bindings"]["epoch_sha256"]
                 and type(preflight.get("training_rows")) is int and preflight["training_rows"] == len(prepared.train_rows)
                 and type(preflight.get("development_rows")) is int and preflight["development_rows"] == len(prepared.development_rows),
                 "original trainer preflight changed its admitted run or row counts")
        actual_counts = {"train": len(prepared.train_rows), "dev": len(prepared.development_rows),
                         "quarantine": preflight.get("quarantined_rows")}
        _require(type(actual_counts["quarantine"]) is int and actual_counts["quarantine"] == 0
                 and sum(actual_counts.values()) == admission["counts"]["candidate_projected_rows"]
                 and all(actual_counts[split] == admission["counts"]["candidate_projected_split_rows"][split]
                         for split in ("train", "dev")),
                 "trainer counts differ from the candidate model-facing projection")
        published.assert_unchanged()
        original.assert_unchanged()
        review_tree.assert_unchanged()
        for _, tree in protected:
            if tree is not None:
                tree.assert_unchanged()
        # Retain complete genuine evidence on disk, not a second multi-megabyte
        # copy on the bounded worker's stdout. This is the existing preflight's
        # JSON transport (not the more restrictive lineage-string grammar).
        preflight_raw = json.dumps(preflight, sort_keys=True, ensure_ascii=False, allow_nan=False,
                                   separators=(",", ":")).encode("utf-8") + b"\n"
        _require(len(preflight_raw) <= MAX_METADATA_BYTES, "complete preflight exceeds its metadata byte bound")
        summary_keys = ("schema", "run_id", "epoch_sha256", "training_rows", "development_rows", "quarantined_rows",
                        "expected_optimizer_steps", "required_pythonhashseed", "adapter_output_dir",
                        "preparation_manifest_sha256", "model_trained", "cuda_initialized", "token_budget_verified",
                        "tokenizer_audit_required_before_model_weights", "research_claim_eligible", "unseen_holdout_claim_eligible")
        result = {"schema": PREPARATION_RESULT_SCHEMA, "status": "prepared-preflight-passed",
                "output_directory": str(output), "run_id": run_id,
                "admission": _identity(admission, _descriptor(_canonical(admission) + b"\n")["sha256"]),
                "preparation_manifest_sha256": _descriptor(prepared.payloads["manifest.json"])["sha256"],
                "prepared_split_rows": actual_counts, "candidate_projected_split_rows": admission["counts"]["candidate_projected_split_rows"],
                "native_source_split_rows": admission["counts"]["native_source_split_rows"],
                "duplicate_split_rows": admission["counts"]["duplicate_split_rows"],
                "preflight_file": _descriptor(preflight_raw),
                "preflight_summary": {key: preflight[key] for key in summary_keys if key in preflight},
                "human_review_record_created": False,
                "token_budget_verified": False, "model_trained": False,
                "model_training_authorized": False, "gpu_execution_authorized": False,
                "research_claim_eligible": False, "sealed_benchmark": False}
        _require(len(_canonical(result)) <= MAX_RESULT_BYTES, "admission result exceeds its compact output bound")
        _write(published, "preflight.json", preflight_raw, MAX_METADATA_BYTES)
        return result
