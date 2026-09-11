"""Reject fabricated release authority without importing the Alpha inventory."""
import ast
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import pytest

import build_peano_library_channels_v35 as builder
import verify_peano_library_channels_v35 as verifier
import constructive_jordan_publication_v35 as publication


@pytest.mark.parametrize("value", [{}, {"families": []}, SimpleNamespace(require_unchanged=lambda: None), "receipt.json"])
def test_saved_observations_cannot_authorize_release_or_publication(value, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("unauthorized input reached proof work or output generation")
    monkeypatch.setattr(builder, "require_scope", lambda: None)
    monkeypatch.setattr(builder, "_project_payloads", forbidden)
    monkeypatch.setattr(builder, "preflight_inputs", forbidden)
    with pytest.raises(ValueError): builder.build_payloads(value)
    with pytest.raises(ValueError): verifier.verify_candidate_payloads({}, value)
    with pytest.raises(ValueError): verifier.context_from_live_audit(value)
    with pytest.raises(ValueError): publication.require_live(value)
    with pytest.raises(ValueError): publication.bind_live_context(value)


def test_unissued_class_instances_cannot_mint_live_authority():
    with pytest.raises(ValueError):
        publication.BoundPresentation(object(), object(), "a" * 64)
    with pytest.raises(ValueError):
        verifier.LiveReleaseContext(object(), {}, {}, {}, {}, ())


@pytest.mark.parametrize("field,bad", [("schema", "v35"), ("max_rows", 8192.0),
    ("max_rows", 8193), ("previous_max_rows", True), ("proof_limits_changed", 0),
    ("proof_limits_changed", True)])
def test_inherited_capacity_policy_is_exact_not_a_kernel_upgrade(field, bad):
    original = dict(builder.codec.CAPACITY_METADATA)
    verifier._verify_capacity(original)
    original[field] = bad
    with pytest.raises(ValueError): verifier._verify_capacity(original)


@pytest.mark.parametrize("field", ["catalog_sha256", "source_binding_sha256", "revision", "promoted_names"])
def test_public_identity_cannot_be_retargeted(field):
    kwargs = dict(source_binding_sha256="a" * 64, catalog_sha256="b" * 64, promoted_names=("actual",))
    original = dict(kwargs, revision="b" * 12)
    verifier._verify_public_identity_fields(original, **kwargs)
    changed = deepcopy(original)
    changed[field] = ("other",) if field == "promoted_names" else "c" * len(changed[field])
    with pytest.raises(ValueError): verifier._verify_public_identity_fields(changed, **kwargs)


def test_exact_two_phase_targets_preserve_legacy_readers():
    assert publication.OUTPUT_NAMES == {"jordan": "constructive-jordan-explorer-v35", "atlas": "constructive-jordan-campaign-v35"}
    import constructive_alpha_v35_publication_process as process
    assert process.PHASES == ("jordan", "atlas")
    assert process.CPU_LIMITS == (170, 175) and process.WALL_SECONDS == 180
    assert process.MAX_RSS_BYTES == 1536 * 1024 * 1024


def test_builder_and_independent_verifier_both_require_live_audit():
    for module, name in ((builder, "build_payloads"), (verifier, "verify_candidate_payloads")):
        tree = ast.parse(Path(module.__file__).read_text())
        function = next(row for row in tree.body if isinstance(row, ast.FunctionDef) and row.name == name)
        source = ast.unparse(function)
        assert "type(audit) is not proof_audit.FreshProofAudit" in source or "type(audit) is proof_audit.FreshProofAudit" in source
        assert source.count("audit.require_unchanged()") == 2


@pytest.mark.parametrize("phase", ["jordan", "atlas"])
@pytest.mark.parametrize("attack", ["empty", "missing", "reordered", "skipped", "failure"])
def test_publication_needs_every_exact_mandatory_case(phase, attack):
    import constructive_alpha_v35_publication_process as process
    ledger = process.TestAccounting(phase)
    expected = process.expected_test_ids(phase)
    assert len(expected) == (3 if phase == "jordan" else 2)
    ledger.collected = expected
    ledger.passed = list(expected)
    status = 0
    if attack == "empty": ledger.collected = (); ledger.passed = []
    elif attack == "missing": ledger.passed.pop()
    elif attack == "reordered": ledger.passed.reverse()
    elif attack == "skipped": ledger.bad = True
    else: status = 1
    with pytest.raises(ValueError): ledger.require_complete(status)
