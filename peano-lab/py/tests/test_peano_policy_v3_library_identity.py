"""Checked, source-ordered identity for the 247-theorem model-v3 ladder."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
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
from peano_lab.library.theorems import THEOREMS, replay
from training.peano_policy.library_identity_v3 import (
    CATALOG_SCHEMA,
    LIVE_CATALOG_SCHEMA,
    EXPECTED_FULL_IDENTITY_SHA256,
    EXPECTED_LIBRARY_SIZE,
    EXPECTED_ORDERED_ROOT_SHA256,
    EXPECTED_SOURCE_SHA256,
    LIBRARY_IDENTITY_FORMAT,
    LIBRARY_IDENTITY_VERSION,
    LibraryIdentityV3Error,
    PUBLIC_LIBRARY_CATALOG,
    clear_model_v3_library_identity_cache,
    model_v3_full_identity_sha256,
    model_v3_library_identity,
    model_v3_library_identity_record,
    model_v3_prefix_index,
    model_v3_prefix_names,
    model_v3_prefix_sha256,
)


def _canonical_sha256(value: object) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def test_v3_identity_import_is_light() -> None:
    program = (
        "import sys; "
        "import training.peano_policy.library_identity_v3 as identity; "
        "assert 'peano_lab.library.theorems' not in sys.modules; "
        "assert identity.EXPECTED_LIBRARY_SIZE == 247"
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


def test_catalog_and_prefix_names_bind_the_exact_source_order() -> None:
    catalog = json.loads(PUBLIC_LIBRARY_CATALOG.read_text(encoding="utf-8"))

    assert EXPECTED_LIBRARY_SIZE == 247 < len(THEOREMS)
    assert catalog["schema"] == LIVE_CATALOG_SCHEMA
    assert catalog["theorem_count"] == len(catalog["theorems"]) == len(THEOREMS)
    legacy_fields = {
        "certificate_representation",
        "certificate_sha256",
        "cut_nodes",
        "dependencies",
        "index",
        "layer",
        "name",
        "proof_depth",
        "proof_nodes",
        "script",
        "script_sha256",
        "statement",
        "statement_sha256",
        "summary",
    }
    projected_prefix = [
        {key: row[key] for key in legacy_fields}
        for row in catalog["theorems"][:EXPECTED_LIBRARY_SIZE]
    ]
    assert _canonical_sha256(projected_prefix) == EXPECTED_ORDERED_ROOT_SHA256
    assert model_v3_prefix_names(0) == ()
    assert model_v3_prefix_names(3) == tuple(
        spec.name for spec in THEOREMS[:3]
    )
    assert model_v3_prefix_names(247) == tuple(
        spec.name for spec in THEOREMS[:EXPECTED_LIBRARY_SIZE]
    )
    assert THEOREMS[EXPECTED_LIBRARY_SIZE].name not in model_v3_prefix_names(247)


def test_prefix_index_accepts_exact_sets_and_rejects_non_prefixes() -> None:
    names = model_v3_prefix_names(4)
    assert model_v3_prefix_index(names) == 4
    assert model_v3_prefix_index(frozenset(reversed(names))) == 4
    assert model_v3_prefix_index(()) == 0

    with pytest.raises(ValueError, match="not an exact model-v3 prefix"):
        model_v3_prefix_index((names[0], names[2]))
    with pytest.raises(ValueError, match="distinct strings"):
        model_v3_prefix_index((names[0], names[0]))
    with pytest.raises(ValueError, match="cannot be text"):
        model_v3_prefix_index(names[0])
    for invalid in (-1, 248, True):
        with pytest.raises(ValueError, match="prefix length"):
            model_v3_prefix_names(invalid)  # type: ignore[arg-type]


def test_small_prefix_replays_closed_certificates_through_kernel() -> None:
    """Exercise the full attestation path without the five-minute full ladder."""

    import training.peano_policy.library_identity_v3 as identity

    clear_model_v3_library_identity_cache()
    replay.cache_clear()
    digest = model_v3_prefix_sha256(2)
    records = identity._prefix_identity(2)

    # Calling the full public accessor would intentionally replay all 247
    # entries. The prefix digest has exercised exactly the same record builder.
    assert len(digest) == 64
    assert len(records) == 2
    assert [record.name for record in records] == list(model_v3_prefix_names(2))
    for record in records:
        theorem = replay(record.name)
        assert check((), theorem.certificate, theorem.formula)
        assert proof_metrics(theorem.certificate) == (
            record.proof_nodes,
            record.proof_depth,
        )


def test_v3_identity_commits_the_current_cut_preserving_certificate() -> None:
    import training.peano_policy.library_identity_v3 as identity

    record = identity._prefix_identity(3)[2]
    theorem = replay("add_comm")
    representation = repr(theorem.certificate)

    assert record.name == "add_comm"
    assert "Cut(" in representation
    assert check((), theorem.certificate, theorem.formula)
    assert hashlib.sha256(
        representation.encode("utf-8")
    ).hexdigest() == record.certificate_sha256


def test_prefix_digests_are_cached_and_domain_separated() -> None:
    first_two = model_v3_prefix_names(2)
    assert first_two == ("zero_add", "add_succ_left")
    empty_digest = model_v3_prefix_sha256(0)
    assert empty_digest == model_v3_prefix_sha256(0)
    assert empty_digest != model_v3_prefix_sha256(1)


def test_public_full_document_digest_definition() -> None:
    if os.environ.get("PEANO_V3_FULL_IDENTITY_TEST") != "1":
        pytest.skip("set PEANO_V3_FULL_IDENTITY_TEST=1 for the 247-theorem release gate")

    clear_model_v3_library_identity_cache()
    records = model_v3_library_identity()
    document = model_v3_library_identity_record()
    assert len(records) == document["prefix_length"] == EXPECTED_LIBRARY_SIZE
    assert document["format"] == LIBRARY_IDENTITY_FORMAT
    assert document["v"] == LIBRARY_IDENTITY_VERSION
    assert _canonical_sha256(document) == model_v3_full_identity_sha256()
    assert model_v3_full_identity_sha256() == EXPECTED_FULL_IDENTITY_SHA256
    with pytest.raises(FrozenInstanceError):
        records[0].name = "forged"  # type: ignore[misc]
    document["theorems"][0]["name"] = "forged"  # type: ignore[index]
    assert model_v3_library_identity_record()["theorems"][0]["name"] != "forged"  # type: ignore[index]


def test_catalog_root_corruption_fails_before_replay(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import training.peano_policy.library_identity_v3 as identity

    catalog = json.loads(PUBLIC_LIBRARY_CATALOG.read_text(encoding="utf-8"))
    catalog["ordered_root_sha256"] = "0" * 64
    corrupted = tmp_path / "catalog.json"
    corrupted.write_text(json.dumps(catalog), encoding="utf-8")
    monkeypatch.setattr(identity, "PUBLIC_LIBRARY_CATALOG", corrupted)
    clear_model_v3_library_identity_cache()
    with pytest.raises(LibraryIdentityV3Error, match="ordered root"):
        model_v3_prefix_names(0)
    clear_model_v3_library_identity_cache()


def test_catalog_baseline_rewrite_fails_after_live_root_is_resealed(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import training.peano_policy.library_identity_v3 as identity

    catalog = json.loads(PUBLIC_LIBRARY_CATALOG.read_text(encoding="utf-8"))
    catalog["theorems"][0]["certificate_sha256"] = "0" * 64
    catalog["ordered_root_sha256"] = _canonical_sha256(catalog["theorems"])
    rewritten = tmp_path / "catalog.json"
    rewritten.write_text(json.dumps(catalog), encoding="utf-8")
    monkeypatch.setattr(identity, "PUBLIC_LIBRARY_CATALOG", rewritten)
    clear_model_v3_library_identity_cache()
    with pytest.raises(LibraryIdentityV3Error, match="frozen 247-row baseline"):
        model_v3_prefix_names(0)
    clear_model_v3_library_identity_cache()
