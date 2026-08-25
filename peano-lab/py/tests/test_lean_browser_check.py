"""Adversarial tests for the real theorem-browser acceptance checker."""

from __future__ import annotations

import importlib.util
import io
import json
from pathlib import Path
import sys
from urllib.parse import quote
import zipfile

import pytest


ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / "scripts" / "check_lean_browser.py"
SPEC = importlib.util.spec_from_file_location("hydra_lean_browser_check", SOURCE)
assert SPEC is not None and SPEC.loader is not None
CHECK = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECK
SPEC.loader.exec_module(CHECK)


def _archive(*, theorem: str = "add_comm", omit: str | None = None, extra: str | None = None) -> bytes:
    output = io.BytesIO()
    catalog = {
        "schema": "peano-lean-proof-strand-package-v1",
        "strands": {"fixture": {"name": theorem}},
    }
    files = {
        "PeanoLab/Presentation.lean": b"import Lean\n",
        "PeanoLab/Generated/AddComm_fixture/Strand.lean": b"import PeanoLab.Codec\n",
        "manifest.json": json.dumps(catalog).encode("utf-8"),
        "README.txt": b"lake build\n",
    }
    if omit is not None:
        files.pop(omit)
    if extra is not None:
        files[extra] = b"not safe\n"
    with zipfile.ZipFile(output, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)
    return output.getvalue()


def _live(source: str) -> str:
    return "https://live.lean-lang.org/#code=" + quote(source, safe="")


def test_accepts_loopback_http_and_public_https() -> None:
    assert CHECK._base_url("http://127.0.0.1:8787/") == "http://127.0.0.1:8787"
    assert CHECK._base_url("https://proof.example") == "https://proof.example"


@pytest.mark.parametrize(
    "value",
    (
        "http://proof.example",
        "https://user:password@proof.example",
        "https://proof.example/path",
        "https://proof.example?token=secret",
    ),
)
def test_rejects_unsafe_browser_origin(value: str) -> None:
    with pytest.raises(CHECK.BrowserCheckError):
        CHECK._base_url(value)


def test_rejects_cross_origin_download() -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="cross-origin"):
        CHECK._same_origin("http://127.0.0.1:8787", "https://invalid.example/leak.lean")


def test_live_share_contains_the_exact_standalone_source() -> None:
    source = "import Lean.Elab.Tactic\n\ntheorem checked : True := by trivial\n"
    CHECK._check_live_url(_live(source), source.encode("utf-8"))


def test_live_share_rejects_a_changed_source() -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="exact downloaded proof"):
        CHECK._check_live_url(_live("import Lean\n"), b"import Lean\n-- changed\n")


@pytest.mark.parametrize(
    "source",
    (
        "import Mathlib\ntheorem checked : True := by trivial\n",
        "import Lean\ntheorem unchecked : True := by sorry\n",
        "import Lean\naxiom unchecked : True\n",
    ),
)
def test_live_share_rejects_unavailable_or_unproved_source(source: str) -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="unavailable or unproved"):
        CHECK._check_live_url(_live(source), source.encode("utf-8"))


def test_generated_lean_package_archive_is_complete() -> None:
    count, size = CHECK._check_archive(_archive(), "add_comm")
    assert count == 4
    assert size > 0


@pytest.mark.parametrize("missing", ("PeanoLab/Presentation.lean", "README.txt"))
def test_archive_rejects_missing_generated_package_file(missing: str) -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="incomplete"):
        CHECK._check_archive(_archive(omit=missing), "add_comm")


@pytest.mark.parametrize("private", ("PeanoLab/Codec.lean", "lakefile.toml", "lean-toolchain"))
def test_archive_does_not_export_the_separate_private_companion(private: str) -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="separate companion source"):
        CHECK._check_archive(_archive(extra=private), "add_comm")


@pytest.mark.parametrize("unsafe", ("../escape.lean", "/absolute.lean", "bad\\escape.lean"))
def test_archive_rejects_path_traversal(unsafe: str) -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="unsafe entry"):
        CHECK._check_archive(_archive(extra=unsafe), "add_comm")


def test_archive_rejects_a_different_selected_theorem() -> None:
    with pytest.raises(CHECK.BrowserCheckError, match="selected theorem"):
        CHECK._check_archive(_archive(theorem="mul_comm"), "add_comm")
