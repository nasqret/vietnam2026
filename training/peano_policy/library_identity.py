"""Content identity for the complete model-v2 theorem authority.

This module deliberately has no eager Peano Lab imports.  Reading constants or
importing training helpers must not replay forty-five theorem certificates.
The first call to :func:`model_v2_library_identity` loads the public library,
replays every permitted theorem, asks the independent kernel to check the
resulting *closed* certificate again, and freezes the resulting records.

Hash preimages are intentionally explicit:

* ``source_spec_sha256`` hashes the canonical JSON form of all five fields in
  the repository's :class:`TheoremSpec` (including its source statement,
  tactic script, and pedagogical summary);
* ``script_sha256`` hashes the canonical JSON array of exact tactic lines;
* ``certificate_sha256`` hashes the deterministic ``repr`` of the closed proof
  term, matching the public modular-arithmetic validation artifact; and
* the library digest hashes the versioned canonical JSON identity document.

Only the kernel-checked identity is cached.  JSON-shaped accessors always
construct fresh containers, so a caller cannot mutate the cached attestation.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys
from typing import TYPE_CHECKING


if TYPE_CHECKING:  # pragma: no cover - imports used by static type checkers only
    from peano_lab.library.theorems import TheoremSpec


LIBRARY_IDENTITY_FORMAT = "peano-model-v2-library-identity"
LIBRARY_IDENTITY_VERSION = 1

# These are evaluation targets, not model-v2 premises.  The identity module
# owns the boundary so prompt, dataset, evaluator, and request integrations can
# all consume the same immutable definition without creating an import cycle.
SEALED_LIBRARY_GOALS: tuple[tuple[str, str], ...] = (
    ("le_trans", "forall n m k. n <= m -> m <= k -> n <= k"),
    ("le_antisymm", "forall n m. n <= m -> m <= n -> n = m"),
    ("le_total", "forall n m. n <= m \\/ m <= n"),
    ("mul_eq_zero", "forall n m. n * m = 0 -> n = 0 \\/ m = 0"),
)
SEALED_LIBRARY_NAMES = frozenset(name for name, _ in SEALED_LIBRARY_GOALS)

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
MOD5_SOURCE_REPORT = (
    REPOSITORY_ROOT
    / "artifacts"
    / "peano-library"
    / "mod5-source-validation-report.json"
)


class LibraryIdentityError(RuntimeError):
    """The public theorem authority could not be independently identified."""


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _json_sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True, slots=True)
class LibraryIdentityRecord:
    """One independently replayed theorem in the model-v2 authority."""

    name: str
    statement: str
    dependencies: tuple[str, ...]
    source_spec_sha256: str
    script_sha256: str
    certificate_sha256: str
    proof_nodes: int
    proof_depth: int

    def to_record(self) -> dict[str, object]:
        """Return a fresh canonical-JSON-compatible record."""

        return {
            "name": self.name,
            "statement": self.statement,
            "dependencies": list(self.dependencies),
            "source_spec_sha256": self.source_spec_sha256,
            "script_sha256": self.script_sha256,
            "certificate_sha256": self.certificate_sha256,
            "proof_nodes": self.proof_nodes,
            "proof_depth": self.proof_depth,
        }


def _source_spec_record(spec: "TheoremSpec") -> dict[str, object]:
    """Canonical value-level preimage of an exact repository theorem spec."""

    return {
        "name": spec.name,
        "statement": spec.statement,
        "dependencies": list(spec.dependencies),
        "script": list(spec.script),
        "summary": spec.summary,
    }


def _load_mod5_report() -> dict[str, object]:
    try:
        raw = MOD5_SOURCE_REPORT.read_bytes()
        report = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LibraryIdentityError(
            "cannot read the modular-arithmetic source validation report"
        ) from exc
    if type(report) is not dict:
        raise LibraryIdentityError(
            "modular-arithmetic source validation report must be an object"
        )
    return report


def _mod5_rows(report: dict[str, object]) -> dict[str, dict[str, object]]:
    rows = report.get("lemmas")
    if type(rows) is not list or not rows:
        raise LibraryIdentityError(
            "modular-arithmetic source validation report has no lemma rows"
        )
    result: dict[str, dict[str, object]] = {}
    for row in rows:
        if type(row) is not dict or type(row.get("name")) is not str:
            raise LibraryIdentityError(
                "modular-arithmetic source validation report has a malformed lemma"
            )
        name = row["name"]
        if name in result:
            raise LibraryIdentityError(
                f"duplicate modular-arithmetic validation row {name!r}"
            )
        result[name] = row
    return result


def _canonical_closed_statement(source: str) -> str:
    from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula

    formula, free_names = parse_formula_with_names(source)
    if free_names:
        raise LibraryIdentityError(
            "model-v2 theorem statement is not closed; free variable(s): "
            + ", ".join(free_names)
        )
    return pretty_formula(formula, list(free_names))


def _validate_mod5_record(
    record: LibraryIdentityRecord,
    row: dict[str, object],
) -> None:
    try:
        artifact_statement = _canonical_closed_statement(str(row["statement"]))
    except (KeyError, ValueError) as exc:
        raise LibraryIdentityError(
            f"source validation row for {record.name!r} is malformed"
        ) from exc
    expected = {
        "statement": artifact_statement,
        "dependencies": tuple(row.get("dependencies", ())),
        "certificate_sha256": row.get("certificate_sha256"),
        "proof_nodes": row.get("proof_nodes"),
        "proof_depth": row.get("proof_depth"),
    }
    actual = {
        "statement": record.statement,
        "dependencies": record.dependencies,
        "certificate_sha256": record.certificate_sha256,
        "proof_nodes": record.proof_nodes,
        "proof_depth": record.proof_depth,
    }
    if actual != expected:
        differing = ", ".join(
            key for key in actual if actual[key] != expected[key]
        )
        raise LibraryIdentityError(
            f"source validation mismatch for {record.name!r}: {differing}"
        )


@lru_cache(maxsize=1)
def model_v2_library_identity() -> tuple[LibraryIdentityRecord, ...]:
    """Replay and return the exact 45-theorem model-v2 library identity.

    Results are sorted by theorem name rather than source order.  Source order
    remains committed by each theorem's dependency tuple and source-spec hash.
    """

    if str(PEANO_PYTHON) not in sys.path:
        sys.path.insert(0, str(PEANO_PYTHON))

    from peano_lab.engine.state import proof_metrics
    from peano_lab.kernel.checker import check
    from peano_lab.library.theorems import MOD5_THEOREMS, THEOREMS, replay

    names = [spec.name for spec in THEOREMS]
    if len(names) != len(set(names)):
        raise LibraryIdentityError("public theorem library has duplicate names")
    sealed_missing = SEALED_LIBRARY_NAMES.difference(names)
    if sealed_missing:
        raise LibraryIdentityError(
            "sealed theorem(s) are absent from the public library: "
            + ", ".join(sorted(sealed_missing))
        )

    canonical_sealed = {
        name: _canonical_closed_statement(statement)
        for name, statement in SEALED_LIBRARY_GOALS
    }
    specs_by_name = {spec.name: spec for spec in THEOREMS}
    for name, statement in canonical_sealed.items():
        actual = _canonical_closed_statement(specs_by_name[name].statement)
        if actual != statement:
            raise LibraryIdentityError(
                f"sealed theorem {name!r} no longer states its frozen target"
            )
    sealed_statements = frozenset(canonical_sealed.values())
    allowed_names = frozenset(names).difference(SEALED_LIBRARY_NAMES)
    for spec in THEOREMS:
        if spec.name in SEALED_LIBRARY_NAMES:
            continue
        statement = _canonical_closed_statement(spec.statement)
        if statement in sealed_statements:
            raise LibraryIdentityError(
                f"allowed theorem {spec.name!r} aliases a sealed target"
            )
        unavailable = set(spec.dependencies).difference(allowed_names)
        if unavailable:
            raise LibraryIdentityError(
                f"allowed theorem {spec.name!r} depends outside model-v2: "
                + ", ".join(sorted(unavailable))
            )

    mod5_names = {spec.name for spec in MOD5_THEOREMS}
    report = _load_mod5_report()
    report_rows = _mod5_rows(report)
    if set(report_rows) != mod5_names:
        raise LibraryIdentityError(
            "modular-arithmetic source report does not identify the exact import"
        )

    records: list[LibraryIdentityRecord] = []
    for spec in THEOREMS:
        if spec.name in SEALED_LIBRARY_NAMES:
            continue
        checked = replay(spec.name)
        if checked.spec != spec:
            raise LibraryIdentityError(
                f"library replay returned the wrong spec for {spec.name!r}"
            )
        if not check((), checked.certificate, checked.formula):
            raise LibraryIdentityError(
                f"independent kernel rejected model-v2 theorem {spec.name!r}"
            )
        statement = _canonical_closed_statement(spec.statement)
        if checked.formula != _parse_closed_formula(spec.statement):
            raise LibraryIdentityError(
                f"library replay returned the wrong formula for {spec.name!r}"
            )
        nodes, depth = proof_metrics(checked.certificate)
        if checked.proof_nodes != nodes:
            raise LibraryIdentityError(
                f"library replay reported inconsistent metrics for {spec.name!r}"
            )
        record = LibraryIdentityRecord(
            name=spec.name,
            statement=statement,
            dependencies=tuple(spec.dependencies),
            source_spec_sha256=_json_sha256(_source_spec_record(spec)),
            script_sha256=_json_sha256(list(spec.script)),
            certificate_sha256=hashlib.sha256(
                repr(checked.certificate).encode("utf-8")
            ).hexdigest(),
            proof_nodes=nodes,
            proof_depth=depth,
        )
        if spec.name in mod5_names:
            _validate_mod5_record(record, report_rows[spec.name])
        records.append(record)

    expected_count = len(THEOREMS) - len(SEALED_LIBRARY_NAMES)
    if len(records) != expected_count or expected_count != 45:
        raise LibraryIdentityError(
            f"model-v2 library must contain exactly 45 theorems, got {len(records)}"
        )
    return tuple(sorted(records, key=lambda item: item.name))


def _parse_closed_formula(source: str) -> object:
    """Parse a closed formula without exporting a kernel type at import time."""

    from peano_lab.kernel.formulas import parse_formula_with_names

    formula, free_names = parse_formula_with_names(source)
    if free_names:
        raise LibraryIdentityError(
            "model-v2 theorem statement is not closed; free variable(s): "
            + ", ".join(free_names)
        )
    return formula


def model_v2_library_identity_record() -> dict[str, object]:
    """Return a fresh versioned JSON identity document."""

    return {
        "format": LIBRARY_IDENTITY_FORMAT,
        "v": LIBRARY_IDENTITY_VERSION,
        "theorems": [
            record.to_record() for record in model_v2_library_identity()
        ],
    }


@lru_cache(maxsize=1)
def model_v2_library_identity_sha256() -> str:
    """Return the canonical JSON SHA-256 of the full identity document."""

    return _json_sha256(model_v2_library_identity_record())


def clear_model_v2_library_identity_cache() -> None:
    """Clear only this module's immutable identity cache (primarily for tests)."""

    model_v2_library_identity_sha256.cache_clear()
    model_v2_library_identity.cache_clear()


__all__ = [
    "LIBRARY_IDENTITY_FORMAT",
    "LIBRARY_IDENTITY_VERSION",
    "SEALED_LIBRARY_GOALS",
    "SEALED_LIBRARY_NAMES",
    "LibraryIdentityError",
    "LibraryIdentityRecord",
    "model_v2_library_identity",
    "model_v2_library_identity_record",
    "model_v2_library_identity_sha256",
    "clear_model_v2_library_identity_cache",
]
