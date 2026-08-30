"""Actual source/alias guards for the separate working113 checkpoint.

These tests construct real frozen theorem syntax but do not import the full
Alpha edition, decode/check a proof body, run Lean, or simulate a successful
proof gate. Pure role fixtures have no authority and never enter proof APIs.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import replace
from hashlib import sha256
import importlib.util
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
import working_euclidean_extension_support as support
import export_working_euclidean_extension as exporter
import check_working_euclidean_extension as checker
from peano_lab.kernel.formulas import parse_formula_with_names


HERE = Path(__file__).resolve().parent
EXPECTED_SPEC = "aac561ef7706c53af00464feba7d0f4a51a3e3960404dba4a53d80405913b8a9"
EXPECTED_PRIOR_SPEC = "b9fef22dbce3893dfadb7c9c5192c7a5a3c8d717ae112a0fff9e016aa68162fb"
EXPECTED_ROOTS = (
    "prime_field_polynomial_division_execution_functional",
    "prime_field_polynomial_division_execution_exists_unique",
    "prime_field_polynomial_convolution_both_left_paddings_equivalent",
    "prime_field_polynomial_convolution_both_left_paddings_exists",
)
EXPECTED_ADDED = (
    ("prime_field_polynomial_division_uniqueness_candidate", 9, 23258,
     "6a9d9ebe1f72202743e5df2c069b9aa367fdb3d61108f1d9354cdc9276ab2d15",
     15599, "b74083e6707eb83e7fab3efa3f610d562edf2168511b07c5995f9ef9f7f588e2",
     "41bb0ad58b6e7ef3cc6fefba62bcc75ae0fe18a10fb87019905cb43e810ae1da"),
    ("prime_field_polynomial_convolution_padding_candidate", 23, 39740,
     "2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007",
     27054, "7632654e36e18cf7c872bd29dd783a55cf597e33e7b5369be178a2d2f42b87f9",
     "5bd7b23cf69bfd35fbf99c47da09a0751c3e267b8cdc31a078b2b65b99f5d619"),
)
EXPECTED_PRESERVED = (
    ("working_euclidean_support.py", 18552, "80e73f977f2464e2f62939610667def8bbf96f19e4d95bf734c52969c39cec4a"),
    ("export_working_euclidean.py", 7319, "5b5ff76c08c01240baa239ca189ad3a372f5d6e7777a0aa9b12eaf88a37b19de"),
    ("check_working_euclidean.py", 9619, "390033da96271b2347a99d5fe5f033d1c6c60f0b82496a1707df6260de353603"),
    ("test_working_euclidean_integration.py", 18658, "04f66780d6b0d7408b72b8e9a8cdc54772d1593e03dfb2e61579a44410ba1038"),
    ("working-euclidean-integration-rfc-v1.md", 9958, "f39c915949e5ca9312553836e7672c4c1b07bffb8b6d8a4efe3d3a0c02d560d9"),
    ("prime_field_polynomial_convolution_triangular_candidate.py", 16677, "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f"),
    ("prime_field_polynomial_representation_candidate.py", 42623, "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a"),
    ("prime_field_polynomial_division_candidate.py", 47986, "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2"),
    ("prime_field_polynomial_distributivity_candidate.py", 26118, "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86"),
    ("test_prime_field_polynomial_convolution_triangular_candidate.py", 9162, "e6bf4d2a0b2b00336b8d83b4ffe5d068e34e3d5bd44e8af4b995ca2723289822"),
    ("test_prime_field_polynomial_representation_candidate.py", 25517, "75a2cee90850ff07468b1d568ce4d3665f8006fdbb892c5838186abbc8fd57b7"),
    ("test_prime_field_polynomial_division_candidate.py", 23978, "c4f7555b19e88789c4a561ec5b66d1f9487f44a32b388f2beea90f9ec42eed3b"),
    ("test_prime_field_polynomial_distributivity_candidate.py", 21925, "d6200ef1e0447f3efb98461ce343a1a3ae5530f74490bd4b7782cbc13ed2e9a6"),
    ("augment_inherited_polynomial_seed.py", 10355, "e9dce56cff718bdce62ecfb258e4f2eb640053c010a1ebd1e8fb433f1b4f3a0f"),
    ("inspect_working_seed_syntax.py", 11886, "f4b374f6696d8772bbd24a4dd830e9e5679ac2a58f8a81489a44dfa591858f61"),
    ("artifacts/inherited-polynomial-products-three-lemmas-seed-v1.json", 812095, "f4d2567e664ae3ad6092e6b54a6599d2858ac4fafc0b4343085a218da6735624"),
    ("artifacts/working-prime-field-euclidean-proof-bundle-v1.json", 1635441, "3614e9504b84cfd24a52780d54ddc9eb16e49bf2df996c99664c9427e9a9fd83"),
    ("working-81-global-syntax-v1.json", 10290, "38e99d5574810ff9820b94952d11fa7b4f17a09a030c36fd42e4df94f2bf23b7"),
    ("working-81-verification-observations-v1.json", 14806, "28fba8440872bcc852f43ce0511d3a7659edc6da9a773bf373f037c7495be5ac"),
)


def _alpha_modules():
    return {name for name in sys.modules if name.startswith("peano_lab.library.editions_v")}


def _spec_digest(rows):
    # Independent materialized syntax serializer, not a proof checker and
    # not the implementation's streaming helper.
    records = [[row.name, row.statement, list(row.dependencies), list(row.script), row.summary] for row in rows]
    text = "".join(json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n" for record in records)
    return sha256(text.encode("utf-8")).hexdigest()


@pytest.fixture(scope="module")
def actual_state():
    before = _alpha_modules()
    state = support.load_candidate_state()
    assert _alpha_modules() == before
    yield state
    support.require_preserved81()
    support.require_extension_sources()
    assert _alpha_modules() == before


@pytest.mark.parametrize("name,size,digest", EXPECTED_PRESERVED, ids=[row[0] for row in EXPECTED_PRESERVED])
def test_all19_separately_verified_working81_inputs_remain_exact(name, size, digest):
    raw = support.bounded_bytes(HERE / name, size)
    assert (len(raw), sha256(raw).hexdigest()) == (size, digest)
    pin = next(pin for pin in support.PRESERVED81_PINS if pin.path == support.WORKING_RELATIVE + "/" + name)
    assert (pin.bytes, pin.sha256) == (size, digest)


@pytest.mark.parametrize("index,which", ((0, "source"), (0, "test"), (1, "source"), (1, "test")))
def test_actual_two_new_math_and_two_test_freezes(index, which):
    expected = EXPECTED_ADDED[index]
    owner = support.EXTENSION_FACTORIES[index]
    assert owner == support.Factory(*expected)
    pin = getattr(owner, which)
    raw = support.bounded_bytes(support.ROOT / pin.path, pin.bytes)
    assert (len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256)


def test_actual113_rows_preserve_the_exact81_prefix_and_topological_order(actual_state):
    assert len(actual_state.rows) == 113 and len(actual_state.added_rows) == 32
    assert all(new is old for new, old in zip(actual_state.rows[:81], actual_state.prior_state.rows, strict=True))
    assert actual_state.rows[81:] == actual_state.added_rows
    assert _spec_digest(actual_state.prior_state.rows) == EXPECTED_PRIOR_SPEC
    assert _spec_digest(actual_state.rows) == EXPECTED_SPEC == actual_state.specs_sha256 == support.COMBINED_SPECS_SHA256
    assert _spec_digest(actual_state.added_rows[:9]) == EXPECTED_ADDED[0][-1]
    assert _spec_digest(actual_state.added_rows[9:]) == EXPECTED_ADDED[1][-1]
    names, seen = {row.name for row in actual_state.rows}, set()
    assert len(names) == 113
    for row in actual_state.rows:
        assert (set(row.dependencies) & names) <= seen
        seen.add(row.name)
    assert sum(len(row.dependencies) for row in actual_state.rows) == 424
    assert sum(len(row.script) for row in actual_state.rows) == 8183


@pytest.mark.parametrize("index", range(113))
def test_every_actual_combined_statement_is_closed_original_first_order_syntax(actual_state, index):
    row = actual_state.rows[index]
    formula, free = parse_formula_with_names(row.statement)
    assert free == ()
    assert formula == support.base._closed_formula(row.statement)
    assert row.script and all(not command.startswith("use ") and "DNE" not in command for command in row.script)


def test_exact_four_new_principals_and_no_arbitrary_identity_uniqueness(actual_state):
    assert support.PRINCIPAL_ROOTS == EXPECTED_ROOTS
    added = {row.name: row for row in actual_state.added_rows}
    assert set(EXPECTED_ROOTS) <= added.keys()
    assert sha256(added[EXPECTED_ROOTS[0]].statement.encode()).hexdigest() == "b14ad2149cd34386887dcac50cb06b7df7014500b1ab918fac7967976b6042fe"
    assert sha256(added[EXPECTED_ROOTS[1]].statement.encode()).hexdigest() == "0ac4c1f5ca519e7db039365ff2a703f8772e22e58376d4c55a3f7777e08565fc"
    assert "prime_field_polynomial_division_execution_functional" in added[EXPECTED_ROOTS[1]].dependencies
    assert EXPECTED_ROOTS[2] in added[EXPECTED_ROOTS[3]].dependencies
    assert all("gcd" not in row.name and "bezout" not in row.name for row in actual_state.added_rows)


def test_repeated_loading_has_no_persistent_or_replaced_runtime_alias(actual_state):
    import peano_lab.library as package
    originals = (support.base.FACTORIES, support.base.MATH_SOURCE_PINS, support.base.MATH_TEST_PINS)
    for _ in range(2):
        another = support.load_candidate_state()
        assert another.rows == actual_state.rows
        for alias, _pin in support.WORKING_ALIAS_PINS:
            assert alias not in sys.modules and alias.rsplit(".", 1)[1] not in vars(package)
    assert originals == (support.base.FACTORIES, support.base.MATH_SOURCE_PINS, support.base.MATH_TEST_PINS)
    assert all(first is last for first, last in zip(originals, (support.base.FACTORIES, support.base.MATH_SOURCE_PINS, support.base.MATH_TEST_PINS)))


def test_temporary_aliases_are_real_exact_pinned_sources_then_removed():
    with support.temporary_working_aliases() as modules:
        assert len(modules) == 2
        for (alias, pin), module in zip(support.WORKING_ALIAS_PINS, modules, strict=True):
            assert sys.modules[alias] is module
            assert Path(module.__file__).resolve() == support.ROOT / pin.path
            assert Path(module.__spec__.origin).resolve() == support.ROOT / pin.path
            factory = getattr(module, "make_" + alias.rsplit(".", 1)[1] + "_theorems")
            assert factory.__module__ == alias
    assert all(alias not in sys.modules for alias, _pin in support.WORKING_ALIAS_PINS)


@pytest.mark.parametrize("index", (0, 1))
@pytest.mark.parametrize("origin", ("runtime", "same_working_file"))
def test_existing_module_even_same_path_is_never_replaced(index, origin, monkeypatch):
    alias, pin = support.WORKING_ALIAS_PINS[index]
    existing = ModuleType(alias)
    existing.__file__ = str(support.ROOT / pin.path) if origin == "same_working_file" else "/runtime/owned.py"
    monkeypatch.setitem(sys.modules, alias, existing)
    with pytest.raises(support.ExtensionError, match="cannot be replaced"):
        with support.temporary_working_aliases():
            pytest.fail("a foreign existing alias was accepted")
    assert sys.modules[alias] is existing
    assert all(other == alias or other not in sys.modules for other, _pin in support.WORKING_ALIAS_PINS)


@pytest.mark.parametrize("index", (0, 1))
def test_existing_package_attribute_is_not_overridden(index, monkeypatch):
    import peano_lab.library as package
    alias, _pin = support.WORKING_ALIAS_PINS[index]
    short, foreign = alias.rsplit(".", 1)[1], object()
    monkeypatch.setattr(package, short, foreign, raising=False)
    with pytest.raises(support.ExtensionError, match="cannot be replaced"):
        with support.temporary_working_aliases():
            pytest.fail("a runtime package attribute was ignored")
    assert getattr(package, short) is foreign
    assert all(name not in sys.modules for name, _pin in support.WORKING_ALIAS_PINS)


@pytest.mark.parametrize("index", (0, 1))
def test_resolvable_runtime_source_is_not_shadowed(index, monkeypatch):
    alias, _pin = support.WORKING_ALIAS_PINS[index]
    original = importlib.util.find_spec
    def found(name, package=None):
        if name == alias:
            return importlib.util.spec_from_loader(name, loader=None, origin="/runtime/owned.py")
        return original(name, package)
    monkeypatch.setattr(importlib.util, "find_spec", found)
    with pytest.raises(support.ExtensionError, match="runtime source"):
        with support.temporary_working_aliases():
            pytest.fail("a resolvable runtime was shadowed")
    assert all(name not in sys.modules for name, _pin in support.WORKING_ALIAS_PINS)


def test_alias_cleanup_after_local_exception_and_nested_collision():
    with pytest.raises(RuntimeError, match="deliberate test exception"):
        with support.temporary_working_aliases():
            raise RuntimeError("deliberate test exception")
    assert all(alias not in sys.modules for alias, _pin in support.WORKING_ALIAS_PINS)
    with support.temporary_working_aliases() as modules:
        with pytest.raises(support.ExtensionError, match="cannot be replaced"):
            with support.temporary_working_aliases():
                pytest.fail("nested overwrite")
        assert all(sys.modules[alias] is module for (alias, _pin), module in zip(support.WORKING_ALIAS_PINS, modules))
    assert all(alias not in sys.modules for alias, _pin in support.WORKING_ALIAS_PINS)


@pytest.mark.parametrize("index", (0, 1))
def test_foreign_alias_replacement_is_retained_but_scope_fails(index):
    alias, _pin = support.WORKING_ALIAS_PINS[index]
    foreign = ModuleType("test_owned_foreign_replacement")
    try:
        with pytest.raises(support.ExtensionError, match="replaced during"):
            with support.temporary_working_aliases():
                sys.modules[alias] = foreign
        assert sys.modules[alias] is foreign
        assert all(other == alias or other not in sys.modules for other, _pin in support.WORKING_ALIAS_PINS)
    finally:
        if sys.modules.get(alias) is foreign:
            del sys.modules[alias]


@pytest.mark.parametrize("attack", ("missing", "reversed", "extra"))
def test_only_exact_two_working_aliases_are_permitted(attack, monkeypatch):
    aliases = support.WORKING_ALIAS_PINS
    changed = aliases[:1] if attack == "missing" else tuple(reversed(aliases)) if attack == "reversed" else (*aliases, aliases[0])
    monkeypatch.setattr(support, "WORKING_ALIAS_PINS", changed)
    with pytest.raises(support.ExtensionError, match="two exact"):
        with support.temporary_working_aliases():
            pytest.fail("a foreign alias list was accepted")


@pytest.mark.parametrize("attack", ("missing", "reversed", "list", "foreign", "float_bytes", "bad_hash", "wrong_artifact"))
def test_preserved81_inventory_cannot_be_rebound(attack, monkeypatch):
    pins = support.PRESERVED81_PINS
    if attack == "wrong_artifact":
        monkeypatch.setattr(support, "PRIOR81_ARTIFACT", pins[15])
    else:
        changed = {"missing": pins[:-1], "reversed": tuple(reversed(pins)), "list": list(pins),
                   "foreign": (object(), *pins[1:]),
                   "float_bytes": (replace(pins[0], bytes=float(pins[0].bytes)), *pins[1:]),
                   "bad_hash": (replace(pins[0], sha256="0" * 64), *pins[1:])}[attack]
        monkeypatch.setattr(support, "PRESERVED81_PINS", changed)
    before = _alpha_modules()
    with pytest.raises(ValueError):
        support.require_preserved81()
    assert _alpha_modules() == before


@pytest.mark.parametrize("attack", ("missing", "reversed", "list", "foreign", "float_count", "boolean_count",
                                    "source_bytes", "source_hash", "test_bytes", "test_hash", "spec_hash"))
def test_exact_final_added_factory_source_and_test_guards(attack, monkeypatch):
    owners = support.EXTENSION_FACTORIES
    if attack in ("missing", "reversed", "list", "foreign"):
        changed = {"missing": owners[:1], "reversed": tuple(reversed(owners)), "list": list(owners),
                   "foreign": (object(), owners[1])}[attack]
    else:
        field, value = {"float_count": ("count", 9.0), "boolean_count": ("count", True),
                        "source_bytes": ("source_bytes", 0), "source_hash": ("source_sha256", "0" * 64),
                        "test_bytes": ("test_bytes", 1), "test_hash": ("test_sha256", "0" * 64),
                        "spec_hash": ("specs_sha256", "wrong")}[attack]
        changed = (replace(owners[0], **{field: value}), owners[1])
    monkeypatch.setattr(support, "EXTENSION_FACTORIES", changed)
    before = _alpha_modules()
    with pytest.raises(ValueError):
        support.require_extension_sources()
    assert _alpha_modules() == before


@pytest.mark.parametrize("value", (None, "", "0" * 63, "x" * 64, b"0" * 64, True))
def test_missing_or_foreign_complete_spec_pin_is_not_authority(value, monkeypatch):
    monkeypatch.setattr(support, "COMBINED_SPECS_SHA256", value)
    with pytest.raises(support.ExtensionError, match="specification"):
        support._require_spec_pin()


@pytest.mark.parametrize("value", (None, 0, 1, "yes", [], {}))
def test_spec_pin_selection_flag_is_boolean(value):
    with pytest.raises(support.ExtensionError, match="Boolean"):
        support.load_candidate_state(require_spec_pin=value)


@pytest.mark.parametrize("value", (None, {"passed": True}, (), object()))
def test_foreign_or_saved_state_is_rejected_before_alpha_import(value):
    before = _alpha_modules()
    with pytest.raises(support.ExtensionError, match="syntax state"):
        support.state_binding(value)
    assert _alpha_modules() == before


@pytest.mark.parametrize("attack", ("rows_list", "added_list", "prior_foreign", "prior_sources", "prior_rows",
                                    "missing_self_consistent", "changed_self_consistent", "wrong_digest", "sources_list"))
def test_changed_real113_state_is_not_a_binding(actual_state, attack):
    if attack == "rows_list":
        changed = replace(actual_state, rows=list(actual_state.rows))
    elif attack == "added_list":
        changed = replace(actual_state, added_rows=list(actual_state.added_rows))
    elif attack == "prior_foreign":
        changed = replace(actual_state, prior_state={"checked": True})
    elif attack == "prior_sources":
        changed = replace(actual_state, prior_state=replace(actual_state.prior_state, sources=()))
    elif attack == "prior_rows":
        changed = replace(actual_state, prior_state=replace(actual_state.prior_state, rows=None))
    elif attack == "sources_list":
        changed = replace(actual_state, added_sources=list(actual_state.added_sources))
    elif attack == "wrong_digest":
        changed = replace(actual_state, specs_sha256="0" * 64)
    else:
        rows = actual_state.rows[:-1] if attack == "missing_self_consistent" else (
            replace(actual_state.rows[0], summary="changed local metadata"), *actual_state.rows[1:])
        changed = replace(actual_state, rows=rows, specs_sha256=_spec_digest(rows))
    before = _alpha_modules()
    with pytest.raises(support.ExtensionError, match="syntax state"):
        support.state_binding(changed)
    assert _alpha_modules() == before


@pytest.mark.parametrize("kind", ("prior", "added", "alpha", "unknown"))
def test_pure_ownership_never_promotes_working81_to_alpha(actual_state, kind):
    # Formatting-only fixture: it is never supplied to a checker or binding.
    previous = tuple(row.name for row in actual_state.prior_state.rows)
    added = tuple(row.name for row in actual_state.added_rows)
    pure = SimpleNamespace(parent_support=("zero_add",))
    selection = support.SupportSelection(pure, previous, added)
    if kind == "unknown":
        with pytest.raises(support.ExtensionError):
            selection.role("not_in_the_cone")
    else:
        name, expected = {"prior": (previous[0], "prior_non_admitted_working81"),
                          "added": (added[0], "added_non_admitted_working32"),
                          "alpha": ("zero_add", "inherited_alpha_v32")}[kind]
        assert selection.role(name) == expected


@pytest.mark.parametrize("names", ((), [], ("zero_add",), ("unknown", "unknown"), (True,), (object(),)))
def test_foreign_or_noncanonical_owned_selection_stops_before_alpha(actual_state, names):
    before = _alpha_modules()
    with pytest.raises(support.ExtensionError, match="selections"):
        support.select_support(actual_state, names)
    assert _alpha_modules() == before


@pytest.mark.parametrize("value", (None, {}, {"passed": True}, object(), ()))
def test_missing_or_foreign_final_registration_fails_closed(value, monkeypatch):
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", value)
    before = _alpha_modules()
    with pytest.raises(support.ExtensionError, match="registered"):
        checker.require_final_inventory()
    assert _alpha_modules() == before


def test_real_complete_artifact_registration_is_exact_data_not_a_saved_receipt():
    before = _alpha_modules()
    pin = checker.require_final_inventory()
    assert type(pin) is checker.ArtifactPin
    assert pin == checker.ArtifactPin(
        support.WORKING_RELATIVE + "/artifacts/working-euclidean-extension-proof-bundle-v1.json",
        2219445, "c2e097f0e04c4b4f01bb219102405d0e93bc847c19625113eb48e55c7900734d",
        368, 1033, 29292)
    raw = support.bounded_bytes(support.ROOT / pin.path, pin.bytes)
    assert (len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256)
    assert pin.path != support.PRIOR81_ARTIFACT.path
    assert _alpha_modules() == before


@pytest.mark.parametrize("field,value", (
    ("bytes", True), ("bytes", 0), ("nodes", 1.0), ("nodes", -1), ("edges", True), ("body_nodes", 0),
    ("sha256", "0" * 63), ("sha256", "z" * 64), ("sha256", b"0" * 64),
    ("path", "/private/tmp/foreign.json"), ("path", support.PRIOR81_ARTIFACT.path),
    ("path", support.WORKING_RELATIVE + "/artifacts/../working-euclidean-extension-false.json"),
))
def test_malformed_or_old81_artifact_cannot_reach_final_proof_gate(field, value, monkeypatch):
    pin = checker.ArtifactPin(support.WORKING_RELATIVE + "/artifacts/working-euclidean-extension-not-a-proof.json",
                             1, "0" * 64, 1, 1, 1)
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", replace(pin, **{field: value}))
    with pytest.raises(support.ExtensionError, match="registered"):
        checker.require_final_inventory()


@pytest.mark.parametrize("name", (None, "", "prime_field_polynomial_division_execution_exists", [], {}, 1))
def test_only_four_exact_new_ordinary_principals_are_selectable(name):
    with pytest.raises(support.ExtensionError, match="four exact"):
        checker.verify_principal(name)


@pytest.mark.parametrize("seeds", (None, (), [], (None,), ("same", "same")))
def test_missing_or_duplicate_seed_paths_cannot_start_authoring(seeds):
    with pytest.raises(ValueError):
        exporter.export_authoring_bundle((EXPECTED_ROOTS[0],),
            HERE / "artifacts/working-euclidean-extension-never-written.json", seed_bundles=seeds)


@pytest.mark.parametrize("names", (None, (), [], (True,), ("same", "same")))
def test_malformed_authoring_selection_cannot_start_an_import(names):
    before = _alpha_modules()
    with pytest.raises(support.ExtensionError):
        exporter.export_authoring_bundle(names, HERE / "artifacts/working-euclidean-extension-never-written.json",
                                         seed_bundles=("not_opened",))
    assert _alpha_modules() == before


@pytest.mark.parametrize("path", (
    "/private/tmp/foreign.json", support.PRIOR81_ARTIFACT.path,
    support.WORKING_RELATIVE + "/artifacts/old-working-name.json",
    support.WORKING_RELATIVE + "/working-euclidean-extension-outside.json",
    support.WORKING_RELATIVE + "/artifacts/../working-euclidean-extension-outside.json",
    support.WORKING_RELATIVE + "/artifacts/.working-euclidean-extension-hidden.json",
))
def test_only_separate_exact_owned_extension_output_names_are_allowed(path):
    with pytest.raises(ValueError):
        exporter.destination(path)


def test_an_unused_new_extension_destination_is_only_a_path_not_a_write():
    path = HERE / "artifacts/working-euclidean-extension-never-written.json"
    assert not path.exists()
    assert exporter.destination(path) == path
    assert not path.exists()


def test_actual_local_report_denies_proof_and_admission_authority():
    report = support.local_manifest()
    assert (report["prior_working_rows"], report["added_working_rows"], report["combined_working_rows"]) == (81, 32, 113)
    assert report["source_factory_counts"] == [8, 30, 25, 18, 9, 23]
    assert report["combined_specs_sha256"] == EXPECTED_SPEC
    assert len(report["maximal_working_roots"]) == 23
    for field in ("global_current3971_novelty_checked", "original_ha_checked", "independent_lean_checked",
                  "ordinary_principals_checked", "prior_working_rows_reclassified_as_alpha",
                  "alpha_admission_performed", "stable_admission_performed"):
        assert report[field] is False


def test_original_proof_and_same_byte_lean_calls_are_not_replaced():
    tree = ast.parse(Path(checker.__file__).read_text())
    functions = {node.name: ast.unparse(node) for node in tree.body if isinstance(node, ast.FunctionDef)}
    bundle, root, loading = (functions[name] for name in ("verify_complete_bundle", "verify_principal", "_load_final"))
    assert "support.closure.check_bottom_layer_bundle(selected.frontier, bundle, target)" in bundle
    assert "independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)" in bundle
    assert "support.closure.replay_bottom_layer_theorem(selected.frontier, name, bundle, target)" in root
    assert "check((), proof.certificate, formula)" in root
    assert "proof.spec != exact_spec" in root and "proof.formula != formula" in root
    assert "_rebind(before)" in bundle and "_rebind(before)" in root
    assert "len(selected.owned) != 113" in loading
    assert "len(selected.previous_working_names) != 81" in loading
    assert "len(selected.added_working_names) != 32" in loading
    assert "support.base.statement_duplicates(state.rows)" in functions["global_metadata_report"]
    assert support.closure is support.base.closure


def test_fresh_seed_and_whole_ha_precede_exact_exclusive_output():
    source = ast.unparse(ast.parse(Path(exporter.__file__).read_text()))
    body = source[source.index("def export_authoring_bundle"):source.index("def main")]
    assert body.index("assemble_bottom_layer_bundle") < body.index("encode_proof_bundle")
    assert body.index("encode_proof_bundle") < body.index("previous_export._write_exclusive")
    assert "seed_bundles=seed_bundles" in body and "batch_size=1" in body
    assert "support.state_binding(support.load_candidate_state()) != before" in body
    assert exporter.previous_export._write_exclusive.__module__ == "export_working_euclidean"


def test_original_limits_and_non_authorizing_readme_observation_boundary():
    assert checker.CPU_LIMITS == exporter.CPU_LIMITS == (170, 175)
    assert checker.WALL_SECONDS == exporter.WALL_SECONDS == 180
    assert support.closure.DEFAULT_BUNDLE_LIMITS is support.base.closure.DEFAULT_BUNDLE_LIMITS
    assert support.closure.DEFAULT_LAYERED_REPLAY_LIMITS is support.base.closure.DEFAULT_LAYERED_REPLAY_LIMITS
    assert all("README" not in name and "PLAN" not in name and "observations" not in name for name in support.CONTROL_FILES)
    tree = ast.parse(Path(support.__file__).read_text())
    functions = {node.name: ast.unparse(node) for node in tree.body if isinstance(node, ast.FunctionDef)}
    assert "check_pin(pin" in functions["require_preserved81"]
    assert "json.loads" not in functions["require_preserved81"]
    assert "base.state_binding(state.prior_state, final=True)" in functions["state_binding"]


def test_cold_local113_loading_is_actual_syntax_without_alpha_or_alias_leaks():
    code = """import json, pathlib, sys
sys.path.insert(0, sys.argv[1])
import working_euclidean_extension_support as support
state = support.load_candidate_state()
assert not any(name.startswith('peano_lab.library.editions_v') for name in sys.modules)
assert all(name not in sys.modules for name, pin in support.WORKING_ALIAS_PINS)
print(json.dumps({'rows': len(state.rows), 'sha256': state.specs_sha256, 'proofs_checked': False}))
"""
    result = subprocess.run([sys.executable, "-I", "-B", "-c", code, str(HERE)],
                            capture_output=True, text=True, timeout=20, check=True)
    assert json.loads(result.stdout) == {"rows": 113, "sha256": EXPECTED_SPEC, "proofs_checked": False}
    assert result.stderr == ""


class _Accounting:
    def __init__(self):
        self.ids, self.calls, self.bad = (), [], []

    def pytest_collection_modifyitems(self, items):
        self.ids = tuple(item.nodeid for item in items)
        if len(self.ids) != len(set(self.ids)):
            raise pytest.UsageError("duplicate extension integration IDs")

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
