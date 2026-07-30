"""Deterministic whole-session selection for the model-v3 curriculum."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import random
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
for import_root in (REPOSITORY_ROOT, SCRIPTS_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import generate_peano_v3_balanced_corpus as generator  # noqa: E402
from training.peano_policy.contract import model_v1_environment  # noqa: E402
from training.peano_policy.prompt import (  # noqa: E402
    PEANO_PROMPT_V3,
    CapabilityIdentity,
    LibraryRecord,
    ProofExample,
    PromptEnvironment,
    render_prompt,
)
from training.peano_policy.selection import (  # noqa: E402
    CATALOG_LANE,
    MODEL_V3_ROOT_HEADS,
    MODEL_V3_SCHEMA_HEADS,
    MODEL_V3_SELECTION_CONTRACT,
    MODEL_V3_SYNTHETIC_ROW_CEILING,
    SELECTION_ALGORITHM,
    SELECTION_FORMAT,
    SYNTHETIC_LANE,
    CurriculumRow,
    CurriculumSelection,
    CurriculumSelectionContract,
    CurriculumSelectionError,
    canonical_selection_json,
    row_from_validated_record,
    select_curriculum,
    selection_record_sha256,
)


SMALL_CONTRACT = CurriculumSelectionContract(
    library_size=2,
    expected_catalog_rows=3,
    root_heads=("h1", "h2"),
    schema_heads=(("s1", "h1"), ("s2", "h1"), ("s3", "h2")),
)
ONE_PER_HEAD_CONTRACT = CurriculumSelectionContract(
    library_size=1,
    expected_catalog_rows=1,
    root_heads=("h1", "h2"),
    schema_heads=(("s1", "h1"), ("s2", "h2")),
)
MODEL_V1_ENVIRONMENT = model_v1_environment()
MODEL_V1_PROMPT = render_prompt(
    goals=("⊢ 0 = 0",),
    focus=0,
    environment=MODEL_V1_ENVIRONMENT,
)


def _example(session: str, step: int, tactic: str = "refl") -> ProofExample:
    return ProofExample(
        example_id=f"{session}:{step}",
        prompt=MODEL_V1_PROMPT,
        completion=f"{tactic}</tactic>",
        environment_sha256=MODEL_V1_ENVIRONMENT.sha256,
    )


def _row_digest(session: str, step: int) -> str:
    return hashlib.sha256(f"row\0{session}\0{step}".encode()).hexdigest()


def _script_digest(steps: int) -> str:
    payload = json.dumps(
        ["refl"] * steps,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _catalog_session(
    session: str,
    target: int,
    steps: int,
    *,
    library_size: int,
) -> list[CurriculumRow]:
    return [
        CurriculumRow(
            example=_example(session, step),
            session=session,
            step=step,
            expected_steps=steps,
            lane=CATALOG_LANE,
            library_size=library_size,
            row_sha256=_row_digest(session, step),
            script_sha256=_script_digest(steps),
            catalog_target_index=target,
            catalog_target_name=f"catalog_{target}",
        )
        for step in range(1, steps + 1)
    ]


def _synthetic_session(
    session: str,
    schema: str,
    head: str,
    steps: int,
    *,
    library_size: int,
) -> list[CurriculumRow]:
    return [
        CurriculumRow(
            example=_example(session, step),
            session=session,
            step=step,
            expected_steps=steps,
            lane=SYNTHETIC_LANE,
            library_size=library_size,
            row_sha256=_row_digest(session, step),
            script_sha256=_script_digest(steps),
            schema=schema,
            root_head=head,
        )
        for step in range(1, steps + 1)
    ]


def _small_population() -> list[CurriculumRow]:
    rows = [
        *_catalog_session("catalog-a", 0, 1, library_size=2),
        *_catalog_session("catalog-b", 1, 2, library_size=2),
    ]
    # Plenty of one-row alternatives make seed-dependent choices observable;
    # s1/s2 give h1 two mandatory schema anchors, so h2 must first rebalance.
    for schema, head, count in (("s1", "h1", 8), ("s2", "h1", 8), ("s3", "h2", 16)):
        for index in range(count):
            rows.extend(
                _synthetic_session(
                    f"{schema}-{index:02d}",
                    schema,
                    head,
                    1,
                    library_size=2,
                )
            )
    return rows


def _selected_sessions(rows: tuple[CurriculumRow, ...]) -> dict[str, list[int]]:
    result: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        result[row.session].append(row.step)
    return dict(result)


def test_public_contract_matches_the_registered_generator_catalog() -> None:
    generated = tuple(
        (schema.name, generator._first_head(schema))
        for schema in generator.SCHEMAS
    )

    assert MODEL_V3_SCHEMA_HEADS == generated
    assert len(MODEL_V3_SCHEMA_HEADS) == 51
    assert MODEL_V3_ROOT_HEADS == generator.ROOT_HEADS
    assert len(MODEL_V3_ROOT_HEADS) == 14
    assert MODEL_V3_SELECTION_CONTRACT.library_size == 247
    assert MODEL_V3_SELECTION_CONTRACT.expected_catalog_rows == 8_494
    assert MODEL_V3_SYNTHETIC_ROW_CEILING == 12_288


def test_selection_is_order_independent_complete_balanced_and_catalog_forcing() -> None:
    population = _small_population()
    first = select_curriculum(
        population,
        seed="selection-seed",
        synthetic_row_ceiling=10,
        contract=SMALL_CONTRACT,
    )
    shuffled = list(population)
    random.Random(77).shuffle(shuffled)
    second = select_curriculum(
        shuffled,
        seed="selection-seed",
        synthetic_row_ceiling=10,
        contract=SMALL_CONTRACT,
    )

    assert first.rows == second.rows
    assert first.record == second.record
    assert first.sha256 == second.sha256
    assert {row.example.example_id for row in first.rows if row.lane == CATALOG_LANE} == {
        "catalog-a:1",
        "catalog-b:1",
        "catalog-b:2",
    }
    sessions = _selected_sessions(first.rows)
    for session, steps in sessions.items():
        expected = next(
            row.expected_steps for row in first.rows if row.session == session
        )
        assert steps == list(range(1, expected + 1))

    synthetic = first.record["selected"]["synthetic"]
    assert synthetic["rows"] <= synthetic["row_ceiling"] == 10
    assert synthetic["schema_count"] == 3
    assert set(synthetic["schemas"]) == {"s1", "s2", "s3"}
    assert all(record["sessions"] >= 1 for record in synthetic["schemas"].values())
    assert synthetic["root_head_session_imbalance"] == 0
    assert {
        head: record["sessions"]
        for head, record in synthetic["root_heads"].items()
    } == {"h1": 5, "h2": 5}
    assert first.record["selected"]["catalog"] == {
        "rows": 3,
        "sessions": 2,
        "target_count": 2,
        "target_index_range": [0, 1],
        "target_names_sha256": first.record["selected"]["catalog"][
            "target_names_sha256"
        ],
    }


def test_seed_changes_membership_but_not_contract_counts() -> None:
    population = _small_population()
    first = select_curriculum(
        population,
        seed="seed-a",
        synthetic_row_ceiling=8,
        contract=SMALL_CONTRACT,
    )
    second = select_curriculum(
        population,
        seed="seed-b",
        synthetic_row_ceiling=8,
        contract=SMALL_CONTRACT,
    )

    first_ids = {row.example.example_id for row in first.rows}
    second_ids = {row.example.example_id for row in second.rows}
    assert first_ids != second_ids
    assert first.record["selected"]["rows"] == second.record["selected"]["rows"]
    assert first.sha256 != second.sha256


def test_whole_balanced_round_stops_below_ceiling_without_partial_session() -> None:
    population = [
        *_catalog_session("catalog", 0, 1, library_size=1),
        *_synthetic_session("s1-anchor", "s1", "h1", 2, library_size=1),
        *_synthetic_session("s2-anchor", "s2", "h2", 2, library_size=1),
        *_synthetic_session("s1-next", "s1", "h1", 2, library_size=1),
        *_synthetic_session("s2-next", "s2", "h2", 2, library_size=1),
    ]
    result = select_curriculum(
        population,
        seed="whole-sessions",
        synthetic_row_ceiling=5,
        contract=ONE_PER_HEAD_CONTRACT,
    )

    synthetic = result.record["selected"]["synthetic"]
    assert synthetic["rows"] == 4
    assert synthetic["unused_row_capacity"] == 1
    assert synthetic["balanced_fill_rounds"] == 0
    assert {row.session for row in result.rows if row.lane == SYNTHETIC_LANE} in (
        {"s1-anchor", "s2-anchor"},
        {"s1-anchor", "s2-next"},
        {"s1-next", "s2-anchor"},
        {"s1-next", "s2-next"},
    )
    for steps in _selected_sessions(result.rows).values():
        assert steps in ([1], [1, 2])


def test_selector_fails_closed_on_incomplete_or_uncovered_populations() -> None:
    complete = _small_population()
    missing_schema = [row for row in complete if row.schema != "s3"]
    with pytest.raises(CurriculumSelectionError, match="lacks reviewed strata"):
        select_curriculum(
            missing_schema,
            seed="x",
            synthetic_row_ceiling=10,
            contract=SMALL_CONTRACT,
        )

    incomplete = [
        row
        for row in complete
        if not (row.session == "catalog-b" and row.step == 2)
    ]
    with pytest.raises(CurriculumSelectionError, match="complete step sequence"):
        select_curriculum(
            incomplete,
            seed="x",
            synthetic_row_ceiling=10,
            contract=SMALL_CONTRACT,
        )

    missing_target = [row for row in complete if row.session != "catalog-b"]
    with pytest.raises(CurriculumSelectionError, match="coverage is not exact"):
        select_curriculum(
            missing_target,
            seed="x",
            synthetic_row_ceiling=10,
            contract=SMALL_CONTRACT,
        )


def test_selector_rejects_cross_row_script_drift_within_a_session() -> None:
    population = _small_population()
    drifted = []
    for row in population:
        if row.session == "catalog-b" and row.step == 2:
            row = replace(row, script_sha256="f" * 64)
        drifted.append(row)

    with pytest.raises(CurriculumSelectionError, match="changes its curriculum metadata"):
        select_curriculum(
            drifted,
            seed="script-drift",
            synthetic_row_ceiling=10,
            contract=SMALL_CONTRACT,
        )


def test_selector_rejects_a_ceiling_below_schema_anchor_and_head_balance_cost() -> None:
    population = [
        *_catalog_session("catalog", 0, 1, library_size=1),
        *_synthetic_session("s1", "s1", "h1", 2, library_size=1),
        *_synthetic_session("s2", "s2", "h2", 2, library_size=1),
    ]
    with pytest.raises(CurriculumSelectionError, match="cannot fit the mandatory"):
        select_curriculum(
            population,
            seed="too-small",
            synthetic_row_ceiling=3,
            contract=ONE_PER_HEAD_CONTRACT,
        )


def test_validated_record_adapter_binds_exact_row_and_rejects_lane_ambiguity() -> None:
    library = (LibraryRecord("tiny_lemma", "0 = 0"),)
    environment = PromptEnvironment(
        False,
        CapabilityIdentity("model-v3", ("refl",), ("tiny_lemma",)),
        prompt_version=PEANO_PROMPT_V3,
        library=library,
        library_identity_sha256="1" * 64,
        library_prefix_length=1,
        library_full_length=1,
        library_full_identity_sha256="2" * 64,
    )
    prompt = render_prompt(
        goals=("⊢ 0 = 0",), focus=0, environment=environment
    )
    example = ProofExample(
        example_id="synthetic-record:1",
        prompt=prompt,
        completion="refl</tactic>",
        environment_sha256=environment.sha256,
    )
    record = {
        "surface": "model-v3",
        "split": "train",
        "session": "synthetic-record",
        "step": 1,
        "prompt": prompt,
        "completion": "refl</tactic>",
        "environment_sha256": environment.sha256,
        "metadata": {
            "library_size": 1,
            "library_prefix_length": 1,
            "lane": SYNTHETIC_LANE,
            "template": "root-equality-refl",
            "root_first_tactic_head": "refl",
            "tactic_rows": 1,
            "tactics": ["refl"],
        },
    }

    row = row_from_validated_record(example, record)
    reordered = dict(reversed(tuple(record.items())))
    assert row == row_from_validated_record(example, reordered)
    assert row.schema == "root-equality-refl"
    assert row.root_head == "refl"
    assert row.lane == SYNTHETIC_LANE

    ambiguous = json.loads(json.dumps(record))
    ambiguous["metadata"]["trajectory"] = CATALOG_LANE
    with pytest.raises(CurriculumSelectionError, match="exactly one"):
        row_from_validated_record(example, ambiguous)

    mixed_marker = json.loads(json.dumps(record))
    mixed_marker["metadata"]["trajectory"] = "forged-trajectory"
    with pytest.raises(CurriculumSelectionError, match="mixes catalog and synthetic"):
        row_from_validated_record(example, mixed_marker)

    boolean_count = json.loads(json.dumps(record))
    boolean_count["metadata"]["tactic_rows"] = True
    with pytest.raises(CurriculumSelectionError, match="tactic count"):
        row_from_validated_record(example, boolean_count)

    wrong_completion = json.loads(json.dumps(record))
    wrong_completion["metadata"]["tactics"] = ["symm"]
    with pytest.raises(CurriculumSelectionError, match="completion differs"):
        row_from_validated_record(example, wrong_completion)


def test_selection_record_is_canonical_self_bound_json() -> None:
    result = select_curriculum(
        _small_population(),
        seed="record",
        synthetic_row_ceiling=8,
        contract=SMALL_CONTRACT,
    )
    rendered = canonical_selection_json(result.record)

    assert rendered.endswith("\n") and not rendered.endswith("\n\n")
    assert json.loads(rendered) == result.record
    assert result.record["format"] == SELECTION_FORMAT
    assert result.record["algorithm"] == SELECTION_ALGORITHM
    assert selection_record_sha256(result.record) == result.sha256

    forged = json.loads(rendered)
    forged["selected"]["rows"] += 1
    assert selection_record_sha256(forged) != forged["selection_sha256"]
    with pytest.raises(CurriculumSelectionError, match="digest mismatch"):
        canonical_selection_json(forged)

    detached = result.record
    detached["selected"]["rows"] += 1
    assert result.record["selected"]["rows"] != detached["selected"]["rows"]
    assert canonical_selection_json(result.record) == rendered

    with pytest.raises(CurriculumSelectionError, match="attested identity"):
        CurriculumSelection(
            rows=result.rows[:-1],
            record_json=result.record_json,
        )

    structurally_empty = {"selection_sha256": "0" * 64}
    structurally_empty["selection_sha256"] = selection_record_sha256(
        structurally_empty
    )
    with pytest.raises(CurriculumSelectionError, match="record identity"):
        CurriculumSelection(
            rows=result.rows,
            record_json=canonical_selection_json(structurally_empty),
        )
