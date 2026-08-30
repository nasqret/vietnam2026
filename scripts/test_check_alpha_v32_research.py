"""Non-authorizing protocol tests for the fifteen-job Alpha-v32 release audit.

Synthetic values below exercise only transport and metadata validation. They
never represent checked mathematics, instantiate a live audit, write a release,
or turn a rejecting checker into an accepting one. Positive proof evidence is
obtained only by the actual runtime tests and the real fifteen-worker command.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import importlib
import inspect
import json
import os
from pathlib import Path
import resource
import signal
import sys
import time
from types import SimpleNamespace

_BOUNDED_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest

ROOT = Path(__file__).resolve().parents[1]
for directory in (ROOT / "scripts", ROOT / "peano-lab/py"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import check_alpha_v32_research as audit


def _tree(name):
    return ast.parse(inspect.getsource(getattr(audit, name)))


def _calls(name):
    return [ast.unparse(node.func) for node in ast.walk(_tree(name)) if isinstance(node, ast.Call)]


def _stop(*_args, **_kwargs):
    pytest.fail("a non-authorizing protocol test reached proof acceptance or publication")


def test_exact_fifteen_job_scope_and_original_resource_transport():
    assert audit.EXPECTED_INVENTORY == (
        ("multiplicative-convolution", 90), ("polynomial-division-prerequisites", 85),
    )
    rows = audit.registry()
    assert len(rows) == 2 and tuple(len(row.principal_roots) for row in rows) == (6, 6)
    assert 1 + len(rows) + sum(len(row.principal_roots) for row in rows) == audit.EXPECTED_JOB_COUNT == 15
    assert audit.CPU_LIMITS == audit.transport.CPU_LIMITS == (170, 175)
    assert audit.WALL_SECONDS == audit.transport.WALL_SECONDS == 180
    assert audit.PARENT_TIMEOUT_SECONDS == audit.transport.PARENT_TIMEOUT_SECONDS == 185
    assert audit.MAX_RSS_BYTES == audit.transport.MAX_RSS_BYTES == 1536 * 1024 * 1024
    assert audit.MAX_STDOUT_BYTES == audit.transport.MAX_STDOUT_BYTES == 128 * 1024
    assert audit.MAX_STDERR_BYTES == audit.transport.MAX_STDERR_BYTES == 8 * 1024
    assert audit.transport is importlib.import_module("check_constructive_lower_continuation")
    assert audit.independent is importlib.import_module("constructive_bottom_layer_checkpoints")


@pytest.mark.parametrize("index,module", (
    (0, "constructive_g009_checkpoints"), (1, "constructive_polynomial_division_checkpoints"),
))
def test_actual_independent_research_pins_match_without_running_old_verifiers(index, module):
    original = importlib.import_module(module)
    item = audit.registry()[index]
    pin = original.FINAL_ARTIFACT
    assert (item.artifact, item.artifact_bytes, item.artifact_sha256) == (pin.path, pin.bytes, pin.sha256)
    assert item.principal_roots == original.PRINCIPAL_ROOTS
    assert item.frontier_specs_sha256 == original.support.NEW_SPECS_SHA256
    assert tuple(source.path for source in original.support.MATH_SOURCE_PINS) == tuple(p.path for p in item.modules)
    assert tuple(source.sha256 for source in original.support.MATH_SOURCE_PINS) == tuple(p.sha256 for p in item.modules)


@pytest.mark.parametrize("module", (
    "arithmetic_multiplicative_candidate", "coprime_divisor_decomposition_candidate",
    "divisor_pair_index_candidate", "signed_block_sum_candidate",
    "signed_cartesian_product_candidate", "signed_support_reindex_candidate",
    "dirichlet_multiplicative_entry_candidate", "dirichlet_multiplicative_support_candidate",
    "dirichlet_multiplicative_candidate", "prime_field_polynomial_subtraction_candidate",
    "prime_field_polynomial_trim_candidate", "prime_field_polynomial_monic_candidate",
    "prime_field_polynomial_synthetic_candidate",
))
def test_every_module_uses_its_real_test_provenance(module):
    shared = {"dirichlet_multiplicative_support_candidate", "dirichlet_multiplicative_candidate"}
    expected = "test_dirichlet_multiplicative_closure_candidate.py" if module in shared else "test_" + module + ".py"
    assert audit.module_test_path(module) == "peano-lab/py/tests/" + expected
    assert (ROOT / audit.module_test_path(module)).is_file()


@pytest.mark.parametrize("module", (None, True, 1, "", "../escape", "missing_candidate", []))
def test_unknown_module_cannot_invent_a_provenance_path(module):
    with pytest.raises(audit.AuditError):
        audit.module_test_path(module)


def test_all_actual_runtime_inputs_and_original_checker_adapters_are_bound():
    paths = set(audit._runtime_source_paths())
    assert all(not path.startswith("/") and ".." not in Path(path).parts for path in paths)
    for path in (
        "peano-lab/py/peano_lab/__init__.py",
        "peano-lab/py/peano_lab/kernel/checker.py",
        "peano-lab/py/peano_lab/kernel/subst.py",
        "peano-lab/py/peano_lab/engine/state.py",
        "peano-lab/py/peano_lab/library/editions_v31.py",
        "peano-lab/py/peano_lab/library/editions_v32.py",
        "peano-lab/py/peano_lab/library/campaign_research_v32_closure.py",
    ):
        assert path in paths
    assert set(audit.previous_audit.CONTROL_SOURCES) <= set(audit.CONTROL_SOURCES)
    for name in ("check_alpha_v32_research.py", "build_peano_library_channels_v32.py",
                 "verify_peano_library_channels_v32.py", "peano_catalog_shards_v32.py"):
        assert "scripts/" + name in audit.CONTROL_SOURCES
    calls = _calls("source_binding")
    assert "parent_catalog.verify_catalog_bindings" in calls
    assert "parent_catalog.load_catalog" not in calls
    assert "research.validate_research_source_bytes" in calls
    assert "independent._check_lean_binary" in calls
    assert "_file_digest" in calls and "_relative_path" in calls


def test_exact_parent_catalogue_and_additional_evidence_pins():
    assert (audit.PARENT_PATH, audit.PARENT_BYTES, audit.PARENT_SHA256) == (
        "artifacts/peano-library/alpha/catalog-v31.json", 293294,
        "6c9ebfb3c37e42aefab200b710f78e7693dc5826c80f053544deea41caf44aab",
    )
    expected = {
        "artifacts/peano-library/alpha/metrics-v31.json",
        "artifacts/peano-library/alpha/dependency-graph-v31.mmd",
        "artifacts/peano-library/channels-v31.json",
        "artifacts/peano-library/catalog-v1.json",
    }
    assert {path for path, _, _ in audit.PARENT_EVIDENCE_PINS} == expected
    for path, size, digest in audit.PARENT_EVIDENCE_PINS:
        assert audit._file_digest(path, audit.parent_catalog.MAX_CATALOG_BYTES,
                                  expected_bytes=size, expected_sha256=digest) == (size, digest)


@pytest.fixture
def transport_file(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    monkeypatch.setattr(audit, "ROOT", root)
    raw = b"transport-only bytes; not a proof or a catalogue\n"
    path = root / "source.bin"
    path.write_bytes(raw)
    return root, path, raw


def test_streamed_byte_authentication_is_relocatable_not_an_acceptance(transport_file, monkeypatch):
    root, path, raw = transport_file
    wanted = (len(raw), sha256(raw).hexdigest())
    assert audit._relative_path(path) == "source.bin"
    assert audit._file_digest("source.bin", 1024, expected_bytes=len(raw), expected_sha256=wanted[1]) == wanted
    moved = root / "relocated"
    moved.mkdir()
    (moved / "source.bin").write_bytes(raw)
    monkeypatch.setattr(audit, "ROOT", moved)
    assert audit._relative_path(moved / "source.bin") == "source.bin"
    assert audit._file_digest("source.bin", 1024) == wanted


@pytest.mark.parametrize("path", (Path("/foreign.py"), Path("../escape.py"), "source.bin", None, True))
def test_foreign_or_untyped_source_identity_fails_closed(transport_file, path):
    with pytest.raises(audit.AuditError):
        audit._relative_path(path)


@pytest.mark.parametrize("path", ("", "/source.bin", "../source.bin", "a/../source.bin",
                                  "./source.bin", "a//source.bin", "a\\source.bin", None, True))
def test_unsafe_repository_paths_fail_before_opening(transport_file, monkeypatch, path):
    monkeypatch.setattr(audit.parent_catalog, "_opened", _stop)
    with pytest.raises(audit.AuditError):
        audit._file_digest(path, 1024)


@pytest.mark.parametrize("maximum,size,digest", (
    (True, None, None), (0, None, None), (-1, None, None),
    (64 * 1024 * 1024 + 1, None, None),
    (1024, True, None), (1024, 0, None), (1024, 1025, None),
    (1024, None, True), (1024, None, "0"), (1024, None, "A" * 64),
))
def test_invalid_stream_bounds_and_literal_pins_fail_before_opening(transport_file, monkeypatch, maximum, size, digest):
    monkeypatch.setattr(audit.parent_catalog, "_opened", _stop)
    with pytest.raises(audit.AuditError):
        audit._file_digest("source.bin", maximum, expected_bytes=size, expected_sha256=digest)


@pytest.mark.parametrize("attack", ("leaf_symlink", "ancestor_symlink", "directory", "fifo",
                                    "missing", "oversize", "wrong_size", "wrong_hash", "owner"))
def test_streamed_input_types_and_wrong_bytes_are_rejected(transport_file, monkeypatch, attack):
    root, path, raw = transport_file
    name = "source.bin"
    kwargs = {}
    maximum = 1024
    if attack == "leaf_symlink":
        (root / "linked").symlink_to(path)
        name = "linked"
    elif attack == "ancestor_symlink":
        real = root / "real"
        real.mkdir()
        (real / "file").write_bytes(raw)
        (root / "alias").symlink_to(real, target_is_directory=True)
        name = "alias/file"
    elif attack == "directory":
        (root / "directory").mkdir()
        name = "directory"
    elif attack == "fifo":
        os.mkfifo(root / "pipe")
        name = "pipe"
    elif attack == "missing":
        name = "missing"
    elif attack == "oversize":
        maximum = len(raw) - 1
    elif attack == "wrong_size":
        kwargs["expected_bytes"] = len(raw) + 1
    elif attack == "wrong_hash":
        kwargs["expected_sha256"] = "0" * 64
    elif attack == "owner":
        monkeypatch.setattr(audit.parent_catalog, "_owner", lambda _value: os.geteuid() + 1)
    with pytest.raises(audit.AuditError):
        audit._file_digest(name, maximum, **kwargs)


@pytest.mark.parametrize("attack", ("grow", "truncate", "same_size", "replace"))
def test_changes_during_actual_stream_reads_fail_closed(transport_file, monkeypatch, attack):
    root, path, raw = transport_file
    original = os.read
    changed = False
    def observed(fd, size):
        nonlocal changed
        block = original(fd, size)
        if not changed and block:
            changed = True
            if attack == "grow":
                path.write_bytes(raw + b"x")
            elif attack == "truncate":
                path.write_bytes(raw[:-1])
            elif attack == "same_size":
                path.write_bytes(b"x" + raw[1:])
            else:
                other = root / "replacement"
                other.write_bytes(raw)
                other.replace(path)
        return block
    monkeypatch.setattr(os, "read", observed)
    with pytest.raises(audit.AuditError):
        audit._file_digest("source.bin", 1024)
    assert changed


def test_streaming_reads_are_bounded_to_actual_size_and_one_mib(transport_file, monkeypatch):
    _, _, raw = transport_file
    original = os.read
    sizes = []
    def observed(fd, size):
        sizes.append(size)
        assert 0 < size <= 1024 * 1024
        return original(fd, size)
    monkeypatch.setattr(os, "read", observed)
    assert audit._file_digest("source.bin", 1024)[0] == len(raw)
    assert sizes == [len(raw), 1]


def _envelope():
    return {"schema": audit.WORKER_SCHEMA, "kind": "novelty", "slug": "all",
            "nonce": "a" * 64, "binding_sha256": "b" * 64, "peak_rss_bytes": 4096,
            "limits": {"cpu": [170, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024},
            "report": {"transport_only": "NOT mathematical evidence"}}


def _validate(payload):
    return audit._validate_message(payload, kind="novelty", slug="all", nonce="a"*64, binding="b"*64)


@pytest.mark.parametrize("field,value", (
    ("schema", "old"), ("kind", "family"), ("slug", "other"), ("nonce", "c" * 64),
    ("binding_sha256", "c" * 64), ("peak_rss_bytes", 0), ("peak_rss_bytes", True),
    ("peak_rss_bytes", 1536 * 1024 * 1024 + 1), ("peak_rss_bytes", 1.0),
    ("limits", {"cpu": [171, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024}),
    ("limits", {"cpu": [170, 175], "wall_seconds": True, "max_rss_bytes": 1536 * 1024 * 1024}),
    ("limits", {"cpu": [170, 175], "wall_seconds": 181, "max_rss_bytes": 1536 * 1024 * 1024}),
))
def test_wrong_live_envelope_never_reaches_any_report_gate(monkeypatch, field, value):
    payload = _envelope()
    payload[field] = value
    monkeypatch.setattr(audit, "_validate_report", _stop)
    with pytest.raises(audit.AuditError):
        _validate(audit.canonical(payload))


@pytest.mark.parametrize("mutation", ("extra", "missing", "duplicate", "nan", "list", "empty", "truncated"))
def test_noncanonical_or_malformed_protocol_is_rejected_before_reports(monkeypatch, mutation):
    value = _envelope()
    if mutation == "extra":
        value["extra"] = "not permitted"
        payload = audit.canonical(value)
    elif mutation == "missing":
        del value["report"]
        payload = audit.canonical(value)
    elif mutation == "duplicate":
        payload = audit.canonical(value).replace(b'"schema":', b'"schema":"duplicate","schema":')
    elif mutation == "nan":
        payload = audit.canonical(value).replace(b"4096", b"NaN")
    elif mutation == "list":
        payload = b"[]"
    elif mutation == "empty":
        payload = b""
    else:
        payload = audit.canonical(value)[:-2]
    monkeypatch.setattr(audit, "_validate_report", _stop)
    with pytest.raises(audit.AuditError):
        _validate(payload)


def test_even_well_formed_envelope_must_reach_a_real_report_gate(monkeypatch):
    class NoProofReport(Exception):
        pass
    def reject(*_args, **_kwargs):
        raise NoProofReport("metadata bytes cannot accept a theorem")
    monkeypatch.setattr(audit, "_validate_report", reject)
    with pytest.raises(NoProofReport):
        _validate(audit.canonical(_envelope()))


def test_subprocess_request_has_original_limits_and_no_saved_receipt_input(monkeypatch):
    captured = {}
    def invalid_capture(command, environment):
        captured.update(command=command, environment=environment)
        return b"{}"
    monkeypatch.setattr(audit.transport, "_capture_bounded", invalid_capture)
    monkeypatch.setattr(audit, "_validate_report", _stop)
    with pytest.raises(audit.AuditError):
        audit._run_worker("novelty", "a" * 64)
    env = captured["environment"]
    command = captured["command"]
    assert env["PYTHONMALLOC"] == "pymalloc" and env["PYTHONNOUSERSITE"] == "1"
    assert env["PYTHONDONTWRITEBYTECODE"] == "1"
    assert env["PYTHONPATH"] == os.pathsep.join((str(ROOT/"peano-lab/py"), str(ROOT/"scripts")))
    assert command[:2] == [sys.executable, str(audit.SCRIPT)]
    assert command[2:6] == ["--worker", "novelty", "--slug", "all"]
    assert "--receipt" not in command and "--skip" not in command and "--accepted" not in command


@pytest.mark.parametrize("failed_job", range(15))
def test_any_failed_job_prevents_live_audit_minting(monkeypatch, failed_job):
    # Scheduling-only fixture: every run MUST fail and cannot mint a capability.
    items = audit.registry()
    seen = []
    monkeypatch.setattr(audit, "_inventory_rows", lambda: ())
    monkeypatch.setattr(audit, "source_binding", lambda: "a" * 64)
    monkeypatch.setattr(audit, "FreshProofAudit", _stop)
    def rejecting_schedule(kind, binding, *, item=None, name=None, family=None):
        seen.append((kind, None if item is None else item.slug, name))
        if len(seen) - 1 == failed_job:
            raise audit.AuditError("intentional non-authority scheduling failure")
        return {"transport_only": "NOT proof evidence"}, 1
    monkeypatch.setattr(audit, "_run_worker", rejecting_schedule)
    with pytest.raises(audit.AuditError, match="scheduling failure"):
        audit.verify_in_fresh_windows()
    expected = [("novelty", None, None)]
    for item in items:
        expected.append(("family", item.slug, None))
        expected.extend(("root", item.slug, name) for name in item.principal_roots)
    assert seen == expected[:failed_job + 1]


@pytest.mark.parametrize("token", (None, False, 0, "", b"saved report", object()))
def test_saved_data_cannot_create_a_live_proof_audit(token):
    with pytest.raises(audit.AuditError, match="saved report"):
        audit.FreshProofAudit(token, "a" * 64, {"not": "proof"}, 1)


@pytest.mark.parametrize("args", (
    ["--receipt", "saved.json"], ["--skip"], ["--accepted"], ["--binding", "a"*64],
    ["--worker", "root", "--slug", "x"], ["--worker", "novelty", "--root", "x"],
))
def test_no_cli_saved_success_or_incomplete_worker_modes(monkeypatch, args):
    monkeypatch.setattr(audit, "verify_in_fresh_windows", _stop)
    monkeypatch.setattr(audit, "_worker", _stop)
    with pytest.raises(SystemExit) as error:
        audit.main(args)
    assert error.value.code == 2


def test_actual_family_gate_keeps_original_ha_and_same_byte_independent_lean():
    calls = _calls("_family")
    assert "edition.checked_research_bundle" in calls
    assert "research.read_research_bundle_bytes" in calls
    assert "independent._lean_check" in calls
    text = ast.unparse(_tree("_family"))
    assert "independent._lean_check(item, receipt.node_count, bundle.root, payload)" in text
    assert "receipt.kernel_calls != len(bundle.nodes)" in text
    assert audit.independent.LEAN_TIMEOUT_SECONDS == 30
    assert audit.independent.LEAN_BINARY_BYTES == 106787344
    assert audit.independent.LEAN_BINARY_SHA256 == "22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033"


def test_ordinary_gate_always_compares_exact_spec_and_original_empty_context_check():
    text = ast.unparse(_tree("_root"))
    assert "edition.replay(name, edition='alpha')" in text
    assert "result.spec != rows[name]" in text and "result.formula != exact" in text
    assert "check((), result.certificate, exact)" in text
    assert "name not in item.principal_roots" in text


def test_novelty_is_exact_ast_bytes_against_all_3796_and_all_new_peers():
    text = ast.unparse(_tree("_novelty"))
    assert "FormulaArena().freeze(_closed_formula(spec.statement)).to_json()" in text
    assert "_edition().v31.ALPHA_CHECKED_SPECS" in text
    assert "if encoded == other" in text
    assert "'new_theorems': 175" in text and "'prior_theorems': 3796" in text
    assert "'exact_ast_novelty_checked': True" in text


def test_worker_limits_and_final_rebinding_precede_every_output_byte():
    tree = _tree("_worker").body[0]
    statements = [ast.unparse(node) for node in tree.body]
    assert statements[0] == "resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)"
    assert statements[1] == "signal.alarm(WALL_SECONDS)"
    assert "source_binding() != binding" in statements[2]
    assert statements[3] == "gc.collect()"
    assert sum("source_binding() != binding" in line for line in statements) == 2
    first_write = next(i for i, line in enumerate(statements) if "sys.stdout.buffer.write" in line)
    last_guard = max(i for i, line in enumerate(statements) if "source_binding() != binding" in line)
    assert last_guard < first_write
    assert statements[first_write - 1] == "authoring_rss_bytes()"


def test_live_audit_report_is_canonical_private_bytes_and_copied_on_access():
    constructor = inspect.getsource(audit.FreshProofAudit.__init__)
    getter = inspect.getsource(audit.FreshProofAudit.report.fget)
    gate = inspect.getsource(audit.FreshProofAudit.require_unchanged)
    assert "token is not _LIVE_AUDIT" in constructor
    assert "self._report_bytes = canonical(report)" in constructor
    assert "json.loads(self._report_bytes)" in getter
    assert "source_binding() != self._binding" in gate
    assert "type(self) is not FreshProofAudit" in gate


@pytest.fixture
def shape_only(monkeypatch):
    """Only private metadata shape: false statements and no certificate exist."""
    from peano_lab.library import campaign_research_v32_closure as research
    rows = (SimpleNamespace(name="transport_only_false", statement="0 = 1"),
            SimpleNamespace(name="transport_only_false_again", statement="1 = 0"))
    item = SimpleNamespace(
        slug="transport-metadata-only", artifact="NOT-A-PROOF-FILE", artifact_bytes=1,
        artifact_sha256="c" * 64, frontier_specs_sha256="d" * 64,
        principal_roots=(rows[0].name,), frontier_count=2,
    )
    sealed = SimpleNamespace(node_count=3, bundle_edges=2, body_nodes=6)
    positions = {row.name: index for index, row in enumerate(rows)}
    plan = SimpleNamespace(family=sealed, positions=positions)
    monkeypatch.setattr(audit, "_owned", lambda _item: rows)
    monkeypatch.setattr(research, "research_plan", lambda _slug: plan)
    monkeypatch.setattr(audit, "_edition", lambda: SimpleNamespace(
        FRONTIER_NEW_NAMES=tuple(row.name for row in rows),
        ALPHA_EDITION=SimpleNamespace(by_name={row.name: SimpleNamespace(spec=row) for row in rows}),
    ))
    report = {
        "slug": item.slug, "new_theorem_count": 2, "specs_sha256": item.frontier_specs_sha256,
        "owned_node_ids": positions.copy(),
        "rows": [{"name": row.name, "node_id": positions[row.name],
                  "statement_sha256": sha256(row.statement.encode()).hexdigest(),
                  "proof_nodes": 3, "proof_depth": 2, "proof_objects": 3,
                  "proof_edges": 2, "reused_objects": 0} for row in rows],
        "bundle": {
            "path": item.artifact, "bytes": item.artifact_bytes, "sha256": item.artifact_sha256,
            "nodes_including_packaging_root": 3, "dependency_edges_including_packaging": 2,
            "body_proof_nodes": 6, "packaging_root_id": 2, "kernel_calls": 3,
            "original_ha_checked": True, "independent_lean_checked": True,
        }, "principal_roots": [],
    }
    return item, report, rows


def test_private_shape_validation_is_not_a_proof_acceptance_capability(shape_only):
    item, report, _ = shape_only
    assert audit._validate_family_report(report, item) is report
    assert not isinstance(report, audit.FreshProofAudit)
    assert report["bundle"]["path"] == "NOT-A-PROOF-FILE"


@pytest.mark.parametrize("field,value", (
    ("slug", "foreign"), ("new_theorem_count", True), ("new_theorem_count", 1),
    ("specs_sha256", "0" * 64), ("owned_node_ids", {}), ("owned_node_ids", []),
    ("rows", []), ("rows", {}), ("principal_roots", ["saved root"]), ("principal_roots", ()),
))
def test_exact_family_report_fields_cannot_be_missing_retyped_or_substituted(shape_only, field, value):
    item, report, _ = shape_only
    report[field] = value
    with pytest.raises(audit.AuditError):
        audit._validate_family_report(report, item)


@pytest.mark.parametrize("place", ("family", "bundle", "row"))
@pytest.mark.parametrize("attack", ("extra", "missing"))
def test_no_extra_or_missing_report_keys(shape_only, place, attack):
    item, report, _ = shape_only
    target = report if place == "family" else report["bundle"] if place == "bundle" else report["rows"][0]
    if attack == "extra":
        target["not_an_authority_extension"] = True
    else:
        del target[next(iter(target))]
    with pytest.raises(audit.AuditError):
        audit._validate_family_report(report, item)


@pytest.mark.parametrize("field,value", (
    ("path", "other"), ("bytes", True), ("bytes", 2), ("sha256", "0" * 64),
    ("nodes_including_packaging_root", True), ("nodes_including_packaging_root", 2),
    ("dependency_edges_including_packaging", 0), ("body_proof_nodes", 0),
    ("packaging_root_id", 0), ("kernel_calls", 2),
    ("original_ha_checked", False), ("original_ha_checked", 1),
    ("independent_lean_checked", False), ("independent_lean_checked", 1),
))
def test_frozen_whole_bundle_identity_and_all_actual_gates_are_exact(shape_only, field, value):
    item, report, _ = shape_only
    report["bundle"][field] = value
    with pytest.raises(audit.AuditError):
        audit._validate_family_report(report, item)


@pytest.mark.parametrize("field,value", (
    ("name", "other"), ("node_id", True), ("node_id", -1), ("node_id", 2),
    ("statement_sha256", "0" * 64), ("proof_nodes", True), ("proof_nodes", 0),
    ("proof_depth", 0), ("proof_depth", 4), ("proof_objects", 4),
    ("proof_objects", 0), ("proof_edges", 0), ("proof_edges", 3),
    ("reused_objects", 1), ("reused_objects", -1), ("proof_nodes", 10**9),
))
def test_exact_statement_node_types_bounds_and_metric_accounting_fail_closed(shape_only, field, value):
    item, report, _ = shape_only
    report["rows"][0][field] = value
    with pytest.raises(audit.AuditError):
        audit._validate_family_report(report, item)


@pytest.mark.parametrize("attack", ("row_order", "duplicate_row", "node_map", "boolean_node_map"))
def test_all_owned_rows_remain_exact_unique_and_in_source_order(shape_only, attack):
    item, report, rows = shape_only
    if attack == "row_order":
        report["rows"].reverse()
    elif attack == "duplicate_row":
        report["rows"][1] = report["rows"][0]
    elif attack == "node_map":
        report["owned_node_ids"][rows[0].name] = 1
    else:
        report["owned_node_ids"][rows[0].name] = False
    with pytest.raises(audit.AuditError):
        audit._validate_family_report(report, item)


@pytest.mark.parametrize("attack", ("wrong_name", "wrong_slug", "wrong_node", "wrong_statement",
                                    "missing", "false", "integer_flag", "boolean_nodes",
                                    "zero_nodes", "huge_nodes", "extra"))
def test_ordinary_report_is_exact_not_a_wildcard(shape_only, attack):
    item, family, rows = shape_only
    report = {
        "slug": item.slug, "name": rows[0].name, "node_id": 0,
        "statement_sha256": sha256(rows[0].statement.encode()).hexdigest(),
        "complete_ordinary_ha_checked": True, "ordinary_certificate_nodes": 3,
    }
    changes = {
        "wrong_name": ("name", "other"), "wrong_slug": ("slug", "other"),
        "wrong_node": ("node_id", 1), "wrong_statement": ("statement_sha256", "0"*64),
        "false": ("complete_ordinary_ha_checked", False),
        "integer_flag": ("complete_ordinary_ha_checked", 1),
        "boolean_nodes": ("ordinary_certificate_nodes", True),
        "zero_nodes": ("ordinary_certificate_nodes", 0),
        "huge_nodes": ("ordinary_certificate_nodes", 10**12),
        "extra": ("extra", True),
    }
    if attack == "missing":
        del report["complete_ordinary_ha_checked"]
    else:
        field, value = changes[attack]
        report[field] = value
    with pytest.raises(audit.AuditError):
        audit._validate_report(report, kind="root", item=item, name=rows[0].name, family=family)


@pytest.mark.parametrize("field,value", (
    ("new_theorems", 174), ("prior_theorems", 3795), ("duplicates", [["x", "y"]]),
    ("exact_ast_novelty_checked", False), ("exact_ast_novelty_checked", 1),
    ("ordered_names_sha256", "0" * 64), ("unrelated", True),
))
def test_novelty_report_cannot_drop_parent_rows_or_hide_duplicates(shape_only, field, value):
    _, _, rows = shape_only
    report = {"new_theorems": 175, "prior_theorems": 3796, "duplicates": [],
              "exact_ast_novelty_checked": True,
              "ordered_names_sha256": sha256("\n".join(row.name for row in rows).encode()).hexdigest()}
    report[field] = value
    with pytest.raises(audit.AuditError):
        audit._validate_report(report, kind="novelty")


@pytest.mark.parametrize("attack", ("open_hypothesis", "other_certificate", "other_formula", "other_spec"))
def test_actual_original_kernel_or_exact_metadata_rejects_false_ordinary_returns(monkeypatch, attack):
    from peano_lab.kernel.formulas import Bot
    from peano_lab.kernel.proofs import EqRefl, Hyp
    from peano_lab.kernel.terms import Zero
    from peano_lab.library.theorems import TheoremSpec, _closed_formula
    row = TheoremSpec("transport_false_no_proof", "0 = 1", (), (), "not a theorem")
    target = _closed_formula(row.statement)
    result = SimpleNamespace(spec=row, formula=target, certificate=Hyp(0), proof_nodes=1)
    if attack == "other_certificate":
        result.certificate = EqRefl(Zero())
    elif attack == "other_formula":
        result.formula = Bot()
    elif attack == "other_spec":
        result.spec = replace(row, summary="not the original specification")
    item = SimpleNamespace(principal_roots=(row.name,), slug="transport-only")
    monkeypatch.setattr(audit, "_owned", lambda _item: (row,))
    monkeypatch.setattr(audit, "_edition", lambda: SimpleNamespace(
        replay=lambda *_a, **_k: result, checked_research_bundle=_stop,
    ))
    with pytest.raises(audit.AuditError, match="ordinary empty-context"):
        audit._root(item, row.name)


def _main(argv=None):
    """Run only the selected actual tests in one original bounded window."""
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pytest-select", default="")
    parser.add_argument("--case-start", type=int, default=0)
    parser.add_argument("--case-count", type=int)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args(argv)
    if args.case_start < 0 or args.case_count is not None and args.case_count <= 0:
        parser.error("a case window must be positive and bounded")

    class Window:
        def __init__(self):
            self.selected = []
            self.passed = set()
            self.bad = []
        @pytest.hookimpl(trylast=True)
        def pytest_collection_modifyitems(self, session, config, items):
            chosen = items[args.case_start:None if args.case_count is None else args.case_start + args.case_count]
            if args.case_count is not None and len(chosen) != args.case_count:
                raise ValueError("the exact requested case window is unavailable")
            if not chosen:
                raise ValueError("an empty bounded case selection is not a pass")
            selected = {item.nodeid for item in chosen}
            rejected = [item for item in items if item.nodeid not in selected]
            config.hook.pytest_deselected(items=rejected)
            items[:] = chosen
            self.selected = [item.nodeid for item in chosen]
        def pytest_runtest_logreport(self, report):
            if report.when == "call" and report.passed:
                self.passed.add(report.nodeid)
            elif report.failed or report.skipped or getattr(report, "wasxfail", None):
                self.bad.append(report.nodeid)

    plugin = Window()
    options = [str(Path(__file__).resolve()), "-q", "--disable-warnings", "-k", args.pytest_select]
    if args.collect_only:
        options.append("--collect-only")
    status = pytest.main(options, plugins=[plugin])
    peak = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    if sys.platform != "darwin":
        peak *= 1024
    if not 0 < peak <= 1536 * 1024 * 1024:
        raise RuntimeError("the original observed RSS ceiling was exceeded")
    if not args.collect_only and (plugin.bad or plugin.passed != set(plugin.selected)):
        status = status or 1
    print(json.dumps({"selected": len(plugin.selected), "passed": len(plugin.passed),
                      "collect_only": args.collect_only, "pytest_exit_code": int(status),
                      "elapsed_seconds": time.monotonic() - _BOUNDED_STARTED,
                      "peak_rss_bytes": peak, "cpu": list(resource.getrlimit(resource.RLIMIT_CPU)),
                      "wall_seconds": 180}, sort_keys=True), flush=True)
    return int(status)


if __name__ == "__main__":
    raise SystemExit(_main())
