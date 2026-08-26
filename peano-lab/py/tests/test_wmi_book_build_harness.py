"""Cheap, no-network regressions for the WMI Jupyter Book build harness."""

from __future__ import annotations

import hashlib
import importlib.util
import os
from pathlib import Path
import sys
import uuid

import pytest


REPO = Path(__file__).resolve().parents[3]
PACKAGER = REPO / "scripts" / "package_wmi_book_snapshot.py"
CHECKER = REPO / "scripts" / "check_wmi_book_build.py"
RUNNER = REPO / "scripts" / "run_wmi_book_build.py"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_snapshot_rejects_an_output_inside_the_repository() -> None:
    packager = _load(PACKAGER, "_test_wmi_book_packager_inside")
    output = REPO / f".wmi-book-audit-{uuid.uuid4().hex}.tar"
    assert not output.exists()

    with pytest.raises(ValueError, match="outside the repository"):
        packager.build_archive(output, REPO)

    assert not output.exists()


def test_snapshot_rejects_an_output_hardlinked_to_an_input(tmp_path: Path) -> None:
    packager = _load(PACKAGER, "_test_wmi_book_packager_hardlink")
    source = REPO / "requirements.txt"
    source_digest = hashlib.sha256(source.read_bytes()).hexdigest()
    output = tmp_path / "hardlinked-output.tar"
    os.link(source, output)

    with pytest.raises(ValueError, match="hardlinked to input: requirements.txt"):
        packager.build_archive(output, REPO)

    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_digest
    assert output.samefile(source)
    assert hashlib.sha256(output.read_bytes()).hexdigest() == source_digest


def test_snapshot_reads_each_input_once_and_is_deterministic(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    packager = _load(PACKAGER, "_test_wmi_book_packager_determinism")
    selected = {
        (REPO / relative).resolve(): 0 for relative in packager.snapshot_files(REPO)
    }
    original_open = os.open

    def counted_open(path, *args, **kwargs):
        resolved = Path(path).resolve()
        if resolved in selected:
            selected[resolved] += 1
        return original_open(path, *args, **kwargs)

    first_archive = tmp_path / "first.tar"
    monkeypatch.setattr(packager.os, "open", counted_open)
    first_metadata = packager.build_archive(first_archive, REPO)
    monkeypatch.setattr(packager.os, "open", original_open)

    assert selected
    assert set(selected.values()) == {1}

    second_archive = tmp_path / "second.tar"
    second_metadata = packager.build_archive(second_archive, REPO)
    assert first_archive.read_bytes() == second_archive.read_bytes()
    assert first_metadata == second_metadata


def test_snapshot_contains_the_complete_proof_explorer_evidence_boundary() -> None:
    packager = _load(PACKAGER, "_test_wmi_book_packager_explorer_boundary")
    selected = {path.as_posix() for path in packager.snapshot_files(REPO)}
    required = {
        "scripts/build_bertrand_defined_explorer.py",
        "scripts/build_bertrand_proof_explorer.py",
        "scripts/build_pa_defined_explorer.py",
        "scripts/build_pa_proof_explorer.py",
        "research/arithmetic-library/pa-proof-tags.json",
        "research/arithmetic-library/pa-proof-informal.json",
        "peano-lab/py/peano_lab/kernel/checker.py",
        "peano-lab/py/peano_lab/kernel/formulas.py",
        "peano-lab/py/peano_lab/kernel/proofs.py",
        "peano-lab/py/peano_lab/kernel/terms.py",
        "peano-lab/py/peano_lab/engine/tactics.py",
        "book/_static/pa-proof-explorer/manifest.json",
        "book/_static/pa-proof-explorer/graph.html",
        "book/_static/pa-proof-explorer/api/corpus.json",
        "book/_static/pa-proof-explorer/api/graph.json",
        "book/_static/pa-proof-explorer/api/graph.schema.json",
        "book/_static/pa-proof-explorer/defined/manifest.json",
        "book/_static/pa-proof-explorer/defined/api/corpus.json",
        "book/_static/pa-proof-explorer/defined/api/graph.json",
        "book/_static/pa-proof-explorer/defined/api/graph.schema.json",
        "book/_static/pa-proof-explorer/defined/assets/explorer.css",
        "book/_static/pa-proof-explorer/defined/assets/explorer.js",
        "book/_static/pa-proof-explorer/k3b/index.html",
        "book/_static/pa-proof-explorer/k3b/assets/k3b.css",
        "book/_static/pa-proof-explorer/k3b/assets/k3b.js",
        "book/_static/bertrand-proof-explorer/manifest.json",
        "book/_static/bertrand-proof-explorer/api/corpus.json",
        "book/_static/bertrand-proof-explorer/api/graph.json",
        "book/_static/bertrand-proof-explorer/defined/manifest.json",
        "book/_static/bertrand-proof-explorer/defined/api/corpus.json",
        "book/_static/bertrand-proof-explorer/defined/api/graph.json",
        "book/_static/bertrand-proof-explorer/defined/api/graph.schema.json",
        "book/_static/bertrand-proof-explorer/defined/assets/explorer.css",
        "book/_static/bertrand-proof-explorer/defined/assets/explorer.js",
    }
    assert required <= selected
    assert any(path.startswith("book/_static/pa-proof-explorer/tag/") for path in selected)
    assert any(
        path.startswith("book/_static/pa-proof-explorer/defined/tag/")
        for path in selected
    )
    assert any(
        path.startswith("book/_static/pa-proof-explorer/defined/definition/")
        for path in selected
    )
    assert any(
        path.startswith("book/_static/bertrand-proof-explorer/defined/tag/")
        for path in selected
    )
    assert any(
        path.startswith("book/_static/bertrand-proof-explorer/defined/definition/")
        for path in selected
    )


def test_runner_checks_both_campaign_editions_before_the_book_build() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    labels = (
        '"05-atlas-check"',
        '"06-proof-explorer-check"',
        '"06b-defined-proof-explorer-check"',
        '"06c-bertrand-proof-explorer-check"',
        '"06d-bertrand-defined-proof-explorer-check"',
        '"07-jupyter-book-build"',
        '"08-book-integrity"',
    )
    positions = [source.index(label) for label in labels]
    assert positions == sorted(positions)
    assert '[str(venv_python), "scripts/build_pa_proof_explorer.py", "--check"]' in source
    assert '[str(venv_python), "scripts/build_pa_defined_explorer.py", "--check"]' in source
    assert '[str(venv_python), "scripts/build_bertrand_proof_explorer.py", "--check"]' in source
    assert '[str(venv_python), "scripts/build_bertrand_defined_explorer.py", "--check"]' in source


def test_checker_rejects_an_existing_target_outside_html_root(
    tmp_path: Path,
) -> None:
    checker = _load(CHECKER, "_test_wmi_book_checker_escape")
    book = tmp_path / "book"
    html = book / "_build" / "html"
    html.mkdir(parents=True)
    (book / "_toc.yml").write_text("format: jb-book\nroot: intro\n", encoding="utf-8")
    (book / "intro.md").write_text("# Introduction\n", encoding="utf-8")

    (html / "index.html").write_text("<html>index</html>\n", encoding="utf-8")
    (html / "intro.html").write_text(
        '<html><a href="../outside.txt">escape</a></html>\n', encoding="utf-8"
    )
    (html / "search.html").write_text("<html>search</html>\n", encoding="utf-8")
    (html / "genindex.html").write_text("<html>index</html>\n", encoding="utf-8")
    (html / "searchindex.js").write_text("const index = {};\n", encoding="utf-8")
    (html / "objects.inv").write_bytes(b"inventory\n")
    outside = book / "_build" / "outside.txt"
    outside.write_text("this existing host file must not excuse the escape\n", encoding="utf-8")

    payload = checker.check(book)

    assert outside.is_file()
    assert payload["status"] == "failed"
    assert payload["escaping_relative_target_count"] == 1
    assert payload["broken_relative_target_count"] == 1
    assert any(
        "relative target escapes HTML root in intro.html: ../outside.txt" in error
        for error in payload["errors"]
    )
    assert any("missing PA Proof Explorer source" in error for error in payload["errors"])


def test_checker_distinguishes_remote_runtime_assets_from_external_links() -> None:
    checker = _load(CHECKER, "_test_wmi_book_checker_remote_assets")
    assert checker._remote_runtime_asset("script", "src", "https://example.test/app.js")
    assert checker._remote_runtime_asset("link", "href", "//example.test/app.css")
    assert not checker._remote_runtime_asset("a", "href", "https://example.test/paper")
    assert not checker._remote_runtime_asset("script", "src", "assets/explorer.js")


def test_checker_enforces_recursive_explorer_asset_isolation() -> None:
    checker = _load(CHECKER, "_test_wmi_book_checker_asset_isolation")
    safe = """
    body.pa-proof-site { color: black; }
    @media print {
      body.pa-proof-site .pa-proof-line,
      body.pa-proof-site .pa-proof-line code { color: inherit; }
    }
    """
    unsafe = safe + "\n@media screen { .foreign-page { display: none; } }\n"
    assert checker._qualified_css_selectors(safe) == (
        "body.pa-proof-site",
        "body.pa-proof-site .pa-proof-line",
        "body.pa-proof-site .pa-proof-line code",
    )
    assert ".foreign-page" in checker._qualified_css_selectors(unsafe)

    gated = """
    whenReady(function () {
      if (!document.body || !document.body.classList.contains("pa-proof-site")) return;
      document.querySelectorAll("[data-proof-dashboard]").forEach(initializeDashboard);
      window.addEventListener("hashchange", markProofLine);
    });
    """
    ungated = gated.replace(
        'if (!document.body || !document.body.classList.contains("pa-proof-site")) return;',
        "",
    )
    assert checker._explorer_javascript_is_body_gated(gated)
    assert not checker._explorer_javascript_is_body_gated(ungated)


def test_submit_and_slurm_scripts_preserve_the_reviewed_boundaries() -> None:
    submit = (REPO / "scripts" / "submit_wmi_book_build.sh").read_text(
        encoding="utf-8"
    )
    slurm = (REPO / "slurm" / "peano_wmi_book_build.sbatch").read_text(
        encoding="utf-8"
    )

    assert submit.count("status --porcelain=v1 -z --untracked-files=all") == 2
    assert 'cmp -s "$head_before" "$head_after"' in submit
    assert 'cmp -s "$status_before" "$status_after"' in submit
    assert 'logs_root="$snapshot_root/logs"' in submit
    assert "$source_root/logs" not in submit
    assert '"bash -c ' in submit
    assert '"bash -s ' in submit
    assert "bash -l" not in submit

    assert slurm.startswith("#!/bin/bash\n")
    assert "#SBATCH --output=/dev/null" in slurm
    assert "#SBATCH --error=/dev/null" in slurm
    for name in ("PYTHONPATH", "PYTHONHOME", "VIRTUAL_ENV", "CONDA_"):
        assert name in submit
        assert name in slurm
