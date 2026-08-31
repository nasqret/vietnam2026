"""Non-authorizing shared notation for the actual associativity-step route.

The 31 frozen shift/scalar/append rows, the modulus-free shift-equivalence
bridge and three actual-witness step rows reuse exactly the same working
398-definition vocabulary. This is a source map, not a dependency-closed
proof artifact, Alpha admission, public explorer or completed associativity.
"""

from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
APPEND_DIRECTORY = HERE.parent / "prime-field-append-v1"
if str(APPEND_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(APPEND_DIRECTORY))

import working_append_notation as previous

shift = previous.shift
BRIDGE_DIRECTORY = HERE.parent / "prime-field-shift-equivalence-v1"
BRIDGE = BRIDGE_DIRECTORY / "prime_field_polynomial_shift_equivalence_candidate.py"
STEP = HERE / "prime_field_polynomial_associativity_step_candidate.py"
SOURCES = {
    **previous.SOURCES,
    APPEND_DIRECTORY / "working_append_notation.py":
        (4068, "b7421fa657f749801ffbd19edae4a6abcbb279363927cf3037cf671a906b2c93"),
    APPEND_DIRECTORY / "test_working_append_notation.py":
        (7475, "c4644d9d11de7ee3003b1a5c5f94781f6e94e104caffd855c25f61ea176c3c3f"),
    BRIDGE: (6021, "8846224923876a4f57ad8d6f31020838ccc86c86a683ec78a7c7c23c35b92068"),
    BRIDGE_DIRECTORY / "test_prime_field_polynomial_shift_equivalence_candidate.py":
        (20376, "9ed90ddc4680f8c2c3d04e2e3a76f8cffda4bfb95b1b83ab391d134c7fe5ab18"),
    STEP: (26607, "dd85dbd1bd87143715a4286724ac7c87f280a909dac6759f00a6cb7dff7c85f1"),
    HERE / "test_prime_field_polynomial_associativity_step_candidate.py":
        (29135, "4cbd15750521b2ad1a3ecd8288bfdf631bd5ad90dc7e623d4e593dc79f615262"),
}
EXPECTED_SPECS_SHA256 = "60a14dc8aecb17f7a2e5f43ccb11d05f520e0277e6604e51c8440974640dbba9"
SCHEMA = "working-polynomial-associativity-step-notation-audit-v1"


def require_sources():
    records = {}
    for path, (size, digest) in SOURCES.items():
        if path.is_symlink() or not path.is_file():
            raise shift.NotationError("a frozen associativity-route input is not an ordinary file")
        raw = path.read_bytes()
        if len(raw) != size or sha256(raw).hexdigest() != digest:
            raise shift.NotationError("a frozen associativity-route source or independent test changed")
        records[path.relative_to(ROOT).as_posix()] = {"bytes": size, "sha256": digest}
    return records


def _load_rows(path, private_name, factory):
    specification = importlib.util.spec_from_file_location(private_name, path)
    if specification is None or specification.loader is None:
        raise shift.NotationError("the exact associativity-route source has no loader")
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return getattr(module, factory)(shift.TheoremSpec)


def source_rows():
    before = require_sources()
    rows = (*previous.source_rows(),
            *_load_rows(BRIDGE, "working_associativity_notation_bridge_v1",
                        "make_prime_field_polynomial_shift_equivalence_candidate_theorems"),
            *_load_rows(STEP, "working_associativity_notation_step_v1",
                        "make_prime_field_polynomial_associativity_step_candidate_theorems"))
    digest = sha256()
    for row in rows:
        value = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        digest.update((json.dumps(value, ensure_ascii=True, separators=(",", ":")) + "\n").encode())
    if (len(rows) != 35 or sum(len(row.dependencies) for row in rows) != 166
            or sum(len(row.script) for row in rows) != 3916
            or digest.hexdigest() != EXPECTED_SPECS_SHA256 or require_sources() != before):
        raise shift.NotationError("the exact 35-row associativity-route inventory changed")
    return rows


def audit():
    before = require_sources()
    result = shift.audit_rows(source_rows())
    result.update(
        schema=SCHEMA,
        working_family_counts={"shift": 15, "scalar": 10, "append": 6,
                               "shift_equivalence": 1, "associativity_step": 3},
        ordered_specs_sha256=EXPECTED_SPECS_SHA256, source_pins=before,
        additional_definitions_beyond_shift=0,
        reused_definition_ids={"shift": "ND0341", "scalar": "ND0271",
                               "left_padding": "ND0334", "formal_equivalence": "ND0336"},
        full_induction_included=False,
        associativity_proved=False, gcd_bezout_proved=False,
        evidence_boundary="Source syntax only: this graph does not establish even its step bodies.",
    )
    if require_sources() != before:
        raise shift.NotationError("associativity-route bytes changed during source-only compaction")
    return result


if __name__ == "__main__":
    print(json.dumps(audit(), ensure_ascii=False, indent=2, sort_keys=True))
