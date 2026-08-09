"""Focused acceptance tests for the selected-only candidate page source."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from html.parser import HTMLParser
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
from types import SimpleNamespace
from urllib.parse import urlsplit

import pytest


ROOT = Path(__file__).resolve().parents[3]
PY_ROOT = ROOT / "peano-lab" / "py"
for entry in (ROOT, PY_ROOT):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

import training.peano_hydra.library_page_deployment as page_module  # noqa: E402
from training.peano_hydra.library_page_deployment import (  # noqa: E402
    LibraryPageDeploymentError,
    build_candidate_library_page_deployment,
    canonical_document_bytes,
    library_page_deployment_schema,
    library_page_deployment_schema_identity,
    load_library_page_deployment,
    readiness_report,
    validate_library_page_deployment,
)


SCHEMA_SOURCE = ROOT / "training/peano_hydra/library-page-deployment-schema-v1.json"
OUTPUT = ROOT / "book/_static/pa-selected-library"
REPORT = ROOT / "artifacts/peano-hydra/library-page-deployment-candidate-v1-readiness.json"
CLI = ROOT / "scripts/build_peano_hydra_library_pages.py"
THEOREM_COUNT = 384
DEFINITION_COUNT = 40
HTML_PAGE_COUNT = 809
CONTENT_FILE_COUNT = 812
TREE_FILE_COUNT = 813
PA_GLOBAL_KEY = re.compile(r"PA[0-9A-Y]{4}")

FINAL_PINS = {
    "schema": (21_410, "8cdf0e947ce7156109b7591c99ed28d8ee1f938edd3cddfb414d48d7efacdafd"),
    "api": (451_803, "a7a4be8ba895b9e69955e82bda5bbfe7418eeda47632a59899e6ba0896acaaf0"),
    "manifest": (140_391, "751c3eefc99e5b30d612049fd99a0d890cd696b3fda0f426ca64d835c5fe2e6f"),
    "readiness": (3_118, "69b11b858348e3dda9a007b495c7198634822623d45314f6f82f551141bc9357"),
}
FINAL_ROOTS = {
    "api": "2efbb00a763f120e5cee6271f3d64838b3a54e04e73a4c78c738f4d50f0b83b1",
    "definition_records": "da9499f4748a64c94f83d3bd4c3bf4a35e1f7291cd0cb54b4c9b17138e8379c6",
    "files": "ff9fae5e0e26c09bb2a9f9778f55a8688b61a06c2357451730669168c566a910",
    "manifest": "94b38f4914853c87315f0bc94d33347164d4cb7c01cd81568b1c4f47cb1b1563",
    "readiness": "8f7bf0fc18917b92d02d862e13507d28f1bf7d2842fcd93427d3a2879a193b1f",
    "theorem_records": "baf22fce94323808529e35480b911c4f0d69fcfb05378931e61a9b06108f95fa",
}

HISTORICAL_PINS = {
    "research/arithmetic-library/pa-proof-tags.json": "84d741c7319cd14ac2f42dd3a131ae908f3ca56b421a1a3bb8c78f4e6f2f2052",
    "book/_static/pa-proof-explorer/manifest.json": "a45a2a85b9fcb418a4117c38d3e5025add873431cb778466ee1a960488c7cd7d",
    "book/_static/pa-proof-explorer/api/corpus.json": "95df7f7d096c41cc25e49217e4310451477ea5c45bf8624f67f41893693e43e1",
    "book/_static/pa-proof-explorer/defined/manifest.json": "e2a9177ad57246d7a40609bd7474e0077ef1522334bdfd521e0b4a5c98432c90",
    "book/_static/pa-proof-explorer/defined/api/corpus.json": "1e5de6a773d5283280909677509420c01afe34a6d4f6fe5dc202114b87b6433d",
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v1.json": "e719dd526d0aa07e2521fb2e499f2ee6810506d32a912298f11dbac60a2c0289",
    "artifacts/peano-hydra/library-epoch-metadata-candidate-v2.json": "dc6a59ce08397eba698651f6ed4faac0533dec55c13d5a8ca49d863d19d7b72d",
}


def _sha(raw: bytes) -> str:
    return sha256(raw).hexdigest()


def _compact(value: object) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


@pytest.fixture(scope="module")
def built() -> tuple[dict[str, bytes], dict[str, object]]:
    return page_module._build_candidate_library_page_deployment_with_readiness(
        repository_root=ROOT
    )


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.tags: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        values = dict(attrs)
        self.tags.append((tag, values))
        for key in ("href", "src"):
            if values.get(key):
                self.links.append((key, str(values[key])))


def test_schema_is_canonical_closed_and_candidate_only() -> None:
    raw = SCHEMA_SOURCE.read_bytes()
    schema = library_page_deployment_schema()
    identity = library_page_deployment_schema_identity()
    assert canonical_document_bytes(schema, limit=131_072) == raw
    preimage = {key: value for key, value in schema.items() if key != "semantic_sha256"}
    assert schema["semantic_sha256"] == _sha(_compact(preimage))
    assert identity["artifact_sha256"] == _sha(raw)
    assert identity["semantic_sha256"] == schema["semantic_sha256"]
    assert schema["claim_boundary"]["deployed"] is False
    shapes = schema["object_shapes"]
    for shape in shapes.values():
        fields = shape["fields"]
        assert len(fields) == len(set(fields))
        assert set(fields) == set(shape["types"])
    roots = schema["root_preimage_shapes"]
    assert roots["api"] == shapes["api_root_preimage"]["fields"]
    assert roots["manifest"] == shapes["manifest_root_preimage"]["fields"]
    assert roots["readiness"] == shapes["readiness_root_preimage"]["fields"]


def test_exact_selected_layout_aggregates_roots_and_record_joins(built) -> None:
    files, report = built
    assert len(files) == TREE_FILE_COUNT
    assert sum(path.endswith(".html") for path in files) == HTML_PAGE_COUNT
    assert sum(path.startswith("explicit/") for path in files) == THEOREM_COUNT
    assert sum(path.startswith("defined/") for path in files) == THEOREM_COUNT
    assert sum(path.startswith("definition/") for path in files) == DEFINITION_COUNT
    assert set(files) >= {
        "api/deployment.json",
        "assets/pages.css",
        "index.html",
        "manifest.json",
        "schema.json",
    }
    assert all("\\" not in path and ".." not in PurePosixPath(path).parts for path in files)
    assert len({path.casefold() for path in files}) == len(files)

    api = json.loads(files["api/deployment.json"])
    manifest = json.loads(files["manifest.json"])
    for document in (api, manifest, report):
        assert document["status"] == "candidate"
        assert document["logic_mode"] == "intuitionistic"
        assert document["deployed"] is False
        for field in (
            "freeze_ready",
            "training_eligible",
            "retrieval_eligible",
            "evaluation_eligible",
        ):
            assert document[field] is False
        assert document["root_sha256"] == _sha(_compact(document["root_preimage"]))
    assert report["deployment_observed"] is False
    assert len(api["theorems"]) == THEOREM_COUNT
    assert len(api["definitions"]) == DEFINITION_COUNT
    assert api["aggregate"] == {
        "declared_dependency_edges": 1_038,
        "defined_page_count": 384,
        "definition_conceptual_edges": 58,
        "definition_count": 40,
        "definition_occurrences": 2_027,
        "definition_page_count": 40,
        "definition_use_relationships": 755,
        "explicit_page_count": 384,
        "html_page_count": 809,
        "index_page_count": 1,
        "tactic_line_count": 13_862,
        "theorem_count": 384,
    }
    assert [row["index"] for row in api["theorems"]] == list(range(384))
    assert [row["index"] for row in api["definitions"]] == list(range(40))
    for row in api["theorems"]:
        body = {key: value for key, value in row.items() if key != "record_sha256"}
        assert row["record_sha256"] == _sha(_compact(body))
        for side in ("explicit_page", "defined_page"):
            receipt = row[side]
            assert receipt["bytes"] == len(files[receipt["path"]])
            assert receipt["sha256"] == _sha(files[receipt["path"]])
    for row in api["definitions"]:
        body = {key: value for key, value in row.items() if key != "record_sha256"}
        assert row["record_sha256"] == _sha(_compact(body))
    assert manifest["aggregate"]["content_file_count"] == CONTENT_FILE_COUNT
    assert manifest["aggregate"]["tree_file_count"] == TREE_FILE_COUNT
    assert len(manifest["content_files"]) == CONTENT_FILE_COUNT
    assert [row["path"] for row in manifest["content_files"]] == sorted(
        path for path in files if path != "manifest.json"
    )
    assert report["aggregate"]["selected_generated_page_pair_complete_count"] == 384
    assert report["aggregate"]["selected_generated_definition_use_receipt_complete_count"] == 384


def test_all_pages_are_static_escaped_and_have_resolving_local_links(built) -> None:
    files, _report = built
    pages = {path: raw for path, raw in files.items() if path.endswith(".html")}
    assert len(pages) == HTML_PAGE_COUNT
    definition_token_links = 0
    for path, raw in pages.items():
        source = raw.decode("utf-8")
        assert source.startswith("<!doctype html>\n")
        assert source.count('class="pa-selected-library"') == 1
        assert "candidate display only" in source
        assert not PA_GLOBAL_KEY.search(source)
        assert "<script" not in source.lower()
        parser = _Links()
        parser.feed(source)
        for tag, attrs in parser.tags:
            assert not tag.startswith(("iframe", "object", "embed", "base"))
            assert not any(key.lower().startswith("on") for key in attrs)
        definition_token_links += source.count('class="pl-definition"')
        origin = PurePosixPath(path).parent
        for _attribute, target in parser.links:
            parsed = urlsplit(target)
            assert not parsed.scheme and not parsed.netloc
            assert parsed.scheme.lower() not in {"data", "javascript", "vbscript"}
            resolved = (origin / parsed.path)
            normalized = PurePosixPath(os.path.normpath(resolved.as_posix()))
            assert ".." not in normalized.parts
            assert normalized.as_posix() in files
    # 2,027 rendered conservative-notation occurrences plus one summary link
    # for each of the 755 theorem/definition relationships.
    assert definition_token_links == 2_027 + 755
    css = files["assets/pages.css"].decode("utf-8")
    assert "http://" not in css and "https://" not in css and ":root" not in css
    for block in css.split("}"):
        header = block.rsplit("{", 1)[0].strip()
        if header and not header.startswith("@"):
            assert all(
                selector.strip().startswith("body.pa-selected-library")
                for selector in header.split(",")
            )


def test_api_has_no_wider_corpus_navigation_fields_or_global_keys(built) -> None:
    files, _report = built
    api_raw = files["api/deployment.json"]
    api = json.loads(api_raw)
    forbidden = {"closure", "dependents", "href", "scope", "tag"}
    for row in api["theorems"]:
        assert forbidden.isdisjoint(row)
    assert not PA_GLOBAL_KEY.search(api_raw.decode("utf-8"))
    source = (ROOT / "training/peano_hydra/library_page_deployment.py").read_text()
    assert "quadratic_reciprocity_stack" not in source
    assert "defined_library_edition" not in source
    assert "build_defined_edition" not in source


def test_mutation_and_authority_flip_fail_exact_reconstruction(built) -> None:
    files, _report = built
    corrupted = dict(files)
    api = json.loads(corrupted["api/deployment.json"])
    api["deployed"] = True
    api["root_preimage"]["deployed"] = True
    api["root_sha256"] = _sha(_compact(api["root_preimage"]))
    corrupted["api/deployment.json"] = canonical_document_bytes(api)
    with pytest.raises(LibraryPageDeploymentError, match="differs"):
        validate_library_page_deployment(corrupted, repository_root=ROOT)


def test_retained_tree_and_external_readiness_match_exact_build(built) -> None:
    files, report = built
    assert OUTPUT.is_dir()
    assert REPORT.is_file()
    loaded = load_library_page_deployment(OUTPUT, repository_root=ROOT)
    assert loaded == files
    assert REPORT.read_bytes() == canonical_document_bytes(report)
    pinned = {
        "schema": SCHEMA_SOURCE.read_bytes(),
        "api": files["api/deployment.json"],
        "manifest": files["manifest.json"],
        "readiness": REPORT.read_bytes(),
    }
    for name, raw in pinned.items():
        assert (len(raw), _sha(raw)) == FINAL_PINS[name]
    api = json.loads(files["api/deployment.json"])
    manifest = json.loads(files["manifest.json"])
    assert api["root_sha256"] == FINAL_ROOTS["api"]
    assert api["root_preimage"]["theorem_record_root_sha256"] == FINAL_ROOTS["theorem_records"]
    assert api["root_preimage"]["definition_record_root_sha256"] == FINAL_ROOTS["definition_records"]
    assert manifest["root_sha256"] == FINAL_ROOTS["manifest"]
    assert manifest["root_preimage"]["file_receipt_root_sha256"] == FINAL_ROOTS["files"]
    assert report["root_sha256"] == FINAL_ROOTS["readiness"]


def test_cli_default_is_no_write_and_retained_check_is_read_only() -> None:
    before = {
        path: (path.stat().st_mtime_ns, _sha(path.read_bytes()))
        for path in (OUTPUT / "manifest.json", REPORT)
    }
    default = subprocess.run(
        [sys.executable, str(CLI)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert default.returncode == 0, default.stdout + default.stderr
    checked = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--output-dir",
            str(OUTPUT),
            "--report",
            str(REPORT),
            "--check",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=45,
        check=False,
    )
    assert checked.returncode == 0, checked.stdout + checked.stderr
    after = {
        path: (path.stat().st_mtime_ns, _sha(path.read_bytes()))
        for path in before
    }
    assert after == before


def test_cli_publication_is_create_only_and_preserves_existing_destinations(
    tmp_path: Path, built
) -> None:
    files, report = built
    output = tmp_path / "pages"
    receipt = tmp_path / "readiness.json"
    page_module_files = files
    from importlib.util import module_from_spec, spec_from_file_location

    spec = spec_from_file_location("_test_page_cli", CLI)
    assert spec is not None and spec.loader is not None
    cli = module_from_spec(spec)
    spec.loader.exec_module(cli)
    cli._publish(output, receipt, page_module_files, report)
    assert load_library_page_deployment(output, repository_root=ROOT) == files
    sentinel = receipt.read_bytes()
    with pytest.raises(LibraryPageDeploymentError, match="already exists"):
        cli._publish(output, receipt, page_module_files, report)
    assert receipt.read_bytes() == sentinel


def test_public_serializer_rejects_floats_huge_integers_and_cycles() -> None:
    with pytest.raises(LibraryPageDeploymentError):
        canonical_document_bytes({"bad": 0.5})
    with pytest.raises(LibraryPageDeploymentError, match="safe domain"):
        canonical_document_bytes({"bad": 9_007_199_254_740_992})
    cyclic: list[object] = []
    cyclic.append(cyclic)
    with pytest.raises(LibraryPageDeploymentError, match="cyclic"):
        canonical_document_bytes(cyclic)


def test_loader_rejects_symlinks_special_files_and_import_origin_poisoning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = tmp_path / "real"
    real.mkdir()
    (real / "child").mkdir()
    ancestor = tmp_path / "ancestor"
    ancestor.symlink_to(real, target_is_directory=True)
    with pytest.raises(LibraryPageDeploymentError, match="symlink components"):
        page_module._safe_external_directory(ancestor / "child")
    with pytest.raises(LibraryPageDeploymentError, match="symlink components"):
        page_module._repository_root(ancestor / "child")

    hostile = tmp_path / "hostile"
    hostile.mkdir()
    (hostile / "link").symlink_to(real, target_is_directory=True)
    with pytest.raises(LibraryPageDeploymentError, match="symlink"):
        page_module._directory_members(hostile)
    (hostile / "link").unlink()
    fifo = hostile / "pipe"
    os.mkfifo(fifo)
    with pytest.raises(LibraryPageDeploymentError, match="nonregular"):
        page_module._directory_members(hostile)
    with pytest.raises(LibraryPageDeploymentError, match="regular file"):
        page_module._read_bounded_regular_file(
            fifo, label="hostile FIFO", limit=128
        )

    fake_path = tmp_path / "fake.py"
    fake_path.write_text("# poisoned import\n", encoding="utf-8")
    fake = SimpleNamespace(__file__=str(fake_path))
    monkeypatch.setattr(page_module.importlib, "import_module", lambda _name: fake)
    with pytest.raises(LibraryPageDeploymentError, match="origin drifted"):
        page_module._documentation_bundle_module(ROOT)


def test_historical_surfaces_and_metadata_remain_exact() -> None:
    for relative, expected in HISTORICAL_PINS.items():
        assert _sha((ROOT / relative).read_bytes()) == expected
