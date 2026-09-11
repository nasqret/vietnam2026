"""Fresh audit protocol, exact raw ownership, and non-admission regressions."""
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_alpha_v35_jordan as audit


def test_registry_has_one_family_seven_roots_and_nine_actual_jobs():
    items = audit.registry()
    assert [(item.slug, item.frontier_count, len(item.modules), len(item.principal_roots))
        for item in items] == [('jordan-totient', 95, 6, 7)]
    assert 1 + len(items) + sum(len(item.principal_roots) for item in items) == 9
    assert audit.CPU_LIMITS == (170, 175)
    assert audit.WALL_SECONDS == 180
    assert audit.MAX_RSS_BYTES == 1536 * 1024 * 1024
    assert 'peano-lab/py/tests/test_campaign_research_v35_closure.py' in audit.CONTROL_SOURCES
    assert 'peano-lab/py/tests/test_alpha_v35_jordan_audit.py' in audit.CONTROL_SOURCES


def test_module_test_provenance_uses_real_shared_regression_file():
    for pin in audit.registry()[0].modules:
        path = audit.module_test_path(pin.module)
        assert path == 'peano-lab/py/tests/test_campaign_research_v35_closure.py'
        assert (ROOT / path).is_file()


def test_actual_audit_factories_produce95_normalized_admissions_from96_originals():
    from peano_lab.library import campaign_research_v35_closure as research
    actual = audit._owned(audit.registry()[0])
    assert actual == research.research_specs()
    assert len(actual) == 95 and len(research.raw_owned_specs()) == 96
    assert 'jordan_tuple_equal_refl' not in {row.name for row in actual}


def test_original_assembler_retains102_frontier_rows_with6_inherited_supports():
    from peano_lab.library import research_source_plan_v35 as source
    from peano_lab.library import campaign_bottom_layer_closure as original
    selected = source.source_selection()
    assert len(selected.frontier) == 102
    assert len(selected.frontier_specs) == 96
    assert len(selected.admitted_specs) == 95
    plan = original.bottom_layer_plan(selected.frontier)
    assert tuple(row.name for row in plan.rows) == tuple(row.name for row in selected.specs)
    assert plan.root_names == selected.root_names
    assert dict(selected.positions) == {row.name: row.node_id for row in plan.rows}


@pytest.mark.parametrize('value', (None, {}, object(), 'old receipt', True))
def test_saved_report_cannot_mint_fresh_proof_authority(value):
    with pytest.raises(audit.AuditError):
        audit.FreshProofAudit(value, '0' * 64, {}, 1)


@pytest.mark.parametrize('path', ('', '../escape', '/absolute', 'scripts//bad', 'scripts/../bad', 'scripts\\bad'))
def test_unsafe_source_path_rejected_before_open(path):
    with pytest.raises(audit.AuditError):
        audit._file_digest(path, 1024)


def test_forged_novelty_count_is_not_a_live_release_gate():
    with pytest.raises(audit.AuditError):
        audit._validate_report({'new_theorems': 96}, kind='novelty')
