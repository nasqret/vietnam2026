"""Full content identity for the model-v2 public theorem authority."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from peano_lab.engine.state import proof_metrics
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
import peano_lab.library.theorems as theorem_library
from peano_lab.library.theorems import MOD5_THEOREMS, THEOREMS, get, replay
from training.peano_policy.library_identity import (
    EXPECTED_MODEL_V2_LIBRARY_COUNT,
    EXPECTED_PUBLIC_LIBRARY_COUNT,
    LIBRARY_IDENTITY_FORMAT,
    LIBRARY_IDENTITY_VERSION,
    MOD5_SOURCE_REPORT,
    PUBLIC_LIBRARY_CATALOG,
    SEALED_LIBRARY_GOALS,
    SEALED_LIBRARY_NAMES,
    LibraryIdentityError,
    clear_model_v2_library_identity_cache,
    model_v2_library_identity,
    model_v2_library_identity_record,
    model_v2_library_identity_sha256,
    sealed_library_closure,
)


EXPECTED_IDENTITY_SHA256 = (
    "3ce83721f4517f2d5f2e734da1fbeae086473c4d1b8abb45d875a52769096439"
)


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_bytes(value)).hexdigest()


def _canonical_statement(source: str) -> str:
    formula, free_names = parse_formula_with_names(source)
    assert free_names == ()
    return pretty_formula(formula, list(free_names))


def test_identity_import_is_light_and_does_not_load_the_prover() -> None:
    program = (
        "import sys; "
        "import training.peano_policy.library_identity as identity; "
        "assert 'peano_lab.library.theorems' not in sys.modules; "
        "assert identity.LIBRARY_IDENTITY_VERSION == 1"
    )
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(REPOSITORY_ROOT)
    completed = subprocess.run(
        [sys.executable, "-c", program],
        cwd=REPOSITORY_ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_full_identity_replays_exactly_56_closed_kernel_certificates() -> None:
    clear_model_v2_library_identity_cache()
    replay.cache_clear()

    records = model_v2_library_identity()
    excluded_names = sealed_library_closure(THEOREMS)
    expected_names = sorted(
        spec.name for spec in THEOREMS if spec.name not in excluded_names
    )

    assert len(THEOREMS) == EXPECTED_PUBLIC_LIBRARY_COUNT == 63
    assert len(records) == EXPECTED_MODEL_V2_LIBRARY_COUNT == 56
    assert [record.name for record in records] == expected_names
    assert {record.name for record in records}.isdisjoint(excluded_names)
    assert excluded_names == SEALED_LIBRARY_NAMES | {
        "mul_ne_zero",
        "two_large_factors_impossible",
        "prime_two",
    }
    assert model_v2_library_identity_sha256() == EXPECTED_IDENTITY_SHA256
    sealed_statements = {
        _canonical_statement(statement) for _, statement in SEALED_LIBRARY_GOALS
    }
    allowed_names = {record.name for record in records}

    for record in records:
        theorem = replay(record.name)
        nodes, depth = proof_metrics(theorem.certificate)
        assert check((), theorem.certificate, theorem.formula)
        assert _canonical_statement(theorem.spec.statement) == record.statement
        assert theorem.spec.dependencies == record.dependencies
        assert (nodes, depth) == (record.proof_nodes, record.proof_depth)
        assert hashlib.sha256(
            repr(theorem.certificate).encode("utf-8")
        ).hexdigest() == record.certificate_sha256
        assert record.statement not in sealed_statements
        assert set(record.dependencies) <= allowed_names


def test_identity_rejects_a_renamed_alias_of_a_sealed_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replacement = tuple(
        replace(
            spec,
            statement=SEALED_LIBRARY_GOALS[0][1],
        )
        if spec.name == "zero_add"
        else spec
        for spec in THEOREMS
    )
    monkeypatch.setattr(theorem_library, "THEOREMS", replacement)
    clear_model_v2_library_identity_cache()
    with pytest.raises(LibraryIdentityError, match="aliases a sealed target"):
        model_v2_library_identity()
    clear_model_v2_library_identity_cache()


def test_identity_rejects_an_authority_change_that_adds_a_sealed_descendant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replacement = tuple(
        replace(spec, dependencies=("le_total",))
        if spec.name == "zero_add"
        else spec
        for spec in THEOREMS
    )
    monkeypatch.setattr(theorem_library, "THEOREMS", replacement)
    clear_model_v2_library_identity_cache()
    with pytest.raises(LibraryIdentityError, match="public catalog source mismatch"):
        model_v2_library_identity()
    clear_model_v2_library_identity_cache()


def test_source_spec_and_script_hashes_commit_their_documented_preimages() -> None:
    spec = get("zero_add")
    assert spec is not None
    record = next(
        item for item in model_v2_library_identity() if item.name == spec.name
    )
    source_preimage = {
        "name": spec.name,
        "statement": spec.statement,
        "dependencies": list(spec.dependencies),
        "script": list(spec.script),
        "summary": spec.summary,
    }

    assert record.source_spec_sha256 == _sha256(source_preimage)
    assert record.script_sha256 == _sha256(list(spec.script))
    assert record.source_spec_sha256 != _sha256(
        {**source_preimage, "summary": spec.summary + " changed"}
    )
    assert record.script_sha256 != _sha256([*spec.script, "refl"])


def test_all_26_imported_records_match_the_public_source_report() -> None:
    report = json.loads(MOD5_SOURCE_REPORT.read_text(encoding="utf-8"))
    source_rows = {row["name"]: row for row in report["lemmas"]}
    records = {record.name: record for record in model_v2_library_identity()}

    assert set(source_rows) == {spec.name for spec in MOD5_THEOREMS}
    for name, row in source_rows.items():
        record = records[name]
        assert record.statement == _canonical_statement(row["statement"])
        assert list(record.dependencies) == row["dependencies"]
        assert record.certificate_sha256 == row["certificate_sha256"]
        assert record.proof_nodes == row["proof_nodes"]
        assert record.proof_depth == row["proof_depth"]


def test_all_63_source_rows_match_the_public_checked_catalog() -> None:
    catalog = json.loads(PUBLIC_LIBRARY_CATALOG.read_text(encoding="utf-8"))
    rows = catalog["theorems"]

    assert catalog["schema"] == "peano-library-snapshot-v1"
    assert catalog["theorem_count"] == len(rows) == len(THEOREMS) == 63
    assert [row["name"] for row in rows] == [spec.name for spec in THEOREMS]
    assert catalog["ordered_root_sha256"] == (
        "d0f9070a2677a03eeca8ce2d1b83bcee04df3c907ef8cec2f797ab5ef99e5db0"
    )


def test_identity_document_is_canonical_and_cached_state_cannot_be_poisoned() -> None:
    first = model_v2_library_identity()
    second = model_v2_library_identity()
    assert second is first
    with pytest.raises(FrozenInstanceError):
        first[0].name = "forged"  # type: ignore[misc]

    document = model_v2_library_identity_record()
    assert document["format"] == LIBRARY_IDENTITY_FORMAT
    assert document["v"] == LIBRARY_IDENTITY_VERSION
    assert _sha256(document) == model_v2_library_identity_sha256()

    document["theorems"][0]["name"] = "forged"  # type: ignore[index]
    fresh = model_v2_library_identity_record()
    assert fresh["theorems"][0]["name"] == first[0].name  # type: ignore[index]
    assert _sha256(fresh) == EXPECTED_IDENTITY_SHA256
