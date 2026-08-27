"""Exact additive, fail-closed, original-kernel Alpha-v27 admission audits."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import subprocess

import pytest

from peano_lab.library import editions_v26 as parent
from peano_lab.library import editions_v27 as current
from peano_lab.library import alpha_enrollment_v27 as enrollment_module
from peano_lab.library.alpha_enrollment_v27 import (
    EXPECTED_CAMPAIGN_COUNTS,
    FRONTIER_V27_EXPECTED_COUNT,
    FRONTIER_V27_EXPECTED_EDGE_COUNT,
    FRONTIER_V27_EXPECTED_NAMES_SHA256,
    PARENT_ALPHA_V26_COUNT,
    PARENT_ALPHA_V26_ENROLLMENT_SHA256,
    PARENT_ALPHA_V26_IDENTITY_SHA256,
    ROOT_STATEMENT_SHA256,
    alpha_v27_enrollment,
)
from peano_lab.library import campaign_second_wave_closure as closure


REPOSITORY = Path(__file__).resolve().parents[3]
ARTIFACT = (
    REPOSITORY / "research/arithmetic-library/artifacts" / current.SECOND_WAVE_ARTIFACT_FILENAME
)


def test_immutable_alpha_v26_parent_and_stable_are_preserved() -> None:
    assert len(parent.ALPHA_ENTRIES) == PARENT_ALPHA_V26_COUNT == 2_138
    assert parent.ALPHA_V26_ENROLLMENT_SHA256 == PARENT_ALPHA_V26_ENROLLMENT_SHA256
    assert parent.ALPHA_V26_IDENTITY_SHA256 == PARENT_ALPHA_V26_IDENTITY_SHA256
    assert current.ALPHA_ENTRIES[:PARENT_ALPHA_V26_COUNT] == parent.ALPHA_ENTRIES
    assert all(
        newer is older
        for newer, older in zip(current.ALPHA_ENTRIES, parent.ALPHA_ENTRIES, strict=False)
    )
    assert current.STABLE_EDITION is parent.STABLE_EDITION
    assert len(current.STABLE_SPECS) == 432


def test_frozen_frontier_is_nonempty_dependency_ordered_and_checked() -> None:
    enrollment = alpha_v27_enrollment()
    assert FRONTIER_V27_EXPECTED_COUNT > 0
    assert len(enrollment.frontier_specs) == FRONTIER_V27_EXPECTED_COUNT
    assert all(count > 0 for count in EXPECTED_CAMPAIGN_COUNTS.values())
    assert Counter(enrollment.campaign_by_name.values()) == EXPECTED_CAMPAIGN_COUNTS
    assert sum(len(row.dependencies) for row in enrollment.frontier_specs) == (
        FRONTIER_V27_EXPECTED_EDGE_COUNT
    )
    assert sha256("\n".join(row.name for row in enrollment.frontier_specs).encode()).hexdigest() == (
        FRONTIER_V27_EXPECTED_NAMES_SHA256
    )
    available = {row.spec.name for row in parent.ALPHA_ENTRIES}
    for row in enrollment.frontier_specs:
        assert row.name not in available
        assert set(row.dependencies) <= available
        assert row.script
        assert current.ALPHA_EDITION.by_name[row.name].checked_use
        available.add(row.name)


@pytest.mark.parametrize("name,expected", ROOT_STATEMENT_SHA256.items())
def test_frozen_root_statement_is_exact(name: str, expected: str) -> None:
    row = current.ALPHA_EDITION.by_name[name]
    assert row.checked_use
    assert sha256(row.spec.statement.encode()).hexdigest() == expected


def test_full_edition_seals_and_immutable_quadratic_corpus() -> None:
    assert len(current.ALPHA_ENTRIES) == current.EXPECTED_ALPHA_V27_COUNT
    assert len(current.ALPHA_CHECKED_SPECS) == current.EXPECTED_ALPHA_V27_CHECKED_USE_COUNT
    assert current.ALPHA_EDITION.edge_count == current.EXPECTED_ALPHA_V27_EDGE_COUNT
    assert current.ALPHA_EDITION.layer_count == current.EXPECTED_ALPHA_V27_LAYER_COUNT
    assert current.ALPHA_V27_ENROLLMENT_SHA256 == current.EXPECTED_ALPHA_V27_ENROLLMENT_SHA256
    assert current.ALPHA_V27_IDENTITY_SHA256 == current.EXPECTED_ALPHA_V27_IDENTITY_SHA256
    corpus = REPOSITORY / "book/_static/pa-proof-explorer/api/corpus.json"
    assert sha256(corpus.read_bytes()).hexdigest() == (
        "ebc78a0c16fe6e9123a52363a69929590d8ca875380431776ef0de28b9b1193a"
    )


def test_exact_self_contained_artifact_passes_independent_lean() -> None:
    payload = ARTIFACT.read_bytes()
    assert len(payload) == closure.EXPECTED_SECOND_WAVE_BUNDLE_BYTES > 0
    assert sha256(payload).hexdigest() == closure.EXPECTED_SECOND_WAVE_BUNDLE_SHA256
    verifier = REPOSITORY.parent / "peano-lab-lean/.lake/build/bin/peano_lab_bundle_verify"
    result = subprocess.run(
        [str(verifier), str(ARTIFACT)],
        cwd=REPOSITORY,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0
    assert result.stdout.startswith("ACCEPT\t")
    assert f"nodes={closure.EXPECTED_SECOND_WAVE_BUNDLE_NODE_COUNT}" in result.stdout


def test_new_alpha_theorems_never_leak_into_stable() -> None:
    stable_names = {row.name for row in current.STABLE_SPECS}
    assert stable_names.isdisjoint(current.FRONTIER_NEW_NAMES)
    for name in current.FRONTIER_NEW_NAMES:
        assert current.entry(name, edition="stable") is None

@pytest.fixture(autouse=True)
def _clear_second_wave_sources():
    current.set_second_wave_bundle_source(None)
    yield
    current.set_second_wave_bundle_source(None)


def test_exact_second_wave_bundle_authenticates_each_current_frontier_row() -> None:
    bundle, receipt, positions = current.checked_second_wave_bundle()
    assert set(current.FRONTIER_NEW_NAMES) <= positions.keys()
    assert receipt.node_count == len(bundle.nodes)
    assert receipt.kernel_calls == len(bundle.nodes)
    from peano_lab.library.theorems import _closed_formula
    for name in current.FRONTIER_NEW_NAMES:
        row = current.entry(name, edition="alpha")
        assert row is not None and row.checked_use
        node = bundle.nodes[positions[name]]
        assert node.target == _closed_formula(row.spec.statement)
        assert node.dependencies == tuple(positions[dependency] for dependency in row.spec.dependencies)


def test_missing_second_wave_artifact_fails_closed(tmp_path: Path) -> None:
    current.set_second_wave_bundle_source(tmp_path / "missing.json")
    with pytest.raises(current.EditionV27ReplayError, match="unavailable"):
        current.checked_second_wave_bundle()


@pytest.mark.parametrize("mutation", ("truncate", "alter"))
def test_changed_second_wave_artifact_fails_before_kernel_use(tmp_path: Path, mutation: str) -> None:
    payload = ARTIFACT.read_bytes()
    corrupted = payload[:-1] if mutation == "truncate" else bytes([payload[0] ^ 1]) + payload[1:]
    source = tmp_path / "changed.json"
    source.write_bytes(corrupted)
    current.set_second_wave_bundle_source(source)
    with pytest.raises(current.EditionV27ReplayError, match="frozen provenance"):
        current.checked_second_wave_bundle()


@pytest.mark.parametrize("source", (0, object(), b"artifact.json"))
def test_nonpath_artifact_source_is_rejected(source: object) -> None:
    with pytest.raises(current.EditionV27ReplayError, match="filesystem path"):
        current.set_second_wave_bundle_source(source)


def test_unsealed_proof_metadata_never_authorizes_checked_use(monkeypatch) -> None:
    from types import SimpleNamespace
    monkeypatch.setattr(current, "_second_wave_module", lambda: SimpleNamespace(
        EXPECTED_SECOND_WAVE_BUNDLE_BYTES=0,
        EXPECTED_SECOND_WAVE_BUNDLE_SHA256="",
        EXPECTED_SECOND_WAVE_BUNDLE_BODY_PROOF_NODES=0,
    ))
    with pytest.raises(current.EditionV27ReplayError, match="frozen provenance"):
        current.checked_second_wave_bundle()


def test_inherited_replay_still_delegates_to_the_immutable_parent(monkeypatch) -> None:
    sentinel = object()
    calls = []
    def inherited(name, *, edition):
        calls.append((name, edition))
        return sentinel
    monkeypatch.setattr(parent, "replay", inherited)
    assert current.replay("zero_add", edition="stable") is sentinel
    assert calls == [("zero_add", current.EditionName.STABLE)]


def test_new_classification_cannot_be_replayed_with_stable_authority() -> None:
    with pytest.raises(current.EditionV27ReplayError, match="unknown stable"):
        current.replay("integer_polynomial_prime_simple_root_lifts_all_positive_powers", edition="stable")


def test_unsealed_edition_metadata_never_authorizes_checked_use(monkeypatch) -> None:
    monkeypatch.setattr(current, "EXPECTED_ALPHA_V27_COUNT", 0)
    with pytest.raises(current.EditionV27ReplayError, match="not sealed"):
        current.checked_second_wave_bundle()


def test_second_wave_browser_runtime_needs_no_repository_catalogue(monkeypatch) -> None:
    def missing_catalogue():
        pytest.fail("the browser replay tried to load a repository catalogue")
    closure.second_wave_plan.cache_clear()
    monkeypatch.setattr(closure, "parent_snapshot", missing_catalogue)
    bundle, receipt, positions = current.checked_second_wave_bundle()
    assert receipt.kernel_calls == len(bundle.nodes)
    assert set(current.FRONTIER_NEW_NAMES) <= positions.keys()


def test_short_browser_layout_reports_missing_proof_not_a_path_index_error(monkeypatch) -> None:
    monkeypatch.setattr(current, "__file__", "/lab/peano_lab/library/editions_v27.py")
    monkeypatch.setattr(Path, "is_file", lambda _path: False)
    assert current._default_second_wave_bundle_source() == Path(
        current.PYODIDE_SECOND_WAVE_BUNDLE_PATH
    )


def test_provider_cold_import_in_the_actual_browser_layout_is_catalogue_free(monkeypatch) -> None:
    import importlib.util
    import sys
    source = Path(closure.__file__).read_text(encoding="utf-8")
    module_name = "peano_lab.library._second_wave_browser_probe"
    spec = importlib.util.spec_from_file_location(module_name, closure.__file__)
    assert spec is not None
    probe = importlib.util.module_from_spec(spec)
    probe.__file__ = "/lab/peano_lab/library/campaign_second_wave_closure.py"
    monkeypatch.setitem(sys.modules, module_name, probe)
    exec(compile(source, probe.__file__, "exec"), probe.__dict__)
    assert probe.ROOT == Path("/lab")
    def unavailable_catalogue():
        pytest.fail("cold browser import/read requested a repository catalogue")
    monkeypatch.setattr(probe, "parent_snapshot", unavailable_catalogue)
    plan = probe.second_wave_plan(parent_specs=parent.ALPHA_CHECKED_SPECS)
    assert plan.frontier_names == current.FRONTIER_NEW_NAMES
    assert len(plan.rows) >= len(current.FRONTIER_NEW_NAMES)


def test_supplied_parent_specs_equal_the_pinned_standalone_catalogue() -> None:
    assert closure._specs_digest(parent.ALPHA_CHECKED_SPECS) == closure.PARENT_SPECS_SHA256
    runtime_plan = closure.second_wave_plan(parent_specs=parent.ALPHA_CHECKED_SPECS)
    standalone_plan = closure.second_wave_plan()
    assert runtime_plan == standalone_plan


@pytest.mark.parametrize("field", ("statement", "summary", "script", "dependencies"))
def test_runtime_parent_authentication_rejects_rewritten_spec_fields(field: str) -> None:
    from dataclasses import replace
    changed = list(parent.ALPHA_CHECKED_SPECS)
    old = changed[-1]
    value = {
        "statement": "forall x. x = x",
        "summary": old.summary + " forged",
        "script": (*old.script, "refl"),
        "dependencies": old.dependencies[:-1],
    }[field]
    changed[-1] = replace(old, **{field: value})
    closure.second_wave_plan.cache_clear()
    with pytest.raises(closure.SecondWaveError, match="immutable v26 specifications"):
        closure.second_wave_plan(parent_specs=tuple(changed))


def test_new_alpha_root_replays_as_an_actual_closed_kernel_proof() -> None:
    from peano_lab.kernel.checker import check
    result = current.replay("hensel_prime_signed_nonzero_derivative_is_unit", edition="alpha")
    assert result.spec.name == "hensel_prime_signed_nonzero_derivative_is_unit"
    assert check((), result.certificate, result.formula)


@pytest.fixture
def fresh_enrollment():
    enrollment_module.alpha_v27_enrollment.cache_clear()
    yield enrollment_module
    enrollment_module.alpha_v27_enrollment.cache_clear()


def test_factory_order_is_reviewed_not_inferred(fresh_enrollment, monkeypatch) -> None:
    monkeypatch.setattr(
        fresh_enrollment, "FACTORIES", tuple(reversed(fresh_enrollment.FACTORIES))
    )
    with pytest.raises(fresh_enrollment.AlphaV27EnrollmentError, match="inventory or order"):
        fresh_enrollment.alpha_v27_enrollment()


@pytest.mark.parametrize(
    "field,value",
    (("factory", "invented"), ("rfc", "../historical-rfc-v1.md"),
     ("rfc", "arbitrary.txt"), ("campaign", "invented")),
)
def test_factory_provenance_metadata_is_not_implicit(
    fresh_enrollment, monkeypatch, field: str, value: str
) -> None:
    from dataclasses import replace
    factories = list(fresh_enrollment.FACTORIES)
    factories[0] = replace(factories[0], **{field: value})
    monkeypatch.setattr(fresh_enrollment, "FACTORIES", tuple(factories))
    with pytest.raises(
        fresh_enrollment.AlphaV27EnrollmentError, match="factory metadata|unavailable reviewed"
    ):
        fresh_enrollment.alpha_v27_enrollment()


@pytest.mark.parametrize(
    "mutation", ("classical", "implicit_use", "duplicate", "unknown_dependency", "empty", "extra")
)
def test_changed_candidate_inventory_or_constructive_script_fails_enrollment(
    fresh_enrollment, monkeypatch, mutation: str
) -> None:
    from dataclasses import replace
    from types import SimpleNamespace
    owner = fresh_enrollment.FACTORIES[0]
    original_import = fresh_enrollment.import_module
    module = original_import(f".{owner.module}", package=fresh_enrollment.__package__)
    from peano_lab.library.theorems import TheoremSpec
    candidates = list(getattr(module, owner.factory)(TheoremSpec))
    if mutation == "empty":
        candidates.clear()
    elif mutation == "extra":
        candidates.append(candidates[-1])
    else:
        fields = {
            "classical": {"script": ("DNE",)},
            "implicit_use": {"script": ("use zero_add",)},
            "duplicate": {"name": "zero_add"},
            "unknown_dependency": {"dependencies": ("unproved_boundary",)},
        }[mutation]
        candidates[0] = replace(candidates[0], **fields)
    fake_module = SimpleNamespace(**{owner.factory: lambda _spec: tuple(candidates)})
    def imported(name, *, package):
        return fake_module if name == f".{owner.module}" else original_import(name, package=package)
    monkeypatch.setattr(fresh_enrollment, "import_module", imported)
    with pytest.raises(fresh_enrollment.AlphaV27EnrollmentError):
        fresh_enrollment.alpha_v27_enrollment()


def test_every_reviewed_factory_has_local_source_test_and_rfc() -> None:
    enrollment = alpha_v27_enrollment()
    for paths in (
        enrollment.source_by_name, enrollment.test_by_name, enrollment.rfc_by_name
    ):
        for path in set(paths.values()):
            assert (REPOSITORY / path).is_file(), path
