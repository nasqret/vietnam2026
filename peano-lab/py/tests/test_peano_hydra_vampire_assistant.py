"""Functional one-shot Hydra/Vampire assistant preview."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra.vampire_assistant import (  # noqa: E402
    VampireAssistantError,
    canonical_evidence_bytes,
    run_vampire_assistant,
)


def _fake_vampire(tmp_path: Path, output: bytes) -> Path:
    path = tmp_path / "fake-vampire.py"
    path.write_text(
        f"#!{sys.executable}\n"
        "import os\n"
        f"os.write(1, {output!r})\n",
        encoding="utf-8",
        newline="\n",
    )
    path.chmod(0o700)
    return path


def _run(
    executable: Path,
    *,
    goal: str = "0 + 0 = 0",
    premises: tuple[str, ...] = ("PA3",),
    allowlist: frozenset[str] | None = None,
) -> dict[str, object]:
    return run_vampire_assistant(
        goal,
        premises,
        executable=executable,
        arguments=("--mode", "casc"),
        wall_time_ms=2_000,
        output_bytes=4_096,
        premise_allowlist=allowlist,
    )


def test_pa3_non_reflexive_goal_succeeds_only_after_fresh_kernel(
    tmp_path: Path,
) -> None:
    executable = _fake_vampire(
        tmp_path, b"% SZS status Theorem for explicit_pa3\n"
    )
    result = _run(executable)

    assert result["status"] == "accepted"
    assert result["solver_status"] == "theorem"
    assert result["reconstructed_commands"] == ["apply PA3"]
    assert result["resolved_premises"] == [
        {"kind": "pa-axiom", "name": "PA3", "statement": "∀ x. x + 0 = x"}
    ]
    assert result["kernel_accepted"] is True
    assert result["certificate_representation"] == "peano-lab-v2"
    assert isinstance(result["certificate_nodes"], int)
    assert isinstance(result["certificate_depth"], int)
    assert len(result["certificate_sha256"]) == 64
    assert len(result["problem_sha256"]) == 64
    assert len(result["executable_sha256"]) == 64
    assert len(result["output_sha256"]) == 64
    assert result["authority"] == "none"
    assert result["live_dispatch_registered"] is False
    for name, value in result.items():
        if name.endswith("_eligible"):
            assert value is False


def test_forged_theorem_status_with_irrelevant_premise_is_diagnostic_failure(
    tmp_path: Path,
) -> None:
    executable = _fake_vampire(
        tmp_path,
        b"% SZS status Theorem for forged\napply PA3\nqed\n",
    )
    result = _run(executable, premises=("PA4",))

    assert result["solver_status"] == "theorem"
    assert result["reconstructed_commands"] == ["apply PA4"]
    assert result["status"] == "rejected"
    assert result["failed_command"] == "apply PA4"
    assert "does not match" in result["diagnostic"]
    assert result["kernel_accepted"] is False
    assert result["certificate_sha256"] is None


def test_unknown_and_masked_names_fail_before_executable_invocation(
    tmp_path: Path,
) -> None:
    absent = tmp_path / "does-not-exist"
    unknown = _run(absent, premises=("not_a_public_theorem",))
    masked = _run(
        absent,
        premises=("PA3",),
        allowlist=frozenset(),
    )

    assert unknown["status"] == masked["status"] == "rejected"
    assert unknown["solver_status"] == masked["solver_status"] == "not-run"
    assert "unknown public PA premise" in unknown["diagnostic"]
    assert "masked by the explicit allow-list" in masked["diagnostic"]
    for result in (unknown, masked):
        assert result["problem_sha256"] is None
        assert result["executable_sha256"] is None
        assert result["output_sha256"] is None
        assert result["kernel_accepted"] is False


def test_evidence_is_byte_deterministic_without_raw_output_or_measured_time(
    tmp_path: Path,
) -> None:
    executable = _fake_vampire(
        tmp_path, b"% SZS status Unsatisfiable for explicit_pa3\n"
    )
    first = _run(executable)
    second = _run(executable)

    assert first == second
    encoded = canonical_evidence_bytes(first)
    assert encoded == canonical_evidence_bytes(second)
    assert encoded.endswith(b"\n")
    decoded = json.loads(encoded)
    assert decoded == first
    assert "raw_output" not in first
    assert "wall_time_ms" not in first


def test_no_reconstructable_commands_is_inert_failure(tmp_path: Path) -> None:
    executable = _fake_vampire(tmp_path, b"% SZS status Theorem for forged\n")
    result = _run(
        executable,
        goal="0 = 1",
        premises=(),
    )
    assert result["reconstructed_commands"] == []
    assert result["kernel_accepted"] is False
    assert result["status"] == "rejected"
    assert "no reconstructable public command" in result["diagnostic"]


def test_goal_and_premise_inputs_are_exact_and_canonical(tmp_path: Path) -> None:
    executable = _fake_vampire(tmp_path, b"% SZS status Theorem for x\n")
    with pytest.raises(VampireAssistantError, match="not canonical"):
        _run(executable, goal="forall x. x + 0 = x")
    with pytest.raises(VampireAssistantError, match="duplicates"):
        _run(executable, premises=("PA3", "PA3"))


def test_cli_prints_one_json_document_and_writes_no_default_artifact(
    tmp_path: Path,
) -> None:
    executable = _fake_vampire(tmp_path, b"% SZS status Theorem for x\n")
    script = ROOT / "scripts" / "peano_hydra_vampire_assist.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "0 + 0 = 0",
            "--premise",
            "PA3",
            "--vampire",
            str(executable),
            "--wall-time-ms",
            "2000",
            "--output-bytes",
            "4096",
        ],
        cwd=tmp_path,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert completed.returncode == 0, completed.stderr.decode()
    result = json.loads(completed.stdout)
    assert result["status"] == "accepted"
    assert result["arguments"] == [
        "--mode",
        "vampire",
        "--input_syntax",
        "tptp",
        "--proof",
        "tptp",
    ]

    explicit = subprocess.run(
        [
            sys.executable,
            str(script),
            "0 + 0 = 0",
            "--premise",
            "PA3",
            "--vampire",
            str(executable),
            "--vampire-arg=--mode",
            "--vampire-arg=casc",
            "--wall-time-ms",
            "2000",
            "--output-bytes",
            "4096",
        ],
        cwd=tmp_path,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert explicit.returncode == 0, explicit.stderr.decode()
    assert json.loads(explicit.stdout)["arguments"] == ["--mode", "casc"]
    assert list(tmp_path.iterdir()) == [executable]
