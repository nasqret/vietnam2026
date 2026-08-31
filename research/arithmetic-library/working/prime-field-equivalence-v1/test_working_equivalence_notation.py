"""Conservative notation tests, not theorem or admission acceptance fixtures."""

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import importlib.util
from pathlib import Path
import sys

import pytest

import working_equivalence_notation as notation
from constructive_formula_compactor import _LocalDefinedParser
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.library.theorems import TheoremSpec


HERE = Path(__file__).resolve().parent
EXPECTED_NAMES = (
    "prime_field_polynomial_equivalent_implies_left_pad",
    "prime_field_polynomial_add_left_pad_output",
    "prime_field_polynomial_subtract_left_pad_output",
    "prime_field_polynomial_add_equivalent_congruent",
    "prime_field_polynomial_subtract_equivalent_congruent",
    "prime_field_polynomial_convolution_equivalent_congruent_left",
    "prime_field_polynomial_convolution_equivalent_congruent_right",
    "prime_field_polynomial_convolution_equivalent_congruent",
)
EXPECTED_USES = (
    ("PolynomialEquivalent", "PolynomialLeftPad"),
    ("Prime", "FpPolyAdd", "PolynomialLeftPad"),
    ("Prime", "FpCoefficientSubtraction", "PolynomialLeftPad"),
    ("Prime", "FpPolyAdd", "PolynomialEquivalent"),
    ("Prime", "FpCoefficientSubtraction", "PolynomialEquivalent"),
    ("FpPolyProduct", "PolynomialEquivalent"),
    ("FpPolyProduct", "PolynomialEquivalent"),
    ("FpPolyProduct", "PolynomialEquivalent"),
)

# Independent human-readable contracts in the already reviewed notation.
# These are checked against actual source ASTs, not used as proof premises.
NAMED_PRINCIPALS = {
    EXPECTED_NAMES[0]: (
        "forall b c L t d e. PolynomialEquivalent(b,c,L,d,e,t+L) -> "
        "PolynomialLeftPad(b,c,L,t,d,e)"),
    EXPECTED_NAMES[3]: (
        "forall p ab ac bb bc cb cc L AB AC BB BC CB CC K. Prime(p) -> "
        "PolynomialEquivalent(ab,ac,L,AB,AC,K) -> PolynomialEquivalent(bb,bc,L,BB,BC,K) -> "
        "FpPolyAdd(p,ab,ac,bb,bc,cb,cc,L) -> FpPolyAdd(p,AB,AC,BB,BC,CB,CC,K) -> "
        "PolynomialEquivalent(cb,cc,L,CB,CC,K)"),
    EXPECTED_NAMES[4]: (
        "forall p ab ac bb bc cb cc L AB AC BB BC CB CC K. Prime(p) -> "
        "PolynomialEquivalent(ab,ac,L,AB,AC,K) -> PolynomialEquivalent(bb,bc,L,BB,BC,K) -> "
        "FpCoefficientSubtraction(p,ab,ac,bb,bc,cb,cc,L) -> "
        "FpCoefficientSubtraction(p,AB,AC,BB,BC,CB,CC,K) -> PolynomialEquivalent(cb,cc,L,CB,CC,K)"),
    EXPECTED_NAMES[7]: (
        "forall p ab ac L bb bc M cb cc N AB AC H BB BC I CB CC K. ~(p=0) -> "
        "PolynomialEquivalent(ab,ac,L,AB,AC,H) -> PolynomialEquivalent(bb,bc,M,BB,BC,I) -> "
        "FpPolyProduct(p,ab,ac,L,bb,bc,M,cb,cc,N) -> FpPolyProduct(p,AB,AC,H,BB,BC,I,CB,CC,K) -> "
        "PolynomialEquivalent(cb,cc,N,CB,CC,K)"),
}


def _editions():
    return {name for name in sys.modules if name.startswith("peano_lab.library.editions")}


@pytest.fixture(scope="module")
def actual_rows():
    # The unchanged old adapter creates only absent, byte-pinned temporary
    # mathematical names. Factories below construct source syntax, no proofs.
    import working_euclidean_extension_support as prior
    before = _editions()
    rows = []
    with prior.temporary_working_aliases():
        for name in ("prime_field_polynomial_equivalence_candidate",
                     "prime_field_polynomial_convolution_congruence_candidate"):
            path = HERE / (name + ".py")
            spec = importlib.util.spec_from_file_location("_notation_" + name, path)
            module = importlib.util.module_from_spec(spec)
            exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
            rows.extend(getattr(module, "make_" + name + "_theorems")(TheoremSpec))
    assert _editions() == before
    assert tuple(row.name for row in rows) == EXPECTED_NAMES
    return tuple(rows)


@pytest.fixture(scope="module")
def actual_audit(actual_rows):
    return notation.audit_rows(actual_rows)


def test_registry_objects_routes_and_all865_edges_are_reused_literally():
    records, order, layers = notation.reviewed_registry()
    old_records, old_order, old_layers = notation.previous_graph.reviewed_registry()
    assert notation.DEFINITIONS is notation.previous.ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
    assert notation.REGISTRIES is notation.previous_graph.DEFAULT_REGISTRIES
    assert notation.definition_closure is notation.previous.definition_closure
    assert (records, order, layers) == (old_records, old_order, old_layers)
    assert len(records) == 397 and sum(len(row["dependencies"]) for row in records.values()) == 865
    assert len({row["id"] for row in records.values()}) == 397
    seen = set()
    for name in order:
        assert set(records[name]["dependencies"]) <= seen
        seen.add(name)


@pytest.mark.parametrize("index", range(8), ids=EXPECTED_NAMES)
def test_every_actual_statement_has_exact_named_roundtrip_and_expected_reused_notation(actual_rows, actual_audit, index):
    row, node = actual_rows[index], actual_audit["nodes"][index]
    assert node["name"] == row.name and node["statement"] == row.statement
    assert node["dependencies"] == list(row.dependencies)
    compact = node["defined"]
    assert compact["exact_ast_equivalence"] is True and compact["free_names"] == []
    parsed = _LocalDefinedParser(compact["defined_statement"], notation.DEFINITIONS).parse()
    assert parsed == parse_formula_in_context(row.statement, [])
    expected_ids = {notation.DEFINITIONS[name].stable_id for name in EXPECTED_USES[index]}
    assert expected_ids <= compact["statement_definition_uses"].keys()
    assert compact["expanded_statement_sha256"] == sha256(row.statement.encode()).hexdigest()
    assert compact["defined_statement_sha256"] == sha256(compact["defined_statement"].encode()).hexdigest()
    assert Counter(part["definition"] for part in compact["statement_parts"] if part["kind"] == "definition") == compact["statement_definition_uses"]
    assert node["authority"] == "source-syntax-only" and node["proof_acceptance_performed"] is False


@pytest.mark.parametrize("name", tuple(NAMED_PRINCIPALS))
@pytest.mark.parametrize("outer", ("", "forall x. ", "forall p. exists ab. "))
def test_independent_named_principal_contracts_reexpand_with_outer_binder_hygiene(actual_rows, name, outer):
    row = next(row for row in actual_rows if row.name == name)
    named = outer + "(" + NAMED_PRINCIPALS[name] + ")"
    expanded = outer + "(" + row.statement + ")"
    assert _LocalDefinedParser(named, notation.DEFINITIONS).parse() == parse_formula_in_context(expanded, [])


def test_all_mixed_edges_have_exact_separate_meanings(actual_rows, actual_audit):
    edges = actual_audit["edges"]
    assert set(edge["kind"] for edge in edges) == {
        "proof_dependency", "uses_definition", "definition_uses_definition"}
    proof = [edge for edge in edges if edge["kind"] == "proof_dependency"]
    assert proof == [{"kind": "proof_dependency", "source": name, "target": row.name}
                     for row in actual_rows for name in row.dependencies]
    usage = [edge for edge in edges if edge["kind"] == "uses_definition"]
    assert usage == [{"kind": "uses_definition", "source": node["id"], "target": name, "occurrence_count": count}
                     for node in actual_audit["nodes"] for name, count in node["defined"]["statement_definition_uses"].items()]
    definitions = {row["id"]: row for row in actual_audit["definitions"]}
    assert all(edge["target"] in definitions for edge in usage)
    expansions = [edge for edge in edges if edge["kind"] == "definition_uses_definition"]
    assert expansions == [{"kind": "definition_uses_definition", "source": row["id"], "target": name}
                          for row in actual_audit["definitions"] for name in row["dependencies"]]
    assert all(edge["source"] in definitions and edge["target"] in definitions for edge in expansions)
    assert actual_audit["proof_dependency_count"] == len(proof)
    assert actual_audit["definition_use_count"] == len(usage)
    assert actual_audit["definition_expansion_count"] == len(expansions)


def test_proof_paths_cannot_follow_definition_arrows_or_claim_unresolved_cone(actual_rows, actual_audit):
    assert actual_audit["path_policy"] == "proof_dependency_edges_only"
    assert actual_audit["external_dependencies_resolved"] is False
    names = {row.name for row in actual_rows}
    expected_external = {name for row in actual_rows for name in row.dependencies if name not in names}
    assert actual_audit["external_dependencies"] == sorted(expected_external)
    assert "supplied_theorems_only" in actual_audit["proof_path_scope"]
    for row in actual_rows:
        path = actual_audit["proof_paths"][row.name]
        assert path[-1] == row.name and set(path) <= names
        for left, right in zip(path, path[1:]):
            target = next(item for item in actual_rows if item.name == right)
            assert left in target.dependencies
    assert max(map(len, actual_audit["proof_paths"].values())) == 3
    assert actual_audit["proof_acceptance_performed"] is False
    assert actual_audit["admission_performed"] is False and actual_audit["publication_performed"] is False
    assert actual_audit["new_definition_count"] == 0


@pytest.mark.parametrize("bad", (None, [], (), "rows", (object(),)))
def test_non_specification_inputs_are_rejected(bad):
    with pytest.raises(notation.NotationError, match="tuple of theorem"):
        notation.audit_rows(bad)


@pytest.mark.parametrize("bad_name", ("", "bad name", "bad/name", None, [], "ND0336"))
def test_bad_or_shadowing_names_are_rejected(actual_rows, bad_name):
    with pytest.raises(notation.NotationError, match="names"):
        notation.audit_rows((replace(actual_rows[0], name=bad_name),))


@pytest.mark.parametrize("attack", ("duplicate", "self", "forward", "repeated_dependency", "definition_dependency", "bad_dependency"))
def test_proof_topology_rejects_cycles_duplicates_and_definition_id_collisions(actual_rows, attack):
    first, second = actual_rows[:2]
    rows = {
        "duplicate": (first, first),
        "self": (replace(first, dependencies=(first.name,)),),
        "forward": (replace(first, dependencies=(second.name,)), second),
        "repeated_dependency": (replace(first, dependencies=("le_total", "le_total")),),
        "definition_dependency": (replace(first, dependencies=("ND0336",)),),
        "bad_dependency": (replace(first, dependencies=(None,)),),
    }[attack]
    with pytest.raises(notation.NotationError):
        notation.audit_rows(rows)


@pytest.mark.parametrize("source", ("", "x=x"))
def test_statements_must_be_nonempty_and_closed(actual_rows, source):
    with pytest.raises(notation.NotationError):
        notation.audit_rows((replace(actual_rows[0], statement=source),))


def test_source_audit_does_not_call_a_proof_factory_or_load_alpha(actual_rows, monkeypatch):
    before = _editions()
    records = notation.previous_graph.reviewed_registry()
    for module in (notation.previous.representation, notation.previous.division):
        def reject(*args, **kwargs):
            pytest.fail("notation attempted to invoke an old theorem factory")
        factory = "make_" + module.__name__ + "_theorems"
        monkeypatch.setattr(module, factory, reject)
    result = notation.audit_rows(actual_rows)
    assert result["proof_acceptance_performed"] is False and _editions() == before
    assert notation.previous_graph.reviewed_registry() == records
    notation._check_prior()
