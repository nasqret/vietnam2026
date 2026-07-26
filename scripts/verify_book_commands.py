#!/usr/bin/env python3
"""Replay every lab command referenced in the book against the real engine.

Two extraction sources, routed to Lambda Lab or Peano Lab:
  1. every ``?cmd=`` deep-link payload (URL-decoded) — replayed in a fresh
     session each (that is what a deep link does);
  2. every ``λ>``- or ``pa>``-prefixed line inside fenced blocks — replayed
     sequentially, one session per lab per fenced block (proof state is kept).

Fails (exit 1) if any replay produces "Unknown command", "Parse error",
"No help topic", a Python traceback, or empty output.

Usage:  python3 scripts/verify_book_commands.py [paths...]
        (default: book/cookbook book/lectures book/appendix book/peano
                  book/intro.md)
"""

from __future__ import annotations

import html
import importlib.util
import pathlib
import re
import signal
import sys
import urllib.parse

REPO = pathlib.Path(__file__).resolve().parents[1]


def _load_driver(alias: str, source: pathlib.Path, import_root: pathlib.Path):
    """Load both top-level ``driver.py`` files without a module-name collision."""

    root = str(import_root)
    if root not in sys.path:
        sys.path.insert(0, root)
    spec = importlib.util.spec_from_file_location(alias, source)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load lab driver from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[alias] = module
    spec.loader.exec_module(module)
    return module


LAMBDA_PY = REPO / "lab-lambda" / "py"
PEANO_PY = REPO / "peano-lab" / "py"
lambda_driver = _load_driver(
    "_book_gate_lambda_driver", LAMBDA_PY / "driver.py", LAMBDA_PY
)
peano_driver = _load_driver(
    "_book_gate_peano_driver", PEANO_PY / "driver.py", PEANO_PY
)
DRIVERS = {"lambda": lambda_driver, "peano": peano_driver}

ANSI = re.compile(r"\x1b\[[0-9;]*m")
BAD = (
    "Unknown command",
    "Parse error",
    "Traceback (most recent call last)",
    "No help topic",
    "TIMEOUT (",
)
PEANO_BAD_PREFIXES = (
    "Unknown `pa` command",
    "No tactic named",
    "No tutorial named",
    "No knowledge-base card",
    "Tactic error:",
    "QED check failed:",
    "Tutorial command failed:",
    "Error:",
)
EXCEPTION_LINE = re.compile(
    r"^(?:Exception|[A-Za-z_][A-Za-z0-9_.]*(?:Error|Exception)):(?:\s|$)"
)
# interactive follow-ups are legal only mid-session; deep links are standalone
STANDALONE_OK = re.compile(
    r"^(reduce|red|r|nf|whnf|eta|debruijn|lam|expand|church|numeral|peano|decode|"
    r"alpha|equiv|let|defs|undef|ch|prove|tutorial|alligators|ag|kb|quiz|lean|"
    r"constants|tour|about|help|clear)\b|^[\\(λ]|^[A-Z0-9]"
)
PEANO_STANDALONE_OK = re.compile(
    r"^(?:pa|kb|tutorial|help|about|commands)(?:\s|$)"
)


def strip(s: str) -> str:
    return ANSI.sub("", s or "")


class _Timeout(Exception):
    pass


def _run_with_timeout(session, cmd: str, seconds: int = 30) -> str:
    """Engine calls are pure CPU; SIGALRM guards against wall-clock monsters."""

    def _alarm(signum, frame):
        raise _Timeout()
    old = signal.signal(signal.SIGALRM, _alarm)
    signal.alarm(seconds)
    try:
        return strip(session.run(cmd))
    except _Timeout:
        return "TIMEOUT (>30s wall clock)"
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def _failure(output: str, lab: str) -> str | None:
    """Return the first engine failure while ignoring markers inside prose."""

    for marker in BAD:
        if marker in output:
            return next(
                (line for line in output.splitlines() if marker in line),
                output.splitlines()[0] if output.splitlines() else marker,
            )[:100]
    if lab == "peano":
        for line in output.splitlines():
            if line.startswith(PEANO_BAD_PREFIXES):
                return line[:100]
    for line in output.splitlines():
        if EXCEPTION_LINE.match(line):
            return line[:100]
    return None


def replay_one(cmd: str, lab: str = "lambda") -> str | None:
    """Fresh-session replay; return an error description or None."""
    out = _run_with_timeout(DRIVERS[lab].LabSession(), cmd)
    if not out.strip():
        return "EMPTY OUTPUT"
    return _failure(out, lab)


def replay_block(cmds: list[str], lab: str = "lambda") -> list[tuple[str, str]]:
    """Sequential replay in one session; collect (cmd, error) pairs."""
    session = DRIVERS[lab].LabSession()
    errors = []
    for cmd in cmds:
        out = _run_with_timeout(session, cmd)
        if not out.strip():
            errors.append((cmd, "EMPTY OUTPUT"))
            continue
        error = _failure(out, lab)
        if error is not None:
            errors.append((cmd, error))
    return errors


def _command_from_href(href: str) -> str | None:
    """Read one command with HTML entities and URL encoding handled once."""

    parsed = urllib.parse.urlsplit(html.unescape(href))
    values = urllib.parse.parse_qs(parsed.query, keep_blank_values=True).get("cmd")
    return values[0] if values else None


def _link_lab(href: str, cmd: str) -> str:
    path = urllib.parse.urlsplit(html.unescape(href)).path.lower()
    if "peano-lab" in path or re.match(r"^pa(?:\s|$)", cmd):
        return "peano"
    return "lambda"


def _markdown_hrefs(source: str) -> list[str]:
    """Extract Markdown destinations while balancing parentheses in URLs."""

    hrefs: list[str] = []
    cursor = 0
    while True:
        marker = source.find("](", cursor)
        if marker < 0:
            return hrefs
        start = marker + 2
        depth = 1
        escaped = False
        index = start
        while index < len(source):
            char = source[index]
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    destination = source[start:index].strip()
                    # Book command destinations contain no literal spaces;
                    # tolerate an optional Markdown link title after one.
                    href = destination.split(maxsplit=1)[0]
                    if "?cmd=" in href:
                        hrefs.append(href)
                    cursor = index + 1
                    break
            index += 1
        else:
            return hrefs


def _deep_links(source: str, built_html: str | None) -> set[tuple[str, str]]:
    """Return deduplicated ``(lab, command)`` pairs from one book page."""

    hrefs: list[str]
    if built_html is not None:
        hrefs = re.findall(r'href="([^"]*[?]cmd=[^"]*)"', built_html)
    else:
        hrefs = _markdown_hrefs(source)
    links: set[tuple[str, str]] = set()
    for href in hrefs:
        cmd = _command_from_href(href)
        if cmd is not None:
            links.add((_link_lab(href, cmd), cmd))
    return links


def main(argv: list[str]) -> int:
    targets = [pathlib.Path(a) for a in argv] or [
        REPO / "book" / "cookbook", REPO / "book" / "lectures",
        REPO / "book" / "appendix", REPO / "book" / "peano",
        REPO / "book" / "intro.md",
    ]
    files: list[pathlib.Path] = []
    for t in targets:
        files += sorted(t.glob("*.md")) if t.is_dir() else [t]

    n_links = n_blocks = n_cmds = 0
    counts = {
        "lambda": {"links": 0, "blocks": 0, "commands": 0},
        "peano": {"links": 0, "blocks": 0, "commands": 0},
    }
    failures: list[str] = []

    for f in files:
        text = f.read_text(encoding="utf-8")
        # 1. deep links — read them from the BUILT page when available: href
        #    attributes are exact, whereas markdown URLs may contain unencoded
        #    parentheses that a source regex cannot delimit reliably.
        try:
            book_relative = f.resolve().relative_to(REPO / "book")
        except ValueError:
            html_f = None
        else:
            html_f = (
                REPO / "book" / "_build" / "html" / book_relative
            ).with_suffix(".html")
        if html_f is not None and html_f.exists():
            html_text = html_f.read_text(encoding="utf-8")
            seen_links = _deep_links(text, html_text)
        else:  # fallback: conservative source scan (encoded links only)
            seen_links = _deep_links(text, None)
        for lab, cmd in sorted(seen_links):
            n_links += 1
            counts[lab]["links"] += 1
            standalone = PEANO_STANDALONE_OK if lab == "peano" else STANDALONE_OK
            if not standalone.match(cmd):
                failures.append(
                    f"{f.name}: {lab} deep link is not standalone: {cmd!r}"
                )
                continue
            err = replay_one(cmd, lab)
            if err:
                failures.append(f"{f.name}: [{lab}] {cmd!r} → {err}")
        # 2. λ> and pa> session blocks.  A bare `pa>` is meaningful ENTER.
        for block in re.findall(r"```(?:text[^\n]*)?\n(.*?)```", text, re.S):
            prefixed = {
                "lambda": [
                    line.strip()[2:].strip()
                    for line in block.splitlines()
                    if line.strip().startswith("λ>")
                ],
                "peano": [
                    line.strip()[3:].strip()
                    for line in block.splitlines()
                    if line.strip().startswith("pa>")
                ],
            }
            for lab, cmds in prefixed.items():
                if not cmds:
                    continue
                n_blocks += 1
                n_cmds += len(cmds)
                counts[lab]["blocks"] += 1
                counts[lab]["commands"] += len(cmds)
                for cmd, err in replay_block(cmds, lab):
                    failures.append(
                        f"{f.name}: [{lab} session] {cmd!r} → {err}"
                    )

    print(f"checked {len(files)} files: {n_links} deep links, "
          f"{n_blocks} session blocks ({n_cmds} commands)")
    print(
        "  lambda: "
        f"{counts['lambda']['links']} links, {counts['lambda']['blocks']} blocks "
        f"({counts['lambda']['commands']} commands); peano: "
        f"{counts['peano']['links']} links, {counts['peano']['blocks']} blocks "
        f"({counts['peano']['commands']} commands)"
    )
    if failures:
        print(f"\n{len(failures)} FAILURES:")
        for fail in failures:
            print("  ✗", fail)
        return 1
    print("all commands replay cleanly ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
