#!/usr/bin/env python3
"""Measure deterministic Peano replay phases without imposing time limits.

The harness clears the in-process library caches before each requested
theorem, measures its ordinary library replay, performs one additional kernel
check against the original formula, and then measures certificate diagnostics
(resource metrics, constructor counts, and a reproducibility digest).
Durations are observations for comparing environments; they are never pass or
fail thresholds and grant no theorem authority beyond the ordinary checker.
"""

from __future__ import annotations

import argparse
from dataclasses import fields
from hashlib import sha256
import json
import os
from pathlib import Path
import platform
import sys
from time import perf_counter_ns


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.engine.state import proof_resource_metrics  # noqa: E402
from peano_lab.kernel import checker as kernel_checker  # noqa: E402
from peano_lab.kernel.proofs import Cut, DNE, Proof  # noqa: E402
from peano_lab.library import theorems as theorem_library  # noqa: E402


BENCHMARK_FORMAT = "peano-replay-phase-benchmark"
BENCHMARK_VERSION = 1
DEFAULT_THEOREM = "zero_add"
PHASE_NAMES = (
    "cold_library_replay",
    "final_kernel_check",
    "certificate_diagnostics",
)


class ReplayBenchmarkError(ValueError):
    """A requested benchmark cannot produce a checked measurement."""


def _proof_constructor_counts(proof: Proof) -> tuple[int, int]:
    """Count structural Cut and DNE occurrences without using recursion."""

    pending = [proof]
    cuts = 0
    dne = 0
    while pending:
        node = pending.pop()
        cuts += type(node) is Cut
        dne += type(node) is DNE
        pending.extend(
            child
            for item in fields(node)
            if isinstance((child := getattr(node, item.name)), Proof)
        )
    return cuts, dne


def _environment() -> dict[str, object]:
    return {
        "cpu_count": os.cpu_count(),
        "machine": platform.machine(),
        "platform_release": platform.release(),
        "platform_system": platform.system(),
        "python_compiler": platform.python_compiler(),
        "python_implementation": platform.python_implementation(),
        "python_optimize": sys.flags.optimize,
        "python_version": platform.python_version(),
    }


def _benchmark_theorem(name: str) -> dict[str, object]:
    spec = theorem_library.get(name)
    if spec is None:
        raise ReplayBenchmarkError(f"unknown checked theorem {name!r}")

    # This is an in-process cold replay: imported modules remain resident, but
    # both caches that can reuse library specifications or checked certificates
    # are explicitly reset before the clock starts.
    theorem_library.replay.cache_clear()
    theorem_library._specs_by_name.cache_clear()
    started = perf_counter_ns()
    checked = theorem_library.replay(spec.name)
    replay_duration = perf_counter_ns() - started

    started = perf_counter_ns()
    accepted = kernel_checker.check((), checked.certificate, checked.formula)
    checker_duration = perf_counter_ns() - started
    if not accepted:
        raise ReplayBenchmarkError(
            f"final kernel check rejected replayed theorem {spec.name!r}"
        )

    started = perf_counter_ns()
    nodes, depth, objects, edges, reused = proof_resource_metrics(
        checked.certificate
    )
    cut_occurrences, dne_occurrences = _proof_constructor_counts(
        checked.certificate
    )
    certificate_sha256 = sha256(
        repr(checked.certificate).encode("utf-8")
    ).hexdigest()
    metrics_duration = perf_counter_ns() - started

    return {
        "certificate": {
            "cut_occurrences": cut_occurrences,
            "dne_occurrences": dne_occurrences,
            "proof_depth": depth,
            "proof_edges": edges,
            "proof_nodes": nodes,
            "reused_proof_references": reused,
            "sha256": certificate_sha256,
            "distinct_proof_objects": objects,
        },
        "kernel_accepted": accepted,
        "phases": [
            {
                "duration_ns": replay_duration,
                "name": PHASE_NAMES[0],
            },
            {
                "duration_ns": checker_duration,
                "name": PHASE_NAMES[1],
            },
            {
                "duration_ns": metrics_duration,
                "name": PHASE_NAMES[2],
            },
        ],
        "theorem": {
            "dependency_count": len(spec.dependencies),
            "name": spec.name,
            "script_command_count": len(spec.script),
            "statement": spec.statement,
            "statement_sha256": sha256(spec.statement.encode("utf-8")).hexdigest(),
        },
    }


def benchmark(theorems: tuple[str, ...] = (DEFAULT_THEOREM,)) -> dict[str, object]:
    """Return a deterministic-schema report for one or more theorem names."""

    if type(theorems) is not tuple or not theorems:
        raise ReplayBenchmarkError("theorems must be a non-empty tuple")
    if not all(type(name) is str and name for name in theorems):
        raise ReplayBenchmarkError("every theorem name must be a non-empty string")

    return {
        "benchmarks": [_benchmark_theorem(name) for name in theorems],
        "environment": _environment(),
        "format": BENCHMARK_FORMAT,
        "library": {
            "cold_replay_definition": (
                "replay and theorem-spec caches cleared; imports retained"
            ),
            "theorem_count": len(theorem_library.THEOREMS),
        },
        "timer": {
            "clock": "time.perf_counter_ns",
            "interpretation": "observational-only-no-pass-fail-threshold",
            "unit": "nanoseconds",
        },
        "version": BENCHMARK_VERSION,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--theorem",
        action="append",
        dest="theorems",
        metavar="NAME",
        help=(
            "checked theorem to benchmark; repeat for multiple theorems "
            f"(default: {DEFAULT_THEOREM})"
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="emit sorted, indented JSON instead of the compact text report",
    )
    return parser


def _text_report(payload: dict[str, object]) -> str:
    environment = payload["environment"]
    assert isinstance(environment, dict)
    lines = [
        "Peano replay phase benchmark",
        (
            f"environment={environment['python_implementation']} "
            f"{environment['python_version']} "
            f"{environment['platform_system']}/{environment['machine']}"
        ),
        "timing=observational only; no pass/fail threshold",
    ]
    rows = payload["benchmarks"]
    assert isinstance(rows, list)
    for row in rows:
        assert isinstance(row, dict)
        theorem = row["theorem"]
        certificate = row["certificate"]
        phases = row["phases"]
        assert isinstance(theorem, dict)
        assert isinstance(certificate, dict)
        assert isinstance(phases, list)
        lines.append(
            f"theorem={theorem['name']} accepted={str(row['kernel_accepted']).lower()} "
            f"nodes={certificate['proof_nodes']} depth={certificate['proof_depth']} "
            f"objects={certificate['distinct_proof_objects']}"
        )
        for phase in phases:
            assert isinstance(phase, dict)
            seconds = int(phase["duration_ns"]) / 1_000_000_000
            lines.append(f"  {phase['name']}={seconds:.9f}s")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    names = tuple(args.theorems or (DEFAULT_THEOREM,))
    try:
        payload = benchmark(names)
    except ReplayBenchmarkError as exc:
        parser.error(str(exc))
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(_text_report(payload))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
