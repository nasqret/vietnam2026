"""File-only derivation of reviewed helper bodies; never imports/runs a recipe."""
from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
REMOTE = HERE.parent / "p6-training-launchers-v2/remote_training_control.py"
LOCAL = HERE.parent / "p6-training-launchers-v2/training_launchers.py"
SMOKE = HERE.parent / "p6-8b-smoke-launchers-v1/smoke_launchers.py"
EXPECTED = {
    REMOTE: "7c87dda334901f464cd63413fc394b4808485dd57e0449634daae9f3f4e7fb62",
    LOCAL: "966552cff6a91253b97fdc6df39ef8ed975d29fac306038af30defc5a49a5329",
    SMOKE: "38c6542d762d3bda684d8b53c47cc70e612e263c49fc5d6b151e587ab6721bd2",
}
REMOTE_NAMES = ("require", "canonical", "digest", "integer", "wall_string", "ordinary_bytes", "save",
                "fields", "tres", "check_queue_row", "check_held", "bounded_command", "Phase",
                "submit", "release", "snapshot")
LOCAL_NAMES = ("read", "put", "file_pin", "ledger_seconds", "check_charges", "phase_lock")
SMOKE_NAMES = ("ssh_once", "execute_phase", "complete_json", "validate_observation")


def extract(path, names):
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == EXPECTED[path], "Reviewed helper source changed."
    source = raw.decode()
    lines = source.splitlines(keepends=True)
    nodes = {n.name: n for n in ast.parse(source).body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    values = []
    for name in names:
        n = nodes[name]
        start = min([n.lineno] + [d.lineno for d in n.decorator_list])
        values.append("".join(lines[start - 1:n.end_lineno]).rstrip())
    return values


def main():
    marker = "\n# BEGIN EXACT REVIEWED HELPERS\n"
    remote = HERE / "remote_recovery_control.py"
    local = HERE / "recovery_launchers.py"
    additions = {
        remote: extract(REMOTE, REMOTE_NAMES),
        local: extract(LOCAL, LOCAL_NAMES) + extract(SMOKE, SMOKE_NAMES),
    }
    substitutions = {
        '"remote_smoke_control.py"': '"remote_recovery_control.py"',
        '"hydra-p6-8b-smoke-control-phase-v1"': '"hydra-p6-saved-recovery-control-phase-v1"',
    }
    for path, parts in additions.items():
        source = path.read_text()
        assert marker not in source, "Helper derivation is one-use; preserve the generated files."
        if path == local:
            parts = [__import__("functools").reduce(lambda s, p: s.replace(*p), substitutions.items(), s) for s in parts]
        source += marker + "\n\n".join(parts) + '\n\n\nif __name__ == "__main__":\n    raise SystemExit(main())\n'
        ast.parse(source)
        path.write_text(source)
    original_map = HERE.parent / "p6-source-bundle-06/controller-source-pins.json"
    with (HERE / "controller-source-pins.json").open("xb") as stream:
        stream.write(original_map.read_bytes())
    record = {"schema": "hydra-p6-saved-recovery-helper-derivation-v1",
        "sources": {str(p.relative_to(ROOT)): {"bytes": p.stat().st_size, "sha256": pin} for p, pin in EXPECTED.items()},
        "remote_helpers_unchanged": REMOTE_NAMES, "local_helpers_unchanged": LOCAL_NAMES,
        "smoke_helpers": SMOKE_NAMES, "only_helper_substitutions": substitutions,
        "old_sources_modified": False, "native_model_ssh_calls": 0}
    with (HERE / "HELPER_DERIVATION.json").open("x") as stream:
        json.dump(record, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps({"status": "derived_sources_only", "copied_remote_helpers": len(REMOTE_NAMES),
                      "copied_local_helpers": len(LOCAL_NAMES) + len(SMOKE_NAMES), "runtime_executions": 0}))


if __name__ == "__main__":
    main()
