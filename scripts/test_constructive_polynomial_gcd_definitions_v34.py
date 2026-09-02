"""Exact canonical407-definition conservation; source syntax, never proof authority."""
from hashlib import sha256
import json
from pathlib import Path
import sys
import pytest

ROOT=Path(__file__).resolve().parents[1]
for path in (ROOT/"scripts",ROOT/"peano-lab/py"):
    if str(path) not in sys.path:sys.path.insert(0,str(path))
import constructive_polynomial_euclidean_definitions as previous
import constructive_polynomial_gcd_definitions_v34 as definitions
import constructive_polynomial_gcd_definition_graph_v34 as graph
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context

ALL=definitions.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
NEW=definitions.GCD_DEFINITIONS
EXPECTED=(("PolynomialShift",5),("FpPolynomialRightDivides",7),("CommonRepresentatives",11),
    ("FpPolynomialAlignedAdd",10),("FpPolynomialAlignedSubtract",10),
    ("FpPolynomialCommonRightDivisor",10),("FpPolynomialBezoutRepresentation",16),
    ("FpPolynomialZeroOrMonic",4),("FpPolynomialRightGcd",10),("FpPolynomialNormalizedGcd",10))

@pytest.fixture(scope="module")
def working_records():
    path=ROOT/"research/arithmetic-library/working/prime-field-gcd-notation-v1/complete-source-dag-v1.json"
    raw=path.read_bytes()
    assert sha256(raw).hexdigest()=="46b67494dca6941c80d4eb5af21b4d46e625c98357ae5eeb4f5993b8fa7bfdc2"
    return {row["name"]:row for row in json.loads(raw)["definitions"]}

def test_exact_new_positions_and_arities():
    assert tuple((item.name,item.arity) for item in NEW)==EXPECTED
    assert tuple(item.stable_id for item in NEW)==tuple(f"ND{i:04d}" for i in range(341,351))
    assert len(ALL)==407

@pytest.mark.parametrize("name",tuple(previous.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME))
def test_every_old397_object_identical(name):
    assert ALL[name] is previous.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[name]

@pytest.mark.parametrize("item",NEW,ids=lambda x:x.name)
def test_exact_working_expansion_identity(item,working_records):
    record=working_records[item.name]
    assert record["id"]==item.stable_id
    assert record["arity"]==item.arity
    assert record["parameters"]==list(item.parameters)
    assert record["expansion_sha256"]==sha256(item.template_source.encode()).hexdigest()
    assert record["dependencies"]==[ALL[name].stable_id for name in item.conceptual_dependencies]

@pytest.mark.parametrize("item",NEW,ids=lambda x:x.name)
def test_each_expansion_arrow_has_actual_occurrence(item):
    for name in item.conceptual_dependencies:
        reading=_FormulaCompactor((ALL[name],)).compact(item.template_source)
        assert ALL[name].stable_id in reading["statement_definition_uses"]

def test_exact407_884_dag_and_old_blueprint_aliases():
    records,order,layers=graph.reviewed_registry()
    assert len(records)==407
    assert sum(len(row["dependencies"]) for row in records.values())==884
    assert len(order)==407 and set(order)==set(ALL)
    assert graph.REVIEWED_BLUEPRINT_ALIASES is graph.previous.REVIEWED_BLUEPRINT_ALIASES
    for name in order:
        assert all(layers[parent]<layers[name] for parent in ALL[name].conceptual_dependencies)

@pytest.mark.parametrize("names",[[],None,("unknown",),("",),(True,)])
def test_unknown_or_malformed_definition_selection_rejects(names):
    with pytest.raises(ValueError):definitions.definition_closure(names)

def test_no_edition_or_working_alias_import():
    assert not any(name.startswith("peano_lab.library.editions") for name in sys.modules)
    assert not any(name.startswith("_working_") for name in sys.modules)
