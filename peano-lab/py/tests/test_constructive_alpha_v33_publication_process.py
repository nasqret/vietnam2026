"""V33 transport and exact-test accounting; no synthetic proof authority."""

from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
import constructive_alpha_v33_publication_process as process


def _context():
    return SimpleNamespace(catalog_sha256="a" * 64, source_binding_sha256="b" * 64,
                           render_source_binding_sha256="c" * 64, proofs_verified=False)


def _message(phase="research"):
    context = _context()
    return {"schema": process.SCHEMA, "nonce": "d" * 64, "phase": phase,
        "catalog_sha256": context.catalog_sha256, "source_binding_sha256": context.source_binding_sha256,
        "render_source_binding_sha256": context.render_source_binding_sha256,
        "check": False, "limits": {"cpu": [170, 175], "wall_seconds": 180, "max_rss_bytes": 1536 * 1024 * 1024},
        "peak_rss_bytes": 100, "inventory": {"bytes": 1, "sha256": "e" * 64}, "pytest_status": 0}


def _validate(message, phase="research"):
    return process._validate_message(process._canonical(message), nonce="d" * 64, phase=phase, context=_context(), check=False)


@pytest.mark.parametrize("phase", process.PHASES)
def test_exact_non_authorizing_transport_shape(phase):
    value = _message(phase)
    assert _validate(value, phase) == value
    with pytest.raises(process.publication.PublicationError):
        process.publication.require_live(_context())


@pytest.mark.parametrize("field", tuple(_message()))
def test_missing_required_transport_field_is_rejected(field):
    value = _message()
    value.pop(field)
    with pytest.raises(ValueError):
        _validate(value)


@pytest.mark.parametrize("field", ("catalog_sha256", "source_binding_sha256", "render_source_binding_sha256", "nonce", "schema", "phase"))
def test_wrong_live_binding_or_generation_is_rejected(field):
    value = _message()
    value[field] = "f" * 64
    with pytest.raises(ValueError):
        _validate(value)


@pytest.mark.parametrize("field,value", (("pytest_status", True), ("pytest_status", 1), ("pytest_status", 0.0),
    ("peak_rss_bytes", 0), ("peak_rss_bytes", True), ("peak_rss_bytes", 1610612737), ("check", 0)))
def test_transport_types_and_original_resource_ceiling(field, value):
    message = _message()
    message[field] = value
    with pytest.raises(ValueError):
        _validate(message)


@pytest.mark.parametrize("phase,count", (("polynomial", 5), ("research", 8), ("completed", 59), ("historical", 90), ("atlas", 1)))
def test_mandatory_test_identity_counts_are_exact(phase, count):
    cases = process.expected_test_ids(phase)
    assert len(cases) == len(set(cases)) == count
    assert all(phase + "_phase" in case for case in cases)


@pytest.mark.parametrize("phase", process.PHASES)
def test_presentation_test_accounting_only_accepts_exact_full_pass(phase):
    ledger = process.TestAccounting(phase)
    ledger.pytest_collection_finish(SimpleNamespace(items=[SimpleNamespace(nodeid=case) for case in ledger.expected]))
    for case in ledger.expected:
        for when in ("setup", "call", "teardown"):
            ledger.pytest_runtest_logreport(SimpleNamespace(nodeid=case, when=when, passed=True, failed=False, skipped=False))
    ledger.require_complete(0)


@pytest.mark.parametrize("fault", ("empty", "missing", "duplicate", "reordered", "unpassed", "skip", "xfail", "setup_failed", "collection_failed", "status_bool", "status_fail"))
def test_missing_or_nonpassing_ui_tests_never_authorize_success(fault):
    ledger = process.TestAccounting("research")
    ledger.collected = ledger.expected
    ledger.passed = list(ledger.expected)
    status = 0
    if fault == "empty": ledger.collected, ledger.passed = (), []
    elif fault == "missing": ledger.collected = ledger.expected[:-1]
    elif fault == "duplicate": ledger.collected = ledger.expected + ledger.expected[:1]
    elif fault == "reordered": ledger.collected = tuple(reversed(ledger.expected))
    elif fault == "unpassed": ledger.passed.pop()
    elif fault in {"skip", "xfail", "setup_failed"}:
        report = SimpleNamespace(nodeid=ledger.expected[0], when="setup", passed=False,
            failed=fault == "setup_failed", skipped=fault == "skip")
        if fault == "xfail": report.wasxfail = "not a complete run"
        ledger.pytest_runtest_logreport(report)
    elif fault == "collection_failed": ledger.pytest_collectreport(SimpleNamespace(failed=True, skipped=False))
    elif fault == "status_bool": status = False
    else: status = 1
    with pytest.raises(process.PublicationProcessError):
        ledger.require_complete(status)


def test_test_inventory_mutation_is_checked_before_publication_message():
    import inspect
    source = inspect.getsource(process._render_child)
    assert source.index("initial_inventory = _canonical(inventory)") < source.index("status = _run_phase_tests")
    assert source.index("initial_inventory != _canonical(inventory)") < source.index('message = {')
    assert source.index("context.require_unchanged()") < source.index('message = {')


def test_public_entry_has_no_saved_receipt_or_test_only_acceptance_path():
    import inspect
    source = inspect.getsource(process.publish_from_live_context)
    assert source.index("publication.bind_live_context(context)") < source.index("_fork_phase(")
    with pytest.raises(process.publication.PublicationError):
        process.publish_from_live_context(_context(), check=False)
