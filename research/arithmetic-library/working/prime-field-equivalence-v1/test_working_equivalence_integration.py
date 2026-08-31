"""Focused changed-boundary guards; no proof mocks or Alpha import.

Real old source syntax and byte pins are used. Deliberately malformed
registrations and pure role fixtures can only exercise rejection/formatting;
they are never accepted as HA, Lean, or live proof evidence.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time
from types import ModuleType, SimpleNamespace

_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest
import working_equivalence_support as support
import export_working_equivalence as exporter
import check_working_equivalence as checker


HERE = Path(__file__).resolve().parent
EXPECTED_PRESERVATION_SHA256 = "8c5d3190f0da93e8925205ea56fcbb3f24efd20d65ef9de3dc349f93b6d8969b"
EXPECTED_ROOTS = (
    "prime_field_polynomial_equivalent_implies_left_pad",
    "prime_field_polynomial_add_equivalent_congruent",
    "prime_field_polynomial_subtract_equivalent_congruent",
    "prime_field_polynomial_convolution_equivalent_congruent",
)
EXPECTED_FACTORIES = (
    ("prime_field_polynomial_equivalence_candidate", 5, 10469,
     "929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373",
     19312, "778a8c9dcd43d5bed00125f176ac013a6aabfa4ae132a3ca16ba2bae2875b0dc",
     "2fe70cc2ff26a6938768fcbdb661c84b2ad17e19dd7d9551689f3f4ea39da273"),
    ("prime_field_polynomial_convolution_congruence_candidate", 3, 8183,
     "effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70",
     19162, "224e7d441f17217616a34e9e6fe85d321ba8c1ba410675cbacf56c34b6f7c4b8",
     "b0da9dd22a52c42045fd22ac189fb9d7fc92365527818f5a61e0f4a71d1be7e6"),
)


def _alpha_modules():
    return {name for name in sys.modules if name.startswith("peano_lab.library.editions_v")}


@pytest.fixture(scope="module")
def actual_state():
    before = _alpha_modules()
    state = support.load_candidate_state()
    assert _alpha_modules() == before
    yield state
    support.require_preserved_tree()
    support.require_source_registration()
    assert _alpha_modules() == before


@pytest.mark.parametrize("index,which", ((0, "source"), (0, "test"), (1, "source"), (1, "test")))
def test_actual_four_new_source_and_test_freezes(index, which):
    owner = support.FACTORIES[index]
    assert owner == support.Factory(*EXPECTED_FACTORIES[index])
    pin = getattr(owner, which)
    raw = support.bounded_bytes(support.ROOT / pin.path, pin.bytes)
    assert (len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256)


def test_actual121_syntax_preserves_prior113_objects_and_exact_new_order(actual_state):
    assert support.REGISTERED_COUNTS == (5, 3)
    assert len(actual_state.rows) == 121 and len(actual_state.added_rows) == 8
    assert all(first is second for first, second in
               zip(actual_state.rows[:113], actual_state.prior_state.rows, strict=True))
    records = [[row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
               for row in actual_state.rows]
    encoded = "".join(json.dumps(row, ensure_ascii=True, separators=(",", ":")) + "\n" for row in records).encode()
    assert sha256(encoded).hexdigest() == actual_state.specs_sha256 == support.COMBINED_SPECS_SHA256
    names, seen = {row.name for row in actual_state.rows}, set()
    for row in actual_state.rows:
        assert set(row.dependencies) & names <= seen
        seen.add(row.name)
    assert set(EXPECTED_ROOTS) <= {row.name for row in actual_state.added_rows}
    assert support.REPRESENTATION_ALIAS not in sys.modules


@pytest.mark.parametrize("attack", ("truncated", "reordered", "self_consistent_changed", "foreign_prior", "wrong_sources"))
def test_altered_actual_syntax_state_is_rejected_before_alpha(actual_state, attack):
    before = _alpha_modules()
    if attack == "truncated":
        changed = replace(actual_state, rows=actual_state.rows[:-1], added_rows=actual_state.added_rows[:-1])
    elif attack == "reordered":
        added = tuple(reversed(actual_state.added_rows))
        changed = replace(actual_state, rows=(*actual_state.prior_state.rows, *added), added_rows=added)
    elif attack == "self_consistent_changed":
        added = (replace(actual_state.added_rows[0], statement="false"), *actual_state.added_rows[1:])
        rows = (*actual_state.prior_state.rows, *added)
        changed = replace(actual_state, rows=rows, added_rows=added, specs_sha256=support.closure._specs_digest(rows))
    elif attack == "foreign_prior":
        changed = replace(actual_state, prior_state=SimpleNamespace(rows=actual_state.prior_state.rows))
    else:
        changed = replace(actual_state, added_sources=tuple(reversed(actual_state.added_sources)))
    with pytest.raises(ValueError):
        support.validate_state(changed)
    assert _alpha_modules() == before


@pytest.mark.parametrize("pin", support.PRESERVED_TREE_PINS,
                         ids=[pin.path.removeprefix(support.PRIOR_RELATIVE + "/")
                              for pin in support.PRESERVED_TREE_PINS])
def test_every_old_tracked_file_is_preserved_including_notes_and_deferred(pin):
    raw = support.bounded_bytes(support.ROOT / pin.path, pin.bytes)
    assert (len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256)


def test_complete43_tracked_inventory_has_an_independent_literal_identity():
    records = [[pin.path, pin.bytes, pin.sha256] for pin in support.PRESERVED_TREE_PINS]
    encoded = json.dumps(records, ensure_ascii=True, separators=(",", ":")).encode("utf-8")
    assert sha256(encoded).hexdigest() == EXPECTED_PRESERVATION_SHA256
    assert len(records) == 43 and sum(row[1] for row in records) == 5323159
    result = subprocess.run(["git", "ls-files", "--", support.PRIOR_RELATIVE],
                            cwd=support.ROOT, capture_output=True, text=True, timeout=10, check=True)
    assert result.stdout.splitlines() == [row[0] for row in records]
    assert result.stderr == ""
    names = {Path(row[0]).name for row in records}
    assert {"README.md", "DEFERRED_division_identity_converse.txt",
            "working-113-verification-observations-v1.json",
            "working-81-verification-observations-v1.json"} <= names


@pytest.mark.parametrize("attack", ("missing", "reversed", "list", "foreign", "bool_size", "wrong_sha", "old_artifact"))
def test_incomplete_or_changed_old_tree_registration_is_rejected(attack, monkeypatch):
    pins = support.PRESERVED_TREE_PINS
    if attack == "old_artifact":
        monkeypatch.setattr(support, "PRIOR113_ARTIFACT", pins[0])
    else:
        changed = {
            "missing": pins[:-1], "reversed": tuple(reversed(pins)), "list": list(pins),
            "foreign": (object(), *pins[1:]),
            "bool_size": (replace(pins[0], bytes=True), *pins[1:]),
            "wrong_sha": (replace(pins[0], sha256="0" * 64), *pins[1:]),
        }[attack]
        monkeypatch.setattr(support, "PRESERVED_TREE_PINS", changed)
    with pytest.raises(ValueError):
        support.require_preserved_tree()


@pytest.mark.parametrize("value", ("foreign_helper", None, 1))
def test_only_two_exact_old_integration_helpers_are_loadable(value):
    with pytest.raises(support.EquivalenceError, match="two exact"):
        support._preserved_helper(value)


def test_foreign_old_helper_module_is_not_overwritten(monkeypatch):
    name = "working_euclidean_support"
    foreign = ModuleType(name)
    foreign.__file__ = "/private/tmp/not-the-old-source.py"
    monkeypatch.setitem(sys.modules, name, foreign)
    with pytest.raises(support.EquivalenceError, match="foreign module"):
        support._preserved_helper(name)
    assert sys.modules[name] is foreign


def test_actual_prior113_syntax_is_loaded_without_alpha_or_math_alias_leaks():
    before = _alpha_modules()
    state = support.load_prior_state()
    assert len(state.rows) == 113
    assert state.specs_sha256 == "aac561ef7706c53af00464feba7d0f4a51a3e3960404dba4a53d80405913b8a9"
    assert len(state.prior_state.rows) == 81 and len(state.added_rows) == 32
    assert all(first is second for first, second in zip(state.rows[:81], state.prior_state.rows, strict=True))
    assert support.REPRESENTATION_ALIAS not in sys.modules
    assert _alpha_modules() == before


@pytest.mark.parametrize("kind", ("prior", "new", "alpha", "foreign"))
def test_pure_role_mapping_does_not_reclassify_prior113_as_alpha(kind):
    # This data-only fixture never enters state binding or any proof API.
    value = support.SupportSelection(SimpleNamespace(parent_support=("zero_add",)), ("prior",), ("new",))
    if kind == "foreign":
        with pytest.raises(support.EquivalenceError):
            value.role("outside")
    else:
        name, expected = {"prior": ("prior", "prior_non_admitted_working113"),
                          "new": ("new", "new_non_admitted_equivalence"),
                          "alpha": ("zero_add", "inherited_alpha_v32")}[kind]
        assert value.role(name) == expected


@pytest.mark.parametrize("counts", (None, (), [], (1,), (1, True), (1, 0), (1, -1), (1, 1.0)))
def test_missing_or_nonexact_final_counts_cannot_load_new_sources(counts, monkeypatch):
    monkeypatch.setattr(support, "REGISTERED_COUNTS", counts)
    before = _alpha_modules()
    with pytest.raises(support.EquivalenceError, match="registered"):
        support.require_source_registration()
    assert _alpha_modules() == before


@pytest.mark.parametrize("owners", ((), [], (object(), object())))
def test_unregistered_factories_cannot_mint_a_candidate_state(owners, monkeypatch):
    monkeypatch.setattr(support, "REGISTERED_COUNTS", (1, 1))
    monkeypatch.setattr(support, "FACTORIES", owners)
    with pytest.raises(support.EquivalenceError, match="registered"):
        support.load_candidate_state(require_spec_pin=False)


@pytest.mark.parametrize("value", (None, "", [], 1, "0" * 63, "Z" * 64))
def test_absent_or_malformed_combined_spec_identity_is_not_authority(value, monkeypatch):
    monkeypatch.setattr(support, "COMBINED_SPECS_SHA256", value)
    with pytest.raises(support.EquivalenceError, match="specification"):
        support._require_spec_pin()


@pytest.mark.parametrize("value", (None, 1, "yes"))
def test_diagnostic_spec_flag_must_be_an_explicit_boolean(value):
    with pytest.raises(support.EquivalenceError, match="Boolean"):
        support.load_candidate_state(require_spec_pin=value)


def test_real_absent_representation_alias_uses_exact_source_then_cleans_up():
    before = _alpha_modules()
    name = support.REPRESENTATION_ALIAS
    assert name not in sys.modules
    with support.temporary_representation_alias() as module:
        assert sys.modules[name] is module
        assert Path(module.__file__) == support.ROOT / support.REPRESENTATION_PIN.path
        assert callable(module.prime_field_polynomial_equivalent_relation)
    assert name not in sys.modules
    assert _alpha_modules() == before


@pytest.mark.parametrize("where", ("sys_modules", "package_attribute", "production_resolution"))
def test_existing_representation_alias_or_production_path_is_never_replaced(where, monkeypatch):
    import peano_lab.library as package
    marker = ModuleType("foreign_representation")
    name = support.REPRESENTATION_ALIAS
    if where == "sys_modules":
        monkeypatch.setitem(sys.modules, name, marker)
    elif where == "package_attribute":
        monkeypatch.setattr(package, name.rsplit(".", 1)[1], marker, raising=False)
    else:
        monkeypatch.setattr(support.importlib.util, "find_spec", lambda _name: object())
    with pytest.raises(support.EquivalenceError, match="cannot be replaced"):
        with support.temporary_representation_alias():
            raise AssertionError("a foreign alias reached source execution")
    if where == "sys_modules":
        assert sys.modules[name] is marker


def test_owned_alias_is_removed_on_a_body_exception():
    with pytest.raises(RuntimeError, match="intentional body stop"):
        with support.temporary_representation_alias():
            raise RuntimeError("intentional body stop")
    assert support.REPRESENTATION_ALIAS not in sys.modules


def test_foreign_alias_replacement_is_retained_but_rejected():
    name = support.REPRESENTATION_ALIAS
    foreign = ModuleType("foreign")
    try:
        with pytest.raises(support.EquivalenceError, match="was replaced"):
            with support.temporary_representation_alias():
                sys.modules[name] = foreign
        assert sys.modules[name] is foreign
    finally:
        if sys.modules.get(name) is foreign:
            del sys.modules[name]


@pytest.mark.parametrize("value", (None, {}, {"passed": True}, object(), ()))
def test_missing_or_foreign_final_artifact_never_reaches_proof_checks(value, monkeypatch):
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", value)
    before = _alpha_modules()
    with pytest.raises(support.EquivalenceError, match="registered"):
        checker.verify_complete_bundle()
    assert _alpha_modules() == before


def test_real_complete_artifact_registration_is_only_exact_pinned_data():
    before = _alpha_modules()
    pin = checker.require_final_inventory()
    assert pin == checker.ArtifactPin(
        support.WORKING_RELATIVE + "/artifacts/working-equivalence-proof-bundle-v1.json",
        2449379, "6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf",
        377, 1071, 30527)
    raw = support.bounded_bytes(support.ROOT / pin.path, pin.bytes)
    assert (len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256)
    assert pin.path != support.PRIOR113_ARTIFACT.path
    assert _alpha_modules() == before


@pytest.mark.parametrize("field,value", (
    ("bytes", True), ("nodes", 1.0), ("edges", 0), ("body_nodes", -1),
    ("sha256", "z" * 64), ("path", support.PRIOR113_ARTIFACT.path),
    ("path", "/private/tmp/foreign.json"),
))
def test_malformed_or_old_directory_artifact_pin_is_rejected(field, value, monkeypatch):
    pin = checker.ArtifactPin(support.WORKING_RELATIVE + "/artifacts/working-equivalence-not-a-proof.json",
                              1, "0" * 64, 1, 1, 1)
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", replace(pin, **{field: value}))
    with pytest.raises(support.EquivalenceError, match="registered"):
        checker.require_final_inventory()


def test_exact_four_principal_names_and_original_proof_interfaces_are_retained():
    assert support.PRINCIPAL_ROOTS == EXPECTED_ROOTS
    tree = ast.parse(Path(checker.__file__).read_text())
    functions = {node.name: ast.unparse(node) for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "support.closure.check_bottom_layer_bundle(selected.frontier, bundle, target)" in functions["verify_complete_bundle"]
    assert "independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)" in functions["verify_complete_bundle"]
    assert "support.closure.replay_bottom_layer_theorem(selected.frontier, name, bundle, target)" in functions["verify_principal"]
    assert "check((), proof.certificate, formula)" in functions["verify_principal"]
    assert "proof.spec != exact_spec" in functions["verify_principal"]
    assert "_rebind(before)" in functions["verify_principal"]
    assert "support.prior_base.statement_duplicates(state.rows)" in functions["global_metadata_report"]
    assert "len(selected.previous_working_names) != support.PRIOR_WORKING_COUNT" in functions["_load_final"]


def test_seed_coverage_uses_inert_exact_metadata_not_proof_acceptance():
    tree = ast.parse(Path(checker.__file__).read_text())
    functions = {node.name: ast.unparse(node) for node in tree.body if isinstance(node, ast.FunctionDef)}
    text = functions["_seed_coverage"]
    assert "json.loads(support._read(pin))" in text
    assert "encode_formula(_closed_formula(row.statement))" in text
    expected = ast.dump(ast.parse("tuple(encoded[edge] for edge in node[2])", mode="eval").body)
    body = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "_seed_coverage")
    assert any(ast.dump(node) == expected for node in ast.walk(body))
    assert "support.check_pin(pin" in text
    assert "decode_proof_bundle(" not in text and "check_proof_bundle(" not in text
    assert "_seed_coverage(selected, state)" in functions["global_metadata_report"]


@pytest.mark.parametrize("name", (None, "", [], 1, "prime_field_polynomial_division_execution_exists_unique"))
def test_only_the_new_four_ordinary_targets_can_be_selected(name):
    with pytest.raises(support.EquivalenceError, match="four exact"):
        checker.verify_principal(name)


@pytest.mark.parametrize("seeds", (None, (), [], (None,), ("same", "same")))
def test_malformed_explicit_seed_lists_stop_before_authoring(seeds):
    with pytest.raises(ValueError):
        exporter.export_authoring_bundle((EXPECTED_ROOTS[0],),
            HERE / "artifacts/working-equivalence-never-written.json", seed_bundles=seeds)


def test_actual_prior113_seed_must_be_explicit():
    # Empty/nonexistent arbitrary paths do not stand in for the real old seed.
    with pytest.raises(support.EquivalenceError, match="preserved113"):
        exporter.export_authoring_bundle((EXPECTED_ROOTS[0],),
            HERE / "artifacts/working-equivalence-never-written.json", seed_bundles=("/private/tmp/foreign.json",))


@pytest.mark.parametrize("path", (
    "/private/tmp/working-equivalence-foreign.json",
    support.PRIOR113_ARTIFACT.path,
    support.WORKING_RELATIVE + "/working-equivalence-wrong-directory.json",
    support.WORKING_RELATIVE + "/artifacts/other.json",
    support.WORKING_RELATIVE + "/artifacts/.hidden.json",
    support.WORKING_RELATIVE + "/artifacts/../working-equivalence-traversal.json",
))
def test_only_new_exact_owned_artifact_paths_are_permitted(path):
    with pytest.raises(ValueError):
        exporter.destination(path)


@pytest.mark.parametrize("payload", (None, "", b"", bytearray(b"x")))
def test_invalid_payload_cannot_create_any_output(payload):
    path = HERE / "artifacts/working-equivalence-never-written.json"
    with pytest.raises(support.EquivalenceError, match="payload limit"):
        exporter.write_exclusive(path, payload)
    assert not path.exists()


def test_new_destination_validation_itself_does_not_write():
    path = HERE / "artifacts/working-equivalence-never-written.json"
    assert not path.exists() and exporter.destination(path) == path
    assert not path.exists()


def test_original_resource_policy_and_new_exclusive_writer_are_exact():
    assert checker.CPU_LIMITS == exporter.CPU_LIMITS == (170, 175)
    assert checker.WALL_SECONDS == exporter.WALL_SECONDS == 180
    assert support.closure is support.prior.closure is support.prior_base.closure
    raw = Path(exporter.__file__).read_text()
    source = ast.unparse(ast.parse(raw))
    assert "0o600" in raw
    for text in ("os.O_EXCL", "os.O_NOFOLLOW", "os.O_DIRECTORY", "os.O_CLOEXEC"):
        assert text in source
    function = source[source.index("def export_authoring_bundle"):source.index("def main")]
    assert function.index("assemble_bottom_layer_bundle") < function.index("encode_proof_bundle") < function.index("write_exclusive")
    assert "batch_size=1" in function and "seed_bundles=seed_bundles" in function
    assert "support.state_binding(support.load_candidate_state()) != before" in function
    assert all("definitions" not in name and "README" not in name and "observations" not in name
               for name in support.CONTROL_FILES)


class _Accounting:
    def __init__(self):
        self.ids, self.calls, self.bad = (), [], []

    def pytest_collection_modifyitems(self, items):
        self.ids = tuple(item.nodeid for item in items)
        if len(self.ids) != len(set(self.ids)):
            raise pytest.UsageError("duplicate equivalence integration test IDs")

    def pytest_runtest_logreport(self, report):
        if report.failed or report.skipped or hasattr(report, "wasxfail"):
            self.bad.append(report.nodeid)
        if report.when == "call" and report.passed:
            self.calls.append(report.nodeid)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--expect", type=int)
    args, pytest_args = parser.parse_known_args(argv)
    account = _Accounting()
    status = int(pytest.main([str(Path(__file__)), *(pytest_args or ["-q"])], plugins=[account]))
    usage = resource.getrusage(resource.RUSAGE_SELF)
    rss = int(usage.ru_maxrss if sys.platform == "darwin" else usage.ru_maxrss * 1024)
    elapsed = time.monotonic() - _STARTED
    if (args.expect is not None and len(account.ids) != args.expect
            or "--collect-only" not in pytest_args and (account.calls != list(account.ids) or account.bad)
            or elapsed > 180 or rss > 1536 * 1024 * 1024
            or resource.getrlimit(resource.RLIMIT_CPU) != (170, 175)):
        status = 1
    print(json.dumps({"status": status, "unique_cases": len(account.ids),
        "node_ids_sha256": sha256("\n".join(sorted(account.ids)).encode()).hexdigest(),
        "seconds": elapsed, "cpu_seconds": usage.ru_utime + usage.ru_stime,
        "peak_rss_bytes": rss, "cpu_limits": [170, 175], "wall_alarm_seconds": 180}, sort_keys=True), flush=True)
    return status


if __name__ == "__main__":
    raise SystemExit(main())
