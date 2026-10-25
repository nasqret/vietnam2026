"""Read this process's RSS once; no child, solver, HTTP, model, or search."""
from pathlib import Path
import ctypes
import hashlib
import json
import os
import resource
import signal
import sys

HERE = Path(__file__).resolve().parent
assert sys.flags.isolated and sys.dont_write_bytecode
resource.setrlimit(resource.RLIMIT_CPU, (2, 2))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
signal.alarm(3)
sys.path.insert(0, str(HERE / "app"))
import vampire_process as runner
rss = runner._resident_size(os.getpid())
record = {"schema": "hydra-fixed-darwin-rss-self-probe-v1", "passed": rss > 0,
          "source_sha256": hashlib.sha256((HERE / "app/vampire_process.py").read_bytes()).hexdigest(),
          "platform": sys.platform, "api": "libproc.proc_pidinfo", "flavor": 4,
          "struct_bytes": ctypes.sizeof(runner._ProcTaskInfo),
          "resident_size_offset": runner._ProcTaskInfo.resident_size.offset,
          "sampled_self_rss_bytes": rss, "self_pid": os.getpid(),
          "child_processes_started": 0, "solver_invocations": 0, "model_invocations": 0}
with (HERE / "darwin-self-probe-result.json").open("x", encoding="utf-8") as stream:
    json.dump(record, stream, indent=2)
    stream.write("\n")
print(json.dumps(record), flush=True)
