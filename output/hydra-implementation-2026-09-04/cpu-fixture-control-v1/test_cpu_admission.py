"""Pure scheduler strings only; no scheduler/native/model execution."""
import importlib.util
from pathlib import Path
import os
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("cpu_wrapper", HERE / "remote_cpu_fixture.py")
wrapper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wrapper)

RECORD = {"job_id": "21910000", "job_name": "hydra-cpu-fixture-aabb", "nonce": "a" * 32, "uid": 105923}
RAW = ("JobId=21910000 JobName=hydra-cpu-fixture-aabb Comment=hydra-cpu-fixture:" + "a" * 32
       + " UserId=plgnasqret(105923) Account=plgccaiautore2026-cpu Partition=plgrid JobState=RUNNING"
       " Requeue=0 Restarts=0 NumNodes=1 NumCPUs=2 NumTasks=1 NodeList=hcpu001 TimeLimit=00:02:00"
       " RunTime=00:00:03 ReqTRES=cpu=2,mem=4G,node=1,billing=2 AllocTRES=cpu=2,mem=4G,node=1,billing=2"
       " TresPerTask=cpu=2")


def seconds(value):
    h, m, s = map(int, value.split(":"))
    return h * 3600 + m * 60 + s


class AdmissionTests(unittest.TestCase):
    def admit(self, text):
        with patch.object(wrapper.os, "getuid", return_value=105923), \
             patch.object(wrapper.os, "uname", return_value=type("Host", (), {"nodename": "hcpu001.cluster"})()), \
             patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "", "SLURM_JOB_GPUS": "", "SLURM_STEP_GPUS": ""}):
            return wrapper.parse_cpu_allocation(text, RECORD, seconds, lambda value: {"4G": 4, "4096M": 4}[value])

    def test_realistic_cpu_per_task(self):
        result = self.admit(RAW)
        self.assertEqual((result["cpus"], result["memory_gib"], result["gpus"]), (2, 4, 0))

    def test_absent_per_task_is_allowed(self):
        self.assertEqual(self.admit(RAW.replace(" TresPerTask=cpu=2", ""))["gpus"], 0)

    def test_gpu_and_resource_near_misses_rejected(self):
        changes = (("TresPerTask=cpu=2", "TresPerTask=cpu=2,gres/gpu=1"),
                   ("TresPerTask=cpu=2", "TresPerTask=cpu=8"),
                   ("AllocTRES=cpu=2,mem=4G,node=1,billing=2", "AllocTRES=cpu=2,mem=4G,node=1,gres/gpu=1"),
                   ("Account=plgccaiautore2026-cpu", "Account=plgccaiautore2026-gpu-gh200"),
                   ("TimeLimit=00:02:00", "TimeLimit=00:03:00"),
                   ("JobState=RUNNING", "JobState=PENDING"),
                   ("UserId=plgnasqret(105923)", "UserId=other(12345)"))
        for old, new in changes:
            with self.subTest(new=new), self.assertRaises(ValueError):
                self.admit(RAW.replace(old, new))


if __name__ == "__main__":
    unittest.main()
