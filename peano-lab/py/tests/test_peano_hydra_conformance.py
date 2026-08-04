"""Focused contracts for the deterministic Peano Hydra H0.2 campaign."""

from __future__ import annotations

from collections import Counter
import hashlib
import json
from pathlib import Path
from runpy import run_path
import subprocess
from threading import Lock
from time import sleep

import pytest


ROOT = Path(__file__).resolve().parents[3]
SCRIPT = run_path(str(ROOT / "scripts" / "validate_peano_hydra_h0.py"))
ExternalVerifierSuite = SCRIPT["ExternalVerifierSuite"]
H0ValidationError = SCRIPT["H0ValidationError"]
REPORT_VERSION = SCRIPT["REPORT_VERSION"]
REVIEWED_LEAN_SOURCE_COMMIT = SCRIPT["REVIEWED_LEAN_SOURCE_COMMIT"]
REVIEWED_LEAN_SOURCE_MANIFEST_SHA256 = SCRIPT[
    "REVIEWED_LEAN_SOURCE_MANIFEST_SHA256"
]
REVIEWED_LEAN_VERIFIER_SHA256 = SCRIPT["REVIEWED_LEAN_VERIFIER_SHA256"]
RUST_MAX_DEPTH = SCRIPT["RUST_MAX_DEPTH"]
RUST_MAX_WIRE_NAT = SCRIPT["RUST_MAX_WIRE_NAT"]
WASM_MAX_DEPTH = SCRIPT["WASM_MAX_DEPTH"]
WASM_MAX_PORTABLE_INDEX = SCRIPT["WASM_MAX_PORTABLE_INDEX"]
WASM_MAX_WIRE_NAT = SCRIPT["WASM_MAX_WIRE_NAT"]
_campaign_eligibility = SCRIPT["_campaign_eligibility"]
_envelope_reason = SCRIPT["_envelope_reason"]
_inspect_lean_source_identity = SCRIPT["_inspect_lean_source_identity"]
_lean_source_identity = SCRIPT["_lean_source_identity"]
_macro_protocol_controls = SCRIPT["_macro_protocol_controls"]
_require_unchanged_repository = SCRIPT["_require_unchanged_repository"]
_run_macro_focused_tests = SCRIPT["_run_macro_focused_tests"]
_run_required_regressions = SCRIPT["_run_required_regressions"]
_schema_controls = SCRIPT["_schema_controls"]
_source_manifest = SCRIPT["_source_manifest"]
_spawn_cold_worker = SCRIPT["_spawn_cold_worker"]
compare_cold_replays = SCRIPT["compare_cold_replays"]
run_cold_replay_pair = SCRIPT["run_cold_replay_pair"]

from peano_lab.kernel.formulas import pretty_formula  # noqa: E402
from training.peano_hydra.conformance import (  # noqa: E402
    ArtifactCase,
    ConformanceError,
    FULL_POSITIVE_COUNT,
    GENERATED_COUNT,
    GENERATED_FORALL_ADD_COUNT,
    GENERATED_FORALL_MUL_COUNT,
    GENERATED_REFLEXIVITY_COUNT,
    artifact_case_row,
    assert_public_constructor_coverage,
    digest_json,
    expected_intuitionistic_constructor_names,
    formula_sha256,
    generated_positive_cases,
    mutation_artifact_cases,
    validate_boundary_mutations,
    validate_positive_with_python,
)
import training.peano_hydra.h0_macro_evidence as macro_evidence  # noqa: E402
from training.peano_hydra.macro_runner import MacroTrace  # noqa: E402
from training.peano_hydra.profile import canonical_profile_theorem  # noqa: E402


EXPECTED_GENERATED_FORMULA_ROOT = (
    "5af8d13da7d1bfc8c5079244c3c4cf83cd51a7842ba54df16b0fad39b1b8f577"
)
EXPECTED_MACRO_FIXTURE_ROOT = (
    "e9e7f0f4c6e6c399de75dbea876d55b57e58a823abc85cffbcfbb519cb740c62"
)


def test_complete_h0_report_schema_is_version_two() -> None:
    assert REPORT_VERSION == 2


def _make_executable(path: Path, source: str) -> Path:
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)
    return path


def test_reviewed_generated_corpus_is_exact_distinct_and_canonical() -> None:
    cases = generated_positive_cases()
    hashes = [formula_sha256(case.formula) for case in cases]

    assert len(cases) == GENERATED_COUNT == 640
    assert len(set(hashes)) == GENERATED_COUNT
    assert Counter(case.source for case in cases) == {
        "generated-refl": GENERATED_REFLEXIVITY_COUNT,
        "generated-forall-add": GENERATED_FORALL_ADD_COUNT,
        "generated-forall-mul": GENERATED_FORALL_MUL_COUNT,
    }
    assert [case.name for case in cases[:2]] == [
        "generated_refl_0000",
        "generated_refl_0001",
    ]
    assert cases[255].name == "generated_refl_0255"
    assert cases[256].name == "generated_forall_add_0000"
    assert cases[511].name == "generated_forall_add_0255"
    assert cases[512].name == "generated_forall_mul_0000"
    assert cases[639].name == "generated_forall_mul_0127"
    for index in (0, 1, 127, 255, 256, 383, 511, 512, 639):
        canonical = pretty_formula(cases[index].formula, [])
        assert canonical_profile_theorem(canonical) == canonical
    assert digest_json(hashes) == EXPECTED_GENERATED_FORMULA_ROOT


def test_each_positive_has_one_exact_certificate_rejection_pair() -> None:
    for case in (
        generated_positive_cases(count=2)[0],
        generated_positive_cases()[255],
        generated_positive_cases()[512],
    ):
        original, wrong = validate_positive_with_python(case)
        assert original.expected == original.python_disposition == "accept"
        assert wrong.expected == wrong.python_disposition == "certificate_rejected"
        assert original.positive_case_id == wrong.positive_case_id == case.case_id
        assert original.formula_sha256 != wrong.formula_sha256
        retained = json.dumps(
            [artifact_case_row(original), artifact_case_row(wrong)], sort_keys=True
        )
        assert "non-theorem" not in retained
        assert "not_theorem" not in retained


def test_targeted_mutations_cover_every_required_rejection_boundary() -> None:
    cases = mutation_artifact_cases()
    by_category = {case.category: case for case in cases}
    assert set(by_category) == {
        "artifact-codec",
        "binder-scope",
        "classical-gate",
        "checker-fuel-envelope",
        "induction-motive",
        "induction-step",
        "proof-constructor",
        "substitution",
        "wasm-index-envelope",
        "wire-nat-envelope",
    }
    assert by_category["artifact-codec"].expected == "input_rejected"
    assert by_category["artifact-codec"].python_disposition == "not_applicable"
    for category, case in by_category.items():
        if category not in {
            "artifact-codec",
            "checker-fuel-envelope",
            "wasm-index-envelope",
            "wire-nat-envelope",
        }:
            assert case.expected == "certificate_rejected"
            assert case.python_disposition == "certificate_rejected"
    for category in {
        "checker-fuel-envelope",
        "wasm-index-envelope",
        "wire-nat-envelope",
    }:
        assert by_category[category].expected == "certificate_rejected"
        assert by_category[category].python_disposition == "not_applicable"


def test_profile_translation_and_negative_evidence_attempts_are_rejected() -> None:
    valid_unknown = {"kind": "unknown", "reason": "search-exhausted"}

    def strict_result_validator(value: object) -> object:
        if value == valid_unknown:
            return dict(valid_unknown)
        raise ValueError("unsupported result evidence")

    results = validate_boundary_mutations(
        result_validator=strict_result_validator,
        valid_unknown_result=valid_unknown,
    )
    assert results == (
        {
            "case_id": "mutation-profile-external-translation",
            "category": "translation",
            "disposition": "profile_rejected",
        },
        {
            "case_id": "mutation-negative-kind",
            "category": "negative-evidence",
            "disposition": "schema_rejected",
        },
        {
            "case_id": "mutation-negative-field",
            "category": "negative-evidence",
            "disposition": "schema_rejected",
        },
    )


def test_result_schema_controls_retain_all_hash_preimages() -> None:
    controls = _schema_controls()
    assert controls["interpretation"] == "schema controls only; not benchmark outcomes"
    assert controls["proved"]["record"]["kind"] == "proved"
    assert controls["proved"]["record"]["kernel_accepted"] is True
    assert set(controls["proved"]["preimages"]) == {
        "certificate_artifact",
        "kernel_identity",
        "replay_evidence",
        "run_evidence",
    }
    artifact = controls["proved"]["preimages"]["certificate_artifact"]
    assert artifact["encoding"] == "utf-8"
    assert len(artifact["content_utf8"].encode("utf-8")) == artifact["bytes"]
    assert controls["unknown"]["record"]["kind"] == "unknown"
    assert set(controls["unknown"]["preimages"]) == {"run_evidence"}
    assert [row["disposition"] for row in controls["rejected_negative_attempts"]] == [
        "schema_rejected",
        "schema_rejected",
    ]
    assert str(ROOT) not in json.dumps(controls)


def _assert_utf8_preimage(preimage: dict[str, object]) -> bytes:
    assert set(preimage) == {"bytes", "content_utf8", "encoding", "sha256"}
    assert preimage["encoding"] == "utf-8"
    content = preimage["content_utf8"]
    assert type(content) is str
    raw = content.encode("utf-8")
    assert preimage["bytes"] == len(raw)
    assert preimage["sha256"] == hashlib.sha256(raw).hexdigest()
    return raw


def test_macro_protocol_controls_are_self_contained_exact_h03_evidence() -> None:
    controls = _macro_protocol_controls(timeout_seconds=120)
    assert controls["interpretation"] == (
        "H0.3 protocol/conformance controls; solver status has no proof authority"
    )
    assert controls["macro_protocol_identity"] == {
        "format": "peano-hydra-macro-protocol",
        "v": 1,
        "id": "peano-hydra-macro-v1",
        "semantic_sha256": (
            "b5fef1ea1b85251ab7f0b8c111cb37e789f96f20771665b4f0dc8b746400552c"
        ),
        "document_sha256": (
            "6f6920d2d952251170733674a3af8da09926f4faf19215317a32bc0317d4a482"
        ),
    }

    fixtures = controls["typed_action_fixtures"]
    assert fixtures["count"] == 7
    assert fixtures["order"] == [
        "Use",
        "Cut",
        "Witness",
        "Induct",
        "Rewrite",
        "Split",
        "Dispatch",
    ]
    assert fixtures["root_sha256"] == EXPECTED_MACRO_FIXTURE_ROOT
    assert digest_json(fixtures["rows"]) == EXPECTED_MACRO_FIXTURE_ROOT
    for row in fixtures["rows"]:
        raw = _assert_utf8_preimage(row["canonical_preimage"])
        assert json.loads(raw) == row["canonical_object"]
        assert set(row["compilation"]) == {"dispatch", "public_commands"}

    for name, expected_status in (
        ("accepted_deterministic_trace", "accepted"),
        ("transactional_rejected_trace", "rejected"),
    ):
        trace = controls[name]
        raw = _assert_utf8_preimage(trace["canonical_preimage"])
        assert json.loads(raw) == trace["record"]
        assert trace["root_sha256"] == hashlib.sha256(raw).hexdigest()
        assert MacroTrace.from_record(trace["record"]).sha256 == trace["root_sha256"]
        assert trace["record"]["outcome"]["status"] == expected_status
    accepted = controls["accepted_deterministic_trace"]
    assert accepted["deterministic_repetitions"] == 2
    assert accepted["exact_match"] is True
    rejected = controls["transactional_rejected_trace"]
    assert rejected["record"]["state_before"] == rejected["record"]["state_after"]
    assert all(rejected["unchanged_owner_assertions"].values())
    owner_raw = _assert_utf8_preimage(rejected["owner_state_preimage"])
    assert json.loads(owner_raw) == rejected["record"]["state_before"]

    dispatch = controls["dispatch_reconstruction"]
    adapter = dispatch["adapter"]
    artifact_raw = _assert_utf8_preimage(adapter["artifact_preimage"])
    configuration_raw = _assert_utf8_preimage(adapter["configuration_preimage"])
    assert adapter["identity"]["artifact_sha256"] == hashlib.sha256(
        artifact_raw
    ).hexdigest()
    assert adapter["identity"]["configuration_sha256"] == hashlib.sha256(
        configuration_raw
    ).hexdigest()
    assert json.loads(configuration_raw) == adapter["configuration"]

    request = dispatch["dispatch_request"]
    request_raw = _assert_utf8_preimage(request["canonical_preimage"])
    assert json.loads(request_raw) == request["preimage"]
    call = dispatch["dispatch_call"]
    call_raw = _assert_utf8_preimage(call["canonical_preimage"])
    assert json.loads(call_raw) == call["preimage"]
    assert call["preimage"]["request"] == request["preimage"]
    assert call["preimage"]["request_sha256"] == request["canonical_preimage"][
        "sha256"
    ]

    dispatch_trace = dispatch["trace"]
    dispatch_trace_raw = _assert_utf8_preimage(
        dispatch_trace["canonical_preimage"]
    )
    assert json.loads(dispatch_trace_raw) == dispatch_trace["record"]
    assert MacroTrace.from_record(dispatch_trace["record"]).sha256 == dispatch_trace[
        "root_sha256"
    ]
    solver = dispatch_trace["record"]["solver"]
    assert solver["request"] == request["preimage"]
    assert solver["request_sha256"] == request["canonical_preimage"]["sha256"]
    assert solver["dispatch_call_request_sha256"] == request["canonical_preimage"][
        "sha256"
    ]
    assert solver["dispatch_call_sha256"] == call["canonical_preimage"]["sha256"]
    assert solver["adapter_identity"] == adapter["identity"]
    assert solver["adapter_configuration"] == adapter["configuration"]
    assert dispatch["fresh_original_goal_kernel_check"] == {
        "accepted": True,
        "context": "empty",
        "original_theorem": "0 = 0",
    }
    final = dispatch_trace["record"]["final_replay"]
    assert final["fresh"] is final["kernel_accepted"] is True
    assert final["original_theorem"] == "0 = 0"
    certificate = _assert_utf8_preimage(dispatch["certificate_artifact_preimage"])
    assert hashlib.sha256(certificate).hexdigest() == final[
        "certificate_sha256"
    ]
    response = _assert_utf8_preimage(dispatch["raw_response_preimage"])
    assert json.loads(response)["public_commands"] == ["refl"]

    focused = controls["focused_pytest"]
    assert focused["command"] == {
        "argv": [
            "python",
            "-B",
            "-m",
            "pytest",
            "-q",
            "tests/test_peano_hydra_macros.py",
            "tests/test_peano_hydra_macro_runner.py",
        ],
        "cwd": "peano-lab/py",
        "environment": {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        },
    }
    assert focused["result"]["exit_code"] == 0
    assert focused["result"]["passed"] == 110
    assert focused["result"]["summary"].startswith("110 passed in ")
    _assert_utf8_preimage(focused["result"]["stdout"])
    assert _assert_utf8_preimage(focused["result"]["stderr"]) == b""
    assert str(ROOT) not in json.dumps(controls)


def test_macro_protocol_controls_fail_closed_on_registered_root_drift(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(macro_evidence, "FIXTURE_ROOT_SHA256", "0" * 64)
    with pytest.raises(
        macro_evidence.H0MacroEvidenceError,
        match="fixture content root drifted",
    ):
        macro_evidence.build_h0_macro_evidence()


def test_macro_evidence_builder_rejects_caller_supplied_test_claims() -> None:
    forged = {"result": {"exit_code": 0, "passed": 110}}
    with pytest.raises(TypeError, match="unexpected keyword argument"):
        macro_evidence.build_h0_macro_evidence(  # type: ignore[call-arg]
            focused_pytest=forged
        )


def test_focused_macro_test_failure_cannot_be_reported_as_green(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failed_run(*_args, **_kwargs):
        return subprocess.CompletedProcess(
            ["pytest"], 1, stdout=b"109 passed, 1 failed\n", stderr=b""
        )

    monkeypatch.setattr(subprocess, "run", failed_run)
    with pytest.raises(H0ValidationError, match="exact green result"):
        _run_macro_focused_tests(timeout_seconds=1)


def test_constructor_coverage_gate_uses_the_exact_profile_inventory() -> None:
    expected = expected_intuitionistic_constructor_names()
    assert assert_public_constructor_coverage(expected) == expected
    with pytest.raises(ConformanceError, match="missing"):
        assert_public_constructor_coverage(expected[:-1])
    with pytest.raises(ConformanceError, match="out-of-profile DNE"):
        assert_public_constructor_coverage((*expected, "DNE"))


def test_shadow_depth_exclusions_are_explicit_not_semantic_disagreements() -> None:
    shallow = validate_positive_with_python(generated_positive_cases(count=1)[0])[0]
    deepest_refl = validate_positive_with_python(generated_positive_cases()[255])[0]

    assert shallow.decoder_depth is not None and shallow.decoder_depth < WASM_MAX_DEPTH
    assert deepest_refl.decoder_depth is not None
    assert deepest_refl.decoder_depth > RUST_MAX_DEPTH > WASM_MAX_DEPTH
    assert _envelope_reason(
        shallow,
        max_bytes=16 * 1024 * 1024,
        max_nodes=1_000_000,
        max_depth=WASM_MAX_DEPTH,
    ) is None
    assert _envelope_reason(
        deepest_refl,
        max_bytes=512 * 1024 * 1024,
        max_nodes=4_000_000,
        max_depth=RUST_MAX_DEPTH,
    ) == f"decoder_depth>{RUST_MAX_DEPTH}"

    mutations = {case.category: case for case in mutation_artifact_cases()}
    wire_nat = mutations["wire-nat-envelope"]
    wasm_index = mutations["wasm-index-envelope"]
    assert _envelope_reason(
        wire_nat,
        max_bytes=512 * 1024 * 1024,
        max_nodes=4_000_000,
        max_depth=RUST_MAX_DEPTH,
        max_wire_nat=RUST_MAX_WIRE_NAT,
    ) == f"wire_nat>{RUST_MAX_WIRE_NAT}"
    assert _envelope_reason(
        wasm_index,
        max_bytes=16 * 1024 * 1024,
        max_nodes=1_000_000,
        max_depth=WASM_MAX_DEPTH,
        max_wire_nat=WASM_MAX_WIRE_NAT,
        max_portable_index=WASM_MAX_PORTABLE_INDEX,
    ) == f"portable_index>{WASM_MAX_PORTABLE_INDEX}"


def test_two_fresh_small_replays_have_identical_rows_and_root(tmp_path: Path) -> None:
    arguments = {
        "names": ("zero_add", "add_succ_left"),
        "external_paths": None,
        "timeout_seconds": 5.0,
        "campaign_timeout_seconds": 60.0,
    }
    first = _spawn_cold_worker(output=tmp_path / "first.json", **arguments)
    second = _spawn_cold_worker(output=tmp_path / "second.json", **arguments)
    summary = compare_cold_replays(first, second)

    assert summary["identical"] is True
    assert summary["pass_count"] == 2
    assert summary["library_count"] == 2
    serialized = json.dumps([first, second, summary], ensure_ascii=False)
    assert str(ROOT) not in serialized
    assert str(tmp_path) not in serialized


def test_cold_pair_controller_overlaps_the_two_fresh_workers(tmp_path: Path) -> None:
    lock = Lock()
    active = 0
    maximum_active = 0

    def fake_worker(**_kwargs):
        nonlocal active, maximum_active
        with lock:
            active += 1
            maximum_active = max(maximum_active, active)
        sleep(0.05)
        with lock:
            active -= 1
        return {"cold": {"rows": [], "root_sha256": "0" * 64}}

    first, second, timing = run_cold_replay_pair(
        temp=tmp_path,
        names=("zero_add",),
        external_paths={},
        timeout_seconds=1,
        campaign_timeout_seconds=1,
        worker=fake_worker,
    )
    assert first == second
    assert maximum_active == 2
    assert timing["pass_1_python_duration_ns"] > 0
    assert timing["pass_2_python_and_external_duration_ns"] > 0
    assert timing["concurrent_wall_duration_ns"] < (
        timing["pass_1_python_duration_ns"]
        + timing["pass_2_python_and_external_duration_ns"]
    )


def test_cold_pair_failure_cancels_its_peer(tmp_path: Path) -> None:
    peer_observed_cancellation = False

    def fake_worker(**kwargs):
        nonlocal peer_observed_cancellation
        if kwargs["output"].name == "pass-1.json":
            sleep(0.05)
            raise H0ValidationError("first failed")
        cancel_event = kwargs["cancel_event"]
        assert cancel_event.wait(timeout=1.0)
        peer_observed_cancellation = True
        raise H0ValidationError("peer cancelled")

    with pytest.raises(H0ValidationError, match="first failed"):
        run_cold_replay_pair(
            temp=tmp_path,
            names=("zero_add",),
            external_paths={},
            timeout_seconds=1,
            campaign_timeout_seconds=2,
            worker=fake_worker,
        )
    assert peer_observed_cancellation is True


def test_external_suite_enforces_three_protocols_without_retaining_paths(
    tmp_path: Path,
) -> None:
    rust = _make_executable(
        tmp_path / "fake-rust",
        """#!/usr/bin/env python3
import json, sys
data = sys.stdin.buffer.read()
if not data.endswith(b"\\n"):
    sys.stderr.write("ERROR: non-canonical artifact at byte 0\\n")
    raise SystemExit(2)
value = json.loads(data)
if value[2][0] == "imp":
    sys.stdout.write("REJECT\\n")
    raise SystemExit(1)
sys.stdout.write("ACCEPT\\n")
""",
    )
    node = _make_executable(
        tmp_path / "fake-node",
        """#!/usr/bin/env python3
import json, struct, sys
while True:
    header = sys.stdin.buffer.read(5)
    if not header:
        break
    _, length = struct.unpack(">BI", header)
    data = sys.stdin.buffer.read(length)
    if not data.endswith(b"\\n"):
        verdict = 3
    else:
        value = json.loads(data)
        verdict = 2 if value[2][0] == "imp" else 1
    sys.stdout.write(str(verdict) + "\\n")
    sys.stdout.flush()
""",
    )
    lean = _make_executable(
        tmp_path / "fake-lean",
        """#!/usr/bin/env python3
import json, pathlib, sys
status = 0
for raw in sys.argv[1:]:
    path = pathlib.Path(raw)
    data = path.read_bytes()
    if not data.endswith(b"\\n"):
        print(f"DECODE_ERROR\\t{raw}\\tnon-canonical", file=sys.stderr)
        status = max(status, 2)
        continue
    value = json.loads(data)
    rejected = value[2][0] == "imp"
    print(("REJECT" if rejected else "ACCEPT") + f"\\t{raw}\\tfuel={value[1]}")
    status = max(status, 1 if rejected else 0)
raise SystemExit(status)
""",
    )
    wasm = tmp_path / "fake.wasm"
    wasm.write_bytes(b"fake-wasm-for-protocol-test")

    positive = generated_positive_cases(count=1)[0]
    original, wrong = validate_positive_with_python(positive)
    malformed = next(
        case for case in mutation_artifact_cases() if case.category == "artifact-codec"
    )
    suite = ExternalVerifierSuite(
        lean_verifier=lean,
        rust_cli=rust,
        node=node,
        wasm=wasm,
        timeout_seconds=5,
    )
    for case in (original, wrong, malformed):
        suite.submit(case)
    rows = suite.finish()

    assert [row["lean"]["disposition"] for row in rows] == [
        "accept",
        "certificate_rejected",
        "input_rejected",
    ]
    assert [row["rust"]["disposition"] for row in rows] == [
        "accept",
        "certificate_rejected",
        "input_rejected",
    ]
    assert [row["wasm"]["disposition"] for row in rows] == [
        "accept",
        "certificate_rejected",
        "input_rejected",
    ]
    retained = json.dumps({"identity": suite.identity, "rows": rows})
    assert str(tmp_path) not in retained


def test_wasm_diagnostic_has_a_per_case_deadline(tmp_path: Path) -> None:
    rust = _make_executable(
        tmp_path / "fake-rust",
        """#!/bin/sh
IFS= read -r artifact || exit 2
printf 'ACCEPT\\n'
""",
    )
    node = _make_executable(
        tmp_path / "hanging-node",
        """#!/usr/bin/env python3
import struct, sys, time
header = sys.stdin.buffer.read(5)
if len(header) == 5:
    _, length = struct.unpack(">BI", header)
    sys.stdin.buffer.read(length)
time.sleep(10)
""",
    )
    lean = _make_executable(
        tmp_path / "fake-lean",
        """#!/usr/bin/env python3
raise SystemExit(0)
""",
    )
    wasm = tmp_path / "fake.wasm"
    wasm.write_bytes(b"fake-wasm-for-timeout-test")
    original = validate_positive_with_python(generated_positive_cases(count=1)[0])[0]
    suite = ExternalVerifierSuite(
        lean_verifier=lean,
        rust_cli=rust,
        node=node,
        wasm=wasm,
        timeout_seconds=0.2,
    )
    suite._run_rust = lambda _case: {"disposition": "accept", "portable": True}
    try:
        with pytest.raises(H0ValidationError, match="WASM diagnostic timed out"):
            suite.submit(original)
    finally:
        suite.abort()


def test_wasm_partial_verdict_cannot_bypass_the_per_case_deadline(
    tmp_path: Path,
) -> None:
    rust = _make_executable(
        tmp_path / "fake-rust",
        """#!/bin/sh
IFS= read -r artifact || exit 2
printf 'ACCEPT\\n'
""",
    )
    node = _make_executable(
        tmp_path / "partial-node",
        """#!/usr/bin/env python3
import struct, sys, time
header = sys.stdin.buffer.read(5)
if len(header) == 5:
    _, length = struct.unpack(">BI", header)
    sys.stdin.buffer.read(length)
sys.stdout.write("1")
sys.stdout.flush()
time.sleep(10)
""",
    )
    lean = _make_executable(
        tmp_path / "fake-lean",
        """#!/usr/bin/env python3
raise SystemExit(0)
""",
    )
    wasm = tmp_path / "fake.wasm"
    wasm.write_bytes(b"fake-wasm-for-partial-line-timeout-test")
    original = validate_positive_with_python(generated_positive_cases(count=1)[0])[0]
    suite = ExternalVerifierSuite(
        lean_verifier=lean,
        rust_cli=rust,
        node=node,
        wasm=wasm,
        timeout_seconds=0.2,
    )
    suite._run_rust = lambda _case: {"disposition": "accept", "portable": True}
    try:
        with pytest.raises(H0ValidationError, match="deadline|timed out"):
            suite.submit(original)
    finally:
        suite.abort()


def test_lean_reference_identity_binds_clean_commit_sources_and_toolchain(
    tmp_path: Path,
) -> None:
    root = tmp_path / "lean-reference"
    sources = root / "PeanoLab"
    binary = root / ".lake" / "build" / "bin" / "peano_lab_verify"
    sources.mkdir(parents=True)
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b"pinned verifier")
    binary.chmod(0o755)
    (root / "PeanoLab.lean").write_text(
        "import PeanoLab.Verify\n", encoding="utf-8"
    )
    for name in (
        "Syntax.lean",
        "Substitution.lean",
        "Semantics.lean",
        "Derivation.lean",
        "Checker.lean",
        "Soundness.lean",
        "Codec.lean",
        "Verify.lean",
    ):
        (sources / name).write_text(f"-- {name}\n", encoding="utf-8")
    (root / "lean-toolchain").write_text("leanprover/lean4:v4.31.0\n", encoding="utf-8")
    (root / "lakefile.toml").write_text("name = 'fixture'\n", encoding="utf-8")
    (root / "lake-manifest.json").write_text("{}\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "."], cwd=root, check=True)
    subprocess.run(
        [
            "git",
            "-c",
            "user.name=Peano H0 Test",
            "-c",
            "user.email=peano-h0@example.invalid",
            "commit",
            "-qm",
            "fixture",
        ],
        cwd=root,
        check=True,
    )

    identity = _inspect_lean_source_identity(root, binary)
    assert identity["clean"] is True
    assert len(identity["commit"]) == 40
    assert identity["verifier_relative_path"] == (
        ".lake/build/bin/peano_lab_verify"
    )
    assert identity["toolchain"]["content_utf8"] == "leanprover/lean4:v4.31.0\n"
    assert len(identity["manifest"]["files"]) == 12
    assert str(root) not in json.dumps(identity)

    with pytest.raises(H0ValidationError, match="exact independently reviewed"):
        _lean_source_identity(root, binary)

    (sources / "Untracked.lean").write_text("-- drift\n", encoding="utf-8")
    with pytest.raises(H0ValidationError, match="must be clean"):
        _inspect_lean_source_identity(root, binary)


def test_reviewed_lean_identity_is_pre_registered_not_post_hoc() -> None:
    assert REVIEWED_LEAN_SOURCE_COMMIT == (
        "05b6acd6e5295dbcb45fd23e96c3c112351c2e5b"
    )
    assert REVIEWED_LEAN_SOURCE_MANIFEST_SHA256 == (
        "8c187b0078c836968287bb978632caa2bc114a533bc17fe89f7804a762454939"
    )
    assert REVIEWED_LEAN_VERIFIER_SHA256 == (
        "c3f6eae40e1d60f1ed2d89c1ea47bc761c5d5fcb5a1df1e2b4cc2b5ba2cbfb98"
    )


def test_dirty_or_skipped_regression_modes_are_never_campaign_eligible() -> None:
    assert _campaign_eligibility(require_clean=True, run_regressions=True) == (
        True,
        [],
    )
    assert _campaign_eligibility(require_clean=False, run_regressions=True) == (
        False,
        ["dirty-worktree-development-mode"],
    )
    assert _campaign_eligibility(require_clean=True, run_regressions=False) == (
        False,
        ["required-regressions-skipped"],
    )


def test_repository_or_source_drift_fails_final_sealing() -> None:
    repository = {"clean": True, "commit": "a" * 40}
    sources = {"root_sha256": "b" * 64}
    _require_unchanged_repository(repository, sources, dict(repository), dict(sources))
    with pytest.raises(H0ValidationError, match="changed during validation"):
        _require_unchanged_repository(
            repository,
            sources,
            {"clean": True, "commit": "c" * 40},
            dict(sources),
        )
    with pytest.raises(H0ValidationError, match="changed during validation"):
        _require_unchanged_repository(
            repository,
            sources,
            dict(repository),
            {"root_sha256": "d" * 64},
        )


def test_required_regressions_receive_a_hard_deadline(monkeypatch) -> None:
    observed: dict[str, object] = {}

    def timeout_run(*_args, **kwargs):
        observed["timeout"] = kwargs.get("timeout")
        raise subprocess.TimeoutExpired(["pytest"], kwargs.get("timeout"))

    monkeypatch.setattr(subprocess, "run", timeout_run)
    with pytest.raises(H0ValidationError, match="failed to run"):
        _run_required_regressions(timeout_seconds=0.125)
    assert observed == {"timeout": 0.125}


def test_implementation_manifest_binds_the_complete_h0_macro_layer() -> None:
    manifest = _source_manifest()
    paths = {row["path"] for row in manifest["files"]}
    assert {
        "peano-lab/py/tests/test_peano_hydra_conformance.py",
        "peano-lab/py/tests/test_peano_hydra_macro_runner.py",
        "peano-lab/py/tests/test_peano_hydra_macros.py",
        "training/peano_hydra/__init__.py",
        "training/peano_hydra/macro-protocol-v1.json",
        "training/peano_hydra/h0_macro_evidence.py",
        "training/peano_hydra/macro_runner.py",
        "training/peano_hydra/macros.py",
        "training/peano_hydra/policy.py",
        "training/peano_hydra/profile.py",
        "training/peano_hydra/profile_theorem_v1.py",
        "training/peano_hydra/result-schema-v1.json",
        "training/peano_hydra/result_schema.py",
        "training/peano_hydra/semantic-profile-v1.json",
        "training/peano_hydra/semantic-profile-v2.json",
        "training/peano_policy/__init__.py",
        "training/peano_policy/library_identity.py",
        "training/peano_policy/prompt.py",
        "training/peano_policy/search.py",
    } <= paths
    assert str(ROOT) not in json.dumps(manifest)


def test_full_count_is_public_plus_generated_without_negative_decision_rows() -> None:
    assert FULL_POSITIVE_COUNT == 384 + GENERATED_COUNT == 1_024
