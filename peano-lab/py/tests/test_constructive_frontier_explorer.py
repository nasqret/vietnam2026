"""Bounded audit of six offline, evidence-honest candidate proof explorers."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from html.parser import HTMLParser
import json
from math import comb, isqrt
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

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
from peano_lab.library import four_square_frontier_promotion as four_square_closure  # noqa: E402
from peano_lab.library import lucas_mixed_promotion as lucas_closure  # noqa: E402


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


@lru_cache(maxsize=1)
def _expected_experimental_campaigns() -> dict[str, set[str]]:
    """Count only actual named prior replays, never pending observations."""

    lucas = {
        *lucas_closure.LUCAS_CAMPAIGN_INITIAL_MICROBATCH,
        *lucas_closure.LUCAS_CAMPAIGN_SECOND_MICROBATCH,
        *lucas_closure.LUCAS_CAMPAIGN_THIRD_MICROBATCH,
        *lucas_closure.LUCAS_CAMPAIGN_FOURTH_MICROBATCH,
        *getattr(lucas_closure, "LUCAS_CAMPAIGN_SHARED_CHECKED_NAMES", ()),
    }
    four = {
        *(name for batch in four_square_closure.four_square_initial_campaign_batches() for name in batch.names),
        *four_square_closure.FOUR_SQUARE_CAMPAIGN_SECOND_LAYER_NAMES,
        *(
            name
            for name, _nodes, _objects in getattr(
                four_square_closure,
                "FOUR_SQUARE_CAMPAIGN_CONTINUATION_CHECKED_DIAGNOSTICS",
                (),
            )
        ),
    }
    return {"lucas": lucas, "four_square": four}


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
    assert manifest["experimental_closure_status"] == (
        generator.EXPERIMENTAL_CLOSURE_STATUS
    )
    assert manifest["experimental_closure_has_persisted_certificates"] is False
    assert manifest["experimental_closure_replayed_during_generation"] is False
    assert manifest["experimental_closure_grants_checked_use"] is False
    assert manifest["experimental_closure_grants_stable_membership"] is False
    assert manifest["admitted_to_alpha"] is False
    assert manifest["admitted_to_stable"] is False
    expected_detail_pages = sum(
        2 * int(row["node_count"]) + int(row["definition_count"])
        for row in manifest["families"]
    )
    # Original inventory + four byte-identical canonical assets + six graph APIs
    # + one exact and one defined page per theorem + one page per definition.
    assert manifest["file_count"] == len(files) == 44 + expected_detail_pages
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
    assert corpus["experimental_closure_status"] == (
        generator.EXPERIMENTAL_CLOSURE_STATUS
    )
    assert corpus["experimental_closed_visible_node_count"] == sum(
        node["experimental_closure_verified"] for node in nodes
    )
    assert corpus["experimental_closure_has_persisted_certificates"] is False
    assert corpus["experimental_closure_replayed_during_generation"] is False
    assert corpus["experimental_closure_grants_checked_use"] is False
    assert corpus["experimental_closure_grants_stable_membership"] is False
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
        assert node["experimental_closure_has_persisted_certificate"] is False
        if node["experimental_closure_verified"]:
            assert alpha_entry is not None
            assert node["alpha_evidence"] == "body_checked"
            assert node["alpha_checked_use"] is False
            assert node["alpha_admission_version"] == "v13"
            assert node["experimental_closure_campaign"] in {"lucas", "four_square"}
            assert isinstance(node["experimental_closure_microbatch"], str)
            assert node["experimental_closure_status"] == (
                generator.EXPERIMENTAL_CLOSURE_STATUS
            )
        else:
            assert node["experimental_closure_campaign"] is None
            assert node["experimental_closure_microbatch"] is None
            assert node["experimental_closure_status"] is None
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
        if edge["experimental_closure_verified"]:
            assert edge["experimental_closure_campaign"] in {"lucas", "four_square"}
            assert edge["experimental_closure_role"] in {"campaign", "parent"}
            assert alpha_entry is not None
            assert edge["alpha_evidence"] == "body_checked"
            assert edge["alpha_checked_use"] is False
        else:
            assert edge["experimental_closure_campaign"] is None
            assert edge["experimental_closure_role"] is None
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


def test_independent_experimental_progress_uses_only_checked_named_microbatches(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, manifest = generated
    expected = _expected_experimental_campaigns()
    campaigns = {
        item["campaign"]: item for item in manifest["experimental_closure_campaigns"]
    }

    assert set(campaigns) == {"lucas", "four_square"}
    assert set(campaigns["lucas"]["verified_campaign_names"]) == expected["lucas"]
    assert set(campaigns["four_square"]["verified_campaign_names"]) == (
        expected["four_square"]
    )
    assert campaigns["lucas"]["verified_campaign_row_count"] == 33
    assert campaigns["lucas"]["campaign_row_count"] == 44
    assert campaigns["lucas"]["verified_parent_row_count"] == 0
    assert campaigns["lucas"]["parent_progress_recorded"] is False
    assert campaigns["four_square"]["verified_campaign_row_count"] == 80
    assert campaigns["four_square"]["campaign_row_count"] == 196
    assert campaigns["four_square"]["verified_parent_row_count"] == 23
    assert campaigns["four_square"]["parent_row_count"] == 23
    assert campaigns["four_square"]["verified_obligation_row_count"] == 103
    assert campaigns["four_square"]["obligation_row_count"] == 219
    assert set(campaigns["four_square"]["verified_parent_names"]) == (
        set(four_square_closure.FOUR_SQUARE_NON_BETA_PARENT_NAMES)
        | set(four_square_closure.FOUR_SQUARE_BETA_PARENT_NAMES)
    )

    visible = {
        campaign: {
            node["name"]
            for slug in EXPECTED_FAMILIES
            for node in _corpus(files, slug)["nodes"]
            if node["experimental_closure_verified"]
            and node["experimental_closure_campaign"] == campaign
        }
        for campaign in campaigns
    }
    assert visible == expected
    assert manifest["experimental_closed_visible_node_count"] == 113
    assert all(
        campaign["status"] == generator.EXPERIMENTAL_CLOSURE_STATUS
        and campaign["source_alpha_edition_version"] == "v13"
        and campaign["source_alpha_edition_identity_sha256"]
        == v13.ALPHA_V13_IDENTITY_SHA256
        and campaign["flagship_experimentally_verified"] is False
        and campaign["has_persisted_certificates"] is False
        and campaign["replayed_during_generation"] is False
        and campaign["changes_alpha_evidence"] is False
        and campaign["grants_checked_use"] is False
        and campaign["grants_stable_membership"] is False
        and campaign["immutable_limits"]
        == {
            "max_microbatch_rows": 16,
            "max_proof_nodes": 125_000,
            "max_proof_objects": 25_000,
        }
        for campaign in campaigns.values()
    )


@pytest.mark.parametrize("slug", EXPECTED_FAMILIES)
def test_experimental_campaign_totals_remain_distinct_from_visible_nodes(
    generated: tuple[dict[str, bytes], dict[str, object]], slug: str,
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, slug)
    expected = _expected_experimental_campaigns()

    for campaign in corpus["experimental_closure_campaigns"]:
        visible_names = {
            node["name"]
            for node in corpus["nodes"]
            if node["experimental_closure_verified"]
            and node["experimental_closure_campaign"] == campaign["campaign"]
        }
        assert set(campaign["visible_node_names"]) == visible_names
        assert campaign["visible_node_count"] == len(visible_names)
        assert set(campaign["verified_campaign_names"]) == (
            expected[campaign["campaign"]]
        )
        assert campaign["verified_campaign_row_count"] >= len(visible_names)
        assert campaign["grants_checked_use"] is False
        assert campaign["grants_stable_membership"] is False

    if slug == "lucas":
        assert corpus["experimental_closed_visible_node_count"] == 33
    if slug == "four-squares":
        assert corpus["experimental_closed_visible_node_count"] < 80
        assert corpus["experimental_closure_campaigns"][0]["campaign"] == "four_square"
    if slug == "two-squares":
        assert corpus["experimental_closed_visible_node_count"] > 0
        assert corpus["experimental_closure_campaigns"][0]["campaign"] == "four_square"


def test_speculative_lucas_and_flagship_roots_never_gain_experimental_evidence(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    lucas = {node["name"]: node for node in _corpus(files, "lucas")["nodes"]}
    four = {node["name"]: node for node in _corpus(files, "four-squares")["nodes"]}

    for name in (
        "lucas_prime_row_interior_zero_mod",
        "lucas_prime_shift_below_base",
        "lucas_theorem",
    ):
        assert lucas[name]["experimental_closure_verified"] is False
        assert lucas[name]["alpha_evidence"] == "body_checked"
        assert lucas[name]["alpha_checked_use"] is False
    assert four["four_square_lagrange"]["experimental_closure_verified"] is False
    assert four["four_square_lagrange"]["alpha_checked_use"] is False


def test_experimental_overlay_surfaces_checked_parent_rows_without_admission(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    four = _corpus(files, "four-squares")
    checked_parents = {
        row["name"]
        for row in four["external_dependencies"]
        if row["experimental_closure_verified"]
        and row["experimental_closure_role"] == "parent"
    }

    assert checked_parents
    assert checked_parents <= (
        set(four_square_closure.FOUR_SQUARE_NON_BETA_PARENT_NAMES)
        | set(four_square_closure.FOUR_SQUARE_BETA_PARENT_NAMES)
    )
    for dependency in four["external_dependencies"]:
        if dependency["name"] not in checked_parents:
            continue
        assert dependency["alpha_evidence"] == "body_checked"
        assert dependency["alpha_checked_use"] is False
        assert dependency["admitted_to_alpha"] is False
        assert dependency["admitted_to_stable"] is False


@pytest.mark.parametrize(
    ("names", "message"),
    (
        ((), "nonempty"),
        (("lucas_theorem", "lucas_theorem"), "repeats"),
        (("four_square_lagrange",), "noncampaign"),
    ),
)
def test_experimental_named_batches_fail_closed_under_mutation(
    names: tuple[str, ...], message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        generator._verified_experimental_names(
            names,
            allowed={"lucas_theorem"},
            source="mutated experimental microbatch",
        )


@pytest.mark.parametrize(
    ("diagnostics", "message"),
    (
        ((), "incomplete"),
        ((("lucas_digit_chain_exists", 125_001, 1),), "limits"),
        ((("lucas_digit_chain_exists", 1, 25_001),), "limits"),
        ((("lucas_choose_prefix_extend", 1, 1),), "names differ"),
    ),
)
def test_experimental_diagnostics_fail_closed_under_mutation(
    diagnostics: tuple[tuple[str, int, int], ...], message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        generator._checked_experimental_diagnostics(
            diagnostics,
            expected_names=("lucas_digit_chain_exists",),
            source="mutated experimental diagnostics",
        )


def test_experimental_records_are_collapsed_and_graph_highlights_remain_honest(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    four = files["four-squares/explorer/defined/graph.html"].decode()
    lucas = files["lucas/explorer/defined/graph.html"].decode()
    two = files["two-squares/explorer/defined/graph.html"].decode()
    unrelated = files["kummer/explorer/defined/graph.html"].decode()
    script = files["assets/frontier.js"].decode()
    styles = files["assets/frontier.css"].decode()

    for slug in EXPECTED_FAMILIES:
        landing = files[f"{slug}/index.html"].decode()
        library = files[f"{slug}/explorer/defined/index.html"].decode()
        assert "frontier-experimental-heading" not in landing
        assert "frontier-experimental-heading" not in library
        assert "campaign · 80 / 196" not in landing
        assert "campaign · 33 / 44" not in landing

    assert "Lagrange four-square campaign · 80 / 196" in four
    assert "23 / 23" in four
    assert "103 / 219" in four
    assert "Lucas campaign · 33 / 44" in lucas
    assert "Lagrange four-square campaign · 80 / 196" in two
    assert "frontier-experimental-heading" not in unrelated
    for page in (four, lucas, two):
        assert '<details class="frontier-evidence-record">' in page
        assert "Historical experimental replay records" in page
        assert "Certificates are not persisted" in page
        assert "checked-use authority, and Stable membership remain unchanged" in page
        assert '"experimental_closure_verified":true' in page
    assert "Independent replay-verified experiment, not release evidence" in script
    assert "No certificate is persisted" in script
    assert ".frontier-experiment-verified rect" in styles


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
def test_family_landing_pages_restore_original_quadratic_reciprocity_format(
    generated: tuple[dict[str, bytes], dict[str, object]], slug: str,
) -> None:
    files, _manifest = generated
    page = files[f"{slug}/index.html"].decode()
    corpus = _corpus(files, slug)

    assert f'class="family-page {slug}-page"' in page
    assert '<header class="family-hero">' in page
    assert '<div class="shell">' in page
    assert '<nav class="crumbs">' in page
    assert '<p class="eyebrow">' in page
    assert '<p class="formula">' in page
    assert '<p class="lede">' in page
    assert '<div class="hero-actions">' in page
    assert '<main class="shell family-main">' in page
    assert '<section class="view-grid">' in page
    assert page.count('class="view-card') == 3
    assert '<section class="release-note">' in page
    revision = generator.CANONICAL_HTML_REVISION
    assert f'href="../assets/proofs.css?v={revision}"' in page
    assert f'href="explorer/defined/?v={revision}"' in page
    assert f'href="explorer/?v={revision}"' in page
    assert f'explorer/defined/graph.html?target={corpus["root_names"][-1]}' in page
    assert f'&amp;v={revision}' in page
    assert generator.CANDIDATE_STATUS in page
    assert "frontier-hero" not in page
    assert "<progress" not in page


@pytest.mark.parametrize("slug", EXPECTED_FAMILIES)
def test_definition_aware_libraries_restore_original_searchable_format(
    generated: tuple[dict[str, bytes], dict[str, object]], slug: str,
) -> None:
    files, _manifest = generated
    page = files[f"{slug}/explorer/defined/index.html"].decode()
    corpus = _corpus(files, slug)

    assert 'class="pa-defined-proof-site"' in page
    assert '<header class="pd-header pd-hero">' in page
    assert '<main data-defined-dashboard>' in page
    assert '<section class="pd-controls">' in page
    assert 'data-search type="search"' in page
    assert '<select data-kind>' in page
    assert '<button data-clear type="button">Clear</button>' in page
    assert '<output data-count>' in page
    assert '<section class="pd-results">' in page
    assert page.count('data-kind="theorem"') == corpus["node_count"]
    assert page.count('data-kind="definition"') == corpus["definition_count"]
    assert page.count('class="pd-result pd-result-definition"') == (
        corpus["definition_count"]
    )
    stylesheet_digest = sha256(files["assets/defined-explorer.css"]).hexdigest()[:12]
    script_digest = sha256(files["assets/defined-explorer.js"]).hexdigest()[:12]
    assert (
        f'href="../../../assets/defined-explorer.css?v={stylesheet_digest}"'
        in page
    )
    assert (
        f'src="../../../assets/defined-explorer.js?v={script_digest}"'
        in page
    )
    assert "conservative definition · not a theorem" in page
    assert "no checked-use authority" in page
    assert generator.CANDIDATE_STATUS in page
    family = next(row for row in generator.FAMILIES if row.slug == slug)
    tags = generator._theorem_tags(family, corpus)
    for definition in corpus["definitions"]:
        assert f'definition/{definition["id"]}.html' in page
    for node in corpus["nodes"]:
        assert f'tag/{tags[node["name"]]}.html' in page


@pytest.mark.parametrize("slug", EXPECTED_FAMILIES)
def test_family_proof_graphs_are_offline_interactive_and_candidate_labeled(
    generated: tuple[dict[str, bytes], dict[str, object]], slug: str,
) -> None:
    files, _manifest = generated
    page = files[f"{slug}/explorer/defined/graph.html"].decode()
    exact = files[f"{slug}/explorer/index.html"].decode()
    defined_css = sha256(files["assets/defined-explorer.css"]).hexdigest()[:12]
    defined_js = sha256(files["assets/defined-explorer.js"]).hexdigest()[:12]
    exact_css = sha256(files["assets/exact-explorer.css"]).hexdigest()[:12]
    exact_js = sha256(files["assets/exact-explorer.js"]).hexdigest()[:12]

    assert generator.CANDIDATE_STATUS in page
    assert 'class="pa-defined-proof-site"' in page
    assert '<header class="pd-header">' in page
    assert '<main class="pd-graph-page" data-defined-graph>' in page
    assert '<form class="pd-graph-controls" data-graph-form>' in page
    assert 'class="pd-graph-layout"' in page
    assert 'class="pd-graph-details"' in page
    assert 'data-graph-svg' in page
    assert 'data-graph-target' in page
    assert 'data-graph-view' in page
    assert 'data-graph-definitions' in page
    assert 'data-graph-edges' in page
    assert 'data-graph-zoom="in"' in page
    assert 'data-graph-zoom="out"' in page
    assert 'data-graph-fit' in page
    assert 'window.PA_DEFINED_GRAPH=' in page
    assert 'id="pa-defined-graph-data"' in page
    assert 'id="frontier-corpus" type="application/json"' in page
    assert 'data-example-form' in page
    assert f'href="../../../assets/defined-explorer.css?v={defined_css}"' in page
    assert f'src="../../../assets/defined-explorer.js?v={defined_js}"' in page
    assert 'class="frontier-main"' not in page
    assert 'class="frontier-graph-section"' not in page
    assert 'id="frontier-graph"' not in page
    assert 'class="pa-proof-site"' in exact
    assert '<header class="pa-proof-header pa-hero">' in exact
    assert '<main data-proof-dashboard data-pa-explorer-index>' in exact
    assert 'class="pa-proof-controls"' in exact
    assert 'class="pa-proof-results"' in exact
    assert f'href="../../assets/exact-explorer.css?v={exact_css}"' in exact
    assert f'src="../../assets/exact-explorer.js?v={exact_js}"' in exact
    assert 'class="pd-graph-page"' not in exact
    assert generator.CANDIDATE_STATUS in exact
    assert "http://" not in page
    assert "https://" not in page
    for root in REQUIRED_ROOTS[slug]:
        assert root in page


def test_canonical_explorer_assets_are_byte_identical_to_original_pa_interfaces(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated

    assert files["assets/defined-explorer.css"] == (
        generator.DEFINED_EXPLORER_STYLESHEET.read_bytes()
    )
    assert files["assets/defined-explorer.js"] == (
        generator.DEFINED_EXPLORER_SCRIPT.read_bytes()
    )
    assert files["assets/exact-explorer.css"] == (
        generator.EXACT_EXPLORER_STYLESHEET.read_bytes()
    )
    assert files["assets/exact-explorer.js"] == (
        generator.EXACT_EXPLORER_SCRIPT.read_bytes()
    )


@pytest.mark.parametrize(
    ("focus", "expected_href", "expected_label", "expected_title"),
    (
        (
            "PA0001",
            "tag/PA0001.html",
            "Open theorem →",
            "PA0001 · Fixture theorem",
        ),
        (
            "PD0001",
            "definition/PD0001.html",
            "Open definition →",
            "PD0001 · Fixture definition",
        ),
    ),
)
def test_canonical_graph_updates_sidebar_despite_getter_only_svg_href(
    focus: str,
    expected_href: str,
    expected_label: str,
    expected_title: str,
) -> None:
    """Run the actual shared graph against Firefox-style SVG anchor properties."""

    payload = {
        "nodes": [
            {
                "id": "PA0001",
                "kind": "theorem",
                "name": "Fixture theorem",
                "summary": "A theorem with an SVG graph link.",
                "href": "tag/PA0001.html",
                "layer": 0,
                "scope": "candidate",
            },
            {
                "id": "PD0001",
                "kind": "definition",
                "name": "Fixture definition",
                "summary": "A conservative definition.",
                "href": "definition/PD0001.html",
            },
        ],
        "edges": [],
        "proof_adjacency": {},
    }
    harness = (
        f"const payload = {json.dumps(payload)};\n"
        f"const selectedFocus = {json.dumps(focus)};\n"
        + r"""
const svgAnchors = [];

class Element {
  constructor(name, namespace = "html") {
    this.name = name;
    this.namespace = namespace;
    this.attributes = {};
    this.children = [];
    this.listeners = {};
    this.dataset = {};
    this.textContent = "";
    this.value = "";
    this.clientWidth = 960;
    this.clientHeight = 640;
    this.classList = {add() {}, remove() {}, contains() { return false; }};
    this.parentElement = {classList: this.classList};
    if (namespace === "svg" && name === "a") {
      Object.defineProperty(this, "href", {
        enumerable: true,
        get: () => ({baseVal: this.attributes.href || ""})
      });
      svgAnchors.push(this);
    }
  }

  get firstChild() { return this.children[0] || null; }

  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "data-graph-node") this.dataset.graphNode = String(value);
  }

  appendChild(child) {
    child.parentElement = this;
    this.children.push(child);
    return child;
  }

  removeChild(child) {
    this.children.splice(this.children.indexOf(child), 1);
    return child;
  }

  addEventListener(name, callback) { this.listeners[name] = callback; }
  focus() {}
}

const sidebarAnchor = new Element("a");
const svg = new Element("svg", "svg");
const title = new Element("h2");
const summary = new Element("p");
const selectors = new Map([
  ["[data-graph-summary]", summary],
  ["[data-graph-svg]", svg],
  ["[data-graph-target]", new Element("input")],
  ["[data-graph-view]", new Element("select")],
  ["[data-graph-definitions]", new Element("select")],
  ["[data-graph-edges]", new Element("select")],
  ["#pd-graph-theorems", new Element("datalist")],
  ["[data-graph-form]", new Element("form")],
  ["[data-graph-zoom='in']", new Element("button")],
  ["[data-graph-zoom='out']", new Element("button")],
  ["[data-graph-fit]", new Element("button")],
  ["[data-graph-title]", title],
  ["[data-graph-kind]", new Element("p")],
  ["[data-graph-description]", new Element("p")],
  ["[data-graph-metadata]", new Element("dl")],
  ["[data-graph-outgoing]", new Element("ul")],
  ["[data-graph-incoming]", new Element("ul")]
]);
const root = new Element("main");
root.querySelector = function (selector) {
  if (selector === "[data-graph-open]") {
    return svgAnchors[0] || sidebarAnchor;
  }
  if (selector === ".pd-graph-details [data-graph-open]") {
    return sidebarAnchor;
  }
  if (!selectors.has(selector)) throw new Error("Unexpected selector " + selector);
  return selectors.get(selector);
};

global.document = {
  readyState: "complete",
  body: {classList: {contains(name) { return name === "pa-defined-proof-site"; }}},
  createElement(name) { return new Element(name); },
  createElementNS(_namespace, name) { return new Element(name, "svg"); },
  createTextNode(value) { return {textContent: String(value)}; },
  getElementById() { return null; },
  querySelectorAll(selector) {
    return selector === "[data-defined-graph]" ? [root] : [];
  }
};
global.window = {
  PA_DEFINED_GRAPH: payload,
  location: {
    href: "https://proofs.example/graph.html?target=PA0001&focus=" + selectedFocus,
    hash: ""
  },
  history: {replaceState() {}},
  requestAnimationFrame(callback) { callback(); },
  addEventListener() {}
};
"""
        + generator.DEFINED_EXPLORER_SCRIPT.read_text()
        + r"""
const svgHref = Object.getOwnPropertyDescriptor(svgAnchors[0], "href");
process.stdout.write(JSON.stringify({
  sidebarHref: sidebarAnchor.attributes.href,
  sidebarLabel: sidebarAnchor.textContent,
  title: title.textContent,
  summary: summary.textContent,
  svgAnchorCount: svgAnchors.length,
  firstSvgHref: svgAnchors[0].href.baseVal,
  svgHrefIsGetterOnly: typeof svgHref.get === "function" && svgHref.set === undefined,
  viewportRendered: svg.attributes.viewBox !== undefined
}));
"""
    )
    result = json.loads(
        subprocess.run(
            ["node", "-e", harness], check=True, text=True, capture_output=True
        ).stdout
    )

    assert result["sidebarHref"] == expected_href
    assert result["sidebarLabel"] == expected_label
    assert result["title"] == expected_title
    assert result["summary"].startswith("1 theorem nodes ·")
    assert result["svgAnchorCount"] >= 1
    assert result["firstSvgHref"] == "tag/PA0001.html"
    assert result["svgHrefIsGetterOnly"] is True
    assert result["viewportRendered"] is True


def test_every_generated_document_navigation_bypasses_proxy_html_caches(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated

    class NavigationCollector(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.links: list[str] = []

        def handle_starttag(
            self, tag: str, attrs: list[tuple[str, str | None]]
        ) -> None:
            if tag != "a":
                return
            attributes = dict(attrs)
            href = attributes.get("href")
            if href is not None:
                self.links.append(href)

    inspected = 0
    for path, payload in files.items():
        if not path.endswith(".html"):
            continue
        parser = NavigationCollector()
        parser.feed(payload.decode())
        for href in parser.links:
            if href.startswith("#"):
                continue
            assert parse_qs(urlsplit(href).query).get("v") == [
                generator.CANONICAL_HTML_REVISION
            ], f"stale cache key for {path}: {href}"
            inspected += 1

    assert inspected > 8_000


@pytest.mark.parametrize("slug", EXPECTED_FAMILIES)
def test_canonical_graphs_distinguish_actual_proof_and_definition_edges(
    generated: tuple[dict[str, bytes], dict[str, object]], slug: str,
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, slug)
    family = next(row for row in generator.FAMILIES if row.slug == slug)
    tags = generator._theorem_tags(family, corpus)
    graph = json.loads(files[f"{slug}/explorer/defined/api/graph.json"])

    assert graph["path_policy"] == "proof_dependency_edges_only"
    assert graph["theorem_count"] == corpus["node_count"]
    assert graph["definition_count"] == corpus["definition_count"]
    assert graph["external_dependency_count"] == corpus["external_dependency_count"]
    assert graph["root_name"] == corpus["root_names"][-1]
    assert graph["root_tag"] == tags[graph["root_name"]]
    graph_nodes = {node["id"]: node for node in graph["nodes"]}
    assert set(graph_nodes) == {
        *tags.values(),
        *(definition["id"] for definition in corpus["definitions"]),
    }
    for node in corpus["nodes"]:
        rendered = graph_nodes[tags[node["name"]]]
        assert rendered["kind"] == "theorem"
        assert rendered["scope"] == "candidate"
        assert rendered["alpha_checked_use"] is False
        assert rendered["href"] == (
            f'tag/{tags[node["name"]]}.html?v={generator.CANONICAL_HTML_REVISION}'
        )
        path = graph["proof_adjacency"][rendered["id"]]["critical_root_path"]
        assert path[-1] == rendered["id"]
        assert rendered["layer"] == len(path) - 1
    assert {
        (edge["source"], edge["target"])
        for edge in graph["edges"]
        if edge["kind"] == "proof_dependency"
    } == {
        (tags[edge["source"]], tags[edge["target"]])
        for edge in corpus["edges"]
        if edge["source"] in tags and edge["target"] in tags
    }
    assert {
        (edge["source"], edge["target"])
        for edge in graph["edges"]
        if edge["kind"] == "uses_definition"
    } == {
        (tags[node["name"]], identifier)
        for node in corpus["nodes"]
        for identifier in node["defined"]["definition_uses"]
    }


@pytest.mark.parametrize("slug", EXPECTED_FAMILIES)
def test_every_frontier_theorem_and_definition_has_a_real_canonical_detail_page(
    generated: tuple[dict[str, bytes], dict[str, object]], slug: str,
) -> None:
    files, _manifest = generated
    corpus = _corpus(files, slug)
    family = next(row for row in generator.FAMILIES if row.slug == slug)
    tags = generator._theorem_tags(family, corpus)

    for node in corpus["nodes"]:
        tag = tags[node["name"]]
        defined = files[f"{slug}/explorer/defined/tag/{tag}.html"].decode()
        exact = files[f"{slug}/explorer/tag/{tag}.html"].decode()
        assert 'class="pa-defined-proof-site"' in defined
        assert 'class="pd-theorem-layout"' in defined
        assert 'class="pd-formal-proof"' in defined
        assert node["statement_sha256"] in defined
        assert (
            f'href="../../tag/{tag}.html?v={generator.CANONICAL_HTML_REVISION}"'
            in defined
        )
        assert node["status"] in defined
        assert "window.PA_DEFINED_GRAPH=" not in defined
        assert 'class="pa-proof-site"' in exact
        assert 'class="pa-theorem-layout"' in exact
        assert 'class="pa-formal-proof"' in exact
        assert node["statement_sha256"] in exact
        assert (
            f'href="../defined/tag/{tag}.html?v={generator.CANONICAL_HTML_REVISION}"'
            in exact
        )
        assert "no checked-use authority" in exact
        assert "window.PA_DEFINED_GRAPH=" not in exact
        for identifier in node["defined"]["definition_uses"]:
            assert f'../definition/{identifier}.html' in defined

    for definition in corpus["definitions"]:
        identifier = definition["id"]
        page = files[
            f"{slug}/explorer/defined/definition/{identifier}.html"
        ].decode()
        assert 'class="pa-defined-proof-site"' in page
        assert 'class="pd-definition-page"' in page
        assert definition["name"] in page
        assert definition["template_sha256"] in page
        assert "conservative notation, not a theorem" in page
        assert "window.PA_DEFINED_GRAPH=" not in page


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
        "pythagorean-fermat-four/explorer/defined/graph.html"
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
    assert 'document.querySelector("[data-defined-dashboard]")' in javascript
    assert "refreshLibrary" in javascript
    assert 'parameters.get("target")' in javascript
    assert 'parameters.get("view") === "prerequisites"' in javascript
    assert 'dataset.frontierNotation === "exact"' in javascript
    assert "@media print" in stylesheet
    assert ".frontier-definition-link" in stylesheet
    assert "body.pa-defined-proof-site .pd-header" in stylesheet
    assert "body.pa-defined-proof-site .pd-controls" in stylesheet


def test_defined_library_filters_work_without_an_embedded_graph_corpus(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    harness = r"""
const listeners = {};
const input = {value:"",focused:false,addEventListener(_event,callback){listeners.search=callback},focus(){this.focused=true}};
const kind = {value:"all",addEventListener(_event,callback){listeners.kind=callback}};
const clear = {addEventListener(_event,callback){listeners.clear=callback}};
const count = {textContent:"3 entries"};
const entries = [
  {dataset:{search:"prime classification theorem",kind:"theorem"},hidden:false},
  {dataset:{search:"prime conservative definition",kind:"definition"},hidden:false},
  {dataset:{search:"lucas digit theorem",kind:"theorem"},hidden:false}
];
const dashboard = {
  querySelector(selector){return ({"[data-search]":input,"[data-kind]":kind,"[data-clear]":clear,"[data-count]":count})[selector]},
  querySelectorAll(){return entries}
};
global.document={querySelector(selector){return selector==="[data-defined-dashboard]"?dashboard:null},getElementById(){return null}};
global.window={};
""" + files["assets/frontier.js"].decode() + r"""
input.value="prime";listeners.search();
const searched={visible:entries.filter(entry=>!entry.hidden).length,count:count.textContent};
kind.value="definition";listeners.kind();
const filtered={visible:entries.filter(entry=>!entry.hidden).map(entry=>entry.dataset.kind),count:count.textContent};
listeners.clear();
process.stdout.write(JSON.stringify({searched,filtered,cleared:{visible:entries.filter(entry=>!entry.hidden).length,count:count.textContent,input:input.value,kind:kind.value,focused:input.focused}}));
"""
    result = json.loads(
        subprocess.run(
            ["node", "-e", harness], check=True, text=True, capture_output=True
        ).stdout
    )

    assert result == {
        "searched": {"visible": 2, "count": "2 entries"},
        "filtered": {"visible": ["definition"], "count": "1 entry"},
        "cleared": {
            "visible": 3,
            "count": "3 entries",
            "input": "",
            "kind": "all",
            "focused": True,
        },
    }


def test_graph_deep_links_honor_requested_target_focus_and_exact_edition(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated

    def node(name: str) -> dict[str, object]:
        return {
            "name": name,
            "summary": f"Summary of {name}",
            "statement": "0 = 0",
            "statement_sha256": "0" * 64,
            "status": generator.ALPHA_BODY_STATUS,
            "source_module": "peano_lab.library.fixture",
            "dependencies": [],
            "sources": [],
            "script": [],
            "experimental_closure_verified": False,
            "defined": {
                "defined_statement": "0 = 0",
                "statement_parts": [{"kind": "text", "text": "0 = 0"}],
                "defined_script_lines": [],
                "definition_uses": {},
                "statement_receipt": None,
                "statement_status": "exact-only-fixture",
            },
        }

    corpus = json.dumps(
        {
            "nodes": [node("default_root"), node("requested_theorem")],
            "external_dependencies": [],
            "definitions": [],
            "edges": [],
            "root_names": ["default_root"],
        }
    )
    harness = f"const corpus={corpus};\n" + r"""
const detail={innerHTML:"",querySelectorAll(){return []}};
const focus={pressed:"false",setAttribute(_name,value){this.pressed=value},addEventListener(){}};
global.document={
  body:{dataset:{frontierNotation:"exact"}},
  getElementById(id){return id==="frontier-corpus"?{textContent:JSON.stringify(corpus)}:id==="frontier-detail"?detail:id==="frontier-focus"?focus:null},
  querySelector(){return null},
  querySelectorAll(){return []}
};
global.window={location:{search:"?target=requested_theorem&view=prerequisites",hash:""},print(){}};
""" + files["assets/frontier.js"].decode() + r"""
process.stdout.write(JSON.stringify({selected:detail.innerHTML.includes("<h2>requested_theorem</h2>"),exact:detail.innerHTML.includes("Exact expanded first-order HA statement"),focused:focus.pressed}));
"""
    result = json.loads(
        subprocess.run(
            ["node", "-e", harness], check=True, text=True, capture_output=True
        ).stdout
    )

    assert result == {"selected": True, "exact": True, "focused": "true"}


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
    page = files["two-squares/explorer/defined/graph.html"].decode()
    javascript = files["assets/frontier.js"].decode()

    assert 'data-input="n" type="number" min="0"' in page
    assert "if (n === 0) return" in javascript
    assert "prime valuations undefined" in javascript


def test_lucas_example_computes_the_entire_digitwise_binomial_product(
    generated: tuple[dict[str, bytes], dict[str, object]],
) -> None:
    files, _manifest = generated
    page = files["lucas/explorer/defined/graph.html"].decode()
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
        assert f'href="{slug}/?v={generator.CANONICAL_HTML_REVISION}"' in hub
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
    assert "Independent replay experiment:" not in hub
    assert "80/196" not in hub
    assert "33/44" not in hub
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
