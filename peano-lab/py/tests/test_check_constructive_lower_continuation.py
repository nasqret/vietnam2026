"""Bounded audit protocol tests, with one genuinely checked family worker.

Protocol fixtures below test transport and exact metadata only; they confer no
proof status. The positive live-worker fixture runs the original complete HA,
the actual pinned Lean binary and all three DI empty-context roots. No proof
checker is replaced by a mocked accepting implementation.
"""

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import ast
import os
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import check_constructive_lower_continuation as cli


NONCE = "1" * 64
BINDING = "2" * 64


@pytest.fixture(scope="module")
def metadata():
    return cli._expected_family_report(cli.checkpoints.CHECKPOINTS[0])


def _message(metadata):
    report = deepcopy(metadata)
    # A small bounded count is protocol test data, never a proof receipt.
    for root in report["principal_roots"]:
        root["ordinary_certificate_nodes"] = 10
    return {
        "schema": cli.WORKER_SCHEMA, "kind": "family", "slug": "divisor-involutions",
        "nonce": NONCE, "binding_sha256": BINDING,
        "limits": {"cpu": [170, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024},
        "peak_rss_bytes": 100, "report": report,
    }


def _validate(payload, metadata):
    return cli._validate_message(payload, kind="family", slug="divisor-involutions",
                                 nonce=NONCE, binding=BINDING, expected=metadata)


def test_exact_protocol_shape_does_not_change_report(metadata):
    envelope = _message(metadata)
    report, peak = _validate(cli._canonical(envelope), metadata)
    assert report == envelope["report"] and peak == 100
    assert cli.MAX_STDOUT_BYTES == 128 * 1024
    assert cli.MAX_STDERR_BYTES == 8 * 1024
    assert cli.CPU_LIMITS == (170, 175) and cli.WALL_SECONDS == 180
    assert cli.PARENT_TIMEOUT_SECONDS == 185
    assert cli.MAX_RSS_BYTES == 1536 * 1024 * 1024
    assert cli.CONTROLLER_WALL_SECONDS == 5 * 185 + 180


@pytest.mark.parametrize("path,value", (
    (("nonce",), "3" * 64), (("binding_sha256",), "4" * 64),
    (("kind",), "novelty"), (("slug",), "polynomial-products"), (("schema",), "old"),
    (("limits", "cpu"), [171, 175]), (("limits", "wall_seconds"), 181),
    (("limits", "max_rss_bytes"), 2**31), (("peak_rss_bytes",), 2**31),
    (("peak_rss_bytes",), True), (("peak_rss_bytes",), 0),
    (("report", "slug"), "polynomial-products"),
    (("report", "new_theorem_count"), 13),
    (("report", "new_specs_sha256"), "0" * 64),
    (("report", "complete_non_alpha_specs_sha256"), "0" * 64),
    (("report", "sources", 0, "sha256"), "0" * 64),
    (("report", "sources", 0, "factory"), "other_factory"),
    (("report", "support", "alpha_v30_count"), 0),
    (("report", "support", "counted_as_new_owned_theorems"), True),
    (("report", "bundle", "sha256"), "0" * 64),
    (("report", "bundle", "body_proof_nodes"), 1),
    (("report", "bundle", "original_ha_checked"), False),
    (("report", "bundle", "independent_lean_checked"), False),
    (("report", "admitted_to_alpha"), True),
    (("report", "stable_member"), True),
    (("report", "principal_roots", 0, "name"), "other_theorem"),
    (("report", "principal_roots", 0, "node_id"), 0),
    (("report", "principal_roots", 0, "statement_sha256"), "0" * 64),
    (("report", "principal_roots", 0, "complete_ordinary_ha_checked"), False),
    (("report", "principal_roots", 0, "complete_ordinary_ha_checked"), 1),
    (("report", "principal_roots", 0, "ordinary_certificate_nodes"), True),
    (("report", "principal_roots", 0, "ordinary_certificate_nodes"), 1),
    (("report", "principal_roots", 0, "ordinary_certificate_nodes"), 500001),
))
def test_stale_foreign_relabelled_or_incomplete_worker_reports_fail_closed(metadata, path, value):
    message = _message(metadata)
    target = message
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    with pytest.raises(cli.AuditWorkerError):
        _validate(cli._canonical(message), metadata)


@pytest.mark.parametrize("mutation", ("missing_envelope", "extra_envelope", "missing_root", "extra_root", "reordered_roots", "extra_report"))
def test_missing_additional_or_reordered_protocol_fields_rejected(metadata, mutation):
    message = _message(metadata)
    if mutation == "missing_envelope": del message["limits"]
    elif mutation == "extra_envelope": message["accepted_from_saved_receipt"] = True
    elif mutation == "missing_root": message["report"]["principal_roots"].pop()
    elif mutation == "extra_root": message["report"]["principal_roots"].append(deepcopy(message["report"]["principal_roots"][0]))
    elif mutation == "reordered_roots": message["report"]["principal_roots"].reverse()
    else: message["report"]["other_authority"] = True
    with pytest.raises(cli.AuditWorkerError):
        _validate(cli._canonical(message), metadata)


@pytest.mark.parametrize("change", (None, "duplicates", "new_theorems", "prior_theorems",
                                   "ordered_specs_sha256", "exact_ast_novelty_checked"))
def test_whole_tranche_novelty_result_is_exact_and_cannot_skip_prior_generations(change):
    expected = cli._expected_novelty_report()
    message = {
        "schema": cli.WORKER_SCHEMA, "kind": "novelty", "slug": "all",
        "nonce": NONCE, "binding_sha256": BINDING,
        "limits": {"cpu": [170, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024},
        "peak_rss_bytes": 100, "report": deepcopy(expected),
    }
    if change is not None:
        message["report"][change] = {
            "duplicates": [["new_name", "old_name"]], "new_theorems": 124,
            "prior_theorems": 3392, "ordered_specs_sha256": "0" * 64,
            "exact_ast_novelty_checked": False,
        }[change]
    arguments = dict(kind="novelty", slug="all", nonce=NONCE, binding=BINDING, expected=expected)
    if change is None:
        assert cli._validate_message(cli._canonical(message), **arguments) == (expected, 100)
    else:
        with pytest.raises(cli.AuditWorkerError):
            cli._validate_message(cli._canonical(message), **arguments)


@pytest.mark.parametrize("payload", (
    b"", b"{}\r\n", b"{}", b"[]\n", b"\xff\n", b'{"a":1,"a":2}\n',
    b'{"a":NaN}\n', b'{"a":Infinity}\n', b'{"a":-Infinity}\n',
    b"{}\n{}\n", b"banner\n{}\n", b" " + b"x" * (128 * 1024),
))
def test_worker_json_is_strict_canonical_duplicate_free_and_byte_bounded(payload):
    with pytest.raises(cli.AuditWorkerError):
        cli._decode_message(payload)


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "reordered", "wrong_count", "foreign"))
def test_exact_registry_guard_rejects_before_loading_any_rows(monkeypatch, mutation):
    items = cli.checkpoints.CHECKPOINTS
    if mutation == "missing": changed = items[:-1]
    elif mutation == "duplicate": changed = (*items, items[0])
    elif mutation == "reordered": changed = tuple(reversed(items))
    elif mutation == "wrong_count": changed = (replace(items[0], frontier_count=13), *items[1:])
    else: changed = (replace(items[0], slug="foreign"), *items[1:])
    monkeypatch.setattr(cli.checkpoints, "CHECKPOINTS", changed)
    def forbidden():
        raise AssertionError("invalid registry reached source loading")
    monkeypatch.setattr(cli.checkpoints, "all_new_rows", forbidden)
    with pytest.raises(cli.AuditWorkerError, match="inventory"):
        cli._inventory()


def test_actual_source_and_cached_factory_output_are_authenticated(monkeypatch):
    item = cli.checkpoints.CHECKPOINTS[0]
    original = cli.checkpoints.load_rows(item)
    module = sys.modules["peano_lab.library." + item.modules[0].module]
    monkeypatch.setattr(module, item.modules[0].factory,
                        lambda _: (replace(original[0], script=("refl",)), *original[1:]))
    with pytest.raises(cli.checkpoints.CheckpointError, match="specifications"):
        cli._binding()


def test_actual_parent_digest_is_rechecked_even_if_snapshot_was_cached(monkeypatch):
    cli.checkpoints.closure.parent_snapshot()
    monkeypatch.setattr(cli.checkpoints.closure, "PARENT_CATALOG_SHA256", "0" * 64)
    with pytest.raises(ValueError, match="bytes changed"):
        cli._binding()


def test_real_bounded_pipe_transport_accepts_only_clean_success():
    command = [sys.executable, "-c", "import sys;sys.stdout.buffer.write(b'{}\\n')"]
    assert cli._capture_bounded(command, os.environ.copy(), timeout=5) == b"{}\n"


@pytest.mark.parametrize("program,match", (
    ("import sys;sys.exit(7)", "status 7"),
    ("import os,signal;os.kill(os.getpid(),signal.SIGTERM)", "status"),
    ("import sys;sys.stderr.write('warning')", "status 0"),
    ("import sys;sys.stdout.buffer.write(b'x'*131073)", "byte bound"),
    ("import sys;sys.stderr.buffer.write(b'x'*8193)", "byte bound"),
))
def test_real_nonzero_signal_and_oversized_pipe_processes_are_rejected(program, match):
    with pytest.raises(cli.AuditWorkerError, match=match):
        cli._capture_bounded([sys.executable, "-c", program], os.environ.copy(), timeout=5)


def test_real_timeout_is_terminated_without_reading_unbounded_output():
    with pytest.raises(cli.AuditWorkerError, match="timeout"):
        cli._capture_bounded([sys.executable, "-c", "import time;time.sleep(2)"],
                             os.environ.copy(), timeout=0.1)


def test_worker_command_is_exact_shell_free_and_pinned_to_this_workspace(metadata, monkeypatch):
    monkeypatch.setattr(cli.secrets, "token_hex", lambda count: NONCE if count == 32 else None)
    observed = []
    def transport(command, environment):
        observed.append((command, environment))
        return cli._canonical(_message(metadata))
    monkeypatch.setattr(cli, "_capture_bounded", transport)
    cli._run_worker("family", "divisor-involutions", BINDING, metadata)
    command, environment = observed[0]
    assert command == [sys.executable, str(cli.SCRIPT), "--worker", "family", "--slug",
                       "divisor-involutions", "--nonce", NONCE, "--binding", BINDING]
    assert environment["PYTHONPATH"] == os.pathsep.join((str(ROOT/"peano-lab/py"), str(ROOT/"scripts")))
    assert environment["PYTHONMALLOC"] == "malloc" and environment["PYTHONNOUSERSITE"] == "1"


def test_fresh_jobs_are_sequential_and_every_family_required_before_aggregation(monkeypatch):
    observed = []
    monkeypatch.setattr(cli, "_binding", lambda: BINDING)
    monkeypatch.setattr(cli, "_expected_novelty_report", lambda: {})
    monkeypatch.setattr(cli, "_expected_family_report", lambda item: {})
    def worker(kind, slug, binding, expected):
        observed.append((kind, slug))
        if slug == "rectangular-sums":
            raise cli.AuditWorkerError("deliberate worker failure")
        return {}, 1
    def aggregate(_):
        raise AssertionError("failed worker reached success aggregation")
    monkeypatch.setattr(cli, "_run_worker", worker)
    monkeypatch.setattr(cli.checkpoints, "_aggregate_reports", aggregate)
    with pytest.raises(cli.AuditWorkerError, match="deliberate"):
        cli.verify_in_fresh_windows()
    assert observed == [("novelty", "all"), ("family", "divisor-involutions"),
                        ("family", "mobius-divisor-cancellation"), ("family", "rectangular-sums")]


@pytest.mark.parametrize("arguments", (
    ("--worker", "family", "--write"), ("--worker", "novelty", "--check"),
    ("--slug", "divisor-involutions"), ("--nonce", NONCE), ("--binding", BINDING),
    ("--worker", "family"), ("--check", "--write"),
))
def test_private_workers_cannot_read_write_or_impersonate_complete_audits(arguments):
    with pytest.raises(SystemExit) as error:
        cli.main(list(arguments))
    assert error.value.code == 2


@pytest.mark.parametrize("mode", ("--check", "--write"))
def test_failure_prevents_receipt_read_or_write_even_when_old_success_file_exists(tmp_path, monkeypatch, mode):
    receipt = tmp_path/"audit.json"
    if mode == "--check": receipt.write_bytes(b"old success is not authority\n")
    monkeypatch.setattr(cli, "RECEIPT", receipt)
    monkeypatch.setattr(cli.resource, "setrlimit", lambda *_: None)
    monkeypatch.setattr(cli.signal, "alarm", lambda *_: None)
    def reject():
        raise cli.AuditWorkerError("fresh checks failed")
    monkeypatch.setattr(cli, "verify_in_fresh_windows", reject)
    def forbidden(*_):
        raise AssertionError("failed proofs reached saved-receipt comparison")
    monkeypatch.setattr(cli, "check_receipt_bytes", forbidden)
    with pytest.raises(cli.AuditWorkerError, match="fresh checks"):
        cli.main([mode])
    assert receipt.read_bytes() == b"old success is not authority\n" if mode == "--check" else not receipt.exists()


def test_worker_and_controller_limits_and_exclusive_write_are_explicit():
    tree = ast.parse(cli.SCRIPT.read_text())
    worker = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_worker")
    main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
    worker_text = ast.unparse(worker)
    assert "resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)" in worker_text
    assert "signal.alarm(WALL_SECONDS)" in worker_text
    assert "ordinary_roots=True" in worker_text
    assert worker_text.count("_binding()") == 2
    assert "statement_duplicates(rows)" in worker_text
    main_text = ast.unparse(main)
    assert "signal.alarm(CONTROLLER_WALL_SECONDS)" in main_text
    assert "RECEIPT.open('x', encoding='utf-8')" in main_text
    assert main_text.index("verify_in_fresh_windows()") < main_text.index("check_receipt_bytes(")
    assert main_text.count("authoring_rss_bytes()") == 2


def test_original_proof_verifier_function_is_byte_identical_to_reviewed_baseline():
    path = ROOT/"scripts/constructive_lower_continuation_checkpoints.py"
    source = path.read_text()
    node = next(n for n in ast.parse(source).body if isinstance(n, ast.FunctionDef) and n.name == "verify_checkpoint")
    assert sha256(ast.get_source_segment(source, node).encode()).hexdigest() == (
        "735571e190a7b88678294f3208ecab84d83375b855e994b8e404f0b276a1267c"
    )


def test_actual_fresh_family_worker_checks_complete_ha_real_lean_and_three_ordinary_roots(metadata):
    before = cli.RECEIPT.read_bytes() if cli.RECEIPT.exists() else None
    binding = cli._binding()
    report, peak = cli._run_worker("family", "divisor-involutions", binding, metadata)
    assert report["new_theorem_count"] == 12
    assert report["bundle"]["original_ha_checked"] is report["bundle"]["independent_lean_checked"] is True
    assert [row["name"] for row in report["principal_roots"]] == list(cli.checkpoints.CHECKPOINTS[0].principal_roots)
    assert all(row["complete_ordinary_ha_checked"] is True and row["ordinary_certificate_nodes"] > 1
               for row in report["principal_roots"])
    assert 0 < peak <= 1536 * 1024 * 1024
    after = cli.RECEIPT.read_bytes() if cli.RECEIPT.exists() else None
    assert after == before, "a family worker must neither create nor change the final audit"
