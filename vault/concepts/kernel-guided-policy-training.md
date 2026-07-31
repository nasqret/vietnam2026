---
title: Kernel-guided policy training
tags: [peano-lab, llm, post-training, tactics, soundness]
---

# Kernel-guided policy training

**Kernel-guided policy training** teaches an untrusted language model to propose one complete
Peano Lab tactic line from the canonical current proof state. The model is a search policy, never
a proof authority: its command is executed through the public surface, and a trajectory becomes a
positive proof only after the [[trusted-kernel]] checks the final [[proof-certificate]] against the
original goal.

The historical repository-owned model-v2 prompt exposes the ordered goals, focus, logic mode, complete-line
grammar, and at most eight deterministically retrieved `name : statement` records. Its authority
digest identifies all 56 permitted theorems by canonical statement, dependencies, source/script
hashes, independently checked certificate hash, node count, and depth. That full identity is
`3ce83721f4517f2d5f2e734da1fbeae086473c4d1b8abb45d875a52769096439`.
The public catalog has 63 ordered entries and root
`d0f9070a2677a03eeca8ce2d1b83bcee04df3c907ef8cec2f797ab5ef99e5db0`.
The prompt shows only the small retrieval projection; manifests retain the complete checked identity. It exposes no hidden
theorem-family label, certificate, or privileged solver. The supervised runtime masks prompt tokens
and trains on the bare tactic followed by EOS.

Model-v3 supersedes that fixed 56-theorem view with the complete declaration-ordered 247-theorem
checked identity. A library proof for theorem $i$ sees exactly the strict predecessor prefix
`THEOREMS[:i]`; its own theorem and every later theorem are absent from both execution and prompt
retrieval. The trajectory imports declared direct dependencies with ordinary `use` commands and
then runs the authored script unchanged. Prompt v3 includes every allowed prefix theorem in a
compact name inventory and displays at most twelve deterministically retrieved detailed statement
records. The split corrects a measured gap: statement retrieval alone exposed only 242 of 640
direct-dependency `use` labels. Manifests still bind the full identity and exact prefix digest.
Every authored certificate is reconstructed and independently kernel-checked from the empty
context, and dataset attestation replays the emitted QEDs rather than trusting catalog claims.

The implemented pipeline includes checked synthetic trace generation, replay compilation, strict
manifests, a Qwen3 BF16 LoRA training runtime, guarded cluster controls, arbitrary-theorem requests,
and kernel-judged rollout evaluation. The first WMI Qwen3-1.7B smoke scored 0/4 at pass@4 and zero
successful parity rollouts in 16 samples (pass@16 = 0.0), but did produce one checked proof in eight
samples for a fresh direct-witness theorem. That result is consistent with a represented template;
attribution to fine-tuning awaits the pretrained-base baseline, and induction-level planning was
not demonstrated.

The first Helios preparation attempt exposed an environment-design distinction: the pinned
`ML-bundle/25.10` module loads CUDA and points `pip` at a reviewed ARM wheel directory, but does not
make Torch importable. The corrected preflight recreates an isolated environment, installs exact
`torch==2.9.1+cu129` plus an explicit transitive closure, requires binary wheels and `pip check`,
replaces inherited Python paths, disables the user site, and only then performs the real BF16 LoRA
step. Dependency gating kept the failed attempt from starting training or evaluation.

The replacement Helios preparation job passed the full one-step BF16 LoRA save/reload smoke. A
second execution site, [[wmi-a100-training-runtime]], is intentionally treated as a different
environment rather than a drop-in queue. Its accepted prepare/train/evaluate chain completed on an
A100 with exact source, package, adapter, and scheduler provenance.

Once an adapter exists, `scripts/eval_trained_peano_policy.py --theorem ... --proof-output ...`
can attempt any bounded closed PA formula under that adapter's exact attested `model-v1` authority.
It exports ordinary pasteable `.pa` source only after the successful rollout is independently
replayed to another kernel-checked QED. A missing proof exits nonzero and creates no proof file;
the model cannot widen its logic mode, tactic set, or importable theorem list.

Training data enters through the [[compact-headless-proof-runner]] and is separated with a
[[genealogy-safe-proof-data-split]]. Model-v2's deterministic 100,000-row schedule historically targeted a 2:1:1
mixture of foundational, induction/IH, and checked-library retrieval/composition transitions; a
10,000-row gate requires all 25 tactic heads and all 56 allowed imports. The four evaluation goals
are `le_trans`, `le_antisymm`, `le_total`, and `mul_eq_zero`; import sealing additionally excludes
their three public descendants, `mul_ne_zero`, `two_large_factors_impossible`, and `prime_two`.
Model-v3 instead combines the exact 247 predecessor-prefix theorem trajectories with 51
root-balanced synthetic schemas across 14 first-tactic heads. Artificial induction gates are
removed, and `intro` is capped at 20% of root sessions. Its separately sealed goals replace the old
model-v2 targets because those theorems now occur in training. The current configuration asks every
selected row to fit the pinned tokenizer within Qwen's 32,768-token native limit; any over-length row fails preparation
instead of being truncated.

The final curriculum is selected by proof session rather than by JSONL prefix. All 8,494 catalog
transitions are mandatory; synthetic sessions are indivisible and fit under a 12,288-row ceiling.
The selector anchors every schema, balances all root heads in complete rounds, is stable under
input reordering, and binds the candidate and selected populations. Exact tokenizer records cap
both total token exposure and the sum of squared sequence lengths. Model-v3 therefore forbids an
additional `max_train_samples` slice.

Long prompts use an exact indexed completion objective. Prompt labels remain ignored and the
supervised tactic-plus-EOS suffix is unchanged, but Qwen materializes vocabulary logits only at
positions that predict supervised tokens. FP32 cross-entropy sums are divided by the exact
supervised-token count across gradient accumulation. A pinned Qwen3 LoRA probe matches full-logit
loss and gradients; this is a memory optimization, not weaker supervision.

Model-v3 completion admits the serialized policy independently of the live training object. Three
deterministic admitted train/validation probes bind exact tokenization, indexed losses, and
projected-logit bytes, while a canonical fingerprint binds every PEFT tensor. One fresh local-only
reload must equal both the terminal state and actual safetensors and must behave differently when
the adapter is disabled. The resulting evidence is joined to the run, base commit/configuration,
single-GPU runtime, and closed artifacts before inference. This guards the optimizer-to-inference
handoff; it does not make model suggestions trusted proofs.

Prompt-v3 attestation and the model-v3 curriculum form one launch contract: each is present if and
only if the other is, with the check performed before importing Torch, PEFT, or Transformers. Once
the saved policy passes semantic admission, both protected artifact trees are checked again after
the remaining provenance work and immediately before no-replace publication of the final manifest.
The direct generation and pretrained-base comparison paths check their adapter/tokenizer trees on
both sides of heavy loading. Recovery requires exact directory/file modes `0555`/`0444`; these are
provenance and accidental-corruption checks, not protection from a hostile same-owner process. The
focused wiring audit passes 89 tests, while optimizer training and model-v3 capability evidence
remain pending.

The implemented [[verifier-guided-policy-evaluation-and-search]] asks for several complete lines at
one immutable state, rejects failures transactionally, deduplicates canonical successor states, and
keeps a bounded depth-32 beam. `scripts/peano_policy_repl.py` keeps the adapter resident and exposes
a proof only after a second fresh kernel replay. The guarded WMI and Helios launchers provide the
same interface on an A100 or GH200. The model-v3 WMI chain first seals the historical replay
corpus, then verifies that current compiler/kernel/prompt/library sources remain eligible to
consume those exact bytes. A distinct sealed-preparation job performs the selected tokenizer audit
and extremal indexed-loss LoRA smoke; only its exact dependent training job may optimize. Frozen
search is followed by a model-free independent replay of every claimed proof. Retry `172729` built
both source lanes, continuation `173040` completed their independent gates, and seal job `213641`
published content SHA-256
`7b22bdf083894e3d87b84fc463ff537a75eeecba8e34098429db215592ec6b5b`.
Current-source preparation `214264` then failed closed before runtime smoke or model loading because
the selected train exposure, 73,446,475 tokens, exceeded its 70,000,000-token ceiling. The reviewed
retry changes only that ceiling to 74,000,000. No model-v3 optimizer step has run; replacement
preparation, adapter, evaluation, independent replay, and proof-quality results remain pending.

## Related

[[proof-trace-corpus]] · [[kernel-judged-evaluation]] · [[pass-at-k]] ·
[[peano-lab-moc|Peano Lab MOC]]
