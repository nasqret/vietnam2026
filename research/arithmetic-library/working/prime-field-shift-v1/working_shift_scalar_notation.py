"""One source-only definition-aware map of the frozen 25 shift/scalar rows.

The 398/867 working registry is reused without adding a scalar alias. This
module cannot verify a proof, authorize Alpha membership or publish readers.
"""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path

import working_shift_notation as shift


ROOT = shift.ROOT
SCALAR_DIRECTORY = ROOT / "research/arithmetic-library/working/prime-field-scalar-v1"
SCALAR_SOURCE = SCALAR_DIRECTORY / "prime_field_polynomial_scalar_convolution_candidate.py"
SOURCES = {
    shift.SOURCE: (29786, "325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b"),
    shift.HERE / "test_prime_field_polynomial_shift_candidate.py":
        (32010, "0622fb92978fcf028842aa4d9822ef61213642eb852e080f7c787dcea4bb395f"),
    SCALAR_SOURCE: (23637, "e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e"),
    SCALAR_DIRECTORY / "test_prime_field_polynomial_scalar_convolution_candidate.py":
        (30353, "881452ada0b5dc3be7d6cd00ee31dc08075b07f51d83595ee60f8cfb40d4c6e5"),
}
EXPECTED_SPECS_SHA256 = "15d48cfcf25a997db2e18771d0c084f4465225c6137f47f53350d39a5ebb6981"
SCHEMA = "working-polynomial-shift-scalar-notation-audit-v1"


def require_sources():
    result = {}
    for path, (size, digest) in SOURCES.items():
        if path.is_symlink() or not path.is_file():
            raise shift.NotationError("a frozen shift/scalar source is not an ordinary file")
        raw = path.read_bytes()
        if len(raw) != size or sha256(raw).hexdigest() != digest:
            raise shift.NotationError("a frozen shift/scalar source or independent test changed")
        result[path.relative_to(ROOT).as_posix()] = {"bytes": size, "sha256": digest}
    return result


def source_rows():
    before = require_sources()
    spec = importlib.util.spec_from_file_location("working_scalar_notation_source_v1", SCALAR_SOURCE)
    if spec is None or spec.loader is None:
        raise shift.NotationError("the exact scalar source has no loader")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    rows = (*shift.source_rows(), *module.make_prime_field_polynomial_scalar_convolution_candidate_theorems(shift.TheoremSpec))
    digest = sha256()
    for row in rows:
        value = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        digest.update((json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n").encode())
    if (len(rows) != 25 or sum(len(row.dependencies) for row in rows) != 81
            or sum(len(row.script) for row in rows) != 1778
            or digest.hexdigest() != EXPECTED_SPECS_SHA256 or require_sources() != before):
        raise shift.NotationError("the exact 25-row shift/scalar inventory changed")
    return rows


def audit():
    before = require_sources()
    rows = source_rows()
    result = shift.audit_rows(rows)
    result.update(schema=SCHEMA, working_family_counts={"shift": 15, "scalar": 10},
                  ordered_specs_sha256=EXPECTED_SPECS_SHA256, source_pins=before,
                  new_scalar_definitions=0, scalar_definition_id="ND0271",
                  associativity_proved=False, gcd_bezout_proved=False)
    if require_sources() != before:
        raise shift.NotationError("shift/scalar input bytes changed during source-only compaction")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
