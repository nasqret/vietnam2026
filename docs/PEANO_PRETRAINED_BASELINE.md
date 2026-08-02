# Model-v3 pretrained-base comparison

The model-v3 experiment has a separate pretrained-base control. It answers a
narrow causal question: under the same prompt, theorem library, frozen goals,
decoder, and kernel-guided search budget, what can pinned
`Qwen/Qwen3-1.7B-Base` do before the Peano LoRA update?

This is not a flag on the trained evaluator. The entry point is
`scripts/eval_pretrained_peano_policy.py`, and its WMI job is
`slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch`. The CLI accepts only a
completed model-v3 comparison adapter and the fixed report location. It has no
goal, seed, decoding, or search-budget switches.

## Authority and treatment separation

The final adapter `training-manifest.json` is the immutable comparison
authority. Before any model framework is imported, the baseline requires:

- the exact prompt-v3 full-prefix environment containing all 247 independently
  checked public theorems;
- the exact four held-out goal records and their contract digest;
- pinned `Qwen/Qwen3-1.7B-Base` model and tokenizer revisions at one 40-hex
  snapshot;
- a positive completed optimizer schedule, with actual steps equal to the
  preflight count; and
- closed, hash-matching adapter and tokenizer directories, including the
  safetensors-only adapter rule.

The adapter directory is verified even though its weights are not used. The
loader reads the closed tokenizer, then loads the base model at the manifest's
pinned revision. It never imports PEFT and never calls
`PeftModel.from_pretrained`. The report's base-policy kind is therefore
`peano-policy-pretrained-base-v1`, and its comparison-authority record binds the
training-manifest SHA-256 plus the closed adapter and tokenizer tree hashes. The
complete comparison record, after adding the frozen goal, seed, and budget
fields, carries its own canonical JSON SHA-256.

The source group, runtime, deployment, Slurm job, and exact training predecessor
are captured before model loading and checked again after evaluation. The
adapter manifest and both closed artifact trees are checked before loading,
after loading, after search, and immediately before no-overwrite publication.
The report is a direct child of the completed comparison run, outside its
closed `adapter/` and `tokenizer/` subtrees.

## Frozen evaluation envelope

The control and trained treatment use the same evaluator-v4 kernel finalization
and the same four goals. The control fixes:

| Field | Value |
|---|---:|
| seed | `20260728` |
| maximum depth | 32 |
| beam width | 16 |
| candidates per state | 8 |
| model calls per goal | 512 |
| discovered states per goal | 4,096 |
| generated tokens per candidate | 256 |
| sampling temperature / top-p | 1.0 / 1.0 |

Every successful search still closes through Peano Lab's independent kernel on
the original target. Unsuccessful model output is only an unsuccessful search;
it cannot become a proof claim.

The trained-adapter replay gate remains intentionally unchanged. In particular,
`training/peano_policy/evaluation_replay.py` accepts only the
`peano-policy-adapter-v1` identity and therefore rejects this baseline report.
If publication later requires a second independent structural replay
attestation, it must be a separate baseline-specific gate rather than a broader
exception in the trained-treatment verifier.

## WMI launch

After the model-v3 training job has completed under the same clean deployed
source, dry-run and then submit the separate dependent job:

```console
scripts/submit_wmi_slurm_job.sh --test-only \
  --completed-predecessor TRAIN_JOB \
  slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch

scripts/submit_wmi_slurm_job.sh --submit \
  --confirm PEANO-LAB-WMI-TRAINING \
  --completed-predecessor TRAIN_JOB \
  slurm/peano_wmi_eval_pretrained_qwen3_1_7b_v3.sbatch
```

The expected report is
`results/peano-policy/qwen3-1.7b-lora-v3-library/pretrained-base-heldout-search-wmi-b16-c8-d32.json`.
The job is implemented and tested, but it must not be submitted before the
comparison adapter has actually completed.
