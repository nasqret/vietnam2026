"""Independent source/inert guards for the separate non-admitted44 cone.

No successful kernel, Lean, replay or admission result is mocked.  A real
final artifact and its fresh proof gates remain separate from these tests.
The complete old37 tree is observed externally for non-mutation; only its
six explicitly selected authority files belong to the new runtime binding.
"""

from __future__ import annotations

import ast
from dataclasses import replace
from hashlib import sha256
import inspect
import json
import os
from pathlib import Path
import stat
import sys
from types import ModuleType, SimpleNamespace

import pytest

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
for directory in (HERE, ROOT / "scripts", ROOT / "peano-lab/py"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import working_divisibility_closure_support as support
import export_working_divisibility_closure as exporter
import check_working_divisibility_closure as checker


NAMES = (
    "prime_field_polynomial_shift_exists",
    "prime_field_polynomial_shift_bounded",
    "prime_field_polynomial_shift_functional",
    "prime_field_polynomial_shift_zero_prefix",
    "polynomial_zero_extended_shift_forward",
    "polynomial_zero_extended_shift_reverse",
    "polynomial_diagonal_term_shift_right_iff",
    "prime_field_convolution_coefficient_shift_right_iff",
    "polynomial_product_length_shift_right_nonempty",
    "prime_field_polynomial_convolution_shift_right_nonempty",
    "prime_field_polynomial_convolution_shift_right_empty",
    "prime_field_polynomial_convolution_shift_right_equivalent",
    "prime_field_polynomial_convolution_shift_right_exists",
    "prime_field_polynomial_shift_power_zero",
    "prime_field_polynomial_shift_power_successor",
    "beta_sum_pointwise_mod_scale",
    "polynomial_zero_extended_scale_congruent",
    "polynomial_diagonal_term_right_scale_congruent",
    "polynomial_diagonal_sum_right_scale_congruent",
    "prime_field_convolution_coefficient_right_scale",
    "prime_field_polynomial_convolution_right_scale",
    "prime_field_polynomial_convolution_right_scale_equal",
    "prime_field_polynomial_convolution_right_scale_exists",
    "prime_field_polynomial_scale_zero_value",
    "prime_field_polynomial_convolution_right_scale_zero",
    "prime_field_polynomial_append_shift_constant_add",
    "prime_field_polynomial_append_shift_constant_decomposition_exists",
    "prime_field_convolution_coefficient_right_append_add",
    "prime_field_polynomial_shift_scale_aligned_sum_exists",
    "prime_field_polynomial_convolution_right_append_equivalent",
    "prime_field_polynomial_convolution_right_append_exists",
    "prime_field_polynomial_shift_equivalent_congruent",
    "prime_field_polynomial_convolution_shift_scale_aligned_equivalent",
    "prime_field_polynomial_shift_scale_aligned_congruent",
    "prime_field_polynomial_convolution_associativity_append_step",
    "prime_field_polynomial_nested_empty_right_equivalent",
    "prime_field_polynomial_convolution_associative_equivalent",
    "prime_field_polynomial_right_divides_from_product",
    "prime_field_polynomial_right_divides_divisor_bounded",
    "prime_field_polynomial_right_divides_dividend_bounded",
    "prime_field_polynomial_right_divides_equivalent_target",
    "prime_field_polynomial_right_divides_empty",
    "prime_field_polynomial_right_divides_equivalent_divisor",
    "prime_field_polynomial_right_divides_transitive",
)
PRINCIPALS = (NAMES[12], NAMES[22], NAMES[24], NAMES[27], NAMES[30],
              *NAMES[38:44])
SPECS_SHA256 = "6ecade7114e2d718b6a564a19d98c981b0236e1e6c6e622caaa0dff43fc95129"
PRIOR37_SPECS_SHA256 = "de95fea3806bc6c227c032bf2c29095ce191e27624c2196bd417df6c77c31491"
DIVISIBILITY7_SPECS_SHA256 = "2ee9efd3344ef213b2170f080ff541ca0a7a45a018ace9f2f7912cd301bc8bce"
# through, inherited rows, theorem rows, theorem edges, packaged nodes/edges.
PHASES = ((43, 248, 291, 827, 292, 838), (44, 248, 292, 835, 293, 846))
NEW_CANONICAL_TARGETS = (
    ("matrix_rank_bounded_prefix_empty", ("matrix_rank_no_index_below_zero",),
     "cf8f846bcc8bebac874164f0347cea5021f8c5e756c53b872c8db186f4f1fb5c"),
    ("prime_field_polynomial_convolution_empty", ("lt_not_le", "zero_le"),
     "c3acf6e9ccf0a8030b8c5a7efdb0c524c96e8fd76a5a04210f6a4a64bd801bc4"),
)


def _specs_digest(rows):
    value = sha256()
    for row in rows:
        fields = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        value.update((json.dumps(fields, ensure_ascii=True, separators=(",", ":")) + "\n").encode())
    return value.hexdigest()


def _authority_modules():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(("peano_lab.library.editions_v", "check_alpha_",
                                "build_peano_library_channels", "verify_peano_library_channels"))}


def _forbid(*_args, **_kwargs):
    pytest.fail("a source-only or rejecting guard reached a proof/Alpha execution seam")


@pytest.fixture(scope="module")
def state():
    before = _authority_modules()
    result = support.load_candidate_state()
    assert _authority_modules() == before
    return result


@pytest.fixture(scope="module")
def selection(state):
    return support.select_support(state)


def test_exact44_source_inventory_preserves37_and_appends_only_the_seven_divisibility_rows(state):
    assert type(state) is support.CandidateState and type(state.rows) is tuple
    assert all(type(row) is support.TheoremSpec for row in state.rows)
    assert tuple(row.name for row in state.rows) == NAMES
    assert state.specs_sha256 == _specs_digest(state.rows) == SPECS_SHA256
    assert _specs_digest(state.rows[:37]) == PRIOR37_SPECS_SHA256
    assert _specs_digest(state.rows[37:]) == DIVISIBILITY7_SPECS_SHA256
    assert sum(len(row.dependencies) for row in state.rows) == 199
    assert sum(len(row.script) for row in state.rows) == 4790
    assert support.PRINCIPAL_ROOTS == PRINCIPALS and len(set(PRINCIPALS)) == 11


@pytest.mark.parametrize("through,ancestors,total,theorem_edges,nodes,edges", PHASES,
                         ids=("through43", "through44"))
def test_two_stages_are_exact_dependency_complete_source_ordered_cones(
        state, through, ancestors, total, theorem_edges, nodes, edges):
    before = _authority_modules()
    chosen = support.select_support(state, NAMES[:through])
    assert chosen.through == through and chosen.owned == state.rows[:through]
    assert len(chosen.canonical_support) == ancestors and len(chosen.complete_specs) == total
    assert len({row.name for row in chosen.complete_specs}) == total and total + 1 == nodes
    assert not {row.name for row in chosen.canonical_support}.intersection(NAMES)
    assert {row.name for row in chosen.complete_specs} == (
        {row.name for row in chosen.canonical_support} | set(NAMES[:through]))
    assert sum(len(row.dependencies) for row in chosen.complete_specs) == theorem_edges
    consumed = {name for row in chosen.complete_specs for name in row.dependencies}
    assert chosen.root_names == tuple(row.name for row in chosen.complete_specs if row.name not in consumed)
    assert len(chosen.root_names) == 11 and theorem_edges + len(chosen.root_names) == edges
    assert set(chosen.root_names) <= set(NAMES[:through])
    seen = set()
    for row in chosen.complete_specs:
        assert type(row.dependencies) is tuple and len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= seen
        seen.add(row.name)
    assert _authority_modules() == before


def test_transitivity_is_the_only_stage44_addition_and_has_no_new_canonical_prerequisite(state, selection):
    earlier = support.select_support(state, NAMES[:43])
    assert earlier.canonical_support == selection.canonical_support
    assert selection.complete_specs == (*earlier.complete_specs, state.rows[-1])
    assert tuple(state.rows[-1].dependencies) == (
        "prime_nonzero", "prime_field_polynomial_convolution_bounded",
        "polynomial_product_length_exists", "prime_field_polynomial_convolution_at_length_exists",
        "prime_field_polynomial_right_divides_from_product",
        "prime_field_polynomial_equivalent_transitive",
        "prime_field_polynomial_convolution_associative_equivalent",
        "prime_field_polynomial_convolution_equivalent_congruent_right",
    )
    assert selection.root_names == PRINCIPALS
    assert earlier.root_names == (*PRINCIPALS[:5], NAMES[36], *PRINCIPALS[5:-1])


def test_exact_two_new_canonical_targets_are_source_rows_not_new_working_ownership(state, selection):
    prior = support.prior.select_support(support.prior.load_candidate_state())
    old_names = {row.name for row in prior.complete_specs}
    added = tuple(row for row in selection.canonical_support if row.name not in old_names)
    assert tuple((row.name, row.dependencies, sha256(row.statement.encode()).hexdigest())
                 for row in added) == NEW_CANONICAL_TARGETS
    assert len(prior.canonical_support) == 246 and len(selection.canonical_support) == 248


@pytest.mark.parametrize("count", (0, 1, 25, 32, 34, 35, 37, 38, 41, 42, 45))
def test_no_unapproved_source_prefix_can_be_selected(count, state):
    names = NAMES[:count] if count <= 44 else (*NAMES, "foreign")
    with pytest.raises(ValueError):
        support.select_support(state, names)


@pytest.mark.parametrize("bad", ([], "all", {}, True, (True,), (1,), ("missing",),
                                 tuple(reversed(NAMES)), (NAMES[0],) * 44),
                         ids=("list", "text", "mapping", "bool", "bool-name", "int-name",
                              "foreign-name", "reverse", "duplicate"))
def test_owned_inventory_requires_exact_ordered_distinct_source_names(bad, state):
    with pytest.raises(ValueError):
        support.select_support(state, bad)


@pytest.mark.parametrize("index", range(44), ids=lambda index: f"row{index:02d}")
def test_each_working_target_is_bound_before_source_selection(index, state):
    changed = list(state.rows)
    changed[index] = replace(changed[index], statement="0=1")
    with pytest.raises(ValueError):
        support.select_support(replace(state, rows=tuple(changed)))


@pytest.mark.parametrize("field", ("name", "dependencies", "script", "summary"))
@pytest.mark.parametrize("index", (0, 24, 25, 36, 37, 42, 43), ids=lambda index: f"boundary{index:02d}")
def test_nonstatement_fields_are_bound_across_old25_old37_new7_and_stage_boundaries(index, field, state):
    row = state.rows[index]
    values = {"name": "foreign_working_row", "dependencies": ("foreign_dependency",),
              "script": ("exact foreign",), "summary": row.summary + " changed"}
    changed = list(state.rows)
    changed[index] = replace(row, **{field: values[field]})
    with pytest.raises(ValueError):
        support.select_support(replace(state, rows=tuple(changed)))


@pytest.mark.parametrize("bad", (None, {}, (), SimpleNamespace(rows=(), specs_sha256="a" * 64)),
                         ids=("none", "mapping", "tuple", "foreign-object"))
def test_foreign_state_objects_cannot_supply_the44_source_inventory(bad):
    with pytest.raises(ValueError):
        support.select_support(bad)


@pytest.mark.parametrize("fault", ("missing", "extra", "list", "digest", "foreign-row"))
def test_state_count_container_digest_and_row_types_are_exact(fault, state):
    if fault == "missing": changed = replace(state, rows=state.rows[:-1])
    elif fault == "extra": changed = replace(state, rows=(*state.rows, state.rows[0]))
    elif fault == "list": changed = replace(state, rows=list(state.rows))
    elif fault == "digest": changed = replace(state, specs_sha256="0" * 64)
    else:
        row = state.rows[0]
        foreign = SimpleNamespace(name=row.name, statement=row.statement,
                                  dependencies=row.dependencies, script=row.script, summary=row.summary)
        changed = replace(state, rows=(foreign, *state.rows[1:]))
    with pytest.raises(ValueError):
        support.select_support(changed)


@pytest.mark.parametrize("index", range(7), ids=lambda index: f"factory{index}")
def test_seven_factories_reconcile_actual_prior37_and_literal_new7_source_test_bytes(index, state):
    owner = support.FACTORIES[index]
    assert type(owner) is support.Factory
    if index < 6:
        assert owner == support.prior.FACTORIES[index]
    else:
        assert (owner.directory, owner.module, owner.count, owner.source_bytes, owner.source_sha256,
                owner.test_bytes, owner.test_sha256, owner.specs_sha256) == (
            "research/arithmetic-library/working/prime-field-divisibility-v1",
            "prime_field_polynomial_divisibility_candidate", 7, 15168,
            "f544adedd3ce963e4a773e8582efcb0f91ba7491207c9792d477d452e854f2b8", 20043,
            "82460849735222acb22c120004226a9e0a91c0231f8ab960cc3657f0767400e3",
            DIVISIBILITY7_SPECS_SHA256,
        )
    for pin, filename in ((owner.source, owner.module + ".py"),
                          (owner.test, "test_" + owner.module + ".py")):
        assert pin.path == owner.directory + "/" + filename
        raw = (ROOT / pin.path).read_bytes()
        assert (len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256)
    start = sum(value.count for value in support.FACTORIES[:index])
    assert _specs_digest(state.rows[start:start + owner.count]) == owner.specs_sha256


def test_the_entire_prior37_source_prefix_is_exact_and_never_reclassified_as_canonical(state, selection):
    old = support.prior.load_candidate_state()
    assert state.rows[:37] == old.rows
    assert not {row.name for row in old.rows}.intersection(row.name for row in selection.canonical_support)
    assert tuple(row.name for row in selection.owned[:37]) == NAMES[:37]


@pytest.mark.parametrize("index", range(11), ids=lambda index: f"principal{index:02d}")
def test_every_selected_ordinary_principal_is_an_exact_maximal_source_target(index, state, selection):
    assert selection.root_names == PRINCIPALS
    row = next(row for row in state.rows if row.name == PRINCIPALS[index])
    assert sha256(row.statement.encode()).hexdigest() == support.PRINCIPAL_STATEMENT_SHA256[index]
    assert len(support.PRINCIPAL_STATEMENT_SHA256) == 11
    assert row.name not in {name for item in selection.complete_specs for name in item.dependencies}


@pytest.mark.parametrize("field,value", (("count", 6), ("source_bytes", True),
    ("source_sha256", "0" * 64), ("test_bytes", 1), ("test_sha256", "1" * 64),
    ("specs_sha256", "2" * 64), ("module", "foreign"), ("directory", "../foreign")))
def test_every_new_factory_ownership_field_is_required_before_source_execution(field, value, monkeypatch):
    owners = list(support.FACTORIES)
    owners[-1] = replace(owners[-1], **{field: value})
    monkeypatch.setattr(support, "FACTORIES", tuple(owners))
    with pytest.raises(ValueError):
        support.load_candidate_state()


@pytest.mark.parametrize("fault", ("missing", "duplicate", "reverse", "list"))
def test_factory_inventory_cannot_omit_repeat_reorder_or_retype_working_sources(fault, monkeypatch):
    owners = support.FACTORIES
    if fault == "missing": owners = owners[:-1]
    elif fault == "duplicate": owners = (*owners, owners[-1])
    elif fault == "reverse": owners = owners[::-1]
    else: owners = list(owners)
    monkeypatch.setattr(support, "FACTORIES", owners)
    with pytest.raises(ValueError):
        support.load_candidate_state()


@pytest.mark.parametrize("bad", (None, True, False, 37, 42, 45, 43.0, "43", -1))
def test_stage_policy_requires_exact_integers43_or44(bad):
    with pytest.raises(ValueError):
        support.stage_metrics(bad)


def test_exact_stage_metrics_leave_original_bundle_limits_unchanged():
    assert support.PHASES == (43, 44)
    assert support.stage_metrics(43) == (291, 827, 11)
    assert support.stage_metrics(44) == (292, 835, 11)
    assert support.CPU_LIMITS == checker.CPU_LIMITS == exporter.CPU_LIMITS == (170, 175)
    assert support.WALL_SECONDS == checker.WALL_SECONDS == exporter.WALL_SECONDS == 180
    assert support.MAX_RSS_BYTES == 1536 * 1024 * 1024
    assert support.MAX_BYTES == support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes == 64000000
    assert support.MAX_CATALOG_BYTES == 64 * 1024 * 1024
    assert support.MAX_BYTES < support.closure.PARENT_CATALOG_BYTES <= support.MAX_CATALOG_BYTES


@pytest.mark.parametrize("bad", (None, "true", 0, 1, [], {}))
def test_final_binding_flag_is_not_a_truthy_receipt_surrogate(bad, state):
    with pytest.raises(ValueError):
        support.state_binding(state, final=bad)


@pytest.mark.parametrize("bad", (None, {}, True, SimpleNamespace(path="saved-receipt.json")),
                         ids=("missing", "saved-object", "bool", "foreign-object"))
@pytest.mark.parametrize("task", ("metadata", "bundle", "root"))
def test_missing_or_receipt_like_final_inventory_never_reaches_original_proof_gates(bad, task, monkeypatch):
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", bad)
    monkeypatch.setattr(support, "require_parent_registration", _forbid)
    monkeypatch.setattr(support.closure, "check_bottom_layer_bundle", _forbid)
    function = {"metadata": checker.global_metadata_report, "bundle": checker.verify_complete_bundle,
                "root": lambda: checker.verify_principal(PRINCIPALS[-1])}[task]
    with pytest.raises(ValueError):
        function()


@pytest.mark.parametrize("bad", (None, True, 1, "", "../root", NAMES[0], NAMES[36], "all"))
def test_only_the_eleven_exact_roots_can_request_a_final_ordinary_replay(bad, monkeypatch):
    monkeypatch.setattr(checker, "_load_final", _forbid)
    with pytest.raises(ValueError):
        checker.verify_principal(bad)


def test_novelty_is_actual_parsed_ast_comparison_not_source_text_or_a_saved_report():
    first = support.TheoremSpec("first", "forall x. x=x", (), ("intro x", "refl"), "inert syntax")
    alias = replace(first, name="alias", statement="forall y. y=y")
    other = replace(first, name="different", statement="forall y. y=0")
    assert checker._novelty_pairs((first, alias), (other,)) == (("alias", "first"),)
    assert checker._novelty_pairs((first,), (alias,)) == (("first", "alias"),)
    assert checker._novelty_pairs((first,), (other,)) == ()


def _calls(function, name):
    return [node for node in ast.walk(ast.parse(inspect.getsource(function)))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == name]


def test_full_kernel_gate_precedes_compiled_lean_on_the_same_original_complete_payload():
    source = inspect.getsource(checker.verify_complete_bundle)
    assert source.index("check_bottom_layer_bundle(") < source.index("independent._lean_check(")
    assert "independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)" in source
    assert "receipt.kernel_calls == pin.nodes" in source and "receipt.total_body_nodes == pin.body_nodes" in source
    assert "_rebind(before)" in source
    calls = _calls(checker.verify_complete_bundle, "check_bottom_layer_bundle")
    assert len(calls) == 1 and len(calls[0].args) == 3 and calls[0].keywords == []
    decoding = [node for node in ast.walk(ast.parse(inspect.getsource(checker._load_final)))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "decode_proof_bundle"]
    assert len(decoding) == 1 and len(decoding[0].args) == 1 and decoding[0].keywords == []


def test_ordinary_replay_is_followed_by_the_original_exact_empty_context_ha_check():
    source = inspect.getsource(checker.verify_principal)
    assert source.index("replay_bottom_layer_theorem(") < source.index("check((), proof.certificate, formula)")
    assert "proof.spec == exact and proof.formula == formula" in source
    assert "_rebind(before)" in source
    calls = _calls(checker.verify_principal, "replay_bottom_layer_theorem")
    assert len(calls) == 1 and len(calls[0].args) == 4 and calls[0].keywords == []


def test_every_final_gate_rechecks_registered_bytes_before_returning_its_own_report():
    source = inspect.getsource(checker._rebind)
    assert source.index("require_final_inventory()") < source.index("state_binding(")
    for function in (checker.global_metadata_report, checker.verify_complete_bundle, checker.verify_principal):
        assert "_rebind(before)" in inspect.getsource(function)


def test_only_novelty_loads_the_current4092_catalogue_and_it_compares_the_whole_inherited_cone():
    for function in (support.load_candidate_state, support.select_support, support.execution_selection,
                     exporter.export_authoring_bundle, checker._load_final, checker.verify_complete_bundle,
                     checker.verify_principal):
        source = inspect.getsource(function)
        assert "load_catalog(" not in source and "import editions_v" not in source
    source = inspect.getsource(checker.global_metadata_report)
    assert 'len(catalog["theorems"]) == 4092' in source
    assert "all(parent.get(row.name) == row for row in selected.support)" in source
    assert "_novelty_pairs(state.rows, parent_rows)" in source


def test_original_process_limits_are_set_before_loading_proof_inputs():
    for module in (exporter, checker):
        source = Path(module.__file__).read_text()
        assert source.index("resource.setrlimit(resource.RLIMIT_CPU, (170, 175))") < source.index(
            "import working_divisibility_closure_support")
        assert "signal.alarm(180)" in source and "authoring_rss_bytes()" in source
        for forbidden in ("setrecursionlimit", "settrace", "setprofile", "fuel=", "max_nodes=", "--receipt", "--skip"):
            assert forbidden not in source


@pytest.mark.parametrize("args", (("--task", "root"), ("--task", "bundle", "--name", PRINCIPALS[0]),
                                  ("--task", "bundle", "--through", "43"),
                                  ("--task", "bundle", "--receipt", "saved.json")))
def test_final_cli_has_no_partial_prefix_or_saved_receipt_acceptance_mode(args, monkeypatch):
    monkeypatch.setattr(checker, "verify_complete_bundle", _forbid)
    monkeypatch.setattr(checker, "verify_principal", _forbid)
    with pytest.raises(SystemExit) as error:
        checker.main(list(args))
    assert error.value.code == 2


def test_roles_and_local_report_keep_prior37_new7_and_canonical248_distinct(selection, monkeypatch):
    for row in selection.owned[:37]:
        assert selection.role(row.name) == "prior_non_admitted_associativity"
    for row in selection.owned[37:]:
        assert selection.role(row.name) == "new_non_admitted_divisibility"
    for row in selection.canonical_support:
        assert selection.role(row.name) == "inherited_canonical_source"
    with pytest.raises(ValueError):
        selection.role("foreign")
    for name in ("parent_snapshot", "check_bottom_layer_bundle", "replay_bottom_layer_theorem"):
        monkeypatch.setattr(support.closure, name, _forbid)
    before = _authority_modules()
    report = support.local_manifest()
    assert (report["non_admitted_rows"], report["previous_non_admitted_rows"],
            report["additional_non_admitted_rows"]) == (44, 37, 7)
    assert (report["packaged_nodes"], report["packaged_edges"]) == (293, 846)
    assert report["ordinary_principals"] == list(PRINCIPALS)
    assert report["prior37_authority_file_count"] == 6
    for key in ("global_current4092_novelty_checked", "original_ha_checked", "independent_lean_checked",
                "ordinary_principals_checked", "complete_checkpoint_acceptance", "gcd_bezout_proved",
                "full_G091_proved", "alpha_admission_performed", "stable_admission_performed",
                "complete_prior37_tree_bound"):
        assert report[key] is False
    assert _authority_modules() == before


@pytest.mark.parametrize("index", range(7), ids=lambda index: f"factory{index}")
def test_preexisting_private_math_slots_are_never_replaced(index, monkeypatch):
    name = "_working_divisibility_closure_v1_" + support.FACTORIES[index].module
    foreign = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, foreign)
    with pytest.raises(ValueError):
        support.load_candidate_state()
    assert sys.modules[name] is foreign


def test_genuine_prior37_controller_uses_only_a_temporary_private_module_slot():
    name = support._PRIVATE_PRIOR_NAME
    assert name not in sys.modules and not name.startswith("peano_lab.")
    before = _authority_modules()
    controller = support._load_prior_support()
    assert type(controller) is ModuleType and controller.__name__ == name
    assert controller.__file__ == str(ROOT / support.PRIOR37_SUPPORT_PIN.path)
    assert name not in sys.modules and _authority_modules() == before


def test_existing_private_prior_controller_is_preserved_on_rejection(monkeypatch):
    name = support._PRIVATE_PRIOR_NAME
    foreign = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, foreign)
    with pytest.raises(ValueError):
        support._load_prior_support()
    assert sys.modules[name] is foreign


def test_failed_private_prior_execution_cleans_only_its_own_slot(monkeypatch):
    class Rejected(Exception):
        pass
    def reject(*_args, **_kwargs):
        raise Rejected("deliberate source-execution failure")
    monkeypatch.setattr(support, "exec", reject, raising=False)
    with pytest.raises(Rejected):
        support._load_prior_support()
    assert support._PRIVATE_PRIOR_NAME not in sys.modules


def test_private_prior_loader_preserves_a_foreign_replacement(monkeypatch):
    name = support._PRIVATE_PRIOR_NAME
    assert name not in sys.modules
    foreign = ModuleType(name)
    def replace_and_reject(*_args, **_kwargs):
        sys.modules[name] = foreign
        raise RuntimeError("deliberate test-owned replacement")
    monkeypatch.setattr(support, "exec", replace_and_reject, raising=False)
    try:
        with pytest.raises(ValueError, match="preserved, not deleted"):
            support._load_prior_support()
        assert sys.modules[name] is foreign
    finally:
        if sys.modules.get(name) is foreign:
            del sys.modules[name]


@pytest.mark.parametrize("fault", ("file", "origin", "factory", "type"))
def test_canonical_factory_origin_cannot_be_supplied_by_a_foreign_module(fault, monkeypatch):
    short = "prime_field_polynomial_convolution_candidate"
    name = "peano_lab.library." + short
    path = str(ROOT / "peano-lab/py/peano_lab/library" / (short + ".py"))
    foreign = ModuleType(name) if fault != "type" else SimpleNamespace()
    foreign.__file__ = "/foreign/source.py" if fault == "file" else path
    foreign.__spec__ = SimpleNamespace(origin="/foreign/source.py" if fault == "origin" else path)
    setattr(foreign, "make_" + short + "_theorems", _forbid)
    monkeypatch.setitem(sys.modules, name, foreign)
    with pytest.raises(ValueError):
        support.canonical_provider_table()
    assert sys.modules[name] is foreign


@pytest.mark.parametrize("fault", ("missing", "extra", "list", "size", "digest", "path", "provider"))
def test_inherited_runtime_identity_cannot_be_shortened_retyped_or_redirected(fault, monkeypatch):
    pins = support.RUNTIME_PINS
    if fault == "missing": pins = pins[:-1]
    elif fault == "extra": pins = (*pins, pins[-1])
    elif fault == "list": pins = list(pins)
    elif fault == "size": pins = (*pins[:-1], replace(pins[-1], bytes=True))
    elif fault == "digest": pins = (*pins[:-1], replace(pins[-1], sha256="0" * 64))
    elif fault == "path": pins = (*pins[:-1], replace(pins[-1], path="../foreign"))
    else: monkeypatch.setattr(support, "PROVIDER_MODULES", support.PROVIDER_MODULES[:-1])
    monkeypatch.setattr(support, "RUNTIME_PINS", pins)
    with pytest.raises(ValueError):
        support.require_runtime_sources()


PRIOR37_FILE_EXPECTATIONS = (
    ("working_associativity_closure_support.py", 32690,
     "be7ba45515dcbfab85cf0b7fe4c17805f9cc1d6e1baf9f975f061eeee7265694"),
    ("export_working_associativity_closure.py", 9110,
     "76d7e186bf49841b50ee2bb2b1cb203c2d5ef3584d3e8249625cfae634df14b7"),
    ("check_working_associativity_closure.py", 12595,
     "05a80d253130cb45b15fe42a3e2187fc7a2674973267f363576c98868cacb4b6"),
    ("test_working_associativity_closure.py", 43298,
     "1caa4ad399fc9704d9186a4290ceb10f18fe142df1f07df7fec5861fcd03dc41"),
    ("working-associativity-closure-rfc-v1.md", 10179,
     "aa043aed3bf93c150a092a9cac7499d410ef9bc6a17e3b80143a4e5b5986560b"),
    ("artifacts/working-associativity-closure-prefix-37-proof-bundle-v1.json", 1581355,
     "60f0f96f6966fd40df51276b2cbae250ab69aae4cc9d16283e1bed4776bef000"),
)


def test_prior37_authority_is_exactly_five_controls_and_one_real_artifact_not_its_observations():
    prefix = "research/arithmetic-library/working/prime-field-associativity-closure-v1/"
    assert tuple((pin.path, pin.bytes, pin.sha256) for pin in support.PROTECTED_PRIOR37_PINS) == tuple(
        (prefix + name, size, digest) for name, size, digest in PRIOR37_FILE_EXPECTATIONS)
    assert len(support.PROTECTED_PRIOR37_PINS) == 6
    assert all(not pin.path.endswith("README.md") and "observations" not in pin.path
               and "independent-source-guards" not in pin.path for pin in support.PROTECTED_PRIOR37_PINS)
    support.require_preserved_archives()
    for pin in support.PROTECTED_PRIOR37_PINS:
        raw = (ROOT / pin.path).read_bytes()
        assert (len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256)
    # Full accepted25 preservation remains in the unchanged prior37 helper.
    assert len(support.prior.PRIOR25_PINS) == 11
    assert sum(pin.bytes for pin in support.prior.PRIOR25_PINS) == 871810
    rows = sorted([pin.path, pin.bytes, pin.sha256] for pin in support.prior.PRIOR25_PINS)
    assert sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest() == (
        "fe38b987cf5eca80fcd9ddc48926f6dc3aa0ba2c396e5151b851b75cf7beba2f")


@pytest.mark.parametrize("fault", ("missing", "extra", "list", "digest", "source-role"))
def test_prior37_authority_pin_inventory_cannot_change(fault, monkeypatch):
    pins = support.PROTECTED_PRIOR37_PINS
    if fault == "missing": pins = pins[:-1]
    elif fault == "extra": pins = (*pins, pins[0])
    elif fault == "list": pins = list(pins)
    elif fault == "digest": pins = (*pins[:-1], replace(pins[-1], sha256="0" * 64))
    else: monkeypatch.setattr(support, "PRIOR37_SUPPORT_PIN", pins[-1])
    monkeypatch.setattr(support, "PROTECTED_PRIOR37_PINS", pins)
    with pytest.raises(ValueError):
        support.require_preserved_archives()


@pytest.mark.parametrize("index", range(6), ids=lambda index: f"authority-file{index}")
def test_every_selected_prior37_file_is_really_read_and_checked(index, tmp_path, monkeypatch):
    shadow = tmp_path.resolve()
    for pin in support.PROTECTED_PRIOR37_PINS:
        target = shadow / pin.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / pin.path).read_bytes())
    changed = shadow / support.PROTECTED_PRIOR37_PINS[index].path
    changed.write_bytes(changed.read_bytes() + b"\nchanged inert copy\n")
    monkeypatch.setattr(support, "ROOT", shadow)
    with pytest.raises(ValueError):
        support.require_preserved_archives()


@pytest.mark.parametrize("kind", ("symlink", "fifo", "directory"))
def test_prior37_protected_artifact_cannot_be_a_link_special_file_or_directory(kind, tmp_path, monkeypatch):
    shadow = tmp_path.resolve()
    for pin in support.PROTECTED_PRIOR37_PINS[:-1]:
        target = shadow / pin.path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / pin.path).read_bytes())
    pin = support.PROTECTED_PRIOR37_PINS[-1]
    path = shadow / pin.path
    path.parent.mkdir(parents=True, exist_ok=True)
    if kind == "symlink": path.symlink_to(ROOT / pin.path)
    elif kind == "fifo": os.mkfifo(path)
    else: path.mkdir()
    monkeypatch.setattr(support, "ROOT", shadow)
    with pytest.raises(ValueError):
        support.require_preserved_archives()


def test_prior37_runtime_subset_guard_still_delegates_actual_old25_full_archive_rejection(monkeypatch):
    class Rejected(Exception):
        pass
    def reject():
        raise Rejected("old25 preservation deliberately rejected")
    monkeypatch.setattr(support.prior, "require_preserved_archives", reject)
    with pytest.raises(Rejected):
        support.require_preserved_archives()


def test_current_parent_identity_fields_are_exact_before_original_parent_validation(monkeypatch):
    fields = ("PARENT_CATALOG_PINS", "PARENT_CHANNEL_PIN", "PARENT_IDENTITY_SHA256",
              "PARENT_ENROLLMENT_SHA256")
    for field in fields:
        with monkeypatch.context() as scoped:
            scoped.setattr(support, field, None)
            scoped.setattr(support.prior, "require_parent_registration", _forbid)
            with pytest.raises(ValueError):
                support.require_parent_registration()


SEED_EXPECTATIONS = (
    ("research/arithmetic-library/working/prime-field-associativity-closure-v1/artifacts/"
     "working-associativity-closure-prefix-37-proof-bundle-v1.json", 1581355,
     "60f0f96f6966fd40df51276b2cbae250ab69aae4cc9d16283e1bed4776bef000"),
    ("research/arithmetic-library/artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json", 688987,
     "6e3a08c73b8a45de127e6d50a771f95b52fd54894b1c2e43468751421488a01a"),
    ("research/arithmetic-library/artifacts/lower-continuation-polynomial-products-proof-bundle-v1.json", 745307,
     "55f12903e1b1d3b4832f6c728cb366c20868c4e88810a736316b30cddf01dde3"),
)


def test_stage43_uses_three_exact_real_seeds_and_stage44_only_its_actual_predecessor():
    assert tuple((pin.path, pin.bytes, pin.sha256) for pin in support.SEED_PINS) == SEED_EXPECTATIONS
    assert support.SEED_PINS == (support.PRIOR37_SEED, support.POLYNOMIAL_SEED, support.PRODUCTS_SEED)
    paths = {n: support.ARTIFACT_DIRECTORY / f"working-divisibility-closure-prefix-{n}-proof-bundle-v1.json"
             for n in (43, 44)}
    assert support.stage_path(43) == paths[43] and support.stage_path(44) == paths[44]
    assert support.required_seed_paths(43) == tuple(ROOT / path for path, _size, _sha in SEED_EXPECTATIONS)
    assert support.required_seed_paths(44) == (paths[43],)


@pytest.mark.parametrize("through", (43, 44))
@pytest.mark.parametrize("fault", ("empty", "reverse-or-extra", "foreign", "duplicate", "list"))
def test_wrong_seed_sequence_is_rejected_before_original_seed_validation(through, fault, monkeypatch):
    actual = support.required_seed_paths(through)
    if fault == "empty": paths = ()
    elif fault == "reverse-or-extra": paths = actual[::-1] if len(actual) > 1 else (*actual, actual[0])
    elif fault == "foreign": paths = (*actual[:-1], ROOT / "foreign.json")
    elif fault == "duplicate": paths = (*actual, actual[0])
    else: paths = list(actual)
    monkeypatch.setattr(support.closure, "_validate_seeds", _forbid)
    with pytest.raises(ValueError):
        support.seed_inventory(paths, through=through)


@pytest.mark.parametrize("fault", ("missing", "extra", "list", "digest", "role"))
def test_literal_seed_registry_and_named_roles_cannot_diverge(fault, monkeypatch):
    pins = support.SEED_PINS
    if fault == "missing": pins = pins[:-1]
    elif fault == "extra": pins = (*pins, pins[0])
    elif fault == "list": pins = list(pins)
    elif fault == "digest": pins = (replace(pins[0], sha256="0" * 64), *pins[1:])
    else: monkeypatch.setattr(support, "PRIOR37_SEED", support.POLYNOMIAL_SEED)
    monkeypatch.setattr(support, "SEED_PINS", pins)
    with pytest.raises(ValueError):
        support.require_seed_identities()


def test_real37_polynomial202_and_products210_cover_all285_preexisting_targets_inertly(state, monkeypatch):
    monkeypatch.setattr(support.closure, "check_bottom_layer_bundle", _forbid)
    monkeypatch.setattr(checker, "decode_proof_bundle", _forbid)
    before = _authority_modules()
    chosen = support.select_support(state, NAMES[:43])
    pins = support.seed_inventory(support.required_seed_paths(43), through=43)
    assert pins == support.SEED_PINS
    report = support.seed_coverage(chosen, pins)
    assert report["preexisting_targets"] == report["covered_targets"] == 285
    assert (report["fresh_working_rows"], report["previous_working_rows"], report["through"]) == (6, 37, 43)
    assert report["missing_names"] == []
    assert [row["inert_nodes"] for row in report["seeds"]] == [284, 202, 210]
    assert report["seeds"][0]["covered_targets"] == 283
    assert report["seeds"][1]["newly_covered_names"] == ["matrix_rank_bounded_prefix_empty"]
    assert report["seeds"][2]["newly_covered_names"] == ["prime_field_polynomial_convolution_empty"]
    assert report["raw_json_only"] is True
    assert report["proof_bodies_decoded"] is report["original_ha_checked"] is report["proof_authority"] is False
    assert _authority_modules() == before


@pytest.mark.parametrize("fault", ("target", "premise", "roots", "phase"))
def test_seed_coverage_reconciles_exact_targets_ordered_premises_roots_and_phase(fault, state):
    selected = support.select_support(state, NAMES[:43])
    if fault in ("target", "premise"):
        row = selected.complete_specs[-1]
        altered = replace(row, statement="0=1") if fault == "target" else replace(row, dependencies=())
        selected = replace(selected, complete_specs=(*selected.complete_specs[:-1], altered))
    elif fault == "roots": selected = replace(selected, root_names=())
    else: selected = replace(selected, through=44)
    with pytest.raises(ValueError):
        support.seed_coverage(selected, support.SEED_PINS)


@pytest.mark.parametrize("fault", ("digest", "size", "order", "list", "receipt-object"))
def test_mutated_seed_data_and_saved_report_objects_never_establish_coverage(fault, state):
    selected = support.select_support(state, NAMES[:43])
    pins = support.SEED_PINS
    if fault == "digest": pins = (replace(pins[0], sha256="0" * 64), *pins[1:])
    elif fault == "size": pins = (replace(pins[0], bytes=1), *pins[1:])
    elif fault == "order": pins = pins[::-1]
    elif fault == "list": pins = list(pins)
    else: pins = (SimpleNamespace(**{"path": pins[0].path, "bytes": pins[0].bytes,
                                    "sha256": pins[0].sha256}), *pins[1:])
    with pytest.raises(ValueError):
        support.seed_coverage(selected, pins)


@pytest.mark.parametrize("value", (None, {}, [], ["wrong", 0, [], []],
    ["peano-lab-bundle-v1", True, ["f"], [[24, ["f"], [], []]]],
    ["peano-lab-bundle-v1", 0, ["f"], [[True, ["f"], [], []]]],
    ["peano-lab-bundle-v1", 0, ["f"], [[24, ["f"], [0], []]]],
    ["peano-lab-bundle-v1", 0, ["f"], [[24, ["g"], [], []]]]),
    ids=("none", "object", "empty", "schema", "root-bool", "fuel-bool", "forward-edge", "target"))
def test_malformed_previous_stage_transport_shapes_are_rejected(value):
    with pytest.raises(ValueError):
        support._inert_bundle_metadata(json.dumps(value).encode())


def test_binding_authenticates_all_five_new_controls_and_reports_its_precise_preservation_scope(
        state, tmp_path, monkeypatch):
    expected = ("working_divisibility_closure_support.py", "export_working_divisibility_closure.py",
                "check_working_divisibility_closure.py", "test_working_divisibility_closure.py",
                "working-divisibility-closure-rfc-v1.md")
    assert support.CONTROL_FILES == expected
    before = support.state_binding(state)
    for name in expected:
        (tmp_path / name).write_bytes((HERE / name).read_bytes())
    monkeypatch.setattr(support, "HERE", tmp_path.resolve())
    assert support.state_binding(state) == before
    changed = tmp_path / expected[1]
    changed.write_bytes(changed.read_bytes() + b"\n# deliberately changed inert source copy\n")
    assert support.state_binding(state) != before
    source = inspect.getsource(support.state_binding)
    for name in ("require_working_sources", "require_runtime_sources", "require_preserved_archives",
                 "require_seed_identities", "CONTROL_FILES", "require_parent_registration"):
        assert name in source
    assert '"complete_prior37_tree_bound": False' in source
    assert '"stored_observations_supply_authority": False' in source
    assert '"prior37_authority_files": _PRIOR37_RECORDS' in source


@pytest.mark.parametrize("field,value", (("path", "../old.json"), ("path", "artifacts/old.json"),
    ("bytes", True), ("bytes", 0), ("bytes", 64000001), ("sha256", "G" * 64),
    ("nodes", 292), ("nodes", True), ("edges", 838), ("edges", 0), ("body_nodes", False)))
def test_final_inventory_rejects_stage43_foreign_paths_and_malformed_literal_fields(field, value, monkeypatch):
    pin = checker.ArtifactPin(support.stage_path(44).relative_to(ROOT).as_posix(), 1, "a" * 64, 293, 846, 1)
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", replace(pin, **{field: value}))
    monkeypatch.setattr(support, "require_parent_registration", _forbid)
    with pytest.raises(ValueError):
        checker.require_final_inventory()


@pytest.fixture
def output_scope(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    directory = root / "artifacts"
    directory.mkdir()
    monkeypatch.setattr(exporter, "ARTIFACT_DIRECTORY", directory)
    monkeypatch.setattr(support, "ARTIFACT_DIRECTORY", directory)
    monkeypatch.setattr(support, "ROOT", root)
    return directory, support.stage_path(43)


@pytest.mark.parametrize("kind", ("wrong-old37-shape", "symlink", "fifo", "hardlink", "foreign-owner"))
def test_previous_stage44_input_must_be_an_actual_owned_regular_stage43_inventory(kind, output_scope, monkeypatch):
    directory, path = output_scope
    actual_old = ROOT / SEED_EXPECTATIONS[0][0]
    if kind == "symlink": path.symlink_to(actual_old)
    elif kind == "fifo": os.mkfifo(path)
    else:
        path.write_bytes(actual_old.read_bytes())
        if kind == "hardlink": os.link(path, directory / "test-owned-second-link.json")
        if kind == "foreign-owner":
            actual = os.getuid()
            monkeypatch.setattr(os, "getuid", lambda: actual + 1)
    # Even genuine old37 bytes cannot masquerade as the required new43 stage.
    with pytest.raises(ValueError):
        support.seed_inventory((path,), through=44)


@pytest.mark.parametrize("bad", ("../old.json", "/outside.json", "unissued.json",
                                 "working-divisibility-closure-prefix-37-proof-bundle-v1.json"))
def test_output_cannot_escape_the_two_exact_new_stage_destinations(bad, output_scope):
    directory, _path = output_scope
    value = Path(bad) if bad.startswith("/") else directory / bad
    with pytest.raises(ValueError):
        exporter.destination(value)


@pytest.mark.parametrize("kind", ("file", "directory", "symlink", "fifo"))
def test_existing_destination_is_rejected_before_source_or_proof_work(kind, output_scope, monkeypatch):
    _directory, path = output_scope
    if kind == "file": path.write_bytes(b"existing unissued transport data")
    elif kind == "directory": path.mkdir()
    elif kind == "symlink": path.symlink_to(path.parent / "absent")
    else: os.mkfifo(path)
    monkeypatch.setattr(support, "load_candidate_state", _forbid)
    monkeypatch.setattr(support.closure, "assemble_bottom_layer_bundle", _forbid)
    with pytest.raises(ValueError):
        exporter.export_authoring_bundle(43, path, seed_bundles=())
    assert path.exists() or path.is_symlink()


def test_cross_stage_output_is_rejected_before_even_loading_source_rows(output_scope, monkeypatch):
    monkeypatch.setattr(support, "load_candidate_state", _forbid)
    with pytest.raises(ValueError):
        exporter.export_authoring_bundle(43, support.stage_path(44), seed_bundles=())


def test_output_ancestor_symlink_is_not_followed(output_scope):
    directory, path = output_scope
    actual = directory.parent / "real-directory"
    actual.mkdir()
    directory.rmdir()
    directory.symlink_to(actual, target_is_directory=True)
    with pytest.raises(ValueError):
        exporter.destination(path)
    assert list(actual.iterdir()) == []


def test_output_directory_with_foreign_ownership_is_rejected(output_scope, monkeypatch):
    _directory, path = output_scope
    actual = os.getuid()
    monkeypatch.setattr(os, "getuid", lambda: actual + 1)
    with pytest.raises(ValueError):
        exporter.destination(path)
    assert not path.exists()


def test_exclusive_writer_preserves_unissued_transport_bytes_and_rejects_overwrite(output_scope):
    _directory, path = output_scope
    payload = b"unissued inert transport fixture, not a proof bundle\n"
    exporter.write_exclusive(path, payload)
    assert path.read_bytes() == payload and path.stat().st_nlink == 1
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    with pytest.raises(ValueError):
        exporter.write_exclusive(path, b"replacement must never be written")
    assert path.read_bytes() == payload


def test_failed_writer_removes_only_its_newly_created_owned_inode(output_scope, monkeypatch):
    _directory, path = output_scope
    original, calls = exporter._resources, []
    class Rejected(Exception):
        pass
    def fail_after_write():
        result = original()
        calls.append(result)
        if len(calls) == 2:
            raise Rejected("deliberate post-write rejection")
        return result
    monkeypatch.setattr(exporter, "_resources", fail_after_write)
    with pytest.raises(Rejected):
        exporter.write_exclusive(path, b"unissued disposable transport data")
    assert len(calls) == 2 and not path.exists()


def test_failed_writer_cannot_remove_a_foreign_replacement_inode(output_scope, monkeypatch):
    _directory, path = output_scope
    original, calls, retained = exporter._resources, [], []
    replacement = b"different test-owned inode must be preserved"
    def replace_after_write():
        result = original()
        calls.append(result)
        if len(calls) == 2:
            retained.append(path.open("rb"))
            path.unlink()
            path.write_bytes(replacement)
            raise RuntimeError("deliberate replacement race")
        return result
    monkeypatch.setattr(exporter, "_resources", replace_after_write)
    try:
        with pytest.raises(ValueError, match="refuses to remove"):
            exporter.write_exclusive(path, b"unissued disposable transport data")
        assert path.read_bytes() == replacement
    finally:
        for handle in retained:
            handle.close()


def test_original_assembler_receives_all_actual_seed_paths_and_rechecks_before_output():
    function = exporter.export_authoring_bundle
    source = inspect.getsource(function)
    calls = _calls(function, "assemble_bottom_layer_bundle")
    assert len(calls) == 1 and ast.unparse(calls[0].args[0]) == "execution.frontier"
    assert {keyword.arg for keyword in calls[0].keywords} == {"seed_bundles", "batch_size", "report"}
    assert next(keyword.value.value for keyword in calls[0].keywords if keyword.arg == "batch_size") == 1
    assert source.index("destination(output)") < source.index("load_candidate_state()")
    assert source.index('not coverage["missing_names"]') < source.index("assemble_bottom_layer_bundle(")
    assert "result.receipt.node_count == result.receipt.kernel_calls == expected_nodes + 1" in source
    assert source.index("for pin in seeds:") < source.index("write_exclusive(output, payload)")
    assert source.index("state_binding(support.load_candidate_state())") < source.index("write_exclusive(output, payload)")
    assert "fuel" not in source and "body_checked" not in source
