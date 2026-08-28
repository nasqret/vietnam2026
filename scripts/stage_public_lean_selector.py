#!/usr/bin/env python3
"""Overlay the verified Lean selector onto staged public theorem pages only.

Frozen source explorers, proof artifacts, kernel receipts, and their original
JavaScript remain untouched.  Only eligible graph/theorem HTML inside the
dedicated public staging tree receives the shared, root-relative UI overlay.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from html import escape
import ipaddress
import os
from pathlib import Path
import re
import shutil
import sys
from urllib.parse import urlsplit


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "book" / "_static" / "lean-selector"
PUBLIC_ASSETS = "/proofs/assets"
MAX_HTML_BYTES = 32 * 1024 * 1024
MAX_API_BYTES = 2048
CLOSING_HEAD = re.compile(rb"</head\s*>", flags=re.IGNORECASE)
GRAPH_PANELS = (b"pa-graph-details", b"pd-graph-details", b"data-graph-title")
THEOREM_PANELS = (b"pa-proof-sidebar", b"pd-theorem-layout", b"data-lean-selector-host")


class PublicSelectorError(ValueError):
    """A public proof overlay or optional HTTPS origin is unsafe."""


@dataclass(frozen=True, slots=True)
class StageResult:
    candidates: int
    injected: int
    unchanged: int
    assets: int


def _api_url(value: str) -> str:
    if type(value) is not str:
        raise PublicSelectorError("public Lean API URL must be exact text")
    if value == "":
        return ""
    if len(value.encode("utf-8")) > MAX_API_BYTES or any(char.isspace() for char in value):
        raise PublicSelectorError("public Lean API URL exceeds its safe bounded form")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as error:
        raise PublicSelectorError("public Lean API URL is malformed") from error
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path.rstrip("/") != "/api/lean-strands"
        or "\\" in value
        or "%" in parsed.netloc
        or (port is not None and not 1 <= port <= 65535)
    ):
        raise PublicSelectorError(
            "an external Lean API must be one credential-free HTTPS /api/lean-strands URL"
        )
    host = parsed.hostname.lower().rstrip(".")
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".localhost"):
        raise PublicSelectorError("a public Lean API cannot point to a private loopback host")
    try:
        address = ipaddress.ip_address(host)
    except ValueError:
        address = None
    if address is not None and (
        address.is_private
        or address.is_loopback
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    ):
        raise PublicSelectorError("a public Lean API cannot target a non-public network address")
    return value.rstrip("/")


def _overlay(api_url: str) -> bytes:
    rows = []
    if api_url:
        rows.append(
            '<meta name="peano-lean-strand-api" content="'
            + escape(api_url, quote=True)
            + '">'
        )
    rows.extend(
        (
            f'<link rel="stylesheet" href="{PUBLIC_ASSETS}/lean-selector.css">',
            f'<script defer src="{PUBLIC_ASSETS}/lean-selector.js"></script>',
        )
    )
    return ("\n".join(rows) + "\n").encode("utf-8")


def _safe_root(root: Path) -> Path:
    chosen = Path(root).expanduser()
    if chosen.is_symlink():
        raise PublicSelectorError("public proof staging root cannot be a symbolic link")
    try:
        resolved = chosen.resolve(strict=True)
    except (OSError, RuntimeError) as error:
        raise PublicSelectorError("public proof staging root does not exist") from error
    if not resolved.is_dir():
        raise PublicSelectorError("public proof staging root must be an ordinary directory")
    return resolved


def _source_asset(filename: str) -> bytes:
    selected = SOURCE / filename
    if selected.is_symlink() or not selected.is_file():
        raise PublicSelectorError(f"required reviewed Lean selector asset is unavailable: {filename}")
    return selected.read_bytes()


def _candidate(path: Path, relative: Path) -> tuple[bool, tuple[bytes, ...]]:
    # Research checkpoints have complete independently verified certificates,
    # but their names are not enrolled in the Alpha-only on-demand service.
    # Publishing a proof must never manufacture a service admission.
    if relative.parts and relative.parts[0] == "checkpoints":
        return False, ()
    if path.suffix.lower() != ".html" or "explorer" not in relative.parts:
        return False, ()
    if path.name == "graph.html":
        return True, GRAPH_PANELS
    if path.parent.name == "tag":
        return True, THEOREM_PANELS
    return False, ()


def _pages(root: Path) -> tuple[Path, ...]:
    pages: list[Path] = []
    for base, directories, names in os.walk(root, followlinks=False):
        directories[:] = sorted(
            directory
            for directory in directories
            if directory not in {"assets", "api", "artifacts", "definition", "name"}
            and not (Path(base) / directory).is_symlink()
        )
        for filename in sorted(names):
            path = Path(base) / filename
            if path.is_symlink():
                continue
            matched, _ = _candidate(path, path.relative_to(root))
            if matched:
                pages.append(path)
    return tuple(sorted(pages))


def stage_public_lean_selector(
    root: Path,
    *,
    api_url: str = "",
    check: bool = False,
) -> StageResult:
    destination = _safe_root(root)
    selected_api = _api_url(api_url)
    insertion = _overlay(selected_api)
    assets = destination / "assets"
    if assets.exists() and (assets.is_symlink() or not assets.is_dir()):
        raise PublicSelectorError("staged Lean selector assets are not a safe ordinary directory")
    if not check:
        assets.mkdir(mode=0o755, exist_ok=True)
    copied = 0
    for filename in ("lean-selector.js", "lean-selector.css"):
        expected = _source_asset(filename)
        target = assets / filename
        if target.is_symlink():
            raise PublicSelectorError("staged Lean selector assets cannot overwrite a symbolic link")
        if check:
            if not target.is_file() or target.read_bytes() != expected:
                raise PublicSelectorError(f"staged Lean selector asset is stale: {filename}")
        else:
            if not target.is_file() or target.read_bytes() != expected:
                shutil.copyfile(SOURCE / filename, target)
                copied += 1

    candidates = 0
    injected = 0
    unchanged = 0
    for path in _pages(destination):
        relative = path.relative_to(destination)
        matched, markers = _candidate(path, relative)
        if not matched:
            continue
        size = path.stat().st_size
        if size > MAX_HTML_BYTES:
            raise PublicSelectorError(f"public proof HTML exceeds its safe overlay bound: {relative}")
        original = path.read_bytes()
        if not any(marker in original for marker in markers):
            raise PublicSelectorError(
                "public theorem graph/detail page lacks a supported reviewed proof panel: "
                f"{relative}"
            )
        candidates += 1
        marker = f'{PUBLIC_ASSETS}/lean-selector.js'.encode("ascii")
        if marker in original:
            if original.count(marker) != 1:
                raise PublicSelectorError(
                    f"public theorem page repeats its Lean proof selector: {relative}"
                )
            if insertion not in original:
                raise PublicSelectorError(f"staged Lean selector configuration is stale: {relative}")
            unchanged += 1
            continue
        if check:
            raise PublicSelectorError(f"public theorem page lacks its Lean proof selector: {relative}")
        closing = CLOSING_HEAD.search(original)
        if closing is None:
            raise PublicSelectorError(f"public theorem page has no safe closing head tag: {relative}")
        updated = original[: closing.start()] + insertion + original[closing.start() :]
        path.write_bytes(updated)
        injected += 1

    if candidates == 0:
        raise PublicSelectorError("public proof staging contains no checked theorem graph/detail pages")
    return StageResult(candidates, injected, unchanged, copied)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--api-url", default="")
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args(argv)
    try:
        result = stage_public_lean_selector(
            arguments.root,
            api_url=arguments.api_url,
            check=arguments.check,
        )
    except (OSError, PublicSelectorError) as error:
        print(f"Public Lean selector staging failed: {error}", file=sys.stderr)
        return 1
    action = "Verified" if arguments.check else "Enhanced"
    print(
        f"{action} {result.candidates:,} public theorem graph/detail pages "
        f"({result.injected:,} new overlays; {result.assets} copied assets)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
