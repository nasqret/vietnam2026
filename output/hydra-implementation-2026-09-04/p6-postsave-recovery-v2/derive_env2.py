"""File-only env2 selector derivation; no recipe import or runtime execution."""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "p6-postsave-recovery-v1"
ROOT = HERE.parents[2]
PINS = {
    "gpu_saved_reload.py": "573b4522cc94b5af2d03c17216fd34163882a25746f190f59a91bf969072ff5a",
    "remote_recovery_control.py": "616f79fa4022201623f79dcafb4d20ca1dd74932ffa53a93f9e288d9286623e7",
    "recovery_launchers.py": "8463accee9c618a13e2fe5fec232291657b0d1acbf53a182de3f49beda9301f7",
    "metadata_recovery.py": "1f485e4207430fb3bc9d42849053cbc7bf32eb07dda789f6c0c9e63d5c07b86e",
    "controller-source-pins.json": "898f5b8a1ee68b7201a397acc9b7e353910453e261386881979c86f715b44547",
    "test_gpu_recovery.py": "40069c8fec95650e5cf00da42903a6aea19a3309cfaec8f0fd787a3addc5917f",
}
COMMON = {
    "p6-saved-recovery-1.7b-01": "p6-saved-recovery-1.7b-env2-01",
    "metadata-recovery.json": "metadata-recovery-env2.json",
    "metadata-actual-completion.json": "metadata-actual-completion-env2.json",
}


def pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def main():
    names = tuple(PINS) + ("derive_helpers.py", "run_gpu_pure_gate.py")
    original = {name: (OLD / name).read_bytes() for name in names}
    for name, expected in PINS.items():
        assert pin(original[name])["sha256"] == expected, "Old reviewed source changed: " + name
    produced = dict(original)
    substitutions = {}
    for name in ("gpu_saved_reload.py", "remote_recovery_control.py", "recovery_launchers.py"):
        changes = dict(COMMON)
        if name == "recovery_launchers.py":
            del changes["p6-saved-recovery-1.7b-01"]
        else:
            changes["gpu_saved_reload.py"] = "gpu_saved_reload_env2.py"
        if name == "remote_recovery_control.py":
            changes[PINS["gpu_saved_reload.py"]] = pin(produced["gpu_saved_reload.py"])["sha256"]
        source = original[name].decode()
        counts = {}
        for old, new in changes.items():
            counts[old] = source.count(old)
            assert counts[old] > 0, (name, old)
            source = source.replace(old, new)
        ast.parse(source)
        produced[name] = source.encode()
        substitutions[name] = [{"old": old, "new": new, "occurrences": counts[old]}
                               for old, new in changes.items()]
        inverse = source
        for old, new in reversed(tuple(changes.items())):
            inverse = inverse.replace(new, old)
        assert inverse.encode() == original[name], "Nonliteral change in " + name
        assert ast.dump(ast.parse(inverse), include_attributes=False) == ast.dump(
            ast.parse(original[name]), include_attributes=False)
    test = original["test_gpu_recovery.py"].decode()
    old = 'control.PACKAGE + "/gpu_saved_reload.py", script)'
    assert test.count(old) == 1
    produced["test_gpu_recovery.py"] = test.replace(
        old, 'control.PACKAGE + "/gpu_saved_reload_env2.py", script)').encode()
    for name, raw in produced.items():
        with (HERE / name).open("xb") as stream:
            stream.write(raw)
    diff = "".join(line for name in substitutions for line in difflib.unified_diff(
        original[name].decode().splitlines(keepends=True),
        produced[name].decode().splitlines(keepends=True),
        fromfile="p6-postsave-recovery-v1/" + name, tofile="p6-postsave-recovery-v2/" + name))
    with (HERE / "selector-only.diff").open("x") as stream:
        stream.write(diff)
    record = {
        "schema": "hydra-p6-saved-recovery-env2-selector-derivation-v1",
        "old_sources": {name: {"path": str((OLD / name).relative_to(ROOT)), **pin(raw)}
                        for name, raw in original.items()},
        "derived_core": {name: pin(produced[name]) for name in substitutions},
        "only_core_substitutions": substitutions,
        "inverse_substitution_byte_and_ast_equal": True,
        "remote_package_unchanged": "/recovery/p6-postsave-recovery-v1",
        "remote_gpu_basename": "gpu_saved_reload_env2.py",
        "attempt": "p6-saved-recovery-1.7b-env2-01",
        "metadata_verifier_and_source_map_byte_identical": True,
        "resource_zero_work_failure_and_schema_contracts_unchanged": True,
        "old_sources_modified": False, "native_model_solver_ssh_calls": 0,
        "actual_cpu_metadata_admission_performed": False,
    }
    with (HERE / "DERIVATION.json").open("x") as stream:
        json.dump(record, stream, sort_keys=True, indent=2)
        stream.write("\n")
    assert all((OLD / name).read_bytes() == raw for name, raw in original.items())
    print(json.dumps({"derived_core": record["derived_core"],
                      "old_sources_unchanged": True, "runtime_executions": 0}))


if __name__ == "__main__":
    main()
