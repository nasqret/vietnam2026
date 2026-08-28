"""Human-readable Lean packages preserve certificate, release, and file authority."""

from __future__ import annotations

from dataclasses import replace
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from peano_lab.kernel.formulas import And, Eq
from peano_lab.kernel.proofs import AndIntro, EqRefl, Hyp, ImpIntro
from peano_lab.kernel.terms import Zero
from peano_lab.library.proof_bundle import BundleNode, ProofBundle, encode_proof_bundle


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "scripts" / "export_peano_lean.py"
LEAN_PROJECT = ROOT.parent / "peano-lab-lean"


def _run(*arguments: object, timeout: int = 30) -> subprocess.CompletedProcess[str]:
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
    spec = importlib.util.spec_from_file_location("peano_lean_presentation_cli", CLI)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _catalog(directory: Path) -> dict[str, object]:
    return json.loads((directory / "manifest.json").read_text(encoding="utf-8"))


def _isolated_lean_project(destination: Path) -> Path:
    """Copy exact verifier inputs so Lake can only refresh an owned test cache."""

    relatives = [
        Path("lakefile.toml"), Path("lake-manifest.json"),
        Path("lean-toolchain"), Path("PeanoLab.lean"),
    ]
    relatives.extend(
        source.relative_to(LEAN_PROJECT)
        for source in (LEAN_PROJECT / "PeanoLab").rglob("*.lean")
    )
    compiled = LEAN_PROJECT / ".lake/build/lib/lean/PeanoLab"
    for name in (
        "Syntax", "Substitution", "Derivation", "Checker", "Semantics",
        "Soundness", "Codec", "ProofBundle",
    ):
        assert (compiled / f"{name}.olean").is_file()
        for pattern in (f"{name}.olean*", f"{name}.ilean*"):
            relatives.extend(source.relative_to(LEAN_PROJECT) for source in compiled.glob(pattern))
    for relative in sorted(set(relatives)):
        source, target = LEAN_PROJECT / relative, destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        assert sha256(target.read_bytes()).digest() == sha256(source.read_bytes()).digest()
    return destination


def _bundle() -> ProofBundle:
    zero = Zero()
    proposition = Eq(zero, zero)
    return ProofBundle(
        nodes=(
            BundleNode(10, proposition, (), EqRefl(zero)),
            BundleNode(
                30,
                And(proposition, proposition),
                (10,),
                ImpIntro(AndIntro(Hyp(0), Hyp(0))),
            ),
        ),
        root=30,
    )


@pytest.mark.parametrize("edition", ("stable", "alpha"))
def test_named_checked_bundle_never_reconstructs_a_redundant_root_certificate(
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    edition: str,
) -> None:
    from peano_lab.library import editions_v19, editions_v30
    from peano_lab.library.theorems import replay as stable_replay

    checked = stable_replay("zero_add")
    bundle = ProofBundle(
        (BundleNode(0, checked.formula, (), checked.certificate),),
        0,
    )
    source = tmp_path / "named-checked-bundle.json"
    source.write_text(encode_proof_bundle(bundle, checked.formula))
    output = tmp_path / f"{edition}-checked-bundle.lean"

    def forbidden(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("an actual canonical proof bundle triggered redundant replay")

    monkeypatch.setattr(exporter, "replay", forbidden)
    monkeypatch.setattr(editions_v19, "replay", forbidden)
    monkeypatch.setattr(editions_v30, "replay", forbidden)

    assert exporter.main(
        [
            "zero_add",
            "--edition",
            edition,
            "--proof-bundle",
            str(source),
            "--output",
            str(output),
        ]
    ) == 0
    actual = output.read_text(encoding="utf-8")
    assert "zero_add" in actual
    assert "checkBundle_sound" in actual
    assert "sorry" not in actual


def test_legacy_default_and_explicit_full_source_remain_identical() -> None:
    original = _run("zero_add")
    explicit = _run("zero_add", "--format", "full")

    assert original.returncode == explicit.returncode == 0
    assert original.stdout == explicit.stdout
    assert "import PeanoLab.Codec" in original.stdout
    assert "private def " in original.stdout
    assert "PeanoLab.Artifact.check_sound" in original.stdout


@pytest.mark.parametrize("style", ("pretty", "exact"))
def test_statement_only_formats_never_replay_or_build_a_certificate(
    style: str,
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import peano_lab.library.lean_presentation as presentation

    def forbidden(*_args, **_kwargs):
        raise AssertionError("a statement-only preview tried to replay or emit a certificate")

    monkeypatch.setattr(exporter, "replay", forbidden)
    monkeypatch.setattr(presentation, "build_checked_presentation", forbidden)

    assert exporter.main(["zero_add", "--format", style]) == 0
    captured = capsys.readouterr()
    assert "0 +" in captured.out
    assert "no fresh kernel or Lean proof replay" in captured.err
    assert "private def " not in captured.out
    if style == "pretty":
        assert "Lean verification: NOT RUN" in captured.out


@pytest.mark.parametrize(
    "name",
    (
        "quadratic_reciprocity_combined",
        "lucas_theorem",
        "kummer_binomial_carry_bit_count",
        "kummer_carry_free_iff_not_divides",
        "bertrand_strict",
        "four_square_lagrange",
        "two_square_iff_zero_or_even_three_mod_four_prime_valuations",
    ),
)
def test_checked_alpha_statement_preview_does_not_replay_its_large_root(
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    name: str,
) -> None:
    from peano_lab.library import editions_v19, editions_v30

    def forbidden(*_args, **_kwargs):
        raise AssertionError("an Alpha statement preview tried to replay its proof")

    monkeypatch.setattr(editions_v19, "replay", forbidden)
    monkeypatch.setattr(editions_v30, "replay", forbidden)
    assert (
        exporter.main([name, "--edition", "alpha", "--format", "pretty"])
        == 0
    )
    captured = capsys.readouterr()
    assert name in captured.out
    assert "Edition: alpha" in captured.out
    assert "no fresh kernel or Lean proof replay" in captured.err


def test_compact_facade_without_package_does_not_print_certificate_header() -> None:
    result = _run("zero_add", "--format", "compact")

    assert result.returncode == 0, result.stderr
    assert "import PeanoLab.Presentation" in result.stdout
    assert "theorem «zero_add»" in result.stdout
    assert "private def " not in result.stdout


def test_one_package_contains_three_content_bound_modules_and_two_manifests(
    tmp_path: Path,
) -> None:
    package = tmp_path / "package"
    result = _run("zero_add", "--format", "compact", "--package-dir", package)

    assert result.returncode == 0, result.stderr
    assert "theorem «zero_add»" in result.stdout
    assert "private def " not in result.stdout
    catalog = _catalog(package)
    assert catalog["schema"] == "peano-lean-presentation-package-v1"
    assert catalog["notation_module"] == "PeanoLab.Presentation"
    assert catalog["presentation_count"] == 1
    token, manifest = next(iter(catalog["presentations"].items()))
    assert manifest["name"] == "zero_add"
    assert manifest["edition"] == "stable"
    assert manifest["authority"]["lean_compiler_verified"] is False
    assert json.loads((package / "manifests" / f"{token}.json").read_text()) == manifest
    assert len(manifest["files"]) == 3
    for entry in manifest["files"]:
        source = package / entry["relative_path"]
        payload = source.read_bytes()
        assert len(payload) == entry["bytes"]
        assert sha256(payload).hexdigest() == entry["sha256"]


def test_multiple_theorems_share_one_notation_and_preserve_every_manifest(
    tmp_path: Path,
) -> None:
    package = tmp_path / "many"
    first = _run("zero_add", "--format", "compact", "--package-dir", package)
    notation = (package / "PeanoLab" / "Presentation.lean").read_bytes()
    second = _run("add_comm", "--format", "compact", "--package-dir", package)

    assert first.returncode == second.returncode == 0
    catalog = _catalog(package)
    assert catalog["presentation_count"] == 2
    assert {entry["name"] for entry in catalog["presentations"].values()} == {
        "zero_add",
        "add_comm",
    }
    assert (package / "PeanoLab" / "Presentation.lean").read_bytes() == notation
    assert len(list((package / "manifests").glob("*.json"))) == 2
    assert len(list((package / "PeanoLab" / "Generated").glob("*/Certificate.lean"))) == 2
    assert len(list((package / "PeanoLab" / "Generated").glob("*/Theorem.lean"))) == 2


def test_identical_theorem_can_be_reexported_without_force(tmp_path: Path) -> None:
    package = tmp_path / "idempotent"
    first = _run("zero_add", "--format", "compact", "--package-dir", package)
    manifest = (package / "manifest.json").read_bytes()
    repeated = _run("zero_add", "--format", "compact", "--package-dir", package)

    assert first.returncode == repeated.returncode == 0
    assert (package / "manifest.json").read_bytes() == manifest
    assert _catalog(package)["presentation_count"] == 1


def test_same_checked_theorem_has_distinct_stable_and_alpha_module_names(
    tmp_path: Path,
) -> None:
    package = tmp_path / "editions"
    stable = _run("zero_add", "--format", "compact", "--package-dir", package)
    alpha = _run(
        "zero_add", "--edition", "alpha", "--format", "compact", "--package-dir", package
    )

    assert stable.returncode == alpha.returncode == 0
    catalog = _catalog(package)
    assert catalog["presentation_count"] == 2
    assert {entry["edition"] for entry in catalog["presentations"].values()} == {
        "stable",
        "alpha",
    }


def test_unregistered_proof_bundle_cannot_claim_stable_or_alpha_membership(
    tmp_path: Path,
) -> None:
    zero = Zero()
    proposition = Eq(zero, zero)
    source = tmp_path / "bundle.json"
    source.write_text(encode_proof_bundle(_bundle(), And(proposition, proposition)))
    package = tmp_path / "external"
    result = _run(
        "independent_shared_theorem",
        "--proof-bundle",
        source,
        "--format",
        "compact",
        "--package-dir",
        package,
    )

    assert result.returncode == 0, result.stderr
    manifest = next(iter(_catalog(package)["presentations"].values()))
    assert manifest["edition"] == "external-bundle"
    assert manifest["proof_mode"] == "bundle"
    assert manifest["authority"]["public_admission"] is False
    assert "not a Stable or Alpha library admission" in result.stderr


def test_existing_modified_source_cannot_be_silently_replaced(tmp_path: Path) -> None:
    package = tmp_path / "tampered-source"
    assert _run("zero_add", "--format", "compact", "--package-dir", package).returncode == 0
    certificate = next((package / "PeanoLab" / "Generated").glob("*/Certificate.lean"))
    certificate.write_text("-- attacker changed checked proof source\n")

    result = _run("add_comm", "--format", "compact", "--package-dir", package)

    assert result.returncode == 1
    assert "altered" in result.stderr
    assert certificate.read_text() == "-- attacker changed checked proof source\n"


def test_existing_modified_individual_manifest_cannot_be_silently_preserved(
    tmp_path: Path,
) -> None:
    package = tmp_path / "tampered-entry"
    assert _run("zero_add", "--format", "compact", "--package-dir", package).returncode == 0
    entry = next((package / "manifests").glob("*.json"))
    entry.write_text("{}\n")

    result = _run("add_comm", "--format", "compact", "--package-dir", package)

    assert result.returncode == 1
    assert "altered" in result.stderr


def test_existing_noncanonical_aggregate_manifest_fails_closed(tmp_path: Path) -> None:
    package = tmp_path / "tampered-catalog"
    assert _run("zero_add", "--format", "compact", "--package-dir", package).returncode == 0
    manifest = package / "manifest.json"
    manifest.write_text(manifest.read_text() + " ")

    result = _run("add_comm", "--format", "compact", "--package-dir", package)

    assert result.returncode == 1
    assert "canonical presentation catalog" in result.stderr


def test_oversized_manifest_is_rejected_before_unbounded_text_loading(
    tmp_path: Path,
    exporter,
) -> None:
    package = tmp_path / "oversized"
    package.mkdir()
    manifest = package / "manifest.json"
    with manifest.open("wb") as stream:
        stream.truncate(exporter.MAX_PACKAGE_MANIFEST_BYTES + 1)

    result = _run("zero_add", "--format", "compact", "--package-dir", package)

    assert result.returncode == 1
    assert "reviewed byte limit" in result.stderr


def test_oversized_generated_module_is_rejected_before_any_package_write(
    tmp_path: Path,
    exporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class OversizedPresentation:
        def files(self) -> list[tuple[str, str]]:
            return [("PeanoLab/Presentation.lean", "éé\n")]

    monkeypatch.setattr(exporter, "MAX_PACKAGE_MODULE_BYTES", 4)
    root = tmp_path / "oversized-module"

    with pytest.raises(ValueError, match="reviewed byte limit"):
        exporter._write_presentation_package(OversizedPresentation(), root, force=False)

    assert not root.exists()


def test_package_root_symlink_is_rejected(tmp_path: Path) -> None:
    actual = tmp_path / "actual"
    actual.mkdir()
    link = tmp_path / "linked"
    link.symlink_to(actual, target_is_directory=True)

    result = _run("zero_add", "--format", "compact", "--package-dir", link)

    assert result.returncode == 1
    assert "must not be a symlink" in result.stderr
    assert list(actual.iterdir()) == []


def test_package_nested_symlink_is_rejected_before_any_source_write(tmp_path: Path) -> None:
    package = tmp_path / "nested"
    package.mkdir()
    foreign = tmp_path / "foreign"
    foreign.mkdir()
    (package / "PeanoLab").symlink_to(foreign, target_is_directory=True)

    result = _run("zero_add", "--format", "compact", "--package-dir", package)

    assert result.returncode == 1
    assert "must not be a symlink" in result.stderr
    assert list(foreign.iterdir()) == []


@pytest.mark.parametrize("style", ("full", "compact", "pretty", "exact"))
def test_output_symlink_is_never_followed_even_with_force(
    style: str,
    tmp_path: Path,
) -> None:
    target = tmp_path / "protected.lean"
    target.write_text("preserve me\n")
    output = tmp_path / "link.lean"
    output.symlink_to(target)

    result = _run("zero_add", "--format", style, "--output", output, "--force")

    assert result.returncode == 1
    assert "must not be a symlink" in result.stderr
    assert target.read_text() == "preserve me\n"


@pytest.mark.parametrize("relative", ("manifest.json", "manifests/injected.json", "bad.lean"))
def test_output_inside_package_is_rejected_even_with_force(
    relative: str,
    tmp_path: Path,
) -> None:
    package = tmp_path / "reserved"
    result = _run(
        "zero_add",
        "--format",
        "compact",
        "--package-dir",
        package,
        "--output",
        package / relative,
        "--force",
    )

    assert result.returncode == 1
    assert "must not be inside its Lean package" in result.stderr
    assert not package.exists()


def test_external_compact_output_is_written_atomically(tmp_path: Path) -> None:
    package = tmp_path / "safe-package"
    output = tmp_path / "Pretty.lean"
    result = _run(
        "zero_add",
        "--format",
        "compact",
        "--package-dir",
        package,
        "--output",
        output,
    )

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert "theorem «zero_add»" in output.read_text()
    assert "private def " not in output.read_text()
    assert list(tmp_path.glob(".peano-lean-*.tmp")) == []


def test_unknown_alpha_theorem_fails_closed() -> None:
    result = _run("does_not_exist", "--edition", "alpha", "--format", "pretty")

    assert result.returncode == 2
    assert "Unknown Alpha Peano theorem" in result.stderr


def test_alpha_body_only_theorem_is_denied_even_for_statement_preview(
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    from peano_lab.library import editions_v19, editions_v30

    actual = editions_v19.entry("zero_add", edition="alpha")
    assert actual is not None
    unauthorized = replace(actual, evidence=editions_v19.EvidenceStatus.BODY_CHECKED)
    monkeypatch.setattr(editions_v30, "entry", lambda *_args, **_kwargs: unauthorized)

    assert exporter.main(["zero_add", "--edition", "alpha", "--format", "pretty"]) == 1
    assert "checked-use authority" in capsys.readouterr().err


@pytest.mark.parametrize(
    "relative",
    (
        "",
        "/PeanoLab/Outside.lean",
        "../PeanoLab/Outside.lean",
        "PeanoLab/../Outside.lean",
        "PeanoLab//Outside.lean",
        "PeanoLab/./Outside.lean",
        "Other/Outside.lean",
        "PeanoLab/Outside.json",
        "PeanoLab\\Outside.lean",
    ),
)
def test_unsafe_module_paths_are_rejected_before_writes(
    relative: str,
    tmp_path: Path,
    exporter,
) -> None:
    with pytest.raises(ValueError, match="path"):
        exporter._safe_package_destination(tmp_path, relative)


@pytest.mark.parametrize("offset", (-1, 0, 1))
def test_lean_verifier_conservative_source_budget_has_an_exact_boundary(
    offset: int,
    tmp_path: Path,
    exporter,
) -> None:
    memory_mib = 64
    ceiling = (
        memory_mib * 1024 * 1024
        // exporter.LEAN_VERIFIER_SOURCE_MEMORY_AMPLIFICATION
    )
    source = tmp_path / "boundary.lean"
    source.write_bytes(b"-" * (ceiling + offset))

    if offset <= 0:
        exporter._require_lean_verifier_source_budget(
            source,
            max_memory_mib=memory_mib,
        )
    else:
        with pytest.raises(ValueError, match="refused before launching any compiler"):
            exporter._require_lean_verifier_source_budget(
                source,
                max_memory_mib=memory_mib,
            )


def test_oversized_standalone_lean_source_never_launches_a_compiler(
    tmp_path: Path,
    exporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_mib = 64
    maximum = (
        memory_mib * 1024 * 1024
        // exporter.LEAN_VERIFIER_SOURCE_MEMORY_AMPLIFICATION
    )
    source = tmp_path / "oversized.lean"
    source.write_bytes(b"-" * (maximum + 1))
    project = tmp_path / "lean-project"
    codec = project / "PeanoLab" / "Codec.lean"
    codec.parent.mkdir(parents=True)
    codec.write_text("-- fake checked companion\n", encoding="utf-8")
    launched: list[object] = []

    def forbidden(*arguments: object, **_options: object) -> None:
        launched.extend(arguments)
        raise AssertionError("unsafe Lean source launched a compiler")

    monkeypatch.setattr(exporter.subprocess, "Popen", forbidden)

    with pytest.raises(ValueError, match="32,768-byte conservative source ceiling"):
        exporter._verify(
            source,
            project,
            tmp_path / "lake",
            max_memory_mib=memory_mib,
            max_verify_seconds=10,
        )

    assert launched == []


def test_oversized_later_package_module_prevents_even_a_prelude_launch(
    tmp_path: Path,
    exporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    memory_mib = 64
    maximum = (
        memory_mib * 1024 * 1024
        // exporter.LEAN_VERIFIER_SOURCE_MEMORY_AMPLIFICATION
    )
    root = tmp_path / "package"
    prelude = root / "PeanoLab" / "Presentation.lean"
    certificate = root / "PeanoLab" / "Generated" / "Guard" / "Certificate.lean"
    prelude.parent.mkdir(parents=True)
    certificate.parent.mkdir(parents=True)
    prelude.write_text("-- small safe prelude\n", encoding="utf-8")
    certificate.write_bytes(b"-" * (maximum + 1))

    class OversizedPresentation:
        @staticmethod
        def files() -> tuple[tuple[str, str], ...]:
            return (
                ("PeanoLab/Presentation.lean", "-- small safe prelude\n"),
                ("PeanoLab/Generated/Guard/Certificate.lean", "-- certificate\n"),
            )

    launched: list[object] = []

    def forbidden(*arguments: object, **_options: object) -> None:
        launched.extend(arguments)
        raise AssertionError("an unsafe later certificate launched a compiler")

    monkeypatch.setattr(exporter.subprocess, "Popen", forbidden)

    with pytest.raises(ValueError, match="Certificate.lean.*32,768-byte"):
        exporter._verify_presentation_package(
            OversizedPresentation(),
            root,
            tmp_path / "lean-project",
            tmp_path / "lake",
            max_memory_mib=memory_mib,
            max_verify_seconds=10,
        )

    assert launched == []


@pytest.mark.skipif(
    not (LEAN_PROJECT / ".lake" / "build" / "lib" / "lean" / "PeanoLab" / "Codec.olean").is_file(),
    reason="independently compiled sibling Lean companion is unavailable",
)
def test_real_lean_compiles_shared_prelude_certificate_and_alias_facade(
    exporter,
    tmp_path: Path,
) -> None:
    package = tmp_path / "verified"
    project = _isolated_lean_project(tmp_path / "lean-companion")
    lake = exporter._lake_binary(LEAN_PROJECT, None)
    result = _run(
        "le_refl",
        "--format",
        "compact",
        "--package-dir",
        package,
        "--lean-project",
        project,
        "--lake",
        lake,
        "--verify",
        "--max-memory-mib",
        "1024",
        "--max-verify-seconds",
        "60",
        timeout=70,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "theorem «le_refl»" in result.stdout
    assert "PeanoLab.Presentation.Le" in result.stdout or "Le " in result.stdout
    assert "depends on axioms" in result.stderr
    assert "sorryAx" not in result.stderr
    assert "Lean.trustCompiler" not in result.stderr
    manifest = next(iter(_catalog(package)["presentations"].values()))
    for entry in manifest["files"]:
        assert (package / entry["relative_path"]).with_suffix(".olean").is_file()
