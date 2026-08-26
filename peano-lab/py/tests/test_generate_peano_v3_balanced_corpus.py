"""Contracts for the model-v3 root-balanced synthetic generator."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from peano_lab.batch import MODEL_V1_COMMANDS, run_proof
from peano_lab.library.theorems import THEOREMS
from peano_lab.ui.prove import SurfaceCapabilities


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPOSITORY_ROOT / "scripts"
GENERATOR_SOURCE = SCRIPTS_ROOT / "generate_peano_v3_balanced_corpus.py"
for import_root in (REPOSITORY_ROOT, SCRIPTS_ROOT):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from export_traces import load_trace_file  # noqa: E402
from training.peano_policy.contract import (  # noqa: E402
    MODEL_V3_LIBRARY_SIZE,
    canonical_held_out_formulas,
    model_v3_environment,
)
from training.peano_policy import attest as attestor  # noqa: E402
from training.peano_policy.prompt import PEANO_PROMPT_V3  # noqa: E402


def _load_script(name: str, path: Path):
    specification = importlib.util.spec_from_file_location(name, path)
    assert specification is not None and specification.loader is not None
    module = importlib.util.module_from_spec(specification)
    sys.modules[specification.name] = module
    specification.loader.exec_module(module)
    return module


generator = _load_script("_test_generate_peano_v3_balanced", GENERATOR_SOURCE)
builder = _load_script(
    "_test_build_for_v3_balanced",
    SCRIPTS_ROOT / "build_peano_policy_dataset.py",
)


def _paths(root: Path) -> tuple[Path, Path, Path]:
    return root / "raw.jsonl", root / "metadata.jsonl", root / "manifest.json"


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _cheap_full_capabilities() -> SurfaceCapabilities:
    """The same name preimage, without replaying identity for schema smoke."""

    return SurfaceCapabilities(
        label="model-v3",
        allowed_commands=MODEL_V1_COMMANDS,
        allowed_theorems=frozenset(
            spec.name for spec in THEOREMS[:MODEL_V3_LIBRARY_SIZE]
        ),
    )


def test_catalog_removes_library_schemas_and_exposes_real_root_shapes() -> None:
    assert generator.PROFILE == "model-v3"
    assert generator.CATALOG_VERSION == 2
    assert generator.GENERATOR == "proof-first-root-balanced-v3"
    assert len(generator.SCHEMAS) == len({schema.name for schema in generator.SCHEMAS})
    assert not [
        schema.name
        for schema in generator.SCHEMAS
        if schema.name.startswith("library-") or "reused-library-" in schema.name
    ]
    assert {"intro", "induction", "exists", "split", "left", "right"} <= set(
        generator.ROOT_HEADS
    )
    assert generator.HELD_OUT_FORMULAS == frozenset(
        canonical_held_out_formulas(PEANO_PROMPT_V3)
    )
    assert len(generator.HELD_OUT_FORMULAS) == 4

    root_kinds: set[str] = set()
    capabilities = _cheap_full_capabilities()
    source = GENERATOR_SOURCE.read_text(encoding="utf-8")
    assert "run_proof(" in source
    for ordinal, schema in enumerate(generator.ROOT_SCHEMAS, 1):
        candidate = schema.build(ordinal)
        canonical, formula = generator._canonical_statement(candidate, schema)
        assert canonical not in generator.HELD_OUT_FORMULAS
        first_head = candidate.tactics[0].split(maxsplit=1)[0]
        root_kinds.add(generator._root_kind(formula, first_head, candidate))
        result = run_proof(
            candidate.statement,
            candidate.tactics,
            capabilities=capabilities,
            request_id=f"root-schema-{ordinal}",
        )
        assert result.status == "proved", (schema.name, result.error)
        assert result.kernel_checked is True
    assert {"equality", "existential", "conjunction", "disjunction"} <= root_kinds


def test_ring_root_domain_excludes_every_over_limit_tuple_and_stays_unique() -> None:
    all_coefficients = {
        (a, b, c, d)
        for a in range(generator.RING_DIGIT_BASE)
        for b in range(generator.RING_DIGIT_BASE)
        for c in range(generator.RING_DIGIT_BASE)
        for d in range(generator.RING_DIGIT_BASE)
    }
    unsafe_coefficients = {
        (5, 6, 6, 6),
        (6, 5, 6, 6),
        (6, 6, 5, 6),
        (6, 6, 6, 5),
        (6, 6, 6, 6),
    }
    safe_coefficients = set(generator.RING_SAFE_COEFFICIENTS)
    assert len(generator.RING_SAFE_COEFFICIENTS) == 2_396
    assert all_coefficients - safe_coefficients == unsafe_coefficients
    assert max((a + b) * (c + d) for a, b, c, d in safe_coefficients) <= 128

    maximum_balanced_ring_index = (
        generator.SCHEMA_OFFSET_MODULUS
        + (generator.MAX_ROW_BUDGET + len(generator.ROOT_HEADS) - 1)
        // len(generator.ROOT_HEADS)
    )
    assert generator.RING_CANDIDATE_PERIOD > maximum_balanced_ring_index
    assert len(
        {
            generator._closed_ring(index).statement
            for index in range(generator.RING_CANDIDATE_PERIOD)
        }
    ) == generator.RING_CANDIDATE_PERIOD

    ring_schema = next(
        schema for schema in generator.ROOT_SCHEMAS if schema.name == "root-equality-ring"
    )
    offset = generator._schema_offset(
        "peano-policy-v3-balanced-wmi-20260729",
        ring_schema,
    )
    capabilities = _cheap_full_capabilities()
    for ordinal, unsafe in enumerate(sorted(unsafe_coefficients), 1):
        old_residue = sum(
            digit * generator.RING_DIGIT_BASE**position
            for position, digit in enumerate(unsafe)
        )
        parameter_index = offset + (
            (old_residue - offset)
            % generator.RING_DIGIT_BASE**len(unsafe)
        )
        candidate = generator._closed_ring(parameter_index)
        assert candidate.parameters["normalized_coefficient"] <= 128
        assert tuple(candidate.parameters["coefficients"]) not in unsafe_coefficients
        result = run_proof(
            candidate.statement,
            candidate.tactics,
            capabilities=capabilities,
            request_id=f"ring-limit-regression-{ordinal}",
        )
        assert result.status == "proved", (parameter_index, result.error)
        assert result.kernel_checked is True


@pytest.mark.parametrize(
    ("schema_name", "parameter_index"),
    (
        ("root-equality-ring", 4_446),
        ("root-equality-ring", 4_452),
        ("root-equality-ring", 4_739),
        ("root-equality-ring", 4_745),
        ("reused-arithmetic-ring-product", 559),
        ("reused-arithmetic-ring-square", 19_327),
    ),
)
def test_ring_resource_frontier_instances_remain_kernel_checked(
    schema_name: str,
    parameter_index: int,
) -> None:
    schema = next(schema for schema in generator.SCHEMAS if schema.name == schema_name)
    candidate = schema.build(parameter_index)
    result = run_proof(
        candidate.statement,
        candidate.tactics,
        capabilities=_cheap_full_capabilities(),
        request_id=f"ring-resource-frontier-{schema_name}-{parameter_index}",
    )
    assert result.status == "proved", result.error
    assert result.kernel_checked is True
    assert result.proof_nodes is not None and result.proof_nodes < 100_000


def test_induction_gate_removal_is_exact_immutable_and_checked() -> None:
    schemas = [
        schema
        for schema in generator.REUSED_SCHEMAS
        if schema.name.startswith("reused-induction-")
    ]
    assert len(schemas) == 4
    capabilities = _cheap_full_capabilities()
    for ordinal, schema in enumerate(schemas, 1):
        parameter_index = generator._schema_offset(
            "peano-policy-v3-balanced-wmi-20260729",
            schema,
        )
        candidate = schema.build(parameter_index)
        assert candidate.tactics[0].split(maxsplit=1)[0] == "induction"
        assert "intro gate" not in candidate.tactics
        assert "gate" not in candidate.parameters
        assert candidate.parameters["artificial_gate_removed"] is True
        assert (
            candidate.parameters["closed_root_zero_tag_method"]
            == "bounded-syntactic-zero-v1"
        )
        assert not candidate.statement.startswith("(") or "gate" not in candidate.statement
        result = run_proof(
            candidate.statement,
            candidate.tactics,
            capabilities=capabilities,
            request_id=f"ungated-induction-{ordinal}",
        )
        assert result.status == "proved", (schema.name, result.error)
        assert result.kernel_checked is True
        assert len(
            {
                schema.build(index).statement
                for index in range(generator.INDUCTION_ZERO_TAG_PERIOD)
            }
        ) == generator.INDUCTION_ZERO_TAG_PERIOD

    malformed = generator.Candidate("0 = 0", ("refl",), {"gate": "0 = 0"})
    with pytest.raises(generator.GenerationError, match="exact removable gate"):
        generator._ungate_candidate(malformed)
    assert malformed == generator.Candidate(
        "0 = 0", ("refl",), {"gate": "0 = 0"}
    )


def test_full_wmi_schedule_is_exact_balanced_unique_and_preflighted() -> None:
    generator._validate_catalog()
    plan = generator._plan_schedule(
        seed="peano-policy-v3-balanced-wmi-20260729",
        row_budget=70_000,
        budget_mode="exact",
    )

    assert plan["positive_tactic_rows"] == 70_000
    assert plan["sessions"] == 32_600
    assert plan["independent_roots"] == plan["sessions"]
    assert plan["unique_canonical_statements"] == plan["sessions"]

    head_counts = plan["root_sessions_by_first_tactic_head"]
    assert isinstance(head_counts, dict)
    assert set(head_counts) == set(generator.ROOT_HEADS)
    assert set(head_counts.values()) == {2_328, 2_329}
    assert max(head_counts.values()) - min(head_counts.values()) == 1
    assert 5 * head_counts["intro"] <= plan["sessions"]
    assert plan["candidate_skips"] == {
        "duplicate_statement": 0,
        "held_out_target": 0,
        "overlong_exact_fill": 0,
    }

    schema_counts = plan["sessions_by_schema"]
    assert isinstance(schema_counts, dict)
    assert set(schema_counts) == {schema.name for schema in generator.SCHEMAS}
    assert all(count > 0 for count in schema_counts.values())
    assert plan["sequence_sha256"] == (
        "79d2704eab6eb73205ff2234f55f0d4a7e034176fe8dc8649c6950ff499d547b"
    )


def test_maximum_schedule_counts_and_skips_reserved_held_out_candidate() -> None:
    schema = next(
        schema
        for schema in generator.ROOT_SCHEMAS
        if schema.name == "root-equality-norm"
    )
    held_out_candidate = schema.build(13_616)
    with pytest.raises(generator._HeldOutTargetError, match="held-out target"):
        generator._canonical_statement(held_out_candidate, schema)

    plan = generator._plan_schedule(
        seed="peano-policy-v3-balanced-wmi-20260729",
        row_budget=generator.MAX_ROW_BUDGET,
        budget_mode="exact",
    )
    assert plan["positive_tactic_rows"] == generator.MAX_ROW_BUDGET
    assert plan["sessions"] == 46_574
    assert plan["independent_roots"] == plan["sessions"]
    assert plan["unique_canonical_statements"] == plan["sessions"]
    assert set(plan["sessions_by_schema"]) == {
        schema.name for schema in generator.SCHEMAS
    }
    assert max(plan["root_sessions_by_first_tactic_head"].values()) - min(
        plan["root_sessions_by_first_tactic_head"].values()
    ) == 1
    assert plan["candidate_skips"] == {
        "duplicate_statement": 0,
        "held_out_target": 1,
        "overlong_exact_fill": 0,
    }
    assert plan["sequence_sha256"] == (
        "c9acdf586b16ee6a8cf8dacf923977f177c4262859156c5f9c5d45848ba1e83e"
    )


def test_schedule_does_not_swallow_an_ordinary_generation_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_candidate(*args: object, **kwargs: object):
        del args, kwargs
        raise generator.GenerationError("ordinary schema failure")

    monkeypatch.setattr(generator, "_canonical_statement", fail_candidate)
    schedule = generator._Schedule(
        "fail-closed-test",
        generator.Counter(),
        generator.Counter(),
        generator.Counter(),
    )
    with pytest.raises(generator.GenerationError, match="ordinary schema failure"):
        generator._select_candidate(
            schedule,
            sessions=0,
            remaining=1,
            budget_mode="exact",
            seen_statements=set(),
            seen_roots=set(),
        )


def test_held_out_formula_cannot_hide_as_an_intermediate_goal_target() -> None:
    held_out = canonical_held_out_formulas(PEANO_PROMPT_V3)[0]
    malicious = run_proof(
        f"({held_out}) /\\ (0 = 0)",
        ("split", "norm_num", "refl"),
        capabilities=_cheap_full_capabilities(),
        request_id="held-out-intermediate-bypass",
        session_id="held-out-intermediate-bypass",
    )
    assert malicious.status == "proved"
    assert malicious.kernel_checked is True
    assert malicious.trace is not None
    transitions = tuple(record for record in malicious.trace if "v" in record)
    assert transitions[1]["goals_before"] == [f"⊢ {held_out}", "⊢ 0 = 0"]

    with pytest.raises(builder.DatasetBuildError, match="held-out.*goal target"):
        builder._validate_no_v3_held_out_goal_targets(
            transitions,
            session_id="held-out-intermediate-bypass",
        )
    with pytest.raises(
        attestor.DatasetAttestationError,
        match="held-out formula appears as goal target",
    ):
        attestor._validate_no_held_out_goal_targets(
            transitions[1]["goals_before"],
            forbidden_targets=builder.MODEL_V3_HELD_OUT_TARGETS,
            location="regression-row",
        )

    # Only the target is excluded. The exact held-out proposition may occur as
    # a hypothesis, and structurally nearby but unequal targets remain valid.
    legitimate = run_proof(
        f"({held_out}) -> 0 = 0",
        ("intro h", "refl"),
        capabilities=_cheap_full_capabilities(),
        request_id="held-out-context-near-miss",
        session_id="held-out-context-near-miss",
    )
    assert legitimate.status == "proved"
    assert legitimate.kernel_checked is True
    assert legitimate.trace is not None
    legitimate_steps = tuple(record for record in legitimate.trace if "v" in record)
    builder._validate_no_v3_held_out_goal_targets(
        legitimate_steps,
        session_id="held-out-context-near-miss",
    )
    attestor._validate_no_held_out_goal_targets(
        legitimate_steps[1]["goals_before"],
        forbidden_targets=builder.MODEL_V3_HELD_OUT_TARGETS,
        location="near-miss-row",
    )


def test_exact_budget_is_root_balanced_full_prefix_and_builder_replayable(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace, metadata_path, manifest_path = _paths(tmp_path / "balanced")
    generated = generator.generate_corpus(
        trace,
        metadata_path,
        manifest_path,
        seed="v3-test",
        row_budget=30,
        budget_mode="exact",
    )

    sessions = load_trace_file(trace)
    metadata = _jsonl(metadata_path)
    manifest = generated.manifest
    counts = manifest["counts"]
    environment = model_v3_environment()
    assert counts["positive_tactic_rows"] == 30
    assert sum(len(session.steps) for session in sessions) == 30
    assert len(sessions) == len(metadata) == counts["sessions"]
    assert counts["kernel_checked_qed"] == len(sessions)
    assert all(session.footer["qed"] is True for session in sessions)
    assert all(step["status"] == "ok" for session in sessions for step in session.steps)
    assert counts["intro_root_percent"] <= 20
    assert counts["root_head_session_imbalance"] <= 1
    assert generator.REQUIRED_ROOT_KINDS <= set(counts["sessions_by_root_kind"])
    assert manifest["config"]["selection"] == generator.SCHEDULE_SELECTION
    assert manifest["curriculum"]["artificial_induction_gates"] == 0
    assert manifest["curriculum"]["library_schemas"] == 0
    assert manifest["curriculum"]["schedule_plan"]["sessions"] == len(sessions)
    assert not {record["statement"] for record in metadata} & generator.HELD_OUT_FORMULAS

    assert all(record["surface"] == "model-v3" for record in metadata)
    assert all(
        record["environment_sha256"] == environment.sha256 for record in metadata
    )
    assert all(
        record["library_identity_sha256"] == environment.library_sha256
        for record in metadata
    )
    assert all(
        record["library_full_identity_sha256"]
        == environment.library_full_identity_sha256
        for record in metadata
    )
    assert all(
        record["library_prefix_length"]
        == record["library_size"]
        == MODEL_V3_LIBRARY_SIZE
        for record in metadata
    )
    assert all(record["root_first_tactic_head"] for record in metadata)
    assert len({record["root"] for record in metadata}) == len(metadata)

    assert manifest["artifacts"]["trace"] == {
        "path": trace.name,
        "bytes": len(trace.read_bytes()),
        "sha256": _sha256(trace),
    }
    assert manifest["artifacts"]["metadata"] == {
        "path": metadata_path.name,
        "bytes": len(metadata_path.read_bytes()),
        "sha256": _sha256(metadata_path),
    }

    replay_options: list[dict[str, object]] = []
    real_run_proof = builder.run_proof

    def observed_replay(*args: object, **kwargs: object):
        replay_options.append(dict(kwargs))
        return real_run_proof(*args, **kwargs)

    monkeypatch.setattr(builder, "run_proof", observed_replay)
    compiled = builder.build_dataset(
        [trace],
        metadata_path,
        tmp_path / "dataset",
        seed="v3-balanced-builder",
        val_fraction=0.1,
        test_fraction=0.1,
    )
    assert compiled.manifest["replay"] == {
        "attempted_qed_sessions": len(sessions),
        "accepted_kernel_checked_sessions": len(sessions),
        "positive_rows": 30,
        "transactional_error_steps_ignored": 0,
    }
    assert replay_options
    assert all("trace_byte_limit" not in options for options in replay_options)
    assert compiled.manifest["environments"] == [
        {**manifest["environment"], "sessions": len(sessions)}
    ]


def test_builder_and_attestor_reject_omitted_forged_or_unbound_synthetic_lane(
    tmp_path: Path,
) -> None:
    trace, metadata_path, manifest_path = _paths(tmp_path / "marker-source")
    generator.generate_corpus(
        trace,
        metadata_path,
        manifest_path,
        seed="v3-marker-test",
        row_budget=1,
        budget_mode="exact",
    )
    original = _jsonl(metadata_path)[0]

    mutations = {
        "omitted-lane": lambda record: record.pop("lane"),
        "forged-lane": lambda record: record.__setitem__("lane", "another-lane"),
        "forged-statement-hash": lambda record: record.__setitem__(
            "statement_sha256", "0" * 64
        ),
        "forged-script-hash": lambda record: record.__setitem__(
            "script_sha256", "0" * 64
        ),
    }
    for label, mutate in mutations.items():
        changed = json.loads(json.dumps(original))
        mutate(changed)
        sidecar = tmp_path / f"{label}.jsonl"
        sidecar.write_text(
            json.dumps(changed, ensure_ascii=False, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        with pytest.raises(
            builder.DatasetBuildError,
            match="approved|differs from its approved",
        ):
            builder.build_dataset(
                [trace],
                sidecar,
                tmp_path / f"dataset-{label}",
                val_fraction=0.0,
                test_fraction=0.0,
            )

        row = {
            "surface": "model-v3",
            "session": changed["session"],
            "formula": changed["statement"],
            "theorem": changed["theorem"],
            "metadata": builder._metadata_extras(changed),
        }
        with pytest.raises(
            attestor.DatasetAttestationError,
            match="approved synthetic lane evidence",
        ):
            attestor._record_v3_curriculum_evidence(
                row,
                {},
                library_size=MODEL_V3_LIBRARY_SIZE,
                location=label,
            )


def test_attestor_derives_schedule_only_from_exact_session_evidence() -> None:
    environment = model_v3_environment()
    evidence = {
        **{
            f"catalog-{prefix:03d}": (
                prefix,
                attestor.V3_CATALOG_TRAJECTORY,
                f"catalog-digest-{prefix:03d}",
            )
            for prefix in range(MODEL_V3_LIBRARY_SIZE)
        },
        "synthetic-001": (
            MODEL_V3_LIBRARY_SIZE,
            attestor.V3_SYNTHETIC_LANE,
            "synthetic-digest",
        ),
    }
    training_environments = tuple(
        {
            "library_prefix_length": prefix,
            "sessions": 1,
        }
        for prefix in range(MODEL_V3_LIBRARY_SIZE + 1)
    )
    assert attestor._verify_v3_curriculum_schedule(
        evidence,
        training_environments,
        environment,
    ) == {
        "method": "catalog-predecessor-prefix-v1+full-synthetic-v1",
        "full_library_sha256": environment.library_full_identity_sha256,
        "library_size": MODEL_V3_LIBRARY_SIZE,
        "training_prefixes": list(range(MODEL_V3_LIBRARY_SIZE + 1)),
        "inference_prefix": MODEL_V3_LIBRARY_SIZE,
    }

    duplicate = dict(evidence)
    duplicate["catalog-000-copy"] = (
        0,
        attestor.V3_CATALOG_TRAJECTORY,
        "copy",
    )
    with pytest.raises(
        attestor.DatasetAttestationError,
        match="prefix 0 must have exactly one",
    ):
        attestor._verify_v3_curriculum_schedule(
            duplicate,
            training_environments,
            environment,
        )

    missing = dict(evidence)
    missing.pop("catalog-001")
    with pytest.raises(
        attestor.DatasetAttestationError,
        match="does not cover the exact authority schedule",
    ):
        attestor._verify_v3_curriculum_schedule(
            missing,
            training_environments,
            environment,
        )


def test_complete_session_budget_and_transactional_publication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    complete = _paths(tmp_path / "complete")
    result = generator.generate_corpus(
        *complete,
        seed="complete-session",
        row_budget=1,
        budget_mode="complete-session",
    )
    sessions = load_trace_file(complete[0])
    assert result.manifest["counts"]["positive_tactic_rows"] >= 1
    assert len(sessions) == 1
    assert sessions[0].footer["qed"] is True
    assert len(sessions[0].steps) == result.manifest["counts"]["positive_tactic_rows"]

    paths = _paths(tmp_path / "transactional")
    old = (b"old trace\n", b"old metadata\n", b"old manifest\n")
    for path, payload in zip(paths, old, strict=True):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    real_run_proof = generator.run_proof

    def unchecked(*args, **kwargs):
        return replace(real_run_proof(*args, **kwargs), kernel_checked=False)

    monkeypatch.setattr(generator, "run_proof", unchecked)
    with pytest.raises(generator.GenerationError, match="failed checked QED"):
        generator.generate_corpus(
            *paths,
            seed="unchecked",
            row_budget=1,
            budget_mode="exact",
        )
    assert tuple(path.read_bytes() for path in paths) == old
    assert not list(tmp_path.rglob(".*.tmp"))


def test_invalid_budget_mode_and_alias_fail_before_opening_outputs(
    tmp_path: Path,
) -> None:
    paths = _paths(tmp_path)
    with pytest.raises(ValueError, match="between 1"):
        generator.generate_corpus(*paths, row_budget=0)
    with pytest.raises(ValueError, match="budget_mode"):
        generator.generate_corpus(*paths, row_budget=1, budget_mode="partial")
    with pytest.raises(generator.GenerationError, match="must be distinct"):
        generator.generate_corpus(
            paths[0], paths[0], paths[2], row_budget=1, budget_mode="exact"
        )
    assert not any(path.exists() for path in paths)


def test_cli_pins_model_v3_and_both_stopping_modes() -> None:
    common = [
        "--trace-output",
        "raw.jsonl",
        "--metadata-output",
        "metadata.jsonl",
        "--manifest",
        "manifest.json",
        "--row-budget",
        "7",
    ]
    with pytest.raises(SystemExit) as missing:
        generator._parser().parse_args(common)
    assert missing.value.code == 2
    parsed = generator._parser().parse_args(
        [
            "--profile",
            "model-v3",
            "--budget-mode",
            "complete-session",
            *common,
        ]
    )
    assert parsed.profile == generator.PROFILE
    assert parsed.budget_mode == "complete-session"
