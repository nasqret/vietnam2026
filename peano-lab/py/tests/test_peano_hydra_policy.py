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
    FixedCandidatePolicy,
    HeadGate,
    HydraCandidatePolicy,
    MacroAction,
    NullCandidatePolicy,
    PolicyHead,
    ScriptCandidatePolicy,
)
from training.peano_hydra.runner import policy_environment  # noqa: E402
from training.peano_policy.contract import model_v2_environment  # noqa: E402
from training.peano_policy.generate import (  # noqa: E402
    PeanoPolicyAdapter,
    PeanoPolicyCandidateAdapter,
)
from training.peano_policy.search import state_sha256  # noqa: E402


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
    environment = policy_environment(_capabilities())
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
    assert policy.generation_provenance["suppressed_duplicates"] == 1


def test_head_environment_and_runtime_identity_are_fail_closed() -> None:
    environment = policy_environment(_capabilities())
    other_environment = policy_environment(_capabilities("hydra-policy-other"))
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
    environment = policy_environment(_capabilities())
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
    environment = policy_environment(capabilities)
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


def test_script_policy_requires_checked_qed_unless_partial_is_explicit() -> None:
    capabilities = _capabilities()
    environment = policy_environment(capabilities)
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
    environment = policy_environment(_capabilities())
    null = NullCandidatePolicy(
        name="no-macro-control",
        policy_environment=environment,
        provider_identity={"kind": "intentional-control"},
    )
    assert null.propose(("⊢ 0 = 0",), max_candidates=1) == ()
    assert null.policy_environment == environment
    assert null.evaluation_identity["provider"] == {
        "kind": "intentional-control"
    }


def test_fixed_and_null_heads_reject_unbound_provider_identity() -> None:
    environment = policy_environment(_capabilities())
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


def test_existing_qwen_candidate_adapter_is_a_drop_in_untrusted_head(
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
    policy = HydraCandidatePolicy(
        (PolicyHead("qwen", "macro", 1, qwen),),
        name="qwen-drop-in-test",
    )

    assert policy.propose(("⊢ 0 = 0",), max_candidates=1) == (
        "have bridge : 0 = 0",
    )
    assert qwen.generation_calls == 1
    assert policy.records[0].outcome == "ok"
    assert policy.evaluation_identity["heads"][0]["policy"]["kind"] == (
        "peano-kernel-guided-candidate-policy-v1"
    )
