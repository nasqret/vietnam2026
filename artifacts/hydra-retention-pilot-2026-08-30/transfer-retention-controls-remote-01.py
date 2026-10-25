"""Five exclusive retention controls after the actual CPU preflight.

The caller supplies `r`, the exact raw-pinned bootstrap receiver module. Its
descriptor, nofollow, exclusive-write and manual USTAR primitives are reused
unchanged. No received helper is installed. Only the genuine frozen launcher
metadata and source-identity functions are called; no scheduler or model work.
"""
import hashlib
import io
import math
import os
from pathlib import Path
import resource
import signal
import stat
import struct
import sys
import time

C_SOURCE_COMMIT = "4aeae795c8cb5bfc622c9943359b5b38446089b9"
C_BASE_SHA = "40d8391d2d770e509470c81c7a5fe21f0e7ec3a80048e4b70fa9cb0059e6edc2"
C_FILES = tuple(sorted(r.PACKAGE + "/" + name for name in r.LATER_CONTROLS))
C_PREFLIGHT = "_deploy/retention-token-preflight-01.json"
C_CPU_START = "_deploy/retention-token-preflight-started-01.json"
C_CPU_PROCESS = "_deploy/retention-token-preflight-process-01.json"
C_START = "_deploy/retention-controls-started-01.json"
C_RECEIPT = "_deploy/retention-controls-receipt-01.json"
C_REQUEST = r.PACKAGE + "/resource-request.json"
C_APPROVAL = r.PACKAGE + "/approval.json"
C_TOKEN = r.PACKAGE + "/token-preflight.json"
C_CLI = "scripts/execute_peano_hydra_retention.py"
C_MAX_FILE = 4 * 1024**2
C_MAX_TOTAL = 8 * 1024**2
C_MAX_BUNDLE = C_MAX_TOTAL + 65536
C_MAX_PLAN = 65536
C_MAGIC = b"HYDRA-RETENTION-FIVE-CONTROLS-V1\n"
C_LIMITS = {
    "remote_cpu_seconds":45, "remote_wall_seconds":55,
    "remote_address_space_bytes":320 * 1024**2,
    "new_control_files":5, "maximum_control_file_bytes":C_MAX_FILE,
    "maximum_total_control_bytes":C_MAX_TOTAL, "maximum_compressed_bytes":C_MAX_BUNDLE,
    "maximum_plan_bytes":C_MAX_PLAN, "maximum_receipt_bytes":C_MAX_FILE,
    "ssh_wall_seconds":60, "ssh_stdout_bytes":65536, "ssh_stderr_bytes":65536,
    "local_cpu_seconds":60, "local_wall_seconds":90,
    "local_checked_rss_bytes":512 * 1024**2, "automatic_retry":False,
}


def c_pin(raw):
    return {"bytes":len(raw), "sha256":r.sha(raw)}


def c_descriptor(value, path, maximum=C_MAX_FILE):
    r.require(type(value) is dict and set(value) == {"path", "bytes", "sha256"}
              and value["path"] == path, "fixed control/input descriptor required")
    r.descriptor({k:value[k] for k in ("bytes", "sha256")}, mode=False, maximum=maximum)
    r.require(value["bytes"] > 0, "empty control/input metadata")
    return value


def c_validate_plan(raw, expected_sha):
    r.require(type(raw) is bytes and 0 < len(raw) <= C_MAX_PLAN
              and type(expected_sha) is str and r.HEX.fullmatch(expected_sha)
              and r.sha(raw) == expected_sha, "exact external controls-plan raw pin required")
    plan = r.decode(raw, C_MAX_PLAN)
    fields = {"schema", "status", "source_root", "source_commit", "destination_host", "destination_directory",
              "bootstrap_receipt", "remote_cpu_process", "remote_cpu_output", "control_files",
              "control_files_sha256", "control_bytes", "bundle", "execution_identity", "source_header_sha256",
              "finalization_receipt", "helpers", "limits", "job_submission_performed", "model_loaded",
              "native_work_performed", "automatic_retry", "resume"}
    r.require(set(plan) == fields and plan["schema"] == "peano-hydra-retention-controls-transfer-plan-v1"
              and plan["status"] == "prepared-local-only" and plan["source_root"] == r.LOCAL_ROOT
              and plan["source_commit"] == C_SOURCE_COMMIT and plan["destination_host"] == r.HOST
              and plan["destination_directory"] == r.REMOTE_ROOT and plan["limits"] == C_LIMITS,
              "five-control transfer scope changed")
    for key in ("job_submission_performed", "model_loaded", "native_work_performed", "automatic_retry", "resume"):
        r.require(plan[key] is False, "control transfer cannot perform compute, retry or resume")
    c_descriptor(plan["bootstrap_receipt"], r.REMOTE_RECEIPT, r.MAX_JSON)
    c_descriptor(plan["remote_cpu_process"], C_CPU_PROCESS)
    c_descriptor(plan["remote_cpu_output"], C_PREFLIGHT)
    c_descriptor(plan["finalization_receipt"], r.ARCHIVE_ROOT + "/finalize-controls-01.json")
    files = plan["control_files"]
    r.require(type(files) is dict and set(files) == set(C_FILES), "exactly the five new control files are required")
    for name, item in files.items():
        r.relative(name)
        r.descriptor(item, maximum=C_MAX_FILE)
        r.require(item["bytes"] > 0 and item["mode"] == "0600", "controls must be bounded private metadata")
    r.require(type(plan["control_bytes"]) is int
              and plan["control_bytes"] == sum(item["bytes"] for item in files.values()) <= C_MAX_TOTAL
              and plan["control_files_sha256"] == r.sha(r.canonical(files)), "control bytes/inventory digest changed")
    r.require({k:files[C_TOKEN][k] for k in ("bytes", "sha256")}
              == {k:plan["remote_cpu_output"][k] for k in ("bytes", "sha256")},
              "incoming token preflight must equal the actual remote CPU output")
    bundle = plan["bundle"]
    c_descriptor(bundle, r.ARCHIVE_ROOT + "/controls-transfer-01/controls-01.tar.gz", C_MAX_BUNDLE)
    bound = plan["execution_identity"]
    r.require(type(bound) is dict and set(bound) == {"approval_sha256", "resource_request_sha256", "source_commit",
              "source_files_sha256", "payloads_sha256", "synced_at", "job_script_sha256"}
              and bound["source_commit"] == C_SOURCE_COMMIT
              and bound["approval_sha256"] == files[C_APPROVAL]["sha256"]
              and bound["resource_request_sha256"] == files[C_REQUEST]["sha256"]
              and plan["source_header_sha256"] == r.sha(r.canonical(bound)), "exact new source/request header required")
    for key in ("source_files_sha256", "payloads_sha256"):
        r.require(type(bound[key]) is str and r.HEX.fullmatch(bound[key]), "source/payload digest missing")
    r.require(type(bound["synced_at"]) is str and len(bound["synced_at"]) == 20,
              "actual bootstrap provenance timestamp required")
    r.datetime.datetime.strptime(bound["synced_at"], "%Y-%m-%dT%H:%M:%SZ")
    jobs = bound["job_script_sha256"]
    r.require(type(jobs) is dict and set(jobs) == {"train", "evaluate"}
              and all(type(value) is str and r.HEX.fullmatch(value) for value in jobs.values()),
              "both exact frozen job scripts must be identified without launching")
    helpers = plan["helpers"]
    r.require(type(helpers) is dict and set(helpers) == {"sender", "receiver", "bootstrap_sender", "bootstrap_receiver"},
              "exact control and inherited helper pins required")
    for item in helpers.values():
        r.descriptor(item, mode=False, maximum=65536)
        r.require(item["bytes"] > 0, "empty helper")
    r.require(helpers["bootstrap_receiver"]["sha256"] == C_BASE_SHA, "inherited bootstrap primitives changed")
    return plan


def c_validate_header(header, plan=None):
    r.require(type(header) is dict and set(header) == {"schema", "plan_bytes", "plan_sha256", "source_header_sha256",
              "source_commit", "sender_sha256", "receiver_sha256", "bootstrap_receiver_sha256", "started_at_utc", "limits"}
              and header["schema"] == "peano-hydra-retention-controls-transfer-header-v1"
              and type(header["plan_bytes"]) is int and 0 < header["plan_bytes"] <= C_MAX_PLAN
              and header["source_commit"] == C_SOURCE_COMMIT and header["bootstrap_receiver_sha256"] == C_BASE_SHA
              and header["limits"] == C_LIMITS, "controls header changed")
    for key in ("plan_sha256", "source_header_sha256", "sender_sha256", "receiver_sha256"):
        r.require(type(header[key]) is str and r.HEX.fullmatch(header[key]), "raw header binding missing")
    r.require(type(header["started_at_utc"]) is str and len(header["started_at_utc"]) == 20, "actual controls send timestamp required")
    r.datetime.datetime.strptime(header["started_at_utc"], "%Y-%m-%dT%H:%M:%SZ")
    if plan is not None:
        r.require(header["source_header_sha256"] == plan["source_header_sha256"]
                  and header["sender_sha256"] == plan["helpers"]["sender"]["sha256"]
                  and header["receiver_sha256"] == plan["helpers"]["receiver"]["sha256"], "controls helper/source header differs")
    return header


def c_read(tree, name, maximum):
    fd, before = tree.open_file(name)
    os.close(fd)
    r.require(0 < before[4] <= maximum, "bounded metadata input required")
    pin, raw, _ = tree.fingerprint(name, retain=True)
    r.require(0 < pin["bytes"] <= maximum, "metadata grew past bound")
    return raw


def c_check_inventory(tree, files, modes, extra=()):
    r.require(tree.files() == set(files) | set(extra), "remote root contains missing or arbitrary extra files")
    total = 0
    for name, expected in files.items():
        actual, _, info = tree.fingerprint(name)
        total += actual["bytes"]
        r.require(total <= r.MAX_TOTAL and actual == expected
                  and stat.S_IMODE(info[2]) == modes[name], "retained input bytes/mode changed: " + name)
    tree.anchored()


def c_bootstrap_and_cpu(tree, plan):
    bootstrap_raw = c_read(tree, r.REMOTE_RECEIPT, r.MAX_JSON)
    r.require(c_pin(bootstrap_raw) == {k:plan["bootstrap_receipt"][k] for k in ("bytes", "sha256")},
              "actual durable bootstrap receipt changed")
    bootstrap = r.decode(bootstrap_raw)
    r.require(bootstrap.get("schema") == "peano-hydra-retention-bootstrap-receipt-v1"
              and bootstrap.get("status") == "transferred-and-rehashed"
              and bootstrap.get("profile") == r.PROFILE and bootstrap.get("run_id") == r.RUN_ID
              and bootstrap.get("remote_root") == r.REMOTE_ROOT and bootstrap.get("source_root") == r.LOCAL_ROOT
              and bootstrap.get("source_commit") == C_SOURCE_COMMIT and bootstrap.get("local_source_clean") is True
              and bootstrap.get("exact_inventory_checked") is True and bootstrap.get("all_file_hashes_rechecked") is True
              and bootstrap.get("receipt_excluded_from_own_inventory") is True
              and bootstrap.get("receiver_sha256") == C_BASE_SHA,
              "genuine completed bootstrap receipt required")
    for key in ("resource_request_present", "approval_present", "job_submission_performed", "installation_performed",
                "model_loaded", "native_work_performed", "automatic_retry", "resume"):
        r.require(bootstrap.get(key) is False, "bootstrap claimed an ineligible action")
    files, declared_modes = bootstrap.get("files"), bootstrap.get("private_modes")
    r.require(type(files) is dict and 1 <= len(files) <= r.MAX_FILES - 9
              and type(declared_modes) is dict and set(declared_modes) == set(files)
              and bootstrap.get("files_sha256") == r.sha(r.canonical(files))
              and bootstrap.get("file_count") == len(files), "bounded exact bootstrap inventory required")
    modes = {}
    for name, item in files.items():
        r.relative(name)
        r.descriptor(item, mode=False)
        r.require(name not in (*C_FILES, C_PREFLIGHT, C_CPU_PROCESS, C_CPU_START, C_START, C_RECEIPT, r.REMOTE_RECEIPT)
                  and declared_modes[name] in ("0600", "0700"), "bootstrap inventory includes later work")
        modes[name] = int(declared_modes[name], 8)
    r.require(bootstrap.get("total_bytes") == sum(item["bytes"] for item in files.values())
              and r.PROVENANCE in files and C_CLI in files and r.PACKAGE + "/inputs.json" in files,
              "bootstrap source/input/provenance closure changed")
    files = dict(files)
    files[r.REMOTE_RECEIPT], modes[r.REMOTE_RECEIPT] = c_pin(bootstrap_raw), 0o600
    provenance = c_read(tree, r.PROVENANCE, r.MAX_PROVENANCE)
    r.require(provenance == (C_SOURCE_COMMIT + "\tfalse\t" + plan["execution_identity"]["synced_at"] + "\n").encode()
              and bootstrap["source_provenance"] == provenance.decode()
              and bootstrap["source_provenance_sha256"] == r.sha(provenance), "actual bootstrap provenance differs")
    process_raw = c_read(tree, C_CPU_PROCESS, C_MAX_FILE)
    output_raw = c_read(tree, C_PREFLIGHT, C_MAX_FILE)
    start_raw = c_read(tree, C_CPU_START, C_MAX_FILE)
    r.require(c_pin(process_raw) == {k:plan["remote_cpu_process"][k] for k in ("bytes", "sha256")}
              and c_pin(output_raw) == {k:plan["remote_cpu_output"][k] for k in ("bytes", "sha256")},
              "actual remote CPU process/output raw pins changed")
    process, start = r.decode(process_raw, C_MAX_FILE), r.decode(start_raw, C_MAX_FILE)
    expected_request = {"schema":"peano-hydra-retention-tokenizer-cpu-request-v1", "source_commit":C_SOURCE_COMMIT,
        "inputs_sha256":files[r.PACKAGE + "/inputs.json"]["sha256"], "cli_sha256":files[C_CLI]["sha256"],
        "bootstrap_receipt":r.REMOTE_RECEIPT, "bootstrap_receipt_sha256":r.sha(bootstrap_raw)}
    r.require(process.get("schema") == "peano-hydra-retention-cpu-preflight-process-v1"
              and process.get("status") == "passed" and type(process.get("returncode")) is int and process["returncode"] == 0
              and process.get("error") is None and process.get("owned_group_quiescent") is True
              and process.get("remaining_live_owned_processes") == [] and process.get("input_pins_unchanged") is True
              and process.get("completion_requires_zero_exit_and_complete_response") is True
              and process.get("request") == expected_request
              and process.get("preflight") == {"path":r.REMOTE_ROOT + "/" + C_PREFLIGHT, **c_pin(output_raw)}
              and start.get("schema") == "peano-hydra-retention-cpu-preflight-start-v1"
              and start.get("request") == expected_request, "actual CPU preflight was not successful for these exact inputs")
    for record in (process, start):
        for key in ("model_weights_requested", "gpu_allocation_requested", "automatic_retry"):
            r.require(record.get(key) is False, "CPU preflight scope changed")
    limits = {"per_process_cpu_seconds":180, "whole_wall_seconds":300, "sampled_group_rss_bytes":2 * 1024**3,
              "sampled_whole_cpu_seconds":180, "combined_child_output_bytes":256 * 1024, "file_bytes":C_MAX_FILE}
    r.require(process.get("limits") == limits and start.get("limits") == limits, "original CPU preflight bounds changed")
    measured = process.get("measurements", {})
    for key, maximum, strict in (("accounted_whole_cpu_seconds",180,True), ("whole_wall_seconds",300,True),
            ("parent_peak_rss_bytes",2 * 1024**3,False), ("peak_sampled_parent_plus_group_rss_bytes",2 * 1024**3,False)):
        value = measured.get(key)
        r.require(type(value) in (int, float) and math.isfinite(value) and value >= 0
                  and (value < maximum if strict else value <= maximum), "CPU preflight measurement exceeded its declared bound")
    for name, raw in ((C_CPU_START,start_raw),(C_CPU_PROCESS,process_raw),(C_PREFLIGHT,output_raw)):
        files[name], modes[name] = c_pin(raw), 0o600
    r.require(sum(item["bytes"] for item in files.values()) + plan["control_bytes"] + C_MAX_FILE + C_MAX_PLAN <= r.MAX_TOTAL,
              "retained inputs plus all new controls and receipts exceed the aggregate cap")
    c_check_inventory(tree, files, modes)
    return bootstrap, files, modes, output_raw


def c_check_incoming(plan, bootstrap, payloads):
    r.require(set(payloads) == set(C_FILES) and all(c_pin(payloads[name])
              == {k:plan["control_files"][name][k] for k in ("bytes", "sha256")} for name in C_FILES),
              "incoming control raw bytes differ")
    request = r.decode(payloads[C_REQUEST], C_MAX_FILE)
    approval = r.decode(payloads[C_APPROVAL], C_MAX_FILE)
    expected_sources = {name:pin for name,pin in bootstrap["files"].items()
                        if name not in (r.FREEZE_RECEIPT, r.ORIGIN_MANIFEST, r.PROVENANCE)
                        and not name.startswith(r.PACKAGE + "/")}
    expected_payloads = {name:pin for name,pin in bootstrap["files"].items() if name.startswith(r.PACKAGE + "/")}
    expected_payloads.update({name:c_pin(payloads[name]) for name in C_FILES if name not in (C_REQUEST,C_APPROVAL)})
    bound = plan["execution_identity"]
    r.require(request.get("source_commit") == C_SOURCE_COMMIT and request.get("source_files") == expected_sources
              and request.get("payloads") == expected_payloads and request.get("payloads_sha256") == bound["payloads_sha256"]
              and r.sha(r.canonical(expected_sources)) == bound["source_files_sha256"]
              and r.sha(r.canonical(expected_payloads)) == bound["payloads_sha256"]
              and approval.get("request_file_sha256") == r.sha(payloads[C_REQUEST]),
              "five controls do not preserve the exact bootstrap source and package closure")
    for stage in ("train", "evaluate"):
        name = "slurm/peano_hydra_retention_" + stage + ".sbatch"
        r.require(expected_sources[name]["sha256"] == bound["job_script_sha256"][stage], "new header changes frozen job scripts")


def c_frozen_metadata_gate(plan):
    r.require(not os.path.lexists(r.REMOTE_ROOT + "/.git"), "remote control gate must use actual transfer provenance")
    sys.dont_write_bytecode = True
    sys.path.insert(0, r.REMOTE_ROOT)
    from training.peano_hydra import retention_launch as gate
    r.require(str(gate.ROOT) == r.REMOTE_ROOT and str(gate.safe.ROOT) == r.REMOTE_ROOT
              and str(Path(gate.__file__).absolute()) == r.REMOTE_ROOT + "/training/peano_hydra/retention_launch.py",
              "metadata gate did not load the fixed byte-verified frozen source")
    approval_sha = plan["control_files"][C_APPROVAL]["sha256"]
    approval, request = gate.validate_metadata(approval_sha)
    actual = gate.identity(approval, request, approval_sha)
    r.require(actual == plan["execution_identity"] and gate.digest(actual) == plan["source_header_sha256"],
              "genuine frozen metadata/source guard differs from the preregistered new header")
    r.require(not any(name in sys.modules for name in ("torch", "transformers", "peft", "peano_lite", "accelerate")),
              "metadata gate unexpectedly loaded a model or native framework")
    return actual


def c_receive(stream, expected_header_sha, progress):
    r.require(getattr(r, "_pinned_raw_sha256", None) == C_BASE_SHA, "original bootstrap primitive pin unavailable")
    r.require(type(expected_header_sha) is str and r.HEX.fullmatch(expected_header_sha), "external controls-header SHA required")
    r.require(r.exact(stream, len(C_MAGIC)) == C_MAGIC, "controls framing magic changed")
    count = struct.unpack(">Q", r.exact(stream,8))[0]
    r.require(0 < count <= r.MAX_HEADER, "controls header byte bound")
    header_raw = r.exact(stream,count)
    r.require(r.sha(header_raw) == expected_header_sha, "external controls-header pin changed")
    header = c_validate_header(r.decode(header_raw))
    plan_raw = r.exact(stream,header["plan_bytes"])
    plan = c_validate_plan(plan_raw,header["plan_sha256"])
    c_validate_header(header,plan)
    progress.update(plan_sha256=header["plan_sha256"], header_sha256=expected_header_sha,
                    source_header_sha256=plan["source_header_sha256"], source_commit=C_SOURCE_COMMIT)
    tree = r.Tree(r.REMOTE_ROOT)
    try:
        bootstrap, before, modes, output_raw = c_bootstrap_and_cpu(tree,plan)
        # The exact initial inventory excludes every target and this one-use
        # marker. Any partial earlier transfer therefore fails before writing.
        start = {"schema":"peano-hydra-retention-controls-transfer-start-v1", "started_at_utc":r.utc(),
                 "plan_sha256":header["plan_sha256"], "header_sha256":expected_header_sha,
                 "source_header_sha256":plan["source_header_sha256"], "limits":C_LIMITS,
                 "automatic_retry":False, "job_submission_performed":False}
        start_raw = r.canonical(start)+b"\n"
        r.write_stream_file(tree,C_START,c_pin(start_raw),0o600,io.BytesIO(start_raw))
        progress["attempt_started"] = True
        before[C_START], modes[C_START] = c_pin(start_raw),0o600
        payloads = {}
        def consume(name,item,expanded):
            value = r.exact(expanded,item["bytes"])
            r.require(c_pin(value) == {k:item[k] for k in ("bytes","sha256")}, "control tar payload hash differs")
            payloads[name] = value
            r.require(sum(map(len,payloads.values())) <= C_MAX_TOTAL, "in-memory controls exceed total bound")
        tar_result = r.consume_tar(stream,plan["control_files"],consume,plan["bundle"])
        r.require(stream.read(1) == b"", "trailing controls wire bytes")
        c_check_incoming(plan,bootstrap,payloads)
        r.require(payloads[C_TOKEN] == output_raw, "incoming token preflight differs byte-for-byte from actual CPU output")
        # Recheck retained state after the input stream, before all five writes.
        c_check_inventory(tree,before,modes)
        for name in C_FILES:
            item = c_pin(payloads[name])
            r.write_stream_file(tree,name,item,0o600,io.BytesIO(payloads[name]))
            before[name], modes[name] = item,0o600
            progress["control_files_written"] += 1
        identity = c_frozen_metadata_gate(plan)
        c_check_inventory(tree,before,modes)
        receipt = {"schema":"peano-hydra-retention-controls-transfer-receipt-v1", "status":"installed-and-validated",
            "remote_root":r.REMOTE_ROOT, "source_commit":C_SOURCE_COMMIT,
            "plan_sha256":header["plan_sha256"], "header_sha256":expected_header_sha,
            "source_header_sha256":plan["source_header_sha256"], "execution_identity":identity,
            "bootstrap_receipt":plan["bootstrap_receipt"], "remote_cpu_process":plan["remote_cpu_process"],
            "remote_cpu_output":plan["remote_cpu_output"], "control_files":plan["control_files"],
            "control_files_sha256":plan["control_files_sha256"], "control_bytes":plan["control_bytes"],
            "actual_cpu_start":before[C_CPU_START], "started":before[C_START], "bundle":tar_result,
            "retained_input_inventory_sha256":r.sha(r.canonical(before)),
            "all_retained_and_new_bytes_rechecked":True, "exact_inventory_checked":True,
            "genuine_frozen_metadata_and_identity_validated":True, "token_preflight_matches_actual_remote_bytes":True,
            "source_provenance_unchanged":True, "limits":C_LIMITS,
            "job_submission_performed":False, "scheduler_called":False, "installation_performed":False,
            "model_loaded":False, "native_work_performed":False, "automatic_retry":False, "resume":False}
        receipt_raw = r.canonical(receipt)+b"\n"
        r.require(len(receipt_raw) <= C_MAX_FILE, "controls receipt byte cap")
        r.write_stream_file(tree,C_RECEIPT,c_pin(receipt_raw),0o600,io.BytesIO(receipt_raw))
        before[C_RECEIPT], modes[C_RECEIPT] = c_pin(receipt_raw),0o600
        r.require(tree.files() == set(before) and tree.fingerprint(C_RECEIPT)[0] == c_pin(receipt_raw),
                  "final control receipt/inventory differs")
        tree.anchored()
        os.fsync(tree.fd)
        return {"status":"installed-and-validated", "remote_receipt":{"path":C_RECEIPT, **c_pin(receipt_raw)},
                "receipt_record":receipt,
                "execution_identity":identity, "source_header_sha256":plan["source_header_sha256"],
                "bootstrap_receipt":plan["bootstrap_receipt"], "remote_cpu_process":plan["remote_cpu_process"],
                "remote_cpu_output":plan["remote_cpu_output"], "control_files_sha256":plan["control_files_sha256"],
                "control_bytes":plan["control_bytes"], "bundle":tar_result,
                "all_retained_and_new_bytes_rechecked":True, "genuine_frozen_metadata_and_identity_validated":True,
                "exact_inventory_checked":True, "token_preflight_matches_actual_remote_bytes":True}
    finally:
        tree.close()


def controls_main():
    r.require(sys.flags.isolated and sys.dont_write_bytecode and sys.platform == "linux" and len(sys.argv) == 2
              and not os.environ.get("SLURM_JOB_ID"), "isolated Linux metadata receiver outside allocation required")
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU,(45,45))
    resource.setrlimit(resource.RLIMIT_AS,(320 * 1024**2,320 * 1024**2))
    resource.setrlimit(resource.RLIMIT_FSIZE,(C_MAX_FILE,C_MAX_FILE))
    resource.setrlimit(resource.RLIMIT_CORE,(0,0))
    def expired(_signum,_frame):
        raise TimeoutError("whole controls receiver55-second wall deadline")
    signal.signal(signal.SIGALRM,expired)
    signal.alarm(55)
    started = time.monotonic()
    result = {"schema":"peano-hydra-retention-controls-transfer-remote-result-v1", "remote_root":r.REMOTE_ROOT,
        "started_at_utc":r.utc(), "attempt_started":False, "control_files_written":0, "limits":C_LIMITS,
        "job_submission_performed":False, "scheduler_called":False, "model_loaded":False,
        "native_work_performed":False, "automatic_retry":False, "partial_outputs_preserved":True}
    code = 2
    try:
        result.update(c_receive(sys.stdin.buffer,sys.argv[1],result))
        usage = resource.getrusage(resource.RUSAGE_SELF)
        r.require(time.monotonic()-started < 55 and usage.ru_utime+usage.ru_stime < 45
                  and usage.ru_maxrss * 1024 <= 320 * 1024**2, "final controls receiver resource bound reached")
        code = 0
    except BaseException as error:
        result.update(status="failed-partial-output-preserved",error=(type(error).__name__+": "+str(error))[:2048])
    finally:
        usage = resource.getrusage(resource.RUSAGE_SELF)
        result.update(finished_at_utc=r.utc(),wall_seconds=time.monotonic()-started,
                      cpu_seconds=usage.ru_utime+usage.ru_stime,peak_rss_bytes=int(usage.ru_maxrss)*1024)
        raw = r.canonical(result)
        r.require(len(raw) <= 65536, "controls receiver stdout cap")
        print(raw.decode(),flush=True)
        signal.alarm(0)
    raise SystemExit(code)
