#!/usr/bin/env python3
"""Replay the complete public library through the real committed WASM shadow."""

from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import struct
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
PEANO_PYTHON = ROOT / "peano-lab" / "py"
if str(PEANO_PYTHON) not in sys.path:
    sys.path.insert(0, str(PEANO_PYTHON))

from peano_lab.engine.state import proof_metrics  # noqa: E402
from peano_lab.kernel.checker import check  # noqa: E402
from peano_lab.kernel.artifact_codec import encode_artifact_bounded  # noqa: E402
from peano_lab.kernel.formulas import Imp  # noqa: E402
from peano_lab.library import theorems  # noqa: E402


MAX_ARTIFACT_BYTES = 16 * 1024 * 1024
FUEL_MULTIPLIER = 8
FUEL_OFFSET = 16
RUNNER_SOURCE_PATHS = (
    "scripts/differential_peano_kernel_shadow_wasm.py",
    "scripts/wasm_shadow_batch_runner.js",
)
CASE_CONTRACT = (
    ("original", 1, "original target, proof, and computed positive fuel"),
    ("wrong_target", 2, "same proof against target (P → P)"),
    ("zero_fuel", 2, "original target and proof with fuel zero"),
    ("malformed", 3, "original artifact with its terminal LF removed"),
)


class WasmDifferentialError(RuntimeError):
    """The real WASM process violated the frozen differential contract."""


def _send(process: subprocess.Popen[bytes], artifact: bytes, expected: int) -> None:
    assert process.stdin is not None and process.stdout is not None
    process.stdin.write(struct.pack(">BI", 0, len(artifact)))
    process.stdin.write(artifact)
    process.stdin.flush()
    response = process.stdout.readline()
    if response != f"{expected}\n".encode("ascii"):
        raise WasmDifferentialError(
            f"WASM returned {response!r}, expected verdict {expected}"
        )


def validate(wasm: Path, node: str = "node") -> dict[str, object]:
    wasm_bytes = wasm.read_bytes()
    runner = ROOT / "scripts" / "wasm_shadow_batch_runner.js"
    process = subprocess.Popen(
        [node, str(runner), str(wasm)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    rows: list[dict[str, object]] = []
    original_hashes: list[str] = []
    case_hashes: list[str] = []
    try:
        for name in theorems.names():
            checked = theorems.replay(name)
            if not check((), checked.certificate, checked.formula):
                raise WasmDifferentialError(
                    f"Python rejected the original goal for {name!r}"
                )
            wrong_target = Imp(checked.formula, checked.formula)
            if check((), checked.certificate, wrong_target):
                raise WasmDifferentialError(
                    f"Python accepted the wrong goal for {name!r}"
                )
            nodes, depth = proof_metrics(checked.certificate)
            fuel = FUEL_MULTIPLIER * nodes + FUEL_OFFSET
            original = encode_artifact_bounded(
                fuel,
                checked.formula,
                checked.certificate,
                max_bytes=MAX_ARTIFACT_BYTES,
            )
            wrong = encode_artifact_bounded(
                fuel,
                wrong_target,
                checked.certificate,
                max_bytes=MAX_ARTIFACT_BYTES,
            )
            zero_fuel = encode_artifact_bounded(
                0,
                checked.formula,
                checked.certificate,
                max_bytes=MAX_ARTIFACT_BYTES,
            )
            malformed = original[:-1]
            artifacts = (original, wrong, zero_fuel, malformed)
            retained_cases: dict[str, dict[str, object]] = {}
            for (case_name, expected, _description), artifact in zip(
                CASE_CONTRACT, artifacts, strict=True
            ):
                _send(process, artifact, expected)
                case_digest = sha256(artifact).hexdigest()
                case_hashes.append(case_digest)
                retained_cases[case_name] = {
                    "artifact_bytes": len(artifact),
                    "artifact_sha256": case_digest,
                    "expected_verdict": expected,
                }
            digest = sha256(original).hexdigest()
            original_hashes.append(digest)
            rows.append(
                {
                    "artifact_bytes": len(original),
                    "artifact_sha256": digest,
                    "case_artifacts": retained_cases,
                    "name": name,
                    "proof_depth": depth,
                    "proof_nodes": nodes,
                }
            )
    finally:
        if process.stdin is not None:
            process.stdin.close()
    return_code = process.wait(timeout=60)
    assert process.stderr is not None
    stderr = process.stderr.read()
    if return_code != 0 or stderr:
        raise WasmDifferentialError(
            f"WASM batch runner failed with {return_code}: {stderr.decode('utf-8', 'replace')}"
        )

    receipt = sha256("\n".join(original_hashes).encode("ascii")).hexdigest()
    case_receipt = sha256("\n".join(case_hashes).encode("ascii")).hexdigest()
    return {
        "artifact_receipt_contract": (
            "sha256 of lowercase original-artifact SHA-256 values joined by LF "
            "in theorem order, without terminal LF"
        ),
        "artifact_receipt_sha256": receipt,
        "authority": {
            "qed": "authoritative-python-original-goal-only",
            "wasm": "diagnostic-only-never-grants-qed",
        },
        "case_contract": [
            {
                "expected_verdict": expected,
                "mutation": description,
                "name": name,
            }
            for name, expected, description in CASE_CONTRACT
        ],
        "case_receipt_contract": (
            "sha256 of lowercase per-case artifact SHA-256 values joined by LF "
            "in theorem order then case_contract order, without terminal LF"
        ),
        "case_receipt_sha256": case_receipt,
        "cases": len(rows) * len(CASE_CONTRACT),
        "format": "peano-kernel-browser-wasm-differential",
        "results": rows,
        "runner_sources": {
            path: sha256((ROOT / path).read_bytes()).hexdigest()
            for path in RUNNER_SOURCE_PATHS
        },
        "theorems": len(rows),
        "validation_passed": True,
        "version": 1,
        "wasm": {
            "bytes": len(wasm_bytes),
            "path": wasm.relative_to(ROOT).as_posix(),
            "sha256": sha256(wasm_bytes).hexdigest(),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--wasm",
        type=Path,
        default=ROOT / "peano-lab" / "peano_kernel_shadow.wasm",
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = validate(args.wasm.resolve())
    body = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        sys.stdout.write(body)
    else:
        args.output.write_text(body, encoding="utf-8")
        print(
            f"WASM differential: {report['theorems']} theorems, "
            f"{report['cases']} cases, receipt {report['artifact_receipt_sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
