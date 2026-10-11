#!/usr/bin/env python3
"""Fresh staged Lean compilation and independent same-byte bundle checking.

No Lake, external C compiler, installed-toolchain mutation, Mathlib import,
certificate generation, or cached project olean is used. The existing checker
sources are copied byte-for-byte into a NEW temporary module tree. Every child
is sequential and OS-bounded. Reported receipts are observations, not axioms.
"""
from hashlib import sha256
import argparse
import gzip
import io
import json
from pathlib import Path
import sys
import tempfile
import time

from run_sqrt2_power_pilot import ROOT, controller_deadline, successful, save_new
from sqrt2_power_automation_baseline import runtime
from sqrt2_power_pilot_contracts import canonical

LEAN_REPO = ROOT.parent / "peano-lab-lean"
LEAN = Path("/Users/bnaskrecki/.elan/toolchains/leanprover--lean4---v4.31.0/bin/lean")
MODULES = ("Syntax", "Substitution", "Derivation", "Semantics", "Checker", "Soundness",
           "Codec", "ProofBundle", "VerifyBundle")
AUDIT_SHA256 = "59b5d0e5897ffac038415af3a11c61db6c8c36f990bb32b59739959813f62253"
AUDIT_OUTPUT = ("'PeanoLab.checkBundle_derives' depends on axioms: [propext, Quot.sound]\n"
    "'PeanoLab.checkBundle_sound' depends on axioms: [propext, Classical.choice, Quot.sound]\n")
SOURCE_SHA256 = (
    "de8dcfd73db4a9e6dc23c8c73f41c15e1d8039ef9f64df6a510285f49158ae3d",
    "e805bc97c64b3169af8d84993ef4ce9bbd3479d6ddfd71824b1c228009b63b22",
    "ba05f624957db3058f3c3e41d6005d067ca2f2b7c5dd1130655e0d36d23586d3",
    "86509169edc2ebcbd8491ef435c133d840f7617cd9596b344edb08774fbea197",
    "e531a9f0da534e601dc4637e990424a6a998c3ccfe6d48823da8f6450e2d9dc0",
    "379e043d06e4abb7127fd3642c398b7dff86057cef1f29702206fcfd0f3c8fee",
    "398ece06d5daf66d2d737013645dbb04628e072bd1a7610541cd22bcfa8cfb57",
    "02ee6d0ee44a3886e9adcfc41f9658d80a114dec694dd9844777f9cd0ff80bcf",
    "9479850d6be70b73ad2cdf5543c0a1d8521e279e38d8b3a34cff1fe10a7e0831",
)


def read_member(folder, phase, report):
    record = report["process_records"][phase]
    path = folder / record["path"]
    if path.parent != folder or path.is_symlink():
        raise ValueError("unsafe process record")
    with gzip.GzipFile(fileobj=io.BytesIO(path.read_bytes())) as stream:
        raw = stream.read(16*1024**2+1)
    if len(raw) > 16*1024**2 or sha256(raw).hexdigest() != record["raw_sha256"]:
        raise ValueError("changed process bytes")
    process = json.loads(raw)
    if not successful(process):
        raise ValueError("not a successful process")
    if sha256(process["stdout"].encode()).hexdigest() != process["stdout_sha256"]:
        raise ValueError("changed original process output")
    return json.loads(process["stdout"])


def exact_bundle(folder):
    from run_sqrt2_power_wave import SCHEMA, target_for, formula_sha256
    report_raw = (folder / "report.json").read_bytes()
    report = json.loads(report_raw)
    if (report.get("schema") != SCHEMA or report.get("status") != "fresh_ordinary_HA_checked"
        or report.get("IR_parents_closed") != 0 or report.get("library_admissions") != 0):
        raise ValueError("not a fresh-HA wave observation")
    producer = read_member(folder, "generation", report)
    replay = read_member(folder, "fresh_replay", report)
    for value in (producer, replay):
        if (value.get("schema") != SCHEMA or value.get("case") != report.get("case")
            or value.get("source_pins") != report.get("source_pins")
            or value.get("IR_parents_closed") != 0):
            raise ValueError("case/source boundary differs between original processes")
    expected_target_hash = formula_sha256(target_for(report["case"]))
    if producer.get("target_ast_sha256") != expected_target_hash or replay.get("target_ast_sha256") != expected_target_hash:
        raise ValueError("certificate is not the independently frozen case target")
    if set(report.get("source_snapshots", {})) != set(report["source_pins"]):
        raise ValueError("missing archived source snapshots")
    for name, pin in report["source_pins"].items():
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts or str(relative) != name:
            raise ValueError("unsafe archived source path")
        saved = "sources/" + name + ".gz"
        if report["source_snapshots"][name] != saved or not 0 < pin["bytes"] <= 16*1024**2:
            raise ValueError("changed archived source binding")
        path = folder / saved
        if path.is_symlink() or path.resolve().is_relative_to(folder.resolve()) is False:
            raise ValueError("archived source escapes original observation")
        with gzip.GzipFile(fileobj=io.BytesIO(path.read_bytes())) as stream:
            raw = stream.read(pin["bytes"]+1)
        if len(raw) != pin["bytes"] or sha256(raw).hexdigest() != pin["sha256"]:
            raise ValueError("archived source bytes differ from original pins")
    payload = producer["bundle"].encode()
    digest = sha256(payload).hexdigest()
    if (len(payload) > 8*1024**2 or digest != producer["bundle_sha256"]
        or digest != replay["bundle_sha256"] or replay["target_ast_sha256"] != producer["target_ast_sha256"]
        or replay["status"] != "fresh_ordinary_HA_checked"):
        raise ValueError("certificate differs from fresh-HA bytes")
    tree = json.loads(payload)
    if (tree[0] != "peano-lab-bundle-v1" or len(tree) != 4
        or len(tree[3]) != replay["local_nodes"]
        or sha256(canonical(tree[2])).hexdigest() != replay["target_ast_sha256"]):
        raise ValueError("not an ordinary bundle")
    return payload, dict(case=report["case"], original_observation=str(folder.relative_to(ROOT)),
        report_sha256=sha256(report_raw).hexdigest(), bundle_sha256=digest,
        bundle_bytes=len(payload), nodes=replay["local_nodes"], root=tree[1],
        target_ast_sha256=replay["target_ast_sha256"])


def toolchain_library_names(platform=None):
    """Explicit platform inventories; missing libraries never silently skip pins."""
    platform = sys.platform if platform is None else platform
    if platform not in {"darwin", "linux"}:
        raise ValueError("fresh Lean checks require macOS or Linux")
    suffix = "dylib" if platform == "darwin" else "so"
    return ("Init.olean", "Lean.olean", *(name + "." + suffix for name in
        ("libleanshared", "libInit_shared", "libleanshared_1", "libleanshared_2")))


def resource_settings(profile):
    if profile == "local":
        return dict(phases=dict(version=(1, 3), build=(10, 15), check=(20, 30), negative=(5, 10)),
            rss_bytes=768*1024**2, controller_base_wall=170)
    if profile == "wmi-ap090-v2":
        from sqrt2_power_wmi_resources import LEAN_PHASES, WORKER_RSS_BYTES
        return dict(phases=dict(LEAN_PHASES), rss_bytes=WORKER_RSS_BYTES, controller_base_wall=1080)
    raise ValueError("unknown explicit Lean resource profile")


def execute(output, folders, *, lean=None, lean_repo=None, resource_profile="local"):
    if output.exists() or output.is_symlink() or not folders:
        raise ValueError("new output and explicit observations required")
    lean = LEAN if lean is None else Path(lean)
    lean_repo = LEAN_REPO if lean_repo is None else Path(lean_repo)
    if not lean.is_absolute() or not lean_repo.is_absolute():
        raise ValueError("explicit absolute Lean executable and source paths required")
    settings = resource_settings(resource_profile)
    if resource_profile != "local":
        from sqrt2_power_wmi_resources import require_allocation
        require_allocation()
    phases = settings["phases"]
    controller_wall = settings["controller_base_wall"] + phases["check"][1]*len(folders)
    # These exact paths are configured project sources, never ambient search.
    sources = {f"PeanoLab/{name}.lean": (lean_repo / "PeanoLab" / f"{name}.lean").read_bytes()
               for name in MODULES}
    if any(sha256(sources[f"PeanoLab/{name}.lean"]).hexdigest() != pin
           for name, pin in zip(MODULES, SOURCE_SHA256)):
        raise ValueError("audited Lean checker sources changed")
    sources["Sqrt2PowerLeanAudit.lean"] = (ROOT / "scripts/assets/Sqrt2PowerLeanAudit.lean").read_bytes()
    if sha256(sources["Sqrt2PowerLeanAudit.lean"]).hexdigest() != AUDIT_SHA256:
        raise ValueError("frozen Lean endpoint audit source changed")
    if resource_profile == "local":
        supervisor = runtime()
    else:
        from sqrt2_power_wmi_lean_runtime import lean_runtime
        supervisor = lean_runtime()
    stage = Path(tempfile.mkdtemp(prefix="sqrt2-fresh-lean-"))
    report = dict(schema="sqrt2-power-fresh-lean-v1", authority="independent_local_check_not_admission",
        stage=str(stage), lean_binary=supervisor.hash_file(lean), source_pins={}, compilation=[], checks=[],
        platform=sys.platform, lean_executable=str(lean), lean_source_root=str(lean_repo),
        resource_profile=resource_profile,
        status="incomplete", IR_parents_closed=0, library_admissions=0,
        mode="fresh_olean_closure_and_Lean_run_not_standalone_C_build")
    for name, raw in sources.items():
        save_new(stage / name, raw)
        save_new(output / "sources" / name, raw)
        report["source_pins"][name] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
    for name in toolchain_library_names():
        report.setdefault("toolchain_library_pins", {})[name] = supervisor.hash_file(lean.parent.parent / "lib/lean" / name)
    if resource_profile != "local":
        for name in ("scripts/sqrt2_power_wmi_lean_guard.py", "scripts/sqrt2_power_wmi_lean_runtime.py",
                "scripts/sqrt2_power_wmi_resources.py", "training/peano_hydra/review_runtime.py"):
            raw = (ROOT/name).read_bytes()
            save_new(output/"runtime-sources"/name,raw)
            report.setdefault("execution_runtime_sources",{})[name] = dict(bytes=len(raw),sha256=sha256(raw).hexdigest())
    common = (str(lean), "-j", "1", "-M", str(settings["rss_bytes"]//1024**2), "-R", str(stage))
    started = time.monotonic()
    process_index = 0
    def run(argv, cpu, wall):
        nonlocal process_index
        limits = supervisor.ProcessLimits(cpu_seconds=cpu, wall_seconds=wall,
            rss_bytes=settings["rss_bytes"], output_bytes=1024**2)
        process = supervisor.run_bounded(tuple(argv), cwd=stage, limits=limits, lean_path=stage)
        supervisor.validate_process_record(process, command=tuple(argv), limits=limits)
        save_new(output / "processes" / f"{process_index:02d}.json",
            json.dumps(process, sort_keys=True, indent=2).encode()+b"\n")
        process_index += 1
        return process
    with controller_deadline(started+controller_wall):
        version = run((str(lean), "-j", "1", "--version"), *phases["version"])
        report["version_probe"] = version
        if not successful(version) or "version 4.31.0" not in version["stdout"]:
            raise ValueError("unexpected configured Lean version")
        for name in MODULES:
            source, compiled = stage / "PeanoLab" / (name+".lean"), stage / "PeanoLab" / (name+".olean")
            process = run((*common, "-o", str(compiled), str(source)), *phases["build"])
            report["compilation"].append(dict(module=name, process=process))
            if not successful(process) or "declaration uses 'sorry'" in process["stdout"]:
                break
            report["compilation"][-1]["olean"] = supervisor.hash_file(compiled)
        if len(report["compilation"]) == len(MODULES) and all(successful(r["process"]) for r in report["compilation"]):
            audit = run((*common, str(stage / "Sqrt2PowerLeanAudit.lean")), *phases["build"])
            report["axiom_audit"] = audit
            if not successful(audit) or audit["stdout"] != AUDIT_OUTPUT or audit["stderr"] != "":
                raise ValueError("fresh endpoint axiom audit failed")
            for folder in folders:
                payload, row = exact_bundle(folder)
                path = stage / "certificates" / (row["case"]+".json")
                save_new(path, payload)
                process = run((*common, "--run", str(stage / "PeanoLab/VerifyBundle.lean"), str(path)), *phases["check"])
                expected = f"ACCEPT\t{path}\tnodes={row['nodes']}\troot={row['root']}\n"
                accepted = (successful(process) and process["stderr"] == ""
                    and process["stdout"] == expected)
                report["checks"].append(dict(row, process=process, independent_lean_checked=accepted))
            report["negative_controls"] = []
            original, original_row = exact_bundle(folders[0])
            for label in ("false-caller-target", "forged-root-body"):
                tree = json.loads(original)
                if label == "false-caller-target":
                    tree[2] = ["bot"]
                else:
                    tree[3][tree[1]][3] = ["eq_refl", ["zero"]]
                raw = canonical(tree)+b"\n"
                path = stage / "certificates" / (label+".json")
                save_new(path, raw)
                process = run((*common, "--run", str(stage / "PeanoLab/VerifyBundle.lean"), str(path)), *phases["negative"])
                rejected = (process["reason"] == "exited" and process["returncode"] == 1
                    and process["stdout"] == "REJECT\t"+str(path)+"\n" and process["stderr"] == "")
                report["negative_controls"].append(dict(kind=label, original_bundle_sha256=original_row["bundle_sha256"],
                    mutated_bundle_sha256=sha256(raw).hexdigest(), process=process, rejected=rejected))
            report["status"] = "fresh_lean_checked" if all(r["independent_lean_checked"] for r in report["checks"]) else "some_checks_failed"
            if not all(r["rejected"] for r in report["negative_controls"]):
                report["status"] = "negative_control_failed"
        if supervisor.hash_file(lean) != report["lean_binary"]:
            raise ValueError("Lean binary changed during run")
        for name, pin in report["toolchain_library_pins"].items():
            if supervisor.hash_file(lean.parent.parent / "lib/lean" / name) != pin:
                raise ValueError("Lean toolchain library changed during run")
        for name, raw in sources.items():
            if (stage / name).read_bytes() != raw:
                raise ValueError("staged checker source changed")
        for name,pin in report.get("execution_runtime_sources",{}).items():
            if supervisor.hash_file(ROOT/name)!=pin:
                raise ValueError("Lean execution runtime changed during run")
        report["elapsed_wall_seconds"] = time.monotonic()-started
        report["measured_cpu_seconds"] = sum(r["process"]["resources"]["cpu_seconds"] for r in report["compilation"]+report["checks"])
        report["measured_cpu_seconds"] += sum(report[k]["resources"]["cpu_seconds"] for k in ("version_probe", "axiom_audit") if k in report)
        report["measured_cpu_seconds"] += sum(r["process"]["resources"]["cpu_seconds"] for r in report.get("negative_controls", []))
        report["limits"] = dict(build_cpu_hard_reservation_seconds=(phases["version"][0]+1)+(len(MODULES)+1)*(phases["build"][0]+1),
            per_check_cpu_hard_reservation_seconds=phases["check"][0]+1, rss_bytes=settings["rss_bytes"],
            negative_controls_cpu_hard_reservation_seconds=2*(phases["negative"][0]+1),
            phase_limits=phases, max_workers=1, controller_wall_seconds=controller_wall)
        save_new(output / "report.json", json.dumps(report, sort_keys=True, indent=2).encode()+b"\n")
    return dict(status=report["status"], stages=len(report["compilation"]),
        checks=[dict(case=r["case"], independent_lean_checked=r["independent_lean_checked"]) for r in report["checks"]],
        elapsed_wall_seconds=report["elapsed_wall_seconds"], stage=str(stage))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--lean", type=Path, help="explicit executable, never an ambient PATH lookup")
    parser.add_argument("--lean-repo", type=Path, help="exact pinned nine-module checker source tree")
    parser.add_argument("--resource-profile", choices=("local", "wmi-ap090-v2"), default="local")
    parser.add_argument("observations", nargs="+", type=Path)
    args = parser.parse_args()
    print(json.dumps(execute(args.output, [p.resolve() for p in args.observations],
        lean=args.lean, lean_repo=args.lean_repo, resource_profile=args.resource_profile), sort_keys=True))
