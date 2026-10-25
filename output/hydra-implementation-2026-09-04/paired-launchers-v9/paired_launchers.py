"""Selected fresh4B first-attempt phases; all actual inputs are mandatory.

Actual source04 transfer and CPU completion are required. No retry or next arm is selected.

Preparation reads only pinned JSON/source metadata. The frozen evaluator owns
case selection, model admission, proof replay and result interpretation.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
import fcntl
import importlib.util
import json
import math
import os
from pathlib import Path
import secrets
import select
import shlex
import subprocess
import sys
import time

import remote_paired_control as control

HERE = Path(__file__).resolve().parent
ROOT, BASE = HERE.parents[2], HERE.parent
BUNDLE = BASE / "combined-source-bundle-04"
PREPARED = HERE / "prepared"
CAMPAIGN_FILE = BASE / "campaign.json"
LOGIN_PYTHON = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/bin/python3"
LOGIN_PYTHON_LIB = "/net/software/x86_64/el8/Python/3.11.5-GCCcore-13.2.0/lib"
SSH = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
    "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
    "-o", "ClearAllForwardings=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
    "-o", "ControlMaster=no", "-o", "ControlPath=none", "--", "plgnasqret@helios.cyfronet.pl"]
ADMISSION_SHA = "b08722b2ba5bad981f32e79d8e93b90bc93a4130de99f056fc86563a4247fa64"
MONITOR_PROBE_MANIFEST_SHA = 'e73c550efcb63366da304f5e63badbd5741e3a31d07ad9c627c0d78c6190b50a'
require, canonical, digest = control.require, control.canonical, control.digest


def read(path, expected=None, limit=4 * 1024**2):
    raw = control.ordinary_bytes(Path(path), limit)
    if expected is not None:
        require(control.valid_sha(expected) and digest(raw) == expected, "File pin differs: " + str(path))
    return raw


def put(path, value):
    control.save(path, value)
    Path(path).chmod(0o444)


def file_pin(path):
    raw = read(path, limit=control.MAX_RESPONSE)
    return {"path": Path(path).relative_to(ROOT).as_posix(), "bytes": len(raw), "sha256": digest(raw)}


def evidence(item, *, limit=16 * 1024**2):
    require(type(item) is dict and set(item) == {"path", "sha256"}, "Evidence needs exact workspace path and SHA.")
    path = Path(item["path"])
    require(not path.is_absolute() and ".." not in path.parts and path.as_posix() == item["path"], "Evidence path escapes.")
    return read(ROOT / path, item["sha256"], limit)


def actual_completion(record):
    keys = ("actual_exit_code", "actual_process_exit_code", "actual_outer_exit_code", "exit_code")
    exits = [record[key] for key in keys if key in record]
    require(exits and all(type(code) is int and code == 0 for code in exits), "Actual observed process exit0 is required.")
    chunks = [record[key] for key in ("completion_chunk", "actual_completion_chunk", "actual_outer_completion_chunk") if key in record]
    require(chunks and all(type(chunk) is str and chunk for chunk in chunks), "Separately observed completion chunk is required.")


def admission_api():
    path = HERE.parent / "pilot-completion-admission-v3/pilot_admission.py"
    raw = read(path, ADMISSION_SHA, 128 * 1024)
    spec = importlib.util.spec_from_file_location("_explicit_pilot_admission", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module


def admit_training(arm, descriptors, study, api, reader):
    require(arm in {"fresh_1_7b", "fresh_4b"}, "Unknown fresh arm.")
    admission = reader.admit_pilot(control.MODEL_KEYS[arm], descriptors, root=ROOT)
    row = study["arms"][arm]
    require(admission["manifest_sha256"] == row["adapter_manifest_sha256"]
            and admission["artifact_directory"] == row["adapter_directory"]
            and admission["base_directory"] == row["base_directory"]
            and admission["training_exposure"] == study["fresh_training_exposure"],
            "Study uses another saved adapter, path or training exposure.")
    return admission


def bundle_inputs():
    control.require_frozen_bindings()
    manifest = json.loads(read(BUNDLE / "manifest.json", control.MANIFEST_SHA))
    source_map = json.loads(read(BUNDLE / "paired-source-pins.json"))
    require(manifest["archive_sha256"] == control.ARCHIVE_SHA and manifest["file_count"] == 1325
            and len(source_map) == 734 and digest(canonical(source_map)) == control.SOURCE_MAP_SHA,
            "Combined source bundle differs.")
    require(all(manifest["files"].get(name) == value for name, value in source_map.items()), "Combined source inventory differs.")
    return manifest, source_map


def charge_records():
    patterns = ("p6-training-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-8b-smoke-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-8b-training-launchers-v*/attempts/*/release/charge-intent.json",
        "paired-launchers-v*/prepared/arms/*/release/charge-intent.json",
        "p7-teacher-launchers-v*/attempts/*/release/charge-intent.json",
        "p7-student-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-postsave-recovery-v*/attempts/*/release/charge-intent.json")
    paths = sorted({path for pattern in patterns for path in BASE.glob(pattern)})
    require(len(paths) <= 64, "Unexpected bounded cross-campaign charge history.")
    return [json.loads(read(path, limit=65536)) for path in paths]


def current_ledger(expected, arm=None):
    raw = read(CAMPAIGN_FILE, expected, 2 * 1024**2)
    ledger = json.loads(raw)
    total = ledger_seconds(ledger)
    check_charges(ledger, charge_records())
    if arm is not None:
        require(arm in control.SELECTED_ARMS, "Only the fresh4B first attempt is selected.")
        require(all(not row["attempt"].startswith("p6-paired-fresh-4b-") for row in ledger["gpu_reservations"]),
                "A fresh4B paired attempt is already charged; no repeat is selected. Reconcile charges after release.")
    return ledger, raw, total


def make_spec(study, study_sha, arm, nonce):
    spec = {"schema": "hydra-paired-allocation-v1", "arm": arm, "attempt": control.attempt(arm),
        "job_name": "hydra-" + control.attempt(arm), "nonce": nonce,
        "remote_job_directory": control.CAMPAIGN + "/jobs/" + control.attempt(arm), "source": control.SOURCE,
        "account": control.ACCOUNT, "partition": control.PARTITION, "uid": control.UID, "gpus": 1, "nodes": 1,
        "cpus": 8, "memory_gib": 64, "seconds": control.PROFILE_SECONDS[study["wall_profile"]],
        "wall_profile": study["wall_profile"], "study_sha256": study_sha,
        "source_archive_sha256": control.ARCHIVE_SHA, "source_manifest_sha256": control.MANIFEST_SHA,
        "source_pins_sha256": control.SOURCE_MAP_SHA, "controller_sha256": control.CONTROLLER_SHA,
        "case_worker_sha256": control.WORKER_SHA, "common_sha256": control.COMMON_SHA,
        "holdout_sha256": control.HOLDOUT_SHA, "slice_sha256": control.SLICE_SHA, "scope": "full16", "case_count": 16,
        "submit_held": True, "automatic_retry": False, "resume": False, "requeue": False}
    control.validate_spec(spec)
    return spec


def admit_copy_transfer(response_raw, transport_raw, manifest):
    """Admit only a separately recorded repair; the original stage remains failed."""
    path = BASE / "p6-source04-repair-02/admission.py"
    expected = "e8e20bf90b0cad40a812caaa2b8783e482350805525b12206555e0010d3234ed"
    require(control.valid_sha(expected), "Source04 repair admission is not yet finalized.")
    raw = read(path, expected, 65536)
    spec = importlib.util.spec_from_file_location("_source04_repair_admission", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    module.admit_source04_repair(response_raw, transport_raw, manifest, read_evidence=evidence)


def admit_selection(item):
    expected = {"path": (BASE / "p6-monitor-followup-01/DECISION.json").relative_to(ROOT).as_posix(),
                "sha256": control.SELECTION_SHA}
    require(item == expected, "The exact one-job parent selection is required.")
    record = json.loads(evidence(item, limit=65536))
    require(record["selected_first_arm"] == "fresh_4b" and record["max_new_gpu_jobs"] == 1
            and record["gpu_allocation"] == {"allocated_seconds": 1560, "cpus": 8, "gpus": 1, "memory_gib": 64}
            and record["automatic_next_arm"] is False and record["automatic_retry"] is False,
            "The fixed first-attempt selection differs.")
    return expected


def admit_monitor_probe(item):
    require(control.valid_sha(MONITOR_PROBE_MANIFEST_SHA), "The final CPU probe package is not yet bound.")
    require(type(item) is dict and set(item) == {"report", "actual_completion"},
            "Actual CPU report and separately observed completion are required.")
    manifest_path = ROOT / "output/p6-paired-linux-monitor-probe-02/manifest.json"
    manifest = json.loads(read(manifest_path, MONITOR_PROBE_MANIFEST_SHA, 65536))
    require(manifest.get("schema") == "hydra-linux-monitor-probe-package-v1"
            and manifest["files"]["paired_controller.py"]["sha256"] == control.CONTROLLER_SHA
            and manifest["files"]["paired_common.py"]["sha256"] == control.COMMON_SHA,
            "CPU probe uses another controller or common schema.")
    report_raw = evidence(item["report"], limit=512 * 1024)
    report = json.loads(report_raw)
    actual = json.loads(evidence(item["actual_completion"], limit=65536))
    require(report.get("schema") == "hydra-linux-monitor-probe-result-v1"
            and report.get("passed") is True and report.get("error") is None
            and report.get("sources_unchanged") is True
            and report.get("manifest_sha256") == MONITOR_PROBE_MANIFEST_SHA
            and report.get("controller_sha256") == control.CONTROLLER_SHA
            and report.get("common_sha256") == control.COMMON_SHA
            and report.get("probe_sha256") == manifest["files"]["run_probe.py"]["sha256"]
            and canonical(report.get("limits")) == canonical(manifest["limits"]),
            "The final-controller CPU result is failed, incomplete or differently bound.")
    for key, maximum in (("elapsed_seconds", 30), ("aggregate_cpu_seconds", 10)):
        value = report.get(key)
        require(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum,
                "CPU probe exceeded its selected bound.")
    require(type(report.get("actual_fixture_launches")) is int and report["actual_fixture_launches"] == 2
            and report.get("all_owned_leaders_reaped") is True and report.get("all_groups_quiescent") is True
            and report.get("automatic_retry") is False and report.get("full_pairing_or_proof_checked") is False,
            "Both original CPU fixtures and cleanup must have completed without retry.")
    require(all(type(report.get(key)) is int and report[key] == 0
                for key in ("model_calls", "native_calls", "scheduler_queries_by_probe")),
            "The CPU prerequisite is not a theorem/model experiment.")
    fixtures = report.get("fixtures")
    require(type(fixtures) is list and len(fixtures) == 2, "Two exact CPU fixture receipts are required.")
    for index, row in enumerate(fixtures):
        require(type(row) is dict and type(row.get("index")) is int and row["index"] == index
                and row.get("passed") is True and type(row.get("execution")) is dict,
                "A CPU fixture is missing, reordered or failed.")
        execution = row["execution"]
        require(type(execution.get("exit_code")) is int and execution["exit_code"] == 0
                and execution.get("leader_reaped") is True and execution.get("quiescent") is True
                and execution.get("termination_reason") == "process_exit"
                and type(execution.get("helper_launches")) is int and execution["helper_launches"] == 1,
                "A CPU fixture did not exit cleanly under the unchanged owned-child guard.")
        expected_maps, expected_bytes = ((1, 8 * 1024**2), (8192, 128 * 1024**2))[index]
        ready = row.get("ready")
        require(type(ready) is dict and ready.get("schema") == "hydra-linux-monitor-fixture-ready-v1"
                and ready.get("index") == index and ready.get("pid") == execution.get("pid")
                and ready.get("uid") == control.UID and ready.get("requested_mappings") == expected_maps
                and ready.get("requested_bytes") == expected_bytes
                and type(ready.get("observed_vma_lines")) is int and ready["observed_vma_lines"] >= expected_maps
                and type(execution.get("rss_samples")) is int and execution["rss_samples"] >= 1
                and type(execution.get("peak_sampled_host_rss_bytes")) is int
                and execution["peak_sampled_host_rss_bytes"] >= expected_bytes,
                "The fixed live mapping/RSS observations are missing or different.")
    require(actual.get("schema") == "hydra-linux-monitor-probe-actual-completion-v1"
            and type(actual.get("job_id")) is str and actual["job_id"].isdigit()
            and 1 <= len(actual["job_id"]) <= 20 and actual["job_id"] == report.get("job_id")
            and actual.get("slurm_state") == "COMPLETED" and actual.get("slurm_exit_code") == "0:0"
            and actual.get("controller_sha256") == control.CONTROLLER_SHA
            and actual.get("manifest_sha256") == MONITOR_PROBE_MANIFEST_SHA
            and canonical(actual.get("result")) == canonical({"bytes": len(report_raw), "sha256": digest(report_raw)})
            and canonical(actual.get("allocation")) == canonical(
                {"cpus": 1, "gpus": 0, "nodes": 1, "memory_bytes": 1024**3, "seconds": 60}),
            "Actual CPU process/scheduler completion or result binding is missing.")
    require(all(type(actual.get(key)) is int and actual[key] == 0 for key in
                ("actual_probe_process_exit_code", "actual_collect_tool_exit_code", "actual_collect_ssh_exit_code"))
            and type(actual.get("completion_chunk")) is str and 1 <= len(actual["completion_chunk"]) <= 200,
            "CPU execution and collection need their separately observed successful exits.")
    return {"report": item["report"], "actual_completion": item["actual_completion"],
            "job_id": actual["job_id"], "controller_sha256": control.CONTROLLER_SHA,
            "manifest_sha256": MONITOR_PROBE_MANIFEST_SHA, "model_or_theorem_work": False}


def prepare(args):
    control.require_frozen_bindings()
    choice_raw = read(Path(args.choice).resolve(), args.choice_sha256, 65536)
    choice = json.loads(choice_raw)
    require(type(choice) is dict and set(choice) == {"schema", "study", "wall_profile", "transfer", "historical_manifest", "fresh_training", "selection", "monitor_probe"}
            and choice["schema"] == "hydra-paired-launch-choice-v4" and choice["wall_profile"] == control.SELECTED_PROFILE,
            "An explicit complete root choice is required; null templates cannot prepare.")
    selection = admit_selection(choice["selection"])
    monitor_probe = admit_monitor_probe(choice["monitor_probe"])
    study_raw = evidence(choice["study"], limit=65536)
    study = json.loads(study_raw)
    api = control.validate_study(study, BUNDLE / "source")
    require(study["wall_profile"] == choice["wall_profile"], "Root choice and frozen study differ.")
    manifest, source_map = bundle_inputs()
    require(type(choice["transfer"]) is dict and set(choice["transfer"]) == {"response", "actual_completion"}, "Missing actual combined transfer.")
    response_raw = evidence(choice["transfer"]["response"])
    transport_raw = evidence(choice["transfer"]["actual_completion"])
    admit_copy_transfer(response_raw, transport_raw, manifest)
    historical = evidence(choice["historical_manifest"])
    require(digest(historical) == control.HISTORICAL_SHA and json.loads(historical).get("model_trained") is True,
            "Preserved historical manifest is missing.")
    require(type(choice["fresh_training"]) is dict and set(choice["fresh_training"]) == {"fresh_1_7b", "fresh_4b"},
            "Both actual completed fresh models are required before any arm.")
    reader = admission_api()
    admissions = {arm: admit_training(arm, choice["fresh_training"][arm], study, api, reader) for arm in ("fresh_1_7b", "fresh_4b")}
    require(admissions["fresh_1_7b"]["training_exposure"] == admissions["fresh_4b"]["training_exposure"], "Fresh sizes did not see identical data.")
    ledger, ledger_raw, used = current_ledger(args.ledger_sha256, control.SELECTED_ARMS[0])
    reader.require_pilot_charges(ledger, admissions.values())
    seconds = control.PROFILE_SECONDS[study["wall_profile"]]
    selected_seconds = len(control.SELECTED_ARMS) * seconds
    require(selected_seconds == 1560 and used + selected_seconds <= 21600,
            "The selected one-arm ceiling exceeds the remaining six-hour campaign.")
    PREPARED.mkdir(exist_ok=False)
    with (PREPARED / "study.json").open("xb") as stream:
        stream.write(study_raw)
    (PREPARED / "study.json").chmod(0o444)
    put(PREPARED / "choice.json", choice)
    put(PREPARED / "source-map.json", source_map)
    put(PREPARED / "prepare-ledger.json", ledger)
    specs = {}
    for arm in control.SELECTED_ARMS:
        directory = PREPARED / "arms" / arm
        directory.mkdir(parents=True, exist_ok=False)
        specs[arm] = make_spec(study, digest(study_raw), arm, secrets.token_hex(16))
        put(directory / "allocation-request.json", specs[arm])
        with (directory / "job.sbatch").open("x") as stream:
            stream.write(control.job_script(specs[arm]))
        (directory / "job.sbatch").chmod(0o444)
    prepared = {"schema": "hydra-prepared-paired-launch-v4", "status": "prepared_not_submitted",
        "selected_arms": list(control.SELECTED_ARMS), "selection": selection, "monitor_probe_admission": monitor_probe,
        "choice": file_pin(PREPARED / "choice.json"), "original_choice_sha256": digest(choice_raw),
        "study": file_pin(PREPARED / "study.json"), "specs": specs, "fresh_training_admissions": admissions,
        "historical_manifest_sha256": control.HISTORICAL_SHA, "ledger_before_sha256": digest(ledger_raw),
        "seconds_charged_or_reserved_before": used, "maximum_selected_arm_seconds": selected_seconds,
        "launcher_sources": {name: file_pin(HERE / name) for name in ("paired_launchers.py", "remote_paired_control.py")},
        "training_metadata_reader_pins": reader.PINNED,
        "admission_source": file_pin(BASE / "pilot-completion-admission-v3/pilot_admission.py"), "source_pins_sha256": control.SOURCE_MAP_SHA,
        "model_loaded": False, "native_evaluation": False, "automatic_launch": False, "automatic_retry": False}
    put(PREPARED / "prepared.json", prepared)
    print(json.dumps({"prepared": file_pin(PREPARED / "prepared.json"), "seconds_per_arm": seconds,
        "selected_arm_ceiling_seconds": selected_seconds, "ssh_calls": 0, "allocations": 0}))


def load_prepared(arm, expected):
    control.require(arm in control.SELECTED_ARMS, "Only fresh4B is selected; no next arm or retry.")
    prepared = json.loads(read(PREPARED / "prepared.json", expected))
    require(prepared.get("schema") == "hydra-prepared-paired-launch-v4"
            and prepared.get("selected_arms") == list(control.SELECTED_ARMS)
            and set(prepared["specs"]) == set(control.SELECTED_ARMS)
            and prepared.get("maximum_selected_arm_seconds") == 1560, "Unknown prepared arm or selected ceiling.")
    for name in ("paired_launchers.py", "remote_paired_control.py"):
        require(file_pin(HERE / name) == prepared["launcher_sources"][name], "Launcher changed after preparation.")
    raw = read(PREPARED / "study.json", prepared["study"]["sha256"], 65536)
    study = json.loads(raw)
    api = control.validate_study(study, BUNDLE / "source")
    reader = admission_api()
    require(file_pin(BASE / "pilot-completion-admission-v3/pilot_admission.py") == prepared["admission_source"],
            "Pilot admission helper changed after preparation.")
    choice = json.loads(read(PREPARED / "choice.json", prepared["choice"]["sha256"]))
    require(admit_selection(choice["selection"]) == prepared["selection"]
            and admit_monitor_probe(choice["monitor_probe"]) == prepared["monitor_probe_admission"],
            "The selected CPU prerequisite changed after preparation.")
    admissions = {name: admit_training(name, choice["fresh_training"][name], study, api, reader)
                  for name in ("fresh_1_7b", "fresh_4b")}
    require(admissions == prepared["fresh_training_admissions"], "Pilot admission evidence changed after preparation.")
    spec = prepared["specs"][arm]
    control.validate_spec(spec)
    directory = PREPARED / "arms" / arm
    require(json.loads(read(directory / "allocation-request.json")) == spec
            and read(directory / "job.sbatch") == control.job_script(spec).encode()
            and digest(raw) == spec["study_sha256"], "Prepared arm/study bytes differ.")
    _, source_map = bundle_inputs()
    require(json.loads(read(PREPARED / "source-map.json")) == source_map, "Prepared source map differs.")
    return directory, prepared, spec, source_map, raw.decode()


def execute_phase(directory, payload):
    put(directory / "request.json", payload)
    output, receipt = ssh_once(payload)
    with (directory / "transport.stdout").open("xb") as stream:
        stream.write(output)
    put(directory / "transport-completion.json", receipt)
    require(receipt["actual_ssh_exit_code"] == 0 and receipt["owned_child_reaped"] is True
            and receipt["stop_reason"] is None and receipt["output_complete"] is True,
            "Single SSH attempt failed or is uncertain; preserve evidence and do not retry.")
    response = json.loads(output)
    put(directory / "response.json", response)
    require(response.get("schema") == "hydra-paired-control-phase-v1" and response.get("completed") is True
            and response.get("phase") == payload["phase"], "Remote phase did not complete.")
    return response["result"]


def mutate_phase(args):
    directory, prepared, spec, source_map, study_raw = load_prepared(args.arm, args.prepared_sha256)
    ledger, ledger_raw, used = current_ledger(args.ledger_sha256, args.arm)
    admission_api().require_pilot_charges(ledger, prepared["fresh_training_admissions"].values())
    require(used + spec["seconds"] <= 21600, "Full arm charge exceeds the campaign ceiling.")
    phase_dir = directory / args.action
    phase_dir.mkdir(exist_ok=False)
    put(phase_dir / "ledger-snapshot.json", ledger)
    payload = {"phase": args.action, "spec": spec, "source_map": source_map, "study_raw": study_raw}
    if args.action == "release":
        actual = json.loads(read(directory / "submit-held/transport-completion.json"))
        require(actual["actual_ssh_exit_code"] == 0 and actual["stop_reason"] is None
                and actual["owned_child_reaped"] is True, "Submission transport did not complete.")
        submission = json.loads(read(directory / "submit-held/response.json"))["result"]
        require(submission["held"] is True and submission["released"] is False
                and submission["actual_sbatch_exit_code"] == 0 and submission["uid"] == control.UID, "Exact held submission is missing.")
        record = control.reservation(spec, submission["job_id"])
        put(phase_dir / "reservation.json", record)
        charge = {"schema": "hydra-paired-full-release-charge-v1", "attempt": spec["attempt"], "job_id": record["job_id"],
            "gpus": 1, "seconds": spec["seconds"], "allocated_seconds": spec["seconds"],
            "reservation_sha256": digest(canonical(record) + b"\n"), "status": "release_requested_or_uncertain",
            "ledger_before_sha256": digest(ledger_raw), "seconds_before": used, "seconds_after": used + spec["seconds"],
            "refund_allowed_automatically": False, "automatic_retry": False}
        put(phase_dir / "charge-intent.json", charge)
        payload["reservation"] = record
    put(phase_dir / "phase-intent.json", {"action": args.action, "prepared_sha256": args.prepared_sha256,
        "ledger_sha256": digest(ledger_raw), "one_use": True, "automatic_retry": False})
    result = execute_phase(phase_dir, payload)
    print(json.dumps({"phase": args.action, "result": result, "campaign_file_modified": False, "automatic_next_arm": False}))


def collect(args):
    directory, _, spec, _, _ = load_prepared(args.arm, args.prepared_sha256)
    record = json.loads(read(directory / "release/reservation.json"))
    output = directory / ("observation-" + str(args.index).zfill(3))
    output.mkdir(exist_ok=False)
    observation = execute_phase(output, {"phase": "collect", "spec": spec, "reservation": record})
    require(observation.get("job_id") == record["job_id"] and observation.get("read_only") is True
            and set(observation["files"]) <= set(control.collection_files()), "Wrong collection identity or file paths.")
    total = 0
    for name, row in observation["files"].items():
        raw = control.base64.b64decode(row["base64"], validate=True)
        total += len(raw)
        require(len(raw) == row["bytes"] and digest(raw) == row["sha256"] and total <= control.MAX_OBSERVATION,
                "Collection byte integrity/bound differs.")
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
        target.chmod(0o444)
        row.pop("base64")
    put(output / "observation.json", observation)
    sacct = observation["scheduler"]["sacct"]
    with (output / "sacct.txt").open("x") as stream:
        stream.write(sacct["stdout_stderr"])
    put(output / "terminal-collection.template.json", {"schema": "hydra-paired-terminal-collection-v1",
        "job_id": record["job_id"], "actual_transport_exit_code": 0, "completion_chunk": None,
        "raw_sacct": {"path": "sacct.txt", **{key: file_pin(output / "sacct.txt")[key] for key in ("bytes", "sha256")}}})
    put(output / "collection-summary.json", {"schema": "hydra-paired-observation-v1", "arm": args.arm,
        "job_id": record["job_id"], "observation_complete": True, "study_success_asserted": False,
        "actual_sacct_exit_code": sacct["actual_exit_code"], "actual_sacct_stop_reason": sacct["stop_reason"],
        "files": len(observation["files"]), "bytes": total,
        "partial_files": sorted(name for name, row in observation["files"].items() if not row["complete_file"]),
        "next_step": "Root records actual outer completion chunk in a NEW terminal receipt, then uses frozen paired_summary.py.",
        "automatic_retry": False})
    print(json.dumps({"arm": args.arm, "observation": str(output.relative_to(ROOT)), "files": len(observation["files"]),
        "bytes": total, "study_success_asserted": False, "actual_sacct_exit_code": sacct["actual_exit_code"]}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest="action", required=True)
    prep = subs.add_parser("prepare")
    prep.add_argument("--choice", required=True)
    prep.add_argument("--choice-sha256", required=True)
    prep.add_argument("--ledger-sha256", required=True)
    for action in ("submit-held", "release", "collect"):
        sub = subs.add_parser(action)
        sub.add_argument("--arm", choices=control.SELECTED_ARMS, required=True)
        sub.add_argument("--prepared-sha256", required=True)
        if action == "collect":
            sub.add_argument("--index", type=int, choices=range(1, 129), required=True)
        else:
            sub.add_argument("--ledger-sha256", required=True)
    args = parser.parse_args()
    os.umask(0o077)
    with phase_lock():
        if args.action == "prepare":
            prepare(args)
        elif args.action == "collect":
            collect(args)
        else:
            mutate_phase(args)
    return 0


# Pure ledger / lock / bounded SSH primitives copied from reviewed training v2.

def integer(value, lower, upper, name):
    require(type(value) is int and lower <= value <= upper, "Invalid " + name)
    return value

def ledger_seconds(ledger):
    """Conservative full reservations, never actual short failure elapsed time."""
    require(ledger.get("schema") == "hydra-implementation-campaign-v1"
            and ledger.get("campaign_gpu_hours_ceiling") == 6 and ledger.get("automatic_retry") is False,
            "Campaign authority/ceiling differs.")
    rows = ledger.get("gpu_reservations")
    require(type(rows) is list and len(rows) <= 64, "Invalid bounded campaign ledger.")
    total, attempts, jobs = 0, set(), set()
    for row in rows:
        require(type(row) is dict and type(row.get("attempt")) is str and row["attempt"] not in attempts,
                "Ambiguous campaign attempt.")
        attempts.add(row["attempt"])
        seconds = integer(row.get("seconds"), 1, 21600, "reserved seconds")
        require(type(row.get("gpus")) is int and row["gpus"] == 1, "Only single-GPU campaign rows are admitted.")
        job = row.get("job_id")
        if job is not None:
            require(type(job) is str and control.re.fullmatch(r"[0-9]{1,20}", job) and job not in jobs, "Ambiguous actual job id.")
            jobs.add(job)
        allocated = row.get("allocated_seconds")
        if allocated is not None:
            integer(allocated, 0, seconds, "charged seconds")
        zero = row.get("status") == "preflight_stopped_before_sbatch" and allocated == 0 and job is None
        if not zero:
            require(allocated in (None, seconds), "A submitted, failed or uncertain allocation cannot receive an automatic partial refund.")
            total += seconds
    reported = ledger.get("gpu_hours_allocated")
    require(type(reported) in (int, float) and math.isfinite(reported) and 0 <= reported <= 6, "Invalid allocated-hours total.")
    reserved = integer(ledger.get("gpu_seconds_reserved"), 0, 21600, "campaign reserved seconds")
    total = max(total, math.ceil(reported * 3600 - 1e-7), reserved)
    require(total <= 21600, "Campaign has exceeded its six-GPU-hour ceiling.")
    return total

def check_charges(ledger, charges):
    """Root must reconcile full immutable charges before any later allocation."""
    rows = {row["attempt"]: row for row in ledger["gpu_reservations"]}
    for charge in charges:
        row = rows.get(charge["attempt"], {})
        require(all(row.get(key) == charge[key] for key in ("attempt", "job_id", "seconds", "allocated_seconds", "reservation_sha256")),
                "Reconcile the existing full release charge into campaign.json before another allocation; no refund/retry.")

@contextmanager
def phase_lock():
    # Serializes only these local launchers; root also serializes the overall campaign.
    with (HERE / ".phase.lock").open("ab") as stream:
        fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(stream, fcntl.LOCK_UN)

def ssh_once(payload):
    """One fixed SSH child, nonblocking input/output and a 600-second ceiling."""
    raw = canonical(payload)
    require(len(raw) <= control.MAX_INPUT, "SSH input exceeds its bound.")
    code = read(HERE / "remote_paired_control.py", limit=65536).decode()
    argv = SSH + ["/usr/bin/env " + shlex.quote("LD_LIBRARY_PATH=" + LOGIN_PYTHON_LIB)
                  + " " + shlex.quote(LOGIN_PYTHON) + " -I -B -c " + shlex.quote(code)]
    process, output, offset, started = None, bytearray(), 0, time.monotonic()
    eof = False
    receipt = {"actual_ssh_exit_code": None, "ssh_attempted": False, "owned_child_reaped": False,
        "stop_reason": None, "automatic_retry": False, "remote_script_sha256": digest(code.encode())}
    limit = control.MAX_RESPONSE
    try:
        process = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        receipt["ssh_attempted"] = True
        os.set_blocking(process.stdin.fileno(), False)
        os.set_blocking(process.stdout.fileno(), False)
        eof = False
        while not (eof and process.poll() is not None):
            if time.monotonic() - started >= 600:
                receipt["stop_reason"] = "ssh_wall_limit"
                break
            readable, writable, _ = select.select([] if eof else [process.stdout],
                [process.stdin] if offset < len(raw) else [], [], 0.05)
            if writable:
                offset += os.write(process.stdin.fileno(), raw[offset:offset + 16384])
                if offset == len(raw):
                    process.stdin.close()
            if readable:
                chunk = os.read(process.stdout.fileno(), min(65536, limit + 1 - len(output)))
                if chunk:
                    output.extend(chunk)
                    if len(output) > limit:
                        receipt["stop_reason"] = "ssh_output_limit"
                        break
                else:
                    eof = True
    except BaseException as exc:
        receipt["stop_reason"] = type(exc).__name__ + ": " + str(exc)[:1024]
    finally:
        if process is not None:
            if process.poll() is None:
                process.kill()
            try:
                receipt["actual_ssh_exit_code"] = process.wait(timeout=3)
                receipt["owned_child_reaped"] = True
            except subprocess.TimeoutExpired:
                receipt["stop_reason"] = "ssh_child_not_reaped"
            for pipe in (process.stdin, process.stdout):
                if pipe and not pipe.closed:
                    pipe.close()
        receipt.update(elapsed_seconds=time.monotonic() - started, input_bytes_sent=offset,
                       output_bytes_retained=min(limit, len(output)), output_complete=bool(eof and offset == len(raw) and receipt["stop_reason"] is None and len(output) <= limit),
                       remote_outcome="reported_in_response" if receipt["stop_reason"] is None
                           and receipt["actual_ssh_exit_code"] == 0 and eof else "unknown")
    return bytes(output[:limit]), receipt


if __name__ == "__main__":
    raise SystemExit(main())
