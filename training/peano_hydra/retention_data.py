"""Portable, bounded retention data preparation; standard library only.

This is a new multi-origin data format. It does not satisfy the historical
single-origin post-training validator and does not claim fresh native replay.
The training boundary must authenticate BOTH original OriginReferences and
call verify_against_originals using their real preparation/source locations.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import stat
from typing import Mapping


SCHEMA = "peano-hydra-retention-preparation-v1"
PROVENANCE_SCHEMA = "peano-hydra-retention-row-origin-v1"
PROFILE = "peano-hydra-retention-pilot-v1"
RUN_ID = "retention-pilot-v1"
MIXTURE_SCHEDULE = "static-mixture-deterministic-shuffle-single-epoch"
SEED = 20260826
ROUTES_PER_FAMILY = 32
SAVED = "saved-v25"
FRONTIER = "frontier-v28"
FRONTIER_FAMILIES = (
    "frontier_conjunction_chain", "frontier_conjunction_rebuild",
    "frontier_inductive_witness", "frontier_local_induction",
    "frontier_witness_recovery", "frontier_witness_transport",
)
MAX_FILE_BYTES = 64 * 1024**2
MAX_MANIFEST_BYTES = 8 * 1024**2
MAX_OUTPUT_BYTES = 128 * 1024**2
MAX_LINE_BYTES = 64 * 1024
MAX_SOURCE_ROWS = 16384
MAX_TRAIN_ROWS = 16384
MAX_DEV_ROWS = 4096
PAYLOAD_NAMES = (
    "train.jsonl", "dev.jsonl", "train-provenance.jsonl", "dev-provenance.jsonl",
    "frontier-proofs.jsonl", "frontier-proof-index.json",
    "saved-preparation.json", "frontier-preparation.json", "frontier-source.json",
)


class RetentionDataError(ValueError):
    """The requested mixture lost an original byte, split or provenance join."""


def _require(value: object, message: str) -> None:
    if not value:
        raise RetentionDataError(message)


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _hash(value: object) -> str:
    return _sha(_canonical(value))


def _pin(value: object) -> str:
    _require(type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value), "raw SHA256 required")
    return value


def _json(raw: bytes) -> dict:
    def pairs(values):
        result = {}
        for key, value in values:
            _require(key not in result, "duplicate JSON key")
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite JSON")))
    except (ValueError, RecursionError) as error:
        raise RetentionDataError("invalid bounded JSON object") from error
    _require(type(value) is dict, "JSON object required")
    return value


def _directory(path: Path) -> int:
    path = Path(path)
    _require(path.is_absolute() and ".." not in path.parts and len(path.parts) <= 64,
             "explicit absolute directory required")
    access = getattr(os, "O_PATH", os.O_RDONLY)
    fd = os.open(path.anchor, access | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for index, part in enumerate(path.parts[1:], 1):
            flags = os.O_RDONLY if index == len(path.parts) - 1 else access
            child = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = child
        result, fd = fd, -1
        return result
    finally:
        if fd >= 0:
            os.close(fd)


def _signature(info):
    return (info.st_dev, info.st_ino, info.st_mode, info.st_size,
            info.st_mtime_ns, info.st_ctime_ns, info.st_nlink)


def _read(path: Path, maximum: int = MAX_FILE_BYTES) -> bytes:
    parent = _directory(path.parent)
    try:
        fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            before = os.fstat(stream.fileno())
            _require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
                     and 0 <= before.st_size <= maximum, "input is not bounded regular single-link data")
            raw = stream.read(maximum + 1)
            _require(len(raw) == before.st_size and _signature(before) == _signature(os.fstat(stream.fileno()))
                     and _signature(before) == _signature(os.stat(path.name, dir_fd=parent, follow_symlinks=False)),
                     "input changed during bounded read")
            return raw
    finally:
        os.close(parent)


def _descriptor(raw: bytes, *, rows: int | None = None) -> dict:
    result = {"bytes": len(raw), "sha256": _sha(raw)}
    if rows is not None:
        result["rows"] = rows
    return result


def _lines(raw: bytes, maximum: int = MAX_SOURCE_ROWS):
    _require(raw.endswith(b"\n") and len(raw) <= MAX_FILE_BYTES, "bounded complete JSONL required")
    lines = raw.splitlines(keepends=True)
    _require(0 < len(lines) <= maximum, "JSONL row cap")
    result = []
    for number, line in enumerate(lines, 1):
        _require(line.endswith(b"\n") and len(line) <= MAX_LINE_BYTES, "JSONL line cap or termination")
        result.append((number, line, _json(line)))
    return result


def _state(row: dict) -> dict:
    prompt = row["prompt"]
    _require(type(prompt) is str and prompt.count("<state>") == prompt.count("</state>") == 1,
             "original prompt state framing changed")
    prefix, tail = prompt.split("<state>")
    body, suffix = tail.split("</state>")
    value = _json(body.encode())
    _require(suffix == "\n<tactic>" and set(value) == {"focus", "goals"}
             and value["focus"] == 0 and type(value["goals"]) is list and value["goals"]
             and all(type(goal) is str and goal for goal in value["goals"]), "original prompt state changed")
    return {"prefix_sha256": _sha(prefix.encode()), "state": value,
            "literal_state_sha256": _hash(value)}


def _routes(manifest: dict, split: str) -> list[dict]:
    routes = manifest["composition"]["plan"]["routes"]
    _require(type(routes) is list and 0 < len(routes) <= 2048, "original route inventory cap")
    names = [route["name"] for route in routes]
    _require(len(set(names)) == len(names), "duplicate original theorem route")
    for route in routes:
        _require(route["split"] in ("train", "dev") and type(route["commands"]) is list
                 and 0 < len(route["commands"]) <= 64
                 and route["commands_sha256"] == _hash(route["commands"])
                 and route["statement_sha256"] == _sha(route["statement"].encode()),
                 "original route command/statement identity changed")
    return [route for route in routes if route["split"] == split]


def _validate_example(row: dict, *, split: str, manifest: dict, routes: Mapping[str, dict]) -> dict:
    schema = ("peano-hydra-posttrain-example-v2" if manifest["version"] == "v25"
              else "peano-hydra-frontier-posttrain-reference-v1")
    _require(row.get("schema") == schema and row.get("split") == row.get("source_split") == split
             and row.get("kernel_checked") is True and row.get("epoch_sha256") == manifest["epoch_sha256"]
             and row.get("edition_identity_sha256") == manifest["edition_identity_sha256"]
             and row.get("authority_profile") == manifest["authority_profile"]
             and row.get("environment_sha256") == manifest["authority"]["environment_sha256"],
             "original example schema/split/epoch/authority changed")
    route = routes.get(row.get("theorem_name"))
    _require(route is not None and row.get("family") == route["family"]
             and row.get("lineage_sha256") == route["lineage_sha256"]
             and row.get("theorem_statement_sha256") == route["statement_sha256"],
             "example escaped its original complete proof route")
    action = row.get("action")
    _require(type(action) is str and action and "\n" not in action
             and row.get("completion") == action + "</tactic>" and action in route["commands"],
             "original positive label changed")
    _pin(row["state_sha256"])
    _pin(row["source_transition_sha256"])
    if manifest["version"] == "v25":
        transition = row.get("transition")
        _require(type(transition) is dict and _hash(transition) == row["source_transition_sha256"]
                 and all(transition[key] == row[key] for key in ("action", "prompt", "completion", "state_sha256")),
                 "saved nested original transition changed")
    else:
        _require(row.get("source_manifest_sha256") == manifest["source"]["manifest_sha256"],
                 "frontier reference lost its original native source manifest")
    return _state(row)


@dataclass(frozen=True)
class _Original:
    role: str
    manifest: dict
    manifest_raw: bytes
    manifest_sha256: str
    splits: dict


def _original(directory: Path, role: str, expected_manifest_sha256: str) -> _Original:
    raw = _read(directory / "manifest.json", MAX_MANIFEST_BYTES)
    manifest_sha256 = _sha(raw)
    _require(manifest_sha256 == _pin(expected_manifest_sha256), "externally pinned original preparation differs")
    manifest = _json(raw)
    version = "v25" if role == SAVED else "v28"
    _require(manifest.get("schema") == "peano-hydra-posttrain-preparation-v2"
             and manifest.get("version") == version
             and manifest.get("authority_profile") == "peano-authority-primitive-v1"
             and manifest["authority"]["classical"] is False
             and manifest["authority"]["capabilities"]["allowed_theorems"] == [],
             "wrong original retention preparation")
    splits = {}
    for split in ("train", "dev"):
        body = _read(directory / (split + ".jsonl"))
        rows = _lines(body)
        _require(_descriptor(body, rows=len(rows)) == manifest["files"][split + ".jsonl"],
                 "original split bytes or row count differ")
        routes = {route["name"]: route for route in _routes(manifest, split)}
        for _, _, row in rows:
            _validate_example(row, split=split, manifest=manifest, routes=routes)
        _require({row["theorem_name"] for _, _, row in rows} == set(routes),
                 "original preparation omitted a complete theorem route")
        splits[split] = rows
    return _Original(role, manifest, raw, manifest_sha256, splits)


def select_frontier_routes(routes: list[dict], *, seed: int = SEED) -> tuple[list[dict], dict]:
    """Select 32/144 routes in each family, balanced across all four axes.

    Keep 32 of 36 depth/shape/width cells, omit one cell per shape, and use
    each numeral exactly eight times. Hash ordering uses identities only;
    neither observed evaluation outcomes nor filesystem locations enter it.
    """
    _require(type(seed) is int and 0 <= seed < 2**63, "finite deterministic selection seed required")
    grouped = defaultdict(list)
    for route in routes:
        _require(route.get("split") == "train", "DEV/test route cannot enter frontier TRAIN selection")
        grouped[route["family"]].append(route)
    _require(set(grouped) == set(FRONTIER_FAMILIES), "frontier TRAIN families changed")
    selected, detail = [], {}
    all_variants = set(itertools.product((1, 2, 3), range(4), (1, 2, 3, 4), (2, 3, 4)))
    for family in FRONTIER_FAMILIES:
        by_variant = {tuple(route["variant"]): route for route in grouped[family]}
        _require(len(grouped[family]) == len(by_variant) == 144 and set(by_variant) == all_variants,
                 "frontier family is not the original full 144-route template grid")
        def ordered(values, label):
            return sorted(values, key=lambda value: _hash([seed, family, label, value]))
        depths, shapes = ordered((1, 2, 3), "depth"), ordered(range(4), "shape")
        widths, numerals = ordered((2, 3, 4), "width"), ordered((1, 2, 3, 4), "numeral")
        omitted = {(depths[index % 3], shape, widths[index % 3]) for index, shape in enumerate(shapes)}
        cells = ordered([cell for cell in itertools.product((1, 2, 3), range(4), (2, 3, 4))
                         if cell not in omitted], "retained-cell")
        chosen = [by_variant[(depth, shape, numerals[index % 4], width)]
                  for index, (depth, shape, width) in enumerate(cells)]
        _require(len(chosen) == ROUTES_PER_FAMILY, "selected route count differs")
        counts = {label: dict(sorted(Counter(route["variant"][axis] for route in chosen).items()))
                  for axis, label in enumerate(("depth", "shape", "numeral", "width"))}
        _require(all(max(values.values()) - min(values.values()) <= 1 for values in counts.values()),
                 "template-axis balance failed")
        selected.extend(chosen)
        detail[family] = {"available_routes": 144, "selected_routes": ROUTES_PER_FAMILY,
                          "axis_counts": counts, "omitted_depth_shape_width_cells": sorted(omitted)}
    selected.sort(key=lambda route: (route["family"], route["name"]))
    return selected, detail


def _origin_record(original: _Original) -> dict:
    manifest = original.manifest
    return {"version": manifest["version"], "run_id": manifest["run_id"],
        "preparation_manifest_sha256": original.manifest_sha256,
        "source_manifest_sha256": manifest["source"]["manifest_sha256"],
        "source_sft_sha256": manifest["source"]["sft_sha256"],
        "source_schema": manifest["source"]["schema"],
        "epoch_sha256": manifest["epoch_sha256"],
        "edition_identity_sha256": manifest["edition_identity_sha256"],
        "files": {name: manifest["files"][name] for name in ("train.jsonl", "dev.jsonl")},
        "families": {split: sorted({row["family"] for _, _, row in original.splits[split]})
                     for split in ("train", "dev")}}


def _frontier_proofs(source: Path, frontier: _Original, selected: list[dict]) -> tuple[dict[str, bytes], dict]:
    raw_manifest = _read(source / "manifest.json", MAX_MANIFEST_BYTES)
    _require(_sha(raw_manifest) == frontier.manifest["source"]["manifest_sha256"],
             "original frontier native curriculum manifest differs")
    source_manifest = _json(raw_manifest)
    _require(source_manifest.get("schema") == "peano-hydra-native-frontier-curriculum-source-v1",
             "wrong original frontier source schema")
    raw_sft = _read(source / "sft.jsonl")
    lines = _lines(raw_sft)
    _require(_descriptor(raw_sft, rows=len(lines)) == source_manifest["files"]["sft.jsonl"]
             and _sha(raw_sft) == frontier.manifest["source"]["sft_sha256"],
             "original frontier native transition bytes differ")
    wanted = {route["name"]: route for route in selected}
    proof_rows, by_route, transition_index = [], defaultdict(list), {}
    for number, raw, row in lines:
        name = row.get("theorem_name")
        if name not in wanted:
            continue
        route = wanted[name]
        step = len(by_route[name]) + 1
        _require(row.get("schema") == "peano-hydra-verified-transition-v1" and row.get("split") == "train"
                 and row.get("epoch_sha256") == frontier.manifest["epoch_sha256"]
                 and row.get("environment_sha256") == frontier.manifest["authority"]["environment_sha256"]
                 and row.get("lineage_sha256") == route["lineage_sha256"] and row.get("family") == route["family"]
                 and row.get("commands_sha256") == route["commands_sha256"]
                 and row.get("theorem") == route["statement"] and row.get("step") == step
                 and step <= len(route["commands"]) and row.get("action") == route["commands"][step - 1]
                 and row.get("completion") == row["action"] + "</tactic>"
                 and row.get("kernel_checked") is True, "selected original proof transition changed")
        before = (["⊢ " + route["statement"]] if step == 1 else by_route[name][-1][2]["goals_after"])
        _require(row.get("goals_before") == before and _state(row)["state"]["goals"] == before
                 and type(row.get("goals_after")) is list, "original proof route has a gap or altered prompt")
        transition_sha = _hash(row)
        _require(transition_sha not in transition_index, "duplicate full original transition identity")
        transition_index[transition_sha] = row
        by_route[name].append((number, raw, row))
        proof_rows.append(raw)
    _require(set(by_route) == set(wanted), "selected complete proof provenance missing")
    index = {}
    for name, rows in sorted(by_route.items()):
        route = wanted[name]
        _require(len(rows) == len(route["commands"]) and rows[-1][2]["goals_after"] == [],
                 "selected original proof provenance is incomplete")
        index[name] = {"family": route["family"], "commands_sha256": route["commands_sha256"],
            "steps": len(rows), "original_source_lines": [number for number, _, _ in rows],
            "original_row_sha256s": [_sha(raw) for _, raw, _ in rows],
            "transition_sha256s": [_hash(row) for _, _, row in rows],
            "original_last_goals_after": [], "native_replay_performed_by_builder": False}
    for _, _, row in frontier.splits["train"]:
        if row["theorem_name"] not in wanted:
            continue
        transition = transition_index.get(row["source_transition_sha256"])
        _require(transition is not None and all(transition[key] == row[key] for key in (
            "theorem_name", "action", "prompt", "completion", "state_sha256", "family", "lineage_sha256")),
            "projected selected label is not in its preserved complete original proof")
    record = {"schema": "peano-hydra-retention-original-proof-index-v1",
        "source_manifest_sha256": _sha(raw_manifest), "source_sft_sha256": _sha(raw_sft),
        "purpose": "original complete proof provenance only; not extra training labels or fresh native replay",
        "routes": index}
    return {"frontier-proofs.jsonl": b"".join(proof_rows),
            "frontier-proof-index.json": _canonical(record) + b"\n",
            "frontier-source.json": raw_manifest}, record


def _exclusions(train: list, dev: list) -> dict:
    def inventory(rows):
        names, statements, pairs = set(), set(), Counter()
        for _, _, _, row in rows:
            names.add(row["theorem_name"])
            statements.add(row["theorem_statement_sha256"])
            pairs[(_state(row)["literal_state_sha256"], row["action"])] += 1
        return names, statements, pairs
    a, b = inventory(train), inventory(dev)
    overlaps = {"theorem_names": sorted(a[0] & b[0]), "statement_sha256s": sorted(a[1] & b[1]),
                "literal_state_action_pairs": sorted(set(a[2]) & set(b[2]))}
    _require(not any(overlaps.values()), "combined TRAIN/DEV conflict; no rows were silently removed: "
             + json.dumps({key: values[:4] for key, values in overlaps.items()}, sort_keys=True))
    return {"exact_train_dev_theorem_overlaps": 0, "exact_train_dev_statement_overlaps": 0,
        "exact_train_dev_literal_state_action_overlaps": 0,
        "train_literal_state_action_duplicate_rows": sum(count - 1 for count in a[2].values()),
        "dev_literal_state_action_duplicate_rows": sum(count - 1 for count in b[2].values()),
        "semantic_equivalence_complete": False, "mathematical_independence_claimed": False,
        "source_correlations_preserved": True, "conflict_resolution": "fail-without-dropping-or-relabeling"}


def _assemble(saved_preparation: Path, frontier_preparation: Path, frontier_source: Path, *,
              saved_manifest_sha256: str, frontier_manifest_sha256: str, seed: int = SEED) -> dict[str, bytes]:
    originals = {SAVED: _original(saved_preparation, SAVED, saved_manifest_sha256),
                 FRONTIER: _original(frontier_preparation, FRONTIER, frontier_manifest_sha256)}
    saved, frontier = originals[SAVED], originals[FRONTIER]
    for key in ("model", "authority", "authority_profile", "prompt_contract", "decoder_profile"):
        _require(saved.manifest[key] == frontier.manifest[key], "original model/prompt/authority contracts differ")
    selected, balance = select_frontier_routes(_routes(frontier.manifest, "train"), seed=seed)
    names = {route["name"] for route in selected}
    train, dev = [], []
    for role, original in originals.items():
        train += [(role, number, raw, row) for number, raw, row in original.splits["train"]
                  if role == SAVED or row["theorem_name"] in names]
        dev += [(role, number, raw, row) for number, raw, row in original.splits["dev"]]
    _require(0 < len(train) <= MAX_TRAIN_ROWS and 0 < len(dev) <= MAX_DEV_ROWS, "mixed split row cap")
    _require({row["theorem_name"] for role, _, _, row in train if role == FRONTIER} == names,
             "selected frontier route lost all projected examples")
    prefixes = {_state(row)["prefix_sha256"] for _, _, _, row in train + dev}
    _require(len(prefixes) == 1, "original literal prompt prefixes differ")
    exclusions = _exclusions(train, dev)
    # Shuffle once by immutable identity. Original bytes are never normalized.
    train.sort(key=lambda item: _hash([seed, "static-mixture", item[0],
        originals[item[0]].manifest_sha256, item[1], _sha(item[2])]))
    payloads, proof_record = _frontier_proofs(frontier_source, frontier, selected)
    payloads.update({"saved-preparation.json": saved.manifest_raw,
                     "frontier-preparation.json": frontier.manifest_raw})
    counts = {}
    for split, rows in (("train", train), ("dev", dev)):
        payloads[split + ".jsonl"] = b"".join(raw for _, _, raw, _ in rows)
        provenance = []
        for output_line, (role, source_line, raw, row) in enumerate(rows, 1):
            original = originals[role]
            provenance.append({"schema": PROVENANCE_SCHEMA, "output_split": split, "output_line": output_line,
                "origin": role, "source_split": split, "source_line": source_line,
                "source_file_sha256": original.manifest["files"][split + ".jsonl"]["sha256"],
                "preparation_manifest_sha256": original.manifest_sha256, "source_row_sha256": _sha(raw),
                "source_transition_sha256": row["source_transition_sha256"], "theorem_name": row["theorem_name"]})
        payloads[split + "-provenance.jsonl"] = b"".join(_canonical(row) + b"\n" for row in provenance)
        counts[split] = {"rows": len(rows), "origins": dict(Counter(role for role, _, _, _ in rows)),
            "family_rows": dict(sorted(Counter(row["family"] for _, _, _, row in rows).items())),
            "action_heads": dict(sorted(Counter(row["action"].split()[0] for _, _, _, row in rows).items()))}
    source_steps = sum(item["steps"] for item in proof_record["routes"].values())
    frontier_count = counts["train"]["origins"][FRONTIER]
    manifest = {"schema": SCHEMA, "profile": PROFILE, "run_id": RUN_ID,
        "status": "prepared-metadata-only-original-authentication-required",
        "mixture_schedule": MIXTURE_SCHEDULE, "seed": seed,
        "origins": {role: _origin_record(original) for role, original in originals.items()},
        "model": saved.manifest["model"], "authority": saved.manifest["authority"],
        "authority_profile": saved.manifest["authority_profile"],
        "prompt_contract": saved.manifest["prompt_contract"], "decoder_profile": saved.manifest["decoder_profile"],
        "literal_prompt_prefix_sha256": next(iter(prefixes)),
        "selection": {"policy": "32-of-144-balanced-template-axes-whole-routes-v1",
            "saved_train": "all-original-rows-no-deduplication-or-relabeling",
            "frontier_train": "all-retained-preparation-rows-for-each-selected-original-route",
            "routes_per_family": ROUTES_PER_FAMILY, "selected_route_count": len(selected),
            "selected_routes": selected, "axis_balance": balance,
            "selected_original_proof_steps": source_steps, "selected_projected_training_rows": frontier_count,
            "frontier_fraction_of_final_train_rows": frontier_count / len(train),
            "source_projection": frontier.manifest.get("source_projection"),
            "projected_rows_are_not_complete_proof_traces": True,
            "complete_original_proof_provenance_preserved_separately": True},
        "dev_cohorts": {role: _routes(original.manifest, "dev") for role, original in originals.items()},
        "counts": counts, "split_exclusions": exclusions,
        "files": {name: _descriptor(raw, rows=raw.count(b"\n") if name.endswith(".jsonl") else None)
                  for name, raw in sorted(payloads.items())},
        "original_native_receipts_required_at_training_boundary": True,
        "original_bytes_revalidation_required_at_training_boundary": True,
        "native_replay_performed_by_builder": False, "model_loaded_by_builder": False,
        "mixed_origin_epoch_equivalence_claimed": False, "dev_or_test_rows_used_for_training": False,
        "heldout_or_sealed_benchmark": False, "research_claim_eligible": False,
        "limits": {"train_rows": MAX_TRAIN_ROWS, "dev_rows": MAX_DEV_ROWS,
                   "file_bytes": MAX_FILE_BYTES, "output_bytes": MAX_OUTPUT_BYTES}}
    payloads["manifest.json"] = _canonical(manifest) + b"\n"
    _require(len(payloads["manifest.json"]) <= MAX_MANIFEST_BYTES
             and all(len(raw) <= MAX_FILE_BYTES for raw in payloads.values())
             and sum(map(len, payloads.values())) <= MAX_OUTPUT_BYTES, "mixed preparation output cap")
    return payloads


@dataclass(frozen=True)
class RetentionPreparation:
    directory: Path
    manifest: dict
    manifest_sha256: str
    train_rows: tuple[dict, ...]
    dev_rows: tuple[dict, ...]

    @property
    def dev_cohorts(self) -> dict:
        return self.manifest["dev_cohorts"]

    def to_dict(self) -> dict:
        """Portable identity: locations are runtime bindings, not identities."""
        return {"schema": SCHEMA, "profile": PROFILE, "run_id": RUN_ID,
                "manifest_sha256": self.manifest_sha256, "files": self.manifest["files"],
                "origins": self.manifest["origins"], "counts": self.manifest["counts"]}

    def protected_paths(self) -> tuple[Path, ...]:
        return (self.directory,) + tuple(self.directory / name for name in ("manifest.json", *PAYLOAD_NAMES))


def load_preparation(directory: Path, *, expected_manifest_sha256: str) -> RetentionPreparation:
    """Load a pinned mixed artifact without model/native work.

    This checks artifact integrity and split/row joins. The independent join to
    authentic complete original bytes is verify_against_originals, which the
    training runner must call after loading its two genuine OriginReferences.
    """
    directory = Path(directory).absolute()
    raw = _read(directory / "manifest.json", MAX_MANIFEST_BYTES)
    _require(_sha(raw) == _pin(expected_manifest_sha256), "externally pinned retention manifest differs")
    manifest = _json(raw)
    _require(manifest.get("schema") == SCHEMA and manifest.get("profile") == PROFILE
             and manifest.get("run_id") == RUN_ID and manifest.get("mixture_schedule") == MIXTURE_SCHEDULE
             and manifest.get("native_replay_performed_by_builder") is False
             and manifest.get("dev_or_test_rows_used_for_training") is False
             and manifest.get("original_native_receipts_required_at_training_boundary") is True
             and manifest.get("original_bytes_revalidation_required_at_training_boundary") is True
             and set(manifest["origins"]) == {SAVED, FRONTIER}
             and set(manifest["files"]) == set(PAYLOAD_NAMES), "unsupported retention artifact scope")
    fd = _directory(directory)
    try:
        _require(set(os.listdir(fd)) == {"manifest.json", *PAYLOAD_NAMES}, "unexpected retention artifact entry")
    finally:
        os.close(fd)
    payloads = {}
    for name in PAYLOAD_NAMES:
        body = _read(directory / name)
        rows = body.count(b"\n") if name.endswith(".jsonl") else None
        _require(_descriptor(body, rows=rows) == manifest["files"][name], "retention payload bytes changed: " + name)
        payloads[name] = body
    _require(sum(map(len, payloads.values())) + len(raw) <= MAX_OUTPUT_BYTES, "retention total byte cap")
    originals = {SAVED: _json(payloads["saved-preparation.json"]), FRONTIER: _json(payloads["frontier-preparation.json"])}
    for role, name in ((SAVED, "saved-preparation.json"), (FRONTIER, "frontier-preparation.json")):
        origin, original = manifest["origins"][role], originals[role]
        _require(origin["preparation_manifest_sha256"] == _sha(payloads[name])
                 and origin["source_manifest_sha256"] == original["source"]["manifest_sha256"]
                 and origin["epoch_sha256"] == original["epoch_sha256"]
                 and origin["files"] == {key: original["files"][key] for key in ("train.jsonl", "dev.jsonl")}
                 and manifest["dev_cohorts"][role] == _routes(original, "dev"), "original portable identity changed")
    selected, balance = select_frontier_routes(_routes(originals[FRONTIER], "train"), seed=manifest["seed"])
    _require(manifest["selection"]["selected_routes"] == selected
             and manifest["selection"]["axis_balance"] == json.loads(_canonical(balance)),
             "retention deterministic route selection changed")
    selected_names = {route["name"] for route in selected}
    joined = {}
    for split, maximum in (("train", MAX_TRAIN_ROWS), ("dev", MAX_DEV_ROWS)):
        rows, provenance = _lines(payloads[split + ".jsonl"], maximum), _lines(payloads[split + "-provenance.jsonl"], maximum)
        _require(len(rows) == len(provenance) == manifest["counts"][split]["rows"], "retention row provenance count changed")
        route_maps = {role: {route["name"]: route for route in _routes(original, split)}
                      for role, original in originals.items()}
        source_rows = defaultdict(dict)
        items = []
        for (line, body, row), (_, _, trace) in zip(rows, provenance):
            role = trace.get("origin")
            _require(role in originals and trace.get("schema") == PROVENANCE_SCHEMA
                     and trace.get("output_split") == trace.get("source_split") == split
                     and trace.get("output_line") == line and trace.get("source_row_sha256") == _sha(body)
                     and trace.get("source_transition_sha256") == row["source_transition_sha256"]
                     and trace.get("theorem_name") == row["theorem_name"], "retention row provenance changed")
            original, origin = originals[role], manifest["origins"][role]
            source_line = trace["source_line"]
            _require(type(source_line) is int and 1 <= source_line <= origin["files"][split + ".jsonl"]["rows"]
                     and source_line not in source_rows[role]
                     and trace["source_file_sha256"] == origin["files"][split + ".jsonl"]["sha256"]
                     and trace["preparation_manifest_sha256"] == origin["preparation_manifest_sha256"],
                     "retention row source location or input identity changed")
            _validate_example(row, split=split, manifest=original, routes=route_maps[role])
            _require(split != "train" or role == SAVED or row["theorem_name"] in selected_names,
                     "unselected frontier route entered TRAIN")
            source_rows[role][source_line] = body
            items.append((role, source_line, body, row))
        for role, values in source_rows.items():
            if split == "dev" or role == SAVED:
                expected = manifest["origins"][role]["files"][split + ".jsonl"]
                _require(set(values) == set(range(1, expected["rows"] + 1))
                         and _descriptor(b"".join(values[index] for index in sorted(values)), rows=len(values)) == expected,
                         "all original saved TRAIN and both complete DEV files must remain byte-identical")
        _require(set(source_rows) == {SAVED, FRONTIER}, "mixed split lost an original source")
        if split == "train":
            _require({row["theorem_name"] for role, _, _, row in items if role == FRONTIER} == selected_names,
                     "selected frontier projected route missing")
            expected_order = sorted(items, key=lambda item: _hash([manifest["seed"], "static-mixture", item[0],
                manifest["origins"][item[0]]["preparation_manifest_sha256"], item[1], _sha(item[2])]))
            _require(items == expected_order, "static training shuffle changed")
        actual_counts = {"rows": len(items), "origins": dict(Counter(role for role, _, _, _ in items)),
            "family_rows": dict(sorted(Counter(row["family"] for _, _, _, row in items).items())),
            "action_heads": dict(sorted(Counter(row["action"].split()[0] for _, _, _, row in items).items()))}
        _require(actual_counts == manifest["counts"][split], "mixed split coverage counts changed")
        joined[split] = items
    _require(_exclusions(joined["train"], joined["dev"]) == manifest["split_exclusions"], "mixed split exclusions changed")
    return RetentionPreparation(directory, manifest, _sha(raw),
        tuple(row for _, _, _, row in joined["train"]), tuple(row for _, _, _, row in joined["dev"]))


def prepare_retention(saved_preparation: Path, frontier_preparation: Path, frontier_source: Path,
                      output_directory: Path, *, saved_manifest_sha256: str,
                      frontier_manifest_sha256: str, seed: int = SEED) -> RetentionPreparation:
    """Build one exclusive artifact; existing directories are never adopted."""
    paths = [Path(path).absolute() for path in (saved_preparation, frontier_preparation, frontier_source)]
    output = Path(output_directory).absolute()
    _require(all(output != source and output not in source.parents and source not in output.parents for source in paths),
             "output must be separate from every immutable input root")
    payloads = _assemble(*paths, saved_manifest_sha256=saved_manifest_sha256,
                         frontier_manifest_sha256=frontier_manifest_sha256, seed=seed)
    parent = _directory(output.parent)
    try:
        os.mkdir(output.name, mode=0o700, dir_fd=parent)
        fd = os.open(output.name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=parent)
    finally:
        os.close(parent)
    try:
        # A failed write retains its partial directory. No overwrite/retry.
        for name, body in sorted(payloads.items(), key=lambda item: (item[0] == "manifest.json", item[0])):
            leaf = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            with os.fdopen(leaf, "wb") as stream:
                stream.write(body)
                stream.flush()
                os.fsync(stream.fileno())
        os.fsync(fd)
    finally:
        os.close(fd)
    return load_preparation(output, expected_manifest_sha256=_sha(payloads["manifest.json"]))


def verify_against_originals(prepared: RetentionPreparation, *, saved_preparation: Path,
                             frontier_preparation: Path, frontier_source: Path) -> dict:
    """Mandatory training-boundary byte join, after both original authentications.

    Recompute the entire deterministic mixture from the real original inputs;
    self-consistent replacement provenance alone cannot pass this comparison.
    Explicit physical input locations are excluded from portable identities.
    """
    _require(type(prepared) is RetentionPreparation, "loaded retention preparation required")
    current = load_preparation(prepared.directory, expected_manifest_sha256=prepared.manifest_sha256)
    _require(prepared.manifest == current.manifest and prepared.train_rows == current.train_rows
             and prepared.dev_rows == current.dev_rows,
             "in-memory retention rows or metadata differ from the pinned artifact")
    origins = current.manifest["origins"]
    expected = _assemble(Path(saved_preparation).absolute(), Path(frontier_preparation).absolute(),
        Path(frontier_source).absolute(), saved_manifest_sha256=origins[SAVED]["preparation_manifest_sha256"],
        frontier_manifest_sha256=origins[FRONTIER]["preparation_manifest_sha256"], seed=current.manifest["seed"])
    _require(_sha(expected["manifest.json"]) == current.manifest_sha256,
             "mixed preparation is not the deterministic projection of actual authenticated original bytes")
    for name, raw in expected.items():
        _require(_read(current.directory / name) == raw, "mixed payload differs from actual original bytes: " + name)
    return {"schema": "peano-hydra-retention-original-byte-join-v1",
        "manifest_sha256": current.manifest_sha256, "origins": origins,
        "all_saved_train_rows_retained": True, "all_original_dev_rows_retained": True,
        "selected_frontier_routes": current.manifest["selection"]["selected_route_count"],
        "complete_original_selected_proof_bytes_matched": True,
        "native_replay_performed": False, "model_loaded": False}
