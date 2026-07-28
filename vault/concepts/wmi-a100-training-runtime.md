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
identity. The first tracked job requests one typed A100 for five minutes, installs nothing, and
checks device isolation, VRAM, BF16 support, a finite forward/backward pass, modules, storage, and
outbound access.

Only after this probe passes may a separate pinned Transformers/PEFT overlay and full LoRA
save/reload smoke be created. Regardless of site, the learned model remains untrusted and every
successful trajectory ends at the [[trusted-kernel]].

## Related

[[kernel-guided-policy-training]] · [[kernel-judged-evaluation]] ·
[[verifier-guided-policy-evaluation-and-search]]
