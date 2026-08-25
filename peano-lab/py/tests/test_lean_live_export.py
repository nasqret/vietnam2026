"""Standalone Lean Live proofs and progress never invent compilation authority."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import re
import signal
import subprocess
from urllib.parse import unquote, urlsplit

import pytest

from peano_lab.library import lean_proof_strand
from peano_lab.library.lean_proof_strand import (
    DEFAULT_LIVE_URL_BYTES,
    LIVE_EXPORT_SCHEMA,
    ProofStrandError,
    ProofStrandLimitError,
    build_live_export,
    build_proof_strand,
    live_hosted_url,
    plan_proof_strand,
)


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "scripts" / "export_peano_lean.py"


@pytest.fixture(scope="module")
def exporter():
    specification = importlib.util.spec_from_file_location("peano_lean_live_cli", CLI)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def addition():
    plan = plan_proof_strand("add_comm")
    return plan, build_proof_strand(plan)


@pytest.mark.parametrize("theorem", ("add_comm", "mul_comm"))
def test_real_complete_arithmetic_strands_fit_a_working_lean_live_link(theorem: str) -> None:
    plan = plan_proof_strand(theorem)
    package = build_proof_strand(plan)
    live = build_live_export(plan, package)

    assert live.url_status == "ready"
    assert live.url is not None
    assert live.url_bytes <= DEFAULT_LIVE_URL_BYTES
    actual = urlsplit(live.url)
    assert actual.scheme == "https"
    assert actual.hostname == "live.lean-lang.org"
    assert actual.path == "/"
    assert actual.fragment.startswith("code=")
    assert unquote(actual.fragment[5:]) == live.source
    assert "import Lean.Elab.Tactic\n" in live.source
    assert "import PeanoLab" not in live.source
    assert "import Mathlib" not in live.source
    assert "PeanoLab.Codec" not in live.source
    assert "PeanoLab.Artifact" not in live.source
    assert "sorry" not in live.source
    assert "native_decide" not in live.source
    assert re.search(r"(?m)^\s*axiom\b", live.source) is None
    assert f"theorem «{theorem}»" in live.source


@pytest.mark.parametrize(
    ("theorem", "required", "unrelated"),
    (
        ("le_zero", "def Le (a b : Nat)", "def Prime"),
        ("prime_nonzero", "def Prime (p : Nat)", "def QRes"),
        ("qres_mod3_one", "def QRes (m a : Nat)", "def Product"),
    ),
)
def test_live_definitions_are_exact_and_dependency_pruned(
    theorem: str,
    required: str,
    unrelated: str,
) -> None:
    plan = plan_proof_strand(theorem)
    live = build_live_export(plan, build_proof_strand(plan))

    assert required in live.source
    assert unrelated not in live.source


def test_only_actual_proven_arithmetic_foundations_are_inlined() -> None:
    plan = plan_proof_strand("succ_ne_zero")
    live = build_live_export(plan, build_proof_strand(plan))

    assert "theorem pa1_sound" in live.source
    assert "theorem pa2_sound" not in live.source
    assert "theorem pa3_sound" not in live.source


def test_live_manifest_never_claims_remote_compilation(addition) -> None:
    plan, package = addition
    actual = build_live_export(plan, package)

    assert actual.manifest["schema"] == LIVE_EXPORT_SCHEMA
    assert actual.manifest["theorem"] == "add_comm"
    assert actual.manifest["source_sha256"] == sha256(actual.source.encode()).hexdigest()
    assert actual.manifest["source_bytes"] == actual.source_bytes
    assert actual.manifest["share_url"] == actual.url
    assert actual.manifest["remote_compilation"] == "not_run"
    assert actual.manifest["fallback_node_count"] == 0
    assert all(value is False for value in actual.manifest["authority"].values())


def test_segmented_topological_proofs_are_flattened_without_private_imports() -> None:
    plan = plan_proof_strand("mul_comm")
    package = build_proof_strand(plan, chunk_max_bytes=14_000)
    assert package.manifest["chunk_count"] > 0

    live = build_live_export(plan, package)

    assert live.url_status == "ready"
    assert "import PeanoLab" not in live.source
    assert "theorem «mul_zero_left»" in live.source
    assert "theorem «mul_comm»" in live.source


def test_any_checked_certificate_fallback_is_honestly_unavailable() -> None:
    plan = plan_proof_strand("zero_add")
    package = build_proof_strand(plan, force_fallback_names=frozenset({"zero_add"}))

    with pytest.raises(ProofStrandError, match="certificate fallbacks"):
        build_live_export(plan, package)


@pytest.mark.parametrize("field", ("schema", "name", "identity_sha256"))
def test_forged_manifest_identity_is_rejected(addition, field: str) -> None:
    plan, package = addition
    manifest = deepcopy(package.manifest)
    manifest[field] = "forged"

    with pytest.raises(ProofStrandError):
        build_live_export(plan, replace(package, manifest=manifest))


@pytest.mark.parametrize("value", (True, -1, 1))
def test_forged_or_unavailable_fallback_counts_are_rejected(addition, value: object) -> None:
    plan, package = addition
    manifest = deepcopy(package.manifest)
    manifest["fallback_node_count"] = value

    with pytest.raises(ProofStrandError):
        build_live_export(plan, replace(package, manifest=manifest))


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("name", "wrong"),
        ("proof_status", "local_checked_certificate"),
        ("source_line_start", True),
        ("source_line_start", 0),
        ("source_line_end", 1_000_000),
        ("generated_relative_path", "../../stolen.lean"),
    ),
)
def test_forged_source_intervals_fail_closed(addition, field: str, value: object) -> None:
    plan, package = addition
    manifest = deepcopy(package.manifest)
    manifest["nodes"][0][field] = value

    with pytest.raises(ProofStrandError):
        build_live_export(plan, replace(package, manifest=manifest))


def test_tampered_generated_source_is_rejected_before_extraction(addition) -> None:
    plan, package = addition
    path, source = package.generated_files[0]
    changed = replace(package, generated_files=((path, source + "\n-- modified"),))

    with pytest.raises(ProofStrandError, match="source digest"):
        build_live_export(plan, changed)


def test_oversized_url_keeps_downloadable_source_without_fake_link(addition) -> None:
    plan, package = addition
    actual = build_live_export(plan, package, max_url_bytes=128)

    assert actual.url is None
    assert actual.url_status == "oversized"
    assert actual.manifest["share_url"] is None
    assert actual.manifest["remote_compilation"] == "not_run"
    assert actual.source.startswith("-- Standalone constructive")


@pytest.mark.parametrize("limit", (True, 0, -1, 16_385))
def test_unsafe_live_url_bounds_are_rejected(addition, limit: object) -> None:
    plan, package = addition
    with pytest.raises(ProofStrandError):
        build_live_export(plan, package, max_url_bytes=limit)  # type: ignore[arg-type]


def test_oversized_source_is_refused_before_an_unbounded_live_export(addition) -> None:
    plan, package = addition
    with pytest.raises(ProofStrandLimitError, match="byte"):
        build_live_export(plan, package, max_source_bytes=128)


def test_metadata_planning_and_local_build_report_exact_progress() -> None:
    planning: list[dict[str, object]] = []
    plan = plan_proof_strand("add_comm", progress=planning.append)
    generation: list[dict[str, object]] = []
    build_proof_strand(plan, progress=generation.append)

    assert planning[0]["stage"] == "plan"
    assert planning[-1]["completed"] == planning[-1]["total"] == 3
    translated = [event for event in generation if event["stage"] == "translate"]
    assert [event["completed"] for event in translated] == [0, 1, 2, 3]
    assert generation[-1]["stage"] == "package"
    assert all(event["kind"] == "lean_strand_progress" for event in [*planning, *generation])


def test_local_certificate_progress_is_explicit_and_never_claims_compilation() -> None:
    plan = plan_proof_strand("zero_add")
    events: list[dict[str, object]] = []
    build_proof_strand(
        plan,
        force_fallback_names=frozenset({"zero_add"}),
        progress=events.append,
    )

    stages = [event["stage"] for event in events]
    assert stages.count("certificate") == 2
    assert "compile" not in stages


@pytest.mark.parametrize("callback", (True, "print", 3))
def test_non_callable_progress_is_rejected(callback: object, addition) -> None:
    plan, _package = addition
    with pytest.raises(ProofStrandError, match="callable"):
        plan_proof_strand("add_comm", progress=callback)  # type: ignore[arg-type]
    with pytest.raises(ProofStrandError, match="callable"):
        build_proof_strand(plan, progress=callback)  # type: ignore[arg-type]


def test_hosted_url_only_hands_off_an_explicit_public_https_lean_file() -> None:
    source = "https://proofs.example.org/theorems/add_comm.lean"
    actual = live_hosted_url(source)

    assert actual.startswith("https://live.lean-lang.org/#url=")
    assert unquote(urlsplit(actual).fragment[4:]) == source


@pytest.mark.parametrize(
    "source",
    (
        "http://proofs.example.org/a.lean",
        "https://localhost/a.lean",
        "https://127.0.0.1/a.lean",
        "https://10.0.0.1/a.lean",
        "https://192.168.1.4/a.lean",
        "https://[::1]/a.lean",
        "https://reviewer.local/a.lean",
        "https://user:secret@proofs.example.org/a.lean",
        "https://proofs.example.org/a.lean#secret",
        "https://proofs.example.org/a.txt",
    ),
)
def test_hosted_handoff_refuses_non_public_or_non_lean_sources(source: str) -> None:
    with pytest.raises(ProofStrandError):
        live_hosted_url(source)


def test_direct_live_cli_emits_only_source_on_stdout_and_json_on_stderr(
    exporter,
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert exporter.main(["add_comm", "--format", "live", "--progress-json"]) == 0
    captured = capsys.readouterr()
    assert captured.out.startswith("-- Standalone constructive")
    assert "import Lean.Elab.Tactic" in captured.out
    events = [json.loads(line) for line in captured.err.splitlines() if line.startswith("{")]
    assert events[0]["stage"] == "plan"
    assert events[-1]["stage"] == "complete"
    assert events[-1]["live_status"] == "ready"
    assert events[-1]["remote_compilation"] == "not_run"
    assert events[-1]["local_source_verified"] is False


def test_strand_cli_writes_live_source_and_truthful_unverified_sidecar(
    exporter,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    source = tmp_path / "live.lean"
    package = tmp_path / "package"
    assert exporter.main(
        [
            "add_comm",
            "--format",
            "strand",
            "--package-dir",
            str(package),
            "--live-lean-output",
            str(source),
            "--progress-json",
        ]
    ) == 0

    receipt = json.loads((tmp_path / "live.json").read_text(encoding="utf-8"))
    payload = source.read_bytes()
    assert receipt["source_sha256"] == sha256(payload).hexdigest()
    assert receipt["source_bytes"] == len(payload)
    assert receipt["local_source_verified"] is False
    assert receipt["remote_compilation"] == "not_run"
    assert "PeanoLab.Codec" not in payload.decode()
    completed = [
        json.loads(line)
        for line in capsys.readouterr().err.splitlines()
        if line.startswith("{")
    ][-1]
    assert completed["stage"] == "complete"
    assert completed["live_status"] == "ready"
    assert completed["local_source_verified"] is False


def test_verified_strand_checks_live_source_sequentially_with_shared_policy(
    exporter,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, int]] = []

    def checked_package(*_args: object, **kwargs: object) -> None:
        calls.append(("package", int(kwargs["max_memory_mib"])))

    def checked_live(source: Path, *_args: object, **kwargs: object) -> None:
        assert source == tmp_path / "live.lean"
        calls.append(("standalone", int(kwargs["max_memory_mib"])))

    monkeypatch.setattr(exporter, "_verify_presentation_package", checked_package)
    monkeypatch.setattr(exporter, "_verify", checked_live)
    monkeypatch.setattr(exporter, "_lake_binary", lambda *_args: Path("/mock/lake"))
    assert exporter.main(
        [
            "add_comm",
            "--format",
            "strand",
            "--package-dir",
            str(tmp_path / "package"),
            "--verify",
            "--max-memory-mib",
            "1024",
            "--live-lean-output",
            str(tmp_path / "live.lean"),
        ]
    ) == 0

    assert calls == [("package", 1024), ("standalone", 1024)]
    receipt = json.loads((tmp_path / "live.json").read_text(encoding="utf-8"))
    assert receipt["local_source_verified"] is True
    assert receipt["remote_compilation"] == "not_run"


@pytest.mark.parametrize(
    "arguments",
    (
        ("--format", "full", "--progress-json"),
        ("--format", "outline", "--live-lean-output", "live.lean"),
        ("--format", "live", "--package-dir", "package"),
        ("--format", "strand", "--max-live-url-bytes", "127"),
    ),
)
def test_incompatible_live_cli_flags_are_rejected(exporter, arguments: tuple[str, ...]) -> None:
    assert exporter.main(["add_comm", *arguments]) == 1


def test_sigterm_propagates_into_the_private_lean_process_group(
    exporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[int, int]] = []

    class Running:
        pid = 12345

        def poll(self):
            return None

        def wait(self, *, timeout: int):
            assert timeout == 2
            return 0

    monkeypatch.setattr(exporter, "_ACTIVE_VERIFIER_PROCESS", Running())
    monkeypatch.setattr(exporter.os, "killpg", lambda pid, sig: calls.append((pid, sig)))
    with pytest.raises(SystemExit) as terminated:
        exporter._cancel_active_verifier(signal.SIGTERM, None)

    assert terminated.value.code == 128 + signal.SIGTERM
    assert calls == [(12345, signal.SIGTERM)]


def test_sigterm_escalates_a_stuck_nested_lean_group_without_orphans(
    exporter,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[int, int]] = []

    class Stuck:
        pid = 54321

        def poll(self):
            return None

        def wait(self, *, timeout: int):
            raise subprocess.TimeoutExpired("lean", timeout)

    monkeypatch.setattr(exporter, "_ACTIVE_VERIFIER_PROCESS", Stuck())
    monkeypatch.setattr(exporter.os, "killpg", lambda pid, sig: calls.append((pid, sig)))
    with pytest.raises(SystemExit):
        exporter._cancel_active_verifier(signal.SIGTERM, None)

    assert calls == [(54321, signal.SIGTERM), (54321, signal.SIGKILL)]


def test_live_export_never_replays_local_or_closed_proofs(
    addition,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plan, package = addition

    def forbidden(*_args: object, **_kwargs: object):
        raise AssertionError("standalone Lean Live generation must never replay a proof")

    monkeypatch.setattr(lean_proof_strand, "_checked_local_body", forbidden)
    monkeypatch.setattr(lean_proof_strand, "start", forbidden)
    actual = build_live_export(plan, package)

    assert actual.url_status == "ready"
