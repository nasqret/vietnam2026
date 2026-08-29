"""Exact Dirichlet evidence: real HA/Lean, honest support, hostile inputs.

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
import constructive_lower_continuation_checkpoints as continuation
import constructive_dirichlet_checkpoints as checkpoints
import constructive_dirichlet_support as support
from peano_lab.kernel.checker import check
from peano_lab.kernel.proofs import Hyp
from peano_lab.library.proof_bundle import ProofBundle
from peano_lab.library.theorems import TheoremSpec, _closed_formula


# Independent mathematical inventory, not a copy of a generated success flag.
EXPECTED = {
    "finite-support": {
        "count": 8, "edges": 25, "commands": 312, "roles": (11, 1, 0, 0, 149),
        "modules": ("signed_finite_support_candidate",),
        "roots": (
            ("signed_prefix_sum_zero_tail", "ae30d900f38f2fa5e22a59fe2a38056ffb4242b1fcb8ebf364c7673606f1d46b"),
            ("signed_prefix_sum_last_value", "d813ceef952a622bca2fb25909b732dc7c4f9987720b050a3c5a41b590690013"),
            ("signed_prefix_sum_zero_padding_iff", "0a6919b464fecaa0138aef0d8ce9f24d3e2f48357a29544523c17e67b3200f4e"),
        ),
    },
    "dirichlet-convolution": {
        "count": 40, "edges": 102, "commands": 1754, "roles": (20, 7, 8, 2, 192),
        "modules": ("dirichlet_convolution_candidate", "dirichlet_commutativity_candidate"),
        "roots": (
            ("dirichlet_convolution_table_exists_extensionally_unique", "dd3b6ce98b1cda129a5105bc176ffbb4e7ca7d9549ea61a8ddcfc53a4a1ced13"),
            ("dirichlet_convolution_table_commutative", "bcbe8d62a9c065aa28bd6caf8450e86381156e555ae1b4bcc6067a08aa6bbb40"),
            ("dirichlet_convolution_padded_prefix_iff", "81ea53acd86ba6b094a55b9de9d69ee97c444f5a9f5eedfa3e5e6c9afcb9002e"),
        ),
    },
    "dirichlet-fubini": {
        "count": 32, "edges": 117, "commands": 1962, "roles": (24, 19, 30, 31, 210),
        "modules": ("dirichlet_fubini_candidate", "dirichlet_associativity_candidate"),
        "roots": (
            ("dirichlet_convolution_fubini_interchange", "52ec70863e39714463cce993fd232ffe99a1a5e0c5a97f0daecfe5b41ed8e3bd"),
            ("dirichlet_convolution_associative", "7963b56c370b9ff42ae43dc3e12d13dd36b6bd1dd356b62269a062a6a90d6738"),
            ("dirichlet_convolution_associative_tables_exists", "f0e95e4639f59cc7b592d82384c2cf72b63e594814599db6b7bf24339b35adc1"),
        ),
    },
    "dirichlet-units": {
        "count": 25, "edges": 82, "commands": 1109, "roles": (21, 8, 8, 22, 197),
        "modules": ("dirichlet_units_candidate",),
        "roots": (
            ("dirichlet_delta_unit_exists", "6924256ebdc7a4a8b46c532d5808e5794dea1430b6d1892c764a826191b4d710"),
            ("dirichlet_constant_one_sum_iff", "f502d0a59a4eb50a35be7b76d39904729a96e3d6d5c91d4e019a6aad9639908f"),
            ("dirichlet_constant_one_realizes_divisor_sum", "5aafb1de83c084f4d86aef3f3649ebc962a43b64c55c7356c45500c8db072d09"),
        ),
    },
    "mobius-inversion": {
        "count": 8, "edges": 28, "commands": 458, "roles": (45, 41, 56, 78, 302),
        "modules": ("mobius_inversion_candidate",),
        "roots": (
            ("mobius_inversion_for_actual_mobius_table", "c69a34ea1a32d3d1188c00a95754507739ed77b953a355e2ffccf0ad69e21dab"),
            ("mobius_inversion_arithmetic_tables", "a0cacd2561b809b9cd7e9909fd37cbbcd7a60f086560bf1bd5a2fecad5c978b9"),
            ("mobius_inversion_iff", "c98dbac33cefe8835eb9c023fd942e6fcb998e7bb8ca0607989b462724a8cad1"),
        ),
    },
}

SOURCE_SHA256 = {
    "signed_finite_support_candidate": "624040e65e0852e652ecda46d2078703e8c0d062dcb06566e24e7d86e9878191",
    "dirichlet_convolution_candidate": "cec111fbad76f106a5a3f79e2d78fc2a8d483267baa1b19738d4cbfb0c0fb342",
    "dirichlet_commutativity_candidate": "1408ca915b4c335afc679b617c4189164b6701730746d3a8aa7f2a260bf75e8d",
    "dirichlet_fubini_candidate": "f18fc61cff3d778568611abebc9698e4c7da9a7dbba37d3b361597dfc988710f",
    "dirichlet_associativity_candidate": "598b0b5658dcba34f97eec4f432de111452ad734a3171832aa2e08bb13a90692",
    "dirichlet_units_candidate": "4821a0e7a8ecac28080db207dd96abf4d02a285a85da6d1173b6a1349a82b77c",
    "mobius_inversion_candidate": "79309dd26c6f434c2e8bb76858dfada758b4a2b489065403b41c70785e1bf183",
}

# Read-only comparison with the committed 421-research-theorem basis, independently of
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
    "scripts/constructive_lower_continuation_checkpoints.py": "de3e315d0fc793cd4acff1199ff8ef98b699e7840ad7e49e012d7ef1e99f9f55",
    "scripts/constructive_lower_continuation_support.py": "4cc9a30642f85f2b541c04e3af2312e1ba9f40f7f72764d3e4e7d0adcee5f41f",
}


def _checkpoint(slug):
    matches = [item for item in checkpoints.CHECKPOINTS if item.slug == slug]
    assert len(matches) == 1, f"exactly one completed {slug} checkpoint must be registered"
    return matches[0]


def _module_checkpoint(module):
    return next(_checkpoint(slug) for slug, row in EXPECTED.items() if module in row["modules"])


def test_exact_113_inventory_and_literal_principal_contracts():
    assert len(checkpoints.CHECKPOINTS) == 5
    assert checkpoints.EXPECTED_FAMILIES == set(EXPECTED)
    assert {item.slug: item.frontier_count for item in checkpoints.CHECKPOINTS} == {
        slug: expected["count"] for slug, expected in EXPECTED.items()
    }
    rows = checkpoints.all_new_rows()
    assert len(rows) == len({row.name for row in rows}) == 113
    assert sum(len(row.dependencies) for row in rows) == 354
    assert sum(len(row.script) for row in rows) == 5595
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
    assert len({name for item in EXPECTED.values() for name, _ in item["roots"]}) == 15


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


def test_parent_catalog_and_all_eleven_prior_non_admitting_bundles_are_unchanged():
    closure=checkpoints.closure
    assert closure.PARENT_COUNT==3222 and closure.PARENT_CATALOG_BYTES==66_503_303
    assert closure.PARENT_CATALOG_SHA256=="ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"
    raw=closure._read_pinned(ROOT/closure.PARENT_CATALOG,66_503_303,closure.PARENT_CATALOG_SHA256)
    assert sha256(raw).hexdigest()==closure.PARENT_CATALOG_SHA256
    del raw
    assert len(closure.parent_snapshot().specs)==3222
    assert len(closure.parent_snapshot().documents)==20
    first=tuple(row for item in bottom.CHECKPOINTS for row in bottom.load_rows(item))
    second=lower.all_new_rows()
    third=continuation.all_new_rows()
    assert tuple(map(len,(first,second,third)))==(170,126,125)
    assert support.previous_rows()==(*first,*second,*third)
    assert len(support.previous_rows())==421
    paths=support.previous_seed_paths()
    assert len(paths)==len(set(paths))==11
    assert set(paths)=={ROOT/item.artifact for item in (*bottom.CHECKPOINTS,*lower.CHECKPOINTS,*continuation.CHECKPOINTS)}
    assert checkpoints.LEAN_BINARY_SHA256==bottom.LEAN_BINARY_SHA256=="22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033"
    assert checkpoints.LEAN_BINARY_BYTES==106_787_344 and bottom.LEAN_TIMEOUT_SECONDS==30


def test_every_new_statement_is_ast_distinct_from_all_3643_prior_rows_and_its_peers():
    assert support.statement_duplicates(checkpoints.all_new_rows()) == ()


@pytest.fixture(scope="module", params=tuple(EXPECTED), ids=tuple(EXPECTED))
def actual_evidence(request):
    # Do not replace either checker here.  A stored report is not consulted.
    try:
        return checkpoints.verify_checkpoint(_checkpoint(request.param))
    except Exception as error:
        # Printing a whole failed proof-bundle fixture can be far larger
        # than the failure itself; report the real checker error directly.
        pytest.fail(f"{type(error).__name__}: {error}",pytrace=False)


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
    evidence=actual_evidence
    selected,report=evidence.selection,evidence.report["support"]
    owned={row.name for row in evidence.owned}
    first={row.name for item in bottom.CHECKPOINTS for row in bottom.load_rows(item)}
    second={row.name for row in lower.all_new_rows()}
    third={row.name for row in continuation.all_new_rows()}
    current={row.name for row in checkpoints.all_new_rows()}
    alpha={row.name for row in checkpoints.closure.parent_snapshot().specs}
    groups={
        "new_owned_theorem":owned,
        "inherited_published_bottom_layer_checkpoint":set(selected.bottom_support),
        "inherited_published_lower_tier_checkpoint":set(selected.lower_support),
        "inherited_local_lower_continuation_checkpoint":set(selected.local_support),
        "new_cross_track_support":set(selected.current_support),
        "inherited_alpha_v30":{row.name for row in evidence.plan.rows}&alpha,
    }
    assert set(selected.bottom_support)<=first and set(selected.lower_support)<=second
    assert set(selected.local_support)<=third and set(selected.current_support)<=current-owned
    assert sum(map(len,groups.values()))==len(set().union(*groups.values()))==len(evidence.plan.rows)
    for role,names in groups.items():
        assert all(selected.role(name)==role for name in names)
    for key,actual in (("prior_bottom_layer_theorems",selected.bottom_support),
                       ("prior_lower_tier_theorems",selected.lower_support),
                       ("prior_lower_continuation_theorems",selected.local_support),
                       ("current_cross_track_theorems",selected.current_support)):
        assert tuple(report[key])==actual
    observed=(len(selected.bottom_support),len(selected.lower_support),len(selected.local_support),
              len(selected.current_support),len(groups["inherited_alpha_v30"]))
    assert observed==EXPECTED[evidence.checkpoint.slug]["roles"]
    for key,value in zip(("prior_bottom_layer_count","prior_lower_tier_count","prior_lower_continuation_count",
                          "current_cross_track_count","alpha_v30_count"),observed,strict=True):
        assert report[key]==value
    assert report["published_non_admitted_count"]==observed[0]+observed[1]
    assert report["local_non_admitted_count"]==observed[2]
    assert report["counted_as_new_owned_theorems"] is False
    assert selected.published_support==(*selected.bottom_support,*selected.lower_support)
    assert selected.inherited_support==(*selected.published_support,*selected.local_support)
    assert set(evidence.plan.root_names)<=owned
    with pytest.raises(support.SupportError,match="actual complete proof cone"):
        selected.role("not_a_proved_dependency")
    # Recompute actual ancestry; helper imports and inventory order grant no premise.
    table={row.name:row for row in (*checkpoints.closure.parent_snapshot().specs,
                                    *support.previous_rows(),*checkpoints.all_new_rows())}
    included,pending=set(),list(owned)
    while pending:
        name=pending.pop()
        if name not in included:
            included.add(name);pending.extend(table[name].dependencies)
    assert included=={row.name for row in evidence.plan.rows}
    assert {row.name for row in selected.frontier}==included-alpha

@pytest.mark.parametrize("root_index", range(3), ids=("root-1", "root-2", "root-3"))
def test_each_of_fifteen_principal_roots_has_an_exact_ordinary_empty_context_proof(actual_evidence, root_index):
    evidence = actual_evidence
    name, statement_sha = EXPECTED[evidence.checkpoint.slug]["roots"][root_index]
    spec = next(row for row in evidence.owned if row.name == name)
    try:
        proof = checkpoints.closure.replay_bottom_layer_theorem(
            evidence.selection.frontier, name, evidence.bundle, evidence.target)
        target = _closed_formula(spec.statement)
        if proof.spec != spec or sha256(proof.spec.statement.encode()).hexdigest() != statement_sha:
            raise AssertionError("the ordinary result changed the exact requested specification")
        if proof.formula != target or proof.proof_nodes <= 1:
            raise AssertionError("the ordinary result changed the requested formula or has no real certificate")
        if not check((), proof.certificate, target):
            raise AssertionError("the actual ordinary certificate failed the original empty-context check")
        if check((), proof.certificate, _closed_formula("0=1")):
            raise AssertionError("the actual certificate was accepted for an unrelated false conclusion")
    except Exception as error:
        pytest.fail(f"{name}: {type(error).__name__}: {error}",pytrace=False)


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
        # this cone, not just its first (usually Alpha) ancestor. In particular, none
        # of the three prior research generations or new cross-track rows is an oracle.
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


@pytest.mark.parametrize("value", (None, False, {}, "finite-support"))
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
    item = _checkpoint("finite-support")
    monkeypatch.setattr(bottom, "_source_bytes", lambda _: pytest.fail("altered registration read a source"))
    with pytest.raises(checkpoints.CheckpointError, match="literal registered"):
        checkpoints.verify_checkpoint(replace(item, **{field: value}))


def test_each_non_admitting_generation_has_a_distinct_literal_registry():
    for older in (bottom, lower, continuation):
        with pytest.raises(checkpoints.CheckpointError, match="literal registered"):
            checkpoints.load_rows(older.CHECKPOINTS[0])
        with pytest.raises(checkpoints.CheckpointError, match="literal registered"):
            older.load_rows(_checkpoint("finite-support"))


@pytest.mark.parametrize("flag", (None, 0, 1, "yes", (), []))
def test_nonboolean_ordinary_request_fails_before_sources(monkeypatch, flag):
    monkeypatch.setattr(checkpoints, "load_rows", lambda _: pytest.fail("invalid flag read sources"))
    with pytest.raises(checkpoints.CheckpointError, match="Boolean"):
        checkpoints.verify_checkpoint(_checkpoint("finite-support"), ordinary_roots=flag)
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
    with pytest.raises(checkpoints.CheckpointError, match="all five exact"):
        checkpoints.verify_all()


@pytest.mark.parametrize("mutation", ("missing", "empty", "same_size_change", "oversized", "symlink", "directory"))
def test_bad_source_bytes_never_execute_even_an_already_imported_factory(tmp_path, monkeypatch, mutation):
    item = _checkpoint("finite-support")
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
    item = _checkpoint("dirichlet-convolution")
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
    index=next(index for index,row in enumerate(rows) if getattr(row,field)!=value)
    altered=(*rows[:index],replace(rows[index],**{field:value}),*rows[index+1:])
    monkeypatch.setattr(imported, pin.factory, lambda _: altered)
    with pytest.raises(checkpoints.CheckpointError, match="literal ordered"):
        checkpoints.load_rows(item)


@pytest.mark.parametrize("mutation", ("omitted", "reordered", "duplicated"))
def test_whole_ordered_spec_pin_covers_missing_reordered_and_duplicate_rows(monkeypatch, mutation):
    item = _checkpoint("finite-support")
    pin = item.modules[0]
    imported = import_module("peano_lab.library." + pin.module)
    rows = getattr(imported, pin.factory)(TheoremSpec)
    altered = rows[1:] if mutation == "omitted" else (rows[1], rows[0], *rows[2:]) if mutation == "reordered" else (*rows, rows[0])
    monkeypatch.setattr(imported, pin.factory, lambda _: altered)
    with pytest.raises(ValueError):
        checkpoints.load_rows(item)


@pytest.mark.parametrize("principal_only", (False, True))
@pytest.mark.parametrize("mutation", ("missing", "truncated", "grown", "same_size_change", "symlink", "directory"))
def test_artifact_size_digest_and_type_fail_before_decoding_or_checking(tmp_path, monkeypatch, mutation, principal_only):
    item = _checkpoint("finite-support")
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
        if principal_only:
            checkpoints.verify_principal_root(item,item.principal_roots[0])
        else:
            checkpoints.verify_checkpoint(item)


@pytest.mark.parametrize("names", (None, [], (), (1,), ("absent",), ("owned", "owned"), ("other", "owned")))
def test_support_rejects_bad_or_recounted_ownership(names):
    rows = (TheoremSpec("owned", "0=0", (), ("refl",), "test syntax"),
            TheoremSpec("other", "1=1", (), ("refl",), "test syntax"))
    with pytest.raises(support.SupportError):
        support.select_support(rows, names)


@pytest.mark.parametrize("mutation", ("alpha_shadow", "bottom_shadow", "lower_shadow", "local_shadow", "missing", "self_cycle", "forward"))
def test_support_validates_even_unused_bad_current_rows(mutation):
    inherited = checkpoints.closure.parent_snapshot().specs[0]
    old_bottom=bottom.load_rows(bottom.CHECKPOINTS[0])[0]
    old_lower=lower.all_new_rows()[0]
    old_local=continuation.all_new_rows()[0]
    anchor = TheoremSpec("new_test_anchor", "0=0", (), ("refl",), "test syntax")
    if mutation.endswith("shadow"):
        original = {"alpha_shadow": inherited, "bottom_shadow": old_bottom, "lower_shadow": old_lower, "local_shadow": old_local}[mutation]
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
        bottom._lean_check(_checkpoint("finite-support"), 170, 169, payload)


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
    item = _checkpoint("finite-support")
    with pytest.raises(checkpoints.CheckpointError):
        bottom._lean_check(item, 170, 169, (ROOT / item.artifact).read_bytes())


@pytest.mark.parametrize("mutation", ("returncode", "reject", "nodes", "root", "path", "extra", "stderr", "timeout", "oserror"))
def test_rejecting_or_forged_lean_receipts_fail_closed_and_use_private_input(monkeypatch, mutation):
    item = _checkpoint("finite-support")
    payload = (ROOT / item.artifact).read_bytes()
    snapshots = []

    def reject(command, **kwargs):
        assert command[0] == str(bottom.LEAN_BINARY)
        snapshot = Path(command[1])
        snapshots.append(snapshot)
        assert snapshot != ROOT / item.artifact and snapshot.read_bytes() == payload
        assert snapshot.parent.stat().st_mode & 0o777 == 0o700
        assert kwargs == {"text": True, "capture_output": True, "timeout": 30, "check": False}
        expected = f"ACCEPT\t{snapshot}\tnodes=170\troot=169\n"
        if mutation == "timeout":
            raise subprocess.TimeoutExpired(command, 30)
        if mutation == "oserror":
            raise OSError("deliberately unavailable verifier")
        output = {
            "reject": "REJECT\n", "nodes": expected.replace("nodes=170", "nodes=1"),
            "root": expected.replace("root=169", "root=0"),
            "path": expected.replace(str(snapshot), "another-proof.json"),
            "extra": expected + "unrelated second receipt\n",
        }.get(mutation, expected)
        return SimpleNamespace(returncode=1 if mutation == "returncode" else 0,
                               stdout=output, stderr="unexpected diagnostics" if mutation == "stderr" else "")

    # The binary's real exact bytes are still checked.  Every stubbed result
    # rejects; there is intentionally no mocked positive receipt case.
    monkeypatch.setattr(bottom.subprocess, "run", reject)
    with pytest.raises(checkpoints.CheckpointError):
        bottom._lean_check(item, 170, 169, payload)
    assert len(snapshots) == 1 and not snapshots[0].exists()


def test_ha_failure_propagates_before_lean_or_any_ordinary_replay(monkeypatch):
    def reject(*args):
        raise checkpoints.closure.BottomLayerClosureError("deliberate HA rejection")

    monkeypatch.setattr(checkpoints.closure, "check_bottom_layer_bundle", reject)
    monkeypatch.setattr(bottom, "_lean_check", lambda *args: pytest.fail("HA failure reached Lean"))
    monkeypatch.setattr(checkpoints.closure, "replay_bottom_layer_theorem", lambda *args: pytest.fail("HA failure reached replay"))
    with pytest.raises(checkpoints.closure.BottomLayerClosureError, match="deliberate HA rejection"):
        checkpoints.verify_checkpoint(_checkpoint("finite-support"), ordinary_roots=True)


def test_lean_failure_prevents_any_ordinary_success_report(monkeypatch):
    def reject(*args):
        raise checkpoints.CheckpointError("deliberate independent rejection")

    monkeypatch.setattr(bottom, "_lean_check", reject)
    monkeypatch.setattr(checkpoints.closure, "replay_bottom_layer_theorem", lambda *args: pytest.fail("Lean failure reached replay"))
    with pytest.raises(checkpoints.CheckpointError, match="deliberate independent rejection"):
        checkpoints.verify_checkpoint(_checkpoint("finite-support"), ordinary_roots=True)


@pytest.mark.parametrize("principal_only", (False, True))
@pytest.mark.parametrize("mutation", ("open_hypothesis", "other_formula", "other_spec", "replay_failure"))
def test_ordinary_return_value_must_prove_the_literal_empty_context_statement(monkeypatch, mutation, principal_only):
    item = _checkpoint("finite-support")
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
        if principal_only:
            # No Lean claim is permitted in a single-root result. Real
            # positive certificates above were checked before being altered.
            checkpoints.verify_principal_root(item,spec.name)
        else:
            # Actual complete original HA and actual compiled Lean run first.
            checkpoints.verify_checkpoint(item, ordinary_roots=True)


@pytest.mark.parametrize('name',(None,False,0,'','add_comm','signed_zero_window_empty',
                                 'mobius_inversion_iff',('signed_prefix_sum_zero_tail',)))
def test_principal_only_api_rejects_nonprincipal_names_before_source_reads(monkeypatch,name):
    item=_checkpoint('finite-support')
    monkeypatch.setattr(checkpoints,'load_rows',lambda _:pytest.fail('invalid principal read mathematical sources'))
    with pytest.raises(checkpoints.CheckpointError,match='registered principal'):
        checkpoints.verify_principal_root(item,name)


def test_principal_only_api_performs_real_replay_but_makes_no_lean_or_admission_claim(monkeypatch):
    item=_checkpoint('finite-support')
    evidence=checkpoints.verify_checkpoint(item)  # Actual HA and actual compiled Lean.
    name,statement_sha=EXPECTED[item.slug]['roots'][0]
    monkeypatch.setattr(bottom,'_lean_check',lambda *args:pytest.fail('single-root API must not grant a separate Lean flag'))
    report=checkpoints.verify_principal_root(item,name)
    assert set(report)=={'slug','bundle_sha256','principal_roots'}
    assert report['slug']==item.slug and report['bundle_sha256']==item.artifact_sha256
    assert len(report['principal_roots'])==1
    record=report['principal_roots'][0]
    assert set(record)=={'name','node_id','statement_sha256','complete_ordinary_ha_checked','ordinary_certificate_nodes'}
    assert record['name']==name and record['statement_sha256']==statement_sha
    assert record['node_id']==next(row.node_id for row in evidence.plan.rows if row.name==name)
    assert record['complete_ordinary_ha_checked'] is True
    assert type(record['ordinary_certificate_nodes']) is int and record['ordinary_certificate_nodes']>1


def test_principal_only_rejects_a_genuinely_checked_conditional_body_as_a_complete_proof(monkeypatch):
    from peano_lab.kernel.formulas import Imp
    item=_checkpoint('finite-support')
    evidence=checkpoints.verify_checkpoint(item)  # Both real complete checkers run.
    name=item.principal_roots[0]
    spec=next(row for row in evidence.owned if row.name==name)
    position=next(row.node_id for row in evidence.plan.rows if row.name==name)
    node=evidence.bundle.nodes[position]
    assert node.dependencies
    conditional=node.target
    for dependency in reversed(node.dependencies):
        conditional=Imp(evidence.bundle.nodes[dependency].target,conditional)
    assert check((),node.body,conditional)
    assert not check((),node.body,_closed_formula(spec.statement))
    counterfeit=SimpleNamespace(spec=spec,formula=_closed_formula(spec.statement),certificate=node.body,proof_nodes=1)
    monkeypatch.setattr(checkpoints.closure,'replay_bottom_layer_theorem',lambda *args:counterfeit)
    with pytest.raises(checkpoints.CheckpointError,match='empty-context certificate'):
        checkpoints.verify_principal_root(item,name)


def test_principal_only_replay_retains_the_original_full_bundle_check(monkeypatch):
    item=_checkpoint('finite-support')
    def reject(*args):
        raise checkpoints.closure.BottomLayerClosureError('deliberate full-bundle rejection')
    monkeypatch.setattr(checkpoints.closure,'check_bottom_layer_bundle',reject)
    monkeypatch.setattr(checkpoints,'check',lambda *args:pytest.fail('full-bundle failure reached final check'))
    with pytest.raises(checkpoints.closure.BottomLayerClosureError,match='full-bundle rejection'):
        checkpoints.verify_principal_root(item,item.principal_roots[0])


def test_inventory_import_cannot_enroll_any_theorem_or_import_editions():
    program = (
        "import sys;sys.path[:0]=['scripts','peano-lab/py'];"
        "from constructive_dirichlet_checkpoints import all_new_rows;"
        "assert len(all_new_rows())==113;"
        "assert not any(name.startswith(('peano_lab.library.editions',"
        "'peano_lab.library.alpha_enrollment')) for name in sys.modules)"
    )
    subprocess.run([sys.executable, "-c", program], cwd=ROOT, check=True, timeout=45)
