"""Bounded audit of six offline, evidence-honest candidate proof explorers."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import json
from math import comb, isqrt
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


REPO = Path(__file__).resolve().parents[3]
SCRIPTS = REPO / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import build_constructive_frontier_explorer as generator  # noqa: E402
from peano_lab.kernel.formulas import parse_formula_in_context  # noqa: E402
from peano_lab.library.bertrand_defined_edition import (  # noqa: E402
    parse_bertrand_defined_formula_in_context,
)
from peano_lab.library import editions_v12 as v12  # noqa: E402
from peano_lab.library import editions_v13 as v13  # noqa: E402
from peano_lab.library import editions_v14 as v14  # noqa: E402
from peano_lab.library import editions_v15 as v15  # noqa: E402


EXPECTED_FAMILIES = (
    "supplementary-laws",
    "kummer",
    "two-squares",
    "four-squares",
    "lucas",
    "pythagorean-fermat-four",
)
EXPECTED_ALPHA_V15_ENROLLMENT_BY_FAMILY = {
    "supplementary-laws": 28,
    "kummer": 13,
    "two-squares": 107,
    "four-squares": 178,
    "lucas": 44,
    "pythagorean-fermat-four": 0,
}
REQUIRED_ROOTS = {
    "supplementary-laws": {
        "quadratic_supplement_minus_one_complete",
        "quadratic_supplement_two_complete",
    },
    "kummer": {"kummer_binomial_carry_bit_count"},
    "two-squares": {
        "prime_mod_four_one_is_sum_of_two_squares",
        "brahmagupta_fibonacci_two_square_identity",
        "prime_is_two_squares_iff_two_or_one_mod_four",
        "three_mod_four_prime_divides_two_square_norm_divides_both",
        "three_mod_four_prime_represented_nonzero_valuation_even",
        "even_valuation_sorted_terminal_prime_has_equal_predecessor",
        "nonzero_two_square_iff_even_three_mod_four_prime_valuations",
        "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
    },
    "four-squares": {
        "quaternion_coordinate_absolute_total",
        "four_square_two_square_factor_identity",
        "four_square_two_square_factor_total",
        "four_square_euler_all_mixed_cancel",
        "four_square_euler_quaternion_conditional",
        "four_square_euler_three_square_expansion",
        "four_square_euler_add_permute_sixteen",
        "four_square_euler_coordinate_triple_decompose",
        "four_square_euler_global_compensation",
        "four_square_euler_quaternion",
        "four_square_euler_four_square_product_total",
        "four_square_euler_representations_closed_under_multiplication",
        "four_square_lagrange_from_three_mod_four_primes",
        "four_square_lagrange_iff_three_mod_four_primes",
        "four_square_cross_interleaved_prefix_exists",
        "four_square_cross_intersection",
        "four_square_prime_half_square_residues_injective",
        "four_square_square_residue_prefix_exists",
        "four_square_bounded_complement_prefix_exists",
        "four_square_odd_prime_modular_seed",
        "four_square_non_two_prime_modular_seed",
        "four_square_prime_modular_seed",
        "four_square_odd_prime_half_coordinate_seed",
        "four_square_odd_prime_half_seed_norm_strict",
        "four_square_odd_prime_bounded_modular_seed",
        "four_square_non_two_prime_bounded_modular_seed",
        "four_square_prime_bounded_modular_seed",
        "four_square_descent_quaternion_quotient",
        "four_square_descent_centered_signed_remainder_exists",
        "four_square_descent_even_multiplier_matching_parity_halving",
        "four_square_parity_even_norm_pair_selection",
        "four_square_parity_even_multiplier_halving",
        "four_square_parity_represented_double_halving",
        "four_square_parity_represented_additive_double_halving",
        "four_square_descent_odd_centered_norm_strict",
        "four_square_descent_bounded_centered_quotient_nonzero",
        "four_square_descent_odd_centered_strict_step",
        "four_square_branch_even_represented_strict_step",
        "four_square_bounded_strict_descent_from_odd_signed_quaternion",
        "four_square_signed_centered_square_congruent",
        "four_square_signed_centered_norm_congruent",
        "four_square_signed_centered_norm_quotient_exists",
        "four_square_signed_absolute_congruence_divisible",
        "four_square_signed_conjugate_positive_blocks",
        "four_square_signed_conjugate_negative_blocks",
        "four_square_signed_conjugate_mixed_blocks",
        "four_square_signed_natural_negative_first_blocks",
        "four_square_signed_natural_positive_first_blocks",
        "four_square_signed_divisible_norm_product_representation",
        "four_square_signed_absolute_block_representation",
        "four_square_signed_orientation_mask_00",
        "four_square_signed_orientation_mask_03",
        "four_square_signed_orientation_mask_07",
        "four_square_signed_orientation_mask_15",
        "four_square_signed_centered_representation",
        "four_square_conjugate_global_compensation",
        "four_square_signed_conjugate_quaternion",
        "four_square_conjugate_absolute_coordinates_total",
        "four_square_lagrange_from_modular_seeds_and_strict_descent",
        "four_square_prime_from_strict_descent",
        "four_square_lagrange_from_strict_descent",
        "four_square_descent_below_prime_multiplier_bounded",
        "four_square_prime_from_bounded_strict_descent_and_seed",
        "four_square_prime_from_bounded_strict_descent",
        "four_square_lagrange_from_bounded_strict_descent",
        "four_square_prime_from_odd_signed_quaternion",
        "four_square_lagrange_from_odd_signed_quaternion",
        "four_square_prime_representation",
        "four_square_lagrange",
    },
    "lucas": {
        "lucas_digit_carry_iff_prime_divides",
        "lucas_base_p_two_digit_total",
        "lucas_base_p_two_digit_reconstruction",
        "lucas_prime_row_sparse_complete",
        "lucas_prime_row_interior_zero_mod",
        "lucas_pascal_congruence_step",
        "lucas_prime_shift_below_base",
        "lucas_prime_shift_high_column",
        "lucas_repeated_prime_shift_below_base",
        "lucas_low_digit_product_congruence",
        "lucas_prime_block_digit_congruence",
        "lucas_one_step_division_congruence",
        "lucas_digit_chain_exists",
        "lucas_prime_digit_chain_exists",
        "lucas_digit_chain_step_exists",
        "lucas_choose_prefix_exists",
        "lucas_choose_prefix_point",
        "lucas_modular_backward_product_fold",
        "lucas_multidigit_congruence_from_one_step",
        "lucas_terminating_multidigit_theorem_from_one_step",
        "lucas_prime_digit_chain_terminal_zero",
        "lucas_terminating_prime_digit_chain_exists",
        "lucas_multidigit_congruence",
        "lucas_terminating_multidigit_theorem",
        "lucas_theorem_for_length",
        "lucas_theorem",
    },
    "pythagorean-fermat-four": {
        "pythagorean_euclidean_identity",
        "pythagorean_euclidean_from_order",
        "pythagorean_primitive_leg_swap",
        "pythagorean_opposite_parity_hypotenuse_odd",
        "pythagorean_primitive_euclidean_legs",
        "pythagorean_primitive_euclidean_constructor",
        "pythagorean_primitive_euclidean_from_order",
        "pythagorean_primitive_euclidean_swapped_constructor",
        "pythagorean_primitive_pairwise_coprime",
        "pythagorean_primitive_legs_not_both_even",
        "pythagorean_triple_legs_not_both_odd",
        "pythagorean_primitive_legs_opposite_parity",
        "pythagorean_primitive_hypotenuse_odd",
        "pythagorean_primitive_normal_form",
        "fermat_four_bounded_descent",
        "fermat_four_no_square_from_descent",
        "fermat_four_no_fourth_from_descent",
    },
}


@pytest.fixture(scope="module")
def generated() -> tuple[dict[str, bytes], dict[str, object]]:
    return generator.build_files()


def _corpus(files: dict[str, bytes], slug: str) -> dict[str, object]:
    return json.loads(files[f"{slug}/api/corpus.json"])


def test_custom_coprime_alias_preserves_its_existing_reviewed_definition() -> None:
    coprime = generator._definition_table()["Coprime"]

    assert coprime["id"] == "PD0005"
    assert coprime["origin"] == "existing-conservative-definition"


def test_incompatible_custom_definition_cannot_shadow_existing_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    custom = generator._custom_definitions()
    custom["Coprime"] = {
        "id": "CF9999",
        "name": "Coprime",
        "parameters": ["x", "y"],
        "summary": "forged collision",
        "expanded_template": "x = y",
        "template_sha256": sha256(b"x = y").hexdigest(),
        "origin": "frontier-conservative-display-alias",
    }
    monkeypatch.setattr(generator, "_custom_definitions", lambda: custom)

    with pytest.raises(ValueError, match="shadows an incompatible"):
        generator._definition_table()


def _browser_example(
    files: dict[str, bytes], example_name: str, inputs: dict[str, int]
) -> str:
    """Run the actual standalone calculator against a tiny browser stub."""

    corpus = json.dumps(
        {
            "nodes": [],
            "external_dependencies": [],
            "definitions": [],
            "edges": [],
            "root_names": [],
            "example": example_name,
        }
    )
    harness = (
        f"const corpus = {corpus};\n"
        f"const values = {json.dumps(inputs)};\n"
        "const output = {textContent: ''};\n"
        "const form = {addEventListener() {}};\n"
        "const example = {querySelector(selector) {\n"
        "  if (selector === '[data-example-form]') return form;\n"
        "  if (selector === '[data-example-result]') return output;\n"
        "  const input = selector.match(/data-input=\\\"([^\\\"]+)\\\"/);\n"
        "  return input ? {value: values[input[1]]} : null;\n"
        "}};\n"
        "global.document = {\n"
        "  getElementById(id) { return id === 'frontier-corpus'\n"
        "    ? {textContent: JSON.stringify(corpus)} : null; },\n"
        "  querySelector(selector) {\n"
        "    return selector === '[data-example]' ? example : null;\n"
        "  },\n"
        "  querySelectorAll() { return []; }\n"
        "};\n"
        "global.window = {print() {}};\n"
        + files["assets/frontier.js"].decode()
        + "\nprocess.stdout.write(output.textContent);\n"
    )
    return subprocess.run(
        ["node", "-e", harness],
        check=True,
        text=True,
        capture_output=True,
    ).stdout


def test_frontier_inventory_is_deterministic_complete_and_evidence_honest(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, manifest = generated
    repeated_files, repeated_manifest = generator.build_files()

    assert files == repeated_files
    assert manifest == repeated_manifest
    assert manifest["schema"] == generator.MANIFEST_SCHEMA
    assert manifest["family_count"] == 6
    assert tuple(row["slug"] for row in manifest["families"]) == EXPECTED_FAMILIES
    assert manifest["candidate_status"] == generator.CANDIDATE_STATUS
    assert manifest["alpha_edition_version"] == "v15"
    assert manifest["alpha_edition_identity_sha256"] == (
        v15.ALPHA_V15_IDENTITY_SHA256
    )
    assert manifest["alpha_enrolled_node_count"] == 370
    assert manifest["alpha_checked_use_node_count"] == 0
    assert manifest["admitted_to_alpha"] is False
    assert manifest["admitted_to_stable"] is False
    assert manifest["file_count"] == len(files) == 16
    assert {row["path"] for row in manifest["files"]} == set(files) - {"manifest.json"}
    for row in manifest["files"]:
        assert row["sha256"] == sha256(files[row["path"]]).hexdigest()
        assert row["bytes"] == len(files[row["path"]])


@pytest.mark.parametrize("slug", EXPECTED_FAMILIES)
def test_each_family_exposes_exact_candidate_bodies_and_dependency_types(
    generated: tuple[dict[str, bytes], dict[str, object]], slug: str,
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, slug)
    nodes = corpus["nodes"]
    names = {node["name"] for node in nodes}

    assert corpus["slug"] == slug
    assert corpus["candidate_status"] == generator.CANDIDATE_STATUS
    assert corpus["alpha_edition_version"] == "v15"
    assert corpus["alpha_edition_identity_sha256"] == (
        v15.ALPHA_V15_IDENTITY_SHA256
    )
    assert corpus["alpha_enrolled_node_count"] == (
        EXPECTED_ALPHA_V15_ENROLLMENT_BY_FAMILY[slug]
    )
    assert corpus["alpha_checked_use_node_count"] == 0
    assert corpus["admitted_to_alpha"] is False
    assert corpus["admitted_to_stable"] is False
    assert corpus["node_count"] == len(nodes) > 0
    assert corpus["edge_count"] == len(corpus["edges"])
    assert corpus["definition_count"] == len(corpus["definitions"]) > 0
    assert REQUIRED_ROOTS[slug] <= names
    assert REQUIRED_ROOTS[slug] <= set(corpus["root_names"])
    assert len(names) == len(nodes)
    assert corpus["external_dependency_count"] == len(corpus["external_dependencies"])
    assert corpus["formal_line_count"] == sum(len(node["script"]) for node in nodes)
    assert corpus["defined_statement_count"] == sum(
        node["defined"]["statement_status"] == "exact-ast-equivalent"
        for node in nodes
    )
    assert corpus["compacted_statement_count"] == sum(
        node["defined"]["defined_statement"] != node["statement"]
        for node in nodes
    )
    assert corpus["defined_tactic_proposition_count"] == sum(
        len(node["defined"]["defined_script_lines"]) for node in nodes
    )

    for node in nodes:
        assert node["statement_sha256"] == sha256(node["statement"].encode()).hexdigest()
        alpha_entry = v15.ALPHA_EDITION.by_name.get(node["name"])
        assert node["enrolled_in_alpha"] is (alpha_entry is not None)
        assert node["alpha_checked_use"] is False
        if alpha_entry is None:
            assert node["status"] == generator.UNENROLLED_CANDIDATE_STATUS
            assert node["alpha_evidence"] is None
            assert node["alpha_edition_version"] is None
            assert node["alpha_admission_version"] is None
            assert node["alpha_edition_identity_sha256"] is None
            assert node["alpha_campaign"] is None
        else:
            assert node["status"] == generator.ALPHA_BODY_STATUS
            assert node["alpha_evidence"] == "body_checked"
            assert node["alpha_edition_version"] == "v15"
            assert node["alpha_admission_version"] in {"v13", "v14", "v15"}
            assert node["alpha_edition_identity_sha256"] == (
                v15.ALPHA_V15_IDENTITY_SHA256
            )
            assert node["alpha_campaign"] in {
                "four_square", "lucas", "kummer", "supplementary", "two_square"
            }
            assert alpha_entry.spec.statement == node["statement"]
            assert tuple(alpha_entry.spec.dependencies) == tuple(node["dependencies"])
            assert tuple(alpha_entry.spec.script) == tuple(node["script"])
        assert node["admitted_to_alpha"] is False
        assert node["admitted_to_stable"] is False
        assert node["source_module"].startswith("peano_lab.library.")
        assert isinstance(node["script"], list)
        assert node["sources"][0]["selected"] is True
        assert node["sources"][0]["source_module"] == node["source_module"]
        assert node["sources"][0]["statement_sha256"] == node["statement_sha256"]
        assert all(source["selected"] is False for source in node["sources"][1:])

    for edge in corpus["edges"]:
        assert edge["target"] in names
        alpha_entry = v15.ALPHA_EDITION.by_name.get(edge["source"])
        assert edge["enrolled_in_alpha"] is (alpha_entry is not None)
        assert edge["alpha_checked_use"] is (
            alpha_entry.checked_use if alpha_entry is not None else False
        )
        assert edge["alpha_evidence"] == (
            alpha_entry.evidence.value if alpha_entry is not None else None
        )
        assert edge["kind"] in {
            "internal-candidate",
            "cross-family-candidate",
            "stable-admitted-theorem",
            "alpha-admitted-theorem",
            "alpha-enrolled-candidate-not-admitted",
            "alpha-pending-candidate-not-admitted",
            "public-registry-release-unverified",
            "external-unenrolled-candidate",
        }
        if edge["kind"] == "internal-candidate":
            assert edge["source"] in names
        if edge["kind"] in {
            "internal-candidate",
            "cross-family-candidate",
            "alpha-enrolled-candidate-not-admitted",
            "alpha-pending-candidate-not-admitted",
            "external-unenrolled-candidate",
        }:
            assert edge["admitted_to_alpha"] is False
            assert edge["admitted_to_stable"] is False
        if edge["kind"] == "stable-admitted-theorem":
            assert edge["evidence"] == "stable_closed"
            assert edge["admitted_to_stable"] is True
        if edge["kind"] == "alpha-admitted-theorem":
            assert edge["evidence"] == "alpha_closed"
            assert edge["admitted_to_alpha"] is True
            assert edge["admitted_to_stable"] is False

    assert corpus["alpha_enrolled_root_names"] == [
        node["name"]
        for node in nodes
        if node["root"] and node["enrolled_in_alpha"]
    ]


def test_frontier_exactly_displays_all_three_minimal_alpha_appends(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, manifest = generated
    enrolled = {
        node["name"]
        for slug in EXPECTED_FAMILIES
        for node in _corpus(files, slug)["nodes"]
        if node["enrolled_in_alpha"]
    }

    assert enrolled == (
        set(v13.FRONTIER_V13_EXPECTED_NAMES)
        | set(v14.FRONTIER_V14_EXPECTED_NAMES)
        | set(v15.FRONTIER_V15_EXPECTED_NAMES)
    )
    assert len(enrolled) == manifest["alpha_enrolled_node_count"] == 370
    assert {
        row["slug"]: row["alpha_enrolled_node_count"]
        for row in manifest["families"]
    } == EXPECTED_ALPHA_V15_ENROLLMENT_BY_FAMILY
    assert all(row["alpha_checked_use_node_count"] == 0 for row in manifest["families"])


@pytest.mark.parametrize("slug", EXPECTED_FAMILIES)
def test_defined_statements_and_local_propositions_have_exact_ast_receipts(
    generated: tuple[dict[str, bytes], dict[str, object]], slug: str,
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, slug)
    definitions = {definition["id"]: definition for definition in corpus["definitions"]}

    for node in corpus["nodes"]:
        defined = node["defined"]
        assert defined["expanded_statement_sha256"] == node["statement_sha256"]
        assert "".join(part["text"] for part in defined["statement_parts"]) == (
            defined["defined_statement"]
        )
        statement_uses = Counter(
            part["definition"]
            for part in defined["statement_parts"]
            if part["kind"] == "definition"
        )
        assert dict(sorted(statement_uses.items())) == defined["statement_definition_uses"]
        assert set(defined["definition_uses"]) <= set(definitions)

        receipt = defined["statement_receipt"]
        if receipt is None:
            assert defined["statement_status"].startswith("exact-only-")
            assert defined["defined_statement"] == node["statement"]
            assert not defined["statement_definition_uses"]
        else:
            assert defined["statement_status"] == "exact-ast-equivalent"
            assert receipt["exact_ast_equivalence"] is True
            assert receipt["expanded_source_sha256"] == node["statement_sha256"]
            assert receipt["defined_source_sha256"] == sha256(
                defined["defined_statement"].encode()
            ).hexdigest()
            assert receipt["expanded_characters"] == len(node["statement"])
            assert receipt["defined_characters"] == len(defined["defined_statement"])
            assert parse_bertrand_defined_formula_in_context(
                defined["defined_statement"], receipt["free_names"]
            ) == parse_formula_in_context(node["statement"], receipt["free_names"])

        script_uses: Counter[str] = Counter()
        for line in defined["defined_script_lines"]:
            exact = node["script"][line["number"] - 1]
            assert line["expanded_command_sha256"] == sha256(exact.encode()).hexdigest()
            assert "".join(part["text"] for part in line["command_parts"]) == (
                line["defined_command"]
            )
            assert line["proposition_receipt"]["exact_ast_equivalence"] is True
            proposition = exact.partition(":")[2].strip()
            assert line["proposition_receipt"]["expanded_source_sha256"] == sha256(
                proposition.encode()
            ).hexdigest()
            script_uses.update(
                part["definition"]
                for part in line["command_parts"]
                if part["kind"] == "definition"
            )
        assert dict(sorted(script_uses.items())) == defined["script_definition_uses"]
        assert dict(sorted((statement_uses + script_uses).items())) == (
            defined["definition_uses"]
        )


def test_flagship_defined_notation_is_genuinely_readable_and_equivalent(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    examples = (
        ("supplementary-laws", "quadratic_supplement_minus_one_complete", ("Prime(", "QRes(", "Mod4One(")),
        ("kummer", "kummer_binomial_carry_bit_count", ("Prime(", "Choose(", "PowerValuation(", "BitCount(")),
        ("two-squares", "prime_mod_four_one_is_sum_of_two_squares", ("Prime(", "Mod4One(")),
        ("lucas", "lucas_digit_carry_iff_prime_divides", ("Prime(", "Choose(", "Dvd(")),
    )
    for slug, name, tokens in examples:
        node = next(row for row in _corpus(files, slug)["nodes"] if row["name"] == name)
        defined = node["defined"]
        assert defined["statement_receipt"]["exact_ast_equivalence"]
        assert len(defined["defined_statement"]) < len(node["statement"])
        assert all(token in defined["defined_statement"] for token in tokens)

    kummer = next(
        row
        for row in _corpus(files, "kummer")["nodes"]
        if row["name"] == "kummer_binomial_carry_bit_count"
    )
    assert len(kummer["statement"]) > 30_000
    assert len(kummer["defined"]["defined_statement"]) < 500


def test_oversized_nonflagship_statements_fail_closed_without_fake_receipts(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    oversized = [
        node
        for node in _corpus(files, "kummer")["nodes"]
        if not node["root"]
        and len(node["statement"]) > generator.MAX_DEFINED_STATEMENT_CHARACTERS
    ]
    assert oversized
    for node in oversized:
        assert node["defined"]["statement_status"] == "exact-only-size-budget"
        assert node["defined"]["statement_receipt"] is None
        assert node["defined"]["defined_statement"] == node["statement"]


@pytest.mark.parametrize("mutation", ("missing_ast_equivalence", "wrong_source_digest"))
def test_defined_compaction_rejects_corrupted_equivalence_receipts(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    family = next(item for item in generator.FAMILIES if item.slug == "supplementary-laws")
    node = next(row for row in generator._family_nodes(family) if row["root"])
    compacted = generator.defined_adapter.compact_formula_source(node["statement"])
    if mutation == "missing_ast_equivalence":
        receipt = replace(compacted.receipt, exact_ast_equivalence=False)
    else:
        receipt = replace(compacted.receipt, expanded_source_sha256="0" * 64)
    corrupted = replace(compacted, receipt=receipt)
    monkeypatch.setattr(
        generator.defined_adapter, "compact_formula_source", lambda _source: corrupted
    )
    definitions = {
        definition["id"]: definition
        for definition in generator._definition_table().values()
    }

    with pytest.raises(ValueError, match="equivalence|SHA-256"):
        generator._defined_node(node, definitions)


@pytest.mark.parametrize("slug", EXPECTED_FAMILIES)
def test_family_pages_are_offline_interactive_and_clearly_candidate_labeled(
    generated: tuple[dict[str, bytes], dict[str, object]], slug: str,
) -> None:
    files, _manifest = generated
    page = files[f"{slug}/index.html"].decode()

    assert generator.CANDIDATE_STATUS in page
    assert 'id="frontier-graph"' in page
    assert 'id="frontier-corpus" type="application/json"' in page
    assert 'id="frontier-detail"' in page
    assert 'id="frontier-search"' in page
    assert 'data-frontier-view="defined"' in page
    assert 'data-frontier-view="exact"' in page
    assert 'id="frontier-zoom-in"' in page
    assert 'id="frontier-zoom-out"' in page
    assert 'id="frontier-zoom-fit"' in page
    assert 'id="frontier-focus"' in page
    assert 'id="frontier-print"' in page
    assert 'id="frontier-definition-' in page
    assert 'data-example-form' in page
    assert 'href="../assets/frontier.css"' in page
    assert 'src="../assets/frontier.js"' in page
    assert "http://" not in page
    assert "https://" not in page
    for root in REQUIRED_ROOTS[slug]:
        assert root in page


def test_four_square_and_multidigit_lucas_are_enrolled_without_checked_authority(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    four = _corpus(files, "four-squares")
    lucas = _corpus(files, "lucas")

    assert "complete universal Lagrange four-square theorem" in four["scope"]
    assert "constructive modular seeds for every prime" in four["scope"]
    assert "all sixteen signed centered orientations" in four["scope"]
    assert "bounded strict prime-multiple descent" in four["scope"]
    assert "enrolled in Alpha v13 as body_checked" in four["scope"]
    assert "without checked-use authority or Stable admission" in four["scope"]
    assert "complete arbitrary-length multidigit Lucas congruence" in lucas["scope"]
    assert "enrolled in Alpha v13 as body_checked" in lucas["scope"]
    assert "without checked-use authority or Stable admission" in lucas["scope"]
    assert "kernel-checked universal theorem is available in the proof map" in files[
        "assets/frontier.js"
    ].decode()


def test_four_square_surface_exposes_the_complete_unconditional_euler_identity(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, "four-squares")
    rows = {row["name"]: row for row in corpus["nodes"]}

    assert "complete eight-variable Euler identity" in corpus["scope"]
    assert "eight-variable Euler endpoint remains conditional" not in corpus["scope"]
    assert rows["four_square_euler_global_compensation"]["statement_sha256"] == (
        "2630c8308d7c3cd5c055381f03903acd00770259dd3a4752459c9bf34a3245d5"
    )
    assert rows["four_square_euler_quaternion"]["statement_sha256"] == (
        "1ce5e34bebbf29675196c766e27edd972d8d6b151d44f63442cad2441f602a65"
    )
    assert rows["four_square_euler_four_square_product_total"]["statement_sha256"] == (
        "edaf2a69b3a80996d5f5a0505639db5607e3fe9d8230cf6375f46fb55e89cecc"
    )
    assert all(
        rows[name]["admitted_to_alpha"] is False
        and rows[name]["admitted_to_stable"] is False
        for name in (
            "four_square_euler_global_compensation",
            "four_square_euler_quaternion",
            "four_square_euler_four_square_product_total",
            "four_square_euler_representations_closed_under_multiplication",
        )
    )


def test_four_square_lagrange_reduction_preserves_its_actual_prime_hypothesis(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, "four-squares")
    rows = {row["name"]: row for row in corpus["nodes"]}
    reduction = rows["four_square_lagrange_from_three_mod_four_primes"]
    equivalence = rows["four_square_lagrange_iff_three_mod_four_primes"]

    assert reduction["statement_sha256"] == (
        "3fd036aef0aeaeee2a01875484a2071f47c484538e3e37907398b410e6222d47"
    )
    assert equivalence["statement_sha256"] == (
        "67c703fb011e9abe5c79cb74d1eef56d754da9f9313053675e8f783f79dc238c"
    )
    assert reduction["statement"].startswith("(forall fsl_three_prime_universal.")
    assert "complete universal Lagrange four-square theorem" in corpus["scope"]


def test_four_square_surface_exposes_the_complete_unconditional_lagrange_theorem(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, "four-squares")
    rows = {row["name"]: row for row in corpus["nodes"]}
    prime = rows["four_square_prime_representation"]
    universal = rows["four_square_lagrange"]

    assert prime["statement_sha256"] == (
        "561b591ea074bf6a2d715665afde074b2c6a90f86c08bdbfa4b6b94553a92240"
    )
    assert universal["statement_sha256"] == (
        "fb653494c208dd59fac181164286a628866e3f7ca467e2a04314b9cb1f3c29a5"
    )
    assert universal["statement"].startswith("forall n.")
    assert "four_square_signed_centered_representation" in prime["dependencies"]
    assert "four_square_prime_representation" in universal["dependencies"]
    assert universal["enrolled_in_alpha"] is True
    assert universal["alpha_evidence"] == "body_checked"
    assert universal["alpha_checked_use"] is False
    assert universal["alpha_campaign"] == "four_square"
    assert universal["status"] == generator.ALPHA_BODY_STATUS
    assert universal["admitted_to_alpha"] is False
    assert universal["admitted_to_stable"] is False
    assert corpus["root_names"][-1] == "four_square_lagrange"


def test_four_square_surface_exposes_unconditional_prime_modular_seeds(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, "four-squares")
    rows = {row["name"]: row for row in corpus["nodes"]}

    assert rows["four_square_odd_prime_modular_seed"]["statement_sha256"] == (
        "3e55824a272594c24c76d9044a4877bb3a75c10d101318dde5d6d928961bfeb2"
    )
    assert rows["four_square_non_two_prime_modular_seed"]["statement_sha256"] == (
        "79e165ce9e984729b5e131898679e59a04391124a61da10d3c9cb2e9339d691e"
    )
    assert rows["four_square_prime_modular_seed"]["statement_sha256"] == (
        "41b3138912bebce6b45a92e266f018ae7d5cae16d20c817ed20a8decbf14c833"
    )
    assert rows["four_square_prime_modular_seed"]["statement"].startswith("forall p.")
    assert rows["four_square_prime_modular_seed"]["admitted_to_alpha"] is False
    assert rows["four_square_prime_modular_seed"]["admitted_to_stable"] is False
    assert rows["four_square_prime_bounded_modular_seed"]["statement_sha256"] == (
        "664f15010c001437b0d990b4e1f81f845a0bc734a8fb5a3b31633ed463774077"
    )


def test_four_square_seed_discharge_retains_only_strict_descent(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, "four-squares")
    rows = {row["name"]: row for row in corpus["nodes"]}
    prime = rows["four_square_prime_from_strict_descent"]
    universal = rows["four_square_lagrange_from_strict_descent"]

    assert prime["statement_sha256"] == (
        "a0db9304ae96fb7094a9722321341b08818fdf0514b9534ec6a81b8340561809"
    )
    assert universal["statement_sha256"] == (
        "9f7dff900d6c44b4dc8eed887ea9b29811d79882645ba7d2264f60765c503dea"
    )
    assert "four_square_prime_modular_seed" in prime["dependencies"]
    assert "four_square_prime_from_strict_descent" in universal["dependencies"]
    assert " -> forall n." in universal["statement"]
    assert rows[
        "four_square_lagrange_from_bounded_strict_descent"
    ]["statement_sha256"] == (
        "1c950fd851415f84bc19ab5370d15465211e4cfcb280ae2594cef84bf5c47ed1"
    )


def test_four_square_surface_exposes_unconditional_even_halving(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    rows = {
        row["name"]: row for row in _corpus(files, "four-squares")["nodes"]
    }

    assert rows["four_square_parity_even_multiplier_halving"]["statement_sha256"] == (
        "1e4b5821869e0e29b9e3eaafa009705e18a94dbc4079a9ec37e4217e30e862c3"
    )
    assert rows["four_square_parity_represented_double_halving"]["statement_sha256"] == (
        "c5af9314d7cf3d665f914153f1a7e96176854a735ce7a7a82b4ae812125d12bc"
    )
    assert rows[
        "four_square_parity_represented_additive_double_halving"
    ]["statement_sha256"] == (
        "ceedc3db189c22bb6c0a7a6fc76fcebe7248e5de4dded044352ad9d1c7028c22"
    )
    assert rows[
        "four_square_parity_represented_additive_double_halving"
    ]["statement"].startswith("forall n.")


def test_four_square_surface_exposes_both_unconditional_quaternion_orientations(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    rows = {
        row["name"]: row for row in _corpus(files, "four-squares")["nodes"]
    }

    assert rows["four_square_conjugate_global_compensation"]["statement_sha256"] == (
        "01f9c0ae7ccb0eb485b27b2956ec2e1e531feed36a85963572bcee10b0c56c66"
    )
    assert rows["four_square_signed_conjugate_quaternion"]["statement_sha256"] == (
        "94bd014681b8c5d3e9505fed47fae5cd591da1fc2428217d55d590062880d7a3"
    )
    assert rows[
        "four_square_conjugate_absolute_coordinates_total"
    ]["statement_sha256"] == (
        "72e122dcb8c33e460a9e1e4829331deb9abfb18ca4e9e1bca9c2dac6f922b44c"
    )
    assert rows["four_square_signed_conjugate_negative_blocks"]["statement_sha256"] == (
        "4bbfc13207d91959aea04b77ab54eacb81c586954f4edd4f00045d5b1d98e258"
    )
    assert rows["four_square_signed_conjugate_positive_blocks"]["statement_sha256"] == (
        "6a03706d5246dd92b6b79d801db89fb44a839cc9f374c56d1eae081f8eb8671a"
    )
    assert rows["four_square_signed_conjugate_mixed_blocks"]["statement_sha256"] == (
        "a397c4c916e5cbf73d104a5172929602adccd7a2b229b2203d35a9014e006dbd"
    )
    assert rows[
        "four_square_signed_natural_negative_first_blocks"
    ]["statement_sha256"] == (
        "30f8f87ffcb55fd6256addc01195d5e190a15492af577027211bed79380f3f4f"
    )
    assert rows[
        "four_square_signed_natural_positive_first_blocks"
    ]["statement_sha256"] == (
        "ff332f2ab05eddd879d8e0665550add793fe35d246f278ec12af98fbe97da149"
    )
    assert rows["four_square_signed_centered_representation"]["statement_sha256"] == (
        "58bb112b380e2d614fb63e33d1cd2184abec50bbf6152278105c0796fe539da6"
    )
    assert sum(
        name.startswith("four_square_signed_orientation_mask_") for name in rows
    ) == 16


def test_lucas_surface_exposes_the_complete_unconditional_one_step_congruence(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, "lucas")
    rows = {row["name"]: row for row in corpus["nodes"]}

    assert rows["lucas_prime_shift_high_column"]["statement_sha256"] == (
        "7b1c762ed80e5f588398b877dc372628b6f143bf9aae4bd289a0988bbb8f6ea0"
    )
    assert rows["lucas_prime_block_digit_congruence"]["statement_sha256"] == (
        "fa40deb1530339b670f83de1cd151ea2d50e625cb9dbb931478e67405188aa81"
    )
    assert rows["lucas_one_step_division_congruence"]["statement_sha256"] == (
        "6869973f7b42c48c4a298a4716e19bc4949c5a6a0aae9e41ded9a110ac7be71e"
    )
    assert "lucas_prime_block_digit_congruence" in rows[
        "lucas_one_step_division_congruence"
    ]["dependencies"]
    assert rows["lucas_one_step_division_congruence"]["admitted_to_alpha"] is False
    assert rows["lucas_terminating_prime_digit_chain_exists"]["statement_sha256"] == (
        "e7519d8f5c7600546594ca5db83677d7bc01ab26d960fdb928e2707286df8e45"
    )
    assert rows["lucas_terminating_multidigit_theorem"]["statement_sha256"] == (
        "89c221df26cc91d9a6de17522d2abf137bb1c11601fddf3fe212ab19b6c4b395"
    )
    assert "lucas_one_step_division_congruence" in rows[
        "lucas_terminating_multidigit_theorem"
    ]["dependencies"]
    assert rows["lucas_theorem_for_length"]["statement_sha256"] == (
        "855e865592946ebe0bd8f0856edb73bc521c2db254a730ccc3e4851384d21ebb"
    )
    assert rows["lucas_theorem"]["statement_sha256"] == (
        "396e47df462c415ea6ea8e29c7506bfb1dc7077a96e768295b1949256d9b0564"
    )
    assert corpus["root_names"][-1] == "lucas_theorem"
    assert rows["lucas_theorem"]["statement"].startswith("forall p n k C.")
    assert rows["lucas_theorem"]["enrolled_in_alpha"] is True
    assert rows["lucas_theorem"]["alpha_evidence"] == "body_checked"
    assert rows["lucas_theorem"]["alpha_checked_use"] is False
    assert rows["lucas_theorem"]["alpha_campaign"] == "lucas"
    assert rows["lucas_theorem"]["status"] == generator.ALPHA_BODY_STATUS
    assert rows["lucas_theorem"]["admitted_to_alpha"] is False


def test_two_square_surface_identifies_the_complete_zero_inclusive_iff(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, "two-squares")
    endpoint = next(
        node
        for node in corpus["nodes"]
        if node["name"] == "two_square_iff_zero_or_even_three_mod_four_prime_valuations"
    )

    assert corpus["root_names"][-1] == endpoint["name"]
    assert endpoint["statement_sha256"] == (
        "4c39da833a313bab5ae810215dae5bbc9cc78ea951fe97fb177c36a5347cecd5"
    )
    assert "complete all-natural iff" in corpus["scope"]
    assert "enrolled in Alpha v15 as body_checked" in corpus["scope"]
    assert "without checked-use authority or Stable admission" in corpus["scope"]
    assert endpoint["enrolled_in_alpha"] is True
    assert endpoint["alpha_evidence"] == "body_checked"
    assert endpoint["alpha_admission_version"] == "v15"
    assert endpoint["alpha_campaign"] == "two_square"
    assert endpoint["alpha_checked_use"] is False
    assert endpoint["admitted_to_alpha"] is False
    assert endpoint["admitted_to_stable"] is False


def test_supplementary_explorer_includes_exact_euler_and_gauss_prerequisites(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, "supplementary-laws")
    rows = {node["name"]: node for node in corpus["nodes"]}

    for name in (
        "bounded_euler_criterion_complete",
        "bounded_gauss_lemma_complete",
        "quadratic_supplement_minus_one_complete",
        "quadratic_supplement_two_complete",
    ):
        assert rows[name]["enrolled_in_alpha"] is True
        assert rows[name]["alpha_evidence"] == "body_checked"
        assert rows[name]["alpha_campaign"] == "supplementary"
        assert rows[name]["alpha_admission_version"] == "v15"
        assert rows[name]["alpha_checked_use"] is False


def test_frontier_preserves_each_flagships_original_enrollment_release(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    roots = (
        ("four-squares", "four_square_lagrange", "v13"),
        ("lucas", "lucas_theorem", "v13"),
        ("kummer", "kummer_binomial_carry_bit_count", "v14"),
        ("kummer", "kummer_carry_free_iff_not_divides", "v14"),
        ("supplementary-laws", "quadratic_supplement_minus_one_complete", "v15"),
        ("supplementary-laws", "quadratic_supplement_two_complete", "v15"),
        (
            "two-squares",
            "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
            "v15",
        ),
    )

    for slug, name, version in roots:
        node = next(
            row for row in _corpus(files, slug)["nodes"] if row["name"] == name
        )
        assert node["alpha_edition_version"] == "v15"
        assert node["alpha_admission_version"] == version
        assert node["alpha_checked_use"] is False


def test_pythagorean_campaign_exposes_only_forward_and_conditional_proofs(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, "pythagorean-fermat-four")
    rows = {node["name"]: node for node in corpus["nodes"]}

    assert corpus["node_count"] == 44
    assert corpus["alpha_enrolled_node_count"] == 0
    assert "primitive inverse classification" in corpus["scope"]
    assert "Fermat strict-descent premise remain unproved" in corpus["scope"]
    assert "complete forward primitive Pythagorean constructor" in corpus["scope"]
    assert {
        "Pythagorean",
        "Coprime",
        "OppositeParity",
        "PrimitivePythagorean",
        "FermatFourCounterexample",
        "FermatFourStrictDescent",
    } <= {definition["name"] for definition in corpus["definitions"]}
    assert " -> " in rows["fermat_four_no_square_from_descent"]["statement"]
    assert " -> " in rows["fermat_four_no_fourth_from_descent"]["statement"]
    assert all(not node["enrolled_in_alpha"] for node in rows.values())
    assert {
        "peano_lab.library.pythagorean_fermat_four_candidate",
        "peano_lab.library.pythagorean_primitive_candidate",
    } == {node["source_module"] for node in rows.values()}
    assert 'data-input="m"' in files[
        "pythagorean-fermat-four/index.html"
    ].decode()
    assert "primitive inverse classification and Fermat strict descent remain open" in (
        files["assets/frontier.js"].decode()
    )


def test_curated_definitions_expand_to_unchanged_first_order_formulas(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    definitions: dict[str, dict[str, object]] = {}
    for slug in EXPECTED_FAMILIES:
        for definition in _corpus(files, slug)["definitions"]:
            definitions[definition["id"]] = definition

    assert {"Prime", "QRes", "Choose", "PowerValuation", "FloorSqrt"} <= {
        definition["name"] for definition in definitions.values()
    }
    assert {"SignedBalance", "SumTwoSquares", "AbsoluteDifference", "Carry", "Digit"} <= {
        definition["name"] for definition in definitions.values()
    }
    for definition in definitions.values():
        assert definition["template_sha256"] == sha256(
            definition["expanded_template"].encode()
        ).hexdigest()
        parse_formula_in_context(
            definition["expanded_template"], definition["parameters"]
        )


def test_interactive_reader_exposes_linked_notation_focus_zoom_and_print(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    javascript = files["assets/frontier.js"].decode()
    stylesheet = files["assets/frontier.css"].decode()

    assert "data-definition=" in javascript
    assert "Exact AST equivalence verified" in javascript
    assert "No unverified equivalence is claimed" in javascript
    assert "defined.defined_script_lines" in javascript
    assert "refreshVisibility" in javascript
    assert "setZoom" in javascript
    assert "window.print()" in javascript
    assert "@media print" in stylesheet
    assert ".frontier-definition-link" in stylesheet


def test_two_square_factory_discovery_includes_new_classification_when_present(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    modules = {
        node["source_module"] for node in _corpus(files, "two-squares")["nodes"]
    }

    assert "peano_lab.library.fermat_two_squares_prime_candidate" in modules
    classification = (
        REPO / "peano-lab" / "py" / "peano_lab" / "library"
        / "fermat_two_squares_classification_candidate.py"
    )
    if classification.is_file():
        assert "peano_lab.library.fermat_two_squares_classification_candidate" in modules
    standalone = classification.with_name("fermat_two_squares_brahmagupta_candidate.py")
    if standalone.is_file():
        assert "peano_lab.library.fermat_two_squares_brahmagupta_candidate" in modules
    valuation = classification.with_name("fermat_two_squares_valuation_candidate.py")
    if valuation.is_file():
        assert "peano_lab.library.fermat_two_squares_valuation_candidate" in modules
    factor_fold = classification.with_name("fermat_two_squares_factor_fold_candidate.py")
    if factor_fold.is_file():
        assert "peano_lab.library.fermat_two_squares_factor_fold_candidate" in modules


def test_lucas_factory_discovery_includes_new_multidigit_tranches_when_present(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    modules = {node["source_module"] for node in _corpus(files, "lucas")["nodes"]}
    library = REPO / "peano-lab" / "py" / "peano_lab" / "library"

    assert "peano_lab.library.lucas_digit_candidate" in modules
    for module in (
        "lucas_convolution_candidate",
        "lucas_block_digit_candidate",
        "lucas_low_digit_candidate",
        "lucas_multidigit_candidate",
    ):
        if (library / f"{module}.py").is_file():
            assert f"peano_lab.library.{module}" in modules


def test_two_square_example_exposes_the_zero_boundary_without_valuation_claim(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    page = files["two-squares/index.html"].decode()
    javascript = files["assets/frontier.js"].decode()

    assert 'data-input="n" type="number" min="0"' in page
    assert "if (n === 0) return" in javascript
    assert "prime valuations undefined" in javascript


def test_lucas_example_computes_the_entire_digitwise_binomial_product(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    page = files["lucas/index.html"].decode()
    javascript = files["assets/frontier.js"].decode()

    assert 'data-input="n" type="number" min="0"' in page
    assert 'data-input="k" type="number" min="0"' in page
    assert "function lucasDigitProduct(n, k, p)" in javascript
    assert "kd <= nd ? choose(nd, kd) : 0n" in javascript
    assert "Digit product=" in javascript
    assert "consult the proof map for the checked theorem boundary" in javascript


@pytest.mark.parametrize(
    ("prime", "upper", "lower"),
    ((2, 0, 0), (2, 42, 21), (3, 26, 8), (5, 7, 3), (5, 37, 13), (7, 100, 33)),
)
def test_lucas_browser_calculator_replays_actual_multidigit_examples(
    generated: tuple[dict[str, bytes], dict[str, object]],
    prime: int,
    upper: int,
    lower: int,
) -> None:
    files, _manifest = generated
    output = _browser_example(files, "lucas", {"p": prime, "n": upper, "k": lower})
    exact = comb(upper, lower)
    expected = 1
    digit_upper, digit_lower = upper, lower
    while digit_upper or digit_lower:
        upper_digit, lower_digit = digit_upper % prime, digit_lower % prime
        expected *= comb(upper_digit, lower_digit) if lower_digit <= upper_digit else 0
        digit_upper //= prime
        digit_lower //= prime

    assert f"C({upper},{lower})={exact} ≡ {exact % prime} (mod {prime})" in output
    assert f"Digit product={expected} ≡ {expected % prime} (mod {prime})" in output
    assert exact % prime == expected % prime


@pytest.mark.parametrize(
    ("first", "second", "coordinates", "primitive"),
    (
        (2, 1, (3, 4, 5), True),
        (3, 2, (5, 12, 13), True),
        (4, 1, (15, 8, 17), True),
        (4, 3, (7, 24, 25), True),
        (3, 1, (8, 6, 10), False),
        (6, 2, (32, 24, 40), False),
    ),
)
def test_pythagorean_browser_calculator_constructs_exact_euclidean_triples(
    generated: tuple[dict[str, bytes], dict[str, object]],
    first: int,
    second: int,
    coordinates: tuple[int, int, int],
    primitive: bool,
) -> None:
    files, _manifest = generated
    output = _browser_example(files, "pythagorean", {"m": first, "n": second})
    difference, doubled, hypotenuse = coordinates

    assert f"({difference}, {doubled}, {hypotenuse})" in output
    assert f"{difference}² + {doubled}² = {hypotenuse}²" in output
    assert difference * difference + doubled * doubled == hypotenuse * hypotenuse
    assert ("Coprime, opposite-parity parameters." in output) is primitive
    assert "primitive inverse classification and Fermat strict descent remain open" in output


@pytest.mark.parametrize(("first", "second"), ((1, 1), (4, 0), (2, 3)))
def test_pythagorean_browser_calculator_rejects_invalid_parameter_order(
    generated: tuple[dict[str, bytes], dict[str, object]], first: int, second: int
) -> None:
    files, _manifest = generated

    assert "Choose natural parameters with 0 < n < m." == _browser_example(
        files, "pythagorean", {"m": first, "n": second}
    )


def test_duplicate_factories_preserve_deterministic_first_source_and_provenance(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    family = next(item for item in generator.FAMILIES if item.slug == "two-squares")
    source = (
        "fermat_two_squares_classification_candidate",
        "make_fermat_two_squares_classification_candidate_theorems",
    )
    monkeypatch.setattr(generator, "_factory_sources", lambda _family: (source, source))

    rows = generator._family_nodes(family)

    assert rows
    assert all(len(row["sources"]) == 2 for row in rows)
    assert all(row["sources"][0]["selected"] is True for row in rows)
    assert all(row["sources"][1]["selected"] is False for row in rows)
    assert all(row["sources"][1]["matches_selected_statement"] for row in rows)


@pytest.mark.parametrize(
    "mutation",
    (
        "statement",
        "dependencies",
        "script",
        "closed_evidence",
        "pending_evidence",
        "missing_campaign",
    ),
)
def test_alpha_v15_frontier_evidence_and_identity_mutations_are_rejected(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    family = next(item for item in generator.FAMILIES if item.slug == "four-squares")
    root = "four_square_lagrange"
    alpha_entries = dict(v15.ALPHA_EDITION.by_name)
    entry = alpha_entries[root]
    message = "unexpected Alpha-v15 evidence"

    if mutation == "statement":
        entry = replace(entry, spec=replace(entry.spec, statement=entry.spec.statement + " "))
        message = "sealed Alpha-v15 entry"
    elif mutation == "dependencies":
        entry = replace(entry, spec=replace(entry.spec, dependencies=entry.spec.dependencies[:-1]))
        message = "sealed Alpha-v15 entry"
    elif mutation == "script":
        entry = replace(entry, spec=replace(entry.spec, script=entry.spec.script[:-1]))
        message = "sealed Alpha-v15 entry"
    elif mutation == "closed_evidence":
        entry = replace(entry, evidence=v13.EvidenceStatus.ALPHA_CLOSED)
    elif mutation == "pending_evidence":
        entry = replace(entry, evidence=v13.EvidenceStatus.PENDING_LAYERED_CLOSURE)
    else:
        campaigns = generator._alpha_frontier_campaigns()
        campaigns.pop(root)
        monkeypatch.setattr(
            generator,
            "_alpha_frontier_campaigns",
            lambda: campaigns,
        )
    alpha_entries[root] = entry
    monkeypatch.setattr(
        generator.v15,
        "ALPHA_EDITION",
        SimpleNamespace(by_name=alpha_entries),
    )

    with pytest.raises(ValueError, match=message):
        generator._family_nodes(family)


def test_frontier_generation_never_mutates_sealed_release_authority() -> None:
    before = (
        v12.ALPHA_V12_ENROLLMENT_SHA256,
        v12.ALPHA_V12_IDENTITY_SHA256,
        v12.STABLE_EDITION.identity_sha256,
        len(v12.ALPHA_CHECKED_SPECS),
        v13.ALPHA_V13_IDENTITY_SHA256,
        len(v13.ALPHA_CHECKED_SPECS),
        v14.ALPHA_V14_IDENTITY_SHA256,
        len(v14.ALPHA_CHECKED_SPECS),
        v15.ALPHA_V15_IDENTITY_SHA256,
        len(v15.ALPHA_CHECKED_SPECS),
    )

    generator.build_files()

    assert before == (
        v12.ALPHA_V12_ENROLLMENT_SHA256,
        v12.ALPHA_V12_IDENTITY_SHA256,
        v12.STABLE_EDITION.identity_sha256,
        len(v12.ALPHA_CHECKED_SPECS),
        v13.ALPHA_V13_IDENTITY_SHA256,
        len(v13.ALPHA_CHECKED_SPECS),
        v14.ALPHA_V14_IDENTITY_SHA256,
        len(v14.ALPHA_CHECKED_SPECS),
        v15.ALPHA_V15_IDENTITY_SHA256,
        len(v15.ALPHA_CHECKED_SPECS),
    )


def test_frontier_generator_check_detects_tampering_without_remote_assets(
    generated: tuple[dict[str, bytes], dict[str, object]], tmp_path: Path,
) -> None:
    files, _manifest = generated
    output = tmp_path / "frontier"
    generator._write(files, output)

    assert generator._check(files, output)
    (output / "lucas" / "index.html").write_text("tampered", encoding="utf-8")
    assert not generator._check(files, output)
    assert "http://" not in files["assets/frontier.js"].decode()
    assert "https://" not in files["assets/frontier.js"].decode()


def test_repository_proof_hub_labels_all_six_candidate_families() -> None:
    hub = (REPO / "deploy" / "proofs" / "index.html").read_text(encoding="utf-8")
    assert generator.CANDIDATE_STATUS in hub
    for slug in EXPECTED_FAMILIES:
        assert f'href="{slug}/"' in hub
    assert hub.count(
        "Alpha v13 enrolled · body_checked; no checked-use authority"
    ) == 2
    assert hub.count(
        "Alpha v14 enrolled · body_checked; no checked-use authority"
    ) == 1
    assert hub.count(
        "Alpha v15 enrolled · body_checked; no checked-use authority"
    ) == 2
    assert "Not enrolled in Alpha/Stable; Fermat descent remains conditional" in hub
    assert 'href="quadratic-reciprocity/"' in hub
    assert 'href="bertrand-postulate/"' in hub


@pytest.mark.parametrize("prime", (5, 13, 17, 29, 37, 41, 53))
def test_constructive_two_square_examples_have_actual_witnesses(prime: int) -> None:
    assert prime % 4 == 1
    assert any(
        first * first + second * second == prime
        for first in range(isqrt(prime) + 1)
        for second in range(isqrt(prime) + 1)
    )


@pytest.mark.parametrize(("prime", "left", "right"), ((2, 5, 3), (3, 8, 7), (5, 8, 7)))
def test_kummer_example_carries_equal_binomial_prime_valuation(
    prime: int, left: int, right: int,
) -> None:
    value = comb(left + right, left)
    valuation = 0
    while value % prime == 0:
        value //= prime
        valuation += 1

    carries = 0
    carry = 0
    while left or right or carry:
        next_carry = (left % prime + right % prime + carry) // prime
        carries += next_carry
        left //= prime
        right //= prime
        carry = next_carry

    assert carries == valuation
