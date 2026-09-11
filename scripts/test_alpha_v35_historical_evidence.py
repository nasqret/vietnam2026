"""The v35 archive recovers exact old bytes without weakening any old checks."""
from hashlib import sha256
from pathlib import Path
from copy import deepcopy

import pytest
import alpha_v31_historical_evidence as old
import alpha_v35_historical_evidence as new

ROOT = Path(__file__).resolve().parents[1]


def original_record():
    return dict(path='scripts/build_constructive_second_wave_explorer.py', bytes=42839,
        sha256='3fd4a7a53939590a163d6a0f229503bd368e5e8da4994b7d4115a64a40509a77',
        role='Exact QR-template second-wave proof explorer publication.')


def test_archived_source_is_exact_and_current_source_remains_distinct():
    record = original_record()
    path = new.verify_inherited_document(record)
    raw = path.read_bytes()
    assert path == ROOT / new.ARCHIVES[0]['archive_path']
    assert len(raw) == record['bytes'] and sha256(raw).hexdigest() == record['sha256']
    assert (ROOT / record['path']).read_bytes() != raw
    with pytest.raises(old.HistoricalEvidenceError):
        old.verify_inherited_document(record)


def test_all_five_existing_archive_dispositions_remain_unchanged():
    assert new.archive_paths()[:5] == old.archive_paths()
    assert new.archive_bindings()[:5] == old.archive_bindings()
    assert new.archive_evidence_documents()[:5] == old.archive_evidence_documents()
    for item in old.ARCHIVES:
        row = dict(path=item['original_path'], bytes=item['bytes'], sha256=item['sha256'], role='historical')
        assert new.verify_inherited_document(row) == old.verify_inherited_document(row)


@pytest.mark.parametrize('field,value', (
    ('bytes', True), ('bytes', 42838), ('sha256', '0' * 64),
    ('path', '../scripts/build_constructive_second_wave_explorer.py'),
    ('role', ''),
))
def test_altered_record_cannot_fall_back_to_current_file(field, value):
    row = original_record()
    row[field] = value
    with pytest.raises(new.HistoricalEvidenceError):
        new.verify_inherited_document(row)


def test_copies_of_bindings_cannot_modify_registered_evidence():
    records = new.archive_bindings()
    records[-1]['sha256'] = '0' * 64
    assert new.archive_bindings()[-1]['sha256'] == original_record()['sha256']


def test_unknown_path_retains_original_no_fallback_validator(tmp_path):
    row = original_record()
    row['path'] = 'missing-current-file.py'
    with pytest.raises(new.HistoricalEvidenceError):
        new.verify_inherited_document(row, root=tmp_path)


def test_missing_registered_archive_is_not_hidden_by_metadata(tmp_path):
    with pytest.raises(new.HistoricalEvidenceError):
        new.verify_inherited_document(original_record(), root=tmp_path)


def test_mutated_alias_registration_fails_closed(monkeypatch):
    changed = deepcopy(new.ARCHIVES)
    changed[0]['archive_path'] = 'scripts/build_constructive_second_wave_explorer.py'
    monkeypatch.setattr(new, 'ARCHIVES', changed)
    with pytest.raises(new.HistoricalEvidenceError):
        new.archive_bindings()
