"""The model-independent policy search is bounded and kernel judged."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field, replace
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.batch import verify_proof  # noqa: E402
from peano_lab.kernel.formulas import parse_formula  # noqa: E402
from peano_lab.library.theorems import get as get_theorem  # noqa: E402
from peano_lab.kernel.terms import UNARY_NUMERAL_LIMIT  # noqa: E402
from peano_lab.ui.prove import MAX_NUMERAL, SurfaceCapabilities  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    EXCLUDED_POLICY_LIBRARY_NAMES,
    HELD_OUT_POLICY_NAMES,
    model_v2_environment,
)
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


def test_persistent_prefix_executes_each_edge_once_with_fresh_branch_traces(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_surface = policy_search.run_surface
    transitions: list[tuple[str, int, object]] = []

    def observed_surface(owner, command, *, capabilities, record_trace):
        transitions.append((command, len(owner.state.history), owner.trace))
        assert record_trace is False
        return real_surface(
            owner,
            command,
            capabilities=capabilities,
            record_trace=record_trace,
        )

    monkeypatch.setattr(policy_search, "run_surface", observed_surface)

    def next_edge(goals: tuple[str, ...], limit: int) -> tuple[str, ...]:
        del limit
        state = goals[0]
        if state.startswith("⊢ ∀"):
            return ("intro n",)
        if "∀" in state:
            return ("intro m",)
        return ("refl",)

    result = policy_search.search(
        "forall n. forall m. n = n",
        FunctionPolicy(next_edge),
        capabilities=_capabilities("intro", "refl"),
        limits=_limits(),
    )

    assert result.status == "proof"
    assert result.commands == ("intro n", "intro m", "refl")
    assert result.candidates_executed == len(transitions) == 3
    assert [(command, depth) for command, depth, _ in transitions] == [
        ("intro n", 0),
        ("intro m", 1),
        ("refl", 2),
    ]
    assert len({id(trace) for _, _, trace in transitions}) == len(transitions)
    assert all(trace.record_count == 0 for _, _, trace in transitions)


def test_failed_tactical_cannot_modify_cached_parent_or_contaminate_sibling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_surface = policy_search.run_surface
    transitions: list[tuple[str, int, object]] = []

    def observed_surface(owner, command, *, capabilities, record_trace):
        transitions.append((command, len(owner.state.history), owner.trace))
        return real_surface(
            owner,
            command,
            capabilities=capabilities,
            record_trace=record_trace,
        )

    monkeypatch.setattr(policy_search, "run_surface", observed_surface)
    result = policy_search.search(
        "forall n. n = n",
        FunctionPolicy(
            lambda goals, limit: (
                ("intro n; left", "intro n")
                if "∀" in goals[0]
                else ("refl",)
            )
        ),
        capabilities=_capabilities("intro", "left", "refl"),
        limits=_limits(),
    )

    assert result.status == "proof"
    assert result.commands == ("intro n", "refl")
    assert result.candidates_executed == len(transitions) == 3
    assert [(command, depth) for command, depth, _ in transitions] == [
        ("intro n; left", 0),
        ("intro n", 0),
        ("refl", 1),
    ]
    assert transitions[0][2] is not transitions[1][2]
    assert [item.kind for item in result.diagnostics] == ["tactic_error"]


@pytest.mark.parametrize(
    "corruption", ("target", "source", "mode", "authority", "commands", "goals")
)
def test_corrupted_cached_prefix_fails_closed_before_executing_next_edge(
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    real_capture = policy_search._PrefixSnapshot.capture
    capabilities = _capabilities("intro", "refl")
    executed_commands: list[str] = []
    real_surface = policy_search.run_surface

    def corrupted_capture(cls, owner, *, commands, goals, capabilities):
        del cls
        snapshot = real_capture(
            owner,
            commands=commands,
            goals=goals,
            capabilities=capabilities,
        )
        if not commands:
            return snapshot
        if corruption == "target":
            return replace(snapshot, target=parse_formula("0 = 0"))
        if corruption == "source":
            return replace(snapshot, theorem_source="0 = 0")
        if corruption == "mode":
            return replace(snapshot, classical=True)
        if corruption == "authority":
            return replace(
                snapshot,
                capabilities=SurfaceCapabilities(
                    label="forged-prefix-authority",
                    allowed_commands=frozenset({"intro", "refl"}),
                    allowed_theorems=frozenset(),
                ),
            )
        if corruption == "commands":
            return replace(snapshot, commands=("intro forged",))
        return replace(snapshot, goals=("⊢ 0 = 0",))

    def observed_surface(owner, command, *, capabilities, record_trace):
        executed_commands.append(command)
        return real_surface(
            owner,
            command,
            capabilities=capabilities,
            record_trace=record_trace,
        )

    monkeypatch.setattr(
        policy_search._PrefixSnapshot,
        "capture",
        classmethod(corrupted_capture),
    )
    monkeypatch.setattr(policy_search, "run_surface", observed_surface)
    result = policy_search.search(
        "forall n. n = n",
        FunctionPolicy(
            lambda goals, limit: ("intro n",) if "∀" in goals[0] else ("refl",)
        ),
        capabilities=capabilities,
        limits=_limits(),
    )

    assert result.status == "exhausted"
    assert result.commands == ()
    assert result.certificate_nodes is None
    assert executed_commands == ["intro n"]
    assert result.candidates_executed == 2
    assert [item.kind for item in result.diagnostics] == ["replay_error"]
    assert "command 1" in result.diagnostics[0].message


@pytest.mark.parametrize("corruption", ("target", "trace"))
def test_successful_surface_cannot_replace_cached_branch_authority(
    monkeypatch: pytest.MonkeyPatch,
    corruption: str,
) -> None:
    real_surface = policy_search.run_surface

    def corrupted_surface(owner, command, *, capabilities, record_trace):
        next_owner = real_surface(
            owner,
            command,
            capabilities=capabilities,
            record_trace=record_trace,
        )
        if corruption == "target":
            return replace(next_owner, original_target=parse_formula("0 = 1"))
        return replace(
            next_owner,
            trace=policy_search.TraceLogger(session_id="forged-branch-trace"),
        )

    monkeypatch.setattr(policy_search, "run_surface", corrupted_surface)
    result = policy_search.search(
        "0 = 0",
        FunctionPolicy(lambda goals, limit: ("refl",)),
        capabilities=_capabilities("refl"),
        limits=_limits(),
    )

    assert result.status == "exhausted"
    assert result.commands == ()
    assert result.certificate_nodes is None
    assert [item.kind for item in result.diagnostics] == ["surface_error"]
    assert "branch authority" in result.diagnostics[0].message


@pytest.mark.parametrize("label", ("model-v1", "model-v2", "model-v3"))
def test_frozen_model_surfaces_cannot_inherit_modern_compact_literal_authority(
    label: str,
) -> None:
    capabilities = SurfaceCapabilities(
        label=label,
        allowed_commands=frozenset({"refl"}),
        allowed_theorems=frozenset(),
    )
    assert policy_search.numeral_limit_for_capabilities(capabilities) == (
        UNARY_NUMERAL_LIMIT
    )

    with pytest.raises(ValueError, match="257"):
        policy_search.search(
            "257 = 257",
            FunctionPolicy(lambda goals, limit: ("refl",)),
            capabilities=capabilities,
            limits=_limits(),
        )

    result = policy_search.search(
        "256 = 256",
        FunctionPolicy(lambda goals, limit: ("refl",)),
        capabilities=capabilities,
        limits=_limits(),
    )
    assert result.proved is True


def test_modern_policy_surface_accepts_compact_literals_up_to_its_current_limit() -> None:
    capabilities = _capabilities("refl")
    assert policy_search.numeral_limit_for_capabilities(capabilities) == MAX_NUMERAL

    result = policy_search.search(
        f"{MAX_NUMERAL} = {MAX_NUMERAL}",
        FunctionPolicy(lambda goals, limit: ("refl",)),
        capabilities=capabilities,
        limits=_limits(),
    )
    assert result.proved is True
    assert result.theorem == f"{MAX_NUMERAL} = {MAX_NUMERAL}"

    with pytest.raises(ValueError, match=str(MAX_NUMERAL + 1)):
        policy_search.search(
            f"{MAX_NUMERAL + 1} = {MAX_NUMERAL + 1}",
            FunctionPolicy(lambda goals, limit: ("refl",)),
            capabilities=capabilities,
            limits=_limits(),
        )


@pytest.mark.parametrize("label", ("model-v1", "model-v2", "model-v3"))
def test_frozen_model_candidate_cannot_smuggle_newer_compact_witness(label: str) -> None:
    capabilities = SurfaceCapabilities(
        label=label,
        allowed_commands=frozenset({"exists", "refl"}),
        allowed_theorems=frozenset(),
    )
    result = policy_search.search(
        "exists n. n = n",
        FunctionPolicy(
            lambda goals, limit: (
                ("exists 257", "exists 5") if "∃" in goals[0] else ("refl",)
            )
        ),
        capabilities=capabilities,
        limits=_limits(),
    )

    assert result.proved is True
    assert result.commands == ("exists 5", "refl")
    assert result.candidates_executed == 2
    assert [item.kind for item in result.diagnostics] == ["invalid_candidate"]
    assert "257" in result.diagnostics[0].message


def test_modern_policy_candidate_may_use_checked_compact_witness() -> None:
    result = policy_search.search(
        "exists n. n = n",
        FunctionPolicy(
            lambda goals, limit: (
                ("exists 257",) if "∃" in goals[0] else ("refl",)
            )
        ),
        capabilities=_capabilities("exists", "refl"),
        limits=_limits(),
    )

    assert result.proved is True
    assert result.commands == ("exists 257", "refl")


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
    assert result.status == "exhausted"
    assert result.diagnostics[0].kind == "policy_error"
    assert "\n" not in result.diagnostics[0].message

    with pytest.raises(ValueError, match="may not exceed"):
        policy_search.SearchLimits(max_depth=33)
    with pytest.raises(ValueError, match="positive integer"):
        policy_search.SearchLimits(beam_width=0)
    with pytest.raises(TypeError, match="capabilities"):
        policy_search.search("0 = 0", RaisingPolicy())  # type: ignore[call-arg]


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
