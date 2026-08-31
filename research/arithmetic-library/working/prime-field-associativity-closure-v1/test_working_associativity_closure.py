"""Independent working37 integration guards, never proof-acceptance fixtures.

Positive cases inspect actual frozen source syntax or inert transport data.
No successful HA/Lean result, admission capability or saved receipt is mocked.
The actual full bundle and six ordinary principals belong to separate fresh
original-bounded verification invocations, not this source-only test suite.
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

import working_associativity_closure_support as support
import export_working_associativity_closure as exporter
import check_working_associativity_closure as checker


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
)
PRINCIPALS = (NAMES[12], NAMES[22], NAMES[24], NAMES[27], NAMES[30], NAMES[36])
SPECS_SHA256 = "de95fea3806bc6c227c032bf2c29095ce191e27624c2196bd417df6c77c31491"
PRIOR25_SPECS_SHA256 = "15d48cfcf25a997db2e18771d0c084f4465225c6137f47f53350d39a5ebb6981"
# through, canonical ancestors, theorem rows, packaged nodes, packaged edges.
PHASES = ((32, 244, 276, 277, 762), (34, 244, 278, 279, 787),
          (35, 245, 280, 281, 804), (37, 246, 283, 284, 818))


def _specs_digest(rows):
    value = sha256()
    for row in rows:
        payload = [row.name, row.statement, list(row.dependencies), list(row.script), row.summary]
        value.update((json.dumps(payload, ensure_ascii=True, separators=(",", ":")) + "\n").encode())
    return value.hexdigest()


def _authority_modules():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(("peano_lab.library.editions_v", "check_alpha_",
                                "build_peano_library_channels", "verify_peano_library_channels"))}


@pytest.fixture(scope="module")
def state():
    before = _authority_modules()
    value = support.load_candidate_state()
    assert _authority_modules() == before
    return value


@pytest.fixture(scope="module")
def selection(state):
    return support.select_support(state)


def test_exact37_inventory_keeps_all_prior25_nonadmitted_specifications(state):
    assert type(state) is support.CandidateState and type(state.rows) is tuple
    assert tuple(row.name for row in state.rows) == NAMES
    assert state.specs_sha256 == _specs_digest(state.rows) == SPECS_SHA256
    assert _specs_digest(state.rows[:25]) == PRIOR25_SPECS_SHA256
    assert sum(len(row.dependencies) for row in state.rows) == 179
    assert sum(len(row.script) for row in state.rows) == 4303
    assert tuple(support.PRINCIPAL_ROOTS) == PRINCIPALS
    assert len(set(PRINCIPALS)) == 6


@pytest.mark.parametrize("through,ancestors,total,nodes,edges", PHASES,
                         ids=("through32", "through34", "through35", "through37"))
def test_four_source_phases_are_exact_topological_and_complete(state, through, ancestors, total, nodes, edges):
    before = _authority_modules()
    chosen = support.select_support(state, NAMES[:through])
    assert chosen.through == through
    assert chosen.owned == state.rows[:through]
    assert len(chosen.canonical_support) == ancestors
    assert len(chosen.complete_specs) == total and total + 1 == nodes
    assert len({row.name for row in chosen.complete_specs}) == total
    assert not {row.name for row in chosen.canonical_support}.intersection(NAMES)
    assert {row.name for row in chosen.complete_specs} == (
        {row.name for row in chosen.canonical_support} | set(NAMES[:through]))
    consumed = {name for row in chosen.complete_specs for name in row.dependencies}
    assert chosen.root_names == tuple(row.name for row in chosen.complete_specs if row.name not in consumed)
    assert set(chosen.root_names) <= set(NAMES[:through])
    assert sum(len(row.dependencies) for row in chosen.complete_specs) + len(chosen.root_names) == edges
    seen = set()
    for row in chosen.complete_specs:
        assert len(set(row.dependencies)) == len(row.dependencies)
        assert set(row.dependencies) <= seen
        seen.add(row.name)
    assert _authority_modules() == before


def test_final_selection_contains_exactly_246_canonical_and_37_working_rows(selection):
    assert selection.through == 37
    assert len(selection.canonical_support) == 246
    assert len(selection.owned) == 37 and len(selection.complete_specs) == 283
    assert selection.root_names == PRINCIPALS
    assert sum(len(row.dependencies) for row in selection.complete_specs) == 812


@pytest.mark.parametrize("count", tuple(i for i in range(38) if i not in (32, 34, 35, 37)))
def test_only_the_four_approved_source_prefixes_are_allowed(count, state):
    with pytest.raises(ValueError):
        support.select_support(state, NAMES[:count])


@pytest.mark.parametrize("bad", ([], "all", {}, True, (True,), (1,), ("missing",),
                                 tuple(reversed(NAMES)), (NAMES[0],) * 37),
                         ids=("list", "text", "mapping", "bool", "bool-name", "int-name",
                              "foreign-name", "reverse", "duplicate"))
def test_unordered_or_foreign_owned_inventories_are_rejected(bad, state):
    with pytest.raises(ValueError):
        support.select_support(state, bad)


@pytest.mark.parametrize("index", range(37), ids=lambda index: f"row{index:02d}")
def test_each_owned_statement_mutation_is_rejected_before_support_selection(index, state):
    changed = list(state.rows)
    changed[index] = replace(changed[index], statement="0=1")
    with pytest.raises(ValueError):
        support.select_support(replace(state, rows=tuple(changed)))


@pytest.mark.parametrize("field", ("name", "dependencies", "script", "summary"))
@pytest.mark.parametrize("index", (0, 24, 25, 31, 32, 34, 35, 36), ids=lambda index: f"boundary{index:02d}")
def test_every_nonstatement_field_is_bound_across_all_ownership_and_phase_boundaries(index, field, state):
    row = state.rows[index]
    values = {"name": "foreign_working_row", "dependencies": ("foreign_dependency",),
              "script": ("exact foreign",), "summary": row.summary + " changed"}
    changed = list(state.rows)
    changed[index] = replace(row, **{field: values[field]})
    with pytest.raises(ValueError):
        support.select_support(replace(state, rows=tuple(changed)))


@pytest.mark.parametrize("bad", (None, {}, (), SimpleNamespace(rows=(), specs_sha256="a" * 64)),
                         ids=("none", "mapping", "tuple", "foreign-object"))
def test_foreign_candidate_state_never_becomes_a_source_checkpoint(bad):
    with pytest.raises(ValueError):
        support.select_support(bad)


@pytest.mark.parametrize("fault", ("missing", "extra", "list", "digest", "foreign-row"))
def test_full_candidate_count_type_and_digest_are_required(fault, state):
    if fault == "missing":
        changed = replace(state, rows=state.rows[:-1])
    elif fault == "extra":
        changed = replace(state, rows=(*state.rows, state.rows[0]))
    elif fault == "list":
        changed = replace(state, rows=list(state.rows))
    elif fault == "digest":
        changed = replace(state, specs_sha256="0" * 64)
    else:
        row = state.rows[0]
        foreign = SimpleNamespace(name=row.name, statement=row.statement,
                                  dependencies=row.dependencies, script=row.script, summary=row.summary)
        changed = replace(state, rows=(foreign, *state.rows[1:]))
    with pytest.raises(ValueError):
        support.select_support(changed)


FACTORY_EXPECTATIONS = (
    ("prime-field-shift-v1", "prime_field_polynomial_shift_candidate", 15, 29786,
     "325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b", 32010,
     "0622fb92978fcf028842aa4d9822ef61213642eb852e080f7c787dcea4bb395f",
     "beac32710e2191f4dc40f6317dc376f6b3307ad8ad48a7ccbac17c8bea990081"),
    ("prime-field-scalar-v1", "prime_field_polynomial_scalar_convolution_candidate", 10, 23637,
     "e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e", 30353,
     "881452ada0b5dc3be7d6cd00ee31dc08075b07f51d83595ee60f8cfb40d4c6e5",
     "a8ab3e2660a01dc79520722de6093c534e4184dcdbcb9481317df4d5b6a54a7b"),
    ("prime-field-append-v1", "prime_field_polynomial_append_candidate", 6, 28396,
     "271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042", 36494,
     "0c554b05b2c7e2c40e3b0e8044160379a3284bb173e48d59d77def0cad4272aa",
     "6035968b0f11aec5e4bd6cb43b4d4958318b55f600fab914025479f571b75c2a"),
    ("prime-field-shift-equivalence-v1", "prime_field_polynomial_shift_equivalence_candidate", 1, 6021,
     "8846224923876a4f57ad8d6f31020838ccc86c86a683ec78a7c7c23c35b92068", 20376,
     "9ed90ddc4680f8c2c3d04e2e3a76f8cffda4bfb95b1b83ab391d134c7fe5ab18",
     "d68b99a4ed9f996bd7e8b23fd0f17e165176b949f07a806a4d2c935d4372529e"),
    ("prime-field-associativity-step-v1", "prime_field_polynomial_associativity_step_candidate", 3, 26607,
     "dd85dbd1bd87143715a4286724ac7c87f280a909dac6759f00a6cb7dff7c85f1", 29135,
     "4cbd15750521b2ad1a3ecd8288bfdf631bd5ad90dc7e623d4e593dc79f615262",
     "87017c7298a0247444be68f9be34e6b354b89d491ca7ee49ea4bd06effd6b2cd"),
    ("prime-field-associativity-induction-v1", "prime_field_polynomial_associativity_induction_candidate", 2, 9924,
     "8d276a028764cd08e6eaebbf25bb4e21fcd5076a610d356a77d52ba6603ebe4c", 19628,
     "d3725cbdd86f8d72446baf5417d25a4ddf31f61b0b6f1d076cb065b8131f2003",
     "b6ad06b7925dbb35202bb263ef14c7dc69d18c80771e075497d0a17d42294dc8"),
)
PRINCIPAL_DIGESTS = (
    "0fc173b813282a7111d604245b1706a4c01c5bcf566812151810e9afe38f065d",
    "5d0349367decc3084471726b73a77617d49f484cf31191bb78effbc434167156",
    "fd6d04fd88ff9f594f7ee27de04486c1932ce5de30b6030b6b9b18cb547511ef",
    "a11e1f29b31ae9076959706b6b5d0813689194a2ab57a1a4e879e6a6c3ad69bd",
    "0ef69b8524dd48c1a9805f158e9eff25c41e421b85378b96b51b7c63bd89f087",
    "7b693d78212d80c6406b09f6ca5151ac88862da29d824494ed6338f601fb6912",
)


@pytest.mark.parametrize("index", range(6), ids=lambda index: f"factory{index}")
def test_six_factory_identities_are_literal_and_match_actual_source_bytes(index, state):
    directory, module, count, size, digest, test_size, test_digest, specs = FACTORY_EXPECTATIONS[index]
    owner = support.FACTORIES[index]
    relative = "research/arithmetic-library/working/" + directory
    assert (owner.directory, owner.module, owner.count, owner.source_bytes, owner.source_sha256,
            owner.test_bytes, owner.test_sha256, owner.specs_sha256) == (
                relative, module, count, size, digest, test_size, test_digest, specs)
    for pin, expected_name in ((owner.source, module + ".py"), (owner.test, "test_" + module + ".py")):
        assert pin.path == relative + "/" + expected_name
        raw = (ROOT / pin.path).read_bytes()
        assert (len(raw), sha256(raw).hexdigest()) == (pin.bytes, pin.sha256)
    start = sum(row[2] for row in FACTORY_EXPECTATIONS[:index])
    assert _specs_digest(state.rows[start:start + count]) == specs
    if index < 2:
        assert owner is support.prior.FACTORIES[index]


@pytest.mark.parametrize("name,digest", tuple(zip(PRINCIPALS, PRINCIPAL_DIGESTS)),
                         ids=lambda value: str(value)[:70])
def test_six_maximal_principal_statement_pins_are_exact(name, digest, state):
    row = next(row for row in state.rows if row.name == name)
    assert sha256(row.statement.encode()).hexdigest() == digest
    assert tuple(support.PRINCIPAL_STATEMENT_SHA256) == PRINCIPAL_DIGESTS


def test_prior_working_and_canonical_roles_are_never_conflated(selection):
    for row in selection.owned[:25]:
        assert selection.role(row.name) == "prior_non_admitted_shift_scalar"
    for row in selection.owned[25:]:
        assert selection.role(row.name) == "new_non_admitted_associativity_support"
    for row in selection.canonical_support:
        assert selection.role(row.name) == "inherited_canonical_source"
    with pytest.raises(ValueError):
        selection.role("foreign")


def _forbid(*_args, **_kwargs):
    pytest.fail("a source-only or rejecting guard reached a proof/Alpha execution seam")


def test_local_source_report_never_invokes_parent_replay_or_accepts_proof_authority(monkeypatch):
    for name in ("parent_snapshot", "check_bottom_layer_bundle", "replay_bottom_layer_theorem"):
        monkeypatch.setattr(support.closure, name, _forbid)
    before = _authority_modules()
    report = support.local_manifest()
    assert (report["non_admitted_rows"], report["previous_non_admitted_rows"],
            report["additional_non_admitted_rows"]) == (37, 25, 12)
    assert report["packaged_nodes"] == 284 and report["packaged_edges"] == 818
    assert report["ordinary_principals"] == list(PRINCIPALS)
    for key in ("global_current4092_novelty_checked", "original_ha_checked", "independent_lean_checked",
                "ordinary_principals_checked", "complete_checkpoint_acceptance", "gcd_bezout_proved",
                "full_G091_proved", "alpha_admission_performed", "stable_admission_performed"):
        assert report[key] is False
    assert _authority_modules() == before


@pytest.mark.parametrize("index", range(6), ids=lambda index: f"factory{index}")
def test_foreign_working_module_slot_is_not_replaced(index, monkeypatch):
    name = "_working_associativity_closure_v1_" + support.FACTORIES[index].module
    foreign = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, foreign)
    with pytest.raises(ValueError, match="already owned"):
        support.load_candidate_state()
    assert sys.modules[name] is foreign


def test_actual_prior_controller_is_only_temporarily_registered_and_cleaned():
    name = support._PRIVATE_PRIOR_NAME
    assert name not in sys.modules
    before = _authority_modules()
    controller = support._load_prior_support()
    assert type(controller) is ModuleType and controller.__name__ == name
    assert controller.__file__ == str(ROOT / support.PRIOR25_SUPPORT_PIN.path)
    assert name not in sys.modules and _authority_modules() == before
    assert not name.startswith("peano_lab.")


def test_preexisting_private_controller_identity_is_preserved(monkeypatch):
    name = support._PRIVATE_PRIOR_NAME
    foreign = ModuleType(name)
    monkeypatch.setitem(sys.modules, name, foreign)
    with pytest.raises(ValueError, match="already owned"):
        support._load_prior_support()
    assert sys.modules[name] is foreign


def test_failed_private_controller_execution_removes_only_its_own_module(monkeypatch):
    class Rejected(Exception):
        pass
    def reject(*_args, **_kwargs):
        raise Rejected("deliberate source-execution failure; no proof accepted")
    monkeypatch.setattr(support, "exec", reject, raising=False)
    with pytest.raises(Rejected):
        support._load_prior_support()
    assert support._PRIVATE_PRIOR_NAME not in sys.modules


def test_private_controller_foreign_replacement_is_not_deleted(monkeypatch):
    name = support._PRIVATE_PRIOR_NAME
    assert name not in sys.modules
    foreign = ModuleType(name)
    def replace_then_reject(*_args, **_kwargs):
        sys.modules[name] = foreign
        raise RuntimeError("deliberately replaced test-owned slot")
    monkeypatch.setattr(support, "exec", replace_then_reject, raising=False)
    try:
        with pytest.raises(ValueError, match="preserved, not deleted"):
            support._load_prior_support()
        assert sys.modules[name] is foreign
    finally:
        if sys.modules.get(name) is foreign:
            del sys.modules[name]


@pytest.mark.parametrize("fault", ("file", "origin", "factory", "type"))
def test_canonical_provider_origin_and_factory_ownership_are_required(fault, monkeypatch):
    short = "prime_field_polynomial_convolution_padding_candidate"
    name = "peano_lab.library." + short
    path = str(ROOT / "peano-lab/py/peano_lab/library" / (short + ".py"))
    foreign = ModuleType(name) if fault != "type" else SimpleNamespace()
    foreign.__file__ = "/foreign/source.py" if fault == "file" else path
    foreign.__spec__ = SimpleNamespace(origin="/foreign/source.py" if fault == "origin" else path)
    def wrong_factory(_spec):
        pytest.fail("a foreign factory must not be invoked")
    setattr(foreign, "make_" + short + "_theorems", wrong_factory)
    monkeypatch.setitem(sys.modules, name, foreign)
    with pytest.raises(ValueError, match="foreign bytes|replaced"):
        support.canonical_provider_table()
    assert sys.modules[name] is foreign


@pytest.mark.parametrize("field,value", (("count", 2), ("source_bytes", True),
    ("source_sha256", "0" * 64), ("test_bytes", 1), ("test_sha256", "1" * 64),
    ("specs_sha256", "2" * 64), ("module", "foreign"), ("directory", "../foreign")))
def test_changed_factory_ownership_is_rejected_before_loading(field, value, monkeypatch):
    owners = list(support.FACTORIES)
    owners[2] = replace(owners[2], **{field: value})
    monkeypatch.setattr(support, "FACTORIES", tuple(owners))
    with pytest.raises(ValueError, match="source ownership"):
        support.require_working_sources()


@pytest.mark.parametrize("fault", ("missing", "extra", "list", "size", "digest", "path", "provider"))
def test_runtime_and_provider_inventory_mutations_fail_closed(fault, monkeypatch):
    pins = support.RUNTIME_PINS
    if fault == "missing": pins = pins[:-1]
    elif fault == "extra": pins = (*pins, pins[-1])
    elif fault == "list": pins = list(pins)
    elif fault == "size": pins = (*pins[:-1], replace(pins[-1], bytes=True))
    elif fault == "digest": pins = (*pins[:-1], replace(pins[-1], sha256="0" * 64))
    elif fault == "path": pins = (*pins[:-1], replace(pins[-1], path="../foreign"))
    else: monkeypatch.setattr(support, "PROVIDER_MODULES", support.PROVIDER_MODULES[:-1])
    monkeypatch.setattr(support, "RUNTIME_PINS", pins)
    with pytest.raises(ValueError, match="runtime or minimal canonical-provider inventory"):
        support.require_runtime_sources()


def test_extra_runtime_declaration_cannot_disable_any_actual_byte_check(monkeypatch):
    original, observed = support.check_pin, []
    def actual_check(pin, *args, **kwargs):
        observed.append(pin.path)
        return original(pin, *args, **kwargs)
    monkeypatch.setattr(support, "check_pin", actual_check)
    monkeypatch.setattr(support, "ADDITIONAL_RUNTIME_PINS", ())
    support.require_runtime_sources()
    assert observed == [pin.path for pin in support.RUNTIME_PINS]
    assert len(observed) == len(set(observed)) == 109


def test_all_eleven_prior_checkpoint_files_are_literal_preservation_inputs():
    records = [[pin.path, pin.bytes, pin.sha256] for pin in support.PRIOR25_PINS]
    assert len(records) == 11 and sum(row[1] for row in records) == 871810
    assert records == sorted(records)
    assert sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest() == (
        "fe38b987cf5eca80fcd9ddc48926f6dc3aa0ba2c396e5151b851b75cf7beba2f")
    support.require_preserved_archives()
    assert {Path(pin.path).name for pin in support.PRIOR25_PINS} >= {
        "README.md", "final-verification-observations-v1.json", "working-shift-scalar-proof-bundle-v1.json"}


@pytest.mark.parametrize("fault", ("missing", "extra", "list", "digest", "path"))
def test_prior_checkpoint_pin_inventory_cannot_be_replaced(fault, monkeypatch):
    pins = support.PRIOR25_PINS
    if fault == "missing": pins = pins[:-1]
    elif fault == "extra": pins = (*pins, pins[0])
    elif fault == "list": pins = list(pins)
    elif fault == "digest": pins = (replace(pins[0], sha256="0" * 64), *pins[1:])
    else: pins = (replace(pins[0], path="../foreign"), *pins[1:])
    monkeypatch.setattr(support, "PRIOR25_PINS", pins)
    with pytest.raises(ValueError, match="complete archive inventory"):
        support.require_preserved_archives()


@pytest.mark.parametrize("fault", ("unknown-file", "unknown-directory", "unknown-link", "fifo",
                                    "known-link", "missing", "changed"))
def test_complete_prior_tree_rejects_all_added_removed_or_changed_paths(fault, tmp_path, monkeypatch):
    shadow = tmp_path.resolve()
    directory = shadow / support.PRIOR25_RELATIVE
    for pin in support.PRIOR25_PINS:
        path = shadow / pin.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / pin.path).read_bytes())
    known = shadow / support.PRIOR25_PINS[0].path
    if fault == "unknown-file": (directory / "unlisted.bin").write_bytes(b"unissued fixture")
    elif fault == "unknown-directory": (directory / "unlisted").mkdir()
    elif fault == "unknown-link": (directory / "unlisted.link").symlink_to(known)
    elif fault == "fifo": os.mkfifo(directory / "unlisted.pipe")
    elif fault == "known-link":
        known.unlink()
        known.symlink_to(ROOT / support.PRIOR25_PINS[0].path)
    elif fault == "missing": known.unlink()
    else: known.write_bytes(known.read_bytes() + b"\nchanged inert fixture\n")
    monkeypatch.setattr(support, "ROOT", shadow)
    with pytest.raises(ValueError):
        support.require_preserved_archives()


@pytest.mark.parametrize("bad", (None, True, False, 31, 33, 36, 38, 37.0, "37", -1))
def test_phase_numbers_require_exact_int_and_one_of_four_values(bad):
    with pytest.raises(ValueError):
        support.stage_metrics(bad)


def test_four_stage_paths_and_seed_orders_are_literal():
    paths = {n: support.ARTIFACT_DIRECTORY / f"working-associativity-closure-prefix-{n}-proof-bundle-v1.json"
             for n in (32, 34, 35, 37)}
    for through, _ancestors, total, _nodes, edges in PHASES:
        assert support.stage_path(through) == paths[through]
        count, actual_edges, roots = support.stage_metrics(through)
        assert count == total and actual_edges + roots == edges
    assert support.required_seed_paths(32) == tuple(ROOT / pin.path for pin in (
        support.PRIOR25_SEED, support.CANONICAL121_SEED, support.POLYNOMIAL_SEED))
    assert support.required_seed_paths(34) == (paths[32],)
    assert support.required_seed_paths(35) == (paths[34], ROOT / support.CANONICAL121_SEED.path)
    assert support.required_seed_paths(37) == (paths[35], ROOT / support.V27_SEED.path)


@pytest.mark.parametrize("through", (32, 34, 35, 37))
@pytest.mark.parametrize("fault", ("empty", "reverse-or-extra", "foreign", "duplicate", "list"))
def test_wrong_stage_seed_sequences_fail_before_original_seed_validation(through, fault, monkeypatch):
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
def test_named_seed_roles_and_literal_inventory_cannot_diverge(fault, monkeypatch):
    pins = support.SEED_PINS
    if fault == "missing": pins = pins[:-1]
    elif fault == "extra": pins = (*pins, pins[0])
    elif fault == "list": pins = list(pins)
    elif fault == "digest": pins = (replace(pins[0], sha256="0" * 64), *pins[1:])
    else: monkeypatch.setattr(support, "PRIOR25_SEED", support.CANONICAL121_SEED)
    monkeypatch.setattr(support, "SEED_PINS", pins)
    with pytest.raises(ValueError):
        support.require_seed_identities()


def test_actual_phase32_seeds_cover_all269_preexisting_targets_without_checking_proofs(state, monkeypatch):
    monkeypatch.setattr(support.closure, "check_bottom_layer_bundle", _forbid)
    monkeypatch.setattr(checker, "decode_proof_bundle", _forbid)
    before = _authority_modules()
    selected = support.select_support(state, NAMES[:32])
    pins = support.seed_inventory(support.required_seed_paths(32), through=32)
    assert pins == (support.PRIOR25_SEED, support.CANONICAL121_SEED, support.POLYNOMIAL_SEED)
    report = support.seed_coverage(selected, pins)
    assert report["preexisting_targets"] == report["covered_targets"] == 269
    assert report["fresh_working_rows"] == 7 and report["previous_working_rows"] == 25
    assert report["missing_names"] == [] and report["through"] == 32
    assert [row["inert_nodes"] for row in report["seeds"]] == [208, 377, 202]
    assert report["raw_json_only"] is True
    assert report["proof_bodies_decoded"] is report["original_ha_checked"] is report["proof_authority"] is False
    assert _authority_modules() == before


@pytest.mark.parametrize("fault", ("target", "premise", "roots", "phase"))
def test_seed_coverage_rejects_altered_source_targets_or_ordered_premises(fault, state):
    selected = support.select_support(state, NAMES[:32])
    pins = (support.PRIOR25_SEED, support.CANONICAL121_SEED, support.POLYNOMIAL_SEED)
    if fault in ("target", "premise"):
        row = selected.complete_specs[-1]
        altered = replace(row, statement="0=1") if fault == "target" else replace(row, dependencies=())
        selected = replace(selected, complete_specs=(*selected.complete_specs[:-1], altered))
    elif fault == "roots": selected = replace(selected, root_names=())
    else: selected = replace(selected, through=37)
    with pytest.raises(ValueError, match="altered source selection"):
        support.seed_coverage(selected, pins)


@pytest.mark.parametrize("fault", ("digest", "size", "order"))
def test_actual_seed_pin_mutations_never_establish_coverage(fault, state):
    selected = support.select_support(state, NAMES[:32])
    pins = (support.PRIOR25_SEED, support.CANONICAL121_SEED, support.POLYNOMIAL_SEED)
    if fault == "digest": pins = (replace(pins[0], sha256="0" * 64), *pins[1:])
    elif fault == "size": pins = (replace(pins[0], bytes=1), *pins[1:])
    else: pins = pins[::-1]
    with pytest.raises(ValueError):
        support.seed_coverage(selected, pins)


@pytest.mark.parametrize("value", (None, {}, [], ["wrong", 0, [], []],
    ["peano-lab-bundle-v1", True, ["f"], [[24, ["f"], [], []]]],
    ["peano-lab-bundle-v1", 0, ["f"], [[True, ["f"], [], []]]],
    ["peano-lab-bundle-v1", 0, ["f"], [[24, ["f"], [0], []]]],
    ["peano-lab-bundle-v1", 0, ["f"], [[24, ["g"], [], []]]]),
    ids=("none", "object", "empty", "schema", "root-bool", "fuel-bool", "forward-edge", "target"))
def test_malformed_inert_previous_stage_shapes_are_rejected(value):
    with pytest.raises(ValueError):
        support._inert_bundle_metadata(json.dumps(value).encode())


@pytest.mark.parametrize("bad", (None, {}, True, SimpleNamespace(path="saved-receipt.json")),
                         ids=("missing", "saved-object", "bool", "foreign-object"))
@pytest.mark.parametrize("task", ("metadata", "bundle", "root"))
def test_missing_or_receipt_like_final_registration_cannot_reach_any_proof_gate(bad, task, monkeypatch):
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", bad)
    monkeypatch.setattr(support, "require_parent_registration", _forbid)
    monkeypatch.setattr(support.closure, "check_bottom_layer_bundle", _forbid)
    function = {"metadata": checker.global_metadata_report, "bundle": checker.verify_complete_bundle,
                "root": lambda: checker.verify_principal(PRINCIPALS[-1])}[task]
    with pytest.raises(ValueError, match="registered"):
        function()


@pytest.mark.parametrize("field,value", (("path", "../old.json"), ("path", "artifacts/old.json"),
    ("bytes", True), ("bytes", 0), ("bytes", 64000001), ("sha256", "G" * 64),
    ("nodes", 281), ("nodes", True), ("edges", 804), ("edges", 0), ("body_nodes", False)))
def test_final_inventory_rejects_partial_foreign_or_malformed_artifact_shapes(field, value, monkeypatch):
    pin = checker.ArtifactPin(support.stage_path(37).relative_to(ROOT).as_posix(), 1, "a" * 64, 284, 818, 1)
    monkeypatch.setattr(checker, "FINAL_ARTIFACT", replace(pin, **{field: value}))
    monkeypatch.setattr(support, "require_parent_registration", _forbid)
    with pytest.raises(ValueError, match="incomplete, foreign, or malformed"):
        checker.require_final_inventory()


@pytest.mark.parametrize("bad", (None, True, 1, "", "../root", NAMES[0], "all"))
def test_only_six_exact_principals_can_reach_final_proof_data(bad, monkeypatch):
    monkeypatch.setattr(checker, "_load_final", _forbid)
    with pytest.raises(ValueError, match="six exact"):
        checker.verify_principal(bad)


@pytest.mark.parametrize("field", ("PARENT_CATALOG_PINS", "PARENT_CHANNEL_PIN",
                                  "PARENT_IDENTITY_SHA256", "PARENT_ENROLLMENT_SHA256"))
def test_changed_current_parent_registration_is_rejected_before_delegation(field, monkeypatch):
    monkeypatch.setattr(support, field, None)
    monkeypatch.setattr(support.prior, "require_parent_registration", _forbid)
    with pytest.raises(ValueError, match="registration changed"):
        support.require_parent_registration()


def test_novelty_compares_parsed_formulas_including_new_new_aliases():
    first = support.TheoremSpec("first", "forall x. x=x", (), ("intro x", "refl"), "inert syntax")
    alias = replace(first, name="alias", statement="forall y. y=y")
    other = replace(first, name="different", statement="forall y. y=0")
    assert checker._novelty_pairs((first, alias), (other,)) == (("alias", "first"),)
    assert checker._novelty_pairs((first,), (alias,)) == (("first", "alias"),)
    assert checker._novelty_pairs((first,), (other,)) == ()


def _calls(function, name):
    return [node for node in ast.walk(ast.parse(inspect.getsource(function)))
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == name]


def test_exporter_uses_whole_original_assembler_and_rebinds_every_seed_before_exclusive_write():
    source = inspect.getsource(exporter.export_authoring_bundle)
    calls = _calls(exporter.export_authoring_bundle, "assemble_bottom_layer_bundle")
    assert len(calls) == 1 and ast.unparse(calls[0].args[0]) == "execution.frontier"
    assert {k.arg for k in calls[0].keywords} == {"seed_bundles", "batch_size", "report"}
    assert next(k.value.value for k in calls[0].keywords if k.arg == "batch_size") == 1
    assert source.index('not coverage["missing_names"]') < source.index("assemble_bottom_layer_bundle(")
    assert "result.receipt.node_count == result.receipt.kernel_calls == expected_nodes + 1" in source
    assert source.index("for pin in seeds:") < source.index("write_exclusive(output, payload)")
    assert source.index("state_binding(support.load_candidate_state())") < source.index("write_exclusive(output, payload)")
    assert "fuel" not in source and "body_checked" not in source


def test_whole_kernel_gate_then_compiled_lean_receive_the_same_complete_payload():
    source = inspect.getsource(checker.verify_complete_bundle)
    assert source.index("check_bottom_layer_bundle(") < source.index("independent._lean_check(")
    assert "independent._lean_check(checkpoint, receipt.node_count, bundle.root, payload)" in source
    assert "receipt.kernel_calls == pin.nodes" in source and "receipt.total_body_nodes == pin.body_nodes" in source
    assert "_rebind(before)" in source
    call = _calls(checker.verify_complete_bundle, "check_bottom_layer_bundle")[0]
    assert len(call.args) == 3 and call.keywords == []
    decoding = [node for node in ast.walk(ast.parse(inspect.getsource(checker._load_final)))
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == "decode_proof_bundle"]
    assert len(decoding) == 1 and len(decoding[0].args) == 1 and decoding[0].keywords == []


def test_ordinary_roots_use_original_replay_and_extra_exact_empty_context_kernel_check():
    source = inspect.getsource(checker.verify_principal)
    assert source.index("replay_bottom_layer_theorem(") < source.index("check((), proof.certificate, formula)")
    assert "proof.spec == exact and proof.formula == formula" in source
    assert source.index("del state, payload") < source.index("replay_bottom_layer_theorem(")
    assert source.index("del bundle, target") < source.index("check((), proof.certificate, formula)")
    assert "_rebind(before)" in source
    call = _calls(checker.verify_principal, "replay_bottom_layer_theorem")[0]
    assert len(call.args) == 4 and call.keywords == []


def test_final_artifact_is_reauthenticated_after_every_final_gate():
    source = inspect.getsource(checker._rebind)
    assert source.index("require_final_inventory()") < source.index("state_binding(")
    assert source.index("state_binding(") < source.index("_resources()")
    for function in (checker.global_metadata_report, checker.verify_complete_bundle, checker.verify_principal):
        assert "_rebind(before)" in inspect.getsource(function)


def test_only_global_novelty_loads_the_actual4092_catalogue_and_checks_all_canonical_rows():
    for function in (support.load_candidate_state, support.select_support, support.execution_selection,
                     exporter.export_authoring_bundle, checker._load_final, checker.verify_complete_bundle,
                     checker.verify_principal):
        source = inspect.getsource(function)
        assert "load_catalog(" not in source and "import editions_v" not in source
    source = inspect.getsource(checker.global_metadata_report)
    assert 'len(catalog["theorems"]) == 4092' in source
    assert "all(parent.get(row.name) == row for row in selected.support)" in source
    assert "_novelty_pairs(state.rows, parent_rows)" in source


def test_proof_and_catalogue_limits_remain_original_and_distinct():
    assert support.CPU_LIMITS == checker.CPU_LIMITS == exporter.CPU_LIMITS == (170, 175)
    assert support.WALL_SECONDS == checker.WALL_SECONDS == exporter.WALL_SECONDS == 180
    assert support.MAX_RSS_BYTES == 1536 * 1024 * 1024
    assert support.MAX_BYTES == support.closure.DEFAULT_BUNDLE_LIMITS.max_payload_bytes == 64000000
    assert support.MAX_CATALOG_BYTES == support.inherited.MAX_CATALOG_COMPONENT_BYTES == 64 * 1024 * 1024
    assert support.MAX_BYTES < support.closure.PARENT_CATALOG_BYTES <= support.MAX_CATALOG_BYTES
    for module in (exporter, checker):
        source = Path(module.__file__).read_text()
        assert source.index("resource.setrlimit(resource.RLIMIT_CPU, (170, 175))") < source.index("import working_associativity_closure_support")
        assert "signal.alarm(180)" in source and "authoring_rss_bytes()" in source
        for forbidden in ("setrecursionlimit", "settrace", "setprofile", "fuel=", "max_nodes=", "--receipt", "--skip"):
            assert forbidden not in source


@pytest.mark.parametrize("bad", (None, "true", 0, 1, [], {}))
def test_binding_final_flag_is_exact_boolean(bad, state):
    with pytest.raises(ValueError, match="Boolean"):
        support.state_binding(state, final=bad)


def test_all_five_controls_and_every_source_seed_and_archive_are_bound(state, tmp_path, monkeypatch):
    expected = ("working_associativity_closure_support.py", "export_working_associativity_closure.py",
                "check_working_associativity_closure.py", "test_working_associativity_closure.py",
                "working-associativity-closure-rfc-v1.md")
    assert support.CONTROL_FILES == expected
    before = support.state_binding(state)
    for name in expected:
        (tmp_path / name).write_bytes((HERE / name).read_bytes())
    monkeypatch.setattr(support, "HERE", tmp_path.resolve())
    assert support.state_binding(state) == before
    # Only unissued temporary control copies change; no real source is edited.
    changed = tmp_path / expected[1]
    changed.write_bytes(changed.read_bytes() + b"\n# deliberately changed inert source copy\n")
    assert support.state_binding(state) != before
    source = inspect.getsource(support.state_binding)
    for name in ("require_working_sources", "require_runtime_sources", "require_preserved_archives",
                 "require_seed_identities", "CONTROL_FILES", "require_parent_registration"):
        assert name in source


@pytest.fixture
def output_scope(tmp_path, monkeypatch):
    root = tmp_path.resolve()
    directory = root / "artifacts"
    directory.mkdir()
    monkeypatch.setattr(exporter, "ARTIFACT_DIRECTORY", directory)
    monkeypatch.setattr(support, "ARTIFACT_DIRECTORY", directory)
    monkeypatch.setattr(support, "ROOT", root)
    return directory, support.stage_path(32)


@pytest.mark.parametrize("bad", ("../old.json", "/outside.json", "unissued.json",
                                 "working-associativity-closure-prefix-36-proof-bundle-v1.json"))
def test_output_basename_cannot_escape_the_four_exact_stage_targets(bad, output_scope):
    directory, _path = output_scope
    value = Path(bad) if bad.startswith("/") else directory / bad
    with pytest.raises(ValueError):
        exporter.destination(value)


@pytest.mark.parametrize("kind", ("file", "directory", "symlink", "fifo"))
def test_existing_output_targets_are_never_overwritten_or_followed(kind, output_scope):
    _directory, path = output_scope
    if kind == "file": path.write_bytes(b"unissued existing data")
    elif kind == "directory": path.mkdir()
    elif kind == "symlink": path.symlink_to(path.parent / "absent")
    else: os.mkfifo(path)
    with pytest.raises(ValueError, match="never overwritten"):
        exporter.destination(path)
    assert path.exists() or path.is_symlink()


def test_output_ancestor_link_is_rejected_without_following(output_scope):
    directory, path = output_scope
    real = directory.parent / "real-directory"
    real.mkdir()
    directory.rmdir()
    directory.symlink_to(real, target_is_directory=True)
    with pytest.raises(ValueError, match="linked or non-directory"):
        exporter.destination(path)
    assert list(real.iterdir()) == []


def test_foreign_output_directory_owner_is_rejected(output_scope, monkeypatch):
    _directory, path = output_scope
    actual = os.getuid()
    monkeypatch.setattr(os, "getuid", lambda: actual + 1)
    with pytest.raises(ValueError, match="foreign owner"):
        exporter.destination(path)
    assert not path.exists()


def test_unissued_transport_bytes_are_written_exclusively_without_becoming_proof(output_scope):
    _directory, path = output_scope
    payload = b"unissued inert transport fixture; not a proof bundle\n"
    exporter.write_exclusive(path, payload)
    assert path.read_bytes() == payload and path.stat().st_nlink == 1
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    with pytest.raises(ValueError, match="never overwritten"):
        exporter.write_exclusive(path, b"replacement must never be written")
    assert path.read_bytes() == payload


def test_failed_owned_transport_write_removes_only_its_new_inode(output_scope, monkeypatch):
    _directory, path = output_scope
    original, calls = exporter._resources, []
    class Rejected(Exception):
        pass
    def fail_after_write():
        value = original()
        calls.append(value)
        if len(calls) == 2:
            raise Rejected("deliberate post-write rejection")
        return value
    monkeypatch.setattr(exporter, "_resources", fail_after_write)
    with pytest.raises(Rejected):
        exporter.write_exclusive(path, b"unissued disposable transport data")
    assert len(calls) == 2 and not path.exists()


def test_failed_transport_never_deletes_a_replacement_inode(output_scope, monkeypatch):
    _directory, path = output_scope
    original, calls, retained = exporter._resources, [], []
    replacement = b"different test-owned inode, must be preserved"
    def replace_after_write():
        value = original()
        calls.append(value)
        if len(calls) == 2:
            retained.append(path.open("rb"))  # Prevent reuse of the original inode number.
            path.unlink()
            path.write_bytes(replacement)
            raise RuntimeError("deliberate replacement race")
        return value
    monkeypatch.setattr(exporter, "_resources", replace_after_write)
    try:
        with pytest.raises(ValueError, match="refuses to remove"):
            exporter.write_exclusive(path, b"unissued disposable transport data")
        assert path.read_bytes() == replacement
    finally:
        for handle in retained:
            handle.close()


@pytest.mark.parametrize("args", (("--task", "root"), ("--task", "bundle", "--name", PRINCIPALS[0]),
                                  ("--task", "bundle", "--through", "32"),
                                  ("--task", "bundle", "--receipt", "saved.json")))
def test_final_cli_has_no_partial_or_saved_receipt_acceptance_mode(args, monkeypatch):
    monkeypatch.setattr(checker, "verify_complete_bundle", _forbid)
    monkeypatch.setattr(checker, "verify_principal", _forbid)
    with pytest.raises(SystemExit) as error:
        checker.main(list(args))
    assert error.value.code == 2
