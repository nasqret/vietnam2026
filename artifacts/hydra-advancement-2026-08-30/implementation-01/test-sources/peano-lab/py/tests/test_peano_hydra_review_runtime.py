"""Owned resource guards do not invoke models or leave runaway children."""

import base64
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import signal
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra.review_runtime import (  # noqa: E402
    RESOURCE_MEASUREMENT, ProcessLimits, ReviewRuntimeError, hash_file, run_bounded,
    validate_process_record,
)


COMMAND = (sys.executable, "-c", "print('proof')")
LIMITS = ProcessLimits(wall_seconds=2, cpu_seconds=1, rss_bytes=128 * 1024**2, output_bytes=128)
INPUT = b"exact request\n"


def _record(*, stdout=b"proof\n", stderr=b"", limits=LIMITS):
    return {
        "command": list(COMMAND), "limits": limits.to_dict(),
        "stdin_bytes": len(INPUT), "stdin_sha256": hashlib.sha256(INPUT).hexdigest(),
        "returncode": 0, "reason": "exited", "stdout": stdout.decode(), "stderr": stderr.decode(),
        "output_encoding": "utf-8", "raw_output_base64": None, "output_truncated": False,
        "stdout_bytes": len(stdout), "stderr_bytes": len(stderr),
        "stdout_sha256": hashlib.sha256(stdout).hexdigest(), "stderr_sha256": hashlib.sha256(stderr).hexdigest(),
        "resources": {"wall_seconds": 0.5, "cpu_seconds": 0.2, "peak_rss_bytes": 16 * 1024**2,
                      "sampled_peak_group_rss_bytes": 15 * 1024**2, "cpu_instructions": None, "energy_joules": None},
        "observed_descendant_count": 0, "resource_measurement": RESOURCE_MEASUREMENT,
    }


def _invalid_encoding_record(*, stdout=b"\xff", stderr=b"", limits=LIMITS):
    result = _record(stdout=b"", stderr=b"", limits=limits)
    result.update(reason="invalid_output_encoding", output_encoding="invalid-utf8-base64-preserved",
                  raw_output_base64={"stdout": base64.b64encode(stdout).decode("ascii"),
                                     "stderr": base64.b64encode(stderr).decode("ascii")},
                  stdout_bytes=len(stdout), stderr_bytes=len(stderr),
                  stdout_sha256=hashlib.sha256(stdout).hexdigest(), stderr_sha256=hashlib.sha256(stderr).hexdigest())
    return result


def _validate(record, **options):
    validate_process_record(record, command=COMMAND, limits=LIMITS, input_bytes=INPUT, **options)


@pytest.mark.parametrize("values", [
    {"cpu_seconds": True}, {"rss_bytes": 1}, {"wall_seconds": 0},
    {"output_bytes": 10**9}, {"cpu_seconds": 121},
    {"wall_seconds": 1, "cpu_seconds": 2},
])
def test_process_limits_fail_closed(values) -> None:
    with pytest.raises(ReviewRuntimeError):
        ProcessLimits(**values)


def test_owned_child_accounts_resources_and_exact_output(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("LEAN_PATH", "/not-an-approved-reference")
    result = run_bounded(
        (sys.executable, "-c", "import os; print(os.environ.get('LEAN_PATH', 'isolated'))"),
        cwd=tmp_path, limits=ProcessLimits(),
    )
    assert result["returncode"] == 0 and result["reason"] == "exited"
    assert result["stdout"] == "isolated\n" and result["stderr"] == ""
    assert result["resources"]["peak_rss_bytes"] > 0
    assert result["resources"]["cpu_seconds"] > 0
    assert result["resources"]["cpu_instructions"] is None


def test_worker_strips_all_dynamic_loader_environment_without_changing_parent(tmp_path, monkeypatch) -> None:
    loader_names = (
        "LD_PRELOAD", "LD_LIBRARY_PATH", "LD_AUDIT", "LD_DEBUG", "LD_REVIEW_FUTURE_OVERRIDE", "LD_",
        "DYLD_INSERT_LIBRARIES", "DYLD_LIBRARY_PATH", "DYLD_FRAMEWORK_PATH",
        "DYLD_FALLBACK_LIBRARY_PATH", "DYLD_REVIEW_FUTURE_OVERRIDE", "DYLD_",
    )
    for name in loader_names:
        monkeypatch.setenv(name, "unreviewed-loader-setting")
    monkeypatch.setenv("HYDRA_LD_LIBRARY_PATH", "unrelated-setting")
    captured = {}

    def capture_launch(*args, **kwargs):
        captured.update(kwargs["env"])
        raise RuntimeError("environment captured before process launch")

    monkeypatch.setattr("training.peano_hydra.review_runtime.subprocess.Popen", capture_launch)
    with pytest.raises(RuntimeError, match="environment captured before process launch"):
        run_bounded(COMMAND, cwd=tmp_path, limits=LIMITS)
    assert not any(name.startswith(("LD_", "DYLD_")) for name in captured)
    assert captured["HYDRA_LD_LIBRARY_PATH"] == "unrelated-setting"
    assert all(os.environ[name] == "unreviewed-loader-setting" for name in loader_names)


def test_nonzero_reference_rejection_is_not_an_inferred_success(tmp_path) -> None:
    result = run_bounded((sys.executable, "-c", "raise SystemExit(2)"),
                         cwd=tmp_path, limits=ProcessLimits())
    assert result["returncode"] == 2 and result["reason"] == "exited"


def test_normal_exit_cleans_up_and_rejects_an_owned_descendant(tmp_path) -> None:
    program = (
        "import subprocess,sys; "
        "p=subprocess.Popen([sys.executable,'-c','import time; time.sleep(10)']); "
        "print(p.pid,flush=True)"
    )
    result = run_bounded((sys.executable, "-c", program), cwd=tmp_path, limits=ProcessLimits())
    assert result["reason"] == "unexpected_descendant"
    assert result["observed_descendant_count"] >= 1
    assert result["resources"]["wall_seconds"] < 4


def test_own_wall_limited_worker_is_terminated_and_measured(tmp_path) -> None:
    result = run_bounded((sys.executable, "-c", "import time; time.sleep(10)"),
                         cwd=tmp_path, limits=ProcessLimits(wall_seconds=1, cpu_seconds=1))
    assert result["reason"] == "wall_limit" and result["returncode"] < 0
    assert 1 <= result["resources"]["wall_seconds"] < 4
    assert result["resources"]["peak_rss_bytes"] > 0


def test_output_flood_is_never_retained_without_a_bound(tmp_path) -> None:
    result = run_bounded((sys.executable, "-c", "print('x' * 10000)"),
                         cwd=tmp_path, limits=ProcessLimits(output_bytes=128))
    assert result["reason"] == "output_limit"
    assert len(result["stdout"].encode()) <= 128
    assert result["stdout_bytes"] > 128


def test_malformed_output_encoding_is_rejected_with_exact_bytes_retained(tmp_path) -> None:
    result = run_bounded((sys.executable, "-c", "import os; os.write(1,bytes([255]))"),
                         cwd=tmp_path, limits=ProcessLimits())
    assert result["reason"] == "invalid_output_encoding"
    assert result["stdout"] == "" and result["raw_output_base64"]["stdout"] == "/w=="
    assert result["output_truncated"] is False


@pytest.mark.parametrize("command", [("python3", "-V"), (), (sys.executable, "\x00")])
def test_commands_must_be_shell_free_bounded_and_explicit(command, tmp_path) -> None:
    with pytest.raises(ReviewRuntimeError):
        run_bounded(command, cwd=tmp_path, limits=ProcessLimits())


def test_hash_input_requires_bounded_regular_nonsymlink_file(tmp_path) -> None:
    source = tmp_path / "source"
    source.write_bytes(b"proof")
    assert hash_file(source)["bytes"] == 5
    with pytest.raises(ReviewRuntimeError):
        hash_file(source, maximum=4)
    link = tmp_path / "link"
    link.symlink_to(source)
    with pytest.raises(OSError):
        hash_file(link)


def test_exact_detached_process_receipt_passes_without_modification() -> None:
    record = _record()
    before = deepcopy(record)
    _validate(record)
    _validate(record, success_codes=(0,))
    assert record == before
    record["returncode"] = 2
    _validate(record, success_codes=(0, 1, 2))
    with pytest.raises(ReviewRuntimeError, match="successful exit"):
        _validate(record, success_codes=(0,))


@pytest.mark.parametrize(("path", "value"), [
    ("command", tuple(COMMAND)), ("command", [sys.executable, "-c", "different"]),
    ("limits.wall_seconds", True), ("limits.wall_seconds", 2.0), ("limits.cpu_seconds", 2),
    ("stdin_bytes", True), ("stdin_bytes", 0), ("stdin_bytes", float(len(INPUT))),
    ("stdin_sha256", "0" * 64), ("stdin_sha256", "A" * 64), ("stdin_sha256", None),
    ("returncode", True), ("returncode", 0.0), ("returncode", None),
    ("returncode", -128), ("returncode", 256),
    ("reason", "success"), ("reason", []), ("reason", None),
    ("stdout", b"proof\n"), ("stdout", "proof\nchanged"), ("stdout", "\ud800"),
    ("stderr", "hidden"), ("output_encoding", "UTF-8"), ("output_encoding", None),
    ("raw_output_base64", {}), ("raw_output_base64", {"stdout": "", "stderr": ""}),
    ("output_truncated", 0), ("output_truncated", True),
    ("stdout_bytes", 0), ("stdout_bytes", -1), ("stdout_bytes", True), ("stdout_bytes", 2**63),
    ("stderr_bytes", 1), ("stderr_bytes", 0.0),
    ("stdout_sha256", "0" * 64), ("stderr_sha256", True),
    ("resources.wall_seconds", -0.1), ("resources.wall_seconds", float("nan")),
    ("resources.cpu_seconds", float("inf")), ("resources.cpu_seconds", True),
    ("resources.cpu_seconds", "0.2"), ("resources.cpu_seconds", 10**1000),
    ("resources.peak_rss_bytes", -1), ("resources.peak_rss_bytes", 1.0),
    ("resources.peak_rss_bytes", None), ("resources.peak_rss_bytes", 2**63),
    ("resources.sampled_peak_group_rss_bytes", False), ("resources.sampled_peak_group_rss_bytes", -1),
    ("resources.sampled_peak_group_rss_bytes", float("nan")),
    ("resources.cpu_instructions", 0), ("resources.cpu_instructions", False),
    ("resources.energy_joules", 0.0), ("resources.energy_joules", "unmeasured"),
    ("observed_descendant_count", True), ("observed_descendant_count", -1),
    ("observed_descendant_count", 1), ("resource_measurement", "estimated"),
])
def test_strict_process_record_mutations_fail_closed(path, value) -> None:
    record = _record()
    owner = record
    parts = path.split(".")
    for part in parts[:-1]:
        owner = owner[part]
    owner[parts[-1]] = value
    with pytest.raises(ReviewRuntimeError):
        _validate(record)


def test_missing_unknown_and_nested_fields_fail_closed() -> None:
    for field in _record():
        record = _record()
        del record[field]
        with pytest.raises(ReviewRuntimeError, match="fields"):
            _validate(record)
    for container in (None, "limits", "resources"):
        record = _record()
        owner = record if container is None else record[container]
        owner["unknown"] = 0
        with pytest.raises(ReviewRuntimeError):
            _validate(record)
    record = _record()
    del record["resources"]["energy_joules"]
    with pytest.raises(ReviewRuntimeError, match="resource fields"):
        _validate(record)


def test_caller_owned_extra_fields_are_required_and_contents_are_not_reinterpreted() -> None:
    record = _record()
    record.update(module="PeanoLab/Codec.lean", compiled_olean={"caller-owned": True})
    _validate(record, extra_fields=("module", "compiled_olean"), success_codes=(0,))
    with pytest.raises(ReviewRuntimeError, match="fields"):
        _validate(record)
    with pytest.raises(ReviewRuntimeError, match="fields"):
        _validate(record, extra_fields=("module", "compiled_olean", "missing"))


@pytest.mark.parametrize("fields", [["module"], ("command",), ("module", "module"),
                                   ("bad\nfield",), ("",), (1,), ([],), None])
def test_extra_field_contract_itself_is_exact(fields) -> None:
    with pytest.raises(ReviewRuntimeError):
        _validate(_record(), extra_fields=fields)


@pytest.mark.parametrize("codes", [[], (), [0], (True,), (0.0,), (-9,), (256,), (0, 0), ([],), "0"])
def test_success_codes_are_exact_normal_exit_codes(codes) -> None:
    with pytest.raises(ReviewRuntimeError):
        _validate(_record(), success_codes=codes)


def test_signal_exit_is_an_observation_but_cannot_be_declared_success() -> None:
    record = _record()
    record["returncode"] = -signal.SIGTERM
    _validate(record)
    with pytest.raises(ReviewRuntimeError, match="successful exit"):
        _validate(record, success_codes=(0,))
    record["returncode"] = -signal.SIGXCPU
    with pytest.raises(ReviewRuntimeError, match="ordinary exit"):
        _validate(record)
    record["reason"] = "cpu_limit"
    _validate(record)  # SIGXCPU is meaningful even at a rounded/below-limit CPU reading.


@pytest.mark.parametrize(("field", "value"), [
    ("wall_seconds", LIMITS.wall_seconds + 0.01),
    ("cpu_seconds", LIMITS.cpu_seconds + 0.01),
    ("peak_rss_bytes", LIMITS.rss_bytes + 1),
    ("sampled_peak_group_rss_bytes", LIMITS.rss_bytes + 1),
])
def test_normal_exits_must_respect_every_declared_resource_ceiling(field, value) -> None:
    record = _record()
    record["resources"][field] = value
    with pytest.raises(ReviewRuntimeError, match="ordinary exit"):
        _validate(record)


@pytest.mark.parametrize(("reason", "changes"), [
    ("wall_limit", {"wall_seconds": LIMITS.wall_seconds + 0.1, "cpu_seconds": LIMITS.cpu_seconds + 0.1}),
    ("cpu_limit", {"cpu_seconds": LIMITS.cpu_seconds + 0.1, "wall_seconds": LIMITS.wall_seconds + 0.1}),
    ("rss_limit", {"peak_rss_bytes": LIMITS.rss_bytes + 10 * 1024**2}),
    ("rss_limit", {"sampled_peak_group_rss_bytes": LIMITS.rss_bytes + 1}),
])
def test_failure_receipts_preserve_legitimate_limit_overshoot(reason, changes) -> None:
    record = _record()
    record.update(reason=reason, returncode=-signal.SIGKILL)
    record["resources"].update(changes)
    _validate(record)
    with pytest.raises(ReviewRuntimeError, match="successful exit"):
        _validate(record, success_codes=(0,))


@pytest.mark.parametrize("reason", ["wall_limit", "cpu_limit", "rss_limit", "output_limit",
                                   "unexpected_descendant", "invalid_output_encoding"])
def test_failure_reason_requires_corresponding_observed_evidence(reason) -> None:
    record = _record()
    record["reason"] = reason
    with pytest.raises(ReviewRuntimeError):
        _validate(record)


def test_unobserved_rss_sample_is_null_not_an_invented_peak() -> None:
    record = _record()
    record["resources"]["sampled_peak_group_rss_bytes"] = None
    _validate(record, success_codes=(0,))
    record.update(reason="unexpected_descendant", observed_descendant_count=2)
    _validate(record)
    with pytest.raises(ReviewRuntimeError, match="successful exit"):
        _validate(record, success_codes=(0,))


def test_output_limit_hashes_retained_prefix_not_the_unretained_stream() -> None:
    record = _record(stdout=b"x" * LIMITS.output_bytes)
    record.update(reason="output_limit", stdout_bytes=10**8, output_truncated=True)
    _validate(record)
    with pytest.raises(ReviewRuntimeError, match="successful exit"):
        _validate(record, success_codes=(0,))
    for changed in (
        {"output_truncated": False}, {"reason": "wall_limit"},
        {"stdout_bytes": LIMITS.output_bytes - 1}, {"stdout": "x" * (LIMITS.output_bytes - 1)},
        {"stdout_sha256": hashlib.sha256(b"x" * (LIMITS.output_bytes + 1)).hexdigest()},
    ):
        with pytest.raises(ReviewRuntimeError):
            _validate({**record, **changed})


@pytest.mark.parametrize(("stdout", "stderr"), [(b"\xff", b""), (b"valid\n", b"\xfe"), (b"\xc2", b"\xff")])
def test_invalid_utf8_preserves_both_exact_retained_streams(stdout, stderr) -> None:
    record = _invalid_encoding_record(stdout=stdout, stderr=stderr)
    _validate(record)
    with pytest.raises(ReviewRuntimeError, match="successful exit"):
        _validate(record, success_codes=(0,))


@pytest.mark.parametrize("changes", [
    {"reason": "output_limit"}, {"stdout": "replacement characters"},
    {"raw_output_base64": {"stdout": "/w=="}},
    {"raw_output_base64": {"stdout": "/w==", "stderr": "", "other": ""}},
    {"raw_output_base64": {"stdout": "/w==\n", "stderr": ""}},
    {"raw_output_base64": {"stdout": "/x==", "stderr": ""}},  # nonzero unused padding bits
    {"raw_output_base64": {"stdout": "_w==", "stderr": ""}},
    {"raw_output_base64": {"stdout": "🙂", "stderr": ""}},
    {"raw_output_base64": {"stdout": 1, "stderr": ""}},
    {"raw_output_base64": {"stdout": "", "stderr": ""}},
    {"stdout_bytes": 2}, {"stdout_sha256": "0" * 64},
])
def test_invalid_utf8_fallback_cannot_hide_noncanonical_or_unbound_bytes(changes) -> None:
    with pytest.raises(ReviewRuntimeError):
        _validate({**_invalid_encoding_record(), **changes})


def test_base64_failure_label_requires_at_least_one_invalid_utf8_stream() -> None:
    record = _invalid_encoding_record(stdout=b"valid text", stderr=b"")
    with pytest.raises(ReviewRuntimeError, match="any invalid UTF-8"):
        _validate(record)


def test_output_cut_inside_utf8_codepoint_is_preserved_not_repaired() -> None:
    tiny = ProcessLimits(wall_seconds=2, cpu_seconds=1, rss_bytes=128 * 1024**2, output_bytes=1)
    record = _invalid_encoding_record(stdout="€".encode()[:1], limits=tiny)
    record.update(stdout_bytes=3, output_truncated=True)
    validate_process_record(record, command=COMMAND, limits=tiny, input_bytes=INPUT)
    assert record["raw_output_base64"]["stdout"] == "4g=="


@pytest.mark.parametrize("changed_input", [b"different request\n", b"", "exact request\n", bytearray(INPUT)])
def test_stdin_binding_uses_exact_bytes_not_similar_text(changed_input) -> None:
    with pytest.raises(ReviewRuntimeError):
        validate_process_record(_record(), command=COMMAND, limits=LIMITS, input_bytes=changed_input)


@pytest.mark.parametrize("command", [list(COMMAND), ("python3",), (sys.executable, "\ud800"),
                                     (sys.executable, ""), (sys.executable, "\x00"), (), None])
def test_validator_request_contract_rejects_malformed_commands(command) -> None:
    with pytest.raises(ReviewRuntimeError):
        validate_process_record(_record(), command=command, limits=LIMITS, input_bytes=INPUT)


def test_validator_request_requires_exact_limits_instance() -> None:
    with pytest.raises(ReviewRuntimeError):
        validate_process_record(_record(), command=COMMAND, limits=LIMITS.to_dict(), input_bytes=INPUT)


def test_real_worker_round_trips_and_binds_binary_stdin(tmp_path) -> None:
    command = (sys.executable, "-c", "import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())")
    payload = "proof\x00β\n".encode()
    limits = ProcessLimits()
    record = run_bounded(command, cwd=tmp_path, limits=limits, input_bytes=payload)
    validate_process_record(record, command=command, limits=limits, input_bytes=payload, success_codes=(0,))
    assert record["stdin_bytes"] == len(payload)
    assert record["stdin_sha256"] == hashlib.sha256(payload).hexdigest()
    assert record["stdout"].encode() == payload
    with pytest.raises(ReviewRuntimeError, match="stdin"):
        validate_process_record(record, command=command, limits=limits, input_bytes=payload + b"x")


def test_real_sigxcpu_worker_is_valid_failure_evidence_not_success(tmp_path) -> None:
    command = (sys.executable, "-c", "while True:\n    pass")
    limits = ProcessLimits(wall_seconds=4, cpu_seconds=1)
    record = run_bounded(command, cwd=tmp_path, limits=limits)
    assert record["reason"] == "cpu_limit"
    assert record["returncode"] < 0
    validate_process_record(record, command=command, limits=limits)
    with pytest.raises(ReviewRuntimeError, match="successful exit"):
        validate_process_record(record, command=command, limits=limits, success_codes=(0,))


def test_real_truncated_multibyte_output_retains_raw_prefix_and_full_count(tmp_path) -> None:
    command = (sys.executable, "-c", "import os; os.write(1,'€'.encode('utf-8'))")
    limits = ProcessLimits(output_bytes=1)
    record = run_bounded(command, cwd=tmp_path, limits=limits)
    assert record["reason"] == "invalid_output_encoding"
    assert record["output_truncated"] is True and record["stdout_bytes"] == 3
    assert record["raw_output_base64"]["stdout"] == "4g=="
    assert record["stdout_sha256"] == hashlib.sha256("€".encode()[:1]).hexdigest()
    validate_process_record(record, command=command, limits=limits)
