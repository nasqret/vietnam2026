"""Small local delivery regressions; synthetic files/HTTP, no proof runtime."""
from hashlib import sha256
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_constructive_delivery_v35 as check


def pin(raw):
    return dict(bytes=len(raw), sha256=sha256(raw).hexdigest())


@pytest.fixture
def stage(tmp_path, monkeypatch):
    root = tmp_path / "stage"
    names = set(check.SAMPLES) | {"jordan-totient/index.html", "changed-not-a-sample.html"}
    files = {}
    for name in names:
        raw = ("synthetic delivery only: " + name).encode()
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        files[name] = pin(raw)
    value = dict(schema="peano-lab-alpha-v35-public-delivery-v1", delivery_metadata_only=True,
        alpha_admission_performed=False, stable_admission_performed=False, public_on_demand_builds=False,
        current_alpha_version="v35", current_alpha_checked_use_count=4318, stable_count=432,
        new_theorem_count=95, source_owned_theorem_count=96, source_alias_count=1, family_count=69,
        current_G008_proved=True, current_G091_proved=False, distinct_prime_product_formula_proved=False,
        current_files=files, current_file_count=len(files),
        additions={"jordan-totient/index.html": files["jordan-totient/index.html"]},
        changed_files={"changed-not-a-sample.html": dict(before=pin(b"old"), after=files["changed-not-a-sample.html"])})
    path = root / check.MANIFEST
    path.parent.mkdir()
    raw = json.dumps(value).encode()
    path.write_bytes(raw)
    monkeypatch.setattr(check, "ROOT", tmp_path)
    monkeypatch.setattr(check, "STAGE", root)
    monkeypatch.setattr(check, "source_binding", lambda: {"sha256": "b"*64, "files": {}})
    return root, sha256(raw).hexdigest(), value


def test_required_alias_reading_assets_and_changed_routes(stage):
    _, accepted, value = stage
    files, names = check.snapshot(accepted)
    assert set(names) == set(value["current_files"]) | {check.MANIFEST}
    assert len(files) == len(names)
    assert "integer-linear-algebra/explorer/defined/tag/DL0071.html" in names
    assert {"assets/defined-explorer.css", "assets/exact-explorer.css",
            "assets/proof-reader.css", "assets/proof-reader.js"} <= set(names)
    assert "changed-not-a-sample.html" in names
    assert "bertrand-postulate/index.html" in names and "bertrand/index.html" not in names


@pytest.mark.parametrize("key,bad", [("stable_count", 433), ("new_theorem_count", 96),
    ("current_G091_proved", True), ("public_on_demand_builds", True),
    ("delivery_metadata_only", False), ("current_file_count", 1)])
def test_wrong_scope_rejected_even_with_matching_digest(stage, key, bad):
    root, _, value = stage
    value[key] = bad
    raw = json.dumps(value).encode()
    (root / check.MANIFEST).write_bytes(raw)
    with pytest.raises(ValueError): check.snapshot(sha256(raw).hexdigest())


@pytest.mark.parametrize("variant", ["wrong_digest", "body", "file_link", "directory_link", "oversized"])
def test_local_read_rejections(stage, monkeypatch, variant):
    root, accepted, _ = stage
    path = root / "index.html"
    if variant == "wrong_digest":
        with pytest.raises(ValueError): check.snapshot("0"*64)
        return
    files, _ = check.snapshot(accepted)
    if variant == "body": path.write_bytes(b"changed")
    elif variant == "file_link":
        target = root / "target.html"
        path.rename(target)
        path.symlink_to(target.name)
    elif variant == "directory_link":
        linked = root.parent / "linked"
        linked.symlink_to(root, target_is_directory=True)
        monkeypatch.setattr(check, "STAGE", linked)
    else:
        with pytest.raises(ValueError): check.read_file(path, 1)
        return
    with pytest.raises((OSError, ValueError)): check.selected_snapshot(files, ["index.html"])


def test_read_uses_nonblocking_no_follow_and_detects_changed_input(stage, monkeypatch):
    root, _, _ = stage
    original_open = check.os.open
    flags_seen = []
    def opened(path, flags, *args, **kwargs):
        flags_seen.append(flags)
        return original_open(path, flags, *args, **kwargs)
    monkeypatch.setattr(check.os, "open", opened)
    check.read_file(root / "index.html", check.transport.MAX_FILE)
    required = check.os.O_NOFOLLOW | check.os.O_NONBLOCK | check.os.O_CLOEXEC
    assert flags_seen and all(flags & required == required for flags in flags_seen)
    ordinary, calls = check.transport.ordinary, 0
    def changed(path, **kwargs):
        nonlocal calls
        if path == root / "index.html":
            calls += 1
            if calls == 2: path.write_bytes(b"changed during read")
        return ordinary(path, **kwargs)
    monkeypatch.setattr(check.transport, "ordinary", changed)
    with pytest.raises(ValueError, match="changed"):
        check.read_file(root / "index.html", check.transport.MAX_FILE)


def test_source_binding_pins_both_checkers_and_tests_without_runtime_imports():
    result = check.source_binding()
    assert set(result["files"]) == {"scripts/" + name for name in (
        "check_constructive_delivery_v35.py", "test_check_constructive_delivery_v35.py",
        "check_constructive_delivery_v34.py", "test_check_constructive_delivery_v34.py")}
    assert result["sha256"] == check.transport.digest_value(result["files"])


def fake_success(row, expected, accepted, deadline, stop):
    assert not stop.is_set()
    assert row["https_path"] == "/proofs/" + row["stage_relative_path"]
    assert deadline > check.monotonic()
    return dict(passed=True, stage_relative_path=row["stage_relative_path"], expected=expected)


def test_all_batches_account_exactly_with_fake_http(stage, monkeypatch):
    _, accepted, _ = stage
    monkeypatch.setattr(check.transport, "fetch", fake_success)
    _, names = check.snapshot(accepted)
    observed = []
    for batch in range(1, (len(names)+15)//16 + 1):
        result = check.run_batch(batch, accepted)
        assert result["passed"] and result["not_completed_count"] == 0
        assert result["request_count"] == result["successful_requests"]
        assert result["stage_before"] == result["stage_after"]
        assert result["proof_authority"] is result["stage_authority"] is False
        observed.extend(row["stage_relative_path"] for row in result["requests"])
    assert observed == names


def test_timeout_preserves_partial_receipt_and_never_waits_for_executor(stage, monkeypatch):
    _, accepted, _ = stage
    futures, stops, shutdowns = [], [], []
    class Future:
        cancelled = False
        def result(self, timeout):
            assert timeout > 0
            if self is futures[0]: return {"passed": True}
            raise TimeoutError("synthetic deadline")
        def cancel(self): self.cancelled = True
    class Executor:
        def __init__(self, max_workers): assert max_workers == 4
        def submit(self, function, *args):
            stops.append(args[-1])
            future = Future()
            futures.append(future)
            return future
        def shutdown(self, **kwargs): shutdowns.append(kwargs)
    monkeypatch.setattr(check, "ThreadPoolExecutor", Executor)
    result = check.run_batch(1, accepted)
    assert not result["passed"] and "synthetic deadline" in result["failure"]
    assert result["request_count"] == result["successful_requests"] == 1
    assert result["not_completed_count"] == 15
    assert all(future.cancelled for future in futures) and all(stop.is_set() for stop in stops)
    assert shutdowns == [{"wait": False, "cancel_futures": True}]


def test_completed_responses_cannot_pass_after_batch_deadline(stage, monkeypatch):
    _, accepted, _ = stage
    now = 0
    monkeypatch.setattr(check, "monotonic", lambda: now)
    calls = 0
    def binding():
        nonlocal calls, now
        calls += 1
        if calls == 2: now = 91
        return {"sha256": "b"*64, "files": {}}
    monkeypatch.setattr(check, "source_binding", binding)
    monkeypatch.setattr(check.transport, "fetch", fake_success)
    result = check.run_batch(1, accepted)
    assert not result["passed"] and "exceeded90seconds" in result["failure"]
    assert result["request_count"] == result["successful_requests"] == 16


@pytest.mark.parametrize("mutation", ["stage", "source"])
def test_changed_inputs_fail_even_after_successful_http(stage, monkeypatch, mutation):
    root, accepted, _ = stage
    if mutation == "source":
        calls = 0
        def changed_binding():
            nonlocal calls
            calls += 1
            return {"sha256": str(calls), "files": {}}
        monkeypatch.setattr(check, "source_binding", changed_binding)
        monkeypatch.setattr(check.transport, "fetch", fake_success)
    else:
        def changed_body(*args):
            result = fake_success(*args)
            (root / args[0]["stage_relative_path"]).write_bytes(b"changed after HTTP")
            return result
        monkeypatch.setattr(check.transport, "fetch", changed_body)
    result = check.run_batch(1, accepted)
    assert not result["passed"] and result["failure"]


def test_main_arms_and_restores_alarm_and_writes_failed_receipt(stage, monkeypatch, tmp_path):
    _, accepted, _ = stage
    alarms, handlers = [], []
    previous = object()
    def handler(number, callback):
        handlers.append((number, callback))
        return previous
    monkeypatch.setattr(check.signal, "signal", handler)
    monkeypatch.setattr(check.signal, "alarm", alarms.append)
    monkeypatch.setattr(check, "run_batch", lambda *args: {"passed": False, "requests": [], "failure": "test"})
    output = tmp_path / "failed.json"
    args = ["--accepted-stage-manifest-sha256", accepted, "--batch", "1", "--output", str(output)]
    assert check.main(args) == 1
    assert json.loads(output.read_bytes())["failure"] == "test"
    assert alarms == [90, 0] and handlers[-1] == (check.signal.SIGALRM, previous)
    with pytest.raises(TimeoutError, match="hard90second"):
        handlers[0][1]()
    with pytest.raises(FileExistsError): check.main(args)
