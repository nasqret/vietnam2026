"""Metadata-only admission of one source04 repair; never relabel stage255.

This module imports no application, native engine, model or transport code.
The caller supplies its existing bounded, pinned workspace evidence reader.
"""
from __future__ import annotations

import base64
import hashlib
import json
import math
import re

BASE = "output/hydra-implementation-2026-09-04/"
REPAIR = BASE + "p6-source04-repair-01/"
REPAIR_REVIEW_SHA = "77f5d30482ade77764fd14b16bcac4dc877b1e6e9efd5e1dae16219c1237b6e1"
SOURCE = "/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-practical-v1-20260904/bundles/combined-source-04/source"
MANIFEST_SHA = "4beeb386a118229b4e3fa9b751d7a4a560853252ab3103cff661a48dc2eb9f0e"
MANIFEST_CONTENT_SHA = "aa001fceb6eaefcf3073287f8cb8a8efacffc245fe524759ad95a0d34571c9dd"
PRESERVED_NAMES_SHA = "dd254b328eb75325e737ac755288506391c27c9acd747e030af3a1d60f3f95cc"
FAILED_STAGE = {"path": BASE + "combined-inference-transfer-04/actual-completion.json", "bytes": 2815,
    "sha256": "e96466bdf428d7202ec1baced75b44c064259099660703212f7f9cdc397635bb"}
FAILED_TOOL = {"path": BASE + "combined-inference-transfer-04/actual-tool-completion.json", "bytes": 704,
    "sha256": "bc72518950743e3e82e498f439f126c52916178cb5c07649aec1496c5e38791d"}
INVENTORY = {"path": BASE + "p6-source04-reconciliation-03/stdout.jsonl", "bytes": 154875,
    "sha256": "d95cf025fc969aa0e6f1ec2e810ab9d038b0d025d5f6152f4acb65efab32e2b8"}
INVENTORY_TOOL = {"path": BASE + "p6-source04-reconciliation-03/actual-tool-completion.json", "bytes": 189,
    "sha256": "4d1461698af6f9cd1d986546294cff170518b17bde63eabd8d481bde21c73e42"}
BOUNDS = {"remote_wall_seconds": 120, "remote_cpu_soft_seconds": 60,
    "remote_cpu_hard_seconds": 75, "remote_address_space_bytes": 536870912,
    "ssh_wall_seconds": 150, "maximum_input_bytes": 2097152,
    "maximum_stdout_bytes": 65536, "maximum_stderr_bytes": 65536}
REMOTE_LIMITS = {"remote_wall_seconds": 120, "remote_cpu_soft_seconds": 60,
    "remote_cpu_hard_seconds": 75, "remote_address_space_bytes": 536870912,
    "quota_query_wall_seconds": 10, "quota_output_bytes": 16384,
    "maximum_open_directories": 192, "request_bytes": 2097152,
    "maximum_cached_missing_bytes": 32782277}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def valid_sha(value):
    return type(value) is str and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def strict(raw, maximum=65536):
    require(type(raw) is bytes and len(raw) <= maximum, "Repair metadata exceeds its bound.")
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate repair metadata key.")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Non-finite repair metadata: " + value)
    result = json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    require(type(result) is dict, "Repair metadata must be an object.")
    return result


def pinned(read_evidence, descriptor, maximum=65536):
    require(type(descriptor) is dict and set(descriptor) in ({"path", "sha256"}, {"path", "bytes", "sha256"})
            and type(descriptor.get("path")) is str and valid_sha(descriptor.get("sha256")),
            "Repair evidence needs an exact bounded workspace descriptor.")
    raw = read_evidence({key: descriptor[key] for key in ("path", "sha256")}, limit=maximum)
    require(type(raw) is bytes and len(raw) <= maximum and digest(raw) == descriptor["sha256"]
            and ("bytes" not in descriptor or type(descriptor["bytes"]) is int and len(raw) == descriptor["bytes"]),
            "Repair evidence pin differs.")
    return raw


def history(read_evidence):
    failed = strict(pinned(read_evidence, FAILED_STAGE))
    failed_tool = strict(pinned(read_evidence, FAILED_TOOL))
    inventory = strict(pinned(read_evidence, INVENTORY, 256 * 1024), 256 * 1024)
    inventory_tool = strict(pinned(read_evidence, INVENTORY_TOOL))
    require(failed.get("actual_ssh_exit_code") == 255
            and failed_tool.get("actual_process_exit_code") == 255
            and failed_tool.get("actual_ssh_exit_code") == 255
            and failed_tool.get("completion_chunk") == "add706"
            and failed_tool.get("source_transfer_success_asserted") is False,
            "The original stage255 must remain a failed, unadmitted transport.")
    require(inventory.get("schema") == "hydra-read-only-partial-source-inventory-v1"
            and inventory.get("root") == SOURCE and inventory.get("read_only") is True
            and inventory.get("file_count") == 821 and inventory.get("total_bytes") == 79300068
            and inventory_tool.get("actual_process_exit_code") == 0
            and inventory_tool.get("actual_ssh_exit_code") == 0
            and inventory_tool.get("completion_chunk") == "42a78c",
            "The actual partial-copy observation differs.")
    names = sorted(row["path"] for row in inventory["files"])
    require(len(names) == len(set(names)) == 821 and digest(canonical(names)) == PRESERVED_NAMES_SHA,
            "The observed starting namespace differs.")


def transport_admission(response_raw, actual_raw, review, wire, read_evidence):
    actual = strict(actual_raw)
    required = {"schema", "actual_process_exit_code", "actual_ssh_exit_code", "completion_chunk",
                "review_sha256", "response", "transport_receipt"}
    require(set(actual) == required and actual["schema"] == "hydra-source04-repair-actual-tool-completion-v1"
            and type(actual["actual_process_exit_code"]) is int and actual["actual_process_exit_code"] == 0
            and type(actual["actual_ssh_exit_code"]) is int and actual["actual_ssh_exit_code"] == 0
            and type(actual["completion_chunk"]) is str and 1 <= len(actual["completion_chunk"]) <= 200
            and actual["review_sha256"] == REPAIR_REVIEW_SHA
            and canonical(actual["response"]) == canonical({"bytes": len(response_raw), "sha256": digest(response_raw)}),
            "Distinct actual repair SSH0 and observed tool0/chunk are required.")
    descriptor = actual["transport_receipt"]
    require(type(descriptor) is dict and descriptor.get("path") == REPAIR + "attempt-01/actual-completion.json",
            "Only the new repair attempt's actual transport receipt is admitted.")
    transport = strict(pinned(read_evidence, descriptor))
    expected = {"schema": "hydra-source04-partial-copy-repair-actual-completion-v1",
        "actual_ssh_exit_code": 0, "outer_timeout": False, "output_limit_exceeded": False,
        "io_error": None, "capture_complete": True, "review_sha256": REPAIR_REVIEW_SHA,
        "remote_code_sha256": review["remote_code"]["sha256"],
        "wire_payload_bytes": len(wire), "wire_payload_sha256": digest(wire), "raw_payload_bytes": 423394,
        "stdin_bytes_written": len(wire), "stdin_bytes_expected": len(wire),
        "stdout": {"bytes": len(response_raw), "sha256": digest(response_raw)},
        "original_stage_exit_code": 255, "original_stage_completion_chunk": "add706",
        "original_stage_preserved": True, "automatic_retry_performed": False,
        "allocations": 0, "automatic_retry": False,
        "remote_copy_outcome": "unadmitted_until_receipt_validation"}
    require(canonical({k: v for k, v in transport.items() if k not in {"elapsed_seconds", "stderr"}})
            == canonical(expected), "Repair transport failed, is incomplete or has different inputs.")
    elapsed = transport.get("elapsed_seconds")
    require(type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed <= BOUNDS["ssh_wall_seconds"],
            "Repair transport time is missing or outside its selected bound.")
    stderr = transport.get("stderr")
    require(type(stderr) is dict and set(stderr) == {"bytes", "sha256"}
            and type(stderr["bytes"]) is int and 0 <= stderr["bytes"] <= BOUNDS["maximum_stderr_bytes"]
            and valid_sha(stderr["sha256"]), "Repair stderr capture is not bounded and pinned.")
    return actual


def admit_source04_repair(response_raw, actual_raw, manifest, *, read_evidence):
    """Admit distinct repair evidence, requiring real SSH and outer tool success."""
    require(valid_sha(REPAIR_REVIEW_SHA), "The exact repair review has not been frozen.")
    review_raw = pinned(read_evidence, {"path": REPAIR + "REPAIR_REVIEW.json", "sha256": REPAIR_REVIEW_SHA})
    review = strict(review_raw)
    require(review.get("schema") == "hydra-source04-partial-copy-repair-review-v1"
            and canonical(review.get("bounds")) == canonical(BOUNDS)
            and review.get("automatic_retry") is False and type(review.get("allocations")) is int
            and review["allocations"] == 0, "The exact bounded repair review is required.")
    require(canonical(review.get("failed_stage_actual")) == canonical(FAILED_STAGE)
            and canonical(review.get("failed_stage_tool_actual")) == canonical(FAILED_TOOL)
            and canonical(review.get("partial_inventory")) == canonical(INVENTORY)
            and canonical(review.get("partial_inventory_tool_actual")) == canonical(INVENTORY_TOOL),
            "The repair review must preserve the exact failed stage and partial observation.")
    history(read_evidence)
    pinned(read_evidence, review["remote_code"])
    expected_payloads = {"manifest.json": (253561, MANIFEST_SHA),
        "paired-source-pins.json": (126170, "d32c30a437070986df9777bf97dbb56f362e720d63ba32be16d8b728155ecf9d"),
        "source/output/hydra-implementation-2026-09-04/paired-evaluation-v2/paired_controller.py":
            (43663, "05100256d9e303810fbac78ef34e788377223225bcc6828bb0100564c6f36217")}
    require(type(review.get("payloads")) is dict and set(review["payloads"]) == set(expected_payloads),
            "Only the original three source04 payloads are admitted.")
    payloads = {}
    for name, (size, sha) in expected_payloads.items():
        raw = pinned(read_evidence, review["payloads"][name], 1024 * 1024)
        require(len(raw) == size and digest(raw) == sha, "A source04 payload changed.")
        payloads[name] = base64.b64encode(raw).decode("ascii")
        if name == "manifest.json":
            require(canonical(strict(raw, 1024 * 1024)) == canonical(manifest)
                    and digest(canonical(manifest)) == MANIFEST_CONTENT_SHA,
                    "The repair must preserve the exact complete source04 manifest.")
    wire = canonical({"schema": "hydra-source04-partial-copy-repair-request-v1",
        "authority": "HYDRA_EXPERIMENT_AUTHORITY.md", "automatic_retry": False,
        "review_sha256": REPAIR_REVIEW_SHA, "payloads": payloads})
    require(len(wire) <= BOUNDS["maximum_input_bytes"], "Repair wire exceeds its bound.")
    actual = transport_admission(response_raw, actual_raw, review, wire, read_evidence)
    response = strict(response_raw)
    expected = {"schema": "hydra-source04-partial-copy-repair-receipt-v1", "completed": True,
        "review_sha256": REPAIR_REVIEW_SHA, "request_sha256": digest(wire),
        "directory": SOURCE.removesuffix("/source"), "source": SOURCE,
        "derived_from_source": SOURCE.replace("/combined-source-04/", "/combined-source-03/"),
        "stage_retained": {"exit_code": 255, "completion_chunk": "add706", "partial_inventory_sha256": INVENTORY["sha256"]},
        "original_stage_success_claimed": False, "manifest_sha256": MANIFEST_SHA,
        "manifest_content_sha256": MANIFEST_CONTENT_SHA, "manifest_raw_bytes_preserved": True,
        "parent_remote_manifest_sha256": "bff0239d9e0c74e088118a271907da887d009acad3e3b21eca4534c1da855c08",
        "parent_local_manifest_sha256": "bff0239d9e0c74e088118a271907da887d009acad3e3b21eca4534c1da855c08",
        "parent_manifest_content_sha256": "9b73388872811477057ff6f3ddff9e5b54020b12c22059d12519594bea15da62",
        "source_maps": manifest["source_maps"], "provider_sha256": manifest["provider_sha256"],
        "provider_profile": manifest["provider_profile"], "verified_files": 1325, "verified_bytes": 112082345,
        "existing_files_preserved": 821, "missing_files_created": 504, "metadata_files_created": 5,
        "starting_source_names_sha256": PRESERVED_NAMES_SHA,
        "initial_inventory_is_not_a_content_hash_attestation": True, "all_final_source_bytes_verified": True,
        "source_directories_read_only": True, "source_directories_frozen": 62,
        "intent_files_created": 1, "repair_receipts_created": 1, "existing_file_stamps_preserved": True,
        "old_whitelisted_sources_unchanged": True, "no_overwrites": True, "no_symlinks": True, "no_hardlinks": True,
        "non_whitelisted_files_copied": 0, "hardlinks_created": 0, "saved_artifact_files_read": 0,
        "uploaded_payload_files": 3, "uploaded_payload_bytes": 423394, "wire_payload_bytes": len(wire),
        "copied_unchanged_metadata_files": ["student-source-pins.json", "teacher-paired-source-pins.json", "teacher-source-pins.json"],
        "local_reference_archive_sha256": manifest["archive_sha256"], "remote_archive_available": False,
        "archive_bytes_uploaded": 0, "application_executions": 0, "gpu_allocations": 0,
        "model_calls": 0, "native_runs": 0, "scheduler_queries": 0, "automatic_retry": False,
        "experiment_retry_or_resume": False, "limits": REMOTE_LIMITS,
        "maximum_cached_missing_bytes": 32782277, "inode_quota_required_with_reserve": 796}
    require(canonical({k: v for k, v in response.items()
                       if k not in {"elapsed_seconds", "open_directory_capabilities", "quota_query"}})
            == canonical(expected), "The repair did not verify the exact source04 population and preservation contract.")
    elapsed = response.get("elapsed_seconds")
    require(type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed < 120,
            "The repair elapsed time is missing or outside its bound.")
    opened = response.get("open_directory_capabilities")
    require(type(opened) is int and 1 <= opened <= 192, "The repair directory capability bound differs.")
    quota = response.get("quota_query")
    require(type(quota) is dict and set(quota) == {"actual_exit_code", "owned_child_reaped", "elapsed_seconds",
                                                 "stdout_stderr", "used", "limit", "automatic_retry"}
            and type(quota["actual_exit_code"]) is int and quota["actual_exit_code"] == 0
            and quota["owned_child_reaped"] is True and quota["automatic_retry"] is False
            and type(quota["elapsed_seconds"]) in (int, float) and math.isfinite(quota["elapsed_seconds"])
            and 0 <= quota["elapsed_seconds"] <= 13
            and type(quota["stdout_stderr"]) is str and len(quota["stdout_stderr"].encode()) <= 16384
            and type(quota["used"]) is int and type(quota["limit"]) is int
            and 0 <= quota["used"] <= quota["limit"] - 796,
            "The one bounded quota query, cleanup or inode reserve is not established.")
    return {"schema": "hydra-source04-repair-admission-v1", "kind": "separately_observed_partial_copy_repair",
        "original_stage_exit_code": 255, "original_stage_completion_chunk": "add706",
        "repair_review_sha256": REPAIR_REVIEW_SHA, "repair_response_sha256": digest(response_raw),
        "repair_actual_tool_completion_sha256": digest(actual_raw), "repair_completion_chunk": actual["completion_chunk"],
        "source": SOURCE, "manifest_sha256": MANIFEST_SHA,
        "cpu_probe_or_gpu_success_asserted": False}
