"""Exact continuation evidence: real HA/Lean, honest support, hostile inputs.

Positive proof fixtures invoke both unchanged checkers.  Deliberately broken
checkers below only raise or return rejecting output; none supplies a mocked
successful proof.  The ordinary-root cases can be run in separate fresh
processes without changing the proof, compiler, or resource limits.
"""

from dataclasses import replace
from hashlib import sha256
from importlib import import_module
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

import constructive_bottom_layer_checkpoints as bottom
import constructive_lower_tier_checkpoints as lower
import constructive_lower_continuation_checkpoints as checkpoints
import constructive_lower_continuation_support as support
from peano_lab.kernel.checker import check
from peano_lab.kernel.proofs import Hyp
from peano_lab.library.proof_bundle import ProofBundle
from peano_lab.library.theorems import TheoremSpec, _closed_formula


# Independent mathematical inventory, not a copy of a generated success flag.
EXPECTED = {
    "divisor-involutions": {
        "count": 12, "edges": 34, "commands": 480,
        "modules": ("divisor_involution_candidate",),
        "roots": (
            ("positive_divisor_quotient_exists_unique", "a02a6f2e061e89191c7e4dff86b60611ebf035717468a17707bf5537486da384"),
            ("positive_divisor_involution_exists", "7fff4b15206b4bc27488134518c5e8231aee964a484e515576a6426be170719d"),
            ("divisor_complement_prefix_involution", "24bdefde49ebf80220bf5c974be3261d250dc98472d1228f6f3484492a9f34c1"),
        ),
    },
    "mobius-divisor-cancellation": {
        "count": 28, "edges": 99, "commands": 1569,
        "modules": ("mobius_divisor_cancellation_candidate",),
        "roots": (
            ("mobius_divisor_sum_cancellation", "dc605f677a0cdb931e7f3e65b29569dea83f1b9db136b932913a1936dc2b3406"),
            ("mobius_divisor_sum_cancellation_exists", "50bcf039c53ca70483eadd8ff3f9c3baf484d1fc82f84afe21009620ff674280"),
            ("mobius_divisor_sum_cancellation_on_positive_values", "be20bbedecba3566c7d3611f121e3d2e4fdaffd7fdee715dcd7e60afdb4cfd56"),
        ),
    },
    "rectangular-sums": {
        "count": 32, "edges": 92, "commands": 1393,
        "modules": ("signed_rectangular_slice_candidate", "signed_rectangular_sums_candidate"),
        "roots": (
            ("signed_rectangular_slice_exists_extensionally_unique", "d0fbe7f70725333cc208f00e860d04886fafdc5fef4a36bc6e811dd88391ddd4"),
            ("signed_rectangular_fubini", "74787482d51c759b2472790323be3c54494bbf97fab08de48afce458898fd14d"),
            ("signed_rectangular_row_major_fubini", "df286640d573e43c4ce8fc84ed9a405eb4568577f4f683001adb7ae8324ff3ec"),
        ),
    },
    "polynomial-products": {
        "count": 53, "edges": 123, "commands": 2496,
        "modules": ("prime_field_polynomial_convolution_candidate", "prime_field_polynomial_degree_candidate"),
        "roots": (
            ("prime_field_polynomial_convolution_exists_unique", "68befd01e16fc6522f2c848ddaac2bef81ead256b41bf6b03fbff132b7693410"),
            ("prime_field_polynomial_convolution_outside_zero", "724cc30193c104f03c1777ace6bec5f40681be6436e7da9f165d44d10cb97501"),
            ("prime_field_polynomial_convolution_represented_degree_exists", "8ff4406ec7462fc8e97a47932550abde9c428392cda01a1c86fe2dfd082fc51a"),
        ),
    },
}

SOURCE_SHA256 = {
    "divisor_involution_candidate": "67297015bcfbeb16b9090f537a2771d5c3cbfa4000d5c83c90cd0ba16cb15be7",
    "mobius_divisor_cancellation_candidate": "9af47fd019e5899586cb02c0e124579d82c4b65d093cfc73d721f411130b457f",
    "signed_rectangular_slice_candidate": "d676600c931936ff00996209c7d744c269427eaf08611fb625e471f608861e5e",
    "signed_rectangular_sums_candidate": "0ce96c5155bb7bf47f5ae2b8151631bd981263f7d05c25f6ec8b3cd365d7a26e",
    "prime_field_polynomial_convolution_candidate": "20502be0d2beaee44ba4bbdb3f7c376db142dbc9c19a5a472c073b0228367c24",
    "prime_field_polynomial_degree_candidate": "3419cefca1f8e4b130a7c8935218815153eaf9865fe1eeed89118ced8bf339e5",
}

# Read-only comparison with the committed 126-theorem basis, independently of
# the new registry.  These files remain the actual trusted/proof-data boundary.
UNCHANGED_SHA256 = {
    "peano-lab/py/peano_lab/kernel/__init__.py": "e4d6cd30f2468de77d6e02fb71bf84394ff8330d264602bb9398df1ad194bc84",
    "peano-lab/py/peano_lab/kernel/checker.py": "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "peano-lab/py/peano_lab/kernel/formulas.py": "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    "peano-lab/py/peano_lab/kernel/proofs.py": "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    "peano-lab/py/peano_lab/kernel/subst.py": "0c685d14aa8494141181b79f25f72699da044526054a80a689e2d5af519226b3",
    "peano-lab/py/peano_lab/kernel/terms.py": "f49313e209a8861918e3aaca38ddfb27f147f824308af699ab5cc1aafbb6dff5",
    "peano-lab/py/peano_lab/library/proof_bundle.py": "55e91347bc0207e75b89ee25c31bdf8d65b24e19c7252bba4fe14ec537af4ef4",
    "peano-lab/py/peano_lab/library/layered_replay.py": "7c8b14b95ab76fe10f265a10271fd58f779fab3b7524c8f9002884b753b2badf",
    "peano-lab/py/peano_lab/library/formula_dag.py": "3dfd0ad9ec3270cb2cd40948b62f223ba9e5f7284152c823405d8002b7a1a45f",
    "peano-lab/py/peano_lab/library/candidate_validation.py": "de38ddb037e03bbbfec2cc48a96aae5d5dd253c190968b61d9a9f7ff28cf9a42",
    "peano-lab/py/peano_lab/library/campaign_bottom_layer_closure.py": "e4d6f74feabf16ac342c9bfb875a39d060f5b97039866ae3a0a5fea99db84477",
    "scripts/constructive_bottom_layer_checkpoints.py": "edbab69b368b2944ceb38d6c7cee856c04c570ef6f7dc167f73528dd9581ab15",
    "scripts/constructive_lower_tier_checkpoints.py": "37c554fa2a25dd0b0bf72a7c313dd634c02830385aa5c943e68a7996eb78239f",
    "scripts/constructive_lower_tier_support.py": "4ff0a74242a09ac62fcaa07f38ccb89c7ef9b8ff2e36f2114fd5eb46fff33a5a",
}


def _checkpoint(slug):
    matches = [item for item in checkpoints.CHECKPOINTS if item.slug == slug]
    assert len(matches) == 1, f"exactly one completed {slug} checkpoint must be registered"
    return matches[0]


def _module_checkpoint(module):
    return next(_checkpoint(slug) for slug, row in EXPECTED.items() if module in row["modules"])


def test_exact_125_inventory_and_literal_principal_contracts():
    assert len(checkpoints.CHECKPOINTS) == 4
    assert checkpoints.EXPECTED_FAMILIES == set(EXPECTED)
    assert {item.slug: item.frontier_count for item in checkpoints.CHECKPOINTS} == {
        slug: expected["count"] for slug, expected in EXPECTED.items()
    }
    rows = checkpoints.all_new_rows()
    assert len(rows) == len({row.name for row in rows}) == 125
    assert sum(len(row.dependencies) for row in rows) == 348
    assert sum(len(row.script) for row in rows) == 5938
    for slug, expected in EXPECTED.items():
        item = _checkpoint(slug)
        owned = checkpoints.load_rows(item)
        assert tuple(pin.module for pin in item.modules) == expected["modules"]
        assert item.principal_roots == tuple(name for name, _ in expected["roots"])
        assert sum(len(row.dependencies) for row in owned) == expected["edges"]
        assert sum(len(row.script) for row in owned) == expected["commands"]
        by_name = {row.name: row for row in owned}
        for name, digest in expected["roots"]:
            assert sha256(by_name[name].statement.encode()).hexdigest() == digest
    assert len({name for item in EXPECTED.values() for name, _ in item["roots"]}) == 12


@pytest.mark.parametrize("module", tuple(SOURCE_SHA256))
def test_actual_source_pins_match_the_frozen_mathematical_sources(module):
    item = _module_checkpoint(module)
    pin = next(pin for pin in item.modules if pin.module == module)
    assert pin.sha256 == SOURCE_SHA256[module]
    assert sha256(bottom._source_bytes(pin)).hexdigest() == SOURCE_SHA256[module]


@pytest.mark.parametrize("path,digest", tuple(UNCHANGED_SHA256.items()), ids=tuple(UNCHANGED_SHA256))
def test_original_kernel_proof_compilers_and_historical_controls_are_byte_identical(path, digest):
    source = ROOT / path
    assert source.is_file() and not source.is_symlink()
    assert sha256(source.read_bytes()).hexdigest() == digest


def test_parent_catalog_and_all_seven_prior_non_admitting_bundles_are_unchanged():
    closure = checkpoints.closure
    assert closure.PARENT_COUNT == 3222
    assert closure.PARENT_CATALOG_BYTES == 66_503_303
    assert closure.PARENT_CATALOG_SHA256 == "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"
    raw = closure._read_pinned(ROOT / closure.PARENT_CATALOG, 66_503_303, closure.PARENT_CATALOG_SHA256)
    assert sha256(raw).hexdigest() == closure.PARENT_CATALOG_SHA256
    del raw
    assert len(closure.parent_snapshot().specs) == 3222
    assert len(closure.parent_snapshot().documents) == 20
    assert [(item.slug, item.frontier_count) for item in bottom.CHECKPOINTS] == [
        ("euler-units", 32), ("prime-fields", 87), ("mobius-values", 21), ("signed-sums", 30),
    ]
    assert [(item.slug, item.frontier_count) for item in lower.CHECKPOINTS] == [
        ("divisor-sums", 37), ("signed-weighted-sums", 40), ("prime-field-polynomials", 49),
    ]
    assert len(support.first.previous_rows()) == 170
    assert len(support.lower.all_new_rows()) == 126
    prior = support.previous_rows()
    assert len(prior) == len({row.name for row in prior}) == 296
    assert len({pin.path for item in (*bottom.CHECKPOINTS, *lower.CHECKPOINTS) for pin in item.modules}) == 19
    paths = support.previous_seed_paths()
    assert len(paths) == len(set(paths)) == 7
    assert set(paths) == {ROOT / item.artifact for item in (*bottom.CHECKPOINTS, *lower.CHECKPOINTS)}
    assert checkpoints.LEAN_BINARY_SHA256 == bottom.LEAN_BINARY_SHA256 == (
        "22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033"
    )
    assert checkpoints.LEAN_BINARY_BYTES == 106_787_344
    assert bottom.LEAN_TIMEOUT_SECONDS == 30


def test_every_new_statement_is_ast_distinct_from_all_3518_prior_rows_and_its_peers():
    assert support.statement_duplicates(checkpoints.all_new_rows()) == ()


@pytest.fixture(scope="module", params=tuple(EXPECTED), ids=tuple(EXPECTED))
def actual_evidence(request):
    # Do not replace either checker here.  A stored report is not consulted.
    return checkpoints.verify_checkpoint(_checkpoint(request.param))


def test_real_ha_and_compiled_lean_accept_every_body_without_granting_admission(actual_evidence):
    evidence = actual_evidence
    report, selected = evidence.report, evidence.selection
    expected = EXPECTED[evidence.checkpoint.slug]
    assert report["new_theorem_count"] == len(evidence.owned) == expected["count"]
    assert report["new_theorem_dependency_edges"] == expected["edges"]
    assert report["new_theorem_tactic_commands"] == expected["commands"]
    assert report["bundle"]["original_ha_checked"] is report["bundle"]["independent_lean_checked"] is True
    assert evidence.receipt.kernel_calls == evidence.receipt.node_count == len(evidence.plan.rows) + 1
    assert report["bundle"]["nodes_including_packaging_root"] == evidence.receipt.node_count
    assert report["bundle"]["dependency_edges_including_packaging"] == evidence.receipt.dependency_edges
    assert report["bundle"]["body_proof_nodes"] == evidence.receipt.total_body_nodes
    assert report["bundle"]["packaging_root_id"] == evidence.bundle.root == len(evidence.plan.rows)
    assert report["new_specs_sha256"] == checkpoints.closure._specs_digest(evidence.owned)
    assert report["complete_non_alpha_specs_sha256"] == checkpoints.closure._specs_digest(selected.frontier)
    assert report["ordered_new_names_sha256"] == sha256("\n".join(row.name for row in evidence.owned).encode()).hexdigest()
    assert report["all_maximal_owned_roots"] == list(evidence.plan.root_names)
    assert report["membership"] == "local_non_admitting_checkpoint"
    assert all(report[key] is False for key in ("admitted_to_alpha", "alpha_checked_use", "stable_member"))
    assert all(record["complete_ordinary_ha_checked"] is False for record in report["principal_roots"])
    assert all("ordinary_certificate_nodes" not in record for record in report["principal_roots"])
    assert tuple((row["name"], row["statement_sha256"]) for row in report["principal_roots"]) == expected["roots"]
    payload = (ROOT / evidence.checkpoint.artifact).read_bytes()
    assert len(payload) == evidence.checkpoint.artifact_bytes == report["bundle"]["bytes"]
    assert sha256(payload).hexdigest() == evidence.checkpoint.artifact_sha256 == report["bundle"]["sha256"]


def test_support_roles_partition_the_actual_dependency_cone_without_recounting(actual_evidence):
    evidence = actual_evidence
    selected, report = evidence.selection, evidence.report["support"]
    owned = {row.name for row in evidence.owned}
    bottom_names = {row.name for row in support.first.previous_rows()}
    lower_names = {row.name for row in support.lower.all_new_rows()}
    current_names = {row.name for row in checkpoints.all_new_rows()}
    alpha_names = {row.name for row in checkpoints.closure.parent_snapshot().specs}
    groups = {
        "new_owned_theorem": owned,
        "inherited_published_bottom_layer_checkpoint": set(selected.bottom_support),
        "inherited_published_lower_tier_checkpoint": set(selected.lower_support),
        "new_cross_track_support": set(selected.current_support),
        "inherited_alpha_v30": {row.name for row in evidence.plan.rows} & alpha_names,
    }
    assert groups["inherited_published_bottom_layer_checkpoint"] <= bottom_names
    assert groups["inherited_published_lower_tier_checkpoint"] <= lower_names
    assert groups["new_cross_track_support"] <= current_names - owned
    assert sum(map(len, groups.values())) == len(set().union(*groups.values())) == len(evidence.plan.rows)
    for role, names in groups.items():
        assert all(selected.role(name) == role for name in names)
    assert tuple(report["prior_bottom_layer_theorems"]) == selected.bottom_support
    assert tuple(report["prior_lower_tier_theorems"]) == selected.lower_support
    assert tuple(report["current_cross_track_theorems"]) == selected.current_support
    assert report["prior_bottom_layer_count"] == len(selected.bottom_support)
    assert report["prior_lower_tier_count"] == len(selected.lower_support)
    assert report["published_non_admitted_count"] == len(selected.published_support)
    assert selected.published_support == (*selected.bottom_support, *selected.lower_support)
    assert report["current_cross_track_count"] == len(selected.current_support)
    assert report["alpha_v30_count"] == len(groups["inherited_alpha_v30"])
    assert report["counted_as_new_owned_theorems"] is False
    assert set(evidence.plan.root_names) <= owned
    with pytest.raises(support.SupportError, match="actual complete proof cone"):
        selected.role("not_a_proved_dependency")

    # Recompute ancestry from literal theorem dependencies, not imports, rows
    # from unrelated families, admission flags, or precomputed role labels.
    table = {row.name: row for row in (*checkpoints.closure.parent_snapshot().specs,
                                     *support.previous_rows(), *checkpoints.all_new_rows())}
    included, pending = set(), list(owned)
    while pending:
        name = pending.pop()
        if name not in included:
            included.add(name)
            pending.extend(table[name].dependencies)
    assert included == {row.name for row in evidence.plan.rows}
    assert {row.name for row in selected.frontier} == included - alpha_names
    if evidence.checkpoint.slug == "divisor-involutions":
        assert not selected.bottom_support and not selected.lower_support and not selected.current_support
        assert report["alpha_v30_count"] == 127
    if evidence.checkpoint.slug == "mobius-divisor-cancellation":
        # Importing a Python tactic-string helper does not use its theorem.
        involutions = {row.name for row in checkpoints.load_rows(_checkpoint("divisor-involutions"))}
        assert not involutions & included


@pytest.mark.parametrize("root_index", range(3), ids=("root-1", "root-2", "root-3"))
def test_each_of_twelve_principal_roots_has_an_exact_ordinary_empty_context_proof(actual_evidence, root_index):
    evidence = actual_evidence
    name, statement_sha = EXPECTED[evidence.checkpoint.slug]["roots"][root_index]
    spec = next(row for row in evidence.owned if row.name == name)
    proof = checkpoints.closure.replay_bottom_layer_theorem(
        evidence.selection.frontier, name, evidence.bundle, evidence.target)
    target = _closed_formula(spec.statement)
    assert proof.spec == spec
    assert sha256(proof.spec.statement.encode()).hexdigest() == statement_sha
    assert proof.formula == target
    assert proof.proof_nodes > 1
    assert check((), proof.certificate, target)
    assert not check((), proof.certificate, _closed_formula("0=1"))


@pytest.mark.parametrize("mutation", (
    "false_inherited_body", "false_owned_body", "omitted_support", "missing_premise",
    "swapped_premises", "wrong_node_target", "wrong_public_target", "open_packaging_body",
    "omitted_packaging_premise", "wrong_root_id",
))
def test_complete_bundles_reject_missing_poisoned_or_miswired_evidence(actual_evidence, mutation):
    evidence = actual_evidence
    nodes = list(evidence.bundle.nodes)
    inherited = next(row.node_id for row in evidence.plan.rows
                     if evidence.selection.role(row.name) != "new_owned_theorem")
    owned = next(row.node_id for row in evidence.plan.rows
                 if evidence.selection.role(row.name) == "new_owned_theorem" and len(row.dependencies) >= 2)
    target, root = evidence.target, evidence.bundle.root
    if mutation == "false_inherited_body":
        # Poison a real representative of EVERY inherited role present in
        # this cone, not just its first (usually Alpha) ancestor.  In
        # particular, neither prior non-admitted generation is an oracle.
        representatives = {}
        for row in evidence.plan.rows:
            role = evidence.selection.role(row.name)
            if role != "new_owned_theorem":
                representatives.setdefault(role, row.node_id)
        assert representatives
        for node_id in representatives.values():
            poisoned = list(evidence.bundle.nodes)
            poisoned[node_id] = replace(poisoned[node_id], body=Hyp(0))
            with pytest.raises(ValueError):
                checkpoints.closure.check_bottom_layer_bundle(
                    evidence.selection.frontier, ProofBundle(tuple(poisoned), root), target)
        return
    elif mutation == "false_owned_body":
        nodes[owned] = replace(nodes[owned], body=Hyp(0))
    elif mutation == "omitted_support":
        nodes.pop(inherited)
    elif mutation == "missing_premise":
        nodes[owned] = replace(nodes[owned], dependencies=nodes[owned].dependencies[1:])
    elif mutation == "swapped_premises":
        dependencies = nodes[owned].dependencies
        nodes[owned] = replace(nodes[owned], dependencies=(dependencies[1], dependencies[0], *dependencies[2:]))
    elif mutation == "wrong_node_target":
        nodes[owned] = replace(nodes[owned], target=_closed_formula("0=1"))
    elif mutation == "wrong_public_target":
        target = _closed_formula("0=1")
    elif mutation == "open_packaging_body":
        nodes[-1] = replace(nodes[-1], body=Hyp(0))
    elif mutation == "omitted_packaging_premise":
        nodes[-1] = replace(nodes[-1], dependencies=nodes[-1].dependencies[1:])
    else:
        root -= 1
    with pytest.raises(ValueError):
        checkpoints.closure.check_bottom_layer_bundle(
            evidence.selection.frontier, ProofBundle(tuple(nodes), root), target)


@pytest.mark.parametrize("value", (None, False, {}, "divisor-involutions"))
def test_nonrecords_fail_before_any_source_read(monkeypatch, value):
    monkeypatch.setattr(bottom, "_source_bytes", lambda _: pytest.fail("invalid record read a source"))
    with pytest.raises(checkpoints.CheckpointError, match="literal registered"):
        checkpoints.load_rows(value)


@pytest.mark.parametrize("field,value", (
    ("slug", "counterfeit"), ("modules", ()), ("artifact", "other.json"),
    ("artifact_bytes", 1), ("artifact_sha256", "0" * 64), ("frontier_count", 1),
    ("principal_roots", ()), ("rfc", "counterfeit.md"), ("frontier_specs_sha256", "0" * 64),
))
def test_changed_literal_registration_is_not_a_new_authority_grant(monkeypatch, field, value):
    item = _checkpoint("divisor-involutions")
    monkeypatch.setattr(bottom, "_source_bytes", lambda _: pytest.fail("altered registration read a source"))
    with pytest.raises(checkpoints.CheckpointError, match="literal registered"):
        checkpoints.verify_checkpoint(replace(item, **{field: value}))


def test_each_non_admitting_generation_has_a_distinct_literal_registry():
    for older in (bottom, lower):
        with pytest.raises(checkpoints.CheckpointError, match="literal registered"):
            checkpoints.load_rows(older.CHECKPOINTS[0])
        with pytest.raises(checkpoints.CheckpointError, match="literal registered"):
            older.load_rows(_checkpoint("divisor-involutions"))


@pytest.mark.parametrize("flag", (None, 0, 1, "yes", (), []))
def test_nonboolean_ordinary_request_fails_before_sources(monkeypatch, flag):
    monkeypatch.setattr(checkpoints, "load_rows", lambda _: pytest.fail("invalid flag read sources"))
    with pytest.raises(checkpoints.CheckpointError, match="Boolean"):
        checkpoints.verify_checkpoint(_checkpoint("divisor-involutions"), ordinary_roots=flag)
    with pytest.raises(checkpoints.CheckpointError, match="Boolean"):
        checkpoints.verify_all(ordinary_roots=flag)


@pytest.mark.parametrize("mutation", ("empty", "missing", "foreign", "duplicate_replacing_family"))
def test_incomplete_or_substituted_tranche_cannot_report_completion(monkeypatch, mutation):
    registry = tuple(_checkpoint(slug) for slug in EXPECTED)
    if mutation == "empty":
        altered = ()
    elif mutation == "missing":
        altered = registry[:-1]
    elif mutation == "foreign":
        altered = (*registry[:-1], bottom.CHECKPOINTS[0])
    else:
        altered = (*registry[:-1], registry[0])
    monkeypatch.setattr(checkpoints, "CHECKPOINTS", altered)
    monkeypatch.setattr(checkpoints, "all_new_rows", lambda: pytest.fail("incomplete inventory loaded mathematics"))
    with pytest.raises(checkpoints.CheckpointError, match="all four exact"):
        checkpoints.verify_all()


@pytest.mark.parametrize("mutation", ("missing", "empty", "same_size_change", "oversized", "symlink", "directory"))
def test_bad_source_bytes_never_execute_even_an_already_imported_factory(tmp_path, monkeypatch, mutation):
    item = _checkpoint("divisor-involutions")
    pin = item.modules[0]
    path = tmp_path / pin.path
    path.parent.mkdir(parents=True)
    if mutation == "empty":
        path.write_bytes(b"")
    elif mutation == "same_size_change":
        raw = (ROOT / pin.path).read_bytes()
        path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
    elif mutation == "oversized":
        path.write_bytes(b"x" * (bottom.MAX_SOURCE_BYTES + 1))
    elif mutation == "symlink":
        path.symlink_to(ROOT / pin.path)
    elif mutation == "directory":
        path.mkdir()
    monkeypatch.setattr(bottom, "ROOT", tmp_path)
    monkeypatch.setattr(checkpoints, "import_module", lambda _: pytest.fail("unauthenticated factory executed"))
    with pytest.raises(checkpoints.CheckpointError):
        checkpoints.load_rows(item)


def test_all_modules_are_authenticated_before_the_first_factory_runs(tmp_path, monkeypatch):
    item = _checkpoint("polynomial-products")
    assert len(item.modules) == 2
    for index, pin in enumerate(item.modules):
        path = tmp_path / pin.path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((ROOT / pin.path).read_bytes() if index == 0 else b"unauthenticated second module")
    monkeypatch.setattr(bottom, "ROOT", tmp_path)
    monkeypatch.setattr(checkpoints, "import_module", lambda _: pytest.fail("first factory ran before all source pins"))
    with pytest.raises(checkpoints.CheckpointError, match="source changed"):
        checkpoints.load_rows(item)


@pytest.mark.parametrize("module", tuple(SOURCE_SHA256))
@pytest.mark.parametrize("field,value", (
    ("name", "counterfeit_cached_name"), ("statement", "0=0"), ("dependencies", ()),
    ("script", ("refl",)), ("summary", "counterfeit cached prose"),
))
def test_source_pins_do_not_authenticate_a_poisoned_cached_factory(monkeypatch, module, field, value):
    item = _module_checkpoint(module)
    pin = next(pin for pin in item.modules if pin.module == module)
    imported = import_module("peano_lab.library." + module)
    rows = getattr(imported, pin.factory)(TheoremSpec)
    assert getattr(rows[0], field) != value
    altered = (replace(rows[0], **{field: value}), *rows[1:])
    monkeypatch.setattr(imported, pin.factory, lambda _: altered)
    with pytest.raises(checkpoints.CheckpointError, match="literal ordered"):
        checkpoints.load_rows(item)


@pytest.mark.parametrize("mutation", ("omitted", "reordered", "duplicated"))
def test_whole_ordered_spec_pin_covers_missing_reordered_and_duplicate_rows(monkeypatch, mutation):
    item = _checkpoint("divisor-involutions")
    pin = item.modules[0]
    imported = import_module("peano_lab.library." + pin.module)
    rows = getattr(imported, pin.factory)(TheoremSpec)
    altered = rows[1:] if mutation == "omitted" else (rows[1], rows[0], *rows[2:]) if mutation == "reordered" else (*rows, rows[0])
    monkeypatch.setattr(imported, pin.factory, lambda _: altered)
    with pytest.raises(ValueError):
        checkpoints.load_rows(item)


@pytest.mark.parametrize("mutation", ("missing", "truncated", "grown", "same_size_change", "symlink", "directory"))
def test_artifact_size_digest_and_type_fail_before_decoding_or_checking(tmp_path, monkeypatch, mutation):
    item = _checkpoint("divisor-involutions")
    raw = (ROOT / item.artifact).read_bytes()
    path = tmp_path / item.artifact
    path.parent.mkdir(parents=True)
    if mutation == "truncated":
        path.write_bytes(raw[:-1])
    elif mutation == "grown":
        path.write_bytes(raw + b" ")
    elif mutation == "same_size_change":
        path.write_bytes(bytes([raw[0] ^ 1]) + raw[1:])
    elif mutation == "symlink":
        path.symlink_to(ROOT / item.artifact)
    elif mutation == "directory":
        path.mkdir()
    monkeypatch.setattr(checkpoints, "ROOT", tmp_path)
    monkeypatch.setattr(checkpoints, "decode_proof_bundle", lambda _: pytest.fail("unpinned artifact decoded"))
    monkeypatch.setattr(bottom, "_lean_check", lambda *args: pytest.fail("unpinned artifact reached Lean"))
    with pytest.raises(checkpoints.closure.BottomLayerClosureError, match="sealed source"):
        checkpoints.verify_checkpoint(item)


@pytest.mark.parametrize("names", (None, [], (), (1,), ("absent",), ("owned", "owned"), ("other", "owned")))
def test_support_rejects_bad_or_recounted_ownership(names):
    rows = (TheoremSpec("owned", "0=0", (), ("refl",), "test syntax"),
            TheoremSpec("other", "1=1", (), ("refl",), "test syntax"))
    with pytest.raises(support.SupportError):
        support.select_support(rows, names)


@pytest.mark.parametrize("mutation", ("alpha_shadow", "bottom_shadow", "lower_shadow", "missing", "self_cycle", "forward"))
def test_support_validates_even_unused_bad_current_rows(mutation):
    inherited = checkpoints.closure.parent_snapshot().specs[0]
    old_bottom = support.first.previous_rows()[0]
    old_lower = support.lower.all_new_rows()[0]
    anchor = TheoremSpec("new_test_anchor", "0=0", (), ("refl",), "test syntax")
    if mutation.endswith("shadow"):
        original = {"alpha_shadow": inherited, "bottom_shadow": old_bottom, "lower_shadow": old_lower}[mutation]
        bad = TheoremSpec(original.name, "0=0", (), ("refl",), "test syntax")
    else:
        name = "new_test_bad"
        dependency = {"missing": "absent_dependency", "self_cycle": name, "forward": "new_test_later"}[mutation]
        bad = TheoremSpec(name, "0=0", (dependency,), ("refl",), "test syntax")
    later = TheoremSpec("new_test_later", "0=0", (), ("refl",), "test syntax")
    with pytest.raises(ValueError):
        support.select_support((anchor, bad, later), (anchor.name,))


@pytest.mark.parametrize("payload", (b"", b"{}", "not bytes", None, bytearray(b"{}")))
def test_lean_receives_only_the_exact_authenticated_ha_bytes(monkeypatch, payload):
    monkeypatch.setattr(bottom, "_check_lean_binary", lambda: pytest.fail("bad input reached binary verification"))
    with pytest.raises(checkpoints.CheckpointError, match="authenticated HA payload"):
        bottom._lean_check(_checkpoint("divisor-involutions"), 140, 139, payload)


@pytest.mark.parametrize("mutation", ("missing", "size", "digest", "symlink"))
def test_fake_lean_executable_is_never_run(tmp_path, monkeypatch, mutation):
    path = tmp_path / "fake-checker"
    if mutation == "size":
        path.write_bytes(b"wrong")
    elif mutation == "digest":
        path.write_bytes(b"fake")
        # This deliberately hostile binary metadata must still fail its SHA.
        monkeypatch.setattr(bottom, "LEAN_BINARY_BYTES", 4)
    elif mutation == "symlink":
        path.symlink_to(bottom.LEAN_BINARY)
    monkeypatch.setattr(bottom, "LEAN_BINARY", path)
    monkeypatch.setattr(bottom.subprocess, "run", lambda *args, **kwargs: pytest.fail("fake checker executed"))
    item = _checkpoint("divisor-involutions")
    with pytest.raises(checkpoints.CheckpointError):
        bottom._lean_check(item, 140, 139, (ROOT / item.artifact).read_bytes())


@pytest.mark.parametrize("mutation", ("returncode", "reject", "nodes", "root", "path", "extra", "stderr", "timeout", "oserror"))
def test_rejecting_or_forged_lean_receipts_fail_closed_and_use_private_input(monkeypatch, mutation):
    item = _checkpoint("divisor-involutions")
    payload = (ROOT / item.artifact).read_bytes()
    snapshots = []

    def reject(command, **kwargs):
        assert command[0] == str(bottom.LEAN_BINARY)
        snapshot = Path(command[1])
        snapshots.append(snapshot)
        assert snapshot != ROOT / item.artifact and snapshot.read_bytes() == payload
        assert snapshot.parent.stat().st_mode & 0o777 == 0o700
        assert kwargs == {"text": True, "capture_output": True, "timeout": 30, "check": False}
        expected = f"ACCEPT\t{snapshot}\tnodes=140\troot=139\n"
        if mutation == "timeout":
            raise subprocess.TimeoutExpired(command, 30)
        if mutation == "oserror":
            raise OSError("deliberately unavailable verifier")
        output = {
            "reject": "REJECT\n", "nodes": expected.replace("nodes=140", "nodes=1"),
            "root": expected.replace("root=139", "root=0"),
            "path": expected.replace(str(snapshot), "another-proof.json"),
            "extra": expected + "unrelated second receipt\n",
        }.get(mutation, expected)
        return SimpleNamespace(returncode=1 if mutation == "returncode" else 0,
                               stdout=output, stderr="unexpected diagnostics" if mutation == "stderr" else "")

    # The binary's real exact bytes are still checked.  Every stubbed result
    # rejects; there is intentionally no mocked positive receipt case.
    monkeypatch.setattr(bottom.subprocess, "run", reject)
    with pytest.raises(checkpoints.CheckpointError):
        bottom._lean_check(item, 140, 139, payload)
    assert len(snapshots) == 1 and not snapshots[0].exists()


def test_ha_failure_propagates_before_lean_or_any_ordinary_replay(monkeypatch):
    def reject(*args):
        raise checkpoints.closure.BottomLayerClosureError("deliberate HA rejection")

    monkeypatch.setattr(checkpoints.closure, "check_bottom_layer_bundle", reject)
    monkeypatch.setattr(bottom, "_lean_check", lambda *args: pytest.fail("HA failure reached Lean"))
    monkeypatch.setattr(checkpoints.closure, "replay_bottom_layer_theorem", lambda *args: pytest.fail("HA failure reached replay"))
    with pytest.raises(checkpoints.closure.BottomLayerClosureError, match="deliberate HA rejection"):
        checkpoints.verify_checkpoint(_checkpoint("divisor-involutions"), ordinary_roots=True)


def test_lean_failure_prevents_any_ordinary_success_report(monkeypatch):
    def reject(*args):
        raise checkpoints.CheckpointError("deliberate independent rejection")

    monkeypatch.setattr(bottom, "_lean_check", reject)
    monkeypatch.setattr(checkpoints.closure, "replay_bottom_layer_theorem", lambda *args: pytest.fail("Lean failure reached replay"))
    with pytest.raises(checkpoints.CheckpointError, match="deliberate independent rejection"):
        checkpoints.verify_checkpoint(_checkpoint("divisor-involutions"), ordinary_roots=True)


@pytest.mark.parametrize("mutation", ("open_hypothesis", "other_formula", "other_spec", "replay_failure"))
def test_ordinary_return_value_must_prove_the_literal_empty_context_statement(monkeypatch, mutation):
    item = _checkpoint("divisor-involutions")
    spec = next(row for row in checkpoints.load_rows(item) if row.name == item.principal_roots[0])
    replacement = SimpleNamespace(spec=spec, formula=_closed_formula(spec.statement), certificate=Hyp(0), proof_nodes=1)
    if mutation in ("other_formula", "other_spec"):
        # Isolate metadata authentication: use a genuinely valid proof of the
        # exact requested formula, and change ONLY one returned metadata field.
        # An invalid certificate would not isolate either equality guard.
        owned = checkpoints.load_rows(item)
        selection = support.select_support(checkpoints.all_new_rows(), tuple(row.name for row in owned))
        payload = checkpoints.closure._read_pinned(
            ROOT / item.artifact, item.artifact_bytes, item.artifact_sha256)
        bundle, target = checkpoints.decode_proof_bundle(payload.decode("utf-8"))
        genuine = checkpoints.closure.replay_bottom_layer_theorem(
            selection.frontier, spec.name, bundle, target)
        assert genuine.spec == spec and genuine.formula == _closed_formula(spec.statement)
        assert check((), genuine.certificate, genuine.formula)
        replacement = (replace(genuine, formula=_closed_formula("0=0")) if mutation == "other_formula"
                       else replace(genuine, spec=replace(genuine.spec, name="counterfeit_returned_name")))

    def broken_replay(*args):
        if mutation == "replay_failure":
            raise checkpoints.closure.BottomLayerClosureError("deliberate ordinary replay rejection")
        return replacement

    monkeypatch.setattr(checkpoints.closure, "replay_bottom_layer_theorem", broken_replay)
    with pytest.raises(ValueError, match="replay rejection|empty-context certificate"):
        # Actual complete original HA and actual compiled Lean run first.
        checkpoints.verify_checkpoint(item, ordinary_roots=True)


def test_inventory_import_cannot_enroll_any_theorem_or_import_editions():
    program = (
        "import sys;sys.path[:0]=['scripts','peano-lab/py'];"
        "from constructive_lower_continuation_checkpoints import all_new_rows;"
        "assert len(all_new_rows())==125;"
        "assert not any(name.startswith(('peano_lab.library.editions',"
        "'peano_lab.library.alpha_enrollment')) for name in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", program], cwd=ROOT, check=True, timeout=45)
