#!/usr/bin/env python3
"""Evaluate one trained Peano adapter with the public surface and kernel."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON, Path(__file__).resolve().parent):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import eval_peano_policy as evaluator  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    attested_training_environment,
)
from training.peano_policy.generate import (  # noqa: E402
    PeanoPolicyAdapter,
    adapter_provenance,
    load_adapter,
)
from training.peano_policy.manifest import write_manifest  # noqa: E402
from training.peano_policy.runtime import (  # noqa: E402
    runtime_identity,
    slurm_job_identity,
    source_files_identity,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", type=Path, required=True)
    parser.add_argument("--goal", action="append", default=[])
    parser.add_argument("--k", type=int, default=8)
    parser.add_argument("--max-steps", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20260728)
    parser.add_argument("--max-new-tokens", type=int)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-p", type=float)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--compact", action="store_true")
    return parser


def _decode_options(
    manifest: dict[str, object], args: argparse.Namespace
) -> dict[str, object]:
    stored = manifest.get("generation")
    if not isinstance(stored, dict):
        raise ValueError("training manifest has no generation configuration")
    max_new_tokens = (
        args.max_new_tokens
        if args.max_new_tokens is not None
        else stored.get("max_new_tokens")
    )
    temperature = (
        args.temperature if args.temperature is not None else stored.get("temperature")
    )
    top_p = args.top_p if args.top_p is not None else stored.get("top_p")
    if type(max_new_tokens) is not int or max_new_tokens <= 0:
        raise ValueError("max_new_tokens must be a positive integer")
    if type(temperature) not in {int, float} or temperature <= 0:
        raise ValueError("temperature must be positive")
    if type(top_p) not in {int, float} or not 0 < top_p <= 1:
        raise ValueError("top_p must lie in (0, 1]")
    return {
        "max_new_tokens": max_new_tokens,
        "do_sample": bool(args.sample),
        "temperature": float(temperature),
        "top_p": float(top_p),
    }


def _evaluation_sources() -> dict[str, object]:
    """Fingerprint every repository file that can affect model judging."""

    return source_files_identity(
        (
            Path(__file__),
            REPOSITORY_ROOT / "scripts" / "eval_peano_policy.py",
            *sorted((REPOSITORY_ROOT / "training" / "peano_policy").glob("*.py")),
            *sorted((PEANO_PYTHON / "peano_lab").rglob("*.py")),
        )
    )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    adapter_dir = args.adapter.resolve()
    evaluation_sources = _evaluation_sources()
    model, tokenizer, manifest = load_adapter(adapter_dir, seed=args.seed)
    provenance = adapter_provenance(adapter_dir, manifest)
    import torch

    evaluation_job = slurm_job_identity()
    provenance["evaluation"] = {
        "sources": evaluation_sources,
        "runtime": runtime_identity(torch),
        "job": evaluation_job,
    }
    options = _decode_options(manifest, args)
    run = manifest.get("run")
    run_name = run.get("name") if isinstance(run, dict) else "unknown-run"
    policy = PeanoPolicyAdapter(
        model=model,
        tokenizer=tokenizer,
        environment=attested_training_environment(manifest),
        name=(
            f"peano-policy:{run_name}:"
            f"{str(provenance['training_manifest_sha256'])[:12]}"
        ),
        provenance=provenance,
        **options,
    )
    report = evaluator.evaluate(
        policy,
        evaluator.selected_goals(args.goal),
        k=args.k,
        max_steps=args.max_steps,
        seed=args.seed,
    )
    if _evaluation_sources() != evaluation_sources:
        raise RuntimeError("evaluation source changed while the run was active")
    if slurm_job_identity() != evaluation_job:
        raise RuntimeError("evaluation deployment changed while the run was active")
    if args.output is not None:
        output = args.output.resolve()
        if output.exists():
            raise FileExistsError(f"refusing to replace evaluation report: {output}")
        write_manifest(output, report.to_dict())
        print(json.dumps({"report": str(output)}, sort_keys=True))
    else:
        print(report.json(indent=None if args.compact else 2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
