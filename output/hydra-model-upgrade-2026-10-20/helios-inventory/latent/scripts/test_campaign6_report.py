"""Meaningful receipt/coverage regressions. Execute only under CPU SLURM."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

if not os.environ.get("SLURM_JOB_ID"):
    raise SystemExit("Reporting tests require SLURM")
spec = importlib.util.spec_from_file_location("report", Path(__file__).with_name("campaign6_report.py"))
report = importlib.util.module_from_spec(spec)
spec.loader.exec_module(report)


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.directory = self.root / "artifacts/campaign6/runs/fixture"
        self.directory.mkdir(parents=True)
        self.planned = {"run_id": "fixture", "cluster": "helios", "arm": "qwen_random", "seed": 11,
                        "job_id": "123", "directory": str(self.directory), "max_steps": 2048,
                        "dispatch_file": "artifacts/campaign6/task-status/fixture.json"}

    def tearDown(self):
        self.temporary.cleanup()

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value) + "\n")
        return path

    def status(self, **changes):
        state = {"run_id": "fixture", "arm": "qwen_random", "seed": 11, "cluster": "helios",
                 "state": "running", "step": 512, "max_steps": 2048, "smoke": False,
                 "metrics": {"train_loss": 0.5}, "history": []}
        state.update(changes)
        self.write("artifacts/campaign6/runs/fixture/status.json", state)
        return state

    def row(self, scheduler=None):
        return report.training_row(self.planned, self.root, "helios", scheduler or {}, {})

    def test_scheduler_completion_is_not_training_completion(self):
        row = self.row({"123": {"state": "COMPLETED"}})
        self.assertEqual(row["state"], "scheduler_completed_receipt_missing")
        self.status(state="completed", step=512)
        self.assertEqual(self.row()["state"], "producer_completed_unvalidated")
        self.status(state="completed", step=2048)
        self.assertEqual(self.row()["state"], "completed")

    def test_terminal_dispatch_overrides_stale_running_trainer(self):
        self.status()
        self.write(self.planned["dispatch_file"], {"run_id": "fixture", "state": "failed_exception"})
        self.assertEqual(self.row({"123": {"state": "RUNNING"}})["state"], "failed_exception")

    def test_identity_mismatch_does_not_publish_another_run(self):
        self.status(seed=47)
        row = self.row()
        self.assertEqual(row["state"], "receipt_invalid")
        self.assertTrue(any("seed differs" in warning for warning in row["warnings"]))

    def test_full_history_uses_observed_status_and_milestone_flags(self):
        self.status(step=512)
        rows = [
            {"step": 100, "train_loss": 1.0, "val_loss": 9.0, "proof_acceptance": .5},
            {"step": 256, "validation": True, "val_loss": .8, "proof_acceptance": .5},
            {"step": 512, "proof_validation": True, "proof_total": 64, "proof_attempted": 30},
            {"step": 600, "train_loss": .4},
        ]
        (self.directory / "metrics.jsonl").write_text("".join(json.dumps(row) + "\n" for row in rows) + '{"step": 601')
        self.write("artifacts/campaign6/runs/fixture/validation-proof-step-512/summary.json", {
            "status": "budget_limited", "proof_counts": {"selected": 64, "attempted": 30,
                "autonomous_python_kernel_proof": 6, "wall_budget_limited": 35}})
        row = self.row()
        self.assertEqual([p["step"] for p in row["history"]], [100, 256, 512])
        self.assertNotIn("val_loss", row["history"][0])
        self.assertNotIn("proof", row["history"][1])
        self.assertEqual(row["history"][2]["proof"]["solved"], 6)
        self.assertFalse(row["history"][2]["proof"]["complete"])

    def test_complete_coverage_cannot_be_inferred_from_partial_pair(self):
        entries = [{"path": "aggregate.json", "report": {"evaluations": [{"suite_id": "missing"}],
            "comparisons": [{"comparison_id": "partial", "complete": False, "paired": True},
                            {"comparison_id": "unpaired", "complete": True, "paired": False},
                            {"comparison_id": "selection_incomplete", "complete": True, "paired": True, "primary_comparison_eligible": False},
                            {"comparison_id": "good", "complete": True, "paired": True, "primary_comparison_eligible": True, "p_value": .001}]}}]
        evaluations, comparisons = report.normalized_evaluations(entries)
        self.assertEqual(len(evaluations), 1)
        self.assertEqual([row["comparison_id"] for row in comparisons], ["good"])
        self.assertNotIn("p_value", comparisons[0])

    def test_missing_evaluation_stays_missing(self):
        entries, warnings = report.evaluation_reports(["artifacts/campaign6/no-report.json"], self.root, {})
        self.assertEqual(entries[0]["state"], "missing")
        self.assertEqual(report.normalized_evaluations(entries), ([], []))
        self.assertEqual(warnings, [])

    def test_paths_cannot_escape_project(self):
        for path in ("../private", "/etc/passwd"):
            with self.assertRaises(ValueError):
                report.inside(self.root, path)

    def test_offline_embedding_escapes_script_end_and_keeps_exact_data(self):
        output = self.root / "dashboard"
        template = self.root / "template.html"
        template.write_text('<script type="application/json">__LATENT_WEEKEND_SNAPSHOT__</script>')
        value = {"format": report.FORMAT, "note": "</script><script>alert(1)</script>", "count": None}
        report.publish(value, output, template)
        html = (output / "index.html").read_text()
        self.assertEqual(html.count("</script>"), 1)
        payload = html.removeprefix('<script type="application/json">').removesuffix("</script>")
        self.assertEqual(json.loads(payload), value)
        self.assertEqual(json.loads((output / "snapshot.json").read_text()), value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
