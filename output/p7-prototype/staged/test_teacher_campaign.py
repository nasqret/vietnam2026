"""Pure scheduler/owned-lifecycle tests with explicit Popen fixtures only."""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import teacher_campaign as campaign


def reservation():
    return {"schema": "hydra-p7-teacher-reservation-v1", "job_id": "123",
        "job_name": "hydra-teacher-test", "nonce": "a" * 32, "uid": os.getuid(),
        "account": campaign.ACCOUNT, "partition": campaign.PARTITION, "model_key": campaign.MODEL_KEY,
        "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64, "seconds": 7200}


class FakeProcess:
    """No subprocess is launched by this unit fixture."""
    pid = 987654
    returncode = None
    def __init__(self):
        self.kills = self.waits = 0
    def poll(self):
        return self.returncode
    def kill(self):
        self.kills += 1
        self.returncode = -9
    def wait(self, timeout=None):
        self.waits += 1
        return self.returncode


class CampaignContractTests(unittest.TestCase):
    def test_teacher_reservation_has_its_own_finite_identity(self):
        self.assertEqual(campaign.reservation_spec(reservation())["seconds"], 7200)
        for key, value in (("model_key", "qwen3-4b-base"), ("seconds", 7201),
                           ("gpus", 2), ("nodes", True), ("uid", os.getuid() + 1)):
            bad = reservation()
            bad[key] = value
            with self.assertRaises(ValueError):
                campaign.reservation_spec(bad)
        bad = reservation()
        bad["extra"] = True
        with self.assertRaises(ValueError):
            campaign.reservation_spec(bad)

    def test_missing_rss_fails_closed_and_reaps_only_owned_child(self):
        process = FakeProcess()
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / "native"
            with patch.object(campaign.subprocess, "Popen", return_value=process) as launch, \
                    patch.object(campaign, "_child_rss", side_effect=ValueError("no RSS")):
                result = campaign.native_child({"kind": "snapshot"}, app=Path(folder), directory=directory, stop=lambda: False)
            self.assertEqual(launch.call_count, 1)
            self.assertEqual(process.kills, 1)
            self.assertGreaterEqual(process.waits, 1)
            self.assertEqual(result["status"], "resource_limit")
            receipt = json.loads((directory / "execution.json").read_bytes())
            self.assertEqual(receipt["actual_exit_code"], -9)
            self.assertTrue(receipt["quiescent"])
            self.assertEqual(receipt["stopped_for"], "owned_child_rss_unavailable")
            self.assertFalse(result["positive_distillation_eligible"])

    def test_cancellation_after_launch_still_retains_actual_exit(self):
        process = FakeProcess()
        calls = [0]
        def stop():
            calls[0] += 1
            if calls[0] > 1:
                raise campaign.CampaignCancelled("fixture cancellation")
            return False
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder) / "native"
            with patch.object(campaign.subprocess, "Popen", return_value=process):
                with self.assertRaises(campaign.CampaignCancelled):
                    campaign.native_child({"kind": "snapshot"}, app=Path(folder), directory=directory, stop=stop)
            receipt = json.loads((directory / "execution.json").read_bytes())
            self.assertEqual(receipt["actual_exit_code"], -9)
            self.assertTrue(receipt["quiescent"])
            self.assertEqual(process.kills, 1)

    def test_json_duplicate_keys_and_nonfinite_numbers_fail(self):
        for raw in ('{"a":1,"a":2}', '{"a":NaN}'):
            with self.assertRaises(ValueError):
                campaign.strict_json(raw)


if __name__ == "__main__":
    unittest.main()
