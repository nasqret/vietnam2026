"""Explicit, pinned hard-corpus extension; legacy Qwen data stays the default.

Candidate destination: latentproof.qwen_corpus. Preparation, tests and consumers
execute only in SLURM. This module never imports a model or an optimizer.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from itertools import combinations
import os
from pathlib import Path
import shutil
import sys
import time

from .qwen_data import (ADMISSION_SHA256, FORMAT as LEGACY_FORMAT,
    SELECTION_FORMAT as LEGACY_SELECTION_FORMAT, ROW_FIELDS, TOKENIZER_FILES,
    SequenceTooLong, canonical, decode, digest, encode_example, group_sessions,
    load_pinned_tokenizer, load_tokenized, object_digest, read_admitted, require,
    require_slurm, validate_tokenized_row, write_json, _order)

ADMISSION_FORMAT = "latent-peano-hard-constructive-v1"
FORMAT = "latent-qwen-compact-bpe-v2"
SELECTION_FORMAT = "latent-qwen-stratified-selection-v2"
PLAN_FORMAT = "latent-qwen-stratified-selection-plan-v1"
SPLITS = {"train", "dev", "test"}
METADATA_REQUIRED = {"session_id", "split", "structural_group", "structural_normalization_version",
    "recipe_ast", "recipe_sha256", "formula_ast", "formula", "difficulty_stratum", "evaluation_regime",
    "dependency_depth", "branch_count", "branch_depth", "gold_tactic_count", "native_proof_nodes", "shortcut_audit"}


def sha256_value(value):
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def contained_path(root, relative):
    require(type(relative) is str and relative and not Path(relative).is_absolute(), "expected relative artifact path")
    path = (Path(root) / relative).resolve()
    require(path.is_relative_to(Path(root).resolve()), "artifact path escapes corpus directory")
    return path


def validate_admission(admission, *, expected_admission_sha256=ADMISSION_SHA256):
    """The caller must hash the actual admission file against this external pin."""
    require(sha256_value(expected_admission_sha256), "missing explicit admission SHA256")
    require(admission.get("status") == "admitted-python-replay", "corpus is not replay-admitted")
    if expected_admission_sha256 == ADMISSION_SHA256:
        require(admission.get("format") == "latent-peano-v3-compact-state-v1"
                and admission.get("mode") == "train-validation", "legacy admission contract changed")
        return {"train", "val"}
    require(admission.get("format") == ADMISSION_FORMAT and type(admission.get("dataset_id")) is str
            and admission["dataset_id"], "new admission requires the explicit hard-corpus contract")
    require(set(admission.get("splits", {})) == SPLITS and set(admission.get("task_metadata", {})) == SPLITS,
            "hard admission must pin train/dev/test separately")
    require(type(admission.get("source_files_sha256")) is dict and admission["source_files_sha256"]
            and type(admission.get("authorities")) is dict and admission["authorities"], "missing source/authority inventories")
    return SPLITS


def validate_preparation(manifest, *, expected_admission_sha256):
    require(sha256_value(expected_admission_sha256) and expected_admission_sha256 != ADMISSION_SHA256,
            "hard corpus needs an externally supplied nonlegacy admission pin")
    require(manifest.get("format") == FORMAT and manifest.get("status") == "prepared"
            and manifest.get("source_admission_sha256") == expected_admission_sha256,
            "prepared hard-corpus identity mismatch")
    require(type(manifest.get("dataset_id")) is str and manifest["dataset_id"]
            and set(manifest.get("splits", {})) == SPLITS
            and set(manifest.get("task_metadata", {})) == SPLITS
            and set(manifest.get("selections", {})) == {"dev", "test"}, "incomplete hard-corpus manifest")
    require(manifest.get("truncation") is False and manifest.get("library_prefix_length") == 247,
            "hard corpus changed the compact full-authority condition")
    require(manifest.get("test", {}).get("used_for_model_selection") is False,
            "held-out test cannot select a checkpoint/policy")


def read_task_metadata(path, spec, *, split, sessions):
    require(type(spec) is dict and type(spec.get("sessions")) is int and spec["sessions"] >= 0
            and sha256_value(spec.get("sha256")), "invalid task metadata manifest counts/hash")
    before = digest(path)
    require(before == spec["sha256"], "task metadata bytes changed")
    result = {}
    with Path(path).open("rb") as stream:
        for raw in stream:
            require(raw.endswith(b"\n") and raw != b"\n", "invalid task metadata JSONL framing")
            task = decode(raw)
            require(type(task) is dict and METADATA_REQUIRED <= set(task), "missing structural task metadata")
            for key in ("session_id", "split", "structural_group", "structural_normalization_version", "formula",
                        "difficulty_stratum", "evaluation_regime"):
                require(type(task[key]) is str and task[key], f"invalid task metadata string: {key}")
            session = task["session_id"]
            require(task["split"] == split and session in sessions and session not in result,
                    "task metadata has duplicate, foreign or cross-split session")
            require(task["formula"] == sessions[session][0]["formula"]
                    and task["gold_tactic_count"] == len(sessions[session]), "task metadata differs from admitted episode")
            require(sha256_value(task["recipe_sha256"]) and task["recipe_sha256"] == object_digest(task["recipe_ast"]),
                    "recipe AST/hash mismatch")
            for key in ("dependency_depth", "branch_count", "branch_depth", "gold_tactic_count", "native_proof_nodes"):
                require(type(task[key]) is int and task[key] >= 0, f"invalid structural count: {key}")
            require(task["gold_tactic_count"] > 0 and task["native_proof_nodes"] > 0
                    and type(task["shortcut_audit"]) is dict, "missing gold proof/shortcut audit")
            result[session] = task
    require(len(result) == spec["sessions"] == len(sessions) and digest(path) == before,
            "task metadata does not cover exactly the admitted sessions, or changed")
    return result


def stratum_key(task):
    return task["evaluation_regime"], task["difficulty_stratum"]


def task_from_episode(episode, metadata):
    first = episode[0]
    return {"id": first["session_id"], "session_id": first["session_id"], "split": first["split"],
            "stratum": canonical(list(stratum_key(metadata))), "task_family": first["task_family"],
            "formula": first["formula"], "initial_state": first["state"], "focus": first["focus"],
            "environment_sha256": first["environment_sha256"], "library_prefix_length": first["library_prefix_length"],
            "source_row_ids": [row["id"] for row in episode],
            "admitted_episode_sha256": object_digest([{key: row[key] for key in sorted(ROW_FIELDS)} for row in episode]),
            "task_metadata_sha256": object_digest(metadata),
            "structural_group": metadata["structural_group"], "difficulty_stratum": metadata["difficulty_stratum"],
            "evaluation_regime": metadata["evaluation_regime"], "dependency_depth": metadata["dependency_depth"],
            "branch_count": metadata["branch_count"], "branch_depth": metadata["branch_depth"],
            "gold_tactic_count": metadata["gold_tactic_count"], "native_proof_nodes": metadata["native_proof_nodes"]}


def stratified_selection(rows, metadata, quotas, *, split, seed):
    """Exact preregistered quotas; no replacement, padding or shortage fallback."""
    require(split in {"dev", "test"} and type(quotas) is list and quotas, "invalid evaluation split/quotas")
    sessions = group_sessions(rows)
    by_id = {row["id"]: row for row in rows}
    available = {stratum_key(task) for task in metadata.values()}
    keyed, validation, generation, tasks, counts = {}, [], [], [], []
    for entry in quotas:
        require(type(entry) is dict and set(entry) == {"evaluation_regime", "difficulty_stratum", "validation_rows", "generation_rows", "proof_tasks"},
                "invalid quota schema")
        key = stratum_key(entry)
        require(key in available and key not in keyed, "quota for absent or duplicate stratum")
        require(all(type(entry[name]) is int and entry[name] >= 0 for name in ("validation_rows", "generation_rows", "proof_tasks"))
                and entry["validation_rows"] >= entry["generation_rows"], "invalid stratum quota counts")
        keyed[key] = entry
    require(set(keyed) == available, "every retained stratum needs an explicit quota, including explicit zeroes")
    for key in sorted(keyed):
        quota = keyed[key]
        local = [row["id"] for row in rows if stratum_key(metadata[row["session_id"]]) == key]
        namespace = seed + ":" + split + ":" + canonical(list(key))
        local.sort(key=lambda identity: _order(identity, namespace + ":validation"))
        require(len(local) >= quota["validation_rows"], "insufficient validation rows in a registered stratum")
        selected = local[:quota["validation_rows"]]
        actions = sorted(selected, key=lambda identity: _order(identity, namespace + ":generation"))[:quota["generation_rows"]]
        excluded = {by_id[identity]["session_id"] for identity in actions}
        eligible = [session for session in sessions if session not in excluded and stratum_key(metadata[session]) == key]
        eligible.sort(key=lambda identity: _order(identity, namespace + ":proof-session"))
        require(len(eligible) >= quota["proof_tasks"], "insufficient disjoint proof sessions in a registered stratum")
        chosen = eligible[:quota["proof_tasks"]]
        validation.extend(selected)
        generation.extend(actions)
        tasks.extend(task_from_episode(sessions[session], metadata[session]) for session in chosen)
        counts.append({**quota, "available_rows": len(local), "available_sessions": sum(stratum_key(t) == key for t in metadata.values()),
                       "available_proof_sessions_after_action_exclusion": len(eligible)})
    require(validation and generation and tasks, "each frozen evaluation selection must contain all three metric scopes")
    # Interleave strata in a deterministic hash order, avoiding an always-late hard
    # stratum under a shared deadline. The exact ordered roster is then frozen.
    validation.sort(key=lambda identity: _order(identity, seed + ":" + split + ":validation-roster"))
    generation.sort(key=lambda identity: _order(identity, seed + ":" + split + ":action-roster"))
    tasks.sort(key=lambda task: _order(task["id"], seed + ":" + split + ":proof-roster"))
    return {"format": SELECTION_FORMAT, "split": split, "seed": seed,
            "validation_ids": validation, "generation_ids": generation,
            "proof_tasks": tasks, "proof_task_ids": [task["id"] for task in tasks],
            "validation_rows": len(validation), "generation_rows": len(generation), "proof_tasks_count": len(tasks),
            "strata": counts, "stratification_fields": ["evaluation_regime", "difficulty_stratum"],
            "selection_rule": "exact per-stratum SHA256 quotas; exclude action sessions from autonomous targets; freeze hash-ordered rosters",
            "used_for_model_selection": split == "dev", "test_parsed": split == "test"}


def prepared_inputs(prepared_dir, *, split="val", expected_admission_sha256=ADMISSION_SHA256,
                    expected_preparation_sha256=None, expected_dataset_id=None):
    """Read only the requested split and its sidecar; never open another split.

    New corpora require both external pins. Returned hashes include every file
    read by this function and can be checked again at the end of a job.
    """
    require_slurm()
    root = Path(prepared_dir)
    manifest_path = root / "preparation.json"
    checksum = digest(manifest_path)
    if expected_preparation_sha256 is not None:
        require(sha256_value(expected_preparation_sha256) and checksum == expected_preparation_sha256,
                "prepared manifest differs from the registered evaluation/training plan")
    manifest = decode(manifest_path.read_text(encoding="utf-8"))
    before = {str(manifest_path.resolve()): checksum}
    if manifest.get("format") == LEGACY_FORMAT:
        require(expected_admission_sha256 == ADMISSION_SHA256 and manifest.get("source_admission_sha256") == ADMISSION_SHA256
                and manifest.get("test", {}).get("parsed") is False and split in {"train", "val"}, "legacy corpus contract mismatch")
        selection_path = root / "selection.json" if split == "val" else None
        metadata = None
    else:
        require(expected_preparation_sha256 is not None, "new corpus requires an external preparation-manifest pin")
        validate_preparation(manifest, expected_admission_sha256=expected_admission_sha256)
        require(split in SPLITS, "unregistered hard-corpus split")
        require(expected_dataset_id is None or manifest["dataset_id"] == expected_dataset_id, "wrong registered dataset_id")
        selection_path = contained_path(root, manifest["selections"][split]["path"]) if split != "train" else None
        metadata = {}
    data_path = root / (split + ".jsonl")
    rows = load_tokenized(data_path, manifest, split, expected_admission_sha256=expected_admission_sha256)
    before[str(data_path.resolve())] = digest(data_path)
    if metadata is not None:
        spec = manifest["task_metadata"][split]
        metadata_path = contained_path(root, spec["path"])
        metadata = read_task_metadata(metadata_path, spec, split=split, sessions=group_sessions(rows))
        before[str(metadata_path.resolve())] = spec["sha256"]
    selection = None
    if selection_path is not None:
        selection_sha = digest(selection_path)
        expected_sha = manifest["selection_sha256"] if metadata is None else manifest["selections"][split]["sha256"]
        require(selection_sha == expected_sha, "frozen evaluation selection changed")
        selection = decode(selection_path.read_text(encoding="utf-8"))
        require(type(selection) is dict, "selection must be a JSON object")
        before[str(selection_path.resolve())] = selection_sha
        expected_format = LEGACY_SELECTION_FORMAT if metadata is None else SELECTION_FORMAT
        require(selection.get("format") == expected_format and selection.get("split") == split
                and selection.get("test_parsed") is (split == "test"), "selection format/split/test-role changed")
        if metadata is None:
            require(selection["validation_ids"] == manifest["selected_validation_ids"]
                    and selection["generation_ids"] == manifest["selected_generation_ids"]
                    and selection["proof_task_ids"] == manifest["selected_proof_task_ids"], "selection/manifest IDs differ")
        else:
            require(selection.get("used_for_model_selection") is (split == "dev")
                    and selection.get("prepared_split_sha256") == manifest["splits"][split]["output_sha256"]
                    and selection.get("task_metadata_file_sha256") == manifest["task_metadata"][split]["sha256"],
                    "selection data/metadata/role binding mismatch")
        ids = {row["id"] for row in rows}
        for field, count in (("validation_ids", "validation_rows"), ("generation_ids", "generation_rows"),
                             ("proof_task_ids", "proof_tasks_count")):
            require(type(selection.get(field)) is list and all(type(identity) is str and identity for identity in selection[field])
                    and type(selection.get(count)) is int and selection[count] >= 0
                    and len(selection[field]) == len(set(selection[field])) == selection[count],
                    "ordered selection IDs must be a unique JSON list with an exact integer count")
        require(type(selection.get("proof_tasks")) is list and len(selection["proof_tasks"]) == selection["proof_tasks_count"]
                and all(type(task) is dict for task in selection["proof_tasks"])
                and [task.get("id") for task in selection["proof_tasks"]] == selection["proof_task_ids"],
                "proof task records differ from their ordered roster")
        require(len(set(selection["validation_ids"])) == len(selection["validation_ids"]) == selection["validation_rows"]
                and set(selection["validation_ids"]) <= ids
                and len(set(selection["generation_ids"])) == len(selection["generation_ids"]) == selection["generation_rows"]
                and set(selection["generation_ids"]) <= set(selection["validation_ids"]), "invalid frozen teacher-forced/action roster")
    require(all(digest(path) == checksum for path, checksum in before.items()), "prepared inputs changed while reading")
    return manifest, selection, rows, metadata, before


def validate_training_context(manifest, split_rows, max_sequence_length):
    """Reject undeclared context growth before model/optimizer construction.

    Check actual loaded lengths as well as the manifest summary. A preparation
    ceiling above the training ceiling is harmless only when every retained row
    still fits the explicitly declared training ceiling.
    """
    require(type(max_sequence_length) is int and max_sequence_length > 1, "invalid training context limit")
    require(type(split_rows) is dict and "train" in split_rows
            and set(split_rows) in ({"train", "val"}, {"train", "dev"}), "training context audit requires train and development only")
    for split, rows in split_rows.items():
        require(rows, "empty training/development context audit")
        observed = max(len(row["input_ids"]) for row in rows)
        declared = manifest["splits"][split]["max_retained_sequence_tokens"]
        require(type(declared) is int and declared == observed, "manifest retained context maximum differs from actual loaded rows")
        require(observed <= max_sequence_length, f"{split} retained sequences exceed the declared training context limit")


def prepare(args):
    require_slurm()
    started = time.monotonic()
    admission_path = args.admitted_dir / "admission.json"
    require(digest(admission_path) == args.expected_admission_sha256, "admission differs from external pin")
    admission = decode(admission_path.read_text(encoding="utf-8"))
    require(validate_admission(admission, expected_admission_sha256=args.expected_admission_sha256) == SPLITS,
            "use qwen_data for the legacy corpus")
    require(digest(args.selection_plan) == args.selection_plan_sha256, "selection plan differs from external pin")
    plan = decode(args.selection_plan.read_text(encoding="utf-8"))
    require(plan.get("format") == PLAN_FORMAT and plan.get("dataset_id") == admission["dataset_id"]
            and set(plan.get("splits", {})) == {"dev", "test"}
            and type(plan.get("seed")) is str and plan["seed"], "invalid frozen selection plan")
    inputs = [admission_path, args.selection_plan, Path(__file__), Path(sys.modules[encode_example.__module__].__file__)]
    inputs += [args.tokenizer_path / name for name in TOKENIZER_FILES]
    inputs += [args.admitted_dir / (split + ".jsonl") for split in sorted(SPLITS)]
    inputs += [contained_path(args.admitted_dir, admission["task_metadata"][split]["path"]) for split in sorted(SPLITS)]
    before = {str(path.resolve()): digest(path) for path in inputs}
    tokenizer, identity = load_pinned_tokenizer(args.tokenizer_path)
    args.output_dir.mkdir(parents=True, exist_ok=False)
    (args.output_dir / "tasks").mkdir()
    prepared, task_sets, audits, task_specs, selections, exclusions = {}, {}, {}, {}, {}, []
    source_groups = {}
    for split in ("train", "dev", "test"):
        rows, sessions = read_admitted(args.admitted_dir / (split + ".jsonl"), admission, split, allowed_splits=SPLITS)
        spec = admission["task_metadata"][split]
        tasks = read_task_metadata(contained_path(args.admitted_dir, spec["path"]), spec, split=split, sessions=sessions)
        source_groups[split] = {task["structural_group"] for task in tasks.values()}
        kept, kept_tasks = [], {}
        for session, episode in sorted(sessions.items()):
            encoded, overlong = [], []
            for row in episode:
                try:
                    value = encode_example(row, tokenizer, args.max_length)
                    validate_tokenized_row(value, eos_token_id=identity["eos_token_id"], max_length=args.max_length,
                                           vocabulary_size=identity["vocabulary_size"], allowed_splits=SPLITS)
                    encoded.append(value)
                except SequenceTooLong as exc:
                    overlong.append({"id": row["id"], "reason": str(exc)})
            if overlong:
                exclusions.append({"split": split, "session_id": session, "structural_group": tasks[session]["structural_group"],
                                   "rows": len(episode), "reason": "whole-session-BPE-length", "overlong_rows": overlong})
            else:
                kept.extend(encoded)
                kept_tasks[session] = tasks[session]
        require(kept, "BPE length exclusion removed an entire split")
        prepared[split], task_sets[split] = kept, kept_tasks
        output = args.output_dir / (split + ".jsonl")
        with output.open("x", encoding="utf-8") as stream:
            for row in kept:
                stream.write(canonical(row) + "\n")
        task_output = args.output_dir / "tasks" / (split + ".jsonl")
        with task_output.open("x", encoding="utf-8") as stream:
            for session in sorted(kept_tasks):
                stream.write(canonical(kept_tasks[session]) + "\n")
        task_specs[split] = {"path": "tasks/" + split + ".jsonl", "sha256": digest(task_output), "sessions": len(kept_tasks),
                             "source_sha256": spec["sha256"]}
        audits[split] = {"source_rows": len(rows), "source_sessions": len(sessions), "retained_rows": len(kept),
            "retained_sessions": len(kept_tasks), "excluded_rows": len(rows) - len(kept), "excluded_sessions": len(sessions) - len(kept_tasks),
            "output_sha256": digest(output), "max_retained_sequence_tokens": max(row["sequence_length"] for row in kept),
            "max_supervised_tokens_including_eos": max(row["supervised_tokens"] for row in kept),
            "supervised_tokens": sum(row["supervised_tokens"] for row in kept),
            "task_family_rows": dict(Counter(row["task_family"] for row in kept))}
    overlaps = {}
    for left, right in combinations(sorted(SPLITS), 2):
        require(not source_groups[left] & source_groups[right], "admitted structural groups overlap before length exclusion")
        values = {key: len({row[key] for row in prepared[left]} & {row[key] for row in prepared[right]})
                  for key in ("id", "session_id", "formula", "prompt")}
        values["structural_group"] = len({task["structural_group"] for task in task_sets[left].values()}
                                         & {task["structural_group"] for task in task_sets[right].values()})
        require(not any(values[key] for key in ("id", "session_id", "formula", "structural_group")),
                "cross-split target/structural-group leakage")
        overlaps[left + ":" + right] = values
    for split in ("dev", "test"):
        selection = stratified_selection(prepared[split], task_sets[split], plan["splits"][split], split=split, seed=plan["seed"])
        selection.update(dataset_id=admission["dataset_id"], prepared_split_sha256=audits[split]["output_sha256"],
                         task_metadata_file_sha256=task_specs[split]["sha256"], selection_plan_sha256=args.selection_plan_sha256)
        name = "selection-" + split + ".json"
        write_json(args.output_dir / name, selection)
        selections[split] = {"path": name, "sha256": digest(args.output_dir / name)}
    write_json(args.output_dir / "length-exclusions.json", exclusions)
    shutil.copyfile(admission_path, args.output_dir / "admission.json")
    shutil.copyfile(args.selection_plan, args.output_dir / "selection-plan.json")
    require(all(digest(path) == checksum for path, checksum in before.items()), "input changed during hard-corpus preparation")
    manifest = {"format": FORMAT, "status": "prepared", "tier": "T4", "dataset_id": admission["dataset_id"],
        "slurm_job_id": os.environ["SLURM_JOB_ID"], "elapsed_seconds": time.monotonic() - started,
        "max_length": args.max_length, "library_prefix_length": 247, "tokenizer": identity,
        "tokenizer_identity_sha256": object_digest(identity), "truncation": False,
        "encoding": "separate literal prompt/action; no BOS/chat; one actual EOS; labels shift once in the trainer",
        "session_rule": "all admitted rows or no rows; structural split assignment never changes",
        "source_admission_sha256": args.expected_admission_sha256, "source_admission": str(admission_path.resolve()),
        "source_split_sha256": {split: admission["splits"][split]["output_sha256"] for split in SPLITS},
        "peano_source_files_sha256": admission["source_files_sha256"], "authorities": admission["authorities"],
        "splits": audits, "task_metadata": task_specs, "selections": selections,
        "selection_plan_sha256": args.selection_plan_sha256, "overlap_counts": overlaps,
        "overlap_scope": "structural groups/targets disjoint; grammar families and reusable intermediate proof states may recur",
        "length_exclusions_sha256": digest(args.output_dir / "length-exclusions.json"),
        "input_sha256_before_and_after": before, "preparer_sha256": digest(__file__),
        "test": {"parsed_during_preparation": True, "used_for_model_selection": False,
                 "training_access": "trainer loads only train and dev files; test is a separate explicit evaluation"},
        "checking_scope": "inherits pinned constructive Python admission; not a new independent replay or Lean proof"}
    write_json(args.output_dir / "preparation.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admitted-dir", type=Path, required=True)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--expected-admission-sha256", required=True)
    parser.add_argument("--selection-plan", type=Path, required=True)
    parser.add_argument("--selection-plan-sha256", required=True)
    parser.add_argument("--max-length", type=int, default=1024)
    args = parser.parse_args()
    require_slurm()
    require(not args.output_dir.exists(), "preparation output already exists")
    require(not args.output_dir.resolve().is_relative_to(args.admitted_dir.resolve())
            and not args.output_dir.resolve().is_relative_to(args.tokenizer_path.resolve()), "output must not modify admitted data/base")
    try:
        prepare(args)
    except Exception as exc:
        if args.output_dir.exists() and not (args.output_dir / "preparation.json").exists():
            write_json(args.output_dir / "FAILED.json", {"status": "infrastructure-abort", "error_type": type(exc).__name__, "error": str(exc)})
        raise


if __name__ == "__main__":
    main()
