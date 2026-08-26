"""Public Lean controls enhance staged theorem pages without altering evidence."""

from __future__ import annotations

from hashlib import sha256
import importlib.util
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts" / "stage_public_lean_selector.py"
SELECTOR = ROOT / "book" / "_static" / "lean-selector"


@pytest.fixture(scope="module")
def public_selector() -> ModuleType:
    specification = importlib.util.spec_from_file_location("hydra_public_selector_stage", SCRIPT)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


@pytest.fixture
def proof_stage(tmp_path: Path) -> Path:
    root = tmp_path / "proofs"
    (root / "assets").mkdir(parents=True)
    for relative, marker in (
        ("quadratic-reciprocity/explorer/graph.html", "pa-graph-details"),
        ("quadratic-reciprocity/explorer/tag/PA000F.html", "pa-proof-sidebar"),
        ("quadratic-reciprocity/explorer/defined/graph.html", "pd-graph-details"),
        ("quadratic-reciprocity/explorer/defined/tag/PA000F.html", "pd-theorem-layout"),
        ("new-alpha-v24-family/explorer/defined/graph.html", "data-graph-title"),
        ("new-alpha-v24-family/explorer/defined/tag/V240001.html", "data-lean-selector-host"),
        ("quadratic-reciprocity/explorer/defined/definition/PD0001.html", "pd-theorem-layout"),
        ("quadratic-reciprocity/index.html", "pa-graph-details"),
        ("grand-campaign/index.html", "pa-graph-details"),
    ):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            '<!doctype html><html><head><title>Checked proof</title></head>'
            f'<body><aside class="{marker}">Exact checked evidence</aside></body></html>\n',
            encoding="utf-8",
        )
    return root


def test_stage_enhances_every_graph_and_checked_theorem_across_future_families(
    public_selector: ModuleType,
    proof_stage: Path,
) -> None:
    result = public_selector.stage_public_lean_selector(proof_stage)

    assert result.candidates == 6
    assert result.injected == 6
    assert result.assets == 2
    for family, relative in (
        ("quadratic-reciprocity", "explorer/graph.html"),
        ("quadratic-reciprocity", "explorer/tag/PA000F.html"),
        ("quadratic-reciprocity", "explorer/defined/graph.html"),
        ("quadratic-reciprocity", "explorer/defined/tag/PA000F.html"),
        ("new-alpha-v24-family", "explorer/defined/graph.html"),
        ("new-alpha-v24-family", "explorer/defined/tag/V240001.html"),
    ):
        source = (proof_stage / family / relative).read_text(encoding="utf-8")
        assert 'href="/proofs/assets/lean-selector.css"' in source
        assert 'src="/proofs/assets/lean-selector.js"' in source
        assert source.index("lean-selector.js") < source.index("</head>")
        assert "Exact checked evidence" in source


def test_stage_does_not_modify_family_landings_campaigns_or_definitions(
    public_selector: ModuleType,
    proof_stage: Path,
) -> None:
    excluded = (
        proof_stage / "quadratic-reciprocity" / "index.html",
        proof_stage / "grand-campaign" / "index.html",
        proof_stage / "quadratic-reciprocity" / "explorer" / "defined" / "definition" / "PD0001.html",
    )
    before = {path: path.read_bytes() for path in excluded}

    public_selector.stage_public_lean_selector(proof_stage)

    assert all(path.read_bytes() == expected for path, expected in before.items())


def test_public_assets_are_byte_identical_to_the_reviewed_shared_selector(
    public_selector: ModuleType,
    proof_stage: Path,
) -> None:
    public_selector.stage_public_lean_selector(proof_stage)

    for filename in ("lean-selector.js", "lean-selector.css"):
        assert (proof_stage / "assets" / filename).read_bytes() == (
            SELECTOR / filename
        ).read_bytes()


def test_public_selector_staging_is_idempotent_and_has_a_read_only_check(
    public_selector: ModuleType,
    proof_stage: Path,
) -> None:
    initial = public_selector.stage_public_lean_selector(proof_stage)
    target = proof_stage / "quadratic-reciprocity" / "explorer" / "graph.html"
    digest = sha256(target.read_bytes()).hexdigest()
    repeated = public_selector.stage_public_lean_selector(proof_stage)
    checked = public_selector.stage_public_lean_selector(proof_stage, check=True)

    assert initial.injected == 6
    assert repeated.injected == 0
    assert repeated.unchanged == 6
    assert checked.unchanged == 6
    assert sha256(target.read_bytes()).hexdigest() == digest


def test_default_public_selector_preserves_its_same_origin_faculty_gateway(
    public_selector: ModuleType,
    proof_stage: Path,
) -> None:
    public_selector.stage_public_lean_selector(proof_stage, api_url="")
    graph = (proof_stage / "quadratic-reciprocity" / "explorer" / "graph.html").read_text(
        encoding="utf-8"
    )

    assert "peano-lean-strand-api" not in graph


def test_explicit_https_backend_is_escaped_into_the_public_graph_metadata(
    public_selector: ModuleType,
    proof_stage: Path,
) -> None:
    public_selector.stage_public_lean_selector(
        proof_stage,
        api_url="https://lean.example.org/api/lean-strands",
    )
    graph = (proof_stage / "quadratic-reciprocity" / "explorer" / "graph.html").read_text(
        encoding="utf-8"
    )

    assert (
        '<meta name="peano-lean-strand-api" '
        'content="https://lean.example.org/api/lean-strands">'
    ) in graph


@pytest.mark.parametrize(
    "address",
    (
        "http://lean.example.org/api/lean-strands",
        "https://localhost/api/lean-strands",
        "https://127.0.0.1/api/lean-strands",
        "https://192.168.1.4/api/lean-strands",
        "https://user:password@lean.example.org/api/lean-strands",
        "https://lean.example.org/api/lean-strands?token=secret",
        "https://lean.example.org/api/lean-strands#unsafe",
        "https://lean.example.org/other-service",
    ),
)
def test_unsafe_external_backends_are_rejected(
    public_selector: ModuleType,
    proof_stage: Path,
    address: str,
) -> None:
    with pytest.raises(public_selector.PublicSelectorError):
        public_selector.stage_public_lean_selector(proof_stage, api_url=address)


def test_check_mode_rejects_missing_staged_selector_assets(
    public_selector: ModuleType,
    proof_stage: Path,
) -> None:
    with pytest.raises(public_selector.PublicSelectorError, match="asset is stale"):
        public_selector.stage_public_lean_selector(proof_stage, check=True)


def test_makefile_cli_contract_is_supported_without_modifying_source_snapshots(
    proof_stage: Path,
) -> None:
    original = SELECTOR / "lean-selector.js"
    digest = sha256(original.read_bytes()).hexdigest()
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--root", str(proof_stage), "--api-url", ""],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stderr
    assert "6 public theorem graph/detail pages" in result.stdout
    assert sha256(original.read_bytes()).hexdigest() == digest
