#!/usr/bin/env python3
"""Run an exact, bounded current-Alpha UI regression window.

A test observation is not mathematical proof authority. No catalogue, stored
receipt or test-only release capability is accepted here. Existing tests run
their real selectors, sentinels and (where specified) actual Lean compiler.
Each invocation uses the original resource limits and rejects skips/xfails.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
from pathlib import Path
import resource
import signal
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    ("test_alpha_v16_ui.py", 181),
    ("test_alpha_v28_ui.py", 146),
    ("test_alpha_v30_ui.py", 148),
    ("test_alpha_v31_ui.py", 168),
    ("test_alpha_v32_ui.py", 92),
    ("test_alpha_v33_ui.py", 79),
    ("test_lean_proof_strand.py", 122),
    ("test_lean_proof_strand_ui.py", 73),
    ("test_lean_proof_strand_cli.py", 120),
    ("test_lean_presentation_ui.py", 45),
    ("test_lean_presentation_cli.py", 50),
    ("test_lean_strand_service_v33.py", 165),
    ("test_browser_shell.py", 20),
    ("test_alpha_v34_ui.py", 171),
    ("test_lean_strand_service_v34.py", 64),
    ("test_peano_worker_v34.py", 30),
    ("test_lean_strand_service_v31.py", 67),
    ("test_library_editions_v34_admission.py", 123),
    ("test_library_editions_v34_cold_import.py", 1),
)
CPU_LIMITS, WALL_SECONDS, MAX_RSS = (170, 175), 180, 1536 * 1024 * 1024


def _pins(filename):
    paths = (
        "scripts/check_alpha_v34_ui.py",
        "peano-lab/py/tests/" + filename,
        "peano-lab/py/peano_lab/ui/data_library.py",
        "peano-lab/py/peano_lab/library/lean_proof_strand.py",
        "scripts/export_peano_lean.py",
        "scripts/serve_lean_strands.py",
        "peano-lab/worker.js",
        "peano-lab/APP_MANIFEST.sha256",
        "peano-lab/index.html",
        "peano-lab/.htaccess",
        "peano-lab/py/tests/worker_boot_harness.js",
        "scripts/update_peano_worker_sources.py",
        "peano-lab/py/tests/test_lean_strand_service.py",
        "peano-lab/py/tests/test_lean_strand_service_v31.py",
        "peano-lab/py/tests/test_lean_strand_service_v33.py",
        "scripts/peano_catalog_capacity_v34.py",
        "scripts/peano_catalog_shards_v34.py",
        *(f"peano-lab/py/peano_lab/library/{name}.py" for name in (
            "alpha_enrollment_v33", "campaign_research_v33_closure", "editions_v33",
            "alpha_enrollment_v34", "campaign_research_v34_closure", "editions_v34",
            "research_source_plan_v34")),
    )
    records = {}
    for path in paths:
        location = ROOT / path
        if location.is_symlink() or not location.is_file():
            raise ValueError("nonordinary UI source")
        raw = location.read_bytes()
        records[path] = {"bytes": len(raw), "sha256": sha256(raw).hexdigest()}
    return records


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("filename", choices=dict(FILES))
    parser.add_argument("--start", type=int, default=0)
    parser.add_argument("--count", type=int)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args(argv)
    expected_total = dict(FILES)[args.filename]
    count = expected_total - args.start if args.count is None else args.count
    if args.start < 0 or count <= 0 or args.start + count > expected_total:
        parser.error("the requested exact test window does not exist")
    resource.setrlimit(resource.RLIMIT_CPU, CPU_LIMITS)
    signal.alarm(WALL_SECONDS)
    started = time.monotonic()
    before = _pins(args.filename)
    for directory in (ROOT / "scripts", ROOT / "peano-lab/py"):
        sys.path.insert(0, str(directory))
    import pytest

    class Accounting:
        def __init__(self):
            self.selected, self.all_ids, self.reports, self.bad = [], [], [], False

        @pytest.hookimpl(trylast=True)
        def pytest_collection_modifyitems(self, session, config, items):
            self.all_ids = [item.nodeid for item in items]
            if len(items) != expected_total or len(set(self.all_ids)) != expected_total:
                raise ValueError("the complete mandatory UI case inventory changed")
            chosen = items[args.start:args.start + count]
            self.selected = [item.nodeid for item in chosen]
            config.hook.pytest_deselected(items=items[:args.start] + items[args.start + count:])
            items[:] = chosen

        def pytest_collectreport(self, report):
            if report.failed or report.skipped:
                self.bad = True

        def pytest_runtest_logreport(self, report):
            self.reports.append((report.nodeid, report.when, report.outcome, hasattr(report, "wasxfail")))
            if report.failed or report.skipped or hasattr(report, "wasxfail"):
                self.bad = True

    ledger = Accounting()
    options = ["-q", "--tb=short", str(ROOT / "peano-lab/py/tests" / args.filename)]
    if args.collect_only:
        options.append("--collect-only")
    status = int(pytest.main(options, plugins=[ledger]))
    elapsed = time.monotonic() - started
    usage, children = (resource.getrusage(kind) for kind in (resource.RUSAGE_SELF, resource.RUSAGE_CHILDREN))
    peak = int(max(usage.ru_maxrss, children.ru_maxrss))
    if sys.platform != "darwin":
        peak *= 1024
    expected_reports = [(identifier, phase, "passed", False)
                        for identifier in ledger.selected for phase in ("setup", "call", "teardown")]
    after = _pins(args.filename)
    passed = (status == 0 and not ledger.bad and len(ledger.selected) == count
              and (args.collect_only or ledger.reports == expected_reports)
              and before == after and elapsed < WALL_SECONDS and 0 < peak <= MAX_RSS)
    record = {
        "schema": "alpha-v34-ui-window-observation-v1", "proof_authority": False,
        "filename": args.filename, "start": args.start, "count": count,
        "complete_file_case_count": expected_total, "collected_ids": ledger.selected,
        "complete_file_ids_sha256": sha256("\n".join(ledger.all_ids).encode()).hexdigest(),
        "reports": ledger.reports, "source_pins": before, "source_pins_after": after,
        "collect_only": args.collect_only,
        "passed": passed, "pytest_status": status, "seconds": elapsed,
        "cpu_seconds": usage.ru_utime + usage.ru_stime, "peak_rss_bytes": peak,
        "cpu_limits": list(resource.getrlimit(resource.RLIMIT_CPU)), "wall_seconds": WALL_SECONDS,
    }
    print("UI_WINDOW_OBSERVATION=" + json.dumps(record, sort_keys=True), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
