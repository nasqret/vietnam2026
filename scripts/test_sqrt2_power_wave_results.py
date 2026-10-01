"""Historical byte-reader tests; never run a kernel, solver, or Lean process.

Adversarial receipts are synthesized in memory. Existing observation files are
read-only and their contents are never rewritten, copied, or promoted.
"""
from copy import deepcopy
from hashlib import sha256
import ast
import gzip
import json
from pathlib import Path

import pytest

import sqrt2_power_wave_results as reader


OBS = "research/arithmetic-library/sqrt2-power/observations/"


def _entry(folder, case=None, target=None):
    relative = OBS + folder + "/report.json"
    raw = (reader.ROOT / relative).read_bytes()
    result = dict(path=relative, bytes=len(raw), sha256=sha256(raw).hexdigest())
    if case is not None:
        report = json.loads(raw)
        result.update(case=case, target_ast_sha256=target or report["results"]["fresh_replay"]["target_ast_sha256"])
    return result


def _index(*entries, lean=()):
    return dict(schema=reader.INDEX_SCHEMA, reports=list(entries), lean_reports=list(lean))


@pytest.fixture
def p08():
    return _entry("shared-wave-p08-e-v1", "P08-eprover")


@pytest.fixture
def failed_p04():
    return _entry("shared-wave-p04-ground-v1", "P04-ground",
                  "67e5493f462533be7b0278c71e26557a606ae3499d32b3fee2ea51e7b4b1ec83")


@pytest.fixture
def lean_index():
    entries = (
        _entry("shared-wave-p10-v1", "P10"),
        _entry("shared-wave-p08-e-v1", "P08-eprover"),
        _entry("shared-wave-p08-v-v1", "P08-vampire"),
        _entry("shared-wave-p04-soundness-v1", "P04-soundness"),
    )
    return _index(*entries, lean=(_entry("fresh-lean-wave-v1"),))


def _overlay(monkeypatch, entry, mutate_report, process_mutation=None):
    """Reseal attacker-controlled report hashes to test inner binding gates."""
    original = reader._read_file
    report_path = reader.ROOT / entry["path"]
    report = json.loads(report_path.read_bytes())
    overrides = {}
    if process_mutation is not None:
        phase, change = process_mutation
        summary = report["process_records"][phase]
        path = report_path.parent / summary["path"]
        process = json.loads(gzip.decompress(path.read_bytes()))
        change(process, report)
        raw = reader._canonical(process)
        overrides[str(path)] = gzip.compress(raw, mtime=0)
        summary["raw_sha256"] = sha256(raw).hexdigest()
    mutate_report(report)
    raw = reader._canonical(report) + b"\n"
    overrides[str(report_path)] = raw
    changed = dict(entry, bytes=len(raw), sha256=sha256(raw).hexdigest())
    def supplied(base, relative, maximum=reader.MAX_RAW):
        path = str(Path(base) / relative)
        value = overrides.get(path)
        if value is not None:
            if len(value) > maximum:
                raise reader.EvidenceError("fixture exceeds requested bound")
            return value
        return original(base, relative, maximum)
    monkeypatch.setattr(reader, "_read_file", supplied)
    return changed


def _set_stdout(process, value):
    raw = reader._canonical(value) + b"\n"
    process.update(stdout=raw.decode(), stdout_bytes=len(raw), stdout_sha256=sha256(raw).hexdigest())


def test_p08_demonstrations_are_one_statement_and_one_canonical_download(p08):
    other = _entry("shared-wave-p08-v-v1", "P08-vampire")
    view, downloads = reader.wave_results(_index(p08, other))
    assert view["counts"]["fresh_HA_attempts"] == 2
    assert view["counts"]["unique_HA_statements"] == 1
    assert view["counts"]["unique_supporting_statements"] == 1
    assert view["counts"]["unique_full_fixed_statements"] == 0
    assert view["rows"][0]["proof_download"] == view["rows"][1]["proof_download"]
    row = view["rows"][0]
    payload = gzip.decompress(downloads[row["proof_download"]])
    assert len(payload) == row["bundle_bytes"]
    assert sha256(payload).hexdigest() == row["bundle_sha256"]
    assert view["kernel_checks_performed_by_reader"] == view["Lean_processes_started_by_reader"] == 0
    assert view["IR_parents_closed"] == view["library_admissions"] == 0


def test_failed_p04_is_retained_without_a_proof_artifact(failed_p04):
    view, downloads = reader.wave_results(_index(failed_p04))
    assert view["rows"][0]["status"] == "not_checked"
    assert view["rows"][0]["generation_returncode"] == 1
    assert "proof_download" not in view["rows"][0]
    assert view["counts"]["failed_or_unchecked_attempts"] == 1
    assert view["counts"]["unique_HA_statements"] == 0
    assert list(downloads) == [view["rows"][0]["report_download"]]


def test_failed_rf003_is_retained_without_inheriting_a_retry_success():
    # The caller's expected target pin is not a proof for a failed attempt.
    target = _entry("shared-wave-rf003-typed-v2", "RF003")["target_ast_sha256"]
    entry = _entry("shared-wave-rf003-v1", "RF003", target)
    view, _ = reader.wave_results(_index(entry))
    assert view["rows"][0]["status"] == "not_checked"
    assert "bundle_sha256" not in view["rows"][0]
    assert view["counts"]["unique_named_foundations"] == 0


def test_only_explicitly_listed_records_are_read():
    view, downloads = reader.wave_results(_index())
    assert view["rows"] == [] and downloads == {}
    assert all(value == 0 for value in view["counts"].values())


@pytest.mark.parametrize("path", ("../report.json", "/tmp/report.json", "a/../report.json", "a//report.json", "a\\report.json"))
def test_unsafe_index_paths_are_rejected(p08, path):
    with pytest.raises(reader.EvidenceError, match="path"):
        reader.wave_results(_index(dict(p08, path=path)))


def test_duplicate_or_unknown_index_fields_fail_closed(p08):
    with pytest.raises(reader.EvidenceError, match="duplicate"):
        reader.wave_results(_index(p08, p08))
    with pytest.raises(reader.EvidenceError, match="fields"):
        reader.wave_results(dict(_index(p08), counts={"proved": 1000}))
    with pytest.raises(reader.EvidenceError, match="fields"):
        reader.wave_results(_index(dict(p08, status="proved")))


@pytest.mark.parametrize("field,value", (("sha256", "0" * 64), ("bytes", True), ("bytes", 1)))
def test_pinned_report_hash_and_exact_byte_count_are_required(p08, field, value):
    with pytest.raises(reader.EvidenceError):
        reader.wave_results(_index(dict(p08, **{field: value})))


def test_changed_indexed_target_is_rejected(p08):
    with pytest.raises(reader.EvidenceError, match="target"):
        reader.wave_results(_index(dict(p08, target_ast_sha256="0" * 64)))


def test_failed_attempt_cannot_be_promoted_by_a_status_string(failed_p04, monkeypatch):
    changed = _overlay(monkeypatch, failed_p04, lambda report: report.update(status="fresh_ordinary_HA_checked"))
    with pytest.raises(reader.EvidenceError, match="status"):
        reader.wave_results(_index(changed))


def test_archived_source_hashes_are_checked_not_current_source_files(p08, monkeypatch):
    def change(report):
        first = next(iter(report["source_pins"]))
        report["source_pins"][first]["sha256"] = "0" * 64
    changed = _overlay(monkeypatch, p08, change)
    with pytest.raises(reader.EvidenceError, match="bytes/hash"):
        reader.wave_results(_index(changed))


def test_unknown_report_counts_and_parent_claims_are_rejected(p08, monkeypatch):
    changed = _overlay(monkeypatch, p08, lambda report: report.update(counts={"proved": 99}))
    with pytest.raises(reader.EvidenceError, match="fields"):
        reader.wave_results(_index(changed))


def test_resealed_false_proof_counts_fail_inert_structural_comparison(p08, monkeypatch):
    def change(process, report):
        replay = json.loads(process["stdout"])
        replay["proof_nodes"] += 1
        report["results"]["fresh_replay"] = replay
        _set_stdout(process, replay)
    changed = _overlay(monkeypatch, p08, lambda report: None, ("fresh_replay", change))
    with pytest.raises(reader.EvidenceError, match="proof counts"):
        reader.wave_results(_index(changed))


def test_missing_negative_test_is_not_a_fresh_ha_observation(p08, monkeypatch):
    def change(process, report):
        replay = json.loads(process["stdout"])
        replay["false_target_rejected"] = False
        report["results"]["fresh_replay"] = replay
        _set_stdout(process, replay)
    changed = _overlay(monkeypatch, p08, lambda report: None, ("fresh_replay", change))
    with pytest.raises(reader.EvidenceError, match="rejection/check"):
        reader.wave_results(_index(changed))


def test_resealed_process_with_changed_stdout_hash_is_rejected(p08, monkeypatch):
    changed = _overlay(monkeypatch, p08, lambda report: None,
        ("generation", lambda process, report: process.update(stdout_sha256="0" * 64)))
    with pytest.raises(reader.EvidenceError, match="process receipt"):
        reader.wave_results(_index(changed))


def test_fresh_lean_attaches_by_identical_bundle_and_deduplicates_statements(lean_index):
    view, _ = reader.wave_results(lean_index)
    assert all(row["independent_lean_checked"] for row in view["rows"])
    assert view["counts"]["fresh_HA_attempts"] == 4
    assert view["counts"]["unique_HA_statements"] == 3
    assert view["counts"]["unique_Lean_checked_statements"] == 3
    assert view["lean_reports"][0]["original_checks"] == 4


def test_lean_cannot_match_only_on_case_name(lean_index, monkeypatch):
    def change(report):
        report["checks"][0]["bundle_sha256"] = "0" * 64
    lean_index = deepcopy(lean_index)
    lean_index["lean_reports"][0] = _overlay(monkeypatch, lean_index["lean_reports"][0], change)
    with pytest.raises(reader.EvidenceError, match="bundle/target identity"):
        reader.wave_results(lean_index)


def test_lean_accept_marker_must_match_exact_root(lean_index, monkeypatch):
    def change(report):
        process = report["checks"][0]["process"]
        process["stdout"] = process["stdout"].replace("\troot=1485", "\troot=0")
        raw = process["stdout"].encode()
        process.update(stdout_bytes=len(raw), stdout_sha256=sha256(raw).hexdigest())
    lean_index = deepcopy(lean_index)
    lean_index["lean_reports"][0] = _overlay(monkeypatch, lean_index["lean_reports"][0], change)
    with pytest.raises(reader.EvidenceError, match="Lean status"):
        reader.wave_results(lean_index)


def test_no_unlisted_wave_is_loaded_via_a_lean_report(lean_index):
    lean_index["reports"] = lean_index["reports"][1:]
    with pytest.raises(reader.EvidenceError, match="unlisted"):
        reader.wave_results(lean_index)


@pytest.fixture
def negative_lean_index():
    return _index(_entry("shared-wave-p10-v1", "P10"),
        _entry("shared-wave-rf003-typed-v2", "RF003"),
        lean=(_entry("fresh-lean-negative-controls-v2"),))


def test_new_lean_shape_validates_root_and_two_negative_controls(negative_lean_index):
    view, _ = reader.wave_results(negative_lean_index)
    summary = view["lean_reports"][0]
    assert summary["negative_controls_checked"] is True
    assert [row["kind"] for row in summary["negative_controls"]] == ["false-caller-target", "forged-root-body"]
    assert all(row["rejected"] for row in summary["negative_controls"])
    assert view["counts"]["unique_Lean_checked_statements"] == 2


def test_negative_mutation_hash_is_recomputed_from_original_bytes(negative_lean_index, monkeypatch):
    def change(report):
        report["negative_controls"][0]["mutated_bundle_sha256"] = "0" * 64
    negative_lean_index["lean_reports"][0] = _overlay(monkeypatch, negative_lean_index["lean_reports"][0], change)
    with pytest.raises(reader.EvidenceError, match="mutation hash"):
        reader.wave_results(negative_lean_index)


def test_negative_rejection_cannot_be_a_claim_without_matching_exit(negative_lean_index, monkeypatch):
    def change(report):
        report["negative_controls"][0]["rejected"] = False
    negative_lean_index["lean_reports"][0] = _overlay(monkeypatch, negative_lean_index["lean_reports"][0], change)
    with pytest.raises(reader.EvidenceError, match="rejection status"):
        reader.wave_results(negative_lean_index)


def test_known_composition_chunks_are_supporting_not_full_ground_closure():
    assert len(reader.CHUNK_PINS) == 16
    for case in reader.CHUNK_PINS:
        assert reader._COVERAGE[case] == ("complete_exact_subconjunction_child", "supporting_leaf")


def test_reader_does_not_import_kernel_or_producer_modules():
    tree = ast.parse(Path(reader.__file__).read_text())
    forbidden = ("peano_lab", "run_sqrt2_power_wave", "check_sqrt2_power_fresh_lean",
                 "sqrt2_power_rational_foundations", "sqrt2_power_binary_dag")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert not any((node.module or "").startswith(name) for name in forbidden)
        elif isinstance(node, ast.Import):
            assert not any(alias.name.startswith(forbidden) for alias in node.names)
