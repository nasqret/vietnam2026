"""Render transport tests only; synthetic files are never proof evidence.

The real positive explorer suite must inherit the reports of all twenty-one
actual proof jobs. These fixtures exercise the subsequent private IPC and file
boundary with explicitly labelled, non-verified data. No proof checker is
replaced by an accepting mock, and no receipt is read as proof authority.
"""

from copy import deepcopy
from hashlib import sha256
import ast
import errno
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import build_constructive_dirichlet_explorer as build


NONCE = "1" * 64
BINDING = "2" * 64
TRANSPORT_REPORT = {"transport_only": True, "proofs_verified": False}


def _info(payload):
    return {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}


def _manifest(files):
    return {
        "schema": build.SCHEMA + "-manifest",
        "publication_scope": "local-only-checkpoint",
        "checkpoint_digest": sha256(b"transport-only-not-a-proof-checkpoint").hexdigest(),
        "navigation_revision": build.HTML_REVISION,
        "file_count_excluding_manifest": len(files),
        "files": {name: _info(payload) for name, payload in sorted(files.items())},
    }


def _envelope(files, *, check=False, test=False, write_audit=False):
    return {
        "schema": "peano-lab-dirichlet-fresh-render-v1",
        "nonce": NONCE, "binding_sha256": BINDING,
        "limits": {"cpu": [170, 175], "wall_seconds": 180,
                   "max_rss_bytes": 1536 * 1024 * 1024},
        "peak_rss_bytes": 100,
        "manifest": _info(files["manifest.json"]),
        "proof_audit": _info(files["proof-audit.json"]),
        "file_count": len(files), "check": check, "test": test,
        "write_audit": write_audit, "pytest_status": 0 if test else None,
    }


def _validate(payload, *, check=False, test=False, write_audit=False):
    return build._validate_render_message(
        payload, nonce=NONCE, binding=BINDING, report=TRANSPORT_REPORT,
        check=check, test=test, write_audit=write_audit,
    )


@pytest.fixture
def transport_files(tmp_path):
    files = {
        "index.html": b"<!doctype html><title>Transport only, no proof verified</title>\n",
        "proof-audit.json": build.audit.canonical_report(TRANSPORT_REPORT).encode("utf-8"),
        "checkpoints.json": build._json({"transport_only": True, "proofs_verified": False,
                                         "render_source_binding_sha256": BINDING}),
        "nested/plain.txt": b"synthetic render transport fixture\n",
    }
    files["manifest.json"] = build._json(_manifest(files))
    output = tmp_path / "transport-output"
    for name, payload in files.items():
        path = output / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    return SimpleNamespace(output=output, files=files, message=_envelope(files))


@pytest.mark.parametrize("check", (False, True))
@pytest.mark.parametrize("test", (False, True))
@pytest.mark.parametrize("write_audit", (False, True))
def test_exact_transport_flags_and_literal_output_roundtrip_are_not_proof_authority(
        transport_files, check, test, write_audit):
    message = _envelope(transport_files.files, check=check, test=test, write_audit=write_audit)
    result = _validate(build.audit._canonical(message), check=check, test=test, write_audit=write_audit)
    assert result == message
    assert build._read_rendered_files(transport_files.output, message) == transport_files.files
    assert json.loads(transport_files.files["proof-audit.json"]) == TRANSPORT_REPORT
    assert TRANSPORT_REPORT["proofs_verified"] is False


@pytest.mark.parametrize("path,value", (
    (("schema",), "old-render-envelope"), (("nonce",), "3" * 64),
    (("binding_sha256",), "4" * 64), (("limits", "cpu"), [171, 175]),
    (("limits", "wall_seconds"), 181), (("limits", "max_rss_bytes"), 2**31),
    (("peak_rss_bytes",), 0), (("peak_rss_bytes",), True),
    (("peak_rss_bytes",), 1536 * 1024 * 1024 + 1),
    (("manifest", "bytes"), 0), (("manifest", "bytes"), True),
    (("manifest", "sha256"), "0" * 63), (("manifest", "sha256"), "F" * 64),
    (("proof_audit", "bytes"), 1), (("proof_audit", "sha256"), "0" * 64),
    (("file_count",), 0), (("file_count",), True),
    (("check",), True), (("check",), 0), (("test",), "false"),
    (("write_audit",), True), (("pytest_status",), 0),
))
def test_stale_foreign_unbounded_or_wrong_mode_render_envelopes_fail_closed(transport_files, path, value):
    message = deepcopy(transport_files.message)
    target = message
    for name in path[:-1]:
        target = target[name]
    target[path[-1]] = value
    with pytest.raises(build.RenderProcessError):
        _validate(build.audit._canonical(message))


@pytest.mark.parametrize("mutation", ("missing", "extra", "extra_manifest", "extra_audit", "missing_limits"))
def test_render_envelope_has_exact_top_level_and_nested_fields(transport_files, mutation):
    message = deepcopy(transport_files.message)
    if mutation == "missing":
        del message["nonce"]
    elif mutation == "extra":
        message["accepted_from_old_receipt"] = True
    elif mutation == "extra_manifest":
        message["manifest"]["unbounded_path"] = "../other-manifest.json"
    elif mutation == "extra_audit":
        message["proof_audit"]["saved_receipt"] = True
    else:
        del message["limits"]["cpu"]
    with pytest.raises(build.RenderProcessError):
        _validate(build.audit._canonical(message))


@pytest.mark.parametrize("status", (None, False, True, 1, -1, "0"))
def test_requested_snapshot_tests_require_an_exact_success_status(transport_files, status):
    message = _envelope(transport_files.files, test=True)
    message["pytest_status"] = status
    with pytest.raises(build.RenderProcessError):
        _validate(build.audit._canonical(message), test=True)


@pytest.mark.parametrize("payload", (
    b"", b"{}\n", b"[]\n", b"\xff\n", b'{"nonce":1,"nonce":2}\n',
    b'{"value":NaN}\n', b"{}\n{}\n", b"banner\n{}\n", b"x" * 8193,
))
def test_render_pipe_payload_is_canonical_duplicate_free_and_byte_bounded(payload):
    # The shared strict decoder retains its original RuntimeError subtype;
    # neither it nor the local ValueError-derived guard is an acceptance.
    with pytest.raises((build.RenderProcessError, build.audit.AuditWorkerError)):
        _validate(payload)


@pytest.mark.parametrize("mutation", ("content", "append", "truncate", "missing", "extra", "manifest_content", "manifest_missing"))
def test_literal_render_files_are_revalidated_after_the_child_exits(transport_files, mutation):
    output = transport_files.output
    target = output / "index.html"
    if mutation == "content":
        target.write_bytes(b"x" * len(transport_files.files["index.html"]))
    elif mutation == "append":
        target.write_bytes(transport_files.files["index.html"] + b"extra")
    elif mutation == "truncate":
        target.write_bytes(b"")
    elif mutation == "missing":
        target.unlink()
    elif mutation == "extra":
        (output / "undeclared.txt").write_bytes(b"not in fresh manifest")
    elif mutation == "manifest_content":
        (output / "manifest.json").write_bytes(b"x" * len(transport_files.files["manifest.json"]))
    else:
        (output / "manifest.json").unlink()
    # Literal pin failures retain the unchanged closure's ValueError subtype.
    with pytest.raises(ValueError):
        build._read_rendered_files(output, transport_files.message)


@pytest.mark.parametrize("path", ("../outside.txt", "/absolute.txt", "folder/../outside.txt", "./index.html", "folder\\outside.txt", "folder//file.txt", ""))
def test_manifest_paths_cannot_escape_or_alias_the_owned_output(transport_files, path):
    manifest = json.loads(transport_files.files["manifest.json"])
    manifest["files"][path] = manifest["files"].pop("index.html")
    payload = build._json(manifest)
    (transport_files.output / "manifest.json").write_bytes(payload)
    message = deepcopy(transport_files.message)
    message["manifest"] = _info(payload)
    with pytest.raises(build.RenderProcessError):
        build._read_rendered_files(transport_files.output, message)


@pytest.mark.parametrize("scope", ("output", "manifest", "leaf", "parent"))
def test_rendered_output_rejects_symlinks_at_every_path_component(transport_files, tmp_path, scope):
    output = transport_files.output
    if scope == "output":
        alias = tmp_path / "linked-output"
        alias.symlink_to(output, target_is_directory=True)
        output = alias
    elif scope == "parent":
        parent = output / "nested"
        moved = tmp_path / "moved-nested"
        parent.rename(moved)
        parent.symlink_to(moved, target_is_directory=True)
    else:
        relative = "manifest.json" if scope == "manifest" else "index.html"
        path = output / relative
        moved = tmp_path / ("moved-" + relative)
        path.rename(moved)
        path.symlink_to(moved)
    with pytest.raises(build.RenderProcessError):
        build._read_rendered_files(output, transport_files.message)


@pytest.fixture
def fork_transport(transport_files, tmp_path, monkeypatch):
    """Real fork/pipe/file handling, with a purely synthetic formatter only."""
    report = deepcopy(TRANSPORT_REPORT)
    syntax = {"transport_only_live_object": object()}
    immutable_before = ("transport-only inherited state",)
    parent_pid = os.getpid()
    observation = tmp_path / "child-observation.json"
    test_observation = tmp_path / "requested-test-observation.txt"
    receipt = tmp_path / "final-research-audit.json"

    def format_transport(actual_report, actual_syntax, actual_binding):
        assert actual_report is report and actual_syntax is syntax
        assert actual_binding == BINDING
        assert os.getpid() != parent_pid and os.getpgrp() == os.getpid()
        assert resource.getrlimit(resource.RLIMIT_CPU) == (170, 175)
        remaining, interval = signal.getitimer(signal.ITIMER_REAL)
        assert 0 < remaining <= 180 and interval == 0
        observation.write_text(json.dumps({
            "pid": os.getpid(), "pgid": os.getpgrp(), "parent_pid": parent_pid,
            "cpu": list(resource.getrlimit(resource.RLIMIT_CPU)),
            "wall_alarm_seconds_remaining": remaining,
            "report_object_is_inherited": actual_report is report,
            "syntax_object_is_inherited": actual_syntax is syntax,
            "transport_only": True, "proofs_verified": False,
        }))
        return dict(transport_files.files)

    def transport_test(files, before):
        assert files == transport_files.files and before is immutable_before
        test_observation.write_text("transport callback only, not the real proof/UI suite\n")
        return 0

    monkeypatch.setattr(build, "_render_binding", lambda: BINDING)
    monkeypatch.setattr(build.secrets, "token_hex", lambda size: NONCE if size == 32 else None)
    monkeypatch.setattr(build, "_render_files", format_transport)
    monkeypatch.setattr(build, "_run_snapshot_tests", transport_test)
    monkeypatch.setattr(build.audit, "RECEIPT", receipt)
    return SimpleNamespace(
        report=report, syntax=syntax, immutable_before=immutable_before,
        output=transport_files.output, files=transport_files.files,
        observation=observation, test_observation=test_observation, receipt=receipt,
        parent_pid=parent_pid,
    )


def _fork(fixture, *, check=False, test=False, write_audit=False):
    return build._fork_render_phase(
        fixture.report, fixture.syntax, BINDING, output=fixture.output,
        check=check, test=test, write_audit=write_audit,
        immutable_before=fixture.immutable_before,
    )


@pytest.mark.parametrize("check,test,write_audit", ((False, False, False), (True, False, False), (False, True, True)))
def test_actual_fork_uses_inherited_live_objects_and_unchanged_child_limits(fork_transport, check, test, write_audit):
    result = _fork(fork_transport, check=check, test=test, write_audit=write_audit)
    assert type(result) is build._RenderResult
    assert result.files == fork_transport.files
    assert 0 < result.peak_rss_bytes <= 1536 * 1024 * 1024
    observation = json.loads(fork_transport.observation.read_text())
    assert observation["pid"] == observation["pgid"] != os.getpid()
    assert observation["cpu"] == [170, 175]
    assert observation["report_object_is_inherited"] is observation["syntax_object_is_inherited"] is True
    assert observation["proofs_verified"] is False
    assert fork_transport.test_observation.exists() is test
    # The transport helper cannot publish the parent-owned research receipt,
    # even when the request authenticates a later exclusive parent write.
    assert not fork_transport.receipt.exists()
    with pytest.raises(ChildProcessError):
        os.waitpid(observation["pid"], os.WNOHANG)


@pytest.mark.parametrize("mode", ("nonzero", "signal", "missing_message", "wrong_nonce", "wrong_binding", "oversized", "wrong_audit"))
def test_real_child_failures_cannot_launder_existing_output_or_write_a_final_receipt(fork_transport, monkeypatch, mode):
    original_child = build._render_child
    actual_fork, actual_waitpid = os.fork, os.waitpid
    spawned = []
    fork_transport.receipt.write_bytes(b"older receipt is not a verification input\n")

    def observed_fork():
        pid = actual_fork()
        if pid:
            spawned.append(pid)
        return pid

    def broken_child(report, syntax, binding, **options):
        if mode in ("nonzero", "signal"):
            original_child(report, syntax, binding, **options)
            if mode == "nonzero":
                os._exit(7)
            os.kill(os.getpid(), signal.SIGTERM)
        elif mode == "missing_message":
            return
        elif mode == "oversized":
            os.write(options["write_fd"], b"x" * 8193)
        else:
            message = _envelope(fork_transport.files, write_audit=True)
            if mode == "wrong_nonce":
                message["nonce"] = "3" * 64
            elif mode == "wrong_binding":
                message["binding_sha256"] = "4" * 64
            else:
                message["proof_audit"]["sha256"] = "0" * 64
            os.write(options["write_fd"], build.audit._canonical(message))

    monkeypatch.setattr(build, "_render_child", broken_child)
    monkeypatch.setattr(build.os, "fork", observed_fork)
    # A sandbox permission denial during cleanup is also an explicit failure,
    # never a successful render. It must still leave the exact child reaped.
    with pytest.raises((ValueError, PermissionError)) as error:
        _fork(fork_transport, write_audit=True)
    if isinstance(error.value, PermissionError):
        assert mode == "oversized"
        assert isinstance(error.value.__context__, build.RenderProcessError)
        assert "oversized" in str(error.value.__context__)
    assert len(spawned) == 1
    with pytest.raises(ChildProcessError):
        actual_waitpid(spawned[0], os.WNOHANG)
    assert fork_transport.receipt.read_bytes() == b"older receipt is not a verification input\n"


def test_failed_requested_render_tests_prevent_clean_transport_and_final_receipt(fork_transport, monkeypatch):
    monkeypatch.setattr(build, "_run_snapshot_tests", lambda *args: 1)
    with pytest.raises(build.RenderProcessError, match="exit successfully"):
        _fork(fork_transport, test=True, write_audit=True)
    assert not fork_transport.receipt.exists()


@pytest.mark.parametrize("target", ("manifest.json", "proof-audit.json"))
def test_parent_rechecks_literal_manifest_and_audit_after_clean_child_exit(fork_transport, monkeypatch, target):
    original_child = build._render_child

    def changed_after_message(*args, **kwargs):
        original_child(*args, **kwargs)
        path = fork_transport.output / target
        path.write_bytes(b"x" * path.stat().st_size)

    monkeypatch.setattr(build, "_render_child", changed_after_message)
    with pytest.raises(ValueError):
        _fork(fork_transport, write_audit=True)
    assert not fork_transport.receipt.exists()


def test_parent_rechecks_source_binding_after_successful_child_render(fork_transport, monkeypatch):
    monkeypatch.setattr(build, "_render_binding", lambda: BINDING if os.getpid() != fork_transport.parent_pid else "f" * 64)
    with pytest.raises(build.RenderProcessError, match="sources changed"):
        _fork(fork_transport, write_audit=True)
    assert not fork_transport.receipt.exists()


@pytest.mark.parametrize("descendant", (False, True))
def test_real_timeout_or_abandoned_descendant_cleans_only_the_owned_group(fork_transport, monkeypatch, descendant):
    actual_fork, actual_killpg, actual_waitpid = os.fork, os.killpg, os.waitpid
    spawned, killed = [], []

    def observed_fork():
        pid = actual_fork()
        if pid:
            spawned.append(pid)
        return pid

    def kill_group(pgid, sig):
        killed.append((pgid, sig))
        return actual_killpg(pgid, sig)

    def blocked_child(*args, **kwargs):
        if descendant:
            pid = actual_fork()
            if pid:
                # The grandchild retains the pipe, so even a clean leader
                # exit cannot hide an uncompleted owned process group.
                return
        else:
            # A hostile synthetic child cannot disable the parent's deadline
            # by ignoring its own alarm. No actual formatter does this.
            signal.signal(signal.SIGALRM, signal.SIG_IGN)
        time.sleep(10)
        os._exit(0)

    monkeypatch.setattr(build.os, "fork", observed_fork)
    monkeypatch.setattr(build.os, "killpg", kill_group)
    monkeypatch.setattr(build, "_render_child", blocked_child)
    monkeypatch.setattr(build, "RENDER_WALL_SECONDS", 1)  # Stricter test-only windows.
    monkeypatch.setattr(build, "RENDER_TIMEOUT_SECONDS", 2)
    started = time.monotonic()
    with pytest.raises((ValueError, PermissionError)) as error:
        _fork(fork_transport, write_audit=True)
    if isinstance(error.value, PermissionError):
        assert descendant is False
        assert isinstance(error.value.__context__, build.RenderProcessError)
        assert "bounded window" in str(error.value.__context__)
    assert time.monotonic() - started < 3
    assert len(spawned) == 1 and spawned[0] != os.getpgrp()
    assert killed == [(spawned[0], signal.SIGKILL)]
    with pytest.raises(ChildProcessError):
        actual_waitpid(spawned[0], os.WNOHANG)
    assert not fork_transport.receipt.exists()


def test_completion_that_crosses_the_transport_deadline_is_not_accepted(fork_transport, monkeypatch):
    actual_pipe, actual_read, actual_waitpid = os.pipe, os.read, os.waitpid
    monotonic = time.monotonic
    state = SimpleNamespace(read_fd=None, eof=False, expired=False)

    def pipe():
        pair = actual_pipe()
        state.read_fd = pair[0]
        return pair

    def read(fd, size):
        value = actual_read(fd, size)
        if fd == state.read_fd and value == b"":
            state.eof = True
        return value

    def waitpid(pid, flags):
        if flags == os.WNOHANG and not state.eof:
            return 0, 0
        result = actual_waitpid(pid, flags)
        if result[0]:
            state.expired = True
        return result

    # A deterministic scheduler-boundary regression, with no long sleep and
    # no changed production limit. Only this module sees the test clock.
    monkeypatch.setattr(build.os, "pipe", pipe)
    monkeypatch.setattr(build.os, "read", read)
    monkeypatch.setattr(build.os, "waitpid", waitpid)
    monkeypatch.setattr(build, "time", SimpleNamespace(
        monotonic=lambda: monotonic() + (build.RENDER_TIMEOUT_SECONDS + 1 if state.expired else 0)))
    with pytest.raises(build.RenderProcessError, match="bounded window|deadline"):
        _fork(fork_transport, write_audit=True)
    assert not fork_transport.receipt.exists()


def test_original_limits_and_parent_only_exclusive_receipt_order_are_explicit():
    assert build.RENDER_WALL_SECONDS == 180 and build.RENDER_TIMEOUT_SECONDS == 185
    assert build.MAX_RENDER_MESSAGE_BYTES == 8192
    assert build.CONTROLLER_WALL_SECONDS == build.audit.CONTROLLER_WALL_SECONDS + 185
    assert build.audit.CPU_LIMITS == (170, 175) and build.audit.MAX_RSS_BYTES == 1536 * 1024 * 1024
    tree = ast.parse(Path(build.__file__).read_text())
    functions = {node.name: ast.unparse(node) for node in tree.body if isinstance(node, ast.FunctionDef)}
    child, transport, parent = (functions[name] for name in ("_render_child", "_fork_render_phase", "_build_verified"))
    assert "audit.RECEIPT" not in child and "audit.RECEIPT" not in transport
    assert transport.index("os.setsid()") < transport.index("resource.setrlimit(resource.RLIMIT_CPU, audit.CPU_LIMITS)")
    assert transport.index("signal.alarm(RENDER_WALL_SECONDS)") < transport.index("_render_child(")
    assert "os.killpg(pid, signal.SIGKILL)" in transport
    assert "os.waitpid(pid, os.WNOHANG)" in transport and "os.waitpid(pid, 0)" not in transport
    assert "RENDER_TIMEOUT_SECONDS - RENDER_WALL_SECONDS" in transport
    assert parent.index("audit.verify_in_fresh_windows(syntax_collector=collect)") < parent.index("_validate_fresh_audit(report)")
    assert parent.index("_validate_fresh_audit(report)") < parent.index("_fork_render_phase(")
    assert parent.index("_fork_render_phase(") < parent.index("result.files['proof-audit.json'] != payload")
    assert parent.index("result.files['proof-audit.json'] != payload") < parent.index("audit.RECEIPT.open('xb')")


@pytest.mark.parametrize("arguments", (("--render-report", "old.json"), ("--receipt", "old.json"), ("--worker", "render"), ("--binding", BINDING)))
def test_no_cli_mode_can_render_from_a_saved_receipt_or_foreign_worker_arguments(arguments):
    with pytest.raises(SystemExit) as error:
        build.main(list(arguments))
    assert error.value.code == 2


def test_real_fresh_audit_rejection_prevents_render_and_parent_receipt_creation(tmp_path, monkeypatch):
    receipt = tmp_path / "must-not-exist.json"
    monkeypatch.setattr(build.audit, "RECEIPT", receipt)
    monkeypatch.setattr(build, "_render_binding", lambda: BINDING)
    monkeypatch.setattr(build, "_immutable_test_state", lambda: ("transport-only",))

    def rejected(*args, **kwargs):
        raise build.audit.AuditWorkerError("deliberate fresh audit rejection")

    monkeypatch.setattr(build.audit, "verify_in_fresh_windows", rejected)
    monkeypatch.setattr(build, "_fork_render_phase", lambda *args, **kwargs: pytest.fail("failed proof audit reached rendering"))
    with pytest.raises(build.audit.AuditWorkerError, match="fresh audit rejection"):
        build._build_verified(output=tmp_path / "unused-output", write_audit=True)
    assert not receipt.exists()


@pytest.mark.parametrize("field,value", (("check", 0), ("test", None), ("write_audit", "true")))
def test_invalid_render_flags_are_rejected_before_allocating_a_pipe(fork_transport, monkeypatch, field, value):
    monkeypatch.setattr(build.os, "pipe", lambda: pytest.fail("invalid mode allocated process resources"))
    options = {"check": False, "test": False, "write_audit": False}
    options[field] = value
    with pytest.raises(build.RenderProcessError, match="Booleans"):
        _fork(fork_transport, **options)


def test_fork_failure_closes_both_owned_pipe_descriptors(fork_transport, monkeypatch):
    actual_pipe = os.pipe
    descriptors = []

    def pipe():
        pair = actual_pipe()
        descriptors.extend(pair)
        return pair

    def failed_fork():
        raise OSError("deliberate process creation failure")

    monkeypatch.setattr(build.os, "pipe", pipe)
    monkeypatch.setattr(build.os, "fork", failed_fork)
    with pytest.raises(OSError, match="process creation failure"):
        _fork(fork_transport, write_audit=True)
    assert len(descriptors) == 2
    for descriptor in descriptors:
        with pytest.raises(OSError):
            os.fstat(descriptor)
    assert not fork_transport.receipt.exists()


@pytest.mark.parametrize("mutation", ("noncanonical", "duplicate", "nonfinite", "foreign_scope", "wrong_count", "extra_field"))
def test_authenticated_manifest_still_requires_strict_structure_and_serialization(transport_files, mutation):
    raw = transport_files.files["manifest.json"]
    manifest = json.loads(raw)
    if mutation == "noncanonical":
        payload = json.dumps(manifest).encode()
    elif mutation == "duplicate":
        payload = raw.replace(b"{", b'{"schema":"duplicate schema",', 1)
    elif mutation == "nonfinite":
        payload = raw.replace(b'"file_count_excluding_manifest": 4', b'"file_count_excluding_manifest": NaN')
    else:
        if mutation == "foreign_scope":
            manifest["publication_scope"] = "alpha-admitted"
        elif mutation == "wrong_count":
            manifest["file_count_excluding_manifest"] += 1
        else:
            manifest["accepted_from_receipt"] = True
        payload = build._json(manifest)
    assert payload != raw
    (transport_files.output / "manifest.json").write_bytes(payload)
    message = deepcopy(transport_files.message)
    message["manifest"] = _info(payload)
    with pytest.raises(ValueError):
        build._read_rendered_files(transport_files.output, message)


def test_denied_group_cleanup_is_not_retried_and_still_reaps_the_exact_owned_child(fork_transport, monkeypatch):
    actual_fork, actual_waitpid = os.fork, os.waitpid
    state = SimpleNamespace(spawned=[], denied=[], denial_seen=False)

    def observed_fork():
        pid = actual_fork()
        if pid:
            state.spawned.append(pid)
        return pid

    def defer_reap_until_cleanup(pid, flags):
        if flags == os.WNOHANG and not state.denial_seen:
            return 0, 0
        return actual_waitpid(pid, flags)

    def denied_group(pgid, sig):
        assert state.spawned == [pgid] and sig == signal.SIGKILL
        state.denied.append(pgid)
        state.denial_seen = True
        # This is a simulated denial, not an attempt to repeat or bypass an
        # actual permission restriction. The child has no descendants.
        raise PermissionError(errno.EPERM, "simulated owned-group signal denial")

    def oversized_child(*args, **kwargs):
        os.write(kwargs["write_fd"], b"x" * 8193)

    monkeypatch.setattr(build.os, "fork", observed_fork)
    monkeypatch.setattr(build.os, "waitpid", defer_reap_until_cleanup)
    monkeypatch.setattr(build.os, "killpg", denied_group)
    monkeypatch.setattr(build, "_render_child", oversized_child)
    with pytest.raises(PermissionError, match="simulated owned-group signal denial"):
        _fork(fork_transport, write_audit=True)
    assert len(state.spawned) == 1 and state.denied == state.spawned
    with pytest.raises(ChildProcessError):
        actual_waitpid(state.spawned[0], os.WNOHANG)
    assert not fork_transport.receipt.exists()
