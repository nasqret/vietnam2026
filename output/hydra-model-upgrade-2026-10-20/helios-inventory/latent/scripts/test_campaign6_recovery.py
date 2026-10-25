"""Synthetic recovery tests. Run under WMI/Helios SLURM only."""
import json
import os
from pathlib import Path
import tempfile
import unittest

from campaign6_recovery import (archive_uncommitted_evaluations, assess_milestones,
                             digest, inventory)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        if not os.environ.get("SLURM_JOB_ID"):
            raise RuntimeError("Tests require SLURM")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.run = Path(self.temporary.name)
        (self.run / "last.pt").write_bytes(b"synthetic committed checkpoint")
        self.identity = {"arm": "qwen_random", "seed": 11, "source": "fixture", "device": "fixture"}
        self.saved = {"identity": self.identity, "step": 7, "best": None}

    def recover(self, **changes):
        values = dict(saved=self.saved, checkpoint_sha256=digest(self.run / "last.pt"),
                      expected_identity=self.identity, expected_total_steps=16)
        values.update(changes)
        return archive_uncommitted_evaluations(self.run, **values)

    def test_move_only_uncommitted_and_preserve_hashes(self):
        for step in (4, 7, 8):
            directory = self.run / f"validation-proof-step-{step}"
            directory.mkdir()
            (directory / "proofs.jsonl").write_text(f"step {step}\n")
            (self.run / f"evaluation-step-{step}.pt").write_text(f"snapshot {step}")
        (self.run / "evaluation-step-9.pt.tmp").write_text("partial tensor")
        original = inventory(self.run / "validation-proof-step-8")
        record = self.recover()
        self.assertEqual(record["state"], "completed")
        self.assertEqual({item["name"] for item in record["archived"]},
                         {"validation-proof-step-8", "evaluation-step-8.pt", "evaluation-step-9.pt.tmp"})
        self.assertEqual(inventory(self.run / record["archive"] / "validation-proof-step-8"), original)
        self.assertTrue((self.run / "validation-proof-step-7").is_dir())
        self.assertTrue((self.run / "evaluation-step-4.pt").is_file())
        self.assertFalse((self.run / "validation-proof-step-8").exists())
        self.assertIsNone(self.recover()["archive"])

    def test_identity_mismatch_does_not_move_evidence(self):
        (self.run / "evaluation-step-8.pt").write_text("uncommitted")
        with self.assertRaisesRegex(ValueError, "identity"):
            self.recover(expected_identity={**self.identity, "seed": 29})
        self.assertTrue((self.run / "evaluation-step-8.pt").exists())

    def test_changed_checkpoint_rejected(self):
        with self.assertRaisesRegex(ValueError, "last.pt changed"):
            self.recover(checkpoint_sha256="0" * 64)

    def test_newer_selected_state_rejected(self):
        with self.assertRaisesRegex(ValueError, "newer"):
            self.recover(saved={**self.saved, "best": {"step": 8, "identity": self.identity}})

    def test_symlink_not_followed(self):
        (self.run / "evaluation-step-8.pt").symlink_to(self.run / "last.pt")
        with self.assertRaisesRegex(ValueError, "symlink"):
            self.recover()

    def test_incomplete_prior_recovery_fails_closed(self):
        archive = self.run / "recovery-archive-fixture"
        archive.mkdir()
        (archive / "recovery.json").write_text(json.dumps({"state": "prepared"}))
        with self.assertRaisesRegex(ValueError, "earlier recovery"):
            self.recover()

    def assessment(self):
        return assess_milestones(self.run, proof_eval_steps=[4, 8, 16], attained_step=16,
                                 expected_roster=["task-a"], expected_policy={"kind": "fixed", "depth": 2})

    def test_skipped_milestone_remains_ineligible(self):
        (self.run / "metrics.jsonl").write_text(json.dumps({
            "step": 8, "evaluation_skipped": "external-stop-or-training-budget"
        }) + "\n")
        result = self.assessment()
        self.assertFalse(result["selection_schedule_complete"])
        self.assertEqual(result["eligible_steps"], [])
        self.assertEqual(result["milestones"][1]["state"], "ineligible_or_skipped")

    def test_claimed_eligibility_without_evidence_rejected(self):
        (self.run / "metrics.jsonl").write_text(json.dumps({
            "step": 8, "proof_selection_eligible": True
        }) + "\n")
        with self.assertRaisesRegex(ValueError, "evidence files"):
            self.assessment()

    def test_complete_metadata_and_byte_bindings(self):
        policy = {"kind": "fixed", "depth": 2}
        points = []
        for step in (4, 8, 16):
            directory = self.run / f"validation-proof-step-{step}"
            directory.mkdir()
            proofs = directory / "proofs.jsonl"
            proofs.write_text("synthetic bytes; not a native proof\n")
            snapshot = self.run / f"evaluation-step-{step}.pt"
            snapshot.write_text(f"synthetic snapshot {step}")
            candidate = {"complete": True, "step": step, "selected": 1,
                         "selection_policy": policy, "proofs_sha256": digest(proofs),
                         "evaluated_checkpoint_step": step,
                         "evaluated_checkpoint_sha256": digest(snapshot)}
            summary = {"status": "completed", "split": "dev", "test_parsed": False,
                       "validation_used_for_selection": True, "proof_task_ids": ["task-a"],
                       "proof_counts": {"selected": 1, "attempted": 1, "recorded": 1,
                                        "wall_budget_limited": 0},
                       "proofs_sha256": digest(proofs),
                       "provenance": {"policy": policy, "checkpoint_step": step,
                                      "checkpoint_role": "current-evaluation-snapshot",
                                      "checkpoint_sha256": digest(snapshot)}}
            (directory / "summary.json").write_text(json.dumps(summary))
            points.append({"step": step, "proof_selection_eligible": True,
                           "proof_selection_candidate": candidate})
        (self.run / "metrics.jsonl").write_text("".join(json.dumps(point) + "\n" for point in points))
        self.assertTrue(self.assessment()["selection_schedule_complete"])
        (self.run / "evaluation-step-8.pt").write_text("changed bytes")
        with self.assertRaisesRegex(ValueError, "binding differs"):
            self.assessment()


if __name__ == "__main__":
    if not os.environ.get("SLURM_JOB_ID"):
        raise SystemExit("Tests require WMI/Helios SLURM")
    unittest.main()
