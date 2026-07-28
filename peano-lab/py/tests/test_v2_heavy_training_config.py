"""Static contract for the overnight model-v2 experiment."""

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
    / "qwen3_1_7b_v2_heavy.toml"
)


def test_v2_heavy_config_has_the_reviewed_training_budget() -> None:
    value = tomllib.loads(CONFIG.read_text(encoding="utf-8"))
    assert value["run"] == {
        "name": "qwen3-1.7b-peano-lora-v2-heavy",
        "seed": 20260728,
        "output_dir": "results/peano-policy/qwen3-1.7b-lora-v2-heavy",
        "max_train_samples": 100000,
        "max_eval_samples": 4000,
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
        "train_path": "data/peano-policy-v2/train.jsonl",
        "eval_path": "data/peano-policy-v2/val.jsonl",
        "max_length": 2048,
    }
    assert value["lora"] == {
        "rank": 16,
        "alpha": 32,
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
    assert trainer["epochs"] == 3.0
    assert trainer["max_steps"] == -1
    assert trainer["per_device_train_batch_size"] == 8
    assert trainer["gradient_accumulation_steps"] == 4
    assert trainer["per_device_train_batch_size"] * trainer[
        "gradient_accumulation_steps"
    ] == 32
    assert trainer["learning_rate"] == 0.0001
    assert trainer["gradient_checkpointing"] is False


def test_both_clusters_consume_the_same_v2_config_and_data_budget() -> None:
    slurm = REPOSITORY_ROOT / "slurm"
    jobs = {
        name: (slurm / name).read_text(encoding="utf-8")
        for name in (
            "peano_prepare_v2_training.sbatch",
            "peano_train_qwen3_1_7b_v2.sbatch",
            "peano_eval_qwen3_1_7b_v2.sbatch",
            "peano_wmi_prepare_v2_training.sbatch",
            "peano_wmi_train_qwen3_1_7b_v2.sbatch",
            "peano_wmi_eval_qwen3_1_7b_v2.sbatch",
        )
    }
    for name, source in jobs.items():
        assert "v2" in name
        assert "peano-policy-v2" in source or "qwen3-1.7b-lora-v2-heavy" in source
    for name in (
        "peano_prepare_v2_training.sbatch",
        "peano_wmi_prepare_v2_training.sbatch",
    ):
        assert "PEANO_POLICY_ROWS=100000" in jobs[name]
        assert "peano-policy-v2-data" in jobs[name]
        assert "training.peano_policy.token_audit" in jobs[name]
        assert "TRANSFORMERS_OFFLINE=1" in jobs[name]
    for name in (
        "peano_train_qwen3_1_7b_v2.sbatch",
        "peano_wmi_train_qwen3_1_7b_v2.sbatch",
    ):
        assert "qwen3_1_7b_v2_heavy.toml" in jobs[name]
        assert "#SBATCH --time=20:00:00" in jobs[name]
