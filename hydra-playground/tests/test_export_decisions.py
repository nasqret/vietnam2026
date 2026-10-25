"""Schema-only evidence fixtures: no native parser, kernel, solver or model."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
import export_decisions as exporter


class TextIdentity:
    """Test adapter only; production uses original native closed AST identity."""
    def __call__(self,text):return hashlib.sha256(text.encode()).hexdigest()
    def goal_identities(self,goal):return [self(goal.split("⊢",1)[1].strip())]


def reservation(theorem="S 0 = 0"):
    return exporter.Reservation({"frozen":True,"reservation":{
        "training_allowed":False,"retrieval_allowed":False,
        "teacher_labeling_for_training_allowed":False,"distillation_allowed":False},
        "cases":[{"id":"reserved","theorem":theorem,"family":"reserved_family",
                  "template_subfamily":"reserved_template"}]},TextIdentity())


def fixture():
    theorem = "0 = 0 ∧ 0 = 0"
    goals = [["⊢ "+theorem],["⊢ 0 = 0","⊢ 0 = 0"],["⊢ 0 = 0"],[]]
    commands = ["split","refl","refl"]
    origins = [{"step":index+1,"branch_id":index+1,"parent_id":index,"source":"heuristic",
                "macro_id":index+1,"macro_step":1,"command":command,"reason":"schema test fixture"}
               for index,command in enumerate(commands)]
    trace = [{"v":1,"session":"pure-fixture","step":index+1,"goals_before":goals[index],
              "goals_after":goals[index+1],"focus":0,"tactic":command,"status":"ok",
              "error":None,"origin":origins[index]} for index,command in enumerate(commands)]
    trace.append({"qed":True,"theorem":theorem,"proof_size":3,"tactic_count":3})
    branches = [{"id":index+1,"parent_id":index,"status":"proof" if index==2 else "open",
                 "goals_after":goals[index+1],"depth":index+1,"command":command,"source":"heuristic"}
                for index,command in enumerate(commands)]
    branches += [{"id":None,"parent_id":0,"status":"rejected","command":"ring",
                  "source":"heuristic","reason":"Goal is not an equality"},
                 {"id":None,"parent_id":0,"status":"rejected","command":"simp",
                  "source":"heuristic","reason":"Proof resource limit exceeded"},
                 {"id":None,"parent_id":999,"status":"rejected","command":"refl",
                  "source":"heuristic","reason":"No parent snapshot"}]
    search = {"profile":"pure-schema-fixture","commands":commands,"provenance":origins,
              "kernel_checked":True,"status":"proof","branches":branches,"branches_omitted":7,
              "diagnostics_omitted":0,"limited_by":[],"model_calls":0,"vampire_calls":0}
    result = {"status":"proved","theorem":theorem,"kernel_checked":True,
              "goals":[],"goals_scope":"final-independent-replay","proof_nodes":3,
              "commands":commands,"trace":trace,"search":search}
    return {"case_id":"test","canonical_theorem":theorem,"outcome":"proved","expected":"provable",
            "kernel_verified":True,"last_job":{"state":"completed","error":None,"result":result,
                "execution":{"worker_exit_code":0,"quiescent":True}}}


def extract(case,reserved=None):
    return exporter.extract_case(case,family="test_family",template_family="test_template",
        reservation=reserved or reservation(),source={"path":"pure-fixture.json","sha256":"a"*64})


class DecisionExportTests(unittest.TestCase):
    def test_complete_proof_yields_all_goal_sft_and_known_distances(self):
        sft,distance,attempts,pairs,outcome = extract(fixture())
        self.assertEqual([x["remaining_steps"] for x in distance],[3,2,1])
        self.assertEqual(sft[1]["goals_before"],["⊢ 0 = 0","⊢ 0 = 0"])
        self.assertTrue(all(row["partial_proof_cost"] is None for row in sft))
        self.assertEqual([x["rejected_action"]for x in pairs],["ring"])
        self.assertEqual(next(x for x in attempts if x["action"]=="simp")["outcome_label"],"resource_censored")
        self.assertEqual(outcome["unavailable_states"],1)
        self.assertEqual(outcome["branches_omitted"],7)

    def test_kernel_boolean_cannot_replace_complete_replay(self):
        for mutate in (
            lambda c:c["last_job"]["result"]["trace"].pop(),
            lambda c:c["last_job"]["result"]["trace"][1].update(goals_before=["⊢ 0 = 0"]),
            lambda c:c["last_job"]["result"]["trace"][-1].update(theorem="0 = 1"),
            lambda c:c["last_job"]["execution"].update(quiescent=False),
        ):
            case = fixture();mutate(case)
            with self.assertRaises(exporter.ExportError):extract(case)

    def test_resource_limited_case_produces_no_sft_or_false_label(self):
        case = fixture();case["outcome"]="unknown";case["kernel_verified"]=False
        case["last_job"]["result"]["search"].update(status="limit",limited_by=["max_states"])
        sft,distance,attempts,pairs,outcome = extract(case)
        self.assertEqual(sft,[]);self.assertEqual(distance,[]);self.assertEqual(pairs,[])
        self.assertTrue(outcome["censored"]);self.assertIsNone(outcome["mathematical_falsity_label"])

    def test_reserved_statement_family_and_intermediate_are_excluded(self):
        case = fixture()
        self.assertEqual(extract(case,reservation(case["canonical_theorem"]))[0],[])
        self.assertEqual(extract(case,reservation("0 = 0"))[0],[])
        reserved = reservation();reserved.families.add("test_template")
        self.assertEqual(extract(case,reserved)[-1]["excluded"],"reserved_template_or_family")

    def test_unparseable_intermediate_is_explicitly_excluded(self):
        reserved = reservation()
        def unavailable(_):raise ValueError("meta-variable identity unavailable")
        reserved.identity.goal_identities = unavailable
        *_,outcome = extract(fixture(),reserved)
        self.assertEqual(len(outcome["excluded_sft_steps"]),3)
        self.assertTrue(all(x["reason"].startswith("intermediate_exclusion_unavailable")
                            for x in outcome["excluded_sft_steps"]))

    def test_family_and_statement_links_cannot_cross_splits(self):
        rows = [{"theorem_identity":"x","family":"family_a","template_family":"template_a"},
                {"theorem_identity":"x","family":"family_b","template_family":"template_b"},
                {"theorem_identity":"y","family":"family_b","template_family":"template_b"},
                {"theorem_identity":"z","family":"family_c","template_family":"template_c"}]
        exporter.family_splits(rows,4)
        self.assertEqual(len({(row["split_group"],row["split"])for row in rows[:3]}),1)
        with self.assertRaises(exporter.ExportError):
            exporter.family_splits(rows,4,{"family_a":"train","family_b":"test"})

    def test_receipt_conflicts_and_website_default_rejected(self):
        self.assertEqual(exporter.receipt_exit({"actual_exit_code":0}),0)
        self.assertEqual(exporter.receipt_exit({"exit_code":0}),0)
        for value in ({},{"actual_exit_code":0,"exit_code":1},{"actual_exit_code":False}):
            with self.assertRaises(exporter.ExportError):exporter.receipt_exit(value)
        with self.assertRaises(exporter.ExportError):
            exporter.load_run(None,{"owner":"website","directory":"anything"})

    def test_exact_pinned_inputs_reject_tampering_symlinks_and_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary);path=root/"input.json";path.write_bytes(b'{"ok":true}')
            inputs = exporter.Inputs(root);pin=hashlib.sha256(path.read_bytes()).hexdigest()
            self.assertEqual(inputs.json("input.json",pin),{"ok":True})
            path.write_bytes(b'{"ok":false}')
            with self.assertRaises(exporter.ExportError):inputs.json("input.json",pin)
            (root/"link.json").symlink_to(path)
            with self.assertRaises(exporter.ExportError):inputs.json("link.json")
            with self.assertRaises(exporter.ExportError):inputs.json("../input.json")
        with self.assertRaises(exporter.ExportError):exporter.decode('{"x":1,"x":2}')

    def test_primitive_output_cannot_smuggle_a_plan_or_import(self):
        for action in ('{"actions":["refl"]}',"refl; exfalso","focus 1 refl","use reserved"):
            with self.assertRaises(exporter.ExportError):exporter.primitive_prompt(["⊢ 0 = 0"],action)


if __name__ == "__main__":unittest.main()
