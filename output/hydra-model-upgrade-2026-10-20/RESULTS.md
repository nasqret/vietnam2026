# WMI and Helios model comparison — 20 October 2026

**Decision: retain the current Hydra model.** The selected recent WMI and Helios checkpoints were loaded and evaluated successfully, but neither added a proof on this restricted-authority integration screen. This does not establish that the new models are universally worse. Their original training project uses a different proof library and evaluation protocol.

**21 October follow-up:** [Exact WMI trace reproduction](../hydra-wmi-bridge-2026-10-21/RESULTS.md) validates all 50 saved WMI successes through the unchanged Hydra checker, with all 3,753 transitions matching. None of these scripts uses library imports. The public worker accepts 24; 26 need a separate larger-input diagnostic profile. Successful trajectories require 35–127 model actions, and a persistent-name rendering difference was reproduced. These findings refine the integration diagnosis; they do not change this report's frozen 32-case results or establish fresh inference performance.

## Actual results

All three arms completed the same 32 cases: 24 positive targets and eight false-statement controls. Every credited proof passed the original Hydra native checker and a separate replay from the original theorem. The analysis validates all 99 result JSON files against the terminal collection receipt.

| Configuration | Positive proofs | False controls proved | Proofs using a model step | Actual model calls | Forward passes | Arm elapsed |
|---|---:|---:|---:|---:|---:|---:|
| Existing mixed-retention adapter | 12/24 | 0/8 | 0 | 20 | 76 | 733.06 s |
| WMI C6 vanilla, seed 47, step 8192 | 12/24 | 0/8 | 0 | 151 | 732 | 600.42 s |
| Helios C5 vanilla, seed 29, step 2048 | 12/24 | 0/8 | 0 | 167 | 624 | 576.21 s |

The solved theorem sets are **identical**: zero gained or lost proofs for either candidate. All 12 successful cases in each arm finished with **zero model calls**; all 112 winning tactic steps came from symbolic heuristics. Calls in the table were spent on unresolved cases. Those cases remain unknown, not disproved. No control was proved, but the runs do not supply refutation certificates for the controls.

Each arm solved one of the 12 positive targets from the exposed September arithmetic panel and 11 of the 12 newly authored composition targets. The other arithmetic targets and `transfer_branch_implication_pair` remained unresolved. Historical/WMI/Helios respectively returned 20/11/9 timeouts and 0/9/11 search-limit outcomes.

The elapsed times do not isolate model quality or decoding speed. Historical decoding constructs an authority token mask; candidate decoding uses its trained unmasked argmax, followed by the same authority check. Runtime overhead consumes the wall budget. This screen also differs from the deployed Mac MLX four-bit, beam-four path.

## Recent WMI models

The selected checkpoint is `/home/bnaskrecki/latent/artifacts/campaign6/runs/wmi-pro6000-c6-main-qwen_vanilla-s47/best.pt`, locked on 18 October at step 8192. Its complete saved development score is **50/64 (78.125%)**. The 139,607,919-byte checkpoint was downloaded, hash-verified and actually loaded in this comparison.

All 15 WMI C6 run directories were rechecked at 23:05:34 UTC on 19 October (20 October in Warsaw). Complete locked vanilla selections scored 47/49/50 of 64 for seeds 11/29/47; fixed selections scored 26/14/33; random selections scored 46/16/43. The three long-vanilla and three adaptive runs had no locked selection receipt at that check. An incomplete final-step evaluation was not substituted for a complete selected checkpoint. Vanilla47 was the strongest completed, locked development selection in this inventory.

The selected Helios C5 vanilla29 checkpoint was step 2048, with a complete saved development score of 16/64. These development scores are model-selection evidence in the Latent project, **not held-out Hydra results**. They use a full-library contract, up to 128 actions, 16,384 total decision tokens and a different evaluation ceiling. They cannot be directly compared with the results table above.

Both recent candidates use **Qwen3-1.7B-Base with rank-32 LoRA** (34,865,152 trainable parameters). They are more recently trained adapters, not larger base models. The deployed historical adapter uses rank 16. The earlier September 4B experiment was never installed as the default and is not the baseline here.

## Method and limitations

The study was frozen before inference. All arms used the same raw Qwen3-1.7B Base, Torch BF16 on one GH200, the same literal inputs, greedy width one, a 6144-token total context ceiling, at most 128 emitted decisions per call and no prompt truncation. Expected answers were not sent to inference.

Each arm retained its trained prompt. The candidates' `library-prefix=247/247` header was conditioning only: execution stayed within the original `hydra-authority-no-imports-v1` authority, with **no theorem imports**. The proof checker was not replaced or weakened. Hydra and Latent native implementations differ, so Latent's saved proof claims were not accepted as current Hydra proofs.

Common search limits were 30 seconds, 16 model calls, 2048 states, 6000 tactic attempts, 384 expansions, frontier 128, depth 96, 48 candidates per state, macro length eight, closure 16 and heuristic burst eight. There was a 35-second outer case deadline. Vampire was disabled in every arm to examine the native/model path. This does not measure the complete website portfolio with Vampire enabled.

The panel is **exposed engineering development**, not an unseen or confirmed training-excluded sample. Existing `holdout_` case IDs are historical names, not a held-out claim. No universal ranking or generalization claim follows from this test.

Promotion required complete clean arms, no proved controls and a strict increase in positive proof coverage without losing baseline proofs. Neither candidate passed. Actual local MLX and live-route checks would also be needed before replacement; they were not run because there was no qualifying winner. The prepared local loader is not a deployed or numerically validated replacement.

## Diagnostic evidence and useful follow-up

WMI produced 150 completed suggestions passing syntax/EOS/current-authority filtering. No forbidden-import rejection was observed in that provider record. A library-authority difference is therefore a methodological caveat, not an established cause of the result.

Retained WMI branch records show inappropriate `cases n` on a natural-number variable, `cases h` on an equality hypothesis, and mismatched `exact h`. An auxiliary existential lemma was accepted as a new open obligation but did not complete a proof. Helios likewise had no winning model step. This supports investigating state-sensitive tactic applicability and useful lemma selection before assuming that more training or a larger model is the remedy.

These branch observations are partial: WMI omitted 34,045 branch records across nine returned unsuccessful searches, and 11 timeout cases lack a search result. Helios omitted 48,217 branch records and has nine missing timeout search logs. These data do **not** establish total tactic acceptance/rejection rates. Winning-proof provenance is complete for every credited proof.

A useful next experiment would first validate the bridge on a few exact WMI development states and their known successful tactic sequences, then compare behavior under an explicitly matched library contract. Any newly enabled theorem would need a proof checked by the current kernel. This is a separate experiment, not a reason to relax the replacement gate.

## Execution and preserved evidence

Helios job **24826674** ended **COMPLETED / 0:0**, consuming **1915 seconds (31 min 55 s)** on one GH200, eight CPUs and 64 GiB. The cap was 60 minutes. No training or automatic retry occurred. The first submission-control attempt hit a login-Python compatibility error before invoking `sbatch`; the corrected control attempt submitted this single job. The closed September GPU ledger remains unchanged.

No live website, model selection, serving configuration or old weights were changed. The four live Python entry/runtime files still match the frozen source. Existing WMI jobs and the unrelated held Helios job were left alone. Candidate weight exports were not downloaded because neither candidate passed promotion.

- [Audited analysis](comparison-01/ANALYSIS.json): paired results, per-case counters, proof provenance and hashes; actual analyzer exit 0, tool chunk `0f68ff`.
- [Terminal completion receipt](comparison-01/TERMINAL_COMPLETION.json): actual scheduler query `d1d17e`, successful collection `fecaa5`, and all 99 result-file hashes.
- [Frozen study](comparison-01/study.json): SHA-256 `b85c30a8d02a5dcc8a32d6c41b5b2d7a28449693499a509a3c3049109ed2d897`.
- [WMI discovery](wmi-inventory/WMI_DISCOVERY.md), [selected WMI receipt](comparison-01/wmi-selected/receipt.json), and [selection](comparison-01/wmi-selected/selection.json).
- [Unchanged live runtime check](comparison-01/LIVE_RUNTIME_UNCHANGED.json).
- [Prepared integration code](runtime-assessment/proposed-provider/): Torch inference was exercised; proposed local MLX inference was not run or installed.

Independent read-only review also matched all 99 files and checked all 36 credited proof records against both saved native replays (actual exit 0, chunk `054d3d`). Analysis SHA-256: `249cb058ae25594f8ae57990ac2d97860666992469bda3d56d8d6a3e5c65f547`.

| Adapter | Checkpoint SHA-256 |
|---|---|
| Existing retention | `7b86fc09aafa5bbb7b443119384e6b83f1f5a5f51a44340c0ca8b2e7a3b4d7c5` |
| WMI C6 vanilla47 | `c6c5c90b27499f5f908d1a45f37d17087774e93e4e07db223fadf669f771c731` |
| Helios C5 vanilla29 | `ce98db794ee6f87565f0012cadce3e0d1b5854ee3bcb513405e85c7f8921467f` |
