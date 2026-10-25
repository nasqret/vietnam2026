"""File/AST-only derivation from sealed P6-v2; never imports application code."""
import ast
import difflib
from hashlib import sha256
import json
from pathlib import Path
import pprint

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "p6-training-launchers-v2"
PINS = {"remote_training_control.py": "7c87dda334901f464cd63413fc394b4808485dd57e0449634daae9f3f4e7fb62",
        "training_launchers.py": "966552cff6a91253b97fdc6df39ef8ed975d29fac306038af30defc5a49a5329"}


def once(text, old, new):
    assert text.count(old) == 1, repr(old)
    return text.replace(old, new)


def functions(text):
    return {node.name: ast.get_source_segment(text, node) for node in ast.parse(text).body if isinstance(node, ast.FunctionDef)}


def main():
    originals = {}
    for name, expected in PINS.items():
        raw = (OLD / name).read_bytes()
        assert sha256(raw).hexdigest() == expected
        originals[name] = raw.decode()
    launch_raw = (HERE.parent / "p6-source-bundle-06/training-launch-inputs.json").read_bytes()
    assert sha256(launch_raw).hexdigest() == "6ae22bd1075f7e83ad1ff427dbe468eeb5e38f30619e98ea7fcc71d48aae6e88"
    launch = json.loads(launch_raw)
    model = launch["models"]["qwen3-8b-base"]
    new_model = {"qwen3-8b-base": {"attempt": "p6-training-fresh-8b-v2-01", "config": model["config"],
        "config_sha256": model["config_sha256"], "plan_sha256": model["plan_sha256"],
        "artifact": model["future_artifact_directory"], "model": model["model"]}}
    remote = originals["remote_training_control.py"]
    node = next(node for node in ast.parse(remote).body if isinstance(node, ast.Assign)
                and any(isinstance(target, ast.Name) and target.id == "MODELS" for target in node.targets))
    remote = once(remote, ast.get_source_segment(remote, node), "MODELS = " + pprint.pformat(new_model, width=120, sort_dicts=True))
    remote = once(remote, "Only the two reviewed fresh model configs are allowed.", "Only the reviewed fresh 8B config is allowed.")
    remote = once(remote, "This draft is bound exclusively to sealed bundle06/source-data-07.",
        "This separate 8B-only extension is bound exclusively to sealed bundle06/source-data-07.")
    local = originals["training_launchers.py"]
    local = once(local, "import json\n", "import json\nimport importlib.util\n")
    source_functions = functions(local)
    block = source_functions["validate_choice"]
    block = once(block, '"transfer_receipt", "base_admission"}', '"transfer_receipt", "base_admission", "completed_8b_smoke"}')
    block = once(block, '"hydra-p6-training-allocation-choice-v1"', '"hydra-p6-8b-training-allocation-choice-v1"')
    block = once(block, "Only fresh 1.7B or 4B is allowed.", "Only the fixed fresh 8B pass is allowed.")
    local = once(local, source_functions["validate_choice"], block)
    block = source_functions["prepare"]
    block = once(block, "manifest, launch, source_map = bundle_inputs()", "manifest, launch, source_map = bundle_inputs()\n    smoke_admission = admit_completed_smoke(choice)")
    block = once(block, 'ledger, ledger_raw, used = current_ledger(args.ledger_sha256, choice["model_key"])',
        'ledger, ledger_raw, used = current_ledger(args.ledger_sha256, choice["model_key"])\n    check_completed_predecessor_charges(ledger, smoke_admission)')
    assert block.count('control.MODELS["qwen3-4b-base"]') == 2
    block = block.replace('control.MODELS["qwen3-4b-base"]', 'control.MODELS["qwen3-8b-base"]')
    block = once(block, "actual eight-example 4B throughput", "actual eight-example 8B throughput")
    block = once(block, '"spec": spec, "choice": file_pin(directory / "choice.json"),',
        '"spec": spec, "smoke_admission": smoke_admission, "choice": file_pin(directory / "choice.json"),')
    local = once(local, source_functions["prepare"], block)
    block = source_functions["load_prepared"]
    block = once(block, "def load_prepared(model_key, expected):", "def load_prepared(model_key, expected, *, recheck_smoke=True):")
    block = once(block, 'read(directory / "choice.json", prepared["choice"]["sha256"])',
        'choice = json.loads(read(directory / "choice.json", prepared["choice"]["sha256"]))\n    if recheck_smoke:\n        require(admit_completed_smoke(choice) == prepared["smoke_admission"], "Prior completed smoke/pilot inputs changed.")')
    local = once(local, source_functions["load_prepared"], block)
    block = source_functions["mutate_phase"]
    block = once(block, "ledger, ledger_raw, used = current_ledger(args.ledger_sha256, args.model_key)",
        'ledger, ledger_raw, used = current_ledger(args.ledger_sha256, args.model_key)\n    check_completed_predecessor_charges(ledger, prepared["smoke_admission"])')
    local = once(local, source_functions["mutate_phase"], block)
    block = source_functions["collect"]
    block = once(block, "load_prepared(args.model_key, args.prepared_sha256)",
        "load_prepared(args.model_key, args.prepared_sha256, recheck_smoke=False)")
    local = once(local, source_functions["collect"], block)
    fragment = (HERE / "admission.fragment.py").read_text()
    fragment_functions = functions(fragment)
    local = once(local, source_functions["current_ledger"], fragment_functions["current_ledger"])
    fragment = once(fragment, fragment_functions["current_ledger"], "")
    local = once(local, 'if __name__ == "__main__":', fragment + '\n\nif __name__ == "__main__":')
    local = once(local, "Explicit, one-use P6 preparation/submission/release/collection; no defaults.",
        "Explicit, conditional 8B-only P6 extension; no duration or next-phase defaults.")
    for name, value in (("remote_training_control.py", remote), ("training_launchers.py", local)):
        ast.parse(value)
        with (HERE / name).open("x") as stream:
            stream.write(value)
        diff = "".join(difflib.unified_diff(originals[name].splitlines(keepends=True), value.splitlines(keepends=True),
                                         fromfile="sealed-p6-v2/" + name, tofile="8b-extension/" + name))
        with (HERE / (name + ".diff")).open("x") as stream:
            stream.write(diff)
        print(json.dumps({"file": name, "bytes": len(value.encode()), "sha256": sha256(value.encode()).hexdigest(),
                          "original_sha256": PINS[name]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
