"""Focused transport, resource, publication, and cancellation hardening tests."""

from __future__ import annotations

import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

import pytest

from peano_lab.batch import BatchRequestError


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "scripts" / "peano_batch.py"
CLI_SPEC = importlib.util.spec_from_file_location("_batch_cli_hardening", CLI)
assert CLI_SPEC is not None and CLI_SPEC.loader is not None
batch_cli = importlib.util.module_from_spec(CLI_SPEC)
sys.modules[CLI_SPEC.name] = batch_cli
CLI_SPEC.loader.exec_module(batch_cli)


def _request(request_id: str = "proof", *, tactics: list[str] | None = None) -> str:
    return json.dumps(
        {
            "v": 1,
            "id": request_id,
            "theorem": "0 = 0",
            "tactics": tactics or ["refl"],
        },
        separators=(",", ":"),
    )


def _run_cli(*args: str, input_text: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CLI), *args],
        cwd=ROOT,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def _install_text_stdio(monkeypatch: pytest.MonkeyPatch, input_text: str):
    output = io.StringIO()
    errors = io.StringIO()
    monkeypatch.setattr(batch_cli.sys, "stdin", io.StringIO(input_text))
    monkeypatch.setattr(batch_cli.sys, "stdout", output)
    monkeypatch.setattr(batch_cli.sys, "stderr", errors)
    return output, errors


def test_json_integer_boundary_is_lexical_and_every_float_is_rejected() -> None:
    digits = batch_cli.MAX_JSON_INTEGER_DIGITS
    positive = "9" * digits
    negative = "-" + positive
    assert batch_cli._decode(positive) == int(positive)
    assert batch_cli._decode(negative) == int(negative)

    for oversized in ("9" * (digits + 1), "-" + "9" * (digits + 1)):
        with pytest.raises(BatchRequestError, match="digit transport limit"):
            batch_cli._decode(oversized)

    for floating in ("1.0", "-0.0", "1e2", "1e9999"):
        with pytest.raises(BatchRequestError, match="floating-point"):
            batch_cli._decode(floating)


def test_json_container_nesting_limit_is_exact_before_decode_and_hash() -> None:
    limit = batch_cli.MAX_JSON_NESTING
    exact_raw = "[" * limit + "0" + "]" * limit
    decoded = batch_cli._decode(exact_raw)
    leaf = decoded
    for _ in range(limit):
        assert isinstance(leaf, list) and len(leaf) == 1
        leaf = leaf[0]
    assert leaf == 0
    assert batch_cli._session_id(
        decoded,
        ordinal=1,
        environment_sha256="0" * 64,
    ).startswith("peano-batch-")

    with pytest.raises(BatchRequestError, match=f"{limit}-container"):
        batch_cli._decode("[" * (limit + 1) + "0" + "]" * (limit + 1))

    excessive: object = 0
    for _ in range(limit + 1):
        excessive = [excessive]
    with pytest.raises(
        BatchRequestError,
        match=rf"deterministically hashed: JSON nesting exceeds the {limit}-container",
    ):
        batch_cli._session_id(
            excessive,
            ordinal=1,
            environment_sha256="0" * 64,
        )


def test_json_nesting_scanner_ignores_delimiters_and_escapes_inside_strings() -> None:
    text = ('[{]} "quoted" \\ ' * (batch_cli.MAX_JSON_NESTING + 1)).rstrip()
    raw = json.dumps({"text": text}, separators=(",", ":"))

    assert batch_cli._decode(raw) == {"text": text}


@pytest.mark.parametrize(
    "bad_version",
    (
        "9" * (batch_cli.MAX_JSON_INTEGER_DIGITS + 1),
        "1.0",
        "1e9999",
    ),
)
def test_numeric_transport_rejection_is_structured_and_starts_no_trace(
    tmp_path: Path,
    bad_version: str,
) -> None:
    trace_path = tmp_path / "must-not-exist.jsonl"
    raw = (
        '{"v":'
        + bad_version
        + ',"id":"bad-number","theorem":"0=0","tactics":["refl"]}\n'
    )
    completed = _run_cli(
        "--trace-output",
        str(trace_path),
        input_text=raw,
    )

    assert completed.returncode == 2
    assert completed.stderr == ""
    response = json.loads(completed.stdout)
    assert response["status"] == "request_error"
    assert response["kernel_checked"] is False
    assert "Traceback" not in completed.stdout
    assert not trace_path.exists()
    assert list(tmp_path.glob("*.partial")) == []


def test_aggregate_input_limit_is_exact_and_aborts_without_partial_output() -> None:
    request = _request() + "\n"
    exact = len(request.encode("utf-8"))
    accepted = _run_cli(
        "--verify-only",
        "--max-input-bytes",
        str(exact),
        input_text=request,
    )
    rejected = _run_cli(
        "--verify-only",
        "--max-input-bytes",
        str(exact - 1),
        input_text=request,
    )

    assert accepted.returncode == 0
    assert json.loads(accepted.stdout)["status"] == "proved"
    assert rejected.returncode == 2
    assert rejected.stdout == ""
    assert "batch limit exceeded" in rejected.stderr


def test_request_count_limit_discards_prior_trace_and_results(tmp_path: Path) -> None:
    trace_path = tmp_path / "must-not-exist.jsonl"
    completed = _run_cli(
        "--trace-output",
        str(trace_path),
        "--max-requests",
        "1",
        input_text=_request("first") + "\n" + _request("second") + "\n",
    )

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "request count" in completed.stderr
    assert not trace_path.exists()
    assert list(tmp_path.glob("*.partial")) == []


def test_result_and_trace_aggregate_limits_fail_before_publication(
    tmp_path: Path,
) -> None:
    result_limited = _run_cli(
        "--verify-only",
        "--max-result-bytes",
        "1",
        input_text=_request() + "\n",
    )
    assert result_limited.returncode == 2
    assert result_limited.stdout == ""
    assert "result JSONL" in result_limited.stderr

    trace_path = tmp_path / "must-not-exist.jsonl"
    trace_limited = _run_cli(
        "--trace-output",
        str(trace_path),
        "--max-trace-bytes",
        "1",
        input_text=_request() + "\n",
    )
    assert trace_limited.returncode == 2
    assert trace_limited.stdout == ""
    assert "raw trace" in trace_limited.stderr
    assert not trace_path.exists()
    assert list(tmp_path.glob("*.partial")) == []


def test_directory_fsync_closes_its_descriptor_on_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    closed: list[int] = []
    monkeypatch.setattr(batch_cli.os, "open", lambda *_args: 73)
    monkeypatch.setattr(
        batch_cli.os,
        "fsync",
        lambda _descriptor: (_ for _ in ()).throw(OSError("injected sync")),
    )
    monkeypatch.setattr(batch_cli.os, "close", closed.append)

    with pytest.raises(OSError, match="injected sync"):
        batch_cli._fsync_directory(Path("."))
    assert closed == [73]


def test_successful_trace_commit_syncs_parent_before_and_after_cleanup(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace_path = tmp_path / "committed.jsonl"
    output, errors = _install_text_stdio(monkeypatch, _request() + "\n")
    synced: list[Path] = []
    monkeypatch.setattr(batch_cli, "_fsync_directory", synced.append)

    assert batch_cli.main(["--trace-output", str(trace_path)]) == 0
    assert json.loads(output.getvalue())["status"] == "proved"
    assert errors.getvalue() == ""
    assert trace_path.exists()
    assert synced == [tmp_path, tmp_path]
    assert list(tmp_path.glob("*.partial")) == []


def test_post_commit_cleanup_failure_keeps_trace_and_publishes_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace_path = tmp_path / "committed.jsonl"
    output, errors = _install_text_stdio(monkeypatch, _request() + "\n")
    original_unlink = Path.unlink

    def fail_committed_stage(path: Path, *args, **kwargs):
        if path.suffix == ".partial" and trace_path.exists():
            raise OSError("injected cleanup failure")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(batch_cli, "_fsync_directory", lambda _path: None)
    monkeypatch.setattr(Path, "unlink", fail_committed_stage)

    assert batch_cli.main(["--trace-output", str(trace_path)]) == 4
    assert trace_path.exists()
    assert json.loads(output.getvalue())["status"] == "proved"
    assert "is committed" in errors.getvalue()
    assert "cannot publish" not in errors.getvalue()
    assert len(list(tmp_path.glob("*.partial"))) == 1


def test_post_commit_directory_sync_failure_still_publishes_matching_results(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace_path = tmp_path / "committed.jsonl"
    output, errors = _install_text_stdio(monkeypatch, _request() + "\n")
    calls = 0

    def fail_first_sync(_path: Path) -> None:
        nonlocal calls
        calls += 1
        if calls == 1:
            raise OSError("injected directory sync failure")

    monkeypatch.setattr(batch_cli, "_fsync_directory", fail_first_sync)

    assert batch_cli.main(["--trace-output", str(trace_path)]) == 4
    assert calls == 2
    assert trace_path.exists()
    assert json.loads(output.getvalue())["status"] == "proved"
    assert "committed, but its directory sync failed" in errors.getvalue()
    assert list(tmp_path.glob("*.partial")) == []


@pytest.mark.parametrize("interruption", (KeyboardInterrupt(), SystemExit(23)))
def test_control_flow_interruptions_propagate_without_publishing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    interruption: BaseException,
) -> None:
    trace_path = tmp_path / "must-not-exist.jsonl"
    output, errors = _install_text_stdio(monkeypatch, _request() + "\n")

    def interrupt(*_args, **_kwargs):
        raise interruption

    monkeypatch.setattr(batch_cli, "execute_request", interrupt)
    with pytest.raises(type(interruption)) as caught:
        batch_cli.main(["--trace-output", str(trace_path)])

    if isinstance(interruption, SystemExit):
        assert caught.value.code == 23
    assert output.getvalue() == ""
    assert errors.getvalue() == ""
    assert not trace_path.exists()
    assert list(tmp_path.glob("*.partial")) == []


@pytest.mark.parametrize("interruption", (KeyboardInterrupt(), SystemExit(29)))
def test_interruption_after_trace_link_preserves_only_the_complete_commit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    interruption: BaseException,
) -> None:
    trace_path = tmp_path / "committed.jsonl"
    output, errors = _install_text_stdio(monkeypatch, _request() + "\n")
    publish = batch_cli._publish_trace_stage

    def link_then_interrupt(stage: Path, target: Path) -> None:
        publish(stage, target)
        raise interruption

    monkeypatch.setattr(batch_cli, "_publish_trace_stage", link_then_interrupt)
    with pytest.raises(type(interruption)) as caught:
        batch_cli.main(["--trace-output", str(trace_path)])

    if isinstance(interruption, SystemExit):
        assert caught.value.code == 29
    assert output.getvalue() == ""
    assert errors.getvalue() == ""
    records = [json.loads(line) for line in trace_path.read_text().splitlines()]
    assert records[-1]["qed"] is True
    assert records[-1]["tactic_count"] == 1
    assert list(tmp_path.glob("*.partial")) == []


def test_require_proved_changes_only_exit_policy_not_canonical_result() -> None:
    request = json.dumps(
        {
            "v": 1,
            "id": "open",
            "theorem": "forall n. n = n",
            "tactics": ["intro n"],
        },
        separators=(",", ":"),
    ) + "\n"
    ordinary = _run_cli("--verify-only", input_text=request)
    strict = _run_cli("--verify-only", "--require-proved", input_text=request)

    assert ordinary.returncode == 0
    assert strict.returncode == 1
    assert ordinary.stderr == strict.stderr == ""
    assert ordinary.stdout == strict.stdout
    assert json.loads(strict.stdout)["status"] == "open"


def test_require_proved_accepts_a_fully_proved_batch() -> None:
    completed = _run_cli(
        "--verify-only",
        "--require-proved",
        input_text=_request() + "\n",
    )
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["status"] == "proved"
