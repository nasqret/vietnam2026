"""Standalone cold-runtime check; no concurrent retained Alpha parent."""
from pathlib import Path
import os
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[3]

def test_cold_installed_runtime_is_artifact_free_and_imports_no_authoring_scripts():
    program = r"""
import resource,signal
resource.setrlimit(resource.RLIMIT_CPU,(170,175))
signal.alarm(180)
from pathlib import Path
import builtins,sys
original_open=Path.open
original_import=builtins.__import__
def guarded_open(path,*args,**kwargs):
    if "catalog" in path.name or "proof-bundle" in path.name:
        raise AssertionError("cold runtime opened an artifact/catalogue")
    return original_open(path,*args,**kwargs)
def guarded_import(name,*args,**kwargs):
    if name=="scripts" or name.startswith("scripts.") or name.startswith("constructive_"):
        raise AssertionError("cold runtime imported authoring scripts")
    return original_import(name,*args,**kwargs)
Path.open=guarded_open
builtins.__import__=guarded_import
from peano_lab.library import editions_v34 as v
v.require_research_seal()
assert len(v.ALPHA_CHECKED_SPECS)==4223 and len(v.STABLE_SPECS)==432
assert not any(name=="scripts" or name.startswith("scripts.") for name in sys.modules)
assert v._checked_research_bundle.cache_info().currsize==0
assert v.replay.cache_info().currsize==0
peak=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
if sys.platform!="darwin":
    peak*=1024
assert peak<=1536*1024*1024
print("artifact-free installed v34 PASS")
"""
    result = subprocess.run([sys.executable, "-c", program], cwd=ROOT,
                            env=dict(os.environ, PYTHONPATH=str(ROOT / "peano-lab/py"),
                                     PYTHONMALLOC="pymalloc", PYTHONDONTWRITEBYTECODE="1"),
                            text=True, capture_output=True, timeout=180)
    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.strip() == "artifact-free installed v34 PASS"
