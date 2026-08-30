"""Strict, model-free replay of the frozen model-v3 evaluation report.

The trained policy and verifier-guided search are deliberately untrusted at
this boundary.  The report is accepted only when its complete benchmark
authority and search accounting match the repository-owned model-v3
contract.  Every attempt labelled ``proof`` is then executed again through
``peano_lab.batch.verify_proof``.  No model framework or adapter weight is
loaded by this module.

The public entry point consumes an immutable report file and returns a
canonical, self-digested attestation.  Parsing, structural validation, search
cross-checking, and kernel replay are separate phases so malformed input is
rejected before any proof execution begins.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import sys
import tempfile
from typing import Callable, Mapping, Sequence
import unicodedata


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

REPORT_FORMAT = "peano-policy-v3-evaluation-replay"
REPORT_VERSION = 1
EVALUATOR_VERSION = 4
EXPECTED_MODE = "kernel-guided-search"
EXPECTED_JUDGE = "checked_final(original_target, exact_mode)"
EXPECTED_GOAL_SET_SHA256 = (
    "198beaf753c0abab3151b4913ca9da63094ab6f28807e949e651e629336470d5"
)
EXPECTED_ENVIRONMENT_SHA256 = (
    "72372974368a4a2b66cba42fa48baae47e24bf811a8b2dd030027ea3b7f16363"
)
EXPECTED_GOAL_NAMES = (
    "closed_arithmetic_seven",
    "existential_subtraction_two",
    "double_right_zero",
    "consecutive_product_even",
)
EXPECTED_SEARCH_LIMITS = {
    "max_depth": 32,
    "beam_width": 16,
    "candidates_per_state": 8,
    "max_model_calls": 512,
    "max_states": 4_096,
}
EXPECTED_SEED = 20_260_728
EXPECTED_MAX_NEW_TOKENS = 256
EXPECTED_EVALUATION_SCRIPT = Path(
    "slurm/peano_wmi_eval_qwen3_1_7b_v3.sbatch"
)
EXPECTED_SUPPORT_SCRIPT = Path("scripts/wmi_job_environment.sh")
REPLAY_SCRIPT = Path("scripts/replay_peano_v3_evaluation.py")

MAX_REPORT_BYTES = 128 * 1024 * 1024
MAX_TEXT_CHARS = 4_000
MAX_ERROR_CHARS = 1_000
MAX_DIAGNOSTICS_PER_GOAL = 8_192
MAX_PROOF_NODES = 100_000
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_JOB_ID_RE = re.compile(r"[0-9]+")

ATTEMPT_STATUSES = ("proof", "invalid", "failing", "limit")
SEARCH_STATUSES = ("proof", "exhausted", "limit")


class EvaluationReplayError(ValueError):
    """The evaluation artifact failed structural or independent replay."""


@dataclass(frozen=True, slots=True)
class FrozenGoal:
    """One literal benchmark source and its canonical kernel theorem."""

    name: str
    source: str
    theorem: str


@dataclass(frozen=True, slots=True)
class FrozenAuthority:
    """Complete repository-owned authority for the four model-v3 goals."""

    goals: tuple[FrozenGoal, ...]
    capabilities: object
    environment: Mapping[str, object]
    allowed_theorems: tuple[str, ...]
    evaluator_source_sha256: str
    evaluator_semantic_sources: Mapping[str, object]
    evaluation_sources: Mapping[str, object]
    prompt_contract_sha256: str
    held_out_contract_sha256: str
    library_snapshot_sha256: str


@dataclass(frozen=True, slots=True)
class ReplayContext:
    """Trusted dependencies captured before an untrusted report is read."""

    authority: FrozenAuthority
    verify_proof: Callable[..., object]
    evaluation_script_sha256: str
    support_script_sha256: str
    replay_sources: Mapping[str, object]
    replay_runtime: Mapping[str, object]
    replay_job: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class ProofClaim:
    goal_index: int
    goal: FrozenGoal
    sample: int
    commands: tuple[str, ...]
    proof_nodes: int


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise EvaluationReplayError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> object:
    raise EvaluationReplayError(f"non-finite JSON number {value!r}")


def _canonical_json(value: object) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, RecursionError) as exc:
        raise EvaluationReplayError(f"value is not canonical JSON: {exc}") from exc


def _sha256_json(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def _mapping(value: object, label: str) -> dict[str, object]:
    if type(value) is not dict:
        raise EvaluationReplayError(f"{label}: expected one object")
    return value


def _array(value: object, label: str, *, maximum: int | None = None) -> list[object]:
    if type(value) is not list:
        raise EvaluationReplayError(f"{label}: expected one array")
    if maximum is not None and len(value) > maximum:
        raise EvaluationReplayError(f"{label}: exceeds the {maximum}-item limit")
    return value


def _exact_fields(record: Mapping[str, object], fields: set[str], label: str) -> None:
    actual = set(record)
    if actual != fields:
        missing = sorted(fields - actual)
        unknown = sorted(actual - fields)
        details: list[str] = []
        if missing:
            details.append("missing " + ", ".join(missing))
        if unknown:
            details.append("unknown " + ", ".join(unknown))
        raise EvaluationReplayError(f"{label}: incompatible fields ({'; '.join(details)})")


def _safe_text(
    value: object,
    label: str,
    *,
    maximum: int = MAX_TEXT_CHARS,
    allow_empty: bool = False,
) -> str:
    if type(value) is not str or (not value and not allow_empty) or len(value) > maximum:
        qualifier = "possibly empty" if allow_empty else "non-empty"
        raise EvaluationReplayError(
            f"{label}: expected {qualifier} text of at most {maximum} characters"
        )
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in value
    ):
        raise EvaluationReplayError(f"{label}: unsafe control or format character")
    return value


def _sha256(value: object, label: str) -> str:
    text = _safe_text(value, label, maximum=64)
    if _SHA256_RE.fullmatch(text) is None:
        raise EvaluationReplayError(f"{label}: expected lowercase SHA-256")
    return text


def _integer(
    value: object,
    label: str,
    *,
    minimum: int = 0,
    maximum: int | None = None,
) -> int:
    if type(value) is not int or value < minimum or (
        maximum is not None and value > maximum
    ):
        suffix = "" if maximum is None else f" and at most {maximum}"
        raise EvaluationReplayError(
            f"{label}: expected an integer of at least {minimum}{suffix}"
        )
    return value


def _read_regular(path: Path) -> bytes:
    if path.is_symlink():
        raise EvaluationReplayError("evaluation report may not be a symlink")
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise EvaluationReplayError(f"cannot open evaluation report {path}: {exc}") from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size < 2:
            raise EvaluationReplayError("evaluation report must be one non-empty regular file")
        if before.st_size > MAX_REPORT_BYTES:
            raise EvaluationReplayError(
                f"evaluation report exceeds {MAX_REPORT_BYTES} bytes"
            )
        with os.fdopen(descriptor, "rb") as stream:
            descriptor = -1
            raw = stream.read(MAX_REPORT_BYTES + 1)
            after = os.fstat(stream.fileno())
    except OSError as exc:
        raise EvaluationReplayError(f"cannot read evaluation report: {exc}") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(raw) > MAX_REPORT_BYTES:
        raise EvaluationReplayError(f"evaluation report exceeds {MAX_REPORT_BYTES} bytes")
    identity = lambda item: (  # noqa: E731 - compact immutable stat projection
        item.st_dev,
        item.st_ino,
        item.st_size,
        item.st_mtime_ns,
        item.st_ctime_ns,
    )
    if identity(before) != identity(after):
        raise EvaluationReplayError("evaluation report changed while it was read")
    return raw


def load_evaluation_report(path: Path) -> tuple[dict[str, object], bytes]:
    """Strictly parse the evaluator's bounded canonical JSON artifact."""

    raw = _read_regular(path)
    try:
        record = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, RecursionError) as exc:
        raise EvaluationReplayError(f"evaluation report is invalid JSON: {exc}") from exc
    if type(record) is not dict:
        raise EvaluationReplayError("evaluation report must contain one JSON object")
    canonical = (
        json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    if raw != canonical:
        raise EvaluationReplayError(
            "evaluation report is not canonical sorted two-space JSON"
        )
    return record, raw


def _validate_runtime_identity(value: object, label: str) -> Mapping[str, object]:
    runtime = _mapping(value, label)
    packages = _mapping(runtime.get("packages"), f"{label}.packages")
    if runtime.get("packages_sha256") != _sha256_json(packages):
        raise EvaluationReplayError(f"{label}: package digest mismatch")
    _safe_text(runtime.get("implementation"), f"{label}.implementation", maximum=64)
    _safe_text(runtime.get("python"), f"{label}.python", maximum=64)
    _safe_text(runtime.get("machine"), f"{label}.machine", maximum=128)
    _safe_text(runtime.get("platform"), f"{label}.platform", maximum=1_000)
    _safe_text(runtime.get("hostname"), f"{label}.hostname", maximum=255)
    return runtime


def _validate_source_group(
    value: object,
    expected: Mapping[str, object],
    label: str,
) -> None:
    record = _mapping(value, label)
    if record != expected:
        raise EvaluationReplayError(f"{label}: differs from the current source inventory")


def _validate_evaluator(
    value: object,
    authority: FrozenAuthority,
) -> None:
    record = _mapping(value, "evaluator")
    _exact_fields(record, {"source_sha256", "semantic_sources", "runtime"}, "evaluator")
    if record.get("source_sha256") != authority.evaluator_source_sha256:
        raise EvaluationReplayError("evaluator source differs from evaluator v4")
    _validate_source_group(
        record.get("semantic_sources"),
        authority.evaluator_semantic_sources,
        "evaluator semantic sources",
    )
    _validate_runtime_identity(record.get("runtime"), "evaluator runtime")


def _validate_evaluation_job(
    value: object,
    *,
    expected_job_id: str,
    expected_source_commit: str,
    context: ReplayContext,
) -> Mapping[str, object]:
    job = _mapping(value, "evaluation job")
    if job.get("scheduler") != "slurm" or job.get("job_id") != expected_job_id:
        raise EvaluationReplayError("evaluation report belongs to a different Slurm job")
    deployment = _mapping(job.get("deployment"), "evaluation deployment")
    source = _mapping(deployment.get("source_sync"), "evaluation source deployment")
    if (
        source.get("status") != "synced"
        or source.get("path") != ".peano-source-provenance.tsv"
        or source.get("git_commit") != expected_source_commit
        or source.get("git_dirty") is not False
    ):
        raise EvaluationReplayError("evaluation used a different or dirty source deployment")
    _sha256(source.get("sha256"), "evaluation source provenance hash")
    _safe_text(source.get("synced_at"), "evaluation source timestamp", maximum=128)

    support = _mapping(deployment.get("support_script"), "evaluation support script")
    if (
        support.get("status") != "declared"
        or support.get("path") != EXPECTED_SUPPORT_SCRIPT.as_posix()
        or support.get("sha256") != context.support_script_sha256
        or support.get("sourced_sha256") != context.support_script_sha256
    ):
        raise EvaluationReplayError("evaluation used a different WMI support script")
    script = _mapping(deployment.get("job_script"), "evaluation job script")
    expected_composite = hashlib.sha256(
        f"{context.evaluation_script_sha256}\n{context.support_script_sha256}\n".encode(
            "ascii"
        )
    ).hexdigest()
    if (
        script.get("status") != "declared"
        or script.get("path") != EXPECTED_EVALUATION_SCRIPT.as_posix()
        or script.get("file_sha256") != context.evaluation_script_sha256
        or script.get("sha256") != expected_composite
        or script.get("support_script") != support
    ):
        raise EvaluationReplayError("evaluation used a different frozen Slurm script")

    submission = _mapping(job.get("submission"), "evaluation submission")
    if (
        submission.get("job_id") != expected_job_id
        or submission.get("script") != EXPECTED_EVALUATION_SCRIPT.as_posix()
        or submission.get("script_sha256") != expected_composite
        or submission.get("git_commit") != expected_source_commit
        or submission.get("git_dirty") != "false"
    ):
        raise EvaluationReplayError("evaluation submission differs from its deployment")
    ledger = _mapping(job.get("ledger"), "evaluation submission ledger")
    if (
        ledger.get("path") != "logs/submissions.tsv"
        or ledger.get("row_sha256") != _sha256_json(submission)
    ):
        raise EvaluationReplayError("evaluation submission ledger binding is invalid")
    return job


def _validate_policy_identity(
    report: Mapping[str, object],
    authority: FrozenAuthority,
    *,
    expected_job_id: str,
    expected_source_commit: str,
    context: ReplayContext,
) -> tuple[Mapping[str, object], int]:
    identity = _mapping(report.get("policy_identity"), "policy identity")
    _exact_fields(
        identity,
        {
            "name",
            "kind",
            "base_policy",
            "limits",
            "seed",
            "seed_schedule",
            "decoder_batching",
        },
        "policy identity",
    )
    policy_name = _safe_text(report.get("policy"), "policy name", maximum=1_000)
    if (
        identity.get("name") != policy_name
        or identity.get("kind") != "peano-kernel-guided-search-v1"
        or identity.get("limits") != EXPECTED_SEARCH_LIMITS
        or identity.get("seed") != EXPECTED_SEED
        or identity.get("seed_schedule")
        != "sha256-json-v1(seed,goal_name,goal_statement)"
        or identity.get("decoder_batching")
        != "one-model-generate-call-per-search-state"
    ):
        raise EvaluationReplayError("kernel-guided search identity is forged")

    base = _mapping(identity.get("base_policy"), "base policy identity")
    _exact_fields(
        base,
        {
            "name",
            "kind",
            "prompt_version",
            "prompt_contract_sha256",
            "environment",
            "decoding",
            "provenance",
        },
        "base policy identity",
    )
    base_name = _safe_text(base.get("name"), "base policy name", maximum=1_000)
    if (
        policy_name != f"{base_name}:kernel-guided-search"
        or base.get("kind") != "peano-policy-adapter-v1"
        or base.get("prompt_version") != 3
        or base.get("prompt_contract_sha256") != authority.prompt_contract_sha256
        or base.get("environment") != authority.environment
    ):
        raise EvaluationReplayError("base policy does not use the exact model-v3 authority")

    decoding = _mapping(base.get("decoding"), "base policy decoding")
    _exact_fields(
        decoding,
        {"max_new_tokens", "do_sample", "temperature", "top_p"},
        "base policy decoding",
    )
    temperature = decoding.get("temperature")
    top_p = decoding.get("top_p")
    if (
        decoding.get("max_new_tokens") != EXPECTED_MAX_NEW_TOKENS
        or decoding.get("do_sample") is not True
        or type(temperature) is not float
        or not math.isfinite(temperature)
        or temperature <= 0
        or type(top_p) is not float
        or not math.isfinite(top_p)
        or not 0 < top_p <= 1
    ):
        raise EvaluationReplayError("base policy decoding differs from the frozen run")

    provenance = _mapping(base.get("provenance"), "adapter provenance")
    _exact_fields(
        provenance,
        {
            "training_manifest_sha256",
            "prompt_version",
            "prompt_contract_sha256",
            "base_model_id",
            "base_model_revision",
            "adapter_sha256",
            "run_name",
            "dataset_sha256",
            "environment_sha256",
            "held_out_contract_sha256",
            "library_snapshot_sha256",
            "evaluation",
        },
        "adapter provenance",
    )
    manifest_sha = _sha256(
        provenance.get("training_manifest_sha256"), "training manifest hash"
    )
    _sha256(provenance.get("adapter_sha256"), "adapter hash")
    _sha256(provenance.get("dataset_sha256"), "dataset hash")
    _safe_text(provenance.get("base_model_id"), "base model id", maximum=500)
    _safe_text(provenance.get("base_model_revision"), "base model revision", maximum=500)
    run_name = _safe_text(provenance.get("run_name"), "training run name", maximum=500)
    if (
        base_name != f"peano-policy:{run_name}:{manifest_sha[:12]}"
        or provenance.get("prompt_version") != 3
        or provenance.get("prompt_contract_sha256") != authority.prompt_contract_sha256
        or provenance.get("environment_sha256") != EXPECTED_ENVIRONMENT_SHA256
        or provenance.get("held_out_contract_sha256")
        != authority.held_out_contract_sha256
        or provenance.get("library_snapshot_sha256")
        != authority.library_snapshot_sha256
    ):
        raise EvaluationReplayError("adapter provenance differs from model-v3 authority")

    evaluation = _mapping(provenance.get("evaluation"), "evaluation provenance")
    _exact_fields(
        evaluation,
        {"sources", "runtime", "job", "training_job_binding"},
        "evaluation provenance",
    )
    _validate_source_group(
        evaluation.get("sources"), authority.evaluation_sources, "evaluation sources"
    )
    _validate_runtime_identity(evaluation.get("runtime"), "evaluation runtime")
    evaluation_job = _validate_evaluation_job(
        evaluation.get("job"),
        expected_job_id=expected_job_id,
        expected_source_commit=expected_source_commit,
        context=context,
    )
    binding = _mapping(
        evaluation.get("training_job_binding"),
        "evaluation training-job binding",
    )
    _exact_fields(
        binding,
        {
            "status",
            "training_manifest_job_id",
            "evaluation_job_id",
            "dependency_job_id",
        },
        "evaluation training-job binding",
    )
    submission = _mapping(
        evaluation_job.get("submission"),
        "evaluation submission",
    )
    dependency = submission.get("dependency_job_id")
    if (
        binding.get("status") != "slurm-bound"
        or binding.get("evaluation_job_id") != expected_job_id
        or binding.get("training_manifest_job_id") != dependency
        or binding.get("dependency_job_id") != dependency
        or type(dependency) is not str
        or _JOB_ID_RE.fullmatch(dependency) is None
    ):
        raise EvaluationReplayError(
            "evaluation training-job binding differs from its submission"
        )
    return base, EXPECTED_MAX_NEW_TOKENS


def _stable_search_seed(seed: int, goal: FrozenGoal) -> int:
    payload = json.dumps(
        [1, seed, goal.name, goal.source],
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big") & (2**63 - 1)


def _validate_command(value: object, label: str) -> str:
    command = _safe_text(value, label, maximum=MAX_TEXT_CHARS)
    if command != command.strip() or command.splitlines() != [command]:
        raise EvaluationReplayError(f"{label}: expected one complete tactic line")
    return command


def _validate_attempt(
    value: object,
    *,
    goal: FrozenGoal,
    goal_index: int,
    seed: int,
) -> tuple[dict[str, object], tuple[str, ...], ProofClaim | None]:
    attempt = _mapping(value, f"goal {goal.name} attempt")
    _exact_fields(
        attempt,
        {"sample", "seed", "status", "steps", "commands", "proof_nodes", "error"},
        f"goal {goal.name} attempt",
    )
    sample = _integer(attempt.get("sample"), f"{goal.name} sample", maximum=0)
    if attempt.get("seed") != _stable_search_seed(seed, goal):
        raise EvaluationReplayError(f"{goal.name}: attempt seed schedule mismatch")
    status = attempt.get("status")
    if status not in ATTEMPT_STATUSES:
        raise EvaluationReplayError(f"{goal.name}: invalid attempt status")
    raw_commands = _array(
        attempt.get("commands"),
        f"{goal.name} commands",
        maximum=EXPECTED_SEARCH_LIMITS["max_depth"],
    )
    commands = tuple(
        _validate_command(command, f"{goal.name} command {index}")
        for index, command in enumerate(raw_commands, 1)
    )
    steps = _integer(
        attempt.get("steps"),
        f"{goal.name} steps",
        maximum=EXPECTED_SEARCH_LIMITS["max_depth"],
    )
    if steps != len(commands):
        raise EvaluationReplayError(f"{goal.name}: steps differ from command count")
    nodes = attempt.get("proof_nodes")
    error = attempt.get("error")
    if status == "proof":
        proof_nodes = _integer(
            nodes,
            f"{goal.name} proof nodes",
            minimum=1,
            maximum=MAX_PROOF_NODES,
        )
        if not commands or error is not None:
            raise EvaluationReplayError(f"{goal.name}: malformed proof attempt")
        claim = ProofClaim(goal_index, goal, sample, commands, proof_nodes)
    else:
        if nodes is not None or type(error) is not str or not error:
            raise EvaluationReplayError(f"{goal.name}: malformed unsuccessful attempt")
        _safe_text(error, f"{goal.name} attempt error", maximum=MAX_ERROR_CHARS)
        claim = None
    return attempt, commands, claim


def _counter(
    record: Mapping[str, object],
    key: str,
    label: str,
    *,
    maximum: int | None = None,
) -> int:
    return _integer(record.get(key), f"{label}.{key}", maximum=maximum)


def _validate_diagnostics(value: object, *, goal: FrozenGoal, max_depth: int) -> None:
    diagnostics = _array(
        value,
        f"{goal.name} search diagnostics",
        maximum=MAX_DIAGNOSTICS_PER_GOAL,
    )
    for index, raw in enumerate(diagnostics, 1):
        label = f"{goal.name} diagnostic {index}"
        item = _mapping(raw, label)
        _exact_fields(item, {"kind", "depth", "state_sha256", "command", "message"}, label)
        _safe_text(item.get("kind"), f"{label}.kind", maximum=128)
        _integer(item.get("depth"), f"{label}.depth", maximum=max_depth)
        _sha256(item.get("state_sha256"), f"{label}.state_sha256")
        command = item.get("command")
        if command is not None:
            _validate_command(command, f"{label}.command")
        _safe_text(item.get("message"), f"{label}.message", maximum=MAX_ERROR_CHARS)


def _validate_search_goal(
    value: object,
    *,
    goal: FrozenGoal,
    attempt: Mapping[str, object],
    commands: tuple[str, ...],
    environment_sha256: str,
    limits: Mapping[str, int],
) -> dict[str, int]:
    record = _mapping(value, f"{goal.name} search record")
    _exact_fields(
        record,
        {"name", "environment_sha256", "result", "decoder"},
        f"{goal.name} search record",
    )
    if (
        record.get("name") != goal.name
        or record.get("environment_sha256") != environment_sha256
    ):
        raise EvaluationReplayError(f"{goal.name}: search authority mismatch")

    result = _mapping(record.get("result"), f"{goal.name} search result")
    _exact_fields(
        result,
        {
            "status",
            "theorem",
            "commands",
            "certificate_nodes",
            "diagnostics",
            "model_calls",
            "states_expanded",
            "states_discovered",
            "candidates_executed",
            "frontier_peak",
            "depth_reached",
        },
        f"{goal.name} search result",
    )
    status = result.get("status")
    if status not in SEARCH_STATUSES:
        raise EvaluationReplayError(f"{goal.name}: invalid search status")
    expected_attempt = {
        "proof": "proof",
        "exhausted": "failing",
        "limit": "limit",
    }[status]
    if (
        attempt.get("status") != expected_attempt
        or result.get("theorem") != goal.theorem
    ):
        raise EvaluationReplayError(f"{goal.name}: attempt and search result disagree")
    result_commands = _array(
        result.get("commands"),
        f"{goal.name} search commands",
        maximum=limits["max_depth"],
    )
    for index, command in enumerate(result_commands, 1):
        _validate_command(command, f"{goal.name} search command {index}")
    if (
        result_commands != list(commands)
        or result.get("certificate_nodes") != attempt.get("proof_nodes")
    ):
        raise EvaluationReplayError(f"{goal.name}: duplicated proof payload differs")
    if status == "proof":
        if not result_commands or type(result.get("certificate_nodes")) is not int:
            raise EvaluationReplayError(f"{goal.name}: proof search lacks certificate data")
    elif result_commands or result.get("certificate_nodes") is not None:
        raise EvaluationReplayError(f"{goal.name}: unsuccessful search claims proof data")

    model_calls = _counter(
        result, "model_calls", goal.name, maximum=limits["max_model_calls"]
    )
    states_expanded = _counter(
        result, "states_expanded", goal.name, maximum=limits["max_states"]
    )
    states_discovered = _counter(
        result, "states_discovered", goal.name, maximum=limits["max_states"]
    )
    candidates_executed = _counter(
        result,
        "candidates_executed",
        goal.name,
        maximum=model_calls * limits["candidates_per_state"],
    )
    frontier_peak = _counter(
        result, "frontier_peak", goal.name, maximum=limits["beam_width"]
    )
    depth_reached = _counter(
        result, "depth_reached", goal.name, maximum=limits["max_depth"]
    )
    if (
        model_calls < 1
        or model_calls != states_expanded
        or states_expanded > states_discovered
        or states_discovered < 1
        or frontier_peak < 1
        or (status == "proof" and depth_reached != len(commands))
    ):
        raise EvaluationReplayError(f"{goal.name}: inconsistent search counters")
    _validate_diagnostics(
        result.get("diagnostics"), goal=goal, max_depth=limits["max_depth"]
    )

    decoder = _mapping(record.get("decoder"), f"{goal.name} decoder")
    _exact_fields(
        decoder,
        {
            "model_generate_calls",
            "candidate_sequences_requested",
            "candidate_sequences_returned",
            "candidate_lines_returned",
            "malformed_sequences_rejected",
            "one_batched_call_per_search_state",
        },
        f"{goal.name} decoder",
    )
    decoder_calls = _counter(
        decoder,
        "model_generate_calls",
        f"{goal.name} decoder",
        maximum=limits["max_model_calls"],
    )
    requested = _counter(
        decoder,
        "candidate_sequences_requested",
        f"{goal.name} decoder",
        maximum=limits["max_model_calls"] * limits["candidates_per_state"],
    )
    returned = _counter(
        decoder,
        "candidate_sequences_returned",
        f"{goal.name} decoder",
        maximum=requested,
    )
    lines = _counter(
        decoder,
        "candidate_lines_returned",
        f"{goal.name} decoder",
        maximum=returned,
    )
    malformed = _counter(
        decoder,
        "malformed_sequences_rejected",
        f"{goal.name} decoder",
        maximum=returned,
    )
    if (
        decoder.get("one_batched_call_per_search_state") is not True
        or decoder_calls != model_calls
        or requested != model_calls * limits["candidates_per_state"]
        or lines + malformed != returned
        or candidates_executed > lines
    ):
        raise EvaluationReplayError(f"{goal.name}: inconsistent decoder counters")
    if status == "proof":
        depth = len(commands)
        if (
            min(
                model_calls,
                states_discovered,
                candidates_executed,
                requested,
                returned,
                lines,
            )
            < depth
        ):
            raise EvaluationReplayError(f"{goal.name}: counters cannot account for proof path")
    return {
        "model_generate_calls": model_calls,
        "states_expanded": states_expanded,
        "states_discovered": states_discovered,
        "candidates_executed": candidates_executed,
        "candidate_sequences_requested": requested,
        "candidate_sequences_returned": returned,
        "candidate_lines_returned": lines,
        "malformed_sequences_rejected": malformed,
        "frontier_peak_per_goal": frontier_peak,
    }


def _status_counts(value: object, expected: Mapping[str, int], label: str) -> None:
    record = _mapping(value, label)
    _exact_fields(record, set(ATTEMPT_STATUSES), label)
    for status in ATTEMPT_STATUSES:
        _integer(record.get(status), f"{label}.{status}")
    if record != expected:
        raise EvaluationReplayError(f"{label}: counts disagree with attempts")


def _validate_search_envelope(
    value: object,
    *,
    goals: Sequence[tuple[FrozenGoal, Mapping[str, object], tuple[str, ...]]],
    environment_sha256: str,
    max_new_tokens: int,
) -> None:
    search = _mapping(value, "search")
    _exact_fields(
        search,
        {"engine", "budget_scope", "limits", "aggregate_upper_bound", "actual", "goals"},
        "search",
    )
    if (
        search.get("engine") != "training.peano_policy.search.search-v1"
        or search.get("budget_scope") != "per-goal"
        or search.get("limits") != EXPECTED_SEARCH_LIMITS
    ):
        raise EvaluationReplayError("search engine or resource limits differ from frozen run")
    count = len(goals)
    upper = _mapping(search.get("aggregate_upper_bound"), "search aggregate upper bound")
    expected_upper = {
        "model_generate_calls": count * EXPECTED_SEARCH_LIMITS["max_model_calls"],
        "candidate_sequences": count
        * EXPECTED_SEARCH_LIMITS["max_model_calls"]
        * EXPECTED_SEARCH_LIMITS["candidates_per_state"],
        "generated_sequence_tokens": count
        * EXPECTED_SEARCH_LIMITS["max_model_calls"]
        * EXPECTED_SEARCH_LIMITS["candidates_per_state"]
        * max_new_tokens,
    }
    if upper != expected_upper or any(type(value) is not int for value in upper.values()):
        raise EvaluationReplayError("search aggregate upper bound is forged")

    search_goals = _array(search.get("goals"), "search goals", maximum=len(goals))
    if len(search_goals) != len(goals):
        raise EvaluationReplayError("search goal count differs from benchmark")
    totals = {
        "model_generate_calls": 0,
        "states_expanded": 0,
        "states_discovered": 0,
        "candidates_executed": 0,
        "candidate_sequences_requested": 0,
        "candidate_sequences_returned": 0,
        "candidate_lines_returned": 0,
        "malformed_sequences_rejected": 0,
        "frontier_peak_per_goal": 0,
    }
    for search_goal, (goal, attempt, commands) in zip(search_goals, goals, strict=True):
        counters = _validate_search_goal(
            search_goal,
            goal=goal,
            attempt=attempt,
            commands=commands,
            environment_sha256=environment_sha256,
            limits=EXPECTED_SEARCH_LIMITS,
        )
        for key, value in counters.items():
            if key == "frontier_peak_per_goal":
                totals[key] = max(totals[key], value)
            else:
                totals[key] += value
    actual = _mapping(search.get("actual"), "search aggregate actual")
    if actual != totals or any(type(value) is not int for value in actual.values()):
        raise EvaluationReplayError("aggregate search counters differ from per-goal data")


def validate_evaluation_record(
    report: Mapping[str, object],
    *,
    expected_source_commit: str,
    expected_evaluation_job_id: str,
    context: ReplayContext,
) -> tuple[ProofClaim, ...]:
    """Validate all report redundancy and return only exact proof claims."""

    if _COMMIT_RE.fullmatch(expected_source_commit) is None:
        raise EvaluationReplayError("expected source commit must be lowercase 40-hex")
    if _JOB_ID_RE.fullmatch(expected_evaluation_job_id) is None:
        raise EvaluationReplayError("expected evaluation job id must be decimal text")
    _exact_fields(
        report,
        {
            "v",
            "policy",
            "policy_identity",
            "evaluator",
            "judge",
            "goal_set_sha256",
            "seed",
            "k",
            "max_steps",
            "goal_count",
            "attempt_count",
            "proved_goals",
            "pass@k",
            "status_counts",
            "goals",
            "mode",
            "search",
        },
        "evaluation report",
    )
    authority = context.authority
    if tuple(goal.name for goal in authority.goals) != EXPECTED_GOAL_NAMES:
        raise EvaluationReplayError("internal frozen goal order changed")
    if authority.environment.get("environment_sha256") != EXPECTED_ENVIRONMENT_SHA256:
        raise EvaluationReplayError("internal model-v3 capability authority changed")
    if (
        report.get("v") != EVALUATOR_VERSION
        or report.get("mode") != EXPECTED_MODE
        or report.get("judge") != EXPECTED_JUDGE
        or report.get("goal_set_sha256") != EXPECTED_GOAL_SET_SHA256
        or report.get("seed") != EXPECTED_SEED
        or report.get("k") != 1
        or report.get("max_steps") != EXPECTED_SEARCH_LIMITS["max_depth"]
        or report.get("goal_count") != len(authority.goals)
        or report.get("attempt_count") != len(authority.goals)
    ):
        raise EvaluationReplayError("evaluation envelope differs from frozen model-v3 run")
    _validate_evaluator(report.get("evaluator"), authority)
    _, max_new_tokens = _validate_policy_identity(
        report,
        authority,
        expected_job_id=expected_evaluation_job_id,
        expected_source_commit=expected_source_commit,
        context=context,
    )

    goal_records = _array(report.get("goals"), "goals", maximum=len(authority.goals))
    if len(goal_records) != len(authority.goals):
        raise EvaluationReplayError("evaluation goal count differs from frozen benchmark")
    proof_claims: list[ProofClaim] = []
    search_inputs: list[tuple[FrozenGoal, Mapping[str, object], tuple[str, ...]]] = []
    top_counts = {status: 0 for status in ATTEMPT_STATUSES}
    proved_goals = 0
    for index, (raw_goal, goal) in enumerate(zip(goal_records, authority.goals, strict=True)):
        record = _mapping(raw_goal, f"goal {goal.name}")
        _exact_fields(
            record,
            {
                "name",
                "statement",
                "classical",
                "surface_profile",
                "environment_sha256",
                "allowed_theorems",
                "passed",
                "status_counts",
                "attempts",
            },
            f"goal {goal.name}",
        )
        if (
            record.get("name") != goal.name
            or record.get("statement") != goal.theorem
            or record.get("classical") is not False
            or record.get("surface_profile") != "model-v3"
            or record.get("environment_sha256") != EXPECTED_ENVIRONMENT_SHA256
            or record.get("allowed_theorems") != list(authority.allowed_theorems)
        ):
            raise EvaluationReplayError(f"{goal.name}: theorem or capability authority differs")
        attempts = _array(record.get("attempts"), f"{goal.name} attempts", maximum=1)
        if len(attempts) != 1:
            raise EvaluationReplayError(f"{goal.name}: search must contain exactly one attempt")
        attempt, commands, claim = _validate_attempt(
            attempts[0], goal=goal, goal_index=index, seed=EXPECTED_SEED
        )
        status = str(attempt["status"])
        expected_counts = {name: int(name == status) for name in ATTEMPT_STATUSES}
        _status_counts(record.get("status_counts"), expected_counts, f"{goal.name} status counts")
        passed = status == "proof"
        if record.get("passed") is not passed:
            raise EvaluationReplayError(f"{goal.name}: passed flag differs from proof status")
        top_counts[status] += 1
        proved_goals += int(passed)
        if claim is not None:
            proof_claims.append(claim)
        search_inputs.append((goal, attempt, commands))

    _status_counts(report.get("status_counts"), top_counts, "evaluation status counts")
    pass_at_k = report.get("pass@k")
    expected_pass = proved_goals / len(authority.goals)
    if (
        type(report.get("proved_goals")) is not int
        or report.get("proved_goals") != proved_goals
        or type(pass_at_k) is not float
        or pass_at_k != expected_pass
    ):
        raise EvaluationReplayError("evaluation summary differs from recomputed results")
    _validate_search_envelope(
        report.get("search"),
        goals=search_inputs,
        environment_sha256=EXPECTED_ENVIRONMENT_SHA256,
        max_new_tokens=max_new_tokens,
    )
    return tuple(proof_claims)


def _replay_claim(claim: ProofClaim, context: ReplayContext) -> dict[str, object]:
    try:
        result = context.verify_proof(
            claim.goal.source,
            claim.commands,
            request_id=f"v3-eval-replay-{claim.goal_index}-{claim.sample}",
            classical=False,
            capabilities=context.authority.capabilities,
        )
    except Exception as exc:
        raise EvaluationReplayError(
            f"{claim.goal.name}: independent verifier raised {type(exc).__name__}: {exc}"
        ) from exc
    checks = {
        "status": "proved",
        "kernel_checked": True,
        "theorem": claim.goal.theorem,
        "tactics_requested": len(claim.commands),
        "tactics_applied": len(claim.commands),
        "failed_tactics": 0,
        "proof_nodes": claim.proof_nodes,
        "mode": "verify",
        "surface": "model-v3",
        "environment_sha256": EXPECTED_ENVIRONMENT_SHA256,
        "classical": False,
        "on_error": "stop",
        "goals": (),
    }
    for field, expected in checks.items():
        if getattr(result, field, object()) != expected:
            raise EvaluationReplayError(
                f"{claim.goal.name}: independent replay {field} differs from {expected!r}"
            )
    commands_record = list(claim.commands)
    return {
        "goal_index": claim.goal_index,
        "name": claim.goal.name,
        "sample": claim.sample,
        "theorem": claim.goal.theorem,
        "commands": commands_record,
        "commands_sha256": _sha256_json(commands_record),
        "steps": len(claim.commands),
        "proof_nodes": claim.proof_nodes,
        "replay": {
            "status": "proved",
            "kernel_checked": True,
            "theorem": claim.goal.theorem,
            "tactics_requested": len(claim.commands),
            "tactics_applied": len(claim.commands),
            "failed_tactics": 0,
            "proof_nodes": claim.proof_nodes,
            "mode": "verify",
            "surface": "model-v3",
            "environment_sha256": EXPECTED_ENVIRONMENT_SHA256,
            "classical": False,
        },
    }


def _replay_evaluation_report(
    report_path: Path,
    *,
    expected_source_commit: str,
    expected_evaluation_job_id: str,
    context: ReplayContext,
    recheck_context: bool,
) -> dict[str, object]:
    """Internal dependency-injected implementation used by focused tests."""

    trusted = context
    report, raw = load_evaluation_report(report_path)
    claims = validate_evaluation_record(
        report,
        expected_source_commit=expected_source_commit,
        expected_evaluation_job_id=expected_evaluation_job_id,
        context=trusted,
    )
    replayed = [_replay_claim(claim, trusted) for claim in claims]
    if recheck_context:
        after = current_replay_context()
        if (
            after.authority != trusted.authority
            or after.verify_proof is not trusted.verify_proof
            or after.evaluation_script_sha256 != trusted.evaluation_script_sha256
            or after.support_script_sha256 != trusted.support_script_sha256
            or after.replay_sources != trusted.replay_sources
            or after.replay_runtime != trusted.replay_runtime
            or after.replay_job != trusted.replay_job
        ):
            raise EvaluationReplayError(
                "kernel, evaluator source, runtime, or deployment changed during replay"
            )
    core: dict[str, object] = {
        "format": REPORT_FORMAT,
        "v": REPORT_VERSION,
        "status": "passed",
        "input": {
            "path": str(report_path.resolve()),
            "bytes": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
            "canonical_record_sha256": _sha256_json(report),
        },
        "evaluation": {
            "source_commit": expected_source_commit,
            "job_id": expected_evaluation_job_id,
            "evaluator_v": EVALUATOR_VERSION,
            "mode": EXPECTED_MODE,
            "goal_set_sha256": EXPECTED_GOAL_SET_SHA256,
            "environment_sha256": EXPECTED_ENVIRONMENT_SHA256,
            "sources": trusted.authority.evaluation_sources,
        },
        "benchmark": {
            "goal_count": len(trusted.authority.goals),
            "goals": [
                {"name": goal.name, "statement": goal.theorem}
                for goal in trusted.authority.goals
            ],
            "search_limits": EXPECTED_SEARCH_LIMITS,
        },
        "summary": {
            "attempts": len(trusted.authority.goals),
            "claimed_proofs": len(claims),
            "kernel_replayed_proofs": len(replayed),
            "proved_goals": report["proved_goals"],
            "pass@k": report["pass@k"],
            "status_counts": report["status_counts"],
        },
        "proofs": replayed,
        "replay_authority": {
            "source_commit": expected_source_commit,
            "sources": trusted.replay_sources,
            "runtime": trusted.replay_runtime,
            "job": trusted.replay_job,
        },
    }
    return {**core, "attestation_sha256": _sha256_json(core)}


def replay_evaluation_report(
    report_path: Path,
    *,
    expected_source_commit: str,
    expected_evaluation_job_id: str,
) -> dict[str, object]:
    """Validate and independently kernel-replay one frozen evaluation file.

    The trusted context is always captured from the current repository and
    Peano installation.  It is captured again after all claimed proofs have
    run, preventing a source or deployment change during replay from being
    published under the earlier identity.
    """

    return _replay_evaluation_report(
        report_path,
        expected_source_commit=expected_source_commit,
        expected_evaluation_job_id=expected_evaluation_job_id,
        context=current_replay_context(),
        recheck_context=True,
    )


def _current_evaluation_sources() -> Mapping[str, object]:
    from .runtime import source_files_identity

    return source_files_identity(
        (
            REPOSITORY_ROOT / "scripts" / "eval_trained_peano_policy.py",
            REPOSITORY_ROOT / "scripts" / "eval_peano_policy.py",
            REPOSITORY_ROOT / "scripts" / "peano_policy_proof_request.py",
            *sorted((REPOSITORY_ROOT / "training" / "peano_policy").glob("*.py")),
            *sorted((PEANO_PYTHON / "peano_lab").rglob("*.py")),
        )
    )


def _current_replay_sources() -> Mapping[str, object]:
    from .runtime import source_files_identity

    return source_files_identity(
        (
            Path(__file__),
            REPOSITORY_ROOT / REPLAY_SCRIPT,
            REPOSITORY_ROOT / "scripts" / "eval_trained_peano_policy.py",
            REPOSITORY_ROOT / "scripts" / "eval_peano_policy.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "contract.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "manifest.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "prompt.py",
            REPOSITORY_ROOT / "training" / "peano_policy" / "runtime.py",
            *sorted((PEANO_PYTHON / "peano_lab").rglob("*.py")),
        )
    )


def _load_frozen_authority() -> FrozenAuthority:
    # These imports intentionally occur only when production replay begins.
    # They load Peano Lab's checked theorem catalog but no model runtime.
    from scripts import eval_peano_policy as evaluator
    from peano_lab.batch import capability_sha256
    from training.peano_policy.contract import (
        MODEL_V3_HELD_OUT_POLICY_GOALS,
        environment_record,
        held_out_contract_sha256,
        model_v3_environment,
    )
    from training.peano_policy.prompt import prompt_contract_sha256

    environment = model_v3_environment()
    goals = tuple(
        evaluator.EvalGoal(
            name,
            source,
            classical=False,
            surface_profile=environment.capabilities.label,
            allowed_theorems=environment.capabilities.allowed_theorems,
        )
        for name, source in MODEL_V3_HELD_OUT_POLICY_GOALS
    )
    if evaluator._goal_set_sha256(goals) != EXPECTED_GOAL_SET_SHA256:
        raise EvaluationReplayError("repository v3 goal-set fingerprint changed")
    if environment.sha256 != EXPECTED_ENVIRONMENT_SHA256:
        raise EvaluationReplayError("repository v3 capability fingerprint changed")
    if capability_sha256(goals[0].capabilities) != EXPECTED_ENVIRONMENT_SHA256:
        raise EvaluationReplayError("kernel surface v3 capability fingerprint changed")
    frozen = tuple(
        FrozenGoal(goal.name, goal.statement, evaluator._parse_closed_goal(goal)[2])
        for goal in goals
    )
    return FrozenAuthority(
        goals=frozen,
        capabilities=goals[0].capabilities,
        environment=environment_record(environment),
        allowed_theorems=environment.capabilities.allowed_theorems or (),
        evaluator_source_sha256=evaluator.EVALUATOR_SOURCE_SHA256,
        evaluator_semantic_sources=evaluator.EVALUATOR_SEMANTIC_SOURCES,
        evaluation_sources=_current_evaluation_sources(),
        prompt_contract_sha256=prompt_contract_sha256(3),
        held_out_contract_sha256=held_out_contract_sha256(3),
        library_snapshot_sha256=environment.library_sha256 or "",
    )


def current_replay_context() -> ReplayContext:
    """Capture the current kernel, evaluator, source, and replay deployment."""

    from peano_lab.batch import verify_proof
    from .runtime import runtime_identity, slurm_job_identity

    evaluation_script = REPOSITORY_ROOT / EXPECTED_EVALUATION_SCRIPT
    support_script = REPOSITORY_ROOT / EXPECTED_SUPPORT_SCRIPT
    for path, label in (
        (evaluation_script, "evaluation Slurm script"),
        (support_script, "WMI support script"),
        (REPOSITORY_ROOT / REPLAY_SCRIPT, "replay CLI"),
    ):
        if not path.is_file() or path.is_symlink():
            raise EvaluationReplayError(f"{label} is not one repository regular file")
    return ReplayContext(
        authority=_load_frozen_authority(),
        verify_proof=verify_proof,
        evaluation_script_sha256=_sha256_file(evaluation_script),
        support_script_sha256=_sha256_file(support_script),
        replay_sources=_current_replay_sources(),
        replay_runtime=runtime_identity(),
        replay_job=slurm_job_identity(),
    )


def write_replay_attestation(path: Path, record: Mapping[str, object]) -> None:
    """Atomically create, never replace, one canonical replay attestation."""

    payload = (
        json.dumps(
            record,
            ensure_ascii=False,
            sort_keys=True,
            indent=2,
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        raise FileExistsError(f"refusing to replace replay attestation: {path}")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, path)
        except FileExistsError:
            raise FileExistsError(f"refusing to replace replay attestation: {path}") from None
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    finally:
        if temporary.exists():
            temporary.unlink()


__all__ = [
    "EXPECTED_ENVIRONMENT_SHA256",
    "EXPECTED_GOAL_NAMES",
    "EXPECTED_GOAL_SET_SHA256",
    "EXPECTED_SEARCH_LIMITS",
    "EvaluationReplayError",
    "FrozenAuthority",
    "FrozenGoal",
    "ReplayContext",
    "current_replay_context",
    "load_evaluation_report",
    "replay_evaluation_report",
    "validate_evaluation_record",
    "write_replay_attestation",
]
