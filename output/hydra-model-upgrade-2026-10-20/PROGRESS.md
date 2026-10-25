# Hydra model replacement comparison — 20 October 2026

**Completed:** job 24826674 ended COMPLETED / 0:0 in 1915 seconds. All 96 case results and three arm receipts were collected and passed the saved-result audit (actual exit 0, chunk `0f68ff`). Each arm proved the same 12/24 positives and zero of eight false controls. All successful proofs used only heuristics and zero model calls. Neither candidate qualifies for replacement; the live default and website remain unchanged. See [RESULTS.md](RESULTS.md) and [ANALYSIS.json](comparison-01/ANALYSIS.json). Notes below preserve preparation history; the terminal decision above supersedes pending-work wording.

The current user request is to compare recently trained WMI/Helios models with the deployed Hydra adapter and replace it only if the results support improvement. WMI is the priority.

WMI's selected candidate is `wmi-pro6000-c6-main-qwen_vanilla-s47`, checkpoint step8192, SHA `c6c5c90b27499f5f908d1a45f37d17087774e93e4e07db223fadf669f771c731`. Its selected development result is50/64, complete. The139,607,919-byte checkpoint was downloaded to `comparison-01/wmi-selected/best.pt` and independently hash-checked (actual0/53445f). All20 loader-source hashes and all seven Base hashes match the authenticated frozen C5 source (actual0/056333). No model is larger than the common Qwen3-1.7B Base; training and adapters differ.

The fixed32-case development panel has24 positives and8 controls. All statements passed the deployed native parser. The panel is exposed development, not a held-out benchmark. Expected answers are not sent to inference.

`comparison-01/study.json` SHA `b85c30a8d02a5dcc8a32d6c41b5b2d7a28449693499a509a3c3049109ed2d897` compares the deployed historical retention adapter, WMI C6 vanilla47, and Helios C5 vanilla29. One sequential three-arm job: one GH200,8CPUs,64GiB,60min maximum, inference only, no automatic retry. This is a new October allocation; the closed September6h campaign is unchanged.

All arms share the same raw Base/TorchBF16,32cases, native no-import authority, native search and independent replay, greedywidth1,6144 context and128 decision-token ceiling. Each retains its trained prompt; historical keeps its authority token mask. This is restricted-authority integration, not replication of Latent's full-library evaluation. It also differs from the deployed Mac4-bit/beam4 preview; local runtime verification is required before promotion.

Remote stage verification passed for28 payload files,1221 preserved native/app files and7 Base files (actual0/42d25b). First submission-control attempt failed before calling sbatch because loginPython3.6 rejects `text=`; no allocation occurred (actual1/eab806). The corrected manual submission uses a separate one-use marker and unchanged payload: job **24826674**, actual0/45a61b, submitted2026-10-19T23:03:00UTC. ObservedRUNNING (actual0/c86de3;0/0d42ef), then COMPLETED / 0:0 (actual0/d1d17e). Final collection succeeded (actual0/fecaa5).

Remote directory: `/net/scratch/hscra/plgrid/plgnasqret/codex-control/projects/peano-lab-training/experiments/hydra-model-upgrade-20261020/comparison-01`.

No live website/default/old model changed. The old adapter remains immutable. The isolated Torch provider and reversible local rank32MLX loader are prepared under `runtime-assessment/proposed-provider/`; metadata fixtures and actual remote numerical candidate inference passed. Local MLX inference/latency were not run because neither candidate passed the remote promotion screen.

At 23:05:34 UTC all fifteen WMI C6 run directories were checked for current locked selection receipts (actual0/efea95). Vanilla seeds11/29/47 selected complete47/49/50 of64. Fixed seeds11/29/47 selected26/14/33 of64. Random seeds11/29/47 selected46/16/43 of64; seed29's selected complete checkpoint is step4096, not its incomplete final-step evaluation. The three long-vanilla and three adaptive runs have no locked selection receipt yet. Vanilla47 remains the strongest completed, selected development candidate in this current inventory.
