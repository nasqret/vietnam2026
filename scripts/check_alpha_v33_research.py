#!/usr/bin/env python3
"""Fresh, bounded proof gates for the complete polynomial Alpha-v33 release.

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
import check_alpha_v32_research as previous_audit
import peano_catalog_shards as parent_catalog
import peano_catalog_shards_v32 as current_parent_catalog


CPU_LIMITS = (170, 175)
WALL_SECONDS = 180
PARENT_TIMEOUT_SECONDS = 185
MAX_RSS_BYTES = 1536 * 1024 * 1024
MAX_STDOUT_BYTES = 128 * 1024
MAX_STDERR_BYTES = 8 * 1024
WORKER_SCHEMA = "peano-alpha-v33-live-proof-worker-v1"
AUDIT_SCHEMA = "peano-alpha-v33-research-proof-audit-v1"
EXPECTED_INVENTORY = (("polynomial-euclidean-division", 121),)
EXPECTED_JOB_COUNT = 10
PARENT_PATH = "artifacts/peano-library/alpha/catalog-v32.json"
PARENT_BYTES = 603_900
PARENT_SHA256 = "41b9f387d88a5a4f0fe5ee2bd5578f37a27a4657b0a80f1a1a2cb5109f69a623"
PARENT_EVIDENCE_PINS = (
    ("artifacts/peano-library/alpha/metrics-v32.json", 618251,
     "62a61fcc37c5a3c01b718d9ddd3604d0cb92db7a8ff2f34355e168e36fa5e0e8"),
    ("artifacts/peano-library/alpha/dependency-graph-v32.mmd", 1050225,
     "31fe3e2a7f0041597c9e061dffdb7c501d4700351603d491647321c2731e5f0c"),
    ("artifacts/peano-library/channels-v32.json", 9400,
     "9ff232e8e018967a7fe08074bf64270eabf190879aecb3e89a4742a3b5df1804"),
    ("research/arithmetic-library/artifacts/alpha-v32-research-receipt-v1.json", 78415,
     "6f0a09144ed53e95c5bee7ca5c033c684e5d6531b830a5b92c0c6042535fcce4"),
    ("artifacts/peano-library/catalog-v1.json", 1310134,
     "87fca4ab6e66d01f728ada1d9c6442f1167b8f2a8fe51cd6ec5eda901b3daffd"),
)
# Exact documentary preservation only; these archived files are never imported.
WORKING_HISTORY_PINS = (
    ("research/arithmetic-library/working/prime-field-equivalence-v1/README.md", 6975,
     "9444dd6431e14b87596ba5f1de7d54d7cf80ec583a3f64066288a8aca0ed5d4a"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/artifacts/working-equivalence-proof-bundle-v1.json", 2449379,
     "6ae667d8518e4dbe722bb08ad1b08715a0d282c2893e533c8133d770fe861dcf"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/check_working_equivalence.py", 12460,
     "7d86c4dc5a731442568c33b12500f10199ae7b0ba558b33c78ac2c9de5f73b14"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/combined-test-isolation-failure-observation-v1.json", 10130,
     "b2efd0668dc9ed9837b54dc99b1fa1115d278777055e659189294bf55d213aab"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/combined-verification-observations-v1.json", 10939,
     "5626fbd44ea2d3bf427370113fc558ce06400e849fe3c41264b2136e3cefa309"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/export_working_equivalence.py", 8084,
     "453b46ee1fee1f0606b170132eac58f3e4169c5c19557e6f0d23ea0bc15c291d"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/focused-proof-observations-v1.json", 15760,
     "87c41f7fbd246c680b4b7d7b121e408e39022ff45d04d99666adb84a71dafb55"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/import-isolation-smoke-observations-v1.json", 14338,
     "5ba6acad34e96357d68bd1458530f92c7bbd636f5507f7d2e1333039c63aebbf"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/notation-verification-observations-v1.json", 18052,
     "50c4b60e9eb4e5c19d820c24c57ac50b9d8bc371b48d4621caa32ba3917fc293"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/prime_field_polynomial_convolution_congruence_candidate.py", 8183,
     "effc4b2df9418d9d964fd34216c4c1c2a09d12dd885877165c6fed2e761a8b70"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/prime_field_polynomial_equivalence_candidate.py", 10469,
     "929eb67318c8a09577fb9ebac277b82656abf04c82b97a417fff83f39e7bb373"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/source-notation-dag-v1.json", 177684,
     "2d92ecdbe56e59571c0752966b29e02a83b1636d0c54ead028e0498e38c22f79"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/test_prime_field_polynomial_convolution_congruence_candidate.py", 19162,
     "224e7d441f17217616a34e9e6fe85d321ba8c1ba410675cbacf56c34b6f7c4b8"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/test_prime_field_polynomial_equivalence_candidate.py", 19312,
     "778a8c9dcd43d5bed00125f176ac013a6aabfa4ae132a3ca16ba2bae2875b0dc"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/test_working_equivalence_integration.py", 21500,
     "1aaaf10785c4ac667b506fe49bffe03b08de59859227406e571ceb4895a1e46d"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/test_working_equivalence_notation.py", 11540,
     "ed1fa13a3919b4295e75c2dc7eec6b0f22c8ad8bb04b684ef876e2f33ca9fe7e"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/working-121-verification-observations-v1.json", 18258,
     "1e3687cc8d0f3b6065b15d478e453c2fc4d44bb9ee848b21155ab470748d5f51"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/working-equivalence-global-syntax-v1.json", 11886,
     "185cfa360625c4b7d7af6a8b1b22f5f89af6c25617094c412ec19dc4276cc50a"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/working-polynomial-equivalence-rfc-v1.md", 6333,
     "56a41ea06d0bc8f40af749b245f326049fc5e95bccb2f38075d93e469f98e029"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/working_equivalence_notation.py", 8213,
     "5baa9a9c91093436e009e53f8b27327e59c15698fb96ed8268889fb6939a1456"),
    ("research/arithmetic-library/working/prime-field-equivalence-v1/working_equivalence_support.py", 24952,
     "7eebd2cdc705d6c9effa2254aa23386e2274e56609082029cde71fa57d6b0f01"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/DEFERRED_division_identity_converse.txt", 18608,
     "64d2e1197fb0a600146b07fdc3c51cf0532653dabaebb74a824a63dc166821ff"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/README.md", 10758,
     "37a415f572e1d703ef754dc2c32e1ad8ab9ab7841e39a3c0164c3891a5903f77"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/artifacts/inherited-polynomial-products-three-lemmas-seed-v1.json", 812095,
     "f4d2567e664ae3ad6092e6b54a6599d2858ac4fafc0b4343085a218da6735624"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/artifacts/inherited-successor-injective-seed-v1.json", 256,
     "bcdf16c331497c3dc26bec8cdfe92b991eb83bfe353d1d9429527a32541f1edb"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/artifacts/working-euclidean-extension-proof-bundle-v1.json", 2219445,
     "c2e097f0e04c4b4f01bb219102405d0e93bc847c19625113eb48e55c7900734d"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/artifacts/working-prime-field-euclidean-proof-bundle-v1.json", 1635441,
     "3614e9504b84cfd24a52780d54ddc9eb16e49bf2df996c99664c9427e9a9fd83"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/augment_inherited_polynomial_seed.py", 10355,
     "e9dce56cff718bdce62ecfb258e4f2eb640053c010a1ebd1e8fb433f1b4f3a0f"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/author_inherited_successor_seed.py", 7093,
     "312df3229ae99a8ec39538d8fd8c2d7f19936d9c9c70062197e0eb23c40512ea"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/check_working_euclidean.py", 9619,
     "390033da96271b2347a99d5fe5f033d1c6c60f0b82496a1707df6260de353603"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/check_working_euclidean_extension.py", 10353,
     "be03cbdb4e19b22a2ffac2ce50625b4bd9f81dcf1b9e8b8bcac782ab05cb74e4"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/current-alpha-v32-ui-observations-v1.json", 33421,
     "d5f78f0f96c57c562ffd464eb2ad71dae5cdd15b58b9811eb5d5de0e8a8a0a40"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/export_working_euclidean.py", 7319,
     "5b5ff76c08c01240baa239ca189ad3a372f5d6e7777a0aa9b12eaf88a37b19de"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/export_working_euclidean_extension.py", 5158,
     "33eb64d1e7015d596f217e5a190577bdb9f36665de5074d1922ff8af15071f56"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/inspect_euclidean_extension_seeds.py", 6797,
     "3aa8e9f74200f960641c7e14f9971dea9d4b28c763412c8f20087ecd0ff6fff5"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/inspect_working_seed_syntax.py", 11886,
     "f4b374f6696d8772bbd24a4dd830e9e5679ac2a58f8a81489a44dfa591858f61"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_convolution_padding_candidate.py", 39740,
     "2d874ecfb35a5db0aecdeb07b549464efebad9072c363113aa5a0a977845d007"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_convolution_triangular_candidate.py", 16677,
     "d53722e52ffb3f98d16d693c8cc28d605e62da8f36d5e6ecffe3df66179aa11f"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_distributivity_candidate.py", 26118,
     "a959962d631759cd1fc773dd7eef2fadf4f3f95361d6d7bc8c6a9e82d0d4ab86"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_division_candidate.py", 47986,
     "edfc7806caf7a83b9cb0e3e420bd2c3a8679f2d4d9ee6ca9f8eae53faca8d5b2"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_division_uniqueness_candidate.py", 23258,
     "6a9d9ebe1f72202743e5df2c069b9aa367fdb3d61108f1d9354cdc9276ab2d15"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/prime_field_polynomial_representation_candidate.py", 42623,
     "fc3b40a6ec88841b937251bfc2b4c2dcce55ddeec9932c2533e0f74e46fc5c6a"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/test_prime_field_polynomial_convolution_padding_candidate.py", 27054,
     "7632654e36e18cf7c872bd29dd783a55cf597e33e7b5369be178a2d2f42b87f9"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/test_prime_field_polynomial_convolution_triangular_candidate.py", 9162,
     "e6bf4d2a0b2b00336b8d83b4ffe5d068e34e3d5bd44e8af4b995ca2723289822"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/test_prime_field_polynomial_distributivity_candidate.py", 21925,
     "d6200ef1e0447f3efb98461ce343a1a3ae5530f74490bd4b7782cbc13ed2e9a6"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/test_prime_field_polynomial_division_candidate.py", 23978,
     "c4f7555b19e88789c4a561ec5b66d1f9487f44a32b388f2beea90f9ec42eed3b"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/test_prime_field_polynomial_division_uniqueness_candidate.py", 15599,
     "b74083e6707eb83e7fab3efa3f610d562edf2168511b07c5995f9ef9f7f588e2"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/test_prime_field_polynomial_representation_candidate.py", 25517,
     "75a2cee90850ff07468b1d568ce4d3665f8006fdbb892c5838186abbc8fd57b7"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/test_working_euclidean_definitions.py", 16004,
     "c30ef4a5aec9065ed745b512fef3e464e53e32a0be2d642d5f3a4f96d62cd3af"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/test_working_euclidean_extension.py", 30204,
     "f92f8784ad84247328b8ebd0f27bfe1595d9989caf37c22b2e9439bcc8ef9c4b"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/test_working_euclidean_integration.py", 18658,
     "04f66780d6b0d7408b72b8e9a8cdc54772d1593e03dfb2e61579a44410ba1038"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working-113-global-syntax-v1.json", 9835,
     "e138bc133d3ff566f98381fb18e5e74faf91fa42b0122e0f2978a1a99139e49a"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working-113-verification-observations-v1.json", 18976,
     "8b070373ea08119fc350d54286382c732d456d8bc62f995a6c1338c99f0f87f5"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working-81-global-syntax-v1.json", 10290,
     "38e99d5574810ff9820b94952d11fa7b4f17a09a030c36fd42e4df94f2bf23b7"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working-81-verification-observations-v1.json", 14806,
     "28fba8440872bcc852f43ce0511d3a7659edc6da9a773bf373f037c7495be5ac"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working-9-execution-uniqueness-observations-v1.json", 11217,
     "5c2f3ef1fd0891f86655da3028f015e9f2dbc487faede851e2918615cf0ef9f4"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working-definition-validation-observations-v1.json", 2962,
     "441d03b867ead6948610c3fc0cb63f4ec75954896f978d99fbaf9e2fc2eb9eec"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working-euclidean-extension-rfc-v1.md", 6400,
     "60227449868efa500ba8dde65d3a80697ea6c2f102d7323586de7c9aba31a280"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working-euclidean-integration-rfc-v1.md", 9958,
     "f39c915949e5ca9312553836e7672c4c1b07bffb8b6d8a4efe3d3a0c02d560d9"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working-padding23-focused-observations-v1.json", 9315,
     "08fd13f02df30c48c54da13961e44de8039c56e86ac34e3fda6131b28c9f2ea8"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working_euclidean_definition_graph.py", 1226,
     "4489cec7dff3a1ea48d12725f2d28b9c9c648543d94f8ee6a7233b3350e7ba15"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working_euclidean_definitions.py", 7278,
     "aec02f0130c3bcaa0b09395874530e2d844eb583411e1a5b7f8033c3fba9c49d"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working_euclidean_extension_support.py", 19237,
     "df377f2ada5015601945caedc93b442a83cb3142ea5d4a652bab78f705ef460e"),
    ("research/arithmetic-library/working/prime-field-euclidean-v1/working_euclidean_support.py", 18552,
     "80e73f977f2464e2f62939610667def8bbf96f19e4d95bf734c52969c39cec4a"),
)

CONTROL_SOURCES = (
    *previous_audit.CONTROL_SOURCES,
    "scripts/check_alpha_v33_research.py",
    "scripts/build_peano_library_channels_v33.py",
    "scripts/verify_peano_library_channels_v33.py",
    "scripts/peano_catalog_shards_v33.py",
    "peano-lab/py/peano_lab/library/alpha_enrollment_v33.py",
    "peano-lab/py/peano_lab/library/editions_v33.py",
    "peano-lab/py/peano_lab/library/campaign_research_v33_closure.py",
    "peano-lab/py/tests/test_library_editions_v33_admission.py",
    "peano-lab/py/tests/test_campaign_research_v33_closure.py",
    "scripts/test_check_alpha_v33_research.py",
    "scripts/test_peano_catalog_shards_v33.py",
    "scripts/test_verify_peano_library_channels_v33.py",
    "research/arithmetic-library/alpha-v33-polynomial-euclidean-promotion-rfc-v1.md",
    "research/arithmetic-library/prime-field-polynomial-euclidean-division-rfc-v1.md",
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
    from peano_lab.library import campaign_research_v33_closure as research
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
            or len({item.artifact for item in result}) != 1
            or sum(item.frontier_count for item in result) != 121
            or tuple(len(item.principal_roots) for item in result) != (8,)
            or 1 + len(result) + sum(len(item.principal_roots) for item in result) != EXPECTED_JOB_COUNT):
        raise AuditError("the exact one-family/eight-principal promotion inventory changed")
    return result


def module_test_path(module):
    """Literal canonical-test provenance, shared by all eight exact factories."""
    from peano_lab.library import campaign_research_v33_closure as research
    research.validate_research_metadata()
    if type(module) is not str or module not in research.FACTORY_BY_MODULE:
        raise AuditError("unknown exact v33 source module")
    return research.FACTORY_BY_MODULE[module].test


def _edition():
    from peano_lab.library import editions_v33
    editions_v33.require_research_seal()
    if (len(editions_v33.ALPHA_ENTRIES) != 4092
            or len(editions_v33.FRONTIER_NEW_NAMES) != 121
            or len(editions_v33.STABLE_ENTRIES) != 432):
        raise AuditError("the exact additive release partition changed")
    return editions_v33


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
    edition = _edition()
    if (len(rows) != item.frontier_count or _specs_digest(rows) != item.frontier_specs_sha256
            or not set(item.principal_roots) <= {row.name for row in rows}
            or any(edition.ALPHA_EDITION.by_name.get(row.name) is None
                   or edition.ALPHA_EDITION.by_name[row.name].spec != row for row in rows)):
        raise AuditError("literal research ownership differs from the new sealed specifications")
    return rows


def _inventory_rows():
    rows = tuple(row for item in registry() for row in _owned(item))
    if tuple(row.name for row in rows) != _edition().FRONTIER_NEW_NAMES:
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
    from peano_lab.library import campaign_research_v33_closure as research
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
    if parent.manifest.bytes != PARENT_BYTES or parent.manifest.row_count != 3971:
        raise AuditError("the immutable v32 parent manifest changed")
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


def _family(item):
    from peano_lab.library import campaign_research_v33_closure as research
    edition = _edition()
    bundle, receipt, positions = edition.checked_research_bundle(item.slug)
    payload = research.read_research_bundle_bytes(item.slug, ROOT / item.artifact)
    independent._lean_check(item, receipt.node_count, bundle.root, payload)
    if receipt.kernel_calls != len(bundle.nodes):
        raise AuditError("not every actual body reached the original HA kernel")
    return _family_syntax_report(item, bundle, receipt, positions)


def _root(item, name):
    from peano_lab.kernel.checker import check
    from peano_lab.library.theorems import _closed_formula
    rows = {row.name: row for row in _owned(item)}
    if name not in item.principal_roots:
        raise AuditError("unregistered ordinary principal")
    edition = _edition()
    result = edition.replay(name, edition="alpha")
    exact = _closed_formula(rows[name].statement)
    if result.spec != rows[name] or result.formula != exact or not check((), result.certificate, exact):
        raise AuditError("the returned ordinary empty-context certificate failed original HA")
    _, _, positions = edition.checked_research_bundle(item.slug)
    return {"slug": item.slug, "name": name, "node_id": positions[name],
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
    for spec in _edition().v32.ALPHA_CHECKED_SPECS:
        encoded = FormulaArena().freeze(_closed_formula(spec.statement)).to_json()
        fingerprint = sha256(encoded.encode()).digest()
        duplicates.extend((name, spec.name) for name, other in index.get(fingerprint, ()) if encoded == other)
    if duplicates:
        raise AuditError(f"exact duplicate promoted statements: {duplicates!r}")
    return {"new_theorems": 121, "prior_theorems": 3971, "duplicates": [],
            "exact_ast_novelty_checked": True,
            "ordered_names_sha256": sha256("\n".join(row.name for row in rows).encode()).hexdigest()}


def _validate_family_report(report, item):
    """Exact identities and bounded observational metrics from the live worker."""
    from peano_lab.library.campaign_research_v33_closure import research_plan
    from peano_lab.library.proof_bundle import DEFAULT_BUNDLE_LIMITS as limits
    rows = _owned(item)
    plan = research_plan(item.slug)
    sealed = plan.family
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
                or actual["node_id"] != plan.positions[spec.name]
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
        expected = {"new_theorems": 121, "prior_theorems": 3971, "duplicates": [],
                    "exact_ast_novelty_checked": True,
                    "ordered_names_sha256": sha256("\n".join(_edition().FRONTIER_NEW_NAMES).encode()).hexdigest()}
        if canonical(report) != canonical(expected):
            raise AuditError("changed exact whole-release novelty audit")
    elif kind == "family":
        _validate_family_report(report, item)
    elif kind == "root":
        from peano_lab.library.layered_replay import DEFAULT_LAYERED_REPLAY_LIMITS
        spec = _edition().ALPHA_EDITION.by_name[name].spec
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
    """Run exactly 10 real jobs: novelty, one HA/Lean bundle, eight ordinary roots."""
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
                         "theorem_count": 3971},
              "new_theorems": 121, "alpha_theorem_count": 4092, "stable_theorem_count": 432,
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
        raise AuditError("the exact ten-window schedule changed")
    signal.alarm(jobs * PARENT_TIMEOUT_SECONDS + WALL_SECONDS)
    audit = verify_in_fresh_windows()
    print(f"Fresh Alpha-v33 proof gates PASS: 121 new theorems; 1 complete HA/Lean bundle; "
          f"{audit.report['ordinary_principal_count']} ordinary principals; peak RSS {audit.peak_rss_bytes} bytes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
