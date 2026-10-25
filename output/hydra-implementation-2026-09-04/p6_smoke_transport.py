"""One SSH attempt with explicit unknown-outcome receipts on transport timeout."""
import json
import subprocess
import time


def run_ssh(argv, *, input, stdout, stderr, timeout, directory, phase):
    started = time.monotonic()
    try:
        return subprocess.run(argv, input=input, stdout=stdout, stderr=stderr, timeout=timeout)
    except subprocess.TimeoutExpired as failure:
        files = {}
        for label, value in (("stdout", failure.stdout), ("stderr", failure.stderr)):
            raw = value or b""
            if isinstance(raw, str):
                raw = raw.encode()
            maximum = 16 * 1024**2
            name = phase + "-timeout." + label
            with (directory / name).open("xb") as stream:
                stream.write(raw[:maximum])
            files[label] = {"file": name, "retained_bytes": min(len(raw), maximum),
                            "truncated": len(raw) > maximum}
        record = {"schema": "hydra-smoke-transport-timeout-v1", "phase": phase,
                  "actual_ssh_exit_code": None, "remote_outcome": "unknown",
                  "reason": "SSH transport exceeded its explicit wall ceiling",
                  "timeout_seconds": timeout, "elapsed_seconds": time.monotonic() - started,
                  "partial_output": files, "automatic_retry": False,
                  "gpu_charge_refunded": False,
                  "recovery": "Inspect the exact owned remote directory and job; do not repeat this mutation."}
        with (directory / (phase + "-timeout-completion.json")).open("x") as stream:
            json.dump(record, stream, indent=2)
            stream.write("\n")
        print(json.dumps({"phase": phase, "transport_timeout": True,
                          "actual_ssh_exit_code": None, "automatic_retry": False}), flush=True)
        raise SystemExit(124) from failure
