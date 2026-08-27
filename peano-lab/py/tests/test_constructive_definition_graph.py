"""Fail-closed audit of blueprint and independently checked definition DAGs."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import constructive_definition_graph as definitions  # noqa: E402
import constructive_second_wave_definition_graph as current_definitions  # noqa: E402
from constructive_second_wave_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL_CURRENT_DEFINITIONS_BY_NAME,
)
from constructive_advanced_layer_definitions import (  # noqa: E402
    ADVANCED_LAYER_DEFINITIONS,
    ADVANCED_LAYER_DEFINITIONS_BY_NAME,
    ADVANCED_LAYER_REGISTRIES,
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME,
)
from constructive_breakthrough_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL_BREAKTHROUGH_DEFINITIONS_BY_NAME,
    BREAKTHROUGH_LAYER_DEFINITIONS,
    BREAKTHROUGH_LAYER_DEFINITIONS_BY_NAME,
    BREAKTHROUGH_LAYER_REGISTRIES,
)
from constructive_next_layer_definitions import (  # noqa: E402
    NEXT_LAYER_DEFINITIONS,
    NEXT_LAYER_DEFINITIONS_BY_NAME,
    NEXT_LAYER_REGISTRIES,
)
from constructive_research_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL_RESEARCH_DEFINITIONS_BY_NAME,
    RESEARCH_LAYER_DEFINITIONS,
    RESEARCH_LAYER_DEFINITIONS_BY_NAME,
    RESEARCH_LAYER_REGISTRIES,
)
from constructive_milestone_closure_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL_MILESTONE_DEFINITIONS_BY_NAME,
    MILESTONE_CLOSURE_DEFINITIONS,
    MILESTONE_CLOSURE_DEFINITIONS_BY_NAME,
    MILESTONE_CLOSURE_REGISTRIES,
)
from constructive_transport_layer_definitions import (  # noqa: E402
    ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME as ALL_TRANSPORT_DEFINITIONS_BY_NAME,
    TRANSPORT_LAYER_DEFINITIONS,
    TRANSPORT_LAYER_DEFINITIONS_BY_NAME,
    TRANSPORT_LAYER_REGISTRIES,
)
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402


CAMPAIGN = ROOT / "book" / "_static" / "constructive-grand-campaign" / "campaign.json"
ARTIFACT = CAMPAIGN.with_name("definitions.json")


@pytest.fixture(scope="module")
def campaign() -> dict:
    return json.loads(CAMPAIGN.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def graph(campaign: dict) -> dict:
    return current_definitions.build_definition_graph(campaign)


def test_public_definition_artifact_is_exactly_reproducible(
    campaign: dict,
    graph: dict,
) -> None:
    expected_bytes = (json.dumps(graph, ensure_ascii=False, allow_nan=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    assert ARTIFACT.read_bytes() == expected_bytes
    assert json.loads(ARTIFACT.read_text(encoding="utf-8")) == graph
    canonical_campaign = json.dumps(
        campaign,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    assert graph["campaign_snapshot_sha256"] == sha256(canonical_campaign).hexdigest()


def test_blueprint_and_checked_definition_inventory_remain_separate(
    graph: dict,
    campaign: dict,
) -> None:
    assert graph["schema"] == "constructive-number-theory-definition-dag-v1"
    assert graph["definition_count"] == len(campaign["definitions"]) >= 107
    names = set(campaign["definitions"])
    expected_definition_edges = sum(
        len(set(re.findall(r"[A-Za-z][A-Za-z0-9_]*", definition["expansion"])) & names)
        for definition in campaign["definitions"].values()
    )
    expected_lexical_usage = sum(
        len(set(re.findall(r"[A-Za-z][A-Za-z0-9_]*", node["statement"])) & names)
        for node in campaign["nodes"]
    )
    expected_declared_usage = sum(
        len(node.get("definition_refs", []))
        for node in campaign["nodes"]
    )
    assert graph["definition_edge_count"] == expected_definition_edges >= 32
    assert graph["statement_usage_edge_count"] == expected_lexical_usage >= 300
    assert graph["declared_notation_edge_count"] == expected_declared_usage
    assert graph["milestone_usage_edge_count"] == (
        expected_lexical_usage + expected_declared_usage
    )
    assert graph["topological_layer_count"] >= 5
    assert graph["definition_count"] == 290
    assert graph["reviewed_definition_count"] == len(ALL_CURRENT_DEFINITIONS_BY_NAME) == 198
    assert graph["reviewed_definition_edge_count"] == sum(
        len(definition.conceptual_dependencies)
        for definition in ALL_CURRENT_DEFINITIONS_BY_NAME.values()
    )
    assert graph["reviewed_definition_edge_count"] == 388
    assert graph["compatible_reviewed_match_count"] == 201
    assert graph["exact_name_reviewed_match_count"] == 196
    assert graph["explicit_alias_reviewed_match_count"] == 5
    assert graph["incompatible_reviewed_match_count"] == 2
    assert "never theorem-proof dependencies" in graph["authority_policy"][
        "notation_edges"
    ]


def test_next_layer_registry_shares_exact_immutable_checked_definition_objects(
    graph: dict,
) -> None:
    reviewed = {row["name"]: row for row in graph["reviewed_definitions"]}
    assert len(NEXT_LAYER_DEFINITIONS) == 11
    assert list(NEXT_LAYER_DEFINITIONS_BY_NAME) == [
        definition.name for definition in NEXT_LAYER_DEFINITIONS
    ]
    flattened = [
        (route, definition)
        for route, items in NEXT_LAYER_REGISTRIES
        for definition in items
    ]
    assert [definition for _, definition in flattened] == list(NEXT_LAYER_DEFINITIONS)
    for route, definition in flattened:
        assert NEXT_LAYER_DEFINITIONS_BY_NAME[definition.name] is definition
        record = reviewed[definition.name]
        assert record["id"] == definition.stable_id
        assert record["route"] == route
        assert record["parameters"] == list(definition.parameters)
        assert record["dependencies"] == list(definition.conceptual_dependencies)
        assert record["expansion_sha256"] == sha256(
            definition.template_source.encode("utf-8")
        ).hexdigest()
        assert parse_formula_in_context(
            definition.template_source, list(definition.parameters)
        ) == definition.template_formula


def test_advanced_layer_registry_reuses_old_objects_and_adds_exact_stable_definitions(
    graph: dict,
) -> None:
    reviewed = {row["name"]: row for row in graph["reviewed_definitions"]}
    assert len(ADVANCED_LAYER_DEFINITIONS) == 16
    assert len(ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME) == 79
    assert tuple(definition.stable_id for definition in ADVANCED_LAYER_DEFINITIONS) == tuple(
        f"ND{index:04d}" for index in range(12, 28)
    )
    assert [route for route, _ in ADVANCED_LAYER_REGISTRIES] == [
        "matrix-coded-products",
        "euclidean-complexity",
        "binary-modular-exponentiation",
    ]
    assert [len(items) for _, items in ADVANCED_LAYER_REGISTRIES] == [6, 3, 7]
    flattened = tuple(
        definition
        for _, group in ADVANCED_LAYER_REGISTRIES
        for definition in group
    )
    assert flattened == ADVANCED_LAYER_DEFINITIONS
    for definition in NEXT_LAYER_DEFINITIONS:
        assert ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[definition.name] is definition
    for route, group in ADVANCED_LAYER_REGISTRIES:
        for definition in group:
            assert ADVANCED_LAYER_DEFINITIONS_BY_NAME[definition.name] is definition
            assert ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME[definition.name] is definition
            row = reviewed[definition.name]
            assert row["id"] == definition.stable_id
            assert row["route"] == route
            assert row["parameters"] == list(definition.parameters)
            assert row["dependencies"] == list(definition.conceptual_dependencies)
            assert row["expansion_sha256"] == sha256(
                definition.template_source.encode("utf-8")
            ).hexdigest()
            assert parse_formula_in_context(
                definition.template_source, list(definition.parameters)
            ) == definition.template_formula


def test_transport_layer_registry_reuses_old_objects_and_adds_exact_stable_definitions(
    graph: dict,
) -> None:
    reviewed = {row["name"]: row for row in graph["reviewed_definitions"]}
    assert len(TRANSPORT_LAYER_DEFINITIONS) == 10
    assert len(ALL_TRANSPORT_DEFINITIONS_BY_NAME) == 89
    assert tuple(definition.stable_id for definition in TRANSPORT_LAYER_DEFINITIONS) == tuple(
        f"ND{index:04d}" for index in range(28, 38)
    )
    assert [route for route, _ in TRANSPORT_LAYER_REGISTRIES] == [
        "binary-length",
        "euclidean-gcd-transport",
        "binary-modular-execution",
    ]
    assert [len(items) for _, items in TRANSPORT_LAYER_REGISTRIES] == [3, 3, 4]
    flattened = tuple(
        definition
        for _, group in TRANSPORT_LAYER_REGISTRIES
        for definition in group
    )
    assert flattened == TRANSPORT_LAYER_DEFINITIONS
    for name, definition in ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME.items():
        assert ALL_TRANSPORT_DEFINITIONS_BY_NAME[name] is definition
    for route, group in TRANSPORT_LAYER_REGISTRIES:
        for definition in group:
            assert TRANSPORT_LAYER_DEFINITIONS_BY_NAME[definition.name] is definition
            assert ALL_TRANSPORT_DEFINITIONS_BY_NAME[definition.name] is definition
            row = reviewed[definition.name]
            assert row["id"] == definition.stable_id
            assert row["route"] == route
            assert row["parameters"] == list(definition.parameters)
            assert row["dependencies"] == list(definition.conceptual_dependencies)
            assert row["expansion_sha256"] == sha256(
                definition.template_source.encode("utf-8")
            ).hexdigest()
            assert parse_formula_in_context(
                definition.template_source, list(definition.parameters)
            ) == definition.template_formula


def test_milestone_registry_preserves_every_historical_identity_and_exact_mod4_ast(
    graph: dict,
) -> None:
    reviewed = {row["name"]: row for row in graph["reviewed_definitions"]}
    assert len(MILESTONE_CLOSURE_DEFINITIONS) == 8
    assert len(ALL_MILESTONE_DEFINITIONS_BY_NAME) == 97
    assert tuple(item.stable_id for item in MILESTONE_CLOSURE_DEFINITIONS) == tuple(
        f"ND{index:04d}" for index in range(38, 46)
    )
    assert [route for route, _ in MILESTONE_CLOSURE_REGISTRIES] == [
        "euclidean-logarithmic-bound",
        "binary-digit-extraction",
        "primes-three-mod-four",
    ]
    assert [len(items) for _, items in MILESTONE_CLOSURE_REGISTRIES] == [2, 4, 2]
    for name, item in ALL_TRANSPORT_DEFINITIONS_BY_NAME.items():
        assert ALL_MILESTONE_DEFINITIONS_BY_NAME[name] is item
    assert reviewed["Mod4Three"]["id"] == "PD0012"
    assert reviewed["AllBits"]["id"] == "PD0016"
    assert reviewed["BitCount"]["id"] == "PD0017"
    assert sum(item.name == "Mod4Three" for item in ALL_MILESTONE_DEFINITIONS_BY_NAME.values()) == 1
    for route, group in MILESTONE_CLOSURE_REGISTRIES:
        for item in group:
            assert MILESTONE_CLOSURE_DEFINITIONS_BY_NAME[item.name] is item
            assert ALL_MILESTONE_DEFINITIONS_BY_NAME[item.name] is item
            row = reviewed[item.name]
            assert row["id"] == item.stable_id
            assert row["route"] == route
            assert row["parameters"] == list(item.parameters)
            assert row["dependencies"] == list(item.conceptual_dependencies)
            assert row["expansion_sha256"] == sha256(item.template_source.encode()).hexdigest()
            assert parse_formula_in_context(item.template_source, list(item.parameters)) == (
                item.template_formula
            )


def test_research_layer_preserves_all_historical_identities_and_adds_exact_hygienic_dag(
    graph: dict,
) -> None:
    reviewed = {row["name"]: row for row in graph["reviewed_definitions"]}
    assert len(RESEARCH_LAYER_DEFINITIONS) == 12
    assert len(ALL_RESEARCH_DEFINITIONS_BY_NAME) == 109
    assert tuple(item.stable_id for item in RESEARCH_LAYER_DEFINITIONS) == tuple(
        f"ND{index:04d}" for index in range(46, 58)
    )
    assert [route for route, _ in RESEARCH_LAYER_REGISTRIES] == [
        "matrix-determinant-minors", "polynomial-hensel", "generalized-crt-fold"
    ]
    assert [len(items) for _, items in RESEARCH_LAYER_REGISTRIES] == [4, 3, 5]
    for name, item in ALL_MILESTONE_DEFINITIONS_BY_NAME.items():
        assert ALL_RESEARCH_DEFINITIONS_BY_NAME[name] is item
    for route, group in RESEARCH_LAYER_REGISTRIES:
        for item in group:
            assert RESEARCH_LAYER_DEFINITIONS_BY_NAME[item.name] is item
            assert ALL_RESEARCH_DEFINITIONS_BY_NAME[item.name] is item
            row = reviewed[item.name]
            assert row["id"] == item.stable_id
            assert row["route"] == route
            assert row["parameters"] == list(item.parameters)
            assert row["dependencies"] == list(item.conceptual_dependencies)
            assert row["expansion_sha256"] == sha256(item.template_source.encode()).hexdigest()
            assert parse_formula_in_context(item.template_source, list(item.parameters)) == (
                item.template_formula
            )


def test_breakthrough_registry_is_additive_hygienic_and_identity_preserving(
    graph: dict,
) -> None:
    reviewed = {row["name"]: row for row in graph["reviewed_definitions"]}
    assert len(BREAKTHROUGH_LAYER_DEFINITIONS) == 11
    assert len(ALL_BREAKTHROUGH_DEFINITIONS_BY_NAME) == 120
    assert tuple(item.stable_id for item in BREAKTHROUGH_LAYER_DEFINITIONS) == tuple(
        f"ND{index:04d}" for index in range(58, 69)
    )
    assert [route for route, _ in BREAKTHROUGH_LAYER_REGISTRIES] == [
        "matrix-cofactor-expansion",
        "polynomial-taylor-hensel",
        "generalized-crt-compatibility",
    ]
    assert [len(group) for _, group in BREAKTHROUGH_LAYER_REGISTRIES] == [7, 2, 2]
    for name, item in ALL_RESEARCH_DEFINITIONS_BY_NAME.items():
        assert ALL_BREAKTHROUGH_DEFINITIONS_BY_NAME[name] is item
    for route, group in BREAKTHROUGH_LAYER_REGISTRIES:
        for item in group:
            assert BREAKTHROUGH_LAYER_DEFINITIONS_BY_NAME[item.name] is item
            assert ALL_BREAKTHROUGH_DEFINITIONS_BY_NAME[item.name] is item
            row = reviewed[item.name]
            assert row["id"] == item.stable_id
            assert row["route"] == route
            assert row["parameters"] == list(item.parameters)
            assert row["dependencies"] == list(item.conceptual_dependencies)
            assert row["expansion_sha256"] == sha256(item.template_source.encode()).hexdigest()
            assert parse_formula_in_context(item.template_source, list(item.parameters)) == (
                item.template_formula
            )


@pytest.mark.parametrize(
    ("name", "identifier", "route", "arity", "dependencies"),
    (
        ("MatrixMinorFourCode", "ND0058", "matrix-cofactor-expansion", 5, ()),
        ("SignedMinorRecord", "ND0059", "matrix-cofactor-expansion", 7, ("MatrixMinorFourCode", "SignedMatrixMinor")),
        ("SignedCofactorMinorPrefix", "ND0060", "matrix-cofactor-expansion", 8, ("Beta", "Lt", "SignedMinorRecord")),
        ("SignedAlternatingCofactorTerm", "ND0061", "matrix-cofactor-expansion", 7, ("Even", "Odd")),
        ("SignedAlternatingProductPrefix", "ND0062", "matrix-cofactor-expansion", 13, ("Beta", "Lt", "SignedAlternatingCofactorTerm")),
        ("SignedAlternatingCofactorFold", "ND0063", "matrix-cofactor-expansion", 11, ("SignedAlternatingProductPrefix", "Sum")),
        ("SignedFirstRowCofactorFold", "ND0064", "matrix-cofactor-expansion", 11, ("MatrixAffineSlice", "SignedAlternatingCofactorFold")),
        ("HornerTaylorRemainder", "ND0065", "polynomial-taylor-hensel", 9, ("HornerDerivative", "Horner")),
        ("HenselCorrection", "ND0066", "polynomial-taylor-hensel", 4, ("Lt", "ModEq")),
        ("CRTPairwiseCompatiblePrefix", "ND0067", "generalized-crt-compatibility", 5, ("Beta", "Lt", "IsGCD", "ModEq")),
        ("CRTMergeCompatiblePrefix", "ND0068", "generalized-crt-compatibility", 5, ("Lt", "Beta", "CRTPrefixLCM", "CRTPrefixSolution", "IsGCD", "ModEq")),
    ),
)
def test_all_breakthrough_blueprint_names_share_exact_reviewed_identities(
    graph: dict,
    name: str,
    identifier: str,
    route: str,
    arity: int,
    dependencies: tuple[str, ...],
) -> None:
    match = next(
        row for row in graph["compatible_reviewed_matches"]
        if row["blueprint_name"] == name
    )
    reviewed = next(row for row in graph["reviewed_definitions"] if row["name"] == name)
    blueprint = next(row for row in graph["definitions"] if row["name"] == name)
    assert match["reviewed_name"] == name
    assert match["reviewed_id"] == identifier
    assert match["route"] == route
    assert match["kind"] == "exact-name"
    assert reviewed["arity"] == arity
    assert tuple(reviewed["dependencies"]) == dependencies
    assert blueprint["reviewed_match"] == match


@pytest.mark.parametrize(
    ("name", "identifier", "route", "arity", "dependencies"),
    (
        ("MatrixSkipIndex", "ND0046", "matrix-determinant-minors", 3, ("Lt", "Le")),
        ("MatrixMinorCell", "ND0047", "matrix-determinant-minors", 8, ("MatrixSkipIndex", "Beta")),
        ("MatrixMinorPrefix", "ND0048", "matrix-determinant-minors", 9, ("Lt", "MatrixMinorCell", "Beta")),
        ("SignedMatrixMinor", "ND0049", "matrix-determinant-minors", 12, ("MatrixMinorPrefix",)),
        ("HornerDerivativeTrace", "ND0050", "polynomial-hensel", 8, ("Beta", "Horner")),
        ("HornerDerivative", "ND0051", "polynomial-hensel", 6, ("HornerDerivativeTrace", "Horner")),
        ("HornerDerivativeOnly", "ND0052", "polynomial-hensel", 5, ("HornerDerivative",)),
        ("CRTPositiveModuliPrefix", "ND0053", "generalized-crt-fold", 3, ("Beta", "Lt")),
        ("CRTPairwiseCoprimePrefix", "ND0054", "generalized-crt-fold", 3, ("Beta", "Lt", "Coprime")),
        ("CRTPrefixSolution", "ND0055", "generalized-crt-fold", 6, ("Beta", "Lt", "ModEq")),
        ("CRTPrefixLCM", "ND0056", "generalized-crt-fold", 4, ("Beta", "Lt", "Dvd")),
        ("CRTCanonicalPrefixSolution", "ND0057", "generalized-crt-fold", 7, ("CRTPrefixLCM", "Lt", "CRTPrefixSolution")),
    ),
)
def test_all_research_blueprint_names_have_exact_shared_hygienic_identities(
    graph: dict,
    name: str,
    identifier: str,
    route: str,
    arity: int,
    dependencies: tuple[str, ...],
) -> None:
    match = next(
        row for row in graph["compatible_reviewed_matches"]
        if row["blueprint_name"] == name
    )
    reviewed = next(row for row in graph["reviewed_definitions"] if row["name"] == name)
    blueprint = next(row for row in graph["definitions"] if row["name"] == name)
    assert match["reviewed_name"] == name
    assert match["reviewed_id"] == identifier
    assert match["route"] == route
    assert match["kind"] == "exact-name"
    assert reviewed["arity"] == arity
    assert tuple(reviewed["dependencies"]) == dependencies
    assert blueprint["reviewed_match"] == match


@pytest.mark.parametrize(
    ("name", "identifier", "route", "arity", "dependencies"),
    (
        ("EuclideanBoundedTrace", "ND0038", "euclidean-logarithmic-bound", 3, ("ContinuedFractionTrace", "Le")),
        ("EuclideanLogarithmicExecution", "ND0039", "euclidean-logarithmic-bound", 5, ("BitLen", "EuclideanAnchoredExecution", "Le")),
        ("BinaryExponentDigitCode", "ND0040", "binary-digit-extraction", 4, ("BinaryDigitPrefix", "Horner")),
        ("BinaryCanonicalExponentDigitCode", "ND0041", "binary-digit-extraction", 4, ("BitLen", "BinaryExponentDigitCode")),
        ("BinaryCompleteModularExecution", "ND0042", "binary-digit-extraction", 7, ("BinaryCanonicalExponentDigitCode", "BinaryModularExecution", "BinaryModularPower")),
        ("BinaryExecutionOperationCount", "ND0043", "binary-digit-extraction", 4, ("BitCount",)),
        ("PrimeThreeModFourDivisor", "ND0044", "primes-three-mod-four", 2, ("Prime", "Mod4Three", "Dvd")),
        ("EuclidThreeNumber", "ND0045", "primes-three-mod-four", 2, ("Mod4Three",)),
    ),
)
def test_all_closed_milestone_blueprint_names_have_exact_shared_hygienic_identities(
    graph: dict,
    name: str,
    identifier: str,
    route: str,
    arity: int,
    dependencies: tuple[str, ...],
) -> None:
    match = next(
        row for row in graph["compatible_reviewed_matches"]
        if row["blueprint_name"] == name
    )
    reviewed = next(row for row in graph["reviewed_definitions"] if row["name"] == name)
    blueprint = next(row for row in graph["definitions"] if row["name"] == name)
    assert match["reviewed_name"] == name
    assert match["reviewed_id"] == identifier
    assert match["route"] == route
    assert match["kind"] == "exact-name"
    assert reviewed["arity"] == arity
    assert tuple(reviewed["dependencies"]) == dependencies
    assert blueprint["reviewed_match"] == match


@pytest.mark.parametrize(
    ("name", "identifier", "route", "arity", "dependencies"),
    (
        ("PowTwo", "ND0028", "binary-length", 2, ("Pow",)),
        ("BinaryDigit", "ND0029", "binary-length", 3, ("BinaryExponentSplit",)),
        ("BitLen", "ND0030", "binary-length", 2, ("PowTwo", "Le", "Lt")),
        ("EuclideanCommonDivisor", "ND0031", "euclidean-gcd-transport", 3, ("Dvd",)),
        ("EuclideanStateAt", "ND0032", "euclidean-gcd-transport", 6, ("Beta",)),
        ("EuclideanAnchoredExecution", "ND0033", "euclidean-gcd-transport", 4, ("ContinuedFractionTrace", "EuclideanStateAt", "IsGCD")),
        ("BinaryDigitPrefix", "ND0034", "binary-modular-execution", 3, ("Beta", "Lt")),
        ("BinaryExecutionTrace", "ND0035", "binary-modular-execution", 7, ("Beta", "Lt", "BinaryModularStep")),
        ("BinaryModularExecution", "ND0036", "binary-modular-execution", 6, ("BinaryExecutionTrace", "Beta")),
        ("BinaryExecutionPowerInvariant", "ND0037", "binary-modular-execution", 6, ("Horner", "BinaryModularPower")),
    ),
)
def test_all_transport_blueprint_names_share_exact_hygienic_reviewed_identities(
    graph: dict,
    name: str,
    identifier: str,
    route: str,
    arity: int,
    dependencies: tuple[str, ...],
) -> None:
    match = next(
        row for row in graph["compatible_reviewed_matches"]
        if row["blueprint_name"] == name
    )
    reviewed = next(row for row in graph["reviewed_definitions"] if row["name"] == name)
    blueprint = next(row for row in graph["definitions"] if row["name"] == name)
    assert match["reviewed_name"] == name
    assert match["reviewed_id"] == identifier
    assert match["route"] == route
    assert match["kind"] == "exact-name"
    assert reviewed["arity"] == arity
    assert tuple(reviewed["dependencies"]) == dependencies
    assert blueprint["reviewed_match"] == match


@pytest.mark.parametrize(
    ("name", "identifier", "route", "arity", "dependencies"),
    (
        ("MatrixAffineSlice", "ND0012", "matrix-coded-products", 7, ("Beta", "Lt")),
        ("MatrixProductCell", "ND0013", "matrix-coded-products", 9, ("MatrixAffineSlice", "DotProduct")),
        ("MatrixProductPrefix", "ND0014", "matrix-coded-products", 9, ("MatrixProductCell", "Beta", "Lt")),
        ("MatrixPointwiseAdd", "ND0015", "matrix-coded-products", 7, ("Beta", "Lt")),
        ("SignedDotProduct", "ND0016", "matrix-coded-products", 11, ("DotProduct",)),
        ("SignedMatrixProduct", "ND0017", "matrix-coded-products", 15, ("MatrixProductPrefix", "MatrixPointwiseAdd")),
        ("EuclideanDivision", "ND0018", "euclidean-complexity", 4, ("Lt",)),
        ("EuclideanHalving", "ND0019", "euclidean-complexity", 2, ("Lt",)),
        ("EuclideanExecution", "ND0020", "euclidean-complexity", 4, ("ContinuedFractionTrace", "IsGCD")),
        ("BinaryModulus", "ND0021", "binary-modular-exponentiation", 1, ("Lt",)),
        ("BinaryExponentSplit", "ND0022", "binary-modular-exponentiation", 3, ()),
        ("CanonicalModularResidue", "ND0023", "binary-modular-exponentiation", 3, ("Lt", "ModEq")),
        ("BinaryDoubledPower", "ND0024", "binary-modular-exponentiation", 5, ("Pow",)),
        ("BinaryOddPower", "ND0025", "binary-modular-exponentiation", 5, ("Pow",)),
        ("BinaryModularStep", "ND0026", "binary-modular-exponentiation", 5, ("CanonicalModularResidue",)),
        ("BinaryModularPower", "ND0027", "binary-modular-exponentiation", 4, ("Pow", "CanonicalModularResidue")),
    ),
)
def test_all_advanced_blueprint_names_share_exact_hygienic_reviewed_identities(
    graph: dict,
    name: str,
    identifier: str,
    route: str,
    arity: int,
    dependencies: tuple[str, ...],
) -> None:
    match = next(
        row for row in graph["compatible_reviewed_matches"]
        if row["blueprint_name"] == name
    )
    reviewed = next(row for row in graph["reviewed_definitions"] if row["name"] == name)
    blueprint = next(row for row in graph["definitions"] if row["name"] == name)
    assert match["reviewed_name"] == name
    assert match["reviewed_id"] == identifier
    assert match["route"] == route
    assert match["kind"] == "exact-name"
    assert reviewed["arity"] == arity
    assert tuple(reviewed["dependencies"]) == dependencies
    assert blueprint["reviewed_match"] == match
    page = (
        ROOT / "book" / "_static" / "constructive-advanced-layer-explorer"
        / route / "explorer" / "defined" / "definition" / f"{identifier}.html"
    )
    assert page.is_file()


@pytest.mark.parametrize(
    ("name", "identifier", "route", "dependencies"),
    (
        ("Horner", "ND0002", "polynomial-horner", ("Beta", "Lt")),
        ("MatrixAt", "ND0003", "matrix-dot-product", ("Beta",)),
        ("DotProduct", "ND0004", "matrix-dot-product", ("Beta", "Lt", "Sum")),
        ("SignedDet2", "ND0005", "matrix-dot-product", ()),
        ("BertrandWindow", "ND0006", "bertrand-prime-chains", ("Prime", "Lt")),
        ("PowerValuationOne", "ND0007", "bertrand-prime-chains", ("PowerValuation",)),
        ("BertrandChain", "ND0008", "bertrand-prime-chains", ("Beta", "Lt", "BertrandWindow")),
        ("ContinuedFraction", "ND0011", "continued-fractions", ("ContinuedFractionTrace",)),
    ),
)
def test_new_blueprint_terms_link_to_real_shared_conservative_definitions(
    graph: dict,
    name: str,
    identifier: str,
    route: str,
    dependencies: tuple[str, ...],
) -> None:
    match = next(
        row for row in graph["compatible_reviewed_matches"]
        if row["blueprint_name"] == name
    )
    reviewed = next(
        row for row in graph["reviewed_definitions"] if row["name"] == name
    )
    blueprint = next(row for row in graph["definitions"] if row["name"] == name)
    assert match["reviewed_name"] == name
    assert match["reviewed_id"] == identifier
    assert match["route"] == route
    assert match["kind"] == "exact-name"
    assert match["reviewed_expansion_sha256"] == reviewed["expansion_sha256"]
    assert reviewed["dependencies"] == list(dependencies)
    assert blueprint["reviewed_match"] == match
    page = (
        ROOT / "book" / "_static" / "constructive-next-layer-explorer"
        / route / "explorer" / "defined" / "definition" / f"{identifier}.html"
    )
    assert page.is_file()


def test_beta_alias_keeps_old_cross_campaign_identity_only_after_exact_ast_equality(
    graph: dict,
) -> None:
    reviewed = {row["name"]: row for row in graph["reviewed_definitions"]}
    canonical = reviewed["Beta"]
    original = reviewed["BetaAt"]
    assert canonical["id"] == "ND0001"
    assert original["id"] == "PD0013"
    assert canonical["parameters"] == original["parameters"]
    assert canonical["expansion_sha256"] == original["expansion_sha256"]
    assert canonical["dependencies"] == original["dependencies"] == []
    match = next(
        row for row in graph["compatible_reviewed_matches"]
        if row["blueprint_name"] == "Beta"
    )
    assert match["reviewed_name"] == "BetaAt"
    assert match["reviewed_id"] == "PD0013"


def test_every_blueprint_definition_is_dependency_first_and_bidirectional(
    graph: dict,
    campaign: dict,
) -> None:
    rows = graph["definitions"]
    by_name = {record["name"]: record for record in rows}
    assert len(by_name) == len(campaign["definitions"])
    assert graph["topological_order"] == [record["name"] for record in rows]
    preceding: set[str] = set()
    for record in rows:
        name = record["name"]
        assert set(record["dependencies"]) <= preceding
        assert len(record["parameters"]) == record["arity"]
        assert record["authority"] == "blueprint-vocabulary-only"
        assert record["expansion_sha256"] == sha256(
            record["expansion"].encode("utf-8")
        ).hexdigest()
        assert record["topological_layer"] == max(
            (
                by_name[dependency]["topological_layer"] + 1
                for dependency in record["dependencies"]
            ),
            default=0,
        )
        for dependency in record["dependencies"]:
            assert name in by_name[dependency]["dependents"]
        expected_closure = set(record["dependencies"])
        for dependency in record["dependencies"]:
            expected_closure.update(by_name[dependency]["transitive_dependencies"])
        assert record["transitive_dependencies"] == sorted(expected_closure)
        preceding.add(name)

    assert [row["number"] for row in graph["layers"]] == list(
        range(graph["topological_layer_count"])
    )
    assert {
        (edge["source"], edge["target"])
        for edge in graph["definition_edges"]
    } == {
        (record["name"], dependency)
        for record in rows
        for dependency in record["dependencies"]
    }
    assert {edge["kind"] for edge in graph["definition_edges"]} == {
        "definition_uses_definition"
    }


def test_milestone_usage_edges_are_never_theorem_proof_dependencies(
    graph: dict,
    campaign: dict,
) -> None:
    milestone_ids = {node["id"] for node in campaign["nodes"]}
    definition_names = {record["name"] for record in graph["definitions"]}
    edges = graph["milestone_usage_edges"]
    assert len(edges) == graph["milestone_usage_edge_count"] >= 312
    assert {edge["kind"] for edge in edges} <= {
        "statement_uses_definition",
        "declared_notation",
    }
    assert all(edge["source"] in milestone_ids for edge in edges)
    assert all(edge["target"] in definition_names for edge in edges)
    assert {
        (edge["source"], edge["target"])
        for edge in edges
    } == {
        (user, record["name"])
        for record in graph["definitions"]
        for user in record["milestone_users"]
    }
    declared = {
        (edge["source"], edge["target"])
        for edge in edges
        if edge["kind"] == "declared_notation"
    }
    assert declared == {
        (node["id"], name)
        for node in campaign["nodes"]
        for name in node.get("definition_refs", [])
    }


@pytest.mark.parametrize(
    ("blueprint", "reviewed", "identifier", "positions"),
    (
        ("Beta", "BetaAt", "PD0013", [0, 1, 2, 3]),
        ("BetaSum", "Sum", "PD0015", [0, 1, 2, 3]),
        ("Binom", "Choose", "PD0041", [0, 1, 2]),
        ("Fact", "Factorial", "PD0023", [0, 1]),
        ("Gcd", "IsGCD", "PD0006", [2, 0, 1]),
    ),
)
def test_reviewed_aliases_record_exact_argument_alignments(
    graph: dict,
    blueprint: str,
    reviewed: str,
    identifier: str,
    positions: list[int],
) -> None:
    record = next(
        match
        for match in graph["compatible_reviewed_matches"]
        if match["blueprint_name"] == blueprint
    )
    assert record["reviewed_name"] == reviewed
    assert record["reviewed_id"] == identifier
    assert record["kind"] == "explicit-alias"
    assert record["reviewed_argument_blueprint_positions"] == positions
    assert record["blueprint_expansion_is_kernel_checked"] is False
    assert [record["blueprint_parameters"][index] for index in positions] == (
        record["reviewed_parameters"]
    )


@pytest.mark.parametrize(
    ("blueprint", "reviewed", "identifier"),
    (("Prod", "Product", "PD0014"), ("Sum", "Sum", "PD0015")),
)
def test_incompatible_beta_code_homonyms_grant_no_checked_evidence(
    graph: dict,
    blueprint: str,
    reviewed: str,
    identifier: str,
) -> None:
    mismatch = next(
        row
        for row in graph["incompatible_reviewed_matches"]
        if row["blueprint_name"] == blueprint
    )
    definition = next(
        row for row in graph["definitions"] if row["name"] == blueprint
    )
    assert mismatch["reviewed_name"] == reviewed
    assert mismatch["reviewed_id"] == identifier
    assert mismatch["blueprint_arity"] == 3
    assert mismatch["reviewed_arity"] == 4
    assert mismatch["reason"] == "incompatible-arity"
    assert mismatch["confers_checked_evidence"] is False
    assert definition["reviewed_incompatibility"] == mismatch
    assert definition["reviewed_match"] is None
    assert all(
        row["blueprint_name"] != blueprint
        for row in graph["compatible_reviewed_matches"]
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "invalid-name",
        "duplicate-parameter",
        "invalid-parameter",
        "empty-meaning",
        "empty-expansion",
        "self-reference",
        "cycle",
        "repeated-milestone",
        "missing-statement",
        "invalid-declared-notation",
        "duplicate-declared-notation",
        "unknown-declared-notation",
    ),
)
def test_corrupt_blueprint_definition_graph_fails_closed(
    campaign: dict,
    mutation: str,
) -> None:
    broken = deepcopy(campaign)
    if mutation == "invalid-name":
        broken["definitions"]["not-valid"] = broken["definitions"].pop("Lt")
    elif mutation == "duplicate-parameter":
        broken["definitions"]["Dvd"]["parameters"] = ["d", "d"]
    elif mutation == "invalid-parameter":
        broken["definitions"]["Dvd"]["parameters"][0] = "0bad"
    elif mutation == "empty-meaning":
        broken["definitions"]["Prime"]["meaning"] = " "
    elif mutation == "empty-expansion":
        broken["definitions"]["Prime"]["expansion"] = ""
    elif mutation == "self-reference":
        broken["definitions"]["Prime"]["expansion"] = "Prime(p)"
    elif mutation == "cycle":
        broken["definitions"]["Dvd"]["expansion"] = "Prime(d)"
    elif mutation == "repeated-milestone":
        broken["nodes"][1]["id"] = broken["nodes"][0]["id"]
    elif mutation == "missing-statement":
        broken["nodes"][0]["statement"] = None
    elif mutation == "invalid-declared-notation":
        broken["nodes"][0]["definition_refs"] = "Prime"
    elif mutation == "duplicate-declared-notation":
        broken["nodes"][0]["definition_refs"] = ["Prime", "Prime"]
    else:
        broken["nodes"][0]["definition_refs"] = ["NotAReviewedTerm"]

    with pytest.raises(definitions.DefinitionGraphError):
        definitions.build_definition_graph(broken)


@pytest.mark.parametrize(
    "mutation",
    (
        "duplicate-name",
        "duplicate-id",
        "missing-dependency",
        "repeated-dependency",
        "self-dependency",
        "cycle",
        "invalid-template",
        "changed-template",
    ),
)
def test_corrupt_reviewed_definition_registries_fail_closed(mutation: str) -> None:
    records = list(definitions.DEFINITIONS)
    if mutation == "duplicate-name":
        records[1] = replace(records[1], name=records[0].name)
    elif mutation == "duplicate-id":
        records[1] = replace(records[1], stable_id=records[0].stable_id)
    elif mutation == "missing-dependency":
        records[2] = replace(records[2], conceptual_dependencies=("Missing",))
    elif mutation == "repeated-dependency":
        records[4] = replace(records[4], conceptual_dependencies=("Dvd", "Dvd"))
    elif mutation == "self-dependency":
        records[2] = replace(records[2], conceptual_dependencies=("Dvd",))
    elif mutation == "cycle":
        records[2] = replace(records[2], conceptual_dependencies=("Prime",))
        records[3] = replace(records[3], conceptual_dependencies=("Dvd",))
    elif mutation == "invalid-template":
        records[2] = replace(records[2], template_source="exists . d = n")
    else:
        records[2] = replace(records[2], template_source="d = n")

    with pytest.raises(definitions.DefinitionGraphError):
        definitions.reviewed_registry(
            (
                ("quadratic-reciprocity", tuple(records)),
                ("bertrand-postulate", definitions.BERTRAND_DEFINITIONS),
            )
        )


@pytest.mark.parametrize(
    "mutation", ("invalid-nd-id", "duplicate-nd-name", "duplicate-nd-id", "cross-campaign-cycle")
)
def test_corrupt_shared_next_layer_definition_registries_fail_closed(mutation: str) -> None:
    groups = [(route, list(rows)) for route, rows in definitions.DEFAULT_REGISTRIES]
    first = groups[2][1][0]
    if mutation == "invalid-nd-id":
        groups[2][1][0] = replace(first, stable_id="ND00ZZ")
    elif mutation == "duplicate-nd-name":
        groups[2][1][1] = replace(groups[2][1][1], name=first.name)
    elif mutation == "duplicate-nd-id":
        groups[2][1][1] = replace(groups[2][1][1], stable_id=first.stable_id)
    else:
        groups[2][1][0] = replace(
            first, conceptual_dependencies=("ContinuedFraction",)
        )
    registries = tuple((route, tuple(rows)) for route, rows in groups)
    with pytest.raises(definitions.DefinitionGraphError):
        definitions.reviewed_registry(registries)


@pytest.mark.parametrize(
    "mutation",
    (
        "invalid-id",
        "duplicate-name",
        "duplicate-id",
        "unknown-dependency",
        "self-dependency",
        "cross-campaign-cycle",
        "changed-template",
        "duplicate-route-definition",
    ),
)
def test_corrupt_shared_advanced_definition_registries_fail_closed(mutation: str) -> None:
    groups = [(route, list(rows)) for route, rows in definitions.DEFAULT_REGISTRIES]
    matrix_index = next(
        index for index, (route, _) in enumerate(groups)
        if route == "matrix-coded-products"
    )
    euclidean_index = next(
        index for index, (route, _) in enumerate(groups)
        if route == "euclidean-complexity"
    )
    first = groups[matrix_index][1][0]
    if mutation == "invalid-id":
        groups[matrix_index][1][0] = replace(first, stable_id="ND12")
    elif mutation == "duplicate-name":
        groups[matrix_index][1][1] = replace(
            groups[matrix_index][1][1], name=first.name
        )
    elif mutation == "duplicate-id":
        groups[matrix_index][1][1] = replace(
            groups[matrix_index][1][1], stable_id=first.stable_id
        )
    elif mutation == "unknown-dependency":
        groups[matrix_index][1][0] = replace(
            first, conceptual_dependencies=("UnreviewedDefinition",)
        )
    elif mutation == "self-dependency":
        groups[matrix_index][1][0] = replace(
            first, conceptual_dependencies=(first.name,)
        )
    elif mutation == "cross-campaign-cycle":
        groups[matrix_index][1][0] = replace(
            first, conceptual_dependencies=("EuclideanExecution",)
        )
        euclidean = groups[euclidean_index][1][2]
        groups[euclidean_index][1][2] = replace(
            euclidean, conceptual_dependencies=(first.name,)
        )
    elif mutation == "changed-template":
        groups[matrix_index][1][0] = replace(first, template_source="b = c")
    else:
        groups[euclidean_index][1].append(first)
    registries = tuple((route, tuple(rows)) for route, rows in groups)
    with pytest.raises(definitions.DefinitionGraphError):
        definitions.reviewed_registry(registries)


@pytest.mark.parametrize(
    "mutation",
    (
        "invalid-id",
        "duplicate-name",
        "duplicate-id",
        "unknown-dependency",
        "self-dependency",
        "cross-campaign-cycle",
        "changed-template",
        "wrong-arity",
        "duplicate-mod4three",
    ),
)
def test_corrupt_closed_milestone_definition_registries_fail_closed(mutation: str) -> None:
    groups = [(route, list(rows)) for route, rows in definitions.DEFAULT_REGISTRIES]
    euclidean_index = next(
        index for index, (route, _) in enumerate(groups)
        if route == "euclidean-logarithmic-bound"
    )
    binary_index = next(
        index for index, (route, _) in enumerate(groups)
        if route == "binary-digit-extraction"
    )
    prime_index = next(
        index for index, (route, _) in enumerate(groups)
        if route == "primes-three-mod-four"
    )
    first = groups[euclidean_index][1][0]
    if mutation == "invalid-id":
        groups[euclidean_index][1][0] = replace(first, stable_id="ND003X")
    elif mutation == "duplicate-name":
        groups[euclidean_index][1][1] = replace(groups[euclidean_index][1][1], name=first.name)
    elif mutation == "duplicate-id":
        groups[euclidean_index][1][1] = replace(
            groups[euclidean_index][1][1], stable_id=first.stable_id
        )
    elif mutation == "unknown-dependency":
        groups[euclidean_index][1][0] = replace(
            first, conceptual_dependencies=("UnreviewedMilestoneDefinition",)
        )
    elif mutation == "self-dependency":
        groups[euclidean_index][1][0] = replace(first, conceptual_dependencies=(first.name,))
    elif mutation == "cross-campaign-cycle":
        groups[euclidean_index][1][0] = replace(
            first, conceptual_dependencies=("BinaryExponentDigitCode",)
        )
        binary = groups[binary_index][1][0]
        groups[binary_index][1][0] = replace(binary, conceptual_dependencies=(first.name,))
    elif mutation == "changed-template":
        groups[euclidean_index][1][0] = replace(first, template_source="a = b")
    elif mutation == "wrong-arity":
        groups[euclidean_index][1][0] = replace(first, parameters=("a", "b"))
    else:
        groups[prime_index][1].append(ALL_MILESTONE_DEFINITIONS_BY_NAME["Mod4Three"])
    with pytest.raises(definitions.DefinitionGraphError):
        definitions.reviewed_registry(tuple((route, tuple(rows)) for route, rows in groups))


def test_beta_direct_name_cannot_shadow_old_alias_without_identical_expansion(
    campaign: dict,
) -> None:
    groups = [(route, list(rows)) for route, rows in definitions.DEFAULT_REGISTRIES]
    beta = groups[2][1][0]
    mutated = "b = b"
    groups[2][1][0] = replace(
        beta,
        template_source=mutated,
        template_formula=parse_formula_in_context(mutated, list(beta.parameters)),
    )
    with pytest.raises(definitions.DefinitionGraphError, match="competing"):
        definitions.build_definition_graph(
            campaign,
            registries=tuple((route, tuple(rows)) for route, rows in groups),
        )


@pytest.mark.parametrize(
    "alignment",
    ((0, 1), (0, 0, 1), (0, 1, 2)),
)
def test_wrong_gcd_argument_permutation_cannot_inherit_checked_evidence(
    campaign: dict,
    alignment: tuple[int, ...],
) -> None:
    aliases = dict(definitions.REVIEWED_BLUEPRINT_ALIASES)
    aliases["Gcd"] = ("IsGCD", alignment)
    with pytest.raises(definitions.DefinitionGraphError, match="argument"):
        definitions.build_definition_graph(campaign, aliases=aliases)


def test_staging_synchronizer_checks_both_snapshot_and_definition_dag() -> None:
    result = subprocess.run(
        ["python3", str(SCRIPTS / "sync_constructive_grand_campaign.py"), "--check"],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "snapshot verified" in result.stdout
    assert "definition DAG verified" in result.stdout
