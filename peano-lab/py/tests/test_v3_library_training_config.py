"""Static contract for the checked 247-theorem model-v3 run."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 CI
    import tomli as tomllib


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CONFIG = (
    REPOSITORY_ROOT
    / "training"
    / "peano_policy"
    / "configs"
    / "qwen3_1_7b_v3_library.toml"
)


def test_v3_config_has_the_reviewed_library_training_budget() -> None:
    value = tomllib.loads(CONFIG.read_text(encoding="utf-8"))

    assert value["run"] == {
        "name": "qwen3-1.7b-peano-lora-v3-library",
        "seed": 20260729,
        "output_dir": "results/peano-policy/qwen3-1.7b-lora-v3-library",
        "max_train_samples": 80000,
        "max_eval_samples": 6000,
        "resume": "auto",
    }
    assert value["model"] == {
        "model_id": "Qwen/Qwen3-1.7B-Base",
        "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
        "dtype": "bfloat16",
        "attn_implementation": "sdpa",
        "trust_remote_code": False,
    }
    assert value["data"] == {
        "train_path": "data/peano-policy-v3/train.jsonl",
        "eval_path": "data/peano-policy-v3/val.jsonl",
        "max_length": 32768,
    }
    assert value["lora"] == {
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
    }
    trainer = value["trainer"]
    assert trainer["epochs"] == 2.0
    assert trainer["max_steps"] == -1
    assert trainer["per_device_train_batch_size"] == 1
    assert trainer["per_device_eval_batch_size"] == 1
    assert trainer["gradient_accumulation_steps"] == 32
    assert trainer["per_device_train_batch_size"] * trainer[
        "gradient_accumulation_steps"
    ] == 32
    assert trainer["learning_rate"] == 0.0001
    assert trainer["gradient_checkpointing"] is True


def test_v3_wmi_jobs_share_config_and_fresh_output_policy() -> None:
    slurm = REPOSITORY_ROOT / "slurm"
    prepare = (slurm / "peano_wmi_prepare_v3_training.sbatch").read_text(
        encoding="utf-8"
    )
    train = (slurm / "peano_wmi_train_qwen3_1_7b_v3.sbatch").read_text(
        encoding="utf-8"
    )
    evaluate = (slurm / "peano_wmi_eval_qwen3_1_7b_v3.sbatch").read_text(
        encoding="utf-8"
    )

    assert "--row-budget 70000" in prepare
    assert "training.peano_policy.attest" in prepare
    assert "training.peano_policy.token_audit" in prepare
    assert "peano-policy-wmi-a100-v3-smoke" in prepare
    assert "qwen3_1_7b_v3_library.toml" in prepare
    assert "qwen3_1_7b_v3_library.toml" in train
    assert "--resume-from-checkpoint NEVER" in train
    assert "qwen3-1.7b-lora-v3-library" in evaluate
    for source in (prepare, train, evaluate):
        assert "export PYTHONHASHSEED=20260729" in source
