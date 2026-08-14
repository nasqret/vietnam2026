import json
from pathlib import Path

import pytest

from ci_shard import (
    DEFAULT_RUNTIME_PROFILE,
    RUNTIME_PROFILE_FORMAT,
    RuntimeProfile,
    RuntimeProfileError,
    discover_test_files,
    load_runtime_profile,
    main,
    partition_test_files,
)


def _sized_file(root: Path, name: str, size: int) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)
    return path


def _profile_payload(
    weights: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    return {
        "format": RUNTIME_PROFILE_FORMAT,
        "version": 1,
        "unit": "ms",
        "fallback": 5000,
        "weights": [] if weights is None else weights,
    }


def _write_profile(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_discovery_is_recursive_filtered_and_sorted(tmp_path: Path) -> None:
    nested = tmp_path / "nested"
    nested.mkdir()
    expected = (
        _sized_file(tmp_path, "test_a.py", 1),
        _sized_file(tmp_path, "suffix_test.py", 1),
        _sized_file(nested, "test_b.py", 1),
        _sized_file(nested, "test_double_test.py", 1),
    )
    _sized_file(tmp_path, "helper.py", 1)

    assert discover_test_files(tmp_path) == tuple(sorted(expected))


def test_partition_without_profile_preserves_source_byte_balancing(
    tmp_path: Path,
) -> None:
    files = tuple(
        _sized_file(tmp_path, f"test_{index}.py", size)
        for index, size in enumerate((101, 89, 61, 43, 31, 23, 17, 11, 7))
    )

    first = partition_test_files(files, 3)
    second = partition_test_files(tuple(reversed(files)), 3)

    assert first == second
    assert set().union(*(set(shard) for shard in first)) == set(files)
    assert sum(len(shard) for shard in first) == len(files)
    loads = [sum(path.stat().st_size for path in shard) for shard in first]
    assert max(loads) - min(loads) <= max(path.stat().st_size for path in files)


def test_runtime_partition_is_deterministic_lpt_with_fallback(tmp_path: Path) -> None:
    files = tuple(
        _sized_file(tmp_path, f"test_{letter}.py", 1)
        for letter in ("a", "b", "c", "d", "e", "f")
    )
    profile = RuntimeProfile(
        weights_ms={files[0]: 100, files[1]: 90, files[2]: 80},
        fallback_ms=10,
    )

    first = partition_test_files(files, 2, profile)
    second = partition_test_files(tuple(reversed(files)), 2, profile)

    assert first == second
    assert first == (
        (files[0], files[3], files[4], files[5]),
        (files[1], files[2]),
    )
    assert [sum(profile.weight_ms(path) for path in shard) for shard in first] == [
        130,
        170,
    ]


@pytest.mark.parametrize("shard_count", (0, -1))
def test_partition_rejects_nonpositive_shard_count(
    tmp_path: Path, shard_count: int
) -> None:
    with pytest.raises(ValueError, match="positive"):
        partition_test_files((_sized_file(tmp_path, "test_a.py", 1),), shard_count)


def test_load_runtime_profile_accepts_nested_paths_and_fallback(tmp_path: Path) -> None:
    files = (
        _sized_file(tmp_path, "test_a.py", 1),
        _sized_file(tmp_path, "nested/test_b.py", 1),
    )
    profile_path = _write_profile(
        tmp_path / "profile.json",
        _profile_payload(
            [
                {"path": "nested/test_b.py", "weight": 17},
                {"path": "test_a.py", "weight": 23},
            ]
        ),
    )

    profile = load_runtime_profile(profile_path, tmp_path, files)

    assert profile.fallback_ms == 5000
    assert profile.weight_ms(files[0]) == 23
    assert profile.weight_ms(files[1]) == 17
    assert profile.weight_ms(tmp_path / "test_unlisted.py") == 5000


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("format", "other", "format"),
        ("version", 2, "version"),
        ("version", 1.0, "version"),
        ("version", True, "version"),
        ("unit", "seconds", "unit"),
        ("fallback", 0, "positive"),
        ("fallback", -1, "positive"),
        ("fallback", True, "positive"),
    ),
)
def test_load_runtime_profile_rejects_invalid_header_fields(
    tmp_path: Path, field: str, value: object, message: str
) -> None:
    _sized_file(tmp_path, "test_a.py", 1)
    payload = _profile_payload()
    payload[field] = value
    profile_path = _write_profile(tmp_path / "profile.json", payload)

    with pytest.raises(RuntimeProfileError, match=message):
        load_runtime_profile(profile_path, tmp_path)


@pytest.mark.parametrize(
    "path",
    (
        "",
        "/test_a.py",
        "./test_a.py",
        "nested/../test_a.py",
        "nested//test_a.py",
        r"nested\test_a.py",
        "helper.py",
        "test_a.txt",
    ),
)
def test_load_runtime_profile_rejects_noncanonical_or_nontest_paths(
    tmp_path: Path, path: str
) -> None:
    _sized_file(tmp_path, "test_a.py", 1)
    profile_path = _write_profile(
        tmp_path / "profile.json",
        _profile_payload([{"path": path, "weight": 1}]),
    )

    with pytest.raises(RuntimeProfileError, match="path|pytest module"):
        load_runtime_profile(profile_path, tmp_path)


def test_load_runtime_profile_rejects_duplicate_and_stale_paths(tmp_path: Path) -> None:
    _sized_file(tmp_path, "test_a.py", 1)
    duplicate = _write_profile(
        tmp_path / "duplicate.json",
        _profile_payload(
            [
                {"path": "test_a.py", "weight": 1},
                {"path": "test_a.py", "weight": 2},
            ]
        ),
    )
    stale = _write_profile(
        tmp_path / "stale.json",
        _profile_payload([{"path": "test_gone.py", "weight": 1}]),
    )

    with pytest.raises(RuntimeProfileError, match="duplicate runtime-weight path"):
        load_runtime_profile(duplicate, tmp_path)
    with pytest.raises(RuntimeProfileError, match="stale runtime-weight path"):
        load_runtime_profile(stale, tmp_path)


@pytest.mark.parametrize("weight", (0, -1, True, 1.5, "1"))
def test_load_runtime_profile_rejects_nonpositive_or_noninteger_weight(
    tmp_path: Path, weight: object
) -> None:
    _sized_file(tmp_path, "test_a.py", 1)
    profile_path = _write_profile(
        tmp_path / "profile.json",
        _profile_payload([{"path": "test_a.py", "weight": weight}]),
    )

    with pytest.raises(RuntimeProfileError, match="positive integer"):
        load_runtime_profile(profile_path, tmp_path)


def test_load_runtime_profile_rejects_wrong_shapes_and_duplicate_json_keys(
    tmp_path: Path,
) -> None:
    _sized_file(tmp_path, "test_a.py", 1)
    extra = _profile_payload()
    extra["unexpected"] = 1
    wrong_entry = _profile_payload([{"path": "test_a.py"}])
    profiles = (
        (_write_profile(tmp_path / "extra.json", extra), "wrong keys"),
        (_write_profile(tmp_path / "array.json", []), "JSON object"),
        (
            _write_profile(
                tmp_path / "weights-object.json",
                {**_profile_payload(), "weights": {}},
            ),
            "JSON array",
        ),
        (_write_profile(tmp_path / "entry.json", wrong_entry), "wrong keys"),
    )
    duplicate_key = tmp_path / "duplicate-key.json"
    duplicate_key.write_text(
        '{"format":"peano-pytest-runtime-weights","format":"again",'
        '"version":1,"unit":"ms","fallback":5000,"weights":[]}',
        encoding="utf-8",
    )

    for profile_path, message in profiles:
        with pytest.raises(RuntimeProfileError, match=message):
            load_runtime_profile(profile_path, tmp_path)
    with pytest.raises(RuntimeProfileError, match="duplicate JSON key"):
        load_runtime_profile(duplicate_key, tmp_path)


def test_checked_in_profile_matches_current_test_tree() -> None:
    tests_root = Path(__file__).parent
    files = discover_test_files(tests_root)

    profile = load_runtime_profile(DEFAULT_RUNTIME_PROFILE, tests_root, files)

    assert profile.fallback_ms == 1000
    assert len(profile.weights_ms) == 111
    assert profile.weight_ms(tests_root / "test_congruence_beta_admission.py") == 274_300
    assert profile.weight_ms(tests_root / "test_peano_hydra_authoring.py") == 500
    assert profile.weight_ms(tests_root / "test_peano_hydra_assistant_repl.py") == 3_000
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_a23a_producer_source_state.py"
        )
        == 7_000
    )
    assert (
        profile.weight_ms(tests_root / "test_peano_hydra_a23a_wmi_protocol.py")
        == 1_500
    )
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_a23b_producer_source_state.py"
        )
        == 6_000
    )
    assert (
        profile.weight_ms(tests_root / "test_peano_hydra_a23b_wmi_protocol.py")
        == 1_000
    )
    assert profile.weight_ms(tests_root / "test_peano_hydra_conformance.py") == 6_000
    assert (
        profile.weight_ms(tests_root / "test_peano_hydra_library_replay_pack.py")
        == 50_000
    )
    assert profile.weight_ms(tests_root / "test_peano_hydra_library_epoch.py") == 126_000
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_library_epoch_metadata.py"
        )
        == 80_000
    )
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_library_documentation_bundle.py"
        )
        == 120_000
    )
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_library_epoch_metadata_v2.py"
        )
        == 360_000
    )
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_library_dependency_audit.py"
        )
        == 15_000
    )
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_library_construction_rebuild.py"
        )
        == 45_000
    )
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_library_optimizer_comparison_pilot.py"
        )
        == 1_500
    )
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_library_pilot_dependency_vector_audit.py"
        )
        == 3_000
    )
    assert (
        profile.weight_ms(
            tests_root
            / "test_peano_hydra_library_pilot_dependency_vector_audit_result.py"
        )
        == 3_500
    )
    assert (
        profile.weight_ms(
            tests_root
            / "test_peano_hydra_library_pilot_dependency_vector_audit_verifier.py"
        )
        == 3_500
    )
    assert (
        profile.weight_ms(
            tests_root
            / "test_peano_hydra_library_pilot_dependency_vector_cut_liveness.py"
        )
        == 20_000
    )
    assert (
        profile.weight_ms(
            tests_root
            / "test_peano_hydra_library_pilot_dependency_vector_negative_replay.py"
        )
        == 6_000
    )
    assert (
        profile.weight_ms(
            tests_root
            / "test_peano_hydra_library_pilot_dependency_vector_negative_replay_result.py"
        )
        == 3_500
    )
    assert (
        profile.weight_ms(
            tests_root
            / "test_peano_hydra_library_pilot_dependency_vector_negative_replay_verifier.py"
        )
        == 9_000
    )
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_a23c_replayer_source_state.py"
        )
        == 6_000
    )
    assert (
        profile.weight_ms(tests_root / "test_peano_hydra_a23c_wmi_protocol.py")
        == 6_000
    )
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_a23d_cut_liveness_source_state.py"
        )
        == 7_500
    )
    assert (
        profile.weight_ms(tests_root / "test_peano_hydra_a23d_wmi_protocol.py")
        == 8_000
    )
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_library_optimizer_comparison_result.py"
        )
        == 3_500
    )
    assert (
        profile.weight_ms(
            tests_root / "test_peano_hydra_library_optimizer_comparison_verifier.py"
        )
        == 2_500
    )
    assert profile.weight_ms(tests_root / "test_peano_hydra_library_pages.py") == 90_000
    assert (
        profile.weight_ms(tests_root / "test_peano_hydra_interactive_assistant.py")
        == 2_000
    )
    assert profile.weight_ms(tests_root / "test_peano_hydra_macro_runner.py") == 14_000
    assert profile.weight_ms(tests_root / "test_peano_hydra_macros.py") == 500
    assert profile.weight_ms(tests_root / "test_peano_hydra_result_schema.py") == 1_000
    assert profile.weight_ms(tests_root / "test_peano_hydra_qwen_bridge.py") == 1_000
    assert profile.weight_ms(tests_root / "test_peano_hydra_vampire_assistant.py") == 2_000
    assert profile.weight_ms(tests_root / "test_peano_hydra_vampire_adapter.py") == 2_000
    assert profile.weight_ms(tests_root / "test_peano_hydra_vampire_live.py") == 6_000
    shards = partition_test_files(files, 8, profile)
    assert [
        sum(profile.weight_ms(path) for path in shard)
        for shard in shards
    ] == [
        549_000,
        549_500,
        549_300,
        549_500,
        549_000,
        549_500,
        549_000,
        549_000,
    ]


def test_cli_reports_modeled_runtime_and_source_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    test_file = _sized_file(tmp_path, "test_a.py", 7)
    profile_path = _write_profile(
        tmp_path / "profile.json",
        _profile_payload([{"path": "test_a.py", "weight": 123}]),
    )
    received: list[list[str]] = []
    monkeypatch.setattr(pytest, "main", lambda arguments: received.append(arguments) or 0)

    result = main(
        [
            "--count",
            "1",
            "--index",
            "0",
            "--tests-root",
            str(tmp_path),
            "--runtime-profile",
            str(profile_path),
            "--",
            "-q",
        ]
    )

    assert result == 0
    assert "123 modeled ms, 7 source bytes" in capsys.readouterr().out
    assert received == [["-q", str(test_file)]]


def test_cli_can_explicitly_keep_source_byte_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    test_file = _sized_file(tmp_path, "test_a.py", 7)
    received: list[list[str]] = []
    monkeypatch.setattr(pytest, "main", lambda arguments: received.append(arguments) or 0)

    result = main(
        [
            "--count",
            "1",
            "--index",
            "0",
            "--tests-root",
            str(tmp_path),
            "--no-runtime-profile",
            "--",
            "-q",
        ]
    )

    assert result == 0
    assert "source-byte model, 7 source bytes" in capsys.readouterr().out
    assert received == [["-q", str(test_file)]]
