"""The fixed subprocess boundary, including one real guarded solver smoke."""
from pathlib import Path
import json
import subprocess
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP))
import vampire_process as runner


class SpawnBoundaryTests(unittest.TestCase):
    def test_file_inclusion_is_rejected_even_with_whitespace_or_comments(self):
        for problem in ("include ('private.p').", "include/*comment*/('private.p').", "INCLUDE('x')."):
            with self.assertRaises(ValueError):
                runner.VampireRunner()(problem)

    def test_only_exact_helper_command_and_environment_are_authorized(self):
        args = (sys.executable, runner.spawn_argv(), str(APP), dict(runner.ENVIRONMENT))
        self.assertTrue(runner.authorized_spawn(*args))
        for changed in (("/bin/sh", *args[1:]), (args[0], [*args[1], "--version"], *args[2:]),
                        (*args[:2], "/tmp", args[3]), (*args[:3], {**args[3], "PYTHONPATH": "/tmp"})):
            self.assertFalse(runner.authorized_spawn(*changed))

    def test_guard_rejects_shell_launch_and_permits_only_fixed_solver_helper(self):
        if not runner.metadata_status()["available"]:
            self.skipTest("Pinned local Vampire has not been prepared")
        script = f'''import sys,json,subprocess
sys.path.insert(0,{str(APP)!r})
import worker
from vampire_process import VampireRunner
worker.install_guard('search',allow_vampire=True)
try:
 open('guard-must-not-create-this-file','w')
except PermissionError:
 pass
else:
 raise AssertionError('file write was allowed')
try:
 subprocess.run(['/bin/sh','-c','true'],check=True)
except RuntimeError:
 pass
else:
 raise AssertionError('unrelated process was allowed')
r=VampireRunner()('fof(goal,conjecture,(a = a)).\\n')
assert r['executed'] and r['exit_code']==0 and 'SZS status Theorem' in r['stdout'],r
print(json.dumps({{'status':'passed','solver_executed':r['executed']}}))
'''
        process = subprocess.run([sys.executable, "-I", "-B", "-c", script],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=8, cwd=str(APP))
        self.assertEqual(process.returncode, 0, process.stderr.decode() + process.stdout.decode())
        self.assertEqual(json.loads(process.stdout)["status"], "passed")


if __name__ == "__main__":
    unittest.main()
