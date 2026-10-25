"""Pure synthetic metadata/byte fixtures. Never an actual teacher/student run."""
import base64
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import remote_student_control as control
import student_transport as local


def packed(value):
    raw = value if type(value) is bytes else control.canonical(value)+b"\n"
    return {"bytes":len(raw),"sha256":control.digest(raw),"base64":base64.b64encode(raw).decode(),
            "stable":True,"complete_file":True}


def plan_fixture(rows=2050):
    data = {"schema":"hydra-teacher-augmented-data-attestation-v1","base_manifest_sha256":control.BASE_DATA_SHA,
        "base_training_rows":2047,"teacher_rows_added":rows-2047,"fresh_verified_continuations":1,
        "actual_teacher_model_calls":1,"selection_sha256":control.SELECTION_SHA,"holdout_sha256":control.HOLDOUT_SHA,
        "reserved_intermediate_check":"exact_closed_AST_plus_declared_template_exclusions",
        "teacher_source_scope":"complete_teacher_proposed_native_continuation","regenerated_byte_exact":True,
        "base_train_prefix_preserved":True,"validation_test_unchanged":True,
        "teacher_model_manifest_sha256":"4"*64,"manifest_sha256":"5"*64,"source_pins":{"fixture.py":"0"*64}}
    plan = {"schema":"hydra-teacher-augmented-pilot-plan-v1","profile":control.PROFILE,"model":control.MODEL,
        "initialization":"fresh_pinned_base_new_lora","resume":False,"automatic_retry":False,
        "model_trained":False,"epochs":1,"prompt_schema":"primitive_v4","planner_rows_allowed":False,
        "training_rows":rows,"validation_rows":432,"expected_optimizer_steps":(rows+7)//8,
        "data_attestation":data,"config_sha256":"6"*64,
        "config":{"run":{"output_dir":control.ARTIFACT},"data":{
            "train_path":control.CYCLE+"/dataset/primitive-train.jsonl",
            "eval_path":control.CYCLE+"/dataset/primitive-val.jsonl"}}}
    plan["plan_sha256"] = control.digest(control.canonical(plan))
    return plan


def spec_fixture(plan):
    # Nominal synthetic timing input only, never a chosen allocation.
    return control.make_spec(plan,config_sha256=plan["config_sha256"],
        dataset_sha256=plan["data_attestation"]["manifest_sha256"],plan_file_sha256="7"*64,
        source_manifest_sha256="8"*64,source_archive_sha256="9"*64,base_identity_sha256="a"*64,
        seconds=600,soft_limit_seconds=540,nonce="b"*32)


def evidence_fixture():
    plan = plan_fixture(); spec = spec_fixture(plan); steps = plan["expected_optimizer_steps"]
    record = control.reservation(spec,"123456",os.getuid())
    source = {"fixture.py":{"bytes":0,"sha256":"0"*64}}
    source_sha = control.digest(control.canonical(source))
    spec["source_pins_sha256"] = source_sha; record["source_pins_sha256"] = source_sha
    request = {"schema":"hydra-p7-student-update-request-v1","profile":control.PROFILE,
        "reservation":record,"reservation_sha256":control.digest(control.canonical(record)+b"\n"),
        "source_pins_before":source,"config":control.SOURCE+"/"+control.CONFIG,
        "dataset_manifest":control.SOURCE+"/"+control.DATA}
    completion = {"schema":"hydra-p7-student-update-completion-v1","profile":control.PROFILE,
        "completed":True,"error":None,"sources_unchanged":True,"source_pins_after":source,
        "actual_optimizer_steps":steps,"optimizer_callbacks_observed":steps,"base_rows_preserved":2047,
        "teacher_rows_added":3,"resume":False,"automatic_retry":False}
    claim = {"schema":"hydra-p7-student-update-consumption-v1","job_id":record["job_id"],"nonce":record["nonce"],
        "reservation_sha256":request["reservation_sha256"],"dataset_sha256":spec["dataset_sha256"],
        "plan_sha256":spec["plan_sha256"],"resume":False,"automatic_retry":False}
    tokens = {"schema":"hydra-decision-token-preflight-v1","plan_sha256":plan["plan_sha256"],
        "base":{"base_identity_sha256":spec["base_identity_sha256"]}}
    manifest = {"schema":"hydra-decision-pilot-artifact-v1","profile":control.PROFILE,"model":control.MODEL,
        "model_trained":True,"actual_optimizer_steps":steps,"resume":False,"automatic_retry":False,
        "saved_adapter_reload_admission":"required_by_P6_before_inference","plan":plan,
        "token_preflight":tokens,"base":tokens["base"],"reservation":{"job_id":record["job_id"]},
        "final_reservation":{"job_id":record["job_id"]},
        "finite_gradient_audit":{**{k:steps for k in ("expected_optimizer_boundaries","observed_optimizer_boundaries",
            "raw_finite_optimizer_boundaries","post_clip_finite_optimizer_boundaries")},
            "first_optimizer_step":1,"last_optimizer_step":steps},
        "adapter_update":{"changed_parameter_tensors":2,"trainable_parameter_tensors":2,"final_finite_parameter_tensors":2,
            "initial_tensor_population_sha256":"c"*64,"final_tensor_population_sha256":"d"*64},
        "adapter":{"root":"adapter","files":{},"sha256":"e"*64},
        "tokenizer":{"root":"tokenizer","files":{},"sha256":"f"*64}}
    contents = {"job/actual-process-exit.txt":b"0\n","job/reservation.json":record,
        "job/reservation.json.claimed":claim,"job/result/request.json":request,"job/result/completion.json":completion,
        "job/result/prepared-plan.json":plan,"job/result/token-preflight.json":tokens,
        "job/result/trained-artifact.json":manifest,"artifact/manifest.json":manifest}
    query = {"actual_exit_code":0,"stop_reason":None,"stdout_stderr":"|".join([
        record["job_id"],spec["job_name"],control.REMOTE_USER,control.ACCOUNT,control.PARTITION,
        "COMPLETED","0:0","100","10","8","64Gn","cpu=8,mem=64G,node=1,gres/gpu=1",
        "cpu=8,mem=64G,node=1,gres/gpu=1","node-fixture"])+"\n"}
    observation = {"job_id":record["job_id"],"read_only":True,"files":{k:packed(v) for k,v in contents.items()},
        "scheduler":{"sacct":query,"scontrol":{}},
        "admitted_plan_check":{"status":"verified_current_pins","plan_sha256":spec["plan_sha256"],
            "plan_file_sha256":spec["plan_file_sha256"],"expected_optimizer_steps":steps},
        "artifact_byte_verification":{"status":"verified_bytes_not_loaded","tensor_reload_performed":False,
            "groups":{k:manifest[k] for k in ("adapter","tokenizer")}}}
    transport = {"actual_ssh_exit_code":0,"owned_child_reaped":True,"output_complete":True,
        "stop_reason":None,"automatic_retry":False}
    return plan,spec,record,observation,transport,source_sha


class StudentTransportTests(unittest.TestCase):
    def evaluate(self, fixture):
        _,spec,record,observation,transport,source_sha = fixture
        with patch.object(control,"SOURCE_MAP_SHA",source_sha):
            return local.summarize(observation,spec,record,transport)

    def test_dynamic_steps_and_exact_student_job(self):
        plan = plan_fixture(); spec = spec_fixture(plan)
        self.assertEqual(spec["expected_optimizer_steps"],257)
        script = control.job_script(spec)
        self.assertIn("remote_student_update.py",script)
        self.assertNotIn(" -P ",script)
        self.assertIn("#!/bin/bash -l",script)
        self.assertEqual(control.reservation(spec,"123456",1000)["schema"],"hydra-p7-student-update-reservation-v1")

    def test_zero_or_changed_admitted_plan_rejected(self):
        for plan in (plan_fixture(2047),plan_fixture()):
            if plan["training_rows"] != 2047:
                plan["expected_optimizer_steps"] = 256
            with self.assertRaises(ValueError): spec_fixture(plan)

    def test_successful_collection_does_not_admit_tensor_reload(self):
        summary = self.evaluate(evidence_fixture())
        self.assertTrue(summary["collection_verified"])
        self.assertTrue(summary["training_evidence_complete"],summary)
        self.assertEqual(summary["finite_gradient_boundaries"],257)
        self.assertFalse(summary["adapter_reload_admitted"])
        self.assertFalse(summary["quality_evaluated"])

    def test_old_fixed_step_count_rejected(self):
        fixture = evidence_fixture(); observation = fixture[3]
        completion = local.complete_json(observation,"job/result/completion.json")
        completion["optimizer_callbacks_observed"] = 256
        observation["files"]["job/result/completion.json"] = packed(completion)
        self.assertFalse(self.evaluate(fixture)["training_evidence_complete"])

    def test_gradient_audit_must_cover_all_dynamic_steps(self):
        fixture = evidence_fixture(); observation = fixture[3]
        value = local.complete_json(observation,"artifact/manifest.json")
        value["finite_gradient_audit"]["raw_finite_optimizer_boundaries"] = 256
        for name in ("artifact/manifest.json","job/result/trained-artifact.json"):
            observation["files"][name] = packed(value)
        self.assertFalse(self.evaluate(fixture)["training_evidence_complete"])

    def test_partial_transport_hash_stop_or_incomplete_artifact_rejected(self):
        for change in ("transport","partial","byte_hashes","incomplete","process"):
            fixture = evidence_fixture(); observation = fixture[3]
            if change == "transport": fixture[4]["output_complete"] = False
            elif change == "partial": observation["files"]["artifact/manifest.json"]["complete_file"] = False
            elif change == "byte_hashes": observation["artifact_byte_verification"]["status"] = "rejected"
            elif change == "incomplete": observation["files"]["artifact/incomplete.json"] = packed({})
            else: observation["files"]["job/actual-process-exit.txt"] = packed(b"1\n")
            self.assertFalse(self.evaluate(fixture)["training_evidence_complete"],change)

    def test_pending_one_node_range_and_no_extra_gpu(self):
        spec = spec_fixture(plan_fixture())
        row = {"JobId":"123456","JobName":spec["job_name"],"Comment":"hydra-p6:"+spec["nonce"],
            "JobState":"PENDING","Reason":"JobHeldUser","Requeue":"0","Restarts":"0",
            "Account":control.ACCOUNT,"Partition":control.PARTITION,"NumCPUs":"8","NumNodes":"1-1",
            "TimeLimit":"00:10:00","Command":spec["remote_job_directory"]+"/job.sbatch",
            "WorkDir":spec["remote_job_directory"],"StdOut":spec["remote_job_directory"]+"/slurm.out",
            "StdErr":spec["remote_job_directory"]+"/slurm.err","UserId":"fixture(1000)",
            "ReqTRES":"cpu=8,mem=64G,node=1,gres/gpu=1"}
        control.check_held(row,spec,"123456",1000)
        row["NumNodes"] = "1-2"
        with self.assertRaises(ValueError): control.check_held(row,spec,"123456",1000)

    def test_saved_hashes_are_bytes_only_and_closed(self):
        with tempfile.TemporaryDirectory(prefix="student-byte-fixture-") as temporary:
            root = Path(temporary).resolve(); target = root/control.ARTIFACT
            manifest = {}
            for group,filename in (("adapter","adapter_model.safetensors"),("tokenizer","tokenizer.json")):
                directory = target/group; directory.mkdir(parents=True)
                raw = b"synthetic byte fixture, not a tensor"
                (directory/filename).write_bytes(raw)
                files = {group+"/"+filename:control.digest(raw)}
                manifest[group] = {"root":group,"files":files,"sha256":control.digest(control.canonical(files))}
            with patch.object(control,"SOURCE",str(root)):
                result = control.hash_saved_artifact(manifest)
                self.assertEqual(result["status"],"verified_bytes_not_loaded")
                self.assertFalse(result["tensor_reload_performed"])
                (target/"adapter"/"extra.bin").write_bytes(b"x")
                with self.assertRaises(ValueError): control.hash_saved_artifact(manifest)

    def test_deadline_propagates_from_collection_hashing(self):
        plan,spec,record,observation,_,source_sha = evidence_fixture()
        def snapshot(path,*,tail):
            text = str(path)
            prefix = "job" if text.startswith(spec["remote_job_directory"]+"/") else "artifact"
            base = spec["remote_job_directory"] if prefix == "job" else control.SOURCE+"/"+control.ARTIFACT
            return observation["files"].get(prefix+"/"+text[len(base)+1:])
        class Phase:
            def run(self,*args,**kwargs): return observation["scheduler"]["sacct"]
        with patch.object(control,"SOURCE_MAP_SHA",source_sha), patch.object(control,"snapshot",snapshot), \
             patch.object(control,"verify_sources",return_value=plan), \
             patch.object(control,"hash_saved_artifact",side_effect=TimeoutError("synthetic deadline")):
            with self.assertRaises(TimeoutError): control.collect(Phase(),spec,{},record)


if __name__ == "__main__":
    unittest.main()
