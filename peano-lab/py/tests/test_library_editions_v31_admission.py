"""Artifact-free membership and real ordinary-proof v31 admission regressions."""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from hashlib import sha256
import os
from pathlib import Path
import random
import subprocess
import sys
from types import SimpleNamespace

import pytest

from peano_lab.kernel.checker import check
from peano_lab.kernel.formulas import Bot
from peano_lab.kernel.proofs import EqRefl, Hyp
from peano_lab.kernel.terms import Zero
from peano_lab.library import alpha_enrollment_v31 as a
from peano_lab.library import campaign_completed_lower_closure as c
from peano_lab.library import editions_v30 as parent
from peano_lab.library import editions_v31 as current
from peano_lab.library.editions_v5 import _enrollment_identity, _identity, _make_edition
from peano_lab.library.theorems import _closed_formula


ROOT = Path(__file__).resolve().parents[3]
SMALL = "dirichlet-signed-units"
PRINCIPAL = "dirichlet_signed_unit_product_classification"
EXPECTED_PRINCIPALS = {
    "euler_theorem_for_units": "fcfb262cc347ec2cd7624dffba31f9ed519292b3ba5f1669682cee308cbac39d",
    "euler_coprime_totient_power": "4f3533b3d207055a1f56ca77655cf26a381735fa3999f34a0a2c7935a21497e4",
    "prime_field_of_prime_order_exists": "f0a61089155f5bb6cd5e6fa79774756a296253a412e2b131bf8f491e8099b8a7",
    "mobius_value_exists_unique": "eb41094b2ceb2273e89e8966ced4cc921decf56dd6bc6dbcb5349c2087aa1135",
    "mobius_fresh_prime_negates": "2b0116e6d32e45fe7ae5e9a8bd7c11e5f95a88021cd42786276cff6e7ec303d2",
    "divisor_signed_table_reindex_exists": "f2cc667b787e62fe9e43a8689834b3edf048e4fe71b615639db1d2062d93f9f9",
    "divisor_signed_sum_permutation_invariant": "0e94ef4db7c6f73d73ae87525d29e24722764adabcd38a908ab3a844bfec57ac",
    "mobius_table_exists": "9d90a11bd987bfe516272671293b30a0d264fe613d2632c628b5701634cf5dd3",
    "signed_divisor_sum_positive_source_extensional": "5db775338790a36cdffa83a65f52f26d244827ba90942feb09600b9f5a202672",
    "signed_divisor_sum_exists_unique": "c148a766390471cd871ca467503a9a7c380142964aff8830ca412a20f743ba6d",
    "signed_weighted_sum_exists_unique": "1ed794504914ee8304903be9fce6c08e5e310c7b0e75c244382438433c4c3f14",
    "signed_weighted_sum_scalar_linearity": "488852252ab9e41daf5e2e6e234f8a9e046042f269dd9f5fd1bd9a074c45cbeb",
    "signed_weighted_sum_add_linearity": "0515fa77e429a50f266b273b77efa2682ec7cc78c3e30948559d6a5c3363f255",
    "prime_field_polynomial_horner_exists_unique": "b4e5a2cd91b33b7366aa11d591d5da743acdb244348f438797daf1be243c3941",
    "prime_field_polynomial_normalized_horner_iff": "fbed602c60a29f5b4474d678ccd397c2ff5d50e7fb52f06480c26e1938a762e5",
    "prime_field_polynomial_reduce_and_evaluate_exists": "2f0d67795bf12542c6c9fb48cb4d63d26213e8e090bbca1a7a89257a49dd0e2c",
    "positive_divisor_quotient_exists_unique": "a02a6f2e061e89191c7e4dff86b60611ebf035717468a17707bf5537486da384",
    "positive_divisor_involution_exists": "7fff4b15206b4bc27488134518c5e8231aee964a484e515576a6426be170719d",
    "divisor_complement_prefix_involution": "24bdefde49ebf80220bf5c974be3261d250dc98472d1228f6f3484492a9f34c1",
    "mobius_divisor_sum_cancellation": "dc605f677a0cdb931e7f3e65b29569dea83f1b9db136b932913a1936dc2b3406",
    "mobius_divisor_sum_cancellation_exists": "50bcf039c53ca70483eadd8ff3f9c3baf484d1fc82f84afe21009620ff674280",
    "mobius_divisor_sum_cancellation_on_positive_values": "be20bbedecba3566c7d3611f121e3d2e4fdaffd7fdee715dcd7e60afdb4cfd56",
    "signed_rectangular_slice_exists_extensionally_unique": "d0fbe7f70725333cc208f00e860d04886fafdc5fef4a36bc6e811dd88391ddd4",
    "signed_rectangular_fubini": "74787482d51c759b2472790323be3c54494bbf97fab08de48afce458898fd14d",
    "signed_rectangular_row_major_fubini": "df286640d573e43c4ce8fc84ed9a405eb4568577f4f683001adb7ae8324ff3ec",
    "prime_field_polynomial_convolution_exists_unique": "68befd01e16fc6522f2c848ddaac2bef81ead256b41bf6b03fbff132b7693410",
    "prime_field_polynomial_convolution_outside_zero": "724cc30193c104f03c1777ace6bec5f40681be6436e7da9f165d44d10cb97501",
    "prime_field_polynomial_convolution_represented_degree_exists": "8ff4406ec7462fc8e97a47932550abde9c428392cda01a1c86fe2dfd082fc51a",
    "signed_prefix_sum_zero_tail": "ae30d900f38f2fa5e22a59fe2a38056ffb4242b1fcb8ebf364c7673606f1d46b",
    "signed_prefix_sum_last_value": "d813ceef952a622bca2fb25909b732dc7c4f9987720b050a3c5a41b590690013",
    "signed_prefix_sum_zero_padding_iff": "0a6919b464fecaa0138aef0d8ce9f24d3e2f48357a29544523c17e67b3200f4e",
    "dirichlet_convolution_table_exists_extensionally_unique": "dd3b6ce98b1cda129a5105bc176ffbb4e7ca7d9549ea61a8ddcfc53a4a1ced13",
    "dirichlet_convolution_table_commutative": "bcbe8d62a9c065aa28bd6caf8450e86381156e555ae1b4bcc6067a08aa6bbb40",
    "dirichlet_convolution_padded_prefix_iff": "81ea53acd86ba6b094a55b9de9d69ee97c444f5a9f5eedfa3e5e6c9afcb9002e",
    "dirichlet_convolution_fubini_interchange": "52ec70863e39714463cce993fd232ffe99a1a5e0c5a97f0daecfe5b41ed8e3bd",
    "dirichlet_convolution_associative": "7963b56c370b9ff42ae43dc3e12d13dd36b6bd1dd356b62269a062a6a90d6738",
    "dirichlet_convolution_associative_tables_exists": "f0e95e4639f59cc7b592d82384c2cf72b63e594814599db6b7bf24339b35adc1",
    "dirichlet_delta_unit_exists": "6924256ebdc7a4a8b46c532d5808e5794dea1430b6d1892c764a826191b4d710",
    "dirichlet_constant_one_sum_iff": "f502d0a59a4eb50a35be7b76d39904729a96e3d6d5c91d4e019a6aad9639908f",
    "dirichlet_constant_one_realizes_divisor_sum": "5aafb1de83c084f4d86aef3f3649ebc962a43b64c55c7356c45500c8db072d09",
    "mobius_inversion_for_actual_mobius_table": "c69a34ea1a32d3d1188c00a95754507739ed77b953a355e2ffccf0ad69e21dab",
    "mobius_inversion_arithmetic_tables": "a0cacd2561b809b9cd7e9909fd37cbbcd7a60f086560bf1bd5a2fecad5c978b9",
    "mobius_inversion_iff": "c98dbac33cefe8835eb9c023fd942e6fcb998e7bb8ca0607989b462724a8cad1",
    "dirichlet_signed_unit_product_classification": "4c6820280f2a7c6e35eb66968d2f4819ea3276baa1af24e495ec1626e963db08",
    "dirichlet_signed_unit_affine_solve": "3c8f3184a683b282d0ef7f8d9f3671f71a9b9509599ff78b4ff47623c65660e4",
    "dirichlet_signed_unit_affine_unique": "68b300d496090f0911613338c333747776a606c71fd28d4c82849bfca1c32d11",
    "dirichlet_convolution_first_input_append_step": "0acd77c052775df9717c6c09715c733ab207c9fa18380b5e279222221a5f1404",
    "dirichlet_convolution_at_one_iff": "6f1888f04b4d2ac46a57cca07719bed191aa2c1e3fc6092ef671965cc8d6b956",
    "dirichlet_convolution_strict_prefix_exists": "745ac62f2fbed061d5ba9f77972361c063ec4020ed9e52144bd2a1b8a38b96d1",
    "dirichlet_unit_equation_construct": "cbb0fc99f0f2eb3e77871b21e4a8d5cfe01d22c86b737e77b516f4c060f8644e",
    "dirichlet_inverse_criterion": "8c777567eae9fae4a3b6f0e0df4e4d80205c694f5b15f93f1808376e1b7d05fc",
    "dirichlet_inverse_exists_positive_unique": "eb7703bdacfaca3d2d4a6c0cf5d2a43326be82107047a7609ce053da0fedd164",
}


@pytest.fixture(scope="module")
def actual_small():
    current.set_completed_lower_bundle_source(SMALL, None)
    bundle, receipt, positions = current.checked_completed_lower_bundle(SMALL)
    assert receipt.kernel_calls == receipt.node_count == 71
    proof = current.replay(PRINCIPAL, edition="alpha")
    assert proof.spec == current.ALPHA_EDITION.by_name[PRINCIPAL].spec
    assert proof.formula == _closed_formula(proof.spec.statement)
    assert check((), proof.certificate, proof.formula)
    yield bundle, receipt, positions, proof
    current.set_completed_lower_bundle_source(SMALL, None)


def test_all_parent_entries_and_every_stable_object_are_preserved():
    assert len(parent.ALPHA_ENTRIES) == 3222
    assert current.ALPHA_ENTRIES[:3222] == parent.ALPHA_ENTRIES
    assert all(new is old for new, old in zip(current.ALPHA_ENTRIES, parent.ALPHA_ENTRIES))
    assert current.STABLE_EDITION is parent.STABLE_EDITION
    assert current.STABLE_ENTRIES is parent.STABLE_ENTRIES
    assert current.STABLE_SPECS is parent.STABLE_SPECS
    assert current.STABLE_RELEASE_ORDER is parent.STABLE_RELEASE_ORDER
    assert len(current.STABLE_SPECS) == 432
    assert a.alpha_v31_enrollment().parent_entries is parent.ALPHA_ENTRIES


def test_actual_complete_edition_has_exact_count_graph_and_identity():
    assert len(current.ALPHA_ENTRIES) == len(current.ALPHA_CHECKED_SPECS) == 3796
    assert len(current.FRONTIER_NEW_NAMES) == 574
    assert current.ALPHA_EDITION.edge_count == 12248
    assert current.ALPHA_EDITION.layer_count == 53
    assert current.ALPHA_V31_ENROLLMENT_SHA256 == "e4f6330197152cab52427ea724c488390e1cd3bd50a77c09746161cb0d343768"
    assert current.ALPHA_V31_IDENTITY_SHA256 == "902fa75c2bf4624bb7fc5aca9a6c49b71ff8fa4499f8bdf9ce726cfd4166a5d7"
    assert current.ALPHA_CHECKED_SPECS == current.ALPHA_SPECS
    assert Counter(item.evidence for item in current.ALPHA_ENTRIES) == {
        current.EvidenceStatus.STABLE_CLOSED: 432, current.EvidenceStatus.ALPHA_CLOSED: 3364,
    }


def test_exact_frontier_ownership_and_every_dependency_is_earlier():
    e = a.alpha_v31_enrollment()
    assert len(e.frontier_specs) == 574
    assert sum(len(row.dependencies) for row in e.frontier_specs) == 1660
    assert sum(len(row.script) for row in e.frontier_specs) == 26004
    assert Counter(e.campaign_by_name.values()) == a.EXPECTED_CAMPAIGN_COUNTS
    assert tuple(row.name for row in e.frontier_specs) == c.FRONTIER_NEW_NAMES
    assert len(set(c.FRONTIER_NEW_NAMES)) == 574
    assert c._specs_digest(e.frontier_specs) == "9ce681cbca759fcc555f582158162e9ba9cb6dbed64b57274fca530435c8c994"
    seen = {item.spec.name for item in parent.ALPHA_ENTRIES}
    for row in e.frontier_specs:
        assert row.name not in seen and set(row.dependencies) <= seen
        assert current.ALPHA_EDITION.by_name[row.name].spec is row
        seen.add(row.name)
    assert len(seen) == 3796


@pytest.mark.parametrize("name,digest", EXPECTED_PRINCIPALS.items())
def test_every_principal_is_the_independently_pinned_exact_statement(name, digest):
    entry = current.ALPHA_EDITION.by_name[name]
    assert entry.checked_use
    assert sha256(entry.spec.statement.encode()).hexdigest() == digest
    assert a.ROOT_STATEMENT_SHA256[name] == digest


@pytest.mark.parametrize("owner", c.FACTORIES, ids=lambda f: f.module)
def test_all_factory_source_test_and_rfc_provenance_is_preserved(owner):
    e = a.alpha_v31_enrollment()
    names = tuple(name for name in current.FRONTIER_NEW_NAMES if e.source_by_name[name] == owner.source)
    assert len(names) == owner.count == a.EXPECTED_FACTORY_COUNTS[owner.module]
    assert a.EXPECTED_FACTORY_SOURCE_SHA256[owner.module] == owner.source_sha256
    for name in names:
        assert e.test_by_name[name] == owner.test
        assert e.rfc_by_name[name] == "research/arithmetic-library/" + owner.rfc
        assert e.campaign_by_name[name].value == owner.campaign
        assert current.ALPHA_EDITION.by_name[name].source_module == owner.source


@pytest.mark.parametrize("family", c.FAMILIES, ids=lambda f: f.slug)
def test_browser_paths_and_case_insensitive_lookup_are_exact(family):
    assert current.COMPLETED_LOWER_ARTIFACT_FILENAMES[family.slug] == Path(family.artifact).name
    assert current.PYODIDE_COMPLETED_LOWER_BUNDLE_PATHS[family.slug] == (
        "/lab/proof-artifacts/" + Path(family.artifact).name
    )
    name = family.owned_names[0]
    assert current.entry(" " + name.upper() + " ", edition=" AlPhA ") is current.ALPHA_EDITION.by_name[name]
    assert current.entry(name) is None


def test_new_rows_do_not_leak_to_stable_even_when_proof_sources_are_available():
    for name in current.FRONTIER_NEW_NAMES:
        assert current.entry(name, edition="stable") is None
    with pytest.raises(current.EditionV31ReplayError, match="unknown stable"):
        current.replay(PRINCIPAL, edition="stable")


@pytest.mark.parametrize("seed", range(8))
def test_streamed_identity_is_exact_old_serialization_including_escaping(seed):
    rng = random.Random(seed)
    samples = tuple(replace(
        rng.choice(current.ALPHA_ENTRIES), source_module='path/quote"\\line\nλ/' + str(i),
        spec=replace(rng.choice(current.ALPHA_SPECS),
                     summary="μ\tline\n" + chr(0x1c) + '"\\' + str(i)),
    ) for i in range(rng.randrange(0, 10)))
    assert current._stream_identity(current.EditionName.ALPHA, samples) == _identity(current.EditionName.ALPHA, samples)
    assert current._stream_enrollment_identity(samples) == _enrollment_identity(samples)


def test_streamed_edition_uses_identical_original_topology_and_entry_objects():
    entries = parent.ALPHA_ENTRIES[:20]
    streamed = current._make_streamed_edition(current.EditionName.ALPHA, entries)
    old = _make_edition(current.EditionName.ALPHA, entries)
    assert streamed == old and streamed.entries is entries
    assert all(streamed.by_name[name] is old.by_name[name] for name in old.by_name)


@pytest.mark.parametrize("field,value", (
    ("EXPECTED_ALPHA_V31_COUNT", 0), ("EXPECTED_ALPHA_V31_COUNT", 3797),
    ("EXPECTED_ALPHA_V31_CHECKED_USE_COUNT", 0), ("EXPECTED_ALPHA_V31_FRONTIER_COUNT", 0),
    ("EXPECTED_ALPHA_V31_IDENTITY_SHA256", ""), ("EXPECTED_ALPHA_V31_ENROLLMENT_SHA256", "0" * 64),
))
def test_unsealed_edition_metadata_cannot_advertise_alpha_but_stable_is_lazy(monkeypatch, field, value):
    monkeypatch.setattr(current, field, value)
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("metadata opened a file"))
    with pytest.raises(current.EditionV31ReplayError):
        current.require_completed_lower_seal()
    with pytest.raises(current.EditionV31ReplayError):
        current.edition("alpha")
    assert current.edition() is parent.STABLE_EDITION
    assert current.entry("zero_add") is parent.entry("zero_add")


@pytest.mark.parametrize("field,value", (
    ("EXPECTED_COMPLETED_LOWER_FAMILY_COUNT", 0),
    ("EXPECTED_COMPLETED_LOWER_FACTORY_COUNT", 0),
    ("EXPECTED_COMPLETED_LOWER_COUNT", 0),
    ("EXPECTED_COMPLETED_LOWER_EDGE_COUNT", 0),
    ("EXPECTED_COMPLETED_LOWER_COMMAND_COUNT", 0),
    ("EXPECTED_COMPLETED_LOWER_NAMES_SHA256", "0" * 64),
    ("EXPECTED_COMPLETED_LOWER_METADATA_SHA256", "0" * 64),
))
def test_unsealed_provider_metadata_blocks_alpha_without_loading_a_plan(monkeypatch, field, value):
    monkeypatch.setattr(c, field, value)
    monkeypatch.setattr(c, "completed_lower_plan", lambda *_a, **_k: pytest.fail("metadata loaded a plan"))
    monkeypatch.setattr(c, "read_completed_lower_bundle_bytes", lambda *_a, **_k: pytest.fail("metadata read an artifact"))
    with pytest.raises(current.EditionV31ReplayError):
        current.require_completed_lower_seal()
    assert current.edition() is parent.STABLE_EDITION


def test_seal_and_lookup_are_artifact_free_not_proof_authority(monkeypatch):
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("lookup opened a file"))
    monkeypatch.setattr(Path, "read_bytes", lambda *_a, **_k: pytest.fail("lookup read a file"))
    monkeypatch.setattr(c, "completed_lower_plan", lambda *_a, **_k: pytest.fail("lookup loaded a plan"))
    monkeypatch.setattr(current, "_checked_completed_lower_bundle", lambda *_a: pytest.fail("lookup invoked proof provider"))
    assert current.require_completed_lower_seal() is None
    assert current.entry(PRINCIPAL, edition="alpha").spec.name == PRINCIPAL
    assert current.entry("zero_add") is parent.entry("zero_add")


@pytest.mark.parametrize("field,value", (
    ("EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BYTES", 0),
    ("EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_SHA256", "0" * 64),
    ("EXPECTED_GAUSSIAN_FACTORIZATION_BUNDLE_BODY_PROOF_NODES", 0),
))
def test_current_alpha_preserves_parent_metadata_eligibility_without_artifact_reads(monkeypatch, field, value):
    from peano_lab.library import campaign_gaussian_factorization_closure as gaussian
    monkeypatch.setattr(gaussian, field, value)
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("parent seal opened a file"))
    monkeypatch.setattr(current, "checked_completed_lower_bundle", lambda *_a: pytest.fail("parent seal loaded proof"))
    with pytest.raises(current.EditionV31ReplayError, match="parent is not sealed"):
        current.require_completed_lower_seal()
    with pytest.raises(current.EditionV31ReplayError, match="parent is not sealed"):
        current.entry(PRINCIPAL, edition="alpha")
    assert current.edition() is parent.STABLE_EDITION
    assert current.entry("zero_add") is parent.entry("zero_add")


def test_real_stable_replay_delegates_without_touching_new_providers(monkeypatch):
    current.replay.cache_clear()
    calls = []
    original = parent.replay
    def recorded(name, *, edition):
        calls.append((name, edition))
        return original(name, edition=edition)
    monkeypatch.setattr(parent, "replay", recorded)
    monkeypatch.setattr(current, "checked_completed_lower_bundle", lambda *_: pytest.fail("Stable opened new proof"))
    checked = current.replay("zero_add", edition="stable")
    assert check((), checked.certificate, checked.formula)
    assert calls == [("zero_add", current.EditionName.STABLE)]
    current.replay.cache_clear()


def test_actual_complete_bundle_and_real_ordinary_certificate(actual_small):
    bundle, receipt, positions, proof = actual_small
    assert receipt.kernel_calls == len(bundle.nodes) == 71 and len(positions) == 70
    assert receipt.total_body_nodes == 4704 and receipt.dependency_edges == 146
    assert proof.proof_nodes == 2126
    assert proof.formula == bundle.nodes[positions[PRINCIPAL]].target
    assert check((), proof.certificate, proof.formula)
    with pytest.raises(TypeError):
        positions["invented"] = 0


def test_source_change_clears_checked_bundles_and_materialized_certificates(actual_small, tmp_path):
    current.checked_completed_lower_bundle(SMALL)
    current.replay(PRINCIPAL, edition="alpha")
    assert current._checked_completed_lower_bundle.cache_info().currsize == 1
    assert current.replay.cache_info().currsize == 1
    current.set_completed_lower_bundle_source(SMALL, tmp_path / "missing.json")
    try:
        assert current._checked_completed_lower_bundle.cache_info().currsize == 0
        assert current.replay.cache_info().currsize == 0
        with pytest.raises(current.EditionV31ReplayError):
            current.replay(PRINCIPAL, edition="alpha")
    finally:
        current.set_completed_lower_bundle_source(SMALL, None)


@pytest.mark.parametrize("slug", ("missing", "", None, 0, True, [SMALL]))
def test_invalid_family_source_setter_does_not_mutate_state(slug):
    before = dict(current._bundle_sources)
    with pytest.raises(current.EditionV31ReplayError):
        current.set_completed_lower_bundle_source(slug, "irrelevant")
    assert current._bundle_sources == before


@pytest.mark.parametrize("source", (0, True, object(), b"proof.json", []))
def test_invalid_source_type_cannot_invalidate_or_redirect_a_valid_provider(source):
    before = dict(current._bundle_sources)
    with pytest.raises(current.EditionV31ReplayError):
        current.set_completed_lower_bundle_source(SMALL, source)
    assert current._bundle_sources == before


@pytest.mark.parametrize("mutation", ("missing", "directory", "symlink", "truncate", "append", "poison"))
def test_changed_artifact_is_rejected_before_decode_kernel_or_parent_fallback(monkeypatch, tmp_path, mutation):
    family = c.completed_lower_family(SMALL)
    path = tmp_path / "changed.json"
    raw = (ROOT / family.artifact).read_bytes()
    if mutation == "directory":
        path.mkdir()
    elif mutation == "symlink":
        path.symlink_to(ROOT / family.artifact)
    elif mutation == "truncate":
        path.write_bytes(raw[:-1])
    elif mutation == "append":
        path.write_bytes(raw + b" ")
    elif mutation == "poison":
        path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
    monkeypatch.setattr(current, "decode_proof_bundle", lambda *_: pytest.fail("bad artifact was decoded"))
    monkeypatch.setattr(parent, "replay", lambda *_a, **_k: pytest.fail("bad new proof fell back to parent"))
    current.set_completed_lower_bundle_source(SMALL, path)
    try:
        with pytest.raises(current.EditionV31ReplayError):
            current.replay(PRINCIPAL, edition="alpha")
    finally:
        current.set_completed_lower_bundle_source(SMALL, None)


def test_short_browser_layout_resolves_only_the_explicit_proof_mount(monkeypatch):
    monkeypatch.setattr(current, "__file__", "/lab/peano_lab/library/editions_v31.py")
    monkeypatch.setattr(Path, "is_file", lambda *_: False)
    assert current._default_completed_lower_bundle_source(SMALL) == Path(
        "/lab/proof-artifacts/dirichlet-signed-units-proof-bundle-v1.json"
    )


def test_provider_and_ordinary_runtime_do_not_need_any_catalogue(actual_small, monkeypatch):
    from peano_lab.library import campaign_bottom_layer_closure as old
    from peano_lab.library import campaign_gaussian_factorization_closure as gaussian
    from peano_lab.library import campaign_lower_layer_closure as lower
    for module in (old, gaussian, lower):
        monkeypatch.setattr(module, "parent_snapshot", lambda: pytest.fail("runtime loaded a repository catalogue"))
    current.set_completed_lower_bundle_source(SMALL, None)
    checked = current.replay(PRINCIPAL, edition="alpha")
    assert check((), checked.certificate, checked.formula)


@pytest.mark.parametrize("mutation", ("none", "node_id", "target", "dependencies", "body", "missing_node", "root"))
def test_interning_is_untrusted_and_cannot_omit_or_rewire_proof_data(actual_small, monkeypatch, mutation):
    original = current.intern_layered_replay_bodies
    def altered(*args, **kwargs):
        result = original(*args, **kwargs)
        if mutation == "none":
            return None
        if mutation == "missing_node":
            return replace(result, nodes=result.nodes[:-1])
        if mutation == "root":
            return replace(result, root=0)
        nodes = list(result.nodes)
        position = next(i for i, node in enumerate(nodes) if node.dependencies)
        node = nodes[position]
        changes = {"node_id": {"node_id": 9999}, "target": {"target": Bot()},
                   "dependencies": {"dependencies": ()}, "body": {"body": Hyp(0)}}[mutation]
        nodes[position] = replace(node, **changes)
        return replace(result, nodes=tuple(nodes))
    monkeypatch.setattr(current, "intern_layered_replay_bodies", altered)
    current.replay.cache_clear()
    with pytest.raises((current.EditionV31ReplayError, ValueError)):
        current.replay(PRINCIPAL, edition="alpha")


@pytest.mark.parametrize("mutation", ("none", "open_hypothesis", "other_formula", "changed_target"))
def test_untrusted_materializer_never_substitutes_an_open_or_other_certificate(actual_small, monkeypatch, mutation):
    _, _, _, actual = actual_small
    if mutation == "none":
        forged = None
    elif mutation == "changed_target":
        forged = SimpleNamespace(target=Bot(), certificate=actual.certificate, proof_nodes=actual.proof_nodes)
    else:
        forged = SimpleNamespace(target=actual.formula, proof_nodes=1,
                                 certificate=Hyp(0) if mutation == "open_hypothesis" else EqRefl(Zero()))
    monkeypatch.setattr(current, "compile_gaussian_factorization_replay", lambda *_a, **_k: forged)
    current.replay.cache_clear()
    with pytest.raises(current.EditionV31ReplayError):
        current.replay(PRINCIPAL, edition="alpha")


def test_original_empty_context_recheck_is_mandatory(actual_small, monkeypatch):
    current.replay.cache_clear()
    original = current.check
    calls = []
    def observed(context, proof, target):
        calls.append((context, target))
        return original(context, proof, target)
    monkeypatch.setattr(current, "check", observed)
    actual = current.replay(PRINCIPAL, edition="alpha")
    assert calls and calls[-1] == ((), actual.formula)
    assert all(context == () for context, _ in calls)


def test_original_checker_rejection_is_never_replaced_by_receipts(actual_small, monkeypatch):
    monkeypatch.setattr(current, "check", lambda *_a, **_k: False)
    current.replay.cache_clear()
    with pytest.raises(current.EditionV31ReplayError):
        current.replay(PRINCIPAL, edition="alpha")


def test_proof_caches_are_single_family_and_single_certificate():
    assert current._checked_completed_lower_bundle.cache_info().maxsize == 1
    assert current.replay.cache_info().maxsize == 1


def test_cold_installed_runtime_is_artifact_free_and_imports_no_authoring_scripts():
    program = r"""
import resource,signal
resource.setrlimit(resource.RLIMIT_CPU,(170,175))
signal.alarm(180)
from pathlib import Path
import builtins,sys
original_open=Path.open
original_import=builtins.__import__
def guarded_open(path,*args,**kwargs):
    if "catalog" in path.name or "proof-bundle" in path.name:
        raise AssertionError("cold runtime opened an artifact/catalogue")
    return original_open(path,*args,**kwargs)
def guarded_import(name,*args,**kwargs):
    if name=="scripts" or name.startswith("scripts.") or name.startswith("constructive_"):
        raise AssertionError("cold runtime imported authoring scripts")
    return original_import(name,*args,**kwargs)
Path.open=guarded_open
builtins.__import__=guarded_import
from peano_lab.library import editions_v31 as v
v.require_completed_lower_seal()
assert len(v.ALPHA_CHECKED_SPECS)==3796 and len(v.STABLE_SPECS)==432
assert not any(name=="scripts" or name.startswith("scripts.") for name in sys.modules)
assert v._checked_completed_lower_bundle.cache_info().currsize==0
assert v.replay.cache_info().currsize==0
peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
if sys.platform!="darwin":
    peak*=1024
assert peak<=1536*1024*1024
print("artifact-free installed v31 PASS")
"""
    result = subprocess.run([sys.executable, "-c", program], cwd=ROOT,
                            env=dict(os.environ, PYTHONPATH=str(ROOT / "peano-lab/py")),
                            text=True, capture_output=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "artifact-free installed v31 PASS"
