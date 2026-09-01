"""Focused source/inert scaffold checks; no successful proof fixture or mock."""
import ast
from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sys
from types import ModuleType

import pytest

import working_gcd_closure_support as s
import export_working_gcd_closure as export
import check_working_gcd_closure as check


@pytest.fixture(scope='module')
def laws():
    # This checkpoint intentionally does not bind unrelated mutable families.
    return s.load_candidate_state(('laws',))


def test_actual_frozen95_prefix_and_selected_source_snapshot(laws):
    assert laws.rows[:95] == s.prior.load_candidate_state().rows
    assert laws.families == ('laws',)
    assert len(laws.source_pins) == 1
    pin = laws.source_pins[0]
    assert pin.path.endswith('/prime_field_polynomial_gcd_bezout_laws_candidate.py')
    assert sha256(s.read_pin(pin)).hexdigest() == pin.sha256
    assert s.preserve_prior().specs_sha256 == s.prior.SPECS_SHA256


@pytest.mark.parametrize('families', [(), ('unknown',), ('laws', 'laws'), ['laws']])
def test_invalid_family_ownership_rejected(families):
    with pytest.raises(s.WorkingError):
        s.load_candidate_state(families)


def test_foreign_private_controller_owner_preserved(monkeypatch):
    foreign = ModuleType(s._PRIVATE_PRIOR_NAME)
    monkeypatch.setitem(sys.modules, s._PRIVATE_PRIOR_NAME, foreign)
    with pytest.raises(ValueError):
        s._load_prior()
    assert sys.modules[s._PRIVATE_PRIOR_NAME] is foreign


def test_inert_seed_target_coverage_and_role_boundary(laws):
    selected = s.select_support(laws)
    coverage = s.inert_coverage(selected, (s.PRIOR95_SEED,))
    assert coverage['raw_json_only'] and not coverage['proof_authority']
    assert not coverage['proof_bodies_decoded'] and not coverage['original_ha_checked']
    assert coverage['covered_targets'] >= 438
    assert selected.role(laws.rows[0].name) == 'prior_non_admitted_euclidean'
    assert selected.role(laws.rows[-1].name) == 'new_non_admitted_gcd'
    assert selected.role(selected.support[0].name) == 'inherited_canonical_source'
    with pytest.raises(s.WorkingError): selected.role('not_in_the_cone')


def test_inert_coverage_detects_a_wrong_ordered_premise(laws):
    selected = s.select_support(laws)
    target = next(r for r in selected.complete_specs if r.dependencies and r.name in
                  {old.name for old in laws.rows[:95]})
    changed = replace(target, dependencies=target.dependencies + (target.name,))
    attack = replace(selected, complete_specs=tuple(changed if r.name == target.name else r
                                                   for r in selected.complete_specs))
    coverage = s.inert_coverage(attack, (s.PRIOR95_SEED,))
    assert target.name in coverage['missing_names']


@pytest.mark.parametrize('fault', ['digest', 'old_prefix', 'duplicate'])
def test_changed_snapshot_cannot_pass_source_validation(laws, fault):
    if fault == 'digest': attack = replace(laws, specs_sha256='0'*64)
    elif fault == 'old_prefix':
        rows = (replace(laws.rows[0], summary='altered'), *laws.rows[1:])
        attack = replace(laws, rows=rows, specs_sha256=s.closure._specs_digest(rows))
    else:
        rows = (*laws.rows, laws.rows[-1])
        attack = replace(laws, rows=rows, specs_sha256=s.closure._specs_digest(rows))
    with pytest.raises(s.WorkingError): s.validate_state(attack)


@pytest.mark.parametrize('gate', ['authoring', 'metadata', 'bundle', 'root', 'binding'])
def test_unfrozen_scaffold_cannot_run_any_positive_gate(gate, laws, monkeypatch, tmp_path):
    monkeypatch.setattr(s, 'FROZEN_SOURCE_PINS', None)
    def forbidden(*args, **kwargs):
        pytest.fail('unfrozen source reached a proof or original parent execution route')
    monkeypatch.setattr(s.closure, 'parent_snapshot', forbidden)
    monkeypatch.setattr(s.closure, 'assemble_bottom_layer_bundle', forbidden)
    monkeypatch.setattr(s.closure, 'check_bottom_layer_bundle', forbidden)
    monkeypatch.setattr(s.closure, 'replay_bottom_layer_theorem', forbidden)
    monkeypatch.setattr(check.independent, '_lean_check', forbidden)
    with pytest.raises(s.WorkingError):
        if gate == 'authoring': export.export_authoring_bundle(999, tmp_path/'unwanted.json', seed_bundles=())
        elif gate == 'metadata': check.global_metadata_report()
        elif gate == 'bundle': check.verify_complete_bundle()
        elif gate == 'root': check.verify_principal('invented_root')
        else: s.state_binding(laws, final=True)
    assert not (tmp_path/'unwanted.json').exists()


def function_tree(path, name):
    module = ast.parse(path.read_text())
    return next(item for item in module.body if isinstance(item, ast.FunctionDef) and item.name == name)


@pytest.mark.parametrize('name', ['_directory_identity', '_resources', 'write_exclusive'])
def test_original_exclusive_writer_and_resource_route_ast_preserved(name):
    old = function_tree(s.ROOT/s.PRIOR_RELATIVE/'export_working_euclidean_closure.py', name)
    new = function_tree(Path(export.__file__), name)
    assert ast.dump(old, include_attributes=False) == ast.dump(new, include_attributes=False)


def test_real_ha_same_payload_lean_and_empty_context_routes_remain_present():
    tree = function_tree(Path(check.__file__), 'verify_complete_bundle')
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)]
    ha = next(c for c in calls if ast.unparse(c.func) == 'support.closure.check_bottom_layer_bundle')
    lean = next(c for c in calls if ast.unparse(c.func) == 'independent._lean_check')
    assert [ast.unparse(a) for a in ha.args] == ['execution.frontier', 'bundle', 'target']
    assert ast.unparse(lean.args[-1]) == 'payload'
    root = function_tree(Path(check.__file__), 'verify_principal')
    empty = next(c for c in ast.walk(root) if isinstance(c, ast.Call) and ast.unparse(c.func) == 'check')
    assert [ast.unparse(a) for a in empty.args] == ['()', 'proof.certificate', 'formula']


def test_diagnostic_uses_explicit_core_and_checks_actual_inputs_in_finally():
    tree = function_tree(s.HERE/'development_check.py', 'main')
    call = next(c for c in ast.walk(tree) if isinstance(c, ast.Call)
                and ast.unparse(c.func) == 'replay_candidate_bodies')
    assert [(k.arg, ast.unparse(k.value)) for k in call.keywords] == [('core', 'core')]
    final = next(node.finalbody for node in ast.walk(tree) if isinstance(node, ast.Try) and node.finalbody)
    text = '\n'.join(ast.unparse(node) for node in final)
    assert 'support.check_pin' in text and 'support.preserve_prior()' in text
    assert 'authoring_rss_bytes()' in text


def test_novelty_uses_parsed_ast_not_spelling_or_saved_receipts():
    row = s.TheoremSpec('a', 'forall x. x=x', (), ('intro x', 'refl'), '')
    alias = replace(row, name='b', statement='forall y. y = y')
    distinct = replace(row, name='c', statement='forall x. S x=S x')
    assert check._novelty_pairs((row, alias), ()) == (('b', 'a'),)
    assert check._novelty_pairs((row,), (alias, distinct)) == (('a', 'b'),)


@pytest.fixture(scope='module')
def frozen():
    return s.require_frozen()


def test_actual_final_source_inventory_and_all_stage_cones(frozen):
    assert len(frozen.rows) == 119
    assert frozen.specs_sha256 == '72701944f71e8d93c55bcf29d27fc92ac616452801ab75c3e478df4d77df4c38'
    assert s.PHASES == (99, 101, 102, 103, 104, 105, 108, 111, 112, 119)
    expected = ((443,1390,18),(446,1399,20),(447,1404,18),(448,1409,18),
                (449,1411,17),(463,1458,13),(466,1463,12),(472,1479,14),
                (484,1536,13),(492,1565,13))
    for through, metrics in zip(s.PHASES, expected):
        selected = s.select_support(frozen, tuple(r.name for r in frozen.rows[:through]))
        assert (len(selected.complete_specs), sum(len(r.dependencies) for r in selected.complete_specs),
                len(selected.root_names)) == metrics == s.stage_metrics(through)
    assert s.previous_through(105) == 104 and s.previous_through(112) == 111
    assert len(s.PRINCIPAL_ROOTS) == 14 and len(set(s.PRINCIPAL_ROOTS)) == 14
    assert s.PRINCIPAL_ROOTS[:-1] == s.FINAL_MAXIMAL_ROOTS
    assert s.PRINCIPAL_ROOTS[-1] == 'prime_field_polynomial_bezout_is_right_gcd'


def test_actual_first_stage_seeds_cover_all_preexisting_targets(frozen):
    selected = s.select_support(frozen, tuple(r.name for r in frozen.rows[:99]))
    pins = s.seed_inventory(s.required_seed_paths(99), through=99)
    assert pins == (s.PRIOR95_SEED, s.SEED_PINS[1])
    report = s.seed_coverage(selected, pins)
    assert report['preexisting_targets'] == report['covered_targets'] == 439
    assert report['missing_names'] == [] and not report['proof_authority']
    assert report['seeds'][1]['newly_covered_names'] == ['prime_field_polynomial_add_zero_right']


@pytest.mark.parametrize('field', ['FROZEN_SOURCE_PINS','FROZEN_TEST_PINS','SPECS_SHA256',
    'NAMES_SHA256','COMPONENT_SPECS','PHASES','STAGE_RECORDS','STAGE_SEEDS','SEED_PINS',
    'PRINCIPAL_ROOTS','PRINCIPAL_STATEMENT_SHA256','FINAL_MAXIMAL_ROOTS'])
def test_registration_mutation_rejected_before_any_worker(field, monkeypatch):
    original = getattr(s, field)
    monkeypatch.setattr(s, field, '0'*64 if type(original) is str else original[:-1])
    with pytest.raises(s.WorkingError): s.require_registration()


@pytest.mark.parametrize('fault', ['reversed','missing','extra','foreign'])
def test_exact_real_seed_policy_rejects_wrong_inputs(fault):
    seeds = s.required_seed_paths(99)
    attack = {'reversed':seeds[::-1], 'missing':seeds[:1], 'extra':seeds+seeds[:1],
              'foreign':(s.HERE/'foreign.json',)}[fault]
    with pytest.raises(s.WorkingError): s.seed_inventory(attack, through=99)


def test_missing_artifact_is_not_a_successful_final_gate(monkeypatch):
    monkeypatch.setattr(check, 'FINAL_ARTIFACT', None)
    with pytest.raises(s.WorkingError): check.require_final_inventory()


def test_frozen_bytes_are_authenticated_before_source_execution(monkeypatch):
    original = s.snapshot_source
    def poisoned(path):
        pin, raw = original(path)
        if path.name == 'prime_field_polynomial_gcd_bezout_laws_candidate.py':
            return replace(pin, sha256='0'*64), b'raise AssertionError("must not execute")'
        return pin, raw
    monkeypatch.setattr(s, 'snapshot_source', poisoned)
    with pytest.raises(s.WorkingError, match='before execution'):
        s.load_candidate_state(('laws',))
