"""On-demand named Lean proof strands preserve release and resource boundaries."""

from __future__ import annotations

from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "scripts" / "export_peano_lean.py"
LEAN_PROJECT = ROOT.parent / "peano-lab-lean"


def _run(*arguments: object, timeout: int = 35) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(
        [sys.executable, "-B", str(CLI), *(str(argument) for argument in arguments)],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


@pytest.fixture(scope="module")
def exporter():
    specification = importlib.util.spec_from_file_location("peano_lean_strand_cli", CLI)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def _catalog(directory: Path) -> dict[str, object]:
    return json.loads((directory / "manifest.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("style", ("outline", "strand"))
def test_parser_recognizes_on_demand_proof_styles(exporter, style: str) -> None:
    assert exporter._parser().parse_args(["zero_add", "--format", style]).format == style


def test_campaign_live_cli_defaults_and_hard_url_bound(
    exporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    options = exporter._parser().parse_args(["zero_add", "--format", "outline"])
    assert options.max_live_url_bytes == 512 * 1024
    assert options.max_live_source_kib == 1024
    assert exporter.main(
        ["zero_add", "--format", "outline", "--max-live-url-bytes", "1048577"]
    ) == 1
    assert "between 128 and 1048576" in capsys.readouterr().err


def test_campaign_progress_keeps_large_authenticated_share_out_of_event_lines(
    exporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    options = exporter._parser().parse_args(
        ["zero_add", "--format", "strand", "--progress-json"]
    )
    url = "https://live.lean-lang.org/#codez=" + "A" * (33 * 1024)
    exporter._emit_cli_progress(
        options,
        stage="complete",
        completed=557,
        total=557,
        theorem="zero_add",
        live_url=url,
        live_status="ready",
    )

    event_line = capsys.readouterr().err.strip()
    assert len(event_line.encode("utf-8")) < 16 * 1024
    event = json.loads(event_line)
    assert event["live_status"] == "ready"
    assert event["live_url"] is None
    assert event["live_url_omitted"] is True
    assert event["live_url_bytes"] == len(url.encode("utf-8"))
    assert event["live_url_sha256"] == sha256(url.encode("utf-8")).hexdigest()


def test_outline_never_replays_a_closed_stable_or_alpha_proof(
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from peano_lab.library import editions_v19

    def forbidden(*_arguments: object, **_options: object) -> None:
        raise AssertionError("a metadata-only strand requested a closed theorem certificate")

    monkeypatch.setattr(exporter, "replay", forbidden)
    monkeypatch.setattr(editions_v19, "replay", forbidden)

    assert exporter.main(["add_comm", "--format", "outline"]) == 0
    captured = capsys.readouterr()
    assert "add_comm" in captured.out
    assert "zero_add" in captured.out
    assert "no fresh Peano proof replay" in captured.err


def test_alpha_outline_preserves_exact_release_membership(
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from peano_lab.library import editions_v19

    monkeypatch.setattr(
        editions_v19,
        "replay",
        lambda *_args, **_kwargs: pytest.fail("an outline replayed an Alpha proof"),
    )

    assert exporter.main(["zero_add", "--edition", "alpha", "--format", "outline"]) == 0
    captured = capsys.readouterr()
    assert "zero_add" in captured.out
    assert "alpha" in captured.out.lower()


@pytest.mark.parametrize(
    ("arguments", "message"),
    (
        (("--verify",), "cannot claim Lean verification"),
        (("--package-dir", "unused"), "does not generate a Lean package"),
        (("--strict-readable",), "requires generating a proof strand"),
    ),
)
def test_outline_rejects_misleading_execution_options(
    arguments: tuple[str, ...],
    message: str,
) -> None:
    result = _run("zero_add", "--format", "outline", *arguments)

    assert result.returncode == 1
    assert message in result.stderr


@pytest.mark.parametrize("style", ("outline", "strand"))
def test_proof_strands_reject_external_bundles(style: str, tmp_path: Path) -> None:
    result = _run(
        "zero_add",
        "--format",
        style,
        "--proof-bundle",
        tmp_path / "untrusted.json",
    )

    assert result.returncode == 1
    assert "not externally supplied proof bundles" in result.stderr


@pytest.mark.parametrize(
    ("option", "value", "message"),
    (
        ("--max-strand-nodes", "0", "node bound"),
        ("--max-strand-nodes", "4097", "node bound"),
        ("--max-strand-edges", "-1", "edge bound"),
        ("--max-strand-edges", "65537", "edge bound"),
        ("--max-strand-depth", "0", "depth bound"),
        ("--max-strand-depth", "257", "depth bound"),
        ("--max-proof-steps", "0", "proof-step bound"),
        ("--max-proof-steps", "65537", "proof-step bound"),
        ("--max-proof-repairs", "-1", "repair bound"),
        ("--max-proof-repairs", "257", "repair bound"),
        ("--max-chunk-kib", "7", "chunk bound"),
        ("--max-chunk-kib", "65537", "chunk bound"),
    ),
)
def test_strand_enforces_hard_resource_boundaries(
    option: str,
    value: str,
    message: str,
) -> None:
    result = _run("zero_add", "--format", "outline", option, value)

    assert result.returncode == 1
    assert message in result.stderr


def test_dependency_limit_stops_before_recursive_certificate_replay(
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        exporter,
        "replay",
        lambda *_args, **_kwargs: pytest.fail("a bounded strand replayed its root"),
    )

    assert (
        exporter.main(["add_comm", "--format", "outline", "--max-strand-nodes", "2"])
        == 1
    )
    assert "limit" in capsys.readouterr().err.lower()


@pytest.mark.parametrize(
    "name",
    (
        "cell_list_valid_nil",
        "doubled_square_plus_one_nonzero",
        "infinitely_many_primes_one_mod_four",
    ),
)
def test_historical_alpha_theorems_have_replay_free_current_v25_strands(
    name: str,
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from peano_lab.library import editions_v19, editions_v23, editions_v24, editions_v25

    monkeypatch.setattr(
        editions_v19,
        "replay",
        lambda *_args, **_kwargs: pytest.fail("a current Alpha outline replayed its proof"),
    )
    monkeypatch.setattr(
        editions_v19,
        "_checked_campaign_bundle",
        lambda *_args, **_kwargs: pytest.fail("a current Alpha outline loaded a proof bundle"),
    )
    monkeypatch.setattr(
        editions_v23,
        "replay",
        lambda *_args, **_kwargs: pytest.fail("an Alpha-v23 outline replayed its proof"),
    )
    monkeypatch.setattr(
        editions_v23,
        "checked_milestone_closure_bundle",
        lambda *_args, **_kwargs: pytest.fail("an Alpha-v23 outline loaded a proof bundle"),
    )
    monkeypatch.setattr(
        editions_v24,
        "replay",
        lambda *_args, **_kwargs: pytest.fail("an Alpha-v24 outline replayed its proof"),
    )
    monkeypatch.setattr(
        editions_v24,
        "checked_research_layer_bundle",
        lambda *_args, **_kwargs: pytest.fail("an Alpha-v24 outline loaded a proof bundle"),
    )
    monkeypatch.setattr(
        editions_v25,
        "replay",
        lambda *_args, **_kwargs: pytest.fail("an Alpha-v25 outline replayed its proof"),
    )
    monkeypatch.setattr(
        editions_v25,
        "checked_breakthrough_layer_bundle",
        lambda *_args, **_kwargs: pytest.fail("an Alpha-v25 outline loaded a proof bundle"),
    )

    assert exporter.main([name, "--edition", "alpha", "--format", "outline"]) == 0
    captured = capsys.readouterr()
    assert name in captured.out
    assert "v25" in captured.out
    assert "no fresh Peano proof replay" in captured.err


@pytest.mark.parametrize(
    "name",
    (
        "beta_signed_matrix_minor_exists",
        "beta_horner_derivative_exists_unique",
        "crt_pairwise_coprime_prefix_canonical_exists_unique",
        "signed_matrix_cofactor_family_and_fold_exists",
        "beta_horner_hensel_lift_exists",
        "crt_merge_compatible_prefix_canonical_exists_unique",
    ),
)
def test_current_v25_frontier_outline_never_loads_actual_proof_artifacts(
    name: str,
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from peano_lab.library import editions_v25

    def forbidden(*_args: object, **_kwargs: object) -> None:
        pytest.fail("an Alpha-v25 metadata-only outline loaded an actual proof")

    monkeypatch.setattr(editions_v25, "replay", forbidden)
    monkeypatch.setattr(editions_v25, "_checked_breakthrough_layer_bundle", forbidden)

    assert exporter.main([name, "--edition", "alpha", "--format", "outline"]) == 0
    captured = capsys.readouterr()
    assert name in captured.out
    assert "v25" in captured.out
    assert "no fresh Peano proof replay" in captured.err


def test_current_v25_full_export_rejects_unavailable_actual_breakthrough_proof(
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from peano_lab.library import editions_v25

    def unavailable() -> None:
        raise editions_v25.EditionV25ReplayError(
            "actual Alpha-v25 proof bytes are unavailable"
        )

    editions_v25.replay.cache_clear()
    monkeypatch.setattr(editions_v25, "_checked_breakthrough_layer_bundle", unavailable)

    assert (
        exporter.main(
            ["crt_mod_one_universal", "--edition", "alpha", "--format", "full"]
        )
        == 1
    )
    captured = capsys.readouterr()
    assert "actual Alpha-v25 proof bytes are unavailable" in captured.err
    assert "theorem «crt_mod_one_universal»" not in captured.out


def test_unknown_theorem_is_never_rebranded_as_a_checked_strand() -> None:
    result = _run("not_a_checked_theorem", "--format", "strand")

    assert result.returncode == 2
    assert "Unknown public Peano theorem" in result.stderr


def test_complete_named_strand_has_two_content_bound_modules(
    tmp_path: Path,
) -> None:
    package = tmp_path / "strand"
    result = _run("add_comm", "--format", "strand", "--package-dir", package)

    assert result.returncode == 0, result.stderr
    assert "add_comm" in result.stdout
    catalog = _catalog(package)
    assert catalog["schema"] == "peano-lean-proof-strand-package-v1"
    assert catalog["notation_module"] == "PeanoLab.Presentation"
    assert catalog["strand_count"] == 1
    token, manifest = next(iter(catalog["strands"].items()))
    assert manifest["name"] == "add_comm"
    assert manifest["edition"] == "stable"
    assert manifest["node_count"] == 3
    assert manifest["authority"]["lean_compiler_verified"] is False
    assert manifest["translated_node_count"] + manifest["fallback_node_count"] == 3
    assert [entry["name"] for entry in manifest["nodes"]] == [
        "zero_add",
        "add_succ_left",
        "add_comm",
    ]
    assert json.loads(
        (package / "strand-manifests" / f"{token}.json").read_text(encoding="utf-8")
    ) == manifest
    assert len(manifest["files"]) == 2
    for entry in manifest["files"]:
        payload = (package / entry["relative_path"]).read_bytes()
        assert len(payload) == entry["bytes"]
        assert sha256(payload).hexdigest() == entry["sha256"]


def test_two_independent_strands_share_an_additive_audited_catalog(
    tmp_path: Path,
) -> None:
    package = tmp_path / "many"
    first = _run("zero_add", "--format", "strand", "--package-dir", package)
    assert first.returncode == 0, first.stderr
    notation = (package / "PeanoLab" / "Presentation.lean").read_bytes()
    second = _run("add_comm", "--format", "strand", "--package-dir", package)

    assert second.returncode == 0, second.stderr
    catalog = _catalog(package)
    assert catalog["strand_count"] == 2
    assert {row["name"] for row in catalog["strands"].values()} == {
        "zero_add",
        "add_comm",
    }
    assert (package / "PeanoLab" / "Presentation.lean").read_bytes() == notation


def test_complete_strand_splits_into_contiguous_content_bound_modules(
    tmp_path: Path,
) -> None:
    package = tmp_path / "chunks"
    result = _run(
        "add_comm",
        "--format",
        "strand",
        "--package-dir",
        package,
        "--max-chunk-kib",
        "13",
    )

    assert result.returncode == 0, result.stderr
    manifest = next(iter(_catalog(package)["strands"].values()))
    assert manifest["chunk_count"] >= 2
    assert len(manifest["files"]) == manifest["chunk_count"] + 2
    chunks = manifest["files"][1:-1]
    assert [row["module"].rsplit(".", 1)[-1] for row in chunks] == [
        f"C{index:03d}" for index in range(len(chunks))
    ]
    assert all(row["bytes"] <= 13 * 1024 for row in chunks)
    assert manifest["files"][-1]["module"].endswith(".Strand")
    assert all(
        node["generated_relative_path"] in {entry["relative_path"] for entry in chunks}
        for node in manifest["nodes"]
    )


def test_chunked_strand_cannot_emit_an_unusable_standalone_import() -> None:
    result = _run("add_comm", "--format", "strand", "--max-chunk-kib", "13")

    assert result.returncode == 1
    assert "segmented proof strand requires --package-dir" in result.stderr


def test_modified_existing_chunk_fails_closed_before_catalog_extension(
    tmp_path: Path,
) -> None:
    package = tmp_path / "tampered-chunk"
    initial = _run(
        "add_comm",
        "--format",
        "strand",
        "--package-dir",
        package,
        "--max-chunk-kib",
        "13",
    )
    assert initial.returncode == 0, initial.stderr
    chunk = next((package / "PeanoLab" / "Generated").glob("*/Chunks/C000.lean"))
    chunk.write_text("-- modified theorem dependency\n", encoding="utf-8")

    result = _run("zero_add", "--format", "strand", "--package-dir", package)

    assert result.returncode == 1
    assert "altered" in result.stderr


def test_reexporting_identical_strand_is_deterministic_and_idempotent(
    tmp_path: Path,
) -> None:
    package = tmp_path / "repeat"
    assert _run("zero_add", "--format", "strand", "--package-dir", package).returncode == 0
    manifest = (package / "manifest.json").read_bytes()

    repeated = _run("zero_add", "--format", "strand", "--package-dir", package)

    assert repeated.returncode == 0, repeated.stderr
    assert (package / "manifest.json").read_bytes() == manifest


def test_stable_and_alpha_strands_have_separate_content_bound_modules(
    tmp_path: Path,
) -> None:
    package = tmp_path / "editions"
    stable = _run("zero_add", "--format", "strand", "--package-dir", package)
    alpha = _run(
        "zero_add",
        "--edition",
        "alpha",
        "--format",
        "strand",
        "--package-dir",
        package,
    )

    assert stable.returncode == alpha.returncode == 0
    catalog = _catalog(package)
    assert catalog["strand_count"] == 2
    assert {item["edition"] for item in catalog["strands"].values()} == {
        "stable",
        "alpha",
    }


def test_modified_existing_strand_source_is_rejected(tmp_path: Path) -> None:
    package = tmp_path / "tampered-source"
    assert _run("zero_add", "--format", "strand", "--package-dir", package).returncode == 0
    module = next((package / "PeanoLab" / "Generated").glob("*/Strand.lean"))
    module.write_text("-- modified proof\n", encoding="utf-8")

    result = _run("add_comm", "--format", "strand", "--package-dir", package)

    assert result.returncode == 1
    assert "altered" in result.stderr
    assert module.read_text(encoding="utf-8") == "-- modified proof\n"


def test_modified_existing_strand_manifest_is_rejected(tmp_path: Path) -> None:
    package = tmp_path / "tampered-manifest"
    assert _run("zero_add", "--format", "strand", "--package-dir", package).returncode == 0
    individual = next((package / "strand-manifests").glob("*.json"))
    individual.write_text("{}\n", encoding="utf-8")

    result = _run("add_comm", "--format", "strand", "--package-dir", package)

    assert result.returncode == 1
    assert "altered" in result.stderr


@pytest.mark.parametrize(
    "authority",
    ("public_admission", "publication", "training", "final_evaluation"),
)
def test_consistently_rewritten_manifest_cannot_grant_false_authority(
    authority: str,
    tmp_path: Path,
    exporter,
) -> None:
    package = tmp_path / "false-authority"
    first = _run("zero_add", "--format", "strand", "--package-dir", package)
    assert first.returncode == 0, first.stderr
    catalog = _catalog(package)
    token, individual = next(iter(catalog["strands"].items()))
    individual["authority"][authority] = True
    (package / "strand-manifests" / f"{token}.json").write_text(
        exporter._canonical_manifest(individual),
        encoding="utf-8",
    )
    (package / "manifest.json").write_text(
        exporter._canonical_manifest(catalog),
        encoding="utf-8",
    )

    result = _run("add_comm", "--format", "strand", "--package-dir", package)

    assert result.returncode == 1
    assert "invalid identity" in result.stderr


def test_noncanonical_strand_catalog_is_rejected(tmp_path: Path) -> None:
    package = tmp_path / "tampered-catalog"
    assert _run("zero_add", "--format", "strand", "--package-dir", package).returncode == 0
    manifest = package / "manifest.json"
    manifest.write_text(manifest.read_text(encoding="utf-8") + " ", encoding="utf-8")

    result = _run("add_comm", "--format", "strand", "--package-dir", package)

    assert result.returncode == 1
    assert "canonical proof-strand catalog" in result.stderr


@pytest.mark.parametrize("field", ("root", "source", "evidence"))
def test_synchronized_manifest_cannot_forge_exact_release_provenance(
    field: str,
    tmp_path: Path,
    exporter,
) -> None:
    package = tmp_path / "false-provenance"
    assert _run("zero_add", "--format", "strand", "--package-dir", package).returncode == 0
    catalog = _catalog(package)
    token, individual = next(iter(catalog["strands"].items()))
    if field == "root":
        individual["name"] = "invented_theorem"
    elif field == "source":
        individual["nodes"][0]["source_sha256"] = "0" * 64
    else:
        individual["nodes"][0]["evidence"] = "alpha_closed"
    (package / "strand-manifests" / f"{token}.json").write_text(
        exporter._canonical_manifest(individual),
        encoding="utf-8",
    )
    (package / "manifest.json").write_text(
        exporter._canonical_manifest(catalog),
        encoding="utf-8",
    )

    result = _run("add_comm", "--format", "strand", "--package-dir", package)

    assert result.returncode == 1
    assert any(
        marker in result.stderr
        for marker in ("altered", "invalid theorem provenance", "inconsistent root")
    )


def test_presentation_catalog_cannot_be_overwritten_by_a_strand(tmp_path: Path) -> None:
    package = tmp_path / "different-kind"
    existing = _run("zero_add", "--format", "compact", "--package-dir", package)
    assert existing.returncode == 0, existing.stderr
    original = (package / "manifest.json").read_bytes()

    result = _run("add_comm", "--format", "strand", "--package-dir", package)

    assert result.returncode == 1
    assert "choose a separate directory" in result.stderr
    assert (package / "manifest.json").read_bytes() == original


def test_proof_strand_rejects_symlinked_package_root(tmp_path: Path) -> None:
    actual = tmp_path / "real"
    actual.mkdir()
    link = tmp_path / "symlink"
    link.symlink_to(actual, target_is_directory=True)

    result = _run("zero_add", "--format", "strand", "--package-dir", link)

    assert result.returncode == 1
    assert "must not be a symlink" in result.stderr
    assert list(actual.iterdir()) == []


def test_selected_output_cannot_overwrite_its_own_package_module(tmp_path: Path) -> None:
    package = tmp_path / "self"
    result = _run(
        "zero_add",
        "--format",
        "strand",
        "--package-dir",
        package,
        "--output",
        package / "selected.lean",
    )

    assert result.returncode == 1
    assert "must not be inside its Lean package" in result.stderr
    assert not package.exists()


def test_oversized_terminal_strand_requires_explicit_file_destination(
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(exporter, "MAX_STRAND_TERMINAL_BYTES", 1)

    assert exporter.main(["zero_add", "--format", "strand"]) == 1
    assert "safe terminal-output budget" in capsys.readouterr().err


def test_strict_readability_does_not_apply_to_other_export_modes() -> None:
    result = _run("zero_add", "--format", "pretty", "--strict-readable")

    assert result.returncode == 1
    assert "only for proof strands" in result.stderr


def test_real_lean_error_repairs_exactly_one_named_local_theorem(
    tmp_path: Path,
    exporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from peano_lab.library.lean_proof_strand import build_proof_strand, plan_proof_strand

    plan = plan_proof_strand("add_comm")
    package = build_proof_strand(plan)
    root = exporter._write_strand_package(package, tmp_path / "repair", force=False)
    args = exporter._parser().parse_args(["add_comm", "--format", "strand"])
    monkeypatch.setattr(exporter, "_lake_binary", lambda *_arguments: tmp_path / "lake")
    calls: list[dict[str, object]] = []

    def fake_verifier(candidate: object, *_arguments: object, **_options: object) -> None:
        calls.append(candidate.manifest)
        if len(calls) == 1:
            first = candidate.manifest["nodes"][0]
            source = root / candidate.relative_path
            raise exporter.LeanVerificationError(
                "Lean rejected the generated theorem",
                f"{source}:{first['source_line_start']}:3: error: unsupported tactic\n",
            )

    monkeypatch.setattr(exporter, "_verify_presentation_package", fake_verifier)

    repaired = exporter._verify_strand_package(plan, package, root, args)

    assert len(calls) == 2
    assert repaired.manifest["fallback_node_count"] == 1
    assert repaired.manifest["translated_node_count"] == 2
    assert repaired.manifest["nodes"][0]["name"] == "zero_add"
    assert repaired.manifest["nodes"][0]["proof_status"] == "local_checked_certificate"
    assert next(iter(_catalog(root)["strands"].values())) == repaired.manifest


def test_real_lean_error_in_a_chunk_maps_to_its_exact_named_theorem(
    tmp_path: Path,
    exporter,
) -> None:
    from peano_lab.library.lean_proof_strand import build_proof_strand, plan_proof_strand

    package = build_proof_strand(plan_proof_strand("add_comm"), chunk_max_bytes=13 * 1024)
    root = exporter._write_strand_package(package, tmp_path / "chunk-error", force=False)
    node = package.manifest["nodes"][0]
    assert "/Chunks/" in node["generated_relative_path"]
    error = exporter.LeanVerificationError(
        "Lean rejected the generated theorem",
        f"{root / node['generated_relative_path']}:"
        f"{node['source_line_start']}:2: error: local failure\n",
    )

    assert exporter._repairable_strand_node(error, package, root) == "zero_add"


def test_multiple_real_lean_errors_repair_one_bounded_dependency_order_batch(
    tmp_path: Path,
    exporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from peano_lab.library.lean_proof_strand import build_proof_strand, plan_proof_strand

    plan = plan_proof_strand("add_comm")
    package = build_proof_strand(plan)
    root = exporter._write_strand_package(package, tmp_path / "batch", force=False)
    args = exporter._parser().parse_args(["add_comm", "--format", "strand"])
    monkeypatch.setattr(exporter, "_lake_binary", lambda *_arguments: tmp_path / "lake")
    calls: list[dict[str, object]] = []

    def fake_verifier(candidate: object, *_arguments: object, **_options: object) -> None:
        calls.append(candidate.manifest)
        if len(calls) == 1:
            rows = candidate.manifest["nodes"]
            lines = [
                f"{root / row['generated_relative_path']}:"
                f"{row['source_line_start']}:3: error: exact local mismatch"
                for row in (rows[1], rows[0], rows[1])
            ]
            raise exporter.LeanVerificationError("Lean rejected the proof", "\n".join(lines))

    monkeypatch.setattr(exporter, "_verify_presentation_package", fake_verifier)

    repaired = exporter._verify_strand_package(plan, package, root, args)

    assert len(calls) == 2
    assert repaired.manifest["fallback_node_count"] == 2
    assert [
        row["name"]
        for row in repaired.manifest["nodes"]
        if row["proof_status"] == "local_checked_certificate"
    ] == ["zero_add", "add_succ_left"]


def test_lean_failure_diagnostics_are_bounded_without_untrusted_placeholder_output(
    exporter,
) -> None:
    diagnostics = "sorryAx " + "x" * (exporter.MAX_LEAN_FAILURE_DIAGNOSTIC_BYTES + 50)

    error = exporter.LeanVerificationError("Lean rejected the generated theorem", diagnostics)

    assert len(error.diagnostics.encode("utf-8")) <= exporter.MAX_LEAN_FAILURE_DIAGNOSTIC_BYTES
    assert error.diagnostics_truncated is True


@pytest.mark.parametrize("failure", ("foreign", "foundation", "already_fallback"))
def test_compiler_repair_never_guesses_non_readable_failure_locations(
    failure: str,
    tmp_path: Path,
    exporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from peano_lab.library.lean_proof_strand import build_proof_strand, plan_proof_strand

    plan = plan_proof_strand("zero_add")
    forced = frozenset({"zero_add"}) if failure == "already_fallback" else frozenset()
    package = build_proof_strand(plan, force_fallback_names=forced)
    root = exporter._write_strand_package(package, tmp_path / "not-repairable", force=False)
    args = exporter._parser().parse_args(["zero_add", "--format", "strand"])
    monkeypatch.setattr(exporter, "_lake_binary", lambda *_arguments: tmp_path / "lake")
    calls = 0

    def fake_verifier(candidate: object, *_arguments: object, **_options: object) -> None:
        nonlocal calls
        calls += 1
        source = (
            tmp_path / "Foreign.lean"
            if failure == "foreign"
            else root / candidate.relative_path
        )
        line = 1 if failure == "foundation" else candidate.manifest["nodes"][0]["source_line_start"]
        raise exporter.LeanVerificationError(
            "Lean rejected the generated theorem",
            f"{source}:{line}:1: error: malformed source\n",
        )

    monkeypatch.setattr(exporter, "_verify_presentation_package", fake_verifier)

    with pytest.raises(exporter.LeanVerificationError):
        exporter._verify_strand_package(plan, package, root, args)
    assert calls == 1


def test_compiler_repair_honors_strict_readability_and_attempt_caps(
    tmp_path: Path,
    exporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from peano_lab.library.lean_proof_strand import build_proof_strand, plan_proof_strand

    plan = plan_proof_strand("zero_add")
    package = build_proof_strand(plan)
    root = exporter._write_strand_package(package, tmp_path / "no-repairs", force=False)
    source = root / package.relative_path
    line = package.manifest["nodes"][0]["source_line_start"]
    monkeypatch.setattr(exporter, "_lake_binary", lambda *_arguments: tmp_path / "lake")

    def fail(*_arguments: object, **_options: object) -> None:
        raise exporter.LeanVerificationError(
            "Lean rejected the generated theorem",
            f"{source}:{line}:1: error: unsupported tactic\n",
        )

    monkeypatch.setattr(exporter, "_verify_presentation_package", fail)
    strict = exporter._parser().parse_args(
        ["zero_add", "--format", "strand", "--strict-readable"]
    )
    with pytest.raises(exporter.LeanVerificationError):
        exporter._verify_strand_package(plan, package, root, strict)

    bounded = exporter._parser().parse_args(
        ["zero_add", "--format", "strand", "--max-proof-repairs", "0"]
    )
    with pytest.raises(ValueError, match="0-attempt local certificate repair budget"):
        exporter._verify_strand_package(plan, package, root, bounded)


def test_compiler_repair_never_retries_a_timeout_or_memory_failure(
    tmp_path: Path,
    exporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from peano_lab.library.lean_proof_strand import build_proof_strand, plan_proof_strand

    plan = plan_proof_strand("zero_add")
    package = build_proof_strand(plan)
    root = exporter._write_strand_package(package, tmp_path / "timeout", force=False)
    args = exporter._parser().parse_args(["zero_add", "--format", "strand"])
    monkeypatch.setattr(exporter, "_lake_binary", lambda *_arguments: tmp_path / "lake")
    calls = 0

    def timeout(*_arguments: object, **_options: object) -> None:
        nonlocal calls
        calls += 1
        raise ValueError("Lean verification exceeded its memory or timeout limit")

    monkeypatch.setattr(exporter, "_verify_presentation_package", timeout)

    with pytest.raises(ValueError, match="memory or timeout"):
        exporter._verify_strand_package(plan, package, root, args)
    assert calls == 1


@pytest.mark.skipif(
    not (LEAN_PROJECT / ".lake" / "build" / "lib" / "lean" / "PeanoLab" / "Codec.olean").is_file(),
    reason="independently compiled sibling Lean companion is unavailable",
)
def test_real_lean_independently_compiles_entire_addition_commutativity_strand(
    tmp_path: Path,
) -> None:
    package = tmp_path / "verified"
    result = _run(
        "add_comm",
        "--format",
        "strand",
        "--package-dir",
        package,
        "--verify",
        "--max-memory-mib",
        "1024",
        "--max-verify-seconds",
        "90",
        timeout=100,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "Independent Lean compilation: PASSED." in result.stderr
    catalog = _catalog(package)
    manifest = next(iter(catalog["strands"].values()))
    source = (package / manifest["relative_path"]).read_text(encoding="utf-8")
    assert "zero_add" in source
    assert "add_succ_left" in source
    assert "add_comm" in source
    assert "sorry" not in source
    assert "sorryAx" not in result.stderr
    assert "Lean.trustCompiler" not in result.stderr
    for entry in manifest["files"]:
        assert (package / entry["relative_path"]).with_suffix(".olean").is_file()
