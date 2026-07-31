"""Model-free contracts for the native ``pa prove-model`` shell."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
SCRIPT = REPOSITORY_ROOT / "scripts" / "peano_model_lab.py"
LAUNCHER = REPOSITORY_ROOT / "pa"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

SPEC = importlib.util.spec_from_file_location("_peano_model_lab", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
MODEL_LAB = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MODEL_LAB
SPEC.loader.exec_module(MODEL_LAB)

import driver  # noqa: E402


@dataclass
class FakeAttempt:
    proof_script: str | None

    @property
    def proved(self) -> bool:
        return self.proof_script is not None

    @property
    def report(self) -> dict[str, object]:
        return {
            "search": {
                "status": "proof" if self.proved else "limit",
                "depth_reached": 2,
                "model_calls": 2,
            }
        }


@dataclass
class FakeArtifacts:
    report: Path
    proof: Path | None


class FakeLab:
    def __init__(self, owner: str | None = None) -> None:
        self.session_owner = owner
        self.lines: list[object] = []

    def run_result(self, line: object) -> dict[str, object]:
        self.lines.append(line)
        return {"out": f"lab:{line}\x1b", "failed": False}


def _shell(
    *,
    lab: object | None = None,
    search=None,
    save=None,
    live: str = "concise",
) -> tuple[object, list[str]]:
    output: list[str] = []
    attempt = FakeAttempt("pa prove 0 = 0\nrefl\nqed\n")

    def default_search(theorem, runtime, budget, *, on_event):
        del runtime, budget
        assert theorem == "0 = 0"
        if on_event is not None:
            on_event(
                {
                    "v": 1,
                    "kind": "model_prompt",
                    "model_call": 1,
                    "prompt_chars": 42,
                    "requested_candidates": 1,
                    "goals_before": ("⊢ 0 = 0",),
                    "prompt": (
                        "<task>next_tactic</task>\n"
                        "<env>peano-lab-v1;surface=model-v3</env>\n"
                    ),
                }
            )
            on_event(
                {
                    "v": 1,
                    "kind": "candidate_started",
                    "candidate_rank": 0,
                    "command": "refl",
                }
            )
            on_event(
                {
                    "v": 1,
                    "kind": "candidate_result",
                    "status": "ok",
                    "disposition": "closed_pending_kernel",
                    "command": "refl",
                    "goals_after": (),
                }
            )
            on_event(
                {
                    "v": 1,
                    "kind": "kernel_check_finished",
                    "status": "accepted",
                    "certificate_nodes": 1,
                    "unexpected": "hostile\x1b[31m",
                }
            )
        return attempt

    def default_save(value, directory):
        assert value is attempt
        return FakeArtifacts(directory / "answer.json", directory / "answer.pa")

    shell = MODEL_LAB.PeanoModelShell(
        lab_session=lab or FakeLab(),
        runtime=object(),
        budget=object(),
        results_dir=Path("results/peano-policy/interactive-local"),
        normalize_theorem=lambda theorem: theorem.strip(),
        run_checked_search=search or default_search,
        save_attempt=save or default_save,
        live_mode=live,
        write=output.append,
    )
    return shell, output


def test_shell_observes_driver_owner_without_changing_browser_driver() -> None:
    session = driver.LabSession()
    assert session._session_owner() is None
    session.run("pa prove 0 = 0")
    assert session._session_owner() == "prove"


def test_active_manual_owner_receives_the_complete_raw_line_first() -> None:
    lab = FakeLab(owner="prove")

    def forbidden(*args, **kwargs):
        raise AssertionError("model search must not intercept an active owner")

    shell, output = _shell(lab=lab, search=forbidden)
    raw = "  pa prove-model 0 = 0\t"
    outcome = shell.dispatch(raw)

    assert outcome.model_command is False
    assert outcome.exit_code == 0
    assert lab.lines == [raw]
    assert "\x1b" not in "".join(output)
    assert "\\x1b" in "".join(output)


def test_idle_exact_model_command_streams_then_saves_only_checked_attempt() -> None:
    saved: list[object] = []
    shell, output = _shell(
        save=lambda attempt, directory: (
            saved.append(attempt)
            or FakeArtifacts(directory / "run.json", directory / "run.pa")
        )
    )

    outcome = shell.dispatch("PA   prove-model   0 = 0")

    assert outcome == MODEL_LAB.ShellOutcome(True, 0)
    assert len(saved) == 1
    rendered = "\n".join(output)
    assert "[prompt #1]" in rendered
    assert "<task>next_tactic</task>" in rendered
    assert "surface=model-v3" in rendered
    assert "Goal 1: ⊢ 0 = 0" in rendered
    assert "[model] #1 refl" in rendered
    assert "[compile + fresh replay] accepted: refl" in rendered
    assert "[kernel] kernel_check_finished" in rendered
    assert "KERNEL-CHECKED PROOF" in rendered
    assert "answer" not in rendered
    assert "run.pa" in rendered and "run.json" in rendered
    assert "\x1b" not in rendered


def test_only_the_exact_idle_command_is_special() -> None:
    lab = FakeLab()
    shell, output = _shell(lab=lab)

    ordinary = shell.dispatch("pa prove-modelish 0 = 0")
    missing = shell.dispatch("pa prove-model")

    assert ordinary.model_command is False
    assert lab.lines == ["pa prove-modelish 0 = 0"]
    assert missing == MODEL_LAB.ShellOutcome(True, 2)
    assert "Usage: pa prove-model" in "\n".join(output)


def test_live_modes_are_bounded_safe_and_forward_compatible() -> None:
    concise: list[str] = []
    MODEL_LAB.LiveEventRenderer("concise", concise.append)(
        {"kind": "future_event", "extra": "ignored", "message": "bad\x1b\nline"}
    )
    assert concise
    assert "\x1b" not in concise[0]
    assert "\\x1b" in concise[0]
    assert "\\x0a" in concise[0]

    full: list[str] = []
    renderer = MODEL_LAB.LiveEventRenderer("full", full.append)
    renderer({"kind": "future_event", "extra": "visible", "prompt": "a\nb"})
    renderer(object())
    assert "event-v=missing" in "\n".join(full)
    assert "extra=visible" in "\n".join(full)

    errors: list[str] = []
    error_renderer = MODEL_LAB.LiveEventRenderer("concise", errors.append)
    error_renderer(
        {"kind": "model_error", "model_call": 3, "message": "MPS failed"}
    )
    error_renderer(
        {
            "kind": "policy_error",
            "model_call": 3,
            "depth": 2,
            "message": "decoder failed",
        }
    )
    assert errors == [
        "[model error] call #3 — MPS failed",
        "[policy error] call #3 · depth=2 — decoder failed",
    ]
    assert "prompt:" in "\n".join(full)
    assert "live malformed" in "\n".join(full)

    off: list[str] = []
    MODEL_LAB.LiveEventRenderer("off", off.append)(
        {"v": 999, "kind": "anything", "extra": object()}
    )
    assert off == []


def test_failed_or_interrupted_search_never_calls_the_saver() -> None:
    saved: list[object] = []

    def save(*args):
        saved.append(args)
        raise AssertionError("unreachable")

    for failure, expected in (
        (RuntimeError("decoder failed\x1b"), 2),
        (KeyboardInterrupt(), 130),
    ):
        def search(*args, _failure=failure, **kwargs):
            raise _failure

        shell, output = _shell(search=search, save=save)
        outcome = shell.dispatch("pa prove-model 0 = 0")
        assert outcome.exit_code == expected
        assert "no proof was published" in "\n".join(output)
    assert saved == []


def test_publication_failure_reports_possible_checked_proof_orphan() -> None:
    def fail_save(*args):
        raise OSError("disk changed\x1b")

    shell, output = _shell(save=fail_save)
    outcome = shell.dispatch("pa prove-model 0 = 0")

    assert outcome == MODEL_LAB.ShellOutcome(True, 2)
    rendered = "\n".join(output)
    assert "publication was incomplete" in rendered
    assert "proof orphan may remain" in rendered
    assert "no proof was published" not in rendered
    assert "\x1b" not in rendered


def test_interactive_loop_reuses_one_shell_and_uses_pa_prompt() -> None:
    shell, output = _shell(live="off")
    lines = iter(("pa prove-model 0 = 0",))
    prompts: list[str] = []

    def read(prompt: str) -> str:
        prompts.append(prompt)
        try:
            return next(lines)
        except StopIteration:
            raise EOFError from None

    assert MODEL_LAB.run_interactive(shell, read=read) == 0
    assert prompts == ["pa> ", "pa> "]
    assert "model loaded once" in "\n".join(output)
    assert "KERNEL-CHECKED PROOF" in "\n".join(output)


def test_cli_defaults_are_low_memory_and_support_one_shot_positionals() -> None:
    args = MODEL_LAB._parser().parse_args(
        ["prove-model", "forall", "n.", "n", "=", "n", "--device", "mps"]
    )
    assert args.command == "prove-model"
    assert args.theorem == ["forall", "n.", "n", "=", "n"]
    assert args.device == "mps"
    assert args.max_new_tokens == 64
    assert args.beam == 1
    assert args.candidates == 1
    assert args.model_calls == 32


@pytest.mark.parametrize("abbreviation", ["--adapt", "--cache", "--cache-d"])
def test_parser_rejects_abbreviated_sealed_identity_options(
    abbreviation: str,
) -> None:
    with pytest.raises(SystemExit):
        MODEL_LAB._parser().parse_args([abbreviation, "/tmp/override"])


def test_help_is_model_free_and_launcher_is_fixed_to_the_diagnostic() -> None:
    completed = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "prove-model" in completed.stdout
    assert "--live" in completed.stdout

    subprocess.run(["sh", "-n", str(LAUNCHER)], check=True)
    source = LAUNCHER.read_text(encoding="utf-8")
    assert "--diagnostic" in source
    assert 'while [ -L "$launcher_path" ]' in source
    assert "HF_HUB_OFFLINE=1" in source
    assert "TRANSFORMERS_OFFLINE=1" in source
    assert "--local-files-only" in source
    assert "prefetch_peano_base_model.py" in source
    assert "verify_peano_morning_adapter.py" in source
    assert "--verify-only" in source
    assert "qwen3-1.7b-lora-v3-morning-diagnostic-20260731-r1" in source
    assert "[startup 1/3]" in source
    assert "[startup 2/3]" in source
    assert 'case "${1-}" in' in source
    assert source.index('case "${1-}" in') < source.index(
        "prefetch_peano_base_model.py"
    )
    assert "PEANO_MODEL_PYTHON" not in source
    assert 'peano_python=python3' in source  # lightweight help only
    assert 'elif [ "$help_requested" = true ]' in source
    for option in ("--adapter", "--cache-dir"):
        refused = subprocess.run(
            [str(LAUNCHER), option, "/tmp/other", "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert refused.returncode == 2
        assert "fixed to the morning diagnostic" in refused.stderr

    for abbreviation in ("--adapt", "--cache", "--cache-d"):
        refused = subprocess.run(
            [str(LAUNCHER), abbreviation, "/tmp/other", "--help"],
            text=True,
            capture_output=True,
            check=False,
        )
        assert refused.returncode == 2


def test_explicit_model_mode_is_an_exact_alias_for_legacy_help() -> None:
    legacy = subprocess.run(
        [str(LAUNCHER), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )
    explicit = subprocess.run(
        [str(LAUNCHER), "model", "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert explicit.returncode == legacy.returncode == 0
    assert explicit.stdout == legacy.stdout
    assert explicit.stderr == legacy.stderr
    assert "pa native" in legacy.stdout
    assert "pa model" in legacy.stdout


def test_native_mode_dispatches_before_every_model_gate(tmp_path: Path) -> None:
    native_root = tmp_path / "native"
    scripts = native_root / "scripts"
    scripts.mkdir(parents=True)
    runner = scripts / "peano_native_shell.py"
    runner.write_text(
        "import sys\nprint('native argv:', repr(sys.argv[1:]))\n",
        encoding="utf-8",
    )
    environment = os.environ.copy()
    environment["PEANO_NATIVE_LAB_ROOT"] = str(native_root)

    completed = subprocess.run(
        [str(LAUNCHER), "native", "--probe", "x"],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert completed.returncode == 0
    assert completed.stdout == "native argv: ['--probe', 'x']\n"
    assert "startup" not in completed.stderr.casefold()
    assert "adapter" not in completed.stderr.casefold()


def test_native_mode_rejects_old_python_without_a_traceback(tmp_path: Path) -> None:
    native_root = tmp_path / "native"
    scripts = native_root / "scripts"
    scripts.mkdir(parents=True)
    runner = scripts / "peano_native_shell.py"
    runner.write_text(
        "raise SystemExit('native runner must not execute')\n",
        encoding="utf-8",
    )

    binary_directory = tmp_path / "bin"
    binary_directory.mkdir()
    old_python = binary_directory / "python3"
    old_python.write_text(
        "#!/bin/sh\n"
        "if [ \"${1-}\" = \"-c\" ]; then exit 1; fi\n"
        "echo 'native runner must not execute' >&2\n"
        "exit 99\n",
        encoding="utf-8",
    )
    old_python.chmod(0o755)

    environment = os.environ.copy()
    environment["PEANO_NATIVE_LAB_ROOT"] = str(native_root)
    environment["PATH"] = f"{binary_directory}:/usr/bin:/bin"
    completed = subprocess.run(
        [str(LAUNCHER), "native", "--version"],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert "Python 3.10 or newer is required for native mode" in completed.stderr
    assert "Traceback" not in completed.stderr
    assert "native runner must not execute" not in completed.stderr


def test_launcher_resolves_a_user_path_symlink(tmp_path: Path) -> None:
    link = tmp_path / "pa"
    link.symlink_to(LAUNCHER)

    completed = subprocess.run(
        [str(link), "--help"],
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "Peano Lab shell" in completed.stdout


def test_startup_interrupt_is_clean_and_never_opens_a_shell(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    policy_repl = SimpleNamespace(
        _validated_results_dir=lambda path: path,
        SearchBudget=lambda **kwargs: SimpleNamespace(**kwargs),
        load_model_runtime=object(),
    )
    monkeypatch.setattr(
        MODEL_LAB,
        "_load_components",
        lambda: (SimpleNamespace(), policy_repl),
    )

    def interrupted(*args, **kwargs):
        del args, kwargs
        raise KeyboardInterrupt

    monkeypatch.setattr(MODEL_LAB, "_load_runtime", interrupted)

    assert MODEL_LAB.main([]) == 130
    captured = capsys.readouterr()
    output = captured.out + captured.err
    assert "Input begins only when the `pa>` prompt appears." in output
    assert "Startup interrupted cleanly" in output
    assert "Traceback" not in output
