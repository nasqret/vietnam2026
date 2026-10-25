"""One owned experimental cancellation, followed by manual native replay."""
from pathlib import Path
import json
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "hydra-playground"
sys.path.insert(0, str(APP))
from evaluate_hybrid import Client, TERMINAL, cancel_owned, require
from evaluate_advanced import source_pins


def main():
    output = Path(__file__).resolve().parent / "p10-http-cancel-01"
    output.mkdir(exist_ok=False)
    started = time.monotonic()
    deadline = started + 60
    signal.alarm(70)
    client = Client("http://127.0.0.1:8767")
    pins = source_pins()
    request = {"theorem":"forall n. n=S n", "search_mode":"symbolic", "search_profile":"deep",
               "max_model_calls":16, "beam_width":4,
               "experimental":{"engine":"sharing-v1", "lemmas":False,
                               "advisers":["sympy","cvc5","egg","e"]}}
    record = {"schema":"hydra-owned-http-cancel-v1", "request":request,
              "automatic_retry":False, "model_calls":0, "gpu_allocations":0, "completed":False}
    identifier, cleanup = None, None
    try:
        status, value = client.request("GET", "/api/status", deadline)
        require(status == 200 and value.get("ok"), "Server was not ready.")
        client.token = value["csrf_token"]
        record["status_before"] = {key:value.get(key) for key in ("ok","active_job","experimental")}
        status, value = client.request("POST", "/api/search", deadline, request)
        require(status == 202 and value.get("ok"), "Owned search was not admitted.")
        identifier = value["job_id"]
        record["job_id"] = identifier
        observed = None
        while time.monotonic() < min(deadline-30, started+20):
            job = client.job(identifier, deadline)
            require(job["state"] not in TERMINAL, "The fixture ended before a cancellation could be checked.")
            if job.get("progress",{}).get("phase") in {"sympy","cvc5","egg","e","vampire"}:
                observed = job
                # The progress event precedes dispatch. This delay allows it
                # to enter the helper, but is not evidence of an actual launch.
                time.sleep(0.15)
                break
            time.sleep(0.05)
        require(observed is not None, "No active adviser phase was observed within the fixture cap.")
        record["job_before_cancel"] = observed
        cleanup = cancel_owned(client, identifier, min(deadline-15, time.monotonic()+15))
        record["cleanup"] = cleanup
        require(cleanup.get("terminal_observed"), "Owned cancellation did not finish.")
        terminal = cleanup["terminal_job"]
        require(terminal["state"] == "cancelled", "Expected the actual cancelled state.")
        execution = terminal.get("execution") or terminal.get("result",{}).get("execution",{})
        record["cancelled_execution"] = execution
        require(execution.get("quiescent") is True, "Worker cleanup did not confirm quiescence.")
        manual = {"theorem":"forall n. n=n", "tactics":["intro","refl"],
                  "experimental":{"engine":"sharing-v1", "lemmas":False}}
        status, value = client.request("POST", "/api/replay", deadline, manual)
        record["manual_replay"] = {"request":manual, "http_status":status, "response":value}
        require(status == 200 and value.get("ok") and value.get("result",{}).get("status") == "proved",
                "The released slot did not complete a fresh manual proof.")
        require(value["result"].get("kernel_checked") is True, "Manual proof omitted the native check.")
        record["completed"] = True
    except BaseException as error:
        record["error"] = {"type":type(error).__name__, "detail":str(error)[:1000]}
        if identifier is not None and not (cleanup and cleanup.get("terminal_observed")):
            record["cleanup_after_error"] = cancel_owned(client, identifier, time.monotonic()+15)
    finally:
        record["elapsed_seconds"] = time.monotonic()-started
        record["source_pins_unchanged"] = source_pins() == pins
        (output/"source-pins.json").write_text(json.dumps(pins,indent=2)+"\n")
        (output/"result.json").write_text(json.dumps(record,indent=2)+"\n")
    print(json.dumps({key:record.get(key) for key in ("completed","job_id","error","elapsed_seconds",
                      "source_pins_unchanged","cancelled_execution")}),flush=True)
    return 0 if record["completed"] and record["source_pins_unchanged"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
