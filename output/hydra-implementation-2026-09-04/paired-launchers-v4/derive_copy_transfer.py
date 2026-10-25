"""One local, source-pinned derivation; never imports launchers or runs phases."""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
PINS = {
    "paired-launchers-v3/paired_launchers.py": "ab45419577d7e0456edd40ae9112f257045e4b77eacac60b0a1e84be0dff9c6d",
    "paired-launchers-v3/remote_paired_control.py": "755289a7b17044c68f974245d2b5408e2099721bb01445999dd6daa407c51bb9",
    "p7-teacher-launchers-v3/teacher_launchers.py": "337c1dcf1c754361ffb88cd83ce15072df576f3030912d44ff8af6226fe84ec4",
    "p7-teacher-launchers-v3/remote_teacher_control.py": "996858ea44d346b94fdc0354a121fa5f6ba1b2651339eb802387b8284074b6be",
}

HELPER = '''
def admit_copy_transfer(response_raw, transport_raw, manifest):
    """Admit the reviewed copy-v2 metadata, not a fabricated legacy upload.

    Callers authenticate both raw files through explicit evidence descriptors.
    The review hash binds all 15 payloads, the exact copier, and its bounds.
    This establishes source transfer only; pilot/model admission is separate.
    """
    def strict(raw):
        require(type(raw) is bytes and len(raw) <= 65536, "Copy metadata exceeds its bound.")
        def pairs(items):
            value = {}
            for key, item in items:
                require(key not in value, "Duplicate copy metadata key.")
                value[key] = item
            return value
        def constant(value):
            raise ValueError("Non-finite copy metadata: " + value)
        result = json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)
        require(type(result) is dict, "Copy metadata must be an object.")
        return result

    response, transport = strict(response_raw), strict(transport_raw)
    manifest_content_sha = "4aeb37d8ad971975a22fe7cd879c69ad35e11246dccc5d37d7a9a0c2ab899ec1"
    require(digest(canonical(manifest)) == manifest_content_sha, "Copy manifest content differs.")
    review = transport.get("review")
    require(type(review) is dict and digest(canonical(review)) ==
            "326dcfeef13e14a0dabf090108d314b204cd9578592fbc9bce0ce563003e9a92",
            "The copy payload, copier, or reviewed bounds differ.")
    stderr_sha = transport.get("stderr_sha256")
    require(type(stderr_sha) is str and len(stderr_sha) == 64
            and all(c in "0123456789abcdef" for c in stderr_sha), "Invalid transport stderr pin.")
    expected_transport = {
        "schema": "hydra-combined-inference-source-stage-actual-completion-v2",
        "actual_ssh_exit_code": 0, "review": review, "stdout_sha256": digest(response_raw),
        "stderr_sha256": stderr_sha, "gpu_allocations": 0, "model_calls": 0,
        "native_runs": 0, "automatic_retry": False,
    }
    require(canonical({k: v for k, v in transport.items() if k != "elapsed_seconds"}) ==
            canonical(expected_transport), "Actual copy transport failed or does not bind these raw receipt bytes.")
    expected_response = {
        "schema": "hydra-combined-inference-source-copy-receipt-v2", "completed": True,
        "directory": str(Path(control.SOURCE).parent), "source": control.SOURCE,
        "derived_from_source": review["remote_parent"] + "/source",
        "manifest_sha256": control.MANIFEST_SHA, "manifest_content_sha256": manifest_content_sha,
        "manifest_raw_bytes_preserved": True,
        "parent_remote_manifest_sha256": review["parent_remote_manifest_sha256"],
        "parent_manifest_content_sha256": review["parent_manifest_content_sha256"],
        "parent_local_manifest_sha256": review["parent_local_manifest_sha256"],
        "source_maps": manifest["source_maps"], "provider_sha256": manifest["provider_sha256"],
        "provider_profile": manifest["provider_profile"], "verified_files": manifest["file_count"],
        "verified_bytes": manifest["expanded_bytes"], "unchanged_files": 1315,
        "changed_files": sorted(manifest["changed_files"]), "uploaded_payload_files": 15,
        "uploaded_payload_bytes": 1059320, "wire_payload_bytes": review["wire_payload_bytes"],
        "archive_bytes_uploaded": 0, "remote_archive_available": False,
        "local_reference_archive_sha256": control.ARCHIVE_SHA,
        "old_whitelisted_sources_unchanged": True, "non_whitelisted_files_copied": 0,
        "saved_artifact_files_read": 0, "hardlinks_created": 0,
        "source_scope": "sealed inference/teacher/student helper source; ordinary P6 training path not admitted",
        "application_executions": 0, "gpu_allocations": 0, "model_calls": 0,
        "native_runs": 0, "scheduler_queries": 0, "automatic_retry": False,
    }
    require(canonical({k: v for k, v in response.items() if k not in {"elapsed_seconds", "inode_quota_before"}}) ==
            canonical(expected_response), "Copy source, raw manifest, provider, maps, counts or preservation evidence differs.")
    for record, maximum in ((response, 120), (transport, 150)):
        value = record.get("elapsed_seconds")
        require(type(value) in (int, float) and math.isfinite(value) and 0 <= value <= maximum,
                "Copy duration is missing or outside the reviewed wall bound.")
    quota = response.get("inode_quota_before")
    require(type(quota) is dict and set(quota) == {"used", "limit", "required_with_reserve"}
            and all(type(value) is int for value in quota.values())
            and quota["required_with_reserve"] == 1642
            and 0 <= quota["used"] <= quota["limit"] - 1642, "Copy quota/reserve evidence differs.")


'''


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def functions(raw):
    return {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(raw).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def main():
    records = []
    for old_name, pin in PINS.items():
        old_path = BASE / old_name
        before = old_path.read_bytes()
        assert digest(before) == pin
        new_path = BASE / old_name.replace("launchers-v3/", "launchers-v4/")
        new_path.parent.mkdir(exist_ok=True)
        assert not new_path.exists()
        text = before.decode()
        if old_path.name == "paired_launchers.py":
            first = '    transferred = json.loads(evidence(choice["transfer"]["response"]))\n'
            last = '    historical = evidence(choice["historical_manifest"])\n'
            start, end = text.index(first), text.index(last)
            old_block = text[start:end]
            legacy = old_block[old_block.index('    require(transfer.get("actual_ssh_exit_code")'):]
            changed = (
                '    response_raw = evidence(choice["transfer"]["response"])\n'
                '    transport_raw = evidence(choice["transfer"]["actual_completion"])\n'
                '    transferred, transfer = json.loads(response_raw), json.loads(transport_raw)\n'
                '    if transferred.get("schema") == "hydra-combined-inference-source-copy-receipt-v2" or \\\n'
                '            transfer.get("schema") == "hydra-combined-inference-source-stage-actual-completion-v2":\n'
                '        admit_copy_transfer(response_raw, transport_raw, manifest)\n'
                '    else:\n' + ''.join('    ' + line if line.strip() else line for line in legacy.splitlines(True)))
            text = text[:start] + changed + text[end:]
            insertion = text.index('def prepare(args):')
            text = text[:insertion] + HELPER.lstrip('\n') + text[insertion:]
            expected = {"prepare"}
        elif old_path.name == "teacher_launchers.py":
            first = '    transfer = admission.strict_json(inputs.descriptor(choice["transfer"]["actual_completion"], 65536))\n'
            last = '    prior = json.loads(read(HERE.parent / "p7-clean-base-admission-01/stdout.json",\n'
            start, end = text.index(first), text.index(last)
            old_block = text[start:end]
            legacy = old_block[old_block.index('    require(type(transfer.get("actual_ssh_exit_code"))'):]
            changed = (
                '    transport_raw = inputs.descriptor(choice["transfer"]["actual_completion"], 65536)\n'
                '    response_raw = inputs.descriptor(choice["transfer"]["response"], 2 * 1024**2)\n'
                '    transfer, upload = admission.strict_json(transport_raw), admission.strict_json(response_raw)\n'
                '    if upload.get("schema") == "hydra-combined-inference-source-copy-receipt-v2" or \\\n'
                '            transfer.get("schema") == "hydra-combined-inference-source-stage-actual-completion-v2":\n'
                '        admit_copy_transfer(response_raw, transport_raw, manifest)\n'
                '    else:\n' + ''.join('    ' + line if line.strip() else line for line in legacy.splitlines(True)))
            text = text[:start] + changed + text[end:]
            insertion = text.index('def bundle_inputs(choice):')
            text = text[:insertion] + HELPER.lstrip('\n') + text[insertion:]
            expected = {"bundle_inputs"}
        else:
            expected = set()
        after = text.encode()
        prior_functions, next_functions = functions(before), functions(after)
        changed_functions = {name for name in prior_functions if prior_functions[name] != next_functions.get(name)}
        assert changed_functions == expected
        assert set(next_functions) - set(prior_functions) == ({"admit_copy_transfer"} if expected else set())
        if expected:
            # Preserve the existing legacy require call, including its exact message.
            old_tree, new_tree = ast.parse(before), ast.parse(after)
            legacy_tree = ast.parse(legacy.lstrip()).body[0]
            assert ast.dump(legacy_tree, include_attributes=False) in {
                ast.dump(node, include_attributes=False) for node in ast.walk(new_tree) if isinstance(node, ast.Expr)}
        else:
            assert before == after
        with new_path.open('xb') as stream:
            stream.write(after)
        difference = ''.join(difflib.unified_diff(before.decode().splitlines(True), text.splitlines(True),
                                                fromfile=old_name, tofile=new_path.relative_to(BASE).as_posix()))
        if difference:
            with (new_path.parent / (new_path.name + '.diff')).open('x') as stream:
                stream.write(difference)
        records.append({"before": old_name, "before_sha256": pin,
                        "after": new_path.relative_to(BASE).as_posix(), "after_sha256": digest(after),
                        "after_bytes": len(after), "changed_functions": sorted(changed_functions),
                        "legacy_requirement_unchanged": True, "remote_byte_identical": not expected})
    result = {"schema": "hydra-copy-transfer-launcher-derivation-v1", "records": records,
              "legacy_choice_and_attempt_schemas_unchanged": True,
              "recovery_v4_binding_pending": True, "model_admission_performed": False,
              "choice_or_job_preparation_performed": False, "native_runs": 0, "ssh_calls": 0}
    with (Path(__file__).resolve().parent / 'derivation.json').open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
