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
    DEFAULT_LIVE_SOURCE_BYTES,
    DEFAULT_LIVE_URL_BYTES,
    LIVE_EXPORT_SCHEMA,
    MAX_LIVE_CODEC_SOURCE_BYTES,
    MAX_LIVE_URL_BYTES,
    ProofStrandError,
    ProofStrandLimitError,
    build_live_export,
    build_proof_strand,
    compress_lean_live_codez,
    decompress_lean_live_codez,
    live_hosted_url,
    plan_proof_strand,
    select_live_share_url,
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


@pytest.mark.parametrize(
    ("source", "compressed"),
    (
        ("", "Q"),
        ("hello", "BYUwNmD2Q"),
        ("Hello, world!", "BIUwNmD2A0AEDukBOYAmBCIA"),
        ("nnnnnnnnnnnnnnnn13", "HY1/AjAzEA"),
        ("qqqqqqqqqqqqqqqqqq16", "I41+gjAbEA"),
        (
            "theorem checked : True := by trivial\n",
            "C4Cwpg9gTmC2AEBjciDWYAm8Bc8AqUArmDgLzwBGAnvMFAJYBu9AhgDYBQQA",
        ),
        (
            "import Lean.Elab.Tactic\n\ntheorem checked : True := by trivial\n",
            "JYWwDg9gTgLgBAGQKYEMB2A6AogGxQIwwBUUBjGYUgKCpgAslokQ5SHSBrJAEzgC44RKAFck/ALxx8ATzgwowAG7AUOKkA",
        ),
    ),
)
def test_official_lz_string_unpadded_base64_fixtures_are_exactly_interoperable(
    source: str,
    compressed: str,
) -> None:
    assert compress_lean_live_codez(source) == compressed
    assert decompress_lean_live_codez(
        compressed,
        max_output_bytes=max(1, len(source.encode("utf-8"))),
    ) == source


@pytest.mark.parametrize(
    "source",
    (
        "a",
        "a" * 4096,
        "∀ n : Nat, n = n",
        "🙂 ∀ ∃ 𝄞 e\u0301",
        "🙂" * 128,
        "\x00\n\t\x7f\u0080\u0800\uffff",
    ),
)
def test_codez_decodes_at_the_exact_utf8_byte_limit(source: str) -> None:
    compressed = compress_lean_live_codez(source)

    assert decompress_lean_live_codez(
        compressed,
        max_output_bytes=len(source.encode("utf-8")),
    ) == source


@pytest.mark.parametrize(
    "payload",
    (
        "",
        " ",
        "BYUwNmD2Q=",
        "BYUwNmD2Q/",
        "BYUwNmD2Q_",
        "HY1-AjAzEA",
        "BYUwNmD2Q-",
        "BYUwNmD2Q%20",
        "BYUwNmD2Q#",
        "$",
        "BYUwNmD2Q$",
        "BYUwNmD2",
        "BYUwNmD2QA",
        "A" * (MAX_LIVE_URL_BYTES + 1),
    ),
)
def test_codez_refuses_malformed_truncated_or_noncanonical_payloads(payload: str) -> None:
    with pytest.raises(ProofStrandError):
        decompress_lean_live_codez(payload)


def test_official_base64_alphabet_has_slash_not_uri_variant_minus() -> None:
    alphabet = lean_proof_strand._LIVE_LZ_ALPHABET

    assert len(alphabet) == 64
    assert alphabet.index("+") == 62
    assert alphabet.index("/") == 63
    assert "-" not in alphabet
    assert "$" not in alphabet
    for source in ("hello", "🙂 ∀ ∃", "n" * 1024):
        assert "$" not in compress_lean_live_codez(source)
        assert "-" not in compress_lean_live_codez(source)
    for invalid in ("$", "HY1-AjAzEA"):
        with pytest.raises(ProofStrandError, match="Base64"):
            decompress_lean_live_codez(invalid)


@pytest.mark.parametrize("limit", (True, 0, -1, 4_194_305))
def test_codez_limits_refuse_boolean_or_unbounded_values(limit: object) -> None:
    with pytest.raises(ProofStrandError):
        compress_lean_live_codez("a", max_input_bytes=limit)  # type: ignore[arg-type]
    with pytest.raises(ProofStrandError):
        decompress_lean_live_codez("BYUwNmD2Q", max_output_bytes=limit)  # type: ignore[arg-type]


def test_codez_refuses_a_compressed_expansion_bomb_before_materialization() -> None:
    source = "proof " * 4096
    compressed = compress_lean_live_codez(source)

    assert len(compressed) < 1024
    with pytest.raises(ProofStrandLimitError, match="output byte"):
        decompress_lean_live_codez(compressed, max_output_bytes=512)


def test_codez_enforces_actual_multibyte_utf8_not_only_utf16_units() -> None:
    source = "🙂" * 128
    compressed = compress_lean_live_codez(source)

    with pytest.raises(ProofStrandLimitError, match="output byte"):
        decompress_lean_live_codez(compressed, max_output_bytes=4 * 128 - 1)


@pytest.mark.parametrize("source", ("\ud800", "\udfff"))
def test_codez_refuses_invalid_unpaired_unicode_surrogates(source: str) -> None:
    with pytest.raises(ProofStrandError, match="surrogate"):
        compress_lean_live_codez(source)


def test_shortest_share_uses_direct_code_when_compression_is_longer() -> None:
    url, encoding, actual = select_live_share_url("")

    assert encoding == "code"
    assert url == "https://live.lean-lang.org/#code="
    assert actual == len(url)


def test_compression_makes_a_previously_oversized_exact_source_shareable() -> None:
    source = "∀" * 60_000

    direct = lean_proof_strand.live_lean_url(source)
    url, encoding, actual = select_live_share_url(source)

    assert len(direct.encode("utf-8")) > DEFAULT_LIVE_URL_BYTES
    assert url is not None and actual <= DEFAULT_LIVE_URL_BYTES
    assert encoding == "codez"
    assert decompress_lean_live_codez(
        unquote(urlsplit(url).fragment.removeprefix("codez=")),
        max_output_bytes=len(source.encode("utf-8")),
    ) == source


def test_campaign_live_limits_are_explicitly_large_but_hard_bounded() -> None:
    assert DEFAULT_LIVE_SOURCE_BYTES == 1_048_576
    assert DEFAULT_LIVE_URL_BYTES == 512 * 1024
    assert MAX_LIVE_URL_BYTES == 1_048_576
    assert MAX_LIVE_CODEC_SOURCE_BYTES == 4 * 1_048_576

    url, encoding, actual = select_live_share_url(
        "theorem checked : True := by trivial\n" * 20,
        max_url_bytes=MAX_LIVE_URL_BYTES,
        max_source_bytes=MAX_LIVE_CODEC_SOURCE_BYTES,
    )
    assert url is not None and encoding == "codez"
    assert actual <= MAX_LIVE_URL_BYTES


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
    encoding, payload = actual.fragment.split("=", 1)
    assert encoding in {"code", "codez"}
    if encoding == "code":
        assert unquote(payload) == live.source
    else:
        assert re.fullmatch(r"(?:[A-Za-z0-9]|%2B|%2F)+", payload)
        assert decompress_lean_live_codez(
            unquote(payload),
            max_output_bytes=live.source_bytes,
        ) == live.source
    assert live.manifest["share_encoding"] == encoding
    assert re.search(r"(?m)^\s*import\b", live.source) is None
    assert "import PeanoLab" not in live.source
    assert "import Mathlib" not in live.source
    assert "PeanoLab.Codec" not in live.source
    assert "PeanoLab.Artifact" not in live.source
    assert "sorry" not in live.source
    assert "native_decide" not in live.source
    assert re.search(r"(?m)^\s*axiom\b", live.source) is None
    assert f"theorem «{theorem}»" in live.source


def test_pa000g_compressed_share_preserves_every_arithmetic_identifier() -> None:
    plan = plan_proof_strand("mul_succ_left")
    package = build_proof_strand(plan)
    live = build_live_export(plan, package)

    assert plan.node_count == 5
    assert package.manifest["fallback_node_count"] == 0
    assert live.url is not None and live.manifest["share_encoding"] == "codez"
    encoded = urlsplit(live.url).fragment.removeprefix("codez=")
    assert "%2F" in encoded and "%2B" in encoded
    assert re.fullmatch(r"(?:[A-Za-z0-9]|%2B|%2F)+", encoded)
    raw = unquote(encoded)
    assert "/" in raw and "+" in raw
    assert "-" not in raw and "=" not in raw
    decoded = decompress_lean_live_codez(raw, max_output_bytes=live.source_bytes)
    assert decoded == live.source
    assert "theorem pa5_sound" in decoded
    assert "theorem pa6_sound" in decoded
    assert "theorem «mul_succ_left»" in decoded


@pytest.mark.parametrize(
    ("source", "required_escape"),
    (
        ("nnnnnnnnnnnnnnnn13", "%2F"),
        ("qqqqqqqqqqqqqqqqqq16", "%2B"),
    ),
)
def test_official_fragment_percent_encodes_reserved_base64_characters(
    source: str,
    required_escape: str,
) -> None:
    url, encoding, _actual = select_live_share_url(source)

    assert encoding == "codez" and url is not None
    fragment = urlsplit(url).fragment.removeprefix("codez=")
    assert required_escape in fragment
    assert re.fullmatch(r"(?:[A-Za-z0-9]|%2B|%2F)+", fragment)
    assert decompress_lean_live_codez(
        unquote(fragment),
        max_output_bytes=len(source.encode("utf-8")),
    ) == source


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
    assert actual.manifest["self_contained"] is True
    assert actual.manifest["core_imports"] == []
    assert actual.manifest["external_import_count"] == 0
    assert actual.manifest["share_url"] == actual.url
    assert actual.manifest["share_encoding"] == "codez"
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


@pytest.mark.parametrize(
    "injected",
    (
        "import Lean.Elab.Tactic",
        "import Init",
        "import Mathlib",
        "import PeanoLab.Codec",
    ),
)
def test_every_explicit_core_external_or_private_import_fails_closed(
    addition,
    monkeypatch: pytest.MonkeyPatch,
    injected: str,
) -> None:
    plan, package = addition
    monkeypatch.setattr(
        lean_proof_strand,
        "_live_node_blocks",
        lambda *_args: ([[injected]], set()),
    )

    with pytest.raises(ProofStrandError, match="unsafe dependency"):
        build_live_export(plan, package)


def test_alpha_pythagorean_dependency_strand_is_import_free_and_compressed() -> None:
    plan = plan_proof_strand("pythagorean_double_product", edition="alpha")
    package = build_proof_strand(plan)
    live = build_live_export(plan, package)

    assert plan.node_count == 9
    assert package.manifest["fallback_node_count"] == 0
    assert live.manifest["share_encoding"] == "codez"
    assert live.url is not None and live.url_bytes <= DEFAULT_LIVE_URL_BYTES
    assert re.search(r"(?m)^\s*import\b", live.source) is None
    assert "theorem «pythagorean_double_product»" in live.source
    assert decompress_lean_live_codez(
        unquote(urlsplit(live.url).fragment.removeprefix("codez=")),
        max_output_bytes=live.source_bytes,
    ) == live.source


def test_oversized_url_keeps_downloadable_source_without_fake_link(addition) -> None:
    plan, package = addition
    actual = build_live_export(plan, package, max_url_bytes=128)

    assert actual.url is None
    assert actual.url_status == "oversized"
    assert actual.manifest["share_url"] is None
    assert actual.manifest["share_encoding"] is None
    assert actual.manifest["remote_compilation"] == "not_run"
    assert actual.source.startswith("-- Standalone constructive")


@pytest.mark.parametrize("limit", (True, 0, -1, MAX_LIVE_URL_BYTES + 1))
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
    assert re.search(r"(?m)^\s*import\b", captured.out) is None
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
    assert receipt["self_contained"] is True
    assert receipt["external_import_count"] == 0
    assert receipt["core_imports"] == []
    assert receipt["share_encoding"] == "codez"
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
