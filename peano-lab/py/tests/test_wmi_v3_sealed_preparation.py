"""Behavioral checks for the fail-closed WMI v3 preparation chain."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import ModuleType, SimpleNamespace

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
VERIFIER_PATH = REPOSITORY_ROOT / "scripts" / "verify_wmi_v3_sealed_preparation.py"
ELIGIBILITY_PATH = REPOSITORY_ROOT / "scripts" / "verify_peano_v3_corpus_eligibility.py"
SEAL_CLI_PATH = REPOSITORY_ROOT / "scripts" / "seal_peano_v3_corpus.py"


def _load_script(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VERIFIER = _load_script("wmi_v3_sealed_verifier", VERIFIER_PATH)
ELIGIBILITY = _load_script("wmi_v3_eligibility_cli", ELIGIBILITY_PATH)
SEAL_CLI = _load_script("peano_v3_seal_cli", SEAL_CLI_PATH)


def _digest(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _self_bound(core: dict[str, object], field: str) -> dict[str, object]:
    return {**core, field: _digest(core)}


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )


def _config_text() -> str:
    return """
[run]
name = "qwen3-1.7b-peano-lora-v3-library"
seed = 20260729
output_dir = "results/peano-policy/qwen3-1.7b-lora-v3-library"
max_eval_samples = 512
resume = "never"

[model]
model_id = "Qwen/Qwen3-1.7B-Base"
revision = "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
dtype = "bfloat16"
attn_implementation = "sdpa"
trust_remote_code = false

[data]
train_path = "checkpoints/corpora/v3-test/data/train.jsonl"
eval_path = "checkpoints/corpora/v3-test/data/val.jsonl"
max_length = 32768

[lora]
rank = 32
alpha = 64
dropout = 0.05
target_modules = [
  "q_proj", "k_proj", "v_proj", "o_proj",
  "gate_proj", "up_proj", "down_proj",
]

[trainer]
epochs = 1.0
max_steps = -1
per_device_train_batch_size = 1
per_device_eval_batch_size = 1
gradient_accumulation_steps = 32
learning_rate = 0.0001
weight_decay = 0.01
warmup_ratio = 0.05
logging_steps = 10
eval_steps = 1000
save_steps = 1000
save_total_limit = 1
gradient_checkpointing = true

[generation]
max_new_tokens = 1024
do_sample = false
temperature = 1.0
top_p = 1.0

[curriculum]
kind = "model-v3-library-balanced-v1"
selection_seed = 20260729
synthetic_row_ceiling = 12288
max_train_tokens = 100000
max_eval_tokens = 1000
max_train_squared_tokens = 1000000
max_eval_squared_tokens = 10000
corpus_seal_path = "checkpoints/corpora/v3-test"
corpus_source_commit = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
corpus_prepare_job_id = "172729"
corpus_content_sha256 = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
""".lstrip()


def _token_record(role: str, *, rows: int, maximum: int, total: int) -> dict[str, object]:
    core: dict[str, object] = {
        "format": "peano-policy-token-exposure",
        "v": 1,
        "role": role,
        "tokenizer": {
            "model_id": "Qwen/Qwen3-1.7B-Base",
            "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
            "class": "Qwen2TokenizerFast",
            "vocab_size": 151936,
            "eos_token_id": 151645,
            "pad_token_id": 151645,
        },
        "max_length": 32768,
        "rows": rows,
        "order_sha256": "1" * 64,
        "tokenized_rows_sha256": "2" * 64,
        "sequence": {
            "minimum": 2,
            "median": 3,
            "p95": 4,
            "p99": maximum,
            "maximum": maximum,
            "mean": round(total / rows, 3),
            "total": total,
            "sum_squared": total * 2,
            "longest_example_id": f"{role}:longest",
        },
        "supervision": {
            "minimum": 1,
            "median": 1,
            "p95": 2,
            "p99": 3,
            "maximum": 8,
            "mean": 1.5,
            "total": rows * 2,
            "longest_example_id": f"{role}:longest",
        },
    }
    return _self_bound(core, "record_sha256")


def _artifact_group(root: str, files: dict[str, str]) -> dict[str, object]:
    return {"root": root, "sha256": _digest(files), "files": files}


def _attach_adapter_admission(smoke: dict[str, object]) -> None:
    """Build one internally exact fixture using the production hash contracts."""

    corpus = smoke["corpus_eligibility"]
    curriculum = smoke["curriculum"]
    train_tokens = smoke["tokenized_train"]
    eval_tokens = smoke["tokenized_evaluation"]
    assert all(
        isinstance(record, dict)
        for record in (corpus, curriculum, train_tokens, eval_tokens)
    )
    train_ids: list[str] = []
    for example_id in (
        train_tokens["sequence"]["longest_example_id"],
        train_tokens["supervision"]["longest_example_id"],
    ):
        assert isinstance(example_id, str)
        if example_id not in train_ids:
            train_ids.append(example_id)
    validation_id = "eval:first"
    selection_core = {
        "format": VERIFIER.ADMISSION_SELECTION_FORMAT,
        "v": 1,
        "sealed_corpus_eligibility_sha256": corpus["eligibility_sha256"],
        "curriculum_sha256": curriculum["curriculum_sha256"],
        "tokenized_train_sha256": train_tokens["record_sha256"],
        "tokenized_evaluation_sha256": eval_tokens["record_sha256"],
        "train_candidate_policy": "natural-memory-extrema-v1",
        "train_candidate_ids": train_ids,
        "validation_candidate_policy": "lexicographically-first-example-id-v1",
        "validation_candidate_id": validation_id,
    }
    selection = _self_bound(selection_core, "selection_binding_sha256")

    candidates = [("train", example_id) for example_id in train_ids]
    candidates.append(("validation", validation_id))
    probe_records = []
    for source, example_id in candidates:
        example_sha = _digest({"fixture_example_id": example_id})
        feature_sha = _digest({"fixture_feature_id": example_id})
        candidate_sha = _digest(
            {
                "source": source,
                "example_sha256": example_sha,
                "feature_sha256": feature_sha,
            }
        )
        rank_sha = _digest(
            {
                "method": VERIFIER.ADMISSION_SELECTION_METHOD,
                "selection_binding_sha256": selection["selection_binding_sha256"],
                "candidate_sha256": candidate_sha,
            }
        )
        probe_records.append(
            {
                "source": source,
                "example_id": example_id,
                "example_sha256": example_sha,
                "feature_sha256": feature_sha,
                "candidate_sha256": candidate_sha,
                "rank_sha256": rank_sha,
            }
        )
    probe_records.sort(
        key=lambda record: (record["rank_sha256"], record["candidate_sha256"])
    )
    population = sorted(
        (
            {
                "source": record["source"],
                "example_id": record["example_id"],
                "candidate_sha256": record["candidate_sha256"],
                "rank_sha256": record["rank_sha256"],
            }
            for record in probe_records
        ),
        key=lambda record: (record["candidate_sha256"], record["source"]),
    )
    output_digest = _digest({"fixture": "identical-admitted-policy-outputs"})
    lora = smoke["lora"]
    model = smoke["model"]
    assert isinstance(lora, dict) and isinstance(model, dict)
    adapter_artifacts = lora["adapter_artifacts"]
    tokenizer_artifacts = lora["tokenizer_artifacts"]
    assert isinstance(adapter_artifacts, dict) and isinstance(tokenizer_artifacts, dict)
    adapter_files = adapter_artifacts["files"]
    assert isinstance(adapter_files, dict)
    admission_core = {
        "format": VERIFIER.ADMISSION_FORMAT,
        "v": 1,
        "status": "passed",
        "base_model": {
            "id": model["id"],
            "requested_revision": model["requested_revision"],
            "resolved_snapshot_hash": model["model_commit"],
            "config_sha256": "a" * 64,
            "dtype": "bfloat16",
            "attention": "sdpa",
            "trust_remote_code": False,
        },
        "artifacts": {
            "adapter_sha256": adapter_artifacts["sha256"],
            "adapter_config_sha256": adapter_files[
                "adapter/adapter_config.json"
            ],
            "adapter_safetensors_sha256": adapter_files[
                "adapter/adapter_model.safetensors"
            ],
            "tokenizer_sha256": tokenizer_artifacts["sha256"],
        },
        "probes": {
            "selection_method": VERIFIER.ADMISSION_SELECTION_METHOD,
            "selection_binding_sha256": selection["selection_binding_sha256"],
            "candidate_population_sha256": _digest(population),
            "candidate_count": len(candidates),
            "train_candidate_count": len(train_ids),
            "validation_candidate_count": 1,
            "count": len(candidates),
            "set_sha256": _digest(probe_records),
            "records": probe_records,
            "original_outputs_sha256": output_digest,
            "fresh_outputs_sha256": output_digest,
        },
        "adapter_tensors": {
            "format": VERIFIER.TENSOR_POPULATION_FORMAT,
            "v": 1,
            "tensor_count": 1,
            "names_sha256": "b" * 64,
            "population_sha256": "c" * 64,
            "population_hash_format": VERIFIER.TENSOR_POPULATION_HASH_FORMAT,
        },
        "reload": {
            "base_model_loads": 1,
            "adapter_loads": 1,
            "tokenizer_loads": 1,
            "adapter_safetensor_reads": 1,
            "adapter_name": "default",
            "device": "cuda:0",
        },
        "checks": {
            "tokenizer_encoding_count": len(candidates),
            "exact_reload_count": len(candidates),
            "differs_from_base_count": 1,
        },
        "hash_contract": {
            "algorithm": "sha256",
            "canonicalization": VERIFIER.HASH_CANONICALIZATION,
            "tensor_population": VERIFIER.TENSOR_POPULATION_HASH_FORMAT,
            "projected_logits": VERIFIER.PROJECTED_LOGITS_HASH_FORMAT,
            "output_set": VERIFIER.OUTPUT_SET_HASH_FORMAT,
        },
    }
    smoke["adapter_admission_selection"] = selection
    smoke["adapter_admission"] = _self_bound(admission_core, "content_sha256")


def _rebind_record(record: dict[str, object], field: str) -> None:
    core = dict(record)
    core.pop(field)
    record[field] = _digest(core)


def _rebind_wrong_admission_selection(smoke: dict[str, object]) -> None:
    selection = smoke["adapter_admission_selection"]
    assert isinstance(selection, dict)
    selection["sealed_corpus_eligibility_sha256"] = "0" * 64
    _rebind_record(selection, "selection_binding_sha256")


def _rebind_wrong_admission_tensor_count(smoke: dict[str, object]) -> None:
    admission = smoke["adapter_admission"]
    assert isinstance(admission, dict)
    tensors = admission["adapter_tensors"]
    assert isinstance(tensors, dict)
    tensors["tensor_count"] = 2
    _rebind_record(admission, "content_sha256")


def _bundle(tmp_path: Path) -> dict[str, object]:
    root = tmp_path.resolve()
    config_path = root / VERIFIER.CONFIG_PATH
    prepare_path = root / VERIFIER.PREPARE_SCRIPT
    support_path = root / VERIFIER.SUPPORT_SCRIPT
    config_path.parent.mkdir(parents=True)
    prepare_path.parent.mkdir(parents=True)
    support_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(_config_text(), encoding="utf-8")
    prepare_path.write_text("sealed prepare\n", encoding="utf-8")
    support_path.write_text("support\n", encoding="utf-8")
    current_commit = "c" * 40
    (root / VERIFIER.SOURCE_PROVENANCE).write_text(
        f"{current_commit}\tfalse\t2026-07-30T00:00:00Z\n",
        encoding="utf-8",
    )

    file_sha = hashlib.sha256(prepare_path.read_bytes()).hexdigest()
    support_sha = hashlib.sha256(support_path.read_bytes()).hexdigest()
    composite = hashlib.sha256(f"{file_sha}\n{support_sha}\n".encode("ascii")).hexdigest()
    submission = {
        "timestamp": "2026-07-30T00:01:00+00:00",
        "job_id": "99",
        "script": VERIFIER.PREPARE_SCRIPT.as_posix(),
        "dependency_job_id": "",
        "workdir": str(root),
        "git_commit": current_commit,
        "git_dirty": "false",
        "sync_timestamp": "2026-07-30T00:00:00Z",
        "script_sha256": composite,
    }
    source_sha = hashlib.sha256(
        (root / VERIFIER.SOURCE_PROVENANCE).read_bytes()
    ).hexdigest()
    job = {
        "scheduler": "slurm",
        "job_id": "99",
        "environment": {},
        "deployment": {
            "mode": "slurm",
            "source_sync": {
                "status": "synced",
                "path": VERIFIER.SOURCE_PROVENANCE.as_posix(),
                "sha256": source_sha,
                "git_commit": current_commit,
                "git_dirty": False,
                "synced_at": "2026-07-30T00:00:00Z",
            },
            "job_script": {
                "status": "declared",
                "path": VERIFIER.PREPARE_SCRIPT.as_posix(),
                "file_sha256": file_sha,
                "sha256": composite,
            },
            "support_script": {
                "status": "declared",
                "path": VERIFIER.SUPPORT_SCRIPT.as_posix(),
                "sha256": support_sha,
                "sourced_sha256": support_sha,
            },
        },
        "submission": submission,
        "ledger": {
            "path": "logs/submissions.tsv",
            "row_sha256": _digest(submission),
        },
    }
    eligibility_core: dict[str, object] = {
        "format": "peano-policy-v3-sealed-corpus-eligibility",
        "version": 1,
        "seal": {
            "root": str(root / "checkpoints/corpora/v3-test"),
            "format": "peano-policy-v3-corpus-seal",
            "version": 1,
            "content_sha256": "b" * 64,
            "files_sha256": "d" * 64,
            "historical_source_commit": "a" * 40,
            "historical_prepare_job_id": "172729",
        },
        "historical_attestation": {
            "format": "peano-policy-dataset-attestation",
            "version": 2,
            "independent_replay": True,
            "held_out_contamination": 0,
        },
        "inputs": {
            "train": {
                "configured_path": str(
                    root / "checkpoints/corpora/v3-test/data/train.jsonl"
                ),
                "sealed_path": "data/train.jsonl",
                "bytes": 100,
                "rows": 9000,
                "sha256": "e" * 64,
            },
            "eval": {
                "configured_path": str(
                    root / "checkpoints/corpora/v3-test/data/val.jsonl"
                ),
                "sealed_path": "data/val.jsonl",
                "bytes": 50,
                "rows": 10,
                "sha256": "f" * 64,
            },
            "manifest": {
                "configured_path": str(
                    root / "checkpoints/corpora/v3-test/data/manifest.json"
                ),
                "sealed_path": "data/manifest.json",
                "bytes": 40,
                "sha256": "9" * 64,
            },
        },
        "current_compatibility": {
            "compiler": {"status": "exact-source-inventory-match"},
        },
    }
    corpus = _self_bound(eligibility_core, "eligibility_sha256")
    selection_core = {
        "format": "peano-policy-v3-curriculum-selection",
        "v": 1,
        "algorithm": "catalog-all-schema-anchor-balanced-whole-sessions-v1",
        "seed": "20260729",
        "contract": {
            "library_size": 247,
            "expected_catalog_rows": 8494,
            "root_heads": list(VERIFIER.ROOT_HEADS),
            "schema_count": 51,
            "schema_heads_sha256": VERIFIER.SCHEMA_HEADS_SHA256,
            "synthetic_row_ceiling": 12288,
        },
        "selected": {
            "rows": 8508,
            "catalog": {
                "rows": 8494,
                "sessions": 247,
                "target_count": 247,
                "target_index_range": [0, 246],
            },
            "synthetic": {
                "rows": 14,
                "row_ceiling": 12288,
                "sessions": 14,
                "schema_count": 51,
                "root_head_session_imbalance": 0,
                "root_heads": {
                    head: {"sessions": 1, "rows": 1}
                    for head in VERIFIER.ROOT_HEADS
                },
            },
        },
    }
    selection = _self_bound(selection_core, "selection_sha256")
    curriculum_core = {
        "format": "peano-policy-v3-curriculum",
        "v": 1,
        "source": {
            "train": {
                "name": "train.jsonl",
                "bytes": 100,
                "rows": 9000,
                "sha256": "e" * 64,
            },
            "manifest": {
                "name": "manifest.json",
                "bytes": 40,
                "sha256": "9" * 64,
            },
        },
        "selection": selection,
        "selected": {
            "rows": 8508,
            "selection_sha256": selection["selection_sha256"],
        },
    }
    curriculum = _self_bound(curriculum_core, "curriculum_sha256")
    train_tokens = _token_record("train", rows=8508, maximum=100, total=20000)
    eval_tokens = _token_record("eval", rows=10, maximum=20, total=100)
    tokenizer = train_tokens["tokenizer"]
    config_sha = hashlib.sha256(config_path.read_bytes()).hexdigest()
    eligibility_report = {
        "format": "peano-policy-wmi-v3-sealed-corpus-eligibility",
        "v": 1,
        "status": "passed",
        "config": {"path": str(config_path), "sha256": config_sha},
        "sealed_corpus_eligibility": corpus,
        "job": job,
    }
    token_report = {
        "format": "peano-policy-token-audit",
        "v": 2,
        "status": "passed",
        "config": {
            "path": str(config_path),
            "sha256": config_sha,
            "max_length": 32768,
        },
        "tokenizer": tokenizer,
        "inputs": {
            "train": {
                "path": "checkpoints/corpora/v3-test/data/train.jsonl",
                "bytes": 100,
                "sha256": "e" * 64,
            },
            "eval": {
                "path": "checkpoints/corpora/v3-test/data/val.jsonl",
                "bytes": 50,
                "sha256": "f" * 64,
            },
            "train_manifest": {
                "path": str(
                    root / "checkpoints/corpora/v3-test/data/manifest.json"
                ),
                "bytes": 40,
                "sha256": "9" * 64,
            },
            "eval_manifest": {
                "path": str(
                    root / "checkpoints/corpora/v3-test/data/manifest.json"
                ),
                "bytes": 40,
                "sha256": "9" * 64,
            },
        },
        "sealed_corpus_eligibility": corpus,
        "sealed_dataset_attestation": {
            "format": "peano-policy-dataset-attestation",
            "v": 2,
            "prompt_version": 3,
            "independent_replay": True,
            "held_out_contamination": 0,
            "authority_schedule": {
                "method": "catalog-predecessor-prefix-v1+full-synthetic-v1",
                "library_size": 247,
                "training_prefixes": list(range(248)),
                "inference_prefix": 247,
            },
        },
        "curriculum": curriculum,
        "compute_gates": {
            "max_train_tokens": 100000,
            "max_eval_tokens": 1000,
            "max_train_squared_tokens": 1000000,
            "max_eval_squared_tokens": 10000,
            "max_supervised_tokens": 1024,
        },
        "splits": {
            "train": {
                "rows": 8508,
                "minimum": 2,
                "median": 3,
                "p95": 4,
                "p99": 100,
                "maximum": 100,
                "mean": round(20000 / 8508, 3),
                "budget": 32768,
                "headroom": 32668,
            },
            "eval": {
                "rows": 10,
                "minimum": 2,
                "median": 3,
                "p95": 4,
                "p99": 20,
                "maximum": 20,
                "mean": 10.0,
                "budget": 32768,
                "headroom": 32748,
            },
        },
        "tokenized_splits": {"train": train_tokens, "eval": eval_tokens},
    }
    smoke_report = {
        "format": "peano-policy-wmi-a100-v3-smoke",
        "v": 2,
        "status": "passed",
        "model": {
            "id": "Qwen/Qwen3-1.7B-Base",
            "requested_revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
            "model_commit": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
            "tokenizer_commit": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
        },
        "example": {
            "id": "train:longest",
            "sequence_tokens": 100,
            "selection": "longest-reviewed-curriculum-row",
        },
        "lora": {
            "rank": 32,
            "alpha": 64,
            "dropout": 0.05,
            "target_modules": [
                "q_proj",
                "k_proj",
                "v_proj",
                "o_proj",
                "gate_proj",
                "up_proj",
                "down_proj",
            ],
            "trainable_parameters": 1000,
            "adapter_artifacts": _artifact_group(
                "adapter",
                {
                    "adapter/adapter_config.json": "4" * 64,
                    "adapter/adapter_model.safetensors": "5" * 64,
                },
            ),
            "tokenizer_artifacts": _artifact_group(
                "tokenizer",
                {
                    "tokenizer/tokenizer.json": "a" * 64,
                    "tokenizer/tokenizer_config.json": "b" * 64,
                },
            ),
            "adapter_update": {
                "changed_parameter_tensors": 1,
                "changed_parameter_names_sha256": "6" * 64,
            },
        },
        "loss": {"training": 1.5, "reloaded": 1.25},
        "objective": {
            "format": "peano-completion-only-indexed-logits",
            "v": 1,
            "projection": {"model_argument": "logits_to_keep"},
        },
        "step": {
            "seconds": 1.0,
            "peak_cuda_allocated_bytes": 100,
            "peak_cuda_reserved_bytes": 120,
            "gradient_checkpointing": True,
            "use_cache": False,
            "optimizer": "adamw_torch_fused",
            "gradient_clip_max_norm": 1.0,
            "tf32": True,
            "probe_count": 1,
            "memory_envelope": {
                "probe_id": "train:longest",
                "construction": "natural-row",
                "sequence_tokens": 100,
                "attended_tokens": 100,
                "supervised_tokens": 8,
                "dominance": (
                    "componentwise-maxima-over-tokenized-selected-curriculum"
                ),
            },
        },
        "optimizer": {
            "name": "adamw_torch_fused",
            "betas": [0.9, 0.999],
            "epsilon": 1e-8,
            "learning_rate": 0.0001,
            "weight_decay": 0.01,
            "decay_parameter_tensors": 1,
            "no_decay_parameter_tensors": 0,
        },
        "scheduler": {
            "name": "cosine",
            "train_rows": 8508,
            "dataloader_batches": 8508,
            "updates_per_epoch": 266,
            "total_steps": 266,
            "warmup_steps": 14,
            "initial_learning_rates": [0.0],
            "probe_start_learning_rates": [0.0001],
            "warmup_advance": "optimizer-and-scheduler-steps-with-no-gradients",
        },
        "smoke_probes": [
            {
                "id": "train:longest",
                "roles": [
                    "longest_sequence",
                    "longest_completion",
                    "combined_memory_envelope",
                ],
                "construction": "natural-row",
                "sequence_tokens": 100,
                "attended_tokens": 100,
                "supervised_tokens": 8,
                "projected_positions": 8,
                "training": {
                    "loss": 1.5,
                    "learning_rate": 0.0001,
                    "seconds": 1.0,
                    "peak_cuda_allocated_bytes": 100,
                    "peak_cuda_reserved_bytes": 120,
                    "gradients": {
                        "parameters_with_grad": 1,
                        "norm_before_clip": 0.5,
                        "max_norm": 1.0,
                        "clipped": False,
                    },
                },
                "post_step_eval": {
                    "loss": 1.25,
                    "projected_logits": {
                        "dtype": "torch.bfloat16",
                        "shape": [1, 8, 151936],
                        "sha256": "7" * 64,
                    },
                },
                "reloaded_eval": {
                    "loss": 1.25,
                    "projected_logits": {
                        "dtype": "torch.bfloat16",
                        "shape": [1, 8, 151936],
                        "sha256": "7" * 64,
                    },
                    "exact_match": True,
                },
            }
        ],
        "trainer_integration": {
            "format": "peano-completion-only-trainer-integration",
            "v": 1,
            "trainer": "CompletionOnlyTrainerMixin+transformers.Trainer",
            "train_global_step": 1,
            "training_loss": 1.2,
            "evaluation_loss": 1.1,
            "batch": {
                "role": "componentwise-maximal-memory-envelope",
                "probe_id": "train:longest",
                "construction": "natural-row",
                "sequence_tokens": 100,
                "attended_tokens": 100,
                "supervised_tokens": 8,
                "projected_positions": 8,
            },
            "arguments": {
                "max_steps": 1,
                "per_device_train_batch_size": 1,
                "per_device_eval_batch_size": 1,
                "gradient_accumulation_steps": 1,
                "learning_rate": 0.0001,
                "weight_decay": 0.01,
                "bf16": True,
                "tf32": True,
                "gradient_checkpointing": True,
                "gradient_checkpointing_kwargs": {"use_reentrant": False},
                "warmup_steps": 0,
                "optimizer": "adamw_torch_fused",
                "adam_beta1": 0.9,
                "adam_beta2": 0.999,
                "adam_epsilon": 1e-8,
                "trainer_builtin_clip": "disabled",
                "trainer_builtin_max_grad_norm": 0.0,
                "custom_pre_optimizer_clip": 1.0,
                "custom_pre_optimizer_error_if_nonfinite": True,
                "average_tokens_across_devices": True,
                "logging_nan_inf_filter": False,
                "save_strategy": "no",
                "eval_strategy": "no",
            },
            "gradients": {
                "hook": "on_pre_optimizer_step",
                "raw": {
                    "parameters_with_finite_grad": 1,
                    "parameter_names_sha256": "8" * 64,
                },
                "custom_pre_optimizer_clip": {
                    "max_norm": 1.0,
                    "error_if_nonfinite": True,
                    "norm_before_clip": 0.5,
                    "clipped": False,
                    "postclip": {
                        "parameters_with_finite_grad": 1,
                        "parameter_names_sha256": "8" * 64,
                    },
                },
            },
            "runtime": {
                "format": "peano-completion-only-trainer-runtime",
                "v": 1,
                "num_processes": 1,
                "visible_gpus": 1,
                "device": {"type": "cuda", "index": 0},
                "mixed_precision": "bf16",
                "distributed_type": {"name": "NO", "value": "NO"},
                "dynamo_backend": {"name": "NO", "value": "NO"},
                "plugins": {
                    "deepspeed": False,
                    "fsdp": False,
                    "tensor_parallel": False,
                },
                "manual_trainer_accumulation": True,
                "configured_trainer_gradient_accumulation_steps": 1,
                "accelerator_backward_divisor": 1,
            },
            "adapter_update": {
                "changed_parameter_tensors": 1,
                "changed_parameter_names_sha256": "9" * 64,
            },
            "train_runtime": {
                "seconds": 1.1,
                "peak_cuda_allocated_bytes": 100,
                "peak_cuda_reserved_bytes": 120,
            },
            "evaluation_runtime": {
                "seconds": 0.5,
                "peak_cuda_allocated_bytes": 90,
                "peak_cuda_reserved_bytes": 120,
            },
        },
        "runtime": {
            "machine": "x86_64",
            "packages": {
                "torch": "2.5.1",
                "transformers": "4.53.3",
                "peft": "0.16.0",
            },
            "accelerator": {
                "cuda_available": True,
                "bf16_supported": True,
                "cuda_runtime": "12.4",
                "device_capability": [8, 0],
                "total_memory": 80_000_000_000,
                "nvidia_driver": "570.00",
            },
        },
        "platform_contract": {
            "expected_machine": "x86_64",
            "minimum_cuda_capability": [8, 0],
            "report_format": "peano-policy-wmi-a100-v3-smoke",
        },
        "job": job,
        "corpus_eligibility": corpus,
        "curriculum": curriculum,
        "tokenized_train": train_tokens,
        "tokenized_evaluation": eval_tokens,
    }
    _attach_adapter_admission(smoke_report)
    reports = {
        "eligibility": root / "logs/peano-wmi-v3-sealed-eligibility-99.json",
        "token": root / "logs/peano-wmi-v3-token-audit-99.json",
        "smoke": root / "logs/peano-wmi-v3-prepare-runtime-99.json",
    }
    _write_json(reports["eligibility"], eligibility_report)
    _write_json(reports["token"], token_report)
    _write_json(reports["smoke"], smoke_report)
    return {
        "root": root,
        "reports": reports,
        "eligibility": eligibility_report,
        "token": token_report,
        "smoke": smoke_report,
    }


def _verify(bundle: dict[str, object]) -> dict[str, object]:
    reports = bundle["reports"]
    assert isinstance(reports, dict)
    return VERIFIER.verify_reports(
        eligibility_report=reports["eligibility"],
        token_audit_report=reports["token"],
        smoke_report=reports["smoke"],
        prepare_job_id="99",
        repository_root=bundle["root"],
    )


def test_wmi_v3_sealed_preparation_accepts_one_cross_bound_chain(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path)
    result = _verify(bundle)
    assert result["status"] == "verified"
    assert result["format"] == (
        "peano-policy-wmi-v3-sealed-preparation-verification"
    )
    assert result["v"] == 1
    assert result["prepare_job_id"] == "99"
    assert result["longest_example_id"] == "train:longest"
    assert result["longest_sequence_tokens"] == 100
    assert result["trainer_integration"] == {
        "train_global_step": 1,
        "training_loss": 1.2,
        "evaluation_loss": 1.1,
    }
    assert result["corpus_eligibility_sha256"] == bundle["eligibility"][
        "sealed_corpus_eligibility"
    ]["eligibility_sha256"]
    assert result["eval_token_record_sha256"] == bundle["token"][
        "tokenized_splits"
    ]["eval"]["record_sha256"]
    assert result["adapter_admission_selection_binding_sha256"] == bundle["smoke"][
        "adapter_admission_selection"
    ]["selection_binding_sha256"]
    assert result["adapter_admission_content_sha256"] == bundle["smoke"][
        "adapter_admission"
    ]["content_sha256"]
    for identity in result["reports"].values():
        path = Path(identity["path"])
        assert identity["bytes"] == path.stat().st_size
        assert identity["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_wmi_v3_sealed_preparation_rejects_report_outside_logs(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path)
    reports = bundle["reports"]
    outside = bundle["root"] / reports["eligibility"].name
    shutil.copyfile(reports["eligibility"], outside)
    with pytest.raises(
        VERIFIER.PreparationVerificationError,
        match="repository logs directory",
    ):
        VERIFIER.verify_reports(
            eligibility_report=outside,
            token_audit_report=reports["token"],
            smoke_report=reports["smoke"],
            prepare_job_id="99",
            repository_root=bundle["root"],
        )


def test_wmi_v3_sealed_preparation_accepts_two_probe_active_envelope(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path)
    token_report = copy.deepcopy(bundle["token"])
    smoke_report = copy.deepcopy(bundle["smoke"])
    train_tokens = token_report["tokenized_splits"]["train"]
    train_tokens["supervision"]["longest_example_id"] = "train:completion"
    core = dict(train_tokens)
    core.pop("record_sha256")
    train_tokens["record_sha256"] = _digest(core)
    smoke_report["tokenized_train"] = copy.deepcopy(train_tokens)

    sequence_probe = copy.deepcopy(smoke_report["smoke_probes"][0])
    sequence_probe["roles"] = ["longest_sequence"]
    sequence_probe.pop("construction")
    sequence_probe["supervised_tokens"] = 4
    sequence_probe["projected_positions"] = 4
    sequence_probe["post_step_eval"]["projected_logits"]["shape"] = [1, 4, 151936]
    sequence_probe["reloaded_eval"]["projected_logits"]["shape"] = [1, 4, 151936]

    envelope_probe = copy.deepcopy(smoke_report["smoke_probes"][0])
    envelope_probe.update(
        {
            "id": "train:completion",
            "source_example_id": "train:completion",
            "roles": ["longest_completion", "combined_memory_envelope"],
            "construction": (
                "attended-masked-prompt-extension-to-longest-sequence"
            ),
            "inserted_prompt_tokens": 20,
        }
    )
    envelope_probe["training"]["learning_rate"] = 0.000099
    smoke_report["smoke_probes"] = [sequence_probe, envelope_probe]
    smoke_report["step"].update(
        {
            "seconds": 2.0,
            "probe_count": 2,
            "memory_envelope": {
                "probe_id": "train:completion",
                "construction": (
                    "attended-masked-prompt-extension-to-longest-sequence"
                ),
                "sequence_tokens": 100,
                "attended_tokens": 100,
                "supervised_tokens": 8,
                "dominance": (
                    "componentwise-maxima-over-tokenized-selected-curriculum"
                ),
            },
        }
    )
    smoke_report["trainer_integration"]["batch"].update(
        {
            "probe_id": "train:completion",
            "construction": (
                "attended-masked-prompt-extension-to-longest-sequence"
            ),
        }
    )
    _attach_adapter_admission(smoke_report)
    reports = bundle["reports"]
    assert isinstance(reports, dict)
    _write_json(reports["token"], token_report)
    _write_json(reports["smoke"], smoke_report)

    result = _verify(bundle)
    assert result["status"] == "verified"
    assert result["longest_example_id"] == "train:longest"


def test_wmi_v3_sealed_preparation_rejects_a_rebound_wrong_selector(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path)
    token_report = copy.deepcopy(bundle["token"])
    smoke_report = copy.deepcopy(bundle["smoke"])

    curriculum = token_report["curriculum"]
    selection = curriculum["selection"]
    selection["algorithm"] = "row-level-random-subsample"
    selection_core = dict(selection)
    selection_core.pop("selection_sha256")
    selection["selection_sha256"] = _digest(selection_core)
    curriculum["selected"]["selection_sha256"] = selection["selection_sha256"]
    curriculum_core = dict(curriculum)
    curriculum_core.pop("curriculum_sha256")
    curriculum["curriculum_sha256"] = _digest(curriculum_core)
    smoke_report["curriculum"] = copy.deepcopy(curriculum)

    reports = bundle["reports"]
    assert isinstance(reports, dict)
    _write_json(reports["token"], token_report)
    _write_json(reports["smoke"], smoke_report)
    with pytest.raises(
        VERIFIER.PreparationVerificationError,
        match="whole-session selector contract",
    ):
        _verify(bundle)


@pytest.mark.parametrize(
    ("report_name", "mutation", "message"),
    (
        (
            "eligibility",
            lambda report: report["job"].update({"job_id": "98"}),
            "different Slurm job",
        ),
        (
            "token",
            lambda report: report.update({"v": 1}),
            "wrong v2 contract",
        ),
        (
            "smoke",
            lambda report: report["example"].update({"id": "not-longest"}),
            "did not exercise the longest row",
        ),
        (
            "smoke",
            lambda report: report["tokenized_train"]["sequence"].update(
                {"maximum": 99}
            ),
            "different training tokens",
        ),
        (
            "smoke",
            lambda report: report.pop("tokenized_evaluation"),
            "different evaluation tokens",
        ),
        (
            "smoke",
            lambda report: report["tokenized_evaluation"]["sequence"].update(
                {"maximum": 19}
            ),
            "different evaluation tokens",
        ),
        (
            "smoke",
            lambda report: report.pop("adapter_admission_selection"),
            "adapter admission selection",
        ),
        (
            "smoke",
            _rebind_wrong_admission_selection,
            "differs from admitted corpus/token evidence",
        ),
        (
            "smoke",
            lambda report: report.pop("adapter_admission"),
            "adapter admission evidence",
        ),
        (
            "smoke",
            lambda report: report["adapter_admission"].update(
                {"unexpected": "field"}
            ),
            "malformed exact schema",
        ),
        (
            "smoke",
            lambda report: report["adapter_admission"]["probes"].update(
                {"selection_binding_sha256": "0" * 64}
            ),
            "differs from its admitted selection binding",
        ),
        (
            "smoke",
            lambda report: report["adapter_admission"]["artifacts"].update(
                {"adapter_sha256": "0" * 64}
            ),
            "differs from its saved artifact trees",
        ),
        (
            "smoke",
            lambda report: report["adapter_admission"]["probes"].update(
                {"fresh_outputs_sha256": "0" * 64}
            ),
            "population/output hashes are inconsistent",
        ),
        (
            "smoke",
            lambda report: report["adapter_admission"]["reload"].update(
                {"base_model_loads": 2}
            ),
            "one exact CUDA reload",
        ),
        (
            "smoke",
            _rebind_wrong_admission_tensor_count,
            "tensor population differs from the optimizer",
        ),
        (
            "smoke",
            lambda report: report["smoke_probes"][0].update(
                {"roles": ["longest_sequence", "combined_memory_envelope"]}
            ),
            "natural memory envelope lacks both",
        ),
        (
            "smoke",
            lambda report: report["smoke_probes"][0].update(
                {"attended_tokens": 99}
            ),
            "inactive sequence tokens",
        ),
        (
            "smoke",
            lambda report: report["smoke_probes"][0]["reloaded_eval"][
                "projected_logits"
            ].update({"sha256": "8" * 64}),
            "reload differs",
        ),
        (
            "smoke",
            lambda report: report["smoke_probes"][0]["training"]["gradients"].update(
                {"max_norm": 2.0}
            ),
            "gradient clipping",
        ),
        (
            "smoke",
            lambda report: report["lora"]["adapter_update"].update(
                {"changed_parameter_tensors": 0}
            ),
            "changed adapter tensor count",
        ),
        (
            "smoke",
            lambda report: report["step"].update({"use_cache": True}),
            "reviewed optimizer step",
        ),
        (
            "smoke",
            lambda report: report["step"]["memory_envelope"].update(
                {"sequence_tokens": 99}
            ),
            "reviewed optimizer step",
        ),
        (
            "smoke",
            lambda report: report.pop("trainer_integration"),
            "runtime Trainer integration",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"].update(
                {"train_global_step": 2}
            ),
            "exact CompletionOnlyTrainer lifecycle",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"]["batch"].update(
                {"sequence_tokens": 99}
            ),
            "maximal memory envelope",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"]["arguments"].update(
                {"save_strategy": "steps"}
            ),
            "different bounded arguments",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"]["arguments"].update(
                {
                    "trainer_builtin_clip": "enabled",
                    "trainer_builtin_max_grad_norm": 1.0,
                }
            ),
            "different bounded arguments",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"]["runtime"].update(
                {"accelerator_backward_divisor": 32}
            ),
            "unreviewed Accelerator runtime",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"]["runtime"].update(
                {"mixed_precision": "fp16"}
            ),
            "unreviewed Accelerator runtime",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"]["runtime"].update(
                {"device": {"type": "cpu", "index": 0}}
            ),
            "unreviewed Accelerator runtime",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"]["runtime"].update(
                {"dynamo_backend": {"name": "INDUCTOR", "value": "INDUCTOR"}}
            ),
            "unreviewed Accelerator runtime",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"]["gradients"][
                "raw"
            ].update(
                {"parameters_with_finite_grad": 0}
            ),
            "every LoRA gradient",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"]["gradients"][
                "custom_pre_optimizer_clip"
            ].update({"error_if_nonfinite": False}),
            "strict custom clipping",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"]["gradients"][
                "custom_pre_optimizer_clip"
            ]["postclip"].update({"parameter_names_sha256": "0" * 64}),
            "finite post-clip gradients",
        ),
        (
            "smoke",
            lambda report: report["trainer_integration"]["adapter_update"].update(
                {"changed_parameter_tensors": 0}
            ),
            "changed adapter tensors",
        ),
    ),
)
def test_wmi_v3_sealed_preparation_rejects_mutated_reports(
    tmp_path: Path,
    report_name: str,
    mutation: object,
    message: str,
) -> None:
    bundle = _bundle(tmp_path)
    report = copy.deepcopy(bundle[report_name])
    assert callable(mutation)
    mutation(report)
    reports = bundle["reports"]
    assert isinstance(reports, dict)
    path = reports["token" if report_name == "token" else report_name]
    _write_json(path, report)
    with pytest.raises(VERIFIER.PreparationVerificationError, match=message):
        _verify(bundle)


def test_wmi_v3_sealed_preparation_rejects_config_drift(tmp_path: Path) -> None:
    bundle = _bundle(tmp_path)
    config = bundle["root"] / VERIFIER.CONFIG_PATH
    config.write_text(
        config.read_text(encoding="utf-8").replace(
            "gradient_accumulation_steps = 32",
            "gradient_accumulation_steps = 16",
        ),
        encoding="utf-8",
    )
    with pytest.raises(
        VERIFIER.PreparationVerificationError,
        match="single-epoch A100 schedule",
    ):
        _verify(bundle)


def test_wmi_v3_sealed_preparation_rejects_noncanonical_report(
    tmp_path: Path,
) -> None:
    bundle = _bundle(tmp_path)
    reports = bundle["reports"]
    assert isinstance(reports, dict)
    reports["smoke"].write_text(
        json.dumps(bundle["smoke"], separators=(",", ":")),
        encoding="utf-8",
    )
    with pytest.raises(
        VERIFIER.PreparationVerificationError,
        match="not canonical",
    ):
        _verify(bundle)


def test_eligibility_preflight_binds_config_seal_and_slurm_job(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.toml"
    config_path.write_text("reviewed config\n", encoding="utf-8")
    curriculum = SimpleNamespace(
        corpus_seal_path="checkpoints/corpora/seal",
        corpus_source_commit="a" * 40,
        corpus_prepare_job_id="172729",
        corpus_content_sha256="b" * 64,
    )
    config = SimpleNamespace(
        path=config_path,
        curriculum=curriculum,
        data=SimpleNamespace(
            train_path="checkpoints/corpora/seal/data/train.jsonl",
            eval_path="checkpoints/corpora/seal/data/val.jsonl",
        ),
    )
    calls: list[tuple[object, dict[str, object]]] = []

    def fake_verify(seal: Path, **kwargs: object) -> SimpleNamespace:
        calls.append((seal, kwargs))
        return SimpleNamespace(record={"eligibility_sha256": "c" * 64})

    monkeypatch.setattr(ELIGIBILITY, "verify_sealed_corpus_eligibility", fake_verify)
    monkeypatch.setattr(
        ELIGIBILITY,
        "slurm_job_identity",
        lambda: {"scheduler": "slurm", "job_id": "99"},
    )
    report = ELIGIBILITY.verify_config(config)
    assert report["format"] == ELIGIBILITY.REPORT_FORMAT
    assert report["v"] == 1
    assert report["job"] == {"scheduler": "slurm", "job_id": "99"}
    assert report["sealed_corpus_eligibility"] == {
        "eligibility_sha256": "c" * 64
    }
    assert calls == [
        (
            ELIGIBILITY.REPOSITORY_ROOT / "checkpoints/corpora/seal",
            {
                "configured_train_path": ELIGIBILITY.REPOSITORY_ROOT
                / "checkpoints/corpora/seal/data/train.jsonl",
                "configured_eval_path": ELIGIBILITY.REPOSITORY_ROOT
                / "checkpoints/corpora/seal/data/val.jsonl",
                "historical_source_commit": "a" * 40,
                "historical_prepare_job_id": "172729",
                "sealed_content_sha256": "b" * 64,
            },
        )
    ]


def _standalone_seal_stage(tmp_path: Path) -> tuple[Path, Path, Path, str, str]:
    stage = tmp_path / "private-stage"
    cli = stage / "scripts" / "seal_peano_v3_corpus.py"
    module = stage / "training" / "peano_policy" / "corpus_seal.py"
    cli.parent.mkdir(parents=True)
    module.parent.mkdir(parents=True)
    shutil.copyfile(REPOSITORY_ROOT / "scripts/seal_peano_v3_corpus.py", cli)
    shutil.copyfile(
        REPOSITORY_ROOT / "training/peano_policy/corpus_seal.py",
        module,
    )
    cli_sha256 = hashlib.sha256(cli.read_bytes()).hexdigest()
    module_sha256 = hashlib.sha256(module.read_bytes()).hexdigest()
    return stage, cli, module, cli_sha256, module_sha256


def test_corpus_seal_cli_bootstraps_from_exact_two_source_inventory(
    tmp_path: Path,
) -> None:
    stage, cli, module, cli_sha256, module_sha256 = _standalone_seal_stage(
        tmp_path
    )
    sources = SEAL_CLI._standalone_sources(
        stage,
        cli_sha256=cli_sha256,
        module_sha256=module_sha256,
        _running_cli=cli,
    )
    assert set(sources) == {
        Path("scripts/seal_peano_v3_corpus.py"),
        Path("training/peano_policy/corpus_seal.py"),
    }
    loaded = SEAL_CLI._load_corpus_seal(
        sources[Path("training/peano_policy/corpus_seal.py")],
        module,
    )
    assert loaded.SEAL_FORMAT == "peano-policy-v3-corpus-seal"
    assert not list(stage.rglob("__pycache__"))

    environment = os.environ.copy()
    environment.pop("PYTHONPATH", None)
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-S",
            str(cli),
            "--standalone-root",
            str(stage),
            "--standalone-cli-sha256",
            cli_sha256,
            "--standalone-module-sha256",
            module_sha256,
            "verify",
            "--seal",
            str(stage / "missing-seal"),
        ],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert "Peano v3 corpus seal failed" in completed.stderr
    assert "missing-seal" in completed.stderr
    assert not list(stage.rglob("__pycache__"))


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("package_marker", "inventory differs"),
        ("bytecode_cache", "forbidden bytecode cache"),
        ("source_mutation", "digest mismatch"),
        ("hard_link", "hard-link alias"),
    ),
)
def test_corpus_seal_standalone_inventory_fails_closed(
    tmp_path: Path,
    mutation: str,
    message: str,
) -> None:
    stage, _cli, module, cli_sha256, module_sha256 = _standalone_seal_stage(
        tmp_path
    )
    if mutation == "package_marker":
        (module.parent / "__init__.py").write_text("raise SystemExit\n", encoding="utf-8")
    elif mutation == "bytecode_cache":
        cache = module.parent / "__pycache__"
        cache.mkdir()
        (cache / "corpus_seal.cpython-312.pyc").write_bytes(b"unreviewed")
    elif mutation == "source_mutation":
        module.write_bytes(module.read_bytes() + b"\n# mutation\n")
    else:
        alias_source = tmp_path / "module-alias-source.py"
        alias_source.write_bytes(module.read_bytes())
        module.unlink()
        os.link(alias_source, module)

    with pytest.raises(SEAL_CLI.BootstrapError, match=message):
        SEAL_CLI._standalone_sources(
            stage,
            cli_sha256=cli_sha256,
            module_sha256=module_sha256,
            _running_cli=stage / "scripts" / "seal_peano_v3_corpus.py",
        )


def test_corpus_seal_source_loader_never_executes_package_marker_or_cache(
    tmp_path: Path,
) -> None:
    stage, cli, module, _cli_sha256, _module_sha256 = _standalone_seal_stage(
        tmp_path
    )
    marker = tmp_path / "package-marker-executed"
    (module.parent / "__init__.py").write_text(
        f"from pathlib import Path\nPath({str(marker)!r}).write_text('bad')\n",
        encoding="utf-8",
    )
    cache = module.parent / "__pycache__"
    cache.mkdir()
    (cache / "corpus_seal.cpython-312.pyc").write_bytes(b"not Python bytecode")
    completed = subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-S",
            str(cli),
            "verify",
            "--seal",
            str(stage / "missing-seal"),
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert completed.returncode == 2
    assert "Peano v3 corpus seal failed" in completed.stderr
    assert not marker.exists()
