"""Paired symbolic/control pilot for Peano Hydra's teacher-oracle plumbing.

This is deliberately an interface test, not a model evaluation.  The checked
``triangular-even-readable.pa`` script supplies structural actions only at the
exact canonical states where they occurred.  A genuine state-independent
``compact_arith`` head is present in both lanes.  The paired control replaces
the macro teacher with an identified null head under the same quota and gate.

Every source and discovered route is independently replayed with a retained
batch trace and Peano Lab's kernel.  The report says
``teacher_oracle_plumbing`` prominently because a positive result demonstrates
interface headroom only; it is not evidence that Qwen learned the proof.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

from peano_lab.batch import BatchResult, capability_sha256, run_proof
from peano_lab.ui.prove import SurfaceCapabilities
from training.peano_hydra.policy import (
    MACRO_ACTION_HEADS,
    FixedCandidatePolicy,
    HeadGate,
    HydraCandidatePolicy,
    NullCandidatePolicy,
    PolicyHead,
    ScriptCandidatePolicy,
)
from training.peano_hydra.runner import (
    HydraRunResult,
    policy_environment,
    run_hydra,
)
from training.peano_hydra.profile import (
    canonical_profile_theorem,
    semantic_profile_identity,
    semantic_profile_sha256 as registered_semantic_profile_sha256,
)
from training.peano_policy.search import SearchLimits


PILOT_VERSION = 2
TEACHER_ORACLE_LABEL = "teacher_oracle_plumbing"
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ARTIFACT = REPOSITORY_ROOT / "artifacts" / "triangular-even-readable.pa"
DEFAULT_ARTIFACT_SHA256 = (
    "d324c0bdcc850a6e214b0c5adc108664750e6ba9148417dd31bfa60e6842d17f"
)
DEFAULT_ARTIFACT_COMMANDS = 13
DEFAULT_ARTIFACT_PROOF_NODES = 180
MAX_ARTIFACT_BYTES = 1_000_000

# Both lanes receive exactly three slots at every expanded state: two fixed
# symbolic candidates and one macro/control candidate.  The contextual form is
# enumerated everywhere (and normally rejected); it is not selected from the
# teacher trace.  The reviewed route has
# 13 commands and 12 open successors, so these bounds admit it exactly without
# providing a hidden exploratory tail.
PILOT_LIMITS = SearchLimits(
    max_depth=13,
    beam_width=1,
    candidates_per_state=3,
    max_model_calls=13,
    max_states=14,
)

PILOT_COMMANDS = frozenset(
    {
        "cases",
        "compact_arith",
        "exact",
        "exists",
        "have",
        "induction",
        "intro",
        "rewrite",
        "specialize",
        "suffices",
    }
)
PILOT_CAPABILITIES = SurfaceCapabilities(
    label="peano-hydra-teacher-pilot-v2",
    allowed_commands=PILOT_COMMANDS,
    allowed_theorems=frozenset(),
)
SYMBOLIC_HEADS = frozenset({"compact_arith"})
MUTATED_THEOREM = "forall n. exists x. n * (n + 1) = 2 * x + 1"


class TeacherOraclePilotError(RuntimeError):
    """The paired pilot lost an evidence or comparison invariant."""


@dataclass(frozen=True, slots=True)
class CheckedScriptArtifact:
    """The exact readable source route and its checked traced execution."""

    path: str
    sha256: str
    theorem_source: str
    canonical_theorem: str
    commands: tuple[str, ...]
    replay: BatchResult
    semantic_profile_sha256: str

    def __post_init__(self) -> None:
        if self.semantic_profile_sha256 != registered_semantic_profile_sha256():
            raise ValueError("teacher artifact has a different semantic profile")
        if canonical_profile_theorem(self.theorem_source) != self.canonical_theorem:
            raise ValueError("teacher artifact theorem is not canonical")
        _validate_source_replay(
            artifact_sha256=self.sha256,
            theorem=self.canonical_theorem,
            commands=self.commands,
            profile_digest=self.semantic_profile_sha256,
            replay=self.replay,
        )

    def to_dict(self, *, include_trace: bool = False) -> dict[str, object]:
        self.__post_init__()
        request_id, session_id = _source_replay_ids(
            self.semantic_profile_sha256,
            self.sha256,
        )
        fresh = run_proof(
            self.canonical_theorem,
            self.commands,
            request_id=request_id,
            classical=False,
            on_error="stop",
            capabilities=PILOT_CAPABILITIES,
            session_id=session_id,
        )
        _validate_source_replay(
            artifact_sha256=self.sha256,
            theorem=self.canonical_theorem,
            commands=self.commands,
            profile_digest=self.semantic_profile_sha256,
            replay=fresh,
        )
        if fresh.to_dict(include_trace=True) != self.replay.to_dict(
            include_trace=True
        ):
            raise TeacherOraclePilotError(
                "teacher artifact publication replay differs from its retained replay"
            )
        payload = {
            "path": self.path,
            "sha256": self.sha256,
            "theorem_source": self.theorem_source,
            "canonical_theorem": self.canonical_theorem,
            "semantic_profile_sha256": self.semantic_profile_sha256,
            "commands": list(self.commands),
            "command_count": len(self.commands),
            "proof_nodes": self.replay.proof_nodes,
            "replay": self.replay.to_dict(include_trace=include_trace),
        }
        return json.loads(
            json.dumps(
                payload,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )


@dataclass(frozen=True, slots=True)
class TeacherOraclePilotReport:
    """One exact paired control/hybrid teacher-oracle plumbing report."""

    artifact: CheckedScriptArtifact
    macro_heads: tuple[str, ...]
    macro_state_sha256s: tuple[str, ...]
    control: HydraRunResult
    hybrid: HydraRunResult
    mutation: HydraRunResult
    semantic_profile_sha256: str

    def __post_init__(self) -> None:
        if self.semantic_profile_sha256 != registered_semantic_profile_sha256():
            raise ValueError("pilot report has a different semantic profile")
        self.artifact.__post_init__()
        if self.artifact.semantic_profile_sha256 != self.semantic_profile_sha256:
            raise ValueError("pilot artifact has a different semantic profile")
        if any(
            lane.semantic_profile_sha256 != self.semantic_profile_sha256
            for lane in (self.control, self.hybrid, self.mutation)
        ):
            raise ValueError("pilot lane has a different semantic profile")
        if self.control.environment != self.hybrid.environment:
            raise ValueError("paired lanes must have the exact same environment")
        if self.control.limits != self.hybrid.limits:
            raise ValueError("paired lanes must have the exact same search limits")
        if self.mutation.environment != self.hybrid.environment:
            raise ValueError("mutation lane must have the exact same environment")
        if self.mutation.limits != self.hybrid.limits:
            raise ValueError("mutation lane must have the exact same search limits")
        if self.control.degraded or self.hybrid.degraded or self.mutation.degraded:
            raise ValueError("the teacher pilot cannot publish a degraded lane")
        if any(
            lane.eligible_for_comparison
            for lane in (self.control, self.hybrid, self.mutation)
        ):
            raise ValueError(
                "surface-macro-v0 teacher-oracle lanes must remain comparison "
                "ineligible"
            )
        if not all(
            lane.comparison_ineligibility_reasons
            for lane in (self.control, self.hybrid, self.mutation)
        ):
            raise ValueError("pilot lanes must explain comparison ineligibility")
        if self.control.proved:
            raise ValueError("the symbolic-only control unexpectedly used a proof route")
        if not self.hybrid.proved:
            raise ValueError("the teacher-oracle plumbing did not reproduce its route")
        if self.hybrid.commands != self.artifact.commands:
            raise ValueError("the hybrid command route differs from the checked artifact")
        if self.hybrid.search.certificate_nodes != self.artifact.replay.proof_nodes:
            raise ValueError("the hybrid certificate size differs from the artifact")
        if self.mutation.proved:
            raise ValueError("teacher transcript was reused for a mutated theorem")

    def to_dict(self, *, include_trace: bool = False) -> dict[str, object]:
        self.__post_init__()
        return {
            "v": PILOT_VERSION,
            "experiment": TEACHER_ORACLE_LABEL,
            "semantic_profile": semantic_profile_identity(),
            "claim_boundary": (
                "checked interface/oracle headroom only; not Qwen capability, "
                "not an LLM advantage result, and not sealed evaluation"
            ),
            "teacher_oracle_plumbing": {
                "enabled": True,
                "source": "exact states and structural actions from a checked script",
                "macro_heads": list(self.macro_heads),
                "macro_state_sha256s": list(self.macro_state_sha256s),
                "macro_state_count": len(self.macro_state_sha256s),
                "symbolic_head": {
                    "candidates": [
                        "compact_arith",
                        "compact_arith [IH_witness]",
                    ],
                    "availability": "every expanded state in both lanes",
                    "context_hint_policy": (
                        "fixed enumeration, independent of the teacher state map"
                    ),
                    "provenance": (
                        "human-selected visible-context IH_witness enumeration for "
                        "this plumbing pilot; not evidence of generic symbolic or "
                        "model capability"
                    ),
                },
                "paired_control": (
                    "identified null macro head with the same quota and state gate"
                ),
            },
            "paired_budget": self.control.limits,
            "artifact": self.artifact.to_dict(include_trace=include_trace),
            "control": self.control.to_dict(include_trace=include_trace),
            "hybrid": self.hybrid.to_dict(include_trace=include_trace),
            "mutation_integrity_check": {
                "claim_boundary": (
                    "transcript non-reuse check only; an unsolved search is unknown, "
                    "not negative-decision evidence"
                ),
                "result": self.mutation.to_dict(include_trace=include_trace),
                "passed": not self.mutation.proved,
            },
            "outcome": {
                "semantic_profile_sha256": self.semantic_profile_sha256,
                "control_status": self.control.status,
                "hybrid_status": self.hybrid.status,
                "hybrid_kernel_checked": (
                    self.hybrid.replay is not None
                    and self.hybrid.replay.kernel_checked is True
                ),
                "hybrid_commands_match_teacher": (
                    self.hybrid.commands == self.artifact.commands
                ),
                "hybrid_proof_nodes": self.hybrid.search.certificate_nodes,
                "mutated_theorem_status": self.mutation.status,
                "mutated_transcript_rejected": not self.mutation.proved,
            },
        }

    def json(
        self,
        *,
        indent: int | None = 2,
        include_trace: bool = False,
    ) -> str:
        return json.dumps(
            self.to_dict(include_trace=include_trace),
            ensure_ascii=False,
            allow_nan=False,
            indent=indent,
            sort_keys=True,
            separators=(",", ":") if indent is None else None,
        )


def _read_script(path: Path) -> tuple[bytes, str, tuple[str, ...]]:
    if not isinstance(path, Path):
        raise TypeError("artifact_path must be a pathlib.Path")
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise TeacherOraclePilotError(f"cannot read teacher artifact: {exc}") from None
    if not raw:
        raise TeacherOraclePilotError("teacher artifact is empty")
    if len(raw) > MAX_ARTIFACT_BYTES:
        raise TeacherOraclePilotError(
            f"teacher artifact exceeds {MAX_ARTIFACT_BYTES} bytes"
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise TeacherOraclePilotError(
            f"teacher artifact is not UTF-8: {exc}"
        ) from None
    lines = text.splitlines()
    if len(lines) < 3 or any(not line for line in lines):
        raise TeacherOraclePilotError(
            "teacher artifact needs a theorem, non-empty commands, and qed"
        )
    prefix = "pa prove "
    if not lines[0].startswith(prefix) or lines[0] == prefix:
        raise TeacherOraclePilotError("teacher artifact must start with `pa prove ...`")
    if lines[-1] != "qed":
        raise TeacherOraclePilotError("teacher artifact must end with exact `qed`")
    theorem = lines[0][len(prefix) :]
    commands = tuple(lines[1:-1])
    if any(line != line.strip() or line.splitlines() != [line] for line in commands):
        raise TeacherOraclePilotError(
            "teacher commands must be complete lines with no outer whitespace"
        )
    return raw, theorem, commands


def _source_replay_ids(profile_digest: str, artifact_sha256: str) -> tuple[str, str]:
    return (
        f"hydra-teacher-source-{profile_digest[:12]}-{artifact_sha256[:12]}",
        (
            f"peano-hydra-teacher-source-{profile_digest[:12]}-"
            f"{artifact_sha256[:12]}"
        ),
    )


def _validate_source_replay(
    *,
    artifact_sha256: str,
    theorem: str,
    commands: tuple[str, ...],
    profile_digest: str,
    replay: BatchResult,
) -> None:
    request_id, session_id = _source_replay_ids(profile_digest, artifact_sha256)
    if (
        type(replay) is not BatchResult
        or replay.status != "proved"
        or replay.request_id != request_id
        or replay.session_id != session_id
        or replay.kernel_checked is not True
        or replay.theorem != theorem
        or replay.mode != "trace"
        or replay.trace is None
        or replay.classical is not False
        or replay.surface != PILOT_CAPABILITIES.label
        or replay.environment_sha256 != capability_sha256(PILOT_CAPABILITIES)
        or replay.on_error != "stop"
        or replay.goals
        or replay.tactics_requested != len(commands)
        or replay.tactics_applied != len(commands)
        or replay.failed_tactics != 0
        or replay.proof_nodes is None
    ):
        raise TeacherOraclePilotError(
            "teacher artifact failed its fresh traced original-goal kernel replay"
        )
    traced_commands = tuple(
        row.get("tactic") if type(row) is dict else None
        for row in replay.trace[:-1]
    )
    if traced_commands != commands:
        raise TeacherOraclePilotError(
            "teacher artifact trace differs from its physical command lines"
        )


def _checked_artifact(path: Path) -> CheckedScriptArtifact:
    raw, theorem, commands = _read_script(path)
    digest = hashlib.sha256(raw).hexdigest()
    profile_digest = registered_semantic_profile_sha256()
    canonical_theorem = canonical_profile_theorem(theorem)
    request_id, session_id = _source_replay_ids(profile_digest, digest)
    replay = run_proof(
        theorem,
        commands,
        request_id=request_id,
        classical=False,
        on_error="stop",
        capabilities=PILOT_CAPABILITIES,
        session_id=session_id,
    )
    _validate_source_replay(
        artifact_sha256=digest,
        theorem=canonical_theorem,
        commands=commands,
        profile_digest=profile_digest,
        replay=replay,
    )

    try:
        is_default = path.resolve() == DEFAULT_ARTIFACT.resolve()
    except OSError:
        is_default = path.absolute() == DEFAULT_ARTIFACT.absolute()
    if is_default and (
        digest != DEFAULT_ARTIFACT_SHA256
        or len(commands) != DEFAULT_ARTIFACT_COMMANDS
        or replay.proof_nodes != DEFAULT_ARTIFACT_PROOF_NODES
    ):
        raise TeacherOraclePilotError(
            "the default teacher artifact changed from its reviewed 13-line, "
            "180-node identity"
        )
    try:
        portable_path = path.resolve().relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except (OSError, ValueError):
        portable_path = str(path)
    return CheckedScriptArtifact(
        path=portable_path,
        sha256=digest,
        theorem_source=theorem,
        canonical_theorem=canonical_theorem,
        commands=commands,
        replay=replay,
        semantic_profile_sha256=profile_digest,
    )


def _command_head(command: str) -> str:
    return command.split(" ", 1)[0]


def _policies(
    artifact: CheckedScriptArtifact,
) -> tuple[HydraCandidatePolicy, HydraCandidatePolicy, tuple[str, ...], tuple[str, ...]]:
    profile_digest = registered_semantic_profile_sha256()
    environment = policy_environment(
        PILOT_CAPABILITIES,
        semantic_profile_sha256=profile_digest,
        classical=False,
    )
    artifact_heads = frozenset(_command_head(line) for line in artifact.commands)
    macro_heads = artifact_heads - SYMBOLIC_HEADS
    if not macro_heads or not macro_heads.issubset(MACRO_ACTION_HEADS):
        raise TeacherOraclePilotError(
            "teacher artifact contains an unsupported structural action head"
        )

    macro_teacher = ScriptCandidatePolicy.from_batch_result(
        artifact.replay,
        name="triangular-even-structural-teacher-v2",
        policy_environment=environment,
        include_heads=frozenset(macro_heads),
    )
    macro_states = tuple(sorted(macro_teacher.state_sha256s))
    macro_gate = HeadGate(frozenset(macro_states))
    symbolic_identity = {
        "kind": "fixed-untrusted-symbolic-closure-v2",
        "semantic_profile_sha256": profile_digest,
        "candidates": ["compact_arith", "compact_arith [IH_witness]"],
        "teacher_conditioned": False,
        "context_hint_enumeration": "fixed-at-every-state",
    }

    def symbolic(name: str) -> FixedCandidatePolicy:
        return FixedCandidatePolicy(
            ("compact_arith", "compact_arith [IH_witness]"),
            name=name,
            policy_environment=environment,
            provider_identity=symbolic_identity,
        )

    control_null = NullCandidatePolicy(
        name="paired-null-macro-control-v2",
        policy_environment=environment,
        provider_identity={
            "kind": "paired-null-control-v2",
            "semantic_profile_sha256": profile_digest,
            "replaces": TEACHER_ORACLE_LABEL,
            "quota": 1,
            "gate_sha256s": list(macro_states),
        },
    )
    control = HydraCandidatePolicy(
        (
            PolicyHead(
                "symbolic-compact-arith",
                "symbolic",
                2,
                symbolic("symbolic-compact-arith-control-v2"),
            ),
            PolicyHead(
                "paired-null-macro-control",
                "control",
                1,
                control_null,
                gating=macro_gate,
            ),
        ),
        name="peano-hydra-symbolic-only-control-v2",
    )
    hybrid = HydraCandidatePolicy(
        (
            PolicyHead(
                "symbolic-compact-arith",
                "symbolic",
                2,
                symbolic("symbolic-compact-arith-hybrid-v2"),
            ),
            PolicyHead(
                "teacher-oracle-structural-macros",
                "macro",
                1,
                macro_teacher,
                gating=macro_gate,
            ),
        ),
        name="peano-hydra-teacher-oracle-plumbing-v2",
    )
    if not (
        control.total_quota
        == hybrid.total_quota
        == PILOT_LIMITS.candidates_per_state
    ):
        raise TeacherOraclePilotError("paired policy quotas disagree")
    return control, hybrid, tuple(sorted(macro_heads)), macro_states


def run_teacher_oracle_pilot(
    artifact_path: Path = DEFAULT_ARTIFACT,
) -> TeacherOraclePilotReport:
    """Run the exact symbolic-only and teacher-macro paired pilot."""

    profile_digest = registered_semantic_profile_sha256()
    artifact = _checked_artifact(artifact_path)
    control_policy, hybrid_policy, macro_heads, macro_states = _policies(artifact)
    control = run_hydra(
        artifact.theorem_source,
        control_policy,
        capabilities=PILOT_CAPABILITIES,
        semantic_profile_sha256=profile_digest,
        classical=False,
        limits=PILOT_LIMITS,
        label="symbolic-only-control",
    )
    hybrid = run_hydra(
        artifact.theorem_source,
        hybrid_policy,
        capabilities=PILOT_CAPABILITIES,
        semantic_profile_sha256=profile_digest,
        classical=False,
        limits=PILOT_LIMITS,
        label=TEACHER_ORACLE_LABEL,
    )
    # Rebuild the hybrid policy so its proposal ledger and provider state are
    # fresh.  Exact full-state gates from the checked source must not activate
    # on even a closely related theorem.
    _, mutation_policy, _, _ = _policies(artifact)
    mutation = run_hydra(
        MUTATED_THEOREM,
        mutation_policy,
        capabilities=PILOT_CAPABILITIES,
        semantic_profile_sha256=profile_digest,
        classical=False,
        limits=PILOT_LIMITS,
        label="teacher-transcript-mutation-integrity",
    )
    try:
        return TeacherOraclePilotReport(
            artifact=artifact,
            macro_heads=macro_heads,
            macro_state_sha256s=macro_states,
            control=control,
            hybrid=hybrid,
            mutation=mutation,
            semantic_profile_sha256=profile_digest,
        )
    except ValueError as exc:
        raise TeacherOraclePilotError(str(exc)) from None


__all__ = [
    "CheckedScriptArtifact",
    "DEFAULT_ARTIFACT",
    "DEFAULT_ARTIFACT_COMMANDS",
    "DEFAULT_ARTIFACT_PROOF_NODES",
    "DEFAULT_ARTIFACT_SHA256",
    "PILOT_CAPABILITIES",
    "PILOT_LIMITS",
    "PILOT_VERSION",
    "MUTATED_THEOREM",
    "TEACHER_ORACLE_LABEL",
    "TeacherOraclePilotError",
    "TeacherOraclePilotReport",
    "run_teacher_oracle_pilot",
]
