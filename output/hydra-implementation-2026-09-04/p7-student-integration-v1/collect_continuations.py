"""Copy the finite P7 evidence closure; no SSH, scheduler, proof, or model work.

Run only after the existing teacher collector reports successful terminal
metadata. This is transport bookkeeping, NOT native or training admission.
Existing distillation code remains the sole admission implementation.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat

SELECTION = "output/p7-prototype/selection-32-v1.json"
SELECTION_SHA = "26c09c2b28f54073f3964c4772113f7496eceb03107b356b892c619c9cc835d7"
SOURCE_SHA = "f3bad0a87debd9f661ba5a239814e52ba50ba96d7fdfff0adeeca8cf1f25b3b1"
TOP = ("request.json", "completion.json", "model-admission.json", "positive-continuations.json")
MAX_FILE = 2 * 1024**2
MAX_TOTAL = 256 * 1024**2
STAT_KEYS = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def strict(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON field.")
            result[key] = value
        return result
    def invalid(value):
        raise ValueError("Nonfinite JSON field: " + value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)


def relative(name):
    require(type(name) is str and "\\" not in name, "Expected a canonical relative path.")
    path = PurePosixPath(name)
    require(not path.is_absolute() and name == path.as_posix()
            and path.parts and not any(p in (".", "..") for p in path.parts),
            "Evidence path must not escape or normalize to another file.")
    return path


def ordinary(path, maximum=MAX_FILE, expected=None):
    path = Path(path).absolute()
    require(path.resolve(strict=True) == path, "Symlinks are not evidence inputs.")
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode) and before.st_size <= maximum,
            "Input is not a bounded ordinary file.")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        opened = os.fstat(stream.fileno())
        raw = stream.read(maximum + 1)
        closed = os.fstat(stream.fileno())
    after = path.lstat()
    require(len(raw) == before.st_size <= maximum and all(
        getattr(before, key) == getattr(opened, key) == getattr(closed, key) == getattr(after, key)
        for key in STAT_KEYS), "Evidence changed during the bounded read.")
    if expected is not None:
        require(type(expected) is str and re.fullmatch(r"[0-9a-f]{64}", expected)
                and digest(raw) == expected, "Evidence SHA differs.")
    return raw


def closure(positive, states):
    """The existing bridge consumes exactly five records per nominated state."""
    records = positive.get("records")
    require(positive.get("schema") == "hydra-teacher-positive-continuations-v1"
            and positive.get("training_performed") is False
            and type(records) is list and 0 <= len(records) <= 32
            and type(positive.get("positive_count")) is int
            and positive["positive_count"] == len(records), "Invalid positive index.")
    require(type(states) is list and len(states) == 32, "Missing fixed cohort.")
    names, seen = {}, set()
    for row in records:
        index = row.get("index")
        require(type(index) is int and 0 <= index < 32 and index not in seen,
                "Repeated or out-of-range positive index.")
        seen.add(index)
        state = states[index]
        require(row.get("state_id") == state["id"] and row.get("split") == "train"
                and row.get("selection_sha256") == SELECTION_SHA
                and row.get("outcome") == "proved"
                and row.get("positive_distillation_eligible") is True,
                "Positive is not a nomination from the exact training cohort.")
        directory = f"{index:03d}-" + state["id"][:16]
        for field, pin in (("successful_native_record", "successful_native_sha256"),
                           ("native_execution_record", "native_execution_sha256"),
                           ("teacher_proposal_record", "teacher_proposal_sha256")):
            name = relative(row[field]).as_posix()
            require(name.startswith(directory + "/") and name not in names
                    and re.fullmatch(r"[0-9a-f]{64}", row[pin]),
                    "A nomination points at another state or duplicates a record.")
            names[name] = row[pin]
        for suffix in ("prefix/result.json", "prefix/execution.json"):
            name = directory + "/" + suffix
            require(name not in names, "A successful record aliases its prefix.")
            names[name] = None
    require(len(names) == 5 * len(records), "Unexpected evidence closure size.")
    return names


def collect(args):
    root, job = args.source_root.absolute(), args.teacher_job.absolute()
    require(root.resolve(strict=True) == root and job.resolve(strict=True) == job,
            "Source root/job must be existing ordinary directory paths.")
    selection_raw = ordinary(root / SELECTION, expected=SELECTION_SHA)
    selection = strict(selection_raw)
    observation_raw = ordinary(args.observation, 8 * 1024**2, args.observation_sha256)
    summary_raw = ordinary(args.summary, MAX_FILE, args.summary_sha256)
    observation, summary = strict(observation_raw), strict(summary_raw)
    require(summary.get("teacher_campaign_metadata_complete") is True
            and summary.get("slurm_state") == "COMPLETED" and summary.get("slurm_exit_code") == "0:0"
            and summary.get("distillation_admitted") is False and summary.get("errors") == []
            and observation.get("job_id") == summary.get("job_id")
            and observation.get("read_only") is True
            and observation.get("remote_result_directory") == str(job / "result"),
            "Use the existing collector's complete exact-job terminal receipt.")
    copies = {"collector/observation.json": observation_raw, "collector/summary.json": summary_raw}
    for name in ["result/" + name for name in TOP] + ["actual-process-exit.txt"]:
        pin = observation["files"][name]
        require(pin.get("complete_file") is True, "A metadata tail is not a complete input.")
        raw = ordinary(job / name, 32 if name == "actual-process-exit.txt" else MAX_FILE, pin["sha256"])
        require(len(raw) == pin["bytes"], "Collected metadata size differs.")
        copies[name] = raw
    require(copies["actual-process-exit.txt"].strip() == b"0", "Teacher process did not exit zero.")
    request, completion, positive = (strict(copies["result/" + name]) for name in
                                      ("request.json", "completion.json", "positive-continuations.json"))
    require(request.get("source_pins_sha256") == SOURCE_SHA
            and digest(canonical(request["source_pins_before"])) == SOURCE_SHA
            and request.get("selection_sha256") == SELECTION_SHA
            and request.get("reservation", {}).get("job_id") == summary["job_id"]
            and request.get("selected_ids") == [s["id"] for s in selection["states"]]
            and completion.get("completed") is True and completion.get("error") is None
            and completion.get("states_completed") == completion.get("selected_states") == 32
            and completion.get("sources_unchanged") is True
            and completion.get("source_pins_after") == request["source_pins_before"],
            "Teacher request/completion differs from the sealed cohort/source.")
    names = closure(positive, selection["states"])
    count = positive["positive_count"]
    require(count == summary.get("positive_continuations_reported") == completion.get("positive_continuations"),
            "Positive count differs across actual records.")
    total = sum(map(len, copies.values()))
    for name, expected in sorted(names.items()):
        raw = ordinary(job / "result" / name, expected=expected)
        total += len(raw)
        require(total <= MAX_TOTAL, "Teacher evidence closure exceeds 256 MiB.")
        copies["result/" + name] = raw
    require(len(copies) <= 167 and total <= MAX_TOTAL, "Evidence closure bound exceeded.")
    destination = root / relative(args.output_relative)
    require(relative(args.output_relative).parts[0] == "output"
            and destination.resolve() == destination and not destination.exists(),
            "Use a new ordinary project-output directory; partial copies are never reused.")
    destination.mkdir(parents=True, exist_ok=False)
    pins = {}
    for name, raw in sorted(copies.items()):
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
        require(digest(ordinary(target, max(MAX_FILE, len(raw)))) == digest(raw), "Copied bytes differ.")
        pins[name] = {"bytes": len(raw), "sha256": digest(raw)}
    record = {"schema": "hydra-p7-continuation-copy-v1", "job_id": summary["job_id"],
        "status": "copied_not_admitted" if count else "copied_zero_yield_training_blocked",
        "positive_continuations_reported": count, "selection_sha256": SELECTION_SHA,
        "source_pins_sha256": SOURCE_SHA, "source_result_directory": str(job / "result"),
        "destination": args.output_relative, "files": pins, "bytes": total,
        "native_admission_performed": False, "training_allowed": False,
        "ssh_calls": 0, "model_calls": 0, "solver_calls": 0, "automatic_retry": False}
    with (destination / "copy-manifest.json").open("xb") as stream:
        stream.write(canonical(record) + b"\n")
    print(json.dumps({k: v for k, v in record.items() if k != "files"}, sort_keys=True))
    return 0 if count else 2


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source-root", "teacher-job", "observation", "summary"):
        parser.add_argument("--" + name, type=Path, required=True)
    for name in ("observation-sha256", "summary-sha256", "output-relative"):
        parser.add_argument("--" + name, required=True)
    return collect(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
