"""Model-free tests for the persistent, kernel-checked policy REPL."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
PEANO_PYTHON = REPOSITORY_ROOT / "peano-lab" / "py"
for import_root in (REPOSITORY_ROOT, PEANO_PYTHON):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))
SCRIPT = REPOSITORY_ROOT / "scripts" / "peano_policy_repl.py"
WMI_LAUNCHER = REPOSITORY_ROOT / "scripts" / "wmi_peano_policy_repl.sh"
SPEC = importlib.util.spec_from_file_location("_peano_policy_repl", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
REPL = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = REPL
SPEC.loader.exec_module(REPL)

from peano_lab.batch import verify_proof  # noqa: E402
from peano_lab.ui.prove import SurfaceCapabilities  # noqa: E402
from training.peano_policy.search import SearchLimits, search  # noqa: E402


@dataclass
class FakeCapabilities:
    label: str = "model-v2"
    allowed_commands: frozenset[str] = frozenset({"intro", "refl"})
    allowed_theorems: frozenset[str] = frozenset({"zero_add"})


@dataclass
class FakeSearchResult:
    status: str
    theorem: str
    commands: tuple[str, ...]
    certificate_nodes: int | None

    @property
    def proved(self) -> bool:
        return self.status == "proof"

    def to_dict(self) -> dict[str, object]:
        return {
            "status": self.status,
            "theorem": self.theorem,
            "commands": list(self.commands),
            "certificate_nodes": self.certificate_nodes,
            "diagnostics": [],
            "model_calls": 2,
            "states_expanded": 2,
            "states_discovered": 2,
            "candidates_executed": 3,
            "frontier_peak": 1,
            "depth_reached": len(self.commands),
        }


@dataclass
class FakeReplay:
    theorem: str
    proof_nodes: int
    status: str = "proved"
    kernel_checked: bool = True
    tactics_applied: int = 2
    failed_tactics: int = 0
    surface: str = "model-v2"
    classical: bool = False

    def to_dict(self, *, include_trace: bool = True) -> dict[str, object]:
        del include_trace
        return {
            "status": self.status,
            "kernel_checked": self.kernel_checked,
            "theorem": self.theorem,
            "proof_nodes": self.proof_nodes,
            "tactics_applied": self.tactics_applied,
            "failed_tactics": self.failed_tactics,
            "surface": self.surface,
            "classical": self.classical,
        }


class FakeLimits:
    def __init__(self, **values: int) -> None:
        self.values = values


def _runtime(search, verify) -> object:
    return REPL.ReplRuntime(
        policy=object(),
        capabilities=FakeCapabilities(),
        classical=False,
        adapter_identity={"adapter_sha256": "a" * 64},
        search=search,
        verify=verify,
        make_limits=FakeLimits,
    )


def test_import_and_help_do_not_import_gpu_packages() -> None:
    code = "\n".join(
        (
            "import importlib.util, pathlib, sys",
            f"p = pathlib.Path({str(SCRIPT)!r})",
            "s = importlib.util.spec_from_file_location('_isolated_repl', p)",
            "m = importlib.util.module_from_spec(s)",
            "sys.modules[s.name] = m",
            "s.loader.exec_module(m)",
            "assert 'torch' not in sys.modules",
            "assert 'transformers' not in sys.modules",
            "assert 'peft' not in sys.modules",
            "m._parser().parse_args(['--help'])",
        )
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-c", code],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0
    assert "--candidates" in completed.stdout
    assert "--diagnostic" in completed.stdout
    assert "--device {auto,cpu,mps,cuda}" in completed.stdout


def test_model_command_prefix_normalizes_to_the_closed_theorem() -> None:
    assert REPL.normalize_theorem_input("pa prove-model forall n. n = n") == (
        "forall n. n = n"
    )
    assert REPL.normalize_theorem_input("pa prove 0 = 0") == "0 = 0"
    assert REPL.normalize_theorem_input("0 = 0") == "0 = 0"


def test_runtime_loader_propagates_explicit_diagnostic_and_mac_placement(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    import training.peano_policy.contract as contract
    import training.peano_policy.generate as generation

    adapter = tmp_path / "adapter"
    adapter.mkdir()
    received: dict[str, object] = {}
    placement = SimpleNamespace(
        to_record=lambda: {"device": "mps", "dtype": "bfloat16"}
    )
    model = SimpleNamespace(
        peano_runtime_placement=placement,
        device="mps:0",
        dtype="torch.bfloat16",
    )
    environment = SimpleNamespace(
        capabilities=SimpleNamespace(
            label="model-v3",
            allowed_commands=("refl",),
            allowed_theorems=(),
        )
    )

    def load(path, **kwargs):
        received.update(path=path, **kwargs)
        return model, object(), {"manifest": "test"}

    class FakeBasePolicy:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

    class FakeCandidatePolicy:
        evaluation_identity = {"kind": "test"}

        def __init__(self, base, *, seed):
            self.base = base
            self.seed = seed

    monkeypatch.setattr(generation, "load_adapter", load)
    monkeypatch.setattr(generation, "adapter_provenance", lambda *args: {})
    monkeypatch.setattr(generation, "PeanoPolicyAdapter", FakeBasePolicy)
    monkeypatch.setattr(
        generation, "PeanoPolicyCandidateAdapter", FakeCandidatePolicy
    )
    monkeypatch.setattr(
        contract, "attested_training_environment", lambda manifest: environment
    )

    runtime = REPL.load_model_runtime(
        adapter,
        seed=17,
        max_new_tokens=48,
        sample=False,
        temperature=0.8,
        top_p=0.95,
        diagnostic_mode=True,
        device="mps",
        dtype="bfloat16",
        local_files_only=True,
        cache_dir=tmp_path / "cache",
    )

    assert received == {
        "path": adapter.resolve(),
        "seed": 17,
        "diagnostic_mode": True,
        "device": "mps",
        "dtype": "bfloat16",
        "local_files_only": True,
        "cache_dir": tmp_path / "cache",
    }
    assert runtime.runtime_identity is not None
    assert runtime.runtime_identity["device"] == "mps"
    assert runtime.runtime_identity["dtype"] == "bfloat16"
    software = runtime.runtime_identity["software"]
    assert software["python"]
    assert software["machine"]
    assert set(software["packages"]) == {
        "accelerate",
        "peft",
        "safetensors",
        "tokenizers",
        "torch",
        "transformers",
    }


def test_wmi_launcher_is_fixed_dry_by_default_and_requires_confirmation() -> None:
    subprocess.run(["bash", "-n", str(WMI_LAUNCHER)], check=True)
    dry = subprocess.run(
        ["bash", str(WMI_LAUNCHER)],
        text=True,
        capture_output=True,
        check=True,
    )
    assert "dry run (no SSH, no allocation)" in dry.stdout
    assert "gpu=nvidia_a100:1" in dry.stdout
    assert "constraint=vram80g" in dry.stdout

    refused = subprocess.run(
        ["bash", str(WMI_LAUNCHER), "--connect"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert refused.returncode == 2
    assert "--connect --confirm PEANO-LAB-WMI-TRAINING" in refused.stderr

    remote_bypass = subprocess.run(
        ["bash", str(WMI_LAUNCHER), "--remote-run"],
        text=True,
        capture_output=True,
        check=False,
    )
    assert remote_bypass.returncode == 2
    assert "reserved for the fixed SSH hop" in remote_bypass.stderr


def test_wmi_launcher_requests_one_typed_a100_and_fixed_loaded_repl() -> None:
    source = WMI_LAUNCHER.read_text(encoding="utf-8")
    assert source.count("exec srun \\") == 1
    assert "--partition=gpu_csi" in source
    assert "--nodes=1" in source
    assert "--ntasks=1" in source
    assert "--gpus=nvidia_a100:1" in source
    assert "--constraint=vram80g" in source
    assert "--time=04:00:00" in source
    assert "--pty" in source
    assert 'active="$(squeue -h --me --name "$repl_job_name"' in source
    assert "flock -s 8" in source
    assert "peano_wmi_current_python" in source
    assert "peano_wmi_assert_runtime" in source
    assert "HF_HUB_OFFLINE=1" in source
    assert "TRANSFORMERS_OFFLINE=1" in source
    assert "scripts/peano_policy_repl.py" in source
    assert "qwen3-1.7b-lora-v3-library" in source
    assert 'exec ssh -tt -o BatchMode=yes' in source
    assert "eval " not in source
    assert '"$@"' not in source


def test_wmi_launcher_rejects_host_option_injection_even_in_dry_run() -> None:
    environment = os.environ.copy()
    environment["WMI_SSH_TARGET"] = "-oProxyCommand=hostile"
    rejected = subprocess.run(
        ["bash", str(WMI_LAUNCHER), "--test-only"],
        text=True,
        capture_output=True,
        check=False,
        env=environment,
    )
    assert rejected.returncode == 2
    assert "invalid WMI_SSH_TARGET" in rejected.stderr


def test_checked_search_replays_original_theorem_before_building_script() -> None:
    searched: list[object] = []
    verified: list[object] = []

    def search(theorem, policy, **kwargs):
        searched.append((theorem, policy, kwargs))
        return FakeSearchResult(
            "proof",
            "∀ n. n = n",
            ("intro n", "refl"),
            3,
        )

    def verify(theorem, commands, **kwargs):
        verified.append((theorem, commands, kwargs))
        return FakeReplay("∀ n. n = n", 3)

    attempt = REPL.run_checked_search(
        "forall n. n = n",
        _runtime(search, verify),
        REPL.SearchBudget(max_depth=8),
        created_at="2026-07-28T12:00:00Z",
    )

    assert attempt.proved
    assert attempt.proof_script == (
        "pa prove ∀ n. n = n\nintro n\nrefl\nqed\n"
    )
    assert verified[0][0] == "forall n. n = n"
    assert verified[0][1] == ("intro n", "refl")
    assert attempt.report["publication"]["status"] == "kernel-checked-proof"
    assert searched[0][2]["limits"].values["max_depth"] == 8


def test_live_events_distinguish_search_certificate_from_independent_replay() -> None:
    events: list[dict[str, object]] = []
    result = FakeSearchResult(
        "proof", "∀ n. n = n", ("intro n", "refl"), 3
    )

    attempt = REPL.run_checked_search(
        "forall n. n = n",
        _runtime(
            lambda *args, **kwargs: result,
            lambda *args, **kwargs: FakeReplay("∀ n. n = n", 3),
        ),
        REPL.SearchBudget(),
        created_at="2026-07-28T12:00:00Z",
        on_event=lambda event: events.append(dict(event)),
    )

    assert attempt.proved
    assert [event["kind"] for event in events] == [
        "independent_replay_started",
        "independent_replay_finished",
    ]
    assert events[-1] == {
        "v": 1,
        "kind": "independent_replay_finished",
        "status": "accepted",
        "kernel_checked": True,
        "proof_nodes": 3,
        "message": None,
    }


def test_each_theorem_gets_fresh_policy_counters_without_reloading_weights() -> None:
    policies: list[object] = []

    class FreshPolicy:
        def __init__(self, generation: int) -> None:
            self.generation = generation
            self.generation_provenance = {"model_generate_calls": generation}

        def fresh(self):
            return FreshPolicy(0)

    def search(theorem, policy, **kwargs):
        del theorem, kwargs
        policies.append(policy)
        policy.generation = 1
        policy.generation_provenance = {"model_generate_calls": 1}
        return FakeSearchResult("limit", "0 = 0", (), None)

    runtime = REPL.ReplRuntime(
        policy=FreshPolicy(99),
        capabilities=FakeCapabilities(),
        classical=False,
        adapter_identity={"adapter_sha256": "a" * 64},
        search=search,
        verify=lambda *args, **kwargs: None,
        make_limits=FakeLimits,
    )
    first = REPL.run_checked_search("0 = 0", runtime, REPL.SearchBudget())
    second = REPL.run_checked_search("0 = 0", runtime, REPL.SearchBudget())

    assert policies[0] is not policies[1]
    assert runtime.policy.generation == 99
    assert first.report["generation"] == {"model_generate_calls": 1}
    assert second.report["generation"] == {"model_generate_calls": 1}


def test_real_search_and_independent_kernel_replay_integrate_without_a_model() -> None:
    class ReflPolicy:
        generation_provenance = {
            "model_generate_calls": 1,
            "candidate_sequences_requested": 1,
            "candidate_sequences_returned": 1,
        }

        def propose(self, goals_before, *, max_candidates):
            assert goals_before == ("⊢ 0 = 0",)
            assert max_candidates == 1
            return ("refl",)

    capabilities = SurfaceCapabilities(
        label="model-v2",
        allowed_commands=frozenset({"refl"}),
        allowed_theorems=frozenset(),
    )
    runtime = REPL.ReplRuntime(
        policy=ReflPolicy(),
        capabilities=capabilities,
        classical=False,
        adapter_identity={"adapter_sha256": "d" * 64},
        search=search,
        verify=verify_proof,
        make_limits=SearchLimits,
    )
    attempt = REPL.run_checked_search(
        "0 = 0",
        runtime,
        REPL.SearchBudget(
            max_depth=1,
            beam_width=1,
            candidates_per_state=1,
            max_model_calls=1,
            max_states=1,
        ),
        created_at="2026-07-28T12:00:00Z",
    )

    assert attempt.proved
    assert attempt.proof_script == "pa prove 0 = 0\nrefl\nqed\n"
    assert attempt.report["kernel_verification"]["kernel_checked"] is True
    assert attempt.report["generation"]["model_generate_calls"] == 1


@pytest.mark.parametrize(
    "mutation",
    (
        {"kernel_checked": False},
        {"status": "open"},
        {"proof_nodes": 4},
        {"theorem": "0 = 0"},
        {"surface": "full"},
    ),
)
def test_mutated_independent_replay_can_never_publish_success(
    mutation: dict[str, object],
) -> None:
    result = FakeSearchResult(
        "proof", "∀ n. n = n", ("intro n", "refl"), 3
    )

    def verify(theorem, commands, **kwargs):
        del theorem, commands, kwargs
        replay = FakeReplay("∀ n. n = n", 3)
        for name, value in mutation.items():
            setattr(replay, name, value)
        return replay

    with pytest.raises(RuntimeError, match="refusing to publish"):
        REPL.run_checked_search(
            "forall n. n = n",
            _runtime(lambda *args, **kwargs: result, verify),
            REPL.SearchBudget(),
        )


def test_no_proof_has_no_script_and_does_not_invoke_verifier() -> None:
    result = FakeSearchResult("limit", "0 = 0", (), None)

    def forbidden(*args, **kwargs):
        raise AssertionError("an unsuccessful search must not invoke verification")

    attempt = REPL.run_checked_search(
        "0 = 0",
        _runtime(lambda *args, **kwargs: result, forbidden),
        REPL.SearchBudget(),
        created_at="2026-07-28T12:00:00Z",
    )
    assert not attempt.proved
    assert attempt.proof_script is None
    assert attempt.report["kernel_verification"] is None
    assert attempt.report["publication"] == {
        "status": "no-checked-proof",
        "script_sha256": None,
    }


def test_save_is_below_results_and_never_replaces_artifacts(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(REPL, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(REPL, "RESULTS_ROOT", tmp_path / "results")
    attempt = REPL.CheckedAttempt(
        {
            "request": {"canonical_theorem": "0 = 0"},
            "publication": {
                "status": "kernel-checked-proof",
                "script_sha256": "b" * 64,
            },
        },
        "pa prove 0 = 0\nrefl\nqed\n",
    )
    directory = tmp_path / "results" / "peano-policy" / "interactive"
    saved = REPL.save_attempt(attempt, directory, stem="fixed")

    assert saved.proof is not None
    assert saved.proof.read_text(encoding="utf-8") == attempt.proof_script
    report = json.loads(saved.report.read_text(encoding="utf-8"))
    assert report["artifacts"] == {
        "proof": "fixed.pa",
        "report": "fixed.json",
    }
    with pytest.raises(FileExistsError, match="refusing to replace"):
        REPL.save_attempt(attempt, directory, stem="fixed")
    with pytest.raises(ValueError, match="below"):
        REPL.save_attempt(attempt, tmp_path / "elsewhere", stem="escape")


def test_terminal_loop_supports_help_formula_and_quit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    lines = iter((":help", "pa prove 0 = 0", ":quit"))
    output: list[str] = []
    attempt = REPL.CheckedAttempt(
        {
            "publication": {
                "status": "kernel-checked-proof",
                "script_sha256": "c" * 64,
            }
        },
        "pa prove 0 = 0\nrefl\nqed\n",
    )
    monkeypatch.setattr(
        REPL,
        "run_checked_search",
        lambda theorem, runtime, budget: attempt,
    )

    def save(value, directory):
        assert value is attempt
        return REPL.SavedArtifacts(
            directory / "answer.json",
            directory / "answer.pa",
        )

    status = REPL.run_repl(
        _runtime(None, None),
        REPL.SearchBudget(),
        tmp_path,
        read=lambda prompt: next(lines),
        write=output.append,
        save=save,
    )
    assert status == 0
    rendered = "\n".join(output)
    assert "Enter one closed" in rendered
    assert "KERNEL CHECKED PROOF" in rendered
    assert "pa prove 0 = 0" in rendered
    assert "Session closed." in rendered
