#!/usr/bin/env python3
"""Replay every lab command referenced in the book against the real engine.

Two extraction sources:
  1. every ``?cmd=`` deep-link payload (URL-decoded) — replayed in a fresh
     session each (that is what a deep link does);
  2. every ``λ>``-prefixed line inside fenced blocks — replayed sequentially,
     one session per fenced block (terminal sessions keep ``let``/proof state).

Fails (exit 1) if any replay produces "Unknown command", "Parse error",
"No help topic", a Python traceback, or empty output.

Usage:  python3 scripts/verify_book_commands.py [paths...]
        (default: book/cookbook book/lectures book/appendix book/intro.md)
"""

from __future__ import annotations

import pathlib
import re
import signal
import sys
import urllib.parse

REPO = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "lab-lambda" / "py"))

import driver  # noqa: E402

ANSI = re.compile(r"\x1b\[[0-9;]*m")
BAD = ("Unknown command", "Parse error", "Traceback (most recent call last)",
       "No help topic", "TIMEOUT (")
# interactive follow-ups are legal only mid-session; deep links are standalone
STANDALONE_OK = re.compile(
    r"^(reduce|red|r|nf|whnf|eta|debruijn|lam|expand|church|numeral|peano|decode|"
    r"alpha|equiv|let|defs|undef|ch|prove|tutorial|alligators|ag|kb|quiz|lean|"
    r"constants|tour|about|help|clear)\b|^[\\(λ]|^[A-Z0-9]"
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


def replay_one(cmd: str) -> str | None:
    """Fresh-session replay; return an error description or None."""
    out = _run_with_timeout(driver.LabSession(), cmd)
    if not out.strip():
        return "EMPTY OUTPUT"
    for marker in BAD:
        if marker in out:
            return out.splitlines()[0][:100]
    return None


def replay_block(cmds: list[str]) -> list[tuple[str, str]]:
    """Sequential replay in one session; collect (cmd, error) pairs."""
    session = driver.LabSession()
    errors = []
    for cmd in cmds:
        out = _run_with_timeout(session, cmd)
        for marker in BAD:
            if marker in out:
                errors.append((cmd, out.splitlines()[0][:100]))
                break
    return errors


def main(argv: list[str]) -> int:
    targets = [pathlib.Path(a) for a in argv] or [
        REPO / "book" / "cookbook", REPO / "book" / "lectures",
        REPO / "book" / "appendix", REPO / "book" / "intro.md",
    ]
    files: list[pathlib.Path] = []
    for t in targets:
        files += sorted(t.glob("*.md")) if t.is_dir() else [t]

    n_links = n_blocks = n_cmds = 0
    failures: list[str] = []

    for f in files:
        text = f.read_text(encoding="utf-8")
        # 1. deep links — read them from the BUILT page when available: href
        #    attributes are exact, whereas markdown URLs may contain unencoded
        #    parentheses that a source regex cannot delimit reliably.
        html_f = (REPO / "book" / "_build" / "html"
                  / f.resolve().relative_to(REPO / "book")).with_suffix(".html")
        seen_cmds: set[str] = set()
        if html_f.exists():
            html_text = html_f.read_text(encoding="utf-8")
            for m in re.finditer(r'href="[^"]*[?]cmd=([^"]+)"', html_text):
                seen_cmds.add(urllib.parse.unquote(
                    m.group(1).replace("&amp;", "&")))
        else:  # fallback: conservative source scan (encoded links only)
            for m in re.finditer(r"[?]cmd=([^)\"'\s&]+)", text):
                seen_cmds.add(urllib.parse.unquote(m.group(1)))
        for cmd in sorted(seen_cmds):
            n_links += 1
            if not STANDALONE_OK.match(cmd):
                failures.append(f"{f.name}: deep link is not standalone: {cmd!r}")
                continue
            err = replay_one(cmd)
            if err:
                failures.append(f"{f.name}: {cmd!r} → {err}")
        # 2. λ> session blocks
        for block in re.findall(r"```(?:text[^\n]*)?\n(.*?)```", text, re.S):
            cmds = [ln[2:].strip() for ln in block.splitlines()
                    if ln.strip().startswith("λ>")]
            if not cmds:
                continue
            n_blocks += 1
            n_cmds += len(cmds)
            for cmd, err in replay_block(cmds):
                failures.append(f"{f.name}: [session] {cmd!r} → {err}")

    print(f"checked {len(files)} files: {n_links} deep links, "
          f"{n_blocks} session blocks ({n_cmds} commands)")
    if failures:
        print(f"\n{len(failures)} FAILURES:")
        for fail in failures:
            print("  ✗", fail)
        return 1
    print("all commands replay cleanly ✓")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
