"""Strict, backward-compatible configuration for model-v3 selection."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from training.peano_policy.config import (  # noqa: E402
    CurriculumConfig,
    load_config,
    validate_config,
)


CONFIG_ROOT = REPOSITORY_ROOT / "training" / "peano_policy" / "configs"
BASE_CONFIG = CONFIG_ROOT / "qwen3_1_7b_smoke.toml"
SOURCE_COMMIT = "855e424c18cd1aa151b5a0c2942d5974606f437a"
CONTENT_SHA256 = "b" * 64


def _curriculum_table() -> str:
    return f"""

[curriculum]
kind = "model-v3-library-balanced-v1"
selection_seed = 20260729
synthetic_row_ceiling = 12288
max_train_tokens = 70000000
max_eval_tokens = 2000000
max_train_squared_tokens = 2300000000000
max_eval_squared_tokens = 66000000000
corpus_seal_path = "checkpoints/corpora/peano-policy-v3-172729"
corpus_source_commit = "{SOURCE_COMMIT}"
corpus_prepare_job_id = "172729"
corpus_content_sha256 = "{CONTENT_SHA256}"
"""


def _v3_text() -> str:
    source = BASE_CONFIG.read_text(encoding="utf-8")
    source = source.replace(
        'name = "qwen3-1.7b-peano-lora-smoke"',
        'name = "qwen3-1.7b-peano-lora-v3-library"',
    )
    source = source.replace("seed = 20260728", "seed = 20260729")
    source = source.replace("max_train_samples = 2048\n", "")
    source = source.replace("max_eval_samples = 256", "max_eval_samples = 512")
    source = source.replace(
        'train_path = "data/peano-policy-v1/train.jsonl"',
        'train_path = "data/peano-policy-v3/train.jsonl"',
    )
    source = source.replace(
        'eval_path = "data/peano-policy-v1/val.jsonl"',
        'eval_path = "data/peano-policy-v3/val.jsonl"',
    )
    return source + _curriculum_table()


def _write(tmp_path: Path, text: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(text, encoding="utf-8")
    return path


def test_old_config_remains_valid_without_curriculum() -> None:
    config = load_config(BASE_CONFIG)

    assert config.curriculum is None


def test_model_v3_curriculum_loads_exact_selection_and_compute_gates(
    tmp_path: Path,
) -> None:
    config = load_config(_write(tmp_path, _v3_text()))

    assert config.run.max_train_samples is None
    assert config.run.max_eval_samples == 512
    assert config.curriculum == CurriculumConfig(
        kind="model-v3-library-balanced-v1",
        selection_seed=20260729,
        synthetic_row_ceiling=12288,
        max_train_tokens=70000000,
        max_eval_tokens=2000000,
        max_train_squared_tokens=2300000000000,
        max_eval_squared_tokens=66000000000,
        corpus_seal_path="checkpoints/corpora/peano-policy-v3-172729",
        corpus_source_commit=SOURCE_COMMIT,
        corpus_prepare_job_id="172729",
        corpus_content_sha256=CONTENT_SHA256,
    )


def test_model_v3_name_or_data_path_requires_curriculum() -> None:
    base = load_config(BASE_CONFIG)

    by_name = replace(
        base,
        run=replace(base.run, name="qwen3-1.7b-peano-lora-v3-library"),
    )
    with pytest.raises(ValueError, match=r"require a \[curriculum\]"):
        validate_config(by_name)

    by_data = replace(
        base,
        data=replace(
            base.data,
            train_path="data/peano-policy-v3/train.jsonl",
        ),
    )
    with pytest.raises(ValueError, match=r"require a \[curriculum\]"):
        validate_config(by_data)


def test_curriculum_is_not_silently_accepted_by_an_old_run(tmp_path: Path) -> None:
    source = BASE_CONFIG.read_text(encoding="utf-8") + _curriculum_table()

    with pytest.raises(ValueError, match="supported only for a model-v3"):
        load_config(_write(tmp_path, source))


def test_curriculum_table_rejects_missing_and_unknown_keys(tmp_path: Path) -> None:
    source = _v3_text()
    missing = source.replace('corpus_prepare_job_id = "172729"\n', "")
    with pytest.raises(ValueError, match=r"missing \[curriculum\] keys"):
        load_config(_write(tmp_path, missing))

    unknown = source.replace(
        'kind = "model-v3-library-balanced-v1"\n',
        'kind = "model-v3-library-balanced-v1"\nextra = 1\n',
    )
    with pytest.raises(ValueError, match=r"unknown \[curriculum\] keys: extra"):
        load_config(_write(tmp_path, unknown))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("kind", "unreviewed", "curriculum.kind"),
        ("selection_seed", -1, "selection_seed"),
        ("synthetic_row_ceiling", True, "positive integers"),
        ("max_train_tokens", 0, "positive integers"),
        ("corpus_seal_path", "../unsealed", "safe path text"),
        ("corpus_source_commit", "A" * 40, "lowercase 40-hex"),
        ("corpus_prepare_job_id", 172729, "decimal text"),
        ("corpus_content_sha256", "b" * 63, "lowercase 64-hex"),
    ],
)
def test_curriculum_values_are_strictly_validated(
    tmp_path: Path,
    field: str,
    value: object,
    message: str,
) -> None:
    config = load_config(_write(tmp_path, _v3_text()))
    assert config.curriculum is not None
    changed = replace(
        config,
        curriculum=replace(config.curriculum, **{field: value}),
    )

    with pytest.raises(ValueError, match=message):
        validate_config(changed)


def test_curriculum_seed_must_equal_the_training_seed(tmp_path: Path) -> None:
    config = load_config(_write(tmp_path, _v3_text()))
    assert config.curriculum is not None

    changed = replace(
        config,
        curriculum=replace(config.curriculum, selection_seed=config.run.seed + 1),
    )

    with pytest.raises(ValueError, match=r"selection_seed must equal run.seed"):
        validate_config(changed)


def test_curriculum_forbids_a_second_row_level_train_cap(tmp_path: Path) -> None:
    config = load_config(_write(tmp_path, _v3_text()))

    changed = replace(config, run=replace(config.run, max_train_samples=1))

    with pytest.raises(ValueError, match=r"forbids run.max_train_samples"):
        validate_config(changed)


@pytest.mark.parametrize("epochs", [0.5, 2.0])
def test_curriculum_requires_exactly_one_training_epoch(
    tmp_path: Path, epochs: float
) -> None:
    config = load_config(_write(tmp_path, _v3_text()))
    changed = replace(
        config,
        trainer=replace(config.trainer, epochs=epochs),
    )

    with pytest.raises(ValueError, match=r"exactly one training epoch"):
        validate_config(changed)
