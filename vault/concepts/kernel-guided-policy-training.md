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

The repository-owned prompt exposes the ordered goals, focus, logic mode, surface name, and a hash
of the exact command-and-theorem capability set. It does not expose a hidden theorem-family label,
certificate, or privileged solver. The supervised runtime masks prompt tokens and trains on the
bare tactic followed by EOS; a delimiter stored in the dataset envelope is validated and removed
before computing loss.

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
[[genealogy-safe-proof-data-split]]. The planned second stage uses
[[verifier-guided-policy-evaluation-and-search]] to collect only newly kernel-checked trajectories
for expert iteration. A new [[content-addressed-lemma-library]] must bind the external foundation
used by model-v2; simply adding theorem names to model-v1 would invalidate the experiment.

## Related

[[proof-trace-corpus]] · [[kernel-judged-evaluation]] · [[pass-at-k]] ·
[[peano-lab-moc|Peano Lab MOC]]
