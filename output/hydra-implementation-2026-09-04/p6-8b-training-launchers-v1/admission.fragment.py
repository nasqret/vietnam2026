# Source fragment inserted into the copied P6-v2 local launcher. Not a module
# imported by the launcher; its only runtime dependencies are pinned stdlib
# metadata readers from the sealed 8B smoke package.

SMOKE_PINS = {
    "smoke_launchers.py": "38c6542d762d3bda684d8b53c47cc70e612e263c49fc5d6b151e587ab6721bd2",
    "remote_smoke_control.py": "d01eb31b502da4c45d7038abc0982484a55007462387e8b550a0d0a08d9637d9",
}


def smoke_reader():
    directory = HERE.parent / "p6-8b-smoke-launchers-v1"
    modules, prior = {}, {}
    try:
        for name, filename in (("remote_smoke_control", "remote_smoke_control.py"),
                               ("_conditional_8b_smoke_metadata", "smoke_launchers.py")):
            path = directory / filename
            read(path, SMOKE_PINS[filename], 65536)
            prior[name] = sys.modules.get(name)
            spec = importlib.util.spec_from_file_location(name, path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[name] = module
            spec.loader.exec_module(module)
            modules[name] = module
    finally:
        for name, old in prior.items():
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old
    return modules["_conditional_8b_smoke_metadata"]


def admit_completed_smoke(choice):
    """Only metadata/file admission: no remote query, native import, or model."""
    value = choice["completed_8b_smoke"]
    require(type(value) is dict and set(value) == {"prepared_sha256", "collection"},
            "An exact completed 8B smoke is required before choosing/executing training.")
    collection = value["collection"]
    require(type(collection) is dict and set(collection) == {"response", "transport", "actual_completion"},
            "Missing actual 8B smoke collection receipts.")
    reader = smoke_reader()
    _, prepared, smoke_spec, source_map = reader.load_prepared(value["prepared_sha256"], recheck_pilots=True)
    reader.actual_completion(json.loads(reader.evidence(collection["actual_completion"])))
    transport = json.loads(reader.evidence(collection["transport"]))
    require(transport.get("actual_ssh_exit_code") == 0 and transport.get("owned_child_reaped") is True
            and transport.get("output_complete") is True and transport.get("stop_reason") is None
            and transport.get("remote_script_sha256") == SMOKE_PINS["remote_smoke_control.py"],
            "The actual pinned smoke collection transport is incomplete.")
    response = json.loads(reader.evidence(collection["response"]))
    require(response.get("schema") == "hydra-p6-8b-smoke-control-phase-v1" and response.get("phase") == "collect"
            and response.get("completed") is True and response.get("error") is None, "Smoke collection failed.")
    observation = response["result"]
    reader.validate_observation(observation)
    request = reader.complete_json(observation, "job/result/request.json")
    require(type(request) is dict and type(request.get("reservation")) is dict, "Smoke reservation is missing.")
    record = request["reservation"]
    require(record == reader.control.reservation(smoke_spec, record.get("job_id"), reader.control.UID),
            "Smoke observation is not the fixed 8B base run.")
    summary = reader.summarize(observation, smoke_spec, record, source_map)
    require(summary.get("status") == "complete_base_provider_and_gradient_smoke"
            and summary.get("transport_and_inference_complete") is True and summary.get("gradient_probe_complete") is True
            and summary.get("actual_model_calls") == 2 and summary.get("gradient_examples") == 8
            and summary.get("optimizer_updates") == 0 and summary.get("model_trained") is False,
            "The actual 8B provider/throughput smoke has not completed: " + str(summary.get("errors"))[:1000])
    probe = reader.complete_json(observation, "job/result/throughput.json")
    require(choice["throughput"].get("format") == "json"
            and choice["throughput"].get("sha256") == observation["files"]["job/result/throughput.json"]["sha256"]
            and evidence(choice["throughput"]) == probe, "The duration evidence is not the actual bound 8B probe.")
    return {"schema": "hydra-completed-8b-smoke-before-training-v1", "job_id": record["job_id"],
        "attempt": reader.control.ATTEMPT, "seconds": 600,
        "reservation_sha256": digest(canonical(record) + b"\n"), "smoke_prepared_sha256": value["prepared_sha256"],
        "completion_sha256": observation["files"]["job/result/completion.json"]["sha256"],
        "throughput_sha256": observation["files"]["job/result/throughput.json"]["sha256"],
        "model_admission_sha256": observation["files"]["job/result/model-admission.json"]["sha256"],
        "pilot_evidence": smoke_spec["pilot_evidence"], "source_sha256": SMOKE_PINS,
        "collection": collection, "observed_probe_elapsed_seconds": probe.get("elapsed_seconds"),
        "inferred_training_duration": None, "native_replay_or_model_load_performed": False}


def charge_records():
    patterns = ("p6-training-launchers-v*/attempts/*/release/charge-intent.json",
        "paired-launchers-v*/prepared/arms/*/release/charge-intent.json",
        "p7-teacher-launchers-v*/attempts/*/release/charge-intent.json",
        "p7-student-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-8b-smoke-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-8b-training-launchers-v*/attempts/*/release/charge-intent.json")
    paths = sorted({path for pattern in patterns for path in HERE.parent.glob(pattern)})
    require(len(paths) <= 16, "Unexpected bounded cross-family charge history.")
    return [json.loads(read(path, limit=65536)) for path in paths]


def current_ledger(expected, model_key):
    raw = read(CAMPAIGN_FILE, expected, 2 * 1024**2)
    ledger = json.loads(raw)
    total = ledger_seconds(ledger)
    check_charges(ledger, charge_records())
    target = control.MODELS[model_key]["attempt"]
    require(all(row["attempt"] != target for row in ledger["gpu_reservations"]),
            "This fresh 8B attempt is already in the campaign ledger; no repeat or retry.")
    return ledger, raw, total


def check_completed_predecessor_charges(ledger, admission):
    rows = {row["attempt"]: row for row in ledger["gpu_reservations"]}
    expected = {"p6-training-fresh-1.7b-v2-01": admission["pilot_evidence"]["qwen3-1.7b-base"],
        "p6-training-fresh-4b-v2-01": admission["pilot_evidence"]["qwen3-4b-base"], admission["attempt"]: admission}
    for attempt, previous in expected.items():
        row = rows.get(attempt, {})
        require(all(row.get(key) == previous[key] for key in ("job_id", "seconds", "reservation_sha256"))
                and row.get("allocated_seconds") == previous["seconds"] and row.get("gpus") == 1,
                "Reconcile both completed pilots and the full 8B smoke charge before training.")
