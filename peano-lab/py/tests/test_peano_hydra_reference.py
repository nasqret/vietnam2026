"""Fresh reference provenance, exact protocol rows, and axiom-audit failures."""

from hashlib import sha256
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from training.peano_hydra import reference  # noqa: E402
from training.peano_hydra.frontier import digest  # noqa: E402


def _audit() -> str:
    return "\n".join(f"'{name}' depends on axioms: [propext, Classical.choice, Quot.sound]"
                     for name in reference.AUDIT_DECLARATIONS)


def test_complete_axiom_audit_retains_only_declared_footprint() -> None:
    result = reference.parse_axiom_audit(_audit())
    assert set(result) == set(reference.AUDIT_DECLARATIONS)
    assert all(set(values) == reference.ALLOWED_AXIOMS for values in result.values())


def test_empty_axiom_footprint_is_supported_without_invented_axioms() -> None:
    output = "\n".join(f"'{name}' does not depend on any axioms"
                       for name in reference.AUDIT_DECLARATIONS)
    assert all(values == [] for values in reference.parse_axiom_audit(output).values())


@pytest.mark.parametrize("output", [
    "", _audit().splitlines()[0], _audit() + "\n" + _audit().splitlines()[0],
    _audit().replace("Quot.sound", "sorryAx"), _audit().replace("Quot.sound", "unreviewedAxiom"),
    _audit() + "\nerror: declaration failed", _audit() + "\nLean.trustCompiler",
    "unparsed prefix\n" + _audit(), _audit() + "\nunparsed suffix",
    _audit().replace(reference.AUDIT_DECLARATIONS[0], "Unexpected.theorem"),
])
def test_reference_axiom_audit_fails_closed(output) -> None:
    with pytest.raises(reference.ReferenceReviewError):
        reference.parse_axiom_audit(output)


def _result(stdout="ACCEPT\ta.json\tfuel=4096\n", stderr="", returncode=0, reason="exited"):
    return {"stdout": stdout, "stderr": stderr, "returncode": returncode, "reason": reason}


def test_mixed_reference_decisions_are_explicit_not_exit_code_guesses() -> None:
    row = _result("ACCEPT\ta.json\tfuel=4096\nREJECT\tb.json\tfuel=4096\n",
                  "DECODE_ERROR\tc.json\tinvalid arity\n", 2)
    assert reference.parse_verifier_output(row, ("a.json", "b.json", "c.json")) == {
        "a.json": "ACCEPT", "b.json": "REJECT", "c.json": "DECODE_ERROR",
    }


@pytest.mark.parametrize("row", [
    _result(reason="cpu_limit"), _result(returncode=1), _result(stdout=""),
    _result(stdout="ACCEPT\tother.json\tfuel=4096\n"),
    _result(stdout="ACCEPT\ta.json\tfuel=4096\n" * 2),
    _result(stdout="ACCEPT\ta.json\nfuel=4096\n"),
    _result(stdout="ACCEPT\ta.json\tfuel=oops\n"),
    _result(stderr="warning: unexpected output\n"),
    _result(stdout="UNKNOWN\ta.json\tfuel=4096\n"),
])
def test_incomplete_malformed_or_killed_reference_is_not_a_match(row) -> None:
    with pytest.raises(reference.ReferenceReviewError):
        reference.parse_verifier_output(row, ("a.json",))


@pytest.mark.parametrize("content", [
    "axiom fake : False\n", "theorem fake : False := by sorry\n", "unsafe def f := 0\n",
    "-- Lean.trustCompiler\n", "admit\n",
])
def test_reference_source_tripwire_rejects_trust_shortcuts(tmp_path, content) -> None:
    path = tmp_path / "Source.lean"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(reference.ReferenceReviewError):
        reference._source(path)


def test_changed_reference_identity_cannot_satisfy_a_hash_only_gate() -> None:
    record = {
        "schema": reference.SCHEMA, "files": {name: {} for name in reference.MODULES},
        "audit_source_sha256": "0" * 64,
    }
    record["reference_sha256"] = digest(record)
    with pytest.raises(reference.ReferenceReviewError):
        reference.validate_reference_identity(record)


def _detached(value):
    return json.loads(json.dumps(value))


def _reseal(value, field):
    value.pop(field, None)
    value[field] = digest(value)
    return value


def _worker_receipt(command, limits, *, stdout="", stderr="", returncode=0, reason="exited"):
    """A complete tiny mock transport receipt; no real compiler is launched."""
    return {
        "command": list(command), "limits": limits.to_dict(), "returncode": returncode,
        "stdin_bytes": 0, "stdin_sha256": sha256(b"").hexdigest(),
        "reason": reason, "stdout": stdout, "stderr": stderr, "output_encoding": "utf-8",
        "raw_output_base64": None, "output_truncated": False,
        "stdout_bytes": len(stdout.encode()), "stderr_bytes": len(stderr.encode()),
        "stdout_sha256": sha256(stdout.encode()).hexdigest(), "stderr_sha256": sha256(stderr.encode()).hexdigest(),
        "resources": {"wall_seconds": 0.01, "cpu_seconds": 0.005, "peak_rss_bytes": 1024**2,
                      "sampled_peak_group_rss_bytes": 1024**2, "cpu_instructions": None, "energy_joules": None},
        "observed_descendant_count": 0,
        "resource_measurement": "owned-child wait4; RSS guard sampled at 100ms; no hardware attestation",
    }


@pytest.fixture
def mock_reference(tmp_path, monkeypatch):
    """Eight tiny staged files and hashed fake binaries, never executable Lean."""
    project = tmp_path / "companion"
    project.mkdir()
    previous = None
    for relative in reference.MODULES:
        source = project / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        imports = "" if previous is None else f"import {previous}\n"
        source.write_text(imports + f"-- test-only source {relative}\nnamespace PeanoLab\nend PeanoLab\n", encoding="utf-8")
        previous = relative.removesuffix(".lean").replace("/", ".")
    (project / "lean-toolchain").write_text("leanprover/lean4:v4.28.0\n", encoding="utf-8")
    toolchain = tmp_path / "toolchain"
    compiler = toolchain / "bin" / "lean"
    compiler.parent.mkdir(parents=True)
    compiler.write_bytes(b"test-only fake compiler, not executed\n")
    runtime = toolchain / "lib" / "lean" / "libleanshared.dylib"
    runtime.parent.mkdir(parents=True)
    runtime.write_bytes(b"test-only fake runtime, not loaded\n")
    monkeypatch.setattr(reference, "_git", lambda project, *args: "c" * 40 if args == ("rev-parse", "HEAD") else "")
    def version_probe(command, **kwargs):
        assert command == [str(compiler.resolve()), "--version"]
        return SimpleNamespace(stdout="Lean (version 4.28.0, test-only, Release)\n", stderr="", returncode=0)
    monkeypatch.setattr(reference.subprocess, "run", version_probe)
    calls = []
    def fake_bounded(command, *, cwd, limits, lean_path, **kwargs):
        assert Path(cwd).is_absolute()
        assert Path(lean_path).resolve() == Path(cwd)
        assert command[:3] == (str(compiler.resolve()), "-j1", "-M768")
        calls.append({"command": command, "cwd": Path(cwd), "lean_path": lean_path, "limits": limits})
        if "-o" in command:
            assert limits == reference.BUILD_LIMITS
            relative = command[-1]
            assert relative in reference.MODULES
            output = Path(command[command.index("-o") + 1])
            assert output.is_absolute()
            assert output == Path(cwd) / Path(relative).with_suffix(".olean")
            output.write_bytes(b"test-only compiled bytes\n" + (Path(cwd) / relative).read_bytes())
            return _worker_receipt(command, limits)
        if command[-1] == "HydraAxiomAudit.lean":
            assert limits == reference.BUILD_LIMITS
            return _worker_receipt(command, limits, stdout=_audit() + "\n")
        assert command[3:5] == ("--run", "PeanoLab/Verify.lean")
        assert limits == reference.CHECK_LIMITS
        paths = command[5:]
        assert paths and all((Path(cwd) / path).is_file() for path in paths)
        return _worker_receipt(command, limits, stdout="".join(f"ACCEPT\t{path}\tfuel=4096\n" for path in paths))
    monkeypatch.setattr(reference, "run_bounded", fake_bounded)
    identity = reference.inspect_reference(project, compiler)
    return SimpleNamespace(project=project, compiler=compiler, runtime=runtime,
                           destination=tmp_path / "staged", identity=identity, calls=calls, run=fake_bounded)


def _build(fixture):
    reference.stage_reference(fixture.project, fixture.destination, fixture.identity)
    return reference.build_reference(fixture.destination, fixture.identity)


def _cases(count=1):
    from training.peano_hydra.conformance import ConformanceCase
    artifact = b'["peano-lab-v2",4096,["eq",["zero"],["zero"]],["eq_refl",["zero"]]]\n'
    return tuple(ConformanceCase(f"fixture_{index}", "fixture", 0, "positive", "0 = 0",
                                 True, "ACCEPT", artifact) for index in range(count))


def test_mock_fresh_build_binds_every_module_binary_and_axiom_row(mock_reference):
    fixture = mock_reference
    build = _build(fixture)
    assert [row["module"] for row in build["compile_rows"]] == list(reference.MODULES)
    assert len(fixture.calls) == len(reference.MODULES) + 1
    assert set(build["compiled_files"]) == {str(Path(name).with_suffix(".olean")) for name in reference.MODULES}
    assert build["compiled_root_sha256"] == digest(build["compiled_files"])
    assert build["reference_sha256"] == fixture.identity["reference_sha256"]
    assert build["fresh_source_build"] is True
    assert build["h0_complete"] is build["research_claim_eligible"] is False
    assert reference.validate_build(fixture.destination, fixture.identity, build) is None


def test_relative_staging_and_build_use_one_absolute_output_directory(mock_reference, monkeypatch, tmp_path):
    fixture = mock_reference
    monkeypatch.chdir(tmp_path)
    destination = Path("relative-reference")
    reference.stage_reference(fixture.project, destination, fixture.identity)
    build = reference.build_reference(destination, fixture.identity)
    assert all(call["cwd"] == destination.resolve() for call in fixture.calls)
    assert reference.validate_build(destination, fixture.identity, build) is None


@pytest.mark.parametrize("suffix", (".olean", ".olean.private", ".olean.server"))
def test_prebuilt_primary_or_sidecar_is_rejected_before_any_compile(mock_reference, suffix):
    fixture = mock_reference
    reference.stage_reference(fixture.project, fixture.destination, fixture.identity)
    source = fixture.destination / reference.MODULES[0]
    source.with_suffix(suffix).write_bytes(b"unreviewed prebuilt artifact")
    with pytest.raises(reference.ReferenceReviewError):
        reference.build_reference(fixture.destination, fixture.identity)
    assert fixture.calls == []


@pytest.mark.parametrize("suffix", (".olean.private", ".olean.server"))
def test_fresh_compilation_sidecars_are_bound_and_later_tamper_is_rejected(mock_reference, monkeypatch, suffix):
    fixture = mock_reference
    def compile_with_sidecar(command, **kwargs):
        result = fixture.run(command, **kwargs)
        if "-o" in command:
            primary = Path(command[command.index("-o") + 1])
            primary.with_suffix(suffix).write_bytes(b"fresh test-only compiler sidecar\n")
        return result
    monkeypatch.setattr(reference, "run_bounded", compile_with_sidecar)
    build = _build(fixture)
    sidecars = {str(Path(name).with_suffix(suffix)) for name in reference.MODULES}
    assert sidecars <= set(build["compiled_files"])
    assert reference.validate_build(fixture.destination, fixture.identity, build) is None
    (fixture.destination / sorted(sidecars)[0]).write_bytes(b"changed compiled sidecar")
    calls_before = len(fixture.calls)
    with pytest.raises(reference.ReferenceReviewError):
        reference.check_reference_cases(fixture.destination, fixture.identity, build, _cases())
    assert len(fixture.calls) == calls_before


@pytest.mark.parametrize("mutation", ("changed", "missing", "foreign", "symlink"))
def test_compiled_inventory_tampering_blocks_case_execution(mock_reference, mutation):
    fixture = mock_reference
    build = _build(fixture)
    compiled = (fixture.destination / reference.MODULES[0]).with_suffix(".olean")
    if mutation == "changed":
        compiled.write_bytes(b"changed compiled proof")
    elif mutation == "missing":
        compiled.unlink()
    elif mutation == "foreign":
        (compiled.parent / "Unreviewed.olean").write_bytes(b"unreviewed module")
    elif mutation == "symlink":
        saved = fixture.destination.parent / "saved-fixture-olean"
        compiled.rename(saved)
        compiled.symlink_to(saved)
    calls_before = len(fixture.calls)
    with pytest.raises((reference.ReferenceReviewError, OSError)):
        reference.check_reference_cases(fixture.destination, fixture.identity, build, _cases())
    assert len(fixture.calls) == calls_before
    assert not (fixture.destination / "cases").exists()


@pytest.mark.parametrize("which", ("compiler", "runtime"))
@pytest.mark.parametrize("phase", ("before_build", "during_build", "before_cases", "during_cases"))
def test_compiler_runtime_changes_are_rejected_at_each_phase(mock_reference, monkeypatch, which, phase):
    fixture = mock_reference
    changed = getattr(fixture, which)
    reference.stage_reference(fixture.project, fixture.destination, fixture.identity)
    if phase == "before_build":
        changed.write_bytes(b"different toolchain bytes")
        with pytest.raises(reference.ReferenceReviewError):
            reference.build_reference(fixture.destination, fixture.identity)
        assert fixture.calls == []
        return
    if phase == "during_build":
        def mutate_during_audit(command, **kwargs):
            result = fixture.run(command, **kwargs)
            if command[-1] == "HydraAxiomAudit.lean":
                changed.write_bytes(b"toolchain changed during compilation")
            return result
        monkeypatch.setattr(reference, "run_bounded", mutate_during_audit)
        with pytest.raises(reference.ReferenceReviewError):
            reference.build_reference(fixture.destination, fixture.identity)
        assert len(fixture.calls) == len(reference.MODULES) + 1
        return
    build = reference.build_reference(fixture.destination, fixture.identity)
    if phase == "before_cases":
        changed.write_bytes(b"different toolchain bytes")
    else:
        def mutate_after_call(*args, **kwargs):
            result = fixture.run(*args, **kwargs)
            changed.write_bytes(b"toolchain changed during worker")
            return result
        monkeypatch.setattr(reference, "run_bounded", mutate_after_call)
    with pytest.raises(reference.ReferenceReviewError):
        reference.check_reference_cases(fixture.destination, fixture.identity, build, _cases())


def test_compiled_tamper_during_cases_cannot_publish_success(mock_reference, monkeypatch):
    fixture = mock_reference
    build = _build(fixture)
    def mutate_after_call(*args, **kwargs):
        result = fixture.run(*args, **kwargs)
        (fixture.destination / "PeanoLab/Codec.olean").write_bytes(b"changed after initial admission")
        return result
    monkeypatch.setattr(reference, "run_bounded", mutate_after_call)
    with pytest.raises(reference.ReferenceReviewError):
        reference.check_reference_cases(fixture.destination, fixture.identity, build, _cases())


def test_missing_build_receipt_never_starts_conformance(mock_reference):
    fixture = mock_reference
    _build(fixture)
    calls_before = len(fixture.calls)
    with pytest.raises(reference.ReferenceReviewError):
        reference.check_reference_cases(fixture.destination, fixture.identity, {}, _cases())
    assert len(fixture.calls) == calls_before


@pytest.mark.parametrize("mutation", (
    "no_compile_rows", "empty_compile_rows", "reordered_compile_rows", "wrong_compile_module",
    "wrong_compile_command", "failed_compile", "limited_compile", "changed_compile_hash",
    "failed_audit", "limited_audit", "wrong_audit_command", "false_fresh_claim",
    "false_h0_claim", "false_research_claim", "wrong_schema", "unknown_field",
))
def test_resealed_build_receipt_cannot_invent_fresh_compilation(mock_reference, mutation):
    fixture = mock_reference
    build = _detached(_build(fixture))
    if mutation == "no_compile_rows":
        build.pop("compile_rows")
    elif mutation == "empty_compile_rows":
        build["compile_rows"] = []
    elif mutation == "reordered_compile_rows":
        build["compile_rows"].reverse()
    elif mutation == "wrong_compile_module":
        build["compile_rows"][0]["module"] = reference.MODULES[-1]
    elif mutation == "wrong_compile_command":
        build["compile_rows"][0]["command"][0] = "/unreviewed/lean"
    elif mutation == "failed_compile":
        build["compile_rows"][0]["returncode"] = 1
    elif mutation == "limited_compile":
        build["compile_rows"][0]["reason"] = "cpu_limit"
    elif mutation == "changed_compile_hash":
        build["compile_rows"][0]["compiled_olean"]["sha256"] = "0" * 64
    elif mutation == "failed_audit":
        build["axiom_audit"]["returncode"] = 1
    elif mutation == "limited_audit":
        build["axiom_audit"]["reason"] = "wall_limit"
    elif mutation == "wrong_audit_command":
        build["axiom_audit"]["command"][-1] = "NotTheAudit.lean"
    elif mutation == "false_fresh_claim":
        build["fresh_source_build"] = False
    elif mutation == "false_h0_claim":
        build["h0_complete"] = True
    elif mutation == "false_research_claim":
        build["research_claim_eligible"] = True
    elif mutation == "wrong_schema":
        build["schema"] = "other-build"
    elif mutation == "unknown_field":
        build["unchecked_authority"] = True
    _reseal(build, "build_sha256")
    calls_before = len(fixture.calls)
    with pytest.raises(reference.ReferenceReviewError):
        reference.check_reference_cases(fixture.destination, fixture.identity, build, _cases())
    assert len(fixture.calls) == calls_before


@pytest.mark.parametrize("worker", ("compile", "audit"))
@pytest.mark.parametrize("mutation", (
    "wrong_limits", "boolean_exit_code", "truncated_output", "raw_output",
    "wrong_encoding", "wrong_output_bytes", "wrong_output_digest", "descendant",
    "cpu_over_budget", "wall_over_budget", "rss_over_budget", "negative_cpu",
    "invented_energy", "invented_instructions", "missing_resources",
))
def test_resealed_build_worker_receipt_preserves_output_and_resource_contract(mock_reference, worker, mutation):
    fixture = mock_reference
    build = _detached(_build(fixture))
    row = build["compile_rows"][0] if worker == "compile" else build["axiom_audit"]
    if mutation == "wrong_limits":
        row["limits"]["cpu_seconds"] -= 1
    elif mutation == "boolean_exit_code":
        row["returncode"] = False
    elif mutation == "truncated_output":
        row["output_truncated"] = True
    elif mutation == "raw_output":
        row["raw_output_base64"] = {"stdout": "", "stderr": ""}
    elif mutation == "wrong_encoding":
        row["output_encoding"] = "base64"
    elif mutation == "wrong_output_bytes":
        row["stdout_bytes"] += 1
    elif mutation == "wrong_output_digest":
        row["stdout_sha256"] = "0" * 64
    elif mutation == "descendant":
        row["observed_descendant_count"] = 1
    elif mutation == "cpu_over_budget":
        row["resources"]["cpu_seconds"] = reference.BUILD_LIMITS.cpu_seconds + 1
    elif mutation == "wall_over_budget":
        row["resources"]["wall_seconds"] = reference.BUILD_LIMITS.wall_seconds + 1
    elif mutation == "rss_over_budget":
        row["resources"]["peak_rss_bytes"] = reference.BUILD_LIMITS.rss_bytes + 1
    elif mutation == "negative_cpu":
        row["resources"]["cpu_seconds"] = -1
    elif mutation == "invented_energy":
        row["resources"]["energy_joules"] = 0
    elif mutation == "invented_instructions":
        row["resources"]["cpu_instructions"] = 0
    elif mutation == "missing_resources":
        row.pop("resources")
    _reseal(build, "build_sha256")
    calls_before = len(fixture.calls)
    with pytest.raises(reference.ReferenceReviewError):
        reference.check_reference_cases(fixture.destination, fixture.identity, build, _cases())
    assert len(fixture.calls) == calls_before


@pytest.mark.parametrize("mutation", (
    "unknown_field", "bad_commit", "untyped_dirty", "relative_compiler", "runtime_escape",
    "compiler_bytes_boolean", "source_digest", "untyped_pin_claim", "false_pin_claim",
    "wrong_toolchain_syntax", "wrong_compiler_version", "wrong_batch_size", "wrong_options",
    "extra_axiom", "missing_source", "false_h0_claim", "allow_prebuilt",
))
def test_resealed_invalid_reference_identity_is_not_accepted(mock_reference, mutation):
    record = _detached(mock_reference.identity)
    if mutation == "unknown_field":
        record["unreviewed"] = True
    elif mutation == "bad_commit":
        record["project_git_commit"] = "HEAD"
    elif mutation == "untyped_dirty":
        record["project_git_dirty"] = 0
    elif mutation == "relative_compiler":
        record["compiler"]["path"] = "bin/lean"
    elif mutation == "runtime_escape":
        record["runtime_library"]["relative_to_toolchain"] = "../../unreviewed.dylib"
    elif mutation == "compiler_bytes_boolean":
        record["compiler"]["bytes"] = True
    elif mutation == "source_digest":
        record["files"][reference.MODULES[0]]["sha256"] = "not-a-digest"
        record["source_root_sha256"] = digest(record["files"])
    elif mutation == "untyped_pin_claim":
        record["matches_project_toolchain_pin"] = 1
    elif mutation == "false_pin_claim":
        record["matches_project_toolchain_pin"] = False
    elif mutation == "wrong_toolchain_syntax":
        record["project_toolchain_pin"] = "unreviewed-channel"
    elif mutation == "wrong_compiler_version":
        record["compiler_version"] = "Something else"
    elif mutation == "wrong_batch_size":
        record["batch_size"] += 1
    elif mutation == "wrong_options":
        record["lean_options"] = ["-j64"]
    elif mutation == "extra_axiom":
        record["allowed_axioms"].append("unreviewedAxiom")
    elif mutation == "missing_source":
        record["files"].pop(reference.MODULES[-1])
        record["source_root_sha256"] = digest(record["files"])
    elif mutation == "false_h0_claim":
        record["h0_complete"] = True
    elif mutation == "allow_prebuilt":
        record["prebuilt_companion_imports_allowed"] = True
    _reseal(record, "reference_sha256")
    with pytest.raises(reference.ReferenceReviewError):
        reference.validate_reference_identity(record)


def test_selected_compiler_override_is_recorded_honestly_not_claimed_pin_match(mock_reference):
    fixture = mock_reference
    (fixture.project / "lean-toolchain").write_text("leanprover/lean4:v4.24.0\n", encoding="utf-8")
    record = reference.inspect_reference(fixture.project, fixture.compiler)
    assert record["matches_project_toolchain_pin"] is False
    assert reference.validate_reference_identity(record) is None
    record["matches_project_toolchain_pin"] = True
    _reseal(record, "reference_sha256")
    with pytest.raises(reference.ReferenceReviewError, match="pin claim"):
        reference.validate_reference_identity(record)


@pytest.mark.parametrize("phase", ("before_build", "before_cases"))
def test_resealed_compiler_version_claim_is_reprobed_against_the_actual_binary(mock_reference, phase):
    fixture = mock_reference
    (fixture.project / "lean-toolchain").write_text("leanprover/lean4:v4.31.0\n", encoding="utf-8")
    fixture.identity = reference.inspect_reference(fixture.project, fixture.compiler)
    assert fixture.identity["matches_project_toolchain_pin"] is False
    build = _build(fixture) if phase == "before_cases" else None
    forged = _detached(fixture.identity)
    forged["compiler_version"] = forged["compiler_version"].replace("4.28.0", "4.31.0")
    forged["matches_project_toolchain_pin"] = True
    _reseal(forged, "reference_sha256")
    assert reference.validate_reference_identity(forged) is None
    calls_before = len(fixture.calls)
    if phase == "before_build":
        reference.stage_reference(fixture.project, fixture.destination, forged)
        with pytest.raises(reference.ReferenceReviewError, match="compiler version"):
            reference.build_reference(fixture.destination, forged)
    else:
        build["reference_sha256"] = forged["reference_sha256"]
        _reseal(build, "build_sha256")
        assert reference.validate_build_receipt(forged, build) is None
        with pytest.raises(reference.ReferenceReviewError, match="compiler version"):
            reference.check_reference_cases(fixture.destination, forged, build, _cases())
    assert len(fixture.calls) == calls_before


def test_live_version_probe_does_not_inherit_lean_or_loader_redirects(mock_reference, monkeypatch):
    fixture = mock_reference
    forbidden = ("LEAN_PATH", "LEAN_SYSROOT", "LEAN_OPTS", "LD_LIBRARY_PATH", "LD_AUDIT",
                 "LD_PRELOAD", "DYLD_LIBRARY_PATH", "DYLD_FALLBACK_LIBRARY_PATH", "DYLD_INSERT_LIBRARIES")
    for name in forbidden:
        monkeypatch.setenv(name, "/unreviewed-test-only-redirect")
    def version_probe(command, **kwargs):
        assert command == [str(fixture.compiler), "--version"]
        assert not set(forbidden) & set(kwargs["env"])
        assert kwargs["timeout"] == 10
        return SimpleNamespace(stdout=fixture.identity["compiler_version"] + "\n")
    monkeypatch.setattr(reference.subprocess, "run", version_probe)
    assert reference._compiler_version(fixture.compiler) == fixture.identity["compiler_version"]


@pytest.mark.parametrize("which", ("compiler", "runtime"))
def test_version_probe_mutation_is_detected_before_compilation(mock_reference, monkeypatch, which):
    fixture = mock_reference
    reference.stage_reference(fixture.project, fixture.destination, fixture.identity)
    def version_probe(command, **kwargs):
        getattr(fixture, which).write_bytes(b"changed during the version probe")
        return SimpleNamespace(stdout=fixture.identity["compiler_version"] + "\n")
    monkeypatch.setattr(reference.subprocess, "run", version_probe)
    with pytest.raises(reference.ReferenceReviewError):
        reference.build_reference(fixture.destination, fixture.identity)
    assert fixture.calls == []


@pytest.mark.parametrize("text", (
    "import Lean.Data.Json PeanoLab.Syntax\n", " import Lean.Data.Json\n",
    "import\tLean.Data.Json\n", "import\nLean.Data.Json\n",
    "import Lean.Data.Json -- not canonical\n", "import Unreviewed.Module\n",
    "import PeanoLab.Verify\n",
))
def test_noncanonical_unapproved_or_forward_imports_are_rejected(mock_reference, text):
    fixture = mock_reference
    (fixture.project / reference.MODULES[0]).write_text(text, encoding="utf-8")
    with pytest.raises(reference.ReferenceReviewError, match="import"):
        reference.inspect_reference(fixture.project, fixture.compiler)
    assert fixture.calls == []


def test_multiline_axiom_footprint_is_fully_consumed_without_allowing_noise():
    output = _audit().replace("[propext, Classical.choice, Quot.sound]", "[propext,\n Classical.choice,\n Quot.sound]")
    assert set(reference.parse_axiom_audit(output)) == set(reference.AUDIT_DECLARATIONS)
    with pytest.raises(reference.ReferenceReviewError):
        reference.parse_axiom_audit(output.replace("\n Classical.choice", "\n unreviewedAxiom"))


def test_mock_cases_use_exact_paths_bounded_batches_and_revalidate_build(mock_reference):
    fixture = mock_reference
    build = _build(fixture)
    cases = _cases(reference.BATCH_SIZE + 1)
    result = reference.check_reference_cases(fixture.destination, fixture.identity, build, cases)
    assert result["status"] == "passed"
    assert len(result["worker_rows"]) == 2
    assert [len(row["case_ids"]) for row in result["worker_rows"]] == [reference.BATCH_SIZE, 1]
    assert [row["case_id"] for row in result["cases"]] == [case.case_id for case in cases]
    assert result["case_count"] == len(cases)
    assert all(row["artifact_sha256"] == sha256(case.artifact).hexdigest()
               for row, case in zip(result["cases"], cases))
    assert result["h0_complete"] is result["negative_theorem_claims"] is False
    assert result["model_calls"] == result["solver_calls"] == 0


def _refresh_worker_output(row):
    for stream in ("stdout", "stderr"):
        raw = row[stream].encode("utf-8")
        row[stream + "_bytes"] = len(raw)
        row[stream + "_sha256"] = sha256(raw).hexdigest()


def test_saved_reference_validators_need_neither_files_nor_executing_saved_commands(mock_reference, monkeypatch):
    fixture = mock_reference
    build = _build(fixture)
    cases = _cases()
    result = reference.check_reference_cases(fixture.destination, fixture.identity, build, cases)
    fixture.destination.rename(fixture.destination.with_name("moved-build"))
    fixture.compiler.rename(fixture.compiler.with_name("moved-compiler"))
    fixture.runtime.rename(fixture.runtime.with_name("moved-runtime"))
    def forbidden(*args, **kwargs):
        raise AssertionError("archived metadata validation must not read or execute saved paths")
    with monkeypatch.context() as pure:
        pure.setattr(reference, "hash_file", forbidden)
        pure.setattr(reference, "read_bytes", forbidden)
        pure.setattr(reference, "run_bounded", forbidden)
        pure.setattr(reference.subprocess, "run", forbidden)
        pure.setattr(Path, "resolve", forbidden)
        pure.setattr(Path, "exists", forbidden)
        assert reference.validate_build_receipt(fixture.identity, build) is None
        assert reference.validate_build_receipt(fixture.identity, build, build_directory=fixture.destination) is None
        assert reference.validate_reference_results(fixture.identity, result, cases) is None


@pytest.mark.parametrize("mutation", (
    "mixed_roots", "relative_root", "dotdot_root", "filesystem_root", "wrong_explicit_root",
    "missing_primary", "foreign_output", "invented_primary_hash", "inventory_digest",
    "compile_descriptor_claim", "inventory_descriptor_claim", "compile_nested_claim",
    "audit_nested_claim", "resource_nested_claim", "boolean_descriptor_size", "float_descriptor_size",
    "missing_stdin_digest", "changed_stdin_digest", "false_h0", "unknown_footprint",
))
def test_resealed_saved_build_attacks_fail_without_current_files(mock_reference, mutation):
    fixture = mock_reference
    build = _detached(_build(fixture))
    explicit = None
    primary = str(Path(reference.MODULES[0]).with_suffix(".olean"))
    if mutation == "mixed_roots":
        build["compile_rows"][1]["command"][4] = str(fixture.destination.parent / "another-build" / Path(reference.MODULES[1]).with_suffix(".olean"))
    elif mutation == "relative_root":
        build["compile_rows"][0]["command"][4] = primary
    elif mutation == "dotdot_root":
        build["compile_rows"][0]["command"][4] = str(fixture.destination) + "/../staged/" + primary
    elif mutation == "filesystem_root":
        for row in build["compile_rows"]:
            row["command"][4] = "/" + str(Path(row["module"]).with_suffix(".olean"))
    elif mutation == "wrong_explicit_root":
        explicit = fixture.destination.parent / "wrong-build"
    elif mutation == "missing_primary":
        build["compiled_files"].pop(primary)
    elif mutation == "foreign_output":
        build["compiled_files"]["PeanoLab/Foreign.olean"] = {"bytes": 1, "sha256": "0" * 64}
    elif mutation == "invented_primary_hash":
        build["compiled_files"][primary]["sha256"] = "0" * 64
    elif mutation == "inventory_digest":
        build["compiled_root_sha256"] = "0" * 64
    elif mutation == "compile_descriptor_claim":
        build["compile_rows"][0]["compiled_olean"]["h0_complete"] = True
    elif mutation == "inventory_descriptor_claim":
        build["compiled_files"][primary]["h0_complete"] = True
    elif mutation == "compile_nested_claim":
        build["compile_rows"][0]["h0_complete"] = True
    elif mutation == "audit_nested_claim":
        build["axiom_audit"]["research_claim_eligible"] = True
    elif mutation == "resource_nested_claim":
        build["compile_rows"][0]["resources"]["h0_complete"] = True
    elif mutation == "boolean_descriptor_size":
        build["compiled_files"][primary]["bytes"] = True
    elif mutation == "float_descriptor_size":
        build["compiled_files"][primary]["bytes"] = float(build["compiled_files"][primary]["bytes"])
    elif mutation == "missing_stdin_digest":
        build["compile_rows"][0].pop("stdin_sha256")
    elif mutation == "changed_stdin_digest":
        build["axiom_audit"]["stdin_sha256"] = "0" * 64
    elif mutation == "false_h0":
        build["h0_complete"] = True
    elif mutation == "unknown_footprint":
        build["axiom_footprint"]["unreviewedClaim"] = []
    if mutation != "inventory_digest":
        build["compiled_root_sha256"] = digest(build["compiled_files"])
    _reseal(build, "build_sha256")
    fixture.destination.rename(fixture.destination.with_name("moved-build"))
    with pytest.raises(reference.ReferenceReviewError):
        reference.validate_build_receipt(fixture.identity, build, build_directory=explicit)


@pytest.mark.parametrize("relative", ("PeanoLab/Syntax.lean", "PeanoLab/Syntax.olean", "HydraAxiomAudit.lean"))
def test_mutation_during_final_audit_cannot_publish_a_fresh_build(mock_reference, monkeypatch, relative):
    fixture = mock_reference
    def mutate_during_audit(command, **kwargs):
        result = fixture.run(command, **kwargs)
        if command[-1] == "HydraAxiomAudit.lean":
            (fixture.destination / relative).write_bytes(b"changed during final audit")
        return result
    monkeypatch.setattr(reference, "run_bounded", mutate_during_audit)
    with pytest.raises(reference.ReferenceReviewError):
        _build(fixture)


@pytest.mark.parametrize("mutation", (
    "source_descriptor_claim", "compiler_descriptor_claim", "runtime_descriptor_claim",
    "float_batch_size", "float_cpu_limit", "unknown_limit", "invented_claim_boundary",
))
def test_resealed_identity_rejects_nested_claims_and_inexact_numeric_types(mock_reference, mutation):
    identity = _detached(mock_reference.identity)
    if mutation == "source_descriptor_claim":
        identity["files"][reference.MODULES[0]]["h0_complete"] = True
        identity["source_root_sha256"] = digest(identity["files"])
    elif mutation == "compiler_descriptor_claim":
        identity["compiler"]["h0_complete"] = True
    elif mutation == "runtime_descriptor_claim":
        identity["runtime_library"]["h0_complete"] = True
    elif mutation == "float_batch_size":
        identity["batch_size"] = float(identity["batch_size"])
    elif mutation == "float_cpu_limit":
        identity["build_limits"]["cpu_seconds"] = float(identity["build_limits"]["cpu_seconds"])
    elif mutation == "unknown_limit":
        identity["check_limits"]["unlimited"] = True
    elif mutation == "invented_claim_boundary":
        identity["claim_boundary"] = "H0 complete"
    _reseal(identity, "reference_sha256")
    with pytest.raises(reference.ReferenceReviewError):
        reference.validate_reference_identity(identity)


@pytest.mark.parametrize("mutation", (
    "boolean_count", "float_count", "wrong_count", "boolean_model_calls", "float_solver_calls",
    "negative_claim_integer", "false_h0", "false_research_claim", "wrong_schema", "wrong_reference",
    "unknown_field", "missing_outcome", "duplicate_outcome", "boolean_agreement_as_int",
    "outcome_nested_claim", "changed_artifact_hash", "changed_case_id", "changed_expected",
    "invented_observed", "invented_mismatch", "invented_status", "missing_worker",
    "wrong_command", "wrong_path", "wrong_worker_case_id", "worker_nested_claim", "resource_nested_claim",
    "wrong_limits", "wrong_output_hash", "wrong_output_count", "wrong_exit_code", "wrong_fuel",
    "missing_stdin", "boolean_stdin_bytes", "wrong_stdin_digest",
))
def test_resealed_saved_results_cannot_change_counts_decisions_or_claims(mock_reference, mutation):
    fixture = mock_reference
    build = _build(fixture)
    cases = _cases()
    result = _detached(reference.check_reference_cases(fixture.destination, fixture.identity, build, cases))
    worker = result["worker_rows"][0]
    outcome = result["cases"][0]
    if mutation == "boolean_count":
        result["case_count"] = True
    elif mutation == "float_count":
        result["case_count"] = float(result["case_count"])
    elif mutation == "wrong_count":
        result["case_count"] += 1
    elif mutation == "boolean_model_calls":
        result["model_calls"] = False
    elif mutation == "float_solver_calls":
        result["solver_calls"] = 0.0
    elif mutation == "negative_claim_integer":
        result["negative_theorem_claims"] = 0
    elif mutation == "false_h0":
        result["h0_complete"] = True
    elif mutation == "false_research_claim":
        result["research_claim_eligible"] = True
    elif mutation == "wrong_schema":
        result["schema"] = "another-results-schema"
    elif mutation == "wrong_reference":
        result["reference_sha256"] = "0" * 64
    elif mutation == "unknown_field":
        result["unchecked_authority"] = True
    elif mutation == "missing_outcome":
        result["cases"] = []
    elif mutation == "duplicate_outcome":
        result["cases"].append(_detached(outcome))
    elif mutation == "boolean_agreement_as_int":
        outcome["agrees"] = 1
    elif mutation == "outcome_nested_claim":
        outcome["h0_complete"] = True
    elif mutation == "changed_artifact_hash":
        outcome["artifact_sha256"] = "0" * 64
    elif mutation == "changed_case_id":
        outcome["case_id"] = "different-case"
    elif mutation == "changed_expected":
        outcome["expected"] = "REJECT"
    elif mutation == "invented_observed":
        outcome["observed"] = "REJECT"
    elif mutation == "invented_mismatch":
        result["mismatches"] = [cases[0].case_id]
    elif mutation == "invented_status":
        result["status"] = "failed"
    elif mutation == "missing_worker":
        result["worker_rows"] = []
    elif mutation == "wrong_command":
        worker["command"][0] = "/unreviewed/lean"
    elif mutation == "wrong_path":
        worker["command"][-1] = "cases/case-99999.json"
    elif mutation == "wrong_worker_case_id":
        worker["case_ids"] = ["different-case"]
    elif mutation == "worker_nested_claim":
        worker["research_claim_eligible"] = True
    elif mutation == "resource_nested_claim":
        worker["resources"]["research_claim_eligible"] = True
    elif mutation == "wrong_limits":
        worker["limits"]["cpu_seconds"] += 1
    elif mutation == "wrong_output_hash":
        worker["stdout_sha256"] = "0" * 64
    elif mutation == "wrong_output_count":
        worker["stdout_bytes"] += 1
    elif mutation == "wrong_exit_code":
        worker["returncode"] = 1
    elif mutation == "wrong_fuel":
        worker["stdout"] = worker["stdout"].replace("fuel=4096", "fuel=0")
        _refresh_worker_output(worker)
    elif mutation == "missing_stdin":
        worker.pop("stdin_sha256")
    elif mutation == "boolean_stdin_bytes":
        worker["stdin_bytes"] = False
    elif mutation == "wrong_stdin_digest":
        worker["stdin_sha256"] = "0" * 64
    _reseal(result, "results_sha256")
    with pytest.raises(reference.ReferenceReviewError):
        reference.validate_reference_results(fixture.identity, result, cases)


def test_saved_failed_result_is_valid_evidence_but_cannot_be_resealed_as_passed(mock_reference, monkeypatch):
    fixture = mock_reference
    build = _build(fixture)
    def reject_case(command, **kwargs):
        row = fixture.run(command, **kwargs)
        row["stdout"] = row["stdout"].replace("ACCEPT", "REJECT")
        row["returncode"] = 1
        _refresh_worker_output(row)
        return row
    monkeypatch.setattr(reference, "run_bounded", reject_case)
    cases = _cases()
    result = reference.check_reference_cases(fixture.destination, fixture.identity, build, cases)
    assert result["status"] == "failed"
    assert result["mismatches"] == [cases[0].case_id]
    assert reference.validate_reference_results(fixture.identity, result, cases) is None
    result["status"] = "passed"
    result["mismatches"] = []
    result["cases"][0]["agrees"] = True
    _reseal(result, "results_sha256")
    with pytest.raises(reference.ReferenceReviewError):
        reference.validate_reference_results(fixture.identity, result, cases)


@pytest.mark.parametrize("mutation", ("reversed_workers", "reversed_ids", "duplicate_paths", "omitted_tail", "reordered_cases"))
def test_saved_results_bind_the_exact_64_plus_1_batch_partition(mock_reference, mutation):
    fixture = mock_reference
    build = _build(fixture)
    cases = _cases(reference.BATCH_SIZE + 1)
    result = reference.check_reference_cases(fixture.destination, fixture.identity, build, cases)
    if mutation == "reversed_workers":
        result["worker_rows"].reverse()
    elif mutation == "reversed_ids":
        result["worker_rows"][0]["case_ids"].reverse()
    elif mutation == "duplicate_paths":
        result["worker_rows"][0]["command"][-1] = result["worker_rows"][0]["command"][-2]
    elif mutation == "omitted_tail":
        result["worker_rows"].pop()
    elif mutation == "reordered_cases":
        result["cases"].reverse()
    _reseal(result, "results_sha256")
    with pytest.raises(reference.ReferenceReviewError):
        reference.validate_reference_results(fixture.identity, result, cases)


def test_mixed_saved_reference_results_preserve_decode_errors_and_actual_zero_fuel(mock_reference, monkeypatch):
    from training.peano_hydra.conformance import ConformanceCase
    fixture = mock_reference
    build = _build(fixture)
    positive = _cases()[0]
    cases = (
        positive,
        ConformanceCase("mutation", "fixture", 0, "certificate_mutation", "0 = 0", False,
                        "REJECT", positive.artifact),
        ConformanceCase("bad-wire", "fixture", 0, "wire_mutation", None, None,
                        "DECODE_ERROR", b"not-json\n"),
        ConformanceCase("zero-fuel", "fixture", 0, "wire_mutation", None, None,
                        "REJECT", positive.artifact.replace(b",4096,", b",0,")),
    )
    def mixed_worker(command, **kwargs):
        fixture.run(command, **kwargs)
        paths = command[5:]
        return _worker_receipt(command, kwargs["limits"], returncode=2,
                               stdout=f"ACCEPT\t{paths[0]}\tfuel=4096\nREJECT\t{paths[1]}\tfuel=4096\nREJECT\t{paths[3]}\tfuel=0\n",
                               stderr=f"DECODE_ERROR\t{paths[2]}\tinvalid JSON\n")
    monkeypatch.setattr(reference, "run_bounded", mixed_worker)
    result = reference.check_reference_cases(fixture.destination, fixture.identity, build, cases)
    assert result["status"] == "passed"
    assert [case["observed"] for case in result["cases"]] == ["ACCEPT", "REJECT", "DECODE_ERROR", "REJECT"]
    assert reference.validate_reference_results(fixture.identity, result, cases) is None


def _mock_historical_git(fixture, monkeypatch):
    """An explicit tiny immutable-object store, with every Git read inspected."""
    blobs = {relative: (fixture.project / relative).read_bytes() for relative in (*reference.MODULES, "lean-toolchain")}
    commit = fixture.identity["project_git_commit"]
    queries = []
    def git(project, *arguments):
        assert Path(project) == fixture.project.resolve()
        queries.append(arguments)
        if arguments == ("rev-parse", "--verify", f"{commit}^{{commit}}"):
            return commit
        assert arguments[:2] in (("cat-file", "-t"), ("cat-file", "-s"))
        assert arguments[2].startswith(commit + ":")
        relative = arguments[2].split(":", 1)[1]
        assert relative in blobs
        return "blob" if arguments[1] == "-t" else str(len(blobs[relative]))
    def read_blob(project, *arguments, maximum):
        assert Path(project) == fixture.project.resolve()
        assert arguments[:2] == ("cat-file", "blob")
        assert arguments[2].startswith(commit + ":")
        relative = arguments[2].split(":", 1)[1]
        assert maximum == (4096 if relative == "lean-toolchain" else reference.MAX_SOURCE_BYTES)
        queries.append(arguments)
        return blobs[relative]
    monkeypatch.setattr(reference, "_git", git)
    monkeypatch.setattr(reference, "bounded_git", read_blob)
    return SimpleNamespace(blobs=blobs, queries=queries, git=git)


def test_historical_reference_provenance_ignores_later_head_and_worktree_edits(mock_reference, monkeypatch):
    fixture = mock_reference
    historical = _mock_historical_git(fixture, monkeypatch)
    (fixture.project / reference.MODULES[0]).write_text("later unrelated worktree edit\n", encoding="utf-8")
    (fixture.project / "lean-toolchain").write_text("leanprover/lean4:v4.99.0\n", encoding="utf-8")
    assert reference.validate_reference_provenance(fixture.project, fixture.identity) is None
    assert len(historical.queries) == 1 + 3 * (len(reference.MODULES) + 1)
    assert all("HEAD" not in argument and argument != "status" for query in historical.queries for argument in query)


def test_resealed_toolchain_pin_cannot_pretend_the_historical_compiler_matched(mock_reference, monkeypatch):
    fixture = mock_reference
    (fixture.project / "lean-toolchain").write_text("leanprover/lean4:v4.31.0\n", encoding="utf-8")
    fixture.identity = reference.inspect_reference(fixture.project, fixture.compiler)
    assert fixture.identity["matches_project_toolchain_pin"] is False
    _mock_historical_git(fixture, monkeypatch)
    assert reference.validate_reference_provenance(fixture.project, fixture.identity) is None
    forged = _detached(fixture.identity)
    forged["project_toolchain_pin"] = "leanprover/lean4:v4.28.0"
    forged["matches_project_toolchain_pin"] = True
    _reseal(forged, "reference_sha256")
    assert reference.validate_reference_identity(forged) is None
    with pytest.raises(reference.ReferenceReviewError, match="historical toolchain pin"):
        reference.validate_reference_provenance(fixture.project, forged)


@pytest.mark.parametrize("mutation", ("dirty", "missing_commit", "changed_source", "wrong_blob_type", "oversized_blob", "changed_pin"))
def test_historical_reference_provenance_rejects_false_or_unbounded_git_evidence(mock_reference, monkeypatch, mutation):
    fixture = mock_reference
    historical = _mock_historical_git(fixture, monkeypatch)
    identity = _detached(fixture.identity)
    if mutation == "dirty":
        identity["project_git_dirty"] = True
        _reseal(identity, "reference_sha256")
    elif mutation == "missing_commit":
        def missing(*args):
            raise reference.subprocess.CalledProcessError(128, "git rev-parse")
        monkeypatch.setattr(reference, "_git", missing)
    elif mutation == "changed_source":
        historical.blobs[reference.MODULES[0]] = b"different historical source\n"
    elif mutation in {"wrong_blob_type", "oversized_blob"}:
        def invalid_metadata(project, *arguments):
            if arguments[:2] == ("cat-file", "-t") and mutation == "wrong_blob_type":
                return "tree"
            if arguments[:2] == ("cat-file", "-s") and mutation == "oversized_blob":
                return str(reference.MAX_SOURCE_BYTES + 1)
            return historical.git(project, *arguments)
        monkeypatch.setattr(reference, "_git", invalid_metadata)
    elif mutation == "changed_pin":
        historical.blobs["lean-toolchain"] = b"leanprover/lean4:v4.29.0\n"
    with pytest.raises(reference.ReferenceReviewError):
        reference.validate_reference_provenance(fixture.project, identity)
    if mutation == "dirty":
        assert historical.queries == []
    if mutation in {"wrong_blob_type", "oversized_blob"}:
        assert not any(query[:2] == ("cat-file", "blob") for query in historical.queries)


def test_all_reference_git_reads_use_the_shared_project_bound_reader(tmp_path, monkeypatch):
    project = tmp_path / "companion"
    project.mkdir()
    commit = "c" * 40
    data = b"test-only historical source\n"
    requests = []
    def bounded_git(project_argument, *arguments, maximum):
        assert project_argument == project
        requests.append((arguments, maximum))
        if arguments == ("rev-parse", "HEAD"):
            return commit.encode() + b"\n"
        assert arguments[0] == "cat-file"
        assert arguments[2] == commit + ":PeanoLab/Syntax.lean"
        if arguments[1] == "-t":
            return b"blob\n"
        if arguments[1] == "-s":
            return str(len(data)).encode() + b"\n"
        assert arguments[1] == "blob" and maximum == reference.MAX_SOURCE_BYTES
        return data
    def forbidden(*args, **kwargs):
        raise AssertionError("reference must not bypass the shared bounded Git reader")
    monkeypatch.setattr(reference, "bounded_git", bounded_git)
    monkeypatch.setattr(reference.subprocess, "run", forbidden)
    assert reference._git(project, "rev-parse", "HEAD") == commit
    assert reference._historical_blob(project, commit, "PeanoLab/Syntax.lean", maximum=reference.MAX_SOURCE_BYTES) == data
    assert len(requests) == 4 and all(0 < limit <= 4 * 1024**2 for _, limit in requests)


def test_shared_git_reader_failure_remains_a_reference_admission_error(tmp_path, monkeypatch):
    def unavailable(*args, **kwargs):
        raise reference.ReviewSourceError("test-only missing historical object")
    monkeypatch.setattr(reference, "bounded_git", unavailable)
    with pytest.raises(reference.ReferenceReviewError):
        reference._git(tmp_path, "rev-parse", "HEAD")
