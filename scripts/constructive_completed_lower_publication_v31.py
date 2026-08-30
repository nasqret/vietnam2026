"""Checked presentation of the nineteen completed lower-layer families.

The five older reader trees are immutable syntax/template inputs.  Their
saved receipts confer no Alpha authority: a live v31 release capability is
required before any promoted corpus or checked-use page is produced.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from dataclasses import dataclass, replace
from hashlib import sha256
from importlib import import_module
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from verify_peano_library_channels_v31 import LiveReleaseContext


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "peano-lab-constructive-completed-lower-explorer-v31"
OUTPUT_NAME = "constructive-completed-lower-explorer-v31"
HISTORICAL_OUTPUT_NAME = "constructive-historical-explorers-v31"
ATLAS_NAME = "constructive-completed-lower-campaign-v31"
CURRENT_VERSION = "v31"
PARENT_VERSION = "v30"
PARENT_COUNT = 3222
PROMOTED_COUNT = 574
CURRENT_COUNT = 3796
STABLE_COUNT = 432
PARENT_CATALOG_SHA256 = "ac7111ec14ff07bf899238ed465de337e6d76e9343384947022360dc7e65d9f7"
LEAN_BINARY_SHA256 = "22a49645acdee1a90bdf09861729d62b7a9c5bc20bc1f799ad05adc54ee0b033"
_SHA = re.compile(r"[0-9a-f]{64}")
_TAG = re.compile(r"[A-Z][A-Z0-9]{5}")


class PublicationError(ValueError):
    """A frozen reader, live authority, mathematical identity or route changed."""


@dataclass(frozen=True, slots=True)
class ReaderSnapshot:
    directory: str
    manifest_bytes: int
    manifest_sha256: str
    checkpoint_digest: str
    file_count: int
    module: str
    families: tuple[tuple[str, int], ...]


SNAPSHOTS = (
    ReaderSnapshot(
        "constructive-bottom-layer-explorer", 80818,
        "d9bd86fe6860edb19c2adab5455d9ead395b0c3f0828baeb3f1037d4bf4955bb",
        "fc592c0a4a0c385178528860634b18678e846327e9206b410cab043eb2ce7d48",
        493, "build_constructive_bottom_layer_explorer",
        (("euler-units", 32), ("prime-fields", 87), ("mobius-values", 21), ("signed-sums", 30)),
    ),
    ReaderSnapshot(
        "constructive-lower-tier-explorer", 63310,
        "ac6c7b3f53a27ba3812969031d7a3eea25bc0c2abeb7944c45f240ca5bb59c32",
        "fc8f85092b7a4ae03f3614e940c4ca4ab5cdf4da63710ea692cb10ca8be5bca9",
        371, "build_constructive_lower_tier_explorer",
        (("divisor-sums", 37), ("signed-weighted-sums", 40), ("prime-field-polynomials", 49)),
    ),
    ReaderSnapshot(
        "constructive-lower-continuation-explorer", 68313,
        "98d78a16815e40281ebf9ef0f4b8b9d183109e5c25960576189e3f5d0c0735a3",
        "25c837e9a7eb4f587f40a5d9fc5a8b0af406d91d629a48cc87115a8b2f935091",
        395, "build_constructive_lower_continuation_explorer",
        (("divisor-involutions", 12), ("mobius-divisor-cancellation", 28),
         ("rectangular-sums", 32), ("polynomial-products", 53)),
    ),
    ReaderSnapshot(
        "constructive-dirichlet-explorer", 72102,
        "9755ca72a5e0341e6f42aa8f05253009d36e0950678a917a400961201b36f921",
        "c649bb3bab89d30db671ac698578290ba813297f98d3a508ce7fa60e888ee593",
        424, "build_constructive_dirichlet_explorer",
        (("finite-support", 8), ("dirichlet-convolution", 40), ("dirichlet-fubini", 32),
         ("dirichlet-units", 25), ("mobius-inversion", 8)),
    ),
    ReaderSnapshot(
        "constructive-dirichlet-inverse-explorer", 29643,
        "0ca7c37be32f0f956b4727d60a8876d29c7b4eb97ca8a4d6c9a8195c25218568",
        "893fb32701bf85235cc15825357cdfed30b5f1bf168e2df669d1525336680ac3",
        173, "build_constructive_dirichlet_inverse_explorer",
        (("dirichlet-signed-units", 9), ("dirichlet-triangular", 10), ("dirichlet-inverses", 21)),
    ),
)

# Display order is historical reader order, not an alternate enrollment order.
FAMILY_COUNTS = dict(pair for snapshot in SNAPSHOTS for pair in snapshot.families)
FAMILY_ORDER = tuple(FAMILY_COUNTS)


def digest(payload: bytes | str) -> str:
    return sha256(payload.encode("utf-8") if isinstance(payload, str) else payload).hexdigest()


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def strict_json(payload: bytes | str):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise PublicationError("duplicate JSON member: " + key)
            result[key] = value
        return result

    def nonfinite(value):
        raise PublicationError("non-finite JSON number: " + value)

    return json.loads(payload, object_pairs_hook=pairs, parse_constant=nonfinite)


def safe_relative(value: object) -> bool:
    return (type(value) is str and bool(value) and "\\" not in value and "\x00" not in value
            and not PurePosixPath(value).is_absolute()
            and all(part not in {"", ".", ".."} for part in value.split("/")))


def read_pinned(path: Path, size: int, sha: str) -> bytes:
    if (type(size) is not int or not 0 < size <= 64 * 1024 * 1024
            or type(sha) is not str or _SHA.fullmatch(sha) is None):
        raise PublicationError("missing, unsafe or wrongly sized presentation input: " + str(path))
    path = Path(path)
    try:
        for parent in path.parents:
            if parent.is_symlink() or not parent.is_dir():
                raise PublicationError("unsafe presentation input ancestor: " + str(path))
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode) or before.st_size != size:
            raise PublicationError("missing, unsafe or wrongly sized presentation input: " + str(path))
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        with os.fdopen(descriptor, "rb") as source:
            opened = os.fstat(source.fileno())
            if (opened.st_dev, opened.st_ino, opened.st_size) != (before.st_dev, before.st_ino, size):
                raise PublicationError("presentation input changed while being opened: " + str(path))
            payload = source.read(size + 1)
            after = os.fstat(source.fileno())
        latest = path.lstat()
        if ((opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) != (after.st_size, after.st_mtime_ns, after.st_ctime_ns)
                or (latest.st_dev, latest.st_ino, latest.st_mode) != (after.st_dev, after.st_ino, after.st_mode)):
            raise PublicationError("presentation input changed while being read: " + str(path))
    except OSError as error:
        raise PublicationError("missing or unsafe presentation input: " + str(path)) from error
    if len(payload) != size or digest(payload) != sha:
        raise PublicationError("pinned presentation input changed: " + str(path))
    return payload


def _snapshot_directory(snapshot: ReaderSnapshot, root: Path) -> Path:
    directory = root
    for part in ("book", "_static", snapshot.directory):
        if directory.is_symlink() or not directory.is_dir():
            raise PublicationError("unsafe frozen reader directory")
        directory /= part
    if directory.is_symlink() or not directory.is_dir():
        raise PublicationError("unsafe frozen reader directory")
    return directory


def snapshot_manifest(snapshot: ReaderSnapshot, *, root: Path = ROOT) -> dict:
    directory = _snapshot_directory(snapshot, root)
    raw = read_pinned(directory / "manifest.json", snapshot.manifest_bytes, snapshot.manifest_sha256)
    manifest = strict_json(raw)
    if (type(manifest) is not dict or json_bytes(manifest) != raw
            or manifest.get("checkpoint_digest") != snapshot.checkpoint_digest
            or type(manifest.get("files")) is not dict
            or len(manifest["files"]) + 1 != snapshot.file_count
            or manifest.get("file_count_excluding_manifest") != snapshot.file_count - 1):
        raise PublicationError("the frozen reader manifest has the wrong inventory")
    for relative, pin in manifest["files"].items():
        if (not safe_relative(relative) or relative == "manifest.json" or type(pin) is not dict
                or set(pin) != {"bytes", "sha256"} or type(pin["bytes"]) is not int
                or not 0 < pin["bytes"] <= 64 * 1024 * 1024
                or type(pin["sha256"]) is not str or _SHA.fullmatch(pin["sha256"]) is None):
            raise PublicationError("malformed frozen reader file pin")
    return manifest


def snapshot_file(snapshot: ReaderSnapshot, manifest: Mapping[str, Any], relative: str, *, root: Path = ROOT) -> bytes:
    if not safe_relative(relative) or relative not in manifest["files"]:
        raise PublicationError("a reader requested an unregistered input file")
    directory = _snapshot_directory(snapshot, root)
    path = directory
    for part in relative.split("/"):
        if path.is_symlink():
            raise PublicationError("a frozen reader contains a symlink ancestor")
        path /= part
    pin = manifest["files"][relative]
    return read_pinned(path, pin["bytes"], pin["sha256"])


def authenticate_snapshots(*, root: Path = ROOT) -> dict[str, dict]:
    """Freshly authenticate every old file without decoding a proof bundle."""
    if len(FAMILY_COUNTS) != 19 or sum(FAMILY_COUNTS.values()) != PROMOTED_COUNT:
        raise PublicationError("the exact nineteen completed family inventory changed")
    manifests = {}
    for snapshot in SNAPSHOTS:
        manifest = snapshot_manifest(snapshot, root=root)
        directory = _snapshot_directory(snapshot, root)
        actual = set()
        for path in directory.rglob("*"):
            if path.is_symlink() or not (path.is_file() or path.is_dir()):
                raise PublicationError("a frozen reader contains a nonregular entry")
            if path.is_file():
                actual.add(path.relative_to(directory).as_posix())
        if actual != set(manifest["files"]) | {"manifest.json"}:
            raise PublicationError("a frozen reader has missing or extra files")
        for relative in manifest["files"]:
            snapshot_file(snapshot, manifest, relative, root=root)
        manifests[snapshot.directory] = manifest
    return manifests


# Mathematical scope is current presentation, not a rewrite of historical
# records.  Complete G007/G014 endpoints are distinct from their prerequisites;
# the prime-power and multiplicativity targets remain open.
_CAVEATS = {
    "euler-units": "The exact G014 theorem covers m>1 and genuinely invertible a. Phi counts coprime residues independently of the conclusion. The broader coprime theorem handles m=1 by congruence, not by asserting that one is a canonical remainder. Multiplicative-order and RSA statements are not claimed.",
    "mobius-values": "Mobius(n,z) is positive-domain only, independently defined from squarefreeness and actual prime-factor parity. Signed codes 0, 2 and 1 represent zero, +1 and -1. This family proves values and prime-adjunction laws; the separate Möbius-inversion family supplies the complete G007 endpoint.",
    "signed-sums": "These are actual signed-table and finite-sum foundations. Equality compares represented signed values, not arbitrary encodings. MatrixMinorFourCode is reused solely as generic nested pairing, without a matrix hypothesis. Full finite signed G007 is established separately in the Möbius-inversion family.",
    "divisor-sums": "A genuine divisor mask has S n entries, indexed zero through n, and forces its zeroth entry to zero regardless of F(0). Möbius values remain positive-domain only. This family constructs divisor sums and Möbius tables; cancellation and the full G007 endpoint are separately proved later in the same release.",
    "signed-weighted-sums": "Operation tables contain actual beta-coded entries and compare represented signed values, not encodings. The strict sum window is i<l and the separately certified endpoint i=l is unused. Rectangular Fubini and full finite signed Möbius inversion are separate, now-admitted families.",
    "divisor-involutions": "The complementary quotient is witnessed by n=d*q at positive divisors. The actual permutation covers indices zero through n, fixing zero and nondivisors. This is the involution foundation for the separate cancellation and full G007 inversion proofs, not an assumed divisor bijection.",
    "mobius-divisor-cancellation": "The input n is positive. Signed code 2 denotes +1, so the actual sum is +1 at n=1 and zero for n>1. The positive-values result permits arbitrary F(0), which the divisor mask excludes. Prime-square multiples contribute zero. Full G007 inversion is established in its separate family.",
    "rectangular-sums": "Every slice, row table, column table and signed sum is an actual beta-coded witness. Entries are F((o+s*i)+t*j), for i<m and j<n. Zero dimensions and zero strides are allowed; separately certified endpoints are unused. Table uniqueness concerns values, not codes. No infinite-sum assertion is made.",
    "dirichlet-convolution": "Each retained summand has a witnessed n=d*q and actual signed multiplication. Zero and nondivisors contribute zero. Input and output values at zero are unrestricted; uniqueness is for positive represented values. The separate inverse family proves the unit-at-one criterion. Full G009 still requires multiplicative-function closure.",
    "dirichlet-units": "Signed one is code 2. Positive-only table graphs preserve arbitrary zeroth values, including N=0. The unit and divisor-sum identities are proved, never embedded in definitions. The separate inverse family proves the general unit-at-one criterion; multiplicative-function closure remains open.",
    "mobius-inversion": "The full finite signed G007 theorem includes the reverse equivalence and actual witnesses at N=0. The divisor-transform premise covers every required positive quotient. F(0), G(0) and H(0) are unrestricted; only the historical Möbius witness retains its separate zero convention. Full G009 multiplicative closure and G091 prime-power fields remain open.",
    "dirichlet-inverses": "For an actual table an inverse exists exactly when N=0 or F(1) is signed +1 or -1. At a positive window this is the unit-at-one criterion; the empty window imposes no condition at one. Every inverse has actual delta and two-sided convolution witnesses. Its zeroth value is arbitrary, so uniqueness is positive-value equality, not equality of codes or of zeroth values. Multiplicative-function closure and full G009 remain open.",
}


def family_models() -> tuple[Any, ...]:
    """Read frozen display metadata only; never call an old proof builder."""
    result = []
    for snapshot in SNAPSHOTS:
        module = import_module(snapshot.module)
        models = module.FAMILIES if snapshot.module == "build_constructive_bottom_layer_explorer" else module.families()
        if tuple(family.slug for family in models) != tuple(slug for slug, _ in snapshot.families):
            raise PublicationError("frozen family display metadata changed")
        for family in models:
            result.append(replace(family, caveat=_CAVEATS.get(family.slug, family.caveat)))
    if tuple(family.slug for family in result) != FAMILY_ORDER:
        raise PublicationError("the completed family order changed")
    return tuple(result)


def frozen_corpora(manifests: Mapping[str, dict], *, root: Path = ROOT) -> dict[str, dict]:
    result = {}
    for snapshot in SNAPSHOTS:
        manifest = manifests[snapshot.directory]
        for slug, count in snapshot.families:
            corpus = strict_json(snapshot_file(snapshot, manifest, slug + "/api/corpus.json", root=root))
            if (corpus.get("family_slug") != slug or corpus.get("node_count") != count
                    or len(corpus.get("nodes", ())) != count
                    or corpus.get("alpha_checked_use_node_count") != 0
                    or corpus.get("stable_admitted_node_count") != 0
                    or corpus.get("local_checkpoint_verified") is not True
                    or corpus.get("original_ha_bundle_verified") is not True
                    or corpus.get("independent_lean_bundle_verified") is not True):
                raise PublicationError("a frozen research corpus changed its exact scope")
            names = [node["name"] for node in corpus["nodes"]]
            if (len(set(names)) != count or set(corpus.get("tags", ())) != set(names)
                    or len(set(corpus["tags"].values())) != count
                    or any(_TAG.fullmatch(tag) is None for tag in corpus["tags"].values())):
                raise PublicationError("a frozen research family lost its stable tags")
            for node in corpus["nodes"]:
                if (node.get("id") != corpus["tags"][node["name"]]
                        or node.get("statement_sha256") != digest(node["statement"])
                        or any(node.get(flag) is not False for flag in
                               ("enrolled_in_alpha", "admitted_to_alpha", "alpha_checked_use", "checked_use", "stable_member", "admitted_to_stable"))
                        or node.get("defined", {}).get("exact_ast_equivalence") is not True):
                    raise PublicationError("a frozen research theorem changed identity or notation")
            result[slug] = corpus
    names = [node["name"] for corpus in result.values() for node in corpus["nodes"]]
    if len(names) != PROMOTED_COUNT or len(set(names)) != PROMOTED_COUNT:
        raise PublicationError("the nineteen readers omit or duplicate a promoted theorem")
    return result


def family_metadata(corpora: Mapping[str, dict] | None = None) -> tuple[dict, ...]:
    """Exact stable routes/roots for the separately owned current atlas."""
    if corpora is None:
        manifests = {item.directory: snapshot_manifest(item) for item in SNAPSHOTS}
        corpora = frozen_corpora(manifests)
    return tuple({
        "slug": family.slug, "title": family.title, "prefix": family.prefix,
        "domain": family.domain, "family": family.family_id,
        "goals": list(family.milestones), "theorem_count": FAMILY_COUNTS[family.slug],
        "root_names": list(family.roots),
        "root_tags": {name: corpora[family.slug]["tags"][name] for name in family.roots},
        "tags": dict(corpora[family.slug]["tags"]), "caveat": family.caveat,
    } for family in family_models())


def validate_definition_identities(corpora: Mapping[str, dict]) -> dict:
    from constructive_dirichlet_inverse_definitions import ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME

    definitions = ALL_CONSTRUCTIVE_DEFINITIONS_BY_NAME
    if (len(definitions) != 372
            or sum(len(item.conceptual_dependencies) for item in definitions.values()) != 787):
        raise PublicationError("the unchanged conservative 372-definition/787-edge registry changed")
    records = []
    for item in definitions.values():
        records.append({"id": item.stable_id, "name": item.name, "parameters": list(item.parameters),
                        "expanded_template": item.template_source,
                        "dependencies": [definitions[name].stable_id for name in item.conceptual_dependencies]})
    for corpus in corpora.values():
        for row in corpus["definitions"]:
            item = definitions.get(row["name"])
            if (item is None or row["id"] != item.stable_id
                    or tuple(row["parameters"]) != item.parameters or row["arity"] != item.arity
                    or row["expanded_template"] != item.template_source
                    or row["expansion_sha256"] != digest(item.template_source)
                    or row["dependency_names"] != list(item.conceptual_dependencies)
                    or row["dependencies"] != [definitions[name].stable_id for name in item.conceptual_dependencies]
                    or row.get("exact_ast_verified") is not True
                    or row.get("kernel_signature_unchanged") is not True):
                raise PublicationError("a reader changed a conservative definition identity")
    return {"definition_count": 372, "definition_dependency_count": 787,
            "definition_inventory_sha256": digest(json_bytes(records)),
            "definitions_are_not_proof_evidence": True}


def require_live(context: LiveReleaseContext) -> None:
    """Only the release verifier can issue the capability accepted here."""
    from verify_peano_library_channels_v31 import LiveReleaseContext

    if type(context) is not LiveReleaseContext:
        raise PublicationError("a live v31 verification capability is required")
    context.require_unchanged()
    catalog = context.catalog
    rows = catalog.get("theorems", ())
    channel = context.channels.get("channels", {}).get("alpha", {})
    if (catalog.get("checked_use_count") != CURRENT_COUNT or len(rows) != CURRENT_COUNT
            or catalog.get("stable_count") != STABLE_COUNT
            or context.channels.get("default_channel") != "stable"
            or channel.get("artifact_sha256") != context.catalog_sha256
            or context.revision != context.catalog_sha256[:12]
            or len(context.families) != len(FAMILY_ORDER) or set(context.families) != set(FAMILY_ORDER)
            or len(context.promoted_names) != PROMOTED_COUNT
            or len(set(context.promoted_names)) != PROMOTED_COUNT
            or tuple(row["name"] for row in rows[PARENT_COUNT:]) != context.promoted_names
            or type(context.source_binding_sha256) is not str
            or _SHA.fullmatch(context.source_binding_sha256) is None
            or context.source_binding_sha256 != context._audit.binding):
        raise PublicationError("live release authority does not match the exact v31 slice")


def _check_literal_row(node: Mapping[str, Any], row: Mapping[str, Any]) -> None:
    for key in ("name", "statement", "script", "dependencies", "summary", "statement_sha256"):
        if node.get(key) != row.get(key):
            raise PublicationError("the reader differs from its actual admitted theorem: " + str(node.get("name")))
    if (row.get("statement_sha256") != digest(row["statement"])
            or row.get("script_sha256") != digest("\n".join(row["script"]) + "\n")
            or row.get("body_checked") is not True or row.get("checked_use") is not True
            or row.get("membership") != "alpha_only" or row.get("evidence_status") != "alpha_closed"):
        raise PublicationError("the displayed new theorem lacks genuine Alpha checked-use evidence")


def _promote_corpus(original: dict, report: Mapping[str, Any], context: LiveReleaseContext,
                    by_name: Mapping[str, dict], routes: Mapping[str, str]) -> dict:
    """Private pure projection, reached only after the live capability guard."""
    slug = original["family_slug"]
    bundle = report["bundle"]
    owned = report["owned_node_ids"]
    metrics = {row["name"]: row for row in report["rows"]}
    expected_names = tuple(node["name"] for node in original["nodes"])
    principals = report["principal_roots"]
    if (set(owned) != set(expected_names) or set(metrics) != set(expected_names)
            or len(metrics) != len(report["rows"])
            or bundle.get("original_ha_checked") is not True
            or bundle.get("independent_lean_checked") is not True
            or bundle.get("sha256") != original["proof_bundle_sha256"]
            or bundle.get("nodes_including_packaging_root") != original["proof_bundle_node_count"]
            or bundle.get("kernel_calls") != bundle["nodes_including_packaging_root"]
            or not principals or len({row["name"] for row in principals}) != len(principals)
            or any(row.get("complete_ordinary_ha_checked") is not True
                   or type(row.get("ordinary_certificate_nodes")) is not int
                   or not 0 < row["ordinary_certificate_nodes"] <= 500000
                   or row["name"] not in owned or row["node_id"] != owned[row["name"]]
                   or row["statement_sha256"] != by_name[row["name"]]["statement_sha256"]
                   for row in principals)):
        raise PublicationError("the family lacks its exact freshly checked proof and ordinary roots")
    corpus = deepcopy(original)
    status = "Alpha v31 checked-use · first admitted v31 · independently kernel and Lean verified; not Stable"
    for node in corpus["nodes"]:
        row, observed = by_name[node["name"]], metrics[node["name"]]
        _check_literal_row(node, row)
        receipt = row["empty_context_closure"]
        if (receipt.get("status") != "checked" or receipt.get("kernel_mode") != "intuitionistic"
                or receipt.get("certificate_sha256") != bundle["sha256"]
                or receipt.get("bundle_node_id") != owned[node["name"]]
                or node["proof_bundle_node_id"] != owned[node["name"]]
                or observed.get("node_id") != owned[node["name"]]
                or observed.get("statement_sha256") != node["statement_sha256"]
                or observed.get("proof_nodes") != node["body_proof_nodes"]
                or observed.get("proof_depth") != node["body_proof_depth"]
                or receipt.get("body_proof_nodes") != observed["proof_nodes"]
                or receipt.get("body_proof_depth") != observed["proof_depth"]):
            raise PublicationError("a displayed proof node differs from the fresh checked bundle")
        node.update(status=status, enrolled_in_alpha=True, admitted_to_alpha=True,
                    alpha_checked_use=True, checked_use=True, alpha_evidence="alpha_closed",
                    alpha_edition_version=CURRENT_VERSION, alpha_first_enrolled_version=CURRENT_VERSION,
                    stable_member=False, admitted_to_stable=False)
    for external in corpus["external_dependencies"]:
        row = by_name.get(external["name"])
        if (row is None or row.get("checked_use") is not True or row.get("body_checked") is not True
                or external.get("statement") != row["statement"]
                or external.get("statement_sha256") != row["statement_sha256"]):
            raise PublicationError("an external reader prerequisite differs from the current checked theorem")
        external["historical_inventory_role"] = external.get("inventory_role")
        external.update(inventory_role="current_alpha_checked_prerequisite", evidence=row["evidence_status"],
                        alpha_evidence=row["evidence_status"], enrolled_in_alpha=True,
                        admitted_to_alpha=True, alpha_checked_use=True, checked_use=True,
                        alpha_edition_version=CURRENT_VERSION, stable_member=row["membership"] == "stable",
                        admitted_to_stable=row["membership"] == "stable")
    corpus["historical_checkpoint_report"] = corpus.pop("checkpoint_report")
    corpus["historical_goal_scope"] = corpus["campaign_goal_scope"]
    corpus.update(
        schema=SCHEMA, publication_scope="alpha_checked_use_publication", candidate_status=status,
        enrolled_in_alpha=True, admitted_to_alpha=True, alpha_checked_use=True, checked_use=True,
        stable_member=False, admitted_to_stable=False, alpha_enrolled_node_count=len(expected_names),
        alpha_checked_use_node_count=len(expected_names), stable_admitted_node_count=0,
        alpha_edition_version=CURRENT_VERSION, alpha_first_enrolled_version=CURRENT_VERSION,
        alpha_catalog_sha256=context.catalog_sha256,
        alpha_first_enrollment_catalog_sha256=context.catalog_sha256,
        alpha_edition_identity_sha256=context.catalog["edition_identity_sha256"],
        alpha_edition_checked_use_count=CURRENT_COUNT, navigation_revision=context.revision,
        alpha_proof_bundle_sha256=bundle["sha256"], first_alpha_admission_report=deepcopy(report),
        external_theorem_routes={name: route for name, route in routes.items() if name not in corpus["tags"]},
        render_evidence_provenance="actual_same_live_v31_release_verifier_capability",
        release_source_binding_sha256=context.source_binding_sha256,
    )
    if slug == "mobius-inversion":
        corpus["campaign_goal_scope"] = "full_G007_finite_signed_mobius_inversion_alpha_closed"
    elif slug == "euler-units":
        corpus["campaign_goal_scope"] = "full_G014_alpha_closed"
    elif "G007" in corpus["campaign_milestone_ids"]:
        corpus["campaign_goal_scope"] = "proved_prerequisite_family_separate_full_G007_alpha_closed"
    elif slug == "dirichlet-inverses":
        corpus["campaign_goal_scope"] = "general_finite_signed_inverse_criterion_alpha_closed_full_G009_open"
    return corpus


__all__ = (
    "SNAPSHOTS", "FAMILY_COUNTS", "FAMILY_ORDER", "PublicationError", "ReaderSnapshot",
    "family_metadata", "family_models", "snapshot_manifest", "snapshot_file",
    "authenticate_snapshots", "frozen_corpora", "validate_definition_identities",
    "require_live", "json_bytes", "strict_json",
)
