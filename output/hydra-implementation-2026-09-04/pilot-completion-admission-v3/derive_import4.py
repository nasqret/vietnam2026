"""Derive only reviewed recovery selectors and local admission-source bindings."""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
PARENT_SHA = "0a4081a7acf35f255994dd9f053f19cec0c5776cabe1d0ab42c16534a40963dc"
REPLACEMENTS = {
    'RECOVERY = "p6-postsave-recovery-v3"': 'RECOVERY = "p6-postsave-recovery-v4"',
    'CPU_REPORT = "metadata-recovery-base3.json"': 'CPU_REPORT = "metadata-recovery-import4.json"',
    'CPU_ACTUAL = "metadata-actual-completion-base3.json"': 'CPU_ACTUAL = "metadata-actual-completion-import4.json"',
    '"selector": "base3"': '"selector": "import4"',
    "3f11a9e6ef501cc4834662f01a4dd7a388892f71cae1bc70ad4a272524c5d2be": "aa2745a98bf56c54dc23d2393b0104bdf9a6ae0e14c6962dd4136c6d1f285e16",
    "7cea491f147d7feebc6478cd0589965df9c4ac106e0bbf03e3c15243c3064639": "b50a2f9c54e977d13dd1f1830cb414701631bd5f46317fe1c8346ce5c49e43e6",
    "395b00b65e0e65be5ce6cf19ca554665ced1576e4f970d7d982fc79643bf6022": "2aba491b719679e7f7b2418ce6c15d5a87d28f50d338f06f1f4e8fe950128b38",
    "a6cd9bb1495d8496b542ab8546ba26f560dfafc9bf6caa0a058e4f335424c150": "bd7bb619fb33a64c732dcd46a7e6f1e64d8f58fa27de40bc0bc4ed9eae7119c6",
}
RECOVERY_PINS = {
    "metadata_recovery.py": "aa2745a98bf56c54dc23d2393b0104bdf9a6ae0e14c6962dd4136c6d1f285e16",
    "gpu_saved_reload.py": "b50a2f9c54e977d13dd1f1830cb414701631bd5f46317fe1c8346ce5c49e43e6",
    "remote_recovery_control.py": "2aba491b719679e7f7b2418ce6c15d5a87d28f50d338f06f1f4e8fe950128b38",
    "recovery_launchers.py": "bd7bb619fb33a64c732dcd46a7e6f1e64d8f58fa27de40bc0bc4ed9eae7119c6",
}
LOCALS = {
    "paired-launchers-v4/paired_launchers.py": "4878061c1467bb411496a43d4bd70b5e75f642e99cb648d533f251aa39e539a5",
    "p7-teacher-launchers-v4/teacher_launchers.py": "45e08df1237f22ccd3f60786e527b32b207e67b8b90fe6dbcd6c9b1bab4a6562",
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def dump(raw):
    return ast.dump(ast.parse(raw), include_attributes=False)


def pin(raw):
    return {"bytes": len(raw), "sha256": digest(raw)}


def difference(before, after, old, new):
    return ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                        fromfile=old, tofile=new))


def main():
    for name, expected in RECOVERY_PINS.items():
        assert digest((BASE / "p6-postsave-recovery-v4" / name).read_bytes()) == expected
    old = BASE / "pilot-completion-admission-v2/pilot_admission.py"
    raw = old.read_bytes()
    assert digest(raw) == PARENT_SHA
    before = raw.decode()
    after = before
    for first, second in REPLACEMENTS.items():
        assert after.count(first) == 1, first
        after = after.replace(first, second)
    restored = after
    for first, second in reversed(tuple(REPLACEMENTS.items())):
        assert restored.count(second) == 1, second
        restored = restored.replace(second, first)
    assert restored == before and dump(restored) == dump(before)
    target = HERE / "pilot_admission.py"
    with target.open("xb") as stream:
        stream.write(after.encode())
    helper_sha = digest(after.encode())
    (HERE / "pilot_admission.py.diff").write_text(difference(before, after,
        old.relative_to(BASE).as_posix(), target.relative_to(BASE).as_posix()))
    records = [{"before": str(old.relative_to(BASE)), "before_pin": pin(raw),
                "after": str(target.relative_to(BASE)), "after_pin": pin(after.encode()),
                "changes": "Only four reviewed reader hashes, three import4 path selectors, and returned selector label.",
                "ast_equal_after_exact_literal_normalization": True}]
    for relative, expected in LOCALS.items():
        path = BASE / relative
        old_raw = path.read_bytes()
        assert digest(old_raw) == expected
        text = old_raw.decode()
        assert text.count(PARENT_SHA) == 1
        assert text.count("pilot-completion-admission-v2/pilot_admission.py") == 3
        changed = text.replace(PARENT_SHA, helper_sha).replace(
            "pilot-completion-admission-v2/pilot_admission.py", "pilot-completion-admission-v3/pilot_admission.py")
        restored = changed.replace(helper_sha, PARENT_SHA).replace(
            "pilot-completion-admission-v3/pilot_admission.py", "pilot-completion-admission-v2/pilot_admission.py")
        assert restored == text and dump(restored) == dump(text)
        path.write_bytes(changed.encode())
        (HERE / (path.name + ".diff")).write_text(difference(text, changed,
            "copy-transfer-gate-01/" + path.name, relative))
        records.append({"before": "paired-launchers-v4/copy-transfer-gate-01/sources/" + path.name,
                        "before_pin": pin(old_raw), "after": relative, "after_pin": pin(changed.encode()),
                        "changes": "Only explicit local admission helper path and SHA bindings.",
                        "ast_equal_after_exact_literal_normalization": True})
    for relative, expected in (
        ("paired-launchers-v4/remote_paired_control.py", "755289a7b17044c68f974245d2b5408e2099721bb01445999dd6daa407c51bb9"),
        ("p7-teacher-launchers-v4/remote_teacher_control.py", "996858ea44d346b94fdc0354a121fa5f6ba1b2651339eb802387b8284074b6be")):
        assert digest((BASE / relative).read_bytes()) == expected
    report = {"schema": "hydra-import4-downstream-binding-derivation-v1", "records": records,
              "recovery_pins": RECOVERY_PINS, "normal4_reader_unchanged": True,
              "copy_and_legacy_branches_unchanged": True, "remote_guards_byte_unchanged": True,
              "receipt_schemas_unchanged": True, "actual_pilot_admissions": 0,
              "choices_prepared": 0, "native_runs": 0, "model_calls": 0, "ssh_calls": 0}
    with (HERE / "derivation.json").open("x") as stream:
        json.dump(report, stream, sort_keys=True, indent=2)
        stream.write("\n")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
