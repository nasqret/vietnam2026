"""Exact contracts for the conservative definition-aware library edition."""

from __future__ import annotations

from collections import Counter
from hashlib import sha256
import json

import pytest

from peano_lab.kernel.formulas import parse_formula, parse_formula_with_names
from peano_lab.library.defined_edition import (
    DEFINED_EDITION_SCHEMA,
    DefinedEditionError,
    DefinedTheoremSpec,
    build_defined_edition,
    compact_formula_source,
    compact_tactic_command,
    compact_theorem_spec,
    compile_defined_library,
    compile_defined_spec,
    defined_library_edition,
)
from peano_lab.library.defined_syntax import (
    DEFINITIONS,
    parse_defined_formula_in_context,
)
from peano_lab.library.quadratic_reciprocity_stack_runtime import (
    quadratic_reciprocity_stack,
)
from peano_lab.library.theorems import TheoremSpec


def test_structural_compaction_prefers_specific_and_composite_definitions() -> None:
    strict = compact_formula_source("exists h. h + S a = b")
    weak = compact_formula_source("exists h. h + a = b")
    assert strict.defined_source == "Lt(a,b)"
    assert weak.defined_source == "Le(a,b)"

    prime = compact_formula_source(
        "~(p = 1) /\\ forall a b. p = a * b -> a = 1 \\/ b = 1"
    )
    assert prime.defined_source == "Prime(p)"
    assert prime.receipt.exact_ast_equivalence


def test_compaction_is_binder_aware_and_reexpands_in_the_original_name_scope() -> None:
    source = "forall q. exists witness. S q = (q + 1) * witness"
    compacted = compact_formula_source(source)
    assert compacted.defined_source == "∀ q. Dvd(q + 1,S q)"
    assert compacted.receipt.free_names == ()
    assert parse_defined_formula_in_context(compacted.defined_source, []) == parse_formula(
        source
    )
    assert "Dvd" in {use.name for use in compacted.receipt.definition_uses}


def test_have_and_suffices_compact_only_the_local_proposition() -> None:
    command = "have hd : exists q. n = d * q"
    compacted = compact_tactic_command(command, 17)
    assert compacted.line_number == 17
    assert compacted.defined_command == "have hd : Dvd(d,n)"
    assert "".join(part.text for part in compacted.parts) == compacted.defined_command
    assert [part.kind for part in compacted.parts] == ["text", "definition"]
    assert compacted.proposition is not None
    assert compacted.proposition.receipt.exact_ast_equivalence

    sufficient = compact_tactic_command(
        "suffices hp : ~(p = 1) /\\ forall a b. p = a * b -> a = 1 \\/ b = 1"
    )
    assert sufficient.defined_command == "suffices hp : Prime(p)"
    unchanged = compact_tactic_command("exact hd")
    assert unchanged.defined_command == "exact hd"
    assert unchanged.proposition is None
    assert [part.as_json() for part in unchanged.parts] == [
        {"kind": "text", "text": "exact hd"}
    ]

    with pytest.raises(DefinedEditionError, match="malformed have"):
        compact_tactic_command("have hd")


def test_defined_specs_compile_to_the_ordinary_theorem_type_and_core_asts() -> None:
    defined = DefinedTheoremSpec(
        "dvd_reflexive_surface",
        "forall n. Dvd(n,n)",
        (),
        (
            "intro n",
            "have hd : Dvd(n,n)",
            "exists n",
            "simp",
            "exact hd",
        ),
        "Definition-aware compiler fixture.",
    )
    compiled = compile_defined_spec(defined)
    assert type(compiled) is TheoremSpec
    assert parse_formula_with_names(compiled.statement)[0] == parse_formula(
        "forall n. exists q. n = n * q"
    )
    assert "Dvd(" not in compiled.statement
    assert "Dvd(" not in compiled.script[1]

    explicit = TheoremSpec(
        defined.name,
        "forall n. exists q. n = n * q",
        defined.dependencies,
        (
            "intro n",
            "have hd : exists q. n = n * q",
            "exists n",
            "simp",
            "exact hd",
        ),
        defined.summary,
    )
    record = compact_theorem_spec(explicit, scope="public")
    assert record.defined_spec.statement == "∀ n. Dvd(n,n)"
    assert parse_formula_with_names(record.compiled_spec.statement)[0] == (
        parse_formula_with_names(explicit.statement)[0]
    )


def test_exact_qr_closure_has_complete_receipts_metrics_and_compilation() -> None:
    edition = defined_library_edition()
    stack = quadratic_reciprocity_stack()
    assert edition.schema == DEFINED_EDITION_SCHEMA
    assert len(DEFINITIONS) == 40
    assert tuple(definition.stable_id for definition in DEFINITIONS) == tuple(
        f"PD{index:04d}" for index in range(1, 41)
    )
    assert len(edition.records) == len(stack.combined_order) == 557
    assert tuple(edition.by_name) == tuple(
        spec.name for _, spec in stack.combined_order
    )
    assert edition.metrics.public_theorem_count == 241
    assert edition.metrics.candidate_theorem_count == 316
    assert edition.metrics.tactic_line_count == 27_491
    assert edition.metrics.local_statement_count == 1_839
    assert edition.metrics.changed_theorem_statement_count == 506
    assert edition.metrics.changed_local_statement_count == 1_275
    assert edition.metrics.expanded_statement_characters == 2_457_096
    assert edition.metrics.defined_statement_characters == 107_386
    assert edition.metrics.expanded_local_statement_characters == 1_971_403
    assert edition.metrics.defined_local_statement_characters == 111_519
    assert edition.metrics.longest_expanded_statement == (
        "eisenstein_transposed_column_count_prefix_extend",
        82_377,
    )
    assert edition.metrics.longest_defined_statement == (
        "eisenstein_transposed_column_count_prefix_extend",
        1_759,
    )
    assert edition.metrics.longest_expanded_local_statement == (
        "eisenstein_rectangle_floor_sum_identity",
        15,
        36_479,
    )
    assert edition.metrics.longest_defined_local_statement == (
        "eisenstein_successor_row_split_prefix_exists",
        26,
        963,
    )
    root = edition.by_name["quadratic_reciprocity_combined"]
    assert root.defined_spec.statement.startswith("∀ p. ∀ q. ")
    assert "Prime(p)" in root.defined_spec.statement
    assert "Prime(q)" in root.defined_spec.statement

    compiled = compile_defined_library()
    assert len(compiled) == 557
    for record, compiled_spec in zip(edition.records, compiled, strict=True):
        assert record.compiled_spec is compiled_spec
        assert record.statement.receipt.exact_ast_equivalence
        assert "".join(part.text for part in record.statement.parts) == (
            record.defined_spec.statement
        )
        assert len(record.tactics) == len(record.expanded_spec.script)
        for tactic in record.tactics:
            assert "".join(part.text for part in tactic.parts) == tactic.defined_command
            if tactic.proposition is not None:
                assert tactic.proposition.receipt.exact_ast_equivalence


def test_explorer_adapter_is_json_stable_and_attests_statements_and_all_lines() -> None:
    raw = build_defined_edition()
    assert raw["schema"] == DEFINED_EDITION_SCHEMA
    definitions = raw["definitions"]
    theorems = raw["theorems"]
    assert isinstance(definitions, list) and len(definitions) == 40
    assert isinstance(theorems, list) and len(theorems) == 557
    json.dumps(raw, ensure_ascii=False)

    stack = quadratic_reciprocity_stack()
    for theorem, (_, spec) in zip(theorems, stack.combined_order, strict=True):
        assert theorem["name"] == spec.name
        assert theorem["expanded_statement_sha256"] == sha256(
            spec.statement.encode("utf-8")
        ).hexdigest()
        assert "".join(part["text"] for part in theorem["statement_parts"]) == (
            theorem["defined_statement"]
        )
        lines = theorem["defined_script_lines"]
        assert len(lines) == len(spec.script)
        for line, expanded in zip(lines, spec.script, strict=True):
            assert "".join(part["text"] for part in line["command_parts"]) == (
                line["defined_command"]
            )
            assert line["expanded_command_sha256"] == sha256(
                expanded.encode("utf-8")
            ).hexdigest()

    normalized_theorems = []
    for theorem in theorems:
        statement_counts = Counter(
            part["definition"]
            for part in theorem["statement_parts"]
            if part["kind"] == "definition"
        )
        script_counts = Counter(
            part["definition"]
            for line in theorem["defined_script_lines"]
            for part in line["command_parts"]
            if part["kind"] == "definition"
        )
        normalized_theorems.append(
            {
                "name": theorem["name"],
                "defined_statement": theorem["defined_statement"],
                "expanded_statement_sha256": theorem["expanded_statement_sha256"],
                "statement_parts": theorem["statement_parts"],
                "defined_script_lines": theorem["defined_script_lines"],
                "statement_definition_uses": dict(sorted(statement_counts.items())),
                "script_definition_uses": dict(sorted(script_counts.items())),
                "definition_uses": dict(
                    sorted((statement_counts + script_counts).items())
                ),
            }
        )
    semantic = {
        "schema": DEFINED_EDITION_SCHEMA,
        "definitions": definitions,
        "theorems": normalized_theorems,
    }
    assert raw["identity_sha256"] == sha256(
        json.dumps(
            semantic,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
