"""Fresh checkpoint evidence, hostile source/checker data, and no admission."""

from dataclasses import fields, is_dataclass, replace
from hashlib import sha256
from pathlib import Path
from importlib import import_module
from types import SimpleNamespace
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import constructive_bottom_layer_checkpoints as checkpoints
import check_constructive_bottom_layers as cli
from peano_lab.kernel.proofs import EqRefl, Hyp
from peano_lab.kernel.terms import Zero
from peano_lab.library.theorems import TheoremSpec, _closed_formula


def test_exact_registered_inventory_and_unchanged_parent_boundary():
    assert [(item.slug, item.frontier_count) for item in checkpoints.CHECKPOINTS] == [
        ("euler-units", 32), ("prime-fields", 87), ("mobius-values", 21), ("signed-sums", 30),
    ]
    rows = tuple(row for checkpoint in checkpoints.CHECKPOINTS for row in checkpoints.load_rows(checkpoint))
    assert len(rows) == len({row.name for row in rows}) == 170
    assert checkpoints.closure.PARENT_COUNT == 3222
    assert checkpoints.closure.PARENT_CATALOG_BYTES == 66_503_303
    assert checkpoints.LEAN_BINARY_SHA256 == "22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033"
    assert checkpoints.LEAN_BINARY_BYTES == 106_787_344
    assert checkpoints.LEAN_TIMEOUT_SECONDS == 30


def _structural_fingerprint(root):
    """Iterative exact AST index; equality still confirms every possible hit."""
    digest = sha256()
    pending = [root]
    while pending:
        value = pending.pop()
        if is_dataclass(value):
            members = fields(value)
            digest.update((type(value).__name__ + "[" + str(len(members)) + "]").encode())
            pending.extend(getattr(value, member.name) for member in reversed(members))
        elif type(value) is int:
            digest.update(("int:" + str(value) + ";").encode())
        elif type(value) is str:
            digest.update(("str:" + str(len(value)) + ":" + value).encode())
        else:
            raise TypeError(type(value))
    return digest.digest()


def test_no_new_theorem_clones_any_parent_statement_or_another_new_row():
    # Check every parent, including long statements: source-length filtering
    # cannot establish AST distinctness because binder names have no meaning.
    rows = tuple(row for checkpoint in checkpoints.CHECKPOINTS for row in checkpoints.load_rows(checkpoint))
    index = {}
    duplicates = []
    for row in rows:
        formula = _closed_formula(row.statement)
        fingerprint = _structural_fingerprint(formula)
        duplicates.extend((row.name, name) for name, other in index.get(fingerprint, ()) if formula == other)
        index.setdefault(fingerprint, []).append((row.name, formula))
    for row in checkpoints.closure.parent_snapshot().specs:
        formula = _closed_formula(row.statement)
        duplicates.extend((name, row.name) for name, other in index.get(_structural_fingerprint(formula), ())
                          if formula == other)
    assert not duplicates


@pytest.fixture(scope="module", params=checkpoints.CHECKPOINTS, ids=lambda item: item.slug)
def actual_evidence(request):
    # Real complete HA and independent compiled Lean checks, not stored flags.
    return checkpoints.verify_checkpoint(request.param)


def test_real_artifacts_are_checked_with_every_actual_frontier_and_parent_body(actual_evidence):
    evidence = actual_evidence
    record = evidence.report
    assert record["frontier_count"] == len(evidence.frontier) == evidence.checkpoint.frontier_count
    assert record["bundle"]["original_ha_checked"] is True
    assert record["bundle"]["independent_lean_checked"] is True
    assert record["bundle"]["nodes_including_packaging_root"] == len(evidence.plan.rows) + 1
    assert record["bundle"]["inherited_theorems"] == len(evidence.plan.rows) - len(evidence.frontier)
    assert record["bundle"]["sha256"] == sha256((ROOT / evidence.checkpoint.artifact).read_bytes()).hexdigest()
    assert record["all_maximal_frontier_roots"] == list(evidence.plan.root_names)
    assert {row.name for row in evidence.frontier} <= {row.name for row in evidence.plan.rows}
    assert record["membership"] == "local_non_admitting_checkpoint"
    for key in ("admitted_to_alpha", "alpha_checked_use", "stable_member"):
        assert record[key] is False
    assert all(row["complete_ordinary_ha_checked"] is False for row in record["principal_roots"])
    assert all("ordinary_certificate_nodes" not in row for row in record["principal_roots"])


@pytest.mark.parametrize("value", [None, False, {}, "euler-units", replace(checkpoints.CHECKPOINTS[0], frontier_count=35),
                                  replace(checkpoints.CHECKPOINTS[0], artifact_sha256="0" * 64)])
def test_unregistered_or_altered_checkpoint_is_rejected_before_source_read(monkeypatch, value):
    monkeypatch.setattr(checkpoints, "_source_bytes", lambda _: pytest.fail("invalid config read a source"))
    with pytest.raises(checkpoints.CheckpointError, match="literal registered"):
        checkpoints.load_rows(value)


@pytest.mark.parametrize("value", [None, 0, 1, "yes", (), []])
def test_nonboolean_ordinary_replay_request_is_rejected_before_sources(monkeypatch, value):
    monkeypatch.setattr(checkpoints, "load_rows", lambda _: pytest.fail("invalid flag read sources"))
    with pytest.raises(checkpoints.CheckpointError, match="Boolean"):
        checkpoints.verify_checkpoint(checkpoints.CHECKPOINTS[0], ordinary_roots=value)


@pytest.mark.parametrize("mutation", ["missing", "empty", "changed", "oversized", "symlink"])
def test_bad_source_never_executes_a_factory(tmp_path, monkeypatch, mutation):
    pin = checkpoints.CHECKPOINTS[0].modules[0]
    path = tmp_path / pin.path
    path.parent.mkdir(parents=True)
    if mutation == "empty":
        path.write_bytes(b"")
    elif mutation == "changed":
        path.write_bytes(b"raise RuntimeError('must not execute')")
    elif mutation == "oversized":
        path.write_bytes(b"x" * (checkpoints.MAX_SOURCE_BYTES + 1))
    elif mutation == "symlink":
        path.symlink_to(ROOT / pin.path)
    monkeypatch.setattr(checkpoints, "ROOT", tmp_path)
    monkeypatch.setattr(checkpoints, "import_module", lambda _: pytest.fail("bad source was imported"))
    with pytest.raises(checkpoints.CheckpointError):
        checkpoints.load_rows(checkpoints.CHECKPOINTS[0])


@pytest.mark.parametrize("mutation", ["missing", "size", "digest", "symlink"])
def test_bad_lean_binary_is_never_executed(tmp_path, monkeypatch, mutation):
    path = tmp_path / "checker"
    if mutation == "size":
        path.write_bytes(b"wrong")
    elif mutation == "digest":
        path.write_bytes(b"fake")
        monkeypatch.setattr(checkpoints, "LEAN_BINARY_BYTES", 4)
    elif mutation == "symlink":
        path.symlink_to(checkpoints.LEAN_BINARY)
    monkeypatch.setattr(checkpoints, "LEAN_BINARY", path)
    monkeypatch.setattr(checkpoints.subprocess, "run", lambda *args, **kw: pytest.fail("unverified binary executed"))
    with pytest.raises(checkpoints.CheckpointError):
        checkpoints._lean_check(checkpoints.CHECKPOINTS[0], 211, 210,
                                (ROOT / checkpoints.CHECKPOINTS[0].artifact).read_bytes())


@pytest.mark.parametrize("mutation", ["returncode", "reject", "nodes", "root", "path", "extra", "stderr", "timeout", "oserror"])
def test_lean_failure_or_wrong_receipt_never_becomes_acceptance(monkeypatch, mutation):
    checkpoint = checkpoints.CHECKPOINTS[0]
    monkeypatch.setattr(checkpoints, "_check_lean_binary", lambda: None)

    def run(command, **kwargs):
        assert command[0] == str(checkpoints.LEAN_BINARY)
        artifact = Path(command[1])
        assert artifact != ROOT / checkpoint.artifact
        assert artifact.read_bytes() == (ROOT / checkpoint.artifact).read_bytes()
        expected = f"ACCEPT\t{artifact}\tnodes=211\troot=210\n"
        assert kwargs["timeout"] == 30 and kwargs["capture_output"] and kwargs["text"]
        if mutation == "timeout":
            raise subprocess.TimeoutExpired(command, 30)
        if mutation == "oserror":
            raise OSError("test failure")
        output = {"reject": "REJECT\n", "nodes": expected.replace("nodes=211", "nodes=1"),
                  "root": expected.replace("root=210", "root=0"), "path": expected.replace(str(artifact), "other.json"),
                  "extra": expected + "another receipt\n"}.get(mutation, expected)
        return SimpleNamespace(returncode=1 if mutation == "returncode" else 0, stdout=output,
                               stderr="unexpected warning" if mutation == "stderr" else "")

    monkeypatch.setattr(checkpoints.subprocess, "run", run)
    with pytest.raises(checkpoints.CheckpointError):
        checkpoints._lean_check(checkpoint, 211, 210, (ROOT / checkpoint.artifact).read_bytes())


@pytest.mark.parametrize("payload", [b"", b"{}", "not bytes", None])
def test_lean_input_must_be_the_exact_authenticated_ha_bytes(monkeypatch, payload):
    monkeypatch.setattr(checkpoints, "_check_lean_binary", lambda: pytest.fail("invalid payload reached the checker"))
    with pytest.raises(checkpoints.CheckpointError, match="authenticated HA payload"):
        checkpoints._lean_check(checkpoints.CHECKPOINTS[0], 211, 210, payload)


def test_lean_checks_private_verified_snapshot_not_a_replaced_original_path(tmp_path, monkeypatch):
    checkpoint = checkpoints.CHECKPOINTS[0]
    payload = (ROOT / checkpoint.artifact).read_bytes()
    original = tmp_path / checkpoint.artifact
    original.parent.mkdir(parents=True)
    original.write_bytes(b"concurrently replaced original data")
    monkeypatch.setattr(checkpoints, "ROOT", tmp_path)
    monkeypatch.setattr(checkpoints, "_check_lean_binary", lambda: None)
    snapshots = []

    def run(command, **kwargs):
        snapshot = Path(command[1])
        snapshots.append(snapshot)
        assert snapshot != original and snapshot.read_bytes() == payload
        assert original.read_bytes() != payload
        assert snapshot.parent.stat().st_mode & 0o777 == 0o700
        return SimpleNamespace(returncode=0, stdout=f"ACCEPT\t{snapshot}\tnodes=211\troot=210\n", stderr="")

    monkeypatch.setattr(checkpoints.subprocess, "run", run)
    checkpoints._lean_check(checkpoint, 211, 210, payload)
    assert len(snapshots) == 1 and not snapshots[0].exists()


@pytest.mark.parametrize("mutation", ["open_hypothesis", "other_true_formula", "other_spec"])
def test_ordinary_root_wrapper_rejects_valid_but_unrelated_certificates(monkeypatch, mutation):
    checkpoint = checkpoints.CHECKPOINTS[0]
    exact_spec = next(row for row in checkpoints.load_rows(checkpoint) if row.name == checkpoint.principal_roots[0])
    exact = _closed_formula(exact_spec.statement)
    replacement = SimpleNamespace(spec=exact_spec, formula=exact, certificate=Hyp(0), proof_nodes=1)
    if mutation == "other_true_formula":
        replacement.formula = _closed_formula("0=0")
        replacement.certificate = EqRefl(Zero())
    elif mutation == "other_spec":
        replacement.spec = TheoremSpec("counterfeit_root", "0=0", (), ("refl",), "Not the requested result")
    monkeypatch.setattr(checkpoints.closure, "replay_bottom_layer_theorem", lambda *args: replacement)
    with pytest.raises(checkpoints.CheckpointError, match="empty-context certificate"):
        checkpoints.verify_checkpoint(checkpoint, ordinary_roots=True)


def test_report_canonicalization_does_not_accept_non_json_numbers():
    assert cli.canonical_report({"z": 2, "a": "α"}) == '{\n  "a": "α",\n  "z": 2\n}\n'
    with pytest.raises(ValueError):
        cli.canonical_report({"number": float("nan")})


@pytest.mark.parametrize("field,value", [
    ("name", "counterfeit_cached_name"), ("statement", "0=0"),
    ("dependencies", ()), ("script", ("refl",)), ("summary", "counterfeit cached prose"),
])
def test_literal_specs_pin_rejects_changed_cached_factory_output(monkeypatch, field, value):
    checkpoint = checkpoints.CHECKPOINTS[0]
    pin = checkpoint.modules[0]
    module = import_module("peano_lab.library." + pin.module)
    original = getattr(module, pin.factory)(TheoremSpec)
    assert getattr(original[0], field) != value
    altered = (replace(original[0], **{field: value}), *original[1:])
    monkeypatch.setattr(module, pin.factory, lambda _: altered)
    with pytest.raises(checkpoints.CheckpointError, match="literal ordered theorem"):
        checkpoints.load_rows(checkpoint)


def test_audit_receipt_is_compared_as_exact_utf8_bytes(tmp_path):
    path = tmp_path / "receipt.json"
    expected = cli.canonical_report({"label": "α", "checked": True})
    path.write_bytes(expected.encode())
    cli.check_receipt_bytes(path, expected)


@pytest.mark.parametrize("mutation", ["missing", "symlink", "changed", "truncated", "oversized", "crlf"])
def test_untrusted_audit_sidecars_are_bounded_and_not_newline_normalized(tmp_path, mutation):
    path = tmp_path / "receipt.json"
    expected = cli.canonical_report({"label": "α", "checked": True})
    if mutation == "symlink":
        target = tmp_path / "real.json"
        target.write_bytes(expected.encode())
        path.symlink_to(target)
    elif mutation == "changed":
        path.write_bytes(expected.replace("true", "null").encode())
    elif mutation == "truncated":
        path.write_bytes(expected.encode()[:-1])
    elif mutation == "oversized":
        path.write_bytes(expected.encode() + b"x" * 100_000)
    elif mutation == "crlf":
        path.write_bytes(expected.replace("\n", "\r\n").encode())
    with pytest.raises(RuntimeError, match="missing or stale"):
        cli.check_receipt_bytes(path, expected)


def test_over_budget_verification_does_not_write_an_audit_receipt(tmp_path, monkeypatch):
    destination = tmp_path / "no-success.json"
    monkeypatch.setattr(cli, "RECEIPT", destination)
    monkeypatch.setattr(cli, "verify_all", lambda **kwargs: {"checkpoints": [], "new_theorems": 0})
    monkeypatch.setattr(cli.resource, "setrlimit", lambda *args: None)
    monkeypatch.setattr(cli.signal, "alarm", lambda *args: None)
    over_limit = 1536 * 1024 * 1024 + 1024
    raw = over_limit if sys.platform == "darwin" else over_limit // 1024
    monkeypatch.setattr(cli.resource, "getrusage", lambda _: SimpleNamespace(ru_maxrss=raw))
    with pytest.raises(RuntimeError, match="1536 MiB"):
        cli.main(["--write"])
    assert not destination.exists()


def test_default_cli_verifies_real_ordinary_roots_without_publication():
    result = subprocess.run([sys.executable, str(ROOT / "scripts/check_constructive_bottom_layers.py")],
                            cwd=ROOT, text=True, capture_output=True, timeout=60, check=True)
    assert "170 local theorems; Alpha remains 3222, Stable 432; no admission or deployment" in result.stdout
    assert result.stdout.count("complete HA + independent Lean + ordinary roots PASS") == 4
    assert "Authoring RSS ceiling PASS:" in result.stdout
