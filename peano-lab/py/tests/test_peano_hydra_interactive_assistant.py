"""Functional join tests for the interactive Qwen + Vampire assistant."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.kernel.checker import check  # noqa: E402
from training.peano_hydra.interactive_assistant import (  # noqa: E402
    HydraAssistantAccepted,
    HydraAssistantRejected,
    HydraAssistantSession,
    PendingQwenProposal,
    apply_qwen_macros,
    ask_qwen,
    attach_qwen_response,
    current_script,
    discard_qwen,
    prepare_qwen_request,
    qwen_prompt,
    render_hydra_state,
    resolve_qwen_premises,
    run_manual_tactic,
    run_vampire_assistance,
    start_hydra_assistant,
)
from training.peano_hydra.macros import Rewrite, Split, macro_object  # noqa: E402
from training.peano_hydra.qwen_hydra_bridge import (  # noqa: E402
    QWEN_HYDRA_PROPOSAL_FORMAT,
    QwenHydraProposal,
)
from training.peano_hydra.vampire_live import (  # noqa: E402
    VAMPIRE_LIVE_MODE,
    VampireLiveBounds,
    VampireLiveSolver,
)


def _proposal(premises: list[str], macros: list[object]) -> str:
    return json.dumps(
        {
            "format": QWEN_HYDRA_PROPOSAL_FORMAT,
            "v": 1,
            "premises": premises,
            "macros": macros,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _fake_vampire(tmp_path: Path, *, theorem: bool = True) -> Path:
    path = tmp_path / "fake-vampire.py"
    status = "Theorem" if theorem else "Unknown"
    path.write_text(
        f"#!{sys.executable}\n"
        "from pathlib import Path\n"
        "import sys\n"
        "assert sys.argv[1:3] == ['--mode', 'vampire']\n"
        "assert b'fof(goal,conjecture,' in Path(sys.argv[3]).read_bytes()\n"
        f"print('% SZS status {status} for hydra_console')\n",
        encoding="utf-8",
    )
    path.chmod(0o700)
    return path


def _solver(path: Path) -> VampireLiveSolver:
    return VampireLiveSolver(
        str(path.resolve()),
        hashlib.sha256(path.read_bytes()).hexdigest(),
        VAMPIRE_LIVE_MODE,
        VampireLiveBounds(
            max_wall_time_ms=30_000,
            max_cpu_time_seconds=2,
            max_memory_bytes=512 * 1024 * 1024,
            max_output_bytes=4_096,
        ),
    )


def test_manual_tactics_commit_only_success_and_freshly_check_qed() -> None:
    session = start_hydra_assistant("0 + 0 = 0")
    assert render_hydra_state(session) == "Goal 1/1\n  ⊢ 0 + 0 = 0"

    rejected = run_manual_tactic(session, "apply PA4")
    assert type(rejected) is HydraAssistantRejected
    assert rejected.session is session
    assert current_script(session) == ()

    accepted = run_manual_tactic(session, "apply PA3")
    assert type(accepted) is HydraAssistantAccepted
    assert accepted.session.is_done
    assert accepted.public_commands == ("apply PA3",)
    assert current_script(accepted.session) == ("apply PA3",)
    assert accepted.certificate is not None
    assert accepted.session.checked_certificate == accepted.certificate
    assert accepted.kernel_accepted is True
    assert check((), accepted.certificate, session.owner.original_target)
    assert "fresh original-goal kernel" in render_hydra_state(accepted.session)


def test_qwen_request_and_response_are_inert_until_explicit_acceptance() -> None:
    session = start_hydra_assistant("0 + 0 = 0")
    prepared = prepare_qwen_request(session, ("PA3",))
    assert prepared.owner is session.owner
    assert current_script(prepared) == ()
    prompt = qwen_prompt(prepared)
    assert '<task>Propose premises and typed Peano Hydra macros. Do not claim QED.</task>' in prompt
    assert '"name":"PA3","statement":"∀ x. x + 0 = x"' in prompt

    attached = attach_qwen_response(
        prepared,
        _proposal(
            ["PA3"],
            [macro_object(Rewrite("PA3", "forward", None))],
        ),
    )
    assert attached.owner is session.owner
    assert attached.pending_qwen is not None
    assert attached.pending_qwen.proposal is not None
    assert attached.pending_qwen.proposal.session_mutated is False
    assert current_script(attached) == ()

    accepted = apply_qwen_macros(attached)
    assert type(accepted) is HydraAssistantAccepted
    assert accepted.channel == "qwen-macros"
    assert accepted.public_commands == ("rewrite PA3",)
    assert accepted.proposal_sha256 == attached.pending_qwen.proposal.raw_sha256
    assert current_script(accepted.session) == ("rewrite PA3",)
    assert not accepted.session.is_done
    assert accepted.session.pending_qwen is None


def test_multi_macro_qwen_failure_rolls_back_the_entire_outer_transaction() -> None:
    session = start_hydra_assistant("0 + 0 = 0")
    prepared = prepare_qwen_request(session, ("PA3",))
    attached = attach_qwen_response(
        prepared,
        _proposal(
            ["PA3"],
            [
                macro_object(Rewrite("PA3", "forward", None)),
                macro_object(Split("conjunction")),
            ],
        ),
    )

    rejected = apply_qwen_macros(attached)
    assert type(rejected) is HydraAssistantRejected
    assert rejected.session is attached
    assert rejected.session.owner is session.owner
    assert current_script(rejected.session) == ()


def test_injected_qwen_transport_can_select_premises_for_checked_vampire(
    tmp_path: Path,
) -> None:
    session = start_hydra_assistant("0 + 0 = 0")
    observed_prompts: list[str] = []

    def model(prompt: str) -> str:
        observed_prompts.append(prompt)
        return _proposal(["PA3"], [])

    proposed = ask_qwen(session, ("PA3",), model)
    assert proposed.owner is session.owner
    assert len(observed_prompts) == 1
    assert proposed.pending_qwen is not None
    assert proposed.pending_qwen.proposal is not None
    proposal_sha = proposed.pending_qwen.proposal.raw_sha256

    accepted = resolve_qwen_premises(
        proposed,
        _solver(_fake_vampire(tmp_path)),
    )
    assert type(accepted) is HydraAssistantAccepted
    assert accepted.channel == "qwen-vampire"
    assert accepted.public_commands == ("apply PA3",)
    assert accepted.proposal_sha256 == proposal_sha
    assert accepted.solver_trace_sha256 is not None
    assert accepted.session.is_done
    assert accepted.certificate is not None
    assert check((), accepted.certificate, session.owner.original_target)


def test_forged_solver_status_and_masked_model_names_never_mutate_the_owner(
    tmp_path: Path,
) -> None:
    false_session = start_hydra_assistant("0 = 1")
    vampire = run_vampire_assistance(
        false_session,
        (),
        _solver(_fake_vampire(tmp_path)),
    )
    assert type(vampire) is HydraAssistantRejected
    assert vampire.session is false_session
    assert vampire.solver_trace_sha256 is not None
    assert current_script(false_session) == ()

    session = start_hydra_assistant("0 + 0 = 0")
    prepared = prepare_qwen_request(session, ("PA3",))
    try:
        attach_qwen_response(prepared, _proposal(["PA4"], []))
    except ValueError as exc:
        assert "allow-list" in str(exc)
    else:  # pragma: no cover - fail-closed assertion
        raise AssertionError("masked model premise was accepted")
    assert prepared.owner is session.owner
    assert current_script(session) == ()

    unselected_axiom = attach_qwen_response(
        prepared,
        _proposal(
            ["PA3"],
            [macro_object(Rewrite("PA4", "forward", None))],
        ),
    )
    rejected_axiom = apply_qwen_macros(unselected_axiom)
    assert type(rejected_axiom) is HydraAssistantRejected
    assert rejected_axiom.session is unselected_axiom
    assert "was not selected" in rejected_axiom.error
    assert current_script(session) == ()


def test_pending_proposal_is_discardable_and_manual_progress_invalidates_it() -> None:
    session = start_hydra_assistant("0 + 0 = 0")
    proposed = ask_qwen(
        session,
        ("PA3",),
        lambda _: _proposal(["PA3"], []),
    )
    assert discard_qwen(proposed).owner is session.owner
    assert discard_qwen(proposed).pending_qwen is None

    advanced = run_manual_tactic(proposed, "rewrite PA3")
    assert type(advanced) is HydraAssistantAccepted
    assert advanced.session.pending_qwen is None

    # Even a caller manually combining an old proposal with a newer owner
    # cannot execute it: the exact rendered goal/retrieval binding is checked
    # again at the execution boundary.
    try:
        HydraAssistantSession(advanced.session.owner, proposed.pending_qwen)
    except ValueError as exc:
        assert "another proof owner" in str(exc)
    else:  # pragma: no cover - constructor must reject stale ownership
        raise AssertionError("stale pending data entered a newer owner")

    # Bypassing the frozen dataclass constructor still cannot bypass the
    # execution-time owner/request check.
    forged = object.__new__(HydraAssistantSession)
    object.__setattr__(forged, "owner", advanced.session.owner)
    object.__setattr__(forged, "pending_qwen", proposed.pending_qwen)
    object.__setattr__(forged, "checked_certificate", None)
    stale = apply_qwen_macros(forged)
    assert type(stale) is HydraAssistantRejected
    assert stale.session is forged
    assert "stale" in stale.error


def test_forged_proposal_object_and_unreceipted_closed_state_cannot_overclaim() -> None:
    session = start_hydra_assistant("0 + 0 = 0")
    raw = _proposal(
        ["PA3"],
        [macro_object(Rewrite("PA3", "forward", None))],
    )
    attached = attach_qwen_response(
        prepare_qwen_request(session, ("PA3",)),
        raw,
    )
    assert attached.pending_qwen is not None
    assert attached.pending_qwen.proposal is not None
    valid = attached.pending_qwen.proposal
    forged = QwenHydraProposal(
        request_sha256=valid.request_sha256,
        prompt_sha256=valid.prompt_sha256,
        raw_sha256=valid.raw_sha256,
        premises=(),
        macro_lines=valid.macro_lines,
        public_commands=valid.public_commands,
        dispatch_requests=valid.dispatch_requests,
    )
    try:
        PendingQwenProposal(
            attached.pending_qwen.request,
            attached.pending_qwen.owner_binding_sha256,
            forged,
            attached.pending_qwen.response_bytes,
        )
    except ValueError as exc:
        assert "differs from its exact response bytes" in str(exc)
    else:  # pragma: no cover - forged object must not acquire provenance
        raise AssertionError("forged Qwen proposal acquired response provenance")

    # An empty goal list alone is not a QED receipt.  Directly constructing a
    # closed owner without the fresh-replay certificate renders neutrally.
    from peano_lab.ui.prove import run_surface

    closed_proof_session = run_surface(
        session.owner.session,
        "apply PA3",
        capabilities=session.owner.capabilities,
        record_trace=False,
    )
    unreceipted = HydraAssistantSession(session.owner.with_session(closed_proof_session))
    assert unreceipted.is_done is True
    assert unreceipted.kernel_accepted is False
    assert render_hydra_state(unreceipted) == (
        "No open goals — no attached fresh-kernel QED receipt."
    )
