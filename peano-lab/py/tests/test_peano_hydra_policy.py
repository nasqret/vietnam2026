"""Provider-neutral Peano Hydra portfolio contracts."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.batch import run_proof  # noqa: E402
from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
from training.peano_hydra.policy import (  # noqa: E402
    HYDRA_POLICY_VERSION,
    FixedCandidatePolicy,
    HeadGate,
    HydraCandidatePolicy,
    MacroAction,
    NullCandidatePolicy,
    PolicyHead,
    ProposalRecord,
    RecordedCandidatePolicy,
    RecordedState,
    ScriptCandidatePolicy,
)
from training.peano_hydra.profile import semantic_profile_sha256  # noqa: E402
from training.peano_hydra.runner import policy_environment  # noqa: E402
from training.peano_policy.contract import model_v2_environment  # noqa: E402
from training.peano_policy.generate import (  # noqa: E402
    PeanoPolicyAdapter,
    PeanoPolicyCandidateAdapter,
)
from training.peano_policy.search import state_sha256  # noqa: E402


SEMANTIC_PROFILE_SHA256 = semantic_profile_sha256()


def _proposal_record(**changes: object) -> ProposalRecord:
    fields: dict[str, object] = {
        "portfolio_call": 1,
        "head": "symbolic",
        "role": "symbolic",
        "head_identity_sha256": "a" * 64,
        "semantic_profile_sha256": SEMANTIC_PROFILE_SHA256,
        "goals": ("⊢ 0 = 0",),
        "state_sha256": state_sha256(("⊢ 0 = 0",)),
        "quota": 2,
        "requested": 2,
        "outcome": "ok",
        "candidates": ("refl",),
        "accepted_candidates": ("refl",),
        "response_sha256": (
            "fe10c6e38248f7cc8f1284a1defc47e62ebcedcf9b92fa23151c8834e20770ce"
        ),
    }
    fields.update(changes)
    return ProposalRecord(**fields)  # type: ignore[arg-type]


def test_proposal_records_pin_quota_outcome_accounting() -> None:
    assert _proposal_record().requested == 2

    with pytest.raises(ValueError, match="full quota"):
        _proposal_record(requested=1)
    with pytest.raises(ValueError, match="more candidates than requested"):
        _proposal_record(
            quota=1,
            requested=1,
            candidates=("refl", "refl"),
            accepted_candidates=("refl",),
        )
    with pytest.raises(ValueError, match="full quota"):
        _proposal_record(
            requested=1,
            outcome="error",
            candidates=(),
            accepted_candidates=(),
            response_sha256=None,
            error_type="RuntimeError",
            error="offline",
        )
    with pytest.raises(ValueError, match="before or during"):
        _proposal_record(
            requested=1,
            outcome="contract-error",
            candidates=(),
            accepted_candidates=(),
            response_sha256=None,
            error_type="ValueError",
            error="identity changed",
        )
    with pytest.raises(ValueError, match="duplicates"):
        _proposal_record(
            requested=0,
            outcome="gated",
            candidates=(),
            accepted_candidates=(),
            response_sha256=None,
            suppressed_duplicates=1,
        )
    with pytest.raises(ValueError, match="cannot claim an error"):
        _proposal_record(
            requested=0,
            outcome="gated",
            candidates=(),
            accepted_candidates=(),
            response_sha256=None,
            error_type="ValueError",
            error="forged",
        )


def _capabilities(label: str = "hydra-policy-test") -> SurfaceCapabilities:
    return SurfaceCapabilities(
        label=label,
        allowed_commands=frozenset(
            {
                "apply",
                "compact_arith",
                "exact",
                "have",
                "induction",
                "refl",
                "rewrite",
                "simp",
            }
        ),
        allowed_theorems=frozenset(),
    )


def _environment(
    capabilities: SurfaceCapabilities,
    *,
    classical: bool = False,
) -> dict[str, object]:
    return policy_environment(
        capabilities,
        classical=classical,
        semantic_profile_sha256=SEMANTIC_PROFILE_SHA256,
    )


def _fixed(
    name: str,
    candidates: tuple[str, ...],
    environment: dict[str, object],
) -> FixedCandidatePolicy:
    return FixedCandidatePolicy(
        candidates,
        name=name,
        policy_environment=environment,
        provider_identity={"kind": "test-fixed-provider", "name": name},
    )


@dataclass
class StubPolicy:
    name: str
    environment: dict[str, object]
    candidates: tuple[object, ...] = ()
    failure: BaseException | None = None
    calls: list[tuple[tuple[str, ...], int]] = field(default_factory=list)
    identity_version: int = 1

    @property
    def policy_environment(self) -> dict[str, object]:
        return self.environment

    @property
    def evaluation_identity(self) -> dict[str, object]:
        return {
            "name": self.name,
            "kind": "test-stub-provider",
            "identity_version": self.identity_version,
            "semantic_profile_sha256": self.environment[
                "semantic_profile_sha256"
            ],
        }

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        max_candidates: int,
    ) -> tuple[object, ...]:
        self.calls.append((goals_before, max_candidates))
        if self.failure is not None:
            raise self.failure
        return self.candidates


@pytest.mark.parametrize(
    "line",
    [
        "have h : 0 = 0",
        "induction n",
        "apply h",
        "exact h",
        "rewrite <- h",
    ],
)
def test_macro_action_accepts_only_one_explicit_structural_line(line: str) -> None:
    action = MacroAction(line)
    assert action.line == line
    assert action.head == line.split(maxsplit=1)[0]


@pytest.mark.parametrize(
    "line",
    [
        "compact_arith",
        "ring",
        "simp",
        "qed",
        "first [exact h | simp]",
        "apply h; simp",
        " apply h",
        "apply h\nqed",
    ],
)
def test_macro_action_rejects_closers_sessions_wrappers_and_multiline(
    line: str,
) -> None:
    with pytest.raises(ValueError):
        MacroAction(line)


def test_portfolio_uses_fixed_quotas_stable_dedup_and_exact_state_gating() -> None:
    environment = _environment(_capabilities())
    goals = ("⊢ 0 = 0",)
    other_goals = ("⊢ S 0 = S 0",)
    first = _fixed("first", ("refl", "simp"), environment)
    gated = StubPolicy("gated", environment, ("simp", "compact_arith"))
    policy = HydraCandidatePolicy(
        (
            PolicyHead("symbolic", "symbolic", 2, first),
            PolicyHead(
                "critical",
                "symbolic",
                2,
                gated,
                HeadGate(frozenset({state_sha256(goals)})),
            ),
        )
    )

    assert policy.total_quota == 4
    assert policy.propose(other_goals, max_candidates=4) == ("refl", "simp")
    assert gated.calls == []
    assert [record.outcome for record in policy.records] == ["ok", "gated"]

    assert policy.propose(goals, max_candidates=4) == (
        "refl",
        "simp",
        "compact_arith",
    )
    assert gated.calls == [(goals, 2)]
    last = policy.records[-1]
    assert last.accepted_candidates == ("compact_arith",)
    assert last.suppressed_duplicates == 1
    assert last.semantic_profile_sha256 == SEMANTIC_PROFILE_SHA256
    assert all(
        record.semantic_profile_sha256 == SEMANTIC_PROFILE_SHA256
        for record in policy.records
    )
    assert policy.semantic_profile_sha256 == SEMANTIC_PROFILE_SHA256
    assert policy.evaluation_identity["v"] == HYDRA_POLICY_VERSION == 2
    assert policy.evaluation_identity["kind"].endswith("-v2")
    assert (
        policy.evaluation_identity["semantic_profile_sha256"]
        == SEMANTIC_PROFILE_SHA256
    )
    assert all(
        head["semantic_profile_sha256"] == SEMANTIC_PROFILE_SHA256
        for head in policy.evaluation_identity["heads"]
    )
    assert (
        first.evaluation_identity["semantic_profile_sha256"]
        == SEMANTIC_PROFILE_SHA256
    )
    assert first.evaluation_identity["kind"].endswith("-v2")
    assert (
        policy.generation_provenance["semantic_profile_sha256"]
        == SEMANTIC_PROFILE_SHA256
    )
    assert policy.generation_provenance["suppressed_duplicates"] == 1


def test_head_identity_binds_environment_and_complete_head_declaration() -> None:
    first_environment = _environment(_capabilities("first-environment"))
    second_environment = _environment(_capabilities("second-environment"))
    first_policy = _fixed("same-provider", ("refl",), first_environment)
    second_policy = _fixed("same-provider", ("refl",), second_environment)

    baseline = PolicyHead("head", "symbolic", 1, first_policy)
    different_environment = PolicyHead("head", "symbolic", 1, second_policy)
    different_name = PolicyHead("other-head", "symbolic", 1, first_policy)
    different_role = PolicyHead("head", "control", 1, first_policy)
    different_quota = PolicyHead("head", "symbolic", 2, first_policy)
    different_gate = PolicyHead(
        "head",
        "symbolic",
        1,
        first_policy,
        HeadGate(frozenset({"0" * 64})),
    )

    assert len(
        {
            baseline.identity_sha256,
            different_environment.identity_sha256,
            different_name.identity_sha256,
            different_role.identity_sha256,
            different_quota.identity_sha256,
            different_gate.identity_sha256,
        }
    ) == 6


def test_semantic_profile_environment_and_runtime_drift_are_fail_closed() -> None:
    environment = _environment(_capabilities())
    assert environment["semantic_profile_sha256"] == SEMANTIC_PROFILE_SHA256

    missing = dict(environment)
    missing.pop("semantic_profile_sha256")
    with pytest.raises(ValueError, match="semantic_profile_sha256"):
        _fixed("missing-profile", ("refl",), missing)

    for malformed in ("0" * 63, "A" * 64, "0" * 64, None):
        altered = dict(environment)
        altered["semantic_profile_sha256"] = malformed
        with pytest.raises(ValueError, match="semantic_profile_sha256"):
            _fixed("wrong-profile", ("refl",), altered)

    mutable = StubPolicy("mutable-profile", environment, ("refl",))
    portfolio = HydraCandidatePolicy(
        (PolicyHead("mutable-profile", "symbolic", 1, mutable),)
    )
    changed = dict(environment)
    changed["semantic_profile_sha256"] = "0" * 64
    mutable.environment = changed
    assert portfolio.propose(("⊢ 0 = 0",), max_candidates=1) == ()
    assert mutable.calls == []
    assert portfolio.records[0].outcome == "contract-error"
    assert (
        portfolio.records[0].semantic_profile_sha256
        == SEMANTIC_PROFILE_SHA256
    )


def test_head_environment_and_runtime_identity_are_fail_closed() -> None:
    environment = _environment(_capabilities())
    other_environment = _environment(_capabilities("hydra-policy-other"))
    one = _fixed("one", ("refl",), environment)
    two = _fixed("two", ("refl",), other_environment)
    with pytest.raises(ValueError, match="same policy environment"):
        HydraCandidatePolicy(
            (
                PolicyHead("one", "symbolic", 1, one),
                PolicyHead("two", "symbolic", 1, two),
            )
        )

    mutable = StubPolicy("mutable", environment, ("refl",))
    fallback = _fixed("fallback", ("refl",), environment)
    portfolio = HydraCandidatePolicy(
        (
            PolicyHead("mutable", "symbolic", 1, mutable),
            PolicyHead("fallback", "control", 1, fallback),
        )
    )
    mutable.identity_version = 2
    assert portfolio.propose(("⊢ 0 = 0",), max_candidates=2) == ("refl",)
    assert [record.outcome for record in portfolio.records] == [
        "contract-error",
        "ok",
    ]
    assert mutable.calls == []


def test_provider_failure_is_ledgered_but_another_head_can_still_propose() -> None:
    environment = _environment(_capabilities())
    failing = StubPolicy(
        "offline-model",
        environment,
        failure=RuntimeError("provider unavailable\nhostile second line"),
    )
    fallback = _fixed("fallback", ("refl",), environment)
    policy = HydraCandidatePolicy(
        (
            PolicyHead("model", "macro", 1, failing),
            PolicyHead("symbolic", "symbolic", 1, fallback),
        )
    )

    assert policy.propose(("⊢ 0 = 0",), max_candidates=2) == ("refl",)
    assert [record.outcome for record in policy.records] == ["error", "ok"]
    error = policy.error_ledger[0]
    assert error.error_type == "RuntimeError"
    assert error.error == "provider unavailable hostile second line"
    assert "\n" not in error.error


def test_checked_batch_trace_becomes_exact_full_state_policy() -> None:
    capabilities = _capabilities()
    environment = _environment(capabilities)
    batch = run_proof(
        "0 = 0",
        ("refl",),
        request_id="hydra-script-policy-test",
        capabilities=capabilities,
    )
    policy = ScriptCandidatePolicy.from_batch_result(
        batch,
        name="checked-script",
        policy_environment=environment,
        include_heads=frozenset({"refl"}),
    )

    root = ("⊢ 0 = 0",)
    assert policy.propose(root, max_candidates=1) == ("refl",)
    assert policy.propose(("⊢ S 0 = S 0",), max_candidates=1) == ()
    assert policy.state_sha256s == frozenset({state_sha256(root)})
    assert policy.recorded_states[0].goals == root
    assert (
        policy.recorded_states[0].semantic_profile_sha256
        == SEMANTIC_PROFILE_SHA256
    )
    assert (
        policy.recorded_states[0].to_record()["semantic_profile_sha256"]
        == SEMANTIC_PROFILE_SHA256
    )
    assert policy.evaluation_identity["kind"].endswith("-v2")
    assert (
        policy.evaluation_identity["semantic_profile_sha256"]
        == SEMANTIC_PROFILE_SHA256
    )
    assert (
        policy.evaluation_identity["provider"]["semantic_profile_sha256"]
        == SEMANTIC_PROFILE_SHA256
    )
    assert policy.evaluation_identity["provider"]["kind"] == (
        "peano-batch-trace-profile-replay-v2"
    )
    rebound = policy.evaluation_identity["provider"]["profile_replay"]
    assert SEMANTIC_PROFILE_SHA256[:12] in rebound["id"]
    assert SEMANTIC_PROFILE_SHA256[:12] in rebound["session"]
    assert rebound["id"] != batch.request_id
    assert rebound["kernel_checked"] is True
    assert policy.evaluation_identity["provider"]["trace_sha256"]

    assert batch.trace is not None
    bad_first = dict(batch.trace[0])
    bad_first["session"] = "wrong-session"
    forged = replace(batch, trace=(bad_first,) + batch.trace[1:])
    with pytest.raises(ValueError, match="identity is inconsistent"):
        ScriptCandidatePolicy.from_batch_result(
            forged,
            name="forged-script",
            policy_environment=environment,
        )


def test_script_policy_rejects_kernel_checked_open_de_bruijn_target() -> None:
    capabilities = _capabilities()
    environment = _environment(capabilities)
    legacy_open_target = run_proof(
        "#0 = #0",
        ("refl",),
        request_id="legacy-open-target",
        capabilities=capabilities,
    )
    assert legacy_open_target.status == "proved"
    assert legacy_open_target.kernel_checked is True

    with pytest.raises(ValueError, match="outside the semantic profile"):
        ScriptCandidatePolicy.from_batch_result(
            legacy_open_target,
            name="forbidden-open-target",
            policy_environment=environment,
        )


def test_recorded_state_is_a_profile_bound_dataset_row() -> None:
    environment = _environment(_capabilities())
    row = RecordedState(
        goals=("⊢ 0 = 0",),
        candidates=("refl",),
        semantic_profile_sha256=SEMANTIC_PROFILE_SHA256,
    )
    policy = RecordedCandidatePolicy.from_records(
        (row,),
        name="profile-bound-recording",
        policy_environment=environment,
        provider_identity={"kind": "test-recording"},
    )

    assert row.to_record()["semantic_profile_sha256"] == SEMANTIC_PROFILE_SHA256
    assert policy.recorded_states == (row,)
    assert policy.evaluation_identity["kind"].endswith("-v2")
    assert (
        policy.evaluation_identity["semantic_profile_sha256"]
        == SEMANTIC_PROFILE_SHA256
    )
    with pytest.raises(ValueError, match="semantic_profile_sha256"):
        replace(row, semantic_profile_sha256="0" * 64)


def test_script_policy_requires_checked_qed_unless_partial_is_explicit() -> None:
    capabilities = _capabilities()
    environment = _environment(capabilities)
    open_batch = run_proof(
        "0 = 0",
        ("have h : 0 = 0",),
        request_id="hydra-partial-script-policy-test",
        capabilities=capabilities,
    )
    assert open_batch.status == "open"
    assert open_batch.kernel_checked is False

    with pytest.raises(ValueError, match="kernel-checked QED"):
        ScriptCandidatePolicy.from_batch_result(
            open_batch,
            name="unlabeled-partial-script",
            policy_environment=environment,
        )

    partial = ScriptCandidatePolicy.from_batch_result(
        open_batch,
        name="explicit-partial-script",
        policy_environment=environment,
        allow_partial=True,
    )
    assert partial.propose(("⊢ 0 = 0",), max_candidates=1) == (
        "have h : 0 = 0",
    )
    assert partial.evaluation_identity["provider"]["allow_partial"] is True


def test_null_policy_is_an_identified_matched_quota_control() -> None:
    environment = _environment(_capabilities())
    null = NullCandidatePolicy(
        name="no-macro-control",
        policy_environment=environment,
        provider_identity={"kind": "intentional-control"},
    )
    assert null.propose(("⊢ 0 = 0",), max_candidates=1) == ()
    assert null.policy_environment == environment
    assert null.evaluation_identity["kind"].endswith("-v2")
    assert (
        null.evaluation_identity["semantic_profile_sha256"]
        == SEMANTIC_PROFILE_SHA256
    )
    assert null.evaluation_identity["provider"] == {
        "kind": "intentional-control"
    }


def test_fixed_and_null_heads_reject_unbound_provider_identity() -> None:
    environment = _environment(_capabilities())
    with pytest.raises(ValueError, match="provider_identity"):
        FixedCandidatePolicy(
            ("refl",),
            name="unbound-fixed",
            policy_environment=environment,
            provider_identity={},
        )
    with pytest.raises(ValueError, match="provider_identity"):
        NullCandidatePolicy(
            name="unbound-null",
            policy_environment=environment,
            provider_identity=None,  # type: ignore[arg-type]
        )


def test_legacy_qwen_prompt_adapter_is_rejected_until_profile_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "training.peano_policy.generate.generate_tactic_candidates",
        lambda **kwargs: ("have bridge : 0 = 0",),
    )
    adapter = PeanoPolicyAdapter(
        model=None,
        tokenizer=None,
        environment=model_v2_environment(),
        name="model-free-qwen-test",
        provenance={"weights": "test-only"},
    )
    qwen = PeanoPolicyCandidateAdapter(
        adapter,
        seed=7,
        name="model-free-qwen-candidates",
    )
    with pytest.raises(ValueError, match="semantic_profile_sha256"):
        PolicyHead("qwen", "macro", 1, qwen)
    assert qwen.generation_calls == 0
