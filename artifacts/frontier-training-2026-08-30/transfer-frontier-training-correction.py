#!/usr/bin/env python3
"""One assessed transport correction for the exact already-approved v1 bundle.

No package regeneration, source edits, new approval, installation, allocation,
resume or automatic retry. V1 helper pins remain historical bundle provenance;
the current client/receiver and successful host diagnosis are pinned separately.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import resource
import shlex
import signal
import struct
import sys

ARCHIVE = Path(__file__).absolute().parent
V1_CLIENT = ARCHIVE / "transfer-frontier-training.py"
spec = importlib.util.spec_from_file_location("preserved_transfer_v1", V1_CLIENT)
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)
r = t.r
RECEIVER = ARCHIVE / "transfer-frontier-training-remote-v2.py"
ATTEMPT = ARCHIVE / "transfer-02"
SCHEMA = "peano-hydra-frontier-training-transport-correction-plan-v2"
INVENTORY_SHA = "e25aeab7944c65c98d4c476db2208070bce6a7e8f29069092874eab9c1eee061"
BUNDLE = {"bytes": 191450787, "sha256": "b3d8d26958f08d9e77680974b79b94085041330919ff859c7b4304bc29932505"}
COMMIT = "b08a6b1303d73217f6cc23800ae15e50b17db792"
REQUEST_SHA = "02e8c485eaee56523b82ce015c0e7478dde19622528c813f9cdf4079eb141feb"
APPROVAL_SHA = "9cc426c7829bba661db24df58d53f036d4f759e0c6548208ca5a25e9737150bd"
RECEIVER_SHA = "b10bf0a801baffeace224d5cd7084332bc4d2ee8df090592ae7c4f0c0849d05a"
PINS = {
    "transfer-frontier-training.py": "faa372fc694a39bb3b13b72d2910dd2dc6dd344b05298127201819da5b051d93",
    "transfer-frontier-training-remote.py": "175b1580fed0156c343224c88fe8376e780e357cbaea1ad224cb3adaaa7d772c",
    "transfer-01/inventory.json": INVENTORY_SHA,
    "transfer-01/send-result.json": "39044852d79b7421fce18d5c537110896d41cd115b12bad4039c9be28eacba7a",
    "explicit-transfer-approval-01.json": "77f6d087bef03c3b4666681b429b66382a9fd79132aeeaa76702867b3023c8ae",
    "transfer-receiver-probe-01.json": "1de11a4aacb27fd3119ade6312b9a2aaf69e7c33ba009a0f60b8c07423886ae9",
    "transfer-receiver-memory-probe-01.json": "dd75137f187be2dbd4953810bb0fee21c2261c79e131d093d5482a1885d6a72e",
    "transfer-receiver-corrected-probe-01.json": "772a444b2110502718631016b359a3f421abd1194b0947328c41fbd87f6f37fd",
    RECEIVER.name: RECEIVER_SHA,
}
LIMITS = {"address_space_bytes": 320 * 1024**2, "remote_cpu_seconds": 45,
          "remote_wall_seconds": 55, "ssh_wall_seconds": 60, "files": 4096,
          "per_file_bytes": 64 * 1024**2, "total_selected_bytes": 512 * 1024**2,
          "automatic_retry": False}


def context():
    """Authenticate historical evidence and the successful actual host probe."""
    data, descriptors = {}, {}
    for name, expected in PINS.items():
        raw = t.read_file(ARCHIVE / name)
        r.require(r.sha(raw) == expected, "pinned correction input changed: " + name)
        descriptors[name] = t.descriptor(raw)
        if name.endswith(".json"):
            data[name] = r.decode(raw)
    inventory = r.validate_inventory(data["transfer-01/inventory.json"])
    r.require(inventory["source_commit"] == COMMIT and inventory["request_sha256"] == REQUEST_SHA
              and inventory["approval_sha256"] == APPROVAL_SHA, "historical package identity differs")
    failure = data["transfer-01/send-result.json"]
    remote = r.decode(failure["ssh_process"]["stdout"].encode())
    r.require(failure.get("status") == "failed-no-automatic-retry" and failure.get("network_contacted") is True
              and failure.get("local_inputs_rechecked") is True and remote.get("destination_created") is False
              and remote.get("files_written") == 0 and remote.get("bytes_written") == 0
              and remote.get("job_submission_performed") is False, "predecessor is not the diagnosed zero-write failure")
    approval = data["explicit-transfer-approval-01.json"]
    r.require(approval.get("approved") is True and approval.get("bundle_sha256") == BUNDLE["sha256"]
              and approval.get("bundle_bytes") == BUNDLE["bytes"] and approval.get("inventory_raw_sha256") == INVENTORY_SHA
              and approval.get("remote_host") == t.HOST and approval.get("remote_root") == r.REMOTE_ROOT
              and approval.get("training_resource_approval_sha256") == APPROVAL_SHA,
              "actual user approval does not cover this exact unchanged transfer")
    probe = data["transfer-receiver-corrected-probe-01.json"]
    r.require(probe.get("returncode") == 0 and probe.get("stderr") == ""
              and probe.get("candidate_receiver_sha256") == RECEIVER_SHA, "successful exact receiver probe missing")
    observation = r.decode(probe["stdout"].encode())
    r.require(observation.get("schema") == "peano-hydra-corrected-transfer-read-only-probe-v1"
              and observation.get("status") == "read-only-control-check-passed"
              and observation.get("inventory_sha256") == INVENTORY_SHA
              and observation.get("inventory_validated") is True
              and observation.get("request_and_approval_validated") is True
              and observation.get("parent_directory_opened") is True
              and observation.get("destination_exists") is False and observation.get("destination_exists_after") is False
              and observation.get("writes_performed") is False and observation.get("job_submission_performed") is False
              and observation.get("address_space_cap_bytes") == LIMITS["address_space_bytes"],
              "host diagnostic did not validate unchanged controls and permission-respecting access")
    prepared = r.decode(t.read_file(ARCHIVE / "transfer-01/prepare-result.json"))
    r.require(prepared.get("status") == "prepared-local-only" and prepared.get("inventory_sha256") == INVENTORY_SHA
              and prepared.get("bundle") == BUNDLE, "original successful bundle preparation differs")
    return inventory, descriptors, observation


def plan_record(inventory, descriptors, diagnostic, stamp):
    return {"schema": SCHEMA, "status": "ready-for-one-assessed-corrected-transport-attempt",
            "profile": r.PROFILE, "run_id": r.RUN_ID, "created_at_utc": stamp,
            "local_root": r.LOCAL_ROOT, "remote_root": r.REMOTE_ROOT, "remote_host": t.HOST,
            "source_commit": COMMIT, "request_sha256": REQUEST_SHA, "approval_sha256": APPROVAL_SHA,
            "original_inventory_sha256": INVENTORY_SHA, "original_bundle": {"path": "transfer-01/bundle.bin", **BUNDLE},
            "file_count": inventory["file_count"], "total_selected_bytes": inventory["total_bytes"],
            "retained_inputs": descriptors,
            "current_client": {"path": Path(__file__).name, **t.descriptor(t.read_file(Path(__file__).absolute()))},
            "current_receiver": {"path": RECEIVER.name, **descriptors[RECEIVER.name]},
            "original_inventory_helper_pins_are_historical": True,
            "corrections": ["receiver RLIMIT_AS: 256 MiB to finite 320 MiB; measured interpreter baseline exceeds 256 MiB",
                            "Linux ancestors: O_PATH|O_DIRECTORY|O_NOFOLLOW; readable leaf: O_RDONLY|O_DIRECTORY|O_NOFOLLOW; unchanged permission checks"],
            "diagnostic": diagnostic, "limits": LIMITS, "attempt_directory": ATTEMPT.name,
            "original_source_package_and_bundle_unchanged": True, "new_approval_created": False,
            "gpu_or_native_worker_limits_changed": False, "scheduler_operations": False,
            "automatic_retry": False, "partial_outputs_preserved": True}


def make_attempt():
    fd = r.directory(str(ARCHIVE))
    try:
        os.mkdir(ATTEMPT.name, 0o700, dir_fd=fd)
        os.fsync(fd)
    finally:
        os.close(fd)


def plan():
    make_attempt()
    t.new_json(ATTEMPT / "plan-started.json", {"started_at_utc": r.utc(), "network_contacted": False,
               "original_inventory_sha256": INVENTORY_SHA, "original_bundle": BUNDLE, "automatic_retry": False})
    result = {"schema": "peano-hydra-frontier-training-correction-plan-result-v2", "network_contacted": False}
    tree = None
    try:
        inventory, descriptors, diagnostic = context()
        tree = r.Tree(r.LOCAL_ROOT)
        t.source_check(tree, inventory)  # intentionally checks the original v1 helper provenance
        checked = t.local_gate(APPROVAL_SHA)
        t.new_json(ATTEMPT / "local-gate-plan.json", checked)
        t.validate_gate(checked, inventory)
        stream, _ = t.bundle_open(ARCHIVE / "transfer-01/bundle.bin", BUNDLE)
        stream.close()
        record = plan_record(inventory, descriptors, diagnostic, r.utc())
        raw_sha = t.new_json(ATTEMPT / "correction-plan.json", record)
        result.update(status="planned-local-only", correction_plan_sha256=raw_sha,
                      current_client=record["current_client"], current_receiver=record["current_receiver"],
                      original_inventory_sha256=INVENTORY_SHA, original_bundle=BUNDLE)
    except BaseException as error:
        result.update(status="failed-partial-output-preserved", error=(type(error).__name__ + ": " + str(error))[:2000])
    finally:
        if tree is not None:
            tree.close()
        result["finished_at_utc"] = r.utc()
        receipt_sha = t.new_json(ATTEMPT / "plan-result.json", result)
    print(json.dumps({**result, "receipt_sha256": receipt_sha}, sort_keys=True), flush=True)
    return 0 if result["status"] == "planned-local-only" else 2


def send(expected_plan_sha):
    # Different attempt receipt, same immutable original bundle. No v1 marker
    # is removed or rewritten, and this marker prevents any second v2 attempt.
    t.new_json(ATTEMPT / "send-started.json", {"started_at_utc": r.utc(), "correction_plan_sha256": expected_plan_sha,
               "original_inventory_sha256": INVENTORY_SHA, "original_bundle": BUNDLE,
               "single_assessed_correction": True, "automatic_retry": False})
    result = {"schema": "peano-hydra-frontier-training-corrected-transfer-result-v2",
              "correction_plan_sha256": expected_plan_sha, "original_inventory_sha256": INVENTORY_SHA,
              "original_bundle": BUNDLE, "network_contacted": False, "automatic_retry": False,
              "partial_outputs_preserved": True}
    tree = None
    try:
        raw = t.read_file(ATTEMPT / "correction-plan.json")
        r.require(r.sha(raw) == expected_plan_sha, "external correction-plan SHA differs")
        record = r.decode(raw)
        inventory, descriptors, diagnostic = context()
        r.require(record == plan_record(inventory, descriptors, diagnostic, record["created_at_utc"]),
                  "correction plan differs from exact preserved and current inputs")
        planned = r.decode(t.read_file(ATTEMPT / "plan-result.json"))
        r.require(planned.get("status") == "planned-local-only" and planned.get("correction_plan_sha256") == expected_plan_sha,
                  "successful exact local correction plan missing")
        tree = r.Tree(r.LOCAL_ROOT)
        t.source_check(tree, inventory)
        checked = t.local_gate(APPROVAL_SHA)
        t.new_json(ATTEMPT / "local-gate-send.json", checked)
        t.validate_gate(checked, inventory)
        stream, before = t.bundle_open(ARCHIVE / "transfer-01/bundle.bin", BUNDLE)
        try:
            prefix = r.exact(stream, len(r.MAGIC) + 8)
            r.require(prefix[:len(r.MAGIC)] == r.MAGIC, "original bundle magic differs")
            length = struct.unpack(">Q", prefix[-8:])[0]
            old_inventory_raw = t.read_file(ARCHIVE / "transfer-01/inventory.json")
            r.require(length == len(old_inventory_raw) and r.exact(stream, length) == old_inventory_raw,
                      "original bundle inventory frame differs")
            stream.seek(0)
            program = t.read_file(RECEIVER).decode() + "\nmain()\n"
            command = ["/usr/bin/ssh", "-T", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                       "-o", "ServerAliveInterval=10", "-o", "ServerAliveCountMax=2", "-o", "ForwardAgent=no",
                       "-o", "ClearAllForwardings=yes", "-o", "StrictHostKeyChecking=yes", "-o", "UpdateHostKeys=no",
                       "-o", "ControlMaster=no", "-o", "ControlPath=none", "--", t.HOST,
                       "/usr/bin/python3 -I -B -c " + shlex.quote(program) + " " + INVENTORY_SHA]
            print(json.dumps({"phase": "single-assessed-corrected-transfer-starting", "original_bundle": BUNDLE,
                              "receiver_sha256": RECEIVER_SHA, "correction_plan_sha256": expected_plan_sha}), flush=True)
            result["network_contacted"] = True
            process = t.bounded(command, timeout=60, stdin=stream, cwd=str(ARCHIVE))
            process["command"] = command[:-1] + ["<fixed v2 remote program; hash recorded below>"]
            process["remote_program_sha256"] = r.sha(program.encode())
            process["receiver_sha256"] = RECEIVER_SHA
            t.new_json(ATTEMPT / "ssh-process.json", process)
            result["ssh_process"] = process
            r.require(r.identity(os.fstat(stream.fileno())) == before, "original bundle changed during transfer")
        finally:
            stream.close()
        t.source_check(tree, inventory)
        stream, _ = t.bundle_open(ARCHIVE / "transfer-01/bundle.bin", BUNDLE)
        stream.close()
        context()  # also preserves diagnostic, approval and predecessor receipts
        result["original_inputs_rechecked"] = True
        r.require(process["returncode"] == 0 and process["reason"] == "exited", "corrected transfer failed; no automatic retry")
        remote = r.decode(process["stdout"].encode())
        r.require(remote.get("schema") == "peano-hydra-frontier-training-transfer-remote-result-v2"
                  and remote.get("status") == "transferred-and-rehashed" and remote.get("inventory_sha256") == INVENTORY_SHA
                  and remote.get("remote_root") == r.REMOTE_ROOT and remote.get("source_commit") == COMMIT
                  and remote.get("request_sha256") == REQUEST_SHA and remote.get("approval_sha256") == APPROVAL_SHA
                  and remote.get("file_count") == inventory["file_count"] and remote.get("total_bytes") == inventory["total_bytes"]
                  and remote.get("all_file_hashes_rechecked") is True and remote.get("exact_inventory_checked") is True
                  and remote.get("job_submission_performed") is False and remote.get("installation_performed") is False,
                  "v2 receipt does not establish the exact approved transfer")
        result.update(status="transferred-and-rehashed", remote=remote, source_commit=COMMIT,
                      request_sha256=REQUEST_SHA, approval_sha256=APPROVAL_SHA)
    except BaseException as error:
        result.update(status="failed-no-automatic-retry", error=(type(error).__name__ + ": " + str(error))[:2000])
    finally:
        if tree is not None:
            tree.close()
        result["finished_at_utc"] = r.utc()
        receipt_sha = t.new_json(ATTEMPT / "send-result.json", result)
    print(json.dumps({"status": result["status"], "receipt": str(ATTEMPT / "send-result.json"),
                      "receipt_sha256": receipt_sha, "network_contacted": result["network_contacted"]}), flush=True)
    return 0 if result["status"] == "transferred-and-rehashed" else 2


def main(argv=None):
    r.require(sys.flags.isolated and sys.dont_write_bytecode, "run with python -I -B")
    os.umask(0o077)
    resource.setrlimit(resource.RLIMIT_CPU, (120, 120))
    def deadline(signum, frame):
        raise TimeoutError("corrected client 180-second wall deadline")
    signal.signal(signal.SIGALRM, deadline)
    signal.alarm(180)
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    choices = parser.add_subparsers(dest="operation", required=True)
    choices.add_parser("plan", allow_abbrev=False)
    second = choices.add_parser("send", allow_abbrev=False)
    second.add_argument("--correction-plan-sha256", required=True)
    args = parser.parse_args(argv)
    if args.operation == "plan":
        return plan()
    r.require(r.HEX.fullmatch(args.correction_plan_sha256), "external correction-plan SHA required")
    return send(args.correction_plan_sha256)


if __name__ == "__main__":
    raise SystemExit(main())
