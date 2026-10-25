# Reversible local vanilla candidate

`hydra_mlx_vanilla.py` is an optional loader/provider proposal. It is not imported by the running website. It makes no changes to the old adapter, quantized Base, live source, or model-selection default. It supports only the vanilla rank-32 checkpoint exported as safetensors, not fixed/random/adaptive recurrence.

The existing `.runtime/model` directory already contains the exact latent Base tokenizer: `tokenizer.json` SHA `c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539` and `tokenizer_config.json` SHA `3c04ed3ca964ea2f6b2b5faf0dc4d31aec1cb1e8b4bcf63f402d295046b422b5`. The old adapter's separate tokenizer differs. The new loader therefore uses the authenticated quantized Base directory's original tokenizer, with no download or tokenizer rewrite.

The conversion reads exactly 392 F32 matrices named `base_model.base_model.model.model.layers.{layer}.{projection}.lora_{A|B}.default.weight`. It checks all names, dimensions, data spans and actual file hash before importing MLX. A `(32,input)` PEFT A matrix becomes MLX `(input,32)` `lora_a`; a `(output,32)` B matrix becomes `(32,output)` `lora_b`. MLX uses scale 2 (`64/32`) and dropout 0. Extra gate/damping tensors, other ranks, missing matrices and non-finite weights are refused. Values are compared against the exact loaded transposes. Nothing is merged into or written over the quantized Base.

At fixed depth 1 the frozen latent wrapper bypasses damping and runs each original decoder block once, making the ordinary Qwen3 architecture appropriate for this vanilla preview. The proposed MLX decoder runs the full prefix without a KV cache and projects only its last hidden state through the tied output head. It reuses the previously implemented `CandidatePolicy`: exact compact-v3 full-library conditioning, greedy width 1, actual EOS and ByteLevel validation, then unchanged current no-import authority compilation and native search/replay. Default limits are 6,144 total-context tokens, 128 new tokens, 16 model calls, 4,096 emitted decisions and 30 provider seconds. The current runtime's 6 GiB Metal memory cap and 256 MiB cache cap are retained.

This remains a **quantized local preview**. Four-bit Base arithmetic and MLX differ from the GH200/BF16 comparison. No numerical equivalence, local latency, memory sufficiency at maximum context, or proof-quality improvement has been established. Full-prefix decoding may be slower than the existing cached MLX decoder; local acceptance/latency testing is a promotion gate, not a reason to silently enlarge budgets or truncate input.

The integration call, after a candidate wins evaluation, is:

```python
from hydra_mlx_vanilla import LocalCandidateSpec, load_local_policy

spec = LocalCandidateSpec(
    export_path=export_path,
    export_bytes=actual_export_bytes,
    export_sha256=actual_export_sha256,
    checkpoint_sha256=selected_checkpoint_sha256,
    training_receipt_path=training_receipt_path,
    training_receipt_sha256=training_receipt_sha256,
    arm_receipt_path=actual_completed_arm_receipt_path,
    arm_receipt_sha256=actual_completed_arm_receipt_sha256,
    selected_step=selected_step,
    run_id=selected_run_id,
)
policy = load_local_policy(
    trained=current_model_runtime,
    spec=spec,
    frozen_data=selected_frozen_qwen_data,
    frozen_eval=selected_frozen_qwen_eval,
    should_stop=shared_stop,
    deadline_monotonic=case_deadline,
)
# Existing search(..., model_policy=policy, same_native_capabilities, ...).
# The host retains the original theorem and independently replays any proof.
# In the host finally path: saved_model_report = policy.finalize().
```

The host authenticates/pins the proposed module and selected configuration before importing them, uses the existing isolated `-I -B` worker, and imports the candidate's frozen qwen helpers in that fresh process. The loader reuses `model_runtime`'s original source/admission and quantized Base checks, verifies candidate helper hashes against the training receipt, and binds the safetensors export to the pinned genuine completed inference-only arm receipt. `selected_step` is an explicit host release binding; the parent comparison manifest supplies its actual checkpoint/selection provenance. The loader will not infer a winner from the training receipt or fabricate a completed evaluation.

No live route is changed here. The eventual minimal route change is a provider factory selecting the old `LazyModelPolicy` by default or this explicitly configured candidate. Load once on the first unresolved model request, retain `calls` and `report()` accounting, and call `finalize()` even when search returns unknown or times out. Fail a candidate request visibly if loading/validation fails; do not automatically retry with the old model and mix its results into candidate statistics. Rollback selects the preserved old provider for the next fresh worker process. The historical adapter remains SHA `7b86fc09aafa5bbb7b443119384e6b83f1f5a5f51a44340c0ca8b2e7a3b4d7c5`.

`check_mlx_mapping.py` validates only the name/shape mapping and safetensors header constraints using a clearly marked sparse metadata fixture. It performs no model execution, framework import or native proof check. Before promotion, the host must separately check the actual exported artifact, one bounded local inference, and proof replay/latency under the intended website route. The current default remains untouched until that evidence exists.
