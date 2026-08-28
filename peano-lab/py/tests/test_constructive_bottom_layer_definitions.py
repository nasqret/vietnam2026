"""Independent exact-definition, hygiene, and mixed-DAG checks for new proofs."""

from collections import Counter
from dataclasses import replace
from importlib import import_module
from pathlib import Path
import re
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import constructive_gaussian_factorization_definition_graph as prior_graph
import constructive_bottom_layer_definition_graph as graph
from constructive_gaussian_factorization_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PRIOR
from constructive_bottom_layer_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL,
    BOTTOM_LAYER_DEFINITIONS as NEW,
    BOTTOM_LAYER_REGISTRIES,
    definition_closure,
)
from constructive_bottom_layer_defined_adapter import compact_formula_source, compact_tactic_command
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context, parse_formula_with_names
from peano_lab.kernel.terms import ParseError
from peano_lab.library.theorems import TheoremSpec
from peano_lab.library import euler_units_residue_candidate as euler_residue
from peano_lab.library import euler_units_product_candidate as euler_product
from peano_lab.library import mobius_value_candidate as mobius
from peano_lab.library import prime_field_arithmetic_candidate as field
from peano_lab.library import prime_field_tables_candidate as field_tables
from peano_lab.library import prime_field_finiteness_candidate as field_finiteness
from peano_lab.library import divisor_sum_table_candidate as signed_tables
from peano_lab.library import divisor_sum_reindex_candidate as signed_reindex


MODULES = (
    "prime_field_arithmetic_candidate",
    "prime_field_tables_candidate", "prime_field_finiteness_candidate",
    "mobius_value_candidate", "mobius_prime_step_candidate",
    "divisor_sum_table_candidate", "divisor_sum_algebra_candidate", "divisor_sum_reindex_candidate",
    "euler_units_residue_candidate", "euler_units_product_candidate", "euler_units_candidate",
)
ROWS = tuple(
    row for name in MODULES
    for row in getattr(import_module("peano_lab.library." + name), "make_" + name + "_theorems")(TheoremSpec)
)

BUILDERS = {
    "FpElement": field.prime_field_carrier_relation,
    "FpAdd": field.prime_field_add_relation,
    "FpMul": field.prime_field_multiply_relation,
    "FpNeg": field.prime_field_negate_relation,
    "FpInv": field.prime_field_inverse_relation,
    "FpFieldLaws": field.prime_field_laws_relation,
    "AlternatingSignedUnit": mobius.alternating_signed_unit_relation,
    "HasPrimeSquareDivisor": mobius.has_prime_square_divisor_relation,
    "FactorParitySign": mobius.prime_factor_parity_sign_relation,
    "Mobius": mobius.mobius_value_relation,
    "Unit": euler_residue.modular_unit_relation,
    "UnitMultiplierPrefix": euler_residue.unit_multiplier_prefix_relation,
    "UnitProductFactor": euler_product.unit_product_factor_relation,
    "UnitProductPrefix": euler_product.unit_product_prefix_relation,
    "UnitScaledPrefix": euler_product.unit_scaled_prefix_relation,
    "FpZeroExtendedInv": field_tables.prime_field_zero_extended_inverse_relation,
    "FpAddGridValue": field_tables.prime_field_add_grid_value_relation,
    "FpMulGridValue": field_tables.prime_field_multiply_grid_value_relation,
    "FpAddPrefix": field_tables.prime_field_add_prefix_relation,
    "FpMulPrefix": field_tables.prime_field_multiply_prefix_relation,
    "FpNegPrefix": field_tables.prime_field_negate_prefix_relation,
    "FpInvPrefix": field_tables.prime_field_inverse_prefix_relation,
    "FpOperationTables": field_tables.prime_field_operation_tables_relation,
    "ArithTable": signed_tables.signed_arithmetic_table_relation,
    "ArithAt": signed_tables.signed_arithmetic_table_entry_relation,
    "SignedPrefixSum": signed_tables.signed_arithmetic_prefix_sum_relation,
    "ArithTableEqual": signed_tables.signed_arithmetic_table_equality_relation,
    "FpCardinality": field_finiteness.prime_field_cardinality_relation,
    "FpUnitSteps": field_finiteness.prime_field_unit_steps_relation,
    "FpUnitTrace": field_finiteness.prime_field_unit_trace_relation,
    "FpUnitMultiple": field_finiteness.prime_field_unit_multiple_relation,
    "FpCharacteristic": field_finiteness.prime_field_characteristic_relation,
    "FpFiniteStructure": field_finiteness.prime_field_finite_structure_relation,
    "ArithReindex": signed_reindex.signed_arithmetic_table_reindex_relation,
}


def test_all_historical_objects_and_dag_records_are_unchanged():
    old, _, _ = prior_graph.reviewed_registry()
    current, order, layers = graph.reviewed_registry()
    assert len(PRIOR) == len(old) == 284
    assert len(NEW) == 34 and len(ALL) == len(current) == 318
    assert all(ALL[name] is definition for name, definition in PRIOR.items())
    assert all(current[name] == record for name, record in old.items())
    assert tuple(item.stable_id for item in NEW) == tuple(f"ND{i:04d}" for i in range(228, 262))
    assert len({item.stable_id for item in ALL.values()}) == 318
    assert sum(len(item.conceptual_dependencies) for item in NEW) == 85
    assert Counter(item.name for _, items in BOTTOM_LAYER_REGISTRIES for item in items) == Counter(item.name for item in NEW)
    seen = set()
    for name in order:
        assert set(current[name]["dependencies"]) <= seen
        assert layers[name] == max((layers[parent] + 1 for parent in current[name]["dependencies"]), default=0)
        assert "proof_dependency" not in current[name]
        seen.add(name)


def test_no_new_definition_is_an_exact_duplicate_of_a_historical_identity():
    for definition in NEW:
        for old in PRIOR.values():
            if definition.arity == old.arity:
                assert definition.template_formula != old.template_formula, (definition.name, old.name)
    assert ALL["CanonicalModularResidue"] is PRIOR["CanonicalModularResidue"]
    assert ALL["CanonicalModularResidue"].stable_id == "ND0023"
    assert "FpResidue" not in ALL


def test_prime_field_reduction_is_literally_the_existing_nd0023():
    definition = ALL["CanonicalModularResidue"]
    source = field.prime_field_residue_relation(*definition.parameters, tag="independent", variables=definition.parameters)
    assert parse_formula_in_context(source, list(definition.parameters)) == definition.template_formula
    for operation in ("FpAdd", "FpMul"):
        assert ALL[operation].conceptual_dependencies == ("Lt", "CanonicalModularResidue")


def test_prime_field_enumeration_reuses_nd0141_with_exact_argument_alignment():
    definition = ALL["IdentityMatrixSelector"]
    assert definition is PRIOR["IdentityMatrixSelector"] and definition.stable_id == "ND0141"
    assert definition.parameters == ("b", "c", "l")
    source = field_finiteness.prime_field_enumeration_relation("l", "b", "c", tag="old_identity", variables=definition.parameters)
    assert parse_formula_in_context(source, list(definition.parameters)) == definition.template_formula
    assert "FpEnumeration" not in ALL
    assert "IdentityMatrixSelector" in ALL["FpCardinality"].conceptual_dependencies


def test_signed_table_packing_reuses_nd0058_without_a_duplicate_identity():
    definition = ALL["MatrixMinorFourCode"]
    assert definition is PRIOR["MatrixMinorFourCode"] and definition.stable_id == "ND0058"
    assert definition.parameters == ("z", "up", "us", "un", "ut")
    source = signed_tables.signed_arithmetic_table_representation_relation(*definition.parameters, tag="old_four_code", variables=definition.parameters)
    assert parse_formula_in_context(source, list(definition.parameters)) == definition.template_formula
    assert "ArithTableRep" not in ALL
    for name in ("ArithTable", "ArithAt", "SignedPrefixSum"):
        assert "MatrixMinorFourCode" in ALL[name].conceptual_dependencies


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_every_named_template_is_exactly_its_ha_ast(definition):
    parser = _LocalDefinedParser(f"{definition.name}({','.join(definition.parameters)})", ALL)
    parser.free = list(definition.parameters)
    assert parser.parse() == definition.template_formula
    assert tuple(parser.free) == definition.parameters
    assert parse_formula_in_context(definition.template_source, list(definition.parameters)) == definition.template_formula


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_nested_binders_repeated_compound_arguments_and_arity_are_hygienic(definition):
    arguments = tuple(("x", "y", "S (x+y)", "x*x")[index % 4] for index in range(definition.arity))
    substitutions = dict(zip(definition.parameters, arguments))
    pattern = r"\b(?:" + "|".join(re.escape(parameter) for parameter in definition.parameters) + r")\b"
    expanded = re.sub(pattern, lambda match: f"({substitutions[match.group()]})", definition.template_source)
    expected = parse_formula_in_context(f"forall x. exists y. ({expanded})", [])
    assert _LocalDefinedParser(f"forall x. exists y. {definition.name}({','.join(arguments)})", ALL).parse() == expected
    with pytest.raises(ParseError, match="expects"):
        _LocalDefinedParser(f"{definition.name}()", ALL).parse()


@pytest.mark.parametrize("name,builder", tuple(BUILDERS.items()))
def test_actual_public_relation_builder_matches_the_reviewed_definition(name, builder):
    definition = ALL[name]
    source = builder(*definition.parameters, tag="independent_surface", variables=definition.parameters)
    assert parse_formula_in_context(source, list(definition.parameters)) == definition.template_formula


@pytest.mark.parametrize("definition", NEW, ids=lambda item: item.name)
def test_every_declared_definition_premise_occurs_in_the_exact_expansion(definition):
    ancestors = definition_closure(definition.conceptual_dependencies)
    compact = _FormulaCompactor(ancestors).compact(definition.template_source)
    assert compact["exact_ast_equivalence"] is True
    used = set(compact["statement_definition_uses"])
    assert definition.stable_id not in used
    assert used <= {item.stable_id for item in ancestors}
    # Specialization can match two real graphs: FpNeg(p,a,b), for example,
    # is exactly FpAdd(p,a,b,0).  The display may choose either spelling.
    # Check each declared edge independently, so that such overlap cannot
    # hide a fabricated dependency or turn a valid edge into a false failure.
    for name in definition.conceptual_dependencies:
        child = ALL[name]
        isolated = _FormulaCompactor((child,)).compact(definition.template_source)
        assert isolated["exact_ast_equivalence"] is True
        assert child.stable_id in isolated["statement_definition_uses"]


@pytest.mark.parametrize("name,source", [
    ("FpElement", "Prime(p) /\\ Lt(a,p)"),
    ("FpAdd", "Lt(a,p) /\\ (Lt(b,p) /\\ CanonicalModularResidue(p,a+b,c))"),
    ("FpMul", "Lt(a,p) /\\ (Lt(b,p) /\\ CanonicalModularResidue(p,a*b,c))"),
    ("FpNeg", "FpAdd(p,a,b,0)"),
    ("FpInv", "~(a=0) /\\ FpMul(p,a,b,1)"),
    ("AlternatingSignedUnit", "(Even(n) /\\ z=2) \\/ (Odd(n) /\\ z=1)"),
    ("HasPrimeSquareDivisor", "exists p. Prime(p) /\\ Dvd(p*p,n)"),
    ("FactorParitySign", "exists b c l. PrimeFactorList(n,b,c,l) /\\ AlternatingSignedUnit(l,z)"),
    ("Mobius", "~(n=0) /\\ ((HasPrimeSquareDivisor(n) /\\ z=0) \\/ (Squarefree(n) /\\ FactorParitySign(n,z)))"),
    ("Unit", "Lt(1,m) /\\ exists b. Lt(b,m) /\\ ModEq(m,a*b,1)"),
    ("UnitProductFactor", "(Coprime(i,m) /\\ v=i) \\/ (~Coprime(i,m) /\\ v=1)"),
    ("UnitProductPrefix", "forall i. Lt(i,l) -> exists v. BetaAt(b,c,i,v) /\\ UnitProductFactor(m,i,v)"),
    ("UnitMultiplierPrefix", "forall i. Lt(i,l) -> exists r. BetaAt(b,c,i,r) /\\ CanonicalModularResidue(m,a*i,r)"),
    ("FpZeroExtendedInv", "Lt(a,p) /\\ (Lt(b,p) /\\ ((a=0 /\\ b=0) \\/ FpInv(p,a,b)))"),
    ("FpAddGridValue", "exists a b. i=a*p+b /\\ FpAdd(p,a,b,v)"),
    ("FpMulGridValue", "exists a b. i=a*p+b /\\ FpMul(p,a,b,v)"),
    ("FpAddPrefix", "forall i. Lt(i,l) -> exists v. BetaAt(b,c,i,v) /\\ FpAddGridValue(p,i,v)"),
    ("FpMulPrefix", "forall i. Lt(i,l) -> exists v. BetaAt(b,c,i,v) /\\ FpMulGridValue(p,i,v)"),
    ("FpNegPrefix", "forall i. Lt(i,l) -> exists v. BetaAt(b,c,i,v) /\\ FpNeg(p,i,v)"),
    ("FpInvPrefix", "forall i. Lt(i,l) -> exists v. BetaAt(b,c,i,v) /\\ FpZeroExtendedInv(p,i,v)"),
    ("FpOperationTables", "FpAddPrefix(p,ab,ac,p*p) /\\ (FpMulPrefix(p,mb,mc,p*p) /\\ (FpNegPrefix(p,nb,nc,p) /\\ FpInvPrefix(p,ib,ic,p)))"),
    ("ArithTable", "exists pb pc nb nc. MatrixMinorFourCode(F,pb,pc,nb,nc) /\\ forall i. Le(i,N) -> exists p n z. BetaAt(pb,pc,i,p) /\\ (BetaAt(nb,nc,i,n) /\\ SignedBalance(z,p,n))"),
    ("ArithAt", "exists pb pc nb nc p n. MatrixMinorFourCode(F,pb,pc,nb,nc) /\\ (BetaAt(pb,pc,i,p) /\\ (BetaAt(nb,nc,i,n) /\\ SignedBalance(z,p,n)))"),
    ("SignedPrefixSum", "exists pb pc nb nc p n. MatrixMinorFourCode(F,pb,pc,nb,nc) /\\ (Sum(pb,pc,l,p) /\\ (Sum(nb,nc,l,n) /\\ SignedBalance(z,p,n)))"),
    ("ArithTableEqual", "forall i a b. Lt(i,l) -> ArithAt(F,i,a) -> ArithAt(G,i,b) -> a=b"),
    ("FpCardinality", "IdentityMatrixSelector(b,c,p) /\\ ((forall i a. Lt(i,p) -> BetaAt(b,c,i,a) -> Lt(a,p)) /\\ ((forall i j a. Lt(i,p) -> Lt(j,p) -> BetaAt(b,c,i,a) -> BetaAt(b,c,j,a) -> i=j) /\\ (forall a. Lt(a,p) -> exists i. Lt(i,p) /\\ BetaAt(b,c,i,a))))"),
    ("FpUnitSteps", "forall i. Lt(i,n) -> exists u v. BetaAt(b,c,i,u) /\\ (BetaAt(b,c,S i,v) /\\ FpAdd(p,u,1,v))"),
    ("FpUnitTrace", "BetaAt(b,c,0,0) /\\ (BetaAt(b,c,n,r) /\\ FpUnitSteps(p,b,c,n))"),
    ("FpUnitMultiple", "exists b c. FpUnitTrace(p,b,c,n,r)"),
    ("FpCharacteristic", "FpUnitMultiple(p,p,0) /\\ forall n. Lt(n,p) -> ~(n=0) -> ~FpUnitMultiple(p,n,0)"),
    ("FpFiniteStructure", "FpOperationTables(p,ab,ac,mb,mc,nb,nc,ib,ic) /\\ (FpCardinality(p,eb,ec) /\\ (FpFieldLaws(p) /\\ FpCharacteristic(p)))"),
    ("ArithReindex", "forall i j a. Lt(i,l) -> BetaAt(r,s,i,j) -> ArithAt(F,j,a) -> ArithAt(G,i,a)"),
])
def test_independently_written_named_contract_is_the_exact_ha_formula(name, source):
    definition = ALL[name]
    parser = _LocalDefinedParser(source, ALL)
    parser.free = list(definition.parameters)
    assert parser.parse() == definition.template_formula
    assert tuple(parser.free) == definition.parameters


def test_units_are_not_confused_with_nonzero_residue_ranges():
    assert ALL["Unit"].stable_id == "ND0237"
    assert ALL["UnitResidue"].stable_id == "PD0030"
    assert ALL["Unit"].template_formula != ALL["UnitResidue"].template_formula
    # 2 is a nonzero residue modulo 4 but has no multiplicative inverse.
    assert 0 < 2 < 4 and not any((2 * b - 1) % 4 == 0 for b in range(4))
    # Arbitrarily large representatives are allowed by Unit, unlike the range.
    assert any((7 * b - 1) % 4 == 0 for b in range(4)) and not 7 < 4


def test_no_full_extension_field_alias_or_oracular_mobius_dependency():
    assert "FiniteField" not in ALL
    assert "FiniteField" not in graph.REVIEWED_BLUEPRINT_ALIASES
    mobius_names = {item.name for item in definition_closure(("Mobius",))}
    assert {"PrimeFactorList", "Squarefree", "HasPrimeSquareDivisor", "AlternatingSignedUnit"} <= mobius_names
    assert not {"MobiusInversion", "DivisorSumCancellation", "AssumedFactorization", "FpFieldLaws"} & mobius_names
    for name in ("FpAdd", "FpMul", "FpNeg", "FpInv"):
        assert "FpFieldLaws" not in {item.name for item in definition_closure((name,))}
    assert "FpFieldLaws" not in {item.name for item in definition_closure(("FpOperationTables",))}
    for name in ("ArithTable", "ArithAt", "SignedPrefixSum", "ArithTableEqual"):
        assert "Mobius" not in {item.name for item in definition_closure((name,))}
    assert "CanonicalModularResidue" not in ALL["FpUnitTrace"].conceptual_dependencies


@pytest.mark.parametrize("mutation", ["cycle", "unknown", "duplicate_id", "changed_ast"])
def test_malformed_additive_registry_fails_closed(mutation):
    selected = ALL["UnitProductPrefix"]
    if mutation == "cycle":
        selected = replace(selected, conceptual_dependencies=(selected.name,))
    elif mutation == "unknown":
        selected = replace(selected, conceptual_dependencies=("AnUnprovedOracle",))
    elif mutation == "duplicate_id":
        selected = replace(selected, stable_id="PD0001")
    else:
        selected = replace(selected, template_source="0=1")
    registries = tuple((route, tuple(selected if item.name == selected.name else item for item in definitions))
                       for route, definitions in graph.DEFAULT_REGISTRIES)
    with pytest.raises(graph.DefinitionGraphError):
        graph.reviewed_registry(registries)


@pytest.mark.parametrize("row", ROWS, ids=lambda item: item.name)
def test_every_new_theorem_statement_has_an_exact_defined_roundtrip(row):
    compact = compact_formula_source(row.statement)
    assert compact.receipt.exact_ast_equivalence
    assert compact.expanded_source == row.statement
    assert "".join(part.text for part in compact.parts) == compact.defined_source
    assert compact.receipt.free_names == ()
    assert _LocalDefinedParser(compact.defined_source, ALL).parse() == parse_formula_in_context(row.statement, [])


@pytest.mark.parametrize("row", ROWS, ids=lambda item: item.name)
def test_every_actual_local_proposition_has_an_exact_defined_roundtrip(row):
    for index, command in enumerate(row.script, 1):
        reading = compact_tactic_command(command, index)
        assert reading.expanded_command == command and reading.line_number == index
        assert "".join(part.text for part in reading.parts) == reading.defined_command
        if reading.proposition is not None:
            proposition = reading.proposition
            assert proposition.receipt.exact_ast_equivalence
            exact, names = parse_formula_with_names(proposition.expanded_source)
            parser = _LocalDefinedParser(proposition.defined_source, ALL)
            parser.free = list(names)
            assert parser.parse() == exact and tuple(parser.free) == names
