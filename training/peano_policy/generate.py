#!/usr/bin/env python3
"""Load a Peano LoRA adapter and emit exactly one candidate tactic line."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import random
from typing import Any

from .contract import attested_training_environment
from .manifest import (
    ADAPTER_SUBDIR,
    MANIFEST_VERSION,
    TOKENIZER_SUBDIR,
    sha256_file,
    sha256_json,
    verify_artifact_directory,
)
from .prompt import (
    CapabilityIdentity,
    PEANO_PROMPT_VERSION,
    PromptEnvironment,
    extract_one_tactic,
    parse_prompt,
    prompt_manifest_record,
    render_prompt,
)


def _newline_stopper(tokenizer: Any, prompt_length: int) -> Any:
    """Stop if a malformed decoder starts a second tactic line."""

    from transformers import StoppingCriteria

    class StopAfterOneLine(StoppingCriteria):
        def __call__(self, input_ids: Any, scores: Any, **kwargs: Any) -> bool:
            del scores, kwargs
            tail = tokenizer.decode(
                input_ids[0, prompt_length:],
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )
            return "\n" in tail or "\r" in tail

    return StopAfterOneLine()


def generate_one_tactic(
    *,
    model: Any,
    tokenizer: Any,
    prompt: str,
    environment: PromptEnvironment,
    max_new_tokens: int = 64,
    do_sample: bool = False,
    temperature: float = 1.0,
    top_p: float = 1.0,
) -> str:
    """Generate one line; Peano Lab must still execute and kernel-check it."""

    import torch
    from transformers import StoppingCriteriaList

    if max_new_tokens <= 0:
        raise ValueError("max_new_tokens must be positive")
    # Reject invented vendor/statement templates at the inference boundary.
    # The same repository-owned prefix is used by the replay dataset.
    parsed = parse_prompt(prompt)
    if type(environment) is not PromptEnvironment:
        raise ValueError("environment must be a PromptEnvironment")
    if parsed.environment != environment.text:
        raise ValueError("prompt environment does not match its capability preimage")
    encoded = tokenizer(prompt, add_special_tokens=False, return_tensors="pt")
    encoded = {name: tensor.to(model.device) for name, tensor in encoded.items()}
    prompt_length = encoded["input_ids"].shape[1]
    generate_options: dict[str, Any] = {
        "max_new_tokens": max_new_tokens,
        "do_sample": do_sample,
        "eos_token_id": tokenizer.eos_token_id,
        "pad_token_id": tokenizer.pad_token_id,
        "stopping_criteria": StoppingCriteriaList(
            [_newline_stopper(tokenizer, prompt_length)]
        ),
    }
    if do_sample:
        generate_options.update(temperature=temperature, top_p=top_p)
    with torch.inference_mode():
        output = model.generate(**encoded, **generate_options)
    generated = tokenizer.decode(
        output[0, prompt_length:],
        skip_special_tokens=True,
        clean_up_tokenization_spaces=False,
    )
    return extract_one_tactic(generated)


@dataclass(slots=True)
class PeanoPolicyAdapter:
    """Adapter for ``scripts/eval_peano_policy.py``'s structural protocol."""

    model: Any
    tokenizer: Any
    environment: PromptEnvironment
    name: str = "qwen3-peano-next-tactic-v1"
    max_new_tokens: int = 64
    do_sample: bool = False
    temperature: float = 0.8
    top_p: float = 0.95
    provenance: dict[str, object] | None = None

    def __post_init__(self) -> None:
        if type(self.environment) is not PromptEnvironment:
            raise ValueError("environment must be a PromptEnvironment")
        if type(self.name) is not str or not self.name.strip():
            raise ValueError("policy name must be non-empty text")
        if type(self.max_new_tokens) is not int or self.max_new_tokens <= 0:
            raise ValueError("max_new_tokens must be a positive integer")
        if type(self.do_sample) is not bool:
            raise ValueError("do_sample must be a Boolean")
        if self.temperature <= 0 or not 0 < self.top_p <= 1:
            raise ValueError("temperature and top_p must be positive")
        if self.provenance is not None and type(self.provenance) is not dict:
            raise ValueError("provenance must be a JSON object or None")

    @property
    def policy_environment(self) -> dict[str, object]:
        """Exact authority preimage that evaluation must execute under."""

        return {
            "classical": self.environment.classical,
            "surface": self.environment.capabilities.label,
            "environment_sha256": self.environment.sha256,
            "capabilities": self.environment.capabilities.to_record(),
        }

    @property
    def evaluation_identity(self) -> dict[str, object]:
        """Bind reports to weights/provenance and the complete decode policy."""

        provenance = self.provenance or {"status": "unbound-in-memory"}
        detached = json.loads(
            json.dumps(
                provenance,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return {
            "name": self.name,
            "kind": "peano-policy-adapter-v1",
            "environment": self.policy_environment,
            "decoding": {
                "max_new_tokens": self.max_new_tokens,
                "do_sample": self.do_sample,
                "temperature": self.temperature,
                "top_p": self.top_p,
            },
            "provenance": detached,
        }

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        sample: int,
        step: int,
        rng: random.Random,
    ) -> str:
        """Predict from canonical goals only, preserving evaluator isolation."""

        del sample, step
        if not goals_before or not all(
            isinstance(goal, str) and goal.strip() for goal in goals_before
        ):
            raise ValueError("goals_before must contain canonical non-empty goals")
        if self.do_sample:
            # The evaluator owns this per-rollout RNG.  Sampling never consumes
            # another theorem's stream.
            import torch

            seed = rng.getrandbits(63)
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seed)
        prompt = render_prompt(
            goals=goals_before,
            focus=0,
            environment=self.environment,
        )
        return generate_one_tactic(
            model=self.model,
            tokenizer=self.tokenizer,
            prompt=prompt,
            environment=self.environment,
            max_new_tokens=self.max_new_tokens,
            do_sample=self.do_sample,
            temperature=self.temperature,
            top_p=self.top_p,
        )


def load_adapter(adapter_dir: Path, *, seed: int) -> tuple[Any, Any, dict[str, Any]]:
    """Load base+adapter according to its immutable training manifest."""

    manifest_path = adapter_dir / "training-manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("v") != MANIFEST_VERSION:
        raise ValueError("unsupported training manifest version")
    if manifest.get("prompt_version") != PEANO_PROMPT_VERSION:
        raise ValueError("adapter uses a different Peano prompt version")
    if manifest.get("prompt_contract_sha256") != sha256_json(prompt_manifest_record()):
        raise ValueError("adapter uses a different Peano prompt contract")
    attested_training_environment(manifest)
    base = manifest.get("base_model")
    tokenizer_record = manifest.get("tokenizer")
    if not isinstance(base, dict) or not isinstance(tokenizer_record, dict):
        raise ValueError("training manifest lacks base-model/tokenizer identity")
    model_id = base.get("id")
    requested_revision = base.get("requested_revision")
    revision = base.get("resolved_snapshot_hash")
    tokenizer_revision = tokenizer_record.get("resolved_snapshot_hash")
    if (
        type(model_id) is not str
        or type(requested_revision) is not str
        or type(revision) is not str
        or len(revision) != 40
        or any(character not in "0123456789abcdef" for character in revision)
        or revision != requested_revision
        or tokenizer_revision != revision
    ):
        raise ValueError(
            "training manifest model/tokenizer snapshots are not one pinned commit"
        )
    adapter_output = verify_artifact_directory(
        adapter_dir, manifest.get("adapter", {}), ADAPTER_SUBDIR
    )
    tokenizer_output = verify_artifact_directory(
        adapter_dir, tokenizer_record.get("artifacts", {}), TOKENIZER_SUBDIR
    )

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    set_seed(seed)
    tokenizer = AutoTokenizer.from_pretrained(tokenizer_output, use_fast=True)
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        revision=revision,
        torch_dtype=torch.bfloat16,
        attn_implementation="sdpa",
        trust_remote_code=False,
    )
    model = PeftModel.from_pretrained(model, adapter_output)
    model.eval()
    if torch.cuda.is_available():
        model.to("cuda")
    return model, tokenizer, manifest


def adapter_provenance(
    adapter_dir: Path, manifest: dict[str, Any]
) -> dict[str, object]:
    """Extract the immutable model identity recorded in evaluation reports."""

    manifest_path = adapter_dir / "training-manifest.json"
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing training manifest: {manifest_path}")
    base = manifest.get("base_model")
    adapter = manifest.get("adapter")
    run = manifest.get("run")
    if (
        not isinstance(base, dict)
        or not isinstance(adapter, dict)
        or not isinstance(run, dict)
    ):
        raise ValueError(
            "training manifest lacks base-model, adapter, or run identity"
        )
    inputs = manifest.get("inputs")
    attestation = (
        inputs.get("dataset_attestation") if isinstance(inputs, dict) else None
    )
    if not isinstance(attestation, dict):
        raise ValueError("training manifest lacks dataset attestation provenance")
    environment = attestation.get("environment")
    return {
        "training_manifest_sha256": sha256_file(manifest_path),
        "base_model_id": base.get("id"),
        "base_model_revision": base.get("resolved_snapshot_hash"),
        "adapter_sha256": adapter.get("sha256"),
        "run_name": run.get("name"),
        "dataset_sha256": attestation.get("dataset_sha256"),
        "environment_sha256": (
            environment.get("environment_sha256")
            if isinstance(environment, dict)
            else None
        ),
        "held_out_contract_sha256": attestation.get(
            "held_out_contract_sha256"
        ),
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument(
        "--prompt-file",
        type=Path,
        required=True,
        help="exact <task>/<env>/<state>/<tactic> prefix produced by Peano Lab",
    )
    parser.add_argument(
        "--environment-file",
        type=Path,
        required=True,
        help=(
            "JSON object with classical and the exact capabilities preimage "
            "used to validate the prompt hash"
        ),
    )
    parser.add_argument("--seed", type=int, default=20260728)
    parser.add_argument("--max-new-tokens", type=int, default=64)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-p", type=float, default=0.95)
    return parser


def _read_environment(path: Path) -> PromptEnvironment:
    value = json.loads(path.read_text(encoding="utf-8"))
    if type(value) is not dict or tuple(value) != ("classical", "capabilities"):
        raise ValueError(
            "environment file must contain classical then capabilities"
        )
    if type(value["classical"]) is not bool:
        raise ValueError("environment classical mode must be a Boolean")
    return PromptEnvironment(
        value["classical"],
        CapabilityIdentity.from_record(value["capabilities"]),
    )


def main() -> int:
    args = _parser().parse_args()
    model, tokenizer, manifest = load_adapter(args.adapter, seed=args.seed)
    environment = _read_environment(args.environment_file)
    if environment != attested_training_environment(manifest):
        raise ValueError(
            "inference environment differs from the adapter's training authority"
        )
    tactic = generate_one_tactic(
        model=model,
        tokenizer=tokenizer,
        prompt=args.prompt_file.read_text(encoding="utf-8"),
        environment=environment,
        max_new_tokens=args.max_new_tokens,
        do_sample=args.sample,
        temperature=args.temperature,
        top_p=args.top_p,
    )
    print(tactic)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
