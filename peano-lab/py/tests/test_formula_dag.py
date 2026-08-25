"""Conservative hash-consed formulas and hygienic shared definition expansion."""

from __future__ import annotations

from dataclasses import replace
import json

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import And, Eq, Forall, parse_formula
from peano_lab.kernel.proofs import AndIntro, EqRefl, ForallIntro
from peano_lab.kernel.terms import Add, ParseError, Var, Zero
from peano_lab.library.defined_syntax import parse_defined_formula
from peano_lab.library.formula_dag import (
    FORMULA_DAG_FORMAT,
    FormulaArena,
    FormulaDag,
    FormulaDagError,
    FormulaDagNode,
    compile_shared_defined_formula,
    parse_shared_defined_formula,
    parse_shared_defined_formula_with_names,
)


def test_structurally_equal_terms_and_formulas_are_one_actual_object() -> None:
    arena = FormulaArena()
    first = Eq(Add(Var(0), Zero()), Add(Var(0), Zero()))
    second = Eq(Add(Var(0), Zero()), Add(Var(0), Zero()))

    shared_first = arena.intern_formula(first)
    shared_second = arena.intern_formula(second)

    assert shared_first is shared_second
    assert type(shared_first) is Eq
    assert shared_first.left is shared_first.right
    dag = arena.freeze(Forall(And(shared_first, shared_second)))
    metrics = dag.metrics()
    assert metrics.unique_nodes < metrics.structural_occurrences
    assert metrics.reused_edges > 0


def test_exact_kernel_judgment_is_unchanged_by_formula_sharing() -> None:
    proposition = Forall(
        And(Eq(Var(0), Var(0)), Eq(Var(0), Var(0)))
    )
    proof = ForallIntro(AndIntro(EqRefl(Var(0)), EqRefl(Var(0))))
    shared = FormulaArena().intern_formula(proposition)

    assert shared == proposition
    assert check((), proof, proposition)
    assert check((), proof, shared)
    assert type(shared) is Forall
    assert type(shared.body) is And
    assert shared.body.left is shared.body.right


def test_formula_dag_round_trip_is_canonical_inert_data() -> None:
    formula = parse_formula("forall x. (x + 0 = x) /\\ (x + 0 = x)")
    dag = FormulaArena().freeze(formula)
    payload = dag.to_json()

    restored = FormulaDag.from_json(payload)

    assert restored == dag
    assert restored.expand() == formula
    assert restored.to_json() == payload
    assert json.loads(payload)[0] == FORMULA_DAG_FORMAT
    assert payload.endswith("\n")
    with pytest.raises(FormulaDagError, match="not canonical"):
        FormulaDag.from_json(json.dumps(json.loads(payload)) + "\n")


@pytest.mark.parametrize(
    "record",
    (
        ["peano-lab-formula-dag-v1", 0, [["zero"]]],
        ["peano-lab-formula-dag-v1", 1, [["zero"], ["eq", 0, 2]]],
        ["peano-lab-formula-dag-v1", 2, [["zero"], ["zero"], ["eq", 0, 1]]],
        ["peano-lab-formula-dag-v1", 1, [["var", True], ["eq", 0, 0]]],
        ["peano-lab-formula-dag-v1", 1, [["zero"], ["forall", 0]]],
        ["peano-lab-formula-dag-v1", 2, [["zero"], ["bot"], ["eq", 0, 0]]],
    ),
)
def test_malformed_forward_duplicate_wrong_sort_and_unreachable_nodes_fail_closed(
    record: object,
) -> None:
    with pytest.raises(FormulaDagError):
        FormulaDag.from_record(record)


def test_nonexact_or_adversarial_kernel_constructors_are_rejected() -> None:
    class EvilEq(Eq):
        pass

    with pytest.raises(FormulaDagError, match="exact"):
        FormulaArena().intern_formula(EvilEq(Zero(), Zero()))
    with pytest.raises(FormulaDagError, match="nonnegative"):
        FormulaArena().intern_term(Var(True))  # type: ignore[arg-type]


def test_unique_node_and_depth_limits_are_fail_closed() -> None:
    formula = parse_formula("forall x. x + S x = x")
    with pytest.raises(FormulaDagError, match="unique-node"):
        FormulaArena(max_unique_nodes=2).freeze(formula)
    with pytest.raises(FormulaDagError, match="nesting-depth"):
        FormulaArena(max_depth=2).freeze(formula)


def test_repeated_definitions_share_the_exact_hygienic_expansion() -> None:
    source = "forall x. Prime(x) /\\ Prime(x)"
    baseline = parse_defined_formula(source)

    result = compile_shared_defined_formula(source)

    assert result.formula == baseline
    assert result.free_names == ()
    assert result.definition_calls == 2
    assert result.definition_cache_hits == 1
    assert result.dag.expand() == baseline
    assert type(result.formula) is Forall
    assert type(result.formula.body) is And
    assert result.formula.body.left is result.formula.body.right
    assert result.dag.metrics().structural_occurrences > result.dag.metrics().unique_nodes


def test_compound_arguments_remain_capture_free_under_distinct_binders() -> None:
    source = "forall x. (exists y. Dvd(x + y, x)) /\\ (exists y. Dvd(x + y, x))"
    result = compile_shared_defined_formula(source)

    assert result.formula == parse_defined_formula(source)
    assert result.definition_calls == 2
    assert result.definition_cache_hits == 1
    assert result.dag.expand() == parse_defined_formula(source)


def test_same_surface_name_under_different_de_bruijn_arguments_is_not_reused() -> None:
    source = "forall x. Prime(x) /\\ exists y. Prime(x)"
    result = compile_shared_defined_formula(source)

    assert result.formula == parse_defined_formula(source)
    assert result.definition_calls == 2
    assert result.definition_cache_hits == 0


def test_compatible_free_name_and_plain_formula_interfaces() -> None:
    source = "Dvd(a,b) /\\ Dvd(a,b)"
    formula, names = parse_shared_defined_formula_with_names(source)

    assert names == ("a", "b")
    assert formula == parse_defined_formula(source)
    assert parse_shared_defined_formula("forall x. x=x") == parse_formula(
        "forall x. x=x"
    )


def test_definition_arity_names_and_budgets_fail_closed() -> None:
    with pytest.raises(ParseError, match="unknown defined predicate"):
        compile_shared_defined_formula("Unknown(0)")
    with pytest.raises(ParseError, match="expects"):
        compile_shared_defined_formula("Dvd(0)")
    with pytest.raises(ParseError, match="budget"):
        compile_shared_defined_formula("Prime(0)", expansion_budget=2)
    with pytest.raises(FormulaDagError, match="structural"):
        compile_shared_defined_formula(
            "forall x. Prime(x) /\\ Prime(x)",
            max_structural_occurrences=5,
        )


def test_canonical_decoder_rejects_duplicate_structural_nodes_after_mutation() -> None:
    dag = FormulaArena().freeze(parse_formula("0=0"))
    assert dag.nodes[0] == FormulaDagNode("zero")
    malformed = replace(dag, nodes=(dag.nodes[0], dag.nodes[0], dag.nodes[-1]), root=2)
    with pytest.raises(FormulaDagError, match="duplicate"):
        malformed.expand()
