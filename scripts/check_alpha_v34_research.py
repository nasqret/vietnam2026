#!/usr/bin/env python3
"""Fresh, bounded proof gates for the polynomial gcd and congruence Alpha-v34 release.

Every family is checked from its real ordinary HA bodies and from exactly the
same bytes by the independently compiled Lean verifier. Principal certificates
run in separate unchanged proof windows. A saved report is never an input.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict
import gc
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path
import re
import resource
import secrets
import signal
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = Path(__file__).resolve()
for directory in (ROOT / "peano-lab/py", ROOT / "scripts"):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))

import check_constructive_lower_continuation as transport
from check_constructive_bottom_layers import authoring_rss_bytes
import constructive_bottom_layer_checkpoints as independent
import check_alpha_v33_research as previous_audit
import peano_catalog_shards as parent_catalog
import peano_catalog_shards_v33 as current_parent_catalog


CPU_LIMITS = (170, 175)
WALL_SECONDS = 180
PARENT_TIMEOUT_SECONDS = 185
MAX_RSS_BYTES = 1536 * 1024 * 1024
MAX_STDOUT_BYTES = 128 * 1024
MAX_STDERR_BYTES = 8 * 1024
WORKER_SCHEMA = "peano-alpha-v34-live-proof-worker-v1"
AUDIT_SCHEMA = "peano-alpha-v34-research-proof-audit-v1"
EXPECTED_INVENTORY = (("polynomial-gcd-bezout", 119), ("congruence-arithmetic", 12))
EXPECTED_JOB_COUNT = 22
PARENT_PATH = "artifacts/peano-library/alpha/catalog-v33.json"
PARENT_BYTES = 946_819
PARENT_SHA256 = "6be052da195a295edce02f4b1955cd9e3dd71d7acefb9ac5794277eda7ef40cc"
PARENT_EVIDENCE_PINS = (
    ("artifacts/peano-library/alpha/metrics-v33.json", 644863,
     "c0eef13d14b48ccf29f0effdbb1a882d62320025c93e32de516a383810eb295b"),
    ("artifacts/peano-library/alpha/dependency-graph-v33.mmd", 1099556,
     "823afe0c40c4e12b51c0942075151fbcc6350308fcd904495363da50ee976a98"),
    ("artifacts/peano-library/channels-v33.json", 9638,
     "d10d87694f813b86451bcccdde4dcd68e5d6fe73795b9610d98bea4f3e5de6bc"),
    ("research/arithmetic-library/artifacts/alpha-v33-research-receipt-v1.json", 55856,
     "cea85e5c595a021061fb50997df7ad489c8905ab563695209dadc8235f6762cb"),
    ("artifacts/peano-library/catalog-v1.json", 1310134,
     "87fca4ab6e66d01f728ada1d9c6442f1167b8f2a8fe51cd6ec5eda901b3daffd"),
)
# Exact documentary preservation only; these archived files are never imported.
WORKING_HISTORY_PINS = (
    *previous_audit.WORKING_HISTORY_PINS,
    ("research/arithmetic-library/working/prime-field-gcd-closure-v1/working_gcd_closure_support.py", 29898, "0c330c4d1557fc9df72935b6f7d51305f3077dcf0eec83b0605fb650ed048a95"),
    ("research/arithmetic-library/working/prime-field-gcd-closure-v1/export_working_gcd_closure.py", 9078, "e1e214ccbdbbc207b093f973be7fe10ab3fefebab787f2e6d7e99818d9c6e390"),
    ("research/arithmetic-library/working/prime-field-gcd-closure-v1/check_working_gcd_closure.py", 12479, "73d4926c1d1726e92c9e010e85a1405fef085b7c7d45bb15b0b9a44ba682c48f"),
    ("research/arithmetic-library/working/prime-field-gcd-closure-v1/test_working_gcd_closure.py", 10451, "f3729458ed63b6a57e0744a6c6a995389e9fc4a17c6d2b8efaa628059a9c17de"),
    ("research/arithmetic-library/working/prime-field-gcd-closure-v1/working-gcd-closure-rfc-v1.md", 6008, "e9d1f5b0ab869488b6501983311cb8570f88b6293fee2318ac0d40a57041e33d"),
    ("research/arithmetic-library/working/prime-field-gcd-closure-v1/README.md", 6150, "abc840de821e921e50922d4750f653f90142ec246931a65afbf3374468b745d2"),
    ("research/arithmetic-library/working/prime-field-gcd-closure-v1/final-verification-observations-v1.json", 134357, "2e95e9d36dff1fbb7a29bb955946c737f2015a56d8e9c9a3a5c98a2128ebb388"),
    ("research/arithmetic-library/working/prime-field-gcd-closure-v1/completion-accounting-v1.json", 35031, "8e727bbf39c1a218bffe6ea3e5915a8c661855eeafacb26087697ba1301dc2f4"),
    ("research/arithmetic-library/working/prime-field-shift-v1/prime_field_polynomial_shift_candidate.py", 29786, "325d3085482ee73a2c6ee90cd17e45cffe53273671edf89c40d88428335c9c4b"),
    ("research/arithmetic-library/working/prime-field-shift-v1/test_prime_field_polynomial_shift_candidate.py", 32010, "0622fb92978fcf028842aa4d9822ef61213642eb852e080f7c787dcea4bb395f"),
    ("research/arithmetic-library/working/prime-field-scalar-v1/prime_field_polynomial_scalar_convolution_candidate.py", 23637, "e84f1c77c6c03fa5f08635aeede53591625d1c2bfcdfb64fbd379c33878aee0e"),
    ("research/arithmetic-library/working/prime-field-scalar-v1/test_prime_field_polynomial_scalar_convolution_candidate.py", 30353, "881452ada0b5dc3be7d6cd00ee31dc08075b07f51d83595ee60f8cfb40d4c6e5"),
    ("research/arithmetic-library/working/prime-field-append-v1/prime_field_polynomial_append_candidate.py", 28396, "271845bfffc7e513fdb0bd0c3666dcccace8436d4d3a0f4db64b67bcd4b87042"),
    ("research/arithmetic-library/working/prime-field-append-v1/test_prime_field_polynomial_append_candidate.py", 36494, "0c554b05b2c7e2c40e3b0e8044160379a3284bb173e48d59d77def0cad4272aa"),
    ("research/arithmetic-library/working/prime-field-shift-equivalence-v1/prime_field_polynomial_shift_equivalence_candidate.py", 6021, "8846224923876a4f57ad8d6f31020838ccc86c86a683ec78a7c7c23c35b92068"),
    ("research/arithmetic-library/working/prime-field-shift-equivalence-v1/test_prime_field_polynomial_shift_equivalence_candidate.py", 20376, "9ed90ddc4680f8c2c3d04e2e3a76f8cffda4bfb95b1b83ab391d134c7fe5ab18"),
    ("research/arithmetic-library/working/prime-field-associativity-step-v1/prime_field_polynomial_associativity_step_candidate.py", 26607, "dd85dbd1bd87143715a4286724ac7c87f280a909dac6759f00a6cb7dff7c85f1"),
    ("research/arithmetic-library/working/prime-field-associativity-step-v1/test_prime_field_polynomial_associativity_step_candidate.py", 29135, "4cbd15750521b2ad1a3ecd8288bfdf631bd5ad90dc7e623d4e593dc79f615262"),
    ("research/arithmetic-library/working/prime-field-associativity-induction-v1/prime_field_polynomial_associativity_induction_candidate.py", 9924, "8d276a028764cd08e6eaebbf25bb4e21fcd5076a610d356a77d52ba6603ebe4c"),
    ("research/arithmetic-library/working/prime-field-associativity-induction-v1/test_prime_field_polynomial_associativity_induction_candidate.py", 19628, "d3725cbdd86f8d72446baf5417d25a4ddf31f61b0b6f1d076cb065b8131f2003"),
    ("research/arithmetic-library/working/prime-field-divisibility-v1/prime_field_polynomial_divisibility_candidate.py", 15168, "f544adedd3ce963e4a773e8582efcb0f91ba7491207c9792d477d452e854f2b8"),
    ("research/arithmetic-library/working/prime-field-divisibility-v1/test_prime_field_polynomial_divisibility_candidate.py", 20043, "82460849735222acb22c120004226a9e0a91c0231f8ab960cc3657f0767400e3"),
    ("research/arithmetic-library/working/prime-field-left-unit-v1/prime_field_polynomial_left_unit_candidate.py", 16858, "dbb8debb4716b6bb9b246700f7e93865c8a6c1b12a3b65c0ffbb62206a890ba6"),
    ("research/arithmetic-library/working/prime-field-left-unit-v1/test_prime_field_polynomial_left_unit_candidate.py", 16474, "5b8758079485c1c7f8a448f218a4b70b9e5df11722eabf63ec6fcc1e68802c71"),
    ("research/arithmetic-library/working/prime-field-alignment-v1/prime_field_polynomial_alignment_candidate.py", 11780, "eb16e2eb02dbd66a7706e616388182992b8cf2e0715818dc1f7748938e7d798e"),
    ("research/arithmetic-library/working/prime-field-aligned-add-v1/prime_field_polynomial_aligned_add_candidate.py", 20704, "a05bb4f5c4230ca05f51690d3ab82e33ff4596af65176874e25fbe38cf87a0db"),
    ("research/arithmetic-library/working/prime-field-aligned-algebra-v1/prime_field_polynomial_aligned_algebra_candidate.py", 16013, "a68de84439afb5f6dd87f1d47449c0bce8dd53a66346c00cc1b7645fb80b2390"),
    ("research/arithmetic-library/working/prime-field-euclidean-identity-v1/prime_field_polynomial_euclidean_identity_candidate.py", 11235, "8efdcd2abf2143891b79edcb3fc90d7126ae69507c1c631ed33b497172ffdb77"),
    ("research/arithmetic-library/working/prime-field-aligned-distributivity-v1/prime_field_polynomial_aligned_distributivity_candidate.py", 8518, "7d535939e24fe6d82158c485533b2ff6934f4d897b6141fde6c50b4fec9788ba"),
    ("research/arithmetic-library/working/prime-field-left-constant-v1/prime_field_polynomial_left_constant_candidate.py", 17620, "9a7a4de30f5f389bcabc2e6267a0d2cc5dc5f061059dcea303a0a03dab58509a"),
    ("research/arithmetic-library/working/prime-field-euclidean-normalization-v1/prime_field_polynomial_euclidean_normalization_candidate.py", 16401, "d2cddfe42dc0d22104dc4e85e95116222914df11ac840d2082a4ff2e462f146f"),
    ("research/arithmetic-library/working/prime-field-euclidean-transport-v1/prime_field_polynomial_euclidean_transport_candidate.py", 18256, "9a589d1749eb38d30d1a24364bc4d66f7df0efb59247527f7831f97557da9c30"),
    ("research/arithmetic-library/working/prime-field-bezout-backward-v1/prime_field_polynomial_bezout_backward_candidate.py", 18747, "c3903482000c957ac77f84a43a85d135e4caa19e4484328035f91b82cbf3a702"),
    ("research/arithmetic-library/working/prime-field-gcd-bezout-laws-v1/prime_field_polynomial_gcd_bezout_laws_candidate.py", 15300, "76b90226e5e29fdde3d9bb49accccf8d9b4c0cc17a4de406af253e999102533c"),
    ("research/arithmetic-library/working/prime-field-gcd-existence-v1/prime_field_polynomial_gcd_existence_candidate.py", 26480, "81f2f48dd2e81894c7a267453646eb6f2b6f9bd3ee320386d8c561f6b9f8b8ca"),
    ("research/arithmetic-library/working/prime-field-gcd-uniqueness-v1/prime_field_polynomial_gcd_uniqueness_candidate.py", 31432, "916c24ad6c59609612e97daee6e49347a9522cdb28b44f6f09c6c5760bff0b5b"),
    ("research/arithmetic-library/working/prime-field-gcd-closure-v1/artifacts/working-gcd-closure-prefix-119-proof-bundle-v1.json", 5193292, "3fe18ad2899cff7db5fbe19df8570ef70b1bfb902171d5212e9b036dda660a46"),
    ("research/arithmetic-library/working/linear-congruence-classification-v1/linear_congruence_classification_candidate.py", 18128, "12b1a98ce830704485f1ea78475fba8b10e39031ffbef00b1b5dfc8ffdef7f47"),
    ("research/arithmetic-library/working/linear-congruence-classification-v1/test_linear_congruence_classification_candidate.py", 13751, "97bb95b1f388fe947eba41f443265a30d5b8f3fa216df4a1abd688d95db5da35"),
    ("research/arithmetic-library/working/prime-field-alignment-v1/test_prime_field_polynomial_alignment_candidate.py", 30676, "6adbed23a43a393a4988d6eba9323cb09a8777b62b644cb1992ebdf7c6411c8b"),
    ("research/arithmetic-library/working/prime-field-aligned-add-v1/test_prime_field_polynomial_aligned_add_candidate.py", 33347, "6e67b246e1c565e44d721ad92ecb2e273c2e1330d226922af89f762630de2ed8"),
    ("research/arithmetic-library/working/prime-field-aligned-algebra-v1/test_prime_field_polynomial_aligned_algebra_candidate.py", 10321, "11f096addd3afb6301e98d61cf359b833754b29eebd7abf61a9e85b3da06d073"),
    ("research/arithmetic-library/working/prime-field-aligned-algebra-v1/test_prime_field_polynomial_aligned_algebra_contracts.py", 12694, "09c34419021d60ad8c78ea5b0430bc17a595fb2b3d97469e1e375a5f55697b2d"),
    ("research/arithmetic-library/working/prime-field-euclidean-identity-v1/test_prime_field_polynomial_euclidean_identity_candidate.py", 31004, "e7225749330ccd9392e584196057ab3a2547856764d25296bee775f9eb62e2c0"),
    ("research/arithmetic-library/working/prime-field-aligned-distributivity-v1/test_prime_field_polynomial_aligned_distributivity_candidate.py", 22358, "5fa4ff32894dcbe7f2010ae526731e88cbe4c2307e1043b56da326c487c26039"),
    ("research/arithmetic-library/working/prime-field-left-constant-v1/test_prime_field_polynomial_left_constant_candidate.py", 27847, "cc93a6d0b8d1ff3eae9bc0b16527936301a7a15e13e7baae3cf818a919cc6a60"),
    ("research/arithmetic-library/working/prime-field-euclidean-normalization-v1/test_prime_field_polynomial_euclidean_normalization_candidate.py", 29037, "e291538321e9d078a8b0044bacfb50d46b5eea59b2126001a2129c69de342791"),
    ("research/arithmetic-library/working/prime-field-euclidean-transport-v1/test_prime_field_polynomial_transport_models.py", 25634, "0c814915ee8b8f6ecc8ffb945699cd4888fa4c4cf86e6b4cb077063407f5cfab"),
    ("research/arithmetic-library/working/prime-field-gcd-bezout-laws-v1/test_prime_field_polynomial_gcd_bezout_laws_candidate.py", 20903, "21da40c3b70a9eb3436b681cfdfd99a2278786dea73b4e5bfdfdefaccdd1b7e0"),
    ("research/arithmetic-library/working/prime-field-gcd-existence-v1/test_prime_field_polynomial_gcd_existence_candidate.py", 15017, "f42c8387e3e84d73eadc0f3eb96e1be1207d2a29fff1f5b2dabd7f60c554ddba"),
    ("research/arithmetic-library/working/prime-field-gcd-uniqueness-v1/test_prime_field_polynomial_gcd_uniqueness_candidate.py", 21350, "6deba14cd0c750c5158c130c8e03f2402861769211605d42d5b61c7bd6936edd"),
)

CONTROL_SOURCES = (
    *previous_audit.CONTROL_SOURCES,
    "scripts/check_alpha_v34_research.py",
    "scripts/build_peano_library_channels_v34.py",
    "scripts/verify_peano_library_channels_v34.py",
    "scripts/peano_catalog_shards_v34.py",
    "scripts/peano_catalog_capacity_v34.py",
    "peano-lab/py/peano_lab/library/research_source_plan_v34.py",
    "peano-lab/py/tests/test_research_source_plan_v34.py",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v34.py",
    "peano-lab/py/peano_lab/library/editions_v34.py",
    "peano-lab/py/peano_lab/library/campaign_research_v34_closure.py",
    "peano-lab/py/tests/test_library_editions_v34_admission.py",
    "peano-lab/py/tests/test_library_editions_v34_cold_import.py",
    "peano-lab/py/tests/test_campaign_research_v34_closure.py",
    "scripts/test_check_alpha_v34_research.py",
    "scripts/test_peano_catalog_shards_v34.py",
    "scripts/test_verify_peano_library_channels_v34.py",
    "research/arithmetic-library/alpha-v34-gcd-congruence-promotion-rfc-v1.md",
    "research/arithmetic-library/prime-field-polynomial-gcd-bezout-rfc-v1.md",
    "research/arithmetic-library/linear-congruence-classification-rfc-v1.md",
)

if any(getattr(transport, key) != globals()[key] for key in (
    "CPU_LIMITS", "WALL_SECONDS", "PARENT_TIMEOUT_SECONDS", "MAX_RSS_BYTES",
    "MAX_STDOUT_BYTES", "MAX_STDERR_BYTES",
)) or transport.ROOT != ROOT:
    raise RuntimeError("the inherited bounded worker transport changed")

AuditError = transport.AuditWorkerError
canonical = transport._canonical
_LIVE_AUDIT = object()


def registry():
    """Exact provider ownership; a registration never accepts a proof."""
    from peano_lab.library import campaign_research_v34_closure as research
    research.validate_research_metadata()
    result = tuple(independent.Checkpoint(
        slug=family.slug,
        modules=tuple(independent.ModulePin(module, research.FACTORY_BY_MODULE[module].source_sha256)
                      for module in family.modules),
        artifact=family.artifact, artifact_bytes=family.artifact_bytes,
        artifact_sha256=family.artifact_sha256, frontier_count=family.count,
        principal_roots=family.principal_roots, rfc=family.rfc,
        frontier_specs_sha256=family.specs_sha256,
    ) for family in research.RESEARCH_FAMILIES)
    if (tuple((item.slug, item.frontier_count) for item in result) != EXPECTED_INVENTORY
            or len({item.artifact for item in result}) != 2
            or sum(item.frontier_count for item in result) != 131
            or tuple(len(item.principal_roots) for item in result) != (14, 5)
            or 1 + len(result) + sum(len(item.principal_roots) for item in result) != EXPECTED_JOB_COUNT):
        raise AuditError("the exact two-family/nineteen-principal promotion inventory changed")
    return result


def module_test_path(module):
    """Literal canonical-test provenance, shared by all twenty-one exact factories."""
    from peano_lab.library import campaign_research_v34_closure as research
    research.validate_research_metadata()
    if type(module) is not str or module not in research.FACTORY_BY_MODULE:
        raise AuditError("unknown exact v34 source module")
    return research.FACTORY_BY_MODULE[module].test


def _edition():
    from peano_lab.library import editions_v34
    editions_v34.require_research_seal()
    if (len(editions_v34.ALPHA_ENTRIES) != 4223
            or len(editions_v34.FRONTIER_NEW_NAMES) != 131
            or len(editions_v34.STABLE_ENTRIES) != 432):
        raise AuditError("the exact additive release partition changed")
    return editions_v34


def _owned(item):
    """Compare exact source factories with the independently sealed new edition."""
    from peano_lab.library.theorems import TheoremSpec
    from peano_lab.library.campaign_bottom_layer_closure import _specs_digest
    rows = []
    for pin in item.modules:
        independent._source_bytes(pin)
        module = import_module("peano_lab.library." + pin.module)
        expected_path = ROOT / pin.path
        factory = getattr(module, pin.factory, None)
        if (not isinstance(getattr(module, "__file__", None), str)
                or not Path(module.__file__).samefile(expected_path)
                or not callable(factory) or getattr(factory, "__module__", None) != module.__name__):
            raise AuditError("a cached source module or factory identity changed")
        rows.extend(factory(TheoremSpec))
    rows = tuple(rows)
    from peano_lab.library import campaign_research_v34_closure as research
    sealed = tuple(row for row in research.research_specs()
                   if research.FAMILY_BY_NAME[row.name].slug == item.slug)
    if (len(rows) != item.frontier_count or _specs_digest(rows) != item.frontier_specs_sha256
            or rows != sealed or not set(item.principal_roots) <= {row.name for row in rows}):
        raise AuditError("literal research ownership differs from the exact registered sources")
    return rows


def _inventory_rows():
    rows = tuple(row for item in registry() for row in _owned(item))
    from peano_lab.library import campaign_research_v34_closure as research
    if tuple(row.name for row in rows) != research.FRONTIER_NEW_NAMES:
        raise AuditError("the exact ordered additive frontier changed")
    return rows


def _relative_path(path):
    """Stable repository identity; never normalize a foreign path into scope."""
    if not isinstance(path, Path):
        raise AuditError("a proof source path must be a Path")
    try:
        relative = path.relative_to(ROOT)
    except ValueError as error:
        raise AuditError("a proof source is outside the repository") from error
    if (not relative.parts or any(part in ("", ".", "..") for part in relative.parts)
            or "\\" in relative.as_posix()):
        raise AuditError("an unsafe proof source identity was supplied")
    return relative.as_posix()


def _file_digest(relative, maximum, *, expected_bytes=None, expected_sha256=None):
    """Strict no-follow, size-first streaming authentication; no large buffer."""
    if (type(relative) is not str or not relative or "\\" in relative
            or relative.startswith("/") or any(part in ("", ".", "..") for part in relative.split("/"))
            or type(maximum) is not int or not 0 < maximum <= parent_catalog.MAX_CATALOG_BYTES
            or expected_bytes is not None and (type(expected_bytes) is not int
                                               or not 0 < expected_bytes <= maximum)
            or expected_sha256 is not None and (type(expected_sha256) is not str
                                                or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None)):
        raise AuditError("invalid bounded repository source")
    path = ROOT / relative
    if _relative_path(path) != relative:
        raise AuditError("a source identity was normalized")
    owner = parent_catalog._owner(None)
    try:
        with parent_catalog._opened(path, owner, expected_bytes) as (descriptor, before):
            if before.size > maximum:
                raise AuditError("a source exceeds its original input ceiling")
            digest = sha256()
            consumed = 0
            while consumed < before.size:
                block = os.read(descriptor, min(1024 * 1024, before.size - consumed))
                if not block:
                    raise AuditError("a proof source was truncated")
                consumed += len(block)
                digest.update(block)
            if os.read(descriptor, 1):
                raise AuditError("a proof source grew during hashing")
            if parent_catalog._fingerprint(path, os.fstat(descriptor)) != before:
                raise AuditError("an open proof source changed during hashing")
        if parent_catalog._stat_file(path, owner, expected_bytes) != before:
            raise AuditError("a proof source path changed during hashing")
    except (OSError, ValueError) as error:
        raise AuditError("an ordinary bounded proof source could not be authenticated: " + relative) from error
    actual = digest.hexdigest()
    if expected_sha256 is not None and actual != expected_sha256:
        raise AuditError("literal proof source bytes changed: " + relative)
    return before.size, actual


def _runtime_source_paths():
    """Bind actual implementation inputs, not an unrestricted metadata wildcard."""
    directory = ROOT / "peano-lab/py/peano_lab"
    result = [_relative_path(path) for path in sorted(directory.rglob("*.py"))]
    if not result or len(result) != len(set(result)):
        raise AuditError("the actual runtime source inventory is malformed")
    return tuple(result)


def source_binding():
    """Bind current bytes; neither hash checks nor old receipts prove a theorem."""
    from peano_lab.library import campaign_research_v34_closure as research
    families = registry()
    controls = {path: _file_digest(path, independent.MAX_SOURCE_BYTES)[1]
                for path in dict.fromkeys((*CONTROL_SOURCES, *_runtime_source_paths()))}
    research.validate_research_source_bytes()
    for item in families:
        for pin in item.modules:
            independent._source_bytes(pin)
            if controls[pin.path] != pin.sha256:
                raise AuditError("the source changed between its live and literal checks")
        _file_digest(item.artifact, parent_catalog.MAX_CATALOG_BYTES,
                     expected_bytes=item.artifact_bytes, expected_sha256=item.artifact_sha256)
    parent = current_parent_catalog.verify_catalog_bindings(ROOT / PARENT_PATH, expected_sha256=PARENT_SHA256)
    if parent.manifest.bytes != PARENT_BYTES or parent.manifest.row_count != 4092:
        raise AuditError("the immutable v33 parent manifest changed")
    parent_inputs = [
        {"role": item.role, "path": _relative_path(item.path), "bytes": item.bytes,
         "sha256": item.sha256, "schema": item.schema, "row_count": item.row_count}
        for item in (parent.manifest, parent.parent, parent.delta)
    ]
    for path, size, digest in (*PARENT_EVIDENCE_PINS, *WORKING_HISTORY_PINS):
        _file_digest(path, parent_catalog.MAX_CATALOG_BYTES,
                     expected_bytes=size, expected_sha256=digest)
    independent._check_lean_binary()
    return sha256(canonical({
        "controls": controls, "families": [asdict(item) for item in families],
        "parent": parent_inputs,
        "parent_evidence": PARENT_EVIDENCE_PINS,
        "preserved_non_admitted_working_history": WORKING_HISTORY_PINS,
        "lean": [independent.LEAN_BINARY_BYTES, independent.LEAN_BINARY_SHA256],
    })).hexdigest()


def _family_syntax_report(item, bundle, receipt, positions):
    from peano_lab.engine.state import proof_identity_metrics, proof_metrics
    owned = _owned(item)
    rows = []
    for spec in owned:
        node_id = positions[spec.name]
        body = bundle.nodes[node_id].body
        nodes, depth = proof_metrics(body)
        objects, edges, reused = proof_identity_metrics(body)
        rows.append({"name": spec.name, "node_id": node_id,
                     "statement_sha256": sha256(spec.statement.encode()).hexdigest(),
                     "proof_nodes": nodes, "proof_depth": depth, "proof_objects": objects,
                     "proof_edges": edges, "reused_objects": reused})
    return {
        "slug": item.slug, "new_theorem_count": len(owned),
        "specs_sha256": item.frontier_specs_sha256,
        "owned_node_ids": {spec.name: positions[spec.name] for spec in owned},
        "rows": rows,
        "bundle": {
            "path": item.artifact, "bytes": item.artifact_bytes, "sha256": item.artifact_sha256,
            "nodes_including_packaging_root": len(bundle.nodes),
            "dependency_edges_including_packaging": receipt.dependency_edges,
            "body_proof_nodes": receipt.total_body_nodes, "packaging_root_id": bundle.root,
            "kernel_calls": receipt.kernel_calls,
            "original_ha_checked": True, "independent_lean_checked": True,
        },
        "principal_roots": [],
    }


def _source_bundle(item):
    """The original exact assembler route without full-edition retention."""
    from peano_lab.library import campaign_research_v34_closure as research
    from peano_lab.library.research_source_plan_v34 import source_selection
    from peano_lab.library.proof_bundle import decode_proof_bundle
    selected = source_selection(item.slug)
    payload = research.read_research_bundle_bytes(item.slug, ROOT / item.artifact)
    bundle, target = decode_proof_bundle(payload.decode("utf-8"))
    return selected, payload, bundle, target


def _family(item):
    from peano_lab.library import campaign_bottom_layer_closure as closure
    from peano_lab.library import campaign_research_v34_closure as research
    selected, payload, bundle, target = _source_bundle(item)
    receipt = closure.check_bottom_layer_bundle(selected.frontier, bundle, target)
    sealed = research.research_family(item.slug)
    if (receipt.kernel_calls != sealed.node_count or receipt.node_count != sealed.node_count
            or receipt.dependency_edges != sealed.bundle_edges
            or receipt.total_body_nodes != sealed.body_nodes):
        raise AuditError("not every exact actual body reached the original HA kernel")
    independent._lean_check(item, receipt.node_count, bundle.root, payload)
    return _family_syntax_report(item, bundle, receipt, selected.positions)


def _root(item, name):
    from peano_lab.kernel.checker import check
    from peano_lab.library import campaign_bottom_layer_closure as closure
    from peano_lab.library.theorems import _closed_formula
    rows = {row.name: row for row in _owned(item)}
    if name not in item.principal_roots:
        raise AuditError("unregistered ordinary principal")
    selected, payload, bundle, target = _source_bundle(item)
    position = selected.positions[name]
    del payload
    result = closure.replay_bottom_layer_theorem(selected.frontier, name, bundle, target)
    exact = _closed_formula(rows[name].statement)
    if result.spec != rows[name] or result.formula != exact or not check((), result.certificate, exact):
        raise AuditError("the returned ordinary empty-context certificate failed original HA")
    return {"slug": item.slug, "name": name, "node_id": position,
            "statement_sha256": sha256(rows[name].statement.encode()).hexdigest(),
            "complete_ordinary_ha_checked": True, "ordinary_certificate_nodes": result.proof_nodes}


def _novelty():
    from peano_lab.library.formula_dag import FormulaArena
    from peano_lab.library.theorems import _closed_formula
    rows = _inventory_rows()
    index = {}
    duplicates = []
    # Exact canonical FormulaDAG bytes decide equality; hashes only index them.
    for spec in rows:
        encoded = FormulaArena().freeze(_closed_formula(spec.statement)).to_json()
        fingerprint = sha256(encoded.encode()).digest()
        duplicates.extend((spec.name, old) for old, other in index.get(fingerprint, ()) if encoded == other)
        index.setdefault(fingerprint, []).append((spec.name, encoded))
    edition = _edition()
    from peano_lab.library.research_source_plan_v34 import source_cone
    current = {spec.name: spec for spec in edition.ALPHA_CHECKED_SPECS}
    for item in registry():
        # Compare every inherited/current source, not merely the new roots.
        selected = source_cone(item.slug)
        if any(current.get(spec.name) != spec for spec in selected.specs):
            raise AuditError("an exact canonical source differs from the sealed current edition")
        if any(current.get(spec.name) != spec for spec in _owned(item)):
            raise AuditError("an exact additive factory differs from the sealed current edition")
    for spec in edition.v33.ALPHA_CHECKED_SPECS:
        encoded = FormulaArena().freeze(_closed_formula(spec.statement)).to_json()
        fingerprint = sha256(encoded.encode()).digest()
        duplicates.extend((name, spec.name) for name, other in index.get(fingerprint, ()) if encoded == other)
    if duplicates:
        raise AuditError(f"exact duplicate promoted statements: {duplicates!r}")
    return {"new_theorems": 131, "prior_theorems": 4092, "duplicates": [],
            "exact_ast_novelty_checked": True,
            "ordered_names_sha256": sha256("\n".join(row.name for row in rows).encode()).hexdigest()}


def _validate_family_report(report, item):
    """Exact identities and bounded observational metrics from the live worker."""
    from peano_lab.library.campaign_research_v34_closure import research_family
    from peano_lab.library.proof_bundle import DEFAULT_BUNDLE_LIMITS as limits
    rows = _owned(item)
    sealed = research_family(item.slug)
    positions_by_name = {name: index for index, name in enumerate(sealed.ordered_cone_names)}
    if (type(report) is not dict or set(report) != {
            "slug", "new_theorem_count", "specs_sha256", "owned_node_ids", "rows", "bundle", "principal_roots"}
            or report["slug"] != item.slug or type(report["new_theorem_count"]) is not int
            or report["new_theorem_count"] != len(rows)
            or report["specs_sha256"] != item.frontier_specs_sha256
            or report["principal_roots"] != []):
        raise AuditError("wrong exact family report")
    bundle = report["bundle"]
    if type(bundle) is not dict or set(bundle) != {
            "path", "bytes", "sha256", "nodes_including_packaging_root",
            "dependency_edges_including_packaging", "body_proof_nodes", "packaging_root_id",
            "kernel_calls", "original_ha_checked", "independent_lean_checked"}:
        raise AuditError("malformed actual bundle report")
    if (bundle["path"] != item.artifact or type(bundle["bytes"]) is not int
            or bundle["bytes"] != item.artifact_bytes or bundle["sha256"] != item.artifact_sha256
            or bundle["original_ha_checked"] is not True or bundle["independent_lean_checked"] is not True):
        raise AuditError("changed actual bundle identity or skipped independent proof gate")
    for key, exact in (("nodes_including_packaging_root", sealed.node_count),
                       ("dependency_edges_including_packaging", sealed.bundle_edges),
                       ("body_proof_nodes", sealed.body_nodes),
                       ("packaging_root_id", sealed.node_count - 1),
                       ("kernel_calls", sealed.node_count)):
        if type(bundle[key]) is not int or bundle[key] != exact:
            raise AuditError("actual proof metrics differ from the independently sealed artifact")
    for key, maximum in (("nodes_including_packaging_root", limits.max_nodes),
                         ("dependency_edges_including_packaging", limits.max_edges),
                         ("body_proof_nodes", limits.max_total_body_nodes),
                         ("kernel_calls", limits.max_nodes)):
        if type(bundle[key]) is not int or not 0 < bundle[key] <= maximum:
            raise AuditError("invalid bounded actual bundle metrics")
    count = bundle["nodes_including_packaging_root"]
    if (type(bundle["packaging_root_id"]) is not int or bundle["packaging_root_id"] != count - 1
            or bundle["kernel_calls"] != count):
        raise AuditError("changed packaging root or omitted original-kernel calls")
    if (type(report["owned_node_ids"]) is not dict
            or set(report["owned_node_ids"]) != {spec.name for spec in rows}
            or type(report["rows"]) is not list or len(report["rows"]) != len(rows)):
        raise AuditError("missing, duplicate or unrelated owned proof rows")
    positions = []
    for spec, actual in zip(rows, report["rows"], strict=True):
        if (type(actual) is not dict or set(actual) != {
                "name", "node_id", "statement_sha256", "proof_nodes", "proof_depth",
                "proof_objects", "proof_edges", "reused_objects"}
                or actual["name"] != spec.name
                or actual["statement_sha256"] != sha256(spec.statement.encode()).hexdigest()
                or type(actual["node_id"]) is not int or not 0 <= actual["node_id"] < count - 1
                or actual["node_id"] != positions_by_name[spec.name]
                or type(report["owned_node_ids"][spec.name]) is not int
                or report["owned_node_ids"][spec.name] != actual["node_id"]):
            raise AuditError("changed exact owned statement or local proof identity")
        positions.append(actual["node_id"])
        for key, minimum, maximum in (
            ("proof_nodes", 1, limits.max_body_nodes), ("proof_depth", 1, limits.max_body_depth),
            ("proof_objects", 1, limits.max_body_nodes), ("proof_edges", 0, limits.max_body_nodes * 2),
            ("reused_objects", 0, limits.max_body_nodes),
        ):
            if type(actual[key]) is not int or not minimum <= actual[key] <= maximum:
                raise AuditError("invalid bounded actual body metrics")
        if (actual["proof_objects"] > actual["proof_nodes"]
                or actual["proof_depth"] > actual["proof_nodes"]
                or not actual["proof_objects"] - 1 <= actual["proof_edges"] <= actual["proof_nodes"] - 1
                or actual["reused_objects"] != actual["proof_edges"] - (actual["proof_objects"] - 1)):
            raise AuditError("inconsistent actual body metrics")
    if positions != sorted(set(positions)):
        raise AuditError("duplicate or reordered owned local proof nodes")
    return report


def _validate_report(report, *, kind, item=None, name=None, family=None):
    if kind == "novelty":
        expected = {"new_theorems": 131, "prior_theorems": 4092, "duplicates": [],
                    "exact_ast_novelty_checked": True,
                    "ordered_names_sha256": sha256("\n".join(row.name for row in _inventory_rows()).encode()).hexdigest()}
        if canonical(report) != canonical(expected):
            raise AuditError("changed exact whole-release novelty audit")
    elif kind == "family":
        _validate_family_report(report, item)
    elif kind == "root":
        from peano_lab.library.layered_replay import DEFAULT_LAYERED_REPLAY_LIMITS
        spec = next(row for row in _owned(item) if row.name == name)
        count = report.get("ordinary_certificate_nodes") if type(report) is dict else None
        if type(count) is not int or not 1 < count <= DEFAULT_LAYERED_REPLAY_LIMITS.max_candidate_proof_occurrences:
            raise AuditError("invalid bounded ordinary-certificate count")
        expected = {"slug": item.slug, "name": name, "node_id": family["owned_node_ids"][name],
                    "statement_sha256": sha256(spec.statement.encode()).hexdigest(),
                    "complete_ordinary_ha_checked": True, "ordinary_certificate_nodes": count}
        if canonical(report) != canonical(expected):
            raise AuditError("changed exact ordinary principal report")
    else:
        raise AuditError("unknown proof job kind")


def _validate_message(payload, *, kind, slug, nonce, binding, item=None, name=None, family=None):
    value = transport._decode_message(payload)
    expected = {"schema": WORKER_SCHEMA, "kind": kind, "slug": slug, "nonce": nonce,
                "binding_sha256": binding,
                "limits": {"cpu": list(CPU_LIMITS), "wall_seconds": WALL_SECONDS, "max_rss_bytes": MAX_RSS_BYTES}}
    if set(value) != {*expected, "peak_rss_bytes", "report"} or canonical({k: value[k] for k in expected}) != canonical(expected):
        raise AuditError("stale, foreign or incorrectly limited proof worker response")
    peak = value["peak_rss_bytes"]
    if type(peak) is not int or not 0 < peak <= MAX_RSS_BYTES:
        raise AuditError("actual proof worker exceeded the unchanged RSS ceiling")
    _validate_report(value["report"], kind=kind, item=item, name=name, family=family)
    return value["report"], peak


def _run_worker(kind, binding, *, item=None, name=None, family=None):
    slug = item.slug if item else "all"
    nonce = secrets.token_hex(32)
    command = [sys.executable, str(SCRIPT), "--worker", kind, "--slug", slug,
               "--nonce", nonce, "--binding", binding]
    if name is not None:
        command.extend(("--root", name))
    environment = os.environ.copy()
    environment.update(PYTHONPATH=os.pathsep.join((str(ROOT / "peano-lab/py"), str(ROOT / "scripts"))),
                       PYTHONMALLOC="pymalloc", PYTHONNOUSERSITE="1", PYTHONDONTWRITEBYTECODE="1")
    label = f"{kind}: {slug}" + (f" / {name}" if name else "")
    print(f"Checking {label}", file=sys.stderr, flush=True)
    payload = transport._capture_bounded(command, environment)
    report, peak = _validate_message(payload, kind=kind, slug=slug, nonce=nonce, binding=binding,
                                     item=item, name=name, family=family)
    print(f"Verified {label}; peak RSS {peak} bytes", file=sys.stderr, flush=True)
    return report, peak


def _worker(kind, slug, nonce, binding, root):
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    if (re.fullmatch(r"[0-9a-f]{64}", nonce or "") is None
            or re.fullmatch(r"[0-9a-f]{64}", binding or "") is None or source_binding() != binding):
        raise AuditError("invalid or stale private proof worker invocation")
    gc.collect()
    if kind == "novelty" and slug == "all" and root is None:
        report = _novelty()
    else:
        items = [item for item in registry() if item.slug == slug]
        if len(items) != 1:
            raise AuditError("unknown exact proof family")
        if kind == "family" and root is None:
            report = _family(items[0])
        elif kind == "root" and root in items[0].principal_roots:
            report = _root(items[0], root)
        else:
            raise AuditError("unknown or incorrectly scoped proof job")
    gc.collect()
    if source_binding() != binding:
        raise AuditError("actual proof sources changed during verification")
    value = {"schema": WORKER_SCHEMA, "kind": kind, "slug": slug, "nonce": nonce,
             "binding_sha256": binding, "report": report, "peak_rss_bytes": authoring_rss_bytes(),
             "limits": {"cpu": list(resource.getrlimit(resource.RLIMIT_CPU)), "wall_seconds": WALL_SECONDS,
                        "max_rss_bytes": MAX_RSS_BYTES}}
    payload = canonical(value)
    if len(payload) > MAX_STDOUT_BYTES:
        raise AuditError("actual proof report exceeds its unchanged protocol size")
    authoring_rss_bytes()
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()
    return 0


class FreshProofAudit:
    """An in-process capability minted only after this invocation's proof jobs."""

    __slots__ = ("_token", "_binding", "_report_bytes", "peak_rss_bytes")

    def __init__(self, token, binding, report, peak):
        if token is not _LIVE_AUDIT:
            raise AuditError("a saved report cannot instantiate a live proof audit")
        self._token, self._binding = token, binding
        self._report_bytes = canonical(report)
        self.peak_rss_bytes = peak

    @property
    def binding(self):
        return self._binding

    @property
    def report(self):
        return json.loads(self._report_bytes)

    def require_unchanged(self):
        if type(self) is not FreshProofAudit or self._token is not _LIVE_AUDIT or source_binding() != self._binding:
            raise AuditError("proof sources changed or no live proof audit is present")


def verify_in_fresh_windows():
    """Run exactly 22 real jobs: novelty, two HA/Lean bundles, nineteen ordinary roots."""
    _inventory_rows()
    binding = source_binding()
    novelty, peak = _run_worker("novelty", binding)
    families = []
    for item in registry():
        report, observed = _run_worker("family", binding, item=item)
        peak = max(peak, observed)
        principals = []
        for name in item.principal_roots:
            root, observed = _run_worker("root", binding, item=item, name=name, family=report)
            peak = max(peak, observed)
            principals.append({key: value for key, value in root.items() if key != "slug"})
        families.append({**report, "principal_roots": principals})
        gc.collect()
    if source_binding() != binding:
        raise AuditError("proof inputs changed across the live release gates")
    report = {"schema": AUDIT_SCHEMA, "source_binding_sha256": binding,
              "parent": {"path": PARENT_PATH, "bytes": PARENT_BYTES, "sha256": PARENT_SHA256,
                         "theorem_count": 4092},
              "new_theorems": 131, "alpha_theorem_count": 4223, "stable_theorem_count": 432,
              "families": families, "novelty": novelty,
              "ordinary_principal_count": sum(len(item.principal_roots) for item in registry()),
              "limits": {"cpu": list(CPU_LIMITS), "wall_seconds": WALL_SECONDS, "max_rss_bytes": MAX_RSS_BYTES}}
    return FreshProofAudit(_LIVE_AUDIT, binding, report, max(peak, authoring_rss_bytes()))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", choices=("family", "root", "novelty"), help=argparse.SUPPRESS)
    for name in ("slug", "nonce", "binding", "root"):
        parser.add_argument("--" + name, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    if args.worker:
        if not all((args.slug, args.nonce, args.binding)) or (args.worker == "root") != (args.root is not None):
            parser.error("invalid private proof worker arguments")
        return _worker(args.worker, args.slug, args.nonce, args.binding, args.root)
    if any((args.slug, args.nonce, args.binding, args.root)):
        parser.error("private proof arguments require an exact worker mode")
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    jobs = 1 + len(registry()) + sum(len(item.principal_roots) for item in registry())
    if jobs != EXPECTED_JOB_COUNT:
        raise AuditError("the exact twenty-two-window schedule changed")
    signal.alarm(jobs * PARENT_TIMEOUT_SECONDS + WALL_SECONDS)
    audit = verify_in_fresh_windows()
    print(f"Fresh Alpha-v34 proof gates PASS: 131 new theorems; 2 complete HA/Lean bundles; "
          f"{audit.report['ordinary_principal_count']} ordinary principals; peak RSS {audit.peak_rss_bytes} bytes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
