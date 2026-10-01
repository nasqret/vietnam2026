#!/usr/bin/env python3
"""Run bounded regression batches in fresh processes; never widen a failed batch."""
import argparse
import ast
from hashlib import sha256
import json
from pathlib import Path
import sys
import time

from run_sqrt2_power_pilot import ROOT, save_new, successful, controller_deadline
from sqrt2_power_automation_baseline import runtime


def validate(output, files):
    if output.exists() or output.is_symlink():
        raise ValueError("new validation report required")
    batches, pins = [], {}
    for relative in files:
        path = ROOT / relative
        raw = path.read_bytes()
        pins[relative] = dict(bytes=len(raw), sha256=sha256(raw).hexdigest())
        if path.name == "test_sqrt2_power_campaign.py":
            test_class = next(n for n in ast.parse(raw).body
                if isinstance(n, ast.ClassDef) and n.name == "CampaignPlanTests")
            ordinary, regeneration = [], []
            for node in test_class.body:
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    group = regeneration if node.name == "test_regeneration_is_byte_deterministic" else ordinary
                    group.append(relative+"::CampaignPlanTests::"+node.name)
            if not ordinary or len(regeneration) != 1:
                raise ValueError("campaign regeneration test boundary changed")
            # Fresh regeneration versus the independently built on-disk
            # snapshot has its own allocator lifetime.
            batches.extend((ordinary, regeneration))
        elif path.name in {"test_sqrt2_power_wave_results.py", "test_sqrt2_power_signed_norm.py",
                           "test_sqrt2_power_norm_separation.py", "test_sqrt2_power_quadratic_norm_product.py",
                           "test_sqrt2_power_convolution_vanishing.py", "test_sqrt2_power_rational_norm_product.py",
                           "test_sqrt2_power_rational_norm_transport.py", "test_sqrt2_power_signed_product_nonzero.py",
                           "test_sqrt2_power_quadratic_nonzero.py", "test_sqrt2_power_quadratic_product_trace.py",
                           "test_sqrt2_power_arithmetic_wave.py"}:
            # Expected-exception tests retain large historical payloads within
            # pytest. Bound that lifetime by grouping four source functions.
            names = []
            for node in ast.parse(raw).body:
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    names.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    names.extend(node.name+"::"+member.name for member in node.body
                                 if isinstance(member, ast.FunctionDef) and member.name.startswith("test_"))
            if not names:
                raise ValueError("fresh-process test inventory is empty")
            # The signed-norm archive tests parse a large historical source.
            # Do not retain that allocator lifetime into a new proof fixture.
            width = 4 if path.name == "test_sqrt2_power_wave_results.py" else 1
            for i in range(0, len(names), width):
                selected = names[i:i+width]
                if (path.name == "test_sqrt2_power_arithmetic_wave.py" and selected ==
                        ["test_exact_new_statements_and_bytes_have_fresh_HA_and_Lean_evidence"]):
                    # Each parameter validates every indexed archive. The
                    # expanded wave no longer fits all parameters into one
                    # CPU-capped process; keep each parameter's lifetime short.
                    assignments = [n for n in ast.parse(raw).body if isinstance(n, ast.Assign)
                        and any(isinstance(t, ast.Name) and t.id == "ATTEMPTS" for t in n.targets)]
                    if len(assignments) != 1:
                        raise ValueError("exact archive-test parameter inventory changed")
                    attempts = ast.literal_eval(assignments[0].value)
                    for folder, case in attempts[2:]:
                        if not all(isinstance(s, str) and s and "[" not in s and "]" not in s for s in (folder, case)):
                            raise ValueError("unsafe archive-test selector")
                        batches.append([relative+"::"+selected[0]+"["+folder+"-"+case+"]"])
                else:
                    batches.append([relative+"::"+name for name in selected])
        else:
            batches.append([relative])
    results = []
    started = time.monotonic()
    with controller_deadline(started+45*len(batches)):
        for batch in batches:
            command = (sys.executable, "-B", "-m", "pytest", "-q", "-x", "--tb=line",
                       "--disable-warnings", "-p", "no:cacheprovider", *batch)
            limits = runtime().ProcessLimits(cpu_seconds=25, wall_seconds=35,
                rss_bytes=512*1024**2, output_bytes=1024**2)
            process = runtime().run_bounded(command, cwd=ROOT, limits=limits)
            runtime().validate_process_record(process, command=command, limits=limits)
            results.append(process)
            print(json.dumps(dict(batch=batch, passed=successful(process), reason=process["reason"],
                stdout=process["stdout"], resources=process["resources"])), flush=True)
            if not successful(process):
                break
        for name, pin in pins.items():
            if runtime().hash_file(ROOT/name) != pin:
                raise ValueError("test source changed during validation")
        report = dict(schema="sqrt2-power-batched-validation-v1", source_pins=pins, processes=results,
            requested_batches=len(batches), completed_batches=len(results), max_workers=1,
            status="passed" if len(results) == len(batches) and all(successful(r) for r in results) else "failed_or_incomplete",
            elapsed_wall_seconds=time.monotonic()-started, IR_parents_closed=0)
        save_new(output, json.dumps(report, sort_keys=True, indent=2).encode()+b"\n")
    return report["status"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("files", nargs="+")
    args = parser.parse_args()
    status = validate(args.output, args.files)
    raise SystemExit(0 if status == "passed" else 1)
