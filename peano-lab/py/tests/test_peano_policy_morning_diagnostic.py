from __future__ import annotations

import json
from pathlib import Path

import training.peano_policy.morning_diagnostic as diagnostic


def _write_rows(path: Path, rows: list[dict[str, object]]) -> None:
    path.write_text(
        "".join(json.dumps(row, separators=(",", ":")) + "\n" for row in rows),
        encoding="utf-8",
    )


def test_catalog_selection_keeps_boundaries_and_one_step_once(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(diagnostic, "EXPECTED_CATALOG_SESSIONS", 2)
    path = tmp_path / "train.jsonl"
    rows = [
        {
            "session": "a",
            "step": step,
            "metadata": {"trajectory": diagnostic.CATALOG_TRAJECTORY},
        }
        for step in (2, 1, 3)
    ]
    rows.extend(
        [
            {
                "session": "b",
                "step": 1,
                "metadata": {"trajectory": diagnostic.CATALOG_TRAJECTORY},
            },
            {
                "session": "synthetic",
                "step": 1,
                "metadata": {"trajectory": "synthetic-root-balanced"},
            },
        ]
    )
    _write_rows(path, rows)

    selected = diagnostic._catalog_boundary_records(path)

    identities = [(row["session"], row["step"]) for _, row in selected]
    assert identities == [("a", 1), ("a", 3), ("b", 1)]


def test_hash_sample_excludes_catalog_and_is_order_independent(tmp_path: Path) -> None:
    path = tmp_path / "train.jsonl"
    rows = [
        {
            "session": f"s{index}",
            "step": index + 1,
            "metadata": {
                "trajectory": (
                    diagnostic.CATALOG_TRAJECTORY
                    if index == 0
                    else "synthetic-root-balanced"
                )
            },
        }
        for index in range(8)
    ]
    _write_rows(path, rows)

    selected = diagnostic._hash_sample_records(
        path,
        count=3,
        seed=17,
        exclude_catalog=True,
    )

    assert len(selected) == 3
    assert all(
        row["metadata"]["trajectory"] != diagnostic.CATALOG_TRAJECTORY
        for _, row in selected
    )
    assert len({row["session"] for _, row in selected}) == 3
