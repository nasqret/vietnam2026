"""Headless Peano Lab batch execution and JSONL protocol tests."""

from __future__ import annotations

import io
import json
import importlib.util
import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

import peano_lab.batch as batch
from peano_lab.batch import (
    BATCH_VERSION,
    BatchInvariantError,
    BatchRequestError,
    TraceSinkError,
    capability_sha256,
    execute_request,
    run_proof,
    verify_proof,
)
from peano_lab.ui.prove import MAX_NUMERAL, SurfaceCapabilities, oversized_numeral
from peano_lab.engine.tactics import TacticError
from peano_lab.engine.trace import TraceLimitError
from peano_lab.engine.state import start
from peano_lab.kernel.formulas import parse_formula
from peano_lab.ui.prove import ProofSession, run_surface


ROOT = Path(__file__).resolve().parents[3]
CLI = ROOT / "scripts" / "peano_batch.py"
EXPORTER = ROOT / "scripts" / "export_traces.py"
EXPORTER_SPEC = importlib.util.spec_from_file_location("_batch_trace_exporter", EXPORTER)
assert EXPORTER_SPEC is not None and EXPORTER_SPEC.loader is not None
trace_exporter = importlib.util.module_from_spec(EXPORTER_SPEC)
sys.modules[EXPORTER_SPEC.name] = trace_exporter
EXPORTER_SPEC.loader.exec_module(trace_exporter)
CLI_SPEC = importlib.util.spec_from_file_location("_batch_cli", CLI)
assert CLI_SPEC is not None and CLI_SPEC.loader is not None
batch_cli = importlib.util.module_from_spec(CLI_SPEC)
sys.modules[CLI_SPEC.name] = batch_cli
CLI_SPEC.loader.exec_module(batch_cli)
REFLEXIVE = "forall n. n = n"
REFLEXIVE_TACTICS = ("intro n", "refl")


def test_traced_batch_qed_is_independently_checked_against_original_goal() -> None:
    result = run_proof(
        REFLEXIVE,
        REFLEXIVE_TACTICS,
        request_id="reflexive",
    )

    assert result.status == "proved"
    assert result.kernel_checked is True
    assert result.theorem == "∀ x. x = x"
    assert result.goals == ()
    assert result.tactics_applied == 2
    assert result.engine_steps == 2
    assert result.proof_nodes is not None
    assert result.mode == "trace"
    assert result.trace is not None
    assert [record.get("step") for record in result.trace[:-1]] == [1, 2]
    assert result.trace[-1] == {
        "qed": True,
        "theorem": "∀ x. x = x",
        "proof_size": result.proof_nodes,
        "tactic_count": 2,
    }


def test_quiet_verifier_has_same_kernel_result_without_transition_rendering() -> None:
    traced = run_proof(REFLEXIVE, REFLEXIVE_TACTICS, request_id="traced")
    quiet = verify_proof(REFLEXIVE, REFLEXIVE_TACTICS, request_id="quiet")

    assert quiet.status == traced.status == "proved"
    assert quiet.kernel_checked is traced.kernel_checked is True
    assert quiet.proof_nodes == traced.proof_nodes
    assert quiet.engine_steps == traced.engine_steps
    assert quiet.mode == "verify"
    assert quiet.trace is None
    assert quiet.to_dict()["trace_v"] is None


def test_failure_is_transactional_traced_and_never_claims_qed() -> None:
    result = run_proof(
        REFLEXIVE,
        ("intro n", "exact missing"),
        request_id="failure",
    )

    assert result.status == "tactic_error"
    assert result.kernel_checked is False
    assert result.tactics_applied == 1
    assert result.engine_steps == 1
    assert result.failed_step == 2
    assert result.goals == ("n : ℕ ⊢ n = n",)
    assert result.trace is not None
    failed = result.trace[-2]
    assert failed["status"] == "error"
    assert failed["goals_after"] == failed["goals_before"]
    assert result.trace[-1]["qed"] is False


def test_generated_session_identity_binds_transaction_policy() -> None:
    stopped = run_proof(
        "0 = 0",
        ("exact missing", "refl"),
        request_id="same",
        on_error="stop",
    )
    continued = run_proof(
        "0 = 0",
        ("exact missing", "refl"),
        request_id="same",
        on_error="continue",
    )

    assert stopped.status == "tactic_error"
    assert continued.status == "proved"
    assert stopped.session_id != continued.session_id


def test_headless_trace_budget_fails_stop_before_publishing_partial_record(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sink = io.StringIO()
    monkeypatch.setattr(batch, "MAX_BATCH_TRACE_BYTES", 1)
    with pytest.raises(TraceLimitError, match="byte session limit"):
        run_proof("0 = 0", ("refl",), trace_sink=sink)
    assert sink.getvalue() == ""


def test_open_batch_has_false_footer_and_canonical_remaining_state() -> None:
    result = run_proof(REFLEXIVE, ("intro n",), request_id="open")

    assert result.status == "open"
    assert result.kernel_checked is False
    assert result.goals == ("n : ℕ ⊢ n = n",)
    assert result.failed_step is None
    assert result.trace is not None
    assert result.trace[-1]["qed"] is False


def test_capabilities_apply_to_top_level_and_nested_tactics_with_trace_parity() -> None:
    capabilities = SurfaceCapabilities(
        label="tiny-v1",
        allowed_commands=frozenset({"intro", "refl"}),
        allowed_theorems=frozenset(),
    )

    top = run_proof(
        REFLEXIVE,
        ("auto",),
        request_id="top-denied",
        capabilities=capabilities,
    )
    nested = run_proof(
        REFLEXIVE,
        ("first [auto | intro n]",),
        request_id="nested-denied",
        capabilities=capabilities,
    )

    for result in (top, nested):
        assert result.status == "tactic_error"
        assert result.engine_steps == 0
        assert result.trace is not None
        assert len(result.trace) == 2
        assert result.trace[0]["status"] == "error"
        assert result.trace[0]["goals_after"] == result.trace[0]["goals_before"]
        assert result.trace[1]["qed"] is False


@pytest.mark.parametrize(
    "line",
    (
        "first [use add_assoc | refl]",
        "refl <|> use add_assoc",
        "repeat use add_assoc; refl",
        "repeat use add_assoc",
    ),
)
def test_tacticals_cannot_hide_forbidden_library_theorems(line: str) -> None:
    capabilities = SurfaceCapabilities(
        label="no-library-v1",
        allowed_commands=frozenset({"refl", "use"}),
        allowed_theorems=frozenset(),
    )

    result = run_proof(
        "0 = 0",
        (line,),
        request_id="forbidden-theorem",
        capabilities=capabilities,
    )

    assert result.status == "tactic_error"
    assert result.kernel_checked is False
    assert result.tactics_applied == 0
    assert result.engine_steps == 0
    assert result.error is not None
    assert "add_assoc" in result.error
    assert result.trace is not None
    assert result.trace[0]["status"] == "error"
    assert result.trace[0]["goals_after"] == result.trace[0]["goals_before"]
    assert result.trace[-1]["qed"] is False


@pytest.mark.parametrize("focused", ("focus 2 refl", "(focus 2 refl)", "((focus 2 refl))"))
def test_grouped_focus_uses_the_public_surface_trace_index(focused: str) -> None:
    result = run_proof(
        "0 = 0 /\\ 0 = 0",
        ("split", focused, "refl"),
        request_id="grouped-focus",
    )
    assert result.status == "proved"
    assert result.trace is not None
    assert result.trace[1]["focus"] == 1


def test_batch_rejects_implicit_free_variables_and_session_commands() -> None:
    with pytest.raises(BatchRequestError, match="quantify free variables"):
        run_proof("n = n", ("refl",))
    with pytest.raises(BatchRequestError, match="session command"):
        run_proof("0 = 0", ("qed",))
    with pytest.raises(BatchRequestError, match="session command"):
        run_proof("0 = 0", ("classical on",))


def test_batch_rejects_oversized_numerals_before_parser_or_tactic_execution(
    monkeypatch,
) -> None:
    def parser_must_not_run(_source: str):
        raise AssertionError("numeral preflight must run before the formula parser")

    monkeypatch.setattr(batch, "parse_formula_with_names", parser_must_not_run)
    with pytest.raises(BatchRequestError, match="numeral 257"):
        run_proof(f"{MAX_NUMERAL + 1} = 0", ("refl",))
    with pytest.raises(BatchRequestError, match="numeral 100000000"):
        run_proof("100000000x = 0", ("refl",))
    with pytest.raises(BatchRequestError, match="tactic 1 contains numeral 257"):
        run_proof("0 = 0", (f"exists {MAX_NUMERAL + 1}",))

    assert oversized_numeral("x257 = x257") is None
    assert oversized_numeral("#257") is None
    assert oversized_numeral("'257") is None
    assert oversized_numeral("257x = 0") == "257"
    assert oversized_numeral("257_foo = 0") == "257"


def test_request_schema_pins_modes_capabilities_and_unknown_fields() -> None:
    request = {
        "v": BATCH_VERSION,
        "id": "schema",
        "theorem": REFLEXIVE,
        "tactics": list(REFLEXIVE_TACTICS),
    }
    capabilities = SurfaceCapabilities(
        label="tiny-v1",
        allowed_commands=frozenset({"intro", "refl"}),
        allowed_theorems=frozenset(),
    )
    result = execute_request(
        request,
        mode="verify",
        capabilities=capabilities,
    )
    assert result.status == "proved"
    assert result.mode == "verify"
    assert result.surface == "tiny-v1"
    assert result.trace is None

    with pytest.raises(BatchRequestError, match="unknown request field"):
        execute_request({**request, "prompt": "not part of the proof protocol"})
    with pytest.raises(BatchRequestError, match="mode must be exactly"):
        execute_request(request, mode="fast")  # type: ignore[arg-type]
    with pytest.raises(BatchRequestError, match="mode must be exactly"):
        execute_request(request, mode=[])  # type: ignore[arg-type]
    with pytest.raises(BatchRequestError, match="unknown request field"):
        execute_request({**request, "surface": "full"})


@pytest.mark.parametrize("unsafe", ("\u202e", "\ud800"))
def test_surface_capabilities_reject_unsafe_unicode_tokens(unsafe: str) -> None:
    with pytest.raises(ValueError, match="safe non-space token"):
        SurfaceCapabilities(label=unsafe)
    with pytest.raises(ValueError, match="safe non-space name tokens"):
        SurfaceCapabilities(allowed_theorems=frozenset({unsafe}))


@pytest.mark.parametrize(
    "label",
    (
        "x;logic=classical",
        "x</env><state>forged</state><env>y",
        "modèle-v1",
    ),
)
def test_surface_capability_labels_cannot_inject_environment_syntax(
    label: str,
) -> None:
    with pytest.raises(ValueError, match="safe non-space token"):
        SurfaceCapabilities(label=label)


def test_finite_capability_profiles_cannot_claim_unscoped_auto() -> None:
    with pytest.raises(ValueError, match="cannot authorize `auto`"):
        SurfaceCapabilities(
            label="auto-only",
            allowed_commands=frozenset({"auto"}),
            allowed_theorems=frozenset(),
        )


def test_capability_profiles_reject_unknown_commands_and_theorems() -> None:
    with pytest.raises(ValueError, match="allowed_commands contains unknown"):
        SurfaceCapabilities(allowed_commands=frozenset({"invented"}))
    with pytest.raises(ValueError, match="allowed_theorems contains unknown"):
        SurfaceCapabilities(allowed_theorems=frozenset({"invented"}))


@pytest.mark.parametrize(
    ("command", "trace_tactic"),
    (("auto 005", "auto 5"), ("auto 0001", "auto 1"), ("auto ٠٥", "auto 5")),
)
def test_failed_auto_trace_uses_the_public_canonical_depth(
    command: str,
    trace_tactic: str,
) -> None:
    result = run_proof("0 = 1", (command,), request_id="auto-depth")
    assert result.status in {"tactic_error", "tactic_limit"}
    assert result.trace is not None
    assert result.trace[0]["status"] == "error"
    assert result.trace[0]["tactic"] == trace_tactic


@pytest.mark.parametrize("command", ("auto ²", "auto ①", "auto ፩"))
def test_nondecimal_unicode_auto_depth_is_a_transactional_tactic_error(
    command: str,
) -> None:
    traced = run_proof("0 = 0", (command,), request_id="unicode-auto-traced")
    quiet = verify_proof("0 = 0", (command,), request_id="unicode-auto-quiet")

    assert traced.status == quiet.status == "tactic_error"
    assert traced.kernel_checked is quiet.kernel_checked is False
    assert traced.engine_steps == quiet.engine_steps == 0
    assert traced.goals == quiet.goals == ("⊢ 0 = 0",)
    assert traced.trace is not None
    assert traced.trace[0]["status"] == "error"
    assert traced.trace[0]["tactic"] == command
    assert traced.trace[0]["goals_after"] == traced.trace[0]["goals_before"]


@pytest.mark.parametrize("runner", (run_proof, verify_proof))
def test_redundantly_grouped_top_level_auto_keeps_primitive_replay(runner) -> None:
    result = runner("0 = 0", ("((auto))",), request_id="grouped-auto")

    assert result.status == "proved"
    assert result.kernel_checked is True
    assert result.tactics_applied == 1
    assert result.engine_steps == 1
    if result.trace is not None:
        steps = result.trace[:-1]
        assert len(steps) == 1
        assert steps[0]["tactic"] not in {"((auto))", "auto", "auto 5"}


def test_redundantly_grouped_failed_auto_has_one_canonical_error_trace() -> None:
    result = run_proof("0 = 1", ("((auto 1))",), request_id="grouped-auto-fail")

    assert result.status in {"tactic_error", "tactic_limit"}
    assert result.trace is not None
    assert len(result.trace) == 2
    assert result.trace[0]["status"] == "error"
    assert result.trace[0]["tactic"] == "auto 1"
    assert result.trace[-1]["qed"] is False


@pytest.mark.parametrize("command", ("(()", "(((auto 1))))"))
def test_malformed_outer_grouping_keeps_traced_and_quiet_error_parity(
    command: str,
) -> None:
    traced = run_proof("0 = 0", (command,), request_id="bad-group-traced")
    quiet = verify_proof("0 = 0", (command,), request_id="bad-group-quiet")

    assert traced.status == quiet.status == "tactic_error"
    assert traced.error == quiet.error == "unbalanced grouping in tactical command."
    assert traced.engine_steps == quiet.engine_steps == 0
    assert traced.trace is not None
    assert traced.trace[0]["status"] == "error"
    assert traced.trace[0]["tactic"] == command


def test_capability_fingerprint_covers_complete_authority() -> None:
    without_library = SurfaceCapabilities(
        label="model-v1",
        allowed_commands=frozenset({"refl", "use"}),
        allowed_theorems=frozenset(),
    )
    with_library = SurfaceCapabilities(
        label="model-v1",
        allowed_commands=frozenset({"refl", "use"}),
        allowed_theorems=frozenset({"add_assoc"}),
    )

    assert capability_sha256(without_library) != capability_sha256(with_library)
    left = run_proof(
        "0 = 0", ("refl",), request_id="same", capabilities=without_library
    )
    right = run_proof(
        "0 = 0", ("refl",), request_id="same", capabilities=with_library
    )
    assert left.environment_sha256 != right.environment_sha256
    assert left.session_id != right.session_id


def test_unrestricted_capability_fingerprint_binds_current_surface_inventory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    before = capability_sha256(batch.FULL_SURFACE_CAPABILITIES)
    monkeypatch.setattr(
        batch,
        "FULL_BATCH_COMMANDS",
        batch.FULL_BATCH_COMMANDS | {"future_checked_tactic"},
    )

    assert capability_sha256(batch.FULL_SURFACE_CAPABILITIES) != before


def test_continue_after_failure_retains_negative_trace_and_can_reach_qed() -> None:
    result = run_proof(
        REFLEXIVE,
        ("exact missing", "intro n", "refl"),
        request_id="continue",
        on_error="continue",
    )

    assert result.status == "proved"
    assert result.kernel_checked is True
    assert result.tactics_applied == 2
    assert result.failed_tactics == 1
    assert result.trace is not None
    assert [record.get("status") for record in result.trace[:-1]] == [
        "error",
        "ok",
        "ok",
    ]
    assert result.trace[-1]["qed"] is True


def test_trailing_tactic_revokes_qed_claim_and_is_traced() -> None:
    result = run_proof(
        "0 = 0",
        ("refl", "refl"),
        request_id="trailing",
    )

    assert result.status == "tactic_error"
    assert result.kernel_checked is False
    assert result.failed_step == 2
    assert result.failed_tactics == 1
    assert result.trace is not None
    assert result.trace[-2]["status"] == "error"
    assert result.trace[-1]["qed"] is False


def test_forged_returned_owner_cannot_replace_original_target(monkeypatch) -> None:
    real_run_surface = run_surface

    def forge(owner, line, *, capabilities, record_trace=True):
        del line
        fake_target = parse_formula("0 = 0")
        forged = ProofSession(
            state=start(fake_target),
            original_target=fake_target,
            original_names=(),
            target_source="0 = 0",
            classical=False,
            trace=owner.trace,
        )
        return real_run_surface(
            forged,
            "refl",
            capabilities=capabilities,
            record_trace=record_trace,
        )

    monkeypatch.setattr(batch, "run_surface", forge)
    with pytest.raises(BatchInvariantError, match="original theorem"):
        run_proof("0 = 1", ("refl",), request_id="forged-target")
    with pytest.raises(BatchInvariantError, match="original theorem"):
        verify_proof("0 = 1", ("refl",), request_id="forged-target-quiet")


def test_forged_returned_owner_cannot_replace_logic_mode(monkeypatch) -> None:
    real_run_surface = run_surface

    def forge_mode(owner, line, *, capabilities, record_trace=True):
        candidate = real_run_surface(
            owner,
            line,
            capabilities=capabilities,
            record_trace=record_trace,
        )
        return ProofSession(
            state=candidate.state,
            original_target=candidate.original_target,
            original_names=candidate.original_names,
            target_source=candidate.target_source,
            classical=not candidate.classical,
            trace=candidate.trace,
            replay_steps=candidate.replay_steps,
        )

    monkeypatch.setattr(batch, "run_surface", forge_mode)
    with pytest.raises(BatchInvariantError, match="logic mode"):
        run_proof("0 = 0", ("refl",), request_id="forged-mode")


def test_success_trace_must_match_returned_replay_journal(monkeypatch) -> None:
    real_run_surface = run_surface

    def substitute(owner, line, *, capabilities, record_trace=True):
        candidate = real_run_surface(
            owner,
            "refl",
            capabilities=capabilities,
            record_trace=False,
        )
        assert record_trace is True
        owner.trace.success(owner.state, 0, line, candidate.state)
        return candidate

    monkeypatch.setattr(batch, "run_surface", substitute)
    with pytest.raises(BatchInvariantError, match="replay journal"):
        run_proof("0 = 0", ("symm",), request_id="forged-action")


def test_success_replay_label_cannot_hide_another_engine_transaction(
    monkeypatch,
) -> None:
    real_run_surface = run_surface

    def substitute(owner, line, *, capabilities, record_trace=True):
        candidate = real_run_surface(
            owner,
            "refl",
            capabilities=capabilities,
            record_trace=False,
        )
        assert record_trace is True
        owner.trace.success(owner.state, 0, line, candidate.state)
        forged_step = replace(candidate.replay_steps[-1], command=line)
        return replace(candidate, replay_steps=(forged_step,))

    monkeypatch.setattr(batch, "run_surface", substitute)
    with pytest.raises(BatchInvariantError, match="proof history"):
        run_proof("0 = 0", ("symm",), request_id="forged-history")


def test_failure_trace_error_must_match_the_raised_tactic_error(monkeypatch) -> None:
    def disagree(owner, line, *, capabilities, record_trace=True):
        del capabilities
        assert record_trace is True
        owner.trace.failure(owner.state, 0, line, TacticError("trace diagnostic"))
        raise TacticError("returned diagnostic")

    monkeypatch.setattr(batch, "run_surface", disagree)
    with pytest.raises(BatchInvariantError, match="non-transactional trace"):
        run_proof("0 = 0", ("refl",), request_id="forged-error")


def test_open_result_goals_reuse_proof_wide_trace_metavariable_aliases() -> None:
    result = run_proof(
        "0 = 0",
        ("trans ?", "refl", "trans ?"),
        request_id="proof-wide-aliases",
    )

    assert result.status == "open"
    assert result.trace is not None
    assert result.goals == tuple(result.trace[-2]["goals_after"])
    assert any("?t2" in goal for goal in result.goals)


def test_trace_sink_tactic_errors_and_short_writes_are_fail_stop() -> None:
    def tactic_error_sink(_text: str):
        raise TacticError("this is trace I/O, not a tactic failure")

    with pytest.raises(TraceSinkError, match="trace sink failed"):
        run_proof(
            "0 = 0",
            ("refl",),
            request_id="sink-error",
            on_error="continue",
            trace_sink=tactic_error_sink,
        )

    class ShortSink:
        def write(self, text: str) -> int:
            return len(text) // 2

    with pytest.raises(TraceSinkError, match="accepted"):
        run_proof(
            "0 = 0",
            ("refl",),
            request_id="short-write",
            trace_sink=ShortSink(),
        )


@pytest.mark.parametrize("session_id", ("bad\nline", "bad\u202eformat", "\ud800"))
def test_injected_session_ids_must_be_export_safe(session_id: str) -> None:
    with pytest.raises(BatchRequestError, match="session_id"):
        run_proof("0 = 0", ("refl",), session_id=session_id)


def test_verify_request_rejects_a_trace_sink_instead_of_ignoring_it() -> None:
    request = {
        "v": 1,
        "id": "quiet-sink",
        "theorem": "0 = 0",
        "tactics": ["refl"],
    }
    with pytest.raises(BatchRequestError, match="cannot receive a trace sink"):
        execute_request(request, mode="verify", trace_sink=io.StringIO())


def test_traced_surface_cannot_silence_or_forge_transition_history(
    monkeypatch,
) -> None:
    real_run_surface = run_surface

    def silent(owner, line, *, capabilities, record_trace=True):
        del record_trace
        return real_run_surface(
            owner,
            line,
            capabilities=capabilities,
            record_trace=False,
        )

    monkeypatch.setattr(batch, "run_surface", silent)
    with pytest.raises(BatchInvariantError, match="without a trace transition"):
        run_proof("0 = 0", ("refl",), request_id="silent-trace")

    def extra(owner, line, *, capabilities, record_trace=True):
        candidate = real_run_surface(
            owner,
            line,
            capabilities=capabilities,
            record_trace=record_trace,
        )
        candidate.trace.success(candidate.state, 0, "forged no-op", candidate.state)
        return candidate

    monkeypatch.setattr(batch, "run_surface", extra)
    with pytest.raises(BatchInvariantError, match="multiple trace transitions"):
        run_proof("0 = 0", ("refl",), request_id="extra-trace")

    def broken(owner, line, *, capabilities, record_trace=True):
        candidate = real_run_surface(
            owner,
            line,
            capabilities=capabilities,
            record_trace=False,
        )
        if record_trace:
            candidate.trace.success(owner.state, 0, line, owner.state)
        return candidate

    monkeypatch.setattr(batch, "run_surface", broken)
    with pytest.raises(BatchInvariantError, match="returned state"):
        run_proof("0 = 0", ("refl",), request_id="broken-trace")


def test_traced_surface_cannot_substitute_a_different_submitted_command(
    monkeypatch,
) -> None:
    real_run_surface = run_surface

    def substitute(owner, line, *, capabilities, record_trace=True):
        del line
        return real_run_surface(
            owner,
            "refl",
            capabilities=capabilities,
            record_trace=record_trace,
        )

    monkeypatch.setattr(batch, "run_surface", substitute)
    with pytest.raises(BatchInvariantError, match="submitted command"):
        run_proof("0 = 0", ("exact missing",), request_id="substituted-line")


def test_failed_surface_cannot_omit_its_transactional_error_trace(monkeypatch) -> None:
    def silent_failure(owner, line, *, capabilities, record_trace=True):
        del owner, line, capabilities, record_trace
        raise TacticError("silent failure")

    monkeypatch.setattr(batch, "run_surface", silent_failure)
    with pytest.raises(BatchInvariantError, match="without a trace transition"):
        run_proof(
            "0 = 0",
            ("exact missing", "refl"),
            request_id="silent-failure",
            on_error="continue",
        )


def test_headless_path_does_not_render_browser_panels(monkeypatch) -> None:
    import peano_lab.ui.prove as prove

    monkeypatch.setattr(
        prove,
        "render_state",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("browser panel")),
    )
    result = verify_proof("0 = 0", ("refl",), request_id="no-panel")
    assert result.status == "proved"


def test_jsonl_cli_separates_valid_raw_traces_and_recovers_from_bad_json(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "run.trace.jsonl"
    requests = "\n".join(
        (
            json.dumps(
                {
                    "v": 1,
                    "id": "traced",
                    "theorem": REFLEXIVE,
                    "tactics": list(REFLEXIVE_TACTICS),
                }
            ),
            "{not-json}",
            json.dumps(
                {
                    "v": 1,
                    "id": "quiet",
                    "theorem": "0 = 0",
                    "tactics": ["refl"],
                }
            ),
            "",
        )
    )
    completed = subprocess.run(
        [sys.executable, str(CLI), "--trace-output", str(trace_path)],
        cwd=ROOT,
        input=requests,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert completed.stderr == ""
    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    assert [response["status"] for response in responses] == [
        "proved",
        "request_error",
        "proved",
    ]
    assert responses[0]["trace_v"] == 1
    assert responses[0]["trace"] is None
    assert responses[1]["kernel_checked"] is False
    assert responses[2]["mode"] == "trace"
    assert responses[2]["trace_v"] == 1
    sessions = trace_exporter.load_trace_file(trace_path)
    assert len(sessions) == 2
    assert all(session.footer["qed"] is True for session in sessions)
    assert sessions[0].session_id != sessions[1].session_id


def test_jsonl_cli_verification_mode_needs_no_trace_artifact() -> None:
    request = json.dumps(
        {
            "v": 1,
            "id": "verify",
            "theorem": "0 = 0",
            "tactics": ["refl"],
        }
    )
    completed = subprocess.run(
        [sys.executable, str(CLI), "--verify-only"],
        cwd=ROOT,
        input=request + "\n",
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    response = json.loads(completed.stdout)
    assert response["status"] == "proved"
    assert response["mode"] == "verify"
    assert response["trace_v"] is None
    assert response["trace"] is None


@pytest.mark.parametrize(
    "raw_request",
    (
        '{"v":1,"id":"\\ud800","theorem":"0=0","tactics":["refl"]}',
        '{"v":1,"id":"\\u202e","theorem":"0=0","tactics":["refl"]}',
        '{"v":1,"id":"bad-on-error","theorem":"0=0","tactics":["refl"],"on_error":[]}',
    ),
)
def test_jsonl_cli_contains_malformed_unicode_and_unhashable_options(
    raw_request: str,
) -> None:
    completed = subprocess.run(
        [sys.executable, str(CLI), "--verify-only"],
        cwd=ROOT,
        input=raw_request + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    response = json.loads(completed.stdout)
    assert response["status"] == "request_error"
    expected_id = "" if "\\u" in raw_request else "bad-on-error"
    assert response["id"] == expected_id
    assert "\u202e" not in completed.stdout


def test_jsonl_cli_rejects_excessive_nesting_without_a_traceback() -> None:
    deeply_nested = "[" * 2_000 + "0" + "]" * 2_000
    completed = subprocess.run(
        [sys.executable, str(CLI), "--verify-only"],
        cwd=ROOT,
        input=deeply_nested + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    assert completed.stderr == ""
    response = json.loads(completed.stdout)
    assert response["status"] == "request_error"
    assert "nesting" in response["error"]


@pytest.mark.parametrize(
    "theorem",
    (
        "(" * 300 + "0=0" + ")" * 300,
        "~" * 1_000 + "0=0",
    ),
)
def test_formula_parser_recursion_is_a_structured_request_error(theorem: str) -> None:
    with pytest.raises(BatchRequestError, match="parser resource limit"):
        run_proof(theorem, ("refl",), request_id="nested-formula")


def test_surface_grouping_and_compilation_depth_never_escape_as_recursion() -> None:
    grouped = run_proof(
        "0 = 0",
        ("(" * 1_000 + "refl" + ")" * 1_000,),
        request_id="grouped",
    )
    assert grouped.status == "proved"

    nested = run_proof(
        "0 = 0",
        ("repeat " * 200 + "refl",),
        request_id="nested-tactical",
    )
    assert nested.status == "tactic_limit"
    assert nested.engine_steps == 0
    assert nested.trace is not None
    assert nested.trace[0]["status"] == "error"


def test_jsonl_cli_rejects_invalid_utf8_as_a_structured_request_error() -> None:
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "ascii:strict"
    completed = subprocess.run(
        [sys.executable, str(CLI), "--verify-only"],
        cwd=ROOT,
        input=b"\xff\n",
        env=environment,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    assert completed.stderr == b""
    response = json.loads(completed.stdout.decode("utf-8"))
    assert response["status"] == "request_error"
    assert "UTF-8" in response["error"]


def test_jsonl_cli_is_utf8_portable_under_an_ascii_process_locale() -> None:
    environment = os.environ.copy()
    environment["PYTHONIOENCODING"] = "ascii:strict"
    request = b'{"v":1,"id":"ascii-locale","theorem":"forall n. n=n","tactics":["intro n","refl"]}\n'
    completed = subprocess.run(
        [sys.executable, str(CLI), "--verify-only"],
        cwd=ROOT,
        input=request,
        env=environment,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    response = json.loads(completed.stdout.decode("ascii"))
    assert response["status"] == "proved"
    assert response["theorem"] == "∀ x. x = x"


def test_session_hash_recursion_is_a_request_error_not_a_fatal_crash() -> None:
    nested: object = 0
    for _ in range(2_000):
        nested = [nested]
    with pytest.raises(BatchRequestError, match="deterministically hashed"):
        batch_cli._session_id(nested, ordinal=1, environment_sha256="0" * 64)


def test_library_allowlist_changes_cli_environment_and_session_identity(
    tmp_path: Path,
) -> None:
    request = json.dumps(
        {"v": 1, "id": "same", "theorem": "0 = 0", "tactics": ["refl"]}
    )
    records = []
    for index, extra in enumerate(([], ["--allow-theorem", "add_comm"]), 1):
        trace_path = tmp_path / f"run-{index}.jsonl"
        completed = subprocess.run(
            [
                sys.executable,
                str(CLI),
                "--trace-output",
                str(trace_path),
                "--environment",
                "model-v1",
                *extra,
            ],
            cwd=ROOT,
            input=request + "\n",
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == 0
        records.append(json.loads(completed.stdout))
    assert records[0]["environment_sha256"] != records[1]["environment_sha256"]
    assert records[0]["session"] != records[1]["session"]


@pytest.mark.parametrize("content", ("", "{not-json}\n"))
def test_empty_or_all_invalid_generation_publishes_no_trace_artifact(
    tmp_path: Path,
    content: str,
) -> None:
    trace_path = tmp_path / "must-not-exist.jsonl"
    completed = subprocess.run(
        [sys.executable, str(CLI), "--trace-output", str(trace_path)],
        cwd=ROOT,
        input=content,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    if content:
        assert json.loads(completed.stdout)["status"] == "request_error"
    else:
        assert completed.stdout == ""
    assert not trace_path.exists()
    assert list(tmp_path.glob("*.partial")) == []


def test_oversized_numeral_requests_are_rejected_without_starting_a_trace(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "must-not-exist.jsonl"
    requests = "\n".join(
        (
            json.dumps(
                {
                    "v": 1,
                    "id": "bad-theorem",
                    "theorem": "100000000x = 0",
                    "tactics": ["refl"],
                }
            ),
            json.dumps(
                {
                    "v": 1,
                    "id": "bad-tactic",
                    "theorem": "exists x. x = x",
                    "tactics": ["exists 100000000"],
                }
            ),
            "",
        )
    )
    completed = subprocess.run(
        [sys.executable, str(CLI), "--trace-output", str(trace_path)],
        cwd=ROOT,
        input=requests,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    responses = [json.loads(line) for line in completed.stdout.splitlines()]
    assert [record["status"] for record in responses] == [
        "request_error",
        "request_error",
    ]
    assert not trace_path.exists()


def test_fail_fast_discards_even_a_nonempty_staged_trace(tmp_path: Path) -> None:
    trace_path = tmp_path / "must-not-exist.jsonl"
    valid = json.dumps(
        {"v": 1, "id": "valid", "theorem": "0 = 0", "tactics": ["refl"]}
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(CLI),
            "--trace-output",
            str(trace_path),
            "--fail-fast",
        ],
        cwd=ROOT,
        input=valid + "\n{not-json}\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    assert completed.stdout == ""
    assert not trace_path.exists()
    assert list(tmp_path.glob("*.partial")) == []


def test_unexpected_batch_failure_never_publishes_final_trace(
    tmp_path: Path,
    monkeypatch,
) -> None:
    trace_path = tmp_path / "must-not-exist.jsonl"
    request = json.dumps(
        {"v": 1, "id": "boom", "theorem": "0 = 0", "tactics": ["refl"]}
    )
    monkeypatch.setattr(
        batch_cli,
        "execute_request",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(batch_cli.sys, "stdin", io.StringIO(request + "\n"))
    output = io.StringIO()
    errors = io.StringIO()
    monkeypatch.setattr(batch_cli.sys, "stdout", output)
    monkeypatch.setattr(batch_cli.sys, "stderr", errors)

    assert batch_cli.main(["--trace-output", str(trace_path)]) == 4
    assert output.getvalue() == ""
    assert not trace_path.exists()
    assert len(list(tmp_path.glob("*.partial"))) == 1
    assert "fatal batch error" in errors.getvalue()


def test_trace_publish_failure_suppresses_staged_success_results(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    trace_path = tmp_path / "must-not-exist.jsonl"
    request = json.dumps(
        {"v": 1, "id": "proved", "theorem": "0 = 0", "tactics": ["refl"]}
    )
    monkeypatch.setattr(batch_cli.sys, "stdin", io.StringIO(request + "\n"))
    output = io.StringIO()
    errors = io.StringIO()
    monkeypatch.setattr(batch_cli.sys, "stdout", output)
    monkeypatch.setattr(batch_cli.sys, "stderr", errors)
    monkeypatch.setattr(
        batch_cli,
        "_publish_trace_stage",
        lambda *args: (_ for _ in ()).throw(OSError("injected link failure")),
    )

    assert batch_cli.main(["--trace-output", str(trace_path)]) == 4
    assert output.getvalue() == ""
    assert not trace_path.exists()
    assert "cannot publish trace output" in errors.getvalue()


def test_long_open_certificate_has_a_complete_non_recursive_trace_footer(
    tmp_path: Path,
) -> None:
    trace_path = tmp_path / "long-open.jsonl"
    request = json.dumps(
        {
            "v": 1,
            "id": "long-open",
            "theorem": "0 = 0",
            "tactics": ["symm"] * 500,
        }
    )
    completed = subprocess.run(
        [sys.executable, str(CLI), "--trace-output", str(trace_path)],
        cwd=ROOT,
        input=request + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    response = json.loads(completed.stdout)
    assert response["status"] == "tactic_limit"
    assert response["engine_steps"] == 255
    assert response["failed_step"] == 256
    sessions = trace_exporter.load_trace_file(trace_path)
    assert len(sessions) == 1
    assert sessions[0].footer["qed"] is False
    assert sessions[0].footer["tactic_count"] == 256


@pytest.mark.parametrize(
    "wrapper",
    (
        lambda command: command,
        lambda command: f"focus 1 {command}",
        lambda command: f"all_goals {command}",
        lambda command: f"({command})",
    ),
)
def test_live_proof_depth_limit_covers_direct_and_tactical_merges(wrapper) -> None:
    commands = tuple(wrapper("symm") for _ in range(400)) + (wrapper("refl"),)
    traced = run_proof("0 = 0", commands, request_id="depth-traced")
    quiet = verify_proof("0 = 0", commands, request_id="depth-quiet")
    assert traced.status == quiet.status == "tactic_limit"
    assert traced.kernel_checked is quiet.kernel_checked is False
    assert traced.engine_steps == quiet.engine_steps == 255
    assert traced.failed_step == quiet.failed_step == 256
    assert traced.trace is not None
    assert traced.trace[-2]["status"] == "error"
    assert traced.trace[-1]["qed"] is False


@pytest.mark.parametrize(
    "bad",
    (
        '{"v":1,"v":1,"id":"dup","theorem":"0=0","tactics":["refl"]}',
        '{"v":1,"id":"nan","theorem":"0=0","tactics":["refl"],"x":NaN}',
    ),
)
def test_jsonl_cli_rejects_duplicate_keys_and_nonfinite_numbers(bad: str) -> None:
    completed = subprocess.run(
        [sys.executable, str(CLI), "--verify-only"],
        cwd=ROOT,
        input=bad + "\n",
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    response = json.loads(completed.stdout)
    assert response["status"] == "request_error"
    assert response["kernel_checked"] is False
