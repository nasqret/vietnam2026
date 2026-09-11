"""Jordan v35 exact syntax, alias, source and original-kernel regression gates.

Metadata tests confer no proof authority. The native tests explicitly check
the real source body / whole unchanged artifact; release Lean gates are separate.
"""
from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from pathlib import Path

import pytest

from peano_lab.library import campaign_research_v35_closure as c
from peano_lab.library import research_source_plan_v35 as source
from peano_lab.library.theorems import TheoremSpec, _closed_formula

ROOT = Path(__file__).resolve().parents[3]
ALIAS = "jordan_tuple_equal_refl"
CANONICAL = "integer_vector_equal_components_zero"


def parent():
    from peano_lab.library import editions_v34
    return editions_v34


def test_exact_raw96_novel95_inventory_and_owned_sources():
    c.validate_research_metadata()
    assert c.EXPECTED_RESEARCH_METADATA_SHA256 == 'f054b171f8776d681d8584f50e1e790760cdb2f21753f514790dfb8fb14d67d9'
    assert len(c.FACTORIES) == 11
    assert len(c.FACTORY_BY_MODULE) == 6
    assert sum(owner.count for owner in c.FACTORIES) == 96
    assert len(c.RAW_OWNED_NAMES) == 96
    assert len(c.FRONTIER_NEW_NAMES) == 95
    assert dict(c.ALIASES) == {ALIAS: CANONICAL}
    assert c.FAMILIES[0].owned_names == c.FRONTIER_NEW_NAMES
    assert (c.FAMILIES[0].node_count, c.FAMILIES[0].bundle_edges, c.FAMILIES[0].body_nodes) == (359, 956, 22165)
    assert c.FAMILIES[0].rfc == 'research/arithmetic-library/alpha-v35-jordan-promotion-rfc-v1.md'
    assert (ROOT / c.FAMILIES[0].rfc).is_file()
    for name in c.RAW_OWNED_NAMES:
        owner = c.source_for(name)
        assert (ROOT / owner['path']).parent == c.source_root()
        assert owner['module'] in c.FACTORY_BY_MODULE


@pytest.mark.parametrize('owner', c.FACTORIES, ids=lambda owner: owner.factory)
def test_actual_callable_source_and_exact_raw_factory_bytes(owner):
    c.validate_research_source_bytes()
    module = import_module('peano_lab.library.' + owner.module)
    function = getattr(module, owner.factory)
    assert function.__module__ == module.__name__
    assert Path(module.__file__) == ROOT / owner.source
    rows = function(TheoremSpec)
    assert type(rows) is tuple and len(rows) == owner.count
    assert c._specs_digest(rows) == owner.specs_sha256
    for row in rows:
        assert c.source_for(row.name)['factory'] == owner.factory


def test_raw_alias_only_changes_four_explicit_tactic_references():
    raw = c.raw_owned_specs()
    normalized = c.normalize_owned_specs(raw, parent().ALPHA_CHECKED_SPECS)
    assert len(raw) == 96 and len(normalized) == 95
    prior = {row.name: row for row in parent().ALPHA_CHECKED_SPECS}
    alias = next(row for row in raw if row.name == ALIAS)
    assert _closed_formula(alias.statement) == _closed_formula(prior[CANONICAL].statement)
    assert alias.dependencies == prior[CANONICAL].dependencies == ('beta_at_unique',)
    changed = []
    originals = {row.name: row for row in raw}
    for row in normalized:
        old = originals[row.name]
        assert row.statement == old.statement and row.summary == old.summary
        assert row.dependencies == tuple(source.ALIASES.get(name, name) for name in old.dependencies)
        if row != old:
            changed.append(row.name)
            assert sum(a != b for a, b in zip(old.script, row.script, strict=True)) == 4
    assert changed == ['jordan_tuple_scan_append']
    assert c.normalized_spec(alias, parent().ALPHA_CHECKED_SPECS) is prior[CANONICAL]


@pytest.mark.parametrize('field,value', (
    ('statement', '0 = 1'), ('dependencies', ()), ('script', ('refl',)),
    ('name', 'invented'), ('summary', 'changed source contract'),
))
def test_changed_raw_inventory_cannot_be_normalized(field, value):
    raw = c.raw_owned_specs()
    changed = (replace(raw[0], **{field: value}), *raw[1:])
    with pytest.raises(c.ResearchClosureError):
        c.normalize_owned_specs(changed, parent().ALPHA_CHECKED_SPECS)


@pytest.mark.parametrize('command', (
    'intro jordan_tuple_equal_refl', 'have x : jordan_tuple_equal_refl',
    'rewrite jordan_tuple_equal_refl', 'exact jordan_tuple_equal_refl_suffix',
))
def test_alias_never_rewrites_formula_binder_or_partial_name(command):
    with pytest.raises(source.SourcePlanError):
        source.rename_reference(command)


def test_exact_raw_cone_is_closed_and_seven_roots_cover_every_node():
    plan = c.research_plan('jordan-totient', parent_specs=parent().ALPHA_CHECKED_SPECS)
    assert len(plan.rows) == 358 and len(plan.frontier_names) == 96
    assert len(plan.owned_names) == 95 and ALIAS not in plan.owned_names
    assert len(plan.root_names) == 7
    assert plan.frontier_specs_sha256 == source.RAW_SPECS_SHA256
    assert c._specs_digest(plan.specs) == source.COMPLETE_SPECS_SHA256
    table = {row.name: row for row in plan.rows}
    seen, pending = set(), list(plan.root_names)
    while pending:
        name = pending.pop()
        if name not in seen:
            seen.add(name)
            pending.extend(table[name].dependencies)
    assert seen == set(table)
    assert table[ALIAS].is_owned is False
    assert set(table) - set(c.RAW_OWNED_NAMES) <= set(parent().ALPHA_EDITION.by_name)
    for row in plan.rows:
        assert all(plan.positions[name] < row.node_id for name in row.dependencies)


@pytest.mark.parametrize('slug', ('', '../jordan-totient', 'missing', None, 1, True))
def test_unknown_family_fails_before_any_file_open(monkeypatch, slug):
    monkeypatch.setattr(Path, 'open', lambda *_a, **_k: pytest.fail('invalid selection opened a file'))
    with pytest.raises(c.ResearchClosureError):
        c.research_family(slug)


@pytest.mark.parametrize('field,value', (
    ('count', 96), ('artifact_bytes', 64_000_001), ('artifact', '../outside.json'),
    ('artifact_sha256', '0' * 64), ('root_names', ()), ('complete_specs_sha256', '0' * 64),
))
def test_changed_metadata_rejected_before_source_use(monkeypatch, field, value):
    monkeypatch.setattr(c, 'FAMILIES', (replace(c.FAMILIES[0], **{field: value}),))
    with pytest.raises(c.ResearchClosureError):
        c.validate_research_metadata()


def test_false_source_ownership_rejected(monkeypatch):
    changed = dict(c._SOURCE_OWNER_INDICES)
    changed[ALIAS] = 1
    monkeypatch.setattr(c, '_SOURCE_OWNER_INDICES', changed)
    with pytest.raises(c.ResearchClosureError):
        c.source_for(ALIAS)


def test_canonical_source_authentication_precedes_warm_source_cache(monkeypatch):
    c.raw_owned_specs()
    def changed():
        raise c.ResearchClosureError('changed bytes')
    monkeypatch.setattr(c, 'validate_research_source_bytes', changed)
    with pytest.raises(c.ResearchClosureError):
        c.raw_owned_specs()


def test_preserved_original_artifact_pin():
    family = c.FAMILIES[0]
    raw = c.read_research_bundle_bytes(family.slug, ROOT / family.artifact)
    assert len(raw) == 1620004
    assert sha256(raw).hexdigest() == '9164d35758d1fa15d18ec792a429cbb33fd4c511df5651b9f15d37bececf5ea7'


def test_parent_and_stable_are_unchanged_and_alias_not_reenrolled():
    from peano_lab.library import editions_v35 as v35
    p = parent()
    assert len(v35.ALPHA_ENTRIES) == 4318
    assert all(a is b for a, b in zip(v35.ALPHA_ENTRIES, p.ALPHA_ENTRIES))
    assert v35.STABLE_EDITION is p.STABLE_EDITION
    assert v35.STABLE_SPECS is p.STABLE_SPECS
    assert len(v35.STABLE_SPECS) == 432
    assert ALIAS not in v35.ALPHA_EDITION.by_name
    assert v35.ALPHA_EDITION.by_name[CANONICAL] is p.ALPHA_EDITION.by_name[CANONICAL]
    assert (v35.ALPHA_EDITION.edge_count, v35.ALPHA_EDITION.layer_count) == (14070, 53)


def test_native_normalized_scan_append_body_uses_existing_alpha_identity():
    from peano_lab.kernel.checker import check
    from peano_lab.kernel.formulas import Imp
    from peano_lab.library.campaign_lower_layer_closure import _reconstruct_body
    rows = c.research_specs()
    table = {row.name: row for row in (*parent().ALPHA_CHECKED_SPECS, *rows)}
    row = table['jordan_tuple_scan_append']
    assert CANONICAL in row.dependencies and ALIAS not in table
    body = _reconstruct_body(row, table)
    target = _closed_formula(row.statement)
    for name in reversed(row.dependencies):
        target = Imp(_closed_formula(table[name].statement), target)
    assert check((), body, target) is True


def test_native_complete_original_bundle_checks_every_body():
    from peano_lab.library.proof_bundle import decode_proof_bundle
    family = c.FAMILIES[0]
    bundle, target = decode_proof_bundle(c.read_research_bundle_bytes(
        family.slug, ROOT / family.artifact).decode())
    receipt = c.check_research_proof_bundle(family.slug, bundle, target)
    assert (receipt.kernel_calls, receipt.node_count, receipt.dependency_edges,
            receipt.total_body_nodes) == (359, 359, 956, 22165)


def test_native_runtime_checked_use_authenticates_alias_and_ordinary_target():
    from peano_lab.kernel.checker import check
    from peano_lab.library import editions_v35 as v35
    result = v35.replay('jordan_tuple_scan_append', edition='alpha')
    assert result.spec is v35.ALPHA_EDITION.by_name[result.spec.name].spec
    assert CANONICAL in result.spec.dependencies
    assert ALIAS not in result.spec.dependencies
    assert check((), result.certificate, result.formula)


def test_runtime_source_gate_cannot_be_bypassed_by_warm_cache(monkeypatch):
    from peano_lab.library import editions_v35 as v35
    called = []
    def changed(*_args):
        called.append(True)
        raise c.ResearchClosureError('current artifact changed')
    monkeypatch.setattr(c, 'read_research_bundle_bytes', changed)
    with pytest.raises(v35.EditionV35ReplayError):
        v35.replay('jordan_tuple_scan_append', edition='alpha')
    assert called == [True]


@pytest.fixture(scope='module')
def original_bundle_syntax():
    from peano_lab.library.proof_bundle import decode_proof_bundle
    family = c.FAMILIES[0]
    return decode_proof_bundle(c.read_research_bundle_bytes(
        family.slug, ROOT / family.artifact).decode())


@pytest.mark.parametrize('mutation', ('target', 'dependencies', 'node_order', 'packaging', 'missing_body'))
def test_changed_proof_inventory_rejected_before_kernel(monkeypatch, original_bundle_syntax, mutation):
    from peano_lab.kernel.formulas import Bot
    bundle, target = original_bundle_syntax
    plan = c.research_plan('jordan-totient')
    nodes = list(bundle.nodes)
    position = plan.positions['jordan_tuple_scan_append']
    if mutation == 'target':
        nodes[position] = replace(nodes[position], target=Bot())
    elif mutation == 'dependencies':
        nodes[position] = replace(nodes[position], dependencies=nodes[position].dependencies[:-1])
    elif mutation == 'node_order':
        nodes[position] = replace(nodes[position], node_id=position + 1)
    elif mutation == 'packaging':
        nodes[-1] = replace(nodes[-1], dependencies=nodes[-1].dependencies[:-1])
    else:
        nodes.pop()
    changed = replace(bundle, nodes=tuple(nodes))
    monkeypatch.setattr(c, 'check_proof_bundle', lambda *_a: pytest.fail('changed exact inventory reached proof checking'))
    with pytest.raises(c.ResearchClosureError):
        c.check_research_proof_bundle('jordan-totient', changed, target)


def test_native_false_body_cannot_reuse_a_correct_target_or_source_pin(original_bundle_syntax):
    from peano_lab.kernel.proofs import Hyp
    from peano_lab.library.proof_bundle import ProofBundleError
    bundle, target = original_bundle_syntax
    nodes = list(bundle.nodes)
    nodes[0] = replace(nodes[0], body=Hyp(0))
    with pytest.raises(ProofBundleError):
        c.check_research_proof_bundle('jordan-totient', replace(bundle, nodes=tuple(nodes)), target)
