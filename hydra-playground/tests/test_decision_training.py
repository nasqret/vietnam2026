"""Pure dataset/config contracts. No training, tokenization, or native checks."""
from dataclasses import replace
import hashlib
from pathlib import Path
import sys
import unittest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(APP))
sys.path.insert(0,str(APP/"training-v5"))
from hydra_training_v5 import decision_data, decision_pilot, pilot_config
import export_decisions as exporter


class DecisionTrainingTests(unittest.TestCase):
    def test_bounded_fresh_configs_share_schedule_but_have_exact_model_pins(self):
        configs = [pilot_config.load_pilot_config(APP/"training-v5/configs"/name) for name in (
            "qwen3_1_7b_decisions_pilot.toml","qwen3_4b_decisions_pilot.toml","qwen3_8b_decisions_pilot.toml")]
        for config in configs:
            self.assertEqual(config.run.resume,"never")
            self.assertEqual(config.run.max_train_samples,4096)
            self.assertEqual(config.trainer,configs[0].trainer)
            self.assertEqual(config.data,configs[0].data)
        self.assertEqual(configs[2].model.revision,"49e3418fbbbca6ecbdf9608b4d22e5a407081db4")

    def test_auto_resume_oversized_epochs_and_unpinned_model_rejected(self):
        config = pilot_config.load_pilot_config(APP/"training-v5/configs/qwen3_4b_decisions_pilot.toml")
        invalid = [replace(config,run=replace(config.run,resume="auto")),
                   replace(config,run=replace(config.run,max_train_samples=4097)),
                   replace(config,trainer=replace(config.trainer,epochs=2)),
                   replace(config,model=replace(config.model,revision="0"*40)),
                   replace(config,model=replace(config.model,model_id="Unreviewed/model"))]
        for value in invalid:
            with self.assertRaises(ValueError):pilot_config.validate_pilot_config(value)

    def test_primitive_row_keeps_exact_all_goal_prompt_contract(self):
        goals = ["⊢ 0 = 0","n : ℕ ⊢ n = n"]
        rendered = exporter.primitive_prompt(goals,"refl")
        row = {"schema":"hydra-primitive-sft-v1","id":"pure-fixture","split":"train",**rendered,
               "kernel_checked":True,"censored":False,"goals_before":goals,"action":"refl",
               "verification_scope":"recorded_full_original_goal_independent_native_replay",
               "reserved_intermediate_check":"exact_closed_AST_plus_declared_template_exclusions"}
        self.assertEqual(decision_data.validate_primitive_row(row,split="train").tactic,"refl")
        for update in ({"goals_before":goals[:1]},{"censored":True},{"schema":"hydra-planner-sft-v1"},
                       {"verification_scope":"solver_said_unsat"},{"split":"test"}):
            with self.assertRaises(ValueError):decision_data.validate_primitive_row({**row,**update},split="train")

    def test_imports_do_not_initialize_native_or_framework(self):
        self.assertFalse(any(name == "peano_lab" or name.startswith("peano_lab.") for name in sys.modules))
        self.assertNotIn("torch",sys.modules)
        self.assertNotIn("mlx",sys.modules)
        self.assertNotIn("transformers",sys.modules)

    def test_actual_reservation_must_stay_single_gpu_and_bounded(self):
        reservation = {"job_id":"schema-fixture","gpus":1,"cpus":8,"memory_gib":64,
                       "seconds":7200,"elapsed_seconds":30}
        self.assertEqual(decision_pilot._reservation(reservation)["gpus"],1)
        for change in ({"gpus":2},{"cpus":9},{"memory_gib":65},{"seconds":7201},
                       {"elapsed_seconds":float("nan")},{"elapsed_seconds":7200}):
            with self.assertRaises(ValueError):decision_pilot._reservation({**reservation,**change})

    def test_gradient_probe_requires_unadapted_exact_session_and_explicit_disposal(self):
        config = pilot_config.load_pilot_config(APP/"training-v5/configs/qwen3_4b_decisions_pilot.toml")
        plan = decision_pilot.PilotPlan(config,None,{})
        identity = {"schema":"hydra-experimental-loaded-model-v1","model_loaded":True,
            "adapter":{"adapter_present":False},"automatic_download":False,
            "model_id":config.model.model_id,"revision":config.model.revision,
            "base_identity_sha256":"a"*64,
            "registry_sha256":hashlib.sha256((APP/"experimental-models/qwen3-base-v1.json").read_bytes()).hexdigest(),
            "source_sha256":hashlib.sha256((APP/"experimental_model.py").read_bytes()).hexdigest()}
        identity["model_manifest_sha256"] = hashlib.sha256(decision_pilot.canonical(identity)).hexdigest()
        decision_pilot._probe_admission(plan,identity,8,120,True,None)
        for changed in ({"adapter":{"adapter_present":True}},{"revision":"0"*40},
                        {"source_sha256":"0"*64},{"model_manifest_sha256":"0"*64}):
            with self.assertRaises(ValueError):
                decision_pilot._probe_admission(plan,{**identity,**changed},8,120,True,None)
        for examples,seconds,disposable in ((9,120,True),(True,120,True),(8,121,True),
                                            (8,float("nan"),True),(8,120,False)):
            with self.assertRaises(ValueError):
                decision_pilot._probe_admission(plan,identity,examples,seconds,disposable,None)
        self.assertNotIn("torch",sys.modules)


if __name__ == "__main__":unittest.main()
