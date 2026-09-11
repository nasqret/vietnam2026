"""One additive exact historical source snapshot; never a fallback resolver.

The v34 catalogue retains its original 1119 documentary records. September's
proof-reader changes legitimately updated one source listed there. This adapter
resolves only that exact old path/size/SHA to its byte-identical Git snapshot.
The five v31 archive dispositions and every other source retain their original
validator. Current explorer sources, old catalogues and v31 code are unchanged.
Documentary authentication is not kernel, Lean or admission authority.
"""
from copy import deepcopy
from pathlib import Path

import alpha_v31_historical_evidence as previous

ROOT = Path(__file__).resolve().parents[1]
MAX_DOCUMENT_BYTES = previous.MAX_DOCUMENT_BYTES
HistoricalEvidenceError = previous.HistoricalEvidenceError
ARCHIVE_DIRECTORY = 'research/arithmetic-library/artifacts/alpha-v35-historical-evidence'
ARCHIVE_ROLE = 'alpha_v35_historical_evidence_archive'
ARCHIVES = ({
    'original_path': 'scripts/build_constructive_second_wave_explorer.py',
    'archive_path': ARCHIVE_DIRECTORY + '/build_constructive_second_wave_explorer.py.snapshot',
    'bytes': 42839,
    'sha256': '3fd4a7a53939590a163d6a0f229503bd368e5e8da4994b7d4115a64a40509a77',
    'recovery': {
        'kind': 'exact_git_commit_blob',
        'git_commit': 'ea90d1080a4ef59c4bd399c21097e9643aa786df',
        'git_blob': '7e3b02c26d953cc08490a23511dd44e4f814b8e7',
        'note': 'Exact original path in this reachable commit; the later current proof-reader source remains untouched.',
    },
},)


def _validate_registration():
    if (type(ARCHIVES) is not tuple or len(ARCHIVES) != 1
            or type(ARCHIVES[0]) is not dict
            or set(ARCHIVES[0]) != {'original_path', 'archive_path', 'bytes', 'sha256', 'recovery'}
            or ARCHIVES[0]['original_path'] != 'scripts/build_constructive_second_wave_explorer.py'
            or ARCHIVES[0]['archive_path'] != 'research/arithmetic-library/artifacts/alpha-v35-historical-evidence/build_constructive_second_wave_explorer.py.snapshot'
            or type(ARCHIVES[0]['bytes']) is not int or ARCHIVES[0]['bytes'] != 42839
            or ARCHIVES[0]['sha256'] != '3fd4a7a53939590a163d6a0f229503bd368e5e8da4994b7d4115a64a40509a77'
            or ARCHIVES[0]['recovery'] != {
                'kind': 'exact_git_commit_blob',
                'git_commit': 'ea90d1080a4ef59c4bd399c21097e9643aa786df',
                'git_blob': '7e3b02c26d953cc08490a23511dd44e4f814b8e7',
                'note': 'Exact original path in this reachable commit; the later current proof-reader source remains untouched.',
            }
            or MAX_DOCUMENT_BYTES != 64 * 1024 * 1024):
        raise HistoricalEvidenceError('unregistered v35 historical documentary alias')


def archive_paths():
    _validate_registration()
    return (*previous.archive_paths(), *(item['archive_path'] for item in ARCHIVES))


def archive_bindings():
    _validate_registration()
    return previous.archive_bindings() + deepcopy(list(ARCHIVES))


def archive_evidence_documents(root=ROOT):
    """Authenticate all six exact snapshots without importing archived code."""
    _validate_registration()
    result = previous.archive_evidence_documents(root=root)
    for item in ARCHIVES:
        previous._verified_path(item['archive_path'], item['bytes'], item['sha256'], root)
        result.append(dict(path=item['archive_path'], bytes=item['bytes'],
            sha256=item['sha256'], role=ARCHIVE_ROLE))
    return result


def verify_inherited_document(record, *, root=ROOT):
    """Only the exact registered old record may select the new frozen file."""
    _validate_registration()
    path, size, digest = previous._record(record)
    for item in ARCHIVES:
        if path == item['original_path']:
            if size != item['bytes'] or digest != item['sha256']:
                raise HistoricalEvidenceError('changed historical source record; no current-file fallback')
            return previous._verified_path(item['archive_path'], size, digest, root)
    return previous.verify_inherited_document(record, root=root)
