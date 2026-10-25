"""The model-v2 post-training acceptance set is frozen and model-free."""

from __future__ import annotations

from dataclasses import asdict
import importlib.util
import hashlib
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from peano_lab.kernel.formulas import parse_formula_with_names, pretty_formula
from peano_lab.library.theorems import THEOREMS
from training.peano_policy.config import load_config
from training.peano_policy.base_snapshot import expected_base_snapshot
from training.peano_policy.contract import (
    HELD_OUT_POLICY_GOALS,
    environment_record,
    held_out_contract_record,
    held_out_contract_sha256,
    model_v2_environment,
)
from training.peano_policy.manifest import artifact_directory_hash
from training.peano_policy.train import _training_source_hash
from training.peano_policy.prompt import (
    PEANO_PROMPT_V2,
    prompt_contract_sha256,
    prompt_manifest_record,
    render_prompt,
)
from training.peano_policy.data import ROW_FIELDS
from scripts import eval_peano_policy as EVALUATOR
from scripts import eval_trained_peano_policy as TRAINED_EVALUATOR


MANIFEST = ROOT / "training" / "peano_policy" / "acceptance_v2.json"
SCRIPT = ROOT / "scripts" / "peano_policy_acceptance.py"
SPEC = importlib.util.spec_from_file_location("_peano_policy_acceptance", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
ACCEPTANCE = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = ACCEPTANCE
SPEC.loader.exec_module(ACCEPTANCE)


@pytest.fixture(scope="module", autouse=True)
def _external_acceptance_pycache(tmp_path_factory: pytest.TempPathFactory):
    """Make local checkout caches inert, matching every guarded WMI job."""

    previous = sys.pycache_prefix
    sys.pycache_prefix = str(tmp_path_factory.mktemp("acceptance-pycache"))
    try:
        yield
    finally:
        sys.pycache_prefix = previous


def _minimal_semantic_tree(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, Path]:
    package = tmp_path / "peano-lab" / "py" / "peano_lab"
    policy = tmp_path / "training" / "peano_policy"
    scripts = tmp_path / "scripts"
    for directory in (package, policy, scripts):
        directory.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (policy / "__init__.py").write_text("", encoding="utf-8")
    selected = scripts / "eval_peano_policy.py"
    selected.write_text("VALUE = 1\n", encoding="utf-8")

    monkeypatch.setattr(ACCEPTANCE, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(ACCEPTANCE, "PEANO_PYTHON", package.parent)
    monkeypatch.setattr(
        ACCEPTANCE,
        "PRIMARY_SEMANTIC_SCRIPT_FILES",
        ("scripts/eval_peano_policy.py",),
    )
    monkeypatch.setattr(ACCEPTANCE, "PRIMARY_SEMANTIC_PROTOCOL_FILES", ())
    monkeypatch.setattr(
        ACCEPTANCE,
        "PRIMARY_SEMANTIC_TRAINING_REVIEWED_NONCODE_FILES",
        (),
    )
    monkeypatch.setattr(
        ACCEPTANCE,
        "PRIMARY_SEMANTIC_EXTERNALLY_SEALED_FILES",
        (),
    )
    return {
        "package": package,
        "policy": policy,
        "scripts": scripts,
        "training": policy.parent,
    }


def test_semantic_source_rejects_a_symlinked_descendant_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _minimal_semantic_tree(monkeypatch, tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (paths["package"] / "unreviewed").symlink_to(
        outside, target_is_directory=True
    )

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="contains symlink"):
        ACCEPTANCE._primary_semantic_source_identity()


def test_semantic_source_rejects_cross_abi_extension_shadowing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _minimal_semantic_tree(monkeypatch, tmp_path)
    competitor = (
        paths["scripts"]
        / "eval_peano_policy.cpython-312-x86_64-linux-gnu.so"
    )
    competitor.write_bytes(b"not an extension")

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="competing loader"):
        ACCEPTANCE._primary_semantic_source_identity()


def test_semantic_source_rejects_same_stem_package_shadowing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    paths = _minimal_semantic_tree(monkeypatch, tmp_path)
    competitor = paths["scripts"] / "eval_peano_policy"
    competitor.mkdir()
    (competitor / "__init__.py").write_text(
        "raise RuntimeError('must never import')\n", encoding="utf-8"
    )

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="competing loader"):
        ACCEPTANCE._primary_semantic_source_identity()


@pytest.mark.parametrize("namespace", ("scripts", "training"))
def test_semantic_source_rejects_namespace_parent_initializers(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    namespace: str,
) -> None:
    paths = _minimal_semantic_tree(monkeypatch, tmp_path)
    (paths[namespace] / "__init__.py").write_text(
        "raise RuntimeError('must never import')\n", encoding="utf-8"
    )

    with pytest.raises(
        ACCEPTANCE.AcceptanceError, match="must remain a namespace package"
    ):
        ACCEPTANCE._primary_semantic_source_identity()


def _canonical(source: str) -> str:
    formula, free_names = parse_formula_with_names(source)
    assert free_names == ()
    return pretty_formula(formula, list(free_names))


def test_preregistered_formulas_are_closed_and_have_only_declared_collisions() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    summary = ACCEPTANCE.validate_manifest(manifest, manifest_path=MANIFEST)
    environment = model_v2_environment()
    allowed = frozenset(environment.capabilities.allowed_theorems or ())
    public: dict[str, list[str]] = {}
    for theorem in THEOREMS:
        public.setdefault(_canonical(theorem.statement), []).append(theorem.name)

    rows = manifest["goals"]
    assert [row["id"] for row in rows] == [
        "R1", "R2", "R3",
        "C1", "C2", "C3", "C4", "C5",
        "I1", "I2", "I3", "I4",
        "H1", "H2", "H3", "H4",
    ]
    for row in rows:
        statement = _canonical(row["statement"])
        assert statement == row["statement"]
        assert public.get(statement, []) == row["public_collisions"]

    assert all(row["retrieval_theorem"] in allowed for row in rows[:3])
    assert all(not row["public_collisions"] for row in rows[3:12])
    sealed_names = [row["sealed_name"] for row in rows[12:]]
    assert sealed_names == [name for name, _ in HELD_OUT_POLICY_GOALS]
    assert set(sealed_names).isdisjoint(allowed)
    assert summary["held_out_names"] == sealed_names
    assert summary["category_counts"] == {
        "retrieval": 3,
        "composition": 5,
        "induction": 4,
        "sealed": 4,
    }


def _outcomes(successes: set[str]) -> tuple[object, ...]:
    categories = {
        **{f"R{index}": "retrieval" for index in range(1, 4)},
        **{f"C{index}": "composition" for index in range(1, 6)},
        **{f"I{index}": "induction" for index in range(1, 5)},
        **{f"H{index}": "sealed" for index in range(1, 5)},
    }
    return tuple(
        ACCEPTANCE.GoalOutcome(
            goal_id,
            category,
            goal_id in successes,
            goal_id in successes and category == "retrieval",
            goal_id in successes,
            "proof" if goal_id in successes else "limit",
            1 if goal_id in successes else 0,
            1 if goal_id in successes else None,
        )
        for goal_id, category in categories.items()
    )


def test_binary_rule_separates_retrieval_from_synthesis() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    exactly_passes = {
        "R1", "R2", "R3",
        "C1", "C2", "C3", "C4",
        "I1", "I2",
        "H1",
    }
    report = ACCEPTANCE.score_outcomes(
        manifest,
        _outcomes(exactly_passes),
        identity_integrity=True,
    )

    assert report["counts"] == {
        "categories": {
            "retrieval": 3,
            "composition": 4,
            "induction": 2,
            "sealed": 1,
        },
        "synthesis": 7,
        "overall": 10,
        "nontrivial_induction": 1,
    }
    assert report["binary_pass"] is True
    assert report["stretch_pass"] is False

    missed_retrieval = list(_outcomes(exactly_passes))
    missed_retrieval[0] = ACCEPTANCE.GoalOutcome(
        "R1", "retrieval", True, False, True, "proof", 1, 1
    )
    missed = ACCEPTANCE.score_outcomes(
        manifest,
        missed_retrieval,
        identity_integrity=True,
    )
    assert missed["counts"]["categories"]["retrieval"] == 2
    assert missed["binary_pass"] is False


def _base_policy(manifest: dict[str, object], runner: str) -> dict[str, object]:
    subject = manifest["subject"]
    authority = subject["authority"]
    environment = model_v2_environment()
    fixed_hashes = {
        "training_manifest_sha256": "a" * 64,
        "adapter_sha256": "b" * 64,
        "dataset_sha256": "c" * 64,
        "base_snapshot_sha256": manifest["subject"]["base_model"]["snapshot"][
            "snapshot_sha256"
        ],
    }
    return {
        "name": "peano-policy:unit",
        "kind": "peano-policy-adapter-v1",
        "prompt_version": PEANO_PROMPT_V2,
        "prompt_contract_sha256": prompt_contract_sha256(PEANO_PROMPT_V2),
        "environment": {
            "classical": False,
            "surface": "model-v2",
            "environment_sha256": authority["environment_sha256"],
            "capabilities": environment.capabilities.to_record(),
        },
        "decoding": manifest["protocol"][runner]["decoding"],
        "provenance": {
            **fixed_hashes,
            "run_name": subject["run_name"],
            "base_model_id": subject["base_model"]["id"],
            "base_model_revision": subject["base_model"]["revision"],
            "environment_sha256": authority["environment_sha256"],
            "held_out_contract_sha256": authority["held_out_contract_sha256"],
            "library_snapshot_sha256": authority["library_identity_sha256"],
            "evaluation": {
                "job": {},
                "sources": ACCEPTANCE._expected_evaluation_sources(manifest),
            },
        },
    }


def _synthetic_reports(
    manifest: dict[str, object], successes: set[str]
) -> tuple[list[dict[str, object]], dict[str, object]]:
    interactive_run = manifest["protocol"]["interactive"]
    repl: list[dict[str, object]] = []
    for goal in manifest["goals"][:12]:
        proved = goal["id"] in successes
        commands = (
            [f"use {goal['retrieval_theorem']}", "apply placeholder"]
            if proved and goal["category"] == "retrieval"
            else (["placeholder"] if proved else [])
        )
        repl.append(
            {
                "format": "peano-policy-interactive-result",
                "v": 1,
                "request": {"canonical_theorem": goal["statement"]},
                "adapter": {
                    "policy": {
                        "name": "peano-policy:unit:candidates",
                        "kind": "peano-kernel-guided-candidate-policy-v1",
                        "base_policy": _base_policy(manifest, "interactive"),
                        "seed": interactive_run["seed"],
                        "seed_schedule": (
                            "sha256-json-v1(seed,call_index,canonical_goals)"
                        ),
                        "batching": "one-model-generate-call-per-search-state",
                    }
                },
                "authority": {
                    "classical": False,
                    "capabilities": model_v2_environment().capabilities.to_record(),
                },
                "budget": interactive_run["search_budget_per_goal"],
                "search": {
                    "status": "proof" if proved else "limit",
                    "theorem": goal["statement"],
                    "commands": commands,
                    "certificate_nodes": 1 if proved else None,
                    "diagnostics": [],
                    "model_calls": 1,
                    "states_expanded": 1,
                    "states_discovered": 1,
                    "candidates_executed": 1,
                    "frontier_peak": 1,
                    "depth_reached": len(commands) if proved else 0,
                },
                "kernel_verification": (
                    {
                        "status": "proved",
                        "kernel_checked": True,
                        "theorem": goal["statement"],
                        "surface": "model-v2",
                        "classical": False,
                        "failed_tactics": 0,
                        "tactics_applied": len(commands),
                        "proof_nodes": 1,
                    }
                    if proved
                    else None
                ),
                "publication": {
                    "status": "kernel-checked-proof" if proved else "no-checked-proof",
                    "script_sha256": "e" * 64 if proved else None,
                },
            }
        )

    sealed_run = manifest["protocol"]["sealed_evaluator"]
    result_rows: list[dict[str, object]] = []
    search_rows: list[dict[str, object]] = []
    for goal in manifest["goals"][12:]:
        proved = goal["id"] in successes
        commands = ["placeholder"] if proved else []
        attempt = {
            "sample": 0,
            "seed": int.from_bytes(
                hashlib.sha256(
                    json.dumps(
                        [
                            1,
                            sealed_run["seed"],
                            goal["sealed_name"],
                            goal["statement"],
                        ],
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ).encode("utf-8")
                ).digest()[:8],
                "big",
            )
            & (2**63 - 1),
            "status": "proof" if proved else "limit",
            "steps": len(commands),
            "commands": commands,
            "proof_nodes": 1 if proved else None,
            "error": None if proved else "kernel-guided search limit",
        }
        attempt_status = "proof" if proved else "limit"
        result_rows.append(
            {
                "name": goal["sealed_name"],
                "statement": goal["statement"],
                "classical": False,
                "surface_profile": "model-v2",
                "allowed_theorems": list(
                    model_v2_environment().capabilities.allowed_theorems or ()
                ),
                "environment_sha256": manifest["subject"]["authority"][
                    "environment_sha256"
                ],
                "passed": proved,
                "status_counts": {
                    status: int(status == attempt_status)
                    for status in EVALUATOR.ATTEMPT_STATUSES
                },
                "attempts": [attempt],
            }
        )
        search_rows.append(
            {
                "name": goal["sealed_name"],
                "environment_sha256": manifest["subject"]["authority"][
                    "environment_sha256"
                ],
                "result": {
                    "status": "proof" if proved else "limit",
                    "theorem": goal["statement"],
                    "commands": commands,
                    "certificate_nodes": 1 if proved else None,
                    "diagnostics": [],
                    "model_calls": 1,
                    "states_expanded": 1,
                    "states_discovered": 1,
                    "candidates_executed": 1,
                    "frontier_peak": 1,
                    "depth_reached": 1 if proved else 0,
                },
                "decoder": {
                    "model_generate_calls": 1,
                    "candidate_sequences_requested": sealed_run[
                        "search_budget_per_goal"
                    ]["candidates_per_state"],
                    "candidate_sequences_returned": sealed_run[
                        "search_budget_per_goal"
                    ]["candidates_per_state"],
                    "candidate_lines_returned": sealed_run[
                        "search_budget_per_goal"
                    ]["candidates_per_state"],
                    "malformed_sequences_rejected": 0,
                    "one_batched_call_per_search_state": True,
                },
            }
        )
    policy_name = "peano-policy:unit:kernel-guided-search"
    sealed_capabilities = model_v2_environment().capabilities
    sealed_goals = tuple(
        EVALUATOR.EvalGoal(
            goal["sealed_name"],
            goal["statement"],
            classical=False,
            surface_profile="model-v2",
            allowed_theorems=sealed_capabilities.allowed_theorems,
        )
        for goal in manifest["goals"][12:]
    )
    proved_goals = sum(row["passed"] for row in result_rows)
    status_counts = {
        status: sum(row["status_counts"][status] for row in result_rows)
        for status in EVALUATOR.ATTEMPT_STATUSES
    }
    per_goal_candidates = sealed_run["search_budget_per_goal"][
        "candidates_per_state"
    ]
    evaluation_sources = ACCEPTANCE._expected_evaluation_sources(manifest)
    snapshot = expected_base_snapshot()
    heldout = {
        "v": EVALUATOR.EVAL_VERSION,
        "policy": policy_name,
        "evaluator": {
            "source_sha256": EVALUATOR.EVALUATOR_SOURCE_SHA256,
            "semantic_sources": EVALUATOR.EVALUATOR_SEMANTIC_SOURCES,
            "runtime": {},
        },
        "mode": "kernel-guided-search",
        "judge": "checked_final(original_target, exact_mode)",
        "goal_set_sha256": EVALUATOR._goal_set_sha256(sealed_goals),
        "seed": sealed_run["seed"],
        "k": 1,
        "max_steps": sealed_run["search_budget_per_goal"]["max_depth"],
        "goal_count": 4,
        "attempt_count": 4,
        "proved_goals": proved_goals,
        "pass@k": proved_goals / 4,
        "status_counts": status_counts,
        "evaluation_integrity": {
            "base_snapshot": {
                "before_load": snapshot,
                "after_evaluation": snapshot,
            },
            "sources": evaluation_sources,
        },
        "policy_identity": {
            "name": policy_name,
            "kind": "peano-kernel-guided-search-v1",
            "limits": sealed_run["search_budget_per_goal"],
            "base_policy": _base_policy(manifest, "sealed_evaluator"),
            "seed": sealed_run["seed"],
            "seed_schedule": "sha256-json-v1(seed,goal_name,goal_statement)",
            "decoder_batching": "one-model-generate-call-per-search-state",
        },
        "goals": result_rows,
        "search": {
            "engine": "training.peano_policy.search.search-v1",
            "budget_scope": "per-goal",
            "limits": sealed_run["search_budget_per_goal"],
            "aggregate_upper_bound": {
                "model_generate_calls": (
                    4 * sealed_run["search_budget_per_goal"]["max_model_calls"]
                ),
                "candidate_sequences": (
                    4
                    * sealed_run["search_budget_per_goal"]["max_model_calls"]
                    * per_goal_candidates
                ),
                "generated_sequence_tokens": (
                    4
                    * sealed_run["search_budget_per_goal"]["max_model_calls"]
                    * per_goal_candidates
                    * sealed_run["decoding"]["max_new_tokens"]
                ),
            },
            "actual": {
                "model_generate_calls": 4,
                "states_expanded": 4,
                "states_discovered": 4,
                "candidates_executed": 4,
                "candidate_sequences_requested": 4 * per_goal_candidates,
                "candidate_sequences_returned": 4 * per_goal_candidates,
                "candidate_lines_returned": 4 * per_goal_candidates,
                "malformed_sequences_rejected": 0,
                "frontier_peak_per_goal": 1,
            },
            "goals": search_rows,
        },
    }
    return repl, heldout


def test_model_free_reporter_consumes_one_exact_primary_run(monkeypatch) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    successes = {
        "R1", "R2", "R3",
        "C1", "C2", "C3", "C4",
        "I1", "I2",
        "H1",
    }
    repl, heldout = _synthetic_reports(manifest, successes)
    replayed: list[str] = []

    def checked(goal_id, statement, commands, expected_nodes):
        assert statement and commands and expected_nodes == 1
        replayed.append(goal_id)
        return True

    monkeypatch.setattr(ACCEPTANCE, "_kernel_replay", checked)
    training_rows = _stub_sealed_wmi(monkeypatch, manifest)
    monkeypatch.setattr(
        ACCEPTANCE,
        "_require_dataset_generator_terminal",
        lambda _chain: dict(ACCEPTANCE.WMI_DATASET_GENERATOR_EVIDENCE),
    )
    unit_chain = {
        "generator": training_rows[0],
        "prepare": training_rows[1],
        "train": training_rows[2],
        "eval": training_rows[3],
        "primary": {"job_id": "180001"},
        "scorer": {"job_id": "180002"},
    }
    monkeypatch.setattr(
        ACCEPTANCE,
        "_current_wmi_job",
        lambda _manifest, role: ({"scheduler": "slurm"}, unit_chain),
    )
    identity = {
        "training_manifest_sha256": "a" * 64,
        "adapter_sha256": "b" * 64,
        "tokenizer_sha256": "d" * 64,
        "dataset_sha256": "c" * 64,
        "config_sha256": manifest["subject"]["training_contract"]["config_sha256"],
        "environment_sha256": manifest["subject"]["authority"][
            "environment_sha256"
        ],
        "base_snapshot_sha256": manifest["subject"]["base_model"]["snapshot"][
            "snapshot_sha256"
        ],
    }
    adapter = ACCEPTANCE.AdapterAuthority(Path("/unit/adapter"), {}, identity)
    primary = ACCEPTANCE.PrimarySession({"session_id": "unit"}, tuple(repl))
    data_audit = {"contamination": 0}
    report = ACCEPTANCE.build_report(
        manifest,
        primary,
        heldout,
        manifest_sha256=hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        adapter=adapter,
        data_audit=data_audit,
    )

    assert replayed == [
        goal["id"] for goal in manifest["goals"] if goal["id"] in successes
    ]
    assert report["binary_pass"] is True
    assert report["integrity"]["passed"] is True
    assert report["adapter"] == identity


def test_sealed_goal_hash_is_the_real_model_v2_evaluator_hash() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    _, heldout = _synthetic_reports(manifest, set())
    real_goals = TRAINED_EVALUATOR._benchmark_goals_for_environment(
        EVALUATOR.DEFAULT_HELD_OUT_GOALS,
        model_v2_environment(),
    )

    assert heldout["goal_set_sha256"] == EVALUATOR._goal_set_sha256(real_goals)
    assert heldout["goal_set_sha256"] != EVALUATOR.HELD_OUT_GOAL_SET_SHA256


def test_sealed_report_rejects_forged_aggregate_accounting(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    _stub_sealed_wmi(monkeypatch, manifest)
    _, heldout = _synthetic_reports(manifest, set())
    heldout["search"]["actual"]["candidates_executed"] += 1

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="aggregate accounting"):
        ACCEPTANCE._sealed_outcomes(
            manifest["goals"][12:],
            heldout,
            manifest,
            _identity(manifest),
        )


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("states_discovered", 3),
        ("frontier_peak", 2),
        ("candidates_executed", 5),
    ),
)
def test_search_accounting_rejects_impossible_counter_combinations(
    field: str,
    value: int,
) -> None:
    search = {
        "status": "proof",
        "model_calls": 1,
        "states_expanded": 1,
        "states_discovered": 1,
        "candidates_executed": 1,
        "frontier_peak": 1,
        "depth_reached": 1,
        "commands": ["refl"],
        "diagnostics": [],
    }
    search[field] = value
    budget = {
        "max_model_calls": 128,
        "max_states": 2048,
        "beam_width": 4,
        "max_depth": 32,
        "candidates_per_state": 4,
    }
    with pytest.raises(ACCEPTANCE.AcceptanceError, match="mutually inconsistent"):
        ACCEPTANCE._validate_search_accounting(
            "C1", search, budget, candidate_lines=4
        )


def _valid_row(
    split: str,
    formula: str,
    *,
    state: list[str] | None = None,
    tactic: str = "refl",
) -> dict[str, object]:
    environment = model_v2_environment()
    goals = state or ["⊢ 0 = 0"]
    template = "unit"
    material = json.dumps(
        [4, template, formula], ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")
    root = f"synthetic-v2/{template}/{hashlib.sha256(material).hexdigest()[:20]}"
    values: dict[str, object] = {field: None for field in ROW_FIELDS}
    values.update(
        {
            "v": 1,
            "task": "next_tactic",
            "env": environment.text,
            "surface": "model-v2",
            "environment_sha256": environment.sha256,
            "classical": False,
            "capabilities": environment.capabilities.to_record(),
            "split": split,
            "session": "unit-session",
            "step": 1,
            "formula": formula,
            "theorem": f"synthetic.{template}.{root.rsplit('/', 1)[-1]}",
            "family": root,
            "lineage": root,
            "state": goals,
            "focus": 0,
            "prompt": render_prompt(goals=goals, focus=0, environment=environment),
            "completion": f"{tactic}</tactic>",
            "metadata": {
                "library_identity_sha256": environment.library_sha256,
                "statement": formula,
                "statement_sha256": hashlib.sha256(formula.encode()).hexdigest(),
                "template": template,
                "root": root,
                "tactics": [tactic],
                "tactic_rows": 1,
            },
        }
    )
    return values


def test_split_audit_rejects_alpha_equivalent_synthesis_target(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    target = manifest["goals"][3]
    # Binder spelling differs from C1, but the de Bruijn formula is identical.
    alpha = _canonical("forall a b c. a = b -> b = c -> S a = S c")
    path = tmp_path / "train.jsonl"
    payload = (json.dumps(_valid_row("train", alpha)) + "\n").encode("utf-8")
    path.write_bytes(payload)
    formula, names = parse_formula_with_names(target["statement"])
    assert names == ()

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="C1"):
        ACCEPTANCE._scan_dataset_split(
            path,
            "train",
            {"rows": 1, "sha256": hashlib.sha256(payload).hexdigest()},
            {formula: "C1"},
        )


def test_split_audit_rejects_target_hidden_only_in_state_and_prompt(
    tmp_path: Path,
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    target = manifest["goals"][3]
    alpha_target = _canonical("forall a b c. a = b -> b = c -> S a = S c")
    root = _canonical("0 = 0")
    row = _valid_row("train", root, state=[f"⊢ {alpha_target}"])
    path = tmp_path / "train.jsonl"
    payload = (json.dumps(row) + "\n").encode("utf-8")
    path.write_bytes(payload)
    formula, names = parse_formula_with_names(target["statement"])
    assert names == ()

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="C1@row-state"):
        ACCEPTANCE._scan_dataset_split(
            path,
            "train",
            {"rows": 1, "sha256": hashlib.sha256(payload).hexdigest()},
            {formula: "C1"},
        )


def test_goal_scan_keeps_rigid_hypothesis_when_another_surface_has_metavariable() -> None:
    forbidden, names = parse_formula_with_names("1 = 1")
    assert names == ()

    collisions = ACCEPTANCE._scan_goal_targets(
        ["h : 1 = 1, q : ?t1 = 0 ⊢ ?t1 = 0"],
        {forbidden: "X"},
        label="unit-goal",
    )

    assert "X@unit-goal[0].hypothesis[0]" in collisions


def test_goal_scan_keeps_rigid_target_subtree_beside_metavariable() -> None:
    forbidden, names = parse_formula_with_names("1 = 1")
    assert names == ()

    collisions = ACCEPTANCE._scan_goal_targets(
        ["⊢ ?t1 = 0 ∧ 1 = 1"],
        {forbidden: "X"},
        label="flexible-target",
    )

    assert "X@flexible-target[0].target" in collisions


def test_goal_scan_closes_target_under_only_rigid_hypotheses() -> None:
    forbidden, names = parse_formula_with_names("(0 = 0) → (1 = 1)")
    assert names == ()

    collisions = ACCEPTANCE._scan_goal_targets(
        ["h : 0 = 0, q : ?t1 = 0 ⊢ 1 = 1 ∧ 2 = 2"],
        {forbidden: "X"},
        label="mixed-context",
    )

    assert "X@mixed-context[0].intro-closed" in collisions


@pytest.mark.parametrize(
    ("goal", "forbidden_source", "surface"),
    (
        (
            "x : ℕ ⊢ x = x ∧ 0 = 0",
            "∀ x. x = x",
            "target-variable-closed",
        ),
        (
            "h : 0 = 0 ⊢ 1 = 1 ∧ 2 = 2",
            "(0 = 0) → (1 = 1)",
            "intro-closed",
        ),
    ),
)
def test_goal_scan_closes_each_embedded_occurrence_under_its_scope(
    goal: str,
    forbidden_source: str,
    surface: str,
) -> None:
    forbidden, names = parse_formula_with_names(forbidden_source)
    assert names == ()

    collisions = ACCEPTANCE._scan_goal_targets(
        [goal], {forbidden: "X"}, label="scoped-goal"
    )

    assert f"X@scoped-goal[0].{surface}" in collisions


def test_split_audit_rejects_target_as_a_wrapped_formula_subtree(
    tmp_path: Path,
) -> None:
    target, names = parse_formula_with_names("1 = 1")
    assert names == ()
    row = _valid_row("train", _canonical("1 = 1 → 1 = 1"))
    path = tmp_path / "train.jsonl"
    payload = (json.dumps(row) + "\n").encode("utf-8")
    path.write_bytes(payload)

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="X@root"):
        ACCEPTANCE._scan_dataset_split(
            path,
            "train",
            {"rows": 1, "sha256": hashlib.sha256(payload).hexdigest()},
            {target: "X"},
        )


def test_split_audit_closes_each_root_occurrence_under_formula_binders(
    tmp_path: Path,
) -> None:
    forbidden, names = parse_formula_with_names("∀ x. x = x")
    assert names == ()
    row = _valid_row("train", _canonical("∀ x. x = x ∧ 0 = 0"))
    path = tmp_path / "train.jsonl"
    payload = (json.dumps(row) + "\n").encode("utf-8")
    path.write_bytes(payload)

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="X@root"):
        ACCEPTANCE._scan_dataset_split(
            path,
            "train",
            {"rows": 1, "sha256": hashlib.sha256(payload).hexdigest()},
            {forbidden: "X"},
        )


def test_split_audit_rejects_have_under_tacticals_using_row_scope(
    tmp_path: Path,
) -> None:
    target, names = parse_formula_with_names("∀ x y. y = x")
    assert names == ()
    tactic = "first [refl | all_goals (have leak : y = x; refl)]"
    row = _valid_row(
        "train",
        _canonical("0 = 0"),
        state=["x : ℕ, y : ℕ ⊢ 0 = 0"],
        tactic=tactic,
    )
    path = tmp_path / "train.jsonl"
    payload = (json.dumps(row) + "\n").encode("utf-8")
    path.write_bytes(payload)

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="X@completion"):
        ACCEPTANCE._scan_dataset_split(
            path,
            "train",
            {"rows": 1, "sha256": hashlib.sha256(payload).hexdigest()},
            {target: "X"},
        )


def test_completion_uses_only_focused_context_with_unrelated_metagoal(
    tmp_path: Path,
) -> None:
    forbidden, names = parse_formula_with_names("2 = 2")
    assert names == ()
    row = _valid_row(
        "train",
        _canonical("0 = 0"),
        state=["x : ℕ ⊢ 0 = 0", "q : ?t1 = 0 ⊢ ?t1 = 0"],
        tactic="have local : x = x",
    )
    path = tmp_path / "train.jsonl"
    payload = (json.dumps(row) + "\n").encode("utf-8")
    path.write_bytes(payload)

    assert ACCEPTANCE._scan_dataset_split(
        path,
        "train",
        {"rows": 1, "sha256": hashlib.sha256(payload).hexdigest()},
        {forbidden: "X"},
    )["contamination"] == 0


def test_context_closure_ignores_only_flexible_hypotheses() -> None:
    forbidden, names = parse_formula_with_names("2 = 2")
    assert names == ()

    assert ACCEPTANCE._scan_tactic_propositions(
        ("have local : x = x",),
        {forbidden: "X"},
        label="unit",
        contexts=((('x',), ('?t1 = 0',)),),
    ) == []


def test_local_proposition_scan_closes_each_occurrence_under_hypotheses() -> None:
    forbidden, names = parse_formula_with_names("(0 = 0) → (1 = 1)")
    assert names == ()

    collisions = ACCEPTANCE._scan_tactic_propositions(
        ("have local : 1 = 1 ∧ 2 = 2",),
        {forbidden: "X"},
        label="local",
        contexts=(((), ("0 = 0",)),),
    )

    assert "X@local[0].proposition[0].context-closed[0]" in collisions


def test_allowed_library_surface_scanner_closes_each_binder_occurrence() -> None:
    statement, names = parse_formula_with_names("∀ x. x = x ∧ 0 = 0")
    forbidden, forbidden_names = parse_formula_with_names("∀ y. y = y")
    assert names == forbidden_names == ()

    assert ACCEPTANCE._formula_subtree_collisions(
        statement,
        {forbidden: "X"},
        label="allowed-library:unit",
    ) == ["X@allowed-library:unit"]


def test_formula_bearing_completion_must_not_hide_scope_changes() -> None:
    target, names = parse_formula_with_names("∀ x. x = x")
    assert names == ()
    with pytest.raises(ACCEPTANCE.AcceptanceError, match="split it into separate"):
        ACCEPTANCE._scan_tactic_propositions(
            ("intro x; have leak : x = x; refl",),
            {target: "X"},
            label="completion",
        )


def test_proof_artifacts_scan_singular_diagnostic_commands_per_line(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request_id = "1" * 64
    theorem = _canonical("∀ x. x = x")
    result_root = tmp_path / "results" / "peano-policy" / "user-proofs"
    result_root.mkdir(parents=True)
    report_path = result_root / f"{request_id}.json"
    proof_path = result_root / f"{request_id}.pa"
    report = {
        "goals": [{"statement": theorem}],
        "search": {
            "commands": ["intro x", "have h : x = x"],
            "diagnostics": [{"command": None, "reason": "model_call_limit"}],
        },
    }
    report_path.write_text(json.dumps(report), encoding="utf-8")
    proof_path.write_text(
        f"pa prove {theorem}\nintro x\nhave h : x = x\nqed\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(ACCEPTANCE, "REPOSITORY_ROOT", tmp_path)
    inventory = {
        "files": {
            f"{request_id}.json": "a" * 64,
            f"{request_id}.pa": "b" * 64,
        }
    }
    proof_rows = ({"request_id": request_id},)
    requests = {request_id: {"theorem": theorem}}
    forbidden, names = parse_formula_with_names("2 = 2")
    assert names == ()

    # Separate proof steps must not be collapsed into one synthetic tactic line.
    ACCEPTANCE._validate_proof_result_artifacts(
        proof_rows, requests, inventory, {forbidden: "X"}
    )

    report["search"]["diagnostics"] = [
        {"command": "have leaked : 2 = 2", "reason": "rejected"}
    ]
    report_path.write_text(json.dumps(report), encoding="utf-8")
    with pytest.raises(ACCEPTANCE.AcceptanceError, match="X@proof-result"):
        ACCEPTANCE._validate_proof_result_artifacts(
            proof_rows, requests, inventory, {forbidden: "X"}
        )


def test_split_audit_rejects_forged_root_formula_redundancy(tmp_path: Path) -> None:
    row = _valid_row("train", _canonical("0 = 0"))
    row["metadata"]["statement_sha256"] = "0" * 64
    path = tmp_path / "train.jsonl"
    payload = (json.dumps(row) + "\n").encode("utf-8")
    path.write_bytes(payload)

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="redundancy is forged"):
        ACCEPTANCE._scan_dataset_split(
            path,
            "train",
            {"rows": 1, "sha256": hashlib.sha256(payload).hexdigest()},
            {},
        )


def test_report_identity_must_match_recomputed_adapter() -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    base = _base_policy(manifest, "interactive")
    with pytest.raises(ACCEPTANCE.AcceptanceError, match="supplied adapter"):
        ACCEPTANCE._validate_base_policy(
            base,
            manifest,
            runner="interactive",
            adapter_identity={
                "training_manifest_sha256": "f" * 64,
                "adapter_sha256": "e" * 64,
                "dataset_sha256": "d" * 64,
            },
        )


def _identity(manifest: dict[str, object]) -> dict[str, str]:
    return {
        "training_manifest_sha256": "a" * 64,
        "adapter_sha256": "b" * 64,
        "tokenizer_sha256": "d" * 64,
        "dataset_sha256": "c" * 64,
        "config_sha256": manifest["subject"]["training_contract"]["config_sha256"],
        "environment_sha256": manifest["subject"]["authority"][
            "environment_sha256"
        ],
        "base_snapshot_sha256": manifest["subject"]["base_model"]["snapshot"][
            "snapshot_sha256"
        ],
    }


SEALED_TRAINING_SOURCE_FILES = _training_source_hash()["files"]


def _write_json(path: Path, value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    path.write_text(payload, encoding="utf-8")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _training_rows(manifest: dict[str, object]) -> tuple[dict[str, str], ...]:
    generation_commit = manifest["subject"]["training_contract"][
        "dataset_generation_source_commit"
    ]
    commit = "f" * 40
    sync = "2026-07-28T08:00:00Z"
    rows: list[dict[str, str]] = [
        {
            "timestamp": "2026-07-28T00:00:00+00:00",
            "job_id": ACCEPTANCE.WMI_DATASET_GENERATOR_EVIDENCE["job_id"],
            "script": ACCEPTANCE.WMI_DATASET_GENERATOR_SCRIPT,
            "dependency_job_id": "",
            "workdir": ACCEPTANCE.WMI_PROJECT_ROOT,
            "git_commit": generation_commit,
            "git_dirty": "false",
            "sync_timestamp": "2026-07-28T00:00:00Z",
            "script_sha256": ACCEPTANCE.WMI_DATASET_GENERATOR_SCRIPT_SHA256,
        }
    ]
    predecessor = ""
    for offset, script in enumerate(ACCEPTANCE.WMI_TRAINING_SCRIPTS, 1):
        job_id = str(170000 + offset)
        rows.append(
            {
                "timestamp": f"2026-07-28T0{offset}:00:00+00:00",
                "job_id": job_id,
                "script": script,
                "dependency_job_id": predecessor,
                "workdir": ACCEPTANCE.WMI_PROJECT_ROOT,
                "git_commit": commit,
                "git_dirty": "false",
                "sync_timestamp": sync,
                "script_sha256": ACCEPTANCE.WMI_TRAINING_SCRIPT_SHA256[script],
            }
        )
        predecessor = job_id
    return tuple(rows)


def _deployment(row: dict[str, str]) -> dict[str, object]:
    commit = row["git_commit"]
    support_hash = ACCEPTANCE.WMI_TRAINING_SUPPORT_SHA256
    support = {
        "status": "declared",
        "path": "scripts/wmi_job_environment.sh",
        "sha256": support_hash,
        "sourced_sha256": support_hash,
    }
    file_hash = "9" * 64
    source_line = (
        f"{commit}\tfalse\t{row['sync_timestamp']}\n".encode("ascii")
    )
    return {
        "mode": "slurm",
        "source_sync": {
            "status": "synced",
            "path": ".peano-source-provenance.tsv",
            "sha256": hashlib.sha256(source_line).hexdigest(),
            "git_commit": commit,
            "git_dirty": False,
            "synced_at": row["sync_timestamp"],
        },
        "job_script": {
            "status": "declared",
            "path": row["script"],
            "sha256": row["script_sha256"],
            "file_sha256": file_hash,
            "support_script": support,
        },
        "modules": {
            "status": "loaded",
            "requested": "anaconda/2025.12-1",
            "loaded_modules": ["anaconda/2025.12-1"],
        },
        "runtime_declaration": {
            "backend": "wmi",
            "base_environment": "pytorch-gpu",
            "base_manifest": {
                "path": "training/peano_policy/wmi-base-v1.json",
                "sha256": "67311313504c3f67dc12cbe6018812720ff4d925ad656961dcc4d9816306941a",
            },
            "requirements": {
                "path": "training/peano_policy/requirements-wmi-overlay.lock",
                "sha256": "6bcc1633302b2df72a1374e5c5e93f05b483bbb276541551cc471c83c5d3b82d",
            },
        },
        "support_script": support,
    }


def _job_identity(row: dict[str, str], name: str) -> dict[str, object]:
    deployment = _deployment(row)
    return {
        "scheduler": "slurm",
        "job_id": row["job_id"],
        "environment": {
            "SLURM_JOB_NAME": name,
            "SLURM_JOB_ACCOUNT": "unit",
            "SLURM_JOB_PARTITION": "gpu_csi",
            "SLURM_CLUSTER_NAME": "cluster",
            "SLURM_JOB_NODELIST": "g3n1",
            "SLURM_SUBMIT_DIR": ACCEPTANCE.WMI_PROJECT_ROOT,
            "SLURM_JOB_CONSTRAINTS": "vram80g",
            "SLURM_JOB_GRES": "gpu:nvidia_a100:1",
        },
        "deployment": deployment,
        "submission": row,
        "ledger": {
            "path": ACCEPTANCE.WMI_SUBMISSION_LEDGER,
            "row_sha256": ACCEPTANCE._sha256_json(row),
        },
    }


def _stub_sealed_wmi(
    monkeypatch: pytest.MonkeyPatch,
    manifest: dict[str, object],
) -> tuple[dict[str, str], ...]:
    rows = _training_rows(manifest)
    monkeypatch.setattr(ACCEPTANCE, "_load_submission_ledger", lambda _manifest: rows)
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validate_job_identity",
        lambda value, **_kwargs: value,
    )
    return rows


def _adapter_authority_fixture(
    tmp_path: Path,
    manifest: dict[str, object],
) -> Path:
    adapter_dir = tmp_path / "adapter-output"
    weights = adapter_dir / "adapter"
    tokenizer = adapter_dir / "tokenizer"
    weights.mkdir(parents=True)
    tokenizer.mkdir()
    (weights / "adapter_model.safetensors").write_bytes(b"unit-safetensors")
    (weights / "adapter_config.json").write_text("{}\n", encoding="utf-8")
    (tokenizer / "tokenizer.json").write_text("{}\n", encoding="utf-8")

    config = load_config(
        ROOT / manifest["subject"]["training_contract"]["config_path"]
    )
    contract = manifest["subject"]["training_contract"]
    environment = model_v2_environment()
    dataset_manifest_hash = "4" * 64
    train_hash = "5" * 64
    val_hash = "6" * 64
    attestation = {
        "format": "peano-policy-dataset-attestation",
        "v": 1,
        "independent_replay": True,
        "held_out_contamination": 0,
        "held_out_contract": held_out_contract_record(),
        "held_out_contract_sha256": held_out_contract_sha256(),
        "environment": environment_record(environment),
        "prompt_version": PEANO_PROMPT_V2,
        "prompt_contract": prompt_manifest_record(PEANO_PROMPT_V2),
        "prompt_contract_sha256": prompt_contract_sha256(PEANO_PROMPT_V2),
        "library_snapshot_sha256": environment.library_sha256,
        "manifest_sha256": dataset_manifest_hash,
        "dataset_sha256": contract["dataset_sha256"],
        "splits": {
            "train": {"rows": 80_494, "sha256": train_hash},
            "val": {"rows": 9_600, "sha256": val_hash},
            "test": {"rows": 9_906, "sha256": "8" * 64},
        },
    }
    source = {
        "sha256": contract["source_sha256"],
        "files": SEALED_TRAINING_SOURCE_FILES,
    }
    training_row = _training_rows(manifest)[2]
    deployment = _deployment(training_row)
    resolved = json.loads(
        json.dumps(
            {
                "run": asdict(config.run),
                "model": asdict(config.model),
                "data": asdict(config.data),
                "lora": asdict(config.lora),
                "trainer": asdict(config.trainer),
                "generation": asdict(config.generation),
            }
        )
    )
    run_inputs = {
        "train": train_hash,
        "eval": val_hash,
        "train_manifest": dataset_manifest_hash,
        "eval_manifest": dataset_manifest_hash,
        "dataset_attestation": attestation,
    }
    run_identity = {
        "v": 1,
        "config": {
            "path": str(config.path),
            "sha256": manifest["subject"]["training_contract"]["config_sha256"],
            "resolved": resolved,
        },
        "model": {"id": config.model.model_id, "revision": config.model.revision},
        "prompt_version": PEANO_PROMPT_V2,
        "prompt_contract_sha256": prompt_contract_sha256(PEANO_PROMPT_V2),
        "inputs": run_inputs,
        "source": source,
        "base_snapshot": {
            "before_load": expected_base_snapshot(),
            "required_after_load": expected_base_snapshot(),
        },
        "deployment": deployment,
    }
    run_identity_hash = _write_json(
        adapter_dir / ACCEPTANCE.RUN_IDENTITY,
        run_identity,
    )
    training = {
        "v": 1,
        "prompt_version": PEANO_PROMPT_V2,
        "prompt_contract_sha256": prompt_contract_sha256(PEANO_PROMPT_V2),
        "run": asdict(config.run),
        "generation": asdict(config.generation),
        "base_model": {
            "id": config.model.model_id,
            "requested_revision": config.model.revision,
            "resolved_snapshot_hash": config.model.revision,
            "config_sha256": "2" * 64,
        },
        "tokenizer": {
            "resolved_snapshot_hash": config.model.revision,
            "identity_sha256": "3" * 64,
            "artifacts": artifact_directory_hash(adapter_dir, "tokenizer"),
        },
        "adapter": artifact_directory_hash(adapter_dir, "adapter"),
        "inputs": {
            "dataset_attestation": attestation,
            "train_data": {"path": config.data.train_path, "sha256": train_hash},
            "eval_data": {"path": config.data.eval_path, "sha256": val_hash},
            "train_dataset_manifest": {
                "path": "data/peano-policy-v2/manifest.json",
                "sha256": dataset_manifest_hash,
            },
            "eval_dataset_manifest": {
                "path": "data/peano-policy-v2/manifest.json",
                "sha256": dataset_manifest_hash,
            },
            "config": {
                "path": str(config.path),
                "sha256": manifest["subject"]["training_contract"]["config_sha256"],
            },
            "run_identity": {
                "path": f"/unit/{config.run.output_dir}/{ACCEPTANCE.RUN_IDENTITY}",
                "sha256": run_identity_hash,
            },
            "source": source,
            "deployment": deployment,
        },
        "runtime": {
            "torch": "2.5.1",
            "transformers": "4.53.3",
            "peft": "0.16.0",
            "accelerate": "1.8.1",
            "dtype": "bfloat16",
            "attention": "sdpa",
            "resume": {
                "trainer_value": False,
                "checkpoint": None,
                "checkpoint_sha256": None,
                "global_step": None,
            },
            "environment": {
                "implementation": "CPython",
                "python": "3.12.12",
                "machine": "x86_64",
                "platform": "Linux-unit-x86_64-with-glibc2.35",
                "hostname": "g3n1.cluster.wmi.amu.edu.pl",
                "packages": ACCEPTANCE.WMI_RUNTIME_PACKAGES,
                "packages_sha256": ACCEPTANCE._sha256_json(
                    ACCEPTANCE.WMI_RUNTIME_PACKAGES
                ),
                "requirements": {
                    "path": "training/peano_policy/requirements-wmi-overlay.lock",
                    "sha256": "6bcc1633302b2df72a1374e5c5e93f05b483bbb276541551cc471c83c5d3b82d",
                },
                "base_manifest": {
                    "path": "training/peano_policy/wmi-base-v1.json",
                    "sha256": "67311313504c3f67dc12cbe6018812720ff4d925ad656961dcc4d9816306941a",
                },
                "accelerator": {
                    "torch": "2.5.1",
                    "cuda_available": True,
                    "cuda_runtime": "12.4",
                    "cudnn": 90100,
                    "device_name": "NVIDIA A100-SXM4-80GB",
                    "device_capability": [8, 0],
                    "bf16_supported": True,
                    "total_memory": 85_119_205_376,
                    "nvidia_driver": "610.43.02",
                },
            },
            "job": _job_identity(training_row, "peano-wmi-qwen17-v2"),
            "base_snapshot": {
                "before_load": expected_base_snapshot(),
                "after_load": expected_base_snapshot(),
                "after_training": expected_base_snapshot(),
            },
        },
        "metrics": {
            "train": {
                "epoch": 3.0,
                "total_flos": 1.0,
                "train_loss": 0.1,
                "train_runtime": 1.0,
                "train_samples_per_second": 1.0,
                "train_steps_per_second": 1.0,
            },
            "eval": {
                "epoch": 3.0,
                "eval_loss": 0.1,
                "eval_runtime": 1.0,
                "eval_samples_per_second": 1.0,
                "eval_steps_per_second": 1.0,
            },
            "train_examples": 80_494,
            "eval_examples": 4_000,
        },
    }
    _write_json(adapter_dir / ACCEPTANCE.TRAINING_MANIFEST, training)
    return adapter_dir


def test_adapter_authority_checks_actual_artifacts_and_resolved_run_config(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    adapter_dir = _adapter_authority_fixture(tmp_path, manifest)
    monkeypatch.setattr(
        ACCEPTANCE,
        "_subject_adapter_directory",
        lambda _manifest: adapter_dir.resolve(),
    )
    monkeypatch.setattr(
        ACCEPTANCE,
        "_load_submission_ledger",
        lambda _manifest: _training_rows(manifest),
    )
    authority = ACCEPTANCE.validate_adapter_authority(adapter_dir, manifest)
    assert authority.identity["adapter_sha256"]
    assert authority.identity["tokenizer_sha256"]

    training_path = adapter_dir / ACCEPTANCE.TRAINING_MANIFEST
    training = json.loads(training_path.read_text(encoding="utf-8"))
    training["runtime"]["resume"]["trainer_value"] = "checkpoint-250"
    _write_json(training_path, training)
    with pytest.raises(ACCEPTANCE.AcceptanceError, match="fresh WMI run"):
        ACCEPTANCE.validate_adapter_authority(adapter_dir, manifest)
    training["runtime"]["resume"]["trainer_value"] = False
    _write_json(training_path, training)

    run_path = adapter_dir / ACCEPTANCE.RUN_IDENTITY
    run_identity = json.loads(run_path.read_text(encoding="utf-8"))
    run_identity["config"]["resolved"]["lora"]["rank"] += 1
    new_run_hash = _write_json(run_path, run_identity)
    training = json.loads(training_path.read_text(encoding="utf-8"))
    training["inputs"]["run_identity"]["sha256"] = new_run_hash
    _write_json(training_path, training)

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="exact config"):
        ACCEPTANCE.validate_adapter_authority(adapter_dir, manifest)


def test_acceptance_validation_never_depends_on_a_git_checkout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    adapter_dir = _adapter_authority_fixture(tmp_path, manifest)
    monkeypatch.setattr(
        ACCEPTANCE,
        "_subject_adapter_directory",
        lambda _manifest: adapter_dir.resolve(),
    )
    monkeypatch.setattr(
        ACCEPTANCE,
        "_load_submission_ledger",
        lambda _manifest: _training_rows(manifest),
    )
    real_run = ACCEPTANCE.subprocess.run

    def reject_git(command: object, *args: object, **kwargs: object) -> object:
        if (
            isinstance(command, (list, tuple))
            and command
            and command[0] == "git"
        ):
            raise AssertionError("acceptance runtime attempted to invoke Git")
        return real_run(command, *args, **kwargs)

    monkeypatch.setattr(ACCEPTANCE.subprocess, "run", reject_git)
    summary = ACCEPTANCE.validate_manifest(manifest, manifest_path=MANIFEST)
    authority = ACCEPTANCE.validate_adapter_authority(adapter_dir, manifest)

    assert summary["goal_count"] == 16
    assert authority.identity["dataset_sha256"] == manifest["subject"][
        "training_contract"
    ]["dataset_sha256"]
    assert '"git"' not in SCRIPT.read_text(encoding="utf-8")


def test_pretraining_audit_is_fixed_and_must_precede_training(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows = _training_rows(manifest)
    monkeypatch.setattr(ACCEPTANCE, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validated_primary_semantic_source",
        lambda _manifest: {"sha256": "semantic"},
    )
    monkeypatch.setattr(ACCEPTANCE, "_load_submission_ledger", lambda _manifest: rows)
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validate_job_identity",
        lambda value, **_kwargs: value,
    )
    monkeypatch.setattr(
        ACCEPTANCE,
        "_file_timestamps",
        lambda _path: (
            ACCEPTANCE._utc_timestamp("2026-07-28T01:31:00Z", "unit"),
            ACCEPTANCE._utc_timestamp("2026-07-28T01:31:00Z", "unit"),
        ),
    )
    report_path = tmp_path / ACCEPTANCE.WMI_PRETRAIN_DATA_AUDIT
    report_path.parent.mkdir(parents=True)
    snapshot_checks = {
        phase: {
            "path": f"logs/{phase}.json",
            "sha256": str(index) * 64,
            "identity": expected_base_snapshot(),
        }
        for index, phase in enumerate(("before", "after"), 7)
    }
    for phase, created in (
        ("before", "2026-07-28T01:00:00Z"),
        ("after", "2026-07-28T01:20:00Z"),
    ):
        _write_json(
            tmp_path / snapshot_checks[phase]["path"],
            {"created_at": created},
        )
    finalizer_gates = {
        "dataset_attestation": {"sha256": "a" * 64},
        "token_audit": {"sha256": "b" * 64},
        "a100_smoke": {"sha256": "c" * 64},
    }
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validated_finalizer_snapshot_checks",
        lambda _manifest, _row: snapshot_checks,
    )
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validated_finalizer_gate_artifacts",
        lambda _manifest, _row, **_kwargs: finalizer_gates,
    )
    post_audit = {
        "format": "peano-policy-acceptance-data-audit",
        "v": 1,
        "phase": "post-training",
        "dataset_sha256": manifest["subject"]["training_contract"][
            "dataset_sha256"
        ],
        "positive_tactic_rows": 100_000,
        "contamination": 0,
        "compiled_manifest_sha256": "d" * 64,
        "source_manifest_sha256": "e" * 64,
        "attestation_sha256": "f" * 64,
        "forbidden_goal_ids": [
            goal["id"]
            for goal in manifest["goals"]
            if goal["category"] != "retrieval"
        ],
        "splits": {
            name: {"rows": count, "sha256": str(index) * 64}
            for index, (name, count) in enumerate(
                (("train", 80_494), ("val", 9_600), ("test", 9_906)), 3
            )
        },
    }
    pre_audit = dict(post_audit)
    pre_audit["phase"] = "pre-training"
    report = {
        "format": "peano-policy-acceptance-data-pretraining",
        "v": 1,
        "created_at": "2026-07-28T01:30:00Z",
        "preregistration": {
            "id": manifest["preregistration_id"],
            "sha256": ACCEPTANCE.EXPECTED_MANIFEST_SHA256,
        },
        "tool": {
            "name": "peano_policy_acceptance.py",
            "sha256": ACCEPTANCE._sha256_file(Path(ACCEPTANCE.__file__)),
        },
        "primary_semantic_source": {"sha256": "semantic"},
        "training_source_sync": ACCEPTANCE._expected_source_sync(rows[1]),
        "finalizer_job": {"job_id": rows[1]["job_id"]},
        "base_snapshot_checks": snapshot_checks,
        "finalizer_gates": finalizer_gates,
        "data_audit": pre_audit,
    }
    expected_hash = _write_json(report_path, report)
    assert (
        ACCEPTANCE._validate_pretraining_data_report(manifest, post_audit)
        == expected_hash
    )
    adapter = ACCEPTANCE.AdapterAuthority(
        tmp_path / "adapter", {}, _identity(manifest)
    )
    adapter.identity["dataset_sha256"] = manifest["subject"]["training_contract"][
        "dataset_sha256"
    ]
    assert (
        ACCEPTANCE._validate_pretraining_report_identity(manifest, adapter)
        == expected_hash
    )

    report["created_at"] = "2026-07-28T02:00:00Z"
    _write_json(report_path, report)
    with pytest.raises(ACCEPTANCE.AcceptanceError, match="does not predate"):
        ACCEPTANCE._validate_pretraining_data_report(manifest, post_audit)


def test_every_ledgered_proof_request_is_checked_for_acceptance_collision(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from scripts import peano_policy_proof_request as request_tool

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    request_id = "1" * 64
    requests = tmp_path / "results" / "peano-policy" / "requests"
    requests.mkdir(parents=True)
    request_path = requests / f"{request_id}.json"
    request_sha256 = _write_json(
        request_path,
        {"theorem": "∀ z. 0 + z = z"},
    )
    submission = {
        "job_id": "190001",
        "script": "slurm/peano_wmi_prove_theorem.sbatch",
    }
    proof_row = {
        "timestamp": "2026-07-28T03:00:00Z",
        "job_id": "190001",
        "request_id": request_id,
        "request_sha256": request_sha256,
    }
    monkeypatch.setattr(ACCEPTANCE, "REPOSITORY_ROOT", tmp_path)
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validated_primary_semantic_source",
        lambda _manifest: {"sha256": "semantic"},
    )
    monkeypatch.setattr(
        ACCEPTANCE, "_load_submission_ledger", lambda _manifest: (submission,)
    )
    monkeypatch.setattr(
        ACCEPTANCE,
        "_load_proof_request_ledger",
        lambda _manifest: ((proof_row,), "2" * 64),
    )
    monkeypatch.setattr(
        request_tool,
        "load_request",
        lambda _request_id: (
            {"theorem": "∀ z. 0 + z = z"},
            request_path,
            request_sha256,
        ),
    )
    adapter = ACCEPTANCE.AdapterAuthority(tmp_path / "adapter", {}, _identity(manifest))

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="R1"):
        ACCEPTANCE.audit_proof_history(manifest, adapter)


def test_adapter_copy_cannot_create_a_second_primary_run(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    copied_adapter = tmp_path / "copied-adapter"
    copied_adapter.mkdir()

    with pytest.raises(ACCEPTANCE.AcceptanceError, match="one preregistered"):
        ACCEPTANCE.validate_adapter_authority(copied_adapter, manifest)


def _primary_fixture(
    tmp_path: Path,
) -> tuple[
    dict[str, object],
    object,
    dict[str, object],
    Path,
    dict[str, object],
    dict[str, object],
]:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    adapter_dir = tmp_path / "adapter"
    session_dir = adapter_dir / ACCEPTANCE.PRIMARY_SESSION_DIRECTORY
    session_dir.mkdir(parents=True)
    identity = _identity(manifest)
    adapter = ACCEPTANCE.AdapterAuthority(adapter_dir, {}, identity)
    data_audit = {"format": "unit", "contamination": 0}
    proof_history = {"format": "unit-proof-history", "collisions": []}
    semantic_source = manifest["subject"]["primary_semantic_source"]
    snapshot = expected_base_snapshot()
    base_snapshot = {"before_load": snapshot, "after_search": snapshot}
    wmi_job = {"scheduler": "slurm", "job_id": "180001"}
    session_id = ACCEPTANCE._primary_session_id(
        manifest_sha,
        identity,
        data_audit,
        proof_history,
        semantic_source,
        base_snapshot,
        wmi_job,
    )
    started = "2026-07-28T17:00:00Z"
    completed = "2026-07-28T17:01:00Z"
    run = manifest["protocol"]["interactive"]
    open_record = {
        "format": ACCEPTANCE.PRIMARY_SESSION_FORMAT,
        "v": ACCEPTANCE.PRIMARY_SESSION_VERSION,
        "status": "open-non-resumable",
        "session_id": session_id,
        "started_at": started,
        "preregistration_sha256": manifest_sha,
        "adapter": identity,
        "data_audit_sha256": ACCEPTANCE._sha256_json(data_audit),
        "proof_history": proof_history,
        "primary_semantic_source": semantic_source,
        "base_snapshot": base_snapshot,
        "wmi_job": wmi_job,
        "goal_ids": run["goal_ids"],
    }
    open_path = session_dir / ACCEPTANCE.PRIMARY_SESSION_OPEN
    open_hash = _write_json(open_path, open_record)

    reports, _ = _synthetic_reports(manifest, set())
    entries: list[dict[str, object]] = []
    calls = 0
    requested = 0
    for ordinal, (goal, report) in enumerate(
        zip(manifest["goals"][:12], reports, strict=True), 1
    ):
        calls += report["search"]["model_calls"]
        requested += (
            report["search"]["model_calls"]
            * run["search_budget_per_goal"]["candidates_per_state"]
        )
        report["created_at"] = started
        report["generation"] = {
            "model_generate_calls": calls,
            "candidate_sequences_requested": requested,
            "candidate_sequences_returned": requested,
            "candidate_lines_returned": requested,
            "malformed_sequences_rejected": 0,
            "one_batched_call_per_search_state": True,
        }
        stem = f"{ordinal:02d}-{goal['id']}"
        report["artifacts"] = {"report": f"{stem}.json", "proof": None}
        report_hash = _write_json(session_dir / f"{stem}.json", report)
        entries.append(
            {
                "ordinal": ordinal,
                "goal_id": goal["id"],
                "statement": goal["statement"],
                "report_path": f"{stem}.json",
                "report_sha256": report_hash,
                "proof_path": None,
                "proof_sha256": None,
            }
        )
    ledger = {
        "format": ACCEPTANCE.PRIMARY_SESSION_FORMAT,
        "v": ACCEPTANCE.PRIMARY_SESSION_VERSION,
        "status": "complete",
        "session_id": session_id,
        "started_at": started,
        "completed_at": completed,
        "preregistration_sha256": manifest_sha,
        "open_marker": {
            "path": ACCEPTANCE.PRIMARY_SESSION_OPEN,
            "sha256": open_hash,
        },
        "adapter": identity,
        "data_audit": data_audit,
        "proof_history": proof_history,
        "primary_semantic_source": semantic_source,
        "base_snapshot": base_snapshot,
        "wmi_job": wmi_job,
        "protocol": {
            "goal_ids": run["goal_ids"],
            "seed": run["seed"],
            "decoding": run["decoding"],
            "search_budget_per_goal": run["search_budget_per_goal"],
            "one_loaded_adapter": True,
            "attempts_per_goal": 1,
            "resumable": False,
        },
        "goals": entries,
    }
    ledger_path = session_dir / ACCEPTANCE.PRIMARY_SESSION_LEDGER
    _write_json(ledger_path, ledger)
    return manifest, adapter, data_audit, ledger_path, proof_history, wmi_job


def test_primary_ledger_binds_one_ordered_non_resumable_session(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    (
        manifest,
        adapter,
        data_audit,
        ledger_path,
        proof_history,
        wmi_job,
    ) = _primary_fixture(tmp_path)
    monkeypatch.setattr(
        ACCEPTANCE, "audit_proof_history", lambda _manifest, _adapter: proof_history
    )
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validated_primary_semantic_source",
        lambda _manifest: manifest["subject"]["primary_semantic_source"],
    )
    monkeypatch.setattr(ACCEPTANCE, "_load_submission_ledger", lambda _manifest: ())
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validate_acceptance_submission_chain",
        lambda _manifest, _rows, *, require_scorer: {"primary": {"job_id": "180001"}},
    )
    monkeypatch.setattr(
        ACCEPTANCE, "_validate_job_identity", lambda value, **_kwargs: value
    )
    manifest_sha = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    session = ACCEPTANCE.load_primary_session(
        manifest,
        manifest_sha256=manifest_sha,
        adapter=adapter,
        data_audit=data_audit,
    )
    assert len(session.reports) == 12

    first = adapter.directory / ACCEPTANCE.PRIMARY_SESSION_DIRECTORY / "01-R1.json"
    first.write_text(first.read_text(encoding="utf-8") + " ", encoding="utf-8")
    with pytest.raises(ACCEPTANCE.AcceptanceError, match="report hash mismatch"):
        ACCEPTANCE.load_primary_session(
            manifest,
            manifest_sha256=manifest_sha,
            adapter=adapter,
            data_audit=data_audit,
        )
    assert ledger_path.exists()


def test_primary_runner_refuses_any_existing_session_directory(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    manifest, adapter, data_audit, _, _, _ = _primary_fixture(tmp_path)
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validated_primary_semantic_source",
        lambda _manifest: manifest["subject"]["primary_semantic_source"],
    )
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validated_base_snapshot",
        lambda _manifest: expected_base_snapshot(),
    )
    with pytest.raises(ACCEPTANCE.AcceptanceError, match="cannot resume"):
        ACCEPTANCE.run_primary_session(
            manifest,
            manifest_sha256=hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
            adapter=adapter,
            data_audit=data_audit,
        )


def test_primary_runner_loads_once_and_runs_the_frozen_order(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from scripts import peano_policy_repl as repl

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    adapter_dir = tmp_path / "adapter"
    adapter_dir.mkdir()
    identity = _identity(manifest)
    adapter = ACCEPTANCE.AdapterAuthority(adapter_dir, {}, identity)
    data_audit = {"format": "unit", "contamination": 0}
    run = manifest["protocol"]["interactive"]
    runtime_policy = {
        "name": "peano-policy:unit:candidates",
        "kind": "peano-kernel-guided-candidate-policy-v1",
        "base_policy": _base_policy(manifest, "interactive"),
        "seed": run["seed"],
        "seed_schedule": "sha256-json-v1(seed,call_index,canonical_goals)",
        "batching": "one-model-generate-call-per-search-state",
    }

    class Runtime:
        adapter_identity = {"directory": str(adapter_dir), "policy": runtime_policy}

    load_calls: list[dict[str, object]] = []
    theorems: list[str] = []

    def load(_directory: Path, **kwargs: object) -> Runtime:
        load_calls.append(dict(kwargs))
        return Runtime()

    def search(
        theorem: str,
        _runtime: Runtime,
        _budget: object,
        *,
        created_at: str,
    ) -> str:
        assert created_at.endswith("Z")
        theorems.append(theorem)
        return theorem

    def save(attempt: str, directory: Path, *, stem: str) -> object:
        report = directory / f"{stem}.json"
        _write_json(report, {"theorem": attempt})
        return repl.SavedArtifacts(report, None)

    monkeypatch.setattr(repl, "_validated_results_dir", lambda path: path)
    monkeypatch.setattr(repl, "load_model_runtime", load)
    monkeypatch.setattr(repl, "run_checked_search", search)
    monkeypatch.setattr(repl, "save_attempt", save)
    proof_history = {"format": "unit-proof-history", "collisions": []}
    wmi_job = {"scheduler": "slurm", "job_id": "180001"}
    monkeypatch.setattr(
        ACCEPTANCE,
        "_current_wmi_job",
        lambda _manifest, *, role: (wmi_job, {"primary": {"job_id": "180001"}}),
    )
    monkeypatch.setattr(
        ACCEPTANCE, "audit_proof_history", lambda _manifest, _adapter: proof_history
    )
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validated_primary_semantic_source",
        lambda _manifest: manifest["subject"]["primary_semantic_source"],
    )
    monkeypatch.setattr(
        ACCEPTANCE,
        "_validated_base_snapshot",
        lambda _manifest: expected_base_snapshot(),
    )
    ledger_path = ACCEPTANCE.run_primary_session(
        manifest,
        manifest_sha256=hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        adapter=adapter,
        data_audit=data_audit,
    )

    assert len(load_calls) == 1
    assert load_calls[0] == {
        "seed": run["seed"],
        "max_new_tokens": run["decoding"]["max_new_tokens"],
        "sample": run["decoding"]["do_sample"],
        "temperature": run["decoding"]["temperature"],
        "top_p": run["decoding"]["top_p"],
    }
    assert theorems == [goal["statement"] for goal in manifest["goals"][:12]]
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    assert [row["goal_id"] for row in ledger["goals"]] == run["goal_ids"]


def test_retrieval_success_is_replayed_by_the_real_kernel() -> None:
    assert ACCEPTANCE._kernel_replay(
        "R1",
        "∀ x. 0 + x = x",
        ["use zero_add", "exact zero_add"],
        17,
    )
