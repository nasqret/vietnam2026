"""New local launcher copies; no phase, scheduler query, or admission runs."""
import ast
import difflib
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
BUNDLE = BASE / "combined-source-bundle-02"
MANIFEST_SHA = "ae47bb1f0b6939c3f1ca8ac406024f832fc95b50ff505cf66648e94df0e578a7"
PARENTS = {
    "paired-launchers-v2/paired_launchers.py": "89b4188d3b8c1c7adb43b23db70bb7a249aa9f322ba515c0d54e86967d409e05",
    "paired-launchers-v2/remote_paired_control.py": "a74d05cf9644faf5581ce69b5b8a28dae7a569f85ada9c69407019b89925c0a9",
    "p7-teacher-launchers-v2/teacher_launchers.py": "8e9568380794ff618f863a5df6eaab441f62c411ea7d54485a1ec6a74c5983b0",
    "p7-teacher-launchers-v2/remote_teacher_control.py": "e3d71ace0f7870d70329005237acb5435842fa364c0595fde60527e81550b099",
}
OLD_PROVIDER = "7bacd4f97272093873db76ea7b2178e1074ca3ff5f2ef88b4e411933c131580f"
OLD_ARCHIVE = "5097481cdaba15d3942ce153dc7943786c80199e9c4ccda6936419bafb494677"
OLD_MANIFEST = "e874311f7561564f84a526cff226e497cd8e9c3dcc8122f13b9871cc96ecb031"
OLD_ADMISSION = "d49c91257d107e4b0618fc35cbaac193efed0f7abf7c29f56a1e79d5ede39e8f"


def once(text, before, after):
    assert text.count(before) == 1, before
    return text.replace(before, after)


def main():
    raw_manifest = (BUNDLE / "manifest.json").read_bytes()
    assert sha256(raw_manifest).hexdigest() == MANIFEST_SHA
    manifest = json.loads(raw_manifest)
    assert manifest["file_count"] == 1325 and manifest["changed_file_count"] == 10
    helper_sha = sha256((HERE / "pilot_admission.py").read_bytes()).hexdigest()
    old_text = {}
    for name, expected in PARENTS.items():
        raw = (BASE / name).read_bytes()
        assert sha256(raw).hexdigest() == expected, name
        old_text[name] = raw.decode()
    pair_dir, teacher_dir = BASE / "paired-launchers-v3", BASE / "p7-teacher-launchers-v3"
    assert not pair_dir.exists() and not teacher_dir.exists(), "New launcher folders only."

    def local_bindings(text):
        text = once(text, '"combined-source-bundle-01"', '"combined-source-bundle-02"')
        text = once(text, OLD_ADMISSION, helper_sha)
        assert 'pilot-completion-admission-v1/pilot_admission.py' in text
        return text.replace('pilot-completion-admission-v1/pilot_admission.py',
                            'pilot-completion-admission-v2/pilot_admission.py')

    def remote_bindings(text):
        for before, after in (("/bundles/combined-source-01/source", "/bundles/combined-source-02/source"),
                              (OLD_ARCHIVE, manifest["archive_sha256"]), (OLD_MANIFEST, MANIFEST_SHA)):
            text = once(text, before, after)
        return text

    pair = local_bindings(old_text["paired-launchers-v2/paired_launchers.py"])
    pair = once(pair, 'manifest["file_count"] == 1301', 'manifest["file_count"] == 1325')
    pair = once(pair, 'transferred.get("verified_files") == 1301',
                'transferred.get("verified_files") == 1325 and transferred.get("verified_bytes") == 112065712')
    pair = once(pair, "actual combined-source-01 transfer", "actual combined-source-02 transfer")
    pair = once(pair, '"hydra-paired-launch-choice-v2"', '"hydra-paired-launch-choice-v3"')
    pair = pair.replace('"hydra-prepared-paired-launch-v2"', '"hydra-prepared-paired-launch-v3"')
    pair_remote = remote_bindings(old_text["paired-launchers-v2/remote_paired_control.py"])
    pair_remote = once(pair_remote, "382098dc8a3f9d79370006d874e4afef23a83896486cd686b87f0d7397040395",
                       manifest["paired_source_map_sha256"])
    pair_remote = once(pair_remote, "395849fde6e363a96a67aab3fbb7c8f5f82e2a8a6919eb123009ff108800a16d",
                       manifest["files"]["output/hydra-implementation-2026-09-04/paired-evaluation-v2/paired_common.py"]["sha256"])
    pair_remote = once(pair_remote, '+ "-v2-01"', '+ "-v3-01"')

    teacher = local_bindings(old_text["p7-teacher-launchers-v2/teacher_launchers.py"])
    teacher = once(teacher, '"f16f46a9cbb98950749e9b67eb0b3818f011ce25256be6285a962700e4fd13da"',
                   repr(manifest["files"]["output/p7-prototype/staged/experimental_teacher.py"]["sha256"]))
    teacher = once(teacher, OLD_PROVIDER, manifest["provider_sha256"])
    teacher = once(teacher, "def bundle_inputs():", "def bundle_inputs(choice):")
    begin = teacher.index('    transfer = json.loads(read(HERE.parent / "cpu-fixture-01/upload/actual-completion.json",')
    end = teacher.index('    prior = json.loads(read(HERE.parent / "p7-clean-base-admission-01/stdout.json",', begin)
    transfer_code = '''    require(type(choice.get("transfer")) is dict
            and set(choice["transfer"]) == {"response", "actual_completion"},
            "Both real combined-source-02 transfer descriptors are required.")
    admission = admission_api()
    inputs = admission.Evidence(ROOT)
    transfer = admission.strict_json(inputs.descriptor(choice["transfer"]["actual_completion"], 65536))
    upload = admission.strict_json(inputs.descriptor(choice["transfer"]["response"], 2 * 1024**2))
    require(type(transfer.get("actual_ssh_exit_code")) is int and transfer["actual_ssh_exit_code"] == 0
            and transfer.get("transport_timeout") is False and transfer.get("operation") == "upload"
            and transfer.get("remote_bundle") == str(Path(control.SOURCE).parent)
            and upload.get("schema") == "hydra-combined-source-upload-v1"
            and upload.get("archive_sha256") == control.ARCHIVE_SHA
            and upload.get("manifest_sha256") == control.MANIFEST_SHA and upload.get("source") == control.SOURCE
            and upload.get("verified_files") == 1325 and upload.get("verified_bytes") == 112065712,
            "Exact combined-source-02 upload has not completed.")
'''
    teacher = teacher[:begin] + transfer_code + teacher[end:]
    teacher = once(teacher, '{"schema", "seconds", "throughput", "fresh_pilots"}',
                   '{"schema", "seconds", "throughput", "fresh_pilots", "transfer"}')
    teacher = once(teacher, '"hydra-p7-teacher-allocation-choice-v2"', '"hydra-p7-teacher-allocation-choice-v3"')
    teacher = teacher.replace('"hydra-p7-prepared-teacher-launch-v2"', '"hydra-p7-prepared-teacher-launch-v3"')
    assert teacher.count("source_map = bundle_inputs()") == 2
    teacher = teacher.replace("source_map = bundle_inputs()", "source_map = bundle_inputs(choice)")
    teacher_remote = remote_bindings(old_text["p7-teacher-launchers-v2/remote_teacher_control.py"])
    teacher_remote = once(teacher_remote, '"p7-teacher-32-v2-01"', '"p7-teacher-32-v3-01"')
    teacher_remote = once(teacher_remote, "f3bad0a87debd9f661ba5a239814e52ba50ba96d7fdfff0adeeca8cf1f25b3b1",
                          manifest["teacher_source_map_sha256"])
    outputs = {
        "paired-launchers-v3/paired_launchers.py": pair,
        "paired-launchers-v3/remote_paired_control.py": pair_remote,
        "p7-teacher-launchers-v3/teacher_launchers.py": teacher,
        "p7-teacher-launchers-v3/remote_teacher_control.py": teacher_remote,
    }
    audit, diffs = {}, []
    for name, text in outputs.items():
        parent_name = name.replace("launchers-v3/", "launchers-v2/")
        before = old_text[parent_name]
        before_tree, after_tree = ast.parse(before), ast.parse(text)
        def bodies(tree):
            return {n.name: ast.dump(n, include_attributes=False) for n in tree.body
                    if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
        old, new = bodies(before_tree), bodies(after_tree)
        assert set(old) == set(new), name
        changes = sorted(n for n in old if old[n] != new[n])
        audit[name] = {"parent": parent_name, "parent_sha256": PARENTS[parent_name],
            "sha256": sha256(text.encode()).hexdigest(), "bytes": len(text.encode()),
            "changed_callable_names": changes, "identical_callable_names": sorted(set(old) - set(changes))}
        diffs.extend(difflib.unified_diff(before.splitlines(True), text.splitlines(True),
                                        fromfile=parent_name, tofile=name))
    assert audit["paired-launchers-v3/remote_paired_control.py"]["changed_callable_names"] == ["attempt"]
    assert audit["p7-teacher-launchers-v3/remote_teacher_control.py"]["changed_callable_names"] == []
    for directory in (pair_dir, teacher_dir):
        directory.mkdir()
    for name, text in outputs.items():
        with (BASE / name).open("x") as stream:
            stream.write(text)
    with (HERE / "launcher-changes.diff").open("x") as stream:
        stream.write("".join(diffs))
    result = {"schema": "hydra-base3-downstream-launcher-derivation-v1", "files": audit,
        "admission_sha256": helper_sha, "combined_manifest_sha256": MANIFEST_SHA,
        "actual_pilot_admissions": 0, "prepared_job_choices": 0, "ssh_calls": 0,
        "model_calls": 0, "native_calls": 0, "allocations": 0, "automatic_retry": False}
    with (HERE / "launcher-derivation.json").open("x") as stream:
        json.dump(result, stream, sort_keys=True, indent=2); stream.write("\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
