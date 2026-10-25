# Proposed Hydra next-tactic provider

This directory is an isolated implementation proposal. It has not changed the running website, its loader, its kernel, or the default adapter. There has been no local model execution and no numerical backend test. The host driver owns actual checkpoint/base/source authentication, cluster submission and evaluation.

**Correction to the earlier runtime assessment:** the latent models are next-tactic models, not full-script models. They consume all current ordered goals and emit one literal tactic. Their training prompt advertises model-v3's full 247-theorem library. Hydra's deployed execution authority is primitive-v4, constructive, with no imported theorems. The comparison must preserve that distinction. No full-library authority is enabled here.

`hydra_torch_candidate.py` implements Hydra's existing `propose(goals_before, *, max_candidates)` interface, integer `calls`, and `report()`. `host_binding.py` provides an executable constructor example. The old adapter remains on disk and the live provider remains untouched; promotion, if supported by the comparison, is a separate reversible configuration change.

The host supplies an authenticated, frozen CUDA model in evaluation mode. For the historical arm this is the original PEFT causal LM; for the candidate arm it is the checkpoint's exact frozen vanilla `QwenRecurrentLM` wrapper at fixed depth 1. No approximation to recurrence is implemented. There are no downloads, checkpoint loaders, training calls, native proof claims, or device fallbacks in this bridge. The numerical backend refuses non-Linux/non-SLURM execution and requires both offline environment flags.

Both arms have a 6,144-token total context, 128 new-token ceiling, 16 actual generation-call ceiling, 4,096 total decision-token ceiling and at most 30 seconds of provider work. The host passes the shared case deadline and cancellation predicate. A provider can be asked for up to four candidates but returns at most one actual greedy candidate. It never pads output, retries failed inference or manufactures a candidate from a truncated result. GPU operations cannot be interrupted by this Python loop; the host must enforce the hard case process timeout (parent plans 35 seconds). Late outputs remain charged and are not accepted.

Prompts are never truncated or rewritten. The historical adapter uses the original primitive-v4 renderer and its existing authority token mask. The latent adapter uses the exact trained `compact_prompt` with all ordered goals, focus 0 and `library_prefix_length=247`; its argmax decoder is unmasked, matching training evaluation. Both outputs must pass the frozen ByteLevel receipt checker, including actual terminal EOS, then the current Hydra native authority compiler. Imported `use` actions are explicitly refused. Only unchanged, bounded literal tactics can reach Hydra search; the native search and original-theorem replay still decide proof validity.

This is **transfer to Hydra restricted authority**, not a reproduction of C6's full-library development score. It is also a fresh paired Torch/BF16 greedy comparison, not an exact replay of the deployed historical MLX/4-bit/beam-4 configuration. Preserve both disclosures when reporting results. Source provenance, checkpoint identity, conditioning authority and execution authority are included in the provider report. Actual call attempts, completed forwards and emitted token decisions (including EOS) are separate counters. Failed or late attempts retain their receipts and never count as proofs.

## Host binding

After authenticating the local base inventory, tokenizer inventory, adapter and source inventory, load with `local_files_only=True` and `trust_remote_code=False`, keep caching disabled, then freeze and evaluate the model. Use the pinned historical manifest and exact PEFT LoRA config for the old adapter. For C5/C6 use the selected checkpoint's exact frozen wrapper/config and parameter binding; do not import the unrelated mutable Campaign 3 checkout. If extracting a PyTorch checkpoint, verify its external SHA first and prefer `torch.load(..., weights_only=True)` with no unsafe-pickle fallback. A checkpoint identity string is not a substitute for checking actual files.

Supply these functions from already authenticated source modules to `bind_policy`:

| Binding | Historical arm | Latent vanilla arm |
| --- | --- | --- |
| `current_prompt_module` | Current native `training.peano_policy.prompt` | Same module, execution environment only |
| `current_authority_module` | Current native `training.peano_policy.authority` | Same current native module |
| `frozen_latent_data_module` | Frozen receipt support module | Candidate's authenticated `qwen_data` |
| `frozen_latent_eval_module` | Authenticated strict receipt checker | Candidate's authenticated `qwen_eval` |
| `provenance.policy` | `{"kind":"fixed","depth":1}` | Exact selected vanilla policy, same value |

`provenance` additionally requires actual `checkpoint_sha256`, `tokenizer_identity_sha256`, `source_inventory_sha256`, nonempty `run_id`, and exact integer `model_vocab_size`. The driver must separately pin the bridge and all callback sources; constructor validation checks the record's structure, not whether the host really authenticated weights. Use a fresh provider per case, keep model loading outside the case clock, and record `provider.report()` in a `finally` block even after a timeout or inference exception. Run C5 and C6 in separate child processes to prevent Python import reuse across different source trees.

Connect the returned provider to the existing `hybrid_search.search` model-policy argument and keep the same heuristic/native search budgets for all arms. Retain the current no-import environment and independent original-target replay. Root owns the 32-case manifest, subprocess supervisor and release decision; this directory does not add another controller.

## Validation scope

`check_contract.py` runs pure fixtures against the actual frozen C5 strict decoder and compact renderer. It tests literal EOS-bound output, failed/late-work accounting, refusal of imports and malformed text, context overflow without truncation, cancellation, receipt drift and invocation of the historical prefix mask. Its tokenizer, numerical backend and authority callback are explicit fixtures. It imports no Torch, Transformers, PEFT, MLX, or native proof runtime. Passing these fixtures does not establish model quality, GPU correctness, C6 source compatibility, or proof validity.

Run from the repository root:

```sh
python3 -B output/hydra-model-upgrade-2026-10-20/runtime-assessment/proposed-provider/check_contract.py \
  --frozen-source output/hydra-model-upgrade-2026-10-20/helios-inventory/c5-frozen-source
```

The actual initial fixture run completed with exit 0 (tool chunk `d8fb21`): ten checks, no forbidden imports, zero real model calls and zero native proof calls. Subsequent numerical-backend edits moved the completed-forward callback directly after model return and set the baseline's `logits_to_keep=1`, avoiding an unnecessary vocabulary-sized output for every prefix token. The installed Qwen3 implementation explicitly supports this argument (static inspection only). That CUDA path remains untested locally by design. Actual remote smoke/paired runs must verify the numerical and loader path before any promotion.
