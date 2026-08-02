"""Model-free contracts for the same-authority pretrained-base comparison."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType, SimpleNamespace
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "eval_pretrained_peano_policy.py"
SPEC = importlib.util.spec_from_file_location("_pretrained_baseline_cli", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CLI = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CLI
SPEC.loader.exec_module(CLI)

from training.peano_policy import pretrained_baseline as baseline  # noqa: E402
from training.peano_policy.adapter_admission import (  # noqa: E402
    ADMISSION_FORMAT,
    ADMISSION_VERSION,
    HASH_CANONICALIZATION as ADMISSION_CANONICALIZATION,
    OUTPUT_SET_HASH_FORMAT,
    PROBE_SELECTION_METHOD,
    PROJECTED_LOGITS_HASH_FORMAT,
    TENSOR_POPULATION_FORMAT,
    TENSOR_POPULATION_HASH_FORMAT,
    TENSOR_POPULATION_VERSION,
)
from training.peano_policy.contract import (  # noqa: E402
    environment_record,
    held_out_contract_record,
    held_out_contract_sha256,
    model_v3_environment,
)
from training.peano_policy.generate import (  # noqa: E402
    PRETRAINED_BASE_POLICY_KIND,
    PeanoPolicyAdapter,
    PeanoPolicyCandidateAdapter,
    PeanoPretrainedBasePolicy,
)
from training.peano_policy.manifest import (  # noqa: E402
    artifact_directory_hash,
    sha256_json,
)
from training.peano_policy.prompt import prompt_contract_sha256  # noqa: E402
from training.peano_policy.training_evidence import (  # noqa: E402
    FiniteGradientAudit,
    adapter_update_audit_record,
    completed_training_evidence_record,
    reviewed_trainer_arguments_record,
)


REVISION = baseline.EXPECTED_BASE_MODEL_REVISION
MANIFEST_SHA = "f" * 64


def _artifact(root: str, filename: str) -> dict[str, object]:
    files = {f"{root}/{filename}": "b" * 64}
    if root == "adapter":
        files["adapter/adapter_config.json"] = "c" * 64
    return {
        "root": root,
        "sha256": "a" * 64,
        "files": files,
    }


def _trainer_runtime() -> dict[str, object]:
    return {
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
        "configured_trainer_gradient_accumulation_steps": 32,
        "accelerator_backward_divisor": 1,
    }


def _attach_adapter_admission(manifest: dict[str, object]) -> None:
    binding = "9" * 64
    raw_records = []
    for source, example_hash, feature_hash in (
        ("train", "1" * 64, "2" * 64),
        ("validation", "3" * 64, "4" * 64),
    ):
        candidate = sha256_json(
            {
                "source": source,
                "example_sha256": example_hash,
                "feature_sha256": feature_hash,
            }
        )
        rank = sha256_json(
            {
                "method": PROBE_SELECTION_METHOD,
                "selection_binding_sha256": binding,
                "candidate_sha256": candidate,
            }
        )
        raw_records.append(
            {
                "source": source,
                "example_id": f"{source}-probe",
                "example_sha256": example_hash,
                "feature_sha256": feature_hash,
                "candidate_sha256": candidate,
                "rank_sha256": rank,
            }
        )
    records = sorted(
        raw_records,
        key=lambda record: (record["rank_sha256"], record["candidate_sha256"]),
    )
    adapter = manifest["adapter"]
    tokenizer = manifest["tokenizer"]["artifacts"]
    base = manifest["base_model"]
    runtime = manifest["runtime"]
    outputs = "5" * 64
    evidence = {
        "format": ADMISSION_FORMAT,
        "v": ADMISSION_VERSION,
        "status": "passed",
        "base_model": {
            "id": base["id"],
            "requested_revision": base["requested_revision"],
            "resolved_snapshot_hash": base["resolved_snapshot_hash"],
            "config_sha256": base["config_sha256"],
            "dtype": runtime["dtype"],
            "attention": runtime["attention"],
            "trust_remote_code": False,
        },
        "artifacts": {
            "adapter_sha256": adapter["sha256"],
            "adapter_config_sha256": adapter["files"][
                "adapter/adapter_config.json"
            ],
            "adapter_safetensors_sha256": adapter["files"][
                "adapter/adapter_model.safetensors"
            ],
            "tokenizer_sha256": tokenizer["sha256"],
        },
        "probes": {
            "selection_method": PROBE_SELECTION_METHOD,
            "selection_binding_sha256": binding,
            "candidate_population_sha256": "6" * 64,
            "candidate_count": 2,
            "train_candidate_count": 1,
            "validation_candidate_count": 1,
            "count": 2,
            "set_sha256": sha256_json(records),
            "records": records,
            "original_outputs_sha256": outputs,
            "fresh_outputs_sha256": outputs,
        },
        "adapter_tensors": {
            "format": TENSOR_POPULATION_FORMAT,
            "v": TENSOR_POPULATION_VERSION,
            "tensor_count": 2,
            "names_sha256": "7" * 64,
            "population_sha256": "8" * 64,
            "population_hash_format": TENSOR_POPULATION_HASH_FORMAT,
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
            "tokenizer_encoding_count": 2,
            "exact_reload_count": 2,
            "differs_from_base_count": 1,
        },
        "hash_contract": {
            "algorithm": "sha256",
            "canonicalization": ADMISSION_CANONICALIZATION,
            "tensor_population": TENSOR_POPULATION_HASH_FORMAT,
            "projected_logits": PROJECTED_LOGITS_HASH_FORMAT,
            "output_set": OUTPUT_SET_HASH_FORMAT,
        },
    }
    evidence["content_sha256"] = sha256_json(evidence)
    manifest["inputs"]["run_identity"] = {"sha256": binding}
    manifest["adapter_admission"] = evidence


def _attach_training_evidence(manifest: dict[str, object]) -> None:
    steps = 650
    audit = FiniteGradientAudit(
        expected_optimizer_steps=steps,
        trainable_parameter_names=("adapter.left", "adapter.right"),
    )
    for previous_step in range(steps):
        audit.observe_pre_optimizer_step(
            trainer_state_global_step=previous_step,
            raw_finite_gradient_parameter_names=(
                "adapter.left",
                "adapter.right",
            ),
            pre_clip_global_norm=0.5,
            post_clip_finite_gradient_parameter_names=(
                "adapter.left",
                "adapter.right",
            ),
        )
    runtime = manifest["runtime"]["trainer"]
    trainer_arguments = manifest["runtime"]["trainer_arguments"]
    metrics = manifest["metrics"]
    trainable_names = ("adapter.left", "adapter.right")
    adapter_update = adapter_update_audit_record(
        trainable_parameter_names=trainable_names,
        initial_tensor_population_sha256="e" * 64,
        final_tensor_population_sha256="f" * 64,
        changed_parameter_names=("adapter.right",),
        final_finite_parameter_names=trainable_names,
    )
    log_history = [
        {
            "step": step,
            "loss": 1.0 / step,
            "learning_rate": 0.0001 * (steps - step) / steps,
        }
        for step in range(10, steps + 1, 10)
    ]
    log_history.extend(
        (
            {**metrics["train"], "step": steps},
            {**metrics["eval"], "step": steps},
        )
    )
    manifest["training_evidence"] = completed_training_evidence_record(
        top_level_metrics=metrics,
        train_result_global_step=steps,
        trainer_state_global_step=steps,
        trainer_state_max_steps=steps,
        trainer_runtime=runtime,
        trainer_arguments=trainer_arguments,
        finite_gradient_audit=audit.record(),
        adapter_update=adapter_update,
        logging_steps=10,
        log_history=log_history,
        adapter_sha256=manifest["adapter"]["sha256"],
        tokenizer_sha256=manifest["tokenizer"]["artifacts"]["sha256"],
    )
    _attach_adapter_admission(manifest)


def _manifest() -> dict[str, object]:
    environment = model_v3_environment()
    runtime = _trainer_runtime()
    trainer_arguments = reviewed_trainer_arguments_record(
        SimpleNamespace(
            args=SimpleNamespace(
                max_grad_norm=0.0,
                bf16=True,
                bf16_full_eval=False,
                save_strategy=SimpleNamespace(value="no"),
                eval_strategy=SimpleNamespace(value="no"),
                logging_nan_inf_filter=False,
                logging_steps=10,
                per_device_train_batch_size=1,
                per_device_eval_batch_size=1,
                gradient_accumulation_steps=32,
            )
        )
    )
    manifest: dict[str, object] = {
        "v": 1,
        "prompt_version": 3,
        "prompt_contract_sha256": prompt_contract_sha256(3),
        "run": {"name": "qwen3-1.7b-lora-v3-library"},
        "base_model": {
            "id": "Qwen/Qwen3-1.7B-Base",
            "requested_revision": REVISION,
            "resolved_snapshot_hash": REVISION,
            "config_sha256": "c" * 64,
        },
        "tokenizer": {
            "resolved_snapshot_hash": REVISION,
            "identity_sha256": "d" * 64,
            "artifacts": _artifact("tokenizer", "tokenizer.json"),
        },
        "adapter": _artifact("adapter", "adapter_model.safetensors"),
        "generation": {"temperature": 1.0, "top_p": 1.0},
        "inputs": {
            "dataset_attestation": {
                "held_out_contract": held_out_contract_record(3),
                "held_out_contract_sha256": held_out_contract_sha256(3),
                "inference_environment": environment_record(environment),
            }
        },
        "metrics": {
            "train": {"train_loss": 0.75, "train_runtime": 10.0},
            "eval": {"eval_loss": 0.8, "eval_runtime": 1.0},
            "train_examples": 20_782,
            "eval_examples": 512,
            "expected_optimizer_steps": 650,
            "actual_optimizer_steps": 650,
        },
        "runtime": {
            "dtype": "bfloat16",
            "attention": "sdpa",
            "trainer": runtime,
            "trainer_arguments": trainer_arguments,
            "job": {"job_id": "172800"},
        },
    }
    _attach_training_evidence(manifest)
    return manifest


@pytest.fixture
def trusted_environment(monkeypatch: pytest.MonkeyPatch):
    environment = model_v3_environment()
    monkeypatch.setattr(
        baseline,
        "attested_training_environment",
        lambda manifest: environment,
    )
    return environment


def test_fixed_baseline_contract_has_no_goal_or_budget_switches() -> None:
    parser = CLI._parser()
    args = parser.parse_args(["--comparison-adapter", "run"])
    assert args.comparison_adapter == Path("run")
    assert CLI.BASELINE_SEED == 20260728
    assert CLI.BASELINE_MAX_NEW_TOKENS == 256
    assert CLI.BASELINE_GOAL_SET_SHA256 == (
        "198beaf753c0abab3151b4913ca9da63094ab6f28807e949e651e629336470d5"
    )
    assert baseline.EXPECTED_V3_ENVIRONMENT_SHA256 == (
        "72372974368a4a2b66cba42fa48baae47e24bf811a8b2dd030027ea3b7f16363"
    )
    assert REVISION == "ea980cb0a6c2ae4b936e82123acc929f1cec04c1"
    assert CLI.BASELINE_SEARCH_LIMITS.max_depth == 32
    assert CLI.BASELINE_SEARCH_LIMITS.beam_width == 16
    assert CLI.BASELINE_SEARCH_LIMITS.candidates_per_state == 8
    assert CLI.BASELINE_SEARCH_LIMITS.max_model_calls == 512
    assert CLI.BASELINE_SEARCH_LIMITS.max_states == 4096
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["--comparison-adapter", "run", "--goal", "different-theorem"]
        )
    with pytest.raises(SystemExit):
        parser.parse_args(
            ["--comparison-adapter", "run", "--max-new-tokens", "1"]
        )
    with pytest.raises(SystemExit):
        CLI.trained._parser().parse_args(
            ["--adapter", "run", "--pretrained-base"]
        )


def test_comparison_manifest_requires_full_v3_qwen_and_completed_steps(
    trusted_environment: object,
) -> None:
    manifest = _manifest()
    assert baseline.validate_comparison_manifest(manifest) is trusted_environment

    mutations = (
        ("base_model", "id", "other/model"),
        ("base_model", "resolved_snapshot_hash", "0" * 40),
        ("base_model", "requested_revision", "0" * 40),
        ("tokenizer", "resolved_snapshot_hash", "0" * 40),
        ("metrics", "actual_optimizer_steps", 649),
        ("metrics", "actual_optimizer_steps", True),
        ("metrics", "expected_optimizer_steps", 0),
        ("runtime", "attention", "flash_attention_2"),
        ("generation", "top_p", 0.9),
    )
    for section, key, replacement in mutations:
        forged = json.loads(json.dumps(manifest))
        forged[section][key] = replacement
        with pytest.raises(ValueError):
            baseline.validate_comparison_manifest(forged)
    forged_holdout = json.loads(json.dumps(manifest))
    forged_holdout["inputs"]["dataset_attestation"][
        "held_out_contract_sha256"
    ] = "0" * 64
    with pytest.raises(ValueError, match="frozen v3 benchmark"):
        baseline.validate_comparison_manifest(forged_holdout)


def test_baseline_identity_is_distinct_and_binds_full_environment(
    trusted_environment: object,
) -> None:
    policy = PeanoPretrainedBasePolicy(
        model=object(),
        tokenizer=object(),
        environment=trusted_environment,
        name="pretrained-control",
        provenance={"comparison": MANIFEST_SHA},
    )
    identity = policy.evaluation_identity
    assert identity["kind"] == "peano-policy-pretrained-base-v1"
    assert identity["environment"] == environment_record(trusted_environment)
    assert identity["provenance"]["comparison"] == MANIFEST_SHA
    candidate = PeanoPolicyCandidateAdapter(policy, seed=7)
    assert candidate.evaluation_identity["base_policy"]["kind"] == (
        "peano-policy-pretrained-base-v1"
    )

    trained = PeanoPolicyAdapter(object(), object(), trusted_environment)
    trained_identity = trained.evaluation_identity
    assert trained_identity["kind"] == "peano-policy-adapter-v1"
    assert trained_identity["environment"] == environment_record(trusted_environment)
    assert trained.policy_environment != trained_identity["environment"]


def test_authority_record_rechecks_both_closed_artifact_trees(
    tmp_path: Path,
    trusted_environment: object,
) -> None:
    adapter_dir = tmp_path / "comparison"
    adapter = adapter_dir / "adapter"
    tokenizer = adapter_dir / "tokenizer"
    adapter.mkdir(parents=True)
    tokenizer.mkdir()
    (adapter / "adapter_config.json").write_text("{}\n", encoding="utf-8")
    (adapter / "adapter_model.safetensors").write_bytes(b"safe")
    (tokenizer / "tokenizer.json").write_text("{}\n", encoding="utf-8")
    manifest = _manifest()
    manifest["adapter"] = artifact_directory_hash(adapter_dir, "adapter")
    manifest["tokenizer"]["artifacts"] = artifact_directory_hash(
        adapter_dir, "tokenizer"
    )
    for directory in (adapter, tokenizer):
        for payload in directory.iterdir():
            payload.chmod(0o444)
        directory.chmod(0o555)
    _attach_training_evidence(manifest)

    record = baseline.comparison_authority_record(
        adapter_dir,
        manifest,
        manifest_sha256=MANIFEST_SHA,
    )
    assert record["format"] == "peano-policy-pretrained-base-comparison-authority"
    assert record["training_manifest_sha256"] == MANIFEST_SHA
    assert record["adapter"]["sha256"] == manifest["adapter"]["sha256"]
    assert record["tokenizer"]["sha256"] == (
        manifest["tokenizer"]["artifacts"]["sha256"]
    )
    assert record["model_runtime"] == {
        "dtype": "bfloat16",
        "attention": "sdpa",
    }

    adapter.chmod(0o755)
    (adapter / "unmanifested.bin").write_bytes(b"mutation")
    (adapter / "unmanifested.bin").chmod(0o444)
    adapter.chmod(0o555)
    with pytest.raises(ValueError, match="complete adapter directory"):
        baseline.comparison_authority_record(
            adapter_dir,
            manifest,
            manifest_sha256=MANIFEST_SHA,
        )


def test_base_loader_never_imports_or_attaches_peft(
    monkeypatch: pytest.MonkeyPatch,
    trusted_environment: object,
) -> None:
    manifest = _manifest()

    class UnitTokenizer:
        eos_token_id = 1
        pad_token_id = 1
        padding_side = "right"
        special_tokens_map = {"eos_token": "<eos>", "pad_token": "<eos>"}

        def __len__(self) -> int:
            return 17

    tokenizer = UnitTokenizer()
    tokenizer_identity = {
        "class": "UnitTokenizer",
        "commit": REVISION,
        "special_tokens": tokenizer.special_tokens_map,
        "vocab_size": 17,
    }
    manifest["tokenizer"]["identity_sha256"] = sha256_json(tokenizer_identity)
    config_record = {"model_type": "unit", "_commit_hash": REVISION}
    manifest["base_model"]["config_sha256"] = sha256_json(config_record)
    _attach_adapter_admission(manifest)
    model = SimpleNamespace(
        config=SimpleNamespace(
            _commit_hash=REVISION,
            to_dict=lambda: config_record,
        ),
        eval=lambda: None,
        to=lambda device: pytest.fail("CPU test must not move model"),
    )
    calls: list[tuple[str, object]] = []
    torch = ModuleType("torch")
    torch.bfloat16 = object()
    torch.manual_seed = lambda seed: calls.append(("torch-seed", seed))
    torch.cuda = SimpleNamespace(
        is_available=lambda: False,
        manual_seed_all=lambda seed: pytest.fail("no CUDA"),
    )
    transformers = ModuleType("transformers")
    loader_calls: list[tuple[str, object, dict[str, object]]] = []

    def load_tokenizer(path: object, **kwargs: object) -> object:
        loader_calls.append(("tokenizer", path, kwargs))
        return tokenizer

    def load_model(model_id: object, **kwargs: object) -> object:
        loader_calls.append(("model", model_id, kwargs))
        return model

    transformers.AutoTokenizer = SimpleNamespace(
        from_pretrained=load_tokenizer
    )
    transformers.AutoModelForCausalLM = SimpleNamespace(
        from_pretrained=load_model
    )
    transformers.set_seed = lambda seed: calls.append(("hf-seed", seed))
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setitem(sys.modules, "transformers", transformers)
    monkeypatch.delitem(sys.modules, "peft", raising=False)
    verification_calls: list[dict[str, object]] = []

    def verify(*args: object, **kwargs: object) -> Path:
        del args
        verification_calls.append(dict(kwargs))
        return Path("x")

    monkeypatch.setattr(
        baseline,
        "verify_artifact_directory",
        verify,
    )
    monkeypatch.setattr(baseline, "require_safetensors_adapter", lambda *args: None)

    loaded_model, loaded_tokenizer = baseline.load_pretrained_base(
        Path("comparison"), manifest, seed=20260728
    )
    assert loaded_model is model
    assert loaded_tokenizer is tokenizer
    assert calls == [("torch-seed", 20260728), ("hf-seed", 20260728)]
    assert loader_calls[0] == (
        "tokenizer",
        Path("x"),
        {"use_fast": True, "trust_remote_code": False},
    )
    assert loader_calls[1][0:2] == ("model", "Qwen/Qwen3-1.7B-Base")
    assert loader_calls[1][2]["revision"] == REVISION
    assert loader_calls[1][2]["attn_implementation"] == "sdpa"
    assert loader_calls[1][2]["use_safetensors"] is True
    assert all("adapter" not in str(call[1]).lower() for call in loader_calls)
    assert verification_calls == [{"require_protected": True}] * 4
    assert "peft" not in sys.modules


def test_cli_uses_fixed_search_and_rechecks_snapshot_before_publication(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    trusted_environment: object,
) -> None:
    manifest = _manifest()
    comparison_dir = tmp_path / "comparison"
    comparison_dir.mkdir()
    checks: list[str] = []
    monkeypatch.setattr(
        CLI.trained,
        "_read_adapter_manifest_snapshot",
        lambda path: (manifest, MANIFEST_SHA),
    )
    monkeypatch.setattr(
        CLI.trained,
        "_recheck_adapter_snapshot",
        lambda *args: checks.append("snapshot"),
    )
    monkeypatch.setattr(CLI, "validate_comparison_manifest", lambda value: trusted_environment)
    monkeypatch.setattr(
        CLI,
        "comparison_authority_record",
        lambda *args, **kwargs: {
            "format": baseline.BASELINE_FORMAT,
            "base_model": {"id": "Qwen/Qwen3-1.7B-Base", "revision": REVISION},
        },
    )
    monkeypatch.setattr(CLI, "load_pretrained_base", lambda *args, **kwargs: (object(), object()))
    source = {"files": {"x": "a" * 64}, "sha256": "b" * 64}
    job = {"scheduler": "none", "deployment": {"mode": "local"}}
    monkeypatch.setattr(CLI, "_baseline_sources", lambda: source)
    monkeypatch.setattr(CLI, "slurm_job_identity", lambda: job)
    monkeypatch.setattr(CLI, "runtime_identity", lambda torch: {"python": "test"})
    torch = ModuleType("torch")
    monkeypatch.setitem(sys.modules, "torch", torch)
    observed: dict[str, object] = {}

    class Report:
        def to_dict(self):
            return {
                "v": 4,
                "goal_set_sha256": observed["goal_set_sha256"],
                "policy_identity": observed["identity"],
            }

    def fake_evaluate(policy, goals, *, seed, limits):
        observed.update(
            seed=seed,
            limits=limits,
            identity=policy.evaluation_identity,
            goal_set_sha256=CLI.trained.evaluator._goal_set_sha256(goals),
        )
        return Report(), {"limits": CLI.trained._search_limits_record(limits)}

    monkeypatch.setattr(CLI.trained, "_evaluate_kernel_search", fake_evaluate)
    output = comparison_dir / CLI.BASELINE_OUTPUT_NAME
    assert CLI.main(
        [
            "--comparison-adapter",
            str(comparison_dir),
            "--output",
            str(output),
        ]
    ) == 0
    record = json.loads(output.read_text(encoding="utf-8"))
    assert observed["seed"] == 20260728
    assert observed["limits"] == CLI.BASELINE_SEARCH_LIMITS
    assert observed["identity"]["kind"] == "peano-policy-pretrained-base-v1"
    assert record["pretrained_base_comparison"]["seed"] == 20260728
    comparison = dict(record["pretrained_base_comparison"])
    claimed = comparison.pop("comparison_authority_sha256")
    assert claimed == sha256_json(comparison)
    assert checks == ["snapshot", "snapshot", "snapshot", "snapshot"]


def test_output_must_be_fixed_child_and_replay_gate_remains_adapter_only(
    tmp_path: Path,
) -> None:
    comparison = tmp_path / "run"
    comparison.mkdir()
    with pytest.raises(ValueError, match="fixed direct child"):
        CLI._fixed_output(comparison, tmp_path / "elsewhere.json")
    replay_source = (
        ROOT / "training" / "peano_policy" / "evaluation_replay.py"
    ).read_text(encoding="utf-8")
    assert 'base.get("kind") != "peano-policy-adapter-v1"' in replay_source
    assert "peano-policy-pretrained-base-v1" not in replay_source


def test_slurm_run_must_name_the_manifest_training_predecessor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = _manifest()
    evaluation_job = {
        "job_id": "172801",
        "submission": {"dependency_job_id": "172800"},
    }
    monkeypatch.setenv("SLURM_JOB_ID", "172801")
    monkeypatch.setenv("PEANO_TRAIN_JOB_ID", "172800")
    CLI._require_comparison_job_binding(manifest, evaluation_job)

    forged = json.loads(json.dumps(manifest))
    forged["runtime"]["job"]["job_id"] = "172799"
    with pytest.raises(RuntimeError, match="declared training job"):
        CLI._require_comparison_job_binding(forged, evaluation_job)

    wrong_dependency = {
        "job_id": "172801",
        "submission": {"dependency_job_id": "172799"},
    }
    with pytest.raises(RuntimeError, match="declared training job"):
        CLI._require_comparison_job_binding(manifest, wrong_dependency)


def test_slurm_job_is_separate_fixed_offline_a100_comparison() -> None:
    path = ROOT / "slurm" / "peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch"
    source = path.read_text(encoding="utf-8")
    for fragment in (
        "#SBATCH --gpus=nvidia_a100:1",
        "#SBATCH --constraint=vram80g",
        "#SBATCH --job-name=peano-wmi-qwen17-v3-base",
        "export HF_HUB_OFFLINE=1",
        "export TRANSFORMERS_OFFLINE=1",
        "PEANO_TRAIN_JOB_ID",
        "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
        "scripts/eval_pretrained_peano_policy.py",
        "--comparison-adapter",
        "pretrained-base-heldout-search-wmi-b16-c8-d32.json",
    ):
        assert fragment in source
    for forbidden in (
        "--goal",
        "--max-new-tokens",
        "--max-steps",
        "--search-beam-width",
        "--search-candidates-per-state",
    ):
        assert forbidden not in source


def test_import_and_help_do_not_load_model_frameworks() -> None:
    code = """
import sys
import training.peano_policy.pretrained_baseline
assert 'torch' not in sys.modules
assert 'transformers' not in sys.modules
assert 'peft' not in sys.modules
"""
    imported = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert imported.returncode == 0, imported.stderr
    helped = subprocess.run(
        [sys.executable, str(SCRIPT), "--help"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert helped.returncode == 0, helped.stderr
    assert "--comparison-adapter" in helped.stdout
    assert "--goal" not in helped.stdout
    assert "--max-new-tokens" not in helped.stdout
