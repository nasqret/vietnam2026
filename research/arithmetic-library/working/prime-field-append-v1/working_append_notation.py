"""Source-only shared definition DAG for the 31 shift/scalar/append laws.

This reuses the frozen 398-definition working vocabulary. Append is expressed
with existing prefix equality and a witnessed next entry, not another alias.
No displayed node or edge authorizes proof acceptance, publication or Alpha.
"""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SHIFT_DIRECTORY = ROOT / "research/arithmetic-library/working/prime-field-shift-v1"
if str(SHIFT_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(SHIFT_DIRECTORY))

import working_shift_scalar_notation as previous

shift = previous.shift
SOURCE = HERE / "prime_field_polynomial_append_candidate.py"
SOURCES = {
    **previous.SOURCES,
    SHIFT_DIRECTORY / "working_shift_notation.py":
        (10437, "d865e613a74c8179849fe4570e7670adde109c5a22da4ea3c154d381a818c9cb"),
    SHIFT_DIRECTORY / "working_shift_scalar_notation.py":
        (3511, "f05cb19ce9eace1a98dc98f13b0478bcd18d4053479b85859726d1ddf746b618"),
    SOURCE: (28396, "271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042"),
    HERE / "test_prime_field_polynomial_append_candidate.py":
        (36494, "0c554b05b2c7e2c40e3b0e8044160379a3284bb173e48d59d77def0cad4272aa"),
}
EXPECTED_SPECS_SHA256 = "9ae49cdf4c7d76b59171fcf3bfe099f8f20990a6b78ea1fc2c3d72f33c2a66e2"
SCHEMA = "working-polynomial-shift-scalar-append-notation-audit-v1"


def require_sources():
    records = {}
    for path, (size, digest) in SOURCES.items():
        if path.is_symlink() or not path.is_file():
            raise shift.NotationError("a frozen continuation input is not an ordinary file")
        raw = path.read_bytes()
        if len(raw) != size or sha256(raw).hexdigest() != digest:
            raise shift.NotationError("a frozen continuation source or independent test changed")
        records[path.relative_to(ROOT).as_posix()] = {"bytes": size, "sha256": digest}
    return records


def source_rows():
    before = require_sources()
    specification = importlib.util.spec_from_file_location("working_append_notation_source_v1", SOURCE)
    if specification is None or specification.loader is None:
        raise shift.NotationError("the exact append source has no loader")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    rows = (*previous.source_rows(),
            *module.make_prime_field_polynomial_append_candidate_theorems(shift.TheoremSpec))
    digest = sha256()
    for row in rows:
        value = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        digest.update((json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n").encode())
    if (len(rows) != 31 or sum(len(row.dependencies) for row in rows) != 123
            or sum(len(row.script) for row in rows) != 2656
            or digest.hexdigest() != EXPECTED_SPECS_SHA256 or require_sources() != before):
        raise shift.NotationError("the exact 31-row continuation inventory changed")
    return rows


def audit():
    before = require_sources()
    result = shift.audit_rows(source_rows())
    result.update(schema=SCHEMA, working_family_counts={"shift": 15, "scalar": 10, "append": 6},
                  ordered_specs_sha256=EXPECTED_SPECS_SHA256, source_pins=before,
                  new_scalar_definitions=0, new_append_definitions=0,
                  reused_definition_ids={"shift": "ND0341", "scalar": "ND0271",
                                         "left_padding": "ND0334", "formal_equivalence": "ND0336"},
                  append_graph="existing decoded prefix equality and actual next-entry witness",
                  associativity_proved=False, gcd_bezout_proved=False)
    if require_sources() != before:
        raise shift.NotationError("continuation bytes changed during source-only compaction")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
