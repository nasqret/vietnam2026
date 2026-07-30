#!/usr/bin/env python3
"""Evaluate pinned Qwen base weights under the exact model-v3 authority.

This is a deliberately separate scientific baseline, not a mode switch in the
trained-adapter evaluator.  The completed adapter artifact supplies immutable
comparison authority, but its PEFT weights are never attached.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON, Path(__file__).resolve().parent):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import eval_trained_peano_policy as trained  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    MODEL_V3_HELD_OUT_POLICY_GOALS,
)
from training.peano_policy.generate import (  # noqa: E402
    PRETRAINED_BASE_POLICY_KIND,
    PeanoPretrainedBasePolicy,
)
from training.peano_policy.manifest import sha256_json  # noqa: E402
from training.peano_policy.pretrained_baseline import (  # noqa: E402
    BASELINE_POLICY_KIND,
    comparison_authority_record,
    load_pretrained_base,
    validate_comparison_manifest,
)
from training.peano_policy.runtime import (  # noqa: E402
    runtime_identity,
    slurm_job_identity,
    source_files_identity,
)
from training.peano_policy.search import SearchLimits  # noqa: E402


BASELINE_SEED = 20_260_728
BASELINE_MAX_NEW_TOKENS = 256
BASELINE_TEMPERATURE = 1.0
BASELINE_TOP_P = 1.0
BASELINE_SEARCH_LIMITS = SearchLimits(
    max_depth=32,
    beam_width=16,
    candidates_per_state=8,
    max_model_calls=512,
    max_states=4_096,
)
BASELINE_OUTPUT_NAME = "pretrained-base-heldout-search-wmi-b16-c8-d32.json"
BASELINE_GOAL_SET_SHA256 = (
    "198beaf753c0abab3151b4913ca9da63094ab6f28807e949e651e629336470d5"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--comparison-adapter",
        type=Path,
        required=True,
        help=(
            "completed model-v3 adapter directory used only as immutable "
            "comparison authority"
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "fixed-name report below the comparison run (default: "
            f"COMPARISON/{BASELINE_OUTPUT_NAME})"
        ),
    )
    return parser


def _baseline_sources() -> dict[str, object]:
    """Fingerprint every current source file that can affect this baseline."""

    return source_files_identity(
        (
            Path(__file__),
            REPOSITORY_ROOT / "scripts" / "eval_trained_peano_policy.py",
            REPOSITORY_ROOT / "scripts" / "eval_peano_policy.py",
            REPOSITORY_ROOT / "scripts" / "peano_policy_proof_request.py",
            *sorted((REPOSITORY_ROOT / "training" / "peano_policy").glob("*.py")),
            *sorted((PEANO_PYTHON / "peano_lab").rglob("*.py")),
        )
    )


def _fixed_output(adapter_dir: Path, requested: Path | None) -> Path:
    expected = adapter_dir / BASELINE_OUTPUT_NAME
    output = expected if requested is None else Path(os.path.abspath(os.fspath(requested)))
    if output != expected:
        raise ValueError(
            "pretrained baseline output must be the fixed direct child of the "
            f"comparison run: {expected}"
        )
    trained._validate_output_location(output, adapter_dir)
    trained._require_new_output(output, label="pretrained-base evaluation report")
    return output


def _assert_frozen_goals(goals: tuple[object, ...]) -> None:
    expected_names = tuple(name for name, _ in MODEL_V3_HELD_OUT_POLICY_GOALS)
    expected_sources = tuple(source for _, source in MODEL_V3_HELD_OUT_POLICY_GOALS)
    if (
        len(goals) != 4
        or tuple(getattr(goal, "name", None) for goal in goals) != expected_names
        or tuple(getattr(goal, "statement", None) for goal in goals) != expected_sources
    ):
        raise RuntimeError("pretrained baseline goal set differs from frozen model-v3")


def _require_comparison_job_binding(
    manifest: dict[str, object], evaluation_job: dict[str, object]
) -> None:
    """On Slurm, bind the comparison manifest to the declared predecessor."""

    current_job_id = os.environ.get("SLURM_JOB_ID")
    predecessor = os.environ.get("PEANO_TRAIN_JOB_ID")
    if current_job_id is None and predecessor is None:
        return
    if (
        type(current_job_id) is not str
        or not current_job_id.isdigit()
        or type(predecessor) is not str
        or not predecessor.isdigit()
    ):
        raise RuntimeError("WMI baseline requires one numeric training predecessor")
    runtime = manifest.get("runtime")
    training_job = runtime.get("job") if type(runtime) is dict else None
    submission = evaluation_job.get("submission")
    if (
        type(training_job) is not dict
        or training_job.get("job_id") != predecessor
        or type(submission) is not dict
        or submission.get("dependency_job_id") != predecessor
        or evaluation_job.get("job_id") != current_job_id
    ):
        raise RuntimeError(
            "baseline comparison manifest differs from its declared training job"
        )


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    adapter_dir = args.comparison_adapter.resolve()
    try:
        output = _fixed_output(adapter_dir, args.output)
    except (FileExistsError, ValueError) as exc:
        _parser().error(str(exc))

    manifest, manifest_sha256 = trained._read_adapter_manifest_snapshot(adapter_dir)
    # First closed-tree verification occurs before even importing a model runtime.
    trained._recheck_adapter_snapshot(adapter_dir, manifest, manifest_sha256)
    environment = validate_comparison_manifest(manifest)
    comparison = comparison_authority_record(
        adapter_dir,
        manifest,
        manifest_sha256=manifest_sha256,
    )
    goals = trained._selected_benchmark_goals([], environment)
    _assert_frozen_goals(goals)
    goal_set_sha256 = trained.evaluator._goal_set_sha256(goals)
    if goal_set_sha256 != BASELINE_GOAL_SET_SHA256:
        raise RuntimeError("pretrained baseline goal-set fingerprint changed")
    comparison["goal_set_sha256"] = goal_set_sha256
    comparison["seed"] = BASELINE_SEED
    comparison["search_limits"] = trained._search_limits_record(
        BASELINE_SEARCH_LIMITS
    )
    comparison["max_new_tokens"] = BASELINE_MAX_NEW_TOKENS
    comparison["sampling"] = {
        "do_sample": True,
        "temperature": BASELINE_TEMPERATURE,
        "top_p": BASELINE_TOP_P,
    }
    comparison["comparison_authority_sha256"] = sha256_json(comparison)
    trained._validate_kernel_search_budget(
        BASELINE_SEARCH_LIMITS,
        goal_count=4,
        max_new_tokens=BASELINE_MAX_NEW_TOKENS,
    )

    evaluation_sources = _baseline_sources()
    evaluation_job = slurm_job_identity()
    _require_comparison_job_binding(manifest, evaluation_job)
    model, tokenizer = load_pretrained_base(
        adapter_dir,
        manifest,
        seed=BASELINE_SEED,
    )
    # Loading the base model/tokenizer must not mutate or replace the authority.
    trained._recheck_adapter_snapshot(adapter_dir, manifest, manifest_sha256)
    import torch

    provenance = {
        "comparison_authority": comparison,
        "weights": {
            "kind": "pretrained-base-no-peft",
            "adapter_attached": False,
            "base_model_id": comparison["base_model"]["id"],
            "base_model_revision": comparison["base_model"]["revision"],
        },
        "evaluation": {
            "sources": evaluation_sources,
            "runtime": runtime_identity(torch),
            "job": evaluation_job,
        },
    }
    policy_name = f"peano-policy:pretrained-base:{manifest_sha256[:12]}"
    policy = PeanoPretrainedBasePolicy(
        model=model,
        tokenizer=tokenizer,
        environment=environment,
        name=policy_name,
        max_new_tokens=BASELINE_MAX_NEW_TOKENS,
        do_sample=True,
        temperature=BASELINE_TEMPERATURE,
        top_p=BASELINE_TOP_P,
        provenance=provenance,
    )
    if (
        BASELINE_POLICY_KIND != PRETRAINED_BASE_POLICY_KIND
        or policy.evaluation_identity.get("kind") != BASELINE_POLICY_KIND
    ):
        raise RuntimeError("pretrained baseline policy identity was lost")
    report, search_record = trained._evaluate_kernel_search(
        policy,
        goals,
        seed=BASELINE_SEED,
        limits=BASELINE_SEARCH_LIMITS,
    )

    if _baseline_sources() != evaluation_sources:
        raise RuntimeError("baseline evaluation source changed while the run was active")
    if slurm_job_identity() != evaluation_job:
        raise RuntimeError("baseline evaluation deployment changed while the run was active")
    trained._recheck_adapter_snapshot(adapter_dir, manifest, manifest_sha256)

    record = report.to_dict()
    if record.get("goal_set_sha256") != goal_set_sha256:
        raise RuntimeError("baseline evaluator changed the frozen goal set")
    record["mode"] = "kernel-guided-search"
    record["search"] = search_record
    # The policy identity contains the same record.  This top-level copy makes
    # the treatment/control comparison easy to audit without changing the v4
    # evaluator or licensing this report in the trained-adapter replay gate.
    record["pretrained_base_comparison"] = comparison

    # Final immutable-authority and deployment recheck immediately precedes
    # no-overwrite publication.
    if _baseline_sources() != evaluation_sources:
        raise RuntimeError("baseline source changed before report publication")
    if slurm_job_identity() != evaluation_job:
        raise RuntimeError("baseline deployment changed before report publication")
    trained._recheck_adapter_snapshot(adapter_dir, manifest, manifest_sha256)
    payload = json.dumps(
        record,
        ensure_ascii=False,
        allow_nan=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    trained._atomic_create_text(output, payload)
    print(json.dumps({"report": str(output)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
