#!/usr/bin/env python3
"""A new current-release projection of forty-four immutable historical readers.

The pinned inputs are presentation and provenance, never a substitute for the
live v31 verifier.  First admission, source editions, mathematical syntax and
non-admitted aliases survive this projection unchanged.  No old tree is edited.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterator, Mapping
from copy import deepcopy
from dataclasses import dataclass
from html import escape
from html.parser import HTMLParser
import json
from pathlib import Path
import posixpath
import re
from typing import TYPE_CHECKING
from urllib.parse import parse_qsl, unquote, urlencode, urlsplit, urlunsplit

import constructive_completed_lower_publication_v31 as publication

if TYPE_CHECKING:
    from verify_peano_library_channels_v31 import LiveReleaseContext


ROOT = publication.ROOT
OUTPUT = ROOT / "book/_static" / publication.HISTORICAL_OUTPUT_NAME
SCHEMA = "peano-lab-constructive-historical-publication-v31-manifest"
DESCRIPTOR_SCHEMA = "peano-lab-historical-first-admission-v1"


@dataclass(frozen=True, slots=True)
class HistoricalSnapshot:
    directory: str
    manifest_bytes: int
    manifest_sha256: str
    slugs: tuple[str, ...]
    flagship: bool = False
    defined: bool = False


SNAPSHOTS = (
    HistoricalSnapshot("pa-proof-explorer", 183604, "dcdd1d3bd2915d901bf7244eca49d2364a9799aa07c3a16b71a5d384b6e1eaec", ("quadratic-reciprocity",), True),
    HistoricalSnapshot("pa-proof-explorer/defined", 189280, "4280853ad9facded5bcbfcfa0762c9aba709df6d65cac4ded2909f5970782e3e", ("quadratic-reciprocity",), True, True),
    HistoricalSnapshot("bertrand-proof-explorer", 177717, "c5035a7adef61c4414701bb84ba412a99db460c2eebcd11e5aab393587624f1b", ("bertrand-postulate",), True),
    HistoricalSnapshot("bertrand-proof-explorer/defined", 182287, "9f1a73a38ba1bb0ec108efb1616b19e23ab6d9cfd7bd384718505389bdb84b1e", ("bertrand-postulate",), True, True),
    HistoricalSnapshot("constructive-frontier-explorer", 319521, "416aba94c6a451d7080d7503fd1d093e822fc2ad5afb07fa92bada0bda34e021", ("supplementary-laws", "kummer", "two-squares", "four-squares", "lucas", "pythagorean-fermat-four")),
    HistoricalSnapshot("constructive-next-layer-explorer", 27841, "66c5baf8e317d1ab391f74ffea161e9869995ac7b34017bf449c6ccc9a74c155", ("polynomial-horner", "matrix-dot-product", "bertrand-prime-chains", "continued-fractions")),
    HistoricalSnapshot("constructive-advanced-layer-explorer", 34139, "6e26d5327493e69deee675be977ad216c703b768e6956717b44e9a3760499dc6", ("matrix-coded-products", "euclidean-complexity", "binary-modular-exponentiation")),
    HistoricalSnapshot("constructive-transport-layer-explorer", 38703, "868405ab8cbf7cdcdfe830ff5772dd1be9812757c755555541c3e55e801081f0", ("binary-length", "euclidean-gcd-transport", "binary-modular-execution")),
    HistoricalSnapshot("constructive-milestone-closure-explorer", 40557, "a3b49ffb8d7147fabc12a32a195370ad550047c6bb54137c0b3470c96b91bf15", ("euclidean-logarithmic-bound", "binary-digit-extraction", "primes-three-mod-four")),
    HistoricalSnapshot("constructive-research-layer-explorer", 38058, "1cbcb25267304abc0331c6ea09ec40c1ebe792f537689cb2f8af4c3c4c98d3ec", ("matrix-determinant-minors", "polynomial-hensel", "generalized-crt-fold")),
    HistoricalSnapshot("constructive-breakthrough-layer-explorer", 46166, "83186a2fee2108f091192f1eb46cd7b4e4eb0082268cbd7b39870c4da224e1f6", ("matrix-cofactor-expansion", "polynomial-taylor-hensel", "generalized-crt-compatibility")),
    HistoricalSnapshot("constructive-second-wave-explorer-v30", 199909, "502bc77536b7ec5b7bfc14a0f140e43eef59d4943083edbf861527cbb3a1c5ca", ("integer-linear-algebra", "hensel-lifting", "generalized-crt", "multinomial-kummer", "prime-count-chebyshev", "cornacchia", "cauchy-davenport")),
    HistoricalSnapshot("constructive-lower-layer-explorer-v30", 98859, "6a40a3ec03840ad8ae73a6a29b594bd04d666a2aeb251a5f07fbfff2fd85bda2", ("arithmetic-foundations", "prime-enumeration", "gaussian-integers", "eisenstein-integers")),
    HistoricalSnapshot("constructive-priority-layer-explorer-v30", 132546, "053085cc23b973bff277f506b9ea2f14e104b152f6a053c44d01e9b8686aae00", ("prime-valuation-support", "best-approximation", "totient-products", "squarefree-kernels", "exponent-lifting")),
    HistoricalSnapshot("constructive-gaussian-factorization-explorer", 80302, "3897c42a773ebcecb3616bdaeb548506e7cdd0d4ddd2047ce97c4b3ea73e8fba", ("gaussian-factorization",)),
)
FAMILY_ORDER = tuple(slug for item in SNAPSHOTS if not item.defined for slug in item.slugs)
LANDINGS = {
    "quadratic-reciprocity": ("deploy/proofs/quadratic-reciprocity.html", 4737, "6ba69ea6f150bfea2a100e3d145b814dfb355eceee488aff349627afe3607351"),
    "bertrand-postulate": ("deploy/proofs/bertrand-postulate.html", 5106, "410666ee31c1b1cc870ca2e5ab510842d9d85e7fd717562083aa26ab64eba3df"),
}
FIRST_CATALOGS = {
    "v13": "cad57a21657e2df09f01174069efcfed194d87b68c0b4042b234df5759583e5a",
    "v14": "37ad33cc709903ae327ca72c67f9308a6214e2792b9269cd3b16e6e5527260fa",
    "v15": "0123e5938f43cf67833751e2a6102d6598ac24c9be6db9a0d353ec3f55e5f32c",
    "v19": "f1c3d3fba013ca3a5b62a4103dd00bd5b7e39b1f785ed9023099704ad033004b",
    "v20": "8f86225cc560d7b59ff665e58594ac6249c12dbb5cdfe47ae2708a0e497c86ce",
    "v21": "84bafa545c3c529eb4bcda9d9b501af8577a8e414f5cabf58a4c2a88da5129f1",
    "v22": "fd0e385e3d0c2d614bfa2754a2c3b70939b9437076ec53501082ddfb5bf9ae22",
    "v23": "818da349674b1ef33c17fa85b2e9a0a6653370046d88e7814300297f7bc7f4d2",
    "v24": "94ac4d193cbfe8c2ec04e54024221bc2c3a534c0ae014d381663b86174b3dcc1",
    "v25": "75fa146ac19bf6aa5f799265b6fc031b725c1e1b2e044854da91b31898d5876e",
    "v26": "969c261f924060552dda393427b4fbc51515b9d4e69daa17f5e9f1691b5ab534",
    "v27": "481a9a378e54dc389422819587e8377a07b63a0d5d50286ffdfd28f0c4bdb2e6",
    "v28": "897410581b66552c7f01f4b1266de887e52b3198b1ff2d2ac5135ab694d467e9",
    "v29": "2db42c10aa3196dda6a2fff73db02a86906091826a880abf4b38227f5f34f0b0",
    "v30": publication.PARENT_CATALOG_SHA256,
}
_FIRST_FIELDS = (
    "alpha_first_enrolled_version", "first_enrollment_catalog_sha256",
    "alpha_first_enrollment_catalog_sha256", "historical_alpha_edition_version",
    "historical_alpha_catalog_sha256", "proof_edition_version", "proof_edition_identity_sha256",
    "source_edition_version", "source_edition_identity_sha256", "source_scope_policy",
)
_AUTHORITY_FIELDS = (
    "enrolled_in_alpha", "admitted_to_alpha", "alpha_checked_use", "checked_use",
    "stable_member", "admitted_to_stable", "alpha_evidence", "evidence_status",
)


def canonical_bytes(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                      separators=(",", ":")).encode("utf-8")


def _directory(item: HistoricalSnapshot, *, root: Path = ROOT) -> Path:
    directory = root
    for part in ("book", "_static", *item.directory.split("/")):
        if directory.is_symlink() or not directory.is_dir():
            raise publication.PublicationError("unsafe historical input ancestor")
        directory /= part
    if directory.is_symlink() or not directory.is_dir():
        raise publication.PublicationError("unsafe historical input directory")
    return directory


def source_manifest(item: HistoricalSnapshot, *, root: Path = ROOT) -> dict:
    raw = publication.read_pinned(_directory(item, root=root) / "manifest.json",
                                  item.manifest_bytes, item.manifest_sha256)
    result = publication.strict_json(raw)
    records = result.get("files") if type(result) is dict else None
    if type(records) is not list or not records:
        raise publication.PublicationError("missing historical file inventory")
    seen = set()
    for pin in records:
        if (type(pin) is not dict or set(pin) != {"path", "bytes", "sha256"}
                or not publication.safe_relative(pin["path"]) or pin["path"] in seen
                or pin["path"] == "manifest.json" or type(pin["bytes"]) is not int
                or not 0 < pin["bytes"] <= 64 * 1024 * 1024
                or type(pin["sha256"]) is not str
                or re.fullmatch(r"[0-9a-f]{64}", pin["sha256"]) is None):
            raise publication.PublicationError("malformed or duplicate historical file pin")
        seen.add(pin["path"])
    if not item.flagship and tuple(row["slug"] for row in result["families"]) != item.slugs:
        raise publication.PublicationError("historical family inventory changed")
    return result


def source_file(item: HistoricalSnapshot, pins: Mapping[str, dict], relative: str, *, root: Path = ROOT) -> bytes:
    if not publication.safe_relative(relative) or relative not in pins:
        raise publication.PublicationError("unregistered historical input")
    path = _directory(item, root=root)
    for part in relative.split("/"):
        if path.is_symlink():
            raise publication.PublicationError("historical input has a symlink ancestor")
        path /= part
    pin = pins[relative]
    return publication.read_pinned(path, pin["bytes"], pin["sha256"])


def manifests(*, root: Path = ROOT) -> dict[str, dict]:
    if len(FAMILY_ORDER) != 44 or len(set(FAMILY_ORDER)) != 44:
        raise publication.PublicationError("wrong exact historical family inventory")
    return {item.directory: source_manifest(item, root=root) for item in SNAPSHOTS}


def _corpus_path(item: HistoricalSnapshot, slug: str) -> str:
    if item.flagship:
        return "api/current-corpus.json" if slug == "quadratic-reciprocity" else "api/corpus.json"
    return slug + "/api/corpus.json"


def _nodes(corpus: dict) -> list[dict]:
    values = corpus.get("nodes", corpus.get("theorems"))
    if type(values) is not list or not values:
        raise publication.PublicationError("missing historical theorem records")
    if any(type(row) is not dict or type(row.get("name")) is not str for row in values):
        raise publication.PublicationError("malformed historical theorem record")
    if len({row["name"] for row in values}) != len(values):
        raise publication.PublicationError("duplicate historical theorem name")
    return values


def _tags(item: HistoricalSnapshot, slug: str, corpus: dict, pins: dict, *, root: Path = ROOT) -> dict[str, str]:
    if "tags" in corpus:
        tags = dict(corpus["tags"])
    elif item.flagship:
        tags = {row["name"]: row["tag"] for row in _nodes(corpus)}
    else:
        graph = publication.strict_json(source_file(item, pins, slug + "/explorer/defined/api/graph.json", root=root))
        tags = {row["name"]: row["id"] for row in graph["nodes"] if row.get("kind") == "theorem"}
    if (set(tags) != {row["name"] for row in _nodes(corpus)}
            or len(set(tags.values())) != len(tags)
            or any(type(tag) is not str or re.fullmatch(r"[A-Z][A-Z0-9]{5}", tag) is None for tag in tags.values())):
        raise publication.PublicationError("historical stable tags changed")
    return tags


def first_admission_records(item: HistoricalSnapshot, slug: str, manifest: dict,
                            corpus: dict, tags: dict[str, str]) -> dict:
    """Literal historical provenance, including explicit absence of first data."""
    relative = _corpus_path(item, slug)
    pin = next(row for row in manifest["files"] if row["path"] == relative)
    family = {} if item.flagship else next(row for row in manifest["families"] if row["slug"] == slug)
    per_theorem, versions = [], set()
    for row in _nodes(corpus):
        first = row.get("alpha_first_enrolled_version", row.get("alpha_admission_version"))
        if first is not None:
            if type(first) is not str or first not in FIRST_CATALOGS:
                raise publication.PublicationError("unregistered first-admission version")
            versions.add(first)
        per_theorem.append({
            "name": row["name"], "tag": tags[row["name"]],
            "recorded_first_version": first if first is not None else "not_recorded",
            "recorded_authority": {key: row[key] for key in _AUTHORITY_FIELDS if key in row},
        })
    return {
        "schema": DESCRIPTOR_SCHEMA,
        "policy": "preserve_recorded_first_admission_without_inferring_it_from_current_or_proof_editions",
        "source_manifest": {"path": "book/_static/" + item.directory + "/manifest.json",
                            "bytes": item.manifest_bytes, "sha256": item.manifest_sha256},
        "source_corpus": {"path": "book/_static/" + item.directory + "/" + relative,
                          "bytes": pin["bytes"], "sha256": pin["sha256"]},
        "source_manifest_fields": {key: manifest[key] for key in _FIRST_FIELDS if key in manifest},
        "source_family_fields": {key: family[key] for key in _FIRST_FIELDS if key in family},
        "source_corpus_fields": {key: corpus[key] for key in _FIRST_FIELDS if key in corpus},
        "catalog_sha256_by_recorded_version": {version: FIRST_CATALOGS[version] for version in sorted(versions)},
        "per_theorem": per_theorem,
    }


def first_admission_descriptor(item: HistoricalSnapshot, slug: str, manifest: dict,
                               corpus: dict, tags: dict[str, str]) -> dict:
    """Compact manifest identity; the full exact row records stay file-pinned."""
    records = first_admission_records(item, slug, manifest, corpus, tags)
    raw = publication.json_bytes(records)
    versions = Counter(row["recorded_first_version"] for row in records["per_theorem"])
    return {
        **{key: value for key, value in records.items() if key != "per_theorem"},
        "theorem_count": len(records["per_theorem"]),
        "recorded_first_version_counts": dict(sorted(versions.items())),
        "per_theorem_records": {"path": slug + "/api/first-admission.json",
                                "bytes": len(raw), "sha256": publication.digest(raw)},
    }


def family_metadata(*, root: Path = ROOT) -> tuple[dict, ...]:
    """Read-only source metadata.  This function neither verifies nor admits."""
    result = []
    for item in SNAPSHOTS:
        if item.defined:
            continue
        manifest = source_manifest(item, root=root)
        pins = {row["path"]: row for row in manifest["files"]}
        for slug in item.slugs:
            corpus = publication.strict_json(source_file(item, pins, _corpus_path(item, slug), root=root))
            tags = _tags(item, slug, corpus, pins, root=root)
            first = first_admission_descriptor(item, slug, manifest, corpus, tags)
            old = {} if item.flagship else next(row for row in manifest["families"] if row["slug"] == slug)
            if slug in LANDINGS:
                title = "Quadratic Reciprocity" if slug == "quadratic-reciprocity" else "Bertrand's Postulate"
            else:
                title = corpus.get("family_title", corpus.get("title"))
            checked = sum(row.get("alpha_checked_use") is True for row in _nodes(corpus))
            stable = sum(row.get("stable_member", row.get("admitted_to_stable")) is True for row in _nodes(corpus))
            result.append({
                "slug": slug, "title": title, "theorem_count": len(tags),
                "checked_use_count": checked, "stable_count": stable,
                "checked_names": [row["name"] for row in _nodes(corpus) if row.get("alpha_checked_use") is True],
                "tags": tags, "root_tags": old.get("root_tags", {}),
                "source_directory": item.directory,
                "first_admission": first,
                "first_admission_sha256": publication.digest(canonical_bytes(first)),
            })
    if tuple(row["slug"] for row in result) != FAMILY_ORDER:
        raise publication.PublicationError("the historical forty-four family order changed")
    return tuple(result)


def first_admission_hashes() -> dict[str, str]:
    return {row["slug"]: row["first_admission_sha256"] for row in family_metadata()}


def theorem_routes(metadata: tuple[dict, ...] | None = None) -> dict[str, str]:
    """Prefer the first actual historical reader when a theorem has aliases."""
    result = {}
    for family in family_metadata() if metadata is None else metadata:
        for name, tag in family["tags"].items():
            if name in family["checked_names"]:
                result.setdefault(name, family["slug"] + "/explorer/defined/tag/" + tag + ".html")
    return result


def authenticate_inputs(sources: Mapping[str, dict], *, root: Path = ROOT) -> str:
    """Freshly read every used frozen byte; do not re-run historical proofs."""
    records = []
    for item in SNAPSHOTS:
        actual = source_manifest(item, root=root)
        if actual != sources[item.directory]:
            raise publication.PublicationError("historical manifest changed during publication")
        pins = {row["path"]: row for row in actual["files"]}
        for name, pin in pins.items():
            source_file(item, pins, name, root=root)
            records.append({"path": item.directory + "/" + name, **{key: pin[key] for key in ("bytes", "sha256")}})
        records.append({"path": item.directory + "/manifest.json", "bytes": item.manifest_bytes, "sha256": item.manifest_sha256})
    for slug, (relative, size, sha) in LANDINGS.items():
        publication.read_pinned(root / relative, size, sha)
        records.append({"path": relative, "bytes": size, "sha256": sha})
    return publication.digest(canonical_bytes(records))


_CURRENT_FIELDS = {
    "alpha_edition_version", "alpha_edition_checked_use_count", "alpha_edition_identity_sha256",
    "alpha_catalog_sha256", "catalog_sha256", "edition_identity_sha256", "navigation_revision", "html_revision",
}
_MATHEMATICAL_FIELDS = (
    "statement", "statement_sha256", "explicit_statement", "explicit_statement_sha256", "script", "lines",
    "dependencies", "dependents", "summary", "defined", "sources", "source", "script_sha256",
    "proof_edition_version", "source_edition_version", "alpha_first_enrolled_version", "alpha_admission_version",
)


def _current_metadata(context) -> dict:
    return {
        "alpha_edition_version": "v31", "alpha_edition_checked_use_count": 3796,
        "alpha_edition_identity_sha256": context.catalog["edition_identity_sha256"],
        "alpha_catalog_sha256": context.catalog_sha256, "catalog_sha256": context.catalog_sha256,
        "edition_identity_sha256": context.catalog["edition_identity_sha256"],
        "navigation_revision": context.revision, "html_revision": context.revision,
    }


def _current_text(text: str) -> str:
    # These are current authority phrases, never a generic version replacement.
    # In particular the two frozen GT summaries about Alpha-v21 executions and
    # all first-admission/proof-edition descriptions remain literal.
    text = re.sub(r"\bAlpha v(?:25|30)(?= (?:checked-use|independently verified))", "Alpha v31", text)
    return text.replace("among 3222 checked release theorems", "among 3796 checked release theorems")


def _refresh_document(original: dict, by_name: Mapping[str, dict], current: Mapping[str, object]) -> dict:
    """Pure metadata projection: source syntax and historical flags are fixed."""
    if type(original) is not dict:
        raise publication.PublicationError("historical API must be a JSON object")
    result = deepcopy(original)
    for key in _CURRENT_FIELDS & result.keys():
        result[key] = current[key]
    for field in ("candidate_status",):
        if type(result.get(field)) is str:
            result[field] = _current_text(result[field])
    for key in ("nodes", "theorems"):
        if key not in result:
            continue
        if type(result[key]) is not list:
            raise publication.PublicationError("historical API node list changed type")
        for old, node in zip(original[key], result[key], strict=True):
            if node.get("kind") == "definition":
                continue
            name = node.get("name")
            if type(name) is not str:
                raise publication.PublicationError("historical API theorem name changed")
            row = by_name.get(name)
            claimed = node.get("alpha_checked_use") is True or node.get("checked_use") is True
            if claimed:
                if (row is None or row.get("checked_use") is not True or row.get("body_checked") is not True):
                    raise publication.PublicationError("an old checked-use claim has no exact current theorem")
                for statement, digest_field in (("statement", "statement_sha256"), ("explicit_statement", "explicit_statement_sha256")):
                    if statement in node and (node[statement] != row["statement"]
                            or node.get(digest_field) != row["statement_sha256"]):
                        raise publication.PublicationError("a historical checked theorem changed its exact statement")
                stable = node.get("stable_member", node.get("admitted_to_stable"))
                if stable is not None and stable is not (row.get("membership") == "stable"):
                    raise publication.PublicationError("historical Stable membership changed")
            # False or absent authority remains false or absent, even if a
            # similarly named theorem exists in the current catalogue.
            for field in _CURRENT_FIELDS & node.keys():
                node[field] = current[field]
            for field in ("status", "status_label"):
                if type(node.get(field)) is str:
                    node[field] = _current_text(node[field])
            for field in (*_MATHEMATICAL_FIELDS, *_AUTHORITY_FIELDS):
                if old.get(field) != node.get(field) or (field in old) != (field in node):
                    raise publication.PublicationError("publication changed historical syntax or authority")
    return result


def _refresh_graph_schema(original: dict) -> dict:
    result = deepcopy(original)
    changed = 0
    def visit(value):
        nonlocal changed
        if type(value) is dict:
            properties = value.get("properties")
            if type(properties) is dict and "alpha_edition_version" in properties:
                field = properties["alpha_edition_version"]
                if field.get("const") == "v25":
                    field["const"] = "v31"
                    changed += 1
            for item in value.values():
                visit(item)
        elif type(value) is list:
            for item in value:
                visit(item)
    visit(result)
    if not changed:
        raise publication.PublicationError("historical graph schema has no reviewed current-edition constraint")
    return result


def _navigation_href(value: str, revision: str) -> str:
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or not parsed.path or parsed.path.endswith((".css", ".js", ".png", ".svg", ".jpg", ".woff2")):
        return value
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    pairs = [(key, item) for key, item in pairs if key != "v"]
    pairs.append(("v", revision))
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(pairs), parsed.fragment))


class _HistoricalHTML(HTMLParser):
    """Only HTML navigation/current metadata and typed graph data are revised."""

    VOID = frozenset(("area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"))
    GRAPH_IDS = {"pa-defined-graph-data": "PA_DEFINED_GRAPH", "pa-proof-graph-data": "PA_PROOF_GRAPH"}
    RELEASE_IDS = frozenset(("pa-proof-release-evidence", "pa-defined-release-evidence",
                             "pa-bertrand-release-evidence", "pa-bertrand-defined-release-evidence"))

    def __init__(self, page: str, revision: str, *, graph: dict | None, portable_script: str,
                 protected_summaries: frozenset[str] = frozenset()):
        super().__init__(convert_charrefs=False)
        self.page, self.revision, self.graph, self.portable_script = page, revision, graph, portable_script
        self.protected_summaries = protected_summaries
        self.stack, self.parts = [], []
        self.script_id = None
        self.script_parts = []
        self.heads = self.bodies = self.graphs = 0
        self.canonical = False

    def handle_starttag(self, tag, attributes):
        values = dict(attributes)
        if len(values) != len(attributes):
            raise publication.PublicationError("duplicate historical HTML attribute")
        raw = self.get_starttag_text()
        changed = False
        if tag == "a" and "href" in values:
            revised = _navigation_href(values["href"], self.revision)
            changed = revised != values["href"]
            values["href"] = revised
        if tag == "link" and values.get("rel") == "canonical":
            old = urlsplit(values.get("href", ""))
            if old.scheme or old.netloc:
                if old.scheme != "https" or old.netloc != "bnaskrecki.faculty.wmi.amu.edu.pl" or not old.path.startswith("/proofs/"):
                    raise publication.PublicationError("foreign historical canonical route")
                canonical = urlunsplit((old.scheme, old.netloc, old.path, "", ""))
            else:
                target = posixpath.normpath(posixpath.join(posixpath.dirname(self.page), unquote(old.path)))
                if not publication.safe_relative(target):
                    raise publication.PublicationError("historical canonical route escapes its reader")
                canonical = "https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/" + target.removesuffix("index.html")
            values["href"] = canonical
            self.canonical, changed = True, True
        if tag == "meta" and values.get("property") == "og:url":
            values["content"] = "https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/" + self.page.removesuffix("index.html")
            changed = True
        if changed:
            raw = "<" + tag + "".join(" " + key + ("" if value is None else '="' + escape(value, quote=True) + '"') for key, value in values.items()) + ">"
        self.parts.append(raw)
        if tag == "main":
            slug = self.page.split("/", 1)[0]
            detail = posixpath.relpath(slug + "/api/first-admission.json", posixpath.dirname(self.page) or ".")
            first_link = (' <a href="' + escape(_navigation_href(detail, self.revision), quote=True)
                          + '">Exact original first-admission records</a>.') if slug in FAMILY_ORDER else ""
            self.parts.append('<p class="pa-callout pd-callout" data-current-release="v31">Current library: Alpha v31, 3,796 checked-use theorems; Stable remains 432. Historical first admissions, original proof editions, and non-admitted aliases are preserved.' + first_link + '</p>')
        if tag == "script":
            self.script_id = values.get("id")
            self.script_parts = []
        if tag not in self.VOID:
            self.stack.append((tag, values))

    def handle_startendtag(self, tag, attributes):
        if tag not in self.VOID:
            raise publication.PublicationError("unexpected historical self-closing element")
        self.handle_starttag(tag, attributes)

    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1][0] != tag:
            raise publication.PublicationError("unbalanced historical HTML: " + tag)
        self.stack.pop()
        if tag == "script":
            data = "".join(self.script_parts)
            if self.script_id in self.GRAPH_IDS:
                variable = self.GRAPH_IDS[self.script_id]
                match = re.fullmatch(r"\s*window\." + variable + r"\s*=\s*(\{.*\});\s*", data, re.S)
                if match is None or self.graph is None:
                    raise publication.PublicationError("historical inline graph has no exact typed API peer")
                publication.strict_json(match[1])
                data = "window." + variable + "=" + canonical_bytes(self.graph).decode("utf-8").replace("<", "\\u003c") + ";"
                self.graphs += 1
            elif self.script_id in self.RELEASE_IDS:
                # Only the frozen release-label adapter, never proof scripts
                # or arbitrary JavaScript strings, receives current prose.
                data = _current_text(data)
            self.parts.append(data)
            self.script_id, self.script_parts = None, []
        if tag == "head":
            if not self.canonical:
                self.parts.append('<link rel="canonical" href="https://bnaskrecki.faculty.wmi.amu.edu.pl/proofs/' + escape(self.page.removesuffix("index.html"), quote=True) + '">')
            self.parts.append('<meta name="proof-publication-scope" content="alpha-v31-historical-first-admission-preserved">')
            self.heads += 1
        if tag == "body":
            self.parts.append(self.portable_script)
            self.bodies += 1
        self.parts.append("</" + tag + ">")

    def handle_data(self, data):
        if self.stack and self.stack[-1][0] == "script":
            self.script_parts.append(data)
        elif any(tag in {"pre", "code", "style"} for tag, _ in self.stack) or data.strip() in self.protected_summaries:
            self.parts.append(data)
        else:
            self.parts.append(_current_text(data))

    def handle_entityref(self, name):
        self.parts.append("&" + name + ";")

    def handle_charref(self, name):
        self.parts.append("&#" + name + ";")

    def handle_comment(self, data):
        self.parts.append("<!--" + data + "-->")

    def handle_decl(self, decl):
        self.parts.append("<!" + decl + ">")

    def finish(self, payload: bytes) -> bytes:
        self.feed(payload.decode("utf-8"))
        self.close()
        if (self.stack or self.heads != 1 or self.bodies != 1
                or (self.graph is not None and self.graphs != 1)):
            raise publication.PublicationError("historical reader lost its exact HTML/graph structure")
        return "".join(self.parts).encode("utf-8")


def _manifest_family(row: dict) -> dict:
    return {key: row[key] for key in ("slug", "title", "theorem_count", "checked_use_count", "stable_count",
                                      "first_admission", "first_admission_sha256")}


def iter_files_from_live(context: LiveReleaseContext) -> Iterator[tuple[str, bytes]]:
    """Stream the large old44 projection after genuine same-live verification."""
    publication.require_live(context)
    sources = manifests()
    original_binding = authenticate_inputs(sources)
    metadata = family_metadata()
    by_slug = {row["slug"]: row for row in metadata}
    by_name = {row["name"]: row for row in context.catalog["theorems"]}
    current = _current_metadata(context)
    from build_constructive_completed_lower_explorer_v31 import _portable_script
    packages = {**{slug: publication.HISTORICAL_OUTPUT_NAME for slug in FAMILY_ORDER},
                **{slug: publication.OUTPUT_NAME for slug in publication.FAMILY_ORDER}}
    portable = _portable_script(packages)
    output_pins = {}

    def output(name, payload):
        pin = {"bytes": len(payload), "sha256": publication.digest(payload)}
        if name in output_pins:
            if output_pins[name] != pin:
                raise publication.PublicationError("historical packages disagree on a shared output")
            return None
        output_pins[name] = pin
        return name, payload

    for item in SNAPSHOTS:
        manifest = sources[item.directory]
        pins = {row["path"]: row for row in manifest["files"]}
        if not item.flagship:
            for name in pins:
                if name.startswith("assets/"):
                    entry = output(name, source_file(item, pins, name))
                    if entry is not None:
                        yield entry
        for slug in item.slugs:
            prefix = "" if item.flagship else slug + "/"
            destination = slug + "/explorer/" + ("defined/" if item.defined else "") if item.flagship else ""
            selected = [name for name in pins if item.flagship or name.startswith(prefix)]
            corpus_name = "api/corpus.json" if item.defined else _corpus_path(item, slug)
            original = publication.strict_json(source_file(item, pins, corpus_name))
            summaries = frozenset(row["summary"] for row in _nodes(original) if type(row.get("summary")) is str)
            graph_name = "api/graph.json" if item.flagship else slug + "/explorer/defined/api/graph.json"
            graph = _refresh_document(publication.strict_json(source_file(item, pins, graph_name)), by_name, current)
            for name in selected:
                payload = source_file(item, pins, name)
                new_name = destination + name
                if name.endswith(".json") and Path(name).name in {"corpus.json", "current-corpus.json", "graph.json"}:
                    revised = graph if name == graph_name else _refresh_document(publication.strict_json(payload), by_name, current)
                    payload = publication.json_bytes(revised)
                elif name.endswith("api/graph.schema.json"):
                    payload = publication.json_bytes(_refresh_graph_schema(publication.strict_json(payload)))
                elif name.endswith(".html"):
                    payload = _HistoricalHTML(new_name, context.revision,
                        graph=graph if name == graph_name.removesuffix("api/graph.json") + "graph.html" else None,
                        portable_script=portable, protected_summaries=summaries).finish(payload)
                entry = output(new_name, payload)
                if entry is not None:
                    yield entry
            if not item.defined:
                tags = by_slug[slug]["tags"]
                records = first_admission_records(item, slug, manifest, original, tags)
                raw = publication.json_bytes(records)
                descriptor = by_slug[slug]["first_admission"]
                if {"bytes": len(raw), "sha256": publication.digest(raw)} != {
                        key: descriptor["per_theorem_records"][key] for key in ("bytes", "sha256")}:
                    raise publication.PublicationError("the exact first-admission sidecar changed")
                yield output(descriptor["per_theorem_records"]["path"], raw)
                # A consistent sibling API for both flagships and later readers.
                if item.flagship:
                    yield output(slug + "/api/corpus.json", publication.json_bytes(_refresh_document(original, by_name, current)))
                if not item.flagship:
                    yield output(slug + "/api/graph.json", publication.json_bytes(graph))
            elif item.flagship:
                yield output(slug + "/api/graph.json", publication.json_bytes(graph))
        raw_manifest = publication.read_pinned(_directory(item) / "manifest.json", item.manifest_bytes, item.manifest_sha256)
        yield output("historical/" + item.directory + "/manifest.json", raw_manifest)
    for slug, (relative, size, sha) in LANDINGS.items():
        payload = publication.read_pinned(ROOT / relative, size, sha)
        yield output(slug + "/index.html", _HistoricalHTML(slug + "/index.html", context.revision,
                     graph=None, portable_script=portable).finish(payload))
    cards = "".join('<article class="family-card"><h2>' + escape(row["title"]) + '</h2><p>'
        + str(row["checked_use_count"]) + ' checked-use entries in ' + str(row["theorem_count"])
        + ' visible theorem records; original first-admission and aliases preserved.</p><a href="'
        + escape(_navigation_href(row["slug"] + "/", context.revision), quote=True) + '">Explore the proof map</a></article>' for row in metadata)
    index = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Historical proof families — current Alpha v31</title><link rel="stylesheet" href="assets/proofs.css"></head>'
        '<body><header class="hero"><div class="shell"><h1>Forty-four established proof families</h1>'
        '<p class="lede">Current Alpha: 3,796 checked-use theorems. Stable: 432 unchanged. These historical readers retain their original first admissions and exact mathematics.</p></div></header>'
        '<main class="shell"><section class="family-grid">' + cards + '</section></main></body></html>').encode("utf-8")
    yield output("index.html", _HistoricalHTML("index.html", context.revision, graph=None, portable_script=portable).finish(index))
    manifest = {
        "schema": SCHEMA, "alpha_edition_version": "v31", "alpha_first_enrolled_version": "mixed_preserved",
        "catalog_sha256": context.catalog_sha256, "edition_identity_sha256": context.catalog["edition_identity_sha256"],
        "html_revision": context.revision, "theorem_count": sum(row["theorem_count"] for row in metadata),
        "checked_use_count": sum(row["checked_use_count"] for row in metadata),
        "stable_count": sum(row["stable_count"] for row in metadata),
        "alpha_edition_checked_use_count": 3796, "stable_edition_count": 432,
        "display_count_policy": "Per-reader node counts may repeat the same theorem across families; they are not edition membership totals.",
        "families": [_manifest_family(row) for row in metadata],
        "historical_input_binding_sha256": original_binding,
        "release_source_binding_sha256": context.source_binding_sha256,
        "file_count_excluding_manifest": len(output_pins), "files": output_pins,
    }
    raw = canonical_bytes(manifest) + b"\n"
    if len(raw) > 2 * 1024 * 1024:
        raise publication.PublicationError("historical manifest exceeds the unchanged 2 MiB public limit")
    publication.require_live(context)
    if authenticate_inputs(sources) != original_binding:
        raise publication.PublicationError("a frozen historical reader changed during publication")
    yield "manifest.json", raw


def build_files_from_live(context: LiveReleaseContext) -> dict[str, bytes]:
    """Convenience API; the bounded public process uses the streaming form."""
    return dict(iter_files_from_live(context))
