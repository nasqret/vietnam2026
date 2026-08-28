"""Readable Euler contracts must retain their exact independently counted Phi."""

from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from constructive_bottom_layer_defined_adapter import (
    DEFINITIONS, compact_formula_source, compact_tactic_command,
)
from constructive_bottom_layer_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL, definition_closure,
)
from constructive_gaussian_factorization_definitions import (
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as PRIOR,
)
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.euler_units_candidate import make_euler_units_candidate_theorems
from peano_lab.library.theorems import TheoremSpec


ROWS = {row.name: row for row in make_euler_units_candidate_theorems(TheoremSpec)}


def test_phi_and_unit_count_are_the_exact_inherited_identities_in_the_adapter():
    by_name = {definition.name: definition for definition in DEFINITIONS}
    assert by_name["Phi"] is PRIOR["Phi"] is ALL["Phi"]
    assert by_name["Phi"].stable_id == "ND0184"
    assert by_name["UnitCount"] is PRIOR["UnitCount"] is ALL["UnitCount"]
    assert len(by_name) == len(DEFINITIONS)
    assert all(by_name[item.name] is item for item in definition_closure(("Phi", "UnitCount")))


def _checked_reading(name):
    row = ROWS[name]
    reading = compact_formula_source(row.statement)
    assert reading.receipt.exact_ast_equivalence is True
    assert reading.receipt.free_names == ()
    assert reading.expanded_source == row.statement
    assert "".join(part.text for part in reading.parts) == reading.defined_source
    assert _LocalDefinedParser(reading.defined_source, ALL).parse() == parse_formula_in_context(row.statement, [])
    return reading


def test_exact_compact_G014_endpoint_preserves_unit_phi_power_and_congruence():
    reading = _checked_reading("euler_theorem_for_units")
    assert reading.defined_source == (
        "∀ a. ∀ m. ∀ t. Lt(1,m) ∧ (Unit(a,m) ∧ Phi(m,t)) → "
        "∃ x. Pow(a,t,x) ∧ ModEq(m,x,1)"
    )
    used = {use.name for use in reading.receipt.definition_uses}
    assert {"Unit", "Phi", "Pow", "ModEq"} <= used
    assert "UnitResidue" not in used


def test_actual_counting_induction_keeps_unit_count_as_a_named_independent_graph():
    reading = _checked_reading("euler_unit_count_product_balance")
    assert reading.defined_source == (
        "∀ l. ∀ a. ∀ m. ∀ b. ∀ c. ∀ d. ∀ e. ∀ t. ∀ P. ∀ Q. ∀ w. "
        "UnitCount(m,l,t) → UnitScaledPrefix(a,m,b,c,d,e,l) → "
        "Product(b,c,l,P) → Product(d,e,l,Q) → Pow(a,t,w) → ModEq(m,w · P,Q)"
    )
    used = {use.name for use in reading.receipt.definition_uses}
    assert {"UnitCount", "UnitScaledPrefix", "Product", "Pow", "ModEq"} <= used


def test_actual_local_count_propositions_use_the_same_unit_count_identity():
    row = ROWS["euler_unit_count_product_balance"]
    matches = []
    for index, command in enumerate(row.script, 1):
        reading = compact_tactic_command(command, index)
        if reading.proposition is None:
            continue
        used = {use.name for use in reading.proposition.receipt.definition_uses}
        if "UnitCount" in used:
            assert reading.proposition.receipt.exact_ast_equivalence is True
            assert "UnitCount(" in reading.proposition.defined_source
            matches.append(reading)
    assert matches, "the actual predecessor-count induction lost the UnitCount name"


UNIT_SCALED_CONTRACT = (
    "forall i u v. Lt(i,l) -> BetaAt(b,c,i,u) -> BetaAt(d,e,i,v) -> "
    "((Coprime(i,m) -> ModEq(m,a*u,v)) /\\ "
    "(~Coprime(i,m) -> ModEq(m,u,v)))"
)

# Independently stated operation laws, not a call to the source's law builder.
FIELD_LAW_CLAUSES = (
    "Lt(0,p)",
    "Lt(1,p)",
    "~(0=1)",
    "forall a b. Lt(a,p) -> Lt(b,p) -> exists c. FpAdd(p,a,b,c) /\\ forall d. FpAdd(p,a,b,d) -> d=c",
    "forall a b c. FpAdd(p,a,b,c) -> FpAdd(p,b,a,c)",
    "forall a b c x y u v. FpAdd(p,a,b,x) -> FpAdd(p,x,c,u) -> FpAdd(p,b,c,y) -> FpAdd(p,a,y,v) -> u=v",
    "forall a b. Lt(a,p) -> Lt(b,p) -> exists c. FpMul(p,a,b,c) /\\ forall d. FpMul(p,a,b,d) -> d=c",
    "forall a b c. FpMul(p,a,b,c) -> FpMul(p,b,a,c)",
    "forall a b c x y u v. FpMul(p,a,b,x) -> FpMul(p,x,c,u) -> FpMul(p,b,c,y) -> FpMul(p,a,y,v) -> u=v",
    "forall a b c s x y u v. FpAdd(p,b,c,s) -> FpMul(p,a,s,u) -> FpMul(p,a,b,x) -> FpMul(p,a,c,y) -> FpAdd(p,x,y,v) -> u=v",
    "forall a b c s x y u v. FpAdd(p,b,c,s) -> FpMul(p,s,a,u) -> FpMul(p,b,a,x) -> FpMul(p,c,a,y) -> FpAdd(p,x,y,v) -> u=v",
    "forall a. Lt(a,p) -> FpAdd(p,a,0,a)",
    "forall a. Lt(a,p) -> FpAdd(p,0,a,a)",
    "forall a. Lt(a,p) -> FpMul(p,a,1,a)",
    "forall a. Lt(a,p) -> FpMul(p,1,a,a)",
    "forall a. Lt(a,p) -> FpMul(p,a,0,0)",
    "forall a. Lt(a,p) -> FpMul(p,0,a,0)",
    "forall a. Lt(a,p) -> exists b. FpNeg(p,a,b) /\\ forall c. FpNeg(p,a,c) -> c=b",
    "forall a. Lt(a,p) -> ~(a=0) -> exists b. FpInv(p,a,b) /\\ forall c. FpInv(p,a,c) -> c=b",
    "forall a b. FpMul(p,a,b,0) -> a=0 \\/ b=0",
)


def _conjunction(parts):
    result = f"({parts[-1]})"
    for part in reversed(parts[:-1]):
        result = f"({part}) /\\ ({result})"
    return result


@pytest.mark.parametrize("name,contract", (
    ("UnitScaledPrefix", UNIT_SCALED_CONTRACT),
    ("FpFieldLaws", _conjunction(FIELD_LAW_CLAUSES)),
))
def test_independently_written_named_operation_contract_matches_exact_ha(name, contract):
    definition = ALL[name]
    parser = _LocalDefinedParser(contract, ALL)
    parser.free = list(definition.parameters)
    assert parser.parse() == definition.template_formula
    assert tuple(parser.free) == definition.parameters


def test_field_law_contract_rejects_a_missing_nonzero_inverse_guard():
    original = _conjunction(FIELD_LAW_CLAUSES)
    unguarded = original.replace("Lt(a,p) -> ~(a=0) -> exists b. FpInv", "Lt(a,p) -> exists b. FpInv")
    assert unguarded != original
    parser = _LocalDefinedParser(unguarded, ALL)
    parser.free = ["p"]
    assert parser.parse() != ALL["FpFieldLaws"].template_formula
