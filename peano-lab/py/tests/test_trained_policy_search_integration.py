"""Model-free integration tests for trained-policy kernel-guided search."""

from __future__ import annotations

from contextlib import nullcontext
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = REPOSITORY_ROOT / "scripts" / "eval_trained_peano_policy.py"
SPEC = importlib.util.spec_from_file_location("_trained_policy_search_cli", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
CLI = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CLI
SPEC.loader.exec_module(CLI)

from training.peano_policy.contract import model_v2_environment  # noqa: E402
from training.peano_policy.generate import (  # noqa: E402
    PeanoPolicyAdapter,
    PeanoPolicyCandidateAdapter,
    generate_tactic_candidates,
)
from training.peano_policy.prompt import render_prompt  # noqa: E402
from training.peano_policy.search import SearchLimits  # noqa: E402


def _adapter(*, sample: bool = True) -> PeanoPolicyAdapter:
    return PeanoPolicyAdapter(
        model=None,
        tokenizer=None,
        environment=model_v2_environment(),
        name="unit-model-v2",
        max_new_tokens=17,
        do_sample=sample,
        temperature=0.7,
        top_p=0.9,
        provenance={"weights": "unit"},
    )


def test_candidate_adapter_batches_once_and_records_exact_seeded_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, object]] = []

    def fake_generate(**kwargs: object) -> tuple[str, ...]:
        calls.append(kwargs)
        return ("left", "refl", "refl")

    monkeypatch.setattr(
        "training.peano_policy.generate.generate_tactic_candidates",
        fake_generate,
    )
    goals = ("⊢ 0 = 0",)
    first = PeanoPolicyCandidateAdapter(_adapter(), seed=41)
    second = PeanoPolicyCandidateAdapter(_adapter(), seed=41)

    assert first.propose(goals, max_candidates=3) == ("left", "refl", "refl")
    assert second.propose(goals, max_candidates=3) == ("left", "refl", "refl")
    assert len(calls) == 2
    assert calls[0]["seed"] == calls[1]["seed"]
    assert calls[0]["max_candidates"] == 3
    assert calls[0]["max_new_tokens"] == 17
    assert calls[0]["do_sample"] is True
    assert calls[0]["temperature"] == 0.7
    assert calls[0]["top_p"] == 0.9
    assert first.generation_provenance == {
        "model_generate_calls": 1,
        "candidate_sequences_requested": 3,
        "candidate_sequences_returned": 3,
        "candidate_lines_returned": 3,
        "malformed_sequences_rejected": 0,
        "one_batched_call_per_search_state": True,
    }


def test_candidate_adapter_discards_envelopes_and_multiline_output_without_repair(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "training.peano_policy.generate.generate_tactic_candidates",
        lambda **kwargs: ("refl</tactic>", "refl\nqed", "refl"),
    )
    candidate = PeanoPolicyCandidateAdapter(_adapter(), seed=42)

    assert candidate.propose(("⊢ 0 = 0",), max_candidates=3) == ("refl",)
    assert candidate.generation_provenance["malformed_sequences_rejected"] == 2
    assert candidate.generation_provenance["candidate_lines_returned"] == 1


def test_low_level_candidate_generation_is_one_physical_model_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    seeds: list[int] = []
    fake_torch = SimpleNamespace(
        manual_seed=seeds.append,
        cuda=SimpleNamespace(is_available=lambda: False),
        inference_mode=nullcontext,
    )
    monkeypatch.setitem(sys.modules, "torch", fake_torch)

    class Tensor:
        shape = (1, 3)

        def to(self, device: str) -> "Tensor":
            assert device == "unit-device"
            return self

    class Output:
        def __len__(self) -> int:
            return 3

        def __getitem__(self, key: object) -> str:
            index, suffix = key  # type: ignore[misc]
            assert suffix == slice(3, None, None)
            return f"decoded-{index}"

    class Tokenizer:
        eos_token_id = 1
        pad_token_id = 1

        def __call__(self, text: str, **kwargs: object) -> dict[str, Tensor]:
            assert text == prompt
            assert kwargs == {"add_special_tokens": False, "return_tensors": "pt"}
            return {"input_ids": Tensor()}

        def decode(self, value: str, **kwargs: object) -> str:
            assert kwargs == {
                "skip_special_tokens": True,
                "clean_up_tokenization_spaces": False,
            }
            return value

    class Model:
        device = "unit-device"

        def __init__(self) -> None:
            self.calls: list[dict[str, object]] = []

        def generate(self, **kwargs: object) -> Output:
            self.calls.append(kwargs)
            return Output()

    environment = model_v2_environment()
    prompt = render_prompt(goals=("⊢ 0 = 0",), focus=0, environment=environment)
    model = Model()
    result = generate_tactic_candidates(
        model=model,
        tokenizer=Tokenizer(),
        prompt=prompt,
        environment=environment,
        max_candidates=3,
        seed=19,
        do_sample=False,
    )

    assert result == ("decoded-0", "decoded-1", "decoded-2")
    assert seeds == [19]
    assert len(model.calls) == 1
    assert model.calls[0]["num_return_sequences"] == 3
    assert model.calls[0]["num_beams"] == 3


class _ScriptedCandidatePolicy:
    def __init__(self, adapter: PeanoPolicyAdapter, *, seed: int, name: str) -> None:
        del adapter, name
        self.seed = seed
        self.calls = 0
        self.requested = 0
        self.returned = 0

    @property
    def generation_provenance(self) -> dict[str, object]:
        return {
            "model_generate_calls": self.calls,
            "candidate_sequences_requested": self.requested,
            "candidate_sequences_returned": self.returned,
            "candidate_lines_returned": self.returned,
            "malformed_sequences_rejected": 0,
            "one_batched_call_per_search_state": True,
        }

    def propose(
        self, goals_before: tuple[str, ...], *, max_candidates: int
    ) -> tuple[str, ...]:
        del goals_before
        self.calls += 1
        self.requested += max_candidates
        values = ("left", "refl")[:max_candidates]
        self.returned += len(values)
        return values


def test_search_evaluation_retries_a_failed_candidate_and_republishes_via_kernel(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(CLI, "PeanoPolicyCandidateAdapter", _ScriptedCandidatePolicy)
    adapter = _adapter(sample=False)
    goal = CLI._user_goal("0 = 0", adapter.environment)
    limits = SearchLimits(
        max_depth=4,
        beam_width=2,
        candidates_per_state=2,
        max_model_calls=8,
        max_states=8,
    )

    report, search_record = CLI._evaluate_kernel_search(
        adapter,
        (goal,),
        seed=7,
        limits=limits,
    )

    assert report.proved_goals == 1
    assert report.goals[0].attempts[0].commands == ("refl",)
    assert search_record["actual"] == {
        "model_generate_calls": 1,
        "states_expanded": 1,
        "states_discovered": 1,
        "candidates_executed": 2,
        "candidate_sequences_requested": 2,
        "candidate_sequences_returned": 2,
        "candidate_lines_returned": 2,
        "malformed_sequences_rejected": 0,
        "frontier_peak_per_goal": 1,
    }
    publication, script = CLI._checked_proof_publication(report)
    assert publication["status"] == "proof"
    assert publication["replay"]["kernel_checked"] is True
    assert script == "pa prove 0 = 0\nrefl\nqed\n"


class _HostileCandidatePolicy(_ScriptedCandidatePolicy):
    def propose(
        self, goals_before: tuple[str, ...], *, max_candidates: int
    ) -> tuple[str, ...]:
        del goals_before
        self.calls += 1
        self.requested += max_candidates
        # The stored dataset envelope uses ``</tactic>``, but supervision strips
        # it before tokenization.  If a decoder nevertheless invents that suffix
        # (or a second line), search must reject the branch rather than repair it.
        values = ("refl</tactic>", "refl\nqed")[:max_candidates]
        self.returned += len(values)
        return values


def test_malformed_search_outputs_never_become_a_publication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(CLI, "PeanoPolicyCandidateAdapter", _HostileCandidatePolicy)
    adapter = _adapter()
    goal = CLI._user_goal("0 = 0", adapter.environment)
    report, record = CLI._evaluate_kernel_search(
        adapter,
        (goal,),
        seed=8,
        limits=SearchLimits(
            max_depth=2,
            beam_width=2,
            candidates_per_state=2,
            max_model_calls=4,
            max_states=4,
        ),
    )

    assert report.proved_goals == 0
    assert report.goals[0].attempts[0].status == "failing"
    assert record["goals"][0]["result"]["status"] == "exhausted"  # type: ignore[index]
    publication, script = CLI._checked_proof_publication(report)
    assert publication == {"status": "no-proof"}
    assert script is None


@pytest.mark.parametrize(
    "arguments",
    (
        ("--mode", "search", "--k", "2"),
        ("--mode", "search", "--max-steps", "33"),
        ("--mode", "search", "--search-candidates-per-state", "65"),
        ("--mode", "search", "--search-max-states", "4097"),
    ),
)
def test_search_bounds_fail_before_adapter_loading(
    arguments: tuple[str, ...],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        CLI,
        "load_adapter",
        lambda *args, **kwargs: pytest.fail("adapter must not load"),
    )
    with pytest.raises(SystemExit) as rejected:
        CLI.main(
            ["--adapter", "missing", "--theorem", "0 = 0", *arguments]
        )
    assert rejected.value.code == 2
