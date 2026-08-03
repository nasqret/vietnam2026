"""Contracts for conservative, opt-in defined predicate syntax."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
import json
from pathlib import Path

import pytest

from peano_lab.library.euler_scaled_inverse_candidate import (
    scaled_fixed_point as campaign_scaled_fixed_point,
    scaled_inverse as campaign_scaled_inverse,
    unit_residue as campaign_unit_residue,
)
from peano_lab.library.euler_scaled_inverse_prefix_candidate import (
    scaled_inverse_index as campaign_scaled_inverse_index,
    scaled_inverse_prefix as campaign_scaled_inverse_prefix,
)
from peano_lab.library.finite_division_prefix_candidate import (
    division_prefix as campaign_division_prefix,
)
from peano_lab.library.finite_factorial_theorems import factorial_relation
from peano_lab.library.finite_fold_surface import (
    all_bits,
    beta_at,
    bit_count,
    power_relation,
    product_relation,
    range_relation,
    repeat_relation,
    sum_relation,
)
from peano_lab.library.finite_permutation_theorems import (
    bounded_prefix,
    contains_prefix,
    injective_prefix,
    permutation_prefix,
    surjective_prefix,
)
from peano_lab.library.qr_bounded_units import (
    balanced_inverse as campaign_balanced_inverse,
    bounded_nonzero_inverse as campaign_bounded_nonzero_inverse,
)
from peano_lab.library.quadratic_residue_surface import (
    bounded_quadratic_residue,
    quadratic_residue,
)
from peano_lab.library.wilson_inverse_point_candidate import (
    inverse_index as campaign_inverse_index,
    successor_inverse as campaign_successor_inverse,
)
from peano_lab.library.wilson_inverse_prefix_candidate import (
    inverse_prefix as campaign_inverse_prefix,
)
from peano_lab.kernel.formulas import (
    And,
    Bot,
    Eq,
    Exists,
    Forall,
    Imp,
    Or,
    parse_formula,
    parse_formula_in_context,
    pretty_formula,
)
from peano_lab.kernel.terms import Add, Mul, ParseError, Succ, Var, Zero
from peano_lab.library.defined_syntax import (
    ADJACENT_DEFINITIONS,
    ALL_DEFINITIONS,
    ALL_DEFINITIONS_BY_ID,
    ALL_DEFINITIONS_BY_NAME,
    DEFINITIONS,
    DEFINITIONS_BY_ID,
    DEFINITIONS_BY_NAME,
    DEFINED_SYNTAX_REGISTRY_ID,
    DEFINED_SYNTAX_REGISTRY_SHA256,
    DEFINED_SYNTAX_VERSION,
    DefinitionSpec,
    parse_defined_formula,
    parse_defined_formula_in_context,
    parse_defined_formula_with_names,
)


EXPECTED_PD_NAMES = (
    "Le",
    "Lt",
    "Dvd",
    "Prime",
    "Coprime",
    "IsGCD",
    "DivRem",
    "ModEq",
    "Even",
    "Odd",
    "Mod4One",
    "Mod4Three",
    "BetaAt",
    "Product",
    "Sum",
    "AllBits",
    "BitCount",
    "Range",
    "Repeat",
    "Pow",
    "QRes",
    "BoundedQRes",
    "Factorial",
    "BoundedPrefix",
    "InjectivePrefix",
    "SurjectivePrefix",
    "ContainsPrefix",
    "AllPrime",
    "Sorted",
    "UnitResidue",
    "BalancedInverse",
    "BoundedNonzeroInverse",
    "ScaledInverse",
    "ScaledFixedPoint",
    "SuccessorInverse",
    "InverseIndex",
    "InversePrefix",
    "ScaledInverseIndex",
    "ScaledInversePrefix",
    "DivisionPrefix",
)


SIMPLE_EXPANSIONS = (
    ("Le(a,b)", "exists h. h + a = b"),
    ("Lt(a,b)", "exists h. h + S a = b"),
    ("Dvd(d,n)", "exists q. n = d * q"),
    (
        "Prime(p)",
        "~(p = 1) /\\ forall a b. p = a * b -> a = 1 \\/ b = 1",
    ),
    (
        "Coprime(a,b)",
        "forall c. (exists u. a = c * u) -> "
        "(exists v. b = c * v) -> c = 1",
    ),
    (
        "IsGCD(g,a,b)",
        "((exists x. a = g * x) /\\ (exists y. b = g * y)) /\\ "
        "forall c. (exists u. a = c * u) -> "
        "(exists v. b = c * v) -> exists w. g = c * w",
    ),
    (
        "DivRem(n,d,q,r)",
        "n = d * q + r /\\ exists k. k + S r = d",
    ),
    ("ModEq(m,a,b)", "exists u v. a + m * u = b + m * v"),
    ("Even(n)", "exists h. n = 2 * h"),
    ("Odd(n)", "exists h. n = 2 * h + 1"),
    ("Mod4One(n)", "exists h. n = 4 * h + 1"),
    ("Mod4Three(n)", "exists h. n = 4 * h + 3"),
    (
        "BalancedBezout(d,a,b)",
        "exists xp yp xn yn. "
        "a * xp + b * yp = d + (a * xn + b * yn)",
    ),
)


HELPER_EXPANSIONS = (
    (
        "BetaAt(b,c,i,x)",
        beta_at("b", "c", "i", "x", tag="test_defined_beta_at"),
    ),
    (
        "Product(b,c,l,z)",
        product_relation("b", "c", "l", "z", tag="test_defined_product"),
    ),
    ("Sum(b,c,l,z)", sum_relation("b", "c", "l", "z", tag="test_defined_sum")),
    ("AllBits(b,c,l)", all_bits("b", "c", "l", tag="test_defined_bits")),
    (
        "BitCount(b,c,l,z)",
        bit_count("b", "c", "l", "z", tag="test_defined_bit_count"),
    ),
    (
        "Range(b,c,a,l)",
        range_relation("b", "c", "a", "l", tag="test_defined_range"),
    ),
    (
        "Repeat(b,c,a,l)",
        repeat_relation("b", "c", "a", "l", tag="test_defined_repeat"),
    ),
    ("Pow(a,e,z)", power_relation("a", "e", "z", tag="test_defined_pow")),
    (
        "QRes(m,a)",
        quadratic_residue("m", "a", tag="test_defined_qres"),
    ),
    (
        "BoundedQRes(m,a)",
        bounded_quadratic_residue("m", "a", tag="test_defined_bounded_qres"),
    ),
    ("Factorial(n,z)", factorial_relation("n", "z", tag="test_defined_factorial")),
    (
        "BoundedPrefix(b,c,l)",
        bounded_prefix("b", "c", "l", tag="test_defined_bounded_prefix"),
    ),
    (
        "InjectivePrefix(b,c,l)",
        injective_prefix("b", "c", "l", tag="test_defined_injective_prefix"),
    ),
    (
        "SurjectivePrefix(b,c,l)",
        surjective_prefix("b", "c", "l", tag="test_defined_surjective_prefix"),
    ),
    (
        "ContainsPrefix(b,c,l,x)",
        contains_prefix("b", "c", "l", "x", tag="test_defined_contains_prefix"),
    ),
    (
        "UnitResidue(m,a)",
        campaign_unit_residue("m", "a", tag="test_defined_unit_residue"),
    ),
    (
        "BalancedInverse(m,a,b)",
        campaign_balanced_inverse("m", "a", "b", tag="test_defined_inverse"),
    ),
    (
        "BoundedNonzeroInverse(m,a)",
        campaign_bounded_nonzero_inverse(
            "m", "a", tag="test_defined_bounded_inverse"
        ),
    ),
    (
        "ScaledInverse(m,t,a,b)",
        campaign_scaled_inverse(
            "m", "t", "a", "b", tag="test_defined_scaled_inverse"
        ),
    ),
    (
        "ScaledFixedPoint(m,t,a)",
        campaign_scaled_fixed_point(
            "m", "t", "a", tag="test_defined_scaled_fixed"
        ),
    ),
    (
        "SuccessorInverse(m,i,j)",
        campaign_successor_inverse(
            "m", "i", "j", tag="test_defined_successor_inverse"
        ),
    ),
    (
        "InverseIndex(m,l,i,j)",
        campaign_inverse_index(
            "m", "l", "i", "j", tag="test_defined_inverse_index"
        ),
    ),
    (
        "InversePrefix(m,l,b,c,k)",
        campaign_inverse_prefix(
            "m", "l", "b", "c", "k", tag="test_defined_inverse_prefix"
        ),
    ),
    (
        "ScaledInverseIndex(m,t,l,i,y)",
        campaign_scaled_inverse_index(
            "m", "t", "l", "i", "y", tag="test_defined_scaled_index"
        ),
    ),
    (
        "ScaledInversePrefix(m,t,l,b,c,k)",
        campaign_scaled_inverse_prefix(
            "m", "t", "l", "b", "c", "k", tag="test_defined_scaled_prefix"
        ),
    ),
    (
        "DivisionPrefix(m,b,c,qb,qc,rb,rc,l)",
        campaign_division_prefix(
            "m",
            "b",
            "c",
            "qb",
            "qc",
            "rb",
            "rc",
            "l",
            tag="test_defined_division_prefix",
        ),
    ),
    (
        "PermutationPrefix(b,c,l)",
        permutation_prefix("b", "c", "l", tag="test_defined_permutation"),
    ),
)


def _reject_duplicate_json_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _documented_definition_registry() -> dict[str, object]:
    repository = Path(__file__).resolve().parents[3]
    path = repository / "research/arithmetic-library/pa-proof-definitions.json"
    return json.loads(
        path.read_text(encoding="utf-8"),
        object_pairs_hook=_reject_duplicate_json_keys,
    )


def test_registry_is_ordered_immutable_versioned_and_self_describing() -> None:
    assert DEFINED_SYNTAX_REGISTRY_ID == "peano-lab.defined-predicates"
    assert DEFINED_SYNTAX_VERSION == 2
    assert len(DEFINED_SYNTAX_REGISTRY_SHA256) == 64
    assert tuple(definition.name for definition in DEFINITIONS) == EXPECTED_PD_NAMES
    assert tuple(definition.stable_id for definition in DEFINITIONS) == tuple(
        f"PD{index:04d}" for index in range(1, 41)
    )
    assert tuple(DEFINITIONS_BY_NAME) == tuple(
        definition.name for definition in DEFINITIONS
    )
    assert tuple(DEFINITIONS_BY_ID) == tuple(
        definition.stable_id for definition in DEFINITIONS
    )
    assert tuple(definition.name for definition in ADJACENT_DEFINITIONS) == (
        "PermutationPrefix",
        "BalancedBezout",
        "CanonicalPF",
    )
    assert ALL_DEFINITIONS == DEFINITIONS + ADJACENT_DEFINITIONS
    assert tuple(ALL_DEFINITIONS_BY_NAME) == tuple(
        definition.name for definition in ALL_DEFINITIONS
    )
    assert tuple(ALL_DEFINITIONS_BY_ID) == tuple(
        definition.stable_id for definition in ALL_DEFINITIONS
    )
    assert len({definition.stable_id for definition in ALL_DEFINITIONS}) == len(
        ALL_DEFINITIONS
    )
    for definition in ALL_DEFINITIONS:
        assert isinstance(definition, DefinitionSpec)
        assert definition.summary
        assert definition.category
        assert definition.priority in {"P0", "P1", "P2", "adjacent"}
        assert definition.template_formula == parse_formula_in_context(
            definition.template_source, list(definition.parameters)
        )
        assert set(definition.conceptual_dependencies) <= set(
            ALL_DEFINITIONS_BY_NAME
        )

    with pytest.raises(FrozenInstanceError):
        DEFINITIONS[0].name = "Other"  # type: ignore[misc]
    with pytest.raises(TypeError):
        DEFINITIONS_BY_NAME["Other"] = DEFINITIONS[0]  # type: ignore[index]
    with pytest.raises(TypeError):
        ALL_DEFINITIONS_BY_NAME["Other"] = DEFINITIONS[0]  # type: ignore[index]
    with pytest.raises(TypeError):
        DEFINITIONS_BY_ID["Other"] = DEFINITIONS[0]  # type: ignore[index]
    with pytest.raises(TypeError):
        ALL_DEFINITIONS_BY_ID["Other"] = DEFINITIONS[0]  # type: ignore[index]


def test_runtime_pd_metadata_matches_duplicate_key_checked_documentation() -> None:
    documented = _documented_definition_registry()
    records = documented["definitions"]
    assert isinstance(records, list)
    assert len(records) == 40
    assert [record["id"] for record in records] == [
        definition.stable_id for definition in DEFINITIONS
    ]

    by_name = {definition.name: definition for definition in DEFINITIONS}
    for definition, record in zip(DEFINITIONS, records, strict=True):
        assert isinstance(record, dict)
        assert record["name"] == definition.name
        assert record["arity"] == definition.arity
        assert record["category"] == definition.category
        assert record["priority"] == definition.priority
        dependencies = [
            by_name[name].stable_id for name in definition.conceptual_dependencies
        ]
        assert record["dependencies"] == dependencies
        counts = record["counts"]
        assert isinstance(counts, dict)
        assert counts["public_occurrences"] + counts["candidate_occurrences"] == (
            counts["occurrences"]
        )


@pytest.mark.parametrize(("surface", "expanded"), SIMPLE_EXPANSIONS)
def test_each_definition_is_exactly_its_reviewed_core_expansion(
    surface: str, expanded: str
) -> None:
    actual, names = parse_defined_formula_with_names(surface)
    expected = parse_formula_in_context(expanded, list(names))
    assert actual == expected


@pytest.mark.parametrize(
    "definition",
    ALL_DEFINITIONS,
    ids=lambda definition: definition.stable_id,
)
def test_every_registered_definition_instantiates_its_reviewed_template(
    definition: DefinitionSpec,
) -> None:
    surface = f"{definition.name}({','.join(definition.parameters)})"
    actual, names = parse_defined_formula_with_names(surface)
    assert names == definition.parameters
    assert actual == parse_formula_in_context(
        definition.template_source,
        list(definition.parameters),
    )


@pytest.mark.parametrize(("surface", "expanded"), HELPER_EXPANSIONS)
def test_runtime_templates_match_existing_authoring_helpers_up_to_alpha(
    surface: str,
    expanded: str,
) -> None:
    actual, names = parse_defined_formula_with_names(surface)
    assert actual == parse_formula_in_context(expanded, list(names))


@pytest.mark.parametrize(
    "definition",
    ALL_DEFINITIONS,
    ids=lambda definition: f"capture-{definition.name}",
)
def test_every_definition_accepts_compound_repeated_arguments_without_capture(
    definition: DefinitionSpec,
) -> None:
    argument = "S (z + 1)"
    source = (
        "forall z. "
        f"{definition.name}({','.join(argument for _ in definition.parameters)})"
    )
    formula, names = parse_defined_formula_with_names(source)
    assert names == ()
    assert formula == parse_defined_formula(source)


def test_compound_arguments_expand_simultaneously_without_capture() -> None:
    actual = parse_defined_formula(
        "forall q a. Dvd(q + a, S (q * a))"
    )
    expected = parse_formula(
        "forall q a. exists witness. S (q * a) = (q + a) * witness"
    )
    assert actual == expected

    repeated = parse_defined_formula("forall q. Dvd(q,q)")
    assert repeated == parse_formula("forall q. exists witness. q = q * witness")


def test_definitions_nest_under_all_formula_constructs() -> None:
    surface = (
        "forall n. Prime(n) -> "
        "(Dvd(2,n) \\/ (Lt(n,S n) /\\ ModEq(5,n,1)))"
    )
    expanded = (
        "forall n. "
        "(~(n = 1) /\\ forall a b. n = a * b -> a = 1 \\/ b = 1) -> "
        "((exists q. n = 2 * q) \\/ "
        "((exists k. k + S n = S n) /\\ "
        "exists u v. n + 5 * u = 1 + 5 * v))"
    )
    assert parse_defined_formula(surface) == parse_formula(expanded)


def test_with_names_preserves_surface_order_and_context_parser_is_exact() -> None:
    formula, names = parse_defined_formula_with_names("Dvd(d + n,n)")
    assert names == ("d", "n")
    rendered = pretty_formula(formula, list(names))
    assert parse_defined_formula_in_context(rendered, list(names)) == formula

    assert parse_defined_formula_in_context("Dvd(n,d)", ["d", "n"]) == (
        parse_formula_in_context("exists q. d = n * q", ["d", "n"])
    )
    with pytest.raises(ParseError, match="unknown term variable.*x"):
        parse_defined_formula_in_context("Dvd(d,x)", ["d", "n"])


def test_expansions_contain_only_the_original_kernel_ast_constructors() -> None:
    formula = parse_defined_formula(
        "forall n d q r. DivRem(n,d,q,r) -> Prime(d) -> Dvd(d,n)"
    )

    def visit_term(term: object) -> None:
        assert type(term) in {Var, Zero, Succ, Add, Mul}
        if isinstance(term, Succ):
            visit_term(term.term)
        elif isinstance(term, (Add, Mul)):
            visit_term(term.left)
            visit_term(term.right)

    def visit_formula(node: object) -> None:
        assert type(node) in {Eq, Bot, Imp, And, Or, Forall, Exists}
        if isinstance(node, Eq):
            visit_term(node.left)
            visit_term(node.right)
        elif isinstance(node, (Imp, And, Or)):
            visit_formula(node.left)
            visit_formula(node.right)
        elif isinstance(node, (Forall, Exists)):
            visit_formula(node.body)

    visit_formula(formula)


def test_core_parse_apis_do_not_enable_defined_predicates() -> None:
    with pytest.raises(ParseError):
        parse_formula("Dvd(a,b)")
    assert parse_formula("forall n. n = n") == parse_defined_formula(
        "forall n. n = n"
    )


@pytest.mark.parametrize(
    "source",
    (
        "Prime()",
        "Dvd(a)",
        "Dvd(a,b,c)",
        "DivRem(n,d,q)",
    ),
)
def test_arity_errors_are_final_and_position_bearing(source: str) -> None:
    with pytest.raises(ParseError, match=r"expects .* at column 1"):
        parse_defined_formula(source)


@pytest.mark.parametrize(
    "definition",
    ALL_DEFINITIONS,
    ids=lambda definition: f"arity-{definition.name}",
)
def test_every_registered_arity_is_enforced(definition: DefinitionSpec) -> None:
    too_few = ",".join(
        f"a{index}" for index in range(max(0, definition.arity - 1))
    )
    too_many = ",".join(f"a{index}" for index in range(definition.arity + 1))
    with pytest.raises(ParseError, match=rf"expects {definition.arity} .*column 1"):
        parse_defined_formula(f"{definition.name}({too_few})")
    with pytest.raises(ParseError, match=rf"expects {definition.arity} .*column 1"):
        parse_defined_formula(f"{definition.name}({too_many})")


@pytest.mark.parametrize(
    "source",
    (
        "dvd(a,b)",
        "Unknown(a)",
        "Dvd(a b)",
        "Dvd(a,)",
        "Dvd(a,b",
    ),
)
def test_call_syntax_errors_are_final_and_position_bearing(source: str) -> None:
    with pytest.raises(ParseError, match=r"column"):
        parse_defined_formula(source)


def test_expansion_budget_is_typed_bounded_and_accumulates() -> None:
    with pytest.raises(ParseError, match=r"1-node budget.*column 1"):
        parse_defined_formula("Dvd(a,b)", expansion_budget=1)
    parse_defined_formula("Dvd(a,b)", expansion_budget=100)

    for invalid in (0, -1, True, 1.5):
        with pytest.raises(ValueError, match="positive integer"):
            parse_defined_formula("Dvd(a,b)", expansion_budget=invalid)  # type: ignore[arg-type]


def test_context_validation_matches_the_core_parser_contract() -> None:
    for invalid in (("a",), ["a", "a"], [1]):
        with pytest.raises(ValueError, match="distinct surface identifiers"):
            parse_defined_formula_in_context(  # type: ignore[arg-type]
                "Dvd(a,a)", invalid
            )
