"""Archive bounded observations losslessly; this cannot admit a theorem.

Gzip is storage only. SHA-256 always binds the original uncompressed bytes.
Source snapshots preserve the exact producer/consumer version of each run.
"""
from hashlib import sha256
import argparse
import gzip
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(raw):
    return sha256(raw).hexdigest()


def write_new(path, raw):
    if path.exists() or path.is_symlink():
        raise ValueError("refusing to overwrite observation: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def archive(source, output):
    if output.exists() or output.is_symlink() or source.is_symlink():
        raise ValueError("archive must be new; source must not be a symlink")
    report = json.loads((source / "report.json").read_bytes())
    if report.get("schema") != "sqrt2-power-bounded-pilot-v1":
        raise ValueError("not a supported observation")
    material = {}
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise ValueError("symlink in observation")
        if path.is_file():
            material["run/" + str(path.relative_to(source))] = path.read_bytes()
    for name, pin in report["source_pins"].items():
        path = ROOT / name
        if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink():
            raise ValueError("invalid pinned source path")
        raw = path.read_bytes()
        if {"bytes": len(raw), "sha256": digest(raw)} != pin:
            raise ValueError("source changed before archival: " + name)
        material["sources/" + name] = raw
    manifest = dict(schema="sqrt2-power-observation-archive-v1",
                    authority="historical_local_observation_not_admission",
                    report_sha256=digest((source / "report.json").read_bytes()), files={})
    for name, raw in sorted(material.items()):
        compressed = gzip.compress(raw, compresslevel=9, mtime=0)
        stored = name + ".gz"
        write_new(output / stored, compressed)
        manifest["files"][name] = dict(path=stored, bytes=len(raw), sha256=digest(raw),
                                      gzip_bytes=len(compressed), gzip_sha256=digest(compressed))
    write_new(output / "manifest.json", (json.dumps(manifest, sort_keys=True, indent=2) + "\n").encode())
    return dict(files=len(material), raw_bytes=sum(len(v) for v in material.values()),
                archive_bytes=sum(r["gzip_bytes"] for r in manifest["files"].values()),
                output=str(output), IR_parents_closed=0)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(archive(args.source, args.output), sort_keys=True))
