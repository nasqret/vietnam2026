"""Portable regressions for inode-bound Hydra receipt publication.

The historical A2.3c/A2.3d tests are retained source evidence and therefore
cannot be edited.  Their attacker fixtures unlink and recreate a pathname,
which may immediately reuse the publisher inode on Linux.  These equivalents
allocate the attacker inode first, then atomically move it over the staged or
published name, making the foreign-identity condition deterministic on APFS
and ext4 alike.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import pytest


ROOT = Path(__file__).resolve().parents[3]


def _load_script(relative: str, name: str) -> ModuleType:
    path = ROOT / relative
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


A23C_SOURCE = _load_script(
    "scripts/build_peano_hydra_a23c_replayer_source_state.py",
    "_test_portable_a23c_source_state",
)
A23C_WMI = _load_script(
    "scripts/run_peano_hydra_a23c_negative_replay_wmi.py",
    "_test_portable_a23c_wmi",
)
A23D_SOURCE = _load_script(
    "scripts/build_peano_hydra_a23d_cut_liveness_source_state.py",
    "_test_portable_a23d_source_state",
)
A23D_WMI = _load_script(
    "scripts/run_peano_hydra_a23d_cut_liveness_wmi.py",
    "_test_portable_a23d_wmi",
)
A23C_CLI = _load_script(
    "scripts/verify_peano_hydra_library_pilot_dependency_vector_negative_replay.py",
    "_test_portable_a23c_negative_replay_cli",
)


def _exercise_staged_swap(
    *,
    module: ModuleType,
    destination: Path,
    publish,
    error_type: type[Exception],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    attacker_bytes = b"foreign-preallocated-inode\n"
    staged_paths: list[Path] = []
    real_link = module.os.link

    def swapped_link(source, target, *, follow_symlinks):
        staged = Path(source)
        staged_paths.append(staged)
        attacker = staged.with_name(f"{staged.name}.attacker")
        attacker.write_bytes(attacker_bytes)
        staged.unlink()
        attacker.replace(staged)
        real_link(staged, target, follow_symlinks=follow_symlinks)

    monkeypatch.setattr(module.os, "link", swapped_link)
    with pytest.raises(error_type, match="identity"):
        publish(destination)

    assert len(staged_paths) == 1
    assert destination.read_bytes() == attacker_bytes
    assert staged_paths[0].read_bytes() == attacker_bytes


def test_a23c_source_state_stage_swap_preserves_preallocated_attacker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _exercise_staged_swap(
        module=A23C_SOURCE,
        destination=tmp_path / "source-state.json",
        publish=lambda path: A23C_SOURCE._publish_one(path, b"authenticated\n"),
        error_type=A23C_SOURCE.ReplayerSourceStateError,
        monkeypatch=monkeypatch,
    )


def test_a23c_wmi_stage_swap_preserves_preallocated_attacker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = A23C_WMI._receipt_with_root(
        {"format": "fixture-receipt", "status": "unknown", "v": 1}
    )
    _exercise_staged_swap(
        module=A23C_WMI,
        destination=tmp_path / "receipt.json",
        publish=lambda path: A23C_WMI._publish_create_only(path, value),
        error_type=A23C_WMI.A23CWMIError,
        monkeypatch=monkeypatch,
    )


def test_a23d_source_state_stage_swap_preserves_preallocated_attacker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _exercise_staged_swap(
        module=A23D_SOURCE,
        destination=tmp_path / "source-state.json",
        publish=lambda path: A23D_SOURCE._publish_one(path, b"authenticated\n"),
        error_type=A23D_SOURCE.CutLivenessSourceStateError,
        monkeypatch=monkeypatch,
    )


def test_a23d_wmi_stage_swap_preserves_preallocated_attacker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    value = A23D_WMI._receipt_with_root(
        {"format": "fixture-receipt", "status": "unknown", "v": 1}
    )
    _exercise_staged_swap(
        module=A23D_WMI,
        destination=tmp_path / "receipt.json",
        publish=lambda path: A23D_WMI._publish_create_only(path, value),
        error_type=A23D_WMI.A23DWMIError,
        monkeypatch=monkeypatch,
    )


def test_a23c_post_link_failure_preserves_preallocated_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    destination = tmp_path / "result.json"
    attacker = tmp_path / "attacker.json"
    attacker_bytes = b"foreign-preallocated-inode\n"
    attacker.write_bytes(attacker_bytes)
    original_open = A23C_CLI.os.open

    def fail_directory_open(path: object, flags: int, *args: object) -> int:
        if Path(path) == tmp_path:
            attacker.replace(destination)
            raise OSError("synthetic directory-open failure")
        return original_open(path, flags, *args)

    monkeypatch.setattr(A23C_CLI.os, "open", fail_directory_open)
    with pytest.raises(
        A23C_CLI.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="cannot publish",
    ):
        A23C_CLI._publish_create_only(destination, b"candidate\n")

    assert destination.read_bytes() == attacker_bytes
    assert not list(tmp_path.glob(".a23c-negative-replay-*.tmp"))
