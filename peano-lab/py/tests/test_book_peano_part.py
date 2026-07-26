"""Release contracts for the six-chapter “Building Peano Lab” book part."""

from __future__ import annotations

from pathlib import Path
import subprocess
import sys


REPO = Path(__file__).resolve().parents[3]
BOOK = REPO / "book"
GATE = REPO / "scripts" / "verify_book_commands.py"
CHAPTERS = (
    "why-pa",
    "kernel",
    "tactics",
    "tacticals",
    "induction-ladder",
    "limits",
)


def test_building_peano_lab_part_has_the_binding_chapter_order() -> None:
    toc = (BOOK / "_toc.yml").read_text(encoding="utf-8")
    positions = [toc.index(f"- file: peano/{chapter}") for chapter in CHAPTERS]

    assert positions == sorted(positions)
    for chapter in CHAPTERS:
        source = BOOK / "peano" / f"{chapter}.md"
        assert source.is_file()
        assert source.read_text(encoding="utf-8").startswith("# ")


def test_landing_page_announces_the_live_checked_lab() -> None:
    landing = (REPO / "index.html").read_text(encoding="utf-8")

    assert "Peano Lab <em>(in development)</em>" not in landing
    assert "Now live · checked in the browser" in landing
    assert "a separate 234-line kernel rechecks every QED" in landing
    assert 'href="/peano-lab/"' in landing
    assert 'href="book/peano/index.html"' in landing


def test_every_new_chapter_command_replays_through_the_real_driver() -> None:
    paths = [str(BOOK / "peano" / f"{chapter}.md") for chapter in CHAPTERS]
    result = subprocess.run(
        [sys.executable, str(GATE), *paths],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "all commands replay cleanly" in result.stdout
