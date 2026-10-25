"""Create only new local launcher derivatives; no launcher phase is executed."""
import ast
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
BASE_PINS = {
    "paired-launchers-v1/paired_launchers.py": "b16084125a6a1f6f4a0b05c6120c4cf9ee3b81327aac9ebaf9cb31852848d5aa",
    "paired-launchers-v1/remote_paired_control.py": "e905a9ac0941676790b290b8d154560ef3d93c4760e51d82914d554c9349baf3",
    "p7-teacher-launchers-v1/teacher_launchers.py": "ae5f8a938ebea2e5c92f5769ac4c643e4710c089d3e8896dd99938be1c79741a",
    "p7-teacher-launchers-v1/remote_teacher_control.py": "e3d71ace0f7870d70329005237acb5435842fa364c0595fde60527e81550b099",
}


def source(name):
    raw = (BASE / name).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == BASE_PINS[name], name
    return raw.decode()


def function(text, old, new):
    tree = ast.parse(text)
    matches = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == old]
    assert len(matches) == 1, old
    node = matches[0]
    lines = text.splitlines(keepends=True)
    return "".join(lines[:node.lineno - 1]) + new.strip() + "\n" + "".join(lines[node.end_lineno:])


def once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after)


LOADER = '''
def admission_api():
    path = HERE.parent / "pilot-completion-admission-v1/pilot_admission.py"
    raw = read(path, ADMISSION_SHA, 128 * 1024)
    spec = importlib.util.spec_from_file_location("_explicit_pilot_admission", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module
'''

ADMIT = '''
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
'''

PATTERNS = '''("p6-training-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-8b-smoke-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-8b-training-launchers-v*/attempts/*/release/charge-intent.json",
        "paired-launchers-v*/prepared/arms/*/release/charge-intent.json",
        "p7-teacher-launchers-v*/attempts/*/release/charge-intent.json",
        "p7-student-launchers-v*/attempts/*/release/charge-intent.json",
        "p6-postsave-recovery-v*/attempts/*/release/charge-intent.json")'''


def main():
    pair_dir, teacher_dir = BASE / "paired-launchers-v2", BASE / "p7-teacher-launchers-v2"
    assert not pair_dir.exists() and not teacher_dir.exists(), "New output directories only."
    helper_sha = hashlib.sha256((HERE / "pilot_admission.py").read_bytes()).hexdigest()
    pair = source("paired-launchers-v1/paired_launchers.py")
    pair = once(pair, 'TRAINING_PINS = {"training_launchers.py": "966552cff6a91253b97fdc6df39ef8ed975d29fac306038af30defc5a49a5329",\n    "remote_training_control.py": "7c87dda334901f464cd63413fc394b4808485dd57e0449634daae9f3f4e7fb62"}',
                'ADMISSION_SHA = "' + helper_sha + '"')
    pair = function(pair, "training_reader", LOADER)
    pair = function(pair, "admit_training", ADMIT)
    pair = function(pair, "charge_records", '''
def charge_records():
    patterns = ''' + PATTERNS + '''
    paths = sorted({path for pattern in patterns for path in BASE.glob(pattern)})
    require(len(paths) <= 64, "Unexpected bounded cross-campaign charge history.")
    return [json.loads(read(path, limit=65536)) for path in paths]
''')
    pair = once(pair, 'choice["schema"] == "hydra-paired-launch-choice-v1"', 'choice["schema"] == "hydra-paired-launch-choice-v2"')
    pair = pair.replace('"hydra-prepared-paired-launch-v1"', '"hydra-prepared-paired-launch-v2"')
    pair = once(pair, "reader = training_reader()", "reader = admission_api()")
    pair = once(pair, 'ledger, ledger_raw, used = current_ledger(args.ledger_sha256)\n    seconds =',
                'ledger, ledger_raw, used = current_ledger(args.ledger_sha256)\n    reader.require_pilot_charges(ledger, admissions.values())\n    seconds =')
    pair = once(pair, '"training_metadata_reader_pins": TRAINING_PINS,',
                '"training_metadata_reader_pins": reader.PINNED,\n        "admission_source": file_pin(BASE / "pilot-completion-admission-v1/pilot_admission.py"),')
    pair = once(pair, 'control.validate_study(json.loads(raw), BUNDLE / "source")',
                'study = json.loads(raw)\n    api = control.validate_study(study, BUNDLE / "source")\n    reader = admission_api()\n    require(file_pin(BASE / "pilot-completion-admission-v1/pilot_admission.py") == prepared["admission_source"],\n            "Pilot admission helper changed after preparation.")\n    choice = json.loads(read(PREPARED / "choice.json", prepared["choice"]["sha256"]))\n    admissions = {name: admit_training(name, choice["fresh_training"][name], study, api, reader)\n                  for name in ("fresh_1_7b", "fresh_4b")}\n    require(admissions == prepared["fresh_training_admissions"], "Pilot admission evidence changed after preparation.")')
    pair = once(pair, 'ledger, ledger_raw, used = current_ledger(args.ledger_sha256, args.arm)\n    require(',
                'ledger, ledger_raw, used = current_ledger(args.ledger_sha256, args.arm)\n    admission_api().require_pilot_charges(ledger, prepared["fresh_training_admissions"].values())\n    require(')

    pair_remote = source("paired-launchers-v1/remote_paired_control.py")
    pair_remote = once(pair_remote, '"fresh_4b": TRAINING_SOURCE + "/output/hydra-implementation-2026-09-04/training-fresh-4b-v2-01"',
                       '"fresh_4b": CAMPAIGN + "/bundles/source-data-08/source/output/hydra-implementation-2026-09-04/training-fresh-4b-v2-01"')

    teacher = source("p7-teacher-launchers-v1/teacher_launchers.py")
    teacher = once(teacher, "import hashlib\n", "import hashlib\nimport importlib.util\n")
    teacher = once(teacher, "require, canonical, digest = control.require, control.canonical, control.digest\n",
                   'ADMISSION_SHA = "' + helper_sha + '"\nrequire, canonical, digest = control.require, control.canonical, control.digest\n\n' + LOADER)
    old_patterns = '''("p6-training-launchers-v*/attempts/*/release/charge-intent.json",
                    "paired-launchers-v*/prepared/arms/*/release/charge-intent.json",
                    "p7-teacher-launchers-v*/attempts/*/release/charge-intent.json")'''
    teacher = once(teacher, old_patterns, PATTERNS)
    teacher = once(teacher, 'choice["schema"] == "hydra-p7-teacher-allocation-choice-v1"',
                   'choice["schema"] == "hydra-p7-teacher-allocation-choice-v2"')
    tree = ast.parse(teacher)
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "verify_prerequisites")
    before = "".join(teacher.splitlines(keepends=True)[node.lineno - 1:node.end_lineno])
    verify = before[:before.index('    for model, reference in choice["fresh_pilots"].items():')]
    verify += '    return admission_api().admit_pair(choice["fresh_pilots"], root=ROOT)\n'
    teacher = function(teacher, "verify_prerequisites", verify)
    teacher = teacher.replace('"hydra-p7-prepared-teacher-launch-v1"', '"hydra-p7-prepared-teacher-launch-v2"')
    teacher = teacher.replace("    verify_prerequisites(choice)\n", "    admissions = verify_prerequisites(choice)\n")
    teacher = once(teacher, 'ledger, ledger_raw, used = current_ledger(args.ledger_sha256)\n    require(used + choice["seconds"]',
                   'ledger, ledger_raw, used = current_ledger(args.ledger_sha256)\n    admission_api().require_pilot_charges(ledger, admissions.values())\n    require(used + choice["seconds"]')
    teacher = once(teacher, '"base_identity_sha256": control.BASE_IDENTITY_SHA, "automatic_retry": False, "automatic_launch": False}',
                   '"base_identity_sha256": control.BASE_IDENTITY_SHA, "automatic_retry": False, "automatic_launch": False,\n        "pilot_admissions": admissions,\n        "admission_source": file_pin(HERE.parent / "pilot-completion-admission-v1/pilot_admission.py")}')
    teacher = once(teacher, '    admissions = verify_prerequisites(choice)\n    require(choice["seconds"]',
                   '    admissions = verify_prerequisites(choice)\n    require(admissions == prepared["pilot_admissions"]\n            and file_pin(HERE.parent / "pilot-completion-admission-v1/pilot_admission.py") == prepared["admission_source"],\n            "Pilot admission evidence/helper changed after preparation.")\n    require(choice["seconds"]')
    teacher = once(teacher, 'ledger, ledger_raw, used = current_ledger(args.ledger_sha256)\n    require(used + spec["seconds"]',
                   'ledger, ledger_raw, used = current_ledger(args.ledger_sha256)\n    admission_api().require_pilot_charges(ledger, prepared["pilot_admissions"].values())\n    require(used + spec["seconds"]')
    teacher_remote = source("p7-teacher-launchers-v1/remote_teacher_control.py")
    outputs = {
        pair_dir / "paired_launchers.py": pair,
        pair_dir / "remote_paired_control.py": pair_remote,
        teacher_dir / "teacher_launchers.py": teacher,
        teacher_dir / "remote_teacher_control.py": teacher_remote,
    }
    for path, text in outputs.items():
        compile(text, str(path), "exec")
    pair_dir.mkdir(); teacher_dir.mkdir()
    for path, text in outputs.items():
        with path.open("x") as stream:
            stream.write(text)
    print("Created four new launcher files; old sources and all runtime payloads unchanged.")


if __name__ == "__main__":
    main()
