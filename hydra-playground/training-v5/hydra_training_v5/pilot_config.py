"""Finite new pilot registry; historical model/config admission is untouched."""
from __future__ import annotations

from pathlib import Path
import re
try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib

from .peano_policy.config import (ExperimentConfig, RunConfig, ModelConfig,
    DataConfig, LoraConfig, TrainerConfig, GenerationConfig)

# Reviewed model revisions shared with P6's dedicated provider manifest.
# There is deliberately no wildcard model or unpinned fallback.
MODEL_PINS = {
    "Qwen/Qwen3-1.7B-Base": "ea980cb0a6c2ae4b936e82123acc929f1cec04c1",
    "Qwen/Qwen3-4B-Base": "906bfd4b4dc7f14ee4320094d8b41684abff8539",
    "Qwen/Qwen3-8B-Base": "49e3418fbbbca6ecbdf9608b4d22e5a407081db4",
}
LORA_MODULES = ("q_proj","k_proj","v_proj","o_proj","gate_proj","up_proj","down_proj")


def load_pilot_config(path):
    path = Path(path).absolute()
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 32768:
        raise ValueError("Expected a small regular pilot config.")
    record = tomllib.loads(path.read_text())
    if set(record) != {"run","model","data","lora","trainer","generation"}:
        raise ValueError("Pilot config must contain exactly the six supported sections.")
    run = dict(record["run"])
    run.setdefault("max_train_samples",4096)
    run.setdefault("max_eval_samples",4096)
    lora = dict(record["lora"])
    lora["target_modules"] = tuple(lora["target_modules"])
    config = ExperimentConfig(path=path,run=RunConfig(**run),model=ModelConfig(**record["model"]),
        data=DataConfig(**record["data"]),lora=LoraConfig(**lora),trainer=TrainerConfig(**record["trainer"]),
        generation=GenerationConfig(**record["generation"]))
    validate_pilot_config(config)
    return config


def validate_pilot_config(config):
    if type(config) is not ExperimentConfig:
        raise ValueError("Exact typed pilot config required.")
    if config.model.model_id not in MODEL_PINS or config.model.revision != MODEL_PINS[config.model.model_id]:
        raise ValueError("Model/revision has no reviewed pilot registry entry.")
    if (config.model.dtype != "bfloat16" or config.model.attn_implementation != "sdpa"
            or config.model.trust_remote_code is not False):
        raise ValueError("Pilot requires pinned BF16/SDPA without remote code.")
    if (config.run.resume != "never" or config.curriculum is not None
            or type(config.run.seed) is not int or not 0 <= config.run.seed < 2**32
            or not re.fullmatch(r"[a-zA-Z0-9_.-]{1,100}",config.run.name)):
        raise ValueError("Pilot must be fresh, explicitly seeded, and nonresumable.")
    if any(type(x) is not int or not 1 <= x <= 4096
           for x in (config.run.max_train_samples,config.run.max_eval_samples)):
        raise ValueError("Pilot selection must be bounded to4096 rows before training.")
    if type(config.data.max_length) is not int or not 128 <= config.data.max_length <= 4096:
        raise ValueError("Pilot max sequence length exceeds its declared token bound.")
    if (config.lora.rank != 16 or config.lora.alpha != 32 or config.lora.dropout != 0.05
            or config.lora.target_modules != LORA_MODULES):
        raise ValueError("The first matched pilot keeps the reviewed common LoRA shape.")
    expected = {"epochs":1.0,"max_steps":-1,"per_device_train_batch_size":1,
        "per_device_eval_batch_size":1,"gradient_accumulation_steps":8,"learning_rate":0.0001,
        "weight_decay":0.01,"warmup_ratio":0.05,"logging_steps":1,"eval_steps":100000,
        "save_steps":100000,"save_total_limit":1,"gradient_checkpointing":True}
    if any(getattr(config.trainer,key) != value for key,value in expected.items()):
        raise ValueError("Pilot must use the fixed one-pass common optimization schedule.")
    if (config.generation.max_new_tokens != 128 or config.generation.do_sample is not False
            or config.generation.temperature != 1.0 or config.generation.top_p != 1.0):
        raise ValueError("Pilot generation settings changed.")
    for value in (config.data.train_path,config.data.eval_path,config.run.output_dir):
        path = Path(value)
        if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
            raise ValueError("Pilot paths must remain canonical relative package paths.")
    return config
