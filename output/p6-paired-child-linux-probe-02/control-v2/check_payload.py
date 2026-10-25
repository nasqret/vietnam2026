"""One file/AST and pure payload gate. No SSH, subprocess or staging writes."""
import ast
import base64
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PAYLOAD = HERE.parent
OLD = PAYLOAD / "control"


def pin(path):
    raw = path.read_bytes()
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def functions(tree):
    return {node.name: node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef))}


def form(node):
    return ast.dump(node, include_attributes=False)


def run():
    source = ast.parse((HERE / "remote_probe_control.py").read_text())
    previous = ast.parse((OLD / "remote_probe_control.py").read_text())
    definitions, old_definitions = functions(source), functions(previous)
    assert set(definitions) - set(old_definitions) == {"decode_uploads"}
    assert not set(old_definitions) - set(definitions)
    assert {key for key in old_definitions if form(definitions[key]) != form(old_definitions[key])} == {"stage"}
    assignments = {node.targets[0].id: node.value for node in source.body
                   if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
    prior_assignments = {node.targets[0].id: node.value for node in previous.body
                         if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)}
    assert {key: form(value) for key, value in assignments.items()} == {key: form(value) for key, value in prior_assignments.items()}
    pins = ast.literal_eval(assignments["PINS"])
    uploads = ast.literal_eval(assignments["UPLOADS"])
    copies = ast.literal_eval(assignments["COPIES"])
    for name, expected in pins.items():
        assert pin(PAYLOAD / name) == expected
    assert pins["manifest.json"]["sha256"] == "4849f4b3245cca6f4c1f337a00798955e24d15df6d0568b326e24ab23efa6222"
    actual = {name: (PAYLOAD / name).read_bytes() for name in uploads}
    copied_actual = {name: (PAYLOAD / name).read_bytes() for name in copies}
    encoded = {name: base64.b64encode(raw).decode("ascii") for name, raw in actual.items()}
    namespace = {"base64": base64, "hashlib": hashlib, "PINS": pins, "UPLOADS": uploads,
                 "COPIES": copies, "SOURCE_MANIFEST": ast.literal_eval(assignments["SOURCE_MANIFEST"]), "Path": Path}
    names = ("require", "digest", "pin", "decode_uploads", "request_binding", "stage")
    module = ast.Module(body=[definitions[name] for name in names], type_ignores=[])
    exec(compile(module, "<pure-control-extract>", "exec"), namespace)
    decoded = namespace["decode_uploads"](encoded)
    assert decoded == actual and sum(map(len, decoded.values())) == 89585
    assert sum(item["bytes"] for item in pins.values()) == 110929
    rejected = []
    for label, bad in (
        ("changed_bytes", dict(encoded, **{uploads[0]: base64.b64encode(actual[uploads[0]] + b"x").decode("ascii")})),
        ("missing_file", {key: value for key, value in encoded.items() if key != uploads[0]}),
        ("extra_file", dict(encoded, **{"unlisted.py": ""})),
        ("invalid_base64", dict(encoded, **{uploads[0]: "!"})),
    ):
        try:
            namespace["decode_uploads"](bad)
        except (ValueError, TypeError):
            rejected.append(label)
        else:
            raise AssertionError("Malformed upload admitted: " + label)
    # Exercise the actual stage admission up to the existing-package guard.
    # Every filesystem/scheduler dependency below is an in-memory stub.
    effects = []
    class ExistingPackage:
        def exists(self):
            effects.append("target_exists")
            return True
        def is_symlink(self):
            raise AssertionError("Short-circuited existence rejection should be final.")
        def __str__(self):
            return "/synthetic-unit-fixture/existing-package"
    class NoCommands:
        def queue(self):
            raise AssertionError("No queue call may precede the target-absence guard.")
    def sources():
        effects.append("source_admission_stub")
        return copied_actual
    namespace.update(PACKAGE=ExistingPackage(), CAMPAIGN="/synthetic-unit-fixture",
                     verify_sources=sources, owned_directory=lambda path: effects.append("owned_directory_stub"))
    request = {"uploads": encoded, "schema": "synthetic_unit_request", "nonce": "synthetic",
               "manifest_sha256": pins["manifest.json"]["sha256"], "remote_control_sha256": "synthetic"}
    try:
        namespace["stage"](request, NoCommands())
    except ValueError as error:
        assert str(error) == "Package already exists; no staging retry."
    else:
        raise AssertionError("Existing package admitted.")
    assert effects == ["source_admission_stub", "owned_directory_stub", "target_exists"]
    first = definitions["stage"].body[0]
    assert isinstance(first, ast.Assign) and isinstance(first.value, ast.Call) and first.value.func.id == "decode_uploads"
    # Evaluate only the real producer's receipt expression in memory; do not
    # write a synthetic completion record or execute the successful write path.
    result_node = next(node.value for node in definitions["stage"].body
                       if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "result" for t in node.targets))
    namespace.update(request=request, queue=[])
    receipt = eval(compile(ast.Expression(result_node), "<pure-receipt-expression>", "eval"), namespace)
    assert receipt["uploaded_bytes"] == 89585 and receipt["payload_bytes"] == 110929
    assert receipt["uploaded_files"] == {name: pins[name] for name in uploads}
    assert receipt["copied_files"] == {name: pins[name] for name in copies}
    local, prior_local = functions(ast.parse((HERE / "probe_control.py").read_text())), functions(ast.parse((OLD / "probe_control.py").read_text()))
    assert set(local) == set(prior_local)
    assert {key for key in local if form(local[key]) != form(prior_local[key])} == {"payload_for"}
    assert any(isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
               and isinstance(node.func.value, ast.Name) and node.func.value.id == "control"
               and node.func.attr == "decode_uploads" for node in ast.walk(local["payload_for"]))
    assert not (HERE / "attempt").exists() and not (HERE / ".phase.lock").exists()
    print(json.dumps({"passed": True, "actual_payload_decoded": True, "uploaded_bytes": 89585,
        "payload_bytes": 110929, "rejections": rejected, "target_absence_guard_exercised": True,
        "actual_receipt_expression_totals_checked": True, "payload_files_unchanged": True,
        "stage_filesystem_or_scheduler_calls": 0, "source_modules_imported": False,
        "synthetic_receipts_written": False}, sort_keys=True))


if __name__ == "__main__":
    run()
