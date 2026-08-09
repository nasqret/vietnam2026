"""Terminal-host tests for the checked Hydra assistant preview."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from peano_lab.ui.prove import run_surface


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
REPL_PATH = REPOSITORY_ROOT / "scripts" / "peano_hydra_assistant_repl.py"


def _load_repl():
    spec = importlib.util.spec_from_file_location(
        "_test_peano_hydra_assistant_repl",
        REPL_PATH,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


REPL = _load_repl()

from training.peano_hydra.interactive_assistant import (  # noqa: E402
    attach_qwen_response,
    prepare_qwen_request,
    qwen_prompt,
    start_hydra_assistant,
)
from training.peano_hydra.macros import Rewrite, macro_object  # noqa: E402
from training.peano_hydra.qwen_hydra_bridge import (  # noqa: E402
    QWEN_HYDRA_PROPOSAL_FORMAT,
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
    executable = tmp_path / "fake-vampire.py"
    status = "Theorem" if theorem else "Unknown"
    executable.write_text(
        f"#!{sys.executable}\n"
        "from pathlib import Path\n"
        "import sys\n"
        "assert sys.argv[1:3] == ['--mode', 'vampire']\n"
        "assert b'fof(goal,conjecture,' in Path(sys.argv[3]).read_bytes()\n"
        f"print('% SZS status {status} for hydra_repl')\n",
        encoding="utf-8",
    )
    executable.chmod(0o700)
    return executable


def _solver(executable: Path) -> VampireLiveSolver:
    return VampireLiveSolver(
        str(executable.resolve()),
        hashlib.sha256(executable.read_bytes()).hexdigest(),
        VAMPIRE_LIVE_MODE,
        VampireLiveBounds(
            max_wall_time_ms=30_000,
            max_cpu_time_seconds=2,
            max_memory_bytes=512 * 1024 * 1024,
            max_output_bytes=4_096,
        ),
    )


def test_prompted_repl_runs_tactics_goals_script_undo_help_and_quit() -> None:
    lines = iter(
        (
            "0 + 0 = 0",
            ":help",
            ":goals",
            "rewrite PA3",
            ":script",
            ":undo",
            "apply PA3",
            ":script",
            ":quit",
        )
    )
    prompts: list[str] = []
    output: list[str] = []

    def read(prompt: str) -> str:
        prompts.append(prompt)
        return next(lines)

    assert REPL.run_repl(read=read, write=output.append) == 0
    rendered = "\n".join(output)
    assert prompts[0] == "theorem> "
    assert prompts[1:] == ["hydra> "] * 8
    assert "PEANO HYDRA — CHECKED INTERACTIVE PREVIEW" in rendered
    assert "Hydra commands" in rendered
    assert "Goal 1/1\n  ⊢ 0 + 0 = 0" in rendered
    assert "ACCEPTED [manual]\n  rewrite PA3" in rendered
    assert "pa prove 0 + 0 = 0\nrewrite PA3" in rendered
    assert "Restored the preceding immutable session." in rendered
    assert "ACCEPTED [manual]\n  apply PA3" in rendered
    assert "QED — fresh original-goal kernel replay accepted." in rendered
    assert "pa prove 0 + 0 = 0\napply PA3\nqed" in rendered
    assert rendered.endswith("Session closed.")


def test_qwen_prompt_json_accept_discard_and_undo_are_explicit_and_persistent() -> None:
    initial = start_hydra_assistant("0 + 0 = 0")
    history = REPL.ConsoleHistory((initial,))
    output: list[str] = []

    prepared_history, close = REPL.dispatch(
        history,
        ":qwen PA3",
        solver=None,
        write=output.append,
    )
    assert close is False
    prepared = prepared_history.current
    assert prepared.owner is initial.owner
    assert qwen_prompt(prepared) in output

    rejected_history, _ = REPL.dispatch(
        prepared_history,
        ":model premises: PA3",
        solver=None,
        write=output.append,
    )
    assert rejected_history is prepared_history
    assert "strict JSON object" in output[-2]

    raw = _proposal(
        ["PA3"],
        [macro_object(Rewrite("PA3", "forward", None))],
    )
    attached_history, _ = REPL.dispatch(
        prepared_history,
        f":model {raw}",
        solver=None,
        write=output.append,
    )
    attached = attached_history.current
    assert attached.owner is initial.owner
    assert attached.pending_qwen is not None
    assert attached.pending_qwen.proposal is not None

    accepted_history, _ = REPL.dispatch(
        attached_history,
        ":accept",
        solver=None,
        write=output.append,
    )
    assert accepted_history.current.owner is not initial.owner
    assert accepted_history.current.pending_qwen is None

    restored, changed = accepted_history.undo()
    assert changed is True
    assert restored.current is attached
    discarded, _ = REPL.dispatch(
        restored,
        ":discard",
        solver=None,
        write=output.append,
    )
    assert discarded.current.owner is initial.owner
    assert discarded.current.pending_qwen is None
    recovered, changed = discarded.undo()
    assert changed is True
    assert recovered.current is attached

    rendered = "\n".join(output)
    assert "Exact prompt follows:" in rendered
    assert '"name":"PA3","statement":"∀ x. x + 0 = x"' in rendered
    assert "Attached inert Qwen proposal: 1 premise(s), 1 typed macro(s)" in rendered
    assert "ACCEPTED [qwen-macros]\n  rewrite PA3" in rendered
    assert "Pending Qwen data discarded; proof owner unchanged." in rendered


def test_direct_and_qwen_selected_vampire_paths_commit_only_checked_commands(
    tmp_path: Path,
) -> None:
    solver = _solver(_fake_vampire(tmp_path))
    output: list[str] = []

    direct = REPL.ConsoleHistory((start_hydra_assistant("0 + 0 = 0"),))
    direct_after, _ = REPL.dispatch(
        direct,
        ":vampire PA3",
        solver=solver,
        write=output.append,
    )
    assert direct_after.current.is_done
    assert direct_after.current.owner.replay_steps[-1].command == "apply PA3"

    initial = start_hydra_assistant("0 + 0 = 0")
    prepared = prepare_qwen_request(initial, ("PA3",))
    attached = attach_qwen_response(prepared, _proposal(["PA3"], []))
    qwen = REPL.ConsoleHistory((initial, prepared, attached))
    qwen_after, _ = REPL.dispatch(
        qwen,
        ":resolve",
        solver=solver,
        write=output.append,
    )
    assert qwen_after.current.is_done
    assert qwen_after.current.owner.replay_steps[-1].command == "apply PA3"

    rendered = "\n".join(output)
    assert "ACCEPTED [vampire]\n  apply PA3" in rendered
    assert "ACCEPTED [qwen-vampire]\n  apply PA3" in rendered
    assert rendered.count("solver-trace-sha256:") == 2
    assert rendered.count("QED — fresh original-goal kernel replay accepted.") == 2


def test_missing_solver_fails_safely_without_losing_pending_qwen_or_proof_state() -> None:
    initial = start_hydra_assistant("0 + 0 = 0")
    prepared = prepare_qwen_request(initial, ("PA3",))
    attached = attach_qwen_response(prepared, _proposal(["PA3"], []))
    history = REPL.ConsoleHistory((initial, prepared, attached))
    output: list[str] = []

    after_resolve, _ = REPL.dispatch(
        history,
        ":resolve",
        solver=None,
        write=output.append,
    )
    after_direct, _ = REPL.dispatch(
        after_resolve,
        ":vampire PA3",
        solver=None,
        write=output.append,
    )
    assert after_resolve is history
    assert after_direct is history
    assert after_direct.current is attached
    assert after_direct.current.pending_qwen is not None
    assert not after_direct.current.is_done

    completed, _ = REPL.dispatch(
        after_direct,
        "apply PA3",
        solver=None,
        write=output.append,
    )
    assert completed.current.is_done
    assert completed.current.pending_qwen is None
    rendered = "\n".join(output)
    assert rendered.count("Vampire unavailable:") == 2
    assert "ACCEPTED [manual]" in rendered


def test_solver_configuration_requires_absolute_path_and_exact_sha(
    tmp_path: Path,
) -> None:
    parser = REPL.build_parser()
    assert REPL.configured_solver(parser.parse_args([])) is None

    with pytest.raises(ValueError, match="supplied together"):
        REPL.configured_solver(parser.parse_args(["--vampire", "/bin/false"]))
    with pytest.raises(ValueError, match="absolute path"):
        REPL.configured_solver(
            parser.parse_args(
                [
                    "--vampire",
                    "relative-vampire",
                    "--vampire-sha256",
                    "0" * 64,
                ]
            )
        )
    with pytest.raises(ValueError, match="SHA-256"):
        REPL.configured_solver(
            parser.parse_args(
                [
                    "--vampire",
                    "/bin/false",
                    "--vampire-sha256",
                    "not-a-digest",
                ]
            )
        )

    executable = _fake_vampire(tmp_path)
    digest = hashlib.sha256(executable.read_bytes()).hexdigest()
    configured = REPL.configured_solver(
        parser.parse_args(
            [
                "--vampire",
                str(executable.resolve()),
                "--vampire-sha256",
                digest,
                "--vampire-wall-time-ms",
                "2500",
                "--vampire-cpu-time-seconds",
                "2",
                "--vampire-memory-bytes",
                str(256 * 1024 * 1024),
                "--vampire-output-bytes",
                "8192",
            ]
        )
    )
    assert configured is not None
    assert configured.executable == str(executable.resolve())
    assert configured.executable_sha256 == digest
    assert configured.arguments == VAMPIRE_LIVE_MODE
    assert configured.bounds.max_wall_time_ms == 2_500
    assert configured.bounds.max_output_bytes == 8_192

    with pytest.raises(SystemExit) as too_large:
        parser.parse_args(
            [
                "--vampire-wall-time-ms",
                str(REPL.CONSOLE_MAX_WALL_TIME_MS + 1),
            ]
        )
    assert too_large.value.code == 2


def test_cli_theorem_option_is_runnable_without_a_solver() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(REPL_PATH),
            "--theorem",
            "0 + 0 = 0",
        ],
        input=":vampire PA3\napply PA3\n:script\n:quit\n",
        text=True,
        capture_output=True,
        check=False,
        cwd=REPOSITORY_ROOT,
    )
    assert completed.returncode == 0
    assert "Vampire unavailable:" in completed.stdout
    assert "ACCEPTED [manual]" in completed.stdout
    assert "pa prove 0 + 0 = 0\napply PA3\nqed" in completed.stdout
    assert completed.stderr == ""


def test_invalid_start_and_prompt_eof_never_claim_a_theorem() -> None:
    invalid_output: list[str] = []
    assert REPL.run_repl("free_variable = 0", write=invalid_output.append) == 2
    assert "Cannot start theorem:" in invalid_output[-1]

    eof_output: list[str] = []

    def eof(_prompt: str) -> str:
        raise EOFError

    assert REPL.run_repl(read=eof, write=eof_output.append) == 0
    assert eof_output[-1] == "No theorem supplied; session closed."


def test_source_has_no_network_or_model_loading_path() -> None:
    source = REPL_PATH.read_text(encoding="utf-8")
    for forbidden in (
        "requests",
        "urllib",
        "socket",
        "transformers",
        "torch",
        "load_model",
    ):
        assert forbidden not in source
    assert "proof_authority" not in source
    assert "run_vampire_assistance" in source
    assert "run_manual_tactic" in source


def test_script_and_quit_do_not_mint_qed_from_an_unreceipted_empty_goal() -> None:
    initial = start_hydra_assistant("0 + 0 = 0")
    closed = run_surface(
        initial.owner.session,
        "apply PA3",
        capabilities=initial.owner.capabilities,
        record_trace=False,
    )
    unreceipted = REPL.HydraAssistantSession(initial.owner.with_session(closed))
    assert unreceipted.is_done is True
    assert unreceipted.kernel_accepted is False
    assert not REPL._script(unreceipted).endswith("qed")

    output: list[str] = []
    _, quit_now = REPL.dispatch(
        REPL.ConsoleHistory((unreceipted,)),
        ":quit",
        solver=None,
        write=output.append,
    )
    assert quit_now is True
    assert output == ["Session closed; the unfinished theorem was not claimed."]
