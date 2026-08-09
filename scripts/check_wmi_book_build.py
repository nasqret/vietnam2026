#!/usr/bin/env python3
"""Perform a non-executing structural integrity check of a built Jupyter Book.

This gate does not replay Peano or Lambda proofs.  It checks that every TOC
source has a corresponding nonempty HTML page, required Sphinx indexes and
static assets exist, and generated HTML does not contain broken relative
``href`` or ``src`` targets.  The generated PA Proof Explorer is audited as a
static microsite: the explicit and defined editions, all theorem pages, and
all definition pages must be copied byte-for-byte; their local links and
fragments must resolve; and they must not load a remote runtime asset.  The
checker also emits deterministic source and output tree manifests for the
enclosing WMI provenance receipt.
"""

from __future__ import annotations

import argparse
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit


TOC_ENTRY = re.compile(
    r"^\s*(?:-\s*)?(?:root|file):\s*['\"]?([^\s#'\"]+)", re.MULTILINE
)
IGNORED_TREE_PARTS = {"_build", "__pycache__", ".ipynb_checkpoints"}
IGNORED_NAMES = {".DS_Store"}
EXPLORER_RELATIVE = Path("_static/pa-proof-explorer")
EXPLORER_REQUIRED = (
    Path("index.html"),
    Path("graph.html"),
    Path("foundations.html"),
    Path("manifest.json"),
    Path("api/corpus.json"),
    Path("api/graph.json"),
    Path("api/graph.schema.json"),
    Path("assets/explorer.css"),
    Path("assets/explorer.js"),
    Path("defined/index.html"),
    Path("defined/graph.html"),
    Path("defined/manifest.json"),
    Path("defined/api/corpus.json"),
    Path("defined/api/graph.json"),
    Path("defined/api/graph.schema.json"),
    Path("defined/assets/explorer.css"),
    Path("defined/assets/explorer.js"),
)
EXPLORER_TAG_COUNT = 557
DEFINED_EXPLORER_TAG_COUNT = 557
DEFINED_EXPLORER_DEFINITION_COUNT = 40
SELECTED_LIBRARY_RELATIVE = Path("_static/pa-selected-library")
SELECTED_LIBRARY_FILE_COUNT = 813
SELECTED_LIBRARY_HTML_COUNT = 809
SELECTED_LIBRARY_THEOREM_COUNT = 384
SELECTED_LIBRARY_DEFINITION_COUNT = 40
SELECTED_LIBRARY_BODY_SELECTOR = "body.pa-selected-library"
SELECTED_LIBRARY_SCHEMA_SHA256 = (
    "8cdf0e947ce7156109b7591c99ed28d8ee1f938edd3cddfb414d48d7efacdafd"
)
SELECTED_LIBRARY_API_SHA256 = (
    "a7a4be8ba895b9e69955e82bda5bbfe7418eeda47632a59899e6ba0896acaaf0"
)
SELECTED_LIBRARY_API_ROOT_SHA256 = (
    "2efbb00a763f120e5cee6271f3d64838b3a54e04e73a4c78c738f4d50f0b83b1"
)
SELECTED_LIBRARY_MANIFEST_SHA256 = (
    "751c3eefc99e5b30d612049fd99a0d890cd696b3fda0f426ca64d835c5fe2e6f"
)
SELECTED_LIBRARY_MANIFEST_ROOT_SHA256 = (
    "94b38f4914853c87315f0bc94d33347164d4cb7c01cd81568b1c4f47cb1b1563"
)
SELECTED_LIBRARY_REQUIRED = (
    Path("index.html"),
    Path("assets/pages.css"),
    Path("api/deployment.json"),
    Path("schema.json"),
    Path("manifest.json"),
)
REMOTE_ASSET_TAGS = {"audio", "embed", "iframe", "img", "object", "script", "source", "video"}
EXPLORER_BODY_SELECTOR = "body.pa-proof-site"


class _References(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.targets: list[tuple[str, str, str]] = []
        self.anchors: set[str] = set()

    def handle_starttag(self, tag: str, attrs) -> None:
        attributes = dict(attrs)
        anchor = attributes.get("id")
        if anchor:
            self.anchors.add(anchor)
        legacy_anchor = attributes.get("name") if tag == "a" else None
        if legacy_anchor:
            self.anchors.add(legacy_anchor)
        for name in ("href", "src"):
            value = attributes.get(name)
            if value:
                self.targets.append((tag, name, value))


def _tree_manifest(root: Path, *, source: bool) -> dict[str, object]:
    digest = hashlib.sha256()
    count = 0
    total = 0
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if source and (
            any(part in IGNORED_TREE_PARTS for part in relative.parts)
            or relative.name in IGNORED_NAMES
            or relative.suffix in {".pyc", ".pyo"}
        ):
            continue
        payload = path.read_bytes()
        count += 1
        total += len(payload)
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(str(len(payload)).encode("ascii"))
        digest.update(b"\0")
        digest.update(hashlib.sha256(payload).hexdigest().encode("ascii"))
        digest.update(b"\n")
    return {
        "file_count": count,
        "total_bytes": total,
        "tree_manifest_sha256": digest.hexdigest(),
    }


def _toc_sources(book: Path) -> tuple[Path, ...]:
    toc = book / "_toc.yml"
    values = TOC_ENTRY.findall(toc.read_text(encoding="utf-8"))
    if not values:
        raise ValueError("book/_toc.yml contains no root or file entries")
    sources: list[Path] = []
    for value in values:
        relative = Path(value)
        candidates = (relative, relative.with_suffix(".md"), relative.with_suffix(".ipynb"))
        source = next((book / item for item in candidates if (book / item).is_file()), None)
        if source is None:
            raise ValueError(f"TOC source is missing: {value}")
        sources.append(source)
    return tuple(sources)


def _local_target(page: Path, html_root: Path, raw: str) -> tuple[Path | None, bool]:
    """Return a local target and whether its relative path escapes the build."""

    if raw.startswith(("#", "/", "//")):
        return None, False
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc or not parsed.path:
        return None, False
    path_text = unquote(parsed.path)
    if path_text.startswith(("mailto:", "tel:", "data:", "javascript:")):
        return None, False
    target = (page.parent / path_text).resolve()
    try:
        target.relative_to(html_root.resolve())
    except ValueError:
        return target, True
    if target.is_dir():
        target = target / "index.html"
    return target, False


def _json_object(path: Path, errors: list[str], label: str) -> dict[str, object] | None:
    """Read one required explorer JSON object without executing any content."""

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"cannot read {label}: {exc}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} must contain a JSON object")
        return None
    return value


def _matching_css_brace(source: str, opening: int) -> int:
    """Find a CSS block boundary while ignoring quoted braces."""

    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(opening, len(source)):
        character = source[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
            continue
        if character in {'"', "'"}:
            quote = character
        elif character == "{":
            depth += 1
        elif character == "}":
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unclosed CSS block")


def _qualified_css_selectors(source: str) -> tuple[str, ...]:
    """Collect qualified selectors, recursively descending conditional rules."""

    source = re.sub(r"/\*.*?\*/", "", source, flags=re.DOTALL)

    def collect(rule_list: str) -> list[str]:
        selectors: list[str] = []
        cursor = 0
        while cursor < len(rule_list):
            while cursor < len(rule_list) and (
                rule_list[cursor].isspace() or rule_list[cursor] == ";"
            ):
                cursor += 1
            if cursor == len(rule_list):
                break
            opening = rule_list.find("{", cursor)
            if opening < 0:
                if rule_list[cursor:].strip():
                    raise ValueError("CSS rule has no block")
                break
            header = rule_list[cursor:opening].strip()
            closing = _matching_css_brace(rule_list, opening)
            content = rule_list[opening + 1 : closing]
            if header.startswith("@"):
                if header.split(None, 1)[0].lower() not in {
                    "@container",
                    "@layer",
                    "@media",
                    "@scope",
                    "@supports",
                }:
                    raise ValueError(f"unsupported explorer CSS at-rule: {header}")
                selectors.extend(collect(content))
            else:
                selectors.extend(
                    selector.strip()
                    for selector in header.split(",")
                    if selector.strip()
                )
            cursor = closing + 1
        return selectors

    return tuple(collect(source))


def _explorer_javascript_is_body_gated(source: str) -> bool:
    """Require the microsite body guard before any document-wide setup."""

    try:
        ready = source.index("whenReady(function () {")
        guard = source.index(
            f'document.body.classList.contains("{EXPLORER_BODY_SELECTOR.split(".", 1)[1]}")',
            ready,
        )
        first_install = min(
            source.index(token, ready)
            for token in (
                'document.querySelectorAll("[data-proof-dashboard]")',
                'window.addEventListener("hashchange"',
            )
        )
    except ValueError:
        return False
    guarded = re.search(
        r'if \((?:!document\.body \|\| )?'
        r'!document\.body\.classList\.contains\("pa-proof-site"\)\) return;',
        source[ready:first_install],
    )
    return bool(guarded and ready < guard < first_install)


def _check_explorer_copy(book: Path, html_root: Path, errors: list[str]) -> dict[str, object]:
    """Require the complete generated explorer and its exact built copy."""

    source = book / EXPLORER_RELATIVE
    built = html_root / EXPLORER_RELATIVE
    result: dict[str, object] = {
        "built": built.is_dir(),
        "source": source.is_dir(),
        "tag_page_count": 0,
        "defined_tag_page_count": 0,
        "defined_definition_page_count": 0,
    }
    if not source.is_dir():
        errors.append(f"missing PA Proof Explorer source: {EXPLORER_RELATIVE}")
        return result
    if not built.is_dir():
        errors.append(f"missing PA Proof Explorer build output: {EXPLORER_RELATIVE}")

    source_files = {
        path.relative_to(source)
        for path in source.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    built_files = (
        {
            path.relative_to(built)
            for path in built.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        if built.is_dir()
        else set()
    )
    if built.is_dir() and built_files != source_files:
        missing = sorted(item.as_posix() for item in source_files - built_files)
        unexpected = sorted(item.as_posix() for item in built_files - source_files)
        errors.append(
            "built explorer file set differs from source: "
            f"missing={missing[:8]!r}, unexpected={unexpected[:8]!r}"
        )
    if built.is_dir():
        for relative in sorted(source_files, key=lambda item: item.as_posix()):
            source_path = source / relative
            built_path = built / relative
            if built_path.is_file() and source_path.read_bytes() != built_path.read_bytes():
                errors.append(f"built explorer output differs from source: {relative.as_posix()}")

    for relative in EXPLORER_REQUIRED:
        source_path = source / relative
        built_path = built / relative
        if not source_path.is_file() or source_path.stat().st_size == 0:
            errors.append(f"missing or empty explorer source: {relative.as_posix()}")
            continue
        if not built_path.is_file() or built_path.stat().st_size == 0:
            errors.append(f"missing or empty built explorer output: {relative.as_posix()}")
            continue

    for relative in (
        Path("manifest.json"),
        Path("api/corpus.json"),
        Path("api/graph.json"),
        Path("api/graph.schema.json"),
        Path("defined/manifest.json"),
        Path("defined/api/corpus.json"),
        Path("defined/api/graph.json"),
        Path("defined/api/graph.schema.json"),
    ):
        source_path = source / relative
        if source_path.is_file():
            _json_object(source_path, errors, f"explorer {relative.as_posix()}")

    script_path = source / "assets/explorer.js"
    style_path = source / "assets/explorer.css"
    if script_path.is_file():
        script = script_path.read_text(encoding="utf-8", errors="replace")
        for sink in (
            "eval(",
            "innerHTML",
            "insertAdjacentHTML",
            "document.write",
            "new Function",
        ):
            if sink in script:
                errors.append(f"unsafe explorer JavaScript sink: {sink}")
        if not _explorer_javascript_is_body_gated(script):
            errors.append("explorer JavaScript is not gated to body.pa-proof-site")
    else:
        script = ""
    style = (
        style_path.read_text(encoding="utf-8", errors="replace")
        if style_path.is_file()
        else ""
    )
    if "http://" in script + style or "https://" in script + style:
        errors.append("explorer CSS/JavaScript contains a remote URL")
    if re.search(r"(?:url\s*\(\s*['\"]?|@import\s+['\"]?)//", style, re.IGNORECASE):
        errors.append("explorer CSS contains a protocol-relative remote asset")
    if ":root" in style or "--pa-" in style:
        errors.append("explorer CSS contains an unscoped root/custom-property surface")
    if style:
        try:
            selectors = _qualified_css_selectors(style)
        except ValueError as exc:
            errors.append(f"cannot audit explorer CSS isolation: {exc}")
        else:
            unscoped = [
                selector
                for selector in selectors
                if not selector.startswith(EXPLORER_BODY_SELECTOR)
            ]
            if not selectors or unscoped:
                errors.append(
                    "explorer CSS is not isolated below body.pa-proof-site: "
                    f"{unscoped[:8]!r}"
                )

    defined_script_path = source / "defined" / "assets" / "explorer.js"
    defined_style_path = source / "defined" / "assets" / "explorer.css"
    if defined_script_path.is_file():
        defined_script = defined_script_path.read_text(encoding="utf-8", errors="replace")
        for sink in ("eval(", "innerHTML", "insertAdjacentHTML", "document.write", "new Function"):
            if sink in defined_script:
                errors.append(f"unsafe defined-explorer JavaScript sink: {sink}")
        if 'classList.contains("pa-defined-proof-site")' not in defined_script:
            errors.append("defined-explorer JavaScript lacks its body-class guard")
    else:
        defined_script = ""
    defined_style = (
        defined_style_path.read_text(encoding="utf-8", errors="replace")
        if defined_style_path.is_file()
        else ""
    )
    if "http://" in defined_script + defined_style or "https://" in defined_script + defined_style:
        errors.append("defined-explorer CSS/JavaScript contains a remote URL")
    if ":root" in defined_style or "--pa-" in defined_style:
        errors.append("defined-explorer CSS contains an unscoped root/custom-property surface")
    if defined_style:
        try:
            defined_selectors = _qualified_css_selectors(defined_style)
        except ValueError as exc:
            errors.append(f"cannot audit defined-explorer CSS isolation: {exc}")
        else:
            unscoped = [
                selector
                for selector in defined_selectors
                if not selector.startswith("body.pa-defined-proof-site")
            ]
            if not defined_selectors or unscoped:
                errors.append(
                    "defined-explorer CSS is not isolated below "
                    f"body.pa-defined-proof-site: {unscoped[:8]!r}"
                )

    source_tags = tuple(sorted((source / "tag").glob("*.html"), key=lambda item: item.name))
    built_tags = tuple(sorted((built / "tag").glob("*.html"), key=lambda item: item.name))
    result["tag_page_count"] = len(built_tags)
    if len(source_tags) != EXPLORER_TAG_COUNT:
        errors.append(
            f"explorer source has {len(source_tags)} tag pages; expected {EXPLORER_TAG_COUNT}"
        )
    source_names = {path.name for path in source_tags}
    built_names = {path.name for path in built_tags}
    if built_names != source_names:
        missing = sorted(source_names - built_names)
        unexpected = sorted(built_names - source_names)
        errors.append(
            "built explorer tag-page set differs from source: "
            f"missing={missing[:8]!r}, unexpected={unexpected[:8]!r}"
        )
    defined_source_tags = tuple((source / "defined" / "tag").glob("*.html"))
    defined_built_tags = tuple((built / "defined" / "tag").glob("*.html"))
    result["defined_tag_page_count"] = len(defined_built_tags)
    if len(defined_source_tags) != DEFINED_EXPLORER_TAG_COUNT:
        errors.append(
            "defined explorer source has "
            f"{len(defined_source_tags)} tag pages; expected {DEFINED_EXPLORER_TAG_COUNT}"
        )
    if {path.name for path in defined_built_tags} != {
        path.name for path in defined_source_tags
    }:
        errors.append("built defined-explorer tag-page set differs from source")
    defined_source_definitions = tuple(
        (source / "defined" / "definition").glob("*.html")
    )
    defined_built_definitions = tuple(
        (built / "defined" / "definition").glob("*.html")
    )
    result["defined_definition_page_count"] = len(defined_built_definitions)
    if len(defined_source_definitions) != DEFINED_EXPLORER_DEFINITION_COUNT:
        errors.append(
            "defined explorer source has "
            f"{len(defined_source_definitions)} definition pages; expected "
            f"{DEFINED_EXPLORER_DEFINITION_COUNT}"
        )
    if {path.name for path in defined_built_definitions} != {
        path.name for path in defined_source_definitions
    }:
        errors.append("built defined-explorer definition-page set differs from source")
    if source.is_dir():
        result["source_manifest"] = _tree_manifest(source, source=False)
    if built.is_dir():
        result["built_manifest"] = _tree_manifest(built, source=False)
    return result


def _compact_json_sha256(value: object) -> str:
    raw = json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _check_selected_library_copy(
    book: Path, html_root: Path, errors: list[str]
) -> dict[str, object]:
    """Audit the separate tagless 384-theorem candidate page source."""

    source = book / SELECTED_LIBRARY_RELATIVE
    built = html_root / SELECTED_LIBRARY_RELATIVE
    result: dict[str, object] = {
        "built": built.is_dir(),
        "deployed": False,
        "source": source.is_dir(),
        "theorem_count": 0,
        "explicit_page_count": 0,
        "defined_page_count": 0,
        "definition_page_count": 0,
        "html_page_count": 0,
        "tree_file_count": 0,
    }
    if not source.is_dir():
        errors.append(f"missing selected-library source: {SELECTED_LIBRARY_RELATIVE}")
        return result
    if not built.is_dir():
        errors.append(
            f"missing selected-library build output: {SELECTED_LIBRARY_RELATIVE}"
        )

    source_symlinks = tuple(path for path in source.rglob("*") if path.is_symlink())
    built_symlinks = (
        tuple(path for path in built.rglob("*") if path.is_symlink())
        if built.is_dir()
        else ()
    )
    if source_symlinks:
        errors.append("selected-library source contains a symlink")
    if built_symlinks:
        errors.append("selected-library build output contains a symlink")
    source_files = {
        path.relative_to(source)
        for path in source.rglob("*")
        if path.is_file() and not path.is_symlink()
    }
    built_files = (
        {
            path.relative_to(built)
            for path in built.rglob("*")
            if path.is_file() and not path.is_symlink()
        }
        if built.is_dir()
        else set()
    )
    result["tree_file_count"] = len(built_files)
    if len(source_files) != SELECTED_LIBRARY_FILE_COUNT:
        errors.append(
            "selected-library source has "
            f"{len(source_files)} files; expected {SELECTED_LIBRARY_FILE_COUNT}"
        )
    if built.is_dir() and built_files != source_files:
        missing = sorted(item.as_posix() for item in source_files - built_files)
        unexpected = sorted(item.as_posix() for item in built_files - source_files)
        errors.append(
            "built selected-library file set differs from source: "
            f"missing={missing[:8]!r}, unexpected={unexpected[:8]!r}"
        )
    if built.is_dir():
        for relative in sorted(source_files, key=lambda item: item.as_posix()):
            source_path = source / relative
            built_path = built / relative
            if built_path.is_file() and source_path.read_bytes() != built_path.read_bytes():
                errors.append(
                    "built selected-library output differs from source: "
                    f"{relative.as_posix()}"
                )

    for relative in SELECTED_LIBRARY_REQUIRED:
        source_path = source / relative
        built_path = built / relative
        if not source_path.is_file() or source_path.stat().st_size == 0:
            errors.append(
                f"missing or empty selected-library source: {relative.as_posix()}"
            )
        if not built_path.is_file() or built_path.stat().st_size == 0:
            errors.append(
                "missing or empty built selected-library output: "
                f"{relative.as_posix()}"
            )

    pinned_artifacts = {
        Path("schema.json"): SELECTED_LIBRARY_SCHEMA_SHA256,
        Path("api/deployment.json"): SELECTED_LIBRARY_API_SHA256,
        Path("manifest.json"): SELECTED_LIBRARY_MANIFEST_SHA256,
    }
    for relative, expected_sha256 in pinned_artifacts.items():
        path = source / relative
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() != expected_sha256:
            errors.append(
                f"selected-library {relative.as_posix()} artifact identity drifted"
            )

    schema = _json_object(source / "schema.json", errors, "selected-library schema")
    api = _json_object(
        source / "api/deployment.json", errors, "selected-library deployment API"
    )
    manifest = _json_object(
        source / "manifest.json", errors, "selected-library manifest"
    )
    candidate_flags = {
        "deployed": False,
        "evaluation_eligible": False,
        "freeze_ready": False,
        "logic_mode": "intuitionistic",
        "retrieval_eligible": False,
        "status": "candidate",
        "training_eligible": False,
    }
    for label, document in (("API", api), ("manifest", manifest)):
        if document is None:
            continue
        for key, expected in candidate_flags.items():
            if document.get(key) != expected:
                errors.append(
                    f"selected-library {label} has invalid {key}: "
                    f"{document.get(key)!r}"
                )
        preimage = document.get("root_preimage")
        if not isinstance(preimage, dict):
            errors.append(f"selected-library {label} lacks a root preimage")
        elif _compact_json_sha256(preimage) != document.get("root_sha256"):
            errors.append(f"selected-library {label} root preimage does not match")

    if schema is not None:
        if schema.get("semantic_sha256") != (
            "eefb4b1154581f248696de3f81bd90296398e5353c6a42d0d01f35b3ccdb2abb"
        ):
            errors.append("selected-library schema semantic identity drifted")

    expected_api_aggregate = {
        "declared_dependency_edges": 1038,
        "defined_page_count": 384,
        "definition_conceptual_edges": 58,
        "definition_count": 40,
        "definition_occurrences": 2027,
        "definition_page_count": 40,
        "definition_use_relationships": 755,
        "explicit_page_count": 384,
        "html_page_count": 809,
        "index_page_count": 1,
        "tactic_line_count": 13862,
        "theorem_count": 384,
    }
    expected_manifest_aggregate = {
        "content_bytes": 5039241,
        "content_file_count": 812,
        "defined_page_count": 384,
        "definition_page_count": 40,
        "explicit_page_count": 384,
        "html_page_count": 809,
        "theorem_count": 384,
        "tree_file_count": 813,
    }
    if api is not None:
        if api.get("root_sha256") != SELECTED_LIBRARY_API_ROOT_SHA256:
            errors.append("selected-library API root identity drifted")
        if api.get("aggregate") != expected_api_aggregate:
            errors.append("selected-library API aggregate drifted")
        theorems = api.get("theorems")
        definitions = api.get("definitions")
        if not isinstance(theorems, list) or not isinstance(definitions, list):
            errors.append("selected-library API routes must be arrays")
        else:
            result["theorem_count"] = len(theorems)
            result["explicit_page_count"] = len(theorems)
            result["defined_page_count"] = len(theorems)
            result["definition_page_count"] = len(definitions)
            if len(theorems) != SELECTED_LIBRARY_THEOREM_COUNT:
                errors.append("selected-library API theorem count drifted")
            if len(definitions) != SELECTED_LIBRARY_DEFINITION_COUNT:
                errors.append("selected-library API definition count drifted")
            route_paths: set[Path] = set()
            for row in theorems:
                if not isinstance(row, dict):
                    errors.append("selected-library theorem route must be an object")
                    continue
                for key in ("explicit_page", "defined_page"):
                    receipt = row.get(key)
                    if not isinstance(receipt, dict) or not isinstance(receipt.get("path"), str):
                        errors.append(f"selected-library theorem route lacks {key}")
                        continue
                    route_paths.add(Path(receipt["path"]))
            for row in definitions:
                if not isinstance(row, dict):
                    errors.append("selected-library definition route must be an object")
                    continue
                receipt = row.get("page")
                if not isinstance(receipt, dict) or not isinstance(receipt.get("path"), str):
                    errors.append("selected-library definition route lacks page")
                    continue
                route_paths.add(Path(receipt["path"]))
            expected_paths = route_paths | set(SELECTED_LIBRARY_REQUIRED)
            if expected_paths != source_files:
                errors.append("selected-library source paths differ from API routes")

    if manifest is not None:
        if manifest.get("root_sha256") != SELECTED_LIBRARY_MANIFEST_ROOT_SHA256:
            errors.append("selected-library manifest root identity drifted")
        if manifest.get("aggregate") != expected_manifest_aggregate:
            errors.append("selected-library manifest aggregate drifted")
        receipts = manifest.get("content_files")
        if not isinstance(receipts, list):
            errors.append("selected-library manifest receipts must be an array")
        else:
            receipt_paths = [
                row.get("path") if isinstance(row, dict) else None for row in receipts
            ]
            expected_receipt_paths = sorted(
                (path.as_posix() for path in source_files - {Path("manifest.json")})
            )
            if receipt_paths != expected_receipt_paths:
                errors.append("selected-library manifest receipt paths drifted")
            for row in receipts:
                if not isinstance(row, dict) or not isinstance(row.get("path"), str):
                    errors.append("selected-library manifest receipt must be an object")
                    continue
                relative = Path(row["path"])
                path = source / relative
                if not path.is_file():
                    continue
                raw = path.read_bytes()
                if row.get("bytes") != len(raw) or row.get("sha256") != hashlib.sha256(raw).hexdigest():
                    errors.append(
                        "selected-library manifest receipt differs from source: "
                        f"{relative.as_posix()}"
                    )

    source_html = tuple(path for path in source_files if path.suffix == ".html")
    built_html = tuple(path for path in built_files if path.suffix == ".html")
    result["html_page_count"] = len(built_html)
    if len(source_html) != SELECTED_LIBRARY_HTML_COUNT:
        errors.append(
            f"selected-library source has {len(source_html)} HTML pages; "
            f"expected {SELECTED_LIBRARY_HTML_COUNT}"
        )
    if len(built_html) != len(source_html):
        errors.append("built selected-library HTML-page count differs from source")

    style_path = source / "assets/pages.css"
    style = (
        style_path.read_text(encoding="utf-8", errors="replace")
        if style_path.is_file()
        else ""
    )
    if "http://" in style or "https://" in style or "@import" in style.lower():
        errors.append("selected-library CSS contains a remote/imported asset")
    if ":root" in style or "--pa-" in style:
        errors.append("selected-library CSS contains an unscoped root/custom property")
    if style:
        try:
            selectors = _qualified_css_selectors(style)
        except ValueError as exc:
            errors.append(f"cannot audit selected-library CSS isolation: {exc}")
        else:
            unscoped = [
                selector
                for selector in selectors
                if not selector.startswith(SELECTED_LIBRARY_BODY_SELECTOR)
            ]
            if not selectors or unscoped:
                errors.append(
                    "selected-library CSS is not isolated below "
                    f"{SELECTED_LIBRARY_BODY_SELECTOR}: {unscoped[:8]!r}"
                )

    if source.is_dir():
        result["source_manifest"] = _tree_manifest(source, source=False)
    if built.is_dir():
        result["built_manifest"] = _tree_manifest(built, source=False)
    return result


def _remote_runtime_asset(tag: str, attribute: str, raw: str) -> bool:
    """Return whether an HTML reference asks the browser to fetch remote code/media."""

    parsed = urlsplit(raw)
    if not (parsed.scheme or parsed.netloc or raw.startswith("//")):
        return False
    if tag in REMOTE_ASSET_TAGS and attribute == "src":
        return True
    return tag == "link" and attribute == "href"


def check(book: Path) -> dict[str, object]:
    book = book.resolve()
    html_root = book / "_build" / "html"
    errors: list[str] = []
    required = (
        html_root / "index.html",
        html_root / "intro.html",
        html_root / "search.html",
        html_root / "searchindex.js",
        html_root / "genindex.html",
        html_root / "objects.inv",
    )
    for path in required:
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f"missing or empty required build output: {path.relative_to(book)}")

    explorer = _check_explorer_copy(book, html_root, errors)
    selected_library = _check_selected_library_copy(book, html_root, errors)

    try:
        sources = _toc_sources(book)
    except ValueError as exc:
        sources = ()
        errors.append(str(exc))
    expected_pages: list[Path] = []
    for source in sources:
        relative = source.relative_to(book).with_suffix(".html")
        page = html_root / relative
        expected_pages.append(page)
        if not page.is_file() or page.stat().st_size == 0:
            errors.append(f"missing or empty TOC page: {relative}")

    html_pages = tuple(sorted(html_root.rglob("*.html"), key=lambda item: item.as_posix()))
    ordinary_pages = tuple(
        page
        for page in html_pages
        if not any(part.startswith("_") for part in page.relative_to(html_root).parts)
    )
    explorer_root = html_root / EXPLORER_RELATIVE
    explorer_pages = (
        tuple(sorted(explorer_root.rglob("*.html"), key=lambda item: item.as_posix()))
        if explorer_root.is_dir()
        else ()
    )
    selected_library_root = html_root / SELECTED_LIBRARY_RELATIVE
    selected_library_pages = (
        tuple(
            sorted(
                selected_library_root.rglob("*.html"),
                key=lambda item: item.as_posix(),
            )
        )
        if selected_library_root.is_dir()
        else ()
    )
    rendered_pages = tuple(
        dict.fromkeys(ordinary_pages + explorer_pages + selected_library_pages)
    )
    broken: set[tuple[str, str]] = set()
    escaping: set[tuple[str, str]] = set()
    broken_fragments: set[tuple[str, str]] = set()
    remote_assets: set[tuple[str, str]] = set()
    unsafe_links: set[tuple[str, str]] = set()
    parsed_pages: dict[Path, _References] = {}

    def parsed_page(path: Path) -> _References | None:
        cached = parsed_pages.get(path)
        if cached is not None:
            return cached
        parser = _References()
        try:
            parser.feed(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError) as exc:
            errors.append(f"cannot parse HTML {path.relative_to(html_root)}: {exc}")
            return None
        parsed_pages[path] = parser
        return parser

    for page in rendered_pages:
        parser = parsed_page(page)
        if parser is None:
            continue
        is_explorer = explorer_root.is_dir() and page.is_relative_to(explorer_root)
        is_selected_library = selected_library_root.is_dir() and page.is_relative_to(
            selected_library_root
        )
        explorer_relative = page.relative_to(explorer_root) if is_explorer else None
        if is_explorer and (
            explorer_relative in {Path("index.html"), Path("foundations.html")}
            or explorer_relative.parent == Path("tag")
            or explorer_relative in {
                Path("defined/index.html"),
                Path("defined/graph.html"),
            }
            or explorer_relative.parent in {
                Path("defined/tag"),
                Path("defined/definition"),
            }
        ):
            referenced_names = [
                Path(urlsplit(raw).path).name
                for _, _, raw in parser.targets
                if urlsplit(raw).path
            ]
            for asset in ("explorer.css", "explorer.js"):
                observed = referenced_names.count(asset)
                if observed != 1:
                    errors.append(
                        f"{page.relative_to(html_root).as_posix()} references "
                        f"{asset} {observed} times; expected once"
                    )
        if is_selected_library:
            referenced_names = [
                Path(urlsplit(raw).path).name
                for _, _, raw in parser.targets
                if urlsplit(raw).path
            ]
            observed = referenced_names.count("pages.css")
            if observed != 1:
                errors.append(
                    f"{page.relative_to(html_root).as_posix()} references "
                    f"pages.css {observed} times; expected once"
                )
        for tag, attribute, raw in parser.targets:
            if (is_explorer or is_selected_library) and _remote_runtime_asset(
                tag, attribute, raw
            ):
                remote_assets.add((page.relative_to(html_root).as_posix(), raw))
            if (
                (is_explorer or is_selected_library)
                and attribute == "href"
                and urlsplit(raw).scheme.lower() in {"data", "javascript", "vbscript"}
            ):
                unsafe_links.add((page.relative_to(html_root).as_posix(), raw))
            target, escaped = _local_target(page, html_root, raw)
            if escaped:
                escaping.add((page.relative_to(html_root).as_posix(), raw))
            elif target is not None and not target.exists():
                broken.add((page.relative_to(html_root).as_posix(), raw))
            if attribute != "href":
                continue
            parsed = urlsplit(raw)
            if parsed.scheme or parsed.netloc or not parsed.fragment:
                continue
            fragment_target = page if not parsed.path else target
            if (
                fragment_target is None
                or not fragment_target.is_file()
                or fragment_target.suffix.lower() not in {".html", ".htm"}
            ):
                continue
            target_parser = parsed_page(fragment_target)
            fragment = unquote(parsed.fragment)
            if target_parser is not None and fragment not in target_parser.anchors:
                broken_fragments.add((page.relative_to(html_root).as_posix(), raw))

    for relative in (
        Path("arithmetic-library/theorem-atlas.html"),
        Path("arithmetic-library/proof-explorer.html"),
    ):
        page = html_root / relative
        if not page.is_file():
            continue
        parser = parsed_page(page)
        if parser is None:
            continue
        referenced_names = [
            Path(urlsplit(raw).path).name
            for _, _, raw in parser.targets
            if urlsplit(raw).path
        ]
        for asset in ("arithmetic-book.css", "arithmetic-book.js"):
            observed = referenced_names.count(asset)
            if observed != 1:
                errors.append(
                    f"{relative.as_posix()} references {asset} {observed} times; expected once"
                )
    errors.extend(
        f"relative target escapes HTML root in {page}: {target}"
        for page, target in sorted(escaping)
    )
    errors.extend(f"broken relative target in {page}: {target}" for page, target in sorted(broken))
    errors.extend(
        f"missing HTML fragment target in {page}: {target}"
        for page, target in sorted(broken_fragments)
    )
    errors.extend(
        f"remote runtime asset in static PA library surface {page}: {target}"
        for page, target in sorted(remote_assets)
    )
    errors.extend(
        f"unsafe active link in static PA library surface {page}: {target}"
        for page, target in sorted(unsafe_links)
    )

    payload: dict[str, object] = {
        "book_source": _tree_manifest(book, source=True),
        "broken_fragment_target_count": len(broken_fragments),
        "broken_relative_target_count": len(broken) + len(escaping),
        "errors": errors,
        "escaping_relative_target_count": len(escaping),
        "explorer": explorer,
        "expected_toc_page_count": len(expected_pages),
        "format": "peano-wmi-book-integrity",
        "html": _tree_manifest(html_root, source=False) if html_root.is_dir() else None,
        "html_page_count": len(html_pages),
        "remote_runtime_asset_count": len(remote_assets),
        "selected_library": selected_library,
        "unsafe_active_link_count": len(unsafe_links),
        "status": "passed" if not errors else "failed",
        "version": 3,
    }
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--book", type=Path, default=Path("book"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    payload = check(args.book)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, allow_nan=False, indent=2, sort_keys=True) + "\n"
    args.output.write_text(encoded, encoding="utf-8")
    print(json.dumps(payload, allow_nan=False, sort_keys=True))
    return 0 if payload["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
