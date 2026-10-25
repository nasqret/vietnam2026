"""Freeze only explicit Hydra sources and admitted project-owned data; no launch."""
from pathlib import Path
import gzip
import hashlib
import io
import json
import tarfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "p6-source-bundle-03"
DATA = Path("output/hydra-implementation-2026-09-04/decisions-v2-01")
DATA_SHA = "e575970df58d046735f492acaf22e1cdea44445608a201c62d0644590b95ea77"
RUNNER_SHA = "0c81000132949df3ab3314272fb39826c942332bc723ce4bec3ed76ad4b6d489"


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    data_raw = (ROOT / DATA / "manifest.json").read_bytes()
    assert digest(data_raw) == DATA_SHA
    data = json.loads(data_raw)
    paths = {DATA / "manifest.json", Path("output/p6-prototype/remote_provider_smoke.py"),
             Path("HYDRA_EXPERIMENT_AUTHORITY.md")}
    app = ROOT / "hydra-playground"
    paths.update(p.relative_to(ROOT) for p in app.glob("*.py") if not p.name.startswith("test_"))
    paths.update(p.relative_to(ROOT) for p in (app / "training-v5").rglob("*")
                 if p.is_file() and p.suffix in {".py", ".json", ".toml", ".lock"})
    inherited = json.loads((app / "training-v5/BASELINE.json").read_bytes())
    paths.update(Path("hydra-playground/training-v5") / row["working"] for row in inherited["files"])
    for directory in (app / "native-v7", app / "experimental-models", app / "lemmas", app / "branch-rankers"):
        paths.update(p.relative_to(ROOT) for p in directory.rglob("*")
                     if p.is_file() and p.suffix in {".py", ".json"})
    # Admission can select this preserved parser before the experimental engine
    # is activated; exact original files, not a module-path integrity exception.
    frozen = ROOT / "_deploy/hydra-retention-evaluation-recovery-execution-20260831/peano-lab/py/peano_lab"
    paths.update(p.relative_to(ROOT) for p in frozen.rglob("*.py"))
    paths.add(Path("hydra-playground/evaluation-holdout.json"))
    for pin in data["inputs"]:
        path = Path(pin["path"])
        raw = (ROOT / path).read_bytes()
        assert len(raw) == pin["bytes"] and digest(raw) == pin["sha256"], str(path)
        paths.add(path)
    for name, pin in data["files"].items():
        path = DATA / name
        raw = (ROOT / path).read_bytes()
        assert len(raw) == pin["bytes"] and digest(raw) == pin["sha256"], str(path)
        paths.add(path)
    assert digest((ROOT / "output/p6-prototype/remote_provider_smoke.py").read_bytes()) == RUNNER_SHA
    OUT.mkdir(exist_ok=False)
    records = {}
    archive = OUT / "source-data.tar.gz"
    with archive.open("xb") as destination, gzip.GzipFile(fileobj=destination, mode="wb", mtime=0) as compressed:
        with tarfile.open(fileobj=compressed, mode="w|") as tar:
            for relative in sorted(paths):
                path = ROOT / relative
                assert path.is_file() and not path.is_symlink() and ".." not in relative.parts
                raw = path.read_bytes()
                records[relative.as_posix()] = {"bytes": len(raw), "sha256": digest(raw)}
                info = tarfile.TarInfo(relative.as_posix())
                info.size = len(raw)
                info.mode = 0o600
                info.mtime = 0
                tar.addfile(info, io.BytesIO(raw))
    record = {"schema": "hydra-exact-source-data-bundle-v1", "files": records,
              "file_count": len(records), "expanded_bytes": sum(p["bytes"] for p in records.values()),
              "archive_bytes": archive.stat().st_size, "archive_sha256": digest(archive.read_bytes()),
              "dataset_manifest_sha256": DATA_SHA, "runner_sha256": RUNNER_SHA,
              "contains_model_weights": False, "contains_secrets": False,
              "automatic_launch": False, "gpu_allocations": 0}
    (OUT / "manifest.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: v for k, v in record.items() if k != "files"}))


if __name__ == "__main__":
    main()
