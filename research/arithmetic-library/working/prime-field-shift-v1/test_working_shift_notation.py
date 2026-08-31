"""Independent conservative-notation checks, never proof acceptance fixtures."""

from collections import Counter
from dataclasses import fields, is_dataclass, replace
from hashlib import sha256
from pathlib import Path
import re
import sys

import pytest

import working_shift_notation as notation
from constructive_formula_compactor import _FormulaCompactor, _LocalDefinedParser
from constructive_polynomial_euclidean_definition_graph import reviewed_registry as previous_registry
from peano_lab.kernel.formulas import parse_formula_in_context
from peano_lab.kernel.terms import ParseError
from peano_lab.library.formula_dag import FormulaArena


CONTRACTS = {
    "prime_field_polynomial_shift_exists":
        "forall b c L. exists d e. PolynomialShift(b,c,L,d,e)",
    "prime_field_polynomial_shift_power_zero":
        "forall b c L d e. PolynomialShift(b,c,L,d,e) -> PolynomialPowerCoefficient(d,e,S L,0,0)",
    "prime_field_polynomial_shift_power_successor":
        "forall b c L d e k a. PolynomialShift(b,c,L,d,e) -> "
        "PolynomialPowerCoefficient(b,c,L,k,a) -> PolynomialPowerCoefficient(d,e,S L,S k,a)",
}


def _authority_modules():
    return {name: module for name, module in sys.modules.items()
            if name.startswith(("peano_lab.library.editions", "check_alpha_", "build_peano_library_channels"))}


@pytest.fixture(autouse=True)
def unchanged_authority_and_frozen_source():
    before = _authority_modules()
    notation._check_sources()
    yield
    assert _authority_modules() == before
    notation._check_sources()


@pytest.fixture(scope="module")
def rows():
    return notation.source_rows()


@pytest.fixture(scope="module")
def audit(rows):
    return notation.audit_rows(rows)


def _same_ast(left, right):
    pending, seen = [(left, right)], set()
    while pending:
        a, b = pending.pop()
        assert type(a) is type(b)
        if (id(a), id(b)) in seen:
            continue
        seen.add((id(a), id(b)))
        if is_dataclass(a):
            pending.extend((getattr(a, field.name), getattr(b, field.name)) for field in fields(a))
        else:
            assert a == b


def _parse(source, context=(), registry=notation.DEFINITIONS):
    parser = _LocalDefinedParser(source, registry)
    parser.free = list(context)
    result = parser.parse()
    assert tuple(parser.free) == tuple(context)
    return result


def _call(arguments):
    return "PolynomialShift(" + ",".join(arguments) + ")"


def _independent(arguments):
    b, c, length, d, e = arguments
    return f"(BetaPrefixEqual({b},{c},{d},{e},{length})) /\\ (BetaAt({d},{e},{length},0))"


def test_preserves397_literal_identities_and_adds_two_actual_expansion_arrows():
    prior, _, _ = previous_registry()
    current, order, layers = notation.reviewed_registry()
    assert len(current) == len(notation.DEFINITIONS) == 398
    assert len({item.stable_id for item in notation.DEFINITIONS.values()}) == 398
    assert all(notation.DEFINITIONS[name] is item for name, item in notation.previous.items())
    assert all(current[name] == record for name, record in prior.items())
    assert sum(len(row["dependencies"]) for row in current.values()) == 867
    assert notation.SHIFT.stable_id == "ND0341"
    assert notation.SHIFT.parameters == ("b", "c", "L", "d", "e")
    assert notation.SHIFT.conceptual_dependencies == ("BetaPrefixEqual", "BetaAt")
    seen = set()
    for name in order:
        assert set(current[name]["dependencies"]) <= seen
        assert layers[name] == max((layers[parent] + 1 for parent in current[name]["dependencies"]), default=0)
        seen.add(name)
    with pytest.raises(TypeError):
        notation.DEFINITIONS["Unreviewed"] = notation.SHIFT


def test_shift_is_not_an_alias_of_existing_padding_or_other_five_parameter_graph():
    identity = FormulaArena().freeze(notation.SHIFT.template_formula).to_json()
    for item in notation.previous.values():
        if item.arity == notation.SHIFT.arity:
            assert identity != FormulaArena().freeze(item.template_formula).to_json(), item.name


@pytest.mark.parametrize("kind", ("parameters", "compound", "large", "zero", "repeated", "reversed"))
def test_independent_lower_vocabulary_and_binder_safe_actual_expansion(kind):
    choices = {"parameters": notation.PARAMETERS, "compound": ("S (x+y)", "x*y", "x+y"),
               "large": (str(2**96 + 17), "x+y", "y"), "zero": ("0",),
               "repeated": ("x+y",), "reversed": ("y", "x")}[kind]
    arguments = tuple(choices[index % len(choices)] for index in range(5))
    context = ("unused_outer", *notation.PARAMETERS, "x", "unused_middle", "y", "unused_last")
    public = notation._candidate.prime_field_polynomial_shift_relation(
        *arguments, tag="independent_notation", variables=context)
    expected = parse_formula_in_context(public, list(context))
    lower = dict(notation.DEFINITIONS)
    lower.pop("PolynomialShift")
    _same_ast(expected, _parse(_independent(arguments), context, lower))
    _same_ast(expected, _parse(_call(arguments), context))
    outer = "forall " + " ".join(context) + ". "
    _same_ast(parse_formula_in_context(outer + "(" + public + ")", []), _parse(outer + _call(arguments)))


def test_public_generator_rejects_capture_and_named_expansion_is_hygienic():
    builder = notation._candidate.prime_field_polynomial_shift_relation
    source = builder(*notation.PARAMETERS, tag="capture_audit", variables=notation.PARAMETERS)
    binders = sorted({name for group in re.findall(r"\b(?:forall|exists)\s+([^.]*)\.", source)
                      for name in group.split()})
    assert binders and not set(binders) & set(notation.PARAMETERS)
    for binder in dict.fromkeys((binders[0], binders[len(binders)//2], binders[-1])):
        with pytest.raises(ValueError, match="captures"):
            builder(*notation.PARAMETERS, tag="capture_audit", variables=(*notation.PARAMETERS, binder))
        context = ("unused", binder, "other_unused")
        _same_ast(_parse(_call((binder,) * 5), context), _parse(_independent((binder,) * 5), context))


@pytest.mark.parametrize("name", ("Prime", "BetaPrefixInto", "PolynomialEquivalent", "FpPolyProduct"))
def test_shift_does_not_assume_canonical_bounds_primality_or_covariance(name):
    item = notation.DEFINITIONS[name]
    reading = _FormulaCompactor((item,)).compact(notation.SHIFT.template_source)
    assert item.stable_id not in reading["statement_definition_uses"]
    assert name not in notation.SHIFT.conceptual_dependencies


@pytest.mark.parametrize("delta", (-1, 1))
def test_named_arity_is_exact(delta):
    with pytest.raises(ParseError, match="expects"):
        _parse(_call(("x",) * (5 + delta)), ("x",))


@pytest.mark.parametrize("index", range(15))
def test_every_actual_statement_and_local_formula_roundtrips_without_authority(rows, audit, index):
    row, node = rows[index], audit["nodes"][index]
    reading = node["defined"]
    assert node["name"] == row.name and node["statement"] == row.statement
    assert node["script"] == list(row.script) and node["dependencies"] == list(row.dependencies)
    assert reading["exact_ast_equivalence"] is True and reading["free_names"] == []
    _same_ast(_parse(reading["defined_statement"]), parse_formula_in_context(row.statement, []))
    assert reading["expanded_statement_sha256"] == sha256(row.statement.encode()).hexdigest()
    assert reading["defined_statement_sha256"] == sha256(reading["defined_statement"].encode()).hexdigest()
    counts = Counter(part["definition"] for part in reading["statement_parts"] if part["kind"] == "definition")
    assert counts == reading["statement_definition_uses"]
    script_uses = Counter()
    for original, rendered, parts in zip(row.script, reading["defined_script"], reading["script_parts"], strict=True):
        assert rendered == "".join(part["text"] for part in parts)
        script_uses.update(part["definition"] for part in parts if part["kind"] == "definition")
        if rendered != original:
            tactic, _, tail = original.partition(" ")
            assert tactic in {"have", "suffices"}
            proposition = tail.partition(":")[2].strip()
            rendered_proposition = rendered.partition(":")[2].strip()
            parser = _LocalDefinedParser(rendered_proposition, notation.DEFINITIONS)
            expanded = parser.parse()
            _same_ast(expanded, parse_formula_in_context(proposition, parser.free))
    assert dict(sorted(script_uses.items())) == reading["script_definition_uses"]
    assert counts + script_uses == reading["definition_uses"]
    assert node["authority"] == "source-syntax-only" and node["proof_acceptance_performed"] is False


@pytest.mark.parametrize("name", tuple(CONTRACTS))
@pytest.mark.parametrize("outer", ("", "forall x. ", "forall b. exists L. "))
def test_independent_readable_contracts_match_actual_statements(rows, name, outer):
    row = next(row for row in rows if row.name == name)
    _same_ast(_parse(outer + "(" + CONTRACTS[name] + ")"),
              parse_formula_in_context(outer + "(" + row.statement + ")", []))


def test_three_edge_kinds_have_separate_meanings_and_literal_counts(rows, audit):
    assert len(rows) == 15 and sum(len(row.script) for row in rows) == 1033
    proof = [edge for edge in audit["edges"] if edge["kind"] == "proof_dependency"]
    assert proof == [{"kind": "proof_dependency", "source": name, "target": row.name}
                     for row in rows for name in row.dependencies]
    usage = [edge for edge in audit["edges"] if edge["kind"] == "uses_definition"]
    assert usage == [{"kind": "uses_definition", "source": node["id"], "target": name, "occurrence_count": count}
                     for node in audit["nodes"] for name, count in node["defined"]["definition_uses"].items()]
    expansions = [edge for edge in audit["edges"] if edge["kind"] == "definition_uses_definition"]
    assert expansions == [{"kind": "definition_uses_definition", "source": row["id"], "target": name}
                          for row in audit["definitions"] for name in row["dependencies"]]
    assert (len(proof), len(usage), len(expansions), len(audit["definitions"])) == (46, 47, 31, 20)
    assert (audit["proof_dependency_count"], audit["definition_use_count"], audit["definition_expansion_count"]) == (46, 47, 31)
    definitions = {row["id"] for row in audit["definitions"]}
    assert "ND0341" in definitions
    assert all(edge["target"] in definitions for edge in usage)
    assert all(edge["source"] in definitions and edge["target"] in definitions for edge in expansions)
    assert set(edge["kind"] for edge in audit["edges"]) == {
        "proof_dependency", "uses_definition", "definition_uses_definition"}


def test_proof_paths_follow_only_supplied_theorem_edges_and_do_not_claim_external_cones(rows, audit):
    names = {row.name for row in rows}
    assert audit["path_policy"] == "proof_dependency_edges_only"
    assert audit["external_dependencies_resolved"] is False
    assert audit["external_dependencies"] == sorted({name for row in rows for name in row.dependencies if name not in names})
    for row in rows:
        path = audit["proof_paths"][row.name]
        assert path[-1] == row.name and set(path) <= names
        for source, target in zip(path, path[1:]):
            assert source in next(item for item in rows if item.name == target).dependencies
    assert all(audit[name] is False for name in ("proof_acceptance_performed", "admission_performed", "publication_performed"))
    assert audit["registry_definition_count"] == 398 and audit["new_definition_count"] == 1


@pytest.mark.parametrize("bad", (None, [], (), "rows", (object(),)))
def test_non_specification_inputs_are_rejected(bad):
    with pytest.raises(notation.NotationError, match="tuple of theorem"):
        notation.audit_rows(bad)


@pytest.mark.parametrize("bad_name", ("", "bad name", "bad/name", None, [], "ND0341", "PolynomialShift"))
def test_names_cannot_be_invalid_or_shadow_notation(rows, bad_name):
    with pytest.raises(notation.NotationError, match="names"):
        notation.audit_rows((replace(rows[0], name=bad_name),))


@pytest.mark.parametrize("attack", ("duplicate", "self", "forward", "repeated", "definition_id", "definition_name", "invalid"))
def test_proof_topology_rejects_cycles_and_notation_as_a_proof_dependency(rows, attack):
    first, second = rows[:2]
    data = {
        "duplicate": (first, first), "self": (replace(first, dependencies=(first.name,)),),
        "forward": (replace(first, dependencies=(second.name,)), second),
        "repeated": (replace(first, dependencies=("le_total", "le_total")),),
        "definition_id": (replace(first, dependencies=("ND0341",)),),
        "definition_name": (replace(first, dependencies=("PolynomialShift",)),),
        "invalid": (replace(first, dependencies=(None,)),),
    }[attack]
    with pytest.raises(notation.NotationError):
        notation.audit_rows(data)


@pytest.mark.parametrize("bad", (None, True, "PolynomialShift", ["PolynomialShift"], ("",), (True,)))
def test_definition_closure_rejects_nonexact_inputs(bad):
    with pytest.raises(notation.NotationError, match="exact tuple"):
        notation.definition_closure(bad)


def test_definition_closure_is_topological_and_rejects_missing_graphs():
    ordered = notation.definition_closure(("PolynomialShift",))
    seen = set()
    for row in ordered:
        assert set(row.conceptual_dependencies) <= seen
        seen.add(row.name)
    assert ordered[-1] is notation.SHIFT
    with pytest.raises(notation.NotationError, match="unknown or cyclic"):
        notation.definition_closure(("Absent",))


@pytest.mark.parametrize("source", ("", "x=x"))
def test_statements_must_be_closed_nonempty_core_formulas(rows, source):
    with pytest.raises(notation.NotationError):
        notation.audit_rows((replace(rows[0], statement=source),))


def test_a_closed_false_formula_can_be_displayed_but_never_marked_proved(rows):
    result = notation.audit_rows((replace(rows[0], statement="0=S 0", script=("exact missing",)),))
    assert result["authority"] == "source-syntax-only"
    assert result["nodes"][0]["statement"] == "0=S 0"
    assert result["nodes"][0]["proof_acceptance_performed"] is False
    assert result["admission_performed"] is False and result["publication_performed"] is False


def test_source_pin_rejects_different_bytes_before_source_factories(monkeypatch, tmp_path):
    changed = tmp_path / "changed.py"
    changed.write_bytes(b"raise AssertionError('untrusted bytes must not run')\n")
    with monkeypatch.context() as scoped:
        scoped.setattr(notation, "SOURCE", changed)
        with pytest.raises(notation.NotationError, match="frozen working shift source"):
            notation.source_rows()


def test_import_and_audit_are_not_alpha_or_proof_services(rows, monkeypatch):
    before = _authority_modules()
    def reject(*args, **kwargs):
        pytest.fail("display attempted to reconstruct theorem source")
    monkeypatch.setattr(notation._candidate, "make_prime_field_polynomial_shift_candidate_theorems", reject)
    result = notation.audit_rows(rows)
    assert result["proof_acceptance_performed"] is False
    assert _authority_modules() == before
