"""Pure and fake-transport tests for the read-only WMI training dashboard."""

from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_policy.dashboard import (  # noqa: E402
    DASHBOARD_SCHEMA,
    MAX_REMOTE_RESPONSE_BYTES,
    REMOTE_SNAPSHOT_SCHEMA,
    REMOTE_SNAPSHOT_SOURCE,
    DashboardError,
    build_dashboard_status,
    disconnected_status,
    fetch_remote_snapshot,
    parse_loss_points,
    parse_tqdm_progress,
    validate_job_id,
    validate_ssh_target,
)


def _command(stdout: str, *, returncode: int = 0, stderr: str = "") -> dict[str, object]:
    return {"returncode": returncode, "stdout": stdout, "stderr": stderr}


def _run_identity(*, total_steps: int = 649) -> dict[str, object]:
    return {
        "config": {
            "sha256": "a" * 64,
            "resolved": {
                "model": {"dtype": "bfloat16"},
                "lora": {"rank": 32, "alpha": 64},
                "trainer": {"logging_steps": 11},
            },
        },
        "deployment": {
            "source_sync": {
                "git_commit": "4d44609ee32d5d28726c082ef7b5649c0a1107a6",
                "synced_at": "2026-08-01T01:39:27Z",
            }
        },
        "inputs": {
            "schedule_preflight": {
                "format": "peano-policy-v3-training-schedule",
                "v": 1,
                "train_rows": 20_765,
                "eval_rows": 512,
                "expected_optimizer_steps": total_steps,
                "adapter_recovery": {
                    "planned_optimizer_steps": [100, 200, 300, 400, 500, 600]
                },
            }
        },
        "job": {
            "submission": {
                "job_id": "217859",
                "dependency_job_id": "217851",
            }
        },
        "model": {
            "id": "Qwen/Qwen3-1.7B-Base",
            "revision": "e" * 40,
        },
    }


def _snapshot(
    *,
    state: str = "RUNNING",
    stderr: str = "",
    stdout: str = "",
    manifest: object = None,
) -> dict[str, object]:
    return {
        "schema": REMOTE_SNAPSHOT_SCHEMA,
        "v": 1,
        "captured_at": "2026-08-01T09:00:00+00:00",
        "job_id": "217859",
        "_connection": {
            "status": "connected",
            "target": "wmicluster",
            "latency_ms": 21,
            "error": None,
        },
        "scheduler": {
            "squeue": _command(
                "217859|gpu_csi|peano-wmi-qwen17-v3|"
                f"{state}|g3n1|N/A|02:44:00|1-12:00:00|"
                "2026-08-01T08:16:26\n"
                if state in {"RUNNING", "COMPLETING"}
                else ""
            ),
            "sacct": _command(
                "217859|peano-wmi-qwen17-v3|gpu_csi|"
                f"{state}|0:0|0:0|9840|2026-08-01T08:16:26|Unknown|"
                "billing=16,cpu=16,gres/gpu:nvidia_a100=1,mem=128G,node=1\n"
            ),
            "sstat": _command(
                "217859.batch|02:44:02|10053020K|10053252K|14108917587|"
                "141153403|cpu=02:44:02,gres/gpumem=17236M,"
                "gres/gpuutil=82,mem=10053020K|cpu=02:44:02,"
                "gres/gpumem=18000M,gres/gpuutil=93,mem=10053252K\n"
            ),
        },
        "files": {
            "stdout": {"exists": True, "text": stdout},
            "stderr": {"exists": True, "text": stderr},
            "run_identity": {"exists": True, "value": _run_identity()},
            "training_manifest": {
                "exists": manifest is not None,
                "value": manifest,
            },
            "preparation_runtime_smoke": {
                "exists": True,
                "value": {
                    "status": "passed",
                    "trainer_integration": {
                        "train_global_step": 1,
                        "training_loss": 2.8299612998962402,
                        "evaluation_loss": 0.8195649981498718,
                    },
                },
            },
        },
        "recovery": [
            {
                "name": "step-00000100-run-2c36b33c855489db-job-217859",
                "declared_step": 100,
                "manifest": {
                    "exists": True,
                    "value": {
                        "global_step": 100,
                        "training_complete": False,
                        "eligible_as_training_result": False,
                        "resumable": False,
                    },
                },
            }
        ],
        "samples": [
            {
                "example_id": "sample:1",
                "theorem": "add_assoc",
                "formula": "∀ x. ∀ y. ∀ z. x + y + z = x + (y + z)",
                "family": "library-theorem/add_assoc",
                "state": ["⊢ ∀ x. ∀ y. ∀ z. x + y + z = x + (y + z)"],
                "next_tactic": "intro n",
                "library": ["zero_add", "add_succ_left", "add_comm"],
                "kind": "selected-catalog-example",
                "untrusted_extra": "must disappear",
            }
        ],
    }


def test_identifiers_reject_options_shell_text_and_job_lists() -> None:
    assert validate_job_id("217859") == "217859"
    assert validate_ssh_target("wmicluster") == "wmicluster"
    assert validate_ssh_target("user@cluster.wmi.example") == (
        "user@cluster.wmi.example"
    )
    for value in ("", "-1", "217859,2", "217859;id", " 217859"):
        with pytest.raises(ValueError):
            validate_job_id(value)
    for value in ("", "-Fconfig", "host;id", "user name@host", "a/b"):
        with pytest.raises(ValueError):
            validate_ssh_target(value)


def test_remote_collector_source_has_only_read_only_file_and_scheduler_calls() -> None:
    tree = ast.parse(REMOTE_SNAPSHOT_SOURCE)
    forbidden_attributes = {
        "chmod",
        "mkdir",
        "rename",
        "replace",
        "rmdir",
        "unlink",
        "write",
        "write_bytes",
        "write_text",
    }
    observed_attributes = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    assert forbidden_attributes.isdisjoint(observed_attributes)
    assert 'path.open("rb")' in REMOTE_SNAPSHOT_SOURCE
    assert "read_bytes()" in REMOTE_SNAPSHOT_SOURCE
    assert "shell=True" not in REMOTE_SNAPSHOT_SOURCE
    assert "os.system" not in REMOTE_SNAPSHOT_SOURCE
    for command in ('["squeue"', '["sacct"', '["sstat"'):
        assert command in REMOTE_SNAPSHOT_SOURCE


def test_tqdm_parser_handles_carriage_returns_and_uses_last_matching_bar() -> None:
    text = (
        "\r 19%|x| 122/649 [41:17<3:01:14, 20.64s/it]"
        "\r 27%|x| 137/512 [05:00<10:00, 1.20it/s]"
        "\r 21%|x| 136/649 [46:00<2:55:40, 20.55s/it]"
    )
    progress = parse_tqdm_progress(text, expected_total=649)
    assert progress == {
        "step": 136,
        "total_steps": 649,
        "percent": pytest.approx(20.955),
        "seconds_per_step": pytest.approx(20.55),
        "eta_seconds": 10_540,
        "training_elapsed_seconds": 2_760,
        "source": "stderr-tqdm",
    }


def test_tqdm_parser_handles_completed_bar_and_it_per_second() -> None:
    complete = parse_tqdm_progress(
        "100%|##########| 10/10 [00:05, 2.00it/s]", expected_total=10
    )
    assert complete is not None
    assert complete["step"] == 10
    assert complete["percent"] == 100.0
    assert complete["seconds_per_step"] == 0.5
    assert complete["eta_seconds"] == 0


def test_loss_parser_accepts_only_finite_schedule_aligned_trainer_records() -> None:
    stdout = "\n".join(
        (
            "{'python': '3.12.12', 'torch': '2.5.1'}",
            "{'loss': 2.4, 'grad_norm': 0.8, 'learning_rate': 3e-05, 'epoch': 0.02}",
            "{'loss': true, 'learning_rate': 2e-05, 'epoch': 0.03}",
            "{'loss': 2.1, 'grad_norm': 0.7, 'learning_rate': 2e-05, 'epoch': 0.03}",
            "{'loss': 9.9, 'epoch': 0.95}",
        )
    )
    points = parse_loss_points(stdout, logging_steps=11, total_steps=649)
    assert [point["step"] for point in points] == [11, 22]
    assert [point["loss"] for point in points] == [2.4, 2.1]
    assert points[0]["source"] == "stdout-transformers-log"


def test_live_status_combines_scheduler_bar_recovery_smoke_resources_and_samples() -> None:
    snapshot = _snapshot(
        stderr="\r 21%|xx| 136/649 [46:00<2:55:40, 20.55s/it]"
    )
    status = build_dashboard_status(snapshot)

    assert status["schema"] == DASHBOARD_SCHEMA
    assert status["v"] == 1
    assert status["connection"]["status"] == "connected"
    assert status["job"]["state"] == "RUNNING"
    assert status["job"]["hardware"] == "1 × NVIDIA A100"
    assert status["progress"]["phase"] == "training"
    assert status["progress"]["step"] == 136
    assert status["progress"]["total_steps"] == 649
    assert status["loss"]["status"] == "buffered"
    assert status["loss"]["points"] == []
    assert status["loss"]["smoke"]["training_loss"] == pytest.approx(2.8299613)
    assert status["snapshots"]["latest_step"] == 100
    assert status["snapshots"]["published"][0]["resumable"] is False
    assert status["resources"]["gpu_utilization_percent"] == 82
    assert status["resources"]["max_gpu_utilization_percent"] == 93
    assert status["model"]["id"] == "Qwen/Qwen3-1.7B-Base"
    assert status["source"]["preparation_job_id"] == "217851"
    assert status["samples"][0]["next_tactic"] == "intro n"
    assert status["samples"][0]["library"] == [
        "zero_add",
        "add_succ_left",
        "add_comm",
    ]
    assert "untrusted_extra" not in status["samples"][0]
    json.dumps(status, allow_nan=False)


def test_live_loss_points_replace_honest_buffered_status() -> None:
    stdout = (
        "{'loss': 2.4, 'grad_norm': 0.8, "
        "'learning_rate': 3e-05, 'epoch': 0.02}\n"
    )
    status = build_dashboard_status(
        _snapshot(
            stdout=stdout,
            stderr="\r 2%|x| 11/649 [03:28<3:31:01, 19.85s/it]",
        )
    )
    assert status["loss"]["status"] == "live"
    assert status["loss"]["points"][0]["step"] == 11


def test_completed_manifest_is_the_authority_for_loss_and_completion() -> None:
    manifest = {
        "adapter": {"sha256": "b" * 64},
        "training_evidence": {
            "logging": {
                "records": [
                    {
                        "step": 11,
                        "loss": 2.2,
                        "learning_rate": 0.0001,
                        "epoch": 0.02,
                    },
                    {"step": 649, "train_loss": 1.2, "epoch": 1.0},
                ]
            }
        },
    }
    snapshot = _snapshot(state="COMPLETED", manifest=manifest)
    status = build_dashboard_status(snapshot)
    assert status["progress"]["phase"] == "completed"
    assert status["loss"]["status"] == "completed-evidence"
    assert status["loss"]["points"] == [
        {
            "step": 11,
            "loss": 2.2,
            "learning_rate": 0.0001,
            "grad_norm": None,
            "epoch": 0.02,
            "source": "completed-training-evidence",
        }
    ]
    assert status["artifacts"]["final_adapter"] is True


def test_terminal_scheduler_failure_is_never_presented_as_training() -> None:
    status = build_dashboard_status(
        _snapshot(
            state="FAILED",
            stderr="\r 21%|x| 136/649 [46:00<2:55:40, 20.55s/it]",
        )
    )
    assert status["job"]["state"] == "FAILED"
    assert status["progress"]["phase"] == "failed"


def test_old_progress_cannot_turn_unknown_or_suspended_scheduler_into_training() -> None:
    unknown = _snapshot(
        stderr="\r 21%|x| 136/649 [46:00<2:55:40, 20.55s/it]"
    )
    unknown["scheduler"]["squeue"] = _command("", returncode=1)
    unknown["scheduler"]["sacct"] = _command("", returncode=1)
    status = build_dashboard_status(unknown)
    assert status["job"]["state"] == "UNKNOWN"
    assert status["progress"]["step"] == 136
    assert status["progress"]["phase"] == "unknown"

    suspended = build_dashboard_status(
        _snapshot(
            state="SUSPENDED",
            stderr="\r 21%|x| 136/649 [46:00<2:55:40, 20.55s/it]",
        )
    )
    assert suspended["progress"]["phase"] == "suspended"


def test_run_identity_must_bind_the_requested_slurm_job() -> None:
    snapshot = _snapshot()
    snapshot["files"]["run_identity"]["value"]["job"]["submission"][
        "job_id"
    ] = "217860"
    with pytest.raises(DashboardError, match="run identity job"):
        build_dashboard_status(snapshot)


def test_fetch_transport_uses_fixed_stdin_source_and_no_shell() -> None:
    payload = _snapshot()
    observed: dict[str, object] = {}

    def runner(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        observed["command"] = command
        observed.update(kwargs)
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps(payload).encode(),
            stderr=b"",
        )

    result = fetch_remote_snapshot(
        "217859", ssh_target="wmicluster", timeout_seconds=12, runner=runner
    )
    assert result["job_id"] == "217859"
    assert observed["command"][-3:] == ["python3", "-", "217859"]
    assert observed["input"] == REMOTE_SNAPSHOT_SOURCE.encode()
    assert "shell" not in observed
    assert observed["timeout"] == 12


def test_fetch_rejects_oversized_invalid_or_mismatched_remote_payload() -> None:
    outputs = (
        b"x" * (MAX_REMOTE_RESPONSE_BYTES + 1),
        b"not json",
        json.dumps({**_snapshot(), "job_id": "999"}).encode(),
    )
    for output in outputs:
        def runner(command: list[str], **_: object) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(command, 0, stdout=output, stderr=b"")

        with pytest.raises(DashboardError):
            fetch_remote_snapshot("217859", runner=runner)


def test_disconnected_status_is_json_ready_and_does_not_invent_progress() -> None:
    status = disconnected_status(
        "217859", ssh_target="wmicluster", error=OSError("VPN unavailable")
    )
    assert status["connection"]["status"] == "error"
    assert status["progress"]["phase"] == "unreachable"
    assert status["progress"]["step"] is None
    assert status["loss"]["points"] == []
    json.dumps(status, allow_nan=False)
