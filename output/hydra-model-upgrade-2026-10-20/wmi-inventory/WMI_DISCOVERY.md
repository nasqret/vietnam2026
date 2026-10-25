# WMI model discovery — 2026-10-20

The actionable candidate is **C6 vanilla seed 47, selected at 8,192 updates**. It is a Qwen3-1.7B native Peano next-tactic model from the `latent` project, not an unrelated Lean/general model. This is additional training in the same 1.7B model class as the historical Hydra baseline, not a larger architecture. Replacement still requires the parent's paired Hydra comparison.

- Remote checkpoint: `/home/bnaskrecki/latent/artifacts/campaign6/runs/wmi-pro6000-c6-main-qwen_vanilla-s47/best.pt`
- Size: **139,607,919 bytes**; SHA-256: `c6c5c90b27499f5f908d1a45f37d17087774e93e4e07db223fadf669f771c731`.
- Selection locked `2026-10-18T10:05:43.407854+00:00`, development-only, fixed depth 1. Complete result: **50/64 development proofs (78.125%)**; validation loss `0.4737441143060169`.
- Local authoritative metadata fetched by parent: [`selection.json`](../comparison-01/wmi-selected/selection.json), [`receipt.json`](../comparison-01/wmi-selected/receipt.json). Parent completed the checkpoint download and hash comparison (actual exit 0, chunk `53445f`); this discovery agent did not read weights.

The selection contract is `campaign5-constructive-v1`, dev split, 64 selected tasks, at most 128 actions, 128 new tokens per action, 16,384 total decision tokens, context 6,144, one candidate, search width 1, and a 7,200-second evaluation ceiling. It explicitly records `complete: true` and `test_used: false`. These are model-selection results, not held-out performance or evidence that Hydra has improved. The Oct19 project memory reports completed vanilla seeds 11/29/47 at 47/49/50 of 64; longer and recurrent runs were still in progress in that snapshot. No exhaustive current WMI winner claim is made.

The frozen training release is `/home/bnaskrecki/latent/releases/campaign6-training-wmi-v5`; its registered release-manifest SHA-256 is `c88869eba4bd5d2d26a0a6f3f09f92d0153815375148861b1b63a6c7bb8f94e2`. Registration is preserved in [`registration-wmi.json`](latent/artifacts/campaign6/registration-wmi.json).

**Reuse the already authenticated 20-module C5 loader** at `../helios-inventory/c5-frozen-source/src/latentproof/`: parent verified all 20 `identity.sources_sha256` entries exactly match the C6 receipt, and the base pins match (actual exit 0, chunk `056333`). The complete expected source pin map remains in the selected C6 receipt; no mutable project source is needed. Core pins:

| Module | SHA-256 |
|---|---|
| `qwen_data.py` | `2f1423410fc26eb32476e3ef051f0270723fa3f9a1296be3d3369e85112d5da4` |
| `qwen_train.py` | `0259ab35873fd7d07f92d31c9cb3d7f7e9b7c8600d8bb9a51ce93c2f56853bcc` |
| `qwen_eval.py` | `b79a8bc9fcf3867f2cbfba5d3d4cd96008b2c020e51a5cc8e5c66249cd810334` |
| `qwen_recurrent.py` | `799d3639670d47480d94c7786bd089bd3afab30e5dbf0195be198abc97dd394e` |

The receipt pins `Qwen/Qwen3-1.7B-Base` revision `ea980cb0a6c2ae4b936e82123acc929f1cec04c1`, base weights SHA-256 `6df85b39330e5a425ee36253d0f894e4387e4f0a15b9c53cb467d668e6b3a841`, LoRA rank 32 / alpha 64 / dropout 0, and 34,865,152 trainable parameters. Recorded runtime: Python 3.12.12, PyTorch 2.7.1+cu128, Transformers 4.53.3, PEFT 0.16.0, NVIDIA RTX PRO 6000 Blackwell Server Edition. WMI microbatch 1, effective batch 16, context 6,144 is a separate numerical trajectory from Helios.

`wmicluster` authentication succeeded; no fallback host, allocation, upload, job modification, or server change was needed. Bounded path/stat evidence is in [`c6-shortlist-06.json`](c6-shortlist-06.json) (actual exit 0, chunk `b81051`). The attempted complete frozen-source text read returned SSH exit 0 but the tool truncated its 108,749-token response; it is **not an authenticated source artifact**. [`c6-source-read-truncation-07.json`](c6-source-read-truncation-07.json) preserves that limitation. It was not repeated because the existing authenticated C5 source exactly matches the C6 receipt.
