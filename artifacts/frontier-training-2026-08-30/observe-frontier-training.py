#!/usr/bin/env python3
"""One read-only observation of the exact job in an externally pinned receipt."""
import argparse
import importlib.util
import json
from pathlib import Path
import re
import shlex
import sys

ARCHIVE = Path(__file__).absolute().parent
REMOTE = ARCHIVE / "observe-frontier-training-remote.py"
CLIENT = ARCHIVE / "transfer-frontier-training.py"
spec = importlib.util.spec_from_file_location("frontier_transfer_client", CLIENT)
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
r = t.r
JOB = re.compile(r"[1-9][0-9]{0,19}\Z")
OUTPUT = re.compile(r"observation-[a-z0-9][a-z0-9-]{0,47}\.json\Z")
ADAPTER = "results/peano-hydra/qwen3-1.7b-authority-primitive-v28-f64b5f100c9c-frontier-training-v1"


def submitted_record(raw):
    """Only the exact final submitted JSON object is a job reference."""
    receipt = r.decode(raw)
    r.require(receipt.get("returncode") == 0 and receipt.get("timed_out", False) is False
              and type(receipt.get("stdout")) is str and len(receipt["stdout"].encode()) <= 1024**2,
              "successful bounded launch process receipt required")
    lines = [line for line in receipt["stdout"].splitlines() if line.strip()]
    r.require(bool(lines), "empty launch output")
    result = r.decode(lines[-1].encode())
    required = {"status", "profile", "run_id", "jobs", "reserved_gpu_seconds", "maximum_concurrent_gpus",
                "automatic_retry", "resume", "refunds", "ledger", "outputs"}
    r.require(set(result) == required and result["status"] == "submitted"
              and result["profile"] == r.PROFILE and result["run_id"] == r.RUN_ID
              and type(result["jobs"]) is dict and set(result["jobs"]) == {"train"}
              and type(result["jobs"]["train"]) is str and JOB.fullmatch(result["jobs"]["train"])
              and result["reserved_gpu_seconds"] == 7200 and result["maximum_concurrent_gpus"] == 1
              and result["automatic_retry"] is False and result["resume"] is False and result["refunds"] is False
              and result["ledger"] == "logs/hydra-frontier-training-v1.jsonl"
              and result["outputs"] == {"adapter": ADAPTER}, "final launch record is not the exact one-job profile")
    for line in lines[:-1]:
        try:
            earlier = r.decode(line.encode())
        except (ValueError, UnicodeError):
            continue
        r.require(earlier.get("status") != "submitted", "ambiguous multiple submitted records")
    return result


def main(argv=None):
    r.require(sys.flags.isolated and sys.dont_write_bytecode, "run observer with python -I -B")
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument("--launch-receipt", type=Path, required=True)
    parser.add_argument("--launch-sha256", required=True)
    parser.add_argument("--approval-sha256", required=True)
    parser.add_argument("--output", required=True, help="fresh observation-NAME.json inside this archive")
    args = parser.parse_args(argv)
    r.require(r.HEX.fullmatch(args.launch_sha256) and r.HEX.fullmatch(args.approval_sha256), "external raw SHA required")
    r.require(OUTPUT.fullmatch(args.output), "fresh bounded observation filename required")
    launch_path = args.launch_receipt.absolute()
    r.require(launch_path.parent == ARCHIVE, "launch receipt must be an exact file in this archive")
    output = ARCHIVE / args.output
    # Claim a fresh local marker before any network action. No repeated output
    # name can silently poll again or overwrite a failed observation.
    marker = output.with_name(output.stem + "-started.json")
    t.new_json(marker, {"started_at_utc": r.utc(), "launch_sha256": args.launch_sha256,
                       "approval_sha256": args.approval_sha256, "read_only": True,
                       "automatic_retry": False})
    result = {"schema": "peano-hydra-frontier-training-observer-process-v1", "read_only": True,
              "network_contacted": False, "automatic_retry": False, "launch_receipt": str(launch_path),
              "launch_sha256": args.launch_sha256, "approval_sha256": args.approval_sha256,
              "observer_sha256": r.sha(t.read_file(Path(__file__).absolute())),
              "observer_remote_sha256": r.sha(t.read_file(REMOTE)),
              "transfer_client_sha256": r.sha(t.read_file(CLIENT)), **t.helper_pins()}
    try:
        raw = t.read_file(launch_path)
        r.require(r.sha(raw) == args.launch_sha256, "external launch receipt bytes differ")
        outer = r.decode(raw)
        r.require(outer.get("schema") == "peano-hydra-frontier-training-control-invocation-v1"
                  and outer.get("phase") == "submit" and outer.get("approval_sha256") == args.approval_sha256,
                  "launch receipt is not the supplied training approval's submit invocation")
        submitted = submitted_record(raw)
        job = submitted["jobs"]["train"]
        result["job_id"] = job
        program = t.read_file(REMOTE).decode() + "\nmain()\n"
        python_command = "/usr/bin/python3 -I -B -c " + shlex.quote(program) + " " + job + " " + args.approval_sha256
        # Login-shell PATH supplies the site's normal Slurm client commands;
        # the Python body has only the three fixed read-only invocations.
        remote_command = "bash -l -c " + shlex.quote("exec " + python_command)
        command = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                   "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
                   "-o", "ClearAllForwardings=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
                   "-o", "ControlMaster=no", "-o", "ControlPath=none", "--", t.HOST, remote_command]
        result["network_contacted"] = True
        process = t.bounded(command, timeout=60, cwd=str(ARCHIVE))
        process["command"] = command[:-1] + ["<fixed read-only remote program; hash recorded below>"]
        process["remote_program_sha256"] = r.sha(program.encode())
        result["process"] = process
        r.require(process["returncode"] == 0 and process["reason"] == "exited", "observation failed; job state is unknown")
        observation = r.decode(process["stdout"].encode())
        r.require(observation.get("schema") == "peano-hydra-frontier-training-observation-v1"
                  and observation.get("status") == "observed" and observation.get("read_only") is True
                  and observation.get("job_id") == job and observation.get("root") == r.REMOTE_ROOT
                  and observation.get("binding", {}).get("approval_sha256") == args.approval_sha256
                  and observation.get("binding", {}).get("source_commit") == outer.get("source_commit"),
                  "remote observation belongs to another job/approval")
        r.require(t.read_file(launch_path) == raw, "local launch receipt changed during observation")
        result.update(status="observed", observation=observation)
    except BaseException as error:
        result.update(status="observation-failed-unknown", error=(type(error).__name__ + ": " + str(error))[:2000])
    result["finished_at_utc"] = r.utc()
    receipt_sha = t.new_json(output, result)
    print(json.dumps({"status": result["status"], "receipt": str(output), "receipt_sha256": receipt_sha,
                      "job_id": result.get("job_id"), "read_only": True}, sort_keys=True), flush=True)
    return 0 if result["status"] == "observed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
