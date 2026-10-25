"""Pure scheduler/recording checks; never contact Slurm or import a model/native engine."""
from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import unittest

PATH = Path(__file__).with_name("remote_provider_smoke.py")
SPEC = importlib.util.spec_from_file_location("p6_remote_smoke", PATH)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def reservation():
    return {"schema": "hydra-p6-smoke-reservation-v1", "job_id": "21460000", "job_name": "hydra-p6-q4-smoke",
        "nonce": "a" * 32, "uid": os.getuid(), "account": MODULE.ACCOUNT, "partition": MODULE.PARTITION,
        "model_key": "qwen3-4b-base", "gpus": 1, "nodes": 1, "cpus": 8, "memory_gib": 64, "seconds": 600}


def scheduler(record):
    return (f"JobId={record['job_id']} JobName={record['job_name']} UserId=owner({record['uid']}) "
        f"Account={record['account']} Partition={record['partition']} Comment=hydra-p6:{record['nonce']} "
        "JobState=RUNNING Requeue=0 Restarts=0 NumNodes=1 NumCPUs=8 NodeList=hgpu0001 "
        "AllocTRES=cpu=8,mem=64G,node=1,billing=8,gres/gpu=1,gres/gpu:gh200=1 "
        "RunTime=00:00:42 TimeLimit=00:10:00")


class SmokePureTests(unittest.TestCase):
    def test_exact_owned_reservation_and_live_allocations_parse(self):
        record = reservation()
        self.assertEqual(MODULE.reservation_spec(record), record)
        actual = MODULE.parse_scontrol(scheduler(record), record)
        self.assertEqual(actual['elapsed_seconds'], 42)
        self.assertEqual(actual['gpus'], 1)
        self.assertEqual(actual['memory_gib'], 64)

    def test_missing_foreign_requeued_or_extra_resources_rejected(self):
        record = reservation(); raw = scheduler(record)
        for before, after in (
            ('JobState=RUNNING', 'JobState=PENDING'), ('Requeue=0', 'Requeue=1'),
            ('Restarts=0', 'Restarts=1'), ('NumNodes=1', 'NumNodes=2'),
            ('NumCPUs=8', 'NumCPUs=16'), ('cpu=8,', 'cpu=16,'), ('mem=64G', 'mem=128G'),
            ('gres/gpu=1', 'gres/gpu=2'), ('TimeLimit=00:10:00', 'TimeLimit=00:20:00'),
            ('Comment=hydra-p6:', 'Comment=wrong:'), ('RunTime=00:00:42', 'RunTime=00:09:59'),
            (f"owner({os.getuid()})", f"owner({os.getuid()+1})"),
        ):
            with self.subTest(before=before):
                with self.assertRaises(ValueError):
                    MODULE.parse_scontrol(raw.replace(before, after), record)
        with self.assertRaises(ValueError):
            MODULE.parse_scontrol(raw + ' JobId=21460001', record)
        with self.assertRaises(ValueError):
            MODULE.parse_scontrol(raw.replace('Restarts=0 ', ''), record)

    def test_invented_fields_nonce_and_float_resources_rejected(self):
        for key, value in (('nonce', 'short'), ('cpus', 8.0), ('model_key', '4B'), ('new_flag', True)):
            changed = deepcopy(reservation()); changed[key] = value
            with self.assertRaises(ValueError):
                MODULE.reservation_spec(changed)

    def test_duration_memory_and_json_bounds(self):
        self.assertEqual(MODULE.seconds('1-02:03:04'), 93784)
        self.assertEqual(MODULE.memory_gib('65536M'), 64)
        for value in ('UNLIMITED', '00:60:00', 'garbage'):
            with self.assertRaises(ValueError): MODULE.seconds(value)
        for raw in ('{"x":1,"x":2}', '{"x":NaN}', '[]'):
            with self.assertRaises(ValueError): MODULE.strict_json(raw)

    def test_recording_wrapper_preserves_callbacks_and_actual_counters(self):
        # Explicit pure recording fixture, not a model or inference test.
        class Delegate:
            identity = object()
            calls = generated_tokens = 0
            def encode_prompt(self, prompt): return (1, 2, 3)
            def generate(self, ids, *, max_new_tokens, should_stop):
                self.calls += 1; self.generated_tokens += 2; return (4, 5)
            def decode_output(self, ids): return '{"v":1,"plans":[]}'
        delegate = Delegate(); wrapper = MODULE.RecordingPlanner(delegate)
        ids = wrapper.encode_prompt('complete prompt')
        output = wrapper.generate(ids, max_new_tokens=2)
        text = wrapper.decode_output(output)
        self.assertIs(wrapper.identity, delegate.identity)
        self.assertEqual(wrapper.calls, 1)
        self.assertEqual(wrapper.generated_tokens, 2)
        self.assertEqual(wrapper.input_ids, ids)
        self.assertEqual(wrapper.output_text, text)


if __name__ == '__main__':
    unittest.main()
