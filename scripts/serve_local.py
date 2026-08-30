#!/usr/bin/env python3
"""Serve the whole site locally, with the same URL shape as the faculty server.

The landing page links to the lab with an ABSOLUTE path (`/lab-lambda/`) because
on the server the two live side by side under `~/public_html/`. Serving the repo
root directly would therefore give 404s for the lab, and serving
`_deploy/vietnam2026` would give 404s too (the lab is not staged into it).

So this builds `_preview/` out of SYMLINKS — no copying, edits are live:

    _preview/index.html -> index.html          (landing page)
    _preview/assets     -> assets
    _preview/slides     -> slides
    _preview/book       -> book/_build/html    (needs `make book` at least once)
    _preview/lab-lambda -> lab-lambda
    _preview/peano-lab  -> peano-lab           (only if present on this branch)

Everything then resolves exactly as in production: `/` is the landing page,
`book/…` relative links work, and `/lab-lambda/` absolute links work.

Usage:  python3 scripts/serve_local.py [--port 8000] [--no-open]
        make serve
"""

from __future__ import annotations

import argparse
import functools
import http.server
import pathlib
import shutil
import socketserver
import sys
import threading
import webbrowser

REPO = pathlib.Path(__file__).resolve().parents[1]
PREVIEW = REPO / "_preview"

# link name -> source path (relative to the repo root)
LINKS = {
    "index.html": "index.html",
    "assets": "assets",
    "slides": "slides",
    "book": "book/_build/html",
    "lab-lambda": "lab-lambda",
    "peano-lab": "peano-lab",
}
OPTIONAL = {"peano-lab"}          # branch-specific; absent on main

# On the server the site lives under /vietnam2026/ while the labs sit at the
# root, and some pages link back with that absolute prefix. Mirror it locally so
# BOTH URL shapes resolve: `/` and `/vietnam2026/` serve the same landing page.
SITE_PREFIX = "vietnam2026"
SITE_CONTENT = ("index.html", "assets", "slides", "book")


class Handler(http.server.SimpleHTTPRequestHandler):
    """Static handler with no-cache headers (so edits show up on reload)."""

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "credentialless")
        super().end_headers()

    def log_message(self, fmt, *args):        # one tidy line per request
        sys.stderr.write("  %s\n" % (fmt % args))


def build_preview() -> list[str]:
    """(Re)create the symlink tree; return warnings about missing sources."""
    warnings: list[str] = []
    if PREVIEW.is_symlink() or PREVIEW.is_file():
        PREVIEW.unlink()
    elif PREVIEW.exists():
        shutil.rmtree(PREVIEW)
    PREVIEW.mkdir(parents=True)

    site = PREVIEW / SITE_PREFIX
    site.mkdir()
    for name, rel in LINKS.items():
        src = REPO / rel
        if not src.exists():
            if name not in OPTIONAL:
                hint = ("  — run `make book` first" if name == "book" else "")
                warnings.append(f"missing: {rel}{hint}")
            continue
        (PREVIEW / name).symlink_to(src)
        if name in SITE_CONTENT:            # also under the /vietnam2026/ prefix
            (site / name).symlink_to(src)
    return warnings


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-open", action="store_true",
                    help="do not open a browser window")
    args = ap.parse_args()

    warnings = build_preview()
    served = sorted(p.name for p in PREVIEW.iterdir())

    print(f"\n  Serving {PREVIEW.relative_to(REPO)}/ (symlinks — edits are live)\n")
    print(f"    landing page   http://localhost:{args.port}/")
    if "book" in served:
        print(f"    knowledge book http://localhost:{args.port}/book/")
    if "slides" in served:
        print(f"    slides         http://localhost:{args.port}/slides/")
    if "lab-lambda" in served:
        print(f"    Lambda Lab     http://localhost:{args.port}/lab-lambda/")
    if "peano-lab" in served:
        print(f"    Peano Lab      http://localhost:{args.port}/peano-lab/")
    for w in warnings:
        print(f"\n  ! {w}")
    print("\n  Ctrl-C to stop.\n")

    handler = functools.partial(Handler, directory=str(PREVIEW))
    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.TCPServer(("127.0.0.1", args.port), handler)
    except OSError as e:
        print(f"  Cannot bind port {args.port}: {e}")
        print(f"  Try:  python3 scripts/serve_local.py --port {args.port + 1}")
        return 1

    if not args.no_open:
        threading.Timer(0.5, webbrowser.open,
                        [f"http://localhost:{args.port}/"]).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  stopped.")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
