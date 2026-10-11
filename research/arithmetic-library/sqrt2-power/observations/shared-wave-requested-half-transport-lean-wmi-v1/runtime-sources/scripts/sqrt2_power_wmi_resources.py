"""Owner-approved WMI AP090 v2 hardware profile, not proof-validity limits.

The 2026-10-04 approval explicitly permits using the cluster's larger resources.
The historical local profile and source-pinned supervisor remain unchanged.
"""
import os
import re
import sys

NAME = "wmi-ap090-v2"
REQUESTED = dict(partition="cpu_idle", cpus=1, memory_mib=4096, wall_seconds=2700)
WORKER_RSS_BYTES = 2 * 1024**3
LEAN_ADDRESS_SPACE_BYTES = 16 * 1024**3
HA_PHASE = (120, 180)
HA_CONTROLLER_WALL = 480
PREFLIGHT_PHASE = (60, 90)
LEAN_PHASES = dict(version=(5, 15), build=(60, 90), check=(120, 180), negative=(30, 60))
ALLOWED_PARTITIONS = frozenset(("cpu_idle", "cpu"))
# The owner explicitly allowed the normal cpu partition on 2026-10-04 after
# cpu_idle saturation. Only routing changes; all CPU/RSS/wall guards remain.


def require_allocation():
    """Execution routing check; Slurm/cgroups, not env values, enforce allocation."""
    if (sys.platform != "linux" or not re.fullmatch(r"[1-9][0-9]*", os.environ.get("SLURM_JOB_ID", ""))
            or os.environ.get("SLURM_CPUS_PER_TASK") != "1"
            or os.environ.get("SLURM_JOB_PARTITION") not in ALLOWED_PARTITIONS
            or os.environ.get("SLURM_MEM_PER_NODE") != "4096"
            or os.environ.get("SLURM_RESTART_COUNT", "0") != "0"
            or not re.fullmatch(r"[0-9a-f]{64}", os.environ.get("PEANO_SQRT2_SNAPSHOT_SHA256", ""))):
        raise ValueError("WMI v2 requires its explicit fresh one-CPU/4-GiB Slurm allocation")
