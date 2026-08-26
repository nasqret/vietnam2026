#!/usr/bin/env python3
"""Independently replay the collected 2026-08-26 Hydra model experiment.

No model framework, GPU, scheduler, or network is used. The collected model
and tokenizer are authenticated as files; mathematical proofs are replayed
from the original benchmark sources through Peano's kernel.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from training.peano_hydra.evaluation import (  # noqa: E402
    MAX_GOAL_EVIDENCE_BYTES,
    MAX_LANE_EVIDENCE_BYTES,
    _canonical,
    _digest,
    _json_object,
    _read_regular,
    _verify_trained_artifacts,
    build_matched_evaluation_plan,
)
from peano_lab.batch import run_proof  # noqa: E402


REPORT_SHA256 = "87085bd544e7121cb1eb41255208c036e74139a4c2c459a69f20b141d60f2689"
ADAPTER_SHA256 = "766b94e1645096840f79499b3b45465c7c29133d2583456e85567bdf5cc2b45f"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def verify(collection: Path) -> dict[str, object]:
    report_path = collection / "evidence" / "matched-alpha-21280018.json"
    raw = _read_regular(report_path, maximum=32 * 1024 * 1024, description="collected report")
    require(hashlib.sha256(raw).hexdigest() == REPORT_SHA256, "collected report file changed")
    report = _json_object(raw, description="collected report")
    unsigned = dict(report)
    evaluation_digest = unsigned.pop("evaluation_sha256")
    require(evaluation_digest == _digest(unsigned), "evaluation digest differs")

    plan = build_matched_evaluation_plan(
        ROOT / "_deploy" / "hydra-posttrain",
        trained_adapter=collection / "model",
    )
    _, _, artifacts = _verify_trained_artifacts(plan)
    require(plan.trained_adapter["manifest_sha256"] == ADAPTER_SHA256, "adapter manifest changed")

    # Only the descriptive path changes when the portable adapter is copied.
    expected = plan.to_dict()
    expected["lanes"]["trained"]["adapter"]["manifest_path"] = (
        report["lanes"]["trained"]["adapter"]["manifest_path"]
    )
    expected.pop("plan_sha256")
    expected["plan_sha256"] = _digest(expected)
    restored = copy.deepcopy(unsigned)
    restored["comparison"] = copy.deepcopy(expected["comparison"])
    for name in ("pretrained", "trained"):
        restored["lanes"][name]["status"] = "not_executed"
        restored["lanes"][name].pop("kernel_checked_proofs")
        restored["lanes"][name].pop("model_generate_calls")
    require(restored == expected, "original evaluation plan or authority differs")

    comparison = report["comparison"]
    require(comparison["status"] == "executed", "model comparison was not executed")
    require(comparison["research_claim_eligible"] is False, "invalid research claim")
    require(set(comparison["lanes"]) == {"pretrained", "trained"}, "unexpected lanes")
    replayed: list[dict[str, object]] = []
    totals: dict[str, tuple[int, int]] = {}
    for name in ("pretrained", "trained"):
        lane = comparison["lanes"][name]
        require(lane["status"] == "executed" and lane["lane"] == name, "invalid lane")
        require(lane["model"] == plan.model, "model identity differs")
        require(lane["epoch_sha256"] == plan.epoch.epoch_sha256, "Alpha epoch differs")
        require(lane["environment_sha256"] == plan.environment["environment_sha256"], "authority differs")
        require(lane["goal_set_sha256"] == plan.goal_set_sha256, "benchmark differs")
        require(lane["matched_budget"] == plan.matched_budget, "search budgets differ")
        require(lane["adapter_attached"] is (name == "trained"), "adapter lane differs")
        provider = lane["provider"]
        require(provider["trained_adapter_artifacts"] == artifacts, "provider artifacts differ")
        require(provider["trained_adapter_manifest_sha256"] == ADAPTER_SHA256, "provider adapter differs")
        require(provider["runtime"] == comparison["provider_runtime"], "lane runtimes differ")
        require(len(lane["goals"]) == len(plan.goals), "goal count differs")
        proofs = calls = retained = 0
        for goal, row in zip(plan.goals, lane["goals"], strict=True):
            require(row["goal"] == goal["name"], "goal order differs")
            evidence = row["evidence"]
            encoded = _canonical(evidence)
            retained += len(encoded)
            require(len(encoded) <= MAX_GOAL_EVIDENCE_BYTES, "goal evidence exceeds bound")
            require(hashlib.sha256(encoded).hexdigest() == row["evidence_sha256"], "evidence digest differs")
            require(evidence["environment"] == plan.environment, "proof authority differs")
            require(evidence["theorem"] == goal["statement"], "proof target differs")
            require(evidence["degraded"] is False, "degraded provider")
            search = evidence["search"]
            require(row["status"] == evidence["status"] == search["status"], "status differs")
            count = row["model_generate_calls"]
            require(type(count) is int and 0 <= count <= plan.limits.max_model_calls, "invalid call count")
            require(count == search["model_calls"] == row["generation"]["model_generate_calls"], "call accounting differs")
            calls += count
            commands = search["commands"]
            require(type(commands) is list and len(commands) <= plan.limits.max_depth, "commands exceed bound")
            require(row["tactic_decisions"] == len(commands), "tactic count differs")
            if row["status"] != "proof":
                require(row["status"] in {"limit", "exhausted"}, "unknown search status")
                require(row["kernel_checked"] is False and not commands and evidence["replay"] is None, "false proof claim")
                continue
            require(row["kernel_checked"] is True, "unchecked proof claim")
            require(_digest(commands) == row["commands_sha256"] == evidence["commands_sha256"], "command digest differs")
            saved = evidence["replay"]
            fresh = run_proof(
                goal["source"], tuple(commands), request_id=saved["id"],
                session_id=saved["session"], classical=False, on_error="stop",
                capabilities=plan.capabilities, trace_byte_limit=MAX_GOAL_EVIDENCE_BYTES,
            )
            require(fresh.kernel_checked and fresh.theorem == goal["statement"], "original-goal replay failed")
            require(fresh.proof_nodes == row["proof_nodes"] == search["certificate_nodes"], "proof size differs")
            require(fresh.to_dict(include_trace=True) == saved, "fresh kernel trace differs")
            proofs += 1
            replayed.append({"lane": name, "goal": goal["name"], "commands": commands, "proof_nodes": fresh.proof_nodes})
        require(retained <= MAX_LANE_EVIDENCE_BYTES and retained == lane["retained_evidence_bytes"], "lane evidence size differs")
        require(proofs == lane["kernel_checked_proofs"], "proof total differs")
        require(calls == lane["model_generate_calls"], "model call total differs")
        require(report["lanes"][name]["kernel_checked_proofs"] == proofs, "lane summary differs")
        totals[name] = proofs, calls
    metrics = {
        "goal_count": len(plan.goals),
        "pretrained_kernel_checked_proofs": totals["pretrained"][0],
        "trained_kernel_checked_proofs": totals["trained"][0],
        "kernel_checked_proof_delta": totals["trained"][0] - totals["pretrained"][0],
        "pretrained_model_generate_calls": totals["pretrained"][1],
        "trained_model_generate_calls": totals["trained"][1],
        "research_claim_eligible": False,
    }
    require(comparison["model_metrics"] == metrics, "comparison totals differ")
    require("torch" not in sys.modules, "verification unexpectedly imported a model framework")
    return {
        "status": "passed", "evaluation_sha256": evaluation_digest,
        "report_file_sha256": REPORT_SHA256, "adapter_manifest_sha256": ADAPTER_SHA256,
        "epoch_sha256": plan.epoch.epoch_sha256, "metrics": metrics,
        "independently_replayed_proofs": replayed, "cuda_initialized": False,
        "research_claim_eligible": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--collection-dir", type=Path, default=ROOT / "results/peano-hydra/helios-21279969")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = verify(args.collection_dir)
    rendered = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    if args.output is not None:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(rendered)
    print(rendered, end="")


if __name__ == "__main__":
    main()
