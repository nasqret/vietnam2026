"""Fresh original-goal replay and experiment-validity checks for Hydra."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
from training.peano_hydra.policy import (  # noqa: E402
    FixedCandidatePolicy,
    HydraCandidatePolicy,
    PolicyHead,
)
import training.peano_hydra.runner as hydra_runner  # noqa: E402
from training.peano_policy.search import SearchLimits  # noqa: E402


def _capabilities() -> SurfaceCapabilities:
    return SurfaceCapabilities(
        label="hydra-runner-test",
        allowed_commands=frozenset({"left", "refl"}),
        allowed_theorems=frozenset(),
    )


def _limits(*, candidates: int = 1) -> SearchLimits:
    return SearchLimits(
        max_depth=1,
        beam_width=1,
        candidates_per_state=candidates,
        max_model_calls=1,
        max_states=1,
    )


def _fixed_portfolio(
    command: str,
    *,
    capabilities: SurfaceCapabilities,
) -> HydraCandidatePolicy:
    environment = hydra_runner.policy_environment(capabilities)
    fixed = FixedCandidatePolicy(
        (command,),
        name=f"fixed-{command}",
        policy_environment=environment,
        provider_identity={"kind": "runner-test-provider"},
    )
    return HydraCandidatePolicy(
        (PolicyHead("symbolic", "symbolic", 1, fixed),),
        name=f"hydra-{command}",
    )


@dataclass
class RaisingPolicy:
    name: str
    environment: dict[str, object]

    @property
    def policy_environment(self) -> dict[str, object]:
        return self.environment

    @property
    def evaluation_identity(self) -> dict[str, object]:
        return {"name": self.name, "kind": "deliberately-offline-test-provider"}

    def propose(self, goals_before, *, max_candidates):
        del goals_before, max_candidates
        raise RuntimeError("model endpoint unavailable")


@dataclass
class LedgerlessPolicy:
    name: str
    policy_environment: dict[str, object]
    total_quota: int = 1

    @property
    def evaluation_identity(self) -> dict[str, object]:
        return {"name": self.name, "kind": "forbidden-ledgerless-policy"}

    def propose(self, goals_before, *, max_candidates):
        del goals_before, max_candidates
        return ("refl",)


def test_proof_is_published_only_with_fresh_binding_trace() -> None:
    capabilities = _capabilities()
    policy = _fixed_portfolio("refl", capabilities=capabilities)
    result = hydra_runner.run_hydra(
        "0 = 0",
        policy,
        capabilities=capabilities,
        limits=_limits(),
        label="checked-refl",
    )

    assert result.proved is True
    assert result.status == "proof"
    assert result.commands == ("refl",)
    assert result.search.certificate_nodes == 1
    assert result.replay is not None
    assert result.replay.status == "proved"
    assert result.replay.kernel_checked is True
    assert result.replay.theorem == "0 = 0"
    assert result.replay.proof_nodes == result.search.certificate_nodes
    assert result.replay.trace is not None
    assert tuple(row["tactic"] for row in result.replay.trace[:-1]) == result.commands
    assert result.replay.trace[-1]["qed"] is True
    assert len(result.proposal_records) == 1
    assert result.degraded is False
    assert result.eligible_for_comparison is False
    assert result.comparison_ineligibility_reasons
    assert "pre-H0" in result.comparison_ineligibility_reasons[0]
    serialized = result.to_dict(include_trace=True)
    assert serialized["replay"]["trace"][-1]["qed"] is True


def test_failed_search_never_claims_replay_or_proof_data() -> None:
    capabilities = _capabilities()
    result = hydra_runner.run_hydra(
        "0 = 0",
        _fixed_portfolio("left", capabilities=capabilities),
        capabilities=capabilities,
        limits=_limits(),
        label="honest-failure",
    )

    assert result.proved is False
    assert result.status == "exhausted"
    assert result.commands == ()
    assert result.search.certificate_nodes is None
    assert result.replay is None
    assert result.commands_sha256 is None
    assert result.degraded is False
    assert result.eligible_for_comparison is False
    assert result.comparison_ineligibility_reasons


def test_provider_outage_does_not_taint_sound_proof_but_degrades_experiment() -> None:
    capabilities = _capabilities()
    environment = hydra_runner.policy_environment(capabilities)
    offline = RaisingPolicy("offline", environment)
    fallback = FixedCandidatePolicy(
        ("refl",),
        name="fallback",
        policy_environment=environment,
        provider_identity={"kind": "runner-test-fallback"},
    )
    policy = HydraCandidatePolicy(
        (
            PolicyHead("model", "macro", 1, offline),
            PolicyHead("fallback", "symbolic", 1, fallback),
        )
    )
    result = hydra_runner.run_hydra(
        "0 = 0",
        policy,
        capabilities=capabilities,
        limits=_limits(candidates=2),
        label="degraded-but-sound",
    )

    assert result.proved is True
    assert result.replay is not None and result.replay.kernel_checked is True
    assert result.degraded is True
    assert result.eligible_for_comparison is False
    assert any("outcome=error" in reason for reason in result.degradation_reasons)


def test_authority_quota_and_fresh_policy_contracts_fail_before_reuse() -> None:
    capabilities = _capabilities()
    policy = _fixed_portfolio("refl", capabilities=capabilities)
    different = SurfaceCapabilities(
        label="different-hydra-runner-test",
        allowed_commands=frozenset({"refl"}),
        allowed_theorems=frozenset(),
    )
    with pytest.raises(ValueError, match="environment"):
        hydra_runner.run_hydra(
            "0 = 0",
            policy,
            capabilities=different,
            limits=_limits(),
        )
    assert policy.records == ()

    with pytest.raises(ValueError, match="candidates_per_state"):
        hydra_runner.run_hydra(
            "0 = 0",
            policy,
            capabilities=capabilities,
            limits=_limits(candidates=2),
        )
    assert policy.records == ()

    first = hydra_runner.run_hydra(
        "0 = 0",
        policy,
        capabilities=capabilities,
        limits=_limits(),
    )
    assert first.proved
    with pytest.raises(ValueError, match="cannot be reused"):
        hydra_runner.run_hydra(
            "0 = 0",
            policy,
            capabilities=capabilities,
            limits=_limits(),
        )


def test_missing_proposal_ledger_blocks_publication_before_search() -> None:
    capabilities = _capabilities()
    policy = LedgerlessPolicy(
        "ledgerless",
        hydra_runner.policy_environment(capabilities),
    )
    with pytest.raises(TypeError, match="HydraPortfolioPolicy"):
        hydra_runner.run_hydra(
            "0 = 0",
            policy,
            capabilities=capabilities,
            limits=_limits(),
        )


def test_any_fresh_replay_disagreement_fails_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    capabilities = _capabilities()
    policy = _fixed_portfolio("refl", capabilities=capabilities)
    real_run_proof = hydra_runner.run_proof

    def forged_run_proof(*args, **kwargs):
        replay = real_run_proof(*args, **kwargs)
        assert replay.proof_nodes is not None
        return replace(replay, proof_nodes=replay.proof_nodes + 1)

    monkeypatch.setattr(hydra_runner, "run_proof", forged_run_proof)
    with pytest.raises(hydra_runner.HydraReplayError, match="certificate nodes"):
        hydra_runner.run_hydra(
            "0 = 0",
            policy,
            capabilities=capabilities,
            limits=_limits(),
            label="forged-replay",
        )


@pytest.mark.parametrize("label", ("model-v1", "model-v2", "model-v3"))
def test_direct_hydra_run_rejects_compact_literals_for_frozen_model_profiles(
    label: str,
) -> None:
    capabilities = SurfaceCapabilities(
        label=label,
        allowed_commands=frozenset({"refl"}),
        allowed_theorems=frozenset(),
    )
    policy = _fixed_portfolio("refl", capabilities=capabilities)

    with pytest.raises(ValueError, match="257"):
        hydra_runner.run_hydra(
            "257 = 257",
            policy,
            capabilities=capabilities,
            limits=_limits(),
        )
    assert policy.records == ()


def test_direct_hydra_run_accepts_modern_compact_literal_with_fresh_kernel_replay() -> None:
    capabilities = _capabilities()
    result = hydra_runner.run_hydra(
        "1000000 = 1000000",
        _fixed_portfolio("refl", capabilities=capabilities),
        capabilities=capabilities,
        limits=_limits(),
        label="modern-compact-campaign",
    )

    assert result.proved is True
    assert result.theorem == "1000000 = 1000000"
    assert result.replay is not None
    assert result.replay.kernel_checked is True
    assert result.replay.theorem == result.theorem
