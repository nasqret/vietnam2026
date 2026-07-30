"""Focused model-free tests for live policy/search event plumbing."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
from training.peano_policy.contract import model_v2_environment  # noqa: E402
from training.peano_policy.events import EVENT_FIELDS  # noqa: E402
from training.peano_policy.generate import (  # noqa: E402
    PeanoPolicyAdapter,
    PeanoPolicyCandidateAdapter,
)
from training.peano_policy.prompt import render_prompt  # noqa: E402
from training.peano_policy.search import SearchLimits, search  # noqa: E402


def _base_adapter() -> PeanoPolicyAdapter:
    return PeanoPolicyAdapter(
        model=None,
        tokenizer=None,
        environment=model_v2_environment(),
        name="event-unit-policy",
        max_new_tokens=19,
        do_sample=False,
        temperature=0.7,
        top_p=0.9,
        provenance={"weights": "unit"},
    )


def test_candidate_adapter_reports_exact_prompt_raw_output_and_fresh_seed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records: list[dict[str, object]] = []
    fresh_records: list[dict[str, object]] = []
    calls: list[dict[str, object]] = []

    def fake_generate(**kwargs: object) -> tuple[str, ...]:
        calls.append(kwargs)
        active = records if len(calls) == 1 else fresh_records
        assert [record["kind"] for record in active] == ["model_prompt"]
        return ("refl</tactic>", "refl")

    monkeypatch.setattr(
        "training.peano_policy.generate.generate_tactic_candidates",
        fake_generate,
    )
    candidate = PeanoPolicyCandidateAdapter(
        _base_adapter(),
        seed=41,
        on_event=records.append,
    )
    goals = ("⊢ 0 = 0",)

    assert candidate.propose(goals, max_candidates=2) == ("refl",)
    assert [record["kind"] for record in records] == [
        "model_prompt",
        "model_output",
    ]
    prompt = records[0]
    assert prompt["prompt"] == render_prompt(
        goals=goals,
        focus=0,
        environment=candidate.adapter.environment,
    )
    assert prompt["prompt_chars"] == len(prompt["prompt"])  # type: ignore[arg-type]
    assert prompt["requested_candidates"] == 2
    output = records[1]
    assert output["raw_candidates"] == ("refl</tactic>", "refl")
    assert output["candidates"] == ("refl",)
    assert output["rejections"] == (
        {"rank": 0, "message": "tactic contains a reserved prompt marker"},
    )
    for record in records:
        assert tuple(record)[2:] == EVENT_FIELDS[record["kind"]]  # type: ignore[index]

    fresh = candidate.fresh(on_event=fresh_records.append)
    assert fresh.adapter is candidate.adapter
    assert fresh.generation_calls == 0
    assert fresh.generation_provenance["candidate_sequences_requested"] == 0
    assert fresh.propose(goals, max_candidates=2) == ("refl",)
    assert calls[0]["seed"] == calls[1]["seed"]
    assert fresh_records[0]["model_call"] == 1
    assert candidate.generation_calls == fresh.generation_calls == 1


def test_search_uses_optional_eventful_protocol_without_changing_legacy_propose(
) -> None:
    class EventfulPolicy:
        def __init__(self) -> None:
            self.eventful_calls = 0

        def propose(self, goals_before, *, max_candidates):
            del goals_before, max_candidates
            raise AssertionError("observed search must use propose_with_events")

        def propose_with_events(
            self, goals_before, *, max_candidates, on_event
        ):
            del on_event
            assert goals_before == ("⊢ 0 = 0",)
            assert max_candidates == 1
            self.eventful_calls += 1
            return ("refl",)

    policy = EventfulPolicy()
    records: list[dict[str, object]] = []
    result = search(
        "0 = 0",
        policy,
        capabilities=SurfaceCapabilities(
            label="event-test",
            allowed_commands=frozenset({"refl"}),
            allowed_theorems=frozenset(),
        ),
        limits=SearchLimits(
            max_depth=1,
            beam_width=1,
            candidates_per_state=1,
            max_model_calls=1,
            max_states=1,
        ),
        on_event=records.append,
    )

    assert result.status == "proof"
    assert policy.eventful_calls == 1
    assert records[1]["kind"] == "state_selected"
    assert records[2]["kind"] == "proposal_received"
