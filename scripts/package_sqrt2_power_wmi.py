#!/usr/bin/env python3
"""Deterministic, allowlisted AP090 snapshot; no proof execution or submission."""
import argparse
from hashlib import sha256
import io
import json
from pathlib import Path, PurePosixPath
import stat
import tarfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "sqrt2-power-wmi-snapshot-v1"
MANIFEST = "snapshot-manifest.json"
SOURCE_SNAPSHOT = "research/arithmetic-library/sqrt2-power/observations/fixed-half-log-root-source-snapshot-v1.json"
SOURCE_SNAPSHOT_SHA256 = "580a983caa7d2d9a1233a82dfa533ceabb2e6e7613fbbe3afefbebb35bdbf374"
PRODUCER_SHA256 = "d0677792dfa5a394ec6f2beea788290e5b85d00c7dd487405607da1c1d5b1cde"
MAX_FILE = 32 * 1024**2
MAX_TOTAL = 128 * 1024**2
MODULES = ("Syntax", "Substitution", "Derivation", "Semantics", "Checker", "Soundness",
           "Codec", "ProofBundle", "VerifyBundle")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode() + b"\n"


def safe_name(name):
    path = PurePosixPath(name)
    if (not isinstance(name, str) or not name or path.is_absolute()
            or ".." in path.parts or str(path) != name
            or path.parts[0] not in {"source", "lean"}):
        raise ValueError("unsafe snapshot member")
    return name


def payload(path):
    if path.is_symlink() or not stat.S_ISREG(path.stat().st_mode):
        raise ValueError("snapshot input is not a regular non-symlink file")
    with path.open("rb") as stream:
        raw = stream.read(MAX_FILE + 1)
    if len(raw) > MAX_FILE:
        raise ValueError("snapshot member too large")
    return raw


def digest(raw):
    return dict(bytes=len(raw), sha256=sha256(raw).hexdigest())


def runtime_library_paths(root):
    """Ship the complete small Python package, including transitive imports.

    Historical proof-input pins are not a Python import-closure manifest.
    Importing the full theorem catalogue remains forbidden at execution time.
    """
    return {str(path.relative_to(root))
        for path in (root / "peano-lab/py/peano_lab").rglob("*.py")}


def selected_files(root=ROOT, lean_root=None, *, with_ap090_ha=False, regression_wheels=None, case="AP090", with_ap094_evidence=False):
    root = root.resolve()
    lean_root = root.parent / "peano-lab-lean" if lean_root is None else lean_root.resolve()
    raw = payload(root / SOURCE_SNAPSHOT)
    if sha256(raw).hexdigest() != SOURCE_SNAPSHOT_SHA256:
        raise ValueError("AP090 inherited source manifest changed")
    inherited = json.loads(raw)["source_pins"]
    paths = set(inherited) | {SOURCE_SNAPSHOT,
        "scripts/assets/Sqrt2PowerLeanAudit.lean",
        "slurm/peano_wmi_sqrt2_pilot.sbatch",
        "scripts/submit_sqrt2_power_wmi.sh",
        "research/arithmetic-library/sqrt2-power/observations/shared-wave-rf001-v1/generation-process.json.gz",
        "research/arithmetic-library/sqrt2-power/observations/fixed-half-log-root-native-constructor-audit-v1.json"}
    # Campaign modules include dynamic imports in the exact frozen driver.
    # No environment, credentials, .git, site output tree or bytecode is copied.
    paths.update(str(p.relative_to(root)) for p in (root / "scripts").glob("*sqrt2*.py"))
    paths.update(runtime_library_paths(root))
    if case in {"AP091", "AP092", "AP093"}:
        from sqrt2_power_fixed_half_log_root_witness import fixed_half_log_root_witness_source_pins
        paths.update(fixed_half_log_root_witness_source_pins())
        paths.update(("slurm/peano_wmi_sqrt2_campaign.sbatch","scripts/submit_sqrt2_power_wmi_campaign.sh"))
        paths.add("research/arithmetic-library/sqrt2-power/observations/shared-wave-rf001-v1/generation-process.json.gz")
        if case in {"AP092", "AP093"}:
            from sqrt2_power_fixed_half_log_fine_root import fixed_half_log_fine_root_source_pins
            paths.update(fixed_half_log_fine_root_source_pins())
            paths.update(("slurm/peano_wmi_sqrt2_ap092.sbatch","scripts/submit_sqrt2_power_wmi_ap092.sh"))
            paths.add("research/arithmetic-library/sqrt2-power/observations/fixed-half-log-fine-root-solvers-v1.json")
            for leaf in ('shared-wave-fixed-half-log-root-witness-v1','shared-wave-fixed-half-log-root-witness-lean-wmi-v1'):
                folder=root/'research/arithmetic-library/sqrt2-power/observations'/leaf
                paths.update(str(p.relative_to(root)) for p in folder.rglob('*') if p.is_file())
        if case == "AP093":
            from sqrt2_power_log_root_half_argument import log_root_half_argument_source_pins
            paths.update(log_root_half_argument_source_pins())
            paths.update(("slurm/peano_wmi_sqrt2_ap093.sbatch","scripts/submit_sqrt2_power_wmi_ap093.sh"))
            paths.add("research/arithmetic-library/sqrt2-power/observations/log-root-half-argument-solvers-v1.json")
            for leaf in ('shared-wave-fixed-half-log-fine-root-v1','shared-wave-fixed-half-log-fine-root-lean-wmi-v1'):
                folder=root/'research/arithmetic-library/sqrt2-power/observations'/leaf
                paths.update(str(p.relative_to(root)) for p in folder.rglob('*') if p.is_file())
    elif case in {"AP094", "AP095"}:
        from sqrt2_power_exp_log_root_half_transport import exp_log_root_half_transport_source_pins
        from sqrt2_power_fixed_half_log_fine_root import fixed_half_log_fine_root_source_pins
        paths.update(exp_log_root_half_transport_source_pins())
        # The AP093 regression rebinds the historical AP092 case exactly.
        paths.update(fixed_half_log_fine_root_source_pins())
        paths.update(("slurm/peano_wmi_sqrt2_ap094.sbatch","scripts/submit_sqrt2_power_wmi_ap094.sh"))
        for observation in ('exp-log-root-half-transport-solvers-v1.json','log-root-half-argument-solvers-v1.json'):
            paths.add('research/arithmetic-library/sqrt2-power/observations/'+observation)
        for leaf in ('shared-wave-log-root-half-argument-v1','shared-wave-log-root-half-argument-lean-wmi-v1',
                'shared-wave-fixed-half-log-fine-root-v1'):
            folder=root/'research/arithmetic-library/sqrt2-power/observations'/leaf
            paths.update(str(p.relative_to(root)) for p in folder.rglob('*') if p.is_file())
        if case == "AP095":
            from sqrt2_power_requested_half_transport import requested_half_transport_source_pins
            paths.update(requested_half_transport_source_pins())
            paths.update(('slurm/peano_wmi_sqrt2_ap095.sbatch','scripts/submit_sqrt2_power_wmi_ap095.sh',
                'research/arithmetic-library/sqrt2-power/observations/exp-log-root-half-transport-wmi-progress-audit-v1.json'))
            for leaf in ('shared-wave-exp-log-root-half-transport-v1','shared-wave-exp-log-root-half-transport-lean-wmi-v1'):
                folder=root/'research/arithmetic-library/sqrt2-power/observations'/leaf
                paths.update(str(p.relative_to(root)) for p in folder.rglob('*') if p.is_file())
    elif case != "AP090":
        raise ValueError("unconfigured campaign snapshot")
    if with_ap094_evidence:
        if case != "AP094":raise ValueError("AP094 evidence is only for its exact regression follow-up")
        from verify_sqrt2_power_wmi_ap094_tests import HA,LEAN,HA_SHA256,LEAN_SHA256,ORIGINAL_MANIFEST,ORIGINAL_MANIFEST_SHA256
        for folder,expected in ((HA,HA_SHA256),(LEAN,LEAN_SHA256)):
            if digest(payload(root/folder/'report.json'))['sha256']!=expected:raise ValueError('completed AP094 receipt changed')
            paths.update(str(p.relative_to(root)) for p in (root/folder).rglob('*') if p.is_file())
        if digest(payload(root/ORIGINAL_MANIFEST))['sha256']!=ORIGINAL_MANIFEST_SHA256:
            raise ValueError('original AP094 snapshot manifest changed')
        paths.update((ORIGINAL_MANIFEST,'slurm/peano_wmi_sqrt2_ap094_tests.sbatch','scripts/submit_sqrt2_power_wmi_ap094_tests.sh'))
    if with_ap090_ha:
        from verify_sqrt2_power_wmi_lean import HA_FOLDER, HA_REPORT_SHA256
        if digest(payload(root/HA_FOLDER/"report.json"))["sha256"] != HA_REPORT_SHA256:
            raise ValueError("verification-only snapshot requires the completed AP090 HA report")
        paths.update(str(p.relative_to(root)) for p in (root/HA_FOLDER).rglob("*") if p.is_file())
        paths.add("scripts/submit_sqrt2_power_wmi_lean.sh")
    if regression_wheels is not None:
        if not with_ap090_ha:
            raise ValueError("regressions require the completed HA evidence")
        from verify_sqrt2_power_wmi_regressions import EXTRA_FILES, WHEELS
        paths.update(EXTRA_FILES)
        folder=root/"research/arithmetic-library/sqrt2-power/observations/shared-wave-half-log-root-uniform-v3"
        paths.update(str(p.relative_to(root)) for p in folder.rglob("*") if p.is_file())
    result = {}
    for name in sorted(paths):
        member = safe_name("source/" + name)
        path = root / name
        if path.resolve().is_relative_to(root) is False:
            raise ValueError("snapshot source escapes repository")
        raw = payload(path)
        if name in inherited and digest(raw) != inherited[name]:
            raise ValueError("inherited AP090 input changed: " + name)
        result[member] = raw
    if digest(result["source/scripts/sqrt2_power_fixed_half_log_root.py"])["sha256"] != PRODUCER_SHA256:
        raise ValueError("AP090 proof producer changed")
    for name in MODULES:
        result["lean/PeanoLab/" + name + ".lean"] = payload(lean_root / "PeanoLab" / (name + ".lean"))
    if regression_wheels is not None:
        for name, expected in WHEELS.items():
            raw=payload(Path(regression_wheels)/name)
            if digest(raw)["sha256"]!=expected:
                raise ValueError("changed pinned test dependency: "+name)
            result["source/wmi-test-wheels/"+name]=raw
    return result


def build_archive(output, *, root=ROOT, lean_root=None, with_ap090_ha=False, regression_wheels=None, case="AP090", with_ap094_evidence=False):
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError("new snapshot destination required")
    entries = dict(selected_files(root, lean_root, with_ap090_ha=with_ap090_ha, regression_wheels=regression_wheels, case=case, with_ap094_evidence=with_ap094_evidence))
    if sum(map(len, entries.values())) > MAX_TOTAL:
        raise ValueError("snapshot exceeds transport bound")
    manifest = dict(schema=SCHEMA, case=case, authority="transport_not_proof",
        files={name: digest(raw) for name, raw in sorted(entries.items())})
    entries[MANIFEST] = canonical(manifest)
    with tarfile.open(output, "x", format=tarfile.USTAR_FORMAT) as archive:
        for name, raw in sorted(entries.items()):
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(raw), 0o444, 0
            archive.addfile(info, io.BytesIO(raw))
    h = sha256()
    with output.open("rb") as stream:
        while block := stream.read(1024**2):
            h.update(block)
    return dict(archive_sha256=h.hexdigest(), archive_bytes=output.stat().st_size,
        manifest_sha256=sha256(entries[MANIFEST]).hexdigest(), files=len(manifest["files"]),
        input_bytes=sum(pin["bytes"] for pin in manifest["files"].values()), case=case)


def verify_snapshot(stage):
    stage = Path(stage).resolve()
    raw = payload(stage / MANIFEST)
    manifest = json.loads(raw)
    if manifest.get("schema") != SCHEMA or manifest.get("case") not in {"AP090", "AP091", "AP092", "AP093", "AP094", "AP095"}:
        raise ValueError("wrong snapshot manifest")
    total = 0
    for name, pin in manifest["files"].items():
        safe_name(name)
        path = stage / name
        if not path.resolve().is_relative_to(stage) or digest(payload(path)) != pin:
            raise ValueError("snapshot input changed: " + name)
        total += pin["bytes"]
    if not manifest["files"] or total > MAX_TOTAL:
        raise ValueError("snapshot boundary is empty or oversized")
    return dict(files=len(manifest["files"]), input_bytes=total,
        manifest_sha256=sha256(raw).hexdigest())


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--output", type=Path)
    group.add_argument("--verify", type=Path)
    parser.add_argument("--with-ap090-ha", action="store_true", help="include completed HA evidence for verification only")
    parser.add_argument("--regression-wheels", type=Path, help="exact pinned offline Python test dependencies")
    parser.add_argument("--case", choices=("AP090","AP091","AP092","AP093","AP094","AP095"), default="AP090")
    parser.add_argument("--with-ap094-evidence", action="store_true", help="exact completed AP094 HA/Lean bytes for regression-only follow-up")
    args = parser.parse_args()
    print(json.dumps(verify_snapshot(args.verify) if args.verify else build_archive(args.output,
        with_ap090_ha=args.with_ap090_ha, regression_wheels=args.regression_wheels, case=args.case, with_ap094_evidence=args.with_ap094_evidence), sort_keys=True))
