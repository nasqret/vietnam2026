"""Source-only 37-law definition/DAG map, including the actual induction.

Including an induction specification does not verify it. All 397 canonical
definitions and the sole working shift abbreviation are reused unchanged;
proof prerequisites, definition uses and abbreviation expansions stay apart.
"""

from hashlib import sha256
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
STEP_DIRECTORY = HERE.parent / "prime-field-associativity-step-v1"
if str(STEP_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(STEP_DIRECTORY))

import working_associativity_notation as previous

shift = previous.shift
SOURCE = HERE / "prime_field_polynomial_associativity_induction_candidate.py"
SOURCES = {
    **previous.SOURCES,
    STEP_DIRECTORY / "working_associativity_notation.py":
        (4977, "66e164502873df086e1a28f5cb2cea089551c61cc9870a0a07e1cb42b79c4b26"),
    STEP_DIRECTORY / "test_working_associativity_notation.py":
        (7372, "496ee45a6a6160bcd4b41028011e1f7e232639d8281dae7b3329656330b52b69"),
    SOURCE: (9924, "8d276a028764cd08e6eaebbf25bb4e21fcd5076a610d356a77d52ba6603ebe4c"),
    HERE / "test_prime_field_polynomial_associativity_induction_candidate.py":
        (19628, "d3725cbdd86f8d72446baf5417d25a4ddf31f61b0b6f1d076cb065b8131f2003"),
}
EXPECTED_SPECS_SHA256 = "de95fea3806bc6c227c032bf2c29095ce191e27624c2196bd417df6c77c31491"
SCHEMA = "working-polynomial-associativity-induction-notation-audit-v1"


def require_sources():
    records = {}
    for path, (size, digest) in SOURCES.items():
        if path.is_symlink() or not path.is_file():
            raise shift.NotationError("a frozen induction-map input is not an ordinary file")
        raw = path.read_bytes()
        if len(raw) != size or sha256(raw).hexdigest() != digest:
            raise shift.NotationError("a frozen induction-map source or independent test changed")
        records[path.relative_to(ROOT).as_posix()] = {"bytes": size, "sha256": digest}
    return records


def source_rows():
    before = require_sources()
    rows = (*previous.source_rows(),
            *previous._load_rows(SOURCE, "working_induction_notation_source_v1",
                                 "make_prime_field_polynomial_associativity_induction_candidate_theorems"))
    digest = sha256()
    for row in rows:
        value = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        digest.update((json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n").encode())
    if (len(rows) != 37 or sum(len(row.dependencies) for row in rows) != 179
            or sum(len(row.script) for row in rows) != 4303
            or digest.hexdigest() != EXPECTED_SPECS_SHA256 or require_sources() != before):
        raise shift.NotationError("the exact 37-row induction-map inventory changed")
    return rows


def audit():
    before = require_sources()
    result = shift.audit_rows(source_rows())
    result.update(
        schema=SCHEMA,
        working_family_counts={"shift": 15, "scalar": 10, "append": 6,
                               "shift_equivalence": 1, "associativity_step": 3,
                               "associativity_induction": 2},
        ordered_specs_sha256=EXPECTED_SPECS_SHA256, source_pins=before,
        additional_definitions_beyond_shift=0,
        reused_definition_ids={"shift": "ND0341", "scalar": "ND0271",
                               "left_padding": "ND0334", "formal_equivalence": "ND0336"},
        full_induction_included=True,
        associativity_proved=False, gcd_bezout_proved=False,
        evidence_boundary="The universal induction source is included; no proof is accepted by this syntax map.",
    )
    if require_sources() != before:
        raise shift.NotationError("induction-map bytes changed during source-only compaction")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
