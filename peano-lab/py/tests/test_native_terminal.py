"""The model-free terminal exposes the current checked theorem library."""

from __future__ import annotations

import importlib.util
from io import StringIO
from pathlib import Path
import subprocess
import sys


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
NATIVE_SHELL = REPOSITORY_ROOT / "scripts" / "peano_native_shell.py"


def _run(
    *arguments: str,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(NATIVE_SHELL), *arguments],
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
        cwd=REPOSITORY_ROOT,
    )


def _load_native_shell():
    spec = importlib.util.spec_from_file_location(
        "_test_peano_native_shell",
        NATIVE_SHELL,
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_native_version_and_library_inventory_are_current() -> None:
    version = _run("--version")
    assert version.returncode == 0
    assert version.stdout == "Peano Lab native shell · 432 theorem specifications\n"
    assert version.stderr == ""

    inventory = _run("-c", "pa lib")
    assert inventory.returncode == 0
    assert "432 scripted theorems" in inventory.stdout
    assert "mul_one" in inventory.stdout
    assert "prime_bounded_nonzero_mod_inverse" in inventory.stdout
    assert inventory.stderr == ""

    conflicting = _run("--version", "-c", "pa prove 0 = S 0")
    assert conflicting.returncode == 2
    assert "not allowed with argument --version" in conflicting.stderr
    assert "Peano Lab native shell" not in conflicting.stdout


def test_native_batch_reuses_a_library_theorem_and_reaches_qed() -> None:
    completed = _run(
        "-c",
        "pa prove forall n. n * 1 + 0 = n",
        "-c",
        "use mul_one",
        "-c",
        "intro n",
        "-c",
        "specialize mul_one n",
        "-c",
        "rewrite mul_one",
        "-c",
        "simp",
        "-c",
        "qed",
    )

    assert completed.returncode == 0
    assert "mul_one : ∀ x. x · 1 = x" in completed.stdout
    assert "No open goals. QED." in completed.stdout
    assert "Checked under: Logic: intuitionistic PA (classical off)" in completed.stdout
    assert completed.stderr == ""


def test_native_batch_is_fail_fast_and_rejects_unfinished_eof() -> None:
    failed = _run("-c", "unknown command", "-c", "about")
    assert failed.returncode == 1
    assert "Unknown command 'unknown'" in failed.stdout
    assert "Soundness boundary" not in failed.stdout

    unfinished = _run(input_text="pa prove 0 = 0\n")
    assert unfinished.returncode == 1
    assert "Target\n    0 = 0" in unfinished.stdout
    assert "no unfinished theorem was claimed" in unfinished.stderr


def test_exit_words_respect_active_proof_ownership() -> None:
    idle = _run("-c", "quit")
    assert idle.returncode == 0
    assert idle.stdout == "Session closed.\n"

    active = _run("-c", "pa prove 0 = 0", "-c", "quit")
    assert active.returncode == 1
    assert "Proof aborted. No theorem was claimed." in active.stdout
    assert "Session closed." not in active.stdout


def test_interactive_eof_and_interrupt_are_clean() -> None:
    native_shell = _load_native_shell()

    def eof(_prompt: str) -> str:
        raise EOFError

    eof_output = StringIO()
    assert native_shell.run_interactive(read=eof, stdout=eof_output) == 0
    assert "PEANO LAB — NATIVE / MODEL-FREE" in eof_output.getvalue()

    def interrupted(_prompt: str) -> str:
        raise KeyboardInterrupt

    interrupt_output = StringIO()
    assert (
        native_shell.run_interactive(read=interrupted, stdout=interrupt_output)
        == 130
    )
    assert "Session interrupted; no new theorem was claimed." in (
        interrupt_output.getvalue()
    )


def test_interrupt_during_dispatch_terminates_without_a_traceback(monkeypatch) -> None:
    native_shell = _load_native_shell()

    def interrupted_dispatch(*_args, **_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(native_shell, "dispatch", interrupted_dispatch)

    interactive_output = StringIO()
    assert (
        native_shell.run_interactive(
            read=lambda _prompt: "pa lib mul_one",
            stdout=interactive_output,
        )
        == 130
    )
    assert "Session interrupted; no new theorem was claimed." in (
        interactive_output.getvalue()
    )
    assert "Traceback" not in interactive_output.getvalue()

    batch_error = StringIO()
    assert native_shell.run_batch(["pa lib"], stderr=batch_error) == 130
    assert "Native command interrupted; no new theorem was claimed." in (
        batch_error.getvalue()
    )
    assert "Traceback" not in batch_error.getvalue()


def test_closed_batch_output_pipe_is_quiet_but_not_successful() -> None:
    native_shell = _load_native_shell()

    class ClosedPipe(StringIO):
        def write(self, _value: str) -> int:
            raise BrokenPipeError

        def fileno(self) -> int:
            raise OSError("synthetic pipe has no descriptor")

    assert native_shell.run_batch(["about"], stdout=ClosedPipe()) == 141
