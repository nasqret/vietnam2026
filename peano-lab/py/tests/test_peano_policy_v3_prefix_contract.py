"""Prompt-v3 exposes only checked strict-predecessor theorem prefixes."""

from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

import pytest


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from peano_lab.library.theorems import THEOREMS
from training.peano_policy.contract import (
    MODEL_V3_LIBRARY_SIZE,
    environment_record,
    model_v3_environment,
    model_v3_prefix_environment,
    prompt_environment,
)
from training.peano_policy.data import example_from_record
from training.peano_policy.prompt import (
    PEANO_PROMPT_V2,
    PEANO_PROMPT_V3,
    V3_NAME_INVENTORY_MAX_PROMPT_CHARS,
    V3_NAME_INVENTORY_METHOD,
    V3_STATE_ENCODING_METHOD,
    V3_STATE_MAX_PROMPT_CHARS,
    CapabilityIdentity,
    LibraryRecord,
    PromptEnvironment,
    PromptError,
    encode_v3_name_inventory,
    parse_prompt,
    prompt_manifest_record,
    retrieve_theorems,
    render_prompt,
    v3_name_inventory_sha256,
)


GOAL = "⊢ 0 = 0"


def _library_payload(prompt: str) -> dict[str, object]:
    text = prompt.split("<library>", 1)[1].split("</library>", 1)[0]
    value = json.loads(text)
    assert type(value) is dict
    return value


def _replace_library_payload(
    prompt: str, payload: dict[str, object]
) -> str:
    before, rest = prompt.split("<library>", 1)
    _, after = rest.split("</library>", 1)
    text = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":")
    )
    return before + "<library>" + text + "</library>" + after


def _state_payload(prompt: str) -> dict[str, object]:
    text = prompt.split("<state>", 1)[1].split("</state>", 1)[0]
    value = json.loads(text)
    assert type(value) is dict
    return value


def _replace_state_payload(prompt: str, payload: dict[str, object]) -> str:
    before, rest = prompt.split("<state>", 1)
    _, after = rest.split("</state>", 1)
    text = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    return before + "<state>" + text + "</state>" + after


def test_every_v3_prefix_exposes_exactly_its_strict_predecessors() -> None:
    for index, target in enumerate(THEOREMS[:MODEL_V3_LIBRARY_SIZE]):
        environment = model_v3_prefix_environment(index)
        allowed = environment.capabilities.allowed_theorems
        expected_names = tuple(sorted(spec.name for spec in THEOREMS[:index]))
        assert environment.prompt_version == PEANO_PROMPT_V3
        assert environment.library_prefix_length == index
        assert allowed == expected_names
        assert target.name not in (allowed or ())
        assert set(target.dependencies) <= set(allowed or ())

        prompt = render_prompt(goals=(GOAL,), focus=0, environment=environment)
        parsed = parse_prompt(prompt)
        assert parsed.allowed_theorem_names == expected_names
        assert parsed.name_inventory_method == V3_NAME_INVENTORY_METHOD
        assert parsed.name_inventory_count == index
        inventory = encode_v3_name_inventory(expected_names)
        assert parsed.name_inventory_sha256 == v3_name_inventory_sha256(
            inventory
        )
        assert set(target.dependencies) <= set(parsed.allowed_theorem_names)
        assert target.name not in parsed.allowed_theorem_names
        assert target.name not in {
            record.name for record in parsed.retrieved_theorems
        }


@pytest.mark.parametrize("prefix", [0, 7, MODEL_V3_LIBRARY_SIZE])
def test_v3_prefix_prompts_round_trip(prefix: int) -> None:
    environment = model_v3_prefix_environment(prefix)
    prompt = render_prompt(goals=(GOAL,), focus=0, environment=environment)
    parsed = parse_prompt(prompt)
    assert parsed.prompt_version == PEANO_PROMPT_V3
    assert parsed.library_prefix_length == prefix
    assert parsed.library_size == MODEL_V3_LIBRARY_SIZE
    assert parsed.library_sha256 == environment.library_sha256
    assert parsed.library_full_sha256 == environment.library_full_identity_sha256
    assert parsed.allowed_theorem_names == tuple(
        record.name for record in environment.library
    )
    assert len(parsed.retrieved_theorems) == min(12, prefix)
    assert parsed.state_encoding == V3_STATE_ENCODING_METHOD


def test_v3_state_encoding_is_lossless_shared_and_idempotent() -> None:
    environment = model_v3_prefix_environment(7)
    goals = (
        "n : ℕ, h : n + 0 = n ⊢ n = n",
        "n : ℕ, h : n + 0 = n ⊢ n = n",
        "n : ℕ ⊢ 0 = 0",
    )
    prompt = render_prompt(goals=goals, focus=1, environment=environment)
    payload = _state_payload(prompt)
    assert payload == {
        "encoding": V3_STATE_ENCODING_METHOD,
        "focus": 1,
        "declarations": ["n : ℕ", "h : n + 0 = n"],
        "targets": ["n = n", "0 = 0"],
        "goals": [[[0, 1], 0], [[0, 1], 0], [[0], 1]],
    }
    parsed = parse_prompt(prompt)
    assert parsed.goals == goals
    assert render_prompt(
        goals=parsed.goals,
        focus=parsed.focus,
        environment=environment,
    ) == prompt


def test_v3_state_tables_reject_invalid_indices_duplicates_and_unused_entries() -> None:
    environment = model_v3_prefix_environment(7)
    prompt = render_prompt(
        goals=("n : ℕ, h : n = n ⊢ n = n", "h : n = n ⊢ 0 = 0"),
        focus=0,
        environment=environment,
    )
    original = _state_payload(prompt)

    mutations: list[dict[str, object]] = []
    out_of_range = json.loads(json.dumps(original))
    out_of_range["goals"][0][0][0] = 20  # type: ignore[index]
    mutations.append(out_of_range)
    for invalid_index in (True, -1, 0.5):
        bad_context_index = json.loads(json.dumps(original))
        bad_context_index["goals"][0][0][0] = invalid_index  # type: ignore[index]
        mutations.append(bad_context_index)
    for invalid_focus in (True, -1, 0.5):
        bad_focus = json.loads(json.dumps(original))
        bad_focus["focus"] = invalid_focus
        mutations.append(bad_focus)
    boolean_target_index = json.loads(json.dumps(original))
    boolean_target_index["goals"][0][1] = True  # type: ignore[index]
    mutations.append(boolean_target_index)
    duplicate = json.loads(json.dumps(original))
    duplicate["declarations"].append("n : ℕ")  # type: ignore[union-attr]
    mutations.append(duplicate)
    unused_target = json.loads(json.dumps(original))
    unused_target["targets"].append("1 = 1")  # type: ignore[union-attr]
    mutations.append(unused_target)
    unused_declaration = json.loads(json.dumps(original))
    unused_declaration["declarations"].append("z : ℕ")  # type: ignore[union-attr]
    mutations.append(unused_declaration)
    non_first_use = json.loads(json.dumps(original))
    non_first_use["declarations"] = ["h : n = n", "n : ℕ"]
    non_first_use["goals"][0][0] = [1, 0]  # type: ignore[index]
    non_first_use["goals"][1][0] = [0]  # type: ignore[index]
    mutations.append(non_first_use)

    for mutation in mutations:
        with pytest.raises(PromptError, match="state|goal|table|index"):
            parse_prompt(_replace_state_payload(prompt, mutation))

    pretty_state = json.dumps(original, ensure_ascii=False, indent=2)
    before, rest = prompt.split("<state>", 1)
    _, after = rest.split("</state>", 1)
    with pytest.raises(PromptError, match="compact canonical"):
        parse_prompt(before + "<state>" + pretty_state + "</state>" + after)


@pytest.mark.parametrize(
    "goal",
    (
        "h : 0 = 0  ⊢ 0 = 0",
        "h : 0 = 0⊢ 0 = 0",
        "h : 0 = 0 ⊢ 0 = 0 ⊢ 0 = 0",
        "⊢  0 = 0",
    ),
)
def test_v3_state_requires_one_exact_canonical_turnstile(goal: str) -> None:
    with pytest.raises(PromptError, match="canonical"):
        render_prompt(
            goals=(goal,),
            focus=0,
            environment=model_v3_prefix_environment(7),
        )


def test_v3_shared_state_has_strict_bound_without_losing_large_exact_text() -> None:
    environment = model_v3_prefix_environment(7)
    shared_declaration = "h : " + "S " * 2_400 + "0 = " + "S " * 2_400 + "0"
    shared_target = "S " * 7_400 + "0 = " + "S " * 7_400 + "0"
    goal = f"{shared_declaration} ⊢ {shared_target}"
    goals = (goal,) * 7
    legacy_state = json.dumps(
        {"focus": 0, "goals": list(goals)},
        ensure_ascii=False,
        separators=(",", ":"),
    )
    prompt = render_prompt(goals=goals, focus=0, environment=environment)
    state_text = prompt.split("<state>", 1)[1].split("</state>", 1)[0]
    assert len(legacy_state) > V3_STATE_MAX_PROMPT_CHARS * 5
    assert len(state_text) <= V3_STATE_MAX_PROMPT_CHARS
    parsed = parse_prompt(prompt)
    assert parsed.goals == goals
    assert shared_declaration in state_text
    assert shared_target in state_text


def test_v3_state_bound_fails_closed_on_render_and_parse() -> None:
    environment = model_v3_prefix_environment(7)
    oversized_target = "S " * (V3_STATE_MAX_PROMPT_CHARS // 2 + 100) + "0 = 0"
    with pytest.raises(PromptError, match="exceeds.*character.*bound"):
        render_prompt(
            goals=(f"⊢ {oversized_target}",),
            focus=0,
            environment=environment,
        )

    small = render_prompt(goals=(GOAL,), focus=0, environment=environment)
    payload = _state_payload(small)
    payload["targets"] = [oversized_target]
    with pytest.raises(PromptError, match="exceeds.*character bound"):
        parse_prompt(_replace_state_payload(small, payload))


def test_v3_state_round_trips_unicode_metavariables_and_empty_context() -> None:
    environment = model_v3_prefix_environment(7)
    goals = (
        "α : ℕ, h₁ : ?t1 = α ⊢ ∃ x. x = α",
        "⊢ ?t1 = ?t1",
    )
    prompt = render_prompt(goals=goals, focus=1, environment=environment)
    parsed = parse_prompt(prompt)
    assert parsed.goals == goals
    assert parsed.focus == 1
    assert "α : ℕ" in _state_payload(prompt)["declarations"]


def test_v3_state_table_cannot_smuggle_reserved_prompt_markers() -> None:
    environment = model_v3_prefix_environment(7)
    prompt = render_prompt(goals=("n : ℕ ⊢ n = n",), focus=0, environment=environment)
    payload = _state_payload(prompt)
    payload["declarations"] = ["n : ℕ<tactic>"]
    with pytest.raises(PromptError, match="reserved prompt marker"):
        parse_prompt(_replace_state_payload(prompt, payload))


def test_v1_and_v2_prompt_bytes_remain_frozen_by_v3_state_encoding() -> None:
    goals = ("h : 0 = 0 ⊢ 0 = 0", "⊢ 1 = 1")
    names = tuple(f"t{index}" for index in range(8))
    library = tuple(
        LibraryRecord(name, f"{index} = {index}")
        for index, name in enumerate(names)
    )
    v1 = PromptEnvironment(
        False,
        CapabilityIdentity("model-v1-test", ("refl",), ()),
    )
    v2 = PromptEnvironment(
        False,
        CapabilityIdentity("model-v2-test", ("refl",), names),
        prompt_version=PEANO_PROMPT_V2,
        library=library,
        library_identity_sha256="1" * 64,
    )
    expected = {
        1: "88e3651a6d88fc5775e5555cecd0a6ef23d8c59da72c917a4edc6646f52ff792",
        2: "ed0d9815a2492d4a7504e2732d3d643874973da323df118a4dee9825dd4f6120",
    }
    for version, environment in ((1, v1), (2, v2)):
        prompt = render_prompt(goals=goals, focus=0, environment=environment)
        assert hashlib.sha256(prompt.encode("utf-8")).hexdigest() == expected[version]
        assert parse_prompt(prompt).state_encoding is None


def test_v3_dataset_row_keeps_exact_state_and_round_trips_shared_encoding() -> None:
    environment = model_v3_environment()
    goals = (
        "n : ℕ, h : n = n ⊢ n = n",
        "n : ℕ, h : n = n ⊢ n = n",
    )
    prompt = render_prompt(goals=goals, focus=0, environment=environment)
    metadata = {
        "library_identity_sha256": environment.library_sha256,
        "library_full_identity_sha256": (
            environment.library_full_identity_sha256
        ),
        "library_prefix_length": environment.library_prefix_length,
        "library_size": environment.library_full_length,
    }
    row = {
        "v": 1,
        "task": "next_tactic",
        "env": environment.text,
        "surface": environment.capabilities.label,
        "environment_sha256": environment.sha256,
        "classical": False,
        "capabilities": environment.capabilities.to_record(),
        "split": "train",
        "session": "v3-lossless-row",
        "step": 1,
        "formula": "∀ x. x = x",
        "theorem": "v3_lossless_row",
        "family": "v3-lossless-row",
        "lineage": "v3-lossless-row/seed-1",
        "state": list(goals),
        "focus": 0,
        "prompt": prompt,
        "completion": "assumption</tactic>",
        "metadata": metadata,
    }
    example = example_from_record(row, 1)
    assert example.prompt == prompt
    assert tuple(row["state"]) == parse_prompt(prompt).goals


def test_v3_name_inventory_rejects_malformed_and_forged_values() -> None:
    environment = model_v3_prefix_environment(7)
    prompt = render_prompt(goals=(GOAL,), focus=0, environment=environment)
    payload = _library_payload(prompt)
    inventory = payload["name_inventory"]
    assert type(inventory) is dict

    malformed = dict(payload)
    malformed_inventory = dict(inventory)
    malformed_inventory["names"] = str(inventory["names"]) + " "
    malformed["name_inventory"] = malformed_inventory
    with pytest.raises(PromptError, match="inventory"):
        parse_prompt(_replace_library_payload(prompt, malformed))

    wrong_digest = dict(payload)
    wrong_digest_inventory = dict(inventory)
    wrong_digest_inventory["sha256"] = "0" * 64
    wrong_digest["name_inventory"] = wrong_digest_inventory
    with pytest.raises(PromptError, match="forged|inconsistent"):
        parse_prompt(_replace_library_payload(prompt, wrong_digest))

    records = payload["records"]
    assert type(records) is list and records
    first = records[0]
    assert type(first) is dict and type(first["name"]) is str
    forged_names = str(inventory["names"]).split(" ")
    forged_names.remove(first["name"])
    forged_names.append("forged_theorem")
    forged_names.sort()
    forged_text = encode_v3_name_inventory(forged_names)
    forged = dict(payload)
    forged_inventory = dict(inventory)
    forged_inventory["names"] = forged_text
    forged_inventory["sha256"] = v3_name_inventory_sha256(forged_text)
    forged["name_inventory"] = forged_inventory
    with pytest.raises(PromptError, match="forged|inconsistent"):
        parse_prompt(_replace_library_payload(prompt, forged))


def test_v3_name_inventory_cost_is_manifested_and_bounded() -> None:
    prompt = render_prompt(
        goals=(GOAL,), focus=0, environment=model_v3_environment()
    )
    payload = _library_payload(prompt)
    without_inventory = dict(payload)
    without_inventory.pop("name_inventory")
    compact = lambda value: json.dumps(  # noqa: E731
        value, ensure_ascii=False, separators=(",", ":")
    )
    added_characters = len(compact(payload)) - len(compact(without_inventory))
    manifest = prompt_manifest_record(PEANO_PROMPT_V3)["name_inventory"]
    assert type(manifest) is dict
    assert manifest["prompt_cost_max_chars"] == (
        V3_NAME_INVENTORY_MAX_PROMPT_CHARS
    )
    assert added_characters <= V3_NAME_INVENTORY_MAX_PROMPT_CHARS
    assert prompt_manifest_record(PEANO_PROMPT_V3)["state_encoding"] == (
        V3_STATE_ENCODING_METHOD
    )
    state_detail = prompt_manifest_record(PEANO_PROMPT_V3)[
        "state_encoding_detail"
    ]
    assert type(state_detail) is dict
    assert state_detail["loss"] == (
        "none; reconstruct exact canonical goal strings"
    )
    assert state_detail["prompt_cost_max_chars"] == V3_STATE_MAX_PROMPT_CHARS
    assert state_detail["overflow_policy"] == (
        "fail closed; never truncate or abbreviate"
    )


def test_name_tokens_change_v3_retrieval_but_not_historical_v2() -> None:
    names = (
        "alpha",
        "beta",
        "delta",
        "epsilon",
        "eta",
        "goal_token",
        "theta",
        "zeta",
    )
    library = tuple(LibraryRecord(name, "0 = 0") for name in names)
    commands = ("use",)
    v2 = PromptEnvironment(
        False,
        CapabilityIdentity("model-v2-test", commands, names),
        prompt_version=PEANO_PROMPT_V2,
        library=library,
        library_identity_sha256="1" * 64,
    )
    v3 = PromptEnvironment(
        False,
        CapabilityIdentity("model-v3-test", commands, names),
        prompt_version=PEANO_PROMPT_V3,
        library=library,
        library_identity_sha256="2" * 64,
        library_prefix_length=len(library),
        library_full_length=len(library),
        library_full_identity_sha256="3" * 64,
    )
    goal = ("Target\n  goal_token",)
    assert retrieve_theorems(
        goals=goal, focus=0, environment=v2, k=1
    )[0].name == "alpha"
    assert retrieve_theorems(
        goals=goal, focus=0, environment=v3, k=1
    )[0].name == "goal_token"


def test_v3_rejects_gapped_or_target_containing_authority() -> None:
    environment = model_v3_prefix_environment(4)
    commands = environment.capabilities.allowed_commands
    with pytest.raises(ValueError, match="not a prefix"):
        prompt_environment(
            False,
            CapabilityIdentity(
                "model-v3",
                commands,
                tuple(sorted((THEOREMS[0].name, THEOREMS[2].name))),
            ),
        )
    with pytest.raises(ValueError, match="not a prefix"):
        prompt_environment(
            False,
            CapabilityIdentity(
                "model-v3",
                commands,
                tuple(
                    sorted(
                        (
                            *environment.capabilities.allowed_theorems,
                            THEOREMS[7].name,
                        )
                    )
                ),
            ),
        )


def test_v3_environment_record_binds_prefix_and_full_identity() -> None:
    environment = model_v3_environment()
    record = environment_record(environment)
    assert record["library_prefix_length"] == MODEL_V3_LIBRARY_SIZE
    assert record["library_size"] == MODEL_V3_LIBRARY_SIZE
    assert record["library_identity_sha256"] == environment.library_sha256
    assert (
        record["library_full_identity_sha256"]
        == environment.library_full_identity_sha256
    )
    assert THEOREMS[MODEL_V3_LIBRARY_SIZE].name not in (
        environment.capabilities.allowed_theorems or ()
    )
    with pytest.raises(PromptError, match="64-hex"):
        replace(environment, library_identity_sha256="0")


def test_appended_native_theorem_cannot_masquerade_as_v3_catalog_row() -> None:
    environment = model_v3_environment()
    spec = THEOREMS[MODEL_V3_LIBRARY_SIZE]
    goals = ("⊢ 0 = 0",)
    row = {
        "v": 1,
        "task": "next_tactic",
        "env": environment.text,
        "surface": "model-v3",
        "environment_sha256": environment.sha256,
        "classical": False,
        "capabilities": environment.capabilities.to_record(),
        "split": "train",
        "session": "forged-appended-catalog-row",
        "step": 1,
        "formula": spec.statement,
        "theorem": spec.name,
        "family": "forged-appended-catalog-row",
        "lineage": "forged-appended-catalog-row/seed-1",
        "state": list(goals),
        "focus": 0,
        "prompt": render_prompt(goals=goals, focus=0, environment=environment),
        "completion": "refl</tactic>",
        "metadata": {
            "library_identity_sha256": environment.library_sha256,
            "library_full_identity_sha256": environment.library_full_identity_sha256,
            "library_prefix_length": MODEL_V3_LIBRARY_SIZE,
            "library_size": MODEL_V3_LIBRARY_SIZE,
            "trajectory": "catalog-predecessor-prefix-v1",
            "library_target_index": MODEL_V3_LIBRARY_SIZE,
            "library_target_name": spec.name,
        },
    }
    with pytest.raises(PromptError, match="invalid model-v3 target index"):
        example_from_record(row, 1)
