"""Source-only combined52 map, reusing the exact existing399 definitions.

Left-unit witnesses and reflexive right-divisibility introduce no definition
identity. Every statement/local formula is compacted through the existing
conservative registry, while actual proof checks remain separate.
"""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
PREVIOUS_DIRECTORY = HERE.parent / 'prime-field-divisibility-v1'
if str(PREVIOUS_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(PREVIOUS_DIRECTORY))

import working_divisibility_notation as previous

NotationError = previous.NotationError
DEFINITIONS = previous.DEFINITIONS
REGISTRIES = previous.REGISTRIES
SOURCE = HERE / 'prime_field_polynomial_left_unit_candidate.py'
SOURCES = {
    **previous.SOURCES,
    PREVIOUS_DIRECTORY / 'working_divisibility_notation.py':
        (11815, '631eac7fb1c4795af4adf66cd5ff5b9753debaa810c8ae8dc2eddd1a66a70c22'),
    PREVIOUS_DIRECTORY / 'test_working_divisibility_notation.py':
        (8556, 'cd8a7d648b7ee132935dd043cddc888f8030d7b2de801021b2c2133f3beece2d'),
    SOURCE: (16858, 'dbb8debb4716b6bb9b246700f7e93865c8a6c1b12a3b65c0ffbb62206a890ba6'),
    HERE / 'test_prime_field_polynomial_left_unit_candidate.py':
        (16474, '5b8758079485c1c7f8a448f218a4b70b9e5df11722eabf63ec6fcc1e68802c71'),
}
LEFT_UNIT_SPECS_SHA256 = 'd948ceded7269773df58eca0ec6d16f77aa8f207483beed48f85bec30e083f08'
SCHEMA = 'working-polynomial-left-unit-notation-audit-v1'


def require_sources():
    records = {}
    for path, (size, digest) in SOURCES.items():
        if path.is_symlink() or not path.is_file():
            raise NotationError('a frozen left-unit-map input is not an ordinary file')
        raw = path.read_bytes()
        if len(raw) != size or sha256(raw).hexdigest() != digest:
            raise NotationError('a frozen left-unit-map source or independent test changed')
        records[path.relative_to(ROOT).as_posix()] = {'bytes': size, 'sha256': digest}
    return records


require_sources()
_specification = importlib.util.spec_from_file_location('working_left_unit_notation_source_v1', SOURCE)
if _specification is None or _specification.loader is None:
    raise NotationError('the exact left-unit source has no loader')
_candidate = importlib.util.module_from_spec(_specification)
_specification.loader.exec_module(_candidate)


def source_rows():
    before = require_sources()
    new = _candidate.make_prime_field_polynomial_left_unit_candidate_theorems(previous.shift.TheoremSpec)
    if (len(new) != 8 or sum(len(row.dependencies) for row in new) != 35
            or sum(len(row.script) for row in new) != 466
            or previous.specs_digest(new) != LEFT_UNIT_SPECS_SHA256):
        raise NotationError('the exact eight left-unit/reflexivity specifications changed')
    rows = (*previous.source_rows(), *new)
    if (len(rows) != 52 or sum(len(row.dependencies) for row in rows) != 234
            or sum(len(row.script) for row in rows) != 5256 or require_sources() != before):
        raise NotationError('the exact combined52 source inventory changed')
    return rows


def audit_rows(rows):
    before = require_sources()
    result = previous.audit_rows(rows)
    if require_sources() != before:
        raise NotationError('left-unit-map inputs changed during exact source compaction')
    result.update({
        'schema': SCHEMA,
        'source_pins': before,
        'additional_definitions_beyond_divisibility': 0,
        'left_unit_included': any(row.name == 'prime_field_polynomial_convolution_left_unit_exists'
                                  for row in rows),
        'left_unit_proved': False,
        'reflexive_divisibility_proved': False,
    })
    return result


def audit():
    return audit_rows(source_rows())


if __name__ == '__main__':
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
