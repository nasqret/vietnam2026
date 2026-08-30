#!/usr/bin/env python3
"""Bounded, admitted-corpus production token preflight without model weights.

The real tokenizers 0.21.2 backend reads the byte-pinned saved Qwen tokenizer.
The ordinary tokenize_split/enforce_token_budget functions produce every token
record. The lightweight wrapper is reported honestly; it does not pretend to
be a Transformers model or grant training/benchmark/resource authorization.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).absolute().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "peano-lab/py")]
SCHEMA = "peano-hydra-frontier-production-token-preflight-v1"
TOKENIZER_VERSION = "0.21.2"
SOURCES = (
    "scripts/preflight_peano_hydra_frontier_tokens.py",
    "training/peano_hydra/scaling_admission.py",
    "training/peano_hydra/scaling_lineage.py",
    "training/peano_hydra/posttrain.py",
    "training/peano_hydra/review_runtime.py",
    "training/peano_policy/data.py",
    "training/peano_policy/prompt.py",
    "training/peano_policy/budget.py",
)


def require(value, message):
    if not value:
        raise ValueError(message)


def worker(args):
    from training.peano_hydra import frontier_pilot_launch as gate, scaling_admission, posttrain
    from training.peano_hydra import corrective_workflow as fileio
    from training.peano_policy.budget import tokenize_split, enforce_token_budget, tokenizer_identity_record
    preparation = args.preparation_dir.absolute()
    raw = fileio.read(preparation / "manifest.json", maximum=4 * 1024**2)
    require(hashlib.sha256(raw).hexdigest() == args.expected_preparation_manifest_sha256,
            "external raw preparation manifest identity differs")
    # This validates the entire exact accepted review and sibling source bytes
    # before importing tokenizers; a recovered unadmitted candidate cannot pass.
    identity = scaling_admission.admission_identity(preparation.parent / "source")
    require(identity["review_sha256"] == args.expected_review_sha256,
            "the exact externally supplied canonical human review SHA is required")
    prepared = posttrain.load_preparation(preparation)
    require(prepared.config.run.resume == "never"
            and prepared.config.model.model_id == gate.MODEL["model_id"]
            and prepared.config.model.revision == gate.MODEL["revision"],
            "preparation is not the reviewed fresh pinned-base run")
    require(prepared.manifest["curriculum_identity"]["review_admission"] == identity,
            "preparation lost its complete admitted source identity")
    preparation_bytes = sum(len(value) for value in prepared.payloads.values())
    require(preparation_bytes <= scaling_admission.MAX_PREPARATION_BYTES
            and set(prepared.payloads) == scaling_admission.PREPARATION_FILES,
            "complete preparation exceeds its unchanged byte cap")
    old_root = args.tokenizer_root.absolute()
    old_raw = fileio.read(old_root / "manifest.json", maximum=4 * 1024**2)
    require(hashlib.sha256(old_raw).hexdigest() == gate.PINS["baseline_adapter_manifest_sha256"],
            "tokenizer root is not the exact saved corrected adapter")
    old = json.loads(old_raw)
    tokenizer_file = old_root / "tokenizer/tokenizer.json"
    tokenizer_raw = fileio.read(tokenizer_file, maximum=64 * 1024**2)
    config_raw = fileio.read(old_root / "tokenizer/tokenizer_config.json", maximum=1024**2)
    tokenizer_sha = hashlib.sha256(tokenizer_raw).hexdigest()
    require(tokenizer_sha == gate.PINS["tokenizer_json_sha256"]
            == old["tokenizer"]["files"]["tokenizer/tokenizer.json"]
            and hashlib.sha256(config_raw).hexdigest() == old["tokenizer"]["files"]["tokenizer/tokenizer_config.json"],
            "saved tokenizer/config bytes changed")
    token_config = json.loads(config_raw)
    require(not {"torch", "transformers", "peft"} & set(sys.modules), "unexpected model framework import")
    if args.tokenizer_site is not None:
        site = args.tokenizer_site.absolute()
        require(site.is_dir() and not site.is_symlink(), "explicit tokenizer site must be a real directory")
        sys.path.insert(0, str(site))
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    import tokenizers
    require(tokenizers.__version__ == TOKENIZER_VERSION
            and importlib.metadata.version("tokenizers") == TOKENIZER_VERSION,
            "the real pinned tokenizers 0.21.2 backend is required")
    backend = tokenizers.Tokenizer.from_str(tokenizer_raw.decode())

    class PinnedBackendTokenizer:
        eos_token_id = backend.token_to_id(token_config["eos_token"])
        pad_token_id = eos_token_id

        def __len__(self):
            return backend.get_vocab_size(with_added_tokens=True)

        def __call__(self, text, *, add_special_tokens):
            require(add_special_tokens is False, "unexpected special-token insertion")
            return {"input_ids": backend.encode(text, add_special_tokens=False).ids}

    tokenizer = PinnedBackendTokenizer()
    require(tokenizer.eos_token_id == 151643 and len(tokenizer) == 151669,
            "pinned Qwen EOS/vocabulary changed")
    tokenizer_identity = tokenizer_identity_record(tokenizer, **gate.MODEL)
    exposures, summaries = {}, {}
    for split, rows, linear_cap, square_cap in (
        ("train", prepared.train_rows, posttrain.MAX_TRAIN_TOKENS, posttrain.MAX_TRAIN_SQUARED_TOKENS),
        ("dev", prepared.development_rows, posttrain.MAX_DEV_TOKENS, posttrain.MAX_DEV_SQUARED_TOKENS),
    ):
        examples = posttrain._proof_examples(prepared, rows, split=split)
        _, record = tokenize_split(examples, tokenizer, role=split, max_length=prepared.config.data.max_length,
                                   tokenizer_identity=tokenizer_identity, retain_encodings=False)
        enforce_token_budget(record, max_total_tokens=linear_cap, max_sum_squared_tokens=square_cap,
                             max_supervised_tokens=prepared.config.generation.max_new_tokens)
        exposures[split] = record
        summaries[split] = {"rows": record["rows"], "total": record["sequence"]["total"],
                            "sum_squared": record["sequence"]["sum_squared"],
                            "maximum": record["sequence"]["maximum"],
                            "supervised_maximum": record["supervision"]["maximum"]}
    require(hashlib.sha256(fileio.read(preparation / "manifest.json", maximum=4 * 1024**2)).hexdigest()
            == args.expected_preparation_manifest_sha256
            and scaling_admission.admission_identity(preparation.parent / "source") == identity
            and hashlib.sha256(fileio.read(tokenizer_file, maximum=64 * 1024**2)).hexdigest() == tokenizer_sha
            and not {"torch", "transformers", "peft"} & set(sys.modules),
            "admitted source/tokenizer changed or a model framework was imported")
    result = {
        "schema": SCHEMA, "status": "passed",
        "preparation_manifest_sha256": args.expected_preparation_manifest_sha256,
        "review_sha256": args.expected_review_sha256, "admission": identity,
        "preparation_bytes": preparation_bytes, "preparation_byte_cap": scaling_admission.MAX_PREPARATION_BYTES,
        "tokenizer_file_sha256": tokenizer_sha, "tokenizer_backend_version": TOKENIZER_VERSION,
        "tokenizer_identity": tokenizer_identity,
        "tokenizer_implementation": "real tokenizers backend plus exact no-special-tokens/EOS wrapper",
        "configured_max_length": prepared.config.data.max_length,
        "token_exposure": exposures, "splits": summaries,
        "model_weights_loaded": False, "model_frameworks_imported": False,
        "training_authorized": False, "gpu_execution_authorized": False,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False), flush=True)


def process_limits():
    """Stay within the existing immutable review-runtime worker ceilings."""
    from training.peano_hydra.review_runtime import ProcessLimits
    return ProcessLimits(cpu_seconds=120, wall_seconds=180, rss_bytes=2 * 1024**3,
                         output_bytes=256 * 1024)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--preparation-dir", type=Path, required=True)
    parser.add_argument("--expected-preparation-manifest-sha256", required=True)
    parser.add_argument("--expected-review-sha256", required=True, help="external CANONICAL human review SHA")
    parser.add_argument("--tokenizer-root", type=Path, required=True)
    parser.add_argument("--tokenizer-site", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    from training.peano_hydra import corrective_workflow as fileio
    from training.peano_hydra.review_runtime import run_bounded
    try:
        require(sys.flags.isolated and sys.dont_write_bytecode, "run with python -I -B")
        if args.worker:
            worker(args)
            return 0
        output = args.output.absolute()
        fileio.guard_output(output, protected=(args.preparation_dir.absolute().parent, args.tokenizer_root.absolute()))
        process_path = output.with_name(output.name + ".process.json")
        fileio.guard_output(process_path, protected=(args.preparation_dir.absolute().parent, args.tokenizer_root.absolute()))
        sources = {name: hashlib.sha256(fileio.read(ROOT / name, maximum=2 * 1024**2)).hexdigest() for name in SOURCES}
        limits = process_limits()
        arguments = list(sys.argv[1:] if argv is None else argv)
        command = (sys.executable, "-I", "-B", "-X", "pycache_prefix=/dev/null",
                   str(Path(__file__).absolute()), *arguments, "--worker")
        process = run_bounded(command, cwd=ROOT, limits=limits)
        unchanged = sources == {name: hashlib.sha256(fileio.read(ROOT / name, maximum=2 * 1024**2)).hexdigest() for name in SOURCES}
        passed = process["reason"] == "exited" and process["returncode"] == 0 and unchanged
        audit = {"schema": "peano-hydra-frontier-token-process-v1", "passed": passed,
                 "source_files": sources, "sources_unchanged": unchanged, "process": process}
        from training.peano_hydra.scaling_workflow import write_json
        write_json(process_path, audit)
        require(passed, "bounded admitted token preflight failed; see " + str(process_path))
        result = json.loads(process["stdout"])
        require(result.get("schema") == SCHEMA and result.get("status") == "passed",
                "token worker did not produce a complete admitted receipt")
        result["process_receipt"] = {"file": process_path.name,
                                    "sha256": hashlib.sha256(process_path.read_bytes()).hexdigest()}
        result["execution_source_files"] = sources
        write_json(output, result)
        print(json.dumps({"status": "passed", "output": str(output),
                          "output_sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
                          "splits": result["splits"], "model_weights_loaded": False}, sort_keys=True), flush=True)
        return 0
    except (ValueError, TypeError, KeyError, OSError, RuntimeError, ImportError) as error:
        print("frontier-token-preflight: " + " ".join(str(error).split()), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
