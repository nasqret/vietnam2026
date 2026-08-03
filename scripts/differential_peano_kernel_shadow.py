#!/usr/bin/env python3
"""Differentially validate checked public theorems with the Rust shadow.

Python remains the only QED authority.  For each selected public theorem this
tool replays the library entry, independently checks its certificate against
the original closed goal with :mod:`peano_lab.kernel.checker`, serializes the
already-checked proof as canonical ``peano-lab-v2``, and asks a supplied Rust
CLI for an observational shadow verdict.

The shadow protocol is deliberately narrow.  The CLI reads exactly one
artifact from stdin.  A valid accepted artifact returns ``ACCEPT``/0, a valid
semantic or fuel rejection returns ``REJECT``/1, and a malformed artifact
returns empty stdout plus one ``ERROR: ...`` line/2.  Timeouts, process errors,
and every other response fail closed.  The report's wall-clock durations are
observations only and never participate in a theorem decision.
"""

from __future__ import annotations

import argparse
from collections.abc import Callable
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import subprocess
import sys
from time import perf_counter_ns


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.engine.state import proof_metrics  # noqa: E402
from peano_lab.kernel import checker as kernel_checker  # noqa: E402
from peano_lab.kernel.artifact_codec import encode_artifact  # noqa: E402
from peano_lab.kernel.formulas import Imp  # noqa: E402
from peano_lab.library import theorems as theorem_library  # noqa: E402


REPORT_FORMAT = "peano-kernel-shadow-differential"
REPORT_VERSION = 1
DEFAULT_THEOREM = "zero_add"
DEFAULT_TIMEOUT_SECONDS = 120.0
LEAN_DEFAULT_FUEL_MULTIPLIER = 8
LEAN_DEFAULT_FUEL_OFFSET = 16
RUST_SOURCE_ROOT = Path("peano-lab/rust/peano-kernel-shadow")
PYTHON_SOURCE_ROOT = Path("peano-lab/py/peano_lab")
IMPLEMENTATION_FIXED_PATHS = (
    Path("scripts/differential_peano_kernel_shadow.py"),
    RUST_SOURCE_ROOT / "Cargo.lock",
    RUST_SOURCE_ROOT / "Cargo.toml",
    RUST_SOURCE_ROOT / "rust-toolchain.toml",
)

Runner = Callable[..., subprocess.CompletedProcess[bytes]]


class DifferentialValidationError(RuntimeError):
    """The differential run could not establish its fail-closed contract."""


def lean_default_fuel(structural_proof_nodes: int) -> int:
    """Return Lean's frozen default artifact fuel for one certificate."""

    if type(structural_proof_nodes) is not int or structural_proof_nodes < 1:
        raise DifferentialValidationError(
            "structural proof nodes must be a positive integer"
        )
    return (
        LEAN_DEFAULT_FUEL_MULTIPLIER * structural_proof_nodes
        + LEAN_DEFAULT_FUEL_OFFSET
    )


def _artifact_record(artifact: bytes) -> dict[str, object]:
    return {
        "bytes": len(artifact),
        "sha256": sha256(artifact).hexdigest(),
    }


def _implementation_source_provenance() -> dict[str, object]:
    """Hash the exact Python/Rust sources needed to reproduce this report."""

    python_sources = (REPOSITORY_ROOT / PYTHON_SOURCE_ROOT).rglob("*.py")
    rust_sources = (REPOSITORY_ROOT / RUST_SOURCE_ROOT / "src").rglob("*.rs")
    paths = sorted(
        {
            *(REPOSITORY_ROOT / path for path in IMPLEMENTATION_FIXED_PATHS),
            *python_sources,
            *rust_sources,
        },
        key=lambda path: path.relative_to(REPOSITORY_ROOT).as_posix(),
    )
    records: list[dict[str, object]] = []
    manifest_lines: list[str] = []
    for path in paths:
        try:
            data = path.read_bytes()
            relative = path.relative_to(REPOSITORY_ROOT).as_posix()
        except (OSError, ValueError) as error:
            raise DifferentialValidationError(
                f"cannot hash implementation source {path}: {error}"
            ) from error
        digest = sha256(data).hexdigest()
        records.append({"bytes": len(data), "path": relative, "sha256": digest})
        manifest_lines.append(f"{digest}  {relative}\n")
    manifest = "".join(manifest_lines).encode("utf-8")
    return {
        "files": records,
        "manifest_contract": (
            "sha256 of UTF-8 '<file-sha256>  <repository-relative-path>\\n' "
            "lines in listed order"
        ),
        "manifest_sha256": sha256(manifest).hexdigest(),
    }


def _shadow_executable_sha256(rust_cli: str, runner: Runner) -> str | None:
    """Hash a real shadow executable; injected test runners are labeled null."""

    if runner is not subprocess.run:
        return None
    path = Path(rust_cli)
    try:
        if path.is_symlink() or not path.is_file():
            raise DifferentialValidationError(
                "Rust shadow CLI must be a regular non-symlink file"
            )
        return sha256(path.read_bytes()).hexdigest()
    except DifferentialValidationError:
        raise
    except OSError as error:
        raise DifferentialValidationError(
            f"cannot hash Rust shadow CLI {rust_cli!r}: {error}"
        ) from error


def _codec_error_stderr(stderr: bytes) -> bool:
    """Recognize exactly one concise Rust codec-error line."""

    return (
        stderr.startswith(b"ERROR: ")
        and stderr.endswith(b"\n")
        and stderr.count(b"\n") == 1
        and b"\r" not in stderr
    )


def _run_shadow_case(
    *,
    case: str,
    artifact: bytes,
    rust_cli: str,
    timeout_seconds: float,
    runner: Runner,
) -> dict[str, object]:
    """Run one exact CLI protocol case or fail closed."""

    started = perf_counter_ns()
    try:
        completed = runner(
            [rust_cli],
            input=artifact,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        raise DifferentialValidationError(
            f"Rust shadow timed out during {case!r} after {timeout_seconds:g}s"
        ) from error
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        raise DifferentialValidationError(
            f"Rust shadow process failed during {case!r}: {error}"
        ) from error
    duration_ns = perf_counter_ns() - started

    if (
        type(completed.returncode) is not int
        or type(completed.stdout) is not bytes
        or type(completed.stderr) is not bytes
    ):
        raise DifferentialValidationError(
            f"Rust shadow returned malformed process data during {case!r}"
        )

    expected: tuple[int, bytes, bytes | None, str]
    if case == "original":
        expected = (0, b"ACCEPT\n", b"", "accept")
    elif case in ("wrong_target", "zero_fuel"):
        expected = (1, b"REJECT\n", b"", "reject")
    elif case == "malformed_bytes":
        expected = (2, b"", None, "input_rejected")
    else:  # Defensive internal boundary: case names are part of report v1.
        raise DifferentialValidationError(f"unknown Rust shadow case {case!r}")

    expected_code, expected_stdout, expected_stderr, verdict = expected
    protocol_ok = (
        completed.returncode == expected_code
        and completed.stdout == expected_stdout
        and (
            completed.stderr == expected_stderr
            if expected_stderr is not None
            else _codec_error_stderr(completed.stderr)
        )
    )
    if not protocol_ok:
        raise DifferentialValidationError(
            "Rust shadow protocol mismatch during "
            f"{case!r}: exit={completed.returncode}, "
            f"stdout_sha256={sha256(completed.stdout).hexdigest()}, "
            f"stderr_sha256={sha256(completed.stderr).hexdigest()}"
        )

    return {
        "artifact": _artifact_record(artifact),
        "duration_ns": duration_ns,
        "exit_code": completed.returncode,
        "name": case,
        "rust_verdict": verdict,
    }


def _resolve_theorems(theorems: tuple[str, ...]) -> tuple[str, ...]:
    if type(theorems) is not tuple or not theorems:
        raise DifferentialValidationError("theorems must be a non-empty tuple")
    if not all(type(name) is str and name for name in theorems):
        raise DifferentialValidationError(
            "every theorem name must be a non-empty string"
        )
    if len(set(theorems)) != len(theorems):
        raise DifferentialValidationError("duplicate theorem names are not allowed")

    canonical: list[str] = []
    for requested in theorems:
        spec = theorem_library.get(requested)
        if spec is None:
            raise DifferentialValidationError(
                f"unknown public theorem {requested!r}"
            )
        canonical.append(spec.name)
    if len(set(canonical)) != len(canonical):
        raise DifferentialValidationError(
            "theorem names must not repeat through case-folded aliases"
        )
    return tuple(canonical)


def _validate_theorem(
    name: str,
    *,
    rust_cli: str,
    timeout_seconds: float,
    runner: Runner,
) -> dict[str, object]:
    started = perf_counter_ns()
    try:
        checked = theorem_library.replay(name)
    except theorem_library.LibraryError as error:
        raise DifferentialValidationError(
            f"public theorem replay failed for {name!r}: {error}"
        ) from error
    replay_duration_ns = perf_counter_ns() - started

    # This call is intentionally independent of library replay's own final
    # check and always uses the original stated goal, not replay_target().
    started = perf_counter_ns()
    python_original_accepted = kernel_checker.check(
        (), checked.certificate, checked.formula
    )
    python_original_duration_ns = perf_counter_ns() - started
    if not python_original_accepted:
        raise DifferentialValidationError(
            f"authoritative Python rejected original goal for {name!r}"
        )

    wrong_target = Imp(checked.formula, checked.formula)
    started = perf_counter_ns()
    python_wrong_target_accepted = kernel_checker.check(
        (), checked.certificate, wrong_target
    )
    python_wrong_target_duration_ns = perf_counter_ns() - started
    if python_wrong_target_accepted:
        raise DifferentialValidationError(
            f"authoritative Python accepted wrong target for {name!r}"
        )

    nodes, depth = proof_metrics(checked.certificate)
    if checked.proof_nodes != nodes:
        raise DifferentialValidationError(
            f"library and structural node counts disagree for {name!r}"
        )
    fuel = lean_default_fuel(nodes)

    started = perf_counter_ns()
    try:
        original_artifact = encode_artifact(
            fuel, checked.formula, checked.certificate
        )
        wrong_target_artifact = encode_artifact(
            fuel, wrong_target, checked.certificate
        )
        zero_fuel_artifact = encode_artifact(
            0, checked.formula, checked.certificate
        )
    except (TypeError, ValueError) as error:
        raise DifferentialValidationError(
            f"canonical artifact encoding failed for {name!r}: {error}"
        ) from error
    # Removing the mandatory terminal LF preserves the entire canonical body
    # while producing a precise strict-codec negative.
    malformed_artifact = original_artifact[:-1]
    encoding_duration_ns = perf_counter_ns() - started
    if not original_artifact.endswith(b"\n") or malformed_artifact.endswith(b"\n"):
        raise DifferentialValidationError("artifact newline mutation was not exact")

    case_inputs = (
        ("original", "accept", "accept", original_artifact),
        ("wrong_target", "reject", "reject", wrong_target_artifact),
        # Fuel belongs only to the bounded shadow envelope.  The authoritative
        # Python judgment still accepts this target/proof pair independently.
        ("zero_fuel", "accept", "reject", zero_fuel_artifact),
        ("malformed_bytes", "not_applicable", "input_rejected", malformed_artifact),
    )
    rust_cases: list[dict[str, object]] = []
    for case, python_verdict, expected_rust_verdict, artifact in case_inputs:
        result = _run_shadow_case(
            case=case,
            artifact=artifact,
            rust_cli=rust_cli,
            timeout_seconds=timeout_seconds,
            runner=runner,
        )
        result["expected_rust_verdict"] = expected_rust_verdict
        result["python_verdict"] = python_verdict
        rust_cases.append(result)

    return {
        "certificate": {
            "canonical_artifact_bytes": len(original_artifact),
            "canonical_artifact_sha256": sha256(original_artifact).hexdigest(),
            "lean_default_fuel": fuel,
            "proof_depth": depth,
            "structural_proof_nodes": nodes,
        },
        "phases": {
            "artifact_encoding_duration_ns": encoding_duration_ns,
            "library_replay_duration_ns": replay_duration_ns,
        },
        "python": {
            "original_goal": {
                "duration_ns": python_original_duration_ns,
                "verdict": "accept",
            },
            "wrong_target": {
                "duration_ns": python_wrong_target_duration_ns,
                "verdict": "reject",
            },
        },
        "rust_cases": rust_cases,
        "theorem": {
            "name": checked.spec.name,
            "statement": checked.spec.statement,
        },
    }


def validate_shadow(
    theorems: tuple[str, ...],
    rust_cli: str | os.PathLike[str],
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    runner: Runner = subprocess.run,
    selection_mode: str = "named",
) -> dict[str, object]:
    """Return a v1 differential report or raise on any failed contract.

    ``runner`` is injectable solely to keep focused protocol tests quick.  A
    production call should retain the default :func:`subprocess.run`.
    """

    names = _resolve_theorems(theorems)
    try:
        cli = os.fspath(rust_cli)
    except TypeError as error:
        raise DifferentialValidationError("Rust CLI path must be path-like") from error
    if type(cli) is not str or not cli:
        raise DifferentialValidationError("Rust CLI path must be non-empty")
    if (
        isinstance(timeout_seconds, bool)
        or not isinstance(timeout_seconds, (int, float))
        or not math.isfinite(timeout_seconds)
        or timeout_seconds <= 0
    ):
        raise DifferentialValidationError(
            "timeout seconds must be a positive finite number"
        )
    if selection_mode not in ("all", "default", "named"):
        raise DifferentialValidationError("invalid theorem selection mode")

    source_provenance = _implementation_source_provenance()
    executable_sha256 = _shadow_executable_sha256(cli, runner)
    rows = [
        _validate_theorem(
            name,
            rust_cli=cli,
            timeout_seconds=float(timeout_seconds),
            runner=runner,
        )
        for name in names
    ]
    artifact_hashes = [
        str(row["certificate"]["canonical_artifact_sha256"])
        for row in rows
    ]
    artifact_receipt_preimage = "\n".join(artifact_hashes).encode("utf-8")
    return {
        "artifact_set": {
            "receipt_contract": (
                "sha256 of lowercase canonical-artifact SHA-256 values joined "
                "by LF in selection.names order, without a terminal LF"
            ),
            "receipt_sha256": sha256(artifact_receipt_preimage).hexdigest(),
            "theorem_count": len(rows),
        },
        "authority": {
            "qed": "authoritative-python-original-goal-only",
            "python_checker": "peano_lab.kernel.checker.check",
            "rust_checker": "shadow-only-never-grants-qed",
        },
        "format": REPORT_FORMAT,
        "implementation_sources": source_provenance,
        "results": rows,
        "selection": {
            "mode": selection_mode,
            "names": list(names),
            "theorem_count": len(names),
        },
        "shadow_cli": {
            "executable_sha256": executable_sha256,
            "path": cli,
            "protocol": "stdin-one-peano-lab-v2-artifact",
            "timeout_seconds": float(timeout_seconds),
        },
        "timer": {
            "clock": "time.perf_counter_ns",
            "interpretation": "observational-only-no-pass-fail-threshold",
            "unit": "nanoseconds",
        },
        "validation_passed": True,
        "version": REPORT_VERSION,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument(
        "--theorem",
        action="append",
        dest="theorems",
        metavar="NAME",
        help=(
            "public theorem to validate; repeat for multiple names "
            f"(default: {DEFAULT_THEOREM})"
        ),
    )
    selection.add_argument(
        "--all",
        action="store_true",
        help="validate every public theorem in dependency order",
    )
    parser.add_argument(
        "--rust-cli",
        required=True,
        metavar="PATH",
        help="path to the built peano-kernel-shadow executable",
    )
    parser.add_argument(
        "--timeout-seconds",
        default=DEFAULT_TIMEOUT_SECONDS,
        type=float,
        metavar="SECONDS",
        help=f"per-invocation timeout (default: {DEFAULT_TIMEOUT_SECONDS:g})",
    )
    parser.add_argument(
        "--output",
        type=Path,
        metavar="PATH",
        help="write the complete canonical JSON report to PATH",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.all:
        names = theorem_library.names()
        selection_mode = "all"
    elif args.theorems:
        names = tuple(args.theorems)
        selection_mode = "named"
    else:
        names = (DEFAULT_THEOREM,)
        selection_mode = "default"

    try:
        payload = validate_shadow(
            names,
            args.rust_cli,
            timeout_seconds=args.timeout_seconds,
            selection_mode=selection_mode,
        )
    except DifferentialValidationError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 1
    rendered = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(rendered, end="")
    else:
        try:
            args.output.write_text(rendered, encoding="utf-8")
        except OSError as error:
            print(f"ERROR: cannot write report {args.output}: {error}", file=sys.stderr)
            return 1
        print(
            f"wrote {payload['selection']['theorem_count']} theorem rows to "
            f"{args.output}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
