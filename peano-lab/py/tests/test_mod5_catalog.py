"""Public import regression for the checked modular-arithmetic catalog."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import driver

from peano_lab.engine.state import proof_metrics
from peano_lab.engine.tactics import (
    MAX_LIVE_PROOF_DEPTH,
    MAX_LIVE_PROOF_NODES,
    MAX_USE_CERTIFICATE_NODES,
    MAX_USE_PARTIAL_NODES,
    MAX_USE_PROOF_DEPTH,
)
from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import parse_formula
from peano_lab.library.theorems import (
    MOD5_LIBRARY_CATALOG_SHA256,
    MOD5_LIBRARY_SOURCE_COMMIT,
    MOD5_THEOREMS,
    _specs_by_name,
    replay,
)
from peano_lab.ui.prove import checked_surface_final, get_owner


REPO = Path(__file__).resolve().parents[3]
SOURCE_REPORT = (
    REPO / "artifacts" / "peano-library" / "mod5-source-validation-report.json"
)


def _certificate_sha256(certificate: object) -> str:
    return hashlib.sha256(repr(certificate).encode("utf-8")).hexdigest()


def _cold_replay_rows() -> tuple[tuple[str, int, int, str], ...]:
    replay.cache_clear()
    _specs_by_name.cache_clear()
    rows = []
    for spec in MOD5_THEOREMS:
        theorem = replay(spec.name)
        nodes, depth = proof_metrics(theorem.certificate)
        assert check((), theorem.certificate, theorem.formula)
        rows.append(
            (spec.name, nodes, depth, _certificate_sha256(theorem.certificate))
        )
    return tuple(rows)


def test_public_mod5_catalog_matches_its_source_validation_artifact() -> None:
    report_bytes = SOURCE_REPORT.read_bytes()
    report = json.loads(report_bytes)

    assert hashlib.sha256(report_bytes).hexdigest() == (
        "bbbfb1a9f228b63aa191c1aabc24297bbef614b40bf7a0bd39d35ca42b69bc36"
    )
    assert MOD5_LIBRARY_SOURCE_COMMIT == (
        "d2ba05dca952e2e33479923433f8d2fcd3409493"
    )
    assert report["catalog_sha256"] == MOD5_LIBRARY_CATALOG_SHA256
    assert report["lemma_count"] == len(MOD5_THEOREMS) == 26
    assert [spec.name for spec in MOD5_THEOREMS] == [
        row["name"] for row in report["lemmas"]
    ]

    source_catalog = [
        {
            "name": spec.name,
            "statement": spec.statement,
            "dependencies": spec.dependencies,
            "script": spec.script,
            "summary": spec.summary,
            "layer": row["layer"],
            "use_tier": row["use_tier"],
        }
        for spec, row in zip(MOD5_THEOREMS, report["lemmas"], strict=True)
    ]
    canonical_catalog = json.dumps(
        source_catalog,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert hashlib.sha256(canonical_catalog).hexdigest() == (
        MOD5_LIBRARY_CATALOG_SHA256
    )

    assert MAX_USE_CERTIFICATE_NODES == (
        report["budgets"]["recommended_certificate_nodes"]
    ) == 32_768
    assert MAX_USE_PARTIAL_NODES == 32_768
    assert MAX_USE_PROOF_DEPTH == 128
    assert MAX_LIVE_PROOF_NODES == 100_000
    assert MAX_LIVE_PROOF_DEPTH == 256

    expected = tuple(
        (
            row["name"],
            row["proof_nodes"],
            row["proof_depth"],
            row["certificate_sha256"],
        )
        for row in report["lemmas"]
    )
    first = _cold_replay_rows()
    second = _cold_replay_rows()

    assert first == expected
    assert second == first
    assert sum(row[1] for row in first) == report["total_proof_nodes"] == 48_121
    assert max(row[1] for row in first) == report["max_proof_nodes"] == 21_515
    assert max(row[2] for row in first) == report["max_proof_depth"] == 66


def test_capstone_can_be_used_to_close_the_original_problem() -> None:
    session = driver.LabSession()
    commands = (
        "pa prove forall n. ~(exists x. n = 5 * x) -> "
        "exists x. n * n * n * n = 5 * x + 1",
        "intro n",
        "intro h",
        "use mod5_fourth_power_one",
        "apply mod5_fourth_power_one",
        "exact h",
    )
    for command in commands:
        result = session.run_result(command)
        assert result["failed"] is False, (command, result["out"])

    owner = get_owner(session.webstate)
    assert owner is not None and not owner.state.goals
    assert proof_metrics(owner.state.partial) == (21_523, 69)
    certificate = checked_surface_final(
        owner.state,
        owner.original_target,
        classical=owner.classical,
    )
    assert proof_metrics(certificate) == (21_515, 66)
    assert check((), certificate, owner.original_target)

    mutation = parse_formula(
        "forall n. ~(exists x. n = 5 * x) -> "
        "exists x. n * n * n * n = 5 * x + 2"
    )
    assert not check((), certificate, mutation)
    assert "QED." in session.run("qed")


def test_two_capstone_imports_still_fail_at_the_partial_certificate_limit() -> None:
    session = driver.LabSession()
    session.run("pa prove 0 = 0")
    first = session.run_result("use mod5_fourth_power_one")
    assert first["failed"] is False
    owner = get_owner(session.webstate)
    assert owner is not None
    before = owner.state

    second = session.run_result("use mod5_fourth_power_one as capstone2")

    assert second["failed"] is True
    assert "live-certificate limit" in str(second["out"])
    assert get_owner(session.webstate).state is before
