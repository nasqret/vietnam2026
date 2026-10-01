"""Target binding, trust boundaries, and a small real HA round trip.

Run with the campaign process supervisor. Integration results for the other
frozen leaves live in the bounded pilot receipts, not mocked theorem claims.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_sqrt2_power_pilot as pilot
from sqrt2_power_campaign_spec import PILOT
from sqrt2_power_native import BASIS_NAMES, Basis, closed_formula
from sqrt2_power_pilot_contracts import canonical, contracts
from peano_lab.library.proof_bundle import encode_formula


class FrozenContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rows = contracts()

    def test_exact_twelve_planning_links(self):
        self.assertEqual([r["pilot_id"] for r in self.rows], [p["id"] for p in PILOT])
        for row, parent in zip(self.rows, PILOT):
            self.assertEqual(row["parent"], parent["parent"])
            self.assertEqual(row["pilot_contract"], parent["contract"])
            self.assertEqual(row["pilot_contract_sha256"], sha256(canonical(parent)).hexdigest())
            self.assertIs(row["closes_IR_parent"], False)

    def test_hashes_bind_original_formula_and_complete_contract(self):
        for row in self.rows:
            original = deepcopy(row)
            digest = original.pop("contract_sha256")
            self.assertEqual(digest, sha256(canonical(original)).hexdigest())
            if row["dispatchable"]:
                ast = encode_formula(closed_formula(row["source"]))
                self.assertEqual(row["statement_ast"], ast)
                self.assertEqual(row["statement_ast_sha256"], sha256(canonical(ast)).hexdigest())
            else:
                self.assertIsNone(row["source"])
                self.assertIsNone(row["statement_ast_sha256"])
                self.assertTrue(row["reason"])

    def test_supporting_identity_is_not_its_parent_contract(self):
        full = {r["pilot_id"] for r in self.rows if r["coverage"] == "full_pilot_contract"}
        partial = {r["pilot_id"] for r in self.rows if r["coverage"] == "supporting_subleaf_only"}
        self.assertEqual(full, {"P01", "P05", "P07"})
        self.assertEqual(partial, {"P02", "P03", "P06", "P08", "P11"})
        for row in self.rows:
            if row["pilot_id"] in partial:
                self.assertNotEqual(row["leaf_id"], row["pilot_id"])

    def test_only_fixed_arithmetic_basis_is_exportable(self):
        basic = Basis()
        for row in self.rows:
            premises = row["allowed_external_premises"]
            self.assertEqual([p["name"] for p in premises], sorted(BASIS_NAMES))
            for premise in premises:
                self.assertEqual(premise["source"], basic.specs[premise["name"]][1])
                self.assertEqual(premise["source_file_sha256"], basic.source_sha256)
                ast = encode_formula(closed_formula(premise["source"]))
                self.assertEqual(premise["statement_ast_sha256"], sha256(canonical(ast)).hexdigest())

    def test_free_variable_cannot_be_frozen(self):
        with self.assertRaises(ValueError):
            closed_formula("forall x. x=y")

    def test_non_allowlisted_theorem_is_not_available(self):
        with self.assertRaises(ValueError):
            Basis().get("IR072")

    def test_unknown_pilot_rejected(self):
        with self.assertRaises(ValueError):
            pilot.by_id("IR072")

    def test_unelaborated_worker_has_no_certificate(self):
        result = pilot.native_worker("P12")
        self.assertEqual(result["status"], "unelaborated")
        self.assertNotIn("bundle", result)
        self.assertEqual(result["IR_parents_closed"], 0)


class ActualReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.value = pilot.native_worker("P05")
        if cls.value["status"] != "native_generated":
            raise AssertionError(cls.value)

    def test_same_canonical_bytes_recheck_against_original(self):
        result = pilot.replay_worker("P05", self.value)
        self.assertEqual(result["status"], "fresh_ordinary_HA_checked")
        # This unit call is in-process. The pilot controller, not this test,
        # supplies the separate-process isolation denoted by that receipt.
        self.assertTrue(result["original_target_checked"])
        self.assertTrue(result["forged_body_rejected"])
        self.assertTrue(result["false_target_rejected"])
        self.assertTrue(result["empty_context"])
        self.assertFalse(result["classical"])
        self.assertFalse(result["independent_lean_checked"])
        self.assertEqual(result["IR_parents_closed"], 0)

    def mutate(self, change):
        value = deepcopy(self.value)
        change(value)
        with self.assertRaises(ValueError):
            pilot.replay_worker("P05", value)

    def test_changed_source_pin_rejected(self):
        self.mutate(lambda v: v["source_pins"].update({"forged.py": {"sha256": "0" * 64}}))

    def test_changed_contract_rejected(self):
        self.mutate(lambda v: v.update(contract_sha256="0" * 64))

    def test_solver_status_cannot_replace_native_proof(self):
        self.mutate(lambda v: v.update(status="unsat"))

    def test_different_pilot_cannot_receive_this_proof(self):
        self.mutate(lambda v: v.update(pilot_id="P07"))

    def test_changed_bytes_rejected_even_if_json_equivalent(self):
        self.mutate(lambda v: v.update(bundle=v["bundle"] + " "))

    def test_forged_byte_hash_rejected(self):
        self.mutate(lambda v: v.update(bundle_sha256="0" * 64))

    def test_wrong_original_goal_rejected_even_with_rehashed_payload(self):
        def change(value):
            # The canonical wire format is inert JSON. The decoder must bind
            # the separately encoded original target, not just trust a digest.
            data = json.loads(value["bundle"])
            data[2] = encode_formula(closed_formula("0=0"))
            value["bundle"] = json.dumps(data, ensure_ascii=True, allow_nan=False,
                                         separators=(",", ":")) + "\n"
            value["bundle_sha256"] = sha256(value["bundle"].encode()).hexdigest()
        self.mutate(change)


class ProcessBoundaryTests(unittest.TestCase):
    def test_only_clean_natural_exit_is_success(self):
        good = dict(reason="exited", returncode=0, output_truncated=False)
        self.assertTrue(pilot.successful(good))
        for changes in (dict(reason="cpu_limit"), dict(reason="rss_limit"),
                        dict(returncode=True), dict(returncode=1),
                        dict(output_truncated=True)):
            self.assertFalse(pilot.successful(dict(good, **changes)))
        self.assertFalse(pilot.successful(None))

    def test_canonical_decoder_and_package_are_pinned(self):
        pins = pilot.pins()
        for name in ("__init__.py", "proof_bundle.py"):
            self.assertIn("peano-lab/py/peano_lab/library/" + name, pins)

    def test_insufficient_wall_budget_returns_exhaustion_without_spawning(self):
        budget = pilot.LeafBudget(time.monotonic() + 7)
        with patch.object(pilot, "runtime", side_effect=AssertionError("must not spawn")):
            self.assertIsNone(budget.run(("unused",), cpu=8, wall=12))
        self.assertEqual(budget.reserved_cpu, 0)

    def test_summary_preserves_supervisor_raw_output_measurements(self):
        record = dict(stdout="retained", stdout_bytes=999,
                      stdout_sha256="a"*64, output_truncated=True,
                      raw_output_base64="/w==")
        result = pilot.concise_process(record)
        self.assertNotIn("stdout", result)
        self.assertEqual(result["stdout_bytes"], 999)
        self.assertEqual(result["stdout_sha256"], "a"*64)
        self.assertEqual(result["raw_output_base64"], "/w==")

    def test_expired_controller_cannot_run_body(self):
        with self.assertRaises(pilot.ControllerDeadline):
            with pilot.controller_deadline(time.monotonic()-1):
                self.fail("expired controller ran")

    def test_controller_restores_alarm_handler_and_timer(self):
        import signal
        before = signal.getsignal(signal.SIGALRM)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))
        with pilot.controller_deadline(time.monotonic()+5):
            self.assertGreater(signal.getitimer(signal.ITIMER_REAL)[0], 0)
        self.assertEqual(signal.getsignal(signal.SIGALRM), before)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0.0, 0.0))


if __name__ == "__main__":
    unittest.main()
