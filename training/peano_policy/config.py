"""Strict TOML configuration for the Peano Qwen3 LoRA runner."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping

try:  # Python 3.11+; the repository's 3.10 test runtime uses pinned tomli.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - branch depends on interpreter
    import tomli as tomllib


@dataclass(frozen=True, slots=True)
class RunConfig:
    name: str
    seed: int
    output_dir: str
    max_train_samples: int | None
    max_eval_samples: int | None
    resume: str


@dataclass(frozen=True, slots=True)
class ModelConfig:
    model_id: str
    revision: str
    dtype: str
    attn_implementation: str
    trust_remote_code: bool


@dataclass(frozen=True, slots=True)
class DataConfig:
    train_path: str
    eval_path: str
    max_length: int


@dataclass(frozen=True, slots=True)
class LoraConfig:
    rank: int
    alpha: int
    dropout: float
    target_modules: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TrainerConfig:
    epochs: float
    max_steps: int
    per_device_train_batch_size: int
    per_device_eval_batch_size: int
    gradient_accumulation_steps: int
    learning_rate: float
    weight_decay: float
    warmup_ratio: float
    logging_steps: int
    eval_steps: int
    save_steps: int
    save_total_limit: int
    gradient_checkpointing: bool


@dataclass(frozen=True, slots=True)
class GenerationConfig:
    max_new_tokens: int
    do_sample: bool
    temperature: float
    top_p: float


@dataclass(frozen=True, slots=True)
class ExperimentConfig:
    path: Path
    run: RunConfig
    model: ModelConfig
    data: DataConfig
    lora: LoraConfig
    trainer: TrainerConfig
    generation: GenerationConfig


_SECTIONS = {"run", "model", "data", "lora", "trainer", "generation"}
_SUPPORTED_BASE_MODELS = {
    "Qwen/Qwen3-1.7B-Base": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
    "Qwen/Qwen3-4B-Base": "906bfd4b4dc7f14ee4320094d8b41684abff8539",
    "Pythagoras-LM/Pythagoras-Prover-4B": "aa05cf9a86cd1bc5af16935ab8f2190f4a1e62b8",
}


def _section(document: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    value = document.get(name)
    if not isinstance(value, dict):
        raise ValueError(f"missing [{name}] table")
    return value


def _only(section: Mapping[str, Any], allowed: set[str], name: str) -> None:
    unknown = set(section) - allowed
    if unknown:
        raise ValueError(f"unknown [{name}] keys: {', '.join(sorted(unknown))}")


def load_config(path: str | Path) -> ExperimentConfig:
    config_path = Path(path).resolve()
    with config_path.open("rb") as handle:
        document = tomllib.load(handle)
    unknown_sections = set(document) - _SECTIONS
    if unknown_sections:
        raise ValueError(f"unknown config tables: {', '.join(sorted(unknown_sections))}")

    run = _section(document, "run")
    model = _section(document, "model")
    data = _section(document, "data")
    lora = _section(document, "lora")
    trainer = _section(document, "trainer")
    generation = _section(document, "generation")
    _only(run, {"name", "seed", "output_dir", "max_train_samples", "max_eval_samples", "resume"}, "run")
    _only(model, {"model_id", "revision", "dtype", "attn_implementation", "trust_remote_code"}, "model")
    _only(data, {"train_path", "eval_path", "max_length"}, "data")
    _only(lora, {"rank", "alpha", "dropout", "target_modules"}, "lora")
    _only(
        trainer,
        {
            "epochs", "max_steps", "per_device_train_batch_size",
            "per_device_eval_batch_size", "gradient_accumulation_steps",
            "learning_rate", "weight_decay", "warmup_ratio", "logging_steps",
            "eval_steps", "save_steps", "save_total_limit",
            "gradient_checkpointing",
        },
        "trainer",
    )
    _only(generation, {"max_new_tokens", "do_sample", "temperature", "top_p"}, "generation")

    result = ExperimentConfig(
        path=config_path,
        run=RunConfig(**run),
        model=ModelConfig(**model),
        data=DataConfig(
            train_path=data["train_path"],
            eval_path=data["eval_path"],
            max_length=data["max_length"],
        ),
        lora=LoraConfig(
            rank=lora["rank"],
            alpha=lora["alpha"],
            dropout=lora["dropout"],
            target_modules=tuple(lora["target_modules"]),
        ),
        trainer=TrainerConfig(**trainer),
        generation=GenerationConfig(**generation),
    )
    validate_config(result)
    return result


def validate_config(config: ExperimentConfig) -> None:
    if not config.run.name or config.run.seed < 0:
        raise ValueError("run name must be non-empty and seed non-negative")
    if config.run.resume not in {"auto", "never"}:
        raise ValueError("run.resume must be 'auto' or 'never'")
    if any(
        value is not None and value <= 0
        for value in (config.run.max_train_samples, config.run.max_eval_samples)
    ):
        raise ValueError("sample caps must be positive or omitted")
    if config.model.model_id not in _SUPPORTED_BASE_MODELS:
        raise ValueError("model_id is not in the reviewed Peano pilot allowlist")
    if re.fullmatch(r"[0-9a-f]{40}", config.model.revision) is None:
        raise ValueError("model revision must be an immutable 40-hex commit")
    if config.model.revision != _SUPPORTED_BASE_MODELS[config.model.model_id]:
        raise ValueError(
            "model revision differs from the reviewed Peano pilot snapshot"
        )
    if config.model.dtype != "bfloat16":
        raise ValueError("the first training regime is pinned to bfloat16")
    if config.model.attn_implementation != "sdpa":
        raise ValueError("attention must be PyTorch SDPA")
    if config.model.trust_remote_code:
        raise ValueError("trust_remote_code must remain false")
    if config.data.max_length < 128:
        raise ValueError("data max_length must be at least 128")
    if config.lora.rank <= 0 or config.lora.alpha <= 0 or not config.lora.target_modules:
        raise ValueError("LoRA rank, alpha, and target modules must be non-empty")
    if not 0.0 <= config.lora.dropout < 1.0:
        raise ValueError("LoRA dropout must be in [0, 1)")
    if config.trainer.max_steps < -1 or config.trainer.max_steps == 0:
        raise ValueError("max_steps must be -1 (epochs) or positive")
    if (
        config.trainer.epochs <= 0
        or config.trainer.per_device_train_batch_size <= 0
        or config.trainer.per_device_eval_batch_size <= 0
    ):
        raise ValueError("epochs and per-device batch sizes must be positive")
    if config.trainer.gradient_accumulation_steps <= 0 or config.trainer.learning_rate <= 0:
        raise ValueError("gradient accumulation and learning rate must be positive")
    if config.generation.max_new_tokens <= 0:
        raise ValueError("generation max_new_tokens must be positive")
    if config.generation.temperature <= 0 or not 0 < config.generation.top_p <= 1:
        raise ValueError("generation temperature and top_p must be positive")
