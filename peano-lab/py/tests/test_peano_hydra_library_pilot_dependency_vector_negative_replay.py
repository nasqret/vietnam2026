"""Synthetic contracts for the source-only Hydra A2.3c negative replay.

The real 22-observation replay is deliberately out of scope here.  These
tests use compact injected tactic/session stubs to exercise the independent
driver, retained-row join, strict transport, and CLI publication boundaries.
"""

from __future__ import annotations

import ast
from copy import deepcopy
from dataclasses import replace
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[3]
PY_ROOT = ROOT / "peano-lab" / "py"
for path in (str(ROOT), str(PY_ROOT)):
    if path not in sys.path:
        sys.path.insert(0, path)

import training.peano_hydra.library_pilot_dependency_vector_negative_replay as replay  # noqa: E402
from peano_lab.engine.tactics import TacticError, TacticLimit  # noqa: E402
from peano_lab.engine.state import (  # noqa: E402
    ProofState,
    invariants_ok,
    record_step,
    start,
)
from peano_lab.kernel.formulas import Eq  # noqa: E402
from peano_lab.kernel.proofs import EqRefl  # noqa: E402
from peano_lab.kernel.terms import Succ, Zero  # noqa: E402
from peano_lab.library.theorems import TheoremSpec  # noqa: E402


MODULE_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library_pilot_dependency_vector_negative_replay.py"
)
SCHEMA_PATH = (
    ROOT
    / "training/peano_hydra/"
    "library-pilot-dependency-vector-negative-replay-schema-v1.json"
)
CLI_PATH = (
    ROOT
    / "scripts/verify_peano_hydra_library_pilot_dependency_vector_negative_replay.py"
)
CANDIDATE_PATH = (
    ROOT
    / "artifacts/peano-hydra/a23b-wmi-vector-audit-220220/results/"
    "l0-pilot-dependency-vector-audit-candidate-v1.json"
)
VERIFICATION_PATH = (
    ROOT
    / "artifacts/peano-hydra/a23b-wmi-vector-audit-220220/results/"
    "l0-pilot-dependency-vector-audit-independent-verification-v1.json"
)
REPLAY_MANIFEST_PATH = (
    ROOT / "artifacts/peano-hydra/l0-replay-candidate-v1/manifest.json"
)
ISOLATED_PYTHON = shutil.which("python3.12") or shutil.which("python3.11")

EXPECTED_ROOTS = (
    (256, "odd_add_odd"),
    (376, "finite_bounded_injective_surjective"),
    (379, "beta_product_swap_last_invariant"),
)
EXPECTED_DIRECT = {
    "odd_add_odd": (
        "mul_add",
        "add_assoc",
        "add_comm",
    ),
    "finite_bounded_injective_surjective": (
        "finite_surjective_zero",
        "finite_contains_decidable",
        "finite_bounded_last_succ",
        "beta_prefix_swap_last_from_entries",
        "finite_swap_last_bounded",
        "finite_swap_last_injective",
        "finite_bounded_prefix_without_top",
        "finite_injective_prefix_succ",
        "finite_surjective_succ_from_prefix",
        "finite_swap_last_surjective_back",
        "finite_no_top_successor_gate",
        "le_succ",
        "le_refl",
        "lt_irrefl_expanded",
    ),
    "beta_product_swap_last_invariant": (
        "beta_product_replace_balance",
        "beta_product_succ_decompose",
        "beta_at_unique",
        "le_succ",
        "lt_irrefl_expanded",
    ),
}
EXPECTED_SCRIPT_SHA256 = {
    "odd_add_odd": (
        "4d303cb1b7886cceba15a4d29f198ca16eff7aabca04ca577ae48d06878eed59"
    ),
    "finite_bounded_injective_surjective": (
        "6f501cc65ba7d78844c5dd6f42463be97c89b32c6dc2e19d40236a7618315533"
    ),
    "beta_product_swap_last_invariant": (
        "b84a265093efa741e13cb8ac729dc53ce9baca8710dd51fac2b6c17534e373ed"
    ),
}
EXPECTED_COMMAND_COUNTS = {
    "odd_add_odd": 10,
    "finite_bounded_injective_surjective": 178,
    "beta_product_swap_last_invariant": 102,
}
EXPECTED_FAILURE_INDEX = {
    ("odd_add_odd", "add_comm"): 9,
    ("odd_add_odd", "add_assoc"): 9,
    ("odd_add_odd", "mul_add"): 9,
    ("finite_bounded_injective_surjective", "lt_irrefl_expanded"): 107,
    ("finite_bounded_injective_surjective", "le_refl"): 96,
    ("finite_bounded_injective_surjective", "le_succ"): 91,
    (
        "finite_bounded_injective_surjective",
        "finite_no_top_successor_gate",
    ): 162,
    (
        "finite_bounded_injective_surjective",
        "finite_swap_last_surjective_back",
    ): 144,
    (
        "finite_bounded_injective_surjective",
        "finite_surjective_succ_from_prefix",
    ): 135,
    (
        "finite_bounded_injective_surjective",
        "finite_injective_prefix_succ",
    ): 121,
    (
        "finite_bounded_injective_surjective",
        "finite_bounded_prefix_without_top",
    ): 112,
    (
        "finite_bounded_injective_surjective",
        "finite_swap_last_injective",
    ): 68,
    (
        "finite_bounded_injective_surjective",
        "finite_swap_last_bounded",
    ): 49,
    (
        "finite_bounded_injective_surjective",
        "beta_prefix_swap_last_from_entries",
    ): 34,
    (
        "finite_bounded_injective_surjective",
        "finite_bounded_last_succ",
    ): 24,
    (
        "finite_bounded_injective_surjective",
        "finite_contains_decidable",
    ): 15,
    (
        "finite_bounded_injective_surjective",
        "finite_surjective_zero",
    ): 5,
    ("beta_product_swap_last_invariant", "lt_irrefl_expanded"): 73,
    ("beta_product_swap_last_invariant", "le_succ"): 67,
    ("beta_product_swap_last_invariant", "beta_at_unique"): 41,
    (
        "beta_product_swap_last_invariant",
        "beta_product_succ_decompose",
    ): 19,
    (
        "beta_product_swap_last_invariant",
        "beta_product_replace_balance",
    ): 79,
}
PINNED_INPUTS = {
    CANDIDATE_PATH: (
        "4f4965508b63d852697c94fe0e7707759b39c5cf456ec2db8aa5a5afe719f2ad"
    ),
    VERIFICATION_PATH: (
        "50c207c4de0cabe8a50518da4d20e83925f0e1df29ffd78df05e249ea18d4396"
    ),
    REPLAY_MANIFEST_PATH: (
        "8b9f9dc8e35e5eb02e43bcffd6aed6280006f4a01c396e43c43c2cbe4cbfb604"
    ),
}


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _lf_sha(values: tuple[str, ...]) -> str:
    return _sha(("\n".join(values) + "\n").encode("utf-8"))


def _load_cli():
    spec = importlib.util.spec_from_file_location("_a23c_negative_replay_cli", CLI_PATH)
    if spec is None or spec.loader is None:
        raise AssertionError("cannot load A2.3c CLI")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _candidate() -> dict[str, object]:
    return json.loads(CANDIDATE_PATH.read_bytes())


def _synthetic_observations(
    candidate: dict[str, object] | None = None,
) -> list[dict[str, object]]:
    retained = _candidate() if candidate is None else candidate
    specs, tasks = replay._registered_specs_and_tasks(
        replay.pilot_dependency_vector_negative_replay_schema(ROOT)
    )
    specs_by_name = {spec.name: spec for spec in specs}
    tasks_by_key = {
        (task.theorem_name, task.omitted_dependency): task for task in tasks
    }
    observations: list[dict[str, object]] = []
    for theorem in retained["theorems"]:
        for attempt in theorem["routes"][0]["attempts"]:
            omitted = attempt["omitted_dependency"]
            registered = tasks_by_key[(theorem["name"], omitted)]
            trial_spec = replace(
                specs_by_name[theorem["name"]],
                dependencies=registered.trial_dependencies,
            )
            target = replay.DEFAULT_NEGATIVE_REPLAY_HOOKS.replay_target(
                trial_spec
            )
            target_bytes = replay.DEFAULT_NEGATIVE_REPLAY_HOOKS.encode_formula(
                target
            )
            assert type(target_bytes) is bytes
            message = f"unknown hypothesis {omitted!r}."
            failure = {
                **attempt["failure"],
                "diagnostic": (
                    f"candidate {theorem['name']!r} failed at command "
                    f"{attempt['failure']['command_index']}: "
                    f"{attempt['failure']['command']!r}: {message}"
                ),
                "message": message,
                "message_source": "fresh-a2.3c-lower-level-replay",
                "omitted_dependency": omitted,
                "retained_message_available": False,
            }
            body = {
                "attempt_index": attempt["attempt_index"],
                "failure": failure,
                "full_dependencies": attempt["before_dependencies"],
                "name": theorem["name"],
                "omitted_dependency": omitted,
                "outcome": "exact-shared-root-body-rejected",
                "prefix_command_count": attempt["failure"]["command_index"],
                "target_formula_sha256": _sha(target_bytes),
                "theorem_index": theorem["index"],
                "trial_dependencies": attempt["attempted_dependencies"],
            }
            body["record_sha256"] = replay._record_hash(body)
            observations.append(body)
    return observations


def _field(value: object, name: str) -> object:
    if type(value) is dict:
        return value[name]
    return getattr(value, name)


def _synthetic_spec() -> TheoremSpec:
    return TheoremSpec(
        "fixture_root",
        "0 = 0",
        ("keep", "drop"),
        ("intro n", "specialize drop n", "use keep"),
        "Synthetic negative replay root.",
    )


def _synthetic_task() -> replay.NegativeReplayTask:
    spec = _synthetic_spec()
    return replay.NegativeReplayTask(
        theorem_index=7,
        theorem_name=spec.name,
        attempt_index=0,
        omitted_dependency="drop",
        full_dependencies=spec.dependencies,
        trial_dependencies=("keep",),
        script=spec.script,
        expected_command_index=1,
        expected_command="specialize drop n",
        expected_message="unknown hypothesis 'drop'.",
    )


def _driver_hooks(
    apply: object,
    *,
    checked: object | None = None,
) -> replay.NegativeReplayHooks:
    zero = Zero()
    target = Eq(zero, zero)
    proof = EqRefl(zero)

    def recorded_apply(state: object, tactic: str, args: str) -> object:
        result = apply(state, tactic, args)
        if result is state and type(state) is ProofState:
            return record_step(state, state, tactic, args)
        return result

    return replace(
        replay.DEFAULT_NEGATIVE_REPLAY_HOOKS,
        replay_target=lambda _spec: target,
        start=start,
        apply_tactic=recorded_apply,
        checked_final=(
            (lambda _state, supplied: proof if supplied == target else None)
            if checked is None
            else checked
        ),
        proof_resource_metrics=lambda _proof: (1, 1, 1, 0, 0),
        proof_state_type=ProofState,
        invariants_ok=invariants_ok,
        encode_formula=lambda _formula: b"synthetic-formula",
        encode_proof=lambda _proof: b"synthetic-proof",
        runtime_identity=lambda: {},
    )


def _synthetic_environment(schema: dict[str, object]) -> dict[str, object]:
    source_paths = {
        "apply_tactic": "peano-lab/py/peano_lab/engine/tactics.py",
        "checked_final": "peano-lab/py/peano_lab/engine/tactics.py",
        "formula_encode": "peano-lab/py/peano_lab/kernel/artifact_codec.py",
        "proof_encode": "peano-lab/py/peano_lab/kernel/artifact_codec.py",
        "proof_metrics": "peano-lab/py/peano_lab/engine/state.py",
        "proof_state_invariants": "peano-lab/py/peano_lab/engine/state.py",
        "proof_state_type": "peano-lab/py/peano_lab/engine/state.py",
        "replay_target": "peano-lab/py/peano_lab/library/theorems.py",
        "start": "peano-lab/py/peano_lab/engine/state.py",
    }
    callables = {
        "callables": [
            {
                "qualified_name": qualified,
                "source_path": source_paths[label],
            }
            for label, qualified in replay.QUALIFIED_CALLABLES.items()
        ],
        "qualified_callables": deepcopy(replay.QUALIFIED_CALLABLES),
        "status": "exact-callable-identities-authenticated",
    }
    replayer_identity = replay._controlled_replayer_identity(ROOT)
    preimage = {
        "callables": callables,
        "fixed_inputs": deepcopy(schema["fixed_inputs"]),
        "format": (
            "peano-hydra-library-pilot-dependency-vector-negative-replay-"
            "environment-preimage"
        ),
        "implementation_source_root_sha256": (
            replay.IMPLEMENTATION_SOURCE_ROOT_SHA256
        ),
        "runtime": deepcopy(schema["runtime_binding"]),
        "replayer": replayer_identity,
        "schema": replay.pilot_dependency_vector_negative_replay_schema_identity(
            ROOT
        ),
        "v": 1,
    }
    return {
        "callables": callables,
        "fixed_input_count": 6,
        "implementation_source_count": replay.EXPECTED_IMPLEMENTATION_SOURCE_COUNT,
        "implementation_source_root_sha256": (
            replay.IMPLEMENTATION_SOURCE_ROOT_SHA256
        ),
        "preimage": preimage,
        "root_sha256": replay._sha256_json(preimage),
        "runtime": deepcopy(schema["runtime_binding"]),
        "replayer": replayer_identity,
        "status": "all-execution-bindings-authenticated",
    }


def _synthetic_result(monkeypatch: pytest.MonkeyPatch) -> dict[str, object]:
    schema = replay.pilot_dependency_vector_negative_replay_schema(ROOT)
    observations = _synthetic_observations()
    retained_baselines = replay._retained_baseline_expectations(_candidate())
    by_key = {
        (row["name"], row["omitted_dependency"]): row
        for row in observations
    }

    def baseline(spec: TheoremSpec, _hooks: object) -> dict[str, object]:
        return {
            **deepcopy(retained_baselines[spec.name]),
            "dependencies": list(spec.dependencies),
            "name": spec.name,
            "script_sha256": _lf_sha(tuple(spec.script)),
            "status": "full-vector-baseline-kernel-accepted",
        }

    def task(
        replay_task: replay.NegativeReplayTask,
        _spec: TheoremSpec,
        _hooks: object,
    ) -> dict[str, object]:
        return deepcopy(
            by_key[(replay_task.theorem_name, replay_task.omitted_dependency)]
        )

    hooks = replace(
        replay.DEFAULT_NEGATIVE_REPLAY_HOOKS,
        baseline_runner=baseline,
        task_runner=task,
    )
    environment = _synthetic_environment(schema)
    monkeypatch.setattr(
        replay,
        "authenticate_negative_replay_environment",
        lambda _root, *, hooks, replayer_identity=None: deepcopy(environment),
    )
    return replay.build_pilot_dependency_vector_negative_replay(
        ROOT, hooks=hooks
    )


def _reroot_result(value: dict[str, object]) -> None:
    body = {
        key: item
        for key, item in value.items()
        if key not in {"root_preimage", "root_sha256"}
    }
    value["root_preimage"] = {
        "format": replay.NEGATIVE_REPLAY_ROOT_PREIMAGE_FORMAT,
        "payload": body,
        "v": 1,
    }
    value["root_sha256"] = replay._sha256_json(value["root_preimage"])


def _refresh_result_receipts(value: dict[str, object]) -> None:
    baselines = value["baseline_records"]
    observations = value["negative_observation_records"]
    for record in (*baselines, *observations):
        record["record_sha256"] = replay._record_hash(record)

    offset = 0
    for theorem, baseline, (_index, name) in zip(
        value["theorems"], baselines, EXPECTED_ROOTS, strict=True
    ):
        count = len(EXPECTED_DIRECT[name])
        theorem["baseline"] = deepcopy(baseline)
        theorem["negative_observations"] = deepcopy(
            observations[offset : offset + count]
        )
        theorem["negative_observation_count"] = count
        theorem["record_sha256"] = replay._record_hash(theorem)
        offset += count

    value["baselines"] = replay._records_bundle(
        baselines, kind="full-vector-baselines"
    )
    value["negative_observations"] = replay._records_bundle(
        observations,
        kind="independent-shared-root-body-negative-replays",
    )
    value["theorem_records"] = replay._records_bundle(
        value["theorems"], kind="theorems"
    )

    join = value["retained_route_join"]
    join_by_key = {
        (row["name"], row["omitted_dependency"]): row
        for row in join["joins"]
    }
    ordered_joins = []
    for observation in observations:
        row = join_by_key[(observation["name"], observation["omitted_dependency"])]
        row["fresh_observation_record_sha256"] = observation["record_sha256"]
        ordered_joins.append(row)
    join["joins"] = ordered_joins
    join["preimage"] = {
        "format": (
            "peano-hydra-library-pilot-dependency-vector-negative-replay-"
            "retained-route-join-preimage"
        ),
        "joins": deepcopy(ordered_joins),
        "v": 1,
    }
    join["root_sha256"] = replay._sha256_json(join["preimage"])
    _reroot_result(value)


def test_schema_is_canonical_and_freezes_exact_counts_inputs_and_runtime() -> None:
    raw = SCHEMA_PATH.read_bytes()
    schema = replay.pilot_dependency_vector_negative_replay_schema(ROOT)
    assert raw == replay.canonical_negative_replay_bytes(
        schema, limit=replay.MAX_SCHEMA_BYTES
    )
    identity = replay.pilot_dependency_vector_negative_replay_schema_identity(
        ROOT
    )
    assert identity["artifact_sha256"] == _sha(raw)
    assert identity["bytes"] == len(raw)
    assert identity["semantic_sha256"] == (
        replay.NEGATIVE_REPLAY_SCHEMA_SEMANTIC_SHA256
    )

    constants = schema["constants"]
    assert constants == {
        "expected_baseline_count": 3,
        "expected_independent_observation_count": 22,
        "expected_retained_route_row_count": 44,
        "logic_mode": "intuitionistic",
        "retained_public_graph_edges": 1_038,
        "routes": [
            "readable-direct-closure",
            "proposed-layered-closure-construction",
        ],
    }
    assert schema["runtime_binding"] == {
        "byteorder": "little",
        "cache_tag": "cpython-312",
        "implementation": "cpython",
        "int_max_str_digits": 4_300,
        "major": 3,
        "micro": 12,
        "minor": 12,
        "optimize": 0,
        "platform_prefix": "linux",
        "safe_path": True,
    }
    assert schema["independence_contract"] == {
        "a2.3b_producer_imported": False,
        "a2.3b_verifier_imported": False,
        "compile_candidate_body_called": False,
        "fresh_process_required": True,
        "independent_wrapper_implementation": True,
        "lower_level_call_sequence": [
            "replay_target",
            "start",
            "apply_tactic:intro",
            "apply_tactic:script-command",
            "ProofState/invariants_ok:after-every-success",
            "checked_final:baseline-only",
        ],
        "route_specific_assemblers_called": False,
        "shared_engine_with_a2.3b": True,
        "shared_intuitionistic_kernel": True,
    }

    fixed = schema["fixed_inputs"]
    for row in fixed.values():
        path = ROOT / row["path"]
        raw_input = path.read_bytes()
        assert len(raw_input) == row["bytes"]
        assert _sha(raw_input) == row["artifact_sha256"]
    assert fixed["a2.3b_candidate"]["root_sha256"] == (
        "21f4c7a06dd8b1abf01d8eddd8c1942733f0955141ba682d53229078e15d5e85"
    )
    assert fixed["a2.3b_verification"]["root_sha256"] == (
        "ef0dfac8552789bb4dc0e6694a1704c63a8781a93a1f0d9117c6e5c6babcfbd1"
    )


def test_schema_freezes_three_baselines_22_diagnostics_and_two_to_one_join() -> None:
    schema = replay.pilot_dependency_vector_negative_replay_schema(ROOT)
    theorem_rows = schema["required_theorems"]
    assert tuple((row["index"], row["name"]) for row in theorem_rows) == (
        EXPECTED_ROOTS
    )
    tasks = []
    for row in theorem_rows:
        name = row["name"]
        assert tuple(row["dependencies"]) == EXPECTED_DIRECT[name]
        assert row["script_command_count"] == EXPECTED_COMMAND_COUNTS[name]
        assert row["script_sha256"] == EXPECTED_SCRIPT_SHA256[name]
        assert tuple(task["omitted_dependency"] for task in row["tasks"]) == (
            tuple(reversed(EXPECTED_DIRECT[name]))
        )
        for task in row["tasks"]:
            omitted = task["omitted_dependency"]
            assert task["expected_command_index"] == (
                EXPECTED_FAILURE_INDEX[(name, omitted)]
            )
            assert omitted in task["expected_command"]
            assert task["expected_message"] == (
                f"unknown hypothesis {omitted!r}."
            )
            tasks.append((name, omitted))
    assert len(tasks) == len(set(tasks)) == 22

    algorithm = " ".join(schema["algorithm"]["join"]).lower()
    assert "22" in algorithm
    assert "two" in algorithm
    assert "two registered route rows" in algorithm
    boundary = schema["claim_boundary"]
    assert "22" in boundary["scope"]
    assert "44" in boundary["scope"]
    assert "two-to-one" in boundary["scope"]


def test_source_only_and_completed_result_contracts_keep_claims_narrow() -> None:
    schema = replay.pilot_dependency_vector_negative_replay_schema(ROOT)
    source_only = schema["result_contract"]["source_only"]
    assert source_only == {
        "campaign_executed": False,
        "negative_observations_independently_verified": False,
        "result_exists": False,
        "route_rejections_independently_verified": False,
        "status": "source-only-no-campaign",
    }
    completed = schema["result_contract"]["completed_campaign"]
    assert completed == {
        "baseline_count": 3,
        "campaign_executed": True,
        "negative_observations_independently_verified": True,
        "result_exists": True,
        "retained_route_row_count": 44,
        "route_rejections_independently_verified": False,
        "shared_observation_count": 22,
        "status": "passed",
    }
    false_fields = set(schema["required_false_result_fields"])
    assert {
        "a2_complete",
        "bounded_three_root_vector_audit_complete",
        "dependency_necessity_established",
        "dependency_vectors_complete",
        "minimality_claim",
        "optimized_best_known",
        "optimized_vector_independently_audited",
        "proof_authority",
        "public_graph_applied",
        "publication_authority",
        "publication_union_complete",
        "route_rejections_independently_verified",
        "theorem_admission_authority",
        "vector_optimizer_executed",
    }.issubset(false_fields)
    assert "negative_observations_independently_verified" not in false_fields


def test_schema_pins_exact_live_source_vector_and_lower_level_callables() -> None:
    schema = replay.pilot_dependency_vector_negative_replay_schema(ROOT)
    sources = schema["implementation_sources"]
    assert len(sources) == len({row["path"] for row in sources}) == 39
    assert all(
        _sha((ROOT / row["path"]).read_bytes()) == row["sha256"]
        for row in sources
    )
    assert replay._sha256_json(sources) == (
        schema["implementation_source_root_sha256"]
    )
    assert schema["qualified_callables"] == {
        "apply_tactic": "peano_lab.engine.tactics.apply_tactic",
        "checked_final": "peano_lab.engine.tactics.checked_final",
        "formula_encode": "peano_lab.kernel.artifact_codec.encode_formula",
        "proof_encode": "peano_lab.kernel.artifact_codec.encode_proof",
        "proof_metrics": "peano_lab.engine.state.proof_resource_metrics",
        "proof_state_invariants": "peano_lab.engine.state.invariants_ok",
        "proof_state_type": "peano_lab.engine.state.ProofState",
        "replay_target": "peano_lab.library.theorems.replay_target",
        "start": "peano_lab.engine.state.start",
    }


def test_source_protocol_has_22_tasks_and_no_campaign_or_authority() -> None:
    source = replay.pilot_dependency_vector_negative_replay_source_protocol(ROOT)
    assert source["status"] == "source-only-no-campaign"
    assert source["campaign_executed"] is False
    assert source["result_exists"] is False
    assert source["negative_observations_independently_verified"] is False
    assert source["route_rejections_independently_verified"] is False
    assert source["source_protocol_frozen"] is True
    assert source["implementation_sources_authenticated"] is False
    assert source["predecessor_inputs_authenticated"] is False
    assert len(source["task_preimage"]["tasks"]) == 22
    assert source["task_root_sha256"] == replay._sha256_json(
        source["task_preimage"], limit=replay.MAX_SCHEMA_BYTES
    )
    assert source["root_sha256"] == replay._sha256_json(
        source["root_preimage"], limit=replay.MAX_SCHEMA_BYTES
    )
    for field in replay.GLOBAL_FALSE_FIELDS:
        assert source[field] is False, field


def test_implementation_source_callable_and_runtime_drift_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    schema = replay.pilot_dependency_vector_negative_replay_schema(ROOT)
    original_reader = replay._safe_regular_bytes
    first_path = ROOT / schema["implementation_sources"][0]["path"]

    def corrupt(path: Path, *, label: str, limit: int) -> bytes:
        raw = original_reader(path, label=label, limit=limit)
        return raw + b"\n" if path == first_path else raw

    with monkeypatch.context() as patcher:
        patcher.setattr(replay, "_safe_regular_bytes", corrupt)
        with pytest.raises(
            replay.LibraryPilotDependencyVectorNegativeReplayError,
            match="implementation source .* drifted",
        ):
            replay._authenticate_implementation_sources(ROOT, schema)

    for forged in (
        replace(
            replay.DEFAULT_NEGATIVE_REPLAY_HOOKS,
            apply_tactic=lambda *_args: None,
        ),
        replace(
            replay.DEFAULT_NEGATIVE_REPLAY_HOOKS,
            invariants_ok=lambda _state: True,
        ),
        replace(
            replay.DEFAULT_NEGATIVE_REPLAY_HOOKS,
            proof_state_type=object,
        ),
    ):
        with pytest.raises(
            replay.LibraryPilotDependencyVectorNegativeReplayError,
            match="hook|callable|registered",
        ):
            replay._require_production_hooks(ROOT, schema, forged)

    wrong_runtime = replace(
        replay.DEFAULT_NEGATIVE_REPLAY_HOOKS,
        runtime_identity=lambda: {
            **schema["runtime_binding"],
            "micro": schema["runtime_binding"]["micro"] + 1,
        },
    )
    with monkeypatch.context() as patcher:
        patcher.setattr(
            replay,
            "pilot_dependency_vector_negative_replay_schema",
            lambda _root: schema,
        )
        patcher.setattr(
            replay,
            "_authenticate_implementation_sources",
            lambda _root, _schema: [],
        )
        patcher.setattr(
            replay,
            "_require_production_hooks",
            lambda _root, _schema, _hooks: {},
        )
        patcher.setattr(
            replay,
            "_authenticate_fixed_inputs",
            lambda _root, _schema: {},
        )
        for name in (
            "peano_lab.library.candidate_validation",
            "training.peano_hydra.library_pilot_dependency_vector_audit",
            "training.peano_hydra.library_pilot_dependency_vector_audit_verifier",
        ):
            patcher.delitem(sys.modules, name, raising=False)
        with pytest.raises(
            replay.LibraryPilotDependencyVectorNegativeReplayError,
            match="runtime identity drifted",
        ):
            replay.authenticate_negative_replay_environment(
                ROOT, hooks=wrong_runtime
            )


def test_public_surface_has_no_admission_publication_or_optimizer_entrypoint() -> None:
    exported = set(replay.__all__)
    assert {
        "NegativeReplayHooks",
        "NegativeReplayTask",
        "build_pilot_dependency_vector_negative_replay",
        "join_retained_route_rows",
        "verify_expected_tactic_rejection",
    }.issubset(exported)
    assert not {
        name
        for name in exported
        if any(
            token in name.lower()
            for token in ("admit", "publish", "minimal", "best_known", "optimize")
        )
    }


def test_canonical_json_and_strict_decoder_fail_closed() -> None:
    value = {"z": [1, False, None], "a": "λ"}
    assert replay.canonical_negative_replay_bytes(value) == (
        b'{\n  "a": "\\u03bb",\n  "z": [\n    1,\n    false,\n    null\n  ]\n}\n'
    ).replace(b"\\u03bb", "λ".encode("utf-8"))
    assert replay._decode_document(
        replay.canonical_negative_replay_bytes(value),
        label="synthetic",
        limit=1_024,
    ) == value

    for raw in (
        b'{"duplicate":1,"duplicate":2}\n',
        b'{"float":1.0}\n',
        b'{"constant":NaN}\n',
        b'{"constant":Infinity}\n',
        b'[]\n',
    ):
        with pytest.raises(
            replay.LibraryPilotDependencyVectorNegativeReplayError,
            match="decode|JSON|object|byte limit",
        ):
            replay._decode_document(raw, label="synthetic", limit=1_024)
    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="byte limit",
    ):
        replay._decode_document(b"{}", label="synthetic", limit=1)


def test_regular_file_reader_rejects_symlink_fifo_and_oversize(
    tmp_path: Path,
) -> None:
    actual = tmp_path / "actual.json"
    actual.write_bytes(b"{}\n")
    linked = tmp_path / "linked.json"
    try:
        linked.symlink_to(actual)
    except OSError:
        pytest.skip("symlinks are unavailable")
    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="symlink|regular|link",
    ):
        replay._safe_regular_bytes(linked, label="synthetic", limit=1_024)

    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    nested = real_parent / "nested.json"
    nested.write_bytes(b"{}\n")
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="ancestor|link|directory",
    ):
        replay._safe_regular_bytes(
            linked_parent / "nested.json", label="synthetic", limit=1_024
        )

    oversized = tmp_path / "oversized.json"
    oversized.write_bytes(b"x" * 1_025)
    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="bounded|limit",
    ):
        replay._safe_regular_bytes(oversized, label="synthetic", limit=1_024)

    if not hasattr(os, "mkfifo") or not hasattr(os, "O_NONBLOCK"):
        return
    fifo = tmp_path / "transport.fifo"
    os.mkfifo(fifo)
    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="regular",
    ):
        replay._safe_regular_bytes(fifo, label="synthetic", limit=1_024)


def test_exact_tactic_rejection_records_only_fresh_diagnostic() -> None:
    task = _synthetic_task()
    receipt = replay.verify_expected_tactic_rejection(
        TacticError(task.expected_message), task=task
    )
    assert receipt == {
        "cause_type": "TacticError",
        "command": "specialize drop n",
        "command_index": 1,
        "diagnostic": (
            "candidate 'fixture_root' failed at command 1: "
            "'specialize drop n': unknown hypothesis 'drop'."
        ),
        "kind": "exact-recipe-rejection",
        "message": "unknown hypothesis 'drop'.",
        "message_source": "fresh-a2.3c-lower-level-replay",
        "omitted_dependency": "drop",
        "phase": "command",
        "retained_message_available": False,
    }


def test_tactic_limit_subclass_internal_and_diagnostic_drift_are_unknown() -> None:
    task = _synthetic_task()

    class ForeignTacticError(TacticError):
        pass

    errors = (
        TacticLimit(task.expected_message),
        ForeignTacticError(task.expected_message),
        RuntimeError(task.expected_message),
        TacticError("unknown hypothesis 'keep'."),
        TacticError("unknown hypothesis 'drop'"),
    )
    for error in errors:
        with pytest.raises(
            replay.LibraryPilotDependencyVectorNegativeReplayError,
            match="resource|exact TacticError|diagnostic",
        ):
            replay.verify_expected_tactic_rejection(error, task=task)


def test_lower_level_baseline_executes_full_prefix_and_checked_final() -> None:
    spec = _synthetic_spec()
    events: list[tuple[str, str]] = []

    def apply(state: object, tactic: str, args: str) -> object:
        events.append((tactic, args))
        return state

    receipt = replay._run_baseline(spec, _driver_hooks(apply))
    assert events == [
        ("intro", "keep"),
        ("intro", "drop"),
        ("intro", "n"),
        ("specialize", "drop n"),
        ("use", "keep"),
    ]
    assert receipt["status"] == "full-vector-baseline-kernel-accepted"
    assert receipt["dependencies"] == ["keep", "drop"]
    assert receipt["dependency_count"] == 2
    assert receipt["command_count"] == 3
    assert receipt["script_sha256"] == _lf_sha(spec.script)
    assert receipt["proof_structure"] == {
        "depth": 1,
        "edges": 0,
        "nodes": 1,
        "objects": 1,
        "reused_objects": 0,
    }


def test_lower_level_negative_driver_requires_successful_prefix_and_exact_failure() -> None:
    spec = _synthetic_spec()
    task = _synthetic_task()
    events: list[tuple[str, str]] = []

    def apply(state: object, tactic: str, args: str) -> object:
        events.append((tactic, args))
        if (tactic, args) == ("specialize", "drop n"):
            raise TacticError(task.expected_message)
        return state

    record = replay._run_negative_task(task, spec, _driver_hooks(apply))
    assert events == [
        ("intro", "keep"),
        ("intro", "n"),
        ("specialize", "drop n"),
    ]
    assert record["outcome"] == "exact-shared-root-body-rejected"
    assert record["prefix_command_count"] == 1
    assert record["full_dependencies"] == ["keep", "drop"]
    assert record["trial_dependencies"] == ["keep"]
    assert record["failure"]["message_source"] == (
        "fresh-a2.3c-lower-level-replay"
    )
    assert record["record_sha256"] == replay._sha256_json(
        {key: value for key, value in record.items() if key != "record_sha256"},
        limit=replay.MAX_SCHEMA_BYTES,
    )


@pytest.mark.parametrize(
    ("failure_point", "error", "pattern"),
    (
        ("intro n", TacticError("unknown hypothesis 'drop'."), "before"),
        (
            "specialize drop n",
            TacticLimit("unknown hypothesis 'drop'."),
            "resource",
        ),
        (
            "specialize drop n",
            RuntimeError("unknown hypothesis 'drop'."),
            "exact TacticError",
        ),
        (
            "specialize drop n",
            TacticError("unknown hypothesis 'keep'."),
            "diagnostic",
        ),
    ),
)
def test_lower_level_negative_driver_aborts_unknown_error_outcomes(
    failure_point: str,
    error: BaseException,
    pattern: str,
) -> None:
    spec = _synthetic_spec()
    task = _synthetic_task()

    def apply(state: object, tactic: str, args: str) -> object:
        command = tactic if not args else f"{tactic} {args}"
        if command == failure_point:
            raise error
        return state

    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match=pattern,
    ):
        replay._run_negative_task(task, spec, _driver_hooks(apply))


def test_accepted_registered_omission_aborts_instead_of_becoming_evidence() -> None:
    spec = _synthetic_spec()
    task = _synthetic_task()
    hooks = _driver_hooks(lambda state, _tactic, _args: state)
    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="accepted|failure command",
    ):
        replay._run_negative_task(task, spec, hooks)


def test_negative_driver_rejects_wrong_initial_state_type_and_target_drift() -> None:
    spec = _synthetic_spec()
    task = _synthetic_task()
    base = _driver_hooks(lambda state, _tactic, _args: state)
    wrong_type = replace(
        base,
        start=lambda target: SimpleNamespace(target=target, history=()),
        invariants_ok=lambda _state: True,
    )
    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="setup is unknown",
    ):
        replay._run_negative_task(task, spec, wrong_type)

    foreign_target = Eq(Zero(), Succ(Zero()))
    target_drift = replace(
        base,
        start=lambda target: replace(start(target), target=foreign_target),
    )
    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="setup is unknown",
    ):
        replay._run_negative_task(task, spec, target_drift)


def test_negative_driver_rejects_discontinuous_successful_prefix_state() -> None:
    spec = _synthetic_spec()
    task = _synthetic_task()

    def apply(state: ProofState, tactic: str, args: str) -> object:
        if (tactic, args) == ("intro", "n"):
            return record_step(state, state, "wrong-tactic", args)
        return state

    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="malformed|discontinuous|target-drifted",
    ):
        replay._run_negative_task(task, spec, _driver_hooks(apply))


@pytest.mark.parametrize("mutation", ("target", "history"))
def test_expected_error_after_mutating_current_state_is_unknown(
    mutation: str,
) -> None:
    spec = _synthetic_spec()
    task = _synthetic_task()

    def apply(state: ProofState, tactic: str, args: str) -> object:
        if (tactic, args) == ("specialize", "drop n"):
            if mutation == "target":
                object.__setattr__(state, "target", Eq(Zero(), Succ(Zero())))
            else:
                object.__setattr__(state, "history", [])
            raise TacticError(task.expected_message)
        return state

    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="malformed|target-drifted",
    ):
        replay._run_negative_task(task, spec, _driver_hooks(apply))


def test_invariant_failure_at_registered_error_cannot_become_evidence() -> None:
    spec = _synthetic_spec()
    task = _synthetic_task()
    failed = False

    def apply(state: ProofState, tactic: str, args: str) -> object:
        nonlocal failed
        if (tactic, args) == ("specialize", "drop n"):
            failed = True
            raise TacticError(task.expected_message)
        return state

    hooks = replace(
        _driver_hooks(apply),
        invariants_ok=lambda state: invariants_ok(state) and not failed,
    )
    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="malformed|target-drifted",
    ):
        replay._run_negative_task(task, spec, hooks)


def test_baseline_internal_resource_or_unsupported_evidence_is_unknown() -> None:
    spec = _synthetic_spec()

    def resource(_state: object, _tactic: str, _args: str) -> object:
        raise TacticLimit("synthetic limit")

    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="baseline is unknown",
    ):
        replay._run_baseline(spec, _driver_hooks(resource))

    hooks = replace(
        _driver_hooks(lambda state, _tactic, _args: state),
        proof_resource_metrics=lambda _proof: (True, 1, 1, 1, 1),
    )
    with pytest.raises(
        replay.LibraryPilotDependencyVectorNegativeReplayError,
        match="unsupported evidence",
    ):
        replay._run_baseline(spec, hooks)


def test_schedule_rejects_vector_order_script_and_diagnostic_mutations() -> None:
    spec = _synthetic_spec()
    registrations = [
        {
            "attempt_index": 0,
            "expected_command": "specialize drop n",
            "expected_command_index": 1,
            "expected_message": "unknown hypothesis 'drop'.",
            "omitted_dependency": "drop",
        },
        {
            "attempt_index": 1,
            "expected_command": "use keep",
            "expected_command_index": 2,
            "expected_message": "unknown hypothesis 'keep'.",
            "omitted_dependency": "keep",
        },
    ]
    tasks = replay.single_omission_replay_tasks(
        spec.name, 7, spec.dependencies, spec.script, registrations
    )
    assert tuple(task.omitted_dependency for task in tasks) == ("drop", "keep")

    mutations: list[tuple[object, object, object]] = []
    mutations.append((list(spec.dependencies), spec.script, registrations))
    mutations.append((("keep", "keep"), spec.script, registrations))
    mutations.append((tuple(reversed(spec.dependencies)), spec.script, registrations))
    mutations.append(
        (
            spec.dependencies,
            (spec.script[0], "refl", spec.script[2]),
            registrations,
        )
    )
    reordered = deepcopy(registrations)
    reordered.reverse()
    mutations.append((spec.dependencies, spec.script, reordered))
    wrong_index = deepcopy(registrations)
    wrong_index[0]["expected_command_index"] = 0
    mutations.append((spec.dependencies, spec.script, wrong_index))
    wrong_command = deepcopy(registrations)
    wrong_command[0]["expected_command"] = "refl"
    mutations.append((spec.dependencies, spec.script, wrong_command))
    wrong_message = deepcopy(registrations)
    wrong_message[0]["expected_message"] = "unknown hypothesis 'keep'."
    mutations.append((spec.dependencies, spec.script, wrong_message))

    for dependencies, script, changed_registrations in mutations:
        with pytest.raises(
            replay.LibraryPilotDependencyVectorNegativeReplayError,
            match="malformed|drifted",
        ):
            replay.single_omission_replay_tasks(
                spec.name,
                7,
                dependencies,
                script,
                changed_registrations,
            )


def test_live_registered_schedule_rejects_root_vector_script_and_digest_drift() -> None:
    schema = replay.pilot_dependency_vector_negative_replay_schema(ROOT)
    specs, tasks = replay._registered_specs_and_tasks(schema)
    assert tuple((spec.name, len(spec.script)) for spec in specs) == (
        ("odd_add_odd", 10),
        ("finite_bounded_injective_surjective", 178),
        ("beta_product_swap_last_invariant", 102),
    )
    assert len(tasks) == 22

    mutations: list[dict[str, object]] = []
    reordered = deepcopy(schema)
    reordered["required_theorems"][0], reordered["required_theorems"][1] = (
        reordered["required_theorems"][1],
        reordered["required_theorems"][0],
    )
    mutations.append(reordered)
    wrong_vector = deepcopy(schema)
    wrong_vector["required_theorems"][0]["dependencies"].reverse()
    mutations.append(wrong_vector)
    wrong_script_digest = deepcopy(schema)
    wrong_script_digest["required_theorems"][0]["script_sha256"] = "0" * 64
    mutations.append(wrong_script_digest)
    wrong_statement_digest = deepcopy(schema)
    wrong_statement_digest["required_theorems"][0]["statement_sha256"] = (
        "1" * 64
    )
    mutations.append(wrong_statement_digest)
    wrong_task_order = deepcopy(schema)
    wrong_task_order["required_theorems"][0]["tasks"].reverse()
    mutations.append(wrong_task_order)
    wrong_command = deepcopy(schema)
    wrong_command["required_theorems"][0]["tasks"][0][
        "expected_command"
    ] = "refl"
    mutations.append(wrong_command)

    for changed in mutations:
        with pytest.raises(
            replay.LibraryPilotDependencyVectorNegativeReplayError,
            match="registered|drifted|task|theorem|vector",
        ):
            replay._registered_specs_and_tasks(changed)


def test_retained_route_join_is_exactly_44_rows_to_22_shared_observations() -> None:
    candidate = _candidate()
    observations = _synthetic_observations(candidate)
    joined = replay.join_retained_route_rows(candidate, observations)
    assert joined["status"] == "exact-44-route-rows-joined-two-to-one"
    assert joined["fresh_observation_count"] == 22
    assert joined["retained_route_row_count"] == 44
    assert joined["route_rows_per_observation"] == 2
    assert len(joined["joins"]) == 22
    assert all(row["route_row_count"] == 2 for row in joined["joins"])
    assert joined["root_sha256"] == replay._sha256_json(joined["preimage"])
    assert {
        (row["name"], row["omitted_dependency"]) for row in joined["joins"]
    } == {
        (row["name"], row["omitted_dependency"]) for row in observations
    }


def test_retained_join_rejects_vector_order_script_digest_and_root_mutations() -> None:
    candidate = _candidate()
    observations = _synthetic_observations(candidate)
    candidate_mutations: list[dict[str, object]] = []

    wrong_root = deepcopy(candidate)
    wrong_root["root_sha256"] = "0" * 64
    candidate_mutations.append(wrong_root)
    wrong_theorem_root = deepcopy(candidate)
    wrong_theorem_root["theorem_records"]["root_sha256"] = "1" * 64
    candidate_mutations.append(wrong_theorem_root)
    wrong_routes = deepcopy(candidate)
    wrong_routes["theorems"][0]["routes"].reverse()
    candidate_mutations.append(wrong_routes)
    wrong_attempt_order = deepcopy(candidate)
    wrong_attempt_order["theorems"][0]["routes"][0]["attempts"].reverse()
    candidate_mutations.append(wrong_attempt_order)
    wrong_vector = deepcopy(candidate)
    wrong_vector["theorems"][0]["routes"][0]["attempts"][0][
        "attempted_dependencies"
    ].reverse()
    candidate_mutations.append(wrong_vector)
    wrong_script = deepcopy(candidate)
    wrong_script["theorems"][0]["routes"][0]["attempts"][0][
        "script_sha256"
    ] = "2" * 64
    candidate_mutations.append(wrong_script)
    wrong_shared_digest = deepcopy(candidate)
    wrong_shared_digest["theorems"][0]["routes"][0]["attempts"][0][
        "shared_root_body_observation_sha256"
    ] = "3" * 64
    candidate_mutations.append(wrong_shared_digest)
    missing_route = deepcopy(candidate)
    missing_route["theorems"][0]["routes"].pop()
    candidate_mutations.append(missing_route)

    for changed in candidate_mutations:
        with pytest.raises(
            replay.LibraryPilotDependencyVectorNegativeReplayError,
            match="identity|route|row|observation|attempt|drifted",
        ):
            replay.join_retained_route_rows(changed, observations)

    observation_mutations: list[list[dict[str, object]]] = []
    reordered = deepcopy(observations)
    reordered[0], reordered[1] = reordered[1], reordered[0]
    observation_mutations.append(reordered)
    duplicate = deepcopy(observations)
    duplicate[1] = deepcopy(duplicate[0])
    observation_mutations.append(duplicate)
    wrong_record = deepcopy(observations)
    wrong_record[0]["record_sha256"] = "4" * 64
    observation_mutations.append(wrong_record)
    wrong_failure = deepcopy(observations)
    wrong_failure[0]["failure"]["command_index"] += 1
    wrong_failure[0]["record_sha256"] = replay._record_hash(wrong_failure[0])
    observation_mutations.append(wrong_failure)
    wrong_trial = deepcopy(observations)
    wrong_trial[0]["trial_dependencies"].reverse()
    wrong_trial[0]["record_sha256"] = replay._record_hash(wrong_trial[0])
    observation_mutations.append(wrong_trial)

    for changed in observation_mutations:
        with pytest.raises(
            replay.LibraryPilotDependencyVectorNegativeReplayError,
            match="observation|route|row|count|join|drifted",
        ):
            replay.join_retained_route_rows(candidate, changed)


def test_synthetic_completed_result_deeply_validates_without_real_campaign(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    result = _synthetic_result(monkeypatch)
    assert replay.validate_pilot_dependency_vector_negative_replay(
        result, ROOT
    ) == result
    assert result["status"] == "passed"
    assert result["campaign_executed"] is True
    assert result["negative_observations_independently_verified"] is True
    assert result["route_rejections_independently_verified"] is False
    assert result["environment"]["replayer"] == (
        replay._controlled_replayer_identity(ROOT)
    )
    assert result["aggregate"] == {
        "full_vector_baseline_count": 3,
        "independent_shared_observation_count": 22,
        "retained_route_row_count": 44,
        "route_rows_per_shared_observation": 2,
        "theorem_count": 3,
    }
    for field in replay.GLOBAL_FALSE_FIELDS:
        assert result[field] is False, field
    assert all(
        theorem[field] is False
        for theorem in result["theorems"]
        for field in replay.GLOBAL_FALSE_FIELDS
    )


def test_fully_rerooted_nested_semantic_forgeries_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid = _synthetic_result(monkeypatch)
    for label in (
        "baseline-vector",
        "observation-message",
        "observation-order",
        "observation-extra-field",
        "theorem-claim",
        "join-cross-binding",
        "environment-runtime",
        "environment-replayer",
        "predecessor-root",
        "top-level-claim",
    ):
        forged = deepcopy(valid)
        if label == "baseline-vector":
            forged["baseline_records"][0]["dependencies"].reverse()
            _refresh_result_receipts(forged)
        elif label == "observation-message":
            observation = forged["negative_observation_records"][0]
            observation["failure"]["message"] = (
                "unknown hypothesis 'different_name'."
            )
            observation["failure"]["diagnostic"] = (
                observation["failure"]["diagnostic"].replace(
                    "unknown hypothesis 'add_comm'.",
                    "unknown hypothesis 'different_name'.",
                )
            )
            _refresh_result_receipts(forged)
        elif label == "observation-order":
            observations = forged["negative_observation_records"]
            observations[0], observations[1] = observations[1], observations[0]
            _refresh_result_receipts(forged)
        elif label == "observation-extra-field":
            forged["negative_observation_records"][0]["extra"] = False
            _refresh_result_receipts(forged)
        elif label == "theorem-claim":
            theorem = forged["theorems"][0]
            theorem["minimality_claim"] = True
            theorem["record_sha256"] = replay._record_hash(theorem)
            forged["theorem_records"] = replay._records_bundle(
                forged["theorems"], kind="theorems"
            )
            _reroot_result(forged)
        elif label == "join-cross-binding":
            join = forged["retained_route_join"]
            join["joins"][0]["retained_shared_observation_sha256"] = (
                join["joins"][1]["retained_shared_observation_sha256"]
            )
            join["preimage"] = {
                **join["preimage"],
                "joins": deepcopy(join["joins"]),
            }
            join["root_sha256"] = replay._sha256_json(join["preimage"])
            _reroot_result(forged)
        elif label == "environment-runtime":
            environment = forged["environment"]
            environment["runtime"]["micro"] += 1
            environment["preimage"]["runtime"] = deepcopy(
                environment["runtime"]
            )
            environment["root_sha256"] = replay._sha256_json(
                environment["preimage"]
            )
            _reroot_result(forged)
        elif label == "environment-replayer":
            environment = forged["environment"]
            environment["replayer"]["sha256"] = "e" * 64
            environment["preimage"]["replayer"] = deepcopy(
                environment["replayer"]
            )
            environment["root_sha256"] = replay._sha256_json(
                environment["preimage"]
            )
            _reroot_result(forged)
        elif label == "predecessor-root":
            forged["predecessors"]["a2.3b_candidate"]["root_sha256"] = (
                "f" * 64
            )
            _reroot_result(forged)
        else:
            forged["bounded_three_root_vector_audit_complete"] = True
            _reroot_result(forged)

        with pytest.raises(
            replay.LibraryPilotDependencyVectorNegativeReplayError,
            match=(
                "baseline|observation|theorem|join|environment|input binding|"
                "forbidden claim|semantics|partition|record"
            ),
        ):
            replay.validate_pilot_dependency_vector_negative_replay(
                forged, ROOT
            )


def test_cli_default_worker_describes_source_only_and_never_builds_or_writes(
    monkeypatch: pytest.MonkeyPatch,
    capfd: pytest.CaptureFixture[str],
) -> None:
    cli = _load_cli()
    events: list[str] = []
    source = {"campaign_executed": False, "status": "source-only-no-campaign"}
    module = SimpleNamespace(
        build_pilot_dependency_vector_negative_replay=lambda _root: events.append(
            "build"
        ),
        canonical_negative_replay_bytes=replay.canonical_negative_replay_bytes,
        pilot_dependency_vector_negative_replay_source_protocol=(
            lambda _root: deepcopy(source)
        ),
    )
    monkeypatch.setattr(cli, "_consume_worker_capability", lambda: None)
    monkeypatch.setattr(cli, "_require_controlled_worker", lambda: None)
    monkeypatch.setattr(cli, "_load_replayer", lambda: (module, {}))
    monkeypatch.setattr(
        cli,
        "_publish_create_only",
        lambda *_args: events.append("publish"),
    )
    args = cli._parser().parse_args([])
    assert cli._worker(args) == 0
    assert events == []
    assert json.loads(capfd.readouterr().out) == source


def test_cli_publish_is_create_only_regular_exact_and_race_safe(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    raw = b'{"fixture":true}\n'
    destination = tmp_path / "result.json"
    cli._publish_create_only(destination, raw)
    metadata = destination.lstat()
    assert stat.S_ISREG(metadata.st_mode)
    assert not stat.S_ISLNK(metadata.st_mode)
    assert stat.S_IMODE(metadata.st_mode) == 0o644
    assert destination.read_bytes() == raw
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="already exists",
    ):
        cli._publish_create_only(destination, b"replacement\n")
    assert destination.read_bytes() == raw

    actual_parent = tmp_path / "actual-parent"
    actual_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(actual_parent, target_is_directory=True)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="symlink|directory|parent",
    ):
        cli._publish_create_only(linked_parent / "forbidden.json", raw)
    assert not (actual_parent / "forbidden.json").exists()

    raced = tmp_path / "raced.json"
    original_link = cli.os.link

    def race(source: object, target: object, **kwargs: object) -> object:
        Path(target).write_bytes(b"racer-won\n")
        return original_link(source, target, **kwargs)

    monkeypatch.setattr(cli.os, "link", race)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="raced|already exists",
    ):
        cli._publish_create_only(raced, raw)
    assert raced.read_bytes() == b"racer-won\n"
    assert not list(tmp_path.glob(".a23c-negative-replay-*.tmp"))


def test_cli_staged_name_swap_cannot_chmod_or_publish_a_symlink_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    destination = tmp_path / "result.json"
    victim = tmp_path / "victim.txt"
    victim.write_bytes(b"untouched\n")
    victim.chmod(0o600)
    staged: list[Path] = []
    original_mkstemp = cli.tempfile.mkstemp
    original_fchmod = cli.os.fchmod

    def tracked_mkstemp(*args: object, **kwargs: object) -> tuple[int, str]:
        descriptor, name = original_mkstemp(*args, **kwargs)
        staged.append(Path(name))
        return descriptor, name

    def swap_before_fchmod(descriptor: int, mode: int) -> None:
        assert staged
        staged[0].unlink()
        staged[0].symlink_to(victim)
        original_fchmod(descriptor, mode)

    monkeypatch.setattr(cli.tempfile, "mkstemp", tracked_mkstemp)
    monkeypatch.setattr(cli.os, "fchmod", swap_before_fchmod)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="staged|publish|identity|regular",
    ):
        cli._publish_create_only(destination, b"candidate\n")
    assert staged
    assert victim.read_bytes() == b"untouched\n"
    assert stat.S_IMODE(victim.stat().st_mode) == 0o600
    assert not destination.exists()
    assert not staged[0].exists()


@pytest.mark.parametrize("replace_destination", (False, True))
def test_cli_post_link_directory_sync_failure_cleans_only_published_inode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    replace_destination: bool,
) -> None:
    cli = _load_cli()
    destination = tmp_path / "result.json"
    original_open = cli.os.open

    def fail_directory_open(path: object, flags: int, *args: object) -> int:
        if Path(path) == tmp_path:
            if replace_destination:
                destination.unlink()
                destination.write_bytes(b"racer-owned\n")
            raise OSError("synthetic directory-open failure")
        return original_open(path, flags, *args)

    monkeypatch.setattr(cli.os, "open", fail_directory_open)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="cannot publish",
    ):
        cli._publish_create_only(destination, b"candidate\n")
    if replace_destination:
        assert destination.read_bytes() == b"racer-owned\n"
    else:
        assert not destination.exists()
    assert not list(tmp_path.glob(".a23c-negative-replay-*.tmp"))


def test_cli_reader_rejects_source_or_ancestor_symlink_fifo_and_oversize(
    tmp_path: Path,
) -> None:
    cli = _load_cli()
    actual = tmp_path / "actual.py"
    actual.write_bytes(b"pass\n")
    linked = tmp_path / "linked.py"
    linked.symlink_to(actual)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="symlink|regular",
    ):
        cli._read_regular(linked, label="source", limit=1_024)

    actual_parent = tmp_path / "actual-parent"
    actual_parent.mkdir()
    (actual_parent / "source.py").write_bytes(b"pass\n")
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(actual_parent, target_is_directory=True)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="symlink|directory|ancestor",
    ):
        cli._read_regular(
            linked_parent / "source.py", label="source", limit=1_024
        )

    oversized = tmp_path / "oversized.py"
    oversized.write_bytes(b"x" * 1_025)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="bounded|limit",
    ):
        cli._read_regular(oversized, label="source", limit=1_024)

    if hasattr(os, "mkfifo") and hasattr(os, "O_NONBLOCK"):
        fifo = tmp_path / "source.fifo"
        os.mkfifo(fifo)
        with pytest.raises(
            cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
            match="regular",
        ):
            cli._read_regular(fifo, label="source", limit=1_024)


def test_cli_lexical_source_boundary_rejects_symlink_alias(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    cli._require_exact_cli_source()
    actual = tmp_path / "actual.py"
    actual.write_bytes(b"pass\n")
    linked = tmp_path / "linked.py"
    linked.symlink_to(actual)
    monkeypatch.setattr(cli, "LEXICAL_CLI_PATH", linked)
    monkeypatch.setattr(cli, "EXPECTED_CLI_PATH", linked)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="non-symlink regular file",
    ):
        cli._require_exact_cli_source()


def test_cli_preimport_poisoning_and_stdlib_shadow_abort_before_authentication(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    for poisoned in (
        {"peano_lab": SimpleNamespace()},
        {"training": SimpleNamespace()},
        {
            "json": SimpleNamespace(
                __file__=str(ROOT / "synthetic-shadow/json.py")
            )
        },
    ):
        with monkeypatch.context() as patcher:
            events: list[str] = []
            for name in tuple(sys.modules):
                if (
                    name == "training"
                    or name.startswith("training.")
                    or name == "peano_lab"
                    or name.startswith("peano_lab.")
                ):
                    patcher.delitem(sys.modules, name, raising=False)
            for name, module in poisoned.items():
                patcher.setitem(sys.modules, name, module)
            patcher.setattr(
                cli,
                "_authenticate_schema_sources_and_inputs",
                lambda: events.append("authenticated"),
            )
            with pytest.raises(
                cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
                match="contaminated|shadowed",
            ):
                cli._load_replayer()
            assert events == []
            assert cli.REPLAYER_MODULE_NAME not in sys.modules


def test_cli_preflight_requires_exact_ordered_standard_meta_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    wanted = (
        importlib.machinery.BuiltinImporter,
        importlib.machinery.FrozenImporter,
        importlib.machinery.PathFinder,
    )
    safe_path = ["/a23c-deliberately-absent-import-root"]
    monkeypatch.setattr(
        cli,
        "sys",
        SimpleNamespace(meta_path=list(wanted), path=safe_path),
    )
    cli._preflight_stdlib_and_import_path()

    for changed in (
        (wanted[1], wanted[0], wanted[2]),
        (*wanted, wanted[2]),
    ):
        monkeypatch.setattr(
            cli,
            "sys",
            SimpleNamespace(meta_path=list(changed), path=safe_path),
        )
        with pytest.raises(
            cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
            match="nonstandard meta-path importer",
        ):
            cli._preflight_stdlib_and_import_path()


def test_cli_rejects_pyc_or_foreign_loader_preference_before_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    fake = SimpleNamespace(
        cached=str(ROOT / "__pycache__/replayer.pyc"),
        loader=importlib.machinery.SourcelessFileLoader(
            "forged", str(ROOT / "__pycache__/replayer.pyc")
        ),
        origin=str(cli.REPLAYER_PATH),
    )
    monkeypatch.setattr(cli, "_require_clean_preimport_state", lambda: None)
    monkeypatch.setattr(cli, "_require_exact_cli_source", lambda: None)
    monkeypatch.setattr(cli, "_preflight_stdlib_and_import_path", lambda: None)
    monkeypatch.setattr(cli, "_preflight_peano_source_specs", lambda _schema: None)
    monkeypatch.setattr(
        cli, "_authenticate_schema_sources_and_inputs", lambda: ({}, b"", {})
    )
    monkeypatch.setattr(cli.importlib.util, "spec_from_file_location", lambda *_a: fake)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="source specification drifted",
    ):
        cli._load_replayer()
    assert cli.REPLAYER_MODULE_NAME not in sys.modules


def test_cli_attests_exact_39_source_loader_origin_cache_closure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    schema = json.loads(SCHEMA_PATH.read_bytes())
    expected = cli._implementation_module_map(schema)
    assert len(expected) == 39

    def modules() -> tuple[dict[str, object], object]:
        result: dict[str, object] = {}
        for name, (source, is_package) in expected.items():
            loader = importlib.machinery.SourceFileLoader(name, str(source))
            specification = importlib.machinery.ModuleSpec(
                name,
                loader,
                origin=str(source),
                is_package=is_package,
            )
            specification.cached = f"{cli.PYCACHE_PREFIX}/{name}.pyc"
            if is_package:
                specification.submodule_search_locations = [str(source.parent)]
            result[name] = SimpleNamespace(
                __file__=str(source),
                __spec__=specification,
            )
        replayer_loader = importlib.machinery.SourceFileLoader(
            cli.REPLAYER_MODULE_NAME, str(cli.REPLAYER_PATH)
        )
        replayer_specification = importlib.machinery.ModuleSpec(
            cli.REPLAYER_MODULE_NAME,
            replayer_loader,
            origin=str(cli.REPLAYER_PATH),
            is_package=False,
        )
        replayer_specification.cached = (
            f"{cli.PYCACHE_PREFIX}/{cli.REPLAYER_MODULE_NAME}.pyc"
        )
        replayer_module = SimpleNamespace(
            __file__=str(cli.REPLAYER_PATH),
            __loader__=replayer_loader,
            __name__=cli.REPLAYER_MODULE_NAME,
            __package__="",
            __spec__=replayer_specification,
        )
        result[cli.__name__] = SimpleNamespace(
            __file__=str(cli.LEXICAL_CLI_PATH)
        )
        result[cli.REPLAYER_MODULE_NAME] = replayer_module
        return result, replayer_module

    exact, exact_replayer = modules()
    monkeypatch.setattr(cli, "sys", SimpleNamespace(modules=exact))
    cli._attest_loaded_source_closure(schema, exact_replayer)

    for mode in (
        "extra-peano-module",
        "foreign-loader",
        "wrong-origin",
        "wrong-cache-prefix",
        "replayer-module-identity",
        "training-contamination",
        "unexpected-allowed-source-alias",
        "unexpected-repository-module",
    ):
        changed, changed_replayer = modules()
        name = next(iter(expected))
        if mode == "extra-peano-module":
            changed["peano_lab.unregistered"] = SimpleNamespace()
        elif mode == "foreign-loader":
            source, _is_package = expected[name]
            changed[name].__spec__.loader = importlib.machinery.SourcelessFileLoader(
                name, str(source.with_suffix(".pyc"))
            )
        elif mode == "wrong-origin":
            changed[name].__spec__.origin = str(SCHEMA_PATH)
        elif mode == "wrong-cache-prefix":
            changed[name].__spec__.cached = str(ROOT / "__pycache__/foreign.pyc")
        elif mode == "replayer-module-identity":
            changed_replayer.__loader__ = object()
        elif mode == "training-contamination":
            changed["training"] = SimpleNamespace()
        elif mode == "unexpected-allowed-source-alias":
            changed["unexpected_alias"] = SimpleNamespace(
                __file__=str(expected[name][0])
            )
        else:
            changed["unregistered_project"] = SimpleNamespace(
                __file__=str(SCHEMA_PATH)
            )
        monkeypatch.setattr(cli, "sys", SimpleNamespace(modules=changed))
        with pytest.raises(
            cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
            match="closure|identity|contaminated|unexpected repository",
        ):
            cli._attest_loaded_source_closure(schema, changed_replayer)


def test_cli_executes_authenticated_replayer_bytes_not_a_changed_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    path = tmp_path / "replayer.py"
    authenticated = b"SENTINEL = 'authenticated'\n"
    path.write_bytes(b"SENTINEL = 'changed-path'\n")
    specification = importlib.util.spec_from_file_location("fixture", path)
    assert specification is not None and specification.cached is not None
    pycache_prefix = str(Path(specification.cached).parent)
    original_path = list(sys.path)
    monkeypatch.setattr(cli, "ROOT", tmp_path)
    monkeypatch.setattr(cli, "PY_ROOT", tmp_path)
    monkeypatch.setattr(cli, "REPLAYER_PATH", path)
    monkeypatch.setattr(cli, "PYCACHE_PREFIX", pycache_prefix)
    monkeypatch.setattr(cli, "_require_clean_preimport_state", lambda: None)
    monkeypatch.setattr(cli, "_require_exact_cli_source", lambda: None)
    monkeypatch.setattr(cli, "_preflight_stdlib_and_import_path", lambda: None)
    monkeypatch.setattr(cli, "_preflight_peano_source_specs", lambda _schema: None)
    monkeypatch.setattr(
        cli, "_attest_loaded_source_closure", lambda _schema, _module: None
    )
    monkeypatch.setattr(
        cli,
        "_attest_authenticated_implementation_bytes",
        lambda _schema, _identities: None,
    )

    def authenticate() -> tuple[
        dict[str, object],
        bytes,
        dict[str, tuple[int, int, int, int, int]],
    ]:
        path.write_bytes(b"SENTINEL = 'mutated-after-auth'\n")
        return {}, authenticated, {}

    monkeypatch.setattr(cli, "_authenticate_schema_sources_and_inputs", authenticate)
    try:
        module, identity = cli._load_replayer()
        assert module.SENTINEL == "authenticated"
        assert identity["sha256"] == _sha(authenticated)
        assert identity["bytes"] == len(authenticated)
        assert identity["load_mode"] == (
            "authenticated-source-bytes-source_to_code-exec"
        )
    finally:
        sys.modules.pop(cli.REPLAYER_MODULE_NAME, None)
        sys.path[:] = original_path


def test_controlled_worker_marker_cannot_be_supplied_as_a_user_bypass(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    monkeypatch.setenv(cli._WORKER_ENVIRONMENT, "1")
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="fresh controlled",
    ):
        cli._require_controlled_worker()

    if ISOLATED_PYTHON is None:
        pytest.skip("Python 3.11+ is required to exercise isolated -P workers")
    environment = {
        name: value
        for name, value in os.environ.items()
        if name in {"LANG", "LC_ALL", "LC_CTYPE", "PATH", "TMPDIR", "TZ"}
    }
    environment.update(
        {
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONPYCACHEPREFIX": cli.PYCACHE_PREFIX,
            cli._WORKER_ENVIRONMENT: "1",
            cli._WORKER_CAPABILITY_FD: "9",
            cli._WORKER_CAPABILITY_SHA256: "a" * 64,
        }
    )
    completed = subprocess.run(
        [
            ISOLATED_PYTHON,
            "-B",
            "-P",
            "-s",
            "-S",
            str(CLI_PATH),
            "--_controlled-worker",
        ],
        cwd=ROOT,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert completed.returncode == 2
    assert "capability" in completed.stderr or "fresh controlled" in completed.stderr


def test_cli_controlled_environment_strips_python_injection_and_requires_seed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    for name in cli._FORBIDDEN_ENVIRONMENT:
        monkeypatch.setenv(name, "synthetic-injection")
    environment = cli._controlled_environment(
        "17", capability_fd=9, capability_sha256="a" * 64
    )
    assert not set(cli._FORBIDDEN_ENVIRONMENT).intersection(environment)
    assert environment["PYTHONDONTWRITEBYTECODE"] == "1"
    assert environment["PYTHONHASHSEED"] == "17"
    assert environment["PYTHONPYCACHEPREFIX"] == cli.PYCACHE_PREFIX
    assert environment[cli._WORKER_ENVIRONMENT] == "1"
    assert environment[cli._WORKER_CAPABILITY_FD] == "9"
    assert environment[cli._WORKER_CAPABILITY_SHA256] == "a" * 64
    for seed in ("", "-1", "1.0", "seed", 1):
        with pytest.raises(
            cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
            match="hash-seed",
        ):
            cli._controlled_environment(
                seed, capability_fd=9, capability_sha256="a" * 64
            )


def test_cli_parent_timeout_and_nonzero_remain_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    args = cli._parser().parse_args([])

    with monkeypatch.context() as patcher:
        patcher.setattr(
            cli,
            "_run_bounded_child",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                cli.LibraryPilotDependencyVectorNegativeReplayCLIError(
                    "controlled A2.3c worker timed out; outcome is unknown"
                )
            ),
        )
        with pytest.raises(
            cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
            match="timed out|unknown",
        ):
            cli._parent(args)

    with monkeypatch.context() as patcher:
        patcher.setattr(
            cli,
            "_run_bounded_child",
            lambda *_args, **_kwargs: SimpleNamespace(
                returncode=9, stderr=b"", stdout=b""
            ),
        )
        with pytest.raises(
            cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
            match="exited 9",
        ):
            cli._parent(args)



def test_bounded_child_terminates_and_reaps_each_noisy_stream_at_hard_cap(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    original_selector = cli.selectors.DefaultSelector
    original_read = cli.os.read
    registered: dict[int, str] = {}
    requested: dict[str, list[int]] = {}

    class TrackingSelector:
        def __init__(self) -> None:
            registered.clear()
            self.inner = original_selector()

        def register(self, fileobj: object, events: int, data: str) -> object:
            registered[fileobj.fileno()] = data
            return self.inner.register(fileobj, events, data)

        def unregister(self, fileobj: object) -> object:
            registered.pop(fileobj.fileno(), None)
            return self.inner.unregister(fileobj)

        def select(self, timeout: float | None = None) -> object:
            return self.inner.select(timeout)

        def get_map(self) -> object:
            return self.inner.get_map()

        def close(self) -> None:
            self.inner.close()

    def bounded_read(descriptor: int, amount: int) -> bytes:
        stream = registered.get(descriptor)
        if stream is not None:
            requested.setdefault(stream, []).append(amount)
        return original_read(descriptor, amount)

    monkeypatch.setattr(cli.selectors, "DefaultSelector", TrackingSelector)
    monkeypatch.setattr(cli.os, "read", bounded_read)
    child_source = (
        "import os,sys\n"
        "with open(sys.argv[1], 'w', encoding='ascii') as handle:\n"
        "    handle.write(str(os.getpid()))\n"
        "descriptor = int(sys.argv[2])\n"
        "while True:\n"
        "    os.write(descriptor, b'x' * 65536)\n"
    )
    for stream, descriptor in (("stdout", 1), ("stderr", 2)):
        requested.clear()
        pid_path = tmp_path / f"{stream}.pid"
        started = cli.time.monotonic()
        with pytest.raises(
            cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
            match=rf"worker {stream} exceeded its hard byte cap; outcome is unknown",
        ):
            cli._run_bounded_child(
                [
                    sys.executable,
                    "-c",
                    child_source,
                    str(pid_path),
                    str(descriptor),
                ],
                cwd=tmp_path,
                environment=dict(os.environ),
                max_stdout_bytes=1_024,
                max_stderr_bytes=1_024,
                timeout_seconds=5,
            )
        assert cli.time.monotonic() - started < 5
        assert requested[stream]
        assert max(requested[stream]) <= 1_025
        child_pid = int(pid_path.read_text(encoding="ascii"))
        with pytest.raises(ProcessLookupError):
            os.kill(child_pid, 0)


def test_cli_execute_requires_exact_confirmation_before_spawning(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    calls: list[object] = []
    monkeypatch.setattr(
        cli,
        "_run_bounded_child",
        lambda *_args, **_kwargs: calls.append((_args, _kwargs)),
    )
    for arguments in (("--execute",), ("--execute", "--confirm", "wrong")):
        with pytest.raises(
            cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
            match="exact confirmation",
        ):
            cli._parent(cli._parser().parse_args(arguments))
    for arguments in (
        ("--confirm", "wrong"),
        ("--validate-result", "missing.json", "--confirm", "wrong"),
    ):
        with pytest.raises(
            cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
            match="only with --execute",
        ):
            cli._parent(cli._parser().parse_args(arguments))
    assert calls == []


def test_cli_authenticates_exact_sources_and_inputs_before_any_peano_import(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    assert cli.SCHEMA_SOURCE_BYTES == SCHEMA_PATH.stat().st_size
    assert cli.SCHEMA_SOURCE_SHA256 == _sha(SCHEMA_PATH.read_bytes())
    assert cli.SCHEMA_SEMANTIC_SHA256 == replay.NEGATIVE_REPLAY_SCHEMA_SEMANTIC_SHA256
    assert cli.REPLAYER_SOURCE_BYTES == MODULE_PATH.stat().st_size
    assert cli.REPLAYER_SOURCE_SHA256 == _sha(MODULE_PATH.read_bytes())

    before = set(sys.modules)
    reads: list[Path] = []
    original_with_identity = cli._read_regular_with_identity

    def tracked_with_identity(
        path: Path, *, label: str, limit: int
    ) -> tuple[bytes, tuple[int, int, int, int, int]]:
        reads.append(path)
        return original_with_identity(path, label=label, limit=limit)

    monkeypatch.setattr(cli, "_read_regular_with_identity", tracked_with_identity)
    schema, replayer_raw, source_identities = (
        cli._authenticate_schema_sources_and_inputs()
    )
    expected = [
        cli.SCHEMA_PATH,
        *(cli.ROOT / row["path"] for row in schema["implementation_sources"]),
        *(cli.ROOT / row["path"] for row in schema["fixed_inputs"].values()),
        cli.REPLAYER_PATH,
    ]
    assert reads == expected
    assert len(reads) == 1 + 39 + 6 + 1
    assert replayer_raw == MODULE_PATH.read_bytes()
    assert set(source_identities) == {
        row["path"] for row in schema["implementation_sources"]
    }
    introduced = set(sys.modules) - before
    assert not {
        name
        for name in introduced
        if name == "training"
        or name.startswith("training.")
        or name == "peano_lab"
        or name.startswith("peano_lab.")
    }


def test_cli_rejects_registered_source_mutated_after_authentication(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    registered = json.loads(SCHEMA_PATH.read_bytes())
    fixture_root = tmp_path / "repository"
    for row in registered["implementation_sources"]:
        source = ROOT / row["path"]
        destination = fixture_root / row["path"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

    fixed_redirects = {
        fixture_root / identity["path"]: ROOT / identity["path"]
        for identity in registered["fixed_inputs"].values()
    }
    original_read = cli._read_regular

    def redirected_read(path: Path, *, label: str, limit: int) -> bytes:
        return original_read(
            fixed_redirects.get(path, path),
            label=label,
            limit=limit,
        )

    monkeypatch.setattr(cli, "ROOT", fixture_root)
    monkeypatch.setattr(cli, "PY_ROOT", fixture_root / "peano-lab/py")
    monkeypatch.setattr(cli, "_read_regular", redirected_read)
    schema, _replayer_raw, authenticated = (
        cli._authenticate_schema_sources_and_inputs()
    )
    assert len(authenticated) == 39

    relative = Path(schema["implementation_sources"][0]["path"])
    changed = fixture_root / relative
    changed.write_bytes(changed.read_bytes() + b"# changed before import\n")
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="implementation source .* changed during load",
    ):
        cli._attest_authenticated_implementation_bytes(schema, authenticated)

    load_source = CLI_PATH.read_text(encoding="utf-8").split(
        "def _load_replayer()", 1
    )[1].split("def _safe_output_parent", 1)[0]
    assert load_source.index("_authenticate_schema_sources_and_inputs") < (
        load_source.index("exec(code")
    ) < load_source.index("_attest_authenticated_implementation_bytes")


def test_cli_source_byte_drift_aborts_before_replayer_load(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cli = _load_cli()
    schema = json.loads(SCHEMA_PATH.read_bytes())
    target = ROOT / schema["implementation_sources"][0]["path"]
    original = cli._read_regular_with_identity
    reads: list[Path] = []

    def corrupt(
        path: Path, *, label: str, limit: int
    ) -> tuple[bytes, tuple[int, int, int, int, int]]:
        reads.append(path)
        raw, identity = original(path, label=label, limit=limit)
        return (raw + b"\n" if path == target else raw), identity

    monkeypatch.setattr(cli, "_read_regular_with_identity", corrupt)
    with pytest.raises(
        cli.LibraryPilotDependencyVectorNegativeReplayCLIError,
        match="implementation source .* drifted",
    ):
        cli._authenticate_schema_sources_and_inputs()
    assert cli.REPLAYER_PATH not in reads
    assert cli.REPLAYER_MODULE_NAME not in sys.modules


def test_cli_fresh_default_subprocess_emits_only_source_protocol() -> None:
    if ISOLATED_PYTHON is None:
        pytest.skip("Python 3.11+ is required to exercise isolated -P workers")
    before = set(
        (ROOT / "artifacts/peano-hydra").glob(
            "l0-pilot-dependency-vector-negative-replay-*.json"
        )
    )
    completed = subprocess.run(
        [ISOLATED_PYTHON, str(CLI_PATH)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    value = json.loads(completed.stdout)
    assert value["status"] == "source-only-no-campaign"
    assert value["campaign_executed"] is False
    assert value["result_exists"] is False
    assert value["negative_observations_independently_verified"] is False
    assert value["route_rejections_independently_verified"] is False
    assert set(
        (ROOT / "artifacts/peano-hydra").glob(
            "l0-pilot-dependency-vector-negative-replay-*.json"
        )
    ) == before


def test_static_driver_is_independent_of_a23b_and_candidate_body_compiler() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported: list[str] = []
    called: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.append(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called.append(node.func.attr)

    forbidden_imports = (
        "training.peano_hydra.library_pilot_dependency_vector_audit",
        "training.peano_hydra.library_pilot_dependency_vector_audit_verifier",
        "peano_lab.library.candidate_validation",
    )
    assert not any(
        name == prefix or name.startswith(prefix + ".")
        for name in imported
        for prefix in forbidden_imports
    )
    assert "compile_candidate_body" not in called


def test_pinned_inputs_and_exact_three_root_scripts_are_unchanged() -> None:
    for path, digest in PINNED_INPUTS.items():
        assert _sha(path.read_bytes()) == digest

    manifest = json.loads(REPLAY_MANIFEST_PATH.read_bytes())
    rows = {row["name"]: row for row in manifest["theorems"]}
    assert len(rows) == 384
    for index, name in EXPECTED_ROOTS:
        row = rows[name]
        script = tuple(row["script"])
        assert row["index"] == index
        assert len(script) == EXPECTED_COMMAND_COUNTS[name]
        assert _lf_sha(script) == EXPECTED_SCRIPT_SHA256[name]


def test_single_omission_schedule_is_exact_unique_and_reverse_ordered() -> None:
    manifest = json.loads(REPLAY_MANIFEST_PATH.read_bytes())
    rows = {row["name"]: row for row in manifest["theorems"]}
    schema_rows = {
        row["name"]: row
        for row in replay.pilot_dependency_vector_negative_replay_schema(ROOT)[
            "required_theorems"
        ]
    }
    tasks: list[object] = []
    for index, name in EXPECTED_ROOTS:
        tasks.extend(
            replay.single_omission_replay_tasks(
                name,
                index,
                EXPECTED_DIRECT[name],
                tuple(rows[name]["script"]),
                schema_rows[name]["tasks"],
            )
        )

    assert len(tasks) == len(EXPECTED_FAILURE_INDEX) == 22
    assert len(
        {
            (
                _field(task, "theorem_name"),
                _field(task, "omitted_dependency"),
            )
            for task in tasks
        }
    ) == 22
    offset = 0
    for index, name in EXPECTED_ROOTS:
        expected = tuple(reversed(EXPECTED_DIRECT[name]))
        actual = tuple(
            _field(task, "omitted_dependency")
            for task in tasks[offset : offset + len(expected)]
        )
        assert actual == expected
        for attempt_index, task in enumerate(
            tasks[offset : offset + len(expected)]
        ):
            omitted = _field(task, "omitted_dependency")
            assert _field(task, "theorem_index") == index
            assert _field(task, "theorem_name") == name
            assert _field(task, "attempt_index") == attempt_index
            assert tuple(_field(task, "full_dependencies")) == (
                EXPECTED_DIRECT[name]
            )
            assert tuple(_field(task, "trial_dependencies")) == tuple(
                dependency
                for dependency in EXPECTED_DIRECT[name]
                if dependency != omitted
            )
            assert _field(task, "expected_command_index") == (
                EXPECTED_FAILURE_INDEX[(name, omitted)]
            )
        offset += len(expected)
