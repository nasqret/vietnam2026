"""Independent exact-inventory and hostile-proof tests for the v34 provider.

Saved checkpoints are authoring references only. The positive proof test below
checks actual frozen bytes with the original HA kernel; no mocked acceptance.
"""

from __future__ import annotations

from dataclasses import replace
from functools import lru_cache
from hashlib import sha256
from importlib import import_module
from pathlib import Path
import sys

import resource
import signal
import time

_BOUNDED_STARTED = time.monotonic()
if __name__ == "__main__":
    resource.setrlimit(resource.RLIMIT_CPU, (170, 175))
    signal.alarm(180)

import pytest

from peano_lab.kernel import checker as kernel_checker
from peano_lab.kernel.formulas import Bot
from peano_lab.kernel.proofs import Hyp
from peano_lab.library import campaign_research_v34_closure as c
from peano_lab.library.proof_bundle import (
    DEFAULT_BUNDLE_LIMITS, ProofBundleError, decode_proof_bundle,
)
from peano_lab.library.theorems import _closed_formula


ROOT = Path(__file__).resolve().parents[3]
SMALL = "congruence-arithmetic"
# Final literal artifact/body/metadata values are set only after genuine authoring.
EXPECTED_CONGRUENCE_BODY_NODES = 13079
EXPECTED_METADATA_SHA256 = "52e939652f8ea66d6ad6511dcaa534f95e5aaef86f69423eb2f2effd2106ea8f"
EXPECTED_INVENTORY = (("polynomial-gcd-bezout", 119, 493, 1578, 47545),
                      ("congruence-arithmetic", 12, 215, 647, EXPECTED_CONGRUENCE_BODY_NODES))
TRUSTED_SOURCE_SHA256 = {
    "peano-lab/py/peano_lab/library/editions_v32.py": "69707c34aed369163cc0cce95db7e6078302fe639df75210176e9b53ab719785",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v32.py": "81003d179548d50417ef093e1e7c6fc1006ec72ff06f39d1e0a47e56335172c6",
    "peano-lab/py/peano_lab/library/campaign_research_v32_closure.py": "cdbc803669fc35c0d8b91e06f5f79d1470ffc2355e041fc12c205ec21dfb3ea0",
    "peano-lab/py/peano_lab/library/editions_v31.py": "24fedcd8a492578f9a1e32bdd984693bd8e27216105000f719188a3a38200870",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v31.py": "7106c15b7196ca70d4bd62a4708696bd38e9b4eee07a127844c2d8398cd6e81b",
    "peano-lab/py/peano_lab/library/campaign_completed_lower_closure.py": "9aec583406e6b890fdd626cb60ecf8de4271581e20e86e1aa8499a4b1701dab3",
    "peano-lab/py/peano_lab/kernel/checker.py": "d7dfb9c256214695b9b7c427afb3b22291b9659b15defb16c57751b536a02ebe",
    "peano-lab/py/peano_lab/kernel/formulas.py": "b449bf50c7c8f6a93ff0dea067d9cfb048b3033f4e761e61c71d55e4f9a57645",
    "peano-lab/py/peano_lab/kernel/proofs.py": "1ff7c055e64f784b45f00488b00fe945a57e4d872e520382da779d1d775f28f2",
    "peano-lab/py/peano_lab/kernel/terms.py": "f49313e209a8861918e3aaca38ddfb27f147f824308af699ab5cc1aafbb6dff5",
    "peano-lab/py/peano_lab/library/proof_bundle.py": "55e91347bc0207e75b89ee25c31bdf8d65b24e19c7252bba4fe14ec537af4ef4",
    "peano-lab/py/peano_lab/library/layered_replay.py": "7c8b14b95ab76fe10f265a10271fd58f779fab3b7524c8f9002884b753b2badf",
    "peano-lab/py/peano_lab/library/formula_dag.py": "3dfd0ad9ec3270cb2cd40948b62f223ba9e5f7284152c823405d8002b7a1a45f",
    "peano-lab/py/peano_lab/library/campaign_gaussian_factorization_closure.py": "68af15379776c0cb36125c1d2f24e7c87b98880a7caad24725453937b864ac3e",
    "peano-lab/py/peano_lab/library/campaign_lower_layer_closure.py": "d7b31c8511d4439e1a2075cba718b2cba0fd7ea42a07c2ffb41d55dd7e75542c",
    "peano-lab/py/peano_lab/library/campaign_bottom_layer_closure.py": "e4d6f74feabf16ac342c9bfb875a39d060f5b97039866ae3a0a5fea99db84477",
    "peano-lab/py/peano_lab/library/editions_v30.py": "88499fde8ae5b19be5fea2d2d88d3ab56c0a27901abdbf6f005c16a0c1c1328f",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v30.py": "ca61a5efa17c8624c29ad3388c97743947a81f648e7f1aeeef848833cd484bac",
}
# Additional immutable v33 pins; the original historical block above is exact.
TRUSTED_SOURCE_SHA256.update({
    "peano-lab/py/peano_lab/library/editions_v33.py": "0fc82d543205064c2fb7a85c1fef5201d615c019b83df48b899b26b8b04482be",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v33.py": "8b41037d09e063c2dc8913fb0626cb804e6d0c69296663fd129aad2748609c0e",
    "peano-lab/py/peano_lab/library/campaign_research_v33_closure.py": "36d5c62b55f8453f08d8129c055ced6fd0b303f4ecb1877cc8532d1db2ee950c"
})
CANONICAL_SOURCE_PINS = (
    ("prime_field_polynomial_shift_candidate", "research/arithmetic-library/working/prime-field-shift-v1/prime_field_polynomial_shift_candidate.py", 15, 29786, "325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b"),
    ("prime_field_polynomial_scalar_convolution_candidate", "research/arithmetic-library/working/prime-field-scalar-v1/prime_field_polynomial_scalar_convolution_candidate.py", 10, 23637, "e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e"),
    ("prime_field_polynomial_append_candidate", "research/arithmetic-library/working/prime-field-append-v1/prime_field_polynomial_append_candidate.py", 6, 28396, "271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042"),
    ("prime_field_polynomial_shift_equivalence_candidate", "research/arithmetic-library/working/prime-field-shift-equivalence-v1/prime_field_polynomial_shift_equivalence_candidate.py", 1, 6021, "8846224923876a4f57ad8d6f31020838ccc86c86a683ec78a7c7c23c35b92068"),
    ("prime_field_polynomial_associativity_step_candidate", "research/arithmetic-library/working/prime-field-associativity-step-v1/prime_field_polynomial_associativity_step_candidate.py", 3, 26607, "dd85dbd1bd87143715a4286724ac7c87f280a909dac6759f00a6cb7dff7c85f1"),
    ("prime_field_polynomial_associativity_induction_candidate", "research/arithmetic-library/working/prime-field-associativity-induction-v1/prime_field_polynomial_associativity_induction_candidate.py", 2, 9924, "8d276a028764cd08e6eaebbf25bb4e21fcd5076a610d356a77d52ba6603ebe4c"),
    ("prime_field_polynomial_divisibility_candidate", "research/arithmetic-library/working/prime-field-divisibility-v1/prime_field_polynomial_divisibility_candidate.py", 7, 15168, "f544adedd3ce963e4a773e8582efcb0f91ba7491207c9792d477d452e854f2b8"),
    ("prime_field_polynomial_left_unit_candidate", "research/arithmetic-library/working/prime-field-left-unit-v1/prime_field_polynomial_left_unit_candidate.py", 8, 16858, "dbb8debb4716b6bb9b246700f7e93865c8a6c1b12a3b65c0ffbb62206a890ba6"),
    ("prime_field_polynomial_alignment_candidate", "research/arithmetic-library/working/prime-field-alignment-v1/prime_field_polynomial_alignment_candidate.py", 7, 11780, "eb16e2eb02dbd66a7706e616388182992b8cf2e0715818dc1f7748938e7d798e"),
    ("prime_field_polynomial_aligned_add_candidate", "research/arithmetic-library/working/prime-field-aligned-add-v1/prime_field_polynomial_aligned_add_candidate.py", 9, 20704, "a05bb4f5c4230ca05f51690d3ab82e33ff4596af65176874e25fbe38cf87a0db"),
    ("prime_field_polynomial_aligned_algebra_candidate", "research/arithmetic-library/working/prime-field-aligned-algebra-v1/prime_field_polynomial_aligned_algebra_candidate.py", 4, 16013, "a68de84439afb5f6dd87f1d47449c0bce8dd53a66346c00cc1b7645fb80b2390"),
    ("prime_field_polynomial_euclidean_identity_candidate", "research/arithmetic-library/working/prime-field-euclidean-identity-v1/prime_field_polynomial_euclidean_identity_candidate.py", 2, 11235, "8efdcd2abf2143891b79edcb3fc90d7126ae69507c1c631ed33b497172ffdb77"),
    ("prime_field_polynomial_aligned_distributivity_candidate", "research/arithmetic-library/working/prime-field-aligned-distributivity-v1/prime_field_polynomial_aligned_distributivity_candidate.py", 2, 8518, "7d535939e24fe6d82158c485533b2ff6934f4d897b6141fde6c50b4fec9788ba"),
    ("prime_field_polynomial_left_constant_candidate", "research/arithmetic-library/working/prime-field-left-constant-v1/prime_field_polynomial_left_constant_candidate.py", 6, 17620, "9a7a4de30f5f389bcabc2e6267a0d2cc5dc5f061059dcea303a0a03dab58509a"),
    ("prime_field_polynomial_euclidean_normalization_candidate", "research/arithmetic-library/working/prime-field-euclidean-normalization-v1/prime_field_polynomial_euclidean_normalization_candidate.py", 5, 16401, "d2cddfe42dc0d22104dc4e85e95116222914df11ac840d2082a4ff2e462f146f"),
    ("prime_field_polynomial_euclidean_transport_candidate", "research/arithmetic-library/working/prime-field-euclidean-transport-v1/prime_field_polynomial_euclidean_transport_candidate.py", 5, 18256, "9a589d1749eb38d30d1a24364bc4d66f7df0efb59247527f7831f97557da9c30"),
    ("prime_field_polynomial_bezout_backward_candidate", "research/arithmetic-library/working/prime-field-bezout-backward-v1/prime_field_polynomial_bezout_backward_candidate.py", 3, 18747, "c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702"),
    ("prime_field_polynomial_gcd_bezout_laws_candidate", "research/arithmetic-library/working/prime-field-gcd-bezout-laws-v1/prime_field_polynomial_gcd_bezout_laws_candidate.py", 4, 15300, "76b90226e5e29fdde3d9bb49accccf8d9b4c0cc17a4de406af253e999102533c"),
    ("prime_field_polynomial_gcd_existence_candidate", "research/arithmetic-library/working/prime-field-gcd-existence-v1/prime_field_polynomial_gcd_existence_candidate.py", 9, 26480, "81f2f48dd2e81894c7a267453646eb6f2b6f9bd3ee320386d8c561f6b9f8b8ca"),
    ("prime_field_polynomial_gcd_uniqueness_candidate", "research/arithmetic-library/working/prime-field-gcd-uniqueness-v1/prime_field_polynomial_gcd_uniqueness_candidate.py", 11, 31432, "916c24ad6c59609612e97daee6e49347a9522cdb28b44f6f09c6c5760bff0b5b"),
    ("linear_congruence_classification_candidate", "research/arithmetic-library/working/linear-congruence-classification-v1/linear_congruence_classification_candidate.py", 12, 18128, "12b1a98ce830704485f1ea78475fba8b10e39031ffbef00b1b5dfc8ffdef7f47"),
)


def _parent():
    # Deliberately lazy: pure source/registration checks need no Alpha import.
    from peano_lab.library import editions_v33
    return editions_v33


@pytest.fixture(scope="module")
def small_syntax():
    family = c.research_family(SMALL)
    payload = c.read_research_bundle_bytes(SMALL, ROOT / family.artifact)
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    return bundle, target


def test_exact_two_families_and_twenty_one_canonical_factories():
    assert type(EXPECTED_CONGRUENCE_BODY_NODES) is int
    assert tuple((f.slug, f.count, f.node_count, f.bundle_edges, f.body_nodes)
                 for f in c.FAMILIES) == EXPECTED_INVENTORY
    assert len(c.FACTORIES) == 21 and len(c.FAMILY_BY_NAME) == 131
    assert sum(f.edge_count for f in c.FAMILIES) == 604
    assert sum(f.command_count for f in c.FAMILIES) == 12869
    assert type(EXPECTED_METADATA_SHA256) is str
    assert c._metadata_digest() == EXPECTED_METADATA_SHA256


def test_both_family_contracts_use_exact_canonical_repository_paths():
    assert tuple(family.rfc for family in c.FAMILIES) == (
        "research/arithmetic-library/prime-field-polynomial-gcd-bezout-rfc-v1.md",
        "research/arithmetic-library/linear-congruence-classification-rfc-v1.md",
    )
    for family in c.FAMILIES:
        path = ROOT / family.rfc
        assert path.is_file() and not path.is_symlink()
        assert all(owner.rfc == path.name for owner in c.FACTORIES
                   if owner.campaign == family.slug)


def test_canonical_registration_matches_frozen_sources_without_loading_old_aliases():
    family = c.FAMILIES[0]
    assert family.specs_sha256 == "72701944f71e8d93c55bcf29d27fc92ac616452801ab75c3e478df4d77df4c38"
    assert (family.artifact_bytes, family.artifact_sha256) == (
        5193292, "3fe18ad2899cff7db5fbe19df8570ef70b1bfb902171d5212e9b036dda660a46")
    assert family.research_checkpoint_slug == "working-polynomial-gcd119"
    assert family.modules == tuple(row[0] for row in CANONICAL_SOURCE_PINS[:20])
    for module, original, count, size, digest in CANONICAL_SOURCE_PINS:
        owner = c.FACTORY_BY_MODULE[module]
        old = (ROOT / original).read_bytes()
        canonical = (ROOT / owner.source).read_bytes()
        assert old == canonical and (len(old), sha256(old).hexdigest()) == (size, digest)
        assert owner.count == count and owner.source_bytes == size and owner.source_sha256 == digest
        assert owner.factory == "make_" + module + "_theorems"
        assert owner.test == "peano-lab/py/tests/test_campaign_research_v34_closure.py"
    rows = c.research_specs()
    assert tuple(row.name for row in rows) == c.FRONTIER_NEW_NAMES and len(rows) == 131
    assert c._specs_digest(rows[:119]) == family.specs_sha256
    assert c._specs_digest(rows[119:]) == c.FAMILIES[1].specs_sha256
    assert not any(name.startswith(("working_gcd_", "working_euclidean_", "_working_gcd_",
                                    "working_linear_congruence_")) for name in sys.modules)


@pytest.mark.parametrize("owner", c.FACTORIES, ids=lambda f: f.module)
def test_every_mathematical_source_is_byte_exact_and_bounded(owner):
    path = ROOT / owner.source
    raw = c._read_pinned(path, owner.source_bytes, owner.source_sha256, maximum=c.MAX_SOURCE_BYTES)
    assert sha256(raw).hexdigest() == owner.source_sha256
    assert len(raw) == owner.source_bytes <= 2 * 1024 * 1024


@pytest.mark.parametrize("path,digest", TRUSTED_SOURCE_SHA256.items())
def test_original_kernel_limits_and_historical_providers_unchanged(path, digest):
    assert sha256((ROOT / path).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize("family", c.FAMILIES, ids=lambda f: f.slug)
def test_actual_complete_cone_has_no_missing_or_recounted_support(family):
    plan = c.research_plan(family.slug, parent_specs=_parent().ALPHA_CHECKED_SPECS)
    assert len(plan.rows) == family.theorem_count
    assert plan.owned_names == family.owned_names
    assert tuple(row.name for row in plan.rows if row.is_owned) == family.owned_names
    assert len(plan.positions) == len(plan.rows)
    assert plan.root_names == family.root_names
    assert set(plan.root_names) <= set(plan.owned_names)
    assert plan.dependency_edge_count == family.dependency_edges
    assert plan.ordered_names_sha256 == family.ordered_cone_names_sha256
    assert plan.frontier_specs_sha256 == family.complete_non_alpha_specs_sha256
    assert tuple(row.name for row in plan.rows) == family.ordered_cone_names
    assert c._specs_digest(plan.specs) == family.complete_specs_sha256
    seen = set()
    for row, spec in zip(plan.rows, plan.specs, strict=True):
        assert row.node_id == len(seen)
        assert row.name == spec.name and row.dependencies == spec.dependencies
        assert set(row.dependencies) <= seen
        assert row.statement_sha256 == sha256(spec.statement.encode()).hexdigest()
        assert row.is_owned == (row.name in family.owned_names)
        assert row.campaign == (c.FAMILY_BY_NAME[row.name].slug if row.name in c.FAMILY_BY_NAME else None)
        seen.add(row.name)
    pending, reachable = list(plan.root_names), set()
    specs = {row.name: row for row in plan.specs}
    while pending:
        name = pending.pop()
        if name not in reachable:
            reachable.add(name)
            pending.extend(specs[name].dependencies)
    assert reachable == seen
    with pytest.raises(TypeError):
        plan.positions["invented"] = 0


def test_actual_artifact_is_the_exact_preserved_119_working_bytes():
    family = c.FAMILIES[0]
    raw = c.read_research_bundle_bytes(family.slug, ROOT / family.artifact)
    archived = (ROOT / "research/arithmetic-library/working/prime-field-gcd-closure-v1/artifacts/working-gcd-closure-prefix-119-proof-bundle-v1.json").read_bytes()
    assert raw == archived
    assert len(raw) == 5193292
    assert sha256(raw).hexdigest() == "3fe18ad2899cff7db5fbe19df8570ef70b1bfb902171d5212e9b036dda660a46"


def test_actual_congruence_artifact_is_the_exact_preserved_12_working_bytes():
    family = c.research_family(SMALL)
    raw = c.read_research_bundle_bytes(SMALL, ROOT / family.artifact)
    archived = (ROOT / "research/arithmetic-library/working/linear-congruence-classification-v1/artifacts/working-linear-congruence-prefix-12-proof-bundle-v1.json").read_bytes()
    assert raw == archived and len(raw) == 542092
    assert sha256(raw).hexdigest() == "983051afddc637a4e033546b8f3ddb8dc0ac22aa996b4e28b3822be8895576ad"


@pytest.mark.parametrize("slug", ("", "missing", "CONGRUENCE-ARITHMETIC", "../congruence-arithmetic", None, 1, True, (SMALL,)))
def test_unknown_or_malformed_family_is_rejected_before_files(monkeypatch, slug):
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("invalid selection opened a file"))
    with pytest.raises(c.ResearchClosureError):
        c.research_family(slug)


@pytest.mark.parametrize("mutation", ("count", "order", "statement", "summary", "script", "name", "dependency", "list", "object", "duplicate"))
def test_every_supplied_parent_field_is_exact(mutation):
    rows = _parent().ALPHA_CHECKED_SPECS
    if mutation == "count":
        altered = rows[:-1]
    elif mutation == "order":
        altered = rows[1:] + rows[:1]
    elif mutation == "list":
        altered = list(rows)
    elif mutation == "object":
        altered = (object(),) + rows[1:]
    elif mutation == "duplicate":
        altered = rows[:1] + rows[:1] + rows[2:]
    else:
        changes = {"statement": "0 = 1", "summary": "altered", "script": ("refl",),
                   "name": "altered", "dependency": ("invented",)}
        key = "dependencies" if mutation == "dependency" else mutation
        altered = (replace(rows[0], **{key: changes[mutation]}),) + rows[1:]
    with pytest.raises(c.ResearchClosureError):
        c._parent_specs(altered)


@pytest.mark.parametrize("field,value", (
    ("artifact_bytes", 0), ("artifact_bytes", True), ("artifact_bytes", 64_000_001),
    ("artifact_sha256", ""), ("artifact_sha256", "0" * 64), ("artifact", "../escape.json"),
    ("count", 0), ("specs_sha256", "0" * 64), ("names_sha256", "0" * 64),
    ("node_count", 0), ("dependency_edges", 0), ("body_nodes", 0),
    ("owned_names", ()), ("principal_roots", ()), ("root_names", ()),
    ("modules", ()), ("research_checkpoint_slug", "not-the-old-slug"), ("edge_count", 1),
    ("complete_non_alpha_specs_sha256", "0" * 64),
    ("ordered_cone_names", ()), ("ordered_cone_names_sha256", "0" * 64),
    ("complete_specs_sha256", "0" * 64),
))
def test_every_family_metadata_change_fails_before_source_or_proof_use(monkeypatch, field, value):
    changed = (replace(c.FAMILIES[0], **{field: value}),) + c.FAMILIES[1:]
    monkeypatch.setattr(c, "FAMILIES", changed)
    monkeypatch.setattr(c, "RESEARCH_FAMILIES", changed)
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("bad metadata opened a source"))
    with pytest.raises(c.ResearchClosureError):
        c.validate_research_metadata()


@pytest.mark.parametrize("field,value", (
    ("module", "../escape"), ("factory", "other"), ("rfc", "../bad-rfc-v1.md"),
    ("source_bytes", 0), ("source_bytes", 2 * 1024 * 1024 + 1),
    ("source_sha256", "0" * 64), ("specs_sha256", "0" * 64), ("count", 1),
    ("test_filename", "../escape.py"), ("test_filename", "test_invented.py"),
))
def test_every_factory_metadata_change_is_rejected(monkeypatch, field, value):
    monkeypatch.setattr(c, "FACTORIES", (replace(c.FACTORIES[0], **{field: value}),) + c.FACTORIES[1:])
    with pytest.raises(c.ResearchClosureError):
        c.validate_research_metadata()


@pytest.mark.parametrize("mutation", ("count", "name", "statement", "dependencies", "script", "summary", "order", "type"))
def test_poisoned_factory_cannot_reuse_old_source_hash_as_authority(monkeypatch, mutation):
    owner = c.FACTORIES[0]
    module = import_module("peano_lab.library." + owner.module)
    original = getattr(module, owner.factory)
    rows = tuple(original(__import__("peano_lab.library.theorems", fromlist=["TheoremSpec"]).TheoremSpec))
    if mutation == "count":
        changed = rows[:-1]
    elif mutation == "order":
        changed = tuple(reversed(rows))
    elif mutation == "type":
        changed = (object(),) + rows[1:]
    else:
        values = {"name": "invented", "statement": "0 = 1", "dependencies": ("invented",),
                  "script": ("refl",), "summary": "altered"}
        changed = (replace(rows[0], **{mutation: values[mutation]}),) + rows[1:]
    c.clear_research_metadata_cache()
    def poisoned(_spec):
        return changed
    poisoned.__module__ = module.__name__
    monkeypatch.setattr(module, owner.factory, poisoned)
    try:
        with pytest.raises(c.ResearchClosureError):
            c.research_specs()
    finally:
        c.clear_research_metadata_cache()


@pytest.mark.parametrize("mutation", ("missing", "directory", "symlink", "truncate", "append", "same_size_poison"))
def test_invalid_proof_file_fails_before_decoding(tmp_path, mutation):
    family = c.research_family(SMALL)
    raw = (ROOT / family.artifact).read_bytes()
    path = tmp_path / "proof.json"
    if mutation == "directory":
        path.mkdir()
    elif mutation == "symlink":
        path.symlink_to(ROOT / family.artifact)
    elif mutation == "truncate":
        path.write_bytes(raw[:-1])
    elif mutation == "append":
        path.write_bytes(raw + b" ")
    elif mutation == "same_size_poison":
        path.write_bytes(bytes((raw[0] ^ 1,)) + raw[1:])
    with pytest.raises(c.ResearchClosureError):
        c.read_research_bundle_bytes(SMALL, path)


def test_bounded_reader_never_calls_unbounded_read(monkeypatch):
    family = c.research_family(SMALL)
    original = Path.open
    calls = []
    class Reader:
        def __init__(self, handle):
            self.handle = handle
        def __enter__(self):
            return self
        def __exit__(self, *args):
            self.handle.close()
        def read(self, size=-1):
            calls.append(size)
            assert size == family.artifact_bytes + 1
            return self.handle.read(size)
    monkeypatch.setattr(Path, "open", lambda path, *args, **kwargs: Reader(original(path, *args, **kwargs)))
    raw = c.read_research_bundle_bytes(SMALL, ROOT / family.artifact)
    assert calls == [family.artifact_bytes + 1] and len(raw) == family.artifact_bytes


@pytest.mark.parametrize("size", (0, -1, True, 64_000_001, 1.0))
def test_invalid_size_never_opens_file(monkeypatch, size):
    monkeypatch.setattr(Path, "open", lambda *_a, **_k: pytest.fail("invalid bound opened a file"))
    with pytest.raises(c.ResearchClosureError):
        c._read_pinned(Path("missing"), size, "a" * 64, maximum=64_000_000)


def test_frozen_metadata_and_explicit_parent_need_no_catalog_or_artifact(monkeypatch):
    from peano_lab.library import campaign_bottom_layer_closure as old
    monkeypatch.setattr(old, "parent_snapshot", lambda: pytest.fail("runtime read a catalogue"))
    monkeypatch.setattr(c, "read_research_bundle_bytes", lambda *_a, **_k: pytest.fail("plan loaded proof bytes"))
    plan = c.research_plan(SMALL, parent_specs=_parent().ALPHA_CHECKED_SPECS)
    assert len(plan.rows) == 214 and len(plan.owned_names) == 12


def test_real_complete_bundle_checks_every_actual_body_in_original_empty_context(small_syntax, monkeypatch):
    bundle, target = small_syntax
    original = kernel_checker.check
    calls = []
    def observed(context, proof, conclusion):
        calls.append((context, proof, conclusion))
        return original(context, proof, conclusion)
    monkeypatch.setattr(kernel_checker, "check", observed)
    receipt = c.check_research_proof_bundle(SMALL, bundle, target, parent_specs=_parent().ALPHA_CHECKED_SPECS)
    assert receipt.kernel_calls == receipt.node_count == len(calls) == 215
    assert receipt.total_body_nodes == EXPECTED_CONGRUENCE_BODY_NODES and receipt.dependency_edges == 647
    assert all(context == () for context, _, _ in calls)
    assert all(proof is node.body for (_, proof, _), node in zip(calls, bundle.nodes, strict=True))


@pytest.mark.parametrize("mutation", (
    "missing_node", "duplicate_node", "reverse_nodes", "root", "boolean_root",
    "target", "node_target", "node_id", "boolean_node_id", "remove_dependency",
    "poison_dependency", "reverse_dependencies", "boolean_dependency",
    "packaging_target", "packaging_body", "packaging_dependencies",
    "tuple_type", "node_type",
))
def test_exact_graph_target_order_and_packaging_fail_before_kernel(small_syntax, monkeypatch, mutation):
    bundle, target = small_syntax
    nodes = list(bundle.nodes)
    selected = next(i for i, node in enumerate(nodes[:-1]) if len(node.dependencies) >= 2)
    if mutation == "missing_node":
        changed = replace(bundle, nodes=tuple(nodes[:-1]))
    elif mutation == "duplicate_node":
        changed = replace(bundle, nodes=tuple(nodes) + (nodes[0],))
    elif mutation == "reverse_nodes":
        changed = replace(bundle, nodes=tuple(reversed(nodes)))
    elif mutation in {"root", "boolean_root"}:
        changed = replace(bundle, root=0 if mutation == "root" else True)
    elif mutation == "target":
        changed, target = bundle, Bot()
    elif mutation == "tuple_type":
        changed = replace(bundle, nodes=nodes)
    else:
        if mutation == "node_target":
            nodes[selected] = replace(nodes[selected], target=Bot())
        elif mutation == "node_id":
            nodes[selected] = replace(nodes[selected], node_id=999)
        elif mutation == "boolean_node_id":
            nodes[0] = replace(nodes[0], node_id=False)
        elif mutation == "remove_dependency":
            nodes[selected] = replace(nodes[selected], dependencies=nodes[selected].dependencies[:-1])
        elif mutation == "poison_dependency":
            nodes[selected] = replace(nodes[selected], dependencies=(999,) + nodes[selected].dependencies[1:])
        elif mutation == "reverse_dependencies":
            nodes[selected] = replace(nodes[selected], dependencies=tuple(reversed(nodes[selected].dependencies)))
        elif mutation == "boolean_dependency":
            i = next(i for i, node in enumerate(nodes[:-1]) if 0 in node.dependencies)
            nodes[i] = replace(nodes[i], dependencies=tuple(False if d == 0 else d for d in nodes[i].dependencies))
        elif mutation == "packaging_target":
            nodes[-1] = replace(nodes[-1], target=Bot())
        elif mutation == "packaging_body":
            nodes[-1] = replace(nodes[-1], body=Hyp(0))
        elif mutation == "packaging_dependencies":
            nodes[-1] = replace(nodes[-1], dependencies=nodes[-1].dependencies[:-1])
        elif mutation == "node_type":
            nodes[0] = object()
        changed = replace(bundle, nodes=tuple(nodes))
    monkeypatch.setattr(c, "check_proof_bundle", lambda *_a, **_k: pytest.fail("bad graph reached proof checker"))
    with pytest.raises(c.ResearchClosureError):
        c.check_research_proof_bundle(SMALL, changed, target, parent_specs=_parent().ALPHA_CHECKED_SPECS)


@pytest.mark.parametrize("which", ("inherited", "owned", "open_own", "DNE"))
def test_false_or_open_bodies_reach_and_fail_original_kernel(small_syntax, which):
    bundle, target = small_syntax
    plan = c.research_plan(SMALL, parent_specs=_parent().ALPHA_CHECKED_SPECS)
    position = next(row.node_id for row in plan.rows if row.is_owned) if which != "inherited" else 0
    body = Hyp(0)
    if which == "DNE":
        from peano_lab.kernel.proofs import DNE
        body = DNE(Bot())
    nodes = list(bundle.nodes)
    nodes[position] = replace(nodes[position], body=body)
    with pytest.raises((ProofBundleError, c.ResearchClosureError)):
        c.check_research_proof_bundle(SMALL, replace(bundle, nodes=tuple(nodes)), target,
                                            parent_specs=_parent().ALPHA_CHECKED_SPECS)


@pytest.mark.parametrize("field,value", (
    ("kernel_calls", 0), ("node_count", 1), ("root", 0),
    ("dependency_edges", 0), ("total_body_nodes", 0), ("topological_order", ()),
    ("target", Bot()),
))
def test_real_checker_receipt_cannot_hide_skipped_nodes_or_wrong_target(small_syntax, monkeypatch, field, value):
    bundle, target = small_syntax
    original = c.check_proof_bundle
    def corrupted_receipt(*args, **kwargs):
        actual = original(*args, **kwargs)
        return replace(actual, **{field: value})
    monkeypatch.setattr(c, "check_proof_bundle", corrupted_receipt)
    with pytest.raises(c.ResearchClosureError):
        c.check_research_proof_bundle(SMALL, bundle, target, parent_specs=_parent().ALPHA_CHECKED_SPECS)


def test_original_resource_limits_are_used_without_a_provider_override():
    from peano_lab.library import proof_bundle
    from peano_lab.library import layered_replay
    from peano_lab.library import editions_v34
    assert c.DEFAULT_BUNDLE_LIMITS is proof_bundle.DEFAULT_BUNDLE_LIMITS
    assert editions_v34.DEFAULT_LAYERED_REPLAY_LIMITS is layered_replay.DEFAULT_LAYERED_REPLAY_LIMITS
    assert DEFAULT_BUNDLE_LIMITS.max_payload_bytes == 64_000_000
    assert DEFAULT_BUNDLE_LIMITS.max_nodes == 4096
    assert DEFAULT_BUNDLE_LIMITS.max_total_body_nodes == 5_000_000
    assert c.MAX_SOURCE_BYTES == 2 * 1024 * 1024


@pytest.mark.parametrize("owner", c.FACTORIES, ids=lambda item: item.module)
def test_even_an_unused_source_pin_is_checked_before_cached_specs(monkeypatch, owner):
    original = c._read_pinned
    calls = []
    def reject_one(path, *args, **kwargs):
        calls.append(path)
        if path.name == owner.module + ".py":
            raise c.ResearchClosureError("intentional changed unused source")
        return original(path, *args, **kwargs)
    monkeypatch.setattr(c, "_read_pinned", reject_one)
    with pytest.raises(c.ResearchClosureError, match="changed unused source"):
        c.research_specs()
    assert any(path.name == owner.module + ".py" for path in calls)


def _main(argv=None):
    """Run only the selected actual tests in one original bounded window."""
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pytest-select", default="")
    parser.add_argument("--case-start", type=int, default=0)
    parser.add_argument("--case-count", type=int)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args(argv)
    if args.case_start < 0 or args.case_count is not None and args.case_count <= 0:
        parser.error("a case window must be positive and bounded")
    input_paths = sorted({Path(__file__).resolve(), Path(c.__file__).resolve(),
        *(ROOT / path for path in TRUSTED_SOURCE_SHA256),
        *(ROOT / "peano-lab/py/peano_lab/library" / (row[0]+".py") for row in CANONICAL_SOURCE_PINS)})
    def input_pins():
        return [[str(path), len(raw), sha256(raw).hexdigest()]
                for path in input_paths for raw in (path.read_bytes(),)]
    before = input_pins()

    class Window:
        def __init__(self):
            self.selected = []
            self.passed = set()
            self.bad = []
            self.phases = []
        @pytest.hookimpl(trylast=True)
        def pytest_collection_modifyitems(self, session, config, items):
            chosen = items[args.case_start:None if args.case_count is None else args.case_start + args.case_count]
            if args.case_count is not None and len(chosen) != args.case_count:
                raise ValueError("the exact requested case window is unavailable")
            if not chosen:
                raise ValueError("an empty bounded case selection is not a pass")
            selected = {item.nodeid for item in chosen}
            rejected = [item for item in items if item.nodeid not in selected]
            config.hook.pytest_deselected(items=rejected)
            items[:] = chosen
            self.selected = [item.nodeid for item in chosen]
        def pytest_runtest_logreport(self, report):
            self.phases.append([report.nodeid, report.when, report.outcome, report.duration,
                                bool(getattr(report, "wasxfail", False))])
            if report.when == "call" and report.passed:
                self.passed.add(report.nodeid)
            elif report.failed or report.skipped or getattr(report, "wasxfail", None):
                self.bad.append(report.nodeid)

    plugin = Window()
    options = [str(Path(__file__).resolve()), "-q", "--disable-warnings", "-k", args.pytest_select]
    if args.collect_only:
        options.append("--collect-only")
    status = pytest.main(options, plugins=[plugin])
    peak = max(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
               resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    if sys.platform != "darwin":
        peak *= 1024
    if not 0 < peak <= 1536 * 1024 * 1024:
        raise RuntimeError("the original observed RSS ceiling was exceeded")
    if not args.collect_only and (plugin.bad or plugin.passed != set(plugin.selected)):
        status = status or 1
    after = input_pins()
    expected_phases = {(nodeid, phase) for nodeid in plugin.selected for phase in ("setup", "call", "teardown")}
    actual_phases = [(record[0], record[1]) for record in plugin.phases]
    if (before != after or not args.collect_only and (
            len(actual_phases) != len(expected_phases) or set(actual_phases) != expected_phases
            or any(record[2] != "passed" or record[4] for record in plugin.phases))):
        status = status or 1
    print(json.dumps({"selected": len(plugin.selected), "passed": len(plugin.passed),
                      "selected_ids": plugin.selected, "phases": plugin.phases,
                      "source_pins_before": before, "source_pins_after": after,
                      "collect_only": args.collect_only, "pytest_exit_code": int(status),
                      "elapsed_seconds": time.monotonic() - _BOUNDED_STARTED,
                      "peak_rss_bytes": peak, "cpu": list(resource.getrlimit(resource.RLIMIT_CPU)),
                      "wall_seconds": 180}, sort_keys=True), flush=True)
    return int(status)


if __name__ == "__main__":
    raise SystemExit(_main())
