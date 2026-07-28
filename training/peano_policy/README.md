# Peano next-tactic policy

This directory contains a small BF16 LoRA runtime for a Qwen3 base model.  It
predicts one Peano Lab tactic from the current canonical proof state.  Its
output is untrusted: evaluation executes the tactic through the public Peano
surface, and QED counts only after the independent kernel checks the complete
certificate against the original goal.

## One prompt contract

There is one repository-owned, non-chat prompt:

```text
<task>next_tactic</task>
<env>peano-lab-v1;surface=model-v1;logic=intuitionistic;capability_sha256=...</env>
<state>{"focus":0,"goals":["⊢ ∀ n. n + 0 = n"]}</state>
<tactic>
```

It contains the visible proof state and the hash of the complete command and
theorem capability set.  It does **not** contain a theorem/library name or a
second, hidden copy of the original statement.  `prompt.py` renders and checks
this contract for both training and inference.

The dataset compiler stores an envelope completion such as
`refl</tactic>`.  The loader validates the single terminal delimiter, extracts
`refl`, and trains on exactly `refl` followed by the tokenizer EOS.  Every
prompt token has label `-100`; only tactic tokens and EOS contribute to the
loss.  Generation therefore returns the bare tactic `refl`, never XML markup.

## Trusted input boundary

Do not point the trainer at a raw trace-v1 export.  First run the replay
compiler:

```bash
python3 scripts/build_peano_policy_dataset.py \
  RAW_TRACE.jsonl \
  --metadata SESSION_METADATA.jsonl \
  --output-dir data/peano-policy-v1
```

The runtime accepts only the compiler's strict 19-field rows.  It verifies:

- the adjacent `manifest.json` identifies the v1 next-tactic dataset;
- every claimed QED session survived checked replay;
- the selected split's byte hash and row count;
- the exact capability preimage and its SHA-256 identity;
- equality of the stored prompt with the row's state/environment fields; and
- a one-line `TACTIC</tactic>` envelope completion.

Before importing PyTorch or downloading a model, `attest.py` also hashes every
raw trace and sidecar named by the manifest, verifies the current compiler and
complete Peano source inventory, rejects the four frozen held-out targets,
checks that neither canonical formulas nor exact policy prompts cross splits,
and rebuilds all three split files by replaying every source session through
the public surface and independent kernel.  The rebuilt bytes must match exactly.  This attestation,
the train/validation hashes, and the one fixed `model-v1` environment are bound
into the run identity and final training manifest.

Unfinished sessions, transactional error attempts, legacy `status="ok"` rows,
and raw trace prefixes are not cross-entropy inputs.  The TOML files therefore
have no `accepted_statuses` escape hatch.

## Runs

The initial configurations are:

- `configs/qwen3_1_7b_smoke.toml`: 100 optimizer steps, rank-8 LoRA;
- `configs/qwen3_4b_pilot.toml`: two epochs, rank-16 LoRA; and
- `configs/pythagoras_4b_pilot.toml`: two epochs, rank-16 LoRA.

All three use BF16 weights and PyTorch SDPA.  They require neither FlashAttention,
vLLM, bitsandbytes, nor quantized loading.  PyTorch comes from Helios
`ML-bundle/25.10`; the small Python layer is pinned in
`requirements-helios.lock`.

After the replay dataset has been installed at the path named in the config:

```bash
python3 -m training.peano_policy.train \
  --config training/peano_policy/configs/qwen3_1_7b_smoke.toml
```

`resume="auto"` discovers the newest Transformers checkpoint in the output
directory. `--resume-from-checkpoint NEVER`, `AUTO`, or an explicit path
overrides it. Every supported model ID is paired with one reviewed immutable
40-character Hub commit; a different commit is rejected even when the model ID
is otherwise allowed. The downloaded model and tokenizer must both resolve to
that exact commit.

Each completed run writes `training-manifest.json` with closed-directory hashes
for every loader-visible adapter and tokenizer file, plus hashes for the
train/eval splits, replay attestation, both replay manifests, TOML config, training
source tree, exact prompt contract, base configuration, and resolved
model/tokenizer identities.

For a standalone decode, supply an exact prompt created with `render_prompt`:

```bash
python3 -m training.peano_policy.generate \
  --adapter results/peano-policy/qwen3-1.7b-lora-smoke \
  --prompt-file /path/to/peano-prompt.txt \
  --environment-file /path/to/peano-environment.json
```

The evaluation adapter renders each new state with an explicit
`PromptEnvironment`; callers must provide the exact capability identity that
the replay attestation recorded at training.  A hard-coded environment cannot
launder an adapter trained with another theorem allowlist, and an adapter whose
data contains a held-out target is rejected before its weights load.  The
standalone environment file has exactly this shape:

```json
{
  "classical": false,
  "capabilities": {
    "label": "model-v1",
    "allowed_commands": ["apply", "assumption", "cases", "compact_arith", "congr", "exact", "exfalso", "exists", "forall_elim", "have", "induction", "intro", "left", "norm_num", "refl", "rewrite", "right", "ring", "simp", "specialize", "split", "suffices", "symm", "trans", "use"],
    "allowed_theorems": ["add_assoc", "add_eq_zero_right", "add_succ_left", "antisymm_from_witnesses", "drop_add_prefix_from_fixed", "no_succ_add_fixed", "zero_add"]
  }
}
```
