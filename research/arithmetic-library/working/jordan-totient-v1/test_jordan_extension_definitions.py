"""New Jordan proofs reuse the reviewed definitions with exact AST equality."""
from functools import lru_cache
import importlib.util
from pathlib import Path
import pytest

from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_with_names
from peano_lab.library.theorems import TheoremSpec
from jordan_unit_modulus_candidate import make_jordan_unit_modulus_candidate_theorems
from jordan_prime_power_characterization_candidate import make_jordan_prime_power_characterization_candidate_theorems

ROWS = (make_jordan_unit_modulus_candidate_theorems(TheoremSpec)
        + make_jordan_prime_power_characterization_candidate_theorems(TheoremSpec))


@lru_cache(None)
def notation():
    path = Path(__file__).parent.parent / 'jordan-orders-fields-v1/existence_definition_dag.py'
    loader = importlib.util.spec_from_file_location('_jordan_extension_existing_definitions', path)
    registry = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(registry)
    definitions = registry.definition_closure(('JordanTotient', 'JordanPrimitiveTuple',
        'BetaPrefixInto', 'Pow', 'Prime', 'IntegerVectorZero'))
    return registry, _FormulaCompactor(definitions)


@pytest.mark.parametrize('row', ROWS, ids=lambda r: r.name)
def test_statement_round_trip_through_existing_definition_dag(row):
    registry, compactor = notation()
    before = tuple(registry.ALL_DEFINITIONS.items())
    formula, names = parse_formula_with_names(row.statement)
    reading = compactor.compact(row.statement)
    parser = _LocalDefinedParser(reading['defined_statement'], compactor.by_name)
    parser.free = list(names)
    assert parser.parse() == formula and tuple(parser.free) == names
    assert tuple(registry.ALL_DEFINITIONS.items()) == before
    assert len(before) == 493
    assert reading['statement_definition_uses']
    if row.name == 'jordan_totient_at_one':
        assert registry.ALL_DEFINITIONS['JordanTotient'].stable_id in reading['statement_definition_uses']
