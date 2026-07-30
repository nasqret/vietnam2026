"""The model-independent policy search is bounded and kernel judged."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.batch import verify_proof  # noqa: E402
from peano_lab.engine.tactics import InvalidProof  # noqa: E402
from peano_lab.kernel.formulas import parse_formula  # noqa: E402
from peano_lab.library.theorems import get as get_theorem  # noqa: E402
from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    EXCLUDED_POLICY_LIBRARY_NAMES,
    HELD_OUT_POLICY_NAMES,
    model_v2_environment,
)
from training.peano_policy.events import EVENT_FIELDS  # noqa: E402
import training.peano_policy.search as policy_search  # noqa: E402


def _capabilities(*commands: str) -> SurfaceCapabilities:
    return SurfaceCapabilities(
        label="policy-search-test",
        allowed_commands=frozenset(commands),
        allowed_theorems=frozenset(),
    )


@dataclass
class FunctionPolicy:
    function: object
    calls: list[tuple[str, ...]] = field(default_factory=list)

    def propose(
        self,
        goals_before: tuple[str, ...],
        *,
        max_candidates: int,
    ) -> tuple[object, ...]:
        self.calls.append(goals_before)
        return self.function(goals_before, max_candidates)  # type: ignore[operator]


def _limits(**changes: int) -> policy_search.SearchLimits:
    values = {
        "max_depth": 8,
        "beam_width": 8,
        "candidates_per_state": 8,
        "max_model_calls": 32,
        "max_states": 64,
    }
    values.update(changes)
    return policy_search.SearchLimits(**values)


def test_failed_first_candidate_retries_sibling_and_batch_rechecks_result(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    theorem = "0 = 0"
    policy = FunctionPolicy(lambda goals, limit: ("left", "refl"))
    capabilities = _capabilities("left", "refl")
    original_targets: list[object] = []
    real_final = policy_search.checked_surface_final

    def checked(state, original_target, *, classical=False, trace=None):
        original_targets.append(original_target)
        return real_final(
            state,
            original_target,
            classical=classical,
            trace=trace,
        )

    monkeypatch.setattr(policy_search, "checked_surface_final", checked)
    result = policy_search.search(
        theorem,
        policy,
        capabilities=capabilities,
        limits=_limits(),
    )

    assert result.status == "proof"
    assert result.commands == ("refl",)
    assert result.certificate_nodes == 1
    assert original_targets == [parse_formula(theorem)]
    assert policy.calls == [("⊢ 0 = 0",)]
    assert [item.kind for item in result.diagnostics] == ["tactic_error"]
    assert result.diagnostics[0].command == "left"

    replay = verify_proof(
        theorem,
        result.commands,
        capabilities=capabilities,
        session_id="policy-search-independent-replay",
    )
    assert replay.status == "proved"
    assert replay.kernel_checked is True
    assert replay.proof_nodes == result.certificate_nodes


def test_beam_keeps_a_sibling_and_backtracks_after_the_preferred_branch_dies() -> None:
    theorem = "0 = 0 \\/ 0 + 0 = 0"

    def candidates(goals: tuple[str, ...], limit: int) -> tuple[str, ...]:
        del limit
        state = goals[0]
        if "∨" in state:
            return ("left", "right")
        if state == "⊢ 0 = 0":
            return ("left",)  # legal model output, inapplicable tactic
        if state == "⊢ 0 + 0 = 0":
            return ("norm_num",)
        return ()

    policy = FunctionPolicy(candidates)
    capabilities = _capabilities("left", "right", "norm_num")
    result = policy_search.search(
        theorem,
        policy,
        capabilities=capabilities,
        limits=_limits(beam_width=2),
    )

    assert result.status == "proof"
    assert result.commands == ("right", "norm_num")
    assert result.model_calls == 3
    assert result.frontier_peak == 2
    assert any(item.kind == "tactic_error" for item in result.diagnostics)
    replay = verify_proof(theorem, result.commands, capabilities=capabilities)
    assert replay.status == "proved" and replay.kernel_checked


def test_canonical_successors_and_repeated_candidates_are_deduplicated() -> None:
    theorem = "0 = 0 \\/ 0 = 0"

    def candidates(goals: tuple[str, ...], limit: int) -> tuple[str, ...]:
        del limit
        return ("left", "left", "right") if "∨" in goals[0] else ("refl",)

    result = policy_search.search(
        theorem,
        FunctionPolicy(candidates),
        capabilities=_capabilities("left", "right", "refl"),
        limits=_limits(),
    )

    assert result.status == "proof"
    assert result.commands == ("left", "refl")
    assert result.states_discovered == 2  # root plus one canonical open state
    assert result.candidates_executed == 3  # duplicate text is never executed
    assert [item.kind for item in result.diagnostics] == [
        "duplicate_candidate",
        "duplicate_state",
    ]


@pytest.mark.parametrize(
    ("limits", "expected_kind"),
    [
        (_limits(max_depth=1), "depth_limit"),
        (_limits(max_model_calls=1), "model_call_limit"),
        (_limits(max_states=1), "state_limit"),
    ],
)
def test_depth_model_call_and_state_budgets_are_hard_limits(
    limits: policy_search.SearchLimits,
    expected_kind: str,
) -> None:
    policy = FunctionPolicy(
        lambda goals, limit: ("intro n",) if "∀" in goals[0] else ("refl",)
    )
    result = policy_search.search(
        "forall n. n = n",
        policy,
        capabilities=_capabilities("intro", "refl"),
        limits=limits,
    )

    assert result.status == "limit"
    assert result.commands == ()
    assert result.certificate_nodes is None
    assert any(item.kind == expected_kind for item in result.diagnostics)


def test_candidate_and_beam_budgets_cannot_fall_through_to_hidden_siblings() -> None:
    candidate_limited = policy_search.search(
        "0 = 0",
        FunctionPolicy(lambda goals, limit: ("left", "refl")),
        capabilities=_capabilities("left", "refl"),
        limits=_limits(candidates_per_state=1),
    )
    assert candidate_limited.status == "limit"
    assert [item.kind for item in candidate_limited.diagnostics] == [
        "candidate_limit",
        "tactic_error",
    ]

    def branches(goals: tuple[str, ...], limit: int) -> tuple[str, ...]:
        del limit
        if "∨" in goals[0]:
            return ("left", "right")
        if goals[0] == "⊢ 0 = 0":
            return ("left",)
        return ("norm_num",)

    beam_limited = policy_search.search(
        "0 = 0 \\/ 0 + 0 = 0",
        FunctionPolicy(branches),
        capabilities=_capabilities("left", "right", "norm_num"),
        limits=_limits(beam_width=1),
    )
    assert beam_limited.status == "limit"
    assert any(item.kind == "beam_limit" for item in beam_limited.diagnostics)
    assert beam_limited.commands == ()


def test_invalid_mutated_and_forbidden_outputs_never_claim_a_proof() -> None:
    hostile = FunctionPolicy(
        lambda goals, limit: (
            "refl\nqed",
            "qed",
            "refl ",
            "refl; unknown_tactic",
            "use add_comm",
            7,
        )
    )
    result = policy_search.search(
        "0 = 0",
        hostile,
        capabilities=_capabilities("refl", "use"),
        limits=_limits(),
    )

    assert result.status == "exhausted"
    assert result.proved is False
    assert result.commands == ()
    assert result.certificate_nodes is None
    assert {item.kind for item in result.diagnostics} == {
        "invalid_candidate",
        "tactic_error",
    }


def test_policy_failure_is_diagnostic_and_configuration_is_host_validated() -> None:
    class RaisingPolicy:
        def propose(self, goals_before, *, max_candidates):
            del goals_before, max_candidates
            raise RuntimeError("model server unavailable\nwith hostile second line")

    result = policy_search.search(
        "0 = 0",
        RaisingPolicy(),
        capabilities=_capabilities("refl"),
        limits=_limits(),
    )
    assert result.status == "limit"
    assert result.diagnostics[0].kind == "policy_error"
    assert "\n" not in result.diagnostics[0].message

    with pytest.raises(ValueError, match="may not exceed"):
        policy_search.SearchLimits(max_depth=33)
    with pytest.raises(ValueError, match="positive integer"):
        policy_search.SearchLimits(beam_width=0)
    with pytest.raises(TypeError, match="capabilities"):
        policy_search.search("0 = 0", RaisingPolicy())  # type: ignore[call-arg]


def test_live_events_are_exact_transactional_and_do_not_change_the_result() -> None:
    theorem = "0 = 0"
    capabilities = _capabilities("left", "refl")
    observed_policy = FunctionPolicy(lambda goals, limit: ("left", "refl"))
    records: list[dict[str, object]] = []

    observed = policy_search.search(
        theorem,
        observed_policy,
        capabilities=capabilities,
        limits=_limits(),
        on_event=records.append,
    )
    unobserved = policy_search.search(
        theorem,
        FunctionPolicy(lambda goals, limit: ("left", "refl")),
        capabilities=capabilities,
        limits=_limits(),
    )

    assert observed.to_dict() == unobserved.to_dict()
    assert [record["kind"] for record in records] == [
        "search_started",
        "state_selected",
        "proposal_received",
        "candidate_started",
        "candidate_result",
        "candidate_started",
        "candidate_result",
        "kernel_check_started",
        "kernel_check_finished",
        "search_finished",
    ]
    for record in records:
        kind = record["kind"]
        assert tuple(record)[0:2] == ("v", "kind")
        assert tuple(record)[2:] == EVENT_FIELDS[kind]  # type: ignore[index]

    failed = next(
        record
        for record in records
        if record["kind"] == "candidate_result"
        and record["command"] == "left"
    )
    assert failed["status"] == "error"
    assert failed["error_kind"] == "tactic_error"
    assert failed["goals_before"] == failed["goals_after"] == ("⊢ 0 = 0",)
    closed = next(
        record
        for record in records
        if record["kind"] == "candidate_result"
        and record["command"] == "refl"
    )
    assert closed["status"] == "ok"
    assert closed["goals_after"] == ()
    assert closed["disposition"] == "closed_pending_kernel"
    assert records[-2]["status"] == "accepted"
    assert records[-2]["certificate_nodes"] == 1
    assert records[-1]["status"] == "proof"


def test_live_events_show_logical_edges_not_internal_prefix_replays() -> None:
    theorem = "0 = 0 \\/ 0 + 0 = 0"

    def candidates(goals: tuple[str, ...], limit: int) -> tuple[str, ...]:
        del limit
        if "∨" in goals[0]:
            return ("left", "right")
        if goals[0] == "⊢ 0 = 0":
            return ("left",)
        return ("norm_num",)

    records: list[dict[str, object]] = []
    result = policy_search.search(
        theorem,
        FunctionPolicy(candidates),
        capabilities=_capabilities("left", "right", "norm_num"),
        limits=_limits(beam_width=2),
        on_event=records.append,
    )

    assert result.commands == ("right", "norm_num")
    starts = [
        record for record in records if record["kind"] == "candidate_started"
    ]
    assert [record["command"] for record in starts] == [
        "left",
        "right",
        "left",
        "norm_num",
    ]
    # The final edge replays its accepted prefix internally, but that prefix is
    # described in the path instead of being falsely displayed as a new firing.
    assert starts[-1]["path"] == ("right", "norm_num")
    assert starts[-1]["replay_commands"] == ("right", "norm_num")
    frontier = next(
        record for record in records if record["kind"] == "frontier_updated"
    )
    assert frontier["depth"] == 1
    assert frontier["frontier_size"] == 2
    assert frontier["pruned"] == 0


def test_kernel_rejection_is_streamed_and_search_still_finishes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records: list[dict[str, object]] = []

    def reject(*args: object, **kwargs: object) -> object:
        del args, kwargs
        raise InvalidProof("unit kernel rejection")

    monkeypatch.setattr(policy_search, "checked_surface_final", reject)
    result = policy_search.search(
        "0 = 0",
        FunctionPolicy(lambda goals, limit: ("refl",)),
        capabilities=_capabilities("refl"),
        limits=_limits(),
        on_event=records.append,
    )

    assert result.status == "exhausted"
    kernel = [
        record for record in records if record["kind"] == "kernel_check_finished"
    ]
    assert len(kernel) == 1
    assert kernel[0]["status"] == "rejected"
    assert kernel[0]["certificate_nodes"] is None
    assert kernel[0]["message"] == "unit kernel rejection"
    assert records[-1]["kind"] == "search_finished"
    assert records[-1]["status"] == "exhausted"


def test_depth_32_budget_contains_a_checked_reference_route_for_every_sealed_goal() -> None:
    """The GPU budget must not make a known held-out proof impossible."""

    environment = model_v2_environment()
    capabilities = SurfaceCapabilities(
        label=environment.capabilities.label,
        allowed_commands=frozenset(environment.capabilities.allowed_commands or ()),
        allowed_theorems=frozenset(environment.capabilities.allowed_theorems or ()),
    )
    assert capabilities.allowed_theorems.isdisjoint(
        EXCLUDED_POLICY_LIBRARY_NAMES
    )
    route_lengths: dict[str, int] = {}
    for name in sorted(HELD_OUT_POLICY_NAMES):
        specification = get_theorem(name)
        commands = tuple(
            f"use {dependency}" for dependency in specification.dependencies
        ) + tuple(specification.script)
        route_lengths[name] = len(commands)
        assert name not in capabilities.allowed_theorems
        assert len(commands) <= policy_search.MAX_SEARCH_DEPTH
        replay = verify_proof(
            specification.statement,
            commands,
            capabilities=capabilities,
            session_id=f"model-v2-oracle-{name}",
        )
        assert replay.status == "proved"
        assert replay.kernel_checked is True

    assert route_lengths == {
        "le_antisymm": 10,
        "le_total": 23,
        "le_trans": 10,
        "mul_eq_zero": 13,
    }
    assert policy_search.MAX_SEARCH_DEPTH >= 24
