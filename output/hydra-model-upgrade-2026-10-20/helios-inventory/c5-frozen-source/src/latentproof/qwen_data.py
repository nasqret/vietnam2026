"""Campaign 3 compact Qwen data contract. Execute preparation/tests only in SLURM.

Candidate destination: latentproof.qwen_data. No model weights are needed.
Labels use the unshifted Hugging Face convention; a trainer must shift ONCE.
The prompt and literal action are encoded separately, then an actual EOS ID is
appended. Whole admitted sessions, never individual rows, may be length-excluded.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

FORMAT = "latent-qwen-compact-bpe-v1"
SELECTION_FORMAT = "latent-qwen-validation-selection-v1"
BASE_MODEL = "Qwen/Qwen3-1.7B-Base"
BASE_REVISION = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
ADMISSION_SHA256 = "85953fa15ce52f902be6eb7411f9f9bfdeaef642fb367f9138ffd5c516e4b14c"
TOKENIZER_FILES = {
    "tokenizer.json": "c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539",
    "tokenizer_config.json": "3c04ed3ca964ea2f6b2b5faf0dc4d31aec1cb1e8b4bcf63f402d295046b422b5",
    "vocab.json": "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910",
    "merges.txt": "8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5",
}
ROW_FIELDS = {"id", "prompt", "completion", "session_id", "task_family", "template", "family", "lineage",
              "step", "split", "formula", "state", "focus", "environment_sha256", "library_prefix_length",
              "source_record_sha256", "sequence_bytes_with_bos_eos"}
TOKEN_FIELDS = {"input_ids", "labels", "prompt_length", "target_start", "supervised_tokens", "sequence_length"}


class IntegrityError(RuntimeError):
    """A data/source/producer inconsistency, rather than a model failure."""


class SequenceTooLong(ValueError):
    pass


def require(condition, message):
    if not condition:
        raise IntegrityError(message)


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def object_pairs(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, f"duplicate JSON key: {key}")
        value[key] = item
    return value


def decode(value):
    def reject_constant(item):
        raise IntegrityError(f"non-finite JSON number: {item}")
    return json.loads(value, object_pairs_hook=object_pairs, parse_constant=reject_constant)


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            checksum.update(block)
    return checksum.hexdigest()


def object_digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        stream.write(canonical(value) + "\n")


def require_slurm():
    require(bool(os.environ.get("SLURM_JOB_ID")), "all execution must occur inside an authorized SLURM job")


def compact_prompt(goals, library_prefix_length=247, focus=0):
    require(type(goals) is list and goals and all(type(goal) is str and goal for goal in goals), "invalid rendered goals")
    require(type(focus) is int and 0 <= focus < len(goals), "invalid compact input focus")
    require(type(library_prefix_length) is int and library_prefix_length == 247, "this campaign uses full model-v3 authority")
    state = json.dumps({"focus": focus, "goals": goals}, ensure_ascii=False, separators=(",", ":"))
    return f"HA model-v3 library-prefix={library_prefix_length}/247\n{state}\nTactic:"


def validate_source_row(row, split, *, allowed_splits=None):
    require(type(row) is dict and set(row) == ROW_FIELDS, "unexpected compact source schema")
    allowed_splits = {"train", "val"} if allowed_splits is None else set(allowed_splits)
    require(row["split"] == split and split in allowed_splits, "source split is outside the explicit corpus contract")
    for key in ROW_FIELDS - {"step", "state", "focus", "library_prefix_length", "sequence_bytes_with_bos_eos"}:
        require(type(row[key]) is str and row[key], f"invalid source string: {key}")
    require(type(row["step"]) is int and row["step"] > 0, "invalid source step")
    require(type(row["focus"]) is int and row["focus"] == 0, "campaign 3 requires canonical first-goal conditioning")
    require(row["id"] == f"{row['session_id']}:{row['step']}", "source ID is not bound to session/step")
    require(row["prompt"] == compact_prompt(row["state"], row["library_prefix_length"], row["focus"]), "compact prompt lost state/focus information")
    require(row["completion"] == row["completion"].strip() and "\n" not in row["completion"] and "\r" not in row["completion"], "invalid literal action")
    require(type(row["sequence_bytes_with_bos_eos"]) is int
            and row["sequence_bytes_with_bos_eos"] == len(row["prompt"].encode()) + len(row["completion"].encode()) + 2,
            "inconsistent inherited byte-length metadata")


def encode_example(row, tokenizer, max_length=1024):
    """Return unshifted training labels; never truncate or repair source text."""
    require(type(max_length) is int and max_length > 1, "invalid maximum sequence length")
    require(type(row) is dict and type(row.get("prompt")) is str and row["prompt"]
            and type(row.get("completion")) is str and row["completion"], "empty prompt/action")
    eos = tokenizer.eos_token_id
    require(type(eos) is int and eos >= 0, "tokenizer lacks a concrete EOS ID")
    prompt = tokenizer.encode(row["prompt"], add_special_tokens=False)
    action = tokenizer.encode(row["completion"], add_special_tokens=False)
    require(type(prompt) is list and prompt and type(action) is list and action
            and all(type(token) is int and token >= 0 for token in prompt + action), "invalid tokenizer encoding")
    forbidden = set(tokenizer.get_added_vocab().values()) | set(getattr(tokenizer, "all_special_ids", [])) | {eos}
    require(not any(token in forbidden for token in prompt + action), "literal source text encoded an added/special control token")
    require(tokenizer.decode(prompt, skip_special_tokens=False, clean_up_tokenization_spaces=False) == row["prompt"]
            and tokenizer.decode(action, skip_special_tokens=False, clean_up_tokenization_spaces=False) == row["completion"],
            "tokenization did not preserve literal source text")
    ids = prompt + action + [eos]
    if len(ids) > max_length:
        raise SequenceTooLong(f"{row.get('id', '<fixture>')}: {len(ids)} > {max_length}")
    return {**row, "input_ids": ids, "labels": [-100] * len(prompt) + action + [eos],
            "prompt_length": len(prompt), "target_start": len(prompt),
            "supervised_tokens": len(action) + 1, "sequence_length": len(ids)}


def tokenizer_identity(tokenizer, tokenizer_path=None):
    require(tokenizer.eos_token_id == 151643 and tokenizer.pad_token_id == 151643,
            "pinned Qwen EOS/PAD identity changed")
    backend = decode(tokenizer.backend_tokenizer.to_str())
    require(backend.get("decoder", {}).get("type") == "ByteLevel", "Qwen tokenizer is not ByteLevel")
    inventory = None
    if tokenizer_path is not None:
        inventory = {name: digest(Path(tokenizer_path) / name) for name in TOKENIZER_FILES}
        require(inventory == TOKENIZER_FILES, "tokenizer bytes differ from pinned base revision")
    return {"model": BASE_MODEL, "revision": BASE_REVISION, "files_sha256": TOKENIZER_FILES,
            "vocabulary_size": len(tokenizer), "eos_token_id": tokenizer.eos_token_id,
            "pad_token_id": tokenizer.pad_token_id, "bos_token_id": tokenizer.bos_token_id,
            "added_vocabulary_sha256": object_digest(tokenizer.get_added_vocab()),
            "backend_sha256": hashlib.sha256(tokenizer.backend_tokenizer.to_str().encode()).hexdigest(),
            "file_bytes_verified": inventory is not None}


def load_pinned_tokenizer(path):
    require_slurm()
    path = Path(path)
    before = {name: digest(path / name) for name in TOKENIZER_FILES}
    require(before == TOKENIZER_FILES, "refusing an unpinned tokenizer")
    from transformers import AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(str(path), local_files_only=True, trust_remote_code=False, use_fast=True)
    identity = tokenizer_identity(tokenizer, path)
    require(before == {name: digest(path / name) for name in TOKENIZER_FILES}, "tokenizer changed while loading")
    return tokenizer, identity


def group_sessions(rows):
    sessions, ids = defaultdict(list), set()
    for row in rows:
        require(row["id"] not in ids, "duplicate row ID")
        ids.add(row["id"])
        sessions[row["session_id"]].append(row)
    invariant = ("formula", "environment_sha256", "library_prefix_length", "task_family", "template", "family", "lineage", "split")
    for session, episode in sessions.items():
        episode.sort(key=lambda row: row["step"])
        require([row["step"] for row in episode] == list(range(1, len(episode) + 1)), "partial or noncontiguous admitted session")
        require(all(all(row[key] == episode[0][key] for key in invariant) for row in episode), f"session identity drift: {session}")
    return dict(sessions)


def read_admitted(path, admission, split, *, allowed_splits=None):
    expected = admission["splits"][split]
    require(digest(path) == expected["output_sha256"], "admitted split bytes changed")
    rows = []
    with Path(path).open("rb") as stream:
        for raw in stream:
            require(raw.endswith(b"\n") and raw != b"\n", "invalid JSONL framing")
            row = decode(raw)
            validate_source_row(row, split, allowed_splits=allowed_splits)
            require(row["environment_sha256"] in admission["authorities"], "unadmitted authority")
            rows.append(row)
    sessions = group_sessions(rows)
    require(len(rows) == expected["retained_rows"] and len(sessions) == expected["retained_sessions"], "admission counts changed")
    return rows, sessions


def _order(identity, namespace):
    return hashlib.sha256((namespace + "\0" + identity).encode()).hexdigest()


def deterministic_evaluation_ids(rows, validation_rows=128, generation_rows=32, seed="latent-campaign3-v1"):
    by_id = {row["id"]: row for row in rows}
    require(len(by_id) == len(rows), "duplicate validation IDs")
    require(type(validation_rows) is int and type(generation_rows) is int
            and 0 < generation_rows <= validation_rows <= len(rows), "invalid validation/generation budget")
    validation = sorted(by_id, key=lambda key: _order(key, seed + ":validation"))[:validation_rows]
    generation = sorted(validation, key=lambda key: _order(key, seed + ":generation"))[:generation_rows]
    return {"validation_ids": validation, "generation_ids": generation}


def proof_stratum(family):
    if "induction" in family:
        return "induction"
    if "logic" in family or family.startswith(("root-conjunction", "root-disjunction")):
        return "logic"
    if "witness" in family or family == "root-existential":
        return "witness"
    if "recurrence" in family:
        return "recurrence"
    return "arithmetic-equality"


def select_proof_tasks(rows, generation_ids, count=16, seed="latent-campaign3-v1"):
    require(type(count) is int and count > 0, "invalid proof task count")
    groups = group_sessions(rows)
    excluded = {row["session_id"] for row in rows if row["id"] in set(generation_ids)}
    buckets = defaultdict(list)
    for session, episode in groups.items():
        if session not in excluded:
            buckets[proof_stratum(episode[0]["task_family"])].append(session)
    for values in buckets.values():
        values.sort(key=lambda session: _order(session, seed + ":proof-session"))
    strata = sorted(buckets, key=lambda family: _order(family, seed + ":proof-stratum"))
    selected, index = [], 0
    while len(selected) < count and any(index < len(buckets[stratum]) for stratum in strata):
        for stratum in strata:
            if index < len(buckets[stratum]) and len(selected) < count:
                selected.append((stratum, buckets[stratum][index]))
        index += 1
    require(len(selected) == count, "insufficient disjoint validation proof sessions")
    tasks = []
    for stratum, session in selected:
        episode, first = groups[session], groups[session][0]
        tasks.append({"id": session, "session_id": session, "split": "val", "stratum": stratum,
                      "task_family": first["task_family"], "formula": first["formula"],
                      "initial_state": first["state"], "focus": 0,
                      "environment_sha256": first["environment_sha256"], "library_prefix_length": first["library_prefix_length"],
                      "source_row_ids": [row["id"] for row in episode],
                      "admitted_episode_sha256": object_digest([{key: row[key] for key in sorted(ROW_FIELDS)} for row in episode])})
    return tasks


def validate_tokenized_row(row, *, eos_token_id, max_length, vocabulary_size=None, allowed_splits=None):
    require(set(row) == ROW_FIELDS | TOKEN_FIELDS, "unexpected tokenized row schema")
    validate_source_row({key: row[key] for key in ROW_FIELDS}, row["split"], allowed_splits=allowed_splits)
    ids, labels, boundary = row["input_ids"], row["labels"], row["prompt_length"]
    require(type(ids) is list and type(labels) is list and type(boundary) is int
            and all(type(token) is int and token >= 0 and (vocabulary_size is None or token < vocabulary_size) for token in ids), "invalid token IDs")
    require(0 < boundary < len(ids) - 1 and len(ids) == len(labels) <= max_length,
            "invalid token sequence or action boundary")
    require(all(type(label) is int for label in labels) and labels == [-100] * boundary + ids[boundary:], "prompt masking or labels changed")
    require(ids[-1] == eos_token_id and eos_token_id not in ids[:-1], "training EOS is absent, duplicated, or nonterminal")
    require(row["target_start"] == boundary and row["sequence_length"] == len(ids)
            and row["supervised_tokens"] == len(ids) - boundary, "invalid supervision counters")


def load_tokenized(path, manifest, split=None, *, expected_admission_sha256=ADMISSION_SHA256):
    """Load and validate an immutable prepared split; no torch import."""
    require_slurm()
    path = Path(path)
    if isinstance(manifest, (str, Path)):
        manifest = decode(Path(manifest).read_text(encoding="utf-8"))
    if manifest.get("format") == FORMAT:
        require(manifest.get("status") == "prepared", "invalid preparation manifest")
        allowed_splits = {"train", "val"}
    else:
        from .qwen_corpus import validate_preparation
        validate_preparation(manifest, expected_admission_sha256=expected_admission_sha256)
        allowed_splits = {"train", "dev", "test"}
    split = path.stem if split is None else split
    require(split in allowed_splits and split in manifest["splits"], "split is outside the explicit prepared contract")
    before = digest(path)
    require(before == manifest["splits"][split]["output_sha256"], "prepared dataset changed")
    rows = []
    with path.open("rb") as stream:
        for raw in stream:
            require(raw.endswith(b"\n") and raw != b"\n", "invalid tokenized JSONL framing")
            row = decode(raw)
            require(row.get("split") == split, "prepared split mismatch")
            validate_tokenized_row(row, eos_token_id=manifest["tokenizer"]["eos_token_id"], max_length=manifest["max_length"],
                                   vocabulary_size=manifest["tokenizer"]["vocabulary_size"], allowed_splits=allowed_splits)
            rows.append(row)
    groups = group_sessions(rows)
    require(len(rows) == manifest["splits"][split]["retained_rows"]
            and len(groups) == manifest["splits"][split]["retained_sessions"], "prepared counts changed")
    require(digest(path) == before, "prepared dataset changed while loading")
    return rows


def collate(rows, pad_token_id, device=None):
    """Right-pad by POSITION, including when PAD==EOS; HF labels stay unshifted.

    Return model tensors plus integer/list accounting fields. Pass only the four
    tensor inputs accepted by the trainer; supervised_token_count is not a model
    keyword. Token NLL denominator is supervised_token_count, never padded size.
    """
    require_slurm()
    require(rows and type(pad_token_id) is int, "empty batch or missing PAD")
    import torch
    lengths = [len(row["input_ids"]) for row in rows]
    width = max(lengths)
    ids = torch.full((len(rows), width), pad_token_id, dtype=torch.long, device=device)
    labels = torch.full_like(ids, -100)
    attention = torch.zeros_like(ids)
    positions = torch.zeros_like(ids)
    supervised = 0
    for index, row in enumerate(rows):
        length = lengths[index]
        require(len(row["labels"]) == length and row["labels"][0] == -100, "invalid batch labels")
        ids[index, :length] = torch.tensor(row["input_ids"], dtype=torch.long, device=device)
        labels[index, :length] = torch.tensor(row["labels"], dtype=torch.long, device=device)
        attention[index, :length] = 1
        positions[index, :length] = torch.arange(length, dtype=torch.long, device=device)
        count = sum(label != -100 for label in row["labels"][1:])
        require(count == row["supervised_tokens"] and count > 0, "supervision denominator drift")
        supervised += count
    return {"input_ids": ids, "labels": labels, "attention_mask": attention, "position_ids": positions,
            "supervised_token_count": supervised, "sequence_lengths": lengths,
            "row_ids": [row["id"] for row in rows]}


def prepare(args):
    require_slurm()
    started = time.monotonic()
    admission_path = args.admitted_dir / "admission.json"
    paths = [admission_path, args.admitted_dir / "train.jsonl", args.admitted_dir / "val.jsonl", Path(__file__)]
    paths += [args.tokenizer_path / name for name in TOKENIZER_FILES]
    before = {str(path.resolve()): digest(path) for path in paths}
    require(digest(admission_path) == ADMISSION_SHA256, "expected the complete campaign2-285001 admission")
    admission = decode(admission_path.read_text(encoding="utf-8"))
    require(admission["format"] == "latent-peano-v3-compact-state-v1" and admission["status"] == "admitted-python-replay"
            and admission["mode"] == "train-validation" and admission["test"]["parsed"] is False,
            "unexpected admission or opened test")
    tokenizer, identity = load_pinned_tokenizer(args.tokenizer_path)
    prepared, audits, seen = {}, {}, {}
    exclusions = []
    for split in ("train", "val"):
        rows, sessions = read_admitted(args.admitted_dir / f"{split}.jsonl", admission, split)
        kept, max_observed, length_histogram = [], 0, Counter()
        for number, (session, episode) in enumerate(sorted(sessions.items()), 1):
            encoded, overlong = [], []
            for row in episode:
                try:
                    value = encode_example(row, tokenizer, args.max_length)
                    validate_tokenized_row(value, eos_token_id=identity["eos_token_id"], max_length=args.max_length,
                                           vocabulary_size=identity["vocabulary_size"])
                    encoded.append(value)
                    max_observed = max(max_observed, value["sequence_length"])
                    length_histogram[str(value["sequence_length"])] += 1
                except SequenceTooLong as exc:
                    overlong.append({"id": row["id"], "reason": str(exc)})
            if overlong:
                exclusions.append({"split": split, "session_id": session, "rows": len(episode), "reason": "whole-session-BPE-length", "overlong_rows": overlong})
            else:
                kept.extend(encoded)
            if number % 2000 == 0:
                print(canonical({"event": "bpe-preparation-progress", "split": split, "sessions": number, "total_sessions": len(sessions)}), flush=True)
        require(kept, "BPE preparation excluded the entire split")
        retained_groups = group_sessions(kept)
        prepared[split] = kept
        seen[split] = {key: {row[key] for row in kept} for key in ("id", "session_id", "formula", "family", "lineage", "prompt")}
        output = args.output_dir / f"{split}.jsonl"
        with output.open("x", encoding="utf-8") as stream:
            for row in kept:
                stream.write(canonical(row) + "\n")
        audits[split] = {"source_rows": len(rows), "source_sessions": len(sessions), "retained_rows": len(kept),
                         "retained_sessions": len(retained_groups), "excluded_rows": len(rows) - len(kept),
                         "excluded_sessions": len(sessions) - len(retained_groups), "output_sha256": digest(output),
                         "max_retained_sequence_tokens": max(row["sequence_length"] for row in kept),
                         "max_supervised_tokens_including_eos": max(row["supervised_tokens"] for row in kept),
                         "supervised_tokens": sum(row["supervised_tokens"] for row in kept),
                         "supervised_tokens_including_eos_histogram": dict(Counter(str(row["supervised_tokens"]) for row in kept)),
                         "retained_sequence_tokens_histogram": dict(Counter(str(row["sequence_length"]) for row in kept)),
                         "task_family_rows": dict(Counter(row["task_family"] for row in kept))}
    overlap = {key: sorted(seen["train"][key] & seen["val"][key]) for key in seen["train"]}
    require(not any(overlap.values()), "prepared train/validation identity or prompt overlap")
    selection = deterministic_evaluation_ids(prepared["val"], args.validation_rows, args.generation_rows, args.seed)
    tasks = select_proof_tasks(prepared["val"], selection["generation_ids"], args.proof_tasks, args.seed)
    selection.update(format=SELECTION_FORMAT, split="val", seed=args.seed,
                     proof_tasks=tasks, proof_task_ids=[task["id"] for task in tasks],
                     validation_rows=args.validation_rows, generation_rows=args.generation_rows,
                     proof_tasks_count=args.proof_tasks, proof_selection="round-robin five metadata strata; SHA256 session order; exclude all generation sessions",
                     used_for_model_selection=True, test_parsed=False,
                     prepared_val_sha256=audits["val"]["output_sha256"])
    write_json(args.output_dir / "selection.json", selection)
    write_json(args.output_dir / "length-exclusions.json", exclusions)
    require(all(digest(path) == checksum for path, checksum in before.items()), "inputs changed during preparation")
    manifest = {"format": FORMAT, "status": "prepared", "tier": "T4", "slurm_job_id": os.environ["SLURM_JOB_ID"],
                "elapsed_seconds": time.monotonic() - started, "max_length": args.max_length,
                "tokenizer": identity, "tokenizer_identity_sha256": object_digest(identity),
                "encoding": "separate-prompt-and-literal-action; no BOS; one real terminal EOS; no chat template",
                "labels": "unshifted: -100 on prompt; literal action IDs plus EOS; trainer shifts exactly once",
                "session_rule": "keep all rows of an admitted session or drop its entire session",
                "truncation": False, "source_admission_sha256": ADMISSION_SHA256,
                "source_admission": str(admission_path.resolve()), "source_split_sha256": {split: admission["splits"][split]["output_sha256"] for split in prepared},
                "peano_source_files_sha256": admission["source_files_sha256"], "authorities": admission["authorities"],
                "splits": audits, "selection_sha256": digest(args.output_dir / "selection.json"),
                "selected_validation_ids": selection["validation_ids"], "selected_generation_ids": selection["generation_ids"],
                "selected_proof_task_ids": selection["proof_task_ids"], "overlap_counts": {key: len(value) for key, value in overlap.items()},
                "length_exclusions_sha256": digest(args.output_dir / "length-exclusions.json"),
                "input_sha256_before_and_after": before, "adapter_sha256": digest(__file__),
                "python": {"version": sys.version, "executable": sys.executable},
                "packages": {name: importlib.metadata.version(name) for name in ("transformers", "tokenizers")},
                "test": {"parsed": False, "used_for_selection": False},
                "checking_scope": "inherits exact admitted Python replay; this job verifies data/tokenization/provenance, not a new Lean check"}
    write_json(args.output_dir / "preparation.json", manifest)
    print(canonical({"event": "bpe-preparation-completed", "manifest": str(args.output_dir / "preparation.json"), "splits": {split: audits[split]["retained_rows"] for split in audits}}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--admitted-dir", type=Path, required=True)
    parser.add_argument("--tokenizer-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--max-length", type=int, default=1024)
    parser.add_argument("--validation-rows", type=int, default=128)
    parser.add_argument("--generation-rows", type=int, default=32)
    parser.add_argument("--proof-tasks", type=int, default=16)
    parser.add_argument("--seed", default="latent-campaign3-v1")
    args = parser.parse_args()
    require_slurm()
    require(not args.output_dir.resolve().is_relative_to(args.admitted_dir.resolve())
            and not args.output_dir.resolve().is_relative_to(args.tokenizer_path.resolve()), "outputs must be outside read-only source inputs")
    args.output_dir.mkdir(parents=True, exist_ok=False)
    try:
        prepare(args)
    except Exception as exc:
        write_json(args.output_dir / "FAILED.json", {"status": "infrastructure-abort", "error_type": type(exc).__name__, "error": str(exc), "slurm_job_id": os.environ["SLURM_JOB_ID"]})
        raise


if __name__ == "__main__":
    main()
