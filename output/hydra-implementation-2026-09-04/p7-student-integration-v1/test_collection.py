"""Synthetic transport-only fixtures; no teacher/model/native proof execution."""
import copy
from pathlib import Path
import tempfile
import unittest

import collect_continuations as subject


class CollectionTests(unittest.TestCase):
    def fixture(self):
        states = [{"id": f"{index:064x}"} for index in range(32)]
        prefix = "003-" + states[3]["id"][:16]
        row = {"index": 3, "state_id": states[3]["id"], "split": "train",
            "selection_sha256": subject.SELECTION_SHA, "outcome": "proved",
            "positive_distillation_eligible": True,
            "successful_native_record": prefix + "/proposal-0/result.json",
            "native_execution_record": prefix + "/proposal-0/execution.json",
            "teacher_proposal_record": prefix + "/teacher-proposal.json",
            "successful_native_sha256": "a" * 64,
            "native_execution_sha256": "b" * 64,
            "teacher_proposal_sha256": "c" * 64}
        return states, {"schema": "hydra-teacher-positive-continuations-v1",
            "training_performed": False, "positive_count": 1, "records": [row]}

    def test_only_exact_five_records_are_nominated(self):
        states, positive = self.fixture()
        names = subject.closure(positive, states)
        self.assertEqual(len(names), 5)
        self.assertEqual(sum(value is None for value in names.values()), 2)
        self.assertTrue(all(name.startswith("003-" + states[3]["id"][:16] + "/") for name in names))

    def test_zero_yield_has_no_proof_files(self):
        states, positive = self.fixture()
        positive.update(positive_count=0, records=[])
        self.assertEqual(subject.closure(positive, states), {})

    def test_paths_cannot_escape(self):
        states, positive = self.fixture()
        for name in ("/tmp/result.json", "../result.json", "003-state/../../result.json"):
            altered = copy.deepcopy(positive)
            altered["records"][0]["successful_native_record"] = name
            with self.assertRaises(ValueError):
                subject.closure(altered, states)

    def test_duplicate_index_rejected(self):
        states, positive = self.fixture()
        positive["records"].append(copy.deepcopy(positive["records"][0]))
        positive["positive_count"] = 2
        with self.assertRaises(ValueError):
            subject.closure(positive, states)

    def test_wrong_count_or_state_rejected(self):
        states, positive = self.fixture()
        for key, value in (("positive_count", 0), ("positive_count", True)):
            altered = copy.deepcopy(positive)
            altered[key] = value
            with self.assertRaises(ValueError):
                subject.closure(altered, states)
        positive["records"][0]["state_id"] = states[4]["id"]
        with self.assertRaises(ValueError):
            subject.closure(positive, states)

    def test_prefix_cannot_alias_successful_record(self):
        states, positive = self.fixture()
        positive["records"][0]["successful_native_record"] = "003-" + states[3]["id"][:16] + "/prefix/result.json"
        with self.assertRaises(ValueError):
            subject.closure(positive, states)

    def test_regular_bounded_exact_files_only(self):
        with tempfile.TemporaryDirectory(prefix="hydra-copy-test-") as temporary:
            directory = Path(temporary).resolve()
            target = directory / "record.json"
            target.write_bytes(b"{}\n")
            self.assertEqual(subject.ordinary(target, 3, subject.digest(b"{}\n")), b"{}\n")
            with self.assertRaises(ValueError):
                subject.ordinary(target, 2)
            with self.assertRaises(ValueError):
                subject.ordinary(target, 3, "0" * 64)
            link = directory / "linked.json"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                subject.ordinary(link)

    def test_duplicate_and_nonfinite_json_rejected(self):
        for raw in (b'{"a":1,"a":2}', b'{"a":NaN}'):
            with self.assertRaises(ValueError):
                subject.strict(raw)


if __name__ == "__main__":
    unittest.main()
