"""Create the new base3 metadata admission only; execute no admission or job."""
import ast
import difflib
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
PARENT = BASE / "pilot-completion-admission-v1/pilot_admission.py"
PARENT_SHA = "d49c91257d107e4b0618fc35cbaac193efed0f7abf7c29f56a1e79d5ede39e8f"
RECOVERY_PINS = {
    "metadata_recovery.py": "3f11a9e6ef501cc4834662f01a4dd7a388892f71cae1bc70ad4a272524c5d2be",
    "gpu_saved_reload.py": "7cea491f147d7feebc6478cd0589965df9c4ac106e0bbf03e3c15243c3064639",
    "remote_recovery_control.py": "395b00b65e0e65be5ce6cf19ca554665ced1576e4f970d7d982fc79643bf6022",
    "recovery_launchers.py": "a6cd9bb1495d8496b542ab8546ba26f560dfafc9bf6caa0a058e4f335424c150",
}


def once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after)


def main():
    before = PARENT.read_bytes()
    assert sha256(before).hexdigest() == PARENT_SHA
    text = before.decode()
    for name, expected in RECOVERY_PINS.items():
        assert sha256((BASE / "p6-postsave-recovery-v3" / name).read_bytes()).hexdigest() == expected, name
    replacements = {
        'RECOVERY = "p6-postsave-recovery-v2"': 'RECOVERY = "p6-postsave-recovery-v3"',
        'CPU_REPORT = "metadata-recovery-env2.json"': 'CPU_REPORT = "metadata-recovery-base3.json"',
        'CPU_ACTUAL = "metadata-actual-completion-env2.json"': 'CPU_ACTUAL = "metadata-actual-completion-base3.json"',
        '"saved_pilot_recovery_v1"': '"saved_pilot_recovery_v2"',
        '1f485e4207430fb3bc9d42849053cbc7bf32eb07dda789f6c0c9e63d5c07b86e': RECOVERY_PINS["metadata_recovery.py"],
        '7a4262e4039fe3fcb77a63e73db76b3eda2b1f93132b7bc290271c4152f0b960': RECOVERY_PINS["gpu_saved_reload.py"],
        'c2bc5986d57d300c84cb8a73a1234d823989ebfd29b1be68aef72104a89fbb54': RECOVERY_PINS["remote_recovery_control.py"],
        '343a8a13569f99e6ee602cf95bd3fe9db4ebfcc08cac575c0835930e7b276b12': RECOVERY_PINS["recovery_launchers.py"],
        'saved tensors through the unchanged provider.': 'saved tensors through the explicitly versioned inference provider.',
    }
    for old, new in replacements.items():
        text = once(text, old, new)
    for old, new in (("hydra-pilot-completion-admission-v1", "hydra-pilot-completion-admission-v2"),
                     ("hydra-pilot-completion-admission-input-v1", "hydra-pilot-completion-admission-input-v2"),
                     ("hydra-pilot-pair-admission-v1", "hydra-pilot-pair-admission-v2")):
        assert old in text
        text = text.replace(old, new)
    text = once(text, 'metadata.get("plan_canonical_json_equal") is True',
        'metadata.get("original_recorded_saved_plan_canonical_json_equal") is True\n'
        '                and metadata.get("runtime_plan_matches_exact_provider_rebinding") is True\n'
        '                and metadata.get("training_exposure_changed") is False')
    text = once(text, '"selector": "env2"', '"selector": "base3"')
    text = once(text,
        '        for name, raw in ((CPU_REPORT, metadata_raw), (CPU_ACTUAL, actual_raw)):\n'
        '            remote[gpu.PACKAGE + "/" + name] = {"bytes": len(raw), "sha256": digest(raw)}\n',
        '        for name, raw in ((CPU_REPORT, metadata_raw), (CPU_ACTUAL, actual_raw)):\n'
        '            remote[gpu.PACKAGE + "/" + name] = {"bytes": len(raw), "sha256": digest(raw)}\n'
        '        for key, path, expected_sha in (\n'
        '            ("runtime_source_map", gpu.PACKAGE + "/runtime-source-pins-base3.json", None),\n'
        '            ("runtime_manifest", str(Path(gpu.SOURCE).parent / "manifest.json"), gpu.RUNTIME_MANIFEST_SHA)):\n'
        '            item = metadata["inputs"].get(key, {})\n'
        '            require(item.get("path") == path and type(item.get("bytes")) is int\n'
        '                    and 0 < item["bytes"] <= 2 * 1024**2 and gpu.sha(item.get("sha256"))\n'
        '                    and (expected_sha is None or item["sha256"] == expected_sha),\n'
        '                    "The separately authenticated inference input binding differs.")\n'
        '            remote[path] = {"bytes": item["bytes"], "sha256": item["sha256"]}\n')
    text = once(text,
        '                "seconds": original_request["reservation"]["seconds"], "reservation_sha256": original_request["reservation_sha256"]},',
        '                "seconds": original_request["reservation"]["seconds"], "reservation_sha256": original_request["reservation_sha256"],\n'
        '                "source_root": gpu.TRAINING_SOURCE, "source_pins_sha256": gpu.TRAINING_SOURCE_MAP_SHA,\n'
        '                "provider_sha256": gpu.TRAINING_PROVIDER_SHA},')
    text = once(text,
        '                "reservation_sha256": digest(canonical(record) + b"\\n"), "selector": "base3"},',
        '                "reservation_sha256": digest(canonical(record) + b"\\n"), "selector": "base3",\n'
        '                "runtime_source_root": gpu.SOURCE, "runtime_source_pins_sha256": gpu.SOURCE_MAP_SHA,\n'
        '                "runtime_provider_sha256": gpu.PROVIDER_SHA, "runtime_manifest_sha256": gpu.RUNTIME_MANIFEST_SHA,\n'
        '                "runtime_inference_only": True, "runtime_training_execution_allowed": False,\n'
        '                "plan_derivation": metadata["plan_derivation"],\n'
        '                "adapter_config_admission": metadata["adapter_config_admission"]},')
    text = once(text,
        '                "reservation_sha256": digest(canonical(record) + b"\\n")},\n'
        '            "recovery": None,',
        '                "reservation_sha256": digest(canonical(record) + b"\\n"),\n'
        '                "source_root": reader.control.SOURCE, "source_pins_sha256": spec["source_pins_sha256"],\n'
        '                "controller_sha256": spec["controller_sha256"],\n'
        '                "provider_sha256": "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"},\n'
        '            "recovery": None,')
    ast.parse(text)
    after = text.encode()
    with (HERE / "pilot_admission.py").open("xb") as stream:
        stream.write(after)
    with (HERE / "admission-changes.diff").open("x") as stream:
        stream.writelines(difflib.unified_diff(before.decode().splitlines(True), text.splitlines(True),
                                             fromfile="v1/pilot_admission.py", tofile="v2/pilot_admission.py"))
    old_tree, new_tree = ast.parse(before), ast.parse(after)
    def nodes(tree):
        return {node.name: ast.dump(node, include_attributes=False) for node in tree.body
                if isinstance(node, (ast.FunctionDef, ast.ClassDef))}
    old, new = nodes(old_tree), nodes(new_tree)
    changed = sorted(name for name in old if old[name] != new.get(name))
    assert set(old) == set(new) and set(changed) == {"recovered", "normal4", "admit_pilot", "require_pilot_charges", "main"}
    audit = {"schema": "hydra-base3-pilot-admission-derivation-v1", "parent_sha256": PARENT_SHA,
        "new_sha256": sha256(after).hexdigest(), "recovery_reader_pins": RECOVERY_PINS,
        "changed_callables": changed, "identical_callables": sorted(set(old) - set(changed)),
        "original_inputs_unchanged": sha256(PARENT.read_bytes()).hexdigest() == PARENT_SHA,
        "model_calls": 0, "native_calls": 0, "ssh_calls": 0, "actual_pilot_admissions": 0}
    with (HERE / "admission-derivation.json").open("x") as stream:
        json.dump(audit, stream, sort_keys=True, indent=2); stream.write("\n")
    print(json.dumps(audit, sort_keys=True))


if __name__ == "__main__":
    main()
