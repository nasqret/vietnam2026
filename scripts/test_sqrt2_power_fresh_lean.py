"""Fresh-checker intake regression tests; no Lean processes are launched."""
from hashlib import sha256
import gzip
import json
from pathlib import Path

import pytest
import check_sqrt2_power_fresh_lean as fresh

FOLDER = fresh.ROOT / "research/arithmetic-library/sqrt2-power/observations/shared-wave-p04-c00-v1"


def test_same_bytes_rebind_to_the_frozen_target():
    payload, info = fresh.exact_bundle(FOLDER)
    assert sha256(payload).hexdigest() == info["bundle_sha256"]
    assert info["case"] == "P04-C00"


@pytest.mark.parametrize("change", ("case", "schema", "source_pins"))
def test_resealed_report_cannot_relabel_a_proof(monkeypatch, change):
    path = FOLDER / "report.json"
    report = json.loads(path.read_bytes())
    if change == "case":
        report["case"] = "P04-C13"
    elif change == "schema":
        report["schema"] = "untrusted_claim"
    else:
        report["source_pins"] = {}
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: json.dumps(report).encode() if p == path else original(p))
    with pytest.raises(ValueError):
        fresh.exact_bundle(FOLDER)


def test_archived_source_bytes_are_checked(monkeypatch):
    report = json.loads((FOLDER / "report.json").read_bytes())
    path = FOLDER / next(iter(report["source_snapshots"].values()))
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: gzip.compress(b"changed source") if p == path else original(p))
    with pytest.raises(ValueError, match="archived source bytes"):
        fresh.exact_bundle(FOLDER)


def test_empty_axiom_audit_is_rejected_before_any_execution(monkeypatch, tmp_path):
    path = fresh.ROOT / "scripts/assets/Sqrt2PowerLeanAudit.lean"
    original = Path.read_bytes
    monkeypatch.setattr(Path, "read_bytes", lambda p: b"" if p == path else original(p))
    def forbidden(*_args, **_kwargs):
        raise AssertionError("invalid audit reached Lean execution")
    monkeypatch.setattr(fresh, "runtime", forbidden)
    with pytest.raises(ValueError, match="audit source changed"):
        fresh.execute(tmp_path / "never_created", [FOLDER])
