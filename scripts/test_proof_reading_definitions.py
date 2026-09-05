"""Notation becomes shorter only after exact expansion and DAG validation."""
from copy import deepcopy
from hashlib import sha256
from importlib import import_module

import pytest

from proof_readability import ReadabilityError, enhance_page, parse_page, strip_reading_layer
from proof_reading_definitions import ReadingDefinitions
from test_proof_readability import fixture


def definition_rows():
    source = "exists q. d * q = n"
    return [dict(id="PD0003", name="Divides", parameters=["d", "n"],
        expanded_template=source, expansion_sha256=sha256(source.encode()).hexdigest(),
        dependencies=[], summary="A witnessed multiple.")]


def test_long_claim_is_shortened_with_exact_free_context_and_original_bytes():
    command = "have h : " + " /\\ ".join(["(exists q. d * q = n)"] * 35)
    raw = fixture((command,))
    definitions = ReadingDefinitions(definition_rows(), dict(path="family/api/corpus.json", sha256="0" * 64))
    revised, report = enhance_page(raw, assets_prefix="../../../assets/", revision="0123456789ab", definitions=definitions)
    assert strip_reading_layer(revised) == raw
    assert report["notation_compacted_claims"] == 1
    receipt = report["notation_compactions"][0]
    assert receipt["exact_ast_equivalence"] is True and set(receipt["free_names"]) == {"d", "n"}
    assert receipt["definition_uses"] == {"PD0003": 35}
    assert b'href="../defined/definition/PD0003.html"' in revised
    assert report["notation_display_characters_saved"] > 0


def test_parameter_order_and_inner_binder_are_not_guessed():
    definitions = ReadingDefinitions(definition_rows(), {})
    source = "have h : exists d. n * d = q"
    page, report = definitions.apply(parse_page(fixture((source,)).decode()), minimum_characters=0)
    assert page.lines[0].displayed == "have h : Divides(n,q)"
    assert report["notation_compactions"][0]["free_names"] == ["n", "q"]


def test_historical_signature_schema_is_supported_without_new_aliases():
    row = definition_rows()[0]
    row["signature"] = "Divides(d,n)"
    row["expansion"] = row.pop("expanded_template")
    del row["parameters"]
    definitions = ReadingDefinitions([row], {})
    assert definitions.report["topological_order"] == ["PD0003"]
    assert definitions.report["new_definitions"] is False


def test_existing_zero_argument_condition_is_expanded_not_assumed():
    source = "forall n m k. n + m + k = n + m + k"
    row = dict(id="CF0015", name="ClosedCondition", parameters=[], expanded_template=source,
        expansion_sha256=sha256(source.encode()).hexdigest(), dependencies=[])
    definitions = ReadingDefinitions([row], {})
    page, report = definitions.apply(parse_page(fixture(("have h : " + source,)).decode()), minimum_characters=0)
    assert page.lines[0].displayed == "have h : ClosedCondition()"
    assert report["notation_compactions"][0]["free_names"] == []


@pytest.mark.parametrize("fault", ["hash", "duplicate-id", "duplicate-name", "parameters", "arity", "cycle", "missing-target"])
def test_inconsistent_definition_metadata_is_rejected(fault):
    rows = definition_rows()
    if fault == "hash":
        rows[0]["expanded_template"] = "d = n"
    elif fault.startswith("duplicate"):
        rows.append(deepcopy(rows[0]))
        if fault == "duplicate-id":
            rows[1]["name"] = "Another"
        else:
            rows[1]["id"] = "PD0004"
    elif fault == "parameters":
        rows[0]["parameters"] = ["n", "n"]
    elif fault == "arity":
        rows[0]["arity"] = 3
    else:
        rows[0]["dependencies"] = ["PD0003" if fault == "cycle" else "PD0004"]
    with pytest.raises(ReadabilityError):
        ReadingDefinitions(rows, {})


def test_inferred_application_remains_a_command_not_an_invented_formula():
    definitions = ReadingDefinitions(definition_rows(), {})
    page = parse_page(fixture(("have h := supplied n",)).decode())
    revised, report = definitions.apply(page, minimum_characters=0)
    assert revised == page and report["notation_compacted_claims"] == 0


@pytest.mark.parametrize("module", [
    "build_constructive_second_wave_explorer", "build_constructive_bottom_layer_explorer",
    "build_constructive_polynomial_euclidean_explorer_v33", "build_constructive_gcd_congruence_explorer_v34",
])
def test_campaign_authoring_adapters_preserve_inferred_claims(module):
    from peano_lab.library.theorems import TheoremSpec
    adapter = import_module(module)
    spec = TheoremSpec("example", "forall n. n = n", (), ("have h := supplied n",), "Example.")
    reading = dict(statement_definition_uses={})
    adapter._compact_script(spec, None, reading)
    assert reading["defined_script"] == list(spec.script)
    assert reading["script_definition_uses"] == {} and reading["definition_uses"] == {}
