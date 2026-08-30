"""Independent publication IPC/transaction tests, never proof acceptance.

All successful private-transport fixtures contain explicitly synthetic bytes
and a NonAuthorityTransportContext.  They do not create a LiveReleaseContext,
replace a proof checker, or read a receipt as authority.  The real public
entry point is exercised only with its genuine rejecting capability guard.
The positive release/UI gates must use the independently verified live run.
"""

from copy import deepcopy
from dataclasses import dataclass, replace
from hashlib import sha256
import ast
import errno
import inspect
import json
import os
from pathlib import Path
import resource
import signal
import sys
import textwrap
import time
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
for directory in (ROOT / "scripts", ROOT / "peano-lab/py"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
import constructive_alpha_v31_publication_process as process


NONCE = "1" * 64
CATALOG = "2" * 64
BINDING = "3" * 64
PHASES = ("completed", "historical", "atlas")
RSS_LIMIT = 1536 * 1024 * 1024
LABEL = {"transport_only": True, "proofs_verified": False}


def _json(value):
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _pin(payload):
    return {"bytes": len(payload), "sha256": sha256(payload).hexdigest()}


def _inventory(files):
    return {"files": {name: _pin(payload) for name, payload in files.items()},
            "file_count": len(files),
            "html_count": sum(name.endswith(".html") for name in files),
            "total_bytes": sum(map(len, files.values()))}


def _write_files(directory, files):
    directory.mkdir()
    for name, payload in files.items():
        destination = directory / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        with destination.open("xb") as stream:
            stream.write(payload)


@dataclass
class NonAuthorityTransportContext:
    """Not a verifier-issued capability, and never accepted by the public API."""

    catalog_sha256: str = CATALOG
    source_binding_sha256: str = BINDING
    transport_only: bool = True
    proofs_verified: bool = False
    guards: int = 0

    def require_unchanged(self):
        assert self.transport_only is True and self.proofs_verified is False
        self.guards += 1


def _envelope(inventory, *, phase="completed", check=False):
    return {
        "schema": "peano-lab-alpha-v31-publication-process-v1",
        "nonce": NONCE, "phase": phase,
        "catalog_sha256": CATALOG, "source_binding_sha256": BINDING,
        "check": check,
        "limits": {"cpu": [170, 175], "wall_seconds": 180,
                   "max_rss_bytes": RSS_LIMIT},
        "peak_rss_bytes": 100,
        "inventory": _pin(_json(inventory)), "pytest_status": 0,
    }


def _validate(payload, *, phase="completed", check=False, context=None, nonce=NONCE):
    return process._validate_message(
        payload, nonce=nonce, phase=phase, check=check,
        context=context if context is not None else NonAuthorityTransportContext(),
    )


@pytest.fixture
def transport_files(tmp_path):
    files = {
        "index.html": b"<!doctype html><title>Transport only; no proof verified</title>\n",
        "transport-only.json": _json(LABEL),
        "nested/plain.txt": b"synthetic transport data, not a proof or release receipt\n",
    }
    directory = tmp_path / "synthetic-tree"
    _write_files(directory, files)
    inventory = _inventory(files)
    return SimpleNamespace(directory=directory, files=files, inventory=inventory,
                           message=_envelope(inventory))


@pytest.mark.parametrize("phase", PHASES)
@pytest.mark.parametrize("check", (False, True))
def test_exact_transport_roundtrip_is_explicitly_not_a_proof_capability(transport_files, phase, check):
    message = _envelope(transport_files.inventory, phase=phase, check=check)
    assert _validate(_json(message), phase=phase, check=check) == message
    process._validate_tree(transport_files.directory, transport_files.inventory)
    assert json.loads(transport_files.files["transport-only.json"]) == LABEL
    assert LABEL["proofs_verified"] is False


@pytest.mark.parametrize("path,value", (
    (("schema",), "old-publication-result"), (("nonce",), "4" * 64),
    (("phase",), "historical"), (("catalog_sha256",), "5" * 64),
    (("source_binding_sha256",), "6" * 64), (("check",), True),
    (("check",), 0), (("check",), "false"),
    (("limits", "cpu"), [171, 175]), (("limits", "cpu"), [170, 176]),
    (("limits", "cpu"), [170.0, 175]), (("limits", "wall_seconds"), 181),
    (("limits", "max_rss_bytes"), RSS_LIMIT + 1),
    (("peak_rss_bytes",), 0), (("peak_rss_bytes",), -1),
    (("peak_rss_bytes",), True), (("peak_rss_bytes",), 1.0),
    (("peak_rss_bytes",), RSS_LIMIT + 1),
    (("inventory", "bytes"), 0), (("inventory", "bytes"), True),
    (("inventory", "bytes"), 2 * 1024 * 1024 + 1),
    (("inventory", "sha256"), "0" * 63),
    (("inventory", "sha256"), "F" * 64),
))
def test_stale_foreign_unbounded_and_wrong_mode_messages_fail_closed(transport_files, path, value):
    message = deepcopy(transport_files.message)
    target = message
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(ValueError):
        _validate(_json(message))


@pytest.mark.parametrize("mutation", ("missing", "extra", "inventory_extra", "inventory_missing", "limits_extra", "limits_missing"))
def test_envelope_requires_exact_nested_and_top_level_fields(transport_files, mutation):
    message = deepcopy(transport_files.message)
    if mutation == "missing":
        del message["nonce"]
    elif mutation == "extra":
        message["receipt_is_authority"] = True
    elif mutation == "inventory_extra":
        message["inventory"]["path"] = "../foreign.json"
    elif mutation == "inventory_missing":
        del message["inventory"]["sha256"]
    elif mutation == "limits_extra":
        message["limits"]["allow_unbounded"] = True
    else:
        del message["limits"]["cpu"]
    with pytest.raises(ValueError):
        _validate(_json(message))


@pytest.mark.parametrize("status", (None, False, True, 1, -1, "0", 0.0))
def test_mandatory_ui_gate_requires_an_exact_success_status(transport_files, status):
    message = deepcopy(transport_files.message)
    message["pytest_status"] = status
    with pytest.raises(ValueError):
        _validate(_json(message))


@pytest.mark.parametrize("payload", (
    b"", b"{}", b"[]", b"\xff", b'{"nonce":1,"nonce":2}',
    b'{"value":NaN}', b'{"value":Infinity}', b"{}\n{}",
    b"banner\n{}", b"x" * 8193,
))
def test_pipe_payload_is_strict_duplicate_free_and_byte_bounded(payload):
    with pytest.raises(ValueError):
        _validate(payload)


@pytest.mark.parametrize("mode", ("trailing_newline", "pretty_json", "duplicate_valid_key", "nonfinite_number"))
def test_otherwise_shaped_messages_still_require_canonical_json(transport_files, mode):
    message = transport_files.message
    raw = _json(message)
    if mode == "trailing_newline":
        raw += b"\n"
    elif mode == "pretty_json":
        raw = json.dumps(message, indent=2).encode()
    elif mode == "duplicate_valid_key":
        raw = raw.replace(b"{", b'{"check":false,', 1)
    else:
        raw = raw.replace(b'"peak_rss_bytes":100', b'"peak_rss_bytes":1e999')
    with pytest.raises(ValueError):
        _validate(raw)


@pytest.mark.parametrize("field,value", (("catalog_sha256", None), ("source_binding_sha256", True),
                                         ("catalog_sha256", "f" * 63), ("source_binding_sha256", "F" * 64)))
def test_transport_context_identities_are_strictly_typed(transport_files, field, value):
    context = NonAuthorityTransportContext()
    setattr(context, field, value)
    message = deepcopy(transport_files.message)
    message[field] = value
    with pytest.raises(ValueError):
        _validate(_json(message), context=context)


@pytest.mark.parametrize("mutation", (
    "missing", "extra", "files_list", "file_count_bool", "file_count_wrong", "file_count_over",
    "html_count_bool", "html_count_wrong", "total_bool", "total_wrong", "total_over",
    "file_bytes_bool", "file_bytes_zero", "file_bytes_over", "file_hash", "extra_pin",
))
def test_inventory_has_exact_bounded_typed_counts_and_file_pins(transport_files, mutation):
    inventory = deepcopy(transport_files.inventory)
    if mutation == "missing":
        del inventory["total_bytes"]
    elif mutation == "extra":
        inventory["accepted"] = True
    elif mutation == "files_list":
        inventory["files"] = list(inventory["files"])
    elif mutation.startswith("file_count"):
        inventory["file_count"] = {"file_count_bool": True, "file_count_wrong": 4,
                                   "file_count_over": 20001}[mutation]
    elif mutation.startswith("html_count"):
        inventory["html_count"] = True if mutation.endswith("bool") else 2
    elif mutation.startswith("total"):
        inventory["total_bytes"] = {"total_bool": True, "total_wrong": 1,
                                    "total_over": RSS_LIMIT + 1}[mutation]
    else:
        pin = inventory["files"]["index.html"]
        if mutation.startswith("file_bytes"):
            pin["bytes"] = {"file_bytes_bool": True, "file_bytes_zero": 0,
                            "file_bytes_over": 64 * 1024 * 1024 + 1}[mutation]
        elif mutation == "file_hash":
            pin["sha256"] = "x" * 64
        else:
            pin["authority"] = "receipt"
    with pytest.raises(ValueError):
        process._validate_inventory(inventory)


@pytest.mark.parametrize("name", ("../outside", "/absolute", "folder/../outside", "./index.html",
                                "folder\\outside", "folder//entry", "", "nul\x00name", 1))
def test_inventory_paths_cannot_escape_or_alias_the_private_tree(transport_files, name):
    inventory = deepcopy(transport_files.inventory)
    inventory["files"][name] = inventory["files"].pop("nested/plain.txt")
    with pytest.raises(ValueError):
        process._validate_inventory(inventory)


@pytest.mark.parametrize("mutation", ("same_size", "append", "truncate", "missing", "extra"))
def test_literal_files_are_rehashed_not_accepted_from_inventory(transport_files, mutation):
    target = transport_files.directory / "index.html"
    original = transport_files.files["index.html"]
    if mutation == "same_size":
        target.write_bytes(b"x" * len(original))
    elif mutation == "append":
        target.write_bytes(original + b"x")
    elif mutation == "truncate":
        target.write_bytes(b"")
    elif mutation == "missing":
        target.unlink()
    else:
        (transport_files.directory / "unregistered.txt").write_bytes(b"extra")
    with pytest.raises(ValueError):
        process._validate_tree(transport_files.directory, transport_files.inventory)


@pytest.mark.parametrize("scope", ("root", "ancestor", "directory", "leaf", "dangling"))
def test_every_tree_component_rejects_symlinks(transport_files, tmp_path, scope):
    tree = transport_files.directory
    if scope == "root":
        alias = tmp_path / "alias"
        alias.symlink_to(tree, target_is_directory=True)
        tree = alias
    elif scope == "ancestor":
        alias = tmp_path / "alias-parent"
        alias.symlink_to(tmp_path, target_is_directory=True)
        tree = alias / tree.name
    elif scope == "directory":
        moved = tmp_path / "moved-nested"
        (tree / "nested").rename(moved)
        (tree / "nested").symlink_to(moved, target_is_directory=True)
    elif scope == "leaf":
        moved = tmp_path / "moved-index"
        (tree / "index.html").rename(moved)
        (tree / "index.html").symlink_to(moved)
    else:
        (tree / "dangling").symlink_to(tmp_path / "does-not-exist")
    with pytest.raises(ValueError):
        process._validate_tree(tree, transport_files.inventory)


def test_nonregular_tree_entry_is_rejected_without_opening_it(transport_files):
    os.mkfifo(transport_files.directory / "pipe")
    with pytest.raises(ValueError, match="nonregular"):
        process._validate_tree(transport_files.directory, transport_files.inventory)


@pytest.fixture
def fork_transport(transport_files, tmp_path, monkeypatch):
    """Actual OS fork and actual child writer, with synthetic format/test hooks."""
    context = NonAuthorityTransportContext()
    parent_pid = os.getpid()
    observation = tmp_path / "synthetic-child-observation.json"
    test_observation = tmp_path / "synthetic-tests-observation.json"

    def entries(actual, phase):
        assert actual is context and phase in PHASES
        assert os.getpid() != parent_pid and os.getpgrp() == os.getpid()
        assert resource.getrlimit(resource.RLIMIT_CPU) == (170, 175)
        remaining, interval = signal.getitimer(signal.ITIMER_REAL)
        assert 0 < remaining <= 180 and interval == 0
        observation.write_text(json.dumps({**LABEL, "pid": os.getpid(), "pgid": os.getpgrp(),
            "cpu": list(resource.getrlimit(resource.RLIMIT_CPU)), "remaining_wall_seconds": remaining,
            "phase": phase, "inherited_context": actual is context}))
        return tuple(transport_files.files.items())

    def mandatory_transport_test(actual, phase, tree, inventory):
        assert actual is context and inventory == transport_files.inventory
        assert {name: (tree / name).read_bytes() for name in inventory["files"]} == transport_files.files
        test_observation.write_text(json.dumps({**LABEL, "phase": phase}))
        return 0

    monkeypatch.setattr(process, "_phase_entries", entries)
    monkeypatch.setattr(process, "_run_phase_tests", mandatory_transport_test)
    monkeypatch.setattr(process.secrets, "token_hex", lambda size: NONCE if size == 32 else None)
    return SimpleNamespace(context=context, parent_pid=parent_pid, files=transport_files.files,
                           inventory=transport_files.inventory, observation=observation,
                           test_observation=test_observation, output=tmp_path / "private-phase-output")


def _fork(fixture, *, phase="completed", check=False):
    return process._fork_phase(fixture.context, phase, output=fixture.output, check=check)


@pytest.mark.parametrize("phase", PHASES)
@pytest.mark.parametrize("check", (False, True))
def test_real_fork_inherits_only_labelled_transport_data_and_enforces_original_caps(fork_transport, phase, check):
    result = _fork(fork_transport, phase=phase, check=check)
    assert type(result) is process.PhaseResult
    assert result.phase == phase and result.directory == fork_transport.output
    assert result.inventory == fork_transport.inventory
    assert result.inventory_sha256 == sha256(_json(fork_transport.inventory)).hexdigest()
    assert 0 < result.peak_rss_bytes <= RSS_LIMIT and 0 < result.elapsed_seconds < 180
    assert fork_transport.context.guards == 1  # One parent call; child memory is private.
    observed = json.loads(fork_transport.observation.read_text())
    assert observed["pid"] == observed["pgid"] != os.getpid()
    assert observed["inherited_context"] is True and observed["proofs_verified"] is False
    assert observed["cpu"] == [170, 175]
    assert json.loads(fork_transport.test_observation.read_text()) == {**LABEL, "phase": phase}
    process._validate_tree(result.directory, result.inventory)
    with pytest.raises(ChildProcessError):
        os.waitpid(observed["pid"], os.WNOHANG)


@pytest.mark.parametrize("mode", ("nonzero", "signal", "missing", "oversized", "wrong_nonce",
                                 "wrong_catalog", "wrong_source", "wrong_phase", "wrong_inventory"))
def test_real_child_failures_leave_no_output_and_reap_the_exact_owned_leader(fork_transport, monkeypatch, mode):
    actual_child, actual_fork, actual_waitpid = process._render_child, os.fork, os.waitpid
    spawned = []

    def observed_fork():
        pid = actual_fork()
        if pid:
            spawned.append(pid)
        return pid

    def bad_child(context, phase, **options):
        if mode in ("nonzero", "signal"):
            actual_child(context, phase, **options)
            if mode == "nonzero":
                os._exit(7)
            os.kill(os.getpid(), signal.SIGTERM)
        elif mode == "missing":
            return
        elif mode == "oversized":
            os.write(options["write_fd"], b"x" * 8193)
        else:
            message = _envelope(fork_transport.inventory)
            field = {"wrong_nonce": "nonce", "wrong_catalog": "catalog_sha256",
                     "wrong_source": "source_binding_sha256", "wrong_phase": "phase"}.get(mode)
            if field is not None:
                message[field] = "historical" if field == "phase" else "f" * 64
            else:
                message["inventory"]["sha256"] = "0" * 64
            os.write(options["write_fd"], _json(message))

    monkeypatch.setattr(process.os, "fork", observed_fork)
    monkeypatch.setattr(process, "_render_child", bad_child)
    with pytest.raises((ValueError, OSError)):
        _fork(fork_transport)
    assert not fork_transport.output.exists() and not fork_transport.output.is_symlink()
    assert len(spawned) == 1
    with pytest.raises(ChildProcessError):
        actual_waitpid(spawned[0], os.WNOHANG)


@pytest.mark.parametrize("status", (None, False, True, 1, "0"))
def test_mandatory_test_failure_cannot_create_a_private_completed_tree(fork_transport, monkeypatch, status):
    monkeypatch.setattr(process, "_run_phase_tests", lambda *args: status)
    with pytest.raises(ValueError, match="exit successfully"):
        _fork(fork_transport)
    assert not fork_transport.output.exists()


@pytest.mark.parametrize("mutation", ("content", "extra"))
def test_child_rehashes_all_files_after_its_test_callback(fork_transport, monkeypatch, mutation):
    def corrupt(context, phase, tree, inventory):
        if mutation == "content":
            (tree / "index.html").write_bytes(b"x" * inventory["files"]["index.html"]["bytes"])
        else:
            (tree / "untested.txt").write_bytes(b"post-test addition")
        return 0

    monkeypatch.setattr(process, "_run_phase_tests", corrupt)
    with pytest.raises(ValueError, match="exit successfully"):
        _fork(fork_transport)
    assert not fork_transport.output.exists()


@pytest.mark.parametrize("mode", ("empty", "duplicate", "traversal", "absolute", "backslash", "nul", "text_payload", "empty_payload"))
def test_actual_child_writer_rejects_invalid_generated_entries(fork_transport, monkeypatch, mode):
    entries = {
        "empty": (),
        "duplicate": (("index.html", b"one"), ("index.html", b"two")),
        "traversal": (("../escape.txt", b"synthetic"),),
        "absolute": (("/escape.txt", b"synthetic"),),
        "backslash": (("folder\\escape.txt", b"synthetic"),),
        "nul": (("nul\x00entry", b"synthetic"),),
        "text_payload": (("index.html", "not literal bytes"),),
        "empty_payload": (("index.html", b""),),
    }[mode]
    monkeypatch.setattr(process, "_phase_entries", lambda *args: entries)
    monkeypatch.setattr(process, "_run_phase_tests", lambda *args: pytest.fail("invalid files reached tests"))
    with pytest.raises(ValueError, match="exit successfully"):
        _fork(fork_transport)
    assert not fork_transport.output.exists()


@pytest.mark.parametrize("phase", PHASES)
def test_real_test_dispatch_keeps_same_inherited_context_and_exact_phase_selection(transport_files, monkeypatch, phase):
    context = NonAuthorityTransportContext()
    expected = {
        "completed": ("test_constructive_completed_lower_explorer_v31.py", "not atlas"),
        "historical": ("test_constructive_historical_publication_v31.py", None),
        "atlas": ("test_constructive_completed_lower_explorer_v31.py", "atlas"),
    }
    seen = []

    def rejecting_pytest(arguments, *, plugins):
        seen.append(arguments)
        assert len(plugins) == 1
        config = SimpleNamespace()
        plugins[0].pytest_configure(config)
        retained = config._alpha_v31_publication
        assert set(retained) == {"phase", "context", "directory", "inventory"}
        assert retained["context"] is context and retained["inventory"] is transport_files.inventory
        assert retained["phase"] == phase and retained["directory"] == transport_files.directory
        filename, selector = expected[phase]
        assert arguments == ["-q", "--tb=short", str(ROOT / "peano-lab/py/tests" / filename)] + (
            [] if selector is None else ["-k", selector])
        return 1  # Always reject: this is not a positive UI or proof-verifier substitute.

    monkeypatch.setattr(pytest, "main", rejecting_pytest)
    assert process._run_phase_tests(context, phase, transport_files.directory, transport_files.inventory) == 1
    assert len(seen) == 1 and context.proofs_verified is False


@pytest.mark.parametrize("target", ("inventory.json", "files/index.html", "files/extra.txt"))
def test_parent_rehashes_literal_inventory_and_tree_after_the_child_has_finished(fork_transport, monkeypatch, target):
    actual_child = process._render_child

    def corrupt_after_message(*args, **options):
        actual_child(*args, **options)
        path = options["work"] / target
        path.write_bytes(b"x" * (path.stat().st_size if path.exists() else 10))

    monkeypatch.setattr(process, "_render_child", corrupt_after_message)
    with pytest.raises(ValueError):
        _fork(fork_transport)
    assert not fork_transport.output.exists()


def test_parent_rechecks_live_source_guard_after_literal_tree_hashing(fork_transport, monkeypatch):
    original_validate = process._validate_tree
    state = {"parent_tree_hashed": False}

    def validate(tree, inventory):
        original_validate(tree, inventory)
        if os.getpid() == fork_transport.parent_pid:
            state["parent_tree_hashed"] = True

    def reject_parent():
        if os.getpid() == fork_transport.parent_pid:
            assert state["parent_tree_hashed"]
            raise ValueError("deliberate post-hash live-source rejection")

    monkeypatch.setattr(process, "_validate_tree", validate)
    monkeypatch.setattr(fork_transport.context, "require_unchanged", reject_parent)
    with pytest.raises(ValueError, match="post-hash live-source rejection"):
        _fork(fork_transport)
    assert not fork_transport.output.exists()


def test_private_output_creation_race_does_not_replace_foreign_data(fork_transport, monkeypatch):
    def guard():
        if os.getpid() == fork_transport.parent_pid:
            fork_transport.output.mkdir()
            (fork_transport.output / "foreign.txt").write_bytes(b"unrelated newly created target")

    monkeypatch.setattr(fork_transport.context, "require_unchanged", guard)
    with pytest.raises(OSError):
        _fork(fork_transport)
    assert (fork_transport.output / "foreign.txt").read_bytes() == b"unrelated newly created target"
    assert set(path.name for path in fork_transport.output.iterdir()) == {"foreign.txt"}


@pytest.mark.parametrize("descendant", (False, True))
def test_timeout_and_abandoned_pipe_descendant_cleanup_only_the_owned_process_group(fork_transport, monkeypatch, descendant):
    actual_fork, actual_waitpid, actual_killpg = os.fork, os.waitpid, os.killpg
    spawned, killed = [], []

    def fork():
        pid = actual_fork()
        if pid:
            spawned.append(pid)
        return pid

    def killpg(pgid, sig):
        killed.append((pgid, sig))
        return actual_killpg(pgid, sig)

    def blocked_child(*args, **kwargs):
        if descendant:
            if actual_fork():
                return  # Descendant retains the pipe; leader is clean but incomplete.
        else:
            signal.signal(signal.SIGALRM, signal.SIG_IGN)
        time.sleep(10)
        os._exit(0)

    monkeypatch.setattr(process.os, "fork", fork)
    monkeypatch.setattr(process.os, "killpg", killpg)
    monkeypatch.setattr(process, "_render_child", blocked_child)
    monkeypatch.setattr(process, "WALL_SECONDS", 1)  # Stricter, synthetic-only limit.
    monkeypatch.setattr(process, "TIMEOUT_SECONDS", 2)
    started = time.monotonic()
    with pytest.raises((ValueError, PermissionError)):
        _fork(fork_transport)
    assert time.monotonic() - started < 3
    assert len(spawned) == 1 and spawned[0] != os.getpgrp()
    assert killed == [(spawned[0], signal.SIGKILL)]
    with pytest.raises(ChildProcessError):
        actual_waitpid(spawned[0], os.WNOHANG)
    assert not fork_transport.output.exists()


def test_denied_group_signal_is_not_retried_and_still_reaps_exact_owned_leader(fork_transport, monkeypatch):
    actual_fork, actual_waitpid = os.fork, os.waitpid
    state = SimpleNamespace(spawned=[], denied=[], denial=False)

    def fork():
        pid = actual_fork()
        if pid:
            state.spawned.append(pid)
        return pid

    def waitpid(pid, flags):
        if flags == os.WNOHANG and not state.denial:
            return 0, 0
        return actual_waitpid(pid, flags)

    def deny(pgid, sig):
        assert state.spawned == [pgid] and sig == signal.SIGKILL
        state.denied.append(pgid)
        state.denial = True
        # A deterministic simulated denial, never a real denied-call retry.
        raise PermissionError(errno.EPERM, "simulated exact-owned-group denial")

    monkeypatch.setattr(process.os, "fork", fork)
    monkeypatch.setattr(process.os, "waitpid", waitpid)
    monkeypatch.setattr(process.os, "killpg", deny)
    monkeypatch.setattr(process, "_render_child", lambda *args, **kwargs: os.write(kwargs["write_fd"], b"x" * 8193))
    with pytest.raises(PermissionError, match="exact-owned-group denial"):
        _fork(fork_transport)
    assert len(state.spawned) == 1 and state.denied == state.spawned
    with pytest.raises(ChildProcessError):
        actual_waitpid(state.spawned[0], os.WNOHANG)
    assert not fork_transport.output.exists()


@pytest.mark.parametrize("boundary", ("child_exit", "parent_tree", "parent_context"))
def test_crossing_the_absolute_deadline_never_installs_a_private_tree(fork_transport, monkeypatch, boundary):
    actual_pipe, actual_read, actual_waitpid = os.pipe, os.read, os.waitpid
    actual_validate, actual_guard, monotonic = process._validate_tree, fork_transport.context.require_unchanged, time.monotonic
    state = SimpleNamespace(fd=None, eof=False, expired=False)

    def pipe():
        pair = actual_pipe()
        state.fd = pair[0]
        return pair

    def read(fd, size):
        data = actual_read(fd, size)
        if fd == state.fd and not data:
            state.eof = True
        return data

    def waitpid(pid, flags):
        if boundary == "child_exit" and flags == os.WNOHANG and not state.eof:
            return 0, 0
        result = actual_waitpid(pid, flags)
        if boundary == "child_exit" and result[0]:
            state.expired = True
        return result

    def validate(tree, inventory):
        actual_validate(tree, inventory)
        if boundary == "parent_tree" and os.getpid() == fork_transport.parent_pid:
            state.expired = True

    def guard():
        actual_guard()
        if boundary == "parent_context" and os.getpid() == fork_transport.parent_pid:
            state.expired = True

    monkeypatch.setattr(process.os, "pipe", pipe)
    monkeypatch.setattr(process.os, "read", read)
    monkeypatch.setattr(process.os, "waitpid", waitpid)
    monkeypatch.setattr(process, "_validate_tree", validate)
    monkeypatch.setattr(fork_transport.context, "require_unchanged", guard)
    monkeypatch.setattr(process, "time", SimpleNamespace(
        monotonic=lambda: monotonic() + (186 if state.expired else 0), sleep=time.sleep))
    with pytest.raises(ValueError, match="deadline|window|bounded phase"):
        _fork(fork_transport)
    assert not fork_transport.output.exists()


@pytest.mark.parametrize("phase,check", (("foreign", False), (None, False), ("completed", 0),
                                       ("completed", None), ("completed", "false")))
def test_invalid_phase_or_check_mode_rejects_before_pipe_allocation(fork_transport, monkeypatch, phase, check):
    monkeypatch.setattr(process.os, "pipe", lambda: pytest.fail("invalid request allocated a pipe"))
    with pytest.raises(ValueError):
        _fork(fork_transport, phase=phase, check=check)


@pytest.mark.parametrize("scope", ("existing", "symlink", "dangling", "ancestor"))
def test_private_output_is_new_and_has_only_regular_ancestors(fork_transport, tmp_path, monkeypatch, scope):
    target = fork_transport.output
    if scope == "existing":
        target.mkdir()
    elif scope == "symlink":
        target.symlink_to(tmp_path, target_is_directory=True)
    elif scope == "dangling":
        target.symlink_to(tmp_path / "missing")
    else:
        alias = tmp_path / "linked-parent"
        alias.symlink_to(tmp_path, target_is_directory=True)
        fork_transport.output = alias / "new-child"
    monkeypatch.setattr(process.os, "pipe", lambda: pytest.fail("unsafe output allocated a pipe"))
    with pytest.raises(ValueError):
        _fork(fork_transport)


def test_fork_failure_closes_both_new_pipe_descriptors(fork_transport, monkeypatch):
    actual_pipe, descriptors = os.pipe, []

    def pipe():
        pair = actual_pipe()
        descriptors.extend(pair)
        return pair

    def fail():
        raise OSError("deliberate fork failure")

    monkeypatch.setattr(process.os, "pipe", pipe)
    monkeypatch.setattr(process.os, "fork", fail)
    with pytest.raises(OSError, match="fork failure"):
        _fork(fork_transport)
    assert len(descriptors) == 2
    for fd in descriptors:
        with pytest.raises(OSError):
            os.fstat(fd)
    assert not fork_transport.output.exists()


@pytest.fixture
def transaction(tmp_path, monkeypatch):
    staging, public = tmp_path / "private", tmp_path / "destinations"
    staging.mkdir()
    public.mkdir()
    outputs = {phase: public / phase for phase in PHASES}
    results = []
    for phase in PHASES:
        files = {"index.html": f"<title>Transport-only {phase}; no verified proof</title>".encode(),
                 "transport-only.json": _json(LABEL)}
        directory = staging / phase
        _write_files(directory, files)
        inventory = _inventory(files)
        results.append(process.PhaseResult(phase, directory, inventory,
            sha256(_json(inventory)).hexdigest(), 100, 0.01))
    monkeypatch.setattr(process, "OUTPUTS", outputs)
    return SimpleNamespace(results=tuple(results), outputs=outputs, staging=staging)


def test_three_private_synthetic_phases_install_together_without_claiming_proof_authority(transaction):
    process._install_results(transaction.results, check=False)
    for row in transaction.results:
        target = transaction.outputs[row.phase]
        assert not row.directory.exists()
        process._validate_tree(target, row.inventory)
        assert json.loads((target / "transport-only.json").read_bytes()) == LABEL


@pytest.mark.parametrize("mutation", ("missing", "reordered", "duplicate", "foreign", "nonboolean"))
def test_install_requires_all_three_exact_phases_and_strict_mode(transaction, mutation):
    rows = transaction.results
    if mutation == "missing":
        rows = rows[:-1]
    elif mutation == "reordered":
        rows = rows[::-1]
    elif mutation == "duplicate":
        rows = (rows[0], rows[0], rows[2])
    elif mutation == "foreign":
        rows = (rows[0], rows[1], replace(rows[2], phase="foreign"))
    with pytest.raises(ValueError):
        process._install_results(rows, check=0 if mutation == "nonboolean" else False)
    assert all(row.directory.is_dir() for row in transaction.results)
    assert not any(target.exists() for target in transaction.outputs.values())


@pytest.mark.parametrize("phase", PHASES)
def test_all_public_destinations_are_preflighted_before_any_move(transaction, phase):
    target = transaction.outputs[phase]
    target.mkdir()
    (target / "old.txt").write_bytes(b"unrelated existing data")
    with pytest.raises(ValueError, match="existing"):
        process._install_results(transaction.results, check=False)
    assert all(row.directory.is_dir() for row in transaction.results)
    assert (target / "old.txt").read_bytes() == b"unrelated existing data"
    assert all(path.exists() == (name == phase) for name, path in transaction.outputs.items())


@pytest.mark.parametrize("check", (False, True))
def test_inventory_cannot_be_rewritten_after_the_child_authenticated_its_digest(transaction, check):
    if check:
        for row in transaction.results:
            _write_files(transaction.outputs[row.phase], {
                name: (row.directory / name).read_bytes() for name in row.inventory["files"]})
    first = transaction.results[0]
    changed = b"post-child mutation is not a passed UI result"
    target = transaction.outputs[first.phase] if check else first.directory
    (target / "index.html").write_bytes(changed)
    first.inventory["files"]["index.html"] = _pin(changed)
    first.inventory["total_bytes"] = sum(pin["bytes"] for pin in first.inventory["files"].values())
    assert sha256(_json(first.inventory)).hexdigest() != first.inventory_sha256
    with pytest.raises(ValueError, match="inventory|identity|digest"):
        process._install_results(transaction.results, check=check)
    assert all(row.directory.is_dir() for row in transaction.results)
    if not check:
        assert not any(path.exists() for path in transaction.outputs.values())


@pytest.mark.parametrize("failed_position", (1, 2))
def test_later_install_failure_rolls_back_only_earlier_owned_moves(transaction, monkeypatch, failed_position):
    actual_rename, calls = process._rename_new, []

    def rename(source, destination):
        calls.append((source, destination))
        if destination == transaction.outputs[PHASES[failed_position]]:
            raise OSError("deliberate later install failure")
        return actual_rename(source, destination)

    monkeypatch.setattr(process, "_rename_new", rename)
    with pytest.raises(OSError, match="later install failure"):
        process._install_results(transaction.results, check=False)
    for row in transaction.results:
        process._validate_tree(row.directory, row.inventory)
    assert not any(path.exists() for path in transaction.outputs.values())
    assert len(calls) == failed_position * 2 + 1


def test_final_rss_failure_rolls_back_all_three_owned_moves(transaction, monkeypatch):
    actual_rss = process._rss_bytes
    calls = []

    def reject_final_peak():
        calls.append(tuple(path.exists() for path in transaction.outputs.values()))
        if all(calls[-1]):
            raise ValueError("deliberate final publication RSS rejection")
        return actual_rss()

    monkeypatch.setattr(process, "_rss_bytes", reject_final_peak)
    with pytest.raises(ValueError, match="final publication RSS rejection"):
        process._install_results(transaction.results, check=False)
    assert (True, True, True) in calls
    assert not any(path.exists() for path in transaction.outputs.values())
    for row in transaction.results:
        process._validate_tree(row.directory, row.inventory)


def test_target_creation_race_never_overwrites_the_foreign_directory(transaction, monkeypatch):
    actual_rename = process._rename_new
    race_target = transaction.outputs["historical"]

    def race(source, destination):
        if destination == race_target:
            destination.mkdir()
            (destination / "foreign.txt").write_bytes(b"concurrently created unrelated data")
        return actual_rename(source, destination)

    monkeypatch.setattr(process, "_rename_new", race)
    with pytest.raises(OSError):
        process._install_results(transaction.results, check=False)
    assert (race_target / "foreign.txt").read_bytes() == b"concurrently created unrelated data"
    assert all(row.directory.is_dir() for row in transaction.results)
    assert not transaction.outputs["completed"].exists() and not transaction.outputs["atlas"].exists()


def test_rollback_identity_is_captured_before_rename_not_from_a_swapped_destination(transaction, tmp_path, monkeypatch):
    actual_rename = process._rename_new
    first_target = transaction.outputs["completed"]
    recovered_owned = tmp_path / "owned-after-adversarial-swap"

    def swap_after_rename(source, destination):
        if destination == transaction.outputs["historical"]:
            raise OSError("deliberate second-phase failure")
        actual_rename(source, destination)
        if destination == first_target:
            actual_rename(first_target, recovered_owned)
            first_target.mkdir()
            (first_target / "foreign.txt").write_bytes(b"foreign directory must not be rolled back")

    monkeypatch.setattr(process, "_rename_new", swap_after_rename)
    with pytest.raises(ValueError, match="changed|foreign|identity"):
        process._install_results(transaction.results, check=False)
    assert (first_target / "foreign.txt").read_bytes() == b"foreign directory must not be rolled back"
    process._validate_tree(recovered_owned, transaction.results[0].inventory)
    assert not transaction.results[0].directory.exists()
    assert all(row.directory.is_dir() for row in transaction.results[1:])


@pytest.mark.parametrize("mutation", ("none", "content", "extra", "missing"))
def test_check_mode_rehashes_existing_outputs_without_renaming_anything(transaction, monkeypatch, mutation):
    for row in transaction.results:
        _write_files(transaction.outputs[row.phase], {
            name: (row.directory / name).read_bytes() for name in row.inventory["files"]})
    target = transaction.outputs["historical"]
    if mutation == "content":
        path = target / "index.html"
        path.write_bytes(b"x" * path.stat().st_size)
    elif mutation == "extra":
        (target / "extra.txt").write_bytes(b"not registered")
    elif mutation == "missing":
        (target / "index.html").unlink()
    monkeypatch.setattr(process, "_rename_new", lambda *args: pytest.fail("check mode attempted a write"))
    if mutation == "none":
        process._install_results(transaction.results, check=True)
    else:
        with pytest.raises(ValueError):
            process._install_results(transaction.results, check=True)
    assert all(row.directory.is_dir() for row in transaction.results)


def test_atomic_native_no_replace_rename_refuses_an_existing_target(tmp_path):
    source, target = tmp_path / "source", tmp_path / "existing"
    source.mkdir()
    target.mkdir()
    (source / "new.txt").write_bytes(b"owned synthetic source")
    (target / "old.txt").write_bytes(b"unrelated target")
    with pytest.raises(OSError):
        process._rename_new(source, target)
    assert (source / "new.txt").read_bytes() == b"owned synthetic source"
    assert (target / "old.txt").read_bytes() == b"unrelated target"


def test_unavailable_atomic_no_replace_primitive_fails_closed(tmp_path, monkeypatch):
    source, target = tmp_path / "source", tmp_path / "target"
    source.mkdir()
    monkeypatch.setattr(process, "sys", SimpleNamespace(platform="unsupported-test-platform"))
    with pytest.raises(ValueError, match="unavailable"):
        process._rename_new(source, target)
    assert source.is_dir() and not target.exists()


@pytest.mark.parametrize("peak", (0, RSS_LIMIT + 1))
def test_original_rss_ceiling_itself_rejects_invalid_measurements(monkeypatch, peak):
    unit = 1 if sys.platform == "darwin" else 1024
    measured = peak if unit == 1 else (peak + unit - 1) // unit
    monkeypatch.setattr(process, "resource", SimpleNamespace(
        RUSAGE_SELF=resource.RUSAGE_SELF,
        getrusage=lambda who: SimpleNamespace(ru_maxrss=measured)))
    with pytest.raises(ValueError, match="1536 MiB"):
        process._rss_bytes()


@pytest.mark.parametrize("context", (None, {}, {"verified": True, "receipt": "old.json"}, NonAuthorityTransportContext()))
def test_actual_public_guard_rejects_receipts_and_plain_transport_contexts_before_any_process(context, monkeypatch):
    monkeypatch.setattr(process, "_fork_phase", lambda *args, **kwargs: pytest.fail("non-capability reached a child"))
    monkeypatch.setattr(process, "_install_results", lambda *args, **kwargs: pytest.fail("non-capability reached installation"))
    with pytest.raises(ValueError, match="live v31 verification capability"):
        process.publish_from_live_context(context, False)


def test_original_limits_mandatory_tests_and_live_only_transaction_order_are_explicit():
    assert process.CPU_LIMITS == (170, 175)
    assert process.WALL_SECONDS == 180 and process.CLEANUP_SECONDS == 5
    assert process.TIMEOUT_SECONDS == 185 and process.MAX_RSS_BYTES == RSS_LIMIT
    assert process.MAX_MESSAGE_BYTES == 8192 and process.MAX_INVENTORY_BYTES == 2 * 1024 * 1024
    assert process.MAX_FILE_BYTES == 64 * 1024 * 1024 and process.MAX_FILES == 20000
    assert process.PHASES == PHASES
    assert tuple(inspect.signature(process.publish_from_live_context).parameters) == ("context", "check")
    assert not hasattr(process, "main")  # No receipt/child CLI can manufacture the inherited capability.
    sources = {name: ast.unparse(ast.parse(textwrap.dedent(inspect.getsource(getattr(process, name)))).body[0])
               for name in ("_render_child", "_fork_phase", "publish_from_live_context")}
    child, fork, public = (sources[name] for name in ("_render_child", "_fork_phase", "publish_from_live_context"))
    assert child.index("_run_phase_tests(") < child.index("raw_inventory = _canonical(")
    assert child.index("_run_phase_tests(") < child.rindex("_validate_tree(") < child.index("context.require_unchanged()")
    assert fork.index("os.setsid()") < fork.index("resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)")
    assert fork.index("signal.alarm(WALL_SECONDS)") < fork.index("_render_child(")
    assert "os.waitpid(pid, 0)" not in fork and "os.waitpid(pid, os.WNOHANG)" in fork
    assert "os.killpg(pid, signal.SIGKILL)" in fork
    assert public.index("publication.require_live(context)") < public.index("_fork_phase(")
    assert public.index("for phase in PHASES:") < public.index("_fork_phase(")
    assert public.index("_fork_phase(") < public.index("context.require_unchanged()") < public.index("_install_results(")
    assert "test=False" not in public and "receipt" not in inspect.signature(process.publish_from_live_context).parameters


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Original-bounded synthetic publication transport regressions.")
    parser.add_argument("--pytest-select", default="")
    args = parser.parse_args()
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)
    started = time.monotonic()
    status = pytest.main(["-q", "--tb=short", "-x", __file__, "-k", args.pytest_select])
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == "darwin" else 1024)
    print(json.dumps({"status": int(status), "seconds": time.monotonic() - started,
                      "peak_rss_bytes": peak, "rss_limit_passed": peak <= RSS_LIMIT,
                      "transport_only": True, "proofs_verified": False}), flush=True)
    assert peak <= RSS_LIMIT
    raise SystemExit(status)
