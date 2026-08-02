#!/usr/bin/env python3
"""Run the isolated WMI Jupyter Book build and write an audit receipt."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
from time import perf_counter
from typing import Any

from package_wmi_book_snapshot import snapshot_metadata


ROOT = Path(__file__).resolve().parents[1]
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
POSITIVE_PATTERN = re.compile(r"^[1-9][0-9]*$")
TIME_PATTERN = re.compile(r"^(?:[0-9]+-)?[0-9]{2}:[0-9]{2}:[0-9]{2}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _identity(name: str, pattern: re.Pattern[str]) -> str:
    value = os.environ.get(name, "")
    if pattern.fullmatch(value) is None:
        raise ValueError(f"missing or malformed {name}")
    return value


def _resources() -> dict[str, Any]:
    partition = os.environ.get("PEANO_BOOK_REQUESTED_PARTITION", "")
    if partition != "cpu_idle":
        raise ValueError("book build partition must be cpu_idle")
    result: dict[str, Any] = {
        "cpus_per_task": int(_identity("PEANO_BOOK_REQUESTED_CPUS_PER_TASK", POSITIVE_PATTERN)),
        "memory_mib": int(_identity("PEANO_BOOK_REQUESTED_MEMORY_MIB", POSITIVE_PATTERN)),
        "nodes": int(_identity("PEANO_BOOK_REQUESTED_NODES", POSITIVE_PATTERN)),
        "ntasks": int(_identity("PEANO_BOOK_REQUESTED_NTASKS", POSITIVE_PATTERN)),
        "partition": partition,
        "time_limit": _identity("PEANO_BOOK_REQUESTED_TIME_LIMIT", TIME_PATTERN),
        "time_limit_seconds": int(
            _identity("PEANO_BOOK_REQUESTED_TIME_LIMIT_SECONDS", POSITIVE_PATTERN)
        ),
    }
    expected = {
        "cpus_per_task": 1,
        "memory_mib": 8192,
        "nodes": 1,
        "ntasks": 1,
        "time_limit": "01:00:00",
        "time_limit_seconds": 3600,
    }
    for key, value in expected.items():
        if result[key] != value:
            raise ValueError(f"unexpected WMI book resource {key}: {result[key]!r}")
    return result


def _require_sanitized_parent_environment() -> None:
    forbidden = {"PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV"}
    observed = sorted(
        name for name in os.environ if name in forbidden or name.startswith("CONDA_")
    )
    if observed:
        raise ValueError(f"unsanitized parent environment variables: {observed}")


def _run_step(
    label: str,
    argv: list[str],
    *,
    logs: Path,
    env: dict[str, str],
    timeout: int,
) -> dict[str, Any]:
    stdout_path = logs / f"{label}.stdout.log"
    stderr_path = logs / f"{label}.stderr.log"
    started = perf_counter()
    started_at = _utc_now()
    timed_out = False
    print(f"BOOK START {label}", flush=True)
    with stdout_path.open("wb") as stdout, stderr_path.open("wb") as stderr:
        try:
            result = subprocess.run(
                argv,
                cwd=ROOT,
                env=env,
                stdout=stdout,
                stderr=stderr,
                timeout=timeout,
                check=False,
            )
            returncode = result.returncode
        except subprocess.TimeoutExpired:
            timed_out = True
            returncode = 124
    duration = perf_counter() - started
    row = {
        "argv": argv,
        "duration_seconds": duration,
        "finished_at": _utc_now(),
        "label": label,
        "returncode": returncode,
        "started_at": started_at,
        "stderr_bytes": stderr_path.stat().st_size,
        "stderr_path": str(stderr_path.relative_to(ROOT)),
        "stderr_sha256": _sha256(stderr_path),
        "stdout_bytes": stdout_path.stat().st_size,
        "stdout_path": str(stdout_path.relative_to(ROOT)),
        "stdout_sha256": _sha256(stdout_path),
        "timed_out": timed_out,
        "timeout_seconds": timeout,
    }
    outcome = "PASS" if returncode == 0 else "FAIL"
    print(f"BOOK {outcome}  {label} ({duration:.3f}s)", flush=True)
    return row


def _write_report(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, allow_nan=False, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = args.report.resolve()
    logs = report.parent
    logs.mkdir(parents=True, exist_ok=True)
    started = perf_counter()
    payload: dict[str, Any] = {
        "commands": [],
        "finished_at": None,
        "format": "peano-wmi-book-build",
        "host": platform.node(),
        "platform": platform.platform(),
        "python": {
            "base_executable": sys.executable,
            "base_version": platform.python_version(),
        },
        "slurm_job_id": os.environ.get("SLURM_JOB_ID"),
        "started_at": _utc_now(),
        "status": "failed",
        "version": 2,
    }
    exit_code = 1
    try:
        snapshot_sha256 = _identity("PEANO_BOOK_SNAPSHOT_SHA256", SHA256_PATTERN)
        content_sha256 = _identity("PEANO_BOOK_CONTENT_MANIFEST_SHA256", SHA256_PATTERN)
        local_commit = _identity("PEANO_BOOK_LOCAL_COMMIT", COMMIT_PATTERN)
        head_capture_sha256 = _identity(
            "PEANO_BOOK_HEAD_CAPTURE_SHA256", SHA256_PATTERN
        )
        worktree_status_sha256 = _identity(
            "PEANO_BOOK_WORKTREE_STATUS_SHA256", SHA256_PATTERN
        )
        dirty_text = os.environ.get("PEANO_BOOK_LOCAL_DIRTY", "")
        if dirty_text not in {"true", "false"}:
            raise ValueError("PEANO_BOOK_LOCAL_DIRTY must be true or false")
        _require_sanitized_parent_environment()
        resources = _resources()
        observed = snapshot_metadata(ROOT)
        if observed["content_manifest_sha256"] != content_sha256:
            raise ValueError(
                "staged source manifest mismatch: "
                f"expected {content_sha256}, observed {observed['content_manifest_sha256']}"
            )
        requirements = ROOT / "requirements.txt"
        payload.update(
            {
                "content_manifest": observed,
                "head_capture_sha256": head_capture_sha256,
                "local_commit": local_commit,
                "local_dirty": dirty_text == "true",
                "requested_resources": resources,
                "requirements_sha256": _sha256(requirements),
                "snapshot_sha256": snapshot_sha256,
                "worktree_status_sha256": worktree_status_sha256,
            }
        )

        venv = ROOT / ".wmi-book-venv"
        if venv.exists() or venv.is_symlink():
            raise ValueError("isolated WMI book venv already exists in the fresh run")
        venv_python = venv / "bin" / "python"
        jupyter_book = venv / "bin" / "jupyter-book"
        env = dict(os.environ)
        env.update(
            {
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_NO_INPUT": "1",
                "PYTHONHASHSEED": "20260730",
                "PYTHONNOUSERSITE": "1",
            }
        )
        payload["environment_boundary"] = {
            "base_interpreter": (
                "absolute interpreter in reviewed WMI Conda environment; "
                "no activation command"
            ),
            "conda_activation_command": False,
            "dependency_hash_lock": False,
            "inherited_variables_removed": [
                "PYTHONPATH",
                "PYTHONHOME",
                "VIRTUAL_ENV",
                "CONDA_*",
            ],
            "pip_configuration_inherited_from_wmi": True,
            "python_no_user_site": True,
            "venv": str(venv.relative_to(ROOT)),
        }
        steps: list[tuple[str, list[str], int, bool]] = [
            ("01-venv", [sys.executable, "-m", "venv", str(venv)], 180, True),
            (
                "02-pip-install",
                [
                    str(venv_python),
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--no-input",
                    "-r",
                    "requirements.txt",
                ],
                1200,
                True,
            ),
            ("03-pip-freeze", [str(venv_python), "-m", "pip", "freeze", "--all"], 120, True),
            ("04-jupyter-book-version", [str(jupyter_book), "--version"], 120, True),
            (
                "05-atlas-check",
                [str(venv_python), "scripts/build_arithmetic_book_atlas.py", "--check"],
                300,
                True,
            ),
            (
                "06-proof-explorer-check",
                [str(venv_python), "scripts/build_pa_proof_explorer.py", "--check"],
                300,
                True,
            ),
            (
                "06b-defined-proof-explorer-check",
                [str(venv_python), "scripts/build_pa_defined_explorer.py", "--check"],
                600,
                True,
            ),
            (
                "07-jupyter-book-build",
                [str(jupyter_book), "build", "book/", "--warningiserror", "--keep-going"],
                1800,
                True,
            ),
        ]
        for label, argv, timeout, stop_on_failure in steps:
            row = _run_step(label, argv, logs=logs, env=env, timeout=timeout)
            payload["commands"].append(row)
            if row["returncode"] != 0 and stop_on_failure:
                raise RuntimeError(f"required WMI book step failed: {label}")

        freeze_log = logs / "03-pip-freeze.stdout.log"
        version_log = logs / "04-jupyter-book-version.stdout.log"
        payload["pip_freeze"] = {
            "bytes": freeze_log.stat().st_size,
            "path": str(freeze_log.relative_to(ROOT)),
            "sha256": _sha256(freeze_log),
        }
        payload["jupyter_book_version"] = version_log.read_text(
            encoding="utf-8", errors="replace"
        ).strip()

        # The two deterministic source generators were checked before Sphinx
        # was allowed to run.  This final non-executing gate audits the copied
        # explorer microsite and every other built relative target.
        row = _run_step(
            "08-book-integrity",
            [
                str(venv_python),
                "scripts/check_wmi_book_build.py",
                "--book",
                "book",
                "--output",
                str(logs / "book-integrity.json"),
            ],
            logs=logs,
            env=env,
            timeout=300,
        )
        payload["commands"].append(row)
        integrity_path = logs / "book-integrity.json"
        if integrity_path.is_file():
            payload["integrity"] = json.loads(integrity_path.read_text(encoding="utf-8"))
            payload["integrity_receipt_sha256"] = _sha256(integrity_path)
        if row["returncode"] != 0:
            raise RuntimeError("the non-executing book integrity check failed")
        payload["status"] = "passed"
        exit_code = 0
    except BaseException as exc:
        payload["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        payload["duration_seconds"] = perf_counter() - started
        payload["finished_at"] = _utc_now()
        _write_report(report, payload)
        print(json.dumps(payload, allow_nan=False, sort_keys=True), flush=True)
        print(f"book_build_report_sha256={_sha256(report)}", flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
