"""Provider-neutral candidate portfolios for Peano kernel-guided search.

This module is deliberately outside :mod:`peano_lab`.  Policies, language
models, recorded scripts, and external solvers remain untrusted: they return
ordinary public-surface tactic lines, and :mod:`training.peano_policy.search`
replays every returned line before the independent kernel judges QED.

The portfolio has two small but important contracts:

* a ``macro`` head may propose only proof-structuring actions such as
  ``induction`` or ``have``; it may not disguise a closing arithmetic tactic as
  a structural hint, and
* every head carries an immutable execution-environment identity.  Heads with
  different tactic/theorem authority cannot be silently combined.

Nothing here parses formulas, mutates proof states, constructs certificates,
or decides whether a tactic succeeds.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Literal, Protocol, runtime_checkable
import unicodedata

from peano_lab.batch import BATCH_VERSION, BatchResult, capability_sha256, run_proof
from peano_lab.ui.prove import MAX_INPUT, SurfaceCapabilities, oversized_numeral
from training.peano_hydra.profile import (
    canonical_profile_theorem,
    semantic_profile_sha256 as registered_semantic_profile_sha256,
)
from training.peano_policy.search import CandidatePolicy, state_sha256


HYDRA_POLICY_VERSION = 3
MAX_RECORDED_STATES = 4_096
MAX_RECORDED_CANDIDATES_PER_STATE = 1_024
MAX_POLICY_NAME_CHARS = 160
MAX_POLICY_ERROR_CHARS = 1_000
MAX_IDENTITY_JSON_CHARS = 1_000_000

HeadRole = Literal["macro", "symbolic", "control"]
ProposalOutcome = Literal["ok", "gated", "error", "contract-error"]

MACRO_ACTION_HEADS = frozenset(
    {
        "apply",
        "cases",
        "exact",
        "exists",
        "have",
        "induction",
        "intro",
        "left",
        "rewrite",
        "right",
        "specialize",
        "split",
        "suffices",
        "trans",
        "use",
    }
)

_POLICY_ENVIRONMENT_FIELDS = frozenset(
    {
        "classical",
        "surface",
        "environment_sha256",
        "semantic_profile_sha256",
        "capabilities",
    }
)
_CAPABILITY_FIELDS = frozenset(
    {"label", "allowed_commands", "allowed_theorems"}
)
_TRACE_STEP_FIELDS = frozenset(
    {
        "v",
        "session",
        "step",
        "goals_before",
        "focus",
        "tactic",
        "goals_after",
        "status",
        "error",
    }
)
_TRACE_FOOTER_FIELDS = frozenset(
    {"qed", "theorem", "proof_size", "tactic_count"}
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_HEAD_RE = re.compile(r"[a-z][a-z0-9_]*")


def _safe_one_line(label: str, value: object, *, limit: int) -> str:
    if type(value) is not str or not value:
        raise ValueError(f"{label} must be non-empty text")
    if len(value) > limit:
        raise ValueError(f"{label} exceeds {limit} characters")
    if value != value.strip() or value.splitlines() != [value]:
        raise ValueError(f"{label} must be exactly one line with no outer whitespace")
    if any(
        unicodedata.category(character) in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        for character in value
    ):
        raise ValueError(f"{label} contains an unsafe control or format character")
    return value


def _safe_policy_name(value: object) -> str:
    return _safe_one_line("policy name", value, limit=MAX_POLICY_NAME_CHARS)


def _validate_goals(goals: object) -> tuple[str, ...]:
    if type(goals) is not tuple or not goals:
        raise ValueError("goals_before must be one non-empty exact tuple")
    if not all(type(goal) is str and bool(goal) for goal in goals):
        raise ValueError("goals_before must contain only non-empty canonical text")
    return goals


def _validate_tactic_line(value: object) -> str:
    line = _safe_one_line("candidate", value, limit=MAX_INPUT)
    dangerous = oversized_numeral(line)
    if dangerous is not None:
        raise ValueError(f"candidate contains resource-dangerous numeral {dangerous}")
    return line


def _command_head(line: str) -> str:
    head = line.split(" ", 1)[0]
    if _HEAD_RE.fullmatch(head) is None:
        raise ValueError("candidate does not begin with one plain tactic head")
    return head


def _canonical_json_text(label: str, value: object) -> str:
    if isinstance(value, Mapping) and type(value) is not dict:
        value = dict(value)
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
        detached = json.loads(encoded)
    except (TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ValueError(f"{label} is not strict JSON: {exc}") from None
    if len(encoded) > MAX_IDENTITY_JSON_CHARS:
        raise ValueError(f"{label} exceeds {MAX_IDENTITY_JSON_CHARS} characters")
    if type(detached) is not dict:
        raise ValueError(f"{label} must be a JSON object")
    return encoded


def _provider_identity_json(value: object) -> str:
    """Require an explicit, minimally typed provenance object.

    This does not pretend to prove that a provider record is sufficient for a
    campaign claim.  It prevents the much simpler failure mode where a fixed
    or recorded head is accidentally admitted with an explicitly unbound
    placeholder.  The pre-H0 runner remains comparison-ineligible regardless;
    later campaign protocols must validate their richer evidence schema.
    """

    encoded = _canonical_json_text("provider_identity", value)
    identity = _detached_object(encoded)
    if not identity:
        raise ValueError("provider_identity must not be empty")
    _safe_one_line("provider_identity.kind", identity.get("kind"), limit=160)
    return encoded


def _detached_object(encoded: str) -> dict[str, object]:
    value = json.loads(encoded)
    if type(value) is not dict:  # pragma: no cover - guarded by construction
        raise RuntimeError("stored JSON object identity is malformed")
    return value


def _json_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _registered_profile_digest(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise ValueError(f"{label} must be one lowercase SHA-256 digest")
    registered = registered_semantic_profile_sha256()
    if value != registered:
        raise ValueError(f"{label} is not the registered semantic profile")
    return value


def _environment_profile_digest(encoded: str) -> str:
    environment = _detached_object(encoded)
    return _registered_profile_digest(
        "policy_environment.semantic_profile_sha256",
        environment.get("semantic_profile_sha256"),
    )


def _name_list(label: str, value: object) -> frozenset[str] | None:
    if value is None:
        return None
    if type(value) is not list or not all(
        type(item) is str and item for item in value
    ):
        raise ValueError(f"{label} must be null or an array of non-empty names")
    if value != sorted(value) or len(set(value)) != len(value):
        raise ValueError(f"{label} must be sorted and unique")
    return frozenset(value)


def _policy_environment_json(value: object) -> str:
    encoded = _canonical_json_text("policy_environment", value)
    environment = _detached_object(encoded)
    if set(environment) != _POLICY_ENVIRONMENT_FIELDS:
        raise ValueError(
            "policy_environment must contain classical, surface, "
            "environment_sha256, semantic_profile_sha256, and capabilities"
        )
    if type(environment["classical"]) is not bool:
        raise ValueError("policy_environment.classical must be a Boolean")
    if environment["classical"]:
        raise ValueError(
            "the registered Hydra semantic profile is intuitionistic"
        )
    _registered_profile_digest(
        "policy_environment.semantic_profile_sha256",
        environment["semantic_profile_sha256"],
    )
    surface = _safe_one_line(
        "policy_environment.surface", environment["surface"], limit=128
    )
    digest = environment["environment_sha256"]
    if type(digest) is not str or _SHA256_RE.fullmatch(digest) is None:
        raise ValueError("policy_environment.environment_sha256 is malformed")
    capabilities = environment["capabilities"]
    if type(capabilities) is not dict or set(capabilities) != _CAPABILITY_FIELDS:
        raise ValueError("policy_environment.capabilities is malformed")
    label = _safe_one_line(
        "policy_environment.capabilities.label",
        capabilities["label"],
        limit=128,
    )
    if label != surface:
        raise ValueError("policy environment surface and capability label disagree")
    commands = _name_list(
        "policy_environment.capabilities.allowed_commands",
        capabilities["allowed_commands"],
    )
    theorems = _name_list(
        "policy_environment.capabilities.allowed_theorems",
        capabilities["allowed_theorems"],
    )
    authority = SurfaceCapabilities(
        label=label,
        allowed_commands=commands,
        allowed_theorems=theorems,
    )
    if capability_sha256(authority) != digest:
        raise ValueError(
            "policy environment hash does not match its capability preimage"
        )
    return encoded


def _safe_error(exc: BaseException) -> tuple[str, str]:
    error_type = type(exc).__name__[:160] or "Exception"
    raw = " ".join(str(exc).split()) or error_type
    visible = "".join(
        character
        if unicodedata.category(character) not in {"Cc", "Cf", "Cs", "Zl", "Zp"}
        else f"\\u{ord(character):04x}"
        for character in raw
    )
    return error_type, visible[:MAX_POLICY_ERROR_CHARS]


@dataclass(frozen=True, slots=True)
class MacroAction:
    """One typed high-level surface action, never a closing automation call.

    A public tactic line may itself contain a tactical program.  Macro actions
    intentionally do not: their role in a portfolio is to propose explicit
    proof structure, witnesses, cuts, theorem uses, or rewrites.  Search still
    parses and executes the returned line independently.
    """

    line: str
    head: str = field(init=False)

    def __post_init__(self) -> None:
        line = _validate_tactic_line(self.line)
        if ";" in line or "<|>" in line or line.startswith("("):
            raise ValueError("a macro action cannot contain a tactical wrapper")
        head = _command_head(line)
        if head not in MACRO_ACTION_HEADS:
            allowed = ", ".join(sorted(MACRO_ACTION_HEADS))
            raise ValueError(
                f"macro action head {head!r} is not structural; expected one of: "
                f"{allowed}"
            )
        object.__setattr__(self, "line", line)
        object.__setattr__(self, "head", head)


@runtime_checkable
class IdentifiedCandidatePolicy(CandidatePolicy, Protocol):
    """A candidate policy with immutable JSON identity and proof authority."""

    @property
    def policy_environment(self) -> dict[str, object]:
        """Return the exact logic and tactic/theorem capability preimage."""

    @property
    def evaluation_identity(self) -> dict[str, object]:
        """Return provider, weights/transcript, prompt, and decode identity."""

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        max_candidates: int,
    ) -> tuple[str | MacroAction, ...]:
        """Return a bounded exact tuple at the declared environment."""


@dataclass(frozen=True, slots=True)
class HeadGate:
    """Serializable, exact-state gating for an expensive or specialist head."""

    state_sha256_allowlist: frozenset[str] | None = None

    def __post_init__(self) -> None:
        value = self.state_sha256_allowlist
        if value is None:
            return
        if isinstance(value, (str, bytes)):
            raise TypeError("state_sha256_allowlist must be a finite collection")
        try:
            frozen = frozenset(value)
        except TypeError as exc:
            raise TypeError(
                "state_sha256_allowlist must be a finite collection"
            ) from exc
        if not all(type(item) is str and _SHA256_RE.fullmatch(item) for item in frozen):
            raise ValueError(
                "state_sha256_allowlist must contain lowercase SHA-256 digests"
            )
        object.__setattr__(self, "state_sha256_allowlist", frozen)

    def allows(self, goals_before: tuple[str, ...]) -> bool:
        goals = _validate_goals(goals_before)
        allowed = self.state_sha256_allowlist
        return allowed is None or state_sha256(goals) in allowed

    def to_record(self) -> dict[str, object]:
        return {
            "state_sha256_allowlist": (
                None
                if self.state_sha256_allowlist is None
                else sorted(self.state_sha256_allowlist)
            )
        }


@dataclass(frozen=True, slots=True)
class PolicyHead:
    """One named portfolio member with a fixed role, quota, and gate."""

    name: str
    role: HeadRole
    quota: int
    policy: IdentifiedCandidatePolicy
    gating: HeadGate = HeadGate()
    semantic_profile_sha256: str = field(init=False)
    _identity_json: str = field(init=False, repr=False)
    _environment_json: str = field(init=False, repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _safe_policy_name(self.name))
        if self.role not in {"macro", "symbolic", "control"}:
            raise ValueError("policy head role must be macro, symbolic, or control")
        if type(self.quota) is not int or not 1 <= self.quota <= 1_024:
            raise ValueError("policy head quota must lie between 1 and 1024")
        if type(self.gating) is not HeadGate:
            raise TypeError("policy head gating must be an exact HeadGate")
        if not isinstance(self.policy, IdentifiedCandidatePolicy):
            raise TypeError(
                "policy head must implement propose, policy_environment, and "
                "evaluation_identity"
            )
        try:
            identity_json = _canonical_json_text(
                "evaluation_identity", self.policy.evaluation_identity
            )
            environment_json = _policy_environment_json(
                self.policy.policy_environment
            )
        except Exception as exc:
            raise ValueError(
                f"policy head {self.name!r} has invalid identity: {exc}"
            ) from None
        identity = _detached_object(identity_json)
        profile_digest = _environment_profile_digest(environment_json)
        if identity.get("semantic_profile_sha256") != profile_digest:
            raise ValueError(
                f"policy head {self.name!r} identity is not profile-bound"
            )
        object.__setattr__(self, "_identity_json", identity_json)
        object.__setattr__(self, "_environment_json", environment_json)
        object.__setattr__(
            self,
            "semantic_profile_sha256",
            profile_digest,
        )

    @property
    def evaluation_identity(self) -> dict[str, object]:
        return _detached_object(self._identity_json)

    @property
    def policy_environment(self) -> dict[str, object]:
        return _detached_object(self._environment_json)

    @property
    def identity_sha256(self) -> str:
        return _json_sha256(
            {
                "v": HYDRA_POLICY_VERSION,
                "semantic_profile_sha256": self.semantic_profile_sha256,
                "name": self.name,
                "role": self.role,
                "quota": self.quota,
                "gating": self.gating.to_record(),
                "environment": self.policy_environment,
                "policy": self.evaluation_identity,
            }
        )

    def to_record(self) -> dict[str, object]:
        return {
            "name": self.name,
            "role": self.role,
            "quota": self.quota,
            "gating": self.gating.to_record(),
            "semantic_profile_sha256": self.semantic_profile_sha256,
            "identity_sha256": self.identity_sha256,
            "policy": self.evaluation_identity,
        }


@dataclass(frozen=True, slots=True)
class ProposalRecord:
    """One complete, immutable account of a head at a canonical state."""

    portfolio_call: int
    head: str
    role: HeadRole
    head_identity_sha256: str
    semantic_profile_sha256: str
    goals: tuple[str, ...]
    state_sha256: str
    quota: int
    requested: int
    outcome: ProposalOutcome
    candidates: tuple[str, ...] = ()
    accepted_candidates: tuple[str, ...] = ()
    suppressed_duplicates: int = 0
    response_sha256: str | None = None
    error_type: str | None = None
    error: str | None = None

    def __post_init__(self) -> None:
        if type(self.portfolio_call) is not int or self.portfolio_call < 1:
            raise ValueError("portfolio_call must be positive")
        _safe_policy_name(self.head)
        if self.role not in {"macro", "symbolic", "control"}:
            raise ValueError("proposal role is malformed")
        if _SHA256_RE.fullmatch(self.head_identity_sha256) is None:
            raise ValueError("proposal head identity is malformed")
        _registered_profile_digest(
            "proposal semantic_profile_sha256", self.semantic_profile_sha256
        )
        goals = _validate_goals(self.goals)
        if self.state_sha256 != state_sha256(goals):
            raise ValueError("proposal state digest does not match its complete goals")
        if type(self.quota) is not int or self.quota < 1:
            raise ValueError("proposal quota must be positive")
        if type(self.requested) is not int or not 0 <= self.requested <= self.quota:
            raise ValueError("proposal requested count is outside its quota")
        if self.outcome not in {"ok", "gated", "error", "contract-error"}:
            raise ValueError("proposal outcome is malformed")
        if (
            type(self.candidates) is not tuple
            or type(self.accepted_candidates) is not tuple
        ):
            raise TypeError("proposal candidates must be exact tuples")
        if not all(type(item) is str for item in self.candidates):
            raise TypeError("proposal candidates must contain text")
        if not all(type(item) is str for item in self.accepted_candidates):
            raise TypeError("accepted proposal candidates must contain text")
        if (
            type(self.suppressed_duplicates) is not int
            or self.suppressed_duplicates < 0
        ):
            raise ValueError("suppressed duplicate count must be non-negative")
        if self.outcome == "gated" and self.requested != 0:
            raise ValueError("a gated proposal cannot claim a provider request")
        if self.outcome in {"ok", "error"} and self.requested != self.quota:
            raise ValueError(
                "a successful or failed provider call must request its full quota"
            )
        if self.outcome == "contract-error" and self.requested not in {
            0,
            self.quota,
        }:
            raise ValueError(
                "a contract error must occur before or during one full-quota call"
            )
        if self.outcome == "ok" and len(self.candidates) > self.requested:
            raise ValueError("a proposal returned more candidates than requested")
        if self.outcome != "ok" and (
            self.candidates
            or self.accepted_candidates
            or self.response_sha256 is not None
            or self.suppressed_duplicates != 0
        ):
            raise ValueError(
                "an unsuccessful proposal cannot claim candidates or duplicates"
            )
        if self.outcome == "ok" and (
            type(self.response_sha256) is not str
            or _SHA256_RE.fullmatch(self.response_sha256) is None
            or self.error_type is not None
            or self.error is not None
        ):
            raise ValueError("a successful proposal needs only its response digest")
        if self.outcome in {"error", "contract-error"} and (
            type(self.error_type) is not str or type(self.error) is not str
        ):
            raise ValueError("an errored proposal needs an error type and message")
        if self.outcome == "gated" and (
            self.error_type is not None or self.error is not None
        ):
            raise ValueError("a gated proposal cannot claim an error")

    def to_record(self) -> dict[str, object]:
        return {
            "portfolio_call": self.portfolio_call,
            "head": self.head,
            "role": self.role,
            "head_identity_sha256": self.head_identity_sha256,
            "semantic_profile_sha256": self.semantic_profile_sha256,
            "goals": list(self.goals),
            "state_sha256": self.state_sha256,
            "quota": self.quota,
            "requested": self.requested,
            "outcome": self.outcome,
            "candidates": list(self.candidates),
            "accepted_candidates": list(self.accepted_candidates),
            "suppressed_duplicates": self.suppressed_duplicates,
            "response_sha256": self.response_sha256,
            "error_type": self.error_type,
            "error": self.error,
        }

    def to_dict(self) -> dict[str, object]:
        """Compatibility spelling used by report composers."""

        return self.to_record()


@runtime_checkable
class HydraPortfolioPolicy(IdentifiedCandidatePolicy, Protocol):
    """The complete portfolio contract required by :func:`run_hydra`.

    Individual candidate heads implement :class:`IdentifiedCandidatePolicy`.
    The runner deliberately requires this stronger interface so its type
    signature does not imply that an arbitrary bare ``CandidatePolicy`` has
    enough identity, quota, and proposal-ledger evidence for publication.
    """

    @property
    def heads(self) -> tuple[PolicyHead, ...]:
        """Return the fixed ordered portfolio head declarations."""

    @property
    def total_quota(self) -> int:
        """Return the exact sum of fixed per-state head quotas."""

    @property
    def semantic_profile_sha256(self) -> str:
        """Return the registered semantic profile shared by every head."""

    @property
    def records(self) -> tuple[ProposalRecord, ...]:
        """Return the immutable proposal ledger accumulated so far."""


@dataclass(slots=True)
class HydraCandidatePolicy:
    """Deterministically merge bounded, identified candidate-policy heads."""

    heads: tuple[PolicyHead, ...]
    name: str = "peano-hydra-candidate-policy-v3"
    _environment_json: str = field(init=False, repr=False)
    _semantic_profile_sha256: str = field(init=False, repr=False)
    _records: list[ProposalRecord] = field(init=False, repr=False)
    _portfolio_calls: int = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self.name = _safe_policy_name(self.name)
        if type(self.heads) is not tuple or not self.heads:
            raise ValueError("Hydra needs one non-empty exact tuple of policy heads")
        if not all(type(head) is PolicyHead for head in self.heads):
            raise TypeError("Hydra heads must be exact PolicyHead values")
        names = tuple(head.name for head in self.heads)
        if len(set(names)) != len(names):
            raise ValueError("Hydra policy head names must be unique")
        environment_json = self.heads[0]._environment_json
        if any(head._environment_json != environment_json for head in self.heads[1:]):
            raise ValueError(
                "all Hydra heads must have the exact same policy environment"
            )
        self._environment_json = environment_json
        self._semantic_profile_sha256 = _environment_profile_digest(environment_json)
        self._records = []
        self._portfolio_calls = 0

    @property
    def total_quota(self) -> int:
        return sum(head.quota for head in self.heads)

    @property
    def policy_environment(self) -> dict[str, object]:
        return _detached_object(self._environment_json)

    @property
    def semantic_profile_sha256(self) -> str:
        return self._semantic_profile_sha256

    @property
    def evaluation_identity(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": "peano-hydra-candidate-policy-v3",
            "v": HYDRA_POLICY_VERSION,
            "semantic_profile_sha256": self.semantic_profile_sha256,
            "merge": "declared-head-order-stable-first-wins-v1",
            "quota_reallocation": False,
            "heads": [head.to_record() for head in self.heads],
            "environment": self.policy_environment,
        }

    @property
    def proposal_records(self) -> tuple[ProposalRecord, ...]:
        return tuple(self._records)

    @property
    def records(self) -> tuple[ProposalRecord, ...]:
        """Read-only proposal ledger consumed by the Hydra runner."""

        return self.proposal_records

    @property
    def error_ledger(self) -> tuple[ProposalRecord, ...]:
        return tuple(
            record
            for record in self._records
            if record.outcome in {"error", "contract-error"}
        )

    @property
    def generation_provenance(self) -> dict[str, object]:
        outcomes = {
            outcome: sum(record.outcome == outcome for record in self._records)
            for outcome in ("ok", "gated", "error", "contract-error")
        }
        return {
            "semantic_profile_sha256": self.semantic_profile_sha256,
            "portfolio_calls": self._portfolio_calls,
            "head_records": len(self._records),
            "outcomes": outcomes,
            "candidate_lines_returned": sum(
                len(record.candidates) for record in self._records
            ),
            "candidate_lines_accepted": sum(
                len(record.accepted_candidates) for record in self._records
            ),
            "suppressed_duplicates": sum(
                record.suppressed_duplicates for record in self._records
            ),
        }

    def _record_failure(
        self,
        *,
        call: int,
        head: PolicyHead,
        goals: tuple[str, ...],
        digest: str,
        outcome: Literal["error", "contract-error"],
        requested: int,
        exc: BaseException,
    ) -> None:
        error_type, error = _safe_error(exc)
        self._records.append(
            ProposalRecord(
                portfolio_call=call,
                head=head.name,
                role=head.role,
                head_identity_sha256=head.identity_sha256,
                semantic_profile_sha256=head.semantic_profile_sha256,
                goals=goals,
                state_sha256=digest,
                quota=head.quota,
                requested=requested,
                outcome=outcome,
                error_type=error_type,
                error=error,
            )
        )

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        max_candidates: int,
    ) -> tuple[str, ...]:
        goals = _validate_goals(goals_before)
        if type(max_candidates) is not int or max_candidates < 1:
            raise ValueError("max_candidates must be a positive integer")
        if max_candidates < self.total_quota:
            raise ValueError(
                "max_candidates is smaller than Hydra's declared fixed head quotas"
            )

        self._portfolio_calls += 1
        call = self._portfolio_calls
        digest = state_sha256(goals)
        merged: list[str] = []
        seen: set[str] = set()

        for head in self.heads:
            if not head.gating.allows(goals):
                self._records.append(
                    ProposalRecord(
                        portfolio_call=call,
                        head=head.name,
                        role=head.role,
                        head_identity_sha256=head.identity_sha256,
                        semantic_profile_sha256=head.semantic_profile_sha256,
                        goals=goals,
                        state_sha256=digest,
                        quota=head.quota,
                        requested=0,
                        outcome="gated",
                    )
                )
                continue

            try:
                current_identity = _canonical_json_text(
                    "evaluation_identity", head.policy.evaluation_identity
                )
                current_environment = _policy_environment_json(
                    head.policy.policy_environment
                )
                if current_identity != head._identity_json:
                    raise ValueError(
                        "policy evaluation identity changed after admission"
                    )
                if current_environment != head._environment_json:
                    raise ValueError("policy environment changed after admission")
            except Exception as exc:
                self._record_failure(
                    call=call,
                    head=head,
                    goals=goals,
                    digest=digest,
                    outcome="contract-error",
                    requested=0,
                    exc=exc,
                )
                continue

            try:
                raw = head.policy.propose(goals, max_candidates=head.quota)
            except Exception as exc:
                self._record_failure(
                    call=call,
                    head=head,
                    goals=goals,
                    digest=digest,
                    outcome="error",
                    requested=head.quota,
                    exc=exc,
                )
                continue

            try:
                after_identity = _canonical_json_text(
                    "evaluation_identity", head.policy.evaluation_identity
                )
                after_environment = _policy_environment_json(
                    head.policy.policy_environment
                )
                if after_identity != head._identity_json:
                    raise ValueError(
                        "policy evaluation identity changed during proposal"
                    )
                if after_environment != head._environment_json:
                    raise ValueError("policy environment changed during proposal")
                if type(raw) is not tuple:
                    raise TypeError("head result must be an exact tuple")
                if len(raw) > head.quota:
                    raise ValueError(
                        "head returned more candidates than its fixed quota"
                    )
                normalized: list[str] = []
                for value in raw:
                    if head.role == "macro":
                        if type(value) is MacroAction:
                            action = value
                        elif type(value) is str:
                            action = MacroAction(value)
                        else:
                            raise TypeError(
                                "macro heads may return only MacroAction or text"
                            )
                        normalized.append(action.line)
                    else:
                        if type(value) is not str:
                            raise TypeError(
                                "symbolic/control heads may return only tactic text"
                            )
                        normalized.append(_validate_tactic_line(value))
                candidates = tuple(normalized)
            except Exception as exc:
                self._record_failure(
                    call=call,
                    head=head,
                    goals=goals,
                    digest=digest,
                    outcome="contract-error",
                    requested=head.quota,
                    exc=exc,
                )
                continue

            accepted: list[str] = []
            duplicates = 0
            for candidate in candidates:
                if candidate in seen:
                    duplicates += 1
                    continue
                seen.add(candidate)
                accepted.append(candidate)
                merged.append(candidate)
            self._records.append(
                ProposalRecord(
                    portfolio_call=call,
                    head=head.name,
                    role=head.role,
                    head_identity_sha256=head.identity_sha256,
                    semantic_profile_sha256=head.semantic_profile_sha256,
                    goals=goals,
                    state_sha256=digest,
                    quota=head.quota,
                    requested=head.quota,
                    outcome="ok",
                    candidates=candidates,
                    accepted_candidates=tuple(accepted),
                    suppressed_duplicates=duplicates,
                    response_sha256=_json_sha256(list(candidates)),
                )
            )

        if len(merged) > max_candidates:  # pragma: no cover - quota invariant
            raise RuntimeError("Hydra's fixed quotas exceeded the host candidate bound")
        return tuple(merged)


class FixedCandidatePolicy:
    """One auditable state-independent candidate tuple for symbolic baselines."""

    __slots__ = (
        "name",
        "candidates",
        "_environment_json",
        "_provider_identity_json",
    )

    def __init__(
        self,
        candidates: tuple[str, ...],
        *,
        name: str,
        policy_environment: Mapping[str, object],
        provider_identity: Mapping[str, object],
    ) -> None:
        self.name = _safe_policy_name(name)
        if type(candidates) is not tuple or not candidates:
            raise ValueError("fixed candidates must be one non-empty exact tuple")
        self.candidates = tuple(_validate_tactic_line(item) for item in candidates)
        self._environment_json = _policy_environment_json(policy_environment)
        self._provider_identity_json = _provider_identity_json(provider_identity)

    @property
    def policy_environment(self) -> dict[str, object]:
        return _detached_object(self._environment_json)

    @property
    def evaluation_identity(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": "peano-hydra-fixed-candidate-policy-v3",
            "semantic_profile_sha256": _environment_profile_digest(
                self._environment_json
            ),
            "candidates": list(self.candidates),
            "candidates_sha256": _json_sha256(list(self.candidates)),
            "provider": _detached_object(self._provider_identity_json),
        }

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        max_candidates: int,
    ) -> tuple[str, ...]:
        _validate_goals(goals_before)
        if type(max_candidates) is not int or max_candidates < 1:
            raise ValueError("max_candidates must be a positive integer")
        return self.candidates[:max_candidates]


class NullCandidatePolicy:
    """An identified empty head for matched-quota ablations and controls."""

    __slots__ = ("name", "_environment_json", "_provider_identity_json")

    def __init__(
        self,
        *,
        name: str,
        policy_environment: Mapping[str, object],
        provider_identity: Mapping[str, object],
    ) -> None:
        self.name = _safe_policy_name(name)
        self._environment_json = _policy_environment_json(policy_environment)
        self._provider_identity_json = _provider_identity_json(provider_identity)

    @property
    def policy_environment(self) -> dict[str, object]:
        return _detached_object(self._environment_json)

    @property
    def evaluation_identity(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": "peano-hydra-null-candidate-policy-v3",
            "semantic_profile_sha256": _environment_profile_digest(
                self._environment_json
            ),
            "provider": _detached_object(self._provider_identity_json),
        }

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        max_candidates: int,
    ) -> tuple[str, ...]:
        _validate_goals(goals_before)
        if type(max_candidates) is not int or max_candidates < 1:
            raise ValueError("max_candidates must be a positive integer")
        return ()


@dataclass(frozen=True, slots=True)
class RecordedState:
    """A complete canonical state and its recorded ranked tactic lines."""

    goals: tuple[str, ...]
    candidates: tuple[str, ...]
    semantic_profile_sha256: str

    def __post_init__(self) -> None:
        goals = _validate_goals(self.goals)
        profile_digest = _registered_profile_digest(
            "recorded state semantic_profile_sha256",
            self.semantic_profile_sha256,
        )
        if type(self.candidates) is not tuple or not self.candidates:
            raise ValueError("a recorded state needs a non-empty candidate tuple")
        if len(self.candidates) > MAX_RECORDED_CANDIDATES_PER_STATE:
            raise ValueError("a recorded state has too many candidates")
        candidates = tuple(_validate_tactic_line(item) for item in self.candidates)
        object.__setattr__(self, "goals", goals)
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "semantic_profile_sha256", profile_digest)

    def to_record(self) -> dict[str, object]:
        return {
            "goals": list(self.goals),
            "state_sha256": state_sha256(self.goals),
            "semantic_profile_sha256": self.semantic_profile_sha256,
            "candidates": list(self.candidates),
        }


class RecordedCandidatePolicy:
    """A deterministic full-state lookup policy backed by inert records."""

    __slots__ = (
        "name",
        "_recorded_states",
        "_buckets",
        "_environment_json",
        "_provider_identity_json",
        "_kind",
    )

    def __init__(
        self,
        records: Iterable[RecordedState],
        *,
        name: str,
        policy_environment: Mapping[str, object],
        provider_identity: Mapping[str, object],
        _kind: str = "peano-hydra-recorded-candidate-policy-v3",
    ) -> None:
        self.name = _safe_policy_name(name)
        environment_json = _policy_environment_json(policy_environment)
        profile_digest = _environment_profile_digest(environment_json)
        merged: dict[tuple[str, ...], list[str]] = {}
        order: list[tuple[str, ...]] = []
        count = 0
        for count, record in enumerate(records, 1):
            if count > MAX_RECORDED_STATES:
                raise ValueError("recorded candidate policy has too many state rows")
            if type(record) is not RecordedState:
                raise TypeError(
                    "recorded policy rows must be exact RecordedState values"
                )
            if record.semantic_profile_sha256 != profile_digest:
                raise ValueError(
                    "recorded state and policy semantic profiles disagree"
                )
            if record.goals not in merged:
                merged[record.goals] = []
                order.append(record.goals)
            candidates = merged[record.goals]
            for candidate in record.candidates:
                if candidate not in candidates:
                    candidates.append(candidate)
            if len(candidates) > MAX_RECORDED_CANDIDATES_PER_STATE:
                raise ValueError("merged recorded state has too many candidates")
        if count == 0:
            raise ValueError("recorded candidate policy needs at least one state row")
        self._recorded_states = tuple(
            RecordedState(
                goals=goals,
                candidates=tuple(merged[goals]),
                semantic_profile_sha256=profile_digest,
            )
            for goals in order
        )
        buckets: dict[str, list[RecordedState]] = {}
        for record in self._recorded_states:
            buckets.setdefault(state_sha256(record.goals), []).append(record)
        self._buckets = {
            digest: tuple(bucket) for digest, bucket in buckets.items()
        }
        self._environment_json = environment_json
        self._provider_identity_json = _provider_identity_json(provider_identity)
        self._kind = _safe_one_line("recorded policy kind", _kind, limit=160)

    @classmethod
    def from_records(
        cls,
        records: Iterable[RecordedState],
        *,
        name: str,
        policy_environment: Mapping[str, object],
        provider_identity: Mapping[str, object],
    ) -> "RecordedCandidatePolicy":
        return cls(
            records,
            name=name,
            policy_environment=policy_environment,
            provider_identity=provider_identity,
        )

    @property
    def policy_environment(self) -> dict[str, object]:
        return _detached_object(self._environment_json)

    @property
    def recorded_states(self) -> tuple[RecordedState, ...]:
        """The exact immutable states used for lookup and gate construction."""

        return self._recorded_states

    @property
    def state_sha256s(self) -> frozenset[str]:
        return frozenset(state_sha256(record.goals) for record in self._recorded_states)

    @property
    def evaluation_identity(self) -> dict[str, object]:
        record_payload = [record.to_record() for record in self._recorded_states]
        return {
            "name": self.name,
            "kind": self._kind,
            "semantic_profile_sha256": _environment_profile_digest(
                self._environment_json
            ),
            "record_count": len(self._recorded_states),
            "records_sha256": _json_sha256(record_payload),
            "provider": _detached_object(self._provider_identity_json),
        }

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        max_candidates: int,
    ) -> tuple[str, ...]:
        goals = _validate_goals(goals_before)
        if type(max_candidates) is not int or max_candidates < 1:
            raise ValueError("max_candidates must be a positive integer")
        # Digest lookup is only an index.  Complete tuples are compared so even
        # a hypothetical SHA-256 collision cannot route another state's action.
        for record in self._buckets.get(state_sha256(goals), ()):
            if record.goals == goals:
                return record.candidates[:max_candidates]
        return ()


class ScriptCandidatePolicy(RecordedCandidatePolicy):
    """Turn a Peano batch v1 trace into a state-keyed untrusted policy."""

    __slots__ = ()

    @classmethod
    def from_batch_result(
        cls,
        batch: BatchResult,
        *,
        name: str,
        policy_environment: Mapping[str, object],
        include_heads: frozenset[str] | None = None,
        allow_partial: bool = False,
    ) -> "ScriptCandidatePolicy":
        if type(batch) is not BatchResult:
            raise TypeError("batch must be an exact BatchResult")
        if type(allow_partial) is not bool:
            raise TypeError("allow_partial must be a Boolean")
        environment_json = _policy_environment_json(policy_environment)
        environment = _detached_object(environment_json)
        profile_digest = _environment_profile_digest(environment_json)
        if (
            environment["classical"] is not batch.classical
            or environment["surface"] != batch.surface
            or environment["environment_sha256"] != batch.environment_sha256
        ):
            raise ValueError("batch result and scripted policy environment disagree")
        if include_heads is not None:
            if type(include_heads) is not frozenset or not include_heads:
                raise ValueError("include_heads must be None or a non-empty frozenset")
            if not all(
                type(head) is str and _HEAD_RE.fullmatch(head)
                for head in include_heads
            ):
                raise ValueError("include_heads contains a malformed tactic head")
        trace = batch.trace
        if type(trace) is not tuple or not trace:
            raise ValueError("script candidate policy requires a retained batch trace")
        try:
            trace_json = json.dumps(
                trace,
                ensure_ascii=False,
                allow_nan=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            detached_trace = json.loads(trace_json)
        except (TypeError, ValueError, json.JSONDecodeError) as exc:
            raise ValueError(f"batch trace is not strict JSON: {exc}") from None
        if type(detached_trace) is not list or not detached_trace:
            raise ValueError("batch trace is malformed")

        footer = detached_trace[-1]
        if type(footer) is not dict or set(footer) != _TRACE_FOOTER_FIELDS:
            raise ValueError("batch trace has no canonical final footer")
        if (
            type(footer["qed"]) is not bool
            or footer["theorem"] != batch.theorem
            or type(footer["tactic_count"]) is not int
            or footer["tactic_count"] != len(detached_trace) - 1
        ):
            raise ValueError("batch trace footer disagrees with its result")
        expected_qed = batch.status == "proved" and batch.kernel_checked is True
        if footer["qed"] is not expected_qed:
            raise ValueError("batch trace QED footer disagrees with its result")
        if expected_qed and footer["proof_size"] != batch.proof_nodes:
            raise ValueError("batch trace proof size disagrees with its result")
        if not expected_qed and not allow_partial:
            raise ValueError(
                "script candidate policy requires a kernel-checked QED; "
                "pass allow_partial=True only for explicitly labeled "
                "partial-search evidence"
            )

        try:
            canonical_theorem = canonical_profile_theorem(batch.theorem)
        except ValueError as exc:
            raise ValueError(
                f"batch theorem is outside the semantic profile: {exc}"
            ) from None
        if canonical_theorem != batch.theorem:
            raise ValueError("batch theorem is not in canonical profile form")

        records: list[RecordedState] = []
        source_commands: list[str] = []
        for index, row in enumerate(detached_trace[:-1], 1):
            if type(row) is not dict or set(row) != _TRACE_STEP_FIELDS:
                raise ValueError("batch trace contains a malformed step row")
            if (
                row["v"] != BATCH_VERSION
                or type(row["v"]) is not int
                or row["session"] != batch.session_id
                or row["step"] != index
                or type(row["step"]) is not int
                or row["status"] not in {"ok", "error"}
            ):
                raise ValueError("batch trace step identity is inconsistent")
            before = row["goals_before"]
            after = row["goals_after"]
            if type(before) is not list or type(after) is not list:
                raise ValueError("batch trace goals must be arrays")
            goals = _validate_goals(tuple(before))
            if not all(type(goal) is str for goal in after):
                raise ValueError("batch trace after-goals contain non-text values")
            line = _validate_tactic_line(row["tactic"])
            source_commands.append(line)
            # Failed attempts remain in the bound source trace as negative
            # search evidence; they are never promoted to recorded positive
            # candidate actions merely because a later command reached QED.
            if row["status"] == "error":
                continue
            selected = include_heads is None
            if include_heads is not None:
                try:
                    selected = _command_head(line) in include_heads
                except ValueError:
                    selected = False
            if selected:
                records.append(
                    RecordedState(
                        goals=goals,
                        candidates=(line,),
                        semantic_profile_sha256=profile_digest,
                    )
                )
        if not records:
            raise ValueError("batch trace contains no selected tactic rows")

        capabilities = environment["capabilities"]
        if type(capabilities) is not dict:  # pragma: no cover - schema guard
            raise ValueError("policy environment capabilities are malformed")
        authority = SurfaceCapabilities(
            label=environment["surface"],
            allowed_commands=_name_list(
                "policy_environment.capabilities.allowed_commands",
                capabilities["allowed_commands"],
            ),
            allowed_theorems=_name_list(
                "policy_environment.capabilities.allowed_theorems",
                capabilities["allowed_theorems"],
            ),
        )
        source_binding = _json_sha256(
            {
                "v": HYDRA_POLICY_VERSION,
                "semantic_profile_sha256": profile_digest,
                "source_batch": batch.to_dict(include_trace=True),
            }
        )
        request_id = (
            f"hydra-script-profile-{profile_digest[:12]}-"
            f"{source_binding[:12]}"
        )
        session_id = (
            f"peano-hydra-script-{profile_digest[:12]}-"
            f"{source_binding[:12]}"
        )
        profile_replay = run_proof(
            canonical_theorem,
            tuple(source_commands),
            request_id=request_id,
            classical=False,
            on_error=batch.on_error,
            capabilities=authority,
            session_id=session_id,
        )
        if profile_replay.request_id != request_id or profile_replay.session_id != session_id:
            raise ValueError("profile-bound batch replay lost its identity")
        if (
            profile_replay.status != batch.status
            or profile_replay.kernel_checked is not batch.kernel_checked
            or profile_replay.theorem != batch.theorem
            or profile_replay.goals != batch.goals
            or profile_replay.failed_tactics != batch.failed_tactics
            or profile_replay.proof_nodes != batch.proof_nodes
            or profile_replay.failed_step != batch.failed_step
            or profile_replay.error_type != batch.error_type
            or profile_replay.error != batch.error
            or profile_replay.surface != batch.surface
            or profile_replay.environment_sha256 != batch.environment_sha256
            or profile_replay.classical is not False
            or profile_replay.on_error != batch.on_error
            or profile_replay.trace is None
        ):
            raise ValueError("profile-bound batch replay disagrees with its source")

        def normalized_trace(value: object) -> list[object]:
            try:
                detached = json.loads(
                    json.dumps(
                        value,
                        ensure_ascii=False,
                        allow_nan=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise ValueError(f"batch replay trace is not strict JSON: {exc}") from None
            if type(detached) is not list or not detached:
                raise ValueError("batch replay trace is malformed")
            for row in detached[:-1]:
                if type(row) is not dict:
                    raise ValueError("batch replay trace row is malformed")
                row["session"] = "<profile-bound-session>"
            return detached

        if normalized_trace(profile_replay.trace) != normalized_trace(detached_trace):
            raise ValueError("profile-bound batch trace differs from its source")

        provider_identity = {
            "kind": "peano-batch-trace-profile-replay-v3",
            "semantic_profile_sha256": profile_digest,
            "batch": batch.to_dict(include_trace=False),
            "trace_sha256": hashlib.sha256(trace_json.encode("utf-8")).hexdigest(),
            "profile_replay": profile_replay.to_dict(include_trace=False),
            "profile_replay_trace_sha256": _json_sha256(
                list(profile_replay.trace)
            ),
            "include_heads": (
                None if include_heads is None else sorted(include_heads)
            ),
            "allow_partial": allow_partial,
        }
        return cls(
            records,
            name=name,
            policy_environment=environment,
            provider_identity=provider_identity,
            _kind="peano-hydra-script-candidate-policy-v3",
        )


__all__ = [
    "HYDRA_POLICY_VERSION",
    "HeadGate",
    "HeadRole",
    "HydraCandidatePolicy",
    "HydraPortfolioPolicy",
    "IdentifiedCandidatePolicy",
    "MACRO_ACTION_HEADS",
    "MacroAction",
    "NullCandidatePolicy",
    "PolicyHead",
    "ProposalOutcome",
    "ProposalRecord",
    "FixedCandidatePolicy",
    "RecordedCandidatePolicy",
    "RecordedState",
    "ScriptCandidatePolicy",
]
