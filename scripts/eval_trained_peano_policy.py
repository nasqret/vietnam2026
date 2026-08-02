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
    MODEL_V3_HELD_OUT_POLICY_GOALS,
    attested_training_environment,
    model_v1_environment,
    model_v2_environment,
    model_v3_environment,
)
from training.peano_policy.generate import (  # noqa: E402
    MAX_CANDIDATES_PER_MODEL_CALL,
    PeanoPolicyCandidateAdapter,
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
from training.peano_policy.search import (  # noqa: E402
    MAX_SEARCH_DEPTH,
    SearchLimits,
    SearchResult,
    search as kernel_guided_search,
)


MAX_USER_FORMULA_RECURSION_MARKERS = 256
MAX_POLICY_NEW_TOKENS = 1_024
MAX_POLICY_MODEL_CALLS = 4_096
MAX_POLICY_GENERATED_TOKENS = 262_144
MAX_POLICY_SEARCH_STATES = 4_096
MAX_POLICY_SEARCH_BEAM = 256
MAX_POLICY_SEARCH_GENERATED_TOKENS = 4_194_304
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
    parser.add_argument(
        "--mode",
        choices=("rollout", "search"),
        default="rollout",
        help=(
            "rollout preserves the v1 one-path evaluator; search runs bounded "
            "kernel-guided beam search (default: rollout)"
        ),
    )
    parser.add_argument("--max-steps", type=int, default=16)
    parser.add_argument("--search-beam-width", type=int, default=16)
    parser.add_argument("--search-candidates-per-state", type=int, default=8)
    parser.add_argument("--search-max-model-calls", type=int, default=512)
    parser.add_argument("--search-max-states", type=int, default=4096)
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
    require_protected = manifest.get("prompt_version") == 3
    verify_artifact_directory(
        adapter_dir,
        adapter_record,
        ADAPTER_SUBDIR,
        require_protected=require_protected,
    )
    tokenizer_artifacts = tokenizer_record.get("artifacts")
    if type(tokenizer_artifacts) is not dict:
        raise ValueError("training manifest lacks tokenizer artifact identity")
    verify_artifact_directory(
        adapter_dir,
        tokenizer_artifacts,
        TOKENIZER_SUBDIR,
        require_protected=require_protected,
    )


def _require_training_job_binding(
    manifest: dict[str, object], evaluation_job: dict[str, object]
) -> dict[str, object]:
    """Bind a scheduled evaluation to the job that produced its manifest.

    The submission helper exports the training predecessor as
    ``PEANO_TRAIN_JOB_ID`` and records the same logical predecessor in the immutable
    submission ledger.  Neither claim is sufficient alone: this gate also
    reads the completed adapter's training manifest and requires all three
    job identifiers to agree before model weights are loaded.
    """

    current_job_id = os.environ.get("SLURM_JOB_ID")
    predecessor = os.environ.get("PEANO_TRAIN_JOB_ID")
    proof_request_id = os.environ.get("PEANO_PROOF_REQUEST_ID")
    if current_job_id is None and predecessor is None:
        if evaluation_job.get("scheduler") == "slurm":
            raise RuntimeError("Slurm evaluation lacks its job environment")
        return {"status": "local-unbound"}
    if predecessor is None and proof_request_id is not None:
        runtime = manifest.get("runtime")
        training_job = runtime.get("job") if type(runtime) is dict else None
        submission = evaluation_job.get("submission")
        training_job_id = (
            training_job.get("job_id") if type(training_job) is dict else None
        )
        if (
            type(current_job_id) is not str
            or not current_job_id.isdigit()
            or type(proof_request_id) is not str
            or re.fullmatch(r"[0-9a-f]{64}", proof_request_id) is None
            or type(training_job) is not dict
            or training_job.get("scheduler") != "slurm"
            or type(training_job_id) is not str
            or not training_job_id.isdigit()
            or evaluation_job.get("scheduler") != "slurm"
            or evaluation_job.get("job_id") != current_job_id
            or type(submission) is not dict
            or submission.get("dependency_job_id") not in {None, ""}
        ):
            raise RuntimeError(
                "WMI proof request cannot bind its completed adapter manifest"
            )
        return {
            "status": "slurm-proof-request-bound",
            "training_manifest_job_id": training_job_id,
            "evaluation_job_id": current_job_id,
            "dependency_job_id": None,
        }
    if (
        type(current_job_id) is not str
        or not current_job_id.isdigit()
        or type(predecessor) is not str
        or not predecessor.isdigit()
    ):
        raise RuntimeError("WMI evaluation requires one numeric training predecessor")

    runtime = manifest.get("runtime")
    training_job = runtime.get("job") if type(runtime) is dict else None
    submission = evaluation_job.get("submission")
    if (
        type(training_job) is not dict
        or training_job.get("scheduler") != "slurm"
        or training_job.get("job_id") != predecessor
        or evaluation_job.get("scheduler") != "slurm"
        or evaluation_job.get("job_id") != current_job_id
        or type(submission) is not dict
        or submission.get("dependency_job_id") != predecessor
    ):
        raise RuntimeError(
            "evaluation adapter manifest differs from its declared training job"
        )
    return {
        "status": "slurm-bound",
        "training_manifest_job_id": predecessor,
        "evaluation_job_id": current_job_id,
        "dependency_job_id": predecessor,
    }


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
    label = getattr(capabilities, "label", None)
    expected = (
        model_v1_environment()
        if label == "model-v1"
        else model_v2_environment()
        if label == "model-v2"
        else model_v3_environment()
        if label == "model-v3"
        else None
    )
    if (
        environment != expected
        or classical is not False
        or label not in {"model-v1", "model-v2", "model-v3"}
        or type(getattr(capabilities, "allowed_theorems", None)) is not tuple
    ):
        raise ValueError(
            "adapter does not expose a fixed intuitionistic model-v1, "
            "model-v2, or model-v3 authority"
        )
    name_hash = hashlib.sha256(canonical_statement.encode("utf-8")).hexdigest()[:12]
    return evaluator.EvalGoal(
        f"user-{name_hash}",
        canonical_statement,
        classical=False,
        surface_profile=capabilities.label,
        allowed_theorems=capabilities.allowed_theorems,
    )


def _benchmark_goals_for_environment(
    goals: tuple[evaluator.EvalGoal, ...],
    environment: object,
) -> tuple[evaluator.EvalGoal, ...]:
    """Execute frozen targets under the adapter's exact attested authority."""

    return tuple(
        evaluator.EvalGoal(
            goal.name,
            goal.statement,
            classical=False,
            surface_profile=environment.capabilities.label,
            allowed_theorems=environment.capabilities.allowed_theorems,
        )
        for goal in goals
    )


def _selected_benchmark_goals(
    names: list[str],
    environment: object,
) -> tuple[evaluator.EvalGoal, ...]:
    """Select the sealed benchmark appropriate to the adapter contract.

    Model-v3 trains on the complete old public theorem ladder, so evaluating
    it on model-v2's tail-ladder holdouts would be direct target leakage.  Its
    four target propositions are separately frozen by the v3 dataset
    attestation and are not library theorem names.
    """

    prompt_version = getattr(environment, "prompt_version", None)
    if prompt_version == 3:
        available = tuple(
            evaluator.EvalGoal(name, statement)
            for name, statement in MODEL_V3_HELD_OUT_POLICY_GOALS
        )
    else:
        available = evaluator.DEFAULT_HELD_OUT_GOALS
    table = {goal.name: goal for goal in available}
    if len(set(names)) != len(names):
        raise ValueError("held-out goal names may not be repeated")
    unknown = [name for name in names if name not in table]
    if unknown:
        raise ValueError("unknown held-out goal(s): " + ", ".join(unknown))
    selected = available if not names else tuple(table[name] for name in names)
    return _benchmark_goals_for_environment(selected, environment)


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


def _search_limits_record(limits: SearchLimits) -> dict[str, int]:
    return {
        "max_depth": limits.max_depth,
        "beam_width": limits.beam_width,
        "candidates_per_state": limits.candidates_per_state,
        "max_model_calls": limits.max_model_calls,
        "max_states": limits.max_states,
    }


def _search_limits_from_args(args: argparse.Namespace) -> SearchLimits:
    if not 1 <= args.search_beam_width <= MAX_POLICY_SEARCH_BEAM:
        raise ValueError(
            f"search beam width must lie between 1 and {MAX_POLICY_SEARCH_BEAM}"
        )
    if not (
        1
        <= args.search_candidates_per_state
        <= MAX_CANDIDATES_PER_MODEL_CALL
    ):
        raise ValueError(
            "search candidates per state must lie between 1 and "
            f"{MAX_CANDIDATES_PER_MODEL_CALL}"
        )
    if not 1 <= args.search_max_model_calls <= MAX_POLICY_MODEL_CALLS:
        raise ValueError(
            "search max model calls must lie between 1 and "
            f"{MAX_POLICY_MODEL_CALLS}"
        )
    if not 1 <= args.search_max_states <= MAX_POLICY_SEARCH_STATES:
        raise ValueError(
            "search max states must lie between 1 and "
            f"{MAX_POLICY_SEARCH_STATES}"
        )
    return SearchLimits(
        max_depth=args.max_steps,
        beam_width=args.search_beam_width,
        candidates_per_state=args.search_candidates_per_state,
        max_model_calls=args.search_max_model_calls,
        max_states=args.search_max_states,
    )


def _stable_search_seed(seed: int, goal: evaluator.EvalGoal) -> int:
    payload = json.dumps(
        [1, seed, goal.name, goal.statement],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (2**63 - 1)


def _search_error(result: SearchResult) -> str | None:
    if result.proved:
        return None
    if not result.diagnostics:
        return f"kernel-guided search {result.status} without a checked proof"
    final = result.diagnostics[-1]
    return (
        f"kernel-guided search {result.status}: {final.kind}: {final.message}"
    )[:1_000]


def _evaluate_kernel_search(
    adapter: PeanoPolicyAdapter,
    goals: tuple[evaluator.EvalGoal, ...],
    *,
    seed: int,
    limits: SearchLimits,
) -> tuple[evaluator.EvaluationReport, dict[str, object]]:
    """Run one bounded verifier-guided search per theorem.

    A fresh candidate wrapper gives every theorem an order-independent seed
    stream and exact decoder counters.  Each wrapper makes one batched physical
    model call for every policy call counted by :func:`kernel_guided_search`.
    """

    goal_results: list[evaluator.GoalResult] = []
    search_results: list[dict[str, object]] = []
    total_model_calls = 0
    total_states_expanded = 0
    total_states_discovered = 0
    total_candidates_executed = 0
    total_sequences_requested = 0
    total_sequences_returned = 0
    total_candidate_lines = 0
    total_malformed_sequences = 0
    frontier_peak = 0

    for goal in goals:
        if adapter.policy_environment != evaluator._goal_environment(goal):
            raise ValueError(
                f"policy environment does not match evaluation goal {goal.name!r}"
            )
        goal_seed = _stable_search_seed(seed, goal)
        candidate_policy = PeanoPolicyCandidateAdapter(
            adapter,
            seed=goal_seed,
            name=f"{adapter.name}:kernel-guided-candidates",
        )
        result = kernel_guided_search(
            goal.statement,
            candidate_policy,
            capabilities=goal.capabilities,
            classical=goal.classical,
            limits=limits,
        )
        generation = candidate_policy.generation_provenance
        decoder_calls = generation["model_generate_calls"]
        if decoder_calls != result.model_calls:
            raise RuntimeError(
                "candidate-policy decoder calls differ from search model-call count"
            )
        if generation["candidate_sequences_requested"] != (
            result.model_calls * limits.candidates_per_state
        ):
            raise RuntimeError("candidate-policy request accounting is inconsistent")

        attempt_status: evaluator.AttemptStatus
        if result.status == "proof":
            attempt_status = "proof"
        elif result.status == "limit":
            attempt_status = "limit"
        else:
            attempt_status = "failing"
        attempt = evaluator.AttemptResult(
            0,
            goal_seed,
            attempt_status,
            result.commands,
            result.certificate_nodes,
            _search_error(result),
        )
        goal_results.append(
            evaluator.GoalResult(
                goal,
                result.theorem,
                (attempt,),
            )
        )
        search_results.append(
            {
                "name": goal.name,
                "environment_sha256": capability_sha256(goal.capabilities),
                "result": result.to_dict(),
                "decoder": generation,
            }
        )
        total_model_calls += result.model_calls
        total_states_expanded += result.states_expanded
        total_states_discovered += result.states_discovered
        total_candidates_executed += result.candidates_executed
        total_sequences_requested += int(generation["candidate_sequences_requested"])
        total_sequences_returned += int(generation["candidate_sequences_returned"])
        total_candidate_lines += int(generation["candidate_lines_returned"])
        total_malformed_sequences += int(
            generation["malformed_sequences_rejected"]
        )
        frontier_peak = max(frontier_peak, result.frontier_peak)

    policy_name = f"{adapter.name}:kernel-guided-search"
    identity = {
        "name": policy_name,
        "kind": "peano-kernel-guided-search-v1",
        "base_policy": adapter.evaluation_identity,
        "limits": _search_limits_record(limits),
        "seed": seed,
        "seed_schedule": "sha256-json-v1(seed,goal_name,goal_statement)",
        "decoder_batching": "one-model-generate-call-per-search-state",
    }
    report = evaluator.EvaluationReport(
        policy_name,
        identity,
        seed,
        1,
        limits.max_depth,
        tuple(goal_results),
    )
    search_record: dict[str, object] = {
        "engine": "training.peano_policy.search.search-v1",
        "budget_scope": "per-goal",
        "limits": _search_limits_record(limits),
        "aggregate_upper_bound": {
            "model_generate_calls": len(goals) * limits.max_model_calls,
            "candidate_sequences": (
                len(goals)
                * limits.max_model_calls
                * limits.candidates_per_state
            ),
            "generated_sequence_tokens": (
                len(goals)
                * limits.max_model_calls
                * limits.candidates_per_state
                * adapter.max_new_tokens
            ),
        },
        "actual": {
            "model_generate_calls": total_model_calls,
            "states_expanded": total_states_expanded,
            "states_discovered": total_states_discovered,
            "candidates_executed": total_candidates_executed,
            "candidate_sequences_requested": total_sequences_requested,
            "candidate_sequences_returned": total_sequences_returned,
            "candidate_lines_returned": total_candidate_lines,
            "malformed_sequences_rejected": total_malformed_sequences,
            "frontier_peak_per_goal": frontier_peak,
        },
        "goals": search_results,
    }
    return report, search_record


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


def _validate_kernel_search_budget(
    limits: SearchLimits,
    *,
    goal_count: int,
    max_new_tokens: int | None,
) -> None:
    """Bound the aggregate batched-decoder work before model loading."""

    if type(goal_count) is not int or goal_count < 1:
        raise ValueError("kernel search needs at least one goal")
    total_calls = goal_count * limits.max_model_calls
    if total_calls > MAX_POLICY_MODEL_CALLS:
        raise ValueError(
            f"kernel search requests up to {total_calls} model calls across "
            f"{goal_count} goals; limit is {MAX_POLICY_MODEL_CALLS}"
        )
    if max_new_tokens is not None:
        generated = (
            total_calls
            * limits.candidates_per_state
            * max_new_tokens
        )
        if generated > MAX_POLICY_SEARCH_GENERATED_TOKENS:
            raise ValueError(
                "kernel search requests up to "
                f"{generated} generated sequence tokens; limit is "
                f"{MAX_POLICY_SEARCH_GENERATED_TOKENS}"
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

    try:
        _validate_decode_overrides(args)
        if len(set(args.goal)) != len(args.goal):
            raise ValueError("held-out goal names may not be repeated")
        known_goal_names = set(evaluator.HELD_OUT_LADDER_NAMES) | {
            name for name, _ in MODEL_V3_HELD_OUT_POLICY_GOALS
        }
        unknown_goals = [name for name in args.goal if name not in known_goal_names]
        if unknown_goals:
            raise ValueError(
                "unknown held-out goal(s): " + ", ".join(unknown_goals)
            )
    except ValueError as exc:
        parser.error(str(exc))
    selected_goal_count = (
        1
        if user_theorem_source is not None
        else len(args.goal) if args.goal else 4
    )

    if args.mode == "search" and args.k not in {None, 1}:
        parser.error(
            "--mode search performs one branching search per goal; --k must be 1"
        )
    if args.mode == "search":
        rollouts = 1
    elif args.k is not None:
        rollouts = args.k
    else:
        rollouts = 1 if args.theorem is not None else 8
    if not 1 <= rollouts <= 256:
        parser.error("--k must lie between 1 and 256")
    if not 1 <= args.max_steps <= MAX_BATCH_TACTICS:
        parser.error(
            f"--max-steps must lie between 1 and {MAX_BATCH_TACTICS}"
        )
    if args.mode == "search" and args.max_steps > MAX_SEARCH_DEPTH:
        parser.error(
            f"--mode search limits --max-steps to {MAX_SEARCH_DEPTH}"
        )
    if (
        args.mode == "rollout"
        and args.theorem is not None
        and rollouts > 1
        and not args.sample
    ):
        parser.error("--theorem with --k greater than 1 requires --sample")
    search_limits: SearchLimits | None = None
    try:
        if args.mode == "search":
            search_limits = _search_limits_from_args(args)
            _validate_kernel_search_budget(
                search_limits,
                goal_count=selected_goal_count,
                max_new_tokens=args.max_new_tokens,
            )
        else:
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
    if search_limits is not None:
        _validate_kernel_search_budget(
            search_limits,
            goal_count=selected_goal_count,
            max_new_tokens=decoded_token_limit,
        )
    else:
        _validate_search_budget(
            rollouts=rollouts,
            max_steps=args.max_steps,
            max_new_tokens=decoded_token_limit,
        )
    environment = attested_training_environment(manifest_snapshot)
    benchmark_goals: tuple[evaluator.EvalGoal, ...] | None = None
    if user_theorem_source is None:
        try:
            benchmark_goals = _selected_benchmark_goals(args.goal, environment)
        except ValueError as exc:
            parser.error(str(exc))
    evaluation_sources = _evaluation_sources()
    evaluation_job = slurm_job_identity()
    training_job_binding = _require_training_job_binding(
        manifest_snapshot,
        evaluation_job,
    )
    model, tokenizer, manifest = load_adapter(adapter_dir, seed=args.seed)
    if manifest != manifest_snapshot:
        raise RuntimeError("adapter training manifest changed while the model loaded")
    provenance = adapter_provenance(adapter_dir, manifest)
    if provenance.get("training_manifest_sha256") != manifest_sha256:
        raise RuntimeError("adapter provenance does not match the loaded manifest")
    _recheck_adapter_snapshot(adapter_dir, manifest_snapshot, manifest_sha256)
    import torch

    provenance["evaluation"] = {
        "sources": evaluation_sources,
        "runtime": runtime_identity(torch),
        "job": evaluation_job,
        "training_job_binding": training_job_binding,
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
    search_record: dict[str, object] | None = None
    if search_limits is None:
        report = evaluator.evaluate(
            policy,
            goals,
            k=rollouts,
            max_steps=args.max_steps,
            seed=args.seed,
        )
    else:
        report, search_record = _evaluate_kernel_search(
            policy,
            goals,
            seed=args.seed,
            limits=search_limits,
        )
    if _evaluation_sources() != evaluation_sources:
        raise RuntimeError("evaluation source changed while the run was active")
    if slurm_job_identity() != evaluation_job:
        raise RuntimeError("evaluation deployment changed while the run was active")
    if (
        _require_training_job_binding(manifest_snapshot, evaluation_job)
        != training_job_binding
    ):
        raise RuntimeError("evaluation training-job binding changed while active")
    _recheck_adapter_snapshot(adapter_dir, manifest_snapshot, manifest_sha256)

    report_record = report.to_dict()
    if search_record is not None:
        report_record["mode"] = "kernel-guided-search"
        report_record["search"] = search_record
    proof_script: str | None = None
    if user_theorem_source is not None:
        publication, proof_script = _checked_proof_publication(report)
        report_record["proof_publication"] = publication

    # Proof replay is part of publication, so provenance is checked again after it.
    if _evaluation_sources() != evaluation_sources:
        raise RuntimeError("evaluation source changed during proof replay")
    if slurm_job_identity() != evaluation_job:
        raise RuntimeError("evaluation deployment changed during proof replay")
    if (
        _require_training_job_binding(manifest_snapshot, evaluation_job)
        != training_job_binding
    ):
        raise RuntimeError("evaluation training-job binding changed during proof replay")
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
