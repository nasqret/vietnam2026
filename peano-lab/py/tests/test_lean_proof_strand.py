"""Bounded, adversarial coverage for source-grounded modular proof strands."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import re
from types import SimpleNamespace

import pytest

from peano_lab.library import (
    editions_v18,
    editions_v19,
    editions_v20,
    editions_v23,
    editions_v24,
    editions_v25,
    editions_v26,
    editions_v27,
    editions_v28,
)
from peano_lab.library.alpha_enrollment_v27 import ROOT_STATEMENT_SHA256
from peano_lab.library.defined_syntax import DEFINITIONS_BY_NAME
from peano_lab.library.lean_presentation import _NOTATION_CODE
from peano_lab.library.lean_proof_reconstruction import LeanProofReconstruction
from peano_lab.library.lean_proof_strand import (
    ProofStrandError,
    ProofStrandLimitError,
    ProofStrandPlan,
    build_proof_strand,
    plan_proof_strand,
    preview_proof_strand,
    readable_strand_formula,
)
from peano_lab.library.theorems import TheoremSpec, _closed_formula


@pytest.fixture(scope="module")
def addition_plan() -> ProofStrandPlan:
    return plan_proof_strand("add_comm")


@pytest.fixture(scope="module")
def addition_package(addition_plan: ProofStrandPlan):
    return build_proof_strand(addition_plan)


def test_addition_strand_is_exact_dependency_topological(
    addition_plan: ProofStrandPlan,
) -> None:
    assert tuple(node.name for node in addition_plan.nodes) == (
        "zero_add",
        "add_succ_left",
        "add_comm",
    )
    assert addition_plan.root == "add_comm"
    assert addition_plan.root_node.name == "add_comm"
    assert addition_plan.edition == "stable"
    assert addition_plan.node_count == 3
    assert addition_plan.edge_count == 2
    assert addition_plan.maximum_depth == 1
    assert addition_plan.total_script_lines == 11


def test_planning_never_replays_stable_or_alpha_theorems(monkeypatch) -> None:
    from peano_lab.library import theorems

    def forbidden(*args, **kwargs):
        raise AssertionError("metadata planning must never replay a theorem")

    monkeypatch.setattr(theorems, "replay", forbidden)
    monkeypatch.setattr(editions_v18, "replay", forbidden)
    monkeypatch.setattr(editions_v19, "replay", forbidden)
    monkeypatch.setattr(editions_v20, "replay", forbidden)
    monkeypatch.setattr(editions_v23, "replay", forbidden)
    monkeypatch.setattr(editions_v24, "replay", forbidden)
    monkeypatch.setattr(editions_v25, "replay", forbidden)
    monkeypatch.setattr(editions_v26, "replay", forbidden)
    monkeypatch.setattr(editions_v27, "replay", forbidden)
    monkeypatch.setattr(editions_v28, "replay", forbidden)
    assert plan_proof_strand("add_comm").node_count == 3
    alpha = plan_proof_strand(
        "distinct_primes_left_not_divide_right",
        edition="alpha",
    )
    assert alpha.edition_version == "v28"
    assert alpha.root_node.evidence == "alpha_closed"


def test_alpha_and_stable_names_have_distinct_plan_identities(
    addition_plan: ProofStrandPlan,
) -> None:
    alpha = plan_proof_strand("add_comm", edition="alpha")
    assert alpha.identity_sha256 != addition_plan.identity_sha256
    assert alpha.edition_identity_sha256 != addition_plan.edition_identity_sha256


@pytest.mark.parametrize(
    "name",
    (
        "Even",
        "IsGCD",
        "DivRem",
        "Sum",
        "Pow",
        "Factorial",
        "BoundedQRes",
        "DivisionPrefix",
    ),
)
def test_all_forty_definition_registry_notations_are_available(name: str) -> None:
    definition = DEFINITIONS_BY_NAME[name]
    source = (
        "forall "
        + " ".join(definition.parameters)
        + ". "
        + definition.template_source
    )
    formula = _closed_formula(source)
    readable = readable_strand_formula(formula, source_statement=source)
    assert f"{name} " in readable


def test_readable_formula_rejects_changed_source_statement() -> None:
    formula = _closed_formula("forall n. n = n")
    with pytest.raises(ProofStrandError, match="differs"):
        readable_strand_formula(formula, source_statement="forall n. n = 0")


def test_readable_formula_rejects_open_source_statement() -> None:
    formula = _closed_formula("forall n. n = n")
    with pytest.raises(ProofStrandError, match="differs|closed"):
        readable_strand_formula(formula, source_statement="n = n")


@pytest.mark.parametrize("name", ("../bad", "_", "bad name", "x; axiom boom"))
def test_unsafe_root_names_are_rejected(name: str) -> None:
    with pytest.raises(ProofStrandError, match="safe theorem name"):
        plan_proof_strand(name)


@pytest.mark.parametrize("edition", ("v18", "Alpha", "body_checked", 1, None))
def test_unknown_edition_cannot_grant_authority(edition: object) -> None:
    with pytest.raises(ProofStrandError, match="edition"):
        plan_proof_strand("add_comm", edition=edition)  # type: ignore[arg-type]


def test_alpha_only_theorem_is_not_in_stable() -> None:
    with pytest.raises(ProofStrandError, match="unknown stable"):
        plan_proof_strand("distinct_primes_left_not_divide_right")


def test_body_checked_alpha_entry_cannot_be_used(monkeypatch) -> None:
    from peano_lab.library import lean_proof_strand

    closed = editions_v19.ALPHA_EDITION.by_name[editions_v19.RESIDUAL_PROMOTED_NAMES[0]]
    body_only = replace(closed, evidence=editions_v19.EvidenceStatus.BODY_CHECKED)
    view = SimpleNamespace(by_name={body_only.spec.name: body_only})
    monkeypatch.setattr(lean_proof_strand, "_edition_view", lambda edition: (view, "v19"))
    with pytest.raises(ProofStrandError, match="checked-use authority"):
        plan_proof_strand(body_only.spec.name, edition="alpha")


def test_historically_body_only_theorem_is_now_checked_in_current_alpha() -> None:
    name = editions_v19.RESIDUAL_PROMOTED_NAMES[0]
    assert not editions_v18.ALPHA_EDITION.by_name[name].checked_use
    plan = plan_proof_strand(name, edition="alpha")
    assert plan.edition_version == "v28"
    assert plan.root_node.evidence == "alpha_closed"
    assert plan.root_node.name == name


def test_new_v19_frontier_theorem_has_metadata_only_checked_strand(
    monkeypatch,
) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("new Alpha-v19 proof strand must never load proof artifacts")

    monkeypatch.setattr(editions_v19, "replay", forbidden)
    name = min(
        editions_v19.FRONTIER_NEW_NAMES,
        key=lambda item: (
            editions_v19.ALPHA_EDITION.dependency_depth_by_name[item],
            len(editions_v19.ALPHA_EDITION.by_name[item].spec.dependencies),
            item,
        ),
    )
    assert name not in editions_v18.ALPHA_EDITION.by_name
    plan = plan_proof_strand(name, edition="alpha")
    assert plan.edition_version == "v28"
    assert plan.root_node.name == name
    assert plan.root_node.evidence == "alpha_closed"


def test_new_v20_frontier_theorem_has_metadata_only_checked_strand(monkeypatch) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("new Alpha-v20 proof planning must never load proof artifacts")

    monkeypatch.setattr(editions_v20, "replay", forbidden)
    monkeypatch.setattr(editions_v20, "checked_next_layer_bundle", forbidden)
    monkeypatch.setattr(editions_v23, "replay", forbidden)
    monkeypatch.setattr(editions_v23, "checked_milestone_closure_bundle", forbidden)
    monkeypatch.setattr(editions_v24, "replay", forbidden)
    monkeypatch.setattr(editions_v24, "checked_research_layer_bundle", forbidden)
    monkeypatch.setattr(editions_v25, "replay", forbidden)
    monkeypatch.setattr(editions_v26, "replay", forbidden)
    monkeypatch.setattr(editions_v25, "checked_breakthrough_layer_bundle", forbidden)
    monkeypatch.setattr(editions_v26, "checked_first_wave_bundle", forbidden)
    monkeypatch.setattr(editions_v27, "replay", forbidden)
    monkeypatch.setattr(editions_v28, "replay", forbidden)
    monkeypatch.setattr(editions_v27, "checked_second_wave_bundle", forbidden)
    monkeypatch.setattr(editions_v28, "checked_lower_layer_bundle", forbidden)
    name = "signed_matrix_two_determinant_exists"
    assert name not in editions_v19.ALPHA_EDITION.by_name
    plan = plan_proof_strand(name, edition="alpha")
    assert plan.edition_version == "v28"
    assert plan.root_node.name == name
    assert plan.root_node.evidence == "alpha_closed"


@pytest.mark.parametrize(
    "name",
    (
        "euclidean_two_step_halving",
        "binary_modular_exponentiation_result_exists_unique",
        "binary_length_exists_unique",
        "euclidean_anchored_execution_linear_bound",
        "binary_modular_execution_result_exists_unique",
        "euclidean_gcd_execution_logarithmic_exists",
        "binary_exponent_digit_prefix_exists",
        "binary_modular_execution_logarithmic_bound",
        "infinitely_many_primes_three_mod_four",
        "beta_signed_matrix_minor_exists",
        "signed_matrix_four_full_determinant_exists",
        "beta_horner_derivative_exists_unique",
        "crt_prefix_lcm_exists_unique",
        "crt_pairwise_coprime_prefix_canonical_exists_unique",
        "signed_matrix_cofactor_family_and_fold_exists",
        "beta_horner_hensel_lift_exists",
        "crt_merge_compatible_prefix_canonical_exists_unique",
        "crt_pairwise_compatible_dominating_last_canonical_exists_unique",
        "coprime_square_product_factors",
        "square_divides_square_root",
        "pythagorean_positive_primitive_classification",
        "fermat_four_complete_classification",
        "fermat_four_positive_sum_not_square",
        *ROOT_STATEMENT_SHA256,
    ),
)
def test_v27_and_historical_frontier_theorems_have_metadata_only_checked_strands(
    monkeypatch, name: str
) -> None:
    def forbidden(*args, **kwargs):
        raise AssertionError("new Alpha-v27 proof planning must never load proof artifacts")

    monkeypatch.setattr(editions_v23, "replay", forbidden)
    monkeypatch.setattr(editions_v23, "checked_milestone_closure_bundle", forbidden)
    monkeypatch.setattr(editions_v24, "replay", forbidden)
    monkeypatch.setattr(editions_v24, "checked_research_layer_bundle", forbidden)
    monkeypatch.setattr(editions_v25, "replay", forbidden)
    monkeypatch.setattr(editions_v26, "replay", forbidden)
    monkeypatch.setattr(editions_v25, "checked_breakthrough_layer_bundle", forbidden)
    monkeypatch.setattr(editions_v26, "checked_first_wave_bundle", forbidden)
    monkeypatch.setattr(editions_v27, "replay", forbidden)
    monkeypatch.setattr(editions_v28, "replay", forbidden)
    monkeypatch.setattr(editions_v27, "checked_second_wave_bundle", forbidden)
    monkeypatch.setattr(editions_v28, "checked_lower_layer_bundle", forbidden)
    assert name not in editions_v20.ALPHA_EDITION.by_name
    plan = plan_proof_strand(name, edition="alpha")
    assert plan.edition_version == "v28"
    assert plan.root_node.name == name
    assert plan.root_node.evidence == "alpha_closed"


def test_unsealed_alpha_cannot_authorize_a_strand_and_does_not_block_stable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from peano_lab.library import lean_proof_strand

    monkeypatch.setattr(editions_v28, "EXPECTED_ALPHA_V28_COUNT", 0)
    with pytest.raises(ProofStrandError, match="not sealed for checked use"):
        lean_proof_strand._edition_view("alpha")
    stable, version = lean_proof_strand._edition_view("stable")
    assert stable is editions_v26.STABLE_EDITION
    assert len(stable.entries) == 432
    assert version == "stable"


def test_node_budget_stops_before_provenance_or_proof_loading(monkeypatch) -> None:
    from peano_lab.library import lean_proof_strand

    def forbidden(*args, **kwargs):
        raise AssertionError("large strands must stop before source or proof access")

    monkeypatch.setattr(lean_proof_strand, "_source_identity", forbidden)
    with pytest.raises(ProofStrandLimitError, match="32-theorem"):
        plan_proof_strand(
            "quadratic_reciprocity_combined",
            edition="alpha",
            max_nodes=32,
        )


def test_edge_budget_is_enforced_before_materialization() -> None:
    with pytest.raises(ProofStrandLimitError, match="1-edge"):
        plan_proof_strand("add_comm", max_edges=1)


def test_depth_budget_is_enforced_before_materialization() -> None:
    with pytest.raises(ProofStrandLimitError, match="1-layer"):
        plan_proof_strand("fundamental_theorem_of_arithmetic", max_depth=1)


@pytest.mark.parametrize(
    "option,value",
    (
        ("max_nodes", 0),
        ("max_nodes", True),
        ("max_edges", -1),
        ("max_depth", 257),
    ),
)
def test_impossible_policy_limits_are_rejected(option: str, value: object) -> None:
    with pytest.raises(ProofStrandError, match="integer"):
        plan_proof_strand("add_comm", **{option: value})  # type: ignore[arg-type]


def test_cycle_in_tampered_inventory_is_rejected(monkeypatch) -> None:
    from peano_lab.library import lean_proof_strand

    original = editions_v18.STABLE_EDITION.by_name["zero_add"]
    cyclic = replace(original, spec=replace(original.spec, dependencies=("zero_add",)))
    view = SimpleNamespace(
        by_name={"zero_add": cyclic},
        dependency_depth_by_name={"zero_add": 0},
        identity_sha256="0" * 64,
    )
    monkeypatch.setattr(lean_proof_strand, "_edition_view", lambda edition: (view, "stable"))
    with pytest.raises(ProofStrandError, match="cycle"):
        plan_proof_strand("zero_add")


def test_unchecked_dependency_in_tampered_inventory_is_rejected(monkeypatch) -> None:
    from peano_lab.library import lean_proof_strand

    root = editions_v18.STABLE_EDITION.by_name["add_comm"]
    first = replace(
        editions_v18.STABLE_EDITION.by_name["zero_add"],
        evidence=editions_v18.EvidenceStatus.BODY_CHECKED,
    )
    second = editions_v18.STABLE_EDITION.by_name["add_succ_left"]
    view = SimpleNamespace(
        by_name={item.spec.name: item for item in (root, first, second)},
        dependency_depth_by_name={"add_comm": 1, "zero_add": 0, "add_succ_left": 0},
        identity_sha256="0" * 64,
    )
    monkeypatch.setattr(lean_proof_strand, "_edition_view", lambda edition: (view, "stable"))
    with pytest.raises(ProofStrandError, match="no checked-use authority"):
        plan_proof_strand("add_comm")


def test_source_path_traversal_is_rejected() -> None:
    from peano_lab.library.lean_proof_strand import _source_identity

    with pytest.raises(ProofStrandError, match="canonical|approved"):
        _source_identity("peano-lab/py/peano_lab/library/../kernel/checker.py")


def test_source_provenance_supports_flattened_pyodide_mount(
    monkeypatch,
    tmp_path,
) -> None:
    from peano_lab.library import lean_proof_strand

    mounted_library = tmp_path / "lab" / "peano_lab" / "library"
    mounted_library.mkdir(parents=True)
    source = mounted_library / "mounted_proof_example.py"
    source.write_text("# browser-mounted immutable proof source\n", encoding="utf-8")
    monkeypatch.setattr(lean_proof_strand, "_LIBRARY", mounted_library)
    canonical = "peano-lab/py/peano_lab/library/mounted_proof_example.py"
    actual_path, actual_digest = lean_proof_strand._source_identity(canonical)
    assert actual_path == canonical
    assert actual_digest == sha256(source.read_bytes()).hexdigest()


def test_node_source_and_specification_are_content_bound(
    addition_plan: ProofStrandPlan,
) -> None:
    root = addition_plan.root_node
    assert root.source_path == "peano-lab/py/peano_lab/library/theorems.py"
    assert len(root.source_sha256) == 64
    assert len(root.specification_sha256) == 64
    assert root.aliases == ()


def test_preview_is_honest_bounded_and_replay_free(
    addition_plan: ProofStrandPlan,
) -> None:
    preview = preview_proof_strand(addition_plan, max_bytes=6_144, max_rows=2)
    assert len(preview.encode("utf-8")) <= 6_144
    assert "Lean verification: NOT RUN" in preview
    assert "Proof-body replay: NOT RUN" in preview
    assert "zero_add" in preview
    assert "add_comm" in preview
    assert "intermediate theorem(s) omitted" in preview


def test_preview_keeps_complete_authority_footer_when_truncated(
    addition_plan: ProofStrandPlan,
) -> None:
    preview = preview_proof_strand(addition_plan, max_bytes=320)
    assert len(preview.encode("utf-8")) <= 320
    assert preview.endswith("Compile the complete proof-strand package.")
    assert "Lean verification: NOT RUN" in preview


def test_oversized_statement_cannot_hide_preview_edition_or_source_identity(
    addition_plan: ProofStrandPlan,
) -> None:
    root = addition_plan.root_node
    oversized_root = replace(root, readable_statement="∀" * 40_000)
    oversized_plan = replace(
        addition_plan,
        nodes=tuple(oversized_root if node.name == root.name else node for node in addition_plan.nodes),
    )

    preview = preview_proof_strand(oversized_plan)

    assert preview.startswith("theorem «add_comm» : ∀")
    assert "theorem statement abbreviated" in preview
    assert "-- Edition: stable" in preview
    assert "-- Checked-use evidence: stable_closed; membership: stable" in preview
    assert root.source_sha256 in preview
    assert root.specification_sha256 in preview
    assert "Proof-body replay: NOT RUN" in preview
    assert "Lean verification: NOT RUN" in preview
    assert len(preview.encode("utf-8")) <= 15_360
    assert oversized_plan.root_node.readable_statement == "∀" * 40_000
    assert addition_plan.root_node is root


def test_preview_rejects_counterfeit_plan() -> None:
    with pytest.raises(TypeError, match="ProofStrandPlan"):
        preview_proof_strand(object())  # type: ignore[arg-type]


def test_generated_addition_strand_contains_real_readable_proofs(
    addition_package,
) -> None:
    assert addition_package.manifest["translated_node_count"] == 3
    assert addition_package.manifest["fallback_node_count"] == 0
    assert "theorem «zero_add»" in addition_package.code
    assert "theorem «add_succ_left»" in addition_package.code
    assert "theorem «add_comm»" in addition_package.code
    assert "induction m with" in addition_package.code
    assert "sorry" not in addition_package.code
    assert "native_decide" not in addition_package.code
    assert "axiom " not in addition_package.code
    assert "_checked_local_body_" not in addition_package.code


@pytest.mark.parametrize(
    ("name", "compact_alias"),
    (
        ("division_remainder_exists", "DivRem"),
        ("inverse_prefix_entry_sound", "InversePrefix"),
        ("gcd_balanced_bezout_exists_up_to", "IsGCD"),
    ),
)
def test_alias_rich_declaration_uses_exact_definitional_reconstruction_bridge(
    name: str,
    compact_alias: str,
) -> None:
    from peano_lab.library.lean_presentation import readable_formula

    plan = plan_proof_strand(name, edition="alpha")
    package = build_proof_strand(plan, strict_readable=True)
    formula = _closed_formula(plan.root_node.statement)
    reconstructed_statement = readable_formula(
        formula,
        source_statement=plan.root_node.statement,
    )

    assert package.manifest["fallback_node_count"] == 0
    assert compact_alias in plan.root_node.readable_statement
    assert reconstructed_statement != plan.root_node.readable_statement
    assert (
        f"theorem «{name}» : {plan.root_node.readable_statement} := by\n"
        f"  change {reconstructed_statement}\n"
    ) in package.code
    assert package.manifest["nodes"][-1]["proof_status"] == "readable_lean"
    assert "_checked_local_body_" not in package.code


def test_equivalent_existing_declaration_needs_no_definitional_bridge(
    addition_package,
) -> None:
    assert "theorem «add_comm»" in addition_package.code
    assert "\n  change " not in addition_package.code


def test_generated_strand_includes_all_forty_conservative_definitions(
    addition_package,
) -> None:
    assert addition_package.manifest["definition_count"] == 40
    assert "def Even " in addition_package.code
    assert "def IsGCD " in addition_package.code
    assert "def Factorial " in addition_package.code
    assert "def DivisionPrefix " in addition_package.code


def test_generated_strand_reuses_exact_shared_presentation(addition_package) -> None:
    files = addition_package.files()
    assert files[0] == ("PeanoLab/Presentation.lean", _NOTATION_CODE)
    assert files[1] == (addition_package.relative_path, addition_package.code)
    assert addition_package.relative_path.endswith("/Strand.lean")


def test_manifest_content_hashes_are_exact(addition_package) -> None:
    assert addition_package.manifest["schema"] == "peano-lab-lean-proof-strand-v1"
    for (path, content), record in zip(
        addition_package.files(),
        addition_package.manifest["files"],
        strict=True,
    ):
        assert record["relative_path"] == path
        assert record["sha256"] == sha256(content.encode("utf-8")).hexdigest()
        assert record["bytes"] == len(content.encode("utf-8"))


def test_manifest_never_fabricates_lean_verification(addition_package) -> None:
    assert addition_package.manifest["authority"] == {
        "lean_compiler_verified": False,
        "public_admission": False,
        "publication": False,
        "training": False,
        "final_evaluation": False,
    }


def test_materialized_preview_honestly_records_body_replay(addition_package) -> None:
    assert "Proof-body replay: RUN" in addition_package.preview
    assert "3 readable Lean candidate(s)" in addition_package.preview
    assert "Lean verification: NOT RUN" in addition_package.preview


def test_harmless_lean_linter_warnings_are_suppressed(addition_package) -> None:
    assert "set_option linter.unusedSimpArgs false" in addition_package.code
    assert "set_option linter.unnecessarySimpa false" in addition_package.code


def test_manifest_node_line_ranges_locate_exact_source(addition_package) -> None:
    lines = addition_package.code.splitlines()
    for row in addition_package.manifest["nodes"]:
        assert lines[row["source_line_start"] - 1] == f"-- PROOF NODE: {row['name']}"
        section = "\n".join(
            lines[row["source_line_start"] - 1:row["source_line_end"]]
        )
        assert f"theorem «{row['name']}»" in section


def test_large_strand_splits_into_bounded_topological_modules(
    addition_plan: ProofStrandPlan,
) -> None:
    package = build_proof_strand(addition_plan, chunk_max_bytes=13_100)
    assert package.manifest["chunk_count"] >= 2
    paths = [path for path, _ in package.files()]
    assert paths[0] == "PeanoLab/Presentation.lean"
    assert "/Chunks/C000.lean" in paths[1]
    assert "/Chunks/C001.lean" in paths[2]
    assert paths[-1].endswith("/Strand.lean")
    for _, source in package.files()[1:]:
        assert len(source.encode("utf-8")) <= 13_100
    assert "#print axioms «add_comm»" in package.code
    assert package.code.startswith("-- Final independently compiled theorem")


def test_chunk_imports_previous_namespace_and_public_foundations(
    addition_plan: ProofStrandPlan,
) -> None:
    package = build_proof_strand(addition_plan, chunk_max_bytes=13_100)
    sources = dict(package.files())
    first_path = next(path for path in sources if path.endswith("/Chunks/C000.lean"))
    second_path = next(path for path in sources if path.endswith("/Chunks/C001.lean"))
    assert "theorem pa1_sound" in sources[first_path]
    assert "private theorem pa1_sound" not in sources[first_path]
    previous_module = first_path[:-5].replace("/", ".")
    assert f"import {previous_module}" in sources[second_path]
    assert f"namespace {package.module_name}" in sources[first_path]
    assert f"namespace {package.module_name}" in sources[second_path]


def test_chunk_manifest_line_ranges_locate_exact_module_source(
    addition_plan: ProofStrandPlan,
) -> None:
    package = build_proof_strand(addition_plan, chunk_max_bytes=13_100)
    files = dict(package.files())
    for node in package.manifest["nodes"]:
        lines = files[node["generated_relative_path"]].splitlines()
        assert lines[node["source_line_start"] - 1] == (
            f"-- PROOF NODE: {node['name']}"
        )
        section = "\n".join(
            lines[node["source_line_start"] - 1:node["source_line_end"]]
        )
        assert f"theorem «{node['name']}»" in section


def test_chunk_too_small_for_one_local_node_fails_closed(
    addition_plan: ProofStrandPlan,
) -> None:
    with pytest.raises(ProofStrandLimitError, match="independent Lean chunk"):
        build_proof_strand(addition_plan, chunk_max_bytes=512)


def test_axiom_audit_can_be_omitted(addition_plan: ProofStrandPlan) -> None:
    package = build_proof_strand(addition_plan, include_axiom_audit=False)
    assert "#print axioms" not in package.code


def test_forced_fallback_is_only_a_checked_dependency_curried_body() -> None:
    plan = plan_proof_strand("add_comm")
    package = build_proof_strand(
        plan,
        force_fallback_names=frozenset({"add_comm"}),
    )
    assert package.manifest["translated_node_count"] == 2
    assert package.manifest["fallback_node_count"] == 1
    root = package.manifest["nodes"][-1]
    assert root["name"] == "add_comm"
    assert root["proof_status"] == "local_checked_certificate"
    assert root["used_dependencies"] == ["zero_add", "add_succ_left"]
    assert "_checked_local_body_add_comm" in package.code
    assert (
        "exact «_checked_local_body_add_comm» «zero_add» «add_succ_left»"
        in package.code
    )


def test_forced_fallback_alias_is_supported() -> None:
    package = build_proof_strand(
        plan_proof_strand("zero_add"),
        force_fallback=frozenset({"zero_add"}),
    )
    assert package.manifest["fallback_node_count"] == 1


def test_nontrivial_local_fallback_unfolds_every_nested_formula_and_term() -> None:
    plan = plan_proof_strand("le_of_succ_le_succ")
    assert plan.node_count == 1
    package = build_proof_strand(
        plan,
        force_fallback_names=frozenset({"le_of_succ_le_succ"}),
    )
    assert package.manifest["fallback_node_count"] == 1
    section = package.code.partition("  have sound :=")[2].partition(
        "] using sound (fun _ => 0)"
    )[0]
    identifiers = re.findall(
        r"^private def (_pl_[0-9a-f]+_[ft][0-9]+) : PeanoLab\.(?:Formula|Term)",
        package.code,
        flags=re.MULTILINE,
    )
    assert len(identifiers) >= 8
    assert all(identifier in section for identifier in identifiers)
    assert "PeanoLab.Formula.Holds" in section
    assert "PeanoLab.Term.eval" in section
    assert "PeanoLab.Valuation.cons" in section


def test_strict_readable_forbids_local_certificate_fallback() -> None:
    with pytest.raises(ProofStrandError, match="strict-readable"):
        build_proof_strand(
            plan_proof_strand("zero_add"),
            strict_readable=True,
            force_fallback_names=frozenset({"zero_add"}),
        )


def test_unknown_forced_fallback_cannot_enter_strand(
    addition_plan: ProofStrandPlan,
) -> None:
    with pytest.raises(ProofStrandError, match="outside"):
        build_proof_strand(addition_plan, force_fallback_names=frozenset({"forged"}))


def test_duplicate_forced_fallback_policy_is_rejected(
    addition_plan: ProofStrandPlan,
) -> None:
    with pytest.raises(ProofStrandError, match="only one"):
        build_proof_strand(
            addition_plan,
            force_fallback_names=frozenset(),
            force_fallback=frozenset(),
        )


def test_forged_translator_statement_is_rejected(monkeypatch) -> None:
    from peano_lab.library import lean_proof_reconstruction

    def forged(spec: TheoremSpec, **kwargs) -> LeanProofReconstruction:
        return LeanProofReconstruction(
            name=spec.name,
            lean_statement="False",
            lean_body="by\n  trivial",
            used_dependencies=(),
            used_axioms=(),
            translated_steps=1,
            unsupported_steps=(),
            status="translated",
            diagnostics=(),
        )

    monkeypatch.setattr(lean_proof_reconstruction, "reconstruct_theorem", forged)
    with pytest.raises(ProofStrandError, match="changed its theorem target"):
        build_proof_strand(plan_proof_strand("zero_add"))


def test_forged_translator_dependency_is_rejected(monkeypatch) -> None:
    from peano_lab.library import lean_proof_reconstruction
    from peano_lab.library.lean_presentation import readable_formula

    def forged(spec: TheoremSpec, **kwargs) -> LeanProofReconstruction:
        formula = _closed_formula(spec.statement)
        return LeanProofReconstruction(
            name=spec.name,
            lean_statement=readable_formula(formula, source_statement=spec.statement),
            lean_body="by\n  trivial",
            used_dependencies=("invented_lemma",),
            used_axioms=(),
            translated_steps=1,
            unsupported_steps=(),
            status="translated",
            diagnostics=(),
        )

    monkeypatch.setattr(lean_proof_reconstruction, "reconstruct_theorem", forged)
    with pytest.raises(ProofStrandError, match="undeclared theorem"):
        build_proof_strand(plan_proof_strand("zero_add"))


def test_module_size_limit_fails_closed(addition_plan: ProofStrandPlan) -> None:
    with pytest.raises(ProofStrandLimitError, match="source limit"):
        build_proof_strand(addition_plan, max_module_bytes=256)


def test_node_step_limit_fails_closed(addition_plan: ProofStrandPlan) -> None:
    with pytest.raises(ProofStrandLimitError, match="step"):
        build_proof_strand(addition_plan, max_steps=1)


def test_policy_booleans_cannot_be_forged(addition_plan: ProofStrandPlan) -> None:
    with pytest.raises(ProofStrandError, match="booleans"):
        build_proof_strand(addition_plan, strict_readable=1)  # type: ignore[arg-type]
