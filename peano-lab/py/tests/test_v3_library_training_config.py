"""Static contract for the sealed 247-theorem model-v3 run."""

from __future__ import annotations

from pathlib import Path
import sys

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10 CI
    import tomli as tomllib


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy.config import CurriculumConfig, load_config  # noqa: E402


CONFIG = (
    REPOSITORY_ROOT
    / "training"
    / "peano_policy"
    / "configs"
    / "qwen3_1_7b_v3_library.toml"
)
CORPUS_CONTENT_SHA256 = (
    "7b22bdf083894e3d87b84fc463ff537a75eeecba8e34098429db215592ec6b5b"
)


def test_v3_config_has_the_reviewed_sealed_training_budget() -> None:
    value = tomllib.loads(CONFIG.read_text(encoding="utf-8"))

    assert value["run"] == {
        "name": "qwen3-1.7b-peano-lora-v3-library",
        "seed": 20260729,
        "output_dir": "results/peano-policy/qwen3-1.7b-lora-v3-library",
        "max_eval_samples": 512,
        "resume": "never",
    }
    assert value["model"] == {
        "model_id": "Qwen/Qwen3-1.7B-Base",
        "revision": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
        "dtype": "bfloat16",
        "attn_implementation": "sdpa",
        "trust_remote_code": False,
    }
    assert value["data"] == {
        "train_path": "checkpoints/corpora/peano-policy-v3-173040/data/train.jsonl",
        "eval_path": "checkpoints/corpora/peano-policy-v3-173040/data/val.jsonl",
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
    assert value["trainer"] == {
        "epochs": 1.0,
        "max_steps": -1,
        "per_device_train_batch_size": 1,
        "per_device_eval_batch_size": 1,
        "gradient_accumulation_steps": 32,
        "learning_rate": 0.0001,
        "weight_decay": 0.01,
        "warmup_ratio": 0.05,
        "logging_steps": 10,
        "eval_steps": 1000,
        "save_steps": 1000,
        "save_total_limit": 1,
        "gradient_checkpointing": True,
    }
    assert value["generation"] == {
        "max_new_tokens": 1024,
        "do_sample": False,
        "temperature": 1.0,
        "top_p": 1.0,
    }
    assert value["curriculum"] == {
        "kind": "model-v3-library-balanced-v1",
        "selection_seed": 20260729,
        "synthetic_row_ceiling": 12288,
        "max_train_tokens": 70000000,
        "max_eval_tokens": 2000000,
        "max_train_squared_tokens": 2300000000000,
        "max_eval_squared_tokens": 66000000000,
        "corpus_seal_path": "checkpoints/corpora/peano-policy-v3-173040",
        "corpus_source_commit": "5faa3d27cbaf522198ffa1bdcd11fa9d57341658",
        "corpus_prepare_job_id": "173040",
        "corpus_content_sha256": CORPUS_CONTENT_SHA256,
    }

    loaded = load_config(CONFIG)
    assert loaded.run.max_train_samples is None
    assert loaded.run.max_eval_samples == 512
    assert loaded.curriculum == CurriculumConfig(**value["curriculum"])


def test_v3_wmi_jobs_share_sealed_config_and_fresh_output_policy() -> None:
    slurm = REPOSITORY_ROOT / "slurm"
    prepare = (slurm / "peano_wmi_prepare_v3_sealed_training.sbatch").read_text(
        encoding="utf-8"
    )
    train = (slurm / "peano_wmi_train_qwen3_1_7b_v3.sbatch").read_text(
        encoding="utf-8"
    )
    evaluate = (slurm / "peano_wmi_eval_qwen3_1_7b_v3.sbatch").read_text(
        encoding="utf-8"
    )

    assert "verify_peano_v3_corpus_eligibility.py" in prepare
    assert "training.peano_policy.token_audit" in prepare
    assert "peano-policy-wmi-a100-v3-smoke" in prepare
    assert "verify_wmi_v3_sealed_preparation.py" in prepare
    assert "qwen3_1_7b_v3_library.toml" in prepare
    assert "qwen3_1_7b_v3_library.toml" in train
    assert "--resume-from-checkpoint NEVER" in train
    assert "qwen3-1.7b-lora-v3-library" in evaluate
    for source in (prepare, train, evaluate):
        assert "export PYTHONHASHSEED=20260729" in source
