"""Large local propositions get checked notation, with bounded exact fallbacks."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
from pathlib import Path
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_constructive_frontier_explorer as generator  # noqa: E402
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.library.bertrand_defined_edition import (  # noqa: E402
    parse_bertrand_defined_formula_in_context,
)
from peano_lab.library.fermat_two_squares_pairing_candidate import (  # noqa: E402
    make_fermat_two_squares_pairing_candidate_theorems,
)
from peano_lab.library.theorems import TheoremSpec  # noqa: E402


@pytest.fixture(scope="module")
def flagship() -> TheoremSpec:
    return next(
        spec
        for spec in make_fermat_two_squares_pairing_candidate_theorems(TheoremSpec)
        if spec.name == "two_square_iff_zero_or_even_three_mod_four_prime_valuations"
    )


@pytest.fixture(scope="module")
def definitions() -> dict[str, dict[str, object]]:
    return {
        record["id"]: record
        for record in generator.defined_adapter.definition_json_records()
    }


def _node(
    script: tuple[str, ...], *, statement: str = "0 = 0", root: bool = False
) -> dict[str, object]:
    return {
        "name": "local_formula_compaction_regression",
        "statement": statement,
        "statement_sha256": sha256(statement.encode()).hexdigest(),
        "script": script,
        "root": root,
    }


def _assert_exact_line(line: dict[str, object], command: str) -> None:
    assert line["expanded_command_sha256"] == sha256(command.encode()).hexdigest()
    assert "".join(part["text"] for part in line["command_parts"]) == (
        line["defined_command"]
    )
    receipt = line["proposition_receipt"]
    exact_source = command.partition(":")[2].strip()
    defined_source = line["defined_command"].partition(":")[2].strip()
    assert receipt["expanded_source_sha256"] == sha256(exact_source.encode()).hexdigest()
    assert receipt["defined_source_sha256"] == sha256(defined_source.encode()).hexdigest()
    assert receipt["exact_ast_equivalence"] is True
    assert parse_formula_in_context(exact_source, receipt["free_names"]) == (
        parse_bertrand_defined_formula_in_context(defined_source, receipt["free_names"])
    )


def test_ts003f_giant_local_lemmas_have_short_exact_readings(flagship, definitions):
    node = _node(flagship.script, statement=flagship.statement, root=True)
    result = generator._defined_node(node, definitions)
    lines = result["defined_script_lines"]
    assert [line["number"] for line in lines] == [13, 27]
    assert result["skipped_tactic_propositions"] == 0
    for line in lines:
        command = flagship.script[line["number"] - 1]
        assert len(command) > 21_000
        assert len(line["defined_command"]) < 300
        assert "PowerValuation(" in line["defined_command"]
        _assert_exact_line(line, command)


def test_small_early_lines_do_not_starve_a_large_local_lemma(flagship, definitions):
    command = flagship.script[12]
    script = tuple(f"have h{index} : {index} = {index}" for index in range(12)) + (
        command,
    )
    result = generator._defined_node(_node(script), definitions)
    assert result["skipped_tactic_propositions"] == 0
    assert [line["number"] for line in result["defined_script_lines"]] == [13]
    _assert_exact_line(result["defined_script_lines"][0], command)


@pytest.mark.parametrize("budget_kind", ("single_source", "total_source", "source_count"))
def test_budget_exhaustion_retains_exact_source_without_a_receipt(
    monkeypatch, flagship, definitions, budget_kind
):
    command = flagship.script[12]
    source = command.partition(":")[2].strip()
    script = (command,)
    if budget_kind == "single_source":
        monkeypatch.setattr(
            generator, "MAX_DEFINED_TACTIC_PROPOSITION_CHARACTERS", len(source) - 1
        )
    elif budget_kind == "total_source":
        monkeypatch.setattr(
            generator, "MAX_DEFINED_TACTIC_SOURCE_CHARACTERS_PER_NODE", len(source) - 1
        )
    else:
        monkeypatch.setattr(generator, "MAX_DEFINED_TACTIC_PROPOSITIONS_PER_NODE", 1)
        script = ("have first : 0 = 0", command)
    node = _node(script)
    result = generator._defined_node(node, definitions)
    assert result["skipped_tactic_propositions"] == 1
    assert result["defined_script_lines"] == []
    assert result["script_definition_uses"] == {}
    assert node["script"] == script


def test_repeated_propositions_share_budget_but_keep_separate_receipts(
    monkeypatch, flagship, definitions
):
    source = flagship.script[12].partition(":")[2].strip()
    monkeypatch.setattr(generator, "MAX_DEFINED_TACTIC_PROPOSITIONS_PER_NODE", 1)
    monkeypatch.setattr(
        generator, "MAX_DEFINED_TACTIC_SOURCE_CHARACTERS_PER_NODE", len(source)
    )
    script = (
        f"have first : {source}",
        "have over_budget : 0 = 0",
        f"suffices repeated : {source}",
    )
    result = generator._defined_node(_node(script), definitions)
    assert result["skipped_tactic_propositions"] == 1
    assert [line["number"] for line in result["defined_script_lines"]] == [1, 3]
    for line in result["defined_script_lines"]:
        _assert_exact_line(line, script[line["number"] - 1])


def test_large_local_formula_rejects_a_forged_equivalence_receipt(
    monkeypatch, flagship, definitions
):
    command = flagship.script[12]
    tactic = generator.defined_adapter.compact_tactic_command(command, 1)
    forged_receipt = replace(tactic.proposition.receipt, exact_ast_equivalence=False)
    forged_proposition = replace(tactic.proposition, receipt=forged_receipt)
    forged_tactic = replace(tactic, proposition=forged_proposition)
    monkeypatch.setattr(
        generator.defined_adapter, "compact_tactic_command", lambda *_args: forged_tactic
    )
    with pytest.raises(ValueError, match="equivalence"):
        generator._defined_node(_node((command,)), definitions)
