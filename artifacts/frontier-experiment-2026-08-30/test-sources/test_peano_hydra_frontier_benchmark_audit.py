"""Small exposure fixtures; no model, epoch regeneration or native QED claim."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT), str(ROOT / 'peano-lab/py')]
from training.peano_hydra import frontier_benchmark_audit as audit


class ExposureAuditTests(unittest.TestCase):
    def inventory(self, rows, *, gap='unknown base pretraining'):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'exposure.jsonl'
            raw = b''.join(audit.canonical_bytes(row) + b'\n' for row in rows)
            path.write_bytes(raw)
            return audit.build_exposure_index([{'path': str(path), 'format': 'jsonl',
                'role': 'test-fixture', 'anchor_origin': 'synthetic-test-only',
                'expected_sha256': hashlib.sha256(raw).hexdigest()}], coverage_gaps=[gap])

    def test_alpha_renamed_root_quarantines_whole_family(self):
        exposure = self.inventory([{'theorem': 'forall x. x = x'}])
        goals = [{'id': 'hit', 'family': 'f', 'statement': 'forall y. y = y'},
                 {'id': 'other', 'family': 'f', 'statement': 'forall y. y + 1 = 1 + y'}]
        result = audit.audit_candidates(exposure, goals, candidate_identity={'synthetic': True})
        self.assertEqual(result['families'][0]['status'], 'quarantine-exact-exposure')
        self.assertTrue(result['families'][0]['whole_family_quarantined'])
        self.assertFalse(result['claims']['sealed_benchmark'])

    def test_same_logical_template_is_review_flag_not_semantic_equivalence(self):
        exposure = self.inventory([{'statement': 'forall a n. ~(exists q. n = a * q) -> forall q. ~(n = a * q)'}])
        goal = {'id': 'negative', 'family': 'new-name',
                'statement': 'forall n. ~(exists x. x + 2 = n) -> forall x. ~(x + 2 = n)'}
        result = audit.audit_candidates(exposure, [goal], candidate_identity={})
        self.assertEqual(result['families'][0]['status'], 'quarantine-template-review')
        self.assertFalse(result['limits']['complete_semantic_equivalence_checked'])

    def test_after_state_closed_target_exposure_is_not_lost(self):
        exposure = self.inventory([{'goals_before': ['h : 0 = 0 ⊢ 1 = 1'],
                                   'goals_after': ['⊢ forall n. n + 0 = n']}])
        goal = {'id': 'a', 'family': 'f', 'statement': 'forall m. m + 0 = m'}
        result = audit.audit_candidates(exposure, [goal], candidate_identity={})
        self.assertIn('closed_targets', result['families'][0]['goals'][0]['matches'])

    def test_complete_reference_trace_detects_full_state_exposure(self):
        target = '∀ x. x = x'
        source = self.inventory([{'goals_before': ['n : ℕ ⊢ n = n']}])
        candidates = [{'id': 'a', 'family': 'f', 'statement': target}]
        rows = [{'theorem_name': 'a', 'step': 1, 'goals_before': ['⊢ ' + target],
                 'goals_after': ['n : ℕ ⊢ n = n']},
                {'theorem_name': 'a', 'step': 2, 'goals_before': ['n : ℕ ⊢ n = n'], 'goals_after': []}]
        result = audit.audit_candidates(source, candidates, candidate_identity={},
                                        reference_records=rows, reference_expected_counts={'a': 2})
        self.assertTrue(result['reference_state_coverage_complete'])
        self.assertEqual(result['families'][0]['status'], 'quarantine-exact-exposure')
        with self.assertRaises(audit.BenchmarkAuditError):
            audit.audit_candidates(source, candidates, candidate_identity={},
                                   reference_records=rows[:1], reference_expected_counts={'a': 2})

    def test_goal_observation_alone_does_not_claim_complete_reference(self):
        source = self.inventory([{'theorem': '1 = 1'}])
        result = audit.audit_candidates(source, [{'id': 'a', 'family': 'f', 'statement': '0 = 0'}],
            candidate_identity={}, reference_records=[{'theorem_name': 'a', 'goals_before': ['⊢ 0 = 0']}])
        self.assertFalse(result['reference_state_coverage_complete'])
        self.assertEqual(result['coverage_gaps'], ['unknown base pretraining'])

    def test_open_targets_not_incorrectly_claimed_closed(self):
        source = self.inventory([{'goals_before': ['x : ℕ ⊢ x = x']}])
        self.assertEqual(source['features']['closed_targets'], {})
        self.assertEqual(source['counts']['open_target_observations'], 1)

    def test_raw_anchor_mismatch_and_duplicate_json_keys_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.json'
            path.write_bytes(b'{"x":1,"x":2}')
            with self.assertRaises(audit.BenchmarkAuditError):
                audit.read_file(path, '0' * 64)
            with self.assertRaises(audit.BenchmarkAuditError):
                audit.build_exposure_index([{'path': str(path), 'format': 'json',
                    'role': 'test', 'anchor_origin': 'fixture'}], coverage_gaps=[])

    def test_out_of_profile_exposure_stays_visible_as_gap(self):
        source = self.inventory([{'statement': '999999999 = 999999999'}])
        self.assertEqual(sum(source['parse_gaps'].values()), 1)
        self.assertFalse(source['claims']['all_historical_exposures_known'])

    def test_bottom_under_distinct_context_is_reported_without_forging_dependency(self):
        source = self.inventory([{'goals_before': ['h : 0 = 1 ⊢ ⊥']}])
        goal = {'id': 'a', 'family': 'negative', 'statement': '~(0 = 1)'}
        rows = [{'theorem_name': 'a', 'step': 1, 'goals_before': ['⊢ ¬0 = 1'],
                 'goals_after': ['other : 0 = 1 ⊢ ⊥']},
                {'theorem_name': 'a', 'step': 2, 'goals_before': ['other : 0 = 1 ⊢ ⊥'],
                 'goals_after': []}]
        result = audit.audit_candidates(source, [goal], candidate_identity={'synthetic': True},
            reference_records=rows, reference_expected_counts={'a': 2})
        self.assertEqual(result['families'][0]['status'], 'no-detected-overlap-in-declared-sources')
        self.assertTrue(result['families'][0]['shared_primitive_correlations'])
        self.assertEqual(audit.audit_summary(result)['status'], 'no-detected-overlap-in-declared-sources')

    def test_receipt_validator_rederives_status_even_after_digest_recomputed(self):
        source = self.inventory([{'theorem': '0 = 0'}])
        result = audit.audit_candidates(source, [{'id': 'a', 'family': 'f', 'statement': '0 = 0'}],
                                        candidate_identity={})
        audit.validate_audit_record(result)
        result['families'][0]['status'] = 'no-detected-overlap-in-declared-sources'
        result['audit_sha256'] = audit.digest({k: v for k, v in result.items() if k != 'audit_sha256'})
        with self.assertRaises(audit.BenchmarkAuditError):
            audit.validate_audit_record(result)

    def test_huge_unparsed_formula_with_same_signature_blocks(self):
        source = self.inventory([{'statement': '999999999 = 999999999'}])
        result = audit.audit_candidates(source, [{'id': 'a', 'family': 'f', 'statement': '0 = 0'}],
                                        candidate_identity={})
        summary = audit.audit_summary(result)
        self.assertEqual(summary['status'], 'blocked')
        self.assertIn('unparsed_exposure_cannot_be_excluded_by_necessary_logical_counts',
                      summary['blocking_coverage_gaps'])

    def test_logical_count_filter_preserves_native_sugar(self):
        self.assertEqual(audit.logical_count_signature('forall x. ~(x <= 1) /\\ (x = 0 \\/ x = 1)'),
                         audit.logical_count_signature('forall x. ((exists k. k + x = 1) -> bot) ∧ (x = 0 ∨ x = 1)'))

    def test_logical_count_filter_does_not_confuse_primed_identifiers_with_bottom(self):
        self.assertEqual(audit.logical_count_signature("forall bot' false'. bot' = false'"),
                         audit.logical_count_signature('forall x y. x = y'))
        self.assertEqual(audit.logical_count_signature('forall αbot. αbot = αbot'),
                         audit.logical_count_signature('forall x. x = x'))


if __name__ == '__main__':
    unittest.main()
