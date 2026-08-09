"""Deterministic, selected-only HTML pages for the candidate PA library.

This module is a presentation builder.  Its only theorem input is the exact
retained five-file selected documentation bundle.  The generated pages are
display-only: they grant no kernel, review, freeze, training, retrieval, or
evaluation authority.
"""

from __future__ import annotations

from hashlib import sha256
import html
import importlib
import json
import os
from pathlib import Path
import re
import stat
from typing import Iterable

class LibraryPageDeploymentError(ValueError):
    """Raised when a selected page deployment violates its closed contract."""


SCHEMA_FORMAT = "peano-hydra-library-page-deployment-schema"
SCHEMA_ID = "urn:peano-hydra:library-page-deployment-schema:v1"
SCHEMA_VERSION = 1
SCHEMA_SEMANTIC_SHA256 = (
    "eefb4b1154581f248696de3f81bd90296398e5353c6a42d0d01f35b3ccdb2abb"
)

API_FORMAT = "peano-hydra-library-page-deployment-api"
API_ID = "urn:peano-hydra:library-page-deployment-api:candidate-v1"
MANIFEST_FORMAT = "peano-hydra-library-page-deployment-manifest"
MANIFEST_ID = "urn:peano-hydra:library-page-deployment-manifest:candidate-v1"
READINESS_FORMAT = "peano-hydra-library-page-deployment-readiness"
READINESS_ID = "urn:peano-hydra:library-page-deployment-readiness:candidate-v1"

STATUS = "candidate"
LOGIC_MODE = "intuitionistic"
THEOREM_COUNT = 384
DECLARED_DEPENDENCY_EDGES = 1_038
TACTIC_LINE_COUNT = 13_862
DEFINITION_COUNT = 40
DEFINITION_OCCURRENCES = 2_027
DEFINITION_USE_RELATIONSHIPS = 755
DEFINITION_CONCEPTUAL_EDGES = 58
EXPLICIT_PAGE_COUNT = 384
DEFINED_PAGE_COUNT = 384
DEFINITION_PAGE_COUNT = 40
INDEX_PAGE_COUNT = 1
HTML_PAGE_COUNT = 809
CONTENT_FILE_COUNT = 812
TREE_FILE_COUNT = 813

SCHEMA_FILE = "schema.json"
API_FILE = "api/deployment.json"
CSS_FILE = "assets/pages.css"
INDEX_FILE = "index.html"
MANIFEST_FILE = "manifest.json"

MAX_SCHEMA_BYTES = 131_072
MAX_JSON_BYTES = 8_388_608
MAX_FILE_BYTES = 4_194_304
MAX_TREE_BYTES = 67_108_864
MAX_JSON_DEPTH = 64
MAX_JSON_ITEMS = 3_000_000
MAX_SAFE_JSON_INTEGER = 9_007_199_254_740_991
MAX_BUNDLE_MEMBER_BYTES = 16_777_216

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
_SCHEMA_PATH = Path("training/peano_hydra/library-page-deployment-schema-v1.json")
_BUNDLE_DIRECTORY = Path("artifacts/peano-hydra/l0-documentation-candidate-v1")

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_THEOREM_NAME_RE = re.compile(r"[a-z][a-z0-9_]{0,127}")
_DEFINITION_ID_RE = re.compile(r"PD[0-9A-Y]{4}")

_BUNDLE_PINS = {
    "schema.json": (
        "a442e89ac312302dcee777b5741ca7f2d67e10f6ebcc996b8096fc6061c28a9c",
        None,
    ),
    "explicit.json": (
        "f1c9f364db0cb7ae7f4c7fe065b1ef48d5522fc49711667479ec3dc4db723936",
        "b7942fa5a866ff7cd8a38f30c93787ec0abd2948e69710651e4d3578e64377da",
    ),
    "defined.json": (
        "164b34dd0cad555baf2164ee3da114fb60a447bd667112481e7225097dd17cea",
        "897fd5e4bedb44b63853e428ff5bc2e2c273e30a0c239450e0ec8f93d73fc61f",
    ),
    "isolation-receipt.json": (
        "8c8a6882d0d5a82552942fc0c3efe5a900244a9cad02c32b24cabe3d86a0eee6",
        "64bdc2c52bcaf88d26382bbe514be4a442cc876b8df2a353c272587e1516d919",
    ),
    "manifest.json": (
        "5ded97c27b859cc4725362bc76aba89fac06c5f11843b50529b78050b19348bf",
        "8f7ef8fcca69bc6f5f8b39c220293b8414a65fd81576c584f78e59da104d46a4",
    ),
}
_BUNDLE_SCHEMA_SEMANTIC_SHA256 = (
    "30236aaaecc41104e7e193476f59a8b764d56fe86c63ca04c1561ad38645832d"
)

_CSS = b"""body.pa-selected-library { margin: 0; color: #172238; background: #f5f7fb; font: 16px/1.55 system-ui, sans-serif; }
body.pa-selected-library * { box-sizing: border-box; }
body.pa-selected-library a { color: #174ea6; }
body.pa-selected-library header { padding: 2rem max(1.25rem, calc((100vw - 76rem) / 2)); color: white; background: #183153; }
body.pa-selected-library header a { color: #d9e8ff; }
body.pa-selected-library main { width: min(76rem, calc(100% - 2rem)); margin: 1.5rem auto 3rem; }
body.pa-selected-library section, body.pa-selected-library aside { padding: 1rem 1.2rem; margin: 1rem 0; border: 1px solid #d8dfeb; border-radius: .55rem; background: white; }
body.pa-selected-library .pl-grid { display: grid; gap: .8rem; grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr)); }
body.pa-selected-library .pl-card { padding: .8rem; border: 1px solid #d8dfeb; border-radius: .4rem; }
body.pa-selected-library .pl-proof { padding-left: 3.5rem; }
body.pa-selected-library .pl-proof li { padding: .25rem .5rem; border-bottom: 1px solid #edf0f5; }
body.pa-selected-library code, body.pa-selected-library pre { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
body.pa-selected-library pre { overflow-x: auto; padding: .8rem; background: #f3f5f8; }
body.pa-selected-library .pl-candidate { display: inline-block; padding: .2rem .5rem; border-radius: 999px; color: #623d00; background: #ffecb5; font-weight: 700; }
body.pa-selected-library .pl-receipt { overflow-wrap: anywhere; }
body.pa-selected-library .pl-definition { color: #6b2f90; font-weight: 650; }
body.pa-selected-library nav { display: flex; flex-wrap: wrap; gap: 1rem; }
body.pa-selected-library dl { display: grid; grid-template-columns: max-content 1fr; gap: .35rem .8rem; }
body.pa-selected-library dt { font-weight: 700; }
@media (max-width: 42rem) { body.pa-selected-library dl { grid-template-columns: 1fr; } }
"""


def _sha256_bytes(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _compact_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise LibraryPageDeploymentError(f"value is not strict JSON: {exc}") from None


def _sha256_json(value: object) -> str:
    return _sha256_bytes(_compact_json_bytes(value))


def _validate_json(
    value: object,
    *,
    depth: int = 0,
    active: set[int] | None = None,
    counter: list[int] | None = None,
) -> None:
    if depth > MAX_JSON_DEPTH:
        raise LibraryPageDeploymentError("JSON exceeds the depth limit")
    if active is None:
        active = set()
    if counter is None:
        counter = [0]
    counter[0] += 1
    if counter[0] > MAX_JSON_ITEMS:
        raise LibraryPageDeploymentError("JSON exceeds the item limit")
    if value is None or type(value) in {bool, str}:
        return
    if type(value) is int:
        if abs(value) > MAX_SAFE_JSON_INTEGER:
            raise LibraryPageDeploymentError(
                "JSON integer exceeds the safe domain"
            )
        return
    if type(value) not in {list, dict}:
        raise LibraryPageDeploymentError(
            f"unsupported JSON value type: {type(value).__name__}"
        )
    identity = id(value)
    if identity in active:
        raise LibraryPageDeploymentError("cyclic JSON value is forbidden")
    active.add(identity)
    try:
        if type(value) is dict:
            if not all(type(key) is str for key in value):
                raise LibraryPageDeploymentError("JSON object keys must be strings")
            values = value.values()
        else:
            values = value
        for item in values:
            _validate_json(
                item,
                depth=depth + 1,
                active=active,
                counter=counter,
            )
    finally:
        active.remove(identity)


def canonical_document_bytes(value: object, *, limit: int = MAX_JSON_BYTES) -> bytes:
    """Return the unique retained JSON representation used by this protocol."""

    if type(limit) is not int or limit < 1:
        raise TypeError("canonical JSON limit must be a positive exact integer")
    _validate_json(value)
    try:
        raw = (
            json.dumps(
                value,
                allow_nan=False,
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError, RecursionError) as exc:
        raise LibraryPageDeploymentError(
            f"value is not canonical JSON: {exc}"
        ) from None
    if len(raw) > limit:
        raise LibraryPageDeploymentError(
            f"canonical JSON exceeds the {limit}-byte limit"
        )
    return raw


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise LibraryPageDeploymentError(f"duplicate JSON key {key!r}")
        result[key] = value
    return result


def _reject_float(_: str) -> object:
    raise LibraryPageDeploymentError("floating-point JSON values are forbidden")


def _reject_constant(_: str) -> object:
    raise LibraryPageDeploymentError("non-finite JSON values are forbidden")


def _decode_json(raw: bytes, label: str) -> object:
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
            parse_float=_reject_float,
        )
    except LibraryPageDeploymentError:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as exc:
        raise LibraryPageDeploymentError(f"{label} is not strict JSON: {exc}") from None
    _validate_json(value)
    return value


def _read_bounded_regular_file(path: Path, *, label: str, limit: int) -> bytes:
    if type(limit) is not int or limit < 1:
        raise TypeError("file limit must be a positive exact integer")
    flags = (
        os.O_RDONLY
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NONBLOCK", 0)
    )
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LibraryPageDeploymentError(f"cannot open {label}") from exc
    try:
        before = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_size < 1
            or before.st_size > limit
        ):
            raise LibraryPageDeploymentError(f"{label} is not a bounded regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            raw = stream.read(limit + 1)
        after = os.fstat(descriptor)
        if (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        ) != (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        ):
            raise LibraryPageDeploymentError(f"{label} changed while read")
    except OSError as exc:
        raise LibraryPageDeploymentError(f"cannot read {label}") from exc
    finally:
        os.close(descriptor)
    if len(raw) != before.st_size:
        raise LibraryPageDeploymentError(f"{label} changed size while read")
    return raw


def _repository_root(value: Path | None) -> Path:
    root = _REPOSITORY_ROOT if value is None else value
    if not isinstance(root, Path):
        raise TypeError("repository root must be a pathlib.Path")
    lexical = Path(os.path.abspath(root))
    try:
        observed = lexical.lstat()
        if not stat.S_ISDIR(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
            raise LibraryPageDeploymentError(
                "repository root must be a non-symlink directory"
            )
        resolved = lexical.resolve(strict=True)
    except OSError as exc:
        raise LibraryPageDeploymentError("cannot resolve repository root") from exc
    if resolved != lexical:
        raise LibraryPageDeploymentError(
            "repository root must not contain symlink components"
        )
    return resolved


def _fixed_file(root: Path, relative: Path, *, limit: int) -> bytes:
    current = root
    for component in relative.parts[:-1]:
        current = current / component
        try:
            observed = current.lstat()
        except OSError as exc:
            raise LibraryPageDeploymentError("fixed input path is unavailable") from exc
        if not stat.S_ISDIR(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
            raise LibraryPageDeploymentError("fixed input path contains a symlink")
    return _read_bounded_regular_file(
        root / relative, label=relative.as_posix(), limit=limit
    )


def _schema_from_root(root: Path) -> dict[str, object]:
    raw = _fixed_file(root, _SCHEMA_PATH, limit=MAX_SCHEMA_BYTES)
    value = _decode_json(raw, "page-deployment schema")
    if type(value) is not dict or canonical_document_bytes(
        value, limit=MAX_SCHEMA_BYTES
    ) != raw:
        raise LibraryPageDeploymentError(
            "page-deployment schema is not one canonical object"
        )
    if (
        value.get("format") != SCHEMA_FORMAT
        or value.get("id") != SCHEMA_ID
        or value.get("v") != SCHEMA_VERSION
    ):
        raise LibraryPageDeploymentError("page-deployment schema identity drifted")
    semantic = value.get("semantic_sha256")
    preimage = {key: item for key, item in value.items() if key != "semantic_sha256"}
    if (
        type(semantic) is not str
        or semantic != SCHEMA_SEMANTIC_SHA256
        or semantic != _sha256_json(preimage)
    ):
        raise LibraryPageDeploymentError("page-deployment schema digest drifted")
    return _decode_json(raw, "detached page-deployment schema")  # type: ignore[return-value]


def _schema_identity_from_root(root: Path) -> dict[str, object]:
    schema = _schema_from_root(root)
    return {
        "artifact_sha256": _sha256_bytes(
            canonical_document_bytes(schema, limit=MAX_SCHEMA_BYTES)
        ),
        "format": SCHEMA_FORMAT,
        "id": SCHEMA_ID,
        "semantic_sha256": SCHEMA_SEMANTIC_SHA256,
        "v": SCHEMA_VERSION,
    }


def library_page_deployment_schema() -> dict[str, object]:
    """Load and verify the binding page-deployment schema."""

    return _schema_from_root(_repository_root(None))


def library_page_deployment_schema_identity() -> dict[str, object]:
    """Return semantic and transport identities of the binding schema."""

    return _schema_identity_from_root(_repository_root(None))


def _require_sha(label: str, value: object) -> str:
    if type(value) is not str or _SHA256_RE.fullmatch(value) is None:
        raise LibraryPageDeploymentError(f"{label} is not one SHA-256 digest")
    return value


def _documentation_bundle_module(root: Path):
    try:
        module = importlib.import_module(
            "training.peano_hydra.library_documentation_bundle"
        )
    except ImportError as exc:
        raise LibraryPageDeploymentError(
            f"cannot import selected documentation validator: {exc}"
        ) from None
    source = getattr(module, "__file__", None)
    if type(source) is not str:
        raise LibraryPageDeploymentError(
            "cannot identify selected documentation validator"
        )
    try:
        expected = (
            root / "training/peano_hydra/library_documentation_bundle.py"
        ).resolve(strict=True)
        actual = Path(source).resolve(strict=True)
    except OSError as exc:
        raise LibraryPageDeploymentError(
            "cannot resolve selected documentation validator"
        ) from exc
    if actual != expected:
        raise LibraryPageDeploymentError(
            "selected documentation validator import origin drifted"
        )
    return module


def _load_selected_bundle(root: Path) -> dict[str, dict[str, object]]:
    directory = root
    for component in _BUNDLE_DIRECTORY.parts:
        directory = directory / component
        try:
            observed = directory.lstat()
        except OSError as exc:
            raise LibraryPageDeploymentError(
                "selected documentation bundle path is unavailable"
            ) from exc
        if not stat.S_ISDIR(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
            raise LibraryPageDeploymentError(
                "selected documentation bundle path contains a symlink"
            )
    module = _documentation_bundle_module(root)
    try:
        loaded = module.load_documentation_bundle(
            directory, repository_root=root
        )
    except Exception as exc:
        raise LibraryPageDeploymentError(
            f"selected documentation bundle is invalid: {exc}"
        ) from None
    if type(loaded) is not dict or set(loaded) != set(_BUNDLE_PINS):
        raise LibraryPageDeploymentError(
            "selected documentation validator returned a malformed bundle"
        )
    documents: dict[str, dict[str, object]] = {}
    for filename, (artifact_pin, root_pin) in _BUNDLE_PINS.items():
        raw = _fixed_file(
            root,
            _BUNDLE_DIRECTORY / filename,
            limit=MAX_BUNDLE_MEMBER_BYTES,
        )
        if _sha256_bytes(raw) != artifact_pin:
            raise LibraryPageDeploymentError(
                f"selected documentation member {filename!r} has drifted"
            )
        document = _decode_json(raw, f"selected documentation member {filename!r}")
        if (
            type(document) is not dict
            or canonical_document_bytes(
                document, limit=MAX_BUNDLE_MEMBER_BYTES
            ) != raw
            or loaded[filename] != document
        ):
            raise LibraryPageDeploymentError(
                f"selected documentation member {filename!r} is not exact"
            )
        if root_pin is not None and document.get("root_sha256") != root_pin:
            raise LibraryPageDeploymentError(
                f"selected documentation root {filename!r} has drifted"
            )
        documents[filename] = document
    manifest_schema = documents["manifest.json"].get("schema")
    if (
        type(manifest_schema) is not dict
        or manifest_schema.get("sha256") != _BUNDLE_SCHEMA_SEMANTIC_SHA256
    ):
        raise LibraryPageDeploymentError("selected documentation schema has drifted")
    return documents


def _source_bundle_identity() -> dict[str, object]:
    return {
        "defined_artifact_sha256": _BUNDLE_PINS["defined.json"][0],
        "defined_root_sha256": _BUNDLE_PINS["defined.json"][1],
        "directory": _BUNDLE_DIRECTORY.as_posix(),
        "explicit_artifact_sha256": _BUNDLE_PINS["explicit.json"][0],
        "explicit_root_sha256": _BUNDLE_PINS["explicit.json"][1],
        "isolation_artifact_sha256": _BUNDLE_PINS["isolation-receipt.json"][0],
        "isolation_root_sha256": _BUNDLE_PINS["isolation-receipt.json"][1],
        "manifest_artifact_sha256": _BUNDLE_PINS["manifest.json"][0],
        "manifest_root_sha256": _BUNDLE_PINS["manifest.json"][1],
        "schema_artifact_sha256": _BUNDLE_PINS["schema.json"][0],
        "schema_semantic_sha256": _BUNDLE_SCHEMA_SEMANTIC_SHA256,
    }


def _candidate_fields() -> dict[str, object]:
    return {
        "deployed": False,
        "evaluation_eligible": False,
        "freeze_ready": False,
        "logic_mode": LOGIC_MODE,
        "retrieval_eligible": False,
        "status": STATUS,
        "training_eligible": False,
    }


def _e(value: object) -> str:
    return html.escape(str(value), quote=True)


def _page(*, title: str, body: str, prefix: str) -> bytes:
    return (
        "<!doctype html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        f"<title>{_e(title)}</title>"
        f'<link rel="stylesheet" href="{prefix}assets/pages.css">'
        '</head><body class="pa-selected-library">'
        f"{body}</body></html>\n"
    ).encode("utf-8")


def _candidate_notice() -> str:
    return (
        '<p><span class="pl-candidate">candidate display only</span> '
        "This reading surface grants no kernel, review, freeze, training, "
        "retrieval, or evaluation authority.</p>"
    )


def _relation(names: Iterable[str], *, directory: str = "") -> str:
    values = list(names)
    if not values:
        return "<p>None.</p>"
    return '<ul>' + ''.join(
        f'<li><a href="{directory}{_e(name)}.html"><code>{_e(name)}</code></a></li>'
        for name in values
    ) + '</ul>'


def _render_command(line: dict[str, object]) -> str:
    text = line["text"]
    references = line["references"]
    if type(text) is not str or type(references) is not list:
        raise LibraryPageDeploymentError("selected command line is malformed")
    cursor = 0
    parts: list[str] = []
    for reference in references:
        if type(reference) is not dict:
            raise LibraryPageDeploymentError("selected command reference is malformed")
        start = reference["start"]
        end = reference["end"]
        if type(start) is not int or type(end) is not int or not (cursor <= start < end <= len(text)):
            raise LibraryPageDeploymentError("selected command reference span is malformed")
        parts.append(_e(text[cursor:start]))
        token = _e(text[start:end])
        if reference["kind"] == "theorem":
            name = reference["name"]
            if type(name) is not str or _THEOREM_NAME_RE.fullmatch(name) is None:
                raise LibraryPageDeploymentError("selected theorem reference is malformed")
            parts.append(f'<a href="{token}.html">{token}</a>')
        else:
            parts.append(f'<span title="primitive PA axiom">{token}</span>')
        cursor = end
    parts.append(_e(text[cursor:]))
    return "".join(parts)


def _render_parts(parts: object) -> str:
    if type(parts) is not list:
        raise LibraryPageDeploymentError("defined text parts are malformed")
    rendered: list[str] = []
    for part in parts:
        if type(part) is not dict or type(part.get("text")) is not str:
            raise LibraryPageDeploymentError("defined text part is malformed")
        if part.get("kind") == "definition":
            definition = part.get("definition")
            if type(definition) is not str or _DEFINITION_ID_RE.fullmatch(definition) is None:
                raise LibraryPageDeploymentError("defined text identifier is malformed")
            rendered.append(
                f'<a class="pl-definition" href="../definition/{definition}.html">'
                f'{_e(part["text"])}</a>'
            )
        elif part.get("kind") == "text":
            rendered.append(_e(part["text"]))
        else:
            raise LibraryPageDeploymentError("defined text part kind is malformed")
    return "".join(rendered)


def _render_index(explicit_rows: list[dict[str, object]]) -> bytes:
    cards = ''.join(
        '<article class="pl-card">'
        f'<h2><code>{_e(row["name"])}</code></h2>'
        f'<p>{_e(row["summary"])}</p>'
        f'<p><a href="explicit/{_e(row["name"])}.html">explicit proof</a> · '
        f'<a href="defined/{_e(row["name"])}.html">defined notation</a></p>'
        '</article>'
        for row in explicit_rows
    )
    body = (
        '<header><p>Peano Hydra selected library</p><h1>384 checked theorem records</h1>'
        '<p>Name-keyed, replay-ordered presentation generated only from the isolated '
        'selected documentation API.</p></header><main>'
        + _candidate_notice()
        + f'<section><h2>Theorems</h2><div class="pl-grid">{cards}</div></section>'
        '</main>'
    )
    return _page(title="Selected PA library", body=body, prefix="")


def _render_explicit(row: dict[str, object]) -> bytes:
    name = row["name"]
    proof = ''.join(
        f'<li id="proof-line-{line["line"]:04d}"><code>{_render_command(line)}</code></li>'
        for line in row["command_lines"]
    )
    source = row["source"]
    body = (
        '<header><nav><a href="../index.html">Selected library</a>'
        f'<a href="../defined/{_e(name)}.html">Defined-notation view</a></nav>'
        f'<h1><code>{_e(name)}</code></h1><p>{_e(row["summary"])}</p></header><main>'
        + _candidate_notice()
        + '<section><h2>Exact selected statement</h2>'
        f'<pre><code>{_e(row["statement_source"])}</code></pre>'
        f'<p>Canonical: <code>{_e(row["statement_canonical"])}</code></p></section>'
        '<section><h2>Direct declared prerequisites</h2>'
        + _relation(row["declared_dependencies"])
        + '</section><section><h2>Readable tactic script</h2>'
        f'<ol class="pl-proof">{proof}</ol></section>'
        '<aside class="pl-receipt"><h2>Selected record receipt</h2><dl>'
        f'<dt>Record SHA-256</dt><dd><code>{_e(row["record_sha256"])}</code></dd>'
        f'<dt>Script SHA-256</dt><dd><code>{_e(row["script_sha256"])}</code></dd>'
        f'<dt>Formula SHA-256</dt><dd><code>{_e(row["formula_sha256"])}</code></dd>'
        f'<dt>Source</dt><dd><code>{_e(source["path"])}:{source["line"]}</code></dd>'
        f'<dt>Source file SHA-256</dt><dd><code>{_e(source["file_sha256"])}</code></dd>'
        '</dl></aside></main>'
    )
    return _page(title=f"{name} — explicit selected proof", body=body, prefix="../")


def _render_defined(
    explicit: dict[str, object], defined: dict[str, object]
) -> bytes:
    name = explicit["name"]
    proof = ''.join(
        f'<li id="proof-line-{line["line"]:04d}"><code>{_render_parts(line["parts"])}</code>'
        + (
            f'<details><summary>Expanded command</summary><pre><code>{_e(line["expanded_command"])}</code></pre></details>'
            if line["defined_command"] != line["expanded_command"]
            else ''
        )
        + '</li>'
        for line in defined["script"]
    )
    uses = defined["definition_uses"]
    use_list = (
        '<ul>'
        + ''.join(
            f'<li><a class="pl-definition" href="../definition/{_e(use["definition"])}.html">'
            f'<code>{_e(use["definition"])}</code> {_e(use["name"])}</a> '
            f'({use["occurrences"]} occurrences)</li>'
            for use in uses
        )
        + '</ul>'
        if uses
        else '<p>None.</p>'
    )
    statement = defined["statement"]
    body = (
        '<header><nav><a href="../index.html">Selected library</a>'
        f'<a href="../explicit/{_e(name)}.html">Explicit proof view</a></nav>'
        f'<h1><code>{_e(name)}</code> with conservative notation</h1>'
        f'<p>{_e(explicit["summary"])}</p></header><main>'
        + _candidate_notice()
        + '<section><h2>Defined-notation statement</h2><pre><code>'
        + _render_parts(statement["parts"])
        + '</code></pre><details><summary>Exact expanded native PA statement</summary>'
        f'<pre><code>{_e(statement["expanded_source"])}</code></pre></details></section>'
        '<section><h2>Conservative definitions used</h2>'
        + use_list
        + '</section><section><h2>Direct declared prerequisites</h2>'
        + _relation(explicit["declared_dependencies"])
        + '</section><section><h2>Definition-aware tactic script</h2>'
        f'<ol class="pl-proof">{proof}</ol></section>'
        '<aside class="pl-receipt"><h2>Selected record receipt</h2><dl>'
        f'<dt>Defined record SHA-256</dt><dd><code>{_e(defined["record_sha256"])}</code></dd>'
        f'<dt>Explicit record SHA-256</dt><dd><code>{_e(defined["explicit_record_sha256"])}</code></dd>'
        '<dt>Exact AST equivalence</dt><dd>true</dd>'
        '</dl></aside></main>'
    )
    return _page(title=f"{name} — selected defined notation", body=body, prefix="../")


def _render_definition(row: dict[str, object]) -> bytes:
    dependencies = _relation(row["conceptual_dependencies"])
    body = (
        '<header><nav><a href="../index.html">Selected library</a></nav>'
        f'<h1><code>{_e(row["id"])}</code> {_e(row["name"])}</h1>'
        '<p>Conservative reading notation</p></header><main>'
        + _candidate_notice()
        + f'<section><h2>Meaning</h2><p>{_e(row["summary"])}</p>'
        f'<p>Parameters: <code>{_e(", ".join(row["parameters"]))}</code></p>'
        f'<pre><code>{_e(row["expansion"])}</code></pre></section>'
        '<section><h2>Conceptual definition prerequisites</h2>'
        + dependencies
        + '</section><aside class="pl-receipt"><h2>Definition receipt</h2><dl>'
        f'<dt>Record SHA-256</dt><dd><code>{_e(row["record_sha256"])}</code></dd>'
        f'<dt>Expansion SHA-256</dt><dd><code>{_e(row["expansion_sha256"])}</code></dd>'
        f'<dt>Registry index</dt><dd>{row["index"]}</dd>'
        '</dl></aside></main>'
    )
    return _page(title=f"{row['id']} {row['name']} — conservative definition", body=body, prefix="../")


def _page_receipt(path: str, raw: bytes) -> dict[str, object]:
    return {"bytes": len(raw), "path": path, "sha256": _sha256_bytes(raw)}


def _validate_emitted_files(
    files: dict[str, bytes], *, expected_count: int
) -> None:
    if len(files) != expected_count:
        raise LibraryPageDeploymentError("selected output file count drifted")
    folded: set[str] = set()
    total = 0
    for path, raw in files.items():
        parts = Path(path).parts
        if (
            type(path) is not str
            or not path
            or len(path) > 256
            or path.startswith("/")
            or "\\" in path
            or "\x00" in path
            or any(part in {"", ".", ".."} for part in parts)
            or Path(path).as_posix() != path
        ):
            raise LibraryPageDeploymentError("selected output path is unsafe")
        casefolded = path.casefold()
        if casefolded in folded:
            raise LibraryPageDeploymentError("selected output path case-collides")
        folded.add(casefolded)
        if type(raw) is not bytes or not raw or len(raw) > MAX_FILE_BYTES:
            raise LibraryPageDeploymentError(
                f"selected output member {path!r} exceeds its bound"
            )
        total += len(raw)
        if total > MAX_TREE_BYTES:
            raise LibraryPageDeploymentError("selected output tree exceeds its bound")


def _record_hash(record: dict[str, object]) -> dict[str, object]:
    result = dict(record)
    result["record_sha256"] = _sha256_json(record)
    return result


def _api_document(
    *,
    explicit_rows: list[dict[str, object]],
    defined_rows: list[dict[str, object]],
    definitions: list[dict[str, object]],
    files: dict[str, bytes],
) -> dict[str, object]:
    theorem_receipts: list[dict[str, object]] = []
    definition_occurrences = 0
    for index, (explicit, defined) in enumerate(zip(explicit_rows, defined_rows, strict=True)):
        if explicit["index"] != index or defined["index"] != index or explicit["name"] != defined["name"]:
            raise LibraryPageDeploymentError("selected theorem order is inconsistent")
        name = explicit["name"]
        if type(name) is not str or _THEOREM_NAME_RE.fullmatch(name) is None:
            raise LibraryPageDeploymentError("selected theorem name is not path-safe")
        uses = defined["definition_uses"]
        definition_occurrences += sum(use["occurrences"] for use in uses)
        theorem_receipts.append(
            _record_hash(
                {
                    "declared_dependencies": explicit["declared_dependencies"],
                    "defined_page": _page_receipt(
                        f"defined/{name}.html", files[f"defined/{name}.html"]
                    ),
                    "defined_record_sha256": _require_sha(
                        f"defined row {name}", defined["record_sha256"]
                    ),
                    "definition_uses": uses,
                    "explicit_page": _page_receipt(
                        f"explicit/{name}.html", files[f"explicit/{name}.html"]
                    ),
                    "explicit_record_sha256": _require_sha(
                        f"explicit row {name}", explicit["record_sha256"]
                    ),
                    "index": index,
                    "name": name,
                }
            )
        )
    definition_receipts: list[dict[str, object]] = []
    for index, definition in enumerate(definitions):
        definition_id = definition["id"]
        if definition["index"] != index or type(definition_id) is not str or _DEFINITION_ID_RE.fullmatch(definition_id) is None:
            raise LibraryPageDeploymentError("selected definition order is inconsistent")
        definition_receipts.append(
            _record_hash(
                {
                    "conceptual_dependencies": definition["conceptual_dependencies"],
                    "id": definition_id,
                    "index": index,
                    "name": definition["name"],
                    "page": _page_receipt(
                        f"definition/{definition_id}.html",
                        files[f"definition/{definition_id}.html"],
                    ),
                    "source_record_sha256": _require_sha(
                        f"definition {definition_id}", definition["record_sha256"]
                    ),
                }
            )
        )
    dependency_edges = sum(
        len(row["declared_dependencies"]) for row in explicit_rows
    )
    tactic_lines = sum(len(row["command_lines"]) for row in explicit_rows)
    if (
        len(theorem_receipts) != THEOREM_COUNT
        or len(definition_receipts) != DEFINITION_COUNT
        or dependency_edges != DECLARED_DEPENDENCY_EDGES
        or tactic_lines != TACTIC_LINE_COUNT
        or definition_occurrences != DEFINITION_OCCURRENCES
    ):
        raise LibraryPageDeploymentError("selected page aggregate drifted")
    aggregate = {
        "declared_dependency_edges": dependency_edges,
        "defined_page_count": DEFINED_PAGE_COUNT,
        "definition_count": len(definition_receipts),
        "definition_conceptual_edges": sum(
            len(row["conceptual_dependencies"]) for row in definitions
        ),
        "definition_occurrences": definition_occurrences,
        "definition_page_count": DEFINITION_PAGE_COUNT,
        "definition_use_relationships": sum(
            len(row["definition_uses"]) for row in defined_rows
        ),
        "explicit_page_count": EXPLICIT_PAGE_COUNT,
        "html_page_count": HTML_PAGE_COUNT,
        "index_page_count": INDEX_PAGE_COUNT,
        "tactic_line_count": tactic_lines,
        "theorem_count": len(theorem_receipts),
    }
    if (
        aggregate["definition_use_relationships"] != DEFINITION_USE_RELATIONSHIPS
        or aggregate["definition_conceptual_edges"] != DEFINITION_CONCEPTUAL_EDGES
    ):
        raise LibraryPageDeploymentError("selected definition graph drifted")
    body: dict[str, object] = {
        "aggregate": aggregate,
        **_candidate_fields(),
        "definitions": definition_receipts,
        "format": API_FORMAT,
        "id": API_ID,
        "source_bundle": _source_bundle_identity(),
        "theorem_count": THEOREM_COUNT,
        "theorems": theorem_receipts,
        "v": 1,
    }
    theorem_root = _sha256_json(
        [[row["index"], row["name"], row["record_sha256"]] for row in theorem_receipts]
    )
    definition_root = _sha256_json(
        [[row["index"], row["id"], row["record_sha256"]] for row in definition_receipts]
    )
    preimage = {
        "aggregate": aggregate,
        "definition_record_root_sha256": definition_root,
        **_candidate_fields(),
        "format": API_FORMAT,
        "id": API_ID,
        "source_bundle_manifest_root_sha256": _BUNDLE_PINS["manifest.json"][1],
        "theorem_record_root_sha256": theorem_root,
        "v": 1,
    }
    body["root_preimage"] = preimage
    body["root_sha256"] = _sha256_json(preimage)
    return body


def _manifest_document(
    *, files: dict[str, bytes], api: dict[str, object], schema_identity: dict[str, object]
) -> dict[str, object]:
    receipts = [
        _page_receipt(path, raw) for path, raw in sorted(files.items())
    ]
    if len(receipts) != CONTENT_FILE_COUNT:
        raise LibraryPageDeploymentError("selected content file count drifted")
    content_bytes = sum(row["bytes"] for row in receipts)
    aggregate = {
        "content_bytes": content_bytes,
        "content_file_count": len(receipts),
        "defined_page_count": DEFINED_PAGE_COUNT,
        "definition_page_count": DEFINITION_PAGE_COUNT,
        "explicit_page_count": EXPLICIT_PAGE_COUNT,
        "html_page_count": HTML_PAGE_COUNT,
        "theorem_count": THEOREM_COUNT,
        "tree_file_count": TREE_FILE_COUNT,
    }
    api_raw = files[API_FILE]
    body: dict[str, object] = {
        "aggregate": aggregate,
        "api": {
            "artifact_sha256": _sha256_bytes(api_raw),
            "path": API_FILE,
            "root_sha256": api["root_sha256"],
        },
        **_candidate_fields(),
        "content_files": receipts,
        "format": MANIFEST_FORMAT,
        "id": MANIFEST_ID,
        "schema": schema_identity,
        "source_bundle": _source_bundle_identity(),
        "v": 1,
    }
    receipt_root = _sha256_json(
        [[row["path"], row["bytes"], row["sha256"]] for row in receipts]
    )
    preimage = {
        "aggregate": aggregate,
        "api_root_sha256": api["root_sha256"],
        **_candidate_fields(),
        "file_receipt_root_sha256": receipt_root,
        "format": MANIFEST_FORMAT,
        "id": MANIFEST_ID,
        "schema_semantic_sha256": SCHEMA_SEMANTIC_SHA256,
        "source_bundle_manifest_root_sha256": _BUNDLE_PINS["manifest.json"][1],
        "v": 1,
    }
    body["root_preimage"] = preimage
    body["root_sha256"] = _sha256_json(preimage)
    return body


def _readiness_document(
    *, api: dict[str, object], api_raw: bytes, manifest: dict[str, object], manifest_raw: bytes,
    schema_identity: dict[str, object]
) -> dict[str, object]:
    aggregate = {
        "selected_generated_defined_page_complete_count": THEOREM_COUNT,
        "selected_generated_defined_page_missing_count": 0,
        "selected_generated_definition_use_receipt_complete_count": THEOREM_COUNT,
        "selected_generated_explicit_page_complete_count": THEOREM_COUNT,
        "selected_generated_explicit_page_missing_count": 0,
        "selected_generated_page_pair_complete_count": THEOREM_COUNT,
        "theorem_count": THEOREM_COUNT,
    }
    api_artifact = _sha256_bytes(api_raw)
    manifest_artifact = _sha256_bytes(manifest_raw)
    body: dict[str, object] = {
        "aggregate": aggregate,
        "api_artifact_sha256": api_artifact,
        "api_root_sha256": api["root_sha256"],
        **_candidate_fields(),
        "deployment_observed": False,
        "format": READINESS_FORMAT,
        "id": READINESS_ID,
        "manifest_artifact_sha256": manifest_artifact,
        "manifest_root_sha256": manifest["root_sha256"],
        "schema": schema_identity,
        "source_bundle_manifest_root_sha256": _BUNDLE_PINS["manifest.json"][1],
        "v": 1,
    }
    preimage = {
        "aggregate": aggregate,
        "api_artifact_sha256": api_artifact,
        "api_root_sha256": api["root_sha256"],
        **_candidate_fields(),
        "deployment_observed": False,
        "format": READINESS_FORMAT,
        "id": READINESS_ID,
        "manifest_artifact_sha256": manifest_artifact,
        "manifest_root_sha256": manifest["root_sha256"],
        "schema_semantic_sha256": SCHEMA_SEMANTIC_SHA256,
        "source_bundle_manifest_root_sha256": _BUNDLE_PINS["manifest.json"][1],
        "v": 1,
    }
    body["root_preimage"] = preimage
    body["root_sha256"] = _sha256_json(preimage)
    return body


def _require_shape(
    schema: dict[str, object], name: str, value: object
) -> dict[str, object]:
    shapes = schema.get("object_shapes")
    shape = shapes.get(name) if type(shapes) is dict else None
    fields = shape.get("fields") if type(shape) is dict else None
    types = shape.get("types") if type(shape) is dict else None
    if (
        type(value) is not dict
        or type(fields) is not list
        or type(types) is not dict
        or len(fields) != len(set(fields))
        or set(fields) != set(types)
        or set(value) != set(fields)
    ):
        raise LibraryPageDeploymentError(
            f"page-deployment object does not match closed shape {name!r}"
        )
    return value


def _validate_api_shapes(
    schema: dict[str, object], api: dict[str, object]
) -> None:
    _require_shape(schema, "api_document", api)
    _require_shape(schema, "api_aggregate", api["aggregate"])
    _require_shape(schema, "api_root_preimage", api["root_preimage"])
    _require_shape(schema, "selected_bundle_identity", api["source_bundle"])
    for row in api["theorems"]:
        _require_shape(schema, "theorem_receipt", row)
        _require_shape(schema, "page_receipt", row["explicit_page"])
        _require_shape(schema, "page_receipt", row["defined_page"])
        for use in row["definition_uses"]:
            _require_shape(schema, "definition_use", use)
    for row in api["definitions"]:
        _require_shape(schema, "definition_receipt", row)
        _require_shape(schema, "page_receipt", row["page"])


def _validate_manifest_shapes(
    schema: dict[str, object], manifest: dict[str, object]
) -> None:
    _require_shape(schema, "manifest_document", manifest)
    _require_shape(schema, "manifest_aggregate", manifest["aggregate"])
    _require_shape(schema, "manifest_api_identity", manifest["api"])
    _require_shape(schema, "manifest_root_preimage", manifest["root_preimage"])
    _require_shape(schema, "schema_identity", manifest["schema"])
    _require_shape(schema, "selected_bundle_identity", manifest["source_bundle"])
    for row in manifest["content_files"]:
        _require_shape(schema, "file_receipt", row)


def _validate_readiness_shapes(
    schema: dict[str, object], report: dict[str, object]
) -> None:
    _require_shape(schema, "readiness_document", report)
    _require_shape(schema, "readiness_aggregate", report["aggregate"])
    _require_shape(schema, "readiness_root_preimage", report["root_preimage"])
    _require_shape(schema, "schema_identity", report["schema"])


def _build_candidate_library_page_deployment(
    *, repository_root: Path | None = None
) -> dict[str, bytes]:
    root = _repository_root(repository_root)
    schema = _schema_from_root(root)
    schema_identity = _schema_identity_from_root(root)
    bundle = _load_selected_bundle(root)
    explicit_rows = bundle["explicit.json"]["theorems"]
    defined_rows = bundle["defined.json"]["theorems"]
    definitions = bundle["defined.json"]["definitions"]
    if not all(type(rows) is list for rows in (explicit_rows, defined_rows, definitions)):
        raise LibraryPageDeploymentError("selected documentation rows are malformed")

    files: dict[str, bytes] = {
        CSS_FILE: _CSS,
        INDEX_FILE: _render_index(explicit_rows),
        SCHEMA_FILE: canonical_document_bytes(schema, limit=MAX_SCHEMA_BYTES),
    }
    for explicit, defined in zip(explicit_rows, defined_rows, strict=True):
        name = explicit["name"]
        files[f"explicit/{name}.html"] = _render_explicit(explicit)
        files[f"defined/{name}.html"] = _render_defined(explicit, defined)
    for definition in definitions:
        definition_id = definition["id"]
        files[f"definition/{definition_id}.html"] = _render_definition(definition)

    api = _api_document(
        explicit_rows=explicit_rows,
        defined_rows=defined_rows,
        definitions=definitions,
        files=files,
    )
    _validate_api_shapes(schema, api)
    api_raw = canonical_document_bytes(api)
    files[API_FILE] = api_raw
    _validate_emitted_files(files, expected_count=CONTENT_FILE_COUNT)
    manifest = _manifest_document(files=files, api=api, schema_identity=schema_identity)
    _validate_manifest_shapes(schema, manifest)
    manifest_raw = canonical_document_bytes(manifest)
    files[MANIFEST_FILE] = manifest_raw
    _validate_emitted_files(files, expected_count=TREE_FILE_COUNT)
    return dict(sorted(files.items()))


def build_candidate_library_page_deployment(
    *, repository_root: Path | None = None
) -> dict[str, bytes]:
    """Build the exact selected candidate page tree in memory."""

    return dict(
        _build_candidate_library_page_deployment(repository_root=repository_root)
    )


def validate_library_page_deployment(
    value: object, *, repository_root: Path | None = None
) -> dict[str, bytes]:
    """Validate a complete tree against exact selected-source reconstruction."""

    if type(value) is not dict:
        raise LibraryPageDeploymentError("page deployment must be one exact file map")
    expected = _build_candidate_library_page_deployment(repository_root=repository_root)
    if set(value) != set(expected):
        raise LibraryPageDeploymentError("page deployment has a missing or extra path")
    supplied: dict[str, bytes] = {}
    total = 0
    for path in expected:
        raw = value[path]
        if type(raw) is not bytes or not raw or len(raw) > MAX_FILE_BYTES:
            raise LibraryPageDeploymentError(f"page deployment member {path!r} is invalid")
        total += len(raw)
        if total > MAX_TREE_BYTES or raw != expected[path]:
            raise LibraryPageDeploymentError(
                f"page deployment member {path!r} differs from exact reconstruction"
            )
        supplied[path] = raw
    return supplied


def _safe_external_directory(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("deployment directory must be a pathlib.Path")
    lexical = Path(os.path.abspath(path))
    try:
        observed = lexical.lstat()
        if not stat.S_ISDIR(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
            raise LibraryPageDeploymentError(
                "deployment path must be a non-symlink directory"
            )
        resolved = lexical.resolve(strict=True)
    except LibraryPageDeploymentError:
        raise
    except OSError as exc:
        raise LibraryPageDeploymentError("cannot resolve deployment directory") from exc
    if resolved != lexical:
        raise LibraryPageDeploymentError(
            "deployment path must not contain symlink components"
        )
    return resolved


def _directory_members(root: Path) -> tuple[set[str], set[str]]:
    files: set[str] = set()
    directories: set[str] = set()
    entry_count = 0

    def visit(directory: Path) -> None:
        nonlocal entry_count
        try:
            with os.scandir(directory) as iterator:
                for entry in iterator:
                    entry_count += 1
                    if entry_count > TREE_FILE_COUNT + 8:
                        raise LibraryPageDeploymentError(
                            "deployment directory exceeds its member bound"
                        )
                    relative = Path(entry.path).relative_to(root).as_posix()
                    if entry.is_symlink():
                        raise LibraryPageDeploymentError(
                            "deployment directory contains a symlink"
                        )
                    if entry.is_dir(follow_symlinks=False):
                        directories.add(relative)
                        visit(Path(entry.path))
                    elif entry.is_file(follow_symlinks=False):
                        files.add(relative)
                    else:
                        raise LibraryPageDeploymentError(
                            "deployment directory contains a nonregular member"
                        )
        except OSError as exc:
            raise LibraryPageDeploymentError("cannot inspect deployment directory") from exc

    visit(root)
    return files, directories


def load_library_page_deployment(
    directory: Path, *, repository_root: Path | None = None
) -> dict[str, bytes]:
    """Load one exact bounded tree with no symlink following."""

    root = _safe_external_directory(directory)
    expected = _build_candidate_library_page_deployment(
        repository_root=repository_root
    )
    expected_files = set(expected)
    expected_directories = {
        parent.as_posix()
        for path in expected_files
        for parent in Path(path).parents
        if parent != Path(".")
    }
    files, directories = _directory_members(root)
    if files != expected_files or directories != expected_directories:
        raise LibraryPageDeploymentError(
            "deployment directory differs from the exact closed layout"
        )
    loaded: dict[str, bytes] = {}
    total = 0
    for relative in sorted(files):
        raw = _read_bounded_regular_file(
            root / relative,
            label=f"deployment member {relative!r}",
            limit=MAX_FILE_BYTES,
        )
        total += len(raw)
        if total > MAX_TREE_BYTES:
            raise LibraryPageDeploymentError("deployment tree exceeds its byte bound")
        loaded[relative] = raw
    return validate_library_page_deployment(
        loaded, repository_root=repository_root
    )


def readiness_report(
    value: object, *, repository_root: Path | None = None
) -> dict[str, object]:
    """Validate a complete tree and return its detached candidate readiness report."""

    validated = validate_library_page_deployment(
        value, repository_root=repository_root
    )
    return _readiness_from_validated(
        validated, repository_root=repository_root
    )


def _readiness_from_validated(
    value: dict[str, bytes], *, repository_root: Path | None = None
) -> dict[str, object]:
    api_value = _decode_json(value[API_FILE], "page-deployment API")
    manifest_value = _decode_json(value[MANIFEST_FILE], "page-deployment manifest")
    if type(api_value) is not dict or type(manifest_value) is not dict:
        raise LibraryPageDeploymentError("page-deployment envelope is malformed")
    report = _readiness_document(
        api=api_value,
        api_raw=value[API_FILE],
        manifest=manifest_value,
        manifest_raw=value[MANIFEST_FILE],
        schema_identity=_schema_identity_from_root(
            _repository_root(repository_root)
        ),
    )
    schema = _schema_from_root(_repository_root(repository_root))
    _validate_readiness_shapes(schema, report)
    return report


def _build_candidate_library_page_deployment_with_readiness(
    *, repository_root: Path | None = None
) -> tuple[dict[str, bytes], dict[str, object]]:
    """Build fixed inputs once and project the non-deployment readiness artifact."""

    built = _build_candidate_library_page_deployment(
        repository_root=repository_root
    )
    return built, _readiness_from_validated(
        built, repository_root=repository_root
    )


__all__ = [
    "LibraryPageDeploymentError",
    "library_page_deployment_schema",
    "library_page_deployment_schema_identity",
    "canonical_document_bytes",
    "build_candidate_library_page_deployment",
    "validate_library_page_deployment",
    "load_library_page_deployment",
    "readiness_report",
]
