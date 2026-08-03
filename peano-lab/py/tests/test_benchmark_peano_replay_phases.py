"""Focused contracts for the observational replay-phase benchmark."""

from __future__ import annotations

import json
from pathlib import Path
from runpy import run_path

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = run_path(str(ROOT / "scripts" / "benchmark_peano_replay_phases.py"))
benchmark = SCRIPT["benchmark"]
main = SCRIPT["main"]
kernel_checker = SCRIPT["kernel_checker"]
ReplayBenchmarkError = SCRIPT["ReplayBenchmarkError"]


def _without_wall_time(value):
    if isinstance(value, dict):
        return {
            key: _without_wall_time(item)
            for key, item in value.items()
            if key != "duration_ns"
        }
    if isinstance(value, list):
        return [_without_wall_time(item) for item in value]
    return value


def test_quick_default_has_stable_schema_and_one_final_checker_call(
    monkeypatch,
) -> None:
    calls = 0
    original = kernel_checker.check

    def recording_check(context, proof, target):
        nonlocal calls
        calls += 1
        return original(context, proof, target)

    monkeypatch.setattr(kernel_checker, "check", recording_check)
    payload = benchmark()

    assert payload["format"] == "peano-replay-phase-benchmark"
    assert payload["version"] == 1
    assert payload["timer"] == {
        "clock": "time.perf_counter_ns",
        "interpretation": "observational-only-no-pass-fail-threshold",
        "unit": "nanoseconds",
    }
    assert payload["library"]["theorem_count"] > 0
    assert len(payload["benchmarks"]) == 1
    row = payload["benchmarks"][0]
    assert row["theorem"]["name"] == "zero_add"
    assert row["kernel_accepted"] is True
    assert calls == 1
    assert [phase["name"] for phase in row["phases"]] == [
        "cold_library_replay",
        "final_kernel_check",
        "certificate_diagnostics",
    ]
    assert all(
        type(phase["duration_ns"]) is int and phase["duration_ns"] >= 0
        for phase in row["phases"]
    )
    certificate = row["certificate"]
    assert certificate["proof_nodes"] >= certificate["distinct_proof_objects"] > 0
    assert certificate["proof_depth"] > 0
    assert certificate["dne_occurrences"] == 0
    assert len(certificate["sha256"]) == 64


def test_report_is_deterministic_after_wall_times_are_removed() -> None:
    first = benchmark(("zero_add",))
    second = benchmark(("zero_add",))

    assert _without_wall_time(first) == _without_wall_time(second)


def test_json_cli_accepts_repeated_named_theorems(capsys) -> None:
    assert main(
        [
            "--theorem",
            "succ_ne_zero",
            "--theorem",
            "zero_add",
            "--json",
        ]
    ) == 0
    payload = json.loads(capsys.readouterr().out)

    assert [row["theorem"]["name"] for row in payload["benchmarks"]] == [
        "succ_ne_zero",
        "zero_add",
    ]


def test_unknown_or_empty_theorem_requests_fail_closed() -> None:
    with pytest.raises(ReplayBenchmarkError, match="unknown checked theorem"):
        benchmark(("not_a_checked_theorem",))
    with pytest.raises(ReplayBenchmarkError, match="non-empty tuple"):
        benchmark(())
