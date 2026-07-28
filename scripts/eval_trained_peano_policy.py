#!/usr/bin/env python3
"""Evaluate one trained Peano adapter with the public surface and kernel."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON, Path(__file__).resolve().parent):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import eval_peano_policy as evaluator  # noqa: E402
from peano_lab.batch import (  # noqa: E402
    MAX_BATCH_TACTICS,
    capability_sha256,
    verify_proof,
)
from peano_lab.kernel.formulas import (  # noqa: E402
    ParseError,
    parse_formula_with_names,
    pretty_formula,
)
from peano_lab.ui.prove import MAX_INPUT, MAX_NUMERAL, oversized_numeral  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    attested_training_environment,
    model_v1_environment,
)
from training.peano_policy.generate import (  # noqa: E402
    PeanoPolicyAdapter,
    adapter_provenance,
    load_adapter,
)
from training.peano_policy.manifest import (  # noqa: E402
    ADAPTER_SUBDIR,
    TOKENIZER_SUBDIR,
    require_safetensors_adapter,
    verify_artifact_directory,
)
from training.peano_policy.runtime import (  # noqa: E402
    runtime_identity,
    slurm_job_identity,
    source_files_identity,
)


MAX_USER_FORMULA_RECURSION_MARKERS = 256
MAX_POLICY_NEW_TOKENS = 1_024
MAX_POLICY_MODEL_CALLS = 4_096
MAX_POLICY_GENERATED_TOKENS = 262_144
MAX_TRAINING_MANIFEST_BYTES = 16_000_000
_FORMULA_RECURSION_MARKER = re.compile(
    r"(?<![A-Za-z0-9_'])(?:forall|exists|S)(?![A-Za-z0-9_'])|->|[∀∃~¬→(]"
)


def _strict_json_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate training-manifest key {key!r}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> object:
    raise ValueError(f"non-finite JSON number {value!r}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--adapter", type=Path, required=True)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--goal",
        action="append",
        default=[],
        metavar="NAME",
        help="frozen held-out goal name (repeatable; default: all held-out goals)",
    )
    selection.add_argument(
        "--theorem",
        metavar="FORMULA",
        help="one closed PA formula to prove under the adapter's attested authority",
    )
    parser.add_argument(
        "--k",
        type=int,
        help="rollouts per goal (default: 1 for --theorem, 8 for benchmarks)",
    )
    parser.add_argument("--max-steps", type=int, default=16)
    parser.add_argument("--seed", type=int, default=20260728)
    parser.add_argument("--max-new-tokens", type=int)
    parser.add_argument("--sample", action="store_true")
    parser.add_argument("--temperature", type=float)
    parser.add_argument("--top-p", type=float)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--proof-output",
        type=Path,
        help="write the selected kernel-replayed proof as a pasteable .pa script",
    )
    parser.add_argument(
        "--require-proof",
        action="store_true",
        help="return exit status 1 unless every selected goal has a checked proof",
    )
    parser.add_argument("--compact", action="store_true")
    return parser


def _preflight_user_theorem(value: object) -> str:
    """Validate and retain the exact closed theorem source before model loading."""

    if type(value) is not str or not value.strip():
        raise ValueError("theorem must be non-empty text")
    if value != value.strip() or len(value) > MAX_INPUT:
        raise ValueError(
            f"theorem must have no outer space and at most {MAX_INPUT} characters"
        )
    if value.splitlines() != [value]:
        raise ValueError("theorem must fit on one line")
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in value
    ):
        raise ValueError("theorem contains an unsafe control or format character")
    oversized = oversized_numeral(value)
    if oversized is not None:
        raise ValueError(
            f"theorem contains numeral {oversized} above the resource limit "
            f"of {MAX_NUMERAL}"
        )
    recursion_markers = len(_FORMULA_RECURSION_MARKER.findall(value))
    if recursion_markers > MAX_USER_FORMULA_RECURSION_MARKERS:
        raise ValueError(
            "formula nesting exceeds the deterministic limit of "
            f"{MAX_USER_FORMULA_RECURSION_MARKERS}"
        )
    try:
        target, names = parse_formula_with_names(value)
    except RecursionError:
        raise ValueError(
            "invalid theorem: formula nesting exceeded the parser resource limit"
        ) from None
    except (ParseError, TypeError, ValueError) as exc:
        message = " ".join(str(exc).split()) or type(exc).__name__
        raise ValueError(f"invalid theorem: {message}") from None
    if names:
        raise ValueError(
            "theorem must be closed; quantify free variables explicitly: "
            + ", ".join(names)
        )
    canonical = pretty_formula(target, list(names))
    try:
        reparsed, reparsed_names = parse_formula_with_names(canonical)
    except (ParseError, RecursionError, TypeError, ValueError) as exc:
        raise RuntimeError("formula printer output did not parse back") from exc
    if reparsed_names or reparsed != target:
        raise RuntimeError("formula parser/printer round trip changed the original goal")
    return value


def _absolute_output(path: Path | None) -> Path | None:
    if path is None:
        return None
    absolute = Path(os.path.abspath(os.fspath(path)))
    if os.path.lexists(absolute):
        return absolute
    return absolute.parent.resolve(strict=False) / absolute.name


def _require_new_output(path: Path | None, *, label: str) -> None:
    if path is not None and os.path.lexists(path):
        raise FileExistsError(f"refusing to replace {label}: {path}")


def _inside(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _validate_output_location(path: Path | None, adapter_dir: Path) -> None:
    if path is None:
        return
    repository = REPOSITORY_ROOT.resolve()
    results = (repository / "results").resolve(strict=False)
    if _inside(path, repository) and (path == results or not _inside(path, results)):
        raise ValueError("repository-local outputs must live below results/")
    for closed in (
        (adapter_dir / ADAPTER_SUBDIR).resolve(strict=False),
        (adapter_dir / TOKENIZER_SUBDIR).resolve(strict=False),
    ):
        if _inside(path, closed):
            raise ValueError("output must not mutate a closed adapter artifact tree")


def _read_adapter_manifest_snapshot(
    adapter_dir: Path,
) -> tuple[dict[str, object], str]:
    manifest_path = adapter_dir / "training-manifest.json"
    if (
        not manifest_path.is_file()
        or manifest_path.is_symlink()
        or manifest_path.stat().st_size > MAX_TRAINING_MANIFEST_BYTES
    ):
        raise ValueError("training manifest must be one bounded regular file")
    payload = manifest_path.read_bytes()
    if not payload or len(payload) > MAX_TRAINING_MANIFEST_BYTES:
        raise ValueError("training manifest size changed or is empty")
    try:
        value = json.loads(
            payload,
            object_pairs_hook=_strict_json_object,
            parse_constant=_reject_json_constant,
        )
    except (UnicodeError, json.JSONDecodeError, RecursionError, ValueError) as exc:
        raise ValueError(f"training manifest is invalid JSON: {exc}") from None
    if type(value) is not dict:
        raise ValueError("training manifest must be one JSON object")
    return value, hashlib.sha256(payload).hexdigest()


def _recheck_adapter_snapshot(
    adapter_dir: Path,
    manifest: dict[str, object],
    manifest_sha256: str,
) -> None:
    current, current_sha256 = _read_adapter_manifest_snapshot(adapter_dir)
    if current_sha256 != manifest_sha256 or current != manifest:
        raise RuntimeError("adapter training manifest changed during evaluation")
    adapter_record = manifest.get("adapter")
    tokenizer_record = manifest.get("tokenizer")
    if type(adapter_record) is not dict or type(tokenizer_record) is not dict:
        raise ValueError("training manifest lacks adapter/tokenizer artifacts")
    require_safetensors_adapter(adapter_record)
    verify_artifact_directory(adapter_dir, adapter_record, ADAPTER_SUBDIR)
    tokenizer_artifacts = tokenizer_record.get("artifacts")
    if type(tokenizer_artifacts) is not dict:
        raise ValueError("training manifest lacks tokenizer artifact identity")
    verify_artifact_directory(
        adapter_dir,
        tokenizer_artifacts,
        TOKENIZER_SUBDIR,
    )


def _atomic_create_text(path: Path, text: str) -> None:
    """Publish complete UTF-8 text without replacing any existing directory entry."""

    path.parent.mkdir(parents=True, exist_ok=True)
    _require_new_output(path, label="output")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            raise FileExistsError(f"refusing to replace output: {path}") from None
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


def _user_goal(canonical_statement: str, environment: object) -> evaluator.EvalGoal:
    capabilities = getattr(environment, "capabilities", None)
    classical = getattr(environment, "classical", None)
    if (
        environment != model_v1_environment()
        or classical is not False
        or getattr(capabilities, "label", None) != "model-v1"
        or type(getattr(capabilities, "allowed_theorems", None)) is not tuple
    ):
        raise ValueError("adapter does not expose the fixed intuitionistic model-v1 authority")
    name_hash = hashlib.sha256(canonical_statement.encode("utf-8")).hexdigest()[:12]
    return evaluator.EvalGoal(
        f"user-{name_hash}",
        canonical_statement,
        classical=False,
        surface_profile="model-v1",
        allowed_theorems=capabilities.allowed_theorems,
    )


def _checked_proof_publication(
    report: evaluator.EvaluationReport,
) -> tuple[dict[str, object], str | None]:
    """Select the smallest proved rollout and independently replay it for export."""

    if len(report.goals) != 1:
        raise ValueError("proof publication requires exactly one theorem")
    goal_result = report.goals[0]
    proved = tuple(
        attempt for attempt in goal_result.attempts if attempt.status == "proof"
    )
    if not proved:
        return {"status": "no-proof"}, None
    selected = min(
        proved,
        key=lambda attempt: (
            attempt.proof_nodes if attempt.proof_nodes is not None else sys.maxsize,
            len(attempt.commands),
            attempt.sample,
        ),
    )
    replay = verify_proof(
        goal_result.goal.statement,
        selected.commands,
        request_id=f"publish-{goal_result.goal.name}",
        classical=goal_result.goal.classical,
        capabilities=goal_result.goal.capabilities,
    )
    if (
        replay.status != "proved"
        or replay.kernel_checked is not True
        or replay.theorem != goal_result.canonical_statement
        or replay.proof_nodes != selected.proof_nodes
        or replay.tactics_applied != len(selected.commands)
        or replay.failed_tactics != 0
        or replay.surface != goal_result.goal.capabilities.label
        or replay.environment_sha256
        != capability_sha256(goal_result.goal.capabilities)
    ):
        raise RuntimeError("refusing to publish a proof that failed exact kernel replay")
    script = "\n".join(
        (
            f"pa prove {goal_result.canonical_statement}",
            *selected.commands,
            "qed",
            "",
        )
    )
    return (
        {
            "status": "proof",
            "sample": selected.sample,
            "proof_nodes": selected.proof_nodes,
            "commands": list(selected.commands),
            "script": script,
            "script_sha256": hashlib.sha256(script.encode("utf-8")).hexdigest(),
            "replay": {
                "status": replay.status,
                "kernel_checked": replay.kernel_checked,
                "proof_nodes": replay.proof_nodes,
                "surface": replay.surface,
                "environment_sha256": replay.environment_sha256,
            },
        },
        script,
    )


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
    if (
        type(max_new_tokens) is not int
        or not 1 <= max_new_tokens <= MAX_POLICY_NEW_TOKENS
    ):
        raise ValueError(
            f"max_new_tokens must lie between 1 and {MAX_POLICY_NEW_TOKENS}"
        )
    if (
        type(temperature) not in {int, float}
        or not math.isfinite(temperature)
        or temperature <= 0
    ):
        raise ValueError("temperature must be positive and finite")
    if (
        type(top_p) not in {int, float}
        or not math.isfinite(top_p)
        or not 0 < top_p <= 1
    ):
        raise ValueError("top_p must be finite and lie in (0, 1]")
    return {
        "max_new_tokens": max_new_tokens,
        "do_sample": bool(args.sample),
        "temperature": float(temperature),
        "top_p": float(top_p),
    }


def _validate_decode_overrides(args: argparse.Namespace) -> None:
    """Reject dangerous explicit overrides before loading model weights."""

    if args.max_new_tokens is not None and not (
        type(args.max_new_tokens) is int
        and 1 <= args.max_new_tokens <= MAX_POLICY_NEW_TOKENS
    ):
        raise ValueError(
            f"max_new_tokens must lie between 1 and {MAX_POLICY_NEW_TOKENS}"
        )
    if args.temperature is not None and not (
        type(args.temperature) in {int, float}
        and math.isfinite(args.temperature)
        and args.temperature > 0
    ):
        raise ValueError("temperature must be positive and finite")
    if args.top_p is not None and not (
        type(args.top_p) in {int, float}
        and math.isfinite(args.top_p)
        and 0 < args.top_p <= 1
    ):
        raise ValueError("top_p must be finite and lie in (0, 1]")


def _validate_search_budget(
    *,
    rollouts: int,
    max_steps: int,
    max_new_tokens: int | None,
) -> None:
    model_calls = rollouts * max_steps
    if model_calls > MAX_POLICY_MODEL_CALLS:
        raise ValueError(
            f"search requests {model_calls} model calls; limit is "
            f"{MAX_POLICY_MODEL_CALLS}"
        )
    if (
        max_new_tokens is not None
        and model_calls * max_new_tokens > MAX_POLICY_GENERATED_TOKENS
    ):
        generated = model_calls * max_new_tokens
        raise ValueError(
            f"search requests up to {generated} generated tokens; limit is "
            f"{MAX_POLICY_GENERATED_TOKENS}"
        )


def _evaluation_sources() -> dict[str, object]:
    """Fingerprint every repository file that can affect model judging."""

    return source_files_identity(
        (
            Path(__file__),
            REPOSITORY_ROOT / "scripts" / "eval_peano_policy.py",
            REPOSITORY_ROOT / "scripts" / "peano_policy_proof_request.py",
            *sorted((REPOSITORY_ROOT / "training" / "peano_policy").glob("*.py")),
            *sorted((PEANO_PYTHON / "peano_lab").rglob("*.py")),
        )
    )


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    if args.proof_output is not None and args.theorem is None:
        parser.error("--proof-output requires --theorem")
    user_theorem_source: str | None = None
    if args.theorem is not None:
        try:
            user_theorem_source = _preflight_user_theorem(args.theorem)
        except ValueError as exc:
            parser.error(str(exc))

    benchmark_goals: tuple[evaluator.EvalGoal, ...] | None = None
    try:
        _validate_decode_overrides(args)
        if user_theorem_source is None:
            benchmark_goals = evaluator.selected_goals(args.goal)
    except ValueError as exc:
        parser.error(str(exc))

    rollouts = args.k if args.k is not None else (1 if args.theorem is not None else 8)
    if not 1 <= rollouts <= 256:
        parser.error("--k must lie between 1 and 256")
    if not 1 <= args.max_steps <= MAX_BATCH_TACTICS:
        parser.error(
            f"--max-steps must lie between 1 and {MAX_BATCH_TACTICS}"
        )
    if args.theorem is not None and rollouts > 1 and not args.sample:
        parser.error("--theorem with --k greater than 1 requires --sample")
    try:
        _validate_search_budget(
            rollouts=rollouts,
            max_steps=args.max_steps,
            max_new_tokens=args.max_new_tokens,
        )
    except ValueError as exc:
        parser.error(str(exc))

    output = _absolute_output(args.output)
    proof_output = _absolute_output(args.proof_output)
    if output is not None and proof_output is not None and (
        output == proof_output
        or output in proof_output.parents
        or proof_output in output.parents
    ):
        parser.error("--output and --proof-output must be separate non-nested files")
    _require_new_output(output, label="evaluation report")
    _require_new_output(proof_output, label="proof script")

    adapter_dir = args.adapter.resolve()
    try:
        _validate_output_location(output, adapter_dir)
        _validate_output_location(proof_output, adapter_dir)
    except ValueError as exc:
        parser.error(str(exc))
    manifest_snapshot, manifest_sha256 = _read_adapter_manifest_snapshot(adapter_dir)
    options = _decode_options(manifest_snapshot, args)
    decoded_token_limit = options.get("max_new_tokens")
    if type(decoded_token_limit) is not int:  # pragma: no cover - decoder invariant
        raise RuntimeError("validated decode token limit was lost")
    _validate_search_budget(
        rollouts=rollouts,
        max_steps=args.max_steps,
        max_new_tokens=decoded_token_limit,
    )
    environment = attested_training_environment(manifest_snapshot)
    evaluation_sources = _evaluation_sources()
    model, tokenizer, manifest = load_adapter(adapter_dir, seed=args.seed)
    if manifest != manifest_snapshot:
        raise RuntimeError("adapter training manifest changed while the model loaded")
    provenance = adapter_provenance(adapter_dir, manifest)
    if provenance.get("training_manifest_sha256") != manifest_sha256:
        raise RuntimeError("adapter provenance does not match the loaded manifest")
    _recheck_adapter_snapshot(adapter_dir, manifest_snapshot, manifest_sha256)
    import torch

    evaluation_job = slurm_job_identity()
    provenance["evaluation"] = {
        "sources": evaluation_sources,
        "runtime": runtime_identity(torch),
        "job": evaluation_job,
    }
    run = manifest.get("run")
    run_name = run.get("name") if isinstance(run, dict) else "unknown-run"
    policy = PeanoPolicyAdapter(
        model=model,
        tokenizer=tokenizer,
        environment=environment,
        name=(
            f"peano-policy:{run_name}:"
            f"{str(provenance['training_manifest_sha256'])[:12]}"
        ),
        provenance=provenance,
        **options,
    )
    goals = (
        (_user_goal(user_theorem_source, environment),)
        if user_theorem_source is not None
        else benchmark_goals
    )
    if goals is None:  # pragma: no cover - guarded by the selection above
        raise RuntimeError("evaluation goal selection was lost")
    report = evaluator.evaluate(
        policy,
        goals,
        k=rollouts,
        max_steps=args.max_steps,
        seed=args.seed,
    )
    if _evaluation_sources() != evaluation_sources:
        raise RuntimeError("evaluation source changed while the run was active")
    if slurm_job_identity() != evaluation_job:
        raise RuntimeError("evaluation deployment changed while the run was active")
    _recheck_adapter_snapshot(adapter_dir, manifest_snapshot, manifest_sha256)

    report_record = report.to_dict()
    proof_script: str | None = None
    if user_theorem_source is not None:
        publication, proof_script = _checked_proof_publication(report)
        report_record["proof_publication"] = publication

    # Proof replay is part of publication, so provenance is checked again after it.
    if _evaluation_sources() != evaluation_sources:
        raise RuntimeError("evaluation source changed during proof replay")
    if slurm_job_identity() != evaluation_job:
        raise RuntimeError("evaluation deployment changed during proof replay")
    _recheck_adapter_snapshot(adapter_dir, manifest_snapshot, manifest_sha256)

    indent = None if args.compact else 2
    report_text = json.dumps(
        report_record,
        ensure_ascii=False,
        allow_nan=False,
        indent=indent,
        sort_keys=True,
        separators=(",", ":") if indent is None else None,
    ) + "\n"
    if output is not None:
        # The JSON record contains the complete replay script and hash, so it
        # is the primary artifact. Publish it before the optional convenience
        # copy; no failure path ever deletes a directory entry it did not own.
        _atomic_create_text(output, report_text)
    if proof_output is not None and proof_script is not None:
        _atomic_create_text(proof_output, proof_script)
    if output is not None:
        print(json.dumps({"report": str(output)}, sort_keys=True))
    else:
        print(report_text, end="")

    all_proved = report.proved_goals == len(report.goals)
    if (user_theorem_source is not None or args.require_proof) and not all_proved:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
