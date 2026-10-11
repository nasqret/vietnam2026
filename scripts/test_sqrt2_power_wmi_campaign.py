"""Dependency-free AP091 routing controls; no network or proof construction."""
import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import run_sqrt2_power_wmi_next as campaign


class WmiCampaignTests(unittest.TestCase):
    def fixture(self):
        cost={key:0 for key in campaign.PREPARATION_COST_FIELDS}
        cost.update(status='prepared',original_native_curried_goal_checked=True,
            full_dependency_closed_theorem_checked=False)
        return dict(schema='sqrt2-power-wmi-AP091-v1',case='AP091',phase='prepare',
            job_id=campaign.PREPARATION_JOB,source_snapshot_sha256=campaign.PREPARATION_SNAPSHOT,
            status='prepared_not_theorem_checked',full_attempt_started=False,cost=cost)

    def test_preflight_gate_preserves_every_comparison_field(self):
        report=self.fixture()
        self.assertEqual(campaign.preparation_cost(report),
            {key:report['cost'][key] for key in campaign.PREPARATION_COST_FIELDS})

    def test_wrong_job_snapshot_case_phase_and_status_are_rejected(self):
        for key,value in (('job_id','268413'),('source_snapshot_sha256','0'*64),('case','AP090'),
                ('phase','full'),('status','metadata_only'),('full_attempt_started',True)):
            report=self.fixture();report[key]=value
            with self.assertRaises(ValueError):campaign.preparation_cost(report)

    def test_metadata_only_or_claimed_closed_theorem_is_not_native_preflight(self):
        for key,value in (('status','metadata_only'),('original_native_curried_goal_checked',False),
                ('original_native_curried_goal_checked',1),('full_dependency_closed_theorem_checked',True)):
            report=self.fixture();report['cost'][key]=value
            with self.assertRaises(ValueError):campaign.preparation_cost(report)

    def test_every_missing_cost_field_is_rejected(self):
        for key in campaign.PREPARATION_COST_FIELDS:
            report=self.fixture();del report['cost'][key]
            with self.assertRaises(ValueError):campaign.preparation_cost(report)

    def test_gate_does_not_mutate_evidence(self):
        report=self.fixture();before=copy.deepcopy(report)
        campaign.preparation_cost(report)
        self.assertEqual(report,before)

    def test_missing_preparation_does_not_launch_a_process(self):
        with patch.object(Path,'read_bytes',side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):campaign.read_preparation(None)

    def test_submission_uses_both_authorized_queues_and_success_only_dependency(self):
        raw=(campaign.ROOT/'scripts/submit_sqrt2_power_wmi_campaign.sh').read_text()
        self.assertIn('--partition=cpu,cpu_idle',raw)
        self.assertIn('--dependency="afterok:$prior" --kill-on-invalid-dep=yes',raw)
        self.assertIn('[ "$prior" = '+campaign.PREPARATION_JOB+' ]',raw)
        self.assertIn(campaign.PREPARATION_SNAPSHOT,raw)
        self.assertEqual(raw.count('sbatch --hold --parsable'),1)
        self.assertLess(raw.index('afterok-job-id.txt'),raw.index('sbatch --hold --parsable'))
        self.assertLess(raw.index('job-id.txt"\n'),raw.index('scontrol release'))
        self.assertIn('--no-requeue',raw)


if __name__=='__main__':unittest.main()
