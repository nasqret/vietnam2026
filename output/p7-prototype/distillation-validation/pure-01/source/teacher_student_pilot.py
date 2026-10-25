"""Explicit teacher-augmented student pilot, derived from frozen v5 v2.

This separate profile changes dataset admission and source provenance only.
The completion-only tokenization, optimizer schedule, model loading, LoRA
shapes, gradient/update audits and saved-artifact code remain v5-derived.
No model/tokenizer/training work occurs unless an orchestrator calls it.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import tempfile
import time

from teacher_data import (ROOT, APP, WORKING, DecisionDataset,
    attest_teacher_dataset as attest_decision_dataset, verify_working_baseline, require)
import teacher_data
from hydra_training_v5.pilot_config import load_pilot_config, validate_pilot_config

PROFILE = "hydra-fresh-teacher-augmented-pilot-v1"
# Metadata copied from the v4 objective contract; its implementation remains in
# peano_policy.objective and is compared again at execution. Importing that
# historical module eagerly imports native data/catalogue code, so preparation
# keeps this inert JSON contract and never initializes that machinery.
OBJECTIVE = {"format":"peano-completion-only-indexed-logits","v":1,
    "task":"causal-next-token-completion-sft","supervision":"contiguous-completion-suffix-including-eos",
    "ignore_index":-100,"causal_shift":1,
    "projection":{"model_argument":"logits_to_keep","positions":"union-of-nonignored-shifted-label-positions"},
    "loss":{"function":"cross_entropy","logits_dtype":"float32","reduction":"summed-token-loss/num-items-in-batch"}}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode()


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _source_pins():
    paths = [WORKING/"BASELINE.json",APP/"export_decisions.py",APP/"branch_ranker.py",
             APP/"experimental_model.py",APP/"experimental-models/qwen3-base-v1.json"]
    paths.extend(sorted((WORKING/"hydra_training_v5").rglob("*.py")))
    pins = {path.relative_to(ROOT).as_posix():_sha(path) for path in paths}
    pins.update(teacher_data.source_pins())
    return pins


@dataclass(frozen=True)
class PilotPlan:
    config: object
    dataset: DecisionDataset
    record: dict


def prepare(config_path, *, dataset_manifest, dataset_sha256, failure_output=None):
    config = load_pilot_config(config_path)
    dataset = attest_decision_dataset(dataset_manifest,expected_sha256=dataset_sha256,failure_output=failure_output)
    require(Path(dataset.manifest_path).parent/"primitive-train.jsonl" == Path(config.data.train_path)
            and Path(dataset.manifest_path).parent/"primitive-val.jsonl" == Path(config.data.eval_path),
            "Config must identify this exact admitted primitive dataset.")
    require(len(dataset.train) <= config.run.max_train_samples
            and len(dataset.validation) <= config.run.max_eval_samples,
            "Row cap must be selected before admission; no model-specific dropping.")
    expected_steps = math.ceil(len(dataset.train)/config.trainer.gradient_accumulation_steps)
    configuration = asdict(config)
    configuration["path"] = config.path.relative_to(ROOT).as_posix()
    record = {"schema":"hydra-teacher-augmented-pilot-plan-v1","profile":PROFILE,
        "config":configuration,"config_sha256":_sha(config.path),
        "data_attestation":dataset.attestation,"source_pins":_source_pins(),
        "model":{"model_id":config.model.model_id,"revision":config.model.revision},
        "prompt_schema":"primitive_v4","planner_rows_allowed":False,
        "initialization":"fresh_pinned_base_new_lora","resume":False,"epochs":1,
        "training_rows":len(dataset.train),"validation_rows":len(dataset.validation),
        "training_row_ids_sha256":dataset.row_ids_sha256,
        "validation_row_ids_sha256":dataset.validation_ids_sha256,
        "expected_optimizer_steps":expected_steps,"objective":json.loads(canonical(OBJECTIVE)),
        "reservation_ceiling":{"gpus":1,"cpus":8,"memory_gib":64,"seconds":7200},
        "campaign_gpu_hours_ceiling":6,"campaign_ledger_enforced_by":"job_orchestrator",
        "automatic_retry":False,"model_trained":False,"benchmark_claim":False}
    record["plan_sha256"] = hashlib.sha256(canonical(record)).hexdigest()
    return PilotPlan(config,dataset,record)


def _refresh(plan):
    require(type(plan) is PilotPlan, "A prepared pilot plan is required.")
    validate_pilot_config(plan.config)
    unsigned = {key:value for key,value in plan.record.items() if key != "plan_sha256"}
    require(hashlib.sha256(canonical(unsigned)).hexdigest() == plan.record["plan_sha256"],
            "Pilot plan changed after preparation.")
    require(_sha(plan.config.path) == plan.record["config_sha256"]
            and _source_pins() == plan.record["source_pins"], "Prepared config/source bytes changed.")
    # The first prepare() regenerates full data. Every execution boundary also
    # verifies exact dataset bytes, avoiding a second claim of new native replay.
    require(_sha(ROOT/plan.dataset.manifest_path) == plan.dataset.manifest_sha256,
            "Prepared dataset manifest changed.")
    from hydra_training_v5.decision_data import _exporter
    exporter = _exporter()
    inputs = exporter.Inputs()
    manifest = inputs.json(plan.dataset.manifest_path,plan.dataset.manifest_sha256)
    require(manifest.get("schema") == teacher_data.DATA_SCHEMA
            and manifest.get("training_allowed") is True and manifest.get("teacher_rows_added",0) > 0
            and manifest.get("source_pins") == teacher_data.source_pins(),
            "Teacher dataset is no longer the explicitly admitted nonempty extension.")
    for record in manifest["inputs"]:
        inputs.read(record["path"],record,exporter.MAX_INPUT_BYTES)
    directory = str(Path(plan.dataset.manifest_path).parent)
    for name,pin in manifest["files"].items():
        inputs.read(directory+"/"+name,pin,exporter.MAX_INPUT_BYTES)


def authenticate_pilot_base(plan, base_directory, *, should_stop=None):
    from hydra_training_v5.decision_data import _exporter
    _exporter()  # Explicitly install/validate this app module path, no model work.
    import experimental_model
    require(Path(experimental_model.__file__).resolve() == APP/"experimental_model.py",
            "Base authenticator came from an unexpected module path.")
    key = {"Qwen/Qwen3-1.7B-Base":"qwen3-1.7b-base", "Qwen/Qwen3-4B-Base":"qwen3-4b-base",
           "Qwen/Qwen3-8B-Base":"qwen3-8b-base"}[plan.config.model.model_id]
    record = experimental_model.authenticate_base(key,base_directory,should_stop=should_stop)
    require(record.get("model_id") == plan.config.model.model_id
            and record.get("revision") == plan.config.model.revision
            and record.get("weight_bytes_fully_hashed") is True and record.get("model_loaded") is False,
            "Base bytes are not authenticated to this exact pilot model.")
    return record


def tokenize(plan, *, base_directory, tokenizer=None, should_stop=None):
    _refresh(plan)
    base_identity = authenticate_pilot_base(plan,base_directory,should_stop=should_stop)
    if tokenizer is None:
        from transformers import AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(str(base_directory),
            local_files_only=True,use_fast=True,trust_remote_code=False)
    require((tokenizer.init_kwargs.get("_commit_hash") or plan.config.model.revision) == plan.config.model.revision,
            "Tokenizer revision differs from the model pin.")
    require(type(tokenizer.eos_token_id) is int, "Tokenizer has no EOS token.")
    if tokenizer.pad_token_id is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"
    # Imported only on an explicitly scheduled tokenizer/training operation.
    from hydra_training_v5.peano_policy.data import tokenize_completion
    from hydra_training_v5.peano_policy.budget import tokenizer_identity_record
    features,report = {},{}
    for split,examples in (("train",plan.dataset.train),("val",plan.dataset.validation)):
        features[split] = []
        for example in examples:
            require(not (should_stop and should_stop()), "Token preflight was cancelled; no row dropping.")
            features[split].append(tokenize_completion(example,tokenizer,max_length=plan.config.data.max_length))
        report[split] = {"rows":len(examples),"total_tokens":sum(len(x["input_ids"])for x in features[split]),
            "supervised_tokens":sum(sum(token != -100 for token in x["labels"]) for x in features[split]),
            "max_tokens":max(len(x["input_ids"])for x in features[split]),
            "squared_tokens":sum(len(x["input_ids"])**2 for x in features[split]),
            "features_sha256":hashlib.sha256(canonical(features[split])).hexdigest()}
    record = {"schema":"hydra-decision-token-preflight-v1","plan_sha256":plan.record["plan_sha256"],
        "base":base_identity,
        "tokenizer":tokenizer_identity_record(tokenizer,model_id=plan.config.model.model_id,
                                              revision=plan.config.model.revision),
        "splits":report,"rows_dropped":0,"state_truncation":False,
        "training_row_ids_sha256":plan.dataset.row_ids_sha256,
        "validation_row_ids_sha256":plan.dataset.validation_ids_sha256}
    return features,record,tokenizer


def _reservation(value):
    require(type(value) is dict and value.get("gpus") == 1
            and type(value.get("cpus")) is int and 1 <= value["cpus"] <= 8
            and type(value.get("memory_gib")) in (int,float) and 0 < value["memory_gib"] <= 64
            and type(value.get("seconds")) in (int,float) and 0 < value["seconds"] <= 7200
            and type(value.get("elapsed_seconds")) in (int,float) and math.isfinite(value["elapsed_seconds"])
            and 0 <= value["elapsed_seconds"] < value["seconds"]
            and type(value.get("job_id")) is str and value["job_id"],
            "Actual live single-GPU reservation exceeds the declared pilot ceiling.")
    return {key:value[key] for key in ("job_id","gpus","cpus","memory_gib","seconds")}






def execute(plan, *, base_directory, expected_token_preflight_sha256, reservation_check,
            stop_requested=None, progress=None, stop_after_seconds=6900):
    """Run one real fresh pilot. Caller supplies the live scheduler observation.

    The outer scheduler enforces wall/RSS limits and the six-hour campaign ledger.
    A callback cannot interrupt a blocked GPU kernel; no instantaneous stop claim.
    """
    require(callable(reservation_check) and (stop_requested is None or callable(stop_requested)),
            "A live reservation checker is required before model loading.")
    require(type(stop_after_seconds) in (int,float) and math.isfinite(stop_after_seconds)
            and 0 < stop_after_seconds <= 6900, "Soft stop exceeds allocation/cleanup reserve.")
    _refresh(plan)
    reservation = reservation_check()
    allocation = _reservation(reservation)
    started = time.monotonic()-reservation["elapsed_seconds"]
    deadline = started+min(stop_after_seconds,allocation["seconds"]-60)
    def boundary():
        require(time.monotonic() < deadline and not (stop_requested and stop_requested()),
                "Pilot stop reached; this attempt is incomplete and cannot resume.")
    def emit(kind,**fields):
        if progress is not None:progress({"kind":kind,**fields})
    output = ROOT/plan.config.run.output_dir
    require(not output.exists() and not output.is_symlink(), "Fresh pilot output directory required.")
    require(os.environ.get("PYTHONHASHSEED") == str(plan.config.run.seed),
            "PYTHONHASHSEED must be set before Python starts.")
    output.mkdir(parents=True,exist_ok=False)
    def save(name,record):
        with (output/name).open("xb") as stream:stream.write(canonical(record)+b"\n")
    save("started.json",{"schema":"hydra-decision-pilot-start-v1","plan":plan.record,
                          "reservation":reservation,"model_trained":False})
    try:
        boundary()
        import torch
        import transformers
        from peft import LoraConfig,get_peft_model
        from hydra_training_v5.peano_policy.train import (_CompletionCollator,_FiniteGradientCallbackMixin,
            _trainable_tensor_population_snapshot,_set_seeds)
        from hydra_training_v5.peano_policy.objective import (CompletionOnlyTrainerMixin,require_indexed_logits_support,completion_objective_record,
                                             single_process_trainer_runtime_record)
        from hydra_training_v5.peano_policy import training_evidence,manifest as artifacts
        require(torch.cuda.is_available() and torch.cuda.device_count() == 1 and torch.cuda.is_bf16_supported(),
                "This pilot requires exactly one BF16 CUDA GPU; no local fallback.")
        require(int(os.environ.get("WORLD_SIZE","1")) == 1,"Multi-process training is outside this pilot.")
        require(completion_objective_record() == plan.record["objective"] == OBJECTIVE,
                "Executed v4 completion objective differs from the prepared contract.")
        _set_seeds(plan.config.run.seed,torch,transformers.set_seed)
        features,tokens,tokenizer = tokenize(plan,base_directory=base_directory,
            should_stop=lambda: time.monotonic() >= deadline or bool(stop_requested and stop_requested()))
        require(hashlib.sha256(canonical(tokens)).hexdigest() == expected_token_preflight_sha256,
                "Tokenized exposure changed since the paired preflight.")
        save("token-preflight.json",tokens)
        boundary()
        require(_reservation(reservation_check()) == allocation, "Scheduler reservation changed.")
        require(authenticate_pilot_base(plan,base_directory,
            should_stop=lambda: time.monotonic() >= deadline or bool(stop_requested and stop_requested())) == tokens["base"],
            "Authenticated base/tokenizer bytes changed before model loading.")
        emit("loading-model",model=plan.record["model"])
        model = transformers.AutoModelForCausalLM.from_pretrained(str(base_directory),
            torch_dtype=torch.bfloat16,attn_implementation="sdpa",
            trust_remote_code=False,use_safetensors=True,local_files_only=True)
        require((getattr(model.config,"_commit_hash",None) or plan.config.model.revision) == plan.config.model.revision,
                "Loaded base model differs from the pinned revision.")
        # Portable PEFT metadata only. Full base-byte authentication above is
        # the authority; this field must never select another model to open.
        model.config._name_or_path = plan.config.model.model_id
        require_indexed_logits_support(model)
        model.config.use_cache = False
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant":False})
        model.enable_input_require_grads()
        model = get_peft_model(model,LoraConfig(r=16,lora_alpha=32,lora_dropout=0.05,bias="none",
            task_type="CAUSAL_LM",target_modules=list(plan.config.lora.target_modules)))
        named = [(name,value)for name,value in model.named_parameters()if value.requires_grad]
        initial = _trainable_tensor_population_snapshot(torch,named)
        expected_steps = plan.record["expected_optimizer_steps"]
        audit = training_evidence.FiniteGradientAudit(expected_optimizer_steps=expected_steps,
                                                     trainable_parameter_names=initial.names)
        class CompletionTrainer(CompletionOnlyTrainerMixin,transformers.Trainer):pass
        class FiniteGradients(_FiniteGradientCallbackMixin,transformers.TrainerCallback):pass
        class StopAndLog(transformers.TrainerCallback):
            def on_step_end(self,args,state,control,**kwargs):
                boundary();emit("optimizer-step",step=int(state.global_step));return control
        args = transformers.TrainingArguments(output_dir=str(output),overwrite_output_dir=False,
            do_train=True,do_eval=True,num_train_epochs=1.0,max_steps=-1,
            per_device_train_batch_size=1,per_device_eval_batch_size=1,gradient_accumulation_steps=8,
            learning_rate=0.0001,weight_decay=0.01,warmup_ratio=0.05,lr_scheduler_type="cosine",
            optim="adamw_torch_fused",bf16=True,bf16_full_eval=False,tf32=True,
            gradient_checkpointing=True,gradient_checkpointing_kwargs={"use_reentrant":False},
            max_grad_norm=0.0,logging_steps=1,logging_nan_inf_filter=False,
            eval_strategy="no",save_strategy="no",save_safetensors=True,report_to=[],
            seed=plan.config.run.seed,data_seed=plan.config.run.seed,dataloader_num_workers=0,
            remove_unused_columns=False,prediction_loss_only=True,label_names=["labels"],
            average_tokens_across_devices=True,disable_tqdm=True)
        trainer = CompletionTrainer(model=model,args=args,train_dataset=features["train"],
            eval_dataset=features["val"],data_collator=_CompletionCollator(torch,tokenizer.pad_token_id),
            callbacks=[FiniteGradients(torch=torch,named_parameters=named,audit=audit),StopAndLog()])
        runtime = single_process_trainer_runtime_record(trainer,expected_gradient_accumulation_steps=8)
        arguments = training_evidence.reviewed_trainer_arguments_record(trainer)
        boundary();emit("training-start",rows=len(features["train"]),expected_optimizer_steps=expected_steps)
        trained = trainer.train(resume_from_checkpoint=False)
        require(trained.global_step == expected_steps, "Training stopped before the exact one-pass schedule completed.")
        final = _trainable_tensor_population_snapshot(torch,named)
        before,after = dict(initial.record_hashes),dict(final.record_hashes)
        update = training_evidence.adapter_update_audit_record(trainable_parameter_names=final.names,
            initial_tensor_population_sha256=initial.population_sha256,final_tensor_population_sha256=final.population_sha256,
            changed_parameter_names=tuple(name for name in final.names if before[name] != after[name]),
            final_finite_parameter_names=final.names)
        boundary()
        development = trainer.evaluate()
        require(_trainable_tensor_population_snapshot(torch,named) == final, "Validation changed adapter weights.")
        boundary()
        adapter_stage = Path(tempfile.mkdtemp(prefix=".adapter.partial-",dir=output))
        model.save_pretrained(adapter_stage,safe_serialization=True)
        artifacts.publish_staged_directory_noreplace(adapter_stage,output/artifacts.ADAPTER_SUBDIR)
        tokenizer_stage = Path(tempfile.mkdtemp(prefix=".tokenizer.partial-",dir=output))
        tokenizer.save_pretrained(str(tokenizer_stage))
        artifacts.publish_staged_directory_noreplace(tokenizer_stage,output/artifacts.TOKENIZER_SUBDIR)
        adapter = artifacts.artifact_directory_hash(output,artifacts.ADAPTER_SUBDIR)
        tokenizer_files = artifacts.artifact_directory_hash(output,artifacts.TOKENIZER_SUBDIR)
        artifacts.require_safetensors_adapter(adapter)
        _refresh(plan);boundary()
        require(authenticate_pilot_base(plan,base_directory,
            should_stop=lambda: time.monotonic() >= deadline or bool(stop_requested and stop_requested())) == tokens["base"],
            "Authenticated base/tokenizer bytes changed during training.")
        final_reservation = reservation_check()
        require(_reservation(final_reservation) == allocation,"Final actual reservation changed.")
        record = {"schema":"hydra-decision-pilot-artifact-v1","profile":PROFILE,"model_trained":True,
            "model":plan.record["model"],"base":tokens["base"],
            "plan":plan.record,"token_preflight":tokens,"reservation":reservation,
            "final_reservation":final_reservation,"elapsed_allocation_seconds":time.monotonic()-started,
            "actual_optimizer_steps":trained.global_step,"training_metrics":trained.metrics,
            "validation_metrics":development,"trainer_runtime":runtime,"trainer_arguments":arguments,
            "objective":completion_objective_record(),"finite_gradient_audit":audit.record(),
            "adapter_update":update,"adapter":adapter,"tokenizer":tokenizer_files,
            "peak_allocated_gpu_bytes":torch.cuda.max_memory_allocated(),
            "frameworks":{"torch":torch.__version__,"transformers":transformers.__version__},
            "saved_adapter_reload_admission":"required_by_P6_before_inference",
            "automatic_retry":False,"resume":False,"benchmark_claim":False}
        save("manifest.json",record);emit("training-complete",optimizer_steps=trained.global_step)
        return record
    except BaseException as error:
        save("incomplete.json",{"schema":"hydra-decision-pilot-incomplete-v1","model_trained":False,
            "plan_sha256":plan.record["plan_sha256"],"error_type":type(error).__name__,
            "error":str(error)[:1000],"elapsed_allocation_seconds":time.monotonic()-started,
            "automatic_retry":False,"resume":False})
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Admit and prepare only; no tokenizer/model/training work.")
    parser.add_argument("--config",type=Path,required=True)
    parser.add_argument("--dataset-manifest",required=True)
    parser.add_argument("--dataset-sha256",required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--failure-output",type=Path)
    args = parser.parse_args(argv)
    require(not args.output.exists(),"Refusing to overwrite a pilot plan.")
    plan = prepare(args.config,dataset_manifest=args.dataset_manifest,dataset_sha256=args.dataset_sha256,
                   failure_output=args.failure_output)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with args.output.open("xb") as stream:stream.write(canonical(plan.record)+b"\n")
    print(json.dumps({"status":"prepared_not_trained","plan_sha256":plan.record["plan_sha256"],
                      "training_rows":len(plan.dataset.train),"output":str(args.output)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
