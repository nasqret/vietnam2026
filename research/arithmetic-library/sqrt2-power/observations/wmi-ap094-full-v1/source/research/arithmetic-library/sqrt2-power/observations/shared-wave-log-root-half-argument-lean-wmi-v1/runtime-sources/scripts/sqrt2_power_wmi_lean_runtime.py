"""Private instance of the unchanged supervisor, with a Lean-only Linux guard.

The original module and its GUARD are never mutated. This separately named
instance keeps the same wait4 accounting, process-group cleanup, sampled RSS,
output bounds, receipt validation and CPU ceilings. Its explicit guard changes
only the virtual-address-space cap for Lean, not the physical-RSS limit.
"""
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]


def lean_runtime():
    name="_sqrt2_wmi_lean_review_runtime"
    if name not in sys.modules:
        spec=importlib.util.spec_from_file_location(name,ROOT/"training/peano_hydra/review_runtime.py")
        module=importlib.util.module_from_spec(spec)
        sys.modules[name]=module
        spec.loader.exec_module(module)
        module.GUARD=ROOT/"scripts/sqrt2_power_wmi_lean_guard.py"
        module.RESOURCE_MEASUREMENT += "; Lean-only Linux guard: 16-GiB virtual address cap, separate sampled RSS"
    return sys.modules[name]
