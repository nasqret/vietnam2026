"""The retained K4 evidence must describe the exact committed browser bytes."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "artifacts" / "peano-kernel" / "browser-wasm-v1.json"
DIFFERENTIAL = (
    ROOT / "artifacts" / "peano-kernel" / "browser-wasm-differential-v1.json"
)
WASM = ROOT / "peano-lab" / "peano_kernel_shadow.wasm"
MANIFEST = ROOT / "peano-lab" / "APP_MANIFEST.sha256"
INDEX = (ROOT / "peano-lab" / "index.html").read_text(encoding="utf-8")


def test_browser_wasm_evidence_binds_exact_module_and_release() -> None:
    report = json.loads(REPORT.read_bytes())
    wasm = WASM.read_bytes()
    manifest = MANIFEST.read_bytes()

    assert report["format"] == "peano-kernel-browser-wasm-evidence"
    assert report["version"] == 1
    assert report["authority"] == {
        "qed": "authoritative-python-original-goal-only",
        "shadow": "diagnostic-only-never-grants-or-retracts-qed",
    }
    assert report["wasm"]["bytes"] == len(wasm)
    assert report["wasm"]["sha256"] == sha256(wasm).hexdigest()
    assert report["wasm"]["imports"] == []
    assert report["wasm"]["shared_memory"] is False
    assert str(ROOT).encode() not in wasm
    assert b"/peano-lab-src/peano-lab/rust/peano-kernel-shadow/" in wasm
    assert report["release"]["application_manifest_sha256"] == sha256(
        manifest
    ).hexdigest()
    assert report["release"]["application_manifest_entries"] == len(
        manifest.splitlines()
    )
    assert report["release"]["deployed"] is False
    app_id = re.search(r'const APP_ROOT="releases/(a-[0-9a-f]{12})/"', INDEX)
    build = re.search(r'const BUILD="([^"]+)"', INDEX)
    assert app_id is not None and build is not None
    assert report["release"]["application_id"] == app_id.group(1)
    assert report["release"]["build"] == build.group(1)

    differential_bytes = DIFFERENTIAL.read_bytes()
    differential = json.loads(differential_bytes)
    retained = report["validation"]["complete_differential"]
    assert retained["file_sha256"] == sha256(differential_bytes).hexdigest()
    assert retained["theorems"] == differential["theorems"] == 384
    assert retained["cases"] == differential["cases"] == 1_536
    assert retained["artifact_receipt_sha256"] == differential[
        "artifact_receipt_sha256"
    ]
    assert retained["case_receipt_sha256"] == differential["case_receipt_sha256"]
    assert differential["validation_passed"] is True
    assert differential["case_contract"] == [
        {
            "expected_verdict": 1,
            "mutation": "original target, proof, and computed positive fuel",
            "name": "original",
        },
        {
            "expected_verdict": 2,
            "mutation": "same proof against target (P → P)",
            "name": "wrong_target",
        },
        {
            "expected_verdict": 2,
            "mutation": "original target and proof with fuel zero",
            "name": "zero_fuel",
        },
        {
            "expected_verdict": 3,
            "mutation": "original artifact with its terminal LF removed",
            "name": "malformed",
        },
    ]
    assert differential["runner_sources"] == {
        path: sha256((ROOT / path).read_bytes()).hexdigest()
        for path in (
            "scripts/differential_peano_kernel_shadow_wasm.py",
            "scripts/wasm_shadow_batch_runner.js",
        )
    }
    assert len(differential["results"]) == differential["theorems"]
    original_hashes = [row["artifact_sha256"] for row in differential["results"]]
    assert differential["artifact_receipt_sha256"] == sha256(
        "\n".join(original_hashes).encode("ascii")
    ).hexdigest()
    case_names = [case["name"] for case in differential["case_contract"]]
    case_hashes = [
        row["case_artifacts"][name]["artifact_sha256"]
        for row in differential["results"]
        for name in case_names
    ]
    assert differential["case_receipt_sha256"] == sha256(
        "\n".join(case_hashes).encode("ascii")
    ).hexdigest()
    for row in differential["results"]:
        assert row["case_artifacts"]["original"]["artifact_sha256"] == row[
            "artifact_sha256"
        ]
        assert row["case_artifacts"]["original"]["artifact_bytes"] == row[
            "artifact_bytes"
        ]
        assert [
            row["case_artifacts"][name]["expected_verdict"] for name in case_names
        ] == [1, 2, 2, 3]


def test_browser_envelope_matches_the_pinned_abi_contract() -> None:
    report = json.loads(REPORT.read_bytes())

    assert report["browser_envelope"] == {
        "max_artifact_bytes": 16 * 1024 * 1024,
        "max_check_steps": 64_000_000,
        "max_codec_depth": 192,
        "max_decoded_nodes": 1_000_000,
        "max_linear_memory_bytes": 256 * 1024 * 1024,
        "max_portable_index": 2**32 - 1 - 256,
        "stack_bytes": 2 * 1024 * 1024,
        "timeout_milliseconds": 30_000,
    }
    assert report["abi"]["verdicts"] == {
        "accept": 1,
        "bad_call_or_internal": 4,
        "logical_reject": 2,
        "malformed_or_resource": 3,
    }
