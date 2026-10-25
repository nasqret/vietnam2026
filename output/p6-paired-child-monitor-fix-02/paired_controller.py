"""Output-only prepared controller: one fresh, bounded child per reserved case.

There is no submit/download/train/retry command. Execution requires a new exact
root-bound Slurm reservation and a completed, hash-bound study specification.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import importlib.util
import os
from pathlib import Path
import platform
import re
import shutil
import signal
import subprocess
import sys
import time

from paired_common import (ACCOUNT, PARTITION, FEATURES, HOLDOUT_SHA, MODEL_LIMITS,
    NATIVE_WORK, RESOURCE_LIMITS, SCHEDULER_SHA, SLICE_IDS, WALL_PROFILES, canonical,
    case_payload, holdout_cases, job_seconds, ordinary, pin, require, save,
    source_pins, strict_json, study_spec, training_exposure, valid_sha)

HERE = Path(__file__).resolve().parent
SLICE_PATH = HERE / "paired-slice-reservation.json"
SLICE_SHA = "01836cabc3ebf7bc69ed648816c8e36abe853a0a81baeafc7d956f2e3f3ca3d8"
RESERVATION_SCHEMA = "hydra-p6-p10-paired-reservation-v1"
# Linux include/linux/sched.h: exit has begun; this is not proof of exit.
PF_EXITING = 0x00000004


def scheduler_helpers():
    path = HERE / "remote_provider_smoke.py"
    require(pin(path)["sha256"] == SCHEDULER_SHA, "The reviewed scheduler helper changed.")
    spec = importlib.util.spec_from_file_location("hydra_paired_scheduler", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reservation_spec(value, study, study_sha):
    fields = {"schema", "job_id", "job_name", "nonce", "uid", "account", "partition",
              "gpus", "nodes", "cpus", "memory_gib", "seconds", "arm", "study_sha256",
              "source_pins_sha256", "controller_sha256", "case_worker_sha256", "common_sha256",
              "holdout_sha256", "slice_sha256"}
    require(type(value) is dict and set(value) == fields and value["schema"] == RESERVATION_SCHEMA,
            "A new exact paired-evaluation reservation is required; smoke/training claims cannot be reused.")
    require(type(value["job_id"]) is str and re.fullmatch(r"\d{1,20}", value["job_id"])
            and type(value["job_name"]) is str and re.fullmatch(r"[A-Za-z0-9_.-]{1,100}", value["job_name"])
            and type(value["nonce"]) is str and re.fullmatch(r"[0-9a-f]{32}", value["nonce"]),
            "Malformed finite reservation identity.")
    require(type(value["uid"]) is int and value["uid"] == os.getuid()
            and value["account"] == ACCOUNT and value["partition"] == PARTITION,
            "Wrong allocation owner/account/partition.")
    for name, expected in (("gpus", 1), ("nodes", 1), ("cpus", 8), ("memory_gib", 64),
                           ("seconds", job_seconds(study["scope"], study["wall_profile"]))):
        require(type(value[name]) is int and value[name] == expected, "Allocation differs from the exact selected limits.")
    require(value["seconds"] % 60 == 0, "Allocation must bind exact whole scheduler minutes.")
    require(value["arm"] in study["arms"] and value["study_sha256"] == study_sha
            and value["source_pins_sha256"] == study["source_pins_sha256"]
            and value["holdout_sha256"] == HOLDOUT_SHA and value["slice_sha256"] == SLICE_SHA,
            "Reservation does not bind this exact arm/study/source/input.")
    require(all(valid_sha(value[name]) for name in fields if name.endswith("_sha256")),
            "Complete SHA-256 bindings are required.")
    return value


def claim_reservation(path, expected_sha, reservation, output, first):
    require(pin(path, 65536)["sha256"] == expected_sha
            and first["job_id"] == reservation["job_id"], "Reservation changed before consumption.")
    claim = Path(path).with_name(Path(path).name + ".claimed")
    save(claim, {"schema": "hydra-paired-reservation-consumption-v1",
        "reservation_sha256": expected_sha, "study_sha256": reservation["study_sha256"],
        "job_id": reservation["job_id"], "nonce": reservation["nonce"], "arm": reservation["arm"],
        "output": str(output), "pid": os.getpid(), "first_live_allocation": first,
        "automatic_retry": False, "resume": False})
    return claim


def selected_cases(app, study):
    require(pin(SLICE_PATH, 65536)["sha256"] == SLICE_SHA, "Prospective paired slice changed.")
    rows = holdout_cases(Path(app) / "evaluation-holdout.json")
    if study["scope"] == "paired5":
        by_id = {row["id"]: row for row in rows}
        return [by_id[name] for name in SLICE_IDS]
    return rows


def parse_proc_stat(raw, pid):
    require(type(raw) is str and len(raw) <= 8192 and raw.startswith(str(pid) + " ("),
            "Malformed owned-process stat record.")
    tail = raw[raw.rfind(")") + 2:].split()
    require(len(tail) >= 22 and tail[0] in "RSDZTtXxKWPI", "Short/unknown owned-process stat.")
    require(tail[6].isdigit() and len(tail[6]) <= 10 and int(tail[6]) <= 0xffffffff,
            "Malformed owned-process flags.")
    return {"state": tail[0], "ppid": int(tail[1]), "pgid": int(tail[2]),
            "sid": int(tail[3]), "flags": int(tail[6]), "start_ticks": int(tail[19])}


def parse_proc_status(raw, state):
    require(type(raw) is str and len(raw.encode()) <= 65536, "Oversized process accounting.")
    uid = re.findall(r"^Uid:\s+(\d+)\s+", raw, re.MULTILINE)
    rss = re.findall(r"^VmRSS:\s+(\d+)\s+kB\s*$", raw, re.MULTILINE)
    require(len(uid) == 1 and (len(rss) == 1 or (not rss and state == "Z")),
            "Missing or ambiguous live RSS/ownership accounting.")
    return int(uid[0]), 0 if not rss else int(rss[0]) * 1024


def proc_read(path, maximum):
    with Path(path).open("rb") as stream:
        raw = stream.read(maximum + 1)
    require(len(raw) <= maximum, "Process accounting exceeded its bound.")
    return raw


def sample_scheduler_child(pid, leader, job_id, scontrol, pending=None):
    """One bounded read, never waitid/signals or an inner polling loop.

    Integer/None retain the ordinary sample/gone API. A dict is an explicitly
    pending RSS/command-line absence or its natural terminal confirmation. Only the outer
    supervisor may carry it between samples, within its shared cleanup budget.
    """
    child = Path("/proc") / str(pid)
    expected = [os.fsencode(scontrol), b"-o", b"show", b"job", job_id.encode(), b""]
    identity_fields = ("ppid", "pgid", "sid", "start_ticks")
    initial = None
    saw_zombie = False
    saw_exiting = pending is not None
    known_rss = 0 if pending is None else pending["known_rss_bytes"]
    rss_absence_observed = False if pending is None else pending["rss_absence_observed"]
    diagnostic = {"schema": "hydra-paired-child-accounting-v1", "pid": str(pid)[:20],
                  "phase": "before", "stats": {}, "records": []}

    def state_seen(state):
        nonlocal saw_zombie
        require(len(state) == 1 and state in "RSDZTtXxKWPI", "Malformed scheduler-query process state.")
        require(not saw_zombie or state == "Z", "Scheduler-query terminal state regressed.")
        saw_zombie = saw_zombie or state == "Z"

    def stat_snapshot(label):
        nonlocal saw_exiting
        diagnostic["phase"] = label + "_stat"
        value = parse_proc_stat(proc_read(child / "stat", 8192).decode(), pid)
        diagnostic["stats"][label] = {key: str(value[key])[:32]
                                      for key in ("state", "flags") + identity_fields}
        require(value["ppid"] == leader and value["pgid"] == value["sid"] == leader,
                "Unowned or escaped scheduler-query child.")
        require(initial is None or all(value[key] == initial[key] for key in identity_fields),
                "Scheduler-query child identity changed between accounting reads.")
        require(pending is None or (pending["pid"] == pid
                and all(value[key] == pending["identity"][key] for key in identity_fields)),
                "Pending scheduler-query identity changed or PID was reused.")
        exiting = bool(value["flags"] & PF_EXITING)
        require(not saw_exiting or exiting, "Scheduler-query exiting flag regressed.")
        saw_exiting = saw_exiting or exiting
        state_seen(value["state"])
        return value

    def records(label):
        observed = {"phase": label}
        diagnostic["records"].append(observed)
        values = {}
        for name, path, maximum in (("status", child / "status", 65536),
                                    ("cmdline", child / "cmdline", 65536),
                                    ("children", child / "task" / str(pid) / "children", 8192)):
            diagnostic["phase"] = label + "_" + name
            try:
                values[name] = proc_read(path, maximum)
            except FileNotFoundError:
                values[name] = None  # Requires a confirmed terminal identity below.
            observed[name + "_bytes"] = None if values[name] is None else len(values[name])
            if name == "status" and values[name] is not None:
                text = values[name].decode()
                state_fields = re.findall(r"^State:[^\r\n]*", text, re.MULTILINE)
                states = re.findall(r"^State:[ \t]+([RSDZTtXxKWPI])(?:[ \t][^\r\n]*)?$", text, re.MULTILINE)
                uid_fields = re.findall(r"^Uid:[^\r\n]*", text, re.MULTILINE)
                uids = re.findall(r"^Uid:[ \t]+(\d+)[ \t]+(\d+)[ \t]+(\d+)[ \t]+(\d+)[ \t]*$", text, re.MULTILINE)
                rss_fields = re.findall(r"^VmRSS:[^\r\n]*", text, re.MULTILINE)
                rss = re.findall(r"^VmRSS:[ \t]+(\d+)[ \t]+kB[ \t]*$", text, re.MULTILINE)
                observed.update({"state_fields": len(state_fields), "valid_state_fields": len(states),
                    "state": states[0] if len(states) == 1 else None,
                    "uid_fields": len(uid_fields), "valid_uid_fields": len(uids),
                    "rss_fields": len(rss_fields), "valid_rss_fields": len(rss)})
                require(len(state_fields) == len(states) == 1,
                        "Missing or ambiguous scheduler-query status state.")
                require(len(uid_fields) == len(uids) == 1, "Malformed scheduler-query UID accounting.")
                require(len(rss_fields) == len(rss) and len(rss) <= 1,
                        "Malformed or ambiguous scheduler-query RSS accounting.")
                observed["uid_matches"] = all(int(value) == os.getuid() for value in uids[0])
                require(observed["uid_matches"], "Scheduler-query child uid changed.")
                state_seen(states[0])
                values["rss"] = None if not rss else int(rss[0]) * 1024
            elif name == "cmdline":
                observed["argv_matches"] = values[name] is not None and values[name].split(b"\0") == expected
                observed["argv_empty"] = values[name] == b""
                require(values[name] in (None, b"") or observed["argv_matches"],
                        "Case spawned an undeclared executable or arguments.")
            elif name == "children":
                require(values[name] is None or not values[name].strip(),
                        "Scheduler query created a further descendant.")
        return values, observed

    def observation(*, terminal=None):
        return {"pid": pid, "identity": (pending["identity"] if initial is None else
                {key: initial[key] for key in identity_fields}),
                "rss_bytes": None if terminal is None else known_rss,
                "known_rss_bytes": known_rss, "pending_exit": terminal is None,
                "rss_absence_observed": rss_absence_observed,
                "terminal": terminal, "diagnostic": diagnostic}

    def sample():
        nonlocal initial, known_rss, rss_absence_observed
        initial = stat_snapshot("before")
        first, first_observed = records("initial")
        require(not rss_absence_observed or first.get("rss") is None,
                "Pending scheduler-query resumed RSS without proving exit.")
        rss_absence_observed = rss_absence_observed or (
            first["status"] is not None and first.get("rss") is None)
        known_rss = max(known_rss, first.get("rss") or 0)
        after = stat_snapshot("after")
        if after["state"] == "Z":
            terminal, terminal_observed = records("terminal")
            final = stat_snapshot("terminal")
            require(final["state"] == "Z" and terminal["status"] is not None
                    and terminal_observed.get("state") == "Z",
                    "Scheduler-query terminal accounting is not coherent.")
            known_rss = max(known_rss, terminal.get("rss") or 0)
            return observation(terminal="zombie") if pending is not None else known_rss
        require(initial["state"] != "Z" and first["status"] is not None
                and first_observed.get("state") != "Z",
                "Missing or ambiguous live RSS/ownership accounting.")
        require(first["children"] is not None, "Live scheduler-query descendant accounting is unavailable.")
        if first["rss"] is None:
            require(after["flags"] & PF_EXITING, "Live scheduler-query lacks RSS without PF_EXITING.")
            return observation()
        # Status can retain a valid RSS snapshot before exit clears cmdline.
        # The later owned stat must prove PF_EXITING; completion still needs
        # the unchanged bounded natural-exit protocol. Never treat this as
        # ordinary live accounting or discard its observed memory.
        if first_observed["argv_empty"] and after["flags"] & PF_EXITING:
            return observation()
        require(pending is None and first_observed["argv_matches"],
                "Live scheduler-query command line is unavailable.")
        return first["rss"]

    try:
        try:
            return sample()
        except FileNotFoundError:
            # Never waitid a grandchild. Pending disappearance requires two
            # absent stat reads; sample_owned also rechecks all owned child lists.
            if pending is None:
                return None
            try:
                stat_snapshot("disappearance_check")
            except FileNotFoundError:
                diagnostic["phase"] = "disappeared"
                diagnostic["absent_stat_reads"] = 2
                return observation(terminal="disappeared")
            raise ValueError("Scheduler-query disappearance was not stable.")
    except (OSError, ValueError) as error:
        error.accounting_diagnostic = diagnostic
        error.child_accounting_violation = True
        raise


def sample_leader(process, initial_start=None):
    """Read one leader; only well-formed PF_EXITING RSS absence may be pending.

    A normal or pending sample uses three bounded reads. Pending is not valid
    live accounting or completed exit: the caller must resolve it naturally
    within the existing cleanup budget. Final acceptance needs two further
    terminal reads and non-reaping exit confirmation. No sleeps occur here.
    """
    leader = process.pid
    root = Path("/proc") / str(leader)
    identity_fields = ("ppid", "pgid", "sid", "start_ticks")
    initial = None
    saw_zombie = False
    saw_exiting = False
    diagnostic = {"schema": "hydra-paired-leader-accounting-v1", "pid": str(leader)[:20],
                  "phase": "before", "stats": {}, "records": [], "exit_observations": []}

    def record_state(state):
        nonlocal saw_zombie
        require(len(state) == 1 and state in "RSDZTtXxKWPI", "Malformed owned-leader process state.")
        require(not saw_zombie or state == "Z", "Owned-leader terminal state regressed.")
        saw_zombie = saw_zombie or state == "Z"

    def stat_snapshot(label):
        nonlocal saw_exiting
        diagnostic["phase"] = label + "_stat"
        value = parse_proc_stat(proc_read(root / "stat", 8192).decode(), leader)
        diagnostic["stats"][label] = {key: str(value[key])[:32]
                                      for key in ("state", "flags") + identity_fields}
        require(value["ppid"] == os.getpid() and value["pgid"] == value["sid"] == leader,
                "Case process left its owned session/group/parent.")
        require(initial_start is None or value["start_ticks"] == initial_start,
                "Owned process identity changed.")
        require(initial is None or all(value[key] == initial[key] for key in identity_fields),
                "Owned-leader identity changed between accounting reads.")
        exiting = bool(value["flags"] & PF_EXITING)
        require(not saw_exiting or exiting, "Owned-leader exiting flag regressed.")
        saw_exiting = saw_exiting or exiting
        record_state(value["state"])
        return value

    def status_snapshot(label):
        diagnostic["phase"] = label + "_status"
        raw = proc_read(root / "status", 65536)
        text = raw.decode()
        observed = {"phase": label, "status_bytes": len(raw)}
        diagnostic["records"].append(observed)
        state_fields = re.findall(r"^State:[^\r\n]*", text, re.MULTILINE)
        states = re.findall(r"^State:[ \t]+([RSDZTtXxKWPI])(?:[ \t][^\r\n]*)?$", text, re.MULTILINE)
        uid_fields = re.findall(r"^Uid:[^\r\n]*", text, re.MULTILINE)
        uids = re.findall(r"^Uid:[ \t]+(\d+)[ \t]+(\d+)[ \t]+(\d+)[ \t]+(\d+)[ \t]*$", text, re.MULTILINE)
        rss_fields = re.findall(r"^VmRSS:[^\r\n]*", text, re.MULTILINE)
        rss = re.findall(r"^VmRSS:[ \t]+(\d+)[ \t]+kB[ \t]*$", text, re.MULTILINE)
        observed.update({"state_fields": len(state_fields), "valid_state_fields": len(states),
                         "state": states[0] if len(states) == 1 else None,
                         "uid_fields": len(uid_fields), "valid_uid_fields": len(uids),
                         "rss_fields": len(rss_fields), "valid_rss_fields": len(rss)})
        require(len(state_fields) == len(states) == 1, "Missing or ambiguous owned-leader status state.")
        require(len(uid_fields) == len(uids) == 1, "Missing or ambiguous owned-leader UID accounting.")
        observed["uid_matches"] = all(int(value) == os.getuid() for value in uids[0])
        require(observed["uid_matches"], "Owned process uid changed.")
        require(len(rss_fields) == len(rss) and len(rss) <= 1,
                "Malformed or ambiguous owned-leader RSS accounting.")
        record_state(states[0])
        return None if not rss else int(rss[0]) * 1024

    def exit_snapshot():
        diagnostic["phase"] = "exit_confirmation"
        exited = peek_owned_exit(process)
        diagnostic["exit_observations"].append(exited)
        return exited

    try:
        require(process.returncode is None, "Owned leader was reaped before accounting.")
        initial = stat_snapshot("before")
        rss = status_snapshot("initial")
        after = stat_snapshot("after")
        if rss is not None:
            return {"info": after, "rss_bytes": rss, "exited": False, "pending_exit": False,
                    "diagnostic": diagnostic}
        require(after["flags"] & PF_EXITING, "Live leader lacks RSS without PF_EXITING.")
        if not exit_snapshot():
            return {"info": after, "rss_bytes": None, "exited": False, "pending_exit": True,
                    "diagnostic": diagnostic}
        terminal_rss = status_snapshot("terminal")
        final = stat_snapshot("terminal")
        exited = exit_snapshot()
        require(final["state"] == diagnostic["records"][-1]["state"] == "Z" and exited,
                "Missing live RSS or unproven owned-leader exit.")
        return {"info": final, "rss_bytes": max(rss or 0, terminal_rss or 0), "exited": True,
                "pending_exit": False, "diagnostic": diagnostic}
    except (OSError, ValueError) as error:
        error.accounting_diagnostic = diagnostic
        # Only explicit pending RSS absence may be deferred by the caller.
        # Wrong identity, malformed fields and inconsistent exit remain fatal.
        error.leader_accounting_violation = True
        raise


def owned_child_ids(leader):
    """The original bounded inventory, also used after a pending PID vanishes."""
    root = Path("/proc") / str(leader)
    tasks = list((root / "task").iterdir())
    require(1 <= len(tasks) <= 512 and all(path.name.isdigit() for path in tasks), "Unbounded process thread inventory.")
    children = set()
    for task in tasks:
        try:
            raw = proc_read(task / "children", 8192).decode().split()
        except FileNotFoundError:  # A thread can finish while the still-owned process runs.
            continue
        require(all(item.isdigit() for item in raw), "Malformed owned-child inventory.")
        children.update(map(int, raw))
    require(len(children) <= 1, "A case created more than its one scheduler-query descendant.")
    return children


def sample_owned(process, job_id, scontrol, initial_start=None, pending_child=None):
    """Account this unreaped leader and at most one bounded scheduler child."""
    leader = process.pid
    observed = sample_leader(process, initial_start)
    info, rss = observed["info"], observed["rss_bytes"]
    child_observation = None
    live_children = []
    known_rss = 0 if rss is None else rss
    try:
        require(pending_child is None or not observed["exited"],
                "Owned leader exited before pending child accounting resolved.")
        if observed["exited"]:
            return {"rss_bytes": rss, "start_ticks": info["start_ticks"], "descendants": [],
                    "leader_exit_confirmed": True, "leader_accounting_diagnostic": observed["diagnostic"]}
        children = owned_child_ids(leader)
        if pending_child is not None:
            pid = pending_child["pid"]
            child_observation = sample_scheduler_child(pid, leader, job_id, scontrol, pending_child)
            if child_observation["terminal"] == "disappeared":
                children = owned_child_ids(leader)
                require(pid not in children, "Disappeared scheduler PID remains in owned child inventory.")
            else:
                require(children == {pid}, "Pending scheduler child inventory changed or became ambiguous.")
                live_children.append(pid)
            known_rss += child_observation["known_rss_bytes"]
            children.discard(pid)
        for pid in children:
            child_rss = sample_scheduler_child(pid, leader, job_id, scontrol)
            if child_rss is None:
                continue
            if type(child_rss) is dict:
                require(child_observation is None, "Two scheduler terminal resolutions overlap in one sample.")
                child_observation = child_rss
                known_rss += child_rss["known_rss_bytes"]
            else:
                known_rss += child_rss
            live_children.append(pid)
        require(child_observation is None or not observed["pending_exit"],
                "Overlapping leader and child terminal resolution is not admitted.")
    except (OSError, ValueError) as error:
        if pending_child is not None or child_observation is not None:
            error.child_accounting_violation = True
            if not hasattr(error, "accounting_diagnostic"):
                error.accounting_diagnostic = (child_observation or pending_child)["diagnostic"]
        raise
    child_pending = child_observation is not None and child_observation["pending_exit"]
    result = {"rss_bytes": None if rss is None else known_rss,
              "start_ticks": info["start_ticks"], "descendants": live_children,
              "leader_accounting_diagnostic": observed["diagnostic"]}
    if child_observation is not None:
        result["child_exit_observation"] = child_observation
    if child_pending:
        result.update({"rss_bytes": None, "known_rss_bytes": known_rss})
    if observed["pending_exit"]:
        result.update({"pending_leader_exit": True, "known_rss_bytes": known_rss,
                       "leader_accounting_diagnostic": observed["diagnostic"]})
    return result


def group_is_empty(pgid):
    try:
        os.killpg(pgid, 0)
        return False
    except ProcessLookupError:
        return True


def peek_owned_exit(process):
    """Observe only this child without releasing its PID for reuse.

    Popen.poll()/kill() can reap a completed child. Group signals must happen
    before the sole wait(), while WNOWAIT still reserves this owned PID.
    """
    require(process.returncode is None, "Owned leader was already reaped before group cleanup.")
    require(all(hasattr(os, name) for name in ("waitid", "P_PID", "WEXITED", "WNOHANG", "WNOWAIT")),
            "Non-reaping owned-child observation is unavailable.")
    result = os.waitid(os.P_PID, process.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
    require(result is None or result.si_pid == process.pid, "Wrong owned-child wait identity.")
    return result is not None


def terminate_owned(process, seconds=RESOURCE_LIMITS["cleanup_seconds"], *, accounting_ok=True):
    deadline = time.monotonic() + seconds
    errors = []
    if process.returncode is not None:
        return {"exit_code": process.returncode, "quiescent": False, "leader_reaped": True,
                "cleanup_error": "leader_reaped_before_owned_group_cleanup"}
    try:
        exited = peek_owned_exit(process)
    except (OSError, ValueError) as error:
        # No verified unreaped ownership: never send a signal to a recyclable
        # PID/PGID. The arm fails closed and requires outer allocation cleanup.
        return {"exit_code": None, "quiescent": False, "leader_reaped": False,
                "cleanup_error": "unreaped_ownership_unconfirmed: " + str(error)[:256]}
    group_verified = False
    try:
        group_verified = os.getpgid(process.pid) == process.pid
        if group_verified:
            os.killpg(process.pid, signal.SIGKILL)
        else:
            errors.append("owned_leader_escaped_original_group")
    except OSError as error:
        errors.append("owned_group_signal_error: " + str(error)[:256])
    if not exited:
        try:
            # This exact unreaped Popen's PID cannot be recycled. Do not use
            # Popen.kill(), which internally calls poll() and can reap first.
            os.kill(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        except OSError as error:
            errors.append("owned_leader_signal_error: " + str(error)[:256])
    try:
        code = process.wait(timeout=max(0.0, deadline - time.monotonic()))
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"exit_code": None, "quiescent": False, "leader_reaped": False,
                "cleanup_error": "owned_wait_incomplete: " + str(error)[:256]}
    # After wait(), only signal-0 observations are allowed. An unexpected
    # reused PGID can cause a conservative false result, never a kill.
    group_empty = False
    if group_verified:
        try:
            group_empty = group_is_empty(process.pid)
            while not group_empty and time.monotonic() < deadline:
                time.sleep(min(0.02, max(0.0, deadline - time.monotonic())))
                group_empty = group_is_empty(process.pid)
        except OSError as error:
            errors.append("group_quiescence_unknown: " + str(error)[:256])
    return {"exit_code": code, "quiescent": bool(accounting_ok and group_empty and not errors),
            "leader_reaped": True, "cleanup_error": "; ".join(errors) or
                (None if accounting_ok else "live_process_accounting_was_incomplete")}


def environment():
    allowed = {"PATH", "LD_LIBRARY_PATH", "LIBRARY_PATH", "CUDA_VISIBLE_DEVICES", "LANG", "LC_ALL"}
    env = {key: value for key, value in os.environ.items() if key in allowed or key.startswith("SLURM_")}
    env.update(PYTHONHASHSEED="0", PYTHONDONTWRITEBYTECODE="1", HF_HUB_OFFLINE="1",
               TRANSFORMERS_OFFLINE="1", TOKENIZERS_PARALLELISM="false", WANDB_MODE="disabled",
               OMP_NUM_THREADS="8", MKL_NUM_THREADS="8", NUMEXPR_MAX_THREADS="8")
    return env


def supervise_case(app, request_path, request_sha, reservation, profile, should_stop=lambda: False):
    directory = request_path.parent
    argv = [sys.executable, "-B", str(HERE / "paired_case_worker.py"),
            "--request", str(request_path), "--request-sha256", request_sha]
    scontrol = shutil.which("scontrol")
    require(scontrol is not None, "The actual scheduler client is unavailable.")
    process = None
    stop_reason = None
    peak = samples = 0
    start_ticks = None
    accounting_ok = True
    accounting_diagnostic = None
    began = time.monotonic()
    terminal_resolution = None
    resolution_started = cleanup_deadline = resolution_deadline = None
    resolution_saw_zombie = False
    max_resolution_samples = int(RESOURCE_LIMITS["cleanup_seconds"] / RESOURCE_LIMITS["sample_seconds"]) + 1
    pending_child = child_resolution = None
    child_started = child_deadline = None
    child_episodes = []
    child_spent = 0.0
    child_samples = 0
    cleanup = {"exit_code": None, "quiescent": True, "leader_reaped": False}

    def record_resolution(diagnostic, observed_at):
        nonlocal resolution_saw_zombie
        require(type(diagnostic) is dict and len(canonical(diagnostic)) <= 4096,
                "Missing or oversized leader resolution diagnostic.")
        require(child_samples + len(terminal_resolution["samples"]) < max_resolution_samples,
                "Leader resolution sample count exceeded its finite bound.")
        terminal_resolution["samples"].append({"elapsed_seconds": observed_at - resolution_started,
                                                "leader": diagnostic})
        terminal_resolution["sample_count"] = len(terminal_resolution["samples"])
        if diagnostic.get("schema") != "hydra-paired-leader-accounting-v1":
            return False  # An unrelated failed child sample is not leader confirmation.
        states = [item.get("state") for item in diagnostic.get("stats", {}).values()]
        states += [item.get("state") for item in diagnostic.get("records", [])]
        regressed = resolution_saw_zombie and any(state != "Z" for state in states)
        resolution_saw_zombie = resolution_saw_zombie or "Z" in states
        return not regressed

    def record_child(diagnostic, observed_at):
        nonlocal child_samples
        require(type(diagnostic) is dict and len(canonical(diagnostic)) <= 4096,
                "Missing or oversized child resolution diagnostic.")
        leader_samples = 0 if terminal_resolution is None else terminal_resolution["sample_count"]
        require(child_samples + leader_samples < max_resolution_samples,
                "Shared terminal resolution sample count exceeded its finite bound.")
        frame = {"elapsed_seconds": observed_at - child_started, "child": diagnostic}
        # Leave fixed headroom for final outcome/elapsed/cleanup metadata.
        require(len(canonical(child_episodes)) + len(canonical(frame)) + 2 <= 256 * 1024 - 4096,
                "Child resolution diagnostics exceeded their byte ceiling.")
        child_resolution["samples"].append(frame)
        child_samples += 1

    with (directory / "stdout").open("xb") as stdout, (directory / "stderr").open("xb") as stderr:
        try:
            process = subprocess.Popen(argv, cwd=app.parent, env=environment(),
                stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr, start_new_session=True)
            accounting_ok = os.getpgid(process.pid) == process.pid
            require(accounting_ok, "New child is not in its owned process group.")
            while True:
                leader_waitable = peek_owned_exit(process)
                if leader_waitable and pending_child is not None:
                    accounting_ok = False
                    stop_reason = "owned_process_accounting_error: Owned leader exited before pending child accounting resolved."
                    break
                if leader_waitable and terminal_resolution is None:
                    break
                if should_stop():
                    stop_reason = "cancelled"
                    break
                if time.monotonic() - began >= WALL_PROFILES[profile]["case_seconds"]:
                    stop_reason = "case_wall_limit"
                    break
                if terminal_resolution is not None and (
                        time.monotonic() >= resolution_deadline
                        or child_samples + terminal_resolution["sample_count"] >= max_resolution_samples):
                    stop_reason = "owned_process_accounting_error: PF_EXITING leader exit remained unproven within cleanup budget."
                    break
                if child_resolution is not None and (time.monotonic() >= child_deadline
                        or child_samples >= max_resolution_samples):
                    stop_reason = "owned_process_accounting_error: PF_EXITING child exit remained unproven within cleanup budget."
                    break
                if os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > RESOURCE_LIMITS["stdout_stderr_bytes"]:
                    stop_reason = "stdout_stderr_limit"
                    break
                entries = list(directory.iterdir())
                require(len(entries) <= 32 and all(path.is_file() and not path.is_symlink() for path in entries),
                        "Case artifact inventory exceeded its bound or added non-files.")
                if sum(path.stat().st_size for path in entries) > RESOURCE_LIMITS["case_artifact_bytes"]:
                    stop_reason = "case_artifact_limit"
                    break
                sample_started = time.monotonic()
                try:
                    if pending_child is None:
                        observed = sample_owned(process, reservation["job_id"], scontrol, start_ticks)
                    else:
                        observed = sample_owned(process, reservation["job_id"], scontrol, start_ticks, pending_child)
                except (OSError, ValueError) as error:
                    if (terminal_resolution is None and pending_child is None
                            and not getattr(error, "leader_accounting_violation", False)
                            and not getattr(error, "child_accounting_violation", False)
                            and peek_owned_exit(process)):
                        break  # Completed children need not retain live /proc accounting.
                    accounting_ok = False
                    accounting_diagnostic = getattr(error, "accounting_diagnostic", None)
                    if terminal_resolution is not None and accounting_diagnostic is not None:
                        record_resolution(accounting_diagnostic, time.monotonic())
                    if child_resolution is not None and accounting_diagnostic is not None:
                        record_child(accounting_diagnostic, time.monotonic())
                    stop_reason = "owned_process_accounting_error: " + str(error)[:256]
                    break
                start_ticks = observed["start_ticks"]
                child_observation = observed.get("child_exit_observation")
                require(pending_child is None or child_observation is not None,
                        "Pending child accounting disappeared without confirmation.")
                if child_observation is not None:
                    if child_resolution is None:
                        require(child_observation["pending_exit"] and terminal_resolution is None,
                                "Child resolution must start with a distinct pending observation.")
                        child_started = sample_started
                        child_deadline = min(began + WALL_PROFILES[profile]["case_seconds"],
                            child_started + RESOURCE_LIMITS["cleanup_seconds"] - child_spent
                            - RESOURCE_LIMITS["sample_seconds"])
                        child_resolution = {"pid": str(child_observation["pid"]), "outcome": "pending",
                            "started_after_seconds": child_started - began, "samples": [],
                            "natural_exit_confirmed_before_cleanup": False,
                            "missing_rss_was_zero_filled": False}
                        child_episodes.append(child_resolution)
                    accounting_ok = False
                    accounting_diagnostic = child_observation["diagnostic"]
                    record_child(accounting_diagnostic, time.monotonic())
                    require(time.monotonic() < child_deadline,
                            "Child terminal resolution exceeded its shared cleanup deadline.")
                    if child_observation["pending_exit"]:
                        pending_child = child_observation
                    else:
                        require(child_observation["terminal"] in {"zombie", "disappeared"},
                                "Child terminal resolution has no natural confirmation.")
                        child_resolution.update(outcome="natural_exit_confirmed",
                            terminal=child_observation["terminal"], natural_exit_confirmed_before_cleanup=True,
                            elapsed_seconds=time.monotonic() - child_started)
                        child_spent += child_resolution["elapsed_seconds"]
                        pending_child = child_resolution = None
                        child_deadline = None
                        accounting_ok = True
                        accounting_diagnostic = None
                if (observed.get("pending_leader_exit") or observed.get("leader_exit_confirmed")) and terminal_resolution is None:
                    resolution_started = sample_started
                    cleanup_deadline = resolution_started + RESOURCE_LIMITS["cleanup_seconds"] - child_spent
                    # Share the existing grace with kill/reap; reserve one
                    # existing sample interval and never extend the case limit.
                    resolution_deadline = min(began + WALL_PROFILES[profile]["case_seconds"],
                                              cleanup_deadline - RESOURCE_LIMITS["sample_seconds"])
                    terminal_resolution = {"schema": "hydra-paired-terminal-resolution-v1", "outcome": "pending",
                        "started_after_seconds": resolution_started - began,
                        "limit_seconds": RESOURCE_LIMITS["cleanup_seconds"],
                        "confirmation_limit_seconds": max(0.0, resolution_deadline - resolution_started),
                        "maximum_samples": max_resolution_samples, "sample_count": 0, "samples": [],
                        "missing_rss_was_zero_filled": False, "natural_exit_confirmed_before_cleanup": False}
                    accounting_ok = False  # Restored only by confirmed natural exit below.
                if terminal_resolution is not None:
                    accounting_diagnostic = observed["leader_accounting_diagnostic"]
                    coherent = record_resolution(accounting_diagnostic, time.monotonic())
                    if not coherent or time.monotonic() >= resolution_deadline:
                        stop_reason = "owned_process_accounting_error: Leader terminal resolution changed state or exceeded its deadline."
                        break
                    if not observed.get("pending_leader_exit") and not observed.get("leader_exit_confirmed"):
                        stop_reason = "owned_process_accounting_error: Leader resumed RSS without proving pending exit."
                        break
                measured_rss = observed["rss_bytes"]
                known_rss = observed.get("known_rss_bytes", 0) if measured_rss is None else measured_rss
                peak = max(peak, known_rss)
                samples += int(measured_rss is not None)
                if known_rss > RESOURCE_LIMITS["host_sampled_rss_bytes"]:
                    stop_reason = "host_sampled_rss_limit"
                    break
                if observed.get("leader_exit_confirmed"):
                    if terminal_resolution is not None:
                        terminal_resolution["outcome"] = "natural_exit_confirmed"
                        terminal_resolution["natural_exit_confirmed_before_cleanup"] = True
                        accounting_ok = True
                        accounting_diagnostic = None
                    break
                delay = RESOURCE_LIMITS["sample_seconds"]
                if terminal_resolution is not None:
                    delay = min(delay, max(0.0, resolution_deadline - time.monotonic()))
                if child_resolution is not None:
                    delay = min(delay, max(0.0, child_deadline - time.monotonic()))
                time.sleep(delay)
        except BaseException as error:
            accounting_ok = False
            stop_reason = "controller_error: " + type(error).__name__ + ": " + str(error)[:256]
        finally:
            if child_resolution is not None:
                child_resolution["outcome"] = "failed"
                child_resolution["elapsed_seconds"] = time.monotonic() - child_started
                child_spent += child_resolution["elapsed_seconds"]
                accounting_ok = False
            if terminal_resolution is not None:
                terminal_resolution["elapsed_seconds"] = time.monotonic() - resolution_started
                if terminal_resolution["outcome"] == "pending":
                    terminal_resolution["outcome"] = "failed"
            cleanup_began = time.monotonic()
            if process is not None:
                if cleanup_deadline is None:
                    cleanup = terminate_owned(process,
                        seconds=max(0.0, RESOURCE_LIMITS["cleanup_seconds"] - child_spent),
                        accounting_ok=accounting_ok)
                else:
                    remaining = max(0.0, cleanup_deadline - time.monotonic())
                    terminal_resolution["cleanup_seconds_remaining"] = remaining
                    cleanup = terminate_owned(process, seconds=remaining, accounting_ok=accounting_ok)
                    terminal_resolution["resolution_and_cleanup_seconds"] = time.monotonic() - resolution_started
            shared_resolution_cleanup = child_spent + (time.monotonic() - cleanup_began
                if terminal_resolution is None else terminal_resolution["resolution_and_cleanup_seconds"])
        # A fast exiting process can finish between samples. Completion does
        # not exempt its final output from the same byte caps.
        if os.fstat(stdout.fileno()).st_size + os.fstat(stderr.fileno()).st_size > RESOURCE_LIMITS["stdout_stderr_bytes"]:
            stop_reason = "stdout_stderr_limit"
        entries = list(directory.iterdir())
        if (len(entries) > 32 or any(not path.is_file() or path.is_symlink() for path in entries)):
            stop_reason = "case_artifact_inventory_error"
        elif sum(path.stat().st_size for path in entries) > RESOURCE_LIMITS["case_artifact_bytes"]:
            stop_reason = "case_artifact_limit"
    if process is not None and not cleanup["quiescent"] and stop_reason is None:
        stop_reason = "owned_group_cleanup_unconfirmed"
    result = {"schema": "hydra-paired-owned-case-execution-v1", "argv": argv,
        "helper_launches": int(process is not None), "pid": None if process is None else process.pid,
        "request_sha256": request_sha, "elapsed_seconds": time.monotonic() - began,
        "termination_reason": stop_reason or "process_exit", "peak_sampled_host_rss_bytes": peak,
        "accounting_diagnostic": accounting_diagnostic,
        "terminal_resolution": terminal_resolution,
        "child_terminal_resolution": None if not child_episodes else {
            "schema": "hydra-paired-child-terminal-resolution-v1", "episodes": child_episodes,
            "sample_count": child_samples, "maximum_shared_samples": max_resolution_samples,
            "elapsed_seconds": child_spent, "limit_seconds": RESOURCE_LIMITS["cleanup_seconds"],
            "resolution_and_cleanup_seconds": shared_resolution_cleanup},
        "rss_samples": samples, "sampled_memory_can_overshoot": True,
        "limits": {**RESOURCE_LIMITS, **WALL_PROFILES[profile]}, **cleanup}
    save(directory / "execution.json", result)
    return result


def classify_case(execution, result):
    if execution["helper_launches"] == 0:
        return "infrastructure_failure"
    if not execution["quiescent"] or not execution["leader_reaped"]:
        return "infrastructure_failure"
    reason = execution["termination_reason"]
    if reason == "cancelled":
        return "cancelled"
    if reason != "process_exit":
        return "resource_stop" if reason in {"case_wall_limit", "host_sampled_rss_limit", "case_artifact_limit", "stdout_stderr_limit"} else "infrastructure_failure"
    if execution["exit_code"] in {-signal.SIGXCPU, -signal.SIGXFSZ}:
        return "resource_stop"
    if type(result) is not dict or execution["exit_code"] not in (0, 3):
        return "infrastructure_failure"
    if result.get("status") == "resource_stop" and execution["exit_code"] == 3:
        return "resource_stop"
    if execution["exit_code"] == 0 and result.get("status") in {"proved", "unknown"}:
        return result["status"]
    return "infrastructure_failure"


def source_snapshot_after(app, before):
    try:
        after = source_pins(app)
        require(after == before, "Executed sources changed during the arm.")
        return after, None
    except BaseException as failure:
        return None, {"type": type(failure).__name__, "detail": str(failure)[:1000],
                      "phase": "source_verification"}


def arm_is_complete(records, expected_count, before, after, error, cancelled):
    return bool(not cancelled and not error and after is not None and before == after
                and len(records) == expected_count
                and all(row["status"] in {"proved", "unknown", "resource_stop"} for row in records)
                and not any(row["unexpected_checked_control"] for row in records))


def run(args):
    require(platform.system() == "Linux" and platform.machine() == "aarch64"
            and sys.version_info[:3] == (3, 13, 5) and not sys.flags.ignore_environment,
            "Prepared evaluation requires the reviewed Linux/aarch64 Python3.13.5 runtime with fixed hash seed.")
    require(os.environ.get("PYTHONHASHSEED") == "0", "Set PYTHONHASHSEED=0 before launching the controller.")
    require(signal.getsignal(signal.SIGCHLD) == signal.SIG_DFL
            and all(hasattr(os, name) for name in ("waitid", "P_PID", "WEXITED", "WNOHANG", "WNOWAIT")),
            "The controller must exclusively retain and reap its direct case child.")
    app = args.app_root.resolve(strict=True)
    study_path = args.study.absolute()
    raw = ordinary(study_path)
    require(valid_sha(args.study_sha256) and sha256(raw).hexdigest() == args.study_sha256, "Study pin differs.")
    study = study_spec(strict_json(raw), SLICE_SHA)
    reservation_path = args.reservation.absolute()
    raw = ordinary(reservation_path, 65536)
    require(valid_sha(args.reservation_sha256) and sha256(raw).hexdigest() == args.reservation_sha256,
            "Reservation pin differs.")
    reservation = reservation_spec(strict_json(raw), study, args.study_sha256)
    for name, key in (("paired_controller.py", "controller_sha256"), ("paired_case_worker.py", "case_worker_sha256"),
                      ("paired_common.py", "common_sha256")):
        require(pin(HERE / name)["sha256"] == reservation[key], "Reserved controller/worker code differs.")
    before = source_pins(app)
    require(sha256(canonical(before)).hexdigest() == study["source_pins_sha256"], "Full executed source scope differs.")
    cases = selected_cases(app, study)
    output = args.output.absolute()
    require(not output.is_symlink() and output.resolve() == output, "Output must not escape through symlinks.")
    output.mkdir(parents=True, exist_ok=False)
    helpers = scheduler_helpers()
    checker = helpers.LiveReservation(reservation, output)
    started = time.monotonic()
    first = checker()
    claim = claim_reservation(reservation_path, args.reservation_sha256, reservation, output, first)
    deadline = started + reservation["seconds"] - first["elapsed_seconds"] - 20
    require(deadline - started > WALL_PROFILES[study["wall_profile"]]["case_seconds"] + 20,
            "Insufficient live allocation for one fully bounded case and cleanup.")
    save(output / "request.json", {"schema": "hydra-paired-arm-request-v1", "study": study,
        "study_sha256": args.study_sha256, "reservation": reservation,
        "reservation_sha256": args.reservation_sha256, "source_pins_before": before,
        "claim": str(claim), "case_ids": [row["id"] for row in cases],
        "campaign_ledger_enforced_by": "root_job_orchestrator", "automatic_retry": False,
        "all_model_and_training_paths_are_local": True})
    cancelled = [False]
    old_handlers = {}
    for sig in (signal.SIGTERM, signal.SIGINT):
        old_handlers[sig] = signal.signal(sig, lambda *_: cancelled.__setitem__(0, True))
    records = []
    error = None
    try:
        for index, case in enumerate(cases):
            if cancelled[0] or time.monotonic() + WALL_PROFILES[study["wall_profile"]]["case_seconds"] + 10 >= deadline:
                break
            checker()
            directory = output / f"case-{index:02d}"
            directory.mkdir(exist_ok=False)
            request = {"schema": "hydra-paired-case-request-v1", "app_root": str(app),
                "study_path": str(study_path), "study_sha256": args.study_sha256,
                "reservation_path": str(reservation_path), "reservation_sha256": args.reservation_sha256,
                "controller_pid": os.getpid(), "case_index": index, "input": case_payload(case, study["wall_profile"])}
            request_path = directory / "case-request.json"
            save(request_path, request)
            request_sha = pin(request_path)["sha256"]
            execution = supervise_case(app, request_path, request_sha, reservation,
                                      study["wall_profile"], should_stop=lambda: cancelled[0])
            result_path = directory / "case-result.json"
            result = strict_json(ordinary(result_path)) if result_path.exists() else None
            if result is not None:
                require(result.get("request_sha256") == request_sha
                        and result.get("input_sha256") == sha256(canonical(request["input"])).hexdigest()
                        and result.get("source_pins_sha256") == study["source_pins_sha256"],
                        "Case returned unbound input/source provenance.")
            status = classify_case(execution, result)
            row = {"case_id": case["id"], "family": case["family"], "category": case["category"],
                "expected": case["expected"], "input_theorem_sha256": case["input_theorem_sha256"],
                "result_path": str(result_path.relative_to(output)) if result is not None else None,
                "result_pin": pin(result_path) if result is not None else None,
                "execution_path": str((directory / "execution.json").relative_to(output)),
                "execution_pin": pin(directory / "execution.json"), "status": status,
                "model_counters": None if result is None else result.get("actual_counters"),
                "unexpected_checked_control": case["category"] == "negative_control" and status == "proved"}
            records.append(row)
            save(directory / "case-summary.json", row)
            print(canonical({"case_index": index, "status": status, "actual_child_exit": execution["exit_code"],
                             "quiescent": execution["quiescent"]}).decode(), flush=True)
            load_resource_failure = (status == "resource_stop" and type(result) is dict
                                     and (result.get("error") or {}).get("phase") == "load")
            if status == "infrastructure_failure" or not execution["quiescent"] or row["unexpected_checked_control"] or load_resource_failure:
                break
    except BaseException as failure:
        error = {"type": type(failure).__name__, "detail": str(failure)[:1000]}
    finally:
        for sig, handler in old_handlers.items():
            signal.signal(sig, handler)
        after, source_error = source_snapshot_after(app, before)
        if error is None and source_error is not None:
            error = source_error
        remaining = [{"case_id": row["id"], "status": "not_run"} for row in cases[len(records):]]
        complete = arm_is_complete(records, len(cases), before, after, error, cancelled[0])
        summary = {"schema": "hydra-paired-arm-completion-v1", "status": "complete" if complete else "incomplete",
            "arm": reservation["arm"], "study_sha256": args.study_sha256,
            "reservation_sha256": args.reservation_sha256, "job_id": reservation["job_id"],
            "cases": records, "not_run": remaining, "error": error, "cancelled": cancelled[0],
            "source_verification_error": source_error,
            "source_pins_after": after, "sources_unchanged": before == after,
            "elapsed_seconds": time.monotonic() - started, "scheduler_calls": checker.calls,
            "last_live_allocation": checker.last, "automatic_retry": False, "resume": False,
            "training_allowed": False, "retrieval_allowed": False, "benchmark_claim": False,
            "control_unknown_is_not_refutation": True, "actual_slurm_exit_requires_collected_scheduler_receipt": True}
        save(output / "completion.json", summary)
    return 0 if complete else 2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-root", type=Path, required=True)
    parser.add_argument("--study", type=Path, required=True)
    parser.add_argument("--study-sha256", required=True)
    parser.add_argument("--reservation", type=Path, required=True)
    parser.add_argument("--reservation-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        return run(args)
    except BaseException as failure:
        print(canonical({"status": "failed", "type": type(failure).__name__,
                         "detail": str(failure)[:1000], "automatic_retry": False}).decode(), flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
