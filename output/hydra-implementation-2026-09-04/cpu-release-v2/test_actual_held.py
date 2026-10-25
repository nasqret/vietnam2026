"""Pure admission of the recorded held response; no transport is executed."""
import ast
import hashlib
import json
from pathlib import Path
import re
import unittest

HERE = Path(__file__).resolve().parent


class RecordedHeldTest(unittest.TestCase):
    def test_actual_pending_range_and_rejections(self):
        receipt = json.loads((HERE.parent / "cpu-fixture-01/held-diagnosis-01/stdout.json").read_bytes())
        held = receipt["files"]["held-inspect.stdout.txt"]
        self.assertEqual(hashlib.sha256(held["text"].encode()).hexdigest(), held["sha256"])
        reservation_file = receipt["files"]["reservation.json"]
        self.assertEqual(hashlib.sha256(reservation_file["text"].encode()).hexdigest(),
                         "0ab2ef94f11b99aa0f0393975ba5c5fac51422c350f2c676b249bca0ebe16e93")
        reservation = json.loads(reservation_file["text"])
        self.assertEqual(reservation["job_id"], "21911629")
        tree = ast.parse((HERE / "cpu_transport.py").read_bytes())
        remote = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "REMOTE" for t in node.targets))
        remote_tree = ast.parse(remote, feature_version=(3, 6))
        pure = ast.Module(body=[node for node in remote_tree.body if isinstance(node, ast.FunctionDef)
                                and node.name in {"need", "fields", "exact_held"}], type_ignores=[])
        self.assertEqual(len(pure.body), 3)
        namespace = {"re": re}
        exec(compile(pure, "<pure-held-admission-functions-only>", "exec"), namespace)
        admit = namespace["exact_held"]
        self.assertEqual(admit(held["text"], reservation)["NumNodes"], "1-1")
        self.assertEqual(admit(held["text"].replace("NumNodes=1-1", "NumNodes=1"), reservation)["NumNodes"], "1")
        for before, after in (("NumNodes=1-1", "NumNodes=1-2"),
                              ("mem=4G", "mem=8G"),
                              ("billing=2", "billing=2,gres/gpu=1")):
            with self.subTest(after=after), self.assertRaises(ValueError):
                admit(held["text"].replace(before, after), reservation)


if __name__ == "__main__":
    unittest.main()
