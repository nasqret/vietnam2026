"""Network-free tests for the Peano Qwen3 training/runtime scaffold."""

from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
TRAINING_ROOT = REPO_ROOT / "training" / "peano_policy"
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from training.peano_policy.config import load_config, validate_config
from training.peano_policy.contract import (
    attested_training_environment,
    environment_record,
    held_out_contract_record,
    held_out_contract_sha256,
    model_v1_environment,
)
from training.peano_policy.data import (
    IGNORE_INDEX,
    ROW_FIELDS,
    example_from_record,
    load_examples,
    tokenize_completion,
)
from training.peano_policy.manifest import (
    artifact_directory_hash,
    hash_files,
    require_safetensors_adapter,
    sha256_file,
    verify_hash_group,
    verify_artifact_directory,
    write_manifest,
)
from training.peano_policy.prompt import (
    PEANO_PROMPT_VERSION,
    CapabilityIdentity,
    PromptEnvironment,
    PromptError,
    ProofExample,
    extract_one_tactic,
    parse_prompt,
    prompt_manifest_record,
    render_prompt,
)
import training.peano_policy.generate as generation
import training.peano_policy.runtime as training_runtime
import training.peano_policy.train as training_run
from peano_lab.batch import capability_sha256, run_proof
from peano_lab.ui.prove import SurfaceCapabilities


CAPABILITIES = CapabilityIdentity(
    label="model-v1",
    allowed_commands=("assumption", "intro", "refl"),
    allowed_theorems=("zero_add",),
)
ENVIRONMENT = PromptEnvironment(False, CAPABILITIES)
GOALS = ("⊢ ∀ n. n + 0 = n",)


class _CharacterTokenizer:
    eos_token_id = 500

    def __call__(self, text: str, *, add_special_tokens: bool) -> dict[str, list[int]]:
        assert add_special_tokens is False
        return {"input_ids": [ord(character) for character in text]}


def _builder_row(
    *,
    split: str = "train",
    step: int = 1,
    tactic: str = "refl",
) -> dict[str, object]:
    """Construct the exact public row emitted by the replay compiler."""

    row = {
        "v": 1,
        "task": "next_tactic",
        "env": ENVIRONMENT.text,
        "surface": "model-v1",
        "environment_sha256": ENVIRONMENT.sha256,
        "classical": False,
        "capabilities": CAPABILITIES.to_record(),
        "split": split,
        "session": "checked-session",
        "step": step,
        "formula": "forall n. n + 0 = n",
        "theorem": "add_zero",
        "family": "addition-identity",
        "lineage": "addition-identity/add-zero/seed-1",
        "state": list(GOALS),
        "focus": 0,
        "prompt": render_prompt(goals=GOALS, focus=0, environment=ENVIRONMENT),
        "completion": tactic + "</tactic>",
        "metadata": {"generator": "unit-test"},
    }
    assert tuple(row) == ROW_FIELDS
    return row


def _valid_training_inputs() -> dict[str, object]:
    train_hash = "1" * 64
    val_hash = "2" * 64
    manifest_hash = "3" * 64
    return {
        "dataset_attestation": {
            "format": "peano-policy-dataset-attestation",
            "v": 1,
            "independent_replay": True,
            "held_out_contamination": 0,
            "held_out_contract": held_out_contract_record(),
            "held_out_contract_sha256": held_out_contract_sha256(),
            "environment": environment_record(model_v1_environment()),
            "manifest_sha256": manifest_hash,
            "splits": {
                "train": {"rows": 1, "sha256": train_hash},
                "val": {"rows": 1, "sha256": val_hash},
                "test": {"rows": 0, "sha256": "4" * 64},
            },
        },
        "train_data": {"sha256": train_hash},
        "eval_data": {"sha256": val_hash},
        "train_dataset_manifest": {"sha256": manifest_hash},
        "eval_dataset_manifest": {"sha256": manifest_hash},
    }


def _jsonl(rows: list[dict[str, object]]) -> bytes:
    return b"".join(
        (
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
        ).encode("utf-8")
        for row in rows
    )


def _write_builder_dataset(
    root: Path,
    *,
    train_rows: list[dict[str, object]],
    replay_accepted: int = 1,
) -> Path:
    rows_by_split = {"train": train_rows, "val": [], "test": []}
    split_records: dict[str, dict[str, object]] = {}
    for split, rows in rows_by_split.items():
        payload = _jsonl(rows)
        (root / f"{split}.jsonl").write_bytes(payload)
        split_records[split] = {
            "groups": [],
            "sessions": 1 if rows else 0,
            "rows": len(rows),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    manifest = {
        "format": "peano-lab-next-tactic",
        "version": 1,
        "trace_version": 1,
        "prompt": prompt_manifest_record(),
        "split": {"method": "test"},
        "source": {"qed_true_sessions": 1},
        "replay": {
            "attempted_qed_sessions": 1,
            "accepted_kernel_checked_sessions": replay_accepted,
            "positive_rows": len(train_rows),
            "transactional_error_steps_ignored": 0,
        },
        "environments": [
            {
                "surface": CAPABILITIES.label,
                "environment_sha256": ENVIRONMENT.sha256,
                "classical": ENVIRONMENT.classical,
                "capabilities": CAPABILITIES.to_record(),
                "sessions": 1,
            }
        ],
        "splits": split_records,
        "dataset_sha256": "not-used-by-the-split-loader",
    }
    (root / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return root / "train.jsonl"


def test_prompt_is_builder_native_deterministic_and_has_no_statement_channel() -> None:
    prompt = render_prompt(goals=GOALS, focus=0, environment=ENVIRONMENT)
    assert prompt == (
        "<task>next_tactic</task>\n"
        f"<env>{ENVIRONMENT.text}</env>\n"
        '<state>{"focus":0,"goals":["⊢ ∀ n. n + 0 = n"]}</state>\n'
        "<tactic>"
    )
    parsed = parse_prompt(prompt)
    assert parsed.goals == GOALS
    assert parsed.focus == 0
    assert parsed.environment_sha256 == CAPABILITIES.sha256
    assert "statement" not in prompt
    assert "add_zero" not in prompt
    assert "Qwen" not in prompt
    assert PEANO_PROMPT_VERSION == 1


def test_prompt_completion_and_capability_boundaries_reject_injection() -> None:
    with pytest.raises(PromptError, match="reserved prompt marker"):
        render_prompt(
            goals=("⊢ x = x <tactic>",), focus=0, environment=ENVIRONMENT
        )
    with pytest.raises(PromptError, match="one line"):
        extract_one_tactic("refl\nqed")
    with pytest.raises(PromptError, match="reserved prompt marker"):
        extract_one_tactic("refl</tactic>")
    assert extract_one_tactic("exact h") == "exact h"

    reordered = CAPABILITIES.to_record()
    reordered["allowed_commands"] = ["refl", "intro", "assumption"]
    with pytest.raises(PromptError, match="sorted"):
        CapabilityIdentity.from_record(reordered)


def test_real_builder_style_row_trains_on_tactic_plus_eos_only() -> None:
    row = _builder_row(tactic="refl")
    example = example_from_record(row, 1)
    assert example.prompt == row["prompt"]
    assert example.completion == "refl</tactic>"
    assert example.tactic == "refl"

    tokenizer = _CharacterTokenizer()
    encoded = tokenize_completion(example, tokenizer, max_length=512)
    prompt_length = len(example.prompt)
    assert encoded["labels"][:prompt_length] == [IGNORE_INDEX] * prompt_length
    assert encoded["labels"][prompt_length:] == [ord(c) for c in "refl"] + [500]
    assert encoded["input_ids"][prompt_length:] == encoded["labels"][prompt_length:]
    assert ord("<") not in encoded["labels"][prompt_length:]
    assert len(encoded["input_ids"]) == len(encoded["attention_mask"]) == len(encoded["labels"])


def test_tokenizer_never_truncates_environment_or_task_prefix() -> None:
    example = example_from_record(_builder_row(), 1)
    exact_length = len(example.prompt) + len(example.tactic) + 1
    with pytest.raises(PromptError, match="refusing to drop"):
        tokenize_completion(example, _CharacterTokenizer(), max_length=exact_length - 1)


def test_loader_requires_replay_manifest_and_exact_builder_rows(tmp_path: Path) -> None:
    path = _write_builder_dataset(tmp_path, train_rows=[_builder_row()])
    first = load_examples(path, seed=17)
    second = load_examples(path, seed=17)
    assert first == second
    assert first[0].tactic == "refl"
    assert first[0].example_id == "checked-session:1"

    raw_dir = tmp_path / "raw"
    raw_dir.mkdir()
    raw_path = raw_dir / "train.jsonl"
    raw_path.write_text(
        json.dumps(
            {
                "v": 1,
                "session": "unfinished",
                "step": 1,
                "goals_before": ["⊢ x = x"],
                "focus": 0,
                "tactic": "refl",
                "goals_after": [],
                "status": "ok",
                "error": None,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(PromptError, match="raw trace-v1"):
        load_examples(raw_path)


def test_loader_accepts_a_manifest_bound_empty_optional_split(tmp_path: Path) -> None:
    _write_builder_dataset(tmp_path, train_rows=[_builder_row()])
    assert load_examples(tmp_path / "val.jsonl") == []
    assert load_examples(tmp_path / "test.jsonl") == []


def test_loader_samples_large_splits_deterministically_without_skipping_validation(
    tmp_path: Path,
) -> None:
    rows = [_builder_row(step=index) for index in range(1, 21)]
    path = _write_builder_dataset(tmp_path, train_rows=rows)
    first = load_examples(path, max_samples=4, seed=17)
    second = load_examples(path, max_samples=4, seed=17)
    other = load_examples(path, max_samples=4, seed=18)
    assert len(first) == 4
    assert first == second
    assert {item.example_id for item in first} != {
        item.example_id for item in other
    }

    decoded = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    unsampled = next(
        row for row in decoded if f"checked-session:{row['step']}" not in {
            item.example_id for item in first
        }
    )
    unsampled["completion"] = "bad\nline</tactic>"
    payload = _jsonl(decoded)
    path.write_bytes(payload)
    manifest_path = tmp_path / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["splits"]["train"]["sha256"] = hashlib.sha256(payload).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(PromptError, match="one line"):
        load_examples(path, max_samples=4, seed=17)


def test_loader_consumes_actual_replay_compiler_artifacts(tmp_path: Path) -> None:
    capabilities = SurfaceCapabilities()
    result = run_proof(
        "0 = 0",
        ("refl",),
        request_id="runtime-integration",
        session_id="runtime-integration",
        capabilities=capabilities,
    )
    assert result.kernel_checked is True and result.trace is not None
    raw = tmp_path / "raw.jsonl"
    raw.write_text(
        "".join(
            json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n"
            for record in result.trace
        ),
        encoding="utf-8",
    )
    metadata = tmp_path / "metadata.jsonl"
    metadata.write_text(
        json.dumps(
            {
                "session": "runtime-integration",
                "theorem": "zero_refl",
                "family": "reflexivity",
                "lineage": "reflexivity/zero",
                "classical": False,
                "surface": "full",
                "environment_sha256": capability_sha256(capabilities),
                "capabilities": {
                    "label": "full",
                    "allowed_commands": None,
                    "allowed_theorems": None,
                },
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "compiled"
    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "build_peano_policy_dataset.py"),
            str(raw),
            "--metadata",
            str(metadata),
            "--output-dir",
            str(output),
            "--val-fraction",
            "0",
            "--test-fraction",
            "0",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "train=1" in completed.stdout
    examples = load_examples(output / "train.jsonl")
    assert len(examples) == 1
    assert examples[0].tactic == "refl"
    assert "zero_refl" not in examples[0].prompt


def test_loader_rejects_tampering_and_missing_qed_replay(tmp_path: Path) -> None:
    row = _builder_row()
    row["prompt"] = str(row["prompt"]).replace("focus\":0", "focus\":1")
    with pytest.raises(PromptError, match="stored prompt"):
        example_from_record(row, 1)

    rejected = tmp_path / "rejected"
    rejected.mkdir()
    path = _write_builder_dataset(
        rejected,
        train_rows=[_builder_row()],
        replay_accepted=0,
    )
    with pytest.raises(PromptError, match="survived checked replay"):
        load_examples(path)

    accepted = tmp_path / "accepted"
    accepted.mkdir()
    path = _write_builder_dataset(accepted, train_rows=[_builder_row()])
    path.write_text(path.read_text(encoding="utf-8").replace("refl", "simp", 1), encoding="utf-8")
    with pytest.raises(PromptError, match="split hash"):
        load_examples(path)


@pytest.mark.parametrize(
    ("name", "model_id", "rank", "max_steps"),
    [
        ("qwen3_1_7b_smoke.toml", "Qwen/Qwen3-1.7B-Base", 8, 100),
        ("qwen3_4b_pilot.toml", "Qwen/Qwen3-4B-Base", 16, -1),
        (
            "pythagoras_4b_pilot.toml",
            "Pythagoras-LM/Pythagoras-Prover-4B",
            16,
            -1,
        ),
    ],
)
def test_cli_configs_pin_bf16_sdpa_lora_and_builder_dataset(
    name: str, model_id: str, rank: int, max_steps: int
) -> None:
    config = load_config(TRAINING_ROOT / "configs" / name)
    assert config.model.model_id == model_id
    assert config.model.dtype == "bfloat16"
    assert config.model.attn_implementation == "sdpa"
    assert config.model.trust_remote_code is False
    assert len(config.model.revision) == 40
    assert config.model.revision != "main"
    assert config.lora.rank == rank
    assert config.trainer.max_steps == max_steps
    assert config.run.seed == 20260728
    assert config.run.resume == "auto"
    assert config.data.train_path == "data/peano-policy-v1/train.jsonl"
    assert not hasattr(config.data, "accepted_statuses")


def test_reviewed_model_id_cannot_be_repointed_to_an_unreviewed_commit() -> None:
    from dataclasses import replace

    config = load_config(TRAINING_ROOT / "configs" / "qwen3_1_7b_smoke.toml")
    changed = replace(
        config,
        model=replace(config.model, revision="0" * 40),
    )
    with pytest.raises(ValueError, match="reviewed Peano pilot snapshot"):
        validate_config(changed)


def test_adapter_loader_rejects_divergent_model_and_tokenizer_snapshots_before_load(
    tmp_path: Path,
) -> None:
    requested = "1" * 40
    manifest = {
        "v": generation.MANIFEST_VERSION,
        "prompt_version": PEANO_PROMPT_VERSION,
        "prompt_contract_sha256": generation.sha256_json(prompt_manifest_record()),
        "base_model": {
            "id": "Qwen/Qwen3-1.7B-Base",
            "requested_revision": requested,
            "resolved_snapshot_hash": "2" * 40,
        },
        "tokenizer": {
            "resolved_snapshot_hash": requested,
            "artifacts": {},
        },
        "adapter": {},
        "inputs": _valid_training_inputs(),
    }
    (tmp_path / "training-manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )

    with pytest.raises(ValueError, match="one pinned commit"):
        generation.load_adapter(tmp_path, seed=0)


def test_training_attestation_cannot_launder_a_different_policy_environment() -> None:
    valid = {"inputs": _valid_training_inputs()}
    assert attested_training_environment(valid) == model_v1_environment()

    forged = json.loads(json.dumps(valid))
    forged["inputs"]["dataset_attestation"]["environment"]["surface"] = "full"
    with pytest.raises(ValueError, match="hash/preimage mismatch"):
        attested_training_environment(forged)

    contaminated = json.loads(json.dumps(valid))
    contaminated["inputs"]["dataset_attestation"]["held_out_contamination"] = 1
    with pytest.raises(ValueError, match="invalid or contaminated"):
        attested_training_environment(contaminated)


def test_manifest_hashes_are_path_bound_and_write_is_canonical(tmp_path: Path) -> None:
    left = tmp_path / "left.txt"
    right = tmp_path / "right.txt"
    left.write_text("same", encoding="utf-8")
    right.write_text("same", encoding="utf-8")
    digest = hash_files(tmp_path, [right, left])
    assert digest["files"] == {
        "left.txt": sha256_file(left),
        "right.txt": sha256_file(right),
    }
    destination = tmp_path / "manifest.json"
    write_manifest(destination, {"z": 1, "a": digest})
    text = destination.read_text(encoding="utf-8")
    assert text.endswith("\n")
    assert text.index('"a"') < text.index('"z"')
    assert not list(tmp_path.glob(".manifest.json.*.tmp"))
    verify_hash_group(tmp_path, digest)
    left.write_text("mutated", encoding="utf-8")
    with pytest.raises(ValueError, match="hash mismatch"):
        verify_hash_group(tmp_path, digest)


def test_loader_artifact_manifest_must_cover_its_complete_closed_directory(
    tmp_path: Path,
) -> None:
    adapter = tmp_path / "adapter"
    adapter.mkdir()
    (adapter / "adapter_config.json").write_text("{}", encoding="utf-8")
    (adapter / "adapter_model.safetensors").write_bytes(b"weights")
    complete = artifact_directory_hash(tmp_path, "adapter")
    assert verify_artifact_directory(tmp_path, complete, "adapter") == adapter

    incomplete = dict(complete)
    incomplete["files"] = {
        "adapter/adapter_config.json": complete["files"][
            "adapter/adapter_config.json"
        ]
    }
    incomplete["sha256"] = hash_files(
        tmp_path, [adapter / "adapter_config.json"]
    )["sha256"]
    with pytest.raises(ValueError, match="complete adapter directory"):
        verify_artifact_directory(tmp_path, incomplete, "adapter")

    (adapter / "unreported.bin").write_bytes(b"surprise")
    with pytest.raises(ValueError, match="complete adapter directory"):
        verify_artifact_directory(tmp_path, complete, "adapter")


def test_adapter_loader_rejects_peft_pickle_fallback_artifacts() -> None:
    safe = {
        "files": {
            "adapter/adapter_config.json": "a" * 64,
            "adapter/adapter_model.safetensors": "b" * 64,
        }
    }
    require_safetensors_adapter(safe)

    with pytest.raises(ValueError, match="exactly adapter_model.safetensors"):
        require_safetensors_adapter(
            {"files": {"adapter/adapter_config.json": "a" * 64}}
        )
    with pytest.raises(ValueError, match="pickle-compatible"):
        require_safetensors_adapter(
            {
                "files": {
                    **safe["files"],
                    "adapter/adapter_model.bin": "c" * 64,
                }
            }
        )


def test_run_identity_gates_and_hashes_checkpoint_resume(tmp_path: Path) -> None:
    output = tmp_path / "run"
    output.mkdir()
    identity = {"v": 1, "experiment": "same"}
    path, digest = training_run._ensure_run_identity(output, identity)
    assert path.name == "run-identity.json"
    assert digest == sha256_file(path)
    assert training_run._ensure_run_identity(output, identity)[1] == digest
    with pytest.raises(ValueError, match="different training identity"):
        training_run._ensure_run_identity(
            output, {"v": 1, "experiment": "other"}
        )

    checkpoint = output / "checkpoint-25"
    checkpoint.mkdir()
    (checkpoint / "trainer_state.json").write_text(
        json.dumps({"global_step": 25}), encoding="utf-8"
    )
    (checkpoint / "adapter_model.safetensors").write_bytes(b"checkpoint")
    decision = training_run._resume_decision(
        output,
        "auto",
        lambda _: str(checkpoint),
        run_identity_sha256=digest,
    )
    assert decision.trainer_value == str(checkpoint.resolve())
    assert decision.checkpoint == str(checkpoint.resolve())
    assert decision.global_step == 25
    assert decision.checkpoint_sha256 is not None

    path.write_text(
        json.dumps({"v": 1, "experiment": "forged"}), encoding="utf-8"
    )
    with pytest.raises(ValueError, match="checkpoint training identity"):
        training_run._resume_decision(
            output,
            str(checkpoint),
            lambda _: None,
            run_identity_sha256=digest,
        )


def test_resume_never_requires_a_fresh_output_directory(tmp_path: Path) -> None:
    output = tmp_path / "one-shot"
    output.mkdir()
    (output / "run-identity.json").write_text("{}\n", encoding="utf-8")

    decision = training_run._resume_decision(
        output,
        "never",
        lambda _: pytest.fail("resume=never must not inspect checkpoints"),
        run_identity_sha256="0" * 64,
    )
    assert decision == training_run.ResumeDecision(False, None, None, None)

    (output / "checkpoint-1").mkdir()
    with pytest.raises(ValueError, match="requires a fresh output directory"):
        training_run._resume_decision(
            output,
            "never",
            lambda _: None,
            run_identity_sha256="0" * 64,
        )


def test_one_shot_freshness_guard_runs_before_identity_mutation(tmp_path: Path) -> None:
    output = tmp_path / "one-shot"
    training_run._require_fresh_one_shot_output(output, "never")
    output.mkdir()
    training_run._require_fresh_one_shot_output(output, "never")
    (output / "run-identity.json").write_text("{}\n", encoding="utf-8")
    with pytest.raises(ValueError, match="requires a fresh output directory"):
        training_run._require_fresh_one_shot_output(output, "never")
    training_run._require_fresh_one_shot_output(output, "auto")


def test_hf_model_loading_and_training_checkpoints_are_safetensors_only() -> None:
    def calls(path: Path, owner: str, method: str) -> list[ast.Call]:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        return [
            node
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == method
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == owner
        ]

    expected_model_loads = {
        "train.py": 1,
        "smoke.py": 2,
        "generate.py": 1,
    }
    for name, expected_count in expected_model_loads.items():
        model_loads = calls(
            TRAINING_ROOT / name,
            "AutoModelForCausalLM",
            "from_pretrained",
        )
        assert len(model_loads) == expected_count
        for model_load in model_loads:
            keyword = next(
                (
                    item
                    for item in model_load.keywords
                    if item.arg == "use_safetensors"
                ),
                None,
            )
            assert keyword is not None
            assert isinstance(keyword.value, ast.Constant)
            assert keyword.value.value is True

    training_arguments = [
        node
        for node in ast.walk(
            ast.parse(
                (TRAINING_ROOT / "train.py").read_text(encoding="utf-8"),
                filename=str(TRAINING_ROOT / "train.py"),
            )
        )
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "TrainingArguments"
    ]
    assert len(training_arguments) == 1
    save_keyword = next(
        (
            item
            for item in training_arguments[0].keywords
            if item.arg == "save_safetensors"
        ),
        None,
    )
    assert save_keyword is not None
    assert isinstance(save_keyword.value, ast.Constant)
    assert save_keyword.value.value is True

    train_source = (TRAINING_ROOT / "train.py").read_text(encoding="utf-8")
    assert "trainer.save_model" not in train_source
    peft_saves = calls(TRAINING_ROOT / "train.py", "model", "save_pretrained")
    assert len(peft_saves) == 1
    safe_keyword = next(
        (item for item in peft_saves[0].keywords if item.arg == "safe_serialization"),
        None,
    )
    assert safe_keyword is not None
    assert isinstance(safe_keyword.value, ast.Constant)
    assert safe_keyword.value.value is True


def test_slurm_runtime_identity_joins_exact_submission_and_source(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    slurm = tmp_path / "slurm"
    logs = tmp_path / "logs"
    training = tmp_path / "training" / "peano_policy"
    slurm.mkdir()
    logs.mkdir()
    training.mkdir(parents=True)
    script = slurm / "job.sbatch"
    script.write_text("#!/bin/bash\ntrue\n", encoding="utf-8")
    requirements = training / "requirements-helios.lock"
    requirements.write_text("transformers==4.53.3\n", encoding="utf-8")
    source = tmp_path / ".peano-source-provenance.tsv"
    commit = "a" * 40
    synced_at = "2026-07-28T10:11:12Z"
    source.write_text(f"{commit}\ttrue\t{synced_at}\n", encoding="utf-8")
    ledger = logs / "submissions.tsv"
    row = (
        "2026-07-28T10:12:00+00:00",
        "424242",
        "slurm/job.sbatch",
        "12345",
        str(tmp_path),
        commit,
        "true",
        synced_at,
        sha256_file(script),
    )
    ledger.write_text(
        "\t".join(training_runtime.SUBMISSION_FIELDS)
        + "\n"
        + "\t".join(row)
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(training_runtime, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(training_runtime, "SOURCE_PROVENANCE_PATH", source)
    monkeypatch.setattr(training_runtime, "SUBMISSION_LEDGER_PATH", ledger)
    monkeypatch.setattr(training_runtime, "REQUIREMENTS_PATH", requirements)
    monkeypatch.setenv("SLURM_JOB_ID", "424242")
    monkeypatch.setenv("SLURM_SUBMIT_DIR", str(tmp_path))
    monkeypatch.setenv("PEANO_JOB_SCRIPT", "slurm/job.sbatch")
    monkeypatch.setenv("SLURM_JOB_NODELIST", "nid[001-002]")
    monkeypatch.setenv("PEANO_HELIOS_ML_MODULE", "ML-bundle/25.10")
    monkeypatch.setenv("LOADEDMODULES", "gcc/13.2.0:ML-bundle/25.10")

    identity = training_runtime.slurm_job_identity()
    assert identity["scheduler"] == "slurm"
    assert identity["submission"]["dependency_job_id"] == "12345"
    assert identity["deployment"]["source_sync"]["git_commit"] == commit
    assert identity["deployment"]["modules"] == {
        "status": "loaded",
        "requested": "ML-bundle/25.10",
        "loaded_modules": ["gcc/13.2.0", "ML-bundle/25.10"],
    }
    assert identity["deployment"]["job_script"] == {
        "status": "declared",
        "path": "slurm/job.sbatch",
        "sha256": sha256_file(script),
    }
    assert identity["ledger"]["row_sha256"]
    assert training_runtime.runtime_identity()["requirements"]["sha256"] == (
        sha256_file(requirements)
    )

    script.write_text("#!/bin/bash\nfalse\n", encoding="utf-8")
    with pytest.raises(ValueError, match="does not match"):
        training_runtime.slurm_job_identity()


def test_runtime_imports_are_lazy_and_stack_has_no_accelerator_extensions() -> None:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(REPO_ROOT)
    code = (
        "import sys; "
        "import training.peano_policy.train; "
        "import training.peano_policy.generate; "
        "assert 'torch' not in sys.modules; "
        "assert 'transformers' not in sys.modules; "
        "assert 'peft' not in sys.modules"
    )
    subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    for module, expected in (
        ("training.peano_policy.train", "--resume-from-checkpoint"),
        ("training.peano_policy.generate", "--prompt-file"),
        ("training.peano_policy.smoke", "--config"),
    ):
        help_run = subprocess.run(
            [sys.executable, "-m", module, "--help"],
            cwd=REPO_ROOT,
            env=environment,
            check=True,
            capture_output=True,
            text=True,
        )
        assert expected in help_run.stdout
    evaluator_help = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "eval_trained_peano_policy.py"),
            "--help",
        ],
        cwd=REPO_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "--adapter" in evaluator_help.stdout
    requirements = (TRAINING_ROOT / "requirements-helios.lock").read_text(encoding="utf-8").lower()
    pins = [
        line.split(";", 1)[0].strip()
        for line in requirements.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert all(pin.count("==") == 1 for pin in pins)
    package_names = {pin.split("==", 1)[0] for pin in pins}
    assert len(package_names) == len(pins)
    assert package_names == {
        "accelerate",
        "certifi",
        "charset-normalizer",
        "filelock",
        "fsspec",
        "hf-xet",
        "huggingface-hub",
        "idna",
        "jinja2",
        "markupsafe",
        "mpmath",
        "networkx",
        "numpy",
        "packaging",
        "peft",
        "pip",
        "psutil",
        "pyyaml",
        "regex",
        "requests",
        "safetensors",
        "setuptools",
        "sympy",
        "tokenizers",
        "tomli",
        "torch",
        "tqdm",
        "transformers",
        "typing-extensions",
        "urllib3",
    }
    assert "transformers==" in requirements
    assert "peft==" in requirements
    assert "accelerate==" in requirements
    assert "huggingface-hub==" in requirements
    assert "tokenizers==" in requirements
    assert "torch==2.9.1+cu129" in requirements
    for forbidden in ("vllm", "flash-attn", "flash_attn", "bitsandbytes"):
        assert forbidden not in requirements


def test_evaluator_adapter_uses_exact_environment_and_returns_bare_tactic(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    observed: dict[str, object] = {}

    def fake_generate(**kwargs: object) -> str:
        observed.update(kwargs)
        return extract_one_tactic("refl")

    monkeypatch.setattr(generation, "generate_one_tactic", fake_generate)
    adapter = generation.PeanoPolicyAdapter(
        model=object(),
        tokenizer=object(),
        environment=ENVIRONMENT,
    )
    result = adapter.propose(
        GOALS,
        sample=3,
        step=4,
        rng=random.Random(7),
    )
    assert result == "refl"
    assert "</tactic>" not in result
    assert observed["prompt"] == _builder_row()["prompt"]
    assert "statement" not in observed
    assert "proof_state" not in observed
    assert adapter.policy_environment == {
        "classical": False,
        "surface": "model-v1",
        "environment_sha256": ENVIRONMENT.sha256,
        "capabilities": CAPABILITIES.to_record(),
    }
    assert adapter.evaluation_identity["decoding"] == {
        "max_new_tokens": 64,
        "do_sample": False,
        "temperature": 0.8,
        "top_p": 0.95,
    }

    other = generation.PeanoPolicyAdapter(
        model=object(),
        tokenizer=object(),
        environment=ENVIRONMENT,
        provenance={"adapter_sha256": "different"},
    )
    assert adapter.evaluation_identity != other.evaluation_identity


def test_training_source_pins_provenance_resume_and_one_line_stopping() -> None:
    train_source = (TRAINING_ROOT / "train.py").read_text(encoding="utf-8")
    generation_source = (TRAINING_ROOT / "generate.py").read_text(encoding="utf-8")
    assert "torch_dtype=torch.bfloat16" in train_source
    assert "attn_implementation=config.model.attn_implementation" in train_source
    assert "resume_from_checkpoint=resume.trainer_value" in train_source
    assert '"run_identity"' in train_source
    assert "checkpoint_sha256" in train_source
    assert '"generation": asdict(config.generation)' in train_source
    assert '"train_data"' in train_source
    assert '"eval_data"' in train_source
    assert '"train_dataset_manifest"' in train_source
    assert '"eval_dataset_manifest"' in train_source
    assert '"config"' in train_source
    assert '"source"' in train_source
    assert '"deployment"' in train_source
    assert "runtime_identity(torch)" in train_source
    assert "slurm_job_identity()" in train_source
    assert '"resolved_snapshot_hash"' in train_source
    assert '"adapter"' in train_source
    assert '"tokenizer"' in train_source
    assert 'return "\\n" in tail or "\\r" in tail' in generation_source
    assert "return extract_one_tactic(generated)" in generation_source
