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
from training.peano_hydra.profile import semantic_profile_sha256  # noqa: E402
from training.peano_hydra.result_schema import result_schema_identity  # noqa: E402
from training.peano_policy.search import SearchLimits  # noqa: E402


PROFILE_SHA256 = semantic_profile_sha256()


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
    environment = hydra_runner.policy_environment(
        capabilities,
        semantic_profile_sha256=PROFILE_SHA256,
    )
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


def _run_fixed(command: str = "refl"):
    capabilities = _capabilities()
    return hydra_runner.run_hydra(
        "0 = 0",
        _fixed_portfolio(command, capabilities=capabilities),
        capabilities=capabilities,
        semantic_profile_sha256=PROFILE_SHA256,
        limits=_limits(),
        label=f"fixed-{command}-run",
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
        return {
            "name": self.name,
            "kind": "deliberately-offline-test-provider",
            "semantic_profile_sha256": self.environment[
                "semantic_profile_sha256"
            ],
        }

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
        semantic_profile_sha256=PROFILE_SHA256,
        limits=_limits(),
        label="checked-refl",
    )

    assert result.proved is True
    assert result.status == "proof"
    assert result.evidence_kind == "proved"
    assert result.semantic_profile_sha256 == PROFILE_SHA256
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
    assert serialized["semantic_profile_sha256"] == PROFILE_SHA256
    assert serialized["environment"]["semantic_profile_sha256"] == PROFILE_SHA256
    assert serialized["policy_identity"]["semantic_profile_sha256"] == PROFILE_SHA256
    assert serialized["proposal_records"][0]["semantic_profile_sha256"] == PROFILE_SHA256
    assert serialized["profile_evidence_schema"] == {
        **result_schema_identity(),
        "schema_status": "exact-content-addressed",
        "claim_kind": "proved",
        "conformant": False,
        "ineligibility_reason": (
            hydra_runner.SURFACE_MACRO_V0_EVIDENCE_INELIGIBILITY
        ),
    }
    assert serialized["replay"]["trace"][-1]["qed"] is True


def test_failed_search_never_claims_replay_or_proof_data() -> None:
    capabilities = _capabilities()
    result = hydra_runner.run_hydra(
        "0 = 0",
        _fixed_portfolio("left", capabilities=capabilities),
        capabilities=capabilities,
        semantic_profile_sha256=PROFILE_SHA256,
        limits=_limits(),
        label="honest-failure",
    )

    assert result.proved is False
    assert result.status == "exhausted"
    assert result.evidence_kind == "unknown"
    assert result.commands == ()
    assert result.search.certificate_nodes is None
    assert result.replay is None
    assert result.commands_sha256 is None
    assert result.degraded is False
    assert result.eligible_for_comparison is False
    assert result.comparison_ineligibility_reasons
    serialized = result.to_dict()
    assert serialized["profile_evidence_schema"]["claim_kind"] == "unknown"
    assert serialized["profile_evidence_schema"]["ineligibility_reason"] == (
        hydra_runner.SURFACE_MACRO_V0_UNKNOWN_EVIDENCE_INELIGIBILITY
    )


def test_provider_outage_does_not_taint_sound_proof_but_degrades_experiment() -> None:
    capabilities = _capabilities()
    environment = hydra_runner.policy_environment(
        capabilities,
        semantic_profile_sha256=PROFILE_SHA256,
    )
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
        semantic_profile_sha256=PROFILE_SHA256,
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
            semantic_profile_sha256=PROFILE_SHA256,
            limits=_limits(),
        )
    assert policy.records == ()

    with pytest.raises(ValueError, match="candidates_per_state"):
        hydra_runner.run_hydra(
            "0 = 0",
            policy,
            capabilities=capabilities,
            semantic_profile_sha256=PROFILE_SHA256,
            limits=_limits(candidates=2),
        )
    assert policy.records == ()

    first = hydra_runner.run_hydra(
        "0 = 0",
        policy,
        capabilities=capabilities,
        semantic_profile_sha256=PROFILE_SHA256,
        limits=_limits(),
    )
    assert first.proved
    with pytest.raises(ValueError, match="cannot be reused"):
        hydra_runner.run_hydra(
            "0 = 0",
            policy,
            capabilities=capabilities,
            semantic_profile_sha256=PROFILE_SHA256,
            limits=_limits(),
        )


def test_missing_proposal_ledger_blocks_publication_before_search() -> None:
    capabilities = _capabilities()
    policy = LedgerlessPolicy(
        "ledgerless",
        hydra_runner.policy_environment(
            capabilities,
            semantic_profile_sha256=PROFILE_SHA256,
        ),
    )
    with pytest.raises(TypeError, match="HydraPortfolioPolicy"):
        hydra_runner.run_hydra(
            "0 = 0",
            policy,
            capabilities=capabilities,
            semantic_profile_sha256=PROFILE_SHA256,
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
            semantic_profile_sha256=PROFILE_SHA256,
            limits=_limits(),
            label="forged-replay",
        )


def test_profile_and_closed_target_admission_fail_closed_before_search() -> None:
    capabilities = _capabilities()

    with pytest.raises(TypeError, match="semantic_profile_sha256"):
        hydra_runner.policy_environment(capabilities)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="registered Hydra profile"):
        hydra_runner.policy_environment(
            capabilities,
            semantic_profile_sha256="0" * 64,
        )
    with pytest.raises(ValueError, match="intuitionistic"):
        hydra_runner.policy_environment(
            capabilities,
            semantic_profile_sha256=PROFILE_SHA256,
            classical=True,
        )

    policy = _fixed_portfolio("refl", capabilities=capabilities)
    with pytest.raises(ValueError, match="de Bruijn|well-scoped|closed"):
        hydra_runner.run_hydra(
            "#0 = #0",
            policy,
            capabilities=capabilities,
            semantic_profile_sha256=PROFILE_SHA256,
            limits=_limits(),
        )
    assert policy.records == ()

    oversized_policy = _fixed_portfolio("refl", capabilities=capabilities)
    with pytest.raises(ValueError, match="exceeds"):
        hydra_runner.run_hydra(
            "0" * (hydra_runner.MAX_INPUT + 1),
            oversized_policy,
            capabilities=capabilities,
            semantic_profile_sha256=PROFILE_SHA256,
            limits=_limits(),
        )
    assert oversized_policy.records == ()

    numeral_policy = _fixed_portfolio("refl", capabilities=capabilities)
    with pytest.raises(ValueError, match="resource-dangerous numeral"):
        hydra_runner.run_hydra(
            "257 = 257",
            numeral_policy,
            capabilities=capabilities,
            semantic_profile_sha256=PROFILE_SHA256,
            limits=_limits(),
        )
    assert numeral_policy.records == ()


def test_run_result_cannot_be_relabelled_to_another_profile() -> None:
    capabilities = _capabilities()
    result = hydra_runner.run_hydra(
        "0 = 0",
        _fixed_portfolio("refl", capabilities=capabilities),
        capabilities=capabilities,
        semantic_profile_sha256=PROFILE_SHA256,
        limits=_limits(),
    )

    with pytest.raises(ValueError, match="registered Hydra profile"):
        replace(result, semantic_profile_sha256="0" * 64)
    bad_environment = dict(result.environment)
    bad_environment["semantic_profile_sha256"] = "0" * 64
    with pytest.raises(ValueError, match="environment"):
        replace(result, environment=bad_environment)

    assert result.replay is not None
    with pytest.raises(hydra_runner.HydraReplayError, match="request id"):
        replace(result, replay=replace(result.replay, request_id="unbound-v1"))


def test_publication_replays_again_and_rejects_mutated_retained_trace() -> None:
    capabilities = _capabilities()
    result = hydra_runner.run_hydra(
        "0 = 0",
        _fixed_portfolio("refl", capabilities=capabilities),
        capabilities=capabilities,
        semantic_profile_sha256=PROFILE_SHA256,
        limits=_limits(),
    )
    assert result.replay is not None and result.replay.trace is not None
    result.replay.trace[0]["tactic"] = "left"

    with pytest.raises(hydra_runner.HydraReplayError, match="executed commands"):
        result.to_dict(include_trace=True)


@pytest.mark.parametrize("target", ["provider", "policy", "proposal", "limits"])
def test_publication_rejects_nested_provenance_mutation(target: str) -> None:
    result = _run_fixed()
    if target == "provider":
        result.policy_identity["heads"][0]["policy"]["provider"]["kind"] = (
            "forged-qwen-provider"
        )
    elif target == "policy":
        result.policy_identity["name"] = "forged-policy"
    elif target == "proposal":
        result.proposal_records[0]["candidates"][0] = "left"
    else:
        result.limits["max_states"] += 1

    with pytest.raises((ValueError, hydra_runner.HydraRunnerError)):
        result.to_dict(include_trace=True)


def test_surface_macro_v0_cannot_be_relabelled_comparison_eligible() -> None:
    result = _run_fixed()
    with pytest.raises(ValueError, match="comparison-ineligible"):
        replace(
            result,
            eligible_for_comparison=True,
            comparison_ineligibility_reasons=(),
        )
    with pytest.raises(ValueError, match="comparison-ineligible"):
        replace(result, comparison_ineligibility_reasons=("forged reason",))


def test_arbitrary_unsuccessful_status_cannot_be_published() -> None:
    result = _run_fixed("left")
    forged_search = replace(result.search, status="not_theorem")
    with pytest.raises(ValueError, match=r"proof \| exhausted \| limit"):
        replace(result, status="not_theorem", search=forged_search)


def test_degradation_is_recomputed_from_provider_records() -> None:
    capabilities = _capabilities()
    environment = hydra_runner.policy_environment(
        capabilities,
        semantic_profile_sha256=PROFILE_SHA256,
    )
    policy = HydraCandidatePolicy(
        (
            PolicyHead("model", "macro", 1, RaisingPolicy("offline", environment)),
            PolicyHead(
                "fallback",
                "symbolic",
                1,
                FixedCandidatePolicy(
                    ("refl",),
                    name="fallback",
                    policy_environment=environment,
                    provider_identity={"kind": "runner-test-fallback"},
                ),
            ),
        )
    )
    result = hydra_runner.run_hydra(
        "0 = 0",
        policy,
        capabilities=capabilities,
        semantic_profile_sha256=PROFILE_SHA256,
        limits=_limits(candidates=2),
    )
    assert result.degraded is True
    with pytest.raises(ValueError, match="degradation"):
        replace(result, degraded=False, degradation_reasons=())


def test_published_payload_is_detached_from_retained_result() -> None:
    result = _run_fixed()
    expected = result.to_dict(include_trace=True)
    mutated = result.to_dict(include_trace=True)
    mutated["policy_identity"]["name"] = "forged-policy"
    mutated["proposal_records"][0]["head"] = "forged-head"
    mutated["limits"]["max_states"] = 0

    assert result.to_dict(include_trace=True) == expected


def test_publication_fresh_replay_compares_noncommand_trace_fields(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _run_fixed()
    real_run_proof = hydra_runner.run_proof

    def forged_trace_run(*args, **kwargs):
        replay = real_run_proof(*args, **kwargs)
        assert replay.trace is not None
        replay.trace[0]["focus"] = "forged-focus"
        return replay

    monkeypatch.setattr(hydra_runner, "run_proof", forged_trace_run)
    with pytest.raises(
        hydra_runner.HydraReplayError,
        match="publication replay differs",
    ):
        result.to_dict(include_trace=True)
