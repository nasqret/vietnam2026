"""Fast source-shape checks; explicit notation preflight is separately scheduled."""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def source(name):
    return (ROOT / "scripts" / name).read_text()


def function(name, function_name):
    return next(row for row in ast.parse(source(name)).body
                if isinstance(row, ast.FunctionDef) and row.name == function_name)


def test_source_public_entry_points_require_same_live_context_twice():
    for name in ("build_constructive_jordan_explorer_v35.py", "extend_constructive_jordan_campaign_v35.py"):
        calls = [ast.unparse(row.func) for row in ast.walk(function(name, "build_files_from_live"))
                 if isinstance(row, ast.Call)]
        assert calls.count("publication.require_live") == 2
        assert not any("LiveReleaseContext" in value or "FreshProofAudit" in value for value in calls)


def test_source_exact95_novel_pages_and_no_field_admission():
    text = source("build_constructive_jordan_explorer_v35.py")
    assert 'if row.name not in ALIASES' in text
    assert 'new_theorem_count=95' in text and 'source_owned_theorem_count=96' in text
    assert 'current_G091_prime_power_fields_proved=False' in text
    assert 'jordan_prime_power_product_formula_proved=False' in text
    assert 'canonical_admission_name=canonical' in text
    assert 'canonical_catalog_record=row' in text


def test_source_three_disjoint_graph_edge_types_and_proof_only_paths():
    text = source("build_constructive_jordan_explorer_v35.py")
    for kind in ("proof_dependency", "uses_definition", "definition_uses_definition"):
        assert 'kind="' + kind + '"' in text
    assert 'path_policy="proof_dependency_edges_only"' in text
    assert 'parents = [p for p in node["dependencies"] if p in tags]' in text


def test_source_conservative_registry_preserves407_and_exact11_identities():
    text = source("constructive_jordan_definitions_v35.py")
    node = function("constructive_jordan_definitions_v35.py", "definitions")
    rows = next(row.value for row in node.body if isinstance(row, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "rows" for target in row.targets))
    assert tuple(row.elts[0].value for row in rows.elts) == tuple(range(371, 382))
    assert 'known[n] is d' in text
    assert 'len(HISTORICAL_DEFINITIONS_BY_NAME) != 407' in text
    assert 'len(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME) != 418' in text
    assert "equal.stable_id!='ND0121'" in text
    assert 'exact_renaming_ast_verified=True' in text
    assert 'blueprint_expansion_is_kernel_checked=False' in text


def test_source_preserves_all_non_jordan_milestones_and_original_contract():
    text = ast.unparse(function("extend_constructive_jordan_campaign_v35.py", "_preserved"))
    assert "before['id'] != 'G008'" in text and "before == after" in text
    assert "{'status', 'why'}" in text
    assert "original['definitions'] == result['definitions']" in text


def test_source_stage_preserves_readability_assets_and_disables_public_builds():
    text = source("stage_constructive_jordan_publication_v35.py")
    assert '10471f7ace1719110af485479052a87dca4cda5a410515d556ebce5473adefc9' in text
    assert 'deploy/proofs/lean-selector-disabled.js' in text
    assert 'set(files) & set(parents) == REPLACEMENTS' in text
    assert 'strip_reading_layer(revised) == raw' in text
    assert 'len(records) == 190' in text
    assert 'public_on_demand_builds=False' in text
    assert 'path.open("xb")' in text
    assert 'inventory(directory) == expected' in text


def _notation_preflight():
    """Explicit bounded source/notation check; never authorize publication."""
    from build_constructive_jordan_explorer_v35 import _source_only_syntax, specs
    from constructive_jordan_definitions_v35 import (
        ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as definitions, HISTORICAL_DEFINITIONS_BY_NAME,
        JORDAN_DEFINITIONS, definition_closure,
    )
    from constructive_formula_compactor import _LocalDefinedParser
    from peano_lab.kernel.formulas import parse_formula_with_names, parse_formula_in_context
    assert len(definitions) == 418 and all(definitions[name] is value
        for name, value in HISTORICAL_DEFINITIONS_BY_NAME.items())
    assert tuple(row.stable_id for row in JORDAN_DEFINITIONS) == tuple(f"ND{i:04d}" for i in range(371, 382))
    rows = specs()
    readings, displayed = _source_only_syntax()
    for row, reading in zip(rows, readings, strict=True):
        original, names = parse_formula_with_names(row.statement)
        assert not names
        parser = _LocalDefinedParser(reading["defined_statement"], definitions)
        assert parser.parse() == original
        assert len(reading["defined_script"]) == len(row.script)
    for row in displayed:
        item = definitions[row["name"]]
        assert parse_formula_in_context(row["expanded_template"], list(item.parameters)) == item.template_formula
    return dict(proof_authority=False, admission_performed=False, source_theorems=95,
                definitions=418, displayed_definitions=len(displayed))
