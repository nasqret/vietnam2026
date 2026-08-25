"""Bounded, dependency-safe concurrent orchestration of checked Hydra goals."""

from __future__ import annotations

from dataclasses import replace
import json
from pathlib import Path
import sys
from threading import Barrier
from weakref import ref

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
from training.peano_hydra.runner import policy_environment  # noqa: E402
import training.peano_hydra.scheduler as scheduler  # noqa: E402
from training.peano_policy.search import SearchLimits  # noqa: E402


def _capabilities() -> SurfaceCapabilities:
    return SurfaceCapabilities(
        label="hydra-campaign-scheduler-test",
        allowed_commands=frozenset({"left", "refl"}),
        allowed_theorems=frozenset(),
    )


def _search_limits() -> SearchLimits:
    return SearchLimits(
        max_depth=1,
        beam_width=1,
        candidates_per_state=1,
        max_model_calls=2,
        max_states=2,
    )


def _portfolio(name: str, command: str) -> HydraCandidatePolicy:
    capabilities = _capabilities()
    provider = FixedCandidatePolicy(
        (command,),
        name=f"fixed-{name}",
        policy_environment=policy_environment(capabilities),
        provider_identity={"kind": "scheduler-test-provider", "name": name},
    )
    return HydraCandidatePolicy(
        (PolicyHead("symbolic", "symbolic", 1, provider),),
        name=f"portfolio-{name}",
    )


def _goal(
    name: str,
    *,
    theorem: str = "0 = 0",
    command: str = "refl",
    dependencies: tuple[str, ...] = (),
    policy_factory=None,
) -> scheduler.CampaignGoal:
    return scheduler.CampaignGoal(
        name,
        theorem,
        _capabilities(),
        policy_factory or (lambda: _portfolio(name, command)),
        dependencies=dependencies,
        limits=_search_limits(),
    )


def test_independent_goals_run_concurrently_and_dependencies_keep_stable_order() -> None:
    first_wave = Barrier(2, timeout=3)

    def root_factory(name: str):
        def create() -> HydraCandidatePolicy:
            first_wave.wait()
            return _portfolio(name, "refl")

        return create

    goals = (
        _goal("join", theorem="2 = 2", dependencies=("first", "second")),
        _goal("first", theorem="0 = 0", policy_factory=root_factory("first")),
        _goal("second", theorem="1 = 1", policy_factory=root_factory("second")),
        _goal("final", theorem="3 = 3", dependencies=("join",)),
    )
    report = scheduler.run_campaign(
        goals,
        limits=scheduler.CampaignLimits(max_workers=2),
    )

    assert [goal.goal_id for goal in report.goals] == [
        "join",
        "first",
        "second",
        "final",
    ]
    assert all(goal.proved for goal in report.goals)
    assert all(
        goal.run is not None
        and goal.run.replay is not None
        and goal.run.replay.kernel_checked is True
        for goal in report.goals
    )
    assert report.workers == 2
    assert report.waves == 3
    assert report.proved_goals == 4
    assert report.blocked_goals == 0
    assert report.model_calls == 4
    assert report.states_discovered == 4
    assert report.candidates_executed == 4
    assert report.proof_nodes == 4
    assert report.reserved_model_calls == 8
    assert report.reserved_states == 8
    assert report.reserved_candidates == 8
    payload = report.to_dict(include_trace=True)
    assert payload["eligible_for_comparison"] is False
    assert payload["goals"][0]["run"]["replay"]["trace"][-1]["qed"] is True


def test_failed_dependencies_block_descendants_without_creating_policies() -> None:
    called: list[str] = []

    def unexpected_policy(name: str):
        def create() -> HydraCandidatePolicy:
            called.append(name)
            return _portfolio(name, "refl")

        return create

    report = scheduler.run_campaign(
        (
            _goal("failed", command="left"),
            _goal("independent", theorem="1 = 1"),
            _goal(
                "child",
                dependencies=("failed",),
                policy_factory=unexpected_policy("child"),
            ),
            _goal(
                "grandchild",
                dependencies=("child",),
                policy_factory=unexpected_policy("grandchild"),
            ),
        )
    )

    assert [goal.status for goal in report.goals] == [
        "exhausted",
        "proof",
        "blocked",
        "blocked",
    ]
    assert report.goals[2].blocked_by == ("failed",)
    assert report.goals[3].blocked_by == ("child",)
    assert report.goals[2].run is None
    assert report.goals[3].run is None
    assert called == []
    assert report.proved_goals == 1
    assert report.blocked_goals == 2
    assert report.model_calls == 2


def test_dependency_failure_propagates_when_descendants_precede_their_parents() -> None:
    report = scheduler.run_campaign(
        (
            _goal("grandchild", dependencies=("child",)),
            _goal("child", dependencies=("failed",)),
            _goal("failed", command="left"),
        )
    )

    assert [goal.status for goal in report.goals] == [
        "blocked",
        "blocked",
        "exhausted",
    ]
    assert report.goals[0].blocked_by == ("child",)
    assert report.goals[1].blocked_by == ("failed",)
    assert report.model_calls == 1


@pytest.mark.parametrize(
    "budget",
    ("max_total_model_calls", "max_total_states", "max_total_candidates"),
)
def test_global_worst_case_budgets_fail_before_any_worker_starts(budget: str) -> None:
    called: list[str] = []

    def forbidden() -> HydraCandidatePolicy:
        called.append("started")
        return _portfolio("unexpected", "refl")

    goals = (
        _goal("first", policy_factory=forbidden),
        _goal("second", policy_factory=forbidden),
    )
    limits = scheduler.CampaignLimits(**{budget: 3})

    with pytest.raises(ValueError, match="global budget"):
        scheduler.run_campaign(goals, limits=limits)
    assert called == []


@pytest.mark.parametrize("corruption", ("duplicate", "unknown", "cycle"))
def test_invalid_dependency_graph_fails_before_policy_creation(corruption: str) -> None:
    called: list[str] = []

    def forbidden() -> HydraCandidatePolicy:
        called.append("started")
        return _portfolio("unexpected", "refl")

    if corruption == "duplicate":
        goals = (
            _goal("same", policy_factory=forbidden),
            _goal("same", policy_factory=forbidden),
        )
    elif corruption == "unknown":
        goals = (
            _goal("first", dependencies=("missing",), policy_factory=forbidden),
        )
    else:
        goals = (
            _goal("first", dependencies=("second",), policy_factory=forbidden),
            _goal("second", dependencies=("first",), policy_factory=forbidden),
        )

    with pytest.raises(ValueError):
        scheduler.run_campaign(goals)
    assert called == []


def test_shared_mutable_policy_owner_is_rejected_between_goal_workers() -> None:
    shared = _portfolio("shared", "refl")
    goals = (
        _goal("first", policy_factory=lambda: shared),
        _goal("second", policy_factory=lambda: shared),
    )

    with pytest.raises(scheduler.CampaignSchedulerError, match="share one policy"):
        scheduler.run_campaign(
            goals,
            limits=scheduler.CampaignLimits(max_workers=1),
        )


def test_completed_wave_releases_large_policy_owners_before_next_wave() -> None:
    class TrackablePortfolio(HydraCandidatePolicy):
        pass

    previous_wave: list[object] = []

    def first_factory() -> HydraCandidatePolicy:
        base = _portfolio("first", "refl")
        policy = TrackablePortfolio(base.heads, name="trackable-first")
        previous_wave.append(ref(policy))
        return policy

    def second_factory() -> HydraCandidatePolicy:
        assert len(previous_wave) == 1
        assert previous_wave[0]() is None
        return _portfolio("second", "refl")

    report = scheduler.run_campaign(
        (
            _goal("first", policy_factory=first_factory),
            _goal("second", dependencies=("first",), policy_factory=second_factory),
        )
    )

    assert report.proved_goals == 2
    assert report.waves == 2


@pytest.mark.parametrize(
    "corruption",
    (
        "theorem",
        "search_theorem",
        "authority",
        "limits",
        "model_calls",
        "negative_calls",
        "states",
        "missing_root",
        "edges",
        "proof_nodes",
    ),
)
def test_forged_worker_result_cannot_exceed_its_original_goal_or_reservation(
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    real_runner = scheduler.run_hydra

    def forged_runner(*args, **kwargs):
        result = real_runner(*args, **kwargs)
        if corruption == "theorem":
            return replace(result, theorem="0 = 1")
        if corruption == "authority":
            return replace(result, environment={})
        if corruption == "limits":
            return replace(result, limits={})
        if corruption == "search_theorem":
            search = replace(result.search, theorem="0 = 1")
        if corruption == "model_calls":
            search = replace(result.search, model_calls=3)
        elif corruption == "negative_calls":
            search = replace(result.search, model_calls=-1)
        elif corruption == "states":
            search = replace(result.search, states_discovered=3)
        elif corruption == "missing_root":
            search = replace(result.search, states_discovered=0)
        elif corruption == "proof_nodes":
            search = replace(result.search, certificate_nodes=2)
        elif corruption == "search_theorem":
            pass
        else:
            search = replace(result.search, candidates_executed=2)
        return replace(result, search=search)

    monkeypatch.setattr(scheduler, "run_hydra", forged_runner)

    with pytest.raises(scheduler.CampaignSchedulerError):
        scheduler.run_campaign((_goal("first"),))


@pytest.mark.parametrize("source", ("n = n", "0 = 0\nqed", " 0 = 0", ""))
def test_goal_validation_rejects_open_or_unsafe_formulas(source: str) -> None:
    with pytest.raises(ValueError):
        _goal("invalid", theorem=source)


def test_scheduler_limits_reject_excessive_workers_goals_and_boolean_budgets() -> None:
    with pytest.raises(ValueError, match="max_workers"):
        scheduler.CampaignLimits(max_workers=scheduler.MAX_CAMPAIGN_WORKERS + 1)
    with pytest.raises(ValueError, match="max_goals"):
        scheduler.CampaignLimits(max_goals=scheduler.MAX_CAMPAIGN_GOALS + 1)
    with pytest.raises(ValueError, match="positive integer"):
        scheduler.CampaignLimits(max_workers=True)  # type: ignore[arg-type]


@pytest.mark.parametrize("label", ("model-v1", "model-v2", "model-v3"))
def test_frozen_model_campaign_goals_reject_newer_compact_numerals(label: str) -> None:
    capabilities = SurfaceCapabilities(
        label=label,
        allowed_commands=frozenset({"refl"}),
        allowed_theorems=frozenset(),
    )
    with pytest.raises(ValueError, match="257"):
        scheduler.CampaignGoal(
            "frozen",
            "257 = 257",
            capabilities,
            lambda: _portfolio("unused", "refl"),
            limits=_search_limits(),
        )


def test_modern_campaign_goal_accepts_large_compact_literal_and_checks_replay() -> None:
    report = scheduler.run_campaign(
        (_goal("modern", theorem="1000000 = 1000000"),)
    )

    assert report.proved_goals == 1
    assert report.goals[0].run is not None
    assert report.goals[0].run.replay is not None
    assert report.goals[0].run.replay.kernel_checked is True
    assert report.goals[0].run.replay.theorem == "1000000 = 1000000"


def test_interrupted_campaign_resumes_only_after_independent_original_goal_replay(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkpoint = tmp_path / "campaign.checkpoint.json"
    attempts: list[str] = []
    failed = {"second": True}

    def first_factory() -> HydraCandidatePolicy:
        attempts.append("first")
        return _portfolio("first", "refl")

    def second_factory() -> HydraCandidatePolicy:
        attempts.append("second")
        if failed["second"]:
            raise RuntimeError("worker interrupted before proof completion")
        return _portfolio("second", "refl")

    goals = (
        _goal("first", policy_factory=first_factory),
        _goal(
            "second",
            theorem="1 = 1",
            dependencies=("first",),
            policy_factory=second_factory,
        ),
    )
    with pytest.raises(scheduler.CampaignSchedulerError, match="interrupted"):
        scheduler.run_campaign(goals, checkpoint=checkpoint)

    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    assert payload["v"] == scheduler.CAMPAIGN_CHECKPOINT_VERSION
    assert [record["id"] for record in payload["receipts"]] == ["first"]
    assert payload["receipts"][0]["commands"] == ["refl"]
    assert attempts == ["first", "second"]

    real_replay = scheduler.run_proof
    replayed: list[str] = []

    def observed_replay(theorem, commands, **kwargs):
        replayed.append(theorem)
        return real_replay(theorem, commands, **kwargs)

    monkeypatch.setattr(scheduler, "run_proof", observed_replay)
    failed["second"] = False
    report = scheduler.run_campaign(goals, checkpoint=checkpoint, resume=True)

    assert attempts == ["first", "second", "second"]
    assert replayed == ["0 = 0"]
    assert report.proved_goals == 2
    assert report.restored_goals == 1
    assert report.goals[0].restored is True
    assert report.goals[0].run is None
    assert report.goals[0].restored_replay is not None
    assert report.goals[0].restored_replay.kernel_checked is True
    assert report.goals[1].restored is False
    assert report.model_calls == 1
    assert report.proof_nodes == 2
    assert report.waves == 1
    assert [
        record["id"]
        for record in json.loads(checkpoint.read_text(encoding="utf-8"))["receipts"]
    ] == ["first", "second"]
    rendered = report.to_dict(include_trace=True)
    assert rendered["restored_goals"] == 1
    assert rendered["goals"][0]["restored_replay"]["trace"][-1]["qed"] is True


def test_complete_checkpoint_restores_all_proofs_without_model_or_policy_execution(
    tmp_path: Path,
) -> None:
    checkpoint = tmp_path / "completed.json"
    calls: list[str] = []

    def policy() -> HydraCandidatePolicy:
        calls.append("model")
        return _portfolio("first", "refl")

    goals = (_goal("first", policy_factory=policy),)
    fresh = scheduler.run_campaign(goals, checkpoint=checkpoint)
    resumed = scheduler.run_campaign(goals, checkpoint=checkpoint, resume=True)

    assert fresh.proved_goals == 1 and fresh.restored_goals == 0
    assert resumed.proved_goals == 1 and resumed.restored_goals == 1
    assert resumed.model_calls == 0
    assert resumed.candidates_executed == 0
    assert resumed.waves == 0
    assert calls == ["model"]


@pytest.mark.parametrize(
    "tampering",
    (
        "theorem",
        "dependencies",
        "goal_digest",
        "environment",
        "logic",
        "commands",
        "command_digest",
        "proof_nodes",
        "unknown_goal",
        "duplicate_goal",
        "unsafe_command",
        "extra_field",
    ),
)
def test_mutated_checkpoint_proof_is_never_trusted_without_exact_fresh_replay(
    tmp_path: Path,
    tampering: str,
) -> None:
    checkpoint = tmp_path / "mutated.json"
    calls: list[str] = []

    def policy() -> HydraCandidatePolicy:
        calls.append("model")
        return _portfolio("first", "refl")

    goals = (_goal("first", policy_factory=policy),)
    scheduler.run_campaign(goals, checkpoint=checkpoint)
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    receipt = payload["receipts"][0]
    if tampering == "theorem":
        receipt["theorem"] = "0 = 1"
    elif tampering == "dependencies":
        receipt["dependencies"] = ["missing"]
    elif tampering == "goal_digest":
        receipt["goal_sha256"] = "0" * 64
    elif tampering == "environment":
        receipt["environment_sha256"] = "0" * 64
    elif tampering == "logic":
        receipt["classical"] = True
    elif tampering == "commands":
        receipt["commands"] = ["left"]
        receipt["commands_sha256"] = scheduler._sha256(receipt["commands"])
    elif tampering == "command_digest":
        receipt["commands_sha256"] = "0" * 64
    elif tampering == "proof_nodes":
        receipt["proof_nodes"] += 1
    elif tampering == "unknown_goal":
        receipt["id"] = "forged"
    elif tampering == "duplicate_goal":
        payload["receipts"].append(dict(receipt))
    elif tampering == "unsafe_command":
        receipt["commands"] = ["refl\nqed"]
        receipt["commands_sha256"] = scheduler._sha256(receipt["commands"])
    else:
        receipt["forged"] = True
    checkpoint.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(scheduler.CampaignSchedulerError):
        scheduler.run_campaign(goals, checkpoint=checkpoint, resume=True)
    assert calls == ["model"]


@pytest.mark.parametrize("change", ("statement", "authority", "goal_limits", "workers"))
def test_resume_rejects_any_changed_graph_authority_or_resource_envelope(
    tmp_path: Path,
    change: str,
) -> None:
    checkpoint = tmp_path / "graph.json"
    calls: list[str] = []

    def policy() -> HydraCandidatePolicy:
        calls.append("model")
        return _portfolio("first", "refl")

    original = _goal("first", policy_factory=policy)
    limits = scheduler.CampaignLimits(max_workers=2)
    scheduler.run_campaign((original,), limits=limits, checkpoint=checkpoint)
    if change == "statement":
        changed = _goal("first", theorem="1 = 1", policy_factory=policy)
    elif change == "authority":
        changed = replace(
            original,
            capabilities=SurfaceCapabilities(
                label="different-campaign-authority",
                allowed_commands=frozenset({"left", "refl"}),
                allowed_theorems=frozenset(),
            ),
        )
    elif change == "goal_limits":
        changed = replace(
            original,
            limits=replace(original.limits, max_model_calls=3),
        )
    else:
        changed = original
        limits = scheduler.CampaignLimits(max_workers=1)

    with pytest.raises(scheduler.CampaignSchedulerError, match="graph"):
        scheduler.run_campaign(
            (changed,),
            limits=limits,
            checkpoint=checkpoint,
            resume=True,
        )
    assert calls == ["model"]


@pytest.mark.parametrize("corruption", ("missing_parent", "reordered"))
def test_checkpoint_never_restores_child_before_verified_prerequisites(
    tmp_path: Path,
    corruption: str,
) -> None:
    checkpoint = tmp_path / "dependency-order.json"
    goals = (
        _goal("first"),
        _goal("second", theorem="1 = 1", dependencies=("first",)),
    )
    scheduler.run_campaign(goals, checkpoint=checkpoint)
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    if corruption == "missing_parent":
        payload["receipts"] = [payload["receipts"][1]]
    else:
        payload["receipts"].reverse()
    checkpoint.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(scheduler.CampaignSchedulerError, match="dependency"):
        scheduler.run_campaign(goals, checkpoint=checkpoint, resume=True)


def test_checkpoint_replay_cannot_widen_frozen_model_witness_profile(
    tmp_path: Path,
) -> None:
    checkpoint = tmp_path / "frozen-model.json"
    capabilities = SurfaceCapabilities(
        label="model-v3",
        allowed_commands=frozenset({"exists", "refl"}),
        allowed_theorems=frozenset(),
    )

    def frozen_policy() -> HydraCandidatePolicy:
        provider = FixedCandidatePolicy(
            ("refl",),
            name="frozen-symbolic",
            policy_environment=policy_environment(capabilities),
            provider_identity={"kind": "frozen-checkpoint-test"},
        )
        return HydraCandidatePolicy(
            (PolicyHead("symbolic", "symbolic", 1, provider),),
            name="frozen-checkpoint-policy",
        )

    goals = (
        scheduler.CampaignGoal(
            "frozen",
            "0 = 0",
            capabilities,
            frozen_policy,
            limits=_search_limits(),
        ),
    )
    scheduler.run_campaign(goals, checkpoint=checkpoint)
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    payload["receipts"][0]["commands"] = ["exists 257"]
    payload["receipts"][0]["commands_sha256"] = scheduler._sha256(
        payload["receipts"][0]["commands"]
    )
    checkpoint.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(scheduler.CampaignSchedulerError, match="unsafe or unbounded"):
        scheduler.run_campaign(goals, checkpoint=checkpoint, resume=True)


@pytest.mark.parametrize("malformation", ("duplicate_key", "extra_field", "version", "size"))
def test_checkpoint_rejects_ambiguous_unsupported_and_unbounded_files(
    tmp_path: Path,
    malformation: str,
) -> None:
    checkpoint = tmp_path / "invalid.json"
    goals = (_goal("first"),)
    scheduler.run_campaign(goals, checkpoint=checkpoint)
    payload = json.loads(checkpoint.read_text(encoding="utf-8"))
    if malformation == "duplicate_key":
        checkpoint.write_text('{"v":1,"v":1}', encoding="utf-8")
    elif malformation == "extra_field":
        payload["unexpected"] = True
        checkpoint.write_text(json.dumps(payload), encoding="utf-8")
    elif malformation == "version":
        payload["v"] = 99
        checkpoint.write_text(json.dumps(payload), encoding="utf-8")
    else:
        checkpoint.write_bytes(b"x" * (scheduler.MAX_CAMPAIGN_CHECKPOINT_BYTES + 2))

    with pytest.raises(scheduler.CampaignSchedulerError):
        scheduler.run_campaign(goals, checkpoint=checkpoint, resume=True)


def test_checkpoint_refuses_symlinks_and_unrequested_overwrite(tmp_path: Path) -> None:
    protected = tmp_path / "protected.txt"
    protected.write_text("leave me untouched", encoding="utf-8")
    link = tmp_path / "checkpoint-link.json"
    link.symlink_to(protected)
    goals = (_goal("first"),)

    with pytest.raises(scheduler.CampaignSchedulerError, match="non-symlink"):
        scheduler.run_campaign(goals, checkpoint=link)
    with pytest.raises(scheduler.CampaignSchedulerError, match="non-symlink"):
        scheduler.run_campaign(goals, checkpoint=link, resume=True)
    assert protected.read_text(encoding="utf-8") == "leave me untouched"

    existing = tmp_path / "existing.json"
    scheduler.run_campaign(goals, checkpoint=existing)
    original = existing.read_bytes()
    with pytest.raises(scheduler.CampaignSchedulerError, match="already exists"):
        scheduler.run_campaign(goals, checkpoint=existing)
    assert existing.read_bytes() == original

    directory = tmp_path / "real-directory"
    directory.mkdir()
    parent_link = tmp_path / "parent-link"
    parent_link.symlink_to(directory, target_is_directory=True)
    with pytest.raises(scheduler.CampaignSchedulerError, match="non-symlink directory"):
        scheduler.run_campaign(goals, checkpoint=parent_link / "unsafe.json")
    assert tuple(directory.iterdir()) == ()


def test_failed_atomic_checkpoint_update_leaves_prior_committed_receipt_valid(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    checkpoint = tmp_path / "atomic.json"
    goals = (_goal("first"),)
    real_replace = scheduler.os.replace

    def interrupted_replace(*args, **kwargs):
        raise OSError("simulated interrupted atomic checkpoint replace")

    monkeypatch.setattr(scheduler.os, "replace", interrupted_replace)
    with pytest.raises(scheduler.CampaignSchedulerError, match="atomic publication"):
        scheduler.run_campaign(goals, checkpoint=checkpoint)

    assert json.loads(checkpoint.read_text(encoding="utf-8"))["receipts"] == []
    assert tuple(path.name for path in tmp_path.iterdir()) == ("atomic.json",)

    monkeypatch.setattr(scheduler.os, "replace", real_replace)
    report = scheduler.run_campaign(goals, checkpoint=checkpoint, resume=True)
    assert report.proved_goals == 1
    assert report.restored_goals == 0
    assert len(json.loads(checkpoint.read_text(encoding="utf-8"))["receipts"]) == 1


def test_resume_flag_requires_exact_checkpoint_path_and_boolean_mode() -> None:
    goals = (_goal("first"),)

    with pytest.raises(ValueError, match="explicit checkpoint"):
        scheduler.run_campaign(goals, resume=True)
    with pytest.raises(TypeError, match="filesystem Path"):
        scheduler.run_campaign(goals, checkpoint="not-a-path")  # type: ignore[arg-type]
    with pytest.raises(TypeError, match="Boolean"):
        scheduler.run_campaign(goals, resume=1)  # type: ignore[arg-type]
