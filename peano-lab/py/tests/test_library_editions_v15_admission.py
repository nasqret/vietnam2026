"""Exact Alpha-v15 supplementary/two-square admission and evidence audit."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path

import pytest

from peano_lab.library import editions_v14 as v14
from peano_lab.library import editions_v15 as v15
from peano_lab.library import alpha_enrollment_v15 as enrollment_module
from peano_lab.library.candidate_validation import CandidateBodyError, replay_candidate_bodies


REPOSITORY = Path(__file__).resolve().parents[3]
ROOT_HASHES = {
    "quadratic_supplement_minus_one_complete": (
        "7ea81062b843e7fff4939ffce5b6fa14a87312619f7f49e3abd5993bfa02134e"
    ),
    "quadratic_supplement_two_complete": (
        "146a886f8f3a54d358321b54faf68a591362016e86139bd487a5496c7af74034"
    ),
    "two_square_iff_zero_or_even_three_mod_four_prime_valuations": (
        "4c39da833a313bab5ae810215dae5bbc9cc78ea951fe97fb177c36a5347cecd5"
    ),
}
SOURCE_COUNTS = {
    "euler_criterion_bounded_candidate": 1,
    "gauss_lemma_bounded_candidate": 1,
    "quadratic_supplement_minus_one_candidate": 6,
    "quadratic_supplement_two_candidate": 20,
    "fermat_two_squares_candidate": 11,
    "fermat_two_squares_classification_candidate": 10,
    "fermat_two_squares_collision_norm_candidate": 12,
    "fermat_two_squares_factor_fold_candidate": 1,
    "fermat_two_squares_pairing_candidate": 17,
    "fermat_two_squares_pigeonhole_candidate": 8,
    "fermat_two_squares_prime_candidate": 9,
    "fermat_two_squares_residue_grid_candidate": 7,
    "fermat_two_squares_valuation_candidate": 13,
    "finite_prefix_collision_decision_candidate": 1,
}


@lru_cache(maxsize=1)
def _enrollment():
    return enrollment_module.alpha_v15_enrollment()


@lru_cache(maxsize=1)
def _parent_by_name():
    return {entry.spec.name: entry for entry in v14.ALPHA_ENTRIES}


@lru_cache(maxsize=1)
def _frontier_by_name():
    return {spec.name: spec for spec in _enrollment().frontier_specs}


def _closure(roots: tuple[str, ...]) -> set[str]:
    parent = _parent_by_name()
    frontier = _frontier_by_name()
    result: set[str] = set()

    def visit(name: str) -> None:
        if name in parent or name in result:
            return
        assert name in frontier, f"missing actual Alpha-v15 dependency {name!r}"
        result.add(name)
        for dependency in frontier[name].dependencies:
            visit(dependency)

    for root in roots:
        visit(root)
    return result


def _compact(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def test_v15_immutable_parent_and_stable_authority() -> None:
    assert len(v14.ALPHA_ENTRIES) == 1_556
    assert len(v15.ALPHA_ENTRIES) == 1_673
    assert _enrollment().parent_entries is v14.ALPHA_ENTRIES
    assert all(
        new is old
        for new, old in zip(v15.ALPHA_ENTRIES[:1_556], v14.ALPHA_ENTRIES, strict=True)
    )
    assert v15.STABLE_EDITION is v14.STABLE_EDITION
    assert v15.STABLE_SPECS is v14.STABLE_SPECS
    assert len(v15.STABLE_SPECS) == 432
    assert v15.ALPHA_CHECKED_SPECS == v14.ALPHA_CHECKED_SPECS
    assert len(v15.ALPHA_CHECKED_SPECS) == 570
    assert enrollment_module.PARENT_ALPHA_V14_ENROLLMENT_SHA256 == (
        v14.ALPHA_V14_ENROLLMENT_SHA256
    )
    assert enrollment_module.PARENT_ALPHA_V14_IDENTITY_SHA256 == (
        v14.ALPHA_V14_IDENTITY_SHA256
    )


def test_v15_exact_minimal_topological_closure_and_pinned_identities() -> None:
    rows = _enrollment().frontier_specs
    names = tuple(spec.name for spec in rows)
    assert len(rows) == 117
    assert names == enrollment_module.FRONTIER_V15_EXPECTED_NAMES
    assert sha256(_compact(names).encode("utf-8")).hexdigest() == (
        "0f351efe479507534d2cf8cca1b9bb82fe1a7eb6149a3c06224f0e9b42f93318"
    )
    assert sha256("\n".join(sorted(names)).encode("utf-8")).hexdigest() == (
        "32756c7da2db95fcb2948d53f79b74b0c22830b3bd3d5cb284228edfe7f54dbb"
    )
    assert len(_enrollment().supplementary_specs) == 28
    assert len(_enrollment().two_square_specs) == 89
    assert rows[6].name == "quadratic_supplement_minus_one_complete"
    assert rows[27].name == "quadratic_supplement_two_complete"
    assert rows[-1].name == (
        "two_square_iff_zero_or_even_three_mod_four_prime_valuations"
    )
    available = set(_parent_by_name())
    for spec in rows:
        assert set(spec.dependencies) <= available
        available.add(spec.name)
    assert sum(len(spec.dependencies) for spec in rows) == 364
    assert v15.ALPHA_EDITION.edge_count == 5_615
    assert v15.ALPHA_EDITION.layer_count == 53
    assert v15.ALPHA_V15_ENROLLMENT_SHA256 == (
        "44be61cdff1a093a78684a9d001d61d2b3761e73bacf6e79fe1a456f4ce50175"
    )
    assert v15.ALPHA_V15_IDENTITY_SHA256 == (
        "2f1a097ac0b6821c74cd4da088c396d3b9960ffd43e169f22b4778d5871adc66"
    )


@pytest.mark.parametrize(
    ("roots", "expected"),
    (
        (("bounded_euler_criterion_complete",), 1),
        (("bounded_gauss_lemma_complete",), 2),
        (("quadratic_supplement_minus_one_complete",), 7),
        (("quadratic_supplement_two_complete",), 22),
        (
            (
                "quadratic_supplement_minus_one_complete",
                "quadratic_supplement_two_complete",
            ),
            28,
        ),
        (("two_square_iff_zero_or_even_three_mod_four_prime_valuations",), 95),
        (enrollment_module.FRONTIER_V15_ROOT_NAMES, 117),
    ),
)
def test_v15_each_root_has_exact_minimal_dependency_closure(
    roots: tuple[str, ...], expected: int
) -> None:
    assert len(_closure(roots)) == expected


def test_v15_authentic_euler_and_gauss_prerequisites_are_enrolled() -> None:
    rows = _frontier_by_name()
    assert "bounded_euler_criterion_complete" not in _parent_by_name()
    assert "bounded_gauss_lemma_complete" not in _parent_by_name()
    euler = rows["bounded_euler_criterion_complete"]
    gauss = rows["bounded_gauss_lemma_complete"]
    euler_factory = import_module("peano_lab.library.euler_criterion_bounded_candidate")
    gauss_factory = import_module("peano_lab.library.gauss_lemma_bounded_candidate")
    actual_euler = next(
        spec
        for spec in euler_factory.make_euler_criterion_bounded_candidate_theorems(
            type(euler)
        )
        if spec.name == euler.name
    )
    actual_gauss = next(
        spec
        for spec in gauss_factory.make_gauss_lemma_bounded_candidate_theorems(
            type(gauss)
        )
        if spec.name == gauss.name
    )
    assert euler == actual_euler
    assert gauss == actual_gauss
    assert euler.name in gauss.dependencies
    assert set(euler.dependencies) <= set(_parent_by_name())


def test_v15_source_inventory_and_research_bindings_exist() -> None:
    manifest = enrollment_module.FRONTIER_V15_BODY_ENROLLMENT_MANIFEST
    assert len(manifest) == 14
    assert {source.module: len(source.names) for source in manifest} == SOURCE_COUNTS
    assert sum(len(source.names) for source in manifest) == 117
    for source in manifest:
        assert (REPOSITORY / source.test_path).is_file()
        assert (REPOSITORY / source.rfc_path).is_file()
        assert (REPOSITORY / "peano-lab/py/peano_lab/library" / f"{source.module}.py").is_file()


def test_v15_evidence_partition_does_not_promote_any_theorem() -> None:
    assert Counter(entry.evidence.value for entry in v15.ALPHA_ENTRIES) == {
        "stable_closed": 432,
        "alpha_closed": 138,
        "body_checked": 1_102,
        "pending_layered_closure": 1,
    }
    assert Counter(entry.membership.value for entry in v15.ALPHA_ENTRIES) == {
        "stable": 432,
        "alpha_only": 1_241,
    }
    for entry in v15.ALPHA_ENTRIES[1_556:]:
        assert entry.evidence is v15.EvidenceStatus.BODY_CHECKED
        assert entry.membership is v15.Membership.ALPHA_ONLY
        assert entry.enrollment_origin is v15.EnrollmentOrigin.HA
        assert not entry.checked_use


@pytest.mark.parametrize("name", tuple(ROOT_HASHES))
def test_v15_root_statement_is_exact_and_checked_use_is_rejected(name: str) -> None:
    item = v15.entry(name, edition="alpha")
    assert item is not None
    assert sha256(item.spec.statement.encode("utf-8")).hexdigest() == ROOT_HASHES[name]
    assert not item.checked_use
    assert v15.entry(name, edition="stable") is None
    with pytest.raises(v15.EditionV15ReplayError, match="checked theorem use requires"):
        v15.replay(name, edition="alpha")


@pytest.mark.parametrize(
    "name", ("bounded_euler_criterion_complete", "bounded_gauss_lemma_complete")
)
def test_v15_hidden_prerequisite_body_replays_and_rejects_statement_mutation(
    name: str,
) -> None:
    core = {spec.name: spec for spec in v15.ALPHA_SPECS}
    spec = core[name]
    receipt, = replay_candidate_bodies((spec,), core=core)
    assert receipt.name == name
    assert receipt.proof_nodes > 0
    assert receipt.proof_objects > 0
    mutated = replace(spec, statement="forall n. n = S(n)")
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=core)


@pytest.mark.parametrize("name", tuple(ROOT_HASHES))
def test_v15_missing_root_dependency_cannot_be_silently_assumed(name: str) -> None:
    spec = _frontier_by_name()[name]
    assert spec.dependencies
    mutated = replace(spec, dependencies=spec.dependencies[1:])
    core = {item.name: item for item in v15.ALPHA_SPECS}
    with pytest.raises(CandidateBodyError):
        replay_candidate_bodies((mutated,), core=core)


@lru_cache(maxsize=1)
def _artifact_catalog() -> dict[str, object]:
    path = REPOSITORY / "artifacts/peano-library/alpha/catalog-v15.json"
    return json.loads(path.read_text(encoding="utf-8"))


def test_v15_artifacts_preserve_exact_parent_and_actual_body_receipts() -> None:
    parent_path = REPOSITORY / "artifacts/peano-library/alpha/catalog-v14.json"
    parent = json.loads(parent_path.read_text(encoding="utf-8"))
    catalog = _artifact_catalog()
    assert catalog["theorem_count"] == 1_673
    assert catalog["checked_use_count"] == 570
    assert catalog["stable_count"] == 432
    assert catalog["theorems"][:1_556] == parent["theorems"]
    rows = catalog["theorems"][1_556:]
    assert len(rows) == 117
    assert tuple(row["name"] for row in rows) == (
        enrollment_module.FRONTIER_V15_EXPECTED_NAMES
    )
    assert catalog["frontier_v15_campaign_counts"] == {
        "supplementary": 28,
        "two_square": 89,
    }
    for row in rows:
        receipt = row["body_receipt"]
        assert receipt["name"] == row["name"]
        assert receipt["status"] == "kernel_checked_dependency_curried_body"
        assert receipt["proof_nodes"] > 0
        assert receipt["proof_objects"] > 0
        assert receipt["dne_command_count"] == 0
        assert row["evidence_status"] == "body_checked"
        assert row["checked_use"] is False
        assert row["empty_context_closure"] is None
        assert len(row["evidence_links"]) == 4


def test_v15_channel_preserves_stable_pointer_and_default() -> None:
    path = REPOSITORY / "artifacts/peano-library/channels-v15.json"
    channels = json.loads(path.read_text(encoding="utf-8"))
    parent_path = REPOSITORY / "artifacts/peano-library/channels-v14.json"
    parent = json.loads(parent_path.read_text(encoding="utf-8"))
    assert channels["default_channel"] == "stable"
    assert channels["channels"]["stable"] == parent["channels"]["stable"]
    assert channels["channels"]["alpha"]["theorem_count"] == 1_673
    assert channels["channels"]["alpha"]["checked_use_count"] == 570
