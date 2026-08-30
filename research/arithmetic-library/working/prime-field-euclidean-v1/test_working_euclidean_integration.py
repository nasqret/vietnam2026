"""Source-only working integration guards, not simulated proof acceptance.

The actual four frozen factories are constructed and parsed, but this small
suite deliberately performs no current-Alpha import, bundle decode, kernel
replay, independent Lean call, proof-data write or registration mutation.
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

_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest
import working_euclidean_support as support
import export_working_euclidean as exporter
import check_working_euclidean as checker


HERE = Path(__file__).resolve().parent
EXPECTED_SPEC = "b9fef22dbce3893dfadb7c9c5192c7a5a3c8d717ae112a0fff9e016aa68162fb"
EXPECTED_FACTORIES = (
    ("prime_field_polynomial_convolution_triangular_candidate", 8),
    ("prime_field_polynomial_representation_candidate", 30),
    ("prime_field_polynomial_division_candidate", 25),
    ("prime_field_polynomial_distributivity_candidate", 18),
)
EXPECTED_ROOTS = (
    "prime_field_polynomial_division_execution_exists",
    "prime_field_polynomial_division_remainder_degree",
    "prime_field_polynomial_division_coefficient_identity",
    "prime_field_polynomial_trim_equivalent",
    "prime_field_polynomial_add_left_pad_transport",
    "prime_field_polynomial_left_distributive_products_exists",
    "prime_field_polynomial_right_distributive_products_exists",
    "prime_field_convolution_prefix_left_subtract",
)
FROZEN = (
    ("prime_field_polynomial_convolution_triangular_candidate.py", 16677,
     "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f"),
    ("prime_field_polynomial_representation_candidate.py", 42623,
     "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a"),
    ("prime_field_polynomial_division_candidate.py", 47986,
     "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2"),
    ("prime_field_polynomial_distributivity_candidate.py", 26118,
     "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86"),
    ("test_prime_field_polynomial_convolution_triangular_candidate.py", 9162,
     "e6bf4d2a0b2b00336b8d83b4ffe5d068e34e3d5bd44e8af4b995ca2723289822"),
    ("test_prime_field_polynomial_representation_candidate.py", 25517,
     "75a2cee90850ff07468b1d568ce4d3665f8006fdbb892c5838186abbc8fd57b7"),
    ("test_prime_field_polynomial_division_candidate.py", 23978,
     "c4f7555b19e88789c4a561ec5b66d1f9487f44a32b388f2beea90f9ec42eed3b"),
    ("test_prime_field_polynomial_distributivity_candidate.py", 21925,
     "d6200ef1e0447f3efb98461ce343a1a3ae5530f74490bd4b7782cbc13ed2e9a6"),
)


@pytest.fixture(scope="module")
def actual_state():
    state = support.load_candidate_state()
    yield state
    for name, size, digest in FROZEN:
        raw = (HERE / name).read_bytes()
        assert (len(raw), sha256(raw).hexdigest()) == (size, digest)


@pytest.mark.parametrize("name,size,digest", FROZEN, ids=[row[0] for row in FROZEN])
def test_eight_original_frozen_math_and_test_bytes_are_preserved(name, size, digest):
    raw = (HERE / name).read_bytes()
    assert (len(raw), sha256(raw).hexdigest()) == (size, digest)


def test_actual_81_factory_contract_and_local_topology(actual_state):
    assert tuple((owner.module, owner.count) for owner in support.FACTORIES) == EXPECTED_FACTORIES
    assert support.PRINCIPAL_ROOTS == EXPECTED_ROOTS
    assert len(actual_state.rows) == 81
    assert actual_state.specs_sha256 == EXPECTED_SPEC == support.NEW_SPECS_SHA256
    assert sum(len(row.dependencies) for row in actual_state.rows) == 259
    assert sum(len(row.script) for row in actual_state.rows) == 5279
    names = {row.name for row in actual_state.rows}
    assert len(names) == 81 and set(EXPECTED_ROOTS) <= names
    seen, external = set(), set()
    for row in actual_state.rows:
        assert (set(row.dependencies) & names) <= seen
        external.update(set(row.dependencies) - names)
        seen.add(row.name)
    assert len(external) == 84
    by_name = {row.name: row for row in actual_state.rows}
    assert "prime_field_convolution_coefficient_append" in by_name["prime_field_polynomial_constant_right_coefficient"].dependencies
    assert "prime_field_convolution_coefficient_append" in {
        dependency for row in actual_state.rows[38:63] for dependency in row.dependencies}


def test_working_factories_are_private_aliases_not_production_adoption(actual_state):
    for owner in support.FACTORIES:
        alias = "_working_euclidean_v1_" + owner.module
        module = sys.modules[alias]
        assert Path(module.__file__).resolve() == HERE / (owner.module + ".py")
        assert getattr(module, owner.factory).__module__ == alias
        installed = sys.modules.get("peano_lab.library." + owner.module)
        assert installed is not module


def test_local_metadata_explicitly_denies_every_proof_admission_and_global_novelty_claim():
    report = support.local_manifest()
    assert report["new_rows"] == 81 and report["syntax_only"] is True
    assert report["factory_counts"] == [list(pair) for pair in EXPECTED_FACTORIES]
    assert report["specs_sha256"] == EXPECTED_SPEC
    assert report["ordinary_principals"] == list(EXPECTED_ROOTS)
    assert len(report["maximal_working_roots"]) == 26
    for field in ("global_current_parent_novelty_checked", "whole_original_ha_checked",
                  "independent_lean_checked", "ordinary_principals_checked",
                  "alpha_admission_performed", "stable_admission_performed"):
        assert report[field] is False


@pytest.mark.parametrize("field", ("MATH_SOURCE_PINS", "MATH_TEST_PINS"))
@pytest.mark.parametrize("attack", ("missing", "reversed", "wrong_digest", "not_tuple"))
def test_missing_reordered_or_corrupt_frozen_inputs_fail_before_loading(field, attack, monkeypatch):
    pins = getattr(support, field)
    changed = {"missing": pins[:-1], "reversed": tuple(reversed(pins)),
               "wrong_digest": (replace(pins[0], sha256="0" * 64), *pins[1:]),
               "not_tuple": list(pins)}[attack]
    monkeypatch.setattr(support, field, changed)
    with pytest.raises((support.WorkingError, support.inherited.G009Error)):
        support.require_working_sources()


@pytest.mark.parametrize("attack", ("missing", "reversed", "wrong_digest", "not_tuple"))
def test_current_parent_runtime_sources_cannot_be_omitted_or_rebound(attack, monkeypatch):
    pins = support.PARENT_RUNTIME_PINS
    changed = {"missing": pins[:-1], "reversed": tuple(reversed(pins)),
               "wrong_digest": (replace(pins[0], sha256="0" * 64), *pins[1:]),
               "not_tuple": list(pins)}[attack]
    monkeypatch.setattr(support, "PARENT_RUNTIME_PINS", changed)
    with pytest.raises((support.WorkingError, support.inherited.G009Error)):
        support.require_parent_runtime()


@pytest.mark.parametrize("bad", (None, 0, 1, "yes", [], {}))
def test_final_selection_flag_is_a_strict_boolean(bad):
    with pytest.raises(support.WorkingError):
        support.load_candidate_state(final=bad)


@pytest.mark.parametrize("value", ("", None, "0" * 63, "G" * 64, b"a" * 64))
def test_unset_or_malformed_spec_registration_fails_closed(value, monkeypatch):
    monkeypatch.setattr(support, "NEW_SPECS_SHA256", value)
    monkeypatch.setattr(support, "PARENT_CATALOG_PINS", ())
    with pytest.raises(support.WorkingError, match="registered"):
        support.require_final_registration()


def test_missing_actual_current_catalogue_is_not_replaced_by_runtime_metadata(monkeypatch):
    monkeypatch.setattr(support, "PARENT_CATALOG_PINS", ())
    with pytest.raises(support.WorkingError, match="registered"):
        support.require_final_registration()


def test_actual_installed_parent_components_are_exact_bytes_without_alpha_import():
    assert tuple((pin.bytes, pin.sha256) for pin in support.PARENT_CATALOG_PINS) == (
        (603900, "41b9f387d88a5a4f0fe5ee2bd5578f37a27a4657b0a80f1a1a2cb5109f69a623"),
        (66503303, "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"),
        (34813857, "d7739760283864277399ff8c524c29cc6561b1a56763fd5c86768fc21499d1e6"),
    )
    before = {name for name in sys.modules if name.startswith("peano_lab.library.editions_v")}
    support.require_final_registration()
    assert {name for name in sys.modules if name.startswith("peano_lab.library.editions_v")} == before


def test_actual_registered_complete_artifact_identity_is_inert_not_proof_acceptance():
    before = {name for name in sys.modules if name.startswith("peano_lab.library.editions_v")}
    pin = checker.require_final_inventory()
    assert pin == checker.ArtifactPin(
        support.WORKING_RELATIVE + "/artifacts/working-prime-field-euclidean-proof-bundle-v1.json",
        1635441, "3614e9504b84cfd24a52780d54ddc9eb16e49bf2df996c99664c9427e9a9fd83",
        314, 822, 21794,
    )
    payload = support.bounded_bytes(support.ROOT / pin.path, pin.bytes)
    assert (len(payload), sha256(payload).hexdigest()) == (pin.bytes, pin.sha256)
    # JSON inventory only: do not decode bodies or simulate HA/Lean acceptance.
    value = json.loads(payload)
    assert type(value) is list and len(value) == 4 and value[0] == "peano-lab-bundle-v1"
    assert type(value[1]) is int and value[1] == 313
    assert len(value[3]) == 314 and value[2] == value[3][313][1]
    assert sum(len(node[2]) for node in value[3]) == 822
    assert {name for name in sys.modules if name.startswith("peano_lab.library.editions_v")} == before


@pytest.mark.parametrize("value", (None, {"passed": True}, object(), ()))
def test_stored_or_foreign_syntax_objects_are_not_source_bindings(value):
    with pytest.raises(support.WorkingError):
        support.state_binding(value)


@pytest.mark.parametrize("attack", ("missing_self_consistent", "altered_self_consistent",
                                   "digest", "sources", "list_rows"))
def test_only_exact_81_state_can_be_bound_before_any_parent_import(actual_state, attack):
    if attack == "missing_self_consistent":
        rows = actual_state.rows[:-1]
        changed = replace(actual_state, rows=rows, specs_sha256=support.closure._specs_digest(rows))
    elif attack == "altered_self_consistent":
        rows = (replace(actual_state.rows[0], summary="altered metadata"), *actual_state.rows[1:])
        changed = replace(actual_state, rows=rows, specs_sha256=support.closure._specs_digest(rows))
    elif attack == "digest":
        changed = replace(actual_state, specs_sha256="0" * 64)
    elif attack == "sources":
        changed = replace(actual_state, sources=tuple(reversed(actual_state.sources)))
    else:
        changed = replace(actual_state, rows=list(actual_state.rows))
    before = {name for name in sys.modules if name.startswith("peano_lab.library.editions_v")}
    with pytest.raises(support.WorkingError, match="syntax state"):
        support.state_binding(changed)
    assert {name for name in sys.modules if name.startswith("peano_lab.library.editions_v")} == before


@pytest.mark.parametrize("value", (None, {"accepted": True}, object()))
def test_missing_or_foreign_artifact_registration_is_a_hard_stop(value, monkeypatch):
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", value)
    with pytest.raises(support.WorkingError, match="artifact"):
        checker.require_final_inventory()


@pytest.mark.parametrize("field,value", (
    ("bytes", 0), ("bytes", True), ("nodes", -1), ("nodes", 1.0), ("edges", True),
    ("body_nodes", 0), ("sha256", "0" * 63), ("sha256", "z" * 64),
    ("path", "/private/tmp/foreign.json"),
    ("path", support.WORKING_RELATIVE + "/artifacts/../foreign.json"),
    ("path", "research/arithmetic-library/artifacts/foreign.json"),
))
def test_malformed_artifact_data_cannot_reach_a_proof_gate(field, value, monkeypatch):
    pin = checker.ArtifactPin(support.WORKING_RELATIVE + "/artifacts/not-a-proof.json",
                             1, "0" * 64, 1, 1, 1)
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", replace(pin, **{field: value}))
    with pytest.raises(support.WorkingError):
        checker.require_final_inventory()


@pytest.mark.parametrize("name", (None, "", "zero_add", "prime_field_polynomial_division_exists_with_remainder_bound", [], {}))
def test_only_eight_exact_principals_are_selectable(name):
    with pytest.raises(support.WorkingError, match="principal"):
        checker.verify_principal(name)


@pytest.mark.parametrize("value", (None, (), [], ("seed",), ("seed", None)))
def test_explicit_seed_authoring_rejects_missing_or_malformed_seeds(value):
    if value == ("seed",):
        # A well-typed path still cannot redirect a proof output out of the
        # working directory; this exits before importing current Alpha.
        output = support.ROOT / "research/arithmetic-library/artifacts/not-authorized.json"
    else:
        output = exporter.ARTIFACT_DIRECTORY / "never-written.json"
    with pytest.raises(support.WorkingError):
        exporter.export_authoring_bundle(("no_theorem",), output, seed_bundles=value)


@pytest.mark.parametrize("path", (
    "/private/tmp/foreign.json", "/proof.json",
    support.WORKING_RELATIVE + "/outside.json",
    support.WORKING_RELATIVE + "/artifacts/.hidden.json",
    support.WORKING_RELATIVE + "/artifacts/data.txt",
    support.WORKING_RELATIVE + "/artifacts/../foreign.json",
))
def test_proof_data_destination_is_one_exact_new_working_json_file(path):
    with pytest.raises(support.WorkingError):
        exporter._destination(path)


@pytest.mark.parametrize("payload", (b"", "", None, bytearray(b"x")))
def test_exclusive_writer_rejects_foreign_or_empty_payload_without_writing(payload):
    with pytest.raises(support.WorkingError):
        exporter._write_exclusive(exporter.ARTIFACT_DIRECTORY / "never-written.json", payload)


def test_original_checker_compiler_and_same_byte_lean_are_called_without_replacement():
    source = Path(checker.__file__).read_text()
    tree = ast.parse(source)
    functions = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
    bundle = ast.unparse(functions["verify_complete_bundle"])
    root = ast.unparse(functions["verify_principal"])
    assert "support.closure.check_bottom_layer_bundle(selected.frontier, bundle, target)" in bundle
    assert "independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)" in bundle
    assert "support.closure.replay_bottom_layer_theorem(selected.frontier, name, bundle, target)" in root
    assert "check((), proof.certificate, formula)" in root
    assert "_rebind(before)" in bundle and "_rebind(before)" in root
    assert "ordinary_principals_checked" in bundle and "False" in bundle
    metadata = ast.unparse(functions["global_metadata_report"])
    assert "'inherited_alpha_v32_names': list(selected.parent_support)" in metadata
    assert "direct_current_alpha_dependencies" not in metadata
    assert not any(isinstance(node, ast.Assign) and any(isinstance(target, ast.Attribute)
        and isinstance(target.value, ast.Name) and target.value.id in {"support", "independent"}
        for target in node.targets) for node in ast.walk(tree))


def test_original_resource_and_authoring_gates_are_explicit_and_not_raised():
    assert exporter.CPU_LIMITS == checker.CPU_LIMITS == (170, 175)
    assert exporter.WALL_SECONDS == checker.WALL_SECONDS == 180
    source = Path(exporter.__file__).read_text()
    assert "batch_size=1" in source
    assert "os.O_EXCL" in source and "os.O_NOFOLLOW" in source
    assert source.index("result = support.closure.assemble_bottom_layer_bundle") < source.index("_write_exclusive(destination, payload)")
    assert source.count("authoring_rss_bytes()") >= 4
    assert "--through" not in Path(checker.__file__).read_text()
    assert "DEFAULT_BUNDLE_LIMITS.max_payload_bytes" in source


def test_cold_local_diagnostic_uses_actual_factories_without_importing_alpha():
    code = """import json, pathlib, sys
sys.path.insert(0, sys.argv[1])
import working_euclidean_support as support
report = support.local_manifest()
assert not any(name.startswith('peano_lab.library.editions_v') for name in sys.modules)
assert report['new_rows'] == 81
assert report['whole_original_ha_checked'] is False
print(json.dumps({'count': 81, 'sha': report['specs_sha256'], 'alpha_loaded': False}))
"""
    completed = subprocess.run([sys.executable, "-I", "-B", "-c", code, str(HERE)],
                               capture_output=True, text=True, timeout=15, check=True)
    assert json.loads(completed.stdout) == {"count": 81, "sha": EXPECTED_SPEC, "alpha_loaded": False}
    assert completed.stderr == ""


class _Accounting:
    def __init__(self):
        self.ids, self.calls, self.bad = (), [], []

    def pytest_collection_modifyitems(self, items):
        self.ids = tuple(item.nodeid for item in items)
        if len(self.ids) != len(set(self.ids)):
            raise pytest.UsageError("duplicate working integration case IDs")

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
