#!/usr/bin/env python3
"""Use the local 0.6B Peano pilot for tactics or kernel-checked proofs.

With no formula option this starts an interactive theorem-proving session.
``--next-tactic FORMULA`` asks the untrusted model for ranked first actions;
``--theorem FORMULA`` runs bounded verifier-guided search and publishes a
script only after independent kernel replay against the original formula.

Torch, Transformers, and PEFT are imported only after CLI and artifact checks.
"""

from __future__ import annotations

import argparse
import importlib
import json
import math
import os
from pathlib import Path
import random
import sys
from typing import Any


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = Path(__file__).resolve().parent
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for _root in (REPOSITORY_ROOT, SCRIPTS_ROOT, PEANO_PYTHON):
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))


DEFAULT_ADAPTER = (
    REPOSITORY_ROOT / "results/peano-policy/qwen3-0.6b-local-pilot"
)
DEFAULT_RESULTS = REPOSITORY_ROOT / "results/peano-policy/local-pilot-interactive"
MANIFEST_NAME = "local-pilot-manifest.json"
MAX_MANIFEST_BYTES = 16_000_000


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate manifest key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _read_manifest(adapter_dir: Path) -> tuple[dict[str, object], Path]:
    manifest_path = adapter_dir / MANIFEST_NAME
    if (
        manifest_path.is_symlink()
        or not manifest_path.is_file()
        or not 0 < manifest_path.stat().st_size <= MAX_MANIFEST_BYTES
    ):
        raise ValueError("local pilot manifest is missing or unsafe")
    try:
        value = json.loads(
            manifest_path.read_text(encoding="utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValueError(f"invalid local pilot manifest: {exc}") from None
    if type(value) is not dict:
        raise ValueError("local pilot manifest must be a JSON object")
    return value, manifest_path


def validate_local_adapter(adapter_dir: Path) -> dict[str, object]:
    """Verify every loader-visible byte and the fixed Peano authority."""

    from train_peano_local_pilot import (
        FORMAT,
        MODEL_ID,
        MODEL_REVISION,
        VERSION,
        snapshot_identity,
    )
    from training.peano_policy.contract import (
        environment_record,
        model_v2_environment,
    )
    from training.peano_policy.manifest import (
        require_safetensors_adapter,
        sha256_file,
        sha256_json,
        verify_artifact_directory,
    )

    lexical = adapter_dir.expanduser().absolute()
    if lexical.is_symlink() or not lexical.is_dir():
        raise ValueError("adapter root must be one plain directory")
    absolute = lexical.resolve(strict=True)
    manifest, manifest_path = _read_manifest(absolute)
    if (
        manifest.get("format") != FORMAT
        or manifest.get("v") != VERSION
        or manifest.get("status") != "complete"
    ):
        raise ValueError("unsupported or incomplete local pilot manifest")
    base = manifest.get("base_model")
    if (
        type(base) is not dict
        or base.get("model_id") != MODEL_ID
        or base.get("revision") != MODEL_REVISION
        or snapshot_identity(Path(str(base.get("path")))) != base
    ):
        raise ValueError("local pilot base-model identity does not validate")
    dataset = manifest.get("dataset")
    expected_environment = environment_record(model_v2_environment())
    if type(dataset) is not dict or dataset.get("environment") != expected_environment:
        raise ValueError("local pilot lacks the exact model-v2 authority")
    source = manifest.get("source")
    files = source.get("files") if type(source) is dict else None
    if type(files) is not dict or not files:
        raise ValueError("local pilot source identity is malformed")
    for relative, expected in files.items():
        if (
            type(relative) is not str
            or type(expected) is not str
            or Path(relative).is_absolute()
            or ".." in Path(relative).parts
        ):
            raise ValueError("local pilot source identity contains an unsafe path")
        path = REPOSITORY_ROOT / relative
        if path.is_symlink() or not path.is_file() or sha256_file(path) != expected:
            raise ValueError(f"local pilot source changed: {relative}")
    if source.get("sha256") != sha256_json(files):
        raise ValueError("local pilot source aggregate identity is malformed")
    adapter_record = manifest.get("adapter")
    tokenizer_record = manifest.get("tokenizer")
    if type(adapter_record) is not dict or type(tokenizer_record) is not dict:
        raise ValueError("local pilot artifact identities are malformed")
    require_safetensors_adapter(adapter_record)
    adapter_path = verify_artifact_directory(absolute, adapter_record, "adapter")
    tokenizer_path = verify_artifact_directory(
        absolute, tokenizer_record, "tokenizer"
    )
    return {
        "root": absolute,
        "manifest": manifest,
        "manifest_path": manifest_path,
        "adapter_path": adapter_path,
        "tokenizer_path": tokenizer_path,
        "environment": model_v2_environment(),
    }


def load_runtime(
    adapter_dir: Path,
    *,
    seed: int,
    device: str,
    max_new_tokens: int,
    sample: bool,
    temperature: float,
    top_p: float,
) -> object:
    """Load one validated pilot and adapt it to the existing safe REPL."""

    validated = validate_local_adapter(adapter_dir)
    from peano_lab.batch import verify_proof
    from peano_lab.ui.prove import SurfaceCapabilities
    from peano_policy_repl import ReplRuntime
    from train_peano_local_pilot import snapshot_identity
    from training.peano_policy.generate import (
        PeanoPolicyAdapter,
        PeanoPolicyCandidateAdapter,
    )
    from training.peano_policy.manifest import sha256_file
    from training.peano_policy.search import SearchLimits, search

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed

    if device == "mps" and not torch.backends.mps.is_available():
        raise RuntimeError("MPS is unavailable; run outside the restricted sandbox")
    random.seed(seed)
    torch.manual_seed(seed)
    if device == "mps":
        torch.mps.manual_seed(seed)
    set_seed(seed)
    manifest = validated["manifest"]
    base = manifest["base_model"]
    snapshot_before = snapshot_identity(Path(str(base["path"])))
    tokenizer = AutoTokenizer.from_pretrained(
        validated["tokenizer_path"], use_fast=True, local_files_only=True
    )
    model = AutoModelForCausalLM.from_pretrained(
        str(base["path"]),
        dtype=torch.float16,
        attn_implementation="sdpa",
        trust_remote_code=False,
        use_safetensors=True,
        local_files_only=True,
    )
    model = PeftModel.from_pretrained(
        model, validated["adapter_path"], is_trainable=False
    )
    model.to(device)
    model.eval()
    if snapshot_identity(Path(str(base["path"]))) != snapshot_before:
        raise RuntimeError("base snapshot changed while loading the local pilot")

    environment = validated["environment"]
    provenance = {
        "format": manifest["format"],
        "manifest_sha256": sha256_file(validated["manifest_path"]),
        "base_model_id": base["model_id"],
        "base_model_revision": base["revision"],
        "base_snapshot_sha256": base["sha256"],
        "adapter_sha256": manifest["adapter"]["sha256"],
        "dataset_sha256": manifest["dataset"]["builder_manifest"]["sha256"],
        "completed_optimizer_steps": manifest["run"][
            "completed_optimizer_steps"
        ],
    }
    base_policy = PeanoPolicyAdapter(
        model=model,
        tokenizer=tokenizer,
        environment=environment,
        name="peano-policy:qwen3-0.6b-local-pilot",
        max_new_tokens=max_new_tokens,
        do_sample=sample,
        temperature=temperature,
        top_p=top_p,
        provenance=provenance,
    )
    policy = PeanoPolicyCandidateAdapter(base_policy, seed=seed)
    capabilities = SurfaceCapabilities(
        label=environment.capabilities.label,
        allowed_commands=frozenset(environment.capabilities.allowed_commands or ()),
        allowed_theorems=frozenset(environment.capabilities.allowed_theorems or ()),
    )
    return ReplRuntime(
        policy=policy,
        capabilities=capabilities,
        classical=False,
        adapter_identity={
            "directory": str(validated["root"]),
            "policy": policy.evaluation_identity,
        },
        search=search,
        verify=verify_proof,
        make_limits=SearchLimits,
    )


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("value must be an integer") from None
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _probability(value: str) -> float:
    try:
        parsed = float(value)
    except ValueError:
        raise argparse.ArgumentTypeError("value must be a number") from None
    if not math.isfinite(parsed) or not 0 < parsed <= 1:
        raise argparse.ArgumentTypeError("value must lie in (0, 1]")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", type=Path, default=DEFAULT_ADAPTER)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    action = parser.add_mutually_exclusive_group()
    action.add_argument("--theorem", help="prove one closed formula, then exit")
    action.add_argument(
        "--next-tactic",
        metavar="FORMULA",
        help="show ranked model proposals for one initial theorem state",
    )
    parser.add_argument("--seed", type=int, default=20260729)
    parser.add_argument("--device", choices=("mps", "cpu"), default="mps")
    parser.add_argument("--max-new-tokens", type=_positive_int, default=64)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--temperature", type=float, default=0.8)
    parser.add_argument("--top-p", type=_probability, default=0.95)
    parser.add_argument("--depth", type=_positive_int, default=24)
    parser.add_argument("--beam", type=_positive_int, default=4)
    parser.add_argument("--candidates", type=_positive_int, default=4)
    parser.add_argument("--model-calls", type=_positive_int, default=128)
    parser.add_argument("--states", type=_positive_int, default=2048)
    return parser


def _initial_goals(theorem: str) -> tuple[str, ...]:
    from peano_lab.engine.state import start
    from peano_lab.engine.trace import render_goals
    from peano_lab.kernel.formulas import parse_formula_with_names

    target, names = parse_formula_with_names(theorem)
    if names:
        raise ValueError(
            "theorem must be closed; quantify: " + ", ".join(names)
        )
    return tuple(render_goals(start(target, tuple(names))))


def main() -> int:
    args = _parser().parse_args()
    if type(args.seed) is not int or args.seed < 0:
        raise ValueError("seed must be a non-negative integer")
    if not math.isfinite(args.temperature) or args.temperature <= 0:
        raise ValueError("temperature must be positive and finite")
    runtime = load_runtime(
        args.adapter,
        seed=args.seed,
        device=args.device,
        max_new_tokens=args.max_new_tokens,
        sample=args.sample,
        temperature=args.temperature,
        top_p=args.top_p,
    )
    repl = importlib.import_module("peano_policy_repl")
    budget = repl.SearchBudget(
        max_depth=args.depth,
        beam_width=args.beam,
        candidates_per_state=args.candidates,
        max_model_calls=args.model_calls,
        max_states=args.states,
    )
    if args.next_tactic is not None:
        theorem = repl.normalize_theorem_input(args.next_tactic)
        goals = _initial_goals(theorem)
        candidates = runtime.policy.propose(
            goals, max_candidates=args.candidates
        )
        print(
            json.dumps(
                {
                    "status": "untrusted-tactic-proposals",
                    "theorem": theorem,
                    "goals": list(goals),
                    "candidates": list(candidates),
                    "warning": "Execute tactics in Peano Lab; model text is not proof.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    if args.theorem is not None:
        theorem = repl.normalize_theorem_input(args.theorem)
        attempt = repl.run_checked_search(theorem, runtime, budget)
        artifacts = repl.save_attempt(attempt, args.results_dir)
        if attempt.proved:
            print("KERNEL CHECKED PROOF")
            print(attempt.proof_script, end="")
            print(f"Proof: {artifacts.proof}")
        else:
            print("NO KERNEL-CHECKED PROOF within the configured bounds.")
        print(f"Report: {artifacts.report}")
        return 0 if attempt.proved else 1
    return repl.run_repl(runtime, budget, args.results_dir)


if __name__ == "__main__":
    raise SystemExit(main())
