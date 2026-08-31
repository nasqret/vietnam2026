"""Independent working25 integration guards; no successful proof simulations.

Positive cases inspect real frozen syntax or write explicitly unissued bytes
to owned temporary transport files. Every proof seam used by a negative test
always rejects. No test imports Alpha, replays a whole bundle, invokes Lean,
mints a live context, or reads a saved observation as proof authority.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
for directory in (HERE, ROOT / "scripts", ROOT / "peano-lab/py"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import working_shift_scalar_support as support
import export_working_shift_scalar as exporter
import check_working_shift_scalar as checker

SOURCE_PINS = (
    ("research/arithmetic-library/working/prime-field-shift-v1/prime_field_polynomial_shift_candidate.py",
     29786, "325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b"),
    ("research/arithmetic-library/working/prime-field-shift-v1/test_prime_field_polynomial_shift_candidate.py",
     32010, "0622fb92978fcf028842aa4d9822ef61213642eb852e080f7c787dcea4bb395f"),
    ("research/arithmetic-library/working/prime-field-scalar-v1/prime_field_polynomial_scalar_convolution_candidate.py",
     23637, "e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e"),
    ("research/arithmetic-library/working/prime-field-scalar-v1/test_prime_field_polynomial_scalar_convolution_candidate.py",
     30353, "881452ada0b5dc3be7d6cd00ee31dc08075b07f51d83595ee60f8cfb40d4c6e5"),
)
PARENT_PINS = (
    ("artifacts/peano-library/alpha/catalog-v33.json", 946819,
     "6be052da195a295edce02f4b1955cd9e3dd71d7acefb9ac5794277eda7ef40cc"),
    ("artifacts/peano-library/alpha/catalog-v30.json", 66503303,
     "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"),
    ("artifacts/peano-library/alpha/catalog-v33-delta.json", 38228899,
     "bf215f0a158b82dfb2e9e5e4a07fd7357d064b7f8a4e0230f3624b761775b1c4"),
    ("artifacts/peano-library/channels-v33.json", 9638,
     "d10d87694f813b86451bcccdde4dcd68e5d6fe73795b9610d98bea4f3e5de6bc"),
)
NAMES = (
    "prime_field_polynomial_shift_exists", "prime_field_polynomial_shift_bounded",
    "prime_field_polynomial_shift_functional", "prime_field_polynomial_shift_zero_prefix",
    "polynomial_zero_extended_shift_forward", "polynomial_zero_extended_shift_reverse",
    "polynomial_diagonal_term_shift_right_iff", "prime_field_convolution_coefficient_shift_right_iff",
    "polynomial_product_length_shift_right_nonempty",
    "prime_field_polynomial_convolution_shift_right_nonempty",
    "prime_field_polynomial_convolution_shift_right_empty",
    "prime_field_polynomial_convolution_shift_right_equivalent",
    "prime_field_polynomial_convolution_shift_right_exists",
    "prime_field_polynomial_shift_power_zero", "prime_field_polynomial_shift_power_successor",
    "beta_sum_pointwise_mod_scale", "polynomial_zero_extended_scale_congruent",
    "polynomial_diagonal_term_right_scale_congruent", "polynomial_diagonal_sum_right_scale_congruent",
    "prime_field_convolution_coefficient_right_scale", "prime_field_polynomial_convolution_right_scale",
    "prime_field_polynomial_convolution_right_scale_equal", "prime_field_polynomial_convolution_right_scale_exists",
    "prime_field_polynomial_scale_zero_value", "prime_field_polynomial_convolution_right_scale_zero",
)
PRINCIPALS = {
    NAMES[9]: "6f60c7f6c17e34de78a145b9a6cb532ca29ba7a0a3b13d3c7b4abc78973bbe00",
    NAMES[11]: "56aeba7667a7fc9ee6253ce009cc56e950d24249a3e1fbd4efb25f3bef7558b0",
    NAMES[12]: "0fc173b813282a7111d604245b1706a4c01c5bcf566812151810e9afe38f065d",
    NAMES[14]: "95f29368de026c7478030396755847941e66199186ea801fb3f3e9f635f86ba7",
    NAMES[20]: "b0ed0acc0a69da43be5864e35d7b089dd83f35d3df5fa493c2716867d8e0c8f4",
    NAMES[21]: "42cae7e1cc12bbe6b7b33d8060e1c66b7b46555d983ade711fd09d5545cb5e6c",
    NAMES[22]: "5d0349367decc3084471726b73a77617d49f484cf31191bb78effbc434167156",
}
INITIAL_MISSING = {
    "polynomial_product_length_functional", "prime_field_polynomial_convolution_bounded",
    "prime_field_polynomial_convolution_outside_zero", "prime_field_polynomial_scale_functional",
}


@pytest.fixture(scope="module")
def state():
    return support.load_candidate_state()


@pytest.fixture(scope="module")
def selection(state):
    return support.select_support(state)


@pytest.fixture(scope="module")
def coverage(selection):
    return support.seed_coverage(selection, support.SEED_PINS)


@pytest.mark.parametrize("relative,size,digest", SOURCE_PINS)
def test_all_four_frozen_source_and_test_files_are_exact(relative, size, digest):
    raw = (ROOT / relative).read_bytes()
    assert (len(raw), sha256(raw).hexdigest()) == (size, digest)


@pytest.mark.parametrize("pin", support.RUNTIME_PINS, ids=lambda pin: pin.path)
def test_every_selected_original_runtime_input_has_its_literal_byte_identity(pin):
    raw = support.read_pin(pin, support.MAX_SOURCE_BYTES)
    assert len(raw) == pin.bytes and sha256(raw).hexdigest() == pin.sha256


@pytest.mark.parametrize("owner", support.FACTORIES, ids=lambda owner: owner.module)
def test_factory_freezes_are_independently_declared(owner, state):
    offset = 0 if owner.count == 15 else 15
    rows = state.rows[offset:offset + owner.count]
    digest = sha256()
    for row in rows:
        digest.update((json.dumps([row.name, row.statement, row.dependencies, row.script, row.summary],
                                 separators=(",", ":")) + "\n").encode())
    assert digest.hexdigest() == {
        15: "beac32710e2191f4dc40f6317dc376f6b3307ad8ad48a7ccbac17c8bea990081",
        10: "a8ab3e2660a01dc79520722de6093c534e4184dcdbcb9481317df4d5b6a54a7b",
    }[owner.count]
    assert owner.specs_sha256 == digest.hexdigest()


def test_exact_25_source_order_and_independent_totals(state, selection):
    assert tuple(row.name for row in state.rows) == NAMES
    assert len(state.rows) == 25
    assert state.specs_sha256 == "15d48cfcf25a997db2e18771d0c084f4465225c6137f47f53350d39a5ebb6981"
    assert sum(len(row.dependencies) for row in state.rows) == 81
    assert sum(len(row.script) for row in state.rows) == 1778
    assert len(selection.complete_specs) == 207 and len(selection.support) == 182
    assert sum(len(row.dependencies) for row in selection.complete_specs) == 490
    assert selection.root_names == (NAMES[12], NAMES[13], NAMES[14], NAMES[22], NAMES[24])
    assert sha256("\n".join(row.name for row in selection.complete_specs).encode()).hexdigest() == (
        "b2b9124392781805a938c379dd1258e8ff54902988e7ed13be5dc2fe8cd8f019")
    assert tuple(support.PRINCIPAL_ROOTS) == tuple(PRINCIPALS)
    assert len(support.PRINCIPAL_ROOTS) == 7
    seen = set()
    for row in selection.complete_specs:
        assert set(row.dependencies) <= seen
        seen.add(row.name)


@pytest.mark.parametrize("name", tuple(PRINCIPALS))
def test_seven_exact_principal_pins_use_actual_raw_statements(name, state):
    row = next(row for row in state.rows if row.name == name)
    assert sha256(row.statement.encode()).hexdigest() == PRINCIPALS[name]
    index = support.PRINCIPAL_ROOTS.index(name)
    assert support.PRINCIPAL_STATEMENT_SHA256[index] == PRINCIPALS[name]


@pytest.mark.parametrize("count", tuple(range(1, 26)))
def test_source_prefixes_keep_exact_ownership_without_proof_or_alpha(count, state):
    before = support._edition_bindings()
    chosen = support.select_support(state, NAMES[:count])
    assert tuple(row.name for row in chosen.owned) == NAMES[:count]
    assert set(chosen.root_names) <= set(NAMES[:count])
    assert not {row.name for row in chosen.support} & set(NAMES)
    assert support._edition_bindings() == before
    for row in chosen.owned:
        assert chosen.role(row.name) == "new_non_admitted_shift_scalar"
    for row in chosen.support:
        assert chosen.role(row.name) == "inherited_canonical_source"


def test_source_loading_never_registers_working_or_production_aliases():
    before = support._edition_bindings()
    names = tuple("_working_shift_scalar_v1_" + owner.module for owner in support.FACTORIES)
    assert all(name not in sys.modules for name in names)
    support.load_candidate_state()
    assert all(name not in sys.modules for name in names)
    after = support._edition_bindings()
    assert after.keys() == before.keys() and all(after[name] is module for name, module in before.items())
    syntax = ast.parse(inspect.getsource(support.load_candidate_state))
    assert not any(isinstance(node, (ast.Assign, ast.AnnAssign))
                   and any(isinstance(item, ast.Attribute) and item.attr == "modules"
                           for item in ast.walk(node)) for node in ast.walk(syntax))
    assert "temporary_representation_alias" not in (HERE / "working_shift_scalar_support.py").read_text()


@pytest.mark.parametrize("owner", support.FACTORIES, ids=lambda owner: owner.module)
def test_foreign_private_factory_name_is_never_replaced(monkeypatch, owner):
    name = "_working_shift_scalar_v1_" + owner.module
    foreign = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, foreign)
    with pytest.raises(support.WorkingError, match="already owned"):
        support.load_candidate_state()
    assert sys.modules[name] is foreign


@pytest.mark.parametrize("fault", ("missing_file", "foreign_file", "foreign_spec", "missing_factory"))
def test_canonical_source_origin_and_factory_fail_closed(monkeypatch, fault):
    name = "peano_lab.library.prime_field_arithmetic_candidate"
    foreign = ModuleType(name)
    path = str(ROOT / "peano-lab/py/peano_lab/library/prime_field_arithmetic_candidate.py")
    foreign.__file__ = path if fault != "foreign_file" else "/unowned/fake.py"
    foreign.__spec__ = SimpleNamespace(origin=path if fault != "foreign_spec" else "/unowned/fake.py")
    if fault == "missing_file":
        del foreign.__file__
    monkeypatch.setitem(sys.modules, name, foreign)
    with pytest.raises(support.WorkingError):
        support.canonical_provider_table()
    assert sys.modules[name] is foreign


@pytest.mark.parametrize("bad", ((), [], (NAMES[0], NAMES[0]), (NAMES[1], NAMES[0]),
                               ("missing",), (True,), (1,), "all", {}))
def test_unknown_unordered_or_duplicate_working_selections_are_rejected(bad, state):
    with pytest.raises(support.WorkingError):
        support.select_support(state, bad)


@pytest.mark.parametrize("index", tuple(range(25)))
@pytest.mark.parametrize("field", ("statement", "script", "dependencies", "summary"))
def test_every_changed_owned_specification_is_rejected(index, field, state):
    row = state.rows[index]
    value = {"statement": "0=1", "script": ("exact missing",),
             "dependencies": ("missing_actual_dependency",), "summary": row.summary + " altered"}[field]
    rows = list(state.rows)
    rows[index] = replace(row, **{field: value})
    bad = replace(state, rows=tuple(rows))
    with pytest.raises(support.WorkingError):
        support.validate_state(bad)


@pytest.mark.parametrize("bad", (None, {}, (), SimpleNamespace(rows=(), specs_sha256="a" * 64)))
def test_foreign_state_cannot_become_a_checkpoint(bad):
    with pytest.raises(support.WorkingError):
        support.validate_state(bad)


@pytest.mark.parametrize("fault", ("missing", "extra", "type", "wrong_digest"))
def test_incomplete_or_forged_state_inventory_fails(fault, state):
    if fault == "missing": bad = replace(state, rows=state.rows[:-1])
    elif fault == "extra": bad = replace(state, rows=(*state.rows, state.rows[0]))
    elif fault == "type": bad = replace(state, rows=list(state.rows))
    else: bad = replace(state, specs_sha256="0" * 64)
    with pytest.raises(support.WorkingError):
        support.validate_state(bad)


@pytest.mark.parametrize("field,value", (("count", 14), ("source_bytes", 1),
    ("test_bytes", True), ("source_sha256", "a" * 64), ("test_sha256", "b" * 64),
    ("specs_sha256", "c" * 64), ("module", "foreign"), ("directory", "../foreign")))
def test_factory_ownership_mutations_are_rejected_before_loading(monkeypatch, field, value):
    owners = (replace(support.FACTORIES[0], **{field: value}), support.FACTORIES[1])
    monkeypatch.setattr(support, "FACTORIES", owners)
    with pytest.raises(support.WorkingError, match="source ownership"):
        support.require_working_sources()


@pytest.mark.parametrize("fault", ("missing", "extra", "sha", "size", "path", "type"))
def test_original_runtime_inventory_cannot_be_weakened(monkeypatch, fault):
    pins = support.RUNTIME_PINS
    if fault == "missing": pins = pins[1:]
    elif fault == "extra": pins = (*pins, pins[0])
    elif fault == "sha": pins = (replace(pins[0], sha256="a" * 64), *pins[1:])
    elif fault == "size": pins = (replace(pins[0], bytes=True), *pins[1:])
    elif fault == "path": pins = (replace(pins[0], path="../foreign"), *pins[1:])
    else: pins = list(pins)
    monkeypatch.setattr(support, "RUNTIME_PINS", pins)
    with pytest.raises(support.WorkingError, match="runtime source inventory"):
        support.require_runtime_sources()


@pytest.mark.parametrize("relative,count,digest", support.PRESERVED_ARCHIVES)
def test_both_complete_historical_archives_remain_literal(relative, count, digest):
    records = support._archive_records(relative)
    assert len(records) == count
    assert sha256(support.canonical(records)).hexdigest() == digest
    assert relative not in {"research/arithmetic-library/working/prime-field-shift-v1",
                            "research/arithmetic-library/working/prime-field-scalar-v1"}


def test_observations_are_preservation_only_and_never_imported():
    source = (HERE / "working_shift_scalar_support.py").read_text()
    assert "working_equivalence_support" not in source
    assert "working_euclidean_support" not in source
    assert "temporary_representation_alias" not in source
    assert "sys.modules[" not in source
    actual = support.local_manifest()
    for field in ("global_current4092_novelty_checked", "original_ha_checked",
                  "independent_lean_checked", "ordinary_principals_checked",
                  "alpha_admission_performed", "stable_admission_performed",
                  "associativity_proved", "gcd_bezout_proved", "full_G091_proved"):
        assert actual[field] is False


def test_initial_real_seed_reports_the_four_actual_missing_targets(selection):
    initial = support.seed_coverage(selection, (support.INITIAL_SEED,))
    assert initial["inherited_targets"] == 182 and initial["covered_targets"] == 178
    assert set(initial["missing_names"]) == INITIAL_MISSING
    assert initial["seeds"][0]["inert_nodes"] == 377
    assert initial["proof_bodies_decoded"] is initial["original_ha_checked"] is initial["proof_authority"] is False


def test_all_three_actual_inert_seeds_cover_the_exact_ordered_premises(coverage):
    assert coverage["inherited_targets"] == coverage["covered_targets"] == 182
    assert coverage["missing_names"] == []
    assert [row["inert_nodes"] for row in coverage["seeds"]] == [377, 210, 202]
    assert set(coverage["seeds"][1]["newly_covered_names"]) == INITIAL_MISSING - {"prime_field_polynomial_scale_functional"}
    assert coverage["seeds"][2]["newly_covered_names"] == ["prime_field_polynomial_scale_functional"]
    assert coverage["raw_json_only"] is True
    assert coverage["proof_bodies_decoded"] is coverage["original_ha_checked"] is coverage["proof_authority"] is False


@pytest.mark.parametrize("pin", support.SEED_PINS, ids=lambda pin: Path(pin.path).name)
def test_seed_identity_is_literal_but_not_a_proof_acceptance(pin):
    raw = support.read_pin(pin)
    assert (len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256)
    value = json.loads(raw)
    assert value[0] == "peano-lab-bundle-v1"
    # The first node field is original codec fuel, NOT its positional ID.
    assert all(type(row[0]) is int and row[0] > 0 for row in value[3])
    assert value[3][0][0] != 0


@pytest.mark.parametrize("bad", ((), [], "seed.json", (True,), (ROOT / "outside.json",),
                               (ROOT / support.INITIAL_SEED.path, ROOT / support.INITIAL_SEED.path)))
def test_seed_selection_is_explicit_narrow_and_distinct(bad):
    with pytest.raises(ValueError):
        support.seed_inventory(bad)


def test_initial_canonical121_seed_cannot_be_silently_omitted():
    with pytest.raises(support.WorkingError, match="canonical121"):
        support.seed_inventory(tuple(ROOT / pin.path for pin in support.SUPPLEMENTAL_SEEDS))


@pytest.mark.parametrize("fault", ("target", "premise"))
def test_inert_matching_requires_actual_target_and_ordered_premises(fault, state, selection):
    # Pure syntax mutations: real seed bytes and every checker stay untouched.
    row = next(row for row in selection.support if row.name == "prime_field_polynomial_scale_functional")
    changed = replace(row, statement="0=1") if fault == "target" else replace(row, dependencies=())
    altered = replace(selection, support=tuple(changed if item.name == row.name else item for item in selection.support),
                      complete_specs=tuple(changed if item.name == row.name else item for item in selection.complete_specs))
    report = support.seed_coverage(altered, support.SEED_PINS)
    assert row.name in report["missing_names"]
    assert report["proof_authority"] is False


@pytest.mark.parametrize("name", ("", "../unsafe", "prime_field_polynomial_associative", None, True, 1))
def test_only_the_seven_exact_ordinary_principals_are_selectable(name, monkeypatch):
    monkeypatch.setattr(checker, "_load_final", lambda: pytest.fail("invalid root reached proof data"))
    with pytest.raises(support.WorkingError, match="seven exact"):
        checker.verify_principal(name)


@pytest.mark.parametrize("bad", (None, {}, SimpleNamespace(path="receipt.json"), True))
def test_unregistered_final_proof_data_never_reaches_parent_or_kernel(monkeypatch, bad):
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", bad)
    monkeypatch.setattr(support, "require_parent_registration", lambda: pytest.fail("bad artifact reached parent"))
    monkeypatch.setattr(support.closure, "check_bottom_layer_bundle", lambda *a, **k: pytest.fail("bad artifact reached HA"))
    with pytest.raises(support.WorkingError):
        checker.verify_complete_bundle()


def test_actual_complete_candidate_registration_is_data_not_proof_acceptance(monkeypatch):
    def forbidden(*_args, **_kwargs):
        pytest.fail("literal candidate registration must not check a proof")
    monkeypatch.setattr(support.closure, "check_bottom_layer_bundle", forbidden)
    before = support._edition_bindings()
    pin = checker.require_final_inventory()
    assert pin == checker.ArtifactPin(
        support.WORKING_RELATIVE + "/artifacts/working-shift-scalar-proof-bundle-v1.json",
        707587, "e8ed419608273f0230348ae498e57a23f0b59ade805964d30e0e8a3f10083cd0",
        208, 495, 12725)
    raw = support.read_pin(support.FilePin(pin.path, pin.bytes, pin.sha256))
    assert (len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256)
    inert = json.loads(raw)
    assert len(inert) == 4 and inert[0] == "peano-lab-bundle-v1"
    assert inert[1] == 207 and inert[2] == inert[3][207][1]
    assert len(inert[3]) == 208 and sum(len(row[2]) for row in inert[3]) == 495
    assert not hasattr(pin, "accepted") and not hasattr(pin, "proof_authority")
    assert support._edition_bindings() == before


@pytest.mark.parametrize("field,value", (("path", "../old.json"), ("path", "artifacts/old.json"),
    ("bytes", True), ("bytes", 0), ("bytes", 67108865), ("sha256", "G" * 64),
    ("nodes", 207), ("nodes", True), ("edges", 0), ("body_nodes", False)))
def test_final_artifact_shape_cannot_accept_prefix_or_foreign_data(monkeypatch, field, value):
    # Always-reject data: never a successful artifact or mocked kernel result.
    pin = checker.ArtifactPin(support.WORKING_RELATIVE + "/artifacts/working-shift-scalar-unissued.json",
                              1, "a" * 64, 208, 495, 1)
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", replace(pin, **{field: value}))
    monkeypatch.setattr(support, "require_parent_registration", lambda: pytest.fail("bad shape reached parent"))
    with pytest.raises(support.WorkingError):
        checker.require_final_inventory()


@pytest.mark.parametrize("bad", (None, (), [], (support.INITIAL_SEED,), True))
def test_unregistered_current_parent_never_reaches_catalogue_or_membership(monkeypatch, bad):
    monkeypatch.setattr(support, "PARENT_CATALOG_PINS", bad)
    import peano_catalog_shards_v33 as codec
    monkeypatch.setattr(codec, "verify_catalog_bindings", lambda *a, **k: pytest.fail("unregistered parent reached codec"))
    with pytest.raises(support.WorkingError, match="registered"):
        support.require_parent_registration()


@pytest.mark.parametrize("index,record", tuple(enumerate(PARENT_PINS)), ids=lambda row: str(row))
def test_registered_parent_literals_match_actual_data_without_decoding(index, record):
    pins = (*support.PARENT_CATALOG_PINS, support.PARENT_CHANNEL_PIN)
    actual = pins[index]
    assert (actual.path, actual.bytes, actual.sha256) == record
    support.check_pin(actual, ROOT, support.MAX_CATALOG_BYTES)


def test_registered_parent_identity_fields_match_actual_small_manifest():
    manifest = json.loads(support.read_pin(support.PARENT_CATALOG_PINS[0], support.MAX_CATALOG_BYTES))
    assert manifest["schema"] == "peano-library-alpha-shards-v33"
    metadata = manifest["metadata"]
    assert metadata["theorem_count"] == metadata["checked_use_count"] == 4092
    assert metadata["stable_count"] == 432
    assert metadata["edition_identity_sha256"] == support.PARENT_IDENTITY_SHA256 == (
        "9e66890600db5f787230fb5e48e18ce08026750ba4a9d3fa7b0b1e30f6e39a3d")
    assert metadata["ordered_enrollment_root_sha256"] == support.PARENT_ENROLLMENT_SHA256 == (
        "0d4101bfee06dfff5a49ee8cfaf955a2c81a43ac622623e27890d6fe541eeaa0")


def test_registered_parent_authenticates_three_files_without_full_catalogue_or_proof(monkeypatch):
    import peano_catalog_shards_v33 as codec
    def forbidden(*_args, **_kwargs):
        pytest.fail("data registration must not parse the full catalogue or check a proof")
    monkeypatch.setattr(codec, "load_catalog", forbidden)
    monkeypatch.setattr(support.closure, "check_bottom_layer_bundle", forbidden)
    before = support._edition_bindings()
    actual = support.require_parent_registration()
    assert tuple((row.path.relative_to(ROOT).as_posix(), row.bytes, row.sha256)
                 for row in actual.files) == PARENT_PINS[:3]
    assert support._edition_bindings() == before


def test_literal_parent_and_final_registration_are_data_not_saved_success_flags():
    source = ast.parse((HERE / "check_working_shift_scalar.py").read_text())
    function = next(row for row in source.body if isinstance(row, ast.FunctionDef) and row.name == "require_final_inventory")
    assert "require_parent_registration" in ast.unparse(function)
    for filename in ("export_working_shift_scalar.py", "check_working_shift_scalar.py"):
        text = (HERE / filename).read_text()
        for bad in ("--skip", "--receipt", "--accept", "mock", "proofs_verified=True"):
            assert bad not in text
    assert not hasattr(checker, "accept_receipt")


def test_global_novelty_is_actual_parsed_ast_not_raw_text_or_digest_alone():
    # Generic syntax test only; these rows are never a current catalogue.
    spec = support.TheoremSpec
    first = spec("first", "forall x. x=x", (), ("intro x", "rfl"), "syntax fixture")
    renamed = spec("renamed", "forall y. y=y", (), ("intro y", "rfl"), "syntax fixture")
    different = spec("different", "forall y. y=0", (), ("intro y", "rfl"), "false syntax fixture")
    assert checker._novelty_pairs((first, renamed), (different,)) == (("renamed", "first"),)
    assert checker._novelty_pairs((first,), (renamed,)) == (("first", "renamed"),)
    assert checker._novelty_pairs((first,), (different,)) == ()


def _calls(function, name):
    return [node for node in ast.walk(ast.parse(inspect.getsource(function)))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == name]


def test_actual_authoring_routes_through_the_unchanged_whole_assembler():
    calls = _calls(exporter.export_authoring_bundle, "assemble_bottom_layer_bundle")
    assert len(calls) == 1
    call = calls[0]
    assert ast.unparse(call.func) == "support.closure.assemble_bottom_layer_bundle"
    assert len(call.args) == 1 and ast.unparse(call.args[0]) == "execution.frontier"
    assert {item.arg for item in call.keywords} == {"seed_bundles", "batch_size", "report"}
    assert next(item.value.value for item in call.keywords if item.arg == "batch_size") == 1
    source = inspect.getsource(exporter.export_authoring_bundle)
    assert source.index('not coverage["missing_names"]') < source.index("assemble_bottom_layer_bundle(")
    assert source.index("state_binding(support.load_candidate_state())") < source.index("write_exclusive(output, payload)")
    assert source.index("for pin in seeds:") < source.index("write_exclusive(output, payload)")


def test_complete_bundle_uses_actual_whole_ha_then_same_payload_original_lean():
    source = inspect.getsource(checker.verify_complete_bundle)
    assert source.index("check_bottom_layer_bundle(") < source.index("independent._lean_check(")
    assert "independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)" in source
    assert "receipt.kernel_calls == pin.nodes" in source
    assert "_rebind(before)" in source
    call = _calls(checker.verify_complete_bundle, "check_bottom_layer_bundle")[0]
    assert not call.keywords and len(call.args) == 3


def test_ordinary_replay_preserves_compiler_full_check_and_exact_empty_context():
    source = inspect.getsource(checker.verify_principal)
    assert source.index("replay_bottom_layer_theorem(") < source.index("check((), proof.certificate, formula)")
    assert "proof.spec == exact and proof.formula == formula" in source
    assert source.index("del state, payload") < source.index("replay_bottom_layer_theorem(")
    assert source.index("del bundle, target") < source.index("check((), proof.certificate, formula)")
    assert "_rebind(before)" in source
    call = _calls(checker.verify_principal, "replay_bottom_layer_theorem")[0]
    assert not call.keywords and len(call.args) == 4


def test_proof_workers_do_not_load_current4092_and_default_codec_fuel_is_unchanged():
    for function in (checker._load_final, checker.verify_complete_bundle, checker.verify_principal,
                     support.execution_selection, exporter.export_authoring_bundle):
        source = inspect.getsource(function)
        assert "load_catalog(" not in source and "editions_v33" not in source
    source = inspect.getsource(checker.global_metadata_report)
    assert 'state_binding(state, final=True)' in source and "load_catalog(" in source
    assert "len(catalog[\"theorems\"]) == 4092" in source
    syntax = ast.parse(inspect.getsource(checker._load_final))
    calls = [node for node in ast.walk(syntax) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "decode_proof_bundle"]
    assert len(calls) == 1 and len(calls[0].args) == 1 and calls[0].keywords == []
    assert "fuel" not in inspect.getsource(exporter.export_authoring_bundle)
    assert "fuel" not in inspect.getsource(checker._load_final)


def test_current_parent_is_only_metadata_and_never_a_replayed_success_receipt():
    source = inspect.getsource(support.require_parent_registration)
    assert "verify_catalog_bindings(" in source
    assert "artifact_sha256" in source and '"stable"' in source and '"v33"' not in source
    assert "receipt" not in source
    assert "load_catalog(" not in source


def test_original_catalogue_and_mathematical_payload_ceilings_are_distinct():
    assert support.MAX_BYTES == support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes == 64000000
    assert support.MAX_CATALOG_BYTES == support.inherited.MAX_CATALOG_COMPONENT_BYTES == 64 * 1024 * 1024
    assert support.MAX_BYTES < support.closure.PARENT_CATALOG_BYTES <= support.MAX_CATALOG_BYTES
    assert "MAX_CATALOG_BYTES" in inspect.getsource(support.require_parent_registration)
    assert "closure.PARENT_CATALOG_SHA256), ROOT, MAX_CATALOG_BYTES" in inspect.getsource(support.state_binding)
    assert "len(payload) <= support.MAX_BYTES" in inspect.getsource(exporter.export_authoring_bundle)


@pytest.mark.parametrize("filename", ("export_working_shift_scalar.py", "check_working_shift_scalar.py"))
def test_original_cpu_alarm_and_no_skip_cli_are_literal(filename):
    source = (HERE / filename).read_text()
    assert "resource.setrlimit(resource.RLIMIT_CPU, (170, 175))" in source
    assert "signal.alarm(180)" in source
    assert source.index("resource.setrlimit(resource.RLIMIT_CPU, (170, 175))") < source.index("import working_shift_scalar_support")
    assert "CPU_LIMITS, WALL_SECONDS = (170, 175), 180" in source
    assert "authoring_rss_bytes()" in source
    for forbidden in ("setrecursionlimit", "setprofile", "settrace", "max_nodes=", "max_edges=", "max_body_nodes=", "fuel="):
        assert forbidden not in source


@pytest.mark.parametrize("bad", (None, "true", 0, 1, [], {}))
def test_state_binding_final_flag_is_strict(bad, state):
    with pytest.raises(support.WorkingError, match="Boolean"):
        support.state_binding(state, final=bad)


@pytest.mark.parametrize("name", ("../old.json", "/old.json", "unissued.json",
    "working-shift-scalar-unissued.txt", "working-shift-scalar-../bad.json", "working-shift-scalar-?.json"))
def test_output_names_cannot_escape_or_overwrite_other_scopes(name):
    path = Path(name) if name.startswith("/") else support.ARTIFACT_DIRECTORY / name
    with pytest.raises(support.WorkingError):
        exporter.destination(path)


def test_all_preexisting_target_types_are_rejected_before_writing(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    directory = root / "artifacts"
    directory.mkdir()
    monkeypatch.setattr(exporter, "ARTIFACT_DIRECTORY", directory)
    for kind in ("file", "directory", "symlink"):
        path = directory / ("working-shift-scalar-" + kind + ".json")
        if kind == "file": path.write_bytes(b"unissued old transport bytes")
        elif kind == "directory": path.mkdir()
        else: path.symlink_to(root / "absent.json")
        with pytest.raises(support.WorkingError, match="never overwritten"):
            exporter.destination(path)


@pytest.fixture
def writer(tmp_path, monkeypatch):
    # Transport-only unissued bytes: no decoder/kernel/receipt is involved.
    root = tmp_path.resolve()
    directory = root / "artifacts"
    monkeypatch.setattr(exporter, "ARTIFACT_DIRECTORY", directory)
    monkeypatch.setattr(support, "ROOT", root)
    monkeypatch.setattr(exporter, "_resources", lambda: 1)
    return root, directory, directory / "working-shift-scalar-unissued.json"


def test_owned_exclusive_transport_write_is_exact_and_nonoverwriting(writer):
    root, directory, path = writer
    payload = b"UNISSUED TRANSPORT FIXTURE; NOT PROOF DATA"
    exporter.write_exclusive(path, payload)
    assert path.read_bytes() == payload and path.stat().st_uid == os.getuid()
    assert path.stat().st_nlink == 1
    with pytest.raises(support.WorkingError, match="never overwritten"):
        exporter.write_exclusive(path, payload + b"changed")
    assert path.read_bytes() == payload


@pytest.mark.parametrize("bad", (b"", bytearray(b"x"), "unissued", None, True))
def test_exclusive_writer_rejects_nonliteral_bytes_before_output(writer, bad):
    path = writer[2]
    with pytest.raises(support.WorkingError, match="proof-data bytes"):
        exporter.write_exclusive(path, bad)
    assert not path.exists()


def test_owned_partial_output_is_removed_after_a_late_resource_rejection(writer, monkeypatch):
    path = writer[2]
    calls = []
    def resources():
        calls.append(None)
        if len(calls) == 2:
            raise support.WorkingError("forced transport resource rejection")
        return 1
    monkeypatch.setattr(exporter, "_resources", resources)
    with pytest.raises(support.WorkingError, match="forced transport"):
        exporter.write_exclusive(path, b"UNISSUED TRANSPORT FIXTURE")
    assert len(calls) == 2 and not path.exists()


def test_rollback_never_deletes_a_replacement_foreign_inode(writer, monkeypatch):
    path = writer[2]
    backup = writer[1] / "owned-backup.txt"
    calls = []
    def resources():
        calls.append(None)
        if len(calls) == 2:
            path.rename(backup)
            path.write_bytes(b"FOREIGN REPLACEMENT TRANSPORT FIXTURE")
            raise support.WorkingError("late rejection")
        return 1
    monkeypatch.setattr(exporter, "_resources", resources)
    with pytest.raises(support.WorkingError, match="rollback refuses"):
        exporter.write_exclusive(path, b"OWNED UNISSUED TRANSPORT FIXTURE")
    assert path.read_bytes() == b"FOREIGN REPLACEMENT TRANSPORT FIXTURE"
    assert backup.read_bytes() == b"OWNED UNISSUED TRANSPORT FIXTURE"


def test_linked_output_ancestor_is_rejected_before_any_write(writer):
    root, directory, path = writer
    other = root / "other"
    other.mkdir()
    directory.symlink_to(other, target_is_directory=True)
    with pytest.raises(support.WorkingError, match="ancestor"):
        exporter.write_exclusive(path, b"UNISSUED TRANSPORT FIXTURE")
    assert not (other / path.name).exists()


def test_binding_uses_relative_identities_and_is_rechecked_without_observations(state):
    source = inspect.getsource(support.state_binding)
    assert 'WORKING_RELATIVE + "/" + name' in source
    assert "str(path)" not in source and "str(ROOT)" not in source
    assert '"stored_observations_supply_authority": False' in source
    first = support.state_binding(state)
    assert len(first) == 64 and first == support.state_binding(support.load_candidate_state())


def test_rfc_does_not_claim_associativity_admission_or_missing_final_gates():
    text = (HERE / "working-shift-scalar-integration-rfc-v1.md").read_text()
    assert "non-admitted working mathematics" in text
    assert "No associativity" in text
    assert "all seven ordinary gates" in text
    assert "same authenticated" in text
    assert "append tranche is excluded" in text
    assert "no temporary" in text
