"""Focused fail-closed contracts for Python/Rust differential validation."""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from runpy import run_path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = run_path(str(ROOT / "scripts" / "differential_peano_kernel_shadow.py"))
DifferentialValidationError = SCRIPT["DifferentialValidationError"]
kernel_checker = SCRIPT["kernel_checker"]
lean_default_fuel = SCRIPT["lean_default_fuel"]
main = SCRIPT["main"]
theorem_library = SCRIPT["theorem_library"]
validate_shadow = SCRIPT["validate_shadow"]
PERSISTED_REPORT = ROOT / "artifacts" / "peano-kernel" / "native-differential-v1.json"
EXPECTED_ARTIFACT_RECEIPT = (
    "4652c103b317ddf3405f74c022d2229be0c7bdb57fa94c9b0cc6e129d5a20b64"
)
EXPECTED_REPORT_SHA256 = (
    "0aaa968c91d8769c101afd51681090396a31e4885a2629e7ecfb44113cd47e5d"
)
PERSISTED_REPORT_SOURCE_COMMIT = "c0171d080ccda1e07b132590db6f7b922dff73ff"


class FakeShadow:
    """Record exact stdin and return the frozen four-case protocol."""

    def __init__(self) -> None:
        self.calls: list[dict[str, object]] = []
        self.responses = iter(
            (
                (0, b"ACCEPT\n", b""),
                (1, b"REJECT\n", b""),
                (1, b"REJECT\n", b""),
                (2, b"", b"ERROR: unexpected byte at byte 17\n"),
            )
        )

    def __call__(self, args, **kwargs):
        self.calls.append({"args": args, **kwargs})
        returncode, stdout, stderr = next(self.responses)
        return subprocess.CompletedProcess(args, returncode, stdout, stderr)


def _without_durations(value):
    if isinstance(value, dict):
        return {
            key: _without_durations(item)
            for key, item in value.items()
            if key != "duration_ns" and not key.endswith("_duration_ns")
        }
    if isinstance(value, list):
        return [_without_durations(item) for item in value]
    return value


def test_tiny_public_theorem_checks_original_and_all_three_negatives(
    monkeypatch,
) -> None:
    python_targets = []
    original_check = kernel_checker.check

    def recording_check(context, proof, target):
        python_targets.append(target)
        return original_check(context, proof, target)

    monkeypatch.setattr(kernel_checker, "check", recording_check)
    fake = FakeShadow()
    report = validate_shadow(
        ("zero_add",),
        "/tmp/fake-peano-kernel-shadow",
        timeout_seconds=7,
        runner=fake,
        selection_mode="named",
    )

    assert report["format"] == "peano-kernel-shadow-differential"
    assert report["version"] == 1
    assert report["validation_passed"] is True
    assert report["authority"] == {
        "qed": "authoritative-python-original-goal-only",
        "python_checker": "peano_lab.kernel.checker.check",
        "rust_checker": "shadow-only-never-grants-qed",
    }
    assert report["selection"] == {
        "mode": "named",
        "names": ["zero_add"],
        "theorem_count": 1,
    }
    assert report["shadow_cli"]["executable_sha256"] is None
    sources = report["implementation_sources"]
    source_manifest = "".join(
        f"{item['sha256']}  {item['path']}\n" for item in sources["files"]
    ).encode("utf-8")
    assert sources["manifest_sha256"] == sha256(source_manifest).hexdigest()

    row = report["results"][0]
    assert row["theorem"]["name"] == "zero_add"
    assert row["python"]["original_goal"]["verdict"] == "accept"
    assert row["python"]["wrong_target"]["verdict"] == "reject"
    assert len(python_targets) == 2 and python_targets[0] != python_targets[1]

    certificate = row["certificate"]
    assert certificate["lean_default_fuel"] == lean_default_fuel(
        certificate["structural_proof_nodes"]
    )
    assert certificate["canonical_artifact_sha256"] == sha256(
        fake.calls[0]["input"]
    ).hexdigest()
    assert certificate["canonical_artifact_bytes"] == len(fake.calls[0]["input"])
    assert report["artifact_set"] == {
        "receipt_contract": (
            "sha256 of lowercase canonical-artifact SHA-256 values joined "
            "by LF in selection.names order, without a terminal LF"
        ),
        "receipt_sha256": sha256(
            certificate["canonical_artifact_sha256"].encode("utf-8")
        ).hexdigest(),
        "theorem_count": 1,
    }

    cases = row["rust_cases"]
    assert [case["name"] for case in cases] == [
        "original",
        "wrong_target",
        "zero_fuel",
        "malformed_bytes",
    ]
    assert [case["rust_verdict"] for case in cases] == [
        "accept",
        "reject",
        "reject",
        "input_rejected",
    ]
    assert [case["python_verdict"] for case in cases] == [
        "accept",
        "reject",
        "accept",
        "not_applicable",
    ]

    assert fake.calls[2]["input"].startswith(b'["peano-lab-v2",0,')
    assert fake.calls[3]["input"] == fake.calls[0]["input"][:-1]
    assert all(call["args"] == ["/tmp/fake-peano-kernel-shadow"] for call in fake.calls)
    assert all(call["timeout"] == 7.0 for call in fake.calls)
    assert all(call["check"] is False for call in fake.calls)
    assert all(call["stdout"] is subprocess.PIPE for call in fake.calls)
    assert all(call["stderr"] is subprocess.PIPE for call in fake.calls)


def test_report_is_deterministic_after_observational_durations_are_removed() -> None:
    first = validate_shadow(("succ_ne_zero",), "fake", runner=FakeShadow())
    second = validate_shadow(("succ_ne_zero",), "fake", runner=FakeShadow())

    assert _without_durations(first) == _without_durations(second)


def test_persisted_complete_report_is_source_sealed_and_self_consistent() -> None:
    report_bytes = PERSISTED_REPORT.read_bytes()
    assert sha256(report_bytes).hexdigest() == EXPECTED_REPORT_SHA256
    report = json.loads(report_bytes)
    names = theorem_library.names()

    assert report["format"] == "peano-kernel-shadow-differential"
    assert report["version"] == 1
    assert report["validation_passed"] is True
    assert report["selection"] == {
        "mode": "all",
        "names": list(names),
        "theorem_count": len(names),
    }
    assert [row["theorem"]["name"] for row in report["results"]] == list(names)

    artifact_hashes = []
    for name, row in zip(names, report["results"], strict=True):
        spec = theorem_library.get(name)
        assert spec is not None
        assert row["theorem"]["statement"] == spec.statement
        certificate = row["certificate"]
        artifact_hashes.append(certificate["canonical_artifact_sha256"])
        cases = row["rust_cases"]
        assert [case["name"] for case in cases] == [
            "original",
            "wrong_target",
            "zero_fuel",
            "malformed_bytes",
        ]
        assert [case["rust_verdict"] for case in cases] == [
            "accept",
            "reject",
            "reject",
            "input_rejected",
        ]
        assert cases[0]["artifact"] == {
            "bytes": certificate["canonical_artifact_bytes"],
            "sha256": certificate["canonical_artifact_sha256"],
        }

    receipt = sha256("\n".join(artifact_hashes).encode("utf-8")).hexdigest()
    assert report["artifact_set"]["theorem_count"] == len(names)
    assert report["artifact_set"]["receipt_sha256"] == receipt
    assert receipt == EXPECTED_ARTIFACT_RECEIPT

    # This K3 report is a retained observation from its producing commit, not
    # a claim that later K4 browser/UI sources are byte-identical. Re-hash the
    # declared Git blobs at that immutable producer instead of silently
    # relabeling historical evidence with the live worktree.
    tree = subprocess.run(
        [
            "git",
            "ls-tree",
            "-r",
            "--name-only",
            PERSISTED_REPORT_SOURCE_COMMIT,
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    fixed = {
        "scripts/differential_peano_kernel_shadow.py",
        "peano-lab/rust/peano-kernel-shadow/Cargo.lock",
        "peano-lab/rust/peano-kernel-shadow/Cargo.toml",
        "peano-lab/rust/peano-kernel-shadow/rust-toolchain.toml",
    }
    expected_sources = sorted(
        {
            *fixed,
            *(
                path
                for path in tree
                if path.startswith("peano-lab/py/peano_lab/")
                and path.endswith(".py")
            ),
            *(
                path
                for path in tree
                if path.startswith("peano-lab/rust/peano-kernel-shadow/src/")
                and path.endswith(".rs")
            ),
        }
    )
    source_records = report["implementation_sources"]["files"]
    assert [record["path"] for record in source_records] == expected_sources
    manifest_lines = []
    for path, record in zip(expected_sources, source_records, strict=True):
        data = subprocess.run(
            ["git", "show", f"{PERSISTED_REPORT_SOURCE_COMMIT}:{path}"],
            cwd=ROOT,
            check=True,
            capture_output=True,
        ).stdout
        digest = sha256(data).hexdigest()
        assert record == {
            "bytes": len(data),
            "path": path,
            "sha256": digest,
        }
        manifest_lines.append(f"{digest}  {record['path']}\n")
    manifest = "".join(manifest_lines).encode("utf-8")
    assert report["implementation_sources"]["manifest_sha256"] == sha256(
        manifest
    ).hexdigest()
    executable_sha256 = report["shadow_cli"]["executable_sha256"]
    assert isinstance(executable_sha256, str) and len(executable_sha256) == 64


@pytest.mark.parametrize(
    "runner, message",
    [
        (
            lambda *args, **kwargs: (_ for _ in ()).throw(
                subprocess.TimeoutExpired(args[0], kwargs["timeout"])
            ),
            "timed out",
        ),
        (
            lambda *args, **kwargs: (_ for _ in ()).throw(
                OSError("executable missing")
            ),
            "process failed",
        ),
        (
            lambda args, **kwargs: subprocess.CompletedProcess(
                args, 0, b"ACCEPT", b""
            ),
            "protocol mismatch",
        ),
    ],
)
def test_timeout_process_and_protocol_failures_all_fail_closed(runner, message) -> None:
    with pytest.raises(DifferentialValidationError, match=message):
        validate_shadow(("succ_ne_zero",), "fake", runner=runner)


def test_malformed_case_requires_the_exact_error_channel_contract() -> None:
    fake = FakeShadow()
    fake.responses = iter(
        (
            (0, b"ACCEPT\n", b""),
            (1, b"REJECT\n", b""),
            (1, b"REJECT\n", b""),
            (2, b"REJECT\n", b""),
        )
    )
    with pytest.raises(DifferentialValidationError, match="protocol mismatch"):
        validate_shadow(("succ_ne_zero",), "fake", runner=fake)


def test_cli_all_selects_the_public_ladder_without_replaying_it(
    capsys, monkeypatch
) -> None:
    observed = {}

    def fake_validate(names, rust_cli, **kwargs):
        observed.update(
            names=names,
            rust_cli=rust_cli,
            timeout_seconds=kwargs["timeout_seconds"],
            selection_mode=kwargs["selection_mode"],
        )
        return {"format": "fixture", "version": 1}

    monkeypatch.setitem(main.__globals__, "validate_shadow", fake_validate)
    assert main(["--all", "--rust-cli", "/tmp/shadow", "--timeout-seconds", "9"]) == 0
    assert observed == {
        "names": theorem_library.names(),
        "rust_cli": "/tmp/shadow",
        "timeout_seconds": 9.0,
        "selection_mode": "all",
    }
    assert json.loads(capsys.readouterr().out) == {"format": "fixture", "version": 1}


def test_cli_can_persist_the_complete_report(
    tmp_path: Path, capsys, monkeypatch
) -> None:
    output = tmp_path / "differential.json"
    payload = {
        "format": "fixture",
        "selection": {"theorem_count": 2},
        "version": 1,
    }
    monkeypatch.setitem(
        main.__globals__, "validate_shadow", lambda *args, **kwargs: payload
    )

    assert main(["--rust-cli", "/tmp/shadow", "--output", str(output)]) == 0
    assert json.loads(output.read_text(encoding="utf-8")) == payload
    assert capsys.readouterr().out == f"wrote 2 theorem rows to {output}\n"
