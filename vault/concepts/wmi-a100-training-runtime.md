---
title: WMI A100 training runtime
tags: [peano-lab, llm, gpu, wmi, reproducibility]
---

# WMI A100 training runtime

The **WMI A100 training runtime** is a second, independently attested execution site for Peano
Lab's [[kernel-guided-policy-training]]. The owner has `hw_csi` access to the non-preemptible
`gpu_csi` partition; node `g3n1` contains four NVIDIA A100 80GB GPUs.

WMI is x86-64 with the central `anaconda/2025.12-1` / `pytorch-gpu` environment (Python 3.12,
PyTorch 2.5.1, CUDA 12.4). It must not reuse Helios's aarch64 CUDA-12.9 lock or claim Helios runtime
identity. Corrected probe `171369` passed on one A100-SXM4-80GB with BF16, a finite backward pass,
driver 610.43.02, model/package access, and 18 TB free storage; it installed nothing.

The follow-on environment binds a canonical central-base manifest and a separate 12-wheel
SHA-256 overlay into one content-addressed release. Source publication reconstructs the clean Git
tree under an exclusive lock; preparation, training, and evaluation hold the shared lock. A current
environment pointer is published only after data attestation and the complete LoRA save/reload smoke
pass. Torch 2.5.1 makes this pilot one-shot with a safetensors-only model-weight path: partial output
cannot be reused, checkpoint state is never loaded, and PEFT's pickle fallback is rejected before
loading. Preparation `171395` passed the full dataset-replay and LoRA save/reload smoke in 8m39s.
The dependent training submission then failed closed before `sbatch` because Bash whitespace
splitting lost its empty TSV dependency field. A strict nine-field parser fixes that control
boundary; source binding requires a fresh preparation job rather than relabeling `171395`.
Regardless of site, the learned model remains untrusted and every successful trajectory ends at
the [[trusted-kernel]].

Fresh same-source preparation `171414`, training `171421`, and evaluation `171423` subsequently
completed. The 100-step adapter recorded train/validation losses 0.78301/0.13615, but its decisive
result was 0/4 held-out goals at pass@4. Arbitrary request `171430` later exported one seven-node
checked direct-witness proof; parity request `171428` found no proof in sixteen samples.

After training, `scripts/wmi_prove_theorem.sh` is the supported arbitrary-theorem entry point. It
stores the closed formula and search budget in immutable canonical JSON, submits only its SHA-256
request ID through the allowlisted typed-A100 job, and binds request/job hashes in a durable ledger
before release. The compute job produces digest-named report, optional `.pa`, and terminal summary
artifacts; ad-hoc login-node or interactive inference is rejected because it lacks this runtime and
submission provenance.

Model-v2 additionally has `scripts/wmi_peano_policy_repl.sh`, a guarded four-hour interactive A100
allocation that loads the attested adapter once and sends theorem text only to the validated Python
input loop. A matching Helios GH200 launcher permits immediate use of a Helios-trained adapter;
moving the closed adapter/tokenizer/manifest tree to WMI remains a separately integrity-checked
deployment step.

Model-v3 separates the expensive historical proof replay from the current GPU program. Historical
job `172729` generated both source lanes, continuation `173040` completed independent replay,
token audit, and A100 runtime smoke, and job `213641` published the verified immutable fifteen-file
seal with content SHA-256
`7b22bdf083894e3d87b84fc463ff537a75eeecba8e34098429db215592ec6b5b`.
A new clean deployment must pass
`peano_wmi_prepare_v3_sealed_training.sbatch`: full seal/current-source eligibility, exact selected
token audit, and a real BF16 indexed-loss LoRA optimizer/save/reload smoke over the combined
longest-active-sequence/largest-completion memory envelope. When distinct rows witness the maxima,
the completion row receives attended label-masked prompt tokens before its supervised suffix;
zero-attention padding is not trusted because an unpadding backend could discard it. After freeing
the manual optimizer state, preparation performs one actual bounded `CompletionOnlyTrainer` step
and explicit evaluation on that same envelope. The cross-verifier requires its finite losses,
complete LoRA gradient population, adapter update, active dimensions, and no-save argument set.
The shared runtime record additionally requires one process/GPU, matching `cuda:0` Trainer and
Accelerator devices, BF16 mixed precision, `DistributedType.NO`, `DynamoBackend.NO`, no
DeepSpeed/FSDP/tensor-parallel plugin, exact Trainer accumulation, and Accelerator's backward
divisor equal to one so an environment override cannot rescale an already window-normalized loss.
The training loss also refuses a missing whole-window `num_items_in_batch`; evaluation alone may
use the local supervised-token mean. Checkpointing mode, AdamW constants, and NaN/Inf filtering are
explicit. Trainer's permissive built-in clipping is disabled; the pre-optimizer callback audits raw
gradients, clips to norm 1.0 with `error_if_nonfinite=True`, and audits all post-clip gradients. That
job performs no proof generation. First current-source attempt `214264` reached the selected-token
audit and failed closed before this runtime smoke or model loading: 73,446,475 train tokens exceeded
the reviewed 70,000,000-token ceiling. Its replacement raised only that ceiling to 74,000,000;
job `217123` passed the linear, quadratic, context, and completion gates and reached the runtime
smoke. It failed closed at saved-policy admission because Accelerate's retained BF16/FP32 forward
wrapper was compared with a bare fresh reload. The repaired shared path explicitly unwraps and
verifies the original forward before semantic capture; all exact output checks remain unchanged.

Production sets both Trainer save and evaluation strategies to `no`. An interval beyond the run is
not a sufficient checkpoint guard because the default callback can request a terminal save at
`max_steps`. Recovery and final persistence are explicit adapter-only safetensors operations; the
explicit stock validation metric is a mean of per-batch token means, not a corpus-global
completion-token NLL.

For model-v3, completion is now a separately validated evidence object. All scheduled, returned,
and Trainer-state optimizer counts agree; raw gradients, the strict custom max-norm-1 clip, and
post-clip gradients are observed at every boundary; and the complete finite norm/log curve is
bound to the final manifest. Canonical raw-byte fingerprints over trainable tensor names, dtypes,
shapes, and contents must change from initialization to the terminal adapter. The loader rejects
partial or inconsistent v3 artifacts before importing the model stack. See
[[kernel-guided-policy-training]] and [[kernel-judged-evaluation]].

Completion also admits the *saved* policy rather than trusting the live Python object. Three
run-bound probes from admitted train and validation states fingerprint canonical PEFT tensors and
exact indexed outputs. After the original Trainer/model is released, one fresh local-only Qwen,
tokenizer, and PEFT reload must reproduce the safetensors population and every probe; disabling the
adapter must change at least one probe. The evidence joins the base configuration, run identity,
`cuda:0` runtime, individual files, closed artifact trees, and completion record. Preparation runs
the same admission mechanism on a smaller extrema-plus-validation probe set and its model-free
verifier cross-binds the selection to the corpus and token audits.

Production pins `bf16_full_eval=false`. In the pinned Transformers version that option casts the
whole live model to BF16, whereas PEFT normally retains FP32 LoRA tensors; using it would mutate the
policy after the terminal save. Tensor populations are rechecked after serialization and explicit
evaluation. Final output is claimed by exclusive directory creation, and the run identity,
adapter, tokenizer, and manifest are protected, fsynced no-replace publications whose output and
parent inode/device/mode identities are checked again before completion. V3 closed-tree hashing
rejects symlink components, special/cross-device nodes, and hard links, binds descriptor identities
through the read, repeats the complete inventory, and requires 0555 directories plus 0444 files.

The launch contract ties that strict lane to the data contract: prompt v3 is accepted if and only
if the model-v3 curriculum is present, and this alignment is checked before Torch, PEFT, or
Transformers import. After semantic admission and slower provenance checks, production re-verifies
both protected trees immediately before publishing the final manifest without replacement. Direct
generation and pretrained-base comparison also verify adapter/tokenizer closure before and after
heavy loading. The focused wiring audit passes 89 tests; it establishes no optimizer or capability
result.

The adapter-only recovery path depends on a real filesystem capability, not just Linux API
availability. Before scheduled training, a retained model-free probe exercises the production
`renameat2(RENAME_NOREPLACE)` branch on the exact `/work` output filesystem, fsyncs and protects its
sentinel tree, and publishes an exclusive canonical report. The trainer binds that report into its
run identity and rechecks the live probe before final publication. Job `217859` passed and retained
that exact-filesystem publication preflight before optimization, so the current run has direct
Linux shared-filesystem evidence rather than an assumption.

Recovery accepts exact modes `0555` for directories and `0444` for regular files. These protected
modes are provenance and accidental-corruption gates. They do not defend against a hostile process
with the same filesystem-owner authority, which can deliberately change modes and bytes.

Only an exact completed sealed-preparation job may authorize the one-shot 36-hour training script;
only that training job may authorize the twelve-hour fixed-budget evaluation. The guarded submitter
checks the immutable ledger, expected predecessor script, report digests, and current reviewed
environment before releasing a held job. Evaluation is followed by a model-free independent
kernel replay. The corpus seal digest is fixed above; job `214264` is rejected evidence, not an
accepted predecessor. Job `217123` contributes a valid token audit but no accepted runtime-smoke
report and is likewise not a training predecessor. Repaired job `217768` passed all three
preparation reports under source `e0f7e7d0`, but the completed-predecessor and 649-step schedule
fixes created a new exact source identity. Fresh same-source preparation `217851` then passed the
full chain under source `4d44609e`; guarded successor `217859` is actively running the production
optimizer. Its live progress and recovery trees are evidence of execution, not a final adapter or
model-v3 solve result.

## Read-only live observation

The Training Observatory keeps the browser outside WMI authority. A localhost-only Python
collector serializes one fixed bounded SSH read, caches sanitized JSON, and exposes only GET/HEAD
routes. VPN loss turns the last view visibly stale. The browser cannot submit, cancel, signal, name
a remote path, or run a command. Exact production loss is shown only after a flushed Trainer record
or final manifest; admission-smoke loss is labeled separately. Because the Trainer shuffles rows
and accumulates 32 microbatches, its corpus panel shows representative admitted examples, never a
claimed current batch. See the repository document
[`docs/PEANO_TRAINING_DASHBOARD.md`](../../docs/PEANO_TRAINING_DASHBOARD.md).

## Related

[[kernel-guided-policy-training]] · [[kernel-judged-evaluation]] ·
[[verifier-guided-policy-evaluation-and-search]] · [[content-addressed-lemma-library]]
