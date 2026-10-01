#!/usr/bin/env python3
"""Freeze an explicit local wave inventory, without scanning or admitting proofs."""
from hashlib import sha256
import argparse
import json
from pathlib import Path

from run_sqrt2_power_wave import ROOT, target_for, formula_sha256
from run_sqrt2_power_pilot import save_new

BASE = ROOT / "research/arithmetic-library/sqrt2-power/observations"
ATTEMPTS = (
    ("shared-wave-p10-v1", "P10"),
    ("shared-wave-p08-e-v1", "P08-eprover"),
    ("shared-wave-p08-v-v1", "P08-vampire"),
    ("shared-wave-p04-ground-v1", "P04-ground"),
    ("shared-wave-p04-ground-flat-v2", "P04-ground"),
    ("shared-wave-p04-soundness-v1", "P04-soundness"),
    *((f"shared-wave-rf{i:03d}-v1", f"RF{i:03d}") for i in range(1, 7)),
    ("shared-wave-rf003-typed-v2", "RF003"),
    *((f"shared-wave-p04-c{i:02d}-v1", f"P04-C{i:02d}") for i in range(16)),
    ("shared-wave-ir016-v1", "IR016"),
    ("shared-wave-signed-norm-v1", "SN001"),
    ("shared-wave-natural-gap-v1", "NG001"),
    ("shared-wave-norm-separation-v1", "SN002"),
    ("shared-wave-norm-product-v1", "SN003"),
    ("shared-wave-convolution-vanishing-v1", "CV001"),
    ("shared-wave-convolution-vanishing-v2", "CV001"),
    ("shared-wave-convolution-vanishing-v3", "CV001"),
    ("shared-wave-rational-norm-transport-v1", "RN001"),
    ("shared-wave-rational-norm-product-v1", "RN002"),
    ("shared-wave-signed-product-nonzero-v1", "SI001"),
    ("shared-wave-quadratic-nonzero-v1", "QN001"),
    ("shared-wave-quadratic-product-trace-v1", "QF001"),
)
LEAN_REPORTS = ("fresh-lean-wave-v1", "fresh-lean-foundations-v1",
                "fresh-lean-negative-controls-v2", "fresh-lean-composition-chunks-v1",
                "fresh-lean-ir016-v1", "fresh-lean-signed-norm-v1", "fresh-lean-norm-separation-v1",
                "fresh-lean-norm-product-v1", "fresh-lean-convolution-vanishing-v1",
                "fresh-lean-rational-norm-wave-v1", "fresh-lean-quadratic-products-v1")


def index_entry(folder, case=None):
    path = BASE / folder / "report.json"
    raw = path.read_bytes()
    row = dict(path=str(path.relative_to(ROOT)), bytes=len(raw), sha256=sha256(raw).hexdigest())
    if case is not None:
        row.update(case=case, target_ast_sha256=formula_sha256(target_for(case)))
    return row


def build(output):
    value = dict(schema="sqrt2-power-wave-evidence-index-v1",
        reports=[index_entry(folder, case) for folder, case in ATTEMPTS],
        lean_reports=[index_entry(folder) for folder in LEAN_REPORTS])
    raw = json.dumps(value, indent=2, sort_keys=True).encode()+b"\n"
    save_new(output, raw)
    return dict(path=str(output), sha256=sha256(raw).hexdigest(), reports=len(value["reports"]))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(build(args.output), sort_keys=True))
