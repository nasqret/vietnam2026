"""Extract resource facts from preserved receipts; never connects or trains."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path("/Users/bnaskrecki/codex/peano")
OUT = Path(__file__).absolute().parent
OLD = ROOT / "_deploy/hydra-corrective-chain-build-20260828/results/peano-hydra/qwen3-1.7b-authority-primitive-v25-a96223a021ed-corrective-v2/manifest.json"
CENSUS = ROOT / "artifacts/session-recovery-2026-08-30/compact-token-census-01.json"
SEARCH = ROOT / "artifacts/session-recovery-2026-08-30/server/job-21421921-terminal-04.json"
ACCOUNTING = OUT / "historical-resource-accounting-01.txt"


def descriptor(path):
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    output = OUT / "resource-evidence-01.json"
    old, census, search = (json.loads(path.read_text()) for path in (OLD, CENSUS, SEARCH))
    diagnostic = census["diagnostic"]["split_census"]
    metrics = old["metrics"]
    train_seconds = metrics["train"]["train_runtime"]
    dev_seconds = metrics["dev"]["eval_runtime"]
    row_scaled = train_seconds * diagnostic["train"]["rows"] / metrics["training_rows"]
    token_scaled = train_seconds * diagnostic["train"]["sequence_tokens"] / old["token_exposure"]["train"]["sequence"]["total"]
    dev_scaled = dev_seconds * diagnostic["dev"]["rows"] / metrics["development_rows"]
    compute_proxy = max(row_scaled, token_scaled) + dev_scaled + 600
    reported_calls = sum(item["reported_model_generate_calls"] for item in search["checkpoint"]["lanes"].values())
    result = {
        "schema": "peano-hydra-frontier-resource-evidence-v1",
        "created_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "proposal-evidence-not-approval",
        "source_files": {name: descriptor(path) for name, path in
                         (("old_training_manifest", OLD), ("recovered_diagnostic", CENSUS),
                          ("search_job_observation", SEARCH), ("read_only_scheduler_response", ACCOUNTING))},
        "scheduler_response_provenance": {
            "observation_date": "2026-08-30",
            "transport": "read-only ssh tool invocation, exit0; stdout copied verbatim to local evidence",
            "command": ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                        "-o", "ServerAliveInterval=15", "-o", "ServerAliveCountMax=2",
                        "plgnasqret@helios.cyfronet.pl",
                        "sacct -n -P -j 21403485,21403486,21403487 --starttime=2026-08-28 --format=JobIDRaw,JobName%80,State,ExitCode,Elapsed,Timelimit,Start,End,AllocTRES%160,TotalCPU,MaxRSS,TRESUsageInAve%256,TRESUsageInMax%256,WorkDir%4096"],
            "remote_mutations": False, "model_or_proof_execution": False,
            "caveat": "Slurm accounting is recorded telemetry, not independent allocator/peak-memory attestation",
        },
        "completed_training_calibration": {
            "job_id": "21403486", "state": "COMPLETED", "exit_code": "0:0",
            "training_rows": metrics["training_rows"], "development_rows": metrics["development_rows"],
            "optimizer_steps": metrics["actual_optimizer_steps"], "train_seconds": train_seconds,
            "dev_seconds": dev_seconds, "job_elapsed_seconds": 4249,
            "other_job_seconds": 4249 - train_seconds - dev_seconds,
            "train_tokens": old["token_exposure"]["train"]["sequence"],
            "runtime": old["runtime"], "batch_max_rss_kib": 6777664,
            "recorded_gpu_memory_mib": 4824, "reserved_host_memory_gib": 64,
        },
        "proposed_pilot": {
            "train_rows": 12772, "development_rows": 2096, "epochs": 1,
            "optimizer_steps": 1597, "train_sequence_tokens": diagnostic["train"]["sequence_tokens"],
            "dev_sequence_tokens": diagnostic["dev"]["sequence_tokens"],
            "max_sequence_tokens": 682, "max_supervised_tokens": 14,
            "diagnostic_compact_jsonl_bytes": census["diagnostic"]["aggregate_compact_model_jsonl_bytes"],
            "complete_admitted_preflight_performed": False,
            "row_scaled_train_seconds": row_scaled, "token_scaled_train_seconds": token_scaled,
            "row_scaled_dev_seconds": dev_scaled, "setup_validation_publication_allowance_seconds": 600,
            "estimated_job_seconds_with_allowance": compute_proxy,
            "requested_train_hard_seconds": 7200,
            "remaining_margin_seconds_against_proxy": 7200 - compute_proxy,
            "caveat": "Inference from one saved run and unadmitted diagnostic; no timing/completion guarantee or benchmark token-fit claim",
        },
        "evaluation_calibration": {
            "job_id": "21421921", "job_elapsed_seconds": 136,
            "outcome_records": 64, "reported_model_generate_calls": reported_calls,
            "batch_max_rss_kib": 8248128, "recorded_gpu_memory_mib": 4754,
            "requested_cohorts": 2, "goals_per_cohort": 32, "roles": 2, "budgets": [8, 16],
            "outcome_records_requested": 256, "maximum_model_calls": 3072,
            "maximum_call_scaled_wall_proxy_seconds": 136 * 3072 / reported_calls,
            "hard_wall_seconds": 1800, "maximum_shared_soft_seconds": 1500,
            "shutdown_margin_seconds": 180,
            "caveat": "Call-scaled historical diagnostic only; new goal complexity/setup may cause unknown outcomes. Both cohorts share one hard/soft deadline.",
        },
        "request": {
            "train": {"gpus": 1, "cpus": 8, "memory_gib": 64, "seconds": 7200},
            "evaluate": {"gpus": 1, "cpus": 8, "memory_gib": 64, "seconds": 1800},
            "maximum_aggregate_gpu_seconds": 9000, "maximum_concurrent_gpus": 1,
            "automatic_retry": False, "resume": False, "refunds": False,
            "approved": False, "jobs_submitted": 0, "transfer_performed": False,
        },
    }
    with output.open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"output": str(output), "sha256": descriptor(output)["sha256"],
                      "estimated_train_job_seconds": compute_proxy, "requested_gpu_seconds": 9000,
                      "approved": False}, sort_keys=True))


if __name__ == "__main__":
    main()
