"""Independent source/inert guards for the separate non-admitted52+43 cone.

No successful HA, Lean, replay or admission result is mocked. These tests
construct actual syntax, compare inert seed targets and attack changed input
boundaries. Seventeen genuine final gates remain mandatory and separate.
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

import working_euclidean_closure_support as support
import export_working_euclidean_closure as exporter
import check_working_euclidean_closure as checker

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
    "polynomial_diagonal_left_unit_first_term",
    "polynomial_diagonal_left_unit_tail_term",
    "polynomial_diagonal_left_unit_natural_sum",
    "prime_field_convolution_coefficient_left_unit",
    "prime_field_polynomial_convolution_left_unit_equal",
    "prime_field_polynomial_convolution_left_unit_equivalent",
    "prime_field_polynomial_convolution_left_unit_exists",
    "prime_field_polynomial_right_divides_reflexive",
    "prime_field_polynomial_bounded_representative_at_length_exists",
    "prime_field_polynomial_common_representatives_same_length",
    "prime_field_polynomial_common_representatives_transport",
    "prime_field_polynomial_common_representatives_at_length_exists",
    "prime_field_polynomial_common_representatives_exists",
    "prime_field_polynomial_common_representatives_functional",
    "prime_field_polynomial_common_representatives_symmetric",
    "prime_field_polynomial_aligned_add_from_common",
    "prime_field_polynomial_aligned_add_bounded",
    "prime_field_polynomial_aligned_add_from_fixed",
    "prime_field_polynomial_aligned_add_transport",
    "prime_field_polynomial_aligned_add_commutative",
    "prime_field_polynomial_aligned_add_functional",
    "prime_field_polynomial_aligned_add_exists",
    "prime_field_polynomial_aligned_add_realize",
    "prime_field_polynomial_aligned_subtract_from_fixed",
    "prime_field_polynomial_aligned_subtract_exists",
    "prime_field_polynomial_aligned_add_cancel_left",
    "prime_field_polynomial_aligned_add_associative",
    "prime_field_polynomial_aligned_subtract_functional",
    "prime_field_polynomial_add_trim_aligned",
    "prime_field_polynomial_division_execution_aligned_identity",
    "prime_field_polynomial_aligned_convolution_left_add",
    "prime_field_polynomial_aligned_convolution_right_add",
    "polynomial_diagonal_left_constant_first_term",
    "polynomial_diagonal_left_constant_natural_sum",
    "prime_field_convolution_coefficient_left_constant",
    "prime_field_polynomial_left_constant_product_to_scale",
    "prime_field_polynomial_scale_to_left_constant_product",
    "prime_field_polynomial_left_constant_product_exists",
    "prime_field_polynomial_division_remainder_length_descent",
    "prime_field_polynomial_division_constant_remainder_empty",
    "prime_field_polynomial_scale_implies_right_divides",
    "prime_field_polynomial_monic_normalization_right_associates",
    "prime_field_polynomial_normalized_right_associate_exists",
    "prime_field_polynomial_right_divides_aligned_add",
    "prime_field_polynomial_right_divides_aligned_subtract",
    "prime_field_polynomial_right_divides_left_product",
    "prime_field_polynomial_common_right_divisor_euclidean_transport",
    "prime_field_polynomial_division_execution_common_right_divisors",
    "prime_field_polynomial_euclidean_backward_coefficient_identity",
    "prime_field_polynomial_bezout_euclidean_backward",
    "prime_field_polynomial_division_execution_bezout_backward",
)

PRINCIPALS = ("prime_field_polynomial_convolution_shift_right_exists", "prime_field_polynomial_convolution_right_scale_exists", "prime_field_polynomial_convolution_right_scale_zero", "prime_field_convolution_coefficient_right_append_add", "prime_field_polynomial_convolution_right_append_exists", "prime_field_polynomial_right_divides_divisor_bounded", "prime_field_polynomial_right_divides_dividend_bounded", "prime_field_polynomial_right_divides_reflexive", "prime_field_polynomial_aligned_subtract_from_fixed", "prime_field_polynomial_aligned_subtract_functional", "prime_field_polynomial_left_constant_product_to_scale", "prime_field_polynomial_division_constant_remainder_empty", "prime_field_polynomial_normalized_right_associate_exists", "prime_field_polynomial_division_execution_common_right_divisors", "prime_field_polynomial_division_execution_bezout_backward",)
SPEC_SHA = "b2b381d67064401d3325b464396c6d156b5fc27a56639f3909dacaa60ae83994"
NAME_SHA = "264f9aaa740b58d792fc3be4890cc292b25500d7475ac7fff78fc910c6cbe54f"
PRIOR52_SPEC_SHA = "c6c4b0610b911d1f17a8b0ef2b6fa4b8f7b79e73e7f1f85f0fe2d6b1a42edc63"
PHASE_RECORDS = ((59, 312, 886, 17,), (68, 324, 917, 17,), (72, 341, 989, 18,), (74, 353, 1022, 19,), (76, 372, 1109, 21,), (82, 378, 1141, 23,), (87, 430, 1316, 21,), (92, 435, 1348, 17,), (93, 436, 1359, 15,), (94, 437, 1366, 15,), (95, 438, 1368, 15,),)
PREVIOUS = {59: 52, 68: 59, 72: 68, 74: 72, 76: 74, 82: 76, 87: 82, 92: 87, 93: 92, 94: 93, 95: 94}
NEW_FACTORY_RECORDS = (
    ("research/arithmetic-library/working/prime-field-alignment-v1/prime_field_polynomial_alignment_candidate.py", 11780, "eb16e2eb02dbd66a7706e616388182992b8cf2e0715818dc1f7748938e7d798e", 7, "76b9c342744170146fcb7898cb5a20154334147578b7e01d059f01b9015d5aec", (("research/arithmetic-library/working/prime-field-alignment-v1/test_prime_field_polynomial_alignment_candidate.py", 30676, "6adbed23a43a393a4988d6eba9323cb09a8777b62b644cb1992ebdf7c6411c8b",),),),
    ("research/arithmetic-library/working/prime-field-aligned-add-v1/prime_field_polynomial_aligned_add_candidate.py", 20704, "a05bb4f5c4230ca05f51690d3ab82e33ff4596af65176874e25fbe38cf87a0db", 9, "b8ce285a000180baef6318db67202fc4fa258ae5bd6aabecfc098236f9588339", (("research/arithmetic-library/working/prime-field-aligned-add-v1/test_prime_field_polynomial_aligned_add_candidate.py", 33347, "6e67b246e1c565e44d721ad92ecb2e273c2e1330d226922af89f762630de2ed8",),),),
    ("research/arithmetic-library/working/prime-field-aligned-algebra-v1/prime_field_polynomial_aligned_algebra_candidate.py", 16013, "a68de84439afb5f6dd87f1d47449c0bce8dd53a66346c00cc1b7645fb80b2390", 4, "0db1ddc08762db5e207469343143a7ead24de983e8f9a21473592a8d6c97d6f4", (("research/arithmetic-library/working/prime-field-aligned-algebra-v1/test_prime_field_polynomial_aligned_algebra_candidate.py", 10321, "11f096addd3afb6301e98d61cf359b833754b29eebd7abf61a9e85b3da06d073",), ("research/arithmetic-library/working/prime-field-aligned-algebra-v1/test_prime_field_polynomial_aligned_algebra_contracts.py", 12694, "09c34419021d60ad8c78ea5b0430bc17a595fb2b3d97469e1e375a5f55697b2d",),),),
    ("research/arithmetic-library/working/prime-field-euclidean-identity-v1/prime_field_polynomial_euclidean_identity_candidate.py", 11235, "8efdcd2abf2143891b79edcb3fc90d7126ae69507c1c631ed33b497172ffdb77", 2, "f992bc15fd84b7f3ba9b0f28c0219cb97a53c47c669a9563b087e7a3c535ab27", (("research/arithmetic-library/working/prime-field-euclidean-identity-v1/test_prime_field_polynomial_euclidean_identity_candidate.py", 31004, "e7225749330ccd9392e584196057ab3a2547856764d25296bee775f9eb62e2c0",),),),
    ("research/arithmetic-library/working/prime-field-aligned-distributivity-v1/prime_field_polynomial_aligned_distributivity_candidate.py", 8518, "7d535939e24fe6d82158c485533b2ff6934f4d897b6141fde6c50b4fec9788ba", 2, "22b9e7ed76b79f0210eee74433a965db62cc5a4b688c3ab2cf0f236b1dca5719", (("research/arithmetic-library/working/prime-field-aligned-distributivity-v1/test_prime_field_polynomial_aligned_distributivity_candidate.py", 22358, "5fa4ff32894dcbe7f2010ae526731e88cbe4c2307e1043b56da326c487c26039",),),),
    ("research/arithmetic-library/working/prime-field-left-constant-v1/prime_field_polynomial_left_constant_candidate.py", 17620, "9a7a4de30f5f389bcabc2e6267a0d2cc5dc5f061059dcea303a0a03dab58509a", 6, "736cd0d7d21f33ac50a189f66a7457909042c83917d9e9cfc2d4932c6fe06836", (("research/arithmetic-library/working/prime-field-left-constant-v1/test_prime_field_polynomial_left_constant_candidate.py", 27847, "cc93a6d0b8d1ff3eae9bc0b16527936301a7a15e13e7baae3cf818a919cc6a60",),),),
    ("research/arithmetic-library/working/prime-field-euclidean-normalization-v1/prime_field_polynomial_euclidean_normalization_candidate.py", 16401, "d2cddfe42dc0d22104dc4e85e95116222914df11ac840d2082a4ff2e462f146f", 5, "815b67478a8c42bd854002317e31ab5e77739551f19516dfc923b7fe66d0ce74", (("research/arithmetic-library/working/prime-field-euclidean-normalization-v1/test_prime_field_polynomial_euclidean_normalization_candidate.py", 29037, "e291538321e9d078a8b0044bacfb50d46b5eea59b2126001a2129c69de342791",),),),
    ("research/arithmetic-library/working/prime-field-euclidean-transport-v1/prime_field_polynomial_euclidean_transport_candidate.py", 18256, "9a589d1749eb38d30d1a24364bc4d66f7df0efb59247527f7831f97557da9c30", 5, "aba201eca067048dc65b5a2f7f6affd415c6ebd639c35bc613503227a65059b8", (("research/arithmetic-library/working/prime-field-euclidean-transport-v1/test_prime_field_polynomial_transport_models.py", 25634, "0c814915ee8b8f6ecc8ffb945699cd4888fa4c4cf86e6b4cb077063407f5cfab",),),),
    ("research/arithmetic-library/working/prime-field-bezout-backward-v1/prime_field_polynomial_bezout_backward_candidate.py", 18747, "c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702", 3, "bbab74ad9d4ecfe3b01e97ab75dccd532fc23e22a5cb275a68963f15dbf57564", (("research/arithmetic-library/working/prime-field-euclidean-transport-v1/test_prime_field_polynomial_transport_models.py", 25634, "0c814915ee8b8f6ecc8ffb945699cd4888fa4c4cf86e6b4cb077063407f5cfab",),),),
)
PRIOR52_RECORDS = (("research/arithmetic-library/working/prime-field-left-unit-closure-v1/working_left_unit_closure_support.py", 31719, "e1374a8d87915bfd72349b675953e5396043704ddb847e435445cc0451e44fc8",), ("research/arithmetic-library/working/prime-field-left-unit-closure-v1/export_working_left_unit_closure.py", 9099, "7e77bfe907ff4804456c62c6bf4076e8939c53e929d6f80dab77d2a3c68fe6df",), ("research/arithmetic-library/working/prime-field-left-unit-closure-v1/check_working_left_unit_closure.py", 12577, "72453c57fc4e138927cb4daeb955bcc0c7292880883c9f496fabe7dc230d9d1b",), ("research/arithmetic-library/working/prime-field-left-unit-closure-v1/test_working_left_unit_closure.py", 53367, "b22b344f95d50fb4cc3305de2529dfead84d1d69870b7f2ac9085c366d9eaeb0",), ("research/arithmetic-library/working/prime-field-left-unit-closure-v1/working-left-unit-closure-rfc-v1.md", 13331, "9ba37f4f1e1d1dc0a0958a917ec38e6b3c1a8951cc8d77876dcf1da0e17297ba",), ("research/arithmetic-library/working/prime-field-left-unit-closure-v1/artifacts/working-left-unit-closure-prefix-52-proof-bundle-v1.json", 1837245, "4051c93175faed973fb3b88d963fdd03f15514e481aab9516d56b7b1e67c44c4",),)
EXTRA_RUNTIME_RECORDS = (("peano-lab/py/peano_lab/library/ha_signed_decode_candidate.py", 10802, "98cd745fe7e75ffabc532bbef491b908550e2dcd0f30295944b126f7748409aa",), ("peano-lab/py/peano_lab/library/prime_field_polynomial_division_candidate.py", 47986, "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2",), ("peano-lab/py/peano_lab/library/prime_field_polynomial_monic_candidate.py", 25658, "3bf93aff71b48a332920b1a6174e44167bf78238caac3b6d35634f3591582eef",), ("peano-lab/py/peano_lab/library/signed_integer_division_candidate.py", 9708, "f9471954bb5e2bd470ae09c08da4b224839c7a29942816f9cf43c8d48cced384",),)
EXTRA_PROVIDERS = ("prime_field_polynomial_subtraction_candidate", "prime_field_polynomial_degree_candidate", "prime_field_polynomial_trim_candidate", "prime_field_polynomial_division_candidate", "prime_field_polynomial_monic_candidate", "finite_sum_pointwise_mod_candidate", "signed_integer_division_candidate",)
CONTROL_NAMES = (
    "working_euclidean_closure_support.py", "export_working_euclidean_closure.py",
    "check_working_euclidean_closure.py", "test_working_euclidean_closure.py",
    "working-euclidean-closure-rfc-v1.md",
)


def _specs_digest(rows):
    result = sha256()
    for row in rows:
        fields = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        result.update((json.dumps(fields, ensure_ascii=True, separators=(",", ":")) + "\n").encode())
    return result.hexdigest()


def _authority_modules():
    return {name: value for name, value in sys.modules.items()
            if name.startswith(("peano_lab.library.editions_v", "check_alpha_",
                                "build_peano_library_channels", "verify_peano_library_channels"))}


def _forbid(*_args, **_kwargs):
    pytest.fail("a source/inert or rejecting test reached a proof/Alpha execution seam")


@pytest.fixture(scope="module")
def state():
    before = _authority_modules()
    result = support.load_candidate_state()
    assert _authority_modules() == before
    assert all("peano_lab.library." + owner.module not in sys.modules for owner in support.FACTORIES)
    assert all("_working_euclidean_closure_v1_" + owner.module not in sys.modules for owner in support.FACTORIES)
    return result


@pytest.fixture(scope="module")
def selections(state):
    return {through: support.select_support(state, NAMES[:through]) for through, *_rest in PHASE_RECORDS}


def test_actual95_sources_preserve_prior52_and_exact_repaired_order(state):
    assert type(state) is support.CandidateState and type(state.rows) is tuple
    assert tuple(row.name for row in state.rows) == NAMES
    assert _specs_digest(state.rows) == state.specs_sha256 == SPEC_SHA
    assert _specs_digest(state.rows[:52]) == PRIOR52_SPEC_SHA
    assert state.rows[:52] == support.prior.load_candidate_state().rows
    assert sha256("\n".join(NAMES).encode()).hexdigest() == NAME_SHA
    assert sum(len(row.dependencies) for row in state.rows) == 436
    assert sum(len(row.script) for row in state.rows) == 10062
    assert tuple(len(row.script) for row in state.rows[-3:]) == (354, 299, 76)
    assert _specs_digest(state.rows[-3:]) == "bbab74ad9d4ecfe3b01e97ab75dccd532fc23e22a5cb275a68963f15dbf57564"


@pytest.mark.parametrize("through,nodes,edges,roots", PHASE_RECORDS)
def test_every_authorized_stage_has_its_exact_source_ordered_closed_cone(through, nodes, edges, roots, selections):
    selected = selections[through]
    assert selected.through == through and tuple(row.name for row in selected.owned) == NAMES[:through]
    assert (len(selected.complete_specs), sum(len(row.dependencies) for row in selected.complete_specs)) == (nodes, edges)
    assert len(selected.support) == nodes - through and len(selected.root_names) == roots
    table = {row.name: row for row in selected.complete_specs}
    seen = set()
    for row in selected.complete_specs:
        assert set(row.dependencies) <= seen
        seen.add(row.name)
    assert seen == set(NAMES[:through]) | {row.name for row in selected.support}
    assert not seen & set(NAMES[through:])
    used = {dep for row in selected.complete_specs for dep in row.dependencies}
    assert selected.root_names == tuple(name for name in NAMES[:through] if name not in used)
    assert support.stage_metrics(through) == (nodes, edges, roots)
    assert support.stage_path(through) == HERE / "artifacts" / (
        "working-euclidean-closure-prefix-" + str(through) + "-proof-bundle-v1.json")
    if through == 95:
        assert selected.root_names == PRINCIPALS and len(selected.support) == 343
        assert (nodes + 1, edges + roots) == (439, 1383)


@pytest.mark.parametrize("index", range(95), ids=lambda i: f"row{i:02d}")
def test_each_actual_working_target_is_bound_before_selection(index, state):
    rows = list(state.rows)
    rows[index] = replace(rows[index], statement="0=0")
    with pytest.raises(ValueError):
        support.validate_state(replace(state, rows=tuple(rows)))


@pytest.mark.parametrize("field", ("name", "dependencies", "script", "summary"))
@pytest.mark.parametrize("index", (0, 51, 52, 59, 68, 72, 74, 76, 82, 87, 92, 93, 94))
def test_all_five_fields_are_bound_across_prior_and_every_new_stage_boundary(index, field, state):
    row = state.rows[index]
    value = {"name": row.name + "_foreign", "dependencies": (), "script": ("refl",),
             "summary": row.summary + " changed"}[field]
    if field == "dependencies" and not row.dependencies:
        value = ("foreign",)
    rows = list(state.rows)
    rows[index] = replace(row, **{field: value})
    with pytest.raises(ValueError):
        support.validate_state(replace(state, rows=tuple(rows)))


@pytest.mark.parametrize("bad", (None, {}, (), SimpleNamespace(rows=(), specs_sha256="a" * 64)))
def test_foreign_state_and_report_objects_do_not_supply_syntax(bad):
    with pytest.raises(ValueError):
        support.validate_state(bad)


@pytest.mark.parametrize("bad", (None, True, 52, 58, 60, 67, 69, 73, 75, 77, 83, 88, 91, 96, "95", 95.0))
def test_only_the_eleven_exact_integer_stage_endpoints_are_allowed(bad):
    with pytest.raises(ValueError):
        support.stage_metrics(bad)


@pytest.mark.parametrize("bad", ((), [], ("foreign",), NAMES[::-1], NAMES[:94] + (NAMES[0],)))
def test_owned_prefix_requires_exact_distinct_names_in_source_order(bad, state):
    with pytest.raises(ValueError):
        support.select_support(state, bad)


@pytest.mark.parametrize("index", range(9), ids=lambda i: f"newfactory{i}")
def test_each_new_source_and_explicit_shared_test_identity_is_actual(index, state):
    expected = NEW_FACTORY_RECORDS[index]
    owner = support.ADDITIONAL_FACTORIES[index]
    assert (owner.source.path, owner.source.bytes, owner.source.sha256, owner.count, owner.specs_sha256,
            tuple((p.path, p.bytes, p.sha256) for p in owner.tests)) == expected
    for pin in (owner.source, *owner.tests):
        raw = (ROOT / pin.path).read_bytes()
        assert (len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256)
    offset = 52 + sum(item[3] for item in NEW_FACTORY_RECORDS[:index])
    assert _specs_digest(state.rows[offset:offset + owner.count]) == expected[4]
    assert owner.factory == "make_" + owner.module + "_theorems"


def test_shared_test_and_separate_algebra_contracts_have_literal_ownership():
    assert support.ADDITIONAL_FACTORIES[7].tests == support.ADDITIONAL_FACTORIES[8].tests
    assert len(support.ADDITIONAL_FACTORIES[2].tests) == 2
    assert support.ADDITIONAL_FACTORIES[2].tests[1].path.endswith(
        "/test_prime_field_polynomial_aligned_algebra_contracts.py")
    paths = [pin.path for owner in support.ADDITIONAL_FACTORIES for pin in owner.tests]
    assert len(paths) == 10 and len(set(paths)) == 9


@pytest.mark.parametrize("field,value", (
    ("count", 2), ("source_bytes", 1), ("source_sha256", "0" * 64),
    ("specs_sha256", "1" * 64), ("tests", ()), ("tests", []),
    ("directory", "../foreign"), ("module", "foreign")))
def test_every_additional_owner_field_is_required_before_source_execution(field, value, monkeypatch):
    changed = replace(support.ADDITIONAL_FACTORIES[-1], **{field: value})
    additions = (*support.ADDITIONAL_FACTORIES[:-1], changed)
    monkeypatch.setattr(support, "ADDITIONAL_FACTORIES", additions)
    monkeypatch.setattr(support, "FACTORIES", (*support.prior.FACTORIES, *additions))
    with pytest.raises(ValueError):
        support.load_candidate_state()


@pytest.mark.parametrize("fault", ("missing", "reordered", "list", "duplicate", "old-as-new"))
def test_complete_factory_ownership_cannot_drop_or_relabel_old52(fault, monkeypatch):
    owners = support.FACTORIES
    if fault == "missing": owners = owners[:-1]
    elif fault == "reordered": owners = owners[::-1]
    elif fault == "list": owners = list(owners)
    elif fault == "duplicate": owners = (*owners, owners[-1])
    else: owners = (*owners[:8], owners[0], *owners[9:])
    monkeypatch.setattr(support, "FACTORIES", owners)
    with pytest.raises(ValueError):
        support.load_candidate_state()


@pytest.mark.parametrize("index", (0, 7, 8, 16))
def test_existing_private_math_owner_is_preserved(index, monkeypatch):
    alias = "_working_euclidean_closure_v1_" + support.FACTORIES[index].module
    foreign = ModuleType(alias)
    monkeypatch.setitem(sys.modules, alias, foreign)
    with pytest.raises(ValueError):
        support.load_candidate_state()
    assert sys.modules[alias] is foreign


def test_actual_prior_controller_is_scoped_private_and_leaves_no_alpha_or_alias():
    before = _authority_modules()
    controller = support._load_prior_support()
    assert controller.__file__ == str(ROOT / support.PRIOR52_SUPPORT_PIN.path)
    assert controller.__name__ == support._PRIVATE_PRIOR_NAME
    assert support._PRIVATE_PRIOR_NAME not in sys.modules
    assert _authority_modules() == before


def test_existing_private_prior_controller_is_not_replaced(monkeypatch):
    foreign = ModuleType(support._PRIVATE_PRIOR_NAME)
    monkeypatch.setitem(sys.modules, support._PRIVATE_PRIOR_NAME, foreign)
    with pytest.raises(ValueError):
        support._load_prior_support()
    assert sys.modules[support._PRIVATE_PRIOR_NAME] is foreign


def test_failed_prior_execution_cleans_only_owned_slot(monkeypatch):
    class Rejected(Exception):
        pass
    def reject(*_args):
        raise Rejected("intentional controller execution rejection")
    monkeypatch.setattr(support, "exec", reject, raising=False)
    with pytest.raises(Rejected):
        support._load_prior_support()
    assert support._PRIVATE_PRIOR_NAME not in sys.modules


def test_foreign_replacement_of_private_controller_is_preserved(monkeypatch):
    foreign = ModuleType(support._PRIVATE_PRIOR_NAME)
    def replace_owner(*_args):
        sys.modules[support._PRIVATE_PRIOR_NAME] = foreign
        raise RuntimeError("intentional foreign ownership replacement")
    monkeypatch.setattr(support, "exec", replace_owner, raising=False)
    try:
        with pytest.raises(ValueError, match="foreign private"):
            support._load_prior_support()
        assert sys.modules[support._PRIVATE_PRIOR_NAME] is foreign
    finally:
        assert sys.modules.get(support._PRIVATE_PRIOR_NAME) is foreign
        del sys.modules[support._PRIVATE_PRIOR_NAME]


def test_actual26_provider_map_and_116_runtime_files_preserve_old_identities():
    assert support.PROVIDER_FACTORIES[:19] == support.prior.PROVIDER_FACTORIES
    assert support.PROVIDER_MODULES[19:] == EXTRA_PROVIDERS
    assert support.PROVIDER_FACTORIES[18][1] == "make_bertrand_power_valuation_law_candidate_theorems"
    assert len(support.PROVIDER_FACTORIES) == 26
    assert support.RUNTIME_PINS[:112] == support.prior.RUNTIME_PINS
    assert tuple((p.path, p.bytes, p.sha256) for p in support.RUNTIME_PINS[112:]) == EXTRA_RUNTIME_RECORDS
    assert len(support.RUNTIME_PINS) == 116
    support.require_runtime_sources()


@pytest.mark.parametrize("fault", ("missing", "extra", "list", "reverse", "wrong-factory", "singular-law"))
def test_provider_map_cannot_change_even_when_a_module_name_looks_valid(fault, monkeypatch):
    pairs = support.PROVIDER_FACTORIES
    if fault == "missing": pairs = pairs[:-1]
    elif fault == "extra": pairs = (*pairs, pairs[-1])
    elif fault == "list": pairs = list(pairs)
    elif fault == "reverse": pairs = pairs[::-1]
    elif fault == "wrong-factory": pairs = (*pairs[:-1], (pairs[-1][0], "make_foreign_theorems"))
    else: pairs = (*pairs[:18], (pairs[18][0], "make_bertrand_power_valuation_laws_candidate_theorems"), *pairs[19:])
    monkeypatch.setattr(support, "PROVIDER_FACTORIES", pairs)
    with pytest.raises(ValueError):
        support.require_runtime_sources()


@pytest.mark.parametrize("short", EXTRA_PROVIDERS)
@pytest.mark.parametrize("fault", ("file", "origin", "factory"))
def test_actual_added_canonical_provider_rejects_foreign_source_or_factory(short, fault, monkeypatch):
    name = "peano_lab.library." + short
    actual = support.import_module(name)
    fake = ModuleType(name)
    fake.__file__ = actual.__file__
    fake.__spec__ = SimpleNamespace(origin=actual.__spec__.origin)
    factory_name = "make_" + short + "_theorems"
    setattr(fake, factory_name, getattr(actual, factory_name))
    if fault == "file": fake.__file__ = "/foreign/source.py"
    elif fault == "origin": fake.__spec__.origin = "/foreign/source.py"
    else: setattr(fake, factory_name, _forbid)
    original = support.import_module
    monkeypatch.setattr(support, "import_module", lambda requested: fake if requested == name else original(requested))
    with pytest.raises(ValueError):
        support.canonical_provider_table()


@pytest.mark.parametrize("fault", ("missing", "extra", "list", "size", "sha", "path", "reverse"))
def test_runtime_inventory_cannot_shed_or_redirect_actual_pins(fault, monkeypatch):
    pins = support.RUNTIME_PINS
    if fault == "missing": pins = pins[:-1]
    elif fault == "extra": pins = (*pins, pins[-1])
    elif fault == "list": pins = list(pins)
    elif fault == "reverse": pins = pins[::-1]
    else:
        field, value = {"size": ("bytes", 1), "sha": ("sha256", "0" * 64),
                        "path": ("path", "peano-lab/py/peano_lab/foreign.py")}[fault]
        pins = (*pins[:-1], replace(pins[-1], **{field: value}))
    monkeypatch.setattr(support, "RUNTIME_PINS", pins)
    with pytest.raises(ValueError):
        support.require_runtime_sources()


@pytest.mark.parametrize("relative,size,digest", EXTRA_RUNTIME_RECORDS)
def test_each_new_runtime_pin_checks_real_bytes_and_rejects_an_actual_mutated_copy(
        relative, size, digest, tmp_path):
    pin = support.FilePin(relative, size, digest)
    support.check_pin(pin, ROOT, support.MAX_SOURCE_BYTES)
    copy = tmp_path / relative
    copy.parent.mkdir(parents=True)
    copy.write_bytes((ROOT / relative).read_bytes() + b"\n# test-owned mutation\n")
    with pytest.raises(ValueError):
        support.check_pin(pin, tmp_path, support.MAX_SOURCE_BYTES)


def test_prior52_authority_is_exact_six_file_subset_not_observation_authority():
    assert tuple((p.path, p.bytes, p.sha256) for p in support.PROTECTED_PRIOR52_PINS) == PRIOR52_RECORDS
    assert all(not p.path.endswith("README.md") and "observations" not in p.path
               for p in support.PROTECTED_PRIOR52_PINS)
    support.require_preserved_archives()
    source = inspect.getsource(support.require_preserved_archives)
    assert "prior.require_preserved_archives()" in source
    assert "for pin in PROTECTED_PRIOR52_PINS:" in source


@pytest.mark.parametrize("index", range(6))
def test_each_prior52_authority_file_rejects_a_real_modified_copy(index, tmp_path):
    pin = support.PROTECTED_PRIOR52_PINS[index]
    copy = tmp_path / pin.path
    copy.parent.mkdir(parents=True)
    copy.write_bytes((ROOT / pin.path).read_bytes() + b"\n")
    with pytest.raises(ValueError):
        support.check_pin(pin, tmp_path, support.MAX_BYTES)


@pytest.mark.parametrize("fault", ("missing", "extra", "list", "sha", "support-role"))
def test_prior52_authority_subset_cannot_mutate(fault, monkeypatch):
    pins = support.PROTECTED_PRIOR52_PINS
    if fault == "missing": pins = pins[:-1]
    elif fault == "extra": pins = (*pins, pins[-1])
    elif fault == "list": pins = list(pins)
    elif fault == "sha": pins = (*pins[:-1], replace(pins[-1], sha256="0" * 64))
    else: monkeypatch.setattr(support, "PRIOR52_SUPPORT_PIN", pins[-1])
    monkeypatch.setattr(support, "PROTECTED_PRIOR52_PINS", pins)
    with pytest.raises(ValueError):
        support.require_preserved_archives()


@pytest.mark.parametrize("kind", ("symlink", "fifo", "directory"))
def test_literal_prior_artifact_cannot_be_link_or_special_file(kind, tmp_path):
    pin = support.PRIOR52_SEED
    copy = tmp_path / pin.path
    copy.parent.mkdir(parents=True)
    if kind == "symlink": copy.symlink_to(ROOT / pin.path)
    elif kind == "fifo": os.mkfifo(copy)
    else: copy.mkdir()
    with pytest.raises(ValueError):
        support.check_pin(pin, tmp_path, support.MAX_BYTES)


def test_prior_archive_rejection_is_not_suppressed(monkeypatch):
    class Rejected(Exception):
        pass
    def reject():
        raise Rejected("original archive guard rejected")
    monkeypatch.setattr(support.prior, "require_preserved_archives", reject)
    with pytest.raises(Rejected):
        support.require_preserved_archives()


def _expected_seed_paths(through):
    if through == 59:
        return (ROOT / PRIOR52_RECORDS[-1][0],)
    previous = HERE / "artifacts" / ("working-euclidean-closure-prefix-" + str(PREVIOUS[through]) + "-proof-bundle-v1.json")
    canonical = ROOT / "research/arithmetic-library/artifacts/prime-field-polynomial-euclidean-division-proof-bundle-v1.json"
    polynomial = ROOT / "research/arithmetic-library/artifacts/lower-tier-prime-field-polynomials-proof-bundle-v1.json"
    prerequisites = ROOT / "research/arithmetic-library/artifacts/prime-field-polynomial-division-prerequisites-proof-bundle-v1.json"
    if through in (68, 72): return (previous, canonical, polynomial)
    if through in (74, 76): return (previous, canonical)
    if through == 87: return (previous, canonical, prerequisites)
    return (previous,)


@pytest.mark.parametrize("through", tuple(PREVIOUS))
def test_every_phase_has_only_its_real_previous_stage_and_declared_literal_supplements(through):
    assert support.required_seed_paths(through) == _expected_seed_paths(through)
    if through in (93, 94, 95):
        assert through - PREVIOUS[through] == 1
        assert len(support.required_seed_paths(through)) == 1


@pytest.mark.parametrize("fault", ("empty", "foreign", "duplicate", "list", "omitted-previous", "reordered"))
def test_wrong_stage_seed_sequence_rejects_before_original_seed_work(fault, monkeypatch):
    paths = _expected_seed_paths(68)
    if fault == "empty": paths = ()
    elif fault == "foreign": paths = (ROOT / "saved-receipt.json", *paths[1:])
    elif fault == "duplicate": paths = (*paths, paths[-1])
    elif fault == "list": paths = list(paths)
    elif fault == "omitted-previous": paths = paths[1:]
    else: paths = paths[::-1]
    monkeypatch.setattr(support.closure, "_validate_seeds", _forbid)
    with pytest.raises(ValueError):
        support.seed_inventory(paths, through=68)


@pytest.mark.parametrize("fault", ("missing", "extra", "list", "sha", "roles"))
def test_named_seed_roles_and_literal_inventory_cannot_diverge(fault, monkeypatch):
    pins = support.SEED_PINS
    if fault == "missing": pins = pins[:-1]
    elif fault == "extra": pins = (*pins, pins[-1])
    elif fault == "list": pins = list(pins)
    elif fault == "sha": pins = (*pins[:-1], replace(pins[-1], sha256="0" * 64))
    else: monkeypatch.setattr(support, "CANONICAL121_SEED", pins[2])
    monkeypatch.setattr(support, "SEED_PINS", pins)
    with pytest.raises(ValueError):
        support.require_seed_identities()


def test_actual_first_stage_seed_covers_all305_preexisting_targets_without_proof_work(selections, monkeypatch):
    for name in ("parent_snapshot", "assemble_bottom_layer_bundle", "check_bottom_layer_bundle", "replay_bottom_layer_theorem"):
        monkeypatch.setattr(support.closure, name, _forbid)
    monkeypatch.setattr(checker, "decode_proof_bundle", _forbid)
    pins = support.seed_inventory(_expected_seed_paths(59), through=59)
    assert pins == (support.PRIOR52_SEED,)
    report = support.seed_coverage(selections[59], pins)
    assert report["preexisting_targets"] == report["covered_targets"] == 305
    assert report["fresh_working_rows"] == 7 and report["previous_working_rows"] == 52
    assert report["missing_names"] == [] and report["raw_json_only"]
    assert report["original_ha_checked"] is report["proof_authority"] is report["proof_bodies_decoded"] is False


@pytest.fixture(scope="module")
def inert_seed_matches(selections):
    from peano_lab.library.proof_bundle import encode_formula
    from peano_lab.library.theorems import _closed_formula
    selected = selections[95]
    targets = {row.name: support.canonical(encode_formula(_closed_formula(row.statement)))
               for row in selected.complete_specs}
    matches = {}
    for pin in support.SEED_PINS:
        value = support._inert_bundle_metadata(support.read_pin(pin))
        encoded = tuple(support.canonical(node[1]) for node in value[3])
        by_target = {}
        for position, target in enumerate(encoded):
            by_target.setdefault(target, []).append(position)
        found = {}
        for row in selected.complete_specs:
            expected = tuple(targets[name] for name in row.dependencies)
            for position in by_target.get(targets[row.name], ()):
                if tuple(encoded[i] for i in value[3][position][2]) == expected:
                    found[row.name] = (position, row.dependencies)
                    break
        matches[pin.path] = found
    return matches


def test_four_actual_external_seeds_cover_exact395_preexisting_targets_inertly(selections, inert_seed_matches):
    preexisting = {row.name for row in selections[95].complete_specs} - set(NAMES[52:])
    actual = set().union(*(set(found) for found in inert_seed_matches.values()))
    assert len(preexisting) == 395 and preexisting <= actual
    earlier = set().union(*(set(inert_seed_matches[p.path]) for p in
                           (support.PRIOR52_SEED, support.CANONICAL121_SEED, support.PREREQUISITES85_SEED)))
    assert preexisting - earlier == {"prime_field_polynomial_add_associative", "prime_field_polynomial_add_transport"}


@pytest.mark.parametrize("through", tuple(PREVIOUS))
def test_each_prospective_previous_source_cone_plus_real_supplements_covers_stage(
        through, state, selections, inert_seed_matches):
    current = selections[through]
    previous_count = PREVIOUS[through]
    previous = (support.prior.select_support(support.prior.load_candidate_state())
                if previous_count == 52 else selections[previous_count])
    before = {row.name for row in current.complete_specs} - set(NAMES[previous_count:through])
    expected_previous_source = {row.name for row in previous.complete_specs}
    paths = _expected_seed_paths(through)
    actual_supplement_matches = set()
    for path in paths[1:]:
        actual_supplement_matches.update(inert_seed_matches[path.relative_to(ROOT).as_posix()])
    assert before <= expected_previous_source | actual_supplement_matches
    # For later stages the previous artifact is deliberately not fabricated by
    # this source-only assertion. Authoring must read and freshly check it.
    if through == 59:
        assert before <= set(inert_seed_matches[support.PRIOR52_SEED.path])


@pytest.mark.parametrize("fault", ("target", "premise", "root", "phase"))
def test_seed_coverage_rejects_altered_exact_source_selection(fault, selections):
    selected = selections[59]
    if fault == "target":
        rows = list(selected.complete_specs)
        rows[0] = replace(rows[0], statement="0=0")
        selected = replace(selected, complete_specs=tuple(rows))
    elif fault == "premise":
        rows = list(selected.complete_specs)
        rows[-1] = replace(rows[-1], dependencies=(*rows[-1].dependencies, "foreign"))
        selected = replace(selected, complete_specs=tuple(rows))
    elif fault == "root": selected = replace(selected, root_names=selected.root_names[:-1])
    else: selected = replace(selected, through=68)
    with pytest.raises(ValueError):
        support.seed_coverage(selected, (support.PRIOR52_SEED,))


@pytest.mark.parametrize("fault", ("sha", "size", "foreign", "list", "receipt"))
def test_bad_seed_pin_or_receipt_never_establishes_coverage(fault, selections):
    pin = support.PRIOR52_SEED
    if fault == "sha": pins = (replace(pin, sha256="0" * 64),)
    elif fault == "size": pins = (replace(pin, bytes=1),)
    elif fault == "foreign": pins = (support.CANONICAL121_SEED,)
    elif fault == "list": pins = [pin]
    else: pins = (SimpleNamespace(path=pin.path, original_ha_checked=True),)
    with pytest.raises(ValueError):
        support.seed_coverage(selections[59], pins)


@pytest.mark.parametrize("value", (None, {}, [], ["wrong", 0, [], []],
    ["peano-lab-bundle-v1", True, [], []],
    ["peano-lab-bundle-v1", 0, ["x"], [[1, ["x"], [0], []]]],
    ["peano-lab-bundle-v1", 0, ["x"], [[1, ["y"], [], []]]]))
def test_malformed_inert_metadata_is_rejected_without_decoding_a_body(value):
    with pytest.raises(ValueError):
        support._inert_bundle_metadata(json.dumps(value).encode())


def test_source_binding_reads_five_controls_and_never_uses_saved_observations(state, tmp_path, monkeypatch):
    assert support.CONTROL_FILES == CONTROL_NAMES
    before = support.state_binding(state)
    for name in CONTROL_NAMES:
        (tmp_path / name).write_bytes((HERE / name).read_bytes())
    monkeypatch.setattr(support, "HERE", tmp_path.resolve())
    assert support.state_binding(state) == before
    target = tmp_path / CONTROL_NAMES[1]
    target.write_bytes(target.read_bytes() + b"\n# inert changed control copy\n")
    assert support.state_binding(state) != before
    source = inspect.getsource(support.state_binding)
    assert '"complete_prior52_tree_bound": False' in source
    assert '"stored_observations_supply_authority": False' in source
    assert '"prior52_authority_files": _PRIOR52_RECORDS' in source
    for name in ("require_working_sources", "require_runtime_sources", "require_preserved_archives",
                 "require_seed_identities", "require_parent_registration"):
        assert name in source


@pytest.mark.parametrize("bad", ((), [], CONTROL_NAMES[:-1], (*CONTROL_NAMES, "README.md")))
def test_five_control_binding_cannot_drop_a_file_or_promote_an_observation(bad, state, monkeypatch):
    monkeypatch.setattr(support, "CONTROL_FILES", bad)
    with pytest.raises(ValueError):
        support.state_binding(state)


@pytest.mark.parametrize("bad", (None, 0, 1, "true", {}, []))
def test_final_binding_flag_is_exact_boolean_not_saved_receipt(bad, state):
    with pytest.raises(ValueError):
        support.state_binding(state, final=bad)


@pytest.mark.parametrize("bad", (None, {}, True, SimpleNamespace(path="saved-receipt.json")))
@pytest.mark.parametrize("task", ("metadata", "bundle", "root"))
def test_no_report_or_missing_final_pin_reaches_a_proof_gate(bad, task, monkeypatch):
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", bad)
    monkeypatch.setattr(support, "require_parent_registration", _forbid)
    monkeypatch.setattr(support.closure, "check_bottom_layer_bundle", _forbid)
    function = {"metadata": checker.global_metadata_report, "bundle": checker.verify_complete_bundle,
                "root": lambda: checker.verify_principal(PRINCIPALS[-1])}[task]
    with pytest.raises(ValueError):
        function()


@pytest.mark.parametrize("field,value", (
    ("path", "../old.json"), ("path", "artifacts/old.json"),
    ("bytes", True), ("bytes", 0), ("bytes", 64000001), ("sha256", "g" * 64),
    ("nodes", 306), ("nodes", 438), ("nodes", True), ("edges", 888),
    ("edges", 1368), ("body_nodes", False), ("body_nodes", 0)))
def test_final_artifact_requires_complete439_geometry_and_exact_new_location(field, value, monkeypatch):
    candidate = checker.ArtifactPin(support.stage_path(95).relative_to(ROOT).as_posix(), 1, "a" * 64, 439, 1383, 1)
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", replace(candidate, **{field: value}))
    monkeypatch.setattr(support, "require_parent_registration", _forbid)
    with pytest.raises(ValueError):
        checker.require_final_inventory()


def test_final_registration_is_absent_or_matches_actual_complete_inert_candidate_bytes():
    pin = checker.FINAL_ARTIFACT
    if pin is None:
        return
    assert type(pin) is checker.ArtifactPin
    assert (pin.nodes, pin.edges) == (439, 1383)
    assert ROOT / pin.path == support.stage_path(95)
    raw = support.read_pin(support.FilePin(pin.path, pin.bytes, pin.sha256))
    value = support._inert_bundle_metadata(raw)
    assert len(value[3]) == 439 and value[1] == 438
    assert sum(len(node[2]) for node in value[3]) == 1383
    # Inert identity is not a successful HA/Lean or ordinary-root check.


@pytest.mark.parametrize("bad", (None, True, "", "all", NAMES[0], NAMES[52], NAMES[92], "../root"))
def test_only_fifteen_exact_maximal_names_can_request_ordinary_replay(bad, monkeypatch):
    monkeypatch.setattr(checker, "_load_final", _forbid)
    with pytest.raises(ValueError):
        checker.verify_principal(bad)


def test_novelty_uses_actual_parsed_core_ast_including_working_working_pairs():
    row = support.TheoremSpec("first", "forall x. x=x", (), ("intro x", "refl"), "inert")
    alias = replace(row, name="alias", statement="forall y. y=y")
    other = replace(row, name="other", statement="forall y. y=0")
    assert checker._novelty_pairs((row, alias), (other,)) == (("alias", "first"),)
    assert checker._novelty_pairs((row,), (alias,)) == (("first", "alias"),)
    assert checker._novelty_pairs((row,), (other,)) == ()


def _calls(function, name):
    return [node for node in ast.walk(ast.parse(inspect.getsource(function)))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == name]


def test_original_complete_ha_precedes_compiled_lean_using_same_authenticated_bytes():
    source = inspect.getsource(checker.verify_complete_bundle)
    assert source.index("check_bottom_layer_bundle(") < source.index("independent._lean_check(")
    assert "independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)" in source
    assert "receipt.kernel_calls == pin.nodes" in source and "receipt.total_body_nodes == pin.body_nodes" in source
    calls = _calls(checker.verify_complete_bundle, "check_bottom_layer_bundle")
    assert len(calls) == 1 and len(calls[0].args) == 3 and not calls[0].keywords
    decode = [n for n in ast.walk(ast.parse(inspect.getsource(checker._load_final)))
              if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == "decode_proof_bundle"]
    assert len(decode) == 1 and len(decode[0].args) == 1 and not decode[0].keywords


def test_ordinary_reconstruction_is_followed_by_original_empty_context_check():
    source = inspect.getsource(checker.verify_principal)
    assert source.index("replay_bottom_layer_theorem(") < source.index("check((), proof.certificate, formula)")
    assert "proof.spec == exact and proof.formula == formula" in source
    calls = _calls(checker.verify_principal, "replay_bottom_layer_theorem")
    assert len(calls) == 1 and len(calls[0].args) == 4 and not calls[0].keywords


def test_all_final_gates_rehash_actual_artifact_and_original_source_binding():
    source = inspect.getsource(checker._rebind)
    assert source.index("require_final_inventory()") < source.index("state_binding(")
    for function in (checker.global_metadata_report, checker.verify_complete_bundle, checker.verify_principal):
        assert "_rebind(before)" in inspect.getsource(function)


def test_only_global_novelty_reads_current_catalogue_and_it_reconciles_all95():
    source = inspect.getsource(checker.global_metadata_report)
    assert 'len(catalog["theorems"]) == 4092' in source
    assert "all(parent.get(row.name) == row for row in selected.support)" in source
    assert "_novelty_pairs(state.rows, parent_rows)" in source
    for function in (support.load_candidate_state, support.select_support, support.execution_selection,
                     exporter.export_authoring_bundle, checker._load_final, checker.verify_complete_bundle, checker.verify_principal):
        assert "load_catalog(" not in inspect.getsource(function)
        assert "import editions_v" not in inspect.getsource(function)


def test_all_original_capacity_limits_and_safe_seed_writer_paths_are_retained():
    assert support.CPU_LIMITS == checker.CPU_LIMITS == exporter.CPU_LIMITS == (170, 175)
    assert support.WALL_SECONDS == checker.WALL_SECONDS == exporter.WALL_SECONDS == 180
    assert support.MAX_RSS_BYTES == 1536 * 1024 * 1024
    assert support.MAX_BYTES == support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes == 64000000
    assert support.MAX_CATALOG_BYTES == 64 * 1024 * 1024
    assert support.MAX_BYTES < support.closure.PARENT_CATALOG_BYTES <= support.MAX_CATALOG_BYTES
    assert support.closure.DEFAULT_BUNDLE_LIMITS is support.prior.closure.DEFAULT_BUNDLE_LIMITS
    for module in (exporter, checker):
        source = Path(module.__file__).read_text()
        assert source.index("resource.setrlimit(resource.RLIMIT_CPU, (170, 175))") < source.index("import working_euclidean_closure_support")
        assert "signal.alarm(180)" in source and "authoring_rss_bytes()" in source
        for forbidden in ("setrecursionlimit", "settrace", "setprofile", "fuel=", "max_nodes=", "--receipt", "--skip"):
            assert forbidden not in source


def test_original_seed_validator_and_dynamic_previous_stage_check_are_not_bypassed():
    source = inspect.getsource(support.seed_inventory)
    assert "closure._validate_seeds(paths)" in source
    assert "path == stage_path(PREVIOUS_THROUGH[through])" in source
    assert "info.st_uid == os.getuid() and info.st_nlink == 1" in source
    assert "stage_metrics(PREVIOUS_THROUGH[through])" in source and "read_pin(pin)" in source
    assert "value[1] == nodes" in source and "edges + roots" in source


def test_authoring_checks_exact_whole_seeds_then_rebinds_before_exclusive_output():
    source = inspect.getsource(exporter.export_authoring_bundle)
    calls = _calls(exporter.export_authoring_bundle, "assemble_bottom_layer_bundle")
    assert len(calls) == 1 and ast.unparse(calls[0].args[0]) == "execution.frontier"
    assert {k.arg for k in calls[0].keywords} == {"seed_bundles", "batch_size", "report"}
    assert next(k.value.value for k in calls[0].keywords if k.arg == "batch_size") == 1
    assert source.index("destination(output)") < source.index("load_candidate_state()")
    assert source.index('not coverage["missing_names"]') < source.index("assemble_bottom_layer_bundle(")
    assert "result.receipt.node_count == result.receipt.kernel_calls == expected_nodes + 1" in source
    assert source.index("for pin in seeds:") < source.index("write_exclusive(output, payload)")
    assert source.index("state_binding(support.load_candidate_state())") < source.index("write_exclusive(output, payload)")
    assert "fuel" not in source and "body_checked" not in source


def test_source_roles_reports_and_seventeen_tasks_do_not_relabel_or_mint_authority(selections, monkeypatch):
    selected = selections[95]
    assert all(selected.role(row.name) == "prior_non_admitted_left_unit" for row in selected.owned[:52])
    assert all(selected.role(row.name) == "new_non_admitted_euclidean_transport" for row in selected.owned[52:])
    assert all(selected.role(row.name) == "inherited_canonical_source" for row in selected.support)
    for name in ("parent_snapshot", "check_bottom_layer_bundle", "replay_bottom_layer_theorem"):
        monkeypatch.setattr(support.closure, name, _forbid)
    before = _authority_modules()
    report = support.local_manifest()
    assert (report["non_admitted_rows"], report["previous_non_admitted_rows"],
            report["additional_non_admitted_rows"]) == (95, 52, 43)
    assert report["ordinary_principals"] == list(PRINCIPALS)
    assert len(PRINCIPALS) + 2 == 17 and report["prior52_authority_file_count"] == 6
    for key in ("global_current4092_novelty_checked", "original_ha_checked", "independent_lean_checked",
                "ordinary_principals_checked", "complete_checkpoint_acceptance", "gcd_bezout_proved",
                "full_G091_proved", "alpha_admission_performed", "stable_admission_performed",
                "complete_prior52_tree_bound"):
        assert report[key] is False
    assert _authority_modules() == before


@pytest.mark.parametrize("args", (("--task", "root"), ("--task", "bundle", "--name", PRINCIPALS[0]),
    ("--task", "bundle", "--through", "95"), ("--task", "bundle", "--receipt", "saved.json")))
def test_final_cli_has_no_prefix_or_receipt_acceptance_mode(args, monkeypatch):
    monkeypatch.setattr(checker, "verify_complete_bundle", _forbid)
    monkeypatch.setattr(checker, "verify_principal", _forbid)
    with pytest.raises(SystemExit) as error:
        checker.main(list(args))
    assert error.value.code == 2


@pytest.fixture
def output_scope(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    directory = root / "artifacts"
    directory.mkdir()
    monkeypatch.setattr(exporter, "ARTIFACT_DIRECTORY", directory)
    monkeypatch.setattr(support, "ARTIFACT_DIRECTORY", directory)
    monkeypatch.setattr(support, "ROOT", root)
    return directory, support.stage_path(95)


@pytest.mark.parametrize("bad", ("../old.json", "/outside.json", "unissued.json",
    "working-euclidean-closure-prefix-91-proof-bundle-v1.json",
    "working-left-unit-closure-prefix-52-proof-bundle-v1.json"))
def test_output_cannot_escape_the_exact_new_stage_destinations(bad, output_scope):
    directory, _path = output_scope
    value = Path(bad) if bad.startswith("/") else directory / bad
    with pytest.raises(ValueError):
        exporter.destination(value)


@pytest.mark.parametrize("kind", ("file", "directory", "symlink", "fifo"))
def test_existing_output_rejects_before_any_source_or_proof_work(kind, output_scope, monkeypatch):
    _directory, path = output_scope
    if kind == "file": path.write_bytes(b"existing inert transport data")
    elif kind == "directory": path.mkdir()
    elif kind == "symlink": path.symlink_to(path.parent / "absent")
    else: os.mkfifo(path)
    monkeypatch.setattr(support, "load_candidate_state", _forbid)
    monkeypatch.setattr(support.closure, "assemble_bottom_layer_bundle", _forbid)
    with pytest.raises(ValueError):
        exporter.export_authoring_bundle(95, path, seed_bundles=())
    assert path.exists() or path.is_symlink()


def test_wrong_stage_output_is_rejected_before_source_construction(output_scope, monkeypatch):
    _directory, path = output_scope
    monkeypatch.setattr(support, "load_candidate_state", _forbid)
    with pytest.raises(ValueError):
        exporter.export_authoring_bundle(94, path, seed_bundles=())


def test_symlink_output_ancestor_is_not_followed(output_scope):
    directory, path = output_scope
    actual = directory.parent / "real-directory"
    actual.mkdir()
    directory.rmdir()
    directory.symlink_to(actual, target_is_directory=True)
    with pytest.raises(ValueError):
        exporter.destination(path)
    assert not tuple(actual.iterdir())


def test_foreign_output_directory_is_rejected(output_scope, monkeypatch):
    _directory, path = output_scope
    uid = os.getuid()
    monkeypatch.setattr(os, "getuid", lambda: uid + 1)
    with pytest.raises(ValueError):
        exporter.destination(path)


def test_original_exclusive_writer_preserves_inert_bytes_and_forbids_overwrite(output_scope):
    _directory, path = output_scope
    payload = b"unissued inert transport fixture, never a proof bundle\n"
    exporter.write_exclusive(path, payload)
    assert path.read_bytes() == payload and path.stat().st_nlink == 1
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    with pytest.raises(ValueError):
        exporter.write_exclusive(path, b"must not overwrite")
    assert path.read_bytes() == payload


def test_failed_writer_removes_only_its_new_owned_inode(output_scope, monkeypatch):
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
        exporter.write_exclusive(path, b"unissued test data")
    assert len(calls) == 2 and not path.exists()


def test_failed_writer_never_deletes_foreign_replacement_inode(output_scope, monkeypatch):
    _directory, path = output_scope
    original, calls, retained = exporter._resources, [], []
    replacement = b"foreign test-owned inode must be preserved"
    def replace_after_write():
        result = original()
        calls.append(result)
        if len(calls) == 2:
            retained.append(path.open("rb"))
            path.unlink()
            path.write_bytes(replacement)
            raise RuntimeError("intentional replacement race")
        return result
    monkeypatch.setattr(exporter, "_resources", replace_after_write)
    try:
        with pytest.raises(ValueError, match="refuses to remove"):
            exporter.write_exclusive(path, b"unissued disposable data")
        assert path.read_bytes() == replacement
    finally:
        for handle in retained:
            handle.close()
