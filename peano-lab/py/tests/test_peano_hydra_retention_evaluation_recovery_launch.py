"""Metadata/filesystem fixtures only; scheduler/native/model/network never run.

The temporary admission/preflight objects below are explicitly synthetic byte
join fixtures, not scientific admission. Production admission remains a
separate required CLI check. Historical producer bytes are read from retained
evidence and copied only into temporary fixtures, never altered in place.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from training.peano_hydra import retention_evaluation_recovery_launch as gate

ARCHIVE = ROOT.parents[1] / "artifacts/hydra-retention-pilot-2026-08-30"
CAPTURE = ARCHIVE / "evaluation-checkpoint-collected-01"


def raw_pin(raw):
    return {"bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}


def controller(job="123", *, running=False):
    return ("JobId=" + job + " JobName=" + gate.JOB_NAMES["evaluate"] + " WorkDir=" + str(gate.ROOT)
        + (" JobState=RUNNING Reason=None Priority=1 RunTime=00:00:42" if running else
           " JobState=PENDING Reason=JobHeldUser Priority=0 RunTime=00:00:00")
        + " Dependency=(null) Requeue=0 Account=" + gate.ACCOUNT + " Partition=" + gate.PARTITION
        + " TimeLimit=01:00:00 NumNodes=1 NumCPUs=8 ReqTRES=cpu=8,mem=64G,node=1,gres/gpu=1")


def ledger(bound, job="123"):
    values = [gate._header("evaluate", bound),
        {"kind": "reserve", "reservation": copy.deepcopy(gate.RESERVATIONS["evaluate"]),
         "created_at": "2026-08-31T00:00:00Z", "model_manifest": copy.deepcopy(gate.MODEL_MANIFEST)},
        {"kind": "accepted", "job_id": job},
        {"kind": "held-validated", "snapshot": gate.snapshot(controller(job), "evaluate", job)},
        {"kind": "release-authorized", "job_id": job}, {"kind": "released", "job_id": job}]
    events, previous = [], "0" * 64
    for index, value in enumerate(values):
        event = {"index": index, "previous_sha256": previous, "payload": value}
        event["sha256"] = gate.digest(event)
        events.append(event); previous = event["sha256"]
    return events


class RecoveryReservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.saved = {}
        for name, expected in gate.PRODUCER_FILES.items():
            if name == ".peano-source-provenance.tsv":
                header = json.loads((CAPTURE / "train-ledger.jsonl").read_bytes().splitlines()[0])["payload"]["identity"]
                raw = (header["source_commit"] + "\tfalse\t" + header["synced_at"] + "\n").encode()
            elif name == gate.PRODUCER_MODEL:
                raw = (ARCHIVE / "trained-model-collected-01/model/manifest.json").read_bytes()
            elif name.endswith("-train.jsonl"):
                raw = (CAPTURE / "train-ledger.jsonl").read_bytes()
            elif name.endswith("-evaluate.jsonl"):
                raw = (CAPTURE / "evaluate-ledger.jsonl").read_bytes()
            else:
                raw = (CAPTURE / Path(name).name).read_bytes()
            if raw_pin(raw) != expected:
                raise AssertionError("retained historical fixture pin changed: " + name)
            cls.saved[name] = raw
        cls.training_inputs = json.loads(cls.saved[gate.PRODUCER_MODEL])["training_inputs"]
        cls.goal_proposal = (CAPTURE / "evaluation-plan.json").read_bytes()
        cls.authority = (ROOT / "_deploy/hydra-retention-pilot-v1/authority.json").read_bytes()
        if raw_pin(cls.goal_proposal) != {k: gate.EVALUATION_PLAN[k] for k in ("bytes", "sha256")}:
            raise AssertionError("retained preregistered goal proposal changed")
        if hashlib.sha256(cls.authority).hexdigest() != gate.STANDING_DIRECTIVE_SHA:
            raise AssertionError("actual retained standing directive changed")

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="retention-gate-fixture-", dir="/private/tmp")
        self.addCleanup(self.temporary.cleanup)
        self.scratch = Path(self.temporary.name)
        self.parent = self.scratch / gate.REMOTE_PARENT
        self.root = self.parent / gate.REMOTE_CHILD
        self.root.mkdir(parents=True)
        for name, value in (("ROOT", self.root),):
            self.addCleanup(patch.stopall)
            patch.object(gate, name, value).start()
        patch.object(gate.safe, "ROOT", self.root).start()
        patch.dict(os.environ, {"SCRATCH": str(self.scratch), "USER": "plgnasqret"}, clear=True).start()
        self.scheduler = patch.object(gate.safe, "run", side_effect=AssertionError("real scheduler forbidden")).start()
        self.producer_root = self.parent / gate.PRODUCER_CHILD
        for name, raw in self.saved.items():
            path = self.producer_root / name
            path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        self.build()

    def write(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)
        return {"path": name, **raw_pin(raw)}

    def metadata(self, name, value):
        return self.write(name, gate.canonical(value) + b"\n")

    def build(self, *, admission_status="completed-caller-admission", null_admission=False,
              admission_schema="peano-hydra-preserved-retention-admission-custody-v1"):
        payloads = {}
        def data(name, raw):
            item = self.write(gate.PACKAGE + "/" + name, raw)
            payloads[item["path"]] = {k: item[k] for k in ("bytes", "sha256")}
            return item
        def record(name, value): return data(name, gate.canonical(value) + b"\n")
        admission = record("admission.json", {"schema": admission_schema,
            "status": admission_status, "synthetic_fixture": True, "scientific_admission_not_executed": True})
        candidate = {"schema": "peano-hydra-preserved-retention-artifact-reference-v1",
            "manifest_sha256": gate.MODEL_MANIFEST["sha256"], "training_inputs": copy.deepcopy(self.training_inputs),
            "producer": copy.deepcopy(gate.PRODUCER_REFERENCE),
            "admission_receipt_sha256": None if null_admission else admission["sha256"]}
        locations = {key: {"manifest_path": "synthetic fixture only", "training_inputs": {}, "producer": {},
            "admission_receipt_path": str(root / gate.PACKAGE / "admission.json")}
            for key, root in (("local", gate.LOCAL_EXECUTION), ("helios", gate.REMOTE_EXECUTION))}
        inputs = record("inputs.json", {"schema": "peano-hydra-retention-evaluation-recovery-inputs-v1",
            "profile": gate.PROFILE, "run_id": gate.RUN_ID, "candidate_reference": candidate,
            "locations": locations, "evaluation_plan": copy.deepcopy(gate.EVALUATION_PLAN)})
        preflight = record("preflight.json", {"schema": "peano-hydra-retention-evaluation-recovery-input-check-v1",
            "profile": gate.PROFILE, "run_id": gate.RUN_ID, "inputs_sha256": inputs["sha256"],
            "candidate_reference": candidate, "model_manifest": copy.deepcopy(gate.MODEL_MANIFEST),
            "evaluation_plan": copy.deepcopy(gate.EVALUATION_PLAN),
            "bound_evaluation_plan": {"plan_sha256": "b" * 64, "synthetic_fixture": True},
            "model_weights_loaded": False, "gpu_allocated": False, "training_authorized": False,
            "native_proof_replay_performed": False})
        stage = record("evaluate-request.json", {"schema": "peano-hydra-retention-evaluation-recovery-stage-request-v1",
            "profile": gate.PROFILE, "run_id": gate.RUN_ID, "stage": "evaluate", "inputs": inputs, "preflight": preflight,
            "evaluation_plan_sha256": gate.EVALUATION_PLAN["sha256"], "bound_evaluation_plan_sha256": "b" * 64,
            "model_manifest": copy.deepcopy(gate.MODEL_MANIFEST), "producer_source_commit": gate.PRODUCER_COMMIT,
            "training_job_id": gate.PRODUCER_JOB, "failed_evaluation_job_id": gate.FAILED_EVALUATION_JOB,
            "output": gate.EVALUATION_OUTPUT, "training_authorized": False, "automatic_retry": False,
            "resume": False, "historical_checkpoint_reuse_allowed": False})
        authority = data("authority.json", self.authority)
        data("evaluation-plan.json", self.goal_proposal)
        sources = {}
        for name in gate.REQUIRED_SOURCES:
            item = self.write(name, ("# synthetic source for byte guards only: " + name + "\n").encode())
            sources[name] = {k: item[k] for k in ("bytes", "sha256")}
        self.write(".peano-source-provenance.tsv", ("a" * 40 + "\tfalse\t2026-08-31T00:00:00Z\n").encode())
        self.request = {"schema": gate.REQUEST_SCHEMA, "status": "ready", "profile": gate.PROFILE, "run_id": gate.RUN_ID,
            "source_commit": "a" * 40, "source_files": sources, "payloads": payloads, "payloads_sha256": gate.digest(payloads),
            "scientific_inputs": {"evaluate": stage}, "authority_file": authority, "model": copy.deepcopy(gate.MODEL),
            "model_manifest": copy.deepcopy(gate.MODEL_MANIFEST), "producer": copy.deepcopy(gate.PRODUCER),
            "historical_admission": admission, "evaluation_plan": copy.deepcopy(gate.EVALUATION_PLAN),
            "reservations": copy.deepcopy(gate.RESERVATIONS), "maximum_aggregate_gpu_seconds": 3600,
            "maximum_concurrent_gpus": 1, "automatic_retry": False, "resume": False, "refunds": False,
            "runtime_dependencies": copy.deepcopy(gate.RUNTIME), "training_authorized": False,
            "evaluation_scope": "old-dev32-and-frontier-dev32-at-8-and-16-calls", "historical_checkpoint_reuse_allowed": False}
        self.seal()

    def seal(self):
        descriptor = self.metadata(gate.REQUEST, self.request)
        approval = {"schema": gate.APPROVAL_SCHEMA, "profile": gate.PROFILE, "run_id": gate.RUN_ID,
            "approved": True, "request_file_sha256": descriptor["sha256"],
            "standing_authority_sha256": gate.STANDING_DIRECTIVE_SHA, "authority_quote": gate.AUTHORITY_QUOTE,
            "approval_reference": "SYNTHETIC RESOURCE-GUARD FIXTURE; not an actual experiment approval"}
        self.approval_sha = self.metadata(gate.APPROVAL, approval)["sha256"]

    def bound(self):
        approval, request = gate.validate_metadata(self.approval_sha)
        return gate.identity(approval, request, self.approval_sha)

    def accounting(self, *, train_state="COMPLETED", failure_state="FAILED"):
        return "\n".join("|".join(row) for row in (
            [gate.PRODUCER_JOB, train_state, "0:0", "peano-hydra-retention-pilot-v1-train", str(self.producer_root),
             "120", "8", "64G", gate.ACCOUNT, gate.PARTITION, "plgnasqret"],
            [gate.FAILED_EVALUATION_JOB, failure_state, "2:0", "peano-hydra-retention-pilot-v1-evaluate", str(self.producer_root),
             "60", "8", "64G", gate.ACCOUNT, gate.PARTITION, "plgnasqret"])) + "\n"

    def test_real_files_join_one_new_reservation_without_scientific_execution(self):
        bound = self.bound()
        self.assertEqual(gate.STAGES, ("evaluate",))
        self.assertEqual(bound["producer_sha256"], gate.digest(gate.PRODUCER))
        self.assertEqual(gate.PRODUCER["reserved_gpu_seconds"], 10800)
        self.assertEqual(gate.RESERVATIONS["evaluate"]["seconds"], 3600)
        self.scheduler.assert_not_called()

    def test_no_training_retry_refund_scope_or_old_source(self):
        for key, value in (("training_authorized", True), ("automatic_retry", True), ("resume", True),
                ("refunds", True), ("historical_checkpoint_reuse_allowed", True),
                ("maximum_aggregate_gpu_seconds", 10800), ("source_commit", gate.PRODUCER_COMMIT)):
            changed = copy.deepcopy(self.request); changed[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): gate.validate_request(changed)
        with self.assertRaises(ValueError): gate._stage("train")
        with self.assertRaises(ValueError): gate.validate_metadata(gate.PRODUCER_APPROVAL_SHA)
        self.scheduler.assert_not_called()

    def test_raw_source_change_and_undeclared_payload_rejected(self):
        source = self.root / sorted(gate.REQUIRED_SOURCES)[0]
        raw = source.read_bytes(); source.write_bytes(raw + b"changed")
        with self.assertRaises(ValueError): self.bound()
        source.write_bytes(raw)
        self.write(gate.PACKAGE + "/foreign.json", b"{}")
        with self.assertRaises(ValueError): self.bound()
        self.scheduler.assert_not_called()

    def test_source_symlink_and_closed_admission_changes_rejected(self):
        source = self.root / sorted(gate.REQUIRED_SOURCES)[0]
        target = self.root / "fixture-source-copy"; target.write_bytes(source.read_bytes())
        source.unlink(); source.symlink_to(target)
        with self.assertRaises((ValueError, OSError)): self.bound()
        self.scheduler.assert_not_called()

    def test_failed_and_null_historical_admission_cannot_reserve(self):
        self.build(admission_status="failed")
        with self.assertRaisesRegex(ValueError, "completed historical"): self.bound()
        self.build(null_admission=True)
        with self.assertRaisesRegex(ValueError, "saved candidate changed"): self.bound()
        self.scheduler.assert_not_called()

    def test_bare_inner_admission_cannot_reserve_even_with_matching_raw_pins(self):
        self.build(admission_schema="peano-hydra-preserved-retention-admission-v1",
                   admission_status="passed-corrected-historical-admission")
        with self.assertRaisesRegex(ValueError, "completed historical admission custody"):
            self.bound()
        self.scheduler.assert_not_called()

    def test_new_snapshot_preserves_held_resource_and_clock_barrier(self):
        raw = controller()
        self.assertEqual(gate.snapshot(raw, "evaluate", "123")["allocation_elapsed_seconds"], 0)
        self.assertEqual(gate.snapshot(controller(running=True), "evaluate", "123", running=True)["allocation_elapsed_seconds"], 42)
        for old, new in (("NumCPUs=8", "NumCPUs=16"), ("mem=64G", "mem=128G"), ("gres/gpu=1", "gres/gpu=2"),
                ("Requeue=0", "Requeue=1"), ("TimeLimit=01:00:00", "TimeLimit=02:00:00"),
                ("RunTime=00:00:00", "RunTime=00:00:01"), ("Dependency=(null)", "Dependency=afterok:1")):
            with self.subTest(new=new), self.assertRaises(ValueError): gate.snapshot(raw.replace(old, new), "evaluate", "123")
        with self.assertRaises(ValueError): gate.snapshot(raw + " NumCPUs=8", "evaluate", "123")
        with self.assertRaises(ValueError):
            gate.snapshot(controller(running=True).replace("00:00:42", "01:00:00"), "evaluate", "123", running=True)

    def test_every_open_ledger_prefix_stays_consumed_and_old_jobs_cannot_be_adopted(self):
        bound = self.bound(); events = ledger(bound)
        for count in range(1, 7):
            self.write(gate.LEDGERS["evaluate"], b"".join(gate.canonical(e) + b"\n" for e in events[:count]))
            state = gate.load_ledger("evaluate", bound)
            self.assertEqual(state["gpu_seconds"], 0 if count == 1 else 3600)
            with self.assertRaisesRegex(ValueError, "already opened"):
                gate.launch("evaluate", self.approval_sha, "a" * 40, submit=False)
        for job in (gate.PRODUCER_JOB, gate.FAILED_EVALUATION_JOB):
            self.write(gate.LEDGERS["evaluate"], b"".join(gate.canonical(e) + b"\n" for e in ledger(bound, job)))
            with self.assertRaisesRegex(ValueError, "original spent jobs"): gate.load_ledger("evaluate", bound)
        self.scheduler.assert_not_called()

    def test_historical_hashes_and_both_actual_terminal_rows_required(self):
        self.scheduler.side_effect = lambda command: self.accounting()
        self.assertEqual(gate._producer_completed(), gate.MODEL_MANIFEST)
        command = self.scheduler.call_args.args[0]
        self.assertEqual(command[:6], ["sacct", "-n", "-P", "-X", "-j", "21456251,21457058"])
        self.scheduler.side_effect = lambda command: self.accounting(train_state="FAILED")
        with self.assertRaises(ValueError): gate._producer_completed()
        self.scheduler.side_effect = lambda command: self.accounting(failure_state="COMPLETED")
        with self.assertRaises(ValueError): gate._producer_completed()

    def test_producer_bytes_cannot_be_replaced_or_hardlinked(self):
        name = "logs/hydra-retention-pilot-v1-train.jsonl"
        path = self.producer_root / name
        os.link(path, path.with_suffix(".link"))
        with self.assertRaises(ValueError): gate._producer_completed()
        self.scheduler.assert_not_called()

    def test_uncertain_sbatch_is_already_fully_charged_and_cannot_retry(self):
        def fake(command):
            self.assertEqual(command[0], "sbatch")
            self.assertIn("--hold", command)
            state = gate.load_ledger("evaluate", self.bound())
            self.assertEqual((state["phase"], state["gpu_seconds"]), ("reserve", 3600))
            raise OSError("synthetic uncertain scheduler response")
        self.scheduler.side_effect = fake
        with patch.object(gate, "_queue_history", return_value=set()), \
             patch.object(gate, "_producer_completed", return_value=dict(gate.MODEL_MANIFEST)):
            with self.assertRaises(OSError): gate.launch("evaluate", self.approval_sha, "a" * 40, submit=True)
            with self.assertRaisesRegex(ValueError, "already opened"):
                gate.launch("evaluate", self.approval_sha, "a" * 40, submit=True)
        self.assertEqual(self.scheduler.call_count, 1)

    def run_fake_submit(self, *, change_before_release=False):
        commands = []
        def fake(command):
            commands.append(command)
            if command[0] == "sacct": return self.accounting()
            if command[0] == "sbatch":
                self.assertEqual(gate.load_ledger("evaluate", self.bound())["gpu_seconds"], 3600)
                return "123\n"
            if command == ["scontrol", "-o", "show", "job", "123"]:
                if change_before_release:
                    path = self.root / sorted(gate.REQUIRED_SOURCES)[0]
                    path.write_bytes(path.read_bytes() + b"changed-before-release")
                return controller()
            if command == ["scontrol", "release", "123"]:
                self.assertEqual(gate.load_ledger("evaluate", self.bound())["phase"], "release-authorized")
                return ""
            raise AssertionError("unexpected scheduler fixture command: " + repr(command))
        self.scheduler.side_effect = fake
        with patch.object(gate, "_queue_history", return_value=set()):
            result = gate.launch("evaluate", self.approval_sha, "a" * 40, submit=True)
        return result, commands

    def test_release_requires_durable_new_barriers_and_preserves_original_files(self):
        result, commands = self.run_fake_submit()
        self.assertEqual(result["job_id"], "123")
        self.assertEqual(result["maximum_aggregate_gpu_seconds"], 3600)
        self.assertEqual(gate.load_ledger("evaluate", self.bound())["phase"], "released")
        self.assertEqual(sum(command[0] == "sbatch" for command in commands), 1)
        self.assertEqual(sum(command[:2] == ["scontrol", "release"] for command in commands), 1)
        for name, raw in self.saved.items(): self.assertEqual((self.producer_root / name).read_bytes(), raw)

    def test_changed_source_keeps_accepted_job_held_and_charged(self):
        bound = self.bound()
        with self.assertRaises(ValueError): self.run_fake_submit(change_before_release=True)
        state = gate.load_ledger("evaluate", bound)
        self.assertEqual((state["phase"], state["gpu_seconds"]), ("held-validated", 3600))
        self.assertFalse(any(call.args[0][:2] == ["scontrol", "release"] for call in self.scheduler.call_args_list))


if __name__ == "__main__":
    unittest.main()
