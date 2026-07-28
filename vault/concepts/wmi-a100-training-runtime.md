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

## Related

[[kernel-guided-policy-training]] · [[kernel-judged-evaluation]] ·
[[verifier-guided-policy-evaluation-and-search]] · [[content-addressed-lemma-library]]
